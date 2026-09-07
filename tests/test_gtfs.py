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
