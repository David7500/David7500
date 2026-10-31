"""Žive vožnje LPP brez objavljenega voznega reda (`zive.py`).

26. 10. 2026: feed je nosil 14 od 15 voženj linije 27 pod id-ji, ki jih
objava ni imela, vse po Vilharjevi (Navje); objava pa je ta teden 27 peljala
mimo kolodvora (Kolodvor, Friškovec). Ure so bile ure objavljenih voženj.
Ti testi postavijo isti primer v majhno bazo: vozni red okrog zdajšnje ure,
ker zajem prometni dan razreši po uri stene.

    ./venv/bin/python -m pytest tests/test_zive.py -q
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta

import pytest
from google.transit import gtfs_realtime_pb2

from kajros import alerts, collector, db, iz_lege, journey, lpp, stats, zamude_lpp, zive

ZDAJ = time.time()
DAN = datetime.fromtimestamp(ZDAJ, stats.TZ).date().isoformat()
TEDEN = (datetime.fromtimestamp(ZDAJ, stats.TZ).date() + timedelta(days=7)).isoformat()
POLNOC = stats.polnoc(DAN)
#: Zdajšnja minuta v voznorednih sekundah današnjega dne.
T0 = (int(ZDAJ) - POLNOC) // 60 * 60
# Objava (vzorec MAS) in vzorec, ki ga LPP vozi (VIL): skupni so V, A, B, C,
# D, R; Navje (N) samo po Vilharjevi, Kolodvor in Friškovec samo v objavi.
POSTAJE = {"V": "Vevče", "A": "Studenec", "B": "BTC", "N": "Navje", "K": "Kolodvor",
           "F": "Friškovec", "C": "Drama", "D": "Križanke", "R": "NS Rudnik"}
LEGE = {"V": (46.060, 14.600), "A": (46.060, 14.580), "B": (46.060, 14.560),
        "N": (46.0599, 14.512), "K": (46.0577, 14.510), "F": (46.0575, 14.517),
        "C": (46.051, 14.505), "D": (46.048, 14.504), "R": (46.035, 14.520)}
MAS = [("V", 0), ("A", 120), ("B", 240), ("K", 360), ("F", 480), ("C", 600), ("D", 720),
       ("R", 840)]
VIL = [("V", 0), ("A", 120), ("B", 240), ("N", 390), ("C", 600), ("D", 720), ("R", 840)]
OBJAVA = {"D26|p1|MAS": T0 - 600, "D26|p2|MAS": T0 + 420, "D26|p3|MAS": T0 + 1440}


@pytest.fixture(autouse=True)
def _cist_spomin():
    def pocisti():
        zive._nacrti.clear()
        zive._preverjeni.clear()
        zive._SKUPINE.clear()
        zive._ne_gre.clear()
        zive._soglasje[:] = [0, 0]
        zive._pocisceno = 0.0
        iz_lege._v_feedu.clear()
        lpp._prihodi.clear()
    pocisti()
    yield
    pocisti()


def _voznja(c, tid, service_id, zacetek, postanki, shape=None, headsign="VEVČE - NS RUDNIK"):
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, mode,"
              " agency, network, shape_id) VALUES(?, 'R27', '27', ?, ?, 'bus', 'lpp',"
              " 'avtobus', ?)", (tid, headsign, service_id, shape))
    c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)",
                  [(tid, i + 1, s, zacetek + t, zacetek + t) for i, (s, t) in enumerate(postanki)])


def _baza():
    c = db.connect(":memory:")
    db.init(c)
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
                  [(s, ime, *LEGE[s]) for s, ime in POSTAJE.items()])
    c.executemany("INSERT INTO service_day(service_id, date) VALUES(?,?)",
                  [("D26", DAN), ("D02", TEDEN)])
    c.executemany("INSERT INTO shape(shape_id, points) VALUES(?, '[]')",
                  [("S_MAS",), ("S_VIL",)])
    for tid, z in OBJAVA.items():
        _voznja(c, tid, "D26", z, MAS, "S_MAS")
    # Vzorec, ki ga LPP vozi, ima vozni red drugega dne: od tam postanki in
    # vozni časi.
    _voznja(c, "D02|t0|VIL", "D02", 36000, VIL, "S_VIL",
            "VEVČE - NS RUDNIK (po Vilharjevi)")
    db.fill_trip_window(c)
    c.commit()
    return c


def _feed(*voznje, lege=()):
    """`voznje` = (trip_id, vozilo, [(seq, stop_id, čas ali None)]); objavljene
    vožnje gredo v feed pod svojim id-jem prav tako."""
    f = gtfs_realtime_pb2.FeedMessage()
    f.header.gtfs_realtime_version = "2.0"
    f.header.timestamp = int(ZDAJ)
    for i, (tid, vozilo, postanki) in enumerate(voznje):
        e = f.entity.add(id=f"t{i}")
        e.trip_update.trip.trip_id = tid
        e.trip_update.trip.route_id = "R27"
        if vozilo:
            e.trip_update.vehicle.id = vozilo
        for seq, sid, cas in postanki:
            u = e.trip_update.stop_time_update.add(stop_sequence=seq, stop_id=sid)
            if cas is None:
                u.arrival.delay = 0
            else:
                u.arrival.time = cas
    for i, (tid, vozilo, stop_id) in enumerate(lege):
        e = f.entity.add(id=f"v{i}")
        e.vehicle.trip.trip_id = tid
        e.vehicle.vehicle.id = vozilo
        e.vehicle.stop_id = stop_id
        e.vehicle.timestamp = int(ZDAJ)
        e.vehicle.position.latitude = 46.05
        e.vehicle.position.longitude = 14.51
    return f


def _napoved(zacetek, zamuda, od):
    """Postanki vzorca VIL od `od` naprej, z napovedjo za `zamuda` s."""
    return [(i + 1, s, POLNOC + zacetek + t + zamuda)
            for i, (s, t) in enumerate(VIL) if i + 1 >= od]


def _caka(zacetek):
    """Vožnja, ki še ni začela: vsi postanki, brez časa."""
    return [(i + 1, s, None) for i, (s, _) in enumerate(VIL)]


# ---------------------------------------------------------------- par

def test_par_po_uri_samo_nedvoumen():
    """Napoved na skupnih postajališčih se ujame z eno objavljeno vožnjo na
    +2 min, s sosednjima na -15 in -32 min: par. Vožnja, ki se v isti napovedi
    ujame z dvema, ostane brez para."""
    c = _baza()
    feed = _feed(("D26|L1|VIL", "bus-1", _napoved(OBJAVA["D26|p1|MAS"], 120, 5)))
    izid = zive.razresi(c, feed, ZDAJ)
    assert izid["pari"] == {"D26|L1|VIL": "D26|p1|MAS"}
    nacin, zamik = c.execute("SELECT nacin, zamik_s FROM ziva_voznja").fetchone()
    assert (nacin, zamik) == ("ura", 120)

    # Gosta linija: druga objavljena vožnja 5 min za prvo -- zamuda +2 ali -3.
    c2 = _baza()
    _voznja(c2, "D26|p1b|MAS", "D26", OBJAVA["D26|p1|MAS"] + 300, MAS, "S_MAS")
    db.fill_trip_window(c2)
    izid = zive.razresi(c2, feed, ZDAJ)
    assert izid["pari"] == {} and izid["stevci"]["brez_para"] == 1


def test_par_po_nacrtu_lpp_jevega_zaslona():
    """Vožnja, ki še ni začela, napovedi nima. LPP-jev zaslon je za njeno
    vozilo kazal načrt na BTC 40 s za objavljeno uro druge vožnje: par."""
    c = _baza()
    zive.zabelezi_nacrt("BUS-2", "VIL", "B", POLNOC + OBJAVA["D26|p2|MAS"] + 240 + 40, ZDAJ - 60)
    izid = zive.razresi(c, _feed(("D26|L2|VIL", "bus-2", _caka(OBJAVA["D26|p2|MAS"]))), ZDAJ)
    assert izid["pari"] == {"D26|L2|VIL": "D26|p2|MAS"}
    assert c.execute("SELECT nacin FROM ziva_voznja").fetchone()[0] == "nacrt"


def test_nacrt_za_poznejso_voznjo_vozila_ni_par():
    """Linija SŽ 26. 10. 2026: zaslon je za vozilo kazal načrt za 17:55, vozilo
    pa je čakalo na vožnjo ob 17:15, katere načrta ni kazal. Prosta objavljena,
    ki začne prej, pomeni, da je načrt za poznejšo vožnjo -- para ni."""
    c = _baza()
    zive.zabelezi_nacrt("bus-2", "VIL", "B", POLNOC + OBJAVA["D26|p3|MAS"] + 240 + 40, ZDAJ - 60)
    izid = zive.razresi(c, _feed(("D26|L2|VIL", "bus-2", _caka(OBJAVA["D26|p2|MAS"]))), ZDAJ)
    assert izid["pari"] == {}


def test_zasedena_objavljena_ne_dobi_druge_zive():
    """Druga živa z isto napovedjo (podvojen vnos v feedu) je dvojnik: para
    ni, šteje se ne. Živa, ki se ujame z isto objavljeno, a vozi 8 min pred
    sparjeno, je drug avtobus -- vožnja mimo voznega reda."""
    c = _baza()
    zive.razresi(c, _feed(("D26|L1|VIL", "bus-1", _napoved(OBJAVA["D26|p1|MAS"], 480, 5))), ZDAJ)
    izid = zive.razresi(c, _feed(("D26|L1|VIL", "bus-1", _napoved(OBJAVA["D26|p1|MAS"], 480, 5)),
                                 ("D26|Lx|VIL", "bus-9", _napoved(OBJAVA["D26|p1|MAS"], 420, 5)),
                                 ("D26|Ly|VIL", "bus-8", _napoved(OBJAVA["D26|p1|MAS"], 0, 5))),
                        ZDAJ)
    assert izid["pari"] == {"D26|L1|VIL": "D26|p1|MAS"}
    assert izid["dvojniki"] == {"D26|Lx|VIL"}
    assert set(izid["brez_para"]) == {"D26|Ly|VIL"}


def test_dvojnik_objavljene_ki_vozi_pod_svojim_id_jem():
    """26. 10. 2026 linija 2: objavljeno vožnjo je feed nosil pod njenim id-jem,
    ob njej živo brez vozila z zadnjimi postanki ob njenih urah. Para ni, v
    zajemu se ne šteje kot vožnja mimo voznega reda."""
    c = _baza()
    z = OBJAVA["D26|p1|MAS"]
    objavljena = [(i + 1, s, POLNOC + z + t + 60) for i, (s, t) in enumerate(MAS) if i >= 4]
    feed = _feed(("D26|p1|MAS", "bus-1", objavljena),
                 ("D26|Lg|VIL", None, _napoved(z, 0, 5)))
    izid = zive.razresi(c, feed, ZDAJ)
    assert izid["pari"] == {} and izid["dvojniki"] == {"D26|Lg|VIL"}
    st = collector.ingest(c, feed, vir="lpp", pari=izid["pari"], dvojniki=izid["dvojniki"])
    assert st["neznanih"] == 0 and st["proge"] == {"R27": [0, 1]}


def test_par_pade_ko_objavljena_vozi_sama():
    """Živa je pripeta, nato feed objavljeno nosi pod njenim id-jem z
    napovedjo: tista vozi sama, živa je njen dvojnik."""
    c = _baza()
    z = OBJAVA["D26|p1|MAS"]
    zive.razresi(c, _feed(("D26|L1|VIL", None, _napoved(z, 60, 5))), ZDAJ)
    assert zive.pari(c, DAN) == {"D26|L1|VIL": "D26|p1|MAS"}
    objavljena = [(i + 1, s, POLNOC + z + t + 60) for i, (s, t) in enumerate(MAS) if i >= 5]
    izid = zive.razresi(c, _feed(("D26|p1|MAS", "bus-1", objavljena),
                                 ("D26|L1|VIL", None, _napoved(z, 60, 5))), ZDAJ)
    assert izid["pari"] == {} and izid["dvojniki"] == {"D26|L1|VIL"}
    assert izid["stevci"]["zavrzenih"] == 1


# ---------------------------------------------------------------- popravek vzorca

def _dva_para(c):
    zive.zabelezi_nacrt("bus-2", "VIL", "B", POLNOC + OBJAVA["D26|p2|MAS"] + 240 + 40, ZDAJ - 60)
    feed = _feed(("D26|L1|VIL", "bus-1", _napoved(OBJAVA["D26|p1|MAS"], 120, 5)),
                 ("D26|L2|VIL", "bus-2", _caka(OBJAVA["D26|p2|MAS"])),
                 lege=[("D26|L1|VIL", "bus-1", "C")])
    return feed, zive.razresi(c, feed, ZDAJ)


def test_objava_prestavljena_na_vzorec_ki_ga_lpp_vozi():
    """Dve sparjeni vožnji po Vilharjevi: tudi tretja objavljena, ki je še
    nihče ni vozil, gre prek Navja in ne prek Kolodvora."""
    c = _baza()
    _, izid = _dva_para(c)
    assert izid["stevci"]["popravljenih"] == 3
    z = OBJAVA["D26|p3|MAS"]
    post = c.execute("SELECT stop_seq, stop_id, arr_s, dep_s FROM sched "
                     "WHERE trip_id = 'D26|p3|MAS' ORDER BY stop_seq").fetchall()
    # Skupni ostanejo ob objavljeni uri in pod objavljeno številko (nanje se
    # sklicujejo meritve); Navje po voznih časih vzorca (6,5 min med BTC ob 4
    # in Dramo ob 10 min), na minuto, pod prosto številko Kolodvora.
    assert [tuple(r) for r in post] == [
        (1, "V", z, z), (2, "A", z + 120, z + 120), (3, "B", z + 240, z + 240),
        (4, "N", z + 420, z + 420), (6, "C", z + 600, z + 600), (7, "D", z + 720, z + 720),
        (8, "R", z + 840, z + 840)]
    t = c.execute("SELECT shape_id, headsign, start_s, end_s, first_seq, last_seq FROM trip "
                  "WHERE trip_id = 'D26|p3|MAS'").fetchone()
    assert tuple(t) == ("S_VIL", "VEVČE - NS RUDNIK (po Vilharjevi)", z, z + 840, 1, 8)
    assert db.get_meta(c, "vozni_red_popravljen")
    assert zive.vzorec_lpp(c, "D26|p3|MAS") == "vil"
    # Objava je shranjena za razveljavitev.
    assert len(json.loads(c.execute("SELECT postanki FROM popravek_vzorca "
                                    "WHERE trip_id = 'D26|p3|MAS'").fetchone()[0])) == 8


def test_tabla_po_popravku_navje_da_kolodvor_ne():
    c = _baza()
    _dva_para(c)
    c.commit()
    navje = journey.board(c, "Navje", DAN, T0 - 3600, network="avtobus")
    kolodvor = journey.board(c, "Kolodvor", DAN, T0 - 3600, network="avtobus")
    assert {r["trip_id"] for r in navje} == set(OBJAVA)
    assert kolodvor == []


def test_zamuda_in_lega_zive_voznje_pod_objavljeno():
    c = _baza()
    feed, izid = _dva_para(c)
    st = collector.ingest(c, feed, vir="lpp", pari=izid["pari"])
    assert st["pripetih"] == 2 and st["neznanih"] == 0
    # Popravljena p1: V1 A2 B3 N4 C6 D7 R8. Feed je napovedal C, D, R.
    vrstice = c.execute("SELECT stop_seq, COALESCE(delay_dep, delay_arr) FROM run "
                        "WHERE trip_id = 'D26|p1|MAS' ORDER BY stop_seq").fetchall()
    assert [tuple(r) for r in vrstice] == [(6, 120), (7, 120), (8, 120)]
    collector.ingest_positions(c, feed, [], izid["pari"])
    v = c.execute("SELECT trip_id, stop_seq, vehicle_id FROM vehicle_now").fetchone()
    assert tuple(v) == ("D26|p1|MAS", 6, "bus-1")


def test_prestavljena_pod_svojim_id_jem_po_postajaliscu():
    """Prestavljeno vožnjo feed nosi pod njenim id-jem, postanke šteje po
    živem vzorcu (Navje 4, Drama 5): zamuda gre na naše številke (Drama 6)."""
    c = _baza()
    _dva_para(c)
    z = OBJAVA["D26|p3|MAS"]
    feed = _feed(("D26|p3|MAS", "bus-3", _napoved(z, 60, 4)),
                 lege=[("D26|p3|MAS", "bus-3", "N")])
    assert zive.razresi(c, feed, ZDAJ)["stevci"]["vrnjenih"] == 0
    collector.ingest(c, feed, vir="lpp")
    vrstice = c.execute("SELECT stop_seq, COALESCE(delay_dep, delay_arr) FROM run "
                        "WHERE trip_id = 'D26|p3|MAS' ORDER BY stop_seq").fetchall()
    # Navje: napoved ob 6,5 min + 1, naš vozni red na minuto ob 7.
    assert [tuple(r) for r in vrstice] == [(4, 30), (6, 60), (7, 60), (8, 60)]
    collector.ingest_positions(c, feed, [])
    assert c.execute("SELECT stop_seq FROM vehicle_now").fetchone()[0] == 4


def test_obvoz_konca_prestavljene_brez_para_se_vrnejo():
    """LPP spet vozi objavo: prestavljena vožnja pod svojim id-jem napove
    Kolodvor. Vrne se ona in vse prestavljene brez para tega dne; sparjeni
    ostaneta. Tudi ko je ni več v feedu, se ne prestavijo znova -- meritve
    pod objavljenim id-jem so dokaz."""
    c = _baza()
    _voznja(c, "D26|p4|MAS", "D26", T0 + 2400, MAS, "S_MAS")
    db.fill_trip_window(c)
    feed, izid = _dva_para(c)
    assert izid["stevci"]["popravljenih"] == 4
    z = OBJAVA["D26|p3|MAS"]
    po_objavi = [(i + 1, s, POLNOC + z + t) for i, (s, t) in enumerate(MAS)]
    feed3 = _feed(("D26|L1|VIL", "bus-1", _napoved(OBJAVA["D26|p1|MAS"], 120, 5)),
                  ("D26|p3|MAS", "bus-3", po_objavi))
    izid = zive.razresi(c, feed3, ZDAJ)
    assert izid["stevci"]["vrnjenih"] == 2
    kolodvor = dict(c.execute("SELECT trip_id, COUNT(*) FROM sched WHERE stop_id = 'K' "
                              "GROUP BY trip_id").fetchall())
    assert kolodvor == {"D26|p3|MAS": 1, "D26|p4|MAS": 1}
    collector.ingest(c, feed3, vir="lpp", pari=izid["pari"])
    izid = zive.razresi(c, feed, ZDAJ)
    assert izid["stevci"]["popravljenih"] == 0
    assert c.execute("SELECT COUNT(*) FROM sched WHERE stop_id = 'K'").fetchone()[0] == 2


def test_ko_lpp_vozi_tudi_objavo_samo_sparjene():
    """Ena živa vožnja vozi objavljen vzorec (le z drugim id-jem): LPP vozi
    oba, prestavita se samo sparjeni, ne vse ostale."""
    c = _baza()
    _voznja(c, "D02|t1|MAS", "D02", 36000, MAS, "S_MAS")
    zive.zabelezi_nacrt("bus-2", "VIL", "B", POLNOC + OBJAVA["D26|p2|MAS"] + 240 + 40, ZDAJ - 60)
    zive.zabelezi_nacrt("bus-3", "MAS", "B", POLNOC + OBJAVA["D26|p3|MAS"] + 240 + 40, ZDAJ - 60)
    db.fill_trip_window(c)
    feed = _feed(("D26|L1|VIL", "bus-1", _napoved(OBJAVA["D26|p1|MAS"], 120, 5)),
                 ("D26|L2|VIL", "bus-2", _caka(OBJAVA["D26|p2|MAS"])),
                 ("D26|L3|MAS", "bus-3", [(i + 1, s, None) for i, (s, _) in enumerate(MAS)]))
    izid = zive.razresi(c, feed, ZDAJ)
    assert izid["pari"]["D26|L3|MAS"] == "D26|p3|MAS"
    assert izid["stevci"]["popravljenih"] == 2
    assert c.execute("SELECT COUNT(*) FROM sched WHERE trip_id = 'D26|p3|MAS' "
                     "AND stop_id = 'K'").fetchone()[0] == 1


def test_voznja_z_meritvami_se_ne_prestavi():
    """Zamude v `run` kažejo po `stop_seq`: preštevilčena vožnja bi jih
    pripisala drugim postankom."""
    c = _baza()
    c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
              "VALUES('D26|p3|MAS', ?, 6, 60, 60, ?)", (DAN, int(ZDAJ)))
    _dva_para(c)
    assert c.execute("SELECT COUNT(*) FROM sched WHERE trip_id = 'D26|p3|MAS' "
                     "AND stop_id = 'K'").fetchone()[0] == 1


def _uvoz(c, preimenuj=None):
    """Kar uvoz naredi prestavljenim vožnjam: objavljeni vozni red znova, vzorca
    na drugem dnevu pa ni več. `preimenuj` = (stari, novi) id, z zamenjavo."""
    c.execute("DELETE FROM sched WHERE trip_id = 'D02|t0|VIL'")
    c.execute("DELETE FROM trip WHERE trip_id = 'D02|t0|VIL'")
    for tid, post in c.execute("SELECT trip_id, postanki FROM popravek_vzorca").fetchall():
        c.execute("DELETE FROM sched WHERE trip_id = ?", (tid,))
        novi = preimenuj[1] if preimenuj and tid == preimenuj[0] else tid
        if novi != tid:
            c.execute("UPDATE trip SET trip_id = ? WHERE trip_id = ?", (novi, tid))
            c.executemany("INSERT INTO zamenjava(stari_trip, stari_seq, novi_trip, novi_seq) "
                          "VALUES(?,?,?,?)", [(tid, p[0], novi, p[0]) for p in json.loads(post)])
        c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) "
                      "VALUES(?,?,?,?,?)", [(novi, *p) for p in json.loads(post)])
    db.fill_trip_window(c)


def test_uvoz_popravek_naredi_znova():
    """Po uvozu se popravek naredi znova: na isti vožnji, tudi z meritvami (te
    so pisane po prestavljenih postankih), in na naslednici pod novim id-jem.
    Predloga je prestavljena vožnja sama -- vzorca v voznem redu ni več."""
    c = _baza()
    _dva_para(c)
    c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
              "VALUES('D26|p1|MAS', ?, 4, 60, 60, ?)", (DAN, int(ZDAJ)))
    pred = c.execute("SELECT trip_id, stop_seq, stop_id, arr_s FROM sched "
                     "WHERE trip_id LIKE 'D26|%' ORDER BY 1, 2").fetchall()
    _uvoz(c, ("D26|p3|MAS", "D26|p3n|MAS"))
    assert c.execute("SELECT COUNT(*) FROM sched WHERE stop_id = 'N'").fetchone()[0] == 0
    assert zive.uporabi_popravke(c, ZDAJ) == 3
    po = c.execute("SELECT trip_id, stop_seq, stop_id, arr_s FROM sched "
                   "WHERE trip_id LIKE 'D26|%' ORDER BY 1, 2").fetchall()
    assert [tuple(r) for r in po] == [
        (t.replace("p3|", "p3n|"), *r) for t, *r in (tuple(x) for x in pred)]
    assert zive.vzorec_lpp(c, "D26|p3n|MAS") == "vil"


def test_razveljavitev_vrne_objavo_in_pobrise_meritve_drugje():
    """Meritev na Navju (4) bi po razveljavitvi kazala na Kolodvor (4): gre.
    Drama (6) je v obeh pod isto številko in ostane."""
    c = _baza()
    _dva_para(c)
    c.executemany("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
                  "VALUES('D26|p1|MAS', ?, ?, 60, 60, ?)", [(DAN, 4, int(ZDAJ)), (DAN, 6, int(ZDAJ))])
    c.commit()
    assert zive.razveljavi(c) == 3
    assert c.execute("SELECT COUNT(*) FROM sched WHERE stop_id = 'K'").fetchone()[0] == 3
    assert c.execute("SELECT COUNT(*) FROM popravek_vzorca").fetchone()[0] == 0
    assert [r[0] for r in c.execute("SELECT stop_seq FROM run WHERE trip_id = 'D26|p1|MAS'")] == [6]


# Drug živ vzorec za isto objavo: mimo Friškovca, brez Kolodvora in Navja.
VI2 = [("V", 0), ("A", 120), ("B", 240), ("F", 450), ("C", 600), ("D", 720), ("R", 840)]


def _vi2(c):
    _voznja(c, "D02|t1|VI2", "D02", 39600, VI2, None, "VEVČE - NS RUDNIK (mimo Friškovca)")
    db.fill_trip_window(c)


def _caka_vi2():
    return [(i + 1, s, None) for i, (s, _) in enumerate(VI2)]


def test_dva_ziva_vzorca_vsaka_na_svojega():
    """Sparjeni vozita po Vilharjevi, tretja mimo Friškovca: vsaka gre na
    vzorec svoje žive, nesparjene pa ostanejo objavljene -- kateri vzorec
    vozijo, ni znano."""
    c = _baza()
    _vi2(c)
    _voznja(c, "D26|p4|MAS", "D26", T0 + 2400, MAS, "S_MAS")
    db.fill_trip_window(c)
    zive.zabelezi_nacrt("bus-2", "VIL", "B", POLNOC + OBJAVA["D26|p2|MAS"] + 240 + 40, ZDAJ - 60)
    zive.zabelezi_nacrt("bus-3", "VI2", "B", POLNOC + OBJAVA["D26|p3|MAS"] + 240 + 40, ZDAJ - 60)
    izid = zive.razresi(c, _feed(("D26|L1|VIL", "bus-1", _napoved(OBJAVA["D26|p1|MAS"], 120, 5)),
                                 ("D26|L2|VIL", "bus-2", _caka(OBJAVA["D26|p2|MAS"])),
                                 ("D26|L3|VI2", "bus-3", _caka_vi2())), ZDAJ)
    assert izid["pari"] == {"D26|L1|VIL": "D26|p1|MAS", "D26|L2|VIL": "D26|p2|MAS",
                            "D26|L3|VI2": "D26|p3|MAS"}
    postanki = {t: [r[0] for r in c.execute(
        "SELECT stop_id FROM sched WHERE trip_id = ? ORDER BY stop_seq", (t,))] for t in
        ("D26|p1|MAS", "D26|p3|MAS", "D26|p4|MAS")}
    assert postanki["D26|p1|MAS"] == ["V", "A", "B", "N", "C", "D", "R"]
    assert postanki["D26|p3|MAS"] == ["V", "A", "B", "F", "C", "D", "R"]
    assert postanki["D26|p4|MAS"] == [s for s, _ in MAS]


def test_prestavljena_po_skupini_dobi_par_drugega_vzorca():
    """Skupinski popravek je tretjo prestavil po Vilharjevi, nato jo dobi živa
    mimo Friškovca: vrne se in ob naslednjem branju gre na vzorec svoje žive;
    četrta brez para se vrne na objavo."""
    c = _baza()
    _vi2(c)
    _voznja(c, "D26|p4|MAS", "D26", T0 + 2400, MAS, "S_MAS")
    db.fill_trip_window(c)
    _dva_para(c)
    assert zive.vzorec_lpp(c, "D26|p3|MAS") == "vil"
    zive.zabelezi_nacrt("bus-3", "VI2", "B", POLNOC + OBJAVA["D26|p3|MAS"] + 240 + 40, ZDAJ - 60)
    feed = _feed(("D26|L1|VIL", "bus-1", _napoved(OBJAVA["D26|p1|MAS"], 120, 5)),
                 ("D26|L3|VI2", "bus-3", _caka_vi2()))
    izid = zive.razresi(c, feed, ZDAJ)
    assert izid["pari"]["D26|L3|VI2"] == "D26|p3|MAS"
    assert izid["stevci"]["vrnjenih"] == 2
    izid = zive.razresi(c, feed, ZDAJ)
    assert izid["stevci"]["popravljenih"] == 1
    assert zive.vzorec_lpp(c, "D26|p3|MAS") == "vi2"
    assert zive.vzorec_lpp(c, "D26|p4|MAS") == "MAS"
    assert zive.razresi(c, feed, ZDAJ)["stevci"]["vrnjenih"] == 0


def test_objavljena_z_vozilom_pod_svojim_id_jem_ni_za_par():
    """Vozilo pod objavljenim id-jem: objavljena vozi sama, tudi brez napovedi.
    Nova živa se nanjo ne pripne, obstoječi par pade."""
    c = _baza()
    z = OBJAVA["D26|p1|MAS"]
    zive.razresi(c, _feed(("D26|L1|VIL", None, _napoved(z, 60, 5))), ZDAJ)
    assert zive.pari(c, DAN) == {"D26|L1|VIL": "D26|p1|MAS"}
    izid = zive.razresi(c, _feed(("D26|L1|VIL", None, _napoved(z, 60, 5)),
                                 lege=[("D26|p1|MAS", "bus-1", "C")]), ZDAJ)
    assert izid["pari"] == {} and izid["dvojniki"] == {"D26|L1|VIL"}


def test_objavljena_brez_ure_in_vozila_je_na_voljo():
    """Linija SŽ 26. 10. 2026: objavljeno je feed eno uro nosil brez ure in
    vozila, vozilo pa je vozilo pod drugim id-jem ob njenih urah -- par."""
    c = _baza()
    z = OBJAVA["D26|p1|MAS"]
    izid = zive.razresi(c, _feed(("D26|p1|MAS", None, [(i + 1, s, None) for i, (s, _) in
                                                      enumerate(MAS)]),
                                 ("D26|L1|VIL", "bus-1", _napoved(z, 60, 5))), ZDAJ)
    assert izid["pari"] == {"D26|L1|VIL": "D26|p1|MAS"}


def test_voznja_z_dnevnikom_se_ne_prestavi():
    """`obs` brez `run` (ničle, ki jih `run` ni sprejel): `kajros repair` bi
    jih pisal po objavljenih številkah na prestavljene postanke."""
    c = _baza()
    c.execute("INSERT INTO obs(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts,"
              " observed_at) VALUES('D26|p3|MAS', ?, 4, 0, 0, ?, ?)", (DAN, int(ZDAJ), int(ZDAJ)))
    _dva_para(c)
    assert c.execute("SELECT COUNT(*) FROM sched WHERE trip_id = 'D26|p3|MAS' "
                     "AND stop_id = 'K'").fetchone()[0] == 1


def test_razveljavljen_dan_se_ne_prestavi_znova():
    c = _baza()
    feed, _ = _dva_para(c)
    assert zive.razveljavi(c, DAN) == 3
    assert zive.razresi(c, feed, ZDAJ)["stevci"]["popravljenih"] == 0
    assert c.execute("SELECT COUNT(*) FROM sched WHERE stop_id = 'K'").fetchone()[0] == 3
    assert zive.pregled(c, ZDAJ)["razveljavljeno"] == [DAN]


def test_prestavljena_naslednica_pod_starim_id_jem_po_postajaliscu():
    """Feed nosi vožnjo pod id-jem izpred uvoza (`zamenjava`), naslednica je
    prestavljena: številke zamenjave so objavljene, postanek gre po
    postajališču."""
    c = _baza()
    _dva_para(c)
    c.executemany("INSERT INTO zamenjava(stari_trip, stari_seq, novi_trip, novi_seq) "
                  "VALUES('D26|old3|MAS', ?, 'D26|p3|MAS', ?)", [(i, i) for i in range(1, 9)])
    z = OBJAVA["D26|p3|MAS"]
    feed = _feed(("D26|old3|MAS", "bus-3", _napoved(z, 60, 4)),
                 lege=[("D26|old3|MAS", "bus-3", "N")])
    collector.ingest(c, feed, vir="lpp")
    vrstice = c.execute("SELECT stop_seq, COALESCE(delay_dep, delay_arr) FROM run "
                        "WHERE trip_id = 'D26|p3|MAS' ORDER BY stop_seq").fetchall()
    assert [tuple(r) for r in vrstice] == [(4, 30), (6, 60), (7, 60), (8, 60)]
    collector.ingest_positions(c, feed, [])
    assert tuple(c.execute("SELECT trip_id, stop_seq FROM vehicle_now").fetchone()) == (
        "D26|p3|MAS", 4)


def test_brez_parov_ni_popravka(monkeypatch):
    monkeypatch.setattr(zive.config, "ZIVE", False)
    c = _baza()
    feed, izid = _dva_para(c)
    assert izid["pari"] == {} and izid["stevci"]["brez_para"] == 2
    assert c.execute("SELECT COUNT(*) FROM popravek_vzorca").fetchone()[0] == 0


# ---------------------------------------------------------------- deli

def test_nov_vozni_red_po_razdalji_brez_voznih_casov():
    objava = [(1, "V", 0, 0), (2, "B", 240, 240), (3, "K", 360, 360), (4, "C", 600, 600)]
    predloga = [("V", None), ("B", None), ("N", None), ("C", None)]
    nova = zive.nov_vozni_red(objava, predloga, [0, 1000, 1500, 3000])
    # Navje je na tretjini poti med BTC in Dramo: 240 + 360 / 3 = 360 s.
    assert nova == [(1, "V", 0, 0), (2, "B", 240, 240), (3, "N", 360, 360), (4, "C", 600, 600)]
    # Brez proste številke med BTC in Dramo se oštevilči znova.
    brez_k = [(1, "V", 0, 0), (2, "B", 240, 240), (3, "C", 600, 600)]
    assert zive.nov_vozni_red(brez_k, predloga, [0, 1000, 1500, 3000]) == nova
    # Predloga brez začetka objavljene vožnje ne pomaga.
    assert zive.nov_vozni_red(objava, predloga[1:], None) is None


def test_preslikava_po_postajaliscu_krozna_linija():
    """Krožna linija: postajališče P je na vožnji dvakrat, odloči ura."""
    nasi = [(1, "P", 0), (2, "Q", 300), (3, "S", 600), (4, "P", 900), (5, "T", 1200)]
    zivi = [(10, "P", 1000 + 905), (11, "T", 1000 + 1210)]
    assert zive.preslikaj(nasi, zivi, 1000) == {10: 4, 11: 5}


def test_zaslon_lpp_zapise_nacrt_za_vozilo():
    """`zamude_lpp` bere zaslone in načrt (vrsta 1) da `zive`."""
    prihod = {"route_name": "27", "trip_id": "VIL", "vehicle_id": "BUS-7", "type": 1,
              "eta_min": 12, "depot": 0}
    zamude_lpp.razberi([("100011", 1000.0, [prihod])], {"100011": "N"}, {}, {})
    assert zive._nacrti["bus-7"] == [("vil", "N", 1720.0, 1000.0)]


def test_obvoz_zive_voznje_pod_objavljeno():
    c = _baza()
    f = gtfs_realtime_pb2.FeedMessage()
    f.header.gtfs_realtime_version = "2.0"
    a = f.entity.add(id="a1").alert
    a.header_text.translation.add(text="Postaja Navje na obvozu", language="sl")
    ie = a.informed_entity.add(stop_id="N")
    ie.trip.trip_id = "D26|L1|VIL"
    alerts.ingest_lpp(c, f, {"D26|L1|VIL": "D26|p1|MAS"})
    assert c.execute("SELECT trip_id, stop_id FROM alert_entity").fetchall()[0][:] == (
        "D26|p1|MAS", "N")


def test_tabla_doda_linijo_kjer_je_objava_nima(monkeypatch):
    """Živa vožnja brez para ustavi na Navju, objava tam linije nima: tabla jo
    vzame z LPP-jevega zaslona. Na Kolodvoru LPP linije naslednjo uro ne kaže:
    objavljene vrstice v tej uri gredo s table."""
    c = _baza()
    db.set_meta(c, "lpp_linije_brez_voznje", json.dumps({
        "ts": ZDAJ, "linije": {"27": [14, 15]}, "postaje": {"27": ["N", "C"]}}))
    monkeypatch.setattr(lpp, "_postaje_lpp", lambda: [
        {"ref_id": "100011", "latitude": LEGE["N"][0], "longitude": LEGE["N"][1]},
        {"ref_id": "300011", "latitude": LEGE["K"][0], "longitude": LEGE["K"][1]}])
    prihod = {"route_name": "27", "eta_min": 4, "type": 0, "depot": 0,
              "trip_name": "VEVČE - BTC - NS RUDNIK (po Vilharjevi)", "vehicle_id": "x",
              "stations": {"departure": "VEVČE", "arrival": "NS RUDNIK"}}
    monkeypatch.setattr(lpp, "_prihodi_postaje",
                        lambda koda: {"100011": [prihod], "300011": []}.get(koda))
    zdaj = datetime.fromtimestamp(ZDAJ, stats.TZ)
    rows, mimo = lpp.na_tablo(c, [], zdaj, True, "Navje")
    assert mimo == ["27"] and [(r["train_no"], r["stop_id"]) for r in rows] == [("27", "N")]

    vrstica = {"trip_id": "D26|p2|MAS", "train_no": "27", "agency": "lpp", "stop_id": "K",
               "service_date": DAN, "t_s": T0 + 600}
    pozneje = dict(vrstica, trip_id="D26|p3|MAS", t_s=T0 + 4 * 3600)
    rows, mimo = lpp.na_tablo(c, [vrstica, pozneje], zdaj, True, "Kolodvor")
    assert mimo == ["27"] and [r["trip_id"] for r in rows] == ["D26|p3|MAS"]


def test_poll_lpp_pripne_in_zapise_pregled(monkeypatch):
    c = _baza()
    monkeypatch.setattr(collector.config, "LPP_ENABLED", True)
    zive.zabelezi_nacrt("bus-2", "VIL", "B", POLNOC + OBJAVA["D26|p2|MAS"] + 240 + 40, ZDAJ - 60)
    feed = _feed(("D26|L1|VIL", "bus-1", _napoved(OBJAVA["D26|p1|MAS"], 120, 5)),
                 ("D26|L2|VIL", "bus-2", _caka(OBJAVA["D26|p2|MAS"])),
                 lege=[("D26|L1|VIL", "bus-1", "C")])
    monkeypatch.setattr(collector, "fetch", lambda *a, **k: feed)
    collector.poll_lpp(c)
    assert db.get_meta(c, "lpp_rt_neznanih") == "0/2"
    p = zive.pregled(c, ZDAJ)
    assert p["sparjenih"] == 2 and p["pari_danes"] == {"nacrt": 1, "ura": 1}
    assert [(x["linija"], x["voznj"]) for x in p["popravki"]] == [("27", 3)]
    assert json.loads(db.get_meta(c, "lpp_vozila_brez_voznje"))["vozila"] == []


class _Sk:
    """Skupina brez baze: vožnja -> ure po postajališču, polnoč 0."""

    def __init__(self, voznje):
        self.polnoc = 0
        self.voznje = {t: {"start": min(u.values()), "ure": u} for t, u in voznje.items()}

    def zamuda(self, tid, napovedi):
        ure = self.voznje[tid]["ure"]
        r = sorted(t - ure[s] for s, t in napovedi.items() if s in ure)
        return r[len(r) // 2] if r else None


def test_dvojnik_v_objavi_ni_tekmec():
    """31. 10. 2026 (praznik): objava LPP ima enake dvojnike (linija 2: 47
    skupin). Kandidatka 17:51 je imela dvojnika z isto zamudo in par po uri
    je bil dvoumen -- živa vožnja brez zamude na tabli."""
    ure = {"A": 64260, "B": 64380, "C": 64500}
    sk = _Sk({"x2": dict(ure), "x1": dict(ure), "y": {s: t + 1500 for s, t in ure.items()}})
    napovedi = {s: t + 160 for s, t in ure.items()}
    assert zive._po_uri(sk, napovedi, ["x1", "x2", "y"]) == ("x1", 160)
    # Je dvojnik zaseden (vozi ga avtobus pod svojim id-jem), je živa isti avtobus.
    assert zive._po_uri(sk, napovedi, ["x1", "x2", "y"], {"x2"}) == ("x2", 160)
    # Prava tekmica (druga ura) ostane tekmica.
    sk = _Sk({"x1": dict(ure), "z": {s: t + 120 for s, t in ure.items()}})
    assert zive._po_uri(sk, napovedi, ["x1", "z"]) is None
