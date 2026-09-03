#!/usr/bin/env bash
# Zgodovina projekta na drugo napravo, brez GitHuba.
#
# Zakaj: 196 commitov je 3. 9. 2026 obstajalo SAMO na razvojnem disku. Potisk
# na GitHub rabi ključ, ki ga nimamo, malina pa je imela le delovno drevo brez
# `.git`. En pokvarjen disk bi odnesel ves projekt.
#
# `git bundle` je ena datoteka s celotno zgodovino. Obnovitev:
#   git clone kajros-YYYYMMDD.bundle kajros
set -euo pipefail
cd "$(dirname "$0")/.."

PI="${KAJROS_PI:-david@192.168.1.166}"
KAM="${KAJROS_KOPIJA:-~/kajros-zgodovina}"
IME="kajros-$(date +%Y%m%d-%H%M).bundle"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "== delam sveženj"
git bundle create "$TMP/$IME" --all
git bundle verify "$TMP/$IME" >/dev/null && echo "  sveženj je cel"
du -h "$TMP/$IME" | awk '{print "  "$1}'

if ! timeout 10 ssh -o BatchMode=yes -o ConnectTimeout=5 "$PI" true 2>/dev/null; then
  echo "  $PI ni dosegljiva -- sveženj ostaja v $TMP" >&2
  trap - EXIT
  exit 1
fi

echo "== nesem na malino"
timeout 30 ssh -o BatchMode=yes "$PI" "mkdir -p $KAM"
timeout 600 scp -q "$TMP/$IME" "$PI:$KAM/"
# Zadnjih pet je dovolj: sveženj vsebuje CELO zgodovino, ne razlike, zato je
# vsak sam po sebi popolna kopija.
timeout 30 ssh -o BatchMode=yes "$PI" \
  "cd $KAM && ls -t *.bundle | tail -n +6 | xargs -r rm -f; ls -lh *.bundle | tail -3"
echo "  obnovitev: git clone $KAM/$IME kajros"
