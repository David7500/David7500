#!/usr/bin/env bash
# Lastni usmerjevalniki (OSRM): peš za hojo do postajališča, avtobus in tir
# za pripenjanje tras na OSM (`kajros/pripni.py`). Iz istega izvoza še tiri s
# številko (`kajros/tiri.py`), da vlak na postaji stoji na tiru s table SŽ.
#
# **Zakaj svoj in ne javni.** Javni `router.project-osrm.org` bi ob vsakem
# iskanju izvedel, kje potnik stoji in kam gre, je izrecno „samo za demo" in bi
# bil nova točka odpovedi. Program je odprta koda; omejitev je bila gostiteljeva,
# ne programova -- naš strežnik vrne isto pot do decimalke (412,8 m na
# preizkusni poti v Polju).
#
# **Zakaj ne faktor.** Izmerjeno na 1 080 poteh: zračna razdalja × 1,45 podceni
# resnično pot v 48 % primerov, največji obvoz je 7,86×. Ovire (Sava, proga,
# avtocesta) so pravilo, ne izjema. Faktor ostane samo kot zasilna pot, kadar
# ta strežnik ne odgovori.
#
# **Zakaj avtobus in tir.** Trase GTFS so od ceste v mediani 3,1 m, od tira
# 1,7 m, razpršene na obe strani; pripete so 0,4 m (docs/MERITVE.md, 2. 10.
# 2026). Brez teh dveh strežnikov prikaz riše surove trase, kot prej.
#
# Izmerjeno ob postavitvi peš profila na arwenu (i5-6200U, 4 niti):
#   prenos 299 MB 30 s · extract 481 s (vrh 2,25 GB) · partition+customize 106 s
#   podatki 807 MB · strežnik med tekom 525 MB · matrika 1×70 ciljev 32 ms
# Avtobus na razvojnem stroju (6 jeder): 81 s, vrh 1,66 GB, 688 MB podatkov.
# Tir: 5 s, 1,1 GB vrha, ~1 MB podatkov.
#
# Gradnja teče lahko ob delujočem strežniku -- omejena je na 3 jedra, da
# spletni odzivi ne trpijo. `znova` zgradi vse tri od začetka.
set -euo pipefail

PODATKI="${KAJROS_OSRM_DIR:-$HOME/osrm}"
SLIKA="${KAJROS_OSRM_IMAGE:-ghcr.io/project-osrm/osrm-backend:latest}"
VIR="${KAJROS_OSRM_PBF:-https://download.geofabrik.de/europe/slovenia-latest.osm.pbf}"
PROFILI="$(cd "$(dirname "$0")" && pwd)/osrm"
APP="${KAJROS_APP:-/opt/kajros}"
PY="${KAJROS_PY:-$APP/.venv/bin/python}"
TIRI="${KAJROS_DATA_DIR:-/var/lib/kajros}/tiri.json"

krepko() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

command -v docker >/dev/null || { echo "docker ni nameščen"; exit 1; }
docker info >/dev/null 2>&1 || { echo "docker ni dosegljiv brez sudota (skupina docker?)"; exit 1; }

mkdir -p "$PODATKI/avtobus" "$PODATKI/tir"

# Peš ostane, kjer je bil (`$PODATKI/slovenia.osrm`), da obstoječa namestitev
# ne gradi znova; nova profila imata vsak svojo mapo.
#
# **Slika se ne posodablja sama.** Podatki so vezani na različico OSRM, ki jih
# je zgradila: 2. 10. 2026 je `docker pull` prinesel 26.10.0, peš podatki
# so bili iz 26.9.0 in strežnik se ni več zagnal („File is incompatible with
# this version of OSRM“) -- hoja bi padla na zračno razdaljo. Zato pull samo
# z `znova` ali kadar slike ni, in vsak profil si zapiše, s katero je
# zgrajen (`.slika`); drugačna slika = gradnja znova.
if [ "${1:-}" = "znova" ] || ! docker image inspect "$SLIKA" >/dev/null 2>&1; then
    krepko "slika $SLIKA"
    docker pull "$SLIKA"
fi
SLIKA_ID=$(docker image inspect --format '{{.Id}}' "$SLIKA")

zgrajen() {   # zgrajen <mapa>: podatki obstajajo in so iz te slike
    [ -f "$1/slovenia.osrm.mldgr" ] || return 1
    # Peš podatki od pred zapisa slike: zgrajeni z isto, ker se ni vlekla.
    [ -f "$1/.slika" ] || return 0
    [ "$(cat "$1/.slika")" = "$SLIKA_ID" ]
}

manjka=()
zgrajen "$PODATKI" || manjka+=(noga)
zgrajen "$PODATKI/avtobus" || manjka+=(avtobus)
zgrajen "$PODATKI/tir" || manjka+=(tir)
[ -f "$TIRI" ] || manjka+=(tiri)
[ "${1:-}" = "znova" ] && manjka=(noga avtobus tir tiri)

gradi() {   # gradi <mapa> <profil v vsebniku> [mapa s profili]
    local mapa="$1" profil="$2" dodatno=()
    [ -n "${3:-}" ] && dodatno=(-v "$3":/profili:ro)
    # osrm-extract piše poleg vhoda, zato vsak profil svojo kopijo (povezavo).
    if [ "$mapa" != "$PODATKI" ]; then
        ln -f "$PODATKI/slovenia.osm.pbf" "$mapa/slovenia.osm.pbf" 2>/dev/null \
            || cp "$PODATKI/slovenia.osm.pbf" "$mapa/slovenia.osm.pbf"
    fi
    for korak in \
        "osrm-extract -p $profil /data/slovenia.osm.pbf" \
        "osrm-partition /data/slovenia.osrm" \
        "osrm-customize /data/slovenia.osrm"
    do
        docker run --rm -t --cpus=3 --memory=4g -v "$mapa":/data "${dodatno[@]}" "$SLIKA" $korak
    done
    [ "$mapa" = "$PODATKI" ] || rm -f "$mapa/slovenia.osm.pbf"
    echo "$SLIKA_ID" > "$mapa/.slika"
}

if [ ${#manjka[@]} -gt 0 ]; then
    krepko "prenos OSM Slovenija"
    # Zemljevid se osveži dnevno, ceste in tiri pa se ne spreminjajo kot vozni
    # redi; ponovna gradnja enkrat ali dvakrat na leto je dovolj.
    curl -fL --progress-bar -o "$PODATKI/slovenia.osm.pbf" "$VIR"

    for kaj in "${manjka[@]}"; do
        case "$kaj" in
            noga)
                krepko "peš (extract → partition → customize), ~10 minut"
                gradi "$PODATKI" /opt/foot.lua ;;
            avtobus)
                krepko "avtobus, ~5 minut"
                gradi "$PODATKI/avtobus" /profili/avtobus.lua "$PROFILI" ;;
            tir)
                krepko "tir, pol minute"
                gradi "$PODATKI/tir" /profili/tir.lua "$PROFILI" ;;
            tiri)
                krepko "tiri s številko (osmium) -> $TIRI"
                docker run --rm -v "$PODATKI":/data debian:stable-slim bash -c "
                    apt-get update -qq >/dev/null && apt-get install -y -qq osmium-tool >/dev/null 2>&1
                    osmium tags-filter /data/slovenia.osm.pbf w/railway=rail -o /data/tiri.pbf --overwrite
                    osmium export /data/tiri.pbf -f geojsonseq --geometry-types=linestring \
                        -o /data/tiri.geojsonseq --overwrite
                    chown $(id -u):$(id -g) /data/tiri.*"
                (cd "$APP" && "$PY" -m kajros.cli tiri "$PODATKI/tiri.geojsonseq" --out "$TIRI")
                rm -f "$PODATKI/tiri.pbf" "$PODATKI/tiri.geojsonseq" ;;
        esac
    done

    # `.pbf` je po pripravi odveč in je 299 MB.
    rm -f "$PODATKI/slovenia.osm.pbf"
fi

# Samo krajevni vmesnik: kliče ga naš strežnik z istega računalnika. Iz
# omrežja ga ni treba videti in nima nobene avtentikacije.
zazeni() {   # zazeni <ime> <vrata> <mapa> <pomnilnik> <dodatne zastavice>
    docker rm -f "$1" >/dev/null 2>&1 || true
    docker run -d --name "$1" \
        --restart=unless-stopped \
        -p "127.0.0.1:$2:5000" \
        --memory="$4" \
        -v "$3":/data \
        "$SLIKA" osrm-routed --algorithm mld $5 /data/slovenia.osrm >/dev/null
}

krepko "zagon strežnikov na 127.0.0.1:5000 (peš), :5001 (avtobus), :5002 (tir)"
# Privzeta meja matrike je nedokumentirana in se lahko spremeni; 1 000 je z
# rezervo nad največjim izmerjenim primerom (201 kandidat pri Bavarskem dvoru).
zazeni kajros-osrm "${KAJROS_OSRM_PORT:-5000}" "$PODATKI" 1g "--max-table-size 1000"
# `pripni.NAJVEC_TOCK` točk na zahtevo; daljši kos se razreže.
zazeni kajros-osrm-avtobus 5001 "$PODATKI/avtobus" 1g "--max-matching-size 2000"
zazeni kajros-osrm-tir 5002 "$PODATKI/tir" 256m "--max-matching-size 2000"

preveri() {   # preveri <ime> <url>
    local odziv=""
    for i in $(seq 1 30); do
        sleep 1
        odziv=$(curl -s -m 3 "$2" || true)
        case "$odziv" in *'"code":"Ok"'*) echo "  $1: deluje"; return 0;; esac
    done
    echo "  $1 se ni odzval; dnevnik:"; docker logs --tail 20 "$1"; return 1
}

krepko "preverjanje"
preveri kajros-osrm "http://127.0.0.1:${KAJROS_OSRM_PORT:-5000}/route/v1/foot/14.5747,46.0698;14.5766,46.0713?overview=false"
preveri kajros-osrm-avtobus "http://127.0.0.1:5001/nearest/v1/x/14.5058,46.0569"
preveri kajros-osrm-tir "http://127.0.0.1:5002/nearest/v1/x/14.5100,46.0585"
echo "  podatki: $(du -sh "$PODATKI" | cut -f1)"
[ -f "$TIRI" ] && echo "  tiri: $(du -h "$TIRI" | cut -f1)"
echo "  Strežnik trase pripne sam ob naslednjem zagonu ali uvozu voznega reda;"
echo "  takoj: sudo systemctl restart kajros.service"
