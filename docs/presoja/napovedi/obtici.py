"""Meja obtiči po luknji v legah: koliko voženj NAP na dan (koledar 3. 11. 2026).

Za vsako vožnjo prevoznikov NAP s prehodi je L zadnji prehod. Če L ni cilj,
pogledamo lege istega vozila po L: ali pride v 100 m postanka, ki je več kot
NAPREJ (8) postankov za L (prehod ga ne išče več, `prehod.py`), in ali je bila
pred tem luknja v legah > RAZMIK_S (120 s). Samo branje, na arwenu:

  scp docs/presoja/napovedi/obtici.py david@192.168.1.46:/tmp/ && \
  ssh david@192.168.1.46 "/opt/kajros/.venv/bin/python -I /tmp/obtici.py 2026-11-02"

Po vožnjah v `/tmp/obtici-DAN.csv`. Vožnje brez `sched` (nagrobniki po
uvozu) se ne dajo oceniti: za dneve pred zadnjo menjavo zipa je števec nižji.
"""
import collections
import csv
import math
import sqlite3
import sys
import time

DAN = sys.argv[1]
NAPREJ, POLMER_M, RAZMIK_S = 8, 100.0, 120
R = 6371008.8


def razdalja(a, b, c, d):
    x = math.radians(d - b) * math.cos(math.radians((a + c) / 2))
    return R * math.hypot(x, math.radians(c - a))


conn = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True, timeout=30)
t0 = time.time()
voznje = conn.execute("""
    SELECT g.trip_id, t.agency, t.train_no, MAX(g.stop_seq), COUNT(*)
    FROM gps_prehod g JOIN trip t USING (trip_id)
    WHERE g.service_date = ? AND t.agency IN ('1119', '1121', '1123')
    GROUP BY g.trip_id""", (DAN,)).fetchall()
izid = collections.Counter()
po_prev = collections.Counter()
vrstice = []
for tid, ag, st, L, n_preh in voznje:
    post = conn.execute("""SELECT s.stop_seq, st.lat, st.lon FROM sched s JOIN station st USING (stop_id)
                           WHERE s.trip_id = ? ORDER BY s.stop_seq""", (tid,)).fetchall()
    if not post:
        izid["brez sched"] += 1
        continue
    idx = {seq: i for i, (seq, _, _) in enumerate(post)}
    iL, zadnji = idx.get(L, -1), len(post) - 1
    if iL == zadnji:
        izid["do cilja"] += 1
        continue
    (TL,) = conn.execute("SELECT prehod_ts FROM gps_prehod WHERE service_date = ? AND trip_id = ? AND stop_seq = ?",
                         (DAN, tid, L)).fetchone()
    v = conn.execute("""SELECT vozilo FROM lega WHERE service_date = ? AND trip_id = ? AND ts BETWEEN ? AND ?
                        ORDER BY ABS(ts - ?) LIMIT 1""", (DAN, tid, TL - 300, TL + 300, TL)).fetchone()
    vozilo = v[0] if v else None
    lege = [(ts, la, lo) for ts, la, lo, vz in conn.execute(
        "SELECT ts, lat, lon, vozilo FROM lega WHERE service_date = ? AND trip_id = ? AND ts >= ? ORDER BY ts",
        (DAN, tid, TL)) if vozilo is None or vz == vozilo]
    daleč = v_oknu = None
    prej = None
    najvecja = (0, None, None)          # luknja (s), indeks pred, indeks po
    for ts, la, lo in lege:
        d = [(razdalja(la, lo, p[1], p[2]), i) for i, p in enumerate(post) if i > iL]
        dmin, imin = min(d) if d else (1e9, None)
        if prej is not None and ts - prej[0] > najvecja[0] and daleč is None:
            najvecja = (ts - prej[0], prej[1], imin)
        prej = (ts, imin)
        if dmin <= POLMER_M:
            if imin > iL + NAPREJ:
                daleč = (ts, imin)
                break
            if v_oknu is None:
                v_oknu = (ts, imin)
    if daleč:
        vrsta = "obtiči po luknji" if najvecja[0] > RAZMIK_S else "obtiči brez luknje"
    elif not lege or lege[-1][0] - TL < 300:
        vrsta = "lega utihne"
    elif v_oknu:
        vrsta = "v oknu brez prehoda"
    else:
        vrsta = "ni dlje"
    izid[vrsta] += 1
    po_prev[(ag, vrsta)] += 1
    konec = lege[-1][0] if lege else TL
    vrstice.append((tid, ag, st, L, iL + 1, len(post), vrsta, najvecja[0], najvecja[1], najvecja[2],
                    daleč[1] + 1 if daleč else "", zadnji - iL, round((konec - TL) / 60), n_preh,
                    time.strftime("%H:%M:%S", time.localtime(TL))))
with open(f"/tmp/obtici-{DAN}.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["trip", "prevoznik", "st", "L", "iL1", "postankov", "vrsta", "luknja_s", "pred_i", "po_i",
                "dalec_i1", "brez_meritve", "min_po_L", "prehodov", "TL"])
    w.writerows(vrstice)
print(DAN, "voženj s prehodi", len(voznje), f"{time.time() - t0:.0f} s")
for k, n in izid.most_common():
    print(f"  {k}: {n}")
for (ag, k), n in sorted(po_prev.items()):
    print(f"  {ag} {k}: {n}")
for r in sorted((r for r in vrstice if r[6].startswith("obtiči")), key=lambda r: -r[11])[:25]:
    print("  ", r)
