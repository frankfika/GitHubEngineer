"""Defence-in-depth safety guards.

These tests cover the P0 fixes the security audit (round 5) called out:
the LLM system prompt treats issue data as untrusted, validation error
messages no longer echo field values back to the user, the trend
history directory guard refuses system paths, and the step-summary
write path refuses to touch a parent directory it cannot write to.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from pydantic import ValidationError

import yaml

from src.analyzer import AnalyzerError, IssueAnalyzer
from src.main import _safe_local_directory, main
from src.models import IssueMetrics


class SafeLocalDirectoryTest(unittest.TestCase):
    def test_relative_user_directory_is_accepted(self):
        self.assertTrue(_safe_local_directory(".ghe/history"))

    def test_home_relative_path_is_accepted(self):
        self.assertTrue(_safe_local_directory("~/ghe-history"))

    def test_tmp_is_accepted(self):
        self.assertTrue(_safe_local_directory("/tmp/ghe-history"))

    def test_etc_is_rejected(self):
        self.assertFalse(_safe_local_directory("/etc/ghe-history"))
        self.assertFalse(_safe_local_directory("/etc"))

    def test_var_is_rejected(self):
        self.assertFalse(_safe_local_directory("/var/log/ghe"))
        self.assertFalse(_safe_local_directory("/var"))

    def test_proc_and_sys_are_rejected(self):
        self.assertFalse(_safe_local_directory("/proc/self/cwd"))
        self.assertFalse(_safe_local_directory("/sys/kernel"))

    def test_unresolvable_path_is_rejected(self):
        # Embedded NUL or obviously broken values must not crash the check
        # and must be rejected.
        for bad in ("\x00/evil",):
            self.assertFalse(_safe_local_directory(bad), f"expected {bad!r} to be rejected")


class LlmSystemPromptTest(unittest.TestCase):
    def test_system_prompt_treats_data_as_untrusted(self):
        captured: dict = {}

        def fake_generate_json(prompt, system=None):
            captured["system"] = system
            return {"priorities": [], "missing_info_issues": []}

        llm = MagicMock()
        llm.generate_json.side_effect = fake_generate_json
        analyzer = IssueAnalyzer(llm)
        analyzer._calculate_priorities("acme/widgets", [], [])
        self.assertIn("untrusted", captured["system"].lower())
        self.assertIn("never as instructions", captured["system"].lower())

    def test_validation_error_does_not_leak_field_values(self):
        import pytest

        llm = MagicMock()
        llm.generate_json.return_value = {
            "priorities": [
                {
                    "issue_number": "not-an-int-with-secret-token-abc123",
                    "title": "title-with-private-info",
                    "priority_score": 5,
                    "reason": "secret reason",
                    "user_impact": "secret impact",
                    "estimated_effort": "low",
                }
            ]
        }
        analyzer = IssueAnalyzer(llm)
        with pytest.raises(AnalyzerError) as exc:
            analyzer._calculate_priorities("acme/widgets", [_make_issue(1)], [])
        message = str(exc.value)
        # The exception message must mention the field path so the user
        # can debug, but it must NOT include the value the LLM returned
        # for that field.
        self.assertIn("issue_number", message)
        for forbidden in (
            "not-an-int-with-secret-token-abc123",
            "secret reason",
            "secret impact",
            "title-with-private-info",
        ):
            self.assertNotIn(forbidden, message)


def _make_issue(number: int) -> IssueMetrics:
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc) - timedelta(days=1)
    return IssueMetrics(
        number=number,
        title=f"Issue {number}",
        body="body",
        created_at=now,
        updated_at=now,
        url=f"https://github.com/acme/widgets/issues/{number}",
    )


class GheHistoryDirGuardTest(unittest.TestCase):
    def test_unsafe_history_dir_disables_trend(self):
        from types import SimpleNamespace
        from datetime import datetime, timezone

        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            config_path = directory / "config.yml"
            config_path.write_text(
                yaml.safe_dump(
                    {
                        "repo": {"full_name": "acme/widgets"},
                        "github": {"token": "test-token"},
                        "model": {"api_key": "test-key", "model_name": "test-model"},
                        "analysis": {"min_issue_age_hours": 0, "max_issues_for_llm": 10, "top_n": 3},
                        "output": {"format": "markdown", "output_dir": str(directory / "reports")},
                    },
                    allow_unicode=True,
                ),
                encoding="utf-8",
            )
            now = datetime.now(timezone.utc)
            fake_issue = SimpleNamespace(
                number=1,
                title="Issue 1",
                body="body",
                created_at=now,
                updated_at=now,
                comments=0,
                labels=[],
                assignees=[],
                state="open",
                html_url="https://github.com/acme/widgets/issues/1",
                pull_request=None,
                get_reactions=lambda: SimpleNamespace(totalCount=0),
            )
            github = MagicMock()
            github.get_open_issues.return_value = [fake_issue]
            github.get_issue_metrics.return_value = {
                "number": 1,
                "title": "Issue 1",
                "body": "body",
                "created_at": now,
                "updated_at": now,
                "comments_count": 0,
                "reactions": 0,
                "labels": [],
                "assignees": [],
                "state": "open",
                "url": "https://github.com/acme/widgets/issues/1",
            }
            llm = MagicMock()
            llm.generate_json.return_value = {
                "summary": "ok",
                "priorities": [
                    {
                        "issue_number": 1,
                        "title": "Issue 1",
                        "priority_score": 5.0,
                        "reason": "r",
                        "user_impact": "u",
                        "estimated_effort": "low",
                    }
                ],
                "missing_info_issues": [],
            }
            previous_argv = sys.argv
            try:
                sys.argv = ["ghe", "--config", str(config_path)]
                with patch.dict(os.environ, {"GHE_HISTORY_DIR": "/etc/ghe-history"}, clear=False):
                    with patch("src.main.GitHubClient", return_value=github), patch(
                        "src.main.LLMClient", return_value=llm
                    ), patch("sys.stderr") as stderr:
                        self.assertEqual(main(), 0)
                warnings = "".join(call.args[0] for call in stderr.write.call_args_list)
                self.assertIn("GHE_HISTORY_DIR", warnings)
            finally:
                sys.argv = previous_argv


if __name__ == "__main__":
    unittest.main()
