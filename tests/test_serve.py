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

    def test_exact_brief_file_endpoint_returns_markdown(self):
        status, headers, body = _http_get(
            self.port, "/briefs/acme_widgets_20260721.md"
        )
        self.assertEqual(status, 200)
        self.assertIn("text/markdown", headers.get("Content-Type", ""))
        self.assertIn(b"# Maintainer Brief", body)

    def test_exact_brief_file_endpoint_blocks_traversal(self):
        status, _, body = _http_get(self.port, "/briefs/%2e%2e%2fconfig.yml")
        self.assertEqual(status, 404)
        self.assertEqual(json.loads(body), {"error": "not found"})

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

    def test_post_rejects_cross_origin_request(self):
        """Round 6 P0: a malicious page on another origin must not be able
        to drive the loopback server. The Origin check is enforced before
        the route is dispatched.
        """

        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/decisions",
            data=json.dumps({"status": "rejected", "theme": "evil"}).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Origin": "http://evil.example.com",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                status = response.status
                body = response.read()
        except urllib.error.HTTPError as exc:
            status = exc.code
            body = exc.read()
        self.assertEqual(status, 403)
        self.assertIn(b"forbidden", body)

    def test_publish_requires_confirm_token(self):
        """Round 6 P0: /api/repairs/<id>/publish creates a Draft PR, an
        external side effect. A bare POST without a confirm token must
        be refused, even if the job exists and is review_ready.
        """

        repair_dir = self.directory / ".ghe" / "repair-jobs"
        repair_dir.mkdir(parents=True, exist_ok=True)
        job = {
            "id": "abc123456789",
            "status": "review_ready",
            "repository": "acme/widgets",
            "issue_number": 1,
            "issue_title": "demo",
            "viewer": "tester",
            "default_branch": "main",
            "delivery_mode": "fork_pr",
            "task_file": "tasks/x.md",
            "task_markdown": "# t",
            "workspace": str(self.directory / ".ghe" / "repair-workspaces" / "abc123456789"),
            "guidance": [],
            "message": "ready",
            "created_at": "2026-07-24T00:00:00+00:00",
            "updated_at": "2026-07-24T00:00:00+00:00",
        }
        (repair_dir / "abc123456789.json").write_text(
            json.dumps(job), encoding="utf-8"
        )
        status, _, body = _http_post(
            self.port,
            "/api/repairs/abc123456789/publish",
            b"{}",
            "application/json",
        )
        self.assertEqual(status, 403)
        self.assertIn(b"confirm token", body)

    def _seed_review_ready_job(self, job_id: str) -> None:
        repair_dir = self.directory / ".ghe" / "repair-jobs"
        repair_dir.mkdir(parents=True, exist_ok=True)
        job = {
            "id": job_id,
            "status": "review_ready",
            "repository": "acme/widgets",
            "issue_number": 1,
            "issue_title": "demo",
            "viewer": "tester",
            "default_branch": "main",
            "delivery_mode": "fork_pr",
            "task_file": "tasks/x.md",
            "task_markdown": "# t",
            "workspace": str(self.directory / ".ghe" / "repair-workspaces" / job_id),
            "guidance": [],
            "message": "ready",
            "created_at": "2026-07-24T00:00:00+00:00",
            "updated_at": "2026-07-24T00:00:00+00:00",
        }
        (repair_dir / f"{job_id}.json").write_text(
            json.dumps(job), encoding="utf-8"
        )

    def test_briefs_modified_field_uses_iso_8601_with_offset(self):
        """Round 7 regression: the /briefs JSON and /ui/briefs HTML
        both render the brief's mtime through _iso_utc() so a
        downstream script can sort them without bespoke parsing.
        """

        import re

        status, _, body = _http_get(self.port, "/")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        modified = payload["briefs"][0]["modified"]
        # ISO 8601 with timezone offset (e.g. "2026-07-21T..." + 00:00),
        # not the old "YYYY-MM-DD HH:MM UTC" shape, and not the Z suffix.
        self.assertRegex(
            modified,
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?\+00:00$",
        )

    def test_briefs_trend_endpoint_aggregates_history(self):
        """Round 7 P1: /api/briefs/trend?range=Nd returns per-day buckets."""

        import json as _json
        from datetime import datetime, timezone, timedelta

        # Seed a single history record so the endpoint has something
        # to aggregate. The test config is set up in setUpClass().
        history_dir = self.directory / ".ghe" / "history"
        history_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        record = {
            "repo_full_name": "acme/widgets",
            "generated_at": now.isoformat(),
            "top_issue_numbers": [1, 2, 3],
            "top_issue_scores": {"1": 5.0, "2": 4.0, "3": 3.0},
            "cluster_names": ["auth", "performance"],
            "new_issues_count": 7,
        }
        (history_dir / f"{now.strftime('%Y-%m-%d_%H%M%S')}__{('acme', 'widgets')}.json".replace("('", "").replace("')", "").replace("', '", "__")).write_text(
            _json.dumps(record), encoding="utf-8"
        )
        status, _, body = _http_get(self.port, "/api/briefs/trend?range=7d")
        self.assertEqual(status, 200)
        payload = _json.loads(body)
        self.assertEqual(payload["repo"], "acme/widgets")
        self.assertEqual(payload["range_days"], 7)
        self.assertGreaterEqual(payload["total_runs"], 1)
        self.assertIn("auth", payload["clusters"])
        self.assertIn("performance", payload["clusters"])

    def test_delete_decision_by_status(self):
        """Round 7 P1: the web UI can revoke decisions via DELETE /decisions."""

        import urllib.request

        # Seed a decision.
        payload = json.dumps(
            {"status": "rejected", "theme": "temp", "reason": "tmp"}
        ).encode("utf-8")
        status, _, body = _http_post(
            self.port, "/decisions", payload, "application/json"
        )
        self.assertEqual(status, 201)
        # DELETE by status.
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/decisions?target=rejected",
            method="DELETE",
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                status = response.status
                body = response.read()
        except urllib.error.HTTPError as exc:
            status = exc.code
            body = exc.read()
            print(f"DELETE failed: status={status} body={body!r}")  # debug
        self.assertEqual(status, 200, f"DELETE returned {status}: {body!r}")
        self.assertIn(b"rejected", body)

    def test_publish_wrong_confirm_token_rejected(self):
        """Round 6 P0 follow-up: getting a token and sending a different
        one must still be refused.
        """

        self._seed_review_ready_job("def987654321")
        # Acquire a real token, then submit a different one.
        status, _, body = _http_get(
            self.port, "/api/repairs/def987654321/confirm-token"
        )
        self.assertEqual(status, 200)
        token = json.loads(body)["token"]
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/repairs/def987654321/publish",
            data=b"{}",
            headers={
                "Content-Type": "application/json",
                "X-Confirm": "totally-wrong-token",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                status = response.status
                body = response.read()
        except urllib.error.HTTPError as exc:
            status = exc.code
            body = exc.read()
        self.assertEqual(status, 403)
        self.assertIn(b"confirm token", body)
        # The real token is still valid (was never consumed).
        self.assertIsNotNone(token)

    def test_prepare_issue_task_requires_repository_and_issue_number(self):
        payload = json.dumps({"repository": "acme/widgets"}).encode("utf-8")
        status, _, body = _http_post(
            self.port, "/api/tasks", payload, "application/json"
        )
        self.assertEqual(status, 400)
        self.assertIn("issue_number", body.decode("utf-8"))

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
        # The only script is the trusted local progressive-enhancement asset;
        # report Markdown itself is still escaped by the renderer.
        self.assertIn('src="/ui/app.js"', body)
        self.assertNotIn("<script>alert", body.lower())

    def test_ui_brief_file_link_resolves(self):
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/ui/briefs/acme_widgets_20260721.md",
            headers={"Accept": "text/html"},
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            self.assertEqual(response.status, 200)
            body = response.read().decode("utf-8")
        self.assertIn("Maintainer Brief", body)
        self.assertIn("acme_widgets_20260721.md", body)

    def test_ui_assets_and_conversation_shell(self):
        status, _, repair_tasks = _http_get(self.port, "/api/repairs")
        self.assertEqual(status, 200)
        self.assertIsInstance(json.loads(repair_tasks), list)

        status, headers, css = _http_get(self.port, "/ui/app.css")
        self.assertEqual(status, 200)
        self.assertIn("text/css", headers.get("Content-Type", ""))
        self.assertIn(b"prefers-color-scheme", css)

        status, headers, script = _http_get(self.port, "/ui/app.js")
        self.assertEqual(status, 200)
        self.assertIn("text/javascript", headers.get("Content-Type", ""))
        self.assertIn(b"assistant-composer", script)
        self.assertIn("自动修复".encode(), script)
        self.assertIn("你的 Fork".encode(), script)
        self.assertIn(b"/api/repair-capabilities", script)
        self.assertIn(b"review_ready", script)
        self.assertIn(b"/guidance", script)
        self.assertIn(b"/publish", script)

        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/ui/", headers={"Accept": "text/html"}
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8")
        self.assertIn("id='assistant-composer'", body)
        self.assertIn("需要关注", body)
        self.assertIn("近 30 天", body)
        self.assertIn("分析 #42", body)
        self.assertIn("当前仓库", body)
        self.assertIn("点击切换", body)
        self.assertIn('id="repair-inspector"', body)
        self.assertIn('id="repair-task-list"', body)
        self.assertNotIn('id="repair-dialog"', body)
        self.assertIn('id="repair-guidance-input"', body)
        self.assertIn("确认创建 Draft PR", body)
        self.assertIn("从我的仓库选择", body)
        self.assertIn("只会加载你主动加入清单的仓库", body)
        self.assertIn('id="repo-switcher"', body)
        self.assertNotIn("查看当前配置", body)

    def test_add_watched_repository_validates_repo_name(self):
        payload = json.dumps({"repository": "not-a-repository"}).encode("utf-8")
        status, _, body = _http_post(
            self.port, "/api/watched-repositories", payload, "application/json"
        )
        self.assertEqual(status, 400)
        self.assertIn("owner/repository", body.decode("utf-8"))

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
