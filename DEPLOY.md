# Objava

**Postavitev od 4. 9. 2026 trojna**, vsak stroj svoja naloga:

| stroj | naslov | naloga |
|---|---|---|
| prenosnik `arwen` | `192.168.1.46` | **streže** `kajros.app`, zajema sam |
| malina (Pi Zero W) | `192.168.1.166` | zajem, teče ves čas, **varovalo** |
| ta računalnik | — | razvoj |

Zakaj oboje zajema: prikaz mora biti živ, poteg pa star toliko kot zadnji poteg. Ko prenosnik nekaj časa ne teče, vrzel zapolni `deploy/zapolni-vrzel.sh` (bere z maline, nikoli ne piše nanjo). Malina ostane prižgana: prenosnik se zapira in seli, ona ne.

**Posodobitev prenosnika = `git push arwen`** (od 17. 9. 2026). Potisk posodobi delovno drevo v `~/kajros`, kavelj `post-receive` požene `deploy/posodobi.sh`, ta prepiše kodo v `/opt/kajros`, znova zažene in počaka na `/api/health`. Izpis pride nazaj na razvojni računalnik → neuspela objava vidna tam, kjer si jo sprožil. **Gesla ne rabi**: restart = eden od štirih ukazov z `NOPASSWD`, nastavi jih `deploy/brez-sudo.sh`.

Enkratna nastavitev: `deploy/arwen-git.sh` (po cevi: `ssh david@192.168.1.46 'bash -s' < deploy/arwen-git.sh`) in na razvojnem računalniku `git remote add arwen david@192.168.1.46:kajros`.

Prej kodo prinašal `rsync`, **mimo gita**: delovno drevo na strežniku novejše od svojega HEAD, katera različica teče, ugotovljivo le po datotekah. `posodobi.sh` še vedno mogoče pognati ročno (`~/kajros/deploy/posodobi.sh ~/kajros`), rabiš za ponovno namestitev istega commita.

Starejši `~/posodobi.sh` **odstranjen 12. 9. 2026**: posodabljal prek `install-rpi.sh`, zato zahteval sudo geslo, ki ga v seji brez terminala ni mogoče vpisati. Podrobnosti in past z `/tmp` na malini: `.claude/rules/objava.md`.

Spodaj namestitev na Raspberry Pi; za majhne gostitelje, ki sprejmejo zip, velja poglavje »Paket za gostitelja« naprej.

## Raspberry Pi

> ### Enkratno: prva namestitev po preimenovanju v Kajros
>
> Malina teče staro kodo pod imenom `sztrack`, dokler tega
> ne pogeneš. Zajem medtem **ne trpi** — `potegni.sh` staro pot sam najde.
>
> Vir že prenesen v `~/kajros-src` (3. 9. 2026). Manjka samo korak s sudom:
>
> ```bash
> ssh david@192.168.1.166
> sudo KAJROS_MODE=zajem KAJROS_SRC=/home/david/kajros-src \
>      KAJROS_AGENCIES=1118,1119,1121,1123 \
>      bash /home/david/kajros-src/deploy/install-rpi.sh
> ```
>
> Enota ima **`KAJROS_OCENA=0`**: senčno merjenje teče v isti zanki kot zajem
> in bi na Pi Zero W vzelo ~14 s vsakih 120 (izmerjeno), kar bi zamaknilo
> zajem. Malina ima eno nalogo.
>
> Naredi: preseli `/var/lib/sztrack/sz.sqlite` (z `-wal` in `-shm`) v
> `/var/lib/kajros/kajros.sqlite`, ugasne in onemogoči `sztrack-zajem`,
> postavi `kajros-zajem`. Selitev preizkušena v peskovniku, na sami malini
> **ne** — zato po zagonu preveri:
>
> ```bash
> systemctl is-active kajros-zajem          # active
> sqlite3 /var/lib/kajros/kajros.sqlite 'SELECT COUNT(*) FROM run'
> ```
>
> Če se kaj zalomi: stara baza ni izbrisana, ampak premaknjena — nazaj z
> `mv /var/lib/kajros/kajros.sqlite /var/lib/sztrack/sz.sqlite` in
> `systemctl enable --now sztrack-zajem`.
>
> Ta odstavek odstrani, ko bo opravljeno.


Pi boljši od brezplačnih gostiteljev iz enega razloga: zajem mora teči **neprekinjeno**, ker zgodovine zamud ni mogoče dobiti za nazaj. Brezplačni paketi zaspijo, zavržejo disk ali zahtevajo ročno podaljševanje. Pi nič od tega.

### Namestitev

```bash
sudo bash deploy/install-rpi.sh
```

Skripta idempotentna — za posodobitev poženeš znova. Naredi:

* sistemskega uporabnika `kajros` brez lupine,
* kodo v `/opt/kajros`, podatke v `/var/lib/kajros`,
* virtualno okolje in odvisnosti,
* priloženo bazo voznega reda, **če je še ni** (obstoječe nikoli ne povozi),
* storitev `kajros.service` in dnevno varnostno kopijo `kajros-backup.timer`.

Po namestitvi:

```bash
curl -s http://localhost:8000/api/health
journalctl -u kajros -f
```

Iz domačega omrežja dosegljiv na `http://<ip-pija>:8000/docs`.

### Kaj je na Pi drugače

**Vozni red se osvežuje sam.** V `kajros.service` `KAJROS_REFRESH=subprocess` — uvoz teče v podprocesu, ki po koncu ves pomnilnik vrne sistemu (vrh 54 MB). Na Pelli izklopljeno zaradi 100 MB omejitve.

**Ura mora biti točna.** Obratovalni dan vožnje se ugotavlja z ujemanjem voznorednega okna s trenutnim časom → `systemd-timesyncd` naj teče. Časovni pas sistema ni pomemben — koda povsod uporablja `Europe/Ljubljana`.

**Zapisovanje majhno.** Piše se samo ob spremembi zamude, nekaj tisoč vrstic na dan; za SD kartico zanemarljivo. USB SSD je vseeno boljše mesto — nastavi `KAJROS_DATA_DIR` nanj v enoti storitve.

**Varnostne kopije** vsak dan ob 3:30 v `/var/lib/kajros/backup/` prek `sqlite3 .backup` (konsistentno tudi med pisanjem), stisnjene z `gzip -1` (~3,1× manjše, merjeno). Hranijo se **tri**, ne štirinajst: z vsemi prevozniki baza zraste ~3,4 GB na leto, štirinajst polnih kopij bi zapolnilo kartico. Če bi po kopiji ostalo manj kot 2 GB prostega, se preskoči in zapiše v dnevnik — polna kartica ustavi tudi zajem, kopija le kratkoročna varovalka.

**Dolgoročni arhiv = računalnik**, ki bazo potegne dol (`kajros merge`), ne Pi. Kartice odpovedo.

## Samo zajem, brez strežnika

Kadar naj stroj le polni bazo — da lahko računalnik ugasneš — se namesti `kajros-zajem.service` namesto strežnika:

```bash
sudo KAJROS_MODE=zajem KAJROS_AGENCIES=1118,1123,1119,1121 bash deploy/install-rpi.sh
```

Zajema se **samo tisto, česar kasneje ni mogoče dobiti**: zamude in obvestila. Vreme ima arhiv za nazaj, statistika je izpeljanka `run` — oboje se izračuna tam, kjer je baza. Lege vozil ni: je samo "zdaj", ne hrani se.

`KAJROS_AGENCIES` se zapiše v enoto, ob spremembi sproži ponovni uvoz voznega reda (`--force`; brez tega bi ETag rekel "nespremenjeno"). Uvoz **zamenja samo statične tabele** — `obs` in `run` ostaneta.

### Prenos zajema s prejšnjega gostitelja

Zajeto drugje se ne sme izgubiti. Prenesi staro `kajros.sqlite` in jo prilij:

```bash
sudo -u kajros /opt/kajros/.venv/bin/python -m kajros.cli merge ~/sz-pella.sqlite
```

```json
{"source_observations": 271, "observations_added": 271,
 "runs_touched": 222, "observations_total": 727, "days_covered": 2}
```

Varno tudi, če sta bazi nekaj časa tekli vzporedno: meritve ključene po `(trip_id, service_date, stop_seq, feed_ts)`, podvojene se tiho zavržejo, v `run` obvelja zapis z novejšim `feed_ts`. Ponovni zagon istega ukaza doda 0 vrstic.

### Dostop od zunaj

Za zajem ni potreben — Pi sam kliče ven. Ko bo frontend rabil API z interneta, najmanj dela s Tailscalom (zasebno omrežje, brez odpiranja vrat) ali Cloudflare Tunnelom (javno, samodejni HTTPS, brez javnega IP-ja). Vrat na usmerjevalniku ne odpiraj — API nima avtentikacije.

## Paket za gostitelja

En proces streže API in hkrati zajema zamude — ločenega delavca ni. Zajem teče v ozadnji niti, ki jo FastAPI zažene ob zagonu.

### Vsebina paketa

```
main.py            vstopna točka: uvicorn na $PORT
requirements.txt   fastapi, uvicorn, requests, gtfs-realtime-bindings
Procfile           web: python main.py
kajros/           koda
seed/kajros.sqlite     pripravljen vozni red (1,7 MB) za takojšen zagon
```

### Zagon

Delujeta oba načina — kar koli gostitelj že uporablja:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT   # gostitelj vodi strežnik (Pella)
python main.py                                 # strežnik zaženemo sami
```

`app` zato izpostavljen na ravni modula `main`. Če gostitelj javi `Error loading ASGI app. Attribute "app" not found in module "main"`, poganja prvo obliko — zato je `app` tam.

Pri drugi obliki se vrata preberejo iz `PORT`; če ga ni, 8000.

### Nastavitve prek okolja

| Spremenljivka | Privzeto | Kaj počne |
|---|---|---|
| `PORT` | 8000 | vrata |
| `KAJROS_DATA_DIR` | `data` | kam gre baza (naj bo na trajnem disku) |
| `KAJROS_POLL_SECONDS` | 30 | razmik med zajemi |
| `KAJROS_COLLECTOR` | 1 | `0` izklopi zajem (samo API) |
| `KAJROS_REFRESH` | `off` | osveževanje voznega reda: `off`, `inprocess`, `subprocess` |
| `KAJROS_REFRESH_HOUR` | 4 | ura osvežitve, kadar ni `off` |
| `KAJROS_WEATHER` | 1 | `0` izklopi dnevno dopolnjevanje vremena |
| `KAJROS_WEATHER_HOUR` | 5 | ura, ob kateri se vreme dopolni za zadnje 3 dni |

### Kaj se zgodi ob prvem zagonu

Baze ni → kopira se `seed/kajros.sqlite` — zagon takojšen. Seeda tudi ni → vozni red prenese sam (41 MB, uvoz ~23 s pri polnem jedru; na 0,1 jedra nekaj minut), zip nato pobriše.

**Obstoječa baza se nikoli ne povozi.** Ponovna objava paketa ne izbriše zajete zgodovine — dokler je `KAJROS_DATA_DIR` na disku, ki preživi objavo.

### Poraba

Merjeno na tem paketu:

| | |
|---|---|
| RSS ob zagonu (s priloženo bazo) | **60 MB** |
| RSS po prvem zajemu | **74 MB** |
| Uvoz GTFS (vrh) | **54 MB**, 23 s |
| Baza po uvozu | 1,7 MB |
| Promet | 250 KB / 30 s + 41 MB enkrat na dan |

Pri 100 MB pomnilnika ~25 MB rezerve. Če zmanjka: prvi korak `KAJROS_POLL_SECONDS=60` + izogib `/api/network.geojson` v vroči zanki (odgovor ~1 MB — raje postavi kot statično datoteko prek `kajros export`).

### Zakaj je osveževanje voznega reda privzeto izklopljeno

Uvoz GTFS = najdražji trenutek v življenju procesa. Izmerjeno na tem paketu:

| način | vrh pomnilnika | opomba |
|---|---|---|
| `inprocess` | **89 MB** | ostane pri 85 MB — Python aren skoraj ne vrne sistemu |
| `subprocess` | 54 MB v otroku **poleg 57 MB starša** = ~111 MB skupaj | oboje hkrati rezidentno |
| `off` | — | privzeto |

Pri 100 MB nobena od obeh ni varna: ob osvežitvi lahko OOM, vsak dan ob isti uri. Zato privzeto `off`.

Vozni red osvežiš: drugje poženi `kajros update`, novo `kajros.sqlite` daj v `seed/`, objavi paket — obstoječa baza se ne povozi, ker se seed uporabi le, kadar baze še ni. (Zato staro bazo enkrat odstrani oz. preimenuj.) Vsebinsko se vozni red spremeni nekajkrat na leto.

Na stroju z več pomnilnika nastavi `KAJROS_REFRESH=subprocess`.

### Preverjanje, da zajem res teče

```
GET /api/health
```

```json
{"trips": 723, "stations": 267, "observations": 271,
 "runs_recorded": 271, "days_covered": 1,
 "db_bytes": 1708032, "last_feed_at": "2026-08-19T13:51:04+02:00"}
```

Po ponovnem zagonu gostitelja poglej prav to: `runs_recorded` pade na 0 → disk ne preživi zagona, zbrano se izgublja.

### Trajnost diska je pogoj

Zgodovine zamud ni od nikoder dobiti nazaj — GTFS-RT nosi samo trenutno stanje. Gostitelj ob vsaki objavi ali ponovnem zagonu zavrže disk → zbrano izgubljeno. Pred resnim zajemom preveri, ali `KAJROS_DATA_DIR` preživi ponovni zagon; uredi občasno kopijo `kajros.sqlite`.

## Pregled za skrbnika (`/admin`)

Obisk strani, napake, odzivni časi, zdravje zajema na enem mestu. **Pot obstaja samo, če je nastavljen `KAJROS_ADMIN_TOKEN`** — brez njega 404; privzetega gesla ni, ker bi ostalo tudi na stroju, ki visi na `kajros.app`.

Žeton **ne sme v git** in **ne v systemd enoto**: enoto v `/etc` sme pisati samo root, posodobitev strežnika pa je namenoma brez sudota. Zato je v podatkovnem imeniku (skupinsko pisljiv), postavi ga skripta:

```bash
bash ~/kajros/deploy/zeton.sh        # naredi ga, če ga ni, in izpiše vstop
sudo systemctl restart kajros.service
```

`zeton.sh --nov` starega zavrže, naredi novega — menjava = ena vrstica, ne opravilo za nekoga z geslom. Datoteka `640`, skupina `kajros`, ker storitev teče pod svojim uporabnikom. Okoljska spremenljivka `KAJROS_ADMIN_TOKEN` datoteko povozi; ostaja za enkratne poskuse.

Prvi obisk: `https://kajros.app/admin?k=<žeton>`; strežnik nastavi piškotek in preusmeri na čist naslov, da žeton ne ostane v zgodovini brskalnika. Napačen žeton 403 (tipkarska napaka), manjkajoč 404 (poti ni).

V razvoju žetona ni treba nastavljati: `scripts/dev-restart.sh` ga naredi sam v `data/.admin-zeton` in ob zagonu izpiše cel naslov.

**Kaj se hrani:** nikoli IP. Obiskovalec = zgoščena vrednost s soljo, ki se ob polnoči zavrže → „različnih ljudi" smiselno samo za en dan; vsota nad 30 dnevi isto osebo šteje večkrat, stran to tudi piše. Števci gredo v bazo enkrat na minuto, obrežejo se po `KAJROS_OBISK_KEEP_DAYS` (550 dni). Štetje ugasne `KAJROS_OBISK=0`.

## Aplikacija za Android (`/android`, `/prenos`)

Razdeljuje se **s strani, ne iz trgovine**: F-Droid sprejme samo prosto programje; Play zahteva račun, 25 $, preverjanje identitete, dvotedenski zaprti preizkus. Podrobnosti in druge možnosti: [android/README.md](android/README.md).

Strežnik samo streže; mapo polni `android/objavi.sh` z razvojnega računalnika. Mapa `${KAJROS_DATA_DIR}/prenos` (`/var/lib/kajros/prenos`), **nič posebnega ni treba pripraviti**: podatkovni imenik je po `deploy/brez-sudo.sh` že skupinsko pisljiv, enota ga sme brati (`ReadWritePaths`). Pot povozi `KAJROS_PRENOS_DIR`; **mape ni → poti `/prenos` ni**, stran `/android` pove, da izdaje še ni. Mount se postavi ob zagonu → po prvi objavi potreben restart storitve; `objavi.sh` ga naredi sam.

Objava nove različice (na razvojnem računalniku, brez sudota):

```bash
cd android && ./objavi.sh posreduj
```

Pred prvo objavo dvigni `versionCode` in naredi varnostno kopijo podpisnega ključa — brez njega posodobitev ni več mogoča.
