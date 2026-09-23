#!/usr/bin/env bash
# Kazalo naslovov za iskanje na strani „Najhitrejša pot" (`kajros/naslovi.py`).
#
# **Zakaj svoje in ne geokodirnik.** Tuji ponudnik bi ob vsakem pritisku tipke
# izvedel, kam kdo gre -- isti razlog kot za lastni peš usmerjevalnik
# (`deploy/osrm.sh`). Kazalo je izpeljano iz OpenStreetMap (ODbL), kjer so
# hišne številke GURS uvožene za vso državo.
#
# Izmerjeno na razvojnem stroju 23. 9. 2026: prenos 313 MB · osmium (izbor in
# izvoz) 28 s · gradnja kazala 12 s · kazalo 51 MB · 435 044 naslovov,
# 17 085 ulic, 11 237 krajev, 82 934 imenovanih točk.
#
# osmium teče v vsebniku, ker ga na strežniku ni in ga ne rabi nič drugega;
# strežnik sam PBF-ja ne bere. Rabi docker brez sudota (skupina docker), isto
# kot `osrm.sh`.
#
# Naslovi se ne spreminjajo kot vozni redi; ponovna gradnja nekajkrat na leto je
# dovolj. Strežnik novo datoteko opazi sam (ključ povezave nosi `mtime`).
set -euo pipefail

DELO="${KAJROS_NASLOVI_DELO:-$HOME/naslovi}"
VIR="${KAJROS_OSRM_PBF:-https://download.geofabrik.de/europe/slovenia-latest.osm.pbf}"
APP="${KAJROS_APP:-/opt/kajros}"
PY="${KAJROS_PY:-$APP/.venv/bin/python}"
CILJ="${KAJROS_NASLOVI:-${KAJROS_DATA_DIR:-/var/lib/kajros}/naslovi.sqlite}"

krepko() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

command -v docker >/dev/null || { echo "docker ni nameščen"; exit 1; }
docker info >/dev/null 2>&1 || { echo "docker ni dosegljiv brez sudota (skupina docker?)"; exit 1; }
mkdir -p "$DELO"

krepko "prenos OSM Slovenija"
curl -fL --progress-bar -o "$DELO/slovenia.osm.pbf" "$VIR"

krepko "izbor naslovov, krajev in imenovanih točk (osmium)"
# Vse, kar ima hišno številko, ime ali je kraj. Ceste z imenom pridejo zraven,
# a kazalo ulic gradi iz naslovov -- lega ulice je hiša na njej, ne sredina črte.
docker run --rm -v "$DELO":/data debian:stable-slim bash -c "
    apt-get update -qq >/dev/null && apt-get install -y -qq osmium-tool >/dev/null 2>&1
    osmium tags-filter /data/slovenia.osm.pbf nwr/addr:housenumber nwr/name nwr/place \
        -o /data/izbor.pbf --overwrite
    osmium export /data/izbor.pbf -f geojsonseq --geometry-types=point,linestring,polygon \
        -a type,id -o /data/izbor.geojsonseq --overwrite
    chown $(id -u):$(id -g) /data/izbor.*"

krepko "kazalo -> $CILJ"
# `zgradi()` piše v začasno datoteko in jo na koncu preimenuje: strežnik med
# gradnjo bere staro kazalo, nikoli napol zgrajenega.
cd "$APP"
KAJROS_NASLOVI="$CILJ" "$PY" -m kajros.cli naslovi "$DELO/izbor.geojsonseq" --out "$CILJ"

rm -f "$DELO/slovenia.osm.pbf" "$DELO/izbor.pbf" "$DELO/izbor.geojsonseq"
krepko "končano: $(du -h "$CILJ" | cut -f1)"
