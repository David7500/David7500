"""Ura namesto zamude: feed drži vozilo na vožnji, ki je ne vozi.

31. 10. 2026 LPP 2 ob 16:43 na Gornjem trgu +66 min, vozilo pri garaži.
"""
from __future__ import annotations

import pytest

from kajros import collector, db


@pytest.fixture(autouse=True)
def _vodi(monkeypatch):
    """Preizkus pravila samega: kot da varovalo vodi (privzeto je v senci)."""
    monkeypatch.setattr(collector.config, "DRSI", "vodi")

T = 1_793_460_000.0


def _baza():
    c = db.connect(":memory:")
    db.init(c)
    c.executemany("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
                  "VALUES('t', '2026-10-31', ?, NULL, ?, ?)",
                  [(2, 60, int(T - 600)), (3, 120, int(T + 200)), (4, 300, int(T + 600))])
    return c


def test_zamuda_ki_raste_z_uro_po_15_min_ne_gre_v_run():
    collector._DRSI.clear()
    collector.FANTOMI.clear()
    c = _baza()
    # Vsakih 90 s zamuda zadnjega postanka zraste za 90 s (en paket 60, drug 120).
    zamude = [100 + 90 * i + (30 if i % 2 else -30) for i in range(12)]
    izidi = [collector.ura_namesto_zamude(c, "t", "2026-10-31", 29, z, T + 90 * i)
             for i, z in enumerate(zamude)]
    assert not any(izidi[:10]) and izidi[10] and izidi[11]
    assert ("t", "2026-10-31") in collector.FANTOMI
    # Kar je bilo zapisano med drsenjem, je pobrisano; prej zapisano ostane.
    assert [r[0] for r in c.execute("SELECT stop_seq FROM run ORDER BY stop_seq")] == [2]


def test_vozilo_ki_vozi_ali_stoji_kratko_ni_fantom():
    collector._DRSI.clear()
    c = _baza()
    # Zastoj 10 min (raste z uro), nato vozi in zamuda pade.
    zamude = [300 + 60 * i for i in range(10)] + [800, 760, 700, 700, 690, 690, 690]
    izidi = [collector.ura_namesto_zamude(c, "t", "2026-10-31", 29, z, T + 60 * i)
             for i, z in enumerate(zamude)]
    assert not any(izidi)
    # Stalna zamuda ni drsenje.
    assert not any(collector.ura_namesto_zamude(c, "u", "2026-10-31", 29, 420, T + 60 * i)
                   for i in range(30))


def test_v_senci_samo_steje(monkeypatch):
    monkeypatch.setattr(collector.config, "DRSI", "senca")
    collector._DRSI.clear()
    collector.FANTOMI.clear()
    c = _baza()
    izidi = [collector.ura_namesto_zamude(c, "t", "2026-10-31", 5, 100 + 90 * i, T + 90 * i)
             for i in range(12)]
    assert not any(izidi) and ("t", "2026-10-31") in collector.FANTOMI
    assert c.execute("SELECT COUNT(*) FROM run").fetchone()[0] == 3
