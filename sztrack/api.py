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

from . import alerts, config, db, journey, stats
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


@app.get("/app/ovire", response_class=HTMLResponse)
def alerts_page(request: Request):
    """Dela na progi in nadomestni prevozi -- edini vir odgovora, ZAKAJ."""
    return templates.TemplateResponse(request, "alerts.html", {})


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


def _active_service_date(conn, train_no: str, now: datetime) -> str:
    """Kateri prometni dan te vožnje je "zdaj".

    Nočni vlak se po polnoči še vedno vozi pod včerajšnjim datumom in njegove
    voznoredne sekunde tečejo čez 86400. Brez tega je EC 79 ob 00:20 videti,
    kot da danes še ni vozil, čeprav je prav takrat na progi z dvema urama in
    pol zamude -- in prav takrat ga potnik gleda.

    Izbiramo med včeraj in danes; zmaga dan, katerega voznoredno okno vsebuje
    trenutni čas. Če ga ne vsebuje nobeno, ostane današnji.
    """
    today = now.date().isoformat()
    row = conn.execute(
        "SELECT MIN(COALESCE(s.dep_s, s.arr_s)) AS a, MAX(COALESCE(s.arr_s, s.dep_s)) AS b "
        "FROM trip t JOIN sched s USING (trip_id) WHERE t.train_no = ?",
        (train_no,),
    ).fetchone()
    if not row or row["a"] is None:
        return today

    now_s = journey.now_seconds(now)
    yesterday = (now.date() - timedelta(days=1)).isoformat()
    # Vceraj gledamo z zamikom cez polnoc; grace pokrije vlak, ki zamuja.
    grace = 3 * 3600
    if row["a"] <= now_s + 86400 <= row["b"] + grace:
        has = conn.execute(
            "SELECT 1 FROM run r JOIN trip t USING (trip_id) "
            "WHERE t.train_no = ? AND r.service_date = ? LIMIT 1",
            (train_no, yesterday),
        ).fetchone()
        if has:
            return yesterday
    return today


# Koliko voženj mora imeti dan, da o njem sploh govorimo. Pod tem je "delež
# točnih" bolj podatek o uri kot o železnici.
MIN_RUNS_FOR_DAY = 20


@app.get("/api/overview")
def api_overview():
    """Kaj se dogaja zdaj -- za obiskovalca, ki še ni nič vpisal.

    Brez tega je vstopna stran prazen obrazec. Vprašanje "kako vozijo vlaki
    danes" je pri prometni aplikaciji enako pogosto kot vprašanje o svoji poti.
    """
    now = datetime.now(TZ)
    today = now.date().isoformat()
    live = api_live()
    with _conn() as conn:
        day = stats.day_summary(conn, today)
        disruptions = len(alerts.active(conn))
        # Zgodaj zjutraj je danasnji vzorec prazen ali droben. "Mediana 0 min,
        # tocnih 100 %" iz ene same voznje ob pol enih zvecer ni slika dneva,
        # ampak nakljucje -- takrat raje povemo za vceraj in tako tudi napisemo.
        fallback = None
        if day.get("runs", 0) < MIN_RUNS_FOR_DAY:
            fallback = stats.day_summary(conn, yesterday_iso(now))
    return {
        "now": now.isoformat(),
        "live_trains": len(live),
        "live_worst": live[:5],
        "today": day,
        "yesterday": fallback,
        "disruptions": disruptions,
    }


def yesterday_iso(now: datetime) -> str:
    return (now.date() - timedelta(days=1)).isoformat()


@app.get("/api/stations")
def api_stations():
    with _conn() as conn:
        return stats.stations(conn)


@app.get("/api/stations/search")
def api_station_search(q: str = Query(..., min_length=1), limit: int = Query(12, ge=1, le=50)):
    """Postaje po delnem imenu, brez šumnikov. Iskalnik na telefonu rabi prav to."""
    with _conn() as conn:
        return journey.search_stations(conn, q, limit)


@app.get("/api/departures")
def api_departures(
    station: str = Query(..., description="ime postaje; delno ime je dovolj"),
    date: str | None = None,
    from_time: str | None = Query(None, alias="from", description="HH:MM; privzeto zdaj"),
    window: int | None = Query(None, ge=15, le=1440,
                               description="minut naprej; privzeto 3 h za danes, cel dan sicer"),
    kind: str = Query("odhodi", pattern="^(odhodi|prihodi)$"),
):
    """Odhodna ali prihodna tabla postaje.

    Najpogostejše vprašanje potnika in doslej edino, na katero API ni znal
    odgovoriti -- `connections` je zahteval izhodišče in cilj hkrati.
    """
    now = datetime.now(TZ)
    date = date or now.date().isoformat()
    if from_time:
        try:
            h, m = (int(x) for x in from_time.split(":")[:2])
        except ValueError:
            raise HTTPException(400, "from mora biti HH:MM")
        from_s = h * 3600 + m * 60
    elif date == now.date().isoformat():
        # Nekaj minut nazaj: vlak, ki je ravnokar odpeljal (ali zamuja), je
        # se vedno tisto, kar clovek na peronu isce.
        from_s = max(0, journey.now_seconds(now) - 10 * 60)
    else:
        from_s = 0
    # Drug dan nima "zdaj". Kdor gleda vceraj ali cez teden, hoce cel dan,
    # ne prvih treh ur od polnoci.
    if window is None:
        window = 180 if (not from_time and date == now.date().isoformat()) else 1440

    with _conn() as conn:
        exact = journey.resolve_station(conn, station)
        if not exact:
            raise HTTPException(404, f"postaje {station!r} ne poznam")
        rows = journey.board(conn, exact, date, from_s, window, kind)
        notices = alerts.for_trains(conn, [r["train_no"] for r in rows],
                                    mentions=[exact])
    return {"station": exact, "date": date, "kind": kind,
            "from_s": from_s, "window_min": window,
            "board": rows, "alerts": notices}


@app.get("/api/alerts")
def api_alerts(lang: str = Query("sl", pattern="^(sl|en)$")):
    """Veljavne ovire: dela na progi, nadomestni prevozi, združene garniture."""
    with _conn() as conn:
        return alerts.active(conn, lang)


@app.get("/api/train/{train_no}/alerts")
def api_train_alerts(train_no: str, lang: str = Query("sl", pattern="^(sl|en)$")):
    """Ovire, ki zadevajo prav ta vlak -- odgovor na 'zakaj zamuja'."""
    with _conn() as conn:
        return alerts.for_train(conn, train_no, lang)


@app.get("/api/train/{train_no}/reports")
def api_train_reports(train_no: str, date: str | None = None):
    """Zaporedje poročil prevoznika o tej vožnji: kje je bil vlak in koliko
    je zamujal. Prometno mesto pogosto ni voznoredni postanek, zato je to
    edini vir imena kraja, kjer je zamuda dejansko izmerjena."""
    with _conn() as conn:
        date = date or _active_service_date(conn, train_no, datetime.now(TZ))
        return {"train_no": train_no, "service_date": date,
                "reports": alerts.train_reports(conn, train_no, date)}


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
    with _conn() as conn:
        date = date or _active_service_date(conn, train_no, datetime.now(TZ))
        rows = stats.run_detail(conn, train_no, date)
        if not rows:
            raise HTTPException(404, f"vlak {train_no} ne obstaja")
        return {"train_no": train_no, "service_date": date, "stops": rows}


@app.get("/api/train/{train_no}/history")
def api_history(train_no: str, days: int = Query(90, ge=1, le=3650),
                exclude_date: str | None = None):
    """Zgodovina te poti. `exclude_date` izpusti en prometni dan -- prikaz
    tekoče vožnje ga rabi, da povprečje ne vsebuje vožnje, ki jo riše zraven."""
    with _conn() as conn:
        return stats.history(conn, train_no, days, exclude_date)


@app.get("/api/train/{train_no}/weather")
def api_run_weather(train_no: str, date: str | None = None):
    """Vreme na vsaki postaji te vožnje, po uri, ko je vlak tam."""
    with _conn() as conn:
        date = date or _active_service_date(conn, train_no, datetime.now(TZ))
        rows = stats.run_weather(conn, train_no, date)
        if not rows:
            raise HTTPException(404, f"vlak {train_no} ne obstaja")
        return {"train_no": train_no, "service_date": date, "stops": rows}


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
-- Feed za se nedosezene postanke pogosto objavi niclo, dokler nima prave
-- napovedi. Brez tega bi tak zapis pomenil, da je (voznored + 0) ze minil,
-- in vlak bi na zemljevidu skocil naprej. Zamuda ne pade z dvajsetih minut
-- na nic med dvema sosednjima postajama, zato tako vrstico preskocimo.
ranked AS (
    SELECT t.*, MAX(COALESCE(t.delay_s, 0)) OVER (
               PARTITION BY t.trip_id ORDER BY t.stop_seq
               ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS prev_max
    FROM t
),
passed AS (
    SELECT r.*, ROW_NUMBER() OVER (PARTITION BY trip_id ORDER BY stop_seq DESC) AS rn
    FROM ranked r
    WHERE r.t_s + COALESCE(r.delay_s, 0) <= :now_s
      AND NOT (COALESCE(r.delay_s, 0) = 0 AND r.prev_max >= 300)
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
    with_transfers: bool = Query(True, description="poišči tudi zveze z enim prestopom"),
):
    """Vožnje od postaje do postaje na dani dan, z zadnjo znano zamudo.

    Relacija se izračuna iz zaporedja postaj, ne iz številke vlaka: `train_no`
    označuje eno konkretno vožnjo, `route_id` pa je v tem feedu ena-na-ena
    s tripom in za grupiranje neuporaben.
    """
    now = datetime.now(TZ)
    date = date or now.date().isoformat()
    is_today = date == now.date().isoformat()
    now_s = journey.now_seconds(now) if is_today else None
    with _conn() as conn:
        a = journey.resolve_station(conn, from_)
        b = journey.resolve_station(conn, to)
        if not a or not b:
            missing = from_ if not a else to
            raise HTTPException(404, f"postaje {missing!r} ne poznam")
        rows = stats.connections(conn, a, b, date, now_s)
        # Prestop ponudimo vedno, ne sele ko neposredne ni: cez dan je
        # neposrednih voznj lahko pet, med njimi pa stiri ure luknje.
        legs = (journey.transfers(conn, a, b, date, earliest_s=(now_s or 0),
                                  direct=rows)
                if with_transfers else [])
        # Obvestila pobere streznik, ne brskalnik: prikaz jih je sicer iskal
        # z eno zahtevo na vlak, torej z dvanajstimi za eno iskanje.
        nos = [c["train_no"] for c in rows] + [t["train1"] for t in legs]
        notices = alerts.for_trains(conn, nos, mentions=[a, b])
    return {"from": a, "to": b, "date": date,
            "connections": rows, "transfers": legs, "alerts": notices}


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
        # Prevoznikovo porocilo je merodajno in edino pozna prometno mesto:
        # nasa `run` pozna samo voznoredne postanke, zamuda pa se meri tudi
        # tam, kjer vlak ne ustavlja.
        # Tudi vcerajsnji prometni dan: nocni vlak po polnoci se vedno vozi
        # pod vcerajsnjim datumom, enako kot vrstice zgoraj.
        reported = {r["train_no"]: r for r in alerts.live_delays(conn, yesterday)}
        reported.update({r["train_no"]: r for r in alerts.live_delays(conn, today)})
    now_ts = int(now.timestamp())
    for r in rows:
        rep = reported.get(r["train_no"])
        if rep:
            r["reported_delay_s"] = rep["delay_min"] * 60
            r["reported_at_station"] = rep["station"]
            r["reported_severe"] = bool(rep["severe"])
            r["reported_age_s"] = now_ts - rep["seen_ts"]
            # Lega, kadar prometno mesto poznamo kot postajo. Zemljevid jo ima
            # raje od nase: nasa je zadnji voznoredni postanek z meritvijo,
            # prevoznikova pa kraj, kjer je bila zamuda dejansko izmerjena.
            if rep["station_lat"] is not None:
                r["reported_lat"] = rep["station_lat"]
                r["reported_lon"] = rep["station_lon"]
        # Koliko je stara meritev, na katero se sklicujemo. Brez tega prikaz
        # ob polnoci se vedno trdi "+20 min", ceprav je bilo to izmerjeno ob 17h.
        r["age_s"] = now_ts - r["feed_ts"] if r.get("feed_ts") else None
    rows.sort(key=lambda r: (r["delay_s"] is None, -(r["delay_s"] or 0)))
    return rows
