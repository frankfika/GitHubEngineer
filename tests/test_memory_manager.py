"""Unit tests for src/memory_manager.py.

``DecisionMemory`` is the persistence layer that keeps a maintainer from
being recommended the same theme twice. These tests cover the load, save,
filter, and prompt-context code paths end-to-end.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from src.memory_manager import DecisionMemory, DecisionMemoryError
from src.models import DecisionRecord, IssueMetrics


def _issue(number: int, *, title: str = "Login broken", body: str = "", labels: list[str] | None = None) -> IssueMetrics:
    return IssueMetrics(
        number=number,
        title=title,
        body=body,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        labels=labels or [],
        url=f"https://github.com/acme/widgets/issues/{number}",
    )


def test_load_returns_empty_memory_when_file_missing(tmp_path: Path):
    memory = DecisionMemory.load(tmp_path / "nope.yml")
    assert memory.records == []


def test_load_parses_existing_yaml(tmp_path: Path):
    path = tmp_path / "decisions.yml"
    path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "decisions": [
                    {
                        "status": "rejected",
                        "reason": "out of scope",
                        "themes": ["dark mode"],
                    }
                ],
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    memory = DecisionMemory.load(path)
    assert len(memory.records) == 1
    assert memory.records[0].status == "rejected"


def test_load_accepts_legacy_field_aliases(tmp_path: Path):
    path = tmp_path / "decisions.yml"
    path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "decisions": [
                    {
                        "status": "rejected",
                        "issue_number": 42,
                        "forbidden_topics": ["charts"],
                    }
                ],
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    memory = DecisionMemory.load(path)
    record = memory.records[0]
    assert record.issue_numbers == [42]
    assert record.guardrails == ["charts"]


def test_load_raises_on_corrupt_yaml(tmp_path: Path):
    path = tmp_path / "decisions.yml"
    path.write_text("decisions: not-a-list", encoding="utf-8")
    with pytest.raises(DecisionMemoryError):
        DecisionMemory.load(path)


def test_save_is_atomic_and_round_trips(tmp_path: Path):
    path = tmp_path / "decisions.yml"
    memory = DecisionMemory(path=path)
    memory.record_decision(
        DecisionRecord(
            status="rejected",
            reason="noise",
            themes=["dark mode"],
        )
    )
    reloaded = DecisionMemory.load(path)
    assert len(reloaded.records) == 1
    assert reloaded.records[0].status == "rejected"


def test_filter_issues_drops_rejected_numbers_and_themes():
    memory = DecisionMemory(
        records=[
            DecisionRecord(status="rejected", issue_numbers=[10]),
            DecisionRecord(status="rejected", themes=["login"]),
        ]
    )
    issues = [
        _issue(10, title="anything"),
        _issue(11, title="Login broken"),
        _issue(12, title="Search broken"),
    ]
    kept = memory.filter_issues(issues)
    assert [i.number for i in kept] == [12]


def test_prompt_context_collects_unique_goals_and_guardrails():
    memory = DecisionMemory(
        records=[
            DecisionRecord(status="accepted", goals=["reliability", "reliability"], guardrails=["no new deps"]),
            DecisionRecord(status="deferred", themes=["auth"], reason="later"),
            DecisionRecord(status="rejected", guardrails=["no new deps"]),
        ]
    )
    context = memory.prompt_context()
    assert "reliability" in context["goals"]
    assert "no new deps" in context["guardrails"]
    assert any("later" in entry for entry in context["deferred_context"])


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
