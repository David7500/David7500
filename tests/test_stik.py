"""Testi obrazca za stik.

To je **edina pot v aplikaciji, ki piše v bazo iz zahteve**, zato tu ne
varujemo videza, ampak natanko to, kaj neznanec sme. Vsaka od varovalk je
tiha, kadar se pokvari: obrazec bi še naprej delal, le spam bi prišel skozi.

    ./venv/bin/python -m pytest tests/test_stik.py -q
"""
from __future__ import annotations

import time

import pytest

from kajros import db, stik


@pytest.fixture()
def conn():
    c = db.connect(":memory:")
    stik.init(c)
    yield c
    c.close()


@pytest.fixture(autouse=True)
def _cist_pomnilnik():
    """Omejitev pogostosti živi v modulu, zato jo med testi počistimo."""
    stik._poslana.clear()
    yield
    stik._poslana.clear()


def _poslji(conn, **kw):
    """Veljavno sporočilo z žetonom, ki je ravno dovolj star."""
    zdaj = time.time()
    priv = dict(email="ana@primer.si", besedilo="Na LPP 25 je zamuda napačna.",
                zeton_iz_obrazca=stik.zeton(zdaj - stik.NAJHITREJE_S - 1),
                vaba="", kljuc="kljuc-a", zdaj=zdaj)
    priv.update(kw)
    return stik.sprejmi(conn, **priv)


# ------------------------------------------------------------- veljavno

def test_veljavno_sporocilo_se_shrani(conn):
    id_ = _poslji(conn)
    assert id_ > 0
    vrstice = stik.seznam(conn)
    assert len(vrstice) == 1
    assert vrstice[0]["email"] == "ana@primer.si"
    assert vrstice[0]["prebrano"] == 0


def test_naslov_ip_ni_v_shemi(conn):
    """Najpomembnejši test tega modula.

    Kdor bo kdaj dodal stolpec za IP „samo za odkrivanje spama", naj tu
    pade. Omejevanje teče nad zgoščeno vrednostjo v pomnilniku in prav to
    je obljuba na strani o zasebnosti.
    """
    stolpci = {v[1] for v in conn.execute("PRAGMA table_info(sporocilo)")}
    assert stolpci == {"id", "prispelo", "email", "besedilo", "drzava",
                       "naprava", "prebrano"}


# --------------------------------------------------------------- vsebina

@pytest.mark.parametrize("email", ["", "ni-naslov", "brez@pike", "a@b",
                                   "a" * 250 + "@b.si"])
def test_slab_email_zavrnjen(conn, email):
    with pytest.raises(stik.Zavrnjeno):
        _poslji(conn, email=email)
    assert stik.seznam(conn) == []


def test_prekratko_in_predolgo(conn):
    with pytest.raises(stik.Zavrnjeno):
        _poslji(conn, besedilo="kratko")
    with pytest.raises(stik.Zavrnjeno):
        _poslji(conn, besedilo="x" * (stik.NAJDALJSE + 1))
    assert stik.seznam(conn) == []


def test_presledki_se_pospravijo(conn):
    _poslji(conn, email="  ana@primer.si  ",
            besedilo="   Zamuda je napačna.   ")
    v = stik.seznam(conn)[0]
    assert v["email"] == "ana@primer.si"
    assert v["besedilo"] == "Zamuda je napačna."


# ----------------------------------------------------------------- žeton

def test_prehitro_izpolnjen_obrazec(conn):
    """Človek ne napiše e-naslova in stavka v manj kot štirih sekundah."""
    zdaj = time.time()
    with pytest.raises(stik.Zavrnjeno):
        _poslji(conn, zeton_iz_obrazca=stik.zeton(zdaj), zdaj=zdaj)
    assert stik.seznam(conn) == []


def test_potekel_zeton(conn):
    zdaj = time.time()
    with pytest.raises(stik.Zavrnjeno):
        _poslji(conn, zeton_iz_obrazca=stik.zeton(zdaj - stik.NAJPOZNEJE_S - 1),
                zdaj=zdaj)


@pytest.mark.parametrize("z", ["", "brez-pike", "123.ponaredek",
                               "nicla.0" * 4])
def test_ponarejen_zeton(conn, z):
    with pytest.raises(stik.Zavrnjeno):
        _poslji(conn, zeton_iz_obrazca=z)
    assert stik.seznam(conn) == []


def test_podpis_je_vezan_na_cas(conn):
    """Podpis enega žetona ne sme veljati za drug čas izdaje."""
    zdaj = time.time()
    podpis = stik.zeton(zdaj - 100).partition(".")[2]
    with pytest.raises(stik.Zavrnjeno):
        _poslji(conn, zeton_iz_obrazca=f"{int(zdaj - 500)}.{podpis}", zdaj=zdaj)


# ------------------------------------------------------------------ vaba

def test_vaba_ne_shrani_in_ne_pove(conn):
    """Robot mora dobiti videz uspeha, sicer se nauči, česa ne izpolniti."""
    id_ = _poslji(conn, vaba="http://spam.primer")
    assert id_ == 0                      # ni izjeme in ni vrstice
    assert stik.seznam(conn) == []


def test_prazna_vaba_ne_ovira(conn):
    assert _poslji(conn, vaba="   ") > 0


# ------------------------------------------------------------ pogostost

def test_omejitev_na_uro(conn):
    zdaj = time.time()
    for i in range(stik.NA_URO):
        _poslji(conn, zdaj=zdaj + i,
                zeton_iz_obrazca=stik.zeton(zdaj - stik.NAJHITREJE_S - 1))
    with pytest.raises(stik.Zavrnjeno, match="kratkem času"):
        _poslji(conn, zdaj=zdaj + 10,
                zeton_iz_obrazca=stik.zeton(zdaj - stik.NAJHITREJE_S - 1))
    assert len(stik.seznam(conn)) == stik.NA_URO


def test_drug_posiljatelj_ni_omejen(conn):
    zdaj = time.time()
    for i in range(stik.NA_URO):
        _poslji(conn, zdaj=zdaj + i, kljuc="kljuc-a",
                zeton_iz_obrazca=stik.zeton(zdaj - stik.NAJHITREJE_S - 1))
    assert _poslji(conn, zdaj=zdaj + 10, kljuc="kljuc-b",
                   zeton_iz_obrazca=stik.zeton(zdaj - stik.NAJHITREJE_S - 1)) > 0


def test_po_uri_gre_spet(conn):
    zdaj = time.time()
    for i in range(stik.NA_URO):
        _poslji(conn, zdaj=zdaj + i,
                zeton_iz_obrazca=stik.zeton(zdaj - stik.NAJHITREJE_S - 1))
    pozneje = zdaj + 3601
    assert _poslji(conn, zdaj=pozneje,
                   zeton_iz_obrazca=stik.zeton(pozneje - stik.NAJHITREJE_S - 1)) > 0


def test_dnevna_meja_na_posiljatelja(conn):
    """Ura mine, dan pa ne: po `NA_DAN` je konec do jutri."""
    zdaj = time.time()
    for i in range(stik.NA_DAN):
        t = zdaj + i * 3601          # vsakič nova ura, da uri ne pademo
        _poslji(conn, zdaj=t, zeton_iz_obrazca=stik.zeton(t - stik.NAJHITREJE_S - 1))
    t = zdaj + stik.NA_DAN * 3601
    with pytest.raises(stik.Zavrnjeno, match="jutri"):
        _poslji(conn, zdaj=t, zeton_iz_obrazca=stik.zeton(t - stik.NAJHITREJE_S - 1))


def test_kljuc_posiljatelja_ni_naslov(conn):
    """Ključ ne sme vsebovati naslova, iz katerega je nastal."""
    class G(dict):
        def get(self, k, p=None):
            return super().get(k.lower(), p)

    k = stik.kljuc_posiljatelja(G({"cf-connecting-ip": "203.0.113.7"}))
    assert "203.0.113.7" not in k
    assert len(k) == 32
    # Isti naslov da isti ključ, drug naslov drugega.
    assert k == stik.kljuc_posiljatelja(G({"cf-connecting-ip": "203.0.113.7"}))
    assert k != stik.kljuc_posiljatelja(G({"cf-connecting-ip": "203.0.113.8"}))


# ------------------------------------------------------------ dnevni strop

def test_dnevni_strop_cez_vse(conn, monkeypatch):
    """Porazdeljena kampanja ne sme napolniti baze meritev.

    Vsako sporočilo pride z drugega ključa, torej nobena omejitev na
    pošiljatelja ne ujame — ustavi jih šele strop čez vse.
    """
    monkeypatch.setattr(stik, "VSEH_NA_DAN", 5)
    zdaj = time.time()
    for i in range(5):
        _poslji(conn, kljuc=f"kljuc-{i}", zdaj=zdaj,
                zeton_iz_obrazca=stik.zeton(zdaj - stik.NAJHITREJE_S - 1))
    with pytest.raises(stik.Zavrnjeno, match="poln"):
        _poslji(conn, kljuc="kljuc-x", zdaj=zdaj,
                zeton_iz_obrazca=stik.zeton(zdaj - stik.NAJHITREJE_S - 1))
    assert len(stik.seznam(conn)) == 5


# ---------------------------------------------------------------- branje

def test_stevec_in_oznacevanje(conn):
    zdaj = time.time()
    a = _poslji(conn, zdaj=zdaj,
                zeton_iz_obrazca=stik.zeton(zdaj - stik.NAJHITREJE_S - 1))
    _poslji(conn, zdaj=zdaj + 1,
            zeton_iz_obrazca=stik.zeton(zdaj - stik.NAJHITREJE_S - 1))
    assert stik.stevec(conn) == {"vseh": 2, "neprebranih": 2}
    stik.oznaci_prebrano(conn, a, True)
    assert stik.stevec(conn) == {"vseh": 2, "neprebranih": 1}
    stik.oznaci_prebrano(conn, a, False)
    assert stik.stevec(conn) == {"vseh": 2, "neprebranih": 2}


def test_najnovejse_prvo(conn):
    zdaj = time.time()
    _poslji(conn, besedilo="Prvo sporočilo v vrsti.", zdaj=zdaj,
            zeton_iz_obrazca=stik.zeton(zdaj - stik.NAJHITREJE_S - 1))
    _poslji(conn, besedilo="Drugo sporočilo v vrsti.", zdaj=zdaj + 1,
            zeton_iz_obrazca=stik.zeton(zdaj - stik.NAJHITREJE_S - 1))
    assert stik.seznam(conn)[0]["besedilo"] == "Drugo sporočilo v vrsti."


def test_brisanje(conn):
    zdaj = time.time()
    a = _poslji(conn, zdaj=zdaj,
                zeton_iz_obrazca=stik.zeton(zdaj - stik.NAJHITREJE_S - 1))
    assert stik.izbrisi(conn, a) is True
    assert stik.seznam(conn) == []
    # Drugič ni česa brisati in to mora povedati, ne pa tiho uspeti.
    assert stik.izbrisi(conn, a) is False


def test_brisanje_ne_sprosti_omejitve(conn):
    """Kdor izbriše spam, s tem ne sme podariti pošiljatelju novih poskusov.

    Omejitev živi v pomnilniku in z vrstico v bazi nima zveze — to je tu
    zapisano kot preizkus, ker bi bilo ob morebitni selitvi štetja v bazo
    prav to tiha vrzel.
    """
    zdaj = time.time()
    ids = [_poslji(conn, zdaj=zdaj + i,
                   zeton_iz_obrazca=stik.zeton(zdaj - stik.NAJHITREJE_S - 1))
           for i in range(stik.NA_URO)]
    for i in ids:
        stik.izbrisi(conn, i)
    with pytest.raises(stik.Zavrnjeno, match="kratkem času"):
        _poslji(conn, zdaj=zdaj + 10,
                zeton_iz_obrazca=stik.zeton(zdaj - stik.NAJHITREJE_S - 1))
