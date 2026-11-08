# Zajem vlakov po popravku skoka nazaj (koledar 8. 11. 2026)

Vrstica koledarja: zajem vlakov po bd9365e (objava 68294cf 7. 11. ob 11.35.14). Merilo kot 7. 11.
(`2026-11-07-koledar/skladnost_po_objavi.py` in `razvrsti.py`), zdaj z objavo in dnevi kot
argumentoma: `vlaki_po_objavi.py 1794047714 2026-11-07 2026-11-08`, na arwenu, izvleček
`/var/tmp/koledar-vlaki-2026-11-08.sqlite` (produkcija samo branje), 8. 11. ob 13.40.

## Izid

Vožnja-dan šteje, kadar so vsi njeni zapisi `run` po objavi.

| | voženj-dni | ura nazaj ≥ 2 min | stal ≥ 10 min | prihod po odhodu ≥ 2 min |
|---|---|---|---|---|
| 7. 11. po objavi | 150 | 3 (2,0 %) | 1 (0,7 %) | 4 (2,7 %) |
| 8. 11. do 13.40 (nedelja) | 116 | 0 | 2 (1,7 %) | 2 (1,7 %) |
| skupaj | 266 | 3 (1,1 %) | 3 (1,1 %) | 6 (2,3 %) |

Pričakovano 1–2 %: drži. Pred popravkom 6. 11. po objavi 22,3 % in 19,0 % (242 voženj-dni).
Dosjeja zato nisem odpiral.

`meta.zamude_sz` šteje po obhodu, ne vsote: ob 13.40 `nepotrjenih` 0, `preklicanih` 0, `nazaj` 0.
Vsote preklicov za dan ni nikjer; merilo je izid zgoraj.

## Kaj ostane (po primerih)

* **Ura nazaj, dva od treh: dolg postanek po voznem redu.** LPV 2419 7. 11.: postanek 8 ima po
  voznem redu 16 min postanka (prihod 16.07, odhod 16.23). Vlak pride s +7, odpelje točno.
  Zemljevid postanek 8 pokaže šele ob odhodu (16.23.34, +0); prvi zapis postanka nastavi prihod
  in odhod na isto vrednost, zato ima prihod +0 namesto +7 in je pred odhodom s postanka 7
  (16.11). Enako LP 4291 7. 11. postanek 25 (11 min postanka): prihod +5 namesto okoli +13.
  To ni skok nazaj, je semantika prvega zapisa na dolgem postanku.
* **Ura nazaj, tretji: med postajama.** LP 4219 7. 11. postanek 11 +9, postanek 12 +3 dve minuti
  pozneje: znana semantika (SŽ pripiše zamudo odhodu prejšnjega postanka, vlaki.md, točka 5).
* **Stal ≥ 10 min**: ICS 11 8. 11. postanek 4 (+6 → +18, isto kot 7. 11.), EN 414 7. 11.
  postanek 2 (+5 → +14), ICS 17 8. 11. postanek 2 (0 → +9). Brez skoka nazaj; zamuda raste med
  postajama.
* Šest od enajstih voženj s kršitvijo ima v zaporedju skok nazaj z višjo zamudo. Pri LPV 2419
  (postanek 6: +0, skok na 5 s +7, 6 v `run` +7) in LP 4291 (21–24 +3, skok na 21 s +13, v `run`
  +13) je preklic delal, kršitev je drugje; drugih štirih nisem pogledal po postankih.

Prihod na dolgem postanku je nov rok: izmeri na delavniku, koliko postankov z ≥ 5 min postanka
po voznem redu ima prihod enak odhodu, ko je zamuda pred njim večja (koledar 9. 11.).
