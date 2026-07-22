"""End-to-end tests for the ``ghe --serve`` local web service.

The server is started in a subprocess so each test can kill it
independently. We bind to 127.0.0.1 on an ephemeral port and use the
stdlib ``urllib`` client to hit each route.
"""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from contextlib import closing
from pathlib import Path

import yaml


def _free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_server(port: int, host: str = "127.0.0.1", deadline: float = 10.0) -> None:
    started = time.monotonic()
    while time.monotonic() - started < deadline:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(0.2)
            try:
                sock.connect((host, port))
            except OSError:
                time.sleep(0.1)
                continue
            return
    raise RuntimeError(f"server on {host}:{port} did not start within {deadline}s")


def _http_get(port: int, path: str, host: str = "127.0.0.1") -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(f"http://{host}:{port}{path}")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read()


def _http_post(
    port: int, path: str, body: bytes, content_type: str, host: str = "127.0.0.1"
) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(
        f"http://{host}:{port}{path}",
        data=body,
        headers={"Content-Type": content_type},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read()


class ServeSubcommandTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._temp_dir = tempfile.TemporaryDirectory()
        cls.directory = Path(cls._temp_dir.name)
        # Write a self-contained config so the server can read output_dir.
        (cls.directory / "reports").mkdir()
        (cls.directory / "reports" / "acme_widgets_20260721.md").write_text(
            "# Maintainer Brief\n\nbody", encoding="utf-8"
        )
        (cls.directory / ".ghe" / "memory").mkdir(parents=True)
        (cls.directory / ".ghe" / "memory" / "decisions.yml").write_text(
            "version: 1\ndecisions: []\n", encoding="utf-8"
        )
        cls.config_path = cls.directory / "config.yml"
        cls.config_path.write_text(
            yaml.safe_dump(
                {
                    "repo": {"full_name": "acme/widgets"},
                    "github": {"token": "test"},
                    "model": {"api_key": "k", "model_name": "gpt-x"},
                    "output": {"format": "markdown", "output_dir": str(cls.directory / "reports")},
                    "analysis": {"lookback_days": 7, "max_issues_for_llm": 10, "top_n": 3},
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        cls.port = _free_port()
        cls._process: subprocess.Popen | None = None

    @classmethod
    def tearDownClass(cls):
        if cls._process is not None and cls._process.poll() is None:
            cls._process.send_signal(signal.SIGINT)
            try:
                cls._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls._process.kill()
                cls._process.wait()
        cls._temp_dir.cleanup()

    def setUp(self):
        # Each test starts a fresh server so the in-process decision
        # memory changes from POST /decisions do not leak across tests.
        env = os.environ.copy()
        env["GHE_SERVE_PORT"] = str(self.port)
        env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent)
        self._process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "src.main",
                "--config",
                str(self.config_path),
                "--serve",
                "--serve-host",
                "127.0.0.1",
            ],
            cwd=str(self.directory),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _wait_for_server(self.port)

    def tearDown(self):
        if self._process is not None and self._process.poll() is None:
            self._process.send_signal(signal.SIGINT)
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()
            self._process = None

    def test_healthz_returns_ok(self):
        status, headers, body = _http_get(self.port, "/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("Content-Type"), "application/json")
        payload = json.loads(body)
        self.assertEqual(payload["status"], "ok")

    def test_index_lists_briefs(self):
        status, _, body = _http_get(self.port, "/")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["brief_count"], 1)
        self.assertEqual(payload["briefs"][0]["file"], "acme_widgets_20260721.md")

    def test_brief_endpoint_returns_markdown(self):
        status, headers, body = _http_get(self.port, "/brief/acme/widgets")
        self.assertEqual(status, 200)
        self.assertIn("text/markdown", headers.get("Content-Type", ""))
        self.assertIn(b"# Maintainer Brief", body)

    def test_decisions_endpoint_returns_empty_array(self):
        status, _, body = _http_get(self.port, "/decisions")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), [])

    def test_post_decisions_persists_to_memory(self):
        payload = json.dumps(
            {
                "status": "rejected",
                "theme": "OAuth rework",
                "reason": "Out of scope this quarter",
            }
        ).encode("utf-8")
        status, _, body = _http_post(
            self.port, "/decisions", payload, "application/json"
        )
        self.assertEqual(status, 201)
        persisted = json.loads(body)
        self.assertEqual(persisted["status"], "rejected")
        self.assertEqual(persisted["themes"], ["OAuth rework"])
        memory_text = (self.directory / ".ghe" / "memory" / "decisions.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("OAuth rework", memory_text)

    def test_unknown_route_returns_404(self):
        status, _, body = _http_get(self.port, "/nope")
        self.assertEqual(status, 404)
        self.assertEqual(json.loads(body), {"error": "not found"})

    def test_post_decisions_rejects_invalid_status(self):
        payload = json.dumps({"status": "maybe", "theme": "anything"}).encode("utf-8")
        status, _, body = _http_post(
            self.port, "/decisions", payload, "application/json"
        )
        self.assertEqual(status, 400)
        self.assertIn("status", body.decode("utf-8"))

    def test_ui_root_renders_html(self):
        import urllib.request
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/ui/", headers={"Accept": "text/html"}
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            self.assertEqual(response.status, 200)
            self.assertIn("text/html", response.headers.get("Content-Type", ""))
            body = response.read().decode("utf-8")
        self.assertIn("<h1>GitHub Engineer</h1>", body)
        self.assertIn("acme_widgets_20260721.md", body)

    def test_ui_brief_renders_markdown_as_html(self):
        import urllib.request
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/ui/brief/acme/widgets",
            headers={"Accept": "text/html"},
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            self.assertEqual(response.status, 200)
            body = response.read().decode("utf-8")
        self.assertIn("<h1>", body)
        self.assertIn("Maintainer Brief", body)
        # Inline rendering escapes user text and turns links into anchors.
        self.assertNotIn("<script", body.lower())

    def test_ui_decisions_renders_html(self):
        import urllib.request
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/ui/decisions",
            headers={"Accept": "text/html"},
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            self.assertEqual(response.status, 200)
            body = response.read().decode("utf-8")
        self.assertIn("Decision memory", body)
        self.assertIn("badge-rejected", body)

    def test_index_json_is_default_for_curl_like_clients(self):
        # A curl that does not set Accept: text/html must get JSON.
        import urllib.request
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}/")
        with urllib.request.urlopen(request, timeout=5) as response:
            self.assertEqual(response.status, 200)
            self.assertIn("application/json", response.headers.get("Content-Type", ""))
            body = response.read().decode("utf-8")
        # JSON content is a parseable envelope, not HTML.
        import json as _json
        payload = _json.loads(body)
        self.assertIn("service", payload)


if __name__ == "__main__":
    unittest.main()
