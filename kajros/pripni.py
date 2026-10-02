"""Trase GTFS, pripete na ceste in tire OpenStreetMap.

Podlaga zemljevida je OSM, trase so iz GTFS -- dva vira, ki se ne ujemata.
Izmerjeno 2. 10. 2026 proti OSM (`docs/MERITVE.md`, „Zemljevid od blizu“):
trase IJPP so od osi ceste v mediani 3,5 m, razpršene na obe strani; proge
SŽ v mediani 2,2 m, a 28 km jih je več kot 25 m stran od tira. Od blizu,
ko je cesta široka 30 px, je to trasa ob cesti, ne na njej.

Zato traso vsake vožnje enkrat pripnemo na OSM z lastnim OSRM (`/match`,
profila `deploy/osrm/avtobus.lua` in `tir.lua`). Pripeta je v `shape.osm`,
surova ostane v `shape.points`. Pripeto berejo prikaz in `deljenje.trasa()`
(okno vožnje drsi po njej, vlak na postaji stoji na njej) -- slika in
številka o istem vozilu se ne smeta razhajati.

**Kar se ne ujema, ostane surovo.** Pripenjanje lahko zgreši (vzporedna
cesta, obvoz, ki ga OSM ne pozna). Vsak pripet kos primerjamo s surovim; če
se kjerkoli razideta za več kot `MEJA_M`, ostane surovi kos. Tako pripenjanje
trase nikoli ne odpelje drugam, kot jo je narisal prevoznik.

Rezultat se hrani po **vsebini** (`pripeto`, ključ = surove točke + profil +
`RAZLICICA`), ne po `shape_id`: uvoz tabelo `shape` vsak dan zamenja, id-ji
se med voznimi redi ponovno uporabijo, točke pa ostanejo večinoma iste. Prvi
prehod čez vse trase je nekaj minut, vsak naslednji nekaj sekund.
"""
from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import time
from urllib.parse import quote

import requests

from . import config, geo

#: Povečaj, kadar se spremeni postopek: vse trase se pripnejo znova.
RAZLICICA = 1

#: Kos, ki se od surove trase kjerkoli oddalji za več, ostane surov. Surove
#: trase so od OSM v p99 15 m (IJPP) oziroma 7,5 m (SŽ v Ljubljani); 35 m je
#: dovolj nad tem, da jih ne zavrnemo zaradi šuma, in pod razmikom do
#: vzporedne ulice, da napačno pot ujamemo.
MEJA_M = {"avtobus": 35.0, "tir": 40.0}

#: Standardni odklon točke za OSRM (`radiuses`). Poenostavljena trasa je od
#: osi do 15 m stran, kandidati se iščejo v nekajkratniku tega.
POLMER_M = {"avtobus": 15, "tir": 20}

#: Toliko točk na zahtevo; daljši kos se razreže. OSRM mora imeti
#: `--max-matching-size` vsaj toliko (`deploy/osrm.sh`).
NAJVEC_TOCK = 2000

#: Pripeta trasa je gosta (vsako oglišče ceste); poenostavimo jo na ~2 m.
#: Izmerjeno na vseh 2 957 trasah (2. 10. 2026): brez poenostavitve 35,7 MB,
#: od OSM v mediani 0,3 m; pri 2e-5 25,4 MB in 0,4 m (p90 1,0 m); pri 3e-5
#: 20,5 MB, a p90 1,6 m. Surove so bile 10,9 MB in 3,1 m.
POENOSTAVI = 2e-5

#: Zapis v predpomnilniku, ki ga 30 dni ni rabila nobena trasa, gre.
HRANI_S = 30 * 86400


def _naslov(profil: str) -> str:
    return {"avtobus": config.OSRM_AVTOBUS_URL, "tir": config.OSRM_TIR_URL}[profil]


def polyline(tocke) -> str:
    """Googlov zapis polilinije s petimi decimalkami -- OSRM ga sprejme
    v naslovu kot `polyline(...)` in je ~4-krat krajši od števil."""
    out, plat, plon = [], 0, 0
    for lat, lon in tocke:
        ilat, ilon = round(lat * 1e5), round(lon * 1e5)
        for d in (ilat - plat, ilon - plon):
            d = ~(d << 1) if d < 0 else d << 1
            while d >= 0x20:
                out.append(chr((0x20 | (d & 0x1F)) + 63))
                d >>= 5
            out.append(chr(d + 63))
        plat, plon = ilat, ilon
    return "".join(out)


def _zahtevaj(naslov: str, tocke, polmer: int) -> dict | None:
    """En klic `/match`. None, kadar OSRM ne odgovori ali poti ne najde."""
    url = (f"{naslov}/match/v1/x/polyline({quote(polyline(tocke), safe='')})"
           f"?overview=full&geometries=geojson&gaps=ignore&annotations=distance"
           f"&radiuses={';'.join([str(polmer)] * len(tocke))}")
    r = requests.get(url, timeout=30, headers={"User-Agent": config.USER_AGENT})
    if r.status_code != 200:
        return None
    odg = r.json()
    return odg if odg.get("code") == "Ok" else None


def dlje_od(tocke, crta, meja: float) -> bool:
    """Ali je katera od `tocke` od polilinije `crta` dlje kot `meja` metrov?

    Odseke črte razvrstimo v mrežo s celico `meja`, zato vsaka točka
    pregleda le sosednje celice -- pripeta trasa ima tisoč oglišč in več,
    vsaka z vsakim bi bil prvi prehod čez vse trase četrt ure.
    """
    lat0 = crta[0][0]
    kx = geo.EARTH_R * math.pi / 180 * math.cos(math.radians(lat0))
    ky = geo.EARTH_R * math.pi / 180
    c = [(p[1] * kx, p[0] * ky) for p in crta]
    if len(c) == 1:
        c = c * 2
    mreza: dict[tuple[int, int], list] = {}
    for (ax, ay), (bx, by) in zip(c, c[1:]):
        for gx in range(int(min(ax, bx) // meja), int(max(ax, bx) // meja) + 1):
            for gy in range(int(min(ay, by) // meja), int(max(ay, by) // meja) + 1):
                mreza.setdefault((gx, gy), []).append((ax, ay, bx, by))
    m2 = meja * meja
    for p in tocke:
        px, py = p[1] * kx, p[0] * ky
        gx, gy = int(px // meja), int(py // meja)
        blizu = False
        for i in (gx - 1, gx, gx + 1):
            for j in (gy - 1, gy, gy + 1):
                for ax, ay, bx, by in mreza.get((i, j), ()):
                    vx, vy = bx - ax, by - ay
                    l2 = vx * vx + vy * vy
                    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / l2))
                    dx, dy = ax + t * vx - px, ay + t * vy - py
                    if dx * dx + dy * dy <= m2:
                        blizu = True
                        break
                if blizu:
                    break
            if blizu:
                break
        if not blizu:
            return True
    return False


def _odseki(matching: dict) -> list[list]:
    """Geometrija matchinga, razrezana na odseke med zaporednima točkama.

    `annotation.distance` ima po en element na odsek geometrije; odsek k
    obsega toliko daljic, kolikor ima njegov seznam, in si s sosedom deli
    robno oglišče.
    """
    g = [(lat, lon) for lon, lat in matching["geometry"]["coordinates"]]
    out, od = [], 0
    for leg in matching.get("legs") or []:
        n = len((leg.get("annotation") or {}).get("distance") or [])
        out.append(g[od:od + n + 1])
        od += n
    return out


def zlepi(kos: list, odgovor: dict | None, meja: float) -> tuple[list, float]:
    """Iz odgovora `/match` sestavi traso in vrne (točke, pripeti delež).

    OSRM vrne več „matchingov“, kadar sledi ne zna povezati, in točke, ki
    jih ni mogel pripeti (`null`). Vsak matching je zaporedje odsekov med
    zaporednima točkama surove trase. **Presojamo odsek po odsek**: kjer se
    pripeti od surovega oddalji za več kot `meja`, ostane surovi odsek. Prej
    je bil enota cel matching in en sam zgrešen konec (končno postajališče
    na dvorišču, ki ga OSM nima) je zavrnil traso čez pol Slovenije -- tako
    je ostalo surovih 994 od 2 667 avtobusnih tras.
    """
    if not odgovor or len(kos) < 2:
        return list(kos), 0.0
    po_matchingu: dict[int, list[tuple[int, int]]] = {}
    for i, tp in enumerate(odgovor.get("tracepoints") or []):
        if tp is not None:
            po_matchingu.setdefault(tp["matchings_index"], []).append((tp["waypoint_index"], i))
    out: list = []
    pripeto_m = 0.0
    naprej = 0                           # prva točka kosa, ki še ni v `out`
    for m in sorted(po_matchingu, key=lambda k: min(i for _, i in po_matchingu[k])):
        indeksi = [i for _, i in sorted(po_matchingu[m])]
        if indeksi[0] < naprej or len(indeksi) < 2:
            continue
        odseki = _odseki(odgovor["matchings"][m])
        if len(odseki) != len(indeksi) - 1:
            continue                     # odgovor ni, kakršnega pričakujemo
        out.extend(kos[naprej:indeksi[0]])
        for crta, i, j in zip(odseki, indeksi, indeksi[1:]):
            surovo = kos[i:j + 1]
            if (len(crta) >= 2
                    and not dlje_od(crta, surovo, meja)
                    and not dlje_od(surovo, crta, meja)):
                novo = crta
                pripeto_m += sum(geo.haversine(a[0], a[1], b[0], b[1])
                                 for a, b in zip(crta, crta[1:]))
            else:
                novo = surovo
            # Sosednja odseka si delita robno točko.
            out.extend(novo[1:] if out and tuple(out[-1]) == tuple(novo[0]) else novo)
        naprej = indeksi[-1] + 1
    out.extend(kos[naprej:])
    vse_m = sum(geo.haversine(a[0], a[1], b[0], b[1]) for a, b in zip(out, out[1:]))
    return out, (min(1.0, pripeto_m / vse_m) if vse_m else 0.0)


def pripni_kos(naslov: str, profil: str, kos: list) -> tuple[list, float]:
    """En nepretrgan kos trase; daljšega od `NAJVEC_TOCK` po delih, ki si
    delijo robno točko."""
    if len(kos) < 2:
        return list(kos), 0.0
    deli, utezi = [], []
    zacetek = 0
    while zacetek < len(kos) - 1:
        konec = min(len(kos), zacetek + NAJVEC_TOCK)
        del_ = kos[zacetek:konec]
        tocke, delez = zlepi(del_, _zahtevaj(naslov, del_, POLMER_M[profil]), MEJA_M[profil])
        if deli and tocke:
            tocke = tocke[1:]            # robna točka je že v prejšnjem delu
        deli.extend(tocke)
        dolzina = sum(geo.haversine(a[0], a[1], b[0], b[1]) for a, b in zip(del_, del_[1:]))
        utezi.append((delez, dolzina))
        zacetek = konec - 1
    vse = sum(d for _, d in utezi)
    delez = sum(p * d for p, d in utezi) / vse if vse else 0.0
    gosto = geo.simplify(deli, POENOSTAVI)
    return [[round(a, 5), round(b, 5)] for a, b in gosto], delez


def _kljuc(profil: str, tocke_json: str) -> str:
    return hashlib.sha1(f"{RAZLICICA}|{profil}|{tocke_json}".encode()).hexdigest()


def _dosegljiv(naslov: str) -> bool:
    if not naslov:
        return False
    try:
        r = requests.get(f"{naslov}/nearest/v1/x/14.5058,46.0569", timeout=3)
        return r.status_code == 200 and r.json().get("code") == "Ok"
    except (requests.RequestException, ValueError):
        return False


def _iz_predpomnilnika(conn, kljuc: str, zdaj: int) -> str | None:
    row = conn.execute("SELECT tocke FROM pripeto WHERE kljuc = ?", (kljuc,)).fetchone()
    if row:
        conn.execute("UPDATE pripeto SET ts = ? WHERE kljuc = ?", (zdaj, kljuc))
        return row[0]
    return None


def po_cesti(naslov: str, postaje: list) -> list | None:
    """Pot po cesti skozi postaje (`/route`), ali None."""
    if len(postaje) < 2:
        return None
    url = (f"{naslov}/route/v1/x/polyline({quote(polyline(postaje), safe='')})"
           f"?overview=full&geometries=geojson")
    r = requests.get(url, timeout=30, headers={"User-Agent": config.USER_AGENT})
    if r.status_code != 200 or r.json().get("code") != "Ok":
        return None
    crta = [(lat, lon) for lon, lat in r.json()["routes"][0]["geometry"]["coordinates"]]
    return [[round(a, 5), round(b, 5)] for a, b in geo.simplify(crta, POENOSTAVI)]


#: Nadomestni prevoz, katerega trasa se na ceste ne pripne niti do polovice,
#: dobi pot po cesti skozi svoje postaje. GTFS mu kot traso pogosto da progo,
#: ki jo zamenjuje: izmerjeno v Ljubljani, 25,7 m od najbližje ceste v
#: mediani -- avtobus po tirih.
NADOMESTNI_PRAG = 0.5


def _pripni_kose(conn, naslov: str, profil: str, kosi: list, kljuc: str,
                 zdaj: int, postaje: list | None = None) -> tuple[str, float | None]:
    """(JSON kosov, delež) iz predpomnilnika ali OSRM. Delež None = iz
    predpomnilnika (izračunan že prej).

    `postaje`: samo za nadomestni prevoz -- glej `NADOMESTNI_PRAG`.
    """
    shranjeno = _iz_predpomnilnika(conn, kljuc, zdaj)
    if shranjeno is not None:
        return shranjeno, None
    novi, pripeto, vse = [], 0.0, 0.0
    for kos in kosi:
        tocke, delez = pripni_kos(naslov, profil, kos)
        dolzina = sum(geo.haversine(a[0], a[1], b[0], b[1]) for a, b in zip(kos, kos[1:]))
        novi.append(tocke)
        pripeto += delez * dolzina
        vse += dolzina
    delez = pripeto / vse if vse else 0.0
    if postaje and delez < NADOMESTNI_PRAG:
        cesta = po_cesti(naslov, postaje)
        if cesta:
            novi, delez = [cesta], 1.0
    tocke_json = json.dumps(novi, separators=(",", ":"))
    conn.execute("INSERT OR REPLACE INTO pripeto(kljuc, tocke, delez, ts) VALUES(?,?,?,?)",
                 (kljuc, tocke_json, delez, zdaj))
    return tocke_json, delez


def pripni(conn: sqlite3.Connection, log=print) -> dict:
    """Pripne vse trase in odseke mreže, ki še niso pripeti.

    Kliče se po vsakem uvozu voznega reda in ob zagonu strežnika. Kar je v
    predpomnilniku, se samo prepiše; OSRM se vpraša samo za nove trase. Brez
    dosegljivega OSRM ne naredi nič -- prikaz takrat riše surove trase.
    """
    from . import db
    if db.get_meta(conn, "pripni_razlicica") != str(RAZLICICA):
        conn.execute("UPDATE shape SET osm = NULL")
        conn.execute("UPDATE edge SET osm = NULL")
        db.set_meta(conn, "pripni_razlicica", str(RAZLICICA))
        conn.commit()

    naslovi = {p: _naslov(p) for p in ("avtobus", "tir")}
    dosegljivi = {p: _dosegljiv(u) for p, u in naslovi.items()}
    izid = {"trase": 0, "odseki": 0, "novih": 0, "delez": [], "osrm": dosegljivi}
    if not any(dosegljivi.values()):
        return izid

    zdaj = int(time.time())
    t0 = time.monotonic()
    delo = conn.execute(
        "SELECT sh.shape_id, sh.points, t.mode, t.agency, t.trip_id "
        "FROM shape sh JOIN trip t ON t.trip_id = "
        "     (SELECT trip_id FROM trip WHERE shape_id = sh.shape_id LIMIT 1) "
        "WHERE sh.osm IS NULL").fetchall()
    for i, (shape_id, points, mode, agency, trip_id) in enumerate(delo):
        profil = "tir" if mode == "vlak" else "avtobus"
        if not dosegljivi[profil]:
            continue
        kosi = json.loads(points)
        postaje = None
        kljuc = _kljuc(profil, points)
        if mode == "bus" and agency == config.RAIL_AGENCY_ID:
            postaje = [[r[0], r[1]] for r in conn.execute(
                "SELECT st.lat, st.lon FROM sched s JOIN station st ON st.stop_id = s.stop_id "
                "WHERE s.trip_id = ? ORDER BY s.stop_seq", (trip_id,))]
            kljuc = _kljuc("nadomestni", points + json.dumps(postaje))
        tocke_json, delez = _pripni_kose(conn, naslovi[profil], profil, kosi,
                                         kljuc, zdaj, postaje)
        conn.execute("UPDATE shape SET osm = ? WHERE shape_id = ?", (tocke_json, shape_id))
        izid["trase"] += 1
        if delez is not None:
            izid["novih"] += 1
            izid["delez"].append(delez)
        if i % 50 == 49:
            conn.commit()                  # zajem piše vzporedno; ne držimo ga
    conn.commit()

    if dosegljivi["tir"]:
        for from_id, to_id, gj in conn.execute(
                "SELECT from_id, to_id, geojson FROM edge WHERE osm IS NULL").fetchall():
            kos = [[lat, lon] for lon, lat in json.loads(gj)["coordinates"]]
            tocke_json, delez = _pripni_kose(conn, naslovi["tir"], "tir", [kos],
                                             _kljuc("tir", json.dumps(kos)), zdaj)
            kosi = json.loads(tocke_json)
            geom = ({"type": "LineString", "coordinates": [[b, a] for a, b in kosi[0]]}
                    if len(kosi) == 1 else
                    {"type": "MultiLineString",
                     "coordinates": [[[b, a] for a, b in k] for k in kosi]})
            conn.execute("UPDATE edge SET osm = ? WHERE from_id = ? AND to_id = ?",
                         (json.dumps(geom, separators=(",", ":")), from_id, to_id))
            izid["odseki"] += 1
            if delez is not None:
                izid["novih"] += 1
        conn.commit()

    conn.execute("DELETE FROM pripeto WHERE ts < ?", (zdaj - HRANI_S,))
    if izid["trase"] or izid["odseki"]:
        # Predpomnilnik mreže prog v `api.py` je vezan na to značko.
        db.set_meta(conn, "pripeto_at", str(zdaj))
    conn.commit()
    d = sorted(izid.pop("delez"))
    if d:
        izid["delez_mediana"] = round(d[len(d) // 2], 3)
        izid["v_celoti"] = sum(1 for x in d if x > 0.99)
    izid["s"] = round(time.monotonic() - t0, 1)
    if izid["trase"] or izid["odseki"]:
        log(f"pripenjanje tras na OSM: {izid}")
    return izid


# ------------------------------------------------------------ lega na cesti

#: Lega GPS, ki je od pripete trase svoje vožnje bližje od tega, se nariše na
#: traso. Izmerjeno 2. 10. 2026 v Ljubljani (552 leg vozil, ki so se med
#: branjema premaknila): 15 m pripne 69,6 %, premik v mediani 4,2 m (p90
#: 9,5 m); 25 m bi dodalo 1,5 točke in tveganje sosednje ulice. Ostalih
#: ~30 % so vožnje, ki se še niso začele (vozilo že nosi naslednjo vožnjo in
#: pelje drugam) -- te ostanejo na legi GPS.
NA_CESTO_M = 15.0

#: Vozilo, ki pelje drugače kot trasa, ni na njej, tudi če je blizu (ista
#: cesta, nasprotna smer: 28 od 552 leg).
NA_CESTO_KOT = 60.0

#: Pripeta trasa je os ceste, avtobus pa vozi po desnem pasu. Izmerjen odmik
#: GPS od pripete trase, desno od smeri vožnje: mediana 1,9 m (p25 −2,6 m,
#: p75 5,2 m). Brez tega bi se avtobusa v nasprotnih smereh narisala drug
#: na drugega.
DESNO_M = 1.9


def na_cesto(trasa, lat: float, lon: float, smer_gps: float | None) -> list | None:
    """[lat, lon, smer] na pripeti trasi (`deljenje.Trasa`) ali None.

    Samo za prikaz: meritev ostane v `lat`/`lon` vrstice, to je risba.
    """
    along, odmik = trasa.projiciraj(lat, lon, najvec_m=NA_CESTO_M)
    if odmik > NA_CESTO_M:
        return None
    smer = trasa.smer(along, 15)
    if smer is None:
        return None
    if smer_gps is not None:
        razlika = abs((smer_gps - smer + 180) % 360 - 180)
        if razlika > NA_CESTO_KOT:
            return None
    t_lat, t_lon = trasa.tocka(along)
    s = math.radians(smer)
    m_na_stopinjo = geo.EARTH_R * math.pi / 180
    t_lat += -math.sin(s) * DESNO_M / m_na_stopinjo
    t_lon += math.cos(s) * DESNO_M / (m_na_stopinjo * math.cos(math.radians(t_lat)))
    return [round(t_lat, 6), round(t_lon, 6), smer]
