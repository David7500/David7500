---
paths:
  - "kajros/api.py"
  - "kajros/lpp.py"
  - "kajros/obisk.py"
---
# Kaj sme in česa ne sme API

Pravila zajema (kaj feed pove in kje laže): `.claude/rules/zajem.md`; tu samo strežba.

**Meja med meritvijo in napovedjo = `stats.last_measured()`.** Vsak odgovor z zamudo jo mora upoštevati — kar je za zadnjim prevoženim postankom, je feedova napoved. Napaka že dvakrat na zaslonu.

**Meja ne gre čez postajo iz svežega poročila SŽ** (od 6. 10. 2026): poročilo „ob prihodu na postajo Y“, mlajše od 8 min (`stats.SVEZE_POROCILO_S`), pomeni, da vlak na Y še ni bil. Napaka „vlak je tu že bil“ 13,1 → 2,7 % ob enaki točnosti, „še ni bil“ 1,2 → 11,8 % (cenejša). Isto pravilo v `_LAST_MEASURED_SQL` in `api._LIVE_SQL`; meritev v MERITVE („Kam torej narisati vlak“).

**Izračuna se na enem mestu.** `/api/train/{no}/run` vrne `last_measured_seq`; prikaz ga bere, **ne računa sam**. Do 3. 9. 2026 pravilo napisano dvakrat — `stats.py` in `common.lastMeasured()` — z lastnim ravnanjem ob ničli za še nedosežen postanek. Dve različici se prej ali slej razideta, tiho: prikaz bi feedovo napoved pokazal kot izmerjeno zamudo. Primerjava ob poenotenju na 27 živih vožnjah: ujemali sta se povsod.

**Vsi potniški endpointi imajo `network`, privzeto `zeleznica`.** Filter **znotraj** poizvedbe, ne za njo: sicer železniško vprašanje (700 000 vrstic) plača avtobusne (12 M). Že dvakrat vzrok počasnosti.

**Vožnja z zamudo čez `api.MAX_LIVE_DELAY_S` (6 h) ni živa.** Pravilo prikaza, ne pospešek: pri železnici ni zamude čez tri ure, pri avtobusih je nad šest ur 0,67 % vrstic — niso zamude, ampak feedova zamenjava prometnega dne.

* **Položaj vlaka = interpoliran, ne GPS.** `vehicle_positions` vsebuje avtobuse, vlakov ne. Dashboard riše vlake na zadnji znani postaji. **Avtobusi GPS imajo** — z legendo, smerjo in hitrostjo (do 130 vozil hkrati). Zemljevid: avtobus = oblika vozila v smeri vožnje, vlak = ploščica na postaji; enak simbol bi zabrisal razliko med izmerjeno lego in zadnjo znano postajo. Hrani se samo trenutna lega (`vehicle_now`, upsert): sled ~300 000 točk/dan, "kje je zdaj" rabi eno vrstico.

  **Ritem izmerjen, ne domnevan** (86 vozil, 492 prehodov med legami): vozilo objavi novo lego vsakih **20 s** (404 od 492 razmikov natanko 20 s); ko se pojavi v feedu, je že **20 s stara** (p90 30 s, najstarejša 104 s). Glava feeda sveža — naš prenos oddaljen 0,5--3 s — zaostanek ni na naši strani, ampak med vozilom in virom.

  **Spodnja meja = feed, ni je mogoče obiti.** Merjeno na glavi feeda: mediana starosti lege 21 s ob 19:44, **33 s ob 21:03** (59 vozil namesto 86) — z uro se slabša, ker vozila proti koncu obratovanja poročajo redkeje. Hitreje ne more nihče, tudi brskalnik ne, če bi bral naravnost.

  **Naravnost tudi ne more.** Feed nima `Access-Control-Allow-Origin` glave, CORS blokira branje iz JS; edina pot = posrednik, to smo mi. Tudi če bi šlo: protobuf knjižnica v brskalniku (odvisnost) in vsak obiskovalec bi tolkel po tuji javni storitvi namesto naši.

  Naše je **vzorčenje**, prej večje od potrebnega: zajem na 30 s prispeval mediano 15 s, brskalnik na 20 s še 10 s. Zdaj `config.POSITION_SECONDS = 10` (pol vozilovega ritma; pod tem ni česa dobiti), brskalnik vpraša **v koraku s strežbo** — odgovor nosi glavo `X-Osvezi-Cez` s sekundami do naslednjega branja, `common.pollVehicles()` se ravna po njej, z zamikom 0--2 s (sto brskalnikov ne sme udariti hkrati) in brez spraševanja, dokler je stran skrita. Izmerjeno: naš prispevek k starosti **15 s → 5 s**.

  **Zdaj ne dodamo praktično ničesar, izmerjeno po vozilih.** Ob istem trenutku prebrana feed in naš `/api/vehicles`, 409 primerjanih vozil: lega ob našem branju **že 28,8 s stara** (p90 42,1), mi pokažemo 32,0 s (p90 47,0), razlika **mediana −0,1 s**, p90 19,3 s. Polovico časa je naša vrednost natanko tako sveža kot feedova — vozilo objavlja na 20 s in ima ista žiga; p90 večji od 10-sekundnega cikla, ker vozilo med našim branjem in primerjavo objavi nov, do 20 s novejši žig.

  **Naš zaostanek za feedom ni „nekaj sekund", ampak dvovrednosten.** Na 490 primerjavah: v **66 %** isti žig kot feed (razlika −1 s), v **25 %** eno vozilovo objavo zadaj (19--20 s). Vmesnih vrednosti skoraj ni. Razlog aritmetičen, ujema se do odstotka: vozilo objavlja na 20 s, mi beremo na 10 s → verjetnost, da je nova lega prispela po našem zadnjem branju, ≈ 5/20 = 25 % (opaženo 122 od 490). Mediana 0 s, povprečje 5,5 s, p90 19 s, največ 41 s.

  **Pogojni GET pri legah ne pomaga.** Feed se spreminja **vsaki 2 s** (39 od 40 zahtev 200, ena 304) — različna vozila poročajo v različnih fazah, datoteka skoraj nikoli ista. Pri voznem redu in obvestilih ETag prihrani prenos, tu ne.

  Kaj bi gostejše branje dalo: pri 5 s verjetnost zaostanka ≈ 12,5 %, povprečje ~2,5 s namesto 5,5. Torej **3 s od 32**, za dvakratno breme tuje javne storitve (63 → 127 MB/dan). Zato ostane 10 s; kdor hoče preizkusiti, ima `KAJROS_POSITION_SECONDS`, kode ni treba spreminjati. Številka, ki jo potnik vidi, ni naš zaostanek — je starost meritve GPS v vozilu. Zato ima žeton naslov, ki to pove.
* **Okno vožnje je lego naložilo enkrat in nikoli več.** Kdor je pustil stran odprto, je gledal, kje je bil avtobus ob odprtju — tam je vprašanje „kje je zdaj" najbolj neposredno. Zdaj se osvežuje z istim `pollVehicles()` kot zemljevid. Pogled se **premakne le, kadar vozilo uide iz okvira**: brezpogojni `setView` bi zemljevid vsakih deset sekund trgal izpod prsta človeku, ki si ogleduje kaj drugega.

* **Vsi dragi odgovori predpomnjeni na značko podatka, ne na uro.** Značke: `rt_fetched` (zamude, 30 s), `positions_fetched` (lege, 10 s), `gtfs_imported_at` (vozni red, ~1×/dan); `_predpomni()` ima še varovalko `najvec_s` za primer, ko zajem ne teče (`KAJROS_COLLECTOR=0`) in se značka nikoli ne spremeni. Ključavnica **na ključ**, ne skupna: skupna bi drage odgovore serializirala med sabo, brez nje bi ob izteku vsi hkratni obiskovalci računali isto.

  Izmerjeno 3. 9. 2026 (mediana 12 zahtev, topel predpomnilnik):

  | pot | prej | zdaj |
  |---|---|---|
  | `/api/live` | 253 ms | **3,8 ms** |
  | `/api/stations` | 77 ms | 3,3 ms |
  | `/api/network.geojson` | 51 ms | 3,3 ms |
  | `/api/shapes/live` | 33 ms | 3,0 ms |

  **`/api/stations` in `/api/network.geojson` predpomnita že serializiran JSON**, ne seznama slovarjev: poizvedba je manjši del cene, večino poje pretvorba 9 791 postaj v niz. Predpomnjenje poizvedbe: 77 → 41 ms, predpomnjenje niza: 41 → 3,3. Zato vračata `Response`, sicer bi FastAPI serializiral znova.

  **Kar mora ostati sveže, se doda po predpomnilniku**: `age_s` pri legah. Predpomnjena bi lagala.

* **`/api/vehicles` predpomnjen na cikel zajema.** Odgovor se med dvema branjema leg ne spremeni → izračun enkrat, vsem iste vrstice; ključ `positions_fetched`, ne ura, da se razveljavi natanko ob novem podatku. Izjema `age_s`: računa se ob vsaki strežbi — starost lege je edino, kar se med cikloma res spreminja, predpomnjena bi lagala. Edini del prikaza, kjer je število uporabnikov vidno: brez tega sto obiskovalcev = sto enakih poizvedb desetkrat na minuto.

* **`vehicle_now` pozna samo lego, zamude v njej ni.** `/api/vehicles` je vračal `v.*`, prikaz je bral neobstoječi `v.delay_s` — kartica na zemljevidu je pri vsakem avtobusu pisala „? min", njegova stran +15. Dve številki o istem vozilu, ena izmišljena. Zamudo doda `stats.last_measured()` — **isto pravilo kot živi seznam in okno vožnje**, ne nova poizvedba: sicer se razideta spet. Preverjeno na 67 vozilih z meritvijo, vsa se ujemajo z vrstico v `run`. Poceni: ~80 voženj z GPS, ne vse omrežje (20 ms).

## Ogrevanje predpomnilnika: kdo dela in kdaj

`/api/live` = najdražji odgovor, ki ga zemljevid vpraša vsakih 30 s. Predpomnilnik vezan na `rt_fetched`, ta se osveži ob vsakem zajemu (tudi 30 s) → skoraj vsak klic padel v prazno.

Zdaj ga **zajemna nit izračuna vnaprej**, takoj po zajemu (`server._ogrej_zive`). Delo enako, le da ga ne opravi uporabnik med čakanjem. Izmerjeno 4. 9. 2026: `?network=zeleznica` 245 ms hladno, **6 ms toplo**.

**Ogrevaj skozi ENDPOINT, ne skozi notranjo funkcijo.** Prva različica je klicala `api._live()`, predpomnilnik pa napolni šele `api_live()`, ki ga ovije v `_predpomni`. Delo opravljeno in zavrženo; učinka nobenega, meritev „6 ms toplo“ = navadno predpomnjenje iz zaporednih zahtev. Po popravku: **0 od 16 klicev čez dve minuti nad 100 ms** (prej 3 od 14 pri 245 ms).

**Značka mora ustrezati temu, od česar je odgovor res odvisen.** Primer (endpoint odstranjen 29. 9. 2026, pravilo ostane): `/api/overview/bus` vezan na `rt_fetched` **in** `positions_fetched` (osveži se vsakih 10 s) → predpomnilnik razpadel prej, kot ga je ogrevanje (na 30 s) ujelo; z njim `day_summary` (463 ms) in `_live("avtobus")` (768 ms), oboje od leg neodvisno. Endpoint dosledno **1,3 s**. Zdaj se drago predpomni na `rt_fetched`, števci vozil se berejo sveže (920 vrstic, poceni): **4–42 ms**.

Dvoje, kar se hitro zgreši:

* **Ogrevaj samo, kar strani res vprašajo.** Zemljevid kliče `network=zeleznica`; `network=None` = 802 ms dela za odgovor, ki ga aplikacija ne uporablja — ogrevanje zamika koristna dva.
* **Na malini tega ne sme biti.** Zajemna zanka ista za strežnik in `kajros collect`. Pi Zero W pri istem poslu ~100× počasnejši; ~1 s dela na obhod bi podrlo ritem zajema — isti razlog, zakaj je tam ugasnjena `ocena`. Varovalo `server._strezemo`, ki ga postavi samo `lifespan`.

Ogrevanje po vsakem **uspešnem** zajemu, ne le ob spremembi: značka se osveži tudi, ko feed ni prinesel nič novega; kadar se ni premaknila, ogrevanje 19 ms, nič ne stane.


## Odhodna tabla: prvi in zadnji postanek sta statika

`_BOARD_SQL` je imel `WITH ends AS (SELECT MIN/MAX(stop_seq) FROM sched GROUP BY trip_id)` — polni pregled **403 208** vrstic `sched` ob **vsaki** zahtevi. Izmerjeno 4. 9. 2026: 117 ms od 120 v tej poizvedbi.

Vozni red se med uvozi ne spreminja → `first_seq` in `last_seq` zdaj stolpca na `trip`, napolni ju `db.fill_trip_window()` — kot prej `start_s` in `end_s`. **120 ms → 7 ms** pri isti vsebini (18 vrstic).

Vožnje brez `sched` (nagrobniki po uvozu, glej `gtfs.py`) imajo `first_seq` NULL, na tablo ne pridejo. Pravilno: vožnja brez voznega reda nima odhoda, ki bi ga bilo mogoče napovedati.

## `zamuda`: strežnik pove, kaj stvar JE

Vsak odgovor z zamudo nosi tudi **odločitev** o njej, odjemalcu je ni treba izpeljati. Zgrajena v `stats.opis_zamude()`:

```json
"zamuda": {"s": 320, "min": 5, "razred": "1-5",
           "vrsta": "izmerjeno", "prezgodaj": false, "pravocasna": true}
```

Na `/api/departures` (`board`), `/api/connections` (`connections`), `/api/train/{no}/run` (`stops`) in `/api/live`. `null`, kadar zamude ni.

**Meja namenoma tu: strežnik pove, kaj stvar JE, odjemalec, kako je VIDETI.** Barve v objektu ni — oblikovanje, na telefonu sme biti drugačno. Razred, minuta in vrsta = pravilo.

Trije razlogi, zakaj ni okras:

* **`min` se ne sme računati na odjemalcu.** Zaokroženo z `floor(x + 0,5)`. JS `Math.round` dela isto, Javin `Math.round` tudi, `kotlin.math.round` pa **ne** — drug odjemalec bi se razšel pri natanko 30 s.
* **`razred` gre po zaokroženi minuti, ne po sekundah.** Napaka že bila: 3 280 voženj (7,29 %) v reži 30–60 s, kjer strežnik rekel „točno“ (sivo), barvna lestvica pa „1–5 min“ (oranžno). Ključ strojni (`tocno`, `1-5`, `5-15`, `nad-15`); prikazna imena („1–5 min“) ostanejo v `povzetek` in odjemalcu.
* **`vrsta` = meja med meritvijo in napovedjo.** Pri `/api/train/{no}/run` jo dopiše endpoint, ker mejo (`last_measured_seq`) pozna šele on. Ta razlika bila po zapisu v CLAUDE.md že dvakrat na zaslonu narobe.

Odjemalec, ki bere `delay_s` in sklepa sam = **star način**. V `common.js` `delayLabel()`, `delayColor()`, `delayText()` in `isEarly()` sprejmejo oboje — objekt ali gole sekunde — sekunde = rezerva za mesta brez objekta. **Nov odjemalec naj bere samo objekt.**

## Živi prihodi mestnega LPP (`lpp.py`)

Drug vir za **isti** promet: `data.lpp.si` se spremeni na 10–30 s, derp.si na ~90 s. Uporablja se **samo za prikaz** in samo za postanke **za mejo meritve** — v bazo nič, sicer bi `backtest` in `ocena` merila dve merili hkrati, ne da bi vedela.

Štiri stvari, brez katerih spoj tiho laže; vse izmerjene:

* **Njihov `trip_id` = vzorec proge, ne vožnja.** 19 163 naših voženj LPP ima 85 različnih tretjih komponent id-ja, najpogostejša 993-krat. `arrivals-on-route` zato vrne prihode **vseh** vozil na vzorcu.
* **Pravo vozilo izbere `vehicle_id`.** Isti prostor id-jev v obeh virih.
* **Lega mora biti sveža** (`collector.POSITION_FRESH_S`). `vehicle_now` hrani vrstico do ure po koncu vožnje; stara vrstica bi vezala vozilo na končano vožnjo — eta pripada naslednjemu obhodu vzorca. Ujeto pri preizkusu: meja postanek 37, eta za postanek 1.
* **Postanki se spajajo po koordinati, ne po vrstnem redu.** Postajališča ista do 0,0 m (704 od 714 pod 5 m), vzorec pa lahko daljši od vožnje.

Ob 22:15 od 25 svežih mestnih vozil **19 z uporabno napovedjo naprej**, meje so se ujemale (meja 9 → eta 10–27, meja 16 → eta 17–21) — najmočnejši dokaz pravega spoja: dva vira neodvisno povesta isto lego vozila.

**Linija mimo voznega reda (`lpp.na_tablo`, od 2. 10. 2026).** Kadar zajem pri liniji LPP vidi vsaj 3 in vsaj 20 % voženj, ki jih vozni red nima (`zajem.md`), današnja tabla „zdaj“ za to linijo pokaže LPP-jev `station/arrival` namesto voznega reda — do zadnjega LPP-jevega prihoda, dlje ostane vozni red. Vrstica nima `trip_id` (vožnje v voznem redu ni, povezava bi odprla napačno), nima zamude, nosi `lpp_vrsta` (`type` po dokumentaciji LPP: napoved / po načrtu / prihaja / obvoz); odgovor nosi `mimo_voznega_reda`. Ob kakršni koli napaki vira ostane vozni red. Postajališče → LPP-jeva koda po koordinati (25 m), seznam postajališč predpomnjen dan, prihodi 15 s. Zemljevid dobi vozila teh voženj brez `trip_id`, z `vehicle_id` kot ključem.

Izklop: `KAJROS_LPP_ZIVO=0`.

## Štetje obiska in pregled za skrbnika (`obisk.py`, `/admin`)

Prvo pravilo projekta „meri, ne domnevaj", o sebi pa ni meril nič: strežnik ni beležil zahtev, Cloudflare dnevnika ne da. Zato `obisk.py`. Štiri stvari, ki se tiho pokvarijo:

* **IP se ne shrani nikoli.** Obiskovalec = `blake2s(sol dneva ‖ IP ‖ UA)`; sol = naključni bajti, ob prehodu dneva zavrženi. Posledica, ki jo je treba **pisati na zaslon, ne samo v kodo**: mesečnih različnih ljudi ni mogoče izračunati, vsota nad 30 dnevi isto osebo šteje do 30-krat. Stran to pove v nogi; brez tega je številka videti kot unikati in ni.
* **Pot se normalizira na obliko iz usmerjevalnika** (`/app/train/{train_no}`), ne na naslov. Sicer tabela raste s prometom, ne s številom strani — LPP linija 3G ima 388 voženj. Vzorci se berejo iz `app.routes`, ne iz seznama v kodi: seznam bi se ob novi strani tiho razšel. Kar ni naša pot, gre v eno vrstico `(neznano)` — en bot, ki ugiba `/wp-admin/…`, bi sicer naredil tisoče vrstic na dan.
* **Boti so izločeni iz razrezov, ne iz prometa.** Ura dneva, naprava, država štejejo samo ljudi; `obisk_pot` šteje oboje, ločeno po stolpcih `zahtev` in `ljudi`. Iskalnik, ki vsako uro pobere isto stran, bi sicer narisal enakomeren dan in ubil edino zanimivo črto.
* **Človek = kdor je stran pognal** (od 15. 9. 2026). Pregled je kazal 104 ljudi na dan, od tega **79 z eno zahtevo** na `/` — skenerji z UA Chroma iz ZDA, Tajske, Kitajske, ponoči; en z 147 zahtevami, vse 404. Zdaj človek = samo obiskovalec s stolpcem `js > 0`: poslal je uspešen `/api/…` ali `/sw.js`, kar naredi samo pognan JS. Ogled pred tem čaka v pomnilniku (`_cakajoci`), pripiše se za nazaj. Vrstice pred stolpcem imajo `js` NULL in štejejo po starem, sicer bi zgodovina postala boti. **Aplikacija = en ključ**, ne dva: WebView (`… Kajros/1.0`) in budilka (`Kajros/1.0 (Android)`) gresta skozi `ua_za_kljuc()`. Menjava Wi-Fi ↔ mobilni podatki je še vedno nov obiskovalec — brez IP-ja se ne da združiti.
* **Pisanje ne gre v zahtevo**, ampak v svojo nit vsakih 60 s (`server._obisk_worker`). En obisk strani = 10–30 zahtev; vrstica na zahtevo bi pomenila stalno pisanje v bazo, v katero teče zajem. Cena štetja izmerjena: **0,11 ms na zahtevo** (p99 0,30 ms), podrobnosti v `docs/MERITVE.md`.

**Odzivni čas se hrani po vedrih, mediana = razred, ne vrednost.** Prikaz piše `‹ 250 ms`, ne `180 ms`: hranimo porazdelitev (`obisk_odziv`), ne vsakega časa. Izmišljena natančnost bi bila posebej zahrbtna, ker je ta stran edino mesto, kjer se počasnost vidi.

**`/admin` zaprt z žetonom iz okolja, brez privzete vrednosti.** Če `KAJROS_ADMIN_TOKEN` ni nastavljen, poti ni (404). Manjkajoč žeton v zahtevi je prav tako 404 — kdor ga nima, naj ne izve, da pot obstaja — **napačen = 403**, da se tipkarska napaka loči od pozabljene nastavitve. Primerjava skozi `hmac.compare_digest`. Po prijavi z `?k=` preusmeritev na čist naslov: žeton bi sicer ostal v zgodovini brskalnika in glavi `Referer`. Piškotek ima pot `/admin`, zato ne potuje z `/api/*` klici, ki jih brskalnik pošilja desetkrat na minuto. Poti ni v OpenAPI — `/docs` je razglas, kaj obstaja.

**Pregled: trije zavihki, en endpoint.** `/admin/podatki?od=&do=` vrne obdobje (brez meja današnji dan) in vedno še `danes`, `zadnjih30`, zdravje, sporočila -- Stanje = en klic, Zgodovina = dva. Meje dneva, tedna (od ponedeljka), meseca, leta računa prikaz; primerjavo „proti prejšnjemu“ strežnik (`obisk.prejsnje_obdobje()`): mesec s prejšnjim mesecem, leto s prejšnjim letom, ne z enako dolgim odsekom -- september proti 2.–31. 8. ni obdobje, ki bi ga kdo imel v glavi. Nad enim dnem je številka „obiskov“, ne „ljudi“ (vsota dnevnih). Oblika = predloga A iz `design/admin/`.

**Četrti zavihek, Deljenje, ima svoj endpoint** (`/admin/deljenje`, od 25. 9. 2026) in svoj ritem, 10 s: `/admin/podatki` teče na minuto, ker gredo števci v bazo na 60 s, lega poročevalca pa se premakne na 10. Iz istega razloga ga `risi()` ob osvežitvi pregleda pusti pri miru -- zemljevid bi sicer vsako minuto nastal znova. `/admin/podatki` nosi samo število za značko (`deljenje.deli_zdaj()`). Kaj je v odgovoru: `deljenje.md`.

**Aplikacija in prenosi se štejejo posebej** (od 24. 9. 2026, `meta.obisk_aplikacija_od`; prej = „ne vemo“, ne nič). Trije kraji, kjer se številka tiho pokvari:

* **Cloudflare je APK stregel s svojega roba** (`cf-cache-status: HIT`, `age` dve uri); do nas je prišel le prenos, ki mu je zgrešil. `/prenos` zato pošilja `Cache-Control: no-store` (`_PrenosStatic`). `no-cache` NE zadošča: Cloudflare z njim hrani, pri nas le preverja — `/static/base.css` izmerjeno `MISS`, nato `REVALIDATED`, pri nas 304, ne prenos.
* **Prenos ne čaka na dokaz JS**, ker `/android` JS nima — kdor pride nanjo naravnost, ga ne pošlje nikoli. Bot se izloči po UA. Šteje se `GET` s 200 ali 206 od `bytes=0-`; nadaljevanje, `HEAD` in 304 niso prenos. Posodobitev loči `?iz=aplikacija`, ki ga nosi `stran` iz `/api/android/razlicica` naprej na gumb — velja za vse nameščene različice, ker naslov pride s strežnika.
* **Pripomoček ni uporabnik.** Okno aplikacije (WebView, `… Kajros/1.2`) in pripomoček/budilka (`Kajros/1.2 (Android)`) = isti ključ, a stolpec `okno` šteje le prve: pripomoček na domačem zaslonu kliče API tudi, ko aplikacije nihče ne odpre, in bi sicer vsak dan veljal za uporabnika. Različica gre v bazo samo kot števke in pike — UA piše kdorkoli.

**Pristajalne strani so strani in prihod z iskalnika je človek** (29. 9. 2026). Do tedaj `vrsta_poti()` pozna samo `/` in `/app*`; pristajalne (brez JS) niso poslale dokaza in človek z Googla ni bil štet nikjer. Zdaj `_STRANI` in `vir_obiska()`: znan vir v `Referer` (ali `utm_source`) je dokaz. Shrani se **ime vira**, nikoli naslov (iskalni niz). `robot()` loči iskalnike in AI po imenu (razrez `robot`); `Claude-User` in `Perplexity-User` besede „bot“ nimata, zato ime robota sproži tudi `bot`. Domene se primerjajo po oznakah, ne kot podniz — „reddit.com“ vsebuje „t.co“. Nova stran za človeka = vnos v `_STRANI`, sicer se ne šteje.

**Pregled in števci se ne štejeta sama.** `/admin*` in `/static/*` gresta mimo štetja; sicer bi skrbnikovo osveževanje na minuto postalo največja postavka v lastni statistiki.

## Kar stran dolguje javnosti, ne aplikaciji

Od 12. 9. 2026 `kajros.app` odprt komurkoli. Poti niso za aplikacijo, ampak za brskalnike, iskalnike, ljudi, ki povezavo pošljejo naprej.

**Napaka = stran za človeka, JSON za stroj.** `_napaka_html()` odloča po poti, ne po glavi `Accept`: pod `/api/` in `/static/` je odjemalec stroj tudi ob `*/*` — tuji odjemalci se ob naši napaki drugače zlomijo, kot pričakujejo. Podrobnost iz kode („vlak 999999 ne obstaja“) pride na zaslon, Starlettov angleški privzetek (`Not Found`) ne.

**Absolutni naslov = `config.BASE_URL`, nikoli `request.url`.** Za Cloudflarovim tunelom je zahteva videti kot `http://127.0.0.1:8000`: izvor govori navaden HTTP, enota ne teče z `--proxy-headers`. Zemljevid strani in značke za predogled bi kazali na naslov, nedosegljiv iz interneta. (Naslova obiskovalca to ne prizadene — `obisk.py` bere `cf-connecting-ip`, ne `request.client`.)

**En naslov: `https://kajros.app`.** `http://` in `www.` preusmeri `api._en_naslov` (301, za ne-GET 308), samo ob glavi `CF-Visitor` — razvoj in domače omrežje je nimata. Do 29. 9. 2026 so vsi štirje vračali 200 z isto vsebino. Kanonski naslov v `_meta.html` gre skozi `urlencode`: `request.url.path` je razkodiran, okno vožnje je imelo `…/LPV 2276` s presledkom.

**Koren `/` = stran, JSON samo na izrecno prošnjo.** Do 15. 9. 2026 HTML samo ob `Accept: text/html`; DuckDuckGo (Bingov indeks) je zato kot opis `kajros.app` kazal `{"service":"kajros",…}`, `facebookexternalhit` z `Accept: */*` prav tako. Privzetek za ljudi — živost = `/api/health`. Straži `preveri.sh`.

**Naš `robots.txt` mora obstajati, sicer Cloudflare postreže svojega.** Njegov privzetek o naših poteh ne ve nič, pusti indeksirati `/api/`. Naš prepove `/api/`, `/admin`, `/docs`, `/redoc`.

**`/favicon.ico` = pot, ne datoteka.** Brskalniki jo prosijo ne glede na `<link rel=icon>` — zaznamek, zavihek, „pogosto obiskano“ gredo pogosto po njej. Streže se PNG; ime poti je zgodovina, brskalnik gleda `Content-Type`.

**Naslov in opis strani zapisana enkrat** (`templates/_meta.html`), ne posebej za `<title>` in `og:`. Dve različici istega stavka se razideta ob prvem popravku.

**`/zasebnost` ni obrazec, ampak edino, česar obiskovalec o nas ne more preveriti sam.** Vsebina mora ostati skladna z `obisk.py`; kdor spremeni, kaj se šteje, spremeni tudi to stran. Naslov za vprašanja = `KAJROS_STIK`, **privzeto prazen** — objava naslova je odločitev lastnika strani, ne privzetek nastavitve.

**Tujih izvorov v strani ni več.** Pisave (`static/pisave/`) in MapLibre (`static/maplibre-6.10.0/`) gostovani pri nas. Prej je šel IP vsakega obiskovalca ob vsakem odprtju Googlu, zemljevid pa je visel na `unpkg.com`. Ostanejo tuje **ploščice zemljevida** — neizogibno; naštete na strani o zasebnosti. Od 22. 9. 2026: vektorske ploščice in pisave OpenFreeMap (`tiles.openfreemap.org`), Esri samo še rezerva brez WebGL2 (glej `zemljevid.md`).


## Obrazec za stik: edina pot, ki piše iz zahteve

Do 12. 9. 2026 `api.py` samo `GET`, zapisano kot razlog, zakaj je javna izpostavitev varna. Zdaj štiri pisalne poti (seznam v CLAUDE.md), nobena nova ne sme priti mimogrede: `test_pisalne_poti_so_nastete` pade, če se seznam podaljša.

**Brisanje in označevanje na ISTI poti** (`POST /admin/sporocila/{id}`, loči ju polje `akcija`), ne vsako na svoji. Pisalne poti so naštete, vsaka nova = odločitev, ne podrobnost. Brisanje nepovratno, ima potrditev: gumb tik ob „prebrano“, zgrešen klik na telefonu bi stal sporočilo.

**Vsa varovalka v `kajros/stik.py`, ne razsuta po `api.py`.** Namen: v enem branju se vidi, kaj neznanec sme. Pet plasti, po vrsti:

| plast | kaj ustavi |
|---|---|
| podpisan žeton (HMAC, čas izdaje) | pošiljanje mimo naše strani, ponovno rabo obrazca |
| časovna past (`NAJHITREJE_S` = 4 s) | robota, ki izpolni in pošlje takoj |
| vaba (skrito polje `naslov`) | robota, ki izpolni vsa polja |
| `NA_URO` = 3, `NA_DAN` = 5 | enega vztrajnega pošiljatelja |
| `VSEH_NA_DAN` = 50 | porazdeljeno kampanjo |

Zadnja šteje: prve štiri ustavijo preprost robot, peta omeji škodo, kadar jih kdo prebije. Brez nje bi bila posledica polna **baza meritev** — edino, česar ni mogoče ponoviti za nazaj.

**Vrstni red preverb ni poljuben: najprej poceni, šele nato poizvedba.** Robot, ki tolče po obrazcu, tako ne povzroči poizvedbe na vsak poskus.

**Ujeta vaba vrne videz uspeha, ne napake.** Robot, ki izve, da je ujet, se nauči, česa ne sme izpolniti. Zato tudi prehitro poslan obrazec ne pove „bilo je prehitro“ — povedalo bi, koliko naj počaka.

**Naslova IP ne shranimo niti tu.** Omejevanje teče v pomnilniku nad zgoščeno vrednostjo, po restartu izgine. Zavestna menjava: raje kdo po restartu pošlje nekaj sporočil več, kot da bi zaradi spama vodili dnevnik naslovov. `test_naslov_ip_ni_v_shemi` straži — kdor doda stolpec „samo za odkrivanje spama“, naj tam pade.

**Telo se razbere s `parse_qs`, ne z `request.form()`.** Slednji potegne `python-multipart` = šesta vrstica v `requirements.txt` za tri vrstice dela. Obrazec zato `application/x-www-form-urlencoded`.

**Po uspehu preusmeritev (303), ne izris.** Brez nje osvežitev pošlje sporočilo znova, v nabiralniku dve enaki. Ob napaki se stran izriše **z vpisanim besedilom**: kdor je napisal odstavek in dobil „e-naslov ni videti pravi“, ga ne sme izgubiti.

**Besedilo = vnos neznanca, gre skozi `escapeHtml`.** Prelome vrstic ohrani CSS (`white-space: pre-wrap`), ne pretvorba v `<br>` — ta bi bila druga pot, po kateri bi lahko kaj ušlo. Preverjeno z vnosom `<img src=x onerror=…><script>…`: v DOM ni živega elementa.

**Stran o zasebnosti mora ostati skladna.** Tu se prvič shrani, kar je človek napisal sam (e-naslov in besedilo); kdor spremeni, kaj se hrani, spremeni tudi `/zasebnost`. Obrazec se da ugasniti s `KAJROS_STIK_OBRAZEC=0` — takrat poti ni (404), odsek na strani o zasebnosti odpade.


## Obvestila kajrosa (`obvestila.py`)

Nastala 28. 9. 2026: DUJPP je objavil vozni red brez vlakov in s pomešanimi trasami, potnik pa ni imel kje prebrati, da ni kriv on. Skrbnik piše v `/admin` (zavihek Obvestila, `POST /admin/obvestila`, `akcija` = `objavi` | `umakni` | `brisi` na isti poti), strani berejo `/api/obvestila?network=zeleznica|avtobus|vse`.

* **Vsako ima rok, največ 30 dni.** Obvestilo, ki ostane, ko razlog ni več res, laže. Umaknjeno dobi rok zdaj in ostane v seznamu pregleda — ve se, kaj je bilo rečeno in do kdaj.
* **Omrežje kot povsod**: obvestilo brez omrežja gre na vse strani, vlakovno ne na avtobusne. Domača, zemljevid in pot vprašajo `vse` in dobijo oznako omrežja na kartici.
* **Stran jih naloži sama, ne predloga** (`common.js`, mesto `[data-obvestila]` iz `_obvestila.html`): aplikacija za Android pusti stran odprto ure in dneve, obvestilo se mora pokazati ob vrnitvi (`pollWhileVisible`, 5 min). Pristajalne strani so brez JS, zato jih izrišejo na strežniku (`obvestila_za`), brez gumba za zapiranje.
* **Zaprto si zapomni brskalnik** (`kajros:obvestila-skrita`, zadnjih 50 številk), ne piškotek: `/zasebnost` obljublja „piškotkov ni“.
* Predpomnjeno na `obvestila.razlicica` (premakne jo vsak zapis, objava je na strani takoj), rok se preveri še ob strežbi. `/api/obvestila` 3–5 ms.
