import sqlite3, statistics as st
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo
TZ = ZoneInfo("Europe/Ljubljana")
c = sqlite3.connect("file:/var/tmp/kajros-stat.sqlite?mode=ro", uri=True)
p = sqlite3.connect("file:/var/tmp/promet-stat.sqlite?mode=ro", uri=True)
def polnoc(d):
    y, m, dd = map(int, d.split("-")); return int(datetime(y, m, dd, 12, tzinfo=TZ).timestamp()) - 12*3600
ac = defaultdict(lambda: defaultdict(list))
for rel, ts, cas in p.execute("SELECT relacija, ts, cas_s FROM ac WHERE cas_s IS NOT NULL"):
    d = datetime.fromtimestamp(ts, TZ)
    if d.weekday() < 5: ac[rel][d.hour].append(cas)
PARI = [("Ljubljana", "Maribor", "LJ - MB"), ("Maribor", "Ljubljana", "MB - LJ"),
        ("Ljubljana", "Koper", "LJ - KP"), ("Koper", "Ljubljana", "KP - LJ"),
        ("Ljubljana", "Jesenice", "LJ - Karavanke"), ("Jesenice", "Ljubljana", "Karavanke - LJ"),
        ("Ljubljana", "Dobova", "LJ - MP Obrežje"), ("Dobova", "Ljubljana", "MP Obrežje - LJ")]
for od, do, rel in PARI:
    rows = c.execute("""
      SELECT r1.service_date, s1.dep_s, COALESCE(r1.delay_dep, r1.delay_arr), s2.arr_s, COALESCE(r2.delay_arr, r2.delay_dep), t.train_no
      FROM trip t
      JOIN sched s1 ON s1.trip_id = t.trip_id JOIN station a ON a.stop_id = s1.stop_id AND a.name = ?
      JOIN sched s2 ON s2.trip_id = t.trip_id AND s2.stop_seq > s1.stop_seq JOIN station b ON b.stop_id = s2.stop_id AND b.name = ?
      JOIN run r1 ON r1.trip_id = t.trip_id AND r1.stop_seq = s1.stop_seq
      JOIN run r2 ON r2.trip_id = t.trip_id AND r2.stop_seq = s2.stop_seq AND r2.service_date = r1.service_date
      WHERE t.network = 'zeleznica' AND t.mode != 'bus' AND r1.service_date BETWEEN '2026-10-11' AND '2026-10-28'""", (od, do)).fetchall()
    po_uri = defaultdict(list)
    for d, dep, z1, arr, z2, no in rows:
        if datetime.strptime(d, "%Y-%m-%d").weekday() >= 5 or z1 is None or z2 is None: continue
        h = (dep // 3600) % 24
        po_uri[h].append(((arr + z2) - (dep + z1)) / 60)
    print(f"## {od} → {do} (vlak, {len(rows)} voženj; avto {rel})")
    for h in sorted(po_uri):
        v = sorted(po_uri[h]); a = sorted(ac[rel].get(h, []))
        if not a: continue
        print(f"  {h:2d}h vlak med {st.median(v):5.0f} p90 {v[int(len(v)*.9)]:5.0f} (n {len(v)}) | avto AC med {st.median(a)/60:5.0f} p90 {a[int(len(a)*.9)]/60:5.0f}")
