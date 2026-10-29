"""Obseg podatkov v kopiji baze na arwenu: kaj statistika lahko uporabi."""
import sqlite3, sys, time

DB = sys.argv[1]
PROMET = sys.argv[2] if len(sys.argv) > 2 else None
c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)


def q(sql, *a):
    t = time.time()
    r = c.execute(sql, a).fetchall()
    return r, round(time.time() - t, 1)


def p(label, sql, *a):
    r, s = q(sql, *a)
    print(f"## {label} ({s} s)")
    for row in r[:40]:
        print("  ", row)


p("run: dnevi po omrežju", """
  SELECT t.network, MIN(r.service_date), MAX(r.service_date),
         COUNT(DISTINCT r.service_date), COUNT(DISTINCT r.trip_id || r.service_date), COUNT(*)
  FROM run r JOIN trip t USING(trip_id) GROUP BY t.network""")
p("run: vožnje po prevozniku (zadnjih 14 dni)", """
  SELECT t.network, t.agency, COUNT(DISTINCT r.trip_id || r.service_date) v, COUNT(*)
  FROM run r JOIN trip t USING(trip_id)
  WHERE r.service_date >= date('now','-14 days') GROUP BY 1,2 ORDER BY v DESC""")
p("načrtovane vožnje po prevozniku (en delavnik, 2026-10-28)", """
  SELECT t.network, t.agency, COUNT(*) FROM trip t JOIN service_day d USING(service_id)
  WHERE d.date = '2026-10-28' GROUP BY 1,2 ORDER BY 3 DESC""")
p("napoved: obseg", """
  SELECT network, MIN(service_date), MAX(service_date), COUNT(*),
         SUM(actual_s IS NOT NULL), SUM(operator_s IS NOT NULL), SUM(ours_own_s IS NOT NULL)
  FROM napoved GROUP BY network""")
p("napoved: horizonti", """
  SELECT network, horizon_s/300*5 hmin, COUNT(*) FROM napoved WHERE actual_s IS NOT NULL
  GROUP BY 1,2 ORDER BY 1,2""")
p("sz_zamuda", "SELECT MIN(service_date), MAX(service_date), COUNT(*) FROM sz_zamuda")
p("lpp_zamuda", "SELECT MIN(service_date), MAX(service_date), COUNT(*) FROM lpp_zamuda")
p("delay_report", "SELECT MIN(service_date), MAX(service_date), COUNT(*), COUNT(DISTINCT event) FROM delay_report")
p("delay_report: dogodki", "SELECT event, COUNT(*) FROM delay_report GROUP BY 1 ORDER BY 2 DESC")
p("deljenje_prehod po omrežju", """
  SELECT t.network, COUNT(*), COUNT(DISTINCT d.deljenje), MIN(d.service_date), MAX(d.service_date),
         SUM(d.odhod_ts IS NOT NULL)
  FROM deljenje_prehod d JOIN trip t USING(trip_id) GROUP BY 1""")
p("gps_prehod po omrežju", """
  SELECT t.network, COUNT(*), MIN(g.service_date), MAX(g.service_date)
  FROM gps_prehod g JOIN trip t USING(trip_id) GROUP BY 1""")
p("vehicle_now: vozila z id po prevozniku", """
  SELECT t.agency, COUNT(*), COUNT(vehicle_id), COUNT(plate) FROM vehicle_now v JOIN trip t USING(trip_id)
  GROUP BY 1 ORDER BY 2 DESC""")
p("lega po prevozniku (zadnji dan)", """
  SELECT t.agency, COUNT(*), COUNT(DISTINCT l.vozilo) FROM lega l JOIN trip t USING(trip_id)
  WHERE l.service_date = date('now','-1 day') GROUP BY 1 ORDER BY 2 DESC""")
p("alert po vrsti", "SELECT kind, effect, COUNT(*), MIN(first_seen), MAX(last_seen) FROM alert GROUP BY 1,2 ORDER BY 3 DESC")
p("peron", "SELECT MIN(datum), MAX(datum), COUNT(*), COUNT(DISTINCT postaja) FROM peron")
p("zasedenost", "SELECT MIN(datum), MAX(datum), COUNT(*), SUM(skrito) FROM zasedenost")
p("weather", "SELECT MIN(hour_ts), MAX(hour_ts), COUNT(*), COUNT(DISTINCT cell) FROM weather")
p("povzetek", "SELECT kind, network, days, computed_at, length(payload) FROM povzetek ORDER BY kind")
p("odklon", "SELECT vrsta, COUNT(*), MIN(service_date) FROM odklon GROUP BY 1")
p("ziva_voznja", "SELECT nacin, COUNT(*), MIN(service_date) FROM ziva_voznja GROUP BY 1")

if PROMET:
    pc = sqlite3.connect(f"file:{PROMET}?mode=ro", uri=True)
    for (t,) in pc.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        cols = [r[1] for r in pc.execute(f"PRAGMA table_info({t})")]
        n = pc.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"## promet.{t} {n} {cols}")
        for row in pc.execute(f"SELECT * FROM {t} LIMIT 3"):
            print("  ", row)
