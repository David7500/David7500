"""JSON API. Prikaz je namerno ločen -- karkoli si izbereš za frontend
(MapLibre, Streamlit, mobilna aplikacija) govori s temi endpointi.

    uvicorn sztrack.api:app --reload
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import config, db, stats
from .server import lifespan

TZ = ZoneInfo(config.TIMEZONE)
app = FastAPI(title="sztrack", version="0.1.0",
              description="Vozni redi, zamude in statistika Slovenskih železnic",
              lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

# Poti relativno na paket, da delajo enako v dev checkoutu in na /opt/sztrack.
_PKG_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=_PKG_DIR / "static"), name="static")
templates = Jinja2Templates(directory=_PKG_DIR / "templates")


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


@app.get("/app", response_class=HTMLResponse)
def connections_page(request: Request):
    """Vstopna stran: od postaje do postaje. Zemljevid je pogled dispecerja,
    povprecen potnik sprasuje "kdaj mi pelje vlak" -- zato je iskalnik prvi."""
    return templates.TemplateResponse(request, "connections.html", {})


@app.get("/app/map", response_class=HTMLResponse)
def dashboard(request: Request):
    """Živi nadzorni pregled -- podatke si pobere sam prek /api/* v JS-u."""
    return templates.TemplateResponse(request, "dashboard.html", {})


@app.get("/app/train/{train_no}", response_class=HTMLResponse)
def dashboard_train(request: Request, train_no: str):
    """Svoje okno za en vlak: ta vožnja + zgodovina zamud te poti."""
    return templates.TemplateResponse(request, "train.html", {"train_no": train_no})


@app.get("/api/health")
def api_health():
    """Stanje zajema. Po ponovnem zagonu gostitelja preveri prav to --
    če `runs_recorded` pade nazaj na 0, disk ne preživi zagona."""
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


# Vlak ostane na seznamu se toliko sekund po voznorednem (z zamudo popravljenem)
# prihodu na cilj -- da ne izgine iz zemljevida v isti sekundi, ko pripelje.
_LIVE_GRACE_S = 300

_LIVE_SQL = """
WITH t AS (
    SELECT r.trip_id, r.stop_seq, r.feed_ts, s.stop_id,
           COALESCE(r.delay_dep, r.delay_arr) AS delay_s,
           COALESCE(s.dep_s, s.arr_s) AS t_s
    FROM run r
    JOIN sched s ON s.trip_id = r.trip_id AND s.stop_seq = r.stop_seq
    WHERE r.service_date = :day
),
win AS (
    SELECT trip_id,
           MIN(COALESCE(dep_s, arr_s)) AS start_s,
           MAX(COALESCE(arr_s, dep_s)) AS end_s
    FROM sched GROUP BY trip_id
),
passed AS (
    SELECT t.*, ROW_NUMBER() OVER (PARTITION BY trip_id ORDER BY stop_seq DESC) AS rn
    FROM t WHERE t.t_s + COALESCE(t.delay_s, 0) <= :now_s
),
tail AS (
    SELECT trip_id, delay_s AS end_delay_s,
           ROW_NUMBER() OVER (PARTITION BY trip_id ORDER BY stop_seq DESC) AS rn
    FROM t
)
SELECT tr.train_no, tr.headsign, st.name AS last_stop, p.stop_seq,
       p.delay_s, p.feed_ts, p.t_s AS sched_s
FROM passed p
JOIN tail  ON tail.trip_id = p.trip_id AND tail.rn = 1
JOIN win   ON win.trip_id = p.trip_id
JOIN trip tr ON tr.trip_id = p.trip_id
JOIN station st ON st.stop_id = p.stop_id
WHERE p.rn = 1
  AND :now_s <= win.end_s + COALESCE(tail.end_delay_s, 0) + :grace
ORDER BY p.delay_s DESC
"""


def _live_rows(conn, service_date: str, now_s: int) -> list[dict]:
    """Vlaki, ki na dani prometni dan ob `now_s` (sekunde od polnoci tega dne)
    dejansko vozijo. Zadnja znana postaja je zadnja, katere cas je ze minil --
    ne zadnja, o kateri feed porocá: feed poslje napoved tudi za naslednjo
    postajo, po koncu voznje pa ostane zapisan cilj."""
    rows = conn.execute(_LIVE_SQL, {"day": service_date, "now_s": now_s,
                                    "grace": _LIVE_GRACE_S}).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["service_date"] = service_date
        # Kje in kdaj je bila zamuda nazadnje izmerjena -- prikaz mora to povedati.
        d["measured_at"] = stats.abs_time(service_date, d.pop("sched_s") + (d["delay_s"] or 0))
        out.append(d)
    return out


@app.get("/api/connections")
def api_connections(
    from_: str = Query(..., alias="from", description="ime izhodiščne postaje"),
    to: str = Query(..., description="ime ciljne postaje"),
    date: str | None = None,
):
    """Vožnje od postaje do postaje na dani dan, z zadnjo znano zamudo.

    Relacija se izračuna iz zaporedja postaj, ne iz številke vlaka: `train_no`
    označuje eno konkretno vožnjo, `route_id` pa je v tem feedu ena-na-ena
    s tripom in za grupiranje neuporaben.
    """
    now = datetime.now(TZ)
    date = date or now.date().isoformat()
    now_s = (now.hour * 3600 + now.minute * 60 + now.second
             if date == now.date().isoformat() else None)
    with _conn() as conn:
        rows = stats.connections(conn, from_, to, date, now_s)
    return {"from": from_, "to": to, "date": date, "connections": rows}


@app.get("/api/live")
def api_live():
    """Vlaki, ki so zdaj na progi, z zadnjo izmerjeno zamudo.

    Ni isto kot "vse, kar je danes v feedu": vozila, ki so vozila zjutraj,
    ostanejo v tabeli `run` do konca dneva in bi jih naiven MAX(stop_seq)
    pokazal kot vlak, ki stoji na cilju z zamudo izpred nekaj ur.
    """
    now = datetime.now(TZ)
    now_s = now.hour * 3600 + now.minute * 60 + now.second
    today = now.date().isoformat()
    # Nocni vlaki: po polnoci se vozijo pod vcerajsnjim prometnim dnem,
    # njihove voznoredne sekunde pa tecejo naprej cez 86400.
    yesterday = (now.date() - timedelta(days=1)).isoformat()
    with _conn() as conn:
        rows = _live_rows(conn, today, now_s) + _live_rows(conn, yesterday, now_s + 86400)
    rows.sort(key=lambda r: (r["delay_s"] is None, -(r["delay_s"] or 0)))
    return rows
