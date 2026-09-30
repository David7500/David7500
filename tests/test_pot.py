"""Testi iskanja od vrat do vrat.

Hoja je tu **izračunana iz zračne razdalje**, ne iz usmerjevalnika: preverjamo
iskanje, ne OSRM. Vrednosti so zato predvidljive in test ne rabi vsebnika.
"""
from __future__ import annotations

import pytest

from kajros import db, geo, hoja, pot, stats

D = "2026-09-08"

# Izhodišče in cilj sta 11 km narazen, torej hoje vso pot ni.
OD = (46.000, 14.500)
DO = (46.100, 14.500)


@pytest.fixture(autouse=True)
def hoja_po_zraku(monkeypatch):
    """Hoja = zračna razdalja pri 5 km/h, brez faktorja in brez omrežja."""
    def matrika(lat, lon, cilji, smer="od"):
        return ([round(geo.haversine(lat, lon, a, b) / hoja.HITROST_MS)
                 for a, b in cilji], hoja.OSRM)
    monkeypatch.setattr(hoja, "matrika", matrika)
    monkeypatch.setattr(pot.hoja, "matrika", matrika)
    hoja._PES_CACHE.clear()
    pot._VOZJE_CACHE.clear()
    pot._IMENA_CACHE.clear()
    yield
    hoja._PES_CACHE.clear()


def _postaja(c, stop_id, ime, lat, lon):
    c.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
              (stop_id, ime, lat, lon))


def _voznja(c, trip_id, ime, postanki, omrezje="avtobus"):
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, "
              "mode, network) VALUES(?,?,?,?, 'S1', 'bus', ?)",
              (trip_id, "r" + trip_id, ime, "kam", omrezje))
    for seq, stop_id, t in postanki:
        c.execute("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) "
                  "VALUES(?,?,?,?,?)", (trip_id, seq, stop_id, t, t))


@pytest.fixture()
def conn():
    c = db.connect(":memory:")
    db.init(c)
    c.execute("INSERT INTO service_day(service_id, date) VALUES('S1', ?)", (D,))
    #   BLIZU   111 m od izhodišča  -> 1,3 min hoje
    #   DALEC   1,1 km od izhodišča -> 13 min hoje
    #   CILJ    111 m od cilja      -> 1,3 min hoje
    #   ROB     1,1 km od cilja     -> 13 min hoje
    _postaja(c, "BLIZU", "Blizu", 46.001, 14.500)
    _postaja(c, "DALEC", "Daleč", 46.010, 14.500)
    _postaja(c, "ROB", "Rob", 46.090, 14.500)
    _postaja(c, "CILJ", "Cilj", 46.099, 14.500)
    c.commit()
    return c


def test_hoja_do_postaje_lahko_zamudi_odhod(conn):
    """Odhod čez pet minut s postajališča, ki je trinajst minut hoje daleč,
    ni povezava — in to je edina razlika med to stranjo in odhodno tablo."""
    _voznja(conn, "t1", "prezgodaj", [(1, "DALEC", 8 * 3600 + 300),
                                      (2, "CILJ", 8 * 3600 + 900)])
    _voznja(conn, "t2", "ujameš", [(1, "DALEC", 8 * 3600 + 1200),
                                   (2, "CILJ", 8 * 3600 + 1800)])
    conn.commit()
    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    voznje = [n for n in r["predlogi"][0]["noge"] if n["vrsta"] == "voznja"]
    assert [v["train_no"] for v in voznje] == ["ujameš"]


def test_zmaga_najmanjsa_vsota_prihoda_in_hoje(conn):
    """Cilj ni postaja, ampak točka.

    Ena vožnja pripelje prej, a se ustavi trinajst minut hoje od cilja; druga
    pripelje pozneje in ustavi pred vrati. Zmagati mora druga.
    """
    # Odhodi so po 8:10, ker je do postajališča 80 s hoje -- avtobus ob 8:00
    # potnik ne ujame in test bi meril nekaj drugega, kot piše.
    _voznja(conn, "t1", "prej_dalec", [(1, "BLIZU", 8 * 3600 + 600),
                                       (2, "ROB", 8 * 3600 + 1200)])
    _voznja(conn, "t2", "pozneje_blizu", [(1, "BLIZU", 8 * 3600 + 660),
                                          (2, "CILJ", 8 * 3600 + 1500)])
    conn.commit()
    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    prvi = r["predlogi"][0]
    voznje = [n for n in prvi["noge"] if n["vrsta"] == "voznja"]
    assert [v["train_no"] for v in voznje] == ["pozneje_blizu"]


def test_pes_prestop_med_postajaliscema(conn):
    """"Izstopi tu, prehodi 200 m, vkrcaj se tam" — brez tega je pot brez izida."""
    _voznja(conn, "t1", "prva", [(1, "BLIZU", 8 * 3600 + 600),
                                 (2, "ROB", 8 * 3600 + 1200)])
    _voznja(conn, "t2", "druga", [(1, "CILJ", 8 * 3600 + 1800),
                                  (2, "ROB", 8 * 3600 + 2400)])
    conn.commit()
    # Brez peš poti se z ROB na CILJ ne pride: vožnja t2 pelje v napačno smer.
    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    prvi = r["predlogi"][0]
    assert [n["do"] for n in prvi["noge"] if n["vrsta"] == "voznja"] == ["Rob"]

    conn.execute("INSERT INTO pespot(a_stop, b_stop, sekunde) VALUES('ROB','CILJ',120)")
    conn.commit()
    hoja._PES_CACHE.clear()
    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    prvi = r["predlogi"][0]
    # Peš prestop in hoja do vrat sta zaporedni hoji in se zlijeta v eno.
    zadnja = prvi["noge"][-1]
    assert zadnja["vrsta"] == "hoja" and zadnja["od"] == "Rob"
    assert zadnja["sekunde"] == 120 + round(
        geo.haversine(46.099, 14.500, *DO) / hoja.HITROST_MS)


def test_max_nog_omeji_stevilo_vozenj(conn):
    """Krogi morajo res omejevati noge.

    Z eno samo tabelo najboljših prihodov jih niso: ko poznejši krog izboljša
    postajališče, se prepiše tudi njegov starš in veriga nazaj preskoči kroge.
    Na pravih podatkih je iskanje pri meji dveh nog vračalo pot s štirimi.
    """
    _voznja(conn, "t1", "a", [(1, "BLIZU", 8 * 3600 + 600),
                              (2, "DALEC", 8 * 3600 + 900)])
    _voznja(conn, "t2", "b", [(1, "DALEC", 8 * 3600 + 1500),
                              (2, "ROB", 8 * 3600 + 1800)])
    _voznja(conn, "t3", "c", [(1, "ROB", 8 * 3600 + 2400),
                              (2, "CILJ", 8 * 3600 + 2700)])
    conn.commit()
    izh, _, _ = pot.blizu(conn, OD[0], OD[1], {"BLIZU", "DALEC", "ROB", "CILJ"})
    cil, _, _ = pot.blizu(conn, DO[0], DO[1], {"BLIZU", "DALEC", "ROB", "CILJ"}, smer="do")
    for meja in (1, 2, 3):
        n = pot._isci_dan(conn, izh, cil, D, 8 * 3600, meja)
        if n is None:
            continue
        voznje = [x for x in n["noge"] if x[0] is not None]
        assert len(voznje) <= meja, f"{meja} nog, dobil {len(voznje)} voženj"


def test_hoja_vso_pot_je_predlog(conn):
    """Peš je včasih hitreje in stran tega ne sme zamolčati."""
    _voznja(conn, "t1", "pocasna", [(1, "BLIZU", 10 * 3600),
                                    (2, "CILJ", 11 * 3600)])
    conn.commit()
    blizu_cilj = (46.003, 14.500)      # ~330 m: štiri minute hoje
    r = pot.isci(conn, OD, blizu_cilj, D, 8 * 3600)
    prvi = r["predlogi"][0]
    assert [n["vrsta"] for n in prvi["noge"]] == ["hoja"]
    assert prvi["trajanje_s"] < 10 * 60


def test_brez_postajalisc_v_dosegu_ni_izmisljene_voznje(conn):
    """Postajališče, ki ta dan nič ne streže, ne sme priti v matriko hoje.

    Predlog vseeno je — hoja. Ta ni izmišljena, ampak edina resnica, ki jo
    imamo, in „ni poti" bi bil slabši odgovor od nje.
    """
    izh, _, _ = pot.blizu(conn, OD[0], OD[1], set())
    assert izh == {}
    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    assert all(n["vrsta"] == "hoja"
               for p in r["predlogi"] for n in p["noge"]), "vožnje ne sme biti"


def test_nicelna_hoja_ni_noga(conn):
    """Postajališče pred vrati ne sme roditi noge „peš 0 min"."""
    _postaja(conn, "PRAG", "Prag", OD[0], OD[1])
    _voznja(conn, "t1", "a", [(1, "PRAG", 8 * 3600), (2, "CILJ", 8 * 3600 + 600)])
    conn.commit()
    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    noge = r["predlogi"][0]["noge"]
    assert noge[0]["vrsta"] == "voznja"
    assert all(n["sekunde"] >= 60 for n in noge if n["vrsta"] == "hoja")


def test_ista_zamuda_kot_iskalnik_zvez(conn, monkeypatch):
    """Ista vožnja, isti postanek, dve strani — ena številka.

    Pravilo, katera zamuda velja in od kod je, je `stats.zamuda_na_postanku()`.
    Dokler je bilo napisano dvakrat, se je razlika pokazala na zaslonu: RG 318
    je v iskalniku pisal +11, v oknu iste vožnje pa +24.
    """
    from kajros import stats

    _voznja(conn, "t1", "LP 1", [(1, "BLIZU", 8 * 3600 + 600),
                                 (2, "CILJ", 8 * 3600 + 1200)], omrezje="zeleznica")
    # Vozilo je videno pred potnikovo postajo: zamuda na njegovem postanku je
    # torej OCENA, ne meritev -- in prav tam sta se poti razšli.
    conn.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_dep, "
                 "delay_arr, feed_ts) VALUES('t1', ?, 1, 240, 240, ?)",
                 (D, 4102444800))
    conn.commit()

    zveze = stats.connections(conn, "Blizu", "Cilj", D, now_s=8 * 3600 + 700)
    assert zveze, "iskalnik zvez mora najti to vožnjo"
    r = pot.isci(conn, OD, DO, D, 8 * 3600, now_s=8 * 3600 + 700)
    noga = next(n for n in r["predlogi"][0]["noge"] if n["vrsta"] == "voznja")
    assert noga["zamuda"]["s"] == zveze[0]["zamuda"]["s"]
    assert noga["zamuda"]["vrsta"] == zveze[0]["zamuda"]["vrsta"]


def test_prestop_uposteva_zamudo_obeh_vozenj(conn, monkeypatch):
    """Preostanek prestopa je načrtovani čas plus zamuda drugega minus prvega.

    Če zamuja tudi vozilo, na katero prestopaš, zveza morda vseeno drži — in
    to je natanko primer, ki potnika najbolj zanima.
    """
    _voznja(conn, "t1", "prva", [(1, "BLIZU", 8 * 3600 + 600),
                                 (2, "DALEC", 8 * 3600 + 900)])
    _voznja(conn, "t2", "druga", [(1, "DALEC", 8 * 3600 + 1500),
                                  (2, "CILJ", 8 * 3600 + 1800)])
    conn.commit()
    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    # Prvi je peš do Daleč in samo druga -- ob istem prihodu brez prestopa.
    p = next(p for p in r["predlogi"] if p["prestopov"] == 1)
    assert len(p["prestopi"]) == 1
    t = p["prestopi"][0]
    assert t["kje"] == "Daleč"
    assert t["nacrtovano_s"] == 600, "1500 - 900, brez hoje vmes"
    assert t["ostane_s"] is None, "brez meritev ni ocene, in tega ne izmišljamo"


def test_po_vseh_merilih_slabsi_predlog_odpade(conn):
    """Pot, ki odide prej, hodi dlje in pride ob isti minuti, ni izbira.

    Videno na zaslonu: Grosuplje → Zmajski most je ponudil 12:53 z 20 min hoje
    poleg 13:01 z 10 min, oba s prihodom 13:31. Vprašanje „z manj hoje" omejuje
    hojo na vsakem koncu posebej, ne v vsoti, in zna zato dati pot z več hoje.
    """
    _voznja(conn, "t1", "blizu", [(1, "BLIZU", 8 * 3600 + 900),
                                  (2, "CILJ", 8 * 3600 + 1800)])
    _voznja(conn, "t2", "dalec", [(1, "DALEC", 8 * 3600 + 840),
                                  (2, "CILJ", 8 * 3600 + 1800)])
    conn.commit()
    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    prihodi = [p["prihod"] for p in r["predlogi"]]
    assert len(prihodi) == len(set(prihodi)) or all(
        r["predlogi"][i]["hoje_s"] < r["predlogi"][i - 1]["hoje_s"]
        for i in range(1, len(r["predlogi"]))), (
        "dva predloga z istim prihodom smeta ostati le, če je poznejši boljši "
        "po kakem drugem merilu")


# ---------------------------------------------------------------- pot po korakih

def test_razberi_noge_prenese_dvopicje_v_id():
    """LPP-jev `trip_id` je trojni niz; ločnico beremo z desne, ne z leve."""
    assert pot.razberi_noge("a|b|c:3:9") == [("a|b|c", 3, 9)]
    assert pot.razberi_noge("x:y:1:2;t2:5:6") == [("x:y", 1, 2), ("t2", 5, 6)]
    with pytest.raises(ValueError):
        pot.razberi_noge("brez-stevilk")


def test_podrobnosti_sestavi_hojo_in_vmesne_postanke(conn, monkeypatch):
    """Podrobni prikaz doda dvoje, česar seznam nima: pešpot in postanke vmes."""
    monkeypatch.setattr(hoja, "pot",
                        lambda *a, **k: {"sekunde": 300, "metri": 400,
                                    "tocke": [[46.0, 14.5], [46.001, 14.5]]})
    _voznja(conn, "t1", "LP 1", [(1, "BLIZU", 8 * 3600 + 600),
                                 (2, "DALEC", 8 * 3600 + 900),
                                 (3, "ROB", 8 * 3600 + 1200),
                                 (4, "CILJ", 8 * 3600 + 1500)])
    conn.commit()
    r = pot.podrobnosti(conn, [("t1", 1, 4)], OD, DO, D)
    noge = r["predlog"]["noge"]
    assert [n["vrsta"] for n in noge] == ["hoja", "voznja", "hoja"]
    assert noge[0]["tocke"], "pešpot mora imeti geometrijo"
    assert noge[0]["metri"] == 400
    # Štirje postanki od vstopa do izstopa, torej dva vmes.
    assert len(noge[1]["postanki"]) == 4
    assert [s["ime"] for s in noge[1]["postanki"][1:-1]] == ["Daleč", "Rob"]


def test_podrobnosti_prestop_je_hoja_tudi_s_kolesom(conn, monkeypatch):
    """Kolo je samo na koncih, kot v seznamu: prestop pri 15 km/h bi bil
    trikrat krajši, pod minuto odpadel in podrobnosti bi kazale drugo uro."""
    monkeypatch.setattr(hoja, "pot",
                        lambda *a, **k: {"sekunde": 240, "metri": 330,
                                    "tocke": [[46.0, 14.5], [46.001, 14.5]]})
    _voznja(conn, "t1", "prva", [(1, "BLIZU", 8 * 3600 + 600),
                                 (2, "DALEC", 8 * 3600 + 900)])
    _voznja(conn, "t2", "druga", [(1, "ROB", 8 * 3600 + 1500),
                                  (2, "CILJ", 8 * 3600 + 1800)])
    conn.commit()
    r = pot.podrobnosti(conn, [("t1", 1, 2), ("t2", 1, 2)], OD, DO, D, kmh=15)
    noge = r["predlog"]["noge"]
    assert [n["vrsta"] for n in noge] == ["hoja", "voznja", "hoja", "voznja", "hoja"]
    assert noge[2]["sekunde"] == 240
    assert noge[0]["sekunde"] == hoja.pri_hitrosti(240, 15)


def test_podrobnosti_brez_geometrije_ne_klicejo_poti(conn, monkeypatch):
    """Osveževanje zamud med vodenjem ne rabi OSRM-ove poti s koraki."""
    def pot_ne(*a, **k):
        raise AssertionError("hoja.pot ne sme biti klican")
    monkeypatch.setattr(hoja, "pot", pot_ne)
    _voznja(conn, "t1", "LP 1", [(1, "DALEC", 8 * 3600 + 600),
                                 (2, "CILJ", 8 * 3600 + 1200)])
    conn.commit()
    r = pot.podrobnosti(conn, [("t1", 1, 2)], OD, DO, D, geometrija=False)
    hoje = [n for n in r["predlog"]["noge"] if n["vrsta"] == "hoja"]
    assert hoje and all(n["tocke"] is None and n["sekunde"] > 0 for n in hoje)


def test_podrobnosti_brez_usmerjevalnika_prizna_da_poti_ni(conn, monkeypatch):
    """Ravna črta na zemljevidu bi trdila pot, ki je ni."""
    monkeypatch.setattr(hoja, "pot", lambda *a, **k: None)
    _voznja(conn, "t1", "LP 1", [(1, "BLIZU", 8 * 3600 + 600),
                                 (2, "CILJ", 8 * 3600 + 1200)])
    conn.commit()
    r = pot.podrobnosti(conn, [("t1", 1, 2)], OD, DO, D)
    hoje = [n for n in r["predlog"]["noge"] if n["vrsta"] == "hoja"]
    assert hoje and all(n["tocke"] is None for n in hoje)


def test_podrobnosti_neobstojeca_voznja_pade(conn):
    """Vozni red se med iskanjem in klikom lahko zamenja; deljena povezava od
    včeraj torej ni napaka odjemalca, a tudi ne sme tiho vrniti prazne poti."""
    with pytest.raises(KeyError):
        pot.podrobnosti(conn, [("ni-me", 1, 2)], OD, DO, D)


def test_voznja_z_vec_hoje_kot_pes_vso_pot_ni_predlog(conn, monkeypatch):
    """Pot z vozilom, v kateri je hoje več, kot bi je bilo peš, je ovinek.

    Videno na zaslonu: vlak stran od cilja in nato 8,8 km peš nazaj — dve uri
    za pot, ki jo prehodiš v pol ure.
    """
    # Peš vso pot 20 minut; vožnja pa zahteva 13 + 13 = 26 minut hoje.
    monkeypatch.setattr(hoja, "sekunde", lambda *a, **k: (20 * 60, hoja.OSRM))
    _voznja(conn, "t1", "ovinek", [(1, "DALEC", 8 * 3600 + 900),
                                   (2, "ROB", 8 * 3600 + 1200)])
    conn.commit()
    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    for p in r["predlogi"]:
        if any(n["vrsta"] == "voznja" for n in p["noge"]):
            assert p["hoje_s"] < 20 * 60, "vožnja z več hoje od same hoje"


def test_ko_ni_poti_pove_koliko_je_pes(conn, monkeypatch):
    """„Ni poti" je slabši odgovor od resnice „peš uro in pol"."""
    monkeypatch.setattr(hoja, "sekunde", lambda *a, **k: (90 * 60, hoja.OSRM))
    r = pot.isci(conn, OD, DO, D, 8 * 3600)      # v bazi ni nobene vožnje
    assert len(r["predlogi"]) == 1
    p = r["predlogi"][0]
    assert p.get("edina") is True
    assert p["hoje_s"] == 90 * 60


def test_nasvet_pove_koliko_hoje_bi_bilo_treba(conn, monkeypatch):
    """„Ni poti" brez nadaljevanja je slep konec.

    Meja hoje velja **do postaje**; kadar je prvo uporabno postajališče tik čez
    njo, je to ugotovitev in ne ugibanje. Da bi s tem pot res nastala, pa ne
    obljubljamo — postajališče v dosegu še ni zveza.
    """
    _voznja(conn, "t1", "a", [(1, "BLIZU", 8 * 3600 + 900),
                              (2, "CILJ", 8 * 3600 + 1500)])
    conn.commit()
    # Cilj je 556 m od postajališča "Cilj", torej 6,7 min hoje. Z mejo petih
    # minut ga ni v dosegu -- in prav to mora stran povedati s številko.
    dalje = (46.104, 14.500)
    r = pot.isci(conn, OD, dalje, D, 8 * 3600, max_hoje_s=5 * 60)
    assert r["ciljev"] == 0
    assert r["nasvet"] and r["nasvet"]["vec_hoje_min"] == 7


def test_brez_podatka_ni_isto_kot_tocno(conn):
    """Vožnja brez vsake besede iz feeda nosi `brez_podatka`, izmerjena ne.

    22. 9. 2026 je 25, ki je zamujal 20 minut, stal v predlogu brez žetona --
    feed zanj ni prišel do nas, zaslon pa je bil videti kot „po voznem redu".
    Za drug dan (brez `now_s`) podatka v živo ne more biti, zato molk.
    """
    _voznja(conn, "t1", "LPP 25", [(1, "BLIZU", 8 * 3600 + 600),
                                   (2, "CILJ", 8 * 3600 + 1200)])
    conn.commit()
    r = pot.isci(conn, OD, DO, D, 8 * 3600, now_s=8 * 3600 + 300)
    noga = next(n for n in r["predlogi"][0]["noge"] if n["vrsta"] == "voznja")
    assert noga["zamuda"] is None and noga["brez_podatka"] is True

    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    noga = next(n for n in r["predlogi"][0]["noge"] if n["vrsta"] == "voznja")
    assert noga["brez_podatka"] is False

    # Uro pred odhodom podatka še ne more biti -- beseda bi bila šum.
    r = pot.isci(conn, OD, DO, D, 7 * 3600, now_s=7 * 3600)
    noga = next(n for n in r["predlogi"][0]["noge"] if n["vrsta"] == "voznja")
    assert noga["brez_podatka"] is False

    conn.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_dep, "
                 "delay_arr, feed_ts) VALUES('t1', ?, 1, 240, 240, ?)", (D, 4102444800))
    conn.commit()
    r = pot.isci(conn, OD, DO, D, 8 * 3600, now_s=8 * 3600 + 700)
    noga = next(n for n in r["predlogi"][0]["noge"] if n["vrsta"] == "voznja")
    assert noga["zamuda"] is not None and noga["brez_podatka"] is False


# ---------------------------------------------------------------- biti tam do

def test_nazaj_da_najpoznejsi_odhod_za_rok(conn):
    """„Moram biti tam ob 8:45" -- prvi predlog je tisti, s katerim od doma
    odideš najpozneje, ne tisti, s katerim si najprej tam."""
    _voznja(conn, "t1", "zgodnji", [(1, "BLIZU", 8 * 3600 + 600),
                                    (2, "CILJ", 8 * 3600 + 1500)])
    _voznja(conn, "t2", "pravi", [(1, "BLIZU", 8 * 3600 + 1200),
                                  (2, "CILJ", 8 * 3600 + 2400)])
    _voznja(conn, "t3", "prepozni", [(1, "BLIZU", 8 * 3600 + 1800),
                                     (2, "CILJ", 8 * 3600 + 3300)])
    conn.commit()
    r = pot.isci(conn, OD, DO, D, None, prihod_do_s=8 * 3600 + 2700)
    voznje = [[n["train_no"] for n in p["noge"] if n["vrsta"] == "voznja"]
              for p in r["predlogi"]]
    assert voznje[0] == ["pravi"]
    assert ["prepozni"] not in voznje
    assert ["zgodnji"] in voznje, "prejšnja zveza je izbira z več rezerve"
    assert r["prihod_do"] == stats.polnoc(D) + 8 * 3600 + 2700
    assert all(p["prihod"] <= r["prihod_do"] for p in r["predlogi"])


def test_cim_prej_ne_caka_na_prestopu_namesto_doma(conn):
    """Dva avtobusa ujameta isti vlak: prvi predlog vzame poznejšega.

    Iskanje naprej se vkrca na prvo vožnjo, ki jo ujame, in je razliko
    prečakalo na prestopu. Sporočilo potnika 30. 9. 2026: „uro za prestope".
    """
    _postaja(conn, "VMES", "Vmes", 46.050, 14.500)     # 5,5 km od obeh koncev
    _voznja(conn, "t1", "zgodnji", [(1, "BLIZU", 8 * 3600 + 600),
                                    (2, "VMES", 8 * 3600 + 1200)])
    _voznja(conn, "t2", "pozni", [(1, "BLIZU", 8 * 3600 + 3000),
                                  (2, "VMES", 8 * 3600 + 3600)])
    _voznja(conn, "t3", "vlak", [(1, "VMES", 9 * 3600 + 1200),
                                 (2, "CILJ", 9 * 3600 + 3000)], "zeleznica")
    conn.commit()
    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    prvi = r["predlogi"][0]
    assert [n["train_no"] for n in prvi["noge"] if n["vrsta"] == "voznja"] == ["pozni", "vlak"]
    assert prvi["prestopi"][0]["nacrtovano_s"] == 20 * 60


def _vmes_in_direkt(conn, pozni_odhod_s):
    """Direkten avtobus ob 8:10 in avtobus + vlak prek VMES; oba na cilju ob 10:00."""
    _postaja(conn, "VMES", "Vmes", 46.050, 14.500)
    _voznja(conn, "t1", "direkt", [(1, "BLIZU", 8 * 3600 + 600),
                                   (2, "CILJ", 10 * 3600)])
    _voznja(conn, "t2", "pozni", [(1, "BLIZU", pozni_odhod_s),
                                  (2, "VMES", 9 * 3600 + 1800)])
    _voznja(conn, "t3", "vlak", [(1, "VMES", 9 * 3600 + 2400),
                                 (2, "CILJ", 10 * 3600)], "zeleznica")
    conn.commit()


def test_cim_prej_prestop_vec_za_uro_doma(conn):
    """Ob isti uri prihoda je prvi predlog tisti, s katerim odideš uro pozneje,
    čeprav ima prestop več (30. 9. 2026: 05:44 namesto 11:43, prihod isti)."""
    _vmes_in_direkt(conn, 9 * 3600 + 1200)
    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    voznje = [[n["train_no"] for n in p["noge"] if n["vrsta"] == "voznja"]
              for p in r["predlogi"]]
    assert voznje[0] == ["pozni", "vlak"]
    assert ["direkt"] in voznje, "pot brez prestopa ostane izbira"


def test_cim_prej_prestop_vec_ni_vreden_minute(conn):
    """Prestop več za dve minuti doma ni boljša pot."""
    _vmes_in_direkt(conn, 8 * 3600 + 720)
    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    prvi = r["predlogi"][0]
    assert [n["train_no"] for n in prvi["noge"] if n["vrsta"] == "voznja"] == ["direkt"]


def test_zvecer_brez_zveze_ponudi_jutrisnje(conn):
    """Ob 22:00 danes ne pelje nič več: odgovor je prva zveza jutri, ne "ni poti"."""
    conn.execute("INSERT OR IGNORE INTO service_day(service_id, date) VALUES('S1', '2026-09-09')")
    _voznja(conn, "t1", "jutranji", [(1, "BLIZU", 8 * 3600 + 600),
                                     (2, "CILJ", 8 * 3600 + 1500)])
    conn.commit()
    r = pot.isci(conn, OD, DO, D, 22 * 3600)
    assert r["danes_ni"] is True and r["datum"] == "2026-09-09"
    prvi = r["predlogi"][0]
    assert prvi["datum"] == "2026-09-09"
    assert prvi["odhod"] > stats.polnoc("2026-09-09")
    assert [n["train_no"] for n in prvi["noge"] if n["vrsta"] == "voznja"] == ["jutranji"]

    r = pot.isci(conn, OD, DO, D, 22 * 3600, jutri=False)
    assert "danes_ni" not in r and r["nasvet"] == {"ni_zveze": True}


def test_tam_do_ne_caka_na_prestopu_namesto_na_cilju(conn):
    """Isti odhod od doma, dva vlaka naprej: prvi predlog vzame zgodnejšega.

    Obratno iskanje je izbralo zadnji vlak, ki še ujame rok, in potnik bi
    uro čakal na prestopu namesto biti uro prej na cilju.
    """
    _postaja(conn, "VMES", "Vmes", 46.050, 14.500)     # 5,5 km od obeh koncev
    _voznja(conn, "t1", "avtobus", [(1, "BLIZU", 8 * 3600 + 600),
                                    (2, "VMES", 8 * 3600 + 1200)])
    _voznja(conn, "t2", "zgodnji", [(1, "VMES", 8 * 3600 + 1800),
                                    (2, "CILJ", 9 * 3600)], "zeleznica")
    _voznja(conn, "t3", "pozni", [(1, "VMES", 9 * 3600 + 1800),
                                  (2, "CILJ", 10 * 3600)], "zeleznica")
    conn.commit()
    r = pot.isci(conn, OD, DO, D, None, prihod_do_s=10 * 3600 + 300)
    prvi = r["predlogi"][0]
    assert [n["train_no"] for n in prvi["noge"] if n["vrsta"] == "voznja"] == ["avtobus", "zgodnji"]


def test_nazaj_prag_prestopa_samo_ob_prihodu_z_vozilom(conn):
    """Prag za prestop velja, kadar na postajališče pripelješ, ne kadar
    prideš peš od doma -- isto kot prvi krog iskanja naprej."""
    # Avtobus z BLIZU pripelje na DALEC dve minuti pred drugim: premalo za
    # avtobusni prag treh minut. Peš do DALEC (13 min) pa ga ujameš.
    _voznja(conn, "t1", "dovoz", [(1, "BLIZU", 8 * 3600 + 300),
                                  (2, "DALEC", 8 * 3600 + 1200)])
    _voznja(conn, "t2", "naprej", [(1, "DALEC", 8 * 3600 + 1320),
                                   (2, "CILJ", 8 * 3600 + 2400)])
    conn.commit()
    r = pot.isci(conn, OD, DO, D, None, prihod_do_s=8 * 3600 + 2700)
    for p in r["predlogi"]:
        voznje = [n["train_no"] for n in p["noge"] if n["vrsta"] == "voznja"]
        assert voznje != ["dovoz", "naprej"], "prestop dveh minut ni prestop"
    prvi = r["predlogi"][0]
    assert [n["train_no"] for n in prvi["noge"] if n["vrsta"] == "voznja"] == ["naprej"]
    assert prvi["noge"][0]["vrsta"] == "hoja" and prvi["noge"][0]["do"] == "Daleč"


def test_nazaj_ne_ponudi_odhoda_pred_zdaj(conn):
    """Za danes je najzgodnejši odhod zdaj: pot, ki bi odšla pred petimi
    minutami, ni odgovor na „kdaj moram od doma"."""
    _voznja(conn, "t1", "odpeljal", [(1, "BLIZU", 8 * 3600 + 600),
                                     (2, "CILJ", 8 * 3600 + 1500)])
    _voznja(conn, "t2", "se_ujames", [(1, "BLIZU", 8 * 3600 + 1200),
                                      (2, "CILJ", 8 * 3600 + 2400)])
    conn.commit()
    zdaj = 8 * 3600 + 900
    r = pot.isci(conn, OD, DO, D, zdaj, now_s=zdaj, prihod_do_s=9 * 3600)
    voznje = [n["train_no"] for p in r["predlogi"] for n in p["noge"]
              if n["vrsta"] == "voznja"]
    assert voznje == ["se_ujames"]
    assert all(p["odhod"] >= stats.polnoc(D) + zdaj for p in r["predlogi"])


def test_nazaj_se_ujema_z_iskanjem_naprej(conn):
    """Naprej od T da prihod A; nazaj z rokom A mora dati odhod, ki ni prej
    od odhoda naprej, in priti do A. Dve smeri istega postopka se ne smeta
    razhajati."""
    _voznja(conn, "t1", "a", [(1, "BLIZU", 8 * 3600 + 600),
                              (2, "DALEC", 8 * 3600 + 900)])
    _voznja(conn, "t2", "b", [(1, "DALEC", 8 * 3600 + 1500),
                              (2, "ROB", 8 * 3600 + 1800)])
    _voznja(conn, "t3", "c", [(1, "ROB", 8 * 3600 + 2400),
                              (2, "CILJ", 8 * 3600 + 2700)])
    _voznja(conn, "t4", "d", [(1, "DALEC", 8 * 3600 + 1560),
                              (2, "CILJ", 8 * 3600 + 3000)])
    conn.commit()
    polnoc = stats.polnoc(D)
    for t0 in (7 * 3600 + 3000, 8 * 3600, 8 * 3600 + 300):
        naprej = pot.isci(conn, OD, DO, D, t0)
        prvi = next(p for p in naprej["predlogi"]
                    if any(n["vrsta"] == "voznja" for n in p["noge"]))
        nazaj = pot.isci(conn, OD, DO, D, None, prihod_do_s=prvi["prihod"] - polnoc)
        z = nazaj["predlogi"][0]
        assert z["odhod"] >= prvi["odhod"]
        assert z["prihod"] <= prvi["prihod"]


def test_rok_ki_ga_ne_ujames_pove_kdaj_si_tam_najprej(conn):
    """Do roka ne gre več: odgovor ni „ni poti", ampak najhitrejša pot od
    zdaj in beseda, da je prepozno. Pot je -- samo prepozna."""
    _voznja(conn, "t1", "odpeljal", [(1, "BLIZU", 8 * 3600 + 600),
                                     (2, "CILJ", 8 * 3600 + 1500)])
    _voznja(conn, "t2", "naslednji", [(1, "BLIZU", 9 * 3600),
                                      (2, "CILJ", 9 * 3600 + 900)])
    conn.commit()
    zdaj = 8 * 3600 + 900
    r = pot.isci_do(conn, OD, DO, D, 8 * 3600 + 1800, zdaj)
    assert r["ne_ujames"] is True
    assert r["prihod_do"] == stats.polnoc(D) + 8 * 3600 + 1800
    assert [n["train_no"] for n in r["predlogi"][0]["noge"]
            if n["vrsta"] == "voznja"] == ["naslednji"]

    # Za drug dan "zdaj" ni meja: rok velja, kakor je.
    r = pot.isci_do(conn, OD, DO, D, 8 * 3600 + 1800, None)
    assert not r.get("ne_ujames")
    assert [n["train_no"] for n in r["predlogi"][0]["noge"]
            if n["vrsta"] == "voznja"] == ["odpeljal"]


def test_nazaj_meja_velja_za_odhod_od_doma_ne_s_postajalisca(conn):
    """Vozilo odpelje s postajališča po zdaj, a do tja je 13 minut hoje:
    odhod od doma bi bil pred zdaj. To ni zveza, ampak `ne_ujames`."""
    _voznja(conn, "t1", "odpelje_po_zdaj", [(1, "DALEC", 8 * 3600 + 1200),
                                            (2, "CILJ", 8 * 3600 + 2100)])
    _voznja(conn, "t2", "naslednji", [(1, "DALEC", 9 * 3600),
                                      (2, "CILJ", 9 * 3600 + 900)])
    conn.commit()
    zdaj = 8 * 3600 + 900
    r = pot.isci_do(conn, OD, DO, D, 8 * 3600 + 2400, zdaj)
    assert r["ne_ujames"] is True
    assert all(p["odhod"] >= stats.polnoc(D) + zdaj for p in r["predlogi"])


# ---------------------------------------------------------------- kolo

def test_kolo_doseze_dlje_in_hitreje(conn):
    """S 15 km/h je postajališče 4 km stran v dosegu, ki ga peš ni, in pot
    do bližnjega traja tretjino časa."""
    _postaja(conn, "DALJE", "Dalje", 46.036, 14.500)      # 4 km: 48 min peš
    _voznja(conn, "t1", "a", [(1, "DALJE", 8 * 3600 + 1800),
                              (2, "CILJ", 8 * 3600 + 2400)])
    _voznja(conn, "t2", "b", [(1, "DALEC", 8 * 3600 + 1800),
                              (2, "CILJ", 8 * 3600 + 2400)])
    conn.commit()
    streze = {"DALJE", "DALEC", "CILJ"}
    pes, _, _ = pot.blizu(conn, OD[0], OD[1], streze)
    kolo, _, _ = pot.blizu(conn, OD[0], OD[1], streze, kmh=hoja.KOLO_KMH)
    assert "DALJE" not in pes and "DALJE" in kolo
    assert kolo["DALEC"] == pytest.approx(pes["DALEC"] / 3, abs=1)


def test_kolo_meri_eno_postajalisce_na_ime(conn, monkeypatch):
    """Pri kolesu je kandidatov devetkrat več; istoimenska postajališča na
    dveh straneh ceste dobijo en izmerjen čas in razliko po zraku."""
    _postaja(conn, "DALEC2", "Daleč", 46.0102, 14.5003)   # druga stran ceste
    merjeni = []
    stara = hoja.matrika

    def matrika(lat, lon, cilji, smer="od"):
        merjeni.extend(cilji)
        return stara(lat, lon, cilji, smer)
    monkeypatch.setattr(pot.hoja, "matrika", matrika)
    streze = {"DALEC", "DALEC2"}
    kolo, _, _ = pot.blizu(conn, OD[0], OD[1], streze, kmh=hoja.KOLO_KMH)
    assert len(merjeni) == 1
    assert set(kolo) == {"DALEC", "DALEC2"}
    assert abs(kolo["DALEC2"] - kolo["DALEC"]) <= 10


# ---------------------------------------------------------------- naslednji odhodi

def test_naslednji_odhod_v_casu_hoje_ni_preskocen(conn):
    """Naslednji odhod se išče od doma minuto pozneje, ne minuto po vstopu.

    Prej je iskanje začelo ob uri vstopa in preskočilo vse, kar odpelje v času
    hoje do postaje. Na pravih podatkih (Vič -> Fužine, 23. 9. 2026) je tako
    izpadel 47 ob 14:19; na seznam je prišel samo po naključju, prek „druge
    poti", ki pa najde le enega. Tu sta dva zapored in drugi mora ostati.
    """
    for i, (ime, t) in enumerate((("prvi", 600), ("drugi", 660),
                                  ("tretji", 720), ("pozni", 1800))):
        _voznja(conn, f"t{i}", ime, [(1, "BLIZU", 8 * 3600 + t),
                                     (2, "CILJ", 8 * 3600 + t + 600)])
    conn.commit()
    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    voznje = [n["train_no"] for p in r["predlogi"] for n in p["noge"]
              if n["vrsta"] == "voznja"]
    assert voznje[:3] == ["prvi", "drugi", "tretji"], voznje


def test_naslednji_odhod_ni_ista_voznja_z_zamudo(conn, monkeypatch):
    """Vožnja, ki zamuja več kot hoja do postaje, ni svoj naslednji odhod.

    Iskanje od poznejše ure jo je našlo znova, dvojnik je izpadel in
    naslednjih odhodov ni bilo -- stran je ponudila en sam avtobus.
    """
    monkeypatch.setattr(pot, "zamiki", lambda *a: {"t0": 600})
    for i, t in enumerate((600, 1800, 3000)):
        _voznja(conn, f"t{i}", f"v{i}", [(1, "BLIZU", 8 * 3600 + t),
                                         (2, "CILJ", 8 * 3600 + t + 600)])
    conn.commit()
    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    voznje = [n["train_no"] for p in r["predlogi"] for n in p["noge"]
              if n["vrsta"] == "voznja"]
    assert voznje == ["v0", "v1", "v2"], voznje


# ---------------------------------------------------------------- nočni avtobus

DV = "2026-09-07"          # dan pred D


def test_nocna_voznja_je_iz_vcerajsnjega_dne_in_to_pove(conn):
    """Ob 00:05 vozi avtobus, ki nosi včerajšnji prometni dan (`dep_s` čez 86 400).

    Predlog mora nositi SVOJ dan: podrobnosti so ga prej iskale po dnevu
    vprašanja in pokazale jutrišnjo vožnjo ob isti uri (izmerjeno: vožnja
    453052, predlog 23. 9. ob 00:05, podrobnosti 24. 9. ob 00:05).
    """
    conn.execute("INSERT INTO service_day(service_id, date) VALUES('S1', ?)", (DV,))
    _voznja(conn, "noc", "N1", [(1, "BLIZU", 86400 + 300), (2, "CILJ", 86400 + 900)])
    conn.commit()
    r = pot.isci(conn, OD, DO, D, 0)
    p = next(p for p in r["predlogi"] if any(n["vrsta"] == "voznja" for n in p["noge"]))
    assert p["datum"] == DV and r["datum"] == D
    noga = next(n for n in p["noge"] if n["vrsta"] == "voznja")
    assert noga["odhod"] == stats.polnoc(D) + 300, "ob 00:05 danes, ne jutri"

    # Ista vožnja danes pelje šele jutri ob 00:05; podrobnosti po dnevu
    # predloga dajo pravo uro.
    d = pot.podrobnosti(conn, [("noc", 1, 2)], OD, DO, p["datum"])
    assert d["predlog"]["noge"][1]["odhod"] == noga["odhod"]


def test_nocno_iskanje_ne_podvoji_hoje(conn):
    """Hoja vso pot je ena, ne ena na prometni dan.

    Ko sta se predloga dveh dni zlila v `api.py`, sta bili na seznamu dve
    enaki „00:30 -> 01:00 peš" (izmerjeno 23. 9. 2026).
    """
    conn.execute("INSERT INTO service_day(service_id, date) VALUES('S1', ?)", (DV,))
    conn.commit()
    blizu_cilj = (46.003, 14.500)
    r = pot.isci(conn, OD, blizu_cilj, D, 30 * 60)
    assert len(r["predlogi"]) == 1


def test_podnevi_vcerajsnjega_dne_ne_iscemo(conn):
    """Drugo iskanje je cel krog čez vozni red, zato samo pred `NOCNI_S`."""
    conn.execute("INSERT INTO service_day(service_id, date) VALUES('S1', ?)", (DV,))
    _voznja(conn, "noc", "N1", [(1, "BLIZU", 86400 + 8 * 3600 + 300),
                                (2, "CILJ", 86400 + 8 * 3600 + 900)])
    conn.commit()
    # Brez jutrišnjega iskanja: vožnja ob 32:05 dne D je jutri ob 8:05 in jo
    # tisto (upravičeno) najde.
    r = pot.isci(conn, OD, DO, D, 8 * 3600, jutri=False)
    assert not any(n["vrsta"] == "voznja" for p in r["predlogi"] for n in p["noge"])


def test_podrobnosti_povedo_ali_je_pot_ziva(conn, monkeypatch):
    """Odštevanje in osveževanje zamud sta za pot, ki je zdaj -- to pove
    strežnik, ne sklepa ga stran iz „dan je danes"."""
    monkeypatch.setattr(hoja, "pot", lambda *a, **k: None)
    _voznja(conn, "t1", "a", [(1, "BLIZU", 8 * 3600 + 600), (2, "CILJ", 8 * 3600 + 1200)])
    conn.commit()
    assert pot.podrobnosti(conn, [("t1", 1, 2)], OD, DO, D, now_s=8 * 3600)["zivo"] is True
    assert pot.podrobnosti(conn, [("t1", 1, 2)], OD, DO, D)["zivo"] is False


def test_predpomnilnik_hrani_dva_dneva_brez_praznjenja():
    """Ponoči se iskanje izmenjuje med danes in včeraj. Z enim mestom je vsako
    drugemu izpraznilo predpomnilnik, `clear()` med `in` in `[]` v drugi niti
    pa je bil KeyError."""
    c: dict = {}
    for k in ("a", "b", "c"):
        pot._shrani(c, k, k.upper())
    assert c == {"b": "B", "c": "C"}
    pot._shrani(c, "c", "C2")
    assert c == {"b": "B", "c": "C2"}
