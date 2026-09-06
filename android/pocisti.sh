#!/usr/bin/env bash
# Odstrani vsa orodja za Android in dokaze, da ni ostalo nic.
#
# Zahteva je bila: da se da vse pobrisati naenkrat, skupaj z nastavitvami, in
# da racunalnik ne ostane posmetan. Ta skripta to naredi in **preveri**.
#
# Koda aplikacije (`android/app/`) je v gitu in je NE briseva -- tu gre samo
# za orodja, ki so velika in jih je vedno mogoce znova prenesti.
set -euo pipefail

KOREN="${KAJROS_ANDROID:-$HOME/kajros-android}"

if [ -d "$KOREN" ]; then
    echo "brisem $KOREN ($(du -sh "$KOREN" | cut -f1))"
    # Emulator in demon adb tecejo iz te mape; ce ju ne ustavimo, bosta po
    # brisanju tekla naprej iz izbrisanih datotek in drzala vrata 5037.
    "$KOREN/sdk/platform-tools/adb" emu kill >/dev/null 2>&1 || true
    "$KOREN/sdk/platform-tools/adb" kill-server >/dev/null 2>&1 || true
    rm -rf "$KOREN"
else
    echo "$KOREN ne obstaja"
fi

# Znane smeti, ki jih orodja delajo zunaj svoje mape. Vsako brisemo samo, ce
# je res njihova -- `~/.android` ima lahko tudi tuje AVD-je, `~/.java` pa
# nastavitve drugih programov.
echo
echo "preverjam znana mesta zunaj mape:"
for pot in "$HOME/.android" "$HOME/.java" "$HOME/.gradle"; do
    printf "  %-22s " "${pot/#$HOME/~}"
    if [ ! -e "$pot" ]; then
        echo "ni ga ✓"
    elif [ -z "$(find "$pot" -mindepth 1 -not -name 'adbkey*' -not -name 'adb.*' \
                 -not -path '*/.userPrefs*' -not -name 'prefs.xml' 2>/dev/null)" ]; then
        rm -rf "$pot"
        echo "izbrisano (samo ključi oz. nastavitve orodij)"
    else
        echo "PUSTIM -- vsebuje še kaj drugega, poglej sam"
    fi
done
echo
echo "gotovo."
