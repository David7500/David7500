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

import sqlite3
import unicodedata
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from . import config
from .stats import _abs_time, typical_at_stops

TZ = ZoneInfo(config.TIMEZONE)

# Koliko minut mora potnik imeti za prestop, da povezavo sploh ponudimo.
# SŽ jamči zvezo pri 5 minutah na istem peronu, a to velja le za načrtovane
# zveze; za tujo kombinacijo je 5 minut lovljenje vlaka, ne potovanje.
MIN_TRANSFER_MIN = 6
MAX_TRANSFER_MIN = 120


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


def search_stations(conn: sqlite3.Connection, q: str, limit: int = 12) -> list[dict]:
    """Postaje, ki ustrezajo nizu. Urejene po tem, kako dobro se ujemajo.

    Rang: točno ime < začetek imena < začetek besede < kjerkoli. Znotraj
    istega ranga odloča promet -- "Ljubljana" mora biti pred "Ljubljana Vodmat",
    ker je stokrat pogostejši cilj, ne zato, ker je krajša.
    """
    needle = _fold(q.strip())
    if not needle:
        return []
    rows = conn.execute(
        "SELECT st.stop_id, st.name, st.lat, st.lon, COUNT(s.trip_id) AS trips "
        "FROM station st LEFT JOIN sched s ON s.stop_id = st.stop_id "
        "GROUP BY st.stop_id"
    ).fetchall()

    scored = []
    for r in rows:
        folded = _fold(r["name"])
        if folded == needle:
            rank = 0
        elif folded.startswith(needle):
            rank = 1
        elif any(w.startswith(needle) for w in folded.split()):
            rank = 2
        elif needle in folded:
            rank = 3
        else:
            continue
        scored.append((rank, -r["trips"], r["name"], dict(r)))
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


def resolve_station(conn: sqlite3.Connection, name: str) -> str | None:
    """Vpisano ime -> točno ime postaje v bazi, ali None.

    Iskalnik sme dobiti "murska" in vseeno najti povezavo; brez tega bi vsaka
    tipkarska nenatančnost dala prazen rezultat, kar je videti kot okvara.
    """
    exact = conn.execute("SELECT name FROM station WHERE name = ?", (name,)).fetchone()
    if exact:
        return exact["name"]
    hits = search_stations(conn, name, limit=1)
    return hits[0]["name"] if hits else None


# ---------------------------------------------------------------- odhodi

_BOARD_SQL = """
WITH ends AS (
    SELECT trip_id,
           MIN(stop_seq) AS first_seq,
           MAX(stop_seq) AS last_seq
    FROM sched GROUP BY trip_id
)
SELECT t.trip_id, t.train_no, t.headsign, t.mode, t.agency,
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
          limit: int = 150) -> list[dict]:
    """Odhodna (ali prihodna) tabla postaje.

    `kind`: "odhodi" izpusti končno postajo vožnje (tam se nič ne odpelje),
    "prihodi" izpusti izhodiščno. Brez tega bi tabla vsakega vlaka štela
    dvakrat -- kot prihod in kot odhod na isti vrstici.
    """
    rows = conn.execute(_BOARD_SQL, {
        "station": station, "day": service_date,
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
        # Kadar meritve na tej postaji ni, a jo ima naslednja, jo uporabimo za
        # priblizek in to povemo. Vlak, ki je na drugi postaji +8, z izhodisca
        # skoraj gotovo ni odpeljal tocno.
        d["delay_from"] = None
        if d["delay_s"] is None and d["next_delay_s"] is not None:
            d["delay_s"] = d["next_delay_s"]
            d["delay_from"] = d["next_stop"]
        d["expected"] = (_abs_time(service_date, d["t_s"] + d["delay_s"])
                         if d["delay_s"] is not None else None)
        # Za odhodno tablo je zanimiv cilj, za prihodno izhodisce.
        d["towards"] = d["destination"] if kind == "odhodi" else d["origin"]
        d["is_terminus"] = d["stop_seq"] == d["last_seq"]
        d["is_origin"] = d["stop_seq"] == d["first_seq"]
        for k in ("first_seq", "last_seq"):
            d.pop(k)
        out.append(d)
        if len(out) >= limit:
            break

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
),
b AS (
    SELECT s.trip_id, s.stop_seq, COALESCE(s.arr_s, s.dep_s) AS arr_s
    FROM sched s JOIN station z ON z.stop_id = s.stop_id AND z.name = :b
    JOIN trip t ON t.trip_id = s.trip_id
    JOIN service_day sd ON sd.service_id = t.service_id AND sd.date = :day
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
              direct: list[dict] | None = None) -> list[dict]:
    """Povezave z enim prestopom.

    Brez tega iskalnik na velikem delu države ne najde ničesar -- neposredne
    vožnje Koper--Maribor ni. Zveze ne jemljemo kot zajamčene: `MIN_TRANSFER_MIN`
    je najkrajši čas, ki ga sploh ponudimo, in če prvi vlak zamuja, prikaz to
    pove sam.

    Več prestopov namenoma ne iščemo. Slovenska mreža jih skoraj ne potrebuje,
    dva prestopa pa bi iz preproste poizvedbe naredila iskanje poti z utežmi.
    """
    rows = conn.execute(_TRANSFER_SQL, {
        "a": from_name, "b": to_name, "day": service_date,
        "min_gap": MIN_TRANSFER_MIN * 60, "max_gap": MAX_TRANSFER_MIN * 60,
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
        d["sched_dep"] = _abs_time(service_date, d["dep_s"])
        d["sched_arr"] = _abs_time(service_date, d["arr_s"])
        d["via_arr"] = _abs_time(service_date, d["x_arr_s"])
        d["via_dep"] = _abs_time(service_date, d["x_dep_s"])
        d["legs"] = [
            {"train_no": d["train1"], "headsign": d["headsign1"],
             "from": from_name, "to": d["via"],
             "dep": d["sched_dep"], "arr": d["via_arr"]},
            {"train_no": d["train2"], "headsign": d["headsign2"],
             "from": d["via"], "to": to_name,
             "dep": d["via_dep"], "arr": d["sched_arr"]},
        ]
    return out


# Koliko minut mora ostati, da zvezo se imenujemo "drzi". Isti prag kot pri
# iskanju -- pod njim je lovljenje vlaka, ne prestop.
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
            f"SELECT r.trip_id, r.stop_seq, COALESCE(r.delay_arr, r.delay_dep) AS d "
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
