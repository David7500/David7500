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
#     (`ANDROID_USER_HOME`);
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
# Gradle NE prek wrapperja: wrapper pomeni binarni .jar v gitu. Tu je orodje
# in orodja zivijo v tej mapi. 8.9 je najnizja, ki jo zahteva AGP 8.7.
GRADLE="${GRADLE:-8.9}"
# Emulator je neobvezen: 2 GB za nekaj, kar rabi samo preverjanje prikaza.
# Vklopi ga s `KAJROS_EMULATOR=1 ./orodja.sh`.
SLIKA="${SLIKA:-system-images;android-35;default;x86_64}"

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
# **Ena sama spremenljivka, ne stiri.** AGP pade, ce jih najde vec in ne kazejo
# na isto mapo, in `ANDROID_SDK_HOME` pomeni STARSA mape `.android`, ne nje
# same -- torej sta `ANDROID_SDK_HOME=$KOREN/domov` in
# `ANDROID_USER_HOME=$KOREN/domov` po AGP dve razlicni poti. Izmerjeno:
# "Several environment variables ... contain different paths".
#
# Zato ostane samo `ANDROID_USER_HOME`, in kaze natanko tja, kamor pise oviti
# adb (`$HOME/.android` pri `HOME=$KOREN/domov`). Vse na eno mesto.
export ANDROID_USER_HOME="$KOREN/domov/.android"
# Emulator ima svojo spremenljivko in `ANDROID_USER_HOME` ne bere: isce po
# `ANDROID_AVD_HOME`, `ANDROID_SDK_HOME/avd` in `$HOME/.android/avd`. Brez te
# vrstice AVD-ja, ki smo ga naredili, ne najde. AGP jo prenese (preizkuseno --
# ni na njegovem seznamu spremenljivk, ki morajo biti ena sama).
export ANDROID_AVD_HOME="$KOREN/domov/.android/avd"
export GRADLE_USER_HOME="$KOREN/gradle"
export TMPDIR="$KOREN/tmp"
# Brez tega JVM naredi `~/.java/.userPrefs` in vanj zapise nastavitve
# sdkmanagerja. Izmerjeno: ob prvem zagonu je nastal `~/.java/google/prefs.xml`
# -- 16 kB smeti natanko tam, kjer je ne sme biti. `JAVA_TOOL_OPTIONS` velja
# za vsak JVM, tudi za Gradlov demon; cena je ena vrstica na stderr.
#
# `-Duser.home` je tu iz drugega razloga in ga je nasla sele meritev: gradnja
# je kljub `ANDROID_USER_HOME` naredila `~/.android/analytics.settings` z
# **obstojnim `userId`**. AGP-jeva telemetrija namrec ne gre skozi mapo
# Androida, ampak skozi lastnost JVM `user.home`. Preizkuseno je bilo troje:
# `ANDROID_USER_HOME` sam (pusca), `HOME=$KOREN/domov` (pusca -- za razliko od
# adb), `ANDROID_PREFS_ROOT` (AGP pade, ker hoce eno samo spremenljivko).
# Deluje samo `-Duser.home`, in datoteka pristane natanko v `ANDROID_USER_HOME`.
mkdir -p "$KOREN/domov/prefs"
export JAVA_TOOL_OPTIONS="-Djava.util.prefs.userRoot=$KOREN/domov/prefs -Djava.util.prefs.systemRoot=$KOREN/domov/prefs -Duser.home=$KOREN/domov"

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
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"

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

# --- emulator (neobvezno) --------------------------------------------------
# `default` in ne `google_apis`: to je AOSP brez Googlovih storitev, torej ista
# izbira kot pri telefonu. Emulator rabimo zato, ker ima ta projekt pravilo, da
# se spremembo prikaza POGLEDA, preden se razglasi za koncano -- brez njega je
# vsako preverjanje odvisno od tega, ali je telefon priklopljen.
#
# KVM mora biti dostopen. Na tem racunalniku je prek ACL (`getfacl /dev/kvm`),
# torej brez sudota in brez clanstva v skupini `kvm`.
if [ "${KAJROS_EMULATOR:-0}" = "1" ]; then
    krepko "emulator in sistemska slika ($SLIKA)"
    android --no-metrics sdk install "emulator" "$SLIKA" >/dev/null 2>&1 || \
        sdkmanager --install "emulator" "$SLIKA" >/dev/null
    if ! "$ANDROID_HOME/cmdline-tools/latest/bin/avdmanager" list avd 2>/dev/null \
         | grep -q "Name: kajros"; then
        echo no | "$ANDROID_HOME/cmdline-tools/latest/bin/avdmanager" \
            create avd -n kajros -k "$SLIKA" -d pixel_6 --force >/dev/null 2>&1
    fi
fi

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

# --- Gradle ----------------------------------------------------------------
if [ ! -x "$KOREN/gradle-dist/bin/gradle" ]; then
    krepko "Gradle $GRADLE"
    curl -fL --progress-bar -o "$KOREN/prenosi/gradle.zip" \
        "https://services.gradle.org/distributions/gradle-${GRADLE}-bin.zip"
    rm -rf "$KOREN/prenosi/graz" "$KOREN/gradle-dist"
    unzip -q "$KOREN/prenosi/gradle.zip" -d "$KOREN/prenosi/graz"
    mv "$KOREN/prenosi/graz/gradle-$GRADLE" "$KOREN/gradle-dist"
    rm -rf "$KOREN/prenosi/graz" "$KOREN/prenosi/gradle.zip"
fi
export PATH="$KOREN/gradle-dist/bin:$PATH"
echo "    $(gradle --version 2>/dev/null | grep -m1 '^Gradle')"

# --- okolje ----------------------------------------------------------------
cat > "$KOREN/okolje.sh" <<EOF
# Poženi z: source ~/kajros-android/okolje.sh
#
# Nastavi SAMO to sejo. Ne pisi tega v .bashrc -- ce je nastavljeno vedno,
# potem \`TMPDIR\` in \`GRADLE_USER_HOME\` veljata tudi za vse drugo delo.
export JAVA_HOME="$KOREN/jdk"
export ANDROID_HOME="$KOREN/sdk"
export ANDROID_SDK_ROOT="$KOREN/sdk"
export ANDROID_USER_HOME="$KOREN/domov/.android"
# Emulator ima svojo spremenljivko in `ANDROID_USER_HOME` ne bere: isce po
# `ANDROID_AVD_HOME`, `ANDROID_SDK_HOME/avd` in `$HOME/.android/avd`. Brez te
# vrstice AVD-ja, ki smo ga naredili, ne najde. AGP jo prenese (preizkuseno --
# ni na njegovem seznamu spremenljivk, ki morajo biti ena sama).
export ANDROID_AVD_HOME="$KOREN/domov/.android/avd"
export GRADLE_USER_HOME="$KOREN/gradle"
export TMPDIR="$KOREN/tmp"
export JAVA_TOOL_OPTIONS="-Djava.util.prefs.userRoot=$KOREN/domov/prefs -Djava.util.prefs.systemRoot=$KOREN/domov/prefs -Duser.home=$KOREN/domov"
export PATH="\$JAVA_HOME/bin:$KOREN/gradle-dist/bin:$KOREN/sdk/cmdline-tools/latest/bin:$KOREN/sdk/platform-tools:$KOREN/sdk/emulator:\$PATH"
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
