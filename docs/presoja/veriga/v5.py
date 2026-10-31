import csv, sqlite3, collections, statistics as st
from datetime import datetime
from zoneinfo import ZoneInfo
TZ = ZoneInfo("Europe/Ljubljana")
c = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
rows = [r for r in csv.DictReader(open("/tmp/veriga_pari.csv")) if r["ag"] == "1118"]
info = {t: (f, l, n) for t, f, l, n in c.execute("SELECT trip_id, first_seq, last_seq, train_no FROM trip WHERE agency='1118'")}
ime = {}
def stopname(t, seq):
    k = (t, seq)
    if k not in ime:
        r = c.execute("SELECT st.name FROM sched s JOIN station st ON st.stop_id=s.stop_id WHERE s.trip_id=? AND s.stop_seq=?", k).fetchone()
        ime[k] = r[0] if r else None
    return ime[k]
runs = {}
for d in sorted({r["dan"] for r in rows}):
    for t, seq, da, dd, fts, a, dp in c.execute("""SELECT r.trip_id, r.stop_seq, r.delay_arr, r.delay_dep, r.feed_ts, s.arr_s, s.dep_s FROM run r JOIN trip t ON t.trip_id=r.trip_id AND t.agency='1118'
            JOIN sched s ON s.trip_id=r.trip_id AND s.stop_seq=r.stop_seq WHERE r.service_date=?""", (d,)):
        runs.setdefault((d, t), {})[seq] = (da, dd, fts, a, dp)
A = collections.Counter(); prim = []
for r in rows:
    d, p, x, T = r["dan"], r["p"], r["x"], int(r["T"]); P = T - int(float(r["x_start"])) + int(float(r["x_start"]))  # T je ze epoha
    is25 = r["x_no"] == "25"; eve = datetime.fromtimestamp(T, TZ).hour >= 18
    fp, lp_, _ = info.get(p, (None, None, None)); fx, lx, _ = info.get(x, (None, None, None))
    rp, rx = runs.get((d, p), {}), runs.get((d, x), {})
    g = ("LPP25" if is25 else "1118") + (" zvečer" if eve else " dan")
    A[g + " pari"] += 1
    A[g + " p v feedu"] += bool(rp); A[g + " x v feedu"] += bool(rx)
    if not rp or not rx or lp_ not in rp or fx not in rx: continue
    da, dd, fts, a, dp = rp[lp_]; pz = da if da is not None else dd
    xda, xdd, xfts, xa, xdp = rx[fx]; xz = xdd if xdd is not None else xda
    if pz is None or xz is None: continue
    base = T - (xdp if xdp is not None else xa)          # polnoc - 12 h
    p_arr = base + a + pz; x_dep = T + xz
    # dokaz: feed je o postanku govoril po dogodku
    if xfts < x_dep or fts < p_arr: A[g + " brez potrditve"] += 1; continue
    A[g + " izmerjeno"] += 1
    if p_arr > T + 60:
        A[g + " prejsnja po uri"] += 1
        if xz <= 120 and x_dep < p_arr - 60:
            A[g + " ta tocna, prejsnja se vozi"] += 1
            prim.append((d, datetime.fromtimestamp(T, TZ).strftime("%H:%M"), info[p][2], round(pz/60), info[x][2], round(xz/60),
                         datetime.fromtimestamp(p_arr, TZ).strftime("%H:%M"), stopname(p, lp_) == stopname(x, fx)))
        else: A[g + " ta pozna"] += 1
for k in sorted(A): print(f"{k}: {A[k]}")
print("primeri (dan, T, prejsnja, zamuda na cilju, ta, zamuda odhoda, prejsnja na cilju ob, ista postaja):")
for p in sorted(prim): print(" ", p)
