"""„Biti tam do“: kako zanesljiv je PRVI predlog in kaj stane.

Prvi predlog je odgovor na „kdaj moram od doma“ -- stran ga napiše kot
„Odidi najpozneje ob …“. Merilo:

* vozni red dneva DAN (privzeto teden nazaj), iskanje vnaprej (`now_s=None`),
  zgodovina tveganja je zato vsa PRED tem dnem;
* izid na naslednjih sedmih dneh, ista vožnja čez dneve (`db.voznja_sql`):
  prvi predlog je bil pravočasen, kadar so držali vsi prestopi in je zadnja
  vožnja pripeljala v rezervi do roka. Resnica je tu napisana posebej, ne
  skozi `pot.zamude_po_dnevih`, da je med različicami iskanja ista;
* koliko prej od roka predlog odide (cena zanesljivosti), kako pogosto je
  prva hoja vso pot in koliko traja iskanje.

Pari: pol mestnih (2-4 km), pol daljših (6-25 km), rok med 7. in 20. uro.

Zagon: ./venv/bin/python scripts/preizkusi_rok.py [vprašanj] [dan]
"""
import math
import random
import statistics
import sys
import time
from collections import defaultdict
from datetime import date, timedelta

sys.path.insert(0, ".")
from kajros import config, db, geo, journey, pot, stats       # noqa: E402

config.OSRM_URL = ""

N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
DAN = sys.argv[2] if len(sys.argv) > 2 else (date.today() - timedelta(days=7)).isoformat()
KONEC = (date.fromisoformat(DAN) + timedelta(days=7)).isoformat()
random.seed(11)

conn = db.connect()
by_trip, at_stop = journey._timetable_for_day(conn, DAN, None)
imena = pot._imena(conn)
promet = {sid: len(v) for sid, v in at_stop.items() if sid in imena}
postaje = [s for s, n in promet.items() if n >= 20]
teze = [promet[s] for s in postaje]
print(f"vozni red {DAN}: {len(by_trip)} voženj, {len(postaje)} postajališč; izid {DAN}..{KONEC}")


def kraj(sid):
    """Točka do 250 m od postajališča: vrata, ne peron."""
    _, lat, lon = imena[sid]
    r = random.uniform(30, 250)
    a = random.uniform(0, 2 * math.pi)
    return (lat + r * math.cos(a) / 111_320,
            lon + r * math.sin(a) / (111_320 * math.cos(math.radians(lat))))


def par(meje):
    while True:
        a, b = random.choices(postaje, teze, k=2)
        d = geo.haversine(imena[a][1], imena[a][2], imena[b][1], imena[b][2])
        if meje[0] <= d <= meje[1]:
            return kraj(a), kraj(b)


vprasanja = []           # (skupina, prvi predlog ali None, ms, rok absolutno)
prevladana_hoja = defaultdict(int)
t0 = time.perf_counter()
for i in range(N):
    skupina = "mesto 2-4 km" if i % 2 == 0 else "daleč 6-25 km"
    od, do = par((2_000, 4_000) if i % 2 == 0 else (6_000, 25_000))
    rok = random.randint(7 * 3600, 20 * 3600)
    try:
        izid = pot.isci(conn, od, do, DAN, None, prihod_do_s=rok, now_s=None)
    except Exception as e:                           # merilo, ne strežba
        print("  napaka:", e)
        continue
    prvi = izid["predlogi"][0] if izid["predlogi"] else None
    # Hoja prva, čeprav je na seznamu vožnja brez prestopa, ki odpelje ob isti
    # uri ali pozneje, pripelje prej in hodi manj: to ni odgovor.
    if prvi and not any(n["vrsta"] == "voznja" for n in prvi["noge"]) and any(
            any(n["vrsta"] == "voznja" for n in q["noge"]) and q["prestopov"] == 0
            and q["odhod"] >= prvi["odhod"] and q["prihod"] <= prvi["prihod"]
            and q["hoje_s"] <= prvi["hoje_s"] for q in izid["predlogi"]):
        prevladana_hoja[skupina] += 1
    vprasanja.append((skupina, prvi, izid["trajalo_ms"], stats.polnoc(DAN) + rok))
print(f"{len(vprasanja)} vprašanj ({time.perf_counter() - t0:.0f} s)")


def zamude(pari, prihod):
    """{(trip_id, seq): {dan: zamuda}} na dneh [DAN, KONEC), ista vožnja čez dneve.

    Odhod s prvega postanka ni nikoli negativen (`stats.odhod_z_izhodisca`):
    vozilo tam čaka, ne odpelje prej."""
    zamuda = "COALESCE(r.delay_arr, r.delay_dep)" if prihod else "COALESCE(r.delay_dep, r.delay_arr)"
    out = defaultdict(dict)
    pari = sorted(set(pari))
    for i in range(0, len(pari), 400):
        kos = pari[i:i + 400]
        vals = ",".join(["(?,?)"] * len(kos))
        for r in conn.execute(
                f"WITH want(trip_id, stop_seq) AS (VALUES {vals}) "
                f"SELECT w.trip_id, w.stop_seq, a.first_seq, r.service_date, {zamuda} AS d "
                f"FROM want w CROSS JOIN trip a ON a.trip_id = w.trip_id "
                f"CROSS JOIN trip t ON {db.voznja_sql('t')} = {db.voznja_sql('a')} "
                f"CROSS JOIN run r ON r.trip_id = t.trip_id AND r.stop_seq = w.stop_seq "
                f"WHERE r.service_date >= ? AND r.service_date < ? AND d IS NOT NULL "
                f"  AND ABS(d) <= {stats.MAX_REALNA_ZAMUDA_S}",
                [x for p in kos for x in p] + [DAN, KONEC]):
            d = r["d"] if prihod else stats.odhod_z_izhodisca(r["d"], r["stop_seq"], r["first_seq"])
            out[(r["trip_id"], r["stop_seq"])][r["service_date"]] = d
    return out


def vozi(trip_ids):
    """{trip_id: dnevi [DAN, KONEC), ko je vožnja kjerkoli poročala}."""
    out = defaultdict(set)
    for tid in set(trip_ids):
        for r in conn.execute(
                f"SELECT DISTINCT r.service_date FROM trip a "
                f"CROSS JOIN trip t ON {db.voznja_sql('t')} = {db.voznja_sql('a')} "
                f"CROSS JOIN run r ON r.trip_id = t.trip_id "
                f"WHERE a.trip_id = ? AND r.service_date >= ? AND r.service_date < ?",
                (tid, DAN, KONEC)):
            out[tid].add(r["service_date"])
    return out


voznje_prvih = [[n for n in p["noge"] if n["vrsta"] == "voznja"] if p else []
                for _, p, _, _ in vprasanja]
prihodi = zamude([(n["trip_id"], n["do_seq"]) for vv in voznje_prvih for n in vv], True)
odhodi = zamude([(b["trip_id"], b["od_seq"]) for vv in voznje_prvih for b in vv[1:]], False)
# Vlak na izhodišču ne poroča nikoli; pred voznim redom ne odpelje.
na_izhodiscu = [b["trip_id"] for vv in voznje_prvih for b in vv[1:]
                if b.get("network") == "zeleznica" and by_trip.get(b["trip_id"])
                and by_trip[b["trip_id"]][0][0] == b["od_seq"]]
vozni_dnevi = vozi(na_izhodiscu)

po_skupini = defaultdict(lambda: defaultdict(list))
for (skupina, p, ms, rok), voznje in zip(vprasanja, voznje_prvih):
    s = po_skupini[skupina]
    s["ms"].append(ms)
    if p is None:
        s["brez"].append(1)
        continue
    if not voznje:
        s["hoja"].append(1)
        continue
    z = (p.get("zanesljivost") or {}).get("p")
    s["p"].append(z if z is not None else 1.0)
    s["prej_min"].append((rok - p["odhod"]) / 60)
    zanesljiv = z is None or z >= pot.ZANESLJIVO_P
    s["zanesljiv"].append(zanesljiv)
    zadnja = voznje[-1]
    dnevi = set(prihodi.get((zadnja["trip_id"], zadnja["do_seq"]), {}))
    for a, b in zip(voznje, voznje[1:]):
        zb = odhodi.get((b["trip_id"], b["od_seq"]))
        if zb is None and b["trip_id"] in vozni_dnevi:
            zb = dict.fromkeys(vozni_dnevi[b["trip_id"]], 0)
        dnevi &= set(prihodi.get((a["trip_id"], a["do_seq"]), {})) & set(zb or {})
    rezerva = rok - p["prihod"]
    for d in dnevi:
        ok = prihodi[(zadnja["trip_id"], zadnja["do_seq"])][d] <= rezerva
        for (a, b), t in zip(zip(voznje, voznje[1:]), p.get("prestopi") or ()):
            zb = odhodi.get((b["trip_id"], b["od_seq"])) or dict.fromkeys(vozni_dnevi[b["trip_id"]], 0)
            ok = ok and t["nacrtovano_s"] + zb[d] - prihodi[(a["trip_id"], a["do_seq"])][d] >= 0
        s["izid"].append(ok)
        (s["izid_zanesljiv"] if zanesljiv else s["izid_tvegan"]).append(ok)


def delez(x):
    return f"{sum(x) / len(x) * 100:5.1f} % ({len(x)})" if x else "   — (0)"


for skupina in sorted(po_skupini):
    s = po_skupini[skupina]
    n = len(s["ms"])
    ms = sorted(s["ms"])
    print(f"\n== {skupina}: {n} vprašanj")
    print(f"  prvi je hoja vso pot      {len(s['hoja']):4d}   od tega pred boljšo vožnjo "
          f"{prevladana_hoja[skupina]}   brez predloga {len(s['brez'])}")
    print(f"  prvi z vozilom zanesljiv  {delez(s['zanesljiv'])}")
    if s["p"]:
        print(f"  zanesljivost prvega       mediana {statistics.median(s['p']):.3f}")
        print(f"  odhod pred rokom          mediana {statistics.median(s['prej_min']):.0f} min, "
              f"povprečje {statistics.mean(s['prej_min']):.0f} min")
    print(f"  pravočasen (7 dni potem)  {delez(s['izid'])}")
    print(f"    ko je bil zanesljiv     {delez(s['izid_zanesljiv'])}")
    print(f"    ko je bil tvegan        {delez(s['izid_tvegan'])}")
    print(f"  iskanje                   mediana {ms[n // 2]} ms, p90 {ms[int(n * 0.9)]} ms")
