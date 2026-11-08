"""Lege avtobusov IJPP naravnost z NAP (SIRI-VM), mimo derp.si.

Zakaj: lege IJPP, ki jih beremo z derp.si, so prav ta vir, le pretvorjen
(`derp-si/ijpp-rt`, `ijppService.js`: SIRI z NAP na 5 s v GTFS-RT). 8. 10.
2026 je strežnik RT derp.si od 16:00 zavračal povezave in zemljevid je ostal
brez medkrajevnih avtobusov, čeprav so vozila lego pošiljala naprej. NAP je
izvirnik: naprava na vozilu -> Realis -> NAP.

Dostop: račun na nap.si in odobritev vsebine „SIRI dinamični podatki - API“
(zaprošeno 8. 10. 2026). Prijava je v `${KAJROS_DATA_DIR}/.nap-prijava` kot
`e-naslov:geslo` (postavi jo `deploy/nap.sh`) ali v `KAJROS_NAP_PRIJAVA`.
API sprejme avtentikacijo basic (`b2b.siri.api.sl.pdf`), zato brez žetonov.

Id vožnje: `VehicleJourneyRef` je NeTEx id
`SI:SI0:ServiceJourney:<GUID>:IJPP`, zadnji štirje bajti GUID-a so `trip_id`
v GTFS IJPP -- isto pretvorbo dela `derp-si/ijpp-rt` (`realisToIjpp`).

Kam gre:

* `vehicle_now` za vsa pripeta vozila; zmaga novejša lega (`zapisi`).
* zamuda iz lege (`iz_lege.opazuj`) za vozila, ki jih derp.si ta hip nima
  (`collector.lege_derp`), kadar feed zamud vožnje ne nosi -- ob izpadu
  derp.si torej za vse.
* kadar imata vozilo oba, se primerjata (`primerjaj`): ista vožnja, odmik
  lege ob istem času, kateri je svežejši. Vse v `meta.nap` za `/admin`.

NAP nima mestnega LPP in ne primestnih vozil LPP (`LJLPP…`), ki jih derp.si
v isti feed doda iz LPP-jevega vira: 9. 10. 2026 55 od ~80 vozil „samo
derp“. Vlakov nima (`VehicleMode` 705-krat `bus`).
"""
from __future__ import annotations

import json
import sqlite3
import statistics
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Callable

import requests

from . import collector, config, db, dosje, geo, iz_lege, prehod, pripis, stats, straza, viri

TZ = collector.TZ

#: Zahtevek za lege vseh vozil (dokumentacija NAP, „Pridobivanje lokacij vseh
#: vozil“). Brez filtra: ene linije potnik ne izbere vnaprej.
_ZAHTEVEK = """<?xml version="1.0" encoding="utf-8"?>
<ServiceRequest xmlns="http://www.siri.org.uk/siri">
  <RequestTimestamp>{cas}</RequestTimestamp>
  <VehicleMonitoringRequest>
    <RequestTimestamp>{cas}</RequestTimestamp>
  </VehicleMonitoringRequest>
</ServiceRequest>"""

#: `derp-si/ijpp-rt` popravlja `RecordedAtTime`, ki je natanko uro v
#: prihodnosti (±3 min) -- naprava očitno pošlje lokalni čas z napačnim
#: zamikom. Popravek prevzamemo; koliko jih je, šteje `popravljenih`.
URA_NAPREJ_S, URA_TOLERANCA_S = 3600, 180
#: Lega, ki je po popravku še v prihodnosti, je napačna.
NAJVEC_NAPREJ_S = 30
#: derp.si izpusti vožnje, ki se začnejo čez več kot 30 min (vozilo čaka na
#: izhodišču prejšnjo vožnjo). Ista meja, da je primerjava primerljiva.
PREZGODAJ_S = 1800
#: Lege derp.si so „zdaj“, dokler jih je zajem potrdil v tem času. Bere jih
#: na 10 s; minuta je šest zgrešenih branj.
DERP_SVEZE_S = 60
#: 401/403 = dostop (še) ni odobren. Ne trkaj na 10 s, ko se ne more nič
#: spremeniti brez človeka.
NI_DOSTOPA_CAKAJ_S = 600
#: ... razen kadar je ista prijava pravkar delala: 17. 10. 2026 ob 6:35 in
#: 7:36 je NAP pod obremenitvijo (časovne meje, prekinjene povezave) dvakrat
#: vrnil 401 in se čez minuto vrnil sam; desetminutni premor je pustil dve
#: devetminutni vrzeli leg. Zavrnjena prijava je šele `ZAVRNJENA_PO` zapored
#: ali brez uspeha v zadnji uri.
ZAVRNJENA_PO, ZAVRNJENA_CAKAJ_S = 3, 60
TIMEOUT_S = (10, 20)


def cakaj_po_zavrnitvi(zapored: int, od_uspeha_s: float) -> int:
    """Koliko sekund počakati po `zapored`-ti zavrnitvi prijave zapored."""
    if zapored < ZAVRNJENA_PO and od_uspeha_s < 3600:
        return ZAVRNJENA_CAKAJ_S
    return NI_DOSTOPA_CAKAJ_S


class NiDostopa(RuntimeError):
    """NAP je prijavo zavrnil: napačno geslo ali vsebina ni odobrena."""

    def __init__(self, http: int):
        super().__init__(f"NAP zavrnil prijavo (HTTP {http})")
        self.http = http


def prijava() -> tuple[str, str] | None:
    """(uporabnik, geslo) ali None. Bere se ob vsakem obhodu, da prijava, ki
    jo skrbnik postavi pozneje, velja brez ponovnega zagona."""
    vrstica = config.okolje("NAP_PRIJAVA", "") or ""
    if not vrstica:
        try:
            vrstica = (config.DATA_DIR / ".nap-prijava").read_text(encoding="utf-8")
        except OSError:
            return None
    # Uporabnik je e-naslov, dvopičja nima; geslo ga sme imeti.
    uporabnik, _, geslo = vrstica.strip().partition(":")
    return (uporabnik, geslo) if uporabnik and geslo else None


def ijpp_id(ref: str | None) -> str | None:
    """`SI:SI0:ServiceJourney:00000000-1177-0008-0000-000000049908:IJPP` ->
    `301320` (zadnji štirje bajti GUID-a)."""
    deli = (ref or "").split(":")
    if len(deli) != 5:
        return None
    guid = deli[3].replace("-", "")
    if len(guid) != 32:
        return None
    try:
        return str(int(guid[-8:], 16))
    except ValueError:
        return None


def _lokalno(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _otrok(el, *pot: str):
    """Otrok po lokalnem imenu: imenski prostor SIRI je pri NAP en, a ga ne
    vežemo -- `derp-si/ijpp-rt` ga prav tako odreže."""
    for ime in pot:
        if el is None:
            return None
        el = next((o for o in el if _lokalno(o.tag) == ime), None)
    return el


def _besedilo(el, *pot: str) -> str | None:
    o = _otrok(el, *pot)
    return o.text.strip() if o is not None and o.text else None


def _cas(s: str | None) -> float | None:
    if not s:
        return None
    try:
        d = datetime.fromisoformat(s)
    except ValueError:
        return None
    return (d if d.tzinfo else d.replace(tzinfo=TZ)).timestamp()


def _za_dosje(va, mvj) -> dict:
    """Kar NAP o vozilu pove, za `dosje`: ključ in telo se sproti ne spreminjata."""
    stalno, deli = {}, []
    for e in mvj if mvj is not None else ():
        ime = _lokalno(e.tag)
        if ime == "JourneyParts":
            deli = [x.text for x in e.iter() if _lokalno(x.tag) == "JourneyPartRef"]
        elif ime not in ("VehicleLocation", "Bearing"):
            stalno[ime] = e.text
    return {"kljuc": (tuple(stalno.items()), len(deli), deli[:1], deli[-1:]),
            "telo": {**stalno, "JourneyParts": deli},
            "sprotno": {"posneto": _besedilo(va, "RecordedAtTime"),
                        "velja_do": _besedilo(va, "ValidUntilTime"),
                        "smer": _besedilo(mvj, "Bearing")}}


def _odpadel(s: dict | None, vozilo: str | None, ts: float | None, lat: float | None,
             lon: float | None, razlog: str, zdaj: float) -> None:
    """Vzorec, ki ga `razberi` izpusti, je ravno vozilo, s katerim je kaj narobe."""
    if s is not None:
        dosje.opazi("nap", vozilo, ts, lat, lon, razlogi=(razlog,), kljuc=s["kljuc"],
                    telo=s["telo"], sprotno=s["sprotno"], zdaj=zdaj)


def razberi(vsebina: bytes, zdaj: float, surovo: dict | None = None) -> tuple[list[dict], dict]:
    """Odgovor SIRI -> [vozilo], števci.

    Vozilo: `vozilo`, `ijpp` (trip_id po pretvorbi), `ts`, `lat`, `lon`,
    `smer`, `nacin`. Brez lege ali s časom zunaj meja se izpusti in šteje.
    `surovo` (če je dan) dobi po vozilu, kar NAP pove zanj (`_za_dosje`).
    """
    koren = ET.fromstring(vsebina)
    dostava = next((e for e in koren.iter() if _lokalno(e.tag) == "ServiceDelivery"), koren)
    odgovor = _cas(_besedilo(dostava, "ResponseTimestamp")) or zdaj
    st = {"vozil": 0, "popravljenih": 0, "starih": 0, "naprej": 0, "brez_lege": 0,
          "brez_id": 0}
    out = []
    for va in koren.iter():
        if _lokalno(va.tag) != "VehicleActivity":
            continue
        st["vozil"] += 1
        mvj = _otrok(va, "MonitoredVehicleJourney")
        s = _za_dosje(va, mvj) if surovo is not None else None
        popravljen = False
        vozilo = _besedilo(mvj, "VehicleRef")
        ts = _cas(_besedilo(va, "RecordedAtTime"))
        try:
            lat = float(_besedilo(mvj, "VehicleLocation", "Latitude") or "")
            lon = float(_besedilo(mvj, "VehicleLocation", "Longitude") or "")
        except ValueError:
            lat = lon = None
        if lat is None or ts is None or not vozilo:
            st["brez_lege"] += 1
            _odpadel(s, vozilo, ts, lat, lon, "brez_lege", zdaj)
            continue
        if abs(ts - odgovor - URA_NAPREJ_S) <= URA_TOLERANCA_S:
            ts -= URA_NAPREJ_S
            st["popravljenih"] += 1
            popravljen = True
        if ts - odgovor > NAJVEC_NAPREJ_S:
            st["naprej"] += 1
            _odpadel(s, vozilo, ts, lat, lon, "ura_naprej", zdaj)
            continue
        if odgovor - ts > collector.POSITION_FRESH_S:
            st["starih"] += 1
            _odpadel(s, vozilo, ts, lat, lon, "stara_lega", zdaj)
            continue
        ijpp = ijpp_id(_besedilo(mvj, "VehicleJourneyRef"))
        if ijpp is None:
            st["brez_id"] += 1
            _odpadel(s, vozilo, ts, lat, lon, "brez_id", zdaj)
            continue
        if s is not None:
            surovo[vozilo] = {**s, "popravljen": popravljen}
        try:
            smer = float(_besedilo(mvj, "Bearing") or "")
        except ValueError:
            smer = None
        out.append({"vozilo": vozilo, "ijpp": ijpp, "ts": int(ts), "lat": lat,
                    "lon": lon, "smer": smer, "nacin": _besedilo(mvj, "VehicleMode")})
    return out, st


def _nacin(conn: sqlite3.Connection) -> dict[str, str]:
    """trip_id -> `mode` (bus/rail). Vlake NAP morda nosi; ali jih, in pod
    katerim id-jem, se bo videlo -- do takrat jih le štejemo."""
    def build():
        return {r[0]: r[1] for r in conn.execute("SELECT trip_id, mode FROM trip")}
    return collector._cached(conn, "nap_nacin", None, build)


#: Toliko nepripetih vozil z vzrokom gre v `meta.nap` (za /preveri-vire).
NEPRIPETIH = 15


def pripni(conn: sqlite3.Connection, vozila: list[dict], zdaj: float,
           za_senco: list | None = None) -> tuple[list[dict], dict]:
    """Vozilo -> naša vožnja in obratovalni dan. Isti prevod starega id-ja
    kot pri derp.si (`zamenjava`), isti izbor dneva kot pri vlakih SŽ, ki
    `start_date` tudi nimajo (`collector.resolve_service_date`).

    `za_senco` dobi (vozilo, vožnja, vzrok) za vsako nepripeto vozilo in za
    pripeto na vožnjo, ki se še ni začela ali se je končala pred več kot
    `PO_KONCU_S` (`Senca`)."""
    okna = collector._rail_trip_windows(conn)
    zdaj_dt = datetime.fromtimestamp(zdaj, TZ)
    dnevi = collector._service_dates(conn, zdaj_dt)
    zamenjave = collector._zamenjave(conn)
    nacin = _nacin(conn)
    agencije = collector._agencije(conn)
    st = {"pripetih": 0, "brez_voznje": 0, "brez_dneva": 0, "prezgodaj": 0, "vlakov": 0}
    # Vzorec nepripetih z vzrokom: 31. 10. 2026 (praznik) je bilo `brez_dneva`
    # 13 vozil, derp.si jih je pripel -- iz števca ni bilo videti, katera
    # vožnja in kateri dnevi (`docs/VIRI-PRESOJA.md`, točka 2).
    nepripeti: list[dict] = []

    def ne(v: dict, tid: str, razlog: str) -> None:
        st[razlog] += 1
        straza.vzorec("nap", v["vozilo"], None, zdaj)
        if len(nepripeti) < NEPRIPETIH:
            nepripeti.append({"vozilo": v["vozilo"], "voznja": v["ijpp"], "nasa": tid,
                              "razlog": razlog, "okno": okna.get(tid),
                              "dnevi": sorted(dnevi.get(tid) or ())[-3:]})
        if za_senco is not None:
            za_senco.append((v, tid, razlog))
    out = []
    for v in vozila:
        tid = v["ijpp"]
        if tid not in okna and tid in zamenjave:
            tid = zamenjave[tid][0]
        if tid not in okna:
            ne(v, tid, "brez_voznje")
            continue
        dan = collector.resolve_service_date(tid, okna[tid], dnevi.get(tid), zdaj_dt)
        if dan is None:
            ne(v, tid, "brez_dneva")
            continue
        if stats.polnoc(dan) + okna[tid][0] - zdaj > PREZGODAJ_S:
            ne(v, tid, "prezgodaj")
            continue
        if nacin.get(tid) != "bus":
            st["vlakov"] += 1
            continue
        st["pripetih"] += 1
        straza.vzorec("nap", v["vozilo"], tid, zdaj)
        out.append({**v, "trip_id": tid, "dan": dan, "agency": agencije.get(tid)})
        if za_senco is not None:
            od_polnoci = zdaj - stats.polnoc(dan)
            if od_polnoci < okna[tid][0]:
                za_senco.append((v, tid, "pred_odhodom"))
            elif od_polnoci - okna[tid][1] > PO_KONCU_S:
                za_senco.append((v, tid, "po_koncu"))
    st["nepripeti"] = nepripeti
    return out, st


#: Pripeto vozilo, čigar vožnja se je po voznem redu končala pred toliko
#: sekundami, gre v senco: `resolve_service_date` dopusti še 3 h, prijava pa
#: ni verjetna (vozilo pelje v garažo ali že drugo vožnjo). V senco gre tudi
#: pripeto na vožnjo, ki se še ni začela: NAP naslednjo javi do 30 min prej
#: (`PREZGODAJ_S`), vozilo pa še vozi prejšnjo -- ponovitev na `lega` 31. 10.
#: 2026, 10-13 h: 292 od 7 830 parov v senci je bila prejšnja vožnja.
PO_KONCU_S = 2700
#: Senca računa isto vozilo največ enkrat v tem času. Napredek (`pripis`) rabi
#: dve opazovanji z različnim naslednjim postankom; minuta je dovolj na
#: medkrajevnih, kjer so postanki 2-5 min narazen, in drži ceno pod NAP-ovim
#: ritmom (10 s; izmerjeno v `docs/VIRI-PRESOJA.md`, točka 2).
SENCA_VSAKIH_S = 60
SENCA_DNI = 14
#: Kandidatka, na kateri se je vozilo od prejšnjega računa premaknilo nazaj za
#: toliko voznorednih sekund, ni njegova: vožnja v drugo smer po isti cesti
#: (končana prejšnja, ki ji vozilo pelje nasproti).
NAZAJ_S = 30


class Senca:
    """Katero vožnjo bi vozilu, ki ga NAP ne pripne, pripel `pripis.py` iz
    lege, ure in voznega reda (`docs/VIRI-PRESOJA.md`, točka 2).

    David 31. 10. 2026: sami računamo, ne od posrednika -- derp.si vozilu
    vožnjo določi sam, mi pa verjamemo `VehicleJourneyRef`, ki je na prazniku
    za naš koledar napačen ali že naslednja vožnja. Kandidatke: vožnje proge
    in verige (`block_id`) NAP-ove vožnje in zadnje vožnje, na katero je NAP
    vozilo pripel, ter NAP-ova vožnja sama tudi na dan, ko je naš koledar
    nima. Odloči `pripis.predlagaj` (ena prosta v oknu, brez tekmice).

    Piše samo `pripis_senca`: v `run`, `obs`, `vehicle_now` nič. derp-ova
    vožnja istega vozila ob istem branju je primerjava, ne vir.
    """

    def __init__(self) -> None:
        self.napredek = pripis.Napredek()
        self.racunano: dict[str, float] = {}
        #: vozilo -> (vožnja, dan), na katero ga je NAP nazadnje pripel
        self.zadnja: dict[str, tuple[str, str]] = {}
        #: (vožnja, dan) -> (vozilo, ts): NAP jo je pripel, drugemu ni prosta
        self.videne: dict[tuple[str, str], tuple[str, float]] = {}
        #: vozilo -> (vožnja, dan) para v senci
        self.par: dict[str, tuple[str, str]] = {}
        #: vozilo -> {(vožnja, dan): [(ts, voznoredni čas kraja)]} računov v
        #: zadnjih `pripis.SMER_S`: `NAZAJ_S` gleda zadnjega, vrata smeri vse
        self.kraj: dict[str, dict[tuple[str, str], list[tuple[float, float]]]] = {}
        self.stevci: dict = {}
        self.obrezano = 0.0

    def opazuj(self, conn: sqlite3.Connection, za_senco: list, pripeta: list[dict],
               derp: dict | None, zdaj: float) -> dict:
        """Senca enega odgovora NAP -> števci dneva za `meta.nap`. Commit
        naredi `korak`, v isti transakciji kot lege (zaklep že drži)."""
        zacetek = time.perf_counter()
        for v in pripeta:
            k = (v["trip_id"], v["dan"])
            self.zadnja[v["vozilo"]] = k
            self.videne[k] = (v["vozilo"], zdaj)
        vidni = {v["vozilo"] for v, _, _ in za_senco}
        self.napredek.pozabi(vidni)
        for slovar in (self.par, self.kraj):
            for k in [k for k in slovar if k not in vidni]:
                del slovar[k]
        dan = straza._dan(zdaj)
        if self.stevci.get("dan") != dan:
            self.stevci = {"dan": dan, "racunov": 0, "par": 0, "brez_kandidata": 0,
                           "miruje": 0, "ni_prosta": 0, "vec": 0, "smer": 0, "napak": 0,
                           "ms_vsota": 0.0, "ms_najvec": 0.0}
        st = self.stevci
        for v, tid, vzrok in za_senco:
            if zdaj - self.racunano.get(v["vozilo"], 0.0) < SENCA_VSAKIH_S:
                continue
            self.racunano[v["vozilo"]] = zdaj
            t0 = time.perf_counter()
            try:
                vrstica = self._racun(conn, v, tid, vzrok, derp, zdaj, dan)
                conn.execute("INSERT OR REPLACE INTO pripis_senca(ts, vozilo, dan, vzrok, "
                             "nap_voznja, nasa_voznja, nas_dan, razlog, zamuda_s, kandidatov, "
                             "derp_voznja, lat, lon) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", vrstica)
            except Exception as exc:        # noqa: BLE001 -- senca ne sme ustaviti NAP
                st["napak"] += 1
                st["napaka"] = f"{type(exc).__name__}: {exc}"[:200]
                continue
            ms = (time.perf_counter() - t0) * 1000
            st["racunov"] += 1
            st["par" if not vrstica[7] else vrstica[7]] += 1
            st["ms_vsota"] = round(st["ms_vsota"] + ms, 1)
            st["ms_najvec"] = round(max(st["ms_najvec"], ms), 1)
        if zdaj - self.obrezano > 3600:
            conn.execute("DELETE FROM pripis_senca WHERE ts < ?", (int(zdaj) - SENCA_DNI * 86400,))
            self.videne = {k: x for k, x in self.videne.items() if zdaj - x[1] < 86400}
            self.racunano = {k: t for k, t in self.racunano.items() if zdaj - t < 3600}
            zivi = vidni | {w for w, _ in self.videne.values()}
            self.zadnja = {k: x for k, x in self.zadnja.items() if k in zivi}
            self.obrezano = zdaj
        return {**st, "vozil": len(za_senco),
                "ms": round((time.perf_counter() - zacetek) * 1000, 1)}

    def _racun(self, conn: sqlite3.Connection, v: dict, tid: str, vzrok: str,
               derp: dict | None, zdaj: float, dan: str) -> tuple:
        okna = collector._rail_trip_windows(conn)
        dnevi = collector._service_dates(conn, datetime.fromtimestamp(zdaj, TZ))
        vozilo = v["vozilo"]
        zadnja = self.zadnja.get(vozilo)
        danes = datetime.fromtimestamp(zdaj, TZ).date()
        datumi = [(danes - timedelta(days=1)).isoformat(), danes.isoformat()]
        prejsnji = self.kraj.get(vozilo, {})
        kraj: dict[tuple[str, str], list[tuple[float, float]]] = {}
        kand: list[tuple[pripis.Voznja, str]] = []
        naprej: set[tuple[str, str]] = set()
        for c, varianta in _sosede(conn, [t for t in (tid, zadnja and zadnja[0]) if t in okna]).items():
            if c not in okna:
                continue
            zac, kon = okna[c]
            for d in datumi:
                # NAP-ova vožnja tudi na dan, ko je naš koledar nima: praznik.
                if d not in dnevi.get(c, ()) and c != tid:
                    continue
                polnoc = stats.polnoc(d)
                if not (polnoc + zac + pripis.OKNO_S[0] <= zdaj <= polnoc + kon + pripis.TEKMEC_S[1]):
                    continue
                naj = pripis.na_voznji(_postanki(conn, c), v["lat"], v["lon"], zdaj - polnoc)
                if naj is None:
                    continue
                zgo = [x for x in prejsnji.get((c, d), ()) if zdaj - x[0] <= pripis.SMER_S]
                kraj[(c, d)] = zgo + [(zdaj, naj[0])]
                if zgo and naj[0] < zgo[-1][1] - NAZAJ_S:
                    continue
                if pripis.naprej(zgo, zdaj, naj[0]):
                    naprej.add((c, d))
                kand.append((pripis.Voznja(c, d, naj[1], polnoc + naj[0]), varianta))
        self.kraj[vozilo] = kraj
        # Svoje vožnje vozilo ne zaseda samo sebi (kot `scripts/pripis_senca.py`):
        # NAP ga je na prejšnjo pripel, preden jo je končalo. Nasproti vožnji, ki
        # jo je končalo, vozilo pelje nazaj -- to izloči `NAZAJ_S`.
        zasedene = {k for k, (w, _) in self.videne.items() if w != vozilo}
        zasedene |= {k for w, k in self.par.items() if w != vozilo}
        if kand:
            naj, varianta = min(kand, key=lambda x: abs(zdaj - x[0].cas))
            gre = self.napredek.opazi(vozilo, varianta, str(naj.seq))
            predlog = pripis.predlagaj([k for k, _ in kand], zdaj, zasedene, gre,
                                       naprej=naprej)
        else:
            predlog = pripis.Predlog(None, "brez_kandidata")
        par = predlog.voznja
        if par is None:
            self.par.pop(vozilo, None)
        else:
            self.par[vozilo] = (par.trip_id, par.dan)
        return (int(zdaj), vozilo, dan, vzrok, tid, par and par.trip_id, par and par.dan,
                predlog.razlog, par and round(zdaj - par.cas), len(kand),
                _derp_voznja(conn, derp, vozilo, okna), v["lat"], v["lon"])


def _sosede(conn: sqlite3.Connection, seme: list[str]) -> dict[str, str]:
    """Vožnje proge in verige (`block_id`) danih -> varianta (trasa ali proga).
    Proga IJPP je linija v obe smeri ali v eno (Koper-Piran 65800, nazaj
    65768); veriga poveže smeri, ki jih vozi isto vozilo."""
    if not seme:
        return {}
    q = ",".join("?" * len(seme))
    rows = conn.execute(f"SELECT route_id, block_id FROM trip WHERE trip_id IN ({q})",
                        seme).fetchall()
    out: dict[str, str] = {}
    for stolpec, vrednosti in (("route_id", {r[0] for r in rows if r[0]}),
                               ("block_id", {r[1] for r in rows if r[1]})):
        if vrednosti:
            for r in conn.execute(
                    f"SELECT trip_id, COALESCE(shape_id, route_id) FROM trip "
                    f"WHERE {stolpec} IN ({','.join('?' * len(vrednosti))})", sorted(vrednosti)):
                out[r[0]] = r[1] or ""
    return out


def _postanki(conn: sqlite3.Connection, trip_id: str) -> list[tuple]:
    """[(stop_seq, lat, lon, čas_s)] vožnje; predpomnjeno do novega uvoza."""
    spomin = collector._cached(conn, "nap_senca_postanki", None, dict)
    if trip_id not in spomin:
        spomin[trip_id] = conn.execute(
            "SELECT s.stop_seq, st.lat, st.lon, COALESCE(s.dep_s, s.arr_s) FROM sched s "
            "JOIN station st USING (stop_id) WHERE s.trip_id = ? ORDER BY s.stop_seq",
            (trip_id,)).fetchall()
    return spomin[trip_id]


def _derp_voznja(conn: sqlite3.Connection, derp: dict | None, vozilo: str,
                 okna: dict) -> str | None:
    """Vožnja vozila po derp.si ob istem branju (po `zamenjava`): NULL = derp.si
    ni svež, '' = vozila nima."""
    if derp is None:
        return None
    d = derp.get(vozilo)
    if d is None:
        return ""
    t = d[0]
    if t not in okna:
        t = collector._zamenjave(conn).get(t, (t,))[0]
    return t


senca = Senca()


def primerjaj(vozila: list[dict], derp: dict | None) -> dict:
    """NAP proti derp.si po vozilu. derp.si bere isti vir, torej morata
    vožnja in lega ob istem času soupasti; razlika je napaka pretvorbe na
    eni strani. `prednost_s` = za koliko je NAP-ova lega novejša."""
    if derp is None:
        return {"derp": False}
    skupni = [(v, derp[v["vozilo"]]) for v in vozila if v["vozilo"] in derp]
    odmiki = [geo.haversine(v["lat"], v["lon"], d[2], d[3])
              for v, d in skupni if v["ts"] == d[1]]
    prednost = [v["ts"] - d[1] for v, d in skupni]
    nap = {v["vozilo"] for v in vozila}
    return {
        "derp": True, "skupnih": len(skupni),
        "ista_voznja": sum(v["ijpp"] == d[0] for v, d in skupni),
        "isti_cas": len(odmiki),
        "odmik_m": round(statistics.median(odmiki), 1) if odmiki else None,
        "odmik_max_m": round(max(odmiki), 1) if odmiki else None,
        "prednost_s": statistics.median(prednost) if prednost else None,
        "samo_nap": len(nap - derp.keys()), "samo_derp": len(derp.keys() - nap),
    }


def zapisi(conn: sqlite3.Connection, pripeta: list[dict], derp: dict | None,
           zdaj: float) -> dict:
    """Lega v `vehicle_now` za vsa vozila, zamuda iz lege samo za tista, ki
    jih derp.si nima.

    Lega: NAP je izvirnik in je novejši (9. 10. 2026 mediana 7-20 s na ~640
    skupnih vozilih, ista vožnja 99,8 %, odmik ob istem času 0,1 m), zato
    zmaga po `seen_ts`; derp-ova starejša lega istega vozila je ne povozi.
    Zamuda iz lege: za vozilo, ki ga derp.si nosi, jo računa njegov zajem
    (`iz_lege.iz_feeda`) -- isto sled bi sicer vodili dve niti.
    """
    zapisanih = prehodov = 0
    for v in pripeta:
        # Dve vozili na isti vožnji: na zemljevidu tisto, ki jo vodi
        # (`prehod.vodja`), dokler se javlja -- sicer ikona skače med njima.
        vodi = prehod.vodja(v["trip_id"], v["dan"])
        if vodi and vodi[0] != v["vozilo"] and v["ts"] - vodi[1] <= prehod.RAZMIK_S:
            dosje.oznaci(v["vozilo"], "drugo_vozilo_vodi", zdaj)
            prehodov += _iz_lege(conn, v, derp, zdaj)
            continue
        conn.execute(
            "INSERT INTO vehicle_now(trip_id, service_date, seen_ts, lat, lon, bearing,"
            "                        vehicle_id) VALUES(?,?,?,?,?,?,?) "
            "ON CONFLICT(trip_id) DO UPDATE SET "
            "  service_date=excluded.service_date, seen_ts=excluded.seen_ts,"
            "  lat=excluded.lat, lon=excluded.lon, bearing=excluded.bearing,"
            "  speed_ms=NULL, stop_seq=NULL, status=NULL,"
            "  vehicle_id=excluded.vehicle_id "
            "WHERE excluded.seen_ts > vehicle_now.seen_ts",
            (v["trip_id"], v["dan"], v["ts"], v["lat"], v["lon"], v["smer"], v["vozilo"]))
        zapisanih += 1
        prehodov += _iz_lege(conn, v, derp, zdaj)
    # Kot `collector.ingest_positions`: ob izpadu derp.si briše le ta nit.
    conn.execute("DELETE FROM vehicle_now WHERE seen_ts < ?", (int(zdaj) - 3600,))
    return {"zapisanih": zapisanih, "prehodov": prehodov}


def _iz_lege(conn: sqlite3.Connection, v: dict, derp: dict | None, zdaj: float) -> int:
    """Zamuda iz lege vozila: samo, kadar ga derp.si nima ali vodi NAP."""
    if (derp is not None and v["vozilo"] in derp
            and not iz_lege.nap_vodi(v.get("agency"), zdaj)):
        return 0
    if config.ZAMUDA_IZ_LEGE and iz_lege.brez_feeda(v["trip_id"], zdaj):
        return iz_lege.opazuj(conn, v["trip_id"], v["dan"], v["ts"],
                              v["lat"], v["lon"], v["vozilo"])
    return 0


def _v_dosje(vozila: list[dict], pripeta: list[dict], za_senco: list, surovo: dict,
             derp: dict | None, zdaj: float) -> None:
    """Vsako vozilo iz odgovora, s tem, kaj je NAP rekel in kaj smo naredili."""
    razlogi: dict[str, list[str]] = {}
    for v, _, razlog in za_senco:
        razlogi.setdefault(v["vozilo"], []).append(razlog)
    nase = {v["vozilo"]: v for v in pripeta}
    for v in vozila:
        s = surovo.get(v["vozilo"])
        if s is None:
            continue
        p = nase.get(v["vozilo"])
        r = list(razlogi.get(v["vozilo"], ()))
        if p is None and not r:
            r.append("ni_avtobus")          # `pripni`: vožnja ni avtobusna
        if s["popravljen"]:
            r.append("ura_popravljena")
        d = derp.get(v["vozilo"]) if derp else None
        if d is not None and d[0] != v["ijpp"]:
            r.append("vira_razlicna")
        dosje.opazi("nap", v["vozilo"], v["ts"], v["lat"], v["lon"],
                    trip_id=p["trip_id"] if p else None, dan=p["dan"] if p else None, razlogi=r,
                    kljuc=s["kljuc"], telo=s["telo"], sprotno=s["sprotno"], zdaj=zdaj)


def korak(conn: sqlite3.Connection, vsebina: bytes, zdaj: float) -> dict:
    """En odgovor NAP: razberi, primerjaj, pripni, zapiši, povzemi v `meta`."""
    surovo: dict | None = {} if dosje.vklopljen() else None
    vozila, st = razberi(vsebina, zdaj, surovo)
    derp = collector.lege_derp(zdaj, DERP_SVEZE_S)
    st.update(primerjaj(vozila, derp))
    za_senco: list = []
    pripeta, s = pripni(conn, vozila, zdaj, za_senco)
    st.update(s)
    # NAP vodi (derp.si za medkrajevne utihne, `iz_lege.nap_vodi`) samo, kadar
    # res kaj da. Prazen, zamrznjen ali nepripet odgovor 200 je prej vodil in
    # derp.si se ni vklopil -- medkrajevni brez zamud (presoja 31. 10. 2026).
    # Ponoči je pripetih nič po pravici; takrat derp.si tudi nima česa dati.
    if pripeta:
        iz_lege.nap_prebran(zdaj)
    st.update(zapisi(conn, pripeta, derp, zdaj))
    if surovo is not None:
        dosje.varno(_v_dosje, vozila, pripeta, za_senco, surovo, derp, zdaj)
    # Za `zapisi`: zaklep za pisanje že drži, senca ne čaka na bazo. Napaka v
    # njej ne sme razveljaviti leg (`teci` ob izjemi naredi rollback).
    try:
        st["senca"] = senca.opazuj(conn, za_senco, pripeta, derp, zdaj)
    except Exception as exc:                # noqa: BLE001
        st["senca"] = {"napaka": f"{type(exc).__name__}: {exc}"[:200]}
    st.update(ts=int(zdaj), bajtov=len(vsebina),
              gps={**prehod.stevci, "nacin": config.PREHOD_GPS})
    db.set_meta(conn, "nap", json.dumps(st, sort_keys=True))
    # Ključ predpomnilnika `/api/vehicles`: brez tega ob izpadu derp.si
    # zemljevid NAP-ovih leg ne bi videl nikoli.
    db.set_meta(conn, "positions_fetched", str(int(zdaj)))
    iz_lege.pospravi(zdaj, conn)
    conn.commit()
    return st


def beri(seja: requests.Session, prijava_: tuple[str, str]) -> bytes:
    cas = datetime.now(TZ).isoformat()
    with viri.branje("nap") as b:
        r = seja.post(config.NAP_URL, data=_ZAHTEVEK.format(cas=cas).encode(),
                      headers={"Content-Type": "application/xml"},
                      auth=prijava_, timeout=TIMEOUT_S)
        b.http = r.status_code
        if r.status_code in (401, 403):
            raise NiDostopa(r.status_code)
        r.raise_for_status()
        b.bajtov = len(r.content)
    return r.content


def teci(stop: threading.Event, log: Callable[[str], None]) -> None:
    """Svoja nit: tuj strežnik ne sme zamikati zajema derp.si."""
    conn = db.connect()
    seja = requests.Session()
    seja.headers["User-Agent"] = config.USER_AGENT
    napak, brez_prijave = 0, False
    zavrnjenih, uspeh_ts = 0, 0.0
    try:
        while not stop.is_set():
            zacetek = time.time()
            p = prijava()
            if p is None:
                if not brez_prijave:
                    log("NAP: prijave ni (deploy/nap.sh), lege samo z derp.si")
                    viri.caka("nap", "prijave ni: na strežniku `deploy/nap.sh`")
                brez_prijave = True
                stop.wait(60)
                continue
            if brez_prijave:
                viri.caka("nap", None)
            brez_prijave = False
            cakaj = config.NAP_SECONDS
            try:
                korak(conn, beri(seja, p), time.time())
                if napak:
                    log(f"NAP spet odgovarja (po {napak} napakah)")
                napak, zavrnjenih, uspeh_ts = 0, 0, time.time()
            except Exception as exc:        # noqa: BLE001 -- vir ni naš
                conn.rollback()             # glej `zamude_sz.teci()`
                napak += 1
                if napak == 1:
                    log(f"NAP: {exc}")
                http = getattr(exc, "http", None)
                if http:
                    zavrnjenih += 1
                    cakaj = cakaj_po_zavrnitvi(zavrnjenih, time.time() - uspeh_ts)
                if isinstance(exc, sqlite3.OperationalError) and "locked" in str(exc):
                    # Bazo drži drug pisec, vir odgovarja. Zapis napake v
                    # `meta` bi na isti zaklep čakal še 30 s.
                    iz_lege.nap_zaklenjen()
                else:
                    try:
                        s = json.loads(db.get_meta(conn, "nap") or "{}")
                        s.update(napaka=str(exc)[:200], napaka_ts=int(time.time()), http=http)
                        db.set_meta(conn, "nap", json.dumps(s, sort_keys=True))
                        conn.commit()
                    except sqlite3.Error:
                        conn.rollback()
            stop.wait(max(1.0, cakaj - (time.time() - zacetek)))
    finally:
        conn.close()
