"""Odseki, kjer vlaki redno izgubijo čas: prirast zamude od odhoda z X do prihoda na Y."""
import sqlite3, statistics as st
from collections import defaultdict
c = sqlite3.connect("file:/var/tmp/kajros-stat.sqlite?mode=ro", uri=True)
rows = c.execute("""
  SELECT r.trip_id, r.service_date, r.stop_seq, r.delay_arr, r.delay_dep, st.name
  FROM run r JOIN trip t USING(trip_id)
  JOIN sched s ON s.trip_id = r.trip_id AND s.stop_seq = r.stop_seq JOIN station st ON st.stop_id = s.stop_id
  WHERE t.network = 'zeleznica' AND t.mode != 'bus' AND r.service_date BETWEEN '2026-10-11' AND '2026-10-28'
  ORDER BY r.trip_id, r.service_date, r.stop_seq""").fetchall()
prirast = defaultdict(list); prej = None
for trip, d, seq, za, zd, ime in rows:
    if prej and prej[0] == trip and prej[1] == d and prej[2] == seq - 1:
        z_od = prej[3]; z_do = za if za is not None else zd
        if z_od is not None and z_do is not None and abs(z_do - z_od) < 3600:
            prirast[(prej[4], ime)].append((z_do - z_od) / 60)
    prej = (trip, d, seq, zd if zd is not None else za, ime)
vrstice = []
for (a, b), v in prirast.items():
    if len(v) >= 100:
        vrstice.append((st.mean(v), st.median(v), 100 * sum(1 for x in v if x >= 2) / len(v), 100 * sum(1 for x in v if x <= -1) / len(v), len(v), a, b))
vrstice.sort(reverse=True)
print("povprečje | mediana | % ≥ 2 min izgube | % ≥ 1 min pridobi | n | odsek")
for r in vrstice[:15]: print(f"{r[0]:+.2f} | {r[1]:+.1f} | {r[2]:.0f} | {r[3]:.0f} | {r[4]} | {r[5]} → {r[6]}")
print("... kjer vlak čas pridobi (rezerva v voznem redu):")
for r in vrstice[-8:]: print(f"{r[0]:+.2f} | {r[1]:+.1f} | {r[2]:.0f} | {r[3]:.0f} | {r[4]} | {r[5]} → {r[6]}")
print("odsekov z n >= 100:", len(vrstice))
