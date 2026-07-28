"""Unit tests for the helpers added on top of the owner's serve().

Three surfaces are covered:

* ``diagnose_repair_error`` -- every error_kind from
  ``_DIAGNOSTIC_PATTERNS`` plus the ``unknown`` fallback, including the
  fallback to ``job["message"]`` when stderr is empty.
* ``resolve_workspace_root`` -- the CLI > config > default priority
  chain plus a sanity check that the resolved path is created on disk.
* ``_build_repair_modes`` -- the anonymous/authenticated decomposition
  that ``render_repair_capabilities`` ships to the UI.

These tests run in plain unittest style so they can be picked up by the
``pytest`` configuration in ``pyproject.toml`` without any extra glue.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.main import (
    _build_repair_modes,
    _FRIENDLY_MISSING,
    _latest_failed_repair_diagnosis,
    diagnose_repair_error,
    resolve_workspace_root,
)


class DiagnoseRepairErrorTest(unittest.TestCase):
    """One test per error_kind so a regex tweak can fail locally."""

    def test_claude_not_authenticated(self) -> None:
        diagnosis = diagnose_repair_error("claude: not logged in")
        self.assertEqual(diagnosis["error_kind"], "claude_not_authenticated")
        self.assertIn("claude auth login", diagnosis["error_action"])
        self.assertTrue(diagnosis["hint"])

    def test_claude_not_authenticated_via_message_fallback(self) -> None:
        """When stderr is empty, fall back to ``job['message']``."""
        diagnosis = diagnose_repair_error(
            "",
            job={"message": "Claude Code: not authenticated, run `claude auth login`"},
        )
        self.assertEqual(diagnosis["error_kind"], "claude_not_authenticated")

    def test_gh_not_authenticated(self) -> None:
        diagnosis = diagnose_repair_error("gh: not authenticated into any GitHub hosts")
        self.assertEqual(diagnosis["error_kind"], "gh_not_authenticated")
        self.assertIn("gh auth login", diagnosis["error_action"])

    def test_test_failed_pytest_style(self) -> None:
        diagnosis = diagnose_repair_error(
            "FAILED tests/test_foo.py::test_bar - assert 1 == 2"
        )
        self.assertEqual(diagnosis["error_kind"], "test_failed")
        self.assertIn("测试日志", diagnosis["error_action"])

    def test_test_failed_short_form(self) -> None:
        diagnosis = diagnose_repair_error("pytest: 3 failed, 1 passed")
        self.assertEqual(diagnosis["error_kind"], "test_failed")

    def test_no_diff_agent_did_not_change_anything(self) -> None:
        diagnosis = diagnose_repair_error(
            "Coding agent produced no code change: Agent did not explain why."
        )
        self.assertEqual(diagnosis["error_kind"], "no_diff")
        self.assertIn("重跑", diagnosis["error_action"])

    def test_permission_denied_posix(self) -> None:
        diagnosis = diagnose_repair_error(
            "Permission denied: '/private/var/folders/abc/T' -> '/foo'"
        )
        self.assertEqual(diagnosis["error_kind"], "permission_denied")

    def test_permission_denied_eacces(self) -> None:
        diagnosis = diagnose_repair_error("OSError: [Errno 13] EACCES")
        self.assertEqual(diagnosis["error_kind"], "permission_denied")

    def test_timeout_subprocess(self) -> None:
        diagnosis = diagnose_repair_error(
            "subprocess.TimeoutExpired: Command 'claude' timed out after 1800s"
        )
        self.assertEqual(diagnosis["error_kind"], "timeout")
        self.assertIn("重试", diagnosis["error_action"])

    def test_unknown_when_nothing_matches(self) -> None:
        diagnosis = diagnose_repair_error("kaboom: a brand new error we have not seen")
        self.assertEqual(diagnosis["error_kind"], "unknown")
        self.assertIn("查看", diagnosis["error_action"])
        self.assertTrue(diagnosis["hint"])

    def test_diagnose_result_has_all_three_keys(self) -> None:
        """Every branch must return the same three-key shape."""
        for stderr in [
            "claude not logged in",
            "gh not authenticated",
            "1 test failed",
            "produced no code change",
            "EACCES",
            "timed out",
            "completely new error",
        ]:
            diagnosis = diagnose_repair_error(stderr)
            self.assertEqual(
                set(diagnosis.keys()),
                {"error_kind", "error_action", "hint"},
                f"unexpected keys for stderr={stderr!r}",
            )


class ResolveWorkspaceRootTest(unittest.TestCase):
    """The CLI > config > default priority chain."""

    def test_cli_override_wins_over_config_and_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cli_root = Path(temp_dir) / "from-cli"
            result = resolve_workspace_root(
                "acme/widgets",
                42,
                config={"repair": {"workspace_root": "/should/be/ignored"}},
                cli_override=str(cli_root),
            )
            self.assertTrue(result.is_dir())
            self.assertEqual(result.name, "from-cli")
            # The path we resolved to must be the one the caller asked for.
            self.assertEqual(str(result), str(cli_root.resolve()))

    def test_config_value_used_when_no_cli_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_root = Path(temp_dir) / "from-config"
            result = resolve_workspace_root(
                "acme/widgets",
                42,
                config={"repair": {"workspace_root": str(config_root)}},
                cli_override=None,
            )
            self.assertEqual(str(result), str(config_root.resolve()))
            self.assertTrue(result.is_dir())

    def test_default_path_is_home_githubengineer(self) -> None:
        """No CLI, no config -> ~/.githubengineer/repos/<owner>/<repo>/<issue#>/"""
        with patch("src.main.Path.home", return_value=Path("/tmp/fake-home")):
            result = resolve_workspace_root("acme/widgets", 42)
        expected = Path("/tmp/fake-home/.githubengineer/repos/acme/widgets/42").resolve()
        self.assertEqual(result, expected)
        self.assertTrue(result.is_dir())

    def test_creates_missing_intermediate_directories(self) -> None:
        """A fresh workspace_root must be created with parents."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested = Path(temp_dir) / "deep" / "nested" / "workspace"
            self.assertFalse(nested.exists())
            result = resolve_workspace_root(
                "acme/widgets", 7, cli_override=str(nested)
            )
            self.assertTrue(result.is_dir())
            self.assertEqual(result, nested.resolve())

    def test_existing_directory_is_not_deleted(self) -> None:
        """Re-running on the same workspace must preserve existing files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            existing = Path(temp_dir) / "kept"
            existing.mkdir()
            sentinel = existing / "sentinel.txt"
            sentinel.write_text("do not touch me", encoding="utf-8")
            result = resolve_workspace_root(
                "acme/widgets", 1, cli_override=str(existing)
            )
            self.assertTrue(sentinel.exists())
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "do not touch me")
            self.assertEqual(result, existing.resolve())

    def test_empty_config_section_falls_through_to_default(self) -> None:
        """An empty config dict should not block the default path."""
        with patch("src.main.Path.home", return_value=Path("/tmp/fake-home-2")):
            result = resolve_workspace_root("acme/widgets", 1, config={})
        expected = Path("/tmp/fake-home-2/.githubengineer/repos/acme/widgets/1").resolve()
        self.assertEqual(result, expected)

    def test_config_with_unrelated_keys_does_not_affect_resolution(self) -> None:
        with patch("src.main.Path.home", return_value=Path("/tmp/fake-home-3")):
            result = resolve_workspace_root(
                "acme/widgets", 1, config={"repo": {"owner": "acme"}}
            )
        expected = Path("/tmp/fake-home-3/.githubengineer/repos/acme/widgets/1").resolve()
        self.assertEqual(result, expected)

    def test_repo_without_slash_uses_safe_default(self) -> None:
        """A malformed repository name should not crash; it falls back to
        ``repos//<name>/<issue#>/``."""
        with patch("src.main.Path.home", return_value=Path("/tmp/fake-home-4")):
            result = resolve_workspace_root("just-a-name", 5)
        expected = Path("/tmp/fake-home-4/.githubengineer/repos//just-a-name/5").resolve()
        self.assertEqual(result, expected)


class BuildRepairModesTest(unittest.TestCase):
    """The anonymous / authenticated decomposition used by the preflight."""

    def test_anonymous_available_when_git_and_claude_present(self) -> None:
        """Only ``gh`` is missing -- anonymous mode still works (no push)."""
        modes = _build_repair_modes(
            missing=["gh"],
            reasons=[_FRIENDLY_MISSING["gh"]],
        )
        self.assertTrue(modes["anonymous"]["available"])
        self.assertIn("clone_public", modes["anonymous"]["capabilities"])
        # gh is NOT part of anonymous mode's required set, so its friendly
        # message must not appear in ``missing_for_anonymous``.
        self.assertEqual(modes["anonymous"]["missing_for_anonymous"], [])
        # But it must show up under authenticated mode -- fork + PR need gh.
        self.assertFalse(modes["authenticated"]["available"])
        self.assertIn(
            _FRIENDLY_MISSING["gh"], modes["authenticated"]["missing_for_authenticated"]
        )

    def test_anonymous_blocked_when_git_missing(self) -> None:
        modes = _build_repair_modes(
            missing=["git"],
            reasons=[_FRIENDLY_MISSING["git"]],
        )
        self.assertFalse(modes["anonymous"]["available"])
        self.assertIn(_FRIENDLY_MISSING["git"], modes["anonymous"]["missing_for_anonymous"])
        self.assertFalse(modes["authenticated"]["available"])

    def test_anonymous_blocked_when_claude_missing(self) -> None:
        modes = _build_repair_modes(
            missing=["claude"],
            reasons=[_FRIENDLY_MISSING["claude"]],
        )
        self.assertFalse(modes["anonymous"]["available"])
        self.assertIn(_FRIENDLY_MISSING["claude"], modes["anonymous"]["missing_for_anonymous"])

    def test_authenticated_capabilities_include_pr_workflow(self) -> None:
        modes = _build_repair_modes(missing=[], reasons=[])
        self.assertTrue(modes["authenticated"]["available"])
        for capability in ("clone", "edit", "test", "fork", "draft_pr"):
            self.assertIn(capability, modes["authenticated"]["capabilities"])

    def test_modes_shape_is_stable(self) -> None:
        """Pin the dict shape so a refactor cannot silently drop a key."""
        modes = _build_repair_modes([], [])
        self.assertEqual(set(modes.keys()), {"anonymous", "authenticated"})
        # Spot-check the per-mode subkeys without a brittle shared set.
        self.assertEqual(
            set(modes["anonymous"].keys()),
            {"available", "capabilities", "missing_for_anonymous", "hint"},
        )
        self.assertEqual(
            set(modes["authenticated"].keys()),
            {"available", "capabilities", "missing_for_authenticated", "hint"},
        )


class LatestFailedRepairDiagnosisTest(unittest.TestCase):
    """The helper that ``render_repair_capabilities`` calls on every refresh."""

    def _write_job(self, directory: Path, job_id: str, status: str, message: str, updated_at: str) -> None:
        (directory / f"{job_id}.json").write_text(
            json.dumps(
                {
                    "id": job_id,
                    "status": status,
                    "repository": "acme/widgets",
                    "message": message,
                    "updated_at": updated_at,
                }
            ),
            encoding="utf-8",
        )

    def test_returns_none_when_no_jobs_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertIsNone(
                _latest_failed_repair_diagnosis(jobs_dir=Path(temp_dir) / "missing")
            )

    def test_returns_none_when_no_failed_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir) / "jobs"
            jobs_dir.mkdir()
            self._write_job(jobs_dir, "abc", "review_ready", "ok", "2026-07-11T10:00:00Z")
            self.assertIsNone(_latest_failed_repair_diagnosis(jobs_dir=jobs_dir))

    def test_picks_most_recent_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir) / "jobs"
            jobs_dir.mkdir()
            self._write_job(jobs_dir, "old", "failed", "1 test failed", "2026-07-10T10:00:00Z")
            self._write_job(
                jobs_dir, "new", "failed", "gh: not authenticated", "2026-07-11T10:00:00Z"
            )
            result = _latest_failed_repair_diagnosis(jobs_dir=jobs_dir)
            self.assertIsNotNone(result)
            assert result is not None  # for type checkers
            self.assertEqual(result["job_id"], "new")
            self.assertEqual(result["error_kind"], "gh_not_authenticated")
            self.assertEqual(result["repository"], "acme/widgets")

    def test_skips_corrupt_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir) / "jobs"
            jobs_dir.mkdir()
            (jobs_dir / "broken.json").write_text("not json at all", encoding="utf-8")
            self.assertIsNone(_latest_failed_repair_diagnosis(jobs_dir=jobs_dir))


if __name__ == "__main__":
    unittest.main()
