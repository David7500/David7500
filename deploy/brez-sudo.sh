#!/usr/bin/env bash
# ENKRATNA nastavitev: po njej posodobitev streznika ne rabi vec gesla.
#
# Doslej je vsaka posodobitev sla skozi `install-rpi.sh` z rootom, ker je
# `/opt/kajros` pripadal uporabniku `kajros` in je bilo treba restartati
# storitev. Oboje se da odpraviti, ne da bi kdorkoli dobil root.
#
# Kaj naredi:
#   1. `david` dobi lastnistvo kode (`/opt/kajros`) -- rsync brez sudota.
#   2. `david` gre v skupino `kajros` in podatkovni imenik postane skupinsko
#      pisljiv -- `merge`, `repair` in `zapolni-vrzel.sh` brez `sudo -u`.
#   3. sudoers dovoli TOCNO stiri ukaze systemctl brez gesla, nic drugega.
#
# Kaj to pomeni za varnost, pošteno povedano: `david` (in kdorkoli ima njegov
# SSH kljuc) lahko odslej brez gesla pozene kodo kot uporabnik `kajros` in
# pise v bazo. To NI root -- `kajros` ima v lasti samo `/opt/kajros` in
# `/var/lib/kajros`, ima `NoNewPrivileges=true` in ne more nic drugega.
# Ker je `david` ze sudoer, mu to ne da nobene nove moci; odpade samo poziv
# za geslo pri teh stirih ukazih.
#
# Storitev ostane pod SVOJIM uporabnikom. Preprostejsa moznost bi bila
# pognati vse kot `david`, a bi to javno izpostavljen proces spustilo v
# domaci imenik -- `ProtectHome=true` v enoti obstaja z razlogom.
set -euo pipefail

UPORABNIK="${SUDO_USER:-$USER}"
APP=/opt/kajros
DATA=/var/lib/kajros
PRAVILA=/etc/sudoers.d/kajros-posodobitev

[ "$(id -u)" -eq 0 ] || { echo "Poženi z: sudo bash $0"; exit 1; }

krepko() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

krepko "1/4  koda: $APP -> $UPORABNIK:kajros"
chown -R "$UPORABNIK":kajros "$APP"
# Skupina samo bere: storitev kode ne piše, in kar ne piše, naj ne more.
chmod -R g+rX,o-w "$APP"

krepko "2/4  podatki: skupina kajros sme pisati"
usermod -aG kajros "$UPORABNIK"
chgrp -R kajros "$DATA"
chmod -R g+rwX "$DATA"
# setgid na imenikih: karkoli nastane pozneje, ostane v skupini `kajros`.
# Brez tega bi datoteka, ki jo naredi `david`, pripadla skupini `david` in
# je storitev ne bi mogla pisati -- napaka bi se pokazala sele cez dneve.
find "$DATA" -type d -exec chmod g+s {} +

krepko "3/4  storitev naj nove datoteke dela skupinsko pisljive"
# Privzeti umask 022 bi WAL in nove kopije naredil samo za branje skupine.
mkdir -p /etc/systemd/system/kajros.service.d
cat > /etc/systemd/system/kajros.service.d/umask.conf <<'EOF'
# Baza je v skupni rabi s clovekom (skupina `kajros`), zato 002 in ne 022.
[Service]
UMask=0002
EOF
systemctl daemon-reload

krepko "4/4  sudoers: štirje ukazi brez gesla"
# Najprej preveri, sele nato namesti. Sintaksna napaka v katerikoli datoteki
# v sudoers.d podre sudo na CELEM stroju -- validacija tu ni formalnost.
ZACASNO="$(mktemp)"
cat > "$ZACASNO" <<EOF
# kajros: posodobitev streznika brez gesla. Samo ti ukazi, dobesedno.
$UPORABNIK ALL=(root) NOPASSWD: /usr/bin/systemctl start kajros.service, \\
    /usr/bin/systemctl stop kajros.service, \\
    /usr/bin/systemctl restart kajros.service, \\
    /usr/bin/systemctl restart cloudflared.service
EOF
if visudo -cf "$ZACASNO"; then
    install -m 0440 -o root -g root "$ZACASNO" "$PRAVILA"
    echo "namesceno: $PRAVILA"
else
    echo "NAPAKA: sudoers ni veljaven, ne namescam nicesar"
    rm -f "$ZACASNO"
    exit 1
fi
rm -f "$ZACASNO"

krepko "gotovo"
echo "Odslej: bash ~/kajros/deploy/posodobi.sh   (brez gesla)"
echo
echo "Clanstvo v skupini velja od NASLEDNJE prijave -- tekoce seje ga se"
echo "nimajo. Preveri z:  ssh $UPORABNIK@localhost id -nG"
