"""En sam proces: API in zajem zamud skupaj.

Zajem teče v ozadnji niti istega procesa, tako da ni treba voditi dveh
storitev. Na majhnem strežniku je to tudi cenejše -- en Python interpreter.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from . import alerts, collector, config, db, gtfs, ocena, stats, weather

TZ = ZoneInfo(config.TIMEZONE)
_stop = threading.Event()

#: Ali ta proces tudi strezhe. Postavi ga `lifespan` v `api.py`.
#:
#: Zajemna zanka je ISTA za streznik in za `kajros collect` -- torej tudi za
#: malino, ki samo polni bazo. Ogrevanje predpomnilnika odgovorov tam ne sme
#: teci: Pi Zero W je pri istem poslu ~100x pocasnejsi in bi si z ~1 s dela
#: na obhod podrl ritem zajema. Isti razlog, zakaj je tam ugasnjena `ocena`.
_strezemo = False


def _log(msg: str) -> None:
    print(f"{datetime.now(TZ):%H:%M:%S}  {msg}", flush=True)


def _ogrej_zive() -> None:
    """Po novem feedu izracunaj `/api/live` vnaprej, da nihce ne caka nanj.

    Predpomnilnik tega odgovora je vezan na `rt_fetched`, ki se spremeni ob
    vsakem zajemu -- torej vsakih 30 s. Zemljevid anketira z isto periodo, zato
    je doslej skoraj vsak njegov klic padel v prazen predpomnilnik in placal
    **1,3 s** (izmerjeno 4. 9. 2026: 822 ms avtobusi, 200 ms zeleznica, 802 ms
    oboje skupaj). Toplo pa je 19 ms.
    
    Dela je enako, le da ga opravi ta nit takoj po zajemu in ne uporabnik med
    cakanjem. Napaka tu ni kriticna -- odgovor se izracuna ob zahtevi kot prej.
    """
    if not _strezemo:
        return                   # `kajros collect`: odgovorov ni komu streci
    from . import api            # pozen uvoz: `api` uvozi `server`, ne obratno
    # Samo tisto, kar strani res vprasajo. Zemljevid klice
    # `/api/live?network=zeleznica`, pregled isto; `network=None` je 802 ms
    # dela za odgovor, ki ga aplikacija ne uporablja -- ogrevati ga pomeni
    # zamikati koristna dva.
    #
    # Zraven oba pregleda: `day_summary` je 200 ms pri zeleznici in 463 pri
    # avtobusih, `/api/overview*` pa ima isto znacko `rt_fetched` -- torej se
    # razveljavi vsakih 30 s in prvi obiskovalec po zajemu placa cel racun.
    # **Klici morajo iti skozi ENDPOINT, ne skozi notranjo funkcijo.**
    # `_live()` samo racuna; predpomnilnik napolni sele `api_live()`, ki ga
    # ovije v `_predpomni`. Prva razlicica tega ogrevanja je klicala `_live()`
    # -- delo je opravila in ga zavrgla, ucinka pa ni bilo nobenega.
    for kaj, klic in (("žive vožnje (železnica)", lambda: api.api_live("zeleznica")),
                      ("pregled (železnica)", api.api_overview),
                      ("žive vožnje (avtobusi)", lambda: api.api_live("avtobus")),
                      ("pregled (avtobusi)", api.api_overview_bus)):
        try:
            klic()
        except Exception as exc:  # noqa: BLE001
            _log(f"predpomnilnika ni bilo mogoče ogreti ({kaj}): {exc}")
            return


def _ogrej_health() -> None:
    """`/api/health` na svojem, mnogo počasnejšem ritmu.

    Ta odgovor ni vezan na značko, ampak samo na čas: TTL je 600 s. Ko poteče,
    ga plača prvi obiskovalec -- in to je vsak obisk katerekoli strani, ker
    `connections.js` kliče health za vrstico v nogi.

    Cena, izmerjena na prenosniku 6. 9. 2026 (19 081 voženj, 778 114 vrstic
    `run`, 5,3 mio `obs`): **2 683 ms**, od tega 2 390 ms sam razrez po
    omrežjih (`run JOIN trip`, 778 k iskanj po `trip_id`), 150 ms
    `COUNT(DISTINCT service_date)` in 124 ms `COUNT(*) obs`. Ostalo je pod
    50 ms skupaj. Prepis razreza v dve poizvedbi ne pomaga (2 258 ms) -- cena
    je sam pregled `run`, ne `COUNT(DISTINCT)`. Zožitev na en dan bi bila
    43 ms, a bi spremenila pomen: v nogi piše, koliko je zajetega **vsega**.

    Zato ne pocenimo poizvedbe, ampak preložimo, kdo jo plača. Vsakih 300 s
    je varno znotraj 600 s TTL, tudi če kak obhod zamudi.
    """
    if not _strezemo:
        return
    from . import api
    try:
        api.api_health()          # skozi endpoint, sicer se rezultat zavrže
    except Exception as exc:  # noqa: BLE001
        _log(f"predpomnilnika ni bilo mogoče ogreti (health): {exc}")


def _ogrej_pot() -> None:
    """Vozni red obeh omrežij v pomnilnik, preden ga kdo vpraša.

    Pot od vrat do vrat bere **obe omrežji hkrati**: 255 245 postankov, 94 MB,
    in na arwenu je prvi tak klic izmerjeno **15,3 s**. Topel je 0,6–1,6 s.
    Nalaganje se zgodi po vsakem zagonu in po vsakem uvozu voznega reda (žig
    razveljavi predpomnilnik), torej ravno takrat, ko ga nihče ne pričakuje.

    Poleg voznega reda še opis voženj, imena postajališč in peš poti — vse
    troje je statika dneva in skupaj nekaj sto milisekund.
    """
    if not _strezemo:
        return                   # `kajros collect`: odgovorov ni komu streci
    from . import hoja, journey, pot
    try:
        conn = db.connect()
        dan = journey.today()
        t = time.monotonic()
        by_trip, _ = journey._timetable_for_day(conn, dan, None)
        pot._vozje(conn, dan)
        pot._imena(conn)
        hoja.pespoti(conn)
        trajalo = (time.monotonic() - t) * 1000
        if trajalo > 1000:       # tiho, kadar je bilo ze toplo
            _log(f"vozni red za pot ogret: {len(by_trip)} voženj, {trajalo:.0f} ms")
    except Exception as exc:  # noqa: BLE001
        _log(f"voznega reda za pot ni bilo mogoče ogreti: {exc}")


def bootstrap() -> None:
    """Poskrbi, da baza obstaja in ima vozni red.

    Če je v paketu priložena pripravljena baza, jo uporabimo -- uvoz iz GTFS
    zipa pomeni 41 MB prenosa in nekaj minut na počasnem jedru. Obstoječe baze
    nikoli ne povozimo, sicer bi vsaka nova objava izbrisala zajeto zgodovino.
    """
    target = Path(config.DB_PATH)
    seed = Path(__file__).resolve().parent.parent / "seed" / "kajros.sqlite"
    if not target.exists() and seed.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(seed, target)
        _log(f"uporabljena priložena baza ({seed.stat().st_size / 1e6:.1f} MB)")

    conn = db.connect()
    db.init(conn)
    have = conn.execute("SELECT COUNT(*) FROM trip").fetchone()[0]
    if have:
        _log(f"vozni red pripravljen: {have} vlakov")
        return

    _log("voznega reda ni -- prenašam GTFS")
    path = gtfs.download(conn, force=True)
    lpp = gtfs.download_lpp(conn, force=True) if config.LPP_ENABLED else None
    if path:
        _log(f"uvažam {path.stat().st_size / 1e6:.0f} MB ...")
        _log(f"uvoženo: {gtfs.import_static(conn, path, lpp_zip=lpp)}")
        path.unlink(missing_ok=True)      # 41 MB ne rabimo obdržati
        if lpp:
            lpp.unlink(missing_ok=True)


def refresh_timetable(conn, mode: str) -> None:
    """Osveži vozni red. `mode`: off | inprocess | subprocess.

    Uvoz je najdražji trenutek v življenju procesa. Izmerjeno na tem paketu:
    v istem procesu vrh 89 MB (in ostane pri 85 MB, ker Python arene vrne
    operacijskemu sistemu redko), v podprocesu 54 MB poleg 57 MB starša.
    Na stroju s 100 MB torej nobena od obeh ni varna -- zato je privzeto `off`
    in vozni red osvežiš z novo priloženo bazo ali z `kajros update` drugje.
    """
    if mode == "off":
        return
    if mode == "subprocess":
        # Lasten naslovni prostor: ob koncu se ves pomnilnik vrne sistemu.
        proc = subprocess.run(
            [sys.executable, "-m", "kajros.cli", "update"],
            capture_output=True, text=True, timeout=1800,
        )
        _log(f"osvežitev (podproces): {proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else proc.stderr[-200:]}")
        return

    path = gtfs.download(conn)
    lpp = gtfs.download_lpp(conn) if config.LPP_ENABLED else None
    if path is None and lpp is None:
        _log("vozni red nespremenjen")
        return
    if path is None:
        path = config.DATA_DIR / "ijpp_gtfs.zip"
        if not path.exists():
            path = gtfs.download(conn, force=True)
    if lpp is None and config.LPP_ENABLED:
        kandidat = config.DATA_DIR / "lpp_gtfs.zip"
        lpp = kandidat if kandidat.exists() else None
    _log(f"nov vozni red: {gtfs.import_static(conn, path, lpp_zip=lpp)}")
    path.unlink(missing_ok=True)
    if lpp:
        lpp.unlink(missing_ok=True)


def _next_at(hour: int, minute: int) -> datetime:
    when = datetime.now(TZ).replace(hour=hour, minute=minute, second=0, microsecond=0)
    return when + timedelta(days=1) if when <= datetime.now(TZ) else when


def _worker(interval: int, refresh_hour: int, refresh_mode: str,
            weather_hour: int, alert_interval: int, maint_hour: int,
            summaries: bool = True,
            position_interval: int = config.POSITION_SECONDS) -> None:
    conn = db.connect()
    db.init(conn)
    # Sencno merjenje napovedi. Samo bere `run` in `sched` in pise v svojo
    # tabelo -- na zajem ne vpliva, zato tece v isti niti in ne v svoji.
    ocena.init(conn)
    meri_napovedi = config.okolje("OCENA", "1") != "0"
    # Lega vozil je smiselna samo, ce so v bazi avtobusi: feed nosi izkljucno
    # njih. Pri zeleznici bi bila to zahteva vsakih 30 s za prazen odgovor.
    has_bus = conn.execute("SELECT 1 FROM trip WHERE mode = 'bus' LIMIT 1").fetchone()
    track_vehicles = bool(has_bus) and config.okolje("POSITIONS", "1") != "0"
    next_refresh = None
    if refresh_mode != "off" and refresh_hour >= 0:
        next_refresh = _next_at(refresh_hour, 20)
    # Vreme se dopolnjuje za nazaj, ne sproti -- arhiv je na voljo sele naslednji
    # dan, zato vsakic pobere zadnje tri dni in s tem povozi vcerajsnjo napoved
    # z arhivsko vrednostjo.
    next_weather = _next_at(weather_hour, 10) if weather_hour >= 0 else None
    # Obvestila so vecji prenos od zamud in se pocasneje spreminjajo (razen
    # SZ-DELAY), zato imajo svoj, redkejsi ritem.
    next_alerts = 0.0 if alert_interval > 0 else float("inf")
    # Ob treh zjutraj je vceraj sklenjen, vlaki pa skoraj ne vozijo -- 34
    # sekund agregata takrat nikogar ne moti.
    next_maint = _next_at(maint_hour, 30) if maint_hour >= 0 else None
    # Ce povzetkov se ni (prva namestitev, nova sirina okna), jih zgradi ob
    # prvem obhodu -- sicer bi racun placal prvi obiskovalec strani, in pri
    # letu zajema je to 34 sekund cakanja.
    if (next_maint and summaries
            and not conn.execute("SELECT 1 FROM povzetek LIMIT 1").fetchone()):
        next_maint = datetime.now(TZ)

    # Zamude in lege imata SVOJ ritem, ker se feeda ne spreminjata enako:
    # vozilo objavi novo lego vsakih 20 s, zamuda pa se zapise sele ob
    # spremembi nad OBS_MIN_DELTA_S (60 s). Prej je oboje teklo na 30 s, kar
    # je lege bralo prepocasi -- pol nasega zaostanka na zaslonu je bilo tu.
    # Zanka zato tikne na krajsem od obeh, vsako opravilo pa ima svoj cas.
    next_trips = 0.0
    next_positions = 0.0 if track_vehicles else float("inf")
    next_lpp = 0.0 if config.LPP_ENABLED else float("inf")
    # Prvi obhod sele cez minuto: ob zagonu je `run` se prazen (bootstrap tece
    # vzporedno) in posnetek bi bil posnetek nicesar.
    next_ocena = (time.monotonic() + 60) if meri_napovedi else float("inf")
    # Health je drag in ni vezan na feed; ogrevamo ga na svojem ritmu.
    # Prvič takoj -- prvi obiskovalec po zagonu je sicer tisti, ki plača.
    next_health = 0.0

    while not _stop.is_set():
        started = time.monotonic()
        if started >= next_trips:
            next_trips = started + interval
            try:
                info = collector.poll_once(conn)
                if info.get("changed"):
                    _log(f"zajem: {info['trips']} vlakov, {info['changed']} sprememb")
                # Ogrejemo po VSAKEM uspesnem zajemu, ne le ob spremembi:
                # znacka predpomnilnika je `rt_fetched`, ta pa se osvezi tudi
                # takrat, ko feed ni prinesel nicesar novega. Kadar se znacka
                # ni premaknila, je to 19 ms in ne stane nic.
                _ogrej_zive()
                if info.get("non_scheduled"):
                    # Doslej vedno 0. Ce se kdaj oglasi, je feed dobil odpovedi in
                    # jih zna povedati strukturirano -- to je vredno vedeti.
                    _log(f"POZOR: feed poroča {info['non_scheduled']} zapisov, "
                         f"ki niso 'SCHEDULED' (odpoved ali izpuščen postanek)")
            except Exception as exc:        # feed občasno resetira povezavo
                _log(f"zajem ni uspel: {exc}")

        if started >= next_positions:
            next_positions = started + position_interval
            try:
                collector.poll_positions(conn)
            except Exception as exc:      # lega ni kriticna za zajem zamud
                _log(f"lege vozil ni bilo mogoče pobrati: {exc}")

        # Mestni LPP je drug vir in en sam feed za zamude, lege in obvestila.
        # Hodi po ritmu zamud, ne leg: zamuda je tisto, kar merimo.
        if config.LPP_ENABLED and started >= next_lpp:
            next_lpp = started + interval
            try:
                info = collector.poll_lpp(conn)
                if info.get("changed"):
                    _log(f"LPP: {info['trips']} voženj, {info['changed']} sprememb, "
                         f"{info.get('vehicles', 0)} leg")
            except Exception as exc:
                _log(f"zajem LPP ni uspel: {exc}")

        if started >= next_ocena:
            next_ocena = started + config.OCENA_SECONDS
            try:
                info = ocena.tick(conn)
                if info["zapisanih"] or info["resenih"]:
                    _log(f"ocena: {info['zapisanih']} novih napovedi, "
                         f"{info['resenih']} razrešenih")
            except Exception as exc:      # merjenje ni kriticno za zajem
                _log(f"ocene napovedi ni bilo mogoče posneti: {exc}")

        if started >= next_health:
            next_health = started + 300
            _ogrej_health()
            # Isti ritem, a v SVOJI niti: topel klic je nekaj milisekund,
            # hladen pa 15 s -- toliko bi zajem stal en cikel, in prav zajem
            # je edino, česar ni mogoče ponoviti za nazaj.
            threading.Thread(target=_ogrej_pot, daemon=True).start()

        if started >= next_alerts:
            next_alerts = started + alert_interval
            try:
                info = alerts.poll_once(conn)
                if info.get("changed"):
                    _log(f"obvestila: {info['alerts']} zapisov, "
                         f"{info['changed']} novih poročil o zamudi")
            except Exception as exc:      # obvestila niso kriticna za zajem
                _log(f"obvestil ni bilo mogoče pobrati: {exc}")

        if next_refresh and datetime.now(TZ) >= next_refresh:
            next_refresh += timedelta(days=1)
            try:
                refresh_timetable(conn, refresh_mode)
            except Exception as exc:
                _log(f"osvežitev voznega reda ni uspela: {exc}")

        if next_weather and datetime.now(TZ) >= next_weather:
            next_weather += timedelta(days=1)
            try:
                info = weather.backfill(conn, days=3)
                _log(f"vreme: {info['rows']} vrstic za {info['cells']} celic")
            except Exception as exc:      # vreme ni kriticno -- zajem tece naprej
                _log(f"vremena ni bilo mogoče dopolniti: {exc}")

        # Nocno vzdrzevanje: obrez dnevnika in razrezi statistike. Prej je bilo
        # oboje priklopljeno na vremensko opravilo in z `KAJROS_WEATHER=0` ni teklo
        # nikoli -- zato ima zdaj svojo uro.
        if next_maint and datetime.now(TZ) >= next_maint:
            next_maint += timedelta(days=1)

            # Z vsemi prevozniki nastane ~300 000 vrstic `obs` na dan (24 MB,
            # 8,7 GB na leto). `run` se ne brise nikoli -- ta je zgodovina.
            try:
                info = collector.prune_obs(conn)
                if info["rail_deleted"] or info["bus_deleted"]:
                    _log(f"dnevnik obrezan: {info['rail_deleted']} železniških, "
                         f"{info['bus_deleted']} avtobusnih vrstic")
            except Exception as exc:
                _log(f"dnevnika ni bilo mogoče obrezati: {exc}")

            try:
                n = ocena.prune(conn)
                if n:
                    _log(f"merjenje napovedi obrezano: {n} vrstic")
            except Exception as exc:
                _log(f"merjenja napovedi ni bilo mogoče obrezati: {exc}")

            # Razrezi cez vso zgodovino. Pri letu zajema je to agregat cez 12
            # milijonov vrstic in traja 34 s, odgovor pa se med dvema dnevoma
            # skoraj ne spremeni -- en nov dan je 1/90 vzorca. Zato enkrat na
            # dan tu, strani pa ga preberejo iz baze v milisekundi.
            # Na stroju, ki samo zajema, tega ne racunamo: razrez se da
            # kadarkoli izracunati iz `run`, izgubljena meritev pa nikoli.
            if summaries:
                try:
                    done = stats.refresh_summaries(conn)
                    worst = max((d["took_ms"] for d in done), default=0)
                    _log(f"povzetki osveženi: {len(done)} razrezov, "
                         f"najdlje {worst / 1000:.1f} s")
                except Exception as exc:  # statistika ni kriticna za zajem
                    _log(f"povzetkov ni bilo mogoče osvežiti: {exc}")

        # Spimo do PRVEGA naslednjega opravila, ne fiksen tik. Prej je bil
        # tik 10 s, naslednji cas pa se je racunal od trenutka PO delu -- zato
        # ga je vsak obhod zgresil za drobec in preskocil cel tik. Izmerjeno:
        # lege so se brale v razmikih 19, 11, 19, 11 s namesto 10.
        # Dnevna opravila (vozni red, vreme, vzdrzevanje) so v tem ritmu
        # preverjena tako ali tako veckrat na minuto.
        cakaj = min(next_trips, next_positions, next_alerts, next_lpp,
                    next_ocena, next_health) - time.monotonic()
        _stop.wait(max(0.5, min(cakaj, interval)))


def _settings() -> dict:
    """Nastavitve zajema iz okolja. Skupne strezniku in `kajros collect`."""
    mode = config.okolje("REFRESH", "off").lower()
    weather_hour = int(config.okolje("WEATHER_HOUR", "5"))
    if config.okolje("WEATHER", "1") == "0":
        weather_hour = -1
    return {
        "interval": int(config.okolje("POLL_SECONDS", config.POLL_SECONDS)),
        "position_interval": int(config.okolje("POSITION_SECONDS",
                                                config.POSITION_SECONDS)),
        "refresh_hour": int(config.okolje("REFRESH_HOUR", "4")),
        "refresh_mode": mode,
        "weather_hour": weather_hour,
        "alert_interval": int(config.okolje("ALERT_SECONDS", "60")),
        "maint_hour": int(config.okolje("MAINT_HOUR", "3")),
        "summaries": config.okolje("SUMMARIES", "1") != "0",
    }


def _describe(s: dict) -> str:
    parts = [f"zajem vsakih {s['interval']} s",
             f"lege vsakih {s['position_interval']} s"]
    parts.append("brez osveževanja voznega reda" if s["refresh_mode"] == "off"
                 else f"osvežitev ob {s['refresh_hour']}:20 ({s['refresh_mode']})")
    parts.append("vreme izklopljeno" if s["weather_hour"] < 0
                 else f"vreme ob {s['weather_hour']}:10")
    parts.append("obvestila izklopljena" if s["alert_interval"] <= 0
                 else f"obvestila vsakih {s['alert_interval']} s")
    if s["maint_hour"] < 0:
        parts.append("vzdrževanje izklopljeno")
    else:
        parts.append(f"{'povzetki in obrez' if s['summaries'] else 'obrez dnevnika'}"
                     f" ob {s['maint_hour']}:30")
    return ", ".join(parts)


def run_collector() -> None:
    """Zajem brez streznika, v ospredju. To poganja `kajros collect`.

    Namenjeno stroju, ki samo polni bazo -- tipicno malini, ki je gor ves cas.
    Razlika proti strezniku ni le HTTP: odpadeta FastAPI in uvicorn (uvoz sam
    je 20 MB RSS) in odpade racunanje, ki se da opraviti kasneje drugje.
    **Zajemati je treba samo tisto, cesar kasneje ni mogoce dobiti** -- zamude
    in obvestila. Vreme ima arhiv za nazaj, statistika pa je izpeljanka `run`.
    """
    bootstrap()
    s = _settings()
    _log(_describe(s))
    try:
        _worker(**s)
    except KeyboardInterrupt:
        _stop.set()
        _log("ustavljeno")


@asynccontextmanager
async def lifespan(app):
    global _strezemo
    _strezemo = True             # samo tu; `kajros collect` tega ne izvede
    bootstrap()
    thread = None
    if config.okolje("COLLECTOR", "1") != "0":
        settings = _settings()
        thread = threading.Thread(
            target=_worker, kwargs=settings,
            daemon=True, name="kajros-collector",
        )
        thread.start()
        _log(_describe(settings))
    else:
        _log("zajem izklopljen (KAJROS_COLLECTOR=0)")
    try:
        yield
    finally:
        _stop.set()
        if thread:
            thread.join(timeout=5)
