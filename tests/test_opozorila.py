"""Barve zdravja in opozorila po pošti.

    ./venv/bin/python -m pytest tests/test_opozorila.py -q
"""
from __future__ import annotations

from kajros import opozorila, zdravje
from kajros.opozorila import KONEC_S, ZAMIK_S

T = 1_790_834_000.0          # 1. 10. 2026 ~7:53


def _zdravo(zdaj=T):
    return {"last_feed_ts": zdaj - 20,
            "by_network": {"zeleznica": {"last_feed_ts": zdaj - 100},
                           "avtobus": {"last_feed_ts": zdaj - 100}},
            "rt_neznanih": {"ijpp": [0, 692], "lpp": [1, 277]},
            "lega_brez_zamude": {"Arriva": [1, 0, 109]},
            "zamude_sz": {"ts": zdaj - 30, "oba": 30, "samo_sz": 0, "samo_derp": 2}}


STROJ = {"disk_prostih": 26 * 2**30, "disk_vseh": 234 * 2**30, "wal_bajtov": 64 * 2**20}


def _rdece(z, m=STROJ, zdaj=T):
    return {k for k, (r, _) in zdravje.ocena(z, m, zdaj).items() if r == zdravje.SLABA}


def test_zdravo_ni_rdece():
    assert _rdece(_zdravo()) == set()


def test_obstala_nit_sz_je_rdeca_nedosegljiv_vir_pa_rumen():
    """1. 10. 2026: nit ni mogla zapisati niti napake -- 4,3 h le rumeno."""
    z = _zdravo()
    z["zamude_sz"] = {"ts": T - 4.3 * 3600, "oba": 2}
    assert _rdece(z) == {"zamude_sz"}
    z["zamude_sz"].update(napaka="500 Server Error", napaka_ts=T - 40)
    assert zdravje.ocena(z, STROJ, T)["zamude_sz"][0] == zdravje.MLACNA


def test_wal_in_disk():
    m = {**STROJ, "wal_bajtov": int(5.4 * 2**30)}
    assert _rdece(_zdravo(), m) == {"wal"}
    m = {**STROJ, "disk_prostih": 20 * 2**30}
    assert zdravje.ocena(_zdravo(), m, T)["disk"][0] == zdravje.MLACNA


def test_lpp_brez_voznega_reda_po_deležu():
    z = _zdravo()
    z["rt_neznanih"]["lpp"] = [30, 282]
    assert _rdece(z) == {"neznane"}
    assert "LPP 30 od 282" in zdravje.ocena(z, STROJ, T)["neznane"][1]


def _ocena(*rdece):
    return {k: (zdravje.SLABA, f"{k} stoji") for k in rdece} | {"feed": (zdravje.DOBRA, "")}


def _teci(koraki, zacetek=T):
    """(sekunde od začetka, rdeče ključe) -> poslana sporočila (zadeva, čas)."""
    stanje, poslano = {}, []
    for t, rdece in koraki:
        stanje, sp, nove, resene = opozorila.korak(stanje, _ocena(*rdece), zacetek + t)
        if sp:
            stanje = opozorila._potrdi(stanje, nove, resene, zacetek + t)
            poslano.append((sp[0], t, sp[1]))
    return poslano


def test_ena_posta_ob_okvari_in_ena_ob_koncu():
    koraki = [(t, ["zamude_sz"]) for t in range(0, 4 * 3600, 60)]
    koraki += [(4 * 3600 + t, []) for t in range(0, 900, 60)]
    poslano = _teci(koraki)
    assert [(z.split(" -- ")[0], t) for z, t, _ in poslano] == [
        ("kajros: stoji", ZAMIK_S), ("kajros: spet dela", 4 * 3600 + KONEC_S)]
    assert "stalo 07:53–11:53, 4 h 0 min" in poslano[1][2]


def test_kratka_motnja_in_nihanje_sta_tiha():
    """Ponovni zagon ali en zgrešen obhod nista okvara; nihanje okoli meje
    po poslanem opozorilu ne pošilja para sporočil za vsak preskok."""
    assert _teci([(0, ["feed"]), (60, ["feed"]), (120, []), (600, []), (900, [])]) == []
    koraki = [(t, ["neznane"]) for t in range(0, 700, 60)]
    koraki += [(700 + t, [] if (t // 60) % 2 else ["neznane"]) for t in range(0, 1800, 60)]
    assert len(_teci(koraki)) == 1


def test_neuspela_posta_se_ponovi():
    stanje, sp, nove, resene = opozorila.korak({}, _ocena("wal"), T)
    stanje, sp, nove, _ = opozorila.korak(stanje, _ocena("wal"), T + ZAMIK_S)
    assert sp and nove == ["wal"]
    # Pošta ne uspe: klicatelj stanja ne potrdi, naslednji obhod poskusi znova.
    _, sp, nove, _ = opozorila.korak(stanje, _ocena("wal"), T + ZAMIK_S + 60)
    assert sp and nove == ["wal"]
