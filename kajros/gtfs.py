"""Prenos in uvoz statičnega GTFS voznega reda (samo železnica)."""
from __future__ import annotations

import csv
import io
import json
import sqlite3
import statistics
import zipfile
from collections import Counter, defaultdict
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
    """Prebere LPP zip in vrne okno od **včeraj** do `dni` dni naprej.

    **Okno je nujno, ne varčnost.** LPP nima voznih vzorcev kot IJPP, ampak
    svojo vožnjo za vsak datum: 62 989 voženj in 1,6 milijona postankov za en
    mesec. Ves feed bi vozni red početveril; osem dni je primerljivo z IJPP.

    **Zakaj se začne včeraj in ne danes.** Pri LPP je prometni dan zapisan kar
    v `trip_id` -- prva komponenta trojnega id-ja je dan. Nočni avtobus, ki ob
    01:00 še vozi, nosi **včerajšnji** dan, in če ga v bazi ni, se meritev ne
    ujame z ničimer in tiho odpade. Ujeto 8. 9. 2026 na malini: uvoz ob 00:15
    je postavil okno od 8. 9., feed ob 01:10 pa je govoril o vožnji z dne
    7. 9. -- `poll_lpp` je vrnil `trips: 0` in to je bilo videti, kot da
    ponoči pač nič ne vozi.

    Cena je en dan: ~2 400 voženj in ~62 000 postankov (izmerjeno: 19 163
    voženj in 496 542 postankov na osem dni).
    """
    danes = danes or datetime.now(TZ).date().isoformat()
    zacetek = (date.fromisoformat(danes) - timedelta(days=1)).isoformat()
    konec = (date.fromisoformat(danes) + timedelta(days=dni)).isoformat()

    with zipfile.ZipFile(zip_path) as zf:
        # Najprej datumi: samo `calendar_dates.txt`, ker `calendar.txt` v tem
        # feedu ni. Vsak `service_id` je en dan.
        dnevi: dict[str, set[str]] = defaultdict(set)
        for r in _rows(zf, "calendar_dates.txt"):
            if r["exception_type"] != "1":
                continue
            d = datetime.strptime(r["date"], "%Y%m%d").date().isoformat()
            if zacetek <= d <= konec:
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


# Najvecji razmik, pri katerem sta dva zapisa se ISTO postajalisce.
#
# Meja je izmerjena, ne izbrana. Med 24 pari imen, ki se razlikujeta samo po
# velikosti crk ali sumniku, je razdelitev ostra:
#
#   14 parov je 3-215 m narazen  -> isto postajalisce, dva zapisa
#   10 parov je 0,8-111,6 km      -> RAZLICNA kraja z istim imenom
#
# Med 215 m in 829 m ni nicesar. "Celje" in "Celje" sta 112 km narazen,
# "Lozice" in "Lozice" 43 km -- to so razlicne vasi in jih ni dovoljeno zliti.
ISTO_POSTAJALISCE_M = 500


def _poenoti_imena(stops: dict) -> int:
    """Isto postajalisce, dva zapisa imena -> eno ime.

    LPP pise dvanajst odstotkov imen s samimi velikimi crkami ("CRNUCE"),
    IJPP pa normalno ("Crnuce"). **Vse v aplikaciji tece po IMENU postaje**,
    zato sta to dve razlicni postaji: iskalnik ju pokaze obe, odhodna tabla
    razdeli odhode, budilka pa si zapomni tistega, ki ga nikjer drugje ni.

    Zdruzimo samo tiste, ki so tudi FIZICNO na istem mestu -- glej
    `ISTO_POSTAJALISCE_M`. Kanonicno je ime, ki ni v samih velikih crkah;
    ce jih je vec takih, odloci pogostost in nato abeceda, da je izid
    ponovljiv.
    """
    from .journey import _fold

    po_imenu: dict[str, list] = defaultdict(list)
    for s in stops.values():
        po_imenu[_fold(s["name"])].append(s)

    spremenjenih = 0
    for skupina in po_imenu.values():
        imena = {s["name"] for s in skupina}
        if len(imena) < 2:
            continue
        naj = max(
            geo.haversine(a["lat"], a["lon"], b["lat"], b["lon"])
            for a in skupina for b in skupina if a["name"] != b["name"]
        )
        if naj > ISTO_POSTAJALISCE_M:
            continue        # razlicna kraja z istim imenom -- pusti pri miru
        stevec = Counter(s["name"] for s in skupina)
        kanon = min(imena, key=lambda n: (n.isupper(), -stevec[n], n))
        for s in skupina:
            if s["name"] != kanon:
                s["name"] = kanon
                spremenjenih += 1
    return spremenjenih


def _lpp_oznaka(kratko: str) -> str:
    """`01` -> `1`, `01B` -> `1B`, `N3` ostane.

    LPP v svojem GTFS pise enomestne linije z vodilno niclo, dvomestnih pa ne.
    Na postajaliscu pise "1", in iskati se mora dati po tem, kar clovek vidi.
    """
    i = 0
    while i < len(kratko) - 1 and kratko[i] == "0":
        i += 1
    return kratko[i:] if kratko[:1] == "0" else kratko


# --- zamenjane vožnje ------------------------------------------------------
#
# Nov vozni red lahko vožnji da nov id, feed v živo pa jo še naprej nosi pod
# starim: ta generator ima svojo kopijo voznega reda in je ne osveži hkrati z
# nami. Brez tega zajem take vožnje zavrže (stari id nima več voznega reda),
# prikaz pa novo vožnjo kaže po voznem redu, ker zanjo ne pride nič.
#
# Ujeto 22. 9. 2026: LPP 25, 12D in 15 so v IJPP dobili nove id-je z veljavo od
# istega dne, feed pa je vseh 12 vozil teh linij javljal pod starimi. Iskalnik
# je ob 15:20 ponudil 25 s Tržnice Moste ob 15:28; LPP je pisal, da pride čez
# 25 minut. Vozilo te vožnje je bilo ob 16:01 na koncu proge, ki bi jo po
# voznem redu doseglo ob 15:41.

#: Največji premik na prvem skupnem postanku, da je nova vožnja ista kot stara.
#: Zamenjava 22. 9. 2026 je spremenila tudi vozne čase (25: 65 -> 52 minut),
#: zato se primerja začetek in ne povprečje čez progo.
ZAMENJAVA_PREMIK_S = 10 * 60

#: Kolikšen del postankov stare vožnje mora imeti tudi nova.
ZAMENJAVA_DELEZ = 0.6


def _z_voznim_redom(conn: sqlite3.Connection) -> set[str]:
    return {r[0] for r in conn.execute(
        "SELECT trip_id FROM trip WHERE start_s IS NOT NULL")}


def _vozje_za(conn: sqlite3.Connection, ids: set[str], od_dne: str,
              kljuci: set | None = None) -> dict[str, dict]:
    """Linija, dnevi od `od_dne` naprej in postanki teh voženj.

    Vožnja brez dneva od `od_dne` naprej ne pride v poštev: zamenjava je za
    feed v živo, ta pa govori o danes. Pri LPP to izloči vse, kar je zdrsnilo
    iz okna uvoza -- tam so id-ji po datumih in vsak dan jih nekaj izgine.
    """
    out: dict[str, dict] = {}
    ids = list(ids)
    for i in range(0, len(ids), 500):
        kos = ids[i:i + 500]
        for r in conn.execute(
            "SELECT t.trip_id, t.agency, t.train_no, sd.date FROM trip t "
            "JOIN service_day sd ON sd.service_id = t.service_id "
            f"WHERE t.trip_id IN ({','.join('?' * len(kos))}) AND sd.date >= ?",
            [*kos, od_dne],
        ):
            kljuc = (r[1], r[2])
            if kljuci is not None and kljuc not in kljuci:
                continue
            v = out.setdefault(r[0], {"kljuc": kljuc, "dnevi": set(), "postanki": []})
            v["dnevi"].add(r[3])
    ids = list(out)
    for i in range(0, len(ids), 500):
        kos = ids[i:i + 500]
        for r in conn.execute(
            "SELECT trip_id, stop_seq, stop_id, arr_s, dep_s FROM sched "
            f"WHERE trip_id IN ({','.join('?' * len(kos))}) ORDER BY trip_id, stop_seq",
            kos,
        ):
            out[r[0]]["postanki"].append((r[1], r[2], r[3], r[4]))
    return out


def _poravnaj(stari: list, novi: list) -> list[tuple]:
    """Pari postankov z istim postajališčem, v istem vrstnem redu.

    Po `stop_id` in ne po `stop_seq`: nova vožnja lahko kakšno postajališče
    izpusti ali doda, in zaporedna številka bi potem tiho zamaknila vse za njim.
    """
    kje: dict[str, list[int]] = defaultdict(list)
    for i, p in enumerate(novi):
        kje[p[1]].append(i)
    pari, j = [], 0
    for p in stari:
        i = next((i for i in kje.get(p[1], ()) if i >= j), None)
        if i is None:
            continue
        pari.append((p, novi[i]))
        j = i + 1
    return pari


def _ura(arr: int | None, dep: int | None) -> int | None:
    return dep if dep is not None else arr


def povezi_zamenjave(stare: dict[str, dict], nove: dict[str, dict]) -> dict[str, tuple]:
    """Katera nova vožnja je katera stara.

    `{stari_trip: (novi_trip, [(stari_seq, novi_seq, stari_arr_s, stari_dep_s)])}`.

    Par je ista linija in prevoznik, vsaj en skupen dan, večina postankov v
    istem vrstnem redu in najmanjši premik na prvem skupnem postanku. Vsaka
    nova vožnja dobi največ eno staro -- sicer bi dve vozili pisali v isto.
    """
    po_kljucu: dict[tuple, list[str]] = defaultdict(list)
    for tid, v in nove.items():
        po_kljucu[v["kljuc"]].append(tid)

    kandidati = []
    for stari, s in stare.items():
        for novi in po_kljucu.get(s["kljuc"], ()):
            n = nove[novi]
            if not s["dnevi"] & n["dnevi"]:
                continue
            pari = _poravnaj(s["postanki"], n["postanki"])
            if len(pari) < max(2, ZAMENJAVA_DELEZ * len(s["postanki"])):
                continue
            a, b = pari[0]
            ta, tb = _ura(a[2], a[3]), _ura(b[2], b[3])
            if ta is None or tb is None or abs(tb - ta) > ZAMENJAVA_PREMIK_S:
                continue
            kandidati.append((abs(tb - ta), -len(pari), stari, novi, pari))

    kandidati.sort()
    out: dict[str, tuple] = {}
    vzete: set[str] = set()
    for _, _, stari, novi, pari in kandidati:
        if stari in out or novi in vzete:
            continue
        vzete.add(novi)
        out[stari] = (novi, [(a[0], b[0], a[2], a[3]) for a, b in pari])
    return out


def _zapisi_zamenjave(conn: sqlite3.Connection, stare: dict, nove: dict) -> int:
    """Zapiše nove pare in pobriše tiste, ki ne veljajo več. Vrne število parov.

    Par velja, dokler ima nova vožnja vozni red in stara ne. Kar je bilo
    povezano ob prejšnjih uvozih, ostane: starega voznega reda takrat ni več in
    para ne bi bilo mogoče sestaviti znova.
    """
    conn.execute(
        "DELETE FROM zamenjava WHERE novi_trip NOT IN "
        "(SELECT trip_id FROM trip WHERE start_s IS NOT NULL) "
        "OR stari_trip IN (SELECT trip_id FROM trip WHERE start_s IS NOT NULL)")
    pari = povezi_zamenjave(stare, nove)
    for stari, (novi, postanki) in pari.items():
        conn.execute("DELETE FROM zamenjava WHERE stari_trip = ?", (stari,))
        conn.executemany(
            "INSERT INTO zamenjava(stari_trip, stari_seq, novi_trip, novi_seq,"
            "                      stari_arr_s, stari_dep_s) VALUES(?,?,?,?,?,?)",
            [(stari, s_seq, novi, n_seq, arr, dep) for s_seq, n_seq, arr, dep in postanki])
    return len(pari)


def zamenjave_iz(conn: sqlite3.Connection, stara: sqlite3.Connection) -> dict:
    """Poveže zamenjane vožnje iz starejše kopije baze.

    Za primer, ko je uvoz novega voznega reda že tekel, preden je to znal
    sam: stari vozni red je takrat samo še v varnostni kopiji.
    """
    od_dne = (datetime.now(TZ).date() - timedelta(days=1)).isoformat()
    stari_ids, novi_ids = _z_voznim_redom(stara), _z_voznim_redom(conn)
    stare = _vozje_za(stara, stari_ids - novi_ids, od_dne)
    nove = _vozje_za(conn, novi_ids - stari_ids, od_dne,
                     {v["kljuc"] for v in stare.values()})
    with conn:
        n = _zapisi_zamenjave(conn, stare, nove)
    return {"izginulih": len(stare), "novih": len(nove), "povezanih": n}


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

    imen_poenotenih = _poenoti_imena(stops)

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
        # Stari vozni red izginulih voženj je treba prebrati ZDAJ: spodnji
        # `DELETE` ga pobriše, in brez njega zamenjave ni mogoče sestaviti.
        od_dne = (datetime.now(TZ).date() - timedelta(days=1)).isoformat()
        stari_ids = _z_voznim_redom(conn)
        izginule = _vozje_za(conn, stari_ids - set(trips), od_dne)

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
        nove = _vozje_za(conn, set(trips) - stari_ids, od_dne,
                         {v["kljuc"] for v in izginule.values()}) if izginule else {}
        zamenjanih = _zapisi_zamenjave(conn, izginule, nove)
        # S pasom, tako kot vse drugo v projektu: brez njega je to cas stroja,
        # ki se od `config.TIMEZONE` lahko razlikuje.
        db.set_meta(conn, "gtfs_imported_at",
                    datetime.now(TZ).isoformat(timespec="seconds"))

    return {
        "stations": len(stops), "edges": len(edges),
        # Koliko voznj je prezivelo uvoz samo zato, ker imajo meritve. Ce je
        # to veliko, se je vozni red mocno premesal in je vredno pogledati.
        "trips_obdrzanih": vrnjenih,
        # Koliko izginulih voznj ima naslednico pod novim id-jem. Feed v zivo
        # jih zna se naprej nositi pod starim; zajem ju poveze sam.
        "trips_zamenjanih": zamenjanih,
        "trips": len(trips), "trips_rail": len(rail_trips),
        "trips_bus": len(trips) - len(rail_trips),
        "trips_lpp": lpp_trips,
        # Koliko postajalisc je dobilo drugo ime, ker je isto mesto v feedih
        # zapisano dvakrat. Ce je to veliko, se je nekaj spremenilo pri viru.
        "imen_poenotenih": imen_poenotenih,
        "stop_times": len(sched_rows), "service_days": sum(len(d) for d in days.values()),
        "trips_blocked": sum(1 for t in trips.values() if t.get("block_id")),
    }
