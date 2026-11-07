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

from . import brskalnik, collector, config, db, dosje, iz_lege, stats, viri
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


#: Ime postaje z zemljevida (ključ `_kljuc_imena`) -> ime v voznem redu IJPP,
#: kjer se razlikujeta. Samo za zemljevid: tabla SŽ (`peroni`) piše polno ime.
#: „Slivnica“ = „Spodnja Slivnica“ (station 1120963, edina od 266 postaj vlakov
#: s tem imenom, 32 vlakov LP 4491--4537 Kočevske proge): brez tega 143 od 153
#: epizod nepripetih vlakov 1.--7. 11. 2026 (dosje), postanek pred Slivnico
#: (Grosuplje, Čušperk) brez meritve v 124 od 143. Vsa druga imena `Postaja` v
#: tednu (254) se ujamejo, razen „Rodik“ (vlaka brez naše vožnje).
IMENA_ZEMLJEVIDA = {"slivnica": "spodnja slivnica"}


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
    naslednje = {naslednja, IMENA_ZEMLJEVIDA.get(naslednja, naslednja)}
    najboljsa, razmik = None, None
    for v in voznje:
        p = v["postanki"]
        if vrsta == 2:
            seq, _, arr, dep = p[-1]
            kandidati = [(seq, arr if arr is not None else dep)]
        else:
            kandidati = [(p[i - 1][0], p[i - 1][3] if p[i - 1][3] is not None else p[i - 1][2])
                         for i in range(1, len(p)) if p[i][1] in naslednje]
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


#: Stanje vsakega vlaka v zadnjem SPREMENJENEM odgovoru: (trip_id, dan) ->
#: (stop_seq, zamuda_s, je_prihod). Nespremenjenih `korak` ne obdela, zato je to
#: "prejšnji spremenjen odgovor" (`potrdi`).
_prejsnji: dict[tuple[str, str], tuple[int, int, bool]] = {}


def potrdi(conn: sqlite3.Connection, pripete: list[tuple],
           prihodnje: list[tuple]) -> tuple[list[tuple], list[tuple], set[tuple[str, str]]]:
    """Stanje vlaka z zemljevida velja šele, ko ga potrdi naslednji spremenjen
    odgovor: (pripete, prihodnje, nepotrjeni (trip_id, dan)).

    **Stanje** = `(stop_seq, zamuda, je_prihod)` pripete vrstice. Velja, kadar
    je enako stanju vlaka v prejšnjem spremenjenem odgovoru ali zadnjemu
    zapisanemu (`sz_zamuda`: osvežitev, vlak stoji ali vozi enako). Kandidat,
    ki ga naslednji spremenjen odgovor ne ponovi, odpade: A, B, A zapiše
    samo A. Isto za vlake z odhodom v prihodnosti (trenutna zamuda).

    Zakaj: SŽ za en odgovor (15 s) vrne zastarelo stanje, in to ne le ničlo.
    1.--6. 11. 2026 na 3 190 voženj-dneh (dosje, vsak vzorec) se je vrednost za
    en odgovor spremenila in takoj vrnila 10 689-krat na ničlo (vlak „po
    voznem redu“), 202-krat na višjo zamudo in 6-krat na nižjo neničelno.
    Višje je prepustilo pravilo „nazaj z večjo zamudo velja“: LPV 2206 6. 11.
    ob 07:57:18 in 08:07:48 +15 namesto +2/+3 (Hrastnik, Zagorje), s poročilom
    v `delay_report`. Ničle je prej ujel poseben `_nicle` (16. 10. 2026: del
    vlakov je SŽ za en odgovor narisal po voznem redu, 7 od 59 ob 14:28:52;
    LP 3234 iz +21 na 0; 11.--16. 10. so ničle zadele 611 od 1 444 voženj z
    zamudo); višjih ni nič. Cena: nova vrednost zamuja en spremenjen odgovor
    (15 s). Pravila „nazaj“, „prvi prihod“ in ponastavitev (`zapisi`) veljajo
    za potrjena stanja.

    Dosje (`_v_dosje`) dobi vse surovo; to sito je samo za `run`, `sz_zamuda`,
    poročilo in trenutno zamudo.
    """
    global _prejsnji
    zdaj_stanja = {(p[0], p[1]): (p[2], p[3], p[4]) for p in (*pripete, *prihodnje)}
    zapisana = {}
    for k in zdaj_stanja:
        if k in _prejsnji and _prejsnji[k] == zdaj_stanja[k]:
            continue
        r = conn.execute(
            "SELECT stop_seq, delay_s FROM sz_zamuda WHERE trip_id = ? AND service_date = ? "
            "ORDER BY zadnjic_ts DESC, stop_seq DESC LIMIT 1", k).fetchone()
        zapisana[k] = tuple(r) if r else None
    nepotrjeni = {k for k, st in zdaj_stanja.items()
                  if _prejsnji.get(k) != st and zapisana.get(k) != st[:2]}
    _prejsnji = zdaj_stanja

    def drzi(vrstice):
        return [p for p in vrstice if (p[0], p[1]) not in nepotrjeni]
    return drzi(pripete), drzi(prihodnje), nepotrjeni


def zapisi(conn: sqlite3.Connection, pripete: list[tuple], zdaj: float) -> dict:
    """Potrjene zamude (`potrdi`) v `sz_zamuda`, `run` in `obs` (in `delay_report`).

    Dve varovali, obe izmerjeni na zemljevidu:

    * **Vlak ne gre nazaj z isto ali manjšo zamudo.** Zemljevid je vozni
      red plus trenutna zamuda, ne sled: vlak, ki zamudo nabira, gre naprej,
      ko poteče stara zamuda, in skoči nazaj, ko SŽ zamudo poveča (RG 615 16.
      10. 2026: „naslednja Šentjur“ / „naslednja Celje“ izmenoma, +3, +5, +8).
      Nazaj z isto zamudo je nihanje in se ne zapiše; z večjo je zvišana
      zamuda in velja (ko jo je potrdil še en odgovor), postanki za
      njim pa niso bili prevoženi in gredo iz `run` (`preklicanih`). Do 16. 10. se ni
      zapisalo nobeno „nazaj“ (LPV 2616 10. 10.: „naslednja Ljubljana Tivoli,
      +9“ po odhodu iz Ljubljane s +0) -- in vlak, ki ga je SŽ najprej risal po
      voznem redu, je ostal točen: LPV 2907 16. 10. 10 min +0 namesto +7. Na
      13 min zemljevida je bila prikazana zamuda prenizka za 3 min ali več
      63-krat od 2 453, zdaj enkrat. Cena: postanek zadaj dobi trenutno
      zamudo, ne odhodne.
    * **Na cilju šteje prvi prihod** (glava modula), in ničla po zamudi nad
      `PONASTAVITEV_S` ni prihod, ampak ponastavitev. Razen kadar je SŽ vlak
      po prihodu spet pokazal na progi: takrat je bil prihod prezgoden.

    **Prihod in odhod iz istega vira.** Zemljevid pove eno zamudo. Prvi zapis
    za postanek (v `sz_zamuda` ga še ni) nastavi prihod IN odhod, ker zemljevid
    postanek preklopi ob prihodu po uri, torej je prva vrednost prihodna;
    vsak naslednji samo odhod. Prej je prihod ostal napoved derp.si: od 1. 11.
    671 postankov „stal >= 10 min“ pri postanku <= 2 min, prihod 0 v 664.
    Na cilju sta prihod in odhod enaka.
    """
    ts = int(zdaj)
    izid = {"zapisanih": 0, "nazaj": 0, "ponastavljenih": 0, "porocil": 0, "preklicanih": 0}
    for trip_id, dan, seq, zamuda, je_prihod in pripete:
        zadnji = conn.execute(
            "SELECT stop_seq, delay_s FROM sz_zamuda WHERE trip_id = ? AND service_date = ? "
            "ORDER BY stop_seq DESC LIMIT 1", (trip_id, dan)).fetchone()
        # Ponastavitev na cilju primerja z ZADNJO besedo SŽ, ne s postankom
        # najdlje naprej (ta je po sprejeti ničli sam ničla).
        prejsnja = conn.execute(
            "SELECT delay_s, stop_seq FROM sz_zamuda WHERE trip_id = ? AND service_date = ? "
            "ORDER BY zadnjic_ts DESC, stop_seq DESC LIMIT 1", (trip_id, dan)).fetchone()
        if zadnji and seq < zadnji[0] and zamuda <= zadnji[1]:
            izid["nazaj"] += 1
            continue
        if zadnji and seq < zadnji[0]:
            # Nazaj z večjo zamudo: postankov za `seq` vlak ni prevozil, SŽ ga
            # je tja narisal po voznem redu ali z nižjo zamudo. Njihov prvi
            # zapis je postal prihod in ga poznejši ne popravi, zato gredo iz
            # `run` in `sz_zamuda` (tudi `seq`): naslednji zapis je spet prvi,
            # prihod = odhod. `obs` ostane, zemljevid jih je res kazal.
            # LPV 2401 7. 11. 2026: 4--7 po voznem redu 0 od 04.36 do 04.46, ob
            # 04.47 nazaj na 4 s +9 -> prihod 0, odhod +9. Po objavi 88ec114 6.
            # 11. tak skok pri 73 od 78 voženj-dni s kršitvijo, ura nazaj 54 od
            # 242 (22,3 %); ponovitev s tem pravilom 5 (2,1 %), stal >= 10 min
            # 46 -> 4, nikoli znova doseženi 3 od 4 039 postankov.
            if not conn.in_transaction:
                conn.execute("BEGIN IMMEDIATE")
            izid["preklicanih"] += conn.execute(
                "DELETE FROM run WHERE trip_id = ? AND service_date = ? AND stop_seq > ? "
                "AND stop_seq IN (SELECT stop_seq FROM sz_zamuda WHERE trip_id = ? "
                "                 AND service_date = ? AND stop_seq > ?)",
                (trip_id, dan, seq, trip_id, dan, seq)).rowcount
            conn.execute("DELETE FROM sz_zamuda WHERE trip_id = ? AND service_date = ? "
                         "AND stop_seq >= ?", (trip_id, dan, seq))
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
        prvi = conn.execute(
            "SELECT 1 FROM sz_zamuda WHERE trip_id = ? AND service_date = ? AND stop_seq = ?",
            (trip_id, dan, seq)).fetchone() is None
        # Prvi zapis (prihod) gre v dnevnik vedno, tudi kadar je enak zadnji
        # vrstici `obs`: brez tega dnevnik ne vidi prihoda ne skoka nazaj na
        # postanek z isto vrednostjo, zgodovine iz njega ni mogoče ponoviti.
        # LPV 2401 7. 11. 2026: derp.si ob 02.54 0/0 na vseh 17 postankih,
        # prvi zapisi zemljevida 04.24--04.46 v `obs` niso šli.
        iz_lege.zapisi_meritev(conn, trip_id, dan, seq, zamuda if (je_prihod or prvi) else None,
                               zamuda, ts, ohrani=True, v_dnevnik=prvi)
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


def _osvezi_trenutne(pripete: list[tuple], prihodnje: list[tuple], zdaj: float,
                     nepotrjeni: frozenset | set = frozenset()) -> None:
    """Trenutna zamuda iz potrjenih stanj (`potrdi`); pri nepotrjenem vlaku
    velja, kar je SŽ rekel prej (in ob izteku `SVEZA_TRENUTNA_S` ne velja)."""
    global _trenutne
    novo = {}
    for trip_id, dan, seq, zamuda, je_prihod in (*pripete, *prihodnje):
        if not je_prihod:
            novo[(trip_id, dan)] = (zamuda, int(zdaj), seq)
    for k in nepotrjeni:
        if k in _trenutne:
            novo[k] = _trenutne[k]
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
        if je_prihod:
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


#: Ura nazaj in prihod po odhodu: od te razlike naprej je vožnja nedosledna
#: (zamuda je v minutah, dve minuti sta že dva koraka).
DOSLED_PRAG_S = 120
#: Primerov (številk vlakov) v vrstici zdravja.
DOSLED_PRIMEROV = 5

_DOSLED_SQL = (
    "SELECT r.trip_id, t.train_no, r.stop_seq, t.first_seq, t.last_seq, "
    "       r.delay_arr, r.delay_dep, s.arr_s, s.dep_s "
    "FROM run r JOIN trip t ON t.trip_id = r.trip_id "
    "JOIN sched s ON s.trip_id = r.trip_id AND s.stop_seq = r.stop_seq "
    "WHERE r.service_date = ? AND t.network = 'zeleznica' AND t.mode = 'vlak' "
    "ORDER BY r.trip_id, r.stop_seq")


def dosled(conn: sqlite3.Connection, dan: str) -> dict:
    """Doslednost `run` za vlake dneva: koliko voženj ima uro nazaj ali prihod
    po odhodu (straža `zdravje` „dosled_vlaki“).

    * **Ura nazaj**: čas postanka (vozni red + `COALESCE(delay_dep, delay_arr)`;
      na cilju prihod) je za >= `DOSLED_PRAG_S` večji od časa naslednjega
      izmerjenega postanka. Izhodišče se ne šteje (feed ga pošlje kot smet).
    * **Prihod po odhodu**: na istem vmesnem postanku je prihod (vozni red +
      `delay_arr`) za >= `DOSLED_PRAG_S` za odhodom (vozni red + `delay_dep`).

    Zakaj: 1.--6. 11. 2026 je bila ura nazaj pri 6,9 % voženj-dni (prej 1,3 %)
    in „stal >= 10 min“ pri postanku <= 2 min pri 25,4 % (prej 2,0 %), ker je
    zemljevid pisal samo odhod, prihod pa je ostal napoved derp.si; nobena
    vrstica zdravja tega ni videla. Računa se po `run_date`, omrežje v
    poizvedbi; šteje vožnje z >= 2 izmerjenima postankoma.
    """
    po_voznjah: dict[str, list] = defaultdict(list)
    ime: dict[str, str] = {}
    for r in conn.execute(_DOSLED_SQL, (dan,)):
        po_voznjah[r["trip_id"]].append(r)
        ime[r["trip_id"]] = r["train_no"]
    voznj = 0
    nazaj: set[str] = set()
    po_odhodu: set[str] = set()
    for tid, vrstice in po_voznjah.items():
        if len(vrstice) < 2:
            continue
        voznj += 1
        prej = None
        for r in vrstice:
            seq = r["stop_seq"]
            if seq == r["first_seq"]:
                continue
            arr_t = r["arr_s"] if r["arr_s"] is not None else r["dep_s"]
            dep_t = r["dep_s"] if r["dep_s"] is not None else r["arr_s"]
            cilj = seq == r["last_seq"]
            d_arr, d_dep = r["delay_arr"], r["delay_dep"]
            if not cilj and d_arr is not None and d_dep is not None and (
                    arr_t + d_arr) - (dep_t + d_dep) >= DOSLED_PRAG_S:
                po_odhodu.add(tid)
            if cilj:
                d, t0 = (d_arr if d_arr is not None else d_dep), arr_t
            else:
                d, t0 = (d_dep if d_dep is not None else d_arr), dep_t
            if d is None or t0 is None:
                continue
            kdaj = t0 + d
            if prej is not None and prej - kdaj >= DOSLED_PRAG_S:
                nazaj.add(tid)
            prej = kdaj
    slabe = nazaj | po_odhodu
    return {"dan": dan, "voznj": voznj, "ura_nazaj": len(nazaj),
            "prihod_po_odhodu": len(po_odhodu), "nedoslednih": len(slabe),
            "primeri": sorted(ime[t] for t in slabe)[:DOSLED_PRIMEROV], "ts": int(time.time())}


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


def odtis_jedra(vrstice: list[dict]) -> str:
    """Odtis iz (številka, Vrsta, Postaja, Zamuda_cas) vseh vlakov."""
    jedro = sorted((str(r.get("St_vlaka")), str(r.get("Vrsta")), str(r.get("Postaja")),
                    str(r.get("Zamuda_cas"))) for r in vrstice)
    return hashlib.blake2s(json.dumps(jedro, ensure_ascii=False).encode(),
                           digest_size=8).hexdigest()


#: Kar zemljevid o vlaku pove sproti; drugo gre v telo dosjeja. `St` = vrstni red.
_SPROTNO = frozenset({"St", "Postaja", "St_postaje", "Odhod", "Koordinate", "Vrsta",
                      "Zamuda_cas", "Predviden_prihod"})


def _v_dosje(vrstice: list[dict], st: dict[str, str], pripete: list[tuple],
             prihodnje: list[tuple], zdaj: float) -> None:
    """Vsak vlak z zemljevida v `dosje`, kot `vlak-<številka>`: lastnega id-ja
    vlak nima, voznega pa v dnevu en sam."""
    if not dosje.vklopljen():
        return
    pri = {st[p[0]]: p for p in pripete if p[0] in st}
    pre = {st[p[0]] for p in prihodnje if p[0] in st}
    for r in vrstice:
        surova = str(r.get("St_vlaka") or "")
        n = stevilka(surova) or surova
        p = pri.get(n)
        razlogi = []
        if p is None and n in pre:
            razlogi.append("odhod_v_prihodnosti")
        elif p is None and r.get("Vrsta") != 0 and not je_avtobus(r):
            razlogi.append("nepripet")
        try:
            lon, lat = (float(x) for x in str(r.get("Koordinate") or "").split(","))
        except ValueError:
            lon = lat = None
        stalno = {k: v for k, v in r.items() if k not in _SPROTNO}
        dosje.opazi("sz", n and f"vlak-{n}", None, lat, lon,
                    trip_id=p[0] if p else None, dan=p[1] if p else None, razlogi=razlogi,
                    kljuc=tuple(sorted(stalno.items())), telo=stalno,
                    sprotno={k: r[k] for k in _SPROTNO if k in r}, zdaj=zdaj)


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
    dosje.varno(_v_dosje, vrstice, st, pripete, prihodnje, zdaj)
    # Dosje je dobil vse surovo; naprej samo potrjena stanja.
    pripete, prihodnje, nepotrjeni = potrdi(conn, pripete, prihodnje)
    stevci["nepotrjenih"] = len(nepotrjeni)
    stevci.update(zapisi(conn, pripete, zdaj))
    _osvezi_trenutne(pripete, prihodnje, zdaj, nepotrjeni)
    stevci["skladnost"] = skladnost(conn, pripete, zdaj)
    stevci["odtis"] = _odtis or ""
    # Straža zamrznitve (`zdravje`, „se ne spreminja“) gleda jedro, ne cel
    # odgovor: ta se spremeni tudi, kadar SŽ ne pove nič novega (polja, ki
    # tečejo z uro). Jedro = kar o vlaku ve SŽ.
    stevci["jedro"] = jedro = odtis_jedra(vrstice)
    stevci["spremenjeno_ts"] = (prej.get("spremenjeno_ts") if prej.get("jedro") == jedro
                                else None) or int(zdaj)
    stevci["ts"] = int(zdaj)
    db.set_meta(conn, "zamude_sz", json.dumps(stevci, sort_keys=True))
    conn.commit()
    return stevci


#: Zemljevid, čigar jedro (`odtis_jedra`) se ob vlakih toliko časa ne spremeni,
#: ne vodi več (`vodi`): derp.si bere isti zemljevid prek `api.modra.ninja` in
#: ima ob zamrznjenem NAŠEM branju (Chrome, Cloudflare) svežega. Najdaljši zdrav
#: presledek jedra ob ≥ 3 vlakih 28.--31. 10. 2026: 8 min 15 s. = `zdravje.SZ_ZAMRZNJEN_S`.
ZAMRZNJEN_S = 600


def vodi(s: dict, zdaj: float) -> bool:
    """Ali odgovor zemljevida sme voditi vlake (derp.si jih takrat ne piše,
    `iz_lege.sz_vodi`). Samo, kadar ima vlak, ki ga pripnemo -- prazen (`null`)
    ob vlakih je prej utišal derp.si za vse vlake, nobena zamuda vlaka nikjer
    (presoja 31. 10. 2026; ponoči je prazen po pravici) -- in dokler se jedro
    spreminja: zamrznjen zemljevid je kot molk (isto pravilo kot
    `iz_lege.FEED_ZAMRZNJEN_S` za derp.si)."""
    vlakov = s.get("vlakov", 0)
    if vlakov <= s.get("nepripetih", 0):
        return False
    return vlakov < 3 or zdaj - (s.get("spremenjeno_ts") or zdaj) <= ZAMRZNJEN_S


#: Od kdaj vodi zemljevid SŽ vlake (`popravi_vlake`).
POPRAVI_OD = "2026-10-10"
#: Do kdaj velja podpis zapisa zemljevida `delay_arr IS NULL AND delay_dep IS NOT
#: NULL` (`obs.observed_at`, 6. 11. 2026 ob 14:45:35, objava `zapisi` s prvim
#: zapisom prihod = odhod). Pozneje zemljevid ob prvem zapisu postanka piše
#: OBA polja, zato je zapis s samim odhodom osvežitev: njegova vrednost je
#: lahko poznejša zamuda (zamuda se je med postankom spremenila) in bi prihod
#: pokvarila. Postanek, katerega prvi zapis zemljevida je po meji, se preskoči.
POPRAVI_DO_TS = 1793972735
#: Razlika, od katere prihod v `run` popravimo: minuta je ločljivost zamude.
POPRAVI_PRAG_S = 60
#: Zapis „nazaj“ je zastarel, če je naslednji zapis na kasnejšem postanku nižji
#: za več kot rezerva postankov vmes in toliko (kot `skladnost`).
ZASTAREL_PRAG_S = 120

_ZEMLJEVID_ODHOD = (
    "SELECT r.trip_id, r.stop_seq, r.delay_arr, o.delay_dep FROM run r "
    "JOIN trip t ON t.trip_id = r.trip_id "
    "JOIN obs o ON o.trip_id = r.trip_id AND o.service_date = r.service_date "
    "          AND o.stop_seq = r.stop_seq "
    "WHERE r.service_date = ? AND t.network = 'zeleznica' AND t.mode = 'vlak' "
    "  AND r.stop_seq != t.last_seq AND r.delay_arr IS NOT NULL "
    "  AND o.delay_arr IS NULL AND o.delay_dep IS NOT NULL AND o.observed_at < ? "
    "  AND o.feed_ts = (SELECT MIN(o2.feed_ts) FROM obs o2 "
    "                   WHERE o2.trip_id = o.trip_id AND o2.service_date = o.service_date "
    "                     AND o2.stop_seq = o.stop_seq AND o2.observed_at < ? "
    "                     AND o2.delay_arr IS NULL AND o2.delay_dep IS NOT NULL)")
_ZEMLJEVID_CILJ = (
    "SELECT r.trip_id, r.stop_seq FROM run r JOIN trip t ON t.trip_id = r.trip_id "
    "WHERE r.service_date = ? AND t.network = 'zeleznica' AND t.mode = 'vlak' "
    "  AND r.stop_seq = t.last_seq AND r.delay_arr IS NOT NULL "
    # Tudi odhod, ki se od prihoda razlikuje: na cilju je to ostanek napovedi
    # derp.si (LPV 2206 6. 11. 2026: prihod +1, odhod +15).
    "  AND (r.delay_dep IS NULL OR r.delay_dep != r.delay_arr) "
    "  AND EXISTS (SELECT 1 FROM obs o WHERE o.trip_id = r.trip_id "
    "              AND o.service_date = r.service_date AND o.stop_seq = r.stop_seq "
    "              AND o.delay_arr IS NOT NULL AND o.delay_dep IS NULL AND o.observed_at < ?)")
#: Zapisi zemljevida (podpis zgoraj, pred mejo) vlakov dneva po času.
_ZEMLJEVID_ZAPISI = (
    "SELECT o.trip_id, o.stop_seq, o.delay_dep FROM (SELECT DISTINCT r.trip_id FROM run r "
    "  JOIN trip t ON t.trip_id = r.trip_id WHERE r.service_date = ? "
    "  AND t.network = 'zeleznica' AND t.mode = 'vlak') v "
    "JOIN obs o ON o.trip_id = v.trip_id AND o.service_date = ? "
    "WHERE o.delay_arr IS NULL AND o.delay_dep IS NOT NULL AND o.observed_at < ? "
    "ORDER BY o.trip_id, o.feed_ts, o.stop_seq")


def zastareli_visji(zapisi: list[tuple[int, int]], rezerva) -> list[tuple[int, int, int]]:
    """Zapisi zemljevida ene vožnje po času [(stop_seq, zamuda_s)] -> zastareli
    [(stop_seq, zamuda_s, zadnja_prejsnja_vrednost)].

    Zapis (k, v) je „nazaj“, kadar je bil pred njim zapisan postanek > k. Zastarel
    je, kadar je PRVI naslednji zapis na postanku j > k nižji od v za več kot
    `rezerva(k, j)` (dolgi postanki vmes) + `ZASTAREL_PRAG_S`. Pri pravem „vlak
    stoji, SŽ dviguje zamudo“ dobijo naslednji postanki >= v - rezerva, zato se
    ne sproži. Tretji člen je zadnja vrednost zemljevida za k pred zapisom
    (None, če je ni).

    Zakaj: zastarel odgovor zemljevida (en odgovor, 15 s) je pred popravkom
    `potrdi` šel skozi pravilo „nazaj z večjo zamudo velja“. LPV 2206 6. 11.
    2026: Hrastnik (postanek 2) ob 07:57:18 in Zagorje (4) ob 08:07:48 +15 min
    (900 s), prava +2 in +3 (120 in 180 s).
    """
    out = []
    najvec = 0
    for i, (k, v) in enumerate(zapisi):
        nazaj = najvec > k
        najvec = max(najvec, k)
        if not nazaj:
            continue
        naslednji = next(((j, w) for j, w in zapisi[i + 1:] if j > k), None)
        if naslednji is None or naslednji[1] >= v - rezerva(k, naslednji[0]) - ZASTAREL_PRAG_S:
            continue
        prej = next((u for q, u in reversed(zapisi[:i]) if q == k), None)
        out.append((k, v, prej))
    return out


#: Od kdaj je `run.feed_ts` vlakov naš čas branja (zemljevid SŽ vodi od 10. 10.
#: 2026). Prej je bil časovni žig derp.si, ki se ne premakne, dokler se vožnja
#: ne spremeni: pravilo „napoved“ spodaj bi tam zadelo 158 508 od 211 301
#: postankov (75 %, 1. 9.--9. 10.), večinoma lažno.
NAPOVED_OD = "2026-10-10"
NAPOVED_TOLERANCA_S = 120

_NAPOVEDI = (
    "SELECT r.trip_id, r.stop_seq FROM run r JOIN trip t ON t.trip_id = r.trip_id "
    "JOIN sched s ON s.trip_id = r.trip_id AND s.stop_seq = r.stop_seq "
    "WHERE r.service_date = ? AND t.network = 'zeleznica' AND t.mode = 'vlak' "
    "  AND r.feed_ts < ? "
    "  AND r.feed_ts < ? + COALESCE(s.arr_s, s.dep_s) "
    "                    + COALESCE(r.delay_dep, r.delay_arr) - ?")


def popravi_vlake(conn: sqlite3.Connection, od: str = POPRAVI_OD, zapisi: bool = False) -> dict:
    """Prihod v `run` iz napovedi derp.si zamenja z izmerjenim iz zemljevida in
    odpravi zastarele višje zapise.

    Zemljevid je pisal samo odhod (`zapisi` do 6. 11. 2026), prihod je ostal
    napoved derp.si (od 1. 11. 2026 671 postankov „stal >= 10 min“ pri postanku
    <= 2 min, prihod 0 v 664). Zapis zemljevida v `obs` se pozna po
    `delay_arr IS NULL AND delay_dep IS NOT NULL` (derp.si piše vedno oba) --
    samo pred `POPRAVI_DO_TS`. Pravilo: `run.delay_arr` = `delay_dep`
    NAJZGODNEJŠEGA takega zapisa postanka (prva vrednost zemljevida je
    prihodna), če se razlikuje za >= `POPRAVI_PRAG_S`; na cilju z zapisom
    zemljevida (prihod brez odhoda) `delay_dep` = `delay_arr`.

    **Zastareli višji zapisi** (`zastareli_visji`): če je `run.delay_dep`
    takega postanka še enak zapisani vrednosti, dobi zadnjo vrednost zemljevida
    za ta postanek pred njo (brez nje ostane).

    **Nepotrjene napovedi** (od `NAPOVED_OD`, pred `POPRAVI_DO_TS`): vrstica,
    katere zadnji zapis je starejši od voznega reda + zamude − 2 min, ni nikoli
    bila meritev -- napoved derp.si ob zagonu, ki je ni nihče prepisal. Gre iz
    `run` (v `obs` ostane). LPV 2206 6. 11. 2026: Zidani Most +15 iz 07:37:37,
    vlak je odpeljal +2; 10. 10.--6. 11. 297 takih vrstic, 32 na izhodišču.

    Brez `zapisi` samo šteje. Po dnevih, vsak v svoji transakciji (kot
    `kajros prune`): dolg zapis ne zaklene zajema. Vrne števila po dnevih:
    postankov in voženj-dni.
    """
    dnevi = [r[0] for r in conn.execute(
        "SELECT DISTINCT service_date FROM run WHERE service_date >= ? ORDER BY 1", (od,))]
    izid: dict = {"dnevi": {}, "postankov": 0, "voznj": 0, "cilj_postankov": 0,
                  "zastarelih": 0, "zastarelih_voznj": 0, "napovedi": 0, "zapisano": zapisi}
    for dan in dnevi:
        pot = [(t, q, d) for t, q, a, d in conn.execute(
            _ZEMLJEVID_ODHOD, (dan, POPRAVI_DO_TS, POPRAVI_DO_TS)) if abs(a - d) >= POPRAVI_PRAG_S]
        cilj = [(t, q) for t, q in conn.execute(_ZEMLJEVID_CILJ, (dan, POPRAVI_DO_TS))]
        po_voznjah: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for t, q, d in conn.execute(_ZEMLJEVID_ZAPISI, (dan, dan, POPRAVI_DO_TS)):
            po_voznjah[t].append((q, d))
        rezerve = stats._slack_ahead(conn, list(po_voznjah))
        stalo = {(t, q): d for t, q, d in conn.execute(
            "SELECT trip_id, stop_seq, delay_dep FROM run WHERE service_date = ?", (dan,))}
        zastareli = []
        for t, zap in po_voznjah.items():
            r = rezerve.get(t, ())
            for k, v, prej in zastareli_visji(
                    zap, lambda k, j, r=r: sum(x for q, x in r if k < q <= j)):
                if prej is not None and stalo.get((t, k)) == v:
                    zastareli.append((t, k, prej))
        napovedi = (conn.execute(_NAPOVEDI, (dan, POPRAVI_DO_TS, int(stats.polnoc(dan)),
                                             NAPOVED_TOLERANCA_S)).fetchall()
                    if dan >= NAPOVED_OD else [])
        if not pot and not cilj and not zastareli and not napovedi:
            continue
        if zapisi:
            with conn:
                conn.executemany(
                    "UPDATE run SET delay_arr = ? WHERE trip_id = ? AND service_date = ? "
                    "AND stop_seq = ?", [(d, t, dan, q) for t, q, d in pot])
                conn.executemany(
                    "UPDATE run SET delay_dep = delay_arr WHERE trip_id = ? "
                    "AND service_date = ? AND stop_seq = ? "
                    "AND (delay_dep IS NULL OR delay_dep != delay_arr)",
                    [(t, dan, q) for t, q in cilj])
                conn.executemany(
                    "UPDATE run SET delay_dep = ? WHERE trip_id = ? AND service_date = ? "
                    "AND stop_seq = ?", [(d, t, dan, q) for t, q, d in zastareli])
                conn.executemany(
                    "DELETE FROM run WHERE trip_id = ? AND service_date = ? AND stop_seq = ?",
                    [(t, dan, q) for t, q in napovedi])
        voznje = {t for t, *_ in pot} | {t for t, _ in cilj}
        izid["dnevi"][dan] = {"postankov": len(pot), "cilj_postankov": len(cilj),
                              "voznj": len(voznje), "zastarelih": len(zastareli),
                              "zastarelih_voznj": len({t for t, *_ in zastareli}),
                              "napovedi": len(napovedi)}
        izid["postankov"] += len(pot)
        izid["cilj_postankov"] += len(cilj)
        izid["voznj"] += len(voznje)
        izid["zastarelih"] += len(zastareli)
        izid["zastarelih_voznj"] += len({t for t, *_ in zastareli})
        izid["napovedi"] += len(napovedi)
    return izid


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
                if vodi(s, zdaj):
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
