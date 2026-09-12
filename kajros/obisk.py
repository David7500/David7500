"""Kdo je bil na strani — števci obiska brez osebnih podatkov.

Doslej tega ni vedel nihče. Strežnik ni beležil ničesar, pred njim pa stoji
Cloudflarov tunel, ki svojega dnevnika ne da; vprašanje „koliko različnih
ljudi to sploh odpre“ je bilo torej neodgovorljivo. Projekt, ki ima za prvo
pravilo „meri, ne domnevaj“, o sebi ni meril ničesar.

**IP se ne shrani nikoli.** Obiskovalec je šestnajst znakov
`blake2s(sol dneva ‖ IP ‖ User-Agent)`, sol pa je šestnajst naključnih bajtov,
ki se ob prehodu dneva zavržejo in nadomestijo. Iz zapisa ni poti nazaj do
naslova, in dveh dni ne more povezati **nihče, tudi mi ne**. Cena te odločitve
je zapisana pri `pregled()`: mesečnih unikatov ni, ker jih iz dnevnih ključev
ni mogoče izračunati — samo vsota dnevnih, ki isto osebo šteje večkrat.

**Pisanje ne gre v zahtevo.** Števci se nabirajo v pomnilniku in jih ena nit
izprazni vsakih `IZPRAZNI_S`. En obisk strani ni ena zahteva, ampak 10–30:
zemljevid anketira lege vsakih 10 s in zamude vsakih 30 s, dokler je zavihek
odprt. Vrstica na zahtevo bi torej pomenila stalno pisanje v isto bazo, v
katero teče zajem — in zajem je edino, česar ni mogoče ponoviti za nazaj.

Kar ta modul namenoma **ni**: ni sledilnik poti posameznika po strani. Vrstica
o obiskovalcu nosi štiri števila (zahteve, ogledi, prvi in zadnji dotik), ne
zaporedja strani. Kdo je kam kliknil, se iz tega ne da sestaviti.
"""

from __future__ import annotations

import hashlib
import re
import secrets
import sqlite3
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from . import config, db

TZ = ZoneInfo(config.TIMEZONE)

#: Kako pogosto gredo števci iz pomnilnika v bazo. Minuta je izbrana tako, da
#: je zapis redek proti zajemu (30 s) in da ob padcu procesa izgubimo največ
#: minuto števcev -- to niso meritve zamud, ampak statistika obiska.
IZPRAZNI_S = 60

#: Zgornje meje razredov odzivnega časa v milisekundah; kar je počasnejše od
#: zadnje, pade v vedro `len(VEDRA)`. Natančnih časov ne hranimo -- za
#: vprašanje „ali je stran komu počasna“ je razred dovolj, vsota vseh časov
#: pa je zapisana posebej in da povprečje.
VEDRA = (10, 25, 50, 100, 250, 500, 1000, 2500, 5000)

#: Varovalka pred neomejeno rastjo pomnilnika med dvema praznjenjema. Ključev
#: je v normalnem teku nekaj sto (35 poti × 24 ur); če jih je toliko, nas
#: nekdo namerno preiskuje z izmišljenimi naslovi in nadaljnje štetje ne
#: pove ničesar novega.
NAJVEC_KLJUCEV = 20_000

#: Kar ni nobena naša pot. Vse take zahteve gredo v eno samo vrstico: brez
#: tega bi en sam bot, ki ugiba `/wp-admin/…`, naredil tisoče vrstic na dan.
NEZNANO = "(neznano)"

# Samopredstavitev programja. Nihče od teh ni človek in vsi bi popačili
# številko, zaradi katere ta modul obstaja. Ujame tudi naš lastni chromium
# (`--headless`) iz `scripts/preveri.sh` in `curl` iz istega skripta.
#
# `python-` brez naštevanja knjižnic: prva različica je imela
# `python-requests|python-httpx` in **spregledala `Python-urllib`**, s katerim
# je tekel naš lastni preizkus hitrosti -- 2 012 zahtev se je v pregledu
# pokazalo kot „računalnik". Ujeto na zaslonu, ne v testu.
_BOT = re.compile(
    r"bot\b|bot/|crawl|spider|slurp|facebookexternalhit|bingpreview|"
    r"headless|phantom|python-|python/|aiohttp|okhttp|"
    r"curl/|wget|scrapy|go-http-client|java/|libwww|"
    r"uptime|pingdom|monitor|probe|scanner|nuclei|zgrab|masscan",
    re.I)
# Vrstni red šteje: tablični Android nima „Mobi“, iPad pa se v novem
# iPadOS predstavlja kot Macintosh -- tega ne ujamemo in pade med računalnike.
_TABLICA = re.compile(r"iPad|Tablet|PlayBook|Silk", re.I)
_TELEFON = re.compile(r"Mobi|Android|iPhone|iPod|Windows Phone|Opera Mini", re.I)


SHEMA = """
-- Števci po poti in dnevu. `vrsta` loči stran od klica API -- brez tega je
-- „ogledov strani“ nerazločljivo od anketiranja, ki teče v ozadju zavihka.
CREATE TABLE IF NOT EXISTS obisk_pot (
    dan      TEXT    NOT NULL,
    pot      TEXT    NOT NULL,     -- oblika poti, ne naslov: /app/train/{train_no}
    vrsta    TEXT    NOT NULL,     -- stran | api | drugo
    zahtev   INTEGER NOT NULL DEFAULT 0,
    ljudi    INTEGER NOT NULL DEFAULT 0,   -- od tega tistih, ki niso boti
    napak4   INTEGER NOT NULL DEFAULT 0,
    napak5   INTEGER NOT NULL DEFAULT 0,
    ms_vsota REAL    NOT NULL DEFAULT 0,
    ms_naj   REAL    NOT NULL DEFAULT 0,
    PRIMARY KEY (dan, pot, vrsta)
);

-- Razrezi, ki so vsi iste oblike (ura dneva, naprava, država, brskalnik).
-- Ena tabela in ne štiri: nov razrez je s tem nov `razsez`, ne nova tabela
-- in nova migracija.
CREATE TABLE IF NOT EXISTS obisk_razrez (
    dan     TEXT    NOT NULL,
    razsez  TEXT    NOT NULL,      -- ura | naprava | drzava
    kljuc   TEXT    NOT NULL,
    zahtev  INTEGER NOT NULL DEFAULT 0,
    ogledov INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (dan, razsez, kljuc)
);

-- Ena vrstica na obiskovalca na dan. `kljuc` je zgoščena vrednost s soljo,
-- ki se ob polnoči zavrže -- ista naprava ima jutri drug ključ in povezave
-- med dnevoma ni. To je namerno; glej opis modula.
CREATE TABLE IF NOT EXISTS obiskovalec (
    dan      TEXT    NOT NULL,
    kljuc    TEXT    NOT NULL,
    bot      INTEGER NOT NULL DEFAULT 0,
    zahtev   INTEGER NOT NULL DEFAULT 0,
    ogledov  INTEGER NOT NULL DEFAULT 0,
    prvi_s   INTEGER NOT NULL,
    zadnji_s INTEGER NOT NULL,
    PRIMARY KEY (dan, kljuc)
);
CREATE INDEX IF NOT EXISTS obiskovalec_dan ON obiskovalec(dan, bot);

-- Porazdelitev odzivnega časa po razredih (`VEDRA`). Mediana in p95 se iz
-- nje izračunata na razred natančno; povprečje da `obisk_pot.ms_vsota`.
CREATE TABLE IF NOT EXISTS obisk_odziv (
    dan   TEXT    NOT NULL,
    pot   TEXT    NOT NULL,
    vedro INTEGER NOT NULL,
    n     INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (dan, pot, vedro)
);
"""

# --------------------------------------------------------------- zbiranje

_zaklep = threading.Lock()
# (dan, pot, vrsta) -> [zahtev, ljudi, napak4, napak5, ms_vsota, ms_naj]
_poti: dict[tuple[str, str, str], list] = {}
# (dan, razsez, kljuc) -> [zahtev, ogledov]
_razrezi: dict[tuple[str, str, str], list] = {}
# (dan, kljuc) -> [bot, zahtev, ogledov, prvi_s, zadnji_s]
_ljudje: dict[tuple[str, str], list] = {}
# (dan, pot, vedro) -> n
_odzivi: dict[tuple[str, str, int], int] = {}
# dan -> sol. Samo v pomnilniku; v bazo gre ob praznjenju, da restart sredi
# dneva istega obiskovalca ne razdeli na dva.
_soli: dict[str, bytes] = {}
_prelito = False                  # ali smo zadeli NAJVEC_KLJUCEV


def init(conn: sqlite3.Connection) -> None:
    """Ustvari tabele in prevzame današnjo sol, če je proces že tekel."""
    conn.executescript(SHEMA)
    conn.commit()
    shranjeno = db.get_meta(conn, "obisk_sol")
    if shranjeno and ":" in shranjeno:
        dan, _, hex_ = shranjeno.partition(":")
        if dan == _danes():
            with _zaklep:
                _soli[dan] = bytes.fromhex(hex_)


def _danes() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d")


def sol(dan: str) -> bytes:
    """Sol dneva. Nastane ob prvi rabi in se ob prehodu dneva zavrže."""
    with _zaklep:
        if dan not in _soli:
            _soli.clear()         # včerajšnje soli ne hranimo niti v pomnilniku
            _soli[dan] = secrets.token_bytes(16)
        return _soli[dan]


def kljuc_obiskovalca(ip: str, ua: str, dan: str) -> str:
    """Šestnajst znakov, iz katerih ni poti nazaj do naslova.

    `blake2s` in ne `sha256`: razlika je nezaznavna, a funkcija sprejme sol
    kot `key` in ne kot zlepljen niz, kar je manj priložnosti za napako.
    """
    h = hashlib.blake2s(key=sol(dan), digest_size=8)
    h.update(ip.encode("utf-8", "replace"))
    h.update(b"\x00")
    h.update(ua.encode("utf-8", "replace"))
    return h.hexdigest()


def je_bot(ua: str) -> bool:
    if not ua:
        return True               # brskalnik se vedno predstavi; program ne
    return bool(_BOT.search(ua))


def naprava(ua: str) -> str:
    # Naš lastni ovoj za Android se predstavi kot `Kajros/<različica>` in ni
    # brskalnik: budilka vpraša strežnik tudi takrat, ko nihče ne gleda. Če bi
    # padel med telefone, bi ga bilo od človeka na strani nemogoče ločiti --
    # in prav ta razlika je tisto, zaradi česar se razrez sploh bere.
    if ua.startswith("Kajros/"):
        return "aplikacija"
    if not ua:
        return "neznano"
    if _TABLICA.search(ua):
        return "tablica"
    if _TELEFON.search(ua):
        return "telefon"
    return "računalnik"


def vrsta_poti(pot: str) -> str:
    if pot == "/" or pot.startswith("/app"):
        return "stran"
    if pot.startswith("/api"):
        return "api"
    return "drugo"


def vedro(ms: float) -> int:
    for i, meja in enumerate(VEDRA):
        if ms <= meja:
            return i
    return len(VEDRA)


def zabelezi(pot: str, vrsta: str, kljuc: str, bot: bool, naprava_: str,
             drzava: str, koda: int, ms: float, zdaj: float | None = None,
             ura: int | None = None, dan: str | None = None) -> None:
    """Doda eno zahtevo v števce. Samo pomnilnik -- v bazo gre `izprazni()`."""
    global _prelito
    zdaj = time.time() if zdaj is None else zdaj
    trenutek = datetime.fromtimestamp(zdaj, TZ)
    dan = dan or trenutek.strftime("%Y-%m-%d")
    ura = trenutek.hour if ura is None else ura
    ogled = 1 if vrsta == "stran" else 0
    with _zaklep:
        if len(_poti) + len(_razrezi) + len(_ljudje) > NAJVEC_KLJUCEV:
            _prelito = True
            return
        p = _poti.setdefault((dan, pot, vrsta), [0, 0, 0, 0, 0.0, 0.0])
        p[0] += 1
        p[1] += 0 if bot else 1
        p[2] += 1 if 400 <= koda < 500 else 0
        p[3] += 1 if koda >= 500 else 0
        p[4] += ms
        p[5] = max(p[5], ms)

        kljuc_odziv = (dan, pot, vedro(ms))
        _odzivi[kljuc_odziv] = _odzivi.get(kljuc_odziv, 0) + 1

        # Razrezi so vprašanje o ljudeh, ne o strojih. Bot, ki vsako uro
        # pobere sitemap, bi sicer narisal enakomeren dan in ubil edino
        # zanimivo črto -- kdaj se ljudje res peljejo.
        if not bot:
            for razsez, k in (("ura", f"{ura:02d}"), ("naprava", naprava_),
                              ("drzava", drzava)):
                r = _razrezi.setdefault((dan, razsez, k), [0, 0])
                r[0] += 1
                r[1] += ogled

        o = _ljudje.setdefault((dan, kljuc), [0, 0, 0, int(zdaj), int(zdaj)])
        o[0] = max(o[0], int(bot))
        o[1] += 1
        o[2] += ogled
        o[3] = min(o[3], int(zdaj))
        o[4] = max(o[4], int(zdaj))


def ip_zahteve(glave, odjemalec: str | None) -> str:
    """Naslov obiskovalca izza posrednika.

    `CF-Connecting-IP` postavi Cloudflare in je edini, ki mu tu smemo verjeti:
    do procesa ne pride nič drugega kot tunel ali domače omrežje, ker
    strežnik ni izpostavljen naravnost (`docs/javna-postavitev.md`). Naslov
    se ne shrani -- gre samo skozi `kljuc_obiskovalca()`.
    """
    za = glave.get("cf-connecting-ip") or glave.get("x-forwarded-for") or ""
    if za:
        return za.split(",")[0].strip()
    return odjemalec or "?"


def iz_zahteve(request, koda: int, ms: float) -> None:
    """Zabeleži eno postreženo zahtevo. Kliče jo posrednik v `api.py`."""
    pot = oblika_poti(request)
    if pot is None:
        return
    glave = request.headers
    ua = glave.get("user-agent", "")
    bot = je_bot(ua)
    zabelezi(pot=pot, vrsta=vrsta_poti(request.url.path),
             kljuc=kljuc_obiskovalca(ip_zahteve(glave, _odjemalec(request)),
                                     ua, _danes()),
             bot=bot, naprava_=naprava(ua),
             drzava=(glave.get("cf-ipcountry") or "??").upper()[:2],
             koda=koda, ms=ms)


def _odjemalec(request) -> str | None:
    odj = getattr(request, "client", None)
    return getattr(odj, "host", None) if odj else None


# Oblike poti gradimo iz usmerjevalnika samega, ne iz seznama v kodi: sicer
# se ob novi strani seznam tiho razide in nova stran pade med `(neznano)`.
_vzorci: list[tuple] | None = None


def _zgradi_vzorce(app) -> list[tuple]:
    out = []
    for route in getattr(app, "routes", []):
        rx = getattr(route, "path_regex", None)
        oblika = getattr(route, "path_format", None)
        if rx is not None and oblika:
            out.append((rx, oblika))
    return out


def oblika_poti(request) -> str | None:
    """`/app/train/2010` -> `/app/train/{train_no}`; statika in admin -> nič.

    Brez tega ima vsaka vožnja svojo vrstico in tabela zraste s prometom, ne
    s številom strani. `None` pomeni „ne štej“.
    """
    global _vzorci
    pot = request.url.path
    if pot.startswith("/static") or pot.startswith("/admin"):
        return None
    if _vzorci is None:
        _vzorci = _zgradi_vzorce(request.scope.get("app"))
    for rx, oblika in _vzorci:
        if rx.match(pot):
            return oblika
    return NEZNANO


# -------------------------------------------------------------- praznjenje

def izprazni(conn: sqlite3.Connection) -> int:
    """Števce iz pomnilnika v bazo. Vrne število zapisanih vrstic.

    Ob napaki so števci že vzeti iz pomnilnika in torej izgubljeni. To je
    namerno: vrnitev nazaj bi ob trajni napaki pomnilnik polnila brez konca,
    izguba minute statistike obiska pa ne pokvari ničesar, kar bi bilo
    kasneje treba popraviti -- za razliko od meritve zamude.
    """
    global _prelito
    with _zaklep:
        if not (_poti or _razrezi or _ljudje or _odzivi):
            return 0
        poti = [(d, p, v, *st) for (d, p, v), st in _poti.items()]
        razrezi = [(d, r, k, *st) for (d, r, k), st in _razrezi.items()]
        ljudje = [(d, k, *st) for (d, k), st in _ljudje.items()]
        odzivi = [(d, p, ve, n) for (d, p, ve), n in _odzivi.items()]
        dan_soli = max(_soli) if _soli else None
        sol_ = _soli.get(dan_soli) if dan_soli else None
        preliv = _prelito
        _poti.clear(); _razrezi.clear(); _ljudje.clear(); _odzivi.clear()
        _prelito = False

    with conn:
        conn.executemany(
            "INSERT INTO obisk_pot(dan, pot, vrsta, zahtev, ljudi, napak4, napak5,"
            "                      ms_vsota, ms_naj) VALUES(?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(dan, pot, vrsta) DO UPDATE SET "
            "  zahtev = zahtev + excluded.zahtev, ljudi = ljudi + excluded.ljudi,"
            "  napak4 = napak4 + excluded.napak4, napak5 = napak5 + excluded.napak5,"
            "  ms_vsota = ms_vsota + excluded.ms_vsota,"
            "  ms_naj = MAX(ms_naj, excluded.ms_naj)", poti)
        conn.executemany(
            "INSERT INTO obisk_razrez(dan, razsez, kljuc, zahtev, ogledov)"
            " VALUES(?,?,?,?,?) "
            "ON CONFLICT(dan, razsez, kljuc) DO UPDATE SET "
            "  zahtev = zahtev + excluded.zahtev,"
            "  ogledov = ogledov + excluded.ogledov", razrezi)
        conn.executemany(
            "INSERT INTO obiskovalec(dan, kljuc, bot, zahtev, ogledov, prvi_s, zadnji_s)"
            " VALUES(?,?,?,?,?,?,?) "
            "ON CONFLICT(dan, kljuc) DO UPDATE SET "
            "  bot = MAX(bot, excluded.bot), zahtev = zahtev + excluded.zahtev,"
            "  ogledov = ogledov + excluded.ogledov,"
            "  prvi_s = MIN(prvi_s, excluded.prvi_s),"
            "  zadnji_s = MAX(zadnji_s, excluded.zadnji_s)", ljudje)
        conn.executemany(
            "INSERT INTO obisk_odziv(dan, pot, vedro, n) VALUES(?,?,?,?) "
            "ON CONFLICT(dan, pot, vedro) DO UPDATE SET n = n + excluded.n", odzivi)
        if sol_ is not None:
            # Sol preživi restart, dneva pa ne: ključ je `obisk_sol` in ne
            # `obisk_sol_<dan>`, zato jo naslednji dan povozi in včerajšnje
            # ni več nikjer.
            db.set_meta(conn, "obisk_sol", f"{dan_soli}:{sol_.hex()}")
        if preliv:
            db.set_meta(conn, "obisk_preliv", datetime.now(TZ).isoformat())
    return len(poti) + len(razrezi) + len(ljudje) + len(odzivi)


def prune(conn: sqlite3.Connection, dni: int | None = None) -> int:
    """Pobriše števce, starejše od `dni`. Vrne število pobrisanih vrstic."""
    dni = config.OBISK_KEEP_DAYS if dni is None else dni
    if dni <= 0:
        return 0
    meja = (datetime.now(TZ).date().toordinal() - dni)
    meja_iso = datetime.fromordinal(meja).strftime("%Y-%m-%d")
    n = 0
    with conn:
        for tabela in ("obisk_pot", "obisk_razrez", "obiskovalec", "obisk_odziv"):
            n += conn.execute(f"DELETE FROM {tabela} WHERE dan < ?", (meja_iso,)).rowcount
    return n


# ----------------------------------------------------------------- pregled

def _percentil(vedra: dict[int, int], p: float) -> dict:
    """Razred, v katerem leži p-ti percentil. Ne vrednost -- razred.

    Točnega časa ne hranimo, zato je pošteno povedati mejo razreda in ne
    izmišljene številke: `{"do": 250}` pomeni „hitreje od 250 ms“,
    `{"do": None}` pa „počasneje od zadnje meje“.
    """
    skupaj = sum(vedra.values())
    if not skupaj:
        return {"do": None, "n": 0}
    cilj = skupaj * p
    tekoce = 0
    for i in range(len(VEDRA) + 1):
        tekoce += vedra.get(i, 0)
        if tekoce >= cilj:
            return {"do": VEDRA[i] if i < len(VEDRA) else None, "n": skupaj}
    return {"do": None, "n": skupaj}


def pregled(conn: sqlite3.Connection, dni: int = 30) -> dict:
    """Vse, kar pokaže stran `/admin`. Ena poizvedba na vprašanje.

    **Mesečnega števila različnih ljudi tu ni in ga ne more biti.** Sol se
    vsak dan zavrže, zato je ista naprava jutri drug ključ; `ljudi_vsota` je
    vsota dnevnih in isto osebo šteje tolikokrat, kolikor dni je prišla. To
    je cena zasebnosti in je zapisana tudi na strani, da je številka ne bo
    kdo bral kot mesečne unikate.
    """
    danes = _danes()
    od = datetime.fromordinal(
        datetime.now(TZ).date().toordinal() - dni + 1).strftime("%Y-%m-%d")

    po_dnevih = [dict(r) for r in conn.execute(
        "SELECT o.dan,"
        "       SUM(CASE WHEN o.bot = 0 THEN 1 ELSE 0 END) AS ljudi,"
        "       SUM(CASE WHEN o.bot = 1 THEN 1 ELSE 0 END) AS botov,"
        "       SUM(CASE WHEN o.bot = 0 THEN o.ogledov ELSE 0 END) AS ogledov,"
        "       SUM(o.zahtev) AS zahtev "
        "FROM obiskovalec o WHERE o.dan >= ? GROUP BY o.dan ORDER BY o.dan",
        (od,))]

    strani = [dict(r) for r in conn.execute(
        "SELECT pot, SUM(zahtev) AS zahtev, SUM(ljudi) AS ljudi "
        "FROM obisk_pot WHERE dan >= ? AND vrsta = 'stran' "
        "GROUP BY pot ORDER BY ljudi DESC, zahtev DESC", (od,))]

    # Odzivni čas in napake: obojega ne meri nihče drug. Cloudflare vidi svoj
    # rob, ne našega izračuna, in 2,7 s za `/api/health` je pri njem videti
    # enako kot 3 ms.
    vedra: dict[str, dict[int, int]] = {}
    for r in conn.execute(
            "SELECT pot, vedro, SUM(n) AS n FROM obisk_odziv WHERE dan >= ? "
            "GROUP BY pot, vedro", (od,)):
        vedra.setdefault(r["pot"], {})[r["vedro"]] = r["n"]

    endpointi = []
    for r in conn.execute(
            "SELECT pot, SUM(zahtev) AS zahtev, SUM(napak4) AS napak4,"
            "       SUM(napak5) AS napak5, SUM(ms_vsota) AS ms_vsota,"
            "       MAX(ms_naj) AS ms_naj "
            "FROM obisk_pot WHERE dan >= ? GROUP BY pot "
            "ORDER BY zahtev DESC", (od,)):
        v = vedra.get(r["pot"], {})
        endpointi.append({
            "pot": r["pot"], "zahtev": r["zahtev"],
            "napak4": r["napak4"], "napak5": r["napak5"],
            "ms_povprecje": round(r["ms_vsota"] / r["zahtev"], 1) if r["zahtev"] else None,
            "ms_naj": round(r["ms_naj"], 1),
            "p50": _percentil(v, 0.50), "p95": _percentil(v, 0.95),
        })

    razrezi: dict[str, list] = {}
    for r in conn.execute(
            "SELECT razsez, kljuc, SUM(zahtev) AS zahtev, SUM(ogledov) AS ogledov "
            "FROM obisk_razrez WHERE dan >= ? GROUP BY razsez, kljuc "
            "ORDER BY razsez, ogledov DESC, zahtev DESC", (od,)):
        razrezi.setdefault(r["razsez"], []).append(dict(r))
    if "ura" in razrezi:
        razrezi["ura"].sort(key=lambda x: x["kljuc"])

    danasnji = next((d for d in po_dnevih if d["dan"] == danes), None)
    skupaj = {
        "ljudi_vsota": sum(d["ljudi"] for d in po_dnevih),
        "ogledov": sum(d["ogledov"] for d in po_dnevih),
        "zahtev": sum(d["zahtev"] for d in po_dnevih),
        "botov_vsota": sum(d["botov"] for d in po_dnevih),
        "napak4": sum(e["napak4"] for e in endpointi),
        "napak5": sum(e["napak5"] for e in endpointi),
    }
    zadnjih7 = po_dnevih[-7:]
    return {
        "dni": dni, "od": od, "do": danes,
        "danes": danasnji or {"dan": danes, "ljudi": 0, "botov": 0,
                              "ogledov": 0, "zahtev": 0},
        "teden": {"ljudi_vsota": sum(d["ljudi"] for d in zadnjih7),
                  "ogledov": sum(d["ogledov"] for d in zadnjih7),
                  "dni": len(zadnjih7)},
        "skupaj": skupaj,
        "po_dnevih": po_dnevih,
        "strani": strani,
        "endpointi": endpointi,
        "razrezi": razrezi,
        "preliv": db.get_meta(conn, "obisk_preliv"),
    }
