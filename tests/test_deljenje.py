"""Deljenje lege potnikov: kandidati, varovalke, prehodi in soglasje.

Sintetična proga: tri postaje na vzporedniku 46° N, 0,1° narazen (~7,7 km).
Vlak t1 vozi A -> B -> C, vlak t2 isto progo v nasprotni smeri, ob istem času.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta

import pytest

from kajros import db, deljenje
from kajros.deljenje import TZ

LAT = 46.0


def _lon(km: float) -> float:
    """Zemljepisna dolžina točke `km` vzhodno od postaje A na vzporedniku."""
    return 14.0 + km / (111.1949 * 0.6946584)


@pytest.fixture()
def conn():
    deljenje._predpomnilnik.clear()
    deljenje._trase.clear()
    deljenje._vzorci.clear()
    deljenje._kandidati_casi.clear()
    deljenje._deljenja_casi.clear()
    deljenje._zadnje_deljenje.clear()
    c = db.connect(":memory:")
    db.init(c)
    deljenje.init(c)
    danes = datetime.now(TZ).date().isoformat()
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)", [
        ("A", "Ajdovščina", LAT, 14.0), ("B", "Bled", LAT, 14.1), ("C", "Celje", LAT, 14.2)])
    c.execute("INSERT OR IGNORE INTO service_day(service_id, date) VALUES('S', ?)", (danes,))
    tocke = [[LAT, 14.0 + i * 0.01] for i in range(21)]
    c.execute("INSERT INTO shape(shape_id, points) VALUES('sh1', ?)", (json.dumps([tocke]),))
    c.execute("INSERT INTO shape(shape_id, points) VALUES('sh2', ?)",
              (json.dumps([tocke[::-1]]),))
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, shape_id) "
              "VALUES('t1', 'r1', 'LP 1', 'A - C', 'S', 'sh1')")
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, shape_id) "
              "VALUES('t2', 'r2', 'LP 2', 'C - A', 'S', 'sh2')")
    # 10:00 iz A, 10:10 v B (minuta postanka), 10:20 v C. t2 obratno.
    c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)", [
        ("t1", 1, "A", None, 36000), ("t1", 2, "B", 36600, 36660), ("t1", 3, "C", 37260, None),
        ("t2", 1, "C", None, 36000), ("t2", 2, "B", 36600, 36660), ("t2", 3, "A", 37260, None)])
    db.fill_trip_window(c)
    c.commit()
    return c


def _ob(ura: str) -> datetime:
    h, m = map(int, ura.split(":")[:2])
    s = int(ura.split(":")[2]) if ura.count(":") == 2 else 0
    return datetime.now(TZ).replace(hour=h, minute=m, second=s, microsecond=0)


def _tocka(km: float, zdaj: datetime, **kw) -> dict:
    return {"lat": LAT, "lon": _lon(km), "acc": 10, "t": zdaj.timestamp() * 1000, **kw}


def _deli(conn, zdaj, *tocke, ident=None, trip="t1", kljuc="k"):
    return deljenje.sprejmi(conn, {
        "trip_id": trip, "service_date": zdaj.date().isoformat(),
        "deljenje": ident, "tocke": list(tocke)}, kljuc, zdaj)


# ------------------------------------------------------------ kandidati

def test_kandidat_je_vlak_na_trasi_ob_pravem_casu(conn):
    zdaj = _ob("10:05")
    k = deljenje.kandidati(conn, LAT, _lon(3.8), 10, zdaj=zdaj)
    assert {x["trip_id"] for x in k} == {"t1", "t2"}   # brez smeri sta oba


def test_smer_izloci_vlak_v_nasprotni_smeri(conn):
    zdaj = _ob("10:05")
    k = deljenje.kandidati(conn, LAT, _lon(3.8), 10,
                           prej={"lat": LAT, "lon": _lon(3.5)}, zdaj=zdaj)
    assert [x["trip_id"] for x in k] == ["t1"]
    assert k[0]["smer_potrjena"] is True
    assert k[0]["med"] == ["Ajdovščina", "Bled"]


def test_dalec_od_trase_ni_kandidatov(conn):
    zdaj = _ob("10:05")
    assert deljenje.kandidati(conn, LAT + 0.05, _lon(3.8), 10, zdaj=zdaj) == []


def test_zamujen_vlak_je_se_kandidat(conn):
    """Vlak, ki ga feed kaže že daleč naprej, a še stoji -- prav ta primer."""
    zdaj = _ob("10:40")
    k = deljenje.kandidati(conn, LAT, _lon(7.7), 10, zdaj=zdaj)
    assert "t1" in [x["trip_id"] for x in k]
    assert k[0]["pri"] == "Bled"


def test_vlak_cez_uro_ni_kandidat(conn):
    zdaj = _ob("08:30")
    assert deljenje.kandidati(conn, LAT, _lon(3.8), 10, zdaj=zdaj) == []


# ------------------------------------------------------------ sprejem

def test_deljenje_zapise_prehod_in_zamudo(conn):
    zdaj = _ob("10:14")
    # Vlak še stoji v Bledu štiri minute po voznorednem odhodu (10:11).
    r = _deli(conn, zdaj, _tocka(7.72, zdaj - timedelta(seconds=20), v=0),
              _tocka(7.72, zdaj, v=0))
    assert r["konec"] is None and r["sprejetih"] == 2
    assert r["stanje"]["pri"] == "Bled"
    assert r["stanje"]["zamuda_s"] == 180
    # Odpelje in gre čez rob postaje: zapiše se odhod.
    z2 = zdaj + timedelta(seconds=60)
    r = _deli(conn, z2, _tocka(8.5, z2), ident=r["deljenje"])
    prehod = r["stanje"]["prehodi"][2]
    assert prehod["odhod"] is not None and prehod["n"] == 1
    ts = conn.execute("SELECT COUNT(*) FROM deljenje_tocka").fetchone()[0]
    assert ts == 3


def test_tocke_se_hranijo_brez_koordinat(conn):
    zdaj = _ob("10:05")
    _deli(conn, zdaj, _tocka(3.8, zdaj))
    stolpci = {r[1] for r in conn.execute("PRAGMA table_info(deljenje_tocka)")}
    assert "lat" not in stolpci and "lon" not in stolpci


def test_zacetek_dalec_od_trase_je_zavrnjen(conn):
    zdaj = _ob("10:05")
    with pytest.raises(deljenje.Zavrnjeno):
        _deli(conn, zdaj, {"lat": LAT + 0.05, "lon": _lon(3.8), "acc": 10})


def test_zacetek_ob_napacnem_casu_je_zavrnjen(conn):
    zdaj = _ob("08:00")
    with pytest.raises(deljenje.Zavrnjeno):
        _deli(conn, zdaj, _tocka(3.8, zdaj))


def test_tri_tocke_izven_trase_so_izstop(conn):
    zdaj = _ob("10:05")
    r = _deli(conn, zdaj, _tocka(3.8, zdaj))
    for i in range(1, 4):
        z = zdaj + timedelta(seconds=10 * i)
        r = _deli(conn, z, {"lat": LAT + 0.01, "lon": _lon(3.8), "acc": 10,
                            "t": z.timestamp() * 1000}, ident=r["deljenje"])
    assert r["konec"] == "izstop"


def test_nenatancna_tocka_ni_izstop(conn):
    """V predoru je natančnost slaba, potnik pa je še na vlaku."""
    zdaj = _ob("10:05")
    r = _deli(conn, zdaj, _tocka(3.8, zdaj))
    for i in range(1, 5):
        z = zdaj + timedelta(seconds=10 * i)
        r = _deli(conn, z, {"lat": LAT + 0.01, "lon": _lon(3.8), "acc": 900,
                            "t": z.timestamp() * 1000}, ident=r["deljenje"])
    assert r["konec"] is None


def test_skok_prehitro_se_zavrze(conn):
    zdaj = _ob("10:05")
    r = _deli(conn, zdaj, _tocka(3.8, zdaj))
    z = zdaj + timedelta(seconds=10)
    r = _deli(conn, z, _tocka(12.0, z), ident=r["deljenje"])   # 820 m/s
    assert r["sprejetih"] == 0


def test_tuje_deljenje_ni_mogoce_nadaljevati_na_drugi_voznji(conn):
    zdaj = _ob("10:05")
    r = _deli(conn, zdaj, _tocka(3.8, zdaj))
    with pytest.raises(deljenje.Zavrnjeno):
        _deli(conn, zdaj, _tocka(3.8, zdaj), ident=r["deljenje"], trip="t2")


def test_prihod_na_cilj_konca_deljenje(conn):
    zdaj = _ob("10:19")
    r = _deli(conn, zdaj, _tocka(14.0, zdaj))
    z = zdaj + timedelta(seconds=60)
    r = _deli(conn, z, _tocka(15.4, z, v=0), ident=r["deljenje"])
    assert r["konec"] == "cilj"


# ------------------------------------------------------------ soglasje

def test_en_porocevalec_ni_soglasje(conn):
    zdaj = _ob("10:14")
    _deli(conn, zdaj, _tocka(7.72, zdaj, v=0))
    st = deljenje.stanje(conn, ["t1"], zdaj)["t1"]
    assert st["n"] == 1 and st["soglasje"] is False


def test_dva_ujemajoca_se_sta_soglasje(conn):
    zdaj = _ob("10:14")
    _deli(conn, zdaj, _tocka(7.72, zdaj, v=0), kljuc="a")
    _deli(conn, zdaj, _tocka(7.80, zdaj, v=0), kljuc="b")
    st = deljenje.stanje(conn, ["t1"], zdaj)["t1"]
    assert st["n"] == 2 and st["soglasje"] is True


def test_dva_neujemajoca_se_nista_soglasje(conn):
    zdaj = _ob("10:14")
    _deli(conn, zdaj, _tocka(7.72, zdaj, v=0), kljuc="a")
    _deli(conn, zdaj, _tocka(2.0, zdaj), kljuc="b")   # ~10 min narazen
    st = deljenje.stanje(conn, ["t1"], zdaj)["t1"]
    assert st["n"] == 2 and st["soglasje"] is False


def test_isti_posiljatelj_znova_ni_drugi_porocevalec(conn):
    """Osvežena stran ali izgubljen odgovor začne novo deljenje; en telefon
    pa ne sme dati soglasja dveh in zamenjati feeda."""
    zdaj = _ob("10:14")
    prvo = _deli(conn, zdaj, _tocka(7.72, zdaj, v=0), kljuc="a")
    _deli(conn, zdaj, _tocka(7.74, zdaj, v=0), kljuc="a")
    st = deljenje.stanje(conn, ["t1"], zdaj)["t1"]
    assert st["n"] == 1 and st["soglasje"] is False
    konec = conn.execute("SELECT konec FROM deljenje WHERE id = ?",
                         (prvo["deljenje"],)).fetchone()[0]
    assert konec == "potnik"


def test_zavrnjen_zacetek_ne_porabi_omejitve(conn):
    """Slab GPS ob postaji da „ni na trasi" večkrat zapored; ključ si za
    CGNAT deli veliko ljudi, zato šteje le deljenje, ki se je začelo."""
    zdaj = _ob("10:05")
    for _ in range(deljenje.DELJENJ_NA_URO + 2):
        with pytest.raises(deljenje.Zavrnjeno):
            _deli(conn, zdaj, {"lat": LAT + 0.05, "lon": _lon(3.8), "acc": 10,
                               "t": zdaj.timestamp() * 1000})
    assert _deli(conn, zdaj, _tocka(3.8, zdaj))["deljenje"]


def _krozna(conn):
    """Krožna t3: A -> B po vzporedniku, nazaj 22 m severneje v A2 ob A."""
    tja = [[LAT, 14.0 + i * 0.01] for i in range(11)]
    nazaj = [[LAT + 0.0002, 14.1 - i * 0.01] for i in range(11)]
    conn.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES('A2', 'Ajdovščina', ?, 14.0)",
                 (LAT + 0.0002,))
    conn.execute("INSERT INTO shape(shape_id, points) VALUES('sh3', ?)",
                 (json.dumps([tja + nazaj]),))
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, shape_id) "
                 "VALUES('t3', 'r3', 'LPP 3', 'krog', 'S', 'sh3')")
    conn.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) "
                     "VALUES(?,?,?,?,?)", [("t3", 1, "A", None, 36000),
                                          ("t3", 2, "B", 37800, 37800),
                                          ("t3", 3, "A2", 39600, None)])
    db.fill_trip_window(conn)
    conn.commit()


def test_krozna_linija_na_izhodiscu_ni_na_cilju(conn):
    """Izhodišče in konec krožne linije sta ista točka. Projekcija brez meje
    je potnika pred odhodom postavila na cilj -- in deljenje zavrnila."""
    _krozna(conn)
    zdaj = _ob("09:58")
    tocka = {"lat": LAT + 0.0002, "lon": 14.0, "acc": 10, "t": zdaj.timestamp() * 1000}
    assert "t3" in {k["trip_id"] for k in deljenje.kandidati(
        conn, tocka["lat"], tocka["lon"], 10, zdaj=zdaj)}
    r = _deli(conn, zdaj, tocka, trip="t3")
    assert r["konec"] is None
    along = conn.execute("SELECT along_m FROM deljenje WHERE id = ?",
                         (r["deljenje"],)).fetchone()[0]
    assert along < 100


def test_prevelika_stevila_so_zavrnitev_ne_napaka(conn):
    zdaj = _ob("10:05")
    with pytest.raises(deljenje.Zavrnjeno):
        _deli(conn, zdaj, {"lat": 10 ** 400, "lon": _lon(3.8), "acc": 10})
    r = _deli(conn, zdaj, _tocka(3.8, zdaj, t=float("inf"), v=10 ** 400))
    assert r["deljenje"]


def test_samo_prava_vrsta_json_sprozi_cors():
    assert deljenje.je_json("application/json")
    assert deljenje.je_json("Application/JSON; charset=utf-8")
    # Za brskalnik je to text/plain in gre brez predpoizvedbe.
    assert not deljenje.je_json("text/plain;charset=application/json")
    assert not deljenje.je_json("")


def test_staro_porocilo_ne_pove_lege(conn):
    zdaj = _ob("10:05")
    _deli(conn, zdaj, _tocka(3.8, zdaj))
    pozneje = zdaj + timedelta(seconds=deljenje.SVEZE_S + 30)
    assert "t1" not in deljenje.stanje(conn, ["t1"], pozneje)


# ------------------------------------------------------------ tabla

def _vrstica_c(zdaj):
    """Vrstica table za postajo Celje (t1, postanek 3), kot jo vrne `board`."""
    return {"trip_id": "t1", "stop_seq": 3, "t_s": 37260, "delay_s": 0,
            "sched": zdaj.replace(hour=10, minute=21).isoformat(),
            "expected": zdaj.replace(hour=10, minute=21).isoformat(),
            "delay_kind": "zadnji podatek", "zamuda": None,
            "nepotrjen_do": zdaj.replace(hour=10, minute=41).isoformat()}


def test_en_porocevalec_tabli_doda_in_ne_zamenja(conn):
    zdaj = _ob("10:14")
    _deli(conn, zdaj, _tocka(7.72, zdaj, v=0))
    r = _vrstica_c(zdaj)
    pred = dict(r)
    deljenje.dopolni(conn, [r], seq="stop_seq", t_s="t_s", pricakovano="expected", ura="sched", zdaj=zdaj)
    assert r["potniki"]["soglasje"] is False
    assert r["potniki"]["zamuda_s"] == 180
    assert r["expected"] == pred["expected"] and r["nepotrjen_do"] == pred["nepotrjen_do"]


def test_soglasje_zamenja_feed_na_tabli(conn):
    zdaj = _ob("10:14")
    _deli(conn, zdaj, _tocka(7.72, zdaj, v=0), kljuc="a")
    _deli(conn, zdaj, _tocka(7.80, zdaj, v=0), kljuc="b")
    r = _vrstica_c(zdaj)
    deljenje.dopolni(conn, [r], seq="stop_seq", t_s="t_s", pricakovano="expected", ura="sched", zdaj=zdaj)
    assert r["potniki"]["soglasje"] is True
    assert r["nepotrjen_do"] is None
    assert r["delay_s"] == 180
    assert r["zamuda"]["vrsta"] == "po poročilu potnikov"
    assert datetime.fromisoformat(r["expected"]) == zdaj.replace(hour=10, minute=24)


def test_vcerajsnji_prehod_ne_velja_danes(conn):
    """Isti `trip_id` vozi vsak dan; včerajšnji odhod ni današnji."""
    zdaj = _ob("10:14")
    vceraj = (zdaj - timedelta(days=1)).date().isoformat()
    conn.execute("INSERT INTO deljenje_prehod(deljenje, trip_id, service_date, stop_seq, odhod_ts) "
                 "VALUES('x', 't1', ?, 3, ?)", (vceraj, int((zdaj - timedelta(days=1)).timestamp())))
    r = _vrstica_c(zdaj)
    deljenje.dopolni(conn, [r], seq="stop_seq", t_s="t_s", pricakovano="expected",
                     ura="sched", zdaj=zdaj)
    assert "potniki" not in r


# ------------------------------------------------------------ pregled za skrbnika

def test_pregled_pokaze_zivo_in_koncano_po_vozilih(conn):
    zdaj = _ob("10:14")
    r = _deli(conn, zdaj - timedelta(seconds=40), _tocka(6.0, zdaj - timedelta(seconds=40)),
              kljuc="a")
    _deli(conn, zdaj, _tocka(7.72, zdaj, v=0), ident=r["deljenje"], kljuc="a")
    koncan = _deli(conn, zdaj, _tocka(7.80, zdaj, v=0), kljuc="b")
    conn.execute("UPDATE deljenje SET konec = 'potnik' WHERE id = ?", (koncan["deljenje"],))
    p = deljenje.pregled(conn, zdaj)
    assert p["povzetek"]["deljenj"] == 2 and p["povzetek"]["vozil"] == 1
    assert p["povzetek"]["izidi"] == {"deli": 1, "potnik": 1}
    assert deljenje.deli_zdaj(conn, zdaj) == 1
    v = p["vozila"][0]
    assert v["train_no"] == "LP 1" and v["od"] == "Ajdovščina" and v["do"] == "Celje"
    # Javno stanje je isto kot na tabli: `stanje()` šteje sveža poročila
    # deljenj, ki še tečejo -- ustavljeno ne poroča več.
    assert v["zivo"] and v["javno"]["n"] == 1 and v["javno"]["pri"] == "Bled"
    assert len(v["trasa"]) == 1
    # Sled je del trase med prvo in zadnjo točko, na vzporedniku.
    sled = v["deljenja"][0]["sled"]
    assert len(sled) == 1
    assert sled[0][0][1] == pytest.approx(_lon(6.0), abs=1e-4)      # ~8 m
    assert sled[0][-1][1] == pytest.approx(_lon(7.72), abs=1e-4)
    assert all(t[0] == LAT for t in sled[0])


def test_pregled_koncanemu_ne_poslje_cele_trase(conn):
    zdaj = _ob("10:14")
    _deli(conn, zdaj, _tocka(7.72, zdaj, v=0))
    v = deljenje.pregled(conn, zdaj + timedelta(seconds=deljenje.SVEZE_S + 30))["vozila"][0]
    assert not v["zivo"] and v["trasa"] == [] and v["deljenja"][0]["izid"] == "utihnil"


def test_pregled_ne_kaze_vcerajsnjih(conn):
    zdaj = _ob("10:14")
    _deli(conn, zdaj, _tocka(7.72, zdaj, v=0))
    jutri = zdaj + timedelta(days=1)
    assert deljenje.pregled(conn, jutri)["vozila"] == []
    assert deljenje.deli_zdaj(conn, jutri) == 0


def test_odsek_trase_se_prelomi_na_vrzeli():
    t = deljenje.Trasa([[(LAT, 14.0), (LAT, 14.01)], [(LAT, 14.1), (LAT, 14.11)]])
    kosi = deljenje._kosi(t)
    assert len(kosi) == 2
    # Del, ki se začne v vrzeli, ne nariše ravne črte čeznjo.
    del_ = deljenje._kosi(t, t.cum[1] + 100, t.cum[3])
    assert len(del_) == 1 and del_[0][0] == [LAT, 14.1]


def test_potnik_na_zivih_ne_spremeni_predpomnjenih_vrstic(monkeypatch):
    """Žive vožnje so predpomnjene do 60 s, potnik pa pošilja na 10 s: potnik
    gre zraven ob vsakem branju, predpomnjena vrstica ostane brez njega."""
    from kajros import api
    vrstice = [{"trip_id": "t1", "network": "zeleznica", "service_date": "D"},
               {"trip_id": "t2", "network": "zeleznica", "service_date": "D"}]
    monkeypatch.setattr(api.deljenje, "stanje", lambda conn, ids, now: {
        "t1": {"service_date": "D", "lat": 46.0, "lon": 14.5, "n": 1}})
    out = api._s_potniki(None, vrstice, None)
    assert out[0]["potnik"]["lat"] == 46.0 and "potnik" not in out[1]
    assert all("potnik" not in r for r in vrstice)
