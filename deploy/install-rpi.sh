#!/usr/bin/env bash
# Namestitev sztracka na Raspberry Pi (ali katerikoli Debian/Ubuntu stroj).
#
#   curl -fsSL <raw-url>/deploy/install-rpi.sh | sudo bash
#   ali:  sudo bash deploy/install-rpi.sh
#
# SZ_MODE=zajem namesti SAMO zajem, brez strežnika:
#
#   sudo SZ_MODE=zajem bash deploy/install-rpi.sh
#
# SZ_AGENCIES pove, katere prevoznike zajemati (prazno = samo SŽ):
#
#   sudo SZ_MODE=zajem SZ_AGENCIES=1118,1123,1119,1121 bash deploy/install-rpi.sh
#
# Ob spremembi te vrednosti se vozni red uvozi znova (sicer bi ETag rekel
# "nespremenjeno" in novih prevoznikov v bazi ne bi bilo).
#
# To je za stroj, ki naj le polni bazo, da lahko računalnik ugasneš. Zajema
# se samo tisto, česar kasneje ni mogoče dobiti -- zamude in obvestila;
# vreme in statistiko izračunaš pozneje tam, kjer je baza.
#
# Skripta je idempotentna -- lahko jo poženeš znova za posodobitev.
set -euo pipefail

REPO="${SZ_REPO:-https://github.com/David7500/David7500.git}"
BRANCH="${SZ_BRANCH:-claude/slovenske-zeleznice-api-ql84hf}"
APP=/opt/sztrack
DATA=/var/lib/sztrack
MODE="${SZ_MODE:-polno}"
# Prevozniki. Prazno = samo SŽ. `1118,1123,1119,1121` = vsi (LPP, Arriva,
# Nomago, AP Murska Sobota). Sprememba te vrednosti sproži ponovni uvoz
# voznega reda -- brez tega bi ETag rekel "nespremenjeno" in avtobusov ne bi bilo.
AGENCIES="${SZ_AGENCIES-__ohrani__}"
# Katera storitev je "ta prava". Doloceno tu, ker jo rabi ze varovalka pri
# uvozu voznega reda -- ta zajem ustavi in ga mora znati prizgati nazaj.
if [ "${SZ_MODE:-polno}" = "zajem" ]; then
    UNIT=sztrack-zajem.service
    DRUGA=sztrack.service
else
    UNIT=sztrack.service
    DRUGA=sztrack-zajem.service
fi

[ "$(id -u)" -eq 0 ] || { echo "Poženi kot root (sudo)."; exit 1; }

# Kadar skripta lezi v polnem izvornem drevesu, je TO vir -- ne GitHub.
# Brez tega je pozabljen `SZ_SRC=` tiho pomenil `git clone` cez vse: koda,
# ki na GitHubu se ni, je izginila in `sztrack-zajem.service` z njo.
HERE=$(cd "$(dirname "$0")/.." 2>/dev/null && pwd || echo "")
if [ -z "${SZ_SRC:-}" ] && [ -n "$HERE" ] && [ -d "$HERE/sztrack" ] \
   && [ -f "$HERE/deploy/sztrack-zajem.service" ] && [ "$HERE" != "$APP" ]; then
    SZ_SRC="$HERE"
    echo "==> vir: $SZ_SRC (skripta tece iz izvornega drevesa)"
fi

echo "==> paketi"
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip git sqlite3

echo "==> uporabnik in imeniki"
id -u sztrack >/dev/null 2>&1 || useradd --system --home "$DATA" --shell /usr/sbin/nologin sztrack
install -d -o sztrack -g sztrack "$DATA" "$DATA/backup"

echo "==> koda"
if [ -n "${SZ_SRC:-}" ]; then
    # Koda je ze na stroju (rsync z razvojnega racunalnika). Uporabno, kadar
    # commiti se niso na GitHubu -- brez tega bi jih `git reset --hard` povozil.
    [ -d "$SZ_SRC/sztrack" ] || { echo "SZ_SRC=$SZ_SRC ni videti kot sztrack"; exit 1; }
    mkdir -p "$APP"
    rm -rf "$APP/.git"
    cp -a "$SZ_SRC/." "$APP/"
    echo "    iz $SZ_SRC"
elif [ -d "$APP/.git" ]; then
    git -C "$APP" fetch --quiet origin "$BRANCH"
    git -C "$APP" reset --quiet --hard "origin/$BRANCH"
else
    rm -rf "$APP"
    git clone --quiet --branch "$BRANCH" --depth 1 "$REPO" "$APP"
fi

# Ce tu cesa ni, je bil vir napacen. Bolje pasti zdaj kot pustiti storitev,
# ki se ne bo zagnala ob naslednjem ponovnem zagonu.
for f in deploy/sztrack.service deploy/sztrack-zajem.service \
         deploy/sztrack-backup.service deploy/sztrack-backup.timer; do
    [ -f "$APP/$f" ] || {
        echo "NAPAKA: v namesceni kodi manjka $f."
        echo "Vir je bil ${SZ_SRC:-GitHub ($BRANCH)}. Ce commiti se niso potisnjeni,"
        echo "pozeni z izvornega drevesa:  sudo SZ_SRC=~/sztrack-src bash ~/sztrack-src/deploy/install-rpi.sh"
        exit 1
    }
done

echo "==> odvisnosti"
[ -d "$APP/.venv" ] || python3 -m venv "$APP/.venv"
# Omrezje do piwheels zna zatajiti; retries so ceneje od ponovnega zagona skripte.
PIP="$APP/.venv/bin/pip"
"$PIP" install --quiet --retries 5 --timeout 60 --upgrade pip
"$PIP" install --quiet --retries 5 --timeout 60 -r "$APP/requirements.txt"
chown -R sztrack:sztrack "$APP"

echo "==> vozni red"
if [ -f "$DATA/sz.sqlite" ]; then
    echo "    baza že obstaja, puščam pri miru"
elif [ -f "$APP/seed/sz.sqlite" ]; then
    install -o sztrack -g sztrack -m 644 "$APP/seed/sz.sqlite" "$DATA/sz.sqlite"
    echo "    priložena baza nameščena"
else
    # Rezerva, kadar priloženo bazo kaj izpusti: sestavimo jo na mestu.
    # 41 MB prenosa in nekaj minut na Pi; vrh pomnilnika okoli 54 MB.
    echo "    priložene baze ni -- gradim vozni red iz GTFS (nekaj minut) ..."
    (cd "$APP" && sudo -u sztrack env SZ_DATA_DIR="$DATA" \
        "$APP/.venv/bin/python" -m sztrack.cli update)
fi

echo "==> storitve"
install -m 644 "$APP/deploy/sztrack.service" \
               "$APP/deploy/sztrack-zajem.service" \
               "$APP/deploy/sztrack-backup.service" \
               "$APP/deploy/sztrack-backup.timer" /etc/systemd/system/

# Prevozniki gredo v enoto, da preživijo ponovni zagon.
if [ "$AGENCIES" != "__ohrani__" ]; then
    for u in sztrack.service sztrack-zajem.service; do
        sed -i "s/^Environment=SZ_AGENCIES=.*/Environment=SZ_AGENCIES=$AGENCIES/" \
            "/etc/systemd/system/$u"
    done
    echo "    prevozniki: ${AGENCIES:-samo SŽ}"
fi
systemctl daemon-reload

# Vozni red mora vsebovati prevoznike, ki jih hocemo zajemati. Uvozimo znova
# samo, kadar kateri manjka -- primerjamo mnozici, ne stevil: stara baza ima
# `agency` NULL pri vseh voznjah, ker je nastala, preden je stolpec obstajal.
# `--force` je nujen: zip je nespremenjen in ETag bi uvoz sicer preskocil.
if [ "$AGENCIES" != "__ohrani__" ] && [ -f "$DATA/sz.sqlite" ]; then
    if ! "$APP/.venv/bin/python" - "$DATA/sz.sqlite" "$AGENCIES" <<'PYEOF'
import sqlite3, sys
db, want = sys.argv[1], sys.argv[2]
zeleznica = "1161"          # config.RAIL_AGENCY_ID
hoceno = {zeleznica} | {a.strip() for a in want.split(",") if a.strip()}
c = sqlite3.connect(db)
imamo = {r[0] for r in c.execute("SELECT DISTINCT agency FROM trip") if r[0]}
manjka = hoceno - imamo
print(f"    v bazi: {', '.join(sorted(imamo)) or 'brez oznak (stara shema)'}")
sys.exit(1 if manjka else 0)
PYEOF
    then
        echo "==> vozni red nima vseh prevoznikov -- uvazam znova"
        echo "    (na Pi Zero nekaj minut; vrh pomnilnika ~217 MB pri vseh stirih)"
        systemctl stop sztrack.service sztrack-zajem.service 2>/dev/null || true
        # Zajem je zdaj ustavljen. Karkoli spodaj pade, ga moramo prizgati
        # nazaj -- ustavljen zajem je izgubljena zgodovina, ki je ni nikjer.
        trap 'systemctl start "$UNIT" 2>/dev/null || true' EXIT
        (cd "$APP" && sudo -u sztrack env SZ_DATA_DIR="$DATA" SZ_AGENCIES="$AGENCIES" \
             "$APP/.venv/bin/python" -m sztrack.cli update --force)
        trap - EXIT
        echo "    zajete meritve ostanejo -- uvoz zamenja samo vozni red"
    fi
fi

# Obe hkrati bi pisali v isto bazo in se prepirali za feed.
systemctl disable --now "$DRUGA" 2>/dev/null || true
systemctl enable --now "$UNIT" sztrack-backup.timer
# `enable --now` že delujoče storitve NE restarta, posodobljena koda pa mora
# stopiti v veljavo -- zato restart posebej.
systemctl restart "$UNIT"
sleep 3

echo
systemctl --no-pager --lines=0 status "$UNIT" || true
echo
if [ "$MODE" = "zajem" ]; then
    echo "Gotovo -- samo zajem, brez strežnika. Preveri:"
    echo "  journalctl -u sztrack-zajem -f"
    echo "  sqlite3 $DATA/sz.sqlite 'SELECT COUNT(*) FROM run'"
    echo
    echo "Bazo preneseš na računalnik z:"
    echo "  ssh $(id -un 2>/dev/null || echo david)@\$(hostname -I | awk '{print \$1}') \\"
    echo "      'sqlite3 $DATA/sz.sqlite \".backup /tmp/sz.sqlite\"'"
else
    echo "Gotovo. Preveri:"
    echo "  curl -s http://localhost:8000/api/health"
    echo "  journalctl -u sztrack -f"
    IP=$(hostname -I 2>/dev/null | awk '{print $1}')
    [ -n "${IP:-}" ] && echo "  iz domačega omrežja: http://$IP:8000/docs"
fi
