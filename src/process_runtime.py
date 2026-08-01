"""Runtime helpers shared by every subprocess boundary.

Both the delegation adapter and the background repair worker spawn
subprocesses that need a controlled environment. Centralising the
helpers here keeps the security policy in one place:

- ``safe_subprocess_env(purpose)`` builds a copy of ``os.environ`` with
  the credentials that the child process must not see stripped out.
  The parent process keeps the original environment; the child gets a
  narrowed view. A coding agent that can read the parent's
  ``LLM_API_KEY`` is a privilege escalation, not a feature.
- ``atomic_write_json(path, data)`` writes a JSON file via a
  ``.tmp`` + ``os.replace`` dance so a worker that is killed mid-write
  cannot leave a half-formed job file behind for the next process to
  choke on.

The module has no third-party dependencies so it is safe to import
from the leaf ``repair_worker`` module (which runs as a subprocess
on its own and must not pull in the entire app).
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

#: Tokens that must never leak to a child process.  Listed by lower-cased
#: variable name.  Both the GitHub token (``GITHUB_TOKEN`` /
#: ``GH_TOKEN``) and the LLM provider key (any ``*_API_KEY``) qualify.
_SENSITIVE_KEYS = {
    "github_token",
    "gh_token",
    "openai_api_key",
    "llm_api_key",
    "anthropic_api_key",
    "ghe_github_token",
    "ghe_openai_api_key",
    "ghe_anthropic_api_key",
    "ghe_llm_api_key",
}


def find_desktop_executable(name: str) -> str | None:
    """Find a CLI from either a shell or a macOS GUI-launched process.

    Finder/Tauri/Electron applications commonly inherit the minimal macOS
    launchd PATH (``/usr/bin:/bin:/usr/sbin:/sbin``). Homebrew and user-local
    commands are therefore invisible even though they work in Terminal.
    Resolve a small set of conventional install locations without invoking a
    login shell or evaluating user-controlled shell startup files.
    """

    discovered = shutil.which(name)
    if discovered:
        return discovered
    home = Path.home()
    candidates = (
        Path("/opt/homebrew/bin") / name,
        Path("/usr/local/bin") / name,
        home / ".local" / "bin" / name,
        home / ".claude" / "local" / name,
        home / "bin" / name,
    )
    return next(
        (
            str(candidate)
            for candidate in candidates
            if candidate.is_file() and os.access(candidate, os.X_OK)
        ),
        None,
    )


def safe_subprocess_env(purpose: str) -> dict[str, str]:
    """Return a copy of ``os.environ`` with secrets stripped.

    ``purpose`` selects the policy:

    - ``"delegate"`` (default): keep only the variables a coding agent
      needs to run (``PATH``, ``HOME``, ``LANG``, ``LC_ALL``, ``TMPDIR``,
      ``USERPROFILE`` on Windows). Drop every token-shaped variable.
    - ``"gh"``: same as ``"delegate"`` but keep ``GITHUB_TOKEN`` /
      ``GH_TOKEN`` so the ``gh`` CLI can authenticate.
    - ``"worker"``: keep the variables the claude / codex worker needs
      (the model provider key plus ``PATH`` / ``HOME`` / language vars)
      but strip GitHub tokens because the worker should not push on
      its own — push is the responsibility of the explicit publish
      step, which uses the ``gh`` policy.
    - ``"repair-worker"``: parent environment for the trusted repair
      coordinator. Keep both model and GitHub credentials so it can create
      purpose-scoped child environments; coding-agent children still receive
      the narrower ``worker`` policy and never inherit GitHub credentials.

    The function is deliberately conservative: when in doubt we strip
    the variable.  Coding agents have run for years without any of
    these variables set; the narrowest environment that still works
    is the safest.

    The keep rules use **explicit name lists** rather than substring
    matches like ``"API_KEY" in name``.  A substring match would let
    a custom ``GHE_OPENAI_API_KEY`` leak through, defeating the
    deny-list check.  Adding a new well-known key means adding it
    to ``_KNOWN_MODEL_KEYS`` or ``_KNOWN_GH_TOKENS`` here.
    """

    allowed_always = {
        "PATH",
        "HOME",
        "USERPROFILE",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "TMPDIR",
        "TMP",
        "TEMP",
        "XDG_CONFIG_HOME",
        "XDG_CACHE_HOME",
        "XDG_DATA_HOME",
        # Preserve standard network routing. Desktop-launched processes often
        # require these to reach the model service; dropping them makes the
        # CLI appear authenticated but hang until timeout.
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "NO_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
        "no_proxy",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "REQUESTS_CA_BUNDLE",
        "CURL_CA_BUNDLE",
        "NO_COLOR",
    }
    _KNOWN_GH_TOKENS = {"GITHUB_TOKEN", "GH_TOKEN"}
    _KNOWN_MODEL_KEYS = {"ANTHROPIC_API_KEY", "OPENAI_API_KEY", "LLM_API_KEY"}
    purpose_normalized = purpose.lower().strip()
    keep_tokens = purpose_normalized in {"gh", "repair-worker"}
    keep_model_key = purpose_normalized in {"worker", "repair-worker"}
    safe: dict[str, str] = {}
    for key, value in os.environ.items():
        upper = key.upper()
        lower = key.lower()
        if upper in allowed_always:
            safe[key] = value
            continue
        if keep_tokens and upper in _KNOWN_GH_TOKENS:
            safe[key] = value
            continue
        if keep_model_key and upper in _KNOWN_MODEL_KEYS:
            safe[key] = value
            continue
        if lower in _SENSITIVE_KEYS:
            # Belt and braces: never let any name in the deny list pass.
            continue
        # Other variables (e.g. CI-specific flags, custom agent config)
        # are dropped by default. Callers that need them must add them
        # to ``allowed_always`` explicitly.
    return safe


def atomic_write_json(path: os.PathLike[str] | str, data: dict[str, Any]) -> None:
    """Write ``data`` to ``path`` atomically.

    Writes to a sibling ``.tmp`` file first, then ``os.replace`` swaps
    it into place. ``os.replace`` is atomic on POSIX and on Windows
    (when the destination is on the same filesystem), so a reader
    always sees either the previous version or the new version, never
    a half-written one.
    """

    target = os.fspath(path)
    parent = os.path.dirname(os.path.abspath(target))
    os.makedirs(parent, exist_ok=True)
    tmp = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{os.path.basename(target)}.",
            suffix=".tmp",
            dir=parent,
            delete=False,
        ) as handle:
            tmp = handle.name
            handle.write(json.dumps(data, ensure_ascii=False, indent=2))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, target)
        tmp = ""
    finally:
        if tmp:
            try:
                os.unlink(tmp)
            except FileNotFoundError:
                pass
