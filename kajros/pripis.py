"""Pripis vozila na vožnjo: skupna koda za vse vire, samo z dokazom.

Zakaj (`docs/OPAZOVANO.md`, del 4): vsak vir je imel svoje pravilo, Marpromov
API pa pove prihod le enega avtobusa na linijo in postajališče. Mrtev avtobus
ga zasede, živi za njim ostane brez vožnje.

Vir pove samo varianto ali linijo, naslednje postajališče in čas. Vožnje iste
variante se med seboj ločijo samo po času, zato sta dokaza dva: vozilo res vozi
po varianti (naslednje postajališče se je že spremenilo, `Napredek`), in v oknu
okoli zdaj je **ena sama prosta vožnja**, širše pa ji nobena druga prosta ne
tekmuje. Napačen par je zamuda druge vožnje (`zive.py`): kadar dokaza ni, je
odgovor „brez para“.

Vir, ki naslednjega postajališča ne pove (NAP: samo lega), ga dobi iz lege:
`na_voznji` postavi vozilo na tetivo med postankoma vožnje in vrne voznoredni
čas tistega kraja -- ta gre v `predlagaj` namesto časa na naslednjem.

Tu je samo račun: brez baze zajema in brez pisanja. Sence v `run` ne pišemo.
"""
from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from . import config, prehod, stats

TZ = ZoneInfo(config.TIMEZONE)

#: Vožnja pride v poštev, če je vozilo od njenega časa na naslednjem
#: postajališču toliko sekund (minus = še pride).
OKNO_S = (-240, 600)
#: Druga prosta vožnja v tem oknu pomeni, da časa ne moremo ločiti.
TEKMEC_S = (-240, 1800)
#: Vozilo dlje od tetive med zaporednima postankoma te vožnje ne vozi.
#: Tetiva, ne trasa (kot `prehod.py`): med daljnimi postanki seka ovinke --
#: lege NAP na svoji vožnji 31. 10. 2026 p50 40 m, p90 611 m, p95 2,6 km. V
#: ponovitvi sence (`lega`, 10-13 h) 500 m: 7 335 parov, 1 000 m: 7 536,
#: 2 500 m: 7 776 in 915 `vec`; napačna pri vseh dva, na meji med vožnjama.
ODMIK_M = 1000


@dataclass(frozen=True)
class Voznja:
    """Vožnja voznega reda na enem postajališču."""
    trip_id: str
    dan: str
    seq: int
    cas: float      # epoha: odhod s postajališča po voznem redu


@dataclass(frozen=True)
class Predlog:
    voznja: Voznja | None
    #: "" kadar je par; sicer zakaj ne: `miruje`, `ni_prosta`, `vec`.
    razlog: str = ""


class Napredek:
    """Ali vozilo vozi po varianti: naslednje postajališče se je na njej že
    spremenilo. Vozilo, ki čaka na končni, ima varianto naslednje vožnje in
    uro, ki s časom ne pove ničesar."""

    def __init__(self) -> None:
        self._vozila: dict[str, tuple[str, str, bool]] = {}

    def opazi(self, vozilo: str, varianta: str, naslednja: str) -> bool:
        prej = self._vozila.get(vozilo)
        napreduje = bool(prej and prej[0] == varianta and (prej[2] or prej[1] != naslednja))
        self._vozila[vozilo] = (varianta, naslednja, napreduje)
        return napreduje

    def pozabi(self, vidni: set[str]) -> None:
        """Vozilo, ki ga vir ne javlja več, začne znova."""
        for k in [k for k in self._vozila if k not in vidni]:
            del self._vozila[k]


def kandidati(idx: dict[tuple[str, str], list[Voznja]], kljuc: str,
              postajalisca: list[str]) -> list[Voznja]:
    """Vožnje variante ali linije na prvem od postajališč, ki ga vozni red ima
    (naslednje, nato iz iste skupine: Marprom 457 namesto 192 na končni)."""
    for p in postajalisca:
        najdene = idx.get((kljuc, p))
        if najdene:
            return najdene
    return []


def predlagaj(kandidati: list[Voznja], zdaj: float, zasedene: set[tuple[str, str]],
              napreduje: bool = True, okno: tuple[int, int] = OKNO_S,
              tekmec: tuple[int, int] = TEKMEC_S) -> Predlog:
    """Vožnje iste variante na naslednjem postajališču vozila -> par ali nič.

    `zasedene` = (trip_id, dan), ki jih drugo vozilo ima ali jih je že odpeljalo.
    """
    if not napreduje:
        return Predlog(None, "miruje")
    proste = [k for k in kandidati if (k.trip_id, k.dan) not in zasedene]
    v_oknu = [k for k in proste if okno[0] <= zdaj - k.cas <= okno[1]]
    if not v_oknu:
        return Predlog(None, "ni_prosta")
    if sum(tekmec[0] <= zdaj - k.cas <= tekmec[1] for k in proste) > 1:
        return Predlog(None, "vec")
    return Predlog(v_oknu[0])


def na_voznji(postanki: list[tuple], lat: float, lon: float, zdaj_s: float,
              odmik_m: float = ODMIK_M) -> tuple[float, int] | None:
    """Kje na vožnji je vozilo po legi: (voznoredni čas tega kraja, naslednji
    postanek) ali None, če je od vseh tetiv dlje kot `odmik_m`.

    `postanki` = [(stop_seq, lat, lon, čas_s)] po vrsti, čas v s od polnoči
    prometnega dne, kot `zdaj_s`. Med postankoma je čas razdeljen po razdalji.
    Kjer gre vožnja dvakrat mimo istega kraja (zanka, tja in nazaj), velja
    odsek, katerega čas je najbližje `zdaj_s`: drugače bi vozilo na prvem
    prehodu dobilo čas drugega.
    """
    kx = math.cos(math.radians(lat)) * prehod._M
    x, y = lon * kx, lat * prehod._M
    naj = None
    for (_, la1, lo1, t1), (seq, la2, lo2, t2) in zip(postanki, postanki[1:]):
        if t1 is None or t2 is None:
            continue
        d, t = prehod._blizina((t1, lo1 * kx, la1 * prehod._M, t2, lo2 * kx, la2 * prehod._M), x, y)
        if d <= odmik_m and (naj is None or abs(zdaj_s - t) < abs(zdaj_s - naj[0])):
            naj = (t, seq)
    return naj


def indeks(conn: sqlite3.Connection, zdaj: float,
           agencija: str) -> dict[tuple[str, str], list[Voznja]]:
    """(varianta, postajališče) in (linija, postajališče) -> vožnje, za včeraj in danes."""
    danes = datetime.fromtimestamp(zdaj, TZ).date()
    out: dict[tuple[str, str], list[Voznja]] = {}
    for dan in ((danes - timedelta(days=1)).isoformat(), danes.isoformat()):
        polnoc = stats.polnoc(dan)
        for r in conn.execute(
                "SELECT t.trip_id, t.route_id, t.shape_id, s.stop_id, s.stop_seq, "
                "       COALESCE(s.dep_s, s.arr_s) "
                "FROM trip t "
                "JOIN service_day sd ON sd.service_id = t.service_id AND sd.date = ? "
                "JOIN sched s ON s.trip_id = t.trip_id "
                "WHERE t.agency = ?", (dan, agencija)):
            if r[5] is None:
                continue
            v = Voznja(r[0], dan, r[4], polnoc + r[5])
            for kljuc in (r[2], r[1]):
                if kljuc:
                    out.setdefault((kljuc, r[3]), []).append(v)
    return out
