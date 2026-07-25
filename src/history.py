"""Persist and compare MaintainerBriefs across runs to expose week-over-week trend.

History is a small, versioned JSON store.  Each run writes a single
``<date>__<repo>.json`` file under ``.ghe/history/``; loading reads the most
recent file for the same repository and returns a diff summary.

The history layer is intentionally side-effect free on read and writes are
explicit.  This keeps it safe to share via PR or to inspect with plain tools.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class HistoryError(RuntimeError):
    """Raised when a history file cannot be read or written safely."""


class HistoryRecord(BaseModel):
    """A single persisted brief snapshot."""

    repo_full_name: str
    generated_at: datetime
    top_issue_numbers: list[int] = Field(default_factory=list)
    top_issue_scores: dict[str, float] = Field(default_factory=dict)
    cluster_names: list[str] = Field(default_factory=list)
    new_issues_count: int = 0


class TrendDiff(BaseModel):
    """Comparison between the latest history and the current run."""

    prior_generated_at: datetime | None = None
    new_issue_numbers: list[int] = Field(default_factory=list)
    resolved_issue_numbers: list[int] = Field(default_factory=list)
    score_changes: dict[str, float] = Field(default_factory=dict)
    new_cluster_names: list[str] = Field(default_factory=list)
    dropped_cluster_names: list[str] = Field(default_factory=list)

    def summary(self, current_count: int) -> str:
        """Return a short, human-readable trend paragraph."""

        if self.prior_generated_at is None:
            return (
                f"No prior baseline for this repository. "
                f"This brief covers {current_count} candidate issues for the first time."
            )
        prior_date = self.prior_generated_at.isoformat()
        parts: list[str] = [f"Compared with the {prior_date} brief:"]
        if self.new_issue_numbers:
            parts.append(
                f"{len(self.new_issue_numbers)} new issue(s) entered the Top N "
                f"({', '.join(f'#{n}' for n in self.new_issue_numbers[:5])})."
            )
        if self.resolved_issue_numbers:
            parts.append(
                f"{len(self.resolved_issue_numbers)} previously recommended issue(s) "
                f"are no longer in the Top N ({', '.join(f'#{n}' for n in self.resolved_issue_numbers[:5])})."
            )
        if self.score_changes:
            sample = next(iter(self.score_changes.items()))
            parts.append(
                f"{len(self.score_changes)} issue(s) shifted in score; "
                f"e.g. issue {sample[0]} moved to {sample[1]:.1f}/10."
            )
        if self.new_cluster_names:
            parts.append(
                f"New cluster(s): {', '.join(self.new_cluster_names[:3])}."
            )
        if self.dropped_cluster_names:
            parts.append(
                f"Cluster(s) that dropped off: {', '.join(self.dropped_cluster_names[:3])}."
            )
        if len(parts) == 1:
            parts.append("No change in Top N or cluster composition.")
        return " ".join(parts)


def save_history(directory: str | Path, record: HistoryRecord) -> Path:
    """Persist ``record`` under ``directory`` and return the written file path."""

    base = Path(directory)
    try:
        base.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise HistoryError(f"Unable to create history directory {base}: {exc}") from exc
    safe_repo = record.repo_full_name.replace("/", "_")
    file_name = f"{record.generated_at.strftime('%Y-%m-%d_%H%M%S')}__{safe_repo}.json"
    target = base / file_name
    try:
        temporary = target.with_suffix(target.suffix + ".tmp")
        payload = record.model_dump(mode="json")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=False)
        import os

        os.replace(temporary, target)
    except OSError as exc:
        raise HistoryError(f"Unable to write history file {target}: {exc}") from exc
    return target


def load_latest(directory: str | Path, repo_full_name: str) -> HistoryRecord | None:
    """Return the most recent history record for ``repo_full_name`` or ``None``."""

    base = Path(directory)
    if not base.exists():
        return None
    safe_repo = repo_full_name.replace("/", "_")
    candidates = sorted(
        base.glob(f"*__{safe_repo}.json"),
        key=lambda path: path.name,
        reverse=True,
    )
    for path in candidates:
        try:
            with path.open("r", encoding="utf-8") as handle:
                raw: Any = json.load(handle)
        except (OSError, json.JSONDecodeError):
            # Skip unreadable or corrupt history files silently; the next
            # candidate may still be valid.
            continue
        if not isinstance(raw, dict):
            continue
        try:
            return HistoryRecord(**raw)
        except (TypeError, ValueError):
            continue
    return None


def aggregate_window(
    directory: str | Path, repo_full_name: str, *, days: int
) -> dict[str, object]:
    """Aggregate the last ``days`` of history records for one repository.

    Returns a shape ready for a trend chart: per-day counts of
    ``new_issues``, ``top_issues`` (sum across snapshots), and the
    list of clusters seen in the window. Corrupt or partial records
    are skipped silently — the trend endpoint is best-effort and
    should never raise.
    """

    from datetime import datetime, timedelta, timezone

    base = Path(directory)
    if not base.exists():
        return {
            "repo": repo_full_name,
            "range_days": days,
            "days": [],
            "total_runs": 0,
            "new_issues": 0,
            "clusters": [],
        }
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    records: list[HistoryRecord] = []
    for path in base.glob("*__*.json"):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            record = HistoryRecord(**raw)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            continue
        if record.repo_full_name != repo_full_name:
            continue
        if record.generated_at and record.generated_at < cutoff:
            continue
        records.append(record)
    records.sort(key=lambda record: record.generated_at)
    by_day: dict[str, dict[str, int]] = {}
    seen_clusters: set[str] = set()
    for record in records:
        day = record.generated_at.date().isoformat() if record.generated_at else "unknown"
        bucket = by_day.setdefault(
            day, {"new_issues": 0, "top_issues": 0, "runs": 0}
        )
        bucket["new_issues"] += record.new_issues_count
        bucket["top_issues"] += len(record.top_issue_numbers)
        bucket["runs"] += 1
        seen_clusters.update(record.cluster_names)
    days_list = [
        {"date": day, **counts} for day, counts in sorted(by_day.items())
    ]
    return {
        "repo": repo_full_name,
        "range_days": days,
        "days": days_list,
        "total_runs": len(records),
        "new_issues": sum(item["new_issues"] for item in days_list),
        "clusters": sorted(seen_clusters),
    }


def compute_diff(prior: HistoryRecord, current: HistoryRecord) -> TrendDiff:
    """Return a :class:`TrendDiff` comparing ``prior`` to ``current``."""

    prior_numbers = set(prior.top_issue_numbers)
    current_numbers = set(current.top_issue_numbers)
    new_issue_numbers = sorted(current_numbers - prior_numbers)
    resolved_issue_numbers = sorted(prior_numbers - current_numbers)
    score_changes: dict[str, float] = {}
    for key, score in current.top_issue_scores.items():
        prior_score = prior.top_issue_scores.get(key)
        if prior_score is None or abs(prior_score - score) > 0.01:
            score_changes[key] = score
    prior_clusters = set(prior.cluster_names)
    current_clusters = set(current.cluster_names)
    return TrendDiff(
        prior_generated_at=prior.generated_at,
        new_issue_numbers=new_issue_numbers,
        resolved_issue_numbers=resolved_issue_numbers,
        score_changes=score_changes,
        new_cluster_names=sorted(current_clusters - prior_clusters),
        dropped_cluster_names=sorted(prior_clusters - current_clusters),
    )


def record_from_brief(
    repo_full_name: str,
    generated_at: datetime,
    top_issue_numbers: list[int],
    top_issue_scores: dict[str, float],
    cluster_names: list[str],
    new_issues_count: int,
) -> HistoryRecord:
    """Build a :class:`HistoryRecord` from the bits of a brief we persist."""

    return HistoryRecord(
        repo_full_name=repo_full_name,
        generated_at=generated_at or datetime.now(timezone.utc),
        top_issue_numbers=top_issue_numbers,
        top_issue_scores=top_issue_scores,
        cluster_names=cluster_names,
        new_issues_count=new_issues_count,
    )
