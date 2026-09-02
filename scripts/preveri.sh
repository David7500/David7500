#!/usr/bin/env bash
# Eno preverjanje, ki vrne "pade" ali "uspe" -- testi, odzivi strani in
# konzola brskalnika. Namenjeno temu, da spremembe ni treba razglašati za
# končano na oko: `./scripts/preveri.sh` in poglej izhodno kodo.
#
# Strežnik mora teči (./scripts/dev-restart.sh). Posnetki gredo v posnetki/,
# ker chromium ne more pisati v /tmp.
set -uo pipefail
cd "$(dirname "$0")/.."

PORT="${KAJROS_PORT:-8001}"
BASE="http://127.0.0.1:$PORT"
STRANI=(/ /app/train /app/bus /app/map /app/ovire /app/statistika /app/statistika/bus)
NAPAKE=0

echo "== testi"
if ./venv/bin/python -m pytest -q 2>&1 | tail -3; then :; else NAPAKE=$((NAPAKE+1)); fi

if ! curl -s -o /dev/null --max-time 5 "$BASE/api/health"; then
  echo "!! strežnik na $PORT ne teče -- poženi ./scripts/dev-restart.sh"
  exit 1
fi

echo "== strani"
mkdir -p posnetki
for pot in "${STRANI[@]}"; do
  koda=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$BASE$pot")
  # Napake JS se v konzoli vidijo tudi takrat, ko je HTTP 200 in stran prazna.
  konzola=$(timeout 60 chromium --headless --disable-gpu --window-size=430,900 \
    --virtual-time-budget=7000 --screenshot="$PWD/posnetki/preveri.png" "$BASE$pot" 2>&1 \
    | grep -Ei "Uncaught|SyntaxError|ReferenceError|TypeError" | head -3)
  if [ "$koda" != "200" ] || [ -n "$konzola" ]; then
    printf "  PADE %-14s %s %s\n" "$pot" "$koda" "$konzola"
    NAPAKE=$((NAPAKE+1))
  else
    printf "  ok   %-14s 200\n" "$pot"
  fi
done

echo "== paleta"
if ./venv/bin/python scripts/preveri_paleto.py >/dev/null 2>&1; then
  echo "  ok   kontrast in barvna slepota"
else
  echo "  PADE paleta -- poženi scripts/preveri_paleto.py za podrobnosti"
  NAPAKE=$((NAPAKE+1))
fi

echo
if [ "$NAPAKE" -eq 0 ]; then echo "vse zeleno"; else echo "napak: $NAPAKE"; fi
exit "$NAPAKE"
