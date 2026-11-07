# Vozila brez prosojnosti po hitrosti (7. 11. 2026)

Vrstica koledarja sob 7. 11.: vozila v polni barvi, hitrost ne spremeni videza; prosojen ostane samo črtkan obris ocene lege.

## Stanje pred delom

* V gitu od 3. 11. samo commit koledarja (99259c4), koda nedotaknjena: naloga ni bila narejena.
* Rabe hitrosti za videz (grep `moving`, `speed >= 3`, `opacity` v `kajros/static/`, `o-nas/src/`):
  * `vozila3d.js` `voziloSvg(size, moving, ...)`: telo `fill-opacity` 1 / 0,5 (ocena 0,55).
  * `dashboard.js` `busIkona(ink, moving, ocena)`: ključ slike `vozi`/`stoji`/`ocena`, `dodajAvtobuse` riše tri stanja na barvo; `avtobusTocka` pošlje `(speed_kmh || 0) >= 3` -- brez hitrosti = stoji.
  * `pot_podrobno.js` `voziloSvg(30, (speed_kmh || 0) >= 3, ...)`.
  * `train.js` `busSvg(moving, ink)`: okno vožnje je vedno na oceni, telo 0,55 / 0,32; `dataset.vozi` je ključ za ponovni izris.
  * `o-nas/src`: brez rabe. 3D modeli (`vozila3d.js`) hitrosti ne berejo.
  * Besedilo (`dashboard.js` kartica in oblaček: „N km/h“ / „stoji“ / „brez hitrosti“) loči `null` pravilno -- ostane, ni videz.

## Meritev na arwenu (`vehicle_now`, sob 7. 11. ob 10.19, svežih 120 s)

| prevoznik | avtobusov | brez hitrosti | < 3 km/h | ≥ 3 km/h |
|---|---|---|---|---|
| 1118 (LPP primestni) | 7 | 0 | 0 | 7 |
| 1119 | 35 | 35 | 0 | 0 |
| 1121 | 5 | 5 | 0 | 0 |
| 1123 | 56 | 56 | 0 | 0 |
| lpp (mestni) | 54 | 0 | 23 | 31 |
| marprom | 20 | 1 | 5 | 14 |
| kranj | 4 | 0 | 0 | 4 |

97 od 181 avtobusov brez hitrosti (medkrajevni IJPP 96 od 96, Marprom 1 od 20), vsi narisani kot stoječi (pol prosojni). Potrdi 5. 11. ob 22.50 (121 od 174). Mestnih z izmerjeno hitrostjo pod 3 km/h 28 od 78 (LPP 23, Marprom 5) -- ti so bili edini, pri katerih je prosojnost kaj pomenila, legende pa ni bilo.

## Narejeno

* `voziloSvg(size, ink, {ocena, vlak})` brez parametra hitrosti: telo polno (1), na oceni 0,55 s črtkanim obrisom.
* `busIkona(ink, ocena)`: ključ `bus-<barva>` / `bus-<barva>-ocena`; `dodajAvtobuse` riše 2 slike na barvo namesto 3.
* `pot_podrobno.js` brez hitrosti v klicu.
* `train.js` `busSvg(ink)`: okno vožnje je vedno na oceni, telo 0,55 ne glede na hitrost (prej 0,55 / 0,32); ponovni izris po barvi (`dataset.ink`), ne po hitrosti.
* Pravilo v `.claude/rules/zemljevid.md` (pod „Meritev od ocene loči oblika“).

## Preverjeno

* Razvojni strežnik 8013 z zajemom, 187 avtobusov v `/api/vehicles` (Arriva 52–54, Nomago 36–37, vsi brez hitrosti).
* Posnetki (CDP, Vulkan): `posnetki/zemljevid-namizje.png` (1850 px, Ljubljana z14), `posnetki/zemljevid-telefon.png` (430 px, avtobusna postaja z15): LPP, Arriva, Nomago vsi v polni barvi, tudi stoječi na postaji. `posnetki/okno-lpp14-telefon.png`: okno LPP 14, vozilo na oceni 0,55 s črtkanim obrisom (`dataset.ink` = `#4db97f`). `posnetki/zemljevid-izbran-namizje.png`: izbrani LPP 14 z obročem. Konzola 0 napak v vseh štirih.
* pytest 1398 zelenih, `preveri.sh` izhod 0.
