import sqlite3, time
c = sqlite3.connect("file:/var/tmp/kajros-stat.sqlite?mode=ro", uri=True)
OD, DO = "2026-10-01", "2026-10-28"
t0 = time.time()
plan = dict(((a, n), k) for a, n, k in c.execute("""
  SELECT t.agency, t.network, COUNT(*) FROM trip t JOIN service_day d USING(service_id)
  WHERE d.date BETWEEN ? AND ? GROUP BY 1,2""", (OD, DO)))
print("plan", round(time.time()-t0,1), "s")
rows = c.execute("""
  WITH cilj AS (
    SELECT r.trip_id, r.service_date, COALESCE(r.delay_arr, r.delay_dep) z
    FROM run r JOIN trip t ON t.trip_id = r.trip_id AND r.stop_seq = t.last_seq
    WHERE r.service_date BETWEEN ? AND ?),
  karkoli AS (
    SELECT DISTINCT r.trip_id, r.service_date FROM run r WHERE r.service_date BETWEEN ? AND ?)
  SELECT t.agency, t.network, COUNT(*),
         (SELECT COUNT(*) FROM cilj JOIN trip t2 USING(trip_id) WHERE t2.agency = t.agency AND t2.network = t.network AND ABS(z) < 10800),
         (SELECT 100.0*AVG(CAST(z/60.0+0.5 AS INT) <= 5) FROM cilj JOIN trip t2 USING(trip_id) WHERE t2.agency = t.agency AND t2.network = t.network AND ABS(z) < 10800),
         (SELECT AVG(z)/60.0 FROM cilj JOIN trip t2 USING(trip_id) WHERE t2.agency = t.agency AND t2.network = t.network AND ABS(z) < 10800),
         (SELECT 100.0*AVG(z >= 900) FROM cilj JOIN trip t2 USING(trip_id) WHERE t2.agency = t.agency AND t2.network = t.network AND ABS(z) < 10800)
  FROM karkoli k JOIN trip t USING(trip_id) GROUP BY 1,2 ORDER BY 3 DESC""", (OD, DO, OD, DO)).fetchall()
print("izračun", round(time.time()-t0,1), "s")
print("prevoznik | omrežje | načrtovanih | z vsaj eno meritvijo | % pokritih | s ciljem | % v 5 min na cilju | povprečje min | % ≥ 15 min")
for a, n, k, kc, p5, avg, p15 in rows:
    pl = plan.get((a, n), 0)
    print(f"{a} | {n} | {pl} | {k} | {100*k/max(pl,1):.0f} | {kc} | {p5 or 0:.1f} | {avg or 0:.2f} | {p15 or 0:.1f}")
