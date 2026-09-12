"""JSON API. Prikaz je namerno ločen -- karkoli si izbereš za frontend
(MapLibre, Streamlit, mobilna aplikacija) govori s temi endpointi.

    uvicorn kajros.api:app --reload
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import (HTMLResponse, JSONResponse, RedirectResponse,
                               Response)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import alerts, collector, config, db, journey, lpp, pot, stats
from .server import lifespan

TZ = ZoneInfo(config.TIMEZONE)
app = FastAPI(title="kajros", version="0.1.0",
              description="Vozni redi, zamude in statistika Slovenskih železnic",
              lifespan=lifespan)
# `expose_headers`: brez tega JS lastnih glav ne vidi. Nasa stran je z istega
# izvora in bi delovala tudi brez, a `X-Osvezi-Cez` je del odgovora in mora
# biti berljiva vsakomur, ki API uporablja.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"],
                   allow_headers=["*"], expose_headers=["X-Osvezi-Cez"])
# Odgovori so JSON s ponavljajocimi se imeni polj in se stisnejo na desetino.
# Pri letu zajema ima lestvica avtobusnih linij 167 KB, stisnjena 20 KB --
# in to prek Tailscala ali tunela ni vseeno. Brez nove odvisnosti (starlette).
app.add_middleware(GZipMiddleware, minimum_size=1024)


@app.exception_handler(journey.VozniRedPrevelik)
def _voznired_prevelik(request: Request, exc: journey.VozniRedPrevelik):
    """Vozni red je prevelik za iskanje v pomnilniku — 503, ne prazen odgovor.

    Prej je varovalka vracala prazen vozni red in prikaz je pokazal "ni zvez".
    To je od pravega odgovora nerazlocljivo, zato je napaka mesece ostala
    neopazena. Zdaj je vidna in ima svojo stevilko.
    """
    return JSONResponse(status_code=503, content={"detail": str(exc)})

# Dve locheni omrezji, ne en kup. `zeleznica` so vlaki IN nadomestni prevozi SZ
# (ti na svoji relaciji zamenjujejo vlak in sodijo v isti odgovor), `avtobus`
# pa LPP in ostali prevozniki. Potnik ve, ali gre z vlakom ali z busom, in ju
# ne isce skupaj -- mesanje je bilo tudi merljivo skodljivo: iskanje "ljublj"
# je vracalo mestna postajalisca in postajo Ljubljana potisnilo iz prvih petih.
#
# Privzeto je zeleznica: projekt je sledilnik SZ, avtobusi so dodatek in se
# zahtevajo izrecno. Tako mesanja ne more povzrociti pozabljen parameter.
NETWORK_Q = Query("zeleznica", pattern="^(zeleznica|avtobus)$",
                  description="zeleznica (vlaki + nadomestni prevozi) ali avtobus")

# Poti relativno na paket, da delajo enako v dev checkoutu in na /opt/kajros.
_PKG_DIR = Path(__file__).parent
class _RevalidatingStatic(StaticFiles):
    """Statične datoteke z obvezno revalidacijo.

    Brez `Cache-Control` brskalnik ugiba: datoteko, ki se dolgo ni
    spremenila, drži v predpomnilniku ure. Posledica je bila prijavljena --
    popravek spodnje plošče na zemljevidu je bil na strežniku, uporabnik pa
    je dobival staro CSS in gumba ni bilo. `no-cache` ni "ne shranjuj":
    datoteka se shrani, a se pred vsako rabo preveri, in ker imamo `ETag`,
    je odgovor 304 brez telesa.
    """

    def file_response(self, *args, **kwargs):
        resp = super().file_response(*args, **kwargs)
        resp.headers["Cache-Control"] = "no-cache"
        return resp


app.mount("/static", _RevalidatingStatic(directory=_PKG_DIR / "static"), name="static")
templates = Jinja2Templates(directory=_PKG_DIR / "templates")


@lru_cache(maxsize=None)
def _razlicica(rel: str) -> str:
    """Osem znakov zgoščene vsebine datoteke. Med tekom se ne spreminja."""
    try:
        return hashlib.sha256((_PKG_DIR / "static" / rel).read_bytes()).hexdigest()[:8]
    except OSError:
        return ""


def s(rel: str) -> str:
    """Naslov statične datoteke z odtisom vsebine.

    **`Cache-Control: no-cache` ni dovolj in to je izmerjeno.** Strežnik ga
    pošilja (glej `_RevalidatingStatic`), Cloudflare pa ga na robu povozi s
    svojim privzetim `max-age=14400` -- štiri ure, v katerih brskalnik
    datoteke sploh ne vpraša znova. Popravek postavitve na telefonu je bil
    6. 9. 2026 na strežniku, uporabnik pa je gledal staro. Ista napaka je
    bila v tem projektu že enkrat odpravljena in se je vrnila skozi druga
    vrata -- tokrat naj bo popravljena tam, kjer je noben posrednik ne more
    razveljaviti.

    Odtis vsebine in ne časa spremembe: `mtime` se premakne ob vsakem
    `rsync`, tudi kadar je datoteka ista, in bi vsem obiskovalcem ob vsaki
    objavi po nepotrebnem izpraznil predpomnilnik.
    """
    v = _razlicica(rel)
    return f"/static/{rel}?v={v}" if v else f"/static/{rel}"


templates.env.globals["s"] = s


def _conn():
    return db.connect()


def _check_date(value: str | None) -> str | None:
    """Datum mora biti YYYY-MM-DD ali nič.

    Brez tega gre napačen niz naravnost v `WHERE service_date = ?`, se ne
    ujame z nicimer in vrne prazen seznam z 200. Prikaz to prebere kot
    "ta dan ni odhodov", kar je za tipkarsko napako napacen odgovor.
    """
    if value is None:
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise HTTPException(400, f"datum {value!r} ni oblike YYYY-MM-DD") from None


@app.get("/")
def index(request: Request):
    """Korenska pot streže dvoje.

    Gostitelji in nadzor preverjajo živost prav tu in pričakujejo JSON, zato
    ta ostane. Človek, ki v naslovno vrstico vtipka domeno, pa ni prišel po
    seznam endpointov -- brskalnik prosi za HTML in dobi preusmeritev na
    aplikacijo.
    """
    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(request, "home.html", {})
    return JSONResponse({
        "service": "kajros",
        "version": app.version,
        "docs": "/docs",
        "app": "/app",
        "endpoints": [r.path for r in app.routes if getattr(r, "path", "").startswith("/api/")],
    })


@app.get("/app", response_class=HTMLResponse)
def app_root():
    """Stara vstopna pot. Vlaki imajo zdaj svojo `/app/train`, tako kot imajo
    avtobusi `/app/bus` -- `/app` je bil vlakovni samo po dogovoru in to je
    bilo iz naslova nevidno. Deljene povezave morajo ostati veljavne."""
    return RedirectResponse("/app/train", status_code=308)


@app.get("/app/train", response_class=HTMLResponse)
def connections_page(request: Request):
    """Vlaki: od postaje do postaje. Zemljevid je pogled dispecerja,
    povprecen potnik sprasuje "kdaj mi pelje vlak" -- zato je iskalnik prvi."""
    return templates.TemplateResponse(request, "connections.html", {
        "here": "iskalnik", "network": "zeleznica",
    })


@app.get("/app/bus", response_class=HTMLResponse)
def bus_page(request: Request):
    """Avtobusi imajo SVOJO stran, ne skupne z vlaki.

    Potnik ve, ali gre z vlakom ali z avtobusom, in ju ne išče skupaj; skupen
    seznam je le manj pregleden. Mešanje je bilo tudi merljivo škodljivo:
    iskanje "ljublj" je vračalo mestna postajališča in postajo Ljubljana
    potisnilo iz prvih petih zadetkov.

    Nadomestni prevozi SŽ sem NE sodijo -- ti na svoji relaciji zamenjujejo
    vlak in ostanejo pri vlakih (`trip.network = 'zeleznica'`).
    """
    return templates.TemplateResponse(request, "connections.html", {
        "here": "avtobusi", "network": "avtobus",
        "section": "Avtobusi",
        "page_title": "kajros — avtobusi: odhodi in zamude",
        "page_desc": "Odhodi in zamude slovenskih avtobusov iz odprtih podatkov.",
        "from_ph": "izhodiščno postajališče",
        "to_ph": "ciljno postajališče",
        "stop_label": "Postajališče",
        "stop_ph": "npr. Bavarski dvor",
    })


@app.get("/app/pot", response_class=HTMLResponse)
def pot_page(request: Request):
    """Od vrat do vrat: potnik ne ve, s katere postaje gre -- ve, kje stoji.

    To je za zemljevidom druga stran, ki obe omrežji **namerno** meša: vlak in
    avtobus sta tu lahko v isti verigi in delitev bi bila ovira, ne pomoč.
    """
    return templates.TemplateResponse(request, "pot.html", {"here": "pot"})


@app.get("/app/map", response_class=HTMLResponse)
def dashboard(request: Request):
    """Živi nadzorni pregled -- podatke si pobere sam prek /api/* v JS-u."""
    return templates.TemplateResponse(request, "dashboard.html", {"here": "zemljevid"})


@app.get("/app/ovire", response_class=HTMLResponse)
def alerts_page(request: Request):
    """Dela na progi in nadomestni prevozi -- edini vir odgovora, ZAKAJ."""
    return templates.TemplateResponse(request, "alerts.html", {"here": "ovire"})


@app.get("/app/statistika", response_class=HTMLResponse)
@app.get("/app/statistika/{omrezje}", response_class=HTMLResponse)
def stats_page(request: Request, omrezje: str = "vlak"):
    """Kdaj se splaca potovati: zamuda po uri, dnevu in vrsti.

    Ime poti je slovensko in ne "stats", ker je naslov tudi besedilo -- kdor
    ga deli naprej, deli poved. Omrezje je v poti iz istega razloga kot pri
    oknu voznje: `/app/statistika` brez pripone bi bila vlakovna samo po
    dogovoru in iz naslova to ne bi bilo vidno.
    """
    # Pripona, ki je ne poznamo, ni vlakovna stran: `/app/statistika/karkoli`
    # je doslej tiho vrnil zeleznico, kar je v nasprotju z razlogom, zakaj je
    # omrezje sploh v poti -- da je iz naslova vidno, kaj gledas.
    if omrezje not in ("vlak", "bus"):
        raise HTTPException(404, f"omrežja {omrezje!r} ne poznam")
    network = "avtobus" if omrezje == "bus" else "zeleznica"
    return templates.TemplateResponse(request, "statistika.html",
                                      {"here": "statistika", "network": network})


def _trip_page(request: Request, train_no: str, trip: str | None, network: str):
    """Okno ene vožnje. Pot mora ustrezati omrežju vožnje.

    Ista predloga streže oboje, a naslov ne sme lagati: `/app/train/25` za
    mestno linijo 25 je napačen naslov, ki ga bo nekdo delil naprej. Zato
    poizvedba po omrežju in preusmeritev na pravo pot.
    """
    with _conn() as conn:
        row = conn.execute(
            "SELECT network FROM trip "
            "WHERE (:trip IS NOT NULL AND trip_id = :trip) "
            "   OR (:trip IS NULL AND train_no = :no) LIMIT 1",
            {"trip": trip, "no": train_no}).fetchone()
    prava = row["network"] if row else network
    if prava != network:
        pot = "/app/bus/" if prava == "avtobus" else "/app/train/"
        q = f"?{request.url.query}" if request.url.query else ""
        return RedirectResponse(f"{pot}{quote(train_no)}{q}", status_code=307)
    return templates.TemplateResponse(request, "train.html", {
        "train_no": train_no, "network": prava,
        "here": "avtobusi" if prava == "avtobus" else "iskalnik",
    })


@app.get("/app/train/{train_no}", response_class=HTMLResponse)
def train_trip_page(request: Request, train_no: str, trip: str | None = None):
    """Okno ene vlakovne vožnje: ta vožnja + zgodovina zamud te poti."""
    return _trip_page(request, train_no, trip, "zeleznica")


@app.get("/app/bus/{train_no}", response_class=HTMLResponse)
def bus_trip_page(request: Request, train_no: str, trip: str | None = None):
    """Okno ene avtobusne vožnje. Ista predloga, druga pot in druga barva --
    potnik mora iz naslova videti, s čim gre."""
    return _trip_page(request, train_no, trip, "avtobus")


@app.get("/api/health")
def api_health():
    """Stanje zajema. Po ponovnem zagonu gostitelja preveri prav to --
    če `runs_recorded` pade nazaj na 0, disk ne preživi zagona.

    **Predpomnjeno za minuto, ker to ni poceni.** Izmerjeno 4. 9. 2026 na
    828 000 vrsticah `run` in 3,9 mio `obs`: 1 223 ms na klic, od tega 926 ms
    razrez po omrežjih (`run JOIN trip`), 170 ms `COUNT(*) obs` in 105 ms
    `MAX(feed_ts)`. Prepis razreza v dve poizvedbi da isti izid in ni hitrejši
    (980 ms) -- cena je sam pregled `run`, ne `COUNT(DISTINCT)`.

    Ceno plača vsak odprt zavihek: `connections.js` kliče ta endpoint vsakih
    30 s za zeleno piko ob feedu. Brez predpomnilnika je to sekunda dela z
    bazo na zavihek na pol minute, na istem disku, kjer piše zajem.

    Minuta zastarelosti je pri tem nedolžna: feed se bere vsakih 30 s, zato
    "je zajem živ" nima boljše ločljivosti od tega niti v načelu.
    """
    # Razdeljeno: **svezina je sveza, stevci predpomnjeni**.
    #
    # Enotni predpomnilnik za minuto ni bil dovolj: stran anketira vsakih 30 s,
    # zato je vsak drugi klic padel v prazno in placal celo ceno. Pika ob feedu
    # pa svezine ne sme brati iz predpomnilnika -- prag "zajem stoji" je 90 s
    # in desetminutni predpomnilnik bi jo prizgal na rdece brez razloga.
    #
    # `MAX(feed_ts)` je 105 ms, stevci pa 1 100 ms. Sveze torej samo prvo.
    out = dict(_predpomni("health", None, 600, lambda: _conn_klic(_health_stevci),
                          v_ozadju=True))
    with _conn() as conn:
        ts = conn.execute("SELECT MAX(feed_ts) FROM run").fetchone()[0]
        # **Ovire so sveze, ne predpomnjene.** Ista funkcija kot pri
        # `/api/alerts` in `overview.disruptions` -- sicer ime laze. Znotraj
        # desetminutnega predpomnilnika sta se stevilki razsli takoj, ko je
        # ovira potekla ali prisla: izmerjeno 19 proti 20, tri mesta, dve
        # stevilki. Sem sodi, ker je poceni: 0,01 ms proti 35,7 ms za
        # `MAX(feed_ts)`, ki je zunaj predpomnilnika ze prej.
        out["alerts_active"] = alerts.active_count(conn)
    out["last_feed_ts"] = ts
    out["last_feed_at"] = (datetime.fromtimestamp(ts, TZ).isoformat() if ts else None)
    return out


def _health_stevci(conn):
    row = conn.execute(
        "SELECT (SELECT COUNT(*) FROM trip) AS trips,"
        "       (SELECT COUNT(*) FROM station) AS stations,"
        "       (SELECT COUNT(*) FROM obs) AS observations,"
        "       (SELECT COUNT(*) FROM run) AS runs_recorded,"
        "       (SELECT COUNT(DISTINCT service_date) FROM run) AS days_covered"
    ).fetchone()
    out = dict(row)
    # Po omrežjih: skupna številka ne pove, ali je odpadel zajem vlakov ali
    # avtobusov, in prav to je tisto, kar hoče nadzor vedeti.
    out["by_network"] = {
        r["network"]: {"trips": r["trips"], "runs": r["runs"],
                       "last_feed_ts": r["last_feed_ts"]}
        for r in conn.execute(
            "SELECT t.network, COUNT(DISTINCT t.trip_id) AS trips,"
            "       COUNT(r.trip_id) AS runs, MAX(r.feed_ts) AS last_feed_ts "
            "FROM trip t LEFT JOIN run r USING (trip_id) GROUP BY t.network"
        )
    }
    out["vehicles_with_gps"] = conn.execute(
        "SELECT COUNT(*) FROM vehicle_now").fetchone()[0]
    # Senca: koliko obratovalnih dni je ze nabranih. Brez tega se da to
    # prebrati samo iz baze, do katere na strezniku ni dostopa brez sudo --
    # in prav strezni stroj je tisti, ki tece ves cas in katerega senca
    # odloca. 21 ms na 47 892 vrsticah; health je itak predpomnjen.
    sen = conn.execute(
        "SELECT COUNT(*) AS vseh, SUM(actual_s IS NOT NULL) AS razresenih,"
        "       MIN(service_date) AS od, MAX(service_date) AS do_,"
        "       COUNT(DISTINCT service_date) AS dni FROM napoved").fetchone()
    out["senca"] = {"dni": sen["dni"], "od": sen["od"], "do": sen["do_"],
                    "vrstic": sen["vseh"], "razresenih": sen["razresenih"]}
    path = Path(config.DB_PATH)
    out["db_bytes"] = path.stat().st_size if path.exists() else 0
    # `db_path` je bil tu, dokler je bil health viden samo domacemu omrezju.
    # Zdaj je endpoint javen: pot do datoteke na strezniku ni nicija stvar in
    # nihce je ne bere -- velikost pove isto o zdravju, brez razkritja.
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

    def izracun():
        today = now.date().isoformat()
        # Pregled je zeleznicki ("kako vozijo vlaki"), zato filter. Endpointa
        # `api_live` se tu ne klice: Python bi kot argument podal FastAPIjev
        # objekt Query namesto None in filter se ne bi ujel z nicimer.
        live = _live("zeleznica")
        with _conn() as conn:
            day = stats.day_summary(conn, today)
            disruptions = alerts.active_count(conn)
            # Zgodaj zjutraj je danasnji vzorec prazen ali droben. "Mediana
            # 0 min, tocnih 100 %" iz ene same voznje ob pol enih zvecer ni
            # slika dneva, ampak nakljucje -- takrat raje povemo za vceraj in
            # tako tudi napisemo.
            fallback = None
            if day.get("runs", 0) < MIN_RUNS_FOR_DAY:
                fallback = stats.day_summary(conn, yesterday_iso(now))
        return {"live_trains": len(live), "today": day,
                "yesterday": fallback, "disruptions": disruptions}

    # Dan v kljucu, ker se ob polnoci vsebina spremeni tudi brez novega feeda.
    odgovor = _predpomni(f"overview:{now.date()}", _znacka("rt_fetched"), 60, izracun)
    # `now` je edino, kar mora biti sveze -- kot `age_s` pri legah.
    return {"now": now.isoformat(), **odgovor}


def yesterday_iso(now: datetime) -> str:
    return (now.date() - timedelta(days=1)).isoformat()


@app.get("/api/overview/bus")
def api_overview_bus():
    """Kaj se dogaja z avtobusi zdaj.

    Ločeno od `/api/overview`, ki je železniški. Zgodovine tu skoraj ni --
    zajem avtobusov je nov -- zato pregled govori o **sedanjosti**: koliko
    vozil je na poti, koliko jih ima GPS in kako hitro se premikajo. To je
    tisto, kar o njih res vemo.
    """
    now = datetime.now(TZ)

    # Razdeljeno po tem, OD CESA je kaj odvisno.
    #
    # Prej je bil cel odgovor vezan na `rt_fetched` IN `positions_fetched`,
    # ta pa se osvezi vsakih 10 s (`KAJROS_POSITION_SECONDS`). Predpomnilnik je
    # zato razpadel vsakih deset sekund in z njim tudi `day_summary` (463 ms) in
    # `_live("avtobus")` (768 ms) -- oboje, kar od leg sploh ni odvisno.
    # Izmerjeno 4. 9. 2026: endpoint je bil dosledno 1,3 s, ogrevanje pa mu ni
    # moglo pomagati, ker tece na 30 s.
    #
    # Zdaj se drago predpomni na `rt_fetched` (30 s), stevci vozil pa se
    # preberejo sveze -- ti so poceni in prav oni se z legami spreminjajo.
    def izracun():
        live = _live("avtobus")
        with _conn() as conn:
            day = stats.day_summary(conn, now.date().isoformat(), network="avtobus")
            # Ista varovalka kot pri vlakih, ki je tu manjkala. Brez nje je
            # stran 3. 9. 2026 ob 00:20 kazala "avtobusi +833 min": mediana
            # sestih voznj, od katerih jih je pet nosilo feedovo zamenjavo
            # prometnega dne (glej `.claude/rules/strezba.md`, MAX_LIVE_DELAY_S).
            # `home.js` je `yesterday` ze bral -- samo poslali ga nismo.
            fallback = None
            if day.get("runs", 0) < MIN_RUNS_FOR_DAY:
                fallback = stats.day_summary(conn, yesterday_iso(now), network="avtobus")
        return {"live_vehicles": len(live), "today": day, "yesterday": fallback}

    odgovor = _predpomni(f"overview-bus:{now.date()}",
                         _znacka("rt_fetched"), 60, izracun)
    # Sveze in poceni: 920 vrstic `vehicle_now`, brez poizvedbe cez `run`.
    vehicles, _ = _vehicles_now()
    moving = [v for v in vehicles if (v.get("speed_kmh") or 0) >= 3]
    return {
        "now": now.isoformat(),
        **odgovor,
        "with_gps": len(vehicles),
        "moving": len(moving),
        "median_speed_kmh": (sorted(v["speed_kmh"] for v in moving)[len(moving) // 2]
                             if moving else None),
    }


@app.get("/api/stations")
def api_stations(network: str | None = Query(None, pattern="^(zeleznica|avtobus)$",
                                             description="samo postaje tega omrežja")):
    # 863 kB in 77 ms, vsebina pa se spremeni enkrat na dan ob uvozu GTFS.
    # Predpomnimo ze SERIALIZIRAN JSON, ne seznama slovarjev: sama poizvedba
    # je manjsi del cene, vecino poje pretvorba 9 791 postaj v niz. Zato
    # `Response`, ne navadna vrnitev -- FastAPI bi jo sicer serializiral znova.
    telo = _predpomni(
        f"stations:{network}", _znacka("gtfs_imported_at"), 3600,
        lambda: json.dumps(_conn_klic(lambda c: stats.stations(c, network)),
                           ensure_ascii=False, separators=(",", ":")).encode())
    return Response(content=telo, media_type="application/json")


#: Iskanje postaj sme na ENI strani teci cez obe omrezji -- na poti od vrat
#: do vrat, kjer sta vlak in avtobus lahko v isti verigi. Drugod ostane
#: privzeta `zeleznica`, ker je bilo mesanje merljivo skodljivo.
NETWORK_ISKANJE_Q = Query("zeleznica", pattern="^(zeleznica|avtobus|vse)$",
                          description="zeleznica, avtobus ali vse")


@app.get("/api/stations/index")
def api_station_index(network: str = NETWORK_ISKANJE_Q,
                      koordinate: bool = Query(False, description="dodaj lego postaje")):
    """Imena postaj omrežja, urejena po prometu — za iskanje brez omrežja.

    Vsebina se spremeni enkrat na dan ob uvozu GTFS, zato je predpomnjena
    enako kot `/api/stations`, in to **serializirana**: pretvorba v niz je
    dražja od poizvedbe.

    **To je odgovor na „zakaj iskanje traja pet sekund".** `/api/stations/search`
    za `network=vse` je izmerjeno 1,35 s na razvojnem računalniku in torej okoli
    pet na arwenu — na vsak pritisk tipke. Postaje se ne spreminjajo vsak dan;
    kazalo se naloži enkrat in išče se v brskalniku, tako kot pri iskalniku zvez.
    """
    net = None if network == "vse" else network
    telo = _predpomni(
        f"stations-index:{network}:{int(koordinate)}", _znacka("gtfs_imported_at"), 3600,
        lambda: json.dumps(
            _conn_klic(lambda c: journey.station_index(c, net, koordinate)),
            ensure_ascii=False, separators=(",", ":")).encode())
    return Response(content=telo, media_type="application/json")


@app.get("/api/stations/search")
def api_station_search(q: str = Query(..., min_length=1), limit: int = Query(12, ge=1, le=50),
                       network: str = NETWORK_ISKANJE_Q):
    """Postaje po delnem imenu, brez šumnikov. Iskalnik na telefonu rabi prav to."""
    with _conn() as conn:
        return journey.search_stations(conn, q, limit,
                                       network=None if network == "vse" else network)


@app.get("/api/stations/near")
def api_stations_near(lat: float = Query(..., ge=-90, le=90),
                      lon: float = Query(..., ge=-180, le=180),
                      network: str = NETWORK_Q,
                      limit: int = Query(8, ge=1, le=30)):
    """Postajališča blizu dane točke. Razdalja je zračna, ne po poti."""
    with _conn() as conn:
        return journey.nearby_stations(conn, lat, lon, network, limit)


def _znano_do(conn, network: str) -> dict:
    """Meja voznega reda, ki jo mora prikaz povedati.

    Prazen odgovor cez to mejo ni "ta dan nic ne vozi", ampak "voznega reda
    se ni". Mestni LPP ima svojo, mnogo blizjo mejo (okno osmih dni), zato je
    posebej -- brez tega bi avtobusna stran cez teden dni tiho izpustila vse
    ljubljanske mestne linije in nihce ne bi vedel, zakaj.
    """
    out = {"vozni_red_do": stats.znano_do(conn, network)}
    if network == "avtobus":
        out["lpp_do"] = stats.znano_do(conn, agency="lpp")
    return out


@app.get("/api/departures")
def api_departures(
    station: str = Query(..., description="ime postaje; delno ime je dovolj"),
    date: str | None = None,
    from_time: str | None = Query(None, alias="from", description="HH:MM; privzeto zdaj"),
    window: int | None = Query(None, ge=15, le=1440,
                               description="minut naprej; privzeto 3 h za danes, cel dan sicer"),
    kind: str = Query("odhodi", pattern="^(odhodi|prihodi)$"),
    network: str = NETWORK_Q,
):
    """Odhodna ali prihodna tabla postaje.

    Najpogostejše vprašanje potnika in doslej edino, na katero API ni znal
    odgovoriti -- `connections` je zahteval izhodišče in cilj hkrati.
    """
    now = datetime.now(TZ)
    date = _check_date(date) or now.date().isoformat()
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
        exact = journey.resolve_station(conn, station, network)
        if not exact:
            raise HTTPException(404, f"postaje {station!r} ne poznam")
        # `now_s` samo za danasnji dan: le takrat obstaja meja med tem, kar je
        # vozilo ze prevozilo, in tem, kar je se pred njim.
        now_s = journey.now_seconds(now) if date == now.date().isoformat() else None
        rows = journey.board(conn, exact, date, from_s, window, kind,
                             network=network, now_s=now_s)
        if network == "zeleznica":
            # Obvestila o ovirah so SZ-jeva in vezana na vlak.
            notices = alerts.for_trains(conn, [r["train_no"] for r in rows],
                                        mentions=[exact])
        else:
            # Mestni LPP poslje eno samo vrsto obvestila -- „tu se avtobus ne
            # bo ustavil" -- in ta je vezana na POSTAJALISCE, ne na vozjno.
            # Doslej je ni videl nihce: feed jo je nosil, mi pa smo jo zavrgli.
            notices = alerts.for_stops(
                conn, [r["stop_id"] for r in conn.execute(
                    "SELECT stop_id FROM station WHERE name = ?", (exact,))])
        meje = _znano_do(conn, network)
    return {"station": exact, "date": date, "kind": kind, "network": network,
            **meje,
            "from_s": from_s, "window_min": window,
            "board": rows, "alerts": notices}


@app.get("/api/alerts")
def api_alerts(lang: str = Query("sl", pattern="^(sl|en)$"),
               napovedane: bool = Query(True, description="tudi tiste, ki se še niso začele")):
    """Ovire: dela na progi, nadomestni prevozi, združene garniture.

    Privzeto **tudi napovedane** (do 14 dni naprej), označene z
    `napovedana: true`. Brez njih je stran ovir molčala o delih, ki se
    začnejo jutri — glej `alerts.active()`.
    """
    with _conn() as conn:
        return alerts.active(conn, lang, tudi_napovedane=napovedane)


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
    date = _check_date(date)
    with _conn() as conn:
        date = date or _active_service_date(conn, train_no, datetime.now(TZ))
        return {"train_no": train_no, "service_date": date,
                "reports": alerts.train_reports(conn, train_no, date)}


# Odgovor se med dvema branjema leg ne spremeni, zato ga izracunamo enkrat na
# cikel in vsem strezemo iste vrstice. Brez tega bi sto hkratnih obiskovalcev
# pomenilo sto enakih poizvedb -- pri legah, ki se osvezijo desetkrat na
# minuto, je to edini del prikaza, kjer je stevilo uporabnikov sploh vidno.
# Kljuc je cas nasega zadnjega branja (`positions_fetched`), ne ura: tako se
# predpomnilnik razveljavi natanko takrat, ko je res kaj novega.
_VEHICLES_CACHE: dict = {"key": None, "rows": []}


# ---------------------------------------------------------------- predpomnilnik
# Isti razlog kot pri legah, le za ostale drage odgovore. Izmerjeno 3. 9. 2026
# na tem racunalniku: `/api/live` 253 ms, `/api/overview` 224 ms,
# `/api/stations` 77 ms (863 kB, 217 kB stisnjeno). Na malini Pi 4B je to
# desetkrat toliko, torej `/api/live` okoli 2,5 s -- in vsak obiskovalec ga
# vprasa vsakih 30 s. Brez tega je zgornja meja ~10-15 hkratnih uporabnikov;
# z njim tisoc obiskovalcev stane toliko kot eden.
#
# Kljuc je ZNACKA PODATKA (`rt_fetched`, `positions_fetched`,
# `gtfs_imported_at`), ne ura -- predpomnilnik se razveljavi natanko takrat,
# ko je res kaj novega. `najvec_s` je varovalka za primer, ko zajem ne tece
# (`KAJROS_COLLECTOR=0`): znacka se takrat ne spreminja in odgovor bi sicer
# obstal za vedno.
_ODGOVORI: dict[str, tuple] = {}
_ODGOVORI_LOCK = threading.Lock()
_KLJUCAVNICE: dict[str, threading.Lock] = {}


def _kljucavnica(kljuc: str) -> threading.Lock:
    with _ODGOVORI_LOCK:
        return _KLJUCAVNICE.setdefault(kljuc, threading.Lock())


def _predpomni(kljuc: str, znacka, najvec_s: float, izracun,
               v_ozadju: bool = False):
    """Vrne predpomnjen odgovor ali ga izracuna in shrani.

    Kljucavnica je NA KLJUC, ne skupna: sicer bi ob izteku vsi hkratni
    obiskovalci racunali isto stvar (naval na prazen predpomnilnik), skupna
    kljucavnica pa bi drage odgovore med sabo serializirala.

    `v_ozadju=True` postrezi **staro vrednost** in jo osvezi v niti. Za
    izracune, ki so predragi, da bi jih kdo cakal: brez tega placa polno ceno
    vsak, ki po izteku prvi pride mimo. Izmerjeno 8. 9. 2026 na `/api/health`
    po prilitju: `COUNT(*) obs` 932 ms in razrez po omrezjih 1 452 ms s toplim
    predpomnilnikom, ob hladnem pa je bil odziv **13 s**.

    Prvi klic po zagonu vrednosti se nima in jo mora izracunati sinhrono --
    stara vrednost, ki je ni, ni izbira.
    """
    zdaj = time.monotonic()
    zapis = _ODGOVORI.get(kljuc)
    if zapis and zapis[0] == znacka and zdaj - zapis[2] < najvec_s:
        return zapis[1]
    if v_ozadju and zapis is not None and zapis[0] == znacka:
        # Stara vrednost je tu; osvezi jo v ozadju in postrezi zdaj. Kljucavnica
        # poskrbi, da tece **ena** osvezitev, ne ena na obiskovalca.
        if _kljucavnica(kljuc).acquire(blocking=False):
            def _osvezi():
                try:
                    _ODGOVORI[kljuc] = (znacka, izracun(), time.monotonic())
                finally:
                    _kljucavnica(kljuc).release()
            threading.Thread(target=_osvezi, daemon=True).start()
        return zapis[1]
    with _kljucavnica(kljuc):
        zapis = _ODGOVORI.get(kljuc)          # medtem ga je morda izracunal kdo drug
        if zapis and zapis[0] == znacka and time.monotonic() - zapis[2] < najvec_s:
            return zapis[1]
        vrednost = izracun()
        _ODGOVORI[kljuc] = (znacka, vrednost, time.monotonic())
        return vrednost


def _conn_klic(f):
    """Odpre povezavo in poklice `f(conn)`.

    Za predpomnjene izracune: `with` v lambdi ni mogoc, ta jo pa lepo zavije.
    """
    with _conn() as conn:
        return f(conn)


def _znacka(*kljuci: str) -> tuple:
    """Trenutne znacke podatkov iz `meta`, kot n-terica za primerjavo."""
    with _conn() as conn:
        return tuple(db.get_meta(conn, k) for k in kljuci)


def _vehicles_rows(conn, zdaj: datetime) -> list[dict]:
    """Vsa vozila z GPS, brez `age_s`. Ta je odvisen od trenutka in se doda
    ob strezbi -- sicer bi predpomnjen odgovor lagal o starosti lege."""
    now = int(zdaj.timestamp())
    now_s = journey.now_seconds(zdaj)
    rows = conn.execute(
        "SELECT v.*, t.train_no, t.mode, t.agency, t.headsign, t.network "
        "FROM vehicle_now v JOIN trip t USING (trip_id) "
        "WHERE v.seen_ts >= ? ORDER BY t.train_no",
        (now - collector.POSITION_FRESH_S,),
    ).fetchall()
    out = [dict(r) for r in rows]
    for d in out:
        d["speed_kmh"] = round(d["speed_ms"] * 3.6) if d["speed_ms"] is not None else None

    # Zamude v `vehicle_now` NI -- ta tabela pozna samo lego. Doda se iz
    # zadnje **prevozene** postaje, po istem pravilu kot zivi seznam in
    # okno voznje (`stats.last_measured`). Brez tega je kartica na
    # zemljevidu pisala "? min" za avtobus, ki je na svoji strani imel
    # +15 -- dve stevilki o istem vozilu, in ena od njiju izmisljena.
    po_dnevih: dict[str, list[str]] = {}
    for d in out:
        po_dnevih.setdefault(d["service_date"] or zdaj.date().isoformat(),
                             []).append(d["trip_id"])
    izmerjeno: dict[str, dict] = {}
    for dan, ids in po_dnevih.items():
        # Voznja cez polnoc ima vcerajsnji prometni dan, zato je "zdaj" v
        # njenih sekundah cez 86400.
        try:
            zamik = (zdaj.date() - date.fromisoformat(dan)).days * 86400
        except ValueError:
            zamik = 0
        izmerjeno.update(stats.last_measured(conn, dan, ids, now_s + zamik))

    for d in out:
        m = izmerjeno.get(d["trip_id"])
        d["delay_s"] = m["delay_s"] if m else None
        d["last_stop"] = m["name"] if m else None
        d["measured_seq"] = m["stop_seq"] if m else None
    return out


def _vehicles_now(trip: str | None = None) -> tuple[list[dict], int]:
    """Vozila z GPS kot NAVADEN seznam in sekunde do naslednjega branja.

    Loceno od endpointa namenoma: ta vraca `JSONResponse` zaradi glave
    `X-Osvezi-Cez`, in `JSONResponse` ni iterabilen. Ko je `/api/overview/bus`
    klical endpoint naravnost, je zato vracal 500 -- domaca stran je pisala
    "podatki trenutno niso dosegljivi" in obe stevilki kot "-".
    """
    zdaj = datetime.now(TZ)
    now = int(zdaj.timestamp())
    with _conn() as conn:
        brano = db.get_meta(conn, "positions_fetched")
        if _VEHICLES_CACHE["key"] != brano or brano is None:
            _VEHICLES_CACHE["rows"] = _vehicles_rows(conn, zdaj)
            _VEHICLES_CACHE["key"] = brano

    # `age_s` se racuna ob vsaki strezbi, ne ob predpomnjenju: starost lege je
    # edino, kar se med dvema branjema res spreminja, in prav ona pove, koliko
    # je piki na zaslonu mogoce verjeti.
    out = []
    for d in _VEHICLES_CACHE["rows"]:
        if trip is not None and d["trip_id"] != trip:
            continue
        d = dict(d)
        d["age_s"] = now - d["seen_ts"]
        out.append(d)

    cez = config.POSITION_SECONDS
    if brano:
        cez = max(1, config.POSITION_SECONDS - (now - int(brano)))
    return out, cez


@app.get("/api/vehicles")
def api_vehicles(trip: str | None = None):
    """Trenutna lega vozil z GPS.

    Feed `vehicle_positions` nosi **samo avtobuse**. Za vlak lege ni in je
    ta seznam nikoli ne bo vseboval -- kar aplikacija riše za vlake, je
    zadnja postaja z meritvijo, ne položaj.

    `trip` zameji na eno vožnjo: okno vožnje rabi eno vrstico in ne stotih.

    Glava `X-Osvezi-Cez` pove, čez koliko sekund bomo lege brali znova.
    Brez nje brskalnik ugiba in polovico svojega ritma zapravi za čakanje na
    podatek, ki v bazi že leži.
    """
    out, cez = _vehicles_now(trip)
    return JSONResponse(out, headers={"X-Osvezi-Cez": str(cez)})


@app.get("/api/trip/{trip_id}/shape")
def api_shape(trip_id: str):
    """Trasa ene vožnje po cesti oziroma progi.

    Za avtobuse je to edini vir: `edge` ima mrežo železniških prog, avtobusi
    pa vozijo po cesti in vanjo namenoma ne gredo.
    """
    with _conn() as conn:
        row = conn.execute(
            "SELECT sh.points FROM trip t JOIN shape sh USING (shape_id) "
            "WHERE t.trip_id = ?", (trip_id,)).fetchone()
    if not row:
        raise HTTPException(404, "za to vožnjo trase ni")
    return {"trip_id": trip_id, "points": json.loads(row["points"])}


@app.get("/api/shapes/live")
def api_shapes_live():
    """Trase vseh vozil, ki so zdaj na poti — po obliki, ne po vožnji.

    Dve vozili iste linije v isti smeri imata isto traso, zato jih zdruzimo.
    Izmerjeno 7. 9. 2026, po vklopu mestnega LPP: **427 oblik in 1,83 MB**
    pred gzipom (prej 128 oblik in 539 kB). Mestne linije so traso potrojile.

    Plast je izbirna in **privzeto ugasnjena** -- gost snop crt cez vso
    Ljubljano je odgovor na vprasanje "kod vozijo linije", ne na "kje je moj
    avtobus". Zato ta velikost zadene samo tistega, ki jo vklopi, in se
    predpomni za minuto. Ce bi kdaj postala privzeta, jo je treba najprej
    razredciti (Douglas-Peucker je v `geo.py` ze).
    """
    # Vezano na lege: dokler se vozila ne premaknejo, so trase iste.
    return _predpomni("shapes-live", _znacka("positions_fetched"), 60, _shapes_live_rows)


def _shapes_live_rows():
    now = int(datetime.now(TZ).timestamp())
    with _conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT sh.shape_id, sh.points, t.network "
            "FROM vehicle_now v JOIN trip t USING (trip_id) "
            "JOIN shape sh ON sh.shape_id = t.shape_id "
            "WHERE v.seen_ts >= ?",
            (now - collector.POSITION_FRESH_S,),
        ).fetchall()
    return [{"shape_id": r["shape_id"], "network": r["network"],
             "points": json.loads(r["points"])} for r in rows]


@app.get("/api/network.geojson")
def api_network(elementary_only: bool = True):
    """Geometrija prog z dolžino odseka v km. Za risanje zemljevida."""
    # Cista statika: spremeni se samo ob uvozu voznega reda.
    telo = _predpomni(
        f"geojson:{elementary_only}", _znacka("gtfs_imported_at"), 3600,
        lambda: json.dumps(_conn_klic(lambda c: stats.network_geojson(c, elementary_only)),
                           ensure_ascii=False, separators=(",", ":")).encode())
    return Response(content=telo, media_type="application/json")


@app.get("/api/train/{train_no}")
def api_train(train_no: str, trip: str | None = None):
    """Vozni red ene vožnje. `trip` je nujen pri avtobusu -- številka linije
    ni številka vožnje in brez njega dobiš poljubno od 217 voženj."""
    with _conn() as conn:
        rows = stats.timetable(conn, train_no, datetime.now(TZ).date().isoformat(), trip)
        if not rows:
            raise HTTPException(404, f"vlak {train_no} ne obstaja")
        return {"train_no": train_no, "trip_id": trip,
                "mode": stats.trip_mode(conn, train_no), "timetable": rows}


def _lpp_zivo(conn, trip_id: str | None, rows: list[dict], service_date: str,
              meja_seq: int | None, zdaj: datetime) -> str | None:
    """Napoved za postanke NAPREJ zamenjaj s svežejšo, kadar jo LPP ponuja.

    Zakaj sploh: derp.si naredi nov posnetek na ~90 s, `data.lpp.si` na
    10-30 s (izmerjeno 7. 9. 2026). Za mestni LPP je vse za mejo tako ali tako
    napoved -- feed pošlje samo postanke pred vozilom -- zato tu ne prepišemo
    nobene meritve, le napoved z novejšo napovedjo.

    Meritve se **nikoli** ne dotakne: pogoj je `stop_seq > meja_seq`. Vrne ime
    vira, kadar je kaj prepisal, sicer `None` -- prikaz mora povedati, čigava
    številka je na zaslonu.
    """
    if not trip_id or service_date != zdaj.date().isoformat():
        return None
    # Lega mora biti SVEZA. `vehicle_now` hrani vrstico do ure po koncu voznje,
    # in stara vrstica bi vozilo vezala na voznjo, ki je ze koncana -- takrat
    # eta pripada NASLEDNJEMU obhodu istega vzorca in bi na zaslon prinesla
    # ure z druge voznje. Ujeto pri preizkusu: meja postanek 37, eta za
    # postanek 1.
    v = conn.execute(
        "SELECT vehicle_id FROM vehicle_now WHERE trip_id = ? AND seen_ts >= ?",
        (trip_id, int(zdaj.timestamp()) - collector.POSITION_FRESH_S)).fetchone()
    if not v or not v["vehicle_id"]:
        return None
    eta = lpp.eta_po_postankih(conn, trip_id, v["vehicle_id"])
    if not eta:
        return None
    now = int(zdaj.timestamp())
    prepisanih = 0
    for s in rows:
        m = eta.get(s["stop_seq"])
        if m is None or (meja_seq is not None and s["stop_seq"] <= meja_seq):
            continue
        vozni_red = s["sched_arr"] or s["sched_dep"]
        if not vozni_red:
            continue
        napovedan = now + m * 60
        zamuda = napovedan - int(datetime.fromisoformat(vozni_red).timestamp())
        s["zamuda"] = stats.opis_zamude(zamuda, "živo")
        s["eta_min"] = m
        prepisanih += 1
    return "LPP" if prepisanih else None


@app.get("/api/train/{train_no}/run")
def api_run(train_no: str, date: str | None = None,
            trip: str | None = Query(None, description="id vožnje, kadar številka ni enolična")):
    """Ena vožnja: vozni red, zamuda in izračunani dejanski časi.

    `trip` je potreben pri avtobusih: `route_short_name` je številka linije in
    LPP linija 3G ima 388 voženj. Odhodna tabla in iskalnik id poznata, zato
    ga podata naprej; brez njega izberemo glavno različico.
    """
    date = _check_date(date)
    with _conn() as conn:
        date = date or _active_service_date(conn, train_no, datetime.now(TZ))
        # Vrnemo RAZRESENO vozjno, ne tistega, kar je poslal odjemalec. Prej je
        # bil `trip_id` pri vlaku brez `?trip=` vedno None, zato prikaz naprej
        # ni vedel, katero od vec voznj z isto stevilko gleda -- in `predict`
        # se je ucil iz vseh treh hkrati. LP 4208 ima tri.
        razresen = stats.resolve_trip(conn, train_no, date, trip)
        # Zahtevana vozjna, ki ne obstaja, je napaka -- ne povod, da izberemo
        # drugo. Brez te straze bi razresen=None spet pomenil "izberi sam" in
        # zastarela deljena povezava bi pokazala tuj vozni red.
        if trip and not razresen:
            raise HTTPException(404, f"vožnje {trip!r} pod številko {train_no} ne poznam")
        rows = stats.run_detail(conn, train_no, date, razresen)
        if not rows:
            raise HTTPException(404, f"vožnje {train_no} ne poznam")
        ident = stats.trip_identity(conn, train_no, razresen)
        # Mejo med meritvijo in napovedjo pove STREZNIK, ne odjemalec.
        # `common.lastMeasured()` jo je racunal sam -- isto pravilo v dveh
        # jezikih, in ce se razideta, je razlika tiha napaka na zaslonu.
        # Po zapisu v CLAUDE.md je bila ta napaka tam ze dvakrat.
        #
        # Za pretekli ali prihodnji dan meje ni: dan je koncan (vse v `run` JE
        # meritev) ali se ni zacel. Takrat vzamemo trenutek za koncem vseh
        # voznj -- isto kot `journey.board()`.
        zdaj = datetime.now(TZ)
        now_s = (journey.now_seconds(zdaj) if date == zdaj.date().isoformat()
                 else 48 * 3600)
        meja = stats.last_measured(conn, date, [razresen], now_s).get(razresen)
        meja_seq = meja["stop_seq"] if meja else None
        # Vrsto zamude dopisemo tu, ker mejo pozna sele endpoint. Postanek za
        # mejo nosi feedovo NAPOVED, ne meritve -- in prav to je razlika, ki
        # je bila ze dvakrat na zaslonu narobe. Odjemalec zdaj ne sklepa:
        # `zamuda.vrsta` mu pove naravnost.
        for s in rows:
            if s["zamuda"] is None:
                continue
            # Postanek, katerega ura si nasprotuje z vecino ostalih, ni
            # meritev -- glej `stats.oznaci_neskladne()`. Brez tega je bila
            # na zaslonu ura, ki tece nazaj, pri vsaki deseti vozjni avtobusa.
            # "Izmerjeno" pomeni opažanje, in to je feed potrdil samo, če je
            # vrednost osvežil PO trenutku, ko trdi prehod. Pri železnici se to
            # zgodi v 0,4 % primerov -- do 9. 9. 2026 je ta beseda tam trdila
            # opažanje, ki ga skoraj nikoli nimamo.
            prehod = s.get("actual_dep") or s.get("actual_arr")
            potrjen = stats.potrjen_prehod(
                s.get("feed_ts"),
                int(datetime.fromisoformat(prehod).timestamp()) if prehod else None)
            s["zamuda"]["vrsta"] = ("neskladno" if s.get("neskladno")
                                    else (stats.IZMERJENO if potrjen
                                          else stats.ZADNJI_PODATEK)
                                    if meja_seq is not None and s["stop_seq"] <= meja_seq
                                    else "napoved prevoznika")
        # **Obicajna zamuda iz zgodovine, za postanke brez meritve.**
        # Iskalnik jo je imel ze prej (`typical_dep`), okno vozjne pa ne --
        # zato je bilo pri vozjni, ki se ni odpeljala, povsod "?" in "brez
        # ocene", ceprav o njej vemo, kako je vozila zadnjih devetnajstkrat.
        # Ni napoved za ta dan; je opis preteklih voznj in prikaz jo mora
        # tako tudi imenovati.
        if razresen:
            typ = stats.typical_at_stops(
                conn, [(razresen, s["stop_seq"]) for s in rows])
            for s in rows:
                s["typical"] = typ.get((razresen, s["stop_seq"]))
            stats.typical_na_izhodisce(rows)
        zivo = _lpp_zivo(conn, razresen, rows, date, meja_seq, zdaj)
        # **Kdaj je feed o tej voznji nazadnje kaj rekel.** Brez tega prikaz ne
        # more lociti sveze stevilke od zadnje znane -- in prav ta razlika je
        # bila 8. 9. 2026 na zaslonu: LPV 2001 je ob 07:00 kazal "+6 min,
        # izmerjeno", medtem ko je bila zadnja novica o njem stara 7 minut in
        # je feed cez cetrt ure povedal +29.
        zadnja = max((s["feed_ts"] for s in rows if s.get("feed_ts")), default=None)
        return {"train_no": train_no, "service_date": date, "trip_id": razresen,
                **ident, "last_measured_seq": meja_seq,
                "zadnja_beseda": zadnja,
                "tiho_s": (int(zdaj.timestamp()) - zadnja) if zadnja else None,
                "zivi_vir": zivo, "stops": rows}


@app.get("/api/train/{train_no}/history")
def api_history(train_no: str, days: int = Query(90, ge=1, le=3650),
                exclude_date: str | None = None, trip: str | None = None):
    """Zgodovina te poti. `exclude_date` izpusti en prometni dan -- prikaz
    tekoče vožnje ga rabi, da povprečje ne vsebuje vožnje, ki jo riše zraven.

    `trip` zamejí na eno vožnjo. Brez njega se pri avtobusu sešteje vseh 217
    voženj linije, in ker profil teče po zaporedni številki postanka, se pod
    isto oznako znajdeta obe smeri."""
    with _conn() as conn:
        return stats.history(conn, train_no, days, exclude_date, trip)


@app.get("/api/train/{train_no}/weather")
def api_run_weather(train_no: str, date: str | None = None, trip: str | None = None):
    """Vreme na vsaki postaji te vožnje, po uri, ko je vlak tam."""
    date = _check_date(date)
    with _conn() as conn:
        date = date or _active_service_date(conn, train_no, datetime.now(TZ))
        rows = stats.run_weather(conn, train_no, date, trip)
        if not rows:
            raise HTTPException(404, f"vlak {train_no} ne obstaja")
        return {"train_no": train_no, "service_date": date, "stops": rows}


@app.get("/api/train/{train_no}/predict")
def api_predict(train_no: str, stop_seq: int, delay_s: int,
                days: int = Query(90, ge=1, le=3650),
                exclude_date: str | None = None, trip: str | None = None):
    """Napoved zamude naprej po progi, glede na trenutno zamudo.

    `exclude_date` izpusti prikazani prometni dan iz učenja -- isto kot pri
    zgodovini, sicer bi ogled končanega dne deloma napovedoval iz odgovora.
    """
    exclude_date = _check_date(exclude_date)
    with _conn() as conn:
        return {"train_no": train_no, "from_stop_seq": stop_seq,
                "current_delay_s": delay_s,
                "forecast": stats.predict(conn, train_no, stop_seq, delay_s, days,
                                          exclude_date, service_date=exclude_date,
                                          trip_id=trip)}


@app.get("/api/train/{train_no}/vehicle")
def api_vehicle_chain(train_no: str, date: str | None = None,
                      trip: str | None = None):
    """Veriga voznj istega vozila: kje je zdaj in kam gre potem.

    Edini nacin, da povemo kaj o avtobusu, ki se ni zacel voziti -- takrat
    zanj ni ne zamude ne lege, vozilo pa obstaja in je na prejsnji voznji.

    Vrne prazno pri vlakih in pri avtobusih brez `block_id`: SZ ga nimajo,
    ostali prevozniki pa le pri tretjini voznj. Podrobno v `stats.vehicle_chain`.
    """
    date = _check_date(date)
    now = datetime.now(TZ)
    with _conn() as conn:
        date = date or _active_service_date(conn, train_no, now)
        chain = stats.vehicle_chain(
            conn, train_no, date, trip,
            now_ts=int(now.timestamp()),
            now_s=journey.now_seconds(now) if date == now.date().isoformat() else None)
    return {"train_no": train_no, "service_date": date, **chain}


# Stran `/app/statistika` je odstranjena, ker jo bomo preuredili -- ta dva
# endpointa in dnevni povzetek za njima pa ostaneta. To NI spregledan mrtev
# kod: razrez je izmerjen, pokrit s testi in se enkrat na dan ze racuna
# (`KAJROS_MAINT_HOUR`); brisati ga zato, da bi ga cez teden dni pisali znova,
# bi bilo drazje od tega komentarja. Kdor ju cez cas najde brez odjemalca in
# nove strani ni, naj ju odstrani.
@app.get("/api/stats/breakdowns")
def api_breakdowns(days: int = Query(90, ge=1, le=3650), network: str = NETWORK_Q,
                   fresh: bool = False):
    """Končne zamude po vrsti vlaka, uri odhoda, dnevu v tednu in dnevu.

    Postrezeno iz dnevnega povzetka. `fresh=1` obide predpomnilnik -- pri letu
    zajema je to nekaj sekund, zato ni privzeto.
    """
    with _conn() as conn:
        if fresh:
            return stats.summary_build(conn, "breakdowns", network, days)
        return stats.summary_get(conn, "breakdowns", network, days)


@app.get("/api/stats")
def api_stats(days: int = Query(90, ge=1, le=3650), network: str = NETWORK_Q,
              fresh: bool = False):
    """Lestvica voženj po zamudi ob koncu poti (iz dnevnega povzetka)."""
    with _conn() as conn:
        if fresh:
            return stats.summary_build(conn, "network_stats", network, days)
        return stats.summary_get(conn, "network_stats", network, days)


# Vlak ostane na seznamu se toliko sekund po voznorednem (z zamudo popravljenem)
# prihodu na cilj -- da ne izgine iz zemljevida v isti sekundi, ko pripelje.
_LIVE_GRACE_S = 300

# Najvecja zamuda, pri kateri voznjo se stejemo za zivo. To ni okrasna
# konstanta, ampak pravilo prikaza, in velja na obeh straneh polnoci.
#
# Sest ur je velikodusno. Merjeno na zajetih podatkih: pri zeleznici ni
# NOBENE zamude cez tri ure (najhujsa je EC 79 z 2,9 h), pri avtobusih pa je
# nad sest ur 0,67 % vrstic -- in te niso zamude. Nomagov N6571 je imel
# 27 060 s (7 h 31 min) enako na vseh 44 postankih vozjne, ki je po voznem
# redu vozila ob 04:15; to je feedova zamenjava prometnega dne, ne avtobus,
# ki se ob pol enih popoldne se vedno vozi. Prej je tak zapis pristal na
# zemljevidu kot vozilo na progi.
#
# Isto stevilo je tudi meja za vcerajsnji prometni dan: vozjna z voznorednim
# koncem pred 18:00 in vec kot sesturno zamudo po polnoci izpade s seznama.
# poizvedbo (173 ms -> 17 ms), ne spregled.
MAX_LIVE_DELAY_S = 6 * 3600

_LIVE_SQL = """
WITH t AS (
    SELECT r.trip_id, r.stop_seq, r.feed_ts, s.stop_id,
           COALESCE(r.delay_dep, r.delay_arr) AS delay_s,
           COALESCE(s.dep_s, s.arr_s) AS t_s
    FROM run r
    JOIN sched s ON s.trip_id = r.trip_id AND s.stop_seq = r.stop_seq
    -- Omrezje omejimo TU, ne sele v Pythonu: z LPP v bazi je vrstic vec kot
    -- petkrat toliko in okenske funkcije spodaj tecejo cez vse. Na tem
    -- prenosniku 190 ms proti 90 ms, na Pi Zero bi bila razlika sekunde.
    JOIN trip tn ON tn.trip_id = r.trip_id
                AND (:network IS NULL OR tn.network = :network)
                -- Vozjne, ki se po voznem redu zdaj lahko vozijo. Brez tega
                -- gre skozi okenske funkcije spodaj cel dan -- pri vseh
                -- prevoznikih 135 000 vrstic za 735 vozil. Okvir je zato
                -- stolpec v `trip` in ne grupiranje `sched` ob vsakem klicu.
                AND tn.start_s <= :now_s
                AND tn.end_s >= :now_s - :max_delay
    WHERE r.service_date = :day
      -- Vcerajsnji prometni dan gledamo SAMO zaradi voznj, ki segajo cez
      -- polnoc. Brez tega pogoja gre cel vcerajsnji dan skozi okenske
      -- funkcije, da na koncu vrne nic: 173 ms za prazen odgovor.
      --
      -- Zamuda mora biti v racunu. Vlak z voznorednim prihodom ob 21:48 in
      -- 161 minutami zamude pripelje ob 00:29 in JE cez polnoc, ceprav
      -- njegov vozni red tega ne pove. Prvi poskus je to izpustil in prav
      -- ta primer je tisti, ki potnika najbolj zanima.
      -- Ne po voznem redu samem in ne z zdruzevanjem `run` (oboje je bilo
      -- 170 ms): dovolj je voznoredni konec, zamaknjen za dopustno zamudo.
      --
      -- Podpoizvedba, ne EXISTS: EXISTS je koreliran in tece enkrat na
      -- vrstico `run`, torej 142 000-krat na dan vseh prevoznikov. Tale se
      -- ovrednoti enkrat, da 3 551 voznj cez polnoc, in `run` se potem
      -- pobira po svojem prvotnem kljucu. Merjeno na letu zajema, obe
      -- omrezji: 392 ms -> 65 ms.
      --
      -- `trip.end_s` in ne `MAX(COALESCE(arr_s, dep_s))` cez `sched`: to je
      -- natanko ista vrednost (`db.fill_trip_window` jo tako racuna), le da
      -- je ze shranjena. Preverjeno, da data isto mnozico 3 551 voznj;
      -- 98,4 ms -> 5,1 ms. Isti vzorec kot `first_seq` pri odhodni tabli.
      AND (:overnight_only = 0 OR r.trip_id IN (
            SELECT trip_id FROM trip WHERE end_s > 86400 - :max_delay))
),
-- Feed za se nedosezene postanke pogosto objavi niclo, dokler nima prave
-- napovedi. Brez tega bi tak zapis pomenil, da je (voznored + 0) ze minil,
-- in vlak bi na zemljevidu skocil naprej. Zamuda ne pade z dvajsetih minut
-- na nic med dvema sosednjima postajama, zato tako vrstico preskocimo.
ranked AS (
    SELECT t.*, MAX(COALESCE(t.delay_s, 0)) OVER (
               PARTITION BY t.trip_id ORDER BY t.stop_seq
               ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS prev_max,
           -- Zamuda na ZADNJEM znanem postanku vozjne. Prej je bila svoj CTE
           -- (`tail`) in spojena nazaj po `trip_id` -- SQLite ga je
           -- materializiral BREZ indeksa, zato je za vsako vrstico `passed`
           -- pregledal cel `tail`. Pri zeleznici je to 2 000 x 2 000 in se
           -- ne pozna, z LPP v bazi pa 59 557 x 59 557 = 3,5 milijarde
           -- primerjav: **216 s proti 1,5 s**. Ista vrednost je okenska
           -- funkcija cez isti okvir, brez spoja in brez druge ovrednotitve
           -- CTE `t`. Izmerjeno: 216 s -> 4,3 s, izid pri zeleznici enak
           -- vrstico za vrstico.
           LAST_VALUE(t.delay_s) OVER (
               PARTITION BY t.trip_id ORDER BY t.stop_seq
               ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS end_delay_s,
           -- Zadnja osvezitev katerega od PREJSNJIH postankov. Postanek,
           -- osvezen prej kot ta, je ostanek, ki ga feed ni vec potrdil --
           -- isto varovalo kot v `stats._LAST_MEASURED_SQL`. Brez njega bi
           -- zemljevid vozilo postavil na napacno postajo z napacno zamudo.
           MAX(t.feed_ts) OVER (
               PARTITION BY t.trip_id ORDER BY t.stop_seq
               ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS prev_ts
    FROM t
),
-- Zadnji trenutek, ko je feed o TEJ voznji sploh kaj rekel. Isto pravilo kot
-- `stats.last_measured()`: meja med meritvijo in napovedjo ne sme prehiteti
-- feeda, sicer se s casom sama od sebe razsiri do konca proge in pika na
-- zemljevidu pripelje na cilj, ceprav o voznji ze pol ure ne vemo nicesar.
zadnja_beseda AS (
    SELECT trip_id, MAX(feed_ts) AS zadnji_ts FROM t GROUP BY trip_id
),
passed AS (
    SELECT r.*, ROW_NUMBER() OVER (PARTITION BY r.trip_id ORDER BY r.stop_seq DESC) AS rn
    FROM ranked r JOIN zadnja_beseda z ON z.trip_id = r.trip_id
    WHERE r.t_s + COALESCE(r.delay_s, 0) <= :now_s
      AND r.t_s + COALESCE(r.delay_s, 0) <= z.zadnji_ts - :polnoc
      AND NOT (COALESCE(r.delay_s, 0) = 0 AND r.prev_max >= 300)
      AND NOT (r.feed_ts IS NOT NULL AND r.prev_ts IS NOT NULL AND r.feed_ts < r.prev_ts)
)
SELECT tr.train_no, tr.headsign, tr.mode, tr.network, p.trip_id,
       st.name AS last_stop, p.stop_seq,
       p.delay_s, p.feed_ts, p.t_s AS sched_s
FROM passed p
JOIN trip tr ON tr.trip_id = p.trip_id
JOIN station st ON st.stop_id = p.stop_id
WHERE p.rn = 1
  AND :now_s <= tr.end_s + COALESCE(p.end_delay_s, 0) + :grace
ORDER BY p.delay_s DESC
"""


def _live_rows(conn, service_date: str, now_s: int,
               network: str | None = None, overnight_only: bool = False) -> list[dict]:
    """Vlaki, ki na dani prometni dan ob `now_s` (sekunde od polnoci tega dne)
    dejansko vozijo. Zadnja znana postaja je zadnja, katere cas je ze minil --
    ne zadnja, o kateri feed porocá: feed poslje napoved tudi za naslednjo
    postajo, po koncu voznje pa ostane zapisan cilj."""
    # Polnoc prometnega dne v sekundah od epohe: `t_s` steje od nje, `feed_ts`
    # pa je epoha. Rabi ju pogoj "meja ne prehiti feeda".
    polnoc = int(datetime.combine(date.fromisoformat(service_date),
                                  datetime.min.time(), tzinfo=TZ).timestamp())
    rows = conn.execute(_LIVE_SQL, {"day": service_date, "now_s": now_s,
                                    "grace": _LIVE_GRACE_S,
                                    "network": network,
                                    "polnoc": polnoc,
                                    "overnight_only": int(overnight_only),
                                    "max_delay": MAX_LIVE_DELAY_S}).fetchall()
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
    network: str = NETWORK_Q,
):
    """Vožnje od postaje do postaje na dani dan, z zadnjo znano zamudo.

    Relacija se izračuna iz zaporedja postaj, ne iz številke vlaka: `train_no`
    označuje eno konkretno vožnjo, `route_id` pa je v tem feedu ena-na-ena
    s tripom in za grupiranje neuporaben.
    """
    now = datetime.now(TZ)
    date = _check_date(date) or now.date().isoformat()
    is_today = date == now.date().isoformat()
    now_s = journey.now_seconds(now) if is_today else None
    with _conn() as conn:
        a = journey.resolve_station(conn, from_, network)
        b = journey.resolve_station(conn, to, network)
        if not a or not b:
            missing = from_ if not a else to
            raise HTTPException(404, f"postaje {missing!r} ne poznam")
        # Ista postaja na obeh straneh ni prazno vprašanje, ampak napačno.
        # Brez te straže je "Ljubljana -> Ljubljana" vrnilo osem zvez z enim
        # prestopom: z IC 503 do Borovnice in z avtobusom nazaj, 2 h 09 min,
        # da prideš tja, kjer si bil. Iskalnik to zadene sam, kadar kdo obe
        # polji dopolni z istim imenom.
        if a == b:
            raise HTTPException(400, "izhodišče in cilj sta ista postaja")
        rows = stats.connections(conn, a, b, date, now_s, network=network)
        # Prestop ponudimo vedno, ne sele ko neposredne ni: cez dan je
        # neposrednih voznj lahko pet, med njimi pa stiri ure luknje.
        #
        # **Izjema so goste linije.** Ta razlog velja za vlake in medkrajevne
        # avtobuse, ne pa za mestne: pri sestminutnem taktu prestop nima kaj
        # prihraniti, poizvedba pa je izmerjeno 26,5 s. Glej `dovolj_gosto()`.
        gosto = journey.dovolj_gosto(rows)
        legs = (journey.transfers(conn, a, b, date, earliest_s=(now_s or 0),
                                  direct=rows, network=network)
                if with_transfers and not gosto else [])
        # Sele ko neposredna voznja in en prestop ne dasta nic. V vzorcu 80
        # parov zeleznickih postaj je bilo takih 36 % -- pot je obstajala, le
        # dva ali tri prestope je rabila.
        if with_transfers and not rows and not legs:
            legs = journey.plan(conn, a, b, date, earliest_s=(now_s or 0),
                                network=network)
        # Obvestila pobere streznik, ne brskalnik: prikaz jih je sicer iskal
        # z eno zahtevo na vlak, torej z dvanajstimi za eno iskanje.
        nos = [c["train_no"] for c in rows] + [t["train1"] for t in legs]
        notices = (alerts.for_trains(conn, nos, mentions=[a, b])
                   if network == "zeleznica" else [])
        meje = _znano_do(conn, network)
    return {"from": a, "to": b, "date": date, "network": network, **meje,
            "connections": rows, "transfers": legs, "alerts": notices}


def _live(network: str | None = None) -> list[dict]:
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
        rows = _live_rows(conn, today, now_s, network)
        # Vcerajsnji prometni dan ima smisel samo, dokler bi po njem se kaj
        # lahko vozilo. Zeleznica ima najpoznejsi voznoredni cas ob 26,4 h,
        # torej je po 08:35 odgovor zagotovo prazen -- prej pa smo ga vseeno
        # racunali in pri letu zajema placali 324 ms za nic.
        last_s = stats.last_sched_s(conn, network)
        if last_s is not None and now_s + 86400 <= last_s + MAX_LIVE_DELAY_S + _LIVE_GRACE_S:
            rows += _live_rows(conn, yesterday, now_s + 86400, network,
                               overnight_only=True)
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

    with _conn() as conn:
        _add_gps_position(conn, rows)
    rows.sort(key=lambda r: (r["delay_s"] is None, -(r["delay_s"] or 0)))
    # Ziva vozjna je po definiciji ze prevozila `last_stop`, zato je njena
    # zamuda meritev -- `_live_rows` bere natanko do meje.
    for r in rows:
        r["zamuda"] = stats.opis_zamude(r["delay_s"], "izmerjeno")
    return rows


# Hitrost, pod katero vozilo stejemo za stojece. Merjeno iz `speed`, NE iz
# `current_status`: to polje je v tem feedu nezanesljivo -- med vozili s
# STOPPED_AT so bila taka pri 23, 28 in 32 km/h, med IN_TRANSIT_TO pa taka
# pri 0. Hitrost je meritev, status je trditev; verjamemo meritvi.
STOPPED_KMH = 3


def _add_gps_position(conn, rows: list[dict]) -> None:
    """Avtobusu pripiše, kje JE, namesto kje je bil nazadnje izmerjen.

    Za vlak je lega sklepana iz voznega reda in zamude -- drugega vira ni.
    Avtobus pa poroča `current_stop_sequence` in status, torej natanko, na
    katerem postajališču stoji ali h kateremu se pelje. Sklepati tam, kjer
    imamo meritev, bi bilo slabše iz navade.
    """
    ids = [r["trip_id"] for r in rows if r.get("network") == "avtobus"]
    if not ids:
        return
    marks = ",".join("?" * len(ids))
    found = {
        r["trip_id"]: r
        for r in conn.execute(
            f"SELECT v.trip_id, v.stop_seq, v.speed_ms, st.name "
            f"FROM vehicle_now v "
            f"JOIN sched s ON s.trip_id = v.trip_id AND s.stop_seq = v.stop_seq "
            f"JOIN station st ON st.stop_id = s.stop_id "
            f"WHERE v.trip_id IN ({marks})",
            ids,
        )
    }
    for r in rows:
        gps = found.get(r["trip_id"])
        if not gps:
            continue
        kmh = round(gps["speed_ms"] * 3.6) if gps["speed_ms"] is not None else None
        r["speed_kmh"] = kmh
        r["gps_stopped"] = kmh is not None and kmh < STOPPED_KMH
        # `current_stop_sequence` pove, pri katerem postajaliscu vozilo je ali
        # h kateremu se pelje. Katero od tega, bi moral povedati `current_status`,
        # a ta ni zanesljiv -- zato "pri", ne "stoji na" ali "proti".
        r["last_stop"] = gps["name"]
        r["position_source"] = "GPS"


@app.get("/api/pot")
def api_pot(
    od_lat: float = Query(..., ge=45.2, le=47.0, description="izhodišče: širina"),
    od_lon: float = Query(..., ge=13.2, le=16.8, description="izhodišče: dolžina"),
    do_lat: float = Query(..., ge=45.2, le=47.0, description="cilj: širina"),
    do_lon: float = Query(..., ge=13.2, le=16.8, description="cilj: dolžina"),
    date: str | None = None,
    ob: str | None = Query(None, description="HH:MM; privzeto zdaj"),
    hoje: int = Query(pot.MAX_HOJE_S // 60, ge=3, le=45,
                      description="koliko minut hoje na vsakem koncu"),
):
    """Pot od vrat do vrat: hoja → vožnja → (prestop) → vožnja → hoja.

    Meje koordinat so Slovenija in nekaj čeznjo. To ni pedantnost: brez njih bi
    zahteva s točko sredi Atlantika pognala matriko hoje in iskanje čez cel
    vozni red, da bi vrnila prazno.

    **Lega potnika se ne zapisuje.** Storitev teče z `--no-access-log`
    (`deploy/kajros.service`), zato koordinate ne gredo v dnevnik. Kdor to
    spremeni, naj ve, da s tem začne beležiti, kje kdo stoji in kam gre.
    """
    now = datetime.now(TZ)
    dan = _check_date(date) or now.date().isoformat()
    if ob:
        try:
            h, m = (int(x) for x in ob.split(":")[:2])
        except ValueError:
            raise HTTPException(400, "ob mora biti HH:MM")
        odhod_s = h * 3600 + m * 60
    else:
        odhod_s = journey.now_seconds(now)

    # `now_s` samo za današnji dan: le takrat obstaja meja med prevoženim in
    # tem, kar je še pred vozilom. Za izrecno vprašan drug datum ostane pomen
    # "prometni dan D" in zamud ni.
    zdaj_s = journey.now_seconds(now) if dan == now.date().isoformat() else None
    with _conn() as conn:
        izid = pot.isci(conn, (od_lat, od_lon), (do_lat, do_lon), dan, odhod_s,
                        max_hoje_s=hoje * 60, now_s=zdaj_s)
        # Nočni avtobus ob 01:00 nosi VČERAJŠNJI prometni dan in ima `dep_s`
        # čez 86 400 (največji v voznem redu je 121 680, torej 33:48). Brez
        # tega vprašanje ob pol enih zjutraj ne najde ničesar, čeprav vozi.
        if not ob and now.hour < 4:
            vceraj = pot.isci(conn, (od_lat, od_lon), (do_lat, do_lon),
                              journey.yesterday(now), odhod_s + 86400,
                              max_hoje_s=hoje * 60,
                              now_s=(zdaj_s + 86400) if zdaj_s is not None else None)
            izid["predlogi"] = sorted(izid["predlogi"] + vceraj["predlogi"],
                                      key=lambda p: (p["prihod"], p["hoje_s"]))
    return izid


@app.get("/api/pot/podrobno")
def api_pot_podrobno(
    noge: str = Query(..., description="trip:od_seq:do_seq;trip:od_seq:do_seq"),
    od_lat: float = Query(..., ge=45.2, le=47.0),
    od_lon: float = Query(..., ge=13.2, le=16.8),
    do_lat: float = Query(..., ge=45.2, le=47.0),
    do_lon: float = Query(..., ge=13.2, le=16.8),
    date: str | None = None,
):
    """Ena pot, razložena: kod hodiš in kje izstopiš.

    Pot je v naslovu in ne v seji, ker mora biti **deljiva** -- kdor jo komu
    pošlje, mu pošlje pot, ne svojega brskalnika.
    """
    now = datetime.now(TZ)
    dan = _check_date(date) or now.date().isoformat()
    try:
        spec = pot.razberi_noge(noge)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not spec:
        raise HTTPException(400, "pot brez nog")
    if len(spec) > pot.MAX_NOG:
        raise HTTPException(400, f"največ {pot.MAX_NOG} voženj")
    zdaj_s = journey.now_seconds(now) if dan == now.date().isoformat() else None
    with _conn() as conn:
        try:
            return pot.podrobnosti(conn, spec, (od_lat, od_lon), (do_lat, do_lon),
                                   dan, zdaj_s)
        except KeyError as e:
            # Vozni red se je med iskanjem in klikom lahko zamenjal (uvoz je
            # dnevni). Deljena povezava od včeraj torej ni napaka odjemalca.
            raise HTTPException(404, str(e).strip("'"))


@app.get("/app/pot/podrobno", response_class=HTMLResponse)
def pot_podrobno_page(request: Request):
    """Ena pot na svoji strani: zemljevid s pešpotjo in postanki vožnje."""
    return templates.TemplateResponse(request, "pot_podrobno.html", {"here": "pot"})


@app.get("/api/live")
def api_live(network: str | None = Query(None, pattern="^(zeleznica|avtobus)$",
                                         description="samo to omrežje")):
    """Vozila, ki so zdaj na poti, z zadnjo izmerjeno zamudo."""
    # Najdrazji odgovor, ki ga zemljevid vprasa vsakih 30 s. Med dvema
    # branjema zamud se ne spremeni, zato ga racunamo enkrat za vse.
    return _predpomni(f"live:{network}", _znacka("rt_fetched"), 60,
                      lambda: _live(network))


# --- HEAD -------------------------------------------------------------------
# **Vse poti so `@app.get`, kar pomeni samo GET.** Starlettov `Route` ob GET
# sam doda HEAD, FastAPIjev `APIRoute` pa ne -- izmerjeno: `r.methods` je
# `{'GET'}` na vseh 34 poteh, in `HEAD https://kajros.app/` je vracal 405.
#
# Dokler je bila stran vidna samo domacemu omrezju, to ni motilo nikogar.
# Javno pa je HEAD prva stvar, ki jo posljejo nadzorniki dosegljivosti
# (UptimeRobot ga uporablja privzeto) in preverjalniki povezav -- vsi bi
# porocali, da stran ne dela.
#
# Zanka mora teci PO vseh dekoratorjih, torej na koncu modula.
for _r in app.routes:
    if isinstance(_r, APIRoute) and _r.methods == {"GET"}:
        _r.methods = {"GET", "HEAD"}

# HEAD ne sme v dokumentacijo. Endpointi so javni in jih kdo bere; 34 vnosov,
# ki povedo "isto kot GET, brez telesa", je samo dvakrat daljsi seznam.
_openapi_z_head = app.openapi


def _openapi_brez_head():
    shema = _openapi_z_head()
    for operacije in shema.get("paths", {}).values():
        operacije.pop("head", None)
    return shema


app.openapi = _openapi_brez_head
