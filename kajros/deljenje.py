"""Deljenje lege potnikov — kdor se pelje, pove, kje je vozilo.

Zakaj to sploh obstaja: **prehoda vlaka se iz feeda ne da ugotoviti.** Pet
signalov je izmerjenih in vsi odpovejo (`docs/MERITVE.md`); feed prehod pri
železnici potrdi v 0,4 % postankov. Vlak, ki čaka na prejšnji postaji, je
zato na tabli „odpeljal“, potnik pa stoji na peronu. Resnico ima samo človek,
ki je na vlaku — in ta ima v žepu GPS.

Potek:

1. potnik pošlje svojo lego, **brez** vožnje; strežnik vrne kandidate
   (`kandidati()`): vožnje, katerih trasa gre mimo in bi po voznem redu in
   zadnji zamudi morale biti ravno tu;
2. potnik izbere svojo (ne vpisuje je — potrdi ali izbere med kandidati);
3. od tedaj pošilja točke (`sprejmi()`), dokler ne izstopi ali vožnja ne
   pride na cilj.

**Kaj se hrani.** Točka se projicira na traso potrjene vožnje in shrani kot
razdalja vzdolž nje, čas, hitrost in natančnost — **brez surovih koordinat**.
Za model (vozni časi med postajami, postanki, prehodi) je to enako dobro, ker
vozilo s trase ne gre; lega potnika pred potrditvijo in lega ob strani trase
se ne zapišeta nikoli. Deljenje ima naključen id, ki ni povezan ne z obiskom
ne z naslovom IP; z njim ločimo sledi in štejemo neodvisne poročevalce.

**Kaj se pokaže** (odločil David, 25. 9. 2026):

* **en poročevalec** — prikaz pokaže feed IN poročilo, vsakega s svojo
  oznako. En sam telefon lahko laže ali se moti;
* **dva ali več, ki se ujemata** — feed za lego in prehod ni več potreben;
  poročilo zamenja „po zadnjem podatku bi odpeljal …, potrditve ni“. To velja
  le, dokler so poročila sveža (`SVEZE_S`); ko vsi nehajo deliti, se vrne feed.

**Varovalke.** API nima avtentikacije, zato mora vsaka točka dokazati, da je
na trasi vožnje, ki jo trdi (`ODMIK_MAX_M`), in se premikati kot vozilo
(`HITROST_MAX_MS`). Deljenja ni mogoče začeti za vožnjo, ki ta hip ni blizu.
Omejitve pogostosti tečejo v pomnilniku nad zgoščeno vrednostjo naslova, kot
pri `stik.py`; dnevna stropa čez vse sta v bazi.
"""
from __future__ import annotations

import json
import math
import secrets
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from . import config, db, geo, stats

TZ = ZoneInfo(config.TIMEZONE)

#: Kako pogosto odjemalca pošiljata točke (`deli.js`, `Deljenje.POSLJI_MS`).
#: Bilo je 10 s; na 5 s od 1. 10. 2026, da mali zemljevid, ki vpraša na
#: toliko, kaže lego, staro povprečno 5 s namesto 20 s. Točke se nabirajo
#: gosteje (brskalnik na 3 s, Android na 5 s), pošiljanje jih le pobere.
POSILJANJE_S = 5
#: Poročilo, starejše od tega, ne opisuje več, kje je vozilo zdaj. To je 24
#: zamujenih pošiljanj: dovolj za krajši predor, ne za potnika, ki je nehal.
SVEZE_S = 120

#: Koliko sta lahko dve poročili narazen, da se „ujemata“. Primerjamo zamudo
#: in ne lege: dve točki iz različnih trenutkov sta na različnih krajih, a
#: izpeljana zamuda je ista. Dve minuti je dvakrat ločljivost feeda.
SOGLASJE_S = 120

#: Točka dlje od trase ni na tem vozilu. Trasa je poenostavljena na ~10 m,
#: GPS v vlaku ima tipično 5--30 m, ob postaji s streho tudi 50.
ODMIK_MAX_M = 200
#: Točk s slabšo natančnostjo ne shranimo in z njimi ne sklepamo -- a tudi ne
#: štejejo kot izstop: v predoru je natančnost slaba, potnik pa je še vedno
#: na vlaku.
NATANCNOST_MAX_M = 250
#: Toliko zaporednih natančnih točk izven trase ali odmaknjenih med stanjem
#: (`VSTRAN_M`) pomeni, da je potnik izstopil.
ZUNAJ_ZA_IZSTOP = 3
#: 250 km/h. Hitreje ne vozi nič na tej mreži; skok čez to je napaka GPS.
HITROST_MAX_MS = 70
#: Nazaj po trasi toliko ali več ni šum, ampak napačna projekcija.
NAZAJ_MAX_M = 300
#: Pod to hitrostjo vozilo stoji.
STOJI_MS = 1.5
#: Kako blizu postaje vozilo „je na postaji“. Vlak je dolg do 200 m in
#: koordinata postaje ni nujno sredina perona; avtobus stoji na točki.
NA_POSTAJI_M = {"zeleznica": 200, "avtobus": 60}
#: Nad to hitrostjo med dvema točkama se vozilo pelje; pod njo stoji ali
#: potnik hodi. Prehod čez rob postaje šteje samo, kadar se je poročevalec
#: čez rob peljal. Izmerjeno 1. 10. 2026 na prvih 14 prehodih (hitrost
#: odseka med točkama, v katerem je rob): pravi 4,6--22,5 m/s, edini lažni
#: 1,8 m/s -- potnik RG 318 je po izstopu v Ljubljani hodil po peronu in
#: vlak „odpeljal“.
VOZI_MS = 3
#: Vozilo, ki stoji, se od trase vstran ne odmika, potnik, ki hodi, pa se.
#: Kdor se med stanjem odmakne od odmika ob ustavitvi za več od tega in obeh
#: natančnosti, ni več na vozilu. Samo z natančnimi točkami (do te meje):
#: točka ±200 m je na vlaku, ki je stal, skočila 150 m vstran (LPV 2010,
#: Ljubljana Zalog). Izmerjeno 1. 10. 2026 na prvih deljenjih: na vozilu je
#: bilo do meje najmanj 16 m (štirje postanki), po izstopu jo je potnik
#: RG 318 prešel po treh minutah hoje po peronu, potnik LPV 2010 v Kresnicah
#: pa za 84 m. Brez tega je izstopivši potnik še 10 minut „stal“ na postaji
#: kot vlak z rastočo zamudo: točke 150--185 m od proge so pod mejo izven
#: trase (`ODMIK_MAX_M`) in vsaka je števec izstopa vrnila na nič.
VSTRAN_M = 40
#: Najmanjši razmik med dvema točkami istega deljenja. Pogosteje ne prinese
#: nič novega, bazo pa polni.
RAZMIK_S = 3
#: Deljenje, daljše od tega, se konča samo. Najdaljša vožnja v Sloveniji
#: (EC čez državo z zamudo) ne traja toliko.
NAJDALJE_S = 6 * 3600

#: Kandidat: kako daleč od trase sme biti potnik ob prvi točki.
KANDIDAT_ODMIK_M = 250
#: Kandidat: za koliko je lahko vozilo po voznem redu in zadnji zamudi še
#: pred potnikovo lego (pride šele) oziroma že za njo (feed zamude ni osvežil
#: -- prav ta primer je razlog za vse skupaj). Zato je okno nesimetrično.
KANDIDAT_PRED_S = 15 * 60
KANDIDAT_ZA_S = 45 * 60
#: Postaje, med katerimi iščemo kandidate. Vlak je lahko 10 km od najbližje
#: postaje (Postojna--Divača); avtobus ima postajališče na vsakih nekaj sto
#: metrov, medkrajevni pa je lahko tudi 5 km od njega (avtocesta). Zato pri
#: avtobusih dva koraka: najprej blizu, in samo če tam ni nič, širše. V
#: Ljubljani je v 6 km ~1 500 postajališč in poizvedba je bila na arwenu
#: večji del od 1,75 s; pri 2,5 km so bili zgrešeni 14 od 150 avtobusov,
#: pri 6 km 7.
KANDIDAT_POLMER_M = {"zeleznica": 12000, "avtobus": 2500}
KANDIDAT_POLMER_SIRSE_M = {"avtobus": 6000}
#: Avtobus z GPS lego, oddaljeno več od tega, ni potnikov avtobus.
KANDIDAT_GPS_M = 600
#: Največ kandidatov v odgovoru; potnik izbira med njimi z dotikom.
KANDIDATOV = 5

#: Omejitve pogostosti na pošiljatelja (v pomnilniku, glej `stik.py`).
KANDIDATI_NA_MINUTO = 20
DELJENJ_NA_URO = 12
#: Dnevna stropa čez vse. Točke pridejo na 3--5 s (brskalnik na 3, Android
#: na 5; izmerjeno na prvih deljenjih), torej 720--1 200 na uro: strop je
#: ~300 potnikovih ur na dan.
TOCK_NA_DAN = 350_000
DELJENJ_NA_DAN = 3000
#: Točk v eni zahtevi. Android jih pošlje več naenkrat, kadar je bil brez
#: povezave (predor).
TOCK_NA_ZAHTEVO = 60

SHEMA = """
-- Eno deljenje: en potnik na eni vožnji. `id` je naključen in ni povezan z
-- obiskom ali naslovom IP. Zadnje stanje je tu, da prikaz ne bere točk.
CREATE TABLE IF NOT EXISTS deljenje (
    id           TEXT PRIMARY KEY,
    trip_id      TEXT NOT NULL,
    service_date TEXT NOT NULL,
    network      TEXT NOT NULL,
    zacetek_ts   INTEGER NOT NULL,
    zadnja_ts    INTEGER NOT NULL,   -- zadnja sprejeta točka
    along_m      REAL,               -- lega vzdolž trase
    lat          REAL,               -- ista lega NA TRASI, ne potnikova
    lon          REAL,
    hitrost_ms   REAL,
    zamuda_s     INTEGER,            -- izpeljana iz zadnje točke
    tock         INTEGER NOT NULL DEFAULT 0,
    zunaj        INTEGER NOT NULL DEFAULT 0,  -- zaporedne točke izven trase
    konec        TEXT                -- izstop | cilj | cas | potnik
);
CREATE INDEX IF NOT EXISTS deljenje_voznja ON deljenje(trip_id, zadnja_ts);
CREATE INDEX IF NOT EXISTS deljenje_zacetek ON deljenje(zacetek_ts);

-- Točke, projicirane na traso. Surovih koordinat ni: vozilo s trase ne gre,
-- razdalja vzdolž nje pa je vse, kar model rabi.
CREATE TABLE IF NOT EXISTS deljenje_tocka (
    deljenje     TEXT NOT NULL,
    ts           INTEGER NOT NULL,
    along_m      REAL NOT NULL,
    odmik_m      REAL NOT NULL,
    natancnost_m REAL,
    hitrost_ms   REAL,
    PRIMARY KEY (deljenje, ts)
);

-- Izpeljano iz točk: kdaj je vozilo prišlo na postajo in odpeljalo z nje.
-- To je opažanje, ki ga feed pri vlakih skoraj nikoli nima.
CREATE TABLE IF NOT EXISTS deljenje_prehod (
    deljenje     TEXT NOT NULL,
    trip_id      TEXT NOT NULL,
    service_date TEXT NOT NULL,
    stop_seq     INTEGER NOT NULL,
    prihod_ts    INTEGER,
    odhod_ts     INTEGER,
    PRIMARY KEY (deljenje, stop_seq)
);
CREATE INDEX IF NOT EXISTS deljenje_prehod_voznja
    ON deljenje_prehod(trip_id, service_date);
"""


class Zavrnjeno(Exception):
    """Zahteve nismo sprejeli. Besedilo je namenjeno potniku."""

    def __init__(self, sporocilo: str, status: int = 400):
        super().__init__(sporocilo)
        self.status = status


def init(conn: sqlite3.Connection) -> None:
    conn.executescript(SHEMA)
    conn.commit()


# ------------------------------------------------------------ geometrija

#: Metrov na stopinjo zemljepisne širine.
_M_NA_STOPINJO = geo.EARTH_R * math.pi / 180


class Trasa:
    """Trasa ene vožnje v krajevni ravnini, pripravljena za projekcijo.

    `geo.project()` računa haversine za vsak odsek in je za eno postajo
    dovolj hiter; tu pa projiciramo potnika na vse trase v okolici in vsako
    njegovo točko, zato je vse preračunano v metre enkrat.
    """

    __slots__ = ("tocke", "x", "y", "cum", "lat0", "k", "okvir", "vrzeli")

    def __init__(self, kosi: list[list[tuple[float, float]]]):
        """`kosi` so deli trase, kot jih hrani `shape` (glej `gtfs.py`).

        Trasa je lahko pretrgana -- med kosi je do 40 km praznine. Za razdaljo
        vzdolž trase se vrzel šteje (vozilo jo prevozi), za projekcijo pa ne:
        ravna črta čez vrzel ni kraj, kjer vozilo vozi.
        """
        tocke: list[tuple[float, float]] = []
        self.vrzeli: set[int] = set()
        for kos in kosi:
            if tocke:
                self.vrzeli.add(len(tocke) - 1)
            tocke.extend(kos)
        self.tocke = tocke
        self.lat0 = sum(p[0] for p in tocke) / len(tocke)
        self.k = math.cos(math.radians(self.lat0))
        self.x = [p[1] * self.k * _M_NA_STOPINJO for p in tocke]
        self.y = [p[0] * _M_NA_STOPINJO for p in tocke]
        self.cum = geo.cumulative(tocke)
        self.okvir = (min(self.x), min(self.y), max(self.x), max(self.y))

    @property
    def dolzina(self) -> float:
        return self.cum[-1]

    @property
    def krozna(self) -> bool:
        """Začetek in konec v isti točki: projekcija sama ne ve, na katerega."""
        return math.hypot(self.x[0] - self.x[-1], self.y[0] - self.y[-1]) < 300

    def xy(self, lat: float, lon: float) -> tuple[float, float]:
        return lon * self.k * _M_NA_STOPINJO, lat * _M_NA_STOPINJO

    def blizu(self, lat: float, lon: float, polmer: float) -> bool:
        x, y = self.xy(lat, lon)
        x0, y0, x1, y1 = self.okvir
        return x0 - polmer <= x <= x1 + polmer and y0 - polmer <= y <= y1 + polmer

    def projiciraj(self, lat: float, lon: float, od_m: float = -1.0,
                   do_m: float = float("inf"),
                   najvec_m: float = float("inf")) -> tuple[float, float]:
        """(razdalja vzdolž trase, odmik od nje) v metrih.

        `od_m`/`do_m` omejita iskanje na del trase. Brez tega se krožna
        mestna linija ali proga, ki gre dvakrat mimo iste točke, projicira na
        napačen krak in potnik skoči za pol vožnje naprej.

        `najvec_m`: odmik, nad katerim nas projekcija ne zanima -- takrat
        vrne `inf`. Odsek, ki je ves dlje od najboljšega doslej, se preskoči
        brez računanja; na arwenu je bilo to 1,26 s od 1,75 za kandidate v
        Ljubljani (1 029 projekcij), ker je vsaka računala vse odseke.
        """
        px, py = self.xy(lat, lon)
        x, y, cum = self.x, self.y, self.cum
        naj_d2, naj_along = float("inf"), 0.0
        r = najvec_m
        vrzeli = self.vrzeli
        for i in range(len(x) - 1):
            ax, ay, bx, by = x[i], y[i], x[i + 1], y[i + 1]
            # Oba konca na isti strani pasu okoli točke: odsek je dlje od r.
            if ((ax < px - r and bx < px - r) or (ax > px + r and bx > px + r)
                    or (ay < py - r and by < py - r) or (ay > py + r and by > py + r)):
                continue
            if cum[i + 1] < od_m or cum[i] > do_m or i in vrzeli:
                continue
            vx, vy = bx - ax, by - ay
            l2 = vx * vx + vy * vy
            t = 0.0 if l2 == 0 else ((px - ax) * vx + (py - ay) * vy) / l2
            t = 0.0 if t < 0 else (1.0 if t > 1 else t)
            dx, dy = ax + t * vx - px, ay + t * vy - py
            d2 = dx * dx + dy * dy
            if d2 < naj_d2:
                naj_d2 = d2
                naj_along = cum[i] + t * (cum[i + 1] - cum[i])
                r = math.sqrt(d2)
        return naj_along, math.sqrt(naj_d2)

    def tocka(self, along: float) -> tuple[float, float]:
        """(lat, lon) na trasi pri dani razdalji vzdolž nje."""
        cum = self.cum
        if along <= 0:
            return self.tocke[0]
        if along >= cum[-1]:
            return self.tocke[-1]
        lo, hi = 0, len(cum) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if cum[mid] <= along:
                lo = mid
            else:
                hi = mid
        dol = cum[hi] - cum[lo]
        t = 0.0 if dol == 0 else (along - cum[lo]) / dol
        (a_lat, a_lon), (b_lat, b_lon) = self.tocke[lo], self.tocke[hi]
        return a_lat + t * (b_lat - a_lat), a_lon + t * (b_lon - a_lon)

    def smer(self, along: float, pol_m: float) -> float | None:
        """Smer trase pri `along`, v stopinjah od severa, naprej po vožnji.

        Tetiva od `pol_m` zadaj do `pol_m` spredaj; na koncu trase se skrajša
        na tisto, kar trasa ima. Brez dolžine (ena točka) vrne None.
        """
        a_lat, a_lon = self.tocka(along - pol_m)
        b_lat, b_lon = self.tocka(along + pol_m)
        dx = (b_lon - a_lon) * math.cos(math.radians((a_lat + b_lat) / 2))
        dy = b_lat - a_lat
        if dx == 0 and dy == 0:
            return None
        return round((math.degrees(math.atan2(dx, dy)) + 360) % 360, 1)


class Voznja:
    """Trasa in postanki ene vožnje, s postanki projiciranimi nanjo."""

    __slots__ = ("trip_id", "train_no", "headsign", "network", "mode", "agency",
                 "trasa", "postanki")

    def __init__(self, vrstica: dict, trasa: Trasa, postanki: list[dict]):
        self.trip_id = vrstica["trip_id"]
        self.train_no = vrstica["train_no"]
        self.headsign = vrstica["headsign"]
        self.network = vrstica["network"]
        self.mode = vrstica["mode"]
        self.agency = vrstica["agency"]
        self.trasa = trasa
        self.postanki = postanki

    @property
    def na_postaji_m(self) -> float:
        return NA_POSTAJI_M.get(self.network, 100)

    def okolica(self, along: float) -> tuple[int, int]:
        """Indeksa postankov pred lego in za njo (lahko isti na koncih)."""
        p = self.postanki
        i = 0
        while i + 1 < len(p) and p[i + 1]["along"] <= along:
            i += 1
        return i, min(i + 1, len(p) - 1)

    def na_postaji(self, along: float) -> int | None:
        """Indeks postanka, na katerem je vozilo, ali None."""
        naj = min(range(len(self.postanki)),
                  key=lambda j: abs(self.postanki[j]["along"] - along))
        if abs(self.postanki[naj]["along"] - along) <= self.na_postaji_m:
            return naj
        return None

    def okno(self, t_s: float, zamuda_s: float, prehiteva_s: float) -> tuple[float, float]:
        """Del trase, kjer je vozilo ob `t_s` po voznem redu lahko: za postankom,
        mimo katerega bi moralo že pred `zamuda_s`, in pred tistim, do katerega
        ima še `prehiteva_s`. Meja za `Trasa.projiciraj()`."""
        cas = [p["dep_s"] if p["dep_s"] is not None else p["arr_s"] for p in self.postanki]
        lo = [p["along"] for p, c in zip(self.postanki, cas) if c <= t_s - zamuda_s]
        hi = [p["along"] for p, c in zip(self.postanki, cas) if c >= t_s + prehiteva_s]
        return (lo[-1] if lo else -1.0), (hi[0] if hi else float("inf"))

    def voznoredni_cas(self, along: float) -> float:
        """Kdaj bi bilo vozilo po voznem redu na tej razdalji (s od polnoči).

        Med postajama linearno. Vlak pospešuje in zavira, zato je to pri
        dolgem odseku lahko minuto mimo -- a le na odprti progi, na postaji
        je čas točen.
        """
        p = self.postanki
        i, j = self.okolica(along)
        a, b = p[i], p[j]
        t_a = a["dep_s"] if a["dep_s"] is not None else a["arr_s"]
        t_b = b["arr_s"] if b["arr_s"] is not None else b["dep_s"]
        if i == j or b["along"] <= a["along"]:
            return float(t_a)
        f = max(0.0, min(1.0, (along - a["along"]) / (b["along"] - a["along"])))
        return t_a + f * (t_b - t_a)

    def zamuda(self, along: float, t_s: float) -> int:
        """Zamuda vozila, ki je ob `t_s` (s od polnoči) na razdalji `along`.

        Na postaji je vozni red interval [prihod, odhod]: kdor je tam vmes,
        je točen, kdor stoji po odhodu, zamuja vsaj za toliko, kolikor že
        stoji čez -- in ta zamuda raste, dokler ne odpelje. Prav to je
        primer, ko feed trdi, da je vlak že šel.
        """
        j = self.na_postaji(along)
        if j is not None:
            s = self.postanki[j]
            prihod = s["arr_s"] if s["arr_s"] is not None else s["dep_s"]
            odhod = s["dep_s"] if s["dep_s"] is not None else s["arr_s"]
            if t_s < prihod:
                return round(t_s - prihod)
            if t_s <= odhod:
                return 0
            return round(t_s - odhod)
        return round(t_s - self.voznoredni_cas(along))


_predpomnilnik: dict[str, Voznja | None] = {}
#: Trase po `shape_id`: vse vožnje ene linije v isti smeri imajo isto traso,
#: in trasa je večji del pomnilnika (postanki so nekaj deset vrstic).
_trase: dict[str, Trasa] = {}
_pp_znacka: str | None = "\0ni prebrana"
_pp_zaklep = threading.Lock()
#: Toliko voženj v pomnilniku. Izmerjeno 25. 9. 2026: vse vožnje v okolici ure
#: (1 512, 941 tras) so 48,5 MB; to je zgornja meja, ne običaj.
_PP_NAJVEC = 2000


#: Lega postankov vzdolž trase po (trasa, zaporedje postajališč). Vse vožnje
#: ene linije v isti smeri imajo isto oboje, projekcija pa je bila hladno
#: večji del iskanja kandidatov: v Ljubljani 493 voženj, 11 529 projekcij.
_vzorci: dict[tuple, list[float]] = {}


def _postanki(conn: sqlite3.Connection, trip_id: str, shape_id: str,
              trasa: Trasa) -> list[dict]:
    """Postanki vožnje s projekcijo na traso, **zaporedno**.

    Vsak postanek se išče samo naprej od prejšnjega: sicer bi se postajališče
    krožne linije projiciralo na drug krak in vrstni red postankov vzdolž
    trase ne bi bil več vrstni red vožnje.
    """
    vrstice = conn.execute(
        "SELECT s.stop_seq, s.stop_id, s.arr_s, s.dep_s, st.name, st.lat, st.lon "
        "FROM sched s JOIN station st ON st.stop_id = s.stop_id "
        "WHERE s.trip_id = ? ORDER BY s.stop_seq", (trip_id,)).fetchall()
    kljuc = (shape_id, tuple(v["stop_id"] for v in vrstice))
    alongi = _vzorci.get(kljuc)
    if alongi is None:
        alongi, prej = [], -1.0
        for v in vrstice:
            along, _ = trasa.projiciraj(v["lat"], v["lon"], od_m=prej - 30)
            prej = max(along, prej)
            alongi.append(prej)
        with _pp_zaklep:
            if len(_vzorci) >= _PP_NAJVEC:
                _vzorci.clear()
            _vzorci[kljuc] = alongi
    return [{"stop_seq": v["stop_seq"], "name": v["name"], "arr_s": v["arr_s"],
             "dep_s": v["dep_s"], "along": a} for v, a in zip(vrstice, alongi)]


#: Kako pogosto preveriti, ali je bil uvožen nov vozni red. Ob vsakem klicu
#: bi bila to poizvedba na vožnjo -- pri kandidatih v Ljubljani šesto.
_PP_PREVERI_S = 60
_pp_preverjeno = 0.0


def _preveri_znacko(conn: sqlite3.Connection) -> None:
    """Nov vozni red lahko spremeni traso in postanke pod istim id-jem."""
    global _pp_znacka, _pp_preverjeno
    if time.monotonic() - _pp_preverjeno < _PP_PREVERI_S:
        return
    # Pripenjanje (`pripni.py`) teče po uvozu in traso pod istim id-jem
    # zamenja s pripeto.
    znacka = f'{db.get_meta(conn, "gtfs_imported_at")}|{db.get_meta(conn, "pripeto_at")}'
    with _pp_zaklep:
        _pp_preverjeno = time.monotonic()
        if znacka != _pp_znacka:
            _predpomnilnik.clear()
            _trase.clear()
            _vzorci.clear()
            _pp_znacka = znacka


def trasa(conn: sqlite3.Connection, shape_id: str | None) -> Trasa | None:
    """Trasa iz pomnilnika. Brez postankov -- za grobo sito kandidatov."""
    if not shape_id:
        return None
    _preveri_znacko(conn)
    t = _trase.get(shape_id)
    if t is not None:
        return t
    # Pripeta na OSM, kadar je (`pripni.py`): na njej je vozilo narisano
    # (okno vožnje drsi po njej, vlak na postaji stoji na njej), in od ceste
    # je v mediani 0,4 m namesto 3,1 m.
    sh = conn.execute("SELECT COALESCE(osm, points) AS points FROM shape WHERE shape_id = ?",
                      (shape_id,)).fetchone()
    kosi = [[tuple(p) for p in kos] for kos in json.loads(sh["points"])] if sh else []
    if sum(len(k) for k in kosi) < 2:
        return None
    t = Trasa(kosi)
    with _pp_zaklep:
        if len(_trase) >= _PP_NAJVEC:
            _trase.clear()
        _trase[shape_id] = t
    return t


def voznja(conn: sqlite3.Connection, trip_id: str) -> Voznja | None:
    """Vožnja s traso in postanki, iz pomnilnika. None, kadar trase ni."""
    _preveri_znacko(conn)
    with _pp_zaklep:
        if trip_id in _predpomnilnik:
            return _predpomnilnik[trip_id]
    v = conn.execute(
        "SELECT trip_id, train_no, headsign, network, mode, agency, shape_id "
        "FROM trip WHERE trip_id = ?", (trip_id,)).fetchone()
    izid = None
    t = trasa(conn, v["shape_id"]) if v else None
    if t is not None:
        postanki = _postanki(conn, trip_id, v["shape_id"], t)
        if len(postanki) >= 2:
            izid = Voznja(dict(v), t, postanki)
    with _pp_zaklep:
        if len(_predpomnilnik) >= _PP_NAJVEC:
            _predpomnilnik.clear()
        _predpomnilnik[trip_id] = izid
    return izid


# --------------------------------------------------------------- čas

def _iso(ts: int | None) -> str | None:
    return datetime.fromtimestamp(ts, TZ).isoformat() if ts else None


def _dneva(zdaj: datetime) -> list[tuple[str, int]]:
    """(prometni dan, sekunde od njegove polnoči) za danes in včeraj.

    Nočni vlak po polnoči vozi pod včerajšnjim dnem in njegove sekunde
    tečejo čez 86 400 -- isto kot pri `api._live`.
    """
    danes = zdaj.date()
    vceraj = danes - timedelta(days=1)
    ts = int(zdaj.timestamp())
    return [(d.isoformat(), ts - stats.polnoc(d.isoformat())) for d in (danes, vceraj)]


# ------------------------------------------------------------ kandidati

_ZIVE_VOZNJE_SQL = """
SELECT DISTINCT t.trip_id, t.shape_id
FROM station st
JOIN sched s ON s.stop_id = st.stop_id
JOIN trip t ON t.trip_id = s.trip_id
JOIN service_day sd ON sd.service_id = t.service_id AND sd.date = ?
WHERE st.lat BETWEEN ? AND ? AND st.lon BETWEEN ? AND ?
  AND t.network = ?
  AND t.shape_id IS NOT NULL
  AND t.start_s <= ? AND t.end_s >= ?
"""


def _zive_blizu(conn: sqlite3.Connection, lat: float, lon: float, zdaj: datetime,
                polmeri: dict[str, int]) -> list[tuple[str, str, int, str]]:
    """(trip_id, prometni dan, sekunde od polnoči, shape_id) za vožnje v okolici.

    Najprej postaje v okolici, šele nato vožnje skozi njih: trase vseh
    voženj, ki se ta hip vozijo, so desettisoče točk, in brati jih vse za
    vsakega potnika bi bilo potratno.
    """
    out = []
    for network, polmer in polmeri.items():
        dlat = polmer / _M_NA_STOPINJO
        dlon = dlat / max(math.cos(math.radians(lat)), 0.1)
        for dan, now_s in _dneva(zdaj):
            for r in conn.execute(_ZIVE_VOZNJE_SQL, (
                    dan, lat - dlat, lat + dlat, lon - dlon, lon + dlon, network,
                    now_s + KANDIDAT_PRED_S,
                    now_s - KANDIDAT_ZA_S - stats.MAX_REALNA_ZAMUDA_S)):
                out.append((r["trip_id"], dan, now_s, r["shape_id"]))
    return out


def _zadnje_zamude(conn: sqlite3.Connection, pari: list[tuple[str, str, int]]
                   ) -> dict[str, int]:
    """Zadnja izmerjena zamuda vsake vožnje -- ista meja kot povsod."""
    po_dnevih: dict[tuple[str, int], list[str]] = {}
    for trip_id, dan, now_s, *_ in pari:
        po_dnevih.setdefault((dan, now_s), []).append(trip_id)
    out = {}
    for (dan, now_s), ids in po_dnevih.items():
        for trip_id, m in stats.last_measured(conn, dan, ids, now_s).items():
            if m.get("delay_s") is not None:
                out[trip_id] = int(m["delay_s"])
    return out


def _gps(conn: sqlite3.Connection, trip_ids: list[str], zdaj_ts: int) -> dict[str, dict]:
    if not trip_ids:
        return {}
    marks = ",".join("?" * len(trip_ids))
    return {r["trip_id"]: dict(r) for r in conn.execute(
        f"SELECT trip_id, lat, lon, seen_ts FROM vehicle_now "
        f"WHERE trip_id IN ({marks}) AND seen_ts >= ?",
        (*trip_ids, zdaj_ts - 180))}


def _kje(v: Voznja, along: float) -> dict:
    """Kje na trasi je to: na postaji ali med dvema.

    `stop_seq` je postaja, od katere naprej teče napoved (tista, na kateri
    vozilo stoji, ali zadnja za njim), `mimo_seq` zadnja, ki jo je vozilo že
    zapustilo -- postaja, na kateri stoji, še ni prevožena.
    """
    j = v.na_postaji(along)
    if j is not None:
        return {"pri": v.postanki[j]["name"], "stop_seq": v.postanki[j]["stop_seq"],
                "mimo_seq": v.postanki[j - 1]["stop_seq"] if j > 0 else None}
    i, k = v.okolica(along)
    # Dve zaporedni postajališči z istim imenom („Izola“, „Izola“): „med
    # Izola in Izola“ ne pove nič, „pri Izola“ pa drži na nekaj sto metrov.
    if v.postanki[i]["name"] == v.postanki[k]["name"]:
        return {"pri": v.postanki[i]["name"], "stop_seq": v.postanki[i]["stop_seq"],
                "mimo_seq": v.postanki[i]["stop_seq"]}
    if along < v.postanki[0]["along"]:
        return {"pri": v.postanki[0]["name"], "stop_seq": v.postanki[0]["stop_seq"],
                "mimo_seq": None}
    return {"med": [v.postanki[i]["name"], v.postanki[k]["name"]],
            "stop_seq": v.postanki[i]["stop_seq"], "mimo_seq": v.postanki[i]["stop_seq"]}


def kandidati(conn: sqlite3.Connection, lat: float, lon: float,
              natancnost: float | None = None, prej: dict | None = None,
              zdaj: datetime | None = None) -> list[dict]:
    """Vožnje, na katerih bi potnik s to lego lahko bil.

    Kandidat mora izpolniti dvoje: potnik je na njeni trasi, in po voznem
    redu ter zadnji znani zamudi bi bila vožnja ravno zdaj nekje tu. Druga
    zahteva je namenoma ohlapna v eno smer (`KANDIDAT_ZA_S`): vlak, ki ga
    feed kaže kot odpeljanega, a še stoji, je natanko primer, ki ga iščemo.

    `prej` je potnikova lega nekaj sekund prej ({lat, lon}). Iz nje je smer
    vožnje, ki loči vlak Ljubljana--Maribor od vlaka Maribor--Ljubljana na
    istem tiru.
    """
    zdaj = zdaj or datetime.now(TZ)
    meja = KANDIDAT_ODMIK_M + min(max(natancnost or 0, 0), NATANCNOST_MAX_M)
    out = _ocenjeni(conn, lat, lon, meja, prej, zdaj, KANDIDAT_POLMER_M)
    if not any(k["network"] == "avtobus" for k in out):
        znani = {k["trip_id"] for k in out}
        out += [k for k in _ocenjeni(conn, lat, lon, meja, prej, zdaj,
                                     KANDIDAT_POLMER_SIRSE_M)
                if k["trip_id"] not in znani]
    out.sort(key=lambda k: k["_ocena"])
    # Dve vožnji z isto oznako, istim ciljem in na istem kraju sta za potnika
    # en gumb -- v IJPP jih je kar nekaj (sezonske različice, A8425 dvakrat
    # proti Ljubljani na emulatorju 25. 9. 2026). Obdrži se bolje ocenjena.
    videni, izbrani = set(), []
    for k in out:
        kljuc = (k["train_no"], k["headsign"], k.get("pri"), tuple(k.get("med") or ()))
        if kljuc in videni:
            continue
        videni.add(kljuc)
        k.pop("_ocena")
        izbrani.append(k)
    return izbrani[:KANDIDATOV]


def _ocenjeni(conn: sqlite3.Connection, lat: float, lon: float, meja: float,
              prej: dict | None, zdaj: datetime, polmeri: dict[str, int]) -> list[dict]:
    """Kandidati v danem polmeru, z oceno (`_ocena`, manjša je boljša)."""
    zdaj_ts = int(zdaj.timestamp())
    # Najprej sito po trasi: v Ljubljani je v okolici ~600 voženj, a le
    # nekaj deset gre res mimo. Trase si delijo vožnje iste linije, postanki
    # pa so za vsako vožnjo svoji -- zato postanki, zamude in GPS šele za
    # tiste, ki sito preživijo. Izmerjeno na arwenu: 17 s hladno in 1,75 s
    # toplo, preden je bilo sito prvo.
    blizu, po_trasi = [], {}
    for trip_id, dan, now_s, shape_id in _zive_blizu(conn, lat, lon, zdaj, polmeri):
        if shape_id not in po_trasi:
            tr = trasa(conn, shape_id)
            po_trasi[shape_id] = (tr.projiciraj(lat, lon, najvec_m=meja)
                                  if tr is not None and tr.blizu(lat, lon, meja) else None)
        pr = po_trasi[shape_id]
        if pr is not None and pr[1] <= meja:
            blizu.append((trip_id, dan, now_s, *pr))
    zamude = _zadnje_zamude(conn, [b[:3] for b in blizu])
    gps = _gps(conn, [b[0] for b in blizu], zdaj_ts)
    out, videno = [], set()
    for trip_id, dan, now_s, along, odmik in blizu:
        if trip_id in videno:
            continue
        v = voznja(conn, trip_id)
        if v is None:
            continue
        zamuda = zamude.get(trip_id, 0)
        if v.trasa.krozna:
            # Sito je projiciralo na celo traso; na krožni liniji je izhodišče
            # tudi konec, in vozilo na izhodišču bi bilo videti kot na cilju.
            along, odmik = v.trasa.projiciraj(
                lat, lon, *v.okno(now_s - zamuda, KANDIDAT_ZA_S, KANDIDAT_PRED_S))
            if odmik > meja:
                continue
        smer = None
        if prej and prej.get("lat") is not None:
            p_along, p_odmik = v.trasa.projiciraj(prej["lat"], prej["lon"],
                                                  along - 3000, along + 3000)
            if p_odmik <= meja and abs(along - p_along) >= 40:
                smer = along > p_along
                if not smer:
                    continue          # pelje v nasprotno smer
        # Kdaj bi bila vožnja tu, po voznem redu in zadnji zamudi -- in
        # koliko je od tega zdaj. Pozitivno: vozilo zamuja več, kot vemo.
        razlika = now_s - (v.voznoredni_cas(along) + zamuda)
        na_zacetku = along <= v.postanki[0]["along"] + v.na_postaji_m
        if na_zacetku:
            # Na začetni postaji vozilo stoji pred odhodom poljubno dolgo.
            razlika = min(max(razlika, -KANDIDAT_PRED_S), max(razlika, 0))
        if not (-KANDIDAT_PRED_S <= razlika <= KANDIDAT_ZA_S):
            continue
        ocena = abs(razlika) if razlika < 0 else razlika / 3
        g = gps.get(trip_id)
        if g:
            d = geo.haversine(lat, lon, g["lat"], g["lon"])
            # Lega avtobusa je izmerjena: kjer je, je, in to je močnejše od
            # voznega reda. Starost lege dopusti nekaj poti.
            if d > KANDIDAT_GPS_M + 15 * max(zdaj_ts - g["seen_ts"], 0):
                continue
            ocena = d / 10
        ocena += odmik / 5
        if smer:
            ocena /= 2
        videno.add(trip_id)
        out.append({
            "trip_id": trip_id, "service_date": dan,
            "train_no": v.train_no, "headsign": v.headsign,
            "network": v.network, "mode": v.mode, "agency": v.agency,
            "smer_potrjena": bool(smer), **_kje(v, along), "_ocena": ocena,
        })
    return out


# ------------------------------------------------------------ omejevanje

_zaklep = threading.Lock()
_kandidati_casi: dict[str, list[float]] = {}
_deljenja_casi: dict[str, list[float]] = {}
#: Zadnje deljenje pošiljatelja na vožnji. Samo v pomnilniku, kot omejitve:
#: v bazi deljenje nima identitete.
_zadnje_deljenje: dict[tuple[str, str], str] = {}


def _pogostost(slovar: dict[str, list[float]], kljuc: str, okno_s: float,
               najvec: int, sporocilo: str, zdaj: float) -> None:
    with _zaklep:
        casi = [c for c in slovar.get(kljuc, []) if zdaj - c < okno_s]
        if len(casi) >= najvec:
            raise Zavrnjeno(sporocilo, 429)
        casi.append(zdaj)
        slovar[kljuc] = casi
        if len(slovar) > 5000:
            for k in [k for k, v in slovar.items() if not v or zdaj - max(v) > okno_s]:
                slovar.pop(k, None)


def je_json(content_type: str) -> bool:
    """Ali zahteva res nosi `application/json` -- edina vrsta, pri kateri
    brskalnik pred tujo zahtevo vpraša CORS. Podniz ne zadošča:
    `text/plain;charset=application/json` je za brskalnik `text/plain` in gre
    brez vprašanja, tuja stran pa bi svoje obiskovalce spremenila v
    poročevalce -- dva sta dovolj za soglasje, ki zamenja feed."""
    return content_type.split(";")[0].strip().lower() == "application/json"


def preveri_kandidate(kljuc: str, zdaj: float | None = None) -> None:
    _pogostost(_kandidati_casi, kljuc, 60, KANDIDATI_NA_MINUTO,
               "Preveč poizvedb. Poskusi čez minuto.", zdaj or time.time())


# --------------------------------------------------------------- sprejem

def _stevilo(v, ime: str, lo: float, hi: float) -> float:
    try:
        x = float(v)
    except (TypeError, ValueError, OverflowError):   # 400-mestno celo število
        raise Zavrnjeno(f"{ime} ni število.") from None
    if not (lo <= x <= hi) or math.isnan(x):
        raise Zavrnjeno(f"{ime} je zunaj meja.")
    return x


def lega(podatki: dict) -> tuple[float, float, float | None]:
    """(lat, lon, natančnost) iz zahteve, preverjeno."""
    lat = _stevilo(podatki.get("lat"), "lat", -90, 90)
    lon = _stevilo(podatki.get("lon"), "lon", -180, 180)
    acc = podatki.get("acc")
    return lat, lon, (_stevilo(acc, "acc", 0, 1e6) if acc is not None else None)


def _dnevni_strop(conn: sqlite3.Connection, zdaj: datetime) -> None:
    polnoc = stats.polnoc(zdaj.date().isoformat())
    n, tock = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(tock), 0) FROM deljenje WHERE zacetek_ts >= ?",
        (polnoc,)).fetchone()
    if n >= DELJENJ_NA_DAN or tock >= TOCK_NA_DAN:
        raise Zavrnjeno("Danes je deljenja dovolj. Hvala — poskusi jutri.", 429)


def _prva_lega(conn: sqlite3.Connection, v: Voznja, dan: str, now_s: int,
               lat: float, lon: float) -> tuple[float, float, int]:
    """(along, odmik, zamuda) prve točke deljenja.

    Projekcija je omejena na del trase, kjer je vozilo po voznem redu in
    zadnji zamudi lahko -- z isto mejo, kot jo ima preverjanje časa v
    `_zacni()`. Krožna linija ima izhodišče in konec v isti točki: brez meje
    prva točka na izhodišču pade na konec trase in deljenje se konča s „cilj“.
    """
    zamuda = _zadnje_zamude(conn, [(v.trip_id, dan, now_s)]).get(v.trip_id, 0)
    od_m, do_m = v.okno(now_s - zamuda, KANDIDAT_ZA_S + stats.MAX_REALNA_ZAMUDA_S,
                        KANDIDAT_PRED_S)
    along, odmik = v.trasa.projiciraj(lat, lon, od_m, do_m)
    return along, odmik, zamuda


def _zacni(conn: sqlite3.Connection, v: Voznja, dan: str, now_s: int,
           prva: dict, kljuc: str, zdaj: datetime) -> str:
    """Novo deljenje. Prva točka mora biti na trasi in ob pravem času.

    Omejitev na uro šteje le deljenja, ki so se res začela: potnik s slabim
    GPS ob postaji dobi „ni na trasi“ večkrat zapored, ključ pa si za
    operaterjevim CGNAT deli veliko ljudi.
    """
    _dnevni_strop(conn, zdaj)
    along, odmik, zamuda = _prva_lega(conn, v, dan, now_s, prva["lat"], prva["lon"])
    if odmik > KANDIDAT_ODMIK_M + min(prva.get("acc") or 0, NATANCNOST_MAX_M):
        raise Zavrnjeno("Tvoja lega ni na trasi te vožnje.")
    razlika = now_s - (v.voznoredni_cas(along) + zamuda)
    if razlika < -KANDIDAT_PRED_S and along > v.postanki[0]["along"] + v.na_postaji_m:
        raise Zavrnjeno("Ta vožnja ta hip ni tu.")
    if razlika > KANDIDAT_ZA_S + stats.MAX_REALNA_ZAMUDA_S:
        raise Zavrnjeno("Ta vožnja ta hip ni tu.")
    _pogostost(_deljenja_casi, kljuc, 3600, DELJENJ_NA_URO,
               "Preveč začetih deljenj. Poskusi čez kakšno uro.", zdaj.timestamp())
    ident = secrets.token_urlsafe(16)
    ts = int(zdaj.timestamp())
    conn.execute(
        "INSERT INTO deljenje(id, trip_id, service_date, network, zacetek_ts, zadnja_ts) "
        "VALUES(?, ?, ?, ?, ?, ?)", (ident, v.trip_id, dan, v.network, ts, ts))
    # Isti pošiljatelj znova na isti vožnji (osvežena stran, izgubljen odgovor
    # na prvo pošiljanje) ni drugi potnik: prejšnje deljenje se konča, sicer
    # bi en telefon dal "soglasje dveh" in zamenjal feed. Konec je `znova`,
    # ne `potnik`: v prvih deljenjih (do 1. 10. 2026) se ponovnega začetka ni
    # dalo ločiti od gumba Ustavi -- en potnik je v 45 minutah začel petkrat.
    # Ključ je naslov, za CGNAT pa si ga deli več ljudi: ponoven začetek,
    # medtem ko staro deljenje še pošilja, je lahko drug potnik.
    with _zaklep:
        prej = _zadnje_deljenje.get((kljuc, v.trip_id))
        _zadnje_deljenje[(kljuc, v.trip_id)] = ident
        if len(_zadnje_deljenje) > 5000:
            _zadnje_deljenje.clear()
    if prej:
        conn.execute("UPDATE deljenje SET konec = 'znova' WHERE id = ? AND konec IS NULL",
                     (prej,))
    return ident


def _tocke(podatki: dict, zdaj_ts: int) -> list[dict]:
    """Točke iz zahteve: preverjene, urejene po času, čas omejen na smiselno.

    Čas pošlje naprava, ker Android točke iz predora pošlje pozneje. Ura
    naprave pa zna biti napačna, zato je omejena: ne v prihodnost in ne
    starejša od četrt ure.
    """
    surove = podatki.get("tocke")
    if not isinstance(surove, list) or not surove:
        raise Zavrnjeno("Ni točk.")
    if len(surove) > TOCK_NA_ZAHTEVO:
        surove = surove[-TOCK_NA_ZAHTEVO:]
    out = []
    for t in surove:
        if not isinstance(t, dict):
            continue
        try:
            lat, lon, acc = lega(t)
        except Zavrnjeno:
            continue
        ts = t.get("t")
        try:
            ts = int(float(ts) / 1000) if ts is not None else zdaj_ts
        except (TypeError, ValueError, OverflowError):   # 1e999 je v JSON inf
            ts = zdaj_ts
        ts = min(max(ts, zdaj_ts - 900), zdaj_ts)
        hitrost = t.get("v")
        try:
            hitrost = float(hitrost) if hitrost is not None else None
        except (TypeError, ValueError, OverflowError):
            hitrost = None
        if hitrost is not None and not (0 <= hitrost <= HITROST_MAX_MS):
            hitrost = None
        out.append({"lat": lat, "lon": lon, "acc": acc, "ts": ts, "v": hitrost})
    if not out:
        raise Zavrnjeno("Ni veljavnih točk.")
    out.sort(key=lambda t: t["ts"])
    return out


def sprejmi(conn: sqlite3.Connection, podatki: dict, kljuc: str,
            zdaj: datetime | None = None) -> dict:
    """Zapiše točke enega deljenja. Vrne stanje in morebiten konec.

    Brez `deljenje` v zahtevi se deljenje začne -- a le, če je prva točka
    na trasi vožnje in vožnja ta hip lahko je tu.
    """
    zdaj = zdaj or datetime.now(TZ)
    zdaj_ts = int(zdaj.timestamp())
    trip_id = str(podatki.get("trip_id") or "")[:64]
    dan = str(podatki.get("service_date") or "")
    dnevi = dict(_dneva(zdaj))
    if dan not in dnevi:
        raise Zavrnjeno("Deliti se da samo vožnjo, ki vozi danes.")
    now_s = dnevi[dan]
    tocke = _tocke(podatki, zdaj_ts)
    v = voznja(conn, trip_id)
    if v is None:
        raise Zavrnjeno("Te vožnje ne poznam.", 404)
    ok = conn.execute(
        "SELECT 1 FROM trip t JOIN service_day sd ON sd.service_id = t.service_id "
        "AND sd.date = ? WHERE t.trip_id = ? AND t.start_s <= ? AND t.end_s >= ?",
        (dan, trip_id, now_s + KANDIDAT_PRED_S,
         now_s - stats.MAX_REALNA_ZAMUDA_S - KANDIDAT_ZA_S)).fetchone()
    if not ok:
        raise Zavrnjeno("Ta vožnja ta hip ne vozi.")

    ident = podatki.get("deljenje")
    if ident:
        d = conn.execute("SELECT * FROM deljenje WHERE id = ?", (str(ident)[:64],)).fetchone()
        if not d or d["trip_id"] != trip_id or d["service_date"] != dan:
            raise Zavrnjeno("Deljenja ne poznam.", 404)
        d = dict(d)
    else:
        ident = _zacni(conn, v, dan, now_s, tocke[0], kljuc, zdaj)
        d = dict(conn.execute("SELECT * FROM deljenje WHERE id = ?", (ident,)).fetchone())

    if d["konec"]:
        conn.commit()
        return {"deljenje": ident, "sprejetih": 0, "konec": d["konec"],
                "stanje": stanje(conn, [trip_id], zdaj).get(trip_id)}
    polnoc = stats.polnoc(dan)
    sprejetih = 0
    for t in tocke:
        if d["konec"]:
            break
        if t["acc"] is not None and t["acc"] > NATANCNOST_MAX_M:
            continue
        if d["along_m"] is not None and t["ts"] < d["zadnja_ts"] + RAZMIK_S:
            continue
        if d["along_m"] is None:
            along, odmik, _ = _prva_lega(conn, v, dan, now_s, t["lat"], t["lon"])
        else:
            dt = max(t["ts"] - d["zadnja_ts"], 1)
            along, odmik = v.trasa.projiciraj(
                t["lat"], t["lon"], d["along_m"] - NAZAJ_MAX_M - 200,
                d["along_m"] + HITROST_MAX_MS * dt + 500)
        if odmik > ODMIK_MAX_M:
            d["zunaj"] += 1
            if d["zunaj"] >= ZUNAJ_ZA_IZSTOP:
                d["konec"] = "izstop"
            continue
        hitrost = t["v"]
        if d["along_m"] is not None:
            dt = t["ts"] - d["zadnja_ts"]
            premik = along - d["along_m"]
            if premik < -NAZAJ_MAX_M or abs(premik) / max(dt, 1) > HITROST_MAX_MS:
                continue
            # Nazaj za manj kot `NAZAJ_MAX_M` je šum GPS: vozilo stoji.
            along = max(along, d["along_m"])
            if hitrost is None and dt > 0:
                hitrost = max(premik, 0) / dt
            if ((along - d["along_m"]) / max(dt, 1) < VOZI_MS
                    and _odmaknjen(conn, ident, odmik, t["acc"])):
                d["zunaj"] += 1
                if d["zunaj"] >= ZUNAJ_ZA_IZSTOP:
                    d["konec"] = "izstop"
                continue
            _prehodi(conn, v, ident, dan, d["along_m"], d["zadnja_ts"], along, t["ts"])
        d["zunaj"] = 0
        conn.execute(
            "INSERT OR IGNORE INTO deljenje_tocka"
            "(deljenje, ts, along_m, odmik_m, natancnost_m, hitrost_ms) "
            "VALUES(?, ?, ?, ?, ?, ?)",
            (ident, t["ts"], round(along, 1), round(odmik, 1), t["acc"],
             None if hitrost is None else round(hitrost, 2)))
        lat, lon = v.trasa.tocka(along)
        d.update(along_m=along, zadnja_ts=t["ts"], lat=round(lat, 5), lon=round(lon, 5),
                 hitrost_ms=hitrost, zamuda_s=v.zamuda(along, t["ts"] - polnoc),
                 tock=d["tock"] + 1)
        sprejetih += 1
        zadnji = v.postanki[-1]
        if (along >= zadnji["along"] - v.na_postaji_m
                and (hitrost is None or hitrost < STOJI_MS)):
            d["konec"] = "cilj"
    if not d["konec"] and zdaj_ts - d["zacetek_ts"] > NAJDALJE_S:
        d["konec"] = "cas"
    # Potnik je ustavil: točke iz iste zahteve so še njegove in veljajo.
    if not d["konec"] and podatki.get("konec"):
        d["konec"] = "potnik"
    conn.execute(
        "UPDATE deljenje SET zadnja_ts = ?, along_m = ?, lat = ?, lon = ?, "
        "hitrost_ms = ?, zamuda_s = ?, tock = ?, zunaj = ?, konec = ? WHERE id = ?",
        (d["zadnja_ts"], d["along_m"], d["lat"], d["lon"], d["hitrost_ms"],
         d["zamuda_s"], d["tock"], d["zunaj"], d["konec"], ident))
    conn.commit()
    return {"deljenje": ident, "sprejetih": sprejetih, "konec": d["konec"],
            "stanje": stanje(conn, [trip_id], zdaj).get(trip_id)}


def _odmaknjen(conn: sqlite3.Connection, ident: str, odmik: float,
               acc: float | None) -> bool:
    """Ali se je potnik, medtem ko vozilo stoji, odmaknil od trase vstran.

    Merilo je prva natančna točka sedanjega stanja -- za zadnjim odsekom, na
    katerem se je vozilo peljalo. Vlak na stranskem tiru je od trase lahko
    tudi 60 m, a ves postanek enako daleč.
    """
    if acc is None or acc > VSTRAN_M:
        return False
    tocke = conn.execute(
        "SELECT ts, along_m, odmik_m, natancnost_m FROM deljenje_tocka "
        "WHERE deljenje = ? ORDER BY ts DESC LIMIT 400", (ident,)).fetchall()
    stanje = tocke[:1]
    for nova, stara in zip(tocke, tocke[1:]):
        if (nova["along_m"] - stara["along_m"]) / max(nova["ts"] - stara["ts"], 1) >= VOZI_MS:
            break
        stanje.append(stara)
    natancne = [t for t in stanje
                if t["natancnost_m"] is not None and t["natancnost_m"] <= VSTRAN_M]
    if not natancne:
        return False
    ref = natancne[-1]
    return abs(odmik - ref["odmik_m"]) > VSTRAN_M + acc + ref["natancnost_m"]


def _prehodi(conn: sqlite3.Connection, v: Voznja, ident: str, dan: str,
             a0: float, t0: int, a1: float, t1: int) -> None:
    """Zapiše prihode in odhode na postaje, ki jih je vozilo prečkalo.

    Prihod je trenutek, ko vozilo pride na `NA_POSTAJI_M` od postaje, odhod
    trenutek, ko to razdaljo zapusti na drugi strani. Čas je linearno
    vmesen med točkama; pri točkah na 3--5 s je to napaka nekaj sekund.
    Odhod je zato nekoliko pozen (vlak še pospešuje) -- surove točke so
    shranjene, da se to lahko kdaj popravi. Čez rob, ki ga je potnik prehodil
    (`VOZI_MS`), vozilo ni ne prišlo ne odpeljalo.
    """
    if a1 <= a0 or (a1 - a0) / max(t1 - t0, 1) < VOZI_MS:
        return
    r = v.na_postaji_m

    def cas(meja: float) -> int:
        return round(t0 + (meja - a0) / (a1 - a0) * (t1 - t0))

    for s in v.postanki:
        prihod = s["along"] - r if s is not v.postanki[0] else None
        odhod = s["along"] + r if s is not v.postanki[-1] else None
        if prihod is not None and a0 < prihod <= a1:
            conn.execute(
                "INSERT INTO deljenje_prehod(deljenje, trip_id, service_date, stop_seq, prihod_ts) "
                "VALUES(?, ?, ?, ?, ?) ON CONFLICT(deljenje, stop_seq) "
                "DO UPDATE SET prihod_ts = COALESCE(prihod_ts, excluded.prihod_ts)",
                (ident, v.trip_id, dan, s["stop_seq"], cas(prihod)))
        if odhod is not None and a0 < odhod <= a1:
            conn.execute(
                "INSERT INTO deljenje_prehod(deljenje, trip_id, service_date, stop_seq, odhod_ts) "
                "VALUES(?, ?, ?, ?, ?) ON CONFLICT(deljenje, stop_seq) "
                "DO UPDATE SET odhod_ts = COALESCE(odhod_ts, excluded.odhod_ts)",
                (ident, v.trip_id, dan, s["stop_seq"], cas(odhod)))


# ---------------------------------------------------------------- stanje

def _soglasni(vrstice: list[dict]) -> list[dict]:
    """Največja skupina poročil, katerih zamude so si v `SOGLASJE_S`."""
    vrstice = sorted(vrstice, key=lambda r: r["zamuda_s"])
    naj: list[dict] = []
    for i in range(len(vrstice)):
        skupina = [r for r in vrstice[i:]
                   if r["zamuda_s"] - vrstice[i]["zamuda_s"] <= SOGLASJE_S]
        if len(skupina) > len(naj):
            naj = skupina
    return naj


def stanje(conn: sqlite3.Connection, trip_ids: list[str],
           zdaj: datetime | None = None) -> dict[str, dict]:
    """Kaj poročajo potniki o teh vožnjah, po `trip_id`.

    Samo sveža poročila (`SVEZE_S`) povedo, kje je vozilo; prehodi pa so
    opažanja in veljajo ves dan, tudi ko je poročevalec že izstopil.

    `soglasje` je res samo, kadar se ujemata vsaj dva neodvisna poročevalca
    -- takrat prikaz feeda za lego in prehod ne rabi več.
    """
    ids = list(dict.fromkeys(t for t in trip_ids if t))
    if not ids:
        return {}
    zdaj = zdaj or datetime.now(TZ)
    zdaj_ts = int(zdaj.timestamp())
    dnevi = [d for d, _ in _dneva(zdaj)]
    marks = ",".join("?" * len(ids))
    sveze = conn.execute(
        f"SELECT id, trip_id, service_date, zadnja_ts, along_m, lat, lon, "
        f"       hitrost_ms, zamuda_s "
        f"FROM deljenje WHERE trip_id IN ({marks}) AND zadnja_ts >= ? "
        f"  AND konec IS NULL AND along_m IS NOT NULL AND zamuda_s IS NOT NULL "
        f"  AND service_date IN (?, ?)",
        (*ids, zdaj_ts - SVEZE_S, *dnevi)).fetchall()
    prehodi = conn.execute(
        f"SELECT trip_id, service_date, stop_seq, "
        f"       COUNT(odhod_ts) AS n_odhod, "
        f"       CAST(AVG(odhod_ts) AS INTEGER) AS odhod_ts, "
        f"       CAST(AVG(prihod_ts) AS INTEGER) AS prihod_ts "
        f"FROM deljenje_prehod WHERE trip_id IN ({marks}) AND service_date IN (?, ?) "
        f"GROUP BY trip_id, service_date, stop_seq",
        (*ids, *dnevi)).fetchall()

    po_voznji: dict[str, list[dict]] = {}
    for r in sveze:
        po_voznji.setdefault(r["trip_id"], []).append(dict(r))
    out: dict[str, dict] = {}
    for trip_id, vrstice in po_voznji.items():
        v = voznja(conn, trip_id)
        if v is None:
            continue
        # En dan na vožnjo: nočni vlak ima lahko sled včeraj in danes.
        dan = max(r["service_date"] for r in vrstice)
        vrstice = [r for r in vrstice if r["service_date"] == dan]
        skupina = _soglasni(vrstice)
        glavna = max(skupina, key=lambda r: r["zadnja_ts"])
        now_s = zdaj_ts - stats.polnoc(dan)
        along = glavna["along_m"]
        stoji = glavna["hitrost_ms"] is not None and glavna["hitrost_ms"] < STOJI_MS
        zamude = sorted(r["zamuda_s"] for r in skupina)
        zamuda = zamude[len(zamude) // 2]
        if stoji:
            # Vozilo, ki stoji po voznorednem odhodu, zamuja vsako sekundo
            # bolj -- tudi med dvema točkama.
            zamuda = max(zamuda, v.zamuda(along, now_s))
        out[trip_id] = {
            "service_date": dan,
            "n": len(vrstice),
            "soglasje": len(skupina) >= 2,
            "starost_s": zdaj_ts - glavna["zadnja_ts"],
            "lat": glavna["lat"], "lon": glavna["lon"],
            "along_m": round(along),
            "stoji": stoji,
            # Okno vožnje z njo pomika vlak med poročili (`ocenjenaLega`).
            "hitrost_ms": (None if glavna["hitrost_ms"] is None
                           else round(glavna["hitrost_ms"], 1)),
            "zamuda_s": zamuda,
            "zamuda": stats.opis_zamude(zamuda, "po poročilu potnikov"),
            **_kje(v, along),
            "prehodi": {},
        }
    # Brez svežih poročil velja zadnji prometni dan s prehodi. Dnevni vlak
    # ima isti `trip_id` vsak dan -- včerajšnji prehod ne sme obveljati danes;
    # to preverijo še klicatelji (`dopolni` po dnevu vrstice).
    zadnji_dan: dict[str, str] = {}
    for r in prehodi:
        zadnji_dan[r["trip_id"]] = max(zadnji_dan.get(r["trip_id"], ""), r["service_date"])
    for r in prehodi:
        st = out.get(r["trip_id"])
        if st is None:
            st = out[r["trip_id"]] = {"service_date": zadnji_dan[r["trip_id"]], "n": 0,
                                      "soglasje": False, "prehodi": {}}
        if r["service_date"] != st["service_date"]:
            continue
        st["prehodi"][r["stop_seq"]] = {
            "odhod": _iso(r["odhod_ts"]), "prihod": _iso(r["prihod_ts"]),
            "n": r["n_odhod"],
        }
    return out


def za_postanek(conn: sqlite3.Connection, st: dict, trip_id: str, stop_seq: int,
                t_s: int | None = None) -> dict | None:
    """Kaj poročilo pove o enem postanku: odpeljal, stoji tu ali še pride.

    To bere tabla in iskalnik. `pricakovano` je čas, ko bo vozilo tu, če
    obdrži sedanjo zamudo -- isto pravilo kot prenos zamude v modelu, a iz
    lege, ki jo je nekdo pravkar izmeril. `t_s` je voznoredna ura, ki jo
    vrstica kaže (odhod na odhodni tabli, prihod na prihodni); brez nje
    prihod.
    """
    v = voznja(conn, trip_id)
    if v is None:
        return None
    s = next((p for p in v.postanki if p["stop_seq"] == stop_seq), None)
    if s is None:
        return None
    prehod = st.get("prehodi", {}).get(stop_seq)
    if prehod and prehod.get("odhod"):
        return {"odpeljal": prehod["odhod"], "n": prehod["n"]}
    if st.get("along_m") is None:
        return None
    dan = st["service_date"]
    along = st["along_m"]
    if along > s["along"] + v.na_postaji_m:
        return {"odpeljal": None, "mimo": True, "n": st["n"]}
    if abs(along - s["along"]) <= v.na_postaji_m:
        return {"tu": True, "n": st["n"], "zamuda_s": st["zamuda_s"]}
    t = t_s if t_s is not None else (s["arr_s"] if s["arr_s"] is not None else s["dep_s"])
    return {"pricakovano": stats.abs_time(dan, t + st["zamuda_s"]),
            "zamuda_s": st["zamuda_s"], "n": st["n"]}


def _dan_vrstice(r: dict, t_s: str, ura: str) -> str | None:
    """Prometni dan vrstice: voznoredna ura minus sekunde od polnoči.

    Tabla nosi tudi včerajšnje nočne vožnje, dan pa v vrstici ni zapisan.
    """
    if r.get(ura) is None or r.get(t_s) is None:
        return None
    return (datetime.fromisoformat(r[ura]) - timedelta(seconds=r[t_s])).date().isoformat()


def dopolni(conn: sqlite3.Connection, vrstice: list[dict], *, seq: str, t_s: str,
            pricakovano: str, ura: str, zdaj: datetime | None = None) -> None:
    """Vrsticam table ali iskalnika doda, kar poročajo potniki.

    Ključi se razlikujejo med tablo (`stop_seq`, `t_s`, `expected`, `sched`)
    in iskalnikom (`from_seq`, `dep_s`, `expected_dep`, `sched_dep`), zato jih
    pove klicatelj.

    Z enim poročevalcem vrstica dobi samo `potniki` -- feed ostane, kot je.
    S soglasjem vsaj dveh poročilo **zamenja** feedovo zamudo, pričakovano uro
    in nepotrjen odhod: sklep iz ure ni več potreben, ker je opažanje.
    """
    if not vrstice:
        return
    zdaj = zdaj or datetime.now(TZ)
    st_vse = stanje(conn, [r["trip_id"] for r in vrstice], zdaj)
    if not st_vse:
        return
    for r in vrstice:
        st = st_vse.get(r["trip_id"])
        if not st or _dan_vrstice(r, t_s, ura) != st["service_date"]:
            continue
        p = za_postanek(conn, st, r["trip_id"], r[seq], r.get(t_s))
        if not p:
            continue
        # Prehod je opažanje enega deljenja; soglasje o njem je, kadar ga je
        # videlo več deljenj. O legi pa soglašajo sveža poročila.
        p["soglasje"] = (p["n"] >= 2 if p.get("odpeljal") else st["soglasje"])
        if st.get("along_m") is not None:
            p["starost_s"] = st["starost_s"]
            p["kje"] = {k: st[k] for k in ("pri", "med") if k in st}
        r["potniki"] = p
        if not p["soglasje"]:
            continue
        sched_s = r[t_s]
        if p.get("odpeljal"):
            z = int(datetime.fromisoformat(p["odpeljal"]).timestamp()
                    - stats.polnoc(st["service_date"]) - sched_s)
            r[pricakovano] = p["odpeljal"]
        elif p.get("mimo"):
            # Mimo je, a kdaj, ne vemo: deljenje se je začelo za postajo.
            # Zamuda ostane feedova, vrstica pa ni več „morda še pride“.
            r["nepotrjen_do"] = None
            if (not r.get(pricakovano)
                    or datetime.fromisoformat(r[pricakovano]) > zdaj):
                r[pricakovano] = zdaj.isoformat(timespec="seconds")
            continue
        else:
            z = p["zamuda_s"]
            r[pricakovano] = stats.abs_time(st["service_date"], sched_s + z)
        r["delay_s"] = z
        r["delay_kind"] = "po poročilu potnikov"
        # Kraj feedove meritve ne sodi več k tej številki.
        for k in ("delay_from", "delay_at"):
            if k in r:
                r[k] = None
        r["zamuda"] = stats.opis_zamude(z, "po poročilu potnikov")
        r["nepotrjen_do"] = None


# ---------------------------------------------------------------- pregled

def _kosi(t: Trasa, od_m: float = 0.0, do_m: float = math.inf) -> list[list[list[float]]]:
    """Del trase med dvema razdaljama vzdolž nje, [lat, lon], za risanje.

    Razrezan na vrzelih: ravna črta čez vrzel ni kraj, kjer vozilo vozi
    (glej `Trasa`). Vrzel `i` je odsek med točkama `i` in `i + 1`.
    """
    cum, tocke, vrzeli = t.cum, t.tocke, t.vrzeli
    od_m, do_m = max(od_m, 0.0), min(do_m, t.dolzina)
    if do_m <= od_m:
        return []
    kosi: list[list[tuple[float, float]]] = []
    kos: list[tuple[float, float]] = []
    for i in range(len(tocke)):
        if cum[i] <= od_m:
            continue
        if not kos and not kosi and i > 0 and (i - 1) not in vrzeli:
            kos.append(t.tocka(od_m))
        if cum[i] >= do_m:
            if (i - 1) not in vrzeli:
                kos.append(t.tocka(do_m))
            break
        kos.append(tocke[i])
        if i in vrzeli:
            kosi.append(kos)
            kos = []
    kosi.append(kos)
    return [[[round(la, 5), round(lo, 5)] for la, lo in k] for k in kosi if len(k) >= 2]


def deli_zdaj(conn: sqlite3.Connection, zdaj: datetime | None = None) -> int:
    """Koliko deljenj ta hip teče -- značka na zavihku pregleda."""
    zdaj_ts = int((zdaj or datetime.now(TZ)).timestamp())
    return conn.execute(
        "SELECT COUNT(*) FROM deljenje WHERE konec IS NULL AND zadnja_ts >= ? "
        "AND zacetek_ts >= ?", (zdaj_ts - SVEZE_S, zdaj_ts - NAJDALJE_S)).fetchone()[0]


def pregled(conn: sqlite3.Connection, zdaj: datetime | None = None) -> dict:
    """Današnja deljenja po vozilih, za skrbnika (`/admin`).

    Kar vidi javnost -- število poročevalcev, soglasje, lega in zamuda --
    pride iz `stanje()`, ne iz lastnega računa: pregled mora pokazati isto
    kot tabla in zemljevid, sicer ne pove ničesar o tem, kar potnik vidi.
    Zraven je feedova zamuda (in pri avtobusu GPS), da se razhajanje vidi.

    Sled deljenja je del trase med prvo in zadnjo sprejeto točko. Surovih
    koordinat ni (glej `SHEMA`), in vozilo s trase ne gre.
    """
    zdaj = zdaj or datetime.now(TZ)
    zdaj_ts = int(zdaj.timestamp())
    polnoc = stats.polnoc(zdaj.date().isoformat())
    # `zacetek_ts` ima kazalo; deljenje, ki je začelo pred polnočjo, ni daljše
    # od `NAJDALJE_S`.
    vrstice = [dict(r) for r in conn.execute(
        "SELECT d.*, MIN(t.along_m) AS od_m, MAX(t.along_m) AS do_m, "
        "       (SELECT COUNT(*) FROM deljenje_prehod p WHERE p.deljenje = d.id) AS prehodov "
        "FROM deljenje d LEFT JOIN deljenje_tocka t ON t.deljenje = d.id "
        "WHERE d.zacetek_ts >= ? GROUP BY d.id ORDER BY d.zacetek_ts",
        (polnoc - NAJDALJE_S,))
        if max(r["zacetek_ts"], r["zadnja_ts"]) >= polnoc]

    po_vozilu: dict[tuple[str, str], list[dict]] = {}
    for r in vrstice:
        po_vozilu.setdefault((r["trip_id"], r["service_date"]), []).append(r)
    ids = list(dict.fromkeys(t for t, _ in po_vozilu))
    marks = ",".join("?" * len(ids))
    tripi = {r["trip_id"]: dict(r) for r in conn.execute(
        f"SELECT trip_id, train_no, headsign, network, mode, agency "
        f"FROM trip WHERE trip_id IN ({marks})", ids)} if ids else {}
    javno = stanje(conn, ids, zdaj)
    gps = _gps(conn, [t for t in ids if tripi.get(t, {}).get("network") == "avtobus"], zdaj_ts)
    feed: dict[tuple[str, str], dict] = {}
    for dan in {d for _, d in po_vozilu}:
        naj = [t for t, d in po_vozilu if d == dan]
        for trip_id, m in stats.last_measured(conn, dan, naj, zdaj_ts - stats.polnoc(dan)).items():
            feed[(trip_id, dan)] = m

    vozila = []
    for (trip_id, dan), dd in po_vozilu.items():
        v = voznja(conn, trip_id)
        t = tripi.get(trip_id, {})
        st = javno.get(trip_id)
        zivo = bool(st and st.get("along_m") is not None and st["service_date"] == dan)
        m = feed.get((trip_id, dan))
        deljenja = []
        for r in dd:
            sveze = r["konec"] is None and r["zadnja_ts"] >= zdaj_ts - SVEZE_S
            deljenja.append({
                "zacetek": _iso(r["zacetek_ts"]), "zadnja": _iso(r["zadnja_ts"]),
                "trajanje_s": max(0, r["zadnja_ts"] - r["zacetek_ts"]),
                "tock": r["tock"], "prehodov": r["prehodov"],
                # Brez konca in brez svežih točk: aplikacija je utihnila
                # (zaprta, brez signala) in deljenja ni nihče ustavil.
                "izid": r["konec"] or ("deli" if sveze else "utihnil"),
                "zamuda": stats.opis_zamude(r["zamuda_s"], "po poročilu potnikov"),
                "hitrost_ms": r["hitrost_ms"],
                "lat": r["lat"], "lon": r["lon"],
                "sled": (_kosi(v.trasa, r["od_m"], r["do_m"])
                         if v is not None and r["od_m"] is not None else []),
            })
        g = gps.get(trip_id)
        vozila.append({
            "trip_id": trip_id, "service_date": dan,
            **{k: t.get(k) for k in ("train_no", "headsign", "network", "mode", "agency")},
            "od": v.postanki[0]["name"] if v else None,
            "do": v.postanki[-1]["name"] if v else None,
            "zivo": zivo,
            "javno": ({k: st[k] for k in ("n", "soglasje", "starost_s", "lat", "lon",
                                           "stoji", "zamuda", "pri", "med") if k in st}
                      if zivo else None),
            # Samo ob živem deljenju: feedova zamuda zdaj in potnikova izpred
            # dveh ur nista primerjava, ampak dva različna trenutka.
            "feed": ({"zamuda": stats.opis_zamude(m["delay_s"], "izmerjeno"),
                      "feed_ts": m.get("feed_ts")}
                     if zivo and m and m.get("delay_s") is not None else None),
            "gps": ({"lat": g["lat"], "lon": g["lon"], "starost_s": zdaj_ts - g["seen_ts"]}
                    if g else None),
            "zadnja_ts": max(r["zadnja_ts"] for r in dd),
            # Cela trasa samo živim: odgovor se vleče na 10 s, in trasa je do
            # 40 kB -- sto končanih vožnji na dan bi bilo nekaj MB na obhod.
            "trasa": _kosi(v.trasa) if v and zivo else [],
            "deljenja": deljenja,
        })
    vozila.sort(key=lambda x: (not x["zivo"], -x["zadnja_ts"]))

    izidi: dict[str, int] = {}
    for x in vozila:
        for d in x["deljenja"]:
            izidi[d["izid"]] = izidi.get(d["izid"], 0) + 1
    return {
        "zdaj": zdaj.isoformat(timespec="seconds"),
        "sveze_s": SVEZE_S,
        "povzetek": {
            "deljenj": len(vrstice),
            "tock": sum(r["tock"] for r in vrstice),
            "prehodov": sum(r["prehodov"] for r in vrstice),
            "vozil": len(vozila),
            "vozil_zdaj": sum(x["zivo"] for x in vozila),
            "deli_zdaj": izidi.get("deli", 0),
            "izidi": izidi,
        },
        "vozila": vozila,
    }
