# Oblikovne smeri

Štiri smeri za prikaz, kot artboardi na enem platnu:

| Datoteka | Smer | Os |
|---|---|---|
| `Main.dc.html` | A — Nadzorna soba | zemljevid je aplikacija, temno, cela mreža naenkrat |
| `Voznired.dc.html` | B — Vozni red | tipografija je aplikacija, en vlak od zgoraj navzdol |
| `Analitika.dc.html` | C — Analitika | številke so aplikacije, porazdelitve in lestvice |
| `Sledilnik.dc.html` | D — Sledilnik | telefon, en vlak, velika številka |

`canvas.json` postavi artboarde in nosi opombe z argumenti za in proti.

## Podatki v mockupih

Zemljevidi so narisani iz prave geometrije mreže (267 postaj, 283 elementarnih
odsekov) — projekcija je web-mercator, generirana iz `kajros export`.
V pravi aplikaciji je to **Leaflet z OSM rastrskimi ploščicami**; v mockupih so
ploščice narisane kot SVG, ker platno nima dostopa do mreže.

Živi podatki (LPV 2206 po postajah, lestvica največjih zamud, izmerjeni hitrosti)
so resnični z zajema 18. 8. 2026. Tridesetdnevna zgodovina in porazdelitev zamud
sta **ponazoritveni** — toliko podatkov še ni zajetih.

## Barve zamud

Ordinalni ramp v enem odtenku, validiran na monotonost svetlosti in kontrast
proti podlagi:

| razred | svetla | temna |
|---|---|---|
| točno | `#8a8175` | `#7c8698` |
| 1–5 min | `#f0934f` | `#f2a87e` |
| 5–15 min | `#dd6a26` | `#e07b45` |
| nad 15 min | `#a83f10` | `#b85417` |

Vsaka oznaka poleg barve vedno nosi tudi število minut — barva nikoli ne nosi
pomena sama.

## Ponovno sestavljanje platna

Platno se generira iz teh datotek; rezultat (`kajros-smeri.html`) ni v gitu.
