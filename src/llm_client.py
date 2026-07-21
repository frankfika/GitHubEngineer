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

        if not response.choices:
            raise LLMClientError("LLM returned no choices.")
        content = response.choices[0].message.content
        if not content:
            raise LLMClientError("LLM returned empty content.")
        return content

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
