"""`stats.uskladi_ure`: v oknu vlaka nobena ura ne gre nazaj."""
from kajros import stats


def _p(seq, arr_min, dep_min, da, dd):
    return {"stop_seq": seq, "arr_s": arr_min * 60, "dep_s": dep_min * 60,
            "delay_arr": da, "delay_dep": dd}


def test_stara_zamuda_na_vmesnem_popusti_naslednji_registraciji():
    """Zemljevid je Zagorje prevozil po uri s +15, naslednja registracija na
    Savi pove +3 (LPV 2206 6. 11. 2026, vozni red 07:53 -> 08:01)."""
    vrstice = [_p(3, 7 * 60 + 47, 7 * 60 + 48, 120, 120),
               _p(4, 7 * 60 + 52, 7 * 60 + 53, 120, 900),
               _p(5, 8 * 60 + 1, 8 * 60 + 2, 180, 180)]
    stats.uskladi_ure(vrstice)
    assert (vrstice[1]["delay_arr"], vrstice[1]["delay_dep"]) == (120, 240)
    assert vrstice[1]["uskladeno"] and "uskladeno" not in vrstice[0]
    ure = []
    for d in vrstice:
        ure += [d["arr_s"] + d["delay_arr"], d["dep_s"] + d["delay_dep"]]
    assert ure == sorted(ure)


def test_prihod_po_odhodu_popusti_odhodu():
    vrstice = [_p(6, 8 * 60 + 8, 8 * 60 + 9, 900, 60), _p(7, 8 * 60 + 15, 8 * 60 + 16, 60, 0)]
    stats.uskladi_ure(vrstice)
    assert (vrstice[0]["delay_arr"], vrstice[0]["delay_dep"]) == (120, 60)


def test_dosledna_voznja_ostane():
    vrstice = [_p(1, 600, 600, None, 120), _p(2, 610, 611, 180, 240), _p(3, 620, 620, 300, None)]
    prej = [dict(d) for d in vrstice]
    stats.uskladi_ure(vrstice)
    assert vrstice == prej


def test_manjkajoca_vrednost_ne_moti():
    vrstice = [_p(1, 600, 600, None, 900), _p(2, 610, 611, None, None), _p(3, 620, 621, 60, 60)]
    stats.uskladi_ure(vrstice)
    assert vrstice[0]["delay_dep"] == 60 + 120
