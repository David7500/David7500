"""Geometrija: razdalje, projekcija na progo, poenostavljanje.

Te funkcije so bile do 4. 9. 2026 brez enega samega testa, čeprav so
najlažje preverljive v projektu in nosijo številke, ki jih prikaz pokaže
potniku: dolžino mreže, „do tebe ima še 1,2 km poti“ in traso na zemljevidu.

Referenčne vrednosti so izračunane neodvisno (poldnevnik, ekvator, znane
razdalje med slovenskimi mesti), ne prepisane iz izhoda funkcije — sicer bi
test potrjeval le, da se koda ni spremenila.
"""
from __future__ import annotations

import math

import pytest

from kajros import geo

# Ljubljana, Maribor, Celje -- iz GTFS postaj, na tri decimalke.
LJ = (46.058, 14.510)
MB = (46.563, 15.650)
CE = (46.229, 15.267)


def test_haversine_je_nic_za_isto_tocko():
    assert geo.haversine(*LJ, *LJ) == pytest.approx(0.0, abs=1e-9)


def test_haversine_po_poldnevniku_ustreza_stopinji():
    """Ena stopinja zemljepisne širine je ~111,2 km povsod na Zemlji."""
    d = geo.haversine(46.0, 14.5, 47.0, 14.5)
    assert d == pytest.approx(111195, rel=0.001)


def test_haversine_po_ekvatorju_ustreza_stopinji():
    d = geo.haversine(0.0, 0.0, 0.0, 1.0)
    assert d == pytest.approx(111195, rel=0.001)


def test_haversine_je_simetricen():
    assert geo.haversine(*LJ, *MB) == pytest.approx(geo.haversine(*MB, *LJ))


def test_haversine_ljubljana_maribor():
    """Zračna razdalja Ljubljana–Maribor je ~104 km.

    Izpeljano neodvisno, ne prepisano iz izhoda: Δšir 0,505° = 56,2 km,
    Δdolž 1,140° pri 46,3° = 1,140 × 111,32 × cos 46,3° = 87,7 km,
    hipotenuza √(56,2² + 87,7²) = 104,2 km. (Železniška je 156 km — proga
    gre prek Zidanega Mosta in je za polovico daljša od zračne.)

    Prva različica tega testa je trdila 98 km in je padla. Padla je po
    pravici: napačna je bila referenca, ne koda.
    """
    assert geo.haversine(*LJ, *MB) / 1000 == pytest.approx(104.2, abs=1.0)


def test_cumulative_raste_in_se_zacne_pri_nic():
    tocke = [LJ, CE, MB]
    c = geo.cumulative(tocke)
    assert len(c) == len(tocke)
    assert c[0] == 0.0
    assert c[1] < c[2]
    # Vsota odsekov mora biti kumulativa -- brez tega bi se napaka skrila.
    assert c[2] == pytest.approx(geo.haversine(*LJ, *CE) + geo.haversine(*CE, *MB))


def test_cumulative_ene_tocke():
    assert geo.cumulative([LJ]) == [0.0]


def test_project_tocke_na_progi_da_odmik_nic():
    """Postaja, ki leži na progi, mora imeti odmik 0 in znano lego vzdolž nje."""
    tocke = [(46.0, 14.0), (46.0, 15.0)]
    c = geo.cumulative(tocke)
    along, off = geo.project(tocke, c, 46.0, 14.5)
    assert off == pytest.approx(0.0, abs=1.0)
    assert along == pytest.approx(c[1] / 2, rel=0.01)


def test_project_odmik_meri_oddaljenost_od_proge():
    """Odmik je merilo zaupanja: velik pomeni, da postaja ni na tej progi."""
    tocke = [(46.0, 14.0), (46.0, 15.0)]
    c = geo.cumulative(tocke)
    _, off = geo.project(tocke, c, 46.01, 14.5)     # 0,01 stopinje severno
    assert off == pytest.approx(1112, rel=0.02)


def test_project_pred_zacetkom_pripne_na_zacetek():
    """Točka pred progo se ne sme projicirati v negativno razdaljo."""
    tocke = [(46.0, 14.0), (46.0, 15.0)]
    c = geo.cumulative(tocke)
    along, _ = geo.project(tocke, c, 46.0, 13.5)
    assert along == pytest.approx(0.0, abs=1.0)


def test_project_za_koncem_pripne_na_konec():
    tocke = [(46.0, 14.0), (46.0, 15.0)]
    c = geo.cumulative(tocke)
    along, _ = geo.project(tocke, c, 46.0, 15.5)
    assert along == pytest.approx(c[-1], abs=1.0)


def test_slice_between_vzame_sredino():
    tocke = [(46.0, 14.0 + i / 10) for i in range(11)]
    c = geo.cumulative(tocke)
    kos = geo.slice_between(tocke, c, c[3], c[6])
    assert kos[0] == tocke[3] and kos[-1] == tocke[6]


def test_slice_between_obrne_kadar_gre_nazaj():
    """Smer šteje: vozilo, ki gre v drugo smer, mora dobiti obrnjeno traso."""
    tocke = [(46.0, 14.0 + i / 10) for i in range(11)]
    c = geo.cumulative(tocke)
    naprej = geo.slice_between(tocke, c, c[2], c[5])
    nazaj = geo.slice_between(tocke, c, c[5], c[2])
    assert nazaj == list(reversed(naprej))


def test_simplify_pusti_ravno_crto_pri_dveh_tockah():
    """Ravna proga se mora skrčiti na krajišči -- to je ves smisel."""
    tocke = [(46.0, 14.0 + i / 100) for i in range(50)]
    assert geo.simplify(tocke, eps=1e-4) == [tocke[0], tocke[-1]]


def test_simplify_obdrzi_pravi_ovinek():
    tocke = [(46.0, 14.0), (46.05, 14.5), (46.0, 15.0)]
    assert geo.simplify(tocke, eps=1e-4) == tocke


def test_simplify_ne_spremeni_kratkega_seznama():
    assert geo.simplify([LJ, MB]) == [LJ, MB]
    assert geo.simplify([LJ]) == [LJ]


def test_simplify_ohrani_krajisci():
    """Karkoli vrže ven, prve in zadnje točke ne sme -- sicer trasa odplava."""
    tocke = [(46.0 + math.sin(i / 3) / 200, 14.0 + i / 100) for i in range(60)]
    p = geo.simplify(tocke, eps=1e-3)
    assert p[0] == tocke[0] and p[-1] == tocke[-1]
    assert len(p) < len(tocke)
