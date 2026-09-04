# Prošnja za dopolnitev podatkov (osnutek)

Za NAP / IJPP (Ministrstvo za infrastrukturo) in SŽ. DERP samo pretvarja, kar
dobi — manjkajoča polja izvirajo pri viru, zato pisati njim nima smisla.

Pismo je namenoma kratko in brez tehničnih izrazov: prvi bralec je najbrž
nekdo, ki podatkov ne dela sam, ampak jih preda naprej. Tehnične podrobnosti
so zato **v prilogi**, ki jo lahko posreduje svojim ljudem.

Številke so izmerjene na zajetem feedu **2. 9. 2026**. Če pošlješ čez čas,
jih preveri znova.

---

## Pismo

**Zadeva: Predlog dopolnitve odprtih podatkov o javnem prevozu**

Spoštovani,

vaše odprte podatke o voznih redih in zamudah uporabljamo za aplikacijo, ki
potniku pove, kdaj mu pelje in koliko zamuja. Podatki so dobri in redno
osveženi — hvala za to.

Ob vsakodnevni rabi sta se pokazali dve stvari, ki manjkata, in obe potnika
zadeneta neposredno.

**Prva je peron oziroma tir.** V podatkih ni zapisano, na kateri tir vlak
pripelje. Ko potnik ve, da vlak pride ob 15:42 in zamuja osem minut, je
naslednje vprašanje vedno isto: *kje ga čakam?* Na večjih postajah je to
razlika med ujetim in zamujenim vlakom. Podatek na postajah obstaja — na
zaslonih in po napovedih — v odprtih podatkih pa ne.

**Druga so odpovedi.** Kadar vlak odpade, je to zapisano samo kot prosto
besedilo v obvestilu („Vlak vozi samo do postaje …“). Računalnik takega
zapisa ne more zanesljivo prebrati, zato aplikacija odpovedanega vlaka ne
zna ločiti od takega, ki samo zamuja. Za potnika je to največja razlika, ki
obstaja: zamuda pomeni čakanje, odpoved pomeni drugo pot. Standard, po
katerem so vaši podatki objavljeni, za odpovedi ima predvideno polje — le
izpolnjeno ni.

Zanima nas, ali je oboje mogoče dodati. Če teh podatkov v izvornih sistemih
ni, nam je koristno vedeti tudi to — potem vsaj vemo, da jih ni smiselno
čakati.

V prilogi je še nekaj manjših stvari, ki bi jih bilo koristno dopolniti;
napisane so tehnično, za tiste, ki podatke pripravljajo.

Hvala za odgovor in za to, da so podatki sploh odprti.

Lep pozdrav,
**Odprti vozni red** — prostovoljni projekt za prikaz zamud javnega prevoza
[kontaktni e-naslov]

---

## Priloga (tehnično)

Izmerjeno na `ijpp_gtfs.zip` in `rt.gtfs.derp.si`, 2. 9. 2026.

| kaj | stanje |
|---|---|
| `stops.txt` ima le `stop_id`, `stop_name`, `stop_lat`, `stop_lon` | ni `platform_code` ne hierarhije `parent_station` / `location_type` |
| `schedule_relationship` v GTFS-RT | `SCHEDULED` v 100 % od 5 135 postankov (319 voženj) |
| `vehicle_positions` | 265 vozil, vsa avtobusna — vlakov ni |
| `direction_id` | ni ga; 0 od 319 voženj v realnem času |
| `shape_dist_traveled` v `stop_times.txt` | ni ga; razdalje računamo s projekcijo, odstopanje ~2–4 % |
| `route_long_name` | prazen pri vseh 2 571 progah |
| `transfers.txt` | datoteke ni — časi prestopov so ocenjeni |
| `bikes_allowed` | `0` pri vseh 20 736 vožnjah; `wheelchair_accessible` in `wheelchair_boarding` ju ni |
| `occupancy_status`, `congestion_level` | neizpolnjena pri vseh 265 vozilih |

Če je peronski podatek na voljo, bi bil uporaben v obeh oblikah: kot
`platform_code` v voznem redu in kot peronski `stop_id` v
`stop_time_update` za spremembe v realnem času.

---

## Poslano

**2. 9. 2026** na **mzi.ncup@gov.si** (Nacionalni center za upravljanje
prometa, Ministrstvo za infrastrukturo in energijo — naslov je z uradne strani
nap.si). Sledi se mu kot niti #5 v `~/Dokumenti/Razno/mailbot`; odgovor pobere
`posta.py preveri`.

Poslano je bilo **samo NAP-u**. SŽ ne: `potniski.sz.si` in `sz.si` sta za
Cloudflarom in naslova ni bilo mogoče preveriti pri viru, iskalnik pa ga je
vrnil prikritega. Namesto ugibanja pismo NAP vpraša, **na koga pri SŽ naj se
obrnemo** — če odgovorijo, gre drugo pismo na pravega človeka in ne na splošni
naslov.

## Odgovor NAP-a (3. 9. 2026)

Odgovoril je **Matej Vovk, vodja NCUP**, naslednje jutro. Vljudno, a vsebinsko
brez odgovora na obe vprašanji:

* „GTFS-RT podatki na NAP zaenkrat še niso na voljo. Na DUJPP in SŽ so v teku
  aktivnosti, ki bodo omogočile dostop tudi do teh podatkov.“
* **„Podatke, ki jih ustvarja DERP, ne moremo komentirat.“** — torej prav za
  feed, ki ga uporabljamo, ni sogovornika.
* „Ostale komentarje posredujemo DUJPP, ki je lastnik obstoječih podatkov
  GTFS.“

**Na vprašanje, na koga pri SŽ naj se obrnemo, ni odgovoril.** Dvoje pa je
odgovor: lastnik GTFS je **DUJPP**, in uradni RT nastaja (torej DERP-ov feed
ni večen).

## Naslova, preverjena pri viru (3. 9. 2026)

Oba sta iz poslovnega registra (bizi.si), ne iz ugibanja po vzorcu
`ime.priimek@`:

| kdo | e-naslov | naslov |
|---|---|---|
| DUJPP d.o.o. | `gp@dujpp.si` | Reška cesta 2, 6230 Postojna |
| SŽ-Potniški promet d.o.o. | `potnik.info@slo-zeleznice.si` | Kolodvorska 11, 1000 Ljubljana |

Dujppova lastna stran ima **samo obrazec in telefon** (080 45 77), e-naslova
ne objavlja; `gp@` je glavna pisarna. `sz.si` je še vedno 403 (Cloudflare),
zato je tudi ta naslov iz registra.

**Slabost, ki jo je treba vedeti:** `potnik.info@` je naslov za **potniška**
vprašanja, ne za podatke. Vprašanje o `platform_code` tam najbrž ne pristane
na pravi mizi. Boljšega preverljivega ni — in ugibati `gp@slo-zeleznice.si`
je natanko to, čemur se je prvo pismo izognilo. Zato naj pismo SŽ **v prvem
odstavku prosi za preusmeritev**, ne šele na koncu.

## Zapiski k pošiljanju (ne pošiljaj tega dela)

* **„Odprti vozni red“ je vstavljeno ime — zamenjaj ga ali preveri.** Preden
  pošlješ, poguglaj, da se ne ujame z obstoječim društvom ali storitvijo.
  In naj ostane pri „prostovoljni projekt“: ne pišite se za društvo, zvezo ali
  organizacijo, ki ne obstaja, in ne trdite, koliko uporabnikov imate. Če
  bo kdaj prišlo na dan, boste izgubili prav to, kar vam meritve dajejo.
* **Anonimno je šibkejše.** Prošnja od nekoga, ki podatke dejansko uporablja,
  je težja od anonimne. Kontaktni e-naslov je nujen — brez njega ne morejo
  odgovoriti, tudi če bi hoteli.
* **Naslovnika sta dva.** NAP je podatkovna točka, peronski podatek pa izvira
  pri SŽ. Vprašaj oba in to v pismu povej.
* Če odgovorijo „podatka ni“, je to **odgovor**: gre v `CLAUDE.md` med stvari,
  ki jih ne bo, enako kot cene in zasedenost.
