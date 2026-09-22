"""Vožnja z novim id-jem, ki jo feed v živo še nosi pod starim.

22. 9. 2026 so linije LPP 25, 12D in 15 v IJPP dobile nove id-je, feed pa je
vozila javljal pod starimi. Zajem jih je zavrgel, iskalnik pa je avtobus, ki je
zamujal okoli 20 minut, ponudil po voznem redu. Ti testi postavijo isti primer
v majhno bazo in preverijo, da zamuda in lega prideta do nove vožnje.

    ./venv/bin/python -m pytest tests/test_zamenjava.py -q
"""
from __future__ import annotations

import sqlite3
from datetime import date, datetime

from google.transit import gtfs_realtime_pb2

from kajros import collector, db, gtfs

DANES = date.today().isoformat()


def _vozja(stari_zacetek, postanki, dnevi=(DANES,), kljuc=("1118", "25")):
    return {"kljuc": kljuc, "dnevi": set(dnevi),
            "postanki": [(i + 1, sid, None, stari_zacetek + i * 60)
                         for i, sid in enumerate(postanki)]}


# ---------------------------------------------------------------- povezovanje

def test_poveze_najblizjo_vozjo_iste_linije():
    """Dve novi vožnji ob 15:28 in 15:48: stara 15:29 je prva, ne druga."""
    stare = {"s1": _vozja(15 * 3600 + 29 * 60, ["A", "B", "C"])}
    nove = {"n1": _vozja(15 * 3600 + 28 * 60, ["A", "B", "C"]),
            "n2": _vozja(15 * 3600 + 48 * 60, ["A", "B", "C"])}
    pari = gtfs.povezi_zamenjave(stare, nove)
    assert pari["s1"][0] == "n1"
    # Postanki nesejo STARI vozni red -- nanj se nanaša feedova zamuda.
    assert pari["s1"][1][0] == (1, 1, None, 15 * 3600 + 29 * 60)


def test_vsaka_nova_vozja_dobi_najvec_eno_staro():
    """Dve stari vozili v isto novo vožnjo bi pisali eno čez drugo."""
    stare = {"s1": _vozja(36000, ["A", "B", "C"]),
             "s2": _vozja(36000 + 120, ["A", "B", "C"])}
    nove = {"n1": _vozja(36000, ["A", "B", "C"])}
    pari = gtfs.povezi_zamenjave(stare, nove)
    assert pari == {"s1": ("n1", pari["s1"][1])}


def test_ne_poveze_cez_mejo_premika():
    stare = {"s1": _vozja(36000, ["A", "B", "C"])}
    nove = {"n1": _vozja(36000 + gtfs.ZAMENJAVA_PREMIK_S + 60, ["A", "B", "C"])}
    assert gtfs.povezi_zamenjave(stare, nove) == {}


def test_ne_poveze_druge_linije_ali_drugih_dni():
    stare = {"s1": _vozja(36000, ["A", "B", "C"])}
    assert gtfs.povezi_zamenjave(
        stare, {"n1": _vozja(36000, ["A", "B", "C"], kljuc=("1118", "12D"))}) == {}
    assert gtfs.povezi_zamenjave(
        stare, {"n1": _vozja(36000, ["A", "B", "C"], dnevi=("2000-01-01",))}) == {}


def test_nasprotna_smer_ni_zamenjava():
    """Mestno postajališče ima svoj id za vsako smer; vrstni red pa odloči
    tudi tam, kjer bi bili id-ji isti."""
    stare = {"s1": _vozja(36000, ["A", "B", "C", "D"])}
    nove = {"n1": _vozja(36000, ["D", "C", "B", "A"])}
    assert gtfs.povezi_zamenjave(stare, nove) == {}


def test_postanki_po_postajaliscu_ne_po_zaporedni_stevilki():
    """Nova vožnja izpusti B: C je pri njej drugi postanek, ne tretji."""
    stare = {"s1": _vozja(36000, ["A", "B", "C", "D"])}
    nove = {"n1": _vozja(36000, ["A", "C", "D"])}
    postanki = gtfs.povezi_zamenjave(stare, nove)["s1"][1]
    assert [(s, n) for s, n, _, _ in postanki] == [(1, 1), (3, 2), (4, 3)]


# ---------------------------------------------------------------- zamuda

def _stu(seq, delay=None, cas=None):
    s = gtfs_realtime_pb2.TripUpdate.StopTimeUpdate()
    s.stop_sequence = seq
    if delay is not None:
        s.departure.delay = delay
    if cas is not None:
        s.departure.time = int(cas)
    return s


def test_zamuda_se_preracuna_na_nov_vozni_red():
    """Staro 15:29 +20 min je 15:49; po novem voznem redu 15:28 je to +21."""
    stari, novi = (None, 15 * 3600 + 29 * 60), (None, 15 * 3600 + 28 * 60)
    assert collector.zamuda_po_zamenjavi(
        _stu(26, delay=1200), "departure", stari, novi, DANES) == 1260


def test_absolutni_cas_ostane_isti():
    """Avtobusi večinoma pošljejo uro; ta se od voznega reda ne spremeni."""
    stari, novi = (None, 15 * 3600 + 29 * 60), (None, 15 * 3600 + 28 * 60)
    d = date.today()
    ura = datetime(d.year, d.month, d.day, 15, 49,
                   tzinfo=collector.TZ).timestamp()
    assert collector.zamuda_po_zamenjavi(
        _stu(26, cas=ura), "departure", stari, novi, DANES) == 21 * 60


# ---------------------------------------------------------------- zajem

def _baza():
    c = db.connect(":memory:")
    db.init(c)
    c.execute("INSERT INTO service_day(service_id, date) VALUES('nov', ?)", (DANES,))
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id,"
              " mode, agency, network) VALUES('n1','r','25','Zadobrova','nov','bus','1118','avtobus')")
    # Nova vožnja nima postanka 2 stare (seq 2 -> B je izpuščen).
    c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)",
                  [("n1", 1, "A", None, 15 * 3600), ("n1", 2, "C", None, 15 * 3600 + 28 * 60)])
    db.fill_trip_window(c)
    c.executemany(
        "INSERT INTO zamenjava(stari_trip, stari_seq, novi_trip, novi_seq, stari_arr_s, stari_dep_s)"
        " VALUES(?,?,?,?,?,?)",
        [("s1", 1, "n1", 1, None, 15 * 3600), ("s1", 3, "n1", 2, None, 15 * 3600 + 29 * 60)])
    c.commit()
    return c


def _feed(trip_id, *stus):
    f = gtfs_realtime_pb2.FeedMessage()
    f.header.gtfs_realtime_version = "2.0"
    e = f.entity.add()
    e.id = "1"
    e.trip_update.trip.trip_id = trip_id
    e.trip_update.trip.start_date = DANES.replace("-", "")
    for s in stus:
        e.trip_update.stop_time_update.add().CopyFrom(s)
    return f


def test_zajem_zapise_pod_novo_vozjo():
    c = _baza()
    izid = collector.ingest(c, _feed("s1", _stu(3, delay=1200)))
    assert izid["zamenjanih"] == 1 and izid["neznanih"] == 0
    vrstice = c.execute("SELECT trip_id, stop_seq, delay_dep FROM run").fetchall()
    assert [tuple(r) for r in vrstice] == [("n1", 2, 1260)]


def test_postanek_brez_para_se_izpusti_in_neznana_vozja_steje():
    c = _baza()
    collector.ingest(c, _feed("s1", _stu(2, delay=300)))
    assert c.execute("SELECT COUNT(*) FROM run").fetchone()[0] == 0
    assert collector.ingest(c, _feed("x9", _stu(1, delay=60)))["neznanih"] == 1


def test_lega_gre_k_novi_vozji():
    c = _baza()
    f = gtfs_realtime_pb2.FeedMessage()
    f.header.gtfs_realtime_version = "2.0"
    e = f.entity.add()
    e.id = "1"
    e.vehicle.trip.trip_id = "s1"
    e.vehicle.position.latitude, e.vehicle.position.longitude = 46.05, 14.53
    e.vehicle.current_stop_sequence = 3
    collector.ingest_positions(c, f)
    assert tuple(c.execute("SELECT trip_id, stop_seq FROM vehicle_now").fetchone()) == ("n1", 2)


# ---------------------------------------------------------------- iz kopije baze

def test_zamenjave_iz_starejse_kopije():
    """Uvoz je že tekel; stari vozni red je samo še v varnostni kopiji."""
    stara = sqlite3.connect(":memory:")
    db.init(stara)
    stara.execute("INSERT INTO service_day(service_id, date) VALUES('star', ?)", (DANES,))
    stara.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, agency)"
                  " VALUES('s1','r','25','star','1118')")
    stara.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s)"
                      " VALUES(?,?,?,?,?)",
                      [("s1", 1, "A", None, 15 * 3600), ("s1", 2, "B", None, 15 * 3600 + 60),
                       ("s1", 3, "C", None, 15 * 3600 + 29 * 60)])
    db.fill_trip_window(stara)

    c = _baza()
    c.execute("DELETE FROM zamenjava")
    assert gtfs.zamenjave_iz(c, stara)["povezanih"] == 1
    assert [tuple(r) for r in c.execute(
        "SELECT stari_seq, novi_seq, stari_dep_s FROM zamenjava ORDER BY stari_seq")] == [
        (1, 1, 15 * 3600), (3, 2, 15 * 3600 + 29 * 60)]
