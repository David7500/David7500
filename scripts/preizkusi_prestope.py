"""Ali prestop drži -- in koliko je to mogoče vedeti vnaprej?

Predlogi poti od vrat do vrat (`pot.isci`) na voznem redu enega dne, za
naključne pare krajev ob naključnih urah: prestopi, kot jih potnik res vidi.
Za vsak prestop vožnje A (izstop) na vožnjo B (vstop) in vsak pretekli dan,
ko sta vozili obe (vožnja čez dneve, `db.voznja_sql`):

    držal = rezerva po voznem redu + zamuda B ob odhodu - zamuda A ob prihodu >= 0

Rezerva je že brez hoje vmes (`nacrtovano_s`). Zamuda A je PRIHODNA
(`COALESCE(delay_arr, delay_dep)`): vlak na dolgem postanku odpelje z manjšo
zamudo, kot je pripeljal, in prestop šteje prihod. Zamuda B je odhodna.

Tri vprašanja:

  vnaprej   Kaj vemo za jutri: izpustitev dneva, napoved za dan d iz ostalih
            dni, izid na dan d. Modeli `globalno` (delež vseh), `rezerva` (po
            omrežju A in razredu rezerve), `par` (ta prestop na ostale dni) in
            `par+kN` (par, skrčen proti `rezerva` z utežjo N dni).
  zdaj      Kaj vemo, ko sta vozili na poti: senca (`napoved`) ima za oba
            postanka številko, ki jo je prikaz kazal 25 min (vlak) oz. 15 min
            (avtobus) prej, in resnico. Verjetnost iz porazdelitve napak sence
            (`pot.verjetnost_zdaj`) proti deležu po razredu preostale rezerve.
  rok       "Biti tam do": delež dni, ko bi bil pravočasno (vsi prestopi in
            prihod do roka), z izpustitvijo dneva.

Zagon: ./venv/bin/python scripts/preizkusi_prestope.py [vprašanj] [dan]
"""
import math
import random
import sys
import time
from collections import defaultdict
from datetime import date

sys.path.insert(0, ".")
from kajros import config, db, geo, journey, pot, stats       # noqa: E402

# Usmerjevalnik ni potreben: rezerva prestopa je iz voznega reda in pešpoti
# med postajališči (`hoja.pespoti`), hoja do vrat pa za to merilo ni pomembna.
config.OSRM_URL = ""

N = int(sys.argv[1]) if len(sys.argv) > 1 else 400
DAN = sys.argv[2] if len(sys.argv) > 2 else date.today().isoformat()
random.seed(7)

conn = db.connect()
t0 = time.perf_counter()
by_trip, at_stop = journey._timetable_for_day(conn, DAN, None)
imena = pot._imena(conn)
promet = {sid: len(v) for sid, v in at_stop.items() if sid in imena}
postaje = [s for s, n in promet.items() if n >= 20]
teze = [promet[s] for s in postaje]
print(f"vozni red {DAN}: {len(by_trip)} voženj, {len(postaje)} postajališč z ≥ 20 odhodi "
      f"({time.perf_counter() - t0:.1f} s)")


def kraj(sid):
    """Točka do 250 m od postajališča: vrata, ne peron."""
    _, lat, lon = imena[sid]
    r = random.uniform(30, 250)
    a = random.uniform(0, 2 * math.pi)
    return (lat + r * math.cos(a) / 111_320,
            lon + r * math.sin(a) / (111_320 * math.cos(math.radians(lat))))


def par():
    """Polovica mestnih (2-10 km), polovica medkrajevnih (10-80 km)."""
    meje = (2_000, 10_000) if random.random() < 0.5 else (10_000, 80_000)
    while True:
        a, b = random.choices(postaje, teze, k=2)
        d = geo.haversine(imena[a][1], imena[a][2], imena[b][1], imena[b][2])
        if meje[0] <= d <= meje[1]:
            return kraj(a), kraj(b)


prestopi = {}            # (A, a_seq, B, b_seq) -> opis
roki = []                # (noge [(trip, od_seq, do_seq)], prestopi [ključ], rezerva do roka)
t0 = time.perf_counter()
for i in range(N):
    od, do = par()
    ura = random.randint(6 * 3600, 20 * 3600)
    z_rokom = random.random() < 0.5
    try:
        if z_rokom:
            izid = pot.isci(conn, od, do, DAN, None, prihod_do_s=ura + 3600, now_s=None)
        else:
            izid = pot.isci(conn, od, do, DAN, ura, now_s=None)
    except Exception as e:                           # merilo, ne strežba
        print("  napaka:", e)
        continue
    for p in izid["predlogi"]:
        voznje = [n for n in p["noge"] if n["vrsta"] == "voznja"]
        kljuci = []
        for a, b, t in zip(voznje, voznje[1:], p.get("prestopi") or []):
            kljuc = (a["trip_id"], a["do_seq"], b["trip_id"], b["od_seq"])
            kljuci.append(kljuc)
            prestopi.setdefault(kljuc, {
                "rezerva_s": t["nacrtovano_s"], "omr_a": a["network"], "omr_b": b["network"],
                "kje": t["kje"],
            })
        if z_rokom and voznje and izid.get("prihod_do"):
            roki.append(([(n["trip_id"], n["od_seq"], n["do_seq"]) for n in voznje], kljuci,
                         izid["prihod_do"] - p["prihod"], voznje[-1]["network"]))
    if (i + 1) % 100 == 0:
        print(f"  {i + 1} vprašanj, {len(prestopi)} prestopov ({time.perf_counter() - t0:.0f} s)")
print(f"prestopov: {len(prestopi)}, predlogov z rokom: {len(roki)}")


def senca(pari):
    """{(trip_id, seq): {dan: (ours_s, actual_s, na_poti)}} iz `napoved`."""
    out = defaultdict(dict)
    pari = sorted(set(pari))
    for i in range(0, len(pari), 400):
        kos = pari[i:i + 400]
        vals = ",".join(["(?,?)"] * len(kos))
        for r in conn.execute(
                f"WITH want(trip_id, stop_seq) AS (VALUES {vals}) "
                f"SELECT w.trip_id, w.stop_seq, n.service_date, n.ours_s, n.actual_s, "
                f"       n.current_s IS NOT NULL AS na_poti "
                f"FROM want w CROSS JOIN trip a ON a.trip_id = w.trip_id "
                f"CROSS JOIN trip t ON {db.voznja_sql('t')} = {db.voznja_sql('a')} "
                f"CROSS JOIN napoved n ON n.trip_id = t.trip_id AND n.stop_seq = w.stop_seq "
                f"WHERE n.actual_s IS NOT NULL AND n.ours_s IS NOT NULL "
                f"  AND ABS(n.actual_s) <= {stats.MAX_REALNA_ZAMUDA_S}",
                [x for p in kos for x in p]):
            out[(r["trip_id"], r["stop_seq"])][r["service_date"]] = (
                r["ours_s"], r["actual_s"], bool(r["na_poti"]))
    return out


t0 = time.perf_counter()
vse_noge = [n for noge, *_ in roki for n in noge]
prihodi = pot.zamude_po_dnevih(
    conn, [(k[0], k[1]) for k in prestopi] + [(t, b) for t, _, b in vse_noge], DAN, prihod=True)
odhodi = pot.zamude_po_dnevih(conn, [(k[2], k[3]) for k in prestopi], DAN, prihod=False)
print(f"zgodovina: {time.perf_counter() - t0:.1f} s")


def razred(s):
    return "0-3" if s < 180 else "3-6" if s < 360 else "6-10" if s < 600 else "10+"


def ocena(ok, n, prior, k):
    return (ok + k * prior) / (n + k) if n > 0 else prior


def vrednoti(ime, napovedi):
    """`napovedi` = [(p, izid)]: Brier, log-loss in umerjenost po desetinah."""
    if not napovedi:
        print(f"  {ime:24} brez primerov")
        return
    n = len(napovedi)
    b = sum((p - ok) ** 2 for p, ok in napovedi) / n
    ll = -sum(math.log(min(max(p, 1e-3), 1 - 1e-3) if ok else 1 - min(max(p, 1e-3), 1 - 1e-3))
              for p, ok in napovedi) / n
    print(f"  {ime:24} n={n:6}  Brier {b:.4f}  log-loss {ll:.4f}")
    return b


def umerjenost(ime, napovedi):
    razredi = defaultdict(lambda: [0, 0.0, 0])
    for p, ok in napovedi:
        r = razredi[min(9, int(p * 10))]
        r[0] += 1
        r[1] += p
        r[2] += ok
    print(f"\n== umerjenost: {ime}")
    print(f"  {'napoved':>9} {'n':>7} {'povp. napoved':>14} {'res':>7}")
    for r in sorted(razredi):
        cnt, vsota, ok = razredi[r]
        print(f"  {r * 10:3d}-{r * 10 + 10:3d} % {cnt:7d} {vsota / cnt * 100:13.1f} % {ok / cnt * 100:6.1f} %")


# ---------------------------------------------------------------- vnaprej

izidi = []               # (prestop, dan, držal)
for k, o in prestopi.items():
    a, b = prihodi.get((k[0], k[1]), {}), odhodi.get((k[2], k[3]), {})
    for d, za in a.items():
        if d in b:
            izidi.append((k, d, o["rezerva_s"] + b[d] - za >= 0))
print(f"parov dan-prestop: {len(izidi)}; prestopov z vsaj enim dnem: {len({x[0] for x in izidi})}")


def kljuc_rezerve(k):
    o = prestopi[k]
    return (o["omr_a"], razred(o["rezerva_s"]))


vse = [0, 0]
po_razredu = defaultdict(lambda: [0, 0])
po_paru = defaultdict(lambda: [0, 0])
dan_vse = defaultdict(lambda: [0, 0])
dan_razred = defaultdict(lambda: [0, 0])
po_omr = defaultdict(lambda: [0, 0])
for k, d, ok in izidi:
    o = prestopi[k]
    for c in (vse, po_razredu[kljuc_rezerve(k)], po_paru[k], dan_vse[d],
              dan_razred[(d, kljuc_rezerve(k))], po_omr[(o["omr_a"], o["omr_b"], razred(o["rezerva_s"]))]):
        c[0] += ok
        c[1] += 1

print("\n== delež, ki drži, po omrežju A → B in rezervi (vsi dnevi)")
for kr, (ok, n) in sorted(po_omr.items()):
    print(f"  {kr[0]:10} → {kr[1]:10} rezerva {kr[2]:>5} min  {ok / n * 100:5.1f} %  n={n}")

MODELI = ["globalno", "rezerva", "par", "par+k1", "par+k2", "par+k4", "par+k8"]
napovedi = defaultdict(list)
for k, d, ok in izidi:
    ok_v, n_v = vse[0] - dan_vse[d][0], vse[1] - dan_vse[d][1]
    kr = kljuc_rezerve(k)
    ok_r = po_razredu[kr][0] - dan_razred[(d, kr)][0]
    n_r = po_razredu[kr][1] - dan_razred[(d, kr)][1]
    ok_p, n_p = po_paru[k][0] - ok, po_paru[k][1] - 1
    globalno = ok_v / n_v if n_v else 0.9
    rezerva = (ok_r + 1) / (n_r + 2) if n_r else globalno
    napovedi["globalno"].append((globalno, ok))
    napovedi["rezerva"].append((rezerva, ok))
    napovedi["par"].append((ok_p / n_p if n_p > 0 else rezerva, ok))
    for kd in (1, 2, 4, 8):
        napovedi[f"par+k{kd}"].append((ocena(ok_p, n_p, rezerva, kd), ok))

print("\n== vnaprej: izpustitev dneva")
for m in MODELI:
    vrednoti(m, napovedi[m])
umerjenost("vnaprej, par+k2", napovedi["par+k2"])

dni_na_par = sorted(n for _, n in po_paru.values())
if dni_na_par:
    print(f"\n== dni na prestop: mediana {dni_na_par[len(dni_na_par) // 2]}, "
          f"p10 {dni_na_par[len(dni_na_par) // 10]}, "
          f"brez zgodovine {len(prestopi) - len(dni_na_par)} od {len(prestopi)}")

# ---------------------------------------------------------------- zdaj

t0 = time.perf_counter()
sa = senca([(k[0], k[1]) for k in prestopi])
sb = senca([(k[2], k[3]) for k in prestopi])
napake = pot.napake_sence(conn)
print(f"\nsenca: {time.perf_counter() - t0:.1f} s")
zivo = []                # (k, dan, ostane_s, omr_a, omr_b, na_poti_a, na_poti_b, izid)
for k, o in prestopi.items():
    for d, (ours_a, act_a, poti_a) in sa.get((k[0], k[1]), {}).items():
        b = sb.get((k[2], k[3]), {}).get(d)
        if not b:
            continue
        ours_b, act_b, poti_b = b
        zivo.append((k, d, o["rezerva_s"] + ours_b - ours_a, o["omr_a"], o["omr_b"],
                     poti_a, poti_b, o["rezerva_s"] + act_b - act_a >= 0))
print(f"prestopov z obema številkama sence istega dne: {len(zivo)}")


def razred_ostanka(m):
    return min(8, max(-2, m // 120))


po_ostanku = defaultdict(lambda: [0, 0])
for _, _, m, oa, *_, ok in zivo:
    c = po_ostanku[(oa, razred_ostanka(m))]
    c[0] += ok
    c[1] += 1
print("\n== zdaj: delež, ki drži, po preostali rezervi (po prikazu ob pogledu)")
for (oa, r), (ok, n) in sorted(po_ostanku.items()):
    print(f"  {oa:10} ostane {r * 2:>3}-{r * 2 + 2:<3} min  {ok / n * 100:5.1f} %  n={n}")

model, razredno = [], []
for k, d, m, oa, ob, pa, pb, ok in zivo:
    model.append((pot.verjetnost_zdaj(m, oa, ob, pa, pb, napake), ok))
    c = po_ostanku[(oa, razred_ostanka(m))]
    razredno.append(((c[0] - ok + 1) / (c[1] - 1 + 2), ok))
print("\n== zdaj: modela")
vrednoti("razred ostanka (izp.)", razredno)
vrednoti("porazdelitev napak", model)
umerjenost("zdaj, porazdelitev napak", model)

# ---------------------------------------------------------------- rok

pravocasni = []          # (indeks predloga, dan, izid)
for i, (noge, kljuci, rezerva, omr) in enumerate(roki):
    dnevi = set(prihodi.get((noge[-1][0], noge[-1][2]), {}))
    for k in kljuci:
        dnevi &= set(prihodi.get((k[0], k[1]), {})) & set(odhodi.get((k[2], k[3]), {}))
    for d in dnevi:
        drzi = all(prestopi[k]["rezerva_s"] + odhodi[(k[2], k[3])][d]
                   - prihodi[(k[0], k[1])][d] >= 0 for k in kljuci)
        pravocasni.append((i, d, drzi and prihodi[(noge[-1][0], noge[-1][2])][d] <= rezerva))
po_predlogu = defaultdict(lambda: [0, 0])
skupaj = [0, 0]
dan_skupaj = defaultdict(lambda: [0, 0])
for i, d, ok in pravocasni:
    for c in (po_predlogu[i], skupaj, dan_skupaj[d]):
        c[0] += ok
        c[1] += 1
# Izhodišče, kot ga računa `pot.pripni_tveganje`: zmnožek verjetnosti
# prestopov (par+k2) in deleža dni, ko je zadnja vožnja prišla v rezervi roka
# (njena zgodovina sama, brez prestopov -- teh dni je več).
par_k2 = {(k, d): p for (k, d, _), (p, _) in zip(izidi, napovedi["par+k2"])}
zadnja = defaultdict(lambda: [0, 0])
for i, (noge, _, rezerva, _) in enumerate(roki):
    for d, z in prihodi.get((noge[-1][0], noge[-1][2]), {}).items():
        zadnja[i][0] += z <= rezerva
        zadnja[i][1] += 1
q0 = sum(c[0] for c in zadnja.values()) / max(1, sum(c[1] for c in zadnja.values()))
print(f"zadnja vožnja v rezervi roka: {q0 * 100:.1f} %")


def razred_roka(r):
    return "0-2" if r < 120 else "2-5" if r < 300 else "5-10" if r < 600 \
        else "10-20" if r < 1200 else "20+"


po_rezervi = defaultdict(lambda: [0, 0])
for i, (noge, _, rezerva, omr) in enumerate(roki):
    for z in prihodi.get((noge[-1][0], noge[-1][2]), {}).values():
        c = po_rezervi[(omr, razred_roka(rezerva))]
        c[0] += z <= rezerva
        c[1] += 1
print("\n== zadnja vožnja v rezervi do roka, po omrežju in rezervi")
for (omr, r), (ok, n) in sorted(po_rezervi.items()):
    print(f"  {omr:10} rezerva {r:>6} min  {ok / n * 100:5.1f} %  n={n}")
rok_napovedi = defaultdict(list)
for i, d, ok in pravocasni:
    g = (skupaj[0] - dan_skupaj[d][0]) / max(1, skupaj[1] - dan_skupaj[d][1])
    ok_p, n_p = po_predlogu[i][0] - ok, po_predlogu[i][1] - 1
    noge, kljuci, rezerva, _ = roki[i]
    z_d = prihodi[(noge[-1][0], noge[-1][2])][d] <= rezerva
    q = ocena(zadnja[i][0] - z_d, zadnja[i][1] - 1, q0, 2)
    zmnozek = q * math.prod(par_k2[(k, d)] for k in kljuci)
    # Izhodišče po rezervi do roka (kot `pot.ROK_IZHODISCE`): z dvema
    # minutama rezerve je zadnja vožnja pravočasna v 27 %, z dvajsetimi v 98 %.
    c = po_rezervi[(roki[i][3], razred_roka(rezerva))]
    q_r = ocena(zadnja[i][0] - z_d, zadnja[i][1] - 1, (c[0] - z_d) / max(1, c[1] - 1), 2)
    rok_napovedi["zmnožek, izhodišče po rezervi"].append(
        (q_r * math.prod(par_k2[(k, d)] for k in kljuci), ok))
    rok_napovedi["globalno"].append((g, ok))
    rok_napovedi["predlog+k2"].append((ocena(ok_p, n_p, g, 2), ok))
    rok_napovedi["zmnožek"].append((zmnozek, ok))
    rok_napovedi["predlog+k2 proti zmnožku"].append((ocena(ok_p, n_p, zmnozek, 2), ok))
print(f"\n== rok: {len(pravocasni)} dan-predlogov, pravočasno {skupaj[0] / max(1, skupaj[1]) * 100:.1f} %")
vrednoti("globalno", rok_napovedi["globalno"])
for m in ("predlog+k2", "zmnožek", "predlog+k2 proti zmnožku", "zmnožek, izhodišče po rezervi"):
    vrednoti(m, rok_napovedi[m])
umerjenost("rok, zmnožek, izhodišče po rezervi", rok_napovedi["zmnožek, izhodišče po rezervi"])
