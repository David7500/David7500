"""Testi povezave s Ko-fi.

Pot piše v bazo iz zahteve tujega strežnika, zato se tu varuje, kaj sme
kdo, ki žetona ne pozna (nič), in da ponovljeno sporočilo ne šteje dvakrat.

    ./venv/bin/python -m pytest tests/test_donacije.py -q
"""
from __future__ import annotations

import json
from urllib.parse import urlencode

import pytest

from kajros import db, donacije

ZETON = "ab12-cd34"


@pytest.fixture()
def conn():
    c = db.connect(":memory:")
    donacije.init(c)
    yield c
    c.close()


@pytest.fixture(autouse=True)
def _cist_pomnilnik():
    donacije.zavrnjeno.update(ts=None, razlog="")
    yield


def _telo(**kw) -> str:
    """Kot pošlje Ko-fi: obrazec z enim poljem `data`, v njem JSON."""
    podatki = {
        "verification_token": ZETON,
        "message_id": "3a1fac0c-f960-4506-a60e-2e3f3d09e6e0",
        "timestamp": "2026-10-20T13:04:30Z",
        "type": "Donation",
        "is_public": True,
        "from_name": "Ana",
        "message": "Hvala za vlake!",
        "amount": "5.00",
        "url": "https://ko-fi.com/Home/CoffeeShop?txid=x",
        "email": "ana@primer.si",
        "currency": "EUR",
        "is_subscription_payment": False,
        "is_first_subscription_payment": False,
        "kofi_transaction_id": "c0ffee00-0000-4000-8000-000000000001",
        "shop_items": None,
        "tier_name": None,
        "shipping": None,
    }
    podatki.update(kw)
    return urlencode({"data": json.dumps(podatki)})


def _sprejmi(conn, **kw) -> str:
    return donacije.sprejmi(conn, donacije.razberi(_telo(**kw), ZETON))


# ---------------------------------------------------------- kdo sme pisati

@pytest.mark.parametrize("telo", [
    "",
    "data=",
    "data=ni-json",
    urlencode({"data": "[1, 2]"}),          # veljaven JSON, a ne predmet
    urlencode({"data": json.dumps({"amount": "5.00"})}),
    _telo(verification_token="napacen"),
    _telo(verification_token=None),
    _telo(verification_token="žeton-s-šumniki"),  # compare_digest ne mara ne-ASCII nizov
])
def test_brez_pravega_zetona_ni_nic(conn, telo):
    with pytest.raises(donacije.Zavrnjeno):
        donacije.razberi(telo, ZETON)
    assert donacije.zavrnjeno["ts"] is not None
    assert conn.execute("SELECT COUNT(*) FROM donacija").fetchone()[0] == 0


def test_brez_nastavljenega_zetona_ne_sprejme_niti_praznega(conn):
    """Prazen pričakovani žeton bi se ujel s praznim v sporočilu."""
    with pytest.raises(donacije.Zavrnjeno):
        donacije.razberi(_telo(verification_token=""), "")


def test_osebni_podatki_niso_v_shemi(conn):
    """Ime, e-naslov in sporočilo darovalca pridejo, a ne ostanejo.

    Kdor bo kdaj dodal stolpec zanje, naj tu pade in premisli, kaj pove
    stran o zasebnosti.
    """
    _sprejmi(conn)
    stolpci = {r[1] for r in conn.execute("PRAGMA table_info(donacija)")}
    assert stolpci == {"id", "placano", "prejeto", "vrsta", "centi", "valuta", "preizkus"}
    vrstica = " ".join(map(str, conn.execute("SELECT * FROM donacija").fetchone()))
    for osebno in ("Ana", "ana@primer.si", "Hvala"):
        assert osebno not in vrstica


# ------------------------------------------------------------------ zapis

def test_placilo_se_zapise_v_centih(conn):
    assert _sprejmi(conn, amount="3.50") == "nova"
    r = conn.execute("SELECT * FROM donacija").fetchone()
    assert (r["centi"], r["valuta"], r["vrsta"], r["preizkus"]) == (350, "EUR", "Donation", 0)
    assert r["placano"] == 1792501470            # 2026-10-20T13:04:30Z


def test_ponovljeno_sporocilo_ne_steje_dvakrat(conn):
    """Ko-fi pošiljanje ponovi, kadar ne dobi 200 -- isto plačilo je eno."""
    assert _sprejmi(conn) == "nova"
    assert _sprejmi(conn) == "ponovljena"
    p = donacije.pregled(conn)
    assert p["valute"] == [{"valuta": "EUR", "centi": 500, "stevilo": 1}]


def test_vsak_mesec_narocnine_je_svoje_placilo(conn):
    _sprejmi(conn, type="Subscription", kofi_transaction_id="t-1")
    _sprejmi(conn, type="Subscription", kofi_transaction_id="t-2")
    assert donacije.pregled(conn)["valute"][0]["centi"] == 1000


@pytest.mark.parametrize("znesek", ["0.00", "-5", "abc", "NaN", "Infinity", "1e9", None, ""])
def test_znesek_brez_smisla_se_prezre(conn, znesek):
    assert _sprejmi(conn, amount=znesek) == "prezrto"
    assert donacije.pregled(conn)["valute"] == []


def test_neberljiv_cas_vzame_cas_prejema(conn):
    donacije.sprejmi(conn, donacije.razberi(_telo(timestamp="včeraj"), ZETON), zdaj=1_800_000_000)
    assert conn.execute("SELECT placano FROM donacija").fetchone()[0] == 1_800_000_000


def test_valute_se_ne_sestevajo(conn):
    """Tečaj bi bil nov vir; vsota v napačni valuti bi bila laž."""
    _sprejmi(conn, kofi_transaction_id="a", amount="5.00", currency="EUR")
    _sprejmi(conn, kofi_transaction_id="b", amount="5.00", currency="usd")
    assert sorted((v["valuta"], v["centi"]) for v in donacije.pregled(conn)["valute"]) == [
        ("EUR", 500), ("USD", 500)]


# ---------------------------------------------------------------- preizkus

def test_preizkus_ni_v_vsoti_a_se_vidi(conn):
    """Gumb za preizkus v Ko-fi pove, da povezava dela, ne prinese denarja."""
    assert _sprejmi(conn, kofi_transaction_id=donacije.PREIZKUS_ID) == "preizkus"
    donacije.sprejmi(conn, donacije.razberi(
        _telo(kofi_transaction_id=donacije.PREIZKUS_ID), ZETON), zdaj=2_000_000_000)
    p = donacije.pregled(conn)
    assert p["valute"] == [] and p["zadnja"] is None
    assert p["preizkus"] == 2_000_000_000        # drugi preizkus osveži čas


def test_naslov_na_example_com_je_preizkus(conn):
    assert _sprejmi(conn, email="jo.example@example.com") == "preizkus"
    assert donacije.pregled(conn)["valute"] == []


def test_zeton_iz_datoteke(tmp_path, monkeypatch):
    """Brez restarta: `deploy/kofi.sh` zapiše datoteko, naslednja zahteva jo vidi."""
    monkeypatch.delenv("KAJROS_KOFI_ZETON", raising=False)
    monkeypatch.delenv("SZ_KOFI_ZETON", raising=False)
    monkeypatch.setattr(donacije.config, "DATA_DIR", tmp_path)
    assert donacije.zeton() == ""
    (tmp_path / ".kofi-zeton").write_text(ZETON + "\n", encoding="utf-8")
    assert donacije.zeton() == ZETON
