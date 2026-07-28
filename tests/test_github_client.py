"""Unit tests for src/github_client.py.

These tests mock PyGithub at the module boundary so they run offline and
exercise the real pagination, rate-limit, and metric-extraction code paths
that were previously only covered indirectly by main_integration.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.github_client import GitHubClient, GitHubClientError


def _make_issue(number: int, *, is_pr: bool = False, days_ago: int = 0):
    """Build a fake PyGithub Issue with the attributes the client reads."""
    now = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return SimpleNamespace(
        number=number,
        title=f"Issue {number}",
        body=f"Body of issue {number}",
        created_at=now,
        updated_at=now,
        comments=2,
        labels=[SimpleNamespace(name="bug")],
        assignees=[],
        state="open",
        html_url=f"https://github.com/acme/widgets/issues/{number}",
        _rawData={"pull_request": {}} if is_pr else {},
        pull_request=SimpleNamespace() if is_pr else None,
        get_reactions=MagicMock(return_value=SimpleNamespace(totalCount=5)),
    )


def _make_repo(issues):
    """Build a fake repo whose get_issues() returns a controllable paginator."""

    class _Paginator:
        def __init__(self, items):
            self._items = list(items)
            self._index = 0

        def get_page(self, page_index):
            # PyGithub semantics: each page is 30 items by default. We send
            # all items on page 0 and raise IndexError on later pages.
            if page_index == 0:
                return self._items
            raise IndexError(page_index)

    return SimpleNamespace(get_issues=MagicMock(return_value=_Paginator(issues)))


def test_get_open_issues_filters_prs_and_respects_max_issues():
    repo = _make_repo(
        [_make_issue(1), _make_issue(2, is_pr=True), _make_issue(3), _make_issue(4)]
    )
    with patch("src.github_client.Github") as gh_cls:
        gh_cls.return_value.get_repo.return_value = repo
        client = GitHubClient("token", "acme/widgets")
        result = client.get_open_issues(max_issues=10)
    assert [issue.number for issue in result] == [1, 3, 4]


def test_get_open_issues_respects_since_and_short_circuits_pagination():
    """When the first page is already older than ``since`` we must stop walking pages."""
    repo = _make_repo([_make_issue(1, days_ago=30), _make_issue(2, days_ago=60)])
    with patch("src.github_client.Github") as gh_cls:
        gh_cls.return_value.get_repo.return_value = repo
        client = GitHubClient("token", "acme/widgets")
        recent_only = client.get_open_issues(
            since=datetime.now(timezone.utc) - timedelta(days=7),
            max_pages=5,
        )
    assert recent_only == []


def test_get_open_issues_caps_pages_to_protect_large_repositories():
    """The fake repo only has page 0; max_pages=1 must not loop or error."""
    repo = _make_repo([_make_issue(1)])
    with patch("src.github_client.Github") as gh_cls:
        gh_cls.return_value.get_repo.return_value = repo
        client = GitHubClient("token", "acme/widgets")
        result = client.get_open_issues(max_pages=1)
    assert len(result) == 1


def test_get_open_issues_stops_after_empty_page():
    """A real PyGithub paginator returns [] after its final page."""

    class _Paginator:
        def __init__(self):
            self.requested_pages = []

        def get_page(self, page_index):
            self.requested_pages.append(page_index)
            if page_index == 0:
                return [_make_issue(1)]
            if page_index == 1:
                return []
            raise AssertionError("pagination continued after an empty page")

    paginator = _Paginator()
    repo = SimpleNamespace(get_issues=MagicMock(return_value=paginator))
    with patch("src.github_client.Github") as gh_cls:
        gh_cls.return_value.get_repo.return_value = repo
        client = GitHubClient("token", "acme/widgets")
        result = client.get_open_issues(max_pages=10)
    assert [issue.number for issue in result] == [1]
    assert paginator.requested_pages == [0, 1]


def test_get_open_issues_does_not_lazy_load_each_issue_to_filter_prs():
    """Filtering list results must not access PyGithub's lazy PR property."""

    class _LazyIssue:
        def __init__(self, number, *, is_pr=False):
            base = _make_issue(number, is_pr=is_pr)
            self.__dict__.update(base.__dict__)
            self._pull_request_accessed = False

        @property
        def pull_request(self):
            self._pull_request_accessed = True
            raise AssertionError("pull_request triggered a detail request")

    issue = _LazyIssue(1)
    pull_request = _LazyIssue(2, is_pr=True)
    repo = _make_repo([issue, pull_request])
    with patch("src.github_client.Github") as gh_cls:
        gh_cls.return_value.get_repo.return_value = repo
        client = GitHubClient("token", "acme/widgets")
        result = client.get_open_issues()
    assert [item.number for item in result] == [1]
    assert issue._pull_request_accessed is False
    assert pull_request._pull_request_accessed is False


def test_get_issue_metrics_handles_reaction_failure():
    from github import GithubException

    issue = _make_issue(7)
    issue.get_reactions.side_effect = GithubException(403, "rate limited", None)
    repo = _make_repo([])
    with patch("src.github_client.Github") as gh_cls:
        gh_cls.return_value.get_repo.return_value = repo
        client = GitHubClient("token", "acme/widgets")
        metrics = client.get_issue_metrics(issue)
    assert metrics["number"] == 7
    assert metrics["reactions"] == 0
    assert metrics["url"].endswith("/7")
    assert "bug" in metrics["labels"]


def test_get_repo_failure_surfaces_as_typed_error():
    from github import GithubException

    with patch("src.github_client.Github") as gh_cls:
        gh_cls.return_value.get_repo.side_effect = GithubException(404, "Not Found", None)
        with pytest.raises(GitHubClientError) as exc:
            GitHubClient(None, "missing/repo")
    assert "missing/repo" in str(exc.value)


def test_get_issue_summary_includes_bounded_untrusted_comments():
    issue = _make_issue(8)
    issue.comments = 25
    issue.get_comments = MagicMock(
        return_value=[
            SimpleNamespace(
                body=("comment " + str(index) + " ") * 500,
                user=SimpleNamespace(login=f"user{index}"),
                created_at=datetime.now(timezone.utc),
            )
            for index in range(25)
        ]
    )
    repo = SimpleNamespace(get_issue=MagicMock(return_value=issue))
    with patch("src.github_client.Github") as gh_cls:
        gh_cls.return_value.get_repo.return_value = repo
        summary = GitHubClient("token", "acme/widgets").get_issue_summary(8)

    assert len(summary["comments"]) <= 20
    assert sum(len(item["body"]) for item in summary["comments"]) <= 12_000
    assert all(item["trust"] == "untrusted_user_input" for item in summary["comments"])
    assert summary["comments_truncated"] is True


def test_resolve_token_prefers_configured_value_without_shelling_out():
    with patch("src.github_client.subprocess.run") as run:
        assert GitHubClient.resolve_token("configured") == "configured"
    run.assert_not_called()


def test_resolve_token_uses_existing_gh_cli_login():
    result = SimpleNamespace(returncode=0, stdout="secret-from-keyring\n")
    with patch("src.github_client.subprocess.run", return_value=result) as run:
        token = GitHubClient.resolve_token()
    assert token == "secret-from-keyring"
    run.assert_called_once()


def test_list_owned_repositories_returns_desktop_switcher_fields():
    updated_at = datetime.now(timezone.utc)
    repository = SimpleNamespace(
        full_name="alice/project",
        name="project",
        owner=SimpleNamespace(login="alice"),
        private=True,
        archived=False,
        open_issues_count=4,
        stargazers_count=12,
        forks_count=3,
        subscribers_count=2,
        language="Python",
        description="Demo",
        updated_at=updated_at,
        pushed_at=updated_at,
        html_url="https://github.com/alice/project",
    )
    user = SimpleNamespace(
        login="alice",
        get_repos=MagicMock(return_value=[repository]),
    )
    with patch("src.github_client.Github") as gh_cls:
        gh_cls.return_value.get_user.return_value = user
        gh_cls.return_value.search_issues.return_value = [
            SimpleNamespace(repository=SimpleNamespace(full_name="alice/project"))
        ]
        login, repositories = GitHubClient.list_owned_repositories("token")
    assert login == "alice"
    assert repositories[0]["full_name"] == "alice/project"
    assert repositories[0]["private"] is True
    assert repositories[0]["open_issues_count"] == 1
    assert repositories[0]["stars"] == 12
    assert repositories[0]["followers"] is None


def test_get_authenticated_login_does_not_enumerate_repositories():
    user = SimpleNamespace(login="alice", get_repos=MagicMock())
    with patch("src.github_client.Github") as gh_cls:
        gh_cls.return_value.get_user.return_value = user
        assert GitHubClient.get_authenticated_login("token") == "alice"
    user.get_repos.assert_not_called()


def test_get_issue_summaries_avoids_reaction_api_calls():
    issue = _make_issue(9)
    repo = _make_repo([issue])
    with patch("src.github_client.Github") as gh_cls:
        gh_cls.return_value.get_repo.return_value = repo
        client = GitHubClient("token", "acme/widgets")
        summaries = client.get_issue_summaries()
    assert summaries[0]["number"] == 9
    assert summaries[0]["labels"] == ["bug"]
    issue.get_reactions.assert_not_called()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
