#!/usr/bin/env bash
# Naredi podpisni ključ za izdajne APK-je.
#
#     ./podpis.sh            naredi ključ, če ga še ni
#     ./podpis.sh prstni     izpiše prstni odtis obstoječega ključa
#
# Ključ NE gre v repozitorij. Živi pri orodjih (`~/kajros-android/podpis/`),
# ker je trajna identiteta aplikacije: telefon sprejme posodobitev samo, če je
# podpisana z istim ključem kot nameščena različica. Izgubljen ključ pomeni,
# da mora vsak uporabnik aplikacijo odstraniti in namestiti znova.
set -euo pipefail
cd "$(dirname "$0")"

KOREN="${KAJROS_ANDROID:-$HOME/kajros-android}"
MAPA="${KAJROS_PODPIS:-$KOREN/podpis}"
SHRAMBA="$MAPA/kajros.jks"
LASTNOSTI="$MAPA/podpis.properties"
VZDEVEK="kajros"

if [ ! -f "$KOREN/okolje.sh" ]; then
    echo "Orodij ni. Poženi najprej: ./orodja.sh" >&2
    exit 1
fi
# shellcheck disable=SC1090
source "$KOREN/okolje.sh"

if [ "${1:-naredi}" = "prstni" ]; then
    [ -f "$SHRAMBA" ] || { echo "Ključa ni: $SHRAMBA" >&2; exit 1; }
    keytool -list -v -keystore "$SHRAMBA" -alias "$VZDEVEK" \
        -storepass "$(sed -n 's/^geslo=//p' "$LASTNOSTI")" \
        | grep -E 'Valid from|SHA-?256'
    exit 0
fi

if [ -f "$SHRAMBA" ]; then
    echo "Ključ že obstaja: $SHRAMBA"
    echo "Novega ne delam — zamenjava ključa razveljavi vse nameščene aplikacije."
    exit 0
fi

# Geslo iz okolja (za neinteraktivno rabo) ali vprašano dvakrat.
if [ -n "${KAJROS_GESLO:-}" ]; then
    GESLO="$KAJROS_GESLO"
else
    read -rsp "Geslo za ključ (vsaj 6 znakov): " GESLO; echo
    read -rsp "Še enkrat: " GESLO2; echo
    [ "$GESLO" = "$GESLO2" ] || { echo "Gesli se ne ujemata." >&2; exit 1; }
fi
[ "${#GESLO}" -ge 6 ] || { echo "Geslo mora imeti vsaj 6 znakov." >&2; exit 1; }

mkdir -p "$MAPA"
chmod 700 "$MAPA"

# 10 000 dni (27 let): ključ, ki poteče, pomeni aplikacijo brez posodobitev.
# RSA 4096, ker je podpis enkraten strošek ob gradnji, ne ob zagonu.
keytool -genkeypair \
    -keystore "$SHRAMBA" -storetype PKCS12 \
    -alias "$VZDEVEK" -keyalg RSA -keysize 4096 -validity 10000 \
    -storepass "$GESLO" -keypass "$GESLO" \
    -dname "CN=Kajros, OU=Kajros, O=Kajros, L=Ljubljana, C=SI"

# `keytool` datoteko naredi po svoje (644) in `umask` spodaj je zanjo prepozen.
chmod 600 "$SHRAMBA"

umask 077
cat > "$LASTNOSTI" <<EOF
# Bere ga app/build.gradle.kts. Pravice 600, zunaj repozitorija.
shramba=kajros.jks
vzdevek=$VZDEVEK
geslo=$GESLO
EOF
chmod 600 "$LASTNOSTI"

echo
echo "Ključ narejen: $SHRAMBA"
keytool -list -v -keystore "$SHRAMBA" -alias "$VZDEVEK" -storepass "$GESLO" \
    | grep -E 'Valid from|SHA-?256' | sed 's/^/  /'
echo
echo "VARNOSTNA KOPIJA: prekopiraj $MAPA na drug medij, ŠE PREDEN objaviš prvi APK."
echo "Brez nje posodobitev ni mogoča — uporabniki bi morali aplikacijo odstraniti."
