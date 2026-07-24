#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-run}"
APP_NAME="github-engineer-desktop"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT_DIR/.codex/run"
LOG_FILE="$LOG_DIR/desktop.log"

cd "$ROOT_DIR"
mkdir -p "$LOG_DIR"

pkill -x "$APP_NAME" >/dev/null 2>&1 || true

BACKEND_PID="$(lsof -tiTCP:8765 -sTCP:LISTEN 2>/dev/null || true)"
if [[ -n "$BACKEND_PID" ]]; then
  BACKEND_COMMAND="$(ps -p "$BACKEND_PID" -o command= 2>/dev/null || true)"
  if [[ "$BACKEND_COMMAND" == *"src.main"*"--serve"* ]]; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
fi

run_desktop() {
  npm run desktop
}

case "$MODE" in
  run)
    run_desktop
    ;;
  --debug|debug)
    RUST_BACKTRACE=1 RUST_LOG=debug run_desktop
    ;;
  --logs|logs)
    run_desktop 2>&1 | tee "$LOG_FILE"
    ;;
  --telemetry|telemetry)
    run_desktop >"$LOG_FILE" 2>&1 &
    /usr/bin/log stream --info --style compact --predicate "process == \"$APP_NAME\""
    ;;
  --verify|verify)
    run_desktop >"$LOG_FILE" 2>&1 &
    LAUNCHER_PID=$!
    for _ in $(seq 1 1800); do
      if pgrep -x "$APP_NAME" >/dev/null 2>&1; then
        echo "GitHub Engineer desktop app is running."
        echo "launcher pid: $LAUNCHER_PID"
        echo "log: $LOG_FILE"
        exit 0
      fi
      if ! kill -0 "$LAUNCHER_PID" >/dev/null 2>&1; then
        tail -80 "$LOG_FILE" >&2
        exit 1
      fi
      sleep 1
    done
    tail -80 "$LOG_FILE" >&2
    echo "Timed out waiting for $APP_NAME." >&2
    exit 1
    ;;
  *)
    echo "usage: $0 [run|--debug|--logs|--telemetry|--verify]" >&2
    exit 2
    ;;
esac
