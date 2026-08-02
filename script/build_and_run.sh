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

# Closing the desktop app normally reaps its sidecar, but allow a few seconds
# for that process-group cleanup before inspecting the well-known port.
for _ in $(seq 1 50); do
  if ! lsof -tiTCP:8765 -sTCP:LISTEN >/dev/null 2>&1; then
    break
  fi
  sleep 0.1
done

BACKEND_PIDS="$(lsof -tiTCP:8765 -sTCP:LISTEN 2>/dev/null | sort -u || true)"
if [[ -n "$BACKEND_PIDS" ]]; then
  while IFS= read -r backend_pid; do
    [[ -n "$backend_pid" ]] || continue
    backend_command="$(ps -p "$backend_pid" -o command= 2>/dev/null || true)"
    if [[ "$backend_command" == *"github-engineer-backend"* \
      || "$backend_command" == *"src.main"*"--serve"* ]]; then
      kill "$backend_pid" >/dev/null 2>&1 || true
    else
      echo "Port 8765 is already used by an unrelated process: $backend_command" >&2
      echo "Refusing to report a stale service as this build." >&2
      exit 1
    fi
  done <<< "$BACKEND_PIDS"
  for _ in $(seq 1 50); do
    if ! lsof -tiTCP:8765 -sTCP:LISTEN >/dev/null 2>&1; then
      break
    fi
    sleep 0.1
  done
  if lsof -tiTCP:8765 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "GitHub Engineer backend did not release port 8765." >&2
    exit 1
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
    # Verify the same release bundle users install. A detached `tauri dev`
    # launcher can disappear with its invoking shell and yield a false green
    # after one transient health response. Launch Services owns the packaged
    # app lifecycle, so it remains running after this command returns.
    npm run desktop:build >"$LOG_FILE" 2>&1
    APP_BUNDLE="$ROOT_DIR/src-tauri/target/release/bundle/macos/GitHub Engineer.app"
    if [[ ! -d "$APP_BUNDLE" ]]; then
      tail -80 "$LOG_FILE" >&2
      echo "Release app bundle was not produced." >&2
      exit 1
    fi
    "$ROOT_DIR/script/verify_desktop_bundle.sh" "$APP_BUNDLE" >>"$LOG_FILE" 2>&1
    /usr/bin/open -na "$APP_BUNDLE"
    for _ in $(seq 1 300); do
      if pgrep -x "$APP_NAME" >/dev/null 2>&1 \
        && curl --fail --silent --max-time 2 http://127.0.0.1:8765/healthz >/dev/null; then
        # Catch apps that render briefly and then lose their sidecar.
        sleep 3
        if pgrep -x "$APP_NAME" >/dev/null 2>&1 \
          && curl --fail --silent --max-time 2 http://127.0.0.1:8765/healthz >/dev/null; then
          echo "GitHub Engineer release app is running."
          echo "Packaged backend health check passed after the stability window."
          echo "app: $APP_BUNDLE"
          echo "build log: $LOG_FILE"
          exit 0
        fi
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
