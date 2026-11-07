"""Razvrsti kršitve po objavi: ali ima vožnja skok zemljevida nazaj z višjo zamudo."""
import sqlite3, sys
from collections import Counter, defaultdict
REL = 1793972735
db = sqlite3.connect("/var/tmp/koledar-vlaki.sqlite")
ime = {r[0]: r[1] for r in db.execute("SELECT trip_id, train_no FROM trip")}
import re
vozn = {}
for l in open("/var/tmp/koledar-vlaki.txt"):
    m = re.match(r"(a 6.11 po objavi|b 7.11 do zdaj) (\S+) .*? (\d+) (2026-11-0[67]) ", l)
    if m: vozn.setdefault((m[3], m[4]), set()).add(m[2])
raz = Counter(); prim = defaultdict(list)
for (tid, d), vr in vozn.items():
    rows = db.execute("""SELECT stop_seq, delay_arr, delay_dep, observed_at FROM obs WHERE trip_id=? AND service_date=?
        AND observed_at >= ? AND observed_at - feed_ts < 5 ORDER BY observed_at""", (tid, d, REL)).fetchall()
    mx = None; skok = False; prej0 = False
    for seq, da, dd, oa in rows:
        if mx and seq < mx[0] and (dd or 0) > mx[1]: skok = True
        if mx is None or seq >= mx[0]: mx = (seq, dd or 0)
    k = "skok_nazaj_visja" if skok else "brez_skoka"
    raz[k] += 1; prim[k].append(ime[tid])
print(raz); print({k: v[:25] for k, v in prim.items()})
# derp (zamik >= 5 s) po objavi, po uri
c = Counter(); n = Counter()
for oa, fts, tid in db.execute("SELECT observed_at, feed_ts, trip_id FROM obs WHERE observed_at >= ? AND observed_at - feed_ts >= 5", (REL,)):
    import time; h = time.strftime("%m-%d %H", time.localtime(oa)); c[h] += 1
print("zamik>=5s po uri:", sorted(c.items()))
