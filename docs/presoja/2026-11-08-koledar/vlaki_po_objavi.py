"""Skladnost zapisov vlakov po objavi popravka (koledar 8. 11. 2026).

Isto merilo kot `2026-11-07-koledar/skladnost_po_objavi.py` in `razvrsti.py`,
z objavo in dnevi kot argumentoma. Samo branje produkcijske baze: vrstice gredo
v /var/tmp/koledar-vlaki-<dan>.sqlite, račun teče na kopiji. Na arwenu:

  python3 vlaki_po_objavi.py REL DAN [DAN ...]

REL = epoha objave (68294cf z bd9365e: 7. 11. 2026 11.35.14 = 1794047714).
Vožnja-dan šteje „po objavi“, kadar so vsi njeni zapisi `run` po REL.
"""
import os, sqlite3, sys, time
from collections import Counter, defaultdict
from datetime import datetime

REL = int(sys.argv[1])
DNI = tuple(sys.argv[2:])
KOP = f"/var/tmp/koledar-vlaki-{DNI[-1]}.sqlite"
if not os.path.exists(KOP):
    k = sqlite3.connect(KOP)
    k.execute("ATTACH 'file:/var/lib/kajros/kajros.sqlite?mode=ro' AS p")
    dni = "(" + ",".join(f"'{d}'" for d in DNI) + ")"
    k.executescript(f"""
    CREATE TABLE trip AS SELECT trip_id, train_no, first_seq, last_seq, start_s FROM p.trip
      WHERE network='zeleznica' AND mode != 'bus';
    CREATE TABLE run AS SELECT r.* FROM trip t JOIN p.run r ON r.trip_id=t.trip_id
      WHERE r.service_date IN {dni};
    CREATE TABLE obs AS SELECT o.* FROM trip t JOIN p.obs o ON o.trip_id=t.trip_id
      WHERE o.service_date IN {dni};
    CREATE TABLE sched AS SELECT s.trip_id, s.stop_seq, s.arr_s, s.dep_s, s.stop_id FROM trip t
      JOIN p.sched s ON s.trip_id=t.trip_id;
    CREATE TABLE sz AS SELECT z.* FROM trip t JOIN p.sz_zamuda z ON z.trip_id=t.trip_id
      WHERE z.service_date IN {dni};
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
    sk = (f"a {d} po objavi" if min(fts) >= REL else f"a' {d} čez objavo" if max(fts) >= REL
          else f"_ {d} pred")
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
             for i in range(len(t)) for j in range(i + 1, len(t))
             if t[j][0] > t[i][0] and t[i][1] - t[j][1] >= 120]
    c["stal_postankov"] += len(stal)
    for k_, v in (("ura_nazaj", nazaj), ("stal>=10", stal), ("prihod_po_odhodu", ppo)):
        if v:
            c[k_] += 1
            if sk.startswith("a "): krsi.append((sk, k_, no, tid, d, v[:3]))
print("== skladnost (voženj-dni z run; delež)")
for sk in sorted(st):
    c = st[sk]; n = c["voženj"]
    print(sk, n, {k: f"{v} ({100*v/n:.1f} %)" for k, v in c.items() if k != "voženj"})
print("== kršitve (samo vožnje-dni v celoti po objavi)")
for x in krsi: print(*x)

# Ali ima kršitev skok zemljevida nazaj z višjo zamudo (razvrsti.py), po objavi
# samo zapisi zemljevida (observed_at - feed_ts < 5 s).
print("== kršitve po vrsti zaporedja zemljevida")
raz = Counter(); prim = defaultdict(list)
for (tid, d) in sorted({(x[3], x[4]) for x in krsi}):
    rows = db.execute("""SELECT stop_seq, delay_arr, delay_dep, observed_at FROM obs WHERE trip_id=? AND service_date=?
        AND observed_at >= ? AND observed_at - feed_ts < 5 ORDER BY observed_at""", (tid, d, REL)).fetchall()
    mx = None; skok = False
    for seq, da, dd, oa in rows:
        if mx and seq < mx[0] and (dd or 0) > mx[1]: skok = True
        if mx is None or seq >= mx[0]: mx = (seq, dd or 0)
    k_ = "skok_nazaj_visja" if skok else "brez_skoka"
    raz[k_] += 1; prim[k_].append(f"{ime[tid][0]} {d}")
print(dict(raz)); print({k: v[:30] for k, v in prim.items()})

print("== nepotrjeni in preklicani (sz_zamuda, run)")
n_sz = db.execute("SELECT COUNT(*), COUNT(DISTINCT trip_id || service_date) FROM sz").fetchone()
print("sz_zamuda vrstic, voženj-dni:", n_sz)
c = Counter()
for (oa, fts) in db.execute("SELECT observed_at, feed_ts FROM obs WHERE observed_at >= ?", (REL,)):
    c["zemljevid" if oa - fts < 5 else "derp"] += 1
print("obs po objavi po viru:", dict(c))
c = Counter()
for oa, fts in db.execute("SELECT observed_at, feed_ts FROM obs WHERE observed_at >= ? AND observed_at - feed_ts >= 5", (REL,)):
    c[time.strftime("%m-%d %H", time.localtime(oa))] += 1
print("derp (zamik >= 5 s) po uri:", sorted(c.items()))
