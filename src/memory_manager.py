"""Explicit, local persistence for maintainer decisions.

Reading decision memory is deliberately side-effect free.  Call
``record_decision`` or ``save`` from a user-driven workflow to write it.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable

import yaml
from pydantic import ValidationError

from .models import DecisionRecord, IssueMetrics


class DecisionMemoryError(RuntimeError):
    """Raised when decision memory cannot be parsed or persisted safely."""


class DecisionMemory:
    """Read and explicitly persist accepted, rejected, and deferred decisions."""

    def __init__(self, records: Iterable[DecisionRecord] = (), path: str | Path = ".ghe/memory/decisions.yml"):
        self.path = Path(path)
        self.records = list(records)

    @classmethod
    def load(cls, path: str | Path = ".ghe/memory/decisions.yml") -> "DecisionMemory":
        """Read memory without creating files or changing its contents.

        A missing file is treated as an empty memory.  YAML is loaded with
        ``safe_load`` and malformed content produces a clear domain error.
        """

        memory_path = Path(path)
        if not memory_path.exists():
            return cls(path=memory_path)
        try:
            with memory_path.open("r", encoding="utf-8") as handle:
                raw = yaml.safe_load(handle) or {}
        except (OSError, yaml.YAMLError) as exc:
            raise DecisionMemoryError(f"Unable to read decision memory at {memory_path}: {exc}") from exc

        if not isinstance(raw, dict):
            raise DecisionMemoryError("Decision memory root must be a mapping.")
        raw_records = raw.get("decisions", [])
        if not isinstance(raw_records, list):
            raise DecisionMemoryError("Decision memory 'decisions' must be a list.")

        records: list[DecisionRecord] = []
        for index, raw_record in enumerate(raw_records):
            if not isinstance(raw_record, dict):
                raise DecisionMemoryError(f"Decision at index {index} must be a mapping.")
            try:
                records.append(DecisionRecord(**cls._normalise_record(raw_record)))
            except ValidationError as exc:
                raise DecisionMemoryError(f"Invalid decision at index {index}: {exc}") from exc
        return cls(records=records, path=memory_path)

    @staticmethod
    def _normalise_record(raw: dict[str, Any]) -> dict[str, Any]:
        """Accept a few intuitive singular/legacy YAML spellings on read."""

        record = dict(raw)
        aliases = {
            "issue_number": "issue_numbers",
            "target": "goals",
            "targets": "goals",
            "forbidden_topics": "guardrails",
            "no_go": "guardrails",
        }
        for source, destination in aliases.items():
            if source in record and destination not in record:
                record[destination] = record.pop(source)
        for key in ("issue_numbers", "themes", "goals", "guardrails"):
            if key in record and not isinstance(record[key], list):
                record[key] = [record[key]]
        return record

    def record_decision(self, decision: DecisionRecord) -> None:
        """Append a decision and persist it. This is an explicit write API."""

        self.records.append(decision)
        self.save()

    def save(self) -> None:
        """Persist current records atomically. This is an explicit write API."""

        payload = {
            "version": 1,
            "decisions": [record.model_dump(mode="json", exclude_none=True) for record in self.records],
        }
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
            with temporary_path.open("w", encoding="utf-8") as handle:
                yaml.safe_dump(payload, handle, allow_unicode=True, sort_keys=False)
            os.replace(temporary_path, self.path)
        except OSError as exc:
            raise DecisionMemoryError(f"Unable to save decision memory at {self.path}: {exc}") from exc

    def filter_issues(self, issues: list[IssueMetrics]) -> list[IssueMetrics]:
        """Exclude issues covered by rejected decisions; retain every other issue."""

        rejected_numbers = {
            number for record in self.records if record.status == "rejected" for number in record.issue_numbers
        }
        rejected_themes = [
            theme.casefold().strip()
            for record in self.records
            if record.status == "rejected"
            for theme in record.themes
            if theme.strip()
        ]
        return [
            issue
            for issue in issues
            if issue.number not in rejected_numbers and not self._matches_theme(issue, rejected_themes)
        ]

    @staticmethod
    def _matches_theme(issue: IssueMetrics, themes: list[str]) -> bool:
        searchable = " ".join([issue.title, issue.body, *issue.labels]).casefold()
        return any(theme in searchable for theme in themes)

    def prompt_context(self) -> dict[str, list[str]]:
        """Return only durable guidance suitable for an LLM prompt."""

        goals = self._unique(
            goal for record in self.records if record.status in {"accepted", "deferred"} for goal in record.goals
        )
        guardrails = self._unique(
            guardrail for record in self.records for guardrail in record.guardrails
        )
        deferred = self._unique(
            f"{', '.join(record.themes) or 'unspecified scope'}: {record.reason}".strip(": ")
            for record in self.records
            if record.status == "deferred"
        )
        return {"goals": goals, "guardrails": guardrails, "deferred_context": deferred}

    @staticmethod
    def _unique(values: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            cleaned = str(value).strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                result.append(cleaned)
        return result
