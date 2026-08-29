#!/usr/bin/env bash
# Sestavi paket za namestitev na malino (ali kateri koli Debian stroj).
# Zažene se iz korena repozitorija.
#
#   ./scripts/build_deploy_zip.sh [izhod.zip]
#
# Vsebina je natanko to, kar je v gitu na HEAD -- `git archive`, ne `zip` na
# delovno drevo: sicer se v paket prikradejo neshranjene spremembe, `venv/`
# in podatki. Priložena baza `seed/sz.sqlite` je v gitu (izjema v .gitignore),
# zato pride zraven sama.
set -euo pipefail
OUT="${1:-sztrack-deploy.zip}"
cd "$(dirname "$0")/.."

if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "OPOZORILO: delovno drevo ni čisto -- v paket gre HEAD, ne to, kar vidiš." >&2
fi

rm -f "$OUT"
git archive --format=zip -o "$OUT" HEAD

printf '\n%s  (%s, %s datotek, HEAD=%s)\n' \
    "$OUT" "$(du -h "$OUT" | cut -f1)" "$(unzip -l "$OUT" | tail -1 | awk '{print $2}')" \
    "$(git rev-parse --short HEAD)"
echo
echo "Namestitev na malini (počakaj, poženi sam -- sudo rabi geslo):"
echo "  unzip -q -o ~/$(basename "$OUT") -d ~/sztrack-src && \\"
echo "  sudo SZ_MODE=zajem SZ_SRC=~/sztrack-src bash ~/sztrack-src/deploy/install-rpi.sh"
