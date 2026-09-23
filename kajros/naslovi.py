"""Iskanje po naslovu, ulici, kraju in imenu — iz lastnega kazala.

Najhitrejša pot se začne pri točki, ne pri postaji, in človek točko pozna po
naslovu: „Trubarjeva 5", „BTC", „Vič". Brez tega je moral hišo zadeti na
zemljevidu, kar je na telefonu klik, ki hiše ne zadene.

**Zakaj lastno kazalo in ne geokodirnik.** Tuji ponudnik (Nominatim, Google)
bi ob vsakem pritisku tipke izvedel, kam kdo gre — in prav temu se ta projekt
izogiba (`hoja.py`, isti razlog za lastni OSRM). Kazalo je izpeljano iz
OpenStreetMap (ODbL), kjer so hišne številke GURS uvožene za vso državo:
**815 060 hišnih številk** v izvozu 23. 9. 2026.

**Svoja datoteka, ne tabela v bazi zajema.** Gradi se na nekaj mesecev iz
izvoza OSM (`deploy/naslovi.sh`), baza zajema pa se vleče z maline in bi ga
ob vsaki vleki izgubila. Kadar datoteke ni, iskanje vrne prazno in stran
išče samo po postajah, kot prej.
"""

from __future__ import annotations

import json
import math
import re
import sqlite3
import time
import unicodedata
from pathlib import Path

from . import config, geo

#: Kraji in kako težki so. Mesto pred vasjo istega imena, vas pred ledinskim
#: imenom: kdor vpiše "Kamnik", misli mesto, ne zaselka.
KRAJI = {
    "city": ("mesto", 100), "town": ("mesto", 85),
    "suburb": ("del mesta", 60), "quarter": ("del mesta", 55),
    "village": ("naselje", 45), "neighbourhood": ("soseska", 40),
    "square": ("trg", 35), "hamlet": ("zaselek", 25),
    "locality": ("kraj", 12), "isolated_dwelling": ("domačija", 8), "farm": ("kmetija", 6),
}

#: Oznake OSM, ki imenovani stvari dajo pravico do mesta v kazalu. Postaj tu
#: ni: te ima aplikacija svoje, s prometom, in dve različici istega imena bi
#: se v seznamu tepli.
TOCKE = ("amenity", "shop", "tourism", "leisure", "office", "healthcare",
         "historic", "building", "craft", "sport", "man_made")
NARAVA = {"peak", "saddle", "beach", "cave_entrance", "spring", "waterfall"}
RABA = {"retail", "commercial", "industrial", "education", "religious", "cemetery"}

UTEZ_ULICA = 30
UTEZ_TOCKA = 25
UTEZ_NASLOV = 10

#: Koliko zadetkov iz besedilnega kazala gre v razvrščanje. Kazalo razvršča po
#: besedilu, mi po teži in razdalji -- zato jih vzamemo več, kot jih vrnemo.
KANDIDATOV = 400

_BESEDA = re.compile(r"[\w]+", re.UNICODE)


def fold(s: str) -> str:
    """Male črke brez strešic. Isto kot `common.fold()` v brskalniku."""
    return "".join(c for c in unicodedata.normalize("NFKD", s.lower())
                   if not unicodedata.combining(c))


def pot_kazala() -> Path:
    return Path(config.okolje("NASLOVI", str(config.DATA_DIR / "naslovi.sqlite")))


# ---------------------------------------------------------------- gradnja

def _sredisce(geom: dict) -> tuple[float, float] | None:
    """(lat, lon) točke, sredine črte ali težišča oboda. Za stavbo in trgovino
    je težišče dovolj natančno; za velike površine (BTC) je sredina območja
    boljša od roba."""
    t = geom.get("type")
    c = geom.get("coordinates")
    if not c:
        return None
    if t == "Point":
        return c[1], c[0]
    if t == "LineString":
        m = c[len(c) // 2]
        return m[1], m[0]
    if t == "Polygon":
        obod = c[0]
    elif t == "MultiPolygon":
        obod = max((p[0] for p in c), key=len)
    else:
        return None
    return (sum(p[1] for p in obod) / len(obod), sum(p[0] for p in obod) / len(obod))


class _Mreza:
    """Najbližji kraj po zračni črti -- za podnapis zadetka brez kraja."""

    def __init__(self, celica: float):
        self.celica = celica
        self.celice: dict[tuple[int, int], list] = {}

    def dodaj(self, lat, lon, ime):
        self.celice.setdefault((int(lat / self.celica), int(lon / self.celica)),
                               []).append((lat, lon, ime))

    def dodaj_mesto(self, lat, lon, ime, polmer_km):
        self.dodaj(lat, lon, (ime, polmer_km))

    def najblizji(self, lat, lon):
        """Ime najbližjega, ali `(ime, polmer)` pri mestih."""
        gy, gx = int(lat / self.celica), int(lon / self.celica)
        naj, najd = None, 1e18
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for la, lo, ime in self.celice.get((gy + dy, gx + dx), ()):
                    d = (la - lat) ** 2 + ((lo - lon) * 0.69) ** 2
                    if d < najd:
                        naj, najd = ime, d
        return naj

    def mesto_okrog(self, lat, lon) -> str | None:
        """Mesto, znotraj katerega točka leži (po polmeru), ali `None`.

        BTC nima kraja v naslovu in najbližja vas je Hrastje; človek pa reče
        "BTC v Ljubljani". Mesto zato prednjači, a samo v svojem polmeru --
        vas tri kilometre iz Kranja ni Kranj."""
        gy, gx = int(lat / self.celica), int(lon / self.celica)
        naj, najd = None, 1e18
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for la, lo, (ime, polmer) in self.celice.get((gy + dy, gx + dx), ()):
                    km = geo.haversine(lat, lon, la, lo) / 1000
                    if km <= polmer and km < najd:
                        naj, najd = ime, km
        return naj


def _brez_cetrtne(ime: str) -> str:
    """"Četrtna skupnost Jarše" je upravna enota, človek reče "Jarše". Isto
    je odrezano v slogu zemljevida (`podlaga.json`)."""
    return ime.removeprefix("Četrtna skupnost ")


def zgradi(vir: Path, cilj: Path, javi=print) -> dict:
    """Kazalo iz izvoza OSM v obliki GeoJSON Text Sequences.

    Izvoz naredi `osmium export -f geojsonseq` (`deploy/naslovi.sh`); tu ga
    samo beremo, da strežnik ne rabi knjižnice za PBF.
    """
    t0 = time.perf_counter()
    naslovi: dict[tuple, tuple] = {}
    ulice: dict[tuple, list] = {}
    kraji: list[tuple] = []
    tocke: list[tuple] = []
    # Naselja za podnapis točke ali naslova brez kraja, mesta za podnapis
    # vasi: "Vič" je dvakrat, in "naselje · Dravograd" pove, kateri.
    naselja = _Mreza(0.05)       # ~5 km
    mesta = _Mreza(0.15)         # ~15 km
    # Brez okolice (človek še ni povedal, kje je) je "Trubarjeva 5" najbolj
    # verjetno v mestu, kjer živi največ ljudi, ne v Laškem.
    velikost: dict[str, float] = {}
    with open(vir, encoding="utf-8") as f:
        for vrstica in f:
            vrstica = vrstica.lstrip("\x1e").strip()
            if not vrstica:
                continue
            o = json.loads(vrstica)
            p = o.get("properties") or {}
            ll = _sredisce(o.get("geometry") or {})
            if ll is None:
                continue
            hs = p.get("addr:housenumber")
            ulica = p.get("addr:street") or p.get("addr:place")
            if hs and ulica:
                kraj = p.get("addr:city") or (p.get("addr:place") if p.get("addr:street") else "")
                kljuc = (fold(ulica), fold(hs), fold(kraj or ""))
                if kljuc not in naslovi:
                    naslovi[kljuc] = (f"{ulica} {hs}", kraj or "", p.get("addr:postcode", ""), *ll)
                    if p.get("addr:street"):
                        ulice.setdefault((ulica, kraj or ""), []).append(ll)
            ime = p.get("name")
            if not ime:
                continue
            if p.get("place") in KRAJI:
                _, utez = KRAJI[p["place"]]
                beseda = KRAJI[p["place"]][0]
                kraji.append((_brez_cetrtne(ime), p["place"], beseda, utez, *ll))
                if p["place"] in ("city", "town", "village", "hamlet"):
                    naselja.dodaj(*ll, ime)
                if p["place"] in ("city", "town"):
                    # Polmer mesta po zračni črti od središča. Grobo, a mest je
                    # 75 in veliki sta dve: Ljubljana in Maribor.
                    mesta.dodaj_mesto(*ll, ime, 6.0 if p["place"] == "city" else 2.5)
                    velikost[ime] = 6 if p["place"] == "city" else 3
                continue
            if (any(k in p for k in TOCKE) or p.get("natural") in NARAVA
                    or p.get("landuse") in RABA):
                if "public_transport" in p or p.get("railway") in ("station", "halt", "stop"):
                    continue    # postaje so svoje kazalo
                tocke.append((ime, p.get("addr:city", ""), *ll))
    javi(f"  prebrano: {len(naslovi)} naslovov, {len(ulice)} ulic, "
         f"{len(kraji)} krajev, {len(tocke)} točk ({time.perf_counter() - t0:.0f} s)")

    cilj.parent.mkdir(parents=True, exist_ok=True)
    zacasna = cilj.with_suffix(".gradnja")
    zacasna.unlink(missing_ok=True)
    c = sqlite3.connect(zacasna)
    c.executescript("""
        CREATE TABLE zadetek(
            id INTEGER PRIMARY KEY, vrsta TEXT NOT NULL, ime TEXT NOT NULL,
            pod TEXT NOT NULL, utez REAL NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL);
        -- Dve kazali, ker sta dve vprašanji: brez številke človek išče ulico,
        -- kraj ali ime, s številko pa naslov. Eno samo kazalo bi za "ljub"
        -- premetalo sto tisoč ljubljanskih naslovov, da bi našlo mesto.
        CREATE VIRTUAL TABLE po_imenu USING fts5(
            besedilo, content='', tokenize='unicode61 remove_diacritics 2');
        CREATE VIRTUAL TABLE po_naslovu USING fts5(
            besedilo, content='', tokenize='unicode61 remove_diacritics 2');
        CREATE TABLE meta(kljuc TEXT PRIMARY KEY, vrednost TEXT);
    """)

    def vstavi(vrsta, ime, pod, utez, lat, lon, besedilo, kazalo):
        cur = c.execute("INSERT INTO zadetek(vrsta, ime, pod, utez, lat, lon) "
                        "VALUES(?,?,?,?,?,?)", (vrsta, ime, pod, utez, lat, lon))
        c.execute(f"INSERT INTO {kazalo}(rowid, besedilo) VALUES(?,?)",
                  (cur.lastrowid, besedilo))

    for ime, vrsta, beseda, utez, lat, lon in kraji:
        blizu = None if vrsta in ("city", "town") else mesta.najblizji(lat, lon)
        blizu = blizu[0] if blizu and blizu[0] != ime else None
        pod = f"{beseda} · {blizu}" if blizu else beseda
        vstavi("kraj", ime, pod, utez, lat, lon, ime, "po_imenu")
    for (ulica, kraj), lege in ulice.items():
        # Lega ulice je hiša, ki je najbližje težišču hišnih številk, ne
        # težišče samo: ulica z dvema krakoma ima težišče sredi njive.
        sl = sum(x[0] for x in lege) / len(lege)
        so = sum(x[1] for x in lege) / len(lege)
        lat, lon = min(lege, key=lambda x: (x[0] - sl) ** 2 + (x[1] - so) ** 2)
        kraj = kraj or mesta.mesto_okrog(lat, lon) or naselja.najblizji(lat, lon) or ""
        vstavi("ulica", ulica, kraj,
               UTEZ_ULICA + math.log10(len(lege)) * 5 + velikost.get(kraj, 0),
               lat, lon, f"{ulica} {kraj}", "po_imenu")
    for ime, kraj, lat, lon in tocke:
        kraj = kraj or mesta.mesto_okrog(lat, lon) or naselja.najblizji(lat, lon) or ""
        vstavi("tocka", ime, kraj, UTEZ_TOCKA + velikost.get(kraj, 0), lat, lon,
               f"{ime} {kraj}", "po_imenu")
    for ime, kraj, posta, lat, lon in naslovi.values():
        kraj = kraj or mesta.mesto_okrog(lat, lon) or naselja.najblizji(lat, lon) or ""
        pod = f"{posta} {kraj}".strip()
        vstavi("naslov", ime, pod, UTEZ_NASLOV + velikost.get(kraj, 0), lat, lon,
               f"{ime} {kraj} {posta}", "po_naslovu")
    c.execute("INSERT INTO meta VALUES('zgrajeno', ?)", (time.strftime("%Y-%m-%d %H:%M"),))
    c.execute("INSERT INTO meta VALUES('vir', ?)", (str(vir),))
    c.commit()
    c.execute("INSERT INTO po_imenu(po_imenu) VALUES('optimize')")
    c.execute("INSERT INTO po_naslovu(po_naslovu) VALUES('optimize')")
    c.commit()
    c.execute("VACUUM")
    c.close()
    zacasna.replace(cilj)
    return {"naslovov": len(naslovi), "ulic": len(ulice), "krajev": len(kraji),
            "tock": len(tocke), "mb": round(cilj.stat().st_size / 1e6, 1),
            "s": round(time.perf_counter() - t0)}


# ---------------------------------------------------------------- iskanje

_POVEZAVA: dict[str, sqlite3.Connection] = {}


def _povezava() -> sqlite3.Connection | None:
    pot = pot_kazala()
    if not pot.exists():
        return None
    kljuc = f"{pot}:{pot.stat().st_mtime_ns}"
    c = _POVEZAVA.get(kljuc)
    if c is None:
        # Samo za branje in brez niti-straže: kazalo se med tekom ne piše,
        # zamenja se kot datoteka -- in takrat ključ z `mtime` odpre novo.
        c = sqlite3.connect(f"file:{pot}?mode=ro", uri=True, check_same_thread=False)
        # Stare povezave ne zapiramo: nit, ki na njej ravno išče, bi dobila
        # napako. Pobere jo zbiralnik smeti (povezava ima krožne reference,
        # zato ne takoj ob `clear()`, ampak ob naslednjem `gc` -- preverjeno z
        # `/proc/self/fd`, 23. 9. 2026).
        _POVEZAVA.clear()
        _POVEZAVA[kljuc] = c
    return c


def _poizvedba(besede: list[str]) -> str:
    # Vsaka beseda kot predpona in v narekovajih: brez njih bi "in" ali "or"
    # FTS prebral kot ukaz. Hišna številka pa ne kot predpona: "50*" ujame
    # poštno številko 5000 in s tem vso Novo Gorico, in pravi naslov je
    # izpadel iz prvih 400 (izmerjeno na "slovenska 50", 23. 9. 2026).
    return " ".join(f'"{b}"' if b[0].isdigit() else f'"{b}"*' for b in besede)


def isci(q: str, blizu: tuple[float, float] | None = None, najvec: int = 8) -> list[dict]:
    """Zadetki za niz `q`, razvrščeni po teži, ujemanju in bližini.

    `blizu` je točka, okrog katere človek išče (drugi konec poti ali sredina
    zemljevida). Brez nje "Trubarjeva" pomeni katerokoli Trubarjevo; z njo
    tisto, ki je blizu.
    """
    c = _povezava()
    besede = [b for b in _BESEDA.findall(fold(q)) if b]
    if c is None or not besede or len("".join(besede)) < 2:
        return []
    stevilka = next((b for b in besede if b[0].isdigit()), None)
    kandidati = set()
    kazala = ["po_imenu"] + (["po_naslovu"] if stevilka else [])
    osnova = ("SELECT z.id, z.vrsta, z.ime, z.pod, z.utez, z.lat, z.lon FROM {k} k "
              "JOIN zadetek z ON z.id = k.rowid WHERE {k} MATCH ?")
    for kazalo in kazala:
        sql = osnova.format(k=kazalo)
        try:
            kandidati.update(c.execute(sql + " ORDER BY rank LIMIT ?",
                                       (_poizvedba(besede), KANDIDATOV)))
            # Okolica posebej: "cesta 1" ima tisoče zadetkov in razvrščanje
            # po besedilu bi bližnjega odrezalo, preden bi razdalja prišla na
            # vrsto.
            if blizu:
                kandidati.update(c.execute(
                    sql + " AND z.lat BETWEEN ? AND ? AND z.lon BETWEEN ? AND ? LIMIT ?",
                    (_poizvedba(besede), blizu[0] - 0.2, blizu[0] + 0.2,
                     blizu[1] - 0.3, blizu[1] + 0.3, KANDIDATOV)))
        except sqlite3.OperationalError:
            continue

    niz = " ".join(besede)
    ocenjeni = []
    for _, vrsta, ime, pod, utez, lat, lon in kandidati:
        f_ime = fold(ime)
        tocka = utez
        # Ujemanje besedila šteje manj od bližine. "Trubarjeva 5" je v Laškem
        # ime do črke, v Ljubljani pa "Trubarjeva cesta 5" -- in kdor išče
        # iz Ljubljane, misli ljubljansko. Z večjo težo ujemanja je bilo Laško
        # prvo (23. 9. 2026).
        if vrsta != "naslov" and f_ime == niz:
            tocka += 20
        elif vrsta != "naslov" and f_ime.startswith(niz):
            tocka += 12
        # Beseda poizvedbe, ki je začetek besede v imenu, in ne le kjerkoli --
        # "ljubljana" v podnapisu ne sme dvigniti vseh ljubljanskih naslovov.
        besede_imena = _BESEDA.findall(f_ime)
        tocka += 8 * sum(any(w.startswith(b) for w in besede_imena) for b in besede)
        if stevilka and vrsta == "naslov":
            hs = besede_imena[-1] if besede_imena else ""
            tocka += 40 if hs == stevilka else (-15 if not hs.startswith(stevilka) else 0)
        if blizu:
            km = geo.haversine(blizu[0], blizu[1], lat, lon) / 1000
            tocka += 45 - 18 * math.log10(1 + km)
        ocenjeni.append((-tocka, vrsta, ime, pod, lat, lon))
    ocenjeni.sort()

    out = []
    for _, vrsta, ime, pod, lat, lon in ocenjeni:
        # Isti naslov je v OSM pogosto dvakrat (točka in stavba, enkrat s
        # krajem, enkrat brez) -- dvojnik je isto ime v nekaj sto metrih. Pri
        # krajih in ulicah je razdalja večja: "Vič" je v OSM dvakrat, kot del
        # mesta in kot četrtna skupnost, 1,1 km narazen.
        prag = 300 if vrsta in ("naslov", "tocka") else 3000
        if any(o["vrsta"] == vrsta and fold(o["ime"]) == fold(ime)
               and geo.haversine(o["lat"], o["lon"], lat, lon) < prag for o in out):
            continue
        out.append({"vrsta": vrsta, "ime": ime, "pod": pod,
                    "lat": round(lat, 6), "lon": round(lon, 6)})
        if len(out) >= najvec:
            break
    return out
