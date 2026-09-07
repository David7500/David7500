"""Prenos in uvoz statičnega GTFS voznega reda (samo železnica)."""
from __future__ import annotations

import csv
import io
import json
import sqlite3
import statistics
import zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

from zoneinfo import ZoneInfo

from . import config, db, geo

TZ = ZoneInfo(config.TIMEZONE)


def _rows(zf: zipfile.ZipFile, name: str):
    with zf.open(name) as fh:
        yield from csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig"))


def download(conn: sqlite3.Connection, force: bool = False) -> Path | None:
    """Prenese zip samo, če se je spremenil. Vrne pot ali None (ni sprememb).

    Zip je ~41 MB in se regenerira približno enkrat dnevno -- pogojni GET s
    shranjenim ETagom pomeni, da običajno prenesemo nič.
    """
    target = config.DATA_DIR / "ijpp_gtfs.zip"
    target.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": config.USER_AGENT}
    if not force and target.exists():
        etag = db.get_meta(conn, "gtfs_etag")
        modified = db.get_meta(conn, "gtfs_last_modified")
        if etag:
            headers["If-None-Match"] = etag
        if modified:
            headers["If-Modified-Since"] = modified

    resp = requests.get(config.GTFS_URL, headers=headers, timeout=300, stream=True)
    if resp.status_code == 304:
        return None
    resp.raise_for_status()

    tmp = target.with_suffix(".tmp")
    with open(tmp, "wb") as fh:
        for chunk in resp.iter_content(1 << 20):
            fh.write(chunk)
    tmp.replace(target)

    if resp.headers.get("ETag"):
        db.set_meta(conn, "gtfs_etag", resp.headers["ETag"])
    if resp.headers.get("Last-Modified"):
        db.set_meta(conn, "gtfs_last_modified", resp.headers["Last-Modified"])
    conn.commit()
    return target


def download_lpp(conn: sqlite3.Connection, force: bool = False) -> Path | None:
    """Prenese LPP-jev lastni GTFS. Isto kot `download()`, drug vir in ključi.

    Zakaj sploh drug zip: mestnih linij LPP v IJPP ni (glej `config`).
    """
    target = config.DATA_DIR / "lpp_gtfs.zip"
    target.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": config.USER_AGENT}
    if not force and target.exists():
        etag = db.get_meta(conn, "lpp_etag")
        modified = db.get_meta(conn, "lpp_last_modified")
        if etag:
            headers["If-None-Match"] = etag
        if modified:
            headers["If-Modified-Since"] = modified

    resp = requests.get(config.LPP_GTFS_URL, headers=headers, timeout=300, stream=True)
    if resp.status_code == 304:
        return None
    resp.raise_for_status()

    tmp = target.with_suffix(".tmp")
    with open(tmp, "wb") as fh:
        for chunk in resp.iter_content(1 << 20):
            fh.write(chunk)
    tmp.replace(target)

    if resp.headers.get("ETag"):
        db.set_meta(conn, "lpp_etag", resp.headers["ETag"])
    if resp.headers.get("Last-Modified"):
        db.set_meta(conn, "lpp_last_modified", resp.headers["Last-Modified"])
    conn.commit()
    return target


def beri_lpp(zip_path: Path, dni: int, danes: str | None = None) -> dict:
    """Prebere LPP zip in vrne le okno `dni` dni od danes.

    **Okno je nujno, ne varčnost.** LPP nima voznih vzorcev kot IJPP, ampak
    svojo vožnjo za vsak datum: 62 989 voženj in 1,6 milijona postankov za en
    mesec. Ves feed bi vozni red početveril; osem dni je primerljivo z IJPP.
    """
    danes = danes or datetime.now(TZ).date().isoformat()
    konec = (date.fromisoformat(danes) + timedelta(days=dni)).isoformat()

    with zipfile.ZipFile(zip_path) as zf:
        # Najprej datumi: samo `calendar_dates.txt`, ker `calendar.txt` v tem
        # feedu ni. Vsak `service_id` je en dan.
        dnevi: dict[str, set[str]] = defaultdict(set)
        for r in _rows(zf, "calendar_dates.txt"):
            if r["exception_type"] != "1":
                continue
            d = datetime.strptime(r["date"], "%Y%m%d").date().isoformat()
            if danes <= d <= konec:
                dnevi[r["service_id"]].add(d)
        if not dnevi:
            return {"stops": {}, "trips": {}, "routes": {}, "sched": [],
                    "days": {}, "shapes": {}}

        routes = {r["route_id"]: r for r in _rows(zf, "routes.txt")}
        trips = {tr["trip_id"]: tr for tr in _rows(zf, "trips.txt")
                 if tr["service_id"] in dnevi}

        seq_by_trip: dict[str, list[tuple[int, str]]] = defaultdict(list)
        sched_rows = []
        for st in _rows(zf, "stop_times.txt"):
            if st["trip_id"] not in trips:
                continue
            n = int(st["stop_sequence"])
            seq_by_trip[st["trip_id"]].append((n, st["stop_id"]))
            sched_rows.append((st["trip_id"], n, st["stop_id"],
                               _to_seconds(st["arrival_time"]),
                               _to_seconds(st["departure_time"])))

        used = {sid for v in seq_by_trip.values() for _, sid in v}
        stops = {
            s["stop_id"]: {"stop_id": s["stop_id"], "name": s["stop_name"],
                           "lat": float(s["stop_lat"]), "lon": float(s["stop_lon"])}
            for s in _rows(zf, "stops.txt") if s["stop_id"] in used
        }

        # Trase: samo tiste, ki jih uvozene voznje res rabijo.
        want = {tr["shape_id"] for tr in trips.values() if tr.get("shape_id")}
        po_obliki: dict[str, list] = defaultdict(list)
        if want and "shapes.txt" in set(zf.namelist()):
            for r in _rows(zf, "shapes.txt"):
                if r["shape_id"] in want:
                    po_obliki[r["shape_id"]].append(
                        (int(r["shape_pt_sequence"]),
                         float(r["shape_pt_lat"]), float(r["shape_pt_lon"])))
        shapes = {}
        for sid, pts in po_obliki.items():
            pts.sort()
            if len(pts) >= 2:
                shapes[sid] = [[(a, b) for _, a, b in pts]]

    return {"stops": stops, "trips": trips, "routes": routes,
            "sched": sched_rows, "days": dnevi, "shapes": shapes}


def _service_days(zf: zipfile.ZipFile, service_ids: set[str]):
    """Razširi calendar.txt + calendar_dates.txt v konkretne datume."""
    days: dict[str, set[str]] = defaultdict(set)
    weekdays = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
    names = set(zf.namelist())

    if "calendar.txt" in names:
        for r in _rows(zf, "calendar.txt"):
            sid = r["service_id"]
            if sid not in service_ids:
                continue
            start = datetime.strptime(r["start_date"], "%Y%m%d").date()
            end = datetime.strptime(r["end_date"], "%Y%m%d").date()
            active = {i for i, w in enumerate(weekdays) if r.get(w) == "1"}
            if not active:
                continue
            d = start
            while d <= end:
                if d.weekday() in active:
                    days[sid].add(d.isoformat())
                d += timedelta(days=1)

    if "calendar_dates.txt" in names:
        for r in _rows(zf, "calendar_dates.txt"):
            sid = r["service_id"]
            if sid not in service_ids:
                continue
            d = datetime.strptime(r["date"], "%Y%m%d").date().isoformat()
            if r["exception_type"] == "1":
                days[sid].add(d)
            else:
                days[sid].discard(d)
    return days


def _to_seconds(hhmmss: str) -> int | None:
    """GTFS dopušča ure >= 24 za vožnje čez polnoč."""
    if not hhmmss:
        return None
    h, m, s = (int(x) for x in hhmmss.split(":"))
    return h * 3600 + m * 60 + s


#: Nad koliko metrov med dvema zaporednima tockama trase gre za pretrgano
#: geometrijo in ne za dolg raven odsek. Izmerjeno: surovi razmiki so 17 m
#: (mediana) do 514 m (99,9. percentil), naslednji je 22,8 km.
SHAPE_BREAK_M = 1000.0


def _edge_builder(stops):
    """Zbira dolžine in geometrijo odsekov, shape po shape.

    Shapes.txt je zvezno grupiran po shape_id, zato ga beremo pretočno in
    obdržimo v pomnilniku vedno le eno progo -- celotna datoteka je 135 MB in
    je naenkrat ne moremo naložiti na majhnem strežniku.
    """
    lengths: dict[tuple[str, str], list[float]] = defaultdict(list)
    geoms: dict[tuple[str, str], list] = {}
    # Zaporedja postankov vseh voznj -- iz njih se presoja elementarnost.
    orders: list[list[str]] = []

    def feed(points, stop_sequences):
        """points: polilinija ene proge; stop_sequences: postanki vlakov po njej."""
        if len(points) < 2:
            return
        cums = geo.cumulative(points)
        cache: dict[str, tuple[float, float]] = {}
        for stop_seq in stop_sequences:
            orders.append([sid for _, sid in stop_seq])
            projected = []
            for _, stop_id in stop_seq:
                if stop_id not in cache:
                    st = stops[stop_id]
                    cache[stop_id] = geo.project(points, cums, st["lat"], st["lon"])
                along, off = cache[stop_id]
                projected.append((stop_id, along, off))

            for (a, along_a, off_a), (b, along_b, off_b) in zip(projected, projected[1:]):
                dist = abs(along_b - along_a)
                if max(off_a, off_b) > config.MAX_STATION_OFFSET_M or dist < 50:
                    continue
                key = (a, b) if a < b else (b, a)
                lengths[key].append(dist)
                line = geo.slice_between(points, cums, along_a, along_b)
                if len(line) >= 2 and len(line) > len(geoms.get(key, ())):
                    geoms[key] = line

    def finish():
        """Odsek je "elementaren", kadar med njegovima postajama ne ustavi
        nihce -- torej kadar ni preskok hitrega vlaka cez vmesne postaje.

        **Merilo je vozni red, ne geometrija.** Prej je bilo geometrijsko:
        odsek ni bil elementaren, ce je katero od poenostavljenih ogljisc
        lezalo v 300 m od kake postaje. To je odpovedalo na obe strani:

        * Kratek mestni odsek po poenostavitvi nima nobenega vmesnega
          ogljisca -- Ljubljana - Ljubljana Tivoli (1,99 km) je imel natanko
          dve tocki in zanka je tekla cez prazen seznam. Glavna postaja je
          bila zato na zemljevidu narisana kot slepo crevo: proge z zahoda in
          juga so se koncale nekaj sto metrov pred njo.
        * Postaja na VZPOREDNI progi v 300 m je odsek razglasila za preskok,
          ceprav vlak mimo nje samo pelje. Zaostritev praga je Ljubljano
          resila, a mrezo razrezala na tri kose (bohinjska proga in Novo
          mesto sta odpadla) -- prag, ki je enkrat prevelik in drugic
          premajhen, ni prag, ampak ugibanje.

        Zdaj: postaji sta elementarno sosednji, kadar sta v kaksni voznji
        SOSEDNJI in v nobeni voznji med njima ne lezi tretja postaja. To je
        natanko pomen besede "preskok", nima prostega parametra in ne
        potrebuje geometrije.
        """
        # (postaja -> mesto v zaporedju) za vsako voznjo. Isto postajo lahko
        # voznja obisce dvakrat (obracanje); takrat vzamemo prvo pojavitev,
        # ker za sosednost steje najkrajsi razmik.
        indeksi = []
        for seq in orders:
            pos: dict[str, int] = {}
            for i, sid in enumerate(seq):
                pos.setdefault(sid, i)
            indeksi.append(pos)

        out = []
        for key, lens in lengths.items():
            line = geoms.get(key)
            if not line:
                continue
            simple = geo.simplify(line, 1e-4)
            a, b = key
            # Ce kaksna voznja obisce obe postaji in med njima se katero, je
            # to preskok in odsek ni elementaren.
            elementary = True
            for pos in indeksi:
                ia, ib = pos.get(a), pos.get(b)
                if ia is not None and ib is not None and abs(ia - ib) > 1:
                    elementary = False
                    break
            coords = [[round(lon, 6), round(lat, 6)] for lat, lon in simple]
            out.append((
                key[0], key[1], round(statistics.median(lens) / 1000, 3),
                int(elementary), len(lens),
                json.dumps({"type": "LineString", "coordinates": coords}),
            ))
        return out

    return feed, finish


def _lpp_oznaka(kratko: str) -> str:
    """`01` -> `1`, `01B` -> `1B`, `N3` ostane.

    LPP v svojem GTFS pise enomestne linije z vodilno niclo, dvomestnih pa ne.
    Na postajaliscu pise "1", in iskati se mora dati po tem, kar clovek vidi.
    """
    i = 0
    while i < len(kratko) - 1 and kratko[i] == "0":
        i += 1
    return kratko[i:] if kratko[:1] == "0" else kratko


def import_static(conn: sqlite3.Connection, zip_path: Path,
                  lpp_zip: Path | None = None) -> dict:
    """Uvozi železniški del GTFS zipa (in nadomestne prevoze SŽ).

    Statične tabele se v celoti zamenjajo -- zajem (`obs`, `run`) ostane.

    `lpp_zip` prilije mestni LPP iz **drugega** vira. Zliti mora biti tu in ne
    v svojem klicu: spodnji `DELETE FROM` pobrise vse staticne tabele, zato bi
    locen uvoz drugega vira vsakic pobrisal prvega.
    """
    with zipfile.ZipFile(zip_path) as zf:
        wanted_types = {config.RAIL_ROUTE_TYPE}
        if config.INCLUDE_REPLACEMENT_BUS:
            wanted_types.add(config.BUS_ROUTE_TYPE)
        extra = set(config.EXTRA_AGENCIES)

        def _wanted(r) -> bool:
            if r["agency_id"] == config.RAIL_AGENCY_ID:
                return r["route_type"] in wanted_types
            return r["agency_id"] in extra

        routes = {r["route_id"]: r for r in _rows(zf, "routes.txt") if _wanted(r)}
        trips = {t["trip_id"]: t for t in _rows(zf, "trips.txt") if t["route_id"] in routes}
        # Nadomestni prevozi vozijo po cesti. Njihova geometrija ne sme v
        # `edge`: mreza prog bi dobila odseke, ki niso proge, in dolzine, ki
        # niso zelezniske. Za vozni red in iskanje povezav pa so enakovredni.
        rail_trips = {
            tid for tid, t in trips.items()
            if routes[t["route_id"]]["route_type"] == config.RAIL_ROUTE_TYPE
        }

        seq_by_trip: dict[str, list[tuple[int, str]]] = defaultdict(list)
        sched_rows = []
        for st in _rows(zf, "stop_times.txt"):
            if st["trip_id"] not in trips:
                continue
            n = int(st["stop_sequence"])
            seq_by_trip[st["trip_id"]].append((n, st["stop_id"]))
            sched_rows.append(
                (st["trip_id"], n, st["stop_id"],
                 _to_seconds(st["arrival_time"]), _to_seconds(st["departure_time"]))
            )
        for v in seq_by_trip.values():
            v.sort()

        used_stops = {sid for v in seq_by_trip.values() for _, sid in v}
        stops = {
            s["stop_id"]: {
                "stop_id": s["stop_id"], "name": s["stop_name"],
                "lat": float(s["stop_lat"]), "lon": float(s["stop_lon"]),
            }
            for s in _rows(zf, "stops.txt")
            if s["stop_id"] in used_stops
        }

        by_shape: dict[str, list] = defaultdict(list)
        for trip_id, t in trips.items():
            if t["shape_id"] and trip_id in rail_trips:
                by_shape[t["shape_id"]].append(seq_by_trip[trip_id])

        # Elementarnost odseka se presoja po tem, ali na njem lezi kaksna druga
        # postaja. Avtobusna postajalisca sem ne sodijo -- ce bi, bi odsek
        # Divaca - Koper nehal biti elementaren zaradi Rodika ob cesti.
        rail_stop_ids = {sid for tid in rail_trips for _, sid in seq_by_trip.get(tid, ())}
        feed, finish = _edge_builder({k: v for k, v in stops.items() if k in rail_stop_ids})
        # Trase VSEH uvozenih voznj, ne le zeleznicnih: "kod pelje moj avtobus"
        # je vprasanje, na katero `edge` ne zna odgovoriti -- ta ima mrezo
        # prog, avtobusi pa vozijo po cesti in vanjo namenoma ne gredo.
        #
        # Beremo v istem prehodu cez `shapes.txt` kot odseke: datoteka ima
        # 4,85 milijona vrstic in dva prehoda bi bila dve minuti za nic.
        want_shapes = {t["shape_id"] for t in trips.values() if t["shape_id"]}
        shapes: dict[str, list] = {}

        def _shrani(sid, pts):
            if sid not in want_shapes or len(pts) < 2:
                return
            # Trasa je lahko PRETRGANA. V zajetem GTFS je 2 185 razmikov od
            # 4,85 milijona (0,045 %) daljsih od kilometra, pri 193 oblikah;
            # najdaljsi je 40 km. Ravna crta cez pol Slovenije je trditev,
            # da vozilo tam vozi, in ta ni resnicna -- zato traso razrezemo
            # na kose in vsakega narisemo posebej.
            #
            # Meja je izmerjena in ne izbrana na oko: surove tocke so 17 m
            # narazen (mediana), 105 m pri 99 % in 514 m pri 99,9 %, nato pa
            # skocijo na 22,8 km. Med 0,5 in 20 km ni nicesar.
            kosi, tekoci = [], [pts[0]]
            for a, b in zip(pts, pts[1:]):
                if geo.haversine(a[0], a[1], b[0], b[1]) > SHAPE_BREAK_M:
                    kosi.append(tekoci)
                    tekoci = [b]
                else:
                    tekoci.append(b)
            kosi.append(tekoci)
            # ~10 m je pod locljivostjo prikaza; iz 4,85 M tock ostane
            # pol milijona, torej 10 MB namesto 107.
            out = [geo.simplify(k) for k in kosi if len(k) >= 2]
            if out:
                shapes[sid] = out

        current, points = None, []
        for p in _rows(zf, "shapes.txt"):
            shape_id = p["shape_id"]
            if shape_id != current:
                urejeno = [pt for _, pt in sorted(points)]
                if current in by_shape:
                    feed(urejeno, by_shape[current])
                if current is not None:
                    _shrani(current, urejeno)
                current, points = shape_id, []
            if shape_id in by_shape or shape_id in want_shapes:
                points.append((int(p["shape_pt_sequence"]),
                               (float(p["shape_pt_lat"]), float(p["shape_pt_lon"]))))
        urejeno = [pt for _, pt in sorted(points)]
        if current in by_shape:
            feed(urejeno, by_shape[current])
        if current is not None:
            _shrani(current, urejeno)
        edges = finish()

        days = _service_days(zf, {t["service_id"] for t in trips.values()})

    # --- mestni LPP iz drugega vira ---------------------------------------
    lpp_trips = 0
    if lpp_zip is not None:
        mesto = beri_lpp(lpp_zip, config.LPP_DAYS)
        # Kljuci se ne morejo zaleteti: LPP ima UUID-je, IJPP stevilke.
        stops.update(mesto["stops"])
        for rid, r in mesto["routes"].items():
            routes[rid] = {**r, "route_short_name": _lpp_oznaka(r["route_short_name"])}
        trips.update(mesto["trips"])
        sched_rows.extend(mesto["sched"])
        for sid, ds in mesto["days"].items():
            days[sid].update(ds)
        shapes.update(mesto["shapes"])
        lpp_trips = len(mesto["trips"])

    with conn:
        # Voznja, ki ima MERITVE, mora prezivati uvoz tudi takrat, ko je nov
        # vozni red nima. Brez tega jo `DELETE FROM trip` osiroti: `run` in
        # `obs` ostaneta, a vsaka poizvedba gre skozi `JOIN trip` (omrezje je
        # tam), zato je od tedaj ne vidi nihce -- niti statistika niti okno
        # voznje. Tiho, brez napake.
        #
        # Izmerjeno 4. 9. 2026: tako je izginilo 114 voznj s 3 043 meritvami
        # (0,37 % vseh), vse ob prehodu na solski vozni red 1. 9. To hkrati
        # pomeni, da trditev "trip_id so med regeneracijami stabilni" drzi za
        # veliko vecino, ne pa za vse.
        #
        # Nagrobnik nima ne `sched` ne `service_day`, zato v iskanju, na tabli
        # in med "danes vozi" ne nastopi -- vidi ga samo zgodovina, kamor sodi.
        nagrobniki = [dict(r) for r in conn.execute(
            "SELECT t.* FROM trip t "
            "WHERE EXISTS (SELECT 1 FROM run r WHERE r.trip_id = t.trip_id)")]

        for table in ("station", "edge", "trip", "sched", "service_day", "shape"):
            conn.execute(f"DELETE FROM {table}")
        conn.executemany(
            "INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
            [(s["stop_id"], s["name"], s["lat"], s["lon"]) for s in stops.values()],
        )
        conn.executemany(
            "INSERT INTO edge(from_id,to_id,km,elementary,trips,geojson) VALUES(?,?,?,?,?,?)", edges
        )
        conn.executemany(
            "INSERT INTO shape(shape_id, points) VALUES(?,?)",
            [(sid, json.dumps([[[round(a, 5), round(b, 5)] for a, b in kos]
                               for kos in kosi], separators=(",", ":")))
             for sid, kosi in shapes.items()],
        )
        conn.executemany(
            "INSERT INTO trip(trip_id,route_id,train_no,headsign,service_id,color,"
            "                 mode,agency,network,block_id,shape_id) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            [
                (tid, t["route_id"], routes[t["route_id"]]["route_short_name"],
                 t.get("trip_headsign"), t["service_id"], routes[t["route_id"]].get("route_color"),
                 "vlak" if tid in rail_trips else "bus",
                 routes[t["route_id"]].get("agency_id"),
                 # Nadomestni prevoz SZ je avtobus, a pripada zeleznici: na
                 # tisti relaciji zamenjuje vlak. LPP in ostali imajo svojo stran.
                 "zeleznica" if routes[t["route_id"]]["agency_id"] == config.RAIL_AGENCY_ID
                 else "avtobus",
                 # Prazen niz je v GTFS "nimam podatka" -- shranimo NULL, da
                 # se poizvedbe ne lovijo na razliko med '' in NULL.
                 t.get("block_id") or None,
                 # Trasa te voznje. Shranimo le, kadar smo jo res uvozili --
                 # sicer bi prikaz iskal vrstico, ki je v `shape` ni.
                 t["shape_id"] if t["shape_id"] in shapes else None)
                for tid, t in trips.items()
            ],
        )
        # Vrni tiste z meritvami, ki jih nov vozni red nima. `INSERT OR IGNORE`,
        # ker je velika vecina ze vstavljena zgoraj -- vrnemo samo razliko.
        vrnjenih = 0
        for t in nagrobniki:
            if t["trip_id"] in trips:
                continue
            stolpci = ",".join(t)
            conn.execute(
                f"INSERT OR IGNORE INTO trip({stolpci}) "
                f"VALUES({','.join('?' * len(t))})", tuple(t.values()))
            vrnjenih += 1

        conn.executemany(
            "INSERT INTO sched(trip_id,stop_seq,stop_id,arr_s,dep_s) VALUES(?,?,?,?,?)", sched_rows
        )
        conn.executemany(
            "INSERT INTO service_day(service_id,date) VALUES(?,?)",
            [(sid, d) for sid, ds in days.items() for d in ds],
        )
        # Voznoredni okvir voznje se da izracunati sele, ko je `sched` poln.
        db.fill_trip_window(conn)
        # S pasom, tako kot vse drugo v projektu: brez njega je to cas stroja,
        # ki se od `config.TIMEZONE` lahko razlikuje.
        db.set_meta(conn, "gtfs_imported_at",
                    datetime.now(TZ).isoformat(timespec="seconds"))

    return {
        "stations": len(stops), "edges": len(edges),
        # Koliko voznj je prezivelo uvoz samo zato, ker imajo meritve. Ce je
        # to veliko, se je vozni red mocno premesal in je vredno pogledati.
        "trips_obdrzanih": vrnjenih,
        "trips": len(trips), "trips_rail": len(rail_trips),
        "trips_bus": len(trips) - len(rail_trips),
        "trips_lpp": lpp_trips,
        "stop_times": len(sched_rows), "service_days": sum(len(d) for d in days.values()),
        "trips_blocked": sum(1 for t in trips.values() if t.get("block_id")),
    }
