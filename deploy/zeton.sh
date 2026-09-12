#!/usr/bin/env bash
# Žeton za pregled `/admin`. BREZ gesla, tako kot `posodobi.sh`.
#
# Zakaj ne v systemd enoto: enoto v `/etc/systemd/system` sme pisati samo
# root, posodobitev strežnika pa je namenoma brez sudota (`brez-sudo.sh`
# dovoli natanko štiri ukaze `systemctl`). Žeton v `/etc` bi torej pomenil,
# da je za vsako menjavo potreben človek z geslom. Podatkovni imenik je
# skupinsko pisljiv, zato gre žeton tja -- bere ga `config._admin_zeton()`.
#
#   bash deploy/zeton.sh          # izpiše obstoječega ali naredi novega
#   bash deploy/zeton.sh --nov    # zavrže starega in naredi novega
#
# Po menjavi je potreben restart: žeton se prebere ob zagonu procesa.
set -euo pipefail

DATA="${KAJROS_DATA_DIR:-/var/lib/kajros}"
DAT="$DATA/.admin-zeton"
NOV=0
[ "${1:-}" = "--nov" ] && NOV=1

[ -d "$DATA" ] || { echo "podatkovnega imenika '$DATA' ni"; exit 1; }

if [ ! -s "$DAT" ] || [ "$NOV" = 1 ]; then
    # `umask 077` pred pisanjem, ne `chmod` po njem: med nastankom in
    # popravkom pravic je datoteka sicer za trenutek berljiva vsem.
    ( umask 077
      command -v openssl >/dev/null \
        && openssl rand -base64 24 | tr -d '\n=+/' > "$DAT" \
        || head -c 24 /dev/urandom | base64 | tr -d '\n=+/' > "$DAT" )
    # Skupina `kajros` mora brati: storitev teče pod svojim uporabnikom,
    # datoteko pa naredi `david`. Brez tega bi strežnik žetona ne videl in
    # `/admin` bi tiho ostal 404 -- napaka, ki je videti kot okvara.
    chgrp kajros "$DAT" 2>/dev/null || true
    chmod 640 "$DAT"
    echo "nov žeton zapisan v $DAT"
    echo "poženi še:  sudo systemctl restart kajros.service"
else
    echo "žeton že obstaja ($DAT); za novega dodaj --nov"
fi

echo
echo "  žeton: $(cat "$DAT")"
echo "  vstop: https://kajros.app/admin?k=$(cat "$DAT")"
