#!/usr/bin/env python3
"""Posnetki strani /o-nas z WebGL prek CDP (brezglavi chromium, SwiftShader).

  python posnetek.py URL --size 412x860 --mobile --shots 0,0.1,0.5 --out pre
  python posnetek.py URL --eval "izraz"       # izpiše rezultat

URL je navadno `http://127.0.0.1:8001/o-nas?dpr=1` (`dpr` = stalna
ločljivost, sicer se prilagaja hitrosti). Stran pred posnetkom počaka na
`window.__pripravljen`. Posnetek `x` je delež drsenja (0..1), `T=<čas filma>`
(prek `window.__film.pojdi(T)`), `Y=<px>` (drsenje v pikslih) ali
`P=T:px:py:pz:cx:cy:cz:f` (lastna kamera, za pregled modelov od blizu).
Posnetki gredo v posnetki/ (v .gitignore). Izpiše napake konzole.

Rabi paket `websockets`, ki ga projekt sicer nima: poženi iz svojega venv-a.
SwiftShader je počasen, ~20 s na kader.
"""
import argparse, asyncio, base64, json, pathlib, subprocess, time
import urllib.request
import websockets

TU = pathlib.Path(__file__).resolve().parent
POSNETKI = TU.parent / "posnetki"
PROFIL = POSNETKI / "cdp-profil"


async def main():
    a = argparse.ArgumentParser()
    a.add_argument("url")
    a.add_argument("--size", default="412x860")
    a.add_argument("--dpr", type=float, default=1)
    a.add_argument("--mobile", action="store_true")
    a.add_argument("--shots", default="")
    a.add_argument("--out", default="p")
    a.add_argument("--eval", default=None)
    a.add_argument("--frames", type=int, default=6)
    a.add_argument("--timeout", type=float, default=60)
    a.add_argument("--port", type=int, default=9333)
    o = a.parse_args()
    w, h = map(int, o.size.split("x"))
    PROFIL.mkdir(parents=True, exist_ok=True)
    p = subprocess.Popen([
        "chromium", "--headless=new", f"--remote-debugging-port={o.port}",
        f"--user-data-dir={PROFIL}", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
        "--ignore-gpu-blocklist", "--hide-scrollbars", "--no-first-run",
        f"--window-size={w},{h}", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    napake = []
    try:
        ws_url = None
        for _ in range(100):
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{o.port}/json"))
                ws_url = next(t["webSocketDebuggerUrl"] for t in tabs if t["type"] == "page")
                break
            except Exception:
                time.sleep(0.1)
        async with websockets.connect(ws_url, max_size=2**29) as ws:
            n = 0
            pending = {}

            async def bralec():
                try:
                    async for m in ws:
                        d = json.loads(m)
                        if "id" in d and d["id"] in pending:
                            pending.pop(d["id"]).set_result(d)
                        elif d.get("method") == "Runtime.consoleAPICalled":
                            pr = d["params"]
                            if pr["type"] in ("error", "warning", "log"):
                                napake.append(pr["type"] + ": " + " ".join(
                                    str(x.get("value", x.get("description", ""))) for x in pr["args"]))
                        elif d.get("method") == "Runtime.exceptionThrown":
                            napake.append("izjema: " + json.dumps(d["params"]["exceptionDetails"])[:900])
                        elif d.get("method") == "Inspector.targetCrashed":
                            napake.append("STRAN SE JE SESULA")
                except Exception as e:
                    napake.append(f"bralec: {e!r}"[:300])

            asyncio.create_task(bralec())

            async def cmd(method, **params):
                nonlocal n
                n += 1
                f = asyncio.get_event_loop().create_future()
                pending[n] = f
                await ws.send(json.dumps({"id": n, "method": method, "params": params}))
                r = await asyncio.wait_for(f, o.timeout)
                if "error" in r:
                    raise RuntimeError(f"{method}: {r['error']}")
                return r.get("result", {})

            async def ev(expr, await_promise=True):
                r = await cmd("Runtime.evaluate", expression=expr, awaitPromise=await_promise,
                              returnByValue=True)
                if "exceptionDetails" in r:
                    raise RuntimeError(json.dumps(r["exceptionDetails"])[:800])
                return r["result"].get("value")

            try:
                await cmd("Runtime.enable")
                await cmd("Page.enable")
                await cmd("Inspector.enable")
                await cmd("Emulation.setDeviceMetricsOverride", width=w, height=h,
                          deviceScaleFactor=o.dpr, mobile=o.mobile)
                if o.mobile:
                    await cmd("Emulation.setTouchEmulationEnabled", enabled=True)
                await cmd("Page.navigate", url=o.url)
                t0 = time.time()
                while time.time() - t0 < o.timeout:
                    try:
                        if await ev("!!window.__pripravljen"):
                            break
                    except Exception:
                        pass
                    await asyncio.sleep(0.25)
                else:
                    print("NI PRIPRAVLJENA v", o.timeout, "s")
                print(f"pripravljena v {time.time() - t0:.1f} s")
                if o.eval:
                    print(json.dumps(await ev(o.eval), ensure_ascii=False, indent=1)[:4000])
                for s in [x for x in o.shots.split(",") if x]:
                    if s.startswith("T="):
                        await ev(f"window.__film.pogled&&window.__film.pogled(null);window.__film.pojdi({float(s[2:])})")
                    elif s.startswith("P="):
                        # P=T:px:py:pz:cx:cy:cz:f  (lastna kamera)
                        v = [float(x) for x in s[2:].split(":")]
                        await ev(f"window.__film.pojdi({v[0]});window.__film.pogled([{v[1]},{v[2]},{v[3]}],[{v[4]},{v[5]},{v[6]}],{v[7] if len(v) > 7 else 40})")
                    elif s.startswith("Y="):
                        await ev(f"(()=>{{scrollTo(0,{float(s[2:])});window.__film&&window.__film.skoci&&window.__film.skoci();}})()")
                    else:
                        await ev(f"(()=>{{const m=document.documentElement.scrollHeight-innerHeight;"
                                 f"scrollTo(0,{float(s)}*m);window.__film&&window.__film.skoci&&window.__film.skoci();}})()")
                    await ev("new Promise(r=>{let k=%d;const f=()=>--k?requestAnimationFrame(f):r();requestAnimationFrame(f)})" % o.frames)
                    r = await cmd("Page.captureScreenshot", format="png")
                    f = POSNETKI / f"s-{o.out}-{s.replace('=', '').replace(':', '_')[:40]}.png"
                    f.write_bytes(base64.b64decode(r["data"]))
                    print("posnetek", f.name)
            except Exception as e:
                print("NAPAKA", repr(e)[:600])
            await asyncio.sleep(0.2)
    finally:
        for x in napake[:40]:
            print(x[:900])
        p.terminate()
        try:
            p.wait(5)
        except Exception:
            p.kill()


asyncio.run(main())
