# Troubleshooting

A working list of symptoms, their likely causes, and the first thing to
try. The CLI's `format_error` helper mirrors the most common entries so
the same hint is available without leaving the terminal.

## "Missing model.api_key"

You ran a command that calls the LLM without an API key.

- Set `LLM_API_KEY` in the environment.
- Or add `model.api_key` to `.ghe/config.yml`.
- The read-only commands (`--show-latest`, `--list-decisions`) do **not**
  need a key.

## "Missing model.model_name"

Same as above, but for the model identifier. Most providers need the
provider-specific name (e.g. `gpt-4o-mini`, `claude-sonnet-4-20250514`).
Set `LLM_MODEL` or `model.model_name`.

## "LLM request failed"

The call reached the provider but was rejected. Common causes:

- **Bad base URL.** Some providers reject custom `base_url`. Try the
  canonical endpoint and re-add the custom URL only if the provider
  documents it.
- **Wrong model name.** Providers 404 on unknown model identifiers.
- **Quota exceeded.** Cloud providers surface this as a 429 or 402.
  Switch to a smaller model, lower `analysis.max_issues_for_llm`, or
  wait for the quota to reset.

## "Could not parse LLM JSON"

The model returned prose instead of a JSON object. The recovery in
`src/llm_client.py` strips code fences and looks for the first `{` in
the response. If neither works, the model is producing a structured
output the tool cannot interpret.

- Try a model with stronger JSON instruction following.
- Lower `analysis.max_issues_for_llm` so the prompt is shorter.
- Open an issue with the exact model name and a sample response if the
  problem persists.

## "GitHub API rate limit exceeded"

The unauthenticated limit is 60 requests per hour. With a `GITHUB_TOKEN`
the limit jumps to 5 000 per hour.

- Export a token: `export GITHUB_TOKEN=ghp_...`.
- If you are already using a token, you may be sharing its quota with
  another CI workflow. Use a dedicated token per environment.

## "Could not access repository"

PyGithub raised 404 or 401.

- Verify `repo.full_name` in `.ghe/config.yml` (or `--repo owner/name`)
  matches a real repository.
- Verify the token has access. For private repos, the token must have
  `repo` scope; for org-managed repos, it must also be a member of the
  org or be installed with the right SSO.

## "Failed to fetch issues"

The token can read the repository but the issues listing call failed.
Usually a transient API error; re-run after a few seconds. If the
message persists, open an issue with the full error.

## Empty `## Top Priorities`

The brief ran successfully but the LLM produced no priorities, or every
candidate was filtered out before the call.

- **Lookback window too short.** Lower `analysis.lookback_days` to 1
  if you are testing with a fresh repository, or raise it to 30 if the
  repository is low-traffic.
- **Decision memory rejecting everything.** Run
  `ghe --list-decisions` and inspect the rejected themes. If you want
  them back, edit `.ghe/memory/decisions.yml` to delete the entry.
- **Age filter too aggressive.** Lower `analysis.min_issue_age_hours`
  if every issue was created in the last few hours.

## "--prepare-issue <N>: is not in this brief's recommended priorities"

The issue number you passed to `--prepare-issue` was not in the current
brief's Top N. The check is intentional — preparing a task for a
non-prioritised issue is almost always a mistake.

1. Open the latest brief (`ghe --show-latest`) and pick an issue from
   the Top N.
2. Re-run `ghe --prepare-issue <N> --allowed-directory ... --forbidden-directory ...`.

## "--agent-repo-path is required"

`--delegate-task` needs a target repository directory. Pass
`--agent-repo-path /absolute/path/to/target-repo`.

## "Executable 'X' is not in the command allowlist"

The `--adapter generic-cli` path validates the executable name against
an allowlist. Pass `--generic-executable` with a name on the allowlist
(`codex`, `claude`, `opencode`, `aider`), or update
`DEFAULT_EXECUTABLE_ALLOWLIST` in `src/delegation.py` and the matching
`allowed_executables=[...]` argument to `execute_delegation`.

## Performance: brief takes more than 5 minutes

On a 50-issue repository with `gpt-4o-mini`, a brief should complete in
well under 30 seconds. If yours is slow:

- Network: GitHub API + LLM provider round trips. Profile with
  `time ghe --config .ghe/config.yml --repo owner/name`.
- Token: missing `GITHUB_TOKEN` triggers the 60 req/hr limit and
  every page request becomes a long retry loop.
- LLM: some providers take 10+ seconds per call. Try a smaller model
  or fewer candidates (`analysis.max_issues_for_llm: 20`).
