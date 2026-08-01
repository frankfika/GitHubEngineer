"""Executable entry point bundled beside the Tauri desktop application."""

from __future__ import annotations

import sys

from src.main import main


def run() -> int:
    """Start the loopback service used by the packaged desktop WebView."""

    if sys.argv[1:2] == ["--repair-worker"]:
        from src.repair_worker import main as repair_worker_main

        sys.argv = [sys.argv[0], *sys.argv[2:]]
        return repair_worker_main()
    if len(sys.argv) == 1:
        sys.argv.extend(["--serve", "--serve-host", "127.0.0.1"])
    try:
        return main()
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(run())
