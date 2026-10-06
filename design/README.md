# Oblikovne smeri

Štiri smeri za prikaz, artboardi na enem platnu:

| Datoteka | Smer | Os |
|---|---|---|
| `Main.dc.html` | A — Nadzorna soba | zemljevid = aplikacija, temno, cela mreža naenkrat |
| `Voznired.dc.html` | B — Vozni red | tipografija = aplikacija, en vlak od zgoraj navzdol |
| `Analitika.dc.html` | C — Analitika | številke = aplikacija, porazdelitve in lestvice |
| `Sledilnik.dc.html` | D — Sledilnik | telefon, en vlak, velika številka |

`canvas.json` postavi artboarde, nosi opombe z argumenti za in proti.

## Podatki v mockupih

Zemljevidi iz prave geometrije mreže (267 postaj, 283 elementarnih odsekov) — projekcija web-mercator, generirana iz `kajros export`. V pravi aplikaciji **Leaflet z OSM rastrskimi ploščicami**; v mockupih ploščice narisane kot SVG, ker platno nima dostopa do mreže.

Živi podatki (LPV 2206 po postajah, lestvica največjih zamud, izmerjeni hitrosti) resnični z zajema 18. 8. 2026. Tridesetdnevna zgodovina in porazdelitev zamud **ponazoritveni** — toliko podatkov še ni zajetih.

## Barve zamud

Ordinalni ramp v enem odtenku, validiran na monotonost svetlosti in kontrast proti podlagi:

| razred | svetla | temna |
|---|---|---|
| točno | `#8a8175` | `#7c8698` |
| 1–5 min | `#f0934f` | `#f2a87e` |
| 5–15 min | `#dd6a26` | `#e07b45` |
| nad 15 min | `#a83f10` | `#b85417` |

Vsaka oznaka poleg barve vedno nosi število minut — barva nikoli ne nosi pomena sama.

## Ponovno sestavljanje platna

Platno se generira iz teh datotek; rezultat (`kajros-smeri.html`) ni v gitu.

## Budilka v 3D (6. 10. 2026)

`budilka/prototip.html` je prototip zaslona zvonjenja (objavljen kot zasebna stran za preizkus na telefonu): vlak ali avtobus potegneš do postaje („Peron“) ali ga potisneš proti cilju na obzorju („V daljavo“). Na vrhu je faza zvonjenja: najprej nežno, čez 45 s glasno, kot v aplikaciji 1.5. Geometrija je iz škatel, enega izvlečenega profila čela in valjev koles, z merami v metrih (KISS SŽ 313 po `o-nas/src/vlak.js`): narejena je za ročni prenos v Kotlin z OpenGL ES 2.0, brez knjižnic. Datoteka je v obliki strani za objavo (brez `<html>`), za ogled v brskalniku jo zavij v navadno ogrodje.

**Izbran je Peron** (David, 6. 10. 2026: „V peron je boljša, le popravi, ker je težko potegniti čisto do roba“). Prva različica je zahtevala 85 % poti, ki je bila 68 % širine zaslona — 58 % širine od vozila naprej, skoraj do roba. Zdaj je pot pol širine in zadošča 60 % (tretjina širine), ali pa sunek: spust s hitrostjo vsaj 0,6 px/ms po vsaj 30 % poti. Začeti je še vedno treba na vozilu (rezerva 44 px), zato dlan ali žep vozila ne premakneta. Preizkus prek CDP z lastnimi časi dogodkov: 20 % širine se vrne, 33 % ustavi, sunek 18 % širine v 0,1 s ustavi, sunek 12 % ne, poteg mimo vozila ne premakne ničesar. Hitrost se meri iz časov dogodkov (`timeStamp`, združeni premiki), ne iz ure ob obdelavi: pri počasnem risanju bi sicer vsak sunek izgledal počasen.

Prenos v aplikacijo (1.6) je v `android/…/Peron.kt` (geometrija in pravilo potega, preizkusi `PeronTest`) in `PeronRisar.kt` (OpenGL ES 2.0). Barve izrisa na emulatorju se s prototipom ujemajo na točko (vzorci neba, perona, tal in megle); glej `.claude/rules/android.md`.
