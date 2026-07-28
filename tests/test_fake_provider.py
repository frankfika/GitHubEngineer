"""Unit tests for the FakeProvider used by the e2e / dev-demo path.

These tests do *not* require a network connection, an API key, or a
live OpenAI server. They are the spec the e2e harness relies on:

* ``test_fake_provider_returns_diff_for_known_issue`` -- the provider
  looks up issue 1, applies its diff, and reports a non-empty summary.
* ``test_fake_provider_default_response`` -- unknown issue numbers
  fall through to the ``default`` key in fake_responses.yml.
* ``test_fake_provider_force_fail`` -- ``FAKE_PROVIDER_FAIL`` env var
  forces a structured ``api_key_invalid`` error so the UI can render
  its error preflight.
* ``test_fake_provider_git_apply_failure`` -- a malformed diff
  surfaces as ``no_diff`` with a hint, not as a 500.
* ``test_fake_provider_via_factory`` -- ``get_provider`` resolves the
  ``"fake"`` provider name to ``FakeProvider`` without raising.

The tests pin the *contract* of FakeProvider -- if you change the
public surface (constructor, name, env-var knobs), update these tests.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.coding_agent import (
    CodingAgentConfigError,
    FakeProvider,
    get_provider,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
FAKE_RESPONSES = REPO_ROOT / "tests" / "mocks" / "fake_responses.yml"


def _make_git_workspace(tmp: Path) -> Path:
    """Create a throwaway git repo with one tracked .py file.

    The contents of ``src/hello.py`` are deliberately tiny so they
    do not collide with the canned diffs in ``fake_responses.yml``.
    Tests that need a specific target file (e.g. ``src/greet.py``)
    create it on top of this base.
    """
    ws = tmp / "ws"
    ws.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=ws, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=ws, check=True)
    (ws / "src").mkdir()
    (ws / "src" / "hello.py").write_text("def hi():\n    return 1\n", encoding="utf-8")
    # Pre-create the files the canned diffs in fake_responses.yml
    # target. Without these, the canned patches fail ``git apply``
    # with "No such file" and the test exercises the wrong path.
    (ws / "src" / "greet.py").write_text(
        'def greet(names):\n    return ", ".join(names)\n\n'
        'if __name__ == "__main__":\n    print(greet([]))\n',
        encoding="utf-8",
    )
    (ws / "src" / "math.py").write_text(
        "def add(a, b):\n    return a + b\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "-A"], cwd=ws, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=ws, check=True)
    return ws


class FakeProviderKnownIssueTest(unittest.TestCase):
    def setUp(self) -> None:
        # Always point at the committed YAML so the test is hermetic.
        self._env = patch.dict(
            os.environ,
            {"FAKE_PROVIDER_RESPONSES": str(FAKE_RESPONSES), "FAKE_PROVIDER_FAIL": ""},
        )
        self._env.start()
        self.provider = FakeProvider()

    def tearDown(self) -> None:
        self._env.stop()

    def test_fake_provider_returns_diff_for_known_issue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = _make_git_workspace(Path(tmp))
            result = self.provider.run(
                "Please fix Issue #1 in this repo.", ws
            )
            self.assertTrue(
                result.ok,
                msg=f"expected ok, got error_kind={result.error_kind!r} "
                    f"hint={result.error_hint!r}",
            )
            self.assertIn("Fix #1", result.summary)
            self.assertIn("[fake]", result.summary)
            # The diff for issue 1 in fake_responses.yml touches src/greet.py.
            # We can't assert that file exists, but we *can* assert the
            # working tree changed.
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=ws, capture_output=True, text=True, check=True,
            )
            self.assertTrue(
                status.stdout.strip(),
                msg="expected git status to show changes after FakeProvider ran",
            )


class FakeProviderDefaultTest(unittest.TestCase):
    def setUp(self) -> None:
        self._env = patch.dict(
            os.environ,
            {"FAKE_PROVIDER_RESPONSES": str(FAKE_RESPONSES), "FAKE_PROVIDER_FAIL": ""},
        )
        self._env.start()
        self.provider = FakeProvider()

    def tearDown(self) -> None:
        self._env.stop()

    def test_fake_provider_synthesizes_response_for_unknown_issue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = _make_git_workspace(Path(tmp))
            # Unknown numbered issues use a workspace-derived patch rather than
            # the YAML ``default`` entry, which may target fixture-only files.
            result = self.provider.run(
                "Please fix Issue #9999 in this repo.", ws
            )
            self.assertTrue(result.ok, msg=result.error_hint)
            self.assertIn("Synthesized", result.summary)
            self.assertIn(
                "Module touched by FakeProvider",
                (ws / "src" / "greet.py").read_text(encoding="utf-8"),
            )


class FakeProviderForceFailTest(unittest.TestCase):
    def setUp(self) -> None:
        self._env = patch.dict(
            os.environ,
            {
                "FAKE_PROVIDER_RESPONSES": str(FAKE_RESPONSES),
                "FAKE_PROVIDER_FAIL": "1,2,3",
            },
        )
        self._env.start()
        self.provider = FakeProvider()

    def tearDown(self) -> None:
        self._env.stop()

    def test_fake_provider_force_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = _make_git_workspace(Path(tmp))
            result = self.provider.run(
                "Please fix Issue #1 in this repo.", ws
            )
            self.assertFalse(result.ok)
            self.assertEqual(result.error_kind, "api_key_invalid")
            self.assertIn("FAKE_PROVIDER_FAIL", (result.error_action or ""))


class FakeProviderGitApplyFailureTest(unittest.TestCase):
    def test_fake_provider_git_apply_failure(self) -> None:
        """An unparseable diff in the canned file surfaces as no_diff."""
        with tempfile.TemporaryDirectory() as tmp:
            bad_yaml = Path(tmp) / "bad.yml"
            bad_yaml.write_text(
                # A diff whose hunk header refers to a file that does not
                # exist. git apply will reject it.
                "\"1\":\n"
                "  summary: \"[fake] broken patch\"\n"
                "  diff: |\n"
                "    --- a/this_file_does_not_exist_anywhere.py\n"
                "    +++ b/this_file_does_not_exist_anywhere.py\n"
                "    @@ -1,1 +1,1 @@\n"
                "    -old\n"
                "    +new\n",
                encoding="utf-8",
            )
            ws = _make_git_workspace(Path(tmp))
            with patch.dict(
                os.environ,
                {"FAKE_PROVIDER_RESPONSES": str(bad_yaml), "FAKE_PROVIDER_FAIL": ""},
            ):
                provider = FakeProvider()
                result = provider.run("Please fix Issue #1 in this repo.", ws)
            self.assertFalse(result.ok)
            self.assertEqual(result.error_kind, "no_diff")
            self.assertIn("git apply", (result.error_hint or "").lower())


class FakeProviderFactoryTest(unittest.TestCase):
    def test_fake_provider_via_factory(self) -> None:
        provider = get_provider({"coding_agent": {"provider": "fake"}})
        self.assertIsInstance(provider, FakeProvider)
        self.assertEqual(provider.name(), "fake")

    def test_fake_provider_via_factory_accepts_aliases(self) -> None:
        # Only "fake" is documented as the canonical name, but the
        # factory should reject unknown names cleanly (not crash).
        with self.assertRaises(CodingAgentConfigError):
            get_provider({"coding_agent": {"provider": "totally-fake"}})


class FakeProviderNameTest(unittest.TestCase):
    def test_provider_name(self) -> None:
        p = FakeProvider()
        self.assertEqual(p.name(), "fake")

    def test_health_check_always_true(self) -> None:
        p = FakeProvider()
        ok, msg = p.health_check()
        self.assertTrue(ok)
        self.assertIsNone(msg)


if __name__ == "__main__":
    unittest.main()
