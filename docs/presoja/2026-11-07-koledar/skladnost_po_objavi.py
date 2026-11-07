"""Skladnost zapisov vlakov po objavi 88ec114 (6. 11. 2026 14:45:35).

Samo branje produkcijske baze: potrebne vrstice gredo v /var/tmp/koledar-vlaki.sqlite,
račun teče na kopiji. Poženi na arwenu: python3 skladnost_po_objavi.py [zagoni_ts ...]
(zagoni_ts = epohe ponovnih zagonov storitve, za izbruh derp.si).
"""
import json, os, sqlite3, statistics, sys
from collections import Counter, defaultdict
from datetime import datetime
REL = 1793972735
DNI = ("2026-11-06", "2026-11-07")
KOP = "/var/tmp/koledar-vlaki.sqlite"
if not os.path.exists(KOP):
    k = sqlite3.connect(KOP)
    k.execute("ATTACH 'file:/var/lib/kajros/kajros.sqlite?mode=ro' AS p")
    k.executescript(f"""
    CREATE TABLE trip AS SELECT trip_id, train_no, first_seq, last_seq, start_s FROM p.trip
      WHERE network='zeleznica' AND mode != 'bus';
    CREATE TABLE run AS SELECT r.* FROM trip t JOIN p.run r ON r.trip_id=t.trip_id
      WHERE r.service_date IN {DNI};
    CREATE TABLE obs AS SELECT o.* FROM trip t JOIN p.obs o ON o.trip_id=t.trip_id
      WHERE o.service_date IN {DNI};
    CREATE TABLE sched AS SELECT s.trip_id, s.stop_seq, s.arr_s, s.dep_s, s.stop_id FROM trip t
      JOIN p.sched s ON s.trip_id=t.trip_id;
    CREATE TABLE sz AS SELECT z.* FROM trip t JOIN p.sz_zamuda z ON z.trip_id=t.trip_id
      WHERE z.service_date IN {DNI};
    CREATE TABLE meta AS SELECT * FROM p.meta WHERE key IN ('zamude_sz','napovedi_vlakov');
    """)
    k.commit(); k.close()
db = sqlite3.connect(KOP)
ime = {r[0]: r[1:] for r in db.execute("SELECT trip_id, train_no, first_seq, last_seq FROM trip")}
vo = defaultdict(list)
for row in db.execute("""SELECT r.trip_id, r.service_date, r.stop_seq, r.delay_arr, r.delay_dep, r.feed_ts,
    s.arr_s, s.dep_s FROM run r JOIN sched s USING(trip_id, stop_seq) ORDER BY 1,2,3"""):
    vo[(row[0], row[1])].append(row[2:])
def ura(ts): return datetime.fromtimestamp(ts).strftime("%H:%M:%S")
st = defaultdict(Counter); krsi = []
for (tid, d), xs in vo.items():
    no, f, l = ime[tid]
    fts = [x[3] for x in xs]
    if d == DNI[0]:
        sk = "a 6.11 po objavi" if min(fts) >= REL else "a' 6.11 čez objavo" if max(fts) >= REL else "_ 6.11 pred"
    else:
        sk = "b 7.11 do zdaj"
    c = st[sk]; c["voženj"] += 1
    t = []; stal = []; ppo = []
    for seq, da, dd, fts_, arr, dep in xs:
        if seq == f: continue
        a = arr + da if da is not None and arr is not None else None
        p = dep + dd if dd is not None and dep is not None else None
        if seq == l: p = None
        if a is not None and p is not None and a - p >= 120: ppo.append(seq)
        if a is not None and p is not None and p - a >= 600 and dep - arr <= 120:
            stal.append((seq, da, dd, ura(fts_)))
        for x in (a, p):
            if x is not None: t.append((seq, x, da, dd, fts_))
    nazaj = [(t[i][0], t[i][2], t[i][3], ura(t[i][4]), t[j][0], t[j][2], t[j][3], ura(t[j][4]))
             for i in range(len(t)) for j in range(i+1, len(t))
             if t[j][0] > t[i][0] and t[i][1] - t[j][1] >= 120]
    c["stal_postankov"] += len(stal)
    for k_, v in (("ura_nazaj", nazaj), ("stal>=10", stal), ("prihod_po_odhodu", ppo)):
        if v:
            c[k_] += 1
            if not sk.startswith("_"): krsi.append((sk, k_, no, tid, d, v[:3]))
print("== skladnost (voženj-dni z run; delež)")
for sk in sorted(st):
    c = st[sk]; n = c["voženj"]
    print(sk, n, {k: f"{v} ({100*v/n:.1f} %)" for k, v in c.items() if k != "voženj"})
print("== kršitve")
for x in krsi: print(*x)
print("== meta")
for k, v in db.execute("SELECT key, value FROM meta"):
    try:
        j = json.loads(v); print(k, {x: j[x] for x in j if x in ("nepotrjenih","zapisanih","nazaj","ponastavljenih","nepripeti","ts","prihodnjih")} if isinstance(j, dict) else str(j)[:200])
    except Exception: print(k, v[:200])
print("== zamik observed_at - feed_ts (s), obs vlakov")
def opis(xs):
    if not xs: return "0"
    xs = sorted(xs); n = len(xs)
    return f"n={n} p50={xs[n//2]} p90={xs[int(n*.9)]} max={xs[-1]} >=5s:{sum(x>=5 for x in xs)}"
sk = defaultdict(list)
for da, dd, fts_, oa in db.execute("SELECT delay_arr, delay_dep, feed_ts, observed_at FROM obs"):
    obd = "pred" if oa < REL else "po"
    vrsta = "samo_odhod" if da is None and dd is not None else "oba" if da is not None and dd is not None else "drugo"
    sk[(obd, vrsta)].append(oa - fts_)
for k in sorted(sk): print(k, opis(sk[k]))
zagoni = [int(x) for x in sys.argv[1:]] or [REL]
for z in zagoni:
    print(f"== obs vlakov okoli zagona {ura(z)} (po minutah, -2..+10 min)")
    m = defaultdict(Counter)
    for tid, da, dd, fts_, oa in db.execute(
            "SELECT trip_id, delay_arr, delay_dep, feed_ts, observed_at FROM obs WHERE observed_at BETWEEN ? AND ?",
            (z - 120, z + 600)):
        c = m[datetime.fromtimestamp(oa).strftime("%H:%M")]
        c["vrstic"] += 1; c["zamik>=5s"] += (oa - fts_) >= 5
        c["oba"] += da is not None and dd is not None
        c["prihodnost"] += 0
    for k in sorted(m): print(k, dict(m[k]))
