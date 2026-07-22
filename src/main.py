from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pydantic import ValidationError

from .analyzer import AnalyzerError, IssueAnalyzer
from .config import ConfigError, get_target_repos, load_config, load_config_lenient
from .delegation import (
    ClaudeCodeAdapter,
    CodexAdapter,
    DelegationError,
    GenericCLIAdapter,
    execute_delegation,
)
from .github_client import GitHubClient, GitHubClientError
from .history import (
    HistoryError,
    compute_diff,
    load_latest,
    record_from_brief,
    save_history,
)
from .llm_client import LLMClient, LLMClientError
from .memory_manager import DecisionMemory, DecisionMemoryError
from .models import DecisionRecord, IssueMetrics, MaintainerBrief
from .report_generator import ReportGenerator
from .task_preparer import TaskPreparer, TaskPreparationError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Maintainer Brief for GitHub issues.")
    parser.add_argument("--config", default=None, help="Path to .ghe/config.yml")
    parser.add_argument(
        "--repo",
        default=None,
        help="Repository full name, for example owner/name. Comma-separated for multiple repos.",
    )
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
    parser.add_argument(
        "--pipeline",
        action="store_true",
        help="After a brief is generated, prepare a task for the top issue and plan a delegation in one shot.",
    )
    parser.add_argument(
        "--show-latest",
        action="store_true",
        help="Print the most recent brief for the target repo to stdout and exit.",
    )
    parser.add_argument(
        "--list-decisions",
        action="store_true",
        help="Print decision memory records and exit.",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Write a starter .ghe/config.yml from the example template, then exit.",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start the local read-only web service on $GHE_SERVE_PORT (default 8765).",
    )
    parser.add_argument(
        "--serve-host",
        default="127.0.0.1",
        help="Bind address for --serve. Use 0.0.0.0 to expose on the LAN.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.record_decision:
            return record_decision(args)
        if args.delegate_task:
            return delegate_task(args)
        if args.list_decisions:
            return list_decisions(args)
        if args.init:
            return init_config()
        if args.serve:
            return serve(args)
        if args.show_latest:
            return show_latest(load_config_lenient(args.config), args)
        config = load_config(args.config)
        target_repos = get_target_repos(config, args.repo)

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
        history_dir = os.getenv("GHE_HISTORY_DIR", ".ghe/history")
        if not _safe_local_directory(history_dir):
            print(
                f"Warning: GHE_HISTORY_DIR={history_dir!r} is not a safe local "
                "directory; the trend baseline will be disabled.",
                file=sys.stderr,
            )
            history_dir = ".ghe/history"
            history_enabled = False
        else:
            history_enabled = os.path.isdir(history_dir) or _writable_dir(history_dir)

        last_repo = target_repos[-1]
        all_outputs: list[Path] = []
        completed_repos: list[str] = []
        failed_repos: list[tuple[str, str]] = []
        last_brief = None
        last_issues: list[IssueMetrics] = []

        for repo_full_name in target_repos:
            try:
                _process_single_repo(
                    repo_full_name=repo_full_name,
                    config=config,
                    history_dir=history_dir,
                    history_enabled=history_enabled,
                    lookback_days=lookback_days,
                    max_issues=max_issues,
                    top_n=top_n,
                    min_issue_age_hours=min_issue_age_hours,
                    github_token=github_token,
                    llm_client=llm_client,
                    memory_path=args.memory_path,
                )
            except (
                AnalyzerError,
                ConfigError,
                GitHubClientError,
                HistoryError,
                LLMClientError,
                DecisionMemoryError,
                ValidationError,
                ValueError,
            ) as exc:
                # Surface the failure for this repo but keep processing the
                # remaining ones. A 3-repo run where the middle one fails
                # should still produce briefs for the other two.
                failed_repos.append((repo_full_name, str(exc)))
                print(
                    f"Error: brief for {repo_full_name} failed: {format_error(exc)}",
                    file=sys.stderr,
                )
                continue
            completed_repos.append(repo_full_name)

        # Surface the multi-repo summary so the user can spot a partial run.
        if failed_repos:
            for repo, error in failed_repos:
                print(f"Failed: {repo} ({error})", file=sys.stderr)
            print(
                f"Summary: {len(completed_repos)} of {len(target_repos)} "
                f"repositories succeeded.",
                file=sys.stderr,
            )

        if not completed_repos:
            # Nothing usable to prepare from; bail with a non-zero exit so
            # CI can detect the partial failure.
            return 1

        last_repo = completed_repos[-1]

        # Prepare / pipeline actions target the last (or only) repo. Multi-repo
        # callers who want to chain a task per repo should loop with --repo.
        if args.prepare_issue is not None:
            # Re-read the last successful brief from disk so downstream
            # prepare / pipeline actions target a real report even if the
            # in-process state was lost.
            try:
                last_brief, last_issues = _reload_last_brief(
                    last_repo, config, llm_client, args.memory_path,
                    min_issue_age_hours=min_issue_age_hours,
                    max_issues=max_issues, top_n=top_n, lookback_days=lookback_days,
                    github_token=github_token, history_dir=history_dir, history_enabled=history_enabled,
                )
            except (AnalyzerError, ConfigError, GitHubClientError, HistoryError,
                    LLMClientError, DecisionMemoryError, ValidationError, ValueError) as exc:
                print(
                    f"Error: could not reload the last brief for the prepare step: {format_error(exc)}",
                    file=sys.stderr,
                )
                return 1
            task_file = prepare_task(args, last_brief.top_priorities, last_issues, llm_client, last_repo)
            print(f"Prepared task generated: {task_file}")
            if args.pipeline:
                # Delegate dry-run. If dry-run fails or the user has not
                # supplied --execute, the task file is left in place so the
                # user can inspect it. We do NOT clean it up automatically:
                # a half-deleted task is more surprising than a leftover one.
                args.delegate_task = str(task_file)
                return delegate_task(args)
        return 0
    except (
        AnalyzerError,
        ConfigError,
        GitHubClientError,
        HistoryError,
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


def _writable_dir(path: str) -> bool:
    """Return True if ``path`` is either a writable directory or creatable now."""

    candidate = Path(path)
    if candidate.exists():
        return candidate.is_dir() and os.access(candidate, os.W_OK)
    parent = candidate.parent if candidate.parent != candidate else Path(".")
    return parent.is_dir() and os.access(parent, os.W_OK)


def _process_single_repo(
    *,
    repo_full_name: str,
    config: dict,
    history_dir: str,
    history_enabled: bool,
    lookback_days: int,
    max_issues: int,
    top_n: int,
    min_issue_age_hours: int,
    github_token: str | None,
    llm_client: LLMClient,
    memory_path: str,
) -> None:
    """Run the full analyze -> render -> persist flow for one repository.

    Split out of ``main`` so a failure in one repository does not abort
    the whole multi-repo brief. Exceptions raised here are caught by
    the caller's per-repo ``except`` block and surfaced as a partial
    failure.
    """

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
        decision_memory=DecisionMemory.load(memory_path),
        min_issue_age_hours=min_issue_age_hours,
    )
    prior_record = load_latest(history_dir, repo_full_name) if history_enabled else None
    brief = analyzer.analyze(issues, repo_full_name, lookback_days)
    current_record = record_from_brief(
        repo_full_name=repo_full_name,
        generated_at=brief.generated_at,
        top_issue_numbers=[item.issue_number for item in brief.top_priorities],
        top_issue_scores={
            f"#{item.issue_number}": item.priority_score for item in brief.top_priorities
        },
        cluster_names=[cluster.cluster_name for cluster in brief.issue_clusters],
        new_issues_count=brief.new_issues_count,
    )
    if prior_record is not None:
        try:
            diff = compute_diff(prior_record, current_record)
            brief = brief.model_copy(update={"trend": diff.summary(brief.new_issues_count)})
        except (HistoryError, ValueError) as exc:
            # Diff failure must not break the user-facing report, but
            # the user has asked for a trend line so we tell them
            # why it is missing.
            print(
                f"Warning: trend diff failed ({exc}); trend line "
                "falls back to the default placeholder.",
                file=sys.stderr,
            )
    else:
        from .history import TrendDiff  # local import to avoid a cycle at module load

        empty_diff = TrendDiff(prior_generated_at=None)
        brief = brief.model_copy(
            update={"trend": empty_diff.summary(brief.new_issues_count)}
        )
    try:
        save_history(history_dir, current_record)
    except HistoryError as exc:
        # A history write failure means the next run will not see a
        # baseline. Surface that to the user instead of swallowing it.
        print(
            f"Warning: history write to {history_dir} failed ({exc}); "
            "the next brief will not have a trend baseline.",
            file=sys.stderr,
        )
    report = ReportGenerator().generate_markdown(brief, repo_full_name)
    output_file = write_report(report, repo_full_name, config)
    write_step_summary(report, config)
    print(f"Report generated: {output_file}")


def _reload_last_brief(
    repo_full_name: str,
    config: dict,
    llm_client: LLMClient,
    memory_path: str,
    *,
    min_issue_age_hours: int,
    max_issues: int,
    top_n: int,
    lookback_days: int,
    github_token: str | None,
    history_dir: str,
    history_enabled: bool,
) -> tuple[MaintainerBrief, list[IssueMetrics]]:
    """Re-run the analyze step for ``repo_full_name`` after a multi-repo run.

    The main loop only stores the last successful brief in process
    state. When the prepare / pipeline actions run, we need the same
    brief plus the source issues so we can call ``TaskPreparer``. This
    helper performs the second pass and returns the pair.
    """

    since = datetime.now(timezone.utc) - timedelta(days=lookback_days)
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
        decision_memory=DecisionMemory.load(memory_path),
        min_issue_age_hours=min_issue_age_hours,
    )
    prior_record = load_latest(history_dir, repo_full_name) if history_enabled else None
    brief = analyzer.analyze(issues, repo_full_name, lookback_days)
    if prior_record is not None:
        try:
            current_record = record_from_brief(
                repo_full_name=repo_full_name,
                generated_at=brief.generated_at,
                top_issue_numbers=[item.issue_number for item in brief.top_priorities],
                top_issue_scores={
                    f"#{item.issue_number}": item.priority_score for item in brief.top_priorities
                },
                cluster_names=[cluster.cluster_name for cluster in brief.issue_clusters],
                new_issues_count=brief.new_issues_count,
            )
            diff = compute_diff(prior_record, current_record)
            brief = brief.model_copy(update={"trend": diff.summary(brief.new_issues_count)})
        except (HistoryError, ValueError):
            pass
    else:
        from .history import TrendDiff  # local import to avoid a cycle at module load

        empty_diff = TrendDiff(prior_generated_at=None)
        brief = brief.model_copy(
            update={"trend": empty_diff.summary(brief.new_issues_count)}
        )
    return brief, issues


# Directories we never want to let an environment variable steer writes
# into, even if the runner is the same user. Listed by absolute prefix.
_UNSAFE_DIRECTORY_PREFIXES: tuple[str, ...] = (
    "/etc",
    "/var",
    "/sys",
    "/proc",
    "/boot",
    "/usr",
    "/bin",
    "/sbin",
    "/lib",
    "/root",
    "/run",
    "/dev",
)


def _safe_local_directory(path: str) -> bool:
    """Return True if ``path`` looks like a safe local user directory.

    The check is intentionally conservative: a path that resolves to one
    of the system roots (e.g. ``/etc/ghe-history``) is rejected, while
    relative paths, ``.ghe/...``, ``/tmp/...``, and the user's home
    directory are accepted. The check is best-effort; treat it as a
    defence-in-depth guardrail, not a security boundary.

    On macOS ``/etc`` is a symlink to ``/private/etc``, so the check
    walks the original components first, then the resolved path, and
    rejects either form. This avoids a "safe-looking" result when the
    user really meant ``/etc``.
    """

    if not path:
        return False
    try:
        original = Path(path).expanduser()
        resolved = original.resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        return False
    for candidate in (str(original), str(resolved)):
        for prefix in _UNSAFE_DIRECTORY_PREFIXES:
            if candidate == prefix or candidate.startswith(prefix + "/"):
                return False
    return True


def _inline_markdown_to_html(text: str) -> str:
    """Render the inline subset of Markdown that the brief uses.

    Handles ``[text](url)`` links, backtick code spans, and the rest
    passes through with HTML escaping. Used by the local web UI to
    turn report markdown into a clickable page without pulling in a
    full Markdown parser.
    """

    import html as _html
    import re as _re

    parts: list[str] = []
    cursor = 0
    pattern = _re.compile(
        r"\[([^\]]+)\]\(([^)\s]+)\)|`([^`]+)`"
    )
    for match in pattern.finditer(text):
        if match.start() > cursor:
            parts.append(_html.escape(text[cursor : match.start()]))
        if match.group(1) is not None:
            parts.append(
                f"<a href='{_html.escape(match.group(2), quote=True)}'>"
                f"{_html.escape(match.group(1))}</a>"
            )
        else:
            parts.append(f"<code>{_html.escape(match.group(3))}</code>")
        cursor = match.end()
    if cursor < len(text):
        parts.append(_html.escape(text[cursor:]))
    return "".join(parts)


def list_decisions(args: argparse.Namespace) -> int:
    """Print every decision in memory as a compact, single-line summary."""

    memory = DecisionMemory.load(args.memory_path)
    if not memory.records:
        print(f"No decisions recorded at {memory.path}.")
        return 0
    for index, record in enumerate(memory.records, 1):
        topics: list[str] = []
        if record.issue_numbers:
            topics.append("issues " + ", ".join(f"#{n}" for n in record.issue_numbers))
        if record.themes:
            topics.append("themes " + ", ".join(record.themes))
        scope = "; ".join(topics) or "no scope"
        timestamp = record.created_at.strftime("%Y-%m-%d") if record.created_at else "unknown"
        print(f"{index}. [{record.status.upper()}] {timestamp} | {scope}")
        if record.reason:
            print(f"   reason: {record.reason}")
    return 0


def init_config() -> int:
    """Write a starter ``.ghe/config.yml`` next to the example template.

    The copy is intentionally non-destructive: if a config already exists
    the command refuses to overwrite it. The user can then edit
    ``.ghe/config.yml`` to point at their repository and LLM provider.
    """

    target = Path(".ghe/config.yml")
    if target.exists():
        print(f"{target} already exists; refusing to overwrite.")
        return 1
    source = Path(__file__).resolve().parent.parent / ".ghe" / "config.example.yml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {target} from {source.name}.")
    print("Next: edit repo.owner / repo.name, set LLM_API_KEY, then run `ghe`.")
    return 0


def show_latest(config: dict[str, Any], args: argparse.Namespace) -> int:
    """Print the most recent brief Markdown for the target repo to stdout."""

    from .config import get_target_repos  # local import to avoid a cycle at module load

    repos = get_target_repos(config, args.repo)
    output_dir = Path(config.get("output", {}).get("output_dir", "reports"))
    if not output_dir.exists():
        raise ConfigError(f"Output directory {output_dir} does not exist; no briefs to show yet.")
    shown = 0
    for repo in repos:
        safe = repo.replace("/", "_")
        candidates = sorted(
            (path for path in output_dir.glob(f"{safe}_*.md") if path.is_file()),
            key=lambda path: path.name,
            reverse=True,
        )
        if not candidates:
            print(f"# No brief found for {repo} under {output_dir}/", file=sys.stderr)
            continue
        latest = candidates[0]
        print(latest.read_text(encoding="utf-8"), end="")
        shown += 1
    if shown == 0:
        return 1
    return 0


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
    """Write the report to disk and return the chosen file path.

    The file name embeds a UTC timestamp with minute precision so two
    runs in the same UTC day on the same repository do not overwrite
    each other. Using UTC also keeps the file name aligned with
    ``MaintainerBrief.generated_at`` (which is always UTC).
    """

    output_config = config.get("output", {})
    output_dir = Path(output_config.get("output_dir", "reports"))
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_repo_name = repo_full_name.replace("/", "_")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    candidate = output_dir / f"{safe_repo_name}_{timestamp}.md"
    # If the same minute, append a numeric suffix so we never overwrite.
    suffix = 1
    while candidate.exists():
        candidate = output_dir / f"{safe_repo_name}_{timestamp}_{suffix}.md"
        suffix += 1
    candidate.write_text(report, encoding="utf-8")
    return candidate


def write_step_summary(report: str, config: dict) -> None:
    output_format = config.get("output", {}).get("format", "markdown")
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path or output_format not in {"markdown", "action-summary"}:
        return
    # The env var is supplied by the workflow runner. We still guard against
    # a malicious or broken value pointing outside a writable directory.
    target = Path(summary_path)
    parent = target.parent if str(target.parent) else Path(".")
    if not parent.is_dir() or not os.access(parent, os.W_OK):
        print(
            f"Warning: GITHUB_STEP_SUMMARY={summary_path!r} is not writable; skipping.",
            file=sys.stderr,
        )
        return
    try:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(report)
            handle.write("\n")
    except OSError as exc:
        print(
            f"Warning: failed to write step summary at {target}: {exc}",
            file=sys.stderr,
        )


def serve(args: argparse.Namespace) -> int:
    """Start the read-only local web service on ``--serve-host:port``.

    The service exposes three surfaces:

    - ``GET /`` and ``GET /briefs`` list the existing Maintainer Briefs.
    - ``GET /brief/<repo>`` returns the most recent brief for ``<repo>``
      as Markdown.
    - ``GET /decisions`` and ``GET /decisions.txt`` expose the decision
      memory; ``POST /decisions`` records a new one and returns the
      persisted record.

    The server is intentionally minimal. It uses only the standard
    library so the runtime stays dependency-free, and it binds to
    127.0.0.1 by default so the LAN cannot reach it without the
    ``--serve-host 0.0.0.0`` opt-in.
    """

    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from urllib.parse import parse_qs, urlparse

    config = load_config_lenient(args.config)
    repos = get_target_repos(config, args.repo)
    output_dir = Path(config.get("output", {}).get("output_dir", "reports"))
    history_dir = os.getenv("GHE_HISTORY_DIR", ".ghe/history")
    host = args.serve_host
    port = int(os.getenv("GHE_SERVE_PORT", "8765"))

    def render_index() -> tuple[int, bytes, str]:
        briefs: list[dict[str, str]] = []
        if output_dir.exists():
            for path in sorted(output_dir.glob("*_*.md"), reverse=True):
                if not path.is_file():
                    continue
                briefs.append(
                    {
                        "file": path.name,
                        "size_bytes": str(path.stat().st_size),
                        "modified": datetime.fromtimestamp(
                            path.stat().st_mtime, tz=timezone.utc
                        ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    }
                )
        body = json.dumps(
            {
                "service": "github-engineer",
                "version": "1.0.0",
                "config": {
                    "repos": repos,
                    "output_dir": str(output_dir),
                    "history_dir": history_dir,
                },
                "brief_count": len(briefs),
                "briefs": briefs,
            },
            indent=2,
            ensure_ascii=False,
        ).encode("utf-8")
        return 200, body, "application/json"

    def render_brief(repo: str) -> tuple[int, bytes, str]:
        candidates = show_latest(config, argparse.Namespace(repo=repo, config=args.config))
        if candidates != 0:
            return 404, b'{"error":"no brief"}', "application/json"
        if not output_dir.exists():
            return 404, b'{"error":"output_dir missing"}', "application/json"
        safe = repo.replace("/", "_")
        files = sorted(
            (path for path in output_dir.glob(f"{safe}_*.md") if path.is_file()),
            key=lambda path: path.name,
            reverse=True,
        )
        if not files:
            return 404, b'{"error":"no brief for repo"}', "application/json"
        return 200, files[0].read_bytes(), "text/markdown; charset=utf-8"

    # ------------------------------------------------------------------
    # HTML UI
    # ------------------------------------------------------------------
    # The JSON routes above are the machine-readable API. The HTML
    # routes below give a maintainer a browser-friendly view of the same
    # data, with one-click navigation between briefs and decisions.
    # Rendering is deliberately minimal: pure stdlib, no JS framework,
    # inline CSS. The Markdown -> HTML conversion is a small line-based
    # reducer, not a full Markdown parser; it is good enough for the
    # report we generate and keeps the runtime dependency-free.

    _HTML_SHELL = """<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<title>{title}</title>
<style>
:root {{
  --bg: #fbfaf7; --fg: #1a1a1a; --muted: #6a6a6a;
  --accent: #1d8c80; --border: #e5e2da;
  --rejected: #b3261e; --deferred: #8a6d3b; --accepted: #2f7d32;
  --code-bg: #f1efe8;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: var(--bg); color: var(--fg);
  font: 16px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}
header {{
  background: var(--accent); color: #fff; padding: 18px 32px;
  display: flex; align-items: center; justify-content: space-between;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}}
header h1 {{ margin: 0; font-size: 20px; font-weight: 600; }}
header nav a {{
  color: #fff; text-decoration: none; margin-left: 24px; font-size: 14px;
  opacity: 0.9;
}}
header nav a:hover {{ opacity: 1; text-decoration: underline; }}
main {{ max-width: 960px; margin: 32px auto; padding: 0 24px; }}
h1, h2, h3 {{ color: var(--fg); }}
h2 {{ font-size: 20px; margin-top: 32px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }}
table {{ width: 100%; border-collapse: collapse; margin: 16px 0; background: #fff;
  border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }}
th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border);
  font-size: 14px; vertical-align: top; }}
th {{ background: #f5f3ed; font-weight: 600; color: var(--muted); text-transform: uppercase;
  letter-spacing: 0.04em; font-size: 12px; }}
tr:last-child td {{ border-bottom: none; }}
a {{ color: var(--accent); text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
code, pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  background: var(--code-bg); border-radius: 4px; padding: 1px 6px; font-size: 13px; }}
pre {{ padding: 12px 14px; overflow-x: auto; }}
.muted {{ color: var(--muted); font-size: 13px; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 10px;
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.04em; }}
.badge-rejected {{ background: #fde8e6; color: var(--rejected); }}
.badge-deferred {{ background: #fbf2e3; color: var(--deferred); }}
.badge-accepted {{ background: #e6f4e7; color: var(--accepted); }}
.empty {{ text-align: center; padding: 48px 16px; color: var(--muted);
  background: #fff; border: 1px dashed var(--border); border-radius: 8px; }}
.brief-body h1 {{ font-size: 22px; }}
.brief-body h2 {{ font-size: 18px; border-bottom: none; margin-top: 24px; }}
.brief-body h3 {{ font-size: 16px; }}
.brief-body ul {{ padding-left: 22px; }}
.brief-body li {{ margin: 4px 0; }}
.brief-body a {{ color: var(--accent); }}
.metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px; margin: 16px 0 32px; }}
.metric {{ background: #fff; border: 1px solid var(--border); border-radius: 8px;
  padding: 16px; }}
.metric .label {{ font-size: 12px; color: var(--muted); text-transform: uppercase;
  letter-spacing: 0.05em; }}
.metric .value {{ font-size: 22px; font-weight: 600; margin-top: 4px; }}
footer {{ max-width: 960px; margin: 64px auto 32px; padding: 0 24px;
  color: var(--muted); font-size: 13px; text-align: center; }}
</style>
</head>
<body>
<header>
  <h1>GitHub Engineer</h1>
  <nav>
    <a href=\"/ui/\">Home</a>
    <a href=\"/ui/briefs\">Briefs</a>
    <a href=\"/ui/decisions\">Decisions</a>
    <a href=\"/healthz\">healthz</a>
  </nav>
</header>
<main>
{body}
</main>
<footer>GitHub Engineer v1.0.0 &middot; read-only local UI &middot; bind 127.0.0.1:8765</footer>
</body>
</html>
"""

    def _markdown_to_html(markdown: str) -> str:
        """Tiny Markdown -> HTML reducer.

        Supports the subset our generator emits: ``# / ## / ###`` headings,
        ``-`` lists, ``[text](url)`` links, fenced code blocks, and
        inline ``code``. Anything else is passed through escaped. We do
        not aim to be a full Markdown parser; we aim to render the
        output of ``ReportGenerator.generate_markdown`` faithfully.
        """

        import html
        import re as _re

        out: list[str] = []
        in_code = False
        in_list = False
        for raw_line in markdown.splitlines():
            line = raw_line.rstrip()
            if line.startswith("```"):
                if in_code:
                    out.append("</code></pre>")
                    in_code = False
                else:
                    out.append("<pre><code>")
                    in_code = True
                continue
            if in_code:
                out.append(html.escape(line))
                continue
            if line.startswith("### "):
                if in_list:
                    out.append("</ul>")
                    in_list = False
                out.append(f"<h3>{_inline_markdown_to_html(line[4:])}</h3>")
            elif line.startswith("## "):
                if in_list:
                    out.append("</ul>")
                    in_list = False
                out.append(f"<h2>{_inline_markdown_to_html(line[3:])}</h2>")
            elif line.startswith("# "):
                if in_list:
                    out.append("</ul>")
                    in_list = False
                out.append(f"<h1>{_inline_markdown_to_html(line[2:])}</h1>")
            elif line.startswith("- "):
                if not in_list:
                    out.append("<ul>")
                    in_list = True
                out.append(f"<li>{_inline_markdown_to_html(line[2:])}</li>")
            elif line.strip() == "":
                if in_list:
                    out.append("</ul>")
                    in_list = False
            else:
                if in_list:
                    out.append("</ul>")
                    in_list = False
                out.append(f"<p>{_inline_markdown_to_html(line)}</p>")
        if in_list:
            out.append("</ul>")
        return "".join(out)

    def render_index_html() -> tuple[int, bytes, str]:
        body = _render_index_html_body()
        return 200, _HTML_SHELL.format(title="GitHub Engineer", body=body).encode(
            "utf-8"
        ), "text/html; charset=utf-8"

    def _render_index_html_body() -> str:
        briefs: list[dict[str, str]] = []
        if output_dir.exists():
            for path in sorted(output_dir.glob("*_*.md"), reverse=True):
                if not path.is_file():
                    continue
                briefs.append(
                    {
                        "file": path.name,
                        "size_bytes": str(path.stat().st_size),
                        "modified": datetime.fromtimestamp(
                            path.stat().st_mtime, tz=timezone.utc
                        ).strftime("%Y-%m-%d %H:%M UTC"),
                    }
                )
        memory = DecisionMemory.load(args.memory_path)
        sections: list[str] = []
        sections.append(
            "<h2>Overview</h2>"
            "<div class='metric-grid'>"
            f"<div class='metric'><div class='label'>Briefs on disk</div><div class='value'>{len(briefs)}</div></div>"
            f"<div class='metric'><div class='label'>Tracked repositories</div><div class='value'>{len(repos)}</div></div>"
            f"<div class='metric'><div class='label'>Decision records</div><div class='value'>{len(memory.records)}</div></div>"
            "</div>"
        )
        if briefs:
            rows = "\n".join(
                "<tr><td><a href='/ui/briefs/{file}'>{file}</a></td>"
                "<td>{size_bytes}</td><td class='muted'>{modified}</td></tr>".format(**brief)
                for brief in briefs
            )
            sections.append(
                "<h2>Recent briefs</h2>"
                "<table><thead><tr><th>File</th><th>Size</th><th>Modified</th></tr></thead>"
                f"<tbody>{rows}</tbody></table>"
            )
        else:
            sections.append(
                "<h2>Recent briefs</h2>"
                "<div class='empty'>No briefs yet. Run <code>ghe --repo owner/name</code> to generate one.</div>"
            )
        sections.append(
            "<h2>Configuration</h2>"
            "<table><tbody>"
            f"<tr><th>Tracked repos</th><td>{', '.join(repos)}</td></tr>"
            f"<tr><th>Output directory</th><td><code>{output_dir}</code></td></tr>"
            f"<tr><th>History directory</th><td><code>{history_dir}</code></td></tr>"
            "</tbody></table>"
        )
        return "".join(sections)

    def render_brief_html(repo: str) -> tuple[int, bytes, str]:
        if not output_dir.exists():
            return (
                404,
                _HTML_SHELL.format(
                    title="Brief not found", body="<div class='empty'>Output directory does not exist.</div>"
                ).encode("utf-8"),
                "text/html; charset=utf-8",
            )
        safe = repo.replace("/", "_")
        files = sorted(
            (path for path in output_dir.glob(f"{safe}_*.md") if path.is_file()),
            key=lambda path: path.name,
            reverse=True,
        )
        if not files:
            return (
                404,
                _HTML_SHELL.format(
                    title="Brief not found",
                    body=f"<div class='empty'>No brief for <code>{repo}</code> yet.</div>",
                ).encode("utf-8"),
                "text/html; charset=utf-8",
            )
        body = _render_brief_html_body(files[0])
        return 200, _HTML_SHELL.format(title=f"Brief — {repo}", body=body).encode(
            "utf-8"
        ), "text/html; charset=utf-8"

    def _render_brief_html_body(path: Path) -> str:
        markdown = path.read_text(encoding="utf-8")
        inner = _markdown_to_html(markdown)
        return (
            "<p class='muted'>"
            f"File: <code>{path.name}</code> &middot; size: {path.stat().st_size} bytes"
            "</p>"
            f"<div class='brief-body'>{inner}</div>"
            "<p><a href='/ui/'>&larr; back to overview</a></p>"
        )

    def render_briefs_index_html() -> tuple[int, bytes, str]:
        if not output_dir.exists():
            body = "<div class='empty'>Output directory does not exist.</div>"
        else:
            briefs = sorted(output_dir.glob("*_*.md"), reverse=True)
            if not briefs:
                body = "<div class='empty'>No briefs yet.</div>"
            else:
                rows = "\n".join(
                    "<tr><td><a href='/ui/briefs/{name}'>{name}</a></td>"
                    "<td>{size}</td><td class='muted'>{modified}</td></tr>".format(
                        name=path.name,
                        size=path.stat().st_size,
                        modified=datetime.fromtimestamp(
                            path.stat().st_mtime, tz=timezone.utc
                        ).strftime("%Y-%m-%d %H:%M UTC"),
                    )
                    for path in briefs
                    if path.is_file()
                )
                body = (
                    "<table><thead><tr><th>File</th><th>Size</th><th>Modified</th></tr></thead>"
                    f"<tbody>{rows}</tbody></table>"
                )
        return 200, _HTML_SHELL.format(title="All briefs", body=body).encode(
            "utf-8"
        ), "text/html; charset=utf-8"

    def render_decisions_html() -> tuple[int, bytes, str]:
        memory = DecisionMemory.load(args.memory_path)
        if not memory.records:
            body = (
                "<p class='muted'>No decisions recorded yet. Use "
                "<code>ghe --record-decision ...</code> or "
                "<code>POST /decisions</code> to add one.</p>"
            )
        else:
            rows = []
            for record in memory.records:
                status_class = f"badge badge-{record.status}"
                topics: list[str] = []
                if record.issue_numbers:
                    topics.append(
                        "issues " + ", ".join(f"#{n}" for n in record.issue_numbers)
                    )
                if record.themes:
                    topics.append("themes " + ", ".join(record.themes))
                timestamp = (
                    record.created_at.strftime("%Y-%m-%d %H:%M UTC")
                    if record.created_at
                    else "—"
                )
                rows.append(
                    "<tr>"
                    f"<td><span class='{status_class}'>{record.status}</span></td>"
                    f"<td class='muted'>{timestamp}</td>"
                    f"<td>{'; '.join(topics) or '<span class=muted>no scope</span>'}</td>"
                    f"<td>{record.reason or '<span class=muted>—</span>'}</td>"
                    "</tr>"
                )
            body = (
                "<table><thead><tr><th>Status</th><th>Recorded</th>"
                "<th>Scope</th><th>Reason</th></tr></thead>"
                f"<tbody>{''.join(rows)}</tbody></table>"
            )
        return 200, _HTML_SHELL.format(title="Decision memory", body=body).encode(
            "utf-8"
        ), "text/html; charset=utf-8"

    def render_decisions() -> tuple[int, bytes, str]:
        from .models import DecisionRecord  # local import keeps main.py at the top lean

        memory = DecisionMemory.load(args.memory_path)
        body = json.dumps(
            [record.model_dump(mode="json", exclude_none=True) for record in memory.records],
            indent=2,
            ensure_ascii=False,
        ).encode("utf-8")
        return 200, body, "application/json"

    def render_decisions_text() -> tuple[int, bytes, str]:
        import io
        import contextlib

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            list_decisions(argparse.Namespace(memory_path=args.memory_path))
        body = buffer.getvalue().encode("utf-8")
        return 200, body, "text/plain; charset=utf-8"

    def handle_post_decision(query: dict[str, list[str]]) -> tuple[int, bytes, str]:
        from datetime import datetime, timezone
        from .models import DecisionRecord

        status = (query.get("status", [""])[0] or "").strip()
        if status not in {"accepted", "rejected", "deferred"}:
            return 400, b'{"error":"status must be accepted|rejected|deferred"}', "application/json"
        try:
            record = DecisionRecord(
                status=status,  # type: ignore[arg-type]
                reason=query.get("reason", [""])[0],
                issue_numbers=[int(value) for value in query.get("issue_number", []) if value],
                themes=[value for value in query.get("theme", []) if value],
                goals=[value for value in query.get("goal", []) if value],
                guardrails=[value for value in query.get("guardrail", []) if value],
                created_at=datetime.now(timezone.utc),
            )
        except (TypeError, ValueError) as exc:
            return 400, json.dumps({"error": f"invalid record: {exc}"}).encode("utf-8"), "application/json"
        memory = DecisionMemory.load(args.memory_path)
        memory.record_decision(record)
        return 201, json.dumps(record.model_dump(mode="json", exclude_none=True), indent=2).encode(
            "utf-8"
        ), "application/json"

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:  # noqa: A002
            sys.stderr.write(
                f"[{self.log_date_time_string}] {self.address_string()} {format % args}\n"
            )

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"
            if path == "/healthz":
                status, body, content_type = (
                    200,
                    b'{"status":"ok","service":"github-engineer"}',
                    "application/json",
                )
            elif path == "/decisions.txt":
                status, body, content_type = render_decisions_text()
            elif path in ("/", "/briefs"):
                # JSON or HTML depending on the Accept header. The machine
                # API callers (curl without an explicit Accept) get JSON
                # by default; browsers (Accept: text/html) get the UI.
                if "text/html" in (self.headers.get("Accept") or ""):
                    status, body, content_type = render_index_html()
                else:
                    status, body, content_type = render_index()
            elif path == "/decisions":
                if "text/html" in (self.headers.get("Accept") or ""):
                    status, body, content_type = render_decisions_html()
                else:
                    status, body, content_type = render_decisions()
            elif path == "/ui":
                status, body, content_type = render_index_html()
            elif path == "/ui/":
                status, body, content_type = render_index_html()
            elif path == "/ui/briefs":
                status, body, content_type = render_briefs_index_html()
            elif path.startswith("/ui/brief/"):
                repo = path.removeprefix("/ui/brief/").strip()
                status, body, content_type = render_brief_html(repo)
            elif path == "/ui/decisions":
                status, body, content_type = render_decisions_html()
            elif path.startswith("/brief/"):
                repo = path.removeprefix("/brief/").strip()
                status, body, content_type = render_brief(repo)
            else:
                status, body, content_type = (
                    404,
                    b'{"error":"not found"}',
                    "application/json",
                )
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"
            if path != "/decisions":
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error":"not found"}')
                return
            length = int(self.headers.get("Content-Length", "0") or 0)
            raw = self.rfile.read(length) if length else b""
            try:
                payload = json.loads(raw.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                payload = parse_qs(raw.decode("utf-8"))
            if not isinstance(payload, dict):
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error":"expected JSON object"}')
                return
            # Normalise repeated keys into lists so parse_qs and JSON both work.
            normalised: dict[str, list[str]] = {}
            for key, value in payload.items():
                if isinstance(value, list):
                    normalised[key] = [str(item) for item in value]
                else:
                    normalised[key] = [str(value)]
            status, body, content_type = handle_post_decision(normalised)
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"github-engineer serving on http://{host}:{port}", flush=True)
    print("Routes:", flush=True)
    print(f"  GET  /                  index of briefs", flush=True)
    print(f"  GET  /briefs            same as /", flush=True)
    print(f"  GET  /brief/<repo>      latest brief as Markdown", flush=True)
    print(f"  GET  /decisions         decision memory as JSON", flush=True)
    print(f"  GET  /decisions.txt     decision memory as plain text", flush=True)
    print(f"  POST /decisions         record a decision (JSON body)", flush=True)
    print(f"  GET  /healthz           liveness check", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
