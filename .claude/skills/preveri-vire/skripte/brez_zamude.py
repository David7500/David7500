"""Vozila z lego na vožnji, ki teče (15 min mimo tretjega postanka), brez vrstice
v run -- isto kot collector.lega_brez_zamude, z imeni in sledjo (obs, gps_prehod,
lega). Nato poglej straza_opazeno: kaj je o vozilu rekel NAP in kaj derp.si.

Zagon (samo branje): scp na arwen, nato
  ssh david@192.168.1.46 '/opt/kajros/.venv/bin/python /tmp/brez_zamude.py ARGUMENTI'
"""
import sqlite3, time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
TZ = ZoneInfo("Europe/Ljubljana")
conn = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True); conn.row_factory = sqlite3.Row
zdaj = datetime.now(TZ); danes = zdaj.date()
pol = int(datetime(danes.year, danes.month, danes.day, 12, tzinfo=TZ).timestamp()) - 43200
now_s = int(zdaj.timestamp()) - pol
for r in conn.execute(
    "SELECT t.agency, t.train_no, t.headsign, v.trip_id, v.vehicle_id, v.lat, v.lon, v.seen_ts, v.service_date, t.start_s, t.end_s, "
    " EXISTS (SELECT 1 FROM run r WHERE r.trip_id = v.trip_id AND r.service_date = COALESCE(v.service_date, ?)) AS ima "
    "FROM vehicle_now v JOIN trip t USING (trip_id) "
    "WHERE v.seen_ts >= ? AND t.start_s IS NOT NULL "
    "  AND CASE COALESCE(v.service_date, ?) WHEN ? THEN ? WHEN ? THEN ? + 86400 END "
    "      BETWEEN (SELECT COALESCE(s.dep_s, s.arr_s) FROM sched s WHERE s.trip_id = t.trip_id ORDER BY s.stop_seq LIMIT 1 OFFSET 2) + 900 AND t.end_s",
    (danes.isoformat(), int(time.time()) - 300, danes.isoformat(), danes.isoformat(), now_s, (danes - timedelta(days=1)).isoformat(), now_s)):
    if not r["ima"]:
        print(dict(r), "start", f"{r['start_s']//3600:02d}:{r['start_s']%3600//60:02d}", "konec", f"{r['end_s']//3600:02d}:{r['end_s']%3600//60:02d}")
        for s in conn.execute("SELECT sc.stop_seq, st.name, sc.dep_s FROM sched sc JOIN station st USING (stop_id) WHERE trip_id=? ORDER BY stop_seq", (r["trip_id"],)).fetchall()[:6]:
            print("   ", s[0], s[1], f"{s[2]//3600:02d}:{s[2]%3600//60:02d}" if s[2] else None)
        print("   obs:", conn.execute("SELECT COUNT(*) FROM obs WHERE trip_id=?", (r["trip_id"],)).fetchone()[0],
              "gps_prehod:", conn.execute("SELECT COUNT(*) FROM gps_prehod WHERE trip_id=?", (r["trip_id"],)).fetchone()[0],
              "lega:", conn.execute("SELECT COUNT(*), MIN(ts), MAX(ts) FROM lega WHERE trip_id=? AND service_date=?", (r["trip_id"], danes.isoformat())).fetchone())
