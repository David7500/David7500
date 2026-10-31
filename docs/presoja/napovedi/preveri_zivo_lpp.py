"""Koledar ned 1. 11. 2026: okna mestnega LPP po objavi aeadaa9. SAMO BRANJE, samo javni API.

    ./venv/bin/python -I preveri_zivo_lpp.py https://kajros.app [najvec_oken, do 40] [--brez-ogrevanja]

Za vsako mestno vozilo LPP z vožnjo: `/api/vehicles` (lega) + `/api/train/{no}/run?trip=`
(okno), ~2,5 zahteve/s, največ 80 oken v dveh krogih, nič se ne piše. Prvi krog samo ogreje:
strežnik bere data.lpp.si v ozadju (`lpp._prinesi`, 0,3 s čakanja, vir mediana 7 s), brez
ogrevanja ima okno živo številko le, če je vzorec nekdo gledal v zadnjih 90 s. Lega je stara
do ~2 min, zato je "za vozilom" šele > 1 postanek nazaj od najbližje tetive.

Vrne kodo 1, če drži katera od NAPAK (+92 iz koledarja):
  A  "v živo" >= +30 min na postanku za vozilom
  B  okno brez meje: izhodišče ocene naprej (kot `common.fetchRunAndForecast`: prvi postanek
     z zamudo) >= +30 min ali za vozilom z |zamuda| >= 30 min
Prava zamuda >= 30 min je mogoča: vsak zadetek preveri na povezavi (lega proti oknu).
Samo izpiše OPOZORILA (druga oblika iste napake in izguba):
  C  "v živo" >= +30 min pred vozilom (naslednji obisk za postankom z manjšim eta)
  D  "v živo" <= -10 min (eta 1 na obvozu ali končni: LPP vrsta 3, 18L)
  E  luknja: >= 3 postanki med vozilom in prvim "v živo", vozilo pa ima meritev ali lego
     (pravilo je vzelo prave številke: min-eta na napačnem postanku)
"""
import json
import math
import sys
import time
import urllib.parse
import urllib.request

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "https://kajros.app"
NAJVEC = min(int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 40, 40)
UA = "kajros-presoja/1.0 (koledar 1. 11., samo branje)"
PAVZA = 0.4


def get(pot):
    time.sleep(PAVZA)
    req = urllib.request.Request(BASE + pot, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read())
    except Exception as e:  # noqa: BLE001 -- posnetek ne pade zaradi enega okna
        print("  napaka", pot[:70], repr(e)[:80])
        return None


def tetiva(lat, lon, a, b):
    k = math.cos(math.radians(lat))
    ax, ay = (a["lon"] - lon) * k * 111320, (a["lat"] - lat) * 111320
    bx, by = (b["lon"] - lon) * k * 111320, (b["lat"] - lat) * 111320
    dx, dy = bx - ax, by - ay
    d2 = dx * dx + dy * dy
    t = 0.0 if d2 == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / d2))
    return math.hypot(ax + t * dx, ay + t * dy)


def naslednji_po_gps(stops, lat, lon):
    naj, seq = 1e12, None
    for a, b in zip(stops, stops[1:]):
        if None in (a.get("lat"), b.get("lat")):
            continue
        d = tetiva(lat, lon, a, b)
        if d < naj - 1e-6:
            naj, seq = d, b["stop_seq"]
    return seq, naj


vozila = get("/api/vehicles") or []
mestni = {}
for v in vozila:
    t = v.get("trip_id") or ""
    if v.get("agency") == "lpp" and t.count("|") == 2 and v.get("lat"):
        mestni.setdefault(t, v)
print(f"{BASE}: mestnih voženj z lego {len(mestni)} (vseh vozil {len(vozila)})")

# Prvi krog: strežnik začne brati vzorce v ozadju; odgovor ne šteje.
if "--brez-ogrevanja" not in sys.argv:
    for tid, v in list(mestni.items())[:NAJVEC]:
        get(f"/api/train/{urllib.parse.quote(v['train_no'], safe='')}/run?trip={urllib.parse.quote(tid, safe='')}")
    time.sleep(25)
    vozila = get("/api/vehicles") or []
    mestni = {}
    for v in vozila:
        t = v.get("trip_id") or ""
        if v.get("agency") == "lpp" and t.count("|") == 2 and v.get("lat"):
            mestni.setdefault(t, v)

st = dict(oken=0, z_zivim=0, brez_meje=0, brez_meje_sredi=0, zivih=0, A=0, B=0, C=0, D=0, E=0)
primeri = []
for tid, v in list(mestni.items())[:NAJVEC]:
    no = urllib.parse.quote(v["train_no"], safe="")
    q = urllib.parse.quote(tid, safe="")
    dan = f"&date={v['service_date']}" if v.get("service_date") else ""
    run = get(f"/api/train/{no}/run?trip={q}{dan}")
    if not run:
        continue
    st["oken"] += 1
    stops = run["stops"]
    zive = [s for s in stops if (s.get("zamuda") or {}).get("vrsta") == "živo"]
    meja = run.get("last_measured_seq")
    g, dist = naslednji_po_gps(stops, v["lat"], v["lon"])
    if not zive:
        continue
    st["z_zivim"] += 1
    st["zivih"] += len(zive)
    st["brez_meje"] += meja is None
    st["brez_meje_sredi"] += meja is None and g is not None and g > 3
    povezava = f"/app/bus/{no}?trip={q}"
    oznaka = f"{v['train_no']} {(stops[0].get('sched_dep') or '')[11:16]} meja={meja} gps={g}({dist:.0f} m, lega {v.get('age_s')} s)"
    na_voljo_za_gps = dist <= 300  # dlje: vozilo ni na tej poti, "za vozilom" nima pomena
    # Izhodišče ocene: isto kot `fetchRunAndForecast`.
    baza = next((s for s in stops if s["stop_seq"] == meja), None) if meja is not None else None
    if baza is None:
        baza = next((s for s in stops if s.get("zamuda")), None)
    if baza is not None:
        bs = baza["zamuda"]["s"]
        za = na_voljo_za_gps and g is not None and baza["stop_seq"] < g - 1
        if meja is None and (bs >= 1800 or (za and abs(bs) >= 1800)):
            st["B"] += 1
            primeri.append(("B", oznaka, f"izhodišče ocene {baza['name']} {bs // 60:+d} min", povezava))
    prvi_ziv = zive[0]["stop_seq"]
    for s in zive:
        z = s["zamuda"]["s"]
        za = na_voljo_za_gps and g is not None and s["stop_seq"] < g - 1
        if z >= 1800 and za:
            st["A"] += 1
            primeri.append(("A", oznaka, f"{s['name']} {z // 60:+d} v živo, za vozilom", povezava))
        elif z >= 1800:
            st["C"] += 1
            primeri.append(("C", oznaka, f"{s['name']} (post. {s['stop_seq']}) {z // 60:+d} v živo", povezava))
        if z <= -600:
            st["D"] += 1
            primeri.append(("D", oznaka, f"{s['name']} (post. {s['stop_seq']}) {z // 60:+d} v živo", povezava))
    od = max(meja or 0, (g - 1) if (g and na_voljo_za_gps) else 0)
    luknja = [s for s in stops if od < s["stop_seq"] < prvi_ziv]
    if len(luknja) >= 3:
        st["E"] += 1
        primeri.append(("E", oznaka, f"{len(luknja)} postankov brez živega, prvi živi {zive[0]['name']} (post. {prvi_ziv}) {zive[0]['zamuda']['s'] // 60:+d}", povezava))

print(json.dumps(st, ensure_ascii=False))
for p in primeri:
    print(*p[:3], sep=" | ")
    print("    ", BASE + p[3])
napake = st["A"] + st["B"]
print("NAPAKE (A+B):", napake, "· opozorila C/D/E:", st["C"], st["D"], st["E"])
sys.exit(1 if napake else 0)
