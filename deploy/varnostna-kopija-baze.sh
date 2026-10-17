#!/bin/sh
# Nočna varnostna kopija baze -- kliče jo `kajros-backup.service`.
#
# **VACUUM INTO, ne `.backup`.** `.backup` kopira po 100 strani in se ob
# vsakem zapisu druge povezave začne znova; zajem piše na nekaj sekund, zato
# se je na arwenu 1.–17. 10. 2026 vrtel do 58 min (40–46 min procesorja) in
# končal šele, ko je kdo drug za dalj časa zaklenil zapis (obrez dnevnika,
# uvoz voznega reda). VACUUM INTO je ena bralna transakcija: posnetek je
# dosleden, zajem piše naprej (WAL), kopija je stisnjena. Na 3,5 GB ~3 min.
#
# Skripta je v kodi, ne v enoti: posodobi jo `git push`, enota v
# /etc/systemd/system pa rabi sudo.
set -eu
DATA="${DATA:-/var/lib/kajros}"
KEEP="${KEEP:-3}"
# Koliko prostora mora ostati, da se kopija sploh splača. Pod tem raje ne
# naredimo ničesar in to povemo -- poln disk ustavi tudi ZAJEM, kopija pa je
# le kratkoročna varovalka. VACUUM INTO najprej napiše nestisnjeno kopijo
# (17. 10. 2026: 4,9 GB), zato velikost baze šteje zraven.
MIN_FREE_MB="${MIN_FREE_MB:-2000}"

free_mb=$(df -Pm "$DATA" | awk 'NR==2{print $4}')
baza_mb=$(du -m "$DATA/kajros.sqlite" | cut -f1)
if [ "$free_mb" -lt $((baza_mb + MIN_FREE_MB)) ]; then
  echo "premalo prostora ($free_mb MB, baza $baza_mb MB) -- kopija preskočena"
  exit 0
fi

mkdir -p "$DATA/backup"
tmp="$DATA/backup/.tekoca.sqlite"
cilj="$DATA/backup/sz-$(date +%Y%m%d).sqlite.gz"
rm -f "$tmp" "$cilj.tmp"
zacetek=$(date +%s)
sqlite3 "file:$DATA/kajros.sqlite?mode=ro" "VACUUM INTO '$tmp'"
gzip -1 -c "$tmp" > "$cilj.tmp"
mv "$cilj.tmp" "$cilj"
rm -f "$tmp"
echo "kopija $cilj: $(du -h "$cilj" | cut -f1), $(( $(date +%s) - zacetek )) s"

# Hranimo tri stisnjene kopije, ne štirinajst: baza z vsemi prevozniki zraste
# ~3,4 GB na leto, tri stisnjene so ob koncu leta ~4 GB.
ls -1t "$DATA"/backup/sz-*.sqlite.gz 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm -f
rm -f "$DATA"/backup/sz-*.sqlite
