"""Čiščenje učne zgodovine in nove metrike backtesta (6. 11. 2026).

`stats.ocisti_dan` je ena funkcija za `backtest._delays_by_day` in
`stats.predict(ocisti=True)`; backtest dobi `podcenj.`, `precenj.`, strošek in
zveznost (docs/presoja/vlaki-prenova/modeli.md).

    ./venv/bin/python -m pytest tests/test_ciscenje_zgodovine.py -q
"""
from __future__ import annotations

import pytest

from kajros import backtest, db, ocena, stats

D = "2026-10-20"
P = stats.polnoc(D)
H = 3600


def _m(d, ts_po_prihodu=True, prihod=None, seq=0):
    """Postanek (zamuda, feed_ts, prihod); zapis je po prihodu, če ni drugače."""
    prihod = 8 * H + seq * 600 if prihod is None else prihod
    ts = P + prihod + d + (60 if ts_po_prihodu else -600)
    return (d, ts, prihod)


def _dan(zamude, nepotrjeni=()):
    return {i + 1: _m(d, ts_po_prihodu=(i + 1) not in nepotrjeni, seq=i)
            for i, d in enumerate(zamude)}


def test_nepotrjena_napoved_odpade():
    """(a) zapis starejši od prihoda + zamude - 120 s ni meritev."""
    ohranjeni, a, b = stats.ocisti_dan(_dan([0, 0, 900, 900], nepotrjeni={3, 4}), {}, D)
    assert a == {3, 4} and ohranjeni == {1, 2} and b == set()


def test_nepotrjena_napoved_pred_zemljevidom_ne_velja():
    """Do 10. 10. 2026 je `feed_ts` žig derp.si, ne naš čas: (a) se ne uporabi."""
    stari = "2026-10-01"
    postanki = {i + 1: (d, stats.polnoc(stari) + 8 * H + i * 600 + d - 600, 8 * H + i * 600)
                for i, d in enumerate([0, 0, 900, 900])}
    assert not stats.ocisti_dan(postanki, {}, stari)[1]
    assert stats.ocisti_dan(postanki, {}, "2026-10-10")[1] == {1, 2, 3, 4}


def test_brez_voznorednega_prihoda_ostane():
    ohranjeni, a, _ = stats.ocisti_dan({1: (0, 5, None), 2: (60, 5, None)}, {}, D)
    assert ohranjeni == {1, 2} and not a


def test_osamelec_v_odstranjen():
    """RG 318: 1200, 240, 1500 -- vlak ne izgubi 16 min na 4 min vožnje."""
    ohranjeni, a, b = stats.ocisti_dan(_dan([1200, 1200, 240, 1500, 1500]), {}, D)
    assert b == {3} and ohranjeni == {1, 2, 4, 5} and not a


def test_osamelec_lambda_odstranjen():
    """Skok navzgor in takoj nazaj: zamuda ne pade za 15 min brez rezerve."""
    ohranjeni, _, b = stats.ocisti_dan(_dan([0, 0, 900, 0, 0]), {}, D)
    assert b == {3}


def test_padec_do_rezerve_in_tolerance_je_dovoljen():
    """Postanek 10 min nad najkrajšim: zamuda lahko pade za 10 min + 2 min."""
    rez = {2: 600}
    _, _, b = stats.ocisti_dan(_dan([900, 300]), rez, D)       # 600 + 0 <= 600 + 120
    assert not b
    _, _, b = stats.ocisti_dan(_dan([900, 100]), rez, D)       # 800 > 600 + 120
    assert b


def test_rezerva_med_postankoma_se_sesteje():
    """Neizmerjen vmesni postanek 3 (rezerva 5 min) šteje med a=1 in b=4."""
    postanki = {1: _m(900, seq=0), 4: _m(300, seq=3)}
    rez = {3: 300, 4: 300}
    assert not stats.ocisti_dan(postanki, rez, D)[2]
    assert stats.ocisti_dan(postanki, {3: 100, 4: 100}, D)[2]


def test_dlje_zaporedje_prevlada_ne_zadnje():
    """Dvoje nasprotujočih: obdrži se tisto z več postanki (kot oznaci_neskladne)."""
    ohranjeni, _, b = stats.ocisti_dan(_dan([1500, 1500, 1500, 0, 0]), {}, D)
    assert ohranjeni == {1, 2, 3} and b == {4, 5}


def test_strosek_para_je_ista_funkcija_kot_strosek():
    vals = [(600, 300), (300, 600), (0, 0), (900, 100)]
    h = ocena.RAZMIK_S["zeleznica"]
    assert ocena._strosek(vals, "zeleznica") == round(
        sum(ocena.strosek_para(a, b, h) for a, b in vals) / len(vals) / 60, 2)
    # precenitev > rezerva = razmik; podcenitev = čakanje razlike
    assert ocena.strosek_para(600, 0, h) == h
    assert ocena.strosek_para(0, 600, h) == 600 + ocena.POTNIKOVA_REZERVA_S


def test_metrike_napovedi_smer_napake():
    m = backtest.metrike_napovedi([(0, 600), (600, 0), (100, 100), (0, 200)])
    assert (m["podcenj"], m["precenj"], m["v5min"]) == (25.0, 25.0, 50.0)
    assert m["mae_min"] == round((600 + 600 + 0 + 200) / 4 / 60, 2)


def test_zveznost_stejse_skoke():
    z = backtest.zveznost([0, 600, 60, 360])
    assert z["n_par"] == 4 and z["zvez_skok"] == 50.0
    assert z["zvez_min"] == round((0 + 600 + 60 + 360) / 4 / 60, 2)
    assert backtest.zveznost([]) == {"n_par": 0}


def _naloga(dan, i, j, d_i, d_j, slack=0, voznja="RG 1"):
    return {"train_no": voznja, "day": dan, "i": i, "j": j, "horizon": j - i,
            "d_i": d_i, "d_j": d_j, "seg": (f"s{i}", f"s{j}"), "slack": slack,
            "network": "zeleznica", "izhodisce": False, "ok": True}


def test_pari_zveznosti_zaporedna_izhodisca_z_isto_zamudo():
    t = [_naloga("d1", 1, 3, 300, 300), _naloga("d1", 2, 3, 330, 300),
         _naloga("d1", 1, 4, 300, 300), _naloga("d1", 2, 4, 330, 300),
         _naloga("d2", 1, 3, 300, 300), _naloga("d2", 2, 3, 900, 300)]
    pari = backtest.pari_zveznosti(t)
    assert sorted((a, b) for a, b, _ in pari) == [(0, 1), (2, 3)]    # d2: razlika 600 s


def _ucni_dnevi():
    naloge = []
    for n in range(8):
        dan = f"2026-10-{10 + n:02d}"
        d_i = 300 if n % 2 else 700
        for j in (3, 4):
            naloge.append(_naloga(dan, 1, j, d_i, d_i - 120 + 60 * n, slack=240))
    return naloge


@pytest.mark.parametrize("ime", [k for k, (_, uci) in backtest.MODELI_VARNI.items() if uci])
def test_varni_modeli_izpuscajo_dan(ime):
    """Tabele iz vseh dni + izpuščanje v `predict` = učenje brez tega dne."""
    vsi = _ucni_dnevi()
    tovarna = backtest.MODELI_VARNI[ime][0]
    skupna = tovarna(vsi)
    for t in vsi:
        brez = [u for u in vsi if u["day"] != t["day"]]
        assert skupna(t) == tovarna(brez)(t)


def test_sedanji_model_je_enak_staremu():
    vsi = _ucni_dnevi()
    nov = backtest.MODELI_VARNI["fizika_razred (sedanji)"][0](vsi)
    for t in vsi:
        brez = [u for u in vsi if u["day"] != t["day"]]
        assert nov(t) == backtest.model_fizika_razred(brez)(t)


def test_varna_strosek_ne_prehiti_varne_mediane():
    """Strošek-optimum je pri empirični porazdelitvi nad nizkim ostankom."""
    vsi = [_naloga(f"2026-10-{10 + n:02d}", 1, 3, 600, 600 + o)
           for n, o in enumerate([0, 0, 0, 0, 0, 0, 0, 0, 0, 900])]
    p = backtest.MODELI_VARNI["varna_strosek"][0](vsi)
    # brez izpuščenega dne (n=9 s poljubno napako 0) ostanek 0 + rezerva 5 min
    assert p(vsi[0]) == 600 + ocena.POTNIKOVA_REZERVA_S


@pytest.fixture()
def conn():
    c = db.connect(":memory:")
    db.init(c)
    c.execute("INSERT INTO service_day(service_id, date) VALUES('S1', ?)", (D,))
    return c


def test_delays_by_day_ocisti_uporabi_isto_pravilo(conn):
    h = 3600
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, network) "
                 "VALUES('t1', 'r', 'RG 1', 'S1', 'rail', 'zeleznica')")
    for seq in range(1, 6):
        conn.execute("INSERT OR IGNORE INTO station(stop_id, name, lat, lon) VALUES(?, ?, 46, 14)",
                     (f"P{seq}", f"P{seq}"))
        conn.execute("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) "
                     "VALUES('t1', ?, ?, ?, ?)", (seq, f"P{seq}", 8 * h + seq * 600,
                                                 8 * h + seq * 600 + 60))
    # 3. postanek: osamelec V; 5. postanek: zapis pred prihodom (napoved)
    for seq, d, ts in [(1, 900, P + 8 * h + 600 + 900 + 60),
                       (2, 900, P + 8 * h + 1200 + 900 + 60),
                       (3, 60, P + 8 * h + 1800 + 60 + 60),
                       (4, 900, P + 8 * h + 2400 + 900 + 60),
                       (5, 900, P + 8 * h + 100)]:
        conn.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_dep, feed_ts) "
                     "VALUES('t1', ?, ?, ?, ?)", (D, seq, d, ts))
    surovo = backtest._delays_by_day(conn)
    cisto = backtest._delays_by_day(conn, ocisti=True)
    assert set(surovo[("t1", D)]) == {1, 2, 3, 4, 5}
    assert set(cisto[("t1", D)]) == {1, 2, 4}
    nalogi = backtest.build_tasks(conn, oznaci=True)
    assert {(t["i"], t["j"]) for t in nalogi if t["ok"]} == {(1, 2), (1, 4), (2, 4)}
