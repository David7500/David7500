import sqlite3
from collections import Counter
from datetime import datetime
db = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
q = """SELECT o.trip_id, o.service_date, t.train_no, o.observed_at, COUNT(*)
FROM obs o JOIN trip t ON t.trip_id = o.trip_id AND t.network='zeleznica' AND t.mode != 'bus'
WHERE o.service_date >= '2026-11-01' AND o.delay_arr IS NOT NULL AND o.delay_dep IS NOT NULL
GROUP BY o.trip_id, o.service_date, o.observed_at"""
rows = db.execute(q).fetchall()
print("zapisov derp (oba polja) po vožnji in trenutku:", len(rows))
po_min = Counter(datetime.fromtimestamp(r[3]).strftime("%m-%d %H:%M") for r in rows)
print("največ voženj v isti minuti:", po_min.most_common(12))
vo = Counter((r[0], r[1]) for r in rows); print("voženj-dni z derp zapisi:", len(vo))
