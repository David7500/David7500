"""Prezgodnji odhodi po prevozniku: odhod z vmesnega postanka vsaj minuto pred voznim redom."""
import sqlite3
c = sqlite3.connect("file:/var/tmp/kajros-stat.sqlite?mode=ro", uri=True)
print("prevoznik | postankov | odhod ≥ 1 min prej | ≥ 2 min prej | ≥ 3 min prej")
for r in c.execute("""
  SELECT t.agency, COUNT(*),
    100.0*AVG(CAST(COALESCE(r.delay_dep, r.delay_arr)/60.0 - 0.5 AS INT) <= -1 AND COALESCE(r.delay_dep, r.delay_arr) < -30),
    100.0*AVG(COALESCE(r.delay_dep, r.delay_arr) <= -90),
    100.0*AVG(COALESCE(r.delay_dep, r.delay_arr) <= -150)
  FROM run r JOIN trip t USING(trip_id)
  WHERE r.service_date BETWEEN '2026-10-15' AND '2026-10-28' AND r.stop_seq > t.first_seq AND r.stop_seq < t.last_seq
    AND COALESCE(r.delay_dep, r.delay_arr) IS NOT NULL AND ABS(COALESCE(r.delay_dep, r.delay_arr)) < 10800
  GROUP BY 1 ORDER BY 2 DESC"""):
    print(" | ".join(f"{x:.1f}" if isinstance(x, float) else str(x) for x in r))
