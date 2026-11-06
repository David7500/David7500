import sqlite3
from collections import Counter
db = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
q = """SELECT r.trip_id, r.service_date, t.train_no, r.stop_seq, r.delay_arr, r.delay_dep, s.dep_s - s.arr_s, t.first_seq, t.last_seq
FROM run r JOIN trip t ON t.trip_id = r.trip_id AND t.network = 'zeleznica' AND t.mode != 'bus'
JOIN sched s ON s.trip_id = r.trip_id AND s.stop_seq = r.stop_seq
WHERE r.service_date >= '2026-11-01' AND r.stop_seq > t.first_seq AND r.stop_seq < t.last_seq
AND r.delay_dep - r.delay_arr >= 600 AND s.dep_s - s.arr_s <= 120"""
rows = db.execute(q).fetchall()
print("postankov:", len(rows))
print("delay_arr vrednosti:", Counter(min(r[4], 900)//60 for r in rows).most_common(8))
print("dnevi:", sorted(Counter(r[1] for r in rows).items()))
ids = {}
for r in rows: ids.setdefault((r[0], r[1], r[2]), []).append((r[3], r[4], r[5]))
for k in list(ids)[:3]: print(k, ids[k][:6])
# obs: od kod delay_arr? zadnji zapis z delay_arr za te postanke
tid, d, _ = list(ids)[0]
for o in db.execute("SELECT stop_seq, delay_arr, delay_dep, time(feed_ts,'unixepoch','localtime'), time(observed_at,'unixepoch','localtime') FROM obs WHERE trip_id=? AND service_date=? ORDER BY observed_at LIMIT 30", (tid, d)): print(" obs", o)
