# Zbiranje sredstev za strežnik

Analiza, 2. 9. 2026. Vprašanje je bilo: kako narediti GoFundMe, da ga podprejo,
koliko bi bilo treba zbrati, in ali gre anonimno.

## Kratek odgovor

**GoFundMe za Slovenijo ne dela.** Denar lahko izplača v 20 držav — ZDA,
Kanada, Mehika, Avstralija, VB, Irska, Francija, Nemčija, Avstrija, Belgija,
Nizozemska, Luksemburg, Italija, Španija, Portugalska, Danska, Finska,
Norveška, Švedska, Švica. Slovenije med njimi ni. Ni pomembno, kako dobro je
kampanja napisana: ob izplačilu se ustavi.

Obvod, ki ga GoFundMe sam omenja („naj kampanjo odpre nekdo v podprti državi
in ti nakaže“), je natanko vzorec, ki ga platforme zamrznejo, poleg tega pa
denar in davčno obveznost preložiš na tujo osebo. Ne.

**Anonimno tudi ne** — ne pri GoFundMe ne nikjer drugje, kjer se pretaka denar.
Za izplačilo zahtevajo osebni dokument, naslov in bančni račun (protipranje
denarja). GoFundMe gre še dlje: v pravilih preverjanja piše, da mora biti
jasno, **kdo** je organizator, sicer kampanja ni preverjena. Najslabši možni
izid je, da denar zberemo in nam ga zamrznejo.

Kar je mogoče, je **javna psevdonimnost**: platforma ve, kdo si, obiskovalec
strani pa vidi ime projekta. To zna vsaka od spodnjih možnosti.

## Koliko je res treba

Izmerjeno na naši bazi 2. 9. 2026, ne ocenjeno.

**Rast baze.** Dnevnik `obs` se poreže (železnica 90 dni, avtobusi 14), zato
raste trajno samo `run` in vreme:

| | |
|---|---|
| `obs` na dan | 11 348 železniških + 1 516 293 avtobusnih vrstic |
| trajno raste | 16,8 MB/dan = **6,1 GB/leto** |
| `obs` v ustaljenem stanju | 1,8 GB |
| baza po 1 / 3 / 5 letih | 7,9 / 20,2 / 32,4 GB |

Torej: **40 GB diska zdrži pet let**, dokler `prune` teče. Brez avtobusov je
rast 0,2 GB/leto in vprašanja diska sploh ni.

**Poraba pomnilnika je 57–89 MB RSS**, procesorja praktično nič. Aplikacija ne
rabi velikega stroja; rabi stroj, ki je ves čas prižgan in ima javni HTTPS.

**Cena** (Hetzner, cene po podražitvi junija 2026):

| postavka | mesečno | letno |
|---|---|---|
| CX23 (2 vCPU, 4 GB, 40 GB NVMe, 20 TB prometa) | 5,49 € | 65,88 € |
| IPv4 | 0,50 € | 6,00 € |
| DDV 22 % | 1,32 € | 15,81 € |
| **strežnik skupaj** | **7,31 €** | **87,7 €** |
| domena (.si ~12,5 € prvo leto, pozneje več) | | ~20 € |
| **skupaj** | **~9 €** | **~108 €** |

Varnostne kopije so 0 €: malina doma je že merodajen zajem in `potegni.sh` že
obstaja — obrne se le smer.

Za primerjavo: malina doma stane ~7 € elektrike na leto. Za denar torej ne
kupujemo zmogljivosti, ampak **javni naslov, HTTPS in to, da domače omrežje
ostane zaprto**. To je pošteno povedati tudi darovalcem.

**Predlagani znesek: 400 €.** To je tri leta strežnika in domene (324 €) plus
~10 % za provizije in rezervo za večji stroj, če pride promet. Minimum, ki še
kaj pomeni, je 120 € (eno leto). Manjši, natančno utemeljen cilj je lažje
doseči in bolj verjeten kot velik in ohlapen — in ta projekt ima za vsako
številko meritev, kar je prednost, ne pomanjkljivost.

## Kje namesto GoFundMe

Vse spodnje izplačujejo v Slovenijo.

| | provizija | javno ime | oblika | opomba |
|---|---|---|---|---|
| **GitHub Sponsors** | 0 % | poljubna oznaka računa | mesečno ali enkratno | Slovenija je na seznamu; rabi **javen repozitorij** |
| **Ko-fi** | 0 % na napitnine | poljubno ime strani | enkratno + mesečno | izplačilo prek Stripe/PayPal |
| **Buy Me a Coffee** | 5 % | poljubno ime strani | enkratno + mesečno | Slovenija podprta |
| **Liberapay** | 0 % | psevdonim | **samo** ponavljajoče | EU, odprtokoden, najbolj zaseben |
| **Open Collective Europe** | 10 % | popolnoma javna knjiga | sklad | denarja ne dobiš ti — račune plača gostitelj |

Dvoje je vredno premisliti:

* **GoFundMe je napačna oblika, tudi kjer dela.** Narejen je za enkraten cilj
  z rokom („zberimo za operacijo“). Strežnik je **ponavljajoč se strošek** —
  za to sta GitHub Sponsors in Ko-fi narejena, GoFundMe pa ne.
* **Open Collective Europe reši davčno in zaupno vprašanje naenkrat**: denarja
  nikoli ne dobiš na svoj račun, račun za strežnik plača gostitelj, vsak evro
  je viden v javni knjigi. Cena je 10 % in popolno nasprotje anonimnosti.
  Če je cilj „plačaj strežnik, ne mene“, je to najbolj pošten kanal.

Priporočilo: **GitHub Sponsors + Ko-fi**, oboje pod imenom projekta, ne pod
osebnim. Skupaj 0 % provizije, ena za redne podpornike, druga za mimoidoče.

## Davek

Darilo v denarju od fizične osebe fizični osebi je obdavčeno **šele nad
5 000 € od istega darovalca v 12 mesecih**; pod to mejo ni ne davka ne
napovedi. Drobni prispevki mnogih ljudi torej ne sprožijo davka na darila.

Dve opozorili: če je za prispevek karkoli **v zameno** (naročnina, premium,
oglas), to ni darilo, ampak dohodek, in velja dohodnina. In to je branje
FURS-ovih lastnih strani, ne davčni nasvet — pred večjim zneskom vprašaj
FURS ali računovodjo.

## Česar še ni, pa mora biti prej

Ta del je pomembnejši od izbire platforme.

1. **Aplikacija ni javno dosegljiva.** Teče na `192.168.1.164:8001` v domačem
   omrežju. Ni domene, ni HTTPS, ni javnega naslova. Nihče ne bo prispeval za
   nekaj, česar ne more odpreti — in prav zaradi tega prispevka pravzaprav
   prosimo.
2. **Koda ni objavljena in nima licence.** ~150 commitov je samo lokalnih,
   licence ni izbrane, kar pomeni „vse pravice pridržane“. Prositi javnost za
   denar za zaprto kodo je slabo — in GitHub Sponsors javen repozitorij
   **zahteva**.
3. **Projekt nima imena.** `sztrack` je delovno ime za vlake in ne pokriva
   avtobusov. Kampanja brez imena ne obstaja.
4. **Zgodovine je 13 dni.** Čez dva ali tri mesece je to arhiv, ki ga nima
   nihče drug, in to je edini pravi argument za prispevek. Zdaj še ni.

Vrstni red je torej: **ime → licenca → javen repozitorij → strežnik z domeno
in HTTPS → šele nato gumb za prispevek.** Ne obratno.

Vmesna možnost, ki nič ne stane, je opisana v
[docs/javna-postavitev.md](javna-postavitev.md). Na kratko: **Oracle Free Tier
odpade** — njihovo pravilo o pobiranju nedejavnih strojev zadene natanko naš
primer (poraba 89 MB od 12 GB in procesor pri nič). Za prvi javni preizkus je
boljši Cloudflare Tunnel z maline, ki ne stane nič in ne odpre nobenih vrat.

## Viri

* [GoFundMe: Countries supported](https://support.gofundme.com/hc/en-us/articles/360001972748-Countries-supported-on-GoFundMe)
  in [seznam 20 držav](https://supportedcountries.com/gofundme/)
* [GoFundMe: pravila preverjanja](https://www.gofundme.com/c/safety/verification-guidelines)
* [Hetzner: prilagoditev cen junij 2026](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/)
* [GitHub Sponsors: dodatni pogoji (seznam držav)](https://docs.github.com/en/site-policy/github-terms/github-sponsors-additional-terms)
* [Buy Me a Coffee: podprte države za izplačila](https://help.buymeacoffee.com/en/articles/6258038-supported-countries-for-payouts-on-buy-me-a-coffee)
* [Open Collective Europe: pogoji in provizija](https://docs.opencollective.com/oceurope/faq/general-faqs)
* [FURS: prejel sem darilo](https://www.fu.gov.si/zivljenjski_dogodki_prebivalci/prejel_sem_darilo/)
