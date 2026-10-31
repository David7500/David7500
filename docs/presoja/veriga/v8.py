"""Veriga, novo pravilo: ponovitev v času za pare blokov (lege NAP v `lega`).

Ob t = T-10, T-5, T-1 min (T = odhod te vožnje po voznem redu) pogledamo, kaj
bi videl prikaz: zadnjo lego prejšnje vožnje (kot `vehicle_now`), ali ima ta
vožnja že svojo lego, ali je `gps_prehod` prihod prejšnje na cilj že zapisal
(`zapisano_ts`, to v živo premakne `last_measured` na končno), in kako daleč je
vozilo od končne prejšnje. Resnica: prejšnja ob t še vozi (prihod na cilj po
`gps_prehod.je_cilj` > t) in ta vožnja dobi isto vozilo (prevladujoče v `lega`).

Baza samo za branje. Izpis: povzetek po prevozniku in pravilu.
"""
import collections
import math
import sqlite3
import sys
import time
from datetime import date, datetime, time as dtime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Ljubljana")
c = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
q = lambda s, *a: c.execute(s, a).fetchall()


def polnoc(d):
    return int(datetime.combine(d, dtime(12), TZ).timestamp()) - 43200


def razdalja(a, b, x, y):
    k = math.pi / 180
    dx = (y - b) * k * math.cos((a + x) / 2 * k)
    dy = (x - a) * k
    return 6371000 * math.hypot(dx, dy)


d0 = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date(2026, 10, 24)
dni = int(sys.argv[2]) if len(sys.argv) > 2 else 7
AG = ("1119", "1121", "1123", "1118")
ODMIKI = (600, 300, 60)
SVEZE = 180
R_CILJ = (0, 100, 200, 300, 500)

# stevci[(ag, odmik, pravilo)] = [prikazano, prav, vseh_prav]
st = collections.defaultdict(lambda: [0, 0])
vsi = collections.Counter()      # (ag, odmik) -> pari z resnico
prav_vsi = collections.Counter()  # (ag, odmik) -> pari, kjer je trditev prava
napake = collections.Counter()
caka = collections.defaultdict(lambda: [0, 0])
t0 = time.time()
for i in range(dni):
    d = d0 + timedelta(i)
    ds = d.isoformat()
    P = polnoc(d)
    rows = q("""SELECT t.trip_id, t.block_id, t.start_s, t.end_s, t.agency, t.first_seq, t.last_seq
                FROM trip t JOIN service_day sd ON sd.service_id = t.service_id AND sd.date = ?
                WHERE t.network = 'avtobus' AND t.block_id IS NOT NULL
                  AND t.agency IN ('1119','1121','1123','1118')""", ds)
    byb = collections.defaultdict(list)
    for r in rows:
        byb[r[1]].append(r)
    pari = []
    for L in byb.values():
        for x in L:
            if x[2] is None:
                continue
            kand = [p for p in L if p[0] != x[0] and p[3] is not None and p[3] <= x[2]]
            if kand:
                pari.append((max(kand, key=lambda p: p[3]), x))
    tocka = {}
    for tid, seq, lat, lon in q("""SELECT s.trip_id, s.stop_seq, st.lat, st.lon FROM sched s
            JOIN station st ON st.stop_id = s.stop_id
            JOIN trip t ON t.trip_id = s.trip_id AND (s.stop_seq = t.first_seq OR s.stop_seq = t.last_seq)
            JOIN service_day sd ON sd.service_id = t.service_id AND sd.date = ?
            WHERE t.block_id IS NOT NULL AND t.agency IN ('1119','1121','1123','1118')""", ds):
        tocka[(tid, seq)] = (lat, lon)
    dom = {}
    best = {}
    for tid, voz, n in q("SELECT trip_id, vozilo, COUNT(*) FROM lega WHERE service_date = ? GROUP BY trip_id, vozilo", ds):
        if n > best.get(tid, 0):
            best[tid] = n
            dom[tid] = voz
    cilj = {tid: (pts, zts) for tid, pts, zts in
            q("SELECT trip_id, prehod_ts, zapisano_ts FROM gps_prehod WHERE service_date = ? AND je_cilj = 1", ds)}
    for p, x in pari:
        ag = x[4]
        pt, xt = p[0], x[0]
        if pt not in cilj or pt not in dom or xt not in dom:
            continue
        T = P + x[2]
        prihod, zapisan = cilj[pt]
        konec = tocka.get((pt, p[6]))
        zacetek = tocka.get((xt, x[5]))
        isto = dom[pt] == dom[xt]
        for o in ODMIKI:
            t = T - o
            vozi = prihod > t
            pravo = vozi and isto
            vsi[(ag, o)] += 1
            prav_vsi[(ag, o)] += pravo
            g = c.execute("SELECT ts, lat, lon FROM lega WHERE service_date = ? AND trip_id = ? AND ts <= ? "
                          "ORDER BY ts DESC LIMIT 1", (ds, pt, t)).fetchone()
            svoja = c.execute("SELECT 1 FROM lega WHERE service_date = ? AND trip_id = ? AND ts BETWEEN ? AND ? LIMIT 1",
                              (ds, xt, t - SVEZE, t)).fetchone() is not None

            def zapisi(ime, kaze):
                s = st[(ag, o, ime)]
                if kaze:
                    s[0] += 1
                    s[1] += pravo
            zapisi("glava zdaj", True)
            zapisi("pilula zdaj", g is not None and t - g[0] <= 900 and not svoja)
            sveza = g is not None and t - g[0] <= SVEZE and not svoja
            dc = razdalja(g[1], g[2], *konec) if (g is not None and konec) else None
            na_cilju_zapisan = zapisan <= t
            for R in R_CILJ:
                kaze = sveza and not na_cilju_zapisan and (R == 0 or dc is None or dc > R)
                zapisi(f"novo R={R}", kaze)
                if R == 200 and kaze and not pravo:
                    napake[(ag, o, "prejsnja ze na cilju" if not vozi else "drugo vozilo")] += 1
            zapisi("brez zapisa cilja, R=200", sveza and (dc is None or dc > 200))
            # Vozilo, ki je prejsnjo koncalo in stoji na izhodiscu te
            if sveza and not vozi and zacetek:
                dz = razdalja(g[1], g[2], *zacetek)
                if dz <= 200:
                    cc = caka[(ag, o)]
                    cc[0] += 1
                    cc[1] += isto
    print(ds, "parov", len(pari), "%.0fs" % (time.time() - t0), file=sys.stderr, flush=True)

IME = {"1119": "Nomago", "1121": "AP MS", "1123": "Arriva", "1118": "LPP prim."}
for ag in AG:
    for o in ODMIKI:
        n = vsi[(ag, o)]
        if not n:
            continue
        print(f"\n{IME[ag]} T-{o // 60} min: parov {n}, trditev prava pri {prav_vsi[(ag, o)]} ({100 * prav_vsi[(ag, o)] / n:.0f} %)")
        for ime in ["glava zdaj", "pilula zdaj"] + [f"novo R={R}" for R in R_CILJ] + ["brez zapisa cilja, R=200"]:
            s = st[(ag, o, ime)]
            if s[0]:
                print(f"  {ime:26s} kaže {100 * s[0] / n:5.1f} %  prav {100 * s[1] / s[0]:5.1f} %  "
                      f"ujame {100 * s[1] / max(1, prav_vsi[(ag, o)]):5.1f} % pravih")
        for k in ("prejsnja ze na cilju", "drugo vozilo"):
            if napake[(ag, o, k)]:
                print(f"  napaka R=200: {k} {napake[(ag, o, k)]}")
        cc = caka[(ag, o)]
        if cc[0]:
            print(f"  čaka na izhodišču (≤ 200 m, končala): {cc[0]}, isto vozilo {100 * cc[1] / cc[0]:.1f} %")
