"""Ovire s strani SŽ: razbor, enako besedilo kot pri derp.si, vezi, vodenje.

    ./venv/bin/python -m pytest tests/test_ovire_sz.py -q
"""
from __future__ import annotations

import json
from datetime import datetime

import pytest
from google.transit import gtfs_realtime_pb2

from kajros import alerts, db, ovire_sz

# Oblika z 11. 10. 2026: vzporedni seznami po kraju, opis s prelomi in HTML.
SKUPINE = [
    {"Naslov": ["OBVESTILO: Združeni vlaki iz/do Zidanega Mosta (do nadaljnjega). "],
     "Cas": ["14.12.2025-12.12.2026"], "Lokacija": "42200",
     "Relacija": ["Maribor / Dobova / Zidani Most - Ljubljana"],
     "Opis": ["\n<strong>ZIDANI MOST - LJUBLJANA:</strong>\n\nGarnitura vlaka RG 619 "
              "se v Zidanem Mostu združi.\r\n<a href=\"https://potniski.sz.si/info\">več</a>"],
     "ID_vrste": ["1"], "ID_ovire": ["9471"], "Sort": ["3"], "Vrsta": ["Izpad vlaka"]},
    {"Naslov": ["Dela na progi", "Postaja Kranj"], "Cas": ["5.9.2026-7.9.2026", "11.10.2026"],
     "Lokacija": "43100", "Relacija": ["Ljubljana - Kranj", "Kranj"],
     "Opis": ["Zapora tira.", "Blagajna zaprta."],
     "ID_vrste": ["3", "99"], "ID_ovire": ["11058", "11059"], "Sort": ["4", "4"],
     "Vrsta": ["Dela na progi", "Neznano"]},
]
HTML = ("<script id=\"_general-js-extra\"> var locations = [{\"st\":\"42001\"}];\n"
        f"var roadworks = {json.dumps(SKUPINE)};\n//# sourceURL=_general-js-extra\n</script>")


@pytest.fixture(autouse=True)
def _cist_spomin(monkeypatch):
    alerts._ovire_sz_ts = 0.0
    monkeypatch.setattr(ovire_sz.brskalnik, "zahtevaj",
                        lambda pot: pytest.fail("potniski.sz.si brez nadomestka"))
    yield
    alerts._ovire_sz_ts = 0.0


def _baza():
    c = db.connect(":memory:")
    db.init(c)
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
                  [("LJ", "Ljubljana", 46.05, 14.51), ("ZM", "Zidani Most", 46.08, 15.17),
                   ("MB", "Maribor", 46.56, 15.66), ("KR", "Kranj", 46.24, 14.36),
                   ("KR2", "Kranj", 46.24, 14.36)])
    for tid, rid, mode, postaje in (("t1", "r1", "vlak", ["LJ", "ZM", "MB"]),
                                    ("t2", "r2", "vlak", ["LJ", "KR"]),
                                    ("t3", "r3", "vlak", ["ZM", "MB"]),
                                    ("t4", "r4", "bus", ["LJ", "ZM"])):
        c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, agency, "
                  "network) VALUES(?, ?, ?, 's1', ?, '1161', 'zeleznica')",
                  (tid, rid, tid.upper(), mode))
        c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) "
                      "VALUES(?,?,?,?,?)",
                      [(tid, i + 1, s, 3600 * (6 + i), 3600 * (6 + i)) for i, s in enumerate(postaje)])
    c.commit()
    return c


def test_seznam_iz_strani_in_brez_njega_napaka():
    assert [g["ID_ovire"] for g in ovire_sz.seznam(HTML)] == [["9471"], ["11058", "11059"]]
    assert ovire_sz.seznam("<script>var roadworks = [];</script>") == []
    with pytest.raises(RuntimeError, match="nima seznama"):
        ovire_sz.seznam("<html>Just a moment</html>")


def test_besedilo_in_veljavnost_kot_pri_derp():
    """Isti alert_id, besedilo in obdobje kot `szService.js`: ob menjavi vira
    se ne sme spremeniti nič, `zapore.py` bere besedilo."""
    o = {x["alert_id"]: x for x in ovire_sz.razberi(SKUPINE)}
    a = o["SZ-OVIRA-9471"]
    assert a["header"] == "OBVESTILO: Združeni vlaki iz/do Zidanega Mosta (do nadaljnjega)."
    assert a["description"] == ("ZIDANI MOST - LJUBLJANA:  Garnitura vlaka RG 619 se v "
                                "Zidanem Mostu združi.  več")
    assert datetime.fromtimestamp(a["start_ts"], ovire_sz.TZ).isoformat() == "2025-12-14T00:00:00+01:00"
    assert datetime.fromtimestamp(a["end_ts"], ovire_sz.TZ).isoformat() == "2026-12-12T23:59:59+01:00"
    rt = gtfs_realtime_pb2.Alert
    assert (a["cause"], a["effect"]) == (rt.TECHNICAL_PROBLEM, rt.MODIFIED_SERVICE)
    assert (o["SZ-OVIRA-11058"]["cause"], o["SZ-OVIRA-11058"]["effect"]) == (
        rt.MAINTENANCE, rt.MODIFIED_SERVICE)
    # Neznana vrsta in en sam dan: brez konca, kot pri derp.si.
    b = o["SZ-OVIRA-11059"]
    assert (b["cause"], b["effect"]) == (rt.UNKNOWN_CAUSE, rt.UNKNOWN_EFFECT)
    assert b["start_ts"] and b["end_ts"] is None


def test_vezi_proge_z_vsaj_dvema_postajama():
    c = _baza()
    poti, postaje = ovire_sz.proge(c)
    assert "r4" not in poti, "nadomestni avtobus ni vlak"
    # Maribor / Dobova / Zidani Most - Ljubljana: r1 (tri), r3 (dve); r2 ima le Ljubljano.
    assert ovire_sz.vezi("Maribor / Dobova / Zidani Most - Ljubljana", poti, postaje) == {
        ("r1", "", ""), ("r3", "", "")}
    # Brez „ - “ so naštete postaje, samo postajališča vlakov (KR2 ni).
    assert ovire_sz.vezi("Kranj", poti, postaje) == {("", "", "KR")}
    assert ovire_sz.vezi("Slovenija", poti, postaje) == set()


def test_zapis_imen_kot_ga_pise_sz():
    """11. 10. 2026: „Zidani Most -Hrastnik“ (zapora, 58 vlakov) in „Lesce
    Bled“ za postajo, ki je v voznem redu „Lesce-Bled“ -- derp.si obema 0."""
    poti = {"r1": {ovire_sz._kljuc(x) for x in ("Zidani Most", "Hrastnik", "Lesce-Bled")}}
    assert ovire_sz.vezi("Zidani Most -Hrastnik", poti, {}) == {("r1", "", "")}
    assert ovire_sz.vezi("Lesce Bled - Hrastnik", poti, {}) == {("r1", "", "")}
    # Vezaj brez presledkov je del imena, ne ločilo.
    assert ovire_sz.vezi("Lesce-Bled", poti, {"lescebled": {"LB"}}) == {("", "", "LB")}


def test_zapis_in_osvezene_vezi():
    """Vezi se računajo ob vsakem branju: derp.si jih je zapisal enkrat, ob
    prvem pogledu -- ovira, prvič vidna 28. 9. 2026 (zip brez vlakov), je
    ostala brez vlakov do 11. 10."""
    c = _baza()
    s = ovire_sz.korak(c, HTML, 1_790_000_000)
    assert (s["ovir"], s["novih"], s["brez_vezi"]) == (3, 3, 0)
    assert json.loads(db.get_meta(c, "ovire_sz"))["ts"] == 1_790_000_000
    assert {r[0] for r in c.execute(
        "SELECT route_id FROM alert_entity WHERE alert_id = 'SZ-OVIRA-11058'")} == {"r2"}
    # Nova proga Ljubljana - Kranj v voznem redu: vez se doda, ovira ni nova.
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, agency, network) "
              "VALUES('t5', 'r5', 'T5', 's1', 'vlak', '1161', 'zeleznica')")
    c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)",
                  [("t5", 1, "KR", 3600, 3600), ("t5", 2, "LJ", 7200, 7200)])
    s = ovire_sz.korak(c, HTML, 1_790_000_300)
    assert (s["novih"], s["vezi_spremenjenih"]) == (0, 1)
    assert {r[0] for r in c.execute(
        "SELECT route_id FROM alert_entity WHERE alert_id = 'SZ-OVIRA-11058'")} == {"r2", "r5"}
    r = c.execute("SELECT kind, lang, url, first_seen, last_seen FROM alert "
                  "WHERE alert_id = 'SZ-OVIRA-9471'").fetchone()
    assert tuple(r) == ("ovira", "sl", ovire_sz.URL, 1_790_000_000, 1_790_000_300)


def _feed_ovir():
    f = gtfs_realtime_pb2.FeedMessage()
    f.header.gtfs_realtime_version = "2.0"
    for oid, lang in (("9471", "sl"), ("9472", "en")):
        e = f.entity.add(id=f"SZ-OVIRA-{oid}")
        e.alert.header_text.translation.add(text=f"derp {oid}", language=lang)
        e.alert.informed_entity.add(route_id="r2")
    return f


def test_derp_pise_slovenske_ovire_le_ob_molku_strani():
    c = _baza()
    alerts.ovire_sz_prebrane()
    izid = alerts.ingest(c, _feed_ovir())
    assert izid["ovir_vodi_sz"] == 1
    assert [r[0] for r in c.execute("SELECT alert_id FROM alert")] == ["SZ-OVIRA-9472"]
    # Stran tri obhode neprebrana: derp.si spet piše vse.
    alerts._ovire_sz_ts -= alerts.OVIRE_VODI_OBHODOV * ovire_sz.config.OVIRE_SZ_SECONDS + 1
    assert "ovir_vodi_sz" not in alerts.ingest(c, _feed_ovir())
    assert c.execute("SELECT header FROM alert WHERE alert_id = 'SZ-OVIRA-9471'"
                     ).fetchone()[0] == "derp 9471"
