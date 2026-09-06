#!/usr/bin/env bash
# Zgradi APK in dokaze, da gradnja ni nicesar pustila zunaj svoje mape.
#
#     ./zgradi.sh            testi JVM + razvojni APK
#     ./zgradi.sh namesti    zgradi in namesti na priklopljen telefon
#     ./zgradi.sh testi      samo testi JVM, brez naprave
#     ./zgradi.sh izdaja     izdajni APK (nepodpisan) -- za merjenje velikosti
#     ./zgradi.sh emulator   zazene emulator (KAJROS_EMULATOR=1 ./orodja.sh)
#     ./zgradi.sh ustavi     ugasne emulator
#
# Orodja so v ~/kajros-android in jih tu samo nalozimo.
set -euo pipefail
cd "$(dirname "$0")"

KOREN="${KAJROS_ANDROID:-$HOME/kajros-android}"
if [ ! -f "$KOREN/okolje.sh" ]; then
    echo "Orodij ni. Poženi najprej: ./orodja.sh" >&2
    exit 1
fi
# shellcheck disable=SC1090
source "$KOREN/okolje.sh"

# Isti dokaz kot v orodja.sh, in iz istega razloga: AGP je ze enkrat naredil
# `~/.android/analytics.settings` z obstojnim `userId` kljub vsem nastavitvam.
# Tega ne lovimo enkrat, ampak ob vsaki gradnji.
PREJ="$(mktemp)"; LC_ALL=C ls -A "$HOME" | LC_ALL=C sort > "$PREJ"

UKAZ="${1:-zgradi}"
case "$UKAZ" in
    testi)   gradle --console=plain :app:testDebugUnitTest ;;
    emulator)
        if ! avdmanager list avd 2>/dev/null | grep -q "Name: kajros"; then
            echo "AVD-ja ni. Poženi: KAJROS_EMULATOR=1 ./orodja.sh" >&2; exit 1
        fi
        # `-no-window`: posnetke jemljemo z `adb exec-out screencap`, okna ne
        # rabimo, brez njega pa emulator ne rabi zaslona sploh.
        nohup emulator -avd kajros -no-window -no-audio -no-boot-anim \
            -no-snapshot -gpu swiftshader_indirect -memory 2048 \
            > "$KOREN/tmp/emulator.log" 2>&1 &
        disown
        echo "zaganjam; počakaj z:  adb wait-for-device shell 'while [ \"\$(getprop sys.boot_completed)\" != 1 ]; do sleep 2; done'"
        exit 0
        ;;
    ustavi)  adb emu kill 2>/dev/null || true; echo "ugasnjen"; exit 0 ;;
    izdaja)  gradle --console=plain :app:assembleRelease ;;
    namesti)
        gradle --console=plain :app:testDebugUnitTest :app:assembleDebug
        adb install -r app/build/outputs/apk/debug/app-debug.apk
        adb shell monkey -p app.kajros -c android.intent.category.LAUNCHER 1 >/dev/null
        ;;
    *)       gradle --console=plain :app:testDebugUnitTest :app:assembleDebug ;;
esac

echo
for apk in app/build/outputs/apk/debug/app-debug.apk \
           app/build/outputs/apk/release/app-release-unsigned.apk; do
    [ -f "$apk" ] && printf '%-52s %s\n' "$apk" "$(du -h "$apk" | cut -f1)"
done

POTEM="$(mktemp)"; LC_ALL=C ls -A "$HOME" | LC_ALL=C sort > "$POTEM"
NOVO="$(LC_ALL=C comm -13 "$PREJ" "$POTEM" || true)"
rm -f "$PREJ" "$POTEM"
if [ -n "$NOVO" ]; then
    echo
    echo "POZOR: gradnja je pustila v domačem imeniku:"
    echo "$NOVO" | sed 's/^/  /'
    exit 1
fi
