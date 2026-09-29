"""IndexNow: pošlje le, kadar se nabor spremeni, in stanje zapiše le ob uspehu.

Neuspeh brez zapisa je bistven: prvi dan ključ ni preverjen (403
`SiteVerificationNotCompleted`), in če bi se stanje vseeno zapisalo, naslednja
objava ne bi poskusila znova.

    ./venv/bin/python -m pytest tests/test_indexnow.py -q
"""
from __future__ import annotations

from kajros import indexnow

A = ["https://kajros.app/", "https://kajros.app/vlak/ljubljana/maribor"]


def test_odtis_ne_gleda_vrstnega_reda():
    assert indexnow.odtis(A) == indexnow.odtis(list(reversed(A)))
    assert indexnow.odtis(A) != indexnow.odtis(A[:1])


def test_neuspeh_ne_zapise_stanja(tmp_path, monkeypatch):
    stanje = tmp_path / "stanje"
    monkeypatch.setattr(indexnow, "poslji", lambda n: [(403, "SiteVerificationNotCompleted")])
    assert indexnow.poslji_ce_spremenjeno(A, stanje).startswith("NI POSLANO")
    assert not stanje.exists()


def test_isti_nabor_se_ne_poslje_dvakrat(tmp_path, monkeypatch):
    stanje = tmp_path / "stanje"
    klici = []
    monkeypatch.setattr(indexnow, "poslji", lambda n: klici.append(n) or [(202, "")])
    indexnow.poslji_ce_spremenjeno(A, stanje)
    indexnow.poslji_ce_spremenjeno(list(reversed(A)), stanje)
    assert len(klici) == 1
