"""Testi štetja obiska.

Kar tu varujemo, ni statistika, ampak dvoje: da se **IP nikoli ne shrani** in
da tabela raste s številom strani, ne s prometom. Oboje je tiho, kadar se
pokvari — pregled bi še vedno kazal številke, le napačne.

    ./venv/bin/python -m pytest tests/test_obisk.py -q
"""
from __future__ import annotations

import sqlite3

import pytest

from kajros import db, obisk


class _Glave(dict):
    """Glave zahteve so pri Starlettu male črke in dostop brez upoštevanja
    velikosti; tu je dovolj slovar z malimi ključi."""

    def get(self, k, privzeto=None):
        return super().get(k.lower(), privzeto)


class _Naslov:
    def __init__(self, path):
        self.path = path


class _Zahteva:
    """Toliko zahteve, kolikor je `obisk.iz_zahteve()` res prebere."""

    def __init__(self, pot, ua="Mozilla/5.0", ip="1.2.3.4", app=None, drzava=None):
        self.url = _Naslov(pot)
        glave = {"user-agent": ua, "cf-connecting-ip": ip}
        if drzava:
            glave["cf-ipcountry"] = drzava
        self.headers = _Glave(glave)
        self.scope = {"app": app}
        self.client = None


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript(db.SCHEMA)
    obisk.init(c)
    yield c
    c.close()


@pytest.fixture(autouse=True)
def cist_pomnilnik():
    """Števci so modulni globali; en test ne sme podedovati drugega."""
    obisk._poti.clear(); obisk._razrezi.clear()
    obisk._ljudje.clear(); obisk._odzivi.clear()
    obisk._soli.clear()
    yield
    obisk._poti.clear(); obisk._razrezi.clear()
    obisk._ljudje.clear(); obisk._odzivi.clear()
    obisk._soli.clear()


def _zabelezi(**kwargs):
    osnova = dict(pot="/app/train", vrsta="stran", kljuc="abc", bot=False,
                  naprava_="telefon", drzava="SI", koda=200, ms=12.0)
    osnova.update(kwargs)
    obisk.zabelezi(**osnova)


# ------------------------------------------------------------- zasebnost

def test_kljuc_ni_povraten_in_se_dnevno_zamenja():
    a = obisk.kljuc_obiskovalca("193.2.1.1", "Firefox", "2026-09-12")
    b = obisk.kljuc_obiskovalca("193.2.1.1", "Firefox", "2026-09-13")
    assert a != b, "ista naprava ima naslednji dan drug ključ"
    # Naslova v ključu ni -- ne kot niz in ne kot del njega.
    assert "193" not in a and "2.1.1" not in a
    assert len(a) == 16


def test_ista_naprava_isti_dan_isti_kljuc():
    prvi = obisk.kljuc_obiskovalca("10.0.0.7", "Chrome", "2026-09-12")
    drugi = obisk.kljuc_obiskovalca("10.0.0.7", "Chrome", "2026-09-12")
    assert prvi == drugi


def test_ip_ne_pride_v_bazo(conn):
    _zabelezi(kljuc=obisk.kljuc_obiskovalca("193.2.1.1", "Chrome", "2026-09-12"))
    obisk.izprazni(conn)
    izpis = "".join(str(r) for r in conn.execute("SELECT * FROM obiskovalec"))
    assert "193.2.1.1" not in izpis


def test_sol_preprecuje_ugibanje():
    """Brez soli bi bil ključ zgolj zgoščen IP in ga je mogoče poiskati z
    obhodom vseh naslovov. Dve soli morata dati dva različna ključa."""
    obisk._soli.clear()
    prvi = obisk.kljuc_obiskovalca("193.2.1.1", "Chrome", "2026-09-12")
    obisk._soli.clear()
    drugi = obisk.kljuc_obiskovalca("193.2.1.1", "Chrome", "2026-09-12")
    assert prvi != drugi


# --------------------------------------------------------- razvrščanje UA

@pytest.mark.parametrize("ua, pricakovano", [
    ("Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit", "telefon"),
    ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", "telefon"),
    ("Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X)", "tablica"),
    ("Mozilla/5.0 (X11; Linux x86_64) Firefox/130.0", "računalnik"),
    ("Kajros/1.2 (Android)", "aplikacija"),
    ("", "neznano"),
])
def test_naprava(ua, pricakovano):
    assert obisk.naprava(ua) == pricakovano


@pytest.mark.parametrize("ua", [
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "curl/8.5.0",
    "python-requests/2.32",
    # Ujeto na zaslonu 12. 9. 2026: naš lastni preizkus hitrosti je s tem UA
    # naredil 2 012 zahtev, ki so se pokazale kot „računalnik". Regexp je
    # naštevala knjižnice in prav te ni imela.
    "Python-urllib/3.14",
    "HeadlessChrome/120.0.0.0",       # nas lastni scripts/preveri.sh
    "",                               # brskalnik se vedno predstavi
])
def test_boti_prepoznani(ua):
    assert obisk.je_bot(ua)


@pytest.mark.parametrize("ua", [
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0",
    "Kajros/1.2 (Android)",           # nas ovoj je uporabnik, ne stroj
])
def test_pravi_odjemalci_niso_boti(ua):
    assert not obisk.je_bot(ua)


# ------------------------------------------------------------ oblike poti

def test_oblika_poti_zdruzi_voznje():
    """`/app/train/2010` in `/app/train/511` sta ISTA vrstica.

    Brez tega tabela raste s prometom in ne s številom strani: LPP linija 3G
    ima 388 voženj, vsaka bi bila svoja vrstica na dan.
    """
    from kajros import api
    obisk._vzorci = None
    a = obisk.oblika_poti(_Zahteva("/app/train/2010", app=api.app))
    b = obisk.oblika_poti(_Zahteva("/app/train/511", app=api.app))
    assert a == b == "/app/train/{train_no}"


def test_neznana_pot_v_eno_vrstico():
    from kajros import api
    obisk._vzorci = None
    assert obisk.oblika_poti(_Zahteva("/wp-admin/setup.php", app=api.app)) == obisk.NEZNANO


def test_statika_in_admin_se_ne_steje():
    from kajros import api
    obisk._vzorci = None
    assert obisk.oblika_poti(_Zahteva("/static/base.css", app=api.app)) is None
    assert obisk.oblika_poti(_Zahteva("/admin", app=api.app)) is None
    assert obisk.oblika_poti(_Zahteva("/admin/podatki", app=api.app)) is None


@pytest.mark.parametrize("pot, vrsta", [
    ("/", "stran"), ("/app/train", "stran"), ("/app/map", "stran"),
    ("/api/live", "api"), ("/docs", "drugo"),
])
def test_vrsta_poti(pot, vrsta):
    assert obisk.vrsta_poti(pot) == vrsta


# -------------------------------------------------------------- seštevanje

def test_stevci_se_sestevajo_cez_vec_praznjenj(conn):
    for _ in range(3):
        _zabelezi()
    obisk.izprazni(conn)
    _zabelezi()
    obisk.izprazni(conn)
    vrstica = conn.execute(
        "SELECT zahtev, ljudi FROM obisk_pot WHERE pot = '/app/train'").fetchone()
    assert vrstica["zahtev"] == 4 and vrstica["ljudi"] == 4
    assert conn.execute("SELECT COUNT(*) FROM obisk_pot").fetchone()[0] == 1


def test_napake_se_stejejo_locheno(conn):
    _zabelezi(koda=404)
    _zabelezi(koda=503)
    _zabelezi(koda=200)
    obisk.izprazni(conn)
    v = conn.execute("SELECT napak4, napak5, zahtev FROM obisk_pot").fetchone()
    assert (v["napak4"], v["napak5"], v["zahtev"]) == (1, 1, 3)


def test_obiskovalec_ena_vrstica_na_dan(conn):
    for _ in range(20):
        _zabelezi(kljuc="ista-naprava")
    obisk.izprazni(conn)
    v = conn.execute("SELECT zahtev, ogledov FROM obiskovalec").fetchall()
    assert len(v) == 1 and v[0]["zahtev"] == 20 and v[0]["ogledov"] == 20


def test_bot_ne_pokvari_razrezov(conn):
    """Bot, ki vsako uro potrka, bi sicer narisal enakomeren dan in ubil edino
    zanimivo črto -- kdaj se ljudje res peljejo."""
    _zabelezi(bot=True, kljuc="bot", ura=3)
    _zabelezi(bot=False, kljuc="clovek", ura=17)
    obisk.izprazni(conn)
    ure = [r["kljuc"] for r in conn.execute(
        "SELECT kljuc FROM obisk_razrez WHERE razsez = 'ura'")]
    assert ure == ["17"]
    # V `obisk_pot` je bot vseeno štet -- promet je promet, le `ljudi` ne.
    v = conn.execute("SELECT zahtev, ljudi FROM obisk_pot").fetchone()
    assert v["zahtev"] == 2 and v["ljudi"] == 1


def test_prazno_praznjenje_ne_pise(conn):
    assert obisk.izprazni(conn) == 0


def test_varovalka_pred_poplavo_kljucev(conn):
    """Kdor preiskuje z izmišljenimi naslovi, ne sme napolniti pomnilnika."""
    obisk._poti.clear()
    for i in range(obisk.NAJVEC_KLJUCEV + 50):
        obisk.zabelezi(pot=f"/x{i}", vrsta="drugo", kljuc="k", bot=True,
                       naprava_="neznano", drzava="??", koda=404, ms=1.0)
    assert len(obisk._poti) <= obisk.NAJVEC_KLJUCEV + 1
    assert obisk._prelito


# ------------------------------------------------------------- odzivni čas

@pytest.mark.parametrize("ms, vedro", [
    (0.5, 0), (10, 0), (10.1, 1), (99, 3), (250, 4), (9999, len(obisk.VEDRA)),
])
def test_vedro(ms, vedro):
    assert obisk.vedro(ms) == vedro


def test_percentil_vrne_razred_in_ne_izmisljene_vrednosti():
    # Devetindevetdeset hitrih in ena zelo počasna: mediana mora ostati v
    # prvem razredu, p95 tudi -- ena sama vrednost ne sme premakniti p95.
    vedra = {0: 99, len(obisk.VEDRA): 1}
    assert obisk._percentil(vedra, 0.50)["do"] == obisk.VEDRA[0]
    assert obisk._percentil(vedra, 0.95)["do"] == obisk.VEDRA[0]
    # Prazno ni nič in ne ničla.
    assert obisk._percentil({}, 0.5) == {"do": None, "n": 0}


def test_percentil_ujame_pocasnost():
    """Polovica zahtev čez zadnjo mejo pomeni, da mediane ni več v vedrih."""
    vedra = {0: 50, len(obisk.VEDRA): 50}
    assert obisk._percentil(vedra, 0.95)["do"] is None


# ----------------------------------------------------------------- pregled

def test_pregled_loci_ljudi_od_botov(conn):
    _zabelezi(kljuc="clovek1", bot=False)
    _zabelezi(kljuc="clovek2", bot=False)
    _zabelezi(kljuc="bot1", bot=True)
    obisk.izprazni(conn)
    p = obisk.pregled(conn, dni=7)
    assert p["danes"]["ljudi"] == 2
    assert p["danes"]["botov"] == 1
    assert p["skupaj"]["ljudi_vsota"] == 2


def test_pregled_prazne_baze_ne_pade(conn):
    p = obisk.pregled(conn, dni=30)
    assert p["danes"]["ljudi"] == 0
    assert p["po_dnevih"] == [] and p["strani"] == []


def test_prune_pobrise_staro(conn):
    conn.execute("INSERT INTO obisk_pot(dan, pot, vrsta, zahtev) "
                 "VALUES('2020-01-01', '/', 'stran', 5)")
    _zabelezi()
    obisk.izprazni(conn)
    assert obisk.prune(conn, dni=30) >= 1
    poti = [r["pot"] for r in conn.execute("SELECT pot FROM obisk_pot")]
    assert poti == ["/app/train"]
