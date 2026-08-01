from __future__ import annotations

import json
import sys
from pathlib import Path

from src import desktop_backend
from src.main import _record_repair_worker_crash, _repair_worker_argv


def test_desktop_backend_defaults_to_loopback_service(monkeypatch) -> None:
    observed: list[str] = []
    monkeypatch.setattr(sys, "argv", ["github-engineer-backend"])
    monkeypatch.setattr(
        desktop_backend,
        "main",
        lambda: observed.extend(sys.argv[1:]) or 0,
    )

    assert desktop_backend.run() == 0
    assert observed == ["--serve", "--serve-host", "127.0.0.1"]


def test_desktop_backend_preserves_explicit_arguments(monkeypatch) -> None:
    observed: list[str] = []
    monkeypatch.setattr(
        sys,
        "argv",
        ["github-engineer-backend", "--serve", "--config", "/tmp/ghe.yml"],
    )
    monkeypatch.setattr(
        desktop_backend,
        "main",
        lambda: observed.extend(sys.argv[1:]) or 0,
    )

    assert desktop_backend.run() == 0
    assert observed == ["--serve", "--config", "/tmp/ghe.yml"]


def test_desktop_backend_treats_interrupt_as_clean_shutdown(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["github-engineer-backend", "--serve"])

    def interrupted() -> int:
        raise KeyboardInterrupt

    monkeypatch.setattr(desktop_backend, "main", interrupted)
    assert desktop_backend.run() == 0


def test_desktop_backend_dispatches_private_repair_worker(monkeypatch) -> None:
    observed: list[str] = []
    monkeypatch.setattr(
        sys,
        "argv",
        ["github-engineer-backend", "--repair-worker", "job.json", "start"],
    )
    monkeypatch.setattr(
        "src.repair_worker.main",
        lambda: observed.extend(sys.argv[1:]) or 0,
    )

    assert desktop_backend.run() == 0
    assert observed == ["job.json", "start"]


def test_frozen_server_relaunches_worker_through_bundle(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", "/Applications/GitHub Engineer")
    job = tmp_path / "job.json"

    assert _repair_worker_argv(job, "start", "/tmp/config.yml") == [
        "/Applications/GitHub Engineer",
        "--repair-worker",
        str(job.resolve()),
        "start",
        "--config",
        "/tmp/config.yml",
    ]


def test_crashed_worker_cannot_leave_task_queued_forever(tmp_path) -> None:
    job = tmp_path / "job.json"
    job.write_text('{"id":"abc","status":"queued"}', encoding="utf-8")

    _record_repair_worker_crash(job, 2)

    payload = json.loads(job.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["message"] == "Repair worker exited unexpectedly (code 2)."
    assert payload["updated_at"]


def test_run_action_verifies_the_packaged_app_without_accepting_a_stale_port() -> None:
    script = (
        Path(__file__).resolve().parents[1] / "script" / "build_and_run.sh"
    ).read_text(encoding="utf-8")

    assert 'npm run desktop:build >"$LOG_FILE" 2>&1' in script
    assert '/usr/bin/open -na "$APP_BUNDLE"' in script
    assert "Packaged backend health check passed after the stability window" in script
    assert "Port 8765 is already used by an unrelated process" in script
    assert "Refusing to report a stale service as this build" in script
    assert "nohup npm run desktop" not in script
