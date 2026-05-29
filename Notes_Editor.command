#!/bin/zsh

cd "$(dirname "$0")" || exit 1

PORT=8765
URL="http://127.0.0.1:${PORT}/"

if /usr/bin/curl -fsS "${URL}api/health" >/dev/null 2>&1; then
  /usr/bin/open "${URL}"
  exit 0
fi

mkdir -p notes-data
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
  if /usr/bin/curl -fsS "${URL}api/health" >/dev/null 2>&1; then
    /usr/bin/open "${URL}"
    exit 0
  fi
  sleep 0.2
done

/usr/bin/open "${URL}"
