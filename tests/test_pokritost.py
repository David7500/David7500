"""Pokritost po prevozniku: koliko voženj, ki tečejo, ima lego in zamudo.

Presoja 31. 10. 2026: izpad prevoznika je bil neviden, dokler je pisal kdo drug.
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from kajros import collector, db, stats

TZ = ZoneInfo("Europe/Ljubljana")
DAN = "2026-10-30"
ZDAJ = datetime(2026, 10, 30, 12, 0, tzinfo=TZ).timestamp()


def _baza():
    c = db.connect(":memory:")
    db.init(c)
    c.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES('A', 'A', 46, 14), ('B', 'B', 46.1, 14.1)")
    for tid, ag, od in (("a1", "1123", 11 * 3600), ("a2", "1123", 11 * 3600 + 1800),
                        ("a3", "1123", 11 * 3600 + 3300), ("l1", "lpp", 11 * 3600 + 1200)):
        c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, agency, network) "
                  "VALUES(?, 'r', ?, 's', 'bus', ?, 'avtobus')", (tid, tid, ag))
        c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)",
                      [(tid, 1, "A", None, od), (tid, 2, "B", od + 7200, None)])
    c.execute("INSERT INTO service_day(service_id, date) VALUES('s', ?)", (DAN,))
    db.fill_trip_window(c)
    c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_dep, feed_ts) "
              "VALUES('a1', ?, 1, 60, ?), ('l1', ?, 1, 0, ?)",
              (DAN, int(ZDAJ - 60), DAN, int(ZDAJ - 3600)))
    c.execute("INSERT INTO vehicle_now(trip_id, service_date, seen_ts, lat, lon) "
              "VALUES('a1', ?, ?, 46, 14), ('a2', ?, ?, 46, 14)", (DAN, int(ZDAJ - 30), DAN, int(ZDAJ - 30)))
    return c


def test_pokritost_steje_voznje_ki_tecejo():
    c = _baza()
    p = collector.pokritost(c, ZDAJ)
    # a3 je odpeljala pred 5 min: še ne šteje. l1 ima staro zamudo, brez lege.
    assert p == {"1123": [2, 2, 1, 1], "lpp": [1, 0, 0, 1]}
    assert stats.polnoc(DAN) < ZDAJ


def test_pokritost_v_tabelo_na_pet_minut():
    c = _baza()
    collector._POKRITOST[0] = 0.0
    collector._zapisi_pokritost(c, ZDAJ)
    collector._zapisi_pokritost(c, ZDAJ + 60)                      # prezgodaj
    assert c.execute("SELECT COUNT(*) FROM pokritost").fetchone()[0] == 2
    collector._zapisi_pokritost(c, ZDAJ + collector.POKRITOST_S)
    assert c.execute("SELECT COUNT(DISTINCT ts) FROM pokritost").fetchone()[0] == 2
