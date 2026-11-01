#!/usr/bin/env bash
# Pregled /admin s produkcije v ukazni vrstici -- za agenta, ki sam ne sme
# brati žetona (razvrščevalnik to zavrne kot razkritje poverilnice).
#
#   scripts/admin.sh podatki [od] [do]   obisk, zdravje, sporočila (YYYY-MM-DD)
#   scripts/admin.sh deljenje            današnja deljenja lege
#   scripts/admin.sh vozila [dan]        vozila dneva, s katerimi je kaj narobe
#   scripts/admin.sh vozilo ID [dan]     dosje vozila (`kajros/dosje.py`)
#
# Samo GET in samo te poti: pisalne poti /admin (sporočila, obvestila
# potnikom) ostanejo človeku. Žeton gre z arwena naravnost v glavo zahteve,
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
  *) echo "uporaba: $0 podatki [od] [do] | deljenje | vozila [dan] | vozilo ID [dan]" >&2; exit 2 ;;
esac

zeton=$(ssh david@192.168.1.46 cat /var/lib/kajros/.admin-zeton)
curl -sSf --max-time 30 -H @<(printf 'Cookie: kajros_admin=%s\n' "$zeton") \
  "https://kajros.app$pot"
echo
