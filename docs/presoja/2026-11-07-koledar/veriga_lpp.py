"""Veriga LPP: razdelek 2 iz 2026-10-31-veriga.md ponovljen na straza_opazeno.

Pari (prejšnja, ta) po pravilu _block_neighbour (isto kot veriga/v3.py), vozilo
vožnje = največ vzorcev v straza_opazeno po viru. Baza samo za branje.
Uporaba: python3 veriga_lpp.py 2026-10-30 8
"""
import collections, sqlite3, sys
from datetime import date, timedelta

c = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
q = lambda s, *a: c.execute(s, a).fetchall()
d0 = date.fromisoformat(sys.argv[1]); n = int(sys.argv[2])
VIRI = {"1118": ("derp",), "lpp": ("lpp", "derp")}
A = collections.defaultdict(collections.Counter)
for i in range(n):
    ds = (d0 + timedelta(i)).isoformat()
    rows = q("""SELECT t.trip_id, t.block_id, t.start_s, t.end_s, t.agency, t.train_no FROM trip t
      JOIN service_day sd ON sd.service_id=t.service_id AND sd.date=?
      WHERE t.network='avtobus' AND t.block_id IS NOT NULL AND t.agency IN ('1118','lpp')""", ds)
    byb = collections.defaultdict(list)
    for r in rows: byb[r[1]].append(r)
    pari = []
    for L in byb.values():
        for x in L:
            if x[2] is None: continue
            kand = [p for p in L if p[0] != x[0] and p[3] is not None and p[3] <= x[2]]
            if kand: pari.append((max(kand, key=lambda p: p[3]), x))
    sv = collections.defaultdict(dict)
    for vir, voz, t, vz in q("SELECT vir, vozilo, trip_id, vzorcev FROM straza_opazeno WHERE dan=? AND vir IN ('derp','lpp')", ds):
        o = sv[(vir, t)]; o[voz] = o.get(voz, 0) + vz
    dom = lambda vir, t: (lambda o: max(o, key=o.get) if o else None)(sv.get((vir, t)))
    for p, x in pari:
        ag = x[4]; T = x[2]
        grupe = ["LPP prim" if ag == "1118" else "LPP mestni"]
        if ag == "1118" and x[5] == "25": grupe.append("LPP 25")
        vecer = T >= 18 * 3600
        for vir in ("derp", "lpp"):
            for g in grupe:
                for gg in (g, g + (" zvečer" if vecer else " dan"), f"{g} {ds}"):
                    a = A[(gg, vir)]; a["pari"] += 1
                    vp, vx = dom(vir, p[0]), dom(vir, x[0])
                    a["p_ima"] += vp is not None; a["x_ima"] += vx is not None
                    if vp and vx:
                        a["oba"] += 1; a["drugo"] += vp != vx
    print(ds, "parov", len(pari), file=sys.stderr, flush=True)
pc = lambda a, b: f"{100*a/b:.0f}%" if b else "-"
for k in sorted(A):
    a = A[k]
    if a["oba"] or "20" not in k[0]:
        print(f"{k[0]:32s} vir {k[1]:5s} pari {a['pari']:5d} | prejšnja ima vozilo {a['p_ima']:5d} ta {a['x_ima']:5d} | oba {a['oba']:5d} drugo vozilo {a['drugo']:4d} ({pc(a['drugo'], a['oba'])})")
