"""Obvestila skrbnika potnikom: rok, omrežje, umik in pot od pregleda do strani.

    ./venv/bin/python -m pytest tests/test_obvestila.py -q
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from kajros import api, db, obvestila

# 28. 9. 2026 ob 10:00 po slovensko (UTC+2).
ZDAJ = int(datetime(2026, 9, 28, 8, 0, tzinfo=timezone.utc).timestamp())


@pytest.fixture()
def conn():
    c = db.connect(":memory:")
    db.init(c)
    yield c
    c.close()


def test_rok_je_slovenska_ura():
    """`datetime-local` pošlje uro brez območja. Kot UTC bi obvestilo
    „do 3:00“ poteklo ob petih zjutraj."""
    assert obvestila.rok("2026-09-29T03:00", ZDAJ) == int(
        datetime(2026, 9, 29, 1, 0, tzinfo=timezone.utc).timestamp())


@pytest.mark.parametrize("niz", ["2026-09-28T09:00", "2026-11-28T10:00", "jutri", ""])
def test_rok_mimo_predalec_ali_ne_datum_se_zavrne(niz):
    with pytest.raises(obvestila.Zavrnjeno):
        obvestila.rok(niz, ZDAJ)


@pytest.mark.parametrize("besedilo, omrezje", [
    ("  ok  ", None), ("x" * (obvestila.NAJDALJSE + 1), None), ("Vlaki danes brez zamud.", "tramvaj"),
])
def test_neveljavno_obvestilo_se_zavrne(conn, besedilo, omrezje):
    with pytest.raises(obvestila.Zavrnjeno):
        obvestila.objavi(conn, besedilo, omrezje, ZDAJ + 3600, zdaj=ZDAJ)


def test_omrezje_izbere_strani(conn):
    """Obvestilo brez omrežja gre povsod; vlakovno ne na avtobusno stran.
    `vse` (domača, zemljevid, pot) dobi vsa, najnovejše prvo."""
    vsem = obvestila.objavi(conn, "Zamude danes zamujajo.", "", ZDAJ + 3600, zdaj=ZDAJ - 30)
    vlaki = obvestila.objavi(conn, "Vlakov ni v voznem redu.", "zeleznica", ZDAJ + 3600, zdaj=ZDAJ - 20)
    bus = obvestila.objavi(conn, "Trase avtobusov so pomešane.", "avtobus", ZDAJ + 3600, zdaj=ZDAJ - 10)
    vsa = obvestila.veljavna(conn, ZDAJ)
    assert [o["id"] for o in obvestila.za_omrezje(vsa, "zeleznica", ZDAJ)] == [vlaki, vsem]
    assert [o["id"] for o in obvestila.za_omrezje(vsa, "avtobus", ZDAJ)] == [bus, vsem]
    assert [o["id"] for o in obvestila.za_omrezje(vsa, "vse", ZDAJ)] == [bus, vlaki, vsem]


def test_poteklo_v_predpomnjenem_seznamu_se_ne_pokaze(conn):
    """Seznam je predpomnjen do minute; rok se zato preveri še ob strežbi."""
    obvestila.objavi(conn, "Samo še pol ure.", None, ZDAJ + 1800, zdaj=ZDAJ)
    vsa = obvestila.veljavna(conn, ZDAJ)
    assert obvestila.za_omrezje(vsa, "vse", ZDAJ + 1799)
    assert obvestila.za_omrezje(vsa, "vse", ZDAJ + 1800) == []


def test_umaknjeno_izgine_s_strani_a_ostane_v_pregledu(conn):
    """Kaj je bilo potnikom rečeno in do kdaj, se ve tudi po umiku."""
    id_ = obvestila.objavi(conn, "Vlakov ni v voznem redu.", None, ZDAJ + 3600, zdaj=ZDAJ)
    assert obvestila.umakni(conn, id_, zdaj=ZDAJ + 60)
    assert obvestila.veljavna(conn, ZDAJ + 61) == []
    (v,) = obvestila.seznam(conn, zdaj=ZDAJ + 61)
    assert v["id"] == id_ and v["velja"] is False
    assert not obvestila.umakni(conn, id_, zdaj=ZDAJ + 120), "umaknjeno se ne umakne znova"
    assert obvestila.izbrisi(conn, id_) and obvestila.seznam(conn) == []


def test_objava_iz_pregleda_je_takoj_na_strani(conn, monkeypatch):
    """Predpomnilnik ne sme zadržati novega obvestila do izteka minute."""
    monkeypatch.setattr(api, "_conn", lambda: conn)
    api._ODGOVORI.pop("obvestila", None)
    assert api.api_obvestila("zeleznica") == {"obvestila": []}

    cez_dve_uri = datetime.fromtimestamp(time.time() + 7200, obvestila.TZ)
    izid = api._admin_obvestila({
        "akcija": ["objavi"], "besedilo": ["Vozni red avtobusov je danes pomanjkljiv."],
        "omrezje": ["avtobus"],
        "do": [cez_dve_uri.replace(tzinfo=None).isoformat(timespec="minutes")]})
    assert api.api_obvestila("zeleznica") == {"obvestila": []}
    (o,) = api.api_obvestila("avtobus")["obvestila"]
    assert o["id"] == izid["id"] and set(o) == {"id", "besedilo", "omrezje", "objavljeno", "velja_do"}

    api._admin_obvestila({"akcija": ["umakni"], "id": [str(izid["id"])]})
    assert api.api_obvestila("vse") == {"obvestila": []}


def test_napaka_obrazca_je_422_z_razlogom(conn, monkeypatch):
    monkeypatch.setattr(api, "_conn", lambda: conn)
    with pytest.raises(HTTPException) as exc:
        api._admin_obvestila({"akcija": ["objavi"], "besedilo": ["kratko ok"],
                              "do": ["2020-01-01T00:00"]})
    assert exc.value.status_code == 422 and "mimo" in exc.value.detail
