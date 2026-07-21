"""Safe, opt-in planning for handing prepared tasks to coding-agent CLIs.

This module deliberately separates *planning* from *execution*.  Adapters only
produce a :class:`DelegationPlan`; creating a plan never starts a subprocess.
The caller must make a second, explicit opt-in call to ``execute_delegation``
before an external CLI can run.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Literal, Protocol, Sequence

from pydantic import BaseModel, Field, field_validator


AdapterName = Literal["codex", "claude-code", "generic-cli"]

# These are program names, rather than paths.  Commands are invoked with
# ``shell=False`` and are never composed into a shell string.
DEFAULT_EXECUTABLE_ALLOWLIST = frozenset({"codex", "claude", "opencode", "aider"})
_SAFE_EXECUTABLE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_MAX_TASK_CHARS = 100_000


class DelegationError(RuntimeError):
    """Raised when a delegation plan is unsafe or cannot be executed."""


class DelegationPlan(BaseModel):
    """A validated command plan that has not been run.

    ``task_markdown`` is passed through standard input, not interpolated into a
    shell command.  ``command`` contains only adapter-controlled arguments.
    """

    adapter: AdapterName
    repo_path: Path
    command: tuple[str, ...]
    task_markdown: str
    dry_run: bool = True
    notes: list[str] = Field(default_factory=list)

    @field_validator("command")
    @classmethod
    def command_must_not_be_empty(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise ValueError("Delegation command must not be empty.")
        return value

    @field_validator("task_markdown")
    @classmethod
    def task_must_be_safe_input(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Prepared task Markdown must not be empty.")
        if "\x00" in value:
            raise ValueError("Prepared task Markdown cannot contain NUL bytes.")
        if len(value) > _MAX_TASK_CHARS:
            raise ValueError(f"Prepared task Markdown exceeds {_MAX_TASK_CHARS} characters.")
        return value


class DelegationResult(BaseModel):
    """Result returned only after a caller explicitly enables execution."""

    plan: DelegationPlan
    return_code: int
    stdout: str
    stderr: str


class DelegationAdapter(Protocol):
    """Protocol implemented by all dry-run adapters."""

    def plan(self, task_markdown: str, repo_path: str | Path) -> DelegationPlan:
        """Validate inputs and return a plan without starting an external CLI."""


def _validate_repo_path(repo_path: str | Path, allowed_root: str | Path | None) -> Path:
    """Resolve a repository directory and optionally constrain it to one root."""

    candidate = Path(repo_path).expanduser()
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise DelegationError(f"Repository path does not exist: {candidate}") from exc
    if not resolved.is_dir():
        raise DelegationError(f"Repository path must be a directory: {resolved}")

    if allowed_root is not None:
        try:
            root = Path(allowed_root).expanduser().resolve(strict=True)
        except OSError as exc:
            raise DelegationError(f"Allowed repository root does not exist: {allowed_root}") from exc
        if not root.is_dir():
            raise DelegationError(f"Allowed repository root must be a directory: {root}")
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise DelegationError(
                f"Repository path must be inside the allowed root ({root})."
            ) from exc
    return resolved


def _validate_executable(executable: str, allowlist: frozenset[str]) -> str:
    """Allow only an explicitly approved bare executable name."""

    if not _SAFE_EXECUTABLE.fullmatch(executable):
        raise DelegationError("Executable must be a bare command name without shell syntax.")
    if executable not in allowlist:
        raise DelegationError(f"Executable {executable!r} is not in the command allowlist.")
    return executable


def _validate_static_arguments(arguments: Sequence[str]) -> tuple[str, ...]:
    """Reject control bytes in adapter configuration before subprocess use."""

    safe: list[str] = []
    for argument in arguments:
        if not isinstance(argument, str) or "\x00" in argument or "\n" in argument or "\r" in argument:
            raise DelegationError("CLI arguments must be strings without control characters.")
        safe.append(argument)
    return tuple(safe)


class _BaseAdapter:
    adapter_name: AdapterName
    executable: str
    arguments: tuple[str, ...]

    def __init__(self, *, allowed_root: str | Path | None = None) -> None:
        self.allowed_root = allowed_root

    def plan(self, task_markdown: str, repo_path: str | Path) -> DelegationPlan:
        """Produce a dry-run plan; this method never invokes a subprocess."""

        repo = _validate_repo_path(repo_path, self.allowed_root)
        # Constructing the model also validates task input before it can reach
        # any potential executor.
        return DelegationPlan(
            adapter=self.adapter_name,
            repo_path=repo,
            command=(self.executable, *self.arguments),
            task_markdown=task_markdown,
            dry_run=True,
            notes=[
                "Dry run only: no external coding agent has been started.",
                "The prepared task is supplied on standard input, never via a shell command.",
                "Call execute_delegation(..., allow_execution=True) to explicitly opt in.",
            ],
        )


class CodexAdapter(_BaseAdapter):
    """Plan a non-interactive Codex CLI invocation using standard input."""

    adapter_name: AdapterName = "codex"
    executable = "codex"
    arguments = ("exec", "-")

    def __init__(self, *, allowed_root: str | Path | None = None) -> None:
        super().__init__(allowed_root=allowed_root)
        _validate_executable(self.executable, DEFAULT_EXECUTABLE_ALLOWLIST)


class ClaudeCodeAdapter(_BaseAdapter):
    """Plan a non-interactive Claude Code invocation using standard input."""

    adapter_name: AdapterName = "claude-code"
    executable = "claude"
    arguments = ("--print",)

    def __init__(self, *, allowed_root: str | Path | None = None) -> None:
        super().__init__(allowed_root=allowed_root)
        _validate_executable(self.executable, DEFAULT_EXECUTABLE_ALLOWLIST)


class GenericCLIAdapter(_BaseAdapter):
    """Dry-run adapter for an explicitly allowlisted stdin-capable CLI.

    ``arguments`` must be static, application-owned configuration.  Do not put
    user-controlled task content in it; task content is always sent on stdin.
    """

    adapter_name: AdapterName = "generic-cli"

    def __init__(
        self,
        executable: str,
        arguments: Sequence[str] = (),
        *,
        allowed_root: str | Path | None = None,
        allowed_executables: Sequence[str] | None = None,
    ) -> None:
        super().__init__(allowed_root=allowed_root)
        allowlist = frozenset(allowed_executables or DEFAULT_EXECUTABLE_ALLOWLIST)
        self.executable = _validate_executable(executable, allowlist)
        self.arguments = _validate_static_arguments(arguments)


def execute_delegation(
    plan: DelegationPlan,
    *,
    allow_execution: bool = False,
    timeout_seconds: int = 1_800,
    allowed_root: str | Path | None = None,
    allowed_executables: Sequence[str] | None = None,
) -> DelegationResult:
    """Execute a previously created plan only after explicit caller opt-in.

    The default is intentionally disabled.  This function uses an argument
    list and ``shell=False`` so task Markdown cannot become shell syntax.
    A custom Generic CLI must be repeated in ``allowed_executables`` here;
    this makes the execution approval independent of the dry-run adapter.
    """

    if not allow_execution:
        raise DelegationError(
            "External execution is disabled. Pass allow_execution=True only after human approval."
        )
    if not plan.dry_run:
        raise DelegationError("Only plans created by a dry-run adapter may be executed.")
    if not 1 <= timeout_seconds <= 7_200:
        raise DelegationError("timeout_seconds must be between 1 and 7200.")

    # Revalidate deserialized or manually-created plans at the execution gate.
    repo = _validate_repo_path(plan.repo_path, allowed_root=allowed_root)
    allowlist = frozenset(allowed_executables or DEFAULT_EXECUTABLE_ALLOWLIST)
    executable = _validate_executable(plan.command[0], allowlist)
    command = (executable, *_validate_static_arguments(plan.command[1:]))

    try:
        completed = subprocess.run(
            command,
            cwd=repo,
            input=plan.task_markdown,
            text=True,
            capture_output=True,
            shell=False,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        raise DelegationError(f"Approved executable was not found: {executable}") from exc
    except subprocess.TimeoutExpired as exc:
        raise DelegationError(f"Delegated CLI exceeded the {timeout_seconds}s timeout.") from exc
    except OSError as exc:
        raise DelegationError(f"Could not start delegated CLI: {exc}") from exc

    return DelegationResult(
        plan=plan,
        return_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
