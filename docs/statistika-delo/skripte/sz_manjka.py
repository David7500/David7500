import sqlite3, re
from collections import Counter, defaultdict
c = sqlite3.connect("file:/var/tmp/kajros-stat.sqlite?mode=ro", uri=True)
OD, DO = "2026-10-11", "2026-10-28"
plan = c.execute("""
  SELECT t.trip_id, d.date, t.train_no, t.mode FROM trip t JOIN service_day d USING(service_id)
  WHERE t.network='zeleznica' AND d.date BETWEEN ? AND ?""", (OD, DO)).fetchall()
imajo = set(c.execute("SELECT DISTINCT trip_id, service_date FROM run WHERE service_date BETWEEN ? AND ?", (OD, DO)).fetchall())
sz = set(c.execute("SELECT DISTINCT trip_id, service_date FROM sz_zamuda WHERE service_date BETWEEN ? AND ?", (OD, DO)).fetchall())
po_vrsti = defaultdict(lambda: [0, 0, 0]); po_dnevu = defaultdict(lambda: [0, 0])
for trip, d, no, mode in plan:
    vrsta = "BUS (nadomestni)" if mode == "bus" else (re.match(r"[A-Z]+", no or "?") or ["?"])[0]
    k = po_vrsti[vrsta]; k[0] += 1; k[1] += (trip, d) in imajo; k[2] += (trip, d) in sz
    po_dnevu[d][0] += 1; po_dnevu[d][1] += (trip, d) in imajo
print("vrsta | načrtovanih | s podatkom | z zemljevida SŽ")
for v, (n, i, s) in sorted(po_vrsti.items(), key=lambda x: -x[1][0]):
    print(f"{v} | {n} | {i} ({100*i/n:.0f} %) | {s} ({100*s/n:.0f} %)")
print("dan | načrtovanih | s podatkom")
for d in sorted(po_dnevu):
    n, i = po_dnevu[d]; print(d, n, i, f"{100*i/n:.0f} %")
# Cilj: SŽ zamudo ob prihodu ponastavi na 0 (Vrsta 2)
rows = c.execute("""
  SELECT o.trip_id, o.service_date, o.observed_at, COALESCE(o.delay_arr, o.delay_dep)
  FROM obs o JOIN trip t USING(trip_id)
  WHERE t.network='zeleznica' AND t.mode != 'bus' AND o.stop_seq = t.last_seq AND o.service_date BETWEEN ? AND ?
  ORDER BY 1,2,3""", (OD, DO)).fetchall()
ser = defaultdict(list)
for trip, d, ts, z in rows:
    if z is not None: ser[(trip, d)].append(z)
n = len(ser); pad = sum(1 for s in ser.values() if max(s) >= 120 and s[-1] < 60)
print(f"cilj: {n} prihodov s serijo; najvišja ≥ 2 min, zadnja < 1 min: {pad} ({100*pad/max(n,1):.1f} %)")
print("run na cilju po tem:", c.execute("""
  SELECT COUNT(*), SUM(COALESCE(r.delay_arr, r.delay_dep) < 60) FROM run r JOIN trip t USING(trip_id)
  WHERE t.network='zeleznica' AND t.mode != 'bus' AND r.stop_seq = t.last_seq AND r.service_date BETWEEN ? AND ?""", (OD, DO)).fetchone())
