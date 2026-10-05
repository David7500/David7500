"""Zapore tira iz besedila obvestil SŽ in vlak pred tabo (`zapore.py`)."""
from datetime import date, datetime, timedelta

import pytest

from kajros import db, stats, zapore

Z, K = date(2026, 9, 19), date(2026, 10, 8)


def _dnevi(z):
    return sorted({o[0] for o in z["okna"]})


def test_zagorje_sava_dnevi_in_ura():
    z, = zapore.razberi(
        "Na progi Zagorje - Sava (19. - 20. in 26. ter 27. september in 1., 2. ter "
        "5. - 8. oktober, 7.00 - 13.30) poteka občasna zapora enega tira.", Z, K)
    assert z["odseki"] == [("Zagorje", "Sava")]
    assert [d.strftime("%d.%m") for d in _dnevi(z)] == [
        "19.09", "20.09", "26.09", "27.09", "01.10", "02.10",
        "05.10", "06.10", "07.10", "08.10"]
    assert {(o[1], o[2]) for o in z["okna"]} == {(420, 810)}


def test_vec_odsekov_vsak_s_svojimi_dnevi():
    zz = zapore.razberi(
        "Na progi Logatec - Rakek (16. september, 7.00 - 15.00) in Rakek - Postojna "
        "(24. - 25. september, 7.00 - 14.00) poteka občasna zapora.",
        date(2026, 9, 16), date(2026, 9, 25))
    assert [(z["odseki"], [d.day for d in _dnevi(z)]) for z in zz] == [
        ([("Logatec", "Rakek")], [16]), ([("Rakek", "Postojna")], [24, 25])]


def test_neprekinjeno_je_ves_dan():
    z, = zapore.razberi(
        "Na progi Prestranek - Postojna (28. september - 4. oktober, neprekinjeno do "
        "18.00 ter 5. oktober 7.00 - 15.00) poteka zapora enega tira.",
        date(2026, 9, 28), date(2026, 10, 5))
    okna = {o[0].strftime("%d.%m"): (o[1], o[2]) for o in z["okna"]}
    assert okna["28.09"] == (0, 1440) and okna["04.10"] == (0, 1440)
    assert okna["05.10"] == (420, 900)


def test_veriga_postaj_in_stevilcni_mesec():
    z, = zapore.razberi(
        "Ponikva – Dolga Gora – Poljčane (  17. 10. od 6.00 do 15.40  ) zapora tira",
        date(2026, 10, 17), date(2026, 10, 21))
    assert z["odseki"] == [("Ponikva", "Dolga Gora"), ("Dolga Gora", "Poljčane")]
    assert [(o[0].day, o[0].month, o[1], o[2]) for o in z["okna"]] == [(17, 10, 360, 940)]


def test_pika_za_imenom_postaje():
    z, = zapore.razberi(
        "Na progi Hrastnik - Zidani Most. (19. - 21. oktober, 7.00 - 13.00) poteka zapora.",
        date(2026, 10, 19), date(2026, 10, 21))
    assert z["odseki"] == [("Hrastnik", "Zidani Most")]


def test_odseki_v_oklepaju_se_ne_ugibajo():
    """Napačna zapora je slabša od nobene."""
    assert zapore.razberi(
        "Na progi Kresnice - Sava (26. – 27. 8. Kresnice – Laze 7:00 – 13.30. in "
        "28. 8. Litija – Kresnice 7.00 – 13.30) poteka zapora.",
        date(2026, 8, 26), date(2026, 9, 2)) == []


# ---------------------------------------------------------------- na progi
#
# A - B - C - D na eni progi. Zapora B - C danes 7.00 - 13.30.

DAN = date.today().isoformat()


def _ts(s):
    return stats.polnoc(DAN) + s


@pytest.fixture()
def conn():
    c = db.connect(":memory:")
    db.init(c)
    for sid, ime in (("a", "Ajdovo"), ("b", "Brezje"), ("c", "Cerkno"), ("d", "Dol")):
        c.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,46,14)", (sid, ime))
    for x, y in (("a", "b"), ("b", "c"), ("c", "d")):
        c.execute("INSERT INTO edge(from_id, to_id, km, elementary, trips, geojson) "
                  "VALUES(?,?,5,1,1,'{}')", (x, y))
    c.execute("INSERT INTO service_day(service_id, date) VALUES('S', ?)", (DAN,))
    for tid, no, postanki in (
            ("t1", "LP 1", "abcd"), ("t2", "LP 3", "abcd"), ("t9", "LP 2", "dcba"),
            ("ic", "IC 5", "ad")):
        c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
                  "VALUES(?,?,?,'',?)", (tid, tid, no, "S"))
        zacetek = {"t1": 8 * 3600, "t2": 8 * 3600 + 1800, "t9": 9 * 3600, "ic": 8 * 3600}[tid]
        c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) "
                      "VALUES(?,?,?,?,?)",
                      [(tid, i + 1, s, zacetek + i * 600, zacetek + i * 600)
                       for i, s in enumerate(postanki)])
    zac = datetime(*map(int, DAN.split("-")), tzinfo=zapore.TZ)
    c.execute("INSERT INTO alert(alert_id, kind, lang, start_ts, end_ts, header, description, "
              "first_seen, last_seen) VALUES('SZ-OVIRA-1','ovira','sl',?,?,'zapora',?,0,0)",
              (int(zac.timestamp()), int((zac + timedelta(days=1)).timestamp()),
               f"Na progi Brezje - Cerkno ({zac.day}. {zac.month}., 7.00 - 13.30) "
               "poteka občasna zapora enega tira na dvotirni progi."))
    c.commit()
    return c


def test_zapora_na_poti_v_oknu(conn):
    o = zapore.za_voznjo(conn, "t1", DAN, None, None, 0, _ts(7 * 3600))
    assert [(x["vrsta"], x["odsek"], x["do_ure"]) for x in o] == [
        ("zapora", "Brezje – Cerkno", "13.30")]


def test_zapora_tudi_za_hitri_vlak_brez_postanka_na_odseku(conn):
    """IC ustavi samo na A in D -- odsek B - C prevozi vmes."""
    assert zapore.za_voznjo(conn, "ic", DAN, None, None, 0, _ts(7 * 3600))


def test_zapora_ne_velja_zunaj_ure(conn):
    assert zapore.za_voznjo(conn, "t1", DAN, None, None, 6 * 3600, _ts(7 * 3600)) == []


def test_zapora_ne_velja_za_odseke_za_vlakom(conn):
    """Vlak je že v C: zapora B - C je za njim."""
    assert zapore.za_voznjo(conn, "t1", DAN, 3, None, 0, _ts(7 * 3600)) == []


def test_vlak_pred_tabo_v_isti_smeri(conn):
    conn.execute("DELETE FROM alert")
    # t1 je med B (08:10) in C (08:20) izgubil 15 min: C ob 08:35.
    zdaj = _ts(8 * 3600 + 40 * 60)
    conn.executemany(
        "INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
        "VALUES('t1', ?, ?, ?, ?, ?)",
        [(DAN, 2, 0, 0, zdaj), (DAN, 3, 900, 900, zdaj)])
    conn.commit()
    o = zapore.za_voznjo(conn, "t2", DAN, None, None, 0, zdaj)
    assert [(x["vrsta"], x["vlak"], x["izguba_s"], x["odsek"], x["od_seq"]) for x in o] == [
        ("pred_tabo", "LP 1", 900, "Brezje – Cerkno", 3)]
    assert zapore.dodatek(o, 3) == 900
    # nasprotna smer ga ne zadeva
    assert zapore.za_voznjo(conn, "t9", DAN, None, None, 0, zdaj) == []
    # uro pozneje ni več novica
    assert zapore.za_voznjo(conn, "t2", DAN, None, None, 0, zdaj + 3700) == []


def test_tveganje_iz_prejsnjih_dni_zapore(conn, monkeypatch):
    monkeypatch.setattr(zapore, "NAJMANJ_PREHODOV", 1)
    vceraj = (date.today() - timedelta(days=1))
    conn.execute("INSERT INTO service_day(service_id, date) VALUES('S', ?)", (vceraj.isoformat(),))
    conn.executemany(
        "INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
        "VALUES(?, ?, ?, ?, ?, 0)",
        [("t1", vceraj.isoformat(), 2, 0, 0), ("t1", vceraj.isoformat(), 3, 720, 720),
         ("t2", vceraj.isoformat(), 2, 60, 60), ("t2", vceraj.isoformat(), 3, 60, 60)])
    zac = datetime(vceraj.year, vceraj.month, vceraj.day, tzinfo=zapore.TZ)
    conn.execute("UPDATE alert SET start_ts = ?, description = ?",
                 (int(zac.timestamp()),
                  f"Na progi Brezje - Cerkno ({vceraj.day}. {vceraj.month}. in "
                  f"{date.today().day}. {date.today().month}., 7.00 - 13.30) zapora tira."))
    conn.commit()
    o, = zapore.za_voznjo(conn, "t1", DAN, None, None, 0, _ts(7 * 3600))
    assert o["tveganje"] == {"dni": 1, "prehodov": 2, "izgubilo": 1,
                             "najmanj_s": 720, "najvec_s": 720, "p90_s": 648}
    # Zgornja meja velja od konca zaprtega odseka naprej (C), ne prej.
    assert o["od_seq"] == 3
    assert [zapore.dodatek([o], seq) for seq in (2, 3, 4)] == [0, 648, 648]
    # Tabla: ocena ostane, zraven zgornja meja.
    vrstica = {"trip_id": "t1", "network": "zeleznica", "stop_seq": 4, "delay_s": 120}
    zapore.dopolni(conn, [vrstica], DAN, "stop_seq", "stop_seq",
                   datetime.fromtimestamp(_ts(7 * 3600), zapore.TZ))
    assert (vrstica["delay_s"], vrstica["do_s"]) == (120, 120 + 648)


def test_ogrevanje_najde_danasnjo_zaporo(conn):
    assert zapore.ogrej(conn, DAN) == 1
