"""Unit tests for src/analyzer.py.

The analyzer's contract is small: pick candidates by signal, cluster titles,
call the LLM once, validate the response, and re-anchor title/URL to
ground-truth GitHub data so the report cannot be tricked by the model.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from src.analyzer import AnalyzerError, IssueAnalyzer
from src.memory_manager import DecisionMemory
from src.models import DecisionRecord, IssueMetrics, IssuePriority


def _issue(
    number: int,
    *,
    title: str = "Login fails on Safari",
    body: str = "Cannot log in via Safari.",
    comments: int = 0,
    reactions: int = 0,
    labels: list[str] | None = None,
    hours_old: int = 48,
) -> IssueMetrics:
    now = datetime.now(timezone.utc) - timedelta(hours=hours_old)
    return IssueMetrics(
        number=number,
        title=title,
        body=body,
        created_at=now,
        updated_at=now,
        comments_count=comments,
        reactions=reactions,
        labels=labels or [],
        url=f"https://github.com/acme/widgets/issues/{number}",
    )


def test_filter_by_age_drops_recent_issues():
    llm = MagicMock()
    analyzer = IssueAnalyzer(llm, min_issue_age_hours=24)
    fresh = _issue(1, hours_old=2)
    stale = _issue(2, hours_old=72)
    kept = analyzer._filter_by_age([fresh, stale])
    assert [i.number for i in kept] == [2]


def test_filter_by_age_disabled_when_zero():
    llm = MagicMock()
    analyzer = IssueAnalyzer(llm, min_issue_age_hours=0)
    issues = [_issue(1, hours_old=0), _issue(2, hours_old=1)]
    assert [i.number for i in analyzer._filter_by_age(issues)] == [1, 2]


def test_select_candidates_ranks_by_signal():
    llm = MagicMock()
    analyzer = IssueAnalyzer(llm, max_issues_for_llm=2)
    issues = [
        _issue(1, comments=0, reactions=0),  # score 0
        _issue(2, comments=10, reactions=5, labels=["bug", "P0"]),  # very high
        _issue(3, comments=2, reactions=0),  # mid
    ]
    picked = analyzer._select_candidates(issues)
    assert [i.number for i in picked] == [2, 3]


def test_find_obvious_clusters_groups_by_title_keyword():
    llm = MagicMock()
    analyzer = IssueAnalyzer(llm)
    issues = [
        _issue(1, title="Login broken on Safari"),
        _issue(2, title="Login broken on Chrome"),
        _issue(3, title="Search box broken"),
    ]
    clusters = analyzer._find_obvious_clusters(issues)
    assert len(clusters) == 1
    assert clusters[0].issue_numbers == [1, 2]
    assert "login" in clusters[0].cluster_name.lower()


def test_calculate_priorities_injects_ground_truth_title_and_url():
    """The model may invent a title; we replace it with the real one."""
    llm = MagicMock()
    llm.generate_json.return_value = {
        "summary": "Top issue is login.",
        "priorities": [
            {
                "issue_number": 42,
                "title": "wrong title from model",
                "priority_score": 9.0,
                "reason": "blocks login",
                "user_impact": "users cannot log in",
                "estimated_effort": "low",
            }
        ],
        "missing_info_issues": [42],
    }
    analyzer = IssueAnalyzer(llm, top_n=3)
    issues = [_issue(42, title="Real title from GitHub")]
    priorities, summary, missing = analyzer._calculate_priorities("acme/widgets", issues, [])
    assert priorities[0].title == "Real title from GitHub"
    assert priorities[0].url == "https://github.com/acme/widgets/issues/42"
    assert summary == "Top issue is login."
    assert missing == [42]


def test_calculate_priorities_sorts_by_score_and_dedupes():
    llm = MagicMock()
    llm.generate_json.return_value = {
        "summary": "",
        "priorities": [
            {
                "issue_number": 1,
                "title": "t1",
                "priority_score": 9.0,
                "reason": "r",
                "user_impact": "u",
                "estimated_effort": "low",
            },
            {
                "issue_number": 1,
                "title": "t1-dup",
                "priority_score": 9.5,
                "reason": "r",
                "user_impact": "u",
                "estimated_effort": "low",
            },
            {
                "issue_number": 2,
                "title": "t2",
                "priority_score": 8.0,
                "reason": "r",
                "user_impact": "u",
                "estimated_effort": "high",
            },
        ],
        "missing_info_issues": [1, 1, 2],
    }
    analyzer = IssueAnalyzer(llm, top_n=3)
    issues = [_issue(1), _issue(2)]
    priorities, _, missing = analyzer._calculate_priorities("acme/widgets", issues, [])
    assert [p.issue_number for p in priorities] == [1, 2]
    assert priorities[0].priority_score == 9.0  # first occurrence wins
    assert missing == [1, 2]


def test_calculate_priorities_raises_on_malformed_payload():
    llm = MagicMock()
    llm.generate_json.return_value = {
        "priorities": [
            {
                "issue_number": "not-an-int",
                "title": "t",
                "priority_score": 5,
                "reason": "r",
                "user_impact": "u",
                "estimated_effort": "low",
            }
        ]
    }
    analyzer = IssueAnalyzer(llm)
    with pytest.raises(AnalyzerError):
        analyzer._calculate_priorities("acme/widgets", [_issue(1)], [])


def test_analyze_returns_empty_brief_when_no_candidates():
    llm = MagicMock()
    analyzer = IssueAnalyzer(llm)
    brief = analyzer.analyze([], "acme/widgets", lookback_days=7)
    assert brief.top_priorities == []
    assert "No open issues" in brief.summary


def test_analyze_filters_rejected_themes_before_llm_call():
    llm = MagicMock()
    llm.generate_json.return_value = {
        "summary": "Only one candidate left.",
        "priorities": [],
        "missing_info_issues": [],
    }
    memory = DecisionMemory(
        records=[
            DecisionRecord(status="rejected", themes=["login"], reason="out of scope")
        ]
    )
    analyzer = IssueAnalyzer(llm, decision_memory=memory, min_issue_age_hours=0)
    issues = [
        _issue(1, title="Login broken"),
        _issue(2, title="Export broken"),
    ]
    analyzer.analyze(issues, "acme/widgets", lookback_days=7)
    # LLM only sees the surviving issue
    assert llm.generate_json.called
    prompt = llm.generate_json.call_args[0][0]
    assert "Export broken" in prompt
    assert "Login broken" not in prompt


def test_truncate_to_prompt_budget_drops_low_signal_candidates():
    llm = MagicMock()
    analyzer = IssueAnalyzer(llm, max_prompt_chars=8_000)
    # 20 large issues; budget only allows a handful.
    issues = [
        _issue(i, title="x" * 200, body="y" * 800) for i in range(20)
    ]
    kept, dropped = analyzer._truncate_to_prompt_budget(issues)
    assert kept
    assert dropped > 0
    assert len(kept) + dropped == 20


def test_analyze_records_token_usage_from_llm_client():
    llm = MagicMock()
    llm.generate_json.return_value = {
        "summary": "s",
        "priorities": [],
        "missing_info_issues": [],
    }
    llm.last_usage = {"prompt_tokens": 1234, "completion_tokens": 56, "total_tokens": 1290}
    analyzer = IssueAnalyzer(llm)
    brief = analyzer.analyze([_issue(1)], "acme/widgets", lookback_days=7)
    assert brief.token_usage == {"prompt_tokens": 1234, "completion_tokens": 56, "total_tokens": 1290}


def test_analyze_handles_missing_or_mock_token_usage():
    llm = MagicMock()
    llm.generate_json.return_value = {
        "summary": "s",
        "priorities": [],
        "missing_info_issues": [],
    }
    # Test fixture accidentally leaks a MagicMock from auto-spec; the analyzer
    # must not crash when extracting usage.
    llm.last_usage = MagicMock()
    analyzer = IssueAnalyzer(llm)
    brief = analyzer.analyze([_issue(1)], "acme/widgets", lookback_days=7)
    assert brief.token_usage == {}


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
