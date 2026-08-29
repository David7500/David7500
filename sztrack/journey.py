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
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from . import config, geo
from .stats import _abs_time, last_measured, typical_at_stops

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

    counts: dict[str, int] = {}
    for i in range(0, len(hits), 400):
        chunk = hits[i:i + 400]
        marks = ",".join("?" * len(chunk))
        sql = (f"SELECT s.stop_id, COUNT(*) AS n FROM sched s "
               f"JOIN trip t ON t.trip_id = s.trip_id "
               f"WHERE s.stop_id IN ({marks}) ")
        params = [r["stop_id"] for r in chunk]
        if network:
            sql += "AND t.network = ? "
            params.append(network)
        sql += "GROUP BY s.stop_id"
        for r in conn.execute(sql, params):
            counts[r["stop_id"]] = r["n"]

    scored = []
    for r in hits:
        trips = counts.get(r["stop_id"], 0)
        if not trips:
            continue        # na tem omrezju te postaje ne strezhe nic
        scored.append((rank_of(r["name"]), -trips, r["name"],
                       {**dict(r), "trips": trips}))
    scored.sort(key=lambda x: x[:3])

    # Isto ime, vec `stop_id`: mestna postajalisca imajo svojega za vsako smer
    # ("Bavarski dvor" dvakrat). Vse naprej v aplikaciji tece po IMENU postaje,
    # zato bi bila dvojnica v seznamu samo dva enaka gumba. Obdrzimo najbolj
    # prometnega in mu prištejemo postanke ostalih, da razvrscanje ostane posteno.
    seen: dict[str, dict] = {}
    for *_, d in scored:
        prev = seen.get(d["name"])
        if prev is None:
            seen[d["name"]] = d
        else:
            prev["trips"] += d["trips"]
    return list(seen.values())[:limit]


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

_BOARD_SQL = """
WITH ends AS (
    SELECT trip_id,
           MIN(stop_seq) AS first_seq,
           MAX(stop_seq) AS last_seq
    FROM sched GROUP BY trip_id
)
SELECT t.trip_id, t.train_no, t.headsign, t.mode, t.agency, t.network,
       s.stop_seq, s.arr_s, s.dep_s,
       COALESCE(s.dep_s, s.arr_s) AS t_s,
       ends.first_seq, ends.last_seq,
       origin.name AS origin, dest.name AS destination,
       COALESCE(r.delay_dep, r.delay_arr) AS delay_s,
       COALESCE(rn.delay_arr, rn.delay_dep) AS next_delay_s,
       sn.stop_seq AS next_seq,
       zn.name AS next_stop,
       r.feed_ts
FROM sched s
JOIN station here ON here.stop_id = s.stop_id AND here.name = :station
JOIN trip t       ON t.trip_id = s.trip_id
JOIN ends         ON ends.trip_id = s.trip_id
JOIN sched so     ON so.trip_id = s.trip_id AND so.stop_seq = ends.first_seq
JOIN station origin ON origin.stop_id = so.stop_id
JOIN sched sd     ON sd.trip_id = s.trip_id AND sd.stop_seq = ends.last_seq
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
          now_s: int | None = None) -> list[dict]:
    """Odhodna (ali prihodna) tabla postaje.

    `kind`: "odhodi" izpusti končno postajo vožnje (tam se nič ne odpelje),
    "prihodi" izpusti izhodiščno. Brez tega bi tabla vsakega vlaka štela
    dvakrat -- kot prihod in kot odhod na isti vrstici.

    `now_s` je trenutek, glede na katerega ločimo meritev od napovedi. Brez
    njega (drug dan) so vse vrednosti feeda enakovredne in tabla se opre na
    zgodovino.
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
    for d in out:
        lm = last.get(d["trip_id"])
        own = d["delay_s"]
        if lm and lm["stop_seq"] >= d["stop_seq"]:
            # Vozilo je tu ze bilo -- vrednost je meritev. Kadar je za TO
            # postajo nimamo (vlaki ne porocajo `stop_seq = 1`), vzamemo
            # zadnjo znano in povemo, od kod je.
            d["delay_s"] = own if own is not None else lm["delay_s"]
            d["delay_from"] = None if own is not None else lm["name"]
            d["delay_kind"] = "izmerjeno"
        elif lm:
            # Vozilo je se pred to postajo. Prenesemo njegovo trenutno zamudo
            # naprej -- merjeno je to bistveno bolje od feedove napovedi
            # (MAE 1,3 min proti 7,9) -- in povemo, da je ocena.
            d["delay_s"] = lm["delay_s"]
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

# Varovalka: iskanje tece nad celim dnevnim voznim redom v pomnilniku. Pri
# zeleznici je to ~10 000 postankov, pri avtobusih 80 000. Ce bi kdaj naraslo
# cez to, raje ne odgovorimo, kot da stran obvisi.
MAX_STOP_TIMES = 200_000


# Dnevni vozni red v pomnilniku, da ga ne beremo znova ob vsakem iskanju.
# Veljaven je, dokler se ne spremeni GTFS uvoz -- `gtfs_imported_at` je zig,
# ki se ob uvozu premakne, in s tem pade cel predpomnilnik. Hranimo najvec
# nekaj dni; vec jih naenkrat nihce ne gleda.
_TT_CACHE: dict[tuple, tuple] = {}
_TT_CACHE_MAX = 4


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
