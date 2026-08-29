#!/usr/bin/env bash
# Ponovni zagon razvojnega streznika. Cakanje na dejansko sprosceni port je
# nujno: uvicorn potrebuje trenutek za zaustavitev in nov proces sicer umre
# na "address already in use", kar je videti kot okvara aplikacije.
#
# `SZ_HOST=0.0.0.0` odpre streznik za lokalno omrezje (telefon, druga naprava).
# To ni isto kot odpiranje vrat na usmerjevalniku: API nima avtentikacije in
# ga sme videti samo domace omrezje.
set -u
cd "$(dirname "$0")/.."
LOG="${SZ_DEV_LOG:-/tmp/sztrack-dev.log}"
HOST="${SZ_HOST:-127.0.0.1}"
PORT="${SZ_PORT:-8001}"
pkill -f "[u]vicorn sztrack.api.*--port $PORT" 2>/dev/null
for _ in $(seq 1 40); do
  pgrep -f "[u]vicorn sztrack.api.*--port $PORT" >/dev/null || break
  sleep 0.25
done
setsid nohup ./venv/bin/python -m uvicorn sztrack.api:app \
  --host "$HOST" --port "$PORT" > "$LOG" 2>&1 < /dev/null &
disown
for _ in $(seq 1 60); do
  if curl -sf -o /dev/null "http://127.0.0.1:$PORT/api/health"; then
    echo "streznik tece na $PORT (dnevnik: $LOG)"
    if [ "$HOST" = "0.0.0.0" ]; then
      ip -4 -br addr show scope global | awk -v p="$PORT" \
        '{split($3,a,"/"); printf "  v omrezju: http://%s:%s/app\n", a[1], p}'
    fi
    exit 0
  fi
  sleep 0.5
done
echo "streznik se ni odzval:" >&2
tail -25 "$LOG" >&2
exit 1
