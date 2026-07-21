"""Estimate the cost of a brief at a given size with a given model.

The numbers are based on public list prices for the major OpenAI-compatible
providers as of mid-2026. They are best-effort estimates, not quotes; the
generated report includes the real token counts in its ``## Cost`` section,
so the authoritative number always lives in the report itself.

Run via ``make bench-cost`` or directly:

    python benchmarks/cost.py --model claude-sonnet-4 --issues 50
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass


# Per-million-token USD list prices, source: each provider's public pricing
# page. Update here when the numbers change.
PRICES_PER_MILLION_TOKENS: dict[str, dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "claude-haiku-4": {"input": 0.80, "output": 4.00},
    "claude-sonnet-4": {"input": 3.00, "output": 15.00},
    "deepseek-chat": {"input": 0.14, "output": 0.28},
}


@dataclass(frozen=True)
class Estimate:
    model: str
    issues: int
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float

    def as_dict(self) -> dict:
        return {
            "model": self.model,
            "issues": self.issues,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost_usd": round(self.cost_usd, 4),
        }


def estimate(model: str, issues: int) -> Estimate:
    """Estimate the cost of a brief with ``issues`` candidates."""

    if model not in PRICES_PER_MILLION_TOKENS:
        raise SystemExit(
            f"Unknown model {model!r}. Known: {', '.join(sorted(PRICES_PER_MILLION_TOKENS))}"
        )
    # ~620 input tokens per issue at 1500 char body + metadata + padding.
    prompt_tokens = 1_400 + issues * 620
    # The completion is dominated by the Top-N JSON; it scales slowly.
    completion_tokens = 200 + min(issues, 50) * 15
    prices = PRICES_PER_MILLION_TOKENS[model]
    cost = (prompt_tokens * prices["input"] + completion_tokens * prices["output"]) / 1_000_000
    return Estimate(model, issues, prompt_tokens, completion_tokens, cost)


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate brief cost by model and size.")
    parser.add_argument(
        "--model",
        default="claude-sonnet-4",
        choices=sorted(PRICES_PER_MILLION_TOKENS),
        help="OpenAI-compatible model name to estimate against.",
    )
    parser.add_argument("--issues", type=int, default=50, help="Candidate issue count.")
    args = parser.parse_args()
    result = estimate(args.model, args.issues).as_dict()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
