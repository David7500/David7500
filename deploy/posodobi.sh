#!/usr/bin/env bash
# Vsakdanja posodobitev streznika. BREZ gesla -- glej `deploy/brez-sudo.sh`.
#
# Namenoma NI `install-rpi.sh`: ta je namestitev (apt, uporabnik, enote,
# uvoz voznega reda) in rabi root. Tu gre samo za novo kodo, kar je 99 %
# primerov. Ce se je spremenila shema baze, jo `db.init()` ob zagonu migrira
# sam -- restart je torej dovolj.
set -euo pipefail

VIR="${1:-$HOME/kajros}"
APP=/opt/kajros
PY="$APP/.venv/bin/python"

[ -d "$VIR/kajros" ] || { echo "vir '$VIR' ni videti kot kajros"; exit 1; }

krepko() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

# Kateri commit se namesca. To je edino, kar je bilo vredno v starem
# `~/posodobi.sh` (odstranjen 12. 9. 2026).
#
# Od 17. 9. 2026 kodo v `$VIR` prinese `git push` (`deploy/post-receive`), ki
# to skripto tudi pozene; ta izpis je zato potrditev, da se namesca prav tisto,
# kar si pravkar potisnil. Rocni zagon ostane za ponovno namestitev istega
# commita.
krepko "nameščam commit"
git -C "$VIR" log --oneline -1 2>/dev/null || echo "  (brez git zgodovine)"

krepko "koda: $VIR -> $APP"
# `--delete`, da odstranjena datoteka res izgine; `.venv` in podatki ostanejo.
rsync -a --delete \
    --exclude '.venv/' --exclude 'venv/' --exclude 'data/' --exclude 'backup/' \
    --exclude '__pycache__/' --exclude '*.pyc' --exclude '.git/' \
    "$VIR/" "$APP/"

# Odvisnosti so pet vrstic in se skoraj nikoli ne spremenijo; primerjamo
# vsoto, da `pip` ne tece po nepotrebnem (na tem stroju 4 s).
VSOTA="$APP/.venv/.requirements.sha"
NOVA="$(sha256sum "$APP/requirements.txt" | cut -d' ' -f1)"
if [ "$(cat "$VSOTA" 2>/dev/null || true)" != "$NOVA" ]; then
    krepko "odvisnosti so se spremenile"
    "$APP/.venv/bin/pip" install --quiet -r "$APP/requirements.txt"
    echo "$NOVA" > "$VSOTA"
fi

krepko "restart"
sudo systemctl restart kajros.service

# Cakamo na odgovor, ne na "systemd pravi, da tece": ob napaki v kodi enota
# ostane `active` in se ponavlja vsakih 15 s, kar je videti kot uspeh.
PORT="$(systemctl show kajros -p Environment --value | tr ' ' '\n' | sed -n 's/^PORT=//p')"
PORT="${PORT:-8000}"
for i in $(seq 1 30); do
    if curl -sf -o /dev/null "http://127.0.0.1:$PORT/api/health"; then
        krepko "streznik odgovarja (po $i s)"
        # Brez `\"` v enojnih narekovajih: lupina jih ne odstrani in Python
        # dobi `d[\"trips\"]`, kar je sintaksna napaka. Dvojni narekovaji
        # znotraj enojnih so povsem v redu.
        curl -s "http://127.0.0.1:$PORT/api/health" | "$PY" -c 'import json, sys
d = json.load(sys.stdin)
print("  %s voženj · %s meritev · %s dni"
      % (d["trips"], d["observations"], d["days_covered"]))'
        exit 0
    fi
    sleep 1
done

echo "NE odgovarja po 30 s -- dnevnik:"
journalctl -u kajros -n 25 --no-pager
exit 1
