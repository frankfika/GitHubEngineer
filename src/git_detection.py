"""Git repository and fork detection utilities."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class GitContext:
    """Git repository context detection result."""

    is_git_repo: bool
    current_repo: Optional[str]  # e.g., "frankfika/csghub"
    is_fork: bool
    upstream_repo: Optional[str]  # e.g., "OpenCSGs/csghub"
    remotes: list[str]


def _as_text(value: str | bytes) -> str:
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value


def detect_git_context() -> GitContext:
    """
    Detect if current directory is a Git repository and if it's a fork.

    Returns:
        GitContext with repository information.
        All fields are safe defaults if detection fails.
    """
    result = GitContext(
        is_git_repo=False,
        current_repo=None,
        is_fork=False,
        upstream_repo=None,
        remotes=[],
    )

    try:
        # Check if in a git repository
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            check=True,
            timeout=2,
        )
        result.is_git_repo = True

        # Get current repo from remote origin
        try:
            origin = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                check=True,
                timeout=2,
                text=True,
            ).stdout.strip()
            origin = _as_text(origin)

            # Parse GitHub repo from URL
            # Matches: git@github.com:user/repo.git or https://github.com/user/repo
            match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', origin)
            if match:
                result.current_repo = f"{match.group(1)}/{match.group(2)}"
        except subprocess.CalledProcessError:
            pass

        # Check for upstream remote (common in forks)
        try:
            upstream = subprocess.run(
                ["git", "remote", "get-url", "upstream"],
                capture_output=True,
                check=True,
                timeout=2,
                text=True,
            ).stdout.strip()
            upstream = _as_text(upstream)

            match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', upstream)
            if match:
                result.is_fork = True
                result.upstream_repo = f"{match.group(1)}/{match.group(2)}"
        except subprocess.CalledProcessError:
            pass

        # Get all remotes
        try:
            remotes_output = subprocess.run(
                ["git", "remote", "-v"],
                capture_output=True,
                check=True,
                timeout=2,
                text=True,
            ).stdout
            remotes_output = _as_text(remotes_output)
            result.remotes = [line.strip() for line in remotes_output.split('\n') if line.strip()]
        except subprocess.CalledProcessError:
            pass

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        pass

    return result


def format_git_context_help(ctx: GitContext) -> str:
    """Format Git context as user-friendly help text."""
    if not ctx.is_git_repo:
        return "📍 Not in a Git repository. You'll need to manually specify the repository to monitor."

    if ctx.is_fork and ctx.upstream_repo and ctx.current_repo:
        return f"""📍 Detected: You're in a fork of {ctx.upstream_repo}

You have two options:

  [1] 🔼 Monitor upstream: {ctx.upstream_repo} (RECOMMENDED)
      → Monitor issues from the original project
      → Best for: Contributing to the upstream project

  [2] 🔀 Monitor your fork: {ctx.current_repo}
      → Monitor issues in your forked copy
      → Best for: Tracking work specific to your fork"""

    if ctx.current_repo:
        return f"📍 Detected: You're in repository {ctx.current_repo}\n\nThis repository will be used as the default."

    return "📍 In a Git repository, but couldn't detect the GitHub remote."
