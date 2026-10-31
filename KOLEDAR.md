# Koledar projekta

Kaj je na vrsti in kdaj. Ko David v projektu napiše **„poglej koledar“**, Claude naredi vse, kar je zapadlo (datum je danes ali prej, stanje „čaka“), izid vpiše spodaj v „Opravljeno“ in doda nove roke, ki se pri delu pokažejo. Postopek: skill `koledar` (`.claude/skills/koledar/SKILL.md`).

Podrobnosti niso tu, ampak v dokumentu v zadnjem stolpcu. Koledar pove samo kdaj, kaj in zakaj.

## Na vrsti

| kdaj | kdo | kaj in zakaj | kako | podrobnosti |
|---|---|---|---|---|
| **ned 1. 11. 2026**, 9–11 h | Claude | **NAP na praznik ne pripne vozil.** 31. 10. je NAP 13 vozil videl brez naše vožnje (`brez_dneva`), derp.si pa jih je pripel. Ker NAP vodi medkrajevne, so bila brez zamude. Jutri je spet praznik, zato je to najboljša priložnost za meritev vzroka. Pogoj: objavljen commit z vzorcem nepripetih (`meta.nap.nepripeti`). | `/preveri-vire`, točka 2 | [docs/VIRI-PRESOJA.md](docs/VIRI-PRESOJA.md) |
| ned 1. 11. 2026 | Claude | Preveri, da je ponoči prvič tekel nočni račun opazovano (vrstica `opazovano` zelena). Preveri tudi, da je popravek dvojnikov znižal „vožnje brez voznega reda LPP“. | `/preveri-vire` | [docs/OPAZOVANO.md](docs/OPAZOVANO.md) |
| od ned 1. 11. 2026 | Claude, ko reče David | Statistika, faza 6: oktober je cel, lahko nastane mesečno poročilo. | po dogovoru | [docs/STATISTIKA.md](docs/STATISTIKA.md) |
| čet 5. 11. 2026, po 3.30 | Claude | Opazovano, prvi preizkus v živo: zapora Vrbanske (Marprom P7, od 3. 11.). Ali se izid odpre? | `kajros opazovano` | [docs/OPAZOVANO.md](docs/OPAZOVANO.md) |
| **sob 7. 11. 2026** | Claude in David | **Teden podatkov je zbran.** (1) Ali varovalo „zamuda raste z uro“ vklopiti zares (`KAJROS_DRSI=vodi`). Čez teden v `/admin` odpri nekaj povezav te vrstice: vozilo v garaži = fantom, v zastoju = resnica. (2) Meje za pokritost po prevozniku iz tabele `pokritost`. | `/preveri-vire`, točki 1 in 3 | [docs/VIRI-PRESOJA.md](docs/VIRI-PRESOJA.md) |
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
