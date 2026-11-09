"""Izvoz železniškega dela produkcijske baze v majhno kopijo (samo branje vira).

Vsak INSERT ... SELECT je svoja kratka transakcija, da bralec ne drži WAL-a.
"""
import sqlite3, sys, time, os

VIR = "file:/var/lib/kajros/kajros.sqlite?mode=ro"
CILJ = sys.argv[1]
if os.path.exists(CILJ):
    os.remove(CILJ)
c = sqlite3.connect(CILJ, isolation_level=None)
c.execute("PRAGMA journal_mode=OFF")
c.execute("PRAGMA synchronous=OFF")
c.execute(f"ATTACH '{VIR}' AS p")
c.execute("CREATE TEMP TABLE vl AS SELECT trip_id FROM p.trip WHERE network='zeleznica'")
c.execute("CREATE UNIQUE INDEX temp.vl_i ON vl(trip_id)")
V = "trip_id IN (SELECT trip_id FROM temp.vl)"
TABELE = {
    "trip": V, "sched": V, "run": V, "obs": V,
    "station": "1", "meta": "1", "prednik": "1", "zamenjava": "1",
    "service_day": "service_id IN (SELECT service_id FROM p.trip WHERE network='zeleznica')",
    "napoved": "network='zeleznica'",
    "sz_zamuda": "1",
}
for t, kje in TABELE.items():
    ddl = c.execute("SELECT sql FROM p.sqlite_master WHERE type='table' AND name=?", (t,)).fetchone()
    if not ddl:
        print(t, "ni tabele"); continue
    c.execute(ddl[0])
    t0 = time.time()
    try:
        n = c.execute(f"INSERT INTO main.{t} SELECT * FROM p.{t} WHERE {kje}").rowcount
    except sqlite3.OperationalError as e:
        print(t, "NAPAKA", e); continue
    print(t, n, round(time.time() - t0, 1), "s", flush=True)
for (sql,) in c.execute("SELECT sql FROM p.sqlite_master WHERE type='index' AND sql IS NOT NULL "
                        "AND tbl_name IN (%s)" % ",".join("?" * len(TABELE)), list(TABELE)).fetchall():
    try:
        c.execute(sql)
    except sqlite3.OperationalError as e:
        print("indeks", e)
print("velikost MB", os.path.getsize(CILJ) // 2**20)
