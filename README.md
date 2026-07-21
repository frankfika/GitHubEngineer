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

Create and activate an isolated environment, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
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
- `.ghe/memory/decisions.yml`: optional, versioned maintainer decisions

## Limits

- v0.1 supports GitHub issues only.
- The output is advisory; maintainers make the final decision.
- Large repositories should keep `max_issues_for_llm` bounded to control cost.
- The report contains issue titles and bodies sent to the configured LLM
  provider. Use a provider that is appropriate for your repository data.
- Coding-agent delegation can modify the target repository only when `--execute`
  is explicitly supplied; review the generated task and dry-run plan first.
