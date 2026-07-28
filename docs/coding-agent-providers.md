# Coding Agent Providers 详细指南

> Companion to `README.md` §F. This doc is the deep-dive — when the README
> is "here's the three providers in 30 seconds", this doc is "here's how
> each one behaves under load, how to debug a stuck diff, and what the
> limits are".
>
> Audience: maintainers who already have `README.md` §F open in another
> tab and want the long form.

---

## Table of contents

- [`openai_compatible` (default, recommended)](#openai_compatible-default-recommended)
  - [What it covers](#what-it-covers)
  - [Configuration shape](#configuration-shape)
  - [Request / response shape](#request--response-shape)
  - [Limitations](#limitations)
  - [Per-provider notes](#per-provider-notes)
- [`anthropic`](#anthropic)
- [`claude_cli` (fallback)](#claude_cli-fallback)
- [Performance comparison](#performance-comparison)
- [Troubleshooting](#troubleshooting)
- [Internal: how `get_provider()` picks one](#internal-how-get_provider-picks-one)
- [Internal: the `error_kind` taxonomy](#internal-the-error_kind-taxonomy)

---

## `openai_compatible` (default, recommended)

### What it covers

Any HTTP server that implements `POST {base_url}/chat/completions` with a
Bearer-key auth header and the OpenAI response shape:

```json
{
  "choices": [
    { "message": { "role": "assistant", "content": "..." } }
  ]
}
```

That covers:

| Backend | How to run it | Why you'd use it |
| --- | --- | --- |
| **OpenAI** | SaaS | First-party, best rate limits, $5 free credit to start |
| **DeepSeek** | SaaS | Very cheap, code-tuned models |
| **OpenRouter** | SaaS | One key, any model — useful for A/B testing |
| **Ollama** | Local | Zero-cost, full data sovereignty, works offline |
| **vLLM** | Local | High-throughput local serving, OpenAI-compatible out of the box |
| **LM Studio** | Local desktop app | GUI for downloading + serving GGUF models |
| **llama.cpp server** | Local | `llama-server -m model.gguf --port 8080` |
| **Custom proxy** | Your infra | E.g. a private gateway in front of a real OpenAI tenant |

If your server speaks the OpenAI schema but lives at a non-standard path,
set `base_url` to the prefix and the provider will append `/chat/completions`
automatically.

### Configuration shape

```yaml
coding_agent:
  provider: openai_compatible
  base_url: https://api.openai.com/v1
  api_key: ${LLM_API_KEY}            # or literal "sk-..."
  model: gpt-4o
  # timeout: 180                    # seconds; optional, default 180
```

- `base_url` is required. Trailing `/` is stripped.
- `api_key` is read directly. If empty, the provider substitutes
  `not-required` so self-hosted servers (Ollama, vLLM) don't 401.
- `${LLM_API_KEY}` is expanded from the environment at config-load time
  (see `_resolve_api_key()` in `src/coding_agent.py`). An unexpanded
  placeholder with no matching env var resolves to `""` — never to the
  literal `${LLM_API_KEY}` text.
- `model` is required. Free-form string — no validation, the provider
  forwards it as-is. A typo becomes a `model_not_found` HTTP 404 at
  first run, not a config error.
- `timeout` is optional. Default 180s. The health check is capped at 30s
  regardless.

### Request / response shape

The provider POSTs:

```json
{
  "model": "gpt-4o",
  "messages": [{"role": "user", "content": "<prompt>\n\n<diff suffix>"}],
  "stream": false,
  "temperature": 0.0
}
```

The `<diff suffix>` is a fixed string appended to every prompt that asks
the model to emit a unified diff in a single ```diff``` fenced code block.
The regex that extracts the block is:

```python
re.compile(r"```(?:diff|patch)?\n(.*?)```", re.DOTALL)
```

The first fenced block wins. If the model emits multiple blocks, the
worker uses the first one and warns (TODO: surface a UI warning).

After the response arrives, the worker writes the diff to
`<workspace>/.ghe-agent.patch` and runs `git apply --check` followed by
`git apply`. If either fails, the result carries `error_kind="no_diff"`
with the git stderr in `error_hint`.

### Current contract and limitations

The API providers deliberately keep a portable text-diff contract:

- **Tool use / function calling.** The request body has no `tools` field.
  Instead, the provider attaches a bounded repository tree and selected
  secret-filtered file contents. The exact included file list and truncation
  metadata are persisted on the repair job for audit.
- **Streaming.** `stream: false` is hard-coded. The UI shows a
  *running...* spinner during the call. For 7B local models on slow
  hardware, expect 30-90s for a single repair attempt.
- **Bounded correction loop.** A patch that fails `git apply` gets one
  correction request. A repair that fails automatic verification gets one
  incremental correction request containing truncated, explicitly untrusted
  test output. This is intentionally bounded rather than an open-ended loop.
- **Token accounting.** `usage.prompt_tokens` / `usage.completion_tokens`
  in the response are ignored. The UI does not show cost per call.

Verification uses detected, fixed commands rather than commands proposed by
the repository or model. It defaults to a preinstalled network-disabled Docker
image; without one the result remains `unverified` and publish is blocked.
For trusted repositories only, set `repair.allow_host_verification: true`.

### Per-provider notes

#### OpenAI

- Models: `gpt-4o` (best quality), `gpt-4o-mini` (cheaper, weaker), `o1-mini` / `o3-mini` (reasoning, slow).
- Watch the rate limit on the `free` tier — `coding_agent.health_check()` returns false during 429s, which trips the `invalid` indicator state in the UI.

#### DeepSeek

- `deepseek-coder` is fine for typo fixes; `deepseek-chat` is better for refactors.
- `base_url: https://api.deepseek.com/v1` — no trailing path.

#### OpenRouter

- Model names are prefixed by provider: `anthropic/claude-sonnet-4-5`, `openai/gpt-4o`, `meta-llama/llama-3.3-70b-instruct:free`.
- The `:free` suffix picks the free-tier route; useful for budget-constrained tests.

#### Ollama

- `api_key: ollama` (or any non-empty string — Ollama ignores it).
- For 32B+ models, give the server 24+ GB of RAM. `qwen2.5-coder:7b` works on 16 GB laptops for small diffs.
- If `ollama serve` is bound to a different host, pass the full URL: `base_url: http://192.168.1.5:11434/v1`.

#### vLLM

- `vllm serve <model> --port 8000` then `base_url: http://localhost:8000/v1`.
- vLLM enforces its own request timeout. If the worker reports `api_timeout`, raise it: `vllm serve ... --max-model-len 8192 --request-timeout 600`.

#### LM Studio

- Enable the *Local Server* toggle in the Developer tab. Default port 1234.
- LM Studio injects a fake `api_key: lm-studio` into the UI — the worker doesn't care, any value works.

---

## `anthropic`

The first-party Anthropic Messages API at `https://api.anthropic.com/v1/messages`.
Use this when you have a Claude.ai API key and want first-party rate limits
+ prompt caching.

### Configuration shape

```yaml
coding_agent:
  provider: anthropic
  api_key: ${ANTHROPIC_API_KEY}
  model: claude-sonnet-4-5
  # base_url: https://api.anthropic.com/v1/messages   # optional
```

- `api_key` is required. Empty key → `CodingAgentConfigError` at config-load.
- `model` is required. Default if omitted: `claude-sonnet-4-5`.
- `base_url` is almost never needed — only set it when running against
  a test mock or a private Anthropic-compatible proxy.

### Request / response shape

The provider POSTs:

```json
{
  "model": "claude-sonnet-4-5",
  "max_tokens": 8192,
  "messages": [{"role": "user", "content": "<prompt>\n\n<diff suffix>"}]
}
```

Headers: `x-api-key: <key>`, `anthropic-version: 2023-06-01`.

The response text is extracted from `content[].text` blocks. Non-text
blocks (tool_use, etc.) are ignored — the MVP contract is "model returns
text that contains a diff", not "model uses tools".

### When to use it vs `openai_compatible`

| Situation | Pick |
| --- | --- |
| You already pay for Claude.ai | `anthropic` (best price/quality) |
| You want to use GPT-4o or local models | `openai_compatible` |
| You're running in a region where Anthropic API is blocked | `openai_compatible` + a different provider |
| You want prompt caching (1M+ context) | `anthropic` (only first-party has it) |
| You need unrestricted interactive tool use | Use `claude_cli`; API providers use bounded repository context |

---

## `claude_cli` (fallback)

Shells out to the local Claude Code CLI binary resolved by
`src.process_runtime.find_desktop_executable`. On macOS that knows about
`/opt/homebrew/bin` and `~/.claude/local`. On Linux it falls back to
`which claude`.

### Configuration shape

```yaml
coding_agent:
  provider: claude_cli
  # No base_url / api_key / model.
```

That's it. If the binary is on `$PATH` and you ran `claude login` at
least once, the provider will spawn it.

### When to use it

- **You're already a Claude Code CLI user** and don't want to maintain a
  second config.
- **You need unrestricted interactive tool use** — `claude --bare`
  provides it at the cost of being tied to one model and a broader execution surface.
- **You're prototyping** and don't want to commit to an API key.

### When NOT to use it

- **CI / headless box.** Claude Code CLI requires a TTY-ish environment
  for `claude login`. A fresh server without `/root/.claude` will fail
  with `claude_not_authenticated`.
- **You want to compare models.** `claude_cli` is locked to whatever
  Anthropic ships; the API providers let you A/B.
- **You want cost visibility.** `ClaudeCLIProvider` can't see token
  counts.

The long-term migration target is `openai_compatible` — see `README.md`
§F.7 for the diff.

---

## Performance comparison

Numbers from the dev box (M-series Mac, local Ollama on 32B) and the
public OpenAI API on a 100-call sample (May 2026). Use as a rough guide,
not a benchmark.

| Provider | Cold-start | p50 latency | p95 latency | Cost / 1K repairs |
| --- | --- | --- | --- | --- |
| `openai_compatible` (OpenAI gpt-4o) | 0.5s | 4s | 12s | ~$2 |
| `openai_compatible` (OpenAI gpt-4o-mini) | 0.5s | 2s | 6s | ~$0.20 |
| `openai_compatible` (DeepSeek chat) | 0.5s | 3s | 10s | ~$0.10 |
| `openai_compatible` (Ollama qwen2.5-coder:32b) | 3s (model load) | 28s | 75s | $0 (electricity) |
| `openai_compatible` (Ollama qwen2.5-coder:7b) | 1s | 9s | 25s | $0 (electricity) |
| `openai_compatible` (vLLM Qwen2.5-Coder-32B) | 5s (warmup) | 11s | 30s | $0 |
| `anthropic` (claude-sonnet-4-5) | 0.5s | 5s | 18s | ~$3 |
| `claude_cli` (claude-sonnet-4-5) | 2s (binary spawn) | 35s | 90s | ~$3 (same model, slower loop) |

*Latencies* include `git apply --check` + `git apply` + JSON parse, not
just the model call. *Cost* assumes an average 2K input + 800 output
tokens per repair attempt, with a 1.6× retry multiplier on transient
errors.

---

## Troubleshooting

### "indicator stays `unconfigured` even after I edit `.ghe/config.yml`"

The worker reads the config once at process start. Restart the web server
(`Ctrl-C` and re-run `ghe --serve`) to pick up changes. The UI also has a
*refresh* button in the topbar that re-fetches `/api/repair-capabilities`
without a full restart — use that first.

### "indicator flips to `invalid` after my first repair attempt"

Run `ghe --repair-capabilities` to see the full reason. The most common
causes:

1. **API key typo** — `error_kind: api_key_invalid`, `action: "API key 无效，更新 .ghe/config.yml 的 api_key"`. Copy the key from the provider dashboard, paste into `api_key:` literally (or set `LLM_API_KEY` and reference it).
2. **Wrong model name** — `error_kind: model_not_found`, `action: "model 名错，看 provider 文档"`. Cross-check the model name against the provider's model list. OpenRouter model names need the `provider/` prefix.
3. **Firewall / base_url** — `error_kind: api_connection_failed`, `action: "API 不可达，检查 base_url + 网络"`. For local servers, check `ollama serve` / `vllm` is actually listening on the configured port. For SaaS, check VPN / corporate proxy.

### "repair attempt returns `no_diff` even though the model ran"

The model produced text, but it didn't contain a ```diff``` fenced block
that `git apply` could apply. Causes:

1. **The model returned a description, not a diff.** Some models (especially
   smaller local ones) will explain what they'd change in prose instead
   of emitting a unified diff. Try a larger / more code-tuned model, or
   add a system prompt that strongly emphasizes "ONLY the diff, nothing
   else".
2. **The diff is wrong / context lines don't match.** `git apply --check`
   rejects hunks whose context doesn't match the file. Re-run the repair
   — `repair_worker` will re-issue the prompt with a fresh prompt that
   includes the current file contents. If it keeps failing, the model
   is probably hallucinating.
3. **The diff is for a file outside the workspace.** `git apply` runs
   inside `<workspace>`, so paths must be relative to the repo root.

### "health check is flaky (passes then fails)"

`health_check()` is a 1-token POST. If the provider is on a cold-start
tier (HuggingFace Spaces, Render free tier), the first call after idle
takes 5-15s — the health check timeout is 30s but the repair timeout is
180s. If the health check times out, the UI shows `invalid` briefly
until the next refresh. Click the indicator to re-check manually.

### "model uses `o1` / reasoning and times out"

`o1-mini` / `o3-mini` are reasoning models — they may take 60-120s for
a single response. Raise `coding_agent.timeout` in `.ghe/config.yml`:

```yaml
coding_agent:
  provider: openai_compatible
  base_url: https://api.openai.com/v1
  api_key: ${LLM_API_KEY}
  model: o3-mini
  timeout: 300
```

The default 180s is calibrated for `gpt-4o` / `claude-sonnet-4-5`.

### "I see the same prompt sent twice"

That's the worker's transient-error retry: it re-issues the prompt on
`rate_limited`, `api_timeout`, and `api_connection_failed` (3 attempts
max with exponential backoff). It's not a bug. Check the worker logs
(`output/repair-worker.log` or whatever `output_dir` points at) — a
*Successful after 2 retries* line means the model eventually cooperated.

---

## Internal: how `get_provider()` picks one

`src/coding_agent.py::get_provider(config)` reads `config["coding_agent"]["provider"]`
and dispatches:

```python
provider_name = str(section.get("provider") or "openai_compatible").strip().lower()
```

Alias table:

| `provider` value | Resolves to |
| --- | --- |
| `"openai_compatible"` | `OpenAICompatibleProvider` |
| `"openai-compatible"` (kebab) | `OpenAICompatibleProvider` |
| `"openai"` | `OpenAICompatibleProvider` |
| `""` / missing | `OpenAICompatibleProvider` (default) |
| `"anthropic"` | `AnthropicProvider` |
| `"claude_cli"` | `ClaudeCLIProvider` |
| `"claude-cli"` (kebab) | `ClaudeCLIProvider` |
| `"claude-code"` | `ClaudeCLIProvider` |
| `"claude"` | `ClaudeCLIProvider` |
| anything else | `CodingAgentConfigError("Unknown coding_agent.provider: ...") |

The kebab variants are accepted for ergonomics — the YAML reader normalises
hyphens to underscores in some cases, and we'd rather not 500 the user.

---

## Internal: the `error_kind` taxonomy

12 values, defined as a `frozenset` in `src/coding_agent.py`:

```python
ERROR_KINDS: frozenset[str] = frozenset({
    # New in §F (HTTP provider errors):
    "api_key_invalid",        # 401/403 with invalid-key body
    "api_connection_failed",  # connection refused / DNS / 5xx
    "model_not_found",        # 404 + body mentions "model" + "not found"
    "rate_limited",           # 429
    "context_too_long",       # 400/413, body says "context length"
    "api_timeout",            # 408/504, or client timeout
    "tool_call_failed",       # response structure broken
    # Legacy (Claude CLI + worker pre-§F):
    "no_diff",                # git apply rejected the model's output
    "permission_denied",      # POSIX EACCES on workspace
    "timeout",                # subprocess timeout
    "claude_not_authenticated",  # Claude CLI says "not logged in"
    "unknown",                # nothing matched
})
```

The HTTP provider errors are produced by `_classify_http_error(status, body, message)`,
which consults `_HTTP_STATUS_TABLE` (status → kind) first, then
`_BODY_PATTERNS` (body-only fallback) for statuses the table doesn't
cover (e.g. 422 from a custom proxy). The legacy kinds come from
`src/diagnose.py::diagnose_repair_error()` and are matched against
subprocess stderr / exit codes.

See `README.md` §F.6 for the colored-badge + action/hint rendering, and
`src/coding_agent.py` lines 240-360 for the full mapping.
