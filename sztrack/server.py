"""En sam proces: API in zajem zamud skupaj.

Zajem teče v ozadnji niti istega procesa, tako da ni treba voditi dveh
storitev. Na majhnem strežniku je to tudi cenejše -- en Python interpreter.
"""
from __future__ import annotations

import os
import shutil
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from . import collector, config, db, gtfs

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


def _worker(interval: int, refresh_hour: int) -> None:
    conn = db.connect()
    db.init(conn)
    next_refresh = datetime.now(TZ).replace(hour=refresh_hour, minute=20, second=0, microsecond=0)
    if next_refresh <= datetime.now(TZ):
        next_refresh += timedelta(days=1)

    while not _stop.is_set():
        started = time.monotonic()
        try:
            info = collector.poll_once(conn)
            if info.get("changed"):
                _log(f"zajem: {info['trips']} vlakov, {info['changed']} sprememb")
        except Exception as exc:            # feed občasno resetira povezavo
            _log(f"zajem ni uspel: {exc}")

        if datetime.now(TZ) >= next_refresh:
            next_refresh += timedelta(days=1)
            try:
                path = gtfs.download(conn)
                if path is None:
                    _log("vozni red nespremenjen")
                else:
                    _log(f"nov vozni red: {gtfs.import_static(conn, path)}")
                    path.unlink(missing_ok=True)
            except Exception as exc:
                _log(f"osvežitev voznega reda ni uspela: {exc}")

        _stop.wait(max(1.0, interval - (time.monotonic() - started)))


@asynccontextmanager
async def lifespan(app):
    bootstrap()
    thread = None
    if os.environ.get("SZ_COLLECTOR", "1") != "0":
        interval = int(os.environ.get("SZ_POLL_SECONDS", config.POLL_SECONDS))
        thread = threading.Thread(
            target=_worker, args=(interval, int(os.environ.get("SZ_REFRESH_HOUR", "4"))),
            daemon=True, name="sztrack-collector",
        )
        thread.start()
        _log(f"zajem teče vsakih {interval} s")
    else:
        _log("zajem izklopljen (SZ_COLLECTOR=0)")
    try:
        yield
    finally:
        _stop.set()
        if thread:
            thread.join(timeout=5)
