"""End-to-end tests for the ``ghe --serve`` local web service.

The server is started in a subprocess so each test can kill it
independently. We bind to 127.0.0.1 on an ephemeral port and use the
stdlib ``urllib`` client to hit each route.
"""

from __future__ import annotations

import json
import hashlib
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
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from src.main import resolve_workspace_root
from src.process_runtime import atomic_write_json


def _free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _server_env(port: int) -> dict[str, str]:
    env = os.environ.copy()
    env["GHE_SERVE_PORT"] = str(port)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent)
    # pytest-cov auto-instruments subprocesses through these variables.
    # GitHub's macOS runners take tens of seconds to import the application
    # under child-process tracing; Ubuntu still records that coverage.
    if sys.platform == "darwin" and env.get("CI"):
        for name in (
            "COV_CORE_SOURCE",
            "COV_CORE_CONFIG",
            "COV_CORE_DATAFILE",
            "COV_CORE_BRANCH",
        ):
            env.pop(name, None)
    return env


def _wait_for_server(port: int, host: str = "127.0.0.1", deadline: float = 60.0) -> None:
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
        cls._server_log = (cls.directory / "server.log").open("w+b")
        cls._process: subprocess.Popen | None = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "src.main",
                "--config",
                str(cls.config_path),
                "--serve",
                "--serve-host",
                "127.0.0.1",
            ],
            cwd=str(cls.directory),
            env=_server_env(cls.port),
            stdout=cls._server_log,
            stderr=subprocess.STDOUT,
        )
        try:
            _wait_for_server(cls.port)
        except Exception:
            cls._process.kill()
            cls._process.wait(timeout=5)
            cls._process = None
            cls._server_log.flush()
            cls._server_log.seek(0)
            output = cls._server_log.read()
            cls._server_log.close()
            cls._temp_dir.cleanup()
            raise RuntimeError(
                "test server failed to start:\n"
                + output.decode("utf-8", errors="replace")[-2000:]
            )

    @classmethod
    def tearDownClass(cls):
        if cls._process is not None and cls._process.poll() is None:
            cls._process.send_signal(signal.SIGINT)
            try:
                cls._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls._process.kill()
                cls._process.wait()
        cls._server_log.close()
        cls._temp_dir.cleanup()

    def test_healthz_returns_ok(self):
        status, headers, body = _http_get(self.port, "/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("Content-Type"), "application/json")
        payload = json.loads(body)
        self.assertEqual(payload["status"], "ok")

    def test_serve_starts_without_a_configured_repository(self):
        port = _free_port()
        config_path = self.directory / "onboarding-config.yml"
        config_path.write_text(
            yaml.safe_dump(
                {
                    "github": {"token": ""},
                    "model": {"api_key": "", "model_name": ""},
                    "output": {
                        "format": "markdown",
                        "output_dir": str(self.directory / "empty-reports"),
                    },
                }
            ),
            encoding="utf-8",
        )
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "src.main",
                "--config",
                str(config_path),
                "--serve",
                "--serve-host",
                "127.0.0.1",
            ],
            cwd=str(self.directory),
            env=_server_env(port),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            _wait_for_server(port)
            status, _, body = _http_get(port, "/api/repositories")
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["repositories"], [])
        finally:
            process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

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
            "coding_agent_provider": "real_provider",
            "verification": {"status": "passed", "commands": []},
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
            "coding_agent_provider": "real_provider",
            "verification": {"status": "passed", "commands": []},
            "message": "ready",
            "created_at": "2026-07-24T00:00:00+00:00",
            "updated_at": "2026-07-24T00:00:00+00:00",
        }
        (repair_dir / f"{job_id}.json").write_text(
            json.dumps(job), encoding="utf-8"
        )

    def _seed_review_workspace(self, job_id: str, file_count: int = 3) -> Path:
        self._seed_review_ready_job(job_id)
        workspace = self.directory / ".ghe" / "repair-workspaces" / job_id
        workspace.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=workspace,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=workspace,
            check=True,
        )
        for index in range(file_count):
            (workspace / f"file{index}.txt").write_text("before\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=workspace, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=workspace, check=True)
        for index in range(file_count):
            (workspace / f"file{index}.txt").write_text("after\n", encoding="utf-8")
        return workspace

    def test_demo_job_cannot_obtain_publish_confirmation(self):
        job_id = "demofailclosed"
        self._seed_review_ready_job(job_id)
        job_path = self.directory / ".ghe" / "repair-jobs" / f"{job_id}.json"
        job = json.loads(job_path.read_text(encoding="utf-8"))
        job["is_demo"] = True
        job["coding_agent_provider"] = "fake"
        job["verification"] = {"status": "unverified", "commands": []}
        job_path.write_text(json.dumps(job), encoding="utf-8")

        status, _, body = _http_get(
            self.port, f"/api/repairs/{job_id}/confirm-token"
        )

        self.assertEqual(status, 409)
        self.assertIn("禁止发布".encode(), body)

    def test_unverified_job_cannot_obtain_publish_confirmation(self):
        job_id = "unverifiedclosed"
        self._seed_review_ready_job(job_id)
        job_path = self.directory / ".ghe" / "repair-jobs" / f"{job_id}.json"
        job = json.loads(job_path.read_text(encoding="utf-8"))
        job["verification"] = {
            "status": "unverified",
            "reason": "sandbox_unavailable",
            "commands": [],
        }
        job_path.write_text(json.dumps(job), encoding="utf-8")

        status, _, body = _http_get(
            self.port, f"/api/repairs/{job_id}/confirm-token"
        )

        self.assertEqual(status, 409)
        self.assertIn("验证".encode(), body)

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

    def test_publish_with_valid_token_rejects_incomplete_review(self):
        """The API must enforce review completeness even if the UI is bypassed."""

        job_id = "reviewpending1"
        self._seed_review_ready_job(job_id)
        status, _, body = _http_get(
            self.port, f"/api/repairs/{job_id}/confirm-token"
        )
        self.assertEqual(status, 200)
        token = json.loads(body)["token"]
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/repairs/{job_id}/publish",
            data=b"{}",
            headers={"Content-Type": "application/json", "X-Confirm": token},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                status = response.status
                body = response.read()
        except urllib.error.HTTPError as exc:
            status = exc.code
            body = exc.read()
        self.assertEqual(status, 409)
        self.assertIn("没有可审核".encode(), body)
        persisted = json.loads(
            (
                self.directory / ".ghe" / "repair-jobs" / f"{job_id}.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(persisted["status"], "review_ready")

    def test_repair_log_endpoint_returns_job_scoped_plaintext(self):
        job_id = "logjob123456"
        self._seed_review_ready_job(job_id)
        log_path = self.directory / ".ghe" / "repair-jobs" / f"{job_id}.log"
        log_path.write_text("cloning repository\nrunning tests: ok\n", encoding="utf-8")

        status, headers, body = _http_get(
            self.port, f"/api/repairs/{job_id}/log"
        )

        self.assertEqual(status, 200)
        self.assertIn("text/plain", headers.get("Content-Type", ""))
        self.assertEqual(body, b"cloning repository\nrunning tests: ok\n")

    def test_repair_log_endpoint_is_empty_while_worker_has_not_started(self):
        job_id = "emptylog1234"
        self._seed_review_ready_job(job_id)

        status, headers, body = _http_get(
            self.port, f"/api/repairs/{job_id}/log"
        )

        self.assertEqual(status, 200)
        self.assertIn("text/plain", headers.get("Content-Type", ""))
        self.assertEqual(body, b"")

    def test_repair_workspace_endpoint_returns_metadata_without_contents(self):
        job_id = "workspace123"
        self._seed_review_ready_job(job_id)
        workspace = (
            self.directory / ".ghe" / "repair-workspaces" / job_id
        )
        workspace.mkdir(parents=True)
        secret_file = workspace / "private.txt"
        secret_file.write_text("must not be returned", encoding="utf-8")

        status, headers, body = _http_get(
            self.port, f"/api/repairs/{job_id}/workspace"
        )

        self.assertEqual(status, 200)
        self.assertEqual(headers.get("Content-Type"), "application/json")
        payload = json.loads(body)
        self.assertEqual(payload["job_id"], job_id)
        self.assertEqual(payload["workspace"], str(workspace))
        self.assertTrue(payload["exists"])
        self.assertTrue(payload["is_directory"])
        self.assertNotIn("must not be returned", body.decode("utf-8"))

    def test_repair_subresources_require_an_existing_job(self):
        for suffix in ("log", "workspace", "confirm-token"):
            with self.subTest(suffix=suffix):
                status, _, body = _http_get(
                    self.port, f"/api/repairs/doesnotexist/{suffix}"
                )
                self.assertEqual(status, 404)
                self.assertEqual(
                    json.loads(body), {"error": "repair job not found"}
                )

    def test_repair_read_endpoints_reject_cross_origin_browser(self):
        job_id = "sameorigin123"
        self._seed_review_ready_job(job_id)
        for suffix in ("log", "workspace"):
            with self.subTest(suffix=suffix):
                request = urllib.request.Request(
                    f"http://127.0.0.1:{self.port}/api/repairs/{job_id}/{suffix}",
                    headers={"Origin": "http://evil.example.com"},
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

    def test_concurrent_hunk_decisions_are_not_lost(self):
        job_id = "parallelhunks"
        self._seed_review_workspace(job_id, file_count=4)

        def decide(index: int):
            return _http_post(
                self.port,
                f"/api/repairs/{job_id}/hunk-decision",
                json.dumps(
                    {"hunk_id": str(index), "decision": "accepted"}
                ).encode("utf-8"),
                "application/json",
            )

        with ThreadPoolExecutor(max_workers=4) as executor:
            responses = list(executor.map(decide, range(4)))
        self.assertEqual([response[0] for response in responses], [200] * 4)
        persisted = json.loads(
            (
                self.directory / ".ghe" / "repair-jobs" / f"{job_id}.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            persisted["hunk_decisions"],
            {str(index): "accepted" for index in range(4)},
        )

    def test_confirm_token_allows_only_one_concurrent_publish_transition(self):
        job_id = "publishonce1"
        workspace = self._seed_review_workspace(job_id, file_count=1)
        diff_text = subprocess.run(
            [
                "git",
                "diff",
                "--binary",
                "--full-index",
                "--no-color",
                "--no-ext-diff",
            ],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        job_path = self.directory / ".ghe" / "repair-jobs" / f"{job_id}.json"
        job = json.loads(job_path.read_text(encoding="utf-8"))
        job["review_diff_sha256"] = hashlib.sha256(
            diff_text.encode("utf-8")
        ).hexdigest()
        job["hunk_decisions"] = {"0": "accepted"}
        job["branch"] = "ghe/test"
        job_path.write_text(json.dumps(job), encoding="utf-8")
        status, _, body = _http_get(
            self.port, f"/api/repairs/{job_id}/confirm-token"
        )
        self.assertEqual(status, 200)
        token = json.loads(body)["token"]

        def publish(_index: int):
            request = urllib.request.Request(
                f"http://127.0.0.1:{self.port}/api/repairs/{job_id}/publish",
                data=b"{}",
                headers={
                    "Content-Type": "application/json",
                    "X-Confirm": token,
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    return response.status
            except urllib.error.HTTPError as exc:
                return exc.code

        with ThreadPoolExecutor(max_workers=2) as executor:
            statuses = sorted(executor.map(publish, range(2)))
        self.assertEqual(statuses, [202, 409])

    def test_hunk_decision_rejects_wrong_state_and_unknown_hunk(self):
        job_id = "validatehunk"
        self._seed_review_workspace(job_id)
        status, _, body = _http_post(
            self.port,
            f"/api/repairs/{job_id}/hunk-decision",
            b'{"hunk_id":"999","decision":"accepted"}',
            "application/json",
        )
        self.assertEqual(status, 400)
        self.assertIn(b"does not exist", body)
        job_path = self.directory / ".ghe" / "repair-jobs" / f"{job_id}.json"
        job = json.loads(job_path.read_text(encoding="utf-8"))
        job["status"] = "completed"
        job_path.write_text(json.dumps(job), encoding="utf-8")
        status, _, _ = _http_post(
            self.port,
            f"/api/repairs/{job_id}/hunk-decision",
            b'{"hunk_id":"0","decision":"accepted"}',
            "application/json",
        )
        self.assertEqual(status, 409)

    def test_coding_agent_configure_writes_secret_without_echoing_it(self):
        original = self.config_path.read_text(encoding="utf-8")
        secret = "sk-test-secret-never-echo"
        try:
            status, _, body = _http_post(
                self.port,
                "/api/coding-agent/configure",
                json.dumps(
                    {
                        "provider": "openai_compatible",
                        "base_url": "http://127.0.0.1:9999/v1",
                        "api_key": secret,
                        "model": "test-model",
                    }
                ).encode("utf-8"),
                "application/json",
            )
            self.assertEqual(status, 200)
            self.assertNotIn(secret.encode("utf-8"), body)
            response = json.loads(body)
            self.assertTrue(response["has_api_key"])
            persisted = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["coding_agent"]["api_key"], secret)
            self.assertEqual(self.config_path.stat().st_mode & 0o777, 0o600)
        finally:
            self.config_path.write_text(original, encoding="utf-8")

    def test_coding_agent_test_rejects_unknown_fields_without_echoing_secret(self):
        secret = "super-secret"
        status, _, body = _http_post(
            self.port,
            "/api/coding-agent/test",
            json.dumps(
                {
                    "provider": "openai_compatible",
                    "model": "m",
                    "api_key": secret,
                    "unexpected": "field",
                }
            ).encode("utf-8"),
            "application/json",
        )
        self.assertEqual(status, 400)
        self.assertNotIn(secret.encode("utf-8"), body)

    def test_post_rejects_invalid_length_oversize_and_utf8(self):
        cases = [
            (b"Content-Length: nope\r\n\r\n", 400),
            (b"Content-Length: 1048577\r\n\r\n", 413),
            (b"Content-Length: 1\r\nContent-Type: application/json\r\n\r\n\xff", 400),
        ]
        for extra_headers, expected in cases:
            with self.subTest(expected=expected, headers=extra_headers):
                with socket.create_connection(("127.0.0.1", self.port), timeout=5) as sock:
                    sock.sendall(
                        b"POST /decisions HTTP/1.1\r\n"
                        b"Host: 127.0.0.1\r\n"
                        + extra_headers
                    )
                    response = sock.recv(4096)
                self.assertIn(f" {expected} ".encode("ascii"), response)

    def test_workspace_paths_are_unique_per_job(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            first = resolve_workspace_root(
                "acme/widgets", 7, cli_override=temp_dir, job_id="jobone"
            )
            second = resolve_workspace_root(
                "acme/widgets", 7, cli_override=temp_dir, job_id="jobtwo"
            )
        self.assertNotEqual(first, second)
        self.assertEqual(first.name, "jobone")
        self.assertEqual(second.name, "jobtwo")

    def test_atomic_json_writes_use_independent_temp_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "job.json"
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [
                    executor.submit(atomic_write_json, path, {"value": value})
                    for value in range(40)
                ]
                for future in futures:
                    future.result()
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn(payload["value"], range(40))
            self.assertEqual(list(Path(temp_dir).glob("*.tmp")), [])

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
        self.assertIn('<span class="brand-title">GitHub Engineer</span>', body)
        self.assertIn("<h1 id='active-repo-heading'", body)
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
        self.assertIn("维护简报", body)
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
        self.assertIn("维护简报", body)
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
        self.assertIn("先在你的副本中准备修改".encode(), script)
        self.assertIn(b"/api/repair-capabilities", script)
        self.assertIn(b"/api/connections/status", script)
        self.assertIn(b"/api/connections/start", script)
        self.assertIn(b"review_ready", script)
        self.assertIn(b"/guidance", script)
        self.assertIn(b"/publish", script)

        status, headers, diff_client = _http_get(
            self.port, "/ui/diff-view-client.js"
        )
        self.assertEqual(status, 200)
        self.assertIn("text/javascript", headers.get("Content-Type", ""))
        self.assertIn(b'from "@codemirror/view"', diff_client)
        self.assertIn(b'from "@codemirror/state"', diff_client)

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
        self.assertIn("确认并提交修复草稿", body)
        self.assertIn("准备自动修复", body)
        self.assertIn("claude auth login", body)
        self.assertIn("从我的仓库选择", body)
        self.assertIn("连接账号", body)
        self.assertIn("查看公开仓库无需连接", body)
        self.assertIn("gh auth login --web --git-protocol https", body)
        self.assertIn('data-start-connection="account"', body)
        self.assertIn('data-start-connection="automatic_repair"', body)
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
        self.assertIn("决策记忆", body)
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
