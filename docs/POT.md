# Načrtuj pot

Načrt strani, ki odgovori na vprašanje *„sem tu, moram biti tam — kako in kdaj
grem?"*. Vse dosedanje strani znajo odgovoriti šele, ko potnik sam ve, s katere
postaje gre; tu je izhodišče **točka na zemljevidu**, ne postaja.

Odgovor je veriga: hoja → vožnja → (prestop) → vožnja → hoja, in ena ura na
vrhu — kdaj moraš iz hiše.

## Kaj je odločeno in zakaj

| odločitev | razlog |
|---|---|
| **brez iskanja po naslovu** | geokodiranje pomeni tujo storitev, ki ob vsakem tipkanju izve, kam greš. Cilj se izbere na zemljevidu, iz shranjenih točk ali po imenu postaje |
| **doseg hoje 25 minut** | izmerjeno: večji doseg ne stane nič in najde boljše poti (Grosuplje 10 minut boljši prihod) |
| **hoja iz OSRM, ne iz faktorja** | izmerjeno na 1 080 poteh: faktor 1,45 podceni pot v 48 % primerov, največji obvoz je 7,86× |
| **usmerjevalnik doma, ne javni** | javni bi ob vsakem iskanju izvedel, kje si; poleg tega je „samo za demo" in bi bil nova točka odpovedi |
| **faktor ostane kot zasilna pot** | če vsebnik ne odgovori, stran vseeno dela — in to prizna |

## Hoja

`hoja.sekunde()` je **ena funkcija** in nihče drug ne ve, od kod številka pride.
Prvi vir je OSRM (`KAJROS_OSRM`, privzeto `http://127.0.0.1:5000`), zasilni pa
zračna razdalja × 1,45 pri 5 km/h.

Izmerjeno pri postavitvi na arwenu (Ubuntu 24.04, i5-6200U, 4 niti):

| korak | čas | vrh pomnilnika |
|---|---|---|
| prenos `slovenia-latest.osm.pbf` (299 MB) | 30 s | — |
| `docker pull` | 21 s | — |
| `osrm-extract -p foot.lua` | **481 s** | **2,25 GB** |
| `osrm-partition` + `osrm-customize` | 106 s | 572 MB |
| podatki na disku (brez `.pbf`) | 807 MB | |
| strežnik med tekom | | 525 MB |

| matrika ena točka → N postajališč | 10 | 30 | 70 | 120 |
|---|---|---|---|---|
| odziv | 8 ms | 14 ms | 32 ms | 81 ms |

Troje, kar je meritev pokazala in se hitro pozabi:

* **Naš strežnik vrne isto kot javni** — 412,8 m do decimalke. „Demo" je bila
  omejitev gostitelja, ne programa.
* **OSRM-ov peš profil hodi 5,00 km/h**, izmerjeno na 1 080 poteh. Trajanja ni
  treba računati posebej; `duration` je že prava številka.
* **Predfilter bližnjih postajališč ne sme uporabiti faktorja.** Zračna črta je
  vedno krajša od prave poti, zato filter pri 2 083 m (25 min × 5 km/h) ne
  izpusti ničesar dosegljivega. Faktor v predfiltru bi tiho odrezal postaje, ki
  so v resnici v dosegu.

Kandidatov v tem polmeru: Bavarski dvor 201, Ljubljana Polje 66, Grosuplje 27,
Bohinjska Bistrica 9 (8. 9. 2026).

## Iskanje

Jedro je razširjen `journey.plan()` — raztezanje po krogih, ki že obstaja.
Manjkajo štiri stvari:

1. **več izhodišč z različnimi časi** — vsako postajališče je dosegljivo ob svoji
   uri, ker je hoja do vsakega druga;
2. **več ciljev z različnimi časi** — cilj ni prihod na postajo, ampak na točko;
3. **peš prestop med postajališči** — zdaj se prestopa samo na istem `stop_id`,
   torej „Bavarski dvor" v eno smer in v drugo za iskalnik nista isti kraj.
   4 507 od 5 500 imen ima več kot en `stop_id`;
4. **obe omrežji hkrati** — vlak in avtobus v isti verigi.

Izmerjeno s prototipom čez obe omrežji, štiri noge, hoja na obeh koncih:
**225–441 ms** na razvojnem računalniku, in **čas ni odvisen od dosega hoje**
(16 ali 73 izhodiščnih postajališč je enako hitro) — cena je v premetavanju
voznega reda, ne v številu izhodišč.

Preverjeno na roko: Grosuplje → Ljubljana center ob 8:00 = 416 m hoje (6,5 min)
→ LP 3232 ob 08:17 → Ljubljana 08:44 → 982 m hoje (15,3 min) → **08:59**.
Prototip vrne isto minuto.

## Zamude

Zaradi tega stran obstaja; vozni red zna vsak. Katera številka velja na
potnikovem postanku in od kod je, odloči `stats.zamuda_na_postanku()` —
**isto pravilo, ki ga uporablja iskalnik zvez**. Načrtovano je bilo brati iz
`journey.board()`; ob pisanju se je pokazalo, da je pravo dejanje izluščiti
pravilo, ne ga poklicati skozi tablo, ki odgovarja na drugo vprašanje.

Iskanje teče **po voznem redu**, ker napovedi za vožnjo čez pet ur ni. Zamuda se
pripiše tam, kjer jo imamo, in veriga se **znova preveri**: če prva noga zamuja
8 minut in je prestop imel 6, predlog pade ali dobi opozorilo.

Pri avtobusih velja tudi obratno: 25 % jih odpelje **pred** voznim redom. Pri
hoji na postajo je to nevarnejše od zamude in mora biti napisano.

## Kaj mora stran priznati

* **Peš vso pot je včasih najhitreje.** Prototip za Polje → BTC vrne prihod
  09:04 pri odhodu ob 08:00; hoja je 47 minut, torej 08:47. Če transport izgubi,
  se to pove.
* **Minute hoje so eno od meril**, sicer bi prvi predlog vedno bil tisti, ki te
  pošlje 25 minut peš, da prihraniš dve. Predlogi: „najhitreje", „najmanj hoje",
  „najmanj prestopov", kadar se razlikujejo.

## Pasti tega projekta

* **Polnoč.** 2 394 postankov ima `dep_s ≥ 86 400`, največji 121 680 (33:48).
  Iskanje ob 23:40 mora videti v naslednji prometni dan.
* **`network` je stran, ne prevozno sredstvo.** Ta stran je za zemljevidom šele
  druga, ki meša obe omrežji, in mora `network` zavestno pustiti prazen.
* **Prag za prestop je odvisen od omrežja** (vlak 6 min, avtobus 3). Pri mešani
  verigi velja prag tistega, na kar se vkrcavaš, plus hoja, če postajališče ni
  isto.
* **`MAX_STOP_TIMES` je tiho vračal prazen vozni red.** Ta razred napake nas je
  že ugriznil, ko je mestni LPP potrojil omrežje. Ne sme se ponoviti.
* **Zapisovanje lege.** Zahteva nosi, kje si in kam greš. To se ne sme znajti v
  dnevniku strežnika.

## Vrstni red

1. ✅ Glasna varovalka `MAX_STOP_TIMES` + `hoja.py` + OSRM na arwenu
2. ✅ Peš noge med postajališči (`pespot`, `kajros pespoti`)
3. ✅ Jedro: iskanje z več izhodišči in cilji čez obe omrežji (`pot.py`,
   `kajros pot`)
4. ✅ Endpoint `/api/pot` + stran `/app/pot`, „čim prej"
5. ✅ Zamude v predlogih in preverjanje, ali veriga drži
6. ✅ Podrobni prikaz ene poti (`/app/pot/podrobno`): pešpot z geometrijo in
   vmesni postanki vožnje
7. ⬜ „Biti tam ob X" (obratno iskanje), shranjene točke

**Peš noge v `journey.plan()` namenoma niso vezane.** Njegova oblika odgovora
(`train1`, `trip1`, `via`) nima mesta za peš nogo in prikaz bi jo narisal
napol; prvorazredne so v `pot.py`, kjer je bil odgovor zasnovan zanje.

### Kaj ostaja odprto

* **„Biti tam ob X"** je obratno iskanje: isti postopek, obrnjen v času, iz
  cilja nazaj do najpoznejšega odhoda. Nekaj deset vrstic, ne nov algoritem.
* **Več predlogov.** Zdaj sta „najhitreje" in „z manj hoje"; „najpozneje
  odideš za isti prihod" je vredno več od obojega in pride z obratnim iskanjem.
* **Shranjene točke** („dom", „služba") — `localStorage`, kot pri shranjenih
  poteh iskalnika.
* **Predlogi po prihodu, ne le prvi.** Iskanje vrne eno pot na vprašanje;
  „naslednja čez pol ure" je še eno vprašanje in še eno iskanje.
