"""Obvestila o ovirah in žive zamude iz GTFS-RT `service_alerts`.

Ta vir je bil dolgo spregledan, čeprav nosi dvoje, česar `trip_updates` nima:

* **`SZ-OVIRA-*`** -- dela na progi, nadomestni prevozi, združene garniture.
  Vezana so na `route_id`, ta pa je v tem feedu ena-na-ena s tripom, zato jih
  znamo pripeti naravnost na številko vlaka. To je edini vir odgovora na
  vprašanje *zakaj* vlak zamuja; vse drugo v bazi pove le *koliko*.

* **`SZ-DELAY-*`** -- živa zamuda z **imenom prometnega mesta**, kjer je
  izmerjena ("Vlak EC 79 ima izjemno zamudo 161 min ob prihodu na postajo
  Sevnica"). Prav to je vrednost, ki jo kaže tudi aplikacija SŽ, in prav to
  je podatek, ki ga iz `trip_updates` ne moremo dobiti: tam imamo samo
  `stop_sequence` voznorednega postanka, prometno mesto pa pogosto ni postanek.

Obvestila prihajajo v parih sl + en pod različnima `alert_id`. Obeh ne
združujemo -- shranimo jezik in prikaz izbere svojega.
"""
from __future__ import annotations

import hashlib

import re
import sqlite3
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from . import config
from .collector import fetch, resolve_service_date, _rail_trip_windows, _service_dates

TZ = ZoneInfo(config.TIMEZONE)

# "Vlak LP 3224 ima izjemno zamudo 42 min ob prihodu na postajo Ljubljana Rakovnik."
# Pika na koncu je neobvezna, ker se je feed glede nje ze premislil.
_DELAY_RE = re.compile(
    r"Vlak\s+(?P<train>.+?)\s+ima\s+(?P<severe>izjemno\s+)?zamudo\s+"
    r"(?P<min>-?\d+)\s*min\s+ob\s+(?P<what>prihodu|odhodu)\s+"
    r"(?:na|s|z)\s+postaj[eo]\s+(?P<station>.+?)\.?$",
    re.IGNORECASE,
)

# GTFS-RT Alert.Cause / Alert.Effect -- samo tiste, ki jih ta feed dejansko
# uporablja; ostale pustimo kot stevilko, da prikaz ne lazniv.
CAUSE_SL = {
    1: "neznano", 2: "drug vzrok", 3: "tehnična težava", 4: "stavka",
    5: "demonstracije", 6: "nesreča", 7: "praznik", 8: "vreme",
    9: "vzdrževalna dela", 10: "gradbena dela", 11: "policijska aktivnost",
    12: "medicinska pomoč",
}
EFFECT_SL = {
    1: "vlak odpovedan", 2: "spremenjena pot", 3: "izjemna zamuda",
    4: "sprememba voznega reda", 5: "postaja zaprta", 6: "spremenjen promet",
    7: "ni vpliva", 8: "gneča", 9: "redkejši promet", 10: "postanek prestavljen",
}


# Predpona obvestil mestnega LPP. Ta feed ne da id-jev, na katere bi se dalo
# vezati -- vsako je nakljucen UUID -- zato ga sestavimo iz besedila sami.
LPP_OBVOZ = "LPP-OBVOZ-"


def _kind(alert_id: str) -> str:
    if alert_id.startswith("SZ-DELAY"):
        return "delay"
    if alert_id.startswith("SZ-OVIRA"):
        return "ovira"
    if alert_id.startswith(LPP_OBVOZ):
        return "obvoz"
    return "drugo"


def ingest_lpp(conn: sqlite3.Connection, feed) -> dict:
    """Obvestila mestnega LPP. **Feed jih poslje na vozjno, ne na dogodek.**

    Izmerjeno 7. 9. 2026: 181 obvestil, od tega **dve razlicni** -- „Postaja
    Cerinova na obvozu" (147 voznj) in „Postaja Tbilisijska na obvozu" (34).
    Vsako ima svoj nakljucen UUID, zato bi jih obicajen zajem zapisal 181 in
    stran bi pokazala isto poved stokrat.

    Zdruzimo jih po besedilu in zberemo prizadeta postajalisca. Za potnika je
    to natanko en podatek: „tu se avtobus ne bo ustavil".
    """
    seen_at = int(time.time())
    skupine: dict[tuple, dict] = {}
    for entity in feed.entity:
        if not entity.HasField("alert"):
            continue
        a = entity.alert
        header, lang = _pick(a.header_text)
        desc, _ = _pick(a.description_text)
        if not header:
            continue
        kljuc = (header, desc, lang)
        s = skupine.setdefault(kljuc, {
            "stops": set(), "routes": set(),
            "cause": a.cause or None, "effect": a.effect or None,
            "start": None, "end": None, "n": 0,
        })
        s["n"] += 1
        for e in a.informed_entity:
            if e.stop_id:
                s["stops"].add(e.stop_id)
            if e.route_id:
                s["routes"].add(e.route_id)
        if a.active_period:
            p = a.active_period[0]
            if p.start:
                s["start"] = min(s["start"] or p.start, p.start)
            if p.end:
                s["end"] = max(s["end"] or p.end, p.end)

    n_new = 0
    with conn:
        for (header, desc, lang), s in skupine.items():
            aid = LPP_OBVOZ + hashlib.sha1(header.encode()).hexdigest()[:12]
            znan = conn.execute("SELECT 1 FROM alert WHERE alert_id = ?",
                                (aid,)).fetchone() is not None
            conn.execute(
                "INSERT INTO alert(alert_id, kind, cause, effect, start_ts, end_ts,"
                "                  header, description, url, lang, first_seen, last_seen) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(alert_id) DO UPDATE SET last_seen = excluded.last_seen,"
                "  header = excluded.header, description = excluded.description",
                (aid, "obvoz", s["cause"], s["effect"], s["start"], s["end"],
                 header, desc, None, lang or "sl", seen_at, seen_at))
            if not znan:
                n_new += 1
            # Prizadeta postajalisca zapisemo znova: obvoz se lahko razsiri.
            conn.execute("DELETE FROM alert_entity WHERE alert_id = ?", (aid,))
            # **Prazen niz, ne NULL, in navaden INSERT.** `route_id` in
            # `trip_id` sta `NOT NULL DEFAULT ''`; z `NULL` je vsaka vrstica
            # padla na omejitvi, `INSERT OR IGNORE` pa jo je tiho pozrl in
            # obvestilo je ostalo brez prizadetih postajalisc -- videti je
            # bilo, kot da zajem dela. Brez `OR IGNORE` bi se to slisalo takoj.
            conn.executemany(
                "INSERT INTO alert_entity(alert_id, route_id, trip_id, stop_id) "
                "VALUES(?,'','',?)",
                [(aid, sid) for sid in s["stops"]])
    return {"obvestil": len(skupine), "novih": n_new,
            "iz_vrstic": sum(s["n"] for s in skupine.values())}


def for_stops(conn: sqlite3.Connection, stop_ids, lang: str = "sl") -> list[dict]:
    """Veljavna obvestila, ki zadevajo katero od teh postajalisc.

    Za avtobusno tablo: „na tej postaji se avtobus ne bo ustavil" je edino
    obvestilo, ki ga mestni feed sploh posilja, in brez tega ga ne vidi nihce.
    """
    ids = list(stop_ids)
    if not ids:
        return []
    now = int(time.time())
    marks = ",".join("?" * len(ids))
    rows = conn.execute(
        f"SELECT DISTINCT a.* FROM alert a JOIN alert_entity e USING (alert_id) "
        f"WHERE e.stop_id IN ({marks}) AND a.lang = ? "
        f"  AND (a.end_ts IS NULL OR a.end_ts >= ?) "
        f"  AND (a.start_ts IS NULL OR a.start_ts <= ?) "
        f"ORDER BY a.header",
        (*ids, lang, now, now)).fetchall()
    return [_alert_row(r) for r in rows]


def _pick(translated, want: str = "sl") -> tuple[str | None, str | None]:
    """Vrne (besedilo, jezik). Feed da vsak alert v enem jeziku, a se
    zanasati na to ni treba -- ce je prevodov vec, ima slovenscina prednost."""
    trs = list(translated.translation)
    if not trs:
        return None, None
    for t in trs:
        if t.language == want:
            return t.text, t.language
    return trs[0].text, trs[0].language or None


def parse_delay_text(text: str) -> dict | None:
    """Razčleni besedilo `SZ-DELAY` obvestila.

    Vrne None, kadar se oblika ne ujema -- takrat obvestilo shranimo kot
    navadno besedilo in ga ne poskušamo razumeti. Tiho ugibanje bi bilo
    slabše od priznanja, da oblike ne poznamo.
    """
    if not text:
        return None
    m = _DELAY_RE.search(text.strip())
    if not m:
        return None
    return {
        "train_no": m.group("train").strip(),
        "delay_min": int(m.group("min")),
        "station": m.group("station").strip(),
        "severe": bool(m.group("severe")),
        "event": "prihod" if m.group("what").lower().startswith("prihod") else "odhod",
    }


def ingest(conn: sqlite3.Connection, feed) -> dict:
    """Zapiše obvestila in žive zamude. Vrne števce za dnevnik."""
    now = datetime.now(TZ)
    seen_at = int(time.time())
    windows = _rail_trip_windows(conn)
    valid = _service_dates(conn, now)

    n_alerts = n_entities = n_reports = n_changed = 0

    vec_obdobij = 0
    for entity in feed.entity:
        a = entity.alert
        kind = _kind(entity.id)
        header, lang = _pick(a.header_text)
        desc, _ = _pick(a.description_text)
        url, _ = _pick(a.url)
        # GTFS-RT dopusca VEC locenih obdobij ("29.-30. avgusta in 7. septembra").
        # Mi hranimo eno, ker jih feed danes tako posilja: izmerjeno 4. 9. 2026
        # na zivem viru -- vseh 102 obvestil ima natanko eno obdobje. Ce se to
        # kdaj spremeni, bi tiho obveljalo prvo in obvestilo bi bilo prikazano
        # z napacno veljavnostjo; zato raje povemo, kot da bi molce skrajsali.
        if len(a.active_period) > 1:
            vec_obdobij += 1
        period = a.active_period[0] if a.active_period else None

        known = conn.execute("SELECT 1 FROM alert WHERE alert_id = ?",
                             (entity.id,)).fetchone() is not None
        conn.execute(
            "INSERT INTO alert(alert_id, kind, cause, effect, start_ts, end_ts,"
            "                  header, description, url, lang, first_seen, last_seen) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(alert_id) DO UPDATE SET "
            "  last_seen = excluded.last_seen, header = excluded.header,"
            "  description = excluded.description, cause = excluded.cause,"
            "  effect = excluded.effect, start_ts = excluded.start_ts,"
            "  end_ts = excluded.end_ts",
            (entity.id, kind, a.cause or None, a.effect or None,
             period.start or None if period else None,
             period.end or None if period else None,
             header, desc, url, lang, seen_at, seen_at),
        )
        n_alerts += 1

        # Prizadete poti se pri obstojecem obvestilu ne spreminjajo. Brez tega
        # pogoja gre vsako minuto 3359 stavkov INSERT OR IGNORE, ki ne
        # naredijo nicesar -- na mocnem stroju neopazno, na malini ne.
        if not known:
            for ie in a.informed_entity:
                conn.execute(
                    "INSERT OR IGNORE INTO alert_entity(alert_id, route_id, trip_id, stop_id) "
                    "VALUES(?,?,?,?)",
                    (entity.id, ie.route_id or "", ie.trip.trip_id or "", ie.stop_id or ""),
                )
                n_entities += 1

        if kind != "delay":
            continue

        # Ziva zamuda: povezi jo s tripom in zapisi samo ob spremembi.
        parsed = parse_delay_text(desc) or parse_delay_text(header)
        trip_id = next((ie.trip.trip_id for ie in a.informed_entity if ie.trip.trip_id), None)
        if not (parsed and trip_id and trip_id in windows):
            continue
        service_date = resolve_service_date(trip_id, windows.get(trip_id),
                                            valid.get(trip_id), now)
        if not service_date:
            continue
        n_reports += 1

        prev = conn.execute(
            "SELECT delay_min, station FROM delay_report "
            "WHERE trip_id=? AND service_date=? ORDER BY seen_ts DESC LIMIT 1",
            (trip_id, service_date),
        ).fetchone()
        if prev and prev["delay_min"] == parsed["delay_min"] and prev["station"] == parsed["station"]:
            continue    # nespremenjeno -- ne pisi

        conn.execute(
            "INSERT OR IGNORE INTO delay_report"
            "(trip_id, service_date, seen_ts, train_no, delay_min, station, event, severe) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (trip_id, service_date, seen_at, parsed["train_no"], parsed["delay_min"],
             parsed["station"], parsed["event"], int(parsed["severe"])),
        )
        n_changed += 1

    conn.commit()
    izid = {"alerts": n_alerts, "entities": n_entities,
            "delay_reports": n_reports, "changed": n_changed}
    # Samo kadar se zgodi -- v izpisu zajema naj ne stoji vsakih 60 s nicla.
    if vec_obdobij:
        izid["vec_obdobij"] = vec_obdobij
    return izid


def poll_once(conn: sqlite3.Connection) -> dict:
    """En zajem obvestil. Pogojni GET -- ob nespremenjenem feedu ne prenese nič.

    Pozor: ETag velja za celoten feed. Ker `SZ-DELAY` obvestila nosijo živo
    zamudo, se feed spreminja skoraj ob vsakem klicu; 304 je tu redkejši kot
    pri voznem redu, a nas nič ne stane.
    """
    feed = fetch(config.SERVICE_ALERTS_URL, conn, "alerts_etag")
    if feed is None:
        return {"alerts": 0, "changed": 0, "unchanged": True}
    return ingest(conn, feed)


# ---------------------------------------------------------------- branje

def _alert_row(r: sqlite3.Row) -> dict:
    d = dict(r)
    d["cause_label"] = CAUSE_SL.get(d.get("cause"))
    d["effect_label"] = EFFECT_SL.get(d.get("effect"))
    return d


def for_train(conn: sqlite3.Connection, train_no: str, lang: str = "sl") -> list[dict]:
    """Obvestila o ovirah, ki zadevajo ta vlak.

    Vez gre prek `route_id`: obvestila naštevajo poti, `trip` pa ima route_id
    vsake vožnje. `SZ-DELAY` sem ne sodi -- to ni ovira, ampak trenutno stanje,
    ki ga prikaz že ima iz `run`.
    """
    now = int(time.time())
    rows = conn.execute(
        "SELECT DISTINCT a.* FROM alert a "
        "JOIN alert_entity ae ON ae.alert_id = a.alert_id "
        "JOIN trip t ON t.route_id = ae.route_id "
        "WHERE t.train_no = ? AND a.kind = 'ovira' AND a.lang = ? "
        "  AND (a.end_ts IS NULL OR a.end_ts >= ?) "
        "ORDER BY a.start_ts DESC",
        (train_no, lang, now),
    ).fetchall()
    if rows:
        return [_alert_row(r) for r in rows]
    return _by_endpoints(conn, train_no, lang, now)


def _by_endpoints(conn: sqlite3.Connection, train_no: str, lang: str, now: int) -> list[dict]:
    """Obvestila, ki v naslovu imenujejo obe krajišči te vožnje.

    Rabijo jo nadomestni prevozi. Obvestila naštevajo `route_id` **vlakov**,
    ki jih avtobus nadomešča, ne avtobusnih poti -- zato po `alert_entity`
    z avtobusa ni poti do razlage, zakaj sploh vozi. Njegova krajišči pa sta
    v naslovu obvestila dobesedno: "Vozni red nadomestnega prevoza:
    Ljubljana - Logatec in obratno".

    Zahtevamo obe imeni, ne enega: "Ljubljana" je v polovici vseh naslovov.
    """
    ends = conn.execute(
        "WITH s AS (SELECT sc.stop_id, sc.stop_seq FROM trip t JOIN sched sc USING (trip_id) "
        "           WHERE t.train_no = ?) "
        "SELECT st.name FROM s JOIN station st ON st.stop_id = s.stop_id "
        "WHERE s.stop_seq = (SELECT MIN(stop_seq) FROM s) "
        "   OR s.stop_seq = (SELECT MAX(stop_seq) FROM s)",
        (train_no,),
    ).fetchall()
    names = [r["name"] for r in ends]
    if len(names) < 2:
        return []
    rows = conn.execute(
        "SELECT * FROM alert WHERE kind = 'ovira' AND lang = ? "
        "  AND (end_ts IS NULL OR end_ts >= ?) AND (start_ts IS NULL OR start_ts <= ?)",
        (lang, now, now),
    ).fetchall()
    out = [_alert_row(r) for r in rows
           if all(n.lower() in (r["header"] or "").lower() for n in names)]
    for d in out:
        d["matched_by"] = "krajišči vožnje"
    return out


#: Kako dalec naprej stran ovir gleda. Dva tedna: dlje je za potnika, ki
#: nacrtuje pot, ze bolj arhiv kot vest, seznam pa se podvoji.
NAPOVEDANO_DNI = 14


def active(conn: sqlite3.Connection, lang: str = "sl",
           tudi_napovedane: bool = False) -> list[dict]:
    """Vse veljavne ovire, z vlaki, ki jih zadevajo.

    `tudi_napovedane` doda tiste, ki se **se niso zacele**. Brez njih je stran
    ovir molcala prav o tem, cemur je namenjena: izmerjeno 4. 9. 2026 je bilo
    veljavnih 16, takih, ki se zacnejo naslednje dni, pa **32** -- najblizja
    ze naslednji dan. Potnik, ki v cetrtek gleda sobotno pot, o sobotnem
    nadomestnem prevozu ni izvedel nicesar.

    Stevec na vstopni strani (`active_count`) ostane pri veljavnih: tam pise
    "veljavnih obvestil" in napovedana bi to besedo naredila neresnicno.
    """
    now = int(time.time())
    do = now + NAPOVEDANO_DNI * 86400
    rows = conn.execute(
        "SELECT a.* FROM alert a WHERE a.kind = 'ovira' AND a.lang = ? "
        "  AND (a.end_ts IS NULL OR a.end_ts >= ?) "
        "  AND (a.start_ts IS NULL OR a.start_ts <= ?) "
        "ORDER BY a.start_ts DESC",
        (lang, now, do if tudi_napovedane else now),
    ).fetchall()
    out = []
    for r in rows:
        d = _alert_row(r)
        d["napovedana"] = bool(r["start_ts"] and r["start_ts"] > now)
        d["trains"] = [x["train_no"] for x in conn.execute(
            "SELECT DISTINCT t.train_no FROM alert_entity ae "
            "JOIN trip t ON t.route_id = ae.route_id "
            "WHERE ae.alert_id = ? ORDER BY t.train_no",
            (r["alert_id"],),
        )]
        out.append(d)
    return out


def active_count(conn: sqlite3.Connection, lang: str = "sl") -> int:
    """Koliko ovir je zdaj veljavnih.

    Vstopna stran hoce samo stevilko. `active()` bi zanjo za vsako obvestilo
    poiskala se prizadete vlake -- seznam, ki ga nihce ne pogleda.
    """
    now = int(time.time())
    return conn.execute(
        "SELECT COUNT(*) FROM alert a WHERE a.kind = 'ovira' AND a.lang = ? "
        "  AND (a.end_ts IS NULL OR a.end_ts >= ?) "
        "  AND (a.start_ts IS NULL OR a.start_ts <= ?)",
        (lang, now, now),
    ).fetchone()[0]


def for_trains(conn: sqlite3.Connection, train_nos: list[str],
               mentions: list[str] | None = None, lang: str = "sl",
               limit: int = 6) -> list[dict]:
    """Ovire za skupino vlakov, urejene po tem, kako verjetno zadevajo potnika.

    Brez urejanja je to neuporabno: generično obvestilo visi na 75 vlakih in
    se pojavi ob vsaki poizvedbi. Zato dvoje:

    * obvestilo, ki v naslovu imenuje postajo s te poti, gre naprej -- "zapora
      Celje - Šentjur" je pri vožnji čez Celje nekaj drugega kot pri vožnji
      po Bohinjski progi;
    * med ostalimi je zgoraj tisto, ki zadeva manj vlakov, ker je bolj določno.

    To ni sklepanje o vzroku zamude. Je razvrščanje besedila po tem, ali
    omenja kraje, skozi katere se pelje.
    """
    if not train_nos:
        return []
    now = int(time.time())
    marks = ",".join("?" * len(train_nos))
    rows = conn.execute(
        f"SELECT a.*, COUNT(DISTINCT t.train_no) AS hits "
        f"FROM alert a "
        f"JOIN alert_entity ae ON ae.alert_id = a.alert_id "
        f"JOIN trip t ON t.route_id = ae.route_id "
        f"WHERE t.train_no IN ({marks}) AND a.kind = 'ovira' AND a.lang = ? "
        f"  AND (a.end_ts IS NULL OR a.end_ts >= ?) "
        f"  AND (a.start_ts IS NULL OR a.start_ts <= ?) "
        f"GROUP BY a.alert_id",
        (*train_nos, lang, now, now),
    ).fetchall()

    folded = [m.lower() for m in (mentions or []) if m]
    out = []
    for r in rows:
        d = _alert_row(r)
        text = f"{d.get('header') or ''} {d.get('description') or ''}".lower()
        d["mentions_route"] = any(m in text for m in folded)
        out.append(d)
    # Najprej imenovane postaje, nato bolj dolocena obvestila (manj vlakov).
    out.sort(key=lambda d: (not d["mentions_route"], d["hits"], d.get("header") or ""))
    return out[:limit]


def live_delays(conn: sqlite3.Connection, service_date: str | None = None) -> list[dict]:
    """Zadnje poročilo o zamudi za vsak vlak na dani dan.

    To je merodajna vrednost prevoznika, vključno s prometnim mestom -- naša
    `run` tabela pozna samo voznoredne postanke in tega imena nima.
    """
    service_date = service_date or datetime.now(TZ).date().isoformat()
    # Prometno mesto pripnemo koordinati, kadar ga poznamo kot postajo. Ni
    # samoumevno -- prometnih mest je vec kot postajalisc -- a v zajetem
    # vzorcu se je doslej ujelo vseh 23 imen, in tam, kjer se ujame, je to
    # tocnejsa lega vlaka od nase "zadnje prevozene postaje z meritvijo".
    rows = conn.execute(
        "WITH last AS ("
        "  SELECT *, ROW_NUMBER() OVER (PARTITION BY trip_id ORDER BY seen_ts DESC) rn"
        "  FROM delay_report WHERE service_date = ?"
        ") "
        "SELECT last.*, st.lat AS station_lat, st.lon AS station_lon "
        "FROM last LEFT JOIN station st ON st.name = last.station "
        "WHERE rn = 1 ORDER BY delay_min DESC",
        (service_date,),
    )
    return [{k: r[k] for k in r.keys() if k != "rn"} for r in rows]


def train_reports(conn: sqlite3.Connection, train_no: str, service_date: str) -> list[dict]:
    """Zaporedje poročil o eni vožnji -- kje je bil vlak in koliko je zamujal.

    Bližje "sledenju" kot karkoli drugega, kar imamo: prometna mesta se
    zvrstijo po progi, čeprav vlak tam ne ustavlja.
    """
    rows = conn.execute(
        "SELECT * FROM delay_report WHERE train_no = ? AND service_date = ? "
        "ORDER BY seen_ts",
        (train_no, service_date),
    )
    return [dict(r) for r in rows]
