# Koledar projekta

Kaj je na vrsti in kdaj. Ko David v projektu napiše **„poglej koledar“**, Claude naredi vse, kar je zapadlo (datum je danes ali prej, stanje „čaka“), izid vpiše spodaj v „Opravljeno“ in doda nove roke, ki se pri delu pokažejo. Postopek: skill `koledar` (`.claude/skills/koledar/SKILL.md`).

Podrobnosti niso tu, ampak v dokumentu v zadnjem stolpcu. Koledar pove samo kdaj, kaj in zakaj.

## Na vrsti

| kdaj | kdo | kaj in zakaj | kako | podrobnosti |
|---|---|---|---|---|
| **sob 31. 10. 2026**, zvečer (nova seja), najkasneje ned 1. 11. zjutraj | Claude, David | **Predaja seje 31. 10.: najprej pregled in objava** aeadaa9 (LPP 2 +92) in df1d5ab/892f019 (senca pripisa NAP, mora teči dopoldne). Nato vse vnose za 1. 11. spodaj po vrsti. | `git diff 47527ed..HEAD -- kajros/`, `./scripts/preveri.sh`, objava po odobritvi | [docs/presoja/2026-10-31-predaja.md](docs/presoja/2026-10-31-predaja.md) |
| **ned 1. 11. 2026**, 9–11 h | Claude | **NAP na praznik ne pripne vozil.** 31. 10. je NAP 13 vozil videl brez naše vožnje (`brez_dneva`), derp.si pa jih je pripel. Ker NAP vodi medkrajevne, so bila brez zamude. Jutri je spet praznik, zato je to najboljša priložnost za meritev vzroka. Vzorec nepripetih z vzrokom (`meta.nap.nepripeti`) teče od 31. 10. zvečer (ob objavi `brez_dneva` 4, pripetih 65). Senca pripisa teče od objave df1d5ab (pogoj: David objavi zvečer 31. 10. ali zjutraj, sicer meritve ni). Načrt: (1) dopoldne `scp .claude/skills/preveri-vire/skripte/pripis_nap.py david@192.168.1.46:/tmp/ && ssh david@192.168.1.46 '/opt/kajros/.venv/bin/python -I /tmp/pripis_nap.py 2026-11-01'` (isto / drugo / derp nima / mi nimamo po vzroku in prevozniku, NAP isti dan, primeri) in `/admin` → NAP „senca pripisa · danes“; „par · derp drugo“ in „NAP nikoli“ preglej na primerih; (2) če se ujema brez napačnih parov, ga isti dan priklopi za vozila z neverjetno prijavo (napačen dan, vožnja čez > 45 min), s preizkusi, objava po Davidovi odobritvi; sicer senca do 7. 11. | `/preveri-vire`, točka 2, `skripte/pripis_nap.py` | [docs/VIRI-PRESOJA.md](docs/VIRI-PRESOJA.md) |
| ned 1. 11. 2026, po objavi aeadaa9 | Claude | Okno mestnega LPP z „živa napoved LPP“ in brez meritve: postanki za vozilom ne smejo več nositi +60 do +90 (Davidov LPP 2 +92, 31. 10.). | okno vožnje, `/api/train/{no}/run` | [docs/presoja/2026-10-31-napovedi.md](docs/presoja/2026-10-31-napovedi.md) |
| pon 2. 11. 2026 | Claude | **Pregled napovedi, drugi krog.** Posnetek 31. 10. je imel časovni zamik, zato (d) meja pred lego, (h) zemljevid proti oknu, (i) tabla proti oknu in naša ocena na dolgem odseku še niso potrjeni. | `docs/presoja/napovedi/sync.py`, `sync_analiza.py` | [docs/presoja/2026-10-31-napovedi.md](docs/presoja/2026-10-31-napovedi.md) |
| sre 4. 11. 2026 | Claude in David | **Trenutna zamuda iz lege za NAP na dolgih odsekih** (≥ 15 min): okno kaže staro meritev, 45 % odsekov ≥ 30 min nad 5 min, 164–203 voženj na dan; ocena iz lege MAE 6,4 → 3,4 min. Najprej senca, nato obe merili proti prenosu, odloči David. Isti teden: mestni LPP brez `trip_update` dobi meritev (iz lege ali pripis zaslona) v senci; vozilo na dveh vožnjah po menjavi (dedup po `vehicle_id`). | senca, `kajros backtest`, `kajros ocena` | [docs/presoja/2026-10-31-napovedi.md](docs/presoja/2026-10-31-napovedi.md) |
| ned 1. 11. 2026 | Claude | Preveri, da je ponoči prvič tekel nočni račun opazovano (vrstica `opazovano` zelena). Preveri tudi, da je popravek dvojnikov znižal „vožnje brez voznega reda LPP“. | `/preveri-vire` | [docs/OPAZOVANO.md](docs/OPAZOVANO.md) |
| od ned 1. 11. 2026 | Claude, ko reče David | Statistika, faza 6: oktober je cel, lahko nastane mesečno poročilo. | po dogovoru | [docs/STATISTIKA.md](docs/STATISTIKA.md) |
| **ned 1. 11. 2026**, po 4.25 (objavljeno 31. 10. ob 21.50) | Claude | **Zdravje med uvozom voznega reda.** Uvoz ob 4:20 vsako noč 4–5 min ustavi glavno zanko; prej se je to kazalo kot „derp.si ne odgovarja“, zdaj mora vrstica `zanka` povedati „uvoz voznega reda teče N min“ in nato spet zelena. Preveri tudi, da `zajem_napake` ostane zelena (ali pove pravo izjemo). | `./scripts/admin.sh podatki`, dnevnik 4:19–4:27 | [docs/VIRI-PRESOJA.md](docs/VIRI-PRESOJA.md), točki 5 in 9 |
| pon 2. 11. 2026 | David | **Odločitev: uvoz voznega reda vzporedno z zanko zajema?** Zdaj zanka ~4,5 min na noč čaka uvoz (mestni in primestni LPP brez zamud in leg derp.si). Vzporedno bi izgubila le 1–2 obhoda, a uvoz bazo zaklene za ≥ 45–80 s in zajem bi takrat dobil „database is locked“ (NAP in zemljevid SŽ ga dobita že zdaj vsako noč). Možnosti (a) `Popen`, (b) ločena datoteka, (c) pusti. | odgovor Claudu | [docs/VIRI-PRESOJA.md](docs/VIRI-PRESOJA.md), točka 5 |
| čet 5. 11. 2026, po 3.30 | Claude | Opazovano, prvi preizkus v živo: zapora Vrbanske (Marprom P7, od 3. 11.). Ali se izid odpre? | `kajros opazovano` | [docs/OPAZOVANO.md](docs/OPAZOVANO.md) |
| **sob 7. 11. 2026** | Claude in David | **Teden podatkov je zbran.** (1) Ali varovalo „zamuda raste z uro“ vklopiti zares (`KAJROS_DRSI=vodi`). Čez teden v `/admin` odpri nekaj povezav te vrstice: vozilo v garaži = fantom, v zastoju = resnica. (2) Meje za pokritost po prevozniku iz tabele `pokritost`. | `/preveri-vire`, točki 1 in 3 | [docs/VIRI-PRESOJA.md](docs/VIRI-PRESOJA.md) |
| sob 7. 11. 2026 | Claude | **Nepripeti vlaki zemljevida SŽ, ki jih piše derp.si.** Od 31. 10. derp.si piše vlak, ki ga zemljevid kaže, a ga mi ne pripnemo (delavnik ~1 vlak, LP 4208). Preštej teden: kateri vlaki, kolikokrat, ali je derp-ova zamuda ista kot kasneje pripeta; zakaj se ne pripnejo (vozni red proti vrstici zemljevida). | `journalctl -u kajros.service --since -7d \| grep 'ki ga ne pripnemo'` | [docs/VIRI-PRESOJA.md](docs/VIRI-PRESOJA.md), točka 6 |
| sob 7. 11. 2026 | Claude | Veriga: ponovi meritev istega vozila za LPP 25, primestni in mestni LPP na `straza_opazeno` 30. 10.–6. 11. (podatki 30. 10. izpadejo 14. 11.). Teden po objavi popravka ponovi `v8.py` za medkrajevne (cilj ≥ 98,8 % pet minut pred odhodom). Za LPP zgodovine leg ni: iz `straza_opazeno` preveri vsaj, da je vozilo verige isto kot vozilo te vožnje. | `docs/presoja/veriga/v3.py`–`v8.py` | [docs/presoja/2026-10-31-veriga.md](docs/presoja/2026-10-31-veriga.md), razdelka 8 in 9 |
| čet 26. 11. 2026 | Claude | Opazovano: konec zapore Vrbanske. Kako hitro se izid zapre? | `kajros opazovano` | [docs/OPAZOVANO.md](docs/OPAZOVANO.md) |
| pet 4. 12. 2026 | Claude | **Menjava voznega reda SŽ 13. 12.** Vlaki so v našem voznem redu le do 11. 12.; od danes je vrstica oranžna, če novega ni. Preveri, da ima zip IJPP vlake po 13. 12., in poženi uvoz. | `/preveri-vire` | `.claude/rules/zajem.md`, „Nov vozni red“ |
| pon 14. 12. 2026 | Claude | Dan po menjavi: nepripeti vlaki zemljevida SŽ (nove številke), zamenjave, tiri, statistika po številki. | `/preveri-vire` | [docs/VIRI-PRESOJA.md](docs/VIRI-PRESOJA.md), točka 6 |
| tor 15. 12. 2026 | David | **Marprom: delavnikov 2027 ni v nobenem viru.** Če Marprom do danes ne objavi novega zipa, mu piše David. | pismo | spomin `marprom-obvoz-vozni-red` |
| pet 26. 3. 2027 | Claude | Pred premikom ure (ned 28. 3. 2027) popravi `journey.now_seconds`: do treh zjutraj je današnji okvir za uro narobe. | koda | `.claude/rules/strezba.md`, „Odprto“ |

## Roki virov (zdravje jih straži samo)

Teh ni treba gledati na roko. `/admin` jih pokaže oranžno teden prej in rdeče dva dni prej. Tu so, da veva, kdaj pridejo.

| rok | kaj | kdaj opozori |
|---|---|---|
| 30. 11. 2026 | vozni red Kranja (MOK, mesec naprej) | oranžno 23. 11., če ni novega |
| 11. 12. 2026 | vozni red vlakov SŽ v zipu IJPP (menjava 13. 12.) | oranžno 4. 12., rdeče 9. 12. |
| 31. 12. 2026 | delavniki Marproma; prvi brez voženj pon 4. 1. 2027 | rdeče 30. 12. |
| 2027 | Google: preverjen razvijalec za namestitve na certificiranih telefonih (Android) — Davidova odločitev | datum še ni znan |
| konec 2027 | RT vlakov SŽ na NAP (DUJPP) — takrat uradni vir namesto zemljevida SŽ | — |

## Vedno

* **Oranžno v `/admin` ali pošta „kajros: za pregled“** pomeni isti dan novo sejo z `/preveri-vire`.
* **Rdeče ali pošta „kajros: stoji“** pomeni takoj ponovni zagon (`sudo systemctl restart kajros.service` na arwenu), nato `/preveri-vire`.
* **Vsak ponedeljek** kratek `/preveri-vire`: rumene vrstice, ki se ponavljajo, in vrstica „zamuda raste z uro“.

## Opravljeno

| kdaj | kaj | izid |
|---|---|---|
| sob 31. 10. 2026 | Presoja virov, tri stopnje opozoril, povezave na vozila, skill `/preveri-vire` | 5bb51c3 … c55fb80, objavljeno; najdbe in odprto v [docs/VIRI-PRESOJA.md](docs/VIRI-PRESOJA.md) |
| sob 31. 10. 2026 | Meritvi za odprte luknje: nepripeta vozila NAP, pokritost po prevozniku; koledar | da7c301, 2e68fdd, objavljeno; prva vrstica pokritosti: Arriva 27 po voznem redu, 22 z zamudo v 15 min, LPP 31 / 23, vlaki 18 / 16 |
| sob 31. 10. 2026 | „Še na prejšnji vožnji“ samo, ko vozilo prejšnjo res še vozi; zamrznjen derp.si velja kot molk (točka 4) | 02bc087, e51931d, objavljeno 31. 10. zvečer; trditev pet minut pred odhodom prav 98,8–99,2 % (prej 34–41 %), [docs/MERITVE.md](docs/MERITVE.md) „Veriga vozila“ |
| sob 31. 10. 2026 | Točke 9, 5, 8, 6, 7 iz presoje virov (agent) in zamrznjen zemljevid SŽ ne vodi | 253e45a … 47527ed, objavljeno 31. 10. ob 21.50; nove vrstice zdravja `zajem_napake`, `zanka`, `nocno`; odprto: odločitev o uvozu (2. 11.), [docs/VIRI-PRESOJA.md](docs/VIRI-PRESOJA.md) |
