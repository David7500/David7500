"""Enotni testi čistih funkcij.

Namenoma brez omrežja in brez baze na disku: vse, kar se da preveriti brez
zajema, naj se preveri hitro. Poizvedbe nad shemo so v `test_poizvedbe.py`.

    ./venv/bin/python -m pytest tests/ -q
"""
from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from kajros import journey, ocena, stats, weather
from kajros.alerts import parse_delay_text
from kajros.collector import (_delay_of, is_forecast, is_zero_blip,
                               resolve_service_date, worth_logging)
from kajros.journey import _fold


# ---------------------------------------------------------------- prehodne nicle

def _row(arr, dep=None):
    """Posnema sqlite3.Row: dostop po imenu stolpca."""
    return {"delay_arr": arr, "delay_dep": dep if dep is not None else arr}


def test_nicla_po_veliki_zamudi_je_sumljiva():
    # 20 minut zamude, cez pol minute tocno -- fizikalno nemogoce.
    assert is_zero_blip(_row(1200), _row(1200), 0, 0)


def test_nicla_po_majhni_zamudi_ni_sumljiva():
    # Dve minuti zamude, ki izgineta, so vsakdanji dogodek.
    assert not is_zero_blip(_row(120), _row(120), 0, 0)


def test_potrjena_nicla_se_sprejme():
    # Ce je ze prejsnji zapis v dnevniku govoril niclo, to ni blip, ampak
    # potrditev -- sicer bi `run` obtical na stari vrednosti za vedno.
    assert not is_zero_blip(_row(1200), _row(0), 0, 0)


def test_brez_prejsnje_vrednosti_ni_blipa():
    assert not is_zero_blip(None, None, 0, 0)


def test_nenicelna_vrednost_ni_blip():
    assert not is_zero_blip(_row(1200), _row(1200), 60, 60)


def test_obe_vrednosti_prazni_nista_blip():
    # Manjkajoc podatek ni isto kot porocana nicla.
    assert not is_zero_blip(_row(1200), _row(1200), None, None)


# ---------------------------------------------------------------- besedilo obvestil

def test_razclenitev_navadne_zamude():
    got = parse_delay_text("Vlak LPV 2616 ima zamudo 5 min ob prihodu na postajo Postojna.")
    assert got == {"train_no": "LPV 2616", "delay_min": 5, "station": "Postojna",
                   "severe": False, "event": "prihod"}


def test_razclenitev_izjemne_zamude():
    got = parse_delay_text(
        "Vlak LP 3224 ima izjemno zamudo 42 min ob prihodu na postajo Ljubljana Rakovnik.")
    assert got["severe"] is True
    assert got["station"] == "Ljubljana Rakovnik"      # vecbesedno ime
    assert got["delay_min"] == 42


def test_razclenitev_brez_koncne_pike():
    got = parse_delay_text("Vlak RG 1604 ima zamudo 8 min ob prihodu na postajo Zagorje")
    assert got is not None and got["station"] == "Zagorje"


def test_neznana_oblika_vrne_none():
    # Tiho ugibanje bi bilo slabse od priznanja, da oblike ne poznamo.
    assert parse_delay_text("Vlak vozi po nadomestni progi.") is None
    assert parse_delay_text("") is None


# ---------------------------------------------------------------- iskanje postaj

def test_zlozitev_odstrani_sumnike():
    assert _fold("Šentjur") == "sentjur"
    assert _fold("Bohinjska Bistrica") == "bohinjska bistrica"
    assert _fold("Ljubljana Črnuče") == "ljubljana crnuce"


# ---------------------------------------------------------------- stopnja razmer

def test_mirno_vreme_je_nic():
    s = weather.severity({"temp_c": 18.0, "precip_mm": 0.0, "snowfall_cm": 0.0,
                          "wind_gust_kmh": 10.0, "code": 0})
    assert s["score"] == 0 and s["label"] == "mirne"


def test_sneg_in_mraz_se_sestejeta():
    s = weather.severity({"temp_c": -8.0, "precip_mm": 0.0, "snowfall_cm": 3.5,
                          "wind_gust_kmh": 10.0, "code": 73})
    assert {p["what"] for p in s["parts"]} == {"sneg", "mraz"}
    assert s["score"] == 9 and s["label"] == "hude"


def test_stopnja_je_omejena_na_deset():
    s = weather.severity({"temp_c": -10.0, "precip_mm": 30.0, "snowfall_cm": 10.0,
                          "wind_gust_kmh": 120.0, "code": 95})
    assert s["score"] == 10


def test_barva_sledi_stopnji():
    # Semafor mora biti monoton: vsaka stopnja svoja barva, brez preskokov.
    seen = [weather.severity_color(n) for n in (0, 2, 5, 9)]
    assert seen == [weather.SEVERITY_STYLE[k] for k in weather.SEVERITY_ORDER]


# ---------------------------------------------------------------- prag dnevnika

def test_prva_vrednost_gre_vedno_v_dnevnik():
    assert worth_logging(None, 120, 120)


def test_drobna_sprememba_ni_vredna_vrstice():
    # Prikaz ima locljivost ene minute; 15 sekund ni sprememba, ampak sum.
    assert not worth_logging(_row(120), 135, 135)


def test_velika_sprememba_gre_v_dnevnik():
    assert worth_logging(_row(120), 200, 200)


def test_lezenje_se_sesteva():
    """Primerjamo z ZADNJO ZAPISANO vrednostjo, ne s prejšnjo prebrano.

    Sicer bi zamuda, ki raste po petnajst sekund, rasla v neskončnost in v
    dnevniku ne bi bilo nikoli nič -- vsak korak zase je premajhen.
    """
    logged = _row(120)
    for value in (135, 150, 165):
        assert not worth_logging(logged, value, value)
    assert worth_logging(logged, 180, 180)      # 60 s od zapisane


def test_pojav_in_izginotje_vrednosti_sta_sprememba():
    assert worth_logging(_row(120), None, None)
    assert worth_logging({"delay_arr": None, "delay_dep": None}, 10, 10)


# ---------------------------------------------------------------- manjkajoca zamuda

def _stu(seq, *, arr_delay=None, arr_time=None, dep_delay=None):
    """Zgradi `stop_time_update`, kakršnega pošlje feed."""
    from google.transit import gtfs_realtime_pb2
    s = gtfs_realtime_pb2.TripUpdate.StopTimeUpdate()
    s.stop_sequence = seq
    if arr_delay is not None:
        s.arrival.delay = arr_delay
    if arr_time is not None:
        s.arrival.time = arr_time
    if dep_delay is not None:
        s.departure.delay = dep_delay
    return s


def test_manjkajoca_zamuda_ni_nicla():
    """Protobuf za neizpolnjeno polje vrne 0 — to ni „točno", ampak „ne vem".

    Izmerjeno na živem feedu: `arrival` ima `delay` pri vlakih v 100 %
    primerov, pri avtobusih pa le v 31–61 %. Zajem je ostalo pisal kot ničlo
    in delež točnih avtobusov je zaradi tega bral 84,3 % namesto 71,2 %.
    """
    prazen = _stu(3)                       # `arrival` sploh ni
    assert _delay_of(prazen, "arrival", (36000, 36060), "2026-08-31") is None


def test_zamuda_se_izracuna_iz_absolutnega_casa():
    """Kadar feed da čas namesto zamude, je zamuda razlika — to je meritev.

    Preverjeno na živem feedu proti poročani odhodni zamudi istega postanka:
    mediana razlike −9 s, 87 % v eni minuti. Negativna je pravilno — vozilo
    na postanku izgubi nekaj časa.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo
    tz = ZoneInfo("Europe/Ljubljana")
    polnoc = datetime(2026, 8, 31, tzinfo=tz).timestamp()
    # Voznoredni prihod ob 10:00 (36000 s), dejanski ob 10:07.
    s = _stu(3, arr_time=int(polnoc + 36000 + 420))
    assert _delay_of(s, "arrival", (36000, 36060), "2026-08-31") == 420


def test_porocana_zamuda_ima_prednost_pred_izracunano():
    # Ce feed zamudo pove, je to njegova beseda in ne ugibamo iz casa.
    s = _stu(3, arr_delay=120, arr_time=999999999)
    assert _delay_of(s, "arrival", (36000, 36060), "2026-08-31") == 120


def test_nicla_ostane_nicla_kadar_jo_feed_res_pove():
    # Vlaki posljejo `delay = 0` in to POMENI tocno -- tega ne smemo zavreci.
    s = _stu(3, arr_delay=0)
    assert _delay_of(s, "arrival", (36000, 36060), "2026-08-31") == 0


# ---------------------------------------------------------------- tekoca ura

def _at(h, m, s=0):
    """Absolutni cas 30. 8. 2026 ob dani uri."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    return datetime(2026, 8, 30, h, m, s, tzinfo=ZoneInfo("Europe/Ljubljana")).timestamp()


DAN = "2026-08-30"
RED = (44220, 44220)        # voznoredni prihod in odhod ob 12:17


def test_ura_za_prevozen_postanek_se_zavrne():
    """Vzorec, ujet v zivo na LPP 25 (Poliklinika, 30. 8.).

    Ob 12:19:36 je feed porocal +126 s -- vozilo je bilo torej ob 12:19:06
    mimo. Ob 12:23:48 je objavil +482 s, kar bi postanek prestavilo na
    12:25:02, torej v prihodnost. To ni popravek meritve, ampak `zdaj -
    vozni red`: naslednjih sedem klicev je vrednost rasla natanko za 60 s
    na 60 s do +842 (+14 min).
    """
    from kajros.collector import undoes_passing
    assert undoes_passing(_row(58, 126), RED, DAN, 482, 482, _at(12, 23, 48))


def test_ura_ostane_zavrnjena_ves_cas_rasti():
    # `prev` ostane zadnja SPREJETA vrednost, zato mora varovalka drzati
    # skozi vse zaporedje in ne le pri prvem skoku.
    from kajros.collector import undoes_passing
    for minuta, vrednost in ((24, 542), (25, 602), (29, 842)):
        assert undoes_passing(_row(58, 126), RED, DAN, vrednost, vrednost,
                              _at(12, minuta, 48))


def test_popravek_navzgor_ki_pusti_postanek_v_preteklosti_gre_skozi():
    # Feed sme povedati, da je bilo vozilo tam pozneje, kot smo mislili --
    # dokler trdi, da je bilo. To je meritev in je ne smemo zavreci.
    from kajros.collector import undoes_passing
    assert not undoes_passing(_row(58, 126), RED, DAN, 200, 200, _at(12, 23, 48))


def test_rast_za_se_nedosezen_postanek_je_zakonita():
    # Vozilo, ki stoji, bo na naslednji postaji res vedno bolj pozno.
    # Zamuda, ki raste s hitrostjo ure, je tam pravilna napoved.
    from kajros.collector import undoes_passing
    assert not undoes_passing(_row(30, 60), RED, DAN, 300, 300, _at(12, 17, 30))


def test_padec_ni_nikoli_tekoca_ura():
    from kajros.collector import undoes_passing
    assert not undoes_passing(_row(400, 482), RED, DAN, 126, 126, _at(12, 30, 29))


def test_brez_prejsnje_vrednosti_ali_voznega_reda_varovalka_miruje():
    from kajros.collector import undoes_passing
    assert not undoes_passing(None, RED, DAN, 482, 482, _at(12, 23, 48))
    assert not undoes_passing(_row(58, 126), None, DAN, 482, 482, _at(12, 23, 48))
    assert not undoes_passing(_row(58, 126), (None, None), DAN, 482, 482, _at(12, 23, 48))


def test_napacen_obratovalni_dan_naredi_varovalko_nemocno_ne_napacno():
    """Oba casa se premakneta skupaj, zato zgresi -- nikoli ne zavrne po krivem."""
    from kajros.collector import undoes_passing
    assert not undoes_passing(_row(58, 126), RED, "2026-08-29", 482, 482, _at(12, 23, 48))
    assert not undoes_passing(_row(58, 126), RED, "2026-08-31", 482, 482, _at(12, 23, 48))


def test_enaka_prihodna_in_odhodna_vrednost_ni_dokaz_o_prevozu():
    """Prva razlicica varovalke je EN 1276 vzela pravo dvourno zamudo.

    Feed je 28. 8. ob 00:03 za Celje objavil `0/0` -- napoved pred prihodom,
    ne meritev -- in ob 01:57 pravih +114 min. Ker je bila zapisana vrednost
    nicla za oba dogodka, ni bila dokaz, da je vlak tam ze bil.
    """
    from kajros.collector import undoes_passing
    assert not undoes_passing(_row(0, 0), RED, DAN, 6840, 6840, _at(13, 57, 41))
    # Enaki, a nenicelni vrednosti prav tako ne stejeta: feed ju za nedosezen
    # postanek objavi enaki, ker je to ista prenesena stevilka.
    assert not undoes_passing(_row(120, 120), RED, DAN, 6840, 6840, _at(13, 57, 41))


def _row_ts(arr, dep, ts):
    r = _row(arr, dep)
    r["feed_ts"] = ts
    return r


def test_nicla_ki_popravlja_napoved_ni_blip():
    """LPP 25 (452632), 30. 8., Medvode novo naselje -- vozni red 11:41.

    Feed je za ta postanek ze od 11:11 objavljal rastoco zamudo vozila s
    PREJSNJE voznje: +8, +10, +11, +12, +13 in ob 11:33:55 +14 min. Vsaka od
    teh vrednosti je ob svojem nastanku postanek postavljala v prihodnost,
    torej ni bila meritev. Ob 11:35:44 jo je feed popravil na 0 in avtobus je
    odpeljal skoraj tocno.

    Brez tega pravila je `is_zero_blip` popravek zavrnil in `run` je obtical
    na +14 za vedno -- feed je niclo povedal enkrat samkrat, drsece okno pa
    je slo naprej in potrditve ni bilo nikoli.
    """
    from kajros.collector import is_zero_blip
    red = (42060, 42060)                       # 11:41
    prej = _row_ts(835, 835, _at(11, 33, 55))  # objavljeno, ko je 11:54 se v prihodnosti
    assert not is_zero_blip(prej, None, 0, 0, red, "2026-08-30")


def test_nicla_po_izmerjeni_zamudi_ostane_blip():
    # Varovalka mora se naprej loviti tisto, zaradi cesar je nastala: niclo,
    # ki pride za ZE IZMERJENO veliko zamudo. Tu je vrednost nastala, ko je
    # bil postanek ze prevozen, zato je meritev in nicla je sumljiva.
    from kajros.collector import is_zero_blip
    red = (42060, 42060)
    prej = _row_ts(835, 835, _at(11, 58, 0))   # 11:41 + 14 min = 11:55, ze mimo
    assert is_zero_blip(prej, None, 0, 0, red, "2026-08-30")


# ---------------------------------------------------------------- ocena: smer napake

def test_precenjenih_in_podcenjenih_merita_pri_istem_pragu():
    """Sosednja stolpca sta primerljiva samo, če je prag isti.

    Prej je `precenjenih` štel vsako precenitev, tudi enosekundno,
    `podcenjenih` pa samo tiste nad pet minut. Na 35 325 zajetih vrsticah je
    to pisalo 58,8 % proti 6,3 % in trdilo, da smo precenjevalec; pri enakem
    pragu je 6,6 % proti 6,3 %, torej uravnoteženi.
    """
    r = ocena.POTNIKOVA_REZERVA_S
    # (napoved, resnica): dve zgrešitvi tik pod pragom in dve nad njim.
    vals = [(r - 30, 0), (0, r - 30), (r + 60, 0), (0, r + 60)]
    m = ocena._meritve(vals)
    assert m["precenjenih"] == 25.0
    assert m["podcenjenih"] == 25.0


def test_vozilo_zamudi_precenitev_in_ne_podcenitev():
    """Nevarna smer je precenitev — to ni stvar okusa, ampak `_strosek`.

    Kdor pride na peron prezgodaj, čaka; kdor pride prepozno, je vozilo
    zamudil, in prepozno ga pripelje prav precenitev. V zajetih podatkih je
    bilo 2 318 zamujenih vozil in nobeno ni izviralo iz podcenitve.
    """
    resnica, razmik = 10 * 60, ocena.RAZMIK_S["zeleznica"]
    podcenili = ocena._strosek([(2 * 60, resnica)], "zeleznica")
    precenili = ocena._strosek([(20 * 60, resnica)], "zeleznica")
    assert podcenili < razmik / 60          # samo čakanje
    assert precenili == razmik / 60         # zamujeno vozilo


# --------------------------------------------- meja med meritvijo in napovedjo

def _prev(delay_s, feed_ts):
    """Vrstica `run`, kot jo vidi `is_forecast`."""
    return {"delay_dep": delay_s, "delay_arr": None, "feed_ts": feed_ts}


def _ob(service_date, ura, minuta):
    """Absolutni čas na dani obratovalni dan, v sekundah od epohe."""
    d = date.fromisoformat(service_date)
    return datetime(d.year, d.month, d.day, ura, minuta,
                    tzinfo=ZoneInfo("Europe/Ljubljana")).timestamp()


def test_vrednost_iz_prihodnosti_je_napoved():
    """Feed za vožnjo, ki se ni odpeljala, objavi zamudo prejšnje vožnje.

    Izmerjeni primer iz `collector.is_forecast`: LPP 25 je za postanek z
    voznim redom 11:41 že ob 11:11 objavljal +8 min. Vrednost, ki ob svojem
    nastanku postanek postavlja v PRIHODNOST, ni meritev.
    """
    dan = "2026-08-30"
    sched = (None, 11 * 3600 + 41 * 60)          # (arr_s, dep_s) -> 11:41
    # objavljeno ob 11:11 s +8 min: 11:41 + 8 = 11:49 je takrat še v prihodnosti
    assert is_forecast(_prev(8 * 60, _ob(dan, 11, 11)), sched, dan) is True


def test_vrednost_iz_preteklosti_je_meritev():
    """Ista vrstica, objavljena po tem, ko je vozilo tam že bilo."""
    dan = "2026-08-30"
    sched = (None, 11 * 3600 + 41 * 60)
    # objavljeno ob 11:55, postanek s +8 je bil ob 11:49 -> že mimo
    assert is_forecast(_prev(8 * 60, _ob(dan, 11, 55)), sched, dan) is False


def test_brez_prejsnje_vrstice_ni_napoved():
    """Merilo potrebuje čas nastanka; brez njega ne trdimo ničesar."""
    dan = "2026-08-30"
    sched = (None, 11 * 3600 + 41 * 60)
    assert is_forecast(None, sched, dan) is False
    assert is_forecast(_prev(60, None), sched, dan) is False
    assert is_forecast(_prev(None, _ob(dan, 11, 11)), sched, dan) is False


def test_brez_voznega_reda_ni_napoved():
    """Postanek brez voznorednega časa: merila ni na kaj postaviti."""
    assert is_forecast(_prev(60, _ob("2026-08-30", 11, 11)), None, "2026-08-30") is False
    assert is_forecast(_prev(60, _ob("2026-08-30", 11, 11)), (None, None), "2026-08-30") is False


def test_merilo_nima_prostih_parametrov():
    """Meja je natanko voznoredni čas + zamuda proti času objave.

    Brez praga: minuto pred to mejo je napoved, minuto za njo meritev.
    """
    dan = "2026-08-30"
    sched = (None, 12 * 3600)                     # 12:00
    zamuda = 5 * 60                               # postanek pade na 12:05
    assert is_forecast(_prev(zamuda, _ob(dan, 12, 4)), sched, dan) is True
    assert is_forecast(_prev(zamuda, _ob(dan, 12, 6)), sched, dan) is False


def test_prihodna_vrednost_se_uporabi_ko_odhodne_ni():
    """`COALESCE(delay_dep, delay_arr)` — odhod ima prednost, prihod je rezerva."""
    dan = "2026-08-30"
    sched = (11 * 3600 + 41 * 60, None)           # samo arr_s
    p = {"delay_dep": None, "delay_arr": 8 * 60, "feed_ts": _ob(dan, 11, 11)}
    assert is_forecast(p, sched, dan) is True


# ------------------------------------------------- kateremu dnevu pripada vožnja

def _zdaj(dan, ura, minuta=0):
    d = date.fromisoformat(dan)
    return datetime(d.year, d.month, d.day, ura, minuta,
                    tzinfo=ZoneInfo("Europe/Ljubljana"))


def test_dnevna_voznja_pripada_danasnjemu_dnevu():
    okno = (8 * 3600, 11 * 3600)                 # 08:00-11:00
    dni = {"2026-09-03", "2026-09-04"}
    assert resolve_service_date("t", okno, dni, _zdaj("2026-09-04", 9)) == "2026-09-04"


def test_nocni_vlak_po_polnoci_ostane_pri_vcerajsnjem_dnevu():
    """EC 79 ob 00:20 vozi pod včerajšnjim datumom in njegove voznoredne
    sekunde tečejo čez 86400. Brez tega je videti, kot da danes še ni vozil —
    in prav takrat ga potnik gleda."""
    okno = (22 * 3600, 26 * 3600)                # 22:00 -> 02:00 naslednjega dne
    dni = {"2026-09-03", "2026-09-04"}
    assert resolve_service_date("t", okno, dni, _zdaj("2026-09-04", 0, 20)) == "2026-09-03"


def test_brez_veljavnih_dni_ni_odgovora():
    assert resolve_service_date("t", (8 * 3600, 9 * 3600), set(), _zdaj("2026-09-04", 8)) is None
    assert resolve_service_date("t", (8 * 3600, 9 * 3600), None, _zdaj("2026-09-04", 8)) is None


def test_brez_okna_ni_odgovora():
    assert resolve_service_date("t", None, {"2026-09-04"}, _zdaj("2026-09-04", 8)) is None


def test_dan_brez_voznje_se_ne_izbere():
    """Vožnja, ki danes ne vozi, ne sme dobiti današnjega datuma."""
    okno = (8 * 3600, 11 * 3600)
    assert resolve_service_date("t", okno, {"2026-09-03"}, _zdaj("2026-09-04", 9)) is None


def test_rezerva_pred_odhodom_je_45_minut():
    """Feed začne poročati, preden vožnja odpelje — a ne poljubno zgodaj."""
    okno = (8 * 3600, 11 * 3600)
    dni = {"2026-09-04"}
    assert resolve_service_date("t", okno, dni, _zdaj("2026-09-04", 7, 30)) == "2026-09-04"
    assert resolve_service_date("t", okno, dni, _zdaj("2026-09-04", 7, 0)) is None


def test_rezerva_po_prihodu_je_tri_ure():
    """Zamujajoča vožnja se še vedno pripiše svojemu dnevu."""
    okno = (8 * 3600, 11 * 3600)
    dni = {"2026-09-04"}
    assert resolve_service_date("t", okno, dni, _zdaj("2026-09-04", 13, 30)) == "2026-09-04"
    assert resolve_service_date("t", okno, dni, _zdaj("2026-09-04", 14, 30)) is None


def test_med_dvema_moznima_zmaga_tisti_z_manjso_vrzeljo():
    """Kadar sta oba dneva v dosegu rezerve, odloči bližina k oknu."""
    okno = (22 * 3600, 26 * 3600)
    dni = {"2026-09-03", "2026-09-04"}
    # ob 23:00 smo sredi današnjega okna -> danes, ne včeraj (ki je že mimo)
    assert resolve_service_date("t", okno, dni, _zdaj("2026-09-04", 23)) == "2026-09-04"


# --------------------------------------------------- vzorčenje sence pri avtobusih

def test_zeleznica_ni_vzorcena():
    """Vlakov je malo; vzorčimo samo avtobuse, ki bi sicer dali 135 000 vrstic
    na dan."""
    assert all(ocena._v_vzorcu(str(i), "zeleznica") for i in range(50))


def test_vzorec_je_priblizno_vsaka_peta_voznja():
    from kajros import config
    n = config.OCENA_BUS_VZOREC
    if n <= 1:
        return                                     # vzorčenje izklopljeno
    izbrani = sum(1 for i in range(100000, 105000)
                  if ocena._v_vzorcu(str(i), "avtobus"))
    delez = izbrani / 5000
    assert abs(delez - 1 / n) < 0.03, f"delež {delez:.3f}, pričakoval ~{1/n:.3f}"


def test_vzorec_je_stabilen_med_zagoni():
    """Vzorec, ki se ob vsakem zagonu zamenja, ni vzorec.

    Vgrajeni `hash` je soljen s `PYTHONHASHSEED`, zato ga `_v_vzorcu` ne sme
    uporabljati. Ta test pokliče funkcijo v ločenem procesu z drugim soljenjem
    in zahteva isti izid.
    """
    import os
    import subprocess
    import sys

    ids = [str(i) for i in range(462170, 462200)]
    tu = [ocena._v_vzorcu(i, "avtobus") for i in ids]

    koda = (
        "import sys; sys.path.insert(0, '.');"
        "from kajros import ocena;"
        f"print(''.join('1' if ocena._v_vzorcu(i, 'avtobus') else '0' for i in {ids!r}))"
    )
    izidi = set()
    for sol in ("0", "1", "12345"):
        okolje = dict(os.environ, PYTHONHASHSEED=sol)
        r = subprocess.run([sys.executable, "-c", koda], capture_output=True,
                           text=True, env=okolje, cwd=".")
        assert r.returncode == 0, r.stderr
        izidi.add(r.stdout.strip())
    assert len(izidi) == 1, f"vzorec se med zagoni spreminja: {izidi}"
    assert izidi.pop() == "".join("1" if x else "0" for x in tu)


def test_ista_voznja_je_vedno_ista_odlocitev():
    """Vožnja mora biti cela ali nobena — sicer se razrez po zamudi meri na
    kosih poti."""
    for tid in ("453041", "462170", "1"):
        prvi = ocena._v_vzorcu(tid, "avtobus")
        assert all(ocena._v_vzorcu(tid, "avtobus") is prvi for _ in range(5))


# ------------------------------------------- koliko ostanku sploh smemo verjeti

def test_omejen_ostanek_pri_tocnem_vozilu():
    """Točnemu vozilu ne pripišemo velike spremembe.

    Mediana enega dneva ni mediana. Absolutna meja je 600 s.
    """
    assert stats._omejen_ostanek(3000, 0) == 600
    assert stats._omejen_ostanek(-3000, 0) == -600
    assert stats._omejen_ostanek(120, 0) == 120        # pod mejo ostane, kar je


def test_omejen_ostanek_pusti_prostor_veliki_zamudi():
    """Vlak s +25 min lahko izgubi še deset, točen pa ne — zato sorazmerna
    meja poleg absolutne."""
    assert stats._omejen_ostanek(3000, 25 * 60) == 1500      # 1x trenutne
    assert stats._omejen_ostanek(600, 25 * 60) == 600        # pod mejo


def test_omejen_ostanek_upoteva_tudi_prezgodnjo_voznjo():
    """Meja je na ABSOLUTNI vrednosti trenutne zamude — prezgoden avtobus je
    prav tako daleč od nič."""
    assert stats._omejen_ostanek(3000, -20 * 60) == 1200


def test_omejen_ostanek_spostuje_podane_parametre():
    """Backtest meri druge meje; funkcija jih mora sprejeti."""
    assert stats._omejen_ostanek(3000, 0, omeji_s=900) == 900
    assert stats._omejen_ostanek(3000, 600, omeji_s=0, omeji_delez=2.0) == 1200


# ------------------------------------------------------- razred trenutne zamude

def test_razred_zamude_ima_vkljucujoce_spodnje_meje():
    """Okrevanje pri +1 in pri +40 min ni isto, zato razredi.

    Meje `DELAY_BUCKETS` so (120, 600, 1800) in veljajo od spodaj navzgor:
    120 s je že razred 1, ne še 0.
    """
    assert stats.DELAY_BUCKETS == (120, 600, 1800)
    assert stats.delay_bucket(119) == 0
    assert stats.delay_bucket(120) == 1
    assert stats.delay_bucket(599) == 1
    assert stats.delay_bucket(600) == 2
    assert stats.delay_bucket(1799) == 2
    assert stats.delay_bucket(1800) == 3
    assert stats.delay_bucket(99999) == 3


def test_prezgodnja_voznja_je_v_najnizjem_razredu():
    """Prezgoden avtobus nima zamude, ki bi jo nadoknadil."""
    assert stats.delay_bucket(-3000) == 0
    assert stats.delay_bucket(0) == 0


def test_backtest_uporablja_isto_delitev_kot_prikaz():
    """Sicer bi merili en model in uporabljali drugega — razlika, ki je
    meritev ne bi pokazala."""
    from kajros import backtest
    assert all(stats.delay_bucket(s) == backtest._bucket(s)
               for s in range(-600, 3600, 7))


# --------------------------------------------------------------- čas in datumi

def test_now_seconds_je_sekunda_od_polnoci():
    t = datetime(2026, 9, 4, 7, 30, 15, tzinfo=ZoneInfo("Europe/Ljubljana"))
    assert journey.now_seconds(t) == 7 * 3600 + 30 * 60 + 15
    assert journey.now_seconds(t.replace(hour=0, minute=0, second=0)) == 0


def test_today_in_yesterday_sta_lokalna_dneva():
    t = datetime(2026, 9, 4, 0, 5, tzinfo=ZoneInfo("Europe/Ljubljana"))
    assert journey.today(t) == "2026-09-04"
    assert journey.yesterday(t) == "2026-09-03"


# ------------------------------------------------------------- vremenska celica

def test_cell_key_je_stabilen_in_na_mrezi():
    """Postaja mora vedno pasti v isto celico; mreža je 0,1 stopinje (~8 km)."""
    assert weather.cell_key(46.058, 14.510) == weather.cell_key(46.058, 14.510)
    assert weather.cell_key(46.058, 14.510) == "46.1,14.5"
    # Sosednji točki znotraj iste celice dasta isti ključ.
    assert weather.cell_key(46.07, 14.52) == weather.cell_key(46.08, 14.53)


def test_cell_key_nikoli_ne_vrne_negativne_nicle():
    """'-0.0' in '0.0' bi bila dva ključa za isto celico."""
    assert "-0.0" not in weather.cell_key(-0.02, -0.02)


# --------------------------------------------------- rezerva voznega reda

def test_rezerva_pobere_najvec_toliko_kolikor_vozilo_zamuja():
    """Vlak s +3 min na rezervi 10 min ne pride 7 min PRED voznim redom."""
    assert stats._after_slack(180, 600) == 0
    assert stats._after_slack(600, 180) == 420      # porabi vso rezervo
    assert stats._after_slack(600, 0) == 600        # brez rezerve ostane isto


def test_rezerva_prezgodnjega_vozila_ne_potisne_se_naprej():
    """Prehiter avtobus ostane prehiter — rezerva mu ne doda prednosti.

    Pri železnici tega ni nikoli (0 negativnih na 78 082 vrsticah), pri
    avtobusih pa je vsakdanje: 10,7 % vrstic je vsaj minuto prezgodnjih.
    """
    assert stats._after_slack(-300, 600) == -300
    assert stats._after_slack(-300, 0) == -300


def test_rezerva_je_monotona():
    """Več rezerve nikoli ne pomeni večje zamude."""
    prej = None
    for slack in range(0, 1200, 60):
        v = stats._after_slack(900, slack)
        if prej is not None:
            assert v <= prej
        prej = v
    assert stats._after_slack(900, 10000) == 0      # nikoli pod nič


def test_opis_zamude_je_edini_vir_pravila():
    """Odjemalec ne sme izpeljevati minute, razreda in praga prezgodnjosti.

    Ta pravila so bila zapisana dvakrat -- v `stats.py` in v `common.js` -- in
    to je natanko oblika napake, ki jo CLAUDE.md ze belezi kot dvakrat videno
    na zaslonu. Z drugim odjemalcem (Android) bi bila zapisana trikrat.
    """
    from kajros import stats

    assert stats.opis_zamude(None) is None

    # Zaokrozevanje: 29 s je se "tocno", 30 s ni. Ista meja kot v prikazu.
    assert stats.opis_zamude(29)["min"] == 0
    assert stats.opis_zamude(30)["min"] == 1
    assert stats.opis_zamude(29)["razred"] == "tocno"
    assert stats.opis_zamude(30)["razred"] == "1-5"

    # Razred se doloca iz ZAOKROZENE minute -- glej `_razred_zamude`.
    for s, kljuc in ((0, "tocno"), (300, "1-5"), (330, "5-15"),
                     (900, "5-15"), (930, "nad-15")):
        assert stats.opis_zamude(s)["razred"] == kljuc, s

    # Kljuci morajo ustrezati prikaznim imenom, ki jih nosi `povzetek`.
    assert set(stats._KLJUC_RAZREDA) == {"točno", "1–5 min", "5–15 min", "nad 15 min"}

    # Prezgodaj je prag na ZAOKROZENI minuti, ne na sekundah, in meja je pri
    # natanko -30 s: floor(-0.5 + 0.5) = 0, JS Math.round(-0.5) = -0. Pri -31 s
    # sta oba ze -1. Prvic sem to napisal narobe -- prav zato je tu test.
    assert stats.opis_zamude(-30)["prezgodaj"] is False
    assert stats.opis_zamude(-30)["min"] == 0
    assert stats.opis_zamude(-31)["prezgodaj"] is True
    assert stats.opis_zamude(-31)["min"] == -1
    assert stats.opis_zamude(-90)["min"] == -1

    # Vrsta gre skozi nespremenjena in je omejena na znane vrednosti.
    assert stats.opis_zamude(0, "izmerjeno")["vrsta"] == "izmerjeno"
    for v in stats.VRSTE_ZAMUDE:
        assert stats.opis_zamude(60, v)["vrsta"] == v


def test_opis_zamude_se_ujema_z_razredi_povzetka():
    """Ce se kljuc in prikazno ime razideta, bo graf kazal drugo kot zeton."""
    from kajros import stats

    for s in (0, 30, 200, 400, 1000, 5000):
        prikazno = stats._razred_zamude(s)
        assert stats.opis_zamude(s)["razred"] == stats._KLJUC_RAZREDA[prikazno]
