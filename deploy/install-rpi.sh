#!/usr/bin/env bash
# Namestitev sztracka na Raspberry Pi (ali katerikoli Debian/Ubuntu stroj).
#
#   curl -fsSL <raw-url>/deploy/install-rpi.sh | sudo bash
#   ali:  sudo bash deploy/install-rpi.sh
#
# Skripta je idempotentna -- lahko jo poženeš znova za posodobitev.
set -euo pipefail

REPO="${SZ_REPO:-https://github.com/David7500/David7500.git}"
BRANCH="${SZ_BRANCH:-claude/slovenske-zeleznice-api-ql84hf}"
APP=/opt/sztrack
DATA=/var/lib/sztrack

[ "$(id -u)" -eq 0 ] || { echo "Poženi kot root (sudo)."; exit 1; }

echo "==> paketi"
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip git sqlite3

echo "==> uporabnik in imeniki"
id -u sztrack >/dev/null 2>&1 || useradd --system --home "$DATA" --shell /usr/sbin/nologin sztrack
install -d -o sztrack -g sztrack "$DATA" "$DATA/backup"

echo "==> koda"
if [ -d "$APP/.git" ]; then
    git -C "$APP" fetch --quiet origin "$BRANCH"
    git -C "$APP" reset --quiet --hard "origin/$BRANCH"
else
    rm -rf "$APP"
    git clone --quiet --branch "$BRANCH" --depth 1 "$REPO" "$APP"
fi

echo "==> odvisnosti"
[ -d "$APP/.venv" ] || python3 -m venv "$APP/.venv"
"$APP/.venv/bin/pip" install --quiet --upgrade pip
"$APP/.venv/bin/pip" install --quiet -r "$APP/requirements.txt" uvicorn
chown -R sztrack:sztrack "$APP"

echo "==> vozni red"
if [ ! -f "$DATA/sz.sqlite" ]; then
    install -o sztrack -g sztrack -m 644 "$APP/seed/sz.sqlite" "$DATA/sz.sqlite"
    echo "    priložena baza nameščena (obstoječe se nikoli ne povozi)"
else
    echo "    baza že obstaja, puščam pri miru"
fi

echo "==> storitve"
install -m 644 "$APP/deploy/sztrack.service" \
               "$APP/deploy/sztrack-backup.service" \
               "$APP/deploy/sztrack-backup.timer" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now sztrack.service sztrack-backup.timer
sleep 3

echo
systemctl --no-pager --lines=0 status sztrack.service || true
echo
echo "Gotovo. Preveri:"
echo "  curl -s http://localhost:8000/api/health"
echo "  journalctl -u sztrack -f"
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
[ -n "${IP:-}" ] && echo "  iz domačega omrežja: http://$IP:8000/docs"
