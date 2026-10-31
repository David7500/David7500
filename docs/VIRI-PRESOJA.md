# Presoja virov: kaj je narejeno, kaj je odprto

Začeto 31. 10. 2026 (David: „zajem virov je steber aplikacije, to more delati v nulo“). Postopek za vsak naslednji pregled je skill `/preveri-vire` (`.claude/skills/preveri-vire/SKILL.md`). Surove najdbe dveh bralcev kode z vrsticami: `docs/presoja/2026-10-31-najdbe.md`. Meritve: `docs/MERITVE.md`, „Viri na praznik in ura namesto zamude“.

## Stopnje opozoril (narejeno, 5bb51c3)

| stopnja | pomen | pošta | potniki |
|---|---|---|---|
| rumeno | popravi se samo ali je samo za vedenje | ne | — |
| oranžno | ne popravi se samo: seja s Claude (`/preveri-vire`) ali Davidovo dejanje | podnevi 7–22 h, z ukrepom | — |
| rdeče | takoj: nekaj stoji ali potniki ne dobijo podatkov | takoj (po `po_s`, privzeto 10 min) | samodejno obvestilo po 20 min molka |

* Rumena, ki ne mine, postane oranžna. Trajanje šteje `zdravje.Sled` (nit pošte jo vsako minuto osveži in hrani v `meta.zdravje_sled`; nit teče tudi brez nastavitev pošte).
* Meje: vir brez odgovora 2 h, derp.si 6 h (rezerve tečejo), dnevni vir 2 dni, stanje vozil Marprom/Kranj 1 h, LPP brez voznega reda ≥ 5 in 10 % 1 h, vozila brez zamude (3 in 5 %) 90 min ali takoj pri 10 in 25 %, vozni red teden prej (dva dni prej rdeče), disk pod 12 % (pod 8 % rdeče).
* Molk omrežja je rdeč po 20 min (prej rumen do 60 min, pošta po 70 min) — ista meja kot obvestilo potnikom (`obvestila.MOLCI_S`, preizkus ju drži skupaj).
* Oranžna, ki postane rdeča, gre v pošto znova.
* `/admin`: pas po stopnjah z naslovom (barva ni sama), ime vrstice, „Kaj storiti“, vozila kot povezave na zemljevid (`?trip=` ali novi `?vozilo=`), ob rdečem ali potniki že vidijo obvestilo.

## Opozorila s posnetka 31. 10. 2026 (presojeno)

* **„vožnje brez voznega reda: LPP 1–2 od 105“ — rumeno, pravilno.** Žive vožnje linije 2 brez para. Vzrok: objava LPP ima na praznik 75 skupin enakih dvojnikov in par po uri je bil dvoumen. Popravljeno v `zive._po_uri` in `_po_nacrtu` (04d6693). Vozilo s slike (d5498517, „vožnja mimo voznega reda“) pa ni dvojnik: najbližja prosta objavljena je +12,9 min, zunaj okna para (−4 … +10). Vir laže le toliko, da LPP vozi drugače od objave; zdravje ni kriva.
* **„vozila brez zamude: Arriva 1 od 18“ — rumeno, a za tem je luknja (odprto, točka 2).** A8426 Ljubljana AP → Koper: NAP vozila 31. 10. ni pripel (praznik, `brez_dneva`), derp.si ga je. Ker NAP vodi Arrivo, derp-ove zamude ne beremo.
* **„uradni zip ne pokrije tedna; velja kopija“ — rumeno, pravilno.** Marprom, rok 4. 1. 2027, rdeče od 30. 12.
* **Neviden na posnetku:** LPP 2 (16:43) +66 min na tabli Gornji trg — vozilo pri garaži, feed mu je zamudo večal z uro. Zdravje tega ni videlo. Zdaj rumena vrstica „avtobusi · zamuda raste z uro“ s povezavami (senca, točka 1).

## Narejeno 31. 10. 2026

| commit | kaj |
|---|---|
| 5bb51c3 | tri stopnje, sled trajanja, pošta po stopnji, povezave na vozila, `?vozilo=` na zemljevidu |
| 3d7054c | NAP vodi samo, ko pripne vsaj eno vozilo; zemljevid SŽ samo, ko ima vlak, ki ga pripnemo (prej je prazen odgovor 200 utišal derp.si) |
| e38d511 | `collector.ura_namesto_zamude` v senci (`KAJROS_DRSI=senca`), vrstica `fantomi` s povezavami |
| 04d6693 | dvojniki v objavi LPP niso tekmici za par |

## Odprto, po prednosti

Rdeča črka = potnik vidi napačno ali nič, zdravje tega ne pove.

1. **Ura namesto zamude: senca → vodi.** Teden zbirati zadetke vrstice `fantomi` (povezave v /admin) in jih ročno pogledati na zemljevidu: vozilo stoji v garaži ali na cesti v zastoju? Ponovitev `skripte/fantom_ponovitev.py` je dala 29, 37, 2, 1 na dan (28.–31. 10.), ujemanje z dejanskimi fantomi (nad 40 min, nagib > 0,8: 19, 8, 15, 2) je slabo — pravilo najbrž rabi še lego (vozilo se ne premakne 15 min) ali LPP-jeve zaslone (vožnje ne kažejo). Tudi statistika: fantomi so v `run` in `stat_dan` od 29. 10.; po odločitvi popraviti za nazaj (`kajros summarize`).
2. **NAP ne pripne, derp.si pa (praznik).** Vozilo, ki ga NAP vodi, a ga ne pripne (`brez_dneva`, `brez_voznje`, `prezgodaj`), ostane brez zamude. Najprej izmeri, zakaj `brez_dneva` (koledar praznika v našem uvozu proti NAP-ovemu id-ju vožnje). Od 31. 10. zvečer `meta.nap.nepripeti` hrani 15 vozil z vzrokom, NAP-ovo vožnjo, okno in dneve, ko po našem uvozu vozi; primerjaj z derp-ovo vožnjo istega vozila (`straza_opazeno`). Meritev na prazniku 1. 11. (`KOLEDAR.md`). **Prvi vzorec 31. 10. ob 19:30** (7 vozil): derp.si nima drugega vira — bere iste lege NAP, vožnjo pa vozilu določi sam iz lege, ure in voznega reda (TransitClock), mi pa verjamemo `VehicleJourneyRef`. (a) 5× `prezgodaj` in 1300586 (`brez_dneva`, a vožnja šele čez > 45 min): NAP že javlja naslednjo vožnjo, derp.si vozilo drži na tej, ki jo vozi (npr. 469603 proti 469595/469600). (b) 1300158: NAP 430253 ob svoji uri (19:00–20:01), po našem uvozu vozi le 30. 10. (petek), na praznik ne; derp.si jo je pripel. Smer popravka (David 31. 10.: sami računamo, ne od posrednika): vozilo, čigar prijava ni verjetna (napačen dan, vožnja čez > 45 min), pripni **sami** iz lege, ure in voznega reda — `kajros/pripis.py` (skupna koda za vse vire, v senci 0 napačnih od 7 621 + 162, ni priklopljena), pomaga veriga `block_id`. derp-ova vožnja istega vozila (`straza_opazeno`) samo kot primerjava, ne kot vir.
3. **Pokritost po prevozniku** (najdba „Izpad prevoznika ali dela voženj neviden“): vožnje po voznem redu, ki tečejo ≥ 10 min, proti tistim z lego in zamudo. Meritev teče od 31. 10. zvečer: `collector.pokritost` na 5 min v tabelo `pokritost` (35 dni) in `/admin` → Zajem „pokritost“; brez barve. 31. 10. ob 19:00 (po voznem redu / z lego / zamuda v 15 min / zamuda danes): Arriva 19/17/14/18, Nomago 24/22/21/24, LPP 42/30/32/32, vlaki 17/–/15/15, Marprom 7/5/7/7. Zamuda v 15 min podceni medkrajevne (med daljnimi postanki ni zapisa), zato četrti števec. 7. 11. (`KOLEDAR.md`) meje iz tedna: npr. delež pod polovico izhodišča prevoznika 20 min → oranžno, pod desetino → rdeče.
4. ~~**derp.si zamrznjen**~~ — narejeno 31. 10. zvečer: vsebina, ki se 10 min ne spremeni, ne nosi voženj, rezervi pišeta, tabla LPP na zaslonih, zdravje rumeno/oranžno (`zajem.md`, „Zamrznjen vir = molk“).
5. **Uvoz voznega reda ob 4:20 ustavi glavno zanko** — zdravje narejeno 31. 10. zvečer (ea845f3), uvoz vzporedno čaka Davidovo odločitev. Izmerjeno 17.–31. 10. (dnevnik arwena, `KAJROS_REFRESH=subprocess`, `subprocess.run` čaka v niti zanke): zanka stoji 4 min 05 s do 5 min 01 s, 17. 10. 7 min 25 s. Manjka: zamude in lege derp.si (30. 10. ob 4:20–4:23 0 zapisov mestnega LPP na minuto, prej 4–24; tedaj vozi 11 mestnih in 3 primestne LPP), obvestila, senca; lege LPP zemljevid po 180 s skrije. NAP, zemljevid SŽ, Marprom, Kranj tečejo v svojih nitih. **Uvoz zaklene bazo**: pisanje je ena transakcija (`gtfs.import_static`, `with conn:`, ~0,96 mio `sched`), zadnjih ≥ 45–80 s; vsako noč 20.–31. 10. dobi „database is locked“ (busy 30 s) zemljevid SŽ, od 22. 10. še NAP, pogosto Kranj, peroni, obisk (30. 10. lege NAP ob 4:23 71 namesto ~165). Uvoz v svoji niti ali `Popen` bi zanki vrnil ~3,5 min prenosa in razbora, v fazi pisanja pa bi zajem dobil „database is locked“ — zato ne brez odločitve. Narejeno: `meta.zanka_ts` (utrip zanke), `meta.uvoz` (od, do); vrstica `zanka`: med uvozom rumeno „uvoz voznega reda teče N min“, od 15 min oranžno, zanka brez uvoza 10 min tiho rdeče; vrstice `derp_*` se takrat ne ocenjujejo. **Predlog** (David, `KOLEDAR.md`): (a) `Popen` brez čakanja — zanka izgubi 1–2 obhoda ob zaklepu namesto ~9, kot NAP in SŽ že zdaj; (b) uvoz piše v ločeno datoteko in jo v kratki transakciji zamenja — brez zaklepa, a večja sprememba; (c) pusti, zdravje pove resnico.
6. ~~**Nepripeti vlaki zemljevida SŽ**~~ — narejeno 31. 10. zvečer: `iz_lege.sz_vodi_vlak` — derp.si piše vlak, ki ga zemljevid **kaže**, a ga v 120 s ne pripnemo; vlaka, ki ga zemljevid ne kaže, ne (derp.si ima iste zamude z zemljevida, za tak vlak le ostanek: 31. 10. ob 20:40 3 od 22 več od zemljevida, EN 415 z jutra brez zamude, LP 4218 ničla, LPV 2278 pred odhodom). Izmerjeno: delavnik 29.–30. 10. nikoli pripet 1 od 569/571 (LP 4208), pripet šele od 3. postanka 4; praznik 31. 10. nikoli 15 od 233 (del ne vozi); dnevnik ob „spet odgovarja“ 75×: nepripetih 0 (69) ali 1 (6). Številke so v `meta.zamude_sz.nepripeti` in enkrat na dan v dnevniku — teden pozneje preštej (`KOLEDAR.md`).
7. **Zamrznjen zemljevid SŽ z odštevanjem**: straža zamrznitve gleda odtis, ki se spremeni zaradi odštevanja. Drug odtis iz (številka, Vrsta, Postaja, Zamuda_cas).
8. ~~**Izid uvoza in nočnih opravil samo v dnevniku**~~ — narejeno 31. 10. zvečer (21a7560): `meta.uvoz` (izid, razlog, vožnje po prevozniku staro → novo, neuspelih noči), `meta.nocno` po opravilu; vrstica `nocno` rumeno ena neuspela noč, oranžno dve ali padec prevoznika > 40 % (`zajem.md`). Izmerjeno 1.–31. 10.: uvoz vsako noč (od 18. 10. koda 0 16 od 16, prej izpis brez kode), povzetki 32, obrez 31, vreme 31, nobene napake; nihanje voženj mestni LPP ±7 % (okno osmih dni), Kranj −31 % 31. 10.
9. ~~**Izjema v naši obdelavi feeda**~~ — narejeno 31. 10. zvečer (253e45a): `meta.zajem_napake` po koraku zanke (napaka, kje v kodi, od kdaj, koliko zapored), napaka branja vira ne šteje (`viri.iz_vira`); vrstica `zajem_napake` rumeno, od treh zapored oranžno; odgovor derp.si iz dnevnika virov (`zajem.md`, „Izjema v naši obdelavi ≠ molk vira“).
10. Manjše (rumeno): Marprom/Kranj zamrznjen vir zelen (`marprom.py` žigosa z našo uro); primerjava derp.si : zasloni LPP slepa nad 10 min; data.lpp.si prazen brez barve; ovire, ki jih vir ne nosi več, ostanejo do `end_ts`; tabla postaje SŽ, ki se ne razbere, je „0 vlakov“; splošni vir brez meje starosti; ovire brez vezi; vreme z `null`.

Vsaka točka: najprej izmeri na produkciji (samo branje), nato popravek s preizkusom, nato vrstica zdravja po stopnjah zgoraj.
