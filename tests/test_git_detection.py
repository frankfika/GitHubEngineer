"""Tests for git_detection module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.git_detection import GitContext, detect_git_context, format_git_context_help


class TestDetectGitContext:
    """Test Git context detection."""

    @patch("subprocess.run")
    def test_not_in_git_repo(self, mock_run):
        """When not in a Git repo, should return safe defaults."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        ctx = detect_git_context()

        assert ctx.is_git_repo is False
        assert ctx.current_repo is None
        assert ctx.is_fork is False
        assert ctx.upstream_repo is None
        assert ctx.remotes == []

    @patch("subprocess.run")
    def test_git_repo_with_origin(self, mock_run):
        """Should detect Git repo and parse origin URL."""
        mock_run.side_effect = [
            MagicMock(stdout=b"", returncode=0),  # git rev-parse --git-dir
            MagicMock(stdout=b"git@github.com:frankfika/csghub.git", returncode=0),  # origin
            subprocess.CalledProcessError(1, "git"),  # no upstream
            MagicMock(stdout=b"origin\tgit@github.com:frankfika/csghub.git (fetch)", returncode=0),  # remotes
        ]

        ctx = detect_git_context()

        assert ctx.is_git_repo is True
        assert ctx.current_repo == "frankfika/csghub"
        assert ctx.is_fork is False
        assert ctx.upstream_repo is None

    @patch("subprocess.run")
    def test_git_repo_with_https_origin(self, mock_run):
        """Should parse HTTPS GitHub URLs."""
        mock_run.side_effect = [
            MagicMock(stdout=b"", returncode=0),
            MagicMock(stdout=b"https://github.com/OpenCSG/csghub", returncode=0),
            subprocess.CalledProcessError(1, "git"),
            MagicMock(stdout=b"origin\thttps://github.com/OpenCSG/csghub (fetch)", returncode=0),
        ]

        ctx = detect_git_context()

        assert ctx.is_git_repo is True
        assert ctx.current_repo == "OpenCSG/csghub"

    @patch("subprocess.run")
    def test_fork_with_upstream(self, mock_run):
        """Should detect fork when upstream remote exists."""
        mock_run.side_effect = [
            MagicMock(stdout=b"", returncode=0),  # rev-parse
            MagicMock(stdout=b"git@github.com:frankfika/csghub.git", returncode=0),  # origin
            MagicMock(stdout=b"git@github.com:OpenCSG/csghub.git", returncode=0),  # upstream
            MagicMock(
                stdout=b"origin\tgit@github.com:frankfika/csghub.git (fetch)\nupstream\tgit@github.com:OpenCSG/csghub.git (fetch)",
                returncode=0,
            ),
        ]

        ctx = detect_git_context()

        assert ctx.is_git_repo is True
        assert ctx.current_repo == "frankfika/csghub"
        assert ctx.is_fork is True
        assert ctx.upstream_repo == "OpenCSG/csghub"
        assert len(ctx.remotes) == 2

    @patch("subprocess.run")
    def test_timeout_handling(self, mock_run):
        """Should handle subprocess timeout gracefully."""
        mock_run.side_effect = subprocess.TimeoutExpired("git", 2)

        ctx = detect_git_context()

        assert ctx.is_git_repo is False


class TestFormatGitContextHelp:
    """Test help text formatting."""

    def test_not_in_git_repo(self):
        """Should show manual specification message."""
        ctx = GitContext(
            is_git_repo=False,
            current_repo=None,
            is_fork=False,
            upstream_repo=None,
            remotes=[],
        )

        help_text = format_git_context_help(ctx)

        assert "Not in a Git repository" in help_text
        assert "manually specify" in help_text

    def test_regular_repo(self):
        """Should show current repo."""
        ctx = GitContext(
            is_git_repo=True,
            current_repo="frankfika/my-project",
            is_fork=False,
            upstream_repo=None,
            remotes=[],
        )

        help_text = format_git_context_help(ctx)

        assert "frankfika/my-project" in help_text
        assert "default" in help_text

    def test_fork_repo(self):
        """Should show both fork and upstream with recommendations."""
        ctx = GitContext(
            is_git_repo=True,
            current_repo="frankfika/csghub",
            is_fork=True,
            upstream_repo="OpenCSG/csghub",
            remotes=[],
        )

        help_text = format_git_context_help(ctx)

        assert "fork of OpenCSG/csghub" in help_text
        assert "Monitor upstream" in help_text
        assert "Monitor your fork" in help_text
        assert "RECOMMENDED" in help_text

    def test_git_repo_without_github_remote(self):
        """Should handle Git repo without GitHub remote."""
        ctx = GitContext(
            is_git_repo=True,
            current_repo=None,
            is_fork=False,
            upstream_repo=None,
            remotes=["origin\tfile:///local/repo (fetch)"],
        )

        help_text = format_git_context_help(ctx)

        assert "couldn't detect the GitHub remote" in help_text
