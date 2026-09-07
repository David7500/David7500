"""Kar potnik dejansko vpraša: kdaj mi pelje, od kod, s katerim prestopom.

Ločeno od `stats.py`, ki odgovarja na analitična vprašanja o preteklosti.
Tu je vse vezano na en dan in en trenutek.

Trije odgovori:

* **odhodi s postaje** -- najpogostejše vprašanje sploh in doslej edino, na
  katero API ni znal odgovoriti: `connections` je zahteval izhodišče IN cilj.
* **iskanje postaje** -- brez šumnikov in z delnim ujemanjem, ker nihče ne
  tipka "Šentjur pri Celju" v celoti.
* **povezave s prestopom** -- brez njih iskalnik odpove na velikem delu
  Slovenije: Koper--Maribor ni neposredne vožnje, Novo mesto--Celje tudi ne.
"""
from __future__ import annotations

import math
import sqlite3
import unicodedata
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from . import config, geo
from .stats import (NOCNI_REP_S, _abs_time, _after_slack, estimate_at, _operator_is_stale, _slack_ahead,
                    _with_operator, dwell_at, last_measured, opis_zamude,
                    typical_at_stops)

TZ = ZoneInfo(config.TIMEZONE)

# Koliko minut mora potnik imeti za prestop, da povezavo sploh ponudimo, in
# koliko čakanja še šteje za eno potovanje. Pragova sta odvisna od omrežja:
#
# * Železnica: SŽ jamči zvezo pri 5 minutah na istem peronu, a to velja le za
#   načrtovane zveze; za tujo kombinacijo je 5 minut lovljenje vlaka. Čakanje
#   do dveh ur je pri vlaku, ki vozi vsake tri ure, še vedno potovanje.
# * Mestni avtobus: postajališča so blizu, tri minute so dovolj. Čakanje pol
#   ure pa ni prestop -- na liniji, ki vozi vsakih deset minut, bi tak predlog
#   pomenil, da smo zamudili tri boljše.
TRANSFER_LIMITS = {
    "zeleznica": (6, 120),
    "avtobus": (3, 30),
}
MIN_TRANSFER_MIN, MAX_TRANSFER_MIN = TRANSFER_LIMITS["zeleznica"]

# Koliko zadetkov po imenu sploh pretehtamo po prometu. Glej `search_stations`.
CANDIDATE_CAP = 300

#: Kolikokrat manj prometen sme biti TOCNI zadetek od najboljsega, preden
#: izgubi prvo mesto. Izmerjeno na avtobusnem omrezju: pri 20 pade 12 iskanj
#: (vsa prava napaka), pri 10 jih je 32 in med njimi pari, ki so isti kraj.
TOCNO_NAJMANJ_DELEZ = 20


# ---------------------------------------------------------------- iskanje postaj

def _fold(s: str) -> str:
    """Male črke brez šumnikov: 'Šentjur' -> 'sentjur'.

    NFKD razstavi č na c + strešico, `combining` jo vrže stran. Brez tega
    iskanje "sentjur" ne najde ničesar, kar je za tipkanje na telefonu ubijalsko.
    """
    return "".join(
        c for c in unicodedata.normalize("NFKD", s.lower())
        if not unicodedata.combining(c)
    )


def station_index(conn: sqlite3.Connection, network: str) -> list[dict]:
    """Vsa imena postaj omrezja, ze urejena po prometu.

    Za iskalnik v brskalniku. `search_stations()` razvrsca po
    `(razred ujemanja, -promet, ime)`; razred je odvisen od poizvedbe, promet
    in ime nista. Ce odjemalec dobi seznam, ze urejen po `(-promet, ime)`, in
    ga stabilno razvrsti samo po razredu, dobi **isti vrstni red** kot bi ga
    dobil od streznika -- brez zahteve na vsak pritisk tipke.

    Imena so zdruzena kot v `search_stations()`: mestno postajalisce ima svoj
    `stop_id` za vsako smer, aplikacija pa vse gradi po imenu.
    """
    rows = conn.execute(
        "SELECT st.name AS n, COUNT(*) AS t"
        "  FROM sched s"
        "  JOIN trip tr ON tr.trip_id = s.trip_id"
        "  JOIN station st ON st.stop_id = s.stop_id"
        " WHERE tr.network = ?"
        " GROUP BY st.name"
        " ORDER BY t DESC, n",
        (network,)).fetchall()
    return [{"n": r["n"], "t": r["t"]} for r in rows]


# Promet po postajaliscu, predpomnjen do naslednjega uvoza GTFS.
#
# Prej se je stel ob VSAKEM pritisku tipke: za do `CANDIDATE_CAP` kandidatov
# poizvedba cez `sched JOIN trip`. Dokler je bilo `sched` 403 000 vrstic, je
# bilo to znosno; z mestnim LPP jih je 890 000 in na arwenu je iskanje trajalo
# **3,5-3,9 s na crko**. Vsebina se spremeni enkrat na dan, zato je to stetje
# tam, kjer sodi -- enkrat, ne stokrat na minuto.
_PROMET: dict[tuple, dict[str, int]] = {}
_PROMET_MAX = 4


def _promet(conn: sqlite3.Connection, network: str | None) -> dict[str, int]:
    """`{stop_id: stevilo postankov}` za dano omrezje."""
    stamp = conn.execute(
        "SELECT value FROM meta WHERE key = 'gtfs_imported_at'").fetchone()
    stamp = stamp["value"] if stamp else None
    where = conn.execute("PRAGMA database_list").fetchone()["file"]
    key = (where, network, stamp)
    if stamp and key in _PROMET:
        return _PROMET[key]

    sql = ("SELECT s.stop_id AS sid, COUNT(*) AS n FROM sched s "
           "JOIN trip t ON t.trip_id = s.trip_id ")
    par: tuple = ()
    if network:
        sql += "WHERE t.network = ? "
        par = (network,)
    sql += "GROUP BY s.stop_id"
    out = {r["sid"]: r["n"] for r in conn.execute(sql, par)}

    if stamp:
        if len(_PROMET) >= _PROMET_MAX:
            _PROMET.clear()
        _PROMET[key] = out
    return out


def search_stations(conn: sqlite3.Connection, q: str, limit: int = 12,
                    network: str | None = None) -> list[dict]:
    """Postaje, ki ustrezajo nizu. Urejene po tem, kako dobro se ujemajo.

    Rang: točno ime < začetek imena < začetek besede < kjerkoli. Znotraj
    istega ranga odloča promet -- "Ljubljana" mora biti pred "Ljubljana Vodmat",
    ker je stokrat pogostejši cilj, ne zato, ker je krajša.

    `network` omeji na postaje enega omrežja. Brez tega bi iskalnik vlakov
    ponujal mestna postajališča, iskalnik avtobusov pa železniške postaje --
    obakrat imena, na katerih tam ni mogoče nič najti.
    """
    needle = _fold(q.strip())
    if not needle:
        return []
    # Dva koraka namesto enega. Prej je poizvedba pri VSAKEM pritisku tipke
    # grupirala vseh 403 000 vrstic `sched`, da je izracunala promet postaj,
    # od katerih jih je nato v Pythonu obdrzala pescico. Zdaj najprej ujamemo
    # imena (9791 vrstic), promet pa stejemo samo za zadetke.
    rows = conn.execute("SELECT stop_id, name, lat, lon FROM station").fetchall()

    def rank_of(name: str) -> int:
        folded = _fold(name)
        if folded == needle:
            return 0
        if folded.startswith(needle):
            return 1
        if any(w.startswith(needle) for w in folded.split()):
            return 2
        return 3 if needle in folded else 9

    def _razred(rang: int) -> int:
        """Zacetek imena in zacetek besede sta za potnika ISTO dobra zadetka.

        Locevanje ju je razvrscalo pred prometom in to je bilo merljivo
        narobe: kdor je vtipkal "polje", je dobil "Polje (Tolmin)" z dvema
        voznjama pred "Kranj Zlato Polje P+R" s 314, "Novo Polje" pa je padlo
        na deveto mesto -- stran zahteva osem in ga zato ni bilo videti. Enako
        pri "most" (Most na Soci pred Zidanim Mostom) in "gora" (Gora pri
        Pecah pred Kranjsko Goro). Tocno ime ostane prvo, ostalo odloca promet.

        Za IZBOR kandidatov ostane locevanje smiselno -- glej `CANDIDATE_CAP`.
        """
        return 1 if rang == 2 else rang

    hits = [(rank_of(r["name"]), r["name"], r) for r in rows]
    hits = [h for h in hits if h[0] < 9]
    if not hits:
        return []
    # Ena sama crka se ujame s tisoci postajalisc in stetje prometa za vsa je
    # pol sekunde. Najprej razvrstimo po tem, KAKO se ujemajo -- to je zastonj --
    # in promet stejemo le za verjetne kandidate. Meja je velikodusna glede na
    # `limit`, ki je obicajno osem.
    hits.sort(key=lambda h: h[:2])
    hits = [h[2] for h in hits[:CANDIDATE_CAP]]

    counts = _promet(conn, network)

    # Isto ime, vec `stop_id`: mestna postajalisca imajo svojega za vsako smer
    # ("Bavarski dvor" dvakrat). Vse naprej v aplikaciji tece po IMENU postaje,
    # zato bi bila dvojnica v seznamu samo dva enaka gumba.
    #
    # Sesteti je treba PRED razvrscanjem, ne po njem. Prej se je razvrscalo po
    # postankih enega `stop_id`, izpisala pa se je vsota vseh smeri -- seznam je
    # bil torej urejen po drugi stevilki, kot jo je kazal.
    po_imenu: dict[str, dict] = {}
    for r in hits:
        trips = counts.get(r["stop_id"], 0)
        if not trips:
            continue        # na tem omrezju te postaje ne strezhe nic
        prej = po_imenu.get(r["name"])
        if prej is None:
            po_imenu[r["name"]] = {**dict(r), "trips": trips, "_naj": trips}
        elif trips > prej["_naj"]:
            # Lego in `stop_id` vzame najbolj prometna smer, promet pa je vsota.
            prej.update(stop_id=r["stop_id"], lat=r["lat"], lon=r["lon"],
                        trips=prej["trips"] + trips, _naj=trips)
        else:
            prej["trips"] += trips

    # **Tocno ime prvo -- razen kadar je nicevo.** Sumniki se pri iskanju
    # zlijejo, zato je "Celje" tudi "Čelje": vas z DVEMA postankoma v vsem
    # voznem redu je stala pred "Celje AP" s 1014. Isto pri "novo" ("Novo" 12
    # proti "Novo mesto" 631) in "krizan" ("Križan" 31 proti "Križanke" 4818).
    # Takih primerov je na avtobusnem omrezju 12, na zeleznickem nobenega.
    #
    # Prag je izmerjen, ne izbran: pri 20-kratniku pade teh 12, pri 10 pa jih
    # je 32 in med njimi so pari, ki so ISTI kraj -- "Boršt" in "Boršt/Krki K",
    # "Straža pri Raki" in "... K". Tam bi bila prestavitev napacna.
    naj_promet = max((d["trips"] for d in po_imenu.values()), default=0)

    def razred_z_prometom(d: dict) -> int:
        rang = rank_of(d["name"])
        if rang == 0 and d["trips"] * TOCNO_NAJMANJ_DELEZ < naj_promet:
            return 1
        return _razred(rang)

    out = sorted(po_imenu.values(),
                 key=lambda d: (razred_z_prometom(d), -d["trips"], d["name"]))
    # Prestavljeni tocni zadetek gre na DRUGO mesto, ne na konec. Prvo dobi
    # najbolj prometna postaja, ker jo isce vec ljudi; tocno tisto, kar je
    # clovek vtipkal, pa mora biti takoj pod njo in ne sme izginiti -- sumnika
    # ni mogoce vtipkati drugace, zato bi bila "Čelje" sicer nedosegljiva.
    vrnjeno = out[:limit]
    tocni = next((d for d in out if rank_of(d["name"]) == 0), None)
    if tocni is not None and limit > 1 and (not vrnjeno or vrnjeno[0] is not tocni):
        vrnjeno = [d for d in vrnjeno if d is not tocni]
        vrnjeno = vrnjeno[:1] + [tocni] + vrnjeno[1:limit - 1]
    for d in out:
        d.pop("_naj")
    return vrnjeno


def resolve_station(conn: sqlite3.Connection, name: str,
                    network: str | None = None) -> str | None:
    """Vpisano ime -> točno ime postaje v bazi, ali None.

    Iskalnik sme dobiti "murska" in vseeno najti povezavo; brez tega bi vsaka
    tipkarska nenatančnost dala prazen rezultat, kar je videti kot okvara.
    """
    if network:
        exact = conn.execute(
            "SELECT st.name FROM station st WHERE st.name = ? AND EXISTS ("
            "  SELECT 1 FROM sched s JOIN trip t ON t.trip_id = s.trip_id "
            "  WHERE s.stop_id = st.stop_id AND t.network = ?) LIMIT 1",
            (name, network),
        ).fetchone()
    else:
        exact = conn.execute("SELECT name FROM station WHERE name = ?", (name,)).fetchone()
    if exact:
        return exact["name"]
    hits = search_stations(conn, name, limit=1, network=network)
    return hits[0]["name"] if hits else None


def nearby_stations(conn: sqlite3.Connection, lat: float, lon: float,
                    network: str | None = None, limit: int = 8,
                    max_km: float = 3.0) -> list[dict]:
    """Postajališča blizu dane točke, urejena po zračni razdalji.

    Za mestni avtobus je to najpogostejši način, kako človek najde postajo:
    ne ve, kako se imenuje, ve pa, kje stoji. Pri vlakih je manj uporabno --
    postaj je 267 na vso državo -- a isti klic pokrije oboje.

    Razdalja je zračna, ne po poti. Za "katero postajališče je najbližje" to
    zadošča; za "koliko časa hodim" ne bi, zato tega tudi ne trdimo.

    Groba omejitev po pravokotniku pred haversinom: 1015 postajališč je malo,
    a poizvedba tece ob vsakem premiku in nima smisla racunati kosinusov za
    vso drzavo.
    """
    dlat = max_km / 111.0
    dlon = max_km / (111.0 * max(0.2, abs(math.cos(math.radians(lat)))))
    # Najprej pravokotnik in razdalja -- to je poceni. Sele za preziveli
    # pescici preverimo, ali jih to omrezje sploh strezhe; zdruzen JOIN cez
    # `sched` bi tekel po 403 000 vrsticah za odgovor, ki ima deset postavk.
    rows = conn.execute(
        "SELECT stop_id, name, lat, lon FROM station "
        "WHERE lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?",
        (lat - dlat, lat + dlat, lon - dlon, lon + dlon),
    ).fetchall()

    near = []
    for r in rows:
        m = geo.haversine(lat, lon, r["lat"], r["lon"])
        if m <= max_km * 1000:
            d = dict(r)
            d["meters"] = round(m)
            near.append(d)
    near.sort(key=lambda d: d["meters"])
    near = near[:200]
    if not near:
        return []

    served: set[str] = set()
    marks = ",".join("?" * len(near))
    sql = (f"SELECT DISTINCT s.stop_id FROM sched s "
           f"JOIN trip t ON t.trip_id = s.trip_id "
           f"WHERE s.stop_id IN ({marks}) ")
    params = [d["stop_id"] for d in near]
    if network:
        sql += "AND t.network = ? "
        params.append(network)
    served = {r["stop_id"] for r in conn.execute(sql, params)}
    out = [d for d in near if d["stop_id"] in served]

    # Isto ime na vec postajaliscih (smeri) -- obdrzi najblizje.
    seen: dict[str, dict] = {}
    for d in out:
        seen.setdefault(d["name"], d)
    return list(seen.values())[:limit]


# ---------------------------------------------------------------- odhodi

# `first_seq` in `last_seq` bereta iz `trip`, ne iz agregata cez `sched`.
# Prej je bilo tu `WITH ends AS (SELECT MIN/MAX(stop_seq) FROM sched GROUP BY
# trip_id)` -- polni pregled 403 208 vrstic ob VSAKI zahtevi, 117 ms od 120.
# Vozni red se med uvozi ne spreminja, zato je to statika in sodi v `trip`
# (napolni `db.fill_trip_window`).
_BOARD_SQL = """
SELECT t.trip_id, t.train_no, t.headsign, t.mode, t.agency, t.network,
       s.stop_seq, s.arr_s, s.dep_s,
       COALESCE(s.dep_s, s.arr_s) AS t_s,
       t.first_seq, t.last_seq,
       origin.name AS origin, dest.name AS destination,
       COALESCE(r.delay_dep, r.delay_arr) AS delay_s,
       COALESCE(rn.delay_arr, rn.delay_dep) AS next_delay_s,
       sn.stop_seq AS next_seq,
       zn.name AS next_stop,
       r.feed_ts
FROM sched s
JOIN station here ON here.stop_id = s.stop_id AND here.name = :station
JOIN trip t       ON t.trip_id = s.trip_id
JOIN sched so     ON so.trip_id = s.trip_id AND so.stop_seq = t.first_seq
JOIN station origin ON origin.stop_id = so.stop_id
JOIN sched sd     ON sd.trip_id = s.trip_id AND sd.stop_seq = t.last_seq
JOIN station dest ON dest.stop_id = sd.stop_id
JOIN service_day sday ON sday.service_id = t.service_id AND sday.date = :day
                     AND (:network IS NULL OR t.network = :network)
LEFT JOIN run r  ON r.trip_id = t.trip_id AND r.service_date = :day
                 AND r.stop_seq = s.stop_seq
-- Feed ni nikoli porocal stop_seq = 1: prva meritev pride sele na drugi
-- postaji. Za odhod z izhodisca je torej edini priblizek zamuda na naslednji
-- postaji -- vzamemo jo, prikaz pa mora povedati, da je od tam.
--
-- "Naslednja" je najmanjsi vecji stop_seq, ne stop_seq + 1. V tem feedu so
-- zaporedja sicer strnjena od 1, a GTFS tega ne zahteva in ob prvi vrzeli bi
-- se tabla tiho nehala sklicevati na pravo postajo.
LEFT JOIN sched sn ON sn.trip_id = t.trip_id
                  AND sn.stop_seq = (SELECT MIN(x.stop_seq) FROM sched x
                                     WHERE x.trip_id = t.trip_id
                                       AND x.stop_seq > s.stop_seq)
LEFT JOIN run rn   ON rn.trip_id = t.trip_id AND rn.service_date = :day
                  AND rn.stop_seq = sn.stop_seq
LEFT JOIN station zn ON zn.stop_id = sn.stop_id
WHERE COALESCE(s.dep_s, s.arr_s) BETWEEN :from_s AND :to_s
ORDER BY t_s
"""


def board(conn: sqlite3.Connection, station: str, service_date: str,
          from_s: int, window_min: int = 180, kind: str = "odhodi",
          limit: int = 150, network: str | None = None,
          now_s: int | None = None, _vceraj: bool = True) -> list[dict]:
    """Odhodna (ali prihodna) tabla postaje.

    `kind`: "odhodi" izpusti končno postajo vožnje (tam se nič ne odpelje),
    "prihodi" izpusti izhodiščno. Brez tega bi tabla vsakega vlaka štela
    dvakrat -- kot prihod in kot odhod na isti vrstici.

    `now_s` je trenutek, glede na katerega ločimo meritev od napovedi. Brez
    njega (drug dan) so vse vrednosti feeda enakovredne in tabla se opre na
    zgodovino.

    Zgodaj zjutraj vključi tudi **včerajšnji prometni dan**: vožnja, ki je
    odpeljala ob 23:50, ima postanke ob 24:21 in pripada včerajšnjemu dnevu.
    Brez tega je tabla ob 00:30 skrila vlak, ki pride ob 00:56 -- torej
    ravno takrat, ko je edini. `_vceraj` ustavi rekurzijo pri eni stopnji;
    dva dneva nazaj ni treba, ker se nobena vožnja ne razteza čez 48 ur.
    """
    rows = conn.execute(_BOARD_SQL, {
        "station": station, "day": service_date, "network": network,
        "from_s": from_s, "to_s": from_s + window_min * 60,
    }).fetchall()

    out = []
    for r in rows:
        d = dict(r)
        if kind == "odhodi" and d["stop_seq"] == d["last_seq"]:
            continue
        if kind == "prihodi" and d["stop_seq"] == d["first_seq"]:
            continue
        d["sched"] = _abs_time(service_date, d["t_s"])
        d["delay_from"] = None
        d["delay_kind"] = None
        # Za odhodno tablo je zanimiv cilj, za prihodno izhodisce.
        d["towards"] = d["destination"] if kind == "odhodi" else d["origin"]
        d["is_terminus"] = d["stop_seq"] == d["last_seq"]
        d["is_origin"] = d["stop_seq"] == d["first_seq"]
        for k in ("first_seq", "last_seq"):
            d.pop(k)
        out.append(d)
        if len(out) >= limit:
            break

    # Meja med meritvijo in napovedjo. Brez tega je tabla kazala feedovo
    # vrednost za se nedosezen postanek kot izmerjeno zamudo -- in ta je
    # izmerjeno slaba: IC 502 je bil v Borovnici +17 min, tabla v Litiji
    # (dve postaji naprej) pa je pisala 0 min. Potnik bi bral, da je vlak
    # tocen. Isto pravilo ze velja pri /api/live in v oknu vozjne.
    # Za dan, ki ni danes, meje ni: pretekli dan je koncan in vse, kar je v
    # `run`, JE meritev; prihodnji dan tam nima nicesar. Zato takrat vzamemo
    # trenutek za koncem vseh voznj -- varovalo za lazne nicle vseeno velja.
    last = last_measured(conn, service_date, [d["trip_id"] for d in out],
                         now_s if now_s is not None else 48 * 3600)
    slack = _slack_ahead(conn, [d["trip_id"] for d in out])
    for d in out:
        lm = last.get(d["trip_id"])
        own = d["delay_s"]
        if lm and lm["stop_seq"] >= d["stop_seq"]:
            # Vozilo je tu ze bilo -- vrednost je meritev. Kadar je za TO
            # postajo nimamo (vlaki ne porocajo `stop_seq = 1`), vzamemo
            # zadnjo znano in povemo, od kod je.
            #
            # Fizika je tretji primer: vozilo je moralo biti TU, preden je
            # prislo do `lm`. Kadar vrednost trdi drugace, je ostanek, ki ga
            # feed ni vec potrdil -- isti pojav, ki ga v oknu voznje lovi
            # `stats.oznaci_neskladne()`, le da tabla vidi en sam postanek in
            # zmore samo to primerjavo. Dopust 60 s, ker prikaz kaze minute.
            nemogoce = (own is not None and lm["stop_seq"] > d["stop_seq"]
                        and d["t_s"] + own > lm["t_s"] + lm["delay_s"] + 60)
            uporabi = None if (own is None or nemogoce) else own
            d["delay_s"] = uporabi if uporabi is not None else lm["delay_s"]
            d["delay_from"] = None if uporabi is not None else lm["name"]
            d["delay_kind"] = "izmerjeno"
        elif lm:
            # Vozilo je se pred to postajo. Prenesemo njegovo trenutno zamudo
            # naprej -- merjeno je to bistveno bolje od feedove napovedi
            # (MAE 1,3 min proti 7,9) -- in povemo, da je ocena.
            #
            # A goli prenos je na dolgih postankih narobe, in to v NAJSLABSO
            # smer: RG 1604 stoji v Ljubljani 21 minut, torej pride +15 in
            # odpelje ob 23:05 po voznem redu. Tabla je pisala 23:20 in
            # potnik bi prisel na ze prazen peron. Zato vozilo najprej porabi
            # rezervo voznega reda med svojo lego in to postajo.
            # Pri odhodih steje tudi postanek na TEJ postaji -- vozilo ga
            # bo skrajsalo, preden odpelje. Pri prihodih ne: takrat vozilo
            # se pride in postanek je sele za tem.
            zadnji = d["stop_seq"] if kind == "odhodi" else d["stop_seq"] - 1
            vrsta = slack.get(d["trip_id"], ())
            rez = sum(w for seq, w in vrsta if lm["stop_seq"] < seq <= zadnji)
            # Prevoznikova vrednost samo navzgor (glej `stats._with_operator`),
            # razen dokler vlak stoji na dolgem postanku -- takrat je to le
            # prenos prihodne zamude (`stats._operator_is_stale`).
            prev = None if _operator_is_stale(
                own, lm["delay_arr"], lm["delay_s"],
                dwell_at(vrsta, lm["stop_seq"])) else own
            # Ista ocena kot v oknu voznje in v iskalniku zvez -- glej
            # `stats.estimate_at`. Sam prenos z rezervo je izmerjeno slabsi.
            #
            # Samo pri ODHODIH: `predict` racuna odhodno zamudo in v rezervo
            # steje tudi postanek na ciljni postaji, kar je pri odhodu prav.
            # Pri prihodih vozilo tega postanka se ni opravilo, `zadnji` pa je
            # tam PREJSNJA postaja -- model bi torej odgovarjal o napacnem
            # kraju. Prihodi zato ostanejo pri prenosu z rezervo.
            ocena = (estimate_at(conn, d["train_no"], d["trip_id"], lm["stop_seq"],
                                 lm["delay_s"], d["stop_seq"], service_date)
                     if kind == "odhodi" else None)
            d["delay_s"] = (ocena if ocena is not None
                            else _with_operator(_after_slack(lm["delay_s"], rez), prev))
            d["slack_s"] = rez
            d["delay_from"] = lm["name"]
            d["delay_kind"] = "ocena"
        else:
            # Nobene meritve na tej voznji: feedova vrednost je napoved
            # prevoznika in ostane samo v naprednem pogledu.
            d["delay_s"] = None
            d["delay_kind"] = None
        d["feed_delay_s"] = own
        d["expected"] = (_abs_time(service_date, d["t_s"] + d["delay_s"])
                         if d["delay_s"] is not None else None)
        # Odlocitev o zamudi gre z vrstico vred -- glej `stats.opis_zamude()`.
        d["zamuda"] = opis_zamude(d["delay_s"], d["delay_kind"])

    # Sezonske razlicice iste voznje: devet vlakov v zajetem voznem redu ima
    # dva ali tri tripe z razlicnimi obdobji veljavnosti, in kadar oba veljata
    # danes, je bila ista voznja na tabli DVAKRAT. Izmerjeno na Bled Jezeru
    # 3. 9. 2026: LP 4208 ob 09:13 v dveh vrsticah, ena brez meritve in ena
    # s +6 min -- potnik vidi dva vlaka, kjer je en.
    #
    # Kljuc je fizicni odhod (stevilka, voznoredna minuta, smer), ne `trip_id`.
    # Obdrzimo vrstico, ki ima kaj povedati: najprej izmerjeno, nato kakrsnokoli
    # vrednost, sicer prvo. `resolve_trip` isto stvar resuje za okno voznje,
    # a tam po dnevih veljavnosti -- tu je bolje po podatku, ker feed poroca
    # za tisti trip, ki dejansko vozi.
    def _kakovost(d):
        return (d.get("delay_kind") == "izmerjeno", d.get("delay_s") is not None)

    zdruzeno: dict[tuple, dict] = {}
    for d in out:
        k = (d["train_no"], d["t_s"], d.get("towards"))
        if k not in zdruzeno or _kakovost(d) > _kakovost(zdruzeno[k]):
            zdruzeno[k] = d
    if len(zdruzeno) < len(out):
        out = [d for d in out if d is zdruzeno.get(
            (d["train_no"], d["t_s"], d.get("towards")))]

    # Obicajna zamuda iz zgodovine: za dan brez meritev je to edino, kar o
    # vlaku vemo. Ni napoved za ta dan in prikaz jo tako tudi imenuje.
    typ = typical_at_stops(
        conn,
        [(d["trip_id"], d["stop_seq"]) for d in out]
        + [(d["trip_id"], d["next_seq"]) for d in out if d["next_seq"] is not None],
    )
    for d in out:
        d["typical"] = typ.get((d["trip_id"], d["stop_seq"]))
        d["typical_from"] = None
        if d["typical"] is None and d["next_seq"] is not None:
            nxt = typ.get((d["trip_id"], d["next_seq"]))
            if nxt:
                d["typical"] = nxt
                d["typical_from"] = d["next_stop"]
        for k in ("next_delay_s", "next_stop", "next_seq"):
            d.pop(k, None)

    # Vceraj zacet promet, ki se ni koncan. Rekurzija namesto druge poizvedbe:
    # vse, kar sledi (meja meritve, zdruzevanje dvojnikov, obicajna zamuda),
    # mora teci nad PRAVIM prometnim dnevom, sicer bi bilo treba isti racun
    # napisati dvakrat. Poizvedba je ozka sama po sebi -- ob `from_s` cez
    # 86400 se ujamejo samo postanki po polnoci, teh pa je 50 (vlak) in
    # 2 241 (avtobus).
    if _vceraj and from_s < NOCNI_REP_S:
        prej = (date.fromisoformat(service_date) - timedelta(days=1)).isoformat()
        vcerajsnje = board(conn, station, prej, from_s + 86400, window_min, kind,
                           limit, network,
                           None if now_s is None else now_s + 86400, _vceraj=False)
        if vcerajsnje:
            out = sorted(vcerajsnje + out, key=lambda d: d["sched"])[:limit]
    return out


# ---------------------------------------------------------------- prestopi

_TRANSFER_SQL = """
WITH a AS (
    SELECT s.trip_id, s.stop_seq, COALESCE(s.dep_s, s.arr_s) AS dep_s
    FROM sched s JOIN station z ON z.stop_id = s.stop_id AND z.name = :a
    JOIN trip t ON t.trip_id = s.trip_id
    JOIN service_day sd ON sd.service_id = t.service_id AND sd.date = :day
                       AND (:network IS NULL OR t.network = :network)
),
b AS (
    SELECT s.trip_id, s.stop_seq, COALESCE(s.arr_s, s.dep_s) AS arr_s
    FROM sched s JOIN station z ON z.stop_id = s.stop_id AND z.name = :b
    JOIN trip t ON t.trip_id = s.trip_id
    JOIN service_day sd ON sd.service_id = t.service_id AND sd.date = :day
                       AND (:network IS NULL OR t.network = :network)
)
SELECT t1.train_no AS train1, t1.trip_id AS trip1, t1.headsign AS headsign1,
       t2.train_no AS train2, t2.trip_id AS trip2, t2.headsign AS headsign2,
       a.stop_seq AS a_seq, a.dep_s AS dep_s,
       x1.stop_seq AS x1_seq, COALESCE(x1.arr_s, x1.dep_s) AS x_arr_s,
       x2.stop_seq AS x2_seq, COALESCE(x2.dep_s, x2.arr_s) AS x_dep_s,
       b.stop_seq AS b_seq, b.arr_s AS arr_s,
       zx.name AS via
FROM a
JOIN sched x1   ON x1.trip_id = a.trip_id AND x1.stop_seq > a.stop_seq
JOIN sched x2   ON x2.stop_id = x1.stop_id
JOIN b          ON b.trip_id = x2.trip_id AND b.stop_seq > x2.stop_seq
JOIN trip t1    ON t1.trip_id = a.trip_id
JOIN trip t2    ON t2.trip_id = b.trip_id
JOIN station zx ON zx.stop_id = x1.stop_id
WHERE t1.trip_id <> t2.trip_id
  AND COALESCE(x2.dep_s, x2.arr_s) - COALESCE(x1.arr_s, x1.dep_s)
      BETWEEN :min_gap AND :max_gap
  AND b.arr_s > a.dep_s
  AND a.dep_s >= :earliest
  -- Ce drugi vlak ustavi tudi na izhodiscu in tam odpelje po nasem odhodu,
  -- potnik nima razloga za prestop: pocakal bi in se peljal naravnost.
  -- Brez tega pogoja iskalnik ponuja 75 minut cakanja na vmesni postaji
  -- namesto vlaka, ki cez uro odpelje z iste postaje.
  AND NOT EXISTS (
        SELECT 1 FROM sched s0
        JOIN station z0 ON z0.stop_id = s0.stop_id AND z0.name = :a
        WHERE s0.trip_id = t2.trip_id
          AND s0.stop_seq < x2.stop_seq
          AND COALESCE(s0.dep_s, s0.arr_s) >= a.dep_s
  )
"""


# Kdaj prestop ne more pomagati, ker neposredne vozijo pogosto.
#
# Meja je izmerjena, ne izbrana. Mediana razmika med zaporednimi neposrednimi
# odhodi (7. 9. 2026, isti dan, iste postaje):
#
#   Bavarski dvor -> Polje   mestni avtobus   161 zvez, mediana  **6 min**
#   Ljubljana AP -> Maribor AP  medkrajevni      8 zvez, mediana   70 min
#   Ljubljana -> Maribor     vlak              11 zvez, mediana  120 min
#   Ljubljana -> Koper       vlak               3 zveze, mediana  520 min
#
# Med 6 in 70 minutami ni ničesar, zato je 15 minut varna sredina.
GOSTO_S = 15 * 60
# Pri treh vožnjah mediana ničesar ne pove; osem je najmanj, da je razmik
# sploh razmik in ne naključje.
GOSTO_MIN_ZVEZ = 8


def dovolj_gosto(direct: list[dict] | None) -> bool:
    """Ali neposredne vozijo tako pogosto, da prestop nima kaj prihraniti.

    **Zakaj to sploh je.** Iskanje z enim prestopom je poizvedba, ki se
    razveji čez vse pare voženj, ki se kje srečata. Na prometni mestni postaji
    je to izmerjeno **26,5 s** (Bavarski dvor -> Polje, od trenutne ure) in
    40,5 s za cel dan, medtem ko je isto pri vlakih 0,0 s. Odgovor je bil zato
    počasnejši od Cloudflarove meje in stran je ostala prazna.

    Kar s tem izgubimo, je pošteno povedati: prestop bi teoretično lahko bil
    hitrejši tudi ob šestminutnem taktu, če neposredna linija vozi v veliki
    zanki. Ob 161 neposrednih zvezah je to šum, ki stane pol minute čakanja.
    """
    if not direct or len(direct) < GOSTO_MIN_ZVEZ:
        return False
    casi = sorted(d["dep_s"] for d in direct if d.get("dep_s") is not None)
    if len(casi) < GOSTO_MIN_ZVEZ:
        return False
    razmiki = sorted(casi[i + 1] - casi[i] for i in range(len(casi) - 1))
    return razmiki[len(razmiki) // 2] <= GOSTO_S


def transfers(conn: sqlite3.Connection, from_name: str, to_name: str,
              service_date: str, earliest_s: int = 0, limit: int = 8,
              direct: list[dict] | None = None,
              network: str | None = None) -> list[dict]:
    """Povezave z enim prestopom.

    Brez tega iskalnik na velikem delu države ne najde ničesar -- neposredne
    vožnje Koper--Maribor ni. Zveze ne jemljemo kot zajamčene: `MIN_TRANSFER_MIN`
    je najkrajši čas, ki ga sploh ponudimo, in če prvi vlak zamuja, prikaz to
    pove sam.

    Več prestopov namenoma ne iščemo. Slovenska mreža jih skoraj ne potrebuje,
    dva prestopa pa bi iz preproste poizvedbe naredila iskanje poti z utežmi.
    """
    min_min, max_min = TRANSFER_LIMITS.get(network or "zeleznica",
                                           TRANSFER_LIMITS["zeleznica"])
    rows = conn.execute(_TRANSFER_SQL, {
        "a": from_name, "b": to_name, "day": service_date, "network": network,
        "min_gap": min_min * 60, "max_gap": max_min * 60,
        "earliest": earliest_s,
    }).fetchall()

    # Za vsak par (odhod, prihod) obdrzi najkrajso izvedbo. Isti par vlakov
    # se lahko srecá na vec postajah -- ponudimo tisto z najmanj cakanja.
    best: dict[tuple, dict] = {}
    for r in rows:
        d = dict(r)
        d["wait_s"] = d["x_dep_s"] - d["x_arr_s"]
        d["duration_s"] = d["arr_s"] - d["dep_s"]
        key = (d["trip1"], d["trip2"])
        prev = best.get(key)
        if prev is None or d["duration_s"] < prev["duration_s"]:
            best[key] = d

    out = sorted(best.values(), key=lambda d: (d["dep_s"], d["duration_s"]))

    # Ista odhodna minuta z istim prvim vlakom: obdrzi najhitrejso zvezo,
    # sicer je seznam poln razlicic istega potovanja.
    seen: dict[tuple, dict] = {}
    for d in out:
        key = (d["train1"], d["dep_s"])
        if key not in seen or d["duration_s"] < seen[key]["duration_s"]:
            seen[key] = d
    out = sorted(seen.values(), key=lambda d: (d["dep_s"], d["duration_s"]))[:limit]

    if direct:
        # Neposredna vožnja, ki odpelje kasneje in pripelje prej ali hkrati,
        # prestop popolnoma prekasa -- prikaz ga ne sme ponujati.
        pairs = [(c["dep_s"], c["arr_s"]) for c in direct]
        out = [d for d in out
               if not any(dep >= d["dep_s"] and arr <= d["arr_s"] for dep, arr in pairs)]

    _annotate_transfer_risk(conn, out, service_date)
    for d in out:
        d["min_transfer_min"] = min_min

    for d in out:
        d["sched_dep"] = _abs_time(service_date, d["dep_s"])
        d["sched_arr"] = _abs_time(service_date, d["arr_s"])
        d["via_arr"] = _abs_time(service_date, d["x_arr_s"])
        d["via_dep"] = _abs_time(service_date, d["x_dep_s"])
        # Ista oblika noge kot pri `plan()`: `dep_s`/`arr_s` sta bila samo tam
        # in prikaz je cakanje racunal iz njiju -- pri enem prestopu je zato
        # pisalo "prestop na postaji Zidani Most · NaN min". Dve poti, ki
        # vracata isto stvar, morata vracati enake kljuce.
        d["legs"] = [
            {"train_no": d["train1"], "headsign": d["headsign1"],
             "trip_id": d["trip1"], "from": from_name, "to": d["via"],
             "dep": d["sched_dep"], "arr": d["via_arr"],
             "dep_s": d["dep_s"], "arr_s": d["x_arr_s"]},
            {"train_no": d["train2"], "headsign": d["headsign2"],
             "trip_id": d["trip2"], "from": d["via"], "to": to_name,
             "dep": d["via_dep"], "arr": d["sched_arr"],
             "dep_s": d["x_dep_s"], "arr_s": d["arr_s"]},
        ]
    return out


# Koliko minut mora ostati, da zvezo se imenujemo "drzi". Pod tem je ujeti
# vlak, ne prestop.
TIGHT_TRANSFER_MIN = 3


def _annotate_transfer_risk(conn: sqlite3.Connection, legs: list[dict],
                            service_date: str) -> None:
    """Ali bo zveza držala, če prvi vlak zamuja.

    Iskalnik, ki ponudi šest minut za prestop in zamolči, da prvi vlak zamuja
    dvanajst, ne odgovarja na vprašanje, s katerim je človek prišel. Meritev
    imamo -- za oba vlaka, na prestopni postaji.

    Račun je preprost in namenoma tak: čas za prestop = (odhod drugega +
    njegova zamuda) − (prihod prvega + njegova zamuda). Ne trdimo, da bo
    drugi vlak počakal; **prevoznik zveze pogosto drži in ta račun tega ne
    ve**, zato prikaz govori o tem, kaj kaže, ne o tem, kaj bo.
    """
    if not legs:
        return
    pairs = [(d["trip1"], d["x1_seq"]) for d in legs] + [(d["trip2"], d["x2_seq"]) for d in legs]
    marks = ",".join(["(?,?)"] * len(pairs))
    params = [x for pair in pairs for x in pair]
    live = {
        (r["trip_id"], r["stop_seq"]): r["d"]
        for r in conn.execute(
            f"WITH want(trip_id, stop_seq) AS (VALUES {marks}) "
            f"SELECT r.trip_id, r.stop_seq, COALESCE(r.delay_dep, r.delay_arr) AS d "
            f"FROM run r JOIN want w ON w.trip_id = r.trip_id AND w.stop_seq = r.stop_seq "
            f"WHERE r.service_date = ? AND d IS NOT NULL",
            (*params, service_date),
        )
    }
    typical = typical_at_stops(conn, pairs)

    for d in legs:
        a_live = live.get((d["trip1"], d["x1_seq"]))
        b_live = live.get((d["trip2"], d["x2_seq"]))
        source = "izmerjeno"
        a = a_live
        b = b_live
        if a is None:
            t = typical.get((d["trip1"], d["x1_seq"]))
            a = round(t["median_s"]) if t else None
            source = "običajno"
        if b is None:
            t = typical.get((d["trip2"], d["x2_seq"]))
            b = round(t["median_s"]) if t else None
            if source == "izmerjeno":
                source = "delno izmerjeno"

        if a is None and b is None:
            d["transfer"] = {"wait_s": d["wait_s"], "status": "brez podatka", "source": None}
            continue

        wait = d["wait_s"] + (b or 0) - (a or 0)
        if wait < 0:
            status = "ne drži"
        elif wait < TIGHT_TRANSFER_MIN * 60:
            status = "tesno"
        else:
            status = "drži"
        d["transfer"] = {
            "wait_s": wait,
            "status": status,
            "source": source,
            "delay1_s": a,
            "delay2_s": b,
        }


def now_seconds(when: datetime | None = None) -> int:
    when = when or datetime.now(TZ)
    return when.hour * 3600 + when.minute * 60 + when.second


def today(when: datetime | None = None) -> str:
    return (when or datetime.now(TZ)).date().isoformat()


def yesterday(when: datetime | None = None) -> str:
    return ((when or datetime.now(TZ)).date() - timedelta(days=1)).isoformat()


# ---------------------------------------------------------------- dva prestopa

# Koliko nog (voznj) najvec. Stiri noge = trije prestopi.
#
# Dva nista dovolj: Ljutomer mesto -> Ribnica in Stara Cerkev -> Prevalje
# rabita tri, in to nista izmisljena primera -- prisla sta iz vzorca, v
# katerem 36 % parov postaj ni imelo odgovora. Cena je majhna: iskanje tece
# 28 ms na zeleznici in 60 ms na avtobusnem omrezju.
MAX_LEGS = 4

# Varovalka: iskanje tece nad celim dnevnim voznim redom v pomnilniku.
#
# Stevilka je bila 200 000 na domnevo "pri avtobusih 80 000". Z mestnim LPP
# jih je **247 346** in varovalka je zacela tiho vracati prazen vozni red --
# `plan()` torej ni nasel nicesar in tega ni nihce povedal. Prav ta razred
# napake straži `preveri.sh`, a je ni ujel, ker `plan()` tece sele takrat, ko
# ni ne neposredne ne prestopa.
#
# Nova meja je izmerjena: cel avtobusni dan je 92 MB zadrzano in 127 MB vrh,
# nalozi se v 1,6 s. Predpomnilnik je zato zmanjsan na dva vnosa, da je
# najhujsi primer ~184 MB in ne 370.
MAX_STOP_TIMES = 300_000


# Dnevni vozni red v pomnilniku, da ga ne beremo znova ob vsakem iskanju.
# Veljaven je, dokler se ne spremeni GTFS uvoz -- `gtfs_imported_at` je zig,
# ki se ob uvozu premakne, in s tem pade cel predpomnilnik. Hranimo najvec
# nekaj dni; vec jih naenkrat nihce ne gleda.
_TT_CACHE: dict[tuple, tuple] = {}
_TT_CACHE_MAX = 2


def _timetable_for_day(conn: sqlite3.Connection, service_date: str,
                       network: str | None) -> tuple[dict, dict]:
    """Ves dnevni vozni red v pomnilnik: po vožnjah in po postajališčih.

    Iskanje z dvema prestopoma je zaporedje "vkrcaj se, pelji, izstopi" in bi
    v SQL pomenilo trojni kartezični zmnožek. V pomnilniku je to nekaj
    slovarjev in nekaj deset milisekund.
    """
    # Kljuc mora vsebovati TUDI bazo. Sicer si dve bazi z istim zigom delita
    # predpomnilnik -- v testih se je to takoj pokazalo, ker vsak test dobi
    # svojo bazo v pomnilniku in vse imajo zig prazen.
    stamp = conn.execute(
        "SELECT value FROM meta WHERE key = 'gtfs_imported_at'").fetchone()
    stamp = stamp["value"] if stamp else None
    where = conn.execute("PRAGMA database_list").fetchone()["file"]
    key = (where, service_date, network, stamp)
    # Brez ziga ne predpomnimo: to je sveza ali testna baza, kjer se vsebina
    # lahko spremeni pod nami in nam nihce ne pove.
    if stamp:
        cached = _TT_CACHE.get(key)
        if cached is not None:
            return cached

    rows = conn.execute(
        "SELECT s.trip_id, s.stop_seq, s.stop_id, s.arr_s, s.dep_s "
        "FROM sched s JOIN trip t ON t.trip_id = s.trip_id "
        "JOIN service_day sd ON sd.service_id = t.service_id AND sd.date = ? "
        "WHERE (? IS NULL OR t.network = ?) "
        "ORDER BY s.trip_id, s.stop_seq",
        (service_date, network, network),
    ).fetchall()
    if len(rows) > MAX_STOP_TIMES:
        # Prazen izid tudi predpomnimo: brez tega bi vsak klic znova prebral
        # cetrt milijona vrstic, da bi vrnil nic. Vsebina se brez novega ziga
        # ne more spremeniti, zato je to varno.
        if stamp:
            _TT_CACHE[key] = ({}, {})
        return {}, {}

    by_trip: dict[str, list] = {}
    at_stop: dict[str, list] = {}
    for r in rows:
        entry = (r["stop_seq"], r["stop_id"],
                 r["arr_s"] if r["arr_s"] is not None else r["dep_s"],
                 r["dep_s"] if r["dep_s"] is not None else r["arr_s"])
        by_trip.setdefault(r["trip_id"], []).append(entry)
        if entry[3] is not None:
            at_stop.setdefault(r["stop_id"], []).append((entry[3], r["trip_id"], r["stop_seq"]))
    for v in at_stop.values():
        v.sort()

    if stamp:
        if len(_TT_CACHE) >= _TT_CACHE_MAX:
            _TT_CACHE.clear()   # brez vrstnega reda; teh je par in so poceni
        _TT_CACHE[key] = (by_trip, at_stop)
    return by_trip, at_stop


def _stop_ids_of(conn: sqlite3.Connection, name: str) -> set[str]:
    """Vsi `stop_id` tega imena. Mestno postajališče jih ima po enega na smer."""
    return {r["stop_id"] for r in conn.execute(
        "SELECT stop_id FROM station WHERE name = ?", (name,))}


def plan(conn: sqlite3.Connection, from_name: str, to_name: str,
         service_date: str, earliest_s: int = 0,
         network: str | None = None, max_legs: int = MAX_LEGS) -> list[dict]:
    """Najzgodnejši prihod z največ `max_legs - 1` prestopi.

    Uporablja se **šele**, ko neposredna vožnja in en prestop ne dasta nič.
    Vzorec 80 parov železniških postaj: 15 neposredno, 36 z enim prestopom,
    29 brez odgovora — 36 % vprašanj je ostalo brez odgovora, čeprav pot
    obstaja (Ljutomer mesto -> Ribnica, Narin -> Kranj).

    Postopek je krog na nogo: iz vsakega dosezenega postajališča se vkrcaj na
    vsako vožnjo, ki odpelje dovolj pozno, in sprosti čase prihoda naprej po
    njej. Ohranjamo najzgodnejši prihod na postajališče; to ni nujno pot z
    najmanj prestopi, je pa pot, ki te najprej pripelje -- in prav to je
    vprašanje, ko drugega odgovora ni.
    """
    by_trip, at_stop = _timetable_for_day(conn, service_date, network)
    if not by_trip:
        return []
    starts = _stop_ids_of(conn, from_name)
    targets = _stop_ids_of(conn, to_name)
    if not starts or not targets:
        return []

    min_gap = TRANSFER_LIMITS.get(network or "zeleznica",
                                  TRANSFER_LIMITS["zeleznica"])[0] * 60

    best: dict[str, int] = {sid: earliest_s for sid in starts}
    # od kod smo prisli: stop_id -> (trip_id, vstopno postajalisce, vstopni seq, izstopni seq)
    parent: dict[str, tuple] = {}
    frontier = set(starts)

    for leg in range(max_legs):
        marked: set[str] = set()
        for sid in frontier:
            ready = best[sid] + (0 if leg == 0 else min_gap)
            for dep_s, trip_id, seq in at_stop.get(sid, ()):
                if dep_s < ready:
                    continue
                # Po tej voznji naprej: sprosti prihode na vse nadaljnje postanke.
                for nseq, nstop, narr, _ in by_trip[trip_id]:
                    if nseq <= seq or narr is None:
                        continue
                    if narr < best.get(nstop, 1 << 30):
                        best[nstop] = narr
                        parent[nstop] = (trip_id, sid, seq, nseq)
                        marked.add(nstop)
        frontier = marked
        if not frontier:
            break

    reached = [t for t in targets if t in parent]
    if not reached:
        return []
    end = min(reached, key=lambda t: best[t])

    # Pot nazaj do izhodisca.
    legs: list[tuple] = []
    cur = end
    while cur in parent:
        trip_id, board, bseq, aseq = parent[cur]
        legs.append((trip_id, board, bseq, cur, aseq))
        cur = board
        if len(legs) > max_legs:
            return []            # varovalka pred ciklom, ki ga ne bi smelo biti
    legs.reverse()
    if len(legs) <= 2:
        return []                # to zna ze `transfers()`, in bolje

    return [_build_itinerary(conn, legs, service_date, by_trip)]


def _build_itinerary(conn: sqlite3.Connection, legs: list[tuple],
                     service_date: str, by_trip: dict) -> dict:
    """Iz zaporedja nog sestavi isto obliko, kot jo vrne `transfers()`.

    Prikaz tako ne rabi vedeti, od kod je pot prišla -- ena oblika, en izris.
    """
    names = {r["stop_id"]: r["name"] for r in conn.execute("SELECT stop_id, name FROM station")}
    info = {r["trip_id"]: r for r in conn.execute(
        "SELECT trip_id, train_no, headsign, mode, network, agency FROM trip "
        f"WHERE trip_id IN ({','.join('?' * len(legs))})", [x[0] for x in legs])}

    out_legs = []
    for trip_id, board, bseq, alight, aseq in legs:
        stops = {s[0]: s for s in by_trip[trip_id]}
        t = info[trip_id]
        out_legs.append({
            "train_no": t["train_no"], "trip_id": trip_id, "headsign": t["headsign"],
            "mode": t["mode"], "network": t["network"], "agency": t["agency"],
            "from": names.get(board, board), "to": names.get(alight, alight),
            "dep": _abs_time(service_date, stops[bseq][3]),
            "arr": _abs_time(service_date, stops[aseq][2]),
            "dep_s": stops[bseq][3], "arr_s": stops[aseq][2],
        })

    first, last = out_legs[0], out_legs[-1]
    waits = [b["dep_s"] - a["arr_s"] for a, b in zip(out_legs, out_legs[1:])]
    return {
        "train1": first["train_no"], "trip1": first["trip_id"],
        "train2": last["train_no"], "trip2": last["trip_id"],
        "via": " · ".join(l["to"] for l in out_legs[:-1]),
        "dep_s": first["dep_s"], "arr_s": last["arr_s"],
        "sched_dep": first["dep"], "sched_arr": last["arr"],
        "duration_s": last["arr_s"] - first["dep_s"],
        "wait_s": min(waits) if waits else 0,
        "transfers": len(out_legs) - 1,
        "legs": out_legs,
        "transfer": {"wait_s": min(waits) if waits else 0,
                     "status": "brez podatka", "source": None},
    }
