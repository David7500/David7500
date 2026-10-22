---
paths:
  - "kajros/zasedenost.py"
  - "kajros/static/zasedenost.js"
  - "kajros/static/zasedenost.css"
  - "tests/test_zasedenost.py"
---

# Zasedenost po poročilih potnikov

Od 21. 10. 2026, na prošnjo potnice (LJ–MB ob petkih 20 min prej, ker je avtobus poln). Noben vir zasedenosti ne objavi (derp.si, NAP SIRI-VM, LPP, zemljevid SŽ: 0 vozil); validacije IJPP ima DUJPP in jih po dveh mesecih zbriše. Meritve in pravo: `docs/MERITVE.md`, „Zasedenost“; delovne datoteke `posnetki/zasedenost/`.

## Davidove odločitve (21. 10. 2026)

* **Stopnje:** prazno, pol polno, skoraj polno, polno, vrsta zunaj. Medkrajevni nimajo stojišč („polno“ = vsi sedeži); vlak in mestni LPP „polno“ = stojijo. **„Vrsta zunaj“ šele od 10 min pred voznorednim odhodom** (`ZUNAJ_PRED_S`), prej siv — David: „prav je“ (vrnjeno isti večer).
* **Ne sme motiti:** razdelek na dnu okna (`#zasedenost` v `.run-pot`), zgoraj le vrstica brez okvirja (`#zas-vrh`), samo s podatki.
* **„Kdaj si prišel“ ni vprašanje**: „pridi vsaj N min prej“ iz najzgodnejšega poročila „polno“ ali več (`prejeto`), iz ≥ `PREJ_DNI` dni („vsaj“, ker je videl polno, ne kdaj se je napolnil).
* **Vlaki in ves LPP** („vklopi za vse“).
* `KAJROS_ZASEDENOST` privzeto vklopljeno; `=0` skrije pot in razdelek, obrez teče.

## Ključ, smer, povzetek

* **Odhod = `(agency, train_no, headsign, start_s)`, ne `trip_id`** (medkrajevni nov `trip_id` vsako obdobje, `zamenjava` 86 % proti 99,6 %). Okno ±10 min zavrnjeno (0 več, 2 % zlitih).
* **Postaja = lastnost poročila, ne ključa.**
* **Povzetek čez odhode in prevoznike v isti smeri** (`_primerljiv`, `_ista_smer`: cilj enega med postajami drugega) — pri LPP (`lpp`, `1118`) samo **ista linija**; LPP in ostali se ne mešajo. Na postaji, ±90 min (`PAS_S`), 8 tednov; najprej isti dan v tednu, sicer tip dneva (`tip_dneva`: pon, tor–čet, pet, sob, ned+praznik). Šteje **odhod na dan** (mediana poročil); povzetek od `NAJMANJ` (5) odhodov in `NAJMANJ_DNI` (3) dni. Mediana in razporeditev, ne povprečje. Nasvet = zgornja četrtina dni. **Omrežje v poizvedbi** (4 463 parov vlak/avtobus z iste postaje).
* **Smer se shrani ob poročilu** (`naprej`), ne iz voznega reda (nagrobniki brez `sched`).
* Teče v zahtevi (majhna tabela, indeks na postaji). Če zraste → nočno vzdrževanje.

## Varovalke in zasebnost

* **Identitete ni v bazi.** En glas na napravo, odhod in **postajo** v `_glasovi` (pomnilnik) nad zgoščenim id-jem naprave (`localStorage` `kajros:naprava`) in soljo **obratovalnega** dne. Po IP in UA se ne šteje (aplikacija ima isti UA, mobilna omrežja delijo naslove); po naslovu le `NA_URO` 20. Isti glas stopnjo popravi (prvo „polno“ ostane v `prejeto`), preklic v `PREKLIC_S`.
* Okno oddaje: od ure pred do 3 h po voznoredni uri na postaji; meja `stats.polnoc() + t_s`. **„Te prejšnji ni vzel?“ v dveh korakih** („Da, javi“) — kot povezava se je oddala med drsenjem.
* **Komentar gre skozi `POST /stik`** (`opomba_trip` …, JSON) v nabiralnik z vožnjo v `sporocilo.opomba`; javen šele po objavi skrbnika (`POST /admin/sporocila/{id}`, `akcija=objavi|umakni`). Razlog: osebne podatke najti pred objavo (SEU C-492/23, 2. 12. 2025). Povezave, e-naslovi, telefonske se zavrnejo ob oddaji; `OPOMB_NA_DAN` 20 (deli si `stik.VSEH_NA_DAN`). Žeton obrazca odjemalec drži 90 min (`stik.py` zavrne žeton mlajši od 4 s). Ob objavljeni opombi „Prijavi“ (`/stik?prijava=id`, DSA čl. 16).
* Na pristajalne strani komentarji ne gredo; tam le povzetek (faza 2).
* Hramba 13 mesecev (`HRAMBA_DNI`). Ob napadu SQL na arwenu (`UPDATE zasedenost SET skrito = 1 WHERE …`).

## Odprto

* Faza 2: „pogosto polno“ / „prejšnji poln“ na tabli in v iskalniku (vzorec `deljenje.dopolni`), povzetek na pristajalni, vprašanje na zaslonu „Hvala“ deljenja (`na_vozilu`).
* Zahteva ZDIJZ na DUJPP: `posnetki/zasedenost/zahteva-dujpp.md`, pošlje David.
* Po tednu meriti: poročila na dan, delež oken s poročilom, pasovi LJ–MB s 5 poročili, zavrnjeni komentarji.
