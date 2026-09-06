#!/usr/bin/env bash
# Zapolni vrzel v zajemu s podatki z maline.
#
# Kdaj: ko je bil ta prenosnik nekaj časa ugasnjen. Malina teče ves čas prav
# zato, da je od kod dopolniti.
#
# Prilitje je idempotentno -- `obs` je ključen po
# (trip_id, service_date, stop_seq, feed_ts) -- zato je skript varno pognati
# večkrat. Ne piše na malino, samo bere.
set -euo pipefail

PI="${KAJROS_PI:-david@192.168.1.166}"
APP=/opt/kajros
DATA=/var/lib/kajros
PY="$APP/.venv/bin/python"
# /var/tmp in NE /tmp: na malini je /tmp tmpfs (214 MB), baza pa cez 368 MB.
ODDALJENA_KOPIJA=/var/tmp/kajros-prenos.sqlite
KAM=/var/tmp/kajros-malina.sqlite

[ -x "$PY" ] || { echo "Ni $PY -- ali je kajros sploh nameščen?"; exit 1; }

echo "== ali pridem do maline"
if ! timeout 10 ssh -o BatchMode=yes -o ConnectTimeout=5 "$PI" true 2>/dev/null; then
  cat <<KONEC
  NE. Ta prenosnik nima ključa za $PI.

  Enkratna nastavitev (poženi na TEM prenosniku):
      ssh-keygen -t ed25519 -N '' -f ~/.ssh/id_ed25519   # če ključa še ni
      ssh-copy-id $PI                                    # vpraša za geslo maline

  Šele nato ima ta skript smisel.
KONEC
  exit 1
fi

echo "== iščem bazo na malini"
ODDALJENA=$(timeout 20 ssh -o BatchMode=yes "$PI" \
  'for p in /var/lib/kajros/kajros.sqlite /var/lib/kajros/sz.sqlite \
            /var/lib/sztrack/sz.sqlite; do [ -f "$p" ] && echo "$p" && break; done')
[ -n "$ODDALJENA" ] || { echo "  baze na malini ni najti"; exit 1; }
echo "  $ODDALJENA"

echo "== preverjam prostor na malini"
timeout 30 ssh -o BatchMode=yes "$PI" "
  v=\$(stat -c%s '$ODDALJENA'); p=\$(df -B1 --output=avail /var/tmp | tail -1)
  echo \"   baza \$((v/1000000)) MB, prosto \$((p/1000000)) MB\"
  [ \"\$p\" -gt \"\$((v + 100000000))\" ] || { echo '   premalo prostora'; exit 1; }"

echo "== dosledna kopija (bere samo; zajema na malini ne prekine)"
timeout 900 ssh -o BatchMode=yes "$PI" "python3 - <<'PYEOF'
import sqlite3, os
src = sqlite3.connect('file:${ODDALJENA}?mode=ro', uri=True)
dst = sqlite3.connect('${ODDALJENA_KOPIJA}')
src.backup(dst); dst.close(); src.close()
print('  ', round(os.path.getsize('${ODDALJENA_KOPIJA}') / 1e6), 'MB')
PYEOF"

echo "== prenašam"
timeout 1800 scp -q -o BatchMode=yes "$PI:$ODDALJENA_KOPIJA" "$KAM"
timeout 30 ssh -o BatchMode=yes "$PI" "rm -f '$ODDALJENA_KOPIJA'"

echo "== preverjam kopijo"
"$PY" - "$KAM" <<'PYEOF'
import sqlite3, sys
c = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
if c.execute("PRAGMA quick_check").fetchone()[0] != "ok":
    sys.exit("  kopija je pokvarjena -- prilitja ni bilo")
print("  cela:", c.execute("SELECT COUNT(*) FROM run").fetchone()[0], "meritev")
PYEOF

stanje() {
  env KAJROS_DATA_DIR="$DATA" "$PY" - <<'PYEOF'
from kajros import db
c = db.connect()
q = lambda s: c.execute(s).fetchone()[0]
print(q("SELECT COUNT(*) FROM run"), q("SELECT COUNT(*) FROM obs"))
PYEOF
}

echo
# Brez sudota: `david` je v skupini `kajros` in podatkovni imenik je skupinsko
# pisljiv (`deploy/brez-sudo.sh`). Prej je bilo tu `sudo -u kajros` in s tem
# poziv za geslo sredi opravila, ki sicer tece samo od zacetka do konca.
if ! [ -w "$DATA/kajros.sqlite" ]; then
    echo "V '$DATA' ne morem pisati. Manjka enkratna nastavitev:"
    echo "  sudo bash ~/kajros/deploy/brez-sudo.sh"
    echo "(clanstvo v skupini velja sele od naslednje prijave)"
    exit 1
fi
chmod 644 "$KAM"

read -r PRE_RUN PRE_OBS <<<"$(stanje)"
env KAJROS_DATA_DIR="$DATA" "$PY" -m kajros.cli merge "$KAM"
# Malina tece starejso kodo, zato prilite meritve niso sle skozi novejse
# varovalke; `repair` popravi samo postanke, kjer se varovalka sprozi.
env KAJROS_DATA_DIR="$DATA" "$PY" -m kajros.cli repair
read -r PO_RUN PO_OBS <<<"$(stanje)"

rm -f "$KAM"
echo
printf "  meritve: %s -> %s  (+%s)\n" "$PRE_RUN" "$PO_RUN" "$((PO_RUN - PRE_RUN))"
printf "  dnevnik: %s -> %s  (+%s)\n" "$PRE_OBS" "$PO_OBS" "$((PO_OBS - PRE_OBS))"
