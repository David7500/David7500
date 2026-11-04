"""Na arwenu, samo branje: zamuda iz lege na dolgih odsekih NAP, ponovitev na `lega`.

Za zaporedna prehoda k -> j (`gps_prehod`, odsek >= 15 min po voznem redu) vzame
lege med njima, na minuto, jih projicira na traso in primerja napoved zamude na j:

  prenos   zamuda na k (to okno kaže zdaj)
  razdalja zdaj minus vozni red, razporejen po razdalji po trasi
  profil   zdaj + običajni ostanek časa od te točke do j: mediana drugih dni istega
           odseka (ime k, ime j, dolžina po trasi na 500 m), koš 5 % odseka; samo
           z vsaj tremi drugimi dnevi. Stara vožnja brez `sched` (nagrobnik) vzame
           traso naslednice z isto šifro in uro odhoda.

Izid po deležu odseka, dolžini, prevozniku; surovo v CSV za nadaljnjo analizo.

  scp ponovitev.py david@192.168.1.46:/tmp/ && ssh david@192.168.1.46 \
    'KAJROS_DATA_DIR=/var/lib/kajros nice -n 19 ionice -c3 \
     /opt/kajros/.venv/bin/python -I /tmp/ponovitev.py 2026-10-26 2026-11-03'
"""
import collections
import csv
import sqlite3
import statistics
import sys
from datetime import date, timedelta

sys.path.insert(0, "/opt/kajros")
from kajros import deljenje  # noqa: E402

OD, DO = date.fromisoformat(sys.argv[1]), date.fromisoformat(sys.argv[2])
DNI = [(OD + timedelta(days=i)).isoformat() for i in range((DO - OD).days + 1)]
NAJMANJ_S = 900
ODMIK_MAX_M = 300
KOS = 0.05
conn = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True, timeout=30)
conn.row_factory = sqlite3.Row


def odsek_prehodov(dan):
    """(trip_id, agency, a, b) za zaporedna prehoda z dolgim odsekom."""
    po = collections.defaultdict(list)
    for r in conn.execute(
            "SELECT g.trip_id, t.agency, g.stop_seq, g.zamuda_s, g.prehod_ts, g.dopolnjen "
            "FROM gps_prehod g JOIN trip t USING (trip_id) "
            "WHERE g.service_date = ? AND t.agency IN ('1119','1121','1123') "
            "ORDER BY g.trip_id, g.stop_seq", (dan,)):
        po[(r["trip_id"], r["agency"])].append(r)
    return po


#: (prevoznik, šifra) -> vožnje z voznim redom: stara vožnja brez `sched` (uvoz
#: 2. 11. je zamenjal ~1 400 voženj brez para v `zamenjava`) vzame traso naslednice.
ZIVE = collections.defaultdict(list)
for r in conn.execute("SELECT t.trip_id, t.agency, t.train_no, t.start_s FROM trip t "
                      "WHERE t.agency IN ('1119','1121','1123') "
                      "AND EXISTS (SELECT 1 FROM sched s WHERE s.trip_id = t.trip_id)"):
    ZIVE[(r["agency"], r["train_no"])].append((r["trip_id"], r["start_s"]))
STARE = {r["trip_id"]: r for r in conn.execute(
    "SELECT t.trip_id, t.agency, t.train_no, t.start_s FROM trip t "
    "WHERE t.agency IN ('1119','1121','1123') "
    "AND NOT EXISTS (SELECT 1 FROM sched s WHERE s.trip_id = t.trip_id)")}


def postanki(tid):
    """Vožnja in stop_seq -> postanek; nagrobnik prek iste šifre in ure odhoda."""
    s = STARE.get(tid)
    if s is not None:
        kandidati = [x for x, st in ZIVE.get((s["agency"], s["train_no"]), ()) if st == s["start_s"]]
        if not kandidati:
            return None, {}
        tid = kandidati[0]
    v = deljenje.voznja(conn, tid)
    return (v, {p["stop_seq"]: p for p in v.postanki}) if v is not None else (None, {})


zapisi = []
for dan in DNI:
    for (tid, ag), rr in odsek_prehodov(dan).items():
        v, idx = postanki(tid)
        if v is None:
            continue
        for a, b in zip(rr, rr[1:]):
            pa, pb = idx.get(a["stop_seq"]), idx.get(b["stop_seq"])
            if pa is None or pb is None:
                continue
            t0 = pa["dep_s"] if pa["dep_s"] is not None else pa["arr_s"]
            t1 = pb["arr_s"] if pb["arr_s"] is not None else pb["dep_s"]
            s = t1 - t0
            dolzina = pb["along"] - pa["along"]
            if s < NAJMANJ_S or dolzina < 1000:
                continue
            polnoc = a["prehod_ts"] - a["zamuda_s"] - t0
            # Zamuda j je proti njegovemu odhodu, ostanek do prehoda: isto merilo.
            t1 = b["prehod_ts"] - b["zamuda_s"] - polnoc
            if abs(t1 - (pb["dep_s"] if pb["dep_s"] is not None else pb["arr_s"])) > 120:
                continue                    # naslednica ima drug vozni red ali postanke
            lege = conn.execute(
                "SELECT ts, lat, lon FROM lega WHERE service_date = ? AND trip_id = ? "
                "AND ts > ? AND ts < ? ORDER BY ts", (dan, tid, a["prehod_ts"], b["prehod_ts"])).fetchall()
            zadnji = 0
            for ts, lat, lon in lege:
                if ts - zadnji < 60:
                    continue
                along, odmik = v.trasa.projiciraj(lat, lon, od_m=pa["along"] - 300, do_m=pb["along"] + 300)
                if odmik > ODMIK_MAX_M:
                    continue
                zadnji = ts
                f = max(0.0, min(1.0, (along - pa["along"]) / dolzina))
                razd = ts - polnoc - (t0 + f * s)
                ostane = b["prehod_ts"] - ts
                zapisi.append(dict(dan=dan, tid=tid, ag=ag, odsek=(pa["name"], pb["name"], round(dolzina / 500)),
                                   s=s, f=round(f, 3), carry=a["zamuda_s"], razd=round(razd), resnica=b["zamuda_s"],
                                   ostane=ostane, t1=t1, ts=ts, polnoc=polnoc, kos=int(f / KOS)))
    print(dan, "vzorcev skupaj", len(zapisi), flush=True)

# Profil: mediana ostanka po (a, b, koš), brez istega dne.
prof = collections.defaultdict(lambda: collections.defaultdict(list))
for z in zapisi:
    prof[(z["odsek"], z["kos"])][z["dan"]].append(z["ostane"])
for z in zapisi:
    dni = prof[(z["odsek"], z["kos"])]
    vals = [x for d, xs in dni.items() if d != z["dan"] for x in xs]
    n_dni = sum(1 for d in dni if d != z["dan"])
    if n_dni >= 3:
        z["profil"] = round(z["ts"] - z["polnoc"] + statistics.median(vals) - z["t1"])
    else:
        z["profil"] = None

with open("/tmp/dolg_odsek.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["dan", "tid", "ag", "odsek", "ts", "s", "f", "carry", "razd", "profil", "resnica", "ostane"],
                       extrasaction="ignore")
    w.writeheader()
    w.writerows(zapisi)


def vrsta(ime, xs):
    if not xs:
        print(f"{ime:26s} 0")
        return
    n = len(xs)
    c = [abs(z["carry"] - z["resnica"]) for z in xs]
    r = [abs(z["razd"] - z["resnica"]) for z in xs]
    pr = [z for z in xs if z["profil"] is not None]
    p = [abs(z["profil"] - z["resnica"]) for z in pr]
    pc = [abs(z["carry"] - z["resnica"]) for z in pr]
    pristr_r = statistics.mean(z["razd"] - z["resnica"] for z in xs) / 60
    print(f"{ime:26s} n {n:6d} | MAE prenos {statistics.mean(c) / 60:5.2f} razdalja {statistics.mean(r) / 60:5.2f} "
          f"(pristr {pristr_r:+.2f}) v2 {sum(x <= 120 for x in c) / n:.0%}->{sum(x <= 120 for x in r) / n:.0%}"
          + (f" | profil n {len(pr)} prenos {statistics.mean(pc) / 60:5.2f} profil {statistics.mean(p) / 60:5.2f} "
             f"v2 {sum(x <= 120 for x in pc) / len(pr):.0%}->{sum(x <= 120 for x in p) / len(pr):.0%}" if pr else ""))


for lo, hi in ((0, .15), (.15, .3), (.3, .5), (.5, .7), (.7, .85), (.85, .95), (.95, 1.01)):
    vrsta(f"delež {lo:.2f}-{hi:.2f}", [z for z in zapisi if lo <= z["f"] < hi])
for lo, hi in ((900, 1800), (1800, 10 ** 6)):
    vrsta(f"odsek {lo // 60}-{hi // 60} min", [z for z in zapisi if lo <= z["s"] < hi])
for ag in ("1119", "1121", "1123"):
    vrsta(f"prevoznik {ag}", [z for z in zapisi if z["ag"] == ag])
vrsta("vse", zapisi)
