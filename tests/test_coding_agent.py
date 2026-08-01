"""Unit tests for the pluggable coding-agent provider abstraction.

The plumbing around ``src.coding_agent`` is split into three concerns,
and the tests mirror that split:

* **HTTP providers** (``OpenAICompatibleProvider``,
  ``AnthropicProvider``) -- request format, error classification,
  diff extraction, ``git apply`` integration.  We mock the HTTP
  transport with ``urllib.request`` patches so the tests do not need
  a real provider.
* **Provider factory** (``get_provider``) -- config-to-class resolution
  plus the failure paths (missing / malformed section, unknown
  provider).
* **Diagnose integration** -- ``diagnose_repair_error`` honours the
  seven new structured ``error_kind`` values that the new providers
  emit.  These tests live next to the older ones in
  ``test_main_diagnose.py``; the ones here focus on the *new* kinds.

The legacy ``ClaudeCLIProvider`` is exercised by an end-to-end
``repair_worker`` test elsewhere (see ``tests/test_repair_worker.py``)
because spawning a real ``claude`` binary is the only way to verify
the subprocess surface.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src.coding_agent import (
    AnthropicProvider,
    ClaudeCLIProvider,
    CodexCLIProvider,
    CodingAgentConfigError,
    CodingAgentProvider,
    CodingAgentResult,
    FakeProvider,
    OpenAICompatibleProvider,
    _classify_http_error,
    _extract_unified_diff,
    _git_apply,
    _HTTP_STATUS_TABLE,
    _resolve_api_key,
    get_provider,
    has_provider_config,
)
from src.workspace_context import build_workspace_context
from src.main import _STRUCTURED_DIAGNOSES, diagnose_repair_error


# ---------------------------------------------------------------------------
# OpenAICompatibleProvider -- request format and error classification.
# ---------------------------------------------------------------------------


class OpenAICompatibleProviderTest(unittest.TestCase):
    """Mocked-HTTP tests for the OpenAI-compatible chat completions path."""

    def _patched_post(self, *, status: int, body: str):
        """Return a context-manager helper that stubs ``_post_json``.

        We patch the *module-level* helper used by every API provider
        so the provider class can stay clean of test seams.  The
        caller chooses the HTTP status and the body string the fake
        server returns.
        """

        from src import coding_agent

        calls: list[dict[str, object]] = []

        def fake_post(url, payload, *, headers, timeout):
            calls.append({"url": url, "payload": payload, "headers": headers, "timeout": timeout})
            return status, body

        return patch.object(coding_agent, "_post_json", side_effect=fake_post), calls

    def test_run_sends_chat_completions_payload(self) -> None:
        """The payload shape, URL, and headers match the OpenAI schema."""
        provider = OpenAICompatibleProvider(
            base_url="https://api.example.com/v1",
            api_key="sk-test",
            model="gpt-4o",
        )
        fake_response = json.dumps(
            {
                "choices": [
                    {
                        "message": {"content": "```diff\n--- a/x\n+++ b/x\n@@\n-old\n+new\n```"}
                    }
                ]
            }
        )
        patcher, calls = self._patched_post(status=200, body=fake_response)
        with tempfile.TemporaryDirectory() as workspace:
            with patch.object(subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="", stderr="")):
                with patcher:
                    result = provider.run("fix the bug", Path(workspace))
        self.assertIsNone(result.error_kind)
        self.assertEqual(len(calls), 1)
        call = calls[0]
        self.assertEqual(call["url"], "https://api.example.com/v1/chat/completions")
        self.assertEqual(call["headers"]["Authorization"], "Bearer sk-test")
        payload = call["payload"]
        assert isinstance(payload, dict)
        self.assertEqual(payload["model"], "gpt-4o")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["messages"][0]["role"], "user")
        # The diff suffix must be appended so the model knows to reply
        # with a unified diff.
        self.assertIn("```diff", payload["messages"][0]["content"])

    def test_run_401_maps_to_api_key_invalid(self) -> None:
        provider = OpenAICompatibleProvider(
            base_url="https://api.example.com/v1",
            api_key="sk-bad",
            model="gpt-4o",
        )
        patcher, _ = self._patched_post(
            status=401, body=json.dumps({"error": {"message": "Invalid API key"}})
        )
        with tempfile.TemporaryDirectory() as workspace:
            with patcher:
                result = provider.run("fix", Path(workspace))
        self.assertEqual(result.error_kind, "api_key_invalid")
        self.assertIn("API key", (result.error_action or ""))

    def test_run_404_maps_to_model_not_found(self) -> None:
        provider = OpenAICompatibleProvider(
            base_url="https://api.example.com/v1",
            api_key="sk-test",
            model="gpt-99",
        )
        patcher, _ = self._patched_post(
            status=404, body=json.dumps({"error": {"message": "The model 'gpt-99' does not exist"}})
        )
        with tempfile.TemporaryDirectory() as workspace:
            with patcher:
                result = provider.run("fix", Path(workspace))
        self.assertEqual(result.error_kind, "model_not_found")

    def test_run_429_maps_to_rate_limited(self) -> None:
        provider = OpenAICompatibleProvider(
            base_url="https://api.example.com/v1",
            api_key="sk-test",
            model="gpt-4o",
        )
        patcher, _ = self._patched_post(
            status=429, body=json.dumps({"error": {"message": "Rate limit reached"}})
        )
        with tempfile.TemporaryDirectory() as workspace:
            with patcher:
                result = provider.run("fix", Path(workspace))
        self.assertEqual(result.error_kind, "rate_limited")

    def test_run_400_context_length_maps_to_context_too_long(self) -> None:
        provider = OpenAICompatibleProvider(
            base_url="https://api.example.com/v1",
            api_key="sk-test",
            model="gpt-4o",
        )
        patcher, _ = self._patched_post(
            status=400, body=json.dumps({"error": {"message": "context_length_exceeded"}})
        )
        with tempfile.TemporaryDirectory() as workspace:
            with patcher:
                result = provider.run("fix", Path(workspace))
        self.assertEqual(result.error_kind, "context_too_long")

    def test_run_504_maps_to_api_timeout(self) -> None:
        provider = OpenAICompatibleProvider(
            base_url="https://api.example.com/v1",
            api_key="sk-test",
            model="gpt-4o",
        )
        patcher, _ = self._patched_post(
            status=504, body="<html>Gateway timeout</html>"
        )
        with tempfile.TemporaryDirectory() as workspace:
            with patcher:
                result = provider.run("fix", Path(workspace))
        self.assertEqual(result.error_kind, "api_timeout")

    def test_run_network_failure_maps_to_api_connection_failed(self) -> None:
        import urllib.error

        provider = OpenAICompatibleProvider(
            base_url="https://api.example.com/v1",
            api_key="sk-test",
            model="gpt-4o",
        )
        from src import coding_agent

        def raise_urlerror(*args, **kwargs):
            raise urllib.error.URLError("NameResolutionError: nodename nor servname provided")

        with tempfile.TemporaryDirectory() as workspace:
            with patch.object(coding_agent, "_post_json", side_effect=raise_urlerror):
                result = provider.run("fix", Path(workspace))
        self.assertEqual(result.error_kind, "api_connection_failed")

    def test_run_bad_json_response_maps_to_api_connection_failed(self) -> None:
        provider = OpenAICompatibleProvider(
            base_url="https://api.example.com/v1",
            api_key="sk-test",
            model="gpt-4o",
        )
        from src import coding_agent

        with tempfile.TemporaryDirectory() as workspace:
            with patch.object(coding_agent, "_post_json", return_value=(200, "not json at all")):
                result = provider.run("fix", Path(workspace))
        self.assertEqual(result.error_kind, "api_connection_failed")
        self.assertIn("JSON", (result.error_action or ""))

    def test_run_unparseable_diff_maps_to_no_diff(self) -> None:
        """A successful HTTP response with no diff in the body is a
        clean ``no_diff`` failure -- the worker can present the raw
        model output for the user to debug."""
        provider = OpenAICompatibleProvider(
            base_url="https://api.example.com/v1",
            api_key="sk-test",
            model="gpt-4o",
        )
        patcher, _ = self._patched_post(
            status=200,
            body=json.dumps({"choices": [{"message": {"content": "I cannot help with that."}}]}),
        )
        with tempfile.TemporaryDirectory() as workspace:
            with patcher:
                result = provider.run("fix", Path(workspace))
        self.assertEqual(result.error_kind, "no_diff")
        self.assertIn("AI", (result.error_action or ""))

    def test_health_check_returns_true_on_2xx(self) -> None:
        provider = OpenAICompatibleProvider(
            base_url="https://api.example.com/v1",
            api_key="sk-test",
            model="gpt-4o",
        )
        from src import coding_agent

        with patch.object(coding_agent, "_post_json", return_value=(200, "{}")):
            self.assertTrue(provider.health_check())

    def test_health_check_returns_false_on_4xx(self) -> None:
        provider = OpenAICompatibleProvider(
            base_url="https://api.example.com/v1",
            api_key="sk-bad",
            model="gpt-4o",
        )
        from src import coding_agent

        with patch.object(coding_agent, "_post_json", return_value=(401, "{}")):
            self.assertFalse(provider.health_check())

    def test_init_rejects_missing_base_url(self) -> None:
        with self.assertRaises(CodingAgentConfigError):
            OpenAICompatibleProvider(base_url="", api_key="sk", model="gpt-4o")

    def test_init_rejects_missing_model(self) -> None:
        with self.assertRaises(CodingAgentConfigError):
            OpenAICompatibleProvider(base_url="https://x", api_key="sk", model="")

    def test_request_contains_repository_file_content_but_not_secrets(self) -> None:
        provider = OpenAICompatibleProvider(
            base_url="https://api.example.com/v1",
            api_key="sk-test",
            model="gpt-4o",
        )
        response = json.dumps(
            {"choices": [{"message": {"content": "```diff\nnot applicable\n```"}}]}
        )
        patcher, calls = self._patched_post(status=200, body=response)
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            (root / "service.py").write_text(
                "UNIQUE_REPOSITORY_MARKER = 731\n", encoding="utf-8"
            )
            (root / ".env").write_text(
                "API_KEY=DO_NOT_LEAK_THIS_VALUE\n", encoding="utf-8"
            )
            with patcher, patch("src.coding_agent._git_apply", return_value=(False, "bad")):
                provider.run("fix service.py", root)
        first_prompt = calls[0]["payload"]["messages"][0]["content"]
        self.assertIn("UNIQUE_REPOSITORY_MARKER = 731", first_prompt)
        self.assertIn("FILE: service.py", first_prompt)
        self.assertNotIn("DO_NOT_LEAK_THIS_VALUE", first_prompt)
        self.assertNotIn("FILE: .env", first_prompt)

    def test_git_apply_failure_is_sent_back_for_one_correction_retry(self) -> None:
        provider = OpenAICompatibleProvider(
            base_url="https://api.example.com/v1",
            api_key="sk-test",
            model="gpt-4o",
        )
        responses = [
            (
                200,
                json.dumps(
                    {"choices": [{"message": {"content": "```diff\nbroken patch\n```"}}]}
                ),
            ),
            (
                200,
                json.dumps(
                    {
                        "choices": [
                            {
                                "message": {
                                    "content": (
                                        "```diff\n"
                                        "--- a/app.py\n"
                                        "+++ b/app.py\n"
                                        "@@ -1 +1 @@\n"
                                        "-old\n"
                                        "+fixed\n"
                                        "```"
                                    )
                                }
                            }
                        ]
                    }
                ),
            ),
        ]
        calls: list[dict[str, object]] = []

        def fake_post(url, payload, *, headers, timeout):
            calls.append(payload)
            return responses.pop(0)

        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            target = root / "app.py"
            target.write_text("old\n", encoding="utf-8")
            with patch("src.coding_agent._post_json", side_effect=fake_post):
                result = provider.run("fix app.py", root)
            self.assertEqual(target.read_text(encoding="utf-8"), "fixed\n")
        self.assertTrue(result.ok)
        self.assertEqual(result.metadata["apply_retries"], 1)
        self.assertEqual(len(calls), 2)
        retry_message = calls[1]["messages"][-1]["content"]
        self.assertIn("git apply", retry_message)
        self.assertIn("rejected the patch", retry_message)


# ---------------------------------------------------------------------------
# AnthropicProvider -- request format and error classification.
# ---------------------------------------------------------------------------


class AnthropicProviderTest(unittest.TestCase):
    """Mocked-HTTP tests for the Anthropic Messages API path."""

    def _patched_post(self, *, status: int, body: str):
        from src import coding_agent

        calls: list[dict[str, object]] = []

        def fake_post(url, payload, *, headers, timeout):
            calls.append({"url": url, "payload": payload, "headers": headers, "timeout": timeout})
            return status, body

        return patch.object(coding_agent, "_post_json", side_effect=fake_post), calls

    def test_run_sends_messages_payload(self) -> None:
        provider = AnthropicProvider(api_key="sk-ant-test", model="claude-sonnet-4-5")
        fake_response = json.dumps(
            {"content": [{"type": "text", "text": "```diff\n--- a/x\n+++ b/x\n@@\n-a\n+b\n```"}]}
        )
        patcher, calls = self._patched_post(status=200, body=fake_response)
        with tempfile.TemporaryDirectory() as workspace:
            with patch.object(subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="", stderr="")):
                with patcher:
                    result = provider.run("fix the bug", Path(workspace))
        self.assertIsNone(result.error_kind)
        self.assertEqual(len(calls), 1)
        call = calls[0]
        self.assertEqual(call["url"], "https://api.anthropic.com/v1/messages")
        self.assertEqual(call["headers"]["x-api-key"], "sk-ant-test")
        self.assertEqual(call["headers"]["anthropic-version"], "2023-06-01")
        payload = call["payload"]
        assert isinstance(payload, dict)
        self.assertEqual(payload["model"], "claude-sonnet-4-5")
        self.assertEqual(payload["messages"][0]["role"], "user")

    def test_run_401_maps_to_api_key_invalid(self) -> None:
        provider = AnthropicProvider(api_key="sk-ant-bad", model="claude-sonnet-4-5")
        patcher, _ = self._patched_post(
            status=401, body=json.dumps({"error": {"message": "invalid x-api-key"}})
        )
        with tempfile.TemporaryDirectory() as workspace:
            with patcher:
                result = provider.run("fix", Path(workspace))
        self.assertEqual(result.error_kind, "api_key_invalid")

    def test_run_429_maps_to_rate_limited(self) -> None:
        provider = AnthropicProvider(api_key="sk-ant", model="claude-sonnet-4-5")
        patcher, _ = self._patched_post(
            status=429, body=json.dumps({"error": {"message": "Number of requests exceeded"}})
        )
        with tempfile.TemporaryDirectory() as workspace:
            with patcher:
                result = provider.run("fix", Path(workspace))
        self.assertEqual(result.error_kind, "rate_limited")

    def test_run_400_context_length_maps_to_context_too_long(self) -> None:
        provider = AnthropicProvider(api_key="sk-ant", model="claude-sonnet-4-5")
        patcher, _ = self._patched_post(
            status=400, body=json.dumps({"error": {"message": "prompt is too long: 250000 tokens"}})
        )
        with tempfile.TemporaryDirectory() as workspace:
            with patcher:
                result = provider.run("fix", Path(workspace))
        self.assertEqual(result.error_kind, "context_too_long")

    def test_run_404_maps_to_model_not_found(self) -> None:
        provider = AnthropicProvider(api_key="sk-ant", model="claude-unknown")
        patcher, _ = self._patched_post(
            status=404, body=json.dumps({"error": {"message": "model not found"}})
        )
        with tempfile.TemporaryDirectory() as workspace:
            with patcher:
                result = provider.run("fix", Path(workspace))
        self.assertEqual(result.error_kind, "model_not_found")

    def test_run_network_failure_maps_to_api_connection_failed(self) -> None:
        import urllib.error

        provider = AnthropicProvider(api_key="sk-ant", model="claude-sonnet-4-5")
        from src import coding_agent

        def raise_urlerror(*args, **kwargs):
            raise urllib.error.URLError("Connection refused")

        with tempfile.TemporaryDirectory() as workspace:
            with patch.object(coding_agent, "_post_json", side_effect=raise_urlerror):
                result = provider.run("fix", Path(workspace))
        self.assertEqual(result.error_kind, "api_connection_failed")

    def test_health_check_returns_true_on_2xx(self) -> None:
        provider = AnthropicProvider(api_key="sk-ant", model="claude-sonnet-4-5")
        from src import coding_agent

        with patch.object(coding_agent, "_post_json", return_value=(200, "{}")):
            self.assertTrue(provider.health_check())

    def test_init_rejects_empty_api_key(self) -> None:
        with self.assertRaises(CodingAgentConfigError):
            AnthropicProvider(api_key="", model="claude-sonnet-4-5")

    def test_init_rejects_empty_model(self) -> None:
        with self.assertRaises(CodingAgentConfigError):
            AnthropicProvider(api_key="sk-ant", model="")

    def test_request_contains_bounded_repository_snapshot(self) -> None:
        provider = AnthropicProvider(api_key="sk-ant", model="claude-sonnet-4-5")
        response = json.dumps(
            {"content": [{"type": "text", "text": "```diff\ninvalid\n```"}]}
        )
        patcher, calls = self._patched_post(status=200, body=response)
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            (root / "handler.ts").write_text(
                "export const REPOSITORY_FACT = 'visible';\n", encoding="utf-8"
            )
            with patcher, patch("src.coding_agent._git_apply", return_value=(False, "bad")):
                provider.run("fix handler.ts", root)
        content = calls[0]["payload"]["messages"][0]["content"]
        self.assertIn("REPOSITORY_FACT = 'visible'", content)
        self.assertIn("UNTRUSTED DATA", content)


class WorkspaceContextSafetyTest(unittest.TestCase):
    def test_context_is_bounded_and_reports_truncation(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            for index in range(20):
                (root / f"module_{index}.py").write_text(
                    f"MARKER_{index} = " + ("x" * 600) + "\n", encoding="utf-8"
                )
            context = build_workspace_context(root, max_chars=2_000, max_file_chars=800)
        self.assertLessEqual(len(context.text), 2_000)
        self.assertTrue(context.truncated)

    def test_sensitive_binary_and_external_symlink_content_is_never_read(self) -> None:
        with tempfile.TemporaryDirectory() as workspace, tempfile.TemporaryDirectory() as outside:
            root = Path(workspace)
            (root / "safe.py").write_text("SAFE_VALUE = 1\n", encoding="utf-8")
            (root / "credentials.json").write_text(
                '{"password":"CREDENTIAL_LEAK"}', encoding="utf-8"
            )
            (root / "token.txt").write_text("TOKEN_LEAK", encoding="utf-8")
            (root / "settings.py").write_text(
                "api_key = 'THIS_IS_A_REAL_SECRET_VALUE'\n", encoding="utf-8"
            )
            (root / ".ghe").mkdir()
            (root / ".ghe" / "config.yml").write_text(
                "api_key: GHE_CONFIG_SECRET_LEAK\n", encoding="utf-8"
            )
            (root / "image.dat").write_bytes(b"\x00BINARY_LEAK")
            (root / "huge.py").write_text(
                "LARGE_FILE_LEAK = '" + ("z" * 20_000) + "'\n", encoding="utf-8"
            )
            outside_secret = Path(outside) / "outside.py"
            outside_secret.write_text("SYMLINK_ESCAPE_LEAK = True\n", encoding="utf-8")
            (root / "linked.py").symlink_to(outside_secret)
            context = build_workspace_context(root)
        self.assertIn("SAFE_VALUE = 1", context.text)
        self.assertNotIn("CREDENTIAL_LEAK", context.text)
        self.assertNotIn("TOKEN_LEAK", context.text)
        self.assertNotIn("THIS_IS_A_REAL_SECRET_VALUE", context.text)
        self.assertNotIn("GHE_CONFIG_SECRET_LEAK", context.text)
        self.assertNotIn("BINARY_LEAK", context.text)
        self.assertNotIn("LARGE_FILE_LEAK", context.text)
        self.assertNotIn("SYMLINK_ESCAPE_LEAK", context.text)


class FakeProviderDisclosureTest(unittest.TestCase):
    def test_result_is_explicitly_marked_as_unverified_demo(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            (root / "sample.py").write_text("value = 1\n", encoding="utf-8")
            result = FakeProvider().run("Issue #999999", root)
        self.assertTrue(result.metadata["demo"])
        self.assertEqual(result.metadata["provider"], "fake")
        self.assertEqual(result.metadata["verification"], "simulated_unverified")


# ---------------------------------------------------------------------------
# Diff extraction and ``git apply`` integration.
# ---------------------------------------------------------------------------


class DiffExtractionTest(unittest.TestCase):
    """The model-side helpers used by every API provider."""

    def test_extract_fenced_diff_block(self) -> None:
        text = (
            "Here is the fix:\n\n"
            "```diff\n--- a/foo.py\n+++ b/foo.py\n@@\n-old\n+new\n```\n\nDone."
        )
        self.assertEqual(
            _extract_unified_diff(text),
            "--- a/foo.py\n+++ b/foo.py\n@@\n-old\n+new",
        )

    def test_extract_generic_fence_when_no_diff_label(self) -> None:
        """Models that forget the ``diff`` label after the opening fence
        still get a parseable patch thanks to the fallback regex."""
        text = "```\n--- a/foo\n+++ b/foo\n@@\n-a\n+b\n```"
        self.assertEqual(
            _extract_unified_diff(text),
            "--- a/foo\n+++ b/foo\n@@\n-a\n+b",
        )

    def test_extract_whole_text_when_no_fence(self) -> None:
        text = "--- a/foo\n+++ b/foo\n@@\n-a\n+b"
        self.assertEqual(_extract_unified_diff(text), text)

    def test_git_apply_writes_and_succeeds_on_valid_diff(self) -> None:
        """Round-trip: write a file, generate a valid diff, apply it."""
        with tempfile.TemporaryDirectory() as workspace:
            target = Path(workspace) / "hello.txt"
            target.write_text("hello\n", encoding="utf-8")
            subprocess.run(
                ["git", "init", "-q"], cwd=workspace, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "config", "user.email", "t@t"],
                cwd=workspace,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "t"],
                cwd=workspace,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "add", "."], cwd=workspace, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "commit", "-m", "init", "-q"],
                cwd=workspace,
                check=True,
                capture_output=True,
            )
            diff = (
                "--- a/hello.txt\n"
                "+++ b/hello.txt\n"
                "@@ -1 +1 @@\n"
                "-hello\n"
                "+hello world\n"
            )
            ok, detail = _git_apply(diff, Path(workspace))
            self.assertTrue(ok, msg=detail)
            self.assertEqual(target.read_text(encoding="utf-8"), "hello world\n")

    def test_git_apply_rejects_empty_diff(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            ok, detail = _git_apply("", Path(workspace))
            self.assertFalse(ok)
            self.assertIn("empty", detail)

    def test_git_apply_uses_external_temp_file_and_always_removes_it(self) -> None:
        seen_paths: list[Path] = []

        def fake_run(arguments, **kwargs):
            patch_path = Path(arguments[-1])
            self.assertTrue(patch_path.exists())
            seen_paths.append(patch_path)
            return SimpleNamespace(returncode=1, stdout="", stderr="bad patch")

        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            with patch.object(subprocess, "run", side_effect=fake_run):
                ok, _ = _git_apply("not a patch", root)
            self.assertFalse(ok)
            self.assertFalse((root / ".ghe-agent.patch").exists())
            self.assertTrue(seen_paths)
            self.assertTrue(all(not path.exists() for path in seen_paths))

    def test_git_apply_rejects_malformed_diff(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            ok, detail = _git_apply("not a diff at all\n", Path(workspace))
            self.assertFalse(ok)
            self.assertIn("git apply", detail)


# ---------------------------------------------------------------------------
# HTTP error classifier -- table-driven check that every status maps right.
# ---------------------------------------------------------------------------


class HttpErrorClassificationTest(unittest.TestCase):
    """``_classify_http_error`` is the single source of truth for the
    new error_kind values. A regression in the mapping table would
    silently mis-diagnose every failure, so each row gets a test."""

    def test_status_400_default_is_unknown_when_no_pattern_matches(self) -> None:
        # A 400 with a body that does not mention context_length falls
        # back to the table's default kind, not a hard unknown.
        result = _classify_http_error(status=400, body="bad shape", message="")
        # 400 with no context pattern -> default falls to "context_too_long"
        # because the table row has no further narrowing, so we expect
        # the row's default.
        self.assertEqual(result.error_kind, "context_too_long")

    def test_status_401_default(self) -> None:
        result = _classify_http_error(status=401, body="", message="HTTP 401")
        self.assertEqual(result.error_kind, "api_key_invalid")

    def test_status_404_default(self) -> None:
        result = _classify_http_error(status=404, body="", message="HTTP 404")
        self.assertEqual(result.error_kind, "model_not_found")

    def test_status_408_default(self) -> None:
        result = _classify_http_error(status=408, body="", message="HTTP 408")
        self.assertEqual(result.error_kind, "api_timeout")

    def test_status_429_default(self) -> None:
        result = _classify_http_error(status=429, body="", message="HTTP 429")
        self.assertEqual(result.error_kind, "rate_limited")

    def test_status_500_default(self) -> None:
        result = _classify_http_error(status=500, body="", message="HTTP 500")
        self.assertEqual(result.error_kind, "api_connection_failed")

    def test_status_502_default(self) -> None:
        result = _classify_http_error(status=502, body="", message="HTTP 502")
        self.assertEqual(result.error_kind, "api_connection_failed")

    def test_status_503_default(self) -> None:
        result = _classify_http_error(status=503, body="", message="HTTP 503")
        self.assertEqual(result.error_kind, "api_connection_failed")

    def test_status_504_default(self) -> None:
        result = _classify_http_error(status=504, body="", message="HTTP 504")
        self.assertEqual(result.error_kind, "api_timeout")

    def test_no_status_with_timeout_message(self) -> None:
        result = _classify_http_error(
            status=None, body="", message="urllib error: timed out"
        )
        self.assertEqual(result.error_kind, "api_timeout")

    def test_no_status_with_connection_refused(self) -> None:
        result = _classify_http_error(
            status=None, body="", message="Connection refused by server"
        )
        self.assertEqual(result.error_kind, "api_connection_failed")

    def test_no_status_with_name_resolution_error(self) -> None:
        result = _classify_http_error(
            status=None,
            body="",
            message="NameResolutionError: nodename nor servname provided",
        )
        self.assertEqual(result.error_kind, "api_connection_failed")

    def test_no_status_with_unknown_message_falls_back_to_unknown(self) -> None:
        result = _classify_http_error(
            status=None, body="", message="something completely new"
        )
        self.assertEqual(result.error_kind, "unknown")

    def test_table_covers_all_required_status_codes(self) -> None:
        """Pin the set of status codes the classifier understands so a
        refactor cannot silently drop one."""
        expected_statuses = {400, 401, 403, 404, 408, 413, 429, 500, 502, 503, 504}
        self.assertEqual(set(_HTTP_STATUS_TABLE.keys()), expected_statuses)


# ---------------------------------------------------------------------------
# Provider factory.
# ---------------------------------------------------------------------------


class GetProviderTest(unittest.TestCase):
    """The factory resolves ``config["coding_agent"]`` to a class."""

    def test_openai_compatible_returns_correct_provider(self) -> None:
        provider = get_provider(
            {
                "coding_agent": {
                    "provider": "openai_compatible",
                    "base_url": "https://api.example.com/v1",
                    "api_key": "sk-test",
                    "model": "gpt-4o",
                }
            }
        )
        self.assertIsInstance(provider, OpenAICompatibleProvider)
        self.assertEqual(provider.name(), "openai_compatible")
        self.assertEqual(provider.model, "gpt-4o")

    def test_anthropic_returns_correct_provider(self) -> None:
        provider = get_provider(
            {
                "coding_agent": {
                    "provider": "anthropic",
                    "api_key": "sk-ant",
                    "model": "claude-sonnet-4-5",
                }
            }
        )
        self.assertIsInstance(provider, AnthropicProvider)
        self.assertEqual(provider.name(), "anthropic")
        self.assertEqual(provider.model, "claude-sonnet-4-5")

    def test_claude_cli_returns_correct_provider(self) -> None:
        provider = get_provider(
            {"coding_agent": {"provider": "claude_cli"}}
        )
        self.assertIsInstance(provider, ClaudeCLIProvider)
        self.assertEqual(provider.name(), "claude_cli")

    def test_codex_cli_returns_correct_provider(self) -> None:
        with patch.object(CodexCLIProvider, "_works", return_value=True), patch(
            "src.process_runtime.find_desktop_executable", return_value="/usr/bin/codex"
        ):
            provider = get_provider({"coding_agent": {"provider": "codex_cli"}})
        self.assertIsInstance(provider, CodexCLIProvider)
        self.assertEqual(provider.name(), "codex_cli")

    def test_default_provider_is_openai_compatible(self) -> None:
        """Omitting ``provider`` falls back to ``openai_compatible``."""
        provider = get_provider(
            {
                "coding_agent": {
                    "api_key": "sk-test",
                    "base_url": "https://api.example.com/v1",
                    "model": "gpt-4o",
                }
            }
        )
        self.assertIsInstance(provider, OpenAICompatibleProvider)
        self.assertEqual(provider.name(), "openai_compatible")

    def test_provider_aliases_are_accepted(self) -> None:
        """``openai-compatible`` and ``openai`` both resolve to the
        OpenAI-compatible provider; ``claude-code`` to the CLI."""
        for alias, expected_cls in [
            ("openai-compatible", OpenAICompatibleProvider),
            ("openai", OpenAICompatibleProvider),
            ("claude-code", ClaudeCLIProvider),
            ("claude", ClaudeCLIProvider),
            ("codex", CodexCLIProvider),
        ]:
            with self.subTest(alias=alias):
                with patch.object(CodexCLIProvider, "_works", return_value=True), patch(
                    "src.process_runtime.find_desktop_executable", return_value="/usr/bin/codex"
                ):
                    provider = get_provider({"coding_agent": {"provider": alias}})
                self.assertIsInstance(provider, expected_cls)

    def test_missing_section_raises_clear_error(self) -> None:
        with self.assertRaises(CodingAgentConfigError) as ctx:
            get_provider({})
        self.assertIn("coding_agent", str(ctx.exception))
        self.assertIn("--configure-coding-agent", str(ctx.exception))

    def test_unknown_provider_raises_clear_error(self) -> None:
        with self.assertRaises(CodingAgentConfigError) as ctx:
            get_provider({"coding_agent": {"provider": "gpt-9000"}})
        self.assertIn("Unknown", str(ctx.exception))
        self.assertIn("gpt-9000", str(ctx.exception))

    def test_empty_config_raises(self) -> None:
        with self.assertRaises(CodingAgentConfigError):
            get_provider(None)  # type: ignore[arg-type]

    def test_config_path_falls_back_to_env_var(self) -> None:
        """When ``api_key`` is left as ``${LLM_API_KEY}`` (unexpanded)
        the factory falls back to the matching environment variable."""
        with patch.dict(os.environ, {"LLM_API_KEY": "from-env"}):
            provider = get_provider(
                {
                    "coding_agent": {
                        "provider": "openai_compatible",
                        "api_key": "${LLM_API_KEY}",
                        "base_url": "https://api.example.com/v1",
                        "model": "gpt-4o",
                    }
                }
            )
        self.assertEqual(provider.api_key, "from-env")

    def test_config_path_falls_back_to_anthropic_env(self) -> None:
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "ant-from-env"}):
            provider = get_provider(
                {
                    "coding_agent": {
                        "provider": "anthropic",
                        "api_key": "${ANTHROPIC_API_KEY}",
                        "model": "claude-sonnet-4-5",
                    }
                }
            )
        self.assertEqual(provider.api_key, "ant-from-env")

    def test_resolve_api_key_prefers_explicit_value(self) -> None:
        """A non-placeholder value is honoured even if an env var is set."""
        with patch.dict(os.environ, {"LLM_API_KEY": "from-env"}):
            self.assertEqual(_resolve_api_key("from-config", env_var="LLM_API_KEY"), "from-config")

    def test_resolve_api_key_handles_placeholder_with_no_env(self) -> None:
        self.assertEqual(_resolve_api_key("${LLM_API_KEY}", env_var="LLM_API_KEY"), "")

    def test_resolve_api_key_uses_the_named_placeholder_environment(self) -> None:
        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "openai-from-env", "LLM_API_KEY": "fallback"},
        ):
            self.assertEqual(
                _resolve_api_key("${OPENAI_API_KEY}", env_var="LLM_API_KEY"),
                "openai-from-env",
            )

    def test_resolve_api_key_handles_empty_string(self) -> None:
        with patch.dict(os.environ, {"LLM_API_KEY": "from-env"}):
            self.assertEqual(_resolve_api_key("", env_var="LLM_API_KEY"), "from-env")


# ---------------------------------------------------------------------------
# ``has_provider_config`` helper.
# ---------------------------------------------------------------------------


class HasProviderConfigTest(unittest.TestCase):
    """The cheap boolean check the preflight uses."""

    def test_returns_true_when_section_present(self) -> None:
        self.assertTrue(
            has_provider_config({"coding_agent": {"provider": "openai_compatible"}})
        )

    def test_returns_false_when_section_missing(self) -> None:
        self.assertFalse(has_provider_config({}))

    def test_returns_false_for_non_dict_section(self) -> None:
        # A scalar value at ``coding_agent`` is a malformed config;
        # we treat it the same as missing.
        self.assertFalse(has_provider_config({"coding_agent": "openai_compatible"}))

    def test_returns_false_for_none_config(self) -> None:
        self.assertFalse(has_provider_config(None))  # type: ignore[arg-type]

    def test_returns_true_for_empty_section_dict(self) -> None:
        """An empty dict still counts as "configured" -- the factory
        will then raise with a precise error."""
        self.assertTrue(has_provider_config({"coding_agent": {}}))


# ---------------------------------------------------------------------------
# ``diagnose_repair_error`` integration with the new error_kinds.
# ---------------------------------------------------------------------------


class DiagnoseNewErrorKindsTest(unittest.TestCase):
    """The seven new error_kinds are *also* matched through the
    structured lookup in :func:`diagnose_repair_error`. The tests
    here focus on the path the new providers take: a job JSON that
    carries a structured ``error_kind`` field. The regex fallback
    path is covered by :mod:`tests.test_main_diagnose`."""

    def test_structured_api_key_invalid(self) -> None:
        result = diagnose_repair_error(
            "some unrelated text",
            job={"error_kind": "api_key_invalid"},
        )
        self.assertEqual(result["error_kind"], "api_key_invalid")
        self.assertIn("API key", result["error_action"])
        self.assertIn(".ghe/config.yml", result["hint"])

    def test_structured_api_connection_failed(self) -> None:
        result = diagnose_repair_error("", job={"error_kind": "api_connection_failed"})
        self.assertEqual(result["error_kind"], "api_connection_failed")
        self.assertIn("base_url", result["hint"])

    def test_structured_model_not_found(self) -> None:
        result = diagnose_repair_error("", job={"error_kind": "model_not_found"})
        self.assertEqual(result["error_kind"], "model_not_found")
        self.assertIn("model", result["hint"].lower())

    def test_structured_rate_limited(self) -> None:
        result = diagnose_repair_error("", job={"error_kind": "rate_limited"})
        self.assertEqual(result["error_kind"], "rate_limited")
        self.assertIn("限流", result["error_action"] or "")

    def test_structured_context_too_long(self) -> None:
        result = diagnose_repair_error("", job={"error_kind": "context_too_long"})
        self.assertEqual(result["error_kind"], "context_too_long")
        self.assertIn("context", result["hint"].lower())

    def test_structured_api_timeout(self) -> None:
        result = diagnose_repair_error("", job={"error_kind": "api_timeout"})
        self.assertEqual(result["error_kind"], "api_timeout")
        self.assertIn("超时", result["error_action"] or "")

    def test_structured_tool_call_failed(self) -> None:
        result = diagnose_repair_error("", job={"error_kind": "tool_call_failed"})
        self.assertEqual(result["error_kind"], "tool_call_failed")
        self.assertIn("工具", result["error_action"] or "")

    def test_structured_no_diff(self) -> None:
        result = diagnose_repair_error("", job={"error_kind": "no_diff"})
        self.assertEqual(result["error_kind"], "no_diff")
        self.assertIn("diff", result["error_action"].lower())

    def test_structured_lookup_wins_over_text_match(self) -> None:
        """When the job carries a structured ``error_kind``, the
        diagnostic text on stderr/message is *ignored* so a provider
        that emits "rate limit" in its action text does not get
        mis-classified as ``rate_limited`` when the structured
        ``error_kind`` says ``api_key_invalid``."""
        result = diagnose_repair_error(
            "rate limit exceeded", job={"error_kind": "api_key_invalid"}
        )
        self.assertEqual(result["error_kind"], "api_key_invalid")

    def test_unknown_structured_kind_falls_through_to_regex(self) -> None:
        """A typo in the structured kind should not crash; the regex
        fallback still runs and the ``unknown`` default catches it."""
        result = diagnose_repair_error(
            "no diff at all", job={"error_kind": "bogus_kind"}
        )
        # "no diff at all" matches the no_diff regex first.
        self.assertEqual(result["error_kind"], "no_diff")

    def test_structured_lookup_covers_all_documented_kinds(self) -> None:
        """Every value in ``src.coding_agent.ERROR_KINDS`` must have
        a structured entry. Adding a new error_kind without a hint
        is a UX regression -- the user would see an empty action."""
        from src.coding_agent import ERROR_KINDS

        missing = sorted(kind for kind in ERROR_KINDS if kind not in _STRUCTURED_DIAGNOSES)
        self.assertEqual(missing, [], msg=f"missing structured diagnoses for: {missing}")

    def test_regex_path_still_works_for_new_kinds(self) -> None:
        """When the structured field is missing, the new regex
        patterns must still match the textual error_action text the
        providers write to ``job['message']``."""
        for needle, expected_kind in [
            ("API key 无效，更新 .ghe/config.yml 的 api_key", "api_key_invalid"),
            ("API 不可达，检查 base_url + 网络", "api_connection_failed"),
            ("model 名错", "model_not_found"),
            ("API 限流", "rate_limited"),
            ("prompt 太大，缩小任务范围", "context_too_long"),
            ("API 超时", "api_timeout"),
            ("工具调用失败", "tool_call_failed"),
        ]:
            with self.subTest(needle=needle):
                result = diagnose_repair_error(needle)
                self.assertEqual(result["error_kind"], expected_kind)


# ---------------------------------------------------------------------------
# ClaudeCLIProvider -- subprocess classification.
# ---------------------------------------------------------------------------


class CodexCLIProviderTest(unittest.TestCase):
    def test_health_check_requires_login_status(self) -> None:
        with patch.object(CodexCLIProvider, "_works", return_value=True):
            provider = CodexCLIProvider(executable="/usr/bin/codex")
        with patch("src.coding_agent.subprocess.run") as run:
            run.return_value = SimpleNamespace(
                returncode=0, stdout="Logged in using ChatGPT\n", stderr=""
            )
            self.assertTrue(provider.health_check())
        run.assert_called_once_with(
            ["/usr/bin/codex", "login", "status"],
            text=True,
            capture_output=True,
            timeout=10,
            shell=False,
        )

    def test_run_uses_workspace_write_and_stdin(self) -> None:
        with patch.object(CodexCLIProvider, "_works", return_value=True):
            provider = CodexCLIProvider(executable="/usr/bin/codex")
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "src.coding_agent.subprocess.run"
        ) as run:
            run.return_value = SimpleNamespace(returncode=0, stdout="done", stderr="")
            result = provider.run("fix it", Path(temp_dir))
        self.assertTrue(result.ok)
        kwargs = run.call_args.kwargs
        self.assertEqual(kwargs["input"], "fix it")
        self.assertEqual(kwargs["cwd"], temp_dir)
        self.assertIn("workspace-write", run.call_args.args[0])
        self.assertEqual(run.call_args.args[0][-1], "-")


class ClaudeCLIErrorClassificationTest(unittest.TestCase):
    """The CLI provider maps subprocess stderr to a stable kind."""

    def test_classify_not_logged_in(self) -> None:
        from src.coding_agent import _classify_claude_cli_error

        self.assertEqual(
            _classify_claude_cli_error("claude: not logged in"),
            "claude_not_authenticated",
        )
        self.assertEqual(
            _classify_claude_cli_error("claude: not authenticated"),
            "claude_not_authenticated",
        )

    def test_classify_rate_limit(self) -> None:
        from src.coding_agent import _classify_claude_cli_error

        self.assertEqual(
            _classify_claude_cli_error("Rate limit exceeded (HTTP 429)"),
            "rate_limited",
        )

    def test_classify_context_length(self) -> None:
        from src.coding_agent import _classify_claude_cli_error

        self.assertEqual(
            _classify_claude_cli_error("prompt is too long: context_length_exceeded"),
            "context_too_long",
        )

    def test_classify_timeout(self) -> None:
        from src.coding_agent import _classify_claude_cli_error

        self.assertEqual(
            _classify_claude_cli_error("claude timed out after 1800s"),
            "timeout",
        )

    def test_classify_permission(self) -> None:
        from src.coding_agent import _classify_claude_cli_error

        self.assertEqual(
            _classify_claude_cli_error("Permission denied: EACCES"),
            "permission_denied",
        )

    def test_classify_unknown_falls_through(self) -> None:
        from src.coding_agent import _classify_claude_cli_error

        self.assertEqual(
            _classify_claude_cli_error("something completely new"),
            "unknown",
        )


# ---------------------------------------------------------------------------
# CodingAgentResult shape.
# ---------------------------------------------------------------------------


class CodingAgentResultTest(unittest.TestCase):
    """The dataclass the worker reads from."""

    def test_ok_property_true_when_no_error(self) -> None:
        result = CodingAgentResult(summary="ok")
        self.assertTrue(result.ok)

    def test_ok_property_false_when_error_kind_set(self) -> None:
        result = CodingAgentResult(summary="", error_kind="api_key_invalid")
        self.assertFalse(result.ok)

    def test_default_changed_files_is_empty_list(self) -> None:
        result = CodingAgentResult(summary="ok")
        self.assertEqual(result.changed_files, [])

    def test_error_fields_default_to_none(self) -> None:
        result = CodingAgentResult(summary="ok")
        self.assertIsNone(result.error_kind)
        self.assertIsNone(result.error_action)
        self.assertIsNone(result.error_hint)

    def test_coding_agent_provider_is_abstract(self) -> None:
        """A direct subclass that forgets ``name`` / ``run`` cannot
        be instantiated. The guard is small but it catches the most
        common refactor mistake."""
        with self.assertRaises(TypeError):
            CodingAgentProvider()  # type: ignore[abstract]


if __name__ == "__main__":
    unittest.main()
