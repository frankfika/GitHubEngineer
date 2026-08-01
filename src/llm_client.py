from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
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
        # Strip *every* fenced code block, not just the outer one. A
        # response like ``\`\`\`json\n{...}\n\`\`\`\nsome prose\n\`\`\`json\n{...}\n\`\`\```
        # should leave the first JSON object intact while the second
        # one disappears — the previous single-pass regex kept the
        # first fence and removed only the trailing one, then a nested
        # ``match.start()`` could land inside the second block.
        cleaned = re.sub(
            r"```(?:json)?\s*|\s*```", "", content, flags=re.IGNORECASE
        ).strip()
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


class CodexLLMClient:
    """Use the authenticated local Codex CLI as a text/JSON model."""

    def __init__(
        self,
        model_name: str | None = None,
        *,
        executable: str | None = None,
        timeout: float = 300.0,
    ):
        from .coding_agent import CodexCLIProvider

        provider = CodexCLIProvider(executable=executable, timeout=timeout)
        self.executable = provider.executable
        self.model_name = model_name or "codex-default"
        self.timeout = float(timeout)
        self.last_usage: dict[str, int] = {}

    def generate(self, prompt: str, system: str | None = None) -> str:
        from .process_runtime import safe_subprocess_env

        full_prompt = prompt
        if system:
            full_prompt = f"System instructions:\n{system}\n\nUser request:\n{prompt}"

        output_path = ""
        try:
            with tempfile.NamedTemporaryFile(
                prefix="ghe-codex-response-", suffix=".txt", delete=False
            ) as output:
                output_path = output.name
            command = [
                self.executable,
                "exec",
                "--sandbox",
                "read-only",
                "--ephemeral",
                "--skip-git-repo-check",
                "--color",
                "never",
                "--output-last-message",
                output_path,
            ]
            if self.model_name and self.model_name != "codex-default":
                command.extend(["--model", self.model_name])
            # Keep repository and Issue content out of the process list. The
            # standard proxy variables retained by safe_subprocess_env are
            # required for the CLI to complete this stdin-based request.
            command.append("-")
            result = subprocess.run(
                command,
                cwd=str(Path.cwd()),
                env=safe_subprocess_env("delegate"),
                input=full_prompt,
                text=True,
                capture_output=True,
                timeout=self.timeout,
                shell=False,
            )
            if result.returncode != 0:
                detail = (result.stderr or result.stdout or "").strip()
                raise LLMClientError(
                    f"Codex LLM request failed: {detail[:1500] or 'non-zero exit code'}"
                )
            content = Path(output_path).read_text(encoding="utf-8").strip()
            if not content:
                raise LLMClientError("Codex LLM returned empty content.")
            return content
        except subprocess.TimeoutExpired as exc:
            raise LLMClientError(
                f"Codex LLM request timed out after {self.timeout:g}s."
            ) from exc
        except OSError as exc:
            raise LLMClientError(f"Codex LLM request failed: {exc}") from exc
        finally:
            if output_path:
                try:
                    os.unlink(output_path)
                except FileNotFoundError:
                    pass

    def generate_json(self, prompt: str, system: str | None = None) -> dict[str, Any]:
        return LLMClient.generate_json(self, prompt, system)


def create_llm_client(model_config: dict[str, Any]) -> LLMClient | CodexLLMClient:
    """Build the configured brief-generation model client."""

    provider = str(model_config.get("provider") or "openai-compatible").lower()
    provider = provider.replace("-", "_")
    if provider in {"codex", "codex_cli"}:
        return CodexLLMClient(model_name=model_config.get("model_name"))
    if provider not in {"openai", "openai_compatible"}:
        raise LLMClientError(
            f"Unsupported model provider {provider!r}. Use 'codex_cli' or 'openai-compatible'."
        )
    return LLMClient(
        model_config.get("base_url") or None,
        str(model_config.get("api_key") or ""),
        str(model_config.get("model_name") or ""),
    )
