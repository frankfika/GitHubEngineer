from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from github import Github, GithubException, RateLimitExceededException


class GitHubClientError(RuntimeError):
    """Raised when GitHub API access fails."""


class GitHubClient:
    """Small wrapper around PyGithub for read-only issue access."""

    def __init__(self, token: str | None, repo_full_name: str):
        self.gh = Github(token) if token else Github()
        try:
            self.repo = self.gh.get_repo(repo_full_name)
        except GithubException as exc:
            raise GitHubClientError(f"Could not access repository {repo_full_name}: {exc}") from exc

    def get_open_issues(
        self,
        since: datetime | None = None,
        max_issues: int = 100,
    ) -> list[Any]:
        """Return open issues, excluding pull requests."""

        try:
            issues = self.repo.get_issues(state="open", sort="updated", direction="desc")
            result = []
            for issue in issues:
                if issue.pull_request:
                    continue
                updated_at = issue.updated_at
                if updated_at.tzinfo is None:
                    updated_at = updated_at.replace(tzinfo=timezone.utc)
                if since and updated_at < since:
                    continue
                result.append(issue)
                if len(result) >= max_issues:
                    break
            return result
        except RateLimitExceededException as exc:
            raise GitHubClientError("GitHub API rate limit exceeded.") from exc
        except GithubException as exc:
            raise GitHubClientError(f"Failed to fetch issues: {exc}") from exc

    def get_issue_metrics(self, issue: Any) -> dict[str, Any]:
        """Extract the fields needed by the analyzer."""

        reactions = 0
        try:
            reactions = issue.get_reactions().totalCount
        except GithubException:
            reactions = 0

        return {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body or "",
            "created_at": issue.created_at,
            "updated_at": issue.updated_at,
            "comments_count": issue.comments,
            "reactions": reactions,
            "labels": [label.name for label in issue.labels],
            "assignees": [assignee.login for assignee in issue.assignees],
            "state": issue.state,
            "url": issue.html_url,
        }
