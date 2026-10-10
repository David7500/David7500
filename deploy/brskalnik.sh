#!/usr/bin/env bash
# Chrome in navidezni zaslon za branje potniski.sz.si (`kajros/brskalnik.py`).
# Rabi sudo, enkrat; posodobitve Chroma nato prinaša `apt upgrade`.
#
#   ssh -t david@192.168.1.46 'sudo bash ~/kajros/deploy/brskalnik.sh'
#
# Zakaj: zamude vlakov in tire beremo naravnost s strani SŽ. Ta je za
# Cloudflarom, ki od 7. 10. 2026 spusti samo Chrome z oknom -- brezglavega ne.
# Na strežniku brez zaslona mu okno da Xvfb.
#
# Zakaj Google Chrome in ne Chromium: na Ubuntuju je Chromium samo snap, Chrome
# pa je paket v /opt/google/chrome, ki ga profil AppArmor `/etc/apparmor.d/chrome`
# (paket apparmor) že pozna -- brez njega Ubuntu 24.04 Chromu ne dovoli
# peskovnika (`kernel.apparmor_restrict_unprivileged_userns = 1`). Paket doda
# Googlov repozitorij APT, zato se posodablja z ostalim sistemom; star Chrome
# bi Cloudflare prej ali slej zavrnil.
#
# Kaj spremeni na stroju (stroj ni naš, zato našteto): paketa `xvfb` in
# `google-chrome-stable`, vir APT `/etc/apt/sources.list.d/google-chrome.list`
# z Googlovim ključem. Enote `kajros.service` ne spremeni.
#
# Na koncu preizkus v ISTEM peskovniku kot storitev (uporabnik `kajros`,
# NoNewPrivileges, ProtectSystem=strict ...), nato restart strežnika.
set -euo pipefail

[ "$(id -u)" = 0 ] || { echo "poženi s sudo: sudo bash $0"; exit 1; }
[ "$(dpkg --print-architecture)" = amd64 ] || { echo "Google Chrome je samo za amd64 (malina ga ne more imeti)"; exit 1; }

krepko() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

krepko "Xvfb"
if command -v Xvfb >/dev/null; then
    echo "  že nameščen: $(command -v Xvfb)"
else
    apt-get update -qq
    apt-get install -y -qq xvfb
fi

krepko "Google Chrome"
if command -v google-chrome-stable >/dev/null; then
    echo "  že nameščen: $(google-chrome-stable --version)"
else
    TMP="$(mktemp -d)"
    trap 'rm -rf "$TMP"' EXIT
    curl -fsSL -o "$TMP/chrome.deb" \
        https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    # `apt-get install ./…` razreši odvisnosti; paket sam doda svoj vir APT.
    apt-get install -y -qq "$TMP/chrome.deb"
    echo "  $(google-chrome-stable --version)"
fi

krepko "AppArmor"
if grep -qs '/opt/google/chrome/chrome' /etc/apparmor.d/chrome; then
    echo "  profil /etc/apparmor.d/chrome pozna Chrome: peskovnik dela"
else
    echo "  OPOZORILO: profila AppArmor za /opt/google/chrome/chrome ni;"
    echo "  Chrome se brez peskovnika ne zažene (\`apt install apparmor\` ga prinese)."
fi

krepko "preizkus kot storitev"
# Isti peskovnik kot `deploy/kajros.service`; razlika bi se sicer pokazala šele
# v storitvi, kjer napako vidi samo /admin.
if systemd-run --quiet --wait --pipe --collect \
        -p User=kajros -p Group=kajros -p WorkingDirectory=/opt/kajros \
        -p NoNewPrivileges=yes -p PrivateTmp=yes -p ProtectSystem=strict \
        -p ProtectHome=yes -p ReadWritePaths=/var/lib/kajros \
        -E KAJROS_DATA_DIR=/var/lib/kajros \
        /opt/kajros/.venv/bin/python -m kajros.cli brskalnik; then
    krepko "restart strežnika"
    systemctl restart kajros.service
    echo "  V /admin, zavihek Viri: kartica „zemljevid SŽ“ in vrstica „brskalnik“."
else
    echo
    echo "Preizkus ni uspel -- strežnika ne zaganjam znova. Izpis zgoraj pove, kje."
    exit 1
fi
