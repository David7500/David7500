#!/usr/bin/env bash
# Pregled /admin s produkcije v ukazni vrstici -- za agenta, ki sam ne sme
# brati žetona (razvrščevalnik to zavrne kot razkritje poverilnice).
#
#   scripts/admin.sh podatki [od] [do]   obisk, zdravje, sporočila (YYYY-MM-DD)
#   scripts/admin.sh deljenje            današnja deljenja lege
#
# Samo GET in samo ti dve poti: pisalne poti /admin (sporočila, obvestila
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
  *) echo "uporaba: $0 podatki [od] [do] | deljenje" >&2; exit 2 ;;
esac

zeton=$(ssh david@192.168.1.46 cat /var/lib/kajros/.admin-zeton)
curl -sSf --max-time 30 -H @<(printf 'Cookie: kajros_admin=%s\n' "$zeton") \
  "https://kajros.app$pot"
echo
