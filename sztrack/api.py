"""JSON API. Prikaz je namerno ločen -- karkoli si izbereš za frontend
(MapLibre, Streamlit, mobilna aplikacija) govori s temi endpointi.

    uvicorn sztrack.api:app --reload
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import config, db, stats
from .server import lifespan

TZ = ZoneInfo(config.TIMEZONE)
app = FastAPI(title="sztrack", version="0.1.0",
              description="Vozni redi, zamude in statistika Slovenskih železnic",
              lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


def _conn():
    return db.connect()


@app.get("/")
def index():
    """Kazalo. Nekateri gostitelji preverjajo živost prav na korenski poti."""
    return {
        "service": "sztrack",
        "version": app.version,
        "docs": "/docs",
        "endpoints": [r.path for r in app.routes if getattr(r, "path", "").startswith("/api/")],
    }


@app.get("/api/health")
def api_health():
    """Stanje zajema. Po ponovnem zagonu gostitelja preveri prav to --
    če `runs_recorded` pade nazaj na 0, disk ne preživi zagona."""
    from pathlib import Path

    with _conn() as conn:
        row = conn.execute(
            "SELECT (SELECT COUNT(*) FROM trip) AS trips,"
            "       (SELECT COUNT(*) FROM station) AS stations,"
            "       (SELECT COUNT(*) FROM obs) AS observations,"
            "       (SELECT COUNT(*) FROM run) AS runs_recorded,"
            "       (SELECT COUNT(DISTINCT service_date) FROM run) AS days_covered,"
            "       (SELECT MAX(feed_ts) FROM run) AS last_feed_ts"
        ).fetchone()
        out = dict(row)
    path = Path(config.DB_PATH)
    out["db_bytes"] = path.stat().st_size if path.exists() else 0
    out["db_path"] = str(path)
    out["last_feed_at"] = (
        datetime.fromtimestamp(out["last_feed_ts"], TZ).isoformat()
        if out["last_feed_ts"] else None
    )
    return out


@app.get("/api/stations")
def api_stations():
    with _conn() as conn:
        return stats.stations(conn)


@app.get("/api/network.geojson")
def api_network(elementary_only: bool = True):
    """Geometrija prog z dolžino odseka v km. Za risanje zemljevida."""
    with _conn() as conn:
        return stats.network_geojson(conn, elementary_only)


@app.get("/api/trains")
def api_trains():
    with _conn() as conn:
        return stats.trains(conn)


@app.get("/api/train/{train_no}")
def api_train(train_no: str):
    with _conn() as conn:
        rows = stats.timetable(conn, train_no)
        if not rows:
            raise HTTPException(404, f"vlak {train_no} ne obstaja")
        return {"train_no": train_no, "timetable": rows}


@app.get("/api/train/{train_no}/run")
def api_run(train_no: str, date: str | None = None):
    """Ena vožnja: vozni red, zamuda in izračunani dejanski časi."""
    date = date or datetime.now(TZ).date().isoformat()
    with _conn() as conn:
        rows = stats.run_detail(conn, train_no, date)
        if not rows:
            raise HTTPException(404, f"vlak {train_no} ne obstaja")
        return {"train_no": train_no, "service_date": date, "stops": rows}


@app.get("/api/train/{train_no}/history")
def api_history(train_no: str, days: int = Query(90, ge=1, le=3650)):
    with _conn() as conn:
        return stats.history(conn, train_no, days)


@app.get("/api/train/{train_no}/predict")
def api_predict(train_no: str, stop_seq: int, delay_s: int,
                days: int = Query(90, ge=1, le=3650)):
    """Napoved zamude naprej po progi, glede na trenutno zamudo."""
    with _conn() as conn:
        return {"train_no": train_no, "from_stop_seq": stop_seq,
                "current_delay_s": delay_s,
                "forecast": stats.predict(conn, train_no, stop_seq, delay_s, days)}


@app.get("/api/speeds")
def api_speeds(train_no: str | None = None):
    """Voznoredna in izmerjena hitrost po odsekih (odseki >= 5 km)."""
    with _conn() as conn:
        return stats.segment_speeds(conn, train_no)


@app.get("/api/stats")
def api_stats(days: int = Query(90, ge=1, le=3650)):
    """Lestvica vlakov po zamudi ob koncu vožnje."""
    with _conn() as conn:
        return stats.network_stats(conn, days)


@app.get("/api/live")
def api_live():
    """Vlaki, ki so trenutno v feedu, z zadnjo znano zamudo."""
    today = datetime.now(TZ).date().isoformat()
    with _conn() as conn:
        rows = conn.execute(
            "WITH last AS ("
            "  SELECT r.*, ROW_NUMBER() OVER (PARTITION BY r.trip_id"
            "                                 ORDER BY r.stop_seq DESC) AS rn"
            "  FROM run r WHERE r.service_date = ?"
            ") "
            "SELECT t.train_no, t.headsign, st.name AS last_stop, "
            "       COALESCE(l.delay_arr, l.delay_dep) AS delay_s, l.feed_ts "
            "FROM last l JOIN trip t USING (trip_id) "
            "JOIN sched s ON s.trip_id = l.trip_id AND s.stop_seq = l.stop_seq "
            "JOIN station st ON st.stop_id = s.stop_id "
            "WHERE l.rn = 1 ORDER BY delay_s DESC",
            (today,),
        )
        return [dict(r) for r in rows]
