import sqlite3, time
c = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
c.row_factory = sqlite3.Row
def q(s, *a):
    t=time.time(); r=c.execute(s, a).fetchall(); return r
print("block po agenciji, vožnje 30.10:")
for r in q("""SELECT t.agency, COUNT(*) n, SUM(t.block_id IS NOT NULL) zb, COUNT(DISTINCT t.block_id) bl
 FROM trip t JOIN service_day sd ON sd.service_id=t.service_id AND sd.date='2026-10-30'
 WHERE t.network='avtobus' GROUP BY t.agency"""):
    print(dict(r))
print("straza_opazeno:")
for r in q("SELECT dan, vir, COUNT(*) n, COUNT(DISTINCT vozilo) voz, COUNT(DISTINCT trip_id) tr FROM straza_opazeno GROUP BY dan, vir"):
    print(dict(r))
print("lega:", [dict(r) for r in q("SELECT MIN(service_date) a, MAX(service_date) b, COUNT(*) n, SUM(vozilo IS NOT NULL) zv FROM lega")])
print("gps_prehod po agenciji:")
for r in q("""SELECT t.agency, MIN(g.service_date) a, MAX(g.service_date) b, COUNT(*) n, COUNT(DISTINCT g.trip_id||g.service_date) tr
 FROM gps_prehod g JOIN trip t ON t.trip_id=g.trip_id GROUP BY t.agency"""):
    print(dict(r))
print("lpp_zamuda:", [dict(r) for r in q("SELECT MIN(service_date) a, MAX(service_date) b, COUNT(*) n, SUM(stop_seq=1) s1 FROM lpp_zamuda")])
print("vehicle_now:", [dict(r) for r in q("SELECT COUNT(*) n, MIN(seen_ts) a, MAX(seen_ts) b, SUM(vehicle_id IS NOT NULL) zv FROM vehicle_now")])
