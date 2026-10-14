"""Promet na cestah z NAP: razbor FCD in potovalnih časov AC, dnevnik sprememb.

    ./venv/bin/python -m pytest tests/test_promet.py -q
"""
from __future__ import annotations

import gzip

import pytest

from kajros import promet


def _pq(odsek: int, cas: float, prosto: float = 2.77) -> str:
    # Oblika iz odgovora NAP 14. 10. 2026, skrajšana.
    return f"""<physicalQuantity xsi:type="SinglePhysicalQuantity"
        xmlns="http://datex2.eu/schema/3/roadTrafficData">
      <pertinentLocation xmlns:q1="http://datex2.eu/schema/3/locationReferencing"
          xsi:type="q1:LocationByReference">
        <q1:predefinedLocationReference id="{odsek}" version="0" targetClass="loc:PredefinedLocation" />
      </pertinentLocation>
      <basicData xsi:type="TravelTimeData">
        <measurementOrCalculationTime><timeValue>2026-10-14T13:25:19</timeValue></measurementOrCalculationTime>
        <travelTime><duration>{cas}</duration></travelTime>
        <freeFlowTravelTime><duration>{prosto}</duration></freeFlowTravelTime>
        <normallyExpectedTravelTime><duration>{prosto}</duration></normallyExpectedTravelTime>
        <travelTimeDelay><duration>{cas - prosto}</duration></travelTimeDelay>
        <freeFlowSpeed><speed xmlns="http://datex2.eu/schema/3/common">63</speed></freeFlowSpeed>
      </basicData>
    </physicalQuantity>"""


def _fcd(cas: str, odseki: list[tuple[int, float]]) -> bytes:
    telo = "".join(_pq(o, c) for o, c in odseki)
    return f"""<ElaboratedDataPublication xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        lang="sl" modelBaseVersion="3">
      <publicationTime xmlns="http://datex2.eu/schema/3/common">{cas}</publicationTime>
      {telo}
    </ElaboratedDataPublication>""".encode()


AC = b"""<?xml version="1.0" encoding="utf-8"?>
<ElaboratedDataPublication xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" lang="sl">
  <publicationTime xmlns="http://datex2.eu/schema/3/common">2026-10-14T11:22:59.0634089Z</publicationTime>
  <physicalQuantity xsi:type="SinglePhysicalQuantity" xmlns="http://datex2.eu/schema/3/roadTrafficData">
    <pertinentLocation><locationContainedInItinerary index="0"><location>
      <basicData><travelTime><duration>1.0</duration></travelTime></basicData>
    </location></locationContainedInItinerary></pertinentLocation>
    <source><sourceCountry>si</sourceCountry>
      <sourceName><values><value lang="sl">LJ - MB</value><value lang="en">LJ - MB</value></values></sourceName>
    </source>
    <basicData xsi:type="TravelTimeData">
      <travelTime><duration>4250.923</duration></travelTime>
      <freeFlowTravelTime><duration>3725.569</duration></freeFlowTravelTime>
      <travelTimeDelay><duration>525.354</duration></travelTimeDelay>
    </basicData>
  </physicalQuantity>
</ElaboratedDataPublication>"""


@pytest.fixture
def conn(tmp_path):
    c = promet.povezi(tmp_path / "promet.sqlite")
    yield c
    c.close()


def test_razbor_fcd_gzip_in_navaden():
    """NAP pošlje datoteko gzip brez `Content-Encoding`; razbor jo razpakira
    sam. Čas brez glave pasu je lokalni."""
    xml = _fcd("2026-10-14T13:25:19", [(1586, 6.535), (1602, 31.843)])
    for vsebina in (xml, gzip.compress(xml)):
        ts, odseki = promet.razberi_fcd(vsebina)
        assert odseki == {1586: (65, 28), 1602: (318, 28)}
        assert ts == promet.nap._cas("2026-10-14T13:25:19")


def test_razbor_ac_vzame_vsoto_relacije_ne_dela_poti():
    ts, relacije = promet.razberi_ac(AC)
    assert relacije == [("LJ - MB", 4251, 3726)]
    assert ts == int(promet.nap._cas("2026-10-14T11:22:59.0634089Z"))


def _vrstice(conn):
    return [tuple(r) for r in conn.execute("SELECT odsek, ts, cas_ds FROM fcd ORDER BY ts, odsek")]


def test_dnevnik_fcd_spremembe_prag_in_izginotje(conn):
    promet.zapisi_fcd(conn, 100, {1: (80, 30), 2: (200, 50)})
    # 1: +0,3 s je pod pragom; 2: +1 s je sprememba; 3 je nov.
    promet.zapisi_fcd(conn, 160, {1: (83, 30), 2: (210, 50), 3: (90, 40)})
    # 1: še +0,3 s -- skupaj 0,6 s od ZAPISANE, torej zapis; 2 izgine = prosto.
    st = promet.zapisi_fcd(conn, 220, {1: (86, 30), 3: (90, 40)})
    assert _vrstice(conn) == [(1, 100, 80), (2, 100, 200), (2, 160, 210), (3, 160, 90),
                              (1, 220, 86), (2, 220, None)]
    assert st == {"odsekov": 2, "novih": 0, "zapisanih": 2, "prostih": 1}
    assert [tuple(r) for r in conn.execute("SELECT * FROM fcd_zdaj ORDER BY odsek")] == \
        [(1, 86), (3, 90)]
    assert [r[0] for r in conn.execute("SELECT ts FROM obhod")] == [100, 160, 220]


def test_ista_objava_dvakrat_ni_nov_obhod(conn):
    promet.zapisi_fcd(conn, 100, {1: (80, 30)})
    assert promet.zapisi_fcd(conn, 100, {}) == {"nespremenjeno": True}
    assert _vrstice(conn) == [(1, 100, 80)], "prazen odgovor z isto objavo ne sprosti odseka"


def test_cas_brez_prometa_se_hrani_po_odseku(conn):
    promet.zapisi_fcd(conn, 100, {1: (80, 30)})
    promet.zapisi_fcd(conn, 160, {1: (80, None)})
    promet.zapisi_fcd(conn, 220, {1: (80, 31)})
    assert tuple(conn.execute("SELECT * FROM fcd_odsek").fetchone()) == (1, 31, 100)


def test_potovalni_casi_ac_ista_objava_enkrat(conn):
    assert promet.zapisi_ac(conn, 100, [("LJ - MB", 4251, 3726), ("LJ - KP", 3840, 3265)]) == 2
    assert promet.zapisi_ac(conn, 100, [("LJ - MB", 4251, 3726)]) == 0
    assert promet.zapisi_ac(conn, 400, [("LJ - MB", 4300, 3726)]) == 1
