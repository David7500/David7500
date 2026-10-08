#!/usr/bin/env bash
# Prijava za NAP (lege avtobusov IJPP, `kajros/nap.py`). BREZ sudota, kot
# `zeton.sh`: podatkovni imenik je skupinsko pisljiv.
#
# Geslo se vpiše v terminal in ne gre ne v ukazno vrstico ne v zgodovino
# lupine. Datoteko bere nit NAP ob vsakem obhodu, zato restart ni potreben.
#
#   ssh -t david@192.168.1.46 'bash ~/kajros/deploy/nap.sh'
#
# Na koncu en poskusni zahtevek: 200 = lege tečejo, 401 = NAP vsebine
# „SIRI dinamični podatki - API“ še ni odobril ali je geslo napačno.
set -euo pipefail

DATA="${KAJROS_DATA_DIR:-/var/lib/kajros}"
DAT="$DATA/.nap-prijava"
URL="${KAJROS_NAP_URL:-https://b2b.nap.si/data/b2b.siri.api/ServiceRequest}"

[ -d "$DATA" ] || { echo "podatkovnega imenika '$DATA' ni"; exit 1; }

read -rp "e-naslov računa na nap.si: " UPORABNIK
read -rsp "geslo: " GESLO
echo
[ -n "$UPORABNIK" ] && [ -n "$GESLO" ] || { echo "prazno -- nič zapisano"; exit 1; }

# `umask 077` pred pisanjem, ne `chmod` po njem (glej `zeton.sh`).
( umask 077; printf '%s:%s\n' "$UPORABNIK" "$GESLO" > "$DAT" )
chgrp kajros "$DAT" 2>/dev/null || true
chmod 640 "$DAT"
echo "prijava zapisana v $DAT"

# Geslo gre curlu po standardnem vhodu (`-K -`), ne kot argument: argumenti
# so v `ps` vidni vsem uporabnikom stroja.
ZDAJ="$(date -Iseconds)"
# V nastavitvi curla sta `\` in `"` v narekovajih posebna.
ESC="${GESLO//\\/\\\\}"; ESC="${ESC//\"/\\\"}"
KODA="$(printf 'user = "%s:%s"\n' "$UPORABNIK" "$ESC" | curl -sS -K - \
    -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/xml' \
    --data "<ServiceRequest xmlns=\"http://www.siri.org.uk/siri\"><RequestTimestamp>$ZDAJ</RequestTimestamp><VehicleMonitoringRequest><RequestTimestamp>$ZDAJ</RequestTimestamp></VehicleMonitoringRequest></ServiceRequest>" \
    "$URL" || true)"
unset GESLO ESC
case "$KODA" in
    200) echo "NAP odgovoril 200: lege tečejo, v /admin vrstica „NAP · lege IJPP“." ;;
    401|403) echo "NAP odgovoril $KODA: dostop še ni odobren ali geslo ni pravo. Nit poskusi znova na 10 min." ;;
    *) echo "NAP odgovoril '$KODA' -- preveri omrežje; nit bo poskušala sama." ;;
esac
