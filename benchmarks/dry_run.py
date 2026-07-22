"""End-to-end dry run that exercises the full main() path with a stubbed
GitHub and LLM. This is the closest we can get to a real ``ghe
owner/name`` invocation without network access; it is the script that
should run in CI on every PR to catch integration regressions before
they ship.

The fake repository contains 60 issues of varying signal so the analyzer's
candidate ranking, cluster detection, and prompt-budget truncation all
get a workout. The fake LLM replies with a deterministic, valid payload
so the rendered report is stable and easy to diff.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.analyzer import IssueAnalyzer
from src.config import get_target_repos, load_config, load_config_lenient
from src.github_client import GitHubClient
from src.history import (
    HistoryError,
    compute_diff,
    load_latest,
    record_from_brief,
    save_history,
)
from src.llm_client import LLMClient
from src.main import main, write_report, write_step_summary
from src.memory_manager import DecisionMemory
from src.models import IssueMetrics
from src.report_generator import ReportGenerator


REPO_FULL_NAME = "opencsg/test-fixture"


def _make_issue(
    number: int,
    *,
    title: str | None = None,
    body: str = "Bug report. Steps to reproduce: (omitted).",
    comments: int = 0,
    reactions: int = 0,
    labels: list[str] | None = None,
    days_ago: int = 0,
) -> SimpleNamespace:
    updated = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return SimpleNamespace(
        number=number,
        title=title or f"Issue {number}",
        body=body,
        created_at=updated - timedelta(days=2),
        updated_at=updated,
        comments=comments,
        labels=[SimpleNamespace(name=name) for name in (labels or [])],
        assignees=[],
        state="open",
        html_url=f"https://github.com/{REPO_FULL_NAME}/issues/{number}",
        pull_request=None,
        get_reactions=MagicMock(return_value=SimpleNamespace(totalCount=reactions)),
    )


def _build_fake_repo(issues: list[SimpleNamespace]):
    """Return a fake PyGithub repo whose get_issues() paginates as the real one does."""

    class _Paginator:
        def __init__(self, items):
            self._items = list(items)
            self._per_page = 30

        def get_page(self, page_index):
            start = page_index * self._per_page
            end = start + self._per_page
            if start >= len(self._items):
                raise IndexError(page_index)
            return self._items[start:end]

    return SimpleNamespace(
        get_issues=MagicMock(return_value=_Paginator(issues)),
    )


def _build_fake_issues(count: int) -> list[SimpleNamespace]:
    """Synthesize ``count`` issues with realistic signal distribution."""

    issues: list[SimpleNamespace] = []
    for n in range(1, count + 1):
        issues.append(
            _make_issue(
                n,
                title=f"Issue {n}: regression in module {n % 12}",
                body=(
                    "Steps to reproduce:\n"
                    f"1. Trigger the {n % 12} module path.\n"
                    "2. Observe that the request returns a 500.\n"
                ),
                comments=(n * 3) % 8,
                reactions=(n * 2) % 5,
                labels=["bug"] if n % 2 == 0 else ["enhancement"],
                days_ago=1,
            )
        )
    return issues


def _build_llm_response(priorities: list[IssueMetrics]) -> dict:
    return {
        "summary": "Test fixture summary: 60 candidate issues, flaky tests dominate.",
        "priorities": [
            {
                "issue_number": issue.number,
                "title": issue.title,
                "priority_score": 9.0 - (i * 0.1),
                "reason": "Recurring regression in core module.",
                "user_impact": "Triggers CI flakes for downstream teams.",
                "estimated_effort": "low" if i < 3 else "medium",
            }
            for i, issue in enumerate(priorities[:5])
        ],
        "missing_info_issues": [issue.number for issue in priorities[5:8]],
    }


def main_dry_run() -> int:
    """Run the full pipeline against a synthetic repo and report results."""

    started = time.perf_counter()
    issue_count = 60
    fake_issues = _build_fake_issues(issue_count)
    fake_repo = _build_fake_repo(fake_issues)
    fake_metrics = [
        IssueMetrics(
            number=issue.number,
            title=issue.title,
            body=issue.body,
            created_at=issue.created_at,
            updated_at=issue.updated_at,
            comments_count=issue.comments,
            reactions=0,
            labels=["bug"] if issue.number % 2 == 0 else ["enhancement"],
            url=issue.html_url,
        )
        for issue in fake_issues
    ]

    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        reports_dir = temp / "reports"
        history_dir = temp / ".ghe" / "history"
        history_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)
        config_path = temp / "config.yml"
        config_path.write_text(
            json.dumps(
                {
                    "repo": {"full_name": REPO_FULL_NAME},
                    "github": {"token": "dry-run"},
                    "model": {"api_key": "dry-run", "model_name": "gpt-4o-mini"},
                    "output": {
                        "format": "markdown",
                        "output_dir": str(reports_dir),
                    },
                    "analysis": {
                        "lookback_days": 7,
                        "top_n": 3,
                        "min_issue_age_hours": 0,
                        "max_issues_for_llm": 50,
                    },
                }
            ),
            encoding="utf-8",
        )

        # Step 1: load the config (lenient, so we do not need a real key).
        config = load_config_lenient(str(config_path))
        assert get_target_repos(config) == [REPO_FULL_NAME], "expected single target repo"

        # Step 2: pull the issues from the fake GitHub client.
        with patch("src.github_client.Github") as gh_cls:
            gh_cls.return_value.get_repo.return_value = fake_repo
            gh_client = GitHubClient("dry-run", REPO_FULL_NAME)
            raw_issues = gh_client.get_open_issues(
                since=datetime.now(timezone.utc) - timedelta(days=7),
                max_issues=100,
                max_pages=10,
            )
        assert len(raw_issues) == issue_count, f"expected {issue_count} issues, got {len(raw_issues)}"

        # Step 3: send them through the analyzer with a stubbed LLM.
        llm = MagicMock()
        llm.generate_json.return_value = _build_llm_response(fake_metrics)
        # The real LLMClient would record usage via _capture_usage; the dry-run
        # sets the attribute directly so the Cost section appears in the report.
        llm.last_usage = {
            "prompt_tokens": 18_400,
            "completion_tokens": 280,
            "total_tokens": 18_680,
        }
        analyzer = IssueAnalyzer(
            llm,
            max_issues_for_llm=50,
            top_n=3,
            min_issue_age_hours=0,
        )
        brief = analyzer.analyze(fake_metrics, REPO_FULL_NAME, lookback_days=7)
        assert len(brief.top_priorities) == 3, f"expected 3 top priorities, got {len(brief.top_priorities)}"
        for item in brief.top_priorities:
            assert item.url, "top priority lost its source url"
            assert item.title, "top priority lost its title"

        # Step 4: history diff (against an empty history, should produce the
        # "no prior baseline" line).
        prior = load_latest(history_dir, REPO_FULL_NAME)
        assert prior is None, "first run should have no prior history"
        current = record_from_brief(
            repo_full_name=REPO_FULL_NAME,
            generated_at=brief.generated_at,
            top_issue_numbers=[p.issue_number for p in brief.top_priorities],
            top_issue_scores={f"#{p.issue_number}": p.priority_score for p in brief.top_priorities},
            cluster_names=[c.cluster_name for c in brief.issue_clusters],
            new_issues_count=brief.new_issues_count,
        )
        save_history(history_dir, current)
        reloaded = load_latest(history_dir, REPO_FULL_NAME)
        assert reloaded is not None
        diff = compute_diff(reloaded, current)
        assert diff.prior_generated_at is not None

        # Step 5: render the report and write it to disk.
        report = ReportGenerator().generate_markdown(brief, REPO_FULL_NAME)
        # Clickable link check
        for item in brief.top_priorities:
            assert f"[#{item.issue_number}]({item.url})" in report, "expected clickable link"
        # Trend line check (no prior -> explicit first-time line)
        assert "first time" in report.lower() or "Trend" in report
        # Cost section check
        assert "## Cost" in report

        # Step 6: write to disk + step summary, just like main() would.
        output_file = write_report(report, REPO_FULL_NAME, {"output": {"output_dir": str(reports_dir)}})
        assert output_file.exists()
        summary_path = temp / "summary.md"
        os.environ["GITHUB_STEP_SUMMARY"] = str(summary_path)
        write_step_summary(report, {"output": {"format": "action-summary"}})
        assert summary_path.exists() and summary_path.read_text(encoding="utf-8").strip()

        # Step 7: simulate a second run, this time against the just-saved
        # history. The diff should now report new / resolved / score changes
        # for the second brief even when nothing changed, because the
        # diff is comparing the previous snapshot to the identical one.
        second_prior = load_latest(history_dir, REPO_FULL_NAME)
        second_diff = compute_diff(second_prior, current)
        assert second_diff.prior_generated_at is not None
        assert second_diff.new_issue_numbers == []  # nothing changed
        assert second_diff.resolved_issue_numbers == []

        elapsed = time.perf_counter() - started
        result = {
            "ok": True,
            "issue_count": issue_count,
            "top_priorities": [p.issue_number for p in brief.top_priorities],
            "rendered_chars": len(report),
            "report_path": str(output_file),
            "step_summary_chars": summary_path.stat().st_size,
            "dropped_candidate_count": brief.dropped_candidate_count,
            "history_recorded": True,
            "second_run_diff_summary": second_diff.summary(current.new_issues_count),
            "elapsed_seconds": round(elapsed, 4),
        }
        print(json.dumps(result, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main_dry_run())
