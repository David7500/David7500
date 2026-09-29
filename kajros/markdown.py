"""Stran kot Markdown, kadar jo agent zahteva z `Accept: text/markdown`.

Claude Code, Cursor in podobna orodja pri branju strani pošljejo to glavo,
ker je Markdown za model krajši in čistejši od HTML z razredi in podobami.
Cloudflare to zna sam, a šele od načrta Pro; naše strani so brez JS in
preproste, zato je pretvorba kratka in brez nove odvisnosti (stdlib).

Pretvori se samo tisto, kar je res besedilo: naslovi, odstavki, seznami,
tabele, povezave in krepko. Podoba, skripta, `<head>` in obrazci odpadejo.
Povezave so absolutne -- Markdown brez strani, na kateri leži, ne ve,
kam kaže `/postaja/ljubljana`.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urljoin

_PRAZNI = {"br", "img", "input", "meta", "link", "hr", "source", "wbr"}
_PRESKOCI = {"script", "style", "svg", "head", "nav", "form", "button",
             "select", "textarea", "template", "noscript", "iframe"}
_BLOKI = {"p", "div", "ul", "ol", "section", "main", "header", "footer",
          "article", "aside", "table", "thead", "tbody", "details", "summary",
          "figure", "figcaption", "blockquote", "dl", "dt", "dd"}
_NASLOVI = {f"h{n}": "#" * n for n in range(1, 7)}
_RAZMIK = re.compile(r"\s+")


def zeli_markdown(accept: str) -> bool:
    """Ali glava `Accept` postavlja Markdown vsaj tako visoko kot HTML.

    Brskalnik Markdowna ne našteje nikoli, `*/*` (curl, iskalniki) pa ga
    ne zahteva -- zato mora biti naveden izrecno.
    """
    q: dict[str, float] = {}
    for del_ in accept.lower().split(","):
        tip, _, ostalo = del_.partition(";")
        tip = tip.strip()
        teza = 1.0
        for par in ostalo.split(";"):
            ime, _, vrednost = par.partition("=")
            if ime.strip() == "q":
                try:
                    teza = float(vrednost)
                except ValueError:
                    teza = 0.0
        if tip:
            q[tip] = teza
    md = q.get("text/markdown", 0.0)
    if md <= 0:
        return False
    html = max(q.get("text/html", 0.0), q.get("application/xhtml+xml", 0.0))
    return md >= html


class _Pretvornik(HTMLParser):
    def __init__(self, osnova: str):
        super().__init__(convert_charrefs=True)
        self.osnova = osnova
        self.bloki: list[tuple[str, str]] = []   # (vrsta, besedilo)
        self.kosi: list[str] = []
        self.predpona = ""
        self.vrsta = "odstavek"
        self.preskoci: str | None = None
        self.globina = 0
        self.povezave: list[str | None] = []
        self.celice: list[str] | None = None
        self.shranjeni: list[str] = []
        self.glava_vrstice = False

    # -- izpis --------------------------------------------------------
    def _zakljuci(self):
        besedilo = _RAZMIK.sub(" ", "".join(self.kosi)).strip()
        besedilo = re.sub(r"\[ ", "[", besedilo)
        besedilo = re.sub(r" \]\(", "](", besedilo)
        if besedilo:
            self.bloki.append((self.vrsta, self.predpona + besedilo))
        self.kosi = []
        self.predpona = ""
        self.vrsta = "odstavek"

    def _presledek(self):
        if self.kosi and not self.kosi[-1].endswith(" "):
            self.kosi.append(" ")

    # -- razčlenjevalnik ----------------------------------------------
    def handle_starttag(self, tag, atributi):
        a = dict(atributi)
        if self.preskoci:
            if tag == self.preskoci:
                self.globina += 1
            return
        if tag not in _PRAZNI and (tag in _PRESKOCI or "hidden" in a
                                   or a.get("aria-hidden") == "true"):
            self.preskoci, self.globina = tag, 1
            return
        if tag in _NASLOVI:
            self._zakljuci()
            self.predpona = _NASLOVI[tag] + " "
        elif tag == "li":
            self._zakljuci()
            self.predpona, self.vrsta = "- ", "seznam"
        elif tag == "tr":
            self._zakljuci()
            self.celice, self.glava_vrstice = [], False
        elif tag in ("td", "th"):
            self.shranjeni.append("".join(self.kosi))
            self.kosi = []
            self.glava_vrstice = self.glava_vrstice or tag == "th"
        elif tag in _BLOKI:
            self._zakljuci()
        elif tag == "a":
            href = (a.get("href") or "").strip()
            if href and not href.startswith(("#", "javascript:")):
                self.povezave.append(urljoin(self.osnova, href))
                self.kosi.append("[")
            else:
                self.povezave.append(None)
        elif tag in ("b", "strong"):
            self.kosi.append("**")
        elif tag in ("i", "em"):
            self.kosi.append("*")
        elif tag == "span":
            self._presledek()
        elif tag == "br":
            self._presledek()

    def handle_endtag(self, tag):
        if self.preskoci:
            if tag == self.preskoci:
                self.globina -= 1
                if self.globina == 0:
                    self.preskoci = None
            return
        if tag in _NASLOVI or tag == "li" or tag in _BLOKI:
            self._zakljuci()
        elif tag in ("td", "th") and self.celice is not None and self.shranjeni:
            self.celice.append(_RAZMIK.sub(" ", "".join(self.kosi)).strip())
            self.kosi = [self.shranjeni.pop()]
        elif tag == "tr" and self.celice is not None:
            self.kosi = []
            if any(self.celice):
                self.bloki.append(("tabela", "| " + " | ".join(self.celice) + " |"))
                if self.glava_vrstice:
                    self.bloki.append(("tabela", "|" + "---|" * len(self.celice)))
            self.celice = None
        elif tag == "a" and self.povezave:
            cilj = self.povezave.pop()
            if cilj:
                self.kosi.append(f"]({cilj})")
        elif tag in ("b", "strong"):
            self.kosi.append("**")
        elif tag in ("i", "em"):
            self.kosi.append("*")
        elif tag == "span":
            self._presledek()

    def handle_data(self, podatki):
        if not self.preskoci:
            self.kosi.append(podatki)

    def izpis(self) -> str:
        self._zakljuci()
        izhod: list[str] = []
        prej = None
        for vrsta, besedilo in self.bloki:
            if prej is not None:
                skupaj = vrsta == prej and vrsta in ("seznam", "tabela")
                izhod.append("\n" if skupaj else "\n\n")
            izhod.append(besedilo)
            prej = vrsta
        return "".join(izhod) + "\n"


def iz_html(html: str, naslov: str) -> str:
    """Markdown iz strani `naslov` (celoten naslov, da se povezave razrešijo)."""
    p = _Pretvornik(naslov)
    p.feed(html)
    p.close()
    return p.izpis()
