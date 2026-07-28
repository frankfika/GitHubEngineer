#!/usr/bin/env bash
# Run the test suite with an auto-spun fake LLM server.
#
# Usage:
#     bash tests/mocks/run_e2e.sh
#     FAKE_LLM_PORT=8080 bash tests/mocks/run_e2e.sh
#     PYTEST_ARGS="-v" bash tests/mocks/run_e2e.sh
#
# What it does:
#   1. Starts tests/mocks/fake_llm_server.py on $FAKE_LLM_PORT (default 9999).
#   2. Writes a temp .ghe/config.yml pointing ``coding_agent`` at the
#      local fake server. The file is removed on exit, even on failure.
#   3. Runs the test suite with pytest, with the temp config in place.
#   4. Cleans up the server and config on exit.
#
# Why a shell script and not a conftest fixture? Because we want this
# to also work as a one-shot CI step where the operator just runs the
# script and watches a green bar -- no pytest plugin required.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

PY="${PY:-.venv/bin/python3}"
if [[ ! -x "$PY" ]]; then
    PY="python3"
fi

PORT="${FAKE_LLM_PORT:-9999}"
LOG="/tmp/fake_llm_${PORT}.log"
TMP_CONFIG=".ghe/config.yml"
BACKUP="$(mktemp -t ghe_config_backup.XXXXXX.yml)"
if [[ -f "$TMP_CONFIG" ]]; then
    cp "$TMP_CONFIG" "$BACKUP"
fi

cleanup() {
    local exit_code=$?
    if [[ -n "${FAKE_PID:-}" ]] && kill -0 "$FAKE_PID" 2>/dev/null; then
        kill "$FAKE_PID" 2>/dev/null || true
        wait "$FAKE_PID" 2>/dev/null || true
    fi
    # Restore or remove temp config.
    if [[ -f "$BACKUP" ]]; then
        mv "$BACKUP" "$TMP_CONFIG"
    else
        rm -f "$TMP_CONFIG"
    fi
    exit "$exit_code"
}
trap cleanup EXIT INT TERM

echo ">> Starting fake LLM server on :$PORT (log: $LOG)"
FAKE_LLM_QUIET="${FAKE_LLM_QUIET:-1}" "$PY" tests/mocks/fake_llm_server.py > "$LOG" 2>&1 &
FAKE_PID=$!

# Wait until the port accepts a TCP connection (max 5s).
for _ in $(seq 1 50); do
    if (echo > /dev/tcp/127.0.0.1/$PORT) 2>/dev/null; then
        break
    fi
    sleep 0.1
done
if ! (echo > /dev/tcp/127.0.0.1/$PORT) 2>/dev/null; then
    echo "!! fake LLM server did not start. Log:" >&2
    cat "$LOG" >&2
    exit 1
fi

echo ">> Writing temp .ghe/config.yml pointing at fake server"
mkdir -p .ghe
cat > "$TMP_CONFIG" <<EOF
coding_agent:
  provider: openai_compatible
  base_url: http://127.0.0.1:$PORT/v1
  api_key: fake-key-not-real
  model: fake-model
EOF

echo ">> Running pytest ${PYTEST_ARGS:--q}"
# shellcheck disable=SC2086
"$PY" -m pytest tests/ ${PYTEST_ARGS:--q}
