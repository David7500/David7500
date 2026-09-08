"""Koliko časa hodiš. Ena funkcija, dva vira — nihče drug ne ve, kateri je bil.

**Zakaj ne zračna razdalja s faktorjem.** Izmerjeno na 1 080 poteh (naključne
točke po Sloveniji do njihovih najbližjih postajališč, primerjava s pravo
pešpotjo): mediana obvoza 1,43, p75 1,83, p90 2,63, **največji 7,86**. Obvoz ni
šum, ampak ovire — Sava, proga, avtocesta. Postajališče 300 m stran po zraku je
lahko 1 400 m hoje. Ena konstanta ne more biti hkrati varna in uporabna:
1,45 podceni pot v 48 % primerov, 2,63 pa bi iz 500 m naredila 15 minut.

**Zakaj svoj OSRM in ne javni.** Javni `router.project-osrm.org` bi ob vsakem
iskanju izvedel, kje potnik stoji in kam gre. Je tudi izrecno „samo za demo".
Program je odprta koda in naš strežnik vrne **isto pot do decimalke** (412,8 m
na preizkusni poti) — omejitev je bila gostiteljeva, ne programova.
Postavitev: `deploy/osrm.sh`.

**Zakaj je hitrost samo ena.** OSRM-ov peš profil hodi 5,00 km/h (izmerjeno na
1 080 poteh), kar je natanko hitrost, s katero računa zasilna pot. Vira se
torej razlikujeta v dolžini poti, ne v hitrosti hoje.
"""

from __future__ import annotations

import time

import requests

from . import config, geo

#: Hitrost hoje. Ista v obeh virih -- glej opombo v glavi modula.
HITROST_MS = 5000 / 3600

#: Zasilni faktor obvoza, kadar usmerjevalnika ni. To je **p75** izmerjene
#: porazdelitve, ne mediana: brez usmerjevalnika ne vemo, kako dolga je pot, in
#: takrat velja isto pravilo kot pri budilki -- potnik ne sme zamuditi, raje
#: kaj rezerve. Z mediano (1,43) bi bila vsaka druga hoja podcenjena in potnik
#: bi avtobus zamudil; s p75 se v najslabšem primeru pokaže malo poznejša
#: povezava, kar je nesreča drugega reda.
FAKTOR = 1.85

#: Hoja je na kritični poti odgovora, ne postranski vir. Izmerjeno je matrika
#: 1 x 70 ciljev 32 ms, torej je ta meja stokratna rezerva -- postavljena je
#: proti obvisenju, ne proti počasnosti.
_TIMEOUT_S = 3.0

#: Ko usmerjevalnik pade, ne poskušamo znova ob vsaki zahtevi: dva klica na
#: iskanje x 3 s pomenita 6 s čakanja na odgovor, ki bo tako ali tako zasilen.
_NAPAKA_MIRUJ_S = 30.0
_zadnja_napaka = 0.0

OSRM = "osrm"
ZRAK = "zrak"


def doseg_zracno(sekund: float) -> float:
    """Polmer v metrih, ki ga v danem času ni mogoče preseči — za predfilter.

    Faktorja tu **ne sme biti**. Zračna črta je vedno krajša ali enaka pravi
    poti, zato ta polmer ne izpusti ničesar dosegljivega; z faktorjem bi tiho
    odrezal postajališča, ki so v resnici v dosegu, in tega ne bi nihče opazil.
    """
    return sekund * HITROST_MS


def _zracno(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    return round(geo.haversine(lat1, lon1, lat2, lon2) * FAKTOR / HITROST_MS)


def _tabela(lat: float, lon: float, cilji: list[tuple[float, float]],
            smer: str) -> list[int | None] | None:
    """Klic OSRM; `None`, kadar vira ni ali ni odgovoril."""
    global _zadnja_napaka
    if not config.OSRM_URL:
        return None
    if time.monotonic() - _zadnja_napaka < _NAPAKA_MIRUJ_S:
        return None

    # Točka je vedno koordinata 0; cilji ji sledijo.
    koord = ";".join([f"{lon:.6f},{lat:.6f}"]
                     + [f"{b:.6f},{a:.6f}" for a, b in cilji])
    # Smer je pomembna: peš profil sicer ne pozna enosmernih cest, a `oneway:foot`
    # obstaja in simetrije ne gre privzeti, kadar je ni treba.
    kljuc = "sources" if smer == "od" else "destinations"
    try:
        r = requests.get(f"{config.OSRM_URL}/table/v1/foot/{koord}",
                         params={kljuc: "0", "annotations": "duration"},
                         timeout=_TIMEOUT_S)
        r.raise_for_status()
        vrstice = r.json()["durations"]
        sekunde = vrstice[0] if smer == "od" else [v[0] for v in vrstice]
    except Exception:
        _zadnja_napaka = time.monotonic()
        return None
    # Prva je pot do sebe; ostale so cilji po vrsti.
    sekunde = sekunde[1:]
    if len(sekunde) != len(cilji):
        _zadnja_napaka = time.monotonic()
        return None
    return [None if s is None else round(s) for s in sekunde]


def matrika(lat: float, lon: float, cilji: list[tuple[float, float]],
            smer: str = "od") -> tuple[list[int | None], str]:
    """Sekunde hoje med točko in vsakim ciljem, ter vir številke.

    `smer="od"` je od točke do ciljev (pot na postajo), `"do"` obratno (pot s
    postaje na cilj). Vir je `"osrm"` ali `"zrak"` in mora priti na zaslon:
    zasilna številka je ocena in se tako tudi imenuje.

    `None` pri posameznem cilju pomeni, da tja peš ni poti.
    """
    if not cilji:
        return [], ZRAK
    sekunde = _tabela(lat, lon, cilji, smer)
    if sekunde is not None:
        return sekunde, OSRM
    return [_zracno(lat, lon, a, b) for a, b in cilji], ZRAK


def sekunde(lat1: float, lon1: float, lat2: float, lon2: float,
            smer: str = "od") -> tuple[int | None, str]:
    """Ena pot; za več ciljev vzemi `matrika()`, ki jih zna v enem klicu."""
    vrsta, vir = matrika(lat1, lon1, [(lat2, lon2)], smer)
    return vrsta[0], vir


# ---------------------------------------------------------------- peš med postajališči

#: Najdaljši peš prestop, ki ga iskanje ponudi. Šest minut je izbrano po
#: pragovih za prestop, ki že veljajo (vlak 6 min, avtobus 3): daljša hoja ne
#: bi bila prestop, ampak druga pot. Predfilter je zato polmer 500 m po zraku,
#: v katerem je 12 070 parov postajališč; koliko jih po pravi poti ostane, je
#: zapisano v `docs/MERITVE.md`.
MAX_PRESTOP_S = 6 * 60

_PES_CACHE: dict[tuple, dict] = {}


def _sosedje(postaje: list[dict], polmer_m: float) -> dict[str, list[dict]]:
    """Kdo je komu bližje od polmera. Mreža, ker je 10 509^2 = 110 milijonov."""
    celica = polmer_m / 111_320.0
    mreza: dict[tuple[int, int], list[dict]] = {}
    for p in postaje:
        mreza.setdefault((int(p["lat"] / celica), int(p["lon"] / celica)), []).append(p)
    out: dict[str, list[dict]] = {}
    for (gy, gx), kos in mreza.items():
        okolica = [q for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                   for q in mreza.get((gy + dy, gx + dx), ())]
        for p in kos:
            blizu = [q for q in okolica
                     if q["stop_id"] != p["stop_id"]
                     and geo.haversine(p["lat"], p["lon"], q["lat"], q["lon"]) <= polmer_m]
            if blizu:
                out[p["stop_id"]] = blizu
    return out


def zgradi_pespoti(conn, znova: bool = False, javi=None) -> dict:
    """Izmeri peš poti med bližnjimi postajališči in jih shrani v `pespot`.

    Teče proti usmerjevalniku in **brez njega ne naredi nič** — ocena po zraku
    se ne sme zapeči v podatke, ker bi jo pozneje nihče ne ločil od meritve.

    Privzeto dopolnjuje: postajališča, ki že imajo vrstice, se preskočijo. Nova
    nastanejo ob uvozu voznega reda in jih je malo, zato je to sekunde dela.
    """
    if znova:
        conn.execute("DELETE FROM pespot")
        conn.commit()

    postaje = [dict(r) for r in conn.execute(
        "SELECT stop_id, lat, lon FROM station WHERE lat IS NOT NULL")]
    sosedje = _sosedje(postaje, doseg_zracno(MAX_PRESTOP_S))
    ze = {r[0] for r in conn.execute("SELECT DISTINCT a_stop FROM pespot")}

    kje = {p["stop_id"]: p for p in postaje}
    novih = 0
    obdelanih = 0
    for stop_id, blizu in sosedje.items():
        if stop_id in ze:
            continue
        p = kje[stop_id]
        sek, vir = matrika(p["lat"], p["lon"], [(q["lat"], q["lon"]) for q in blizu])
        if vir != OSRM:
            raise RuntimeError(
                f"peš usmerjevalnik ({config.OSRM_URL or 'ugasnjen'}) ne odgovarja; "
                "ocene po zraku se v `pespot` ne shranjujejo")
        vrstice = [(stop_id, q["stop_id"], s) for q, s in zip(blizu, sek)
                   if s is not None and s <= MAX_PRESTOP_S]
        conn.executemany(
            "INSERT OR REPLACE INTO pespot(a_stop, b_stop, sekunde) VALUES(?,?,?)",
            vrstice)
        novih += len(vrstice)
        obdelanih += 1
        if javi and obdelanih % 500 == 0:
            javi(f"  {obdelanih} postajališč, {novih} poti")
    conn.commit()
    _PES_CACHE.clear()
    return {"postajalisc": obdelanih, "poti": novih,
            "v_bazi": conn.execute("SELECT COUNT(*) FROM pespot").fetchone()[0]}


def pespoti(conn) -> dict[str, list[tuple[str, int]]]:
    """`{stop_id: [(sosed, sekunde)]}` iz baze, v pomnilniku.

    Ključ predpomnilnika nosi tudi število vrstic: `kajros pespoti` tabelo
    spremeni med tekom strežnika in stara slika bi ostala do ponovnega zagona.
    """
    kje = conn.execute("PRAGMA database_list").fetchone()["file"]
    kljuc = (kje, conn.execute("SELECT COUNT(*) FROM pespot").fetchone()[0])
    v = _PES_CACHE.get(kljuc)
    if v is not None:
        return v
    out: dict[str, list[tuple[str, int]]] = {}
    for a, b, s in conn.execute("SELECT a_stop, b_stop, sekunde FROM pespot"):
        out.setdefault(a, []).append((b, s))
    _PES_CACHE.clear()          # ena slika naenkrat; te so velike in kratkožive
    _PES_CACHE[kljuc] = out
    return out
