"""Pristajalne strani: ena relacija in ena postaja na svojem naslovu.

**Zakaj obstajajo.** Do 17. 9. 2026 je bilo v `sitemap.xml` enajst naslovov in
vsak je bil prazna lupina, ki se napolni v JS -- iskalnik torej ni imel česa
indeksirati. Človek pa ne išče „kajros"; išče **„vlak ljubljana koper"** in
**„odhodi celje"**. Za vsak tak niz mora obstajati naslov, ki že v odgovoru
strežnika nosi naslov, odhode in izmerjeno številko.

Vsebina teh strani je edino, česar nima nihče drug: vozni red objavi tudi
prevoznik, **zgodovine zamud pa ne**.

Tu je kazalo -- kateri naslovi obstajajo in kaj je o njih izmerjeno. Izris je
v `templates/relacija.html` in `templates/postaja.html`, poti v `api.py`.

Kazalo je **povzetek** (`stats.summary_get`, kind `pristanek`): agregat čez
vso zgodovino se po pravilu projekta ne računa v zahtevi, tu pa je pri
avtobusih dvanajst sekund dela.
"""
from __future__ import annotations

import re
import sqlite3
import statistics
from datetime import datetime, timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo

from . import config, geo, journey, stats

TZ = ZoneInfo(config.TIMEZONE)

#: Koliko relacij na omrežje pride v zemljevid strani. Meja ni estetska:
#: parov, ki prestanejo `MIN_VOZENJ` in `MIN_RAZDALJA_M`, je 5 903 pri
#: železnici in 26 049 pri avtobusih (izmerjeno 17. 9. 2026). Tisoče tankih
#: strani so za iskalnik breme, ne prednost -- v zemljevid gre vrh po prometu,
#: ostalo ostane dosegljivo in `noindex`.
NAJVEC_RELACIJ = 400

#: Koliko postaj na omrežje pride v zemljevid strani. Železnica jih ima 264 z
#: meritvijo, postajališč pa je 5 356 in rep so tista z eno vožnjo na dan.
NAJVEC_POSTAJ = 300

#: Koliko voženj v voznem redu mora imeti par postaj, da je sploh kandidat.
#: Štiri je pri železnici en par na dan v obe smeri; pri avtobusih je isto
#: število brez pomena, ker je voženj petdesetkrat več.
MIN_VOZENJ = {"zeleznica": 4, "avtobus": 30}

#: Koliko zračne razdalje mora biti med postajama. **To ni okras, ampak edino,
#: kar loči relacijo od dveh postajališč iste ulice.** Brez te meje je vrh
#: avtobusne lestvice „Ljubljana Kino Šiška → Ljubljana Tivoli" (1,2 km,
#: 870 voženj) -- par, po katerem nihče ne išče povezave, ker gre peš. Z njo
#: sta na vrhu „Medvode → Ljubljana Šentvid" in „Grosuplje → Ljubljana
#: Strelišče", torej relaciji, ki ju ljudje res vozijo.
MIN_RAZDALJA_M = {"zeleznica": 3000, "avtobus": 6000}

#: Koliko meritev mora stati za številko, da jo stran napiše. Pod tem pove, da
#: je zajema premalo: izmišljena natančnost je tu posebej škodljiva, ker je ta
#: številka edini razlog, da stran obstaja.
MIN_MERITEV = 30

#: Mestni LPP v kazalu relacij ne sodi. Njegove „relacije" so postajališče do
#: postajališča znotraj mesta in nihče ne vpraša „kdaj mi pelje z Bavarskega
#: dvora na Ajdovščino" -- vpraša za linijo ali za postajališče. Mestna
#: postajališča **svojo stran imajo**, relacije ne.
BREZ_AGENCIJE = "lpp"

#: Koliko odhodov se izpiše na eni strani. Medvode → Ljubljana Šentvid jih ima
#: 108 na dan in stran je bila 43 kB naštevanja -- tabela, ki je nihče ne
#: prebere do konca, ni vsebina. Kdor hoče ves dan, ima iskalnik.
NAJVEC_ODHODOV = 24

#: Koliko relacij se ponudi na strani postaje in ob relaciji. Več kot toliko
#: povezav v vrsti je seznam, ne predlog.
POVEZAV = 8

_NI_CRKA = re.compile(r"[^a-z0-9]+")


def slug(ime: str) -> str:
    """Ime postaje -> del naslova: 'Ljubljana Železna' -> 'ljubljana-zelezna'.

    Šumnike zlaga isto kot iskalnik (`journey._fold`): kdor v naslov natipka
    „zelezna" brez strešice, mora priti na isto stran kot povezava.
    """
    return _NI_CRKA.sub("-", journey._fold(ime)).strip("-")


# ---------------------------------------------------------------- povzetek

_IZBOR_SQL = """
WITH p AS (
  SELECT s.trip_id, s.stop_seq, st.name
  FROM sched s
  JOIN station st ON st.stop_id = s.stop_id
  JOIN trip t ON t.trip_id = s.trip_id
  WHERE t.network = :net AND (:brez IS NULL OR t.agency <> :brez)
)
SELECT a.name AS od, b.name AS cilj, COUNT(*) AS vozenj
FROM p a
JOIN p b ON b.trip_id = a.trip_id AND b.stop_seq > a.stop_seq
GROUP BY a.name, b.name
HAVING vozenj >= :min_vozenj
ORDER BY vozenj DESC
"""

# Vožnje izbranih relacij. `a.stop_seq` je bar stolpec ob `MIN(b.stop_seq)` --
# sqlite zanj jamči vrstico, ki je dala minimum, torej prvi cilj za tem
# izhodiščem. Isto pravilo kot v `stats.connections()`: vožnja lahko postajo
# obišče dvakrat in šteje najzgodnejši par.
_PAR_SQL = """
WITH p AS (
  SELECT s.trip_id, s.stop_seq, st.name
  FROM sched s
  JOIN station st ON st.stop_id = s.stop_id
  JOIN trip t ON t.trip_id = s.trip_id
  WHERE t.network = :net AND (:brez IS NULL OR t.agency <> :brez)
)
INSERT INTO _par (od, cilj, trip_id, od_seq, cilj_seq)
SELECT i.od, i.cilj, a.trip_id, a.stop_seq, MIN(b.stop_seq)
FROM _izbor i
JOIN p a ON a.name = i.od
JOIN p b ON b.trip_id = a.trip_id AND b.name = i.cilj AND b.stop_seq > a.stop_seq
GROUP BY i.od, i.cilj, a.trip_id
"""

#: Zamuda v ZAOKROŽENI minuti, izračunana v sqlite in brez `floor()`.
#: `floor()` je v sqlite del matematičnih funkcij, ki jih ni v vsaki izdaji;
#: celoštevilsko deljenje pa reže proti ničli in bi pri prezgodnji vožnji
#: (−100 s) dalo −1 namesto −2. Zamik za en dan naredi števec zanesljivo
#: pozitiven -- zamude so omejene z `MAX_REALNA_ZAMUDA_S` -- in deljenje je
#: spet isto kot `floor(x + 0,5)` v `stats._minute()`.
MINUTA = "(COALESCE(r.delay_dep, r.delay_arr) + 30 + 86400) / 60 - 1440"

# Zamuda ob prihodu na CILJ relacije, kot histogram po zaokroženi minuti.
# Histogram in ne seznam sekund: razred zamude se tako ali tako določi iz
# minute (`stats._razred_zamude`), torej je natanko tako natančen kot prikaz --
# in ne potegne dveh milijonov vrstic v pomnilnik.
_ZAMUDE_RELACIJ_SQL = f"""
SELECT p.od, p.cilj,
       {MINUTA} AS minuta, COUNT(*) AS n
FROM _par p
JOIN run r ON r.trip_id = p.trip_id AND r.stop_seq = p.cilj_seq
WHERE r.service_date >= :since
  AND COALESCE(r.delay_dep, r.delay_arr) IS NOT NULL
  AND ABS(COALESCE(r.delay_dep, r.delay_arr)) <= {stats.MAX_REALNA_ZAMUDA_S}
GROUP BY p.od, p.cilj, minuta
"""

_TRAJANJE_SQL = """
SELECT p.od, p.cilj,
       COALESCE(sb.arr_s, sb.dep_s) - COALESCE(sa.dep_s, sa.arr_s) AS trajanje
FROM _par p
JOIN sched sa ON sa.trip_id = p.trip_id AND sa.stop_seq = p.od_seq
JOIN sched sb ON sb.trip_id = p.trip_id AND sb.stop_seq = p.cilj_seq
WHERE trajanje > 0
"""

# Zamuda na postanku, po postaji. Ista oblika kot pri relacijah in iz istega
# razloga histogram.
_ZAMUDE_POSTAJ_SQL = f"""
SELECT st.name AS ime,
       {MINUTA} AS minuta, COUNT(*) AS n
FROM run r
JOIN trip t ON t.trip_id = r.trip_id AND t.network = :net
JOIN sched s ON s.trip_id = r.trip_id AND s.stop_seq = r.stop_seq
JOIN station st ON st.stop_id = s.stop_id
WHERE r.service_date >= :since
  AND COALESCE(r.delay_dep, r.delay_arr) IS NOT NULL
  AND ABS(COALESCE(r.delay_dep, r.delay_arr)) <= {stats.MAX_REALNA_ZAMUDA_S}
GROUP BY st.name, minuta
"""


def _kvantil(minute: list[int], hist: dict[int, int], n: int, q: float) -> float:
    """Kvantil iz histograma, z ISTO definicijo kot `stats._pct()`.

    Dve definiciji kvantila na istih straneh bi pomenili, da „p90 20 min" na
    lestvici in „p90 20 min" na relaciji nista primerljiva -- in bralec tega
    ne more vedeti.
    """
    k = (n - 1) * q
    lo_i, hi_i = int(k), min(int(k) + 1, n - 1)
    vrednosti = []
    for meja in (lo_i, hi_i):
        tek = 0
        for m in minute:
            tek += hist[m]
            if tek > meja:
                vrednosti.append(m)
                break
    lo, hi = vrednosti
    return round(lo + (hi - lo) * (k - lo_i), 1)


def _iz_histograma(hist: dict[int, int]) -> dict:
    """Mediana, p90 in delež točnih iz histograma minut."""
    n = sum(hist.values())
    minute = sorted(hist)
    tocnih = sum(c for m, c in hist.items() if m <= stats.ON_TIME_MIN)
    median = _kvantil(minute, hist, n, 0.5)
    return {
        "meritev": n,
        "median_min": median,
        "p90_min": _kvantil(minute, hist, n, 0.9),
        "tocnih": round(tocnih / n, 3),
        # Odlocitev o zamudi gre z vrstico vred in jo naredi `opis_zamude()`:
        # razred, minuta in beseda so pravilo, ne oblikovanje, in ne smejo
        # nastati drugic v predlogi (glej .claude/rules/strezba.md).
        "zamuda": stats.opis_zamude(round(median * 60)),
    }


def zgradi(conn: sqlite3.Connection, days: int = 90,
           network: str | None = "zeleznica") -> dict:
    """Kazalo pristajalnih strani enega omrežja. Gradilnik povzetka.

    Vrne `{"relacije": [...], "postaje": [...]}`, urejeno po prometu. Vsaka
    vrstica nosi tudi, koliko meritev stoji za njeno številko -- brez tega
    stran ne more povedati, koliko naj ji bralec verjame.
    """
    network = network or "zeleznica"
    since = (datetime.now(TZ).date() - timedelta(days=days)).isoformat()
    brez = BREZ_AGENCIJE if network == "avtobus" else None
    par = {"net": network, "brez": brez, "since": since}

    lege = {d["n"]: (d["lat"], d["lon"])
            for d in journey.station_index(conn, network, True)}
    promet = {d["n"]: d["t"] for d in journey.station_index(conn, network)}

    # ---- kateri pari sploh pridejo v poštev
    kandidati = []
    for r in conn.execute(_IZBOR_SQL,
                          {**par, "min_vozenj": MIN_VOZENJ.get(network, 10)}):
        a, b = r["od"], r["cilj"]
        if a not in lege or b not in lege:
            continue
        m = geo.haversine(*lege[a], *lege[b])
        if m < MIN_RAZDALJA_M.get(network, 3000):
            continue
        kandidati.append({"od": a, "cilj": b, "vozenj": r["vozenj"],
                          "km": round(m / 1000, 1)})
        if len(kandidati) >= NAJVEC_RELACIJ:
            break

    # ---- vožnje teh relacij v ločeno tabelo, da jo vprašamo dvakrat
    conn.execute("CREATE TEMP TABLE IF NOT EXISTS _izbor (od TEXT, cilj TEXT)")
    conn.execute("CREATE TEMP TABLE IF NOT EXISTS _par "
                 "(od TEXT, cilj TEXT, trip_id TEXT, od_seq INT, cilj_seq INT)")
    conn.execute("DELETE FROM _izbor")
    conn.execute("DELETE FROM _par")
    conn.executemany("INSERT INTO _izbor (od, cilj) VALUES (?, ?)",
                     [(k["od"], k["cilj"]) for k in kandidati])
    conn.execute(_PAR_SQL, par)

    trajanja: dict[tuple, list[int]] = {}
    for r in conn.execute(_TRAJANJE_SQL):
        trajanja.setdefault((r["od"], r["cilj"]), []).append(r["trajanje"])

    zamude: dict[tuple, dict[int, int]] = {}
    for r in conn.execute(_ZAMUDE_RELACIJ_SQL, par):
        zamude.setdefault((r["od"], r["cilj"]), {})[r["minuta"]] = r["n"]

    relacije = []
    for k in kandidati:
        kljuc = (k["od"], k["cilj"])
        t = trajanja.get(kljuc)
        vrstica = {
            **k,
            "od_pot": slug(k["od"]), "cilj_pot": slug(k["cilj"]),
            "trajanje_s": int(statistics.median(t)) if t else None,
            "meritev": 0, "median_min": None, "p90_min": None, "tocnih": None,
        }
        h = zamude.get(kljuc)
        if h:
            vrstica.update(_iz_histograma(h))
        relacije.append(vrstica)

    # ---- postaje
    po_postaji: dict[str, dict[int, int]] = {}
    for r in conn.execute(_ZAMUDE_POSTAJ_SQL, par):
        po_postaji.setdefault(r["ime"], {})[r["minuta"]] = r["n"]

    postaje = []
    for ime, t in sorted(promet.items(), key=lambda kv: (-kv[1], kv[0])):
        vrstica = {"ime": ime, "pot": slug(ime), "postankov": t,
                   "meritev": 0, "median_min": None, "p90_min": None,
                   "tocnih": None}
        h = po_postaji.get(ime)
        if h:
            vrstica.update(_iz_histograma(h))
        postaje.append(vrstica)
        if len(postaje) >= NAJVEC_POSTAJ:
            break

    dnevi = [r["d"] for r in conn.execute(
        "SELECT DISTINCT service_date AS d FROM run WHERE service_date >= ? "
        "ORDER BY d", (since,))]

    # **Bralno transakcijo je treba zapreti, preden klicatelj piše.** V WAL je
    # bralec priklenjen na posnetek baze ob prvem branju; pisanje v isti
    # transakciji potem, ko je zajem medtem zapisal svoje, odpove s
    # „database is locked" -- in to je SQLITE_BUSY_SNAPSHOT, ki ga čakanje NE
    # reši. Pri avtobusih je branje petnajst sekund, torej je vmesni zapis
    # zajema skoraj gotov. Vsebina temp tabel gre s tem stran, a je ne rabimo
    # več.
    conn.rollback()
    return {"relacije": relacije, "postaje": postaje, "days": dnevi,
            "runs": sum(r["meritev"] for r in relacije)}


# ---------------------------------------------------------------- kazalo za strežbo

def kazalo(conn: sqlite3.Connection, network: str) -> dict:
    """Povzetek, dopolnjen s slovarjema za iskanje po naslovu.

    Ob dveh imenih z istim naslovom obvelja **prometnejše** -- vrstice so
    urejene po prometu in prvo ne prepišemo. Naključna izbira bi pomenila, da
    isti naslov enkrat pelje na eno in drugič na drugo postajo.
    """
    got = stats.summary_get(conn, "pristanek", network)
    po_relaciji, po_postaji = {}, {}
    for r in got.get("relacije", []):
        po_relaciji.setdefault((r["od_pot"], r["cilj_pot"]), r)
    for p in got.get("postaje", []):
        po_postaji.setdefault(p["pot"], p)
    return {**got, "po_relaciji": po_relaciji, "po_postaji": po_postaji}


def ime_postaje(conn: sqlite3.Connection, kaz: dict, pot: str,
                network: str) -> str | None:
    """Naslov -> ime postaje, ali `None`.

    Kazalo pozna samo vrh po prometu (`NAJVEC_POSTAJ`). Ostale postaje strani
    prav tako imajo -- samo v zemljevidu strani jih ni -- zato je za njih
    rezerva iskalnik, ki šumnike zlaga po istem pravilu kot `slug()`. Zadetek
    velja le, če se naslov **natanko** vrne: sicer bi `/postaja/karkoli`
    postregla najbližjo postajo in iskalnikom odprla neskončen prostor.
    """
    zapis = kaz["po_postaji"].get(pot)
    if zapis:
        return zapis["ime"]
    for hit in journey.search_stations(conn, pot.replace("-", " "), limit=5,
                                       network=network):
        if slug(hit["name"]) == pot:
            return hit["name"]
    return None


def sosednje(kaz: dict, ime: str, razen: str | None = None) -> list[dict]:
    """Relacije s te postaje -- povezave, po katerih se pride naprej.

    Brez njih je vsaka stran slepa ulica: obiskovalec nima kam, iskalnik pa
    strani, do katere ne vodi nobena povezava, skoraj ne obišče.
    """
    out = [r for r in kaz["relacije"]
           if r["od"] == ime and r["cilj"] != razen]
    return out[:POVEZAV]


def _dopolni_obicajno(vrstice: list[dict], polje: str) -> None:
    """Vožnjam brez meritve pripiše, koliko so zamujale doslej.

    Brez tega ima stolpec zamude pri jutranjem vlaku pomišljaj -- in to je za
    obiskovalca isto kot prazna stran, čeprav o tej vožnji vemo osemnajst
    prejšnjih. Vrednost **ni napoved za ta dan** in stran jo tako tudi
    imenuje („običajno"); pravilo je iz `stats.typical_at_stops()`.
    """
    for v in vrstice:
        t = v.get(polje)
        v["obicajno"] = (stats.opis_zamude(round(t["median_s"]))
                         if v.get("zamuda") is None and t else None)


def relacija(conn: sqlite3.Connection, kaz: dict, od: str, cilj: str,
             network: str, datum: str, now_s: int | None) -> dict:
    """Vse, kar potrebuje stran ene relacije."""
    zapis = kaz["po_relaciji"].get((slug(od), slug(cilj)))
    zveze = stats.connections(conn, od, cilj, datum, now_s, network)
    _dopolni_obicajno(zveze, "typical_arr")

    # **Kar je odpeljalo, potniku ne pomaga.** Prva različica je izpisala prvih
    # 24 voženj dneva -- na relaciji Medvode → Ljubljana Šentvid (138 voženj)
    # je bilo to ob pol treh popoldne naštevanje odhodov med 04:52 in 07:28.
    # Kadar danes ni več ničesar (pozno zvečer), ostane dan od začetka: prazna
    # tabela je slabša od včerajšnje ure, ki je vsaj vozni red.
    zdaj = datetime.now(TZ)
    odslej = [z for z in zveze
              if z["sched_dep"] and datetime.fromisoformat(z["sched_dep"]) >= zdaj]
    prikaz = odslej or zveze
    return {
        "od": od, "cilj": cilj, "network": network, "datum": datum,
        "zapis": zapis, "zveze": prikaz[:NAJVEC_ODHODOV], "vseh": len(zveze),
        "odslej": bool(odslej),
        "obratno": kaz["po_relaciji"].get((slug(cilj), slug(od))),
        "naprej": sosednje(kaz, od, razen=cilj),
        "iz_cilja": sosednje(kaz, cilj, razen=od),
        "izracunano": kaz.get("computed_at"),
        # V zemljevid strani gredo samo relacije iz kazala. Kar je zunaj njega,
        # ostane dosegljivo, a `noindex` -- sicer je prostor naslovov
        # neskončen (26 049 parov pri avtobusih) in iskalnik ga bo prehodil.
        "indeksiraj": zapis is not None,
    }


def postaja(conn: sqlite3.Connection, kaz: dict, ime: str, network: str,
            datum: str, now_s: int, smer: str | None = None) -> dict:
    """Vse, kar potrebuje stran ene postaje.

    `smer` je stran ceste (`journey.smeri_postaje`) -- ista izbira kot na
    odhodni tabli, le da tu kot povezava, ker stran nima JS. Izbrana smer ne
    spremeni kanonicnega naslova: to je ista stran, samo ozja.
    """
    zapis = kaz["po_postaji"].get(slug(ime))
    smeri = journey.smeri_postaje(conn, ime, network) if network == "avtobus" else []
    izbrana = journey.smer_za(smeri, smer)
    # Eden več od prikazanih: brez tega stran ne more ločiti „toliko jih je"
    # od „toliko jih kažemo", in prvo je za potnika drug odgovor.
    odhodi = journey.board(conn, ime, datum, now_s, window_min=180,
                           kind="odhodi", limit=NAJVEC_ODHODOV + 1,
                           network=network, now_s=now_s,
                           stop_ids=set(izbrana["stop_ids"]) if izbrana else None)
    _dopolni_obicajno(odhodi, "typical")
    return {
        "ime": ime, "network": network, "datum": datum,
        "smeri": smeri if len(smeri) > 1 else [],
        "smer": izbrana["kljuc"] if izbrana else None,
        "zapis": zapis, "odhodi": odhodi[:NAJVEC_ODHODOV],
        "vseh": len(odhodi),
        "naprej": sosednje(kaz, ime),
        "izracunano": kaz.get("computed_at"),
        "indeksiraj": zapis is not None,
    }


def besedilo(z: dict | None) -> str:
    """Zamuda kot beseda, isto kot `common.delayText()` v brskalniku.

    Pri prezgodnji vožnji **beseda, ne minus**: „3 min prej" in ne „−3 min".
    Minus pred številko je uganka -- pravilo je v `.claude/rules/oznake.md`.
    """
    if not z:
        return "ni podatka"
    m = z["min"]
    if m <= -1:
        return f"{-m} min prej"
    return f"{'+' if m > 0 else ''}{m} min"


def trajanje(sekund: int | None) -> str:
    """Sekunde -> „1 h 3 min". Ure se izpišejo šele, ko so."""
    if not sekund:
        return ""
    minut = round(sekund / 60)
    return f"{minut // 60} h {minut % 60} min" if minut >= 60 else f"{minut} min"


# ---------------------------------------------------------------- naslovi

def pot_relacije(network: str, od: str, cilj: str) -> str:
    """Naslov strani ene relacije. Omrežje je v poti in ne v parametru: naslov
    mora povedati, s čim greš -- isto pravilo kot pri `/app/train`."""
    koren = "avtobus" if network == "avtobus" else "vlak"
    return f"/{koren}/{slug(od)}/{slug(cilj)}"


def pot_postaje(network: str, ime: str) -> str:
    """Naslov strani ene postaje. Mestno je postajališče, železniška postaja --
    beseda je v naslovu, ker je v naslovu tudi omrežje."""
    koren = "postajalisce" if network == "avtobus" else "postaja"
    return f"/{koren}/{slug(ime)}"


def pot_vozje(network: str, train_no: str, trip_id: str | None = None) -> str:
    """Okno ene vožnje. `?trip=` je obvezen pri avtobusih: številka linije ni
    številka vožnje in LPP 3G ima 388 voženj."""
    koren = "/app/bus/" if network == "avtobus" else "/app/train/"
    naslov = koren + quote(train_no)
    return f"{naslov}?trip={quote(trip_id)}" if trip_id else naslov


def stevnik(n: int, ena: str, dve: str, tri: str, pet: str) -> str:
    """Slovenska oblika ob številu: 1 vožnja, 2 vožnji, 3 vožnje, 5 voženj.

    Brez tega piše „peljejo 39 voženj" in to je narobe -- pri petih in več je
    glagol v ednini in samostalnik v rodilniku. Odloča **zadnji dve števki**
    (101 je kot 1, 111 kot 5), ne cela številka.
    """
    o = n % 100
    if o == 1:
        return ena
    if o == 2:
        return dve
    if o in (3, 4):
        return tri
    return pet


def stevilo(n: int | None) -> str:
    """Tisočice z nedeljivim presledkom: 1671 -> „1 671".

    Tako so številke zapisane povsod drugje v tem projektu; brez tega je
    „1671 postankih" videti kot letnica.
    """
    return "" if n is None else f"{n:,}".replace(",", "\u00a0")


def km(vrednost: float | None) -> str:
    """Razdalja po slovensko: 17.6 -> „17,6 km". Pika je angleška."""
    return "" if vrednost is None else f"{vrednost:.1f}".replace(".", ",") + " km"
