"""Pot od vrat do vrat: iz točke na zemljevidu do druge točke.

Vse dosedanje iskanje se začne pri **postaji** — potnik mora sam vedeti, s
katere gre. Tu je izhodišče točka, in odgovor je veriga: hoja → vožnja →
(prestop) → vožnja → hoja.

Trije razlogi, zakaj to ni `journey.plan()` z drugim vhodom:

* **Izhodišč je več in vsako ima svoj čas.** Do bližnjega postajališča si čez
  tri minute, do boljšega čez enajst — to ni ista poizvedba z drugim
  parametrom, ampak drugačen začetek.
* **Cilj ni postaja, ampak točka.** Zmaga tisto postajališče, ki ima najmanjšo
  vsoto prihoda in hoje s postaje, ne tisto z najzgodnejšim prihodom.
* **Omrežji sta obe.** Vlak in avtobus v isti verigi; `network` je pri drugih
  straneh delitev prikaza, tu pa bi bila ovira.

**Iskanje teče po voznem redu, ne po napovedi.** Zamude poznamo za vozila, ki
so blizu zdaj; za vožnjo čez pet ur ne obstajajo. Zamude se pripišejo posebej
in veriga se z njimi znova preveri.

Vsi časi v odgovoru so **absolutne sekunde epoch**, ne sekunde od polnoči
prometnega dne. Pot čez polnoč je pri avtobusih vsakdanja (največji `dep_s` v
voznem redu je 121 680, torej 33:48) in relativni čas bi jo pokvaril.
"""

from __future__ import annotations

import math
import sqlite3
import time
from datetime import date, datetime

from . import geo, hoja, journey, stats

TZ = journey.TZ

#: Koliko sme potnik hoditi na vsakem koncu. Izmerjeno, da večji doseg ne
#: podraži iskanja (16 ali 73 izhodišč je enako hitro, ker je cena v
#: premetavanju voznega reda) in da najde boljše poti -- pri Grosupljem 10
#: minut boljši prihod. Minute hoje so zato eno od meril pri izbiri predlogov,
#: ne omejitev iskanja.
MAX_HOJE_S = 25 * 60

#: Štiri noge = trije prestopi, ista meja kot pri `journey.plan()`.
MAX_NOG = 4

#: Koliko kandidatov gre največ v eno matriko hoje. Pri Bavarskem dvoru jih je
#: v polmeru 25 minut 201; matrika 1 x 120 je izmerjeno 81 ms, 1 x 201 pa okoli
#: 130 ms. Meja je tu zato, da najbolj prometno mesto v državi ne postavi cene
#: za vso državo -- odrežejo se najbolj oddaljena, torej najmanj verjetna.
MAX_KANDIDATOV = 120

#: Hoja vso pot je odgovor, kadar je krajša od tega. Nad tem ni več predlog,
#: ampak opomba. Izmerjeno: Ljubljana Polje -> BTC je z avtobusom 64 minut in
#: peš 47 -- brez te primerjave stran pošilja ljudi na počasnejšo pot.
MAX_PES_VSO_POT_S = 60 * 60

#: Kdaj se splača vprašati še "in kaj, če nočem toliko hoditi". Deset minut je
#: meja, pri kateri hoja neha biti postranska: pod njo je vsaka pot podobna.
MANJ_HOJE_S = 10 * 60

#: Koliko pozneje sme priti pot z manj hoje, da je še izbira in ne druga pot.
NAJVEC_POZNEJE_S = 30 * 60

#: Koliko naslednjih odhodov ponudimo poleg prvega. Potnik, ki vpraša "kdaj mi
#: pelje", hoče seznam in ne ene ure -- prvi odhod je lahko čez minuto in ga ne
#: ujame. Vsak je svoje iskanje, a peš matriki sta že izračunani.
NASLEDNJIH = 2

#: Kako daleč naprej sploh gledamo naslednje odhode. Brez te meje bi na progi
#: s tremi vožnjami na dan ponudili odhod čez sedem ur kot "naslednjega".
ISKALNO_OKNO_S = 3 * 3600

_VOZJE_CACHE: dict[tuple, dict] = {}
_ZAMIK_CACHE: dict[tuple, dict] = {}
_IMENA_CACHE: dict[tuple, dict] = {}


def _vozje(conn: sqlite3.Connection, service_date: str) -> dict[str, dict]:
    """`{trip_id: podatki o vožnji}` za ta prometni dan.

    Omrežje rabi že iskanje (prag za prestop je pri vlaku 6 minut in pri
    avtobusu 3), ostalo pa prikaz. Ker je to statika, se prebere enkrat na dan
    in ne enkrat na iskanje: 12 963 voženj je nekaj megabajtov.
    """
    stamp = conn.execute(
        "SELECT value FROM meta WHERE key = 'gtfs_imported_at'").fetchone()
    stamp = stamp["value"] if stamp else None
    kje = conn.execute("PRAGMA database_list").fetchone()["file"]
    kljuc = (kje, service_date, stamp)
    if stamp and kljuc in _VOZJE_CACHE:
        return _VOZJE_CACHE[kljuc]

    out = {r["trip_id"]: dict(r) for r in conn.execute(
        "SELECT t.trip_id, t.train_no, t.headsign, t.mode, t.network, t.agency "
        "FROM trip t JOIN service_day sd ON sd.service_id = t.service_id "
        "WHERE sd.date = ?", (service_date,))}
    if stamp:
        _VOZJE_CACHE.clear()        # en dan naenkrat; te slike so velike
        _VOZJE_CACHE[kljuc] = out
    return out


def _imena(conn: sqlite3.Connection) -> dict[str, tuple]:
    """`{stop_id: (ime, lat, lon)}`. Statika, ki se med uvozi ne spreminja;
    branje vseh 10 509 vrstic ob vsakem predlogu je bilo brez potrebe.

    Koordinate so zraven, ker mora zemljevid pot narisati -- brez njih bi jih
    prikaz iskal z novo zahtevo na postajališče."""
    kje = conn.execute("PRAGMA database_list").fetchone()["file"]
    n = conn.execute("SELECT COUNT(*) FROM station").fetchone()[0]
    kljuc = (kje, n)
    if kljuc not in _IMENA_CACHE:
        _IMENA_CACHE.clear()
        _IMENA_CACHE[kljuc] = {r["stop_id"]: (r["name"], r["lat"], r["lon"])
                               for r in conn.execute(
                                   "SELECT stop_id, name, lat, lon FROM station")}
    return _IMENA_CACHE[kljuc]


def zamiki(conn: sqlite3.Connection, service_date: str,
           now_s: int | None) -> dict[str, int]:
    """`{trip_id: zamuda v sekundah}` za vozila, ki so **zdaj na poti**.

    Iskanje brez tega izbira po voznem redu in zamudo pripiše šele izbrani
    poti — torej lahko izbere pot, ki je po voznem redu tri minute boljša in
    v resnici šest minut slabša. Ujeto v živo 8. 9. 2026: avtobus 25 je imel
    +4 min **že pred izbiro**, vlak LPV 2219 pa je bil boljša pot.

    To je goli **prenos zamude naprej**, ne model: iskanje mora premetati ves
    vozni red in `predict()` na vsako vožnjo je predrago. Za izbiro med potmi
    je dovolj -- prikazane številke gredo tako ali tako skozi `pripni_zamude()`,
    kjer teče pravi model.

    Predpomnjeno na žig zajema (`rt_fetched`), ker je izračun za vseh 13 107
    voženj dneva izmerjeno 541 ms.
    """
    if now_s is None:
        return {}
    zig = conn.execute(
        "SELECT value FROM meta WHERE key = 'rt_fetched'").fetchone()
    zig = zig["value"] if zig else None
    kje = conn.execute("PRAGMA database_list").fetchone()["file"]
    kljuc = (kje, service_date, zig)
    if zig and kljuc in _ZAMIK_CACHE:
        return _ZAMIK_CACHE[kljuc]

    vse = [r[0] for r in conn.execute(
        "SELECT t.trip_id FROM trip t JOIN service_day sd "
        "ON sd.service_id = t.service_id AND sd.date = ?", (service_date,))]
    lm = stats.last_measured(conn, service_date, vse, now_s)
    out = {t: v["delay_s"] for t, v in lm.items() if v.get("delay_s")}
    if zig:
        _ZAMIK_CACHE.clear()
        _ZAMIK_CACHE[kljuc] = out
    return out


def _polnoc(service_date: str) -> int:
    return int(datetime.combine(date.fromisoformat(service_date),
                                datetime.min.time(), tzinfo=TZ).timestamp())


def blizu(conn: sqlite3.Connection, lat: float, lon: float,
          streze: set[str], najvec_s: int = MAX_HOJE_S,
          smer: str = "od") -> tuple[dict[str, int], str]:
    """Postajališča v peš dosegu točke: `{stop_id: sekunde hoje}` in vir.

    Predfilter je **zračni polmer brez faktorja obvoza** (`hoja.doseg_zracno`):
    zračna črta je vedno krajša od prave poti, zato ne izpusti ničesar
    dosegljivega. Pravo mejo postavi šele izmerjena pot.

    `streze` so postajališča, s katerih ta dan sploh kaj pelje. Prihaja iz že
    naloženega voznega reda in ne iz svoje poizvedbe: ista stvar v SQL (JOIN
    čez `sched`) je izmerjeno 629 ms, tu pa je zastonj.
    """
    polmer = hoja.doseg_zracno(najvec_s)
    dlat = polmer / 111_320.0
    dlon = dlat / max(0.2, abs(math.cos(math.radians(lat))))
    kandidati = []
    for stop_id, la, lo in conn.execute("SELECT stop_id, lat, lon FROM station"):
        if stop_id not in streze or la is None:
            continue
        if abs(la - lat) > dlat or abs(lo - lon) > dlon:
            continue
        m = geo.haversine(lat, lon, la, lo)
        if m <= polmer:
            kandidati.append((m, stop_id, la, lo))
    kandidati.sort()
    kandidati = kandidati[:MAX_KANDIDATOV]
    if not kandidati:
        return {}, hoja.OSRM

    sekunde, vir = hoja.matrika(lat, lon, [(k[2], k[3]) for k in kandidati], smer)
    out = {}
    for (_, stop_id, _, _), s in zip(kandidati, sekunde):
        if s is not None and s <= najvec_s:
            out[stop_id] = s
    return out, vir


def _isci_dan(conn, izhodisca: dict[str, int], cilji: dict[str, int],
              service_date: str, odhod_s: int, max_nog: int,
              meja: int | None = None, zamik: dict | None = None,
              brez: set | None = None) -> dict | None:
    """Najzgodnejši prihod na cilj. Časi so sekunde od polnoči prometnega dne.

    Postopek je krog na nogo: iz vsakega doseženega postajališča se vkrcaj na
    vsako vožnjo, ki odpelje dovolj pozno, in sprosti prihode naprej po njej.
    Novo glede na `journey.plan()` je troje -- peš prestopi med postajališči,
    prag za prestop po omrežju vožnje, na katero se vkrcavaš, in obrezovanje.

    **Oznake so po krogih, ne ena sama.** Z eno samo tabelo najboljših prihodov
    `max_nog` ne omeji ničesar: ko poznejši krog izboljša postajališče, se
    prepiše tudi njegov starš in veriga nazaj preskoči kroge. Izmerjeno na
    Maribor -> Koper: pri `max_nog=2` je vrnil pot s štirimi vožnjami. Zato je
    tu `tau[k]` -- najzgodnejši prihod z največ k vožnjami -- kot v RAPTOR.

    `meja` je zgornja meja prihoda na cilj (npr. čas hoje vso pot). Vse, kar je
    za njo, ne more biti odgovor; brez tega obrezovanja zadnja kroga premetavata
    pol države, ki je ne bo nihče videl (izmerjeno 510 ms proti 7 ms).
    """
    by_trip, at_stop = journey._timetable_for_day(conn, service_date, None)
    if not by_trip:
        return None
    vozje = _vozje(conn, service_date)
    noge_pes = hoja.pespoti(conn)
    zamik = zamik or {}
    # `at_stop` je urejen po VOZNOREDNEM odhodu; zamiki to urejenost podrejo.
    # Zgodnji izhod iz zanke zato ne sme gledati voznorednega casa naravnost,
    # ampak ga mora zamakniti za najvecji prezgodnji zamik -- sicer bi izpustil
    # avtobus, ki vozi pred voznim redom (izmerjeno: 10,7 % vrstic).
    naj_prej = max(0, -min(zamik.values(), default=0))
    pragovi = {k: v[0] * 60 for k, v in journey.TRANSFER_LIMITS.items()}

    tau: list[dict[str, int]] = [{} for _ in range(max_nog + 1)]
    starsi: list[dict[str, tuple]] = [{} for _ in range(max_nog + 1)]
    tau[0] = {sid: odhod_s + hoje for sid, hoje in izhodisca.items()}
    najboljsi = dict(tau[0])        # čez vse kroge, samo za obrezovanje
    front = set(tau[0])

    if meja is None:
        meja = 1 << 30
    for sid, pes in cilji.items():
        if sid in najboljsi:
            meja = min(meja, najboljsi[sid] + pes)

    for krog in range(1, max_nog + 1):
        oznaceni: set[str] = set()
        # Vožnje, ki smo jo v tem krogu že prevozili, ni treba znova: iz
        # poznejšega postanka bi sprostila podmnožico istih prihodov ob istih
        # urah. Iz zgodnejšega pa je treba -- tam da več.
        vkrcani: dict[str, int] = {}
        for sid in front:
            prispel = tau[krog - 1][sid]
            if prispel >= meja:
                continue            # tja pridemo pozneje, kot smo že na cilju
            for dep_s, trip_id, seq in at_stop.get(sid, ()):
                if dep_s - naj_prej >= meja:
                    break
                # Vozilo, ki je zdaj na poti, odpelje z znano zamudo. Iskanje
                # mora izbirati po URI, ki bo, ne po tisti v voznem redu.
                if brez and trip_id in brez:
                    continue        # iščemo DRUGO pot, ne iste
                z = zamik.get(trip_id, 0)
                dep_s = dep_s + z
                if dep_s >= meja:
                    continue
                if vkrcani.get(trip_id, 1 << 30) <= seq:
                    continue
                v = vozje.get(trip_id)
                if v is None:
                    continue        # vožnja brez opisa; brez omrežja ne vemo praga
                # Vstop na prvem krogu ni prestop -- rezerva je v hoji do
                # postajališča, ne v pragu.
                gap = 0 if krog == 1 else pragovi.get(v["network"], 180)
                if dep_s < prispel + gap:
                    continue
                vkrcani[trip_id] = seq
                for nseq, nstop, narr, _ in by_trip[trip_id]:
                    if nseq <= seq or narr is None:
                        continue
                    narr = narr + z
                    if narr >= meja:
                        continue
                    if narr >= najboljsi.get(nstop, 1 << 30):
                        continue
                    tau[krog][nstop] = narr
                    starsi[krog][nstop] = (trip_id, sid, seq, nseq)
                    najboljsi[nstop] = narr
                    oznaceni.add(nstop)
                    if nstop in cilji:
                        meja = min(meja, narr + cilji[nstop])
        # Hoja do sosednjega postajališča: "izstopi tu, prehodi 200 m". Hoja ne
        # porabi kroga -- ni vožnja -- zato ostane v istem `tau[krog]`.
        for sid in list(oznaceni):
            for sosed, pes in noge_pes.get(sid, ()):
                kdaj = tau[krog][sid] + pes
                if kdaj >= meja or kdaj >= najboljsi.get(sosed, 1 << 30):
                    continue
                tau[krog][sosed] = kdaj
                starsi[krog][sosed] = (None, sid, 0, 0)
                najboljsi[sosed] = kdaj
                oznaceni.add(sosed)
                if sosed in cilji:
                    meja = min(meja, kdaj + cilji[sosed])
        front = oznaceni
        if not front:
            break

    dosezeni = [(tau[k][sid] + pes, k, sid)
                for sid, pes in cilji.items()
                for k in range(1, max_nog + 1) if sid in tau[k]]
    if not dosezeni:
        return None
    prihod, krog, konec = min(dosezeni)

    # Nazaj do izhodišča. Vožnja porabi krog, hoja ne.
    noge = []
    cur, k = konec, krog
    while k >= 1:
        p = starsi[k].get(cur)
        if p is None:
            k -= 1                  # do sem smo prišli z manj vožnjami
            continue
        trip_id, prej, bseq, aseq = p
        noge.append((trip_id, prej, bseq, cur, aseq))
        cur = prej
        if trip_id is not None:
            k -= 1
        if len(noge) > 2 * max_nog + 2:
            return None             # varovalka pred ciklom, ki ga ne bi smelo biti
    noge.reverse()
    if not noge:
        return None                 # izhodišče je hkrati cilj; to zna hoja sama
    return {"noge": noge, "prvo": cur, "zadnje": konec,
            "prihod_s": prihod, "odhod_s": odhod_s}


def _sestavi(conn, najdba: dict, izhodisca: dict[str, int], cilji: dict[str, int],
             service_date: str, vir_hoje: str) -> dict:
    """Iz surovih nog sestavi predlog, kot ga bere prikaz."""
    polnoc = _polnoc(service_date)
    vozje = _vozje(conn, service_date)
    imena = _imena(conn)

    noge = []
    prvo = najdba["prvo"]
    # Hoja od izhodišča do prvega postajališča.
    def ime(sid):
        return imena[sid][0] if sid in imena else sid

    def ll(sid):
        return [imena[sid][1], imena[sid][2]] if sid in imena else None

    noge.append({"vrsta": "hoja", "sekunde": izhodisca[prvo],
                 "od": None, "do": ime(prvo), "do_stop": prvo, "do_ll": ll(prvo)})

    by_trip = journey._timetable_for_day(conn, service_date, None)[0]
    for trip_id, prej, bseq, cur, aseq in najdba["noge"]:
        if trip_id is None:
            noge.append({"vrsta": "hoja",
                         "sekunde": None,      # dopolni se spodaj iz ur
                         "od": ime(prej), "do": ime(cur),
                         "od_stop": prej, "do_stop": cur,
                         "od_ll": ll(prej), "do_ll": ll(cur)})
            continue
        postanki = {s[0]: s for s in by_trip[trip_id]}
        v = vozje[trip_id]
        noge.append({
            "vrsta": "voznja", "trip_id": trip_id, "train_no": v["train_no"],
            "headsign": v["headsign"], "mode": v["mode"], "network": v["network"],
            "agency": v["agency"],
            "od": ime(prej), "do": ime(cur),
            "od_stop": prej, "do_stop": cur,
            "od_ll": ll(prej), "do_ll": ll(cur),
            "od_seq": bseq, "do_seq": aseq,
            "odhod": polnoc + postanki[bseq][3],
            "prihod": polnoc + postanki[aseq][2],
        })

    # Hoja s zadnjega postajališča na cilj.
    zadnje = najdba["zadnje"]
    noge.append({"vrsta": "hoja", "sekunde": cilji[zadnje],
                 "od": ime(zadnje), "do": None, "od_stop": zadnje,
                 "od_ll": ll(zadnje)})

    # Peš prestopi med vožnjama: čas je razlika med prihodom in odhodom, a
    # samo toliko, kolikor je hoje -- ostalo je čakanje.
    pes_med = hoja.pespoti(conn)
    for i, n in enumerate(noge):
        if n["vrsta"] == "hoja" and n["sekunde"] is None:
            n["sekunde"] = next((s for b, s in pes_med.get(n["od_stop"], ())
                                 if b == n["do_stop"]), 0)

    # Dve hoji zapored sta ena hoja. Nastaneta, kadar pot s postajališča
    # pelje čez peš prestop na drugo in šele od tam do vrat -- vmesno
    # postajališče je za potnika brez pomena, minute pa ne.
    zlite = []
    for n in noge:
        if (n["vrsta"] == "hoja" and zlite and zlite[-1]["vrsta"] == "hoja"):
            zlite[-1]["sekunde"] += n["sekunde"]
            zlite[-1]["do"] = n["do"]
            zlite[-1]["do_stop"] = n.get("do_stop")
            zlite[-1]["do_ll"] = n.get("do_ll")
            continue
        zlite.append(n)
    # Hoja nič minut ni noga, ampak šum: postajališče je pred vrati.
    noge = [n for n in zlite if n["vrsta"] != "hoja" or n["sekunde"] >= 60]

    voznje = [n for n in noge if n["vrsta"] == "voznja"]
    # Zadnja vožnja ni nujno zadnji dogodek: pot se lahko konča s peš prestopom
    # na postajališče, ki nosi ime cilja, in šele za njim s hojo do vrat.
    rep = 0
    for n in reversed(noge):
        if n["vrsta"] == "voznja":
            break
        rep += n["sekunde"]
    zacetna = noge[0]["sekunde"] if noge[0]["vrsta"] == "hoja" else 0
    odhod = voznje[0]["odhod"] - zacetna
    prihod = voznje[-1]["prihod"] + rep
    hoje = sum(n["sekunde"] for n in noge if n["vrsta"] == "hoja")
    return {
        "odhod": odhod, "prihod": prihod,
        "trajanje_s": prihod - odhod,
        "hoje_s": hoje, "prestopov": len(voznje) - 1,
        "vir_hoje": vir_hoje,
        "noge": noge,
    }


def _pes_vso_pot(od: tuple[float, float], do: tuple[float, float],
                 odhod: int) -> dict | None:
    """Hoja od vrat do vrat, kadar je to sploh smiselno.

    Brez tega stran pošilja ljudi na avtobus, ki je počasnejši od njihovih nog:
    Ljubljana Polje -> BTC je z avtobusom 64 minut in peš 47.
    """
    # Zračna črta je spodnja meja poti: če je že ona predolga, usmerjevalnika
    # ni treba vprašati. Brez tega je Maribor -> Koper pomenil izračun
    # dvestokilometrske pešpoti, ki gre takoj v koš.
    if geo.haversine(od[0], od[1], do[0], do[1]) > hoja.doseg_zracno(MAX_PES_VSO_POT_S):
        return None
    sek, vir = hoja.sekunde(od[0], od[1], do[0], do[1])
    if sek is None or sek > MAX_PES_VSO_POT_S:
        return None
    return {"odhod": odhod, "prihod": odhod + sek, "trajanje_s": sek,
            "hoje_s": sek, "prestopov": 0, "vir_hoje": vir,
            "noge": [{"vrsta": "hoja", "sekunde": sek, "od": None, "do": None}]}


def isci(conn: sqlite3.Connection, od: tuple[float, float],
         do: tuple[float, float], service_date: str, odhod_s: int,
         max_hoje_s: int = MAX_HOJE_S, max_nog: int = MAX_NOG,
         now_s: int | None = None) -> dict:
    """Predlogi poti od točke do točke, po voznem redu danega prometnega dne.

    `odhod_s` je sekunda od polnoči tega prometnega dne. Odgovor nosi absolutne
    čase, da se dneva dasta zlepiti brez ugibanja.

    `now_s` obstaja samo za današnji dan -- le takrat je meja med tem, kar je
    vozilo že prevozilo, in tem, kar je pred njim. Brez njega so predlogi po
    voznem redu in brez zamud.
    """
    t0 = time.perf_counter()
    polnoc = _polnoc(service_date)
    # Vozni red se naloži tu in ne šele v iskanju: iz njega pride tudi
    # množica postajališč, ki ta dan sploh kaj strežejo.
    at_stop = journey._timetable_for_day(conn, service_date, None)[1]
    streze = set(at_stop)

    zamik = zamiki(conn, service_date, now_s)
    izhodisca, vir_a = blizu(conn, od[0], od[1], streze, max_hoje_s, "od")
    cilji, vir_b = blizu(conn, do[0], do[1], streze, max_hoje_s, "do")
    vir_hoje = hoja.OSRM if vir_a == vir_b == hoja.OSRM else hoja.ZRAK

    predlogi = []
    pes = _pes_vso_pot(od, do, polnoc + odhod_s)
    if pes:
        predlogi.append(pes)
    # Hoja vso pot je hkrati zgornja meja iskanja: pot, ki pride pozneje, kot
    # bi prišel peš, ni odgovor.
    meja = odhod_s + pes["trajanje_s"] if pes else None

    if izhodisca and cilji:
        najdba = _isci_dan(conn, izhodisca, cilji, service_date, odhod_s,
                           max_nog, meja, zamik)
        if najdba:
            prvi = _sestavi(conn, najdba, izhodisca, cilji, service_date, vir_hoje)
            predlogi.append(prvi)
            # Drugačno vprašanje, ne drugačen izid. Poganjamo ju le, kadar se
            # od prvega sploh moreta razlikovati -- vsak je svoje iskanje.
            zgornja = najdba["prihod_s"]
            if prvi["prestopov"] > 0:
                a = _isci_dan(conn, izhodisca, cilji, service_date, odhod_s,
                              prvi["prestopov"], meja, zamik)
                if a:
                    predlogi.append(_sestavi(conn, a, izhodisca, cilji,
                                             service_date, vir_hoje))
            # Naslednja odhoda. To je poceni: peš matriki sta že izračunani
            # in vsako nadaljnje iskanje je le še krog čez vozni red (7-300 ms
            # z obrezovanjem). Brez tega stran odgovori "ob 13:01" in molči o
            # tem, da naslednji pelje čez deset minut.
            zadnji = prvi
            for _ in range(NASLEDNJIH):
                prva = next((n for n in zadnji["noge"] if n["vrsta"] == "voznja"), None)
                if prva is None:
                    break
                nov_s = prva["odhod"] - polnoc + 60
                if nov_s > odhod_s + ISKALNO_OKNO_S:
                    break
                nova_meja = nov_s + pes["trajanje_s"] if pes else None
                a = _isci_dan(conn, izhodisca, cilji, service_date, nov_s,
                              max_nog, nova_meja, zamik)
                if not a:
                    break
                zadnji = _sestavi(conn, a, izhodisca, cilji, service_date, vir_hoje)
                predlogi.append(zadnji)

            # Druga pot, ne ista ob drugi uri. Kadar avtobus po voznem redu
            # zmaga za tri minute, vlak sploh ne pride na zaslon -- potnik pa
            # ga pozna in ve, da je zanesljivejši. Ujeto v živo 8. 9. 2026:
            # Križanke -> Novo Polje je ponudil štiri avtobusne poti in nobene
            # z vlakom, čeprav je vlak prišel prej.
            uporabljene = {n["trip_id"] for n in prvi["noge"] if n["vrsta"] == "voznja"}
            if uporabljene:
                # Meja je najdeni prihod plus toliko, kolikor sme biti druga
                # pot poznejša -- brez nje to iskanje premeta pol države za
                # predlog, ki ga bo naslednja vrstica tako ali tako zavrgla.
                a = _isci_dan(conn, izhodisca, cilji, service_date, odhod_s,
                              max_nog, najdba["prihod_s"] + NAJVEC_POZNEJE_S,
                              zamik, uporabljene)
                if a:
                    predlogi.append(_sestavi(conn, a, izhodisca, cilji,
                                             service_date, vir_hoje))

            if prvi["hoje_s"] > MANJ_HOJE_S:
                kratka_i = {k: v for k, v in izhodisca.items() if v <= MANJ_HOJE_S}
                kratka_c = {k: v for k, v in cilji.items() if v <= MANJ_HOJE_S}
                if kratka_i and kratka_c:
                    a = _isci_dan(conn, kratka_i, kratka_c, service_date,
                                  odhod_s, max_nog, meja, zamik)
                    # Pot z manj hoje sme biti počasnejša -- to je njen smisel --
                    # a ne poljubno; sicer je to druga pot, ne druga izbira.
                    if a and a["prihod_s"] <= zgornja + NAJVEC_POZNEJE_S:
                        predlogi.append(_sestavi(conn, a, kratka_i, kratka_c,
                                                 service_date, vir_hoje))

    # Zamude PRED razvrščanjem: stran razvršča po uri, ki jo pokaže, ne po
    # voznoredni. Sicer si vrstni red in številke nasprotujeta -- ujeto v živo
    # 8. 9. 2026: avtobus "13:35, pričakovano 13:43" je stal nad vlakom, ki
    # pride ob 13:38. Ista past kot barva, ki pripoveduje drugo zgodbo kot
    # številka poleg nje.
    pripni_zamude(conn, predlogi, service_date, now_s)

    def kdaj(p):
        return p.get("prihod_ocena") or p["prihod"]

    def odhod(p):
        return p.get("odhod_ocena") or p["odhod"]

    # Ista pot se rodi iz dveh vprašanj. Ključ so **samo vožnje**: dve poti z
    # istima avtobusoma sta ista pot, tudi če se hoja na koncu vije čez drugo
    # postajališče in se ure razlikujejo za pol minute. Obdrži se tista z manj
    # hoje, ker je razvrščanje takšno.
    #
    # Za tem pade vse, kar je po VSEH treh merilih slabše od že izbranega.
    # Brez tega je stran ponudila pot, ki odide prej, hodi dvakrat dlje in
    # pride ob isti minuti -- videno na zaslonu 8. 9. 2026 (Grosuplje ->
    # Zmajski most: 12:53 z 20 min hoje poleg 13:01 z 10 min, oba prihod
    # 13:31). Vprašanje "z manj hoje" omejuje hojo na VSAKEM koncu, ne v
    # vsoti, in zna zato dati pot z več hoje skupaj.
    videni, izbrani = set(), []
    for p in sorted(predlogi, key=lambda p: (kdaj(p), p["hoje_s"])):
        kljuc = tuple((n["trip_id"], n["od_seq"], n["do_seq"])
                      for n in p["noge"] if n["vrsta"] == "voznja")
        if kljuc in videni:
            continue
        if any(kdaj(q) <= kdaj(p) and q["hoje_s"] <= p["hoje_s"]
               and q["prestopov"] <= p["prestopov"] and odhod(q) >= odhod(p)
               for q in izbrani):
            continue
        videni.add(kljuc)
        izbrani.append(p)

    return {
        "datum": service_date,
        "izhodisc": len(izhodisca), "ciljev": len(cilji),
        "vir_hoje": vir_hoje,
        "predlogi": izbrani,
        "trajalo_ms": round((time.perf_counter() - t0) * 1000),
    }


# ---------------------------------------------------------------- zamude

def _feed_zamude(conn, pari: list[tuple[str, int]], service_date: str) -> dict:
    """Kaj feed pravi o teh postankih. `COALESCE(delay_dep, delay_arr)`, ker je
    `departure.delay` izpolnjen pri vseh prevoznikih, `arrival.delay` pa ne."""
    if not pari:
        return {}
    marks = ",".join("(?,?)" for _ in pari)
    par: list = []
    for t, q in pari:
        par += [t, q]
    vrstice = conn.execute(
        "SELECT trip_id, stop_seq, COALESCE(delay_dep, delay_arr) AS d FROM run "
        f"WHERE service_date = ? AND (trip_id, stop_seq) IN ({marks})",
        [service_date, *par]).fetchall()
    return {(r["trip_id"], r["stop_seq"]): r["d"] for r in vrstice}


def pripni_zamude(conn: sqlite3.Connection, predlogi: list[dict],
                  service_date: str, now_s: int | None) -> None:
    """Vsaki vožnji pripiše zamudo ob vstopu in oceno ob izstopu.

    **Iskanje teče po voznem redu**, ker napovedi za vožnjo čez pet ur ni.
    Zamuda se pripiše šele tu in veriga se z njo znova prebere: če prva noga
    zamuja osem minut in je prestop imel šest, mora to potnik videti.

    Pravilo, katera številka velja in od kod je, je `stats.zamuda_na_postanku()`
    — **isto, ki ga uporablja iskalnik zvez**. Druga različica bi se prej ali
    slej razšla in razlika bi bila tiha.
    """
    noge = [n for p in predlogi for n in p["noge"] if n["vrsta"] == "voznja"]
    if not noge:
        return
    trip_ids = list({n["trip_id"] for n in noge})
    lm = stats.last_measured(conn, service_date, trip_ids, now_s)
    slack = stats._slack_ahead(conn, trip_ids)
    feed = _feed_zamude(conn, [(n["trip_id"], n["od_seq"]) for n in noge],
                        service_date)

    for n in noge:
        tid = n["trip_id"]
        z = stats.zamuda_na_postanku(
            conn, train_no=n["train_no"], trip_id=tid, stop_seq=n["od_seq"],
            ime_postaje=n["od"], feed_delay_s=feed.get((tid, n["od_seq"])),
            lm=lm.get(tid), slack_vrsta=slack.get(tid, ()),
            service_date=service_date)
        n["zamuda"] = stats.opis_zamude(z["delay_s"], z["delay_kind"])
        n["zamuda_od"] = z["delay_at"]
        if z["delay_s"] is None:
            n["odhod_ocena"] = n["prihod_ocena"] = None
            continue
        n["odhod_ocena"] = n["odhod"] + z["delay_s"]
        # Zamuda ob izstopu ni ista kot ob vstopu: vlak vmes porabi rezervo
        # voznega reda. Isti model kot v oknu vožnje.
        ob_izstopu = stats.estimate_at(conn, n["train_no"], tid, n["od_seq"],
                                       z["delay_s"], n["do_seq"], service_date)
        if ob_izstopu is None:
            ob_izstopu = z["delay_s"]
        n["prihod_ocena"] = n["prihod"] + ob_izstopu

    for p in predlogi:
        voznje = [n for n in p["noge"] if n["vrsta"] == "voznja"]
        if not voznje:
            continue
        # Kdaj moraš zares od doma: če prvi avtobus zamuja pet minut, imaš pet
        # minut več. To je edini razlog, zakaj ta stran obstaja.
        prva = voznje[0]
        zac = p["noge"][0]["sekunde"] if p["noge"][0]["vrsta"] == "hoja" else 0
        p["odhod_ocena"] = prva["odhod_ocena"] - zac if prva["odhod_ocena"] else None
        rep = 0
        for n in reversed(p["noge"]):
            if n["vrsta"] == "voznja":
                break
            rep += n["sekunde"]
        zadnja = voznje[-1]
        p["prihod_ocena"] = zadnja["prihod_ocena"] + rep if zadnja["prihod_ocena"] else None

        # Ali prestopi še držijo. Načrtovani čas je razlika voznega reda; kar
        # od njega ostane, je razlika **pričakovanih** ur minus hoja vmes.
        p["prestopi"] = []
        for a, b in zip(voznje, voznje[1:]):
            i, j = p["noge"].index(a), p["noge"].index(b)
            pes = sum(n["sekunde"] for n in p["noge"][i + 1:j] if n["vrsta"] == "hoja")
            nacrtovano = b["odhod"] - a["prihod"] - pes
            ostane = None
            if a["prihod_ocena"] is not None and b["odhod_ocena"] is not None:
                ostane = b["odhod_ocena"] - a["prihod_ocena"] - pes
            p["prestopi"].append({
                "kje": a["do"], "pes_s": pes,
                "nacrtovano_s": nacrtovano, "ostane_s": ostane,
            })
