---
name: koledar
description: Ko David napiše „poglej koledar“ ali vpraša, kaj je na vrsti v projektu Kajros. Prebere KOLEDAR.md, naredi vse zapadlo, izid vpiše v „Opravljeno“ in doda nove roke.
---

# Koledar

`KOLEDAR.md` v korenu projekta je skupni seznam rokov za Davida in Claude. David ga bere sam, zato mora ostati kratek in berljiv: datum z dnevom v tednu, „kaj in zakaj“ v stavku, brez kode razen imen ukazov. Podrobnosti so v povezanem dokumentu, ne v koledarju.

## Ko David reče „poglej koledar“

1. Ugotovi današnji datum (`date`) in preberi `KOLEDAR.md`.
2. Za vsak vnos v „Na vrsti“ z datumom danes ali prej:
   * **kdo = Claude**: naredi ga po stolpcu „kako“ (skill, ukaz) in po dokumentu v „podrobnostih“. Pred delom preveri pogoj, ki ga vnos navaja (npr. „objavljen commit“).
   * **kdo = David**: povej mu, kaj mora narediti, in mu pripravi, kar se da (osnutek pisma, ukaz). Ne delaj namesto njega.
   * Česar ne moreš končati, pusti v „Na vrsti“ in v stolpec „kaj“ dopiši „čaka: <zakaj>“.
3. Narejeno premakni v „Opravljeno“: datum, kaj, izid v eni vrstici (številka, commit, odločitev).
4. Rok, ki se pri delu pokaže, dodaj v „Na vrsti“ po vrsti datumov. Rok, ki ga straži zdravje samo (konec voznega reda), gre v „Roki virov“.
5. Vnose za prihodnost samo preglej: če je pogoj očitno odpadel ali se je datum premaknil, popravi in povej.
6. Na koncu Davidu kratko: kaj je narejeno, kaj ostane, kdaj je naslednji vnos.

## Pravila

* Zapadli vnos ni razlog za veliko delo v isti seji: večje delo postane nov vnos z datumom (nova seja).
* Tehnično odločitev (popravek, meja, vklop varovala) sprejme Claude po meritvi in jo zapiše z razlogom (David 1. in 3. 11. 2026: „sam se odločaš, bolj poznaš kot jaz“). Davidu ostane, kar je njegovo: pismo, prijava, denar, sporočilo v njegovem imenu.
* Koledar ni seznam idej. Vnos ima datum ali pogoj, ki ga sproži, sicer ne sodi vanj.
* Vpisuje vsaka seja in vsak agent, ko se pri delu pokaže naloga za pozneje (`CLAUDE.md`). Agent brez pravice pisanja rok vrne v izidu.
* Ob vsakem vnosu v „Opravljeno“ preveri, da so številke in odločitve tudi v trajnem zapisu (`docs/MERITVE.md`, commit, `.claude/rules/`). Koledar je kazalo, ne arhiv.
