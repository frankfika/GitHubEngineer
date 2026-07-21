# Architecture

This document explains how the pieces of GitHub Engineer fit together and why
each boundary exists. It is intended for contributors who want to extend the
tool without re-deriving the design.

## Pipeline at a glance

```
                  +----------------------+
                  | .ghe/config.yml      |
                  | .ghe/memory/         |
                  | .ghe/history/        |
                  +----------+-----------+
                             |
                             v
+--------+        +---------+----------+        +-----------------+
|  ghe   |  ----> |   src/main.py       |  ----> |  src/github_     |
|  CLI   |        |   (argparse + glue) |        |  client.py       |
+--------+        +---------+----------+        +--------+--------+
                             |                            |
                             v                            v
                  +----------+-----------+      +---------+----------+
                  |  src/llm_client.py   |      |  GitHub REST API   |
                  |  (OpenAI-compatible) |      +--------------------+
                  +----------+-----------+
                             |
                             v
                  +----------+-----------+
                  |  src/analyzer.py     |
                  |  + memory_manager    |
                  |  + history.py        |
                  +----------+-----------+
                             |
                             v
                  +----------+-----------+
                  |  src/report_         |
                  |  generator.py        |
                  +----------+-----------+
                             |
                  +----------+----------------------+
                  |                                 |
                  v                                 v
        +-------------------+              +-------------------+
        | reports/*.md      |              | tasks/*.md        |
        | + history/*.json  |              | (when --pipeline) |
        +-------------------+              +---------+---------+
                                                      |
                                                      v
                                          +-----------+----------+
                                          |  src/delegation.py   |
                                          |  (--execute opt-in)  |
                                          +----------------------+
```

## Module boundaries

| File | Owns | Does not own |
| --- | --- | --- |
| `src/config.py` | Reading YAML, expanding `${ENV}`, validating required keys. Two entry points: `load_config` (strict, used by every command that calls an LLM) and `load_config_lenient` (used by read-only subcommands that should not require an LLM key). | Talking to GitHub, the LLM, or the file system beyond the config path. |
| `src/github_client.py` | Walking `get_issues()` page by page with a hard `max_pages` cap so 100 K+ repositories cannot exhaust the quota. Translating PyGithub exceptions into `GitHubClientError`. | Filtering, ranking, or writing anything. |
| `src/llm_client.py` | Calling an OpenAI-compatible chat endpoint, recovering from JSON the model wrapped in code fences, exposing `last_usage` for cost reporting. | Selecting the model, crafting the prompt, or interpreting the response. |
| `src/analyzer.py` | The decision logic: filter by age, drop rejected themes, pick the highest-signal candidates, call the LLM once, sort and de-dupe, re-anchor `title` and `url` to ground-truth GitHub data so the model cannot fake them. Truncating the candidate list when the prompt would exceed `max_prompt_chars`. | Generating Markdown, persisting history, recording decisions. |
| `src/memory_manager.py` | Reading and writing `.ghe/memory/decisions.yml` atomically. `filter_issues` drops rejected numbers and themes; `prompt_context` returns only durable guidance suitable for a prompt. | Reasoning about whether a decision is "right" — that is the maintainer's call. |
| `src/history.py` | Persisting one JSON snapshot per run, comparing the latest snapshot to the new run, and rendering a one-line trend summary. Skips corrupt files silently. | Mutating the brief in flight; main.py applies the diff. |
| `src/report_generator.py` | Turning a `MaintainerBrief` into Markdown. The clickable link rendering, Quick Wins section, Possible Duplicate Clusters, Missing Information, Trend, and Cost sections all live here. | Collecting data or making decisions. |
| `src/task_preparer.py` | Turning one approved `IssuePriority` plus its source `IssueMetrics` into a bounded Markdown task. Only publishes model-proposed reproduction steps when their evidence is verbatim in the issue body, to avoid invented repro steps. | Searching the target repository for the affected files. File locations stay `待定位` until a repo-search integration lands. |
| `src/delegation.py` | Building a `DelegationPlan` for Codex, Claude Code, or an allowlisted generic CLI. **Planning** is always allowed; **execution** requires `execute_delegation(..., allow_execution=True)`. Task Markdown is supplied on standard input, never composed into a shell command. | Running the coding agent. |
| `src/main.py` | Argparse, subcommand dispatch, and the orchestration loop. Holds the `format_error` table that maps known error substrings to actionable hints. | Any of the above. It is the only place that wires them together. |

## Why these boundaries

- **No silent shell.** The delegation adapter enforces `shell=False` and a
  regex-checked executable allowlist (`^[A-Za-z0-9][A-Za-z0-9._-]*$`).
  The plan never reaches `os.system`; the task Markdown reaches the
  subprocess through `stdin` only.
- **Model output is data, not instructions.** The analyzer re-anchors
  `title` and `url` to the source GitHub issue so a model cannot trick
  the report into pointing at a malicious page. The task preparer
  refuses to publish reproduction steps that are not verbatim in the
  issue body.
- **Reads are free, writes are explicit.** The decision memory, the
  history, the prepared task, and the delegation plan are each written
  by a single named function call. There is no background daemon and
  no "magic" auto-save.
- **The CLI is the only side effect.** `python -m src.main` is the
  blessed entry point. The `ghe` console script and the GitHub Action
  are thin wrappers that set environment variables and call it.
- **No global state.** Each `LLMClient`, `GitHubClient`, and
  `DecisionMemory` instance owns its data. The analyzer can be
  constructed repeatedly in a single process without surprises.

## Read-only by default

The default configuration produces zero public write operations on the
target repository. Confirmed by `tests/test_github_client.py` (no
write API is exposed) and `action.yml` (`permissions: { issues: read,
contents: read }`). Public writes — comments, labels, issue creation —
are intentionally absent. If you need them, build a separate tool that
takes a `MaintainerBrief` as input and posts the recommendations, so
the trust boundary stays where the human can see it.
