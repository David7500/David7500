"""Kje ustavi nadomestni avtobus (`nadomestni.py`) in kako to preberemo s strani SŽ."""
import importlib.util
from pathlib import Path

from kajros import nadomestni

_SKRIPTA = Path(__file__).resolve().parent.parent / "scripts" / "nadomestna_postajalisca.py"
_spec = importlib.util.spec_from_file_location("nadomestna_postajalisca", _SKRIPTA)
skripta = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(skripta)


def test_kljuc_poveze_zapise_imen():
    assert nadomestni.kljuc("Lesce Bled") == nadomestni.kljuc("Lesce-Bled")
    assert nadomestni.kljuc("Šmarje Sap") == nadomestni.kljuc("Šmarje-Sap")
    assert nadomestni.kljuc("Lavrica(Železniški)") == nadomestni.kljuc("Lavrica")
    assert nadomestni.kljuc("Hrplje – Kozina") == nadomestni.kljuc("Hrpelje-Kozina")


def test_ljubljana_na_avtobusni_postaji():
    p = nadomestni.za_postajo("Ljubljana")
    assert "peroni 37, 38 in 39" in p["opis"]
    assert abs(p["lat"] - 46.058) < 0.001 and abs(p["lon"] - 14.514) < 0.001
    assert nadomestni.za_postajo("Postaja, ki je ni") is None
    assert nadomestni.za_postajo(None) is None


def test_posnetek_nosi_vir_in_dan():
    import json
    p = json.loads(nadomestni.DATOTEKA.read_text())
    assert p["vir"] == nadomestni.VIR and p["pregledano"]
    assert len(p["postaje"]) > 200
    # Lega je samo, kjer je prestala preverjanje: napačno povezavo (Paška vas
    # -> Ponikva, 33 km) zavržemo, opis ostane.
    pv = next(x for x in p["postaje"] if x["postaja"] == "Paška vas")
    assert pv["opis"] and pv["lat"] is None


def test_dopolni_samo_nadomestne_voznje():
    bus = {"mode": "bus", "network": "zeleznica"}
    vlak = {"mode": "vlak", "network": "zeleznica"}
    mestni = {"mode": "bus", "network": "avtobus"}
    nadomestni.dopolni([bus, vlak, mestni], "Ljubljana")
    assert "peroni" in bus["nadomestni_postanek"]["opis"]
    assert "nadomestni_postanek" not in vlak and "nadomestni_postanek" not in mestni


# ---------------------------------------------------------------- povezave SŽ

POSTAJA = (46.0, 14.5)


def test_zebljicek_v_imenu_je_najtocnejsi():
    t, kako = skripta.tocka("https://www.google.com/maps/place/46%C2%B003'29.2%22N+14%C2%B030'49.2%22E/"
                            "@46.0582419,14.5119424,226m/data=!3m1!1e3!4m4!3m3!8m2!3d46.058118!4d14.513669", None)
    assert kako == "žebljiček"
    assert abs(t[0] - 46.058111) < 1e-5 and abs(t[1] - 14.513667) < 1e-5


def test_imenovan_kraj_pred_zaokrozenim_zebljickom():
    """Velika Nedelja: zaokrožen žebljiček je 1,9 km mimo, kraj 28 m."""
    t, kako = skripta.tocka(
        "https://www.google.com/maps/place/Mihovci+pri+Vel.+Nedelji+74+Parking/@46.4152457,16.1046458,151m/"
        "data=!3m1!1e3!4m12!1m5!3m4!2zNDbCsDI1JzAxLjIiTiAxNsKwMDQnNDguMCJF!8m2!3d46.417!4d16.08"
        "!3m5!1s0x476f5bafac80dd29:0xf768ebdcb489ced9!8m2!3d46.4150567!4d16.104858!16", None)
    assert (kako, t) == ("kraj", (46.4150567, 16.104858))


def test_pot_vzame_tocko_najdlje_od_postaje():
    """Medno: od postaje (imenovana točka v podatkih) do postajališča (številke v poti)."""
    url = ("https://www.google.com/maps/dir/Medno/46.1244612,14.4369512/@46.1236201,14.4371822,454m/"
           "data=!3m1!1e3!4m9!4m8!1m5!1m1!1s0x477acc684a4a21bd:0xffb3aefb8bc09b89"
           "!2m2!1d14.4390528!2d46.1221444!1m0!3e2?entry=ttu")
    t, kako = skripta.tocka(url, (46.122132, 14.439149))
    assert (kako, t) == ("pot", (46.1244612, 14.4369512))


def test_samo_pogled_je_zadnja_moznost():
    t, kako = skripta.tocka("https://www.google.com/maps/@46.058357,13.617482,120m/data=!3m1!1e3", None)
    assert (kako, t) == ("pogled", (46.058357, 13.617482))
