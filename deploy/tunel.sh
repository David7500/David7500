#!/usr/bin/env bash
# Imenovani Cloudflarov tunel: kajros.app -> ta stroj, brez odprtih vrat.
#
# Zakaj tunel in ne preusmeritev vrat: `cloudflared` sam vzpostavi izhodno
# povezavo do Cloudflara, zato na usmerjevalniku ni treba odpreti nicesar in
# domaci naslov ostane skrit. Promet pride do nas sele skozi Cloudflarov rob.
#
# Zakaj IMENOVANI in ne hitri: hitri tunel dobi nakljucen `*.trycloudflare.com`
# in umre s procesom. Imenovani ima trajen UUID, svoj DNS zapis in systemd.
#
# Skripta se pozene kot obicajen uporabnik in si sudo vzame sama, kjer ga rabi.
# Idempotentna: ce tunel ze obstaja, ga ne podvoji.
set -euo pipefail

IME="${TUNEL_IME:-kajros}"
DOMENA="${TUNEL_DOMENA:-kajros.app}"
VRATA="${TUNEL_VRATA:-8000}"
CFDIR="$HOME/.cloudflared"

krepko() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

# --- 1. cloudflared --------------------------------------------------------
if ! command -v cloudflared >/dev/null; then
    krepko "namescam cloudflared (Cloudflarov apt vir)"
    # Njihov vir in ne enkraten .deb: to je storitev, izpostavljena internetu,
    # in mora dobivati varnostne popravke skupaj z ostalim sistemom.
    sudo mkdir -p --mode=0755 /usr/share/keyrings
    curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg \
        | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
    echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main' \
        | sudo tee /etc/apt/sources.list.d/cloudflared.list >/dev/null
    sudo apt-get update -qq
    sudo apt-get install -y -qq cloudflared
fi
echo "cloudflared: $(cloudflared --version)"

# --- 2. prijava ------------------------------------------------------------
# Zapise `cert.pem`, s katerim smemo ustvarjati tunele in DNS zapise v coni.
if [ ! -f "$CFDIR/cert.pem" ]; then
    krepko "prijava v Cloudflare"
    echo "Spodaj se izpise naslov. Odpri ga v brskalniku, kjer si prijavljen,"
    echo "in izberi cono $DOMENA."
    cloudflared tunnel login
fi

# --- 3. tunel --------------------------------------------------------------
if cloudflared tunnel list --output json | grep -q "\"name\":\"$IME\""; then
    krepko "tunel '$IME' ze obstaja"
else
    krepko "ustvarjam tunel '$IME'"
    cloudflared tunnel create "$IME"
fi
UUID="$(cloudflared tunnel list --output json \
        | python3 -c "import json,sys;print(next(t['id'] for t in json.load(sys.stdin) if t['name']=='$IME'))")"
echo "UUID: $UUID"

# --- 4. DNS ----------------------------------------------------------------
# `--overwrite-dns`, ker cona ob prenosu z name.coma podeduje A zapis na
# parkirisce (91.195.240.94). Brez tega `route dns` odpove z "record exists".
krepko "DNS: $DOMENA in www.$DOMENA -> tunel"
cloudflared tunnel route dns --overwrite-dns "$IME" "$DOMENA"
cloudflared tunnel route dns --overwrite-dns "$IME" "www.$DOMENA"

# --- 5. nastavitev ---------------------------------------------------------
krepko "pisem /etc/cloudflared/config.yml"
sudo mkdir -p /etc/cloudflared
sudo cp "$CFDIR/$UUID.json" "/etc/cloudflared/$UUID.json"
sudo chmod 600 "/etc/cloudflared/$UUID.json"
sudo tee /etc/cloudflared/config.yml >/dev/null <<YAML
tunnel: $UUID
credentials-file: /etc/cloudflared/$UUID.json

# Ne "localhost": na tem stroju se razresi tudi v ::1, uvicorn pa poslusa na
# 0.0.0.0 in IPv6 ne prevzame -- cloudflared bi vsako drugo povezavo zavrnil.
ingress:
  - hostname: $DOMENA
    service: http://127.0.0.1:$VRATA
  - hostname: www.$DOMENA
    service: http://127.0.0.1:$VRATA
  - service: http_status:404
YAML

# --- 6. storitev -----------------------------------------------------------
krepko "systemd"
if systemctl list-unit-files | grep -q '^cloudflared.service'; then
    sudo systemctl restart cloudflared
else
    sudo cloudflared service install
    sudo systemctl enable --now cloudflared
fi
sleep 5
sudo systemctl --no-pager --lines=5 status cloudflared || true

krepko "preizkus"
for pot in / /api/health; do
    printf '  %-14s ' "$pot"
    curl -s -o /dev/null -w '%{http_code}  %{time_total}s\n' "https://$DOMENA$pot" || echo "se ne odziva"
done
echo
echo "Ce je koda 000 ali 5xx, je DNS se v razsirjanju -- poskusi cez nekaj minut."
