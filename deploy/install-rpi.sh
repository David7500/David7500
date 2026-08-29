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

[ "$(id -u)" -eq 0 ] || { echo "Poženi kot root (sudo)."; exit 1; }

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
    sudo -u sztrack env SZ_DATA_DIR="$DATA" "$APP/.venv/bin/python" -m sztrack.cli update
fi

echo "==> storitve"
install -m 644 "$APP/deploy/sztrack.service" \
               "$APP/deploy/sztrack-zajem.service" \
               "$APP/deploy/sztrack-backup.service" \
               "$APP/deploy/sztrack-backup.timer" /etc/systemd/system/
systemctl daemon-reload

if [ "$MODE" = "zajem" ]; then
    UNIT=sztrack-zajem.service
    # Obe hkrati bi pisali v isto bazo in se prepirali za feed.
    systemctl disable --now sztrack.service 2>/dev/null || true
else
    UNIT=sztrack.service
    systemctl disable --now sztrack-zajem.service 2>/dev/null || true
fi
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
