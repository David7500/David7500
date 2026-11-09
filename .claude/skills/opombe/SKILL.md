---
name: opombe
description: Pregled sporočil in opomb potnikov na kajros.app. Ko David reče „preglej sporočila“ ali „preglej opombe“ ali ko je v KOLEDAR.md na vrsti pregled opomb (vsake tri dni). Prebere nabiralnik s produkcije, umakne opombe, ki ne smejo biti javne, in izbriše neželeno pošto.
---

# Pregled sporočil in opomb

Opombe potnikov k vožnjam se od 9. 11. 2026 objavijo same, brez potrditve (David). Pred objavo jih ustavi le filter povezav, e-naslovov in telefonskih številk (`zasedenost._PREPOVEDANO`). Ta pregled je druga varovalka: vsake tri dni preberi vse, kar je prišlo, in odstrani, kar ne sme biti javno.

## Koraki

1. Datum zadnjega pregleda je v `KOLEDAR.md`, „Opravljeno“ (vrstica „Pregled opomb“). Vzemi dan prej, zaradi prekrivanja.
2. `./scripts/admin.sh sporocila <od>` vrne eno vrstico JSON na sporočilo: `id`, `prispelo`, `besedilo`, `email` (ali je pustil naslov, ne naslov sam), `opomba` (oznaka vožnje ali `null` za navadno sporočilo), `objavljena`, `st` (javna številka opombe). Seznam ima največ zadnjih 100 sporočil.
3. Vsako besedilo preberi in presodi po spodnjih merilih.
4. Opombo, ki ne sme biti javna: `./scripts/admin.sh umakni <id>`. Izvirnik ostane v nabiralniku, David ga vidi kot „umaknjena“.
5. Neželeno pošto (oglas, nesmisel, robot): `./scripts/admin.sh izbrisi <id>`.
6. Izid vpiši v `KOLEDAR.md`, „Opravljeno“: „Pregled opomb“, koliko prebranih, koliko umaknjenih in izbrisanih, z `id` in razlogom v nekaj besedah. Besedila umaknjenega ne prepisuj (če ima osebni podatek, bi ga s tem shranil v git). Nato v „Na vrsti“ dodaj naslednji pregled čez tri dni.
7. Davidu na kratko: koliko prebranih, kaj umaknjeno ali izbrisano in zakaj, katera sporočila čakajo nanj (vprašanja, predlogi, prijave).

## Umakni opombo, če

* **ima osebni podatek**: ime ali priimek, vzdevek, opis, po katerem se prepozna človek („sprevodnica s kitko na progi Jesenice ob 7.10“), registrska tablica zasebnega avta, naslov. Številka vozila ali vlaka ni osebni podatek.
* **žali ali grozi** komu (vozniku, potniku, skupini ljudi), ali je sovražna.
* **je oglas ali zavaja**: vabi drugam, prodaja, ali trdi očitno neresnico o vožnji, ki bi potnika napotila narobe (npr. „ta vlak danes ne vozi“, ko je vozil).
* **ni o vožnji**: pogovor, šala, preizkus („test“, „asdf“) — ta je tudi za izbris.
* **je prijavljena upravičeno**: sporočilo „Prijavljam opombo potnika št. N, ker …“. Opombo s to številko (`st`) poišči in presodi po istih merilih; prijavo pusti v nabiralniku za Davida.

## Pusti

* Kritiko prevoznika, tudi ostro, brez imen in brez žalitev („spet 20 min zamude, sramota“).
* Kratke ali slovnično slabe opombe, ki povedo kaj o vožnji („Tak 5 mest“).
* Podatke, ki jih ne moreš preveriti (nadomestni avtobus, pokvarjena vrata): potnik jih je videl, mi ne.

Pri dvomu opombo umakni in Davidu povej, zakaj: umik je povraten (gumb „objavi pri vožnji“ v `/admin`), objava osebnega podatka ni.

## Navadna sporočila

Niso javna, berejo jih David. Briši samo očitno neželeno pošto. Vprašanja, predloge in prijave napak pusti, Davidu jih naštej na kratko (en stavek vsako). Na sporočila ne odgovarjaj sam.
