"""SŽ: ali zemljevid pokaže vlak kot odpeljan, preden res odpelje?

Za vsako (vožnja, dan, postanek X) vzame dnevnik `obs` z zemljevida SŽ
(od 11. 10. 2026 vodi): prva in zadnja odhodna zamuda za X. Če zadnja
preseže prvo, je SŽ odhod z X pozneje popravil -- vmes je kazal vlak kot
odpeljan ob uri, ki ni držala. Resnica, kjer je: prehod potnika (deljenje).
"""
import sqlite3, sys, statistics as st
from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

DB = sys.argv[1]
OD = sys.argv[2] if len(sys.argv) > 2 else "2026-10-11"
c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
TZ = ZoneInfo("Europe/Ljubljana")


def polnoc(d):
    # GTFS: ura 12:00 minus 12 h, kot stats.polnoc()
    y, m, dd = map(int, d.split("-"))
    poldne = datetime(y, m, dd, 12, tzinfo=TZ)
    return int(poldne.timestamp()) - 12 * 3600


print("obs obseg:", c.execute("""SELECT MIN(service_date), MAX(service_date), COUNT(*)
  FROM obs o JOIN trip t USING(trip_id) WHERE t.network='zeleznica'""").fetchone())

rows = c.execute("""
  SELECT o.trip_id, o.service_date, o.stop_seq, o.observed_at, COALESCE(o.delay_dep, o.delay_arr),
         s.dep_s, t.first_seq, t.last_seq, t.mode, t.train_no
  FROM obs o JOIN trip t USING(trip_id)
  JOIN sched s ON s.trip_id = o.trip_id AND s.stop_seq = o.stop_seq
  WHERE t.network = 'zeleznica' AND o.service_date >= ?
  ORDER BY o.trip_id, o.service_date, o.stop_seq, o.observed_at""", (OD,)).fetchall()
print("vrstic obs:", len(rows))

serije = defaultdict(list)
meta = {}
for trip, d, seq, ts, dl, dep_s, fs, ls, mode, no in rows:
    if dl is None:
        continue
    serije[(trip, d, seq)].append((ts, dl))
    meta[(trip, d, seq)] = (dep_s, fs, ls, mode, no)

inc = []
dolg = []
izhodisce = []
primeri = []
for k, s in serije.items():
    dep_s, fs, ls, mode, no = meta[k]
    if mode == "bus" or k[2] == ls:
        continue
    d0, d1 = s[0][1], s[-1][1]
    up = d1 - d0
    inc.append(up)
    if up >= 120:
        trajanje = s[-1][0] - s[0][0]
        dolg.append((up, trajanje))
        if len(primeri) < 8 and up >= 300:
            primeri.append((no, k[1], k[2], d0, d1, len(s), trajanje))
    if k[2] == fs:
        izhodisce.append((d0, d1))

n = len(inc)
print(f"postankov s serijo: {n}")
for meja in (60, 120, 300, 600):
    m = sum(1 for x in inc if x >= meja)
    print(f"  zadnja - prva >= {meja//60} min: {m} ({100*m/max(n,1):.1f} %)")
print("  zmanjšanje >= 2 min:", sum(1 for x in inc if x <= -120))
if dolg:
    razmerje = [u / t for u, t in dolg if t > 0]
    print(f"popravki >= 2 min: {len(dolg)}; mediana popravka {st.median(u for u,_ in dolg)/60:.1f} min,"
          f" mediana trajanja serije {st.median(t for _,t in dolg)/60:.1f} min,"
          f" mediana popravek/trajanje {st.median(razmerje):.2f}")
print("primeri:", primeri)
ni = len(izhodisce)
z0 = sum(1 for a, b in izhodisce if a <= 30 and b >= 120)
print(f"izhodišče: {ni} odhodov; prva zamuda <= 0,5 min, zadnja >= 2 min: {z0} ({100*z0/max(ni,1):.1f} %)")

# Resnica: prehodi potnikov (deljenje) proti prvi trditvi SŽ.
pr = c.execute("""
  SELECT d.trip_id, d.service_date, d.stop_seq, d.odhod_ts, s.dep_s, t.train_no
  FROM deljenje_prehod d JOIN trip t USING(trip_id)
  JOIN sched s ON s.trip_id = d.trip_id AND s.stop_seq = d.stop_seq
  WHERE t.network = 'zeleznica' AND d.odhod_ts IS NOT NULL""").fetchall()
print(f"prehodi potnikov z odhodom (železnica): {len(pr)}")
for trip, d, seq, odhod, dep_s, no in pr:
    s = serije.get((trip, d, seq))
    sched_ts = polnoc(d) + dep_s
    if not s:
        print(f"  {no} {d} seq {seq}: res odpeljal {(odhod-sched_ts)/60:+.1f} min, serije SŽ ni")
        continue
    t_first, d0 = s[0]
    print(f"  {no} {d} seq {seq}: res {(odhod-sched_ts)/60:+.1f} min; SŽ prvič {(t_first-sched_ts)/60:+.1f} min"
          f" z zamudo {d0/60:+.1f}, zadnja {s[-1][1]/60:+.1f}; SŽ pokazal odhod {(t_first-odhod)/60:+.1f} min glede na res")
