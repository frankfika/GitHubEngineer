from __future__ import annotations

import sys

from src import desktop_backend


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
