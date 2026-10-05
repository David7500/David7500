#!/usr/bin/env bash
# Zgradi kajros/static/o-nas/o3.js iz o-nas/src.
#
# Orodji sta pripeti različici paketov z npm: three (svet) in esbuild (sveženj).
# Node za to ni potreben: tarbala se preneseta v o-nas/node_modules (ni v gitu)
# in se preverita po sha512 iz registra, preden se razpakirata. Sveženj gre v
# git, zato strežnik ničesar ne gradi.
set -euo pipefail
cd "$(dirname "$0")"

THREE=0.186.1
THREE_SHA="sha512-blFeqb49wRCSGUGj7gtpfnSGHy2lwDk94RhUmS1c/hTby70kvChbWpkJ4Pm1390LqzzvTmzgXKHPEafJwCb8jA=="
ESBUILD=0.28.2
ESBUILD_SHA="sha512-4xTZr1FUmSoQW4XIWmit3tzQrUTZM+N3P0XV8xROKYF50XfI7xeO90+1bZvNwxIufQ9hDQVRJH5YhgPVF8A/HQ=="

prenesi() {   # url, sha512, ciljna mapa
  [ -d "$3" ] && return
  local t
  t=$(mktemp)
  curl -fsSL "$1" -o "$t"
  if [ "sha512-$(openssl dgst -sha512 -binary "$t" | base64 -w0)" != "$2" ]; then
    echo "!! $1: sha512 se ne ujema" >&2
    rm -f "$t"
    exit 1
  fi
  mkdir -p "$3"
  tar -xzf "$t" -C "$3" --strip-components=1
  rm -f "$t"
}

prenesi "https://registry.npmjs.org/three/-/three-$THREE.tgz" "$THREE_SHA" node_modules/three
prenesi "https://registry.npmjs.org/@esbuild/linux-x64/-/linux-x64-$ESBUILD.tgz" "$ESBUILD_SHA" node_modules/@esbuild/linux-x64

# Licenčni komentarji (three.js, MIT) ostanejo na koncu svežnja.
node_modules/@esbuild/linux-x64/bin/esbuild src/main.js --bundle --format=iife --minify --target=es2020 \
  --legal-comments=eof --outfile=../kajros/static/o-nas/o3.js
