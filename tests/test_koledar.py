"""Koledar v `/admin`: izris `KOLEDAR.md` (`koledar.py`) in pot `/admin/koledar`.

Izris je lasten, zato tu varujemo dvoje: da je izpis tisto, kar je napisano
(tabela je tabela, cev v kodi ni meja stolpca), in da iz datoteke, ki jo pišejo
seje in agenti, ne more priti nič, kar bi se v skrbniškem pregledu izvedlo.

    ./venv/bin/python -m pytest tests/test_koledar.py -q
"""
from __future__ import annotations

import re
from datetime import date
from fnmatch import fnmatch
from html.parser import HTMLParser
from pathlib import Path

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from kajros import api, config, koledar

KOREN = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- izris

def test_tabela_postane_tabela():
    h = koledar.izrisi("## Roki\n\n| kdaj | kaj |\n|---|---|\n"
                       "| 1. 11. 2026 | **prvi** |\n| 2. 11. 2026 | drugi |\n")
    assert h.count("<table") == 1
    assert "<th>kdaj</th><th>kaj</th>" in h
    assert h.count("<tr") == 3                          # glava in dve vrstici
    assert "<td><strong>prvi</strong></td>" in h
    assert "|---|" not in h
    # Okvir, ki se drsi sam: na telefonu stran ne sme dobiti vodoravnega drsnika.
    assert h.count('class="adm-ovoj-t"') == 1


def test_cev_v_kodi_ni_meja_stolpca():
    """Ukazi v stolpcu „kako“ imajo cevi: `\\|` je cev, ne konec celice."""
    h = koledar.izrisi("| a | b |\n|---|---|\n| `x \\| cut -c1-9` | z |\n")
    assert "<td><code>x | cut -c1-9</code></td><td>z</td>" in h


def test_brez_locila_ni_tabele():
    h = koledar.izrisi("| a | b |\n| c | d |\n")
    assert "<table" not in h
    assert h.count("<p>") == 1                          # besedilo se ne izgubi


def test_ploscica_na_razdelek_alineje_in_odstavki():
    h = koledar.izrisi(
        "# Naslov\n\nprva vrstica\ndruga vrstica\n\n## Razdelek\n\n"
        "* ena\n  nadaljevanje\n\n* dve\n\n### Podnaslov\n\nkonec\n")
    assert h.count("<section") == 2
    assert "<h2>Naslov</h2>" in h and "<h2>Razdelek</h2>" in h and "<h3>Podnaslov</h3>" in h
    assert "<p>prva vrstica druga vrstica</p>" in h     # odstavek je en odstavek
    assert "<ul><li>ena nadaljevanje</li><li>dve</li></ul>" in h


def test_datum_na_zacetku_vrstice_ni_oštevilčen_seznam():
    """„1. 11. 2026“ je datum, ne prva točka seznama."""
    h = koledar.izrisi("1. 11. 2026 je ponedeljek.\n")
    assert "<ol" not in h and "<li>" not in h
    assert "<p>1. 11. 2026 je ponedeljek.</p>" in h


def test_koda_ni_krepka_krepko_lahko_nosi_kodo():
    assert "<code>**x**</code>" in koledar.izrisi("`**x**`")
    assert "<strong>a <code>b</code> c</strong>" in koledar.izrisi("**a `b` c**")
    # Nezaprto ostane, kar je bilo napisano.
    assert "<strong>" not in koledar.izrisi("**nezaprto")


def test_povezava_na_datoteko_ni_mrtva_povezava():
    h = koledar.izrisi("[docs/A.md](docs/A.md), [predaji](docs/b.md), "
                       "[vir](https://primer.si/a?b=1&c=2)")
    assert "<code>docs/A.md</code>, " in h              # enaka pot: samo koda
    assert "predaji <code>docs/b.md</code>" in h        # besedilo in pot
    assert h.count("<a ") == 1                          # `href` samo za splet
    assert ('<a href="https://primer.si/a?b=1&amp;c=2" target="_blank" '
            'rel="noopener noreferrer">vir</a>') in h


class _Oznake(HTMLParser):
    """Oznake in atributi izpisa, da se escapiranje preveri po zgradbi in ne po nizu."""

    def __init__(self):
        super().__init__()
        self.oznake: set[str] = set()
        self.atributi: list[tuple[str, str | None]] = []

    def handle_starttag(self, tag, attrs):
        self.oznake.add(tag)
        self.atributi += attrs


def test_izris_escapira_html():
    """Nič iz datoteke ne postane oznaka ali atribut, ki ga mi nismo napisali."""
    zlo = ("# <script>alert(1)</script> naslov\n\n"
           "Odstavek <img src=x onerror=alert(1)> in **<b>krepko</b>** ter `<script>koda</script>`.\n\n"
           "* alineja <iframe src=\"//zlo\"></iframe>\n\n"
           "| <u>glava</u> | b |\n|---|---|\n"
           "| <script>alert(2)</script> | [klik](javascript:alert(3)) |\n"
           "| [vir](https://primer.si/a?b=1&c=\"><script>alert(4)</script>) | [x](data:text/html;base64,AAAA) |\n"
           "| [y](https://primer.si/\" onmouseover=\"alert(5)) | c |\n\n"
           "```\n<script>alert(6)</script>\n```\n")
    h = koledar.izrisi(zlo, date(2026, 11, 1))
    p = _Oznake()
    p.feed(h)
    assert p.oznake <= {"div", "section", "h2", "h3", "p", "ul", "li", "table", "thead", "tbody",
                        "tr", "th", "td", "strong", "code", "a", "pre", "hr"}, p.oznake
    assert {k for k, _ in p.atributi} <= {"class", "style", "href", "target", "rel"}, p.atributi
    hrefi = [v for k, v in p.atributi if k == "href"]
    assert hrefi and all(v.startswith(("http://", "https://")) for v in hrefi), hrefi
    # Pretvorba za vsako besedilo posebej: nobena dobesedna oznaka ne ostane.
    for oznaka in ("<script", "<img", "<iframe", "<u>", "<b>"):
        assert oznaka not in h, oznaka


def test_znak_nul_ne_more_ponarediti_zascitene_kode():
    """Zaščitena koda in povezave so v besedilu označbe z znakom NUL; datoteka
    ga ne sme nositi, sicer bi ponarejena označba z neobstoječo številko
    sprožila napako, z obstoječo pa tuj kos besedila."""
    h = koledar.izrisi("`a` \x000\x00 \x00999\x00")
    assert "\x00" not in h and h.count("<code>") == 1


def test_zapadle_vrstice_samo_v_na_vrsti():
    md = ("## Na vrsti\n\n| kdaj | kaj |\n|---|---|\n"
          "| **sob 31. 10. 2026** | prej |\n"
          "| ned 1. 11. 2026, 16.30 | danes |\n"
          "| pon 2. 11. 2026 | jutri |\n"
          "| 31. 2. 2026 | nemogoč datum |\n"
          "| po objavi | brez datuma |\n\n"
          "## Opravljeno\n\n| kdaj | kaj |\n|---|---|\n| sob 31. 10. 2026 | staro |\n")
    h = koledar.izrisi(md, date(2026, 11, 1))
    assert h.count("je-zapadlo") == 2                   # prej in danes
    assert "je-zapadlo" not in h[h.index("<h2>Opravljeno</h2>"):]
    assert "je-zapadlo" not in koledar.izrisi(md)       # brez „danes“ nič ni zapadlo


def test_dolg_stolpec_se_loci_po_vidnem_besedilu():
    """Povezava `[pot](pot)` ima pot v zapisu dvakrat, vidno pa enkrat."""
    dolgo = "beseda " * 20
    h = koledar.izrisi(f"| kratko | dolgo |\n|---|---|\n| [docs/X.md](docs/X.md) | {dolgo} |\n")
    assert '<th>kratko</th><th class="dolg">dolgo</th>' in h


# ---------------------------------------------------------------- datoteka

def test_datoteke_ni_pogled_pove_in_ne_pade(tmp_path, monkeypatch):
    monkeypatch.setattr(koledar, "DATOTEKA", tmp_path / "ni.md")
    odgovor = koledar.pregled(date(2026, 11, 1))
    assert "koledarja ni" in odgovor["html"] and odgovor["spremenjeno"] is None
    # Prazna datoteka in mapa namesto datoteke sta isto.
    prazna = tmp_path / "prazna.md"
    prazna.write_text("  \n", encoding="utf-8")
    monkeypatch.setattr(koledar, "DATOTEKA", prazna)
    assert "koledarja ni" in koledar.pregled(date(2026, 11, 1))["html"]
    monkeypatch.setattr(koledar, "DATOTEKA", tmp_path)
    assert "koledarja ni" in koledar.pregled(date(2026, 11, 1))["html"]


def test_datoteka_se_prebere_ob_vsaki_zahtevi(tmp_path, monkeypatch):
    d = tmp_path / "KOLEDAR.md"
    monkeypatch.setattr(koledar, "DATOTEKA", d)
    d.write_text("## Prvi\n\nbesedilo\n", encoding="utf-8")
    assert "<h2>Prvi</h2>" in koledar.pregled(date(2026, 11, 1))["html"]
    d.write_text("## Drugi\n\nbesedilo\n", encoding="utf-8")      # brez ponovnega zagona
    odgovor = koledar.pregled(date(2026, 11, 1))
    assert "<h2>Drugi</h2>" in odgovor["html"] and isinstance(odgovor["spremenjeno"], int)
    d.write_bytes(b"## Neveljaven \xff\xfe znak\n")               # ne pade na kodiranju
    assert "<h2>" in koledar.pregled(date(2026, 11, 1))["html"]


def test_pravi_koledar_se_izrise():
    assert koledar.DATOTEKA == KOREN / "KOLEDAR.md" and koledar.DATOTEKA.is_file()
    h = koledar.izrisi(koledar.DATOTEKA.read_text(encoding="utf-8"), date(2026, 11, 1))
    assert h.count("<table") >= 1
    assert "|---" not in h, "tabela ni prepoznana in je ostala besedilo"
    # Po tem razdelku se barvajo zapadli roki: preimenovanje bi tiho izklopilo barvanje.
    assert f"<h2>{koledar.NA_VRSTI}</h2>" in h, "razdelek v KOLEDAR.md je preimenovan: popravi koledar.NA_VRSTI"


def test_objava_prenese_koledar():
    """`deploy/posodobi.sh` prepiše celo drevo v `/opt/kajros`, koledar ob kodi
    pa je tam le, dokler ga noben `--exclude` ne ujame."""
    sh = (KOREN / "deploy" / "posodobi.sh").read_text(encoding="utf-8")
    izkljuceno = re.findall(r"--exclude\s+'([^']+)'", sh)
    assert izkljuceno, "oblika rsync ukaza se je spremenila: popravi ta preizkus"
    assert [p for p in izkljuceno if not p.endswith("/") and fnmatch("KOLEDAR.md", p)] == []
    assert (koledar.DATOTEKA.parent / "kajros" / "koledar.py").is_file()


# ---------------------------------------------------------------- pot /admin/koledar

def _zahteva(poizvedba: bytes = b"", piskotek: str | None = None) -> Request:
    glave = [(b"host", b"kajros.app")]
    if piskotek:
        glave.append((b"cookie", f"{api.ADMIN_PISKOTEK}={piskotek}".encode()))
    return Request({"type": "http", "method": "GET", "path": "/admin/koledar",
                    "raw_path": b"/admin/koledar", "query_string": poizvedba,
                    "headers": glave, "scheme": "https", "server": ("kajros.app", 443)})


def test_pogled_z_zetonom_vrne_vsebino(tmp_path, monkeypatch):
    d = tmp_path / "KOLEDAR.md"
    d.write_text("## Na vrsti\n\n| kdaj | kaj |\n|---|---|\n| 1. 1. 2020 | staro |\n", encoding="utf-8")
    monkeypatch.setattr(koledar, "DATOTEKA", d)
    monkeypatch.setattr(config, "ADMIN_TOKEN", "zeton")
    for zahteva in (_zahteva(piskotek="zeton"), _zahteva(b"k=zeton")):
        odgovor = api.admin_koledar(zahteva)
        assert "<table" in odgovor["html"] and "je-zapadlo" in odgovor["html"]
        assert isinstance(odgovor["spremenjeno"], int)


@pytest.mark.parametrize("pot", ["admin_koledar", "admin_podatki", "admin_deljenje",
                                 "admin_viri_preveri"])
def test_brez_zetona_isto_kot_ostali_admin(monkeypatch, pot):
    """Brez žetona 404 (poti ni), napačen 403, brez nastavljenega žetona 404."""
    funkcija = getattr(api, pot)
    monkeypatch.setattr(config, "ADMIN_TOKEN", "pravi")
    with pytest.raises(HTTPException) as e:
        funkcija(_zahteva())
    assert e.value.status_code == 404
    with pytest.raises(HTTPException) as e:
        funkcija(_zahteva(piskotek="napacen"))
    assert e.value.status_code == 403
    monkeypatch.setattr(config, "ADMIN_TOKEN", "")
    with pytest.raises(HTTPException) as e:
        funkcija(_zahteva(piskotek="pravi"))
    assert e.value.status_code == 404


def test_pot_je_samo_get_in_ni_v_shemi():
    poti = [r for r in api.app.routes if getattr(r, "path", None) == "/admin/koledar"]
    assert len(poti) == 1
    assert poti[0].methods == {"GET", "HEAD"}
    assert poti[0].include_in_schema is False
