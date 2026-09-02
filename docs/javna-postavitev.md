# Kako aplikacijo javno postaviti in kako varno

Analiza, 2. 9. 2026. Vprašanje: kako varno je dati to na Oracle Free Tier.

## Kaj sploh izpostavljamo

Izmerjeno na kodi in na tekočem strežniku, ne po občutku:

* **Vseh 32 endpointov je `GET`. Zapisov ni nobenega** (`grep` po
  `@app.post|put|delete|patch` vrne 0). Javni obiskovalec baze ne more
  spremeniti — lahko jo samo bere.
* **Ni uporabniških računov, gesel ne osebnih podatkov.** Podatki so tuji in
  že javni (CC BY-SA 4.0). Ni česa „ukrasti“.
* `CORS` je `allow_origins=["*"]`, a `allow_methods=["GET"]` in brez
  poverilnic — za odprtopodatkovni API je to pravilna nastavitev, ne luknja.
* Parametri imajo meje (`Query(..., ge=1, le=50)`), `gzip` je vklopljen.

Opozorilo v `CLAUDE.md` („API nima avtentikacije in ga sme videti samo domače
omrežje“) torej **ni o podatkih, ampak o omrežju**. Na javnem stroju velja v
drugačni obliki: *na tem stroju ne sme biti ničesar, kar odpira dom.*

## Kaj lahko gre narobe, po vrsti

1. **Stroj kdo prevzame** (SSH, nezakrpana storitev) in ga uporabi za zlorabo.
   To je edino resno tveganje in ni specifično za nas.
2. **Bot tolče po največjem odgovoru.** Izmerjeno: `/api/stations` je 863 kB,
   stisnjen 217 kB, in se postreže v 0,07 s. Pri 10 zahtevah na sekundo je to
   5,6 TB na mesec — še znotraj brezplačnih 10 TB, a stroj je neuporaben.
   Rešitev je predpomnjenje (seznam postaj se spremeni enkrat na dan) in
   omejitev hitrosti v Caddyju, ne avtentikacija.
3. **Ponudnik stroj vzame.** Pri Oraclu to ni hipotetično — glej spodaj.

## Oracle Free Tier: brezplačno, a nas bo pobralo

| | |
|---|---|
| ARM A1 | **2 OCPU / 12 GB** (v 2026 znižano s 4/24) |
| disk | 200 GB skupaj (zagonski + podatkovni) |
| promet navzven | 10 TB/mesec |
| račun | **brez nadgradnje na Pay As You Go te ne morejo zaračunati** |

Zadnja vrstica je najboljša varovalka, kar jih je: dokler računa ne nadgradiš,
je strošek trdo nič — ne opozorilo, ampak zid.

**Težava je pobiranje nedejavnih strojev.** Oracle stroj vzame, če v sedmih
dneh velja vse troje: 95. percentil procesorja pod 20 %, omrežje pod 20 % in
(pri A1) pomnilnik pod 20 %. Naša aplikacija porabi **89 MB od 12 GB (0,7 %)**
in procesorja praktično nič — zadenemo vse tri pogoje naenkrat. Nismo mejni
primer, smo šolski primer stroja, ki ga poberejo.

Izhod je nadgradnja na Pay As You Go, ki pobiranje odpravi — a s tem odpreš
tudi vrata računu, torej zavržeš edino stvar, zaradi katere je Oracle privlačen.

**Sklep: Oracle Free Tier ni primeren.** Ne zato, ker bi bil nevaren, ampak
ker ga bomo izgubili, in to tiho.

## Kaj namesto tega

| | cena | dom izpostavljen? | zdrži? |
|---|---|---|---|
| **Cloudflare Tunnel z maline** | 0 € | delno (aplikacija da, omrežje ne) | da |
| **Hetzner CX23** | ~7 €/mesec | ne | da |
| Oracle Free | 0 € | ne | **ne** |

**Za prvi javni preizkus: Cloudflare Tunnel z maline.** Na usmerjevalniku ne
odpre nobenih vrat — povezava gre od maline navzven — javni naslov dobi HTTPS
in Cloudflarovo zaščito pred navalom, novega stroja pa ni treba vzdrževati.
Tveganje, ki ostane: če ima aplikacija hrošča, je to opora v domačem omrežju.
Ker so vsi endpointi brati-samo in ni zapisov, je to majhno, ni pa nič.

**Ko bo kdo prišel: Hetzner.** Ločen stroj, doma ne izpostavi ničesar in ga
nihče ne pobere. Sedem evrov na mesec je natanko to, za kar bi zbirala denar.

## Cloudflare Tunnel: kaj to je

**Obrnjena smer.** Preusmeritev vrat na usmerjevalniku prebije luknjo navznoter:
svetu poveš svoj naslov in čakaš, kdo potrka. Tunel dela nasprotno — na malini
teče majhen program (`cloudflared`), ki **sam pokliče ven** k Cloudflaru in to
povezavo drži odprto. Obiskovalec pride do Cloudflara, Cloudflare pa ga spusti
po tisti že odprti povezavi do maline.

Posledica: na usmerjevalniku ni odprtih vrat, malina nima javnega naslova in
domači IP ni nikjer viden. Ni luknja v zidu, ampak telefonska linija, ki jo
hiša vzpostavi sama.

```
obiskovalec → Cloudflare ⇠(povezava, ki jo vzpostavi malina)⇢ cloudflared → 127.0.0.1:8001
```

**Kaj dobimo zraven, brezplačno:**

* **HTTPS s pravim potrdilom**, samodejno. To reši tudi napako, ki je zapisana
  v `CLAUDE.md`: `navigator.geolocation` zahteva varen kontekst, zato lastna
  lega prek `http://192.168.1.164:8001` ne dela. S tunelom dela.
* Cloudflare spredaj: zaščita pred navalom, predpomnjenje, pravila za omejitev
  hitrosti — natanko to, kar rabimo za `/api/stations`.
* Prometne omejitve ni in tuneli ne potečejo.
* **Cloudflare Access** (Zero Trust, brezplačno do 50 uporabnikov) zna predenj
  postaviti prijavo. To je odgovor na „API nima avtentikacije“ brez vrstice
  kode: za zaprt preizkus spustiš noter samo povabljene naslove.

**Dve različici, in razlika je pomembna:**

| | hitri tunel (TryCloudflare) | imenovani tunel |
|---|---|---|
| ukaz | `cloudflared tunnel --url http://localhost:8001` | nastavitev + systemd |
| račun | ni ga | Cloudflare račun |
| domena | ni je | **potrebna**, z DNS pri Cloudflaru |
| naslov | naključen `*.trycloudflare.com` | naš, stalen |
| omejitve | 200 sočasnih zahtev (nato 429), brez SSE, brez SLA | ni jih |
| ob ustavitvi | **naslov izgine** | ostane |

Hitri tunel je za „pokaži mi zdaj“ — v eni minuti in brez računa. Za naslov,
ki ga daš ljudem, ne pride v poštev. Imenovani tunel rabi domeno, torej tistih
~20 € na leto iz proračuna; sam Cloudflare in DNS pri njem sta brezplačna.

**Česar tunel ne naredi:**

* **Aplikacije ne naredi varne** — naredi jo javno, kar je ravno namen. Vsi
  endpointi so brati-samo, zato je to sprejemljivo, a hrošč v aplikaciji je
  odslej dosegljiv z interneta, in aplikacija teče doma.
* **Cloudflare vidi ves promet** (pri njem se konča TLS). Za odprte prometne
  podatke to ni težava, je pa treba vedeti.

## Varnostni recept za javni stroj

Velja za Hetzner enako kot za Oracle.

* **Stroj ne sme znati domov.** Nobenega SSH ključa, ki odpre malino, nobenega
  VPN-a v domače omrežje. Smer je dom → strežnik (malina potisne), ali pa
  strežnik zajema sam z NAP-a. Če stroj izgubimo, ne izgubimo ničesar: arhiv
  je doma.
* **Aplikacija posluša na `127.0.0.1`**, spredaj Caddy za HTTPS (samodejni
  Let's Encrypt) in omejitev hitrosti.
* **Odprta samo 80 in 443.** SSH prek Tailscala ali omejen na svoj IP.
  *Past pri Oraclu:* poleg oblačnega požarnega zidu ima njihova slika Ubuntuja
  **še svoja `iptables` pravila** — dva zidova, oba je treba odpreti, in
  natanko na tem ljudje izgubijo popoldne.
* **SSH samo s ključem**, brez gesel, brez `root`; `unattended-upgrades` in
  `fail2ban`.
* **Systemd okrepi enoto**: `NoNewPrivileges`, `ProtectSystem=strict`,
  `PrivateTmp`, `ReadWritePaths` samo na podatkovni imenik, lasten uporabnik.
* **Predpomni velike odgovore.** `/api/stations` in `/api/network.geojson` se
  spremenita enkrat na dan; brez tega je to najcenejši način, da nas kdo
  upočasni.

## Viri

* [Oracle: Always Free Resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
  (omejitve in merila za pobiranje nedejavnih strojev)
* [Oracle: FAQ o brezplačnem nivoju](https://www.oracle.com/cloud/free/faq/) (brez nadgradnje ni zaračunavanja)
* [Cloudflare Tunnel: kako deluje](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/)
* [Cloudflare: hitri tuneli in njihove omejitve](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/)
