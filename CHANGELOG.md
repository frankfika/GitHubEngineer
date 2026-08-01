# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Production desktop release path.** A pinned GitHub Actions workflow now
  tests and builds both Apple Silicon and Intel macOS bundles, and can sign,
  notarize, and publish a release when Apple Developer credentials are
  configured. The packaged app enables the hardened runtime with the minimum
  entitlement required by its embedded Python sidecar.
- **Explicit host verification.** When an isolated container runtime is not
  available, a repair can be re-verified on the host only after a per-task
  risk confirmation. Verification remains fail-closed, and a failed test run
  still prevents publishing.
- **Packaged repair workers.** Frozen desktop builds can now launch start,
  revise, verify, and publish workers through an internal worker entry point.
  Unexpected worker exits are persisted instead of leaving jobs queued
  forever.
- **Trend baseline.** `src/history.py` saves each brief as a versioned JSON
  snapshot under `.ghe/history/` and computes a week-over-week diff
  (new / resolved / score-shifted issues, new / dropped clusters). The diff is
  rendered into `brief.trend` on the next run so maintainers can see what
  changed since the previous brief. Corrupt history files are skipped
  silently.
- **Cost control.** `LLMClient.last_usage` captures `prompt_tokens`,
  `completion_tokens`, and `total_tokens` from the provider's response.
  `IssueAnalyzer.max_prompt_chars` (default 90 000, ~30 K tokens) truncates
  the lowest-signal candidates and reports the drop count. The Markdown
  report gains a `## Cost` section listing the actual numbers.
- **Multi-repo support.** `get_target_repos` accepts a top-level `repos:`
  list in `.ghe/config.yml`, a comma-separated `--repo owner/a,b/c`, or the
  legacy single-repo form. The CLI now writes one report per repository
  using the same LLM client.
- **Read-only subcommands.** `ghe --show-latest [--repo owner/name]`
  prints the most recent brief Markdown to stdout; `ghe --list-decisions`
  prints a one-line summary of every record in
  `.ghe/memory/decisions.yml`. Both bypass the API key requirement.
- **3-step pipeline.** `ghe --pipeline` runs brief → prepare → delegate
  dry-run in one shot for the top issue of the last (or only) target repo.
- **Packaging polish.** `Makefile` with `venv` / `install` / `install-dev`
  / `test` / `test-fast` / `lint` / `smoke` / `clean` targets. `README.md`
  adds a cost estimate and a multi-repo config example. `examples/sample_report.md`
  is now a real-shape brief, not a placeholder.
- **Repository startup restoration.** The assistant restores the last valid
  repository selection, falls back to the backend default or first tracked
  repository, and loads its issue inbox immediately. Empty / failed loads
  still show clear onboarding or retry states. Sidebar pills show green
  "我的" / amber "外部" tags so maintainers can distinguish owner and fork
  contribution flows.
- **Dev-only mock route.** `GHE_MOCK_REPOSITORIES=1` short-circuits
  /api/repositories with a fixed owner + monitor pair (no GitHub token
  required). Useful for UI development, screenshots, and the
  failure-recovery flow.

### Changed

- Quitting or closing the desktop app now terminates the entire embedded
  backend process group, including the PyInstaller child process, so port 8765
  is not left occupied by an orphaned server.
- `report_generator.py` now renders every recommended issue as a clickable
  `[[#N](url)]` link instead of a bare `#N:`. Falls back to the plain form
  when the model-supplied URL is empty.
- `analyzer.py` filters out issues younger than `analysis.min_issue_hours`
  (default 24, previously declared but never read) so reports stop
  recommending issues the moment they are opened.
- `github_client.get_open_issues` walks `get_issues()` with explicit
  per-page fetching and a `max_pages` cap (default 10) so 100 K+ issue
  repositories cannot exhaust the GitHub API quota.
- `main.py` catches the `HistoryError` family so a single corrupt history
  file never breaks the user-facing report.

### Tests

- 68 pytest tests (was 8). New files: `test_github_client.py`,
  `test_llm_client.py`, `test_analyzer.py`, `test_delegation.py`,
  `test_history.py`, `test_main_subcommands.py`, `test_performance_50_issues.py`.
  `test_report_generator.py` grew from one to four cases.

## [0.1.0] - 2026-07-21

### Added

- **v0.1 Maintainer Brief.** Read open GitHub issues (`src/github_client.py`), rank
  them with an OpenAI-compatible model using the prompt in
  `prompts/maintainer_brief.md`, and render a Markdown report
  (`src/report_generator.py`). The CLI entry point lives in `src/main.py` and is
  also exposed as the `ghe` console script after `pip install -e .`.
- **v0.1 Config & Schema.** Load configuration from `.ghe/config.yml` (see
  `.ghe/config.example.yml`) via `src/config.py`, with Pydantic models in
  `src/models.py` validating `repo`, `github`, `model`, `output`, and
  `analysis` sections. Environment variable fallback is wired through
  `python-dotenv` (`config.example.yml` uses `${VAR}` placeholders).
- **v0.1 GitHub Action.** `action.yml` is a composite Action that installs
  dependencies, generates the brief, writes the report to `$GITHUB_STEP_SUMMARY`,
  and uploads it as an artifact. The example workflow
  `.github/workflows/maintainer-brief.example.yml` shows a weekly schedule.
- **v0.2 Decision Memory.** `src/memory_manager.py` reads and writes
  `.ghe/memory/decisions.yml`. The `--record-decision {accepted,rejected,deferred}`
  flag captures `theme`, `reason`, `goal`, and `guardrail`; rejected issues are
  filtered out of future recommendations so the same work is not proposed again.
- **v0.3 Agent-Ready Task.** `src/task_preparer.py` turns an approved priority
  (selected via `--prepare-issue`) into a bounded Markdown task with objective,
  reproduction steps, acceptance criteria, risks, and test plan. The task is
  written to `tasks/owner_name_issue_N.md`; repository file locations are kept
  as `待定位` until a repository-search integration is added. Prompt:
  `prompts/task_prep.md`.
- **v0.4 Delegation.** `src/delegation.py` prepares a dry-run handoff plan for
  Codex, Claude Code, or any allowlisted generic CLI (`--adapter codex |
  claude-code | generic-cli`). The plan is safe by default; `--execute` is
  required to start the agent, and task content is passed over standard input
  rather than composed into a shell command.
- **Tests.** 12 pytest tests cover config loading, report generation, the
  three v0.2-v0.4 capabilities, and the `main()` end-to-end integration paths
  (success, no recent issues, failure). Run with `pytest tests/ -v`.
- **Documentation.** `README.md` covers local usage, the GitHub Action, config
  fields, and limits. `DESIGN.md` and `IMPLEMENTATION_PLAN.md` capture the
  design rationale and the v0.1-v0.4 delivery plan.
