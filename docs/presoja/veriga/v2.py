import sqlite3
c = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
c.row_factory = sqlite3.Row
q = lambda s, *a: c.execute(s, a).fetchall()
print("trips z blokom po dnevu (avtobus):")
for r in q("""SELECT sd.date, COUNT(*) n, SUM(t.block_id IS NOT NULL) zb FROM trip t JOIN service_day sd ON sd.service_id=t.service_id
 WHERE sd.date BETWEEN '2026-10-17' AND '2026-10-31' AND t.network='avtobus' GROUP BY sd.date"""):
    print(" ", r["date"], r["n"], r["zb"])
for d in ("2026-10-30", "2026-10-31"):
    print("LPP mestni linije z blokom", d, [tuple(r) for r in q("""SELECT t.train_no, COUNT(*), SUM(t.block_id IS NOT NULL) FROM trip t JOIN service_day sd ON sd.service_id=t.service_id AND sd.date=?
     WHERE t.agency='lpp' GROUP BY t.train_no HAVING SUM(t.block_id IS NOT NULL)>0 ORDER BY 3 DESC""", d)])
print("LPP 25 30.10: z blokom", [tuple(r) for r in q("""SELECT COUNT(*), SUM(t.block_id IS NOT NULL), COUNT(DISTINCT t.block_id) FROM trip t JOIN service_day sd ON sd.service_id=t.service_id AND sd.date='2026-10-30' WHERE t.agency='lpp' AND t.train_no='25'""")])
print("vir x agencija (straza 30.10):")
for r in q("""SELECT o.vir, t.agency, COUNT(DISTINCT o.trip_id) tr, COUNT(DISTINCT o.vozilo) voz FROM straza_opazeno o JOIN trip t ON t.trip_id=o.trip_id WHERE o.dan='2026-10-30' GROUP BY o.vir, t.agency"""):
    print(" ", tuple(r))
print("vzorec voznj LPP 25 bloka:")
b = q("""SELECT t.block_id FROM trip t JOIN service_day sd ON sd.service_id=t.service_id AND sd.date='2026-10-30' WHERE t.agency='lpp' AND t.train_no='25' AND t.block_id IS NOT NULL LIMIT 1""")
if b:
    for r in q("""SELECT t.train_no, t.headsign, t.start_s/3600.0 h0, t.end_s/3600.0 h1, substr(t.trip_id,1,12) FROM trip t JOIN service_day sd ON sd.service_id=t.service_id AND sd.date='2026-10-30' WHERE t.block_id=? ORDER BY t.start_s""", b[0][0]):
        print("  ", tuple(r))
