#!/usr/bin/env python3
"""Posnetek seznama SŽ: kje ustavi nadomestni avtobus na vsaki postaji.

  python scripts/nadomestna_postajalisca.py              # prenese in zapiše
  python scripts/nadomestna_postajalisca.py --iz tabela.json

SŽ seznam objavlja samo na svoji strani (`nadomestni.VIR`), po progah, z opisom
in povezavo na Googlov zemljevid. Stran je za Cloudflarom: navaden `curl` dobi
403, brezglavi chromium z namiznim `User-Agent` jo odpre (6. 10. 2026). Zato
skripta odpre stran prek CDP kot `o-nas/posnetek.py` in rabi paket
`websockets`, ki ga projekt sicer nima -- poženi jo iz svojega venv-a.

Lega iz povezave ni vedno lega postajališča, zato jo izberemo po zanesljivosti
in preverimo z razdaljo do železniške postaje v naši bazi:

* žebljiček s koordinatami v imenu (`/place/46°03'29.2"N 14°30'49.2"E`) -- točno;
* imenovan kraj (`!3m…!8m2!3d…!4d…`) -- točka, ki jo je SŽ izbrala;
* pot (`/maps/dir/`): od postaje do postajališča ali obratno, zato točka poti,
  ki je od postaje najdlje;
* zaokrožen žebljiček iz podatkov (`!2z…`, tri decimalke): pri Veliki Nedelji
  1,9 km mimo, zato šele za krajem;
* sredina pogleda (`/@lat,lon`) -- samo, če drugega ni.

Točka dlje od `NAJDLJE_M` od postaje (od `PRI_POSTAJI_M`, kadar opis pravi, da
avtobus stoji pri postaji) se zavrže, opis ostane: 6. 10. 2026 sta dve povezavi
kazali na drugo postajo (Paška vas -> Ponikva, 33 km; Velenje Pesje ->
Poljčane, 38 km), ena 1,5 km mimo (Trbonje). Napačna točka je slabša od nobene.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import re
import sqlite3
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

TU = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TU))
from kajros import nadomestni  # noqa: E402

NAJDLJE_M = 700
#: Kadar opis pravi, da avtobus stoji pri postaji, je točka dlje od tega
#: protislovje: Cirkovce in Dobrije („Zunanja stran železniške postaje“) sta
#: 6. 10. 2026 kazali 550 m stran, vse ostale take so v 150 m.
PRI_POSTAJI_M = 300
_PRI_POSTAJI = re.compile(r"zunanja stran železniške postaje|ob železniški postaji", re.I)
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/141.0.0.0 Safari/537.36")

# Tabele po progah: naslov harmonike, nato vrstice [postaja, opis s povezavami].
_JS_TABELE = """(() => [...document.querySelectorAll('table')].map(t => {
  let el = t, naslov = null;
  for (let i = 0; i < 8 && el; i++) {
    el = el.parentElement;
    const b = el && el.querySelector(':scope > button, :scope > h2, :scope > h3, :scope > h4,'
      + ' :scope > [class*=title], :scope > [class*=header]');
    if (b && b.textContent.trim()) { naslov = b.textContent.trim(); break; }
  }
  return {naslov, vrstice: [...t.querySelectorAll('tr')].map(tr => [...tr.querySelectorAll('td,th')]
    .map(c => ({t: c.innerText.trim(), a: [...c.querySelectorAll('a')].map(a => [a.innerText.trim(), a.href])})))};
}))()"""


async def _prenesi(port: int) -> list[dict]:
    import websockets
    profil = TU / "posnetki" / "cdp-sz"
    profil.mkdir(parents=True, exist_ok=True)
    p = subprocess.Popen([
        "chromium", "--headless=new", f"--remote-debugging-port={port}",
        f"--user-data-dir={profil}", "--no-first-run", f"--user-agent={UA}", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ws_url = None
        for _ in range(100):
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json"))
                ws_url = next(t["webSocketDebuggerUrl"] for t in tabs if t["type"] == "page")
                break
            except Exception:
                time.sleep(0.1)
        async with websockets.connect(ws_url, max_size=2**27) as ws:
            n = 0

            async def ukaz(metoda, **par):
                nonlocal n
                n += 1
                await ws.send(json.dumps({"id": n, "method": metoda, "params": par}))
                while True:
                    m = json.loads(await ws.recv())
                    if m.get("id") == n:
                        return m.get("result", {})

            await ukaz("Page.enable")
            await ukaz("Page.navigate", url=nadomestni.VIR)
            for _ in range(60):
                await asyncio.sleep(0.5)
                r = await ukaz("Runtime.evaluate", expression=_JS_TABELE, returnByValue=True)
                tabele = r.get("result", {}).get("value") or []
                if tabele:
                    return tabele
        raise SystemExit("na strani ni tabel -- Cloudflare ali nova oblika strani")
    finally:
        p.terminate()


def _razresi(url: str) -> str:
    """Kratka povezava (maps.app.goo.gl) -> polni naslov z lego, brez obiska cilja."""
    if "goo.gl" not in url:
        return url

    class Ne(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    try:
        urllib.request.build_opener(Ne).open(urllib.request.Request(url, method="HEAD"), timeout=20)
    except urllib.error.HTTPError as e:
        return e.headers.get("Location") or url
    return url


def _dms(s: str):
    m = re.match(r"(\d+)°(\d+)'([\d.]+)\"([NS])\s*\+?(\d+)°(\d+)'([\d.]+)\"([EW])", s)
    if not m:
        return None
    lat = int(m[1]) + int(m[2]) / 60 + float(m[3]) / 3600
    lon = int(m[5]) + int(m[6]) / 60 + float(m[7]) / 3600
    return (lat if m[4] == "N" else -lat, lon if m[8] == "E" else -lon)


def _razd(a, b) -> float:
    f1, f2 = math.radians(a[0]), math.radians(b[0])
    h = (math.sin((f2 - f1) / 2) ** 2
         + math.cos(f1) * math.cos(f2) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2)
    return 2 * 6371000 * math.asin(math.sqrt(h))


def tocka(url: str, postaja: tuple[float, float] | None) -> tuple[tuple[float, float] | None, str]:
    """Lega postajališča iz Googlove povezave in kako zanesljivo jo poznamo."""
    u = urllib.parse.unquote(url).replace("+", " ")
    pot, _, data = u.partition("/data=")
    if "/maps/place/" in pot:
        p = _dms(pot.split("/maps/place/")[1].split("/")[0])
        if p:
            return p, "žebljiček"
    kraj = re.search(r"!3m\d+(?:!1s[^!]*)?!8m2!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", data)
    if "/maps/dir/" in pot:
        imenovane = iter((float(m[2]), float(m[1]))
                         for m in re.finditer(r"!2m2!1d(-?\d+\.\d+)!2d(-?\d+\.\d+)", data))
        tocke = []
        for x in pot.split("/maps/dir/")[1].split("/"):
            if x.startswith("@"):
                break
            m = re.fullmatch(r"\s*(-?\d+\.\d+),\s*(-?\d+\.\d+)\s*", x)
            if m:
                tocke.append((float(m[1]), float(m[2])))
            elif x:
                nx = next(imenovane, None)
                if nx:
                    tocke.append(nx)
        if tocke:
            if postaja:
                return max(tocke, key=lambda t: _razd(t, postaja)), "pot"
            return tocke[-1], "pot"
    if kraj:
        return (float(kraj[1]), float(kraj[2])), "kraj"
    pin = re.search(r"!2z[^!]*!8m2!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", data)
    if pin:
        return (float(pin[1]), float(pin[2])), "zaokrožen žebljiček"
    pogled = re.search(r"/@(-?\d+\.\d+),(-?\d+\.\d+),", u)
    if pogled:
        return (float(pogled[1]), float(pogled[2])), "pogled"
    return None, "brez lege"


def _postaje_v_bazi(db: Path) -> dict[str, tuple[float, float]]:
    """Lega železniških postaj po ključu imena; nadomestna postajališča (BUS)
    nosijo ista imena, včasih s pripono „(Železniški)“."""
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    out: dict[str, tuple[float, float]] = {}
    for ime, lat, lon, vlak in c.execute(
            "SELECT st.name, st.lat, st.lon, MAX(t.mode != 'bus') FROM station st "
            "JOIN sched s ON s.stop_id = st.stop_id JOIN trip t ON t.trip_id = s.trip_id "
            "WHERE t.network = 'zeleznica' GROUP BY st.stop_id ORDER BY 4 DESC"):
        out.setdefault(nadomestni.kljuc(ime), (lat, lon))
    return out


def razberi(tabele: list[dict], postaje: dict) -> tuple[list[dict], list[str]]:
    vrstice, opombe = {}, []
    for t in tabele:
        for v in t["vrstice"][1:]:
            if len(v) < 2 or not v[0]["t"]:
                continue
            ime = v[0]["t"].strip()
            k = nadomestni.kljuc(ime)
            if k in vrstice:                 # ista postaja na dveh progah
                continue
            opis = v[1]["t"].split("\n")[0].strip().rstrip(":.").strip()
            pov = next((a[1] for a in v[1]["a"] if "google" in a[1] or "goo.gl" in a[1]), None)
            st = postaje.get(k)
            lega, kako = tocka(_razresi(pov), st) if pov else (None, "brez povezave")
            meja = PRI_POSTAJI_M if _PRI_POSTAJI.search(opis) else NAJDLJE_M
            if lega and st and _razd(lega, st) > meja:
                opombe.append(f"{ime}: {kako} {_razd(lega, st) / 1000:.2f} km od postaje "
                              f"(meja {meja} m) -- zavrženo")
                lega = None
            if not st:
                opombe.append(f"{ime}: postaje ni v voznem redu")
            vrstice[k] = {"postaja": ime, "opis": opis,
                          "lat": round(lega[0], 6) if lega else None,
                          "lon": round(lega[1], 6) if lega else None,
                          "lega": kako if lega else None}
    return sorted(vrstice.values(), key=lambda x: nadomestni.kljuc(x["postaja"])), opombe


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--iz", type=Path, help="že prenesene tabele (JSON) namesto strani")
    a.add_argument("--port", type=int, default=9371)
    a.add_argument("--db", type=Path, default=TU / "data" / "kajros.sqlite")
    o = a.parse_args()
    tabele = json.loads(o.iz.read_text()) if o.iz else asyncio.run(_prenesi(o.port))
    vrstice, opombe = razberi(tabele, _postaje_v_bazi(o.db))
    nadomestni.DATOTEKA.write_text(json.dumps(
        {"vir": nadomestni.VIR, "pregledano": date.today().isoformat(), "postaje": vrstice},
        ensure_ascii=False, indent=1) + "\n")
    z_lego = sum(1 for v in vrstice if v["lat"] is not None)
    print(f"{len(vrstice)} postaj, {z_lego} z lego -> {nadomestni.DATOTEKA}")
    for x in opombe:
        print("  " + x)


if __name__ == "__main__":
    main()
