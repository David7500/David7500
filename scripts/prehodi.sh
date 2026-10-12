#!/usr/bin/env bash
# Prehod brez trase proti sedanjemu načinu, s produkcije (arwen): koliko
# vmesnih postankov izmeri vsak in kako se ujemata (`kajros prehodi`,
# docs/MERITVE.md 12. 10. 2026). Baza samo za branje, zato brez sudota.
#
#   scripts/prehodi.sh [--dni N] [--pred N]
set -euo pipefail
ssh david@192.168.1.46 "cd /opt/kajros && KAJROS_DATA_DIR=/var/lib/kajros \
  .venv/bin/python -m kajros.cli prehodi --samo-branje$(printf ' %q' "$@")"
