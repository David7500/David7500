"""Viri podatkov: kaj beremo, od koga, kako pogosto -- in ali ta hip odgovarja.

Do 9. 10. 2026 je bil vsak vir zapisan drugje: naslov v `config`, ritem v
`server`, meja zdravja v `zdravje`, seznam za preverjanje v `opozorila`,
opis v `admin.js`, vsakič z drugim imenom. NAP (8. 10.) je pomenil pet mest,
pregled pa ga je pokazal kot dve vrstici med triindvajsetimi. Kadar vir ni
odgovarjal, je bil vzrok samo v dnevniku strežnika -- do tega skrbnik s
telefona ne pride.

Zdaj je vsak vir opisan enkrat, tu (`vsi()`), in vsak klic na tuj strežnik
gre skozi `branje()`. Pregled, preverjanje dosegljivosti v pošti in zavihek
„Viri“ v /admin berejo oboje od tu.

**Dnevnik branj je v pomnilniku procesa, ne v bazi.** Pove, kaj vidi TA
proces; po ponovnem zagonu začne prazen, in prav to mora pregled vedeti --
prejšnji proces je lahko imel nit, ki je ta nima (stara `napaka_ts` v bazi je
po zagonu kazala „ne odgovarja pred 3 h“, čeprav nit še ni niti poskusila).
Kar mora preživeti zagon -- kdaj je vir nazadnje kaj zapisal -- je v bazi
(`zapisano()`). Brez zapisa v bazo tudi ostane: branje leg na 10 s bi sicer
pomenilo pisanje na 10 s samo zato, da ga kdo kdaj pogleda.
"""
from __future__ import annotations

import statistics
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Callable

import requests

from . import brskalnik, config

#: Skupine v vrstnem redu, v katerem jih pokaže pregled.
SKUPINE = (
    ("zivo", "derp.si — posrednik"),
    ("izvirniki", "Izvirniki in drugi viri"),
    ("dodatki", "Dodatki za prikaz"),
    ("statika", "Vozni red in vreme"),
)


@dataclass(frozen=True)
class Vir:
    kljuc: str
    ime: str
    skupina: str
    #: Kaj daje, en stavek -- po njem skrbnik ve, kaj potnik izgubi.
    kaj: str
    #: Kakšno vlogo ima ob drugih virih: glavni, rezerva, primerjava.
    vloga: str
    naslov: str
    #: Kdo podatek ustvari in kdo ga posreduje. Navedba vira je pogoj licence.
    izvor: str
    licenca: str
    ritem: str
    #: Nit, ki vir bere; brez nje vir bere zahteva obiskovalca.
    nit: str | None
    vklopljen: bool
    #: Ključi iz `zdravje.ocena()`, ki pobarvajo ta vir. Prazno = splošno
    #: pravilo iz dnevnika branj (`vir:<ključ>`).
    zdravje: tuple[str, ...]
    #: Kaj storiti, kadar ne dela. Pregled ga pokaže samo takrat.
    ukrep: str
    #: Naslov za preverjanje dosegljivosti (GET, samo glava) ali None.
    preveri: str | None = None
    #: Kode >= 400, ki vseeno pomenijo „strežnik je tu“: NAP brez prijave 401,
    #: potniski.sz.si brez brskalnika 403 (Cloudflare).
    preveri_ok: tuple[int, ...] = ()
    #: Zaporednih napak, preden je vir rumen (splošno pravilo). Dnevni vir
    #: že ob eni: naslednji poskus je šele jutri.
    prag_napak: int = 3


def _zamude_sz_pot() -> str:
    # Uvoz ob klicu: `zamude_sz` uvozi ta modul.
    from .zamude_sz import AKTIVNI
    return AKTIVNI


def _okolje_vklop(ime: str) -> bool:
    return config.okolje(ime, "1") != "0"


def vsi() -> tuple[Vir, ...]:
    """Vsi viri, kot jih ta proces bere. Zgrajeno ob klicu, ne ob uvozu:
    nastavitve se berejo iz okolja in preizkusi jih menjajo."""
    poll = int(config.okolje("POLL_SECONDS", config.POLL_SECONDS))
    lege = int(config.okolje("POSITION_SECONDS", config.POSITION_SECONDS))
    ovire = int(config.okolje("ALERT_SECONDS", "60"))
    osvezi = (config.okolje("REFRESH", "off") or "off").lower()
    ura = config.okolje("REFRESH_HOUR", "4")
    vozni_red = ("osveževanje izklopljeno (KAJROS_REFRESH=off)" if osvezi == "off"
                 else f"dnevno ob {ura}:20" + (", v podprocesu" if osvezi == "subprocess" else ""))
    vreme_ura = config.okolje("WEATHER_HOUR", "5")
    # Vlake derp.si dobi z zemljevida SŽ prek posrednika api.modra.ninja
    # (`derp-si/ijpp-rt`, `szService.js`, prebrano 8. 10. 2026), avtobuse iz
    # NAP. Isti zemljevid beremo sami (`zamude_sz`), zato derp.si vlake piše le
    # še, kadar našega branja ni.
    derp = "DERP (derp.si): avtobusi iz NAP, vlaki z zemljevida SŽ prek api.modra.ninja"
    derp_ukrep = ("Izpad je skoraj vedno pri derp.si, ne pri nas — „Preveri vire“ "
                  "pove, ali odgovarja in ali imamo internet. Rezerve tečejo same: "
                  "NAP za medkrajevne, LPP-jevi zasloni za mestni LPP, zemljevid SŽ "
                  "za vlake. Obvestilo potnikom nastane samo po 20 min.")
    brskalnik_ukrep = ("Stran SŽ beremo s Chromom (`brskalnik.py`). „ni Chroma“ ali "
                       "„ni zaslona“: na arwenu `deploy/brskalnik.sh` (namesti Chrome "
                       "in Xvfb, rabi sudo). „Cloudflare ne spusti“: brskalnik se "
                       "ob naslednjem branju zažene znova s praznim profilom; če "
                       "ostane, SŽ je zaostril zaščito — glej MERITVE (10. 10. 2026). "
                       "Vrstica „brskalnik“ spodaj pove, ali teče in koliko izzivov je rešil.")
    return (
        Vir("derp_zamude", "derp.si · zamude IJPP", "zivo",
            "Zamude IJPP (GTFS-RT): avtobusne računa derp.si sam (TransitClock), "
            "vlakov z zemljevida SŽ od 7. 10. 2026 nima.",
            "glavni vir zamud primestnega LPP; vlake piše, kadar zemljevid SŽ ni prebran",
            config.TRIP_UPDATES_URL, derp, "CC BY-SA 4.0",
            f"vsakih {poll} s", "kajros-collector", True, ("derp_ijpp",), derp_ukrep,
            preveri=config.TRIP_UPDATES_URL),
        Vir("derp_lege", "derp.si · lege IJPP", "zivo",
            "Lege avtobusov z GPS; vlakov ni.",
            "lege primestnega LPP; Arrivo, Nomago in AP MS ima NAP svežejše",
            config.VEHICLE_POSITIONS_URL,
            "DERP (derp.si) iz NAP; primestni LPP od LPP (NAP ga nima)", "CC BY-SA 4.0",
            f"vsakih {lege} s", "kajros-collector", _okolje_vklop("POSITIONS"), (),
            derp_ukrep, preveri=config.VEHICLE_POSITIONS_URL),
        Vir("derp_ovire", "derp.si · obvestila IJPP", "zivo",
            "Ovire na progi in nadomestni prevozi (SZ-OVIRA); poročila o zamudi "
            "(SZ-DELAY) le, kadar zemljevid SŽ ni prebran.",
            "edini vir ovir in nadomestnih prevozov",
            config.SERVICE_ALERTS_URL,
            "DERP (derp.si) iz potniski.sz.si prek api.modra.ninja", "CC BY-SA 4.0",
            "izklopljeno" if ovire <= 0 else f"vsakih {ovire} s",
            "kajros-collector", ovire > 0, (), derp_ukrep,
            preveri=config.SERVICE_ALERTS_URL),
        Vir("derp_lpp", "derp.si · mestni LPP", "zivo",
            "Zamude, lege in obvozi mestnih linij LPP v enem feedu.",
            "glavni vir mestnega LPP",
            config.LPP_RT_URL, "DERP (derp.si) iz data.lpp.si, s ključem LPP",
            "CC BY-SA 4.0",
            f"vsakih {poll} s", "kajros-collector", config.LPP_ENABLED, ("derp_lpp",),
            derp_ukrep, preveri=config.LPP_RT_URL),
        Vir("nap", "NAP · lege SIRI", "izvirniki",
            "Lege medkrajevnih avtobusov naravnost z NAP, izvirnik tistega, kar "
            "derp.si pretvori.",
            "vodi lege in zamude Arrive, Nomaga in AP MS; ob molku prevzame derp.si",
            config.NAP_URL, "NAP (b2b.nap.si), naprave na vozilih prek Realisa",
            "CC BY-SA 4.0", f"vsakih {config.NAP_SECONDS} s", "kajros-nap", config.NAP,
            ("nap",),
            "HTTP 401 ali 403: NAP prijave ne sprejme — na arwenu `deploy/nap.sh` "
            "(novo geslo) ali odobritev vsebine na nap.si. Drugače počakaj: lege "
            "in zamude medtem spet piše derp.si.",
            preveri=config.NAP_URL, preveri_ok=(401, 403, 405)),
        Vir("zamude_sz", "zemljevid SŽ", "izvirniki",
            "Zamude vseh vlakov z zemljevida potniski.sz.si, po številki vlaka; "
            "beremo ga sami, s Chromom.",
            "vodi zamude vlakov; ko ni prebran 2 min, jih spet piše derp.si "
            "(isti zemljevid prek posrednika)",
            f"{brskalnik.IZVOR}{_zamude_sz_pot()}", "SŽ (potniski.sz.si), brez posrednika",
            "ni navedena", f"vsakih {config.SZ_ZAMUDE_SECONDS} s",
            "kajros-zamude-sz", config.SZ_ZAMUDE, ("zamude_sz",), brskalnik_ukrep,
            preveri=brskalnik.ZACETNA, preveri_ok=(403,)),
        Vir("zamude_lpp", "LPP · zasloni postajališč", "izvirniki",
            "Prihodi z LPP-jevih zaslonov na ~75 postajališčih, pripeti na vožnje.",
            "rezerva za mestni LPP, kadar ga derp.si nima; sicer primerjava",
            "https://data.lpp.si/api/station/arrival", "LPP (data.lpp.si)",
            "ni navedena", f"obhod vsaki {config.LPP_ZAMUDE_SECONDS // 60} min",
            "kajros-zamude-lpp", config.LPP_ZAMUDE, ("zamude_lpp",),
            "data.lpp.si ne odgovarja: počakaj. Tabla kaže vozni red, dokler "
            "derp.si dela, potnik ne izgubi ničesar.",
            preveri="https://data.lpp.si/api/station/arrival?station-code=600011"),
        Vir("peroni", "tabla SŽ · tiri", "dodatki",
            "Tir vlaka na postaji s table prihodov in odhodov.",
            "dodatek: star ali manjkajoč tir se ne pokaže",
            f"{brskalnik.IZVOR}/odhodi-in-prihodi-na-postaji/",
            "SŽ (potniski.sz.si), brez posrednika", "ni navedena",
            f"velike postaje vsakih {config.PERONI_SECONDS // 60} min, male do 2 h",
            "kajros-peroni", config.PERONI, (),
            "Tir je dodatek, ki sme izginiti. " + brskalnik_ukrep,
            preveri=brskalnik.ZACETNA, preveri_ok=(403,)),
        Vir("lpp_zivo", "LPP · prihodi za prikaz", "dodatki",
            "Živa napoved prihoda mestnega LPP v oknu vožnje in na tabli.",
            "samo prikaz, v bazo ne gre nič",
            "https://data.lpp.si/api/", "LPP (data.lpp.si)", "ni navedena",
            "ob zahtevi obiskovalca, predpomnjeno 15 s", None,
            config.LPP_ENABLED and config.LPP_ZIVO, (),
            "Stran deluje naprej z derp.si; počakaj.",
            preveri="https://data.lpp.si/api/station/station-details"),
        Vir("gtfs_ijpp", "vozni red IJPP", "statika",
            "Vozni red vseh prevoznikov v IJPP (zip, ~41 MB).",
            "edini vir voznega reda vlakov in medkrajevnih avtobusov",
            config.GTFS_URL, "DUJPP, zip sestavi DERP (gitlab)", "CC BY-SA 4.0",
            vozni_red, "kajros-collector", True, ("vozni_red",),
            "Uvoz ne teče: na arwenu `journalctl -u kajros` okoli 4:20. Ročno: "
            "`KAJROS_AGENCIES=1118,1119,1121,1123 kajros update`. Zip brez "
            "prevoznika ali s tujimi trasami se zavrne sam (zajem.md).",
            preveri=config.GTFS_URL, prag_napak=1),
        Vir("gtfs_lpp", "vozni red LPP", "statika",
            f"Vozni red mestnih linij LPP, okno {config.LPP_DAYS} dni naprej.",
            "edini vir voznega reda mestnega LPP",
            config.LPP_GTFS_URL, "LPP (avl.lpp.si)", "ni navedena",
            vozni_red, "kajros-collector", config.LPP_ENABLED, ("vozni_red_lpp",),
            f"Okno je {config.LPP_DAYS} dni: ko poteče, mestnih linij ni več na "
            "nobeni strani. Na arwenu `journalctl -u kajros` okoli 4:20; ročno "
            "`kajros update`.",
            preveri=config.LPP_GTFS_URL, prag_napak=1),
        Vir("vreme", "vreme · Open-Meteo", "statika",
            "Vreme po celicah 0,1° za vsako uro, za nazaj iz arhiva.",
            "samo prikaz ob zamudi",
            "https://api.open-meteo.com/v1/forecast", "Open-Meteo", "CC BY 4.0",
            f"dnevno ob {vreme_ura}:10, zadnji trije dnevi", "kajros-collector",
            _okolje_vklop("WEATHER"), (),
            "Ni nujno: `kajros weather` dopolni za nazaj kadarkoli.",
            preveri="https://api.open-meteo.com/v1/forecast", prag_napak=1),
    )


def po_kljucu() -> dict[str, Vir]:
    return {v.kljuc: v for v in vsi()}


# --- dnevnik branj --------------------------------------------------------

#: Branja zadnje ure za vsak vir. Najgostejši vir (lege, NAP) bere na 10 s,
#: prikaz LPP ob vsaki zahtevi; meja drži pomnilnik omejen tudi ob navalu.
_NAJVEC_BRANJ = 5000
_URA_S = 3600


@dataclass
class _Stanje:
    uspeh_ts: float | None = None
    napaka_ts: float | None = None
    napaka: str | None = None
    http: int | None = None
    zaporednih: int = 0
    ms: int | None = None
    bajtov: int | None = None
    nespremenjeno: bool = False
    opomba: str | None = None
    izpad_od: float | None = None
    #: Zakaj nit ta hip ne bere, čeprav teče (ni prijave, noč, čaka na
    #: derp.si). Brez tega je „v tem zagonu še nobenega branja“ uganka.
    caka: str | None = None
    caka_ts: float | None = None
    branja: deque = field(default_factory=lambda: deque(maxlen=_NAJVEC_BRANJ))


_stanje: dict[str, _Stanje] = {}
_dogodki: deque = deque(maxlen=200)
_kljucavnica = threading.Lock()

#: Postavi ga `server.lifespan`, ko zažene niti zajema. Šele tedaj je
#: manjkajoča nit okvara -- pri `KAJROS_COLLECTOR=0` in v preizkusih je ni.
zajem_zagnan = False


class Branje:
    """Kar klicatelj ve o enem branju in ga dnevnik ne more uganiti."""
    __slots__ = ("http", "bajtov", "nespremenjeno", "opomba")

    def __init__(self):
        self.http = self.bajtov = self.opomba = None
        self.nespremenjeno = False


def opis_napake(exc: BaseException, povezava_s: float | None = None,
                odgovor_s: float | None = None) -> str:
    """Napaka po človeško: kaj je šlo narobe, ne kje v knjižnici."""
    rex = requests.exceptions
    if isinstance(exc, rex.ConnectTimeout):
        return f"ni povezave v {povezava_s:g} s" if povezava_s else "ni povezave (časovna meja)"
    if isinstance(exc, rex.ReadTimeout):
        return (f"povezava je, odgovora ni v {odgovor_s:g} s" if odgovor_s
                else "povezava je, odgovora ni (časovna meja)")
    if isinstance(exc, rex.ConnectionError):
        s = str(exc)
        if "resolve" in s or "NameResolution" in s:
            return "ime se ne razreši (DNS)"
        if "refused" in s.lower():
            return "zavrača povezave"
        return "povezava pade"
    if isinstance(exc, rex.HTTPError) and exc.response is not None:
        return f"odgovori {exc.response.status_code}"
    if isinstance(exc, rex.RequestException):
        return f"napaka {type(exc).__name__}"
    s = str(exc).strip()
    # Naše napake (`RuntimeError`) povedo vse v besedilu; tuje (razbor
    # protobufa, JSON) brez imena vrste ne povedo, kaj se je zgodilo.
    if isinstance(exc, RuntimeError) and s:
        return s[:200]
    return f"{type(exc).__name__}: {s}"[:200] if s else type(exc).__name__


def _http(exc: BaseException) -> int | None:
    odgovor = getattr(exc, "response", None)
    if odgovor is not None and getattr(odgovor, "status_code", None):
        return odgovor.status_code
    return getattr(exc, "http", None)


def _zapisi(kljuc: str, ok: bool, ms: int, b: Branje, napaka: str | None = None,
            http: int | None = None, zdaj: float | None = None) -> None:
    zdaj = time.time() if zdaj is None else zdaj
    with _kljucavnica:
        s = _stanje.setdefault(kljuc, _Stanje())
        s.branja.append((zdaj, ok, ms, b.bajtov or 0))
        s.ms, s.http = ms, (b.http if ok else http)
        s.caka = s.caka_ts = None           # bere, torej ne čaka več
        prag = _prag(kljuc)
        if ok:
            if s.izpad_od is not None:
                _dogodki.append({"ts": zdaj, "kljuc": kljuc, "ok": True,
                                 "besedilo": f"spet odgovarja po {s.zaporednih} napakah, "
                                             f"{_trajanje(zdaj - s.izpad_od)}"})
            s.uspeh_ts, s.zaporednih, s.izpad_od = zdaj, 0, None
            s.bajtov, s.nespremenjeno, s.opomba = b.bajtov, b.nespremenjeno, b.opomba
        else:
            s.napaka_ts, s.napaka = zdaj, napaka
            s.zaporednih += 1
            # Dogodek šele ob pragu: ena izgubljena tabla med 266 postajami
            # ali en počasen odgovor LPP ni izpad, ki bi ga bilo treba brati.
            if s.zaporednih == prag:
                s.izpad_od = zdaj
                _dogodki.append({"ts": zdaj, "kljuc": kljuc, "ok": False,
                                 "besedilo": f"ne odgovarja: {napaka}"})


_PRAGOVI: dict[str, int] = {}


def _prag(kljuc: str) -> int:
    # Prag je lastnost vira, ne nastavitev: vsi() se ob vsakem branju ne
    # gradi znova (prikaz LPP bere ob vsaki zahtevi obiskovalca).
    if not _PRAGOVI:
        _PRAGOVI.update({v.kljuc: v.prag_napak for v in vsi()})
    return _PRAGOVI.get(kljuc, 3)


@contextmanager
def branje(kljuc: str | None):
    """Ovij en klic na tuj strežnik. Napako zapiše in jo spusti naprej --
    kaj ob njej storiti, ve klicatelj, ne dnevnik."""
    b = Branje()
    if kljuc is None:
        yield b
        return
    t = time.monotonic()
    try:
        yield b
    except Exception as exc:
        _zapisi(kljuc, False, round((time.monotonic() - t) * 1000), b,
                opis_napake(exc), _http(exc))
        raise
    _zapisi(kljuc, True, round((time.monotonic() - t) * 1000), b)


def caka(kljuc: str, razlog: str | None, zdaj: float | None = None) -> None:
    """Nit vira teče, a namenoma ne bere -- in zakaj. `None` pobriše."""
    with _kljucavnica:
        s = _stanje.setdefault(kljuc, _Stanje())
        if razlog != s.caka:
            s.caka, s.caka_ts = razlog, (time.time() if zdaj is None else zdaj) if razlog else None


def shrani(conn, kljuc: str) -> None:
    """Stanje vira v `meta`, za vire, ki berejo redko ali v drugem procesu.

    Vozni red bere enkrat na dan, na arwenu v podprocesu (`KAJROS_REFRESH=
    subprocess`): dnevnik strežnika njegovega branja ne vidi nikoli, po
    ponovnem zagonu pa do jutra niti vremena ne. Zapis je en ključ na dan.
    """
    import json
    with _kljucavnica:
        s = _stanje.get(kljuc)
        if s is None:
            return
        d = {k: getattr(s, k) for k in s.__dataclass_fields__ if k != "branja"}
    try:
        conn.execute("INSERT INTO meta(key, value) VALUES(?, ?) "
                     "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                     (f"vir:{kljuc}", json.dumps(d, ensure_ascii=False)))
        conn.commit()
    except Exception:  # noqa: BLE001 -- samo za pregled; napaka branja je pomembnejša
        conn.rollback()


def _shranjeno(conn, kljuc: str) -> dict | None:
    import json
    r = conn.execute("SELECT value FROM meta WHERE key = ?", (f"vir:{kljuc}",)).fetchone()
    try:
        return json.loads(r[0]) if r and r[0] else None
    except ValueError:
        return None


def _trajanje(s: float) -> str:
    m = round(s / 60)
    return f"{m} min" if m < 60 else f"{m // 60} h {m % 60} min"


def dnevnik(zdaj: float | None = None) -> dict[str, dict]:
    """Posnetek dnevnika: zadnje stanje in zadnja ura za vsak brani vir."""
    zdaj = time.time() if zdaj is None else zdaj
    out = {}
    with _kljucavnica:
        for kljuc, s in _stanje.items():
            ura = [x for x in s.branja if x[0] >= zdaj - _URA_S]
            d = {k: getattr(s, k) for k in s.__dataclass_fields__ if k != "branja"}
            d["ura"] = {
                "branj": len(ura), "napak": sum(not ok for _, ok, _, _ in ura),
                "ms_mediana": round(statistics.median(ms for _, _, ms, _ in ura)) if ura else None,
                "bajtov": sum(b for _, _, _, b in ura),
            }
            out[kljuc] = d
    return out


def dogodki(n: int = 60) -> list[dict]:
    with _kljucavnica:
        return list(_dogodki)[-n:][::-1]


def pozabi() -> None:
    """Za preizkuse: dnevnik začne prazen."""
    with _kljucavnica:
        _stanje.clear()
        _dogodki.clear()


def niti() -> list[str]:
    return sorted(t.name for t in threading.enumerate() if t.is_alive())


def pricakovane_niti() -> dict[str, list[str]]:
    """Nit -> viri, ki jih bere. Samo vklopljeni in samo, kadar zajem teče."""
    if not zajem_zagnan:
        return {}
    out: dict[str, list[str]] = {}
    for v in vsi():
        if v.nit and v.vklopljen:
            out.setdefault(v.nit, []).append(v.kljuc)
    return out


# --- kdaj je vir nazadnje kaj zapisal (v bazi) ----------------------------


def _meta_ts(conn, kljuc: str) -> int | None:
    r = conn.execute("SELECT value FROM meta WHERE key = ?", (kljuc,)).fetchone()
    try:
        return int(r[0]) if r and r[0] else None
    except ValueError:
        return None


def _meta_json_ts(conn, kljuc: str) -> int | None:
    import json
    r = conn.execute("SELECT value FROM meta WHERE key = ?", (kljuc,)).fetchone()
    try:
        return (json.loads(r[0]) or {}).get("ts") if r and r[0] else None
    except ValueError:
        return None


def _uvoz_ts(conn) -> int | None:
    r = conn.execute("SELECT value FROM meta WHERE key = 'gtfs_imported_at'").fetchone()
    try:
        return int(datetime.fromisoformat(r[0]).timestamp()) if r and r[0] else None
    except ValueError:
        return None


def _ena(conn, sql: str, *arg) -> int | None:
    try:
        r = conn.execute(sql, arg).fetchone()
    except Exception:  # noqa: BLE001 -- tabele vira še ni (peroni brez niti)
        return None
    return int(r[0]) if r and r[0] else None


#: Kdaj je vir nazadnje kaj zapisal -- preživi zagon. Lege derp.si nimajo
#: svojega žiga (`positions_fetched` premakne tudi NAP), prikaz LPP ne piše.
_ZAPISANO: dict[str, Callable] = {
    "derp_zamude": lambda c, z: _meta_ts(c, "rt_fetched"),
    "derp_lpp": lambda c, z: _meta_ts(c, "lpp_rt_fetched"),
    "derp_ovire": lambda c, z: _ena(c, "SELECT MAX(last_seen) FROM alert"),
    "nap": lambda c, z: _meta_json_ts(c, "nap"),
    "zamude_sz": lambda c, z: _meta_json_ts(c, "zamude_sz"),
    "zamude_lpp": lambda c, z: _meta_json_ts(c, "zamude_lpp"),
    "peroni": lambda c, z: _ena(c, "SELECT MAX(preverjeno) FROM peron_postaja"),
    "gtfs_ijpp": lambda c, z: _uvoz_ts(c),
    "gtfs_lpp": lambda c, z: _uvoz_ts(c),
    # Po indeksu ure, ne `MAX(fetched_at)` čez vso tabelo.
    "vreme": lambda c, z: _ena(c, "SELECT MAX(fetched_at) FROM weather WHERE hour_ts >= ?",
                               int(z) - 5 * 86400),
}


def zapisano(conn, kljuc: str, zdaj: float) -> int | None:
    f = _ZAPISANO.get(kljuc)
    return f(conn, zdaj) if f else None


# --- pregled --------------------------------------------------------------

_RANG = {"je-slaba": 3, "je-mlacna": 2, "je-dobra": 1, "": 0}


def pregled(conn, ocena: dict[str, tuple[str, str]], zdaj: float | None = None) -> list[dict]:
    """Vsi viri za /admin: opis, dnevnik, zadnji zapis in barva.

    Barvo računa `zdravje.ocena()` (isto kot pošta); tu se le zbere po viru:
    njegovi ključi, splošno pravilo `vir:<ključ>` in nit, ki ga bere.
    """
    zdaj = time.time() if zdaj is None else zdaj
    dn = dnevnik(zdaj)
    zive = set(niti())
    out = []
    for v in vsi():
        ocene = [ocena[k] for k in (v.zdravje or (f"vir:{v.kljuc}",)) if k in ocena]
        # Živa nit ne pomeni zdravega vira -- NAP brez prijave teče in ne
        # bere nič. Nit vir pobarva samo, kadar ne teče.
        nit = ocena.get(f"nit:{v.nit}") if v.nit else None
        if nit and nit[0] == "je-slaba":
            ocene.append(nit)
        razred = max((r for r, _ in ocene), key=lambda r: _RANG.get(r, 0), default="")
        if not v.vklopljen:
            razred = ""
        d = dn.get(v.kljuc)
        # Vir, ki ga ta proces še ni bral (dnevni, ali bere podproces): zadnje
        # shranjeno stanje, z oznako, da ni iz tega procesa.
        if (d is None or d.get("uspeh_ts") is None and d.get("napaka_ts") is None) and v.vklopljen:
            shranjeno = _shranjeno(conn, v.kljuc)
            if shranjeno:
                d = {**shranjeno, "caka": (d or {}).get("caka"), "caka_ts": (d or {}).get("caka_ts"),
                     "ura": None, "iz_baze": True}
        out.append({
            **asdict(v),
            "razred": razred,
            "razlogi": [r for raz, r in ocene if r and raz in ("je-slaba", "je-mlacna")],
            "dnevnik": d,
            "zapisano": zapisano(conn, v.kljuc, zdaj) if v.vklopljen else None,
            "nit_tece": (v.nit in zive) if v.nit else None,
        })
    return out


# --- preverjanje dosegljivosti --------------------------------------------

#: Pošta ne sme stati minute na vir: vsi gredo hkrati, najdlje toliko,
#: kolikor ti dve meji skupaj.
POVEZAVA_S, ODGOVOR_S = 10, 20
#: Neodvisen naslov: kadar tudi ta ne odgovori, ni interneta na strežniku.
KONTROLA = ("internet (cloudflare.com)", "https://www.cloudflare.com/cdn-cgi/trace")


def preveri(url: str, get: Callable = requests.get,
            ok_kode: tuple[int, ...] = ()) -> tuple[bool, str]:
    """(odgovarja, opis po človeško). Telesa ne bere: dovolj je, da pride
    glava -- vir, ki obvisi, obvisi že prej."""
    t = time.monotonic()
    try:
        r = get(url, headers={"User-Agent": config.USER_AGENT},
                timeout=(POVEZAVA_S, ODGOVOR_S), stream=True)
        r.close()
    except requests.RequestException as exc:
        return False, opis_napake(exc, POVEZAVA_S, ODGOVOR_S)
    if r.status_code >= 400 and r.status_code not in ok_kode:
        return False, f"odgovori {r.status_code}"
    cas = f"{time.monotonic() - t:.1f} s".replace(".", ",")
    if r.status_code in ok_kode:
        return True, f"dosegljiv v {cas} (brez prijave ali brskalnika odgovori {r.status_code})"
    return True, f"odgovori {r.status_code} v {cas}"


def preveri_vire(viri: list[Vir] | None = None, get: Callable = requests.get,
                 zdaj: float | None = None) -> dict:
    """Vsi vklopljeni viri in kontrola hkrati, s sklepom: pri njih ali pri nas."""
    viri = [v for v in (viri if viri is not None else vsi()) if v.vklopljen and v.preveri]
    naslovi = [(v.preveri, v.preveri_ok) for v in viri] + [(KONTROLA[1], ())]
    with ThreadPoolExecutor(len(naslovi)) as ex:
        izidi = list(ex.map(lambda n: preveri(n[0], get, n[1]), naslovi))
    internet = izidi[-1][0]
    padli = [v.ime for v, (ok, _) in zip(viri, izidi) if not ok]
    if not internet:
        sklep = "Strežnik ne pride niti do kontrole — verjetno nima interneta."
    elif padli:
        n = len(padli)
        koliko = ("vir ne odgovarja" if n == 1 else "dva vira ne odgovarjata" if n == 2
                  else f"{n} viri ne odgovarjajo" if n <= 4 else f"{n} virov ne odgovarja")
        sklep = (f"Internet dela, {koliko} ({', '.join(padli)}) — izpad je pri njih, "
                 "ne pri nas.")
    else:
        sklep = ("Vsi viri odgovarjajo. Če podatkov vseeno ni, so prazni ali pa je "
                 "napaka pri nas: journalctl -u kajros.service.")
    return {
        "ts": int(time.time() if zdaj is None else zdaj),
        "viri": [{"kljuc": v.kljuc, "ime": v.ime, "ok": ok, "opis": opis}
                 for v, (ok, opis) in zip(viri, izidi)],
        "kontrola": {"ime": KONTROLA[0], "ok": internet, "opis": izidi[-1][1]},
        "padli": padli,
        "sklep": sklep,
    }
