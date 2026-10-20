#!/usr/bin/env bash
# Žeton za sporočila Ko-fi (`kajros/donacije.py`). BREZ sudota, kot `nap.sh`:
# podatkovni imenik je skupinsko pisljiv.
#
# Žeton je „Verification Token“ na ko-fi.com/manage/webhooks. Na isti
# strani v polje Webhook URL vpiši natanko
#
#   https://kajros.app/donacije/ko-fi
#
# Strežnik datoteko bere ob vsaki zahtevi, zato restart ni potreben.
#
#   ssh -t david@192.168.1.46 'bash ~/kajros/deploy/kofi.sh'
#
# Nato na isti strani gumb za preizkusno donacijo; v /admin pod Podporo se
# mora pokazati „preizkus pred … s“. „zavrnjeno (napačen žeton)“ = prepiši žeton.
set -euo pipefail

DATA="${KAJROS_DATA_DIR:-/var/lib/kajros}"
DAT="$DATA/.kofi-zeton"

[ -d "$DATA" ] || { echo "podatkovnega imenika '$DATA' ni"; exit 1; }

# Žeton ne gre ne v ukazno vrstico ne v zgodovino lupine.
read -rsp "Verification Token s Ko-fi: " ZETON
echo
ZETON="$(printf '%s' "$ZETON" | tr -d '[:space:]')"
[ -n "$ZETON" ] || { echo "prazno -- nič zapisano"; exit 1; }

# `umask 077` pred pisanjem, ne `chmod` po njem (glej `zeton.sh`).
( umask 077; printf '%s\n' "$ZETON" > "$DAT" )
unset ZETON
chgrp kajros "$DAT" 2>/dev/null || true
chmod 640 "$DAT"
echo "žeton zapisan v $DAT"

# Brez žetona je pot 404, z njim prazna zahteva 403 -- tako se vidi, da ga
# strežnik bere, ne da bi kaj zapisali v bazo.
KODA="$(curl -sS -o /dev/null -w '%{http_code}' -X POST \
    "http://127.0.0.1:${KAJROS_PORT:-8000}/donacije/ko-fi" || true)"
case "$KODA" in
    403) echo "strežnik žeton vidi (prazna zahteva: 403). Zdaj preizkus na Ko-fi." ;;
    404) echo "strežnik žetona ne vidi (404) -- ali bere skupina kajros datoteko?" ;;
    *)   echo "strežnik odgovoril '$KODA' -- teče na tem vratu?" ;;
esac
