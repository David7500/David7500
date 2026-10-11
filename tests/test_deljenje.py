"""Deljenje lege potnikov: kandidati, varovalke, prehodi in verodostojnost.

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
    # Pol kilometra pred Bledom sta po voznem redu oba: t1 je tu ob 10:09:27,
    # t2 ob 10:11:33 (ob 10:05 pri Ajdovščini bi t2 prehiteval 11 min).
    zdaj = _ob("10:10")
    k = deljenje.kandidati(conn, LAT, _lon(7.3), 10, zdaj=zdaj)
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
    assert r["stanje"]["hitrost_ms"] == 0
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


def _stoji_v_bledu(conn, zdaj):
    """Vlak stoji v Bledu; vrne odgovor na drugo točko."""
    _deli(conn, zdaj - timedelta(seconds=20), _tocka(7.72, zdaj - timedelta(seconds=20), v=0))
    ident = conn.execute("SELECT id FROM deljenje").fetchone()[0]
    return _deli(conn, zdaj, _tocka(7.72, zdaj, v=0), ident=ident)


def _vstran(km: float, metrov: float, zdaj: datetime, acc: float = 10) -> dict:
    return {"lat": LAT + metrov / 111195, "lon": _lon(km), "acc": acc,
            "t": zdaj.timestamp() * 1000, "v": 0}


def test_potnik_odide_s_postaje_je_izstop(conn):
    """Izstopil je in čaka ob progi: 100 m vstran je še pod mejo izven trase,
    a vlak, ki stoji, se vstran ne premika."""
    zdaj = _ob("10:14")
    r = _stoji_v_bledu(conn, zdaj)
    for i in range(1, 4):
        z = zdaj + timedelta(seconds=10 * i)
        r = _deli(conn, z, _vstran(7.72, 100, z), ident=r["deljenje"])
    assert r["konec"] == "izstop" and r["sprejetih"] == 0


def test_premik_vstran_v_meji_natancnosti_ni_izstop(conn):
    zdaj = _ob("10:14")
    r = _stoji_v_bledu(conn, zdaj)
    for i in range(1, 4):
        z = zdaj + timedelta(seconds=10 * i)
        r = _deli(conn, z, _vstran(7.72, 30, z), ident=r["deljenje"])
    assert r["konec"] is None and r["sprejetih"] == 1


def test_nenatancen_skok_vstran_med_stanjem_ni_izstop(conn):
    """Točka ±200 m je na vlaku, ki je stal, skočila 150 m vstran (LPV 2010)."""
    zdaj = _ob("10:14")
    r = _stoji_v_bledu(conn, zdaj)
    for i in range(1, 4):
        z = zdaj + timedelta(seconds=10 * i)
        r = _deli(conn, z, _vstran(7.72, 150, z, acc=200), ident=r["deljenje"])
    assert r["konec"] is None


def test_hoja_cez_rob_postaje_ni_odhod(conn):
    """Potnik je izstopil in hodi po peronu vzdolž proge (RG 318, Ljubljana):
    rob postaje prečka peš, vlak pa ni odpeljal."""
    zdaj = _ob("10:14")
    r = _stoji_v_bledu(conn, zdaj)
    for i in range(1, 16):
        z = zdaj + timedelta(seconds=10 * i)
        r = _deli(conn, z, _tocka(7.72 + 0.018 * i, z, v=1.5), ident=r["deljenje"])
    assert r["sprejetih"] == 1
    assert 2 not in r["stanje"]["prehodi"]


# ------------------------------------------------------------ verodostojnost

def test_en_porocevalec_ki_stoji_ni_verodostojen(conn):
    """Kdor se ni peljal, je lahko izstopil in čaka na peronu."""
    zdaj = _ob("10:14")
    _deli(conn, zdaj, _tocka(7.72, zdaj, v=0))
    st = deljenje.stanje(conn, ["t1"], zdaj)["t1"]
    assert st["n"] == 1 and st["verodostojno"] is False


def test_dva_ujemajoca_se_sta_verodostojna(conn):
    zdaj = _ob("10:14")
    _deli(conn, zdaj, _tocka(7.72, zdaj, v=0), kljuc="a")
    _deli(conn, zdaj, _tocka(7.80, zdaj, v=0), kljuc="b")
    st = deljenje.stanje(conn, ["t1"], zdaj)["t1"]
    assert st["n"] == 2 and st["verodostojno"] is True


def test_dva_neujemajoca_se_nista_verodostojna(conn):
    zdaj = _ob("10:14")
    _deli(conn, zdaj, _tocka(7.72, zdaj, v=0), kljuc="a")
    _deli(conn, zdaj, _tocka(2.0, zdaj), kljuc="b")   # ~10 min narazen
    st = deljenje.stanje(conn, ["t1"], zdaj)["t1"]
    assert st["n"] == 2 and st["verodostojno"] is False


def test_isti_posiljatelj_znova_ni_drugi_porocevalec(conn):
    """Osvežena stran ali izgubljen odgovor začne novo deljenje; en telefon
    pa ne sme dati dveh, ki se ujemata, in zamenjati feeda."""
    zdaj = _ob("10:14")
    prvo = _deli(conn, zdaj, _tocka(7.72, zdaj, v=0), kljuc="a")
    _deli(conn, zdaj, _tocka(7.74, zdaj, v=0), kljuc="a")
    st = deljenje.stanje(conn, ["t1"], zdaj)["t1"]
    assert st["n"] == 1 and st["verodostojno"] is False
    konec = conn.execute("SELECT konec FROM deljenje WHERE id = ?",
                         (prvo["deljenje"],)).fetchone()[0]
    assert konec == "znova"


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
    assert r["potniki"]["verodostojno"] is False
    assert r["potniki"]["zamuda_s"] == 180
    assert r["expected"] == pred["expected"] and r["nepotrjen_do"] == pred["nepotrjen_do"]


def test_dva_ki_se_ujemata_zamenjata_feed_na_tabli(conn):
    zdaj = _ob("10:14")
    _deli(conn, zdaj, _tocka(7.72, zdaj, v=0), kljuc="a")
    _deli(conn, zdaj, _tocka(7.80, zdaj, v=0), kljuc="b")
    r = _vrstica_c(zdaj)
    deljenje.dopolni(conn, [r], seq="stop_seq", t_s="t_s", pricakovano="expected", ura="sched", zdaj=zdaj)
    assert r["potniki"]["verodostojno"] is True
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
    """Žive vožnje so predpomnjene do 60 s, potnik pa pošilja na 5 s: potnik
    gre zraven ob vsakem branju, predpomnjena vrstica ostane brez njega."""
    from kajros import api
    vrstice = [{"trip_id": "t1", "network": "zeleznica", "service_date": "D"},
               {"trip_id": "t2", "network": "zeleznica", "service_date": "D"}]
    monkeypatch.setattr(api.deljenje, "stanje", lambda conn, ids, now: {
        "t1": {"service_date": "D", "lat": 46.0, "lon": 14.5, "n": 1}})
    monkeypatch.setattr(api.deljenje, "voznja", lambda conn, trip_id: None)
    out = api._s_potniki(None, vrstice, None)
    assert out[0]["potnik"]["lat"] == 46.0 and "potnik" not in out[1]
    assert all("potnik" not in r for r in vrstice)


# ------------------------------------------------- vlak na postaji (3D)

def test_smer_trase_gleda_naprej_po_voznji():
    t = deljenje.Trasa([[(LAT, 14.0), (LAT, 14.01), (LAT, 14.02)]])
    assert t.smer(t.dolzina / 2, 40) == pytest.approx(90, abs=0.5)
    # Na koncu se tetiva skrajša, smer ostane.
    assert t.smer(t.dolzina, 40) == pytest.approx(90, abs=0.5)
    obratna = deljenje.Trasa([[(LAT, 14.02), (LAT, 14.0)]])
    assert obratna.smer(0, 40) == pytest.approx(270, abs=0.5)


def _vrstica(seq, zamuda=0, trip="t1"):
    return {"trip_id": trip, "stop_seq": seq, "delay_s": zamuda}


def test_vlak_med_postankom_stoji_na_naslednji_postaji(conn):
    """`_LIVE_SQL` šteje Bled za prevožen šele ob odhodu (10:11); med
    postankom je zadnja prevožena postaja še Ajdovščina."""
    from kajros import api
    p = api._na_postaji(conn, _vrstica(1), 36630)
    assert p["ime"] == "Bled" and not p["koncna"]
    assert p["smer"] == pytest.approx(90, abs=1)
    assert p["lon"] == pytest.approx(14.1, abs=1e-4)
    # t2 vozi po isti progi nazaj: isti postanek, nasprotna smer.
    assert api._na_postaji(conn, _vrstica(1, trip="t2"), 36630)["smer"] == \
        pytest.approx(270, abs=1)


def test_vlak_med_postajama_ne_stoji(conn):
    from kajros import api
    assert api._na_postaji(conn, _vrstica(1), 36300) is None


def test_postanek_se_zamakne_za_zamudo(conn):
    from kajros import api
    # Dve minuti zamude: ob 10:10:30 še ni prispel, ob 10:12:30 stoji.
    assert api._na_postaji(conn, _vrstica(1, 120), 36630) is None
    assert api._na_postaji(conn, _vrstica(1, 120), 36750)["ime"] == "Bled"


def test_vlak_na_koncni_stoji(conn):
    from kajros import api
    p = api._na_postaji(conn, _vrstica(3), 37300)
    assert p["ime"] == "Celje" and p["koncna"]
    assert p["smer"] == pytest.approx(90, abs=1)


def test_vozilo_po_potnikih_samo_ob_soglasju(conn):
    """Mali zemljevid v oknu vožnje: en potnik je lahko že izstopil in čaka
    na peronu, zato lega šele od dveh, ki se ujemata."""
    from kajros import api
    zdaj = _ob("10:14")
    _deli(conn, zdaj, _tocka(7.72, zdaj, v=0), kljuc="a")
    assert api._vozilo_po_potnikih(conn, "t1", zdaj) is None
    _deli(conn, zdaj, _tocka(7.80, zdaj, v=0), kljuc="b")
    v = api._vozilo_po_potnikih(conn, "t1", zdaj)
    assert v["vir"] == "potniki" and v["potnikov"] == 2
    assert v["train_no"] == "LP 1" and v["speed_ms"] == 0 and v["age_s"] == 0
    assert v["lat"] == pytest.approx(LAT, abs=1e-4)


# ------------------------------------------------------------ en verodostojen potnik

def _pelje(conn, zacetek: datetime, km0: float, korak_km: float, n: int, kljuc="k", **kw):
    """Potnik se pelje: `n` točk na 10 s, vsaka `korak_km` naprej."""
    r = None
    for i in range(n):
        z = zacetek + timedelta(seconds=10 * i)
        r = _deli(conn, z, _tocka(km0 + korak_km * i, z, **kw),
                  ident=r["deljenje"] if r else None, kljuc=kljuc)
    return r


def test_en_potnik_ki_se_pelje_je_verodostojen(conn):
    """Od 11. 10. 2026 dovolj en: kdor se je peljal, ni na peronu."""
    zdaj = _ob("10:05")
    _pelje(conn, zdaj, 3.0, 0.1, 3)            # 100 m na 10 s
    st = deljenje.stanje(conn, ["t1"], zdaj + timedelta(seconds=20))["t1"]
    assert st["n"] == 1 and st["verodostojno"] is True
    r = _vrstica_c(zdaj)
    deljenje.dopolni(conn, [r], seq="stop_seq", t_s="t_s", pricakovano="expected",
                     ura="sched", zdaj=zdaj + timedelta(seconds=20))
    assert r["zamuda"]["vrsta"] == "po poročilu potnikov" and r["nepotrjen_do"] is None
    assert r["delay_s"] == st["zamuda_s"] > 0


def test_tresenje_lege_ni_voznja(conn):
    """Lega, ki stoji, v 30 s ne naredi 100 m naprej, tudi če skače."""
    zdaj = _ob("10:14")
    _pelje(conn, zdaj, 7.72, 0.008, 4, v=0)    # 8 m na 10 s
    assert deljenje.stanje(conn, ["t1"], zdaj + timedelta(seconds=30))["t1"]["verodostojno"] is False


def test_vlak_ki_prehiteva_ni_verodostojen(conn):
    """Vlak prezgodaj ne vozi: tak potnik je izbral napačno vožnjo."""
    zdaj = _ob("10:03")
    _pelje(conn, zdaj, 6.0, 0.1, 3)            # po voznem redu tu ob 10:08
    st = deljenje.stanje(conn, ["t1"], zdaj + timedelta(seconds=20))["t1"]
    assert st["verodostojno"] is False
    assert st["zamuda_s"] == 0                 # vlaku se „prej“ ne napiše


def test_prehod_steje_samo_od_potnika_ki_se_je_peljal(conn):
    zdaj = _ob("10:14")
    r = _stoji_v_bledu(conn, zdaj)
    conn.execute("INSERT INTO deljenje_prehod(deljenje, trip_id, service_date, stop_seq, odhod_ts) "
                 "VALUES(?, 't1', ?, 2, ?)", (r["deljenje"], zdaj.date().isoformat(),
                                             int(zdaj.timestamp())))
    assert deljenje.stanje(conn, ["t1"], zdaj)["t1"]["prehodi"] == {}
    conn.execute("UPDATE deljenje SET peljal_ts = 1")
    assert 2 in deljenje.stanje(conn, ["t1"], zdaj)["t1"]["prehodi"]


# ------------------------------------------------------------ čakanje na odhod

def _bus(conn):
    conn.execute("UPDATE trip SET mode = 'bus', network = 'avtobus' WHERE trip_id = 't1'")
    deljenje._predpomnilnik.clear()


def test_cakanje_na_izhodiscu_ni_prezgodaj(conn):
    """A5161 je 5. 10. 2026 sedem minut pred odhodom čakal v Kamniku, kartica
    je pisala „6 min prej“, tabla naprej prihod pred voznim redom."""
    _bus(conn)
    zdaj = _ob("09:53")
    r = _deli(conn, zdaj, _tocka(0.02, zdaj, v=0))
    assert r["stanje"]["zamuda_s"] == 0


def test_avtobus_ki_gre_skozi_prezgodaj_je_prezgoden(conn):
    _bus(conn)
    v = deljenje.voznja(conn, "t1")
    assert v.zamuda(7.72 * 1000, 36480, stoji=False) == -120   # B ob 10:08, prihod 10:10
    assert v.zamuda(7.72 * 1000, 36480, stoji=True) == 0


def test_vlak_ob_prihodu_prej_caka(conn):
    v = deljenje.voznja(conn, "t1")
    assert v.zamuda(7.72 * 1000, 36480) == 0


def test_hitrost_avtobusa_iz_telefona_ima_mejo(conn):
    """Brskalnik je na avtobusu javil 186 km/h; okno vožnje z njo pomika vozilo."""
    _bus(conn)
    zdaj = _ob("10:05")
    r = _pelje(conn, zdaj, 3.0, 0.1, 2, v=52)
    assert r["stanje"]["hitrost_ms"] == pytest.approx(10, abs=0.5)


# ------------------------------------------------------------ kandidati: ura

def test_kandidat_pove_odhod_in_zamudo(conn):
    zdaj = _ob("10:40")
    k = next(x for x in deljenje.kandidati(conn, LAT, _lon(7.7), 10, zdaj=zdaj)
             if x["trip_id"] == "t1")
    assert k["odhod"]["postaja"] == "Ajdovščina"
    assert datetime.fromisoformat(k["odhod"]["ura"]).strftime("%H:%M") == "10:00"
    assert k["zamuda_s"] == 29 * 60                 # stoji v Bledu od 10:11


def test_vlak_ki_bi_med_postajama_prehiteval_ni_kandidat(conn):
    """Lokalni posnetek 11. 10. 2026: med Pragerskim in Celjem sta bila
    kandidata še vlaka, ki bi bila tam 4 in 11 min pred voznim redom."""
    zdaj = _ob("10:03")
    assert "t1" not in {x["trip_id"] for x in deljenje.kandidati(conn, LAT, _lon(6.0), 10, zdaj=zdaj)}


def test_na_postaji_lahko_caka_vlak_ki_sele_pride(conn):
    zdaj = _ob("10:02")
    k = {x["trip_id"]: x for x in deljenje.kandidati(conn, LAT, _lon(7.72), 10, zdaj=zdaj)}
    assert "t1" in k and k["t1"]["zamuda_s"] == 0


# ------------------------------------------------------------ lijak

def test_lijak_steje_zacetke_po_odjemalcu(conn):
    zdaj = _ob("10:05")
    deljenje.sprejmi(conn, {"trip_id": "t1", "service_date": zdaj.date().isoformat(),
                            "tocke": [_tocka(3.8, zdaj)], "vir": "okno"}, "k", zdaj,
                     odjemalec="android")
    deljenje.stej(conn, "kandidati:0", zdaj)
    deljenje.stej(conn, "kandidati:0", zdaj)
    dan = deljenje.lijak(conn, zdaj)[0]
    assert dan["dogodki"] == {"zacetek:android": 1, "kandidati:0": 2}
    assert conn.execute("SELECT odjemalec, vir FROM deljenje").fetchone()[:] == ("android", "okno")


def test_vir_zunaj_seznama_se_ne_shrani(conn):
    zdaj = _ob("10:05")
    _deli(conn, zdaj, {**_tocka(3.8, zdaj)})
    deljenje.sprejmi(conn, {"trip_id": "t1", "service_date": zdaj.date().isoformat(),
                            "tocke": [_tocka(3.9, zdaj)], "vir": "<script>"}, "drug", zdaj)
    assert {r[0] for r in conn.execute("SELECT vir FROM deljenje")} == {None}


def test_odjemalec_iz_ua():
    assert deljenje.odjemalec("Kajros/1.10 (Android)") == "android"
    assert deljenje.odjemalec("Mozilla/5.0 (Linux; Android 15) Chrome/130 Kajros/1.10") == "aplikacija"
    assert deljenje.odjemalec("Mozilla/5.0 (Linux; Android 15) Chrome/130") == "splet"


def test_stara_tabela_dobi_nove_stolpce():
    c = db.connect(":memory:")
    c.execute("CREATE TABLE deljenje (id TEXT PRIMARY KEY, trip_id TEXT, service_date TEXT, "
              "network TEXT, zacetek_ts INTEGER, zadnja_ts INTEGER, konec TEXT)")
    deljenje.init(c)
    stolpci = {r[1] for r in c.execute("PRAGMA table_info(deljenje)")}
    assert {"peljal_ts", "odjemalec", "vir"} <= stolpci


# ------------------------------------------------------------ zemljevid: novejša lega

def _gps(age, cesta=True, trip="b1", network="avtobus"):
    d = {"trip_id": trip, "network": network, "lat": 46.0, "lon": 14.0, "bearing": 90,
         "speed_ms": 8, "speed_kmh": 29, "age_s": age, "seen_ts": 1000 - age,
         "delay_s": 60, "vehicle_id": "v1"}
    if cesta:
        d["cesta"] = {"lat": 46.0, "lon": 14.0}
    return d


def _potnik(age, network="avtobus"):
    return {"network": network, "lat": 46.1, "lon": 14.1, "bearing": 80, "speed_ms": 9,
            "speed_kmh": 32, "age_s": age, "delay_s": 120, "vir": "potniki", "potnikov": 1,
            "trip_id": "b1"}


def _na_legah(monkeypatch, out, potnik, trip=None):
    from kajros import api
    monkeypatch.setattr(api.deljenje, "zive_voznje", lambda conn, zdaj: ["b1"])
    monkeypatch.setattr(api.deljenje, "stanje", lambda conn, ids, zdaj: {"b1": {}})
    monkeypatch.setattr(api, "_vozilo_po_potnikih", lambda conn, t, zdaj, st=None: potnik)
    return api._s_potniki_na_legah(None, out, datetime.fromtimestamp(1000, TZ), trip)


def test_novejsi_potnik_zamenja_gps(monkeypatch):
    out, potniki = _na_legah(monkeypatch, [_gps(85)], _potnik(5))
    assert potniki and out[0]["vir"] == "potniki" and out[0]["lat"] == 46.1
    assert "cesta" not in out[0] and out[0]["vehicle_id"] == "v1" and out[0]["seen_ts"] == 995


def test_starejsi_potnik_ne_premakne_gps(monkeypatch):
    out, potniki = _na_legah(monkeypatch, [_gps(3)], _potnik(5))
    assert not potniki and "vir" not in out[0] and out[0]["lat"] == 46.0


def test_vozilo_brez_gps_dobi_potnika(monkeypatch):
    out, potniki = _na_legah(monkeypatch, [], _potnik(5))
    assert potniki and out[0]["vir"] == "potniki"


def test_vlak_gre_na_veliki_zemljevid_po_drugi_poti(monkeypatch):
    """Vlake in nadomestne riše veliki zemljevid iz `/api/live`; v legah jih ni."""
    out, potniki = _na_legah(monkeypatch, [], _potnik(5, "zeleznica"))
    assert out == [] and not potniki
    out, potniki = _na_legah(monkeypatch, [], _potnik(5, "zeleznica"), trip="b1")
    assert potniki and len(out) == 1
