# Release notes

This file collects the user-facing notes for every tagged release. The
maintainer copies the matching section into the GitHub Release body when
publishing a tag; the `## Cost` table at the end is computed by
`benchmarks/cost.py` and updated each release.

## v1.0.0 - 2026-07-21

### Highlights

- **v0.1 Maintainer Brief.** Read open GitHub issues, rank them with an
  OpenAI-compatible LLM, and render a Markdown report with clickable
  `[[#N](url)]` links, Quick Wins, possible duplicate clusters, missing
  information, the week-over-week trend line, and the prompt/completion
  token usage.
- **v0.2 Decision Memory.** Reject themes once and never see them again.
- **v0.3 Agent-Ready Task.** Turn an approved priority into a bounded
  Markdown task with objective, repro steps, acceptance criteria, risks,
  and a test plan.
- **v0.4 Delegation.** Hand the prepared task to Codex, Claude Code, or
  any allowlisted generic CLI. Dry-run by default; `--execute` is the
  only thing that starts a subprocess.
- **v1.0 multi-repo.** Brief multiple repositories in a single run via
  `repos:` in config or a comma-separated `--repo a/b,c/d`.
- **v1.0 trend baseline.** Each run is persisted to `.ghe/history/`
  and the next run renders a one-line diff against the previous one.
- **v1.0 cost control.** `max_prompt_chars` cap, dropped-candidate
  counter, and a `## Cost` section with real provider token counts.
- **v1.0 subcommands.** `ghe --show-latest` (no LLM key required),
  `ghe --list-decisions`, and `ghe --pipeline` for a one-shot brief
  → prepare → delegate-dry-run flow.

### Packaging

- `pyproject.toml` declares the `ghe` console script and the
  `pip install -e ".[dev]"` dev extra.
- `Makefile` with `venv`, `install`, `install-dev`, `test`, `lint`,
  `smoke`, `bench`, `bench-cost`, and `clean` targets.
- `benchmarks/perf.py` and `benchmarks/cost.py` keep an eye on the
  v0.1 budgets.
- `SECURITY.md` and `CODE_OF_CONDUCT.md` are now in place. Issue
  templates (`bug`, `feature`, `question`) and a PR template live under
  `.github/`.
- `ARCHITECTURE.md` documents the module boundaries and the threat
  model.

### Tests

85/85 pytest cases (was 8 in the v0.1-only draft). New coverage:

- `tests/test_github_client.py` — pagination, since filter, max_pages
  cap, reaction error, repo 404.
- `tests/test_llm_client.py` — success, API error, timeout, empty
  content, no choices, JSON fence stripping, JSON recovery, top-level
  non-object, usage capture, missing usage.
- `tests/test_analyzer.py` — age filter on/off, candidate ranking,
  cluster grouping, ground-truth title + URL injection, sort + dedupe,
  malformed payload, empty brief, rejected theme filter, prompt
  budget truncation, token usage, mock usage.
- `tests/test_delegation.py` — adapter plans, allowlist, shell-syntax
  rejection, opt-in required, safe subprocess args, timeout, allowed
  root, control bytes, safe executables.
- `tests/test_history.py` — save/load round-trip, missing directory,
  corrupt file skip, new vs resolved, empty prior, no-prior summary,
  record_from_brief round-trip, OSError wrapping.
- `tests/test_memory_manager.py` — load empty, parse YAML, legacy
  aliases, corrupt YAML, save round-trip, filter rejected numbers and
  themes, prompt_context dedupe.
- `tests/test_main_subcommands.py` — `--show-latest` happy path, no
  reports, no api key required; `--list-decisions` with and without
  data; `--init` writes and refuses to overwrite.
- `tests/test_performance_50_issues.py` — 60-issue end-to-end pipeline
  finishes in under 5 seconds (current: ~0.4 s on dev hardware).
- `tests/test_config.py` expanded to 12 cases (load, lenient load,
  validation, multi-repo resolution, dedupe, malformed input).

### Known limitations

- The `ghe --pipeline` command chains prepare and delegate-dry-run for
  the last (or only) repository. Looping pipeline across multiple
  repos is the user's job for now.
- `--record-decision` and `--pipeline` are independent: a single
  command cannot both record a decision and chain a task. A future
  v1.1 release may add an atomic "accept and delegate" flow.
- Cost numbers in this release were measured on dev hardware with a
  stub LLM. Real provider numbers will land once the PyPI publish
  workflow runs against a live key.

### Estimated run cost

| Model | 50 issues | 200 issues |
| --- | --- | --- |
| `gpt-4o-mini` | $0.0054 | $0.0194 |
| `claude-haiku-4` | $0.0280 | $0.1020 |
| `claude-sonnet-4` | $0.1114 | $0.3905 |
| `deepseek-chat` | $0.0048 | $0.0179 |

Refreshed each release by `python benchmarks/cost.py --issues 50` and
`--issues 200` for every model in the table.
