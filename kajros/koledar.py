"""Koledar v `/admin`: `KOLEDAR.md` iz korena repozitorija, izrisan v HTML.

Skupni seznam rokov za Davida in Claude (skill `koledar`). Datoteka je edini
vir: tu se ob vsaki zahtevi prebere in izriše, zato prikaz nikoli ni starejši
od datoteke in ne rabi ponovnega zagona. Pot je ob kodi in ne v domači mapi:
`deploy/posodobi.sh` prepiše vse drevo v `/opt/kajros`, torej je koledar na
strežniku tam, kjer ga najde tudi razvoj (`test_objava_prenese_koledar`).

Izris je lasten in majhen, brez odvisnosti (`requirements.txt` ima pet vrstic):
naslovi, odstavki, alineje, tabele s cevmi, **krepko**, `koda` in
[povezave](pot). Karkoli drugega ostane besedilo.

**Vse besedilo gre skozi `html.escape`, preden dobi oznake.** Datoteko pišejo
seje in agenti, ki vanjo prepisujejo tudi izpise ukazov in tuja besedila, zato
„je naše“ ne zadošča. `href` dobi samo `http(s)://`; pot v repozitoriju
(`docs/…`) na strežniku ni naslov, zato je koda in ne mrtva povezava.
"""
from __future__ import annotations

import html
import re
from datetime import date
from pathlib import Path

DATOTEKA = Path(__file__).resolve().parent.parent / "KOLEDAR.md"

#: Stolpec, v katerem je kakšna celica daljša od tega, je „dolg“ (`.dolg`).
DOLG_STOLPEC = 80

#: Razdelek z roki. Njegove vrstice z datumom danes ali prej so zapadle in se
#: pobarvajo; v „Opravljeno“ bi bil vsak datum zapadel.
NA_VRSTI = "Na vrsti"

_KODA = re.compile(r"`([^`\n]+)`")
_KREPKO = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
_POVEZAVA = re.compile(r"\[([^\]\n]+)\]\(([^)\s]+)\)")
_ZASCITENO = re.compile(r"\x00(\d+)\x00")
_NASLOV = re.compile(r"^(#{1,6})\s+(.+?)(?:\s+#+)?\s*$")
# Samo alineje: „1. 11. 2026“ na začetku vrstice bi bila sicer oštevilčen seznam.
_ALINEJA = re.compile(r"^\s*[*+-]\s+(.*)$")
_CRTA = re.compile(r"^\s*([-*_])(?:\s*\1){2,}\s*$")
_DATUM = re.compile(r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})")
_OZNAKE = re.compile(r"<[^>]*>")


def _krepko(t: str) -> str:
    return _KREPKO.sub(r"<strong>\1</strong>", t)


def _povezava(besedilo: str, cilj: str) -> str:
    """Obe polovici sta že escapirani."""
    if cilj.startswith(("http://", "https://")):
        return f'<a href="{cilj}" target="_blank" rel="noopener noreferrer">{besedilo}</a>'
    # Pot v repozitoriju (`docs/…`) na strežniku ni naslov: povezava bi bila mrtva.
    if besedilo == cilj:
        return f"<code>{cilj}</code>"
    return f"{besedilo} <code>{cilj}</code>"


def _vrstica(besedilo: str) -> str:
    """Besedilo ene vrstice v HTML.

    Koda je prva: v njej ne velja nič, tudi `**` ne. Vsaka zaščitena stvar
    (koda, povezava) gre v seznam in v besedilo samo označba z znakom NUL, ki
    ga vhod ne more nositi -- tako krepko ne popravlja `href`, ko je v naslovu
    `**`, in koda ne dobi povezave ali krepkega.
    """
    deli: list[str] = []

    def zavaruj(h: str) -> str:
        deli.append(h)
        return f"\x00{len(deli) - 1}\x00"

    t = _KODA.sub(lambda m: zavaruj(f"<code>{html.escape(m[1])}</code>"),
                  besedilo.replace("\x00", ""))
    t = html.escape(t)
    t = _POVEZAVA.sub(lambda m: zavaruj(_povezava(_krepko(m[1]), m[2])), t)
    t = _krepko(t)

    def vrni(m: re.Match) -> str:
        return _ZASCITENO.sub(vrni, deli[int(m[1])])

    return _ZASCITENO.sub(vrni, t)


# --- tabele ------------------------------------------------------------------

def _celice(vrstica: str) -> list[str]:
    """Celice vrstice tabele. `\\|` je cev v besedilu (tudi v kodi), ne meja:
    ukazi v stolpcu „kako“ imajo cevi."""
    s = vrstica.strip()
    s = s[1:] if s.startswith("|") else s
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)]


def _je_locilo(vrstica: str) -> bool:
    """`|---|:---:|`: druga vrstica tabele. Brez nje to ni tabela."""
    return all(re.fullmatch(r":?-+:?", c) for c in _celice(vrstica))


def _konec_tabele(vrstice: list[str], i: int) -> int:
    """Vrstica za zadnjo vrstico tabele, ki se začne pri `i`; `i`, če tam ni tabele."""
    if not vrstice[i].lstrip().startswith("|"):
        return i
    j = i
    while j < len(vrstice) and vrstice[j].lstrip().startswith("|"):
        j += 1
    return j if j - i >= 2 and _je_locilo(vrstice[i + 1]) else i


def _datum(celica: str) -> date | None:
    m = _DATUM.search(celica)
    try:
        return date(int(m[3]), int(m[2]), int(m[1])) if m else None
    except ValueError:
        return None


def _tabela(vrstice: list[str], zapadlo_do: date | None) -> str:
    """Tabela v lastnem okviru, ki se drsi vodoravno (`.adm-ovoj-t`): stran
    sama na telefonu ne sme. `zapadlo_do`: vrstica, katere prva celica nosi
    datum do vključno tega dne, dobi razred `je-zapadlo`."""
    glava = [_vrstica(c) for c in _celice(vrstice[0])]
    surova = [_celice(v) for v in vrstice[2:]]
    telo = [[_vrstica(c) for c in r] for r in surova]
    # Stolpec z daljšim besedilom dobi prostor tudi na telefonu: brez tega ga
    # razporeditev po vsebini stisne na šest znakov v vrstici, ko ga sosednji
    # stolpci z enako dolgim besedilom vlečejo vsak na svojo stran. Meri se
    # vidno besedilo, ne zapis: povezava `[pot](pot)` ima pot dvakrat.
    dolg = [max((len(_OZNAKE.sub("", r[k])) for r in telo if k < len(r)), default=0) > DOLG_STOLPEC
            for k in range(len(glava))]

    def celica(oznaka: str, k: int, izris: str) -> str:
        razred = ' class="dolg"' if k < len(dolg) and dolg[k] else ""
        return f"<{oznaka}{razred}>{izris}</{oznaka}>"

    vrste = []
    for r, izris in zip(surova, telo):
        d = _datum(r[0]) if zapadlo_do else None
        razred = ' class="je-zapadlo"' if d and d <= zapadlo_do else ""
        vrste.append(f"<tr{razred}>"
                     + "".join(celica("td", k, c) for k, c in enumerate(izris)) + "</tr>")
    return (f'<div class="adm-ovoj-t"><table class="adm-t adm-kol-t" style="--st:{len(glava)}">'
            "<thead><tr>" + "".join(celica("th", k, c) for k, c in enumerate(glava))
            + "</tr></thead><tbody>" + "".join(vrste) + "</tbody></table></div>")


# --- bloki -------------------------------------------------------------------

def _zacne_blok(vrstice: list[str], i: int) -> bool:
    """Ali vrstica `i` začne nekaj drugega kot nadaljevanje odstavka ali alineje."""
    v = vrstice[i]
    return bool(_NASLOV.match(v) or _ALINEJA.match(v) or _CRTA.match(v)
                or v.lstrip().startswith("```") or _konec_tabele(vrstice, i) > i)


def _alineje(vrstice: list[str], i: int) -> tuple[list[str], int]:
    """Zaporedne alineje s tem, kar jim sledi v naslednjih vrsticah. Zamaknjene
    so ravne: ugnezdenih seznamov koledar nima."""
    postavke: list[str] = []
    while i < len(vrstice):
        m = _ALINEJA.match(vrstice[i])
        if m:
            postavke.append(m[1].strip())
            i += 1
        elif vrstice[i].strip() and postavke and not _zacne_blok(vrstice, i):
            postavke[-1] += " " + vrstice[i].strip()
            i += 1
        else:
            # Prazna vrstica seznama ne konča, če za njo sledi alineja.
            j = i
            while j < len(vrstice) and not vrstice[j].strip():
                j += 1
            if i < j < len(vrstice) and _ALINEJA.match(vrstice[j]):
                i = j
            else:
                break
    return postavke, i


def izrisi(tekst: str, danes: date | None = None) -> str:
    """Markdown v HTML: ena plošča (`.adm-plosca`) na naslov prve ali druge
    stopnje, kot drugi zavihki. Brez `danes` nič ni zapadlo."""
    vrstice = tekst.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    plosce: list[tuple[str | None, list[str]]] = []

    def dodaj(blok: str) -> None:
        if not plosce:
            plosce.append((None, []))
        plosce[-1][1].append(blok)

    i = 0
    while i < len(vrstice):
        v = vrstice[i]
        if not v.strip():
            i += 1
        elif v.lstrip().startswith("```"):
            konec = i + 1
            while konec < len(vrstice) and not vrstice[konec].lstrip().startswith("```"):
                konec += 1
            dodaj(f"<pre>{html.escape(chr(10).join(vrstice[i + 1:konec]))}</pre>")
            i = konec + 1
        elif m := _NASLOV.match(v):
            stopnja, naslov = len(m[1]), m[2]
            if stopnja <= 2:
                plosce.append((naslov, []))
            else:
                dodaj(f"<h{stopnja}>{_vrstica(naslov)}</h{stopnja}>")
            i += 1
        elif _CRTA.match(v):
            dodaj("<hr>")
            i += 1
        elif (konec := _konec_tabele(vrstice, i)) > i:
            razdelek = plosce[-1][0] if plosce else None
            dodaj(_tabela(vrstice[i:konec], danes if razdelek == NA_VRSTI else None))
            i = konec
        elif _ALINEJA.match(v):
            postavke, i = _alineje(vrstice, i)
            dodaj("<ul>" + "".join(f"<li>{_vrstica(p)}</li>" for p in postavke) + "</ul>")
        else:
            odstavek = [v.strip()]
            i += 1
            while i < len(vrstice) and vrstice[i].strip() and not _zacne_blok(vrstice, i):
                odstavek.append(vrstice[i].strip())
                i += 1
            dodaj(f"<p>{_vrstica(' '.join(odstavek))}</p>")

    if not plosce:
        return ""
    return '<div class="adm-kol">' + "".join(
        '<section class="adm-plosca">'
        + (f"<h2>{_vrstica(naslov)}</h2>" if naslov else "")
        + "".join(bloki) + "</section>"
        for naslov, bloki in plosce) + "</div>"


def pregled(danes: date) -> dict:
    """Odgovor za `/admin/koledar`: izrisan HTML in kdaj je bila datoteka
    zadnjič spremenjena (unix čas; `None`, kadar je ni). Brez datoteke ali z
    prazno pogled pove, da koledarja ni -- ne pade."""
    try:
        tekst = DATOTEKA.read_text(encoding="utf-8", errors="replace")
        spremenjeno = int(DATOTEKA.stat().st_mtime)
    except OSError:
        tekst, spremenjeno = "", None
    izris = izrisi(tekst, danes) if tekst.strip() else ""
    if not izris:
        return {"html": '<div class="adm-prazno">koledarja ni</div>', "spremenjeno": None}
    return {"html": izris, "spremenjeno": spremenjeno}
