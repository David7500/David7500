#!/usr/bin/env bash
# Sestavi zip za gostitelja, ki sprejme zip (glej DEPLOY.md, "Paket za gostitelja").
# Zažene se iz korena repozitorija.
#
#   ./scripts/build_deploy_zip.sh [izhod.zip]
#
# Vsebina je natanko to, kar je v gitu na HEAD -- `git archive`, ne `zip` na
# delovno drevo: sicer se v paket prikradejo neshranjene spremembe, `venv/`
# in podatki. Priložena baza `seed/kajros.sqlite` je v gitu (izjema v .gitignore),
# zato pride zraven sama.
set -euo pipefail
OUT="${1:-kajros-deploy.zip}"
cd "$(dirname "$0")/.."

if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "OPOZORILO: delovno drevo ni čisto -- v paket gre HEAD, ne to, kar vidiš." >&2
fi

rm -f "$OUT"
git archive --format=zip -o "$OUT" HEAD

printf '\n%s  (%s, %s datotek, HEAD=%s)\n' \
    "$OUT" "$(du -h "$OUT" | cut -f1)" "$(unzip -l "$OUT" | tail -1 | awk '{print $2}')" \
    "$(git rev-parse --short HEAD)"
