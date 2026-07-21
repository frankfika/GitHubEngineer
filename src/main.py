from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pydantic import ValidationError

from .analyzer import AnalyzerError, IssueAnalyzer
from .config import ConfigError, get_repo_full_name, load_config
from .delegation import (
    ClaudeCodeAdapter,
    CodexAdapter,
    DelegationError,
    GenericCLIAdapter,
    execute_delegation,
)
from .github_client import GitHubClient, GitHubClientError
from .llm_client import LLMClient, LLMClientError
from .memory_manager import DecisionMemory, DecisionMemoryError
from .models import DecisionRecord, IssueMetrics
from .report_generator import ReportGenerator
from .task_preparer import TaskPreparer, TaskPreparationError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Maintainer Brief for GitHub issues.")
    parser.add_argument("--config", default=None, help="Path to .ghe/config.yml")
    parser.add_argument("--repo", default=None, help="Repository full name, for example owner/name")
    parser.add_argument("--memory-path", default=".ghe/memory/decisions.yml", help="Decision memory YAML path")
    parser.add_argument("--record-decision", choices=("accepted", "rejected", "deferred"))
    parser.add_argument("--issue-number", type=int, action="append", default=[])
    parser.add_argument("--theme", action="append", default=[])
    parser.add_argument("--reason", default="")
    parser.add_argument("--goal", action="append", default=[])
    parser.add_argument("--guardrail", action="append", default=[])
    parser.add_argument("--prepare-issue", type=int, help="Generate an Agent-ready task for a recommended issue")
    parser.add_argument("--task-output-dir", default="tasks", help="Directory for prepared task Markdown")
    parser.add_argument("--allowed-directory", action="append", default=[])
    parser.add_argument("--forbidden-directory", action="append", default=[])
    parser.add_argument("--delegate-task", help="Path to prepared task Markdown")
    parser.add_argument("--adapter", choices=("codex", "claude-code", "generic-cli"), default="codex")
    parser.add_argument("--agent-repo-path", help="Local repository directory for delegated work")
    parser.add_argument("--generic-executable", help="Explicit allowlisted executable for generic-cli")
    parser.add_argument("--execute", action="store_true", help="Actually start the selected coding agent")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.record_decision:
            return record_decision(args)
        if args.delegate_task:
            return delegate_task(args)
        config = load_config(args.config)
        repo_full_name = get_repo_full_name(config, args.repo)

        analysis_config = config.get("analysis", {})
        lookback_days = int(analysis_config.get("lookback_days", 7))
        max_issues = int(analysis_config.get("max_issues_for_llm", 50))
        top_n = int(analysis_config.get("top_n", 3))
        min_issue_age_hours = int(analysis_config.get("min_issue_age_hours", 24))

        github_token = config.get("github", {}).get("token") or os.getenv("GITHUB_TOKEN")
        model_config = config["model"]
        llm_client = LLMClient(
            model_config.get("base_url"),
            model_config["api_key"],
            model_config["model_name"],
        )

        since = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        # Cap how many GitHub pages we walk. 30 issues per page * 10 pages = 300
        # issues is enough for any realistic weekly brief and protects against
        # runaway pagination on 100k+ issue repos.
        gh_client = GitHubClient(github_token, repo_full_name)
        raw_issues = gh_client.get_open_issues(
            since=since,
            max_issues=max(100, max_issues),
            max_pages=10,
        )
        issues = [IssueMetrics(**gh_client.get_issue_metrics(issue)) for issue in raw_issues]

        analyzer = IssueAnalyzer(
            llm_client,
            max_issues_for_llm=max_issues,
            top_n=top_n,
            decision_memory=DecisionMemory.load(args.memory_path),
            min_issue_age_hours=min_issue_age_hours,
        )
        brief = analyzer.analyze(issues, repo_full_name, lookback_days)
        report = ReportGenerator().generate_markdown(brief, repo_full_name)
        output_file = write_report(report, repo_full_name, config)
        write_step_summary(report, config)

        print(f"Report generated: {output_file}")
        if args.prepare_issue is not None:
            task_file = prepare_task(args, brief.top_priorities, issues, llm_client, repo_full_name)
            print(f"Prepared task generated: {task_file}")
        return 0
    except (
        AnalyzerError,
        ConfigError,
        GitHubClientError,
        LLMClientError,
        DecisionMemoryError,
        TaskPreparationError,
        DelegationError,
        OSError,
        RuntimeError,
        ValidationError,
        ValueError,
    ) as exc:
        print(format_error(exc), file=sys.stderr)
        return 1


# Map of substrings → fix-it hint. Keep generic enough to avoid leaking
# credentials but specific enough to tell the user the next step.
_ERROR_HINTS: tuple[tuple[str, str], ...] = (
    ("Missing model.api_key", "Set the LLM_API_KEY environment variable or add model.api_key to .ghe/config.yml."),
    ("Missing model.model_name", "Set the LLM_MODEL environment variable or add model.model_name to .ghe/config.yml."),
    ("rate limit", "Wait for the GitHub API rate limit to reset, or supply a GITHUB_TOKEN with higher quota."),
    ("Could not access repository", "Verify the repository owner/name and that GITHUB_TOKEN has read access."),
    ("Failed to fetch issues", "Check that the repository exists and the GITHUB_TOKEN has 'repo' or 'public_repo' scope."),
    ("LLM request failed", "Check LLM_BASE_URL, LLM_API_KEY, and LLM_MODEL in the environment or .ghe/config.yml."),
    ("Could not parse LLM JSON", "The model returned non-JSON. Try a different model or lower the issue count (analysis.max_issues_for_llm)."),
    ("is not in this brief's recommended priorities", "Re-run the brief first (without --prepare-issue), then call --prepare-issue with one of the issue numbers from the new report."),
    ("--agent-repo-path is required", "Pass --agent-repo-path /absolute/path/to/target-repo when delegating."),
    ("--generic-executable is required", "Pass --generic-executable /absolute/path/to/agent-cli when --adapter generic-cli is used."),
)


def format_error(exc: BaseException) -> str:
    """Render an exception as a one-line, actionable error message."""

    message = str(exc).strip() or exc.__class__.__name__
    for needle, hint in _ERROR_HINTS:
        if needle in message:
            return f"Error: {message}\nHint: {hint}"
    return f"Error: {message}"


def record_decision(args: argparse.Namespace) -> int:
    """Persist a maintainer-approved decision without contacting GitHub or an LLM."""

    if not args.issue_number and not args.theme:
        raise ConfigError("A decision needs at least one --issue-number or --theme.")
    memory = DecisionMemory.load(args.memory_path)
    memory.record_decision(
        DecisionRecord(
            status=args.record_decision,
            reason=args.reason,
            issue_numbers=args.issue_number,
            themes=args.theme,
            goals=args.goal,
            guardrails=args.guardrail,
            created_at=datetime.now(timezone.utc),
        )
    )
    print(f"Decision recorded: {memory.path}")
    return 0


def prepare_task(
    args: argparse.Namespace,
    priorities: list,
    issues: list[IssueMetrics],
    llm_client: LLMClient,
    repo_full_name: str,
) -> Path:
    """Prepare a task only for an issue explicitly selected from this brief."""

    priority = next((item for item in priorities if item.issue_number == args.prepare_issue), None)
    if priority is None:
        raise TaskPreparationError(
            f"Issue #{args.prepare_issue} is not in this brief's recommended priorities; "
            "review and approve it before preparing a task."
        )
    issue = next((item for item in issues if item.number == args.prepare_issue), None)
    if issue is None:
        raise TaskPreparationError(f"Source data for issue #{args.prepare_issue} was not fetched.")
    task = TaskPreparer(llm_client).prepare(
        priority,
        issue,
        allowed_directories=args.allowed_directory,
        forbidden_directories=args.forbidden_directory,
    )
    directory = Path(args.task_output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    safe_repo_name = repo_full_name.replace("/", "_")
    output_file = directory / f"{safe_repo_name}_issue_{args.prepare_issue}.md"
    output_file.write_text(task, encoding="utf-8")
    return output_file


def delegate_task(args: argparse.Namespace) -> int:
    """Show a safe delegation plan, or execute it only with --execute."""

    if not args.agent_repo_path:
        raise ConfigError("--agent-repo-path is required with --delegate-task.")
    task_path = Path(args.delegate_task)
    try:
        task_markdown = task_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DelegationError(f"Unable to read prepared task {task_path}: {exc}") from exc

    if args.adapter == "codex":
        adapter = CodexAdapter(allowed_root=args.agent_repo_path)
    elif args.adapter == "claude-code":
        adapter = ClaudeCodeAdapter(allowed_root=args.agent_repo_path)
    else:
        if not args.generic_executable:
            raise ConfigError("--generic-executable is required with --adapter generic-cli.")
        adapter = GenericCLIAdapter(
            args.generic_executable,
            allowed_root=args.agent_repo_path,
            allowed_executables=[args.generic_executable],
        )
    plan = adapter.plan(task_markdown, args.agent_repo_path)
    print(f"Delegation plan ({plan.adapter}): {' '.join(plan.command)}")
    print(f"Repository: {plan.repo_path}")
    if not args.execute:
        print("Dry run only. Add --execute only after human approval to start the coding agent.")
        return 0
    result = execute_delegation(
        plan,
        allow_execution=True,
        allowed_root=args.agent_repo_path,
        allowed_executables=[args.generic_executable] if args.adapter == "generic-cli" else None,
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result.return_code


def write_report(report: str, repo_full_name: str, config: dict) -> Path:
    output_config = config.get("output", {})
    output_dir = Path(output_config.get("output_dir", "reports"))
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_repo_name = repo_full_name.replace("/", "_")
    output_file = output_dir / f"{safe_repo_name}_{datetime.now().strftime('%Y%m%d')}.md"
    output_file.write_text(report, encoding="utf-8")
    return output_file


def write_step_summary(report: str, config: dict) -> None:
    output_format = config.get("output", {}).get("format", "markdown")
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path or output_format not in {"markdown", "action-summary"}:
        return
    with open(summary_path, "a", encoding="utf-8") as handle:
        handle.write(report)
        handle.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
