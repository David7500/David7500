"""Stran v aplikaciji za Android ne sme izdati, da je v WebView.

Prijavljeno 26. 9. 2026: gumbi so modri, ko jih pritisneš. Modro je Chromov
`tap-highlight`; namesto njega ima `base.css` plast v barvi besedila. Drugi
znak je `:hover`, ki na zaslonu na dotik obvisi na zadnjem pritisnjenem
elementu -- zato sme stati samo znotraj `@media (hover: hover)`. Pravilo je
v devetih datotekah in brez preizkusa bi ga naslednja nova vrstica pozabila.
"""
from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "kajros/static"
# Pregled je za skrbnika na računalniku, ne za telefon.
IZJEME = {"admin.css"}


def test_hover_samo_za_misko():
    napake = []
    for css in sorted(STATIC.glob("*.css")):
        if css.name in IZJEME:
            continue
        for st, vrstica in enumerate(css.read_text().splitlines(), 1):
            # Drsnik je na telefonu prekrivni in ga miška niti ne doseže.
            if ":hover" in vrstica and "@media (hover: hover)" not in vrstica \
                    and "scrollbar" not in vrstica:
                napake.append(f"{css.name}:{st}: {vrstica.strip()}")
    assert not napake, "\n".join(napake)


def test_brez_brskalniskih_barv():
    css = (STATIC / "base.css").read_text()
    assert "-webkit-tap-highlight-color: transparent" in css
    assert "color-scheme: dark" in css
    assert "accent-color: var(--accent)" in css
    # Dolg pritisk na povezavo je začel vleko z oblačkom naslova.
    assert "-webkit-user-drag: none" in css
