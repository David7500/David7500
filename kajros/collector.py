"""Zajem zamud iz GTFS-RT.

Feed nosi samo `delay` (brez absolutnega časa) in je drseče okno -- v enem klicu
dobiš le postanke okoli trenutnega položaja vlaka. Celotno vožnjo zato sestavimo
iz zaporednih pollov; zato pišemo ob vsaki spremembi in vzdržujemo tabelo `run`
z zadnjim znanim stanjem.
"""
from __future__ import annotations

import json
import sqlite3
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from google.transit import gtfs_realtime_pb2

from . import config, db, iz_lege, stats

TZ = ZoneInfo(config.TIMEZONE)


def fetch(url: str, conn: sqlite3.Connection, etag_key: str):
    """Pogojni GET. Vrne None, kadar se feed ni spremenil."""
    headers = {"User-Agent": config.USER_AGENT}
    etag = db.get_meta(conn, etag_key)
    if etag:
        headers["If-None-Match"] = etag
    resp = requests.get(url, headers=headers, timeout=60)
    if resp.status_code == 304:
        return None
    resp.raise_for_status()
    if resp.headers.get("ETag"):
        db.set_meta(conn, etag_key, resp.headers["ETag"])
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)
    return feed


# Vozni red se med dvema uvozoma GTFS ne spremeni, zajem pa tece vsakih 30 s.
# Oboje spodaj je bilo prej zgrajeno ob VSAKEM pollu. Izmerjeno na bazi vseh
# prevoznikov: okna 75 ms in 4 MB, koledar **5,3 s in 557 MB** -- vsakih
# trideset sekund, za podatek, ki je enak kot prej. Pri sami zeleznici (789
# voznj) se to ni videlo; z avtobusi je proces jedel 290-518 MB in bi malino
# s 427 MB ubil.
_STATIC_CACHE: dict[tuple, object] = {}


def _cached(conn: sqlite3.Connection, name: str, extra, build):
    key = db.cache_key(conn)
    if key is None:                 # sveza ali testna baza -- ne predpomni
        return build()
    baza, key = key, (key, name, extra)
    if key not in _STATIC_CACHE:
        # Nov uvoz razveljavi vse, tudi včerajšnji koledar -- a SAMO nov uvoz.
        # Prej je bil tu `clear()` ob vsakem novem ključu, in ključi so trije
        # (okna, koledar, zamenjave): vsak je izbrisal druga dva, zato se je
        # vse gradilo znova ob vsakem klicu. Izmerjeno 25. 9. 2026 na kopiji
        # arwena: v 240 s 62 gradenj oken (11,4 s CPU), 20 koledarja (7,6 s) in
        # 58 zamenjav (2,1 s) -- 9 % jedra za predpomnilnik, ki ni predpomnil.
        # Stara vrednost ISTE vrste (včerajšnji koledar, prejšnje število
        # zamenjav) gre ven, da se ne kopiči.
        for k in [k for k in _STATIC_CACHE if k[0] != baza or k[1] == name]:
            del _STATIC_CACHE[k]
        _STATIC_CACHE[key] = build()
    return _STATIC_CACHE[key]


def _rail_trip_windows(conn: sqlite3.Connection) -> dict[str, tuple[int, int]]:
    """trip_id -> (prvi odhod, zadnji prihod) v sekundah od polnoči."""
    def build():
        # Iz `trip`, ne z grupiranjem 403 000 vrstic `sched`: okvir vozjne je
        # od uvoza naprej stolpec (`db.fill_trip_window`).
        return {r["trip_id"]: (r["start_s"], r["end_s"]) for r in conn.execute(
            "SELECT trip_id, start_s, end_s FROM trip WHERE start_s IS NOT NULL")}
    return _cached(conn, "windows", None, build)


def _service_dates(conn: sqlite3.Connection, now: datetime) -> dict[str, set[str]]:
    """trip_id -> obratovalni dnevi, ki pridejo v postev **zdaj**.

    `resolve_service_date` gleda samo vceraj, danes in jutri, zato ni razloga
    nositi celega koledarja: ta ima 4 650 807 parov (trip, datum) in v Pythonu
    zasede 557 MB. Trije dnevi jih imajo 60 000.
    """
    days = tuple((now.date() + timedelta(days=o)).isoformat() for o in (-1, 0, 1))

    def build():
        out: dict[str, set[str]] = {}
        for r in conn.execute(
            "SELECT t.trip_id, sd.date FROM trip t JOIN service_day sd USING (service_id) "
            "WHERE sd.date IN (?, ?, ?)", days
        ):
            out.setdefault(r["trip_id"], set()).add(r["date"])
        return out

    return _cached(conn, "dates", days, build)


def _zamenjave(conn: sqlite3.Connection) -> dict[str, tuple[str, dict]]:
    """Stari id -> (novi id, {stari_seq: (novi_seq, stari_arr_s, stari_dep_s)}).

    Vožnje, ki jim je nov vozni red dal drug id, feed pa jih nosi pod starim
    (`gtfs.povezi_zamenjave`). Brez tega jih zajem zavrže kot neznane.
    """
    def build():
        out: dict[str, tuple[str, dict]] = {}
        for r in conn.execute(
            "SELECT stari_trip, stari_seq, novi_trip, novi_seq, stari_arr_s, stari_dep_s "
            "FROM zamenjava"
        ):
            out.setdefault(r[0], (r[2], {}))[1][r[1]] = (r[3], r[4], r[5])
        return out
    # Ključ je tudi število vrstic: `kajros zamenjave` jih doda mimo uvoza,
    # torej brez novega `gtfs_imported_at`, in brez tega bi tekoči zajem do
    # naslednjega uvoza bral stare.
    n = conn.execute("SELECT COUNT(*) FROM zamenjava").fetchone()[0]
    return _cached(conn, "zamenjave", n, build)


def _cas_zamude(sched_row, kaj: str) -> int | None:
    """Voznoredni čas, na katerega se nanaša zamuda za `arrival`/`departure`."""
    t_s = sched_row[0] if kaj == "arrival" else sched_row[1]
    if t_s is None:
        t_s = sched_row[1] if kaj == "arrival" else sched_row[0]
    return t_s


def zamuda_po_zamenjavi(stu, kaj: str, stari_row, novi_row,
                        service_date: str) -> int | None:
    """Zamuda iz feeda, preračunana s starega voznega reda na novega.

    Feedova zamuda je razlika do voznega reda, ki ga pozna feed -- starega.
    Uro, ki jo pomeni, obdržimo in odštejemo novega: sicer bi vožnjo, ki je po
    novem voznem redu tri minute prej, kazali tri minute prepozno.
    """
    d = _delay_of(stu, kaj, stari_row, service_date)
    if d is None or novi_row is None:
        return None
    a, b = _cas_zamude(stari_row, kaj), _cas_zamude(novi_row, kaj)
    if a is None or b is None:
        return None
    return d + a - b


def resolve_service_date(trip_id, window, valid_dates, now: datetime) -> str | None:
    """Ugotovi, kateremu obratovalnemu dnevu pripada ta vožnja.

    SŽ zapisi nimajo `start_date`, vožnje pa gredo lahko čez polnoč, zato datum
    izberemo tako, da se voznoredno okno vožnje ujema s trenutnim časom.
    """
    if not window or not valid_dates:
        return None
    start_s, end_s = window
    best, best_gap = None, None
    for offset in (-1, 0, 1):
        d = (now.date() + timedelta(days=offset)).isoformat()
        if d not in valid_dates:
            continue
        midnight = datetime.combine(date.fromisoformat(d), datetime.min.time(), tzinfo=TZ)
        start = midnight + timedelta(seconds=start_s)
        end = midnight + timedelta(seconds=end_s)
        if not (start - timedelta(minutes=45) <= now <= end + timedelta(hours=3)):
            continue
        gap = 0 if start <= now <= end else min(abs((now - start).total_seconds()),
                                                abs((now - end).total_seconds()))
        if best_gap is None or gap < best_gap:
            best, best_gap = d, gap
    return best


# Najmanjsa sprememba, ki si zasluzi novo vrstico v dnevniku `obs`.
#
# Prikaz ima locljivost ene minute in sekund ne kaze nikoli; feed sam prilaga
# `uncertainty: 120`. Sprememba za 15 sekund torej ni sprememba, ampak sum.
#
# Pri vlakih to nic ne spremeni -- ti porocajo v celih minutah in imajo 1,6
# zapisa na postanek. Pri mestnih avtobusih pa 23,3, z mediano spremembe
# 15 sekund: to je 14 000 vrstic na uro za nihanje, ki ga ne pokazemo.
#
# `run` ostane TOCEN -- prag velja samo za dnevnik. Trenutno stanje je vedno
# tisto, kar je feed nazadnje rekel.
OBS_MIN_DELTA_S = 60


# Zamuda, pod katero skok na niclo ni sumljiv. Vlak, ki je bil dve minuti v
# zamudi in je zdaj tocen, je vsakdanji dogodek; vlak, ki je bil dvajset minut
# v zamudi in je cez pol minute tocen, ni.
SUSPECT_DROP_S = 300


def worth_logging(last, arr, dep) -> bool:
    """Ali je ta vrednost dovolj drugacna od zadnje zapisane v dnevniku?

    Prva vrednost za postanek gre vedno noter. Kasnejse samo, ce se od zadnje
    ZAPISANE razlikujejo vsaj za `OBS_MIN_DELTA_S` -- primerjamo z zapisano,
    ne s prejsnjo prebrano, da se pocasno lezenje sesteva in ne izgine.
    """
    if last is None:
        return True
    for new, old in ((arr, last["delay_arr"]), (dep, last["delay_dep"])):
        if new is None and old is None:
            continue
        if new is None or old is None:
            return True
        if abs(new - old) >= OBS_MIN_DELTA_S:
            return True
    return False


# Postanek, ki je bil prevozen, ne more spet postati prihodnji. Rezerva je
# 120 s, kolikor feed sam prilaga kot `uncertainty`.
PASSED_MARGIN_S = 120


def _sched_abs(service_date: str, sched_row) -> float | None:
    """Absolutni cas voznorednega odhoda (ali prihoda, ce odhoda ni)."""
    if sched_row is None:
        return None
    t_s = sched_row[1] if sched_row[1] is not None else sched_row[0]
    if t_s is None:
        return None
    return stats.polnoc(service_date) + t_s


def undoes_passing(prev, sched_row, service_date, arr, dep, ts) -> bool:
    """Ali nova vrednost trdi, da vozilo postanka se ni doseglo, ceprav smo
    ze zapisali, da ga je?

    Feed obcasno izgubi vozilo in za postanke, ki jih je to ze prevozilo,
    zacne objavljati `zdaj - vozni red`: vrednost, ki raste natanko za minuto
    na minuto. Ujeto v zivo 30. 8. na LPP 25 (voznja 452632, Poliklinika):
    ob 12:19:36 je feed porocal prihod +58 s in odhod +126 s, torej pravo
    meritev z razlicnima vrednostma; ob 12:23:48 je skocil na +482 in nato
    sedem klicev zapored rasel natanko za 60 s na 60 s do +842 (+14 min),
    ob 12:30:29 pa se vrnil na +58/+126. Vlak je bil ves ta cas ze davno
    mimo -- rasla je ura, ne zamuda.

    V zajetih podatkih je takih zaporedij 11 827 pri 947 voznjah, od tega
    2 731 takih, kjer se feed ni popravil in je tekoca vrednost obticala v
    `run` (mediana 9 min, p90 71 min, najvec 11 h). To pojasni tudi doslej
    nepojasnjeno "enotno zamudo cez vso voznjo": Nomagov N6571 s 27 060 s na
    vseh postankih je natanko ta vzorec, ujet po tem, ko se je ustavil.

    Pravilo je zato ozko in brez prostih parametrov: zavrnemo samo vrednost,
    ki bi postanek, za katerega smo ze zapisali, da je bil prevozen pred vec
    kot `PASSED_MARGIN_S`, prestavila nazaj v prihodnost. Popravek navzgor,
    ki postanek pusti v preteklosti, je meritev in gre skozi. Ce je
    obratovalni dan razresen narobe, je varovalka neucinkovita, nikoli pa ne
    napacna -- oba casa se premakneta skupaj.

    Dnevnik `obs` obdrzi vse, kar je feed rekel; caka samo `run`.
    """
    if prev is None:
        return False
    old = prev["delay_dep"] if prev["delay_dep"] is not None else prev["delay_arr"]
    new = dep if dep is not None else arr
    if old is None or new is None or new <= old:
        return False
    # Zapisana vrednost je dokaz o prevozu samo, ce je bila MERITEV. Feed za
    # se nedosezen postanek pogosto objavi niclo -- in prav ta nicla je bila
    # prva past: EN 1276 je 28. 8. ob 00:03 imel v Celju zapisano 0 (napoved
    # pred prihodom), ob 01:57 pa pravih +114 min. Brez tega pogoja bi
    # varovalka resnicno dvourno zamudo nocnega vlaka zavrgla.
    #
    # Za meritev steje samo zapis, kjer je feed dal RAZLICNI vrednosti za
    # prihod in odhod: tega za nedosezen postanek ne naredi. Vlaki tako ali
    # tako niso prizadeti -- 11 794 od 11 827 zaporedij je avtobusnih.
    if prev["delay_arr"] is None or prev["delay_dep"] is None:
        return False
    if prev["delay_arr"] == prev["delay_dep"]:
        return False
    t0 = _sched_abs(service_date, sched_row)
    if t0 is None:
        return False
    return (t0 + old) < ts - PASSED_MARGIN_S and (t0 + new) > ts


def is_forecast(prev, sched_row, service_date) -> bool:
    """Ali je bila zapisana vrednost NAPOVED -- objavljena, preden bi vozilo
    lahko bilo tam?

    Feed za voznjo, ki se ni odpeljala, objavi zamudo vozila s prejsnje
    voznje. LPP 25 (452632) 30. 8.: postanek Medvode novo naselje ima vozni
    red 11:41, feed pa je zanj ze od 11:11 objavljal +8, +10, +11, +12, +13
    in ob 11:33:55 +14 min -- vsakic cas, ki je bil takrat se v prihodnosti.
    Ob 11:35:44 je vrednost popravil na 0 in avtobus je odpeljal skoraj
    tocno.

    Merilo je zato brez prostih parametrov: vrednost, ki ob svojem nastanku
    postanek postavlja v prihodnost, ni meritev.
    """
    if prev is None or prev["feed_ts"] is None:
        return False
    d = prev["delay_dep"] if prev["delay_dep"] is not None else prev["delay_arr"]
    if d is None:
        return False
    t0 = _sched_abs(service_date, sched_row)
    return t0 is not None and (t0 + d) > prev["feed_ts"]


def is_zero_blip(prev, last, arr, dep, sched_row=None, service_date=None) -> bool:
    """Ali je to prehodna nicla, ki jo feed vrine med dve pravi vrednosti?

    V zajetih podatkih se pri 14 % postankov z vec kot dvema zapisoma pojavi
    vzorec X, 0, X -- ista nenicelna vrednost, med njima ena sama nicla, vse
    v razmiku ene minute. Osemnajst vrstic v `run` je zaradi tega trdilo, da
    je bil vlak tocen, ceprav je zamujal pet minut ali vec.

    Fizikalno je to nemogoce: pri ze prevozenem postanku je zamuda razlika med
    dejanskim in voznorednim casom in se med dvema klicema ne more zmanjsati
    za vec, kot je vmes minilo casa.

    Pravilo je zato ozko: niclo sprejmemo sele, ko jo potrdi drugi zaporedni
    poll. Dnevnik `obs` obdrzi vse, kar je feed rekel -- zavrzemo nicesar,
    samo `run` pocaka en korak.
    """
    if arr not in (0, None) or dep not in (0, None):
        return False
    if arr is None and dep is None:
        return False
    before = None
    if prev is not None:
        before = prev["delay_arr"] if prev["delay_arr"] is not None else prev["delay_dep"]
    if before is None or before < SUSPECT_DROP_S:
        return False
    # Nicla, ki popravlja NAPOVED, ni blip, ampak popravek -- in prav ta je
    # najbolj dragocen. Brez tega je `run` obtical na napovedi izpred odhoda
    # za vedno: feed jo je popravil enkrat samkrat, drseče okno pa je slo
    # naprej in potrditve ni bilo nikoli. V grafu LPP 25 je bilo to videti
    # kot devet postaj pri +14 in nato padec za petnajst minut v enem koraku
    # -- tam se je koncala napoved in zacela meritev.
    if service_date is not None and is_forecast(prev, sched_row, service_date):
        return False
    # Ce je ze prejsnji zapis v dnevniku govoril niclo, je to potrditev in ne blip.
    if last is not None:
        prior = last["delay_arr"] if last["delay_arr"] is not None else last["delay_dep"]
        if prior == 0:
            return False
    return True


def _delay_of(stu, kaj: str, sched_row, service_date: str) -> int | None:
    """Zamuda iz enega `stop_time_update`, ali None, kadar je feed ne pove.

    **Ne beri `stu.arrival.delay` naravnost.** Protobuf za neizpolnjeno polje
    vrne 0, kar je videti kot "tocno". Izmerjeno na zivem feedu: `arrival`
    ima `delay` pri vlakih v 100 % primerov, pri avtobusih pa le v 31-61 % --
    ostalo so bile zapisane nicle. V bazi je to 11 906 od 20 523 avtobusnih
    vrstic (58 %) in delez tocnih je zaradi tega bral 84,3 % namesto 71,2 %.

    Kadar zamude ni, a je absolutni cas, jo izracunamo iz njega -- to je
    meritev, ne ugibanje. Vlaki absolutnega casa nimajo nikoli, avtobusi
    skoraj vedno (87-100 %).
    """
    if not stu.HasField(kaj):
        return None
    m = getattr(stu, kaj)
    if m.HasField("delay"):
        return m.delay
    if not m.HasField("time") or sched_row is None:
        return None
    t_s = _cas_zamude(sched_row, kaj)
    if t_s is None:
        return None
    return int(m.time - (stats.polnoc(service_date) + t_s))


def _sched_times(conn: sqlite3.Connection, trip_ids: set[str]) -> dict:
    """(trip_id, stop_seq) -> (arr_s, dep_s) za vozjne iz tega klica.

    Samo zanje: cel vozni red je 403 000 vrstic, en poll pa jih zadeva 1 700.
    """
    if not trip_ids:
        return {}
    ids = list(trip_ids)
    out = {}
    for i in range(0, len(ids), 400):      # sqlite ima mejo vezanih vrednosti
        kos = ids[i:i + 400]
        for r in conn.execute(
            f"SELECT trip_id, stop_seq, arr_s, dep_s FROM sched "
            f"WHERE trip_id IN ({','.join('?' * len(kos))})", kos
        ):
            out[(r["trip_id"], r["stop_seq"])] = (r["arr_s"], r["dep_s"])
    return out


def ingest(conn: sqlite3.Connection, feed, vir: str = "ijpp") -> dict:
    """Zapiše spremembe zamud. Vrne števce za log."""
    now = datetime.now(TZ)
    windows = _rail_trip_windows(conn)
    valid = _service_dates(conn, now)
    zamenjave = _zamenjave(conn)

    def nas_id(tid):
        """Pod katerim id-jem vožnjo vodimo: pod njenim ali pod naslednico."""
        if tid in windows:
            return tid, None
        z = zamenjave.get(tid)
        return z if z and z[0] in windows else (None, None)

    # Vozni red postankov rabimo, kadar feed da absolutni cas namesto zamude.
    sched = _sched_times(conn, {nas_id(e.trip_update.trip.trip_id)[0]
                                for e in feed.entity} - {None})
    feed_ts = feed.header.timestamp or int(time.time())
    observed_at = int(time.time())

    changed = 0
    trips_seen = 0
    skipped = 0
    blips = 0
    smoothed = 0
    # GTFS-RT zna povedati, da je voznja odpovedana (`schedule_relationship`),
    # a SZ tega polja ne uporablja -- odpovedi sporocajo z besedilom obvestila
    # (`effect = 6`, "vlak vozi samo do ..."). Vseeno stejemo: ce se to kdaj
    # spremeni, hocemo izvedeti takoj in ne cez pol leta.
    non_scheduled = 0
    unpassed = 0
    # Vožnje, ki jih feed nosi, vozni red pa ne pozna. Zavržemo jih, a jih
    # štejemo: tako je bil 22. 9. 2026 zavržen ves zajem treh linij LPP in tega
    # ni videl nihče, dokler potnik ni čakal na avtobus.
    neznanih = 0
    zamenjanih = 0
    v_feedu: set[str] = set()
    # Po progah, ker LPP včasih ne izgubi vožnje, ampak linijo: 2. 10. 2026
    # je bilo 38 od 44 voženj linije 1 neznanih, liniji 11 in 27 pa 3 in 4.
    proge: dict[str, list[int]] = {}

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue            # LPP v isti feed da tudi lege in obvestila
        tu = entity.trip_update
        trip_id, zamenjava = nas_id(tu.trip.trip_id)
        if vir == "lpp":
            stevec = proge.setdefault(tu.trip.route_id, [0, 0])
            stevec[0] += trip_id is None
            stevec[1] += 1
        if trip_id is None:
            neznanih += 1
            continue
        zamenjanih += zamenjava is not None
        trips_seen += 1
        v_feedu.add(trip_id)

        service_date = tu.trip.start_date or None
        if service_date and len(service_date) == 8:
            service_date = f"{service_date[:4]}-{service_date[4:6]}-{service_date[6:]}"
        else:
            service_date = resolve_service_date(trip_id, windows.get(trip_id), valid.get(trip_id), now)
        if not service_date:
            skipped += 1
            continue

        if tu.trip.schedule_relationship != 0:
            non_scheduled += 1

        ts = tu.timestamp or feed_ts
        for stu in tu.stop_time_update:
            if stu.schedule_relationship != 0:
                non_scheduled += 1
            seq = stu.stop_sequence
            if zamenjava is None:
                arr = _delay_of(stu, "arrival", sched.get((trip_id, seq)), service_date)
                dep = _delay_of(stu, "departure", sched.get((trip_id, seq)), service_date)
            else:
                p = zamenjava.get(seq)
                if p is None:
                    continue    # tega postanka nov vozni red nima
                seq, stari = p[0], (p[1], p[2])
                novi = sched.get((trip_id, seq))
                arr = zamuda_po_zamenjavi(stu, "arrival", stari, novi, service_date)
                dep = zamuda_po_zamenjavi(stu, "departure", stari, novi, service_date)
            if arr is None and dep is None:
                continue        # feed o tem postanku ni povedal nicesar

            prev = conn.execute(
                "SELECT delay_arr, delay_dep, feed_ts FROM run "
                "WHERE trip_id=? AND service_date=? AND stop_seq=?",
                (trip_id, service_date, seq),
            ).fetchone()
            if prev and prev["delay_arr"] == arr and prev["delay_dep"] == dep:
                continue    # nespremenjeno -- ne pisi

            # Zadnji zapis v dnevniku rabimo, preden vanj pisemo: na njem
            # sloni preverjanje sumljivega skoka na niclo (glej spodaj) in
            # presoja, ali je sprememba dovolj velika za novo vrstico.
            last = conn.execute(
                "SELECT delay_arr, delay_dep FROM obs "
                "WHERE trip_id=? AND service_date=? AND stop_seq=? "
                "ORDER BY feed_ts DESC LIMIT 1",
                (trip_id, service_date, seq),
            ).fetchone()

            if worth_logging(last, arr, dep):
                conn.execute(
                    "INSERT OR IGNORE INTO obs"
                    "(trip_id,service_date,stop_seq,delay_arr,delay_dep,feed_ts,observed_at) "
                    "VALUES(?,?,?,?,?,?,?)",
                    (trip_id, service_date, seq, arr, dep, ts, observed_at),
                )
                changed += 1
            else:
                smoothed += 1

            if is_zero_blip(prev, last, arr, dep,
                            sched.get((trip_id, seq)), service_date):
                # Dnevnik obdrzi vse, `run` pa ne prevzame vrednosti, dokler je
                # ne potrdi naslednji poll. Zamuda se v pol minute ne more
                # zmanjsati za dvajset minut.
                blips += 1
                continue

            if undoes_passing(prev, sched.get((trip_id, seq)), service_date,
                              arr, dep, ts):
                # Feed je izgubil vozilo in za ze prevozen postanek objavlja
                # `zdaj - vozni red`. To je ura, ne zamuda.
                unpassed += 1
                continue

            conn.execute(
                "INSERT INTO run(trip_id,service_date,stop_seq,delay_arr,delay_dep,feed_ts) "
                "VALUES(?,?,?,?,?,?) "
                "ON CONFLICT(trip_id,service_date,stop_seq) DO UPDATE SET "
                "delay_arr=excluded.delay_arr, delay_dep=excluded.delay_dep, "
                "feed_ts=excluded.feed_ts WHERE excluded.feed_ts >= run.feed_ts",
                (trip_id, service_date, seq, arr, dep, ts),
            )

    conn.commit()
    iz_lege.zabelezi_feed(v_feedu, vir=vir)
    return {"trips": trips_seen, "changed": changed, "skipped": skipped,
            "blips": blips, "unpassed": unpassed, "smoothed": smoothed,
            "non_scheduled": non_scheduled, "feed_ts": feed_ts,
            "neznanih": neznanih, "zamenjanih": zamenjanih, "proge": proge}


def _zapisi_neznane(conn: sqlite3.Connection, kljuc: str, izid: dict) -> None:
    """Koliko voženj iz feeda je bilo zavrženih: `neznanih/vseh` za pregled."""
    vseh = izid["trips"] + izid["neznanih"]
    db.set_meta(conn, kljuc, f"{izid['neznanih']}/{vseh}")
    conn.commit()


#: Koliko mora biti vožnja po voznem redu že na poti, preden je molk feeda
#: napaka in ne le prvo sporočilo, ki še pride. Izmerjeno 25. 9. 2026 ob 11:50:
#: pri tej meji je bilo brez zamude 0 od 295 vozil na vožnjah, ki jih feed
#: nosi, in 10 od 10 na vožnjah z veljavnostjo od 21. 9., ki jih ne.
BREZ_ZAMUDE_PO_S = 600


def lega_brez_zamude(conn: sqlite3.Connection, zdaj: datetime) -> dict[str, list[int]]:
    """Prevoznik -> [ne v feedu zamud, brez zamude, vozil z lego] na vožnjah,
    ki zdaj vozijo.

    Obratna stran `rt_neznanih`: tam feed nosi vožnjo, ki je ne poznamo, tu
    vozilo z lego vozi vožnjo, ki je feed zamud **ne nosi**. Od 21. 9. 2026 je
    bilo tako ~430 Nomagovih voženj na dan (vse z veljavnostjo od 21. 9.) --
    lege so bile, zamud ni bilo, in števec `rt_neznanih` je bil ves čas zelen.
    Na tabli smo jo opazili štiri dni pozneje.

    Števca sta dva, ker `iz_lege` vrzel zapolni: „ne v feedu“ je napaka vira,
    „brez zamude“ (nobene vrstice v `run`) pa tisto, kar vidi potnik. Brez
    prvega bi zapolnitev napako vira skrila.

    Vožnja „vozi“, kadar je po voznem redu na poti vsaj `BREZ_ZAMUDE_PO_S`;
    brez tega bi štelo vsako vozilo, ki čaka na izhodišču ali je ravnokar
    odpeljalo.
    """
    danes = zdaj.date()
    now_s = int(zdaj.timestamp()) - stats.polnoc(danes.isoformat())
    out: dict[str, list[int]] = {}
    for r in conn.execute(
        "SELECT t.agency, v.trip_id, "
        "       EXISTS (SELECT 1 FROM run r WHERE r.trip_id = v.trip_id "
        "                AND r.service_date = COALESCE(v.service_date, ?)) AS ima "
        "FROM vehicle_now v JOIN trip t USING (trip_id) "
        "WHERE v.seen_ts >= ? AND t.start_s IS NOT NULL "
        "  AND CASE COALESCE(v.service_date, ?) "
        "        WHEN ? THEN ? WHEN ? THEN ? + 86400 END "
        "      BETWEEN t.start_s + ? AND t.end_s",
        (danes.isoformat(), int(zdaj.timestamp()) - POSITION_FRESH_S,
         danes.isoformat(), danes.isoformat(), now_s,
         (danes - timedelta(days=1)).isoformat(), now_s, BREZ_ZAMUDE_PO_S),
    ):
        stevec = out.setdefault(r["agency"], [0, 0, 0])
        stevec[0] += iz_lege.brez_feeda(r["trip_id"], zdaj.timestamp())
        stevec[1] += not r["ima"]
        stevec[2] += 1
    return out


def poll_once(conn: sqlite3.Connection) -> dict:
    feed = fetch(config.TRIP_UPDATES_URL, conn, "rt_etag")
    # Znacka za predpomnilnik strezbe, po vzoru `positions_fetched`. Pise se
    # tudi ob 304 ("ob tem casu smo zamude potrdili"), ker mora predpomnilnik
    # vedeti, da je odgovor se vedno tocen, in ne le, da se je spremenil.
    db.set_meta(conn, "rt_fetched", str(int(time.time())))
    if feed is None:
        iz_lege.feed_nespremenjen("ijpp")
        conn.commit()
        return {"trips": 0, "changed": 0, "skipped": 0, "unchanged": True}
    izid = ingest(conn, feed)
    _zapisi_neznane(conn, "rt_neznanih", izid)
    db.set_meta(conn, "lega_brez_zamude",
                json.dumps(lega_brez_zamude(conn, datetime.now(TZ)), sort_keys=True))
    conn.commit()
    return izid


def _lpp_vzorci(conn: sqlite3.Connection) -> dict[str, dict]:
    """Vzorec proge (tretja komponenta id-ja) -> proga, linija in smer.

    Vožnja, ki je vozni red ne pozna, ima vzorec iz njega: 2. 10. 2026 vseh
    45 od 45. Linija in smer sta torej znani, ure pa ne.
    """
    def build():
        out: dict[str, dict] = {}
        for r in conn.execute("SELECT trip_id, route_id, train_no, headsign "
                              "FROM trip WHERE agency = 'lpp'"):
            out.setdefault(r["trip_id"].split("|")[-1], {
                "route_id": r["route_id"], "train_no": r["train_no"],
                "headsign": r["headsign"]})
        return out
    return _cached(conn, "lpp_vzorci", None, build)


def _zapisi_brez_voznje(conn: sqlite3.Connection, proge: dict[str, list[int]],
                        vozila: list[dict]) -> None:
    """Linije in vozila mestnega LPP, ki vozijo mimo voznega reda, za prikaz.

    LPP vožnje izda pod id-ji, ki jih objavljeni vozni red nima (1. 10. 2026
    17 % voženj šestih linij, 2. 10. ob kolesarskem prvenstvu linija 1).
    Zamude se jim ne da izračunati -- ni ure, od katere bi jo merili -- zato
    v `run` ne gredo. Tabla zanje vpraša LPP (`lpp.na_tablo`), zemljevid pa
    jih nariše brez zamude.
    """
    vzorci = _lpp_vzorci(conn)
    linija = {v["route_id"]: v["train_no"] for v in vzorci.values()}
    linije: dict[str, list[int]] = {}
    for route_id, (n, vseh) in proge.items():
        ime = linija.get(route_id)
        if ime is not None and n:
            stevec = linije.setdefault(ime, [0, 0])
            stevec[0] += n
            stevec[1] += vseh
    zdaj = int(time.time())
    db.set_meta(conn, "lpp_linije_brez_voznje",
                json.dumps({"ts": zdaj, "linije": linije}, sort_keys=True))
    out = []
    for v in vozila:
        p = vzorci.get(v.pop("trip_id").split("|")[-1])
        if p is not None:
            out.append({**v, "train_no": p["train_no"], "headsign": p["headsign"]})
    db.set_meta(conn, "lpp_vozila_brez_voznje",
                json.dumps({"ts": zdaj, "vozila": out}, ensure_ascii=False))
    conn.commit()


def poll_lpp(conn: sqlite3.Connection) -> dict:
    """Mestni LPP: **en feed za vse troje** -- zamude, lege in obvestila.

    Zakaj poseben klic in ne le se en URL v `poll_once()`: IJPP ima tri
    locene vire, LPP enega samega (`sources/lpp/all`), zato ga preberemo
    enkrat in razdelimo tu.

    **`delay` je v tem feedu vedno 0** in ga ne smemo brati. Izmerjeno dvakrat
    (nedelja 22:00 in ponedeljkova konica 07:11, skupaj cez 5 000 postankov):
    nobena zamuda ni bila nenicelna, `trip_update.delay` pa ni izpolnjen nikjer.
    Zamuda je v ABSOLUTNIH napovedanih casih (1 882 od 4 517 postankov), kar
    `_delay_of()` ze pokriva -- ta bere `.time` in odsteje vozni red.
    """
    if not config.LPP_ENABLED:
        return {"trips": 0, "vehicles": 0, "unchanged": True}
    feed = fetch(config.LPP_RT_URL, conn, "lpp_rt_etag")
    db.set_meta(conn, "lpp_rt_fetched", str(int(time.time())))
    if feed is None:
        iz_lege.feed_nespremenjen("lpp")
        conn.commit()
        return {"trips": 0, "vehicles": 0, "unchanged": True}
    izid = ingest(conn, feed, vir="lpp")
    _zapisi_neznane(conn, "lpp_rt_neznanih", izid)
    brez_voznje: list[dict] = []
    lege = ingest_positions(conn, feed, brez_voznje)
    _zapisi_brez_voznje(conn, izid.pop("proge"), brez_voznje)
    # Obvestila so v ISTEM feedu in jih doslej nismo brali -- 181 vrstic na
    # zajem v smeti. Zdruzena so v `alerts.ingest_lpp()`, ker jih feed poslje
    # na vozjno in ne na dogodek.
    from . import alerts as _alerts
    obv = _alerts.ingest_lpp(conn, feed)
    return {**izid, "vehicles": lege.get("vehicles", 0),
            "obvestil": obv.get("obvestil", 0)}


def run_forever(conn: sqlite3.Connection, interval: int | None = None) -> None:
    interval = interval or config.POLL_SECONDS
    while True:
        started = time.monotonic()
        try:
            info = poll_once(conn)
            stamp = datetime.now(TZ).strftime("%H:%M:%S")
            if not info.get("unchanged"):
                print(f"{stamp}  vlakov={info['trips']:3d}  sprememb={info['changed']:3d}"
                      f"  brez datuma={info['skipped']}", flush=True)
        except Exception as exc:               # feed občasno resetira povezavo
            print(f"{datetime.now(TZ):%H:%M:%S}  napaka: {exc}", flush=True)
        time.sleep(max(1.0, interval - (time.monotonic() - started)))


def rebuild_run(conn: sqlite3.Connection) -> dict:
    """Znova zgradi `run` iz dnevnika `obs` po istem pravilu kot zajem.

    Rabi se po uvedbi vsake nove varovalke: vrstice, ki so nastale prej, so
    lahko obtičale na nicli, ki jo je feed vrnil za en klic
    (`is_zero_blip`), ali na tekoči uri za postanek, ki je bil že prevožen
    (`undoes_passing`). Idempotentno -- ponovni zagon ne spremeni nič, ker
    je pravilo isto.

    Popravi se le, kar je še v dnevniku: ta se obrezuje (železnica 90 dni,
    avtobusi 14), `run` pa nikoli. Starejšega ni iz česa graditi.

    Dnevnik je merodajen in ostane nedotaknjen; popravlja se samo povzetek.
    """
    rows = conn.execute(
        "SELECT trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts "
        "FROM obs ORDER BY trip_id, service_date, stop_seq, feed_ts"
    ).fetchall()

    # Vozni red rabi `undoes_passing`, da ve, kdaj bi postanek moral biti.
    sched = {(r["trip_id"], r["stop_seq"]): (r["arr_s"], r["dep_s"])
             for r in conn.execute(
                 "SELECT trip_id, stop_seq, arr_s, dep_s FROM sched "
                 "WHERE trip_id IN (SELECT DISTINCT trip_id FROM obs)")}

    accepted: dict[tuple, tuple] = {}
    fixed = 0
    unpassed = 0
    key = None
    prev = last = None
    for r in rows:
        k = (r["trip_id"], r["service_date"], r["stop_seq"])
        if k != key:
            key, prev, last = k, None, None
        if is_zero_blip(prev, last, r["delay_arr"], r["delay_dep"],
                        sched.get((r["trip_id"], r["stop_seq"])), r["service_date"]):
            fixed += 1
        elif undoes_passing(prev, sched.get((r["trip_id"], r["stop_seq"])),
                            r["service_date"], r["delay_arr"], r["delay_dep"],
                            r["feed_ts"]):
            unpassed += 1
        else:
            accepted[k] = (r["delay_arr"], r["delay_dep"], r["feed_ts"])
            prev = {"delay_arr": r["delay_arr"], "delay_dep": r["delay_dep"],
                    "feed_ts": r["feed_ts"]}
        last = {"delay_arr": r["delay_arr"], "delay_dep": r["delay_dep"]}

    # Pisemo samo tam, kjer se ponovitev od `run` razlikuje za vsaj minuto.
    # Dnevnik belezi le spremembe nad `OBS_MIN_DELTA_S`, `run` pa vsako -- kdor
    # bi cezenj prepisal ves ponovljeni dnevnik, bi 16 696 vrstic zamenjal za
    # do minuto grobejse, da bi popravil 4 217 pokvarjenih. Minuta je hkrati
    # locljivost prikaza: pod njo ni kaj popravljati.
    changed = 0
    with conn:
        for (trip_id, day, seq), (arr, dep, ts) in accepted.items():
            cur = conn.execute(
                "SELECT delay_arr, delay_dep FROM run "
                "WHERE trip_id=? AND service_date=? AND stop_seq=?",
                (trip_id, day, seq),
            ).fetchone()
            if cur is None:
                continue
            staro = cur["delay_dep"] if cur["delay_dep"] is not None else cur["delay_arr"]
            novo = dep if dep is not None else arr
            if staro is None or novo is None or abs(novo - staro) < OBS_MIN_DELTA_S:
                continue
            conn.execute(
                "INSERT INTO run(trip_id,service_date,stop_seq,delay_arr,delay_dep,feed_ts) "
                "VALUES(?,?,?,?,?,?) "
                "ON CONFLICT(trip_id,service_date,stop_seq) DO UPDATE SET "
                "delay_arr=excluded.delay_arr, delay_dep=excluded.delay_dep, "
                "feed_ts=excluded.feed_ts",
                (trip_id, day, seq, arr, dep, ts),
            )
            changed += 1
    return {"stops": len(accepted), "blips_skipped": fixed,
            "unpassed_skipped": unpassed, "run_rows_corrected": changed}


# ---------------------------------------------------------------- lega vozil

# Koliko sekund je lega še "zdaj". Feed osvežuje na ~30 s; nad tem je vozilo
# ali končalo vožnjo ali izgubilo signal in prikaz ga ne sme risati kot živega.
POSITION_FRESH_S = 180


def ingest_positions(conn: sqlite3.Connection, feed,
                     brez_voznje: list[dict] | None = None) -> dict:
    """Zapiše trenutno lego vozil.

    Feed `vehicle_positions` nosi **samo avtobuse** -- vlakov v njem ni. Za
    avtobus je to torej edina prava lega v celem projektu: vse drugo, kar
    aplikacija riše, je zadnja postaja z meritvijo, ne dejanski položaj.

    Zgodovine ne vodimo. 130 vozil na 30 s je ~300 000 točk na dan, prikaz
    "kje je zdaj" pa rabi eno vrstico na vožnjo -- zato upsert.

    Vozila na vožnjah, ki jih vozni red ne pozna, gredo v `brez_voznje`, če
    je dan: v `vehicle_now` ne smejo, ker tam vse teče prek `JOIN trip`.
    """
    known = {r["trip_id"] for r in conn.execute("SELECT trip_id FROM trip")}
    windows = _rail_trip_windows(conn)
    zamenjave = _zamenjave(conn)
    seen_at = int(time.time())
    written = 0

    for entity in feed.entity:
        v = entity.vehicle
        trip_id = v.trip.trip_id
        stop_seq = v.current_stop_sequence or None
        # Isto kot pri zamudah: vozilo, ki ga feed javlja pod starim id-jem,
        # sodi k naslednici -- sicer ga zemljevid riše ob vožnji, ki je ni.
        z = zamenjave.get(trip_id) if trip_id not in windows else None
        if z is not None:
            trip_id = z[0]
            p = z[1].get(stop_seq)
            stop_seq = p[0] if p else None
        if not v.HasField("position"):
            continue
        if trip_id not in known:
            if brez_voznje is not None and trip_id:
                brez_voznje.append({
                    "trip_id": trip_id, "vehicle_id": v.vehicle.id or None,
                    "seen_ts": v.timestamp or seen_at,
                    "lat": v.position.latitude, "lon": v.position.longitude,
                    "bearing": v.position.bearing if v.position.HasField("bearing") else None,
                    "speed_ms": v.position.speed if v.position.HasField("speed") else None})
            continue
        day = v.trip.start_date or ""
        if len(day) == 8:
            day = f"{day[:4]}-{day[4:6]}-{day[6:]}"
        conn.execute(
            "INSERT INTO vehicle_now(trip_id, service_date, seen_ts, lat, lon, bearing,"
            "                        speed_ms, stop_seq, status, vehicle_id, plate) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(trip_id) DO UPDATE SET "
            "  service_date=excluded.service_date, seen_ts=excluded.seen_ts,"
            "  lat=excluded.lat, lon=excluded.lon, bearing=excluded.bearing,"
            "  speed_ms=excluded.speed_ms, stop_seq=excluded.stop_seq,"
            "  status=excluded.status, vehicle_id=excluded.vehicle_id, plate=excluded.plate "
            "WHERE excluded.seen_ts >= vehicle_now.seen_ts",
            (trip_id, day or None, v.timestamp or seen_at,
             v.position.latitude, v.position.longitude,
             v.position.bearing if v.position.HasField("bearing") else None,
             v.position.speed if v.position.HasField("speed") else None,
             stop_seq, v.current_status,
             v.vehicle.id or None, v.vehicle.license_plate or None),
        )
        written += 1

    # Stare lege pobrisi -- tabela naj ostane "zdaj", ne smetisce.
    conn.execute("DELETE FROM vehicle_now WHERE seen_ts < ?", (seen_at - 3600,))
    conn.commit()
    return {"vehicles": written}


def poll_positions(conn: sqlite3.Connection) -> dict:
    feed = fetch(config.VEHICLE_POSITIONS_URL, conn, "positions_etag")
    # Cas branja zapisemo tudi ob 304: pomeni "ob tem casu smo lege potrdili".
    # Iz njega prikaz ve, kdaj ima smisel vprasati znova -- brez tega brskalnik
    # ugiba in polovico svojega ritma zapravi za cakanje na podatek, ki ze je.
    db.set_meta(conn, "positions_fetched", str(int(time.time())))
    if feed is None:
        conn.commit()
        return {"vehicles": 0, "unchanged": True}
    izid = ingest_positions(conn, feed)
    # Za vožnje, ki jih feed zamud ne nosi, zamudo izmerimo iz lege sami.
    # Za `ingest_positions`, da so lege shranjene tudi, če to odpove.
    if config.ZAMUDA_IZ_LEGE:
        izid["iz_lege"] = iz_lege.iz_feeda(conn, feed)
    return izid


# ---------------------------------------------------------------- obrezovanje

# Koliko dni dnevnika `obs` obdrzimo. `run` (zadnje stanje na postanek) se NE
# brise nikoli -- ta je zgodovina, iz katere zivijo statistika, "obicajna
# zamuda" in backtest.
#
# Zakaj sploh: z vsemi prevozniki nastane ~300 000 vrstic `obs` na dan.
# Ena vrstica stane 79 B (41 B tabela + 38 B kljuc, merjeno z `dbstat`),
# torej 24 MB na dan in 8,7 GB na leto. Zeleznica jih naredi 4 000 -- 1 %.
#
# Zato dve meji. Zeleznica je jedro projekta in njen dnevnik je poceni, zato
# ga hranimo cetrt leta (toliko, kolikor projekt naceruje za analizo vremena
# kot dejavnika). Avtobusi so dodatek, kjer za prikaz zadosca `run`, njihov
# dnevnik pa je 75-krat drazji.
OBS_KEEP_DAYS = 90
OBS_KEEP_DAYS_BUS = 14


def prune_obs(conn: sqlite3.Connection, rail_days: int = OBS_KEEP_DAYS,
              bus_days: int = OBS_KEEP_DAYS_BUS) -> dict:
    """Pobriše stare vrstice dnevnika `obs`. `run` pusti pri miru.

    Idempotentno. Brisanje je nepovratno, zato meji nista skriti v kodi,
    ampak sta argumenta in ju `kajros prune` izpiše, preden briše.
    """
    today = datetime.now(TZ).date()
    rail_before = (today - timedelta(days=rail_days)).isoformat()
    bus_before = (today - timedelta(days=bus_days)).isoformat()

    with conn:
        rail = conn.execute(
            "DELETE FROM obs WHERE service_date < ? AND trip_id IN "
            "(SELECT trip_id FROM trip WHERE network = 'zeleznica')",
            (rail_before,),
        ).rowcount
        bus = conn.execute(
            "DELETE FROM obs WHERE service_date < ? AND trip_id IN "
            "(SELECT trip_id FROM trip WHERE network = 'avtobus')",
            (bus_before,),
        ).rowcount
    return {
        "rail_deleted": rail, "rail_before": rail_before,
        "bus_deleted": bus, "bus_before": bus_before,
        "obs_left": conn.execute("SELECT COUNT(*) FROM obs").fetchone()[0],
    }
