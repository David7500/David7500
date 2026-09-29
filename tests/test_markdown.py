"""Markdown za agente: pretvorba strani in odločitev, kdaj ga postreči.

    ./venv/bin/python -m pytest tests/test_markdown.py -q
"""
from __future__ import annotations

import pytest

from kajros import markdown

NASLOV = "https://kajros.app/vlak/ljubljana/maribor"


@pytest.mark.parametrize("accept, pricakovano", [
    ("text/markdown", True),
    ("text/markdown, text/html;q=0.5", True),
    ("text/markdown;q=0.9, text/html", False),
    ("text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", False),
    ("*/*", False),          # curl in iskalniki: Markdowna ne zahtevajo
    ("text/markdown;q=0", False),
    ("", False),
])
def test_zeli_markdown(accept, pricakovano):
    assert markdown.zeli_markdown(accept) is pricakovano


def test_naslovi_povezave_in_krepko():
    md = markdown.iz_html(
        '<h1>Vlak A → B</h1><p>Danes pelje <b>10</b> vožnj, '
        '<a href="/postaja/a">tabla</a>.</p>', NASLOV)
    assert md == ("# Vlak A → B\n\n"
                  "Danes pelje **10** vožnj, [tabla](https://kajros.app/postaja/a).\n")


def test_tabela_ima_glavo_in_vrstice():
    md = markdown.iz_html(
        "<table><thead><tr><th>Odhod</th><th>Zamuda</th></tr></thead>"
        "<tbody><tr><td>05:00</td><td>+3 min</td></tr>"
        "<tr><td>06:00</td><td>0 min</td></tr></tbody></table>", NASLOV)
    assert md == ("| Odhod | Zamuda |\n|---|---|\n| 05:00 | +3 min |\n"
                  "| 06:00 | 0 min |\n")


def test_seznam_je_brez_praznih_vrstic_med_alinejami():
    md = markdown.iz_html(
        '<ul><li><a href="/a"><span>Vlak A</span><span>1 km</span></a></li>'
        '<li>drugi</li></ul>', NASLOV)
    assert md == "- [Vlak A 1 km](https://kajros.app/a)\n- drugi\n"


def test_skripta_slog_svg_glava_in_skrito_odpadejo():
    md = markdown.iz_html(
        "<html><head><title>T</title><style>p{}</style></head><body>"
        "<script>var x = '<p>ne</p>';</script><svg><path/></svg>"
        '<p hidden>skrito</p><nav><a href="/x">meni</a></nav>'
        "<p>ostane</p></body></html>", NASLOV)
    assert md == "ostane\n"


def test_povezava_brez_cilja_ostane_besedilo():
    md = markdown.iz_html('<p><a href="#">gumb</a> in <a>sidro</a></p>', NASLOV)
    assert md == "gumb in sidro\n"


def test_stran_z_glavo_in_tabelo_ima_naslov_in_vrstice():
    """Oblika pristajalne strani: prazen izpis bi bil tiha napaka."""
    html = ('<main><h1>Vlak Ljubljana → Maribor</h1><h2>Odhodi danes</h2>'
            '<table class="odhodi"><thead><tr><th>Odhod</th></tr></thead>'
            "<tbody><tr><td>05:00</td></tr></tbody></table></main>")
    md = markdown.iz_html(html, NASLOV)
    assert md.startswith("# Vlak Ljubljana → Maribor\n\n## Odhodi danes\n\n")
    assert "| 05:00 |" in md
