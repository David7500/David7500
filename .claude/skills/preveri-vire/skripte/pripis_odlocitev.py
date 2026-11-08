"""Odločitev o priklopu pripisa NAP iz `pripis_senca` (samo branje). Dopolnilo k `pripis_nap.py`.

Enota = par (vozilo, naša vožnja, dan), ne vrstica in ne niz: `vec` vmes niz razbije in napihne vzorec.
Vsak par dobi natanko eno oznako; vsote se preverijo. Ocena velja za senco z vrati premika
(`PREMIK_*`), ker priklop brez njih ne pride v poštev. „Napačen“ pomeni dokazano napačen: resnice na
produkciji ni, zato pravilo ne more trditi „brez napačnih“, samo zgornjo mejo iz velikosti vzorca.

Argumenti: DAN ali OD..DO (skupen vzorec) [--baza POT] [--od URA] [--do URA] [--seznam N]
[--smer] [--koda POT]
Zagon (samo branje, na stroju ne ostane nič):
  ssh david@192.168.1.46 '/opt/kajros/.venv/bin/python -I - 2026-11-01' < pripis_odlocitev.py

`--smer` (od 8. 11. 2026): vrata smeri kot `nap.Senca` -- vrstica gre skozi vrata, kadar
`pripis.naprej` potrdi premik naprej po naši vožnji iz leg istega vozila 2-5 min prej
(`pripis.na_voznji` na teh legah, samo kjer bi bila vožnja v oknu sence). Koda iz `--koda`
(privzeto /opt/kajros; za neobjavljeno kodo kopija paketa `kajros`). Doda drugo merilo,
neodvisno od preteklih leg: pot vozila v naslednjih 15 min po prvi vrstici skozi vrata
(`pot` spodaj).
"""
import argparse
import collections
import functools
import math
import os
import sqlite3
import time

os.environ["TZ"] = "Europe/Ljubljana"
time.tzset()

ap = argparse.ArgumentParser()
ap.add_argument("dan", help="DAN ali OD..DO (skupen vzorec čez dneve)")
ap.add_argument("--baza", default="/var/lib/kajros/kajros.sqlite")
ap.add_argument("--od", type=float, default=0.0, help="samo vrstice od te ure (lokalno)")
ap.add_argument("--do", type=float, default=24.0)
ap.add_argument("--seznam", type=int, default=40)
ap.add_argument("--stoji-m", type=float, default=150.0)
ap.add_argument("--smer", action="store_true", help="vrata smeri (pripis.naprej) in drugo merilo")
ap.add_argument("--koda", default="/opt/kajros", help="imenik s paketom kajros za --smer")
ap.add_argument("--konec", type=float, default=None,
                help="z --smer: vrstica s krajem v zadnjih KONEC s vožnje ne gre skozi vrata (poskus)")
a = ap.parse_args()
dan_od, dan_do = (a.dan.split("..") + [a.dan])[:2]
conn = sqlite3.connect(f"file:{a.baza}?mode=ro", uri=True)
if not conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'pripis_senca'").fetchone():
    raise SystemExit("tabele pripis_senca ni: senca še ni objavljena na tej bazi")

#: Koledar: neverjetna prijava = napačen dan ali vožnja daleč naprej. Drugi vzroki se ne priklopijo.
OBSEG = ("brez_dneva", "prezgodaj")
MIN_PAROV, MIN_VOZIL = 30, 10
NAJVEC_NEPOTRJENIH = 0.10
#: Krajši napačen par (vrstica ~ minuta) je meja med vožnjama: se izpiše, ne odloča.
MIN_VRSTIC_NAPAKE = 3
#: Vrata premika: par samo vozilu, ki se je v zadnjih PREMIK_S premaknilo za PREMIK_M. `Napredek` tega
#: ne zagotovi: stoječe vozilo preide iz `miruje` v par, ko se najbližja kandidatka zamenja.
PREMIK_S, PREMIK_M = 300, 150.0

V = collections.namedtuple("V", "ts voz vzrok nap nasa nd razlog zam derp lat lon dan")
vrst = [V(*r) for r in conn.execute(
    "SELECT ts, vozilo, vzrok, nap_voznja, nasa_voznja, nas_dan, razlog, zamuda_s, derp_voznja, lat, lon, dan "
    "FROM pripis_senca WHERE dan BETWEEN ? AND ? ORDER BY vozilo, ts", (dan_od, dan_do))]
if not vrst:
    print(f"{a.dan}: v pripis_senca ni vrstic")
    raise SystemExit(0)


def razd(la1, lo1, la2, lo2):
    return math.hypot((la1 - la2) * 111195, (lo1 - lo2) * 111195 * math.cos(math.radians(la1)))


def ura(ts):
    return time.strftime("%H:%M", time.localtime(ts))


def v_oknu(ts):
    h = time.localtime(ts)
    return a.od <= h.tm_hour + h.tm_min / 60 < a.do


T = {r[0]: r[1:] for r in conn.execute("SELECT trip_id, route_id, start_s, end_s FROM trip")}


def oknos(t):
    x = T.get(t)
    if x and x[1] is not None and x[2] is not None:
        return f"{t} {x[1] // 3600:02d}:{x[1] % 3600 // 60:02d}-{x[2] // 3600:02d}:{x[2] % 3600 // 60:02d}"
    return f"{t} (ni voznega reda)"


@functools.lru_cache(maxsize=None)
def konci(t):
    """(prvi, zadnji) postanek vožnje; (None, None) pri nagrobniku."""
    r = conn.execute("SELECT st.lat, st.lon FROM sched s JOIN station st USING (stop_id) "
                     "WHERE s.trip_id = ? ORDER BY s.stop_seq", (t,)).fetchall()
    return (r[0], r[-1]) if r else (None, None)


def blizu(v, tocka, m):
    return bool(tocka) and tocka[0] is not None and razd(v.lat, v.lon, tocka[0], tocka[1]) <= m


@functools.lru_cache(maxsize=None)
def na_koledarju(t, dan):
    return conn.execute("SELECT 1 FROM trip t JOIN service_day sd ON sd.service_id = t.service_id AND sd.date = ? "
                        "WHERE t.trip_id = ?", (dan, t)).fetchone() is not None


@functools.lru_cache(maxsize=None)
def dvojcki(t, dan):
    """Vožnje na koledarju tega dne z isto progo, odhodom in prihodom: delavniški dvojček prazniške."""
    x = T.get(t)
    if not x or x[1] is None:
        return frozenset()
    return frozenset(r[0] for r in conn.execute(
        "SELECT t.trip_id FROM trip t JOIN service_day sd ON sd.service_id = t.service_id AND sd.date = ? "
        "WHERE t.route_id = ? AND t.start_s = ? AND t.end_s = ? AND t.trip_id != ?", (dan, x[0], x[1], x[2], t)))


def predhodnica(nasa, nap):
    """Naša vožnja se konča, kjer se NAP-ova začne, in ne pozneje: NAP naslednjo prijavi, vozilo vozi prejšnjo."""
    x, y = T.get(nasa), T.get(nap)
    if not x or not y or x[2] is None or y[1] is None or not -300 <= y[1] - x[2] <= 7200:
        return False
    k, z = konci(nasa)[1], konci(nap)[0]
    return bool(k and z) and k[0] is not None and z[0] is not None and razd(k[0], k[1], z[0], z[1]) <= 500


po_vozilu = collections.defaultdict(list)
kje = {}
for r in vrst:
    kje[(r.ts, r.voz)] = len(po_vozilu[r.voz])
    po_vozilu[r.voz].append(r)


def premik(r):
    """Največja razdalja od lege istega vozila v zadnjih PREMIK_S."""
    vs, i, naj = po_vozilu[r.voz], kje[(r.ts, r.voz)], 0.0
    while i >= 0 and r.ts - vs[i].ts <= PREMIK_S:
        naj = max(naj, razd(r.lat, r.lon, vs[i].lat, vs[i].lon))
        i -= 1
    return naj


if a.smer:
    import sys
    sys.path.insert(0, a.koda)
    from kajros import pripis as P  # noqa: E402
    from kajros import stats as S  # noqa: E402

    @functools.lru_cache(maxsize=None)
    def postanki(t):
        return conn.execute("SELECT s.stop_seq, st.lat, st.lon, COALESCE(s.dep_s, s.arr_s) FROM sched s "
                            "JOIN station st USING (stop_id) WHERE s.trip_id = ? ORDER BY s.stop_seq",
                            (t,)).fetchall()

    @functools.lru_cache(maxsize=None)
    def polnoc(d):
        return S.polnoc(d)

    def kraj(r, t, d):
        """Voznoredni čas kraja vozila na vožnji (t, d), kot ga računa senca, ali None, kadar
        vožnja ob r.ts ne bi bila kandidatka (zunaj okna sence) ali je vozilo dlje od tetive."""
        x = T.get(t)
        if not x or x[1] is None or x[2] is None:
            return None
        p0 = polnoc(d)
        if not p0 + x[1] + P.OKNO_S[0] <= r.ts <= p0 + x[2] + P.TEKMEC_S[1]:
            return None
        naj = P.na_voznji(postanki(t), r.lat, r.lon, r.ts - p0)
        return None if naj is None else naj[0]

    def smer_ok(r):
        """`nap.Senca`: zgodovina (ts, kraj) iz računov v zadnjih SMER_S, nato `pripis.naprej`."""
        vs, i = po_vozilu[r.voz], kje[(r.ts, r.voz)]
        zgo = []
        j = i - 1
        while j >= 0 and r.ts - vs[j].ts <= P.SMER_S:
            k = kraj(vs[j], r.nasa, r.nd)
            if k is not None:
                zgo.append((vs[j].ts, k))
            j -= 1
        zgo.reverse()
        k = kraj(r, r.nasa, r.nd)
        if k is not None and a.konec is not None and k >= T[r.nasa][2] - a.konec:
            return False
        return k is not None and P.naprej(zgo, r.ts, k)

    def pot(n):
        """Drugo merilo, neodvisno od leg pred parom: vozilo v naslednjih POT_S po prvi vrstici
        skozi vrata. Ob vsaki svoji vrstici (tudi brez para) mora biti na naši vožnji s
        podobno zamudo kot ob prvi (POT_ZAMUDA_S), kraj ne sme pasti za več kot POT_NAZAJ_S.
        `po poti` = vsaj POT_VRSTIC takih; `NAROBE po poti` = kraj pade ali vozilo zapusti
        vožnjo (tri zapored brez kraja) pred koncem; sicer `premalo leg`."""
        v0 = n["vrata"][0]
        x = T.get(n["nasa"])
        p0 = polnoc(n["nd"])
        konec = p0 + x[2] + v0.zam if x and x[2] is not None and v0.zam is not None else v0.ts + POT_S
        k0 = kraj(v0, n["nasa"], n["nd"])
        if k0 is None or v0.zam is None:
            return "premalo leg"
        dobrih, brez, naj_kraj = 0, 0, k0
        for r in po_vozilu[n["voz"]][kje[(v0.ts, v0.voz)] + 1:]:
            if r.ts - v0.ts > POT_S or r.ts > konec:
                break
            k = kraj(r, n["nasa"], n["nd"])
            if k is None:
                if naj_kraj >= x[2] - POT_NAZAJ_S:
                    break                       # na cilju: vožnja končana, vozilo gre naprej
                brez += 1
                if brez >= 3:
                    return "NAROBE po poti: zapusti vožnjo"
                continue
            brez = 0
            naj_kraj = max(naj_kraj, k)
            if k < naj_kraj - POT_NAZAJ_S:
                return "NAROBE po poti: kraj pade"
            if abs((r.ts - p0 - k) - v0.zam) <= POT_ZAMUDA_S:
                dobrih += 1
        return "po poti" if dobrih >= POT_VRSTIC else "premalo leg"


#: Drugo merilo (`pot`): 15 min po prvi vrstici skozi vrata, zamuda v 5 min od prve,
#: kraj ne pade za več kot 2 min, vsaj pet vrstic (računi so na minuto).
POT_S, POT_ZAMUDA_S, POT_NAZAJ_S, POT_VRSTIC = 900, 300, 120, 5

izbrane = [r for r in vrst if v_oknu(r.ts)]
pari = {}
for r in izbrane:
    if r.nasa is not None:
        pari.setdefault((r.voz, r.nasa, r.nd), {"voz": r.voz, "nasa": r.nasa, "nd": r.nd, "vr": []})["vr"].append(r)
pari = list(pari.values())


def oznaci(n):
    vs, nasa, nd, voz = n["vr"], n["nasa"], n["nd"], n["voz"]
    t1, t2 = vs[0].ts, vs[-1].ts
    okol = [r for r in po_vozilu[voz] if t1 - 130 <= r.ts <= t2 + 130]
    n["md"] = max(razd(okol[0].lat, okol[0].lon, r.lat, r.lon) for r in okol)
    stoji = n["md"] < a.stoji_m and okol[-1].ts - okol[0].ts >= 120
    n["kraj"] = 0 if any(r.zam is None for r in vs) else (t2 - vs[-1].zam) - (t1 - vs[0].zam)
    vv = n["vrata"] = [r for r in vs if premik(r) >= PREMIK_M and (not a.smer or smer_ok(r))]
    dt = vv[-1].ts - vv[0].ts if vv else 0
    dk = (vv[-1].ts - (vv[-1].zam or 0)) - (vv[0].ts - (vv[0].zam or 0)) if vv else 0
    # Vrstice brez vozila (NULL) se ne štejejo kot drugo vozilo: lahko je isto vozilo iz drugega vira.
    drugi = conn.execute("SELECT COUNT(DISTINCT vozilo) FROM lega WHERE service_date = ? AND trip_id = ? "
                         "AND vozilo != ? AND ts BETWEEN ? AND ?", (nd, nasa, voz, t1 - 600, t2 + 600)).fetchone()[0]
    n["brez_vozila"] = conn.execute("SELECT COUNT(*) FROM lega WHERE service_date = ? AND trip_id = ? "
                                    "AND vozilo IS NULL AND ts BETWEEN ? AND ?", (nd, nasa, t1 - 600, t2 + 600)).fetchone()[0]
    isti = conn.execute("SELECT COUNT(*) FROM lega WHERE service_date = ? AND trip_id = ? AND vozilo = ?",
                        (nd, nasa, voz)).fetchone()[0]
    prvi, zadnji = konci(nasa)
    napi = {(r.nap, r.nd) for r in vs}
    enako = all(r.nap == nasa for r in vs)
    dvojcek = any(nasa in dvojcki(x, d) for x, d in napi)
    if drugi:
        return "NAROBE drugo vozilo na vožnji"
    if stoji:
        if blizu(vs[-1], zadnji, 200) and isti:
            return "stoji na končni svoje vožnje"
        if (enako or dvojcek) and blizu(vs[0], prvi, 300):
            return "stoji pred NAP-ovo vožnjo"
        return "NAROBE stoji"
    if n["kraj"] < -60:
        return "NAROBE vozi nazaj"
    # Vožnja, ki je koledar ta dan nima: table gredo po koledarju, take zamude potnik ne bi videl.
    if not na_koledarju(nasa, nd):
        return "mimo koledarja (ne šteje, ne priklopi)"
    if enako:
        return "NAP-ov id, vozi"
    if isti:
        return "potrjen: NAP ga je imel na njej"
    if dvojcek:
        return "potrjen: dvojček NAP-ove vožnje"
    if any(predhodnica(nasa, x) for x, _ in napi):
        return "potrjen: prejšnja pred NAP-ovo"
    if any(r.derp == nasa for r in vs):
        return "potrjen: derp ima isto, NAP ne"
    # derp.si vožnjo določi sam: tretja vožnja, ne NAP-ova in ne naša, je edini neodvisen ugovor.
    if any(r.derp and r.derp not in (nasa, r.nap) for r in vs):
        return "NEPOTRJEN: derp ima tretjo vožnjo"
    # Isti dokaz, iz katerega je par nastal, zato ne potrditev: samo loči dolgo sled od kratke.
    if dt >= 540 and 0.5 * dt <= dk <= 1.5 * dt:
        return "skladen: sled 9+ min po voznem redu, brez potrditve"
    return "NEPOTRJEN (premika se, drugače od NAP, nihče ne potrdi)"


ozn = collections.Counter()
for n in pari:
    n["o"] = oznaci(n)
    n["pot"] = pot(n) if a.smer and n["vrata"] else ""
    n["obseg"] = any(r.vzrok in OBSEG for r in n["vr"])
    k = ("obseg" if n["obseg"] else "zunaj", n["o"])
    ozn[k + ("parov",)] += 1
    ozn[k + ("vrstic",)] += len(n["vr"])
    ozn[k + ("vrata",)] += len(n["vrata"])

s_parom = sum(r.nasa is not None for r in izbrane)
print(f"{a.dan}: {len(izbrane)} vrstic v oknu, {len({r.voz for r in izbrane})} vozil, {len(pari)} parov, "
      f"{s_parom} vrstic s parom + {len(izbrane) - s_parom} brez para")
if sum(len(n["vr"]) for n in pari) != s_parom or sum(v for k, v in ozn.items() if k[2] == "vrstic") != s_parom:
    raise SystemExit("NAPAKA: oznake se ne seštejejo v vrstice s parom")
print(f"{'':6} {'oznaka':58} {'parov':>6} {'vrstic':>7} {'vrata':>6}")
for k in sorted(k for k in ozn if k[2] == "parov"):
    print(f"{k[0]:6} {k[1]:58} {ozn[k]:6} {ozn[k[:2] + ('vrstic',)]:7} {ozn[k[:2] + ('vrata',)]:6}")

vsi = [n for n in pari if n["obseg"]]
mimo = [n for n in vsi if n["o"].startswith("mimo")]
ocena = [n for n in vsi if n["vrata"] and n not in mimo]
vozil = len({n["voz"] for n in ocena})
slabi = [n for n in ocena if n["o"].startswith("NAROBE")]
nar = [n for n in slabi if len(n["vrata"]) >= MIN_VRSTIC_NAPAKE]
meja = [n for n in slabi if len(n["vrata"]) < MIN_VRSTIC_NAPAKE]
vrata_ods = [n for n in vsi if not n["vrata"] and n["o"].startswith("NAROBE")]
nep = [n for n in ocena if n["o"].startswith("NEPOTRJEN")]
vr_ocena = sum(len(n["vrata"]) for n in ocena)
vr_nep = sum(len(n["vrata"]) for n in nep)
print(f"\nobseg {OBSEG}: {len(vsi)} parov; skozi vrata {len(ocena)} parov, {vozil} vozil; napačnih {len(nar)}, "
      f"meja (< {MIN_VRSTIC_NAPAKE} vrstice) {len(meja)}, nepotrjenih {len(nep)} ({vr_nep} od {vr_ocena} vrstic), "
      f"mimo koledarja {len(mimo)}, napačnih, ki jih vrata odstranijo {len(vrata_ods)}")
kr = collections.Counter()
for r in izbrane:
    if r.vzrok in OBSEG:
        k = r.razlog or "par"
        if k == "vec" and not na_koledarju(r.nap, r.dan) and dvojcki(r.nap, r.dan):
            k = "vec, dvojček NAP-ove na koledarju"
        kr[("premika" if premik(r) >= PREMIK_M else "stoji", k)] += 1
print("obseg, vrstice po izidu:", {f"{x[0]} · {x[1]}": v for x, v in sorted(kr.items())})
vz = collections.Counter()
for voz, t, d in {(r.voz, r.nap, r.dan) for r in izbrane if r.vzrok == "brez_dneva"}:
    x = T.get(t)
    if x is None or x[1] is None:
        vz["vožnje ni ali nagrobnik"] += 1
    elif na_koledarju(t, d):
        vz["koledar ima, okno daleč"] += 1
    else:
        vz["koledar nima, dvojček na koledarju" if dvojcki(t, d) else "koledar nima, brez dvojčka"] += 1
print("brez_dneva, (vozilo, NAP-ova vožnja):", dict(sorted(vz.items())))
print("lege brez vozila na parih v obsegu:", sum(bool(n["brez_vozila"]) for n in vsi))
if a.smer:
    pt = collections.Counter((n["pot"], "NAROBE" if n["o"].startswith("NAROBE") else
                              "NEPOTRJEN" if n["o"].startswith("NEPOTRJEN") else "drugo") for n in ocena)
    print("drugo merilo (pot 15 min), pari skozi vrata po (pot, oznaka):",
          {f"{k[0]} · {k[1]}": v for k, v in sorted(pt.items())})
if ocena:
    print(f"zgornja meja 95 %, če je napačnih 0: {100 * 3 / len(ocena):.1f} % parov")
nar_pot = [n for n in ocena if n.get("pot", "").startswith("NAROBE")]
if nar:
    izid = f"NE: {len(nar)} dokazano napačnih parov v obsegu; preglej vsakega, senca do 7. 11."
elif nar_pot:
    izid = f"NE: {len(nar_pot)} parov napačnih po drugem merilu (pot); preglej vsakega"
elif len(ocena) < MIN_PAROV or vozil < MIN_VOZIL:
    izid = (f"NE DANES: {len(ocena)} parov z {vozil} vozil (rabimo >= {MIN_PAROV} z >= {MIN_VOZIL}); senca do 7. 11., "
            f"nato skupen vzorec {dan_od}..2026-11-07")
elif vr_nep > NAJVEC_NEPOTRJENIH * vr_ocena:
    izid = f"NE DANES: nepotrjenih {vr_nep} od {vr_ocena} vrstic (največ {NAJVEC_NEPOTRJENIH:.0%}); senca do 7. 11."
else:
    izid = "GO: predlog Davidu; priklop z vrati premika in preizkusi, po odobritvi"
print("ODLOČITEV:", izid)


def izpisi(naslov, seznam):
    if not seznam:
        return
    print(f"\n{naslov} ({len(seznam)}):")
    korak = max(1, len(seznam) // max(1, a.seznam))     # enakomerno po dnevu, ne prvih N
    for n in sorted(seznam, key=lambda x: x["vr"][0].ts)[::korak][:a.seznam]:
        v0 = n["vr"][0]
        print(f"  {n['voz']:10} {ura(v0.ts)}-{ura(n['vr'][-1].ts)} {v0.vzrok:12} vrstic {len(n['vr']):3} vrata {len(n['vrata']):3} "
              f"premik {round(n['md']):5} m kraj {round(n['kraj']):+5} s · NAP {oknos(v0.nap)} · naša {oknos(n['nasa'])} · "
              f"derp {v0.derp!r} · {n['o']}{' · ' + n['pot'] if n.get('pot') else ''} · {v0.lat:.5f},{v0.lon:.5f}")


izpisi("NAPAČNI v obsegu", nar)
izpisi("NAPAČNI po drugem merilu (pot)", nar_pot)
izpisi("MEJA v obsegu", meja)
izpisi("NEPOTRJENI v obsegu", nep)
izpisi("MIMO KOLEDARJA v obsegu", mimo)
izpisi("NAROBE, ki jih vrata odstranijo", vrata_ods)
izpisi("NAROBE zunaj obsega", [n for n in pari if not n["obseg"] and n["o"].startswith("NAROBE")])

# Samo simulacija (`dan_sim.py`): oznaka proti znani resnici. Na produkciji te tabele ni.
if conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'sim_resnica'").fetchone():
    res = {(r[0], r[1]): r[2:] for r in conn.execute("SELECT ts, vozilo, kaj, zadnja, nasl FROM sim_resnica")}

    def resnica(r):
        kaj, zad, nasl = res[(r.ts, r.voz)]
        if kaj == "vozi" and r.nasa == zad:
            return "PRAV vozi"
        if kaj == "stoji" and r.nasa == zad:
            return "stoji na koncu"
        if nasl == r.nasa:
            return "stoji, naslednja" if kaj == "stoji" else "vozi prejšnjo, par naslednja"
        return "NAROBE parkira" if kaj == "parkira" else "NAROBE tuja"

    tab, vr = collections.Counter(), collections.Counter()
    for n in pari:
        for r in n["vr"]:
            tab[("obseg" if n["obseg"] else "zunaj", n["o"][:34], resnica(r))] += 1
            vr[(resnica(r), "skozi" if premik(r) >= PREMIK_M else "odpade")] += 1
    print("\nresnica simulacije, vrstice po oznaki:")
    for k, v in sorted(tab.items()):
        print(f"  {k[0]:6} {k[1]:35} {k[2]:30} {v:6}")
    print("vrata:", sorted(vr.items()))
