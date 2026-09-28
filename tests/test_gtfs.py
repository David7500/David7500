"""Uvoz voznega reda: kar se da preveriti brez zipa in brez omrežja.

Večino uvoza preverja `scripts/preveri_skladnost.py` na pravi bazi; tu so
čiste funkcije, ki se pokvarijo tiho.

    ./venv/bin/python -m pytest tests/test_gtfs.py -q
"""
from __future__ import annotations

from kajros import gtfs
from kajros.gtfs import _lpp_oznaka


def test_lpp_oznaka_odstrani_vodilno_niclo():
    """LPP v svojem GTFS piše enomestne linije z vodilno ničlo, dvomestnih ne.

    Na postajališču piše „1", ne „01", in iskati se mora dati po tem, kar
    človek vidi. Črke in nočne oznake ostanejo nedotaknjene.
    """
    assert _lpp_oznaka("01") == "1"
    assert _lpp_oznaka("01B") == "1B"
    assert _lpp_oznaka("09") == "9"
    assert _lpp_oznaka("18") == "18"
    assert _lpp_oznaka("20Z") == "20Z"
    assert _lpp_oznaka("N3") == "N3"
    assert _lpp_oznaka("SŽ") == "SŽ"
    # Sama ničla ni linija, a ne sme postati prazen niz.
    assert _lpp_oznaka("0") == "0"


def test_poenoti_imena_zdruzi_le_isto_mesto():
    """„ČRNUČE" in „Črnuče" sta ista postaja; „Celje" in „Čelje" nista.

    Meja je izmerjena (glej `ISTO_POSTAJALISCE_M`): med 24 pari, ki se
    razlikujeta le po velikosti črk ali šumniku, jih je 14 od 3 do 215 m
    narazen, ostalih 10 pa od 0,8 do 111,6 km. Vmes ni ničesar.
    """
    stops = {
        # ista postaja, dva zapisa -- 116 m narazen
        "a1": {"stop_id": "a1", "name": "ČRNUČE", "lat": 46.1080, "lon": 14.5290},
        "a2": {"stop_id": "a2", "name": "Črnuče", "lat": 46.1090, "lon": 14.5295},
        # različna kraja z istim imenom -- 112 km
        "b1": {"stop_id": "b1", "name": "Celje", "lat": 46.2300, "lon": 15.2600},
        "b2": {"stop_id": "b2", "name": "Čelje", "lat": 45.7500, "lon": 13.7300},
        # samo eno ime -- nedotaknjeno
        "c1": {"stop_id": "c1", "name": "AMZS", "lat": 46.0600, "lon": 14.5100},
    }
    n = gtfs._poenoti_imena(stops)
    assert n == 1
    assert stops["a1"]["name"] == "Črnuče"      # velike črke se umaknejo
    assert stops["a2"]["name"] == "Črnuče"
    assert stops["b1"]["name"] == "Celje"       # 112 km -- ne zliva se
    assert stops["b2"]["name"] == "Čelje"
    assert stops["c1"]["name"] == "AMZS"        # brez para ostane, kot je


def _zip(pot, trips, trasa=None):
    """Najmanjši IJPP zip: ena proga SŽ in vožnje, ki jih dobi.

    `trasa` = (lat, lon) začetka trase, ki jo dobijo vse vožnje; brez nje
    vožnje trase nimajo.
    """
    import zipfile
    sid = "sh1" if trasa else ""
    with zipfile.ZipFile(pot, "w") as zf:
        zf.writestr("routes.txt", "route_id,agency_id,route_short_name,route_type\n"
                                  "r1,1161,LP 2010,2\n")
        zf.writestr("trips.txt", "trip_id,route_id,service_id,shape_id,trip_headsign\n"
                    + "".join(f"{t},r1,s1,{sid},Ljubljana\n" for t in trips))
        zf.writestr("stop_times.txt",
                    "trip_id,stop_sequence,stop_id,arrival_time,departure_time\n"
                    + "".join(f"{t},1,A,08:00:00,08:00:00\n{t},2,B,08:30:00,08:30:00\n"
                              for t in trips))
        zf.writestr("stops.txt", "stop_id,stop_name,stop_lat,stop_lon\n"
                                 "A,Kamnik,46.2,14.6\nB,Ljubljana,46.05,14.5\n")
        zf.writestr("shapes.txt", "shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence\n"
                    + (f"sh1,{trasa[0]},{trasa[1]},1\nsh1,{trasa[0] + 0.004},{trasa[1]},2\n"
                       if trasa else ""))
        zf.writestr("calendar_dates.txt", "service_id,date,exception_type\n"
                                          "s1,20260928,1\n")
    return pot


def test_zip_brez_vlakov_ne_izbrise_voznega_reda(tmp_path):
    """DUJPP je 28. 9. 2026 objavil zip s progami SŽ in brez njihovih voženj.

    Uvoz ga je sprejel in pobrisal vozni red vseh vlakov; zato ga zdaj zavrne,
    zip z vožnjami pa gre skozi kot prej.
    """
    import pytest
    from kajros import db
    c = db.connect(":memory:")
    db.init(c)
    gtfs.import_static(c, _zip(tmp_path / "prej.zip", ["v1"]), lpp_zip=None)
    assert c.execute("SELECT COUNT(*) FROM sched").fetchone()[0] == 2

    with pytest.raises(gtfs.UvozZavrnjen, match="1161"):
        gtfs.import_static(c, _zip(tmp_path / "prazen.zip", []), lpp_zip=None)
    assert c.execute("SELECT COUNT(*) FROM sched").fetchone()[0] == 2, \
        "zavrnjen uvoz je vseeno pobrisal vozni red"

    # Pravi nov vozni red: druge vožnje, isti prevoznik.
    izid = gtfs.import_static(c, _zip(tmp_path / "nov.zip", ["v2", "v3"]), lpp_zip=None)
    assert izid["trips_rail"] == 2


def test_zip_s_tujimi_trasami_se_zavrne(tmp_path):
    """28. 9. 2026 so bile v zipu DUJPP trase pomešane pri 74-100 % voženj
    vsakega avtobusnega prevoznika. Trasa, ki se začne pri prvem postanku
    (Kamnik), gre skozi; ista trasa z začetkom v Novem mestu ne."""
    import pytest
    from kajros import db
    c = db.connect(":memory:")
    db.init(c)
    voznje = [f"v{i}" for i in range(gtfs.TRASA_NAJMANJ)]
    izid = gtfs.import_static(c, _zip(tmp_path / "prej.zip", voznje, (46.2, 14.6)))
    assert izid["trips_rail"] == gtfs.TRASA_NAJMANJ

    with pytest.raises(gtfs.UvozZavrnjen, match="trase"):
        gtfs.import_static(c, _zip(tmp_path / "pomesan.zip", voznje, (45.8, 15.17)))
    assert c.execute("SELECT COUNT(*) FROM sched").fetchone()[0] == 2 * gtfs.TRASA_NAJMANJ
