"""Unit tests for src/llm_client.py.

Mock the OpenAI SDK so we can exercise success, API error, timeout, empty
content, and JSON recovery paths without a real LLM.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from openai import APIError, APITimeoutError

from src.llm_client import CodexLLMClient, LLMClient, LLMClientError, create_llm_client


def _build_response(content: str):
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = content
    return response


def _make_client(response_content: str | None):
    client = LLMClient(base_url=None, api_key="test", model_name="gpt-x")
    if response_content is not None:
        client.client.chat.completions.create = MagicMock(
            return_value=_build_response(response_content)
        )
    else:
        client.client.chat.completions.create = MagicMock(
            side_effect=APIError("upstream blew up", request=MagicMock(), body=None)
        )
    return client


def test_generate_returns_text_on_success():
    client = _make_client("hello world")
    assert client.generate("ping") == "hello world"


def test_generate_wraps_api_error_with_typed_exception():
    client = _make_client(None)
    with pytest.raises(LLMClientError) as exc:
        client.generate("ping")
    assert "upstream blew up" in str(exc.value)


def test_generate_wraps_timeout():
    client = LLMClient(base_url=None, api_key="test", model_name="gpt-x")
    client.client.chat.completions.create = MagicMock(
        side_effect=APITimeoutError(request=MagicMock())
    )
    with pytest.raises(LLMClientError) as exc:
        client.generate("ping")
    assert "LLM request failed" in str(exc.value)


def test_generate_rejects_empty_content():
    client = _make_client("")
    with pytest.raises(LLMClientError):
        client.generate("ping")


def test_generate_rejects_no_choices():
    client = LLMClient(base_url=None, api_key="test", model_name="gpt-x")
    response = MagicMock()
    response.choices = []
    client.client.chat.completions.create = MagicMock(return_value=response)
    with pytest.raises(LLMClientError) as exc:
        client.generate("ping")
    assert "no choices" in str(exc.value)


def test_generate_json_strips_markdown_fences():
    client = _make_client("```json\n{\"a\": 1}\n```")
    payload = client.generate_json("ping")
    assert payload == {"a": 1}


def test_generate_records_token_usage_from_response():
    response = _build_response("ok")
    response.usage.prompt_tokens = 12
    response.usage.completion_tokens = 7
    response.usage.total_tokens = 19
    client = LLMClient(base_url=None, api_key="test", model_name="gpt-x")
    client.client.chat.completions.create = MagicMock(return_value=response)
    assert client.generate("ping") == "ok"
    assert client.last_usage == {"prompt_tokens": 12, "completion_tokens": 7, "total_tokens": 19}


def test_generate_leaves_usage_empty_when_provider_omits_it():
    response = _build_response("ok")
    # No ``usage`` attribute on the response at all.
    del response.usage
    client = LLMClient(base_url=None, api_key="test", model_name="gpt-x")
    client.client.chat.completions.create = MagicMock(return_value=response)
    assert client.generate("ping") == "ok"
    assert client.last_usage == {}


def test_generate_json_recovery_finds_object_in_prose():
    client = _make_client('Sure! Here you go: {"answer": 42, "ok": true}')
    payload = client.generate_json("ping")
    assert payload == {"answer": 42, "ok": True}


def test_generate_json_raises_when_no_object_present():
    client = _make_client("just plain text, no json here at all")
    with pytest.raises(LLMClientError) as exc:
        client.generate_json("ping")
    assert "JSON" in str(exc.value)


def test_generate_json_rejects_top_level_non_object():
    client = _make_client("[1, 2, 3]")
    with pytest.raises(LLMClientError) as exc:
        client.generate_json("ping")
    assert "must be an object" in str(exc.value)


@patch("src.coding_agent.CodexCLIProvider")
def test_codex_client_captures_final_message(mock_provider, tmp_path, monkeypatch):
    executable = tmp_path / "codex"
    executable.write_text("", encoding="utf-8")
    mock_provider.return_value.executable = str(executable)

    def fake_run(command, **kwargs):
        output_path = command[command.index("--output-last-message") + 1]
        Path(output_path).write_text('{"ok": true}', encoding="utf-8")
        result = MagicMock(returncode=0, stdout="events", stderr="")
        return result

    monkeypatch.setattr("src.llm_client.subprocess.run", fake_run)
    client = CodexLLMClient()
    assert client.generate_json("Return JSON") == {"ok": True}


@patch("src.llm_client.CodexLLMClient")
def test_factory_builds_codex_without_api_key(mock_codex):
    result = create_llm_client({"provider": "codex_cli"})
    assert result is mock_codex.return_value
    mock_codex.assert_called_once_with(model_name=None)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
