# GitHub Engineer

GitHub Engineer generates a Maintainer Brief for a GitHub repository: the top issues worth a maintainer's attention, with evidence and estimated effort.

It is not a coding agent. It helps decide what should be handled first, then you can hand those tasks to Copilot, Claude Code, Codex, or a human maintainer.

## What Works Today

- Read open GitHub issues
- Rank the most important issues with an OpenAI-compatible model
- Generate a Markdown report in `reports/`
- Write the report to GitHub Actions Step Summary
- Upload the report as a GitHub Actions artifact
- Remember maintainer decisions locally, so rejected work is not recommended again
- Turn an approved recommendation into a bounded, Agent-ready task Markdown file
- Create a safe dry-run handoff plan for Codex or Claude Code

By default, it does not comment on issues, create discussions, apply labels, or modify code.

## Local Usage

Requirements: Python 3.11 or later, a GitHub token that can read issues, and an
OpenAI-compatible API key. Public repositories can be read without a GitHub
token, but using one avoids the low unauthenticated API limit.

Install with `pip` (recommended for users) or with `pip install -e .` if you
intend to hack on the code:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
# or, after `pip install -e .[dev]`, use the `ghe` entry point:
python -m src.main --help
```

Create a config:

```bash
cp .ghe/config.example.yml .ghe/config.yml
```

Set environment variables:

```bash
export GITHUB_TOKEN="github_token" # optional for public repositories
export LLM_API_KEY="model_api_key"
export LLM_MODEL="gpt-4o-mini"
```

`LLM_BASE_URL` is optional when using the default OpenAI endpoint. Set it when
using another OpenAI-compatible provider:

```bash
export LLM_BASE_URL="https://your-provider.example/v1"
```

Run:

```bash
python -m src.main --config .ghe/config.yml --repo owner/name
```

The report will be written to `reports/owner_name_YYYYMMDD.md`.

## Decisions, Tasks, and Coding Agents

Record a maintainer decision explicitly. This is the only command that writes
`.ghe/memory/decisions.yml`; normal report generation only reads it.

```bash
python -m src.main --record-decision rejected \
  --issue-number 42 --theme "dark mode" \
  --reason "Not on this year's roadmap" \
  --goal "Improve reliability" --guardrail "Do not add theme customization"
```

Generate a fresh brief and prepare one of its recommended issues as a bounded
task. Selecting the issue with `--prepare-issue` is the explicit approval step.

```bash
python -m src.main --config .ghe/config.yml --repo owner/name \
  --prepare-issue 42 --allowed-directory src/ --forbidden-directory infra/
```

The task is written to `tasks/owner_name_issue_42.md`. It includes known facts,
verified reproduction information, acceptance criteria, risk, directory bounds,
and test guidance. It deliberately marks repository files as “待定位” until a
repository-search integration is added.

Plan a handoff to a local coding agent. This command is dry-run by default and
does not start an external process:

```bash
python -m src.main --delegate-task tasks/owner_name_issue_42.md \
  --adapter codex --agent-repo-path /absolute/path/to/target-repo
```

Only after reviewing the task and plan, add `--execute` to allow the selected
agent to run. Task content is supplied over standard input; it is never composed
into a shell command.

## GitHub Action Usage

Copy `.github/workflows/maintainer-brief.example.yml` to
`.github/workflows/maintainer-brief.yml`, then commit it to the repository
where you want to generate briefs.

`.ghe/config.yml` is optional for the Action. If it is missing, the Action uses workflow inputs and environment variables.

Required secrets:

- `LLM_API_KEY`

`GITHUB_TOKEN` is provided by GitHub Actions.

Optional configuration:

- Set the repository variable `LLM_MODEL` to select a model; it defaults to
  `gpt-4o-mini`.
- Set the secret `LLM_BASE_URL` only for an OpenAI-compatible endpoint other
  than OpenAI's default endpoint.
- To use a checked-in configuration file, pass `config-path` to the action.
  Keep its `output.output_dir` aligned with the action's `report-path` input
  (both default to `reports/*.md`). Do not put API keys in that file.

The Action writes the brief to the workflow Step Summary and uploads `reports/*.md` as an artifact.

## Config

See `.ghe/config.example.yml`.

Important fields:

- `repo`: target repository
- `model`: OpenAI-compatible model settings
- `output.output_dir`: where Markdown reports are written
- `analysis.lookback_days`: how far back to inspect updated issues
- `analysis.max_issues_for_llm`: how many candidate issues to send to the model
- `analysis.min_issue_age_hours`: drop issues newer than this (default 24)
- `analysis.top_n`: how many top priorities to surface (default 3)
- `repos`: optional list form (`- owner/name`) for multi-repo briefs (v1.0)
- `.ghe/memory/decisions.yml`: optional, versioned maintainer decisions
- `.ghe/history/`: optional trend baseline directory; created on first run

## Cost

A single brief against a 50-issue repo typically costs well under **$0.10**
with `gpt-4o-mini` and around **$0.20–$0.40** with `claude-sonnet-4` based on
the default `max_issues_for_llm=50` and `max_prompt_chars=90_000` budget. The
report's `## Cost` section prints the exact prompt and completion token counts
for the run, and the analyzer silently drops the lowest-signal issues when the
prompt would otherwise exceed the budget. You can cap spend by lowering
`analysis.max_issues_for_llm` or by pinning a cheaper model via
`LLM_MODEL`/`model.model_name`.

## Example Output

See `examples/sample_report.md` for the shape of a real brief. The rendered
Markdown includes a clickable `[[#N](url)]` link for every recommended issue,
a separate Quick Wins section, possible duplicate clusters, the missing-info
list, the week-over-week trend line, and the prompt/completion token usage.

## Why not just use GitHub Copilot / Agentic Workflows?

Copilot and Agentic Workflows are *execution* tools: they read a single
issue and ship a PR. GitHub Engineer is a *decision* tool: it reads every
open issue in a repository, scores them against your goals and guardrails,
and tells you **which** three are worth a maintainer's attention this week —
with evidence. The two are complementary, not competitive. Use GitHub
Engineer to pick the next issue, then hand the prepared task to Copilot,
Claude Code, or Codex with `ghe --pipeline` (or `--prepare-issue` + `--delegate-task`).

## FAQ

**Q: Does it comment on issues or apply labels?**
No. The tool is read-only by default. It only writes local files
(`reports/*.md`, `.ghe/history/*.json`, `tasks/*.md`) and the optional
`$GITHUB_STEP_SUMMARY` when running as an Action.

**Q: Does it work on private repositories?**
Yes, as long as the supplied `GITHUB_TOKEN` has `repo` (or `public_repo`)
scope on the target. The tool does not store the token anywhere outside the
runtime memory of the CLI process.

**Q: How much does one run cost?**
Under **$0.10** with `gpt-4o-mini` and around **$0.20–$0.40** with
`claude-sonnet-4` for a 50-issue weekly brief. See the `## Cost` section
of the generated report for the exact numbers.

**Q: Can I run it on multiple repositories at once?**
Yes. Set `repos:` to a list in `.ghe/config.yml`, or pass
`--repo owner/a,owner/b,owner/c`. Each repository gets its own report file
under `reports/`.

**Q: How do I look at the most recent brief without re-running?**
`ghe --show-latest [--repo owner/name] [--config path/to/config.yml]`
prints the newest brief Markdown to stdout. It does not require an LLM key.

**Q: How do I record a maintainer decision so the same work is not proposed again?**
`ghe --record-decision rejected --theme "dark mode" --reason "Not on this year's roadmap"`.
Run `ghe --list-decisions` to see what is currently in memory.

**Q: Does the tool support GitLab?**
Not in v0.x. The decision layer is platform-agnostic; only `src/github_client.py`
would need a sibling for GitLab.

## Troubleshooting

- **"Missing model.api_key"**: set `LLM_API_KEY` in the environment, or add
  `model.api_key` to `.ghe/config.yml`. Read-only commands (`--show-latest`,
  `--list-decisions`) do not need a key.
- **"LLM request failed"**: check `LLM_BASE_URL`, `LLM_API_KEY`, and
  `LLM_MODEL`. Some providers reject custom `base_url`; try the canonical
  endpoint.
- **"GitHub API rate limit exceeded"**: supply a `GITHUB_TOKEN` (free
  tier raises the limit from 60/hr to 5 000/hr) or wait for the reset.
- **"Could not parse LLM JSON"**: the model returned prose. Try a model with
  stronger JSON instruction following, or lower `analysis.max_issues_for_llm`
  so the prompt is shorter and easier to follow.
- **Empty `## Top Priorities`**: the lookback window is too narrow, or every
  issue is filtered by `decision_memory` (rejected themes). Run
  `ghe --list-decisions` to inspect.
- **Brief includes a `--prepare-issue <N>` error**: issue N is not in the
  current brief's Top N. Re-run the brief first, then call `--prepare-issue`
  with one of the recommended numbers.

## Limits

- v0.1 supports GitHub issues only.
- The output is advisory; maintainers make the final decision.
- Large repositories should keep `max_issues_for_llm` bounded to control cost.
- The report contains issue titles and bodies sent to the configured LLM
  provider. Use a provider that is appropriate for your repository data.
- Coding-agent delegation can modify the target repository only when `--execute`
  is explicitly supplied; review the generated task and dry-run plan first.
