"""Barve zdravja in opozorila po pošti.

    ./venv/bin/python -m pytest tests/test_opozorila.py -q
"""
from __future__ import annotations

import json

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


STROJ = {"disk_prostih": 114 * 2**30, "disk_vseh": 234 * 2**30, "wal_bajtov": 64 * 2**20}


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
    # Vir ne odgovarja: rumeno, dokler je motnja; po `VIR_ORANZNO_S` oranžno --
    # tako dolg molk je sprememba pri viru (7. 10. 2026 Cloudflare), ne motnja.
    assert zdravje.ocena(z, STROJ, T)["zamude_sz"][0] == zdravje.ORANZNA
    z["zamude_sz"]["ts"] = T - 30 * 60
    assert zdravje.ocena(z, STROJ, T)["zamude_sz"][0] == zdravje.MLACNA


def test_cloudflare_s_premorom_ni_obstala_nit():
    """14. 10. 2026 1:39--3:59: Chrome ni prišel skozi izziv, nov poskus po
    5 min premora -- napaka vsakih 6,5 min. Pošta je rekla „nit ne piše“."""
    z = _zdravo()
    z["zamude_sz"] = {"ts": T - 3600, "napaka": "izziv ni rešen v 90 s", "napaka_ts": T - 480}
    assert zdravje.ocena(z, STROJ, T)["zamude_sz"][0] == zdravje.MLACNA
    z["zamude_sz"]["napaka_ts"] = T - 2 * zdravje.SZ_NAPAKA_S
    assert _rdece(z) == {"zamude_sz"}


def test_obstala_nit_sz_ponoci_ni_rdeca():
    """Ko vlaki ne vozijo, zamud ni komu kazati; zjutraj spet rdeče."""
    z = _zdravo()
    z["zamude_sz"] = {"ts": T - 2 * 3600}
    z["vozi_zdaj"] = {"zeleznica": 1, "avtobus": 20}
    assert zdravje.ocena(z, STROJ, T)["zamude_sz"][0] == zdravje.MLACNA
    z["vozi_zdaj"]["zeleznica"] = 5
    assert "zamude_sz" in _rdece(z)


def test_rumena_vrstica_pove_stevilo_ki_jo_prizge():
    """Pri prevoznikih NAP je „ne v feedu“ vedno 0; prej je vrstica pisala
    „Nomago 0 od 160“, prižgalo pa jo je 5 vozil brez zamude."""
    z = _zdravo()
    z["lega_brez_zamude"] = {"Nomago": [0, 2, 160], "Arriva": [0, 0, 137], "LPP": [3, 0, 40]}
    raz, besedilo = zdravje.ocena(z, STROJ, T)["lega_brez_zamude"]
    assert raz == zdravje.MLACNA
    assert besedilo == ("vozila z lego, a brez zamude: Nomago 2 od 160; "
                        "feed zamud jih ne nosi, zamudo meri lega: LPP 3 od 40")


def test_wal_in_disk():
    m = {**STROJ, "wal_bajtov": int(5.4 * 2**30)}
    assert _rdece(_zdravo(), m) == {"wal"}
    for prostih, raz in ((40, zdravje.MLACNA), (26, zdravje.ORANZNA), (15, zdravje.SLABA)):
        m = {**STROJ, "disk_prostih": prostih * 2**30}
        assert zdravje.ocena(_zdravo(), m, T)["disk"][0] == raz


def test_lpp_brez_voznega_reda_po_deležu():
    """Mestni LPP vsak dan vozi kaj mimo objave: rumeno. Veliko uro dolgo
    (1. 10. 2026 17 %) je oranžno -- pripenjanje ne zmore, rabi kodo."""
    z = _zdravo()
    z["rt_neznanih"]["lpp"] = [30, 282]
    sled = zdravje.Sled()
    raz, besedilo = zdravje.ocena(z, STROJ, T, sled)["neznane"]
    assert raz == zdravje.MLACNA and "LPP 30 od 282" in besedilo
    assert zdravje.ocena(z, STROJ, T + 1800, sled)["neznane"][0] == zdravje.MLACNA
    assert zdravje.ocena(z, STROJ, T + 3600, sled)["neznane"][0] == zdravje.ORANZNA
    # 31. 10. 2026 (praznik, dvojniki v objavi): malo, ves dan rumeno.
    z["rt_neznanih"]["lpp"] = [2, 105]
    for t in (7200, 4 * 3600, 9 * 3600):
        assert zdravje.ocena(z, STROJ, T + t, sled)["neznane"][0] == zdravje.MLACNA
    # Brez sledi (en klic) trajanja ni.
    z["rt_neznanih"]["lpp"] = [30, 282]
    assert zdravje.ocena(z, STROJ, T + 9 * 3600)["neznane"][0] == zdravje.MLACNA


def test_ponoci_feed_ne_zvoni_podnevi_in_pri_okvari_pa():
    """Od ~23:30 do ~4:30 nič ne vozi in feed molči po pravici: tri rdeče
    vrstice in do 10 mailov na noč. Okvara, ko vozni red vozila ima, ostane."""
    z = _zdravo()
    z["last_feed_ts"] = T - 5 * 3600
    z["by_network"]["zeleznica"]["last_feed_ts"] = T - 5 * 3600
    z["by_network"]["avtobus"]["last_feed_ts"] = T - 5 * 3600
    assert _rdece(z) == {"feed", "zeleznica", "avtobus"}          # brez podatka kot prej
    z["vozi_zdaj"] = {"zeleznica": 0, "avtobus": 1}               # eden ne šteje
    assert _rdece(z) == set()
    z["vozi_zdaj"] = {"zeleznica": 5, "avtobus": 0}
    assert _rdece(z) == {"feed", "zeleznica"}
    # Pravi nočni alarm: disk in WAL se ne ozirata na vozni red.
    z["vozi_zdaj"] = {"zeleznica": 0, "avtobus": 0}
    assert _rdece(z, {**STROJ, "wal_bajtov": 5 * 2**30}) == {"wal"}


def test_sveza_svezina_premaga_stare_stevce():
    """17. 10. 2026 ob 3:58: števci po omrežjih so ob nočnem računu povzetkov
    obtičali pri 1:22, vlaki pa so se pisali od 3:24 -- pošta „vlaki: zadnji
    zapis pred 2,6 h“. Sveži zapis zadnje ure odloči; brez njega števci."""
    z = _zdravo()
    z["vozi_zdaj"] = {"zeleznica": 5, "avtobus": 30}
    z["by_network"]["zeleznica"]["last_feed_ts"] = T - 2.6 * 3600
    assert _rdece(z) == {"zeleznica"}
    z["svezina"] = {"zeleznica": T - 120, "avtobus": T - 30}
    assert _rdece(z) == set()
    z["svezina"] = {"avtobus": T - 30}                    # vlakov zadnjo uro ni
    assert _rdece(z) == {"zeleznica"}


def _ocena(*rdece, neznano=()):
    """Izid `zdravje.posta()`: rdeče ključe kot okvare, `neznano` kot None."""
    return ({k: zdravje.Okvara(f"{k} stoji", f"popravi {k}") for k in rdece}
            | {k: None for k in neznano})


def _teci(koraki, zacetek=T):
    """(sekunde od začetka, rdeče ključe[, neocenjene]) -> poslana sporočila."""
    stanje, poslano = {}, []
    for t, rdece, *neznano in koraki:
        okvare = _ocena(*rdece, neznano=neznano[0] if neznano else ())
        stanje, sp, nove, resene = opozorila.korak(stanje, okvare, zacetek + t)
        if sp:
            stanje = opozorila._potrdi(stanje, nove, resene, zacetek + t)
            poslano.append((sp[0], t, sp[1]))
    return poslano


def test_ena_posta_ob_okvari_in_ena_ob_koncu():
    koraki = [(t, ["zamude_sz"]) for t in range(0, 4 * 3600, 60)]
    koraki += [(4 * 3600 + t, []) for t in range(0, 1200, 60)]
    poslano = _teci(koraki)
    assert [(z.split(" -- ")[0], t) for z, t, _ in poslano] == [
        ("kajros: stoji", ZAMIK_S), ("kajros: spet v redu", 4 * 3600 + KONEC_S)]
    assert "stalo 07:53–11:53, 4 h 0 min" in poslano[1][2]
    # Pošta pove, kaj storiti, in ime vrstice, ne le razloga.
    assert "zemljevid SŽ: zamude_sz stoji" in poslano[0][2]
    assert "Kaj storiti: popravi zamude_sz" in poslano[0][2]


def test_ponoci_okvara_ne_ugasne_in_ne_zvoni_znova():
    """Obstala nit ob 23:40; ponoči vrstica nima ocene (nič ne vozi). Prej:
    „spet dela“ ob polnoči in „stoji“ zjutraj znova -- dve lažni pošti."""
    koraki = [(t, ["zamude_sz"]) for t in range(0, 1200, 60)]
    koraki += [(1200 + t, [], ["zamude_sz"]) for t in range(0, 4 * 3600, 60)]
    koraki += [(1200 + 4 * 3600 + t, ["zamude_sz"]) for t in range(0, 1800, 60)]
    assert [z.split(" -- ")[0] for z, _, _ in _teci(koraki)] == ["kajros: stoji"]
    # Zjutraj spet v redu: ena pošta o koncu, po `KONEC_S`.
    koraki = koraki[:-30] + [(1200 + 4 * 3600 + t, []) for t in range(0, 1800, 60)]
    assert [z.split(" -- ")[0] for z, _, _ in _teci(koraki)] == [
        "kajros: stoji", "kajros: spet v redu"]


def test_posta_dolocenega_trajanja():
    """Okvara pove, koliko mora trajati, preden gre pošta."""
    okvare = {"neznane": zdravje.Okvara("x", "y", 1800)}
    stanje, sp, _, _ = opozorila.korak({}, okvare, T)
    stanje, sp, _, _ = opozorila.korak(stanje, okvare, T + ZAMIK_S)
    assert sp is None
    _, sp, nove, _ = opozorila.korak(stanje, okvare, T + 1800)
    assert nove == ["neznane"]


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


class _Odgovor:
    def __init__(self, koda):
        self.status_code = koda

    def close(self):
        pass


def _get(izidi):
    """Ponaredek `requests.get`: naslov -> koda ali izjema; ostalo 200."""
    def get(url, **_):
        izid = next((v for k, v in izidi.items() if k in url), 200)
        if isinstance(izid, Exception):
            raise izid
        return _Odgovor(izid)
    return get


def test_vir_pove_po_cloveško_kaj_je_narobe():
    exc = opozorila.requests.exceptions
    primeri = {
        "a": exc.ConnectTimeout("Caused by ConnectTimeoutError"),
        "b": exc.ConnectionError("[Errno 111] Connection refused"),
        "c": exc.ConnectionError("NameResolutionError: Failed to resolve"),
        "d": exc.ReadTimeout("Read timed out. (read timeout=20)"),
        "e": 503,
    }
    get = _get(primeri)
    assert [opozorila.preveri_vir(f"https://{k}/", get) for k in "abcde"] == [
        (False, "ni povezave v 10 s"), (False, "zavrača povezave"),
        (False, "ime se ne razreši (DNS)"), (False, "povezava je, odgovora ni v 20 s"),
        (False, "odgovori 503")]
    assert opozorila.preveri_vir("https://f/", get)[0]


def test_vzrok_loci_izpad_vira_od_nasega_interneta():
    """8. 10. 2026: derp.si ne sprejema povezav, kontrola dela -> izpad pri
    viru. Brez kontrole bi bil isti izid videti kot izpad pri nas."""
    exc = opozorila.requests.exceptions.ConnectTimeout("x")
    besedilo = opozorila.vzrok(_get({"derp.si": exc}), zdaj=T)
    assert "derp.si · zamude IJPP: ni povezave v 10 s" in besedilo
    assert "izpad je pri njih, ne pri nas." in besedilo
    besedilo = opozorila.vzrok(_get({"derp.si": exc, "cloudflare": exc}), zdaj=T)
    assert "nima interneta" in besedilo
    assert "Vsi viri odgovarjajo" in opozorila.vzrok(_get({}), zdaj=T)


def test_vzrok_samo_pri_okvari_zajema():
    """Preverjanje virov traja do pol minute; pri polnem disku ne pove nič."""
    klici = []

    def vzrok():
        klici.append(1)
        return "Vzrok: test"
    stanje, _, _, _ = opozorila.korak({}, _ocena("wal"), T, vzrok)
    _, sp, _, _ = opozorila.korak(stanje, _ocena("wal"), T + ZAMIK_S, vzrok)
    assert sp and not klici
    stanje, _, _, _ = opozorila.korak({}, _ocena("avtobus"), T, vzrok)
    _, sp, _, _ = opozorila.korak(stanje, _ocena("avtobus"), T + ZAMIK_S, vzrok)
    assert klici == [1] and "Vzrok: test" in sp[1]
    assert sp[1].index("Vzrok") < sp[1].index("/admin")


def test_rumene_v_posti_samo_ob_novi_okvari():
    rumene = ["zemljevid SŽ ne odgovarja od pred 70 min: izziv ni rešen v 90 s"]
    stanje, _, _, _ = opozorila.korak({}, _ocena("zeleznica"), T, rumene=rumene)
    stanje, sp, nove, _ = opozorila.korak(stanje, _ocena("zeleznica"), T + ZAMIK_S, rumene=rumene)
    assert "Ob tem rumeno" in sp[1] and rumene[0] in sp[1]
    stanje = opozorila._potrdi(stanje, nove, [], T + ZAMIK_S)
    poslano = []
    for t in range(60, 1200, 60):
        stanje, sp, _, resene = opozorila.korak(stanje, {}, T + ZAMIK_S + t, rumene=rumene)
        if sp:
            stanje = opozorila._potrdi(stanje, [], resene, T + ZAMIK_S + t)
            poslano.append(sp)
    assert len(poslano) == 1 and "spet v redu" in poslano[0][0] and "rumeno" not in poslano[0][1]


def _posta(z, m=STROJ, zdaj=T, vse=False):
    """Okvare za pošto; z `vse` tudi neocenjene vrstice (None)."""
    p = zdravje.posta(z, m, zdravje.ocena(z, m, zdaj), zdaj)
    return p if vse else {k: o for k, o in p.items() if o is not None}


def test_v_posti_samo_kar_rabi_skrbnika():
    """Od 1. do 17. 10. 2026 je šlo 67 pošt „stoji“, pri večini skrbnik ni
    mogel nič: nekaj vozil brez zamude, LPP mimo voznega reda ob maratonu,
    derp.si pol ure ne odgovarja (rezerve tečejo)."""
    z = _zdravo()
    z["vozi_zdaj"] = {"zeleznica": 30, "avtobus": 300}
    z["lega_brez_zamude"] = {"Arriva": [0, 3, 29], "Nomago": [0, 8, 150]}
    z["rt_neznanih"] = {"ijpp": [1, 97], "lpp": [4, 197]}
    z["derp_prebran"] = {"ijpp": T - 45 * 60, "lpp": T - 30}
    ocena = zdravje.ocena(z, STROJ, T)
    assert {k for k in ("lega_brez_zamude", "neznane", "derp_ijpp")
            if ocena[k][0] == zdravje.MLACNA} == {"lega_brez_zamude", "neznane", "derp_ijpp"}
    assert _posta(z) == {}
    # Kar rabi poseg: obstala nit, poln disk, WAL.
    assert set(_posta(z, {**STROJ, "wal_bajtov": 5 * 2**30})) == {"wal"}


def test_vozila_brez_zamude_v_posti_sele_v_velikem():
    z = _zdravo()
    z["lega_brez_zamude"] = {"Arriva": [0, 9, 40]}
    assert "lega_brez_zamude" not in _posta(z)
    z["lega_brez_zamude"] = {"Arriva": [0, 25, 100], "Nomago": [0, 2, 150]}
    o = _posta(z)["lega_brez_zamude"]
    assert o.razlog.startswith("vozila z lego, a brez zamude: Arriva 25 od 100")
    assert o.po_s == ZAMIK_S and not o.nujno                 # oranžno: podnevi
    z["lega_brez_zamude"] = {"Arriva": [0, 15, 70]}         # 21 %: še resnica na cesti
    assert "lega_brez_zamude" not in _posta(z)
    # Rumena, ki ne mine poldrugo uro, ni več resnica na cesti.
    sled = zdravje.Sled()
    assert zdravje.ocena(z, STROJ, T, sled)["lega_brez_zamude"][0] == zdravje.MLACNA
    assert (zdravje.ocena(z, STROJ, T + zdravje.BREZ_ZAMUDE_ORANZNO_S, sled)["lega_brez_zamude"][0]
            == zdravje.ORANZNA)


def test_neznane_v_posti_samo_ijpp():
    """22. 9. 2026: IJPP 16 od 662 (2,4 %), stari id-ji po novem voznem redu --
    popravilo je rabilo kodo. LPP vozi mimo voznega reda sam od sebe."""
    z = _zdravo()
    z["rt_neznanih"] = {"ijpp": [16, 662], "lpp": [40, 280]}
    o = _posta(z)["neznane"]
    assert o.razlog.startswith("vožnje v feedu brez voznega reda: IJPP 16 od 662")
    assert o.po_s == 1800 and not o.nujno
    z["rt_neznanih"] = {"ijpp": [0, 662], "lpp": [40, 280]}
    assert "neznane" not in _posta(z)


def test_straza_proti_sz_v_posti_po_pol_ure():
    z = _zdravo()
    z["zamude_sz"]["skladnost"] = {"primerjav": 2000, "prenizko": 60, "previsoko": 0,
                                    "vlakov": 4, "primeri": ["RG 318 (SŽ +18, prikaz +12)"]}
    o = _posta(z)["skladnost_sz"]
    assert o.po_s == 1800 and "RG 318" in o.razlog


def test_derp_v_posti_po_sestih_urah():
    """Rezerve tečejo same (rumeno); šest ur molka je vprašanje, ali vir še
    obstaja -- oranžno, pošta podnevi."""
    z = _zdravo()
    z["vozi_zdaj"] = {"zeleznica": 30, "avtobus": 300}
    z["derp_prebran"] = {"ijpp": T - 5 * 3600, "lpp": T - 30}
    assert zdravje.ocena(z, STROJ, T)["derp_ijpp"][0] == zdravje.MLACNA and _posta(z) == {}
    z["derp_prebran"]["ijpp"] = T - 7 * 3600
    assert set(_posta(z)) == {"derp_ijpp"} and not _posta(z)["derp_ijpp"].nujno


def test_zamrznjen_derp_kot_molk():
    """Odgovor z isto vsebino ni dokaz, da vir dela: zajem vožnje izpusti,
    zamude pišejo rezerve (rumeno); šest ur je vprašanje za Claude."""
    from kajros import iz_lege
    assert zdravje.DERP_ZAMRZNJEN_S == iz_lege.FEED_ZAMRZNJEN_S
    z = _zdravo()
    z["vozi_zdaj"] = {"zeleznica": 30, "avtobus": 300}
    z["derp_prebran"] = {"ijpp": T - 30, "lpp": T - 30}
    z["derp_vsebina"] = {"ijpp": T - 60, "lpp": T - 15 * 60}
    o = zdravje.ocena(z, STROJ, T)
    assert o["derp_ijpp"][0] == zdravje.DOBRA
    assert o["derp_lpp"][0] == zdravje.MLACNA and "vsebina se ni spremenila" in o["derp_lpp"][1]
    assert _posta(z) == {}
    z["derp_vsebina"]["lpp"] = T - 7 * 3600
    assert set(_posta(z)) == {"derp_lpp"} and not _posta(z)["derp_lpp"].nujno


def test_napaka_nase_kode_ni_molk_vira():
    """Izjema v naši obdelavi feeda: derp.si je odgovoril, `rollback` pa je
    razveljavil zapis branja -- do 31. 10. 2026 „derp.si ne odgovarja“.
    Napaka branja vira niza ne podaljša; tri zapored je koda (oranžno)."""
    import requests
    from kajros import collector, db, viri

    c = db.connect(":memory:")
    db.init(c)

    def pade(exc):
        try:
            raise exc
        except Exception as e:      # noqa: BLE001 -- preizkus vzame, kar zanka
            return e

    collector.zapisi_korak(c, "zamude")                       # uspeh brez niza: nič
    assert db.get_meta(c, "zajem_napake") is None
    for i in range(2):
        collector.zapisi_korak(c, "zamude", pade(KeyError("trip_id")), zdaj=T - 60 + 30 * i)
    vira = pade(requests.ReadTimeout("derp.si"))
    vira.kajros_vir = "derp_zamude"                            # kot `viri.branje`
    assert viri.iz_vira(vira) == "derp_zamude"
    collector.zapisi_korak(c, "zamude", vira, zdaj=T - 20)
    zn = json.loads(db.get_meta(c, "zajem_napake"))
    assert zn["zamude"]["zapored"] == 2 and zn["zamude"]["od"] == T - 60
    assert "KeyError" in zn["zamude"]["napaka"] and "test_opozorila.py" not in zn["zamude"]["kje"]

    z = _zdravo()
    z["vozi_zdaj"] = {"zeleznica": 30, "avtobus": 300}
    z["derp_prebran"] = {"ijpp": T - 20 * 60, "lpp": T - 30}  # zapis branja razveljavljen
    z["derp_vsebina"] = {"ijpp": T - 20 * 60, "lpp": T - 30}
    z["zajem_napake"] = zn
    m = {**STROJ, "viri": {"derp_zamude": {"uspeh_ts": T - 20, "zaporednih": 0}}}
    o = zdravje.ocena(z, m, T)
    assert o["derp_ijpp"] == (zdravje.DOBRA, "")
    assert o["zajem_napake"][0] == zdravje.MLACNA and "zamude IJPP: 2×" in o["zajem_napake"][1]
    assert _posta(z, m) == {}
    # Brez dnevnika virov (drug proces) ostane star zapis branja: molk.
    assert zdravje.ocena(z, STROJ, T)["derp_ijpp"][0] == zdravje.MLACNA

    collector.zapisi_korak(c, "zamude", pade(KeyError("trip_id")), zdaj=T)
    z["zajem_napake"] = json.loads(db.get_meta(c, "zajem_napake"))
    assert zdravje.ocena(z, m, T)["zajem_napake"][0] == zdravje.ORANZNA
    assert set(_posta(z, m)) == {"zajem_napake"} and not _posta(z, m)["zajem_napake"].nujno

    collector.zapisi_korak(c, "zamude", zdaj=T + 30)            # uspeh konča niz
    z["zajem_napake"] = json.loads(db.get_meta(c, "zajem_napake"))
    assert z["zajem_napake"]["zamude"]["zapored"] == 0
    assert zdravje.ocena(z, m, T + 30)["zajem_napake"] == (zdravje.DOBRA, "")


def test_uvoz_voznega_reda_ni_molk_derp():
    """Uvoz ob 4:20 ustavi glavno zanko (17.--31. 10. 2026 4--5 min, 17. 10.
    7,4 min): zdravje pove uvoz, ne „derp.si ne odgovarja“. Zanka, ki brez
    uvoza ne tiktaka, je obstala (rdeče); obhod s štirimi časovnimi mejami
    derp.si (do 4 min) to še ni."""
    z = _zdravo()
    z["vozi_zdaj"] = {"zeleznica": 20, "avtobus": 40}
    z["derp_prebran"] = {"ijpp": T - 6 * 60, "lpp": T - 6 * 60}
    z["derp_vsebina"] = {"ijpp": T - 11 * 60, "lpp": T - 11 * 60}
    z["zanka_ts"] = T - 20
    z["uvoz"] = {"od": T - 3600, "do": T - 3300}
    o = zdravje.ocena(z, STROJ, T)
    assert o["zanka"] == (zdravje.DOBRA, "") and "ne odgovarja" in o["derp_ijpp"][1]

    z["zanka_ts"], z["uvoz"] = T - 5 * 60, {"od": T - 6 * 60, "do": None}
    o = zdravje.ocena(z, STROJ, T)
    assert o["zanka"][0] == zdravje.MLACNA and "uvoz voznega reda teče 6 min" in o["zanka"][1]
    assert o["derp_ijpp"] == ("", "") and o["derp_lpp"] == ("", "")
    assert _posta(z) == {}
    z["uvoz"]["od"] = T - 16 * 60
    assert zdravje.ocena(z, STROJ, T)["zanka"][0] == zdravje.ORANZNA
    assert set(_posta(z)) == {"zanka"} and not _posta(z)["zanka"].nujno

    z["uvoz"] = {"od": T - 3600, "do": T - 3300}                # brez uvoza
    assert zdravje.ocena(z, STROJ, T)["zanka"] == (zdravje.DOBRA, "")
    z["zanka_ts"] = T - 11 * 60
    assert zdravje.ocena(z, STROJ, T)["zanka"][0] == zdravje.SLABA
    z["uvoz"] = {"od": T - 9 * 3600, "do": None}                # prekinjen z zagonom
    assert zdravje.ocena(z, STROJ, T)["zanka"][0] == zdravje.SLABA
    assert set(_posta(z)) == {"zanka"} and _posta(z)["zanka"].nujno


def test_uvoz_zapise_zacetek_in_konec(monkeypatch):
    """`meta.uvoz` ve, da uvoz teče, in ga zapre tudi ob napaki."""
    import pytest
    from kajros import db, server

    c = db.connect(":memory:")
    db.init(c)

    def pade(conn, mode):
        assert json.loads(db.get_meta(conn, "uvoz"))["do"] is None
        raise RuntimeError("zip ni zip")
    monkeypatch.setattr(server, "_uvozi", pade)
    with pytest.raises(RuntimeError):
        server.refresh_timetable(c, "subprocess")
    uv = json.loads(db.get_meta(c, "uvoz"))
    assert uv["od"] <= uv["do"]


def test_nocni_uvoz_in_opravila(monkeypatch):
    """Izid nočnega uvoza in opravil je bil samo v dnevniku. Rumeno ena
    neuspela noč, oranžno dve zapored ali padec prevoznika nad 40 %."""
    from kajros import db, gtfs, server

    c = db.connect(":memory:")
    db.init(c)

    def zavrni(conn, mode):
        raise gtfs.UvozZavrnjen("zip nima nobene vožnje prevoznika 1161")
    monkeypatch.setattr(server, "_uvozi", zavrni)
    for _ in range(2):
        try:
            server.refresh_timetable(c, "subprocess")
        except gtfs.UvozZavrnjen:
            pass
        uv = json.loads(db.get_meta(c, "uvoz"))
        z = {**_zdravo(), "uvoz": uv, "nocno": {}}
        o = zdravje.ocena(z, STROJ, T)["nocno"]
        assert "uvoz voznega reda zavrnjen" in o[1] and "1161" in o[1]
        assert o[0] == (zdravje.MLACNA if uv["neuspelih"] == 1 else zdravje.ORANZNA)
    assert uv["neuspelih"] == 2 and set(_posta(z)) == {"nocno"}

    monkeypatch.setattr(server, "_uvozi", lambda conn, mode: {
        "izid": "ok", "prevozniki": {"kranj": [446, 309], "1123": [9593, 9600]}})
    server.refresh_timetable(c, "subprocess")
    uv = json.loads(db.get_meta(c, "uvoz"))
    assert uv["neuspelih"] == 0 and uv["izid"] == "ok"
    z = {**_zdravo(), "uvoz": uv, "nocno": {}}
    assert zdravje.ocena(z, STROJ, T)["nocno"] == (zdravje.DOBRA, "")   # konec meseca MOK
    z["uvoz"]["prevozniki"]["1123"] = [9593, 5000]
    o = zdravje.ocena(z, STROJ, T)["nocno"]
    assert o[0] == zdravje.ORANZNA and "1123 9593 → 5000" in o[1]

    # Opravila: noči zapored; star niz (opravilo ne teče več) odpade.
    z["uvoz"]["prevozniki"]["1123"] = [9593, 9600]
    z["nocno"] = {"povzetki": {"zapored": 1, "ts": T - 3600, "napaka": "OperationalError: x",
                               "kje": "stats.py:1 refresh_summaries"}}
    o = zdravje.ocena(z, STROJ, T)["nocno"]
    assert o[0] == zdravje.MLACNA and "povzetki: 1. noč" in o[1]
    z["nocno"]["povzetki"]["zapored"] = 2
    assert zdravje.ocena(z, STROJ, T)["nocno"][0] == zdravje.ORANZNA
    z["nocno"]["povzetki"]["ts"] = T - 4 * 86400
    assert zdravje.ocena(z, STROJ, T)["nocno"] == (zdravje.DOBRA, "")


def test_zavrnjena_prijava_nap_v_posti_po_uri():
    z = _zdravo()
    z["nap"] = {"ts": T - 20 * 60, "http": 401, "napaka_ts": T - 60}
    assert zdravje.ocena(z, STROJ, T)["nap"][0] == zdravje.MLACNA
    assert "nap" not in _posta(z)
    z["nap"]["ts"] = T - 2 * 3600
    assert "deploy/nap.sh" in _posta(z)["nap"].ukrep


def test_mrtva_nit_in_vozni_red_v_posti():
    z = _zdravo()
    z["vozni_red"] = {"zeleznica": "2026-10-02", "avtobus": "2027-12-31"}
    m = {**STROJ, "niti": ["kajros-collector"],
         "pricakovane_niti": {"kajros-collector": ["derp_zamude"], "kajros-nap": ["nap"]}}
    assert set(_posta(z, m)) == {"vozni_red", "nit:kajros-nap"}
    assert "kajros update" in _posta(z, m)["vozni_red"].ukrep


def test_ponoci_vrstice_zajema_niso_ocenjene():
    """Ko nič ne vozi, pošta ne ve, ali je okvara mimo: None, ne „v redu“."""
    z = _zdravo()
    z["vozi_zdaj"] = {"zeleznica": 0, "avtobus": 1}
    z["zamude_sz"] = {"ts": T - 2 * 3600}
    p = _posta(z, vse=True)
    assert p.get("feed", 1) is None and p.get("zeleznica", 1) is None
    assert p.get("zamude_sz", 1) is None


def test_jutro_molk_od_zacetka_prometa():
    """Vsako jutro 7.–17. 10. 2026 ob ~3:58: „vlaki: zadnji zapis pred 2,6 h“.
    Zadnji nočni zapis je iz 1:22; prvi vlaki po voznem redu vozijo od 3:20.
    Molk šteje od začetka prometa (`stats.promet_od`), ne od noči."""
    z = _zdravo()
    z["vozi_zdaj"] = {"zeleznica": 5, "avtobus": 30}
    z["by_network"]["zeleznica"]["last_feed_ts"] = T - 2.6 * 3600
    assert "zeleznica" in _rdece(z)
    z["promet_od"] = {"zeleznica": T - 10 * 60, "avtobus": T - 3600}
    assert _rdece(z) == set()
    z["promet_od"]["zeleznica"] = T - 70 * 60        # promet teče 70 min, zapisa ni
    assert "zeleznica" in _rdece(z)


def test_stats_promet_od_zacne_po_nocnem_presledku():
    """`stats.promet_od`: od kdaj vozijo vsaj tri vožnje, vsaka vsaj četrt
    ure. Nočni vlak ob 0:17 ne šteje -- za njim je presledek."""
    from kajros import db, stats
    c = db.connect(":memory:")
    db.init(c)
    dan = "2026-10-17"
    c.execute("INSERT INTO service_day(service_id, date) VALUES('S', ?)", (dan,))
    voznje = [("zeleznica", 17 * 60, 3600), ("zeleznica", 3 * 3600 + 1200, 3600),
              ("zeleznica", 3 * 3600 + 2100, 3600), ("zeleznica", 3 * 3600 + 2400, 3600),
              ("zeleznica", 5 * 3600, 3600), ("avtobus", 4 * 3600, 3600)]
    for i, (omr, start, traja) in enumerate(voznje):
        c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, network, "
                  "start_s, end_s) VALUES(?, 'r', ?, 'S', 'rail', ?, ?, ?)",
                  (f"t{i}", f"LP {i}", omr, start, start + traja))
    p = stats.polnoc(dan)
    assert stats.promet_od(c, p + 4 * 3600) == {"zeleznica": p + 3 * 3600 + 2400 + 900}
    assert stats.promet_od(c, p + 2 * 3600) == {}          # ponoči ne vozi nič
    # Ob 4:50 vozita le še dva od treh: promet se je prekinil.
    assert stats.promet_od(c, p + 4 * 3600 + 3000) == {}


def test_obrez_dnevnika_po_kosih(monkeypatch):
    """17. 10. 2026: obrez 1,86 mio vrstic v eni transakciji je držal zapis
    do 116 s -- „database is locked“ v petih nitih vsako noč ob 3:30. Po kosih
    pobriše isto, nove vrstice in drugo omrežje ostanejo."""
    from datetime import datetime, timedelta
    from kajros import collector, db
    monkeypatch.setattr(collector, "PRUNE_PREMOR_S", 0)
    c = db.connect(":memory:")
    db.init(c)
    danes = datetime.now(collector.TZ).date()
    staro, novo = (danes - timedelta(days=100)).isoformat(), danes.isoformat()
    sredina = (danes - timedelta(days=30)).isoformat()
    for tid, omr in (("v", "zeleznica"), ("b", "avtobus")):
        c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, network) "
                  "VALUES(?, 'r', ?, 'S', 'bus', ?)", (tid, tid, omr))
    vrstice = [(tid, dan, seq, 60, ts, ts) for tid in "vb" for dan in (staro, sredina, novo)
               for seq in range(1, 8) for ts in (1, 2)]
    c.executemany("INSERT INTO obs(trip_id, service_date, stop_seq, delay_dep, feed_ts, "
                  "observed_at) VALUES(?, ?, ?, ?, ?, ?)", vrstice)
    c.commit()
    izid = collector.prune_obs(c, 90, 14, kos=3, prestej=True)
    assert (izid["rail_deleted"], izid["bus_deleted"]) == (14, 28)
    ostane = [tuple(r) for r in c.execute("SELECT trip_id, service_date, COUNT(*) FROM obs "
                                          "GROUP BY 1, 2 ORDER BY 1, 2")]
    assert ostane == [("b", novo, 14), ("v", sredina, 14), ("v", novo, 14)]
    assert izid["obs_left"] == 42
    assert collector.prune_obs(c, 90, 14, kos=3) == {
        "rail_deleted": 0, "rail_before": izid["rail_before"],
        "bus_deleted": 0, "bus_before": izid["bus_before"]}


# --- stopnje: rdeče takoj, oranžno za pregled, rumeno za vedenje (31. 10. 2026)


def test_molk_omrezja_je_rdec_ko_potniki_vidijo_obvestilo():
    """Do 31. 10. 2026 je bil molk vlakov do ure le rumen, pošta po 70 min;
    potniki pa so obvestilo „ne dobivamo podatkov“ videli že po 20 min."""
    from kajros import obvestila
    assert zdravje.OMREZJE_MOLCI_S == obvestila.MOLCI_S
    z = _zdravo()
    z["vozi_zdaj"] = {"zeleznica": 20, "avtobus": 300}
    z["svezina"] = {"zeleznica": T - 19 * 60, "avtobus": T - 30}
    assert zdravje.ocena(z, STROJ, T)["zeleznica"][0] == zdravje.DOBRA
    z["svezina"]["zeleznica"] = T - 21 * 60
    assert zdravje.ocena(z, STROJ, T)["zeleznica"][0] == zdravje.SLABA


def test_oranzno_samo_podnevi_rdece_takoj():
    """Oranžna ni nujna: ponoči počaka do jutra. Rdeča zvoni tudi ponoči."""
    noc = 1_790_890_000.0                     # 1. 10. 2026 ~23:26
    assert not zdravje.podnevi(noc) and zdravje.podnevi(T)
    oranzna = {"skladnost_sz": zdravje.Okvara("x", "y", 600, nujno=False)}
    stanje, sp, _, _ = opozorila.korak({}, oranzna, noc)
    stanje, sp, nove, _ = opozorila.korak(stanje, oranzna, noc + 3600)
    assert sp is None and nove == []
    jutro = 1_790_917_200.0                   # 2. 10. 2026 7:00
    stanje, sp, nove, _ = opozorila.korak(stanje, oranzna, jutro)
    assert nove == ["skladnost_sz"] and sp[0].startswith("kajros: za pregled -- x")
    assert "Za pregled s Claude" in sp[1]
    rdeca = {"wal": zdravje.Okvara("w", "z")}
    stanje2, _, _, _ = opozorila.korak({}, rdeca, noc)
    _, sp, nove, _ = opozorila.korak(stanje2, rdeca, noc + ZAMIK_S)
    assert nove == ["wal"] and sp[0].startswith("kajros: stoji -- w")


def test_oranzna_ki_postane_rdeca_gre_znova():
    """Vozni red teden prej oranžen (poslano), dva dni prej rdeč: znova."""
    o = {"vozni_red": zdravje.Okvara("se konča čez 5 dni", "u", 600, nujno=False)}
    stanje, _, _, _ = opozorila.korak({}, o, T)
    stanje, sp, nove, _ = opozorila.korak(stanje, o, T + 600)
    stanje = opozorila._potrdi(stanje, nove, [], T + 600)
    _, sp, nove, _ = opozorila.korak(stanje, o, T + 1200)
    assert sp is None
    r = {"vozni_red": zdravje.Okvara("se konča jutri", "u", 600)}
    _, sp, nove, _ = opozorila.korak(stanje, r, T + 86400)
    assert nove == ["vozni_red"] and sp[0].startswith("kajros: stoji -- se konča jutri")


def test_sled_prezivi_zagon_in_pozabi_staro():
    sled = zdravje.Sled()
    assert sled.koliko("a", True, T) == 0
    assert sled.koliko("a", True, T + 600) == 600
    obnovljena = zdravje.Sled(sled.stanje(T + 600))
    assert obnovljena.koliko("a", True, T + 900) == 900
    assert obnovljena.koliko("a", False, T + 960) == 0
    assert obnovljena.koliko("a", True, T + 1000) == 0
    # Ključ, ki ga nihče ne vpraša dan dolgo, odpade.
    assert "a" not in obnovljena.stanje(T + 1000 + 86401)


def test_primeri_vozil_so_povezave_na_zemljevid():
    """David, 31. 10. 2026: ob vrstici povezava na zemljevid z izbranim vozilom."""
    z = {"lega_brez_zamude_primeri": {"Arriva": [
            {"trip_id": "432192", "vozilo": "1301553", "lat": 45.754, "lon": 14.048,
             "oznaka": "A8426 → Ljubljana AP - Koper"}]},
         "vozila_brez_voznje": {"LPP": [{"vozilo": "d5498517", "lat": 46.048, "lon": 14.5014,
                                         "oznaka": "LPP 2 → ZELENA JAMA - NOVE JARŠE"}]}}
    p = zdravje.primeri(z)
    assert p["lega_brez_zamude"] == [{"oznaka": "Arriva A8426 → Ljubljana AP - Koper",
                                      "pot": "/app/map?trip=432192&lat=45.75400&lon=14.04800&z=16"}]
    assert p["neznane"][0]["pot"] == "/app/map?vozilo=d5498517&lat=46.04800&lon=14.50140&z=16"
