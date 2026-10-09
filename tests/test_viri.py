"""Viri podatkov: register, dnevnik branj, preverjanje in barve v pregledu.

    ./venv/bin/python -m pytest tests/test_viri.py -q
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import requests

from kajros import db, viri, zdravje

T = 1_791_558_000.0          # 9. 10. 2026 ~16:20


@pytest.fixture(autouse=True)
def _prazen_dnevnik():
    viri.pozabi()
    yield
    viri.pozabi()
    viri.zajem_zagnan = False


def _beri(kljuc, napaka=None, **polja):
    with pytest.raises(type(napaka)) if napaka else _nic():
        with viri.branje(kljuc) as b:
            for k, v in polja.items():
                setattr(b, k, v)
            if napaka:
                raise napaka


class _nic:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_vsak_klic_na_tuj_streznik_je_v_registru():
    """Nov vir = vnos v `viri.vsi()`. Branje s ključem, ki ga register ne
    pozna, bi bilo v pregledu nevidno -- prav to je register odpravil."""
    kljuci = {v.kljuc for v in viri.vsi()}
    assert len(kljuci) == len(viri.vsi()), "ključi so edinstveni"
    koda = "\n".join(p.read_text(encoding="utf-8")
                     for p in Path(viri.__file__).parent.glob("*.py"))
    rabljeni = set(re.findall(r'viri\.branje\("(\w+)"\)', koda))
    rabljeni |= set(re.findall(r'fetch\([^)]*"(\w+)"\)', koda)) - {
        "rt_etag", "lpp_rt_etag", "positions_etag", "alerts_etag"}
    assert rabljeni and rabljeni <= kljuci, rabljeni - kljuci
    # In obratno: vir brez branja v kodi je mrtev vnos.
    assert kljuci <= rabljeni, kljuci - rabljeni
    assert {s for s, _ in viri.SKUPINE} >= {v.skupina for v in viri.vsi()}


def test_dnevnik_steje_branja_in_napake():
    _beri("derp_zamude", http=200, bajtov=1000)
    _beri("derp_zamude", requests.ConnectionError("[Errno 111] Connection refused"))
    d = viri.dnevnik()["derp_zamude"]
    assert d["zaporednih"] == 1 and d["napaka"] == "zavrača povezave"
    assert d["uspeh_ts"] and d["bajtov"] == 1000
    assert (d["ura"]["branj"], d["ura"]["napak"], d["ura"]["bajtov"]) == (2, 1, 1000)
    assert viri.dogodki() == [], "ena napaka ni izpad"


def test_izpad_in_vrnitev_sta_dogodka():
    for _ in range(3):
        _beri("nap", requests.ReadTimeout("x"))
    _beri("nap")
    dogodki = viri.dogodki()
    assert [e["ok"] for e in dogodki] == [True, False], "najnovejši prvi"
    assert "odgovora ni" in dogodki[1]["besedilo"]
    assert "spet odgovarja po 3 napakah" in dogodki[0]["besedilo"]
    assert viri.dnevnik()["nap"]["zaporednih"] == 0


def test_dnevni_vir_je_izpad_ze_ob_prvi_napaki():
    """Vozni red bere enkrat na dan: naslednji poskus je šele jutri."""
    _beri("gtfs_ijpp", requests.ConnectTimeout("x"))
    assert viri.dogodki()[0]["kljuc"] == "gtfs_ijpp"


def test_opis_napake_po_cloveško():
    odg = requests.Response()
    odg.status_code = 503
    assert viri.opis_napake(requests.HTTPError(response=odg)) == "odgovori 503"
    assert viri.opis_napake(requests.ConnectionError("NameResolutionError")) == \
        "ime se ne razreši (DNS)"
    assert viri.opis_napake(RuntimeError("data.lpp.si: 40 od 75")) == "data.lpp.si: 40 od 75"
    assert viri.opis_napake(ValueError("Error parsing")) == "ValueError: Error parsing"


def test_cakanje_pove_zakaj_nit_ne_bere():
    viri.caka("nap", "prijave ni", zdaj=T)
    assert viri.dnevnik()["nap"]["caka"] == "prijave ni"
    _beri("nap")
    assert viri.dnevnik()["nap"]["caka"] is None, "uspešno branje čakanje konča"


class _Odgovor:
    def __init__(self, koda):
        self.status_code = koda

    def close(self):
        pass


def test_preveri_vire_loci_vir_od_interneta():
    v = viri.po_kljucu()
    izbrani = [v["derp_zamude"], v["nap"]]

    def get(izidi):
        def g(url, **_):
            izid = next((x for k, x in izidi.items() if k in url), 200)
            if isinstance(izid, Exception):
                raise izid
            return _Odgovor(izid)
        return g

    izid = viri.preveri_vire(izbrani, get({"b2b.nap.si": 403}), zdaj=T)
    assert all(r["ok"] for r in izid["viri"]), "NAP brez prijave: strežnik je tu"
    assert "Vsi viri odgovarjajo" in izid["sklep"]
    izid = viri.preveri_vire(izbrani, get({"derp.si": requests.ConnectTimeout("x")}), zdaj=T)
    assert izid["padli"] == ["derp.si · zamude IJPP"]
    assert "izpad je pri njih" in izid["sklep"]
    izid = viri.preveri_vire(izbrani, get({"derp.si": requests.ConnectTimeout("x"),
                                           "cloudflare": requests.ConnectTimeout("x")}), zdaj=T)
    assert "nima interneta" in izid["sklep"]


def test_mrtva_nit_je_rdeca_ziva_vira_ne_pobarva():
    viri.zajem_zagnan = True
    m = {"niti": ["kajros-collector"], "pricakovane_niti": viri.pricakovane_niti()}
    o = zdravje.ocena({}, m, T)
    assert o["nit:kajros-collector"][0] == zdravje.DOBRA
    assert o["nit:kajros-nap"] == (zdravje.SLABA, "nit kajros-nap ne teče (nap)")

    c = db.connect(":memory:")
    db.init(c)
    kartice = {v["kljuc"]: v for v in viri.pregled(c, o, T)}
    assert kartice["nap"]["razred"] == zdravje.SLABA
    assert kartice["nap"]["nit_tece"] is False
    # Živa nit ne pomeni zdravega vira: NAP brez prijave teče in ne bere.
    assert kartice["derp_lege"]["razred"] == ""


def test_splosno_pravilo_je_samo_rumeno():
    for _ in range(3):
        _beri("peroni", requests.ReadTimeout("x"))
    o = zdravje.ocena({}, {"viri": viri.dnevnik()}, T)
    assert o["vir:peroni"][0] == zdravje.MLACNA
    assert "tabla SŽ" in o["vir:peroni"][1]
    _beri("peroni")
    assert zdravje.ocena({}, {"viri": viri.dnevnik()}, T)["vir:peroni"][0] == zdravje.DOBRA
    # Vir s svojim pravilom splošnega nima: dve vrstici za isto bi se razšli.
    for _ in range(3):
        _beri("derp_zamude", requests.ReadTimeout("x"))
    assert "vir:derp_zamude" not in zdravje.ocena({}, {"viri": viri.dnevnik()}, T)


def test_vozni_red_ki_se_konca():
    """9. 10. 2026: na razvojnem računalniku LPP znan do 12. 10. -- uvoz ne
    teče, mestne linije bi čez tri dni izginile brez napake v dnevniku."""
    o = zdravje.ocena({"vozni_red": {"zeleznica": "2026-12-12", "avtobus": "2027-12-31",
                                     "lpp": "2026-10-17"}}, {}, T)
    assert o["vozni_red"][0] == o["vozni_red_lpp"][0] == zdravje.DOBRA
    o = zdravje.ocena({"vozni_red": {"lpp": "2026-10-12"}}, {}, T)
    assert o["vozni_red_lpp"] == (zdravje.MLACNA, "vozni red mestnega LPP znan le do 12. 10.")
    o = zdravje.ocena({"vozni_red": {"lpp": "2026-10-10", "zeleznica": "2026-10-14"}}, {}, T)
    assert o["vozni_red_lpp"][0] == zdravje.SLABA
    assert o["vozni_red"][0] == zdravje.MLACNA
    o = zdravje.ocena({"vozni_red": {"lpp": "2026-10-05"}}, {}, T)
    assert o["vozni_red_lpp"][1] == "vozni red mestnega LPP se je končal 5. 10."


def test_shranjeno_stanje_prezivi_zagon(tmp_path):
    """Vozni red na arwenu bere podproces: pregled ga vidi le prek baze."""
    c = db.connect(tmp_path / "k.sqlite")
    db.init(c)
    _beri("gtfs_lpp", http=304, nespremenjeno=True)
    viri.shrani(c, "gtfs_lpp")
    viri.pozabi()
    kartica = {v["kljuc"]: v for v in viri.pregled(c, {}, T)}["gtfs_lpp"]
    assert kartica["dnevnik"]["iz_baze"] and kartica["dnevnik"]["nespremenjeno"]
