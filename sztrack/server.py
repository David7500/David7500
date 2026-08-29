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

from . import alerts, collector, config, db, gtfs, weather

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
            weather_hour: int, alert_interval: int) -> None:
    conn = db.connect()
    db.init(conn)
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
    next_alerts = 0.0

    while not _stop.is_set():
        started = time.monotonic()
        try:
            info = collector.poll_once(conn)
            if info.get("changed"):
                _log(f"zajem: {info['trips']} vlakov, {info['changed']} sprememb")
            if info.get("non_scheduled"):
                # Doslej vedno 0. Ce se kdaj oglasi, je feed dobil odpovedi in
                # jih zna povedati strukturirano -- to je vredno vedeti.
                _log(f"POZOR: feed poroča {info['non_scheduled']} zapisov, "
                     f"ki niso 'SCHEDULED' (odpoved ali izpuščen postanek)")
        except Exception as exc:            # feed občasno resetira povezavo
            _log(f"zajem ni uspel: {exc}")

        if track_vehicles:
            try:
                collector.poll_positions(conn)
            except Exception as exc:      # lega ni kriticna za zajem zamud
                _log(f"lege vozil ni bilo mogoče pobrati: {exc}")

        if alert_interval > 0 and time.monotonic() >= next_alerts:
            next_alerts = time.monotonic() + alert_interval
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

            # Ob istem dnevnem opravilu obrezemo dnevnik. Z vsemi prevozniki
            # nastane ~300 000 vrstic `obs` na dan (24 MB, 8,7 GB na leto).
            # `run` se ne brise nikoli -- ta je zgodovina.
            try:
                info = collector.prune_obs(conn)
                if info["rail_deleted"] or info["bus_deleted"]:
                    _log(f"dnevnik obrezan: {info['rail_deleted']} železniških, "
                         f"{info['bus_deleted']} avtobusnih vrstic")
            except Exception as exc:
                _log(f"dnevnika ni bilo mogoče obrezati: {exc}")

        _stop.wait(max(1.0, interval - (time.monotonic() - started)))


@asynccontextmanager
async def lifespan(app):
    bootstrap()
    thread = None
    if os.environ.get("SZ_COLLECTOR", "1") != "0":
        interval = int(os.environ.get("SZ_POLL_SECONDS", config.POLL_SECONDS))
        mode = os.environ.get("SZ_REFRESH", "off").lower()
        hour = int(os.environ.get("SZ_REFRESH_HOUR", "4"))
        weather_hour = int(os.environ.get("SZ_WEATHER_HOUR", "5"))
        if os.environ.get("SZ_WEATHER", "1") == "0":
            weather_hour = -1
        alert_interval = int(os.environ.get("SZ_ALERT_SECONDS", "60"))
        thread = threading.Thread(
            target=_worker, args=(interval, hour, mode, weather_hour, alert_interval),
            daemon=True, name="sztrack-collector",
        )
        thread.start()
        note = "brez osveževanja voznega reda" if mode == "off" else f"osvežitev ob {hour}:20 ({mode})"
        wnote = "vreme izklopljeno" if weather_hour < 0 else f"vreme ob {weather_hour}:10"
        anote = ("obvestila izklopljena" if alert_interval <= 0
                 else f"obvestila vsakih {alert_interval} s")
        _log(f"zajem teče vsakih {interval} s, {note}, {wnote}, {anote}")
    else:
        _log("zajem izklopljen (SZ_COLLECTOR=0)")
    try:
        yield
    finally:
        _stop.set()
        if thread:
            thread.join(timeout=5)
