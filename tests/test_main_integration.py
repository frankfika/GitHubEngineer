from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import yaml

from src.github_client import GitHubClientError
from src.llm_client import LLMClientError
from src.main import main


class MainIntegrationTest(unittest.TestCase):
    """Exercise the CLI orchestration without GitHub or LLM network access."""

    def _write_config(self, directory: Path, output_format: str = "markdown") -> Path:
        config_path = directory / "config.yml"
        config_path.write_text(
            yaml.safe_dump(
                {
                    "repo": {"full_name": "acme/widgets"},
                    "github": {"token": "test-token"},
                    "model": {
                        "api_key": "test-key",
                        "model_name": "test-model",
                    },
                    "analysis": {
                        "lookback_days": 7,
                        "max_issues_for_llm": 10,
                        "top_n": 3,
                    },
                    "output": {
                        "format": output_format,
                        "output_dir": str(directory / "reports"),
                    },
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        return config_path

    @staticmethod
    def _issue_payload(number: int = 42) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "number": number,
            "title": "Application crashes when saving",
            "body": "Steps to reproduce: save a document.",
            "created_at": now,
            "updated_at": now,
            "comments_count": 4,
            "reactions": 3,
            "labels": ["bug"],
            "assignees": [],
            "state": "open",
            "url": f"https://github.com/acme/widgets/issues/{number}",
        }

    def test_main_generates_report_and_action_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            config_path = self._write_config(directory, output_format="action-summary")
            summary_path = directory / "step-summary.md"
            github = Mock()
            github.get_open_issues.return_value = [object()]
            github.get_issue_metrics.return_value = self._issue_payload()
            llm = Mock()
            llm.generate_json.return_value = {
                "summary": "Saving failures affect several users.",
                "priorities": [
                    {
                        "issue_number": 42,
                        "title": "Application crashes when saving",
                        "priority_score": 9.0,
                        "reason": "Several independent reports block a core workflow.",
                        "user_impact": "Users cannot save documents.",
                        "estimated_effort": "low",
                    }
                ],
                "missing_info_issues": [42],
            }
            previous_args = sys.argv
            previous_summary = os.environ.get("GITHUB_STEP_SUMMARY")
            try:
                sys.argv = ["ghe", "--config", str(config_path)]
                os.environ["GITHUB_STEP_SUMMARY"] = str(summary_path)
                with patch("src.main.GitHubClient", return_value=github) as github_class, patch(
                    "src.main.LLMClient", return_value=llm
                ) as llm_class:
                    self.assertEqual(main(), 0)

                github_class.assert_called_once_with("test-token", "acme/widgets")
                llm_class.assert_called_once_with(None, "test-key", "test-model")
                github.get_open_issues.assert_called_once()
                llm.generate_json.assert_called_once()

                reports = list((directory / "reports").glob("acme_widgets_*.md"))
                self.assertEqual(len(reports), 1)
                report = reports[0].read_text(encoding="utf-8")
                self.assertIn("#42: Application crashes when saving", report)
                self.assertIn("Saving failures affect several users.", report)
                self.assertEqual(summary_path.read_text(encoding="utf-8"), report + "\n")
            finally:
                sys.argv = previous_args
                if previous_summary is None:
                    os.environ.pop("GITHUB_STEP_SUMMARY", None)
                else:
                    os.environ["GITHUB_STEP_SUMMARY"] = previous_summary

    def test_main_generates_empty_report_when_no_recent_open_issues(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            config_path = self._write_config(directory)
            github = Mock()
            github.get_open_issues.return_value = []
            llm = Mock()
            llm.generate_json.return_value = {
                "summary": "No recently updated open issues.",
                "priorities": [],
                "missing_info_issues": [],
            }
            previous_args = sys.argv
            try:
                sys.argv = ["ghe", "--config", str(config_path)]
                with patch("src.main.GitHubClient", return_value=github), patch(
                    "src.main.LLMClient", return_value=llm
                ):
                    self.assertEqual(main(), 0)

                report = next((directory / "reports").glob("acme_widgets_*.md")).read_text(
                    encoding="utf-8"
                )
                self.assertIn("No high-confidence priorities were identified.", report)
            finally:
                sys.argv = previous_args

    def test_main_returns_error_for_github_or_llm_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = self._write_config(Path(temp_dir))
            previous_args = sys.argv
            try:
                sys.argv = ["ghe", "--config", str(config_path)]
                with patch(
                    "src.main.GitHubClient",
                    side_effect=GitHubClientError("repository access denied"),
                ), patch("sys.stderr") as stderr:
                    self.assertEqual(main(), 1)
                github_error = "".join(call.args[0] for call in stderr.write.call_args_list)
                self.assertIn("repository access denied", github_error)

                github = Mock()
                github.get_open_issues.return_value = [object()]
                github.get_issue_metrics.return_value = self._issue_payload()
                llm = Mock()
                llm.generate_json.side_effect = LLMClientError("model unavailable")
                with patch("src.main.GitHubClient", return_value=github), patch(
                    "src.main.LLMClient", return_value=llm
                ), patch("sys.stderr") as stderr:
                    self.assertEqual(main(), 1)
                llm_error = "".join(call.args[0] for call in stderr.write.call_args_list)
                self.assertIn("model unavailable", llm_error)
            finally:
                sys.argv = previous_args


if __name__ == "__main__":
    unittest.main()
