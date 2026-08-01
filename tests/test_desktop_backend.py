from __future__ import annotations

import json
import sys

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
