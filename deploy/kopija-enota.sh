#!/usr/bin/env bash
# Enkratno, s sudo: enota varnostne kopije na VACUUM INTO in ob 2:40.
# Skripto kopije (`varnostna-kopija-baze.sh`) in enoto prinese `git push`;
# v /etc/systemd/system ju spravi samo sudo.
#
#   ssh -t david@192.168.1.46 'bash ~/kajros/deploy/kopija-enota.sh'
set -euo pipefail
APP=/opt/kajros
if [ ! -f "$APP/deploy/varnostna-kopija-baze.sh" ]; then
  echo "v $APP ni varnostna-kopija-baze.sh -- najprej git push arwen"
  exit 1
fi
sudo install -m 644 "$APP/deploy/kajros-backup.service" \
                    "$APP/deploy/kajros-backup.timer" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart kajros-backup.timer
echo "==> preizkus kopije zdaj (nekaj minut) ..."
sudo systemctl start kajros-backup.service
journalctl -u kajros-backup.service -n 5 --no-pager
systemctl list-timers kajros-backup.timer --no-pager
