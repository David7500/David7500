#!/usr/bin/env bash
# Namestitev kajrosa na Raspberry Pi (ali katerikoli Debian/Ubuntu stroj).
#
#   curl -fsSL <raw-url>/deploy/install-rpi.sh | sudo bash
#   ali:  sudo bash deploy/install-rpi.sh
#
# KAJROS_MODE=zajem namesti SAMO zajem, brez strežnika:
#
#   sudo KAJROS_MODE=zajem bash deploy/install-rpi.sh
#
# KAJROS_AGENCIES pove, katere prevoznike zajemati (prazno = samo SŽ):
#
#   sudo KAJROS_MODE=zajem KAJROS_AGENCIES=1118,1123,1119,1121 bash deploy/install-rpi.sh
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

REPO="${KAJROS_REPO:-https://github.com/David7500/David7500.git}"
BRANCH="${KAJROS_BRANCH:-claude/slovenske-zeleznice-api-ql84hf}"
APP=/opt/kajros
DATA=/var/lib/kajros
MODE="${KAJROS_MODE:-polno}"
# Prevozniki. Prazno = samo SŽ. `1118,1123,1119,1121` = vsi (LPP, Arriva,
# Nomago, AP Murska Sobota). Sprememba te vrednosti sproži ponovni uvoz
# voznega reda -- brez tega bi ETag rekel "nespremenjeno" in avtobusov ne bi bilo.
AGENCIES="${KAJROS_AGENCIES-__ohrani__}"
# Katera storitev je "ta prava". Doloceno tu, ker jo rabi ze varovalka pri
# uvozu voznega reda -- ta zajem ustavi in ga mora znati prizgati nazaj.
if [ "${KAJROS_MODE:-polno}" = "zajem" ]; then
    UNIT=kajros-zajem.service
    DRUGA=kajros.service
else
    UNIT=kajros.service
    DRUGA=kajros-zajem.service
fi

[ "$(id -u)" -eq 0 ] || { echo "Poženi kot root (sudo)."; exit 1; }

# Kadar skripta lezi v polnem izvornem drevesu, je TO vir -- ne GitHub.
# Brez tega je pozabljen `KAJROS_SRC=` tiho pomenil `git clone` cez vse: koda,
# ki na GitHubu se ni, je izginila in `kajros-zajem.service` z njo.
HERE=$(cd "$(dirname "$0")/.." 2>/dev/null && pwd || echo "")
if [ -z "${KAJROS_SRC:-}" ] && [ -n "$HERE" ] && [ -d "$HERE/kajros" ] \
   && [ -f "$HERE/deploy/kajros-zajem.service" ] && [ "$HERE" != "$APP" ]; then
    KAJROS_SRC="$HERE"
    echo "==> vir: $KAJROS_SRC (skripta tece iz izvornega drevesa)"
fi

echo "==> paketi"
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip git sqlite3

echo "==> uporabnik in imeniki"
id -u kajros >/dev/null 2>&1 || useradd --system --home "$DATA" --shell /usr/sbin/nologin kajros
install -d -o kajros -g kajros "$DATA" "$DATA/backup"

echo "==> koda"
if [ -n "${KAJROS_SRC:-}" ]; then
    # Koda je ze na stroju (rsync z razvojnega racunalnika). Uporabno, kadar
    # commiti se niso na GitHubu -- brez tega bi jih `git reset --hard` povozil.
    [ -d "$KAJROS_SRC/kajros" ] || { echo "KAJROS_SRC=$KAJROS_SRC ni videti kot kajros"; exit 1; }
    mkdir -p "$APP"
    rm -rf "$APP/.git"
    cp -a "$KAJROS_SRC/." "$APP/"
    echo "    iz $KAJROS_SRC"
elif [ -d "$APP/.git" ]; then
    git -C "$APP" fetch --quiet origin "$BRANCH"
    git -C "$APP" reset --quiet --hard "origin/$BRANCH"
else
    rm -rf "$APP"
    git clone --quiet --branch "$BRANCH" --depth 1 "$REPO" "$APP"
fi

# Ce tu cesa ni, je bil vir napacen. Bolje pasti zdaj kot pustiti storitev,
# ki se ne bo zagnala ob naslednjem ponovnem zagonu.
for f in deploy/kajros.service deploy/kajros-zajem.service \
         deploy/kajros-backup.service deploy/kajros-backup.timer; do
    [ -f "$APP/$f" ] || {
        echo "NAPAKA: v namesceni kodi manjka $f."
        echo "Vir je bil ${KAJROS_SRC:-GitHub ($BRANCH)}. Ce commiti se niso potisnjeni,"
        echo "pozeni z izvornega drevesa:  sudo KAJROS_SRC=~/kajros-src bash ~/kajros-src/deploy/install-rpi.sh"
        exit 1
    }
done

echo "==> odvisnosti"
[ -d "$APP/.venv" ] || python3 -m venv "$APP/.venv"
# Omrezje do piwheels zna zatajiti; retries so ceneje od ponovnega zagona skripte.
PIP="$APP/.venv/bin/pip"
"$PIP" install --quiet --retries 5 --timeout 60 --upgrade pip
"$PIP" install --quiet --retries 5 --timeout 60 -r "$APP/requirements.txt"
chown -R kajros:kajros "$APP"

echo "==> vozni red"
# Preimenovanje projekta 3. 9. 2026: do prve namestitve nove kode je zajem
# pisal v /var/lib/sztrack/sz.sqlite. Brez te selitve bi nova namestitev tam
# ne nasla nicesar, namestila prilozeno seme in zacela zajemati od nule --
# merodajna zgodovina bi ostala osirotela na stari poti in tega nihce ne bi
# opazil, dokler ne bi kdo pogledal stevila meritev. Odstrani po 1. 12. 2026.
STARI_DATA=/var/lib/sztrack
if [ ! -f "$DATA/kajros.sqlite" ] && [ -f "$STARI_DATA/sz.sqlite" ]; then
    echo "==> selim zajem s starega imena ($STARI_DATA -> $DATA)"
    systemctl stop sztrack-zajem 2>/dev/null || true
    systemctl disable sztrack-zajem 2>/dev/null || true
    install -d -o kajros -g kajros "$DATA"
    for pripona in "" "-wal" "-shm"; do
        [ -f "$STARI_DATA/sz.sqlite$pripona" ] \
            && mv "$STARI_DATA/sz.sqlite$pripona" "$DATA/kajros.sqlite$pripona"
    done
    chown kajros:kajros "$DATA"/kajros.sqlite* 2>/dev/null || true
    echo "    preseljeno; stari imenik pustim prazen za vsak primer"
fi

if [ -f "$DATA/kajros.sqlite" ]; then
    echo "    baza že obstaja, puščam pri miru"
elif [ -f "$APP/seed/kajros.sqlite" ]; then
    install -o kajros -g kajros -m 644 "$APP/seed/kajros.sqlite" "$DATA/kajros.sqlite"
    echo "    priložena baza nameščena"
else
    # Rezerva, kadar priloženo bazo kaj izpusti: sestavimo jo na mestu.
    # 41 MB prenosa in nekaj minut na Pi; vrh pomnilnika okoli 54 MB.
    echo "    priložene baze ni -- gradim vozni red iz GTFS (nekaj minut) ..."
    (cd "$APP" && sudo -u kajros env KAJROS_DATA_DIR="$DATA" \
        "$APP/.venv/bin/python" -m kajros.cli update)
fi

echo "==> storitve"
install -m 644 "$APP/deploy/kajros.service" \
               "$APP/deploy/kajros-zajem.service" \
               "$APP/deploy/kajros-backup.service" \
               "$APP/deploy/kajros-backup.timer" /etc/systemd/system/

# Prevozniki gredo v enoto, da preživijo ponovni zagon.
if [ "$AGENCIES" != "__ohrani__" ]; then
    for u in kajros.service kajros-zajem.service; do
        sed -i "s/^Environment=KAJROS_AGENCIES=.*/Environment=KAJROS_AGENCIES=$AGENCIES/" \
            "/etc/systemd/system/$u"
    done
    echo "    prevozniki: ${AGENCIES:-samo SŽ}"
fi
systemctl daemon-reload

# Vozni red mora vsebovati prevoznike, ki jih hocemo zajemati. Uvozimo znova
# samo, kadar kateri manjka -- primerjamo mnozici, ne stevil: stara baza ima
# `agency` NULL pri vseh voznjah, ker je nastala, preden je stolpec obstajal.
# `--force` je nujen: zip je nespremenjen in ETag bi uvoz sicer preskocil.
if [ "$AGENCIES" != "__ohrani__" ] && [ -f "$DATA/kajros.sqlite" ]; then
    if ! "$APP/.venv/bin/python" - "$DATA/kajros.sqlite" "$AGENCIES" <<'PYEOF'
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
        systemctl stop kajros.service kajros-zajem.service 2>/dev/null || true
        # Zajem je zdaj ustavljen. Karkoli spodaj pade, ga moramo prizgati
        # nazaj -- ustavljen zajem je izgubljena zgodovina, ki je ni nikjer.
        trap 'systemctl start "$UNIT" 2>/dev/null || true' EXIT
        (cd "$APP" && sudo -u kajros env KAJROS_DATA_DIR="$DATA" KAJROS_AGENCIES="$AGENCIES" \
             "$APP/.venv/bin/python" -m kajros.cli update --force)
        trap - EXIT
        echo "    zajete meritve ostanejo -- uvoz zamenja samo vozni red"
    fi
fi

# Obe hkrati bi pisali v isto bazo in se prepirali za feed.
systemctl disable --now "$DRUGA" 2>/dev/null || true
systemctl enable --now "$UNIT" kajros-backup.timer
# `enable --now` že delujoče storitve NE restarta, posodobljena koda pa mora
# stopiti v veljavo -- zato restart posebej.
systemctl restart "$UNIT"
sleep 3

echo
systemctl --no-pager --lines=0 status "$UNIT" || true
echo
if [ "$MODE" = "zajem" ]; then
    echo "Gotovo -- samo zajem, brez strežnika. Preveri:"
    echo "  journalctl -u kajros-zajem -f"
    echo "  sqlite3 $DATA/kajros.sqlite 'SELECT COUNT(*) FROM run'"
    echo
    echo "Bazo preneseš na računalnik z:"
    # Pod sudo je `id -un` root; hocemo uporabnika, ki je sudo pognal.
    # V /var/tmp in NE v /tmp: na malini je /tmp tmpfs (214 MB v RAM-u),
    # baza pa je ze cez 368 MB. Kopija bi padla sredi pisanja.
    echo "  ssh ${SUDO_USER:-$(id -un)}@$(hostname -I 2>/dev/null | awk '{print $1}') \\"
    echo "      'sqlite3 $DATA/kajros.sqlite \".backup /var/tmp/kajros.sqlite\"'"
else
    echo "Gotovo. Preveri:"
    echo "  curl -s http://localhost:8000/api/health"
    echo "  journalctl -u kajros -f"
    IP=$(hostname -I 2>/dev/null | awk '{print $1}')
    [ -n "${IP:-}" ] && echo "  iz domačega omrežja: http://$IP:8000/docs"
fi
