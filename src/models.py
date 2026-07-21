from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Effort = Literal["low", "medium", "high"]
DecisionStatus = Literal["accepted", "rejected", "deferred"]


class DecisionRecord(BaseModel):
    """A maintainer decision retained between brief generations.

    ``issue_numbers`` and ``themes`` describe the scope of a decision.  Goals
    and guardrails are deliberately separate: the former guide prioritization,
    while the latter tell the model what not to recommend.
    """

    status: DecisionStatus
    reason: str = ""
    issue_numbers: list[int] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class IssueMetrics(BaseModel):
    """Normalized issue data used by the analyzer."""

    number: int
    title: str
    body: str = ""
    created_at: datetime
    updated_at: datetime
    comments_count: int = 0
    reactions: int = 0
    labels: list[str] = Field(default_factory=list)
    assignees: list[str] = Field(default_factory=list)
    state: str = "open"
    url: str


class IssuePriority(BaseModel):
    """A prioritized issue recommendation."""

    issue_number: int
    title: str
    priority_score: float = Field(..., ge=0, le=10)
    reason: str
    user_impact: str
    estimated_effort: Effort = "medium"


class IssueCluster(BaseModel):
    """A group of issues that appear to share the same theme."""

    cluster_name: str
    issue_numbers: list[int]
    common_theme: str


class MaintainerBrief(BaseModel):
    """The final report payload."""

    generated_at: datetime
    period: str
    summary: str
    new_issues_count: int
    top_priorities: list[IssuePriority] = Field(default_factory=list)
    quick_wins: list[IssuePriority] = Field(default_factory=list)
    issue_clusters: list[IssueCluster] = Field(default_factory=list)
    missing_info_issues: list[int] = Field(default_factory=list)
    trend: str = "No prior baseline is available yet."
