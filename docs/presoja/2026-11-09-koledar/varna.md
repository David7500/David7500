# Varna napoved na senci po popravku zajema (9. 11. 2026)

Vprašanje iz koledarja: gre varna napoved (`napoved.varna_s`, rezerva + kvantil 0,25
skrčenega ostanka) v prikaz za vlake na poti? Merilo, postavljeno vnaprej: na senci ≥ 3 dni
sta precenjenost in strošek nižja od naše ocene, MAE pa ni slabši od prenosa.

## Od kod senca bere izid

`ocena.resolve` zapiše `actual_s` enkrat, ob razrešitvi (`ocena.py:336`), in ga pozneje ne
preračuna. Vrstice, razrešene pred popravkom zgodovine 7. 11. ob 11.50, zato nosijo stare,
pri okoli petini voženj napačne ure prihoda. `kajros ocena --days 3` bi jih vzel zraven.
Merjeno je zato samo na vrsticah z `made_ts` od 7. 11. 11.36 (objava popravka zajema), kjer
sta posnetek in resnica oba po popravku. Skripta: `varna_senca.py` (arwen, samo branje).

## Izid

Železnica, 10 414 razrešenih vrstic od 7. 11. 11.36 do 9. 11. ~16 h (sobota popoldne,
nedelja, ponedeljek do popoldneva). Na poti 6 645 vrstic, vse imajo vse tri vrednosti, zato
je vzorec za vse modele isti.

| na poti | precenjenih | strošek (min) | MAE (min) | v 2 min | podcenjenih |
|---|---|---|---|---|---|
| naša (prikaz) | 3,1 % | 7,73 | 2,10 | 71,3 % | 5,5 % |
| **varna** | **0,8 %** | **6,79** | **2,00** | 73,6 % | 8,5 % |
| prenos | 1,5 % | 8,07 | 2,54 | 66,5 % | 11,8 % |

Po dnevih drži na vsakem posebej (precenjenih / strošek / MAE, varna proti naši):
7. 11. (1 357) 0,7 / 6,61 / 2,01 proti 4,2 / 8,57 / 2,19; 8. 11. (2 403) 0,8 / 6,73 / 2,01
proti 3,1 / 7,67 / 2,18; 9. 11. (2 885) 0,8 / 6,92 / 1,99 proti 2,5 / 7,38 / 1,99.

Pred odhodom (3 769 vrstic): varna 0,0 % precenjenih, strošek 6,20, MAE 1,20; naša 4,0 %,
8,52, 1,31.

Na senci je varna boljša od naše tudi po MAE (2,00 proti 2,10), na zgodovini pa je bila
slabša (2,23 proti 2,05, `docs/presoja/vlaki-prenova/modeli.md`). Razlika med merili ni
razložena; za odločitev ne šteje, ker merilo zahteva samo MAE ne slabši od prenosa.

## Odločitev

Merilo izpolnjeno na vseh treh dneh: **varna gre v prikaz za vlake na poti.** Pred odhodom
po prenovi (točka 3): prikaz = vozni red, „običajno“ kot opomba. Izvedba je nova seja; pred
preklopom ista skripta še na celem delavniku 10. 11. Če se tam precenjenost ali strošek
obrneta, ostane v senci.

Omejitev: samo en delavnik (9. 11., do popoldneva) in en vikend. Senca teče naprej tudi po
preklopu (`ours_s` = takrat varna), zato bo vsak obrat viden v `kajros ocena`.
