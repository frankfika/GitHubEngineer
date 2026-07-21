# Security Policy

## Supported versions

| Version | Supported |
| --- | --- |
| `main` (unreleased) | ✅ |
| `1.x` | ✅ until 6 months after the next minor release |
| `0.x` | ❌ — please upgrade |

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Email `security@opencsg.com` with the subject line `ghe-security` and
include:

- A short description of the vulnerability and the impact.
- A reproduction recipe (commands, sample config, issue payload) with any
  secrets redacted.
- The affected version, commit SHA, and (if known) a suggested fix.

We will acknowledge within **3 business days** and aim to ship a fix or a
mitigation within **30 days** of confirmation. We follow coordinated
disclosure: please give us a reasonable window before publishing details.

## Threat model in scope

The tool runs in three contexts, each with its own threat model:

1. **Local CLI.** Runs as the user. Reads GitHub issues via the supplied
   `GITHUB_TOKEN` and sends the issue payloads to the configured LLM
   provider. The model is **not** trusted: the analyzer re-anchors
   titles and URLs to ground-truth GitHub data so the report cannot be
   tricked by prompt injection inside an issue body.
2. **GitHub Action.** Runs with the workflow-supplied `GITHUB_TOKEN`,
   which has `issues: read` and `contents: read` only. The Action
   **never** posts comments, applies labels, or modifies the target
   repository. All writes go to `$GITHUB_STEP_SUMMARY` and the artifact
   upload.
3. **Delegation (`--delegate-task`).** Plans a coding-agent invocation
   that **always** requires an explicit `--execute` to start. The plan
   is constructed with `shell=False` and a strict executable allowlist
   so a malicious task Markdown cannot reach a shell. Treat the
   delegated CLI itself as out of scope — that is the responsibility of
   its own maintainers.

## What this project does not do

- It does not sign releases; PyPI trusted publishing handles provenance.
- It does not sandbox the LLM provider; the user picks a provider they
  trust with the issue data.
- It does not ship SBOMs yet; that is a v1.1 item.

## Acknowledgements

We are grateful to the maintainers of the GitHub Copilot Coding Agent and
the `continuous-ai-resolver` projects, whose threat models informed the
design above.
