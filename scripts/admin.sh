#!/usr/bin/env bash
# Pregled /admin s produkcije v ukazni vrstici -- za agenta, ki sam ne sme
# brati žetona (razvrščevalnik to zavrne kot razkritje poverilnice).
#
#   scripts/admin.sh podatki [od] [do]   obisk, zdravje, sporočila (YYYY-MM-DD)
#   scripts/admin.sh deljenje            današnja deljenja lege
#   scripts/admin.sh vozila [dan]        vozila dneva, s katerimi je kaj narobe
#   scripts/admin.sh vozilo ID [dan]     dosje vozila (`kajros/dosje.py`)
#   scripts/admin.sh sporocila [od]      nabiralnik in opombe od dneva, ena vrstica JSON na sporočilo
#   scripts/admin.sh umakni ID           opombo umakne z vožnje, v nabiralniku ostane
#   scripts/admin.sh izbrisi ID          sporočilo izbriše (in opombo umakne)
#
# Ena pisalna pot, `POST /admin/sporocila/{id}`: opombe se objavijo same
# (David, 9. 11. 2026), Claude jih pregleda vsake tri dni (skill `opombe`).
# Obvestila potnikom ostanejo človeku. Žeton gre z arwena naravnost v glavo zahteve,
# prek datoteke, ne argumenta -- v izpis, `ps` in zgodovino lupine ne pride.
# Dovoljenje v `.claude/settings.local.json`: "Bash(./scripts/admin.sh:*)".
set -euo pipefail

datum='^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
case "${1:-podatki}" in
  podatki)
    pot=/admin/podatki
    if [[ -n "${2:-}" ]]; then
      od=$2 do=${3:-$2}
      [[ $od =~ $datum && $do =~ $datum ]] || { echo "datum je YYYY-MM-DD" >&2; exit 2; }
      pot+="?od=$od&do=$do"
    fi ;;
  deljenje) pot=/admin/deljenje ;;
  vozila)
    pot=/admin/vozila
    if [[ -n "${2:-}" ]]; then
      [[ $2 =~ $datum ]] || { echo "datum je YYYY-MM-DD" >&2; exit 2; }
      pot+="?dan=$2"
    fi ;;
  vozilo)
    [[ ${2:-} =~ ^[A-Za-z0-9_.-]+$ ]] || { echo "uporaba: $0 vozilo ID [dan]" >&2; exit 2; }
    pot="/admin/vozilo/$2"
    if [[ -n "${3:-}" ]]; then
      [[ $3 =~ $datum ]] || { echo "datum je YYYY-MM-DD" >&2; exit 2; }
      pot+="?dan=$3"
    fi ;;
  sporocila)
    pot=/admin/podatki od=${2:-0000-00-00}
    [[ $od =~ $datum ]] || { echo "datum je YYYY-MM-DD" >&2; exit 2; } ;;
  umakni|izbrisi)
    [[ ${2:-} =~ ^[0-9]+$ ]] || { echo "uporaba: $0 $1 ID" >&2; exit 2; }
    pot="/admin/sporocila/$2" ;;
  *) echo "uporaba: $0 podatki [od] [do] | deljenje | vozila [dan] | vozilo ID [dan]" \
          "| sporocila [od] | umakni ID | izbrisi ID" >&2; exit 2 ;;
esac

zeton=$(ssh david@192.168.1.46 cat /var/lib/kajros/.admin-zeton)
beri() {
  curl -sSf --max-time 30 -H @<(printf 'Cookie: kajros_admin=%s\n' "$zeton") "$@"
}
case $1 in
  sporocila)
    # Brez voženj in naslednjih postaj: pregled rabi besedilo in oznako.
    beri "https://kajros.app$pot" | jq -c --arg od "$od" '.sporocila.seznam[]
      | select(.prispelo[0:10] >= $od)
      | {id, prispelo: .prispelo[0:16], besedilo, email: (.email != ""),
         opomba: (.opomba.oznaka // null), objavljena: (.objavljeno // null),
         st: (.opomba_id // null)}' ;;
  umakni) beri -X POST --data akcija=umakni "https://kajros.app$pot"; echo ;;
  izbrisi) beri -X POST --data akcija=brisi "https://kajros.app$pot"; echo ;;
  *) beri "https://kajros.app$pot"; echo ;;
esac
