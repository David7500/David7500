"""Žive vožnje mestnega LPP, ki jih objavljeni vozni red nima.

LPP-jev živi sistem vozi vožnje pod id-ji, ki jih objavljeni vozni red nima:
1. 10. 2026 17 % voženj šestih linij, 2. 10. vsa linija 1, 19. 10. liniji 18
in 18L, 26. 10. vsa linija 27 -- 14 od 15 voženj v feedu. Zajem jih je
zavrgel: zamud ni bilo, zemljevid je pisal „vožnje ni v voznem redu“, tabla
je kazala objavo.

**Kaj o taki vožnji vemo.** Id je `dan|vožnja|vzorec`. Dan in vzorec
poznamo -- vzorec ima vožnje drugih dni --, vožnje ne. 26. 10. so bile ure
ure objavljenih voženj do minute: LPP-jev zaslon jih je pred odhodom kazal
kot načrt (vrsta 1) in vseh 13 je bilo 38-40 s za objavljeno uro (eta je
cela minuta od branja). Drug je bil le vzorec: po Vilharjevi (Navje), objava
pa mimo kolodvora (Kolodvor, Friškovec).

Zato živo vožnjo **pripnemo na objavljeno** z istim načrtom (`ziva_voznja`)
in njena zamuda gre pod objavljeno, kot da bi feed nosil njen id. Dokaz je
eden od dveh:

* **načrt**: LPP-jev zaslon je za vozilo te vožnje pred odhodom kazal uro po
  načrtu na postajališču, kjer ima objavljena vožnja isto uro (`NACRT_S`).
  Zaslone bere `zamude_lpp` in načrte zapiše sem (`zabelezi_nacrt`).
* **ura**: napoved feeda se na skupnih postajališčih z eno objavljeno vožnjo
  ujame na verjetno zamudo (`URA_OKNO_S`), z nobeno drugo pa niti na manj
  verjetno (`URA_TEKMEC_S`). Vožnje po vrsti, najprej tista, ki je začela
  prej; zasedena objavljena ne pride več v poštev. Na 116 znanih vožnjah
  (feed 26. 10., id pozabljen) je bilo tako 68 parov, vsi pravi; ostale so
  na gostih linijah dvoumne in ostanejo brez para -- **brez para ni zamude,
  napačen par pa bi bil zamuda druge vožnje**. Kako se ura ujema z načrtom,
  se meri sproti (`soglasje`).

Živa, ki se najbolje ujame z vožnjo, ki jo že imamo (vozi pod svojim id-jem
ali jo nosi druga živa), je njen **dvojnik** in se ne šteje (`_dvojnik`).

Kadar sparjene vožnje istega dne in proge vozijo drug vzorec kot objavljene,
objavljene **prestavimo na vzorec, ki ga LPP vozi** (`popravi`): postanki iz
vzorca, ure in številke skupnih postajališč ostanejo, vmesne ure iz voznih
časov vzorca. Sparjena vožnja se prestavi takoj, vse ostale tega dne in
vzorca pa, ko to kažeta vsaj dve in nobena ne kaže objave
(`POPRAVEK_DOKAZOV`). Ko LPP objavo spet vozi, se prestavljene brez para
vrnejo (`_vrni`). Tabla, iskalnik in pot vedo, da 27 ustavi na Navju in ne
na Kolodvoru.
"""
from __future__ import annotations

import json
import sqlite3
import statistics
import threading
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from . import config, db, geo, stats

#: Načrt z zaslona in objavljena ura se smeta razlikovati toliko: eta je cela
#: minuta od trenutka branja (26. 10. 2026 13 od 13 načrtov 38-40 s za uro).
NACRT_S = 90
#: Načrt velja, dokler vozilo vožnje ne začne; LPP ga kaže do 60 min naprej.
NACRT_HRANI_S = 3 * 3600
#: Par po načrtu z vožnjo, ki že vozi, velja le pri tolikšni zamudi -- in
#: tudi par, sklenjen pred odhodom, pade, ko napoved pokaže drugače
#: (`_preveri_pare`). Mestni LPP nad uro skoraj ne zamuja (p99 +23 min);
#: prezgodaj je lahko nekaj minut: 26. 10. 2026 je 27 po Vilharjevi, krajši
#: od objavljene poti mimo kolodvora, na Flajšmanovi prišel 6 min pred uro.
NACRT_ZAMUDA_S = (-600, 5400)
#: Vožnja, ki še ni začela, se pripne le na načrt, ki ga je zaslon kazal pred
#: kratkim (`zamude_lpp` bere na 2 min), in na objavljeno vožnjo, ki naj bi
#: začela največ toliko prej.
NACRT_SVEZ_S = 600
#: Ob paru po napovedi mora biti zamuda do najboljše objavljene vožnje v tem
#: oknu, do vseh drugih pa zunaj `URA_TEKMEC_S`. Mestni LPP zamuja malo
#: (mediana 0, p95 +7 min), prezgodaj pa redko več kot nekaj minut.
URA_OKNO_S = (-240, 600)
URA_TEKMEC_S = (-240, 1200)
#: Vožnja je primerljiva z objavljeno, kadar ima ta vsaj tolikšen delež njenih
#: postajališč (26. 10. 27: 19 od 21 po Vilharjevi je bilo tudi v objavi).
SKUPNIH_DELEZ = 0.6
#: Koliko sparjenih voženj mora kazati isti drug vzorec, da se prestavi tudi
#: objavljene vožnje tega dne, ki jih še nihče ni vozil.
POPRAVEK_DOKAZOV = 2
#: Toliko dni pari ostanejo v bazi: zamuda je že pod objavljeno vožnjo, par
#: je le še za pregled (`kajros zive`).
PARI_HRANI_DNI = 14
#: Živa, ki se ujema z vožnjo, ki jo že imamo, je isti avtobus, kadar sta
#: napovedi na skupnih postajališčih tako blizu: 26. 10. 2026 je feed ob
#: liniji 2 iz 16:43 nosil živo brez vozila z njenimi šestimi zadnjimi
#: postanki, 0-5 min pred njeno napovedjo (49 branj).
DVOJNIK_S = 300

NACIN_NACRT = "nacrt"
NACIN_URA = "ura"

#: vozilo -> [(vzorec, stop_id, ura po načrtu, kdaj prebrano)], od `zamude_lpp`.
_nacrti: dict[str, list[tuple[str, str, float, float]]] = {}
_zaklep = threading.Lock()
_pocisceno = 0.0
#: Kako se par po uri ujema s parom po načrtu, kjer sta oba: [enako, drugače].
#: Živo merilo, ali je par po uri zaupanja vreden (`soglasje`).
_soglasje = [0, 0]
_preverjeni: set[str] = set()
#: (baza, značka reda, dan, proga) -> _Skupina; zajem jo rabi vsakih 30 s.
_SKUPINE: dict[tuple, "_Skupina"] = {}
#: (vožnja, živ vzorec), ki se ne da prestaviti (meritve, predloga brez njenega
#: začetka ali konca), za uvoz `_ne_gre_uvoz`: sicer bi jo zajem poskušal
#: vsakih 30 s.
_ne_gre: set[tuple[str, str]] = set()
_ne_gre_uvoz: str | None = None
#: (baza, značka reda, vzorec) -> predloga iz voznega reda (`_predloga_iz_reda`).
_PREDLOGE: dict[tuple, dict | None] = {}


def zabelezi_nacrt(vozilo: str, vzorec: str, stop_id: str, ura: float,
                   prebrano: float) -> None:
    """LPP-jev zaslon je za `vozilo` kazal prihod po načrtu (vrsta 1)."""
    vozilo, vzorec = vozilo.lower(), vzorec.lower()
    with _zaklep:
        stari = _nacrti.get(vozilo, ())
        _nacrti[vozilo] = [n for n in stari if prebrano - n[3] <= NACRT_HRANI_S
                           and not (n[0] == vzorec and n[1] == stop_id)] + [
            (vzorec, stop_id, ura, prebrano)]


def _nacrti_vozila(vozilo: str | None, zdaj: float) -> list[tuple[str, str, float, float]]:
    if not vozilo:
        return []
    with _zaklep:
        return [n for n in _nacrti.get(vozilo, ()) if zdaj - n[3] <= NACRT_HRANI_S]


def _pocisti_nacrte(zdaj: float) -> None:
    with _zaklep:
        for v in [v for v, ns in _nacrti.items()
                  if not any(zdaj - n[3] <= NACRT_HRANI_S for n in ns)]:
            del _nacrti[v]


def soglasje() -> list[int]:
    """[enako, drugače]: par po uri proti paru po načrtu na istih vožnjah."""
    return list(_soglasje)


def _vzorec(trip_id: str) -> str:
    return trip_id.rpartition("|")[2].lower()


def _cas(stu) -> int | None:
    """Absolutni čas postanka iz feeda: odhod, sicer prihod (kot `COALESCE(dep,
    arr)` v voznem redu). Ničla brez časa je LPP-jevo mesto za vožnjo brez
    napovedi (`collector._delay_of`), ne čas."""
    for kaj in ("departure", "arrival"):
        if stu.HasField(kaj) and getattr(stu, kaj).HasField("time"):
            return getattr(stu, kaj).time
    return None


# ---------------------------------------------------------------- pari

def pari(conn: sqlite3.Connection, od_dne: str) -> dict[str, str]:
    """Živa vožnja -> naša, za dneve od `od_dne`."""
    return dict(conn.execute(
        "SELECT ziva, nasa FROM ziva_voznja WHERE service_date >= ?", (od_dne,)).fetchall())


def postanki(conn: sqlite3.Connection, trip_ids) -> dict[str, list[tuple]]:
    """Naša vožnja -> [(stop_seq, stop_id, t_s)] po vrsti; `t_s` = odhod,
    sicer prihod."""
    out: dict[str, list[tuple]] = defaultdict(list)
    ids = list(trip_ids)
    for i in range(0, len(ids), 400):
        kos = ids[i:i + 400]
        for r in conn.execute(
                "SELECT trip_id, stop_seq, stop_id, COALESCE(dep_s, arr_s) FROM sched "
                f"WHERE trip_id IN ({','.join('?' * len(kos))}) ORDER BY trip_id, stop_seq",
                kos):
            out[r[0]].append((r[1], r[2], r[3]))
    return dict(out)


def preslikaj(nasi: list[tuple], zivi: list[tuple], polnoc: int | None = None) -> dict[int, int]:
    """`{stop_seq v feedu: naš stop_seq}` po postajališču, v istem vrstnem redu.

    Po `stop_id` in ne po zaporedni številki: popravljena vožnja ima postanke
    oštevilčene znova, delna vožnja pa lahko šteje od svojega začetka. Kadar
    je postajališče na vožnji dvakrat (krožna linija), odloči ura.
    """
    kje: dict[str, list[int]] = defaultdict(list)
    for i, (_, sid, _t) in enumerate(nasi):
        kje[sid].append(i)
    out: dict[int, int] = {}
    j = 0
    for zseq, sid, cas in sorted(zivi, key=lambda z: z[0]):
        moznosti = [i for i in kje.get(sid, ()) if i >= j]
        if not moznosti:
            continue
        i = moznosti[0]
        if len(moznosti) > 1 and cas is not None and polnoc is not None:
            z_uro = [k for k in moznosti if nasi[k][2] is not None]
            if z_uro:
                i = min(z_uro, key=lambda k: abs(cas - polnoc - nasi[k][2]))
        out[zseq] = nasi[i][0]
        j = i + 1
    return out


def _zive_iz_feeda(feed, znane) -> dict[str, dict]:
    """Vožnje iz feeda, ki jih ne poznamo: proga, postanki, vozilo."""
    out: dict[str, dict] = {}
    for e in feed.entity:
        if not e.HasField("trip_update"):
            continue
        tu = e.trip_update
        tid = tu.trip.trip_id
        if not tid or tid in znane or tid.count("|") != 2:
            continue
        out[tid] = {
            "route": tu.trip.route_id, "dan": tid.split("|", 1)[0], "vzorec": _vzorec(tid),
            "postanki": [(s.stop_sequence, s.stop_id, _cas(s)) for s in tu.stop_time_update],
            "vozilo": tu.vehicle.id.lower() if tu.vehicle.id else None,
        }
    # Vozilo iz lege, kjer je: TripUpdate ga nosi samo, dokler vožnja ni začela.
    for e in feed.entity:
        if e.HasField("vehicle") and e.vehicle.vehicle.id:
            z = out.get(e.vehicle.trip.trip_id)
            if z is not None:
                z["vozilo"] = e.vehicle.vehicle.id.lower()
    return out


def _znane_v_feedu(feed, znane) -> dict[str, dict[str, int]]:
    """Objavljene vožnje, ki jih feed nosi pod njihovim id-jem, z napovedjo
    (`_napovedi`; prazna, dokler vožnja ni začela)."""
    out = {}
    for e in feed.entity:
        if e.HasField("trip_update") and e.trip_update.trip.trip_id in znane:
            out[e.trip_update.trip.trip_id] = _napovedi({"postanki": [
                (s.stop_sequence, s.stop_id, _cas(s)) for s in e.trip_update.stop_time_update]})
    return out


class _Skupina:
    """Objavljene vožnje enega dne ene proge mestnega LPP."""

    def __init__(self, conn: sqlite3.Connection, dan_id: str, route_id: str):
        r = conn.execute("SELECT date FROM service_day WHERE service_id = ? LIMIT 1",
                         (dan_id,)).fetchone()
        self.dan = r[0] if r else None
        self.polnoc = stats.polnoc(self.dan) if self.dan else None
        self.voznje: dict[str, dict] = {}
        #: stop_id -> vožnje, ki tam ustavijo (za `primerljive`).
        self.po_postaji: dict[str, list[str]] = defaultdict(list)
        if self.dan is None:
            return
        for r in conn.execute(
                "SELECT t.trip_id, t.start_s, t.end_s, s.stop_seq, s.stop_id, "
                "       COALESCE(s.dep_s, s.arr_s) "
                "FROM trip t JOIN sched s ON s.trip_id = t.trip_id "
                "WHERE t.route_id = ? AND t.service_id = ? AND t.agency = 'lpp' "
                "  AND t.start_s IS NOT NULL ORDER BY t.trip_id, s.stop_seq",
                (route_id, dan_id)):
            v = self.voznje.setdefault(r[0], {"start": r[1], "end": r[2], "ure": {}})
            if r[5] is not None and r[4] not in v["ure"]:
                v["ure"][r[4]] = r[5]
                self.po_postaji[r[4]].append(r[0])

    def primerljive(self, postajalisca) -> list[str]:
        """Objavljene vožnje z vsaj `SKUPNIH_DELEZ` teh postajališč."""
        nabor = set(postajalisca)
        if not nabor:
            return []
        meja = max(2, SKUPNIH_DELEZ * len(nabor))
        stevec: Counter = Counter()
        for s in nabor:
            stevec.update(self.po_postaji.get(s, ()))
        return sorted(t for t, n in stevec.items() if n >= meja)

    def zamuda(self, tid: str, napovedi: dict[str, int]) -> float | None:
        """Napoved minus vozni red na skupnih postajališčih (mediana), v s."""
        ure = self.voznje[tid]["ure"]
        razlike = [t - self.polnoc - ure[s] for s, t in napovedi.items() if s in ure]
        return statistics.median(razlike) if razlike else None


def _skupina(conn: sqlite3.Connection, dan_id: str, route_id: str) -> _Skupina:
    kljuc = (db.cache_key(conn), dan_id, route_id)
    if kljuc[0] is None:
        return _Skupina(conn, dan_id, route_id)
    sk = _SKUPINE.get(kljuc)
    if sk is None:
        for k in [k for k in _SKUPINE if k[0] != kljuc[0]]:
            _SKUPINE.pop(k, None)
        sk = _SKUPINE[kljuc] = _Skupina(conn, dan_id, route_id)
    return sk


def _napovedi(ziva: dict) -> dict[str, int]:
    """stop_id -> absolutni čas; pri dvakrat obiskanem postajališču prvi."""
    out: dict[str, int] = {}
    for _, sid, cas in sorted(ziva["postanki"], key=lambda p: p[0]):
        if cas is not None:
            out.setdefault(sid, cas)
    return out


def _po_nacrtu(sk: _Skupina, ziva: dict, kandidatke: list[str], zdaj: float) -> str | None:
    """Objavljena vožnja, ki jo za vozilo te vožnje kaže LPP-jev načrt.

    Načrt (vrsta 1) zaslon kaže le za vožnjo, ki še ni začela. Kadar vozilo
    vožnjo že vozi, je načrt istega vzorca lahko že za njegovo naslednjo
    vožnjo po obratu: 26. 10. 2026 linija 1, načrt za 17:16, vozilo pa na
    vožnji iz 15:41 (64 min) -- velja samo načrt, ki se z napovedjo ujame na
    verjetno zamudo (`NACRT_ZAMUDA_S`). Vožnja, ki še ni začela, je prva, ki
    jo ima vozilo na vrsti: najzgodnejši sveži načrt (`NACRT_SVEZ_S`), ki ni
    začel davno -- starejši je od vožnje, ki jo je vozilo že odpeljalo --, in
    prosta objavljena, ki začne prej, je ne sme biti: tedaj je načrt za
    vozilovo poznejšo (26. 10. 2026 linija SŽ: načrt za 17:55, vozilo pa je
    čakalo na vožnjo ob 17:15, katere načrta zaslon ni kazal).
    """
    napovedi = _napovedi(ziva)
    nasli: set[str] = set()
    for vzorec, sid, ura, prebrano in _nacrti_vozila(ziva["vozilo"], zdaj):
        if vzorec != ziva["vzorec"] or (not napovedi and zdaj - prebrano > NACRT_SVEZ_S):
            continue
        for tid in kandidatke:
            t = sk.voznje[tid]["ure"].get(sid)
            if t is not None and abs(sk.polnoc + t - ura) <= NACRT_S:
                nasli.add(tid)
    if napovedi:
        nasli = {t for t in nasli if (z := sk.zamuda(t, napovedi)) is not None
                 and NACRT_ZAMUDA_S[0] <= z <= NACRT_ZAMUDA_S[1]}
    else:
        nasli = {t for t in nasli if sk.polnoc + sk.voznje[t]["start"] >= zdaj - NACRT_SVEZ_S}
        if nasli:
            prva = min(nasli, key=lambda t: sk.voznje[t]["start"])
            od = zdaj - NACRT_SVEZ_S - sk.polnoc
            if any(od <= sk.voznje[t]["start"] < sk.voznje[prva]["start"] for t in kandidatke):
                return None
            nasli = {prva}
    return next(iter(nasli)) if len(nasli) == 1 else None


def _tocke(z: float) -> float:
    """Kako neverjetna je zamuda: prezgodaj trikrat bolj kot pozno."""
    return z if z >= 0 else -3 * z


def _po_uri(sk: _Skupina, napovedi: dict[str, int], kandidatke: list[str],
            zasedene: set[str] = frozenset()) -> tuple[str, float] | None:
    """(vožnja, zamuda) po napovedi, ali None, kadar par ni nedvoumen.

    Zasedena vožnja (vozi pod svojim id-jem ali jo nosi druga živa) ni
    tekmica -- zanjo je že odločeno. Kadar pa se napoved najbolje ujame prav z
    njo, vrne njo: živa jo ponavlja ali je kateri od parov napačen, in para
    ni (`razresi`).
    """
    ocene = sorted(((z, t) for t in kandidatke
                    if (z := sk.zamuda(t, napovedi)) is not None),
                   key=lambda o: _tocke(o[0]))
    if not ocene or not URA_OKNO_S[0] <= ocene[0][0] <= URA_OKNO_S[1]:
        return None
    if ocene[0][1] not in zasedene and any(
            URA_TEKMEC_S[0] <= z <= URA_TEKMEC_S[1]
            for z, t in ocene[1:] if t not in zasedene):
        return None
    return ocene[0][1], ocene[0][0]


def _dvojnik(napovedi: dict[str, int], nase: dict[str, int] | None) -> bool:
    """Živa, ki se najbolje ujame z zasedeno vožnjo, je isti avtobus, kadar
    zasedena napovedi še nima ali se napovedi na skupnih postajališčih ujemata
    (`DVOJNIK_S`). Sicer je drug avtobus -- vožnja mimo voznega reda."""
    if not nase:
        return True
    razlike = [abs(t - nase[s]) for s, t in napovedi.items() if s in nase]
    return not razlike or statistics.median(razlike) <= DVOJNIK_S


def razresi(conn: sqlite3.Connection, feed, zdaj: float | None = None) -> dict:
    """Pripne žive vožnje iz feeda LPP na objavljene in popravi vzorce.

    Vrne `{"pari": {živa: naša}, "brez_para": {živa: {...}}, "dvojniki":
    {živa}, "stevci": {...}}`. `pari` so vsi pari od včeraj -- zajem z njimi
    prevede zamude in lege (`collector.ingest`, `ingest_positions`).
    `dvojniki` ponavljajo vožnjo, ki jo že imamo: zajem jih preskoči in ne
    šteje. Pisanje potrdi sam.
    """
    from . import collector                 # `collector` uvozi ta modul
    global _pocisceno
    zdaj = time.time() if zdaj is None else zdaj
    danes = datetime.fromtimestamp(zdaj, stats.TZ).date()
    vceraj = (danes - timedelta(days=1)).isoformat()
    znane = collector._rail_trip_windows(conn)
    zamenjave = collector._zamenjave(conn)
    obstojeci = pari(conn, vceraj)
    v_feedu = _znane_v_feedu(feed, znane)
    # Objavljena z napovedjo ali vozilom pod svojim id-jem vozi sama: za par ni
    # na voljo. Sam vnos brez obojega ne pove nič. 26. 10. 2026 je feed linijo
    # SŽ ob 17:55 tako nosil eno uro, vozila pa je vozilo pod drugim id-jem;
    # linijo 2 iz 16:43 pol ure, vozilo je dobila ob 16:33, ob njej pa je bila
    # živa brez vozila s šestimi zadnjimi postanki ob njenih urah (dvojnik).
    sama = {t for t, nap in v_feedu.items() if nap} | {
        e.vehicle.trip.trip_id for e in feed.entity
        if e.HasField("vehicle") and e.vehicle.trip.trip_id in znane}
    zive = {t: z for t, z in _zive_iz_feeda(feed, znane).items() if t not in zamenjave}
    st = {"zivih": len(zive), "sparjenih": 0, "novih": 0, NACIN_NACRT: 0, NACIN_URA: 0,
          "brez_para": 0, "dvojnikov": 0, "popravljenih": 0, "vrnjenih": 0, "zavrzenih": 0}
    if zdaj - _pocisceno > 3600:
        _pocisti_nacrte(zdaj)
        conn.execute("DELETE FROM ziva_voznja WHERE service_date < ?",
                     ((danes - timedelta(days=PARI_HRANI_DNI)).isoformat(),))
        _preverjeni.intersection_update(obstojeci)
        _pocisceno = zdaj
    if not config.ZIVE:
        return {"pari": {}, "brez_para": zive, "dvojniki": set(),
                "stevci": {**st, "brez_para": len(zive)}}

    # Par ne velja, kadar naše vožnje ni več (uvoz ji je dal nov id) ali jo
    # feed nosi pod njenim id-jem z napovedjo ali vozilom -- tedaj vozi sama
    # in živa je druga vožnja. Živa gre znova v par.
    for ziva in [z for z, n in obstojeci.items() if n not in znane or n in sama]:
        conn.execute("DELETE FROM ziva_voznja WHERE ziva = ?", (ziva,))
        del obstojeci[ziva]
        st["zavrzenih"] += 1
    zasedene = set(obstojeci.values()) | sama
    # Najprej stari pari: kar ob prvi napovedi ne drži, pade in gre znova v
    # par. Objavljena, ki vozi pod svojim id-jem, ostane zasedena.
    st["zavrzenih"] += _preveri_pare(conn, zive, obstojeci, zasedene)
    zasedene |= sama
    po_skupinah: dict[tuple[str, str], list[str]] = defaultdict(list)
    for tid, z in zive.items():
        if tid not in obstojeci:
            po_skupinah[(z["dan"], z["route"])].append(tid)
    # Napovedi zasedenih voženj, za dvojnike: feed pod njihovim id-jem ali živa.
    nase = dict(v_feedu)
    for ziva, nasa in obstojeci.items():
        if ziva in zive:
            nase[nasa] = _napovedi(zive[ziva])

    novi: list[tuple] = []
    dvojniki: set[str] = set()
    for (dan_id, proga), ids in po_skupinah.items():
        sk = _skupina(conn, dan_id, proga)
        if sk.dan is None:
            continue
        # Najprej načrt: ta je točen na minuto, napoved pa le verjetna.
        brez = []
        for tid in ids:
            z = zive[tid]
            kand = [t for t in sk.primerljive(p[1] for p in z["postanki"])
                    if t not in zasedene]
            t = _po_nacrtu(sk, z, kand, zdaj)
            if t is None:
                brez.append(tid)
                continue
            napovedi = _napovedi(z)
            zam = sk.zamuda(t, napovedi) if napovedi else None
            novi.append((tid, t, sk.dan, NACIN_NACRT, None if zam is None else round(zam)))
            zasedene.add(t)
            nase[t] = napovedi
        # Nato napoved, po vrsti začetka: prejšnji avtobus vzame prejšnjo vožnjo.
        vrsta = []
        for tid in brez:
            napovedi = _napovedi(zive[tid])
            if len(napovedi) < 2:
                continue
            kand = sk.primerljive(napovedi)
            ocene = [(z, t) for t in kand if (z := sk.zamuda(t, napovedi)) is not None]
            if ocene:
                z, t = min(ocene, key=lambda o: abs(o[0]))
                vrsta.append((sk.voznje[t]["start"] + z, tid, napovedi, kand))
        for _, tid, napovedi, kand in sorted(vrsta):
            izbira = _po_uri(sk, napovedi, kand, zasedene)
            if izbira is None:
                continue
            if izbira[0] in zasedene:
                if _dvojnik(napovedi, nase.get(izbira[0])):
                    dvojniki.add(tid)
                continue
            novi.append((tid, izbira[0], sk.dan, NACIN_URA, round(izbira[1])))
            zasedene.add(izbira[0])
            nase[izbira[0]] = napovedi

    for tid, nasa, dan, nacin, zam in novi:
        if conn.execute(
                "INSERT OR IGNORE INTO ziva_voznja(ziva, nasa, service_date, nacin, zamik_s, ts) "
                "VALUES(?,?,?,?,?,?)", (tid, nasa, dan, nacin, zam, int(zdaj))).rowcount:
            obstojeci[tid] = nasa
            st[nacin] += 1
            st["novih"] += 1

    if config.ZIVE_POPRAVKI:
        st["popravljenih"], st["vrnjenih"] = _popravi_po_dokazih(
            conn, v_feedu, zive, vceraj, zdaj)
    st["sparjenih"] = sum(1 for t in zive if t in obstojeci)
    brez_para = {t: z for t, z in zive.items() if t not in obstojeci and t not in dvojniki}
    st["brez_para"] = len(brez_para)
    st["dvojnikov"] = len(dvojniki)
    conn.commit()
    return {"pari": obstojeci, "brez_para": brez_para, "dvojniki": dvojniki, "stevci": st}


def _preveri_pare(conn: sqlite3.Connection, zive: dict, pari_: dict[str, str],
                  zasedene: set[str]) -> int:
    """Par, sklenjen pred odhodom, ob prvi napovedi: zamuda do naše vožnje
    mora biti verjetna (`NACRT_ZAMUDA_S`), sicer par pade, preden zajem pod
    njim kaj zapiše. Pri paru po načrtu še, kaj bi izbral par po uri
    (`_soglasje`). Enkrat na vožnjo. Vrne število zavrženih parov."""
    zavrzenih = 0
    for tid, z in zive.items():
        nasa = pari_.get(tid)
        if nasa is None or tid in _preverjeni:
            continue
        napovedi = _napovedi(z)
        if len(napovedi) < 2:
            continue
        _preverjeni.add(tid)
        sk = _skupina(conn, z["dan"], z["route"])
        if sk.dan is None or nasa not in sk.voznje:
            continue
        zam = sk.zamuda(nasa, napovedi)
        if zam is None or not NACRT_ZAMUDA_S[0] <= zam <= NACRT_ZAMUDA_S[1]:
            conn.execute("DELETE FROM ziva_voznja WHERE ziva = ?", (tid,))
            del pari_[tid]
            zasedene.discard(nasa)
            zavrzenih += 1
            continue
        r = conn.execute("SELECT nacin FROM ziva_voznja WHERE ziva = ?", (tid,)).fetchone()
        if r is None or r[0] != NACIN_NACRT:
            continue
        kand = [t for t in sk.primerljive(napovedi) if t == nasa or t not in zasedene]
        izbira = _po_uri(sk, napovedi, kand)
        if izbira is not None:
            _soglasje[0 if izbira[0] == nasa else 1] += 1
    return zavrzenih


# ---------------------------------------------------------------- popravki vzorca

def popravljeni(conn: sqlite3.Connection) -> dict[str, str]:
    """Naša vožnja -> vzorec, ki ga LPP vozi, za prestavljene vožnje.

    LPP-jev API (`arrivals-on-route`, zasloni) vožnjo pozna po vzorcu, ki ga
    vozi; tretja komponenta našega id-ja je pri prestavljeni objavljen vzorec,
    ki ga nihče ne vozi.
    """
    from . import collector
    return collector._cached(conn, "popravljeni_vzorci", None, lambda: dict(conn.execute(
        "SELECT trip_id, ziv FROM popravek_vzorca").fetchall()))


def vzorec_lpp(conn: sqlite3.Connection, trip_id: str) -> str | None:
    """Vzorec, pod katerim LPP vozi to vožnjo (`popravljeni`), ali tretja
    komponenta id-ja."""
    deli = trip_id.split("|")
    if len(deli) != 3:
        return None
    return popravljeni(conn).get(trip_id) or deli[2]


def _predloga_iz_reda(conn: sqlite3.Connection, vzorec: str) -> dict | None:
    """Najdaljša vožnja vzorca v voznem redu (drug dan): postanki z voznimi
    časi, trasa, smer. Predpomnjeno do nove značke voznega reda -- iskanje po
    vsej tabeli `trip` bi se sicer ponavljalo vsakih 30 s."""
    kljuc = (db.cache_key(conn), vzorec)
    if kljuc[0] is not None and kljuc in _PREDLOGE:
        return _PREDLOGE[kljuc]
    naj = None
    for r in conn.execute(
            "SELECT t.trip_id, t.shape_id, t.headsign, "
            "       (SELECT COUNT(*) FROM sched s WHERE s.trip_id = t.trip_id) AS n "
            "FROM trip t WHERE t.agency = 'lpp' AND t.start_s IS NOT NULL "
            "  AND t.trip_id LIKE ?", (f"%|{vzorec}",)):
        # Prestavljena vožnja ni predloga: v id-ju nosi objavljen vzorec.
        if _vzorec(r["trip_id"]) == vzorec and (naj is None or r["n"] > naj["n"]):
            naj = dict(r)
    out = None
    if naj is not None:
        obstaja = naj["shape_id"] and conn.execute(
            "SELECT 1 FROM shape WHERE shape_id = ?", (naj["shape_id"],)).fetchone()
        out = {"postanki": [(r[0], r[1]) for r in conn.execute(
                   "SELECT stop_id, COALESCE(dep_s, arr_s) FROM sched WHERE trip_id = ? "
                   "ORDER BY stop_seq", (naj["trip_id"],))],
               "shape_id": naj["shape_id"] if obstaja else None,
               "headsign": naj["headsign"]}
    if kljuc[0] is not None:
        for k in [k for k in _PREDLOGE if k[0] != kljuc[0]]:
            _PREDLOGE.pop(k, None)
        _PREDLOGE[kljuc] = out
    return out


def _predloga(conn: sqlite3.Connection, vzorec: str,
              zivi: list[tuple] | None = None) -> dict | None:
    """Postanki vzorca z voznimi časi, trasa in smer: najdaljša vožnja tega
    vzorca v voznem redu (`_predloga_iz_reda`), sicer postanki žive vožnje
    brez ur -- vožnja, ki še ni začela, v feedu nosi vse svoje postanke."""
    iz_reda = _predloga_iz_reda(conn, vzorec)
    if iz_reda is not None and (zivi is None or len(iz_reda["postanki"]) >= len(zivi)):
        return iz_reda
    if zivi and min(z[0] for z in zivi) <= 1:
        return {"postanki": [(sid, None) for _, sid, _ in sorted(zivi, key=lambda z: z[0])],
                "shape_id": None, "headsign": None}
    return None


def _razdalje(conn: sqlite3.Connection, stop_ids: list[str]) -> list[float]:
    """Kumulativna razdalja po postajališčih (zračno), za vmesne ure brez predloge."""
    lega = {r[0]: (r[1], r[2]) for r in conn.execute(
        f"SELECT stop_id, lat, lon FROM station WHERE stop_id IN ({','.join('?' * len(stop_ids))})",
        stop_ids)}
    out, vsota, prej = [], 0.0, None
    for sid in stop_ids:
        tu = lega.get(sid)
        if prej is not None and tu is not None:
            vsota += geo.haversine(prej[0], prej[1], tu[0], tu[1])
        out.append(vsota)
        prej = tu or prej
    return out


def nov_vozni_red(objava: list[tuple], predloga: list[tuple],
                  razdalje: list[float] | None = None) -> list[tuple] | None:
    """Postanki objavljene vožnje, prestavljeni na vzorec predloge.

    `objava` = [(stop_seq, stop_id, arr_s, dep_s)], `predloga` = [(stop_id,
    t_s ali None)] po vrsti, `razdalje` = kumulativni metri predloge. Vrne
    [(stop_seq, stop_id, arr_s, dep_s)] od prvega do zadnjega postanka
    objavljene vožnje, ali None, kadar predloga njenega začetka ali konca
    nima ali sta si vzorca preveč različna.

    Ure postajališč, ki jih imata oba, ostanejo objavljene; vmesne so
    razdeljene po voznih časih predloge (brez njih po razdalji): LPP-jev
    zaslon je 26. 10. 2026 Navje kazal 2 min pred objavljenim Kolodvorom,
    vmes med sosedoma, ki sta oba v objavi.
    """
    if len(objava) < 2 or len(predloga) < 2:
        return None
    sids = [p[0] for p in predloga]
    prvi, zadnji = objava[0][1], objava[-1][1]
    if prvi not in sids:
        return None
    a = sids.index(prvi)
    za = [i for i in range(a + 1, len(sids)) if sids[i] == zadnji]
    if not za:
        return None
    b = za[-1] if prvi == zadnji else za[0]
    nova = predloga[a:b + 1]
    # Sidra: postajališča objave v istem vrstnem redu.
    sidra: dict[int, tuple] = {}
    j = 0
    for k, (sid, _) in enumerate(nova):
        for i in range(j, len(objava)):
            if objava[i][1] == sid:
                sidra[k] = objava[i]
                j = i + 1
                break
    if 0 not in sidra or len(nova) - 1 not in sidra \
            or len(sidra) < max(2, SKUPNIH_DELEZ * len(objava)):
        return None
    zaporedje = sorted(sidra)
    # Skupni postanki obdržijo objavljeno številko: nanje se sklicujejo zamude
    # v `run`, zgodovina drugih dni in vse, kar pride po razveljavitvi ali
    # novem uvozu. Novi dobijo proste številke vmes; kadar jih ni dovolj, se
    # oštevilči vse znova.
    stevilke = {k: sidra[k][0] for k in zaporedje}
    for k1, k2 in zip(zaporedje, zaporedje[1:]):
        vmes = range(k1 + 1, k2)
        if len(vmes) > stevilke[k2] - stevilke[k1] - 1:
            stevilke = {k: k + 1 for k in range(len(nova))}
            break
        for i, k in enumerate(vmes):
            stevilke[k] = stevilke[k1] + 1 + i
    out = []
    for k, (sid, tt) in enumerate(nova):
        if k in sidra:
            _, _, arr, dep = sidra[k]
            out.append((stevilke[k], sid, arr, dep))
            continue
        k1 = max(x for x in zaporedje if x < k)
        k2 = min(x for x in zaporedje if x > k)
        t1 = sidra[k1][3] if sidra[k1][3] is not None else sidra[k1][2]
        t2 = sidra[k2][2] if sidra[k2][2] is not None else sidra[k2][3]
        if t1 is None or t2 is None:
            return None
        p1, p2 = nova[k1][1], nova[k2][1]
        if tt is not None and p1 is not None and p2 is not None and p2 > p1:
            delez = (tt - p1) / (p2 - p1)
        elif razdalje is not None and razdalje[a + k2] > razdalje[a + k1]:
            delez = (razdalje[a + k] - razdalje[a + k1]) / (razdalje[a + k2] - razdalje[a + k1])
        else:
            delez = (k - k1) / (k2 - k1)
        # Na minuto, kot objava; `+ 0.5` in ne `round()` (bančno zaokroževanje).
        t = int((t1 + min(1.0, max(0.0, delez)) * (t2 - t1)) / 60 + 0.5) * 60
        out.append((stevilke[k], sid, t, t))
    return out


def popravi(conn: sqlite3.Connection, trip_id: str, ziv: str, dokazov: int,
            zdaj: float, predloga: dict | None = None, z_meritvami: bool = False) -> bool:
    """Prestavi objavljeno vožnjo na vzorec `ziv`. Ne potrdi; značko voznega
    reda premakne klicatelj (`_premakni_znacko`).

    Vožnje z meritvami (`_z_meritvami`) ne prestavi: feed pod njenim id-jem
    jih je pisal po objavljenih številkah, in tiste izpuščenih postankov bi
    dobili novi. Razen `z_meritvami`: meritve sparjene so pisane po
    postajališču, na skupne postanke, ki obdržijo številko, in uvoz vrača
    popravek, po katerem so bile pisane.
    """
    if conn.execute("SELECT 1 FROM popravek_vzorca WHERE trip_id = ?", (trip_id,)).fetchone() \
            or not z_meritvami and _z_meritvami(conn, [trip_id]):
        return False
    t = conn.execute("SELECT route_id, service_id, shape_id, headsign FROM trip "
                     "WHERE trip_id = ?", (trip_id,)).fetchone()
    if t is None:
        return False
    objava = [tuple(r) for r in conn.execute(
        "SELECT stop_seq, stop_id, arr_s, dep_s FROM sched WHERE trip_id = ? ORDER BY stop_seq",
        (trip_id,))]
    predloga = predloga or _predloga(conn, ziv)
    if predloga is None or not objava:
        return False
    nova = nov_vozni_red(objava, predloga["postanki"],
                         _razdalje(conn, [p[0] for p in predloga["postanki"]]))
    if nova is None or [p[1] for p in nova] == [p[1] for p in objava]:
        return False
    dan = conn.execute("SELECT date FROM service_day WHERE service_id = ? LIMIT 1",
                       (t["service_id"],)).fetchone()
    conn.execute(
        "INSERT INTO popravek_vzorca(trip_id, service_date, route_id, objavljen, ziv, dokazov,"
        "                            ts, shape_id, headsign, postanki, prestavljen) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (trip_id, dan[0] if dan else "", t["route_id"], _vzorec(trip_id), ziv, dokazov,
         int(zdaj), t["shape_id"], t["headsign"], json.dumps(objava),
         json.dumps({"postanki": nova, "shape_id": predloga["shape_id"],
                     "headsign": predloga["headsign"]})))
    conn.execute("DELETE FROM sched WHERE trip_id = ?", (trip_id,))
    conn.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) "
                     "VALUES(?,?,?,?,?)", [(trip_id, *p) for p in nova])
    conn.execute("UPDATE trip SET shape_id = ?, headsign = COALESCE(?, headsign) "
                 "WHERE trip_id = ?", (predloga["shape_id"], predloga["headsign"], trip_id))
    db.fill_trip_window(conn, [trip_id])
    return True


def _premakni_znacko(conn: sqlite3.Connection) -> None:
    db.set_meta(conn, "vozni_red_popravljen", str(time.time_ns()))


def _samo_objava(conn: sqlite3.Connection, trip_id: str) -> set[str]:
    """Postajališča objave, ki jih prestavljena vožnja nima."""
    r = conn.execute("SELECT postanki FROM popravek_vzorca WHERE trip_id = ?",
                     (trip_id,)).fetchone()
    if r is None:
        return set()
    ima = {s[0] for s in conn.execute("SELECT stop_id FROM sched WHERE trip_id = ?", (trip_id,))}
    return {p[1] for p in json.loads(r[0])} - ima


def _z_meritvami(conn: sqlite3.Connection, trip_ids: list[str]) -> set[str]:
    """Vožnje z zapisom v `run` ali v `obs`: dnevnik hrani tudi vrednosti, ki
    jih `run` ni sprejel (`is_zero_blip`), in `kajros repair` jih zna vrniti."""
    return {t for t in trip_ids
            if conn.execute("SELECT 1 FROM run WHERE trip_id = ? LIMIT 1", (t,)).fetchone()
            or conn.execute("SELECT 1 FROM obs WHERE trip_id = ? LIMIT 1", (t,)).fetchone()}


def _vozi_objavo(conn: sqlite3.Connection, dan_id: str, proga: str, objavljen: str,
                 izvzete) -> bool:
    """Ali je LPP ta dan objavljen vzorec že vozil pod objavljenim id-jem:
    vožnja z meritvami, ki ni ne prestavljena ne sparjena (`izvzete`). Iz
    baze, ker vožnja pod objavljenim id-jem v feedu ostane le, dokler vozi."""
    sk = _skupina(conn, dan_id, proga)
    return bool(_z_meritvami(conn, [t for t in sk.voznje
                                    if _vzorec(t) == objavljen and t not in izvzete]))


def _popravi_po_dokazih(conn: sqlite3.Connection, v_feedu: dict[str, dict], zive: dict,
                        od_dne: str, zdaj: float) -> tuple[int, int]:
    """Prestavi sparjene vožnje z drugim vzorcem in, ob dovolj dokazih, vse
    objavljene vožnje tega dne, proge in vzorca. Vrne (prestavljenih,
    vrnjenih).

    Dokaz je par iz `ziva_voznja` (tudi vožnje, ki so že končale): vzorec žive
    je tretja komponenta njenega id-ja. Sparjena gre na vzorec svoje žive.
    Nasprotni dokaz za vse ostale je, da LPP ta dan vozi tudi objavljen
    vzorec -- par z njim ali vožnja pod objavljenim id-jem, z napovedjo ali
    meritvami (`_vozi_objavo`) -- ali še kak drug živ vzorec. Tedaj se tisto,
    kar je bilo prestavljeno brez para, vrne (`_vrni`): stalo je le na tem, da
    vožnje brez para vozijo isto kot sparjene -- obvoz se konča, LPP spet vozi
    pod objavljenimi id-ji. Vrne se tudi prestavljena vožnja, ki jo feed nosi
    pod njenim id-jem z napovedjo na postajališču, ki ga ima samo objava, in
    sparjena, prestavljena na drug vzorec, kot ga vozi njena živa (ta gre ob
    naslednjem branju na pravega). Dan, ki ga je skrbnik razveljavil
    (`razveljavi`), se ne prestavlja.
    """
    pop = popravljeni(conn)
    dokazi: dict[tuple, set[str]] = defaultdict(set)   # (dan_id, proga, objavljen, ziv) -> naše
    proti: set[tuple] = set()                          # (dan_id, proga, vzorec), ki ga LPP vozi
    vzorec_para: dict[str, str] = {}                   # sparjena -> vzorec njene žive
    # CROSS JOIN drži vrstni red: brez statistike nove tabele je SQLite bral
    # vso tabelo `trip` (19 ms namesto 0,3).
    for ziva, nasa, proga in conn.execute(
            "SELECT z.ziva, z.nasa, t.route_id FROM ziva_voznja z "
            "CROSS JOIN trip t ON t.trip_id = z.nasa WHERE z.service_date >= ?", (od_dne,)):
        objavljen, ziv = _vzorec(nasa), _vzorec(ziva)
        vzorec_para[nasa] = ziv
        kljuc = (nasa.split("|", 1)[0], proga)
        if ziv == objavljen:
            proti.add((*kljuc, objavljen))
        else:
            dokazi[(*kljuc, objavljen, ziv)].add(nasa)
    if not dokazi and not pop:
        return 0, 0
    napacne = [t for t, ziv in vzorec_para.items() if t in pop and pop[t] != ziv]
    napacne += [t for t, nap in v_feedu.items()
                if t in pop and t not in napacne and nap and set(nap) & _samo_objava(conn, t)]
    # Prestavljene po skupini (brez para) in brez meritev.
    po_skupini: dict[tuple, list[str]] = defaultdict(list)
    if pop:
        kand = [r for r in conn.execute(
            "SELECT p.trip_id, t.service_id, t.route_id, p.objavljen "
            "FROM popravek_vzorca p CROSS JOIN trip t ON t.trip_id = p.trip_id "
            "WHERE p.service_date >= ?", (od_dne,))
            if r[0] not in vzorec_para and r[0] not in napacne]
        merjene = _z_meritvami(conn, [r[0] for r in kand])
        for tid, dan_id, proga, objavljen in kand:
            if tid not in merjene:
                po_skupini[(dan_id, proga, objavljen)].append(tid)
    # Nasprotni dokaz iz feeda, le za skupine, ki jim kaj spremeni. Dan in
    # vzorec sta v id-ju vožnje, vzorec pa je ene same proge.
    skupine = {k[:3] for k in dokazi} | set(po_skupini)
    po_vzorcu = {(k[0], k[2]): k for k in skupine}
    for tid, nap in v_feedu.items():
        k = po_vzorcu.get((tid.split("|", 1)[0], _vzorec(tid)))
        if k is not None and nap and (tid not in pop or tid in napacne):
            proti.add(k)
    # Dva živa vzorca za isti objavljeni: kateri vozi vožnje brez para, ni znano.
    proti |= {k for k, n in Counter(k[:3] for k in dokazi).items() if n > 1}
    proti |= {k for k in skupine - proti
              if _vozi_objavo(conn, *k, pop.keys() | vzorec_para.keys())}
    napacne += [t for k, ids in po_skupini.items() if k in proti for t in ids]
    vrnjenih = _vrni(conn, napacne)
    if vrnjenih:
        pop = popravljeni(conn)

    global _ne_gre_uvoz
    uvoz = db.get_meta(conn, "gtfs_imported_at")
    if uvoz != _ne_gre_uvoz:
        _ne_gre.clear()
        _ne_gre_uvoz = uvoz
    prepovedani = razveljavljeni_dnevi(conn)
    n = 0
    for (dan_id, proga, objavljen, ziv), nase in dokazi.items():
        sk = _skupina(conn, dan_id, proga)
        if sk.dan in prepovedani:
            continue
        # Sparjene tudi z meritvami: te so pisane po postajališču, na skupne
        # postanke, ki obdržijo številko (`nov_vozni_red`).
        cilj = [(t, True) for t in sorted(nase)
                if t not in pop and t not in napacne and (t, ziv) not in _ne_gre]
        if len(nase) >= POPRAVEK_DOKAZOV and (dan_id, proga, objavljen) not in proti:
            # Vse objavljene vožnje tega vzorca, ki jih še nihče ni vozil;
            # sparjene z drugo živo gredo na njen vzorec.
            kand = [t for t in sk.voznje
                    if _vzorec(t) == objavljen and t not in pop and t not in vzorec_para
                    and t not in napacne and (t, ziv) not in _ne_gre]
            merjene = _z_meritvami(conn, kand) if kand else set()
            cilj += [(t, False) for t in kand if t not in merjene]
        if not cilj:
            continue
        predloga = _predloga(conn, ziv, next((z["postanki"] for z in zive.values()
                                              if z["vzorec"] == ziv), None))
        if predloga is None:
            continue
        for tid, z_meritvami in cilj:
            if popravi(conn, tid, ziv, len(nase), zdaj, predloga, z_meritvami):
                n += 1
            else:
                _ne_gre.add((tid, ziv))
    if n:
        _premakni_znacko(conn)
    return n, vrnjenih


def uporabi_popravke(conn: sqlite3.Connection, zdaj: float | None = None) -> int:
    """Po uvozu: objavljeni vozni red je spet po svoje, popravki za dneve od
    včeraj se naredijo znova, starejši se pobrišejo. Na isti vožnji ali,
    kadar ji je uvoz dal nov id, na naslednici (`zamenjava`); predloga je
    prestavljena vožnja sama -- drugje v voznem redu vzorca morda ni več.
    Ne potrdi -- teče v transakciji uvoza, pred novo značko."""
    zdaj = time.time() if zdaj is None else zdaj
    vceraj = (datetime.fromtimestamp(zdaj, stats.TZ).date() - timedelta(days=1)).isoformat()
    stari = conn.execute(
        "SELECT trip_id, ziv, dokazov, prestavljen FROM popravek_vzorca "
        "WHERE service_date >= ?", (vceraj,)).fetchall()
    conn.execute("DELETE FROM popravek_vzorca")
    n = 0
    for tid, ziv, dokazov, prestavljen in stari:
        p = json.loads(prestavljen)
        trasa = p["shape_id"] and conn.execute(
            "SELECT 1 FROM shape WHERE shape_id = ?", (p["shape_id"],)).fetchone()
        predloga = {"postanki": [(s[1], s[3] if s[3] is not None else s[2])
                                 for s in p["postanki"]],
                    "shape_id": p["shape_id"] if trasa else None, "headsign": p["headsign"]}
        cilj = [tid] if conn.execute(
            "SELECT 1 FROM sched WHERE trip_id = ? LIMIT 1", (tid,)).fetchone() else [
            r[0] for r in conn.execute(
                "SELECT DISTINCT novi_trip FROM zamenjava WHERE stari_trip = ?", (tid,))]
        for t in cilj:
            n += popravi(conn, t, ziv, dokazov, zdaj, predloga, z_meritvami=True)
    return n


def _vrni(conn: sqlite3.Connection, trip_ids) -> int:
    """Vrne prestavljenim vožnjam objavljene postanke, traso in smer. Značko
    premakne, ne potrdi.

    Meritve na postankih, kjer ima objava drugo postajališče ali postanka
    sploh nima, gredo z njimi: pod objavljeno številko bi kazale drug kraj.
    """
    vrnjene = []
    for tid in trip_ids:
        r = conn.execute("SELECT shape_id, headsign, postanki FROM popravek_vzorca "
                         "WHERE trip_id = ?", (tid,)).fetchone()
        if r is None:
            continue
        objava = [tuple(p) for p in json.loads(r[2])]
        kje = {p[0]: p[1] for p in objava}
        drugje = [(tid, s[0]) for s in conn.execute(
            "SELECT stop_seq, stop_id FROM sched WHERE trip_id = ?", (tid,))
            if kje.get(s[0]) != s[1]]
        for tabela in ("run", "obs"):
            conn.executemany(f"DELETE FROM {tabela} WHERE trip_id = ? AND stop_seq = ?", drugje)
        conn.execute("DELETE FROM sched WHERE trip_id = ?", (tid,))
        conn.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) "
                         "VALUES(?,?,?,?,?)", [(tid, *p) for p in objava])
        conn.execute("UPDATE trip SET shape_id = ?, headsign = ? WHERE trip_id = ?",
                     (r[0], r[1], tid))
        conn.execute("DELETE FROM popravek_vzorca WHERE trip_id = ?", (tid,))
        vrnjene.append(tid)
    if vrnjene:
        db.fill_trip_window(conn, vrnjene)
        _premakni_znacko(conn)
    return len(vrnjene)


def razveljavljeni_dnevi(conn: sqlite3.Connection) -> set[str]:
    """Dnevi, ki jih je skrbnik razveljavil (`razveljavi`): ta dan se ne
    prestavlja nič več."""
    try:
        return set(json.loads(db.get_meta(conn, "zive_razveljavljeno") or "[]"))
    except ValueError:
        return set()


def razveljavi(conn: sqlite3.Connection, dan: str | None = None) -> int:
    """Vrne objavo prestavljenim vožnjam (vsem ali enega dne) in tisti dan
    (brez `dan` vse dneve s popravki in današnjega) prestavljanje ustavi:
    napačen popravek ne sme čakati naslednjega uvoza, zajem pa bi ga sicer
    ob naslednjem branju naredil znova. Prepoved velja do konca dneva,
    zapisana je v bazi, da jo vidi tudi strežnik (`razveljavljeni_dnevi`)."""
    danes = datetime.now(stats.TZ).date()
    ids = [r[0] for r in conn.execute(
        "SELECT trip_id FROM popravek_vzorca" + (" WHERE service_date = ?" if dan else ""),
        (dan,) if dan else ())]
    dnevi = {dan} if dan else {r[0] for r in conn.execute(
        "SELECT DISTINCT service_date FROM popravek_vzorca")} | {danes.isoformat()}
    vceraj = (danes - timedelta(days=1)).isoformat()
    with conn:
        db.set_meta(conn, "zive_razveljavljeno", json.dumps(sorted(
            d for d in razveljavljeni_dnevi(conn) | dnevi if d >= vceraj)))
        return _vrni(conn, ids)


def naslednji(ziva: dict, zdaj: float) -> tuple[str, int] | None:
    """(stop_id, čas) prvega napovedanega postanka pred vozilom."""
    for _, sid, cas in sorted(ziva["postanki"], key=lambda p: p[0]):
        if cas is not None and cas >= zdaj - 60:
            return sid, cas
    return None


def pregled(conn: sqlite3.Connection, zdaj: float | None = None) -> dict:
    """Za /admin in `kajros zive`: zadnje branje, današnji pari po načinu,
    prestavljene vožnje po liniji in dnevu, ujemanje ure z načrtom."""
    zdaj = time.time() if zdaj is None else zdaj
    danes = datetime.fromtimestamp(zdaj, stats.TZ).date().isoformat()
    try:
        out = json.loads(db.get_meta(conn, "lpp_zive") or "{}")
    except ValueError:
        out = {}
    out["razveljavljeno"] = sorted(razveljavljeni_dnevi(conn))
    out["pari_danes"] = dict(conn.execute(
        "SELECT nacin, COUNT(*) FROM ziva_voznja WHERE service_date = ? GROUP BY nacin",
        (danes,)).fetchall())
    out["popravki"] = [dict(r) for r in conn.execute(
        "SELECT p.service_date AS dan, t.train_no AS linija, COUNT(*) AS voznj, "
        "       MAX(p.dokazov) AS dokazov, MIN(t.headsign) AS smer "
        "FROM popravek_vzorca p CROSS JOIN trip t ON t.trip_id = p.trip_id "
        "WHERE p.service_date >= ? GROUP BY p.service_date, t.train_no, p.objavljen, p.ziv "
        "ORDER BY p.service_date, t.train_no", (danes,))]
    return out
