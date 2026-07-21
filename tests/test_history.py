"""Unit tests for src/history.py."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.history import (
    HistoryError,
    HistoryRecord,
    compute_diff,
    load_latest,
    record_from_brief,
    save_history,
)


def _record(repo: str = "acme/widgets", days_offset: int = 0, **kwargs) -> HistoryRecord:
    base = datetime(2026, 7, 21, tzinfo=timezone.utc) - timedelta(days=days_offset)
    defaults = {
        "repo_full_name": repo,
        "generated_at": base,
        "top_issue_numbers": [1, 2, 3],
        "top_issue_scores": {"#1": 9.0, "#2": 7.5, "#3": 6.0},
        "cluster_names": ["Login"],
        "new_issues_count": 20,
    }
    defaults.update(kwargs)
    return HistoryRecord(**defaults)


def test_save_then_load_returns_latest(tmp_path: Path):
    save_history(tmp_path, _record(days_offset=14))
    save_history(tmp_path, _record(days_offset=7))
    latest = load_latest(tmp_path, "acme/widgets")
    assert latest is not None
    assert latest.generated_at.day == 14


def test_load_latest_returns_none_when_dir_missing(tmp_path: Path):
    assert load_latest(tmp_path / "nope", "acme/widgets") is None


def test_load_latest_skips_corrupt_files(tmp_path: Path):
    save_history(tmp_path, _record())
    # Inject a non-JSON sibling that sorts after the valid one.
    (tmp_path / "9999-12-31_000000__acme_widgets.json").write_text("not json", encoding="utf-8")
    latest = load_latest(tmp_path, "acme/widgets")
    assert latest is not None
    assert latest.top_issue_numbers == [1, 2, 3]


def test_compute_diff_reports_new_and_resolved_issues():
    prior = _record(days_offset=7, top_issue_numbers=[1, 2, 3], top_issue_scores={"#1": 9.0, "#2": 7.0})
    current = _record(
        days_offset=0,
        top_issue_numbers=[1, 4, 5],
        top_issue_scores={"#1": 8.5, "#4": 7.0, "#5": 6.5},
    )
    diff = compute_diff(prior, current)
    assert diff.new_issue_numbers == [4, 5]
    assert diff.resolved_issue_numbers == [2, 3]
    assert "#1" in diff.score_changes  # 9.0 -> 8.5
    summary = diff.summary(current_count=25)
    assert "2026-07-14" in summary  # prior date
    assert "#4" in summary
    assert "#2" in summary


def test_compute_diff_handles_empty_prior():
    diff = compute_diff(_record(), _record())
    # Same set, no movement.
    assert diff.new_issue_numbers == []
    assert diff.resolved_issue_numbers == []
    assert diff.score_changes == {}


def test_summary_when_no_prior():
    diff = compute_diff(_record(), _record())
    diff.prior_generated_at = None
    text = diff.summary(current_count=10)
    assert "first time" in text


def test_record_from_brief_helpers_round_trip(tmp_path: Path):
    record = record_from_brief(
        repo_full_name="acme/widgets",
        generated_at=datetime(2026, 7, 21, tzinfo=timezone.utc),
        top_issue_numbers=[10, 20],
        top_issue_scores={"#10": 9.0, "#20": 7.0},
        cluster_names=["Login"],
        new_issues_count=15,
    )
    save_history(tmp_path, record)
    loaded = load_latest(tmp_path, "acme/widgets")
    assert loaded is not None
    assert loaded.top_issue_numbers == [10, 20]
    assert loaded.new_issues_count == 15


def test_save_history_surfaces_oserror_as_typed(monkeypatch, tmp_path: Path):
    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("os.replace", boom)
    with pytest.raises(HistoryError):
        save_history(tmp_path, _record())


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
