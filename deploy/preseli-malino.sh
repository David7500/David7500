#!/usr/bin/env bash
# Preseli malino s starega imena (`sztrack`) na `kajros`. Poženi Z ROOTOM,
# na malini:
#
#     sudo bash ~/kajros-src/deploy/preseli-malino.sh
#
# Zakaj svoj skript in ne kar `install-rpi.sh`: ta zna preseliti, ne pove pa
# nič o tem, ali je bilo varno začeti in ali je bilo po koncu res v redu.
# Malina je merodajen zajem -- meritev, ki je nihče ne posname, ne obstaja
# nikoli več -- zato tu pred selitvijo preverimo predpogoje in po njej štejemo.
set -euo pipefail

STARI_DATA=/var/lib/sztrack
STARA_BAZA="$STARI_DATA/sz.sqlite"
NOVA_BAZA=/var/lib/kajros/kajros.sqlite
VIR="${KAJROS_SRC:-/home/david/kajros-src}"

krepko() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
padec()  { printf '\n\033[1;31m%s\033[0m\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || padec "Ta skript rabi root: sudo bash $0"

krepko "predpogoji"
[ -f "$STARA_BAZA" ] || {
    if [ -f "$NOVA_BAZA" ]; then
        echo "   stare baze ni, nova je -- videti je, da je selitev že bila"
        echo "   nadaljujem samo s posodobitvijo kode"
    else
        padec "Ne najdem ne $STARA_BAZA ne $NOVA_BAZA. Ali je to prava naprava?"
    fi
}
[ -d "$VIR/kajros" ] || padec "V '$VIR' ni kode. Najprej z razvojnega računalnika:
    rsync -az --exclude venv --exclude data --exclude .git ./ david@192.168.1.166:~/kajros-src/"

if [ -f "$STARA_BAZA" ]; then
    VELIKOST=$(stat -c%s "$STARA_BAZA")
    PROSTO=$(df -B1 --output=avail /var/lib | tail -1)
    printf "   baza %d MB, prosto %d MB\n" $((VELIKOST/1000000)) $((PROSTO/1000000))
    # Selitev je `mv` znotraj istega diska, torej prostora ne rabi. Rabi ga
    # varnostna kopija, ki jo naredimo spodaj -- in ta je pogoj, ne izbira.
    [ "$PROSTO" -gt "$((VELIKOST + 500000000))" ] \
        || padec "Premalo prostora za varnostno kopijo pred selitvijo."
fi

krepko "kaj teče zdaj"
systemctl is-active sztrack-zajem.service >/dev/null 2>&1 \
    && echo "   sztrack-zajem: teče" || echo "   sztrack-zajem: ne teče"

if [ -f "$STARA_BAZA" ]; then
    krepko "varnostna kopija pred selitvijo"
    # `.backup` in ne `cp`: baza je v WAL in gola datoteka nima zadnjih zapisov.
    KOPIJA="$STARI_DATA/backup/pred-selitvijo-$(date +%Y%m%d-%H%M).sqlite"
    install -d -o sztrack -g sztrack "$STARI_DATA/backup"
    sqlite3 "$STARA_BAZA" ".backup $KOPIJA"
    gzip -1 "$KOPIJA"
    ls -la "$KOPIJA.gz"

    krepko "koliko je v bazi PRED selitvijo"
    PRED=$(sqlite3 "file:$STARA_BAZA?mode=ro" "SELECT COUNT(*) FROM run;")
    echo "   meritev: $PRED"
else
    PRED=""
fi

krepko "namestitev (to je dolg korak)"
KAJROS_MODE=zajem KAJROS_SRC="$VIR" bash "$VIR/deploy/install-rpi.sh"

krepko "preverjam izid"
[ -f "$NOVA_BAZA" ] || padec "Baze na novi poti ni: $NOVA_BAZA"
if [ -n "$PRED" ]; then
    PO=$(sqlite3 "file:$NOVA_BAZA?mode=ro" "SELECT COUNT(*) FROM run;")
    echo "   meritev: $PRED -> $PO"
    [ "$PO" -ge "$PRED" ] || padec "Po selitvi je meritev MANJ. Ustavi se in poglej."
fi
systemctl is-enabled sztrack-zajem.service >/dev/null 2>&1 \
    && echo "   POZOR: sztrack-zajem je še vedno omogočen" \
    || echo "   sztrack-zajem: onemogočen (prav)"
systemctl is-active kajros-zajem.service >/dev/null 2>&1 \
    && echo "   kajros-zajem: teče (prav)" \
    || padec "kajros-zajem ne teče. Poglej: journalctl -u kajros-zajem -n 50"

krepko "gotovo"
cat <<KONEC
   Vozni red se osveži sam ob 4:00 (KAJROS_REFRESH_HOUR), v podprocesu.
   Do takrat so v bazi še stari zapisi o vožnjah -- meritve so cele.

   Mestni LPP je v enoti IZKLOPLJEN (KAJROS_LPP=0), ker cena na Pi Zero W
   ni izmerjena. Ko bo, se vklopi v deploy/kajros-zajem.service.

   Ostanke starih namestitev lahko zdaj pobrišeš:
     rm -rf ~/sztrack ~/sztrack-src ~/sztrack-deploy.zip
     sudo rm -rf /opt/sztrack
   Pusti: ~/kajros-zgodovina (git bundle) in $STARI_DATA/backup (kopije).
KONEC
