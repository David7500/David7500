import sqlite3, sys, statistics as st
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo
TZ = ZoneInfo("Europe/Ljubljana")
c = sqlite3.connect("file:/var/tmp/promet-stat.sqlite?mode=ro", uri=True)
print(c.execute("SELECT MIN(ts), MAX(ts), COUNT(DISTINCT relacija) FROM ac").fetchone())
po = defaultdict(lambda: defaultdict(list))
prosto = {}
for rel, ts, cas, pr in c.execute("SELECT relacija, ts, cas_s, prosto_s FROM ac"):
    d = datetime.fromtimestamp(ts, TZ)
    if d.weekday() < 5 and cas:
        po[rel][d.hour].append(cas)
    prosto[rel] = pr
for rel in sorted(po):
    ure = po[rel]
    vrh = max(ure, key=lambda h: st.median(ure[h]))
    print(f"{rel:28s} prosto {prosto[rel]/60:5.1f} min | med 3h {st.median(ure.get(3,[0]) or [0])/60:5.1f}"
          f" 7h {st.median(ure.get(7,[0]))/60:5.1f} 8h {st.median(ure.get(8,[0]))/60:5.1f}"
          f" 15h {st.median(ure.get(15,[0]))/60:5.1f} 16h {st.median(ure.get(16,[0]))/60:5.1f}"
          f" | vrh {vrh}h {st.median(ure[vrh])/60:5.1f}, p90 vrh {sorted(ure[vrh])[int(len(ure[vrh])*.9)]/60:5.1f} | n {sum(len(v) for v in ure.values())}")
print("fcd:", c.execute("SELECT MIN(ts), MAX(ts), COUNT(DISTINCT odsek) FROM fcd").fetchone())
