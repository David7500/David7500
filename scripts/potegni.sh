#!/usr/bin/env bash
# Potegne zajem z maline in ga prilije v lokalno bazo.
#
# Zakaj v to smer in nikoli obratno: malina je edina naprava, ki teče ves čas,
# zato je njen zajem merodajen. Ta računalnik je pogosto ugasnjen in ima
# luknje -- 31. 8. je imel 4 645 železniških meritev, malina pa 6 912.
#
# Prilitje je idempotentno: `obs` je ključen po
# (trip_id, service_date, stop_seq, feed_ts), zato se podvojene meritve tiho
# zavržejo. Skripto je varno pognati večkrat na dan.
set -euo pipefail

PI="${KAJROS_PI:-david@192.168.1.166}"
ODDALJENA="${KAJROS_PI_DB:-}"
KAM="${KAJROS_TMP:-/tmp/kajros-malina.sqlite}"
# NE `/tmp` na malini: tam je tmpfs 214 MB v RAM-u, baza pa je presegla
# 368 MB. Kopija bi padla, in to na napravi s 427 MB pomnilnika, kjer
# teče merodajen zajem. `/var/tmp` je ext4 z 19 G.
ODDALJENI_TMP="${KAJROS_PI_TMP:-/var/tmp/kajros-prenos.sqlite}"
cd "$(dirname "$0")/.."
PY=./venv/bin/python

stanje() {   # meritve, dnevnik, dnevi -- da se vidi, kaj je prilitje dodalo
  $PY - <<'PYEOF'
from kajros import db
c = db.connect()
q = lambda s: c.execute(s).fetchone()[0]
print(q("SELECT COUNT(*) FROM run"), q("SELECT COUNT(*) FROM obs"),
      q("SELECT COUNT(DISTINCT service_date) FROM run"))
PYEOF
}

echo "== malina =="
if ! timeout 10 ssh -o BatchMode=yes -o ConnectTimeout=5 "$PI" true 2>/dev/null; then
  echo "  $PI ni dosegljiva (ssh)" >&2
  exit 1
fi

# Malina do prve ponovne namestitve tece STARO kodo pod starim imenom, zato
# poti ne ugibamo, ampak jo poiscemo. Vrstni red je od najnovejse nazaj; brez
# tega bi vleka baze med preimenovanjem in deployem tiho crknila.
if [ -z "$ODDALJENA" ]; then
  ODDALJENA=$(timeout 20 ssh -o BatchMode=yes "$PI" \
    'for p in /var/lib/kajros/kajros.sqlite /var/lib/kajros/sz.sqlite \
              /var/lib/sztrack/sz.sqlite; do [ -f "$p" ] && echo "$p" && break; done')
  if [ -z "$ODDALJENA" ]; then
    echo "  baze na malini ni najti (poskusil /var/lib/{kajros,sztrack})" >&2
    exit 1
  fi
  echo "  baza na malini: $ODDALJENA"
fi

# Preden se lotimo kopije: ali je zanjo sploh prostor? Brez tega se napaka
# pokaze sele sredi pisanja, ko je ciljni sistem ze poln -- na malini je to
# nekoc pomenilo poln RAM disk.
echo "  preverjam prostor …"
timeout 30 ssh -o BatchMode=yes "$PI" "
  velikost=\$(stat -c%s '$ODDALJENA')
  prosto=\$(df -B1 --output=avail '$(dirname "$ODDALJENI_TMP")' | tail -1)
  echo \"   baza \$((velikost/1000000)) MB, prosto \$((prosto/1000000)) MB v $(dirname "$ODDALJENI_TMP")\"
  [ \"\$prosto\" -gt \"\$((velikost + 100000000))\" ] || {
    echo '   premalo prostora za kopijo' >&2; exit 1; }"

# Dosledna kopija, ne golo kopiranje datoteke: baza je v načinu WAL in
# `sz.sqlite` sam po sebi ne vsebuje zadnjih zapisov. `backup()` jih zajame,
# bere pa samo -- zajema na malini ne prekine in ne zaklene.
echo "  delam dosledno kopijo …"
timeout 600 ssh -o BatchMode=yes "$PI" "python3 - <<'PYEOF'
import sqlite3, os
src = sqlite3.connect('file:${ODDALJENA}?mode=ro', uri=True)
dst = sqlite3.connect('${ODDALJENI_TMP}')
src.backup(dst); dst.close(); src.close()
print('  ', round(os.path.getsize('${ODDALJENI_TMP}') / 1e6), 'MB')
PYEOF"

echo "  prenašam …"
timeout 900 scp -q -o BatchMode=yes "$PI:$ODDALJENI_TMP" "$KAM"
timeout 30 ssh -o BatchMode=yes "$PI" "rm -f '$ODDALJENI_TMP'"

# Pokvarjena kopija bi prilila smeti. Preverimo, preden se je dotaknemo baze.
$PY - "$KAM" <<'PYEOF'
import sqlite3, sys
c = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
if c.execute("PRAGMA quick_check").fetchone()[0] != "ok":
    sys.exit("  kopija je pokvarjena -- prilitja ni bilo")
print("  kopija je cela:", c.execute("SELECT COUNT(*) FROM run").fetchone()[0], "meritev")
PYEOF

echo "== prilivam =="
read -r PRE_RUN PRE_OBS PRE_DNI <<<"$(stanje)"
$PY -m kajros.cli merge "$KAM"

# Malina teče starejšo kodo, zato prilite meritve niso šle skozi novejše
# varovalke (`undoes_passing`, `is_forecast`). `repair` popravi samo postanke,
# na katerih se varovalka sproži -- ne prepisuje celega dnevnika.
echo "== popravljam =="
$PY -m kajros.cli repair

read -r PO_RUN PO_OBS PO_DNI <<<"$(stanje)"
echo
printf "  meritve: %s -> %s  (+%s)\n" "$PRE_RUN" "$PO_RUN" "$((PO_RUN - PRE_RUN))"
printf "  dnevnik: %s -> %s  (+%s)\n" "$PRE_OBS" "$PO_OBS" "$((PO_OBS - PRE_OBS))"
printf "  dnevi:   %s -> %s\n" "$PRE_DNI" "$PO_DNI"
