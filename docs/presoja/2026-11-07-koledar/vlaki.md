# Zajem vlakov po prenovi, prvi dan (koledar 7. 11. 2026)

Objava 88ec114 6. 11. 2026 ob 14:45:35 (`zamude_sz.POPRAVI_DO_TS` = 1793972735). Merjeno na arwenu, samo branje (kopija vrstic v `/var/tmp/koledar-vlaki.sqlite`, na koncu pobrisana). Skripta `skladnost_po_objavi.py` v tem imeniku.

Izhodišče po popravilu zgodovine 6. 11., od 1. 11.: ura nazaj ≥ 2 min 3,4 % voženj-dni, „stal ≥ 10 min“ na postanku ≤ 2 min 5,1 %. Cilj < 0,5 %.

## Sprotne najdbe

1. **Prvi rez (10.05)**, voženj-dni z `run`, vlaki brez nadomestnih:
   * 6. 11. pred objavo (po `popravi-vlake`): 311, ura nazaj 18 (5,8 %), stal ≥ 10 min 7 (2,3 %).
   * **6. 11. po objavi** (vsi zapisi `run` po 14:45:35): 242, **ura nazaj 54 (22,3 %), stal ≥ 10 min 46 (19,0 %)**, prihod po odhodu 2 (0,8 %). Čez objavo 46: 9 / 3.
   * **7. 11. do 10.02**: 86, ura nazaj 6 (7,0 %), stal ≥ 10 min 7 (8,1 %), prihod po odhodu 1.
   * Cilj < 0,5 % ne drži, po objavi slabše od izhodišča 3,4 / 5,1 %.
2. **Izbruh derp.si ob zagonih: 0.** Podpis derp.si v `obs` = `observed_at − feed_ts` (pred objavo „oba polja“ p50 45 s, n = 1 387; zemljevid p50 1 s, n = 5 395). V minuti po vsakem od šestih zagonov 6. 11. (14:45:35, 14:57:56, 15:08:56, 15:18:46, 15:27:44, 16:29:58) 0 vrstic z zamikom ≥ 5 s.
3. `meta.zamude_sz` ob 10.02: nepotrjenih 2, nazaj 0, ponastavljenih 0 (posnetek, ne zgodovina).
4. **Vzorec LPV 2401 7. 11.**: zemljevid je vlak od 04:36 do 04:46 risal po voznem redu (postanki 4–7, zamuda 0), ob 04:47 skok nazaj na 4 z +9 (`nazaj` z večjo velja). Prvi zapis vsakega od 4–7 je postavil prihod 0, poznejši samo odhod +9 → prihod 0 ostane: „stal 9 min“ na 1-min postankih in ura nazaj. Prej je prihod ostal napoved derp.si, zdaj prvi zapis zemljevida, ki je bil izmišljen. Vzrok: vir laže (SŽ riše po voznem redu), naša koda ga zapeče v prihod.
5. **Razvrstitev 78 voženj-dni s kršitvijo po objavi** (`razvrsti.py`): **73 ima skok zemljevida nazaj z višjo zamudo** (zapis na postanku s < največjega zapisanega, odhod višji) — vir laže (SŽ riše vlak po voznem redu ali z nizko zamudo, nato zamudo dvigne in vlak skoči nazaj), **naša koda** pa prvi zapis vsakega postanka, ki ga vlak še ni dosegel, zapeče kot prihod (88ec114, `zamude_sz.zapisi`). 5 brez skoka (ICS 11, MV 577, LP 3524, LP 4521, EC 78): zamuda raste, ko je vlak med postajama (ICS 11 7. 11. postanek 4 +6 → +19 na odseku 06:54–07:42), SŽ jo pripiše odhodu prejšnjega postanka = znana semantika zemljevida („stal X min je lahko napačno pripisan“, presoja 6. 11.), okno jo uskladi.
6. **Ponovitev s predlaganim pravilom** (`ponovi.py`; skok nazaj z višjo zamudo pobriše postanke od skoka naprej, naslednji zapis je spet prvi). Ponovitev brez pravila da `run` nazaj (55 / 46 proti 54 / 46; 6 / 7 proti 6 / 7), torej je ponovitev zvesta.

   | | voženj | ura nazaj zdaj → predlog | stal ≥ 10 zdaj → predlog | prihod po odhodu |
   |---|---|---|---|---|
   | 6. 11. po objavi | 242 | 54 (22,3 %) → 5 (2,1 %) | 46 (19,0 %) → 4 (1,7 %) | 2 → 3 |
   | 7. 11. do 10.02 | 86 | 6 (7,0 %) → 0 | 7 (8,1 %) → 1 (1,2 %) | 1 → 1 |

   Izgubljenih postankov (pobrisan, nikoli znova dosežen): 3 od 4 039. Ostanek ≈ pet voženj semantike med postajama; cilj 0,5 % tudi s pravilom ne drži, dokler se pripis med postajama ne reši.
7. Ponoči derp.si piše vlake v `obs`, ko zemljevid nima pripetega vlaka (7. 11. 00:30–04:00: 220 vrstic, 15 voženj, zamik ≥ 5 s; LPV 2401 ob 02:54 0/0 na vseh 17 postankih, 1,5 h pred odhodom). To je po načrtu (`napoved_vlaka`: samo `obs`), ne izbruh ob zagonu; ob prvem zapisu zemljevida pa enaka vrednost ne gre v `obs` (`worth_logging`), zato dnevnik prvega zapisa zemljevida ne vidi.

## Predlog popravka

`kajros/zamude_sz.py:296` (`zapisi`): ob skoku nazaj z VIŠJO zamudo (`seq < zadnji[0] and zamuda > zadnji[1]`) pobriši `sz_zamuda` za `stop_seq >= seq` te vožnje-dne in v `run` ponastavi postanke `stop_seq > seq` (niso bili prevoženi), da je naslednji zapis prvi (prihod = odhod). Preizkus: LPV 2401 7. 11. (0 na 4–7, skok +9 ob 04:47). Zgodovino od objave popravi `popravi-vlake` z novim pravilom (obs ima zaporedje).
