import sqlite3
from collections import Counter, defaultdict
db = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
q = """SELECT r.trip_id, r.service_date, r.stop_seq, r.delay_arr, r.delay_dep, s.arr_s, s.dep_s, t.first_seq, t.last_seq
FROM run r JOIN trip t ON t.trip_id = r.trip_id AND t.network = 'zeleznica' AND t.mode != 'bus'
JOIN sched s ON s.trip_id = r.trip_id AND s.stop_seq = r.stop_seq
WHERE r.service_date >= '2026-09-01' ORDER BY r.trip_id, r.service_date, r.stop_seq"""
vo = defaultdict(list)
for row in db.execute(q): vo[(row[0], row[1])].append(row[2:])
def obd(d): return "a 09-01..10-09" if d < "2026-10-10" else "b 10-10..10-31" if d < "2026-11-01" else "c 11-01.."
st = defaultdict(Counter)
for (tid, d), xs in vo.items():
    o = obd(d); c = st[o]; c["voženj-dni"] += 1
    t = []
    for seq, da, dd, arr, dep, f, l in xs:
        if seq == f: continue          # izhodišče ne poroča
        a = arr + da if da is not None and arr is not None else None
        p = dep + dd if dd is not None and dep is not None else None
        if seq == l: p = None          # odhod na cilju ni dogodek
        if a is not None and p is not None and a - p >= 120: c["prihod_po_odhodu>=2min"] += 1; c["_v"] += 0
        if a is not None and p is not None and p - a >= 600 and (dep - arr) <= 120: c["stal>=10min_kratek_postanek"] += 1
        for x in (a, p):
            if x is not None: t.append((seq, x))
    slab = any(t[i][1] - t[j][1] >= 120 for i in range(len(t)) for j in range(i+1, len(t)) if t[j][0] > t[i][0])
    c["ura_nazaj>=2min"] += slab
    # V-osamelec: vrednost >=10 min nizja od obeh sosedov
    dl = [(seq, dd if dd is not None else da) for seq, da, dd, arr, dep, f, l in xs if seq != f and (dd is not None or da is not None)]
    c["V_osamelec"] += any(dl[i][1] <= dl[i-1][1] - 600 and dl[i][1] <= dl[i+1][1] - 600 for i in range(1, len(dl)-1))
for o in sorted(st):
    c = st[o]; n = c["voženj-dni"]
    print(o, n, {k: f"{v} ({100*v/n:.1f} %)" for k, v in c.items() if k not in ("voženj-dni", "_v")})
