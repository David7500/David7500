"""Zasedenost po poročilih potnikov: kako polno je vozilo in ali je koga pustilo na postaji.

Zakaj: potnica na liniji Ljubljana–Maribor (21. 10. 2026) ob petkih pride na
postajo 20 min prej, ker je avtobus ob odhodu že poln. Strojnega vira o tem
ni: derp.si, NAP SIRI-VM, LPP in zemljevid SŽ zasedenosti ne nosijo (0 od
829, 802, 142 vozil), validacije IJPP hrani DUJPP in jih po dveh mesecih
zbriše, potnikov, ki jih avtobus pusti zunaj, pa ne zapiše nihče
(`docs/MERITVE.md`, „Zasedenost“). Zato poročajo potniki sami, z enim
dotikom v oknu vožnje.

Kaj se hrani: vožnja, postaja, stopnja in čas -- **brez identitete**. „En
glas na odhod na dan“ se drži samo v pomnilniku (`_glasovi`) nad naključnim
id-jem naprave, ki ga brskalnik hrani sam; v bazo ne gre, ker bi povezal
vsa poročila iste osebe, to pa je njena vsakdanja pot. Po IP in UA se glasovi
ne štejejo: aplikacija ima za vse UA „Kajros“, mobilna omrežja si delijo
naslove, in sopotnik na polnem avtobusu bi dobil „že oddano“. Naslov šteje
samo za strop `NA_URO`, kot pri `stik.py`.

Ključ odhoda je `(agency, train_no, headsign, start_s)`, ne `trip_id`:
medkrajevne vožnje ga ob menjavi obdobja voznega reda zamenjajo (86 % ostane
istih, ključ 99,6 %, MERITVE 21. 10. 2026). Postaja ni del ključa, ampak
lastnost poročila -- vožnja ima mediano 17 postankov in poročila istega
odhoda bi se razsula. Za povzetek („običajno“) se poročila na isti postaji
združijo čez odhode in prevoznike v isti smeri (`_ista_smer`), ker ima en
odhod premalo poročil.

Komentar ne gre skozi to pot, ampak skozi `POST /stik` v nabiralnik; javen je
šele, ko ga skrbnik objavi (`objavi`). Kdor objavlja uporabniško besedilo,
mora osebne podatke v njem najti pred objavo (SEU, Russmedia, C-492/23).
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import secrets
import sqlite3
import threading
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from . import config, pristanek, stats

TZ = ZoneInfo(config.TIMEZONE)

#: Davidove stopnje (21. 10. 2026). „polno“ = vsi sedeži zasedeni,
#: medkrajevni avtobusi stojišč nimajo; „vrsta zunaj“ = ljudje so ostali na
#: postaji. Indeks + 1 je vrednost v bazi.
STOPNJE = ("prazno", "pol polno", "skoraj polno", "polno", "vrsta zunaj")
#: Od te stopnje naprej je vozilo polno -- za „koliko prej priti“.
POLNO = 4
ZUNAJ = 5

#: Poročilo velja od ure pred voznoredno uro na postaji do treh ur po njej:
#: kdor čaka, vidi avtobus na peronu, kdor se pelje, poroča med vožnjo.
PRED_S = 3600
PO_S = 3 * 3600
#: Da so ljudje ostali zunaj, se zgodi ob odhodu, ne pol ure prej.
ZUNAJ_PRED_S = 600
#: Zgrešen dotik se da preklicati toliko časa.
PREKLIC_S = 600

NA_URO = 20
#: Strop čez vse naprave in naslove skupaj, da porazdeljen napad ne napolni
#: diska z bazo meritev vred (isti razlog kot `stik.VSEH_NA_DAN`).
VSEH_NA_DAN = 2000

#: „Običajno“: poročila zadnjih osmih tednov, odhodi ±90 min od tega.
TEDNOV = 8
PAS_S = 90 * 60
#: Pod tem povzetka ni, so samo poročila z datumi -- majhnega vzorca ne
#: skrijemo, a ga tudi ne napihnemo v „običajno“.
NAJMANJ = 5
#: „Poln je bil že N min pred odhodom“ šele iz toliko različnih dni.
PREJ_DNI = 3
NAJVEC_ZGODOVINE = 5
NAJVEC_OPOMB = 5
#: Komentar o vrsti na peronu po pol leta ne velja več (vozni red, šola).
OPOMBE_DNI = 183
#: Poročila 13 mesecev: da se vidi lanski isti mesec.
HRAMBA_DNI = 400
#: „Te prejšnji ni vzel?“: odhod, ki je po voznem redu odpeljal v zadnjih 30 min.
PREJSNJI_ODPELJAL_S = 30 * 60
#: Danes poln prejšnji odhod se pokaže, dokler je od njega minilo največ 2 h.
PREJSNJI_S = 2 * 3600

OPOMBA_NAJKRAJSE = 3
OPOMBA_NAJDALJSE = 280

DNEVI = ("ob ponedeljkih", "ob torkih", "ob sredah", "ob četrtkih", "ob petkih",
         "ob sobotah", "ob nedeljah")
DNEVI_KRATKO = ("pon", "tor", "sre", "čet", "pet", "sob", "ned")
#: Ponedeljek je svoj tip: vozni red LJ AP ↔ MB AP ima ob ponedeljkih tri
#: ojačitve več kot od torka do četrtka, ki so med sabo enaki (21. 10. 2026).
TIPI = {"pon": "ob ponedeljkih", "tor-cet": "od torka do četrtka", "pet": "ob petkih",
        "sob": "ob sobotah", "ned": "ob nedeljah in praznikih"}

SHEMA = """
-- Poročila potnikov o zasedenosti. Brez identitete: glej `zasedenost.py`.
CREATE TABLE IF NOT EXISTS zasedenost (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    prejeto     INTEGER NOT NULL,   -- epoha; ob prehodu na „polno“ se premakne
    spremenjeno INTEGER NOT NULL,
    datum       TEXT    NOT NULL,   -- obratovalni dan
    omrezje     TEXT    NOT NULL,
    agency      TEXT    NOT NULL,
    train_no    TEXT    NOT NULL,
    headsign    TEXT    NOT NULL,
    start_s     INTEGER NOT NULL,
    trip_id     TEXT    NOT NULL,   -- samo za povezavo; ključ odhoda ni
    postaja     TEXT    NOT NULL,
    t_s         INTEGER NOT NULL,   -- voznoredna ura na tej postaji
    naprej      TEXT    NOT NULL,   -- JSON: postaje za `postaja`, za smer
    stopnja     INTEGER NOT NULL CHECK (stopnja BETWEEN 1 AND 5),
    skrito      INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_zasedenost_postaja ON zasedenost(postaja, datum);
CREATE INDEX IF NOT EXISTS ix_zasedenost_odhod ON zasedenost(train_no, start_s, datum);
CREATE INDEX IF NOT EXISTS ix_zasedenost_prejeto ON zasedenost(prejeto);
-- Objavljeni komentarji. Izvirnik ostane v `sporocilo` (nabiralnik).
CREATE TABLE IF NOT EXISTS opomba (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sporocilo   INTEGER NOT NULL UNIQUE,
    objavljeno  INTEGER NOT NULL,
    datum       TEXT    NOT NULL,
    agency      TEXT    NOT NULL,
    train_no    TEXT    NOT NULL,
    headsign    TEXT    NOT NULL,
    start_s     INTEGER NOT NULL,
    postaja     TEXT    NOT NULL,
    t_s         INTEGER NOT NULL,
    naprej      TEXT    NOT NULL,
    besedilo    TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_opomba_postaja ON opomba(postaja);
"""

_NAPRAVA = re.compile(r"[0-9a-f]{16,64}")
_DATUM = re.compile(r"\d{4}-\d{2}-\d{2}")
#: Komentar brez povezav, e-naslovov in telefonskih številk: prvo je oglas,
#: drugo in tretje osebni podatek, ki ga pred objavo ne bi smeli spregledati.
_PREPOVEDANO = re.compile(
    r"https?://|www\.|\b[\w.+-]+@[\w-]+\.\w|(?:\d[\s/-]?){9,}", re.IGNORECASE)

_zaklep = threading.Lock()
#: Od preverbe pogostosti do zapisa je eno dejanje, kot v `stik.sprejmi`.
_sprejem = threading.Lock()
#: `naslov -> [časi]`, samo v pomnilniku.
_poslana: dict[str, list[float]] = {}
#: `glas -> (id vrstice, čas prvega poročila)`. Glas je zgoščen s soljo
#: dneva, ki se ob prehodu dneva zavrže skupaj s slovarjem.
_glasovi: dict[str, tuple[int, float]] = {}
_sol: dict[str, object] = {"dan": None, "bajti": b""}


class Zavrnjeno(Exception):
    """Poročila nismo sprejeli. Besedilo je namenjeno potniku."""

    def __init__(self, sporocilo: str, koda: str = "drugo", status: int = 400):
        super().__init__(sporocilo)
        self.koda = koda
        self.status = status


def init(conn: sqlite3.Connection) -> None:
    conn.executescript(SHEMA)
    conn.commit()


# ------------------------------------------------------------- tip dneva

def _velika_noc(leto: int) -> date:
    """Velikonočna nedelja (gregorijanski koledar, Meeus/Jones/Butcher)."""
    a, b, c = leto % 19, leto // 100, leto % 100
    d, e = b // 4, b % 4
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 19 * l_) // 433
    mesec = (h + l_ - 7 * m + 90) // 25
    return date(leto, mesec, (h + l_ - 7 * m + 33 * mesec + 19) % 32)


#: Dela prosti dnevi (Zakon o praznikih in dela prostih dnevih). Binkošti in
#: velikonočna nedelja so nedelje že same.
_PRAZNIKI = {(1, 1), (1, 2), (2, 8), (4, 27), (5, 1), (5, 2), (6, 25), (8, 15),
             (10, 31), (11, 1), (12, 25), (12, 26)}


def praznik(d: date) -> bool:
    return (d.month, d.day) in _PRAZNIKI or d == _velika_noc(d.year) + timedelta(days=1)


def tip_dneva(datum: str) -> str:
    """Kateri dnevi se povprečijo skupaj. Praznik vozi kot nedelja: vozni red
    25. 12. 2026 (petek) ima 1 074 medkrajevnih voženj, navaden petek 8 744."""
    d = date.fromisoformat(datum)
    if d.weekday() == 6 or praznik(d):
        return "ned"
    return ("pon", "tor-cet", "tor-cet", "tor-cet", "pet", "sob")[d.weekday()]


# ------------------------------------------------------------------ vožnja

def _ura(t_s: int) -> str:
    t = int(t_s) % 86400
    return f"{t // 3600:02d}:{t % 3600 // 60:02d}"


def _ura_epohe(ts: float) -> str:
    return datetime.fromtimestamp(ts, TZ).strftime("%H:%M")


class Voznja:
    """Vožnja, kot jo rabi poročilo: ključ odhoda in postanki z urami."""

    def __init__(self, vrstica: sqlite3.Row, postanki: list[tuple[str, int]]):
        self.trip_id = vrstica["trip_id"]
        self.train_no = vrstica["train_no"]
        self.agency = vrstica["agency"] or ""
        self.network = vrstica["network"]
        self.headsign = vrstica["headsign"] or ""
        self.start_s = vrstica["start_s"]
        self.postanki = postanki

    @property
    def kljuc(self) -> tuple:
        return (self.agency, self.train_no, self.headsign, self.start_s)

    def na(self, postaja: str | None) -> tuple[str, int, list[str]]:
        """Postaja, ura na njej in postaje za njo. Brez postaje prva.

        Pri zanki (ista postaja dvakrat) velja prvi obisk.
        """
        for i, (ime, t_s) in enumerate(self.postanki[:-1]):
            if postaja is None or ime == postaja:
                return ime, t_s, [p for p, _ in self.postanki[i + 1:]]
        raise Zavrnjeno("Ta vožnja na tej postaji ne ustavi.", "postaja")


def voznja(conn: sqlite3.Connection, trip_id: str, datum: str) -> Voznja:
    v = conn.execute(
        "SELECT t.trip_id, t.train_no, t.agency, t.network, t.headsign, t.start_s,"
        "       EXISTS(SELECT 1 FROM service_day d"
        "               WHERE d.service_id = t.service_id AND d.date = ?) AS vozi"
        "  FROM trip t WHERE t.trip_id = ?", (datum, trip_id)).fetchone()
    if not v or v["start_s"] is None:
        raise Zavrnjeno("Te vožnje ne poznam.", "voznja", 404)
    if not v["vozi"]:
        raise Zavrnjeno("Ta vožnja ta dan ne vozi.", "ne_vozi")
    # Mestni LPP gneče na postaji nima (David, 21. 10. 2026), ima pa sto
    # voženj na linijo -- poročila bi bila šum.
    if v["agency"] == "lpp":
        raise Zavrnjeno("Za mestne avtobuse LPP zasedenosti ne zbiramo.", "lpp")
    postanki = [(r["name"], int(r["t_s"])) for r in conn.execute(
        "SELECT st.name, COALESCE(s.dep_s, s.arr_s) AS t_s FROM sched s"
        "  JOIN station st ON st.stop_id = s.stop_id"
        " WHERE s.trip_id = ? ORDER BY s.stop_seq", (trip_id,))]
    if len(postanki) < 2:
        raise Zavrnjeno("Te vožnje ne poznam.", "voznja", 404)
    return Voznja(v, postanki)


def _ista_smer(nasa: list[str], njihova: list[str]) -> bool:
    """Ali odhoda z iste postaje peljeta v isto smer.

    Po cilju, ne po naslednji postaji: A2527 iz Ljubljana AP pelje naravnost
    v Maribor, M2123 prek Stadiona v Mursko Soboto, a za potnika v Maribor sta
    isti odhod. Skupne prve postaje ne zadoščajo -- mimo Stadiona pelje tudi
    avtobus v Kamnik.
    """
    return bool(nasa and njihova) and (nasa[-1] in njihova or njihova[-1] in nasa)


# ------------------------------------------------------------------ sprejem

def _niz(v, najvec: int) -> str:
    if not isinstance(v, str) or not v.strip() or len(v) > najvec:
        raise Zavrnjeno("Osveži stran in poskusi znova.", "polje")
    return v.strip()


def _datum(v) -> str:
    if not isinstance(v, str) or not _DATUM.fullmatch(v):
        raise Zavrnjeno("Osveži stran in poskusi znova.", "polje")
    try:
        date.fromisoformat(v)
    except ValueError:
        raise Zavrnjeno("Osveži stran in poskusi znova.", "polje") from None
    return v


def _kljuc_glasu(naprava: str, v: Voznja, datum: str, zdaj: float) -> str:
    dan = datetime.fromtimestamp(zdaj, TZ).date().isoformat()
    with _zaklep:
        if _sol["dan"] != dan:
            _sol.update(dan=dan, bajti=secrets.token_bytes(16))
            _glasovi.clear()
        sol = _sol["bajti"]
    besedilo = "\0".join([naprava, *map(str, v.kljuc), datum])
    return hashlib.blake2s(besedilo.encode(), key=sol, digest_size=16).hexdigest()


def _preveri_pogostost(kljuc: str, zdaj: float) -> None:
    with _zaklep:
        casi = [c for c in _poslana.get(kljuc, []) if zdaj - c < 3600]
        if len(casi) >= NA_URO:
            raise Zavrnjeno("Preveč poročil v kratkem času. Poskusi čez kakšno uro.",
                            "pogostost", 429)
        _poslana[kljuc] = casi + [zdaj]
        if len(_poslana) > 5000:
            for k in [k for k, v in _poslana.items() if not v or zdaj - max(v) > 3600]:
                _poslana.pop(k, None)


def _zacetek_dneva(zdaj: float) -> int:
    d = datetime.fromtimestamp(zdaj, TZ)
    return int(d.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())


def sprejmi(conn: sqlite3.Connection, podatki: dict, kljuc: str,
            zdaj: float | None = None) -> dict:
    """Preveri in zapiše poročilo, ali ga prekliče (`preklic`). Vrne, kaj je zapisano.

    `{trip_id, service_date, postaja, stopnja, naprava}`. Ista naprava na
    istem odhodu isti dan stopnjo popravi, ne doda nove vrstice: kdor je ob
    16:08 javil „polno“, ob 16:20 pa ostal zunaj, je en potnik.
    """
    t = zdaj if zdaj is not None else time.time()
    naprava = podatki.get("naprava")
    if not isinstance(naprava, str) or not _NAPRAVA.fullmatch(naprava):
        raise Zavrnjeno("Osveži stran in poskusi znova.", "naprava")
    datum = _datum(podatki.get("service_date"))
    v = voznja(conn, _niz(podatki.get("trip_id"), 80), datum)
    postaja, t_s, naprej = v.na(_niz(podatki.get("postaja"), 120))
    glas = _kljuc_glasu(naprava, v, datum, t)

    if podatki.get("preklic") is True:
        with _sprejem:
            prej = _glasovi.get(glas)
            if not prej or t - prej[1] > PREKLIC_S:
                raise Zavrnjeno("Poročila ni več mogoče preklicati.", "preklic")
            conn.execute("DELETE FROM zasedenost WHERE id = ?", (prej[0],))
            conn.commit()
            _glasovi.pop(glas, None)
        return {"preklicano": True}

    stopnja = podatki.get("stopnja")
    # `True` je v Pythonu tudi 1; „prazno“ mora biti številka.
    if type(stopnja) is not int or not 1 <= stopnja <= len(STOPNJE):
        raise Zavrnjeno("Izberi, kako polno je.", "stopnja")
    odhod = stats.polnoc(datum) + t_s
    if not odhod - PRED_S <= t <= odhod + PO_S:
        raise Zavrnjeno("Javiš lahko od ure pred odhodom do treh ur po njem.", "cas")
    if stopnja == ZUNAJ and t < odhod - ZUNAJ_PRED_S:
        raise Zavrnjeno("Da so ljudje ostali zunaj, se javi ob odhodu.", "prezgodaj")

    with _sprejem:
        _preveri_pogostost(kljuc, t)
        prej = _glasovi.get(glas)
        staro = (conn.execute("SELECT stopnja FROM zasedenost WHERE id = ?",
                              (prej[0],)).fetchone() if prej else None)
        if staro:
            id_ = prej[0]
            # `prejeto` je čas, ko je potnik vozilo prvič videl polno: iz njega
            # je „poln je bil že N min pred odhodom“.
            conn.execute(
                "UPDATE zasedenost SET stopnja = ?, spremenjeno = ?, postaja = ?, t_s = ?,"
                "       naprej = ?, prejeto = CASE WHEN ? >= ? AND stopnja < ? THEN ?"
                "                                  ELSE prejeto END"
                " WHERE id = ?",
                (stopnja, int(t), postaja, t_s, json.dumps(naprej, ensure_ascii=False),
                 stopnja, POLNO, POLNO, int(t), id_))
        else:
            (n,) = conn.execute("SELECT COUNT(*) FROM zasedenost WHERE prejeto >= ?",
                                (_zacetek_dneva(t),)).fetchone()
            if n >= VSEH_NA_DAN:
                raise Zavrnjeno("Danes poročil ne sprejemamo več. Poskusi jutri.",
                                "strop", 429)
            id_ = int(conn.execute(
                "INSERT INTO zasedenost(prejeto, spremenjeno, datum, omrezje, agency,"
                " train_no, headsign, start_s, trip_id, postaja, t_s, naprej, stopnja)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (int(t), int(t), datum, v.network, v.agency, v.train_no, v.headsign,
                 v.start_s, v.trip_id, postaja, t_s, json.dumps(naprej, ensure_ascii=False),
                 stopnja)).lastrowid)
        conn.commit()
        _glasovi[glas] = (id_, prej[1] if staro else t)
    return {"id": id_, "stopnja": stopnja, "postaja": postaja, "ura": _ura_epohe(t)}


# ------------------------------------------------------------------ pregled

def _dan(datum: str) -> str:
    return DNEVI_KRATKO[date.fromisoformat(datum).weekday()]


def _obicajno(vrstice: list[dict], datum: str, t_s: int) -> dict | None:
    """Povzetek po istem dnevu v tednu, sicer po tipu dneva -- z vzorcem."""
    d = date.fromisoformat(datum)
    tip = tip_dneva(datum)
    istega = [r for r in vrstice if tip_dneva(r["datum"]) == tip
              and date.fromisoformat(r["datum"]).weekday() == d.weekday()]
    if len(istega) >= NAJMANJ:
        izbor, kdaj = istega, DNEVI[d.weekday()]
    else:
        izbor = [r for r in vrstice if tip_dneva(r["datum"]) == tip]
        kdaj = TIPI[tip]
    if len(izbor) < NAJMANJ:
        return None
    stopnje = [0] * len(STOPNJE)
    for r in izbor:
        stopnje[r["stopnja"] - 1] += 1
    urejene = sorted(r["stopnja"] for r in izbor)
    datumi = sorted({r["datum"] for r in izbor})
    # Najzgodnejše „polno“ pred odhodom, po dnevu in odhodu. Poročilo pove,
    # kdaj je potnik videl polno, ne kdaj se je napolnilo -- zato „vsaj“.
    prvo: dict[tuple, float] = {}
    for r in izbor:
        odhod = stats.polnoc(r["datum"]) + r["t_s"]
        if r["stopnja"] >= POLNO and r["prejeto"] < odhod:
            k = (r["datum"], r["agency"], r["train_no"], r["headsign"], r["start_s"])
            prvo[k] = max(prvo.get(k, 0), odhod - r["prejeto"])
    prej = None
    po_dnevih: dict[str, float] = {}
    for (dan, *_), s in prvo.items():
        po_dnevih[dan] = max(po_dnevih.get(dan, 0), s)
    if len(po_dnevih) >= PREJ_DNI:
        mini = round(min(po_dnevih.values()) / 60)
        maksi = round(max(po_dnevih.values()) / 60)
        prej = {"dni": len(po_dnevih), "od_min": mini, "do_min": maksi,
                "nasvet_min": max(5, math.ceil(maksi / 5) * 5)}
    return {"kdaj": kdaj, "od": _ura(t_s - PAS_S), "do": _ura(t_s + PAS_S),
            "porocil": len(izbor), "dni": len(datumi), "prvi": datumi[0],
            "zadnji": datumi[-1], "stopnje": stopnje,
            "mediana": urejene[(len(urejene) - 1) // 2], "prej": prej}


def _te_ni_vzel(conn: sqlite3.Connection, v: Voznja, datum: str, postaja: str,
                t_s: int, naprej: list[str], zdaj_s: int) -> dict | None:
    """Prejšnji odhod v isto smer, ki je po voznem redu pravkar odpeljal.

    Kdor je ostal zunaj, gleda naslednji odhod, ne tistega, ki ga ni vzel --
    tabla ga kaže le še 10 min (`api.py`). Zato ga ponudimo tu.
    """
    od, do = max(zdaj_s - PREJSNJI_ODPELJAL_S, t_s - PREJSNJI_S), min(zdaj_s, t_s - 1)
    if od > do:
        return None
    vrstice = conn.execute(
        "SELECT t.trip_id, t.train_no, t.agency, t.network, t.headsign,"
        "       COALESCE(s.dep_s, s.arr_s) AS t_s, b.stop_seq, sb.name AS naprej"
        "  FROM service_day d JOIN trip t ON t.service_id = d.service_id"
        "  JOIN sched s ON s.trip_id = t.trip_id"
        "  JOIN station st ON st.stop_id = s.stop_id"
        "  JOIN sched b ON b.trip_id = t.trip_id AND b.stop_seq > s.stop_seq"
        "  JOIN station sb ON sb.stop_id = b.stop_id"
        " WHERE d.date = ? AND t.network = ? AND st.name = ? AND t.trip_id != ?"
        "   AND t.agency != 'lpp' AND COALESCE(s.dep_s, s.arr_s) BETWEEN ? AND ?"
        " ORDER BY t_s DESC, t.trip_id, b.stop_seq",
        (datum, v.network, postaja, v.trip_id, od, do)).fetchall()
    voznje: dict[str, dict] = {}
    for r in vrstice:
        x = voznje.setdefault(r["trip_id"], {**dict(r), "postaje": []})
        x["postaje"].append(r["naprej"])
    for x in voznje.values():                 # najnovejši odhod prvi
        if _ista_smer(naprej, x["postaje"]):
            return {"trip_id": x["trip_id"], "ura": _ura(x["t_s"]),
                    "oznaka": pristanek.ime_voznje(x)}
    return None


def pregled(conn: sqlite3.Connection, trip_id: str, datum: str,
            postaja: str | None = None, zdaj: float | None = None) -> dict:
    """Vse, kar okno vožnje pokaže o zasedenosti ene vožnje na eni postaji.

    Majhna tabela, omejena na osem tednov in eno postajo prek indeksa, zato
    teče v zahtevi; povzetek nosi razpon datumov, iz katerih je.
    """
    t = zdaj if zdaj is not None else time.time()
    v = voznja(conn, trip_id, datum)
    try:
        postaja, t_s, naprej = v.na(postaja)
    except Zavrnjeno:
        postaja, t_s, naprej = v.na(None)
    k = v.kljuc
    d = date.fromisoformat(datum)
    danes = [{"ura": _ura_epohe(r["spremenjeno"]), "postaja": r["postaja"],
              "stopnja": r["stopnja"]} for r in conn.execute(
        "SELECT spremenjeno, postaja, stopnja FROM zasedenost"
        " WHERE train_no = ? AND start_s = ? AND datum = ? AND agency = ? AND headsign = ?"
        "   AND skrito = 0 ORDER BY spremenjeno DESC LIMIT 5",
        (v.train_no, v.start_s, datum, v.agency, v.headsign))]

    od = (d - timedelta(weeks=TEDNOV)).isoformat()
    zgodovina = [{"datum": r["datum"], "dan": _dan(r["datum"]), "postaja": r["postaja"],
                  "stopnja": r["stopnja"], "porocil": r["n"]} for r in conn.execute(
        "SELECT datum, postaja, MAX(stopnja) AS stopnja, COUNT(*) AS n FROM zasedenost"
        " WHERE train_no = ? AND start_s = ? AND datum >= ? AND datum < ?"
        "   AND agency = ? AND headsign = ? AND skrito = 0"
        " GROUP BY datum, postaja ORDER BY datum DESC LIMIT ?",
        (v.train_no, v.start_s, od, datum, v.agency, v.headsign, NAJVEC_ZGODOVINE))]

    vrstice = [dict(r) for r in conn.execute(
        "SELECT datum, agency, train_no, headsign, start_s, t_s, naprej, stopnja, prejeto"
        "  FROM zasedenost WHERE postaja = ? AND datum >= ? AND datum <= ?"
        "   AND skrito = 0 AND t_s BETWEEN ? AND ?",
        (postaja, od, datum, t_s - PAS_S, t_s + PAS_S))]
    for r in vrstice:
        r["postaje"] = json.loads(r["naprej"])
    v_smer = [r for r in vrstice if _ista_smer(naprej, r["postaje"])]
    obicajno = _obicajno([r for r in v_smer if r["datum"] < datum], datum, t_s)

    # Danes poln prejšnji odhod v isto smer: kdor čaka na ta odhod, mora to vedeti.
    prejsnji = None
    for r in sorted((r for r in v_smer if r["datum"] == datum and r["t_s"] < t_s
                     and r["t_s"] >= t_s - PREJSNJI_S and r["stopnja"] >= POLNO
                     and (r["agency"], r["train_no"], r["headsign"], r["start_s"]) != k),
                    key=lambda r: (r["t_s"], r["stopnja"]), reverse=True):
        prejsnji = {"ura": _ura(r["t_s"]), "stopnja": r["stopnja"],
                    "oznaka": pristanek.ime_voznje({**r, "network": v.network}),
                    "javljeno": _ura_epohe(r["prejeto"])}
        break

    te_ni_vzel = None
    zdaj_s = int(t) - stats.polnoc(datum)
    # Samo dokler ta odhod še ni odpeljal: potem je to vprašanje za naslednjega.
    if t_s - PREJSNJI_S <= zdaj_s <= t_s:
        te_ni_vzel = _te_ni_vzel(conn, v, datum, postaja, t_s, naprej, zdaj_s)

    opombe = []
    for r in conn.execute(
            "SELECT id, datum, postaja, t_s, naprej, besedilo, agency, train_no,"
            "       headsign, start_s FROM opomba"
            " WHERE objavljeno >= ? AND (postaja = ? OR (train_no = ? AND start_s = ?))"
            " ORDER BY datum DESC, id DESC LIMIT 100",
            (int(t) - OPOMBE_DNI * 86400, postaja, v.train_no, v.start_s)):
        isti_odhod = (r["agency"], r["train_no"], r["headsign"], r["start_s"]) == k
        if isti_odhod or (r["postaja"] == postaja and abs(r["t_s"] - t_s) <= PAS_S
                          and _ista_smer(naprej, json.loads(r["naprej"]))):
            opombe.append({"id": r["id"], "datum": r["datum"], "dan": _dan(r["datum"]),
                           "postaja": r["postaja"], "besedilo": r["besedilo"]})
        if len(opombe) >= NAJVEC_OPOMB:
            break

    return {"vklopljeno": True, "postaja": postaja, "odhod": _ura(t_s),
            "odhod_ts": stats.polnoc(datum) + t_s, "okno": [PRED_S, PO_S, ZUNAJ_PRED_S],
            "postaje": [{"ime": p, "ura": _ura(s)} for p, s in v.postanki[:-1]],
            "stopnje": STOPNJE, "danes": danes, "prejsnji": prejsnji,
            "te_ni_vzel": te_ni_vzel, "obicajno": obicajno, "zgodovina": zgodovina,
            "opombe": opombe, "izracunano": int(t)}


# ------------------------------------------------------------------ komentarji

def preveri_opombo(conn: sqlite3.Connection, trip_id: str, datum: str, postaja: str,
                   besedilo: str, zdaj: float | None = None) -> tuple[str, str]:
    """Pospravi komentar in sestavi, h kateri vožnji sodi. Vrne (besedilo, JSON).

    Komentar gre v nabiralnik (`stik.sprejmi`), z vožnjo v stolpcu `opomba`,
    da ga skrbnik vidi v kontekstu in ga lahko objavi (`objavi`).
    """
    t = zdaj if zdaj is not None else time.time()
    besedilo = " ".join((besedilo or "").split())
    if len(besedilo) < OPOMBA_NAJKRAJSE:
        raise Zavrnjeno("Opomba je prekratka.", "kratko")
    if len(besedilo) > OPOMBA_NAJDALJSE:
        raise Zavrnjeno(f"Opomba je predolga (največ {OPOMBA_NAJDALJSE} znakov).", "dolgo")
    if _PREPOVEDANO.search(besedilo):
        raise Zavrnjeno("V opombi ne sme biti povezav, e-naslovov ali telefonskih številk.",
                        "vsebina")
    datum = _datum(datum)
    # Komentar pride tudi zvečer doma, a o današnji ali včerajšnji vožnji.
    danes = datetime.fromtimestamp(t, TZ).date()
    if date.fromisoformat(datum) not in (danes, danes - timedelta(days=1)):
        raise Zavrnjeno("Opombo lahko dodaš samo k današnji ali včerajšnji vožnji.", "cas")
    v = voznja(conn, _niz(trip_id, 80), datum)
    postaja, t_s, naprej = v.na(_niz(postaja, 120))
    kontekst = {"trip_id": v.trip_id, "datum": datum, "postaja": postaja, "t_s": t_s,
                "agency": v.agency, "train_no": v.train_no, "headsign": v.headsign,
                "start_s": v.start_s, "naprej": naprej, "network": v.network,
                "oznaka": f"{pristanek.ime_voznje(vars(v))} · {_ura(t_s)} · {postaja}"}
    return besedilo, json.dumps(kontekst, ensure_ascii=False)


def objavi(conn: sqlite3.Connection, sporocilo_id: int, zdaj: float | None = None) -> bool:
    """Komentar iz nabiralnika postane javen. Vrne, ali je bil komentar."""
    r = conn.execute("SELECT besedilo, opomba FROM sporocilo WHERE id = ?",
                     (sporocilo_id,)).fetchone()
    if not r or not r["opomba"]:
        return False
    o = json.loads(r["opomba"])
    conn.execute(
        "INSERT OR REPLACE INTO opomba(sporocilo, objavljeno, datum, agency, train_no,"
        " headsign, start_s, postaja, t_s, naprej, besedilo) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (sporocilo_id, int(zdaj if zdaj is not None else time.time()), o["datum"],
         o["agency"], o["train_no"], o["headsign"], o["start_s"], o["postaja"], o["t_s"],
         json.dumps(o["naprej"], ensure_ascii=False), r["besedilo"]))
    conn.commit()
    return True


def umakni(conn: sqlite3.Connection, sporocilo_id: int) -> bool:
    n = conn.execute("DELETE FROM opomba WHERE sporocilo = ?", (sporocilo_id,)).rowcount
    conn.commit()
    return n > 0


def oznaci_objavljene(conn: sqlite3.Connection, sporocila: list[dict]) -> list[dict]:
    """Nabiralniku pove, kateri komentarji so javni (gumb „objavi“ / „umakni“)."""
    objavljeni = {r[0] for r in conn.execute("SELECT sporocilo FROM opomba")}
    for s in sporocila:
        if s.get("opomba"):
            s["opomba"] = json.loads(s["opomba"])
            s["objavljeno"] = s["id"] in objavljeni
    return sporocila


# ------------------------------------------------------------------ vzdrževanje

def pocisti(conn: sqlite3.Connection, zdaj: float | None = None) -> int:
    """Poročila in komentarji, starejši od `HRAMBA_DNI`, gredo ven."""
    t = zdaj if zdaj is not None else time.time()
    meja = datetime.fromtimestamp(t - HRAMBA_DNI * 86400, TZ).date().isoformat()
    n = conn.execute("DELETE FROM zasedenost WHERE datum < ?", (meja,)).rowcount
    n += conn.execute("DELETE FROM opomba WHERE datum < ?", (meja,)).rowcount
    conn.commit()
    return n
