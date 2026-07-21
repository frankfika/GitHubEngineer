---
name: Bug report
about: Something is broken in GitHub Engineer
title: "[bug] "
labels: bug
assignees: ""
---

## Summary

One-sentence description of what is broken.

## Environment

- OS: (e.g. macOS 14.4, Ubuntu 22.04)
- Python: (run `python --version`)
- GitHub Engineer version: (run `ghe --version` or `pip show github-engineer`)
- Installation: `pip install -e .[dev]` / `make install-dev` / Docker / other

## Steps to reproduce

```bash
# Exact commands, copy-pasteable.
```

## Expected behavior

What you expected to see.

## Actual behavior

What actually happened. Include the **full** error message and, if possible,
the relevant section of the Markdown report.

## Affected configuration

Attach (or paste) the contents of `.ghe/config.yml` with secrets redacted.
Mention any environment variables you set.

## Logs

If the bug surfaces in CI, paste the failing workflow run link plus the
relevant log slice. For local runs, prepend `GHE_LOG_LEVEL=DEBUG` to your
invocation and attach the output.
