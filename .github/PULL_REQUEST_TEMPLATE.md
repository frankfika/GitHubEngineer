## What

One-sentence description of the change.

## Why

Link the issue this PR fixes (or describe the gap). Keep the rationale to
two or three sentences — if it needs more, the proposal belongs in a
discussion first.

## How

Walk through the change in the order a reviewer will read it:

- Which files moved and why.
- Any new public API and how it interacts with existing functions.
- New tests, named with the behaviour they cover (e.g.
  `test_filter_issues_drops_rejected_themes`).

## Verification

Tick all that apply:

- [ ] `make test` — 85/85 pass locally.
- [ ] `make smoke` — CLI entry points and example config still parse.
- [ ] Manual run against a public repository, brief generated without
      exceptions.
- [ ] For delegation changes, dry-run only — `--execute` is for a follow-up
      PR that the maintainer approves explicitly.

## Risk

- [ ] **No public write**: this PR does not introduce or change any code
      that posts comments, applies labels, or creates issues on the target
      repository.
- [ ] **Backwards compatible**: no CLI flag, config key, or persisted
      file format changed in a breaking way. If it did, call it out below
      and bump the version in `pyproject.toml`.

## Out of scope

What was tempting to include but is intentionally left for a follow-up.
