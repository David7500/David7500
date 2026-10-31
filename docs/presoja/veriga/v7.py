import csv, sqlite3, collections, statistics as st
from datetime import datetime
from zoneinfo import ZoneInfo
TZ = ZoneInfo("Europe/Ljubljana")
c = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
rows = list(csv.DictReader(open("/tmp/veriga_pari.csv")))
I = lambda v: int(float(v)) if v not in ("", None) else None
fs = dict(c.execute("SELECT trip_id, first_seq FROM trip WHERE network='avtobus'").fetchall())
dep = {}
for d in sorted({r["dan"] for r in rows}):
    for t, s, ts, z in c.execute("SELECT trip_id, MIN(stop_seq), prehod_ts, zamuda_s FROM gps_prehod WHERE service_date=? AND je_cilj=0 GROUP BY trip_id", (d,)):
        f = fs.get(t)
        if f is not None and s - f <= 2: dep[(d, t)] = (ts, z)
N = {"1119": "Nomago", "1121": "AP MS", "1123": "Arriva"}
A = collections.Counter(); Z = collections.defaultdict(list)
for r in rows:
    if r["ag"] not in N or not (r["lega_p"] and r["lega_x"] and int(r["n_p"]) >= 5 and int(r["n_x"]) >= 5): continue
    T = int(r["T"]); g = N[r["ag"]]; same = r["lega_p"] == r["lega_x"]
    pl, xf = I(r["p_last"]), I(r["x_first"]); pa = I(r["p_arr"]) or pl; xd = dep.get((r["dan"], r["x"]))
    A[g, "pari"] += 1
    for m in (10, 5, 1):
        t = T - 60 * m
        brez_svoje = xf is None or xf > t
        A[g, m, "svoja lega"] += not brez_svoje
        # predlog R: ta brez svoje lege, prejsnja z lego <= 2 min in se ni na cilju
        R = brez_svoje and pl is not None and pl >= t - 120 and pa is not None and pa > t
        if R:
            A[g, m, "R"] += 1; A[g, m, "R isto"] += same
            if m == 5 and xd: Z[g, "R"].append(xd[1])
        elif m == 5 and xd: Z[g, "ne R"].append(xd[1])
pc = lambda a, b: f"{100*a/b:.0f}%" if b else "-"
for g in N.values():
    n = A[g, "pari"]
    print(g, "pari", n, " | ".join(f"T-{m}: svoja lega {pc(A[g,m,'svoja lega'],n)}, R {A[g,m,'R']} ({pc(A[g,m,'R'],n)}) isto vozilo {pc(A[g,m,'R isto'],A[g,m,'R'])}" for m in (10, 5, 1)))
    for k in ("R", "ne R"):
        v = Z[g, k]
        if v: print(f"   odhod te, kadar R ob T-5 {'DA' if k=='R' else 'NE'}: n={len(v)} mediana {st.median(v)/60:+.1f} min, nad 2 min {pc(sum(z>120 for z in v), len(v))}")
# LPP 25: konec prejsnje = zacetek te? in vecer 30.10
nm = {}
def ime(t, last):
    k = (t, last)
    if k not in nm:
        q = "SELECT st.name FROM sched s JOIN station st ON st.stop_id=s.stop_id WHERE s.trip_id=? ORDER BY s.stop_seq " + ("DESC" if last else "ASC") + " LIMIT 1"
        x = c.execute(q, (t,)).fetchone(); nm[k] = x[0] if x else None
    return nm[k]
L = [r for r in rows if r["ag"] == "1118" and r["x_no"] == "25"]
ista = sum(ime(r["p"], True) == ime(r["x"], False) for r in L)
print("LPP 25 pari", len(L), "konec prejsnje = izhodisce te:", ista)
no = dict(c.execute("SELECT trip_id, train_no FROM trip WHERE agency='1118'").fetchall())
print("LPP 25 30.10 zvečer z vozilom derp (T, prejsnja, konec prejsnje po voznem redu, isto vozilo, izhodisce):")
for r in sorted(L, key=lambda r: r["T"]):
    T = int(r["T"])
    if r["dan"] == "2026-10-30" and datetime.fromtimestamp(T, TZ).hour >= 18 and r["sd_p"] and r["sd_x"]:
        print("  ", datetime.fromtimestamp(T, TZ).strftime("%H:%M"), no.get(r["p"]), datetime.fromtimestamp(I(r["p_end"]), TZ).strftime("%H:%M"), r["sd_p"] == r["sd_x"], ime(r["x"], False))
