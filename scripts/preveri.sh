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
STRANI=(/ /app/train /app/bus /app/pot /app/pot/podrobno /app/map /app/ovire /app/statistika /app/statistika/bus /stik /zasebnost)
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

# Robni primeri, ki so bili ze napaka: tiha zamenjava (druga voznja namesto
# neobstojece) in nesmiselno vprasanje, na katerega je aplikacija odgovorila
# (ista postaja na obeh straneh je vrnila osem zvez z enim prestopom).
echo "== robni primeri API"
api() {                     # opis, pot, pricakovana koda
  koda=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$BASE$2")
  if [ "$koda" = "$3" ]; then
    printf "  ok   %-34s %s\n" "$1" "$koda"
  else
    printf "  PADE %-34s %s (pricakoval %s)\n" "$1" "$koda" "$3"
    NAPAKE=$((NAPAKE+1))
  fi
}
api "ista postaja"        "/api/connections?from=Ljubljana&to=Ljubljana" 400
api "neobstojeca postaja" "/api/connections?from=Nikjer&to=Maribor"      404
api "neobstojec trip"     "/api/train/3G?trip=999999999"                 404
api "nesmiseln datum"     "/api/connections?from=Ljubljana&to=Maribor&date=neki" 400
# Pregled za skrbnika ne sme biti odprt. 404 brez zetona (pot naj ne obstaja
# za nikogar, ki ga nima) in 403 z napacnim (tipkarska napaka se mora lociti
# od pozabljene nastavitve).
api "admin brez zetona"   "/admin"                                        404
api "admin napacen zeton" "/admin?k=napacno"                              403
api "admin podatki"       "/admin/podatki"                                404

echo "== koda"
# Ujame nedefinirana imena in mrtvo kodo. Uvoz modula tega ne ujame: vrstica,
# ki se ob uvozu ne izvede, pade sele ob klicu.
if ./venv/bin/python -m pyflakes kajros/ tests/ scripts/*.py; then
  echo "  ok   pyflakes brez najdb"
else
  NAPAKE=$((NAPAKE+1))
fi

echo "== celovitost in skladnost"
if ./venv/bin/python scripts/preveri_skladnost.py; then :; else NAPAKE=$((NAPAKE+1)); fi

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
