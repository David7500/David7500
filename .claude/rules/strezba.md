---
paths:
  - "sztrack/api.py"
---

# Kaj sme in česa ne sme API

Pravila zajema (kaj feed sploh pove in kje laže) so v
`.claude/rules/zajem.md`; tu je samo tisto, kar velja za strežbo.

**Meja med meritvijo in napovedjo je `stats.last_measured()`.** Vsak odgovor,
ki nosi zamudo, jo mora upoštevati -- kar je za zadnjim prevoženim postankom,
je feedova napoved. Ta napaka je bila že dvakrat na zaslonu.

**Vsi potniški endpointi imajo `network` in privzeto `zeleznica`.** Filter
mora biti **znotraj** poizvedbe, ne za njo: železniško vprašanje (700 000
vrstic) sicer plača avtobusne (12 M). Bil je že dvakrat vzrok počasnosti.

**Vožnja, ki zamuja več kot `api.MAX_LIVE_DELAY_S` (6 h), ni živa.** To je
pravilo prikaza, ne pospešek: pri železnici ni nobene zamude čez tri ure,
pri avtobusih pa je nad šest ur 0,67 % vrstic in te niso zamude, ampak
feedova zamenjava prometnega dne.

* **Položaj vlaka je interpoliran, ne GPS.** `vehicle_positions` vsebuje
  avtobuse, vlakov ne. Dashboard zato riše vlake na zadnji znani postaji.
  **Avtobusi pa GPS imajo** -- z legendo, smerjo in hitrostjo (do 130 vozil
  hkrati). Na zemljevidu so zato puščica v smeri vožnje, vlak pa krog na
  postaji: enak simbol za oboje bi zabrisal razliko med izmerjeno lego in
  zadnjo znano postajo. Hrani se samo trenutna lega (`vehicle_now`, upsert):
  sled bi bila ~300 000 točk na dan, prikaz "kje je zdaj" pa rabi eno vrstico.

  **Ritem je izmerjen, ne domnevan** (86 vozil, 492 prehodov med legami):
  vozilo objavi novo lego vsakih **20 s** (404 od 492 razmikov je natanko 20 s),
  in ko se ta v feedu prvič pojavi, je že **20 s stara** (p90 30 s, najstarejša
  104 s). Glava feeda je sveža -- naš prenos je od nje oddaljen 0,5--3 s --
  torej zaostanek ni na naši strani, ampak med vozilom in virom.

  **Spodnja meja je feed in je ni mogoče obiti.** Merjeno na glavi feeda samega
  je mediana starosti lege 21 s ob 19:44 in **33 s ob 21:03** (59 vozil namesto
  86) -- z uro se slabša, ker vozila proti koncu obratovanja poročajo redkeje.
  Hitreje od tega ne more nihče, tudi brskalnik ne, če bi bral naravnost.

  **Naravnost tudi ne more.** Feed nima nobene `Access-Control-Allow-Origin`
  glave, zato CORS branje iz JS blokira; edina pot je posrednik, in ta smo mi.
  Tudi če bi šlo, bi to pomenilo protobuf knjižnico v brskalniku (odvisnost) in
  vsak obiskovalec bi tolkel po tuji javni storitvi namesto po naši.

  Kar je torej naše, je **vzorčenje**, in to je bilo prej večje od potrebnega:
  zajem na 30 s je prispeval mediano 15 s, brskalnik na 20 s še 10 s. Zdaj
  `config.POSITION_SECONDS = 10` (pol vozilovega ritma; pod tem ni česa dobiti)
  in brskalnik vpraša **v koraku s strežbo** -- odgovor nosi glavo
  `X-Osvezi-Cez` s sekundami do naslednjega branja, `common.pollVehicles()` pa
  se po njej ravna, z zamikom 0--2 s (sto brskalnikov ne sme udariti hkrati) in
  brez spraševanja, dokler je stran skrita. Izmerjeno: naš prispevek k starosti
  **15 s → 5 s**.

  **Zdaj ne dodamo praktično ničesar, in to je izmerjeno po vozilih.** V istem
  trenutku prebrana feed in naš `/api/vehicles`, 409 primerjanih vozil: lega je
  ob našem branju **že 28,8 s stara** (p90 42,1), mi pokažemo 32,0 s (p90 47,0),
  razlika pa je **mediana −0,1 s** in p90 19,3 s. Polovico časa je torej naša
  vrednost natanko tako sveža kot feedova — ker vozilo objavlja na 20 s in ima
  ista žiga; p90 je večji od 10-sekundnega cikla zato, ker vozilo med našim
  branjem in primerjavo objavi nov, do 20 s novejši žig.

  **Naš zaostanek za feedom ni „nekaj sekund", ampak dvovrednosten.** Merjeno
  na 490 primerjavah: v **66 %** imamo natanko isti žig kot feed (razlika −1 s),
  v **25 %** pa smo eno vozilovo objavo zadaj (19--20 s). Vmesnih vrednosti
  skoraj ni. Razlog je aritmetičen in se ujema do odstotka: vozilo objavlja na
  20 s, mi beremo na 10 s, torej je verjetnost, da je nova lega prispela po
  našem zadnjem branju, ≈ 5/20 = 25 % (opaženo 122 od 490). Mediana 0 s,
  povprečje 5,5 s, p90 19 s, največ 41 s.

  **Pogojni GET pri legah ne pomaga.** Feed se spreminja **vsaki 2 s** (39 od
  40 zahtev je vrnilo 200, en sam 304) — različna vozila poročajo v različnih
  fazah, zato datoteka skoraj nikoli ni ista. Pri voznem redu in obvestilih
  ETag prihrani prenos, tu ne.

  Iz tega sledi, kaj bi gostejše branje res dalo: pri 5 s bi bila verjetnost
  zaostanka ≈ 12,5 % in povprečje ~2,5 s namesto 5,5. Torej **3 sekunde od 32**,
  za dvakratno breme tuje javne storitve (63 → 127 MB/dan). Zato ostane 10 s;
  kdor hoče preizkusiti, ima `SZ_POSITION_SECONDS` in ne rabi spreminjati kode.
  Številka, ki jo potnik vidi, ni naš zaostanek — je starost meritve GPS v
  vozilu. Zato ima žeton naslov, ki to pove.
* **Okno vožnje je lego naložilo enkrat in nikoli več.** Kdor je stran pustil
  odprto, je gledal, kje je bil avtobus ob odprtju -- in prav tam je vprašanje
  „kje je zdaj" najbolj neposredno. Zdaj se osvežuje z istim
  `pollVehicles()` kot zemljevid. Pogled se **premakne le, kadar vozilo uide
  iz okvira**: brezpogojni `setView` bi zemljevid vsakih deset sekund trgal
  izpod prsta človeku, ki si ogleduje kaj drugega.

* **`/api/vehicles` je predpomnjen na cikel zajema.** Odgovor se med dvema
  branjema leg ne spremeni, zato se izračuna enkrat in vsem strežejo iste
  vrstice; ključ je `positions_fetched`, ne ura, da se razveljavi natanko ob
  novem podatku. Izjema je `age_s`, ki se računa ob vsaki strežbi -- starost
  lege je edino, kar se med cikloma res spreminja, in predpomnjena bi lagala.
  To je edini del prikaza, kjer je število uporabnikov sploh vidno: brez tega
  bi sto obiskovalcev pomenilo sto enakih poizvedb desetkrat na minuto.

* **`vehicle_now` pozna samo lego, zamude v njej ni.** `/api/vehicles` je
  vračal `v.*` in prikaz je bral `v.delay_s`, ki ni obstajal -- kartica na
  zemljevidu je zato pri vsakem avtobusu pisala „? min", njegova stran pa
  +15. Dve številki o istem vozilu, ena izmišljena. Zamudo doda
  `stats.last_measured()` -- **isto pravilo kot živi seznam in okno vožnje**,
  ne nova poizvedba: sicer se razideta spet. Preverjeno na 67 vozilih z
  meritvijo, vsa se ujemajo z vrstico v `run`. Poceni je, ker gre za ~80
  voženj z GPS in ne za vse omrežje (20 ms).
