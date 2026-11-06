"""Odvisnosti med vlaki: vlak B z izhodišča S proti vlaku A, ki v S pride pred njim."""
import sqlite3
from collections import defaultdict
db = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
OD = "2026-09-01"
trips = defaultdict(list); ime = {}
for tid, no, seq, name, arr, dep in db.execute("""SELECT t.trip_id, t.train_no, s.stop_seq, st.name, s.arr_s, s.dep_s
  FROM trip t JOIN sched s ON s.trip_id=t.trip_id JOIN station st ON st.stop_id=s.stop_id
  WHERE t.network='zeleznica' AND t.mode='vlak' ORDER BY t.trip_id, s.stop_seq"""):
    trips[tid].append((seq, name, arr, dep)); ime[tid] = no
zam = defaultdict(dict)   # (tid, dan) -> {seq: (arr_delay, dep_delay)}
for tid, d, seq, da, dd in db.execute("""SELECT r.trip_id, r.service_date, r.stop_seq, r.delay_arr, r.delay_dep FROM run r
  JOIN trip t ON t.trip_id=r.trip_id AND t.network='zeleznica' AND t.mode='vlak' WHERE r.service_date >= ?""", (OD,)):
    if (da is not None and abs(da) > 10800) or (dd is not None and abs(dd) > 10800): continue
    zam[(tid, d)][seq] = (da, dd)
dni = defaultdict(set)
for tid, d in zam: dni[tid].add(d)
def odhod_B(tid, d):
    z = zam.get((tid, d)); st = trips[tid]
    for seq, name, arr, dep in st[1:3]:
        if seq in z:
            da, dd = z[seq]; v = dd if dd is not None else da
            if v is not None: return v
def prihod_A(tid, d, seq, zadnji):
    z = zam.get((tid, d))
    if not z or seq not in z: return None
    da, dd = z[seq]
    return (da if da is not None else dd) if zadnji else (da if da is not None else dd)
# kandidati: A ima postanek z imenom S z arr v [tb-90min, tb-2min]
po_postaji = defaultdict(list)
for tid, st in trips.items():
    for i, (seq, name, arr, dep) in enumerate(st):
        if arr is not None and i > 0: po_postaji[name].append((tid, seq, arr, i == len(st)-1))
rez = []
for B, st in trips.items():
    if len(st) < 3 or not dni[B]: continue
    S, tb = st[0][1], st[0][3]
    if tb is None: continue
    for A, seqA, ta, zadnji in po_postaji[S]:
        if A == B or not (120 <= tb - ta <= 5400): continue
        skupni = dni[A] & dni[B]
        if len(skupni) < 8: continue
        late = hold = base_n = base_late = 0
        for d in skupni:
            dA = prihod_A(A, d, seqA, zadnji); dB = odhod_B(B, d)
            if dA is None or dB is None: continue
            pres = dA - (tb - ta)
            if pres >= 300:
                late += 1; hold += dB >= pres - 120
            elif pres < 0:
                base_n += 1; base_late += dB >= 300
        if late >= 3:
            rez.append((hold/late, late, base_late/base_n if base_n else None, ime[A], ime[B], S, (tb-ta)//60, zadnji, len(skupni)))
dobri = [r for r in rez if r[0] >= 0.7 and (r[2] is None or r[2] <= 0.2)]
bs = {r[4] for r in dobri}
print("parov z >=3 dnevi zamude A:", len(rez), "odvisnih (hold>=0.7, base<=0.2):", len(dobri), "vlakov B:", len(bs))
print("od tega obrat (A konča v S):", sum(r[7] for r in dobri))
for r in sorted(dobri, key=lambda r: (-r[1], -r[0]))[:30]:
    print(f"  {r[3]:>9} -> {r[4]:<9} {r[5]:<16} razmik {r[6]:>2} min  drži {r[0]:.0%} ({r[1]} dni)  sicer {'' if r[2] is None else f'{r[2]:.0%}'}  {'obrat' if r[7] else 'zveza'}  dni {r[8]}")
slabi = [r for r in rez if r[0] <= 0.3]
print("neodvisnih (hold<=0.3):", len(slabi))
