---
paths:
  - "kajros/zasedenost.py"
  - "kajros/static/zasedenost.js"
  - "kajros/static/zasedenost.css"
  - "tests/test_zasedenost.py"
---

# Zasedenost po poročilih potnikov

Nastalo 21. 10. 2026 na prošnjo potnice (Ljubljana–Maribor: ob petkih pride 20 min prej, ker je avtobus ob odhodu poln). Noben vir zasedenosti ne objavi (derp.si, NAP SIRI-VM, LPP, zemljevid SŽ: 0 vozil). Validacije IJPP ima DUJPP in jih po dveh mesecih zbriše. Ljudi, ki ostanejo zunaj, ne beleži nihče. Meritve in pravo: `docs/MERITVE.md`, „Zasedenost“; delovne datoteke v `posnetki/zasedenost/` (predlog, kritika, pravo, prototip).

## Kaj je odločil David (21. 10. 2026)

* **Stopnje:** prazno, pol polno, skoraj polno, polno, vrsta zunaj (Davidovo „polno + vrste zunaj“). Medkrajevni avtobusi nimajo stojišč: „polno“ = vsi sedeži zasedeni. Pri vlaku in mestnem LPP „polno“ pomeni, da stojijo. „Vrsta zunaj“ se vidi že pred odhodom (avtobus poln na peronu), zato nima časovne omejitve -- do 21. 10. zvečer je veljala šele od 10 min pred odhodom in gumb je bil siv brez razlage (David).
* **Ne sme motiti:** razdelek je na dnu okna vožnje (`#zasedenost` v `.run-pot`, na namizju pod časovnico), zgoraj samo vrstica brez okvirja (`#zas-vrh`), in to le, kadar so podatki. Prototip in videz potrdil.
* **„Kdaj si prišel na postajo“ ni vprašanje.** Potnik pove trenutno stanje; „pridi vsaj N min prej“ se izpelje iz časa najzgodnejšega poročila „polno“ ali več pred odhodom (`prejeto`), iz vsaj `PREJ_DNI` dni. Poročilo pove, kdaj je potnik videl polno, ne kdaj se je napolnil -- zato „vsaj“.
* **Vlaki tudi, in ves LPP** (od 21. 10. 2026 zvečer, David: „vklopi za vse“). Prej je bil mestni LPP izklopljen po viru (`agency = 'lpp'`), LPP 25 iz IJPP (`1118`) pa ne -- potnik je pri eni liniji LPP videl gumbe, pri drugi ne.
* **Stikalo** `KAJROS_ZASEDENOST`, privzeto vklopljeno od objave 21. 10. 2026 (David: „kar objavi“); `=0` pot in razdelek skrije, obrez poročil teče naprej.

## Ključ, smer, povzetek

* **Odhod = `(agency, train_no, headsign, start_s)`, ne `trip_id`.** Medkrajevni dobijo nov `trip_id` ob vsakem obdobju voznega reda in `zamenjava` jih ne poveže (86 % proti 99,6 %, MERITVE). Okno ±10 min v ključu je bilo izmerjeno in zavrnjeno: ne ujame niti enega odhoda več, zlije pa 2 % različnih (A2527 15:25 in 15:30).
* **Postaja je lastnost poročila, ne ključa** -- sicer bi se poročila istega odhoda razsula po 17 postankih.
* **Povzetek gre čez odhode in prevoznike v isti smeri** (`_primerljiv`, `_ista_smer`: cilj enega je med postajami drugega) -- razen pri LPP (`lpp` in `1118`), kjer šteje samo **ista linija**: na postajališču čakaš na 11, ne na 6, in mestni avtobus do Stadiona ni v smeri Maribora, čeprav je Stadion na poti medkrajevnega. LPP in ostali se nikoli ne mešajo. Na postaji, ±90 min (`PAS_S`), zadnjih 8 tednov, najprej isti dan v tednu, sicer tip dneva (`tip_dneva`: pon, tor–čet, pet, sob, ned+praznik; ponedeljek ima v voznem redu LJ ↔ MB ojačitve, torek–četrtek je enak). Šteje **odhod na dan** (mediana njegovih poročil), ne poročilo: povzetek šele od `NAJMANJ` (5) takih in `NAJMANJ_DNI` (3) različnih dni -- pet potnikov enega avtobusa ali en naslov s petimi id-ji naprave ni navada (pregled e955c1a). Povprečja stopenj ni -- mediana in razporeditev. Nasvet „pridi vsaj N min prej“ je zgornja četrtina dni, ne največja vrednost. **Omrežje je v poizvedbi**: vlak in avtobus z iste postaje v isto smer se ne mešata (na razvojni bazi 4 463 takih parov), „polno“ pri vlaku pomeni drugo.
* **Smer se shrani ob poročilu** (`naprej`: postaje za postajo poročila) in se ne bere iz voznega reda: nagrobniki nimajo `sched`.
* Teče v zahtevi: majhna tabela, indeks na postaji, osem tednov. Če zraste, gre povzetek v nočno vzdrževanje (pravilo v CLAUDE.md o agregatu).

## Varovalke in zasebnost

* **Identitete ni v bazi.** En glas na napravo, odhod in **postajo** drži `_glasovi` v pomnilniku nad zgoščenim naključnim id-jem naprave (`localStorage` `kajros:naprava`, nastane ob prvem poročilu) in soljo **obratovalnega** dne (popravek po polnoči je isti potnik). Postaja v glasu: popravek z druge postaje bi sicer obdržal `prejeto` s prve. Po IP in UA se glasovi ne štejejo (aplikacija ima za vse UA „Kajros“, mobilna omrežja delijo naslove: sopotnik bi dobil „že oddano“); po naslovu le `NA_URO` 20. Isti glas stopnjo popravi (prvo „polno“ ostane v `prejeto`), preklic v `PREKLIC_S` od zadnjega dotika.
* Okno oddaje: od ure pred voznoredno uro na postaji do 3 h po njej; meja `stats.polnoc() + t_s` (polnoč, premik ure). **„Te prejšnji ni vzel?“ v dveh korakih** (potrditev „Da, javi“): kot povezava se je na telefonu oddala ob dotiku med drsenjem (David, 21. 10. 2026).
* **Komentar ne gre skozi to pot**, ampak skozi `POST /stik` (`opomba_trip` …, odgovor JSON) v nabiralnik, z vožnjo v `sporocilo.opomba`. Javen je šele, ko ga skrbnik objavi (`POST /admin/sporocila/{id}`, `akcija=objavi|umakni`; brisanje sporočila ga umakne). Razlog: kdor objavlja uporabniško besedilo, mora osebne podatke v njem najti pred objavo (SEU, Russmedia, C-492/23, 2. 12. 2025). Povezave, e-naslovi in telefonske številke se zavrnejo že ob oddaji; opombe imajo svoj strop (`OPOMB_NA_DAN` 20), ker si z nabiralnikom delijo `stik.VSEH_NA_DAN`. Žeton obrazca odjemalec drži 90 min: `stik.py` zavrne žeton, mlajši od 4 s, in osvežitev na minuto bi ga sicer vsakič zamenjala. Ob objavljeni opombi gumb „Prijavi“ (`/stik?prijava=id`, DSA čl. 16).
* Na pristajalne strani komentarji ne gredo (iskalniki, `ai-train=yes`); tam bi smel biti samo povzetek (faza 2).
* Hramba 13 mesecev (`HRAMBA_DNI`), nočno vzdrževanje. Poročilo ob napadu skrije SQL na arwenu (`UPDATE zasedenost SET skrito = 1 WHERE …`); gumba in ukaza ni, dokler ga ne bo treba.

## Odprto

* Faza 2: oznaka „pogosto polno“ / „prejšnji poln“ na tabli in v iskalniku (`deljenje.dopolni` kot vzorec), povzetek na pristajalni strani relacije, vprašanje na zaslonu „Hvala“ ob koncu deljenja lege (`na_vozilu`).
* Zahteva ZDIJZ na DUJPP: osnutek `posnetki/zasedenost/zahteva-dujpp.md`, pošlje David v svojem imenu.
* Po objavi meriti: poročila na dan, delež oken s poročilom, koliko pasov LJ–MB doseže 5 poročil, delež zavrnjenih komentarjev.
