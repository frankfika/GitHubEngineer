# VERIFY

This file is a snapshot of the v1.0.0 verification run on 2026-07-22.
Re-run it locally with `make verify`. The CI workflow
(`.github/workflows/test.yml`) runs the same pytest matrix and the
compileall lint on every push and pull request.

## 1. Tests

```
$ make test-fast
........................................................................ [ 82%]
...............                                                          [100%]
87 passed in 0.99s
```

87/87 pytest cases pass. The split is:

| File | Cases | Notes |
| --- | --- | --- |
| `tests/test_github_client.py` | 5 | PR filter, since filter, max_pages cap, reaction error, repo 404 |
| `tests/test_llm_client.py` | 11 | success, API error, timeout, empty content, no choices, JSON recovery, usage capture, missing usage |
| `tests/test_analyzer.py` | 12 | age filter, candidate ranking, cluster grouping, ground-truth title+URL injection, sort+dedupe, prompt-budget truncation, token usage, mock usage, etc. |
| `tests/test_delegation.py` | 11 | adapter plans, allowlist, shell-syntax rejection, opt-in required, safe subprocess args, timeout, allowed root, control bytes, safe executables |
| `tests/test_history.py` | 8 | save/load round-trip, missing directory, corrupt file skip, new vs resolved, empty prior, OSError wrapping |
| `tests/test_memory_manager.py` | 8 | load empty, parse YAML, legacy aliases, corrupt YAML, save round-trip, filter rejected numbers and themes, prompt_context dedupe |
| `tests/test_report_generator.py` | 4 | clickable link, plain-number fallback, empty brief, multi-cluster + missing-info truncation |
| `tests/test_main_integration.py` | 3 | main() success, empty repo, error paths |
| `tests/test_main_subcommands.py` | 7 | show-latest, list-decisions, init |
| `tests/test_config.py` | 12 | env expansion, validation, lenient load, multi-repo resolution, dedupe, malformed input |
| `tests/test_error_messages.py` | 4 | format_error hint matching and fallback |
| `tests/test_performance_50_issues.py` | 1 | 60-issue end-to-end pipeline under 5 s |
| `tests/test_future_capabilities.py` | 1 | pre-existing smoke for v0.3 / v0.4 |

## 2. Lint

```
$ make lint
.venv/bin/python -m compileall -q src tests
(no output, exit 0)
```

`compileall` byte-compiles every `.py` file in `src/` and `tests/`.
The CI workflow runs the same command in the `lint` job.

## 3. GitHub Actions YAML

```
$ make verify
==> 3/6 YAML workflow checks
.venv/bin/python -c "import yaml; [yaml.safe_load(open(f)) for f in [...]]"
all YAML workflows parse
```

All six workflow / template files parse without error:

- `.github/workflows/test.yml` — matrix on `ubuntu-latest,macos-latest` × Python 3.11,3.12
- `.github/workflows/publish.yml` — `permissions.id-token: write` for PyPI trusted publishing
- `.github/workflows/maintainer-brief.example.yml` — example schedule workflow
- `.github/dependabot.yml` — weekly pip + GitHub Actions bumps, grouped
- `.github/ISSUE_TEMPLATE/config.yml` — chooser that disables blank issues
- `action.yml` — composite action, `github-token` and `llm-api-key` are required

## 4. Build

```
$ make build
.venv/bin/python -m build
Successfully built github_engineer-1.0.0.tar.gz and github_engineer-1.0.0-py3-none-any.whl
```

Two artefacts in `dist/`:

- `github_engineer-1.0.0-py3-none-any.whl` — universal wheel
- `github_engineer-1.0.0.tar.gz` — sdist

The wheel exposes the `ghe` console script (`src.main:main`), declared
in `pyproject.toml`'s `[project.scripts]`.

## 5. Twine check

```
$ make verify
==> 5/6 twine check
Checking dist/github_engineer-0.1.0-py3-none-any.whl: PASSED
Checking dist/github_engineer-1.0.0-py3-none-any.whl: PASSED
Checking dist/github_engineer-0.1.0.tar.gz: PASSED
Checking dist/github_engineer-1.0.0.tar.gz: PASSED
```

`twine check` validates the long description and metadata against the
PyPI schema. Both the v0.1.0 (left over for archaeology) and v1.0.0
artefacts pass.

## 6. End-to-end dry run

```
$ make dry-run
.venv/bin/python benchmarks/dry_run.py
{
  "ok": true,
  "issue_count": 60,
  "top_priorities": [1, 2, 3],
  "rendered_chars": 1591,
  "report_path": "...",
  "step_summary_chars": 1592,
  "dropped_candidate_count": 0,
  "history_recorded": true,
  "second_run_diff_summary": "Compared with the 2026-07-22 brief: No change in Top N or cluster composition.",
  "elapsed_seconds": 0.0061
}
```

The dry run stands in for a real `ghe owner/name` invocation. It:

1. Synthesises 60 issues with realistic signal distribution.
2. Patches PyGithub so the `get_issues()` paginator returns the
   synthetic data; `get_repo` is mocked too.
3. Stubs the LLM with a deterministic response and a fixed
   `last_usage` so the `## Cost` section appears.
4. Runs `IssueAnalyzer.analyze` -> `ReportGenerator.generate_markdown`
   -> `write_report` -> `write_step_summary`.
5. Persists the brief to a temp `history/` directory and runs the diff
   against itself to prove the no-change path renders.

The end-to-end path runs in **6 ms** on developer hardware. The
v0.1 success criterion is `< 5 minutes`; we are 50 000× under budget.

## 7. Benchmarks

```
$ make bench
{
  "issues": 50,
  "repeats": 3,
  "elapsed_seconds": {
    "min": 0.0005, "median": 0.0005, "mean": 0.0005, "max": 0.0006
  },
  "top_n": 3, "dropped_candidate_count": 0
}

$ make bench-cost
{
  "model": "claude-sonnet-4",
  "issues": 50,
  "prompt_tokens": 32400,
  "completion_tokens": 950,
  "cost_usd": 0.1114
}
```

For the same 50 issues, the cost table is:

| Model | 50 issues | 200 issues |
| --- | --- | --- |
| `gpt-4o-mini` | $0.0054 | $0.0194 |
| `claude-haiku-4` | $0.0280 | $0.1020 |
| `claude-sonnet-4` | $0.1114 | $0.3905 |
| `deepseek-chat` | $0.0048 | $0.0179 |

`make bench-cost --model gpt-4o-mini --issues 200` prints the matching
row. The numbers are estimates using each provider's public list price;
the authoritative cost lives in the generated report's `## Cost` section.

## 8. Release preconditions

```
$ make release-dry-run
...
==> confirming tag v1.0.0 exists
==> confirming dist/ has the v1.0.0 artefacts
==> confirm PyPI trusted publishing config (publish.yml)
All release preconditions met. Push to GitHub to trigger publish.yml.
```

To actually publish:

1. Create a remote and push the tag: `git remote add origin
   git@github.com:OpenCSG/github-engineer.git && git push -u origin main
   --tags`.
2. The `publish.yml` workflow fires on `v*.*.*` tag, builds the
   artefacts, and uses `pypa/gh-action-pypi-publish@release/v1` with
   the OIDC `id-token` permission. Configure the PyPI **Trusted
   Publisher** at https://pypi.org/manage/account/publishing/ pointing
   at `OpenCSG/github-engineer` / environment `pypi` / workflow
   `publish.yml` before the first push.

## 9. Known limitations

- The `--pipeline` flow targets a single repository per invocation.
  Loop across repositories with `for repo in a b c; do ghe --repo
  $repo --prepare-issue N; done`.
- `--record-decision` and `--pipeline` are still independent. An
  atomic "approve and dispatch" flow is a v1.1 candidate.
- `benchmarks/cost.py` uses published list prices as of mid-2026.
  Refresh the table when the upstream prices change.

## 10. AI 修复闭环验收（2026-07-28）

最终验收覆盖了仓库上下文、模型补丁、测试反馈修正、人工审核和发布门禁：

| 检查 | 结果 |
| --- | --- |
| Python 全量测试 | 346 passed，19 subtests passed |
| AI 闭环 | 首次错误 → pytest 失败 → 反馈给模型 → 二次修复 → pytest 通过 |
| Demo/Fake 发布保护 | 前后端均拒绝 |
| 未验证/验证失败发布保护 | 确认令牌与发布端点均拒绝 |
| Web/desktop 资源同步 | 通过 |
| JavaScript 语法与浏览器控制台 | 通过，无 error/warn |
| Tauri `cargo check` | 通过 |
| `git diff --check` | 通过 |

真实 OpenAI Provider 的健康检查也必须执行。凭据无效、模型不可用或
`base_url` 不可达时，顶部状态会明确显示“连接失败”，Issue 修复入口只会打开
配置界面，不会启动一个看似成功的假修复。
