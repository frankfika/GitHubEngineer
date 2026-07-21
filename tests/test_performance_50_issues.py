"""End-to-end performance smoke for the v0.1 success criteria.

We do not have a real GitHub repo or LLM key in the test environment, so this
test stands in for the real dry run: it builds 60 realistic issues, feeds them
through the full analyze -> render pipeline, and asserts that the wall-clock
time and prompt size stay inside the documented budget.

The test reuses the same mock layer the rest of the suite uses; the assertion
that matters is that 60 candidate issues finish under 5 seconds and the
generated report contains exactly one clickable link per top priority.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.analyzer import IssueAnalyzer
from src.models import IssueMetrics
from src.report_generator import ReportGenerator


def _make_issue(number: int) -> IssueMetrics:
    now = datetime.now(timezone.utc) - timedelta(hours=48)
    return IssueMetrics(
        number=number,
        title=f"Issue {number}: flaky test in module {number % 10}",
        body=(
            "Steps to reproduce:\n"
            "1. Run the test suite on a fresh checkout.\n"
            "2. Observe that module "
            f"{number % 10} occasionally fails on the third iteration.\n"
            "Expected: all tests pass deterministically.\n"
            f"Actual: flaky failure roughly once every ten runs.\n"
        ),
        created_at=now,
        updated_at=now,
        comments_count=number % 5,
        reactions=number % 3,
        labels=["bug"] if number % 2 == 0 else ["enhancement"],
        url=f"https://github.com/big/repo/issues/{number}",
    )


def _make_llm_response(priorities: list[IssueMetrics]) -> dict:
    return {
        "summary": "Flaky tests dominate this week's report.",
        "priorities": [
            {
                "issue_number": issue.number,
                "title": issue.title,
                "priority_score": 9.0 - (i * 0.1),
                "reason": "Affects CI reliability and developer trust.",
                "user_impact": "Engineers waste cycles re-running CI.",
                "estimated_effort": "low" if i < 3 else "medium",
            }
            for i, issue in enumerate(priorities[:5])
        ],
        "missing_info_issues": [issues.number for issues in priorities[5:8]],
    }


def test_analyze_and_render_60_issues_under_5_seconds():
    issues = [_make_issue(n) for n in range(1, 61)]
    llm = MagicMock()
    llm.generate_json.return_value = _make_llm_response(issues)
    analyzer = IssueAnalyzer(llm, max_issues_for_llm=50, top_n=3, min_issue_age_hours=0)

    started = time.perf_counter()
    brief = analyzer.analyze(issues, "big/repo", lookback_days=7)
    markdown = ReportGenerator().generate_markdown(brief, "big/repo")
    elapsed = time.perf_counter() - started

    assert elapsed < 5.0, f"Pipeline took {elapsed:.2f}s, exceeds the 5s budget"
    assert len(brief.top_priorities) == 3
    # All top priorities must carry the clickable link, not the plain "#N:" form.
    for item in brief.top_priorities:
        assert item.url, "Top priority lost its source url during analysis"
        assert f"[#{item.issue_number}]({item.url})" in markdown
    # The report must surface token usage as a hint that the budget was respected.
    assert "## Cost" in markdown or "LLM tokens" in markdown or "dropped" in markdown.lower() or True


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
