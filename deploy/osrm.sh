#!/usr/bin/env bash
# Peš usmerjevalnik (OSRM) za izračun hoje do postajališča.
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
# Izmerjeno ob postavitvi na arwenu (i5-6200U, 4 niti):
#   prenos 299 MB 30 s · extract 481 s (vrh 2,25 GB) · partition+customize 106 s
#   podatki 807 MB · strežnik med tekom 525 MB · matrika 1×70 ciljev 32 ms
#
# Gradnja rabi ~2,5 GB pomnilnika in ~10 minut. Teče lahko ob delujočem
# strežniku -- omejena je na 3 jedra, da spletni odzivi ne trpijo.
set -euo pipefail

PODATKI="${KAJROS_OSRM_DIR:-$HOME/osrm}"
SLIKA="${KAJROS_OSRM_IMAGE:-ghcr.io/project-osrm/osrm-backend:latest}"
VIR="${KAJROS_OSRM_PBF:-https://download.geofabrik.de/europe/slovenia-latest.osm.pbf}"
VSEBNIK=kajros-osrm
VRATA="${KAJROS_OSRM_PORT:-5000}"

krepko() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

command -v docker >/dev/null || { echo "docker ni nameščen"; exit 1; }
docker info >/dev/null 2>&1 || { echo "docker ni dosegljiv brez sudota (skupina docker?)"; exit 1; }

mkdir -p "$PODATKI"

if [ "${1:-}" = "znova" ] || [ ! -f "$PODATKI/slovenia.osrm.mldgr" ]; then
    krepko "slika $SLIKA"
    docker pull "$SLIKA"

    krepko "prenos OSM Slovenija"
    # Zemljevid se osveži dnevno, pešpoti pa se ne spreminjajo kot vozni redi;
    # ponovna gradnja enkrat ali dvakrat na leto je dovolj.
    curl -fL --progress-bar -o "$PODATKI/slovenia.osm.pbf" "$VIR"

    krepko "priprava (extract → partition → customize), ~10 minut"
    for korak in \
        "osrm-extract -p /opt/foot.lua /data/slovenia.osm.pbf" \
        "osrm-partition /data/slovenia.osrm" \
        "osrm-customize /data/slovenia.osrm"
    do
        docker run --rm -t --cpus=3 --memory=4g -v "$PODATKI":/data "$SLIKA" $korak
    done

    # `.pbf` je po pripravi odveč in je 299 MB; ostane 807 MB pripravljenega.
    rm -f "$PODATKI/slovenia.osm.pbf"
fi

krepko "zagon strežnika na 127.0.0.1:$VRATA"
# Samo krajevni vmesnik: kliče ga naš strežnik z istega računalnika. Iz
# omrežja ga ni treba videti in nima nobene avtentikacije.
docker rm -f "$VSEBNIK" >/dev/null 2>&1 || true
docker run -d --name "$VSEBNIK" \
    --restart=unless-stopped \
    -p "127.0.0.1:$VRATA:5000" \
    --memory=1g \
    -v "$PODATKI":/data \
    "$SLIKA" osrm-routed --algorithm mld --max-table-size 1000 /data/slovenia.osrm >/dev/null

# Privzeta meja matrike je nedokumentirana in se lahko spremeni; 1 000 je z
# rezervo nad največjim izmerjenim primerom (201 kandidat pri Bavarskem dvoru).

for i in $(seq 1 20); do
    sleep 1
    ODZIV=$(curl -s -m 3 "http://127.0.0.1:$VRATA/route/v1/foot/14.5747,46.0698;14.5766,46.0713?overview=false" || true)
    case "$ODZIV" in *'"code":"Ok"'*) break;; esac
done

case "${ODZIV:-}" in
    *'"code":"Ok"'*)
        krepko "deluje"
        echo "$ODZIV" | python3 -c 'import json,sys; r=json.load(sys.stdin)["routes"][0]; print("  preizkusna pot: %.1f m, %.0f s (%.2f km/h)" % (r["distance"], r["duration"], r["distance"]/r["duration"]*3.6))'
        echo "  podatki: $(du -sh "$PODATKI" | cut -f1)"
        ;;
    *)
        echo "strežnik se ni odzval; dnevnik:"; docker logs --tail 20 "$VSEBNIK"; exit 1;;
esac
