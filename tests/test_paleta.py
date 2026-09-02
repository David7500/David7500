"""Paleta živi v treh kopijah in nič je doslej ni varovalo.

`base.css` jo ima kot spremenljivke, `common.js` kot `DELAY_RAMP` in
`SEVERITY_STYLE`, `scripts/preveri_paleto.py` pa svojo, s katero meri kontrast
in barvno slepoto. Komentar v skripti obljublja, da so iste ("Isti zapisi kot
v static/base.css"), a te obljube ni preverjal nihče -- in tiho razhajanje bi
pomenilo, da validator potrjuje barve, ki jih prikaz ne uporablja.
"""
import re
from pathlib import Path

KOREN = Path(__file__).resolve().parent.parent
CSS = (KOREN / "kajros/static/base.css").read_text()
JS = (KOREN / "kajros/static/common.js").read_text()
SKRIPTA = (KOREN / "scripts/preveri_paleto.py").read_text()


def _css(ime: str) -> str:
    m = re.search(rf"--{ime}:\s*(#[0-9a-fA-F]{{6}})", CSS)
    assert m, f"v base.css ni spremenljivke --{ime}"
    return m.group(1).lower()


def _js_ramp() -> list[str]:
    blok = re.search(r"const DELAY_RAMP = \[(.*?)\];", JS, re.S).group(1)
    return [c.lower() for c in re.findall(r'color:\s*"(#[0-9a-fA-F]{6})"', blok)]


def _js_severity() -> list[str]:
    blok = re.search(r"const SEVERITY_STYLE = \{(.*?)\};", JS, re.S).group(1)
    return [c.lower() for c in re.findall(r'"(#[0-9a-fA-F]{6})"', blok)]


def _skripta(ime: str) -> list[str]:
    blok = re.search(rf"^{ime} = \[(.*?)\]", SKRIPTA, re.S | re.M).group(1)
    return [c.lower() for c in re.findall(r'"(#[0-9a-fA-F]{6})"', blok)]


def test_lestvica_zamud_je_povsod_ista():
    css = [_css(x) for x in ("d-ontime", "d-small", "d-mid", "d-big")]
    assert css == _js_ramp(), "base.css in common.js se razhajata"
    assert css == _skripta("DELAY_RAMP"), "base.css in preveri_paleto.py se razhajata"


def test_semafor_razmer_je_povsod_isti():
    css = [_css(x) for x in ("sev-calm", "sev-mild", "sev-hard", "sev-bad")]
    assert css == _js_severity(), "base.css in common.js se razhajata"
    assert css == _skripta("SEVERITY"), "base.css in preveri_paleto.py se razhajata"


def test_rezervirana_barva_ni_v_lestvici():
    """`--d-none` pomeni 'meritve ni'. Ce zaide v lestvico zamud, barva nosi
    dva pomena in prikaz laze."""
    rezervirana = _css("d-none")
    assert rezervirana not in _js_ramp()
    assert rezervirana not in _js_severity()
    assert rezervirana in _skripta("RESERVED")


def test_okno_voznje_uporablja_rezervirano_barvo_za_oceno():
    """Ocena lege ni meritev in mora biti v rezervirani barvi, ne v zeleni."""
    train = (KOREN / "kajros/static/train.js").read_text()
    m = re.search(r'const ESTIMATE_COLOR = "(#[0-9a-fA-F]{6})"', train)
    assert m, "train.js nima ESTIMATE_COLOR"
    assert m.group(1).lower() == _css("d-none")
