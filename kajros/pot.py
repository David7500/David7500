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
import itertools
import math
import sqlite3
import time
from datetime import date, timedelta
from functools import partial

from . import alerts, collector, config, db, geo, hoja, journey, nadomestni, stats

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

#: Za koliko dlje od vrat do vrat sme trajati pot z manj hoje: za toliko, ali
#: za toliko, kolikor hoje prihrani, če je to več. Sama meja prihoda je
#: pustila oditi poljubno prej -- Jesenice -> Ljubljana ob 16:00 „16:21 ->
#: 18:22, 2 prestopa, 6 min hoje“ ob „16:52 -> 18:18, 18 min hoje“: 12 min
#: manj hoje za pol ure dlje zdoma (presoja 18. 10. 2026).
MANJ_HOJE_DLJE_S = 10 * 60


def _manj_hoje_vredna(k: dict, prvi: dict) -> bool:
    """Ali je pot z manj hoje `k` še izbira ob prvem predlogu (`MANJ_HOJE_DLJE_S`)."""
    return k["trajanje_s"] <= prvi["trajanje_s"] + max(MANJ_HOJE_DLJE_S,
                                                       prvi["hoje_s"] - k["hoje_s"])

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
#: Kako dolgo velja izračun `zamiki()`. Zajem je na 30 s; za izbiro poti je
#: dve minuti stara zamuda dovolj, številke na zaslonu so sveže.
ZAMIK_VELJA_S = 120

#: Kako daleč naprej sploh gledamo naslednje odhode. Brez te meje bi na progi
#: s tremi vožnjami na dan ponudili odhod čez sedem ur kot "naslednjega".
ISKALNO_OKNO_S = 3 * 3600

#: Do katere ure se išče tudi po VČERAJŠNJEM prometnem dnevu. Nočni avtobus ob
#: 01:00 nosi včerajšnji datum in `dep_s` čez 86 400 (največji v voznem redu
#: je 121 680, torej 33:48); brez drugega iskanja ga vprašanje ob pol enih ne
#: najde, čeprav vozi. Drugo iskanje je cel krog čez vozni red, zato ne ves
#: dopoldan -- do štirih, kot je bilo to prej v `api.py`.
NOCNI_S = 4 * 3600

#: Prevozniki, kot jih izbere potnik: po imenu na vozilu, ne po šifri v
#: GTFS. Potnik z mesečno LPP ne ve, da ima LPP dve šifri (mestni promet je
#: drug vir, primestne linije so v IJPP), ve pa, da ima vozovnico za LPP --
#: zato ena izbira za oboje (David, 6. 10. 2026: „LPP je vse v zvezi z LPP“).
#: Nadomestni avtobus SŽ je pod vlakom, ker ga vozi SŽ in velja vozovnica za
#: vlak. Prevoznik, ki ga ni v tabeli, ni nikoli izločen.
#:
#: Zakaj izbira sploh obstaja: na 48 poteh po Ljubljani ob 7.30 (kajros.app,
#: 6. 10. 2026) je bil pri 17 prvi predlog z drugim prevoznikom kot mestnim
#: LPP, čeprav je bila pot samo z LPP pri 16 od njih na seznamu nižje.
PREVOZNIKI = {
    "vlak": (config.RAIL_AGENCY_ID,),
    "lpp": ("lpp", "1118"),
    "arriva": ("1123",),
    "nomago": ("1119",),
    "apms": ("1121",),
}


def izlocene(conn: sqlite3.Connection, service_date: str,
             prevozniki: frozenset[str] | None) -> frozenset[str]:
    """Vožnje tega dne, ki jih potnik z izbranimi prevozniki ne more vzeti.

    Iskanje jih preskoči prek iste poti kot vožnje, ki so že na seznamu
    (`brez`), zato pravilo ne potrebuje svoje veje v krogu čez vozni red.
    """
    if not prevozniki or set(PREVOZNIKI) <= prevozniki:
        return frozenset()
    ven = {a for k, agencije in PREVOZNIKI.items() if k not in prevozniki for a in agencije}
    return frozenset(t for t, v in _vozje(conn, service_date).items() if v["agency"] in ven)


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


def _postaje_kljuc(conn: sqlite3.Connection) -> tuple:
    """Ključ statike postajališč: baza in število vrstic."""
    kje = conn.execute("PRAGMA database_list").fetchone()["file"]
    return kje, conn.execute("SELECT COUNT(*) FROM station").fetchone()[0]


def _imena(conn: sqlite3.Connection, kljuc: tuple | None = None) -> dict[str, tuple]:
    """`{stop_id: (ime, lat, lon)}`. Statika, ki se med uvozi ne spreminja;
    branje vseh 10 509 vrstic ob vsakem predlogu je bilo brez potrebe.

    Koordinate so zraven, ker mora zemljevid pot narisati -- brez njih bi jih
    prikaz iskal z novo zahtevo na postajališče."""
    kljuc = kljuc or _postaje_kljuc(conn)
    if (v := _IMENA_CACHE.get(kljuc)) is not None:
        return v
    return _shrani(_IMENA_CACHE, kljuc,
                   {r["stop_id"]: (r["name"], r["lat"], r["lon"])
                    for r in conn.execute("SELECT stop_id, name, lat, lon FROM station")},
                   mest=1)


#: Izmerjena hoja ene točke: `{(postaje, lat, lon, smer): (čas, {stop_id: s})}`.
#:
#: Ista točka se v enem vprašanju išče večkrat: zvečer, ko danes ne pelje nič
#: več, še enkrat za jutri (`danes_ni`), pri roku, ki ga ne ujameš, še enkrat
#: čim prej (`ne_ujames`) -- in vsakič je šla ista matrika na usmerjevalnik.
#: Izmerjeno lokalno 19. 10. 2026: pri Koper -> Ljubljana ob 23:40 štirje
#: klici matrike (78 ms) in štirje pregledi postajališč (143 ms) za dve točki.
#: Potnik isto točko vpraša tudi ob vsaki spremembi ure, prevoznikov ali meje.
#: Pešpoti se med uvozi ne spreminjajo; ura je meja proti premaknjenemu
#: postajališču z istim številom vrstic.
_HOJA_TOCKE: dict[tuple, tuple] = {}
_HOJA_VSO_POT: dict[tuple, tuple] = {}
HOJA_VELJA_S = 3600
_HOJA_MEST = 200


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

    Na arwenu je bil to večji del vsakega klica (presoja 18. 10. 2026): klic,
    ki je padel v novo okno zajema (`rt_fetched`, 30 s), je trajal 1,8-2 s,
    v istem oknu 0,3-0,7 s; na delavnik ob 17h 13 000 vezanih id-jev. Zato
    dvoje: samo vožnje, ki so na poti ali odpeljejo v uri (končana pred več
    kot uro ali začeta čez več kot uro zamude za izbiro od zdaj nimata), in
    rezultat velja `ZAMIK_VELJA_S` -- za IZBIRO poti je dovolj, prikazane
    številke so sveže iz `pripni_zamude()`.
    """
    if now_s is None:
        return {}
    kje = conn.execute("PRAGMA database_list").fetchone()["file"]
    kljuc = (kje, service_date)
    zapis = _ZAMIK_CACHE.get(kljuc)
    if zapis and 0 <= now_s - zapis[0] < ZAMIK_VELJA_S:
        return zapis[1]

    vse = [r[0] for r in conn.execute(
        "SELECT t.trip_id FROM trip t JOIN service_day sd "
        "ON sd.service_id = t.service_id AND sd.date = ? "
        "WHERE t.end_s >= ? AND t.start_s <= ?",
        (service_date, now_s - MAX_ZAMIK_S, now_s + MAX_ZAMIK_S))]
    lm = stats.last_measured(conn, service_date, vse, now_s)
    out = {t: max(-MAX_ZAMIK_S, min(MAX_ZAMIK_S, v["delay_s"]))
           for t, v in lm.items() if v.get("delay_s")}
    if kje:          # baza v pomnilniku (testi) se lahko spremeni pod nami
        _shrani(_ZAMIK_CACHE, kljuc, (now_s, out))
    return out


def _matrika_tocke(kljuc_p: tuple, lat: float, lon: float, merjeni: list[tuple],
                   smer: str) -> tuple[list[int | None], str]:
    """`hoja.matrika()` za kandidate `blizu()`, ki že izmerjenih ne meri znova.

    Zapomni se samo, kar je izmeril usmerjevalnik: ocena po zraku, kadar ta ne
    odgovarja, ni meritev in ne sme ostati, ko spet odgovarja.
    """
    kljuc = (kljuc_p, lat, lon, smer)
    zdaj = time.monotonic()
    zapis = _HOJA_TOCKE.get(kljuc)
    znano = zapis[1] if zapis and zdaj - zapis[0] < HOJA_VELJA_S else {}
    novi = [k for k in merjeni if k[1] not in znano]
    vir, izmerjeno = hoja.OSRM, {}
    if novi:
        sekunde, vir = hoja.matrika(lat, lon, [(k[2], k[3]) for k in novi], smer)
        izmerjeno = {k[1]: s for k, s in zip(novi, sekunde)}
        if vir == hoja.OSRM:
            _shrani(_HOJA_TOCKE, kljuc, (zapis[0] if znano else zdaj, {**znano, **izmerjeno}),
                    mest=_HOJA_MEST)
    return [znano[k[1]] if k[1] in znano else izmerjeno[k[1]] for k in merjeni], vir


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
    čez `sched`) je izmerjeno 629 ms, tu pa je zastonj. Postajališča z legami
    so v pomnilniku (`_imena`), ne iz baze ob vsakem klicu.

    Matrika gre na usmerjevalnik samo za postajališča, ki jih ta točka še ni
    izmerila (`_HOJA_TOCKE`).
    """
    kljuc_p = _postaje_kljuc(conn)
    imena = _imena(conn, kljuc_p)
    polmer = hoja.doseg_zracno(max(najvec_s, NASVET_MEJA_S), kmh)
    dlat = polmer / 111_320.0
    dlon = dlat / max(0.2, abs(math.cos(math.radians(lat))))
    kandidati = []
    for stop_id in streze:
        v = imena.get(stop_id)
        if v is None:
            continue
        ime, la, lo = v
        if la is None or abs(la - lat) > dlat or abs(lo - lon) > dlon:
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

    sekunde, vir = _matrika_tocke(kljuc_p, lat, lon, merjeni, smer)
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


def obvozi_po_postaji(pari) -> dict[str, set[str]]:
    """Pari (vožnja, postajališče) obvoza -> postajališče -> vožnje. Iskanje
    gleda vsak vstop in izstop; postajališča brez obvoza naj stanejo en vpogled
    v slovar, ne dveh terk."""
    out: dict[str, set[str]] = {}
    for trip_id, stop_id in pari:
        out.setdefault(stop_id, set()).add(trip_id)
    return out


def _isci_dan(conn, izhodisca: dict[str, int], cilji: dict[str, int],
              service_date: str, odhod_s: int, max_nog: int,
              meja: int | None = None, zamik: dict | None = None,
              brez: set | None = None, ne_ustavi: dict | None = None) -> dict | None:
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

    `ne_ustavi` je obvoz LPP (`obvozi_po_postaji`): postajališče -> vožnje, ki
    tam ne ustavijo (prazna = nobena). Tam ni ne vstopa ne izstopa.
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
                if ne_ustavi and (nu := ne_ustavi.get(sid)) is not None and ("" in nu or trip_id in nu):
                    continue        # obvoz: tu ne ustavi
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
                    if ne_ustavi and (nu := ne_ustavi.get(nstop)) is not None and ("" in nu or trip_id in nu):
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
                brez: set | None = None, ne_ustavi: dict | None = None) -> dict | None:
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
                if ne_ustavi and (nu := ne_ustavi.get(sid)) is not None and ("" in nu or trip_id in nu):
                    continue        # obvoz: tu ne ustavi
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
                    if ne_ustavi and (nu := ne_ustavi.get(bstop)) is not None and ("" in nu or trip_id in nu):
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

#: Prvo mesto pri "čim prej" ni nujno minuto najzgodnejši prihod. Lesce,
#: Ljubljana -> Bled ob 7:00 (presoja 18. 10. 2026): prvi je bil RG 318 do
#: Lesc z 31 min čakanja na avtobus, prihod 9:14; neposredni avtobus ob 7:50
#: je prišel ob 9:15. Ena minuta prihoda je povozila 18 minut doma in prestop
#: -- prav to je prijava "uro za prestope" (30. 9. 2026). Zato: med predlogi,
#: ki pridejo največ `SKORAJ_ENAKO_S` za najzgodnejšim in nimajo več kot
#: `VEC_HOJE_NAJVEC_S` več hoje, gre prvi tisti z najmanj časa od vrat do vrat
#: (prestop šteje `PRESTOP_VREDEN_S`) -- a le, kadar prihrani vsaj
#: `PRIHRANEK_S`; za manj ostane najzgodnejši. Izmerjeno na naboru 1 280
#: vprašanj (21. 10. 2026 po voznem redu): prvi zamenjan v 38 od 1 138 z
#: vozilom, prihod mediano 1,7 min pozneje (največ 3), od doma 11 min pozneje,
#: od vrat do vrat 8,8 min manj, 13-krat prestop manj, hoje več nikjer za več
#: kot 3 min. Brez praga prihranka (kot je predlagala presoja) 92 zamenjav,
#: tudi za minuto doma ob 3 min poznejšem prihodu, in 3-krat več kot 3 min hoje.
SKORAJ_ENAKO_S = 3 * 60
VEC_HOJE_NAJVEC_S = 5 * 60
PRIHRANEK_S = 5 * 60

#: Prevlada, kot jo vidi potnik: predlog pade, kadar je že izbran tak, ki po
#: urah na kartici (minuta) ne pride pozneje in ne odide prej, nima več kot
#: `PREVLADA_HOJA_S` več hoje in nima več prestopov. Na sekundo primerjano je
#: ostalo "07:07 -> 08:19 z dvema prestopoma" pod "07:07 -> 07:53 z enim", ker
#: je imelo 14 s manj hoje (Škofja Loka -> Ljubljana, presoja 18. 10. 2026).
#: Toleranca ±60 s na obeh urah, kot jo je predlagala presoja, je odstranila
#: tudi naslednji odhod minuto pozneje (`test_naslednji_odhod_v_casu_hoje_ni_
#: preskocen`) -- ta ni šum, ampak rezerva, če prvega ne ujameš. Najzgodnejšega
#: prihoda ne odstrani: ostane, tudi kadar je prva druga (`SKORAJ_ENAKO_S`).
PREVLADA_HOJA_S = 3 * 60


def _stevilo_vozenj(najdba: dict) -> int:
    return sum(1 for n in najdba["noge"] if n[0] is not None)


def _naprej(conn, izhodisca: dict[str, int], cilji: dict[str, int],
            service_date: str, odhod_s: int, max_nog: int,
            meja: int | None = None, zamik: dict | None = None,
            brez: set | None = None, vec_vozenj: bool = False,
            ne_ustavi: dict | None = None) -> dict | None:
    """Najzgodnejši prihod, in od poti s tem prihodom tista, ki odide zadnja."""
    najdba = _isci_dan(conn, izhodisca, cilji, service_date, odhod_s, max_nog,
                       meja, zamik, brez, ne_ustavi)
    if najdba is None:
        return None
    k = _stevilo_vozenj(najdba)
    zadnja = _isci_nazaj(conn, izhodisca, cilji, service_date, najdba["prihod_s"],
                         k, odhod_s - 1, zamik, brez, ne_ustavi)
    # Z vožnjo več se od doma včasih odide ure pozneje in pride ob isti minuti.
    # Iskanje z enakim številom voženj tega ne vidi; prestop več se splača le,
    # kadar prinese vsaj PRESTOP_VREDEN_S doma na vsako dodatno vožnjo. Samo
    # za prvi predlog (`vec_vozenj`): ostala iskanja so zato, da pokažejo
    # drugo izbiro, in razvrstitev v `isci()` jih ob isti uri uredi sama.
    if vec_vozenj and k < max_nog:
        vec = _isci_nazaj(conn, izhodisca, cilji, service_date, najdba["prihod_s"],
                          max_nog, odhod_s - 1, zamik, brez, ne_ustavi)
        if vec and (zadnja is None or vec["odhod_s"] >= zadnja["odhod_s"]
                    + PRESTOP_VREDEN_S * (_stevilo_vozenj(vec) - k)):
            zadnja = vec
    return zadnja or najdba


def _nazaj(conn, izhodisca: dict[str, int], cilji: dict[str, int],
           service_date: str, prihod_s: int, max_nog: int,
           meja: int | None = None, zamik: dict | None = None,
           brez: set | None = None, ne_ustavi: dict | None = None) -> dict | None:
    """Najpoznejši odhod, in od poti s tem odhodom tista, ki pride prva."""
    najdba = _isci_nazaj(conn, izhodisca, cilji, service_date, prihod_s, max_nog,
                         meja, zamik, brez, ne_ustavi)
    if najdba is None:
        return None
    prva = _isci_dan(conn, izhodisca, cilji, service_date, najdba["odhod_s"],
                     _stevilo_vozenj(najdba), najdba["prihod_s"] + 1, zamik, brez,
                     ne_ustavi)
    return prva or najdba


#: Bliže od tega je nadomestni avtobus „pred postajo“ in hoje ne spreminjamo.
NADOMESTNI_PREMIK_M = 60


def _premakni_nadomestne(voznje: list[dict]) -> None:
    """Vstop in izstop nadomestne vožnje na mesto, ki ga objavi SŽ, z opisom."""
    for n in voznje:
        if n["vrsta"] != "voznja" or n.get("mode") != "bus" or n.get("network") != "zeleznica":
            continue
        for kje in ("od", "do"):
            mesto = nadomestni.za_postajo(n.get(kje))
            ll = n.get(f"{kje}_ll")
            if not mesto or mesto.get("lat") is None or not ll:
                continue
            if geo.haversine(ll[0], ll[1], mesto["lat"], mesto["lon"]) < NADOMESTNI_PREMIK_M:
                continue
            n[f"{kje}_ll"] = [mesto["lat"], mesto["lon"]]
            n[f"{kje}_postanek"] = mesto["opis"]


def _nadomestna_mesta(noge: list[dict], od: tuple[float, float] | None,
                      do: tuple[float, float] | None, kmh: float) -> list[dict]:
    """Nadomestni avtobus ne ustavi tam, kjer vlak: vstop in izstop na pravo mesto.

    V voznem redu ima nadomestna vožnja lego železniške postaje (18 od 22
    postajališč), SŽ pa objavi, kje avtobus res stoji (`nadomestni.py`): na
    Ljubljani Tivoli 351 m stran, na Tobačni. Brez tega je pot vodila na
    peron, s katerega avtobus ne pelje, in hoja je bila pet minut prekratka.

    Hoja od vrat in do vrat se izmeri do pravega mesta; med dvema vožnjama,
    ki se srečata na isti postaji, a ne na istem mestu, pride peš prestop.
    """
    _premakni_nadomestne(noge)
    out: list[dict] = []
    for i, n in enumerate(noge):
        if n["vrsta"] == "hoja":
            prej = noge[i - 1] if i > 0 else None
            naprej = noge[i + 1] if i + 1 < len(noge) else None
            if n.get("od") is None and naprej and naprej.get("od_postanek") and od:
                sek, _ = hoja.sekunde(od[0], od[1], *naprej["od_ll"])
                if sek is not None:
                    n["sekunde"] = hoja.pri_hitrosti(sek, kmh)
                n["do_ll"] = naprej["od_ll"]
            if n.get("do") is None and prej and prej.get("do_postanek") and do:
                sek, _ = hoja.sekunde(do[0], do[1], *prej["do_ll"], smer="do")
                if sek is not None:
                    n["sekunde"] = hoja.pri_hitrosti(sek, kmh)
                n["od_ll"] = prej["do_ll"]
        elif out and out[-1]["vrsta"] == "voznja" and out[-1].get("do_ll") and n.get("od_ll") \
                and geo.haversine(*out[-1]["do_ll"], *n["od_ll"]) >= NADOMESTNI_PREMIK_M:
            a, b = out[-1]["do_ll"], n["od_ll"]
            sek, _ = hoja.sekunde(a[0], a[1], b[0], b[1])
            out.append({"vrsta": "hoja", "sekunde": sek or 0,
                        "od": out[-1]["do"], "do": n["od"],
                        "od_stop": out[-1]["do_stop"], "do_stop": n["od_stop"],
                        "od_ll": a, "do_ll": b})
        out.append(n)
    return out


def _sestavi(conn, najdba: dict, izhodisca: dict[str, int], cilji: dict[str, int],
             service_date: str, vir_hoje: str, od: tuple[float, float] | None = None,
             do: tuple[float, float] | None = None, kmh: float = hoja.KMH) -> dict:
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
    noge = _nadomestna_mesta(noge, od, do, kmh)
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
    # Isti par se v enem vprašanju vpraša dvakrat (`danes_ni`, `ne_ujames`);
    # zapomni se samo, kar je izmeril usmerjevalnik (glej `_HOJA_TOCKE`).
    zdaj = time.monotonic()
    zapis = _HOJA_VSO_POT.get((od, do))
    if zapis and zdaj - zapis[0] < HOJA_VELJA_S:
        sek, vir = zapis[1], hoja.OSRM
    else:
        sek, vir = hoja.sekunde(od[0], od[1], do[0], do[1])
        if vir == hoja.OSRM:
            _shrani(_HOJA_VSO_POT, (od, do), (zdaj, sek), mest=_HOJA_MEST)
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
                  pes_s: int | None, ponudi_pes: bool, vir_hoje: str,
                  od: tuple[float, float] | None = None,
                  do: tuple[float, float] | None = None,
                  kmh: float = hoja.KMH,
                  prevozniki: frozenset[str] | None = None) -> list[dict]:
    """Predlogi z vozilom po voznem redu ENEGA prometnega dne, z zamudami.

    Vhodni časi so sekunde od polnoči tega dne, časi v predlogih pa absolutni,
    zato se predlogi dveh dni dajo zložiti v en seznam. Pomen `odhod_s` in
    `prihod_do_s` je isti kot pri `isci()`.
    """
    polnoc = stats.polnoc(service_date)
    zamik = zamiki(conn, service_date, now_s)
    ven = izlocene(conn, service_date, prevozniki)
    # Obvoz LPP velja zdaj (`alerts.ne_ustavi`), po vožnji: 17. 10. 2026 ob
    # maratonu bi pot ponudila vstop na zaprti Slovenski (Konzorcij, Pošta).
    # Za drug dan ga ne vemo; vožnje drugega dne imajo druge id-je.
    obvozi = obvozi_po_postaji(alerts.ne_ustavi(conn)) if now_s is not None else None
    # Odpovedana vožnja (feed: CANCELED) ne vozi -- ni ne vstopa ne izstopa.
    ven = ven | {t for t, d in collector.odpovedane() if d == service_date}
    naprej = partial(_naprej, ne_ustavi=obvozi)
    nazaj = partial(_nazaj, ne_ustavi=obvozi)

    def brez(*druge: set) -> frozenset | None:
        """Vožnje, ki jih to iskanje preskoči: izločeni prevozniki in druge."""
        return ven.union(*druge) or None

    def sestavi(najdba, izh=izhodisca, cil=cilji):
        return _sestavi(conn, najdba, izh, cil, service_date, vir_hoje, od, do, kmh)

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
        najdba = naprej(conn, izhodisca, cilji, service_date, odhod_s,
                        max_nog, meja, zamik, brez(), vec_vozenj=True)
        if not najdba:
            pripni_zamude(conn, predlogi, service_date, now_s)
            return predlogi
        prvi = sestavi(najdba)
        predlogi.append(prvi)
        # Drugačno vprašanje, ne drugačen izid. Poganjamo ju le, kadar se
        # od prvega sploh moreta razlikovati -- vsak je svoje iskanje.
        zgornja = najdba["prihod_s"]
        if prvi["prestopov"] > 0:
            a = naprej(conn, izhodisca, cilji, service_date, odhod_s,
                       prvi["prestopov"], meja, zamik, brez())
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
            a = naprej(conn, izhodisca, cilji, service_date, nov_s,
                       max_nog, nova_meja, zamik, brez(prikazane))
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
            a = naprej(conn, izhodisca, cilji, service_date, odhod_s,
                       max_nog, najdba["prihod_s"] + NAJVEC_POZNEJE_S,
                       zamik, brez(uporabljene))
            if a:
                predlogi.append(sestavi(a))

        if prvi["hoje_s"] > MANJ_HOJE_S:
            kratka_i, kratka_c = kratka()
            if kratka_i and kratka_c:
                a = naprej(conn, kratka_i, kratka_c, service_date,
                           odhod_s, max_nog, meja, zamik, brez())
                # Pot z manj hoje sme biti počasnejša -- to je njen smisel --
                # a ne poljubno; sicer je to druga pot, ne druga izbira.
                if a and a["prihod_s"] <= zgornja + NAJVEC_POZNEJE_S:
                    k = sestavi(a, kratka_i, kratka_c)
                    if _manj_hoje_vredna(k, prvi):
                        predlogi.append(k)
    else:
        rok = prihod_do_s
        najprej = odhod_s if odhod_s is not None else -(1 << 30)
        # Oditi prej, kot je treba peš, ni odgovor; oditi pred zdaj ne gre.
        spodaj = max(najprej - 1, rok - pes_s if pes_s is not None else -(1 << 30))
        najdba = nazaj(conn, izhodisca, cilji, service_date, rok,
                        max_nog, spodaj, zamik, brez())
        if not najdba:
            pripni_zamude(conn, predlogi, service_date, now_s)
            return predlogi
        prvi = sestavi(najdba)
        predlogi.append(prvi)
        # Druge izbire smejo oditi prej -- to je njihov smisel -- a ne
        # poljubno; sicer so druga pot, ne druga izbira.
        spodnja = max(spodaj, najdba["odhod_s"] - NAJVEC_POZNEJE_S)
        if prvi["prestopov"] > 0:
            a = nazaj(conn, izhodisca, cilji, service_date, rok,
                       prvi["prestopov"], spodnja, zamik, brez())
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
            a = nazaj(conn, izhodisca, cilji, service_date, nov_rok,
                       max_nog, spodaj, zamik, brez(prikazane))
            if not a:
                break
            predlogi.append(sestavi(a))
            zadnja = a
        uporabljene = {n["trip_id"] for n in prvi["noge"] if n["vrsta"] == "voznja"}
        if uporabljene:
            a = nazaj(conn, izhodisca, cilji, service_date, rok,
                       max_nog, spodnja, zamik, brez(uporabljene))
            if a:
                predlogi.append(sestavi(a))
        if prvi["hoje_s"] > MANJ_HOJE_S:
            kratka_i, kratka_c = kratka()
            if kratka_i and kratka_c:
                a = nazaj(conn, kratka_i, kratka_c, service_date, rok,
                           max_nog, spodnja, zamik, brez())
                if a:
                    k = sestavi(a, kratka_i, kratka_c)
                    if _manj_hoje_vredna(k, prvi):
                        predlogi.append(k)

    # Zamude PRED razvrščanjem: stran razvršča po uri, ki jo pokaže, ne po
    # voznoredni. Sicer si vrstni red in številke nasprotujeta -- ujeto v živo
    # 8. 9. 2026: avtobus "13:35, pričakovano 13:43" je stal nad vlakom, ki
    # pride ob 13:38. Ista past kot barva, ki pripoveduje drugo zgodbo kot
    # številka poleg nje.
    pripni_zamude(conn, predlogi, service_date, now_s)
    return predlogi


def _kdaj(p: dict) -> int:
    """Prihod na cilj, kot ga pokaže kartica: z zamudo, kadar jo poznamo."""
    return p.get("prihod_ocena") or p["prihod"]


def _odhod(p: dict) -> int:
    """Odhod od doma, kot ga pokaže kartica."""
    return p.get("odhod_ocena") or p["odhod"]


def _zanesljivost(p: dict) -> float:
    """Verjetnost, da gre vse po načrtu; pot brez prestopa in roka je 1."""
    z = p.get("zanesljivost")
    return z["p"] if z and z.get("p") is not None else 1.0


#: Za koliko manj zanesljiv sme biti predlog, ki drugega izrine (prevlada).
#: Pet točk je pod ločljivostjo kratke zgodovine (dva dneva od dvajsetih).
PREVLADA_ZANESLJIVOST = 0.05


def izberi_predloge(predlogi: list[dict], rok: int | None = None) -> list[dict]:
    """Vrstni red predlogov in kateri ostanejo. `rok` (absolutno) je ura, do
    katere mora biti potnik na cilju; brez njega je vprašanje "čim prej".

    Zamude so že pripete: stran razvršča po uri, ki jo pokaže, ne po
    voznoredni. Sicer si vrstni red in številke nasprotujeta -- ujeto v živo
    8. 9. 2026: avtobus "13:35, pričakovano 13:43" je stal nad vlakom, ki
    pride ob 13:38.
    """
    najzgodnejsi = None
    if rok is not None:
        # Iskanje je upoštevalo zamude vozil, ki so zdaj na poti; model ob
        # izstopu zna reči drugače. Pot, ki po njem pride prepozno, ostane na
        # seznamu, a ne na vrhu in ne brez besede.
        for p in predlogi:
            p["prepozno"] = _kdaj(p) > rok
        # Kdor mora biti tam, hoče najpoznejši odhod, ki je ZANESLJIV: prvi
        # predlog "biti tam do" je bil po voznem redu pravočasen v 70 % dni
        # (`scripts/preizkusi_prestope.py`). Tvegani ostanejo pod njimi, med
        # sabo najzanesljivejši prvi.
        def po_roku(p):
            z = _zanesljivost(p)
            if z >= ZANESLJIVO_P:
                return (p["prepozno"], 0, -_odhod(p), _kdaj(p), p["hoje_s"])
            return (p["prepozno"], 1, -z, -_odhod(p), p["hoje_s"])
        vrstni = sorted(predlogi, key=po_roku)
    else:
        # Ob isti minuti prihoda je prvi tisti, s katerim odideš najpozneje --
        # prestop več pa mora prinesti vsaj PRESTOP_VREDEN_S doma.
        vrstni = sorted(predlogi, key=lambda p: (
            _kdaj(p) // 60, -(_odhod(p) - PRESTOP_VREDEN_S * p["prestopov"]),
            _kdaj(p), p["hoje_s"]))
        # Skoraj enak prihod z manj čakanja ali prestopov gre prvi (glej
        # `SKORAJ_ENAKO_S`). Ostali ostanejo po prihodu.
        if vrstni:
            p0 = najzgodnejsi = vrstni[0]

            def cena(p):
                return _kdaj(p) - _odhod(p) + PRESTOP_VREDEN_S * p["prestopov"]
            boljsi = min((p for p in vrstni
                          if _kdaj(p) <= _kdaj(p0) + SKORAJ_ENAKO_S
                          and p["hoje_s"] <= p0["hoje_s"] + VEC_HOJE_NAJVEC_S), key=cena)
            if cena(boljsi) <= cena(p0) - PRIHRANEK_S:
                vrstni.insert(0, vrstni.pop(next(
                    i for i, p in enumerate(vrstni) if p is boljsi)))

    # Ista pot se rodi iz dveh vprašanj. Ključ so **samo vožnje in vstopi**:
    # dve poti z istima avtobusoma sta ista pot, tudi če se hoja na koncu vije
    # čez drugo postajališče in se ure razlikujejo za pol minute. Izstop ni v
    # ključu: "25 ob 6:51, izstop Kolodvor" in "... izstop Bavarski dvor" sta
    # za potnika en odhod, na zaslonu pa sta stala drug pod drugim (videno
    # 23. 9. 2026 pri obratnem iskanju). Obdrži se prva po razvrstitvi.
    # Prometni dan je v ključu: ista vožnja včeraj in danes nista isti odhod.
    #
    # Za tem pade vse, kar je po VSEH merilih slabše od že izbranega, kot ga
    # vidi potnik (`PREVLADA_HOJA_S`). Brez tega je stran ponudila pot, ki
    # odide prej, hodi dvakrat dlje in pride ob isti minuti -- videno na
    # zaslonu 8. 9. 2026 (Grosuplje -> Zmajski most: 12:53 z 20 min hoje poleg
    # 13:01 z 10 min, oba prihod 13:31). Vprašanje "z manj hoje" omejuje hojo
    # na VSAKEM koncu, ne v vsoti, in zna zato dati pot z več hoje skupaj.
    def z_vozilom(p):
        return any(n["vrsta"] == "voznja" for n in p["noge"])

    # Hoja vso pot se z vožnjo primerja na sekundo, kot prej: s toleranco je
    # "peš 30 min" izrinil avtobus z 28 min hoje, ki pride minuto pozneje, in
    # stran je trdila "zveze ta čas ni" (lj13 ob 17:10 na naboru 1 280).
    def prevlada(q, p):
        # Tveganje je na kartici kot ura: hitrejša pot s prestopom, ki drži
        # trikrat od štirih, zanesljivejše ne izrine.
        if _zanesljivost(q) < _zanesljivost(p) - PREVLADA_ZANESLJIVOST:
            return False
        if p is najzgodnejsi or not (z_vozilom(p) and z_vozilom(q)):
            return (_kdaj(q) <= _kdaj(p) and _odhod(q) >= _odhod(p)
                    and q["hoje_s"] <= p["hoje_s"] and q["prestopov"] <= p["prestopov"])
        return (_kdaj(q) // 60 <= _kdaj(p) // 60 and _odhod(q) // 60 >= _odhod(p) // 60
                and q["hoje_s"] <= p["hoje_s"] + PREVLADA_HOJA_S
                and q["prestopov"] <= p["prestopov"])

    videni, izbrani = set(), []
    for p in vrstni:
        kljuc = (p["datum"],) + tuple((n["trip_id"], n["od_seq"])
                                      for n in p["noge"] if n["vrsta"] == "voznja")
        if kljuc in videni:
            continue
        if any(prevlada(q, p) for q in izbrani):
            continue
        videni.add(kljuc)
        izbrani.append(p)
    return izbrani


def isci(conn: sqlite3.Connection, od: tuple[float, float],
         do: tuple[float, float], service_date: str, odhod_s: int | None,
         max_hoje_s: int = MAX_HOJE_S, max_nog: int = MAX_NOG,
         now_s: int | None = None, prihod_do_s: int | None = None,
         kmh: float = hoja.KMH, jutri: bool = True,
         nadaljevanje: bool = False,
         prevozniki: frozenset[str] | None = None) -> dict:
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
    `nadaljevanje=True` je to jutrišnje iskanje od polnoči: hoje ne ponudi in
    z njo ne reže voženj (ob polnoči nihče ne gre peš), včerajšnjega dne pa ne
    išče znova -- ta je bil pravkar preiskan do konca.
    """
    t0 = time.perf_counter()
    polnoc = stats.polnoc(service_date)
    nazaj = prihod_do_s is not None
    # (prometni dan, koliko je njegova polnoč pred polnočjo `service_date`).
    # Včerajšnji dan šteje sekunde od svoje polnoči, zato vse ure +86 400.
    ura = prihod_do_s if nazaj else odhod_s
    dnevi = [(service_date, 0)]
    if ura is not None and ura < NOCNI_S and not nadaljevanje:
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
    ponudi_pes = not nadaljevanje and pes_s is not None and pes_s <= MAX_PES_VSO_POT_S
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
                max_nog, None if nadaljevanje else pes_s, ponudi_pes, vir_hoje, od, do, kmh,
                prevozniki)

    # Pot z vozilom, v kateri je HOJE več, kot bi je bilo, če bi šel kar peš,
    # ni predlog, ampak ovinek. Ta primer je bil na zaslonu: vlak stran od
    # cilja in nato osem kilometrov peš nazaj.
    if pes_s is not None:
        predlogi = [p for p in predlogi
                    if not any(n["vrsta"] == "voznja" for n in p["noge"])
                    or p["hoje_s"] < pes_s]
    # Tveganje PRED izbiro: pri roku odloča, kateri predlog je prvi, in pot,
    # ki je hitrejša, a tvegana, zanesljivejše ne izrine (`izberi_predloge`).
    pripni_tveganje(conn, predlogi, {d for d, _ in dnevi} if now_s is not None else set(),
                    polnoc + prihod_do_s if nazaj else None)
    izbrani = izberi_predloge(predlogi, polnoc + prihod_do_s if nazaj else None)

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
                    jutri=False, nadaljevanje=True, prevozniki=prevozniki)
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
        # Vozilo, ki je že kje izmerjeno, je na poti: njegova ocena je iz
        # meritve, in tveganje prestopa se računa iz nje (`verjetnost_zdaj`).
        n["na_poti"] = lm.get(tid) is not None
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
        # Vozni red + zaokrožena minuta, ki jo kaže žeton (`stats.ura_z_zamudo`).
        n["odhod_ocena"] = stats.ura_z_zamudo(n["odhod"], z["delay_s"])
        # Zamuda ob izstopu ni ista kot ob vstopu: vlak vmes porabi rezervo
        # voznega reda. Isti model kot v oknu vožnje.
        ob_izstopu = stats.estimate_at(conn, n["train_no"], tid, n["od_seq"],
                                       z["delay_s"], n["do_seq"], service_date)
        if ob_izstopu is None:
            ob_izstopu = z["delay_s"]
        n["prihod_ocena"] = stats.ura_z_zamudo(n["prihod"], ob_izstopu)
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


# ---------------------------------------------------------------- tveganje prestopa
#
# Prestop drži, kadar zamuda prvega vozila ob prihodu ne poje rezerve po
# voznem redu in zamude drugega ob odhodu. Kaj o tem vemo, je odvisno od
# trenutka (`scripts/preizkusi_prestope.py`):
#
# * vnaprej (jutri, čez uro) samo, kako je ISTI prestop držal prejšnje dni --
#   isti vožnji čez dneve, isti postanki, oba isti dan, da ostane tudi to,
#   da slabo vreme zamudi obe;
# * ko je prvo vozilo na poti, njegovo zamudo; negotova je le še napaka
#   ocene, in ta je izmerjena (senca, `ocena.porazdelitev_napak`).

#: Koliko dni nazaj šteje zgodovina prestopa.
TVEGANJE_DNI = 60

#: Najmanj vrstic sence na omrežje in stanje vozila, da porazdelitvi napak
#: verjamemo. Senca jih ima na dan nekaj tisoč; to je varovalka za novo bazo.
NAPAK_NAJMANJ = 500

#: Kako dolgo velja prebrani povzetek napak v pomnilniku. Računa se enkrat
#: na dan (`stats.refresh_summaries`), branje iz baze ob vsakem iskanju pa
#: je samo razčlenjevanje istega JSON-a.
NAPAKE_VELJA_S = 600

_NAPAKE: list = [0.0, None, None]          # (kdaj, baza, porazdelitve)


def napake_sence(conn: sqlite3.Connection) -> dict:
    """`{omrežje: povzetek}` napake prikaza iz dnevnega povzetka sence."""
    kje = conn.execute("PRAGMA database_list").fetchone()["file"]
    if _NAPAKE[1] == kje and time.monotonic() - _NAPAKE[0] < NAPAKE_VELJA_S:
        return _NAPAKE[2]
    out = {omr: stats.summary_get(conn, "napake_sence", omr, stats.SUMMARY_WINDOWS[0])
           for omr in ("zeleznica", "avtobus")}
    if kje:          # baza v pomnilniku (testi) se lahko spremeni pod nami
        _NAPAKE[:] = [time.monotonic(), kje, out]
    return out


def _delezi_napak(napake: dict, omrezje: str, na_poti: bool) -> tuple | None:
    """(korak, od, deleži po razredih) ali `None`, kadar sence ni dovolj."""
    p = (napake or {}).get(omrezje)
    stevci = p and p.get("na_poti" if na_poti else "pred_odhodom")
    vsota = sum(stevci or ())
    if vsota < NAPAK_NAJMANJ:
        return None
    return p["korak_s"], p["od_s"], [c / vsota for c in stevci]


def verjetnost_zdaj(ostane_s: int, omr_a: str, omr_b: str, na_poti_a: bool,
                    na_poti_b: bool, napake: dict) -> float | None:
    """Verjetnost, da prestop drži, kadar prikaz kaže `ostane_s` rezerve.

    Resnica = kar prikaz kaže + napaka, zato prestop drži, kadar napaka
    prvega vozila (pride pozneje, kot piše) minus napaka drugega ne preseže
    rezerve. Napaki sta iz sence za omrežje in stanje vozila, vzeti kot
    neodvisni -- slabo vreme ju premakne skupaj, zato je to stran previdnosti.
    `None`, kadar sence ni dovolj.
    """
    a = _delezi_napak(napake, omr_a, na_poti_a)
    b = _delezi_napak(napake, omr_b, na_poti_b)
    if a is None or b is None:
        return None
    korak, od, pa = a
    kum = list(itertools.accumulate(pa))
    p = 0.0
    for j, wb in enumerate(b[2]):
        if wb:
            # Prvo vozilo sme zamuditi največ toliko več, kot kaže prikaz.
            i = math.floor((ostane_s + b[1] + j * b[0] - od) / korak)
            if i >= 0:
                p += wb * kum[min(i, len(kum) - 1)]
    return min(1.0, p)


def _razred_rezerve(rezerva_s: int) -> str:
    return "0-3" if rezerva_s < 180 else "3-6" if rezerva_s < 360 \
        else "6-10" if rezerva_s < 600 else "10+"


_ZAMUDE_DNI: dict[tuple, tuple] = {}
#: Pretekli dnevi se ne spreminjajo; ura je zato, da včerajšnji pozni
#: podatki pridejo zraven in da predpomnilnik ne raste brez meje.
ZAMUDE_DNI_VELJA_S = 3600
_ZAMUDE_DNI_NAJVEC = 20_000


def zamude_po_dnevih(conn: sqlite3.Connection, pari: list[tuple[str, int]],
                     dan: str, prihod: bool) -> dict[tuple[str, int], dict[str, int]]:
    """`{(trip_id, stop_seq): {dan: zamuda}}` za `TVEGANJE_DNI` pred `dan`.

    `prihod=True` je zamuda ob PRIHODU (`COALESCE(delay_arr, delay_dep)`):
    za vozilo, s katerega izstopiš -- vlak na dolgem postanku odpelje z manjšo
    zamudo, kot je pripeljal. Sicer odhodna, kot povsod drugje.

    Po vožnji čez dneve (`db.voznja_sql`) in s predhodnicami (`PREDNIKI_SQL`),
    isto kot `stats._tipicno_po_dnevih`; tam je tudi, zakaj `CROSS JOIN`.
    """
    kje = conn.execute("PRAGMA database_list").fetchone()["file"]
    zdaj = time.monotonic()
    out: dict[tuple[str, int], dict[str, int]] = {}
    manjka = []
    for par in sorted(set(pari)):
        v = _ZAMUDE_DNI.get((kje, dan, prihod, par)) if kje else None
        if v and zdaj - v[0] < ZAMUDE_DNI_VELJA_S:
            out[par] = v[1]
        else:
            manjka.append(par)
    if not manjka:
        return out
    zamuda = "COALESCE({0}delay_arr, {0}delay_dep)" if prihod \
        else "COALESCE({0}delay_dep, {0}delay_arr)"
    od = (date.fromisoformat(dan) - timedelta(days=TVEGANJE_DNI)).isoformat()
    novi: dict[tuple[str, int], dict[str, int]] = {par: {} for par in manjka}
    for i in range(0, len(manjka), 400):
        kos = manjka[i:i + 400]
        vals = ",".join(["(?,?)"] * len(kos))
        vezave = [x for par in kos for x in par] + [od, dan]
        for r in conn.execute(
                f"WITH want(trip_id, stop_seq) AS (VALUES {vals}) "
                f"SELECT w.trip_id, w.stop_seq, r.service_date, {zamuda.format('r.')} AS d "
                f"FROM want w CROSS JOIN trip a ON a.trip_id = w.trip_id "
                f"CROSS JOIN trip t ON {db.voznja_sql('t')} = {db.voznja_sql('a')} "
                f"CROSS JOIN run r ON r.trip_id = t.trip_id AND r.stop_seq = w.stop_seq "
                f"WHERE r.service_date >= ? AND r.service_date < ? AND d IS NOT NULL "
                f"  AND ABS(d) <= {stats.MAX_REALNA_ZAMUDA_S}", vezave):
            novi[(r["trip_id"], r["stop_seq"])][r["service_date"]] = r["d"]
        # Isti dan pod novim id-jem in pod predhodnico šteje enkrat -- nova velja.
        for r in conn.execute(
                f"WITH want(trip_id, stop_seq) AS (VALUES {vals}) "
                f"SELECT p.trip_id, p.stop_seq, p.service_date, {zamuda.format('p.')} AS d "
                f"FROM want w CROSS JOIN ({db.PREDNIKI_SQL}) p "
                f"  ON p.trip_id = w.trip_id AND p.stop_seq = w.stop_seq "
                f"WHERE p.service_date >= ? AND p.service_date < ? AND d IS NOT NULL "
                f"  AND ABS(d) <= {stats.MAX_REALNA_ZAMUDA_S}", vezave):
            novi[(r["trip_id"], r["stop_seq"])].setdefault(r["service_date"], r["d"])
    if kje:          # baza v pomnilniku (testi) se lahko spremeni pod nami
        if len(_ZAMUDE_DNI) + len(novi) > _ZAMUDE_DNI_NAJVEC:
            _ZAMUDE_DNI.clear()
        for par, v in novi.items():
            _ZAMUDE_DNI[(kje, dan, prihod, par)] = (zdaj, v)
    out.update(novi)
    return out


#: Delež prestopov, ki so držali, po omrežju obeh vozil in rezervi po voznem
#: redu. Izhodišče za prestop brez lastne zgodovine in vrednost, proti kateri
#: se kratka zgodovina skrči. Izmerjeno 22. 10. 2026
#: (`scripts/preizkusi_prestope.py`, 500 vprašanj na voznem redu četrtka,
#: 1 867 prestopov iz predlogov, 15 689 dni-prestopov). Rezerva 3-6 min pri
#: vlaku na avtobus drži v 49 %, med avtobusi v 70 %: iskanje je take
#: prestope ponujalo brez besede. Pod 6 min na vlak jih ni (prag iskanja).
PRESTOP_IZHODISCE = {
    ("avtobus", "avtobus", "3-6"): 0.70,
    ("avtobus", "avtobus", "6-10"): 0.77,
    ("avtobus", "avtobus", "10+"): 0.91,
    ("avtobus", "zeleznica", "6-10"): 0.92,
    ("avtobus", "zeleznica", "10+"): 0.97,
    ("zeleznica", "avtobus", "3-6"): 0.49,
    ("zeleznica", "avtobus", "6-10"): 0.62,
    ("zeleznica", "avtobus", "10+"): 0.86,
    ("zeleznica", "zeleznica", "6-10"): 0.87,
    ("zeleznica", "zeleznica", "10+"): 0.93,
}
#: Utež izhodišča v dneh. Na izpustitvi dneva (isti nabor) je par sam
#: Brier 0,100 in log-loss 0,393 (dva dneva zgodovine sta trdna "vedno"),
#: z utežjo 2 0,098 in 0,321, z 8 0,105; razred rezerve sam 0,152.
IZHODISCE_DNI = 2
#: Delež dni, ko je zadnja vožnja predloga "biti tam do" prišla v rezervi do
#: roka, po omrežju in rezervi (isti nabor, 12 404 dni-voženj): izhodišče za
#: njeno kratko zgodovino. Rezerva odloča skoraj vse -- z dvema minutama je
#: avtobus pravočasen v 27 %, z dvajsetimi v 98 % --, zato eno samo izhodišče
#: (89 %) ni šlo: 50 minut rezerve brez zgodovine je bilo „92 %“. Zmnožek z
#: izhodiščem po rezervi Brier 0,111 proti 0,112.
ROK_IZHODISCE = {
    ("avtobus", "0-2"): 0.27, ("avtobus", "2-5"): 0.54, ("avtobus", "5-10"): 0.71,
    ("avtobus", "10-20"): 0.87, ("avtobus", "20+"): 0.98,
    ("zeleznica", "0-2"): 0.32, ("zeleznica", "2-5"): 0.39, ("zeleznica", "5-10"): 0.88,
    ("zeleznica", "10-20"): 0.97, ("zeleznica", "20+"): 0.98,
}


def _razred_roka(rezerva_s: int) -> str:
    return "0-2" if rezerva_s < 120 else "2-5" if rezerva_s < 300 else "5-10" \
        if rezerva_s < 600 else "10-20" if rezerva_s < 1200 else "20+"

#: Meji stopenj. Predlog z rokom, ki je pravočasen manj kot devetkrat od
#: desetih, ni odgovor na "moram biti tam" (David, 22. 10. 2026: "je precej
#: važno, da je tveganost precej nizka").
ZANESLJIVO_P = 0.9
TVEGANO_P = 0.7


def _izhodisce(omr_a: str, omr_b: str, rezerva_s: int) -> float:
    r = _razred_rezerve(rezerva_s)
    return PRESTOP_IZHODISCE.get((omr_a, omr_b, r)) \
        or PRESTOP_IZHODISCE.get((omr_a, omr_b, "6-10" if r in ("0-3", "3-6") else r)) or 0.8


def stopnja(p: float) -> str:
    return "zanesljivo" if p >= ZANESLJIVO_P else "tvegano" if p >= TVEGANO_P else "zelo tvegano"


def pripni_tveganje(conn: sqlite3.Connection, predlogi: list[dict],
                    zivi_dnevi: set[str], rok: int | None = None) -> None:
    """Vsakemu prestopu verjetnost, da drži, predlogu pa `zanesljivost`.

    Zanesljivost je verjetnost, da gre vse po načrtu: da držijo vsi prestopi,
    pri roku pa še, da je zadnja vožnja pravočasna. Zmnožek delov je na
    izpustitvi dneva najboljši izmed preizkušenih (Brier 0,113 proti 0,117 za
    delež dni celega predloga in 0,208 za delež vseh): delov ima vsak več dni
    kot cel predlog, in umerjen je (napoved 90-100 % -> 96,6 % proti 96,7 %).

    `zivi_dnevi` so prometni dnevi, za katere je zdaj -- le tam je vozilo
    lahko na poti in velja `verjetnost_zdaj`. `rok` je absoluten.
    """
    if not predlogi:
        return
    napake = None
    po_dnevih: dict[str, list] = {}
    for p in predlogi:
        voznje = [n for n in p["noge"] if n["vrsta"] == "voznja"]
        if voznje:
            po_dnevih.setdefault(p["datum"], []).append((p, voznje))
    for dan, skupina in po_dnevih.items():
        by_trip = journey._timetable_for_day(conn, dan, None)[0]
        prihodi = zamude_po_dnevih(conn, [(n["trip_id"], n["do_seq"]) for _, vv in skupina
                                          for n in vv], dan, prihod=True)
        odhodi = zamude_po_dnevih(conn, [(n["trip_id"], n["od_seq"]) for _, vv in skupina
                                         for n in vv[1:]], dan, prihod=False)
        zivo = dan in zivi_dnevi
        if zivo and napake is None:
            napake = napake_sence(conn)
        for p, voznje in skupina:
            deli, zivi = [], False
            for a, b, t in zip(voznje, voznje[1:], p.get("prestopi") or ()):
                omr_a, omr_b = a.get("network"), b.get("network")
                za = prihodi.get((a["trip_id"], a["do_seq"]), {})
                zb = odhodi.get((b["trip_id"], b["od_seq"]), {})
                # Vlak na izhodišču ne poroča nikoli (`model.md`), pred voznim
                # redom pa ne odpelje: brez zgodovine odhoda je nič -- previdno,
                # ker zamuda drugega prestopu samo pomaga.
                if not zb and omr_b == "zeleznica" and by_trip.get(b["trip_id"]) \
                        and by_trip[b["trip_id"]][0][0] == b["od_seq"]:
                    zb = dict.fromkeys(za, 0)
                skupni = [d for d in za if d in zb]
                drzal = sum(1 for d in skupni if t["nacrtovano_s"] + zb[d] - za[d] >= 0)
                izh = _izhodisce(omr_a, omr_b, t["nacrtovano_s"])
                verj = (drzal + IZHODISCE_DNI * izh) / (len(skupni) + IZHODISCE_DNI)
                tv = {"p": round(verj, 3), "vir": "zgodovina", "dni": len(skupni),
                      "drzal": drzal}
                if zivo and a.get("na_poti") and t.get("ostane_s") is not None:
                    z = verjetnost_zdaj(t["ostane_s"], omr_a, omr_b, True,
                                        bool(b.get("na_poti")), napake)
                    if z is not None:
                        tv.update(p=round(z, 3), vir="zdaj")
                        zivi = True
                tv["stopnja"] = stopnja(tv["p"])
                t["tveganje"] = tv
                deli.append(tv["p"])
            zan = {"p": math.prod(deli) if deli else None,
                   "vir": "zdaj" if zivi else "zgodovina"}
            if rok is not None:
                zan["p"] = (zan["p"] if deli else 1.0) * _pravocasno(
                    p, voznje[-1], rok, prihodi, zivo, napake)
                zan["rok"] = True
            if zan["p"] is None:
                continue                  # brez prestopa in brez roka: ni o čem
            zan["p"] = round(zan["p"], 3)
            zan["stopnja"] = stopnja(zan["p"])
            p["zanesljivost"] = zan


def _pravocasno(p: dict, zadnja: dict, rok: int, prihodi: dict, zivo: bool,
                napake: dict | None) -> float:
    """Verjetnost, da zadnja vožnja pripelje v rezervi do roka.

    Na poti iz napake ocene ob prihodu, sicer iz njene zgodovine: delež dni,
    ko je zamuda ob prihodu ostala v rezervi, skrčen proti `ROK_IZHODISCE`
    za to rezervo.
    """
    if zivo and zadnja.get("na_poti") and napake and zadnja.get("prihod_ocena"):
        d = _delezi_napak(napake, zadnja.get("network"), True)
        if d is not None:
            korak, od, delezi = d
            rezerva = rok - (p.get("prihod_ocena") or p["prihod"])
            i = math.floor((rezerva - od) / korak)
            return sum(delezi[:max(0, min(i + 1, len(delezi)))])
    rezerva = rok - p["prihod"]
    dnevi = prihodi.get((zadnja["trip_id"], zadnja["do_seq"]), {})
    ok = sum(1 for z in dnevi.values() if z <= rezerva)
    izh = ROK_IZHODISCE.get((zadnja.get("network"), _razred_roka(rezerva)), 0.9)
    return (ok + IZHODISCE_DNI * izh) / (len(dnevi) + IZHODISCE_DNI)


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
                kmh: float = hoja.KMH, geometrija: bool = True,
                rok: int | None = None) -> dict:
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
            # potnik ne ve, kdaj vstati. Lega zato, da stran na poti iz GPS
            # ve, katera postaja je naslednja (`pot_podrobno.js`).
            "postanki": [{"stop_seq": s[0], "ime": ime(s[1]), "ll": ll(s[1]),
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
                # Točki poti, ne postaje: pri nadomestnem avtobusu se razlikujeta.
                "od_ll": [a[0], a[1]], "do_ll": [b[0], b[1]]}

    _premakni_nadomestne(voznje)
    noge = [hoja_noga(od, voznje[0]["od_ll"], None, voznje[0]["od_stop"])]
    for a, b in zip(voznje, voznje[1:]):
        noge.append(a)
        if a["do_stop"] != b["od_stop"] or a["do_ll"] != b["od_ll"]:
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
    # Na poti je to edino mesto, kjer potnik vidi, ali prestop še drži.
    pripni_tveganje(conn, [predlog], {service_date} if now_s is not None else set(), rok)
    # `zivo` pove prikazu, ali ima smisel odštevati do odhoda in osveževati
    # zamude. Prej je to sklepal iz "datum je danes", in nočna vožnja, ki nosi
    # včerajšnji prometni dan, je ostala brez obojega.
    return {"datum": service_date, "zivo": now_s is not None, "predlog": predlog}
