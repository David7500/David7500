#!/usr/bin/env bash
# Časovni stroj: vsi preizkusi pod lažno uro, da datumska bomba poči tu in ne
# čez mesec na dan objave.
#
#   ./scripts/casovni_stroj.sh                  kratek nabor (ta teče v preveri.sh)
#   ./scripts/casovni_stroj.sh --vse            še vsaka ura dneva, konec leta, premik ure
#   ./scripts/casovni_stroj.sh "2027-03-28 02:30:00" ...     izbrani trenutki
#
# Zakaj: preizkus s trdim datumom in oknom v kodi („zadnjih 90 dni“) je zelen,
# dokler datum ne zdrsne iz okna. 9. 11. 2026 je prvi zagon našel preizkus, ki
# bi padel 26. 11. 2026, dva, ki sta padala vsako noč med polnočjo in 7.06, in
# enega v prvih minutah po polnoči (`docs/MERITVE.md`, „Časovni stroj“).
#
# Uro ponaredi libfaketime prek LD_PRELOAD: velja za Python IN za SQLite
# (`date('now')`), česar zamenjava `time.time` v preizkusu ne doseže. Knjižnica
# ni odvisnost projekta: če je sistem nima, se paket prenese in razpakira v
# predpomnilnik brez namestitve (brez sudo). Brez omrežja in brez knjižnice se
# korak preskoči z izhodno kodo 0 -- preveri.sh zaradi tega ne sme biti rdeč.
set -u
cd "$(dirname "$0")/.."

PREDPOMNILNIK="${XDG_CACHE_HOME:-$HOME/.cache}/kajros/faketime"
SISTEMSKA=/usr/lib/x86_64-linux-gnu/faketime/libfaketime.so.1

knjiznica() {
  if [ -n "${KAJROS_FAKETIME:-}" ] && [ -f "$KAJROS_FAKETIME" ]; then echo "$KAJROS_FAKETIME"; return; fi
  if [ -f "$SISTEMSKA" ]; then echo "$SISTEMSKA"; return; fi
  local najdena
  najdena=$(find "$PREDPOMNILNIK" -name 'libfaketime.so.1' 2>/dev/null | head -1)
  if [ -z "$najdena" ] && command -v apt >/dev/null && command -v dpkg >/dev/null; then
    mkdir -p "$PREDPOMNILNIK" && (
      cd "$PREDPOMNILNIK" && apt download libfaketime >/dev/null 2>&1 \
        && for p in libfaketime_*.deb; do dpkg -x "$p" .; done
    )
    najdena=$(find "$PREDPOMNILNIK" -name 'libfaketime.so.1' 2>/dev/null | head -1)
  fi
  echo "$najdena"
}

LIB=$(knjiznica)
if [ -z "$LIB" ]; then
  echo "  --   časovni stroj preskočen: libfaketime ni na voljo (apt download libfaketime ni uspel)"
  exit 0
fi

# Zadnja nedelja meseca v naslednjih 13 mesecih: premik ure (marec, oktober).
premik() {                  # mesec -> LLLL-MM-DD
  ./venv/bin/python - "$1" <<'PY'
import sys
from datetime import date, timedelta
mesec, danes = int(sys.argv[1]), date.today()
for leto in (danes.year, danes.year + 1):
    d = date(leto, mesec, 31)
    while d.weekday() != 6:
        d -= timedelta(days=1)
    if d > danes:
        print(d.isoformat())
        break
PY
}

jutri=$(date -d tomorrow +%F)
KRATEK=(
  "$jutri 00:00:01"                       # prve sekunde dneva: negativne voznoredne sekunde
  "$jutri 03:00:00"                       # noč: obratovalni dan še včerajšnji, nočna opravila
  "$(date -d '+30 days' +%F) 12:00:00"    # mesec naprej: opozorilo pred bombo
  "$(date -d '+90 days' +%F) 12:00:00"    # okno „zadnjih 90 dni“ se izprazni
)

if [ "${1:-}" = "--vse" ]; then
  TRENUTKI=("${KRATEK[@]}")
  for ura in $(seq -w 1 23); do TRENUTKI+=("$jutri $ura:30:00"); done
  leto=$(date +%Y)
  marec=$(premik 3); oktober=$(premik 10)
  TRENUTKI+=(
    "$(date -d '+366 days' +%F) 12:00:00"
    "$leto-12-31 23:59:40" "$((leto + 1))-01-01 00:10:00"
    "$marec 01:59:50" "$marec 03:30:00" "$(date -d "$marec +1 day" +%F) 08:00:00"
    "$oktober 02:30:00" "$oktober 12:00:00" "$(date -d "$oktober +1 day" +%F) 00:30:00"
    "2028-02-29 12:00:00"
  )
elif [ $# -gt 0 ]; then
  TRENUTKI=("$@")
else
  TRENUTKI=("${KRATEK[@]}")
fi

IZPISI=$(mktemp -d)
trap 'rm -rf "$IZPISI"' EXIT

en() {                      # trenutek -> vrstica izida; izhodna koda preizkusov
  local kdaj="$1" izpis
  izpis="$IZPISI/$(echo "$kdaj" | tr ' :' '__').txt"
  LD_PRELOAD="$LIB" FAKETIME="@$kdaj" DONT_FAKE_MONOTONIC=1 timeout 600 \
    ./venv/bin/python -m pytest -q -p no:cacheprovider --tb=line > "$izpis" 2>&1
  local koda=$?
  if [ $koda -eq 0 ]; then
    echo "  ok   $kdaj  $(tail -1 "$izpis")"
  else
    echo "  PADE $kdaj  $(tail -1 "$izpis")"
    grep '^FAILED\|^ERROR' "$izpis" | sed 's/ - .*//; s/^/         /'
  fi
  return $koda
}
export -f en
export LIB IZPISI

# Štirje hkrati: en zagon ~15 s, več vzporednih podaljša vsakega.
if printf '%s\n' "${TRENUTKI[@]}" | xargs -P 4 -I{} bash -c 'en "{}"'; then
  exit 0
fi
echo "  Ponovi en trenutek: ./scripts/casovni_stroj.sh \"LLLL-MM-DD UU:MM:SS\""
exit 1
