#!/usr/bin/env bash
# Zgradi podpisan APK in ga objavi za prenos na kajros.app/android.
#
#     ./objavi.sh            zgradi, podpiši, pripravi lokalno
#     ./objavi.sh posreduj   isto in pošlji na strežnik (arwen)
#
# Trgovine ni namenoma: glavni F-Droid zahteva prosto licenco (koda je
# zaprta), Play pa račun, 25 $, preverjanje identitete in dva tedna zaprtega
# preizkusa z dvanajstimi ljudmi. Prenos s strani dela danes in za vsakogar.
#
# Podpisni ključ je trajna identiteta aplikacije: telefon sprejme posodobitev
# samo, če je podpisana z istim ključem. Živi v ~/kajros-android/podpis/ in
# NE v repozitoriju; brez varnostne kopije posodobitev ni več mogoča.
set -euo pipefail
cd "$(dirname "$0")"

KOREN="${KAJROS_ANDROID:-$HOME/kajros-android}"
IZHOD="${KAJROS_PRENOS:-$KOREN/prenos}"
STREZNIK="${KAJROS_STREZNIK:-david@192.168.1.46}"
STREZNIK_MAPA="${KAJROS_STREZNIK_PRENOS:-/var/lib/kajros/prenos}"

[ -f "$KOREN/podpis/podpis.properties" ] || {
    echo "Podpisnega ključa ni. Poženi najprej:  ./podpis.sh" >&2
    exit 1
}

# 1. Testi in podpisan APK. `zgradi.sh` izpiše tudi prstni odtis podpisa.
./zgradi.sh testi
./zgradi.sh izdaja
APK="app/build/outputs/apk/release/app-release.apk"
[ -f "$APK" ] || { echo "Podpisanega APK-ja ni: $APK" >&2; exit 1; }

# 2. Kaj je v njem. Številke beremo iz APK-ja, ne iz `build.gradle.kts`:
# objaviti različico, ki ni ta, ki je zgrajena, je tiha napaka.
BT="$(ls -d "$KOREN/sdk/build-tools"/* | sort -V | tail -1)"
BADGING="$("$BT/aapt2" dump badging "$APK")"
KODA="$(sed -n "s/.*versionCode='\([0-9]*\)'.*/\1/p" <<<"$BADGING" | head -1)"
IME="$(sed -n "s/.*versionName='\([^']*\)'.*/\1/p" <<<"$BADGING" | head -1)"
DATOTEKA="kajros-$IME.apk"

mkdir -p "$IZHOD"
cp "$APK" "$IZHOD/$DATOTEKA"
VSOTA="$(sha256sum "$IZHOD/$DATOTEKA" | cut -d' ' -f1)"
BAJTOV="$(stat -c%s "$IZHOD/$DATOTEKA")"

# 3. Opis izdaje. Bere ga stran `/android` in aplikacija sama
# (`/api/android/razlicica`), da ve, ali je na voljo kaj novejšega.
cat > "$IZHOD/razlicica.json" <<EOF
{
  "koda": $KODA,
  "ime": "$IME",
  "datoteka": "$DATOTEKA",
  "sha256": "$VSOTA",
  "bajtov": $BAJTOV,
  "objavljeno": "$(date +%Y-%m-%d)"
}
EOF

echo
echo "  različica $IME ($KODA) · $((BAJTOV / 1024)) kB"
echo "  sha256    $VSOTA"
echo "  mapa      $IZHOD"

# 4. Stare izdaje ostanejo: kdor ima povezavo do nje, jo mora dobiti tudi
# jutri, in vrnitev na prejšnjo je edina pot nazaj ob slabi izdaji.
ls -1 "$IZHOD"/*.apk | sed 's/^/  /'

if [ "${1:-}" = "posreduj" ]; then
    echo
    echo "Pošiljam na $STREZNIK:$STREZNIK_MAPA"
    # Mapa je v podatkovnem imeniku, ki je skupinsko pisljiv -- brez sudota.
    ssh "$STREZNIK" "mkdir -p $STREZNIK_MAPA"
    # Brez `--delete`: stare izdaje na strežniku ostanejo.
    rsync -av "$IZHOD/" "$STREZNIK:$STREZNIK_MAPA/"
    # Mount `/prenos` nastane ob zagonu; ob PRVI objavi ga torej še ni.
    ssh "$STREZNIK" "sudo systemctl restart kajros.service"
    echo
    echo "Objavljeno: ${KAJROS_BASE_URL:-https://kajros.app}/android"
else
    echo
    echo "Za objavo:  ./objavi.sh posreduj"
fi
