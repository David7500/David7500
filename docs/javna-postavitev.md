# Kako aplikacijo javno postaviti in kako varno

Analiza 2. 9. 2026, dopolnjena 4. 9. 2026. Vprašanje: kako varno je dati to na Oracle Free Tier.

**Odločeno kot priporoča analiza: Cloudflarov tunel.** Spremenil se le stroj — tunel teče s **prenosnika** `arwen` (192.168.1.46), ne z maline, ker prenosnik streže in je zmogljivejši; malina zajema naprej kot varovalo. Domena `kajros.app` registrirana 3. 9. 2026.

## Kaj sploh izpostavljamo

Izmerjeno na kodi in tekočem strežniku, ne po občutku:

* **Vseh 34 poti = `GET`. Zapisov ni nobenega** (`grep` po `@app.post|put|delete|patch` vrne 0). 24 `/api/*` + 10 strani; preverjeno znova 4. 9. 2026. Javni obiskovalec baze ne more spremeniti, samo bere.
* **Ni uporabniških računov, gesel ne osebnih podatkov.** Podatki tuji in že javni (CC BY-SA 4.0). Ni česa „ukrasti“.
* `CORS` = `allow_origins=["*"]`, a `allow_methods=["GET"]` in brez poverilnic — za odprtopodatkovni API pravilna nastavitev, ne luknja.
* Parametri imajo meje (`Query(..., ge=1, le=50)`), `gzip` vklopljen.

Opozorilo v `CLAUDE.md` („API nima avtentikacije in ga sme videti samo domače omrežje“) **ni o podatkih, ampak o omrežju**. Na javnem stroju velja: *na tem stroju ne sme biti ničesar, kar odpira dom.*

## Kaj lahko gre narobe, po vrsti

1. **Stroj kdo prevzame** (SSH, nezakrpana storitev) in ga zlorabi. Edino resno tveganje, ni specifično za nas.
2. **Bot tolče po največjem odgovoru.** Izmerjeno: `/api/stations` 863 kB, stisnjen 217 kB, postrežen v 0,07 s. Pri 10 zahtevah/s = 5,6 TB/mesec — še znotraj brezplačnih 10 TB, a stroj neuporaben. Rešitev: predpomnjenje (seznam postaj se spremeni enkrat na dan) + omejitev hitrosti v Caddyju, ne avtentikacija.
3. **Ponudnik stroj vzame.** Pri Oraclu ni hipotetično — glej spodaj.

## Oracle Free Tier: brezplačno, a nas bo pobralo

| | |
|---|---|
| ARM A1 | **2 OCPU / 12 GB** (v 2026 znižano s 4/24) |
| disk | 200 GB skupaj (zagonski + podatkovni) |
| promet navzven | 10 TB/mesec |
| račun | **brez nadgradnje na Pay As You Go te ne morejo zaračunati** |

Zadnja vrstica = najboljša varovalka: dokler računa ne nadgradiš, je strošek trdo nič — ne opozorilo, zid.

**Težava: pobiranje nedejavnih strojev.** Oracle stroj vzame, če 7 dni velja vse troje: 95. percentil procesorja pod 20 %, omrežje pod 20 % in (pri A1) pomnilnik pod 20 %. Aplikacija porabi **89 MB od 12 GB (0,7 %)**, procesorja praktično nič — zadenemo vse tri pogoje naenkrat. Nismo mejni primer, smo šolski primer stroja, ki ga poberejo.

Izhod: nadgradnja na Pay As You Go odpravi pobiranje — a odpreš vrata računu, torej zavržeš edino, zaradi česar je Oracle privlačen.

**Sklep: Oracle Free Tier ni primeren.** Ne ker bi bil nevaren, ampak ker ga bomo izgubili, tiho.

## Kaj namesto tega

| | cena | dom izpostavljen? | zdrži? |
|---|---|---|---|
| **Cloudflare Tunnel z domačega stroja** | 0 € | delno (aplikacija da, omrežje ne) | da |
| **Hetzner CX23** | ~7 €/mesec | ne | da |
| Oracle Free | 0 € | ne | **ne** |

**Za prvi javni preizkus: Cloudflare Tunnel z domačega stroja** (odločeno; teče s prenosnika, ne z maline). Na usmerjevalniku ne odpre nobenih vrat — povezava gre od strežnega stroja navzven — javni naslov dobi HTTPS in Cloudflarovo zaščito pred navalom; novega stroja ni treba vzdrževati. Ostane tveganje: hrošč v aplikaciji = opora v domačem omrežju. Vsi endpointi brati-samo, brez zapisov → majhno, ni pa nič.

**Ko bo kdo prišel: Hetzner.** Ločen stroj, doma ne izpostavi ničesar, nihče ga ne pobere. Sedem evrov/mesec = natanko to, za kar bi zbirala denar.

## Cloudflare Tunnel: kaj to je

**Obrnjena smer.** Preusmeritev vrat na usmerjevalniku prebije luknjo navznoter: svetu poveš naslov in čakaš, kdo potrka. Tunel obratno — na strežnem stroju teče majhen program (`cloudflared`), ki **sam pokliče ven** k Cloudflaru in drži povezavo odprto. Obiskovalec pride do Cloudflara, ta ga spusti po že odprti povezavi.

Posledica: na usmerjevalniku ni odprtih vrat, malina nima javnega naslova, domači IP nikjer viden. Ni luknja v zidu, ampak telefonska linija, ki jo hiša vzpostavi sama.

```
obiskovalec → Cloudflare ⇠(povezava, ki jo vzpostavi malina)⇢ cloudflared → 127.0.0.1:8000
```

**Zraven, brezplačno:**

* **HTTPS s pravim potrdilom**, samodejno. Reši tudi napako iz `CLAUDE.md`: `navigator.geolocation` zahteva varen kontekst, zato lastna lega prek `http://192.168.1.164:8001` ne dela. S tunelom dela.
* Cloudflare spredaj: zaščita pred navalom, predpomnjenje, pravila za omejitev hitrosti — natanko to, kar rabimo za `/api/stations`.
* Prometne omejitve ni, tuneli ne potečejo.
* **Cloudflare Access** (Zero Trust, brezplačno do 50 uporabnikov) zna predenj postaviti prijavo. Odgovor na „API nima avtentikacije“ brez vrstice kode: za zaprt preizkus spustiš noter samo povabljene naslove.

**Dve različici, razlika pomembna:**

| | hitri tunel (TryCloudflare) | imenovani tunel |
|---|---|---|
| ukaz | `cloudflared tunnel --url http://localhost:8001` | nastavitev + systemd |
| račun | ni ga | Cloudflare račun |
| domena | ni je | **potrebna**, z DNS pri Cloudflaru |
| naslov | naključen `*.trycloudflare.com` | naš, stalen |
| omejitve | 200 sočasnih zahtev (nato 429), brez SSE, brez SLA | ni jih |
| ob ustavitvi | **naslov izgine** | ostane |

Hitri tunel = „pokaži mi zdaj“, v eni minuti in brez računa. Za naslov, ki ga daš ljudem, ne pride v poštev. Imenovani tunel rabi domeno, torej ~20 €/leto iz proračuna; Cloudflare in DNS pri njem brezplačna.

**Kje se nastavi:**

* **Hitri tunel nima strani.** Naslov izpiše `cloudflared` v terminal — `https://<naključne-besede>.trycloudflare.com`. Ne izbereš ga; ob ustavitvi procesa konec.
* **Imenovani tunel: `dash.cloudflare.com`.** Tam narediš račun in dodaš domeno (pri registrarju nato preusmeriš imenske strežnike na Cloudflare). Tuneli in Access pod `dash.cloudflare.com/one/` — stari naslov `one.dash.cloudflare.com` se zdaj preusmeri tja.
* Na strežnem stroju `cloudflared tunnel login` izpiše povezavo, ki jo odpreš v brskalniku **na drugem računalniku** (malina brez zaslona); potrdilo shrani v `~/.cloudflared/cert.pem`.
* Naslov je **naš**, ne Cloudflarov: izbereš poddomeno svoje domene, Cloudflare zanjo naredi `CNAME` na `<uuid>.cfargotunnel.com`.

**Ta past je z odločitvijo odpadla — a ostane zapisana**, ker se vrne, ko bi kdo hotel tunel pognati z maline. Strežni stroj = `arwen`, x86_64, `cloudflared` deluje iz uradnega paketa brez posebnosti.

**Past pri malini — izmerjeno 2. 9. 2026.** Malina = **Raspberry Pi Zero W**: eno jedro `armv6l`, 427 MB pomnilnika, Raspbian 13, `armhf`. Uradni paket `armhf` preveden z `GOARM=7`, na ARMv6 pade z *Illegal instruction* — znan hrošč `cloudflared`, ne naša napaka. Deluje binarna datoteka **`cloudflared-linux-arm`**:

```bash
curl -sL -o /tmp/cfd \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm
chmod +x /tmp/cfd && /tmp/cfd --version    # cloudflared version 2026.8.3, izhod 0
```

Torej: **ne** `apt install cloudflared` in **ne** paket `armhf`, ampak ta binarna datoteka. Preizkušeno na sami malini, ne prebrano.

**Česar tunel ne naredi:**

* **Aplikacije ne naredi varne** — naredi jo javno, kar je namen. Vsi endpointi brati-samo, zato sprejemljivo, a hrošč v aplikaciji je odslej dosegljiv z interneta, aplikacija pa teče doma.
* **Cloudflare vidi ves promet** (pri njem se konča TLS). Za odprte prometne podatke ni težava, treba pa vedeti.

## Koliko uporabnikov zmore stroj

**Razdelek nastal, ko je bila malina kandidatka za strežnik.** Odločeno drugače — streže prenosnik `arwen` (x86_64, 7,8 GB), pri istem poslu enakega reda kot razvojni računalnik. Številke niso več omejitev, ampak razlog, **zakaj malina ne streže**.

Izmerjeno 2. 9. 2026. Isti posel (SQLite v pomnilniku, 200 000 vrstic, 20 agregatov) na obeh strojih:

| | pisanje + indeks | 20× agregat |
|---|---|---|
| ta računalnik (Core Ultra 7 255U) | 0,12 s | 0,90 s |
| malina (Pi Zero W, armv6) | 29,36 s | 88,68 s |

**Pi Zero W ~100× počasnejši** od tega računalnika. Pi 4B po enem jedru ~10× hitrejši od Zeroja (A72 1,5 GHz proti ARM11 1 GHz) → **~10× počasnejši od tega računalnika**. Odzivi, tu izmerjeni topli (mediana 10 zahtev):

Odzivi, izmerjeni **4. 9. 2026 po popravkih hitrosti**, precej nižji od tistih, na katerih so spodnje ocene zgrajene: `/api/live` 5 ms namesto 253, `/api/health` 80 ms namesto 1223. Ocene za Pi sorazmerno padejo, sklep ostane isti.

| pot | tu (2. 9.) | ocena Pi 4B |
|---|---|---|
| `/api/live` | 253 ms | **~2,5 s** |
| `/api/overview` | 224 ms | ~2,2 s |
| `/api/stations` | 77 ms | ~0,8 s |
| `/api/departures` | 53 ms | ~0,5 s |
| `/api/connections` | 17 ms | ~0,2 s |

Vseh 32 endpointov = `def`, ne `async def` — Starlette jih požene v nitih, SQLite med poizvedbo spusti GIL, zato štiri jedra res štejejo.

**Zgornja meja brez predpomnjenja.** Zemljevid poizve `/api/live` vsakih 30 s: 2,5 s procesorja na uporabnika na 30 s = 8 % enega jedra. S tremi prostimi jedri ~35 hkratnih uporabnikov po prepustnosti, a čakalna vrsta odziv pokvari prej: **pri ~10–15 hkratnih na zemljevidu** gre `/api/live` čez pet sekund. Iskalnik povezav desetkrat cenejši, zdrži ~100 hkratnih. V jutranji konici 10–15 hkratnih ≈ **200–400 uporabnikov na dan**.

**S predpomnjenjem meja skoraj izgine.** `/api/live` se spremeni vsakih 10–30 s, `/api/stations` enkrat na dan; odgovor izračunan enkrat in postrežen vsem → tisoč uporabnikov stane kot eden. Predpomnilnika odgovorov zdaj **ni** (`grep lru_cache|Cache-Control` po `api.py` najde samo statične datoteke). Najcenejša izboljšava; narediti pred objavo, ne po njej.

**SD kartica večja težava od procesorja.** Baza čez leto ~8 GB, več od 4 GB pomnilnika — od tam naključna branja na kartico, 10–40× počasnejšo od NVMe, faktor 10 se slabša. Poleg tega v `obs` ~1,5 M vrstic na dan; ceneno kartico to pobije. **Zaganjaj z USB SSD, ne s kartice** — ~25 €, odpade največje tveganje.

## Varnostni recept za javni stroj

Velja za Hetzner enako kot za Oracle.

* **Stroj ne sme znati domov.** Nobenega SSH ključa, ki odpre malino, nobenega VPN-a v domače omrežje. Smer: dom → strežnik (malina potisne), ali strežnik zajema sam z NAP-a. Izguba stroja = nič izgubljenega: arhiv je doma.
* **Aplikacija posluša na `127.0.0.1`**, spredaj Caddy za HTTPS (samodejni Let's Encrypt) in omejitev hitrosti.
* **Odprta samo 80 in 443.** SSH prek Tailscala ali omejen na svoj IP. *Past pri Oraclu:* poleg oblačnega požarnega zidu ima slika Ubuntuja **še svoja `iptables` pravila** — dva zidova, oba odpreti; natanko tu ljudje izgubijo popoldne.
* **SSH samo s ključem**, brez gesel, brez `root`; `unattended-upgrades` in `fail2ban`.
* **Systemd okrepi enoto**: `NoNewPrivileges`, `ProtectSystem=strict`, `PrivateTmp`, `ReadWritePaths` samo na podatkovni imenik, lasten uporabnik.
* **Predpomni velike odgovore.** `/api/stations` in `/api/network.geojson` se spremenita enkrat na dan; brez tega najcenejši način, da nas kdo upočasni.

## Viri

* [Oracle: Always Free Resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm) (omejitve in merila za pobiranje nedejavnih strojev)
* [Oracle: FAQ o brezplačnem nivoju](https://www.oracle.com/cloud/free/faq/) (brez nadgradnje ni zaračunavanja)
* [Cloudflare Tunnel: kako deluje](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/)
* [Cloudflare: hitri tuneli in njihove omejitve](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/)
