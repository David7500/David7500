import sqlite3, statistics as st
from datetime import datetime
c = sqlite3.connect("file:/var/tmp/kajros-stat.sqlite?mode=ro", uri=True)
PARI = [("Ljubljana", "Kranj", "zeleznica"), ("Ljubljana AP", "Kranj AP", "avtobus"),
        ("Kranj", "Ljubljana", "zeleznica"), ("Kranj AP", "Ljubljana AP", "avtobus"),
        ("Ljubljana", "Maribor", "zeleznica"), ("Ljubljana AP", "Maribor AP", "avtobus"),
        ("Ljubljana", "Celje", "zeleznica"), ("Ljubljana AP", "Celje AP", "avtobus")]
for od, do, net in PARI:
    rows = c.execute("""
      SELECT r2.service_date, s1.dep_s, COALESCE(r1.delay_dep, r1.delay_arr), s2.arr_s, COALESCE(r2.delay_arr, r2.delay_dep), t.agency
      FROM trip t
      JOIN sched s1 ON s1.trip_id = t.trip_id JOIN station a ON a.stop_id = s1.stop_id AND a.name = ?
      JOIN sched s2 ON s2.trip_id = t.trip_id AND s2.stop_seq > s1.stop_seq JOIN station b ON b.stop_id = s2.stop_id AND b.name = ?
      LEFT JOIN run r1 ON r1.trip_id = t.trip_id AND r1.stop_seq = s1.stop_seq
      JOIN run r2 ON r2.trip_id = t.trip_id AND r2.stop_seq = s2.stop_seq AND (r1.service_date IS NULL OR r2.service_date = r1.service_date)
      WHERE t.network = ? AND (t.network = 'avtobus' OR t.mode != 'bus') AND r2.service_date BETWEEN '2026-10-11' AND '2026-10-28'""", (od, do, net)).fetchall()
    sched, dej, z, ag = [], [], [], {}
    for d, dep, z1, arr, z2, a in rows:
        if datetime.strptime(d, "%Y-%m-%d").weekday() >= 5 or z2 is None or abs(z2) > 10800: continue
        sched.append((arr - dep) / 60); z.append(z2 / 60); ag[a] = ag.get(a, 0) + 1
        if z1 is not None: dej.append(((arr + z2) - (dep + z1)) / 60)
    if not sched: print(od, do, "nič"); continue
    v5 = 100 * sum(1 for x in z if int(x + 0.5) <= 5) / len(z)
    print(f"{od} → {do} ({net}, {ag}): voženj {len(sched)}, vozni red mediana {st.median(sched):.0f} min,"
          f" dejansko {st.median(dej) if dej else float('nan'):.0f} (n {len(dej)}), zamuda na cilju mediana {st.median(z):.1f}, v 5 min {v5:.0f} %")
