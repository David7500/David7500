#!/usr/bin/env bash
# Orodja za gradnjo Androida -- VSA v eni mapi, brez sudota, brez smeti drugod.
#
# Zahteva je bila izrecna: da se da vse pobrisati z enim ukazom in da po
# odstranitvi na racunalniku ne ostane nic. Zato:
#
#   * JDK NE gre skozi `apt` (to bi bilo sistemsko in bi ostalo), ampak kot
#     razpakiran arhiv Temurin v to mapo;
#   * Gradle svojih predpomnilnikov ne odlaga v `~/.gradle`, ampak v
#     `$KOREN/gradle` (`GRADLE_USER_HOME`) -- to je obicajno najvecja smet,
#     lahko vec GB;
#   * `adb` svojega kljuca ne pise v `~/.android`, ampak v `$KOREN/domov`
#     (`ANDROID_USER_HOME`, pri starejsih orodjih `ANDROID_SDK_HOME`);
#   * zacasne datoteke gredo v `$KOREN/tmp`, ne v `/tmp`.
#
# Odstranitev vsega, vkljucno z nastavitvami in licencami:
#
#     rm -rf ~/kajros-android
#
# Koda aplikacije NI tu -- ta gre v git, v `android/app/`. Tu so samo orodja,
# ki so velika, prenosljiva in jih je vedno mogoce znova prenesti.
set -euo pipefail

KOREN="${KAJROS_ANDROID:-$HOME/kajros-android}"
# Zadnja izdaja v Googlovem `repository2-3.xml` ob pisanju (6. 9. 2026), 181 MB.
CMDLINE_BUILD="${CMDLINE_BUILD:-16111833}"
# Android 15. Ciljna raven se doloci v `build.gradle`, tu gre za prevajalnik.
PLATFORMA="${PLATFORMA:-android-35}"
BUILD_TOOLS="${BUILD_TOOLS:-35.0.0}"

krepko() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

# Dokaz, ne obljuba: posnamemo vrh domacega imenika pred in po, in na koncu
# izpisemo, kaj je nastalo zunaj nase mape. Ce je seznam prazen, zahteva drzi.
PREJ="$(mktemp)"
LC_ALL=C ls -A "$HOME" | LC_ALL=C sort > "$PREJ"

mkdir -p "$KOREN"/{sdk,gradle,domov,tmp,prenosi}

# --- JDK -------------------------------------------------------------------
if [ ! -x "$KOREN/jdk/bin/javac" ]; then
    krepko "JDK 21 (Temurin, brez sistemske namestitve)"
    URL="$(curl -fsS "https://api.adoptium.net/v3/assets/latest/21/hotspot?architecture=x64&image_type=jdk&os=linux&vendor=eclipse" \
           | python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["binary"]["package"]["link"])')"
    echo "    $URL"
    curl -fL --progress-bar -o "$KOREN/prenosi/jdk.tar.gz" "$URL"
    mkdir -p "$KOREN/jdk"
    # `--strip-components=1`: arhiv ima svojo mapo `jdk-21.../`, mi hocemo
    # ravno pot, da `JAVA_HOME` ni odvisen od stevilke izdaje.
    tar -xzf "$KOREN/prenosi/jdk.tar.gz" -C "$KOREN/jdk" --strip-components=1
    rm -f "$KOREN/prenosi/jdk.tar.gz"
fi
export JAVA_HOME="$KOREN/jdk"
export PATH="$JAVA_HOME/bin:$PATH"
echo "    $("$JAVA_HOME/bin/java" -version 2>&1 | head -1)"

# --- Android SDK -----------------------------------------------------------
export ANDROID_HOME="$KOREN/sdk"
export ANDROID_SDK_ROOT="$ANDROID_HOME"          # starejsa orodja berejo tega
export ANDROID_USER_HOME="$KOREN/domov"
export ANDROID_SDK_HOME="$KOREN/domov"           # pred orodji 34
export ANDROID_EMULATOR_HOME="$KOREN/domov/emulator"
export ANDROID_AVD_HOME="$KOREN/domov/avd"
export GRADLE_USER_HOME="$KOREN/gradle"
export TMPDIR="$KOREN/tmp"
# Brez tega JVM naredi `~/.java/.userPrefs` in vanj zapise nastavitve
# sdkmanagerja. Izmerjeno: ob prvem zagonu je nastal `~/.java/google/prefs.xml`
# -- 16 kB smeti natanko tam, kjer je ne sme biti. `JAVA_TOOL_OPTIONS` velja
# za vsak JVM, tudi za Gradlov demon; cena je ena vrstica na stderr.
mkdir -p "$KOREN/domov/prefs"
export JAVA_TOOL_OPTIONS="-Djava.util.prefs.userRoot=$KOREN/domov/prefs -Djava.util.prefs.systemRoot=$KOREN/domov/prefs"

if [ ! -x "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" ]; then
    krepko "cmdline-tools ($CMDLINE_BUILD)"
    ZIP="$KOREN/prenosi/cmdline-tools.zip"
    curl -fL --progress-bar -o "$ZIP" \
        "https://dl.google.com/android/repository/commandlinetools-linux-${CMDLINE_BUILD}_latest.zip"
    # Zip razpakira v `cmdline-tools/`, `sdkmanager` pa hoce biti v
    # `cmdline-tools/latest/` -- sicer se pritozi nad lastno postavitvijo.
    rm -rf "$KOREN/prenosi/raz"
    unzip -q "$ZIP" -d "$KOREN/prenosi/raz"
    mkdir -p "$ANDROID_HOME/cmdline-tools"
    mv "$KOREN/prenosi/raz/cmdline-tools" "$ANDROID_HOME/cmdline-tools/latest"
    rm -rf "$KOREN/prenosi/raz" "$ZIP"
fi
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"

krepko "licence in paketi"
# **`--no-metrics` gre na `android`, NE na `sdkmanager`.** Ta je v teh
# orodjih ze opuscen in samo preusmerja na novi CLI; z zastavico ukaz tiho
# ne naredi nicesar (izmerjeno: `sdkmanager --no-metrics --list_installed`
# izpise samo opozorilo o opustitvi in nic drugega).
#
# Da zastavica res deluje, je prav tako izmerjeno na stevilu datotek v
# `analytics/metrics/spool/`: brez nje 8 -> 9, z njo ostane 9.
#
# Zakaj to sploh pocnemo: CLI v spool zapise izvedene ukaze in **imena
# spremenljivk okolja iz tvoje lupine**, nato pa jih poslje Googlu
# (`analytics/last_upload_time`). Za projekt, ki se Googlu namenoma izogiba,
# je to najmanj, kar se da izklopiti ob gradnji.
#
# Licence pristanejo v `$ANDROID_HOME/licenses/`, torej znotraj mape. Zanje
# novi CLI se nima ukaza, zato gre ta en klic po stari poti.
yes | sdkmanager --licenses >/dev/null 2>&1 || true
android --no-metrics sdk install "platform-tools" "platforms;$PLATFORMA" \
    "build-tools;$BUILD_TOOLS" >/dev/null 2>&1 || \
    sdkmanager --install "platform-tools" "platforms;$PLATFORMA" \
        "build-tools;$BUILD_TOOLS" >/dev/null

# Kar je med namescanjem vseeno pristalo v spoolu, naj ne odide nikamor.
rm -rf "$KOREN/domov/cli/analytics/metrics/spool" 2>/dev/null || true

# --- adb ovijemo NA MESTU --------------------------------------------------
# `adb` na Linuxu `ANDROID_USER_HOME` ne upostevа: kljuc zapise v `$HOME/.android`
# ne glede na nastavitve (izmerjeno -- mapa je nastala kljub obema
# spremenljivkama). Edino, kar ga premakne, je drugacen `$HOME`.
#
# Ovoj gre na mesto pravega programa in ne v svojo mapo pred PATH, ker Gradle
# `adb` klice po ABSOLUTNI poti (`$ANDROID_HOME/platform-tools/adb`) in bi
# ovoj v PATH preprosto obsel.
ADB="$ANDROID_HOME/platform-tools/adb"
if [ -f "$ADB" ] && ! head -c2 "$ADB" | grep -q '#!'; then
    krepko "ovijam adb, da ne pise v ~/.android"
    mv "$ADB" "$ADB.pravi"
    cat > "$ADB" <<EOF
#!/usr/bin/env bash
# Ovoj: glej android/orodja.sh. Pravi program je adb.pravi.
HOME="$KOREN/domov" exec "$ADB.pravi" "\$@"
EOF
    chmod +x "$ADB"
fi

# --- okolje ----------------------------------------------------------------
cat > "$KOREN/okolje.sh" <<EOF
# Poženi z: source ~/kajros-android/okolje.sh
#
# Nastavi SAMO to sejo. Ne pisi tega v .bashrc -- ce je nastavljeno vedno,
# potem \`TMPDIR\` in \`GRADLE_USER_HOME\` veljata tudi za vse drugo delo.
export JAVA_HOME="$KOREN/jdk"
export ANDROID_HOME="$KOREN/sdk"
export ANDROID_SDK_ROOT="$KOREN/sdk"
export ANDROID_USER_HOME="$KOREN/domov"
export ANDROID_SDK_HOME="$KOREN/domov"
export ANDROID_EMULATOR_HOME="$KOREN/domov/emulator"
export ANDROID_AVD_HOME="$KOREN/domov/avd"
export GRADLE_USER_HOME="$KOREN/gradle"
export TMPDIR="$KOREN/tmp"
export JAVA_TOOL_OPTIONS="-Djava.util.prefs.userRoot=$KOREN/domov/prefs -Djava.util.prefs.systemRoot=$KOREN/domov/prefs"
export PATH="\$JAVA_HOME/bin:$KOREN/sdk/cmdline-tools/latest/bin:$KOREN/sdk/platform-tools:\$PATH"
EOF

# --- dokaz -----------------------------------------------------------------
krepko "kaj je nastalo ZUNAJ $KOREN"
POTEM="$(mktemp)"
LC_ALL=C ls -A "$HOME" | LC_ALL=C sort > "$POTEM"
NOVO="$(LC_ALL=C comm -13 "$PREJ" "$POTEM" | grep -v "^$(basename "$KOREN")$" || true)"
if [ -z "$NOVO" ]; then
    echo "    nič -- domači imenik je nedotaknjen"
else
    echo "    POZOR, nastalo je:"
    echo "$NOVO" | sed 's/^/      /'
fi
rm -f "$PREJ" "$POTEM"

krepko "velikost"
du -sh "$KOREN" | sed 's/^/    /'
echo
echo "Uporaba:   source $KOREN/okolje.sh"
echo "Brisanje:  rm -rf $KOREN"
