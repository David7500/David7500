# Statistika — naročilo, načrt, stanje

Delovni dokument za sistem strani s statistiko. Delo teče čez več 5-urnih oken
porabe; ob nadaljevanju (ali po compactu) najprej preberi ta dokument.

## Naročilo (David, 29. 10. 2026)

Sistem strani za statistiko, „mora biti dobro narejeno“. Najprej premisli, kaj
vse vključiti. Davidovi primeri:

1. kako dobre so naše napovedi zamud v primerjavi z uradnimi in s konkurenco;
2. statistika za vsako vozilo in za vsakega prevoznika;
3. relacije — npr. kdaj si z javnim prevozom hitreje kot z avtom;
4. SŽ: pomanjkljivosti in napake — npr. uradna aplikacija kaže, da je vlak že
   odpeljal, v resnici pa še čaka na prejšnji postaji ali nekje vmes;
5. še kaj, kar bi uporabnika zanimalo.

Pravilo seje: pri 90 % 5-urnega okna se ustavi in sem zapiši predajo.
Subagente samo, kjer je to učinkovito (spomin `agenti-in-okno`).

## Načela

* Meri, ne domnevaj: vsaka številka na strani ima vzorec in obdobje.
* Agregat čez zgodovino se ne računa v zahtevi: nočni izračun v `povzetek`
  (nova `kind`), stran pove čas izračuna.
* Primerjava napovedi samo **parna** (isti nabor vrstic za vse modele).
* Zamuda = zaokrožena minuta, razred po isti minuti (`oznake.md`); „točen“ na
  strani vedno s pragom z besedo („v 5 min“).
* Strop `stats.MAX_REALNA_ZAMUDA_S` (3 h) pri vsakem agregatu.
* Stran za potnika: kratko, brez tehničnih podrobnosti; slog E (M3 Expressive),
  telefon najprej. Design potrdi David pred izvedbo.
* Izris na strežniku (kot pristajalne): HTML + vgrajen SVG, brez JS za branje;
  JSON pod `/api/statistika/…`. Brez novih odvisnosti.
* Prejšnja `/app/statistika` („Kdaj potovati“) umaknjena 19. 9. 2026, ker v tisti
  obliki ni bila uporabna. „Kdaj potovati“ se vrne samo kot del strani vožnje
  ali relacije, ne kot samostojna stran.

## Kaj podatki dovolijo (izmerjeno 29. 10. 2026, kopija baze z arwena)

| vir | obseg |
|---|---|
| `run` | vlaki od 21. 8. (70 dni, 31 627 voženj-dni), avtobusi od 29. 8. (62 dni, 534 173) |
| `napoved` (senca) | od 29. 9.: avtobusi 1,05 mio (15 min prej), vlaki 159 k (25 min prej) |
| `deljenje_prehod` | vlaki 86 prehodov iz 27 deljenj, avtobusi 506 iz 66 — edina resnica za prehod |
| `gps_prehod` | avtobusi 1,63 mio od 15. 10. |
| `sz_zamuda` / `delay_report` | od 28. 9. / 28. 8. (226 k poročil) |
| `peron` | 86 k od 25. 9., 90 postaj |
| `promet.sqlite` | AC: 10 odsekov (LJ–KP, LJ–MB, LJ–Karavanke, LJ–Obrežje, obvoznica) vsakih ~5 min od 14. 10.; FCD 15,9 mio vrstic, 311 k odsekov (preslikava na cesto še ni) |
| `weather` | od 16. 8., 269 celic |
| `zasedenost` | 28 poročil od 21. 10. — premalo |
| `povzetek` | `breakdowns`, `network_stats`, `napake_sence`, `pristanek` (nočno) |

Pokritost: vlaki od 11. 10. 99–100 % voženj (zemljevid SŽ), **nadomestni
avtobusi SŽ 0 od 777** (18 dni). Marprom in Kranj šele od 27. 10.

Merjeno za ta načrt (podrobno v `docs/MERITVE.md`, 29. 10. 2026):

* **SŽ pokaže vlak kot odpeljan, preden odpelje**: na 61 odhodih s prehodom
  potnika mediana 2,7 min prezgodaj, ≥ 2 min pri 66 %, ≥ 10 min pri 23 %.
  Na 109 383 postankih je SŽ odhodno zamudo že „prevoženega“ postanka pozneje
  dvignil za ≥ 2 min pri 20,2 %; na izhodišču točen odhod, ki to ni, 17,8 %.
* **Senca po prevoznikih**: vlaki na poti naš MAE 2,58 min, prenos (= kar
  kaže SŽ) 3,39, vozni red 7,28; avtobusi povsod boljši od prevoznikove
  napovedi (npr. Arriva 2,31 proti 3,86, mestni LPP 1,93 proti 2,04).
* **Točnost na cilju, 1.–28. 10.** (v 5 min / povprečje / ≥ 15 min): SŽ 59 % /
  7,5 min / 17 %; Arriva 75 % / 3,9 / 8 %; Nomago 82 % / 2,4 / 4 %; LPP
  primestni 64 % / 4,1 / 9 %; mestni LPP 77 % / 3,8 / 3 %; AP MS 88 % / 2,1 /
  3 %. Nočni `breakdowns` za vlake: 58,3 % v 5 min, mediana 3 min.
* **Vlak proti avtu na avtocesti** (11.–28. 10., delavniki, postaja–postaja
  proti odseku AC): LJ→MB vlak mediana 122–173 min, avto 70–75; LJ→KP 170 proti
  65; LJ→Jesenice 60–90 proti 38; LJ→Dobova 132–151 proti 62. Avto povsod
  ~2× hitrejši. Gneča: MB→LJ ob 7h 85 min (prosto 62, p90 102), obvoznica
  zunanji krog ob 15h 30 min (prosto 18, p90 58).

## Katalog (predlog)

Oznaka izvedljivosti: **zdaj** = podatki so · **pozneje** = rabi čas zajema ali
večje delo · **ne** = podatka ni.

### 1. Napovedi — `/statistika/napovedi` (zdaj)

* Parna primerjava ob potnikovem pogledu (vlak 25, avtobus 15 min prej):
  Kajros · prevoznik (uradno) · trenutna zamuda naprej (tako kaže SŽ in
  po pregledu 19. 9. zamudil.si) · vozni red. MAE, delež v 1 in 3 min, po
  omrežju in prevozniku. Vir `napoved`.
* Krivulja po času do odhoda (`napake_sence`, korak 30 s od −30 min).
* Smer napake: kolikokrat bi napoved potnika pustila na peronu, kolikokrat
  čaka. Avtobusi odpeljejo prezgodaj pri ~25 % (MERITVE 6. 9.).
* Po tednih: ali se izboljšujemo. Nasvet: rezerva 5 min (budilka).

### 2. Prevozniki — `/statistika/prevozniki` + `/statistika/prevoznik/{ime}` (zdaj)

* Točnost na cilju v 5 min, mediana, delež ≥ 15 min; trend po dnevih,
  po urah, po dnevih v tednu.
* Kaj prevoznik objavlja: delež voženj z živim podatkom, lega vozil, ali
  napoveduje in kako dobro (MAE prevoznikove napovedi), prezgodnji odhodi.
* Najbolj in najmanj točne linije/vožnje prevoznika (z vzorcem).
* Poštenost: mestni in medkrajevni ločeno, različni začetki zajema povedani.

### 3. Vožnja in linija — `/statistika/vlak/{št}`, `/statistika/linija/{prevoznik}/{št}` (zdaj)

* Vlak: točnost 30/90 dni, koledar dni, kje na progi zamudo nabere (po
  postajah), dan v tednu, najhujši dnevi z vzrokom (ovira, vreme), tir.
* Avtobusna linija: zanesljivost po odhodu (uri), po postajališču,
  prezgodnji odhodi. Fizično vozilo (garažna številka) ne — potniku nič ne pove.
* Lestvice najbolj/najmanj točnih z vzorcem.
* Past: šolski vozni red zamenja avtobusne vožnje → združuj po liniji in uri.

### 4. Relacije — `/statistika/relacije` + razdelek na `/vlak/{od}/{cilj}` (deloma zdaj)

* Vlak ali avtobus na isti relaciji (zdaj): čas potovanja z izmerjeno
  zamudo, točnost, pogostost.
* Vlak ali avto, avtocestni koridorji (zdaj, AC od 14. 10.): pošteno od
  središča do središča (dostop in parkiranje povedana). Sklep že zdaj: na
  avtocesti je avto ~2× hitrejši; zanimivo je, kdaj gneča razliko skrči.
* Vlak/avtobus ali avto za dnevne poti v Ljubljano (pozneje): FCD po
  odseku, preslikava OpenLR na cesto (~11 200 odsekov). Tu je odgovor na
  „kdaj je JP hitrejši“ verjetno pritrdilen (konica na vpadnicah).
* Kateri odhod izbrati: „LPV 2010 pride do 7:30 v 92 % dni“.
* Prestopi: kako pogosto prestop uspe na vozliščih (Zidani Most, Pragersko,
  Divača, Ljubljana). Osnova obstaja: `scripts/preizkusi_prestope.py` (22. 10.,
  17 506 dni-prestopov, delež po rezervi).

### 5. SŽ: uradni podatki proti resnici — `/statistika/sz` (zdaj)

* Odhod, ki ga ni bilo (zgoraj): s prehodi potnikov in vzorcem vseh voženj.
  Potnik je 24. 9. 2026 sam prijavil: „vlak čaka na prejšnji postaji … isto v
  uradni aplikaciji“ (MERITVE „Vlak, ki ga je ura spravila s table“).
* „Odpeljal je“ je sklep iz ure: 20. 8.–23. 9. od 123 280 trditev o odhodu
  95,8 % nepotrjenih; feed SŽ postanke naprej odšteva po uri (LPV 2206 5. 10.).
* Lažni padci zamude: zemljevid SŽ 11.–16. 10. 4 086 padcev na 0 po zamudi
  ≥ 5 min na 1 181 vožnjah, 92 % se vrne (p50 4,5 min).
* Zamuda, ki raste minuto na minuto, medtem ko je vlak na zemljevidu na poti.
* Nadomestni avtobusi brez podatka v živo (0 od 777); vozni red le v PDF.
* Tir objavljen na 14 od 20 postaj s tablo.
* Napovedi SŽ nima: uradno = trenutna zamuda, izmerjeno slabše od naše.
* Tabla zamud kaže le ≥ 3 min; zamuda na cilju se po 1–2 min ponastavi na 0.
* Vozni red, ki ne drži: odseki, kjer vlaki redno izgubijo čas (izračunati).
* Izpadi virov po dnevih (7. 10. Cloudflare, 28. 9. zip DUJPP …).
* Ton: dejstva z datumom in vzorcem, brez posmeha. Podoben razdelek za
  avtobusne vire (lažne zamude, prezgodnji odhodi, LPP in Marprom zunaj IJPP).

### 6. Še za potnika

* Pregled `/statistika`: ta mesec po omrežju, naše napovedi v enem stavku,
  lestvice, vstopi v 1–5, čas izračuna (zdaj).
* Mesečno poročilo `/statistika/2026-10`: za deljenje in iskalnike (zdaj, ko
  je mesec zaključen).
* Nadomestila: vožnje z zamudo ≥ 60 min (pravice potnikov) — štetje in
  opozorilo na strani vlaka (zdaj; cen ni).
* Točnost odhodov s postaje na pristajalni `/postaja/{ime}` (zdaj).
* Vreme kot dejavnik (pozneje, ob prvem snegu preveri vzorec).
* Zasedenost po urah (pozneje, 28 poročil).

## Odločitve (David, 29. 10. 2026)

* Konkurenca **po metodi, brez imen**; imena ostanejo na `/primerjava`.
* Stran SŽ **javna, poimenska**, samo dejstva z vzorcem in datumom.
* Vrstni red: **pregled, napovedi, prevozniki**; nato vlak/linija, SŽ,
  relacije, mesečno poročilo.
* Smer strani: **A · Odgovori** (David, 29. 10. 2026 ~16.45): kartice z
  vprašanjem potnika in eno veliko številko, pod njo trak ali stolpci, vsaka
  vodi na podstran; podstrani v istem slogu.
* Faza 1 na localhostu: David „pogledal sem in je dobro, a nadaljuj naprej in
  objaviva potem vse naenkrat“ (29. 10. ~17.40) — **objava šele na koncu, vse
  skupaj**.
* **Povratna informacija po fazah 1–5** (David, 29. 10. 2026 ~20.10):
  „Nadaljuj s fazami, če so še. Izboljšaj preglednost na desktopu (ne rabi
  biti kot pri telefonu — novinarji ponavadi gledajo iz računalnikov).
  Preglej, ali so prikazani podatki dobro razloženi. Kako se podatki
  posodabljajo? (ne statično, ne ob vsaki zahtevi). Pri relacijah iskalnik za
  čisto vsako relacijo, tudi male (presodi, ali je preveč). Stran SŽ drugače,
  bolj razumljivo: kaj je ‚zemljevid‘? kako točni so podatki potnikov z GPS?
  ročno napiši pripombe, kaj bi se dalo pri SŽ izboljšati.“ Vrstni red (moj):
  SŽ → namizje + razlage na vseh straneh → iskalnik relacij → faza 6.
* Postopek (moj): najprej nočni izračun in API (od designa neodvisno), nato
  osnutki strani s pravimi številkami, David izbere, nato predloge.
* **Iskanje relacije samo brez prestopov** (David, 29. 10. 2026 pozno:
  „Brez prestopov“). Za prestope je iskalnik povezav (`/app/train`,
  `/app/pot`); stran relacij nanj kaže, kadar neposredne vožnje ni.
* **Objava zdaj, vse skupaj** (David, 29. 10. 2026 pozno, po zaprtih
  najdbah pregleda).

## Predlogi pred odločitvijo (zgodovina)

* Konkurenca: predlagam **po metodi, brez imen** („trenutna zamuda naprej —
  tako kaže zemljevid SŽ“, „samo vozni red“); imena ostanejo na `/primerjava`
  (pravilo: o drugih samo, kar povedo sami, z datumom).
* Stran SŽ: predlagam **javno, poimensko, samo dejstva** z vzorcem in
  datumom; isti razdelek za avtobusne vire.
* Vrstni red: predlagam (1) osnova + pregled + napovedi, (2) prevozniki,
  (3) vožnja/linija, (4) SŽ, (5) relacije, (6) mesečno poročilo.
* Design: osnutki na platnu pred izvedbo (kot prenova vozil).

## Arhitektura (predlog)

* **Hramba**: `napoved` živi 30 dni (`OCENA_KEEP_DAYS`), `obs` 90 dni za
  vlake in 14 za avtobuse, `lega` 14 dni; `run` nikoli ne obreže. Kar se
  izračuna iz obrezanih tabel (senca, popravki SŽ, pokritost), gre ponoči v
  novo tabelo **`stat_dan`** (dan, vrsta, ključ, JSON), ki se ne briše —
  sicer trenda čez mesec ni. Ob prvem zagonu dopolni nazaj, kolikor sega vir.
* **Okna** (30/90 dni, mesec) iz `stat_dan` in `run` ponoči v `povzetek`
  (nove `kind`, `SUMMARY_VERSION`); po vožnji/liniji ločena tabela
  (`stat_voznja`: omrežje, ključ, JSON) za branje ene strani brez branja
  vseh.
* **Modul** `kajros/statistika.py` (stats.py ima 2 683 vrstic); strani v
  `api.py` po vzoru pristajalnih, predloge `templates/statistika*.html`.
* **Grafi** iz strežnika kot vgrajen SVG (brez JS berljivo, iskalnik), JS le
  za namig ob dotiku. Brez knjižnic.
* **Nočno delo samo, kjer je baza cela** (arwen); malina brez vlakov ne
  računa statistike vlakov (stikalo kot `KAJROS_…`).
* **Mesečno poročilo** zamrzne 1. v mesecu (`stat_mesec`), se ne preračuna.
* **API** `/api/statistika/…` (GET, odprto); stran `noindex` pod vzorcem.

## Stanje

* 29. 10. 2026: popis (dva bralca, vključeno v načrt) in meritve
  izvedljivosti na kopiji baze z arwena. Merilne skripte so v gitu v commitu
  6ae95af (`git show 6ae95af:docs/statistika-delo/skripte/sz_odhod.py`;
  še `pregled.py`, `senca.py`, `prevozniki.py`, `sz_manjka.py`,
  `vlak_avto.py`, `vlak_bus.py`, `ac.py`, `odseki.py`, `prezgodaj.py`),
  tečejo nad kopijo. Številke v `docs/MERITVE.md` (razdelki 29. 10. 2026).

* 29. 10. 2026 popoldne: **zaledje faze 1 narejeno** (commit 44a2fd4):
  `kajros/statistika.py`, tabela `stat_dan`, kinda `stat_napovedi` in
  `stat_prevozniki` v `SUMMARY_BUILDERS`, ob zagonu brez njiju nočni izračun
  takoj, API `/api/statistika/napovedi` in `/api/statistika/prevozniki`,
  `tests/test_statistika.py` (12). Na kopiji arwena: dopolnitev 69 dni 477 s,
  okna 0,1–36 s. Ni še objavljeno. Lestvica: vlakov 596, Arriva 478, Nomago
  885 voženj z ≥ 10 dnevi. Delež voženj z lego NI na strani (`lega` = le NAP).

* 29. 10. 2026 ~16.40: **osnutki na platnu** https://claude.ai/artifact/4T7UpCgyisqYxNenSvrP12
  (vir v scratchpadu `statistika-osnutki/project/`, sicer Artifact `read`):
  A Odgovori (kartice z vprašanjem in eno številko), B Poročilo (naslovna
  poved, tabela, seznami), C Lestvice (zavihki Prevozniki/Vlaki/Linije,
  uvrstitve s trakom), podstran Napovedi v slogu A. Številke prave (kopija
  arwena do 28. 10.). Čaka Davidovo izbiro.

* 29. 10. 2026 ~17.30: **strani faze 1 narejene** (commit 81a393e, ni objavljeno):
  `/statistika` (pregled A), `/statistika/napovedi`, `/statistika/prevozniki`,
  `/statistika/prevoznik/{slug}`; meni Več, zemljevid strani, `obisk._STRANI`,
  `preveri.sh` (zeleno), 1 078 testov. Posnetki `posnetki/statistika/`. Lokalno
  so povzetki uvoženi s kopije arwena (vlakov lokalna baza od 7. 10. nima).
  Čaka Davidov ogled na localhost:8001/statistika.

* 29. 10. 2026 ~18.30: **faza 3 narejena** (7b54895, b1dccb3, ed61ad5, ni
  objavljeno): `/statistika/vlak/{slug}` in `/statistika/linija/{prevoznik}/{slug}`
  iz `stat_voznja` (nočni izračun prevoznikov zdaj bere končne zamude 90 dni
  in piše lestvico + 2 295 strani; avtobusi 66 s na arwenu), profil po
  postajah iz `stats.history` v zahtevi, odhodi pri medkrajevni šifri, dnevi
  v tednu le ob razliki. Okno vožnje ima v nogi „kako točno vozi ›“
  (`statistika` v `/api/train/{no}/run`). `/app/statistika` → 301, stara
  predloga in JS izbrisana (nova `statistika.css` je povozila staro).

* 29. 10. 2026 ~19.00: **faza 4 narejena** (efe4bf5, ni objavljeno):
  `/statistika/sz` + rjava kartica na pregledu; `stat_dan` vrsta `sz` (od
  `SZ_VODI_OD` 11. 10.), okno `stat_sz` (popravki odhoda, lažno točna
  izhodišča, prehodi potnikov, odseki, nadomestni, delež napovedi SŽ).
  `stat_dan` ima različico (`STAT_DAN_VERZIJA` 2, meta `stat_dan_verzija`):
  nova vrsta = vsi dnevi znova, vrste z obrezanim virom ostanejo.

* 29. 10. 2026 ~19.30: **faza 5 narejena** (03d8077, ni objavljeno):
  `/statistika/relacije` + kartica LJ → MB na pregledu; okno `stat_relacije`
  (`RELACIJE`: šest parov, obe smeri; vlak/avtobus `_par`, avto `_avto` iz
  `promet.ac` — kjer `promet.sqlite` ni, avto izpade).

* 29. 10. 2026 ~20.00: **faze 1–5 preverjene s številkami z arwena** (d5a8b7e),
  `preveri.sh` zelen, 1 083 testov. Okno relacij prepisano (411 s → 0,2 s).
  Na kopiji arwena: dopolnitev vseh dni s SŽ 9,5 min. Lokalna baza ima
  uvožene povzetke in `stat_voznja` s kopije (za ogled na localhost:8001).
  SŽ (11.–28. 10.): 51 odhodov s potnikom, 75 % vsaj 2 min prezgodaj,
  20,4 % postankov pozneje dvignjenih za ≥ 2 min, nadomestni 0 od 1 316.

* 29. 10. 2026 ~21.00: **Davidove pripombe po fazah 1–5 narejene** (3264d4b,
  a556f0b, ni objavljeno): namizje (mreža do 1240 px, tabela prevoznikov),
  ista razlaga številk na vseh straneh (`_stat.razlaga`), na napovedih „Kako
  merimo“; stran SŽ na novo (kaj je zemljevid vlakov, GPS potnikov 3–5 s
  ~4 m, 30 s v korist SŽ — `POTNIK_ZAMIK_S`, „Kaj bi SŽ lahko izboljšal“);
  **iskanje relacije** `?od=&do=` (ob zahtevi, `_par` ~10 ms, predpomnilnik
  do konca okna, `noindex`; samo vožnje brez prestopa); faza 6 deloma:
  **prag nadomestila** (60/120 min, kartica SŽ in vrstica vlaka).
  Lokalni povzetki z arwena so bili starejši od kode: `stat_sz` in
  `stat_prevozniki` sem dopolnil na roke (samo lokalno, za ogled).
* Kako se številke osvežujejo (odgovor Davidu): vsako noč ob 3.30
  (`KAJROS_MAINT_HOUR`, nit `kajros-povzetki`) `stat_dan` za nove dni in
  zadnje 3 dni znova, nato okna v `povzetek` in strani voženj v
  `stat_voznja`; strani le berejo (6–35 ms). V zahtevi se računa samo profil
  vlaka po postajah (`stats.history`) in iskanje relacije.

* 29. 10. 2026 ~22.30: **namizje brez lukenj** (56c2904): vrste flex, enako
  visoke kartice, dolgi seznami čez vso širino v stolpcih, zavihki med
  stranmi, ploščice za dneve in odhode, stolpci avtobusov na pregledu.
  Funkcionalni pregled (en agent, sonnet): 856 naslovov 200, brez puščanja,
  številke skladne, telefon brez vodoravnega drsnika; najdbe popravljene
  (spodaj). Ustavljeno pri 96 % 5-urnega okna.

* 29. 10. 2026 pozno: **najdbe pregleda popravljene** (29bff36, 4b09437,
  102e25d, ni objavljeno): števniki prek `stevnik`; lestvica prevoznika
  največ polovica linij na seznam (Kranj 8 je dve kazal na obeh);
  prezgodnji odhodi vlakov povsod „—“ (vir pod nič ne poroča); stran
  vožnje z malo meritvami (`malo_voznje`: vlak < 10 dni, linija < 30
  voženj) z opozorilom, `noindex`, ni v zemljevidu strani — lokalno 80
  vlakov in 7 od 95 mestnih linij; stolpci po dnevih z `aria-label`;
  besedilo pri točnih vlakih, naslov iskanja relacije = par. `preveri.sh`
  zelen, 1 092 testov.

## Naslednji koraki

1. **Objava vsega skupaj** (`git push arwen claude/slovenske-zeleznice-api-ql84hf`),
   ko David reče: ob zagonu brez `stat_prevozniki` se nočni izračun sproži
   takoj (`stat_dan` vsi dnevi ~10 min, prevozniki avtobusi ~1 min). Malina
   statistike ne računa (`KAJROS_SUMMARIES`). Po objavi preveri
   kajros.app/statistika in podstrani; na arwenu pobriši
   `/var/tmp/kajros-stat.sqlite`, `promet-stat.sqlite`, `kajros-dev*`,
   `stat_*.json`, `*.py`.
2. **Po objavi preveri številke SŽ**: kopija z arwena (izračun pred
   `POTNIK_ZAMIK_S`) je dala 51 odhodov in 75 % ≥ 2 min, MERITVE pravi 61 in
   66 % (drugo okno). Z zamikom 30 s mora delež pasti; uskladi MERITVE.
3. Drobno iz pregleda, neodločeno: napovedi vlakov imajo 27 od 30 dni
   (7.–9. 10. brez zajema), stran vrzeli ne omeni; `/statistika/prevoznik/SZ`
   vrne 404 (vlak z veliko začetnico preusmeri 301); `/statistika/` vrne 307
   (FastAPI), ne 301.
4. **Relacije, Davidova vprašanja** (29. 10. 2026 pozno, neodločeno):
   kartica Ljubljana ↔ Jesenice nima avtobusa, ker ima `RELACIJE` avtobusno
   ime „Jesenice“ (železniška postaja, brez avtobusnih voženj); avtobusi
   ustavijo na „Jesenice občina“ (347 voženj v voznem redu) in „Jesenice ŽP“
   (344), iskanje najde 253 oz. 230 voženj z meritvijo (Arriva). Avto: DARS
   objavi deset relacij (LJ–MB, LJ–KP, LJ–Karavanke, LJ–MP Obrežje, oba
   kroga obvoznice; obe smeri, `promet.ac` od 14. 10.). Celje, Kranj in Novo
   mesto so sredi daljših, delnega časa DARS ne da — kartica avto izpusti
   brez besede. Parov postaj z neposredno vožnjo je za vlak 8 795 (arwen),
   za avtobus 244 232 (lokalna baza, 41 954 voženj): zato izbran seznam in
   iskanje ob zahtevi. Ptuj → Ljubljana „0 % v 5 min“ je resnično: IC 503 in
   MV 246 (po 25 voženj, najmanj +18 in +14 min), RG 1641/1643 (4 + 4),
   okno 29. 9.–28. 10. Polje → Ljubljana da samo vlak (Ljubljana Polje,
   561 voženj): „Ljubljana“ se za avtobus razreši v „Ljubljana AP“, kamor
   LPP ne pelje (s Polja linije 11, 11B, 20Z, 24, 25, 27: Bavarski dvor 973
   voženj v voznem redu, Ajdovščina 735, Konzorcij 340, Ljubljana AP 0).
   Tipkarska napaka: ime je podniz brez šumnikov in velikih črk
   (`journey.search_stations`), „Ljubljna“ ne najde ničesar. Od 29. 10.
   stran ponudi do tri podobna imena (`journey.podobna_imena`, `difflib`
   0,75, 1–5 ms na 5 798 imenih) s povezavo na popravljen par.
5. **Faza 6, ostanek**: mesečno poročilo (ko je oktober cel, od 1. 11.),
   točnost odhodov na `/postaja/{ime}`.
