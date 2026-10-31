"""Zamude vlakov z zemljevida SŽ, prebrane naravnost s potniski.sz.si.

Zakaj: zemljevid vlakov na potniski.sz.si (`admin-ajax.php?action=aktivni_vlaki`)
je izvor vseh zamud vlakov, ki smo jih kdaj imeli. derp.si jih je bral z
`api.modra.ninja/sz/lokacije` (8. 10. 2026, `szService.js`), ta pa s tega
naslova -- polja so ista, le preimenovana. 7. 10. 2026 ob 1:24 sta posrednika
utihnila, ker jima Cloudflare strani ni več odprl; mi jo beremo s Chromom
(`brskalnik.py`). Od 10. 10. 2026 ta vir **vodi** zamude vlakov: zajem derp.si
vlakov ne piše, dokler je zemljevid prebran (`iz_lege.sz_vodi`) -- isti
podatek prek dveh posrednikov je le starejši.

Vlak tam nosi številko, ne id vožnje iz zipa, zato ga pokvarjen zip DUJPP ne
prizadene (28. 9. 2026 je derp.si izgubil vse vlake, zemljevid ne).

Kaj vrstica pove, po polju `Vrsta` (izmerjeno 10. 10. 2026, 84 branj po 15 s):

* **1 -- vozi.** `Postaja` je naslednja postaja, `Odhod` voznoredni odhod s
  postaje PRED njo plus `Zamuda_cas` (izmerjeno na 12 vlakih 28. 9. 2026, ko
  je isto bral modra.ninja). Zamuda je torej odhodna zamuda zadnjega
  prevoženega postanka; enakost je hkrati preizkus, da je vlak pripet na
  pravo vožnjo in dan.
* **0 -- še stoji na izhodišču.** `Odhod` je voznoredni odhod. Ni meritev.
* **2 -- na cilju.** `Postaja` je prazna, `Odhod` prihod na cilj, `Zamuda_cas`
  zamuda ob prihodu. Ostane 1--2 min, nato ga SŽ ponastavi na zamudo 0 ob
  voznorednem prihodu (1897: +7, dve minuti pozneje 0; 3287: +8, nato 0).
  Šteje zato samo prvi prihod.

Vsaka vrednost gre v `sz_zamuda` (zadnje stanje na postanek, s časom prvega in
zadnjega branja) in v `run` in `obs`; zamuda od pet minut naprej še v
`delay_report` kot napoved prihoda na naslednjo postajo (`porocilo`).

Tabla zamud SŽ (`/pomoc-uporabnikom-in-stanje-v-prometu/`) se ne bere: v senci
11. 10. 2026 je isto minuto na 246 parih pokazala le nekaj sekund pred
zemljevidom, pripeti pa bi se dala tretjina njenih vrstic (docs/MERITVE.md).
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
from collections import Counter, defaultdict, deque
from datetime import date, datetime, timedelta
from typing import Callable
from zoneinfo import ZoneInfo

from . import brskalnik, collector, config, db, iz_lege, stats, viri
from .peroni import _kljuc_imena, stevilka

TZ = ZoneInfo(config.TIMEZONE)

#: Zemljevid vlakov SŽ. Isti naslov bere njihova stran vsakih 15 s
#: (`setInterval(…, 15e3)` v `main-*.js`), toliko je tudi takt odgovora.
AKTIVNI = "/wp-admin/admin-ajax.php?action=aktivni_vlaki"

#: Toliko sme `Odhod` odstopati od voznega reda plus zamude. Oboje je v
#: celih minutah, zato ena minuta za zaokroževanje.
ODSTOPA_ODHOD_S = 60
#: Odhod, starejši od tega, ni odhod te vožnje, ampak ista številka drug dan.
NAJSTAREJSI_ODHOD_S = 6 * 3600
#: Odhod do toliko v prihodnosti je še ista vožnja: SŽ je zamudo povečala,
#: preden je vlak odpeljal (LP 314 16. 10. 2026 ob 14:40: +5 -> +10, odhod
#: 2,5 min naprej), ali vlak še stoji na postaji. Takšna vrstica ne gre v
#: `run` -- postanek, ki ga je vlak že prevozil, bi spet postal neprevožen --
#: velja pa za trenutno zamudo (`trenutne`).
NAJDLJE_NAPREJ_S = 3 * 3600
#: Prihod z zamudo 0 po vožnji z več kot toliko zamude je SŽ-jeva ponastavitev
#: vrstice na cilju, ne prihod (glava modula).
PONASTAVITEV_S = 180
#: Poročilo o zamudi (`delay_report`) šele od toliko minut. Mejo je postavil
#: derp.si, ko je iz istega zemljevida sestavljal `SZ-DELAY` (`szService.js`,
#: `zamuda_min >= 5`, izjemna od 30); vseh 101 137 poročil do 7. 10. 2026 jo
#: ima, zato ostane -- zgodovina in novo sta tako primerljiva.
POROCILO_OD_MIN = 5
IZJEMNA_OD_MIN = 30


def vozni_red(conn: sqlite3.Connection, danes: date) -> dict[str, list[dict]]:
    """Številka vlaka -> vožnje, ki bi lahko zdaj vozile (včeraj ali danes).

    Nadomestni avtobusi ne: zemljevid SŽ jih kaže z zamudo 0 v točki postaje
    (pregled 25. 9. 2026) -- izračun, ne meritev.
    """
    dnevi = ((danes - timedelta(days=1)).isoformat(), danes.isoformat())

    def build():
        out: dict[str, dict[tuple, dict]] = defaultdict(dict)
        for r in conn.execute(
            "SELECT t.trip_id, t.train_no, d.date, s.stop_seq, st.name, s.arr_s, s.dep_s "
            "FROM trip t JOIN service_day d USING (service_id) "
            "JOIN sched s USING (trip_id) JOIN station st USING (stop_id) "
            "WHERE t.network = 'zeleznica' AND t.mode != 'bus' AND d.date IN (?, ?) "
            "ORDER BY t.trip_id, d.date, s.stop_seq", dnevi):
            v = out[stevilka(r["train_no"])].setdefault(
                (r["trip_id"], r["date"]),
                {"trip_id": r["trip_id"], "dan": r["date"], "postanki": []})
            v["postanki"].append((r["stop_seq"], _kljuc_imena(r["name"]),
                                  r["arr_s"], r["dep_s"]))
        return {st: list(v.values()) for st, v in out.items()}

    return collector._cached(conn, "vozni_red_sz", dnevi, build)


def _ura(ts: float) -> str:
    return datetime.fromtimestamp(ts, TZ).strftime("%H:%M")


def _minute(hhmm: str) -> int | None:
    try:
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)
    except (AttributeError, ValueError):
        return None


def je_avtobus(vrstica: dict) -> bool:
    return (str(vrstica.get("Vrsta_vlaka") or "").upper() == "B"
            or str(vrstica.get("Rang") or "").upper() == "BUS")


def _ujema(dan: str, t_s: int | None, zamuda_min: int, odhod_min: int,
           zdaj: float, naprej_s: int = 0) -> float | None:
    """Koliko je minilo od voznega reda plus zamude, kadar se ura ujema z
    `Odhod`; sicer None."""
    if t_s is None:
        return None
    kdaj = stats.polnoc(dan) + t_s + zamuda_min * 60
    if not (-ODSTOPA_ODHOD_S - naprej_s <= zdaj - kdaj <= NAJSTAREJSI_ODHOD_S):
        return None
    # Ura z zemljevida je lokalna ura dneva; primerjava po modulu dneva,
    # ker vlak čez polnoč odpelje ob 00:10 prometnega dne včeraj.
    ura = _minute(_ura(kdaj))
    if min((ura - odhod_min) % 1440, (odhod_min - ura) % 1440) * 60 > ODSTOPA_ODHOD_S:
        return None
    return zdaj - kdaj


def pripni(vrstica: dict, voznje: list[dict], zdaj: float,
           naprej_s: int = 0) -> tuple | None:
    """Vrstica zemljevida -> (trip_id, dan, stop_seq, zamuda_s, je_prihod) ali None.

    Vozi: postanek je zadnji prevoženi, torej tisti PRED `Postaja`. Na cilju:
    zadnji postanek vožnje. Od več voženj z isto številko (sezonske različice,
    včeraj in danes) velja tista, pri kateri se `Odhod` ujema z voznim redom
    plus zamudo; kadar se ne ujema nobena, vlaka ne pripnemo -- raje nič kot na
    napačno vožnjo. `naprej_s` dovoli odhod v prihodnosti (`NAJDLJE_NAPREJ_S`).
    """
    zamuda = vrstica.get("Zamuda_cas")
    odhod = _minute(vrstica.get("Odhod"))
    vrsta = vrstica.get("Vrsta")
    if zamuda is None or odhod is None or vrsta not in (1, 2):
        return None
    naslednja = _kljuc_imena(vrstica.get("Postaja") or "")
    if vrsta == 1 and not naslednja:
        return None
    najboljsa, razmik = None, None
    for v in voznje:
        p = v["postanki"]
        if vrsta == 2:
            seq, _, arr, dep = p[-1]
            kandidati = [(seq, arr if arr is not None else dep)]
        else:
            kandidati = [(p[i - 1][0], p[i - 1][3] if p[i - 1][3] is not None else p[i - 1][2])
                         for i in range(1, len(p)) if p[i][1] == naslednja]
        for seq, t_s in kandidati:
            r = _ujema(v["dan"], t_s, zamuda, odhod, zdaj, naprej_s)
            if r is not None and (razmik is None or abs(r) < abs(razmik)):
                najboljsa, razmik = (v["trip_id"], v["dan"], seq, zamuda * 60, vrsta == 2), r
    return najboljsa


def razberi(vrstice: list[dict], po_stevilki: dict[str, list[dict]],
            zdaj: float) -> tuple[list[tuple], dict, list[tuple]]:
    """Vse vrstice zemljevida -> (pripete, števci, prihodnje).

    Prihodnje so vlaki z odhodom v prihodnosti (`NAJDLJE_NAPREJ_S`), v isti
    obliki kot pripete; v `run` ne gredo, le v trenutno zamudo."""
    pripete, prihodnje = [], []
    stevci = {"vlakov": 0, "pred_odhodom": 0, "na_cilju": 0, "nepripetih": 0, "prihodnjih": 0,
              "nepripeti": []}
    for r in vrstice:
        if je_avtobus(r):
            continue
        stevci["vlakov"] += 1
        if r.get("Vrsta") == 0:
            stevci["pred_odhodom"] += 1
            continue
        stevci["na_cilju"] += r.get("Vrsta") == 2
        voznje = po_stevilki.get(stevilka(str(r.get("St_vlaka") or "")), [])
        p = pripni(r, voznje, zdaj)
        if p is not None:
            pripete.append(p)
        elif r.get("Vrsta") == 1 and (p := pripni(r, voznje, zdaj, NAJDLJE_NAPREJ_S)):
            prihodnje.append(p)
            stevci["prihodnjih"] += 1
        else:
            stevci["nepripetih"] += 1
            # Številke za derp.si (`iz_lege.sz_vodi_vlak`) in za pregled.
            if st := stevilka(str(r.get("St_vlaka") or "")):
                stevci["nepripeti"].append(st)
    return pripete, stevci, prihodnje


#: Vožnje, ki so v zadnjem spremenjenem odgovoru po zamudi pokazale ničlo
#: (`zapisi`, tretje varovalo). Druga ničla zapored jo potrdi.
_nicle: set[tuple[str, str]] = set()


def zapisi(conn: sqlite3.Connection, pripete: list[tuple], zdaj: float) -> dict:
    """Pripete zamude v `sz_zamuda`, `run` in `obs` (in `delay_report`).

    Tri varovala, vsa izmerjena na zemljevidu:

    * **Vlak ne gre nazaj z isto ali manjšo zamudo.** Zemljevid je vozni
      red plus trenutna zamuda, ne sled: vlak, ki zamudo nabira, gre naprej,
      ko poteče stara zamuda, in skoči nazaj, ko SŽ zamudo poveča (RG 615 16.
      10. 2026: „naslednja Šentjur“ / „naslednja Celje“ izmenoma, +3, +5, +8).
      Nazaj z isto zamudo je nihanje in se ne zapiše; z večjo je zvišana
      zamuda in velja. Do 16. 10. se ni zapisalo nobeno „nazaj“ (LPV 2616 10.
      10.: „naslednja Ljubljana Tivoli, +9“ po odhodu iz Ljubljane s +0) --
      in vlak, ki ga je SŽ najprej risal po voznem redu, je ostal točen:
      LPV 2907 16. 10. 10 min +0 namesto +7. Na 13 min zemljevida je bila
      prikazana zamuda prenizka za 3 min ali več 63-krat od 2 453, zdaj
      enkrat. Cena: postanek zadaj dobi trenutno zamudo, ne odhodne.
    * **Na cilju šteje prvi prihod** (glava modula), in ničla po zamudi nad
      `PONASTAVITEV_S` ni prihod, ampak ponastavitev. Razen kadar je SŽ vlak
      po prihodu spet pokazal na progi: takrat je bil prihod prezgoden.
    * **Ničla po zamudi velja šele, ko jo potrdi naslednji odgovor.** SŽ na
      vsake 3--4 min za en odgovor (15 s) del vlakov pokaže po voznem redu:
      zamuda 0, postaja in lega tam, kjer bi vlak bil, če bi bil točen. 16.
      10. 2026 ob 14:28:52 sedem od 59 vlakov, LP 3234 iz +21 pred Ivančno
      Gorico na 0 pred Žalno; 15 s pozneje spet +21. Takšen odgovor je vlak
      prestavil naprej, prvo varovalo (takrat še brez izjeme za večjo
      zamudo) pa je nato prave vrstice zavračalo kot vožnjo nazaj -- dokler
      ga ni pravi vlak dohitel in ga naslednja ničla spet prestavila. RG 318 je tako 16. 10. od Zidanega Mosta (6:32) do
      Ljubljane Polje (7:48) pisal +0, vozil pa +12 do +18. Od 11. do 16.
      10. 2026 so ničle zadele 611 od 1 444 voženj z zamudo. Velja za vsako
      zamudo, ne le veliko: tudi +3 bi vlak prestavil 3 min naprej. Cena je
      15 s zakasnitve pravega okrevanja na 0. „Po zamudi“ pomeni po zadnji
      besedi SŽ o vlaku, ne po postanku najdlje naprej (glej spodaj).
    """
    ts = int(zdaj)
    izid = {"zapisanih": 0, "nazaj": 0, "ponastavljenih": 0, "porocil": 0, "nicel": 0}
    nicle = set()
    for trip_id, dan, seq, zamuda, je_prihod in pripete:
        zadnji = conn.execute(
            "SELECT stop_seq, delay_s FROM sz_zamuda WHERE trip_id = ? AND service_date = ? "
            "ORDER BY stop_seq DESC LIMIT 1", (trip_id, dan)).fetchone()
        # Ničlo primerjamo z ZADNJO besedo SŽ, ne s postankom najdlje naprej:
        # ta je po ničli, ki je prišla skozi, sam ničla, in vsaka naslednja
        # bi šla mimo kot „ničla po ničli“. Tako je bilo po prvem popravku
        # 16. 10. 2026 pri vlakih, ki so ničlo naprej že imeli: LPV 2504 je
        # +0 dobil ob 14:40, 14:47 in 14:51, SŽ pa je vmes kazal +16 do +18.
        prejsnja = conn.execute(
            "SELECT delay_s, stop_seq FROM sz_zamuda WHERE trip_id = ? AND service_date = ? "
            "ORDER BY zadnjic_ts DESC, stop_seq DESC LIMIT 1", (trip_id, dan)).fetchone()
        if (not je_prihod and zamuda == 0 and prejsnja and prejsnja[0] > 0
                and (trip_id, dan) not in _nicle):
            nicle.add((trip_id, dan))
            izid["nicel"] += 1
            continue
        if zadnji and seq < zadnji[0] and zamuda <= zadnji[1]:
            izid["nazaj"] += 1
            continue
        if je_prihod and zadnji:
            # Prihod je že zapisan, kadar je bil zadnja beseda SŽ o vlaku. Če
            # ga je SŽ potem spet pokazal pred ciljem (z večjo zamudo -- to
            # sprejme pravilo „nazaj“ zgoraj), je bil prvi prihod prezgoden:
            # SŽ obtičali vlak nariše na cilju ob voznem redu in stari zamudi.
            # 16.–17. 10. 2026 32 od 360 prihodov (8,9 %), v `run` je ostal
            # prvi: ICS 11 +15 namesto +75, RG 315 0 namesto +62.
            if seq == zadnji[0] and (prejsnja is None or prejsnja[1] == seq):
                continue                       # prihod je že zapisan
            if zamuda == 0 and (prejsnja[0] if prejsnja else zadnji[1]) > PONASTAVITEV_S:
                izid["ponastavljenih"] += 1
                continue
        iz_lege.zapisi_meritev(conn, trip_id, dan, seq, zamuda if je_prihod else None,
                               None if je_prihod else zamuda, ts, ohrani=True)
        conn.execute(
            "INSERT INTO sz_zamuda(trip_id, service_date, stop_seq, delay_s, "
            "                      prvic_ts, zadnjic_ts, v_run) VALUES(?,?,?,?,?,?,1) "
            "ON CONFLICT(trip_id, service_date, stop_seq) DO UPDATE SET "
            "  delay_s = excluded.delay_s, zadnjic_ts = excluded.zadnjic_ts, v_run = 1",
            (trip_id, dan, seq, zamuda, ts, ts))
        izid["zapisanih"] += 1
        if not je_prihod:
            izid["porocil"] += porocilo(conn, trip_id, dan, seq, zamuda, ts)
    conn.commit()
    _nicle.clear()
    _nicle.update(nicle)
    return izid


def porocilo(conn: sqlite3.Connection, trip_id: str, dan: str, seq: int,
             zamuda_s: int, ts: int) -> int:
    """Zamuda ob prihodu na naslednjo postajo v `delay_report`; 1, kadar je
    zapisana nova vrstica.

    Do 7. 10. 2026 je to pisal `alerts.ingest` iz obvestil `SZ-DELAY`, ki jih
    je derp.si sestavil iz tega istega zemljevida („Vlak … ima zamudo N min ob
    prihodu na postajo <naslednja>“). Z modra.ninja so utihnila tudi ta (6. 10.
    3 749 poročil, od 8. 10. eno na dan) in z njimi vrstica „napoved
    prevoznika“ v oknu vožnje in meja prehoda v `stats.last_measured()`.

    Ime postaje je naše (`station.name`), ne zapis SŽ, ker se meja prehoda
    nanj veže z enakostjo. Zapis samo ob spremembi, kot prej.
    """
    if zamuda_s < POROCILO_OD_MIN * 60:
        return 0
    r = conn.execute(
        "SELECT t.train_no, st.name FROM trip t "
        "JOIN sched s ON s.trip_id = t.trip_id AND s.stop_seq > ? "
        "JOIN station st ON st.stop_id = s.stop_id "
        "WHERE t.trip_id = ? ORDER BY s.stop_seq LIMIT 1", (seq, trip_id)).fetchone()
    if r is None:
        return 0
    minut = zamuda_s // 60
    prej = conn.execute(
        "SELECT delay_min, station FROM delay_report WHERE trip_id = ? AND service_date = ? "
        "ORDER BY seen_ts DESC LIMIT 1", (trip_id, dan)).fetchone()
    if prej and (prej[0], prej[1]) == (minut, r[1]):
        return 0
    return conn.execute(
        "INSERT OR IGNORE INTO delay_report(trip_id, service_date, seen_ts, train_no, "
        "                                  delay_min, station, event, severe) "
        "VALUES(?,?,?,?,?,?,'prihod',?)",
        (trip_id, dan, ts, r[0], minut, r[1], int(minut >= IZJEMNA_OD_MIN))).rowcount


#: Trenutna zamuda vsake vožnje na zemljevidu: (trip_id, dan) -> (zamuda_s,
#: čas odgovora, postanek pred `Postaja`). Ves slovar se zamenja ob vsakem
#: spremenjenem odgovoru, zato ga niti strežbe berejo brez zaklepanja.
_trenutne: dict[tuple[str, str], tuple[int, int, int]] = {}

#: Kako dolgo velja trenutna zamuda brez novega odgovora. SŽ odgovor spremeni
#: na 15 s; minuta so štirje zgrešeni.
SVEZA_TRENUTNA_S = 60


def _osvezi_trenutne(pripete: list[tuple], prihodnje: list[tuple], zdaj: float) -> None:
    global _trenutne
    novo = {}
    for trip_id, dan, seq, zamuda, je_prihod in (*pripete, *prihodnje):
        k = (trip_id, dan)
        if je_prihod:
            continue
        if k in _nicle:
            # Nepotrjena ničla (`zapisi`): velja, kar je SŽ rekel prej.
            if k in _trenutne:
                novo[k] = _trenutne[k]
            continue
        novo[k] = (zamuda, int(zdaj), seq)
    _trenutne = novo


def trenutne(dan: str, trip_ids, zdaj: float) -> dict[str, dict]:
    """trip_id -> trenutna zamuda z zemljevida, kadar je sveža.

    `Zamuda_cas` je zamuda vlaka ZDAJ (pred postajo `Postaja`), zamuda v
    `run` pa odhodna zamuda zadnjega prevoženega postanka. Kadar vlak stoji
    ali SŽ zamudo poveča med postajama, je prva višja, in to ves čas, dokler
    vlak ne prevozi naslednje postaje: LPV 2417 16. 10. 2026 ob 14:58 SŽ +14,
    prikaz +1 s postaje prej. Uporaba: `stats.last_measured`."""
    t = _trenutne
    out = {}
    for trip_id in trip_ids:
        z = t.get((trip_id, dan))
        if z and zdaj - SVEZA_TRENUTNA_S <= z[1] <= zdaj + SVEZA_TRENUTNA_S:
            out[trip_id] = {"s": z[0], "ts": z[1], "seq": z[2]}
    return out


#: Straža: kar shranimo in pokažemo, proti temu, kar SŽ pravi ta hip. Od 11.
#: do 16. 10. 2026 je prikaz pri 611 od 1 444 voženj z zamudo kazal prenizko
#: (RG 318 +0 in +12 namesto +18), pa ni nihče vedel: zdravje je bilo zeleno,
#: ker je vir odgovarjal. Primerjamo le vlake, ki jim SŽ zamude vsaj
#: `USTALJENA_S` ne spreminja -- vlak, ki stoji in mu zamuda raste, ima
#: zadnji prevoženi postanek po pravici nižji. Na 3 381 takih primerjavah
#: (25 min zemljevida 16. 10. 2026, ponovljenih skozi kodo) je bil prikaz
#: za 3 min ali več mimo s staro kodo 2,3--4,1 %, z novo 0.
USTALJENA_S = 120
SKLADNOST_RAZLIKA_S = 180
SKLADNOST_OKNO_S = 30 * 60

#: (trip_id, dan) -> (zamuda_s, od kdaj jo SŽ ima)
_ustaljene: dict[tuple[str, str], tuple[int, float]] = {}
#: Po en vnos na spremenjen odgovor: (čas, primerjav, prenizko, previsoko,
#: {vlak: „SŽ +18, prikaz +12“} za vlake, ki so bili mimo).
_skladnost: deque = deque()


def skladnost(conn: sqlite3.Connection, pripete: list[tuple], zdaj: float) -> dict:
    """Ustaljena zamuda SŽ proti meji meritve (`stats.last_measured`) za
    zadnjih `SKLADNOST_OKNO_S`; gre v `meta` in v zdravje (`skladnost_sz`).

    Meja brez trenutne zamude (`trenutna_s`): ta bi zakrila prav tisto, kar
    straža išče -- da `run` ne nosi tega, kar SŽ pravi."""
    global _ustaljene
    ustaljene, po_dnevih = {}, defaultdict(dict)
    for trip_id, dan, seq, zamuda, je_prihod in pripete:
        k = (trip_id, dan)
        if je_prihod or k in _nicle:
            continue
        prej = _ustaljene.get(k)
        ustaljene[k] = prej if prej and prej[0] == zamuda else (zamuda, zdaj)
        if zdaj - ustaljene[k][1] >= USTALJENA_S:
            po_dnevih[dan][trip_id] = (zamuda, seq)
    _ustaljene = ustaljene
    n = nizko = visoko = 0
    mimo: dict[str, str] = {}
    for dan, sz in po_dnevih.items():
        meje = stats.last_measured(conn, dan, list(sz), int(zdaj - stats.polnoc(dan)))
        rezerve = stats._slack_ahead(conn, list(sz))
        for trip_id, (zamuda, seq) in sz.items():
            m = meje.get(trip_id)
            prikaz = (m["delay_s"] or 0) if m else None
            # SŽ vlak, ki obtiči, riše po voznem redu (RG 210 17. 10. 2026: uro
            # +0, vlak je stal pred Borovnico; potem +36). Padca, ki ga
            # rezerva voznega reda ne pojasni, prikaz namenoma ne vzame
            # (`stats._LAST_MEASURED_SQL`) -- to ni neskladje, ampak SŽ.
            # Straža je 16. in 17. 10. zaradi tega dvakrat lažno zvonila.
            if prikaz is not None and prikaz >= zamuda + SKLADNOST_RAZLIKA_S:
                rezerva = sum(r for q, r in rezerve.get(trip_id, ())
                              if m["stop_seq"] <= q <= seq)
                if prikaz - zamuda > rezerva + 120:
                    continue
            n += 1
            if prikaz is None and zamuda >= SKLADNOST_RAZLIKA_S:
                nizko += 1
            elif prikaz is not None and prikaz <= zamuda - SKLADNOST_RAZLIKA_S:
                nizko += 1
            elif prikaz is not None and prikaz >= zamuda + SKLADNOST_RAZLIKA_S:
                visoko += 1
            else:
                continue
            st = conn.execute("SELECT train_no FROM trip WHERE trip_id = ?", (trip_id,)).fetchone()
            mimo[st[0] if st else trip_id] = (
                f"SŽ +{zamuda // 60}, prikaz " + ("brez" if prikaz is None else f"+{prikaz // 60}"))
    _skladnost.append((zdaj, n, nizko, visoko, mimo))
    while _skladnost[0][0] < zdaj - SKLADNOST_OKNO_S:
        _skladnost.popleft()
    kolikokrat: Counter = Counter()
    zadnje: dict[str, str] = {}
    for *_, v in _skladnost:
        kolikokrat.update(v.keys())
        zadnje.update(v)
    return {"primerjav": sum(x[1] for x in _skladnost),
            "prenizko": sum(x[2] for x in _skladnost),
            "previsoko": sum(x[3] for x in _skladnost),
            "vlakov": len(kolikokrat),
            "primeri": [f"{vlak} ({zadnje[vlak]})" for vlak, _ in kolikokrat.most_common(5)],
            "od_ts": int(_skladnost[0][0])}


#: Odtis zadnjega odgovora: nespremenjen zemljevid je v /admin opomba, dolgo
#: nespremenjen ob vlakih na poti pa opozorilo (`zdravje.ocena`).
_odtis: str | None = None


def _get() -> list[dict]:
    global _odtis
    with viri.branje("zamude_sz") as b:
        besedilo = brskalnik.zahtevaj(AKTIVNI)
        b.http, b.bajtov = 200, len(besedilo.encode())
        try:
            vrstice = json.loads(besedilo)
        except ValueError:
            raise RuntimeError("zemljevid SŽ ni vrnil JSON") from None
        # Ko ne vozi noben vlak, SŽ vrne `null`, ne prazen seznam (izmerjeno
        # 10. 10. 2026 ob 23:58).
        if vrstice is None:
            vrstice = []
        if not isinstance(vrstice, list):
            # Z začetkom odgovora: 17.–18. 10. 2026 ponoči petkrat po 1–62 min
            # tako, vmes `null` ali par vlakov -- ali je to nočni molk ali
            # okvara, se ve šele iz vsebine.
            raise RuntimeError(f"zemljevid SŽ ni vrnil seznama vlakov: {besedilo[:60]!r}")
        odtis = hashlib.blake2s(besedilo.encode(), digest_size=8).hexdigest()
        b.nespremenjeno = odtis == _odtis
        _odtis = odtis
        return vrstice


def korak(conn: sqlite3.Connection, vrstice: list[dict], zdaj: float,
          nespremenjeno: bool = False) -> dict:
    """En odgovor zemljevida: pripni, zapiši, povzemi v `meta` za pregled.

    Nespremenjen odgovor (dve od treh branj, ker beremo na 5 s, SŽ pa
    preračuna na 15) samo potrdi, da vir živi: znova zapisan bi vsaki vrednosti
    premaknil čas zadnjega podatka, čeprav SŽ ni povedal nič novega.
    """
    prej = json.loads(db.get_meta(conn, "zamude_sz") or "{}")
    if nespremenjeno and prej.get("odtis") == _odtis and "vlakov" in prej:
        prej["ts"] = int(zdaj)
        prej.pop("napaka", None)
        prej.pop("napaka_ts", None)
        db.set_meta(conn, "zamude_sz", json.dumps(prej, sort_keys=True))
        conn.commit()
        return prej
    po_stevilki = vozni_red(conn, datetime.fromtimestamp(zdaj, TZ).date())
    pripete, stevci, prihodnje = razberi(vrstice, po_stevilki, zdaj)
    # Vlak, ki ga zemljevid kaže, mi pa ga ne pripnemo, piše derp.si.
    st = {v["trip_id"]: k for k, vs in po_stevilki.items() for v in vs}
    iz_lege.sz_stevilke({st[p[0]] for p in pripete + prihodnje if p[0] in st},
                        stevci["nepripeti"], zdaj)
    stevci.update(zapisi(conn, pripete, zdaj))
    _osvezi_trenutne(pripete, prihodnje, zdaj)
    stevci["skladnost"] = skladnost(conn, pripete, zdaj)
    odtis = _odtis or ""
    stevci["odtis"] = odtis
    stevci["spremenjeno_ts"] = (prej.get("spremenjeno_ts") if prej.get("odtis") == odtis
                                else None) or int(zdaj)
    stevci["ts"] = int(zdaj)
    db.set_meta(conn, "zamude_sz", json.dumps(stevci, sort_keys=True))
    conn.commit()
    return stevci


#: Nepripeti vlaki, ki so danes že v dnevniku (`teci`).
_javljeni: dict[date, set[str]] = {}


def teci(stop: threading.Event, log: Callable[[str], None]) -> None:
    """Svoja nit: brskalnik zna obviseti (izziv do 90 s) -- v zajemni zanki bi
    to zamaknilo zamude avtobusov."""
    conn = db.connect()
    napak, prvic = 0, True
    try:
        while not stop.is_set():
            zdaj = time.time()
            try:
                prej = _odtis
                vrstice = _get()
                s = korak(conn, vrstice, zdaj, nespremenjeno=prej is not None and _odtis == prej)
                # Zemljevid vodi (derp.si vlakov ne piše, `iz_lege.sz_vodi`) samo,
                # kadar ima vlak, ki ga pripnemo. Prazen (`null`) ob vlakih je
                # prej utišal derp.si za vse vlake -- nobena zamuda vlaka nikjer
                # (presoja 31. 10. 2026). Ponoči je prazen po pravici.
                if s.get("vlakov", 0) > s.get("nepripetih", 0):
                    iz_lege.sz_prebran(zdaj)
                # Enkrat na vlak in dan v dnevnik: koliko jih piše derp.si
                # (`iz_lege.sz_vodi_vlak`), se čez teden prešteje iz dnevnika.
                dan = datetime.fromtimestamp(zdaj, TZ).date()
                for st in set(s.get("nepripeti") or ()) - _javljeni.get(dan, set()):
                    _javljeni.setdefault(dan, set()).add(st)
                    log(f"zemljevid SŽ kaže vlak {st}, ki ga ne pripnemo -- piše ga derp.si")
                for d in [d for d in _javljeni if d < dan]:
                    del _javljeni[d]
                if napak or prvic:
                    log(f"zemljevid SŽ {'spet ' if napak else ''}odgovarja"
                        f"{f' (po {napak} napakah)' if napak else ''}: {s['vlakov']} vlakov, "
                        f"{s['zapisanih']} zapisanih, {s['nepripetih']} nepripetih; "
                        "zamude vlakov vodi zemljevid SŽ")
                napak, prvic = 0, False
            except Exception as exc:        # noqa: BLE001 -- vir ni naš
                # Brez tega je nit obstala za vedno. 1. 10. 2026 ob 3:30 je
                # nočno vzdrževanje drlo pisanje dlje od 30 s, `korak` je
                # odnehal sredi transakcije, `get_meta` spodaj je v njej
                # zamrznil posnetek in vsako nadaljnje pisanje je vrnilo
                # „database is locked“ (SQLITE_BUSY_SNAPSHOT, čakanje ne
                # pomaga). Zemljevid SŽ 4 h brez zapisa, WAL zrasel na 5,4 GB,
                # ker ga za odprtim posnetkom ni mogoče prepisati.
                conn.rollback()
                napak += 1
                if napak == 1:
                    log(f"zemljevid SŽ ne odgovarja: {exc}; zamude vlakov spet piše "
                        f"derp.si, ko mine {iz_lege.SZ_VODI_S} s")
                # Zadnji uspešni števci ostanejo; pregled po `napaka_ts`
                # vidi, da so stari in zakaj.
                try:
                    s = json.loads(db.get_meta(conn, "zamude_sz") or "{}")
                    s.update(napaka=str(exc)[:200], napaka_ts=int(zdaj))
                    db.set_meta(conn, "zamude_sz", json.dumps(s, sort_keys=True))
                    conn.commit()
                except sqlite3.Error:
                    conn.rollback()
            # Takt od začetka branja, ne od konca: branje (0,5--0,8 s, dlje,
            # ko brskalnik bere tablo postaje) bi ga sicer raztegnilo.
            stop.wait(max(0.5, config.SZ_ZAMUDE_SECONDS - (time.time() - zdaj),
                          brskalnik.pocitek_s() if napak else 0.0))
    finally:
        conn.close()
