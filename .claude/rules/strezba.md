---
paths:
  - "kajros/api.py"
  - "kajros/lpp.py"
  - "kajros/obisk.py"
---

# Kaj sme in česa ne sme API

Pravila zajema (kaj feed sploh pove in kje laže) so v
`.claude/rules/zajem.md`; tu je samo tisto, kar velja za strežbo.

**Meja med meritvijo in napovedjo je `stats.last_measured()`.** Vsak odgovor,
ki nosi zamudo, jo mora upoštevati -- kar je za zadnjim prevoženim postankom,
je feedova napoved. Ta napaka je bila že dvakrat na zaslonu.

**In izračuna se na enem mestu.** `/api/train/{no}/run` vrne
`last_measured_seq`; prikaz ga bere in ga **ne računa sam**. Do 3. 9. 2026 je
bilo isto pravilo napisano dvakrat -- v `stats.py` in v `common.lastMeasured()`
-- z lastnim ravnanjem ob ničli za še nedosežen postanek. Dve različici istega
pravila se prej ali slej razideta, razlika pa bi bila tiha: prikaz bi feedovo
napoved pokazal kot izmerjeno zamudo. Primerjano ob poenotenju na 27 živih
vožnjah: ujemali sta se povsod.

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
  kdor hoče preizkusiti, ima `KAJROS_POSITION_SECONDS` in ne rabi spreminjati kode.
  Številka, ki jo potnik vidi, ni naš zaostanek — je starost meritve GPS v
  vozilu. Zato ima žeton naslov, ki to pove.
* **Okno vožnje je lego naložilo enkrat in nikoli več.** Kdor je stran pustil
  odprto, je gledal, kje je bil avtobus ob odprtju -- in prav tam je vprašanje
  „kje je zdaj" najbolj neposredno. Zdaj se osvežuje z istim
  `pollVehicles()` kot zemljevid. Pogled se **premakne le, kadar vozilo uide
  iz okvira**: brezpogojni `setView` bi zemljevid vsakih deset sekund trgal
  izpod prsta človeku, ki si ogleduje kaj drugega.

* **Vsi dragi odgovori so predpomnjeni na značko podatka, ne na uro.**
  Značke so `rt_fetched` (zamude, 30 s), `positions_fetched` (lege, 10 s) in
  `gtfs_imported_at` (vozni red, ~1×/dan); `_predpomni()` ima še varovalko
  `najvec_s` za primer, ko zajem ne teče (`KAJROS_COLLECTOR=0`) in se značka
  nikoli ne spremeni. Ključavnica je **na ključ**, ne skupna: skupna bi drage
  odgovore serializirala med sabo, brez nje pa bi ob izteku vsi hkratni
  obiskovalci računali isto stvar.

  Izmerjeno 3. 9. 2026 (mediana 12 zahtev, topel predpomnilnik):

  | pot | prej | zdaj |
  |---|---|---|
  | `/api/live` | 253 ms | **3,8 ms** |
  | `/api/overview` | 224 ms | 2,9 ms |
  | `/api/overview/bus` | 230 ms | 2,6 ms |
  | `/api/stations` | 77 ms | 3,3 ms |
  | `/api/network.geojson` | 51 ms | 3,3 ms |
  | `/api/shapes/live` | 33 ms | 3,0 ms |

  **`/api/stations` in `/api/network.geojson` predpomnita že serializiran
  JSON**, ne seznama slovarjev: sama poizvedba je manjši del cene, večino
  poje pretvorba 9 791 postaj v niz. Samo predpomnjenje poizvedbe je dalo
  77 → 41 ms, predpomnjenje niza pa 41 → 3,3. Zato vračata `Response`, sicer
  bi FastAPI serializiral znova.

  **Kar mora ostati sveže, se doda po predpomnilniku**: `now` v pregledih in
  `age_s` pri legah. Predpomnjena bi lagala.

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


## Ogrevanje predpomnilnika: kdo dela in kdaj

`/api/live` je najdražji odgovor, ki ga zemljevid vpraša vsakih 30 s. Njegov
predpomnilnik je vezan na `rt_fetched`, ta pa se osveži ob vsakem zajemu —
torej prav tako vsakih 30 s. Skoraj vsak klic je zato padel v prazno.

Zdaj ga **zajemna nit izračuna vnaprej**, takoj po zajemu (`server._ogrej_zive`).
Dela je enako, le da ga ne opravi uporabnik med čakanjem. Izmerjeno 4. 9. 2026:
`?network=zeleznica` 245 ms hladno, **6 ms toplo**.

**Ogrevaj skozi ENDPOINT, ne skozi notranjo funkcijo.** Prva različica tega
ogrevanja je klicala `api._live()`, predpomnilnik pa napolni šele
`api_live()`, ki ga ovije v `_predpomni`. Delo je bilo opravljeno in zavrženo;
učinka ni bilo nobenega, meritev „6 ms toplo“ pa je bila navadno predpomnjenje
iz zaporednih zahtev. Po popravku: **0 od 16 klicev čez dve minuti nad
100 ms** (prej 3 od 14 pri 245 ms).

**Značka mora ustrezati temu, od česa je odgovor res odvisen.**
`/api/overview/bus` je bil vezan na `rt_fetched` **in** `positions_fetched`,
ta pa se osveži vsakih 10 s — predpomnilnik je razpadel prej, kot ga je
ogrevanje (na 30 s) lahko ujelo, in z njim `day_summary` (463 ms) ter
`_live("avtobus")` (768 ms), torej oboje, kar od leg sploh ni odvisno.
Endpoint je bil dosledno **1,3 s**. Zdaj se drago predpomni na `rt_fetched`,
števci vozil pa se berejo sveže (920 vrstic, poceni): **4–42 ms**.

Dvoje, kar se pri tem hitro zgreši:

* **Ogrevaj samo, kar strani res vprašajo.** Zemljevid in pregled kličeta
  `network=zeleznica`; `network=None` je 802 ms dela za odgovor, ki ga
  aplikacija ne uporablja — ogrevati ga pomeni zamikati koristna dva.
* **Na malini tega ne sme biti.** Zajemna zanka je ista za strežnik in za
  `kajros collect`. Pi Zero W je pri istem poslu ~100× počasnejši in bi si z
  ~1 s dela na obhod podrl ritem zajema — isti razlog, zakaj je tam ugasnjena
  `ocena`. Varovalo je `server._strezemo`, ki ga postavi samo `lifespan`.

Ogrevanje po vsakem **uspešnem** zajemu, ne le ob spremembi: značka se osveži
tudi takrat, ko feed ni prinesel ničesar novega, in kadar se ni premaknila,
je ogrevanje 19 ms in ne stane nič.


## Odhodna tabla: prvi in zadnji postanek sta statika

`_BOARD_SQL` je imel `WITH ends AS (SELECT MIN/MAX(stop_seq) FROM sched GROUP
BY trip_id)` — polni pregled **403 208** vrstic `sched` ob **vsaki** zahtevi.
Izmerjeno 4. 9. 2026: 117 ms od 120 je bilo v tej eni poizvedbi.

Vozni red se med uvozi ne spreminja, zato sta `first_seq` in `last_seq` zdaj
stolpca na `trip`, ki ju napolni `db.fill_trip_window()` — isto kot že prej
`start_s` in `end_s`. **120 ms → 7 ms** pri isti vsebini (18 vrstic).

Vožnje brez `sched` (nagrobniki po uvozu, glej `gtfs.py`) imajo `first_seq`
NULL in na tablo ne pridejo. To je pravilno: vožnja brez voznega reda nima
odhoda, ki bi ga bilo mogoče napovedati.

## `zamuda`: strežnik pove, kaj stvar JE

Vsak odgovor, ki nosi zamudo, nosi zraven tudi **odločitev** o njej, da je
odjemalcu ni treba izpeljati. Zgrajena je v `stats.opis_zamude()`:

```json
"zamuda": {"s": 320, "min": 5, "razred": "1-5",
           "vrsta": "izmerjeno", "prezgodaj": false, "pravocasna": true}
```

Je na `/api/departures` (`board`), `/api/connections` (`connections`),
`/api/train/{no}/run` (`stops`) in `/api/live`. `null` je, kadar zamude ni.

**Meja je namenoma tu: strežnik pove, kaj stvar JE, odjemalec, kako je
VIDETI.** Barve v objektu zato ni — ta je oblikovanje in sme biti na telefonu
drugačna. Razred, minuta in vrsta pa so pravilo.

Trije razlogi, zakaj to ni okras:

* **`min` se ne sme računati na odjemalcu.** Zaokroženo je z `floor(x + 0,5)`.
  JS `Math.round` dela isto in Javin `Math.round` tudi, `kotlin.math.round`
  pa **ne** — drugi odjemalec bi se razšel pri natanko 30 s.
* **`razred` gre po zaokroženi minuti, ne po sekundah.** Ta napaka je v tem
  projektu že bila: 3 280 voženj (7,29 %) je padlo v režo 30–60 s, kjer je
  strežnik rekel „točno“ (sivo), barvna lestvica pa „1–5 min“ (oranžno).
  Ključ je strojni (`tocno`, `1-5`, `5-15`, `nad-15`); prikazna imena
  („1–5 min“) ostanejo v `povzetek` in v odjemalcu.
* **`vrsta` je meja med meritvijo in napovedjo.** Pri `/api/train/{no}/run` jo
  dopiše endpoint, ker mejo (`last_measured_seq`) pozna šele on. Prav ta
  razlika je bila po zapisu v CLAUDE.md že dvakrat na zaslonu narobe.

Odjemalec, ki bere `delay_s` in sklepa sam, je zato **star način**. V
`common.js` funkcije `delayLabel()`, `delayColor()`, `delayText()` in
`isEarly()` sprejmejo oboje — objekt ali gole sekunde — a sekunde so rezerva
za mesta, ki objekta še nimajo. **Nov odjemalec naj bere samo objekt.**

## Živi prihodi mestnega LPP (`lpp.py`)

Drug vir za **isti** promet: `data.lpp.si` se spremeni na 10–30 s, derp.si na
~90 s. Uporablja se **samo za prikaz** in samo za postanke **za mejo meritve**
— v bazo ne gre nič, sicer bi `backtest` in `ocena` merila dve merili hkrati
in tega ne vedela.

Štiri stvari, brez katerih ta spoj tiho laže; vse so izmerjene:

* **Njihov `trip_id` je vzorec proge, ne vožnja.** 19 163 naših voženj LPP ima
  85 različnih tretjih komponent id-ja, najpogostejša 993-krat. `arrivals-on-route`
  zato vrne prihode **vseh** vozil na tem vzorcu.
* **Pravo vozilo izbere `vehicle_id`.** Isti prostor id-jev v obeh virih.
* **Lega mora biti sveža** (`collector.POSITION_FRESH_S`). `vehicle_now` hrani
  vrstico do ure po koncu vožnje in stara vrstica bi vezala vozilo na končano
  vožnjo — takrat eta pripada naslednjemu obhodu vzorca. Ujeto pri preizkusu:
  meja postanek 37, eta za postanek 1.
* **Postanki se spajajo po koordinati, ne po vrstnem redu.** Postajališča so
  ista do 0,0 m (704 od 714 pod 5 m), vzorec pa je lahko daljši od vožnje.

Ob 22:15 je bilo od 25 svežih mestnih vozil **19 takih z uporabno napovedjo
naprej**, meje pa so se ujemale (meja 9 → eta 10–27, meja 16 → eta 17–21) —
to je najmočnejši dokaz, da je spoj pravi: dva vira neodvisno povesta isto
lego vozila.

Izklop: `KAJROS_LPP_ZIVO=0`.

## Štetje obiska in pregled za skrbnika (`obisk.py`, `/admin`)

Prvo pravilo projekta je „meri, ne domnevaj", o sebi pa projekt ni meril nič:
strežnik ni beležil zahtev in Cloudflare svojega dnevnika ne da. Zato
`obisk.py`. Štiri stvari, ki se pri tem hitro pokvarijo tiho:

* **IP se ne shrani nikoli.** Obiskovalec je `blake2s(sol dneva ‖ IP ‖ UA)`,
  sol pa so naključni bajti, ki se ob prehodu dneva zavržejo. Posledica, ki
  jo je treba **pisati na zaslon in ne samo v kodo**: mesečnih različnih ljudi
  ni mogoče izračunati, vsota nad 30 dnevi isto osebo šteje do 30-krat. Stran
  to pove v nogi; brez tega je številka videti kot unikati in ni.
* **Pot se normalizira na obliko iz usmerjevalnika** (`/app/train/{train_no}`),
  ne na naslov. Sicer tabela raste s prometom in ne s številom strani — LPP
  linija 3G ima 388 voženj. Vzorci se berejo iz `app.routes` in ne iz seznama
  v kodi: seznam bi se ob novi strani tiho razšel. Kar ni nobena naša pot, gre
  v eno samo vrstico `(neznano)` — en bot, ki ugiba `/wp-admin/…`, bi sicer
  naredil tisoče vrstic na dan.
* **Boti so izločeni iz razrezov, ne iz prometa.** Ura dneva, naprava in
  država štejejo samo ljudi; `obisk_pot` šteje oboje, ločeno po stolpcih
  `zahtev` in `ljudi`. Iskalnik, ki vsako uro pobere isto stran, bi sicer
  narisal enakomeren dan in ubil edino zanimivo črto.
* **Pisanje ne gre v zahtevo**, ampak v svojo nit vsakih 60 s
  (`server._obisk_worker`). En obisk strani je 10–30 zahtev; vrstica na zahtevo
  bi pomenila stalno pisanje v bazo, v katero teče zajem. Cena štetja je
  izmerjena: **0,11 ms na zahtevo** (p99 0,30 ms), podrobnosti v
  `docs/MERITVE.md`.

**Odzivni čas se hrani po vedrih in mediana je razred, ne vrednost.** Prikaz
piše `‹ 250 ms` in ne `180 ms`: hranimo porazdelitev (`obisk_odziv`), ne
vsakega časa. Izmišljena natančnost bi bila tu posebej zahrbtna, ker je ta
stran edino mesto, kjer se počasnost sploh vidi.

**`/admin` je zaprt z žetonom iz okolja in brez privzete vrednosti.** Če
`KAJROS_ADMIN_TOKEN` ni nastavljen, poti ni (404). Manjkajoč žeton v zahtevi
je prav tako 404 — kdor ga nima, naj ne izve, da pot obstaja — **napačen pa
je 403**, da se tipkarska napaka loči od pozabljene nastavitve. Primerjava gre
skozi `hmac.compare_digest`. Po prijavi z `?k=` sledi preusmeritev na čist
naslov: žeton bi sicer ostal v zgodovini brskalnika in v glavi `Referer`.
Piškotek ima pot `/admin`, zato ne potuje z `/api/*` klici, ki jih brskalnik
pošilja desetkrat na minuto. Poti ni v OpenAPI — `/docs` je razglas, kaj
obstaja.

**Pregled in števci se ne štejeta sama.** `/admin*` in `/static/*` gresta mimo
štetja; sicer bi skrbnikovo osveževanje na minuto postalo največja postavka v
lastni statistiki.


## Kar stran dolguje javnosti, ne aplikaciji

Od 12. 9. 2026 je `kajros.app` odprt komurkoli. Te poti niso za aplikacijo,
ampak za brskalnike, iskalnike in ljudi, ki povezavo pošljejo naprej.

**Napaka je stran, kadar jo bere človek, in JSON, kadar jo bere stroj.**
`_napaka_html()` se odloči po poti, ne po glavi `Accept`: pod `/api/` in
`/static/` je odjemalec stroj tudi takrat, ko pošlje `*/*` — tuji odjemalci
se ob naši napaki sicer zlomijo drugače, kot pričakujejo. Podrobnost iz
kode („vlak 999999 ne obstaja“) pride na zaslon, Starlettov angleški
privzetek (`Not Found`) pa ne.

**Absolutni naslov je `config.BASE_URL`, nikoli `request.url`.** Za
Cloudflarovim tunelom je zahteva videti kot `http://127.0.0.1:8000`, ker
izvor govori navaden HTTP in enota ne teče z `--proxy-headers`. Zemljevid
strani in značke za predogled bi torej kazali na naslov, ki iz interneta ni
dosegljiv. (Naslov obiskovalca to ne prizadene — `obisk.py` bere
`cf-connecting-ip`, ne `request.client`.)

**Naš `robots.txt` mora obstajati, sicer Cloudflare postreže svojega.**
Njegov privzetek o naših poteh ne ve ničesar in pusti indeksirati `/api/`.
Naš prepove `/api/`, `/admin`, `/docs` in `/redoc`.

**`/favicon.ico` je pot, ne datoteka.** Brskalniki jo prosijo ne glede na
`<link rel=icon>` — zaznamek, zavihek in „pogosto obiskano“ gredo pogosto po
njej. Streže se PNG; ime poti je zgodovina, brskalnik gleda `Content-Type`.

**Naslov in opis strani sta zapisana enkrat** (`templates/_meta.html`), ne
posebej za `<title>` in posebej za `og:`. Dve različici istega stavka se
razideta ob prvem popravku.

**`/zasebnost` ni obrazec, ampak edino, česar obiskovalec o nas ne more
preveriti sam.** Vsebina mora ostati skladna z `obisk.py`; kdor spremeni,
kaj se šteje, spremeni tudi to stran. Naslov za vprašanja je `KAJROS_STIK`
in **privzeto prazen** — objava naslova je odločitev lastnika strani, ne
privzetek nastavitve.

**Tujih izvorov v strani ni več.** Pisave (`static/pisave/`) in Leaflet
(`static/leaflet/`) so gostovani pri nas. Prej je šel naslov IP vsakega
obiskovalca ob vsakem odprtju Googlu, zemljevid pa je visel na `unpkg.com`.
Kar ostane tuje, so **ploščice zemljevida** (OpenStreetMap, Esri) in to je
neizogibno; na strani o zasebnosti je zato našteto.


## Obrazec za stik: edina pot, ki piše iz zahteve

Do 12. 9. 2026 je bil `api.py` samo `GET` in to je bilo zapisano kot razlog,
zakaj je javna izpostavitev varna. Zdaj sta pisalni poti dve — `POST /stik`
in `POST /admin/sporocila/{id}` — in nobene tretje ne sme biti mimogrede:
`test_pisalne_poti_so_nastete` pade, če se seznam podaljša.

**Vsa varovalka je v `kajros/stik.py`, ne razsuta po `api.py`.** Namen je, da
se v enem branju vidi, kaj neznanec sme. Pet plasti, po vrsti:

| plast | kaj ustavi |
|---|---|
| podpisan žeton (HMAC, čas izdaje) | pošiljanje mimo naše strani, ponovno rabo obrazca |
| časovna past (`NAJHITREJE_S` = 4 s) | robota, ki izpolni in pošlje takoj |
| vaba (skrito polje `naslov`) | robota, ki izpolni vsa polja |
| `NA_URO` = 3, `NA_DAN` = 5 | enega vztrajnega pošiljatelja |
| `VSEH_NA_DAN` = 50 | porazdeljeno kampanjo |

Zadnja je tista, ki šteje: prve štiri ustavijo preprost robot, peta omeji
škodo, kadar jih kdo prebije. Brez nje bi bila posledica polna **baza
meritev**, torej edino, česar ni mogoče ponoviti za nazaj.

**Vrstni red preverb ni poljuben: najprej poceni, šele nato poizvedba.**
Robot, ki tolče po obrazcu, tako ne povzroči poizvedbe na vsak poskus.

**Ujeta vaba vrne videz uspeha, ne napake.** Robot, ki izve, da je ujet, se
nauči, česa ne sme izpolniti. Iz istega razloga prehitro poslan obrazec ne
pove „bilo je prehitro“ — to bi povedalo, koliko naj počaka.

**Naslova IP ne shranimo niti tu.** Omejevanje teče v pomnilniku nad
zgoščeno vrednostjo in po restartu izgine. To je zavestna menjava: raje
kdo po restartu pošlje nekaj sporočil več, kot da bi zaradi neželene pošte
začeli voditi dnevnik naslovov. `test_naslov_ip_ni_v_shemi` to straži —
kdor bo kdaj dodal stolpec „samo za odkrivanje spama“, naj tam pade.

**Telo se razbere s `parse_qs`, ne z `request.form()`.** Slednji potegne
`python-multipart`, kar bi bila šesta vrstica v `requirements.txt` za tri
vrstice dela. Obrazec je zato `application/x-www-form-urlencoded`.

**Po uspehu gre preusmeritev (303), ne izris.** Brez nje osvežitev strani
pošlje sporočilo še enkrat in v nabiralniku sta dva enaka. Ob napaki pa se
stran izriše **z vpisanim besedilom**: kdor je napisal odstavek in dobil
nazaj „e-naslov ni videti pravi“, ga ne sme izgubiti.

**Besedilo je vnos neznanca in gre skozi `escapeHtml`.** Prelome vrstic
ohrani CSS (`white-space: pre-wrap`), ne pretvorba v `<br>` — ta bi bila
druga pot, po kateri bi lahko kaj ušlo. Preverjeno z vnosom
`<img src=x onerror=…><script>…`: v DOM ni živega elementa.

**Stran o zasebnosti mora ostati skladna.** Tu se prvič shrani nekaj, kar je
človek napisal sam (e-naslov in besedilo); kdor spremeni, kaj se hrani,
spremeni tudi `/zasebnost`. Obrazec se da ugasniti s `KAJROS_STIK_OBRAZEC=0`
in takrat poti ni (404), odsek na strani o zasebnosti pa odpade.
