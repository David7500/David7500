"""Dosje vozila: vse, kar viri o vozilu povedo, in kaj smo iz tega naredili.

David, 1. 11. 2026: „Za vsa vozila, s katerimi je kaj narobe, morava shranjevati
vse, da bova vedela, kaj je z njimi. Na koncu morava čisto za vsako vozilo
vedeti vse.“

Do zdaj se je diagnoza vozila sestavljala iz ostankov: `lega` ima samo pripeta
vozila, `vehicle_now` zadnje stanje, `meta.nap.nepripeti` prvih 15, surovega
odgovora vira ni hranil nihče. Ko je vozilo prižgalo opozorilo, je bilo za
vprašanje „kaj je NAP o njem rekel ob 13.05“ že prepozno.

**Hrani se vsak vzorec vsakega vozila iz vsakega vira, ne samo „slabih“.** Kaj je
narobe, se pogosto izkaže šele pozneje, in vnaprejšnje sito izgubi ravno tisto,
kar bi iskali. `razlogi` so oznaka v dnevniku, ne pogoj za shranjevanje. Izjema
je `zamude`: surova napoved vira je velika, zato samo za vozila z razlogom.

Tabele, svoja baza `config.DOSJE_DB` kot `promet.sqlite` (brez varnostne kopije;
`meta.dosje` v glavni bazi samo za /admin):

* `tocke`: vzorci po vozilu in viru v stisnjenih kosih (`KOS_S`); en vzorec je
  `[ts, lat, lon, sprotno]`, `sprotno` = kar se pri viru spreminja sproti.
* `stanje`: dnevnik sprememb vozila po viru: vožnja, dan, razlogi, telo.
* `telo`: kar je vir povedal o vozilu in se sproti ne spreminja (id-ji, linija,
  smer ...), po vsebini: vsaka različica enkrat.
* `zamude`: surov TripUpdate vira za vozila z razlogom, največ na `ZAMUDE_VSAKIH_S`.
* `vozilo_dan`: vzorci po dnevu, viru, vozilu in razlogu ('' = vsi). Ne obrezuje se.
* `oznaka`: tablica ali številka vozila -> id, za iskanje.

Razlogi. Vir pove, kar ve sam; drugo je isti račun za vse:

* `stara_lega`, `ura_naprej`, `miruje`: `_opazi`, za vse vire.
* `brez_lege`, `brez_voznje`, `brez_dneva`, `prezgodaj`, `pred_odhodom`,
  `po_koncu`, `brez_id`, `ura_popravljena`, `ni_avtobus`, `vira_razlicna`,
  `drugo_vozilo_vodi`: pripenjanje NAP in derp.si (`nap.py`, `collector.py`).
* `ni_ziva`, `brez_linije` in vzrok `razresi` (`ni_prihoda` ...): `marprom.py`.
* `nepripet`, `odhod_v_prihodnosti`: `zamude_sz.py`; vlak je „vlak-<številka>“.
* `brez_zamude` (`collector.lega_brez_zamude`), `zamuda_raste`
  (`collector.ura_namesto_zamude`): `oznaci`, velja `OZNAKA_S`.

Zajem nikoli ne čaka na dosje: `opazi` le doda v pomnilnik, piše `teci` v svoji
niti in svoji bazi, napaka tu ne sme doseči vira. Brez `vklopi` (malina, preizkusi,
ukazna vrstica) je vse skupaj prazen klic, sicer bi medpomnilnik rasel brez bralca.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time
import zlib
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable
from zoneinfo import ZoneInfo

from google.protobuf import json_format, text_format
from google.transit import gtfs_realtime_pb2

from . import config, db, geo, straza

TZ = ZoneInfo(config.TIMEZONE)

SHEMA = """
CREATE TABLE IF NOT EXISTS tocke (
    vozilo   TEXT NOT NULL,
    vir      TEXT NOT NULL,
    od_ts    INTEGER NOT NULL,      -- naša ura ob prvem vzorcu kosa
    do_ts    INTEGER NOT NULL,
    n        INTEGER NOT NULL,
    vsebina  BLOB NOT NULL,         -- zlib, JSON [[ts, lat, lon, sprotno], ...]
    PRIMARY KEY (vozilo, vir, od_ts)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS tocke_do ON tocke(do_ts);
CREATE TABLE IF NOT EXISTS stanje (
    vozilo   TEXT NOT NULL,
    vir      TEXT NOT NULL,
    ts       INTEGER NOT NULL,      -- naša ura
    vir_ts   INTEGER,               -- ura vzorca po viru
    trip_id  TEXT,                  -- naša vožnja; NULL = ne pripnemo
    dan      TEXT,                  -- obratovalni dan vožnje
    razlogi  TEXT NOT NULL,         -- po abecedi, z vejico; '' = nič narobe
    telo     BLOB,                  -- `telo.odtis`
    lat      REAL,
    lon      REAL,
    sprotno  TEXT,
    PRIMARY KEY (vozilo, vir, ts)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS telo (
    odtis    BLOB PRIMARY KEY,
    vsebina  BLOB NOT NULL          -- zlib, JSON
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS zamude (
    vozilo   TEXT NOT NULL,
    vir      TEXT NOT NULL,
    ts       INTEGER NOT NULL,
    trip_id  TEXT,                  -- id iz feeda
    vsebina  BLOB NOT NULL,         -- zlib, TripUpdate
    PRIMARY KEY (vozilo, vir, ts)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS vozilo_dan (
    dan      TEXT NOT NULL,         -- prometni dan od 3:00 (`straza._dan`)
    vir      TEXT NOT NULL,
    vozilo   TEXT NOT NULL,
    razlog   TEXT NOT NULL,         -- '' = vsi vzorci
    vzorcev  INTEGER NOT NULL,
    prvic    INTEGER NOT NULL,
    nazadnje INTEGER NOT NULL,
    PRIMARY KEY (dan, vir, vozilo, razlog)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS vozilo_dan_vozilo ON vozilo_dan(vozilo, dan);
CREATE TABLE IF NOT EXISTS oznaka (
    oznaka   TEXT NOT NULL,
    vozilo   TEXT NOT NULL,
    vir      TEXT NOT NULL,
    prvic    INTEGER NOT NULL,
    PRIMARY KEY (oznaka, vozilo, vir)
) WITHOUT ROWID;
"""

#: En kos točk zajame toliko časa. Daljši kos se bolje stisne, ob padcu procesa
#: pa je toliko izgubljenega (ob ustavitvi `teci` izprazni vse).
KOS_S = 300
IZPRAZNI_S = 60
#: Varovalo: nit, ki stoji, ne sme pojesti pomnilnika. Vozilo na 5 s da v kosu
#: 60 vzorcev.
NAJVEC_TOCK = 500
#: = `collector.POSITION_FRESH_S` (uvoz sem bi bil krog; preizkus ju drži skupaj).
STARA_LEGA_S = 180
URA_NAPREJ_S = 60
#: Vozilo na vožnji, ki se toliko časa ne premakne za več od `MIRUJE_M`. Samo
#: oznaka: čakanje na končni in zastoj sta tudi to.
MIRUJE_S, MIRUJE_M = 900, 50
#: Oznaka iz preverjanja (`oznaci`) drži toliko; preverjanje teče na 30 s.
OZNAKA_S = 120
#: Surov TripUpdate je do nekaj kB na vožnjo: na vozilo največ tako pogosto.
ZAMUDE_VSAKIH_S = 300
#: Vozilo, ki ga toliko časa ni, gre iz pomnilnika.
POZABI_S = 86400
#: Koliko dni. `stanje`, `telo`, `vozilo_dan` in `oznaka` se ne obrezujejo:
#: skupaj nekaj MB na dan, in zgodovine vozil nima nihče drug.
TOCKE_DNI, ZAMUDE_DNI = 365, 35


class _Vozilo:
    """Kaj si o vozilu zapomnimo med vzorci, po viru."""
    __slots__ = ("stanje", "odtis", "tocke", "kos_od", "zadnja", "videno", "sidro", "sidro_ts")

    def __init__(self) -> None:
        self.stanje: tuple | None = None
        self.odtis: bytes | None = None
        self.tocke: list[list] = []
        self.kos_od = 0
        self.zadnja: tuple | None = None
        self.videno = 0.0
        self.sidro: tuple | None = None
        self.sidro_ts = 0.0


_vklopljen = [False]
_zaklep = threading.Lock()
_vozila: dict[tuple[str, str], _Vozilo] = {}
_stanja: list[tuple] = []
_telesa: dict[bytes, bytes] = {}
_znana_telesa: set[bytes] = set()
_zamude: list[tuple] = []
_zamude_ts: dict[tuple[str, str], float] = {}
_dnevi: dict[tuple[str, str, str, str], list[int]] = {}
_oznake: dict[str, dict[str, float]] = {}
_narobe: dict[str, float] = {}
_nove_oznake: list[tuple] = []
_znane_oznake: set[tuple] = set()
_stevci: dict = defaultdict(int)


def vklopi() -> None:
    _vklopljen[0] = True


def vklopljen() -> bool:
    return _vklopljen[0]


def pocisti() -> None:
    """Izklopi in pozabi vse (ustavitev, preizkusi)."""
    _vklopljen[0] = False
    with _zaklep:
        for x in (_vozila, _stanja, _telesa, _znana_telesa, _zamude, _zamude_ts, _dnevi,
                  _oznake, _narobe, _nove_oznake, _znane_oznake, _stevci):
            x.clear()


def _napaka(exc: Exception) -> None:
    _stevci["napak"] += 1
    _stevci["napaka"] = f"{type(exc).__name__}: {exc}"[:200]


def varno(fn: Callable, *args) -> None:
    """Zapis v dosje iz niti vira: napaka ne sme doseči vira."""
    try:
        fn(*args)
    except Exception as exc:                # noqa: BLE001 -- dosje ne sme ustaviti zajema
        _napaka(exc)


def _shrani_telo(telo: object) -> bytes | None:
    """Telo po vsebini: isti odziv vira čez dneve je ena vrstica."""
    if telo is None:
        return None
    besedilo = json.dumps(telo, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    odtis = hashlib.sha1(besedilo.encode()).digest()[:10]
    if odtis not in _znana_telesa:
        _znana_telesa.add(odtis)
        _telesa[odtis] = zlib.compress(besedilo.encode(), 6)
    return odtis


def _miruje(s: _Vozilo, trip_id: str | None, lat: float | None, lon: float | None,
            zdaj: float) -> bool:
    if lat is None or lon is None or not trip_id:
        s.sidro = None
        return False
    if s.sidro is None or geo.haversine(*s.sidro, lat, lon) > MIRUJE_M:
        s.sidro, s.sidro_ts = (lat, lon), zdaj
        return False
    return zdaj - s.sidro_ts >= MIRUJE_S


def _opazi(vir: str, vozilo: str, ts, lat, lon, trip_id, dan, razlogi, kljuc, telo, sprotno,
           oznaka, zdaj: float) -> None:
    k = (vir, vozilo)
    s = _vozila.get(k)
    if s is None:
        s = _vozila[k] = _Vozilo()
    s.videno = zdaj
    if lat is not None and lon is not None:
        lat, lon = round(lat, 6), round(lon, 6)
    r = set(razlogi)
    if ts is not None:
        if zdaj - ts > STARA_LEGA_S:
            r.add("stara_lega")
        elif ts - zdaj > URA_NAPREJ_S:
            r.add("ura_naprej")
    if _miruje(s, trip_id, lat, lon, zdaj):
        r.add("miruje")
    oz = _oznake.get(vozilo)
    if oz:
        for ime in [x for x, do in oz.items() if do < zdaj]:
            del oz[ime]
        r.update(oz)
    if r:
        _narobe[vozilo] = zdaj
    cas = int(zdaj)
    dan_p = straza._dan(zdaj)
    for ime in ("", *r):
        d = _dnevi.get((dan_p, vir, vozilo, ime))
        if d is None:
            _dnevi[(dan_p, vir, vozilo, ime)] = [1, cas, cas]
        else:
            d[0] += 1
            d[2] = cas
    if oznaka and (oznaka, vozilo, vir) not in _znane_oznake:
        _znane_oznake.add((oznaka, vozilo, vir))
        _nove_oznake.append((oznaka, vozilo, vir, cas))
    _stevci["vzorcev"] += 1

    razlog = ",".join(sorted(r))
    novo = (trip_id, dan, razlog, kljuc)
    sp = None
    izracunano = False
    if novo != s.stanje:
        if s.stanje is None or s.stanje[3] != kljuc:
            s.odtis = _shrani_telo(telo() if callable(telo) else telo)
        sp = sprotno() if callable(sprotno) else sprotno
        izracunano = True
        _stanja.append((vozilo, vir, cas, int(ts) if ts is not None else None, trip_id, dan,
                        razlog, s.odtis, lat, lon,
                        json.dumps(sp, ensure_ascii=False, separators=(",", ":"))
                        if sp is not None else None))
        s.stanje = novo

    # Isti vzorec, ki ga vir ponovi, ni nova informacija. Vir brez svoje ure
    # (zemljevid SŽ): ponovitev je ista lega in isto sprotno.
    if not izracunano:
        sp = sprotno() if callable(sprotno) else sprotno
    tocka = (ts, lat, lon) if ts is not None else (lat, lon, json.dumps(sp, sort_keys=True))
    if tocka == s.zadnja:
        return
    s.zadnja = tocka
    if lat is None and sp is None:
        return
    if len(s.tocke) >= NAJVEC_TOCK:
        _stevci["izgubljenih"] += 1
        return
    if not s.tocke:
        s.kos_od = cas
    s.tocke.append([int(ts) if ts is not None else cas, lat, lon, sp])


def opazi(vir: str, vozilo: str | None, ts: float | None = None, lat: float | None = None,
          lon: float | None = None, *, trip_id: str | None = None, dan: str | None = None,
          razlogi: Iterable[str] = (), kljuc: object = None,
          telo: object = None, sprotno: object = None, oznaka: str | None = None,
          zdaj: float | None = None) -> None:
    """En vzorec vozila. `kljuc` = kar se sproti ne spreminja: ko se spremeni, se
    izračuna `telo` (lahko funkcija, da se pri nespremenjenem ne plača). `sprotno`
    je lahko funkcija. `trip_id` in `dan` = naša vožnja, None = ne pripnemo."""
    if not _vklopljen[0] or not vozilo:
        return
    try:
        with _zaklep:
            _opazi(vir, str(vozilo), ts, lat, lon, trip_id, dan, razlogi, kljuc, telo, sprotno,
                   oznaka, time.time() if zdaj is None else zdaj)
    except Exception as exc:                # noqa: BLE001 -- dosje ne sme ustaviti zajema
        _napaka(exc)


def _gtfs_telo(vp) -> dict:
    d = json_format.MessageToDict(vp, preserving_proto_field_name=True)
    for polje in ("position", "timestamp", "current_status", "current_stop_sequence",
                  "stop_id", "congestion_level", "occupancy_status", "occupancy_percentage"):
        d.pop(polje, None)
    return d


def _gtfs_sprotno(vp) -> dict | None:
    p = vp.position
    d = {k: v for k, v in (
        ("smer", p.bearing if p.HasField("bearing") else None),
        ("hitrost", round(p.speed, 2) if p.HasField("speed") else None),
        ("km", p.odometer if p.HasField("odometer") else None),
        ("seq", vp.current_stop_sequence or None),
        ("status", vp.current_status if vp.HasField("current_status") else None),
        ("postaja", vp.stop_id or None),
        ("gneca", vp.congestion_level or None),
        ("polnost", vp.occupancy_status if vp.HasField("occupancy_status") else None),
    ) if v is not None}
    return d or None


def opazi_gtfs(vir: str, vp, trip_id: str | None, dan: str | None, razlogi: Iterable[str] = (),
               vozilo: str | None = None, zdaj: float | None = None) -> None:
    """Vzorec iz GTFS-RT `VehiclePosition`. `trip_id` = naša vožnja."""
    if not _vklopljen[0]:
        return
    try:
        p = vp.position if vp.HasField("position") else None
        t = vp.trip
        opazi(vir, vozilo or vp.vehicle.id, vp.timestamp or None,
              p.latitude if p else None, p.longitude if p else None,
              trip_id=trip_id, dan=dan, razlogi=razlogi,
              kljuc=(t.trip_id, t.start_date, t.start_time, t.route_id, t.direction_id,
                     t.schedule_relationship, vp.vehicle.label, vp.vehicle.license_plate),
              telo=lambda: _gtfs_telo(vp), sprotno=lambda: _gtfs_sprotno(vp),
              oznaka=vp.vehicle.license_plate or vp.vehicle.label or None, zdaj=zdaj)
    except Exception as exc:                # noqa: BLE001 -- dosje ne sme ustaviti zajema
        _napaka(exc)


def oznaci(vozilo: str | None, razlog: str, zdaj: float | None = None) -> None:
    """Preverjanje mimo vira (brez zamude, zamuda raste): oznaka na vozilu v
    vseh virih, dokler jo preverjanje obnavlja."""
    if not _vklopljen[0] or not vozilo:
        return
    with _zaklep:
        _oznake.setdefault(str(vozilo), {})[razlog] = (
            time.time() if zdaj is None else zdaj) + OZNAKA_S


def zamude(vir: str, feed, zdaj: float | None = None) -> None:
    """Surova napoved vira za vozila z razlogom: pri medkrajevnih je v bazi ni
    (feed derp.si se izpusti, ko vodi NAP), a pove, kaj je derp.si o vozilu vedel."""
    if not _vklopljen[0] or feed is None:
        return
    zdaj = time.time() if zdaj is None else zdaj
    try:
        with _zaklep:
            for e in feed.entity:
                if not e.HasField("trip_update"):
                    continue
                vozilo = e.trip_update.vehicle.id
                if not vozilo or zdaj - _narobe.get(vozilo, 0) > OZNAKA_S:
                    continue
                if zdaj - _zamude_ts.get((vir, vozilo), 0) < ZAMUDE_VSAKIH_S:
                    continue
                _zamude_ts[(vir, vozilo)] = zdaj
                _zamude.append((vozilo, vir, int(zdaj), e.trip_update.trip.trip_id,
                                zlib.compress(e.trip_update.SerializeToString(), 6)))
    except Exception as exc:                # noqa: BLE001 -- dosje ne sme ustaviti zajema
        _napaka(exc)


# ---------------------------------------------------------------- pisanje

def povezi(path: Path | str | None = None) -> sqlite3.Connection:
    pot = Path(path or config.DOSJE_DB)
    # Bere tudi skrbnik (skupina, kot glavna baza). Pred prvo povezavo: `-wal` in
    # `-shm` ob nastanku dobita način baze.
    pot.touch()
    os.chmod(pot, 0o664)
    conn = db.connect(pot)
    conn.executescript(SHEMA)
    return conn


def _kos(tocke: list[list]) -> bytes:
    return zlib.compress(json.dumps(tocke, ensure_ascii=False, separators=(",", ":")).encode(), 6)


def izprazni(conn: sqlite3.Connection, zdaj: float | None = None, vse: bool = False) -> dict:
    """Medpomnilnik v bazo; kosi točk, ki so stari `KOS_S` (ali vsi ob `vse`).
    Račun in stiskanje zunaj zaklepa: viri ne čakajo."""
    zdaj = time.time() if zdaj is None else zdaj
    kosi = []
    with _zaklep:
        stanja, telesa, zamude_ = list(_stanja), list(_telesa.items()), list(_zamude)
        dnevi = [(*k, *v) for k, v in _dnevi.items()]
        oznake = list(_nove_oznake)
        for x in (_stanja, _telesa, _zamude, _dnevi, _nove_oznake):
            x.clear()
        for (vir, vozilo), s in list(_vozila.items()):
            if s.tocke and (vse or zdaj - s.kos_od >= KOS_S):
                kosi.append((vozilo, vir, s.kos_od, s.tocke))
                s.tocke = []
            elif not s.tocke and zdaj - s.videno > POZABI_S:
                del _vozila[(vir, vozilo)]
        for k in [k for k, ts in _narobe.items() if zdaj - ts > POZABI_S]:
            del _narobe[k]
        for k in [k for k, ts in _zamude_ts.items() if zdaj - ts > POZABI_S]:
            del _zamude_ts[k]
    vrstice = [(vozilo, vir, od, max(t[0] for t in tocke), len(tocke), _kos(tocke))
               for vozilo, vir, od, tocke in kosi]
    conn.executemany("INSERT OR IGNORE INTO telo(odtis, vsebina) VALUES(?,?)", telesa)
    conn.executemany("INSERT OR REPLACE INTO stanje(vozilo, vir, ts, vir_ts, trip_id, dan, razlogi,"
                     " telo, lat, lon, sprotno) VALUES(?,?,?,?,?,?,?,?,?,?,?)", stanja)
    conn.executemany("INSERT OR REPLACE INTO tocke(vozilo, vir, od_ts, do_ts, n, vsebina) "
                     "VALUES(?,?,?,?,?,?)", vrstice)
    conn.executemany("INSERT OR REPLACE INTO zamude(vozilo, vir, ts, trip_id, vsebina) "
                     "VALUES(?,?,?,?,?)", zamude_)
    conn.executemany(
        "INSERT INTO vozilo_dan(dan, vir, vozilo, razlog, vzorcev, prvic, nazadnje) "
        "VALUES(?,?,?,?,?,?,?) ON CONFLICT(dan, vir, vozilo, razlog) DO UPDATE SET "
        "vzorcev = vzorcev + excluded.vzorcev, nazadnje = excluded.nazadnje", dnevi)
    conn.executemany("INSERT OR IGNORE INTO oznaka(oznaka, vozilo, vir, prvic) VALUES(?,?,?,?)",
                     oznake)
    conn.commit()
    _stevci["kosov"] += len(vrstice)
    _stevci["stanj"] += len(stanja)
    _stevci["zamud"] += len(zamude_)
    return {"kosov": len(vrstice), "stanj": len(stanja), "zamud": len(zamude_)}


def obrezi(conn: sqlite3.Connection, zdaj: float | None = None) -> None:
    zdaj = time.time() if zdaj is None else zdaj
    conn.execute("DELETE FROM tocke WHERE do_ts < ?", (int(zdaj) - TOCKE_DNI * 86400,))
    conn.execute("DELETE FROM zamude WHERE ts < ?", (int(zdaj) - ZAMUDE_DNI * 86400,))
    conn.commit()


def _povzetek(glavna: sqlite3.Connection, zdaj: float) -> None:
    """Stanje v `meta` glavne baze za /admin in zdravje; čakanje na zaklep glavne
    baze (uvoz) tu ne moti nikogar."""
    with _zaklep:
        st = dict(_stevci)
        st["vozil"] = len(_vozila)
    try:
        st["bajtov"] = Path(config.DOSJE_DB).stat().st_size
    except OSError:
        pass
    st["ts"] = int(zdaj)
    try:
        db.set_meta(glavna, "dosje", json.dumps(st, sort_keys=True))
        glavna.commit()
    except sqlite3.Error:
        glavna.rollback()


def teci(stop: threading.Event, log: Callable[[str], None]) -> None:
    """Svoja nit in svoja baza: zajem nikoli ne čaka na disk zaradi dosjeja."""
    try:
        conn = povezi()
    except (sqlite3.Error, OSError) as exc:
        # Brez baze ni kam pisati, in vzorci bi rasli brez bralca.
        log(f"dosjeja ni mogoče odpreti: {exc}")
        pocisti()
        return
    glavna = db.connect()
    obrezano = 0.0
    napak = 0
    try:
        while not stop.wait(IZPRAZNI_S):
            zdaj = time.time()
            try:
                izprazni(conn, zdaj)
                if zdaj - obrezano > 86400:
                    obrezi(conn, zdaj)
                    obrezano = zdaj
                napak = 0
            except Exception as exc:        # noqa: BLE001 -- zajem teče naprej
                conn.rollback()             # glej `zamude_sz.teci()`
                napak += 1
                _napaka(exc)
                if napak == 1:
                    log(f"dosje: {exc}")
            _povzetek(glavna, zdaj)
        try:
            izprazni(conn, vse=True)
        except sqlite3.Error as exc:
            conn.rollback()
            log(f"dosje ob ustavitvi: {exc}")
    finally:
        conn.close()
        glavna.close()


# ---------------------------------------------------------------- branje

def _beri(path: Path | str) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{Path(path).resolve()}?mode=ro", uri=True, timeout=5)
    c.row_factory = sqlite3.Row
    return c


def _ura(ts: int | None) -> str:
    return datetime.fromtimestamp(ts, TZ).strftime("%H:%M:%S") if ts else "–"


def _najdi(d: sqlite3.Connection, iskano: str) -> list[str]:
    """Id vozila, tablica, številka ali id brez predpone vira (472 -> marprom-472)."""
    najdeno = [r[0] for r in d.execute(
        "SELECT DISTINCT vozilo FROM vozilo_dan WHERE vozilo = ?", (iskano,))]
    if najdeno:
        return najdeno
    najdeno = [r[0] for r in d.execute(
        "SELECT DISTINCT vozilo FROM oznaka WHERE oznaka = ? COLLATE NOCASE", (iskano,))]
    return najdeno or [r[0] for r in d.execute(
        "SELECT DISTINCT vozilo FROM vozilo_dan WHERE vozilo LIKE ? ESCAPE '\\'",
        ("%-" + iskano.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_"),))]


def _oznaka_voznje(g: sqlite3.Connection | None, trip_id: str | None) -> str:
    if not trip_id:
        return "brez vožnje"
    if g is not None:
        try:
            r = g.execute("SELECT train_no, headsign, agency FROM trip WHERE trip_id = ?",
                          (trip_id,)).fetchone()
        except sqlite3.Error:
            r = None
        if r:
            return f"{trip_id[:24]} ({r['agency']} {r['train_no']} → {r['headsign']})"
    return trip_id[:24]


def _iz_glavne(g: sqlite3.Connection, vozilo: str, dan: str,
               voznje: list[tuple[str, str]]) -> list[str]:
    """Kaj o vozilu ta dan ve glavna baza: lege, prehodi, meritve, senca, zdaj."""
    out = []
    for trip_id, sd in voznje:
        lega = g.execute("SELECT COUNT(*), MIN(ts), MAX(ts) FROM lega "
                         "WHERE service_date = ? AND trip_id = ? AND vozilo = ?",
                         (sd, trip_id, vozilo)).fetchone()
        prehodov = g.execute("SELECT COUNT(*) FROM gps_prehod WHERE service_date = ? AND trip_id = ?",
                             (sd, trip_id)).fetchone()[0]
        run = g.execute("SELECT COUNT(*), MAX(stop_seq), MAX(feed_ts) FROM run "
                        "WHERE trip_id = ? AND service_date = ?", (trip_id, sd)).fetchone()
        zadnja = g.execute("SELECT COALESCE(delay_dep, delay_arr) FROM run "
                           "WHERE trip_id = ? AND service_date = ? ORDER BY stop_seq DESC LIMIT 1",
                           (trip_id, sd)).fetchone()
        out.append(f"  {_oznaka_voznje(g, trip_id)} {sd}: lega {lega[0]} ({_ura(lega[1])}–"
                   f"{_ura(lega[2])}), prehodov {prehodov}, run {run[0]} postankov do {run[1]}, "
                   f"zadnja zamuda {zadnja[0] if zadnja else '–'} s")
    senca = g.execute(
        "SELECT vzrok, razlog, nap_voznja, nasa_voznja, derp_voznja, COUNT(*) AS n, MIN(ts) AS od, "
        "MAX(ts) AS do FROM pripis_senca WHERE dan = ? AND vozilo = ? GROUP BY 1, 2, 3, 4, 5 "
        "ORDER BY od", (dan, vozilo)).fetchall()
    if senca:
        out.append("senca pripisa (NAP / predlog / derp.si):")
        out += [f"  {_ura(r['od'])}–{_ura(r['do'])} ×{r['n']} {r['vzrok']} {r['razlog'] or 'par'}: "
                f"{r['nap_voznja']} / {r['nasa_voznja']} / {r['derp_voznja']}" for r in senca]
    opazeno = g.execute("SELECT vir, trip_id, vzorcev FROM straza_opazeno WHERE dan = ? AND vozilo = ?",
                        (dan, vozilo)).fetchall()
    if opazeno:
        out.append("straža, vzorci po vožnji: " + ", ".join(
            f"{r['vir']} {r['trip_id'][:12] or 'brez'} ×{r['vzorcev']}" for r in opazeno))
    zdaj = g.execute("SELECT trip_id, service_date, seen_ts, lat, lon, speed_ms, plate "
                     "FROM vehicle_now WHERE vehicle_id = ?", (vozilo,)).fetchall()
    for r in zdaj:
        out.append(f"zdaj: {_oznaka_voznje(g, r['trip_id'])} {r['service_date']}, lega "
                   f"{r['lat']:.5f},{r['lon']:.5f} ob {_ura(r['seen_ts'])}"
                   + (f", tablica {r['plate']}" if r["plate"] else ""))
    return out


def porocilo(iskano: str, dan: str | None = None, tocke: bool = False, surovo: bool = False,
             dosje_db: Path | str | None = None, glavna_db: Path | str | None = None) -> str:
    """Vse o vozilu: dnevi, dnevnik stanja dneva, kaj o njem ve glavna baza. Samo branje."""
    try:
        d = _beri(dosje_db or config.DOSJE_DB)
    except sqlite3.Error as exc:
        return f"dosjeja ni: {exc}"
    try:
        g = _beri(glavna_db or config.DB_PATH)
    except sqlite3.Error:
        g = None
    try:
        najdena = _najdi(d, iskano)
        if not najdena:
            return f"vozila {iskano} ni v dosjeju"
        vrstice = []
        for vozilo in najdena:
            vrstice += _porocilo_vozila(d, g, vozilo, dan, tocke, surovo) + [""]
        return "\n".join(vrstice)
    finally:
        d.close()
        if g is not None:
            g.close()


def _porocilo_vozila(d: sqlite3.Connection, g: sqlite3.Connection | None, vozilo: str,
                     dan: str | None, tocke: bool, surovo: bool) -> list[str]:
    dnevi = d.execute("SELECT dan, vir, razlog, vzorcev, prvic, nazadnje FROM vozilo_dan "
                      "WHERE vozilo = ? ORDER BY dan, vir, razlog", (vozilo,)).fetchall()
    oznake = [r[0] for r in d.execute("SELECT DISTINCT oznaka FROM oznaka WHERE vozilo = ?", (vozilo,))]
    out = [f"VOZILO {vozilo}" + (f"  ({', '.join(oznake)})" if oznake else "")]
    if not dnevi:
        return out + ["ni vzorcev"]
    po_dnevih: dict[str, list] = {}
    for r in dnevi:
        po_dnevih.setdefault(r["dan"], []).append(r)
    out.append("dnevi:")
    for x, vs in po_dnevih.items():
        vsi = [f"{r['vir']} ×{r['vzorcev']} {_ura(r['prvic'])}–{_ura(r['nazadnje'])}"
               for r in vs if not r["razlog"]]
        razlogi = [f"{r['vir']}:{r['razlog']} ×{r['vzorcev']}" for r in vs if r["razlog"]]
        out.append(f"  {x}  {'; '.join(vsi)}" + (f"  NAROBE {', '.join(razlogi)}" if razlogi else ""))
    dan = dan or dnevi[-1]["dan"]
    # Prometni dan se začne ob 3:00 (`straza._dan`); dnevnik je po uri, ne po dnevu.
    od = int(datetime.fromisoformat(f"{dan}T03:00:00").replace(tzinfo=TZ).timestamp())
    do = od + 86400
    out.append(f"== {dan}")
    stanja = d.execute(
        "SELECT * FROM stanje WHERE vozilo = ? AND ts >= ? AND ts < ? ORDER BY ts, vir",
        (vozilo, od, do)).fetchall()
    out.append(f"dnevnik stanja ({len(stanja)}):")
    prej: dict[str, bytes | None] = {}
    for s in stanja:
        vrstica = f"  {_ura(s['ts'])} {s['vir']:<7} {_oznaka_voznje(g, s['trip_id'])}"
        if s["dan"]:
            vrstica += f" {s['dan']}"
        if s["razlogi"]:
            vrstica += f"  [{s['razlogi']}]"
        if s["lat"] is not None:
            vrstica += f"  {s['lat']:.5f},{s['lon']:.5f}"
        if s["vir_ts"]:
            vrstica += f"  vir {_ura(s['vir_ts'])}"
        if s["sprotno"]:
            vrstica += f"  {s['sprotno']}"
        out.append(vrstica)
        if surovo and s["telo"] != prej.get(s["vir"]):
            t = d.execute("SELECT vsebina FROM telo WHERE odtis = ?", (s["telo"],)).fetchone()
            if t:
                out.append("    telo: " + zlib.decompress(t[0]).decode())
        prej[s["vir"]] = s["telo"]
    if g is not None:
        voznje = sorted({(s["trip_id"], s["dan"]) for s in stanja if s["trip_id"] and s["dan"]})
        try:
            out.append("glavna baza:")
            out += _iz_glavne(g, vozilo, dan, voznje)
        except sqlite3.Error as exc:
            out.append(f"  glavna baza ni dosegljiva: {exc}")
    zam = d.execute("SELECT vir, ts, trip_id, vsebina FROM zamude WHERE vozilo = ? AND ts >= ? "
                    "AND ts < ? ORDER BY ts", (vozilo, od, do)).fetchall()
    if zam:
        out.append(f"surove napovedi vira ({len(zam)}):")
        for r in zam:
            tu = gtfs_realtime_pb2.TripUpdate()
            tu.ParseFromString(zlib.decompress(r["vsebina"]))
            besedilo = text_format.MessageToString(tu, as_one_line=True, as_utf8=True)
            out.append(f"  {_ura(r['ts'])} {r['vir']} {r['trip_id']}: "
                       + (besedilo if surovo else besedilo[:200]))
    kosi = d.execute("SELECT vir, od_ts, n, vsebina FROM tocke WHERE vozilo = ? AND od_ts >= ? "
                     "AND od_ts < ? ORDER BY od_ts, vir", (vozilo, od, do)).fetchall()
    out.append(f"točke: {sum(k['n'] for k in kosi)} v {len(kosi)} kosih"
               + ("" if tocke else " (izpis: --tocke)"))
    if tocke:
        for k in kosi:
            for t in json.loads(zlib.decompress(k["vsebina"])):
                out.append(f"  {k['vir']:<7} {_ura(t[0])} {t[1]},{t[2]}"
                           + (f" {json.dumps(t[3], ensure_ascii=False)}" if t[3] else ""))
    return out


def seznam(dan: str | None = None, razlog: str | None = None,
           dosje_db: Path | str | None = None) -> str:
    """Vsa vozila dneva, s katerimi je bilo kaj narobe, po vzorcih. Samo branje."""
    try:
        d = _beri(dosje_db or config.DOSJE_DB)
    except sqlite3.Error as exc:
        return f"dosjeja ni: {exc}"
    try:
        dan = dan or (d.execute("SELECT MAX(dan) FROM vozilo_dan").fetchone()[0])
        if not dan:
            return "dosje je prazen"
        vseh = d.execute("SELECT COUNT(DISTINCT vozilo) FROM vozilo_dan WHERE dan = ?",
                         (dan,)).fetchone()[0]
        po_vozilu: dict[str, list] = {}
        for r in d.execute("SELECT vozilo, vir, razlog, vzorcev, prvic, nazadnje FROM vozilo_dan "
                           "WHERE dan = ? AND razlog != '' ORDER BY vzorcev DESC", (dan,)):
            po_vozilu.setdefault(r["vozilo"], []).append(r)
        if razlog:
            po_vozilu = {k: v for k, v in po_vozilu.items() if any(r["razlog"] == razlog for r in v)}
        po_razlogu: dict[str, set] = {}
        for k, v in po_vozilu.items():
            for r in v:
                po_razlogu.setdefault(r["razlog"], set()).add(k)
        out = [f"{dan}: vozil {vseh}, z razlogom {len(po_vozilu)}",
               ", ".join(f"{k} {len(v)}" for k, v in
                         sorted(po_razlogu.items(), key=lambda x: -len(x[1])))]
        for k, v in sorted(po_vozilu.items(), key=lambda x: -sum(r["vzorcev"] for r in x[1])):
            out.append(f"{k}  " + ", ".join(
                f"{r['vir']}:{r['razlog']} ×{r['vzorcev']} {_ura(r['prvic'])}–{_ura(r['nazadnje'])}"
                for r in v))
        return "\n".join(out)
    finally:
        d.close()
