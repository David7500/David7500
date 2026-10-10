"""Brskalnik za potniski.sz.si: podatki SŽ brez posrednika.

Zakaj: potniski.sz.si je za Cloudflarom. `curl` dobi 403 od nekdaj, brezglavi
chromium je izziv rešil še 6. 10. 2026, od 7. 10. ne več (stran „Izvajanje
varnostnega preverjanja“ v zanki). Isti dan sta utihnila `api.modra.ninja`, ki
je stran strgal za nas in za derp.si, in z njim vse zamude vlakov. Chrome
**z oknom** izziv reši sam v nekaj sekundah -- izmerjeno 10. 10. 2026 na
razvojnem stroju (pravi zaslon) in na arwenu pod Xvfb (navidezni zaslon).

Kako: en Chrome za ves proces, voden prek CDP na vratih localhosta, ki jih
izberemo sami. **Ne po cevi** (`--remote-debugging-pipe`) **in ne z vrati 0**
(`--remote-debugging-port=0`, Chrome izbere sam): v obeh primerih Chrome sam
postavi `navigator.webdriver = true` in Cloudflare ga ne spusti -- izmerjeno
10. 10. 2026, pet poskusov po 40--90 s brez preboja; z izbranimi vrati isti
Chrome v 3--7 s. Naloži se ena stran SŽ; podatke nato beremo s `fetch` ZNOTRAJ
nje, da gre piškotek `cf_clearance` zraven. Ena zahteva 0,6--0,8 s.

Cloudflare piškotek občasno zavrne (10. 10. 2026: enkrat v 40 min, 403 z
izzivom). Tedaj se stran naloži znova, izziv se reši sam (7 s) in zahteva se
ponovi enkrat. Kadar ne gre, je napaka vidna v /admin (`stanje()`).

Bralca sta dva (`zamude_sz`, `peroni`), vsak v svoji niti; zahteve gredo ena
za drugo (`_kljuc`). Chrome se zažene ob prvi zahtevi, ne ob zagonu
strežnika, in se vsakih `NAJDLJE_ZIVI_S` zažene znova s praznim profilom --
dolgo živ brskalnik raste.
"""
from __future__ import annotations

import atexit
import base64
import hashlib
import json
import os
import select
import shutil
import signal
import socket
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

from . import config

IZVOR = "https://potniski.sz.si"
#: Stran, ki jo naložimo za prehod skozi izziv: tabla zamud, 455 kB.
ZACETNA = IZVOR + "/pomoc-uporabnikom-in-stanje-v-prometu/"
#: WordPress SŽ na vsaki strani postavi `siteVars`; stran z izzivom ga nima.
_NALOZENA_JS = "typeof siteVars !== 'undefined' && document.readyState === 'complete'"

#: Toliko čakamo, da Chrome po zagonu odpre vrata in odgovori.
ZAGON_S = 30
#: Toliko sme trajati izziv. Izmerjeno 10. 10. 2026: 3--7 s.
PREBOJ_S = 90
#: Ena zahteva; odgovor je 5 kB (zemljevid) do 175 kB (tabla postaje).
ZAHTEVA_S = 45
#: Po neuspelem zagonu (ni Chroma, ni zaslona) toliko ne poskusimo znova:
#: niti ga kličeta vsako minuto in vsaka bi sicer zagnala svoj poskus.
PO_NAPAKI_ZAGONA_S = 300
#: Chrome, ki teče dlje, se ob naslednji zahtevi zažene znova.
NAJDLJE_ZIVI_S = 6 * 3600

#: Po vrsti, prvi najdeni. Na arwenu `google-chrome-stable` iz paketa Google
#: (`deploy/brskalnik.sh`): Ubuntu 24.04 mu z AppArmorjem dovoli peskovnik.
_CHROMI = ("google-chrome-stable", "google-chrome", "chromium", "chromium-browser", "chrome")

#: Besedilo, po katerem prepoznamo Cloudflarov izziv namesto odgovora SŽ.
_IZZIV = ("/cdn-cgi/challenge-platform/", "_cf_chl_opt", "cf-chl", "<title>just a moment")


class NapakaBrskalnika(RuntimeError):
    """`http` prebere `viri._http`, besedilo `viri.opis_napake`."""

    def __init__(self, sporocilo: str, http: int | None = None):
        super().__init__(sporocilo)
        self.http = http


class _Izziv(NapakaBrskalnika):
    """Cloudflare je namesto odgovora vrnil izziv."""


class _Zastoj(NapakaBrskalnika):
    """Chrome ne odgovori: tak se ne popravi sam."""


def najdi_chrome() -> str | None:
    if config.SZ_CHROME:
        return config.SZ_CHROME if os.access(config.SZ_CHROME, os.X_OK) else None
    return next((p for p in map(shutil.which, _CHROMI) if p), None)


def najdi_xvfb() -> str | None:
    if config.SZ_XVFB:
        return config.SZ_XVFB if os.access(config.SZ_XVFB, os.X_OK) else None
    return shutil.which("Xvfb")


def je_izziv(besedilo: str) -> bool:
    zacetek = besedilo[:20000].lower()
    return any(z in zacetek for z in _IZZIV)


# --- WebSocket ---------------------------------------------------------------


def _xor(podatki: bytes, maska: bytes) -> bytes:
    n = len(podatki)
    if not n:
        return b""
    m = (maska * (n // 4 + 1))[:n]
    return (int.from_bytes(podatki, "little") ^ int.from_bytes(m, "little")).to_bytes(n, "little")


class _Ws:
    """Najmanjši odjemalec WebSocket (RFC 6455) za CDP na localhostu.

    Samo to, kar Chrome rabi: besedilni okvirji, k strežniku maskirani,
    brez razširitev. Knjižnice zanj ni v `requirements.txt` in je za
    rokovanje in dve vrsti okvirjev ne rabimo.
    """

    _GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    def __init__(self, port: int, pot: str, cas: float = 10):
        self._s = socket.create_connection(("127.0.0.1", port), timeout=cas)
        self._pisanje = threading.Lock()
        kljuc = base64.b64encode(os.urandom(16))
        self._s.sendall(
            f"GET {pot} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {kljuc.decode()}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n".encode())
        glava = bytearray()
        while b"\r\n\r\n" not in glava:
            kos = self._s.recv(4096)
            if not kos:
                raise NapakaBrskalnika("Chrome je zaprl povezavo ob rokovanju")
            glava += kos
        konec = glava.index(b"\r\n\r\n")
        self._buf = bytearray(glava[konec + 4:])
        vrstice = bytes(glava[:konec]).decode("latin-1").split("\r\n")
        sprejem = base64.b64encode(hashlib.sha1(kljuc + self._GUID).digest()).decode()
        glave = {k.strip().lower(): v.strip() for k, _, v in (x.partition(":") for x in vrstice[1:])}
        if vrstice[0].split(" ")[1:2] != ["101"] or glave.get("sec-websocket-accept") != sprejem:
            raise NapakaBrskalnika(f"Chrome ne sprejme povezave: {vrstice[0]}")
        self._s.settimeout(None)

    def _beri(self, n: int) -> bytes:
        while len(self._buf) < n:
            kos = self._s.recv(1 << 16)
            if not kos:
                raise EOFError("Chrome je zaprl povezavo")
            self._buf += kos
        out = bytes(self._buf[:n])
        del self._buf[:n]
        return out

    def _okvir(self, opcode: int, podatki: bytes) -> None:
        n = len(podatki)
        glava = bytearray([0x80 | opcode])
        if n < 126:
            glava.append(0x80 | n)
        elif n < 1 << 16:
            glava += bytes([0x80 | 126]) + n.to_bytes(2, "big")
        else:
            glava += bytes([0x80 | 127]) + n.to_bytes(8, "big")
        maska = os.urandom(4)
        with self._pisanje:
            self._s.sendall(bytes(glava) + maska + _xor(podatki, maska))

    def poslji(self, besedilo: str) -> None:
        self._okvir(0x1, besedilo.encode())

    def prejmi(self) -> str:
        deli = []
        while True:
            b0, b1 = self._beri(2)
            n = b1 & 0x7F
            if n == 126:
                n = int.from_bytes(self._beri(2), "big")
            elif n == 127:
                n = int.from_bytes(self._beri(8), "big")
            maska = self._beri(4) if b1 & 0x80 else None
            podatki = self._beri(n)
            if maska:
                podatki = _xor(podatki, maska)
            opcode = b0 & 0x0F
            if opcode == 0x8:
                raise EOFError("Chrome je zaprl povezavo")
            if opcode == 0x9:
                self._okvir(0xA, podatki)
                continue
            if opcode == 0xA:
                continue
            deli.append(podatki)
            if b0 & 0x80:
                return b"".join(deli).decode()

    def zapri(self) -> None:
        try:
            self._s.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self._s.close()


class _Cdp:
    """Ukazi CDP in odgovori nanje; dogodke zavržemo."""

    def __init__(self, ws: _Ws):
        self._ws = ws
        self._n = 0
        self._odgovori: dict[int, dict] = {}
        self._pogoj = threading.Condition()
        self.zaprt: str | None = None
        threading.Thread(target=self._beri, daemon=True, name="kajros-brskalnik-cdp").start()

    def _beri(self) -> None:
        try:
            while True:
                m = json.loads(self._ws.prejmi())
                if "id" in m:
                    with self._pogoj:
                        self._odgovori[m["id"]] = m
                        self._pogoj.notify_all()
        except Exception as exc:        # noqa: BLE001 -- vsak konec branja je konec povezave
            razlog = f"povezava s Chromom: {exc}"
        with self._pogoj:
            self.zaprt = razlog
            self._pogoj.notify_all()

    def ukaz(self, metoda: str, seja: str | None = None, cas: float = 30, **par) -> dict:
        with self._pogoj:
            if self.zaprt:
                raise NapakaBrskalnika(self.zaprt)
            self._n += 1
            moj = self._n
        sporocilo = {"id": moj, "method": metoda, "params": par}
        if seja:
            sporocilo["sessionId"] = seja
        try:
            self._ws.poslji(json.dumps(sporocilo))
        except OSError as exc:
            raise NapakaBrskalnika(f"povezava s Chromom: {exc}") from exc
        konec = time.monotonic() + cas
        with self._pogoj:
            while moj not in self._odgovori:
                if self.zaprt:
                    raise NapakaBrskalnika(self.zaprt)
                ostane = konec - time.monotonic()
                if ostane <= 0:
                    raise _Zastoj(f"Chrome ni odgovoril v {cas:g} s ({metoda})")
                self._pogoj.wait(ostane)
            m = self._odgovori.pop(moj)
        if "error" in m:
            raise NapakaBrskalnika(f"{metoda}: {m['error'].get('message')}")
        return m.get("result", {})

    def zapri(self) -> None:
        self._ws.zapri()


# --- procesi -----------------------------------------------------------------


def _prosta_vrata() -> int:
    """Prosta vrata na localhostu. Izberemo jih mi: ob `=0` bi Chrome izbral
    sam in se razglasil za avtomatiziranega (glej glavo modula)."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _ustavi_skupino(p: subprocess.Popen | None) -> None:
    """Chrome ima desetino procesov; vsi so v skupini, ki jo vodi prvi."""
    if p is None or p.poll() is not None:
        return
    try:
        os.killpg(p.pid, signal.SIGTERM)
        p.wait(timeout=5)
    except (ProcessLookupError, PermissionError):
        pass
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        p.wait(timeout=5)


def _pomnilnik(pgid: int) -> int | None:
    """PSS vseh procesov skupine (Linux). Vsota RSS bi deljeni pomnilnik
    štela 14-krat: 1 287 MB proti 563 MB PSS (arwen, 10. 10. 2026)."""
    vsota = 0
    try:
        imena = os.listdir("/proc")
    except OSError:
        return None
    for ime in imena:
        if not ime.isdigit():
            continue
        try:
            with open(f"/proc/{ime}/stat", encoding="ascii", errors="replace") as fh:
                polja = fh.read().rsplit(")", 1)[1].split()
            if int(polja[2]) != pgid:
                continue
            with open(f"/proc/{ime}/smaps_rollup", encoding="ascii") as fh:
                for vrstica in fh:
                    if vrstica.startswith("Pss:"):
                        vsota += int(vrstica.split()[1]) * 1024
                        break
        except (OSError, ValueError, IndexError):
            continue
    return vsota or None


class Brskalnik:
    def __init__(self, profil: Path | None = None):
        self._profil = profil or config.DATA_DIR / "sz-brskalnik"
        self._kljuc = threading.Lock()          # ena zahteva naenkrat
        self._stanje_kljuc = threading.Lock()   # za `stanje()`, ki ne sme čakati zahteve
        self._chrome: subprocess.Popen | None = None
        self._xvfb: subprocess.Popen | None = None
        self._cdp: _Cdp | None = None
        self._seja: str | None = None
        self._cilj: str | None = None
        self._napaka_zagona_ts = 0.0
        self._s = {"pot": None, "razlicica": None, "zaslon": None, "od_ts": None,
                   "zagonov": 0, "preboji": 0, "izzivi": 0, "zadnji_preboj_ts": None,
                   "zadnji_preboj_s": None, "zahtev": 0, "napaka": None, "napaka_ts": None}

    # --- javno ---------------------------------------------------------

    def zahtevaj(self, pot: str, cas: float = ZAHTEVA_S) -> str:
        """Besedilo odgovora za `pot` na potniski.sz.si (npr. `/wp-admin/...`)."""
        with self._kljuc:
            try:
                self._zagotovi()
                try:
                    besedilo = self._fetch(pot, cas)
                except _Izziv:
                    self._zapisi(izzivi=self._s["izzivi"] + 1)
                    self._prebij()
                    besedilo = self._fetch(pot, cas)
            except _Izziv as exc:
                # Tudi po prebijanju izziv: piškotek ali profil je pokvarjen.
                # Naslednja zahteva začne s svežim Chromom.
                self._ugasni()
                self._napaka(exc)
                raise
            except NapakaBrskalnika as exc:
                if isinstance(exc, _Zastoj) or self._cdp is None or self._cdp.zaprt:
                    self._ugasni()
                self._napaka(exc)
                raise
            self._zapisi(zahtev=self._s["zahtev"] + 1)
            return besedilo

    def stanje(self) -> dict:
        with self._stanje_kljuc:
            s = dict(self._s)
        p = self._chrome
        s["tece"] = p is not None and p.poll() is None
        s["pid"] = p.pid if s["tece"] else None
        s["pomnilnik"] = _pomnilnik(p.pid) if s["tece"] else None
        return s

    def ustavi(self) -> None:
        with self._kljuc:
            self._ugasni()

    def pocitek_s(self) -> float:
        """Koliko sekund še ne poskusi zagona (po neuspelem). Nit, ki bere na
        5 s, sicer ves ta čas dobiva isto napako -- na malini brez Chroma vsakih
        5 s zapis napake v bazo."""
        return max(0.0, PO_NAPAKI_ZAGONA_S - (time.time() - self._napaka_zagona_ts))

    # --- notranje ------------------------------------------------------

    def _zapisi(self, **kv) -> None:
        with self._stanje_kljuc:
            self._s.update(kv)

    def _napaka(self, exc: BaseException) -> None:
        self._zapisi(napaka=str(exc)[:300], napaka_ts=int(time.time()))

    def _zagotovi(self) -> None:
        p, cdp = self._chrome, self._cdp
        zivi = (p is not None and p.poll() is None and cdp is not None and not cdp.zaprt)
        if zivi and time.time() - (self._s["od_ts"] or 0) < NAJDLJE_ZIVI_S:
            return
        self._ugasni()
        if time.time() - self._napaka_zagona_ts < PO_NAPAKI_ZAGONA_S:
            raise NapakaBrskalnika(self._s["napaka"] or "brskalnik se ne zažene")
        try:
            self._zazeni()
            self._prebij()
        except NapakaBrskalnika:
            self._napaka_zagona_ts = time.time()
            self._ugasni()
            raise
        if not self._s["zaslon"].startswith("Xvfb"):
            # Na zaslonu razvijalca okno pomanjšamo -- šele po izzivu, ki ga
            # pomanjšano okno morda ne reši. Stran teče naprej.
            try:
                okno = self._cdp.ukaz("Browser.getWindowForTarget", seja=None,
                                      targetId=self._cilj)["windowId"]
                self._cdp.ukaz("Browser.setWindowBounds", windowId=okno,
                               bounds={"windowState": "minimized"})
            except (NapakaBrskalnika, KeyError):
                pass

    def _zaslon(self, env: dict) -> list[str]:
        """Navidezni zaslon, sicer zaslon tega stroja. Brez okna ne gre:
        brezglavega Chroma Cloudflare od 7. 10. 2026 ne spusti."""
        xvfb = najdi_xvfb()
        if xvfb:
            beri, pisi = os.pipe()
            self._xvfb = subprocess.Popen(
                [xvfb, "-displayfd", str(pisi), "-screen", "0", "1366x900x24", "-nolisten", "tcp"],
                pass_fds=(pisi,), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, start_new_session=True)
            os.close(pisi)
            try:
                if not select.select([beri], [], [], 10)[0]:
                    raise NapakaBrskalnika("Xvfb ne pove zaslona v 10 s")
                st = os.read(beri, 32).decode().strip()
            finally:
                os.close(beri)
            if not st.isdigit():
                raise NapakaBrskalnika("Xvfb se ne zažene")
            env["DISPLAY"] = f":{st}"
            env.pop("WAYLAND_DISPLAY", None)
            self._zapisi(zaslon=f"Xvfb :{st}")
            return ["--ozone-platform=x11"]
        if env.get("DISPLAY"):
            self._zapisi(zaslon=f"zaslon {env['DISPLAY']} (okno)")
            return []
        if env.get("WAYLAND_DISPLAY"):
            self._zapisi(zaslon="Wayland (okno)")
            return []
        raise NapakaBrskalnika("ni zaslona: namesti Xvfb (deploy/brskalnik.sh)")

    def _zazeni(self) -> None:
        chrome = najdi_chrome()
        self._zapisi(pot=chrome)
        if not chrome:
            raise NapakaBrskalnika("ni Chroma: namesti Google Chrome (deploy/brskalnik.sh)")
        env = dict(os.environ)
        argumenti = self._zaslon(env)
        # Prazen profil ob vsakem zagonu: po prekinjenem Chromu stanje za
        # obnovo zavihkov ustavi naslednji zagon (9. 10. 2026, dvakrat).
        shutil.rmtree(self._profil, ignore_errors=True)
        self._profil.mkdir(parents=True, exist_ok=True)
        port = _prosta_vrata()
        self._chrome = subprocess.Popen(
            [chrome, *argumenti, f"--remote-debugging-port={port}", f"--user-data-dir={self._profil}",
             "--no-first-run", "--no-default-browser-check", "--password-store=basic",
             "--mute-audio", "--window-size=1366,900",
             # Stran mora teči naprej tudi pomanjšana ali prekrita.
             "--disable-renderer-backgrounding", "--disable-background-timer-throttling",
             "--disable-backgrounding-occluded-windows", "about:blank"],
            env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, start_new_session=True)
        konec = time.monotonic() + ZAGON_S
        while True:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=5) as r:
                    naslov = json.load(r)["webSocketDebuggerUrl"]
                ws = _Ws(port, "/" + naslov.split("/", 3)[3])
                break
            except (OSError, ValueError, KeyError, NapakaBrskalnika):
                if self._chrome.poll() is not None:
                    raise NapakaBrskalnika(f"Chrome se je ustavil ob zagonu (koda {self._chrome.returncode})")
                if time.monotonic() > konec:
                    raise NapakaBrskalnika(f"Chrome ne odpre vrat v {ZAGON_S} s")
                time.sleep(0.2)
        self._cdp = _Cdp(ws)
        razlicica = self._cdp.ukaz("Browser.getVersion", cas=ZAGON_S).get("product")
        cilji = self._cdp.ukaz("Target.getTargets").get("targetInfos", [])
        self._cilj = next((t["targetId"] for t in cilji if t.get("type") == "page"), None)
        if self._cilj is None:
            self._cilj = self._cdp.ukaz("Target.createTarget", url="about:blank")["targetId"]
        self._seja = self._cdp.ukaz("Target.attachToTarget", targetId=self._cilj,
                                    flatten=True)["sessionId"]
        self._zapisi(razlicica=razlicica, od_ts=int(time.time()),
                     zagonov=self._s["zagonov"] + 1)

    def _izvedi(self, izraz: str, cas: float):
        r = self._cdp.ukaz("Runtime.evaluate", seja=self._seja, cas=cas, expression=izraz,
                           returnByValue=True, awaitPromise=True)
        if "exceptionDetails" in r:
            d = r["exceptionDetails"]
            opis = d.get("exception", {}).get("description") or d.get("text")
            raise NapakaBrskalnika(f"napaka v strani: {str(opis)[:150]}")
        return r.get("result", {}).get("value")

    def _prebij(self) -> None:
        """Naloži začetno stran in počakaj, da izziv mine."""
        t0 = time.monotonic()
        r = self._cdp.ukaz("Page.navigate", seja=self._seja, cas=PREBOJ_S, url=ZACETNA)
        if r.get("errorText"):
            raise NapakaBrskalnika(f"potniski.sz.si se ne naloži: {r['errorText']}")
        while time.monotonic() - t0 < PREBOJ_S:
            time.sleep(0.5)
            try:
                if self._izvedi(_NALOZENA_JS, 10):
                    self._zapisi(preboji=self._s["preboji"] + 1, zadnji_preboj_ts=int(time.time()),
                                 zadnji_preboj_s=round(time.monotonic() - t0, 1))
                    return
            except NapakaBrskalnika:
                # Med preusmeritvijo izziva kontekst strani izgine; poskusi znova.
                if self._cdp.zaprt:
                    raise
        raise _Izziv(f"Cloudflare ne spusti: izziv ni rešen v {PREBOJ_S} s", http=403)

    def _fetch(self, pot: str, cas: float) -> str:
        ms = int(cas * 1000) - 2000
        izraz = f"""(async () => {{
          const c = new AbortController(), t = setTimeout(() => c.abort(), {ms});
          try {{
            const r = await fetch({json.dumps(pot)}, {{cache: "no-store", credentials: "same-origin", signal: c.signal}});
            return {{status: r.status, besedilo: await r.text()}};
          }} catch (e) {{
            return {{napaka: String(e)}};
          }} finally {{ clearTimeout(t); }}
        }})()"""
        v = self._izvedi(izraz, cas)
        if not isinstance(v, dict):
            raise NapakaBrskalnika("stran ni vrnila odgovora")
        if v.get("napaka"):
            raise NapakaBrskalnika(f"potniski.sz.si: {v['napaka'][:150]}")
        status, besedilo = v.get("status"), v.get("besedilo") or ""
        if status in (403, 429, 503) and je_izziv(besedilo):
            raise _Izziv(f"Cloudflare izziv ({status})", http=status)
        if not status or status >= 400:
            raise NapakaBrskalnika(f"odgovori {status}", http=status)
        return besedilo

    def _ugasni(self) -> None:
        if self._cdp is not None:
            self._cdp.zapri()
        _ustavi_skupino(self._chrome)
        _ustavi_skupino(self._xvfb)
        self._chrome = self._xvfb = self._cdp = self._seja = None


_en: Brskalnik | None = None
_en_kljuc = threading.Lock()


def brskalnik() -> Brskalnik:
    global _en
    with _en_kljuc:
        if _en is None:
            _en = Brskalnik()
        return _en


def zahtevaj(pot: str, cas: float = ZAHTEVA_S) -> str:
    return brskalnik().zahtevaj(pot, cas)


def stanje() -> dict | None:
    """Za /admin. None, dokler ga nihče ni rabil."""
    return _en.stanje() if _en is not None else None


def ustavi() -> None:
    if _en is not None:
        _en.ustavi()


def pocitek_s() -> float:
    return _en.pocitek_s() if _en is not None else 0.0


# Niti so `daemon`: ob koncu procesa ne pridejo do `finally`, Chrome pa bi
# brez tega ostal sirota s svojim Xvfb.
atexit.register(ustavi)
