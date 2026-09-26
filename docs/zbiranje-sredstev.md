# Zbiranje sredstev za strežnik

Analiza, 2. 9. 2026. Vprašanje: kako narediti GoFundMe, da ga podprejo, koliko zbrati, ali gre anonimno.

## Kratek odgovor

**GoFundMe za Slovenijo ne dela.** Izplača v 20 držav — ZDA, Kanada, Mehika, Avstralija, VB, Irska, Francija, Nemčija, Avstrija, Belgija, Nizozemska, Luksemburg, Italija, Španija, Portugalska, Danska, Finska, Norveška, Švedska, Švica. Slovenije ni. Kakovost kampanje ni pomembna: ob izplačilu se ustavi.

Obvod, ki ga GoFundMe sam omenja („naj kampanjo odpre nekdo v podprti državi in ti nakaže“) = vzorec, ki ga platforme zamrznejo; denar in davčna obveznost preideta na tujo osebo. Ne.

**Anonimno tudi ne** — nikjer, kjer se pretaka denar. Izplačilo zahteva osebni dokument, naslov, bančni račun (protipranje denarja). GoFundMe: pravila preverjanja zahtevajo jasno, **kdo** je organizator, sicer kampanja ni preverjena. Najslabši izid: denar zberemo, zamrznejo ga.

Mogoča je **javna psevdonimnost**: platforma ve, kdo si, obiskovalec vidi ime projekta. Zna vsaka spodnja možnost.

## Koliko je res treba

Izmerjeno na naši bazi 2. 9. 2026, ne ocenjeno.

**Rast baze.** Dnevnik `obs` se poreže (železnica 90 dni, avtobusi 14), zato trajno raste samo `run` in vreme:

| | |
|---|---|
| `obs` na dan | 11 348 železniških + 1 516 293 avtobusnih vrstic |
| trajno raste | 16,8 MB/dan = **6,1 GB/leto** |
| `obs` v ustaljenem stanju | 1,8 GB |
| baza po 1 / 3 / 5 letih | 7,9 / 20,2 / 32,4 GB |

**40 GB diska zdrži pet let**, dokler `prune` teče. Brez avtobusov rast 0,2 GB/leto, disk ni vprašanje.

**Pomnilnik 57–89 MB RSS**, procesor praktično nič. Ne rabi velikega stroja; rabi stroj, ki je ves čas prižgan z javnim HTTPS.

**Cena** (Hetzner, cene po podražitvi junija 2026):

| postavka | mesečno | letno |
|---|---|---|
| CX23 (2 vCPU, 4 GB, 40 GB NVMe, 20 TB prometa) | 5,49 € | 65,88 € |
| IPv4 | 0,50 € | 6,00 € |
| DDV 22 % | 1,32 € | 15,81 € |
| **strežnik skupaj** | **7,31 €** | **87,7 €** |
| domena (.si ~12,5 € prvo leto, pozneje več) | | ~20 € |
| **skupaj** | **~9 €** | **~108 €** |

Varnostne kopije 0 €: malina doma = merodajen zajem, `potegni.sh` že obstaja — obrne se le smer.

Primerjava: malina doma ~7 € elektrike/leto. Za denar ne kupujemo zmogljivosti, ampak **javni naslov, HTTPS in zaprto domače omrežje**. To povedati tudi darovalcem.

**Predlagani znesek: 400 €.** = tri leta strežnika in domene (324 €) + ~10 % za provizije in rezervo za večji stroj ob prometu. Minimum, ki še kaj pomeni: 120 € (eno leto). Manjši, natančno utemeljen cilj je lažje doseči in bolj verjeten kot velik ohlapen — projekt ima za vsako številko meritev: prednost.

## Kje namesto GoFundMe

Vse spodnje izplačujejo v Slovenijo.

| | provizija | javno ime | oblika | opomba |
|---|---|---|---|---|
| **GitHub Sponsors** | 0 % | poljubna oznaka računa | mesečno ali enkratno | Slovenija na seznamu; rabi **javen repozitorij** |
| **Ko-fi** | 0 % na napitnine | poljubno ime strani | enkratno + mesečno | izplačilo prek Stripe/PayPal |
| **Buy Me a Coffee** | 5 % | poljubno ime strani | enkratno + mesečno | Slovenija podprta |
| **Liberapay** | 0 % | psevdonim | **samo** ponavljajoče | EU, odprtokoden, najbolj zaseben |
| **Open Collective Europe** | 10 % | popolnoma javna knjiga | sklad | denarja ne dobiš ti — račune plača gostitelj |

Dvoje premisliti:

* **GoFundMe = napačna oblika, tudi kjer dela.** Za enkraten cilj z rokom („zberimo za operacijo“). Strežnik = **ponavljajoč se strošek** — za to sta narejena GitHub Sponsors in Ko-fi, GoFundMe ne.
* **Open Collective Europe reši davčno in zaupno vprašanje naenkrat**: denarja nikoli ne dobiš na svoj račun, račun za strežnik plača gostitelj, vsak evro viden v javni knjigi. Cena 10 % in popolno nasprotje anonimnosti. Če je cilj „plačaj strežnik, ne mene“, najbolj pošten kanal.

Priporočilo: **GitHub Sponsors + Ko-fi**, oboje pod imenom projekta, ne osebnim. Skupaj 0 % provizije; prva za redne podpornike, druga za mimoidoče.

## Davek

Darilo v denarju od fizične osebe fizični osebi obdavčeno **šele nad 5 000 € od istega darovalca v 12 mesecih**; pod mejo ni davka ni napovedi. Drobni prispevki mnogih davka na darila ne sprožijo.

Dve opozorili: če je karkoli **v zameno** (naročnina, premium, oglas) = ni darilo, ampak dohodek, velja dohodnina. To je branje FURS-ovih strani, ne davčni nasvet — pred večjim zneskom vprašaj FURS ali računovodjo.

## Česar še ni, pa mora biti prej

Pomembnejše od izbire platforme.

1. **Aplikacija ni javno dosegljiva.** Teče na `192.168.1.164:8001` v domačem omrežju. Ni domene, HTTPS, javnega naslova. Nihče ne prispeva za nekaj, česar ne more odpreti — za to prositi prispevek.
2. **Koda ni objavljena, brez licence.** ~150 commitov samo lokalnih, licence ni izbrane = „vse pravice pridržane“. Prositi za denar za zaprto kodo je slabo — GitHub Sponsors javen repozitorij **zahteva**.
3. **Projekt nima imena.** `kajros` = delovno ime za vlake, ne pokriva avtobusov. Kampanja brez imena ne obstaja.
4. **Zgodovine 13 dni.** Čez dva ali tri mesece = arhiv, ki ga nima nihče drug; edini pravi argument za prispevek. Zdaj še ne.

Vrstni red: **ime → licenca → javen repozitorij → strežnik z domeno in HTTPS → šele nato gumb za prispevek.** Ne obratno.

Vmesna možnost brez stroška: [docs/javna-postavitev.md](javna-postavitev.md). Na kratko: **Oracle Free Tier odpade** — pravilo o pobiranju nedejavnih strojev zadene natanko naš primer (poraba 89 MB od 12 GB, procesor pri nič). Za prvi javni preizkus boljši Cloudflare Tunnel z maline: brez stroška, brez odprtih vrat.

## Viri

* [GoFundMe: Countries supported](https://support.gofundme.com/hc/en-us/articles/360001972748-Countries-supported-on-GoFundMe) in [seznam 20 držav](https://supportedcountries.com/gofundme/)
* [GoFundMe: pravila preverjanja](https://www.gofundme.com/c/safety/verification-guidelines)
* [Hetzner: prilagoditev cen junij 2026](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/)
* [GitHub Sponsors: dodatni pogoji (seznam držav)](https://docs.github.com/en/site-policy/github-terms/github-sponsors-additional-terms)
* [Buy Me a Coffee: podprte države za izplačila](https://help.buymeacoffee.com/en/articles/6258038-supported-countries-for-payouts-on-buy-me-a-coffee)
* [Open Collective Europe: pogoji in provizija](https://docs.opencollective.com/oceurope/faq/general-faqs)
* [FURS: prejel sem darilo](https://www.fu.gov.si/zivljenjski_dogodki_prebivalci/prejel_sem_darilo/)
