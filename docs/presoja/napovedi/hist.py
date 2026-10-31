"""Na arwenu, samo branje: kako stara je „zadnja meritev“ na dolgih odsekih NAP.

Za zaporedna prehoda k -> k+1 (gps_prehod) primerja zamudo na k (to okno kaže,
dokler vozilo ne pride na k+1) z zamudo na k+1 (resnica), po dolžini odseka po
voznem redu. Za dolge odseke (>= 15 min) še oceno iz lege sredi odseka
(razmerje razdalj zračno do obeh postankov) proti prenosu.
"""
import math
import sqlite3
import statistics
from collections import Counter, defaultdict

DNI = ("2026-10-28", "2026-10-29", "2026-10-30")
con = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)


def hav(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    h = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2)
    return 2 * 6371000 * math.asin(math.sqrt(h))


vrst = con.execute(
    "SELECT g.service_date, g.trip_id, g.stop_seq, g.zamuda_s, g.prehod_ts, s.arr_s, s.dep_s, "
    "       st.lat, st.lon, t.agency "
    "FROM gps_prehod g JOIN trip t ON t.trip_id = g.trip_id "
    "JOIN sched s ON s.trip_id = g.trip_id AND s.stop_seq = g.stop_seq "
    "JOIN station st ON st.stop_id = s.stop_id "
    f"WHERE g.service_date IN ({','.join('?' * len(DNI))}) AND t.agency IN ('1119','1121','1123')",
    DNI).fetchall()
po = defaultdict(list)
for r in vrst:
    po[(r[0], r[1])].append(r)
pasovi = [(0, 300), (300, 900), (900, 1800), (1800, 10 ** 6)]
st = {p: [] for p in pasovi}
voznje_dolgih = Counter()
voznje_napak = Counter()
ocene = {"sredina": [], "pozno": []}
for (dan, tid), rr in po.items():
    rr.sort(key=lambda r: r[2])
    napaka = False
    for a, b in zip(rr, rr[1:]):
        S = (b[5] if b[5] is not None else b[6]) - (a[6] if a[6] is not None else a[5])
        if S <= 0:
            continue
        D = b[3] - a[3]
        for p in pasovi:
            if p[0] <= S < p[1]:
                st[p].append(D)
        if S >= 900:
            voznje_dolgih[dan] += 1
            if abs(D) > 300:
                napaka = True
            # lega sredi odseka
            t_a = a[4]
            sched_a = a[4] - a[3]
            lege = con.execute(
                "SELECT ts, lat, lon FROM lega WHERE service_date = ? AND trip_id = ? "
                "AND ts > ? AND ts < ?", (dan, tid, t_a + 60, b[4] - 60)).fetchall()
            for ts_, la, lo in lege[::3]:
                d1, d2 = hav(la, lo, a[7], a[8]), hav(la, lo, b[7], b[8])
                if d1 + d2 < 1000:
                    continue
                f = d1 / (d1 + d2)
                est = ts_ - (sched_a + f * S)
                kam = "sredina" if 0.3 <= f <= 0.7 else "pozno" if 0.7 < f <= 0.95 else None
                if kam:
                    ocene[kam].append((abs(a[3] - b[3]), abs(est - b[3]), b[3] - a[3], est - a[3]))
    if napaka:
        voznje_napak[dan] += 1


def opis(xs):
    if not xs:
        return "-"
    n = len(xs)
    return (f"n={n} mediana {statistics.median(xs):+.0f} s, |D|>5 min {sum(abs(x) > 300 for x in xs) / n:.1%}, "
            f"prej za >=3 min {sum(x <= -180 for x in xs) / n:.1%}, pozneje >=3 min {sum(x >= 180 for x in xs) / n:.1%}")


print("Odsek po voznem redu -> D = zamuda na k+1 minus zamuda na k (NAP: Arriva, Nomago, AP MS)", DNI)
for p in pasovi:
    print(f"  {p[0] // 60}-{p[1] // 60 if p[1] < 10 ** 5 else 'inf'} min:", opis(st[p]))
print("odsekov >= 15 min po dnevih", dict(voznje_dolgih), "voženj z |D|>5 min na takem odseku", dict(voznje_napak))
for kam, xs in ocene.items():
    if not xs:
        continue
    n = len(xs)
    p = [x[0] for x in xs]
    g = [x[1] for x in xs]
    print(f"lega {kam} odseka n={n}: MAE prenos {statistics.mean(p) / 60:.2f} min, iz lege {statistics.mean(g) / 60:.2f} min; "
          f"v 2 min prenos {sum(x <= 120 for x in p) / n:.1%}, lega {sum(x <= 120 for x in g) / n:.1%}; "
          f"lega boljša {sum(b < a for a, b, _, _ in xs) / n:.1%}")
