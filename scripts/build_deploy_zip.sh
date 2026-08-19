#!/usr/bin/env bash
# Sestavi paket za objavo. Zažene se iz korena repozitorija.
set -euo pipefail
OUT="${1:-sztrack-deploy.zip}"
rm -f "$OUT"
zip -r -q "$OUT" \
  main.py requirements.txt Procfile DEPLOY.md \
  sztrack seed \
  -x '*__pycache__*' '*.pyc'
printf '%s: %s\n' "$OUT" "$(du -h "$OUT" | cut -f1)"
unzip -l "$OUT" | tail -n +4 | head -20
