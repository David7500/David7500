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

**Kolo ali rolka je ista pot, hitreje prevožena** (`pri_hitrosti()`). Pot
ostane peš pot — kolesarskega profila usmerjevalnik nima, in za "koliko do
postaje" je razlika majhna: pločnik in kolesarska steza tečeta ob isti cesti.
Kjer peš pot gre čez stopnice, jo bo kolesar obšel; tega ne računamo.
"""

from __future__ import annotations

import time

import requests

from . import config, geo

#: Hitrost hoje. Ista v obeh virih -- glej opombo v glavi modula.
KMH = 5.0
HITROST_MS = KMH * 1000 / 3600

#: Kolo, rolka ali tek. Ena sama druga hitrost in ne drsnik: potnik ve, ali ima
#: s sabo kolo, ne pa, koliko km/h vozi. 15 km/h je mestna vožnja s semaforji.
KOLO_KMH = 15.0


def pri_hitrosti(sekunde: int | None, kmh: float = KMH) -> int | None:
    """Sekunde peš poti, prevožene s hitrostjo `kmh`. Pot je ista, čas ne."""
    if sekunde is None:
        return None
    return sekunde if kmh == KMH else round(sekunde * KMH / kmh)

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


def doseg_zracno(sekund: float, kmh: float = KMH) -> float:
    """Polmer v metrih, ki ga v danem času ni mogoče preseči — za predfilter.

    Faktorja tu **ne sme biti**. Zračna črta je vedno krajša ali enaka pravi
    poti, zato ta polmer ne izpusti ničesar dosegljivega; z faktorjem bi tiho
    odrezal postajališča, ki so v resnici v dosegu, in tega ne bi nihče opazil.
    """
    return sekund * kmh / 3.6


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


def pot(lat1: float, lon1: float, lat2: float, lon2: float,
        koraki: bool = False) -> dict | None:
    """Ena pešpot z **geometrijo**: `{"sekunde", "metri", "tocke": [[lat,lon]]}`.

    Matrika pove samo, koliko časa hodiš; ta pove **kod**. Rabi jo podrobni
    prikaz poti, kjer je vprašanje "kako pridem do postajališča" in je odgovor
    črta na zemljevidu, ne številka.

    `koraki=True` doda še navodila za vodenje (`navodilo()`): kje zaviti in
    kam. Brez njih je vodenje samo črta, ki ji mora človek slediti z očmi.

    `None`, kadar usmerjevalnika ni — takrat prikaz nariše ravno črto in to
    tudi pove, namesto da bi trdil pot, ki je ni.
    """
    global _zadnja_napaka
    if not config.OSRM_URL:
        return None
    if time.monotonic() - _zadnja_napaka < _NAPAKA_MIRUJ_S:
        return None
    try:
        r = requests.get(
            f"{config.OSRM_URL}/route/v1/foot/"
            f"{lon1:.6f},{lat1:.6f};{lon2:.6f},{lat2:.6f}",
            params={"overview": "full", "geometries": "geojson",
                    "steps": "true" if koraki else "false"},
            timeout=_TIMEOUT_S)
        r.raise_for_status()
        poti = r.json().get("routes") or []
        if not poti:
            return None
        naj = poti[0]
        # OSRM piše [lon, lat], Leaflet bere [lat, lon]. Zamenjava tu in ne v
        # brskalniku: obrnjena koordinata je napaka, ki je na zemljevidu videti
        # kot pot nekje v Somaliji, in nihče je ne pripiše temu mestu.
        tocke = [[c[1], c[0]] for c in naj["geometry"]["coordinates"]]
        # Usmerjevalnik začne pot na najbližji poti, ne na vratih ali
        # postajališču: hiša je sredi parcele, postajališče na pločniku. Brez
        # priključka na obeh koncih je bila črta na zemljevidu pretrgana --
        # obroč postajališča je stal ob koncu poti, ne na njem (23. 9. 2026).
        # Čas ostane usmerjevalnikov; priključek je nekaj korakov.
        zacetek = geo.haversine(lat1, lon1, *tocke[0]) if tocke else 0
        if zacetek > 2:
            tocke.insert(0, [lat1, lon1])
        if tocke and geo.haversine(lat2, lon2, *tocke[-1]) > 2:
            tocke.append([lat2, lon2])
        out = {"sekunde": round(naj["duration"]), "metri": round(naj["distance"]),
               "tocke": tocke}
        if koraki:
            out["koraki"] = []
            # Koraki štejejo od začetka črte, ta pa zdaj vključuje priključek.
            prevozeno = zacetek if zacetek > 2 else 0.0
            for noga in naj.get("legs", ()):
                for k in noga.get("steps", ()):
                    n = navodilo(k)
                    n["od_zacetka"] = round(prevozeno)
                    out["koraki"].append(n)
                    prevozeno += k.get("distance", 0)
    except Exception:
        _zadnja_napaka = time.monotonic()
        return None
    return out


# ---------------------------------------------------------------- navodila

_SMER = {"left": "levo", "right": "desno",
         "slight left": "rahlo levo", "slight right": "rahlo desno",
         "sharp left": "ostro levo", "sharp right": "ostro desno",
         "straight": "naravnost", "uturn": "nazaj"}

#: Stran neba v mestniku: "pojdi proti severu". Osem, ker je na začetku poti
#: to edino, kar lahko rečemo -- ulice, po kateri greš, pogosto nima imena.
_STRAN_NEBA = ("severu", "severovzhodu", "vzhodu", "jugovzhodu",
               "jugu", "jugozahodu", "zahodu", "severozahodu")


def navodilo(korak: dict) -> dict:
    """En OSRM-ov korak kot navodilo: `{znak, besedilo, ulica, metri, ll}`.

    **Ime ulice ostane v imenovalniku in stoji posebej** ("Levo · Trubarjeva
    cesta"), ne v stavku ("zavij levo na Trubarjevo cesto"). Sklanjati imena
    ne znamo splošno in napačen sklon je slabši od nobenega -- isto pravilo
    kot pri imenih postaj.

    `znak` je ključ za puščico na zaslonu; besedilo je za tiste, ki je ne vidijo
    (in za bralnik zaslona).
    """
    m = korak.get("maneuver") or {}
    tip = m.get("type", "")
    smer = m.get("modifier")
    beseda = _SMER.get(smer, "naravnost")
    znak = beseda.replace(" ", "-")
    if tip == "depart":
        znak = "start"
        besedilo = "Pojdi proti " + _STRAN_NEBA[round(m.get("bearing_after", 0) / 45) % 8]
    elif tip == "arrive":
        znak = "cilj"
        besedilo = "Na cilju"
    elif tip in ("roundabout", "rotary", "roundabout turn"):
        znak = "krozisce"
        izvoz = m.get("exit")
        besedilo = f"V krožišču {izvoz}. izvoz" if izvoz else "Skozi krožišče"
    elif tip in ("exit roundabout", "exit rotary"):
        besedilo = "Zapusti krožišče"
    elif beseda == "nazaj":
        besedilo = "Obrni se"
    elif beseda == "naravnost":
        besedilo = "Naravnost"
    elif tip == "fork":
        besedilo = f"Na razcepu {beseda}"
    elif tip == "end of road":
        besedilo = f"Na koncu ceste {beseda}"
    else:
        besedilo = f"Zavij {beseda}" if " " not in beseda else beseda.capitalize()
    lon, lat = (m.get("location") or [None, None])[:2]
    return {"znak": znak, "besedilo": besedilo, "ulica": korak.get("name") or "",
            "metri": round(korak.get("distance", 0)),
            "sekunde": round(korak.get("duration", 0)),
            "ll": [lat, lon] if lat is not None else None}


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
