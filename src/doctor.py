"""Configuration diagnostics and health check."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from .config import ConfigError, load_config_lenient
from .git_detection import detect_git_context
from .github_client import GitHubClient, GitHubClientError
from .llm_client import LLMClient, LLMClientError


def run_doctor(config_path: str | None = None) -> int:
    """
    Run health checks on GitHub Engineer configuration.

    Returns:
        0 if all checks pass, 1 if any check fails.
    """
    print("🏥 GitHub Engineer Health Check")
    print("=" * 60)
    print()

    failed_checks = 0

    # Check 1: Python version
    print("🐍 Python version...", end=" ")
    version = sys.version_info
    version_tuple = tuple(version[:3])
    version_label = ".".join(str(part) for part in version_tuple)
    if version >= (3, 11):
        print(f"✓ {version_label}")
    else:
        print(f"✗ {version_label} (requires 3.11+)")
        failed_checks += 1

    # Check 2: Config file
    config_path = config_path or os.getenv("GHE_CONFIG_PATH", ".ghe/config.yml")
    config_file = Path(config_path)
    print(f"📄 Config file ({config_path})...", end=" ")
    if config_file.exists():
        print("✓ exists")
    else:
        print("✗ not found")
        print("   Run `ghe --init` to create it.")
        failed_checks += 1
        return failed_checks

    # Check 3: Load config
    print("⚙️  Config validity...", end=" ")
    try:
        config = load_config_lenient(config_path)
        print("✓ valid")
    except ConfigError as e:
        print("✗ invalid")
        print(f"   {e}")
        failed_checks += 1
        return failed_checks

    # Check 4: Repository configuration
    repo_config = config.get("repo") or {}
    owner = repo_config.get("owner")
    name = repo_config.get("name")
    repo_full_name = str(repo_config.get("full_name") or "")
    configured_repos = config.get("repos") or []
    if not repo_full_name and owner and name:
        repo_full_name = f"{owner}/{name}"
    if not repo_full_name and configured_repos:
        repo_full_name = str(configured_repos[0])
    if "/" in repo_full_name:
        owner, name = repo_full_name.split("/", 1)
    print("📦 Repository config...", end=" ")
    if (
        owner
        and name
        and owner != "REPLACE_ME"
        and name != "REPLACE_ME"
    ):
        print(f"✓ {repo_full_name}")
    else:
        print("✗ not configured (still has REPLACE_ME)")
        print(f"   Edit {config_path} to set repos: [owner/repository]")
        failed_checks += 1

    # Check 5: GitHub account (optional for public reads)
    configured_token = os.getenv("GITHUB_TOKEN") or config.get("github", {}).get("token")
    if configured_token == "${GITHUB_TOKEN}":
        configured_token = None
    github_token = GitHubClient.resolve_token(configured_token)
    print("🔑 GitHub account...", end=" ")
    if github_token:
        print("✓ connected once (reused for every repository)")
    else:
        print("ℹ anonymous public-read mode")
        print("   Account actions: `gh auth login --web --git-protocol https`")

    # Check 5a: GitHub API connection. Anonymous access is valid for public repos.
    if owner and name and owner != "REPLACE_ME" and name != "REPLACE_ME":
        print(f"🌐 GitHub API access ({repo_full_name})...", end=" ")
        try:
            GitHubClient(token=github_token, repo_full_name=repo_full_name)
            print("✓ connected" if github_token else "✓ public repository (anonymous)")
        except Exception as e:
            print("✗ failed")
            print(f"   {str(e)[:80]}")
            if not github_token:
                print("   If this is private, connect once with `gh auth login --web`.")
            failed_checks += 1

    # Check 6: LLM API key
    print("🤖 LLM API key...", end=" ")
    llm_key = os.getenv("LLM_API_KEY") or config.get("model", {}).get("api_key")
    if llm_key and llm_key != "${LLM_API_KEY}":
        print("�� found")

        # Check 6a: LLM connection
        print("🔌 LLM API connection...", end=" ")
        try:
            model_config = config.get("model", {})
            base_url = os.getenv("LLM_BASE_URL") or model_config.get("base_url") or ""
            model_name = os.getenv("LLM_MODEL") or model_config.get("model_name", "gpt-4o-mini")

            llm_client = LLMClient(
                base_url=base_url if base_url else None,
                api_key=llm_key,
                model=model_name,
            )
            # Try a minimal request
            response = llm_client.chat([{"role": "user", "content": "test"}], max_tokens=5)
            print(f"✓ OK (model: {model_name})")
        except Exception as e:
            print("✗ failed")
            print(f"   {str(e)[:80]}")
            failed_checks += 1
    else:
        print("✗ not set")
        print("   Set LLM_API_KEY environment variable")
        failed_checks += 1

    # Check 7: Git context (informational)
    print()
    print("📍 Git Repository Context:")
    git_ctx = detect_git_context()
    if git_ctx.is_git_repo:
        print(f"   Current repo: {git_ctx.current_repo or 'unknown'}")
        if git_ctx.is_fork:
            print(f"   Fork of: {git_ctx.upstream_repo}")
            if owner and name:
                print(f"   💡 You're monitoring: {owner}/{name}")
                if git_ctx.upstream_repo == f"{owner}/{name}":
                    print("   ✓ Configured to monitor upstream (recommended for contributors)")
                elif git_ctx.current_repo == f"{owner}/{name}":
                    print("   ℹ️  Configured to monitor your fork")
    else:
        print("   Not in a Git repository")

    # Summary
    print()
    print("=" * 60)
    if failed_checks == 0:
        print("✅ All checks passed! You're ready to generate briefs.")
        print()
        print("Next: Run `ghe --config .ghe/config.yml` to generate your first brief")
        return 0
    else:
        print(f"⚠️  {failed_checks} check(s) failed. Fix the issues above and try again.")
        return 1
