"""Lastna lega gre skozi en sam kraj: `common.js` (`LEGA`, `stanjeLege`).

Od 22. 10. 2026 lega teče sama, kadar je dovoljenje že dano, okna za
dovoljenje pa stran še vedno ne odpre sama (David). Obe polovici pravila
držita samo, dokler je pot do lege ena: kopija `watchPosition` v datoteki
zemljevida bi tekla brez preverjanja dovoljenja -- in v aplikaciji sprožila
sistemsko okno, ki ga nihče ni prosil -- ali pa ob skriti strani ne bi
ugasnila GPS.
"""
from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "kajros/static"

#: Deljenje lege ima svojo pot: tam je lega privolitev v pošiljanje, ne
#: prikaz (`deljenje.md`), in jo sproži samo dotik „Deli lego“.
SMEJO = {"common.js", "deli.js"}


def _kje(niz: str) -> set[str]:
    return {js.name for js in STATIC.rglob("*.js") if niz in js.read_text(encoding="utf-8")}


def test_geolocation_samo_v_skupni_kodi():
    tuji = _kje("navigator.geolocation") - SMEJO
    assert not tuji, f"lego beri prek `LEGA` / `poisciMe` iz common.js, ne sam: {sorted(tuji)}"


def test_dovoljenje_bere_samo_skupna_koda():
    # V aplikaciji `navigator.permissions` ne obstaja (WebView 124), resnica je
    # most (`Most.dovoljenja`, `lega`). `stanjeLege()` ve za oboje.
    tuji = _kje("navigator.permissions") - {"common.js"}
    assert not tuji, f"stanje dovoljenja beri s `stanjeLege()`: {sorted(tuji)}"
