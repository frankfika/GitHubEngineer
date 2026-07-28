#!/usr/bin/env python3
"""Fake LLM HTTP server for e2e tests.

Listens on 127.0.0.1:9999 (override with the PORT env var). Implements
``POST /v1/chat/completions`` and returns an OpenAI-shaped JSON response
with a fenced unified diff in ``choices[0].message.content``.

The server is deliberately tiny: stdlib only, single endpoint, no
streaming, no auth, no retries. Its job is to let the repair worker
exercise its full code path (HTTP -> diff extraction -> git apply)
without a real API key. The FakeProvider at ``src.coding_agent.py``
takes a parallel path and does not need this server, but the
end-to-end suite is closer to production when an actual HTTP call is
made.

Run standalone:

    python3 tests/mocks/fake_llm_server.py
    PORT=8080 python3 tests/mocks/fake_llm_server.py

Or from a test:

    from tests.mocks.fake_llm_server import start_server
    with start_server(port=9999) as base_url:
        ...

The two env vars the server respects:

* ``FAKE_PROVIDER_FAIL`` -- comma-separated issue numbers that should
  fail. The server returns a 200 with a no-op diff but the worker
  treats that as ``no_diff``. (We keep the 200 for HTTP-layer tests.)
* ``FAKE_LLM_QUIET`` -- silence the per-request log line.

Exit with SIGINT cleanly so tests can stop it from a thread.
"""
from __future__ import annotations

import contextlib
import json
import os
import re
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Iterator


PORT = int(os.environ.get("PORT", "9999"))


def _make_diff(prompt: str) -> str:
    """Build a tiny unified diff for ``prompt`` (which mentions an issue)."""
    m = re.search(r"Issue\s+#(\d+)", prompt or "")
    issue_number = m.group(1) if m else "default"
    return (
        f"--- a/src/fix_{issue_number}.py\n"
        f"+++ b/src/fix_{issue_number}.py\n"
        f"@@ -1,2 +1,4 @@\n"
        f" def hello():\n"
        f'-    return "hi"\n'
        f'+    """Fixed by fake LLM for issue #{issue_number}."""\n'
        f'+    return f"hi from issue {issue_number}"\n'
    )


def make_response(prompt: str) -> dict:
    """Return an OpenAI-compatible chat-completion dict for ``prompt``."""
    m = re.search(r"Issue\s+#(\d+)", prompt or "")
    issue_number = m.group(1) if m else "default"

    fail_on = {
        x.strip() for x in os.environ.get("FAKE_PROVIDER_FAIL", "").split(",") if x.strip()
    }
    if issue_number in fail_on:
        # 200 with a no-op diff so callers can assert the diff path ran
        # but the resulting patch is empty.
        return {
            "id": f"fake-{issue_number}",
            "object": "chat.completion",
            "model": "fake-model",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "```diff\n--- a/nope.py\n+++ b/nope.py\n@@ -1,1 +1,1 @@\n",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }

    diff = _make_diff(prompt)
    return {
        "id": f"fake-{issue_number}",
        "object": "chat.completion",
        "model": "fake-model",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"```diff\n{diff}\n```",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    }


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler API)
        if not self.path.endswith("/chat/completions"):
            self.send_error(404, "use POST /v1/chat/completions")
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(length) if length else b""
        prompt = ""
        try:
            data = json.loads(body)
            messages = data.get("messages") or []
            if messages and isinstance(messages, list):
                prompt = str(messages[0].get("content", ""))
        except (json.JSONDecodeError, IndexError, KeyError, TypeError):
            prompt = ""
        response = make_response(prompt)
        payload = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
        if not os.environ.get("FAKE_LLM_QUIET"):
            short = prompt[:80].replace("\n", " ")
            sys.stderr.write(f"[fake_llm] POST {self.path} prompt={short!r}\n")
            sys.stderr.flush()

    def log_message(self, format, *args) -> None:  # noqa: A002 (stdlib name)
        # Silence the default per-request log; we emit our own above.
        return


def _free_port() -> int:
    """Ask the OS for a free TCP port (used by tests that don't bind 9999)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def start_server(port: int | None = None) -> Iterator[str]:
    """Context manager that boots the server on a background thread.

    Yields the base URL (``http://127.0.0.1:<port>``). The server is
    shut down on context exit, even on exceptions. Used by tests that
    want an isolated server without hard-coding 9999.
    """
    chosen = port or _free_port()
    httpd = HTTPServer(("127.0.0.1", chosen), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, name="fake-llm", daemon=True)
    thread.start()
    try:
        # Give the server a beat to start listening.
        import time

        time.sleep(0.05)
        yield f"http://127.0.0.1:{chosen}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)


def main() -> int:
    server = HTTPServer(("127.0.0.1", PORT), _Handler)
    print(
        f"fake LLM listening on http://127.0.0.1:{PORT} "
        f"(pid={os.getpid()}, fail_on={os.environ.get('FAKE_PROVIDER_FAIL', '')!r})",
        file=sys.stderr,
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
