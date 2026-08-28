#!/usr/bin/env bash
# Ponovni zagon razvojnega streznika. Cakanje na dejansko sprosceni port je
# nujno: uvicorn potrebuje trenutek za zaustavitev in nov proces sicer umre
# na "address already in use", kar je videti kot okvara aplikacije.
set -u
cd "$(dirname "$0")/.."
LOG="${SZ_DEV_LOG:-/tmp/sztrack-dev.log}"
pkill -f "[u]vicorn sztrack.api" 2>/dev/null
for _ in $(seq 1 40); do
  pgrep -f "[u]vicorn sztrack.api" >/dev/null || break
  sleep 0.25
done
setsid nohup ./venv/bin/python -m uvicorn sztrack.api:app \
  --host 127.0.0.1 --port 8001 > "$LOG" 2>&1 < /dev/null &
disown
for _ in $(seq 1 60); do
  if curl -sf -o /dev/null http://127.0.0.1:8001/api/health; then
    echo "streznik tece na 8001 (dnevnik: $LOG)"
    exit 0
  fi
  sleep 0.5
done
echo "streznik se ni odzval:" >&2
tail -25 "$LOG" >&2
exit 1
