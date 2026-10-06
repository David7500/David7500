"""Predogled povezave na okno vožnje: stanje ob pošiljanju (`api._stanje_za_predogled`)."""
from kajros import api, stats

DAN = "2026-10-06"


def _stanje(monkeypatch, zadnji):
    monkeypatch.setattr(stats, "resolve_trip", lambda *a: "t1")
    monkeypatch.setattr(stats, "last_measured", lambda *a: {"t1": zadnji} if zadnji else {})
    return api._stanje_za_predogled(None, "RG 318", None, DAN)


def test_zamuja_z_imenom_in_uro(monkeypatch):
    t = _stanje(monkeypatch, {"delay_s": 23 * 60 + 20, "t_s": 6 * 3600 + 47 * 60,
                              "name": "Trbovlje"})
    assert t == "Zamuja 23 min (zadnji podatek s postaje Trbovlje ob 07:10)."


def test_tocno_in_prej_po_zaokrozeni_minuti(monkeypatch):
    """Ista minuta kot na zaslonu (`Math.round`, ne bančno): 29 s je točno,
    -90 s je 1 min prej, -91 s 2 min."""
    t = _stanje(monkeypatch, {"delay_s": 29, "t_s": 8 * 3600, "name": "Celje"})
    assert t.startswith("Vozi točno")
    t = _stanje(monkeypatch, {"delay_s": -90, "t_s": 8 * 3600, "name": "Celje"})
    assert t.startswith("Vozi 1 min prej")
    t = _stanje(monkeypatch, {"delay_s": -91, "t_s": 8 * 3600, "name": "Celje"})
    assert t.startswith("Vozi 2 min prej")


def test_brez_meritve_ni_stanja(monkeypatch):
    assert _stanje(monkeypatch, None) is None
    assert _stanje(monkeypatch, {"delay_s": None, "t_s": 0, "name": "X"}) is None
