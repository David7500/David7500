#!/usr/bin/env bash
# Pospravi malino PO uspešni selitvi na `kajros`. Poženi z rootom:
#
#     sudo bash ~/kajros-koda/deploy/pospravi-malino.sh
#
# Vse tri stvari tu so take, da jih agent ne more narediti sam (rabijo root)
# in nobena ni nujna za delovanje -- so pa razlog, da je na stroju nered.
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "Rabi root: sudo bash $0" >&2; exit 1; }

krepko() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

krepko "varovalka: selitev mora biti končana"
[ -f /var/lib/kajros/kajros.sqlite ] || {
    echo "Nove baze ni -- selitev ni bila uspešna. Ne pospravljam." >&2; exit 1; }
systemctl is-active --quiet kajros-zajem.service || {
    echo "kajros-zajem ne teče. Najprej to popravi, šele potem pospravi." >&2; exit 1; }

krepko "stari časovnik za kopije"
# Po premiku baze kaze na /var/lib/sztrack/sz.sqlite, ki je ni vec.
systemctl disable --now sztrack-backup.timer 2>/dev/null || true
systemctl disable --now sztrack-zajem.service 2>/dev/null || true
rm -f /etc/systemd/system/sztrack-*.service /etc/systemd/system/sztrack-*.timer \
      /etc/systemd/system/sztrack.service
systemctl daemon-reload
echo "   odstranjene stare enote"

krepko "časovni pas"
# Malina je tekla v Europe/London. Zajem to prenese -- koda povsod uporablja
# Europe/Ljubljana -- a dnevniki in systemd casovniki so bili premaknjeni za
# uro, kar je pri iskanju napake zavajajoce.
if [ "$(timedatectl show -p Timezone --value)" != "Europe/Ljubljana" ]; then
    timedatectl set-timezone Europe/Ljubljana
    echo "   nastavljen Europe/Ljubljana"
else
    echo "   je že Europe/Ljubljana"
fi

krepko "stara koda"
rm -rf /opt/sztrack
echo "   /opt/sztrack odstranjen"

krepko "gotovo"
echo "   Merodajno ostaja: /opt/kajros, /var/lib/kajros"
echo "   Stare kopije baze so v /var/lib/sztrack/backup -- pusti jih ali pobriši sam."
