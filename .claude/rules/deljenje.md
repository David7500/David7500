---
paths:
  - "kajros/deljenje.py"
  - "kajros/static/deli.js"
  - "kajros/static/deli.css"
  - "kajros/static/admin_deljenje.js"
  - "android/app/src/main/kotlin/app/kajros/Deljenje*.kt"
  - "tests/test_deljenje.py"
---

# Deljenje lege potnikov

Potnik na vozilu deli lego; drugi vidijo, kje je vozilo. Razlog je
`docs/MERITVE.md`, „Prehoda vlaka se iz teh podatkov ne da ugotoviti“: feed
prehod pri vlaku potrdi v 0,4 % postankov, resnico ima samo človek na vlaku.
Uvedeno 25. 9. 2026, obljubljeno dvema potnikoma do 2. 10. 2026.

## Kaj se pokaže (odločil David, 25. 9. 2026)

* **En poročevalec: feed IN poročilo**, vsak s svojo oznako. Tabla in
  iskalnik dobita vrstico „potnik na vozilu: …“, okno vožnje okvir s
  poročilom, zemljevid vlak na potnikovi legi in v kartici obe vrstici.
  Feedova zamuda, ura in `nepotrjen_do` ostanejo.
* **Dva ali več, ki se ujemata: feed ni več potreben.** `deljenje.dopolni()`
  zamenja zamudo, pričakovano uro in `nepotrjen_do` (vrsta
  „po poročilu potnikov“); okno vožnje premakne mejo meritve do zadnje
  postaje, ki sta jo potnika prevozila (`mimo_seq`), napoved za naprej teče
  od njune lege (`common.fetchRunAndForecast`).
* **Ujemanje je po zamudi, ne po legi** (`SOGLASJE_S`, 2 min): dve točki iz
  različnih trenutkov sta na različnih krajih, izpeljana zamuda pa je ista.
* **Samo dokler so poročila sveža** (`SVEZE_S`, 120 s). Prehodi pa so
  opažanja in veljajo ves dan, tudi ko je poročevalec izstopil.

## Kaj se hrani

Točke **projicirane na traso** (`deljenje_tocka`: razdalja vzdolž, odmik,
čas, natančnost, hitrost) — brez surovih koordinat in brez identitete.
Hranijo se za kasnejše izboljšanje modela (Davidova zahteva). Lega pred
potrditvijo vozila ne gre nikamor; kandidati so `POST`, da koordinate ne
pristanejo v dnevnikih strežnika in tunela. `/zasebnost` to pove.

## Varovalke

API nima avtentikacije. Zato: deljenje se začne samo za vožnjo, ki ta hip
lahko je tu (isto pravilo kot kandidati); vsaka točka mora biti ≤ 200 m od
trase in se premikati hitreje od 250 km/h ne sme; tri zaporedne natančne
točke izven trase so izstop; točke z natančnostjo slabšo od 250 m se
preskočijo (predor ni izstop). Omejitve na pošiljatelja so v pomnilniku kot
v `stik.py`, dnevni strop čez vse v bazi. `Content-Type: application/json`
je obvezen, da brskalnik pred tujo zahtevo vpraša CORS (dovoli samo GET).

## Kandidati

Postaje v okolici (vlak 12 km, avtobus 6 km), vožnje skozi njih, projekcija
na traso, nato čas: po voznem redu in zadnji zamudi mora biti vozilo tu
v oknu −15 / +45 min (nesimetrično, ker je zamuda, ki je feed ne pozna,
prav primer, zaradi katerega vse to obstaja). Avtobus z GPS se oceni po
razdalji do vozila. Smer iz dveh leg (≥ 40 m narazen) izloči vozila v
nasprotni smeri. Izmerjeno v `docs/MERITVE.md`, „Deljenje lege“.

## Pregled za skrbnika (`/admin#deljenje`)

Zemljevid in seznam današnjih deljenj po vozilih (`deljenje.pregled()`).
**Kar je „javno“, pride iz `stanje()`** in ne iz lastnega računa: pregled mora
pokazati isto kot tabla in zemljevid, sicer ne pove ničesar o tem, kar potnik
vidi. Zraven sta feedova zamuda in GPS avtobusa, da se razhajanje vidi --
**samo ob živem deljenju**; feed zdaj proti potniku izpred dveh ur ni
primerjava.

Sled je del trase med prvo in zadnjo sprejeto točko (`_kosi()`, razrezan na
vrzelih), ker surovih koordinat ni. Cela trasa gre samo živim vozilom: odgovor
se vleče na 10 s, trasa je do 40 kB. Izmerjeno 25. 9. 2026 na razvojnem
stroju, 9 vozil in 23 deljenj, nobeno živo: 10 kB (1,4 kB z gzipom), 4--19 ms;
ko je traso nosilo vseh devet, 60 kB (16 kB) in 15--44 ms.

Izid deljenja: `konec` iz baze, sicer `deli` (sveže točke) ali **`utihnil`**
-- brez konca in brez svežih točk, aplikacija zaprta ali brez signala.

## Android

`DeljenjeStoritev` je storitev v ospredju vrste `location`: lego dobiva
tudi z ugasnjenim zaslonom (preizkušeno na emulatorju: 8 točk v 40 s v
ozadju). Začne jo **stran** prek `Most.deliZacni()` — voznjo izbere stran,
storitev samo pošilja. Dvojno pošiljanje (stran in storitev) bi bilo dva
„potnika“ in lažno soglasje, zato stran v aplikaciji lege ne pošilja.
`zaganja` pokrije trenutek med klicem in zagonom storitve; brez njega je
prvo branje stanja deljenje razglasilo za končano.

**Emulator:** `adb emu geo fix` vrne „unknown command“, ker konzola zahteva
avtentikacijo (žeton v `~/.emulator_console_auth_token`). Lega gre prek
vtičnice na 5554 z `auth <žeton>`. Za varen kontekst v WebView
`adb reverse tcp:8001 tcp:8001` in naslov `http://127.0.0.1:8001`
(`-PkajrosUrl`, nato `pm clear`, ker je shranjen naslov močnejši).
