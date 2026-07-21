from __future__ import annotations

import json
import re
from typing import Any

from openai import APIError, APITimeoutError, OpenAI


class LLMClientError(RuntimeError):
    """Raised when the LLM call fails or returns invalid JSON."""


class LLMClient:
    """OpenAI-compatible chat client."""

    def __init__(self, base_url: str | None, api_key: str, model_name: str):
        kwargs: dict[str, str] = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)
        self.model_name = model_name
        # Most-recent token usage reported by the provider, used by callers
        # that want to surface cost information in the final report.
        self.last_usage: dict[str, int] = {}

    def generate(self, prompt: str, system: str | None = None) -> str:
        """Generate text from a prompt."""

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.2,
            )
        except (APIError, APITimeoutError) as exc:
            raise LLMClientError(f"LLM request failed: {exc}") from exc

        self._capture_usage(response)
        if not response.choices:
            raise LLMClientError("LLM returned no choices.")
        content = response.choices[0].message.content
        if not content:
            raise LLMClientError("LLM returned empty content.")
        return content

    def _capture_usage(self, response: Any) -> None:
        """Best-effort capture of OpenAI's usage object on this client.

        The OpenAI SDK exposes ``response.usage`` with prompt / completion /
        total token counts; some providers omit it. We swallow any Attribute
        error so legacy or stub responses never break generation.
        """

        usage = getattr(response, "usage", None)
        if usage is None:
            return
        for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
            value = getattr(usage, key, None)
            if isinstance(value, int):
                self.last_usage[key] = value

    def generate_json(self, prompt: str, system: str | None = None) -> dict[str, Any]:
        """Generate and parse a JSON object."""

        content = self.generate(prompt, system)
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.IGNORECASE)
        decoder = json.JSONDecoder()
        try:
            payload, _ = decoder.raw_decode(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{", cleaned)
            if not match:
                raise LLMClientError("LLM response did not contain JSON.")
            try:
                payload, _ = decoder.raw_decode(cleaned[match.start() :])
            except json.JSONDecodeError as exc:
                raise LLMClientError(f"Could not parse LLM JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise LLMClientError("LLM JSON response must be an object.")
        return payload
