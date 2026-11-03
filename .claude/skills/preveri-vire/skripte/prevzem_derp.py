"""Prevzem derp.si med zaklepom uvoza: koliko meritev NAP prepiše (3. 11. 2026).

NAP vodi zamude medkrajevnih (`iz_lege.nap_vodi`), dokler je prebran v 60 s.
Uvoz ob 4.20 drži bazo 60--90 s; ko NAP zato molči dlje, derp.si za en obhod
piše vse postanke voženj 1119/1121/1123, tudi že izmerjene. Za dan DAN izpiše
zapise teh prevoznikov po minuti 4.15--4.40 (ali OD, MINUT), nato za vsako
sekundo z vsaj 100 zapisi (izbruh derp.si): koliko jih je prepisalo prejšnjo
meritev, za koliko, in ali je prepis ostal v `run`. Podnevi je 100 na sekundo
lahko tudi NAP sam po zaklepu (30. 10. ob 11.31: 145, 0 prepisov). Samo
branje, na arwenu:

  scp .claude/skills/preveri-vire/skripte/prevzem_derp.py david@192.168.1.46:/tmp/ && \
  ssh david@192.168.1.46 '/opt/kajros/.venv/bin/python -I /tmp/prevzem_derp.py 2026-11-04 [04:15 25]'
"""
import sqlite3
import sys
from datetime import datetime

DAN = sys.argv[1]
NAP = ("1119", "1121", "1123")
OD = int(datetime.fromisoformat(f"{DAN} {sys.argv[2] if len(sys.argv) > 2 else '04:15'}").timestamp())
DO = OD + int(sys.argv[3] if len(sys.argv) > 3 else 25) * 60
conn = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True, timeout=30)


def rowid_od(t):
    """`obs` nima indeksa po času; rowid raste z zapisom, meja z bisekcijo."""
    lo, hi = 1, conn.execute("SELECT MAX(rowid) FROM obs").fetchone()[0]
    while lo < hi:
        sredina = (lo + hi) // 2
        (ts,) = conn.execute("SELECT observed_at FROM obs WHERE rowid >= ? ORDER BY rowid LIMIT 1",
                             (sredina,)).fetchone()
        lo, hi = (sredina + 1, hi) if ts < t else (lo, sredina)
    return lo


R0 = rowid_od(OD - 3600)            # ura rezerve za zapise, ki niso po vrsti
print(DAN, "minuta | 1119/1121/1123 | vsi")
for k, nap, vsi in conn.execute(f"""
        SELECT (o.observed_at - ?) / 60, SUM(t.agency IN {NAP}), COUNT(*)
        FROM obs o JOIN trip t USING (trip_id)
        WHERE o.rowid >= ? AND o.observed_at BETWEEN ? AND ? GROUP BY 1""", (OD, R0, OD, DO - 1)):
    print(" ", datetime.fromtimestamp(OD + 60 * k).strftime("%H.%M"), nap, vsi)

izbruhi = conn.execute(f"""
    SELECT o.observed_at FROM obs o JOIN trip t USING (trip_id)
    WHERE o.rowid >= ? AND o.observed_at BETWEEN ? AND ? AND t.agency IN {NAP}
    GROUP BY o.observed_at HAVING COUNT(*) >= 100""", (R0, OD, DO - 1)).fetchall()
if not izbruhi:
    print("izbruha derp.si za prevoznike NAP ni")
for (ts,) in izbruhi:
    vrstice = conn.execute(f"""
        SELECT o.trip_id, o.service_date, o.stop_seq, COALESCE(o.delay_dep, o.delay_arr), o.feed_ts
        FROM obs o JOIN trip t USING (trip_id)
        WHERE o.rowid >= ? AND o.observed_at = ? AND t.agency IN {NAP}""", (R0, ts)).fetchall()
    prepisi = []
    for tid, sd, seq, d, fts in vrstice:
        p = conn.execute("""SELECT COALESCE(delay_dep, delay_arr) FROM obs
                            WHERE trip_id = ? AND service_date = ? AND stop_seq = ? AND observed_at < ?
                            ORDER BY observed_at DESC LIMIT 1""", (tid, sd, seq, ts)).fetchone()
        if p is None or p[0] is None or d is None:
            continue
        r = conn.execute("SELECT COALESCE(delay_dep, delay_arr), feed_ts FROM run "
                         "WHERE trip_id = ? AND service_date = ? AND stop_seq = ?", (tid, sd, seq)).fetchone()
        prepisi.append((tid, abs(d - p[0]), r is not None and r[1] == fts and r[0] == d))
    print(datetime.fromtimestamp(ts).strftime("%H:%M:%S"), f"zapisov {len(vrstice)},",
          f"voženj {len({v[0] for v in vrstice})};",
          f"prepisanih meritev {len(prepisi)} na {len({p[0] for p in prepisi})} vožnjah,",
          f"> 2 min {sum(p[1] > 120 for p in prepisi)}, > 5 min {sum(p[1] > 300 for p in prepisi)},",
          f"največ {max((p[1] for p in prepisi), default=0)} s, v `run` ostalo {sum(p[2] for p in prepisi)}")
