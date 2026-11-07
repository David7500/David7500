"""Drugo vozilo v paru po liniji (1118, derp), straza_opazeno. Uporaba: python3 veriga_lpp_linije.py 2026-11-02 5"""
import collections, sqlite3, sys
from datetime import date, timedelta
c = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
q = lambda s, *a: c.execute(s, a).fetchall()
d0 = date.fromisoformat(sys.argv[1]); n = int(sys.argv[2])
A = collections.defaultdict(lambda: [0, 0, 0]); B = collections.Counter()
for i in range(n):
    ds = (d0 + timedelta(i)).isoformat()
    rows = q("""SELECT t.trip_id, t.block_id, t.start_s, t.end_s, t.train_no FROM trip t JOIN service_day sd ON sd.service_id=t.service_id AND sd.date=?
      WHERE t.network='avtobus' AND t.block_id IS NOT NULL AND t.agency='1118'""", ds)
    byb = collections.defaultdict(list)
    for r in rows: byb[r[1]].append(r)
    sv = collections.defaultdict(dict)
    for voz, t, vz in q("SELECT vozilo, trip_id, vzorcev FROM straza_opazeno WHERE dan=? AND vir='derp'", ds):
        o = sv[t]; o[voz] = o.get(voz, 0) + vz
    dom = lambda t: max(sv[t], key=sv[t].get) if t in sv else None
    for L in byb.values():
        B[(len(L))] += 1
        for x in L:
            kand = [p for p in L if p[0] != x[0] and p[3] is not None and p[3] <= x[2]]
            if not kand: continue
            p = max(kand, key=lambda p: p[3]); a, b = dom(p[0]), dom(x[0])
            s = A[x[4]]; s[0] += 1
            if a and b: s[1] += 1; s[2] += a != b
for k, v in sorted(A.items(), key=lambda kv: -kv[1][2])[:12]:
    print(f"linija {k:4s} pari {v[0]:4d} oba {v[1]:4d} drugo {v[2]:3d} ({100*v[2]/max(1,v[1]):.0f} %)")
print("vozenj v bloku (1118):", sorted(B.items()))
