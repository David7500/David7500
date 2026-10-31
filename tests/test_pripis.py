"""Pripis vozila na vožnjo: par samo z dokazom, sicer brez para."""
from kajros import db, pripis, stats
from kajros.pripis import Napredek, Voznja, kandidati, predlagaj

ZDAJ = 1_000_000.0


def _v(trip, min_od_zdaj, dan="2026-10-30", seq=5):
    return Voznja(trip, dan, seq, ZDAJ + 60 * min_od_zdaj)


def test_ena_prosta_v_oknu_je_par():
    p = predlagaj([_v("T1", -3), _v("T2", 40)], ZDAJ, set())
    assert p.voznja.trip_id == "T1" and p.razlog == ""


def test_zasedena_ni_na_voljo_in_prepusti_naslednji():
    # Mrtvo vozilo ima T1; živi za njim je na T2, ki je blizu.
    p = predlagaj([_v("T1", -8), _v("T2", 2)], ZDAJ, {("T1", "2026-10-30")})
    assert p.voznja.trip_id == "T2"


def test_dve_prosti_nista_dokaz():
    p = predlagaj([_v("T1", -3), _v("T2", -9)], ZDAJ, set())
    assert p.voznja is None and p.razlog == "vec"


def test_starejsa_prosta_tekmuje_tudi_zunaj_okna():
    # Vožnja 25 min nazaj nima vozila: to je lahko prav ta, zelo pozna.
    p = predlagaj([_v("T1", -25), _v("T2", 2)], ZDAJ, set())
    assert p.voznja is None and p.razlog == "vec"


def test_brez_voznje_v_oknu_ni_para():
    p = predlagaj([_v("T1", -45), _v("T2", 30)], ZDAJ, set())
    assert p.voznja is None and p.razlog == "ni_prosta"


def test_isti_trip_drug_dan_ni_zaseden():
    p = predlagaj([_v("T1", -2)], ZDAJ, {("T1", "2026-10-29")})
    assert p.voznja.trip_id == "T1"


def test_vozilo_ki_ne_napreduje_nima_para():
    p = predlagaj([_v("T1", -2)], ZDAJ, set(), napreduje=False)
    assert p.voznja is None and p.razlog == "miruje"


def test_napredek_rabi_spremembo_na_isti_varianti():
    n = Napredek()
    assert n.opazi("a", "V1", "S1") is False
    assert n.opazi("a", "V1", "S1") is False
    assert n.opazi("a", "V1", "S2") is True
    assert n.opazi("a", "V1", "S2") is True, "ostane, tudi ko vozilo stoji na postanku"
    assert n.opazi("a", "V2", "S3") is False, "nova varianta začne znova"
    n.pozabi(set())
    assert n.opazi("a", "V2", "S4") is False


def test_kandidati_vzamejo_prvo_postajalisce_z_voznjami():
    idx = {("V1", "S2"): [_v("T1", 0)]}
    assert kandidati(idx, "V1", ["S1", "S2"])[0].trip_id == "T1"
    assert kandidati(idx, "V9", ["S1", "S2"]) == []


def test_indeks_po_varianti_in_liniji(tmp_path):
    conn = db.connect(tmp_path / "t.sqlite")
    db.init(conn)
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, agency, shape_id) "
                 "VALUES('T1', 'R1', 'G1', 'S', 'marprom', 'V1')")
    conn.execute("INSERT INTO service_day(service_id, date) VALUES('S', '2026-10-30')")
    conn.execute("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) "
                 "VALUES('T1', 2, 'P1', 36000, 36060)")
    zdaj = stats.polnoc("2026-10-30") + 36000
    idx = pripis.indeks(conn, zdaj, "marprom")
    # Odhod, ne prihod: povsod `COALESCE(dep, arr)`.
    assert idx[("V1", "P1")] == [Voznja("T1", "2026-10-30", 2, zdaj + 60)]
    assert idx[("R1", "P1")] == idx[("V1", "P1")]
    assert pripis.indeks(conn, zdaj, "drug") == {}


def test_na_voznji_čas_po_razdalji_in_v_zanki_bližji_čas():
    postanki = [(1, 46.0, 14.0, 0), (2, 46.0, 14.1, 600), (3, 46.0, 14.0, 1200)]
    t, seq = pripis.na_voznji(postanki, 46.0, 14.03, 200)
    assert seq == 2 and abs(t - 180) < 5
    # Isti kraj tja in nazaj: velja prehod, ki je bližje uri.
    t, seq = pripis.na_voznji(postanki, 46.0, 14.03, 1000)
    assert seq == 3 and abs(t - 1020) < 5
    assert pripis.na_voznji(postanki, 46.05, 14.03, 200) is None     # 5,6 km od tetive
