"""Unit tests for src/delegation.py.

Focus on the safety properties: a dry-run plan must never start a subprocess,
executable names must be allowlisted, task content can never reach a shell,
and explicit opt-in is required to run anything.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.delegation import (
    ClaudeCodeAdapter,
    CodexAdapter,
    DelegationError,
    GenericCLIAdapter,
    _validate_executable,
    _validate_repo_path,
    _validate_static_arguments,
    execute_delegation,
)


def test_codex_adapter_plan_does_not_invoke_subprocess(tmp_path):
    adapter = CodexAdapter(allowed_root=tmp_path)
    plan = adapter.plan("# task\nDo the thing.", tmp_path)
    assert plan.adapter == "codex"
    assert plan.command[0] == "codex"
    assert plan.dry_run is True
    assert plan.task_markdown.startswith("# task")
    assert "Dry run only" in plan.notes[0]


def test_claude_code_adapter_uses_print_mode(tmp_path):
    adapter = ClaudeCodeAdapter(allowed_root=tmp_path)
    plan = adapter.plan("task body", tmp_path)
    assert plan.adapter == "claude-code"
    assert plan.command == ("claude", "--print")


def test_generic_cli_requires_explicit_executable_allowlist(tmp_path):
    """A bare ``GenericCLIAdapter("aider")`` works because aider is in the default allowlist."""
    adapter = GenericCLIAdapter("aider", allowed_root=tmp_path)
    plan = adapter.plan("task", tmp_path)
    assert plan.command[0] == "aider"


def test_generic_cli_rejects_unknown_executable(tmp_path):
    with pytest.raises(DelegationError) as exc:
        GenericCLIAdapter("rm", allowed_root=tmp_path)
    assert "not in the command allowlist" in str(exc.value)


def test_generic_cli_rejects_executable_with_path_or_shell_syntax(tmp_path):
    with pytest.raises(DelegationError):
        GenericCLIAdapter("../bin/agent", allowed_root=tmp_path)
    with pytest.raises(DelegationError):
        GenericCLIAdapter("aider; rm -rf /", allowed_root=tmp_path)


def test_execute_delegation_refuses_without_explicit_opt_in(tmp_path):
    adapter = CodexAdapter(allowed_root=tmp_path)
    plan = adapter.plan("task", tmp_path)
    with pytest.raises(DelegationError) as exc:
        execute_delegation(plan)
    assert "allow_execution=True" in str(exc.value)


def test_execute_delegation_invokes_subprocess_with_safe_arguments(tmp_path):
    adapter = CodexAdapter(allowed_root=tmp_path)
    plan = adapter.plan("task content", tmp_path)
    fake_completed = MagicMock()
    fake_completed.returncode = 0
    fake_completed.stdout = "ok"
    fake_completed.stderr = ""
    with patch("src.delegation.subprocess.run", return_value=fake_completed) as run:
        result = execute_delegation(plan, allow_execution=True)
    assert result.return_code == 0
    args, kwargs = run.call_args
    assert args[0] == ("codex", "exec", "-")
    assert kwargs["shell"] is False
    assert kwargs["input"] == "task content"


def test_execute_delegation_handles_subprocess_timeout(tmp_path):
    adapter = CodexAdapter(allowed_root=tmp_path)
    plan = adapter.plan("task", tmp_path)
    with patch(
        "src.delegation.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=1),
    ):
        with pytest.raises(DelegationError) as exc:
            execute_delegation(plan, allow_execution=True, timeout_seconds=1)
    assert "timeout" in str(exc.value).lower()


def test_validate_repo_path_rejects_outside_allowed_root(tmp_path):
    outside = tmp_path.parent / "elsewhere"
    outside.mkdir()
    with pytest.raises(DelegationError) as exc:
        _validate_repo_path(outside, allowed_root=tmp_path)
    assert "inside the allowed root" in str(exc.value)


def test_validate_static_arguments_rejects_control_bytes():
    with pytest.raises(DelegationError):
        _validate_static_arguments(["ok", "bad\nvalue"])


def test_validate_executable_accepts_known_safe_names():
    _validate_executable("codex", frozenset({"codex"}))
    _validate_executable("claude", frozenset({"claude"}))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
