"""En sam proces: API in zajem zamud skupaj.

Zajem teče v ozadnji niti istega procesa, tako da ni treba voditi dveh
storitev. Na majhnem strežniku je to tudi cenejše -- en Python interpreter.
"""
from __future__ import annotations

import os
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


def _log(msg: str) -> None:
    print(f"{datetime.now(TZ):%H:%M:%S}  {msg}", flush=True)


def bootstrap() -> None:
    """Poskrbi, da baza obstaja in ima vozni red.

    Če je v paketu priložena pripravljena baza, jo uporabimo -- uvoz iz GTFS
    zipa pomeni 41 MB prenosa in nekaj minut na počasnem jedru. Obstoječe baze
    nikoli ne povozimo, sicer bi vsaka nova objava izbrisala zajeto zgodovino.
    """
    target = Path(config.DB_PATH)
    seed = Path(__file__).resolve().parent.parent / "seed" / "sz.sqlite"
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
    if path:
        _log(f"uvažam {path.stat().st_size / 1e6:.0f} MB ...")
        _log(f"uvoženo: {gtfs.import_static(conn, path)}")
        path.unlink(missing_ok=True)      # 41 MB ne rabimo obdržati


def refresh_timetable(conn, mode: str) -> None:
    """Osveži vozni red. `mode`: off | inprocess | subprocess.

    Uvoz je najdražji trenutek v življenju procesa. Izmerjeno na tem paketu:
    v istem procesu vrh 89 MB (in ostane pri 85 MB, ker Python arene vrne
    operacijskemu sistemu redko), v podprocesu 54 MB poleg 57 MB starša.
    Na stroju s 100 MB torej nobena od obeh ni varna -- zato je privzeto `off`
    in vozni red osvežiš z novo priloženo bazo ali z `sztrack update` drugje.
    """
    if mode == "off":
        return
    if mode == "subprocess":
        # Lasten naslovni prostor: ob koncu se ves pomnilnik vrne sistemu.
        proc = subprocess.run(
            [sys.executable, "-m", "sztrack.cli", "update"],
            capture_output=True, text=True, timeout=1800,
        )
        _log(f"osvežitev (podproces): {proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else proc.stderr[-200:]}")
        return

    path = gtfs.download(conn)
    if path is None:
        _log("vozni red nespremenjen")
        return
    _log(f"nov vozni red: {gtfs.import_static(conn, path)}")
    path.unlink(missing_ok=True)


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
    meri_napovedi = os.environ.get("SZ_OCENA", "1") != "0"
    # Lega vozil je smiselna samo, ce so v bazi avtobusi: feed nosi izkljucno
    # njih. Pri zeleznici bi bila to zahteva vsakih 30 s za prazen odgovor.
    has_bus = conn.execute("SELECT 1 FROM trip WHERE mode = 'bus' LIMIT 1").fetchone()
    track_vehicles = bool(has_bus) and os.environ.get("SZ_POSITIONS", "1") != "0"
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
    # Prvi obhod sele cez minuto: ob zagonu je `run` se prazen (bootstrap tece
    # vzporedno) in posnetek bi bil posnetek nicesar.
    next_ocena = (time.monotonic() + 60) if meri_napovedi else float("inf")

    while not _stop.is_set():
        started = time.monotonic()
        if started >= next_trips:
            next_trips = started + interval
            try:
                info = collector.poll_once(conn)
                if info.get("changed"):
                    _log(f"zajem: {info['trips']} vlakov, {info['changed']} sprememb")
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

        if started >= next_ocena:
            next_ocena = started + config.OCENA_SECONDS
            try:
                info = ocena.tick(conn)
                if info["zapisanih"] or info["resenih"]:
                    _log(f"ocena: {info['zapisanih']} novih napovedi, "
                         f"{info['resenih']} razrešenih")
            except Exception as exc:      # merjenje ni kriticno za zajem
                _log(f"ocene napovedi ni bilo mogoče posneti: {exc}")

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
        # oboje priklopljeno na vremensko opravilo in z `SZ_WEATHER=0` ni teklo
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
        cakaj = min(next_trips, next_positions, next_alerts,
                    next_ocena) - time.monotonic()
        _stop.wait(max(0.5, min(cakaj, interval)))


def _settings() -> dict:
    """Nastavitve zajema iz okolja. Skupne strezniku in `sztrack collect`."""
    mode = os.environ.get("SZ_REFRESH", "off").lower()
    weather_hour = int(os.environ.get("SZ_WEATHER_HOUR", "5"))
    if os.environ.get("SZ_WEATHER", "1") == "0":
        weather_hour = -1
    return {
        "interval": int(os.environ.get("SZ_POLL_SECONDS", config.POLL_SECONDS)),
        "position_interval": int(os.environ.get("SZ_POSITION_SECONDS",
                                                config.POSITION_SECONDS)),
        "refresh_hour": int(os.environ.get("SZ_REFRESH_HOUR", "4")),
        "refresh_mode": mode,
        "weather_hour": weather_hour,
        "alert_interval": int(os.environ.get("SZ_ALERT_SECONDS", "60")),
        "maint_hour": int(os.environ.get("SZ_MAINT_HOUR", "3")),
        "summaries": os.environ.get("SZ_SUMMARIES", "1") != "0",
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
    """Zajem brez streznika, v ospredju. To poganja `sztrack collect`.

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
    bootstrap()
    thread = None
    if os.environ.get("SZ_COLLECTOR", "1") != "0":
        settings = _settings()
        thread = threading.Thread(
            target=_worker, kwargs=settings,
            daemon=True, name="sztrack-collector",
        )
        thread.start()
        _log(_describe(settings))
    else:
        _log("zajem izklopljen (SZ_COLLECTOR=0)")
    try:
        yield
    finally:
        _stop.set()
        if thread:
            thread.join(timeout=5)
