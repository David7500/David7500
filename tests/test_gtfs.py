"""Uvoz voznega reda: kar se da preveriti brez zipa in brez omrežja.

Večino uvoza preverja `scripts/preveri_skladnost.py` na pravi bazi; tu so
čiste funkcije, ki se pokvarijo tiho.

    ./venv/bin/python -m pytest tests/test_gtfs.py -q
"""
from __future__ import annotations

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
