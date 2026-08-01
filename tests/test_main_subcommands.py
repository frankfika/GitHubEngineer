"""Tests for the read-only subcommands added in v1.0: --list-decisions and --show-latest."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from src.main import (
    _safe_local_directory,
    _write_config_repositories,
    main,
    show_latest,
)


class RepositoryConfigPersistenceTest(unittest.TestCase):
    def test_repository_list_write_is_canonical_atomic_and_private(self):
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / ".ghe" / "config.yml"
            target.parent.mkdir(parents=True)
            target.write_text(
                "model:\n  provider: codex_cli\nrepos:\n  - old/repository\n",
                encoding="utf-8",
            )

            written = _write_config_repositories(
                target,
                ["old/repository", "new/repository", "new/repository", "invalid"],
            )

            self.assertEqual(written, ["old/repository", "new/repository"])
            payload = yaml.safe_load(target.read_text(encoding="utf-8"))
            self.assertEqual(payload["repos"], written)
            self.assertEqual(payload["model"], {"provider": "codex_cli"})
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            self.assertEqual(list(target.parent.glob(".config.yml.*.tmp")), [])

    def test_repository_list_write_does_not_replace_invalid_config(self):
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "config.yml"
            original = "repos: [unterminated\n"
            target.write_text(original, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "could not safely read"):
                _write_config_repositories(target, ["new/repository"])

            self.assertEqual(target.read_text(encoding="utf-8"), original)


class ShowLatestSubcommandTest(unittest.TestCase):
    def _write_config(self, directory: Path, repo: str = "acme/widgets") -> Path:
        config_path = directory / "config.yml"
        config_path.write_text(
            yaml.safe_dump(
                {
                    "repo": {"full_name": repo},
                    "github": {"token": "test-token"},
                    "model": {"api_key": "test-key", "model_name": "gpt-x"},
                    "output": {"format": "markdown", "output_dir": str(directory / "reports")},
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        return config_path

    def test_show_latest_prints_most_recent_brief(self):
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            config_path = self._write_config(directory)
            reports = directory / "reports"
            reports.mkdir()
            (reports / "acme_widgets_20260714.md").write_text("old brief", encoding="utf-8")
            (reports / "acme_widgets_20260721.md").write_text("new brief", encoding="utf-8")
            previous_argv = sys.argv
            try:
                sys.argv = ["ghe", "--config", str(config_path), "--show-latest"]
                with patch("sys.stdout") as stdout:
                    self.assertEqual(main(), 0)
                output = "".join(call.args[0] for call in stdout.write.call_args_list)
                self.assertIn("new brief", output)
                self.assertNotIn("old brief", output)
            finally:
                sys.argv = previous_argv

    def test_show_latest_errors_when_no_reports_yet(self):
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            config_path = self._write_config(directory)
            previous_argv = sys.argv
            try:
                sys.argv = ["ghe", "--config", str(config_path), "--show-latest"]
                with patch("sys.stderr") as stderr:
                    self.assertEqual(main(), 1)
                errors = "".join(call.args[0] for call in stderr.write.call_args_list)
                self.assertIn("does not exist", errors)
            finally:
                sys.argv = previous_argv

    def test_show_latest_does_not_require_api_key(self):
        """show-latest must be a read-only path; config validation can be lenient."""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            config_path = directory / "config.yml"
            config_path.write_text(
                yaml.safe_dump(
                    {
                        "repo": {"full_name": "acme/widgets"},
                        "output": {"format": "markdown", "output_dir": str(directory / "reports")},
                    },
                    allow_unicode=True,
                ),
                encoding="utf-8",
            )
            (directory / "reports").mkdir()
            (directory / "reports" / "acme_widgets_20260721.md").write_text(
                "ok brief", encoding="utf-8"
            )
            previous_argv = sys.argv
            try:
                sys.argv = ["ghe", "--config", str(config_path), "--show-latest"]
                with patch("sys.stdout") as stdout:
                    self.assertEqual(main(), 0)
                output = "".join(call.args[0] for call in stdout.write.call_args_list)
                self.assertIn("ok brief", output)
            finally:
                sys.argv = previous_argv


class InitSubcommandTest(unittest.TestCase):
    def setUp(self):
        import tempfile

        self._temp_dir = tempfile.TemporaryDirectory()
        self.directory = Path(self._temp_dir.name)
        self.previous_cwd = Path.cwd()
        import os
        os.chdir(self.directory)
        # Make sure we always start without a user config.
        user_config = self.directory / ".ghe" / "config.yml"
        if user_config.exists():
            user_config.unlink()
        self.previous_argv = sys.argv

    def tearDown(self):
        import os
        os.chdir(self.previous_cwd)
        sys.argv = self.previous_argv
        self._temp_dir.cleanup()

    def test_init_writes_starter_config(self):
        sys.argv = ["ghe", "--init"]
        with patch("sys.stdout") as stdout:
            self.assertEqual(main(), 0)
        text = "".join(call.args[0] for call in stdout.write.call_args_list)
        self.assertIn("Wrote .ghe/config.yml", text)
        self.assertTrue((self.directory / ".ghe" / "config.yml").exists())

    def test_init_refuses_to_overwrite_existing_config(self):
        target = self.directory / ".ghe" / "config.yml"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# user customisation", encoding="utf-8")
        sys.argv = ["ghe", "--init"]
        with patch("sys.stdout") as stdout:
            self.assertEqual(main(), 1)
        self.assertEqual(target.read_text(encoding="utf-8"), "# user customisation")


class ListDecisionsSubcommandTest(unittest.TestCase):
    def setUp(self):
        import tempfile

        self._temp_dir = tempfile.TemporaryDirectory()
        self.directory = Path(self._temp_dir.name)
        self.memory_path = self.directory / "decisions.yml"
        self.memory_path.write_text(
            yaml.safe_dump(
                {
                    "version": 1,
                    "decisions": [
                        {
                            "status": "rejected",
                            "reason": "out of scope",
                            "themes": ["dark mode"],
                            "created_at": "2026-07-01T00:00:00Z",
                        }
                    ],
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        self.previous_argv = sys.argv

    def tearDown(self):
        sys.argv = self.previous_argv
        self._temp_dir.cleanup()

    def test_list_decisions_prints_one_line_per_record(self):
        sys.argv = ["ghe", "--memory-path", str(self.memory_path), "--list-decisions"]
        with patch("sys.stdout") as stdout:
            self.assertEqual(main(), 0)
        text = "".join(call.args[0] for call in stdout.write.call_args_list)
        self.assertIn("REJECTED", text)
        self.assertIn("dark mode", text)

    def test_list_decisions_reports_empty_memory(self):
        self.memory_path.unlink()
        sys.argv = ["ghe", "--memory-path", str(self.memory_path), "--list-decisions"]
        with patch("sys.stdout") as stdout:
            self.assertEqual(main(), 0)
        text = "".join(call.args[0] for call in stdout.write.call_args_list)
        self.assertIn("No decisions recorded", text)


class NoSubcommandHintTest(unittest.TestCase):
    """Round 6: a bare ``ghe`` invocation with no target should print
    a hint and exit 2 instead of falling through to the analysis
    branch and crashing on a missing --config.
    """

    def test_no_args_prints_hint_and_exits_2(self):
        previous = sys.argv
        try:
            sys.argv = ["ghe"]
            with patch("sys.stderr") as stderr:
                self.assertEqual(main(), 2)
            text = "".join(call.args[0] for call in stderr.write.call_args_list)
            self.assertIn("nothing to do", text)
            self.assertIn("ghe --init", text)
        finally:
            sys.argv = previous


if __name__ == "__main__":
    unittest.main()
