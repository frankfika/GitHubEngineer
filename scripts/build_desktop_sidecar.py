"""Build the Python service as the target-specific Tauri sidecar binary."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def target_triple() -> str:
    configured = os.environ.get("TAURI_ENV_TARGET_TRIPLE", "").strip()
    if configured:
        return configured
    result = subprocess.run(
        ["rustc", "-vV"],
        check=True,
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        if line.startswith("host: "):
            return line.removeprefix("host: ").strip()
    raise RuntimeError("rustc did not report a host target triple")


def main() -> int:
    triple = target_triple()
    suffix = ".exe" if "windows" in triple else ""
    binary_name = f"github-engineer-backend-{triple}{suffix}"
    binary_dir = ROOT / "src-tauri" / "binaries"
    work_dir = ROOT / "build" / "desktop-sidecar"
    binary_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    produced = binary_dir / binary_name
    inputs = [
        ROOT / "pyproject.toml",
        *sorted((ROOT / "src").glob("*.py")),
    ]
    if produced.is_file() and produced.stat().st_mtime >= max(
        path.stat().st_mtime for path in inputs
    ):
        print(produced)
        return 0
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--name",
        binary_name.removesuffix(suffix),
        "--distpath",
        str(binary_dir),
        "--workpath",
        str(work_dir / "work"),
        "--specpath",
        str(work_dir),
        str(ROOT / "src" / "desktop_backend.py"),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    if not produced.is_file():
        raise RuntimeError(f"PyInstaller did not create {produced}")
    print(produced)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
