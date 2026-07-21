"""Benchmark the analyze -> render pipeline for varying issue counts.

Run via ``make bench`` or directly:

    python benchmarks/perf.py --issues 50 --repeats 3

The script does not call any external LLM or GitHub API; it synthesises
fake issues with realistic signal distributions, runs the full
``IssueAnalyzer.analyze`` -> ``ReportGenerator.generate_markdown`` path
against a stubbed LLM, and prints a row per run with elapsed time and
the truncated candidate count. Use this to spot regressions before
pushing a change.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

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
        "missing_info_issues": [issue.number for issue in priorities[5:8]],
    }


def run_once(issue_count: int) -> tuple[float, int, int]:
    issues = [_make_issue(n) for n in range(1, issue_count + 1)]
    llm = MagicMock()
    llm.generate_json.return_value = _make_llm_response(issues)
    analyzer = IssueAnalyzer(llm, max_issues_for_llm=min(50, issue_count), top_n=3, min_issue_age_hours=0)
    started = time.perf_counter()
    brief = analyzer.analyze(issues, "big/repo", lookback_days=7)
    ReportGenerator().generate_markdown(brief, "big/repo")
    elapsed = time.perf_counter() - started
    return elapsed, len(brief.top_priorities), brief.dropped_candidate_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark the analyze -> render pipeline.")
    parser.add_argument("--issues", type=int, default=50, help="How many issues to synthesize.")
    parser.add_argument("--repeats", type=int, default=3, help="How many runs to average over.")
    args = parser.parse_args()

    samples: list[float] = []
    top_n = 0
    dropped = 0
    for _ in range(args.repeats):
        elapsed, top_n, dropped = run_once(args.issues)
        samples.append(elapsed)

    result = {
        "issues": args.issues,
        "repeats": args.repeats,
        "elapsed_seconds": {
            "min": round(min(samples), 4),
            "median": round(statistics.median(samples), 4),
            "mean": round(statistics.mean(samples), 4),
            "max": round(max(samples), 4),
        },
        "top_n": top_n,
        "dropped_candidate_count": dropped,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
