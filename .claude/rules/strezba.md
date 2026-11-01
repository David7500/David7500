---
paths:
  - "kajros/api.py"
  - "kajros/lpp.py"
  - "kajros/obisk.py"
---
# Kaj sme in česa ne sme API

Zajem (kaj feed pove in kje laže): `zajem.md`; tu strežba.

* **Meja meritev/napoved = `stats.last_measured()`** v vsakem odgovoru z zamudo. `/api/train/{no}/run` vrne `last_measured_seq` — prikaz ga bere, **ne računa sam**.
* **Meja ne gre čez postajo iz svežega poročila SŽ**: poročilo „ob prihodu na Y“, mlajše od 8 min (`stats.SVEZE_POROCILO_S`) = vlak na Y še ni bil. „Je tu že bil“ 13,1 → 2,7 %, „še ni bil“ 1,2 → 11,8 % (cenejša). V `_LAST_MEASURED_SQL` in `api._LIVE_SQL`.
* **`network` povsod, privzeto `zeleznica`, filter v poizvedbi** (železnica 700 000 vrstic, avtobusi 12 M).
* **Zamuda čez `api.MAX_LIVE_DELAY_S` (6 h) ni živa.**
* **Odprto: `journey.now_seconds` je ura stene**, včerajšnji okvir `now_s + 86400` (deset mest). Na dan premika ure (25. 10. 2026, 28. 3. 2027) do treh zjutraj je današnji okvir za uro stran, včerajšnji jeseni slučajno prav. Popravek le oboje hkrati skozi `stats.polnoc` (razlika polnoči obeh dni, ne 86 400); sam `now_seconds` pokvari včerajšnje nočne. Zveze z `od` (`_ura_ts`, `_odhod_ts`) že gredo skozi epoho.
* `vehicle_now` = samo lega (upsert); **zamude v njej ni** — doda jo `stats.last_measured()`, isto pravilo kot živi seznam (prej kartica „? min“).

## Lege: zaostanek je feed, ne mi

* Vlak = interpoliran na postaji, avtobus = GPS.
* Vozilo objavi na **20 s**, v feedu je že ~20 s staro (p90 30 s), proti večeru slabše. CORS (`Access-Control-Allow-Origin` ni) prepreči branje iz brskalnika — posrednik smo mi.
* `config.POSITION_SECONDS = 10`; brskalnik vpraša v koraku s strežbo (`X-Osvezi-Cez`, `common.pollVehicles()`, zamik 0–2 s, skrita stran nič). Naš prispevek 15 → 5 s. Proti feedu: v 66 % isti žig, v 25 % ena objava zadaj (≈ 5/20). Na 5 s bi prihranili 3 s od 32 za dvojno breme → ostane 10 s (`KAJROS_POSITION_SECONDS`).
* Pogojni GET pri legah ne pomaga (feed se spremeni na 2 s).
* Okno vožnje lego osvežuje s `pollVehicles()`; pogled se premakne le, ko vozilo uide iz okvira.

## Predpomnilnik na znački podatka, ne na uri

* Značke: `rt_fetched` (30 s), `positions_fetched` (10 s), `gtfs_imported_at`; `_predpomni()` ima `najvec_s` za `KAJROS_COLLECTOR=0`. Ključavnica **na ključ**.

  | pot | prej | zdaj |
  |---|---|---|
  | `/api/live` | 253 ms | **3,8 ms** |
  | `/api/stations` | 77 ms | 3,3 ms |
  | `/api/network.geojson` | 51 ms | 3,3 ms |
  | `/api/shapes/live` | 33 ms | 3,0 ms |

* `/api/stations` in `/api/network.geojson` predpomnita **serializiran JSON** (`Response`; pretvorba 9 791 postaj je večina cene).
* **Sveže po predpomnilniku**: `age_s` pri legah.
* `/api/vehicles` na `positions_fetched`. **Ključ premakne vsak, ki lege zapiše**: `poll_positions`, NAP, `poll_lpp`. Cena: `X-Osvezi-Cez` šteje 10 s od zadnjega premika.
* **Značka = to, od česar je odgovor res odvisen** (vezava na `positions_fetched` je predpomnilnik razbila vsakih 10 s; drago na `rt_fetched`, števci sveže: 1,3 s → 4–42 ms).
* **Ogrevanje** (`server._ogrej_zive`, po vsakem uspešnem zajemu): **skozi ENDPOINT, ne notranjo funkcijo** (`api._live()` je delo zavrgel). Samo, kar strani vprašajo (`network=zeleznica`). **Na malini ne** (`server._strezemo`, postavi ga samo `lifespan`).
* Statika na znački uvoza (`/api/stations*`, `/api/network.geojson`): `STATIKA_S` in `v_ozadju`; `_ogrej_pot` ogreje VSE ključe.
* **Vozni red v zahtevi samo iz predpomnilnika**: `stats._vozni_red_zveze`, `journey._tabla_vozni_red`, zložena imena, `stats._TIPICNO_PREJ`. Lege računa nit `kajros-vozila` po premiku `positions_fetched` (le, če je kdo vprašal v 2 min).
* Pika živosti bere `/api/svezina`, ne `/api/health`.
* Tabla: `first_seq`/`last_seq` na `trip` (`db.fill_trip_window()`), ne `GROUP BY` čez `sched` (120 → 7 ms). Nagrobniki (`first_seq` NULL) na tablo ne pridejo.

## En proces in GIL

**Konvoj GIL je vzrok repov**: `sqlite3` GIL spusti in čaka `switchinterval`, dokler ga nit s čistim Pythonom ne odda (tabla 7 ms → 11,9 s). `server.lifespan`: `sys.setswitchinterval(0.0005)`. Novo dolgo Pythonovo delo v kos, ki sprošča GIL, ali iz procesa (`promet._Razbor`: tabla 608 → 80 ms). Diagnoza `scripts/konvoj_gil.py`.

**Tuj strežnik nikoli sinhrono v zahtevi.** `lpp._prinesi` v ozadju, zahteva vzame odgovor do 90 s, prvič čaka ≤ 0,3 s, po neuspehu 15 s mir; zasloni ob napaki minuto tišine.

## `zamuda`: strežnik pove, kaj stvar JE

```json
"zamuda": {"s": 320, "min": 5, "razred": "1-5",
           "vrsta": "izmerjeno", "prezgodaj": false, "pravocasna": true}
```

Na `/api/departures`, `/api/connections`, `/api/train/{no}/run`, `/api/live` (`stats.opis_zamude()`); `null` brez zamude. Barve ni — to je odjemalčevo.
* **`min` ne računaj na odjemalcu** (`floor(x + 0,5)`; `kotlin.math.round` se razide pri 30 s).
* **`razred` po zaokroženi minuti** (3 280 voženj v 30–60 s je bilo sivih in oranžnih hkrati). Ključi `tocno`, `1-5`, `5-15`, `nad-15`.
* `vrsta` pri `/run` dopiše endpoint.
* `common.js` (`delayLabel`, `delayColor`, `delayText`, `isEarly`) sprejme objekt ali sekunde; **nov odjemalec bere samo objekt**.

## Živi prihodi mestnega LPP (`lpp.py`)

`data.lpp.si` (10–30 s) **samo za prikaz** in za postanke **za mejo meritve** — v bazo ne (to dela `zamude_lpp`).
* Njihov `trip_id` = vzorec, ne vožnja; vozilo izbere `vehicle_id`.
* Lega mora biti sveža (`collector.POSITION_FRESH_S`).
* Postanki se spajajo po koordinati.
* **Za vozilom ni napovedi te vožnje** (`lpp.eta_po_postankih`): prevoženo postajališče ima prihod NASLEDNJEGA obiska (naslednja vožnja vzorca), vrsta 1. **Odloči vrsta**: ima vozilo napoved (0, 2), velja samo ta; obvoz (3, stalno eta 1) nikoli; samo načrt: od najmanjšega eta naprej. Sam najmanjši eta je vzel prave številke pred vozilom pri 3 od 29 vozil (LPP 14 Čerinova, 18L Litostroj). 31. 10. 2026 LPP 2 brez meje: izhodišče +92 „v živo“, ocena +92 na 16 postankih. Meritev po objavi: `docs/presoja/napovedi/preveri_zivo_lpp.py`.
* **Linija mimo voznega reda** (`lpp.na_tablo`): ≥ 3 in ≥ 20 % neznanih voženj z napovedjo (pripete in dvojniki ne štejejo, `zajem.md`) → tabla „zdaj“ za to linijo iz `station/arrival` do zadnjega LPP-jevega prihoda in vsaj `OBZORJE_S` (55 min), kjer je bil zaslon prebran: zaslon kaže vse prihode do 60 min, česar ni, ne pride (26. 10. 27 po objavi na Kolodvoru, ki ga ni vozila). Linijo, ki je vozni red tu nima, živa brez para pa tu ustavi (`postaje_brez_voznje`, 27 na Navju), doda z zaslona; `stop_ids` = izbrana stran ceste. Vrstica brez `trip_id` in zamude, z `lpp_vrsta`; odgovor `mimo_voznega_reda`. Ob napaki vozni red. Postajališče → koda LPP po koordinati (25 m).
* **Vozilo žive brez para** na zemljevidu: „ni znana · vožnja mimo voznega reda“ in naslednji postanek po napovedi feeda („napoved LPP“).
* **derp.si 5 min tiho** (`lpp.derp_molci`, po `meta.lpp_rt_fetched`): vse linije LPP z zaslona, `lpp_izpad`, stran napiše „Zamud mestnih avtobusov LPP ta hip ne dobivamo. Prihode kažemo, kot jih napove LPP.“
* **Obvoz in odpoved** (`api._oznaci_obvoze`): `ne_ustavi` (`alerts.ne_ustavi`; primestne po zaslonu), `odpovedano` (`collector.odpovedane`). Prečrtano, „naslednja“ prva, ki ustavi; Moje poti ne štejejo; iskalnik `ne_ustavi`: `od` | `do`; pot tam ne vstopi; pristajalna izpusti. Molk zaslona minuto (`lpp._zasloni_molcijo_do`).
* Izklop `KAJROS_LPP_ZIVO=0`.

## Kje vozila ne ustavijo: prikaz (`opazovano.za_prikaz`)

* **Edino, kar prikaz bere**; `ne_ustavi`, `za_voznjo` iz njega. Predpomnjeno na znački reda in `opazovano_dan.koncano`, prvič 41 ms, nato 0,12 ms. Izklop `KAJROS_OPAZOVANO_PRIKAZ=0`.
* Vožnje se iz ključa izberejo ob branju (`trip_id` zamenja uvoz, `start_s` ostane).
* **`ne_ustavi` = ista pot kot obvoz LPP** (tabla, `alerts.oznaci_zveze`, `alerts.brez_zaprtih_prestopov`, `alerts.ne_ustavi_vsi` za pot, pristajalni), z `opazovano` za besedo. **`redko` ni `ne_ustavi`**: odhod ostane, opomba.
* Beseda „zadnje dni tu ni ustavljal“, nikoli „zaprto“: vemo samo iz leg.
* **Današnji prehod takoj omili** v `redko` (`_danes`, na `OSVEZI_S`), trditev po `POZABI_S` odpade, če nočni račun stoji (`zdravje`: `opazovano`).
* Drug dan samo beseda, nič prečrtanega; za nazaj nič (`_na_postankih`).
* `limit` (widget): `ne_ustavi` v `/api/connections` je niz „od“/„do“, Android ga bere z `optBoolean`, zato strežnik vrstico vzame ven.

## Štetje obiska (`obisk.py`) in `/admin`

* **IP se ne shrani nikoli**: `blake2s(sol dneva ‖ IP ‖ UA)`, sol zavržena ob polnoči. Mesečnih unikatov ni — stran to pove.
* Pot normalizirana na usmerjevalnik (`/app/train/{train_no}`, iz `app.routes`); tuje → `(neznano)`.
* Boti izločeni iz razrezov; `obisk_pot` ima `zahtev` in `ljudi`.
* **Človek = je pognal JS** (`js > 0`: uspešen `/api/…` ali `/sw.js`; prej 79 od 104 skenerji). Ogled čaka v `_cakajoci`. Aplikacija = en ključ (`ua_za_kljuc()`).
* Pisanje v svojo nit na 60 s (`server._obisk_worker`); 0,11 ms na zahtevo.
* Odzivni čas po vedrih (`obisk_odziv`), prikaz `‹ 250 ms`.
* **Aplikacija in prenosi**: `/prenos` `Cache-Control: no-store` (`_PrenosStatic`; `no-cache` Cloudflare hrani). Prenos brez dokaza JS (bot po UA); `GET` 200 ali 206 od `bytes=0-`. Posodobitev loči `?iz=aplikacija`. Stolpec `okno` šteje le WebView, ne pripomočka.
* **Prihod z iskalnika je človek**: `_STRANI` in `vir_obiska()` (`Referer` ali `utm_source`); shrani se **ime vira**, nikoli naslov. `robot()` po imenu (`Claude-User`, `Perplexity-User`). Domene po oznakah („reddit.com“ vsebuje „t.co“). Nova stran za človeka = vnos v `_STRANI`. Naša `utm_source`: „povabilo“, „poslano“.
* **Vir = dokaz le z `Sec-Fetch-Mode: navigate`** (ponarejen Google: 357 namesto ~238). Razrez `prihod` šteje vse. `scripts/boti.sh [dan]`.
* `/admin*` in `/static/*` mimo štetja.

**`/admin`**: žeton iz okolja brez privzetka; brez nastavitve ali brez žetona **404**, napačen **403**; `hmac.compare_digest`; po `?k=` preusmeritev na čist naslov; piškotek s potjo `/admin`; ni v OpenAPI.
* `/admin/podatki?od=&do=` (+ `danes`, `zadnjih30`, zdravje, sporočila). Primerjava `obisk.prejsnje_obdobje()` (mesec s prejšnjim mesecem). Nad dnem „obiskov“, ne „ljudi“. Oblika A iz `design/admin/`.
* **Zavihek Viri**: kartica na vir iz `viri.pregled()` (vloga, ritem, zadnji odgovor, zadnja napaka, nit, „čaka“, licenca, „Kaj storiti“); `razlogi`; gumb **Preveri vire zdaj** (`GET /admin/viri/preveri`, ne piše). „Zajem“, „Stroj“, „Dnevnik“ (`server.DNEVNIK`, 150 vrstic). **Živa nit vira ne pobarva**; le ustavljena (rdeče).
* **Deljenje** svoj endpoint `/admin/deljenje`, na 10 s; `risi()` ga ob osvežitvi pusti. `deljenje.md`.
* **Koledar** (`koledar.py`, `GET /admin/koledar` → `{html, spremenjeno}`): `KOLEDAR.md` ob kodi, prebran ob vsaki zahtevi. Izris lasten: vse skozi `html.escape`, `href` samo `http(s)`, pot v repozitoriju = koda. Vrstice razdelka `koledar.NA_VRSTI` z datumom danes ali prej dobijo `je-zapadlo`; preimenovan razdelek barvanje tiho izklopi (`test_pravi_koledar_se_izrise`). **Na arwenu je datoteka z zadnjega potiska**: `posodobi.sh` prepiše celo drevo, `ProtectHome` domače mape ne vidi (`test_objava_prenese_koledar`).

## Kar stran dolguje javnosti

* **Napaka = stran za človeka, JSON za stroj** po poti (`_napaka_html()`; `/api/`, `/static/` = stroj).
* **Absolutni naslov = `config.BASE_URL`**, nikoli `request.url` (tunel: `http://127.0.0.1:8000`). `obisk.py` bere `cf-connecting-ip`.
* **En naslov `https://kajros.app`**: `api._en_naslov` 301 (ne-GET 308), samo ob `CF-Visitor`. Kanonski v `_meta.html` skozi `urlencode`.
* **`/` = stran**; JSON samo na izrecno prošnjo (živost `/api/health`). Straži `preveri.sh`.
* Naš `robots.txt` mora obstajati (prepove `/api/`, `/admin`, `/docs`, `/redoc`).
* `/favicon.ico` = pot, streže PNG.
* Naslov in opis enkrat (`templates/_meta.html`).
* `/zasebnost` skladna z `obisk.py`; `KAJROS_STIK` privzeto prazen.
* **Tujih izvorov ni** (pisave `static/pisave/`, MapLibre lokalno) razen ploščic (`tiles.openfreemap.org`, Esri rezerva).

## Obrazec za stik (`stik.py`)

Pisalne poti naštete (`CLAUDE.md`), `test_pisalne_poti_so_nastete`.
* Brisanje in označevanje na **isti** poti (`POST /admin/sporocila/{id}`, `akcija`); brisanje s potrditvijo.
* **Vsa varovalka v `stik.py`**, po vrsti, najprej poceni:

  | plast | kaj ustavi |
  |---|---|
  | podpisan žeton (HMAC, čas izdaje) | pošiljanje mimo strani, ponovno rabo |
  | časovna past (`NAJHITREJE_S` = 4 s) | takojšnjega robota |
  | vaba (skrito polje `naslov`) | robota, ki izpolni vse |
  | `NA_URO` = 3, `NA_DAN` = 5 | vztrajnega pošiljatelja |
  | `VSEH_NA_DAN` = 50 | porazdeljeno kampanjo (varuje bazo meritev) |

* Ujeta vaba in prehitro = **videz uspeha**.
* IP ne niti tu (omejevanje v pomnilniku nad zgoščeno); `test_naslov_ip_ni_v_shemi`.
* Telo s `parse_qs`, ne `request.form()` (`python-multipart`); `application/x-www-form-urlencoded`.
* Po uspehu 303; ob napaki izris z vpisanim besedilom.
* Besedilo skozi `escapeHtml`, prelomi s `white-space: pre-wrap`.
* Ob spremembi hranjenega popravi `/zasebnost`. `KAJROS_STIK_OBRAZEC=0` → 404.

## Obvestila kajrosa (`obvestila.py`)

Skrbnik v `/admin` (`POST /admin/obvestila`, `akcija` = `objavi` | `umakni` | `brisi`), strani `/api/obvestila?network=zeleznica|avtobus|vse`.
* **Rok obvezen, največ 30 dni**; umaknjeno dobi rok zdaj.
* Brez omrežja na vse strani; domača, zemljevid, pot vprašajo `vse`.
* Stran naloži sama (`common.js`, `[data-obvestila]`, `_obvestila.html`, `pollWhileVisible` 5 min); pristajalne na strežniku (`obvestila_za`).
* Zaprto v `kajros:obvestila-skrita` (50), ne piškotek.
* Predpomnjeno na `obvestila.razlicica`; rok še ob strežbi.
* **Samodejno** (`obvestila.samodejna`, `obvestila.brez_podatkov(vrsta, …)`): ≥ 3 vožnje po voznem redu, zadnji podatek > 20 min → „Od 01:24 ne dobivamo podatkov o vlakih …“. Mesec zgodovine: najdaljša zdrava vrzel 15,6 min (avtobusi 7,2). `id` = čas zadnjega podatka (avtobusi + 10¹⁰). Ni v bazi, računa na minuto. V pregledu „Samodejna“, brez gumba. Avtobusni zadnji podatek po `run_feed_ts` (vlakovni ne: 1,8 s).
* **Avtobusi v dveh skupinah** (`stats.vozi_zdaj(lpp_posebej=True)`): medkrajevni in mestni LPP; mestni „molči“ šele, ko molči tudi nit zaslonov (15 min). Oba → eno „o avtobusih“.
