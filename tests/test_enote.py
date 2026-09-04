"""Enotni testi čistih funkcij.

Namenoma brez omrežja in brez baze na disku: vse, kar se da preveriti brez
zajema, naj se preveri hitro. Poizvedbe nad shemo so v `test_poizvedbe.py`.

    ./venv/bin/python -m pytest tests/ -q
"""
from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from kajros import ocena, weather
from kajros.alerts import parse_delay_text
from kajros.collector import (_delay_of, is_forecast, is_zero_blip,
                               worth_logging)
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
