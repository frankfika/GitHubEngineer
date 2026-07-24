from __future__ import annotations

import subprocess
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

    @staticmethod
    def resolve_token(configured_token: str | None = None) -> str | None:
        """Resolve GitHub auth without ever printing or logging the credential.

        Desktop users commonly authenticate with ``gh auth login`` rather than
        exporting ``GITHUB_TOKEN`` in every graphical session.  Prefer an
        explicitly configured token, then fall back to the credential already
        held by the official GitHub CLI.
        """

        if configured_token:
            return configured_token
        try:
            result = subprocess.run(
                ["gh", "auth", "token"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        token = result.stdout.strip()
        return token if result.returncode == 0 and token else None

    @classmethod
    def list_owned_repositories(
        cls, token: str | None, *, max_repositories: int = 100
    ) -> tuple[str, list[dict[str, Any]]]:
        """Return repositories owned by the authenticated GitHub user."""

        if not token:
            raise GitHubClientError(
                "GitHub login is required. Run `gh auth login` or set GITHUB_TOKEN."
            )
        try:
            github = Github(token)
            user = github.get_user()
            repositories = user.get_repos(
                affiliation="owner",
                sort="updated",
                direction="desc",
            )
            open_issue_counts: dict[str, int] = {}
            for issue in github.search_issues(
                query=f"user:{user.login} is:issue is:open",
                sort="updated",
                order="desc",
            ):
                full_name = issue.repository.full_name
                open_issue_counts[full_name] = open_issue_counts.get(full_name, 0) + 1
            result: list[dict[str, Any]] = []
            for repository in repositories:
                result.append(
                    {
                        "full_name": repository.full_name,
                        "name": repository.name,
                        "owner": repository.owner.login,
                        "private": bool(repository.private),
                        "archived": bool(repository.archived),
                        "open_issues_count": open_issue_counts.get(repository.full_name, 0),
                        "stars": int(repository.stargazers_count),
                        "forks": int(repository.forks_count),
                        # ``subscribers_count`` is not part of GitHub's list
                        # response and would trigger one extra API call per
                        # repository. The selected repository profile fills it.
                        "followers": None,
                        "language": repository.language,
                        "description": repository.description or "",
                        "updated_at": repository.updated_at.isoformat(),
                        "pushed_at": repository.pushed_at.isoformat()
                        if repository.pushed_at
                        else None,
                        "url": repository.html_url,
                        "access": "owner",
                    }
                )
                if len(result) >= max_repositories:
                    break
            return user.login, result
        except RateLimitExceededException as exc:
            raise GitHubClientError("GitHub API rate limit exceeded.") from exc
        except GithubException as exc:
            raise GitHubClientError(f"Failed to list owned repositories: {exc}") from exc

    @classmethod
    def get_authenticated_login(cls, token: str | None) -> str:
        """Return the current GitHub login without enumerating repositories."""

        if not token:
            raise GitHubClientError(
                "GitHub login is required. Run `gh auth login` or set GITHUB_TOKEN."
            )
        try:
            return str(Github(token).get_user().login)
        except RateLimitExceededException as exc:
            raise GitHubClientError("GitHub API rate limit exceeded.") from exc
        except GithubException as exc:
            raise GitHubClientError(f"Failed to read GitHub account: {exc}") from exc

    def get_open_issues(
        self,
        since: datetime | None = None,
        max_issues: int = 100,
        max_pages: int = 10,
    ) -> list[Any]:
        """Return open issues, excluding pull requests.

        ``max_pages`` caps the number of GitHub paginated requests we make so
        that 100k+ issue repositories do not exhaust the API quota. PyGithub
        fetches pages lazily as we iterate, so we walk them explicitly.
        """

        try:
            issues = self.repo.get_issues(
                state="open",
                sort="updated",
                direction="desc",
            )
            result: list[Any] = []
            for page_index in range(max_pages):
                try:
                    page = issues.get_page(page_index)
                except IndexError:
                    # Past the last page.
                    break
                for issue in page:
                    if issue.pull_request:
                        continue
                    updated_at = issue.updated_at
                    if updated_at.tzinfo is None:
                        updated_at = updated_at.replace(tzinfo=timezone.utc)
                    if since and updated_at < since:
                        # Issues on this page are sorted by updated_at desc, so
                        # everything after this is also older than ``since``.
                        return result
                    result.append(issue)
                    if len(result) >= max_issues:
                        return result
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

    def get_issue_summaries(self, *, max_issues: int = 60) -> list[dict[str, Any]]:
        """Return lightweight Issue rows for the desktop daily inbox."""

        raw_issues = self.get_open_issues(max_issues=max_issues, max_pages=4)
        return [
            {
                "number": issue.number,
                "title": issue.title,
                "body": (issue.body or "")[:4_000],
                "created_at": issue.created_at.isoformat(),
                "updated_at": issue.updated_at.isoformat(),
                "comments_count": int(issue.comments),
                "labels": [label.name for label in issue.labels],
                "assignees": [assignee.login for assignee in issue.assignees],
                "state": issue.state,
                "url": issue.html_url,
            }
            for issue in raw_issues
        ]

    def get_issue_summary(self, issue_number: int) -> dict[str, Any]:
        """Return one Issue for a local task draft."""

        try:
            issue = self.repo.get_issue(number=issue_number)
        except GithubException as exc:
            raise GitHubClientError(f"Could not access issue #{issue_number}: {exc}") from exc
        if issue.pull_request:
            raise GitHubClientError(f"#{issue_number} is a pull request, not an issue.")
        return {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body or "",
            "created_at": issue.created_at.isoformat(),
            "updated_at": issue.updated_at.isoformat(),
            "comments_count": int(issue.comments),
            "labels": [label.name for label in issue.labels],
            "assignees": [assignee.login for assignee in issue.assignees],
            "state": issue.state,
            "url": issue.html_url,
        }

    def get_repository_profile(self) -> dict[str, Any]:
        """Return stable repository metadata used by daily monitoring."""

        repository = self.repo
        return {
            "full_name": repository.full_name,
            "name": repository.name,
            "owner": repository.owner.login,
            "private": bool(repository.private),
            "archived": bool(repository.archived),
            "stars": int(repository.stargazers_count),
            "forks": int(repository.forks_count),
            "followers": int(getattr(repository, "subscribers_count", 0) or 0),
            "language": repository.language,
            "description": repository.description or "",
            "default_branch": repository.default_branch,
            "updated_at": repository.updated_at.isoformat(),
            "pushed_at": repository.pushed_at.isoformat()
            if repository.pushed_at
            else None,
            "url": repository.html_url,
        }
