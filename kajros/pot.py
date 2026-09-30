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

import bisect
import math
import sqlite3
import time
from datetime import date, timedelta

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

#: Do kod iščemo kandidate ne glede na nastavljeno mejo. To je največ, kar
#: polje na strani dovoli (45 min); vse čez mejo se **zavrže**, obdrži se le
#: podatek, kako daleč je prvo. Brez tega odgovora "koliko hoje bi bilo treba"
#: ni mogoče dati: postajališče tik čez mejo prefilter sploh ne izmeri.
NASVET_MEJA_S = 45 * 60

#: Koliko kandidatov gre največ v eno matriko hoje. Pri Bavarskem dvoru jih je
#: v polmeru 25 minut 201; matrika 1 x 120 je izmerjeno 81 ms, 1 x 201 pa okoli
#: 130 ms. Meja je tu zato, da najbolj prometno mesto v državi ne postavi cene
#: za vso državo -- odrežejo se najbolj oddaljena, torej najmanj verjetna.
MAX_KANDIDATOV = 120

#: S kolesom je doseg trikrat daljši in ploščina devetkrat večja: pri Bavarskem
#: dvoru je v 25 minutah vožnje 760 postajališč, ki jih meja 120 odreže pri
#: 1,3 km -- torej prav tam, kjer bi kolo začelo pomagati (izmerjeno 23. 9.
#: 2026). Zato se pri kolesu meri **eno postajališče na ime** (vsa istega imena
#: v `ISTO_IME_M` dobijo njegov čas in razliko po zraku): 340 imen namesto 760
#: postajališč, in meja je 300 imen. Matrika 1 x 300 je na razvojnem stroju
#: 71 ms, 1 x 600 pa 202 ms; arwen je okoli trikrat počasnejši.
MAX_KANDIDATOV_KOLO = 300
ISTO_IME_M = 200

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
#:
#: Tri in ne dva, izmerjeno 23. 9. 2026 na 60 vprašanjih po Ljubljani: odkar
#: naslednji odhod res pomeni naslednjega (glej `_voznje_dneva`), ga pri
#: konvergentnih zvezah pogosteje povozi boljši predlog z istim prihodom, in
#: seznam se je skrčil s povprečno 1,55 na 1,30 predloga z vozilom. S tremi
#: je 1,67 (različnih prihodov 1,57 proti prejšnjim 1,52), mediana iskanja
#: pa 136 ms proti 125.
NASLEDNJIH = 3

#: Največji zamik, ki ga iskanje sploh upošteva. Nad tem ni zamuda, ampak
#: feedova zamenjava prometnega dne -- isti razlog kot `api.MAX_LIVE_DELAY_S`.
#: Meja hkrati dovoli preskočiti odhode pred potnikovim prihodom: vožnja z
#: zamudo lahko odpelje pozneje, kot piše v voznem redu, a ne poljubno pozneje.
MAX_ZAMIK_S = 60 * 60

#: Kako daleč naprej sploh gledamo naslednje odhode. Brez te meje bi na progi
#: s tremi vožnjami na dan ponudili odhod čez sedem ur kot "naslednjega".
ISKALNO_OKNO_S = 3 * 3600

#: Do katere ure se išče tudi po VČERAJŠNJEM prometnem dnevu. Nočni avtobus ob
#: 01:00 nosi včerajšnji datum in `dep_s` čez 86 400 (največji v voznem redu
#: je 121 680, torej 33:48); brez drugega iskanja ga vprašanje ob pol enih ne
#: najde, čeprav vozi. Drugo iskanje je cel krog čez vozni red, zato ne ves
#: dopoldan -- do štirih, kot je bilo to prej v `api.py`.
NOCNI_S = 4 * 3600

_VOZJE_CACHE: dict[tuple, dict] = {}
_ZAMIK_CACHE: dict[tuple, dict] = {}
_IMENA_CACHE: dict[tuple, dict] = {}

#: Koliko prometnih dni hranijo predpomnilniki spodaj. Dva, ker nočno
#: vprašanje bere danes IN včeraj: z enim samim mestom je vsako tako iskanje
#: drugemu izpraznilo predpomnilnik in `zamiki()` (~0,8 s) se je računal
#: dvakrat na zahtevo.
_DNI_V_PREDPOMNILNIKU = 2


def _shrani(cache: dict, kljuc, vrednost, mest: int = _DNI_V_PREDPOMNILNIKU):
    """Shrani v predpomnilnik z `mest` mesti; najstarejše gre prvo ven.

    Brez `cache.clear()`: zahteve tečejo v več nitih, in `kljuc in cache`
    ter `cache[kljuc]` v drugi niti med njima nista atomarna -- vmesno
    praznjenje je bil KeyError. Bralci zato jemljejo z `cache.get()`.
    """
    if kljuc not in cache:
        for star in list(cache)[:max(0, len(cache) - mest + 1)]:
            cache.pop(star, None)
    cache[kljuc] = vrednost
    return vrednost


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
    if stamp and (v := _VOZJE_CACHE.get(kljuc)) is not None:
        return v

    out = {r["trip_id"]: dict(r) for r in conn.execute(
        "SELECT t.trip_id, t.train_no, t.headsign, t.mode, t.network, t.agency "
        "FROM trip t JOIN service_day sd ON sd.service_id = t.service_id "
        "WHERE sd.date = ?", (service_date,))}
    if stamp:
        _shrani(_VOZJE_CACHE, kljuc, out)
    return out


def _imena(conn: sqlite3.Connection) -> dict[str, tuple]:
    """`{stop_id: (ime, lat, lon)}`. Statika, ki se med uvozi ne spreminja;
    branje vseh 10 509 vrstic ob vsakem predlogu je bilo brez potrebe.

    Koordinate so zraven, ker mora zemljevid pot narisati -- brez njih bi jih
    prikaz iskal z novo zahtevo na postajališče."""
    kje = conn.execute("PRAGMA database_list").fetchone()["file"]
    n = conn.execute("SELECT COUNT(*) FROM station").fetchone()[0]
    kljuc = (kje, n)
    if (v := _IMENA_CACHE.get(kljuc)) is not None:
        return v
    return _shrani(_IMENA_CACHE, kljuc,
                   {r["stop_id"]: (r["name"], r["lat"], r["lon"])
                    for r in conn.execute("SELECT stop_id, name, lat, lon FROM station")},
                   mest=1)


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
    if zig and (v := _ZAMIK_CACHE.get(kljuc)) is not None:
        return v

    vse = [r[0] for r in conn.execute(
        "SELECT t.trip_id FROM trip t JOIN service_day sd "
        "ON sd.service_id = t.service_id AND sd.date = ?", (service_date,))]
    lm = stats.last_measured(conn, service_date, vse, now_s)
    out = {t: max(-MAX_ZAMIK_S, min(MAX_ZAMIK_S, v["delay_s"]))
           for t, v in lm.items() if v.get("delay_s")}
    if zig:
        _shrani(_ZAMIK_CACHE, kljuc, out)
    return out


def blizu(conn: sqlite3.Connection, lat: float, lon: float,
          streze: set[str], najvec_s: int = MAX_HOJE_S,
          smer: str = "od",
          kmh: float = hoja.KMH) -> tuple[dict[str, int], str, int | None]:
    """Postajališča v peš dosegu točke: `{stop_id: sekunde hoje}`, vir in
    koliko hoje bi bilo treba do **prvega postajališča čez mejo**.

    Zadnje je za odgovor, kadar ni poti: "z 32 minutami hoje bi bilo v dosegu
    tudi postajališče" je uporabno, "ni poti" ni.

    Predfilter je **zračni polmer brez faktorja obvoza** (`hoja.doseg_zracno`):
    zračna črta je vedno krajša od prave poti, zato ne izpusti ničesar
    dosegljivega. Pravo mejo postavi šele izmerjena pot.

    `streze` so postajališča, s katerih ta dan sploh kaj pelje. Prihaja iz že
    naloženega voznega reda in ne iz svoje poizvedbe: ista stvar v SQL (JOIN
    čez `sched`) je izmerjeno 629 ms, tu pa je zastonj.
    """
    polmer = hoja.doseg_zracno(max(najvec_s, NASVET_MEJA_S), kmh)
    dlat = polmer / 111_320.0
    dlon = dlat / max(0.2, abs(math.cos(math.radians(lat))))
    kandidati = []
    for stop_id, ime, la, lo in conn.execute("SELECT stop_id, name, lat, lon FROM station"):
        if stop_id not in streze or la is None:
            continue
        if abs(la - lat) > dlat or abs(lo - lon) > dlon:
            continue
        m = geo.haversine(lat, lon, la, lo)
        if m <= polmer:
            kandidati.append((m, stop_id, la, lo, ime))
    kandidati.sort()

    # Kdo se meri in kdo dobi čas po sosedu istega imena. Peš se meri vsako
    # postajališče posebej -- stran ceste je tam minuta hoje.
    clani: dict[str, list[tuple[str, int]]] = {}
    if kmh == hoja.KMH:
        merjeni = kandidati[:MAX_KANDIDATOV]
    else:
        merjeni = []
        po_imenu: dict[str, list[tuple]] = {}
        for k in kandidati:
            _, sid, la, lo, ime = k
            rep = next((r for r in po_imenu.get(ime, ())
                        if geo.haversine(r[2], r[3], la, lo) <= ISTO_IME_M), None)
            if rep is not None:
                razlika = round(geo.haversine(rep[2], rep[3], la, lo) * 3.6 / kmh)
                clani[rep[1]].append((sid, razlika))
            elif len(merjeni) < MAX_KANDIDATOV_KOLO:
                merjeni.append(k)
                po_imenu.setdefault(ime, []).append(k)
                clani[sid] = []
    if not merjeni:
        return {}, hoja.OSRM, None

    sekunde, vir = hoja.matrika(lat, lon, [(k[2], k[3]) for k in merjeni], smer)
    out = {}
    cez_mejo = None
    for k, s in zip(merjeni, sekunde):
        s = hoja.pri_hitrosti(s, kmh)
        if s is None:
            continue
        for stop_id, dodatek in [(k[1], 0), *clani.get(k[1], ())]:
            if s + dodatek <= najvec_s:
                out[stop_id] = s + dodatek
            elif cez_mejo is None or s + dodatek < cez_mejo:
                cez_mejo = s + dodatek
    return out, vir, cez_mejo


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
            odhodi = at_stop.get(sid, ())
            # Preskoči vse, kar je odpeljalo, preden smo prišli. Vožnja z
            # zamudo lahko odpelje pozneje od voznega reda, a največ za
            # `MAX_ZAMIK_S` -- toliko nazaj torej pogledamo in nič dlje.
            # Brez tega se na prometnem postajališču prehodijo vsi dnevni
            # odhodi za vsako postajališče v čelu iskanja.
            od = bisect.bisect_left(odhodi, (prispel - MAX_ZAMIK_S,))
            for dep_s, trip_id, seq in odhodi[od:]:
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


# ---------------------------------------------------------------- obratno iskanje

_PRIHODI_CACHE: dict[tuple, dict] = {}
_PES_NAZAJ: list = [None, None]         # (slika naprej, slika nazaj)


def _prihodi(conn: sqlite3.Connection, service_date: str) -> dict[str, list]:
    """`{stop_id: [(prihod_s, trip_id, stop_seq)]}`, urejeno po prihodu.

    Zrcalo `at_stop` iz `journey._timetable_for_day()`: obratno iskanje ne
    sprašuje "kaj odpelje od tu po tej uri", ampak "kaj pripelje sem pred to
    uro". Prvi postanek vožnje ni prihod -- tam nihče ne izstopi.
    """
    stamp = conn.execute(
        "SELECT value FROM meta WHERE key = 'gtfs_imported_at'").fetchone()
    stamp = stamp["value"] if stamp else None
    kje = conn.execute("PRAGMA database_list").fetchone()["file"]
    kljuc = (kje, service_date, stamp)
    if stamp and (v := _PRIHODI_CACHE.get(kljuc)) is not None:
        return v
    by_trip = journey._timetable_for_day(conn, service_date, None)[0]
    out: dict[str, list] = {}
    for trip_id, postanki in by_trip.items():
        for seq, stop_id, arr, _ in postanki[1:]:
            if arr is not None:
                out.setdefault(stop_id, []).append((arr, trip_id, seq))
    for v in out.values():
        v.sort()
    if stamp:
        _shrani(_PRIHODI_CACHE, kljuc, out)
    return out


def _pespoti_nazaj(conn) -> dict[str, list[tuple[str, int]]]:
    """`{b: [(a, sekunde a -> b)]}`: kdo pride peš DO tega postajališča.

    `pespot` je shranjen od izhodišča naprej; obratno iskanje ga bere z druge
    strani. Obe smeri sta izmerjeni posebej, ker peš pot ni nujno simetrična.
    """
    naprej = hoja.pespoti(conn)
    if _PES_NAZAJ[0] is not naprej:
        nazaj: dict[str, list[tuple[str, int]]] = {}
        for a, sosedje in naprej.items():
            for b, s in sosedje:
                nazaj.setdefault(b, []).append((a, s))
        _PES_NAZAJ[:] = [naprej, nazaj]
    return _PES_NAZAJ[1]


def _isci_nazaj(conn, izhodisca: dict[str, int], cilji: dict[str, int],
                service_date: str, prihod_s: int, max_nog: int,
                meja: int | None = None, zamik: dict | None = None,
                brez: set | None = None) -> dict | None:
    """Najpoznejši odhod z izhodišča, s katerim si na cilju do `prihod_s`.

    Isti postopek kot `_isci_dan()`, obrnjen v času: začne se pri cilju z uro,
    do katere moraš biti tam, in se po krogih širi nazaj -- katera vožnja
    pripelje sem dovolj zgodaj, in kdaj moraš biti na njenem vstopnem
    postajališču. Odgovor je "od doma najpozneje ob", kar je vprašanje človeka,
    ki mora biti v službi ob osmih.

    **Oznaki sta dve na postajališče, ne ena.** Prag za prestop (vlak 6 min,
    avtobus 3) velja samo, kadar na postajališče pripelješ z vozilom; kdor
    pride peš od doma, ga ne rabi -- enako kot v iskanju naprej, kjer prvi krog
    praga nima. `pes[k]` je zato "do kdaj moraš biti tu peš", `voz[k]` pa "do
    kdaj moraš sem pripeljati", že zmanjšano za prag vožnje, na katero se tu
    vkrcaš.

    `meja` je spodnja meja odhoda: vse, kar odide prej, ni odgovor (hoja vso
    pot je hitrejša ali je odhod že mimo). Brez nje zadnja kroga premetavata
    ves dan nazaj.
    """
    by_trip, _ = journey._timetable_for_day(conn, service_date, None)
    if not by_trip:
        return None
    prihodi = _prihodi(conn, service_date)
    vozje = _vozje(conn, service_date)
    k_pesu = _pespoti_nazaj(conn)
    zamik = zamik or {}
    # Voznoredna ura prihoda ni prava: vozilo z zamudo pripelje pozneje, tisto
    # pred voznim redom prej. Iskanje po urejenem seznamu mora zato pogledati
    # toliko čez, kolikor je največji prezgodnji zamik, in odnehati toliko
    # prej, kolikor je največja zamuda -- ista past kot v `_isci_dan()`.
    naj_prej = max(0, -min(zamik.values(), default=0))
    naj_kasneje = max(0, max(zamik.values(), default=0))
    pragovi = {k: v[0] * 60 for k, v in journey.TRANSFER_LIMITS.items()}

    nic = -(1 << 30)
    if meja is None:
        meja = nic
    # `meja` med iskanjem raste (najboljši že najdeni odhod) in reže vožnje po
    # uri na postajališču. Za odgovor šteje odhod OD DOMA, ki je zaradi hoje
    # prej -- vozilo po zdaj s postajališča 13 minut stran je odhod pred zdaj.
    spodnja = meja
    voz: list[dict[str, int]] = [{} for _ in range(max_nog + 1)]
    pes: list[dict[str, int]] = [{} for _ in range(max_nog + 1)]
    starsi_voz: list[dict[str, tuple]] = [{} for _ in range(max_nog + 1)]
    starsi_pes: list[dict[str, tuple]] = [{} for _ in range(max_nog + 1)]
    voz[0] = {sid: prihod_s - h for sid, h in cilji.items()}
    naj_voz = dict(voz[0])
    naj_pes: dict[str, int] = {}
    front = set(voz[0])

    for krog in range(1, max_nog + 1):
        oznaceni: set[str] = set()
        # Vožnje, ki smo jo v tem krogu že prebrali od poznejšega izstopa, ni
        # treba znova od zgodnejšega: vstopna postajališča in ure so ista.
        izstopi: dict[str, int] = {}
        for sid in front:
            rok = voz[krog - 1][sid]
            if rok <= meja:
                continue            # vse od tu odide prej, kot že znamo oditi
            vrsta = prihodi.get(sid, ())
            i = bisect.bisect_right(vrsta, (rok + naj_prej + 1,))
            while i > 0:
                i -= 1
                arr_s, trip_id, seq = vrsta[i]
                if arr_s + naj_kasneje <= meja:
                    break
                if brez and trip_id in brez:
                    continue        # iščemo DRUGO pot, ne iste
                z = zamik.get(trip_id, 0)
                if arr_s + z > rok:
                    continue
                if izstopi.get(trip_id, -1) >= seq:
                    continue
                v = vozje.get(trip_id)
                if v is None:
                    continue        # vožnja brez opisa; brez omrežja ne vemo praga
                izstopi[trip_id] = seq
                prag = pragovi.get(v["network"], 180)
                for bseq, bstop, _, bdep in by_trip[trip_id]:
                    if bseq >= seq:
                        break
                    if bdep is None:
                        continue
                    d = bdep + z
                    if d <= meja:
                        continue
                    if d > naj_pes.get(bstop, nic):
                        pes[krog][bstop] = d
                        starsi_pes[krog][bstop] = (trip_id, bseq, sid, seq)
                        naj_pes[bstop] = d
                        if bstop in izhodisca:
                            meja = max(meja, d - izhodisca[bstop])
                    if d - prag > meja and d - prag > naj_voz.get(bstop, nic):
                        voz[krog][bstop] = d - prag
                        starsi_voz[krog][bstop] = (trip_id, bseq, sid, seq)
                        naj_voz[bstop] = d - prag
                        oznaceni.add(bstop)
        # Peš prestop: "izstopi tam, prehodi 200 m sem". Hoja ne porabi kroga.
        for sid in list(oznaceni):
            for sosed, s in k_pesu.get(sid, ()):
                kdaj = voz[krog][sid] - s
                if kdaj <= meja or kdaj <= naj_voz.get(sosed, nic):
                    continue
                voz[krog][sosed] = kdaj
                starsi_voz[krog][sosed] = (None, 0, sid, 0)
                naj_voz[sosed] = kdaj
                oznaceni.add(sosed)
        front = oznaceni
        if not front:
            break

    # Najpoznejši odhod od doma; ob enakem tisti z manj vožnjami.
    dosezeni = [(pes[k][sid] - h, -k, sid)
                for sid, h in izhodisca.items()
                for k in range(1, max_nog + 1)
                if sid in pes[k] and pes[k][sid] - h > spodnja]
    if not dosezeni:
        return None
    odhod, minus_k, zacetek = max(dosezeni)
    krog = -minus_k

    # Naprej do cilja. Vožnja porabi krog, hoja ne.
    trip_id, bseq, cur, aseq = starsi_pes[krog][zacetek]
    noge = [(trip_id, zacetek, bseq, cur, aseq)]
    k = krog - 1
    while k >= 1:
        p = starsi_voz[k].get(cur)
        if p is None or len(noge) > 2 * max_nog + 2:
            return None             # varovalka; do sem se ne bi smelo priti
        trip_id, bseq, nasl, aseq = p
        noge.append((trip_id, cur, bseq, nasl, aseq))
        cur = nasl
        if trip_id is not None:
            k -= 1
    if cur not in cilji:
        return None
    zadnja = next(n for n in reversed(noge) if n[0] is not None)
    prihod = next(s[2] for s in by_trip[zadnja[0]] if s[0] == zadnja[4])
    prihod += zamik.get(zadnja[0], 0) + cilji[cur]
    return {"noge": noge, "prvo": zacetek, "zadnje": cur,
            "prihod_s": prihod, "odhod_s": odhod}


# ---------------------------------------------------------------- zategovanje
#
# Iskanje v eno smer se na vsako vožnjo vkrca, brž ko jo ujame. Naprej zato od
# doma odide ob prvi priložnosti in razliko prečaka na prestopu; nazaj izbere
# zadnjo vožnjo, ki še ujame rok, in prav tako čaka vmes. Prihod oziroma odhod
# je pravi, pot med njima pa ne. Obratno iskanje od najdene ure z enakim
# številom voženj vrne isto uro in najkrajšo pot do nje.
#
# Sporočilo potnika 30. 9. 2026 ("uro za prestope"), izmerjeno na 120 naključnih
# parih po državi: pri "čim prej" je lahko prvi predlog ob istem prihodu odšel
# vsaj 20 minut pozneje v 15 primerih (8 vsaj 45 minut, največ 195), pri "biti
# tam do" je lahko ob istem odhodu prišel vsaj 20 minut prej v 25 (14 vsaj 45).

#: Koliko poznejšega odhoda od doma odtehta en prestop več. Pri "čim prej" z
#: istim prihodom: 05:44 z dvema prestopoma ali 11:43 s tremi (izmerjeno
#: 30. 9. 2026, 1280 vprašanj: v 39 je prvi predlog odšel prej od drugega z
#: isto uro prihoda, do 6 ur). Deset minut: prestop je tveganje in hoja, ni pa
#: vreden pol ure čakanja.
PRESTOP_VREDEN_S = 10 * 60


def _stevilo_vozenj(najdba: dict) -> int:
    return sum(1 for n in najdba["noge"] if n[0] is not None)


def _naprej(conn, izhodisca: dict[str, int], cilji: dict[str, int],
            service_date: str, odhod_s: int, max_nog: int,
            meja: int | None = None, zamik: dict | None = None,
            brez: set | None = None, vec_vozenj: bool = False) -> dict | None:
    """Najzgodnejši prihod, in od poti s tem prihodom tista, ki odide zadnja."""
    najdba = _isci_dan(conn, izhodisca, cilji, service_date, odhod_s, max_nog,
                       meja, zamik, brez)
    if najdba is None:
        return None
    k = _stevilo_vozenj(najdba)
    zadnja = _isci_nazaj(conn, izhodisca, cilji, service_date, najdba["prihod_s"],
                         k, odhod_s - 1, zamik, brez)
    # Z vožnjo več se od doma včasih odide ure pozneje in pride ob isti minuti.
    # Iskanje z enakim številom voženj tega ne vidi; prestop več se splača le,
    # kadar prinese vsaj PRESTOP_VREDEN_S doma na vsako dodatno vožnjo. Samo
    # za prvi predlog (`vec_vozenj`): ostala iskanja so zato, da pokažejo
    # drugo izbiro, in razvrstitev v `isci()` jih ob isti uri uredi sama.
    if vec_vozenj and k < max_nog:
        vec = _isci_nazaj(conn, izhodisca, cilji, service_date, najdba["prihod_s"],
                          max_nog, odhod_s - 1, zamik, brez)
        if vec and (zadnja is None or vec["odhod_s"] >= zadnja["odhod_s"]
                    + PRESTOP_VREDEN_S * (_stevilo_vozenj(vec) - k)):
            zadnja = vec
    return zadnja or najdba


def _nazaj(conn, izhodisca: dict[str, int], cilji: dict[str, int],
           service_date: str, prihod_s: int, max_nog: int,
           meja: int | None = None, zamik: dict | None = None,
           brez: set | None = None) -> dict | None:
    """Najpoznejši odhod, in od poti s tem odhodom tista, ki pride prva."""
    najdba = _isci_nazaj(conn, izhodisca, cilji, service_date, prihod_s, max_nog,
                         meja, zamik, brez)
    if najdba is None:
        return None
    prva = _isci_dan(conn, izhodisca, cilji, service_date, najdba["odhod_s"],
                     _stevilo_vozenj(najdba), najdba["prihod_s"] + 1, zamik, brez)
    return prva or najdba


def _sestavi(conn, najdba: dict, izhodisca: dict[str, int], cilji: dict[str, int],
             service_date: str, vir_hoje: str) -> dict:
    """Iz surovih nog sestavi predlog, kot ga bere prikaz."""
    polnoc = stats.polnoc(service_date)
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
        # Prometni dan voženj v predlogu. Ni nujno dan vprašanja: ponoči je
        # nočni avtobus včerajšnji, in podrobnosti ga morajo iskati tam --
        # z današnjim dnem so kazale jutrišnjo vožnjo ob isti uri.
        "datum": service_date,
        "odhod": odhod, "prihod": prihod,
        "trajanje_s": prihod - odhod,
        "hoje_s": hoje, "prestopov": len(voznje) - 1,
        "vir_hoje": vir_hoje,
        "noge": noge,
    }


#: Do kod sploh vprašamo, koliko traja hoja vso pot. To ni meja predloga
#: (ta je `MAX_PES_VSO_POT_S`), ampak meja **primerjave**: pot z vozilom, ki je
#: slabša od hoje, ni predlog, in brez te številke tega ni mogoče vedeti.
#: Nad tremi urami hoje primerjava nima več pomena, izračun 200-kilometrske
#: pešpoti pa stane.
MAX_PES_PRIMERJAVA_S = 3 * 3600


def _pes_vso_pot(od: tuple[float, float], do: tuple[float, float],
                 kmh: float = hoja.KMH) -> tuple[int | None, str]:
    """Koliko traja pot od vrat do vrat brez vozila, in vir številke.

    Trajanje se vrne **tudi takrat, ko predloga iz njega ne bo** — hoja treh
    ur ni pot, ki bi jo kdo ponudil, je pa merilo: kar je počasnejše od nje,
    ni predlog. Brez tega stran pošilja ljudi na avtobus, ki je počasnejši od
    njihovih nog: Ljubljana Polje -> BTC je z avtobusom 64 minut in peš 47.
    """
    # Zračna črta je spodnja meja poti: če je že ona predolga, usmerjevalnika
    # ni treba vprašati. Brez tega je Maribor -> Koper pomenil izračun
    # dvestokilometrske pešpoti, ki gre takoj v koš.
    if geo.haversine(od[0], od[1], do[0], do[1]) > hoja.doseg_zracno(
            MAX_PES_PRIMERJAVA_S, kmh):
        return None, hoja.OSRM
    sek, vir = hoja.sekunde(od[0], od[1], do[0], do[1])
    return hoja.pri_hitrosti(sek, kmh), vir


def _pes_predlog(datum: str, odhod: int, sek: int, vir: str, **dodatno) -> dict:
    """Pot brez vozila kot predlog. `odhod` je absoluten čas."""
    return {"datum": datum, "odhod": odhod, "prihod": odhod + sek, "trajanje_s": sek,
            "hoje_s": sek, "prestopov": 0, "vir_hoje": vir, **dodatno,
            "noge": [{"vrsta": "hoja", "sekunde": sek, "od": None, "do": None}]}


def _vceraj(service_date: str) -> str:
    return (date.fromisoformat(service_date) - timedelta(days=1)).isoformat()


def _voznje_dneva(conn: sqlite3.Connection, izhodisca: dict[str, int],
                  cilji: dict[str, int], service_date: str, odhod_s: int | None,
                  prihod_do_s: int | None, now_s: int | None, max_nog: int,
                  pes_s: int | None, ponudi_pes: bool, vir_hoje: str) -> list[dict]:
    """Predlogi z vozilom po voznem redu ENEGA prometnega dne, z zamudami.

    Vhodni časi so sekunde od polnoči tega dne, časi v predlogih pa absolutni,
    zato se predlogi dveh dni dajo zložiti v en seznam. Pomen `odhod_s` in
    `prihod_do_s` je isti kot pri `isci()`.
    """
    polnoc = stats.polnoc(service_date)
    zamik = zamiki(conn, service_date, now_s)

    def sestavi(najdba, izh=izhodisca, cil=cilji):
        return _sestavi(conn, najdba, izh, cil, service_date, vir_hoje)

    def kratka():
        """Izhodišča in cilji z malo hoje: za vprašanje "z manj hoje"."""
        return ({k: v for k, v in izhodisca.items() if v <= MANJ_HOJE_S},
                {k: v for k, v in cilji.items() if v <= MANJ_HOJE_S})

    predlogi: list[dict] = []
    if prihod_do_s is None:
        # Hoja vso pot je hkrati zgornja meja iskanja: pot, ki pride pozneje,
        # kot bi prišel peš, ni odgovor. Meja velja tudi takrat, ko hoje ne
        # ponudimo (nad uro) -- takrat je merilo, ne predlog.
        meja = odhod_s + pes_s if pes_s is not None else None
        najdba = _naprej(conn, izhodisca, cilji, service_date, odhod_s,
                        max_nog, meja, zamik, vec_vozenj=True)
        if not najdba:
            pripni_zamude(conn, predlogi, service_date, now_s)
            return predlogi
        prvi = sestavi(najdba)
        predlogi.append(prvi)
        # Drugačno vprašanje, ne drugačen izid. Poganjamo ju le, kadar se
        # od prvega sploh moreta razlikovati -- vsak je svoje iskanje.
        zgornja = najdba["prihod_s"]
        if prvi["prestopov"] > 0:
            a = _naprej(conn, izhodisca, cilji, service_date, odhod_s,
                       prvi["prestopov"], meja, zamik)
            if a:
                predlogi.append(sestavi(a))
        # Naslednja odhoda. To je poceni: peš matriki sta že izračunani in
        # vsako nadaljnje iskanje je le še krog čez vozni red (7-300 ms z
        # obrezovanjem). Brez tega stran odgovori "ob 13:01" in molči o tem,
        # da naslednji pelje čez deset minut.
        #
        # Iskanje gre od doma **minuto po prejšnjem predlogu**, ne minuto po
        # njegovem vstopu: to je preskočilo vse, kar odpelje v času hoje do
        # postaje. Izmerjeno Vič -> Fužine ob 14:00 (23. 9. 2026): z deset
        # minutami hoje je naslednji postal 60 ob 14:42, 47 ob 14:19 pa je na
        # seznam prišel samo po naključju, prek iskanja "druge poti".
        #
        # Vožnje, ki so že prvi del predloga, gredo ven. Z zamudo bi jo iskanje
        # od poznejše ure našlo znova, brez zamude pa isto vozilo postajo
        # pozneje -- oboje je isti odhod, ne naslednji.
        #
        # Okno teče od prvega predloga, ne od vprašanja: jutrišnje iskanje gre
        # od polnoči in bi sicer pokazalo samo prvo zvezo. Meri se odhod od
        # doma NAJDENE poti, ne začetek iskanja -- iskanje ob 10:41 je na
        # podeželju vrnilo odhod ob 19:20 kot "naslednjega".
        okno = max(odhod_s, prvi["odhod"] - polnoc) + ISKALNO_OKNO_S
        zadnji, nov_s, prikazane = prvi, odhod_s, set()
        for _ in range(NASLEDNJIH):
            prva = next((n for n in zadnji["noge"] if n["vrsta"] == "voznja"), None)
            if prva is None:
                break
            prikazane.add(prva["trip_id"])
            nov_s = max(nov_s, zadnji["odhod"] - polnoc) + 60
            if nov_s > okno:
                break
            nova_meja = nov_s + pes_s if ponudi_pes else None
            a = _naprej(conn, izhodisca, cilji, service_date, nov_s,
                       max_nog, nova_meja, zamik, prikazane)
            if not a:
                break
            zadnji = sestavi(a)
            if zadnji["odhod"] - polnoc > okno:
                break
            predlogi.append(zadnji)

        # Druga pot, ne ista ob drugi uri. Kadar avtobus po voznem redu
        # zmaga za tri minute, vlak sploh ne pride na zaslon -- potnik pa ga
        # pozna in ve, da je zanesljivejši. Ujeto v živo 8. 9. 2026:
        # Križanke -> Novo Polje je ponudil štiri avtobusne poti in nobene z
        # vlakom, čeprav je vlak prišel prej.
        uporabljene = {n["trip_id"] for n in prvi["noge"] if n["vrsta"] == "voznja"}
        if uporabljene:
            # Meja je najdeni prihod plus toliko, kolikor sme biti druga pot
            # poznejša -- brez nje to iskanje premeta pol države za predlog,
            # ki ga bo naslednja vrstica tako ali tako zavrgla.
            a = _naprej(conn, izhodisca, cilji, service_date, odhod_s,
                       max_nog, najdba["prihod_s"] + NAJVEC_POZNEJE_S,
                       zamik, uporabljene)
            if a:
                predlogi.append(sestavi(a))

        if prvi["hoje_s"] > MANJ_HOJE_S:
            kratka_i, kratka_c = kratka()
            if kratka_i and kratka_c:
                a = _naprej(conn, kratka_i, kratka_c, service_date,
                           odhod_s, max_nog, meja, zamik)
                # Pot z manj hoje sme biti počasnejša -- to je njen smisel --
                # a ne poljubno; sicer je to druga pot, ne druga izbira.
                if a and a["prihod_s"] <= zgornja + NAJVEC_POZNEJE_S:
                    predlogi.append(sestavi(a, kratka_i, kratka_c))
    else:
        rok = prihod_do_s
        najprej = odhod_s if odhod_s is not None else -(1 << 30)
        # Oditi prej, kot je treba peš, ni odgovor; oditi pred zdaj ne gre.
        spodaj = max(najprej - 1, rok - pes_s if pes_s is not None else -(1 << 30))
        najdba = _nazaj(conn, izhodisca, cilji, service_date, rok,
                        max_nog, spodaj, zamik)
        if not najdba:
            pripni_zamude(conn, predlogi, service_date, now_s)
            return predlogi
        prvi = sestavi(najdba)
        predlogi.append(prvi)
        # Druge izbire smejo oditi prej -- to je njihov smisel -- a ne
        # poljubno; sicer so druga pot, ne druga izbira.
        spodnja = max(spodaj, najdba["odhod_s"] - NAJVEC_POZNEJE_S)
        if prvi["prestopov"] > 0:
            a = _nazaj(conn, izhodisca, cilji, service_date, rok,
                       prvi["prestopov"], spodnja, zamik)
            if a:
                predlogi.append(sestavi(a))
        # Prejšnji zvezi: kdor mora biti tam ob osmih, hoče vedeti tudi, kaj
        # pelje pred tem -- če prvo zamudi ali hoče rezervo. Zrcalo
        # "naslednjih odhodov" pri vprašanju čim prej, tudi v tem, da prvo
        # vozilo že prikazanega predloga ne sme priti nazaj: isti avtobus z
        # drugim izstopom je isti odhod od doma, ne prejšnja zveza.
        zadnja, prikazane = najdba, set()
        for _ in range(NASLEDNJIH):
            prikazane.add(next(n[0] for n in zadnja["noge"] if n[0] is not None))
            nov_rok = zadnja["prihod_s"] - 60
            if nov_rok < rok - ISKALNO_OKNO_S:
                break
            a = _nazaj(conn, izhodisca, cilji, service_date, nov_rok,
                       max_nog, spodaj, zamik, prikazane)
            if not a:
                break
            predlogi.append(sestavi(a))
            zadnja = a
        uporabljene = {n["trip_id"] for n in prvi["noge"] if n["vrsta"] == "voznja"}
        if uporabljene:
            a = _nazaj(conn, izhodisca, cilji, service_date, rok,
                       max_nog, spodnja, zamik, uporabljene)
            if a:
                predlogi.append(sestavi(a))
        if prvi["hoje_s"] > MANJ_HOJE_S:
            kratka_i, kratka_c = kratka()
            if kratka_i and kratka_c:
                a = _nazaj(conn, kratka_i, kratka_c, service_date, rok,
                           max_nog, spodnja, zamik)
                if a:
                    predlogi.append(sestavi(a, kratka_i, kratka_c))

    # Zamude PRED razvrščanjem: stran razvršča po uri, ki jo pokaže, ne po
    # voznoredni. Sicer si vrstni red in številke nasprotujeta -- ujeto v živo
    # 8. 9. 2026: avtobus "13:35, pričakovano 13:43" je stal nad vlakom, ki
    # pride ob 13:38. Ista past kot barva, ki pripoveduje drugo zgodbo kot
    # številka poleg nje.
    pripni_zamude(conn, predlogi, service_date, now_s)
    return predlogi


def isci(conn: sqlite3.Connection, od: tuple[float, float],
         do: tuple[float, float], service_date: str, odhod_s: int | None,
         max_hoje_s: int = MAX_HOJE_S, max_nog: int = MAX_NOG,
         now_s: int | None = None, prihod_do_s: int | None = None,
         kmh: float = hoja.KMH, jutri: bool = True, pes_meja: bool = True) -> dict:
    """Predlogi poti od točke do točke, po voznem redu danega prometnega dne.

    Vprašanji sta dve, in obe sta potnikovi:

    * **čim prej** (brez `prihod_do_s`): `odhod_s` je sekunda od polnoči, od
      katere naprej iščemo, prvi predlog pa tisti, s katerim si najprej tam;
    * **biti tam do** (`prihod_do_s`): prvi predlog je tisti, s katerim od
      doma odideš **najpozneje** in si še pravočasno tam. `odhod_s` je takrat
      najzgodnejši dovoljeni odhod (za danes: zdaj) ali `None`.

    Odgovor nosi absolutne čase, da se dneva dasta zlepiti brez ugibanja.
    **Pred `NOCNI_S` se išče tudi po včerajšnjem prometnem dnevu**, in vsak
    predlog nosi svoj `datum`: to je dan, po katerem ga iščejo podrobnosti.

    `now_s` obstaja samo za današnji dan -- le takrat je meja med tem, kar je
    vozilo že prevozilo, in tem, kar je pred njim. Brez njega so predlogi po
    voznem redu in brez zamud.

    `kmh` je hitrost na obeh koncih (hoja ali kolo). Peš prestop med
    postajališči ostane hoja: kolo se na postaji pelje ob sebi.

    Kadar pri "čim prej" danes ni več nobene zveze, so odgovor zveze
    naslednjega dne (`danes_ni`), ne "ni poti"; `jutri=False` to izklopi.
    `pes_meja=False` ne ponudi hoje in ne reže voženj, ki pridejo pozneje, kot
    bi prišel peš -- za jutrišnje iskanje od polnoči, ko nihče ne gre peš.
    """
    t0 = time.perf_counter()
    polnoc = stats.polnoc(service_date)
    nazaj = prihod_do_s is not None
    # (prometni dan, koliko je njegova polnoč pred polnočjo `service_date`).
    # Včerajšnji dan šteje sekunde od svoje polnoči, zato vse ure +86 400.
    ura = prihod_do_s if nazaj else odhod_s
    dnevi = [(service_date, 0)]
    if ura is not None and ura < NOCNI_S:
        dnevi.append((_vceraj(service_date), 86400))
    # Vozni red se naloži tu in ne šele v iskanju: iz njega pride tudi
    # množica postajališč, ki te dni sploh kaj strežejo.
    streze: set[str] = set()
    for dan, _ in dnevi:
        streze.update(journey._timetable_for_day(conn, dan, None)[1])

    izhodisca, vir_a, cez_a = blizu(conn, od[0], od[1], streze, max_hoje_s, "od", kmh)
    cilji, vir_b, cez_b = blizu(conn, do[0], do[1], streze, max_hoje_s, "do", kmh)
    vir_hoje = hoja.OSRM if vir_a == vir_b == hoja.OSRM else hoja.ZRAK

    pes_s, vir_pes = _pes_vso_pot(od, do, kmh)
    ponudi_pes = pes_meja and pes_s is not None and pes_s <= MAX_PES_VSO_POT_S
    najprej = odhod_s if odhod_s is not None else -(1 << 30)

    # Hoja vso pot je ena, ne ena na prometni dan: ponoči sta bili na seznamu
    # dve enaki "00:30 -> 01:00 peš" (izmerjeno 23. 9. 2026).
    predlogi: list[dict] = []
    if ponudi_pes and not nazaj:
        predlogi.append(_pes_predlog(service_date, polnoc + odhod_s, pes_s, vir_pes))
    elif ponudi_pes and prihod_do_s - pes_s >= najprej:
        predlogi.append(_pes_predlog(service_date, polnoc + prihod_do_s - pes_s,
                                     pes_s, vir_pes))
    if izhodisca and cilji:
        for dan, zamik_s in dnevi:
            predlogi += _voznje_dneva(
                conn, izhodisca, cilji, dan,
                None if odhod_s is None else odhod_s + zamik_s,
                None if prihod_do_s is None else prihod_do_s + zamik_s,
                None if now_s is None else now_s + zamik_s,
                max_nog, pes_s if pes_meja else None, ponudi_pes, vir_hoje)

    def kdaj(p):
        return p.get("prihod_ocena") or p["prihod"]

    def odhod(p):
        return p.get("odhod_ocena") or p["odhod"]

    # Pot z vozilom, v kateri je HOJE več, kot bi je bilo, če bi šel kar peš,
    # ni predlog, ampak ovinek. Ta primer je bil na zaslonu: vlak stran od
    # cilja in nato osem kilometrov peš nazaj.
    if pes_s is not None:
        predlogi = [p for p in predlogi
                    if not any(n["vrsta"] == "voznja" for n in p["noge"])
                    or p["hoje_s"] < pes_s]

    if nazaj:
        # Iskanje je upoštevalo zamude vozil, ki so zdaj na poti; model ob
        # izstopu zna reči drugače. Pot, ki po njem pride prepozno, ostane na
        # seznamu, a ne na vrhu in ne brez besede.
        for p in predlogi:
            p["prepozno"] = kdaj(p) > polnoc + prihod_do_s
        vrstni = sorted(predlogi, key=lambda p: (p["prepozno"], -odhod(p),
                                                 kdaj(p), p["hoje_s"]))
    else:
        # Ob isti minuti prihoda je prvi tisti, s katerim odideš najpozneje --
        # prestop več pa mora prinesti vsaj PRESTOP_VREDEN_S doma.
        vrstni = sorted(predlogi, key=lambda p: (
            kdaj(p) // 60, -(odhod(p) - PRESTOP_VREDEN_S * p["prestopov"]),
            kdaj(p), p["hoje_s"]))

    # Ista pot se rodi iz dveh vprašanj. Ključ so **samo vožnje in vstopi**:
    # dve poti z istima avtobusoma sta ista pot, tudi če se hoja na koncu vije
    # čez drugo postajališče in se ure razlikujejo za pol minute. Izstop ni v
    # ključu: "25 ob 6:51, izstop Kolodvor" in "... izstop Bavarski dvor" sta
    # za potnika en odhod, na zaslonu pa sta stala drug pod drugim (videno
    # 23. 9. 2026 pri obratnem iskanju). Obdrži se prva po razvrstitvi.
    # Prometni dan je v ključu: ista vožnja včeraj in danes nista isti odhod.
    #
    # Za tem pade vse, kar je po VSEH merilih slabše od že izbranega.
    # Brez tega je stran ponudila pot, ki odide prej, hodi dvakrat dlje in
    # pride ob isti minuti -- videno na zaslonu 8. 9. 2026 (Grosuplje ->
    # Zmajski most: 12:53 z 20 min hoje poleg 13:01 z 10 min, oba prihod
    # 13:31). Vprašanje "z manj hoje" omejuje hojo na VSAKEM koncu, ne v
    # vsoti, in zna zato dati pot z več hoje skupaj.
    videni, izbrani = set(), []
    for p in vrstni:
        kljuc = (p["datum"],) + tuple((n["trip_id"], n["od_seq"])
                                      for n in p["noge"] if n["vrsta"] == "voznja")
        if kljuc in videni:
            continue
        if any(kdaj(q) <= kdaj(p) and q["hoje_s"] <= p["hoje_s"]
               and q["prestopov"] <= p["prestopov"] and odhod(q) >= odhod(p)
               for q in izbrani):
            continue
        videni.add(kljuc)
        izbrani.append(p)

    # Kadar z vozilom ni ničesar, je "ni poti" slabši odgovor od resnice.
    # Hoja uro in pol ni predlog, ki bi ga kdo dal prvi -- je pa edini, ki
    # obstaja, in potnik ga mora videti, da ne čaka avtobusa, ki ne pride.
    if not izbrani and pes_s is not None:
        zacetek = odhod_s if not nazaj else prihod_do_s - pes_s
        if not nazaj or zacetek >= najprej:
            izbrani = [_pes_predlog(service_date, polnoc + zacetek, pes_s, vir_hoje,
                                    edina=True)]

    # Kaj bi pomagalo, kadar z vozilom ni ničesar. Meja hoje velja **do
    # postaje**; kadar je prvo uporabno postajališče tik čez njo, je to
    # ugotovitev in ne ugibanje -- povemo, koliko bi je bilo treba. Da bi s tem
    # pot res nastala, pa ne obljubljamo: postajališče v dosegu še ni zveza.
    nasvet = None
    if not any(n["vrsta"] == "voznja" for p in izbrani for n in p["noge"]):
        potrebno = [x for x in (cez_a if not izhodisca else None,
                                cez_b if not cilji else None) if x]
        if potrebno:
            nasvet = {"vec_hoje_min": min(45, -(-max(potrebno) // 60))}
        elif izhodisca and cilji:
            nasvet = {"ni_zveze": True}

    # Zvečer "ni poti" ni odgovor: potnik hoče vedeti, kdaj gre prvo jutri.
    # Izmerjeno 30. 9. 2026 na 91 naključnih parih: ob 22:30 brez vozila 78,
    # od teh ima 51 zvezo naslednje jutro. Hoja do ure ostane odgovor za nocoj.
    if jutri and not nazaj and nasvet == {"ni_zveze": True} and not ponudi_pes:
        naslednji = (date.fromisoformat(service_date) + timedelta(days=1)).isoformat()
        izid = isci(conn, od, do, naslednji, 0, max_hoje_s, max_nog, kmh=kmh,
                    jutri=False, pes_meja=False)
        if any(n["vrsta"] == "voznja" for p in izid["predlogi"] for n in p["noge"]):
            izid["predlogi"] = [p for p in izid["predlogi"] if not p.get("edina")] + izbrani
            izid["danes_ni"] = True
            izid["trajalo_ms"] = round((time.perf_counter() - t0) * 1000)
            return izid

    return {
        "datum": service_date,
        "izhodisc": len(izhodisca), "ciljev": len(cilji),
        "vir_hoje": vir_hoje,
        "kmh": kmh,
        "prihod_do": polnoc + prihod_do_s if nazaj else None,
        "nasvet": nasvet,
        "predlogi": izbrani,
        "trajalo_ms": round((time.perf_counter() - t0) * 1000),
    }


def isci_do(conn: sqlite3.Connection, od: tuple[float, float],
            do: tuple[float, float], service_date: str, rok_s: int,
            now_s: int | None = None, **kako) -> dict:
    """"Biti tam do ure" -- kot ga vpraša stran.

    Za danes je najzgodnejši odhod zdaj: pot, ki bi odšla pred petimi
    minutami, ni odgovor na "kdaj moram od doma". Kadar do roka ne gre več,
    odgovor ni "ni poti" -- pot je, samo prepozna --, ampak iskanje čim prej
    od zdaj z `ne_ujames`, da stran pove, kdaj si tam najprej.
    """
    izid = isci(conn, od, do, service_date, now_s, now_s=now_s,
                prihod_do_s=rok_s, **kako)
    if not izid["predlogi"] and now_s is not None:
        rok = izid["prihod_do"]
        izid = isci(conn, od, do, service_date, now_s, now_s=now_s, **kako)
        izid["prihod_do"] = rok
        izid["ne_ujames"] = True
    return izid


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


#: Koliko pred odhodom "brez podatka" pomeni, da podatek manjka.
BREZ_PODATKA_PRED_S = 30 * 60


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
    polnoc = stats.polnoc(service_date)
    trip_ids = list({n["trip_id"] for n in noge})
    lm = stats.last_measured(conn, service_date, trip_ids, now_s)
    slack = stats._slack_ahead(conn, trip_ids)
    _, potrjeni = stats.stanje_postankov(conn, service_date, trip_ids)
    feed = _feed_zamude(conn, [(n["trip_id"], n["od_seq"]) for n in noge],
                        service_date)
    # Vožnja brez meritve rabi "običajno" -- isto pravilo kot iskalnik zvez
    # (`stats.pred_odhodom`).
    typ = stats.typical_at_stops(conn, [(n["trip_id"], n["od_seq"]) for n in noge])

    for n in noge:
        tid = n["trip_id"]
        z = stats.zamuda_na_postanku(
            conn, train_no=n["train_no"], trip_id=tid, stop_seq=n["od_seq"],
            ime_postaje=n["od"], feed_delay_s=feed.get((tid, n["od_seq"])),
            lm=lm.get(tid), slack_vrsta=slack.get(tid, ()),
            service_date=service_date,
            potrjen=(tid, n["od_seq"]) in potrjeni,
            obicajno_s=(typ.get((tid, n["od_seq"])) or {}).get("median_s"))
        n["zamuda"] = stats.opis_zamude(z["delay_s"], z["delay_kind"])
        n["zamuda_od"] = z["delay_at"]
        # Brez podatka ni isto kot točno, na zaslonu pa je bilo videti enako:
        # prazno mesto ob liniji. 22. 9. 2026 je tako stal 25, ki je zamujal
        # 20 minut, ker feed zanj ni prišel do nas. Samo za danes -- za drug
        # dan podatka v živo ne more biti in beseda bi bila šum.
        # Za vožnjo, ki odpelje čez uro, podatka v živo še ne more biti in
        # beseda je šum: 30. 9. 2026 je stala pri 86 % voženj na seznamu,
        # mediana 78 min do odhoda. Nekaj pove šele, ko bi vozilo že moralo
        # biti na poti.
        n["brez_podatka"] = (now_s is not None and z["delay_s"] is None
                             and n["odhod"] - polnoc - now_s <= BREZ_PODATKA_PRED_S)
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
        # Zamuda ob izstopu je pogosto DRUGA od tiste ob vstopu -- vozilo vmes
        # porabi rezervo ali jo izgubi. En sam žeton nad vrstico, ki kaže obe
        # uri, si zato nasprotuje: "+1 min" nad prihodom šest minut za voznim
        # redom je videti kot napaka, čeprav je napoved.
        n["zamuda_izstop"] = stats.opis_zamude(ob_izstopu, z["delay_kind"])

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
            # Vožnja brez podatka šteje po voznem redu -- tako jo pokaže tudi
            # stran. Sicer je prestop kazal načrtovane minute poleg ur z
            # zamudo (30. 9. 2026: v 18 od 112 prestopov za 3 min ali več).
            ostane = None
            if a["prihod_ocena"] is not None or b["odhod_ocena"] is not None:
                ostane = ((b["odhod_ocena"] or b["odhod"])
                          - (a["prihod_ocena"] or a["prihod"]) - pes)
            p["prestopi"].append({
                "kje": a["do"], "pes_s": pes,
                "nacrtovano_s": nacrtovano, "ostane_s": ostane,
            })


# ---------------------------------------------------------------- ena pot, razložena

def razberi_noge(niz: str) -> list[tuple[str, int, int]]:
    """`trip:od_seq:do_seq;trip:od_seq:do_seq` -> seznam trojic.

    Vožnja je v naslovu in ne v seji, ker mora biti pot **deljiva**: kdor jo
    komu pošlje, mu pošlje pot, ne svojega brskalnika. LPP-jev `trip_id` nosi
    navpičnice, zato gre skozi `encodeURIComponent` -- tu je že razkodiran.
    """
    out = []
    for kos in niz.split(";"):
        if not kos.strip():
            continue
        deli = kos.rsplit(":", 2)
        if len(deli) != 3:
            raise ValueError(f"noga {kos!r} ni oblike trip:od:do")
        out.append((deli[0], int(deli[1]), int(deli[2])))
    return out


def podrobnosti(conn: sqlite3.Connection, noge_spec: list[tuple[str, int, int]],
                od: tuple[float, float], do: tuple[float, float],
                service_date: str, now_s: int | None = None,
                kmh: float = hoja.KMH, geometrija: bool = True) -> dict:
    """Ena pot, razložena: kod hodiš in kje izstopiš.

    Seznam predlogov odgovarja na „s čim in kdaj"; to na „kako". Zato dvoje,
    česar seznam nima: **pešpot z geometrijo** (črta na zemljevidu, ne število
    minut) in **vmesni postanki vožnje** (kje izstopiš in kaj je pred tem).

    Pot se sestavi iz naslova, ne iz shranjenega iskanja: ista pot mora
    obstajati tudi za tistega, ki mu jo nekdo pošlje.

    `geometrija=False` je za osveževanje zamud med vodenjem (vsakih 30 s):
    pešpoti tedaj le kot čas iz matrike, brez OSRM-ove poti s koraki, ki bi
    jo odjemalec tako ali tako zavrgel.
    """
    by_trip = journey._timetable_for_day(conn, service_date, None)[0]
    vozje = _vozje(conn, service_date)
    imena = _imena(conn)
    polnoc = stats.polnoc(service_date)

    def ime(sid):
        return imena[sid][0] if sid in imena else sid

    def ll(sid):
        return [imena[sid][1], imena[sid][2]] if sid in imena else None

    voznje = []
    for trip_id, od_seq, do_seq in noge_spec:
        if trip_id not in by_trip or trip_id not in vozje:
            raise KeyError(f"vožnje {trip_id} ta dan ni")
        postanki = [s for s in by_trip[trip_id] if od_seq <= s[0] <= do_seq]
        if len(postanki) < 2:
            raise KeyError(f"vožnja {trip_id} nima postankov {od_seq}-{do_seq}")
        v = vozje[trip_id]
        voznje.append({
            "vrsta": "voznja", "trip_id": trip_id, "train_no": v["train_no"],
            "headsign": v["headsign"], "mode": v["mode"], "network": v["network"],
            "agency": v["agency"],
            "od": ime(postanki[0][1]), "do": ime(postanki[-1][1]),
            "od_stop": postanki[0][1], "do_stop": postanki[-1][1],
            "od_ll": ll(postanki[0][1]), "do_ll": ll(postanki[-1][1]),
            "od_seq": od_seq, "do_seq": do_seq,
            "odhod": polnoc + postanki[0][3],
            "prihod": polnoc + postanki[-1][2],
            # Vmesni postanki: kje si in koliko jih je še do izstopa. Brez njih
            # potnik ne ve, kdaj vstati.
            "postanki": [{"stop_seq": s[0], "ime": ime(s[1]),
                          "prihod": polnoc + s[2] if s[2] is not None else None,
                          "odhod": polnoc + s[3] if s[3] is not None else None}
                         for s in postanki],
        })

    def hoja_noga(a, b, od_stop=None, do_stop=None, kmh=kmh):
        # S koraki: na tej strani se po poti tudi hodi, ne le gleda.
        p = hoja.pot(a[0], a[1], b[0], b[1], koraki=True) if geometrija else None
        if p is None:
            # Brez usmerjevalnika ne rišemo ravne črte kot poti: povemo, da
            # geometrije ni, in pustimo prikazu, da to prizna.
            sek, _ = hoja.sekunde(a[0], a[1], b[0], b[1])
            p = {"sekunde": sek or 0, "metri": None, "tocke": None, "koraki": None}
        for k in p.get("koraki") or ():
            k["sekunde"] = hoja.pri_hitrosti(k["sekunde"], kmh)
        return {"vrsta": "hoja", "sekunde": hoja.pri_hitrosti(p["sekunde"], kmh),
                "metri": p["metri"], "tocke": p["tocke"], "koraki": p.get("koraki"),
                "od": ime(od_stop) if od_stop else None,
                "do": ime(do_stop) if do_stop else None,
                "od_stop": od_stop, "do_stop": do_stop,
                "od_ll": ll(od_stop) if od_stop else [a[0], a[1]],
                "do_ll": ll(do_stop) if do_stop else [b[0], b[1]]}

    noge = [hoja_noga(od, voznje[0]["od_ll"], None, voznje[0]["od_stop"])]
    for a, b in zip(voznje, voznje[1:]):
        noge.append(a)
        if a["do_stop"] != b["od_stop"]:
            # Prestop je hoja tudi s kolesom, enako kot v `isci()`: sicer
            # podrobnosti kažejo drugo uro kot seznam, iz katerega so prišle.
            noge.append(hoja_noga(a["do_ll"], b["od_ll"], a["do_stop"], b["od_stop"],
                                  hoja.KMH))
    noge.append(voznje[-1])
    noge.append(hoja_noga(voznje[-1]["do_ll"], do, voznje[-1]["do_stop"], None))
    noge = [n for n in noge if n["vrsta"] != "hoja" or n["sekunde"] >= 60]

    rep = 0
    for n in reversed(noge):
        if n["vrsta"] == "voznja":
            break
        rep += n["sekunde"]
    zac = noge[0]["sekunde"] if noge[0]["vrsta"] == "hoja" else 0
    predlog = {
        "datum": service_date,
        "odhod": voznje[0]["odhod"] - zac,
        "prihod": voznje[-1]["prihod"] + rep,
        "hoje_s": sum(n["sekunde"] for n in noge if n["vrsta"] == "hoja"),
        "prestopov": len(voznje) - 1,
        "noge": noge,
    }
    predlog["trajanje_s"] = predlog["prihod"] - predlog["odhod"]
    pripni_zamude(conn, [predlog], service_date, now_s)
    # `zivo` pove prikazu, ali ima smisel odštevati do odhoda in osveževati
    # zamude. Prej je to sklepal iz "datum je danes", in nočna vožnja, ki nosi
    # včerajšnji prometni dan, je ostala brez obojega.
    return {"datum": service_date, "zivo": now_s is not None, "predlog": predlog}
