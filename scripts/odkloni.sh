#!/usr/bin/env bash
# Odkloni od trase s produkcije (arwen), po odsekih -- pregled po nekaj dneh
# beleženja (`kajros odkloni`, docs/MERITVE.md 11. 10. 2026). Baza se odpre
# samo za branje, zato brez sudota.
#
#   scripts/odkloni.sh [--dni N] [--najmanj N] [--najvec N]
set -euo pipefail
ssh david@192.168.1.46 "cd /opt/kajros && KAJROS_DATA_DIR=/var/lib/kajros \
  .venv/bin/python -m kajros.cli odkloni --samo-branje$(printf ' %q' "$@")"
