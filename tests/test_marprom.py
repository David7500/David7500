"""Mestni Marprom: vozni red z dveh naslovov, vozilo -> vožnja po prihodih,
lege in vozila brez vožnje, zdravje.

    ./venv/bin/python -m pytest tests/test_marprom.py -q
"""
from __future__ import annotations

import io
import json
import zipfile
from datetime import date, timedelta

import pytest

from kajros import collector, config, db, gtfs, iz_lege, marprom, prehod, stats, zdravje

DAN = "2026-10-27"                                   # torek
POLNOC = stats.polnoc(DAN)
ZDAJ = POLNOC + 10 * 3600 + 55 * 60                  # 10:55

STOPS = ("stop_id,stop_code,stop_name,stop_lat,stop_lon\n"
         "192,001,Avtobusna postaja,46.558713,15.655748\n"
         "91,091,Gosposvetska,46.567180,15.632200\n"
         "120,120,Kavčičeva,46.526876,15.672361\n")


def _mp_zip(koledar: str, voznje=(("101714", "10:50"), ("101715", "11:20"))) -> bytes:
    """Najmanjši Marpromov zip: linija P7 (proga 73, varianta 6970)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("agency.txt", "agency_id,agency_name,agency_url,agency_timezone\n"
                                  '3,"Marprom","https://marprom.si","Europe/Ljubljana"\n')
        zf.writestr("stops.txt", STOPS)
        zf.writestr("routes.txt", "route_id,agency_id,route_short_name,route_long_name,route_type\n"
                                  '73,3,"P7","Kamnica",3\n')
        zf.writestr("trips.txt", "route_id,service_id,trip_id,trip_headsign,shape_id\n"
                    + "".join(f"73,{(sv or ['8860'])[0]},{t},Avtobusna postaja - Kamnica,6970\n"
                              for t, _, *sv in voznje))
        vrstice = []
        for t, ura, *_ in voznje:
            h, m = map(int, ura.split(":"))
            for seq, (sid, plus) in enumerate((("192", 0), ("91", 6), ("120", 15)), 1):
                c = f"{h + (m + plus) // 60:02d}:{(m + plus) % 60:02d}:00"
                vrstice.append(f"{t},{c},{c},{sid},{seq}\n")
        zf.writestr("stop_times.txt",
                    "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
                    + "".join(vrstice))
        zf.writestr("calendar.txt", "service_id,monday,tuesday,wednesday,thursday,friday,"
                                    "saturday,sunday,start_date,end_date\n" + koledar)
        zf.writestr("calendar_dates.txt", "service_id,date,exception_type\n")
        # Gosto, kot v pravem zipu: razmik nad 1 km bi traso pretrgal.
        oglisca = ((46.558713, 15.655748), (46.567180, 15.632200), (46.526876, 15.672361))
        tocke = [(a[0] + (b[0] - a[0]) * i / 40, a[1] + (b[1] - a[1]) * i / 40)
                 for a, b in zip(oglisca, oglisca[1:]) for i in range(40)] + [oglisca[-1]]
        zf.writestr("shapes.txt", "shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence\n"
                    + "".join(f"6970,{la:.6f},{lo:.6f},{i}\n"
                              for i, (la, lo) in enumerate(tocke, 1)))
    return buf.getvalue()


SOLSKI = "8860,1,1,1,1,1,0,0,20260101,20271231\n"


def _ijpp_zip(pot):
    """IJPP z eno vožnjo in ljubljansko „Kavčičevo“ (LPP jo ima, 136 km)."""
    with zipfile.ZipFile(pot, "w") as zf:
        zf.writestr("routes.txt", "route_id,agency_id,route_short_name,route_type\n"
                                  "r1,1161,LP 2010,2\n")
        zf.writestr("trips.txt", "trip_id,route_id,service_id,shape_id,trip_headsign\n"
                                 "v1,r1,s1,,Ljubljana\n")
        zf.writestr("stop_times.txt",
                    "trip_id,stop_sequence,stop_id,arrival_time,departure_time\n"
                    "v1,1,A,08:00:00,08:00:00\nv1,2,K,08:30:00,08:30:00\n")
        zf.writestr("stops.txt", "stop_id,stop_name,stop_lat,stop_lon\n"
                                 "A,Kamnik,46.2,14.6\nK,Kavčičeva,46.0640,14.5440\n")
        zf.writestr("shapes.txt", "shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence\n")
        zf.writestr("calendar_dates.txt", "service_id,date,exception_type\ns1,20261027,1\n")
    return pot


@pytest.fixture(autouse=True)
def _cist_spomin():
    marprom._vozila.clear()
    marprom._primerjave.clear()
    marprom._po_voznem_redu[:] = [0.0, 0]
    collector._STATIC_CACHE.clear()
    iz_lege._v_feedu.clear()
    iz_lege._prvic = None
    prehod._sledi.clear()
    yield
    marprom._vozila.clear()


@pytest.fixture
def baza(tmp_path):
    c = db.connect(":memory:")
    db.init(c)
    mp = tmp_path / "marprom_gtfs.zip"
    mp.write_bytes(_mp_zip(SOLSKI))
    gtfs.import_static(c, _ijpp_zip(tmp_path / "ijpp.zip"), mestni={"marprom": mp})
    c.commit()
    return c


def test_uvoz_da_predpono_prevoznika_in_razlocno_ime(baza):
    """Id-ji Marproma so števila kot IJPP-jevi: brez predpone bi storitev
    8860 dala vožnji IJPP Marpromove dneve. Ime, ki je drugje daleč, dobi
    kraj -- aplikacija teče po imenu."""
    t = dict(baza.execute(
        "SELECT trip_id, route_id, service_id, shape_id, agency, network, mode, train_no "
        "FROM trip WHERE trip_id = 'mp-101714'").fetchone())
    assert t == {"trip_id": "mp-101714", "route_id": "mp-73", "service_id": "mp-8860",
                 "shape_id": "mp-6970", "agency": "marprom", "network": "avtobus",
                 "mode": "bus", "train_no": "P7"}
    imena = dict(baza.execute("SELECT stop_id, name FROM station").fetchall())
    assert imena["mp-120"] == "Kavčičeva (Maribor)"
    assert imena["K"] == "Kavčičeva"
    assert imena["mp-192"] == "Avtobusna postaja"
    assert baza.execute("SELECT COUNT(*) FROM service_day WHERE service_id = 'mp-8860' "
                        "AND date = ?", (DAN,)).fetchone()[0] == 1


def test_pokritost_zavrne_poletni_zip_in_vzame_solskega(tmp_path):
    """Uradni zip od 5. 10. 2026: sobote in nedelje so, med tednom nič."""
    poletni = tmp_path / "poletni.zip"
    poletni.write_bytes(_mp_zip("8860,1,1,1,1,1,0,0,20260707,20260831\n"
                                "8727,0,0,0,0,0,1,1,20260707,20261231\n"))
    pk = gtfs.pokritost(poletni, DAN)
    assert pk == [0, 0, 0, 0, 0, 0, 0]    # vožnje so le v storitvi 8860
    assert not gtfs.sprejmi(pk)
    solski = tmp_path / "solski.zip"
    solski.write_bytes(_mp_zip(SOLSKI))
    pk = gtfs.pokritost(solski, DAN)
    assert pk == [2, 2, 2, 2, 0, 0, 2] and not gtfs.sprejmi(pk)
    assert gtfs.sprejmi([2, 2, 2, 2, 2, 0, 2]), "en prazen dan sme biti"
    assert gtfs.sprejmi(pk, praznih=3), "Kranj ob nedeljah ne vozi"
    assert not gtfs.sprejmi([0] * 7, praznih=7), "prazen zip ni vozni red"


def test_rok_je_konec_prve_vrste_dne(tmp_path):
    """Kopija Marproma: `do` 20. 6. 2027, delavniki pa do 31. 12. 2026."""
    z = tmp_path / "kopija.zip"
    z.write_bytes(_mp_zip("8860,1,1,1,1,1,0,0,20260901,20261231\n"
                          "8727,0,0,0,0,0,1,1,20260901,20270620\n",
                          voznje=(("1", "10:50", "8860"), ("2", "10:50", "8727"))))
    assert gtfs._zadnji_dan(z) == "2027-06-20"
    assert gtfs.rok(z, DAN) == "2026-12-31"
    # Po roku ostane rok, dokler je blizu: to je ravno takrat, ko šteje ...
    assert gtfs.rok(z, "2027-01-04") == "2026-12-31"
    # ... mesec pozneje je to sezona, velja naslednja vrsta.
    assert gtfs.rok(z, "2027-03-01") == "2027-06-19"    # zadnja sobota


class _Odgovor:
    def __init__(self, vsebina: bytes, status: int = 200):
        self.vsebina, self.status_code, self.headers = vsebina, status, {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def iter_content(self, n):
        yield self.vsebina


def test_download_vzame_prvega_ki_pokrije_in_obdrzi_sprejetega(tmp_path, monkeypatch):
    """Uradni ne pokrije tedna -> kopija. Ko ne pokrije noben, ostane zadnji
    sprejeti na disku: uvoz brez njega bi Maribor izbrisal."""
    danes = date.today()
    od, do = ((danes - timedelta(days=30)).strftime("%Y%m%d"),
              (danes + timedelta(days=200)).strftime("%Y%m%d"))
    zastarel = (danes - timedelta(days=50)).strftime("%Y%m%d")
    dobri = _mp_zip(f"8860,1,1,1,1,1,1,1,{od},{do}\n")
    stari = _mp_zip(f"8860,1,1,1,1,1,1,1,{od},{zastarel}\n")
    odgovori = {"https://uradni/gtfs.zip": stari, "http://kopija/gtfs.zip": dobri}
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "MARPROM_GTFS_URLS", tuple(odgovori))
    monkeypatch.setattr(gtfs.requests, "get", lambda url, **kw: _Odgovor(odgovori[url]))
    c = db.connect(":memory:")
    db.init(c)
    vir = next(v for v in gtfs.mestni_viri() if v.kljuc == "marprom")

    pot = gtfs.download_mestni(c, vir)
    assert pot == tmp_path / "marprom_gtfs.zip" and pot.read_bytes() == dobri
    meta = json.loads(db.get_meta(c, "marprom_vozni_red"))
    assert [v["sprejet"] for v in meta["viri"]] == [False, True]
    assert meta["do"] == (danes + timedelta(days=200)).isoformat()
    assert gtfs.download_mestni(c, vir) is None, "nespremenjen"

    odgovori["http://kopija/gtfs.zip"] = stari
    assert gtfs.download_mestni(c, vir) is None
    assert gtfs.zadnji_mestni(vir).read_bytes() == dobri
    assert json.loads(db.get_meta(c, "marprom_vozni_red"))["do"] == meta["do"], \
        "velja zadnji sprejeti"
    assert not list(tmp_path.glob("*.tmp"))

    odgovori["https://uradni/gtfs.zip"] = dobri
    assert gtfs.download_mestni(c, vir, force=True) == pot
    assert [v["sprejet"] for v in json.loads(
        db.get_meta(c, "marprom_vozni_red"))["viri"]] == [True, False]


def test_razberi_loci_zive_in_izpusti_lege_izven_slovenije():
    vozila = marprom.razberi({"Vehicles": [
        {"DeviceId": 472, "BusCode": "184", "RouteId": 6970, "LineId": 73, "Lat": 46.567,
         "Lon": 15.632, "NextStopPointId": 91, "LKStopPointId": 192, "Predicted": 0,
         "DirectionDescription": "Avtobusna postaja  - Kamnica"},
        {"DeviceId": 529, "BusCode": "141", "RouteId": 7484, "LineId": 84, "Lat": 46.54,
         "Lon": 15.59, "NextStopPointId": 17, "Predicted": 1},
        {"DeviceId": 1, "BusCode": "1", "Lat": 0, "Lon": 0},
        {"BusCode": "brez naprave", "Lat": 46.5, "Lon": 15.6},
    ]})
    assert [(v["naprava"], v["zivo"]) for v in vozila] == [("472", True), ("529", False)]
    assert vozila[0]["smer_opis"] == "Avtobusna postaja - Kamnica"
    assert (vozila[0]["linija"], vozila[0]["varianta"], vozila[0]["naslednja"]) == ("73", "6970", "91")


def _v(naprava="472", bus="184", naslednja="91", zivo=True, lat=46.56718, lon=15.6322):
    return {"naprava": naprava, "bus": bus, "linija": "73", "varianta": "6970",
            "naslednja": naslednja, "lat": lat, "lon": lon, "zivo": zivo,
            "smer_opis": "Avtobusna postaja - Kamnica"}


def test_razresi_po_uri_naslednjega_postajalisca(baza):
    """Ura, ki jo Marprom za vozilo pričakuje na naslednjem postajališču, z
    linijo in varianto = natanko ena vožnja."""
    idx = marprom.indeks(baza, ZDAJ)
    prihodi = [{"LineId": 73, "BusCode": "184", "ArrivalTime": "10:56", "ETAMin": 1, "DelayMin": 2},
               {"LineId": 73, "BusCode": "184", "ArrivalTime": "11:26", "ETAMin": 31}]
    assert marprom.razresi(_v(), prihodi, idx, {})[:2] == (("mp-101714", DAN, 2), "")
    # Drugo vozilo že ima to vožnjo: ni na voljo.
    assert marprom.razresi(_v(), prihodi, idx, {("mp-101714", DAN): "999"})[1] == "zasedena"
    assert marprom.razresi(_v(bus="7"), prihodi, idx, {})[1] == "ni_prihoda"
    tuji = [{**prihodi[0], "ArrivalTime": "10:57"}]
    assert marprom.razresi(_v(), tuji, idx, {})[1] == "ni_v_voznem_redu"
    # Vozilo pred končno ima naslednje 457, vozni red konča na 192 (skupina 5480).
    pred_koncno = [{"LineId": 73, "BusCode": "184", "ArrivalTime": "10:50", "ETAMin": 0}]
    assert marprom.razresi(_v(naslednja="457"), pred_koncno, idx, {})[1] == "ni_v_voznem_redu"
    assert marprom.razresi(_v(naslednja="457"), pred_koncno, idx, {},
                           {"457": ["192"]})[0] == ("mp-101714", DAN, 1)


def test_potrebuje_ob_novi_voznji_in_ob_preverjanju(baza):
    postanki = marprom._postanki(baza)
    okna = {"mp-101714": (10 * 3600 + 50 * 60, 11 * 3600 + 5 * 60)}
    s = marprom.Vozilo()
    assert marprom.potrebuje(s, _v(), ZDAJ, postanki, okna)          # nova
    s = marprom.Vozilo("mp-101714", DAN, "73", "6970", seq=2, razreseno_ts=ZDAJ)
    assert not marprom.potrebuje(s, _v(naslednja="120"), ZDAJ + 60, postanki, okna)
    assert s.seq == 3
    # Nazaj na izhodišče: začela se je nova vožnja iste variante.
    assert marprom.potrebuje(s, _v(naslednja="192"), ZDAJ + 120, postanki, okna)
    # Pred končno: naslednjega (kot 457 na avtobusni postaji) vožnja nima, ima
    # pa drugega iz iste skupine -- ista vožnja, ne nova razrešitev vsako branje.
    s.seq = 2
    assert not marprom.potrebuje(s, _v(naslednja="777"), ZDAJ, postanki, okna, {"777": ["120"]})
    assert s.seq == 3
    s.seq = 2
    assert marprom.potrebuje(s, {**_v(), "varianta": "6971"}, ZDAJ, postanki, okna)
    assert marprom.potrebuje(s, _v(), ZDAJ + marprom.PREVERI_S, postanki, okna)
    assert marprom.potrebuje(s, _v(), POLNOC + okna["mp-101714"][1] + marprom.PO_KONCU_S + 1,
                             postanki, okna)


def test_korak_pripne_zapise_lego_in_vozila_brez_voznje(baza):
    """Pripeto vozilo gre v `vehicle_now`; vozilo brez vožnje v pregled za
    zemljevid z imenom naslednjega postajališča. Mrtva lega (`Predicted`)
    je stara od zadnjega premika."""
    prihodi = {"91": [{"LineId": 73, "BusCode": "184", "ArrivalTime": "10:56", "ETAMin": 1}],
               "120": []}
    klici = []

    def prihodi_za(p):
        klici.append(p)
        return prihodi[p]

    vozila = [_v(), _v(naprava="9", bus="5", naslednja="120", zivo=False)]
    st = marprom.korak(baza, vozila, ZDAJ, prihodi_za, {"120": {"ime": "Kavčičeva", "skupina": None}})
    assert (st["pripetih"], st["brez_voznje"], st["klicev"]) == (1, 1, 2)
    v = dict(baza.execute("SELECT trip_id, service_date, seen_ts, vehicle_id FROM vehicle_now").fetchone())
    assert v == {"trip_id": "mp-101714", "service_date": DAN, "seen_ts": int(ZDAJ),
                 "vehicle_id": "marprom-472"}
    brez = json.loads(db.get_meta(baza, "marprom_vozila_brez_voznje"))["vozila"]
    assert [(b["train_no"], b["naslednja"], b["seen_ts"]) for b in brez] == [
        ("P7", "Kavčičeva (Maribor)", int(ZDAJ))]

    # Naslednji obhod: pripeto vozilo ne vpraša znova, brez vožnje šele čez ZNOVA_S.
    klici.clear()
    vozila[1]["lat"] += 0          # lega mrtvega se ne premakne
    st = marprom.korak(baza, vozila, ZDAJ + 10, prihodi_za)
    assert klici == [] and st["pripetih"] == 1
    brez = json.loads(db.get_meta(baza, "marprom_vozila_brez_voznje"))["vozila"]
    assert brez[0]["seen_ts"] == int(ZDAJ), "mrtva lega ostane stara"


def test_korak_preklopi_in_ne_pusti_dvojnika_na_zemljevidu(baza):
    """Ko vozilo začne novo vožnjo, lega stare izgine -- sicer bi bil isti
    avtobus do konca svežine narisan dvakrat."""
    p1 = [{"LineId": 73, "BusCode": "184", "ArrivalTime": "10:56", "ETAMin": 1}]
    marprom.korak(baza, [_v()], ZDAJ, lambda p: p1)
    p2 = [{"LineId": 73, "BusCode": "184", "ArrivalTime": "11:20", "ETAMin": 2}]
    st = marprom.korak(baza, [_v(naslednja="192")], ZDAJ + 20 * 60, lambda p: p2)
    assert st["preklopov"] == 1
    assert [r[0] for r in baza.execute("SELECT trip_id FROM vehicle_now")] == ["mp-101715"]


def test_zdravje_marprom():
    vozi = {"zeleznica": 5, "avtobus": 50}

    def ocena(mm, mv=None):
        z = {"vozi_zdaj": vozi, "marprom": mm,
             "mestni_vozni_red": {"marprom": mv} if mv else {}}
        return zdravje.ocena(z, {}, ZDAJ)

    assert "marprom" not in ocena(None)
    dobro = {"ts": ZDAJ - 5, "vozil": 30, "brez_voznje": 1, "po_voznem_redu": 25}
    assert ocena(dobro)["marprom"][0] == zdravje.DOBRA
    assert ocena({**dobro, "brez_voznje": 12})["marprom"][0] == zdravje.MLACNA
    assert ocena({**dobro, "vozil": 0, "brez_voznje": 0})["marprom"][0] == zdravje.MLACNA
    assert ocena({**dobro, "vozil": 0, "brez_voznje": 0, "po_voznem_redu": 0})["marprom"] == ("", "")
    assert ocena({"ts": ZDAJ - 1000, "napaka_ts": ZDAJ - 20})["marprom"][0] == zdravje.MLACNA
    assert ocena({"ts": ZDAJ - 1000, "napaka_ts": ZDAJ - 1000})["marprom"][0] == zdravje.SLABA

    # Uradni zip ne pokrije tedna: rumeno, potnik ne izgubi nič.
    do = (date.fromtimestamp(ZDAJ) + timedelta(days=200)).isoformat()
    mv = {"viri": [{"url": "u", "pokrito": [0, 0, 0, 0, 3, 3, 0], "sprejet": False},
                   {"url": "k", "pokrito": [9] * 7, "sprejet": True}], "do": do}
    raz, razlog = ocena(dobro, mv)["vozni_red_marprom"]
    assert raz == zdravje.MLACNA and "5 od 7 dni" in razlog and "kopija" in razlog
    assert ocena(dobro, {"viri": [{**mv["viri"][0], "sprejet": True}], "do": do})[
        "vozni_red_marprom"][0] == zdravje.DOBRA
    # Vozni red, ki ga uvoz res vzame, se izteče: rdeče dva dni prej.
    kmalu = (date.fromtimestamp(ZDAJ) + timedelta(days=1)).isoformat()
    assert ocena(dobro, {**mv, "do": kmalu})["vozni_red_marprom"][0] == zdravje.SLABA
    # Delavniki se končajo prej kot sobote: rok šteje, ne `do`.
    assert ocena(dobro, {**mv, "rok": kmalu})["vozni_red_marprom"][0] == zdravje.SLABA
    cez_mesec = (date.fromtimestamp(ZDAJ) + timedelta(days=30)).isoformat()
    raz, razlog = ocena(dobro, {**mv, "rok": cez_mesec})["vozni_red_marprom"]
    assert raz == zdravje.MLACNA and "del voznih redov se konča" in razlog


def test_zdravje_opazovano():
    danes = date.fromtimestamp(ZDAJ)
    ocena = lambda dan: zdravje.ocena({"vozi_zdaj": {}, "opazovano_dan": dan}, {}, ZDAJ).get("opazovano")
    assert ocena(None) is None
    assert ocena((danes - timedelta(days=2)).isoformat())[0] == zdravje.DOBRA
    raz, razlog = ocena((danes - timedelta(days=4)).isoformat())
    assert raz == zdravje.MLACNA and "4 dni" in razlog


def test_manjkajoci_vir_osvezi_ob_zagonu(monkeypatch):
    """Nov vir brez voženj v bazi: osvežitev ob zagonu, ne šele ob 4.20."""
    from kajros import server
    c = db.connect(":memory:")
    db.init(c)
    monkeypatch.setattr(config, "LPP_ENABLED", True)
    monkeypatch.setattr(config, "MARPROM", True)
    monkeypatch.setattr(config, "KRANJ", False)
    monkeypatch.setattr(config, "MS", True)
    assert server.manjkajoci_viri(c) == ["lpp", "marprom", "ms"]
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, agency, network) "
              "VALUES('mp-1', 'mp-73', 'P7', 'mp-8860', 'bus', 'marprom', 'avtobus')")
    assert server.manjkajoci_viri(c) == ["lpp", "ms"]
    monkeypatch.setattr(config, "LPP_ENABLED", False)
    monkeypatch.setattr(config, "MS", False)
    assert server.manjkajoci_viri(c) == []


def test_brez_voznega_reda_ne_bere_prihodov():
    """Pred prvim uvozom je vsako branje prihodov zaman: vozila gredo na
    zemljevid brez vožnje, Marpromov strežnik ne dobi zahtev."""
    c = db.connect(":memory:")
    db.init(c)
    klici = []
    st = marprom.korak(c, [_v()], ZDAJ, lambda p: klici.append(p) or [])
    assert klici == [] and st["brez"] == {"ni_voznega_reda": 1} and st["brez_voznje"] == 1
