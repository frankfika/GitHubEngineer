# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- **Tests.** Eight pytest tests cover config loading, report generation, the
  three v0.2-v0.4 capabilities, and the `main()` end-to-end integration paths
  (success, no recent issues, failure). Run with `pytest tests/ -v`.
- **Documentation.** `README.md` covers local usage, the GitHub Action, config
  fields, and limits. `DESIGN.md` and `IMPLEMENTATION_PLAN.md` capture the
  design rationale and the v0.1-v0.4 delivery plan.
