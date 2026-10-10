"""Brskalnik za potniski.sz.si: WebSocket do Chroma, izziv Cloudflara, ponovni zagon.

Brez Chroma: odjemalec WebSocket se pogovarja s strežnikom v preizkusu,
logika zahtev pa z lažnim CDP.

    ./venv/bin/python -m pytest tests/test_brskalnik.py -q
"""
from __future__ import annotations

import base64
import hashlib
import json
import socket
import threading

import pytest

from kajros import brskalnik

IZZIV = ('<!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title>'
         '<script src="/cdn-cgi/challenge-platform/h/g/orchestrate/chl_page/v1"></script>')


def test_izziv_prepoznan_stran_ne():
    assert brskalnik.je_izziv(IZZIV)
    assert brskalnik.je_izziv("<html><title>Trenutek …</title><script>window._cf_chl_opt={}")
    assert not brskalnik.je_izziv('[{"St_vlaka":"39","Zamuda_cas":0}]')
    assert not brskalnik.je_izziv("<title>Odhodi in prihodi na postaji - Slovenske železnice</title>")


def test_maska_je_svoja_inverzna():
    podatki = bytes(range(256)) * 300 + b"x"
    maska = b"\x01\x80\xfe\x37"
    assert brskalnik._xor(brskalnik._xor(podatki, maska), maska) == podatki
    assert brskalnik._xor(b"", maska) == b""


# --- strežnik WebSocket v preizkusu -----------------------------------------


def _okvir(opcode: int, podatki: bytes, fin: bool = True) -> bytes:
    n = len(podatki)
    glava = bytes([(0x80 if fin else 0) | opcode])
    if n < 126:
        glava += bytes([n])
    elif n < 1 << 16:
        glava += bytes([126]) + n.to_bytes(2, "big")
    else:
        glava += bytes([127]) + n.to_bytes(8, "big")
    return glava + podatki


def _beri_okvir(s: socket.socket) -> tuple[int, bytes]:
    def beri(n):
        out = b""
        while len(out) < n:
            out += s.recv(n - len(out))
        return out
    b0, b1 = beri(2)
    assert b1 & 0x80, "odjemalec mora maskirati"
    n = b1 & 0x7F
    if n == 126:
        n = int.from_bytes(beri(2), "big")
    elif n == 127:
        n = int.from_bytes(beri(8), "big")
    maska = beri(4)
    return b0 & 0x0F, brskalnik._xor(beri(n), maska)


@pytest.fixture
def streznik():
    """(vrata, seznam za izid) -- strežnik sprejme eno povezavo in odigra
    `scenarij(sock)`, ki ga preizkus postavi pred povezavo."""
    ls = socket.socket()
    ls.bind(("127.0.0.1", 0))
    ls.listen(1)
    stanje = {"scenarij": None, "odgovor": None}

    def teci():
        s, _ = ls.accept()
        zahteva = b""
        while b"\r\n\r\n" not in zahteva:
            zahteva += s.recv(4096)
        kljuc = next(v.split(b":", 1)[1].strip() for v in zahteva.split(b"\r\n")
                     if v.lower().startswith(b"sec-websocket-key"))
        sprejem = base64.b64encode(hashlib.sha1(kljuc + brskalnik._Ws._GUID).digest())
        s.sendall(stanje["odgovor"] or (b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\n"
                  b"Connection: Upgrade\r\nSec-WebSocket-Accept: " + sprejem + b"\r\n\r\n"))
        if stanje["scenarij"]:
            stanje["scenarij"](s)
        s.close()

    nit = threading.Thread(target=teci, daemon=True)
    yield ls.getsockname()[1], stanje, nit
    ls.close()


def test_ws_okvirji_vseh_dolzin_razdeljeni_in_ping(streznik):
    vrata, stanje, nit = streznik
    prejeto = []
    velik = json.dumps({"id": 2, "result": {"value": "x" * 70_000}}).encode()

    def scenarij(s):
        prejeto.append(_beri_okvir(s))
        s.sendall(_okvir(0x9, b"zivo?"))                 # ping
        prejeto.append(_beri_okvir(s))                   # pong
        s.sendall(_okvir(0x1, b'{"id": 1'))
        s.sendall(_okvir(0x1, b'{"a": ', fin=False) + _okvir(0x0, b'"b"}'))   # v dveh kosih
        s.sendall(_okvir(0x1, b"y" * 300))
        s.sendall(_okvir(0x1, velik))
        s.sendall(_okvir(0x8, b""))

    stanje["scenarij"] = scenarij
    nit.start()
    ws = brskalnik._Ws(vrata, "/devtools/browser/x")
    ws.poslji('{"id": 1, "method": "Browser.getVersion"}')
    assert ws.prejmi() == '{"id": 1'
    assert ws.prejmi() == '{"a": "b"}'
    assert ws.prejmi() == "y" * 300
    assert ws.prejmi() == velik.decode()
    with pytest.raises(EOFError):
        ws.prejmi()
    nit.join(5)
    assert prejeto[0] == (0x1, b'{"id": 1, "method": "Browser.getVersion"}')
    assert prejeto[1] == (0xA, b"zivo?")
    ws.zapri()


def test_ws_zavrnjeno_rokovanje(streznik):
    vrata, stanje, nit = streznik
    stanje["odgovor"] = b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n"
    nit.start()
    with pytest.raises(brskalnik.NapakaBrskalnika, match="403"):
        brskalnik._Ws(vrata, "/devtools/browser/x")


def test_cdp_odgovor_po_id_in_zaprta_povezava(streznik):
    vrata, stanje, nit = streznik

    def scenarij(s):
        op, sporocilo = _beri_okvir(s)
        m = json.loads(sporocilo)
        s.sendall(_okvir(0x1, b'{"method": "Target.targetCreated", "params": {}}'))
        s.sendall(_okvir(0x1, json.dumps({"id": m["id"], "result": {"product": "Chrome/155"}}).encode()))
        op, sporocilo = _beri_okvir(s)
        m = json.loads(sporocilo)
        assert m["sessionId"] == "S"
        s.sendall(_okvir(0x1, json.dumps({"id": m["id"], "error": {"message": "ne gre"}}).encode()))

    stanje["scenarij"] = scenarij
    nit.start()
    cdp = brskalnik._Cdp(brskalnik._Ws(vrata, "/x"))
    assert cdp.ukaz("Browser.getVersion")["product"] == "Chrome/155"
    with pytest.raises(brskalnik.NapakaBrskalnika, match="ne gre"):
        cdp.ukaz("Runtime.evaluate", seja="S", expression="1")
    nit.join(5)
    with pytest.raises(brskalnik.NapakaBrskalnika, match="povezava s Chromom"):
        cdp.ukaz("Browser.getVersion", cas=2)
    cdp.zapri()


# --- logika zahtev z lažnim Chromom -------------------------------------------


class _LazniProces:
    pid = 999_999_999

    def poll(self):
        return None


class _LazniCdp:
    """Odigra odgovore `fetch` po vrsti; izziv se reši, kadar `resi`."""

    def __init__(self, odgovori, resi=True):
        self.odgovori = list(odgovori)
        self.resi = resi
        self.zaprt = None
        self.klici = []

    def ukaz(self, metoda, seja=None, cas=30, **par):
        self.klici.append(metoda)
        if metoda == "Page.navigate":
            return {}
        if metoda == "Runtime.evaluate":
            if par["expression"] == brskalnik._NALOZENA_JS:
                return {"result": {"value": self.resi}}
            o = self.odgovori.pop(0)
            if isinstance(o, Exception):
                raise o
            return {"result": {"value": o}}
        return {}

    def zapri(self):
        pass


@pytest.fixture
def brsk(monkeypatch, tmp_path):
    monkeypatch.setattr(brskalnik, "_ustavi_skupino", lambda p: None)
    monkeypatch.setattr(brskalnik, "PREBOJ_S", 1)
    monkeypatch.setattr(brskalnik.time, "sleep", lambda s: None)
    b = brskalnik.Brskalnik(tmp_path / "profil")
    zagoni = []

    def zazeni(odgovori, resi=True):
        def _zazeni():
            zagoni.append(1)
            b._chrome, b._seja = _LazniProces(), "S"
            b._cdp = _LazniCdp(odgovori, resi)
            b._s.update(zaslon="Xvfb :7", od_ts=int(brskalnik.time.time()))
        monkeypatch.setattr(b, "_zazeni", _zazeni)

    return b, zazeni, zagoni


def test_izziv_se_resi_in_zahteva_ponovi(brsk):
    b, zazeni, zagoni = brsk
    zazeni([{"status": 403, "besedilo": IZZIV}, {"status": 200, "besedilo": "[]"}])
    assert b.zahtevaj("/wp-admin/admin-ajax.php?action=aktivni_vlaki") == "[]"
    s = b.stanje()
    assert (s["izzivi"], s["preboji"], s["zahtev"], s["napaka"]) == (1, 2, 1, None)
    assert len(zagoni) == 1


def test_izziv_dvakrat_ugasne_chrome(brsk):
    b, zazeni, zagoni = brsk
    zazeni([{"status": 403, "besedilo": IZZIV}, {"status": 403, "besedilo": IZZIV}])
    with pytest.raises(brskalnik.NapakaBrskalnika, match="izziv"):
        b.zahtevaj("/x")
    assert b._chrome is None and "izziv" in b.stanje()["napaka"]


def test_izziv_ki_ga_chrome_ne_resi(brsk):
    b, zazeni, zagoni = brsk
    zazeni([{"status": 403, "besedilo": IZZIV}], resi=False)
    with pytest.raises(brskalnik.NapakaBrskalnika, match="Cloudflare ne spusti") as e:
        b.zahtevaj("/x")
    assert e.value.http == 403


def test_napaka_strani_ne_ugasne_zastoj_pa(brsk):
    b, zazeni, zagoni = brsk
    zazeni([{"status": 500, "besedilo": "napaka"}, {"napaka": "TypeError: Failed to fetch"},
            brskalnik._Zastoj("Chrome ni odgovoril v 45 s")])
    with pytest.raises(brskalnik.NapakaBrskalnika, match="odgovori 500") as e:
        b.zahtevaj("/x")
    assert e.value.http == 500 and b._chrome is not None
    with pytest.raises(brskalnik.NapakaBrskalnika, match="Failed to fetch"):
        b.zahtevaj("/x")
    assert b._chrome is not None
    with pytest.raises(brskalnik.NapakaBrskalnika, match="ni odgovoril"):
        b.zahtevaj("/x")
    assert b._chrome is None


def test_neuspel_zagon_pocaka_preden_poskusi_znova(brsk, monkeypatch):
    b, zazeni, zagoni = brsk
    klici = []

    def ne_gre():
        klici.append(1)
        raise brskalnik.NapakaBrskalnika("ni Chroma: namesti Google Chrome (deploy/brskalnik.sh)")

    monkeypatch.setattr(b, "_zazeni", ne_gre)
    for _ in range(3):
        with pytest.raises(brskalnik.NapakaBrskalnika, match="ni Chroma"):
            b.zahtevaj("/x")
    assert len(klici) == 1, "naslednji poskus šele po PO_NAPAKI_ZAGONA_S"
    assert brskalnik.PO_NAPAKI_ZAGONA_S - 5 < b.pocitek_s() <= brskalnik.PO_NAPAKI_ZAGONA_S
    b._napaka_zagona_ts -= brskalnik.PO_NAPAKI_ZAGONA_S
    assert b.pocitek_s() == 0


def test_star_chrome_se_zazene_znova(brsk, monkeypatch):
    b, zazeni, zagoni = brsk
    zazeni([{"status": 200, "besedilo": "a"}, {"status": 200, "besedilo": "b"},
            {"status": 200, "besedilo": "c"}])
    assert b.zahtevaj("/x") == "a"
    b._s["od_ts"] -= brskalnik.NAJDLJE_ZIVI_S + 1
    zazeni([{"status": 200, "besedilo": "b"}])
    assert b.zahtevaj("/x") == "b"
    assert len(zagoni) == 2


def test_chrome_in_xvfb_po_nastavitvi(monkeypatch, tmp_path):
    monkeypatch.setattr(brskalnik.config, "SZ_CHROME", str(tmp_path / "ni-ga"))
    assert brskalnik.najdi_chrome() is None, "izrecna pot, ki ne obstaja, ni Chrome"
    exe = tmp_path / "chrome"
    exe.write_text("#!/bin/sh\n")
    exe.chmod(0o755)
    monkeypatch.setattr(brskalnik.config, "SZ_CHROME", str(exe))
    assert brskalnik.najdi_chrome() == str(exe)
    monkeypatch.setattr(brskalnik.config, "SZ_XVFB", "")
    monkeypatch.setattr(brskalnik.shutil, "which", lambda ime: None)
    assert brskalnik.najdi_xvfb() is None


def test_brez_zaslona_ni_brskalnika(monkeypatch, tmp_path):
    monkeypatch.setattr(brskalnik, "najdi_xvfb", lambda: None)
    b = brskalnik.Brskalnik(tmp_path / "p")
    with pytest.raises(brskalnik.NapakaBrskalnika, match="ni zaslona"):
        b._zaslon({})
    assert b._zaslon({"DISPLAY": ":0"}) == []
