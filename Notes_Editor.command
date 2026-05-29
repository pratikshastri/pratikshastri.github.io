#!/bin/zsh

cd "$(dirname "$0")" || exit 1

PORT=8765
URL="http://127.0.0.1:${PORT}/"
PORT_FILE="notes-data/editor.port"

open_if_healthy() {
  local candidate_port="$1"
  local candidate_url="http://127.0.0.1:${candidate_port}/"
  if /usr/bin/curl -fsS "${candidate_url}api/health" >/dev/null 2>&1; then
    /usr/bin/open "${candidate_url}"
    exit 0
  fi
}

mkdir -p notes-data
if [[ -f "${PORT_FILE}" ]]; then
  SAVED_PORT="$(cat "${PORT_FILE}")"
  open_if_healthy "${SAVED_PORT}"
fi

open_if_healthy "${PORT}"

rm -f "${PORT_FILE}"
NOTES_EDITOR_PORT="${PORT}" python3 -c 'import os, subprocess, sys
log = open("notes-data/editor.log", "ab")
subprocess.Popen(
    [sys.executable, "scripts/notes_editor.py", "--port", os.environ["NOTES_EDITOR_PORT"], "--no-open"],
    stdin=subprocess.DEVNULL,
    stdout=log,
    stderr=log,
    start_new_session=True,
)'

for _ in {1..30}; do
  if [[ -f "${PORT_FILE}" ]]; then
    STARTED_PORT="$(cat "${PORT_FILE}")"
    open_if_healthy "${STARTED_PORT}"
  fi
  sleep 0.2
done

open_if_healthy "${PORT}"
/usr/bin/open "notes-data/editor.log"
