"""Zamude mestnega LPP z LPP-jevih zaslonov (`data.lpp.si`) -- drugi vir poleg derp.si.

Zakaj: 8. 10. 2026 je strežnik RT derp.si od 16:00 zavračal povezave in
mestni LPP je ostal brez zamud in leg, LPP-jev lastni API pa je odgovarjal.
Do tedaj je bil ta vir samo za prikaz (`lpp.py`).

Kaj vir pove (izmerjeno 8. 10. 2026): `station/arrival` za eno postajališče
vrne vsa vozila, ki nanj prihajajo -- vzorec proge (`trip_id`, tretja
komponenta našega id-ja), `vehicle_id`, `eta_min` v celih minutah in vrsto
(0 napoved, 1 po voznem redu, 2 prihaja, 3 obvoz). Vožnje ne pove. Pri
vrsti 1 je eta vozni red: pri 470 od 539 takih prihodov je bila najbližja
vožnja našega voznega reda v 60 s (mediana 43 s, eta je cela minuta). Vrsta
1 zato ni meritev in je ne pišemo.

**Vozilo -> vožnja** prek `vehicle_id` iz derp.si (`vehicle_now`), kot v
`lpp.eta_po_postankih`: derp.si vožnjo vozila pozna, LPP-jev odprti API ne.
Velja tudi, ko derp.si utihne, dokler `vehicle_now` lego hrani (uro), a le,
če ima vožnja isti vzorec in se zamuda ujema z zadnjo znano zamudo vožnje
(`SKLADNO_S`) -- vozilo, ki je medtem začelo novo vožnjo, pade ven. Vira se
morata ujemati, da ju sploh povežemo. **Po voznem redu samem ne pripenjamo**:
v obhodu 8. 10. ob 17:50 je imelo 398 od 758 živih prihodov dve ali več
kandidatk z zamudo od -3 do +20 min (linije na 5-10 min), edina kandidatka
pa je derp-ovo vožnjo zadela 67-krat od 98 -- zgreši prav pri velikih
zamudah. Sproti se meri naprej (`po_voznem_redu` v `meta.zamude_lpp`).

**Kaj beremo**: ne vseh 658 postajališč na 74 vzorcih, ampak tista, med
katerimi ima vsako zaporedje postajališč (172 jih je na 74 vzorcih) največ
`config.LPP_POSTAJ_KORAK - 1` neizbranih zapored (`izberi`): pri 12 jih je
76, pri 8 132. Zahteva je mediana 50 ms, a z repom do 10 s -- 177
postajališč je ena za drugo trajalo 267 s, 75 z dvema delavcema 36 s.
`route/arrivals-on-route` bi dal ves vzorec naenkrat, a ga LPP računa
6-19 s (mediana 7,4 s na 206 vzorcih) -- za njihov strežnik dražje.

**Kam gre**: kot `zamude_sz` -- vsaka vrednost v `lpp_zamuda`, v `run` le,
kadar derp.si vožnje ne nosi (`iz_lege.brez_feeda`), tedaj `v_run = 1`.
Kadar nosita oba, `primerjava()` pove, kako se razhajata. Vrednost je
napoved prihoda na postajališče, kot pri derp.si, ki pri mestnem LPP pošilja
samo postanke pred vozilom (`zajem.md`).
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Callable

import requests

from . import collector, config, db, iz_lege, lpp, stats, zdravje

_URL = "https://data.lpp.si/api/station/arrival"

#: Vrste prihoda, ki so napoved iz žive lege (`lpp.VRSTE`).
ZIVE = frozenset({0, 2})
#: Zamuda, pri kateri derp-ova vožnja vozila sploh pride v poštev.
DERP_OKNO_S = (-600, 3600)
#: Vozilo je še na derp-ovi vožnji, kadar se LPP-jeva zamuda z zadnjo znano
#: zamudo te vožnje ujema na toliko. Vozilo, ki je medtem začelo naslednjo
#: vožnjo istega vzorca, bi bilo glede na staro pozno za cel obrat linije:
#: 8. 10. 2026 ob 18:22, z legami derp.si izpred 14 min, je imelo brez tega
#: 195 pripetih prihodov mediano zamude 22 min in p90 50 min, edina kandidatka
#: po voznem redu pa se je z derp-ovo vožnjo ujela le 74-krat od 145.
SKLADNO_S = 600
#: Okno, v katerem se šteje kandidatke po voznem redu (samo za meritev).
VR_OKNO_S = (-180, 1200)
#: Dve vzporedni zahtevi: ena za drugo je obhod 97 postajališč trajal dlje od
#: razmika, več bi LPP-jev strežnik obremenilo brez potrebe.
DELAVCEV = 2
TIMEOUT_S = 10
#: Kadar ne odgovori niti polovica postajališč, vir ne dela.
NAJVEC_NAPAK = 0.5


def izberi(vzorci: dict, teze: dict, korak: int) -> set[str]:
    """Postajališča, med katerimi ima vsak vzorec največ `korak - 1`
    neizbranih zapored. Požrešno: vsakič tisto, ki pokrije največ voženj v še
    odprtih vrzelih -- tako so prometna postajališča izbrana prva."""
    izbrane: set[str] = set()
    while True:
        glas: dict[str, int] = defaultdict(int)
        for v, p in vzorci.items():
            zadnja = -1
            for i in range(len(p) + 1):
                if i == len(p) or p[i] in izbrane:
                    if i - zadnja - 1 >= korak:
                        for s in p[zadnja + 1:i]:
                            glas[s] += teze.get(v, 1)
                    zadnja = i
        if not glas:
            return izbrane
        izbrane.add(max(glas, key=lambda s: (glas[s], s)))


def vozni_red(conn: sqlite3.Connection, dnevi: tuple[str, str],
              korak: int) -> tuple[set[str], dict]:
    """(izbrana postajališča, (vzorec, stop_id) -> [(trip_id, dan, stop_seq,
    prihod po voznem redu, zadnji postanek)]) za mestni LPP včeraj in danes."""
    def build():
        poti: dict[str, dict[str, list]] = defaultdict(dict)
        for r in conn.execute(
                "SELECT t.trip_id, sd.date, s.stop_seq, s.stop_id, "
                "       COALESCE(s.arr_s, s.dep_s) AS t_s, t.last_seq "
                "FROM trip t JOIN service_day sd ON sd.service_id = t.service_id "
                "     AND sd.date IN (?, ?) "
                "JOIN sched s ON s.trip_id = t.trip_id "
                "WHERE t.agency = 'lpp' ORDER BY t.trip_id, s.stop_seq", dnevi):
            if r["t_s"] is None:
                continue
            poti[r["trip_id"]].setdefault(r["date"], []).append(
                (r["stop_seq"], r["stop_id"], stats.polnoc(r["date"]) + r["t_s"],
                 r["stop_seq"] == r["last_seq"]))
        # Po zaporedju postajališč, ne po vzorcu: vožnje istega vzorca imajo
        # lahko različna (na razvojnem voznem redu je bila zato vrzel 12
        # postankov pri koraku 12).
        teze: dict[tuple[str, ...], int] = defaultdict(int)
        for po_dnevih in poti.values():
            for postanki in po_dnevih.values():
                teze[tuple(p[1] for p in postanki)] += 1
        izbrane = izberi({k: list(k) for k in teze}, teze, korak)
        po_postaji: dict[tuple[str, str], list] = defaultdict(list)
        for tid, po_dnevih in poti.items():
            v = _vzorec(tid)
            for dan, postanki in po_dnevih.items():
                for seq, sid, kdaj, zadnji in postanki:
                    if sid in izbrane:
                        po_postaji[(v, sid)].append((tid, dan, seq, kdaj, zadnji))
        return izbrane, dict(po_postaji)

    return collector._cached(conn, "vozni_red_lpp", (dnevi, korak), build)


def _vzorec(trip_id: str) -> str:
    return trip_id.rpartition("|")[2].lower()


def derp_vozila(conn: sqlite3.Connection, zdaj: float) -> dict[str, tuple]:
    """vehicle_id -> (trip_id, dan, zadnja zamuda vožnje v `run` ali None)
    zadnje lege, ki jo derp.si pozna. Lega mestnega LPP dneva ne nosi
    (`service_date` NULL), njegov `trip_id` pa je za vsak dan svoj."""
    out = {}
    for r in conn.execute(
            "SELECT v.vehicle_id, v.trip_id, v.service_date, "
            "       (SELECT COALESCE(r.delay_dep, r.delay_arr) FROM run r "
            "        WHERE r.trip_id = v.trip_id ORDER BY r.feed_ts DESC LIMIT 1) AS zamuda "
            "FROM vehicle_now v WHERE v.vehicle_id IS NOT NULL AND v.seen_ts >= ? "
            "ORDER BY v.seen_ts", (int(zdaj) - 3600,)):
        out[r["vehicle_id"].lower()] = (r["trip_id"], r["service_date"], r["zamuda"])
    return out


def pripni(prihod: dict, stop_id: str, ts: float, po_postaji: dict,
           derp: dict[str, tuple[str, str]]) -> tuple[tuple | None, tuple | None, int]:
    """En prihod -> (po derp.si, po voznem redu, kandidatk po voznem redu).

    Prvo in drugo je (trip_id, dan, stop_seq, zamuda_s, zadnji) ali None;
    drugo samo, kadar je kandidatka v `VR_OKNO_S` ena sama.
    """
    kand = po_postaji.get(((prihod.get("trip_id") or "").lower(), stop_id))
    if not kand or prihod.get("eta_min") is None:
        return None, None, 0
    kdaj = ts + 60 * int(prihod["eta_min"])
    po_derp = None
    voznja = derp.get((prihod.get("vehicle_id") or "").lower())
    if voznja:
        vtid, vdan, vzam = voznja
        for tid, dan, seq, t, zadnji in kand:
            if tid == vtid and vdan in (None, dan):
                z = kdaj - t
                if (DERP_OKNO_S[0] <= z <= DERP_OKNO_S[1]
                        and vzam is not None and abs(z - vzam) <= SKLADNO_S):
                    po_derp = (tid, dan, seq, round(z), zadnji)
                break
    okno = [k for k in kand if VR_OKNO_S[0] <= kdaj - k[3] <= VR_OKNO_S[1]]
    po_vr = None
    if len(okno) == 1:
        tid, dan, seq, t, zadnji = okno[0]
        po_vr = (tid, dan, seq, round(kdaj - t), zadnji)
    return po_derp, po_vr, len(okno)


def razberi(odgovori: list[tuple[str, float, list]], kode: dict[str, str],
            po_postaji: dict, derp: dict) -> tuple[list[tuple], dict]:
    """Odgovori postajališč -> (pripete žive vrednosti, števci).

    `po_voznem_redu` = [enako, drugače, dvoumno, brez]: kolikokrat bi edina
    kandidatka po voznem redu zadela derp-ovo vožnjo istega vozila.
    """
    pripete: dict[tuple, tuple] = {}
    st = {"prihodov": 0, "zivih": 0, "pripetih": 0, "brez_voznega_reda": 0}
    vr = [0, 0, 0, 0]
    for koda, ts, prihodi in odgovori:
        sid = kode[koda]
        for p in prihodi:
            st["prihodov"] += 1
            if p.get("depot") or p.get("type") not in ZIVE:
                continue
            st["zivih"] += 1
            # LPP vozi tudi vožnje, ki jih objavljeni vozni red nima (`zajem.md`).
            if ((p.get("trip_id") or "").lower(), sid) not in po_postaji:
                st["brez_voznega_reda"] += 1
                continue
            po_derp, po_vr, n = pripni(p, sid, ts, po_postaji, derp)
            if po_derp is None:
                continue
            pripete[po_derp[:3]] = po_derp
            if po_vr is not None:
                vr[0 if po_vr[:3] == po_derp[:3] else 1] += 1
            else:
                vr[2 if n > 1 else 3] += 1
    st["pripetih"] = len(pripete)
    st["po_voznem_redu"] = vr
    return list(pripete.values()), st


def zapisi(conn: sqlite3.Connection, pripete: list[tuple], zdaj: float) -> dict:
    """V `lpp_zamuda`; v `run` samo vožnje, ki jih derp.si ne nosi."""
    ts = int(zdaj)
    samo_lpp = oba = 0
    for trip_id, dan, seq, zamuda, zadnji in pripete:
        v_run = iz_lege.brez_feeda(trip_id, zdaj)
        if v_run:
            # Na zadnjem postanku prihod, drugje odhod -- kot `iz_lege.opazuj`.
            iz_lege.zapisi_meritev(conn, trip_id, dan, seq, zamuda if zadnji else None,
                                   None if zadnji else zamuda, ts)
            samo_lpp += 1
        else:
            oba += 1
        conn.execute(
            "INSERT INTO lpp_zamuda(trip_id, service_date, stop_seq, delay_s, "
            "                       prvic_ts, zadnjic_ts, v_run) VALUES(?,?,?,?,?,?,?) "
            "ON CONFLICT(trip_id, service_date, stop_seq) DO UPDATE SET "
            "  delay_s = excluded.delay_s, zadnjic_ts = excluded.zadnjic_ts, "
            "  v_run = MAX(v_run, excluded.v_run)",
            (trip_id, dan, seq, zamuda, ts, ts, int(v_run)))
    conn.commit()
    return {"samo_lpp": samo_lpp, "oba": oba}


def primerjava(conn: sqlite3.Connection, od_ts: int, najvec: int = 0) -> dict:
    """Kako se LPP-jevi zasloni in derp.si razhajata na istih postankih.

    Samo postanki, kjer je `run` od derp.si (`v_run = 0`). `mediana_s` je
    LPP minus derp.si, v sekundah.
    """
    vrstice = conn.execute(
        "SELECT z.trip_id, z.service_date, z.delay_s AS lpp, "
        "       COALESCE(r.delay_dep, r.delay_arr) AS derp, z.zadnjic_ts, t.train_no, "
        "       st.name AS postaja "
        "FROM lpp_zamuda z "
        "JOIN run r ON r.trip_id = z.trip_id AND r.service_date = z.service_date "
        "          AND r.stop_seq = z.stop_seq "
        "JOIN trip t ON t.trip_id = z.trip_id "
        "LEFT JOIN sched s ON s.trip_id = z.trip_id AND s.stop_seq = z.stop_seq "
        "LEFT JOIN station st ON st.stop_id = s.stop_id "
        "WHERE z.zadnjic_ts >= ? AND z.v_run = 0 "
        "  AND COALESCE(r.delay_dep, r.delay_arr) IS NOT NULL", (od_ts,)).fetchall()
    razlike = sorted(r["lpp"] - r["derp"] for r in vrstice)
    out = {
        "parov": len(razlike),
        "v_minuti": sum(abs(d) <= 60 for d in razlike),
        "nad_5_min": sum(abs(d) > 300 for d in razlike),
        "mediana_s": razlike[len(razlike) // 2] if razlike else None,
        "samo_lpp": conn.execute(
            "SELECT COUNT(*) FROM lpp_zamuda WHERE zadnjic_ts >= ? AND v_run = 1",
            (od_ts,)).fetchone()[0],
    }
    if najvec:
        out["najvecje"] = [
            {"linija": r["train_no"], "dan": r["service_date"], "postaja": r["postaja"],
             "lpp_min": round(r["lpp"] / 60), "derp_min": round(r["derp"] / 60),
             "ob": datetime.fromtimestamp(r["zadnjic_ts"], stats.TZ).strftime("%H:%M")}
            for r in sorted(vrstice, key=lambda r: -abs(r["lpp"] - r["derp"]))[:najvec]
            if r["lpp"] != r["derp"]]
    return out


def postajalisca(conn: sqlite3.Connection, izbrane: set[str]) -> dict[str, str] | None:
    """LPP-jeva koda -> naš `stop_id` za izbrana postajališča, ali None."""
    lpp_postaje = lpp._postaje_lpp()
    if not lpp_postaje or not izbrane:
        return None
    sids = sorted(izbrane)
    nasa = [dict(r) for r in conn.execute(
        f"SELECT stop_id, lat, lon FROM station WHERE stop_id IN ({','.join('?' * len(sids))}) "
        "AND lat IS NOT NULL", sids)]
    return lpp.kode_postaj(nasa, lpp_postaje) or None


def _dnevi(zdaj: float) -> tuple[str, str]:
    danes = datetime.fromtimestamp(zdaj, stats.TZ).date()
    return (danes - timedelta(days=1)).isoformat(), danes.isoformat()


def korak(conn: sqlite3.Connection, odgovori: list[tuple[str, float, list]],
          kode: dict[str, str], zdaj: float, napak: int = 0) -> dict:
    """En obhod: pripni, zapiši, povzemi v `meta` za pregled."""
    _, po_postaji = vozni_red(conn, _dnevi(zdaj), config.LPP_POSTAJ_KORAK)
    pripete, st = razberi(odgovori, kode, po_postaji, derp_vozila(conn, zdaj))
    st.update(zapisi(conn, pripete, zdaj))
    st.update(ts=int(zdaj), postaj=len(kode), napak_zahtev=napak,
              primerjava=primerjava(conn, int(zdaj) - 86400))
    db.set_meta(conn, "zamude_lpp", json.dumps(st, sort_keys=True))
    conn.commit()
    return st


def _obhod(kode: dict[str, str]) -> tuple[list[tuple[str, float, list]], int]:
    """Vsa izbrana postajališča: [(koda, čas odgovora, prihodi)], napak."""
    seja = requests.Session()
    seja.headers["User-Agent"] = config.USER_AGENT

    def ena(koda: str):
        try:
            r = seja.get(_URL, params={"station-code": koda}, timeout=TIMEOUT_S)
            r.raise_for_status()
            podatki = r.json().get("data") or {}
            return koda, time.time(), (podatki.get("arrivals") or []
                                       if isinstance(podatki, dict) else [])
        except (requests.RequestException, ValueError):
            return koda, time.time(), None

    with ThreadPoolExecutor(DELAVCEV) as ex:
        izidi = list(ex.map(ena, list(kode)))
    napak = sum(p is None for _, _, p in izidi)
    if izidi and napak > NAJVEC_NAPAK * len(izidi):
        raise RuntimeError(f"data.lpp.si: {napak} od {len(izidi)} postajališč brez odgovora")
    return [(k, ts, p) for k, ts, p in izidi if p is not None], napak


def teci(stop: threading.Event, log: Callable[[str], None]) -> None:
    """Svoja nit: tuj strežnik z repom do 10 s na zahtevo ne sme zamikati
    zajema derp.si."""
    conn = db.connect()
    napak, kode, za = 0, None, None
    try:
        while not stop.is_set():
            zacetek = time.time()
            # Brez tega bi bila ob zagonu vsaka vožnja „samo LPP“ in bi šla v
            # `run` mimo derp.si (glej `zamude_sz.teci`).
            if not iz_lege.feed_prebran():
                stop.wait(10)
                continue
            try:
                # Ponoči vozijo 0-2 avtobusa: obhod 97 postajališč za nič.
                if stats.vozi_zdaj(conn, zacetek)["avtobus"] < zdravje.MIN_VOZENJ:
                    stop.wait(config.LPP_ZAMUDE_SECONDS)
                    continue
                dnevi = _dnevi(zacetek)
                if kode is None or za != (dnevi, db.cache_key(conn)):
                    izbrane, _ = vozni_red(conn, dnevi, config.LPP_POSTAJ_KORAK)
                    kode = postajalisca(conn, izbrane)
                    if kode is None:
                        raise RuntimeError("data.lpp.si: seznama postajališč ni")
                    za = (dnevi, db.cache_key(conn))
                    log(f"zamude LPP: {len(kode)} postajališč od {len(izbrane)} izbranih")
                odgovori, napak_zahtev = _obhod(kode)
                s = korak(conn, odgovori, kode, time.time(), napak_zahtev)
                if napak:
                    log(f"data.lpp.si spet odgovarja (po {napak} napakah)")
                napak = 0
            except Exception as exc:        # noqa: BLE001 -- vir ni naš
                conn.rollback()             # glej `zamude_sz.teci()`
                napak += 1
                if napak == 1:
                    log(f"zamude LPP: {exc}")
                try:
                    s = json.loads(db.get_meta(conn, "zamude_lpp") or "{}")
                    s.update(napaka=str(exc)[:200], napaka_ts=int(time.time()))
                    db.set_meta(conn, "zamude_lpp", json.dumps(s, sort_keys=True))
                    conn.commit()
                except sqlite3.Error:
                    conn.rollback()
            stop.wait(max(5.0, config.LPP_ZAMUDE_SECONDS - (time.time() - zacetek)))
    finally:
        conn.close()
