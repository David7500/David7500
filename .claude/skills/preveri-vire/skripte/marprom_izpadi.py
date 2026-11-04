"""Marprom: izpadi vožnja -> brez -> vožnja iz dosjeja (`stanje`), samo branje.

Izpise izpade na isto in na drugo vožnjo po razlogu, druge razvrsti: naslednje
postajališče ni na stari vožnji (prava menjava), pred koncem stare, sredi stare z
novo po njenem koncu, prekrivanje, dolg izpad. Na arwenu:

  scp .claude/skills/preveri-vire/skripte/marprom_izpadi.py david@192.168.1.46:/tmp/ && \
  ssh david@192.168.1.46 '/opt/kajros/.venv/bin/python -I /tmp/marprom_izpadi.py "2026-11-04 21:50" "2026-11-07 12:00"'
"""
import sqlite3, json, statistics, collections, sys
from datetime import datetime
from zoneinfo import ZoneInfo
TZ = ZoneInfo("Europe/Ljubljana")
OD = int(datetime.fromisoformat(sys.argv[1]).replace(tzinfo=TZ).timestamp())
DO = int(datetime.fromisoformat(sys.argv[2]).replace(tzinfo=TZ).timestamp())
d = sqlite3.connect("file:/var/lib/kajros/dosje.sqlite?mode=ro", uri=True, timeout=30)
k = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True, timeout=30)
polnoc = lambda dan: int(datetime.fromisoformat(dan + " 12:00").replace(tzinfo=TZ).timestamp()) - 43200
trip = {r[0]: r[1:] for r in k.execute(
    "SELECT trip_id, route_id, shape_id, train_no, start_s, end_s FROM trip WHERE agency='marprom'")}
stops = collections.defaultdict(list)
for t, q, sid, a, de in k.execute(
        "SELECT s.trip_id, s.stop_seq, s.stop_id, s.arr_s, s.dep_s FROM sched s JOIN trip t USING(trip_id) "
        "WHERE t.agency='marprom' ORDER BY 1, 2"):
    stops[t].append((q, sid, a, de))
po_vozilu = collections.defaultdict(list)
for r in d.execute("SELECT vozilo, ts, trip_id, dan, razlogi, sprotno FROM stanje "
                   "WHERE vir='marprom' AND ts BETWEEN ? AND ? ORDER BY vozilo, ts", (OD, DO)):
    po_vozilu[r[0]].append(r[1:])
izpadi = []
for voz, vr in po_vozilu.items():
    i = 0
    while i < len(vr) - 1:
        if vr[i][1] and not vr[i + 1][1]:
            zacetek = vr[i + 1]
            j = i + 1
            while j < len(vr) and not vr[j][1]:
                j += 1
            if j == len(vr):
                break
            razlogi = [x for x in vr[i + 1][3].split(",") if x not in ("brez_voznje", "ni_ziva", "miruje", "stara_lega", "ura_naprej")]
            s = json.loads(zacetek[4] or "{}")
            izpadi.append(dict(vozilo=voz, t0=zacetek[0], t1=vr[j][0], a=vr[i][1], dan_a=vr[i][2], b=vr[j][1], dan_b=vr[j][2],
                               razlog=razlogi[0] if razlogi else "-", nasl=str(s.get("NextStopPointId") or ""),
                               razlogi=vr[i+1][3]))
            i = j
        else:
            i += 1
print("izpadov", len(izpadi))
def mins(x): return round(x / 60, 1)
ista = [x for x in izpadi if (x["a"], x["dan_a"]) == (x["b"], x["dan_b"])]
druga = [x for x in izpadi if (x["a"], x["dan_a"]) != (x["b"], x["dan_b"])]
def pov(ime, xs):
    tr = sorted(x["t1"] - x["t0"] for x in xs)
    if not tr: print(ime, 0); return
    print(ime, "n", len(xs), "med", tr[len(tr)//2], "p90", tr[int(len(tr)*.9)], "skupaj min", mins(sum(tr)),
          dict(collections.Counter(x["razlog"] for x in xs).most_common()))
pov("ista", ista); pov("druga", druga)
pov("ista<30min", [x for x in ista if x["t1"]-x["t0"] < 1800])
pov("druga<30min", [x for x in druga if x["t1"]-x["t0"] < 1800])
# razvrsti druge
raz = collections.Counter(); prim = collections.defaultdict(list)
for x in druga:
    a, b = x["a"], x["b"]
    if a not in trip or b not in trip:
        raz["neznana"] += 1; continue
    ra, sa, noa, sta, ena = trip[a]; rb, sb, nob, stb, enb = trip[b]
    konec_a = polnoc(x["dan_a"]) + ena; zacetek_b = polnoc(x["dan_b"]) + stb
    na_a = [q for q, sid, *_ in stops[a] if sid == "mp-" + x["nasl"]]
    zadnji = stops[a][-1][0]
    do_konca = (konec_a - x["t0"]) / 60
    if x["t1"] - x["t0"] >= 1800:
        vrsta = "dolg_izpad>=30min"
    elif not na_a:
        vrsta = "naslednje_ni_na_A"
    elif max(na_a) >= zadnji and do_konca < 10:
        vrsta = "pred_koncem_A"
    elif zacetek_b >= konec_a - 300:
        vrsta = "A_sredi_B_kasneje"     # naslednje je na A sredi, B šele po koncu A
    else:
        vrsta = "A_sredi_B_prekriva"    # A in B hkrati: ena je narobe
    raz[(vrsta, x["razlog"])] += 1
    prim[vrsta].append(x)
for k_, v in sorted(raz.items(), key=lambda kv: str(kv[0])):
    print(" ", k_, v)
for vrsta, xs in prim.items():
    tr = sorted(x["t1"] - x["t0"] for x in xs)
    print(vrsta, "n", len(xs), "med", tr[len(tr)//2], "p90", tr[int(len(tr)*.9)], "skupaj min", mins(sum(tr)))
