# Nepripeti vlaki zemljevida SŽ, teden 31. 10.–7. 11. 2026

Vrstica koledarja sob 7. 11.; VIRI-PRESOJA točka 6 (ca22a50, 31. 10.).
Pot: `zamude_sz.razberi` -> `stevci["nepripeti"]` -> `iz_lege.sz_stevilke` (derp.si piše) in dnevnik `teci` enkrat na vlak in dan.
Objava prenove 6. 11. 14:45 (88ec114): pot nepripetih nespremenjena (razberi/pripni ista), spremenil se je samo `potrdi` za pripete.

## Koraki
1. **Dnevnik arwen 31. 10.–7. 11. 10.00** (`journalctl ... | grep 'ki ga ne pripnemo'`): 161 vrstic. Po dnevih: 31. 10. 3 (od 20.59), 1. 11. 17, 2.–6. 11. 26–28 na dan, 7. 11. 6 (do 10 h). Dvojniki (ponovni zagon: `_javljeni` je v pomnilniku) 1803, 4494, 4515: 4 vrstice.
   Premisa koledarja „delavnik ~1 vlak (LP 4208)“ je bila drugo merilo (vlak, ki ga nikoli ne pripnemo, 29.–30. 10.). Dnevnik piše vlak, ki je kdaj koli nepripet, zato 27 na delavnik.
2. **Kateri** (dnevnik): 21 različnih vlakov Kočevske proge LP 4491–4537 (vsak delavnik isti niz 4500–4527) + 6 na dan brez naše vožnje (1803, 1804, 671, 673, 9550, 9568) + posamezni 7974, 7982, 33887, 2283, 4445.
3. **Vzrok, dosje** (`dosje.sqlite`, `stanje` vir `sz`, 1. 11. 13.42–7. 11. 10.00): 153 epizod nepripetosti (zaporedna stanja `nepripet`):
   - **ime postaje 143 (93 %)**: zemljevid piše `Postaja = "Slivnica"`, naša postaja je „Spodnja Slivnica“ (`station` 1120963). 28 vlakov, 7 dni; obe smeri (Grosuplje/Ljubljana–Kočevje 76, nazaj 67). `zamude_sz.py:154` naslednjo postajo išče po `peroni._kljuc_imena` (`peroni.py:62`: odstrani le „(Železniški)“) in primerja `p[i][1] == naslednja` (`zamude_sz.py:161`) → ni kandidatke → `pripni` vrne None.
     Primer: LP 4501 6. 11. (vožnja 453667: Ljubljana 04:16, Grosuplje 04:37/04:38, Spodnja Slivnica 04:41, Čušperk 04:48). Zemljevid 04:16 „Grosuplje, Odhod 04:16“ pripet; **04:37 „Slivnica, Odhod 04:38, +0“ nepripet**; 04:41 „Čušperk“ spet pripet.
     Trajanje epizode: mediana 210 s, p90 422 s, največ 481 s; nad 120 s (`SZ_VODI_S`, derp.si sme pisati) 110 od 143.
   - **ni v voznem redu 8**: mednarodni MO/MV (Sežana–Sežana 1803/1804, Gorica–Nova Gorica 7982/33887, Spielfeld–Maribor 671/673, Őriszentpéter–Hodoš 9550/9568). V zipu IJPP jih ni; derp.si jih ima kot `INTL-…` (HAFAS), mi jih ne štejemo → derp.si za nas nič ne zapiše, škode ni.
   - **ura 2**: 2283 Brestanica in 4445 Maribor Studenci, 2. 11. ob 00:02–00:03 (Odhod minuto naprej, čez polnoč). Enkrat v tednu, nepojasnjeno.
   - Vsa imena Postaja v tednu (Vrsta 1, 11 625 stanj, 254 imen): neujemanje le „Slivnica“ (145) in „Rodik“ (3, vlaka 27501 in 44213 brez naše vožnje).
4. **Pred in po objavi 6. 11. 14:45**: 131 / 12 epizod, vse Slivnica razen 10 pred. `pripni`, `razberi`, `_kljuc_imena` od ca22a50 nespremenjeni (`git diff ca22a50 HEAD`, samo komentarji v `zapisi`). Prenova poti ni spremenila.
5. **Ali derp.si zapolni luknjo**: postanek pred Slivnico (Grosuplje 76, Čušperk 67) — zemljevid ga ne more zapisati (kadar je naslednja Slivnica).
   - `run` na tem postanku **prazen v 124 od 143** epizod: postanek ostane brez meritve trajno. derp.si je v epizodi v `obs` zapisal ta postanek le v 16 od 143 (13 enako zemljevidu ±60 s, 3 ničla namesto +2: LP 4492 1. 11., LP 4500 2. 11.); od epizod nad 150 s brez zapisa derp.si 93.
   - `run` z vrednostjo 19: 12 enako zemljevidu, 7 drugače — večinoma derp.si 0 pri zemljevidu +2 … +16 (LP 4521 3. 11. +14 → 0; LP 4527 4. 11. +9 → 0; LP 4493 1. 11. +16 → +10).
   - Slivnica sama ima zapis zemljevida (`sz_zamuda`) ob naslednjem pripetju (Postaja = Čušperk/Grosuplje).
   Zakaj derp.si molči, ni izmerjeno (v 40 klicih ne); popravek imena ga naredi nepomembnega.
6. **Odločitev**: popravek je ime, ne derp.si. „Slivnica“ z zemljevida = „Spodnja Slivnica“ samo pri pripenjanju zemljevida (vožnja mora imeti postajo, zato „Slivnica pri Mar.“ ne more biti zadeta). Odpravi 143 od 153 epizod (93 %) in luknjo na Grosuplju/Čušperku pri 21 vlakih na delavnik. Kode ta agent ne spreminja (predlog glavni seji).

Skripte (na arwenu, `python3 -I`, samo branje): `nepripeti_sz.py` (epizode iz dosjeja -> /var/tmp/koledar-nepripeti.json), `nepripeti_sz_derp.py` (postanek pred Slivnico), `nepripeti_sz_imena.py` (imena Postaja brez naše postaje). Začasne datoteke na arwenu pobrisane.
