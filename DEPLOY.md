# Objava

**Postavitev od 3. 11. 2026 dvojna** (malina ni več del projekta):

| stroj | naslov | naloga |
|---|---|---|
| prenosnik `arwen` | `192.168.1.46` | **streže** `kajros.app` in je **edini zajem** |
| ta računalnik | — | razvoj; podatki za analizo = kopija z arwena (`.claude/rules/objava.md`, „Kopija baze za razvoj“) |

**Posodobitev prenosnika = `git push arwen`** (od 17. 9. 2026). Potisk posodobi delovno drevo v `~/kajros`, kavelj `post-receive` požene `deploy/posodobi.sh`, ta prepiše kodo v `/opt/kajros`, znova zažene in počaka na `/api/health`. Izpis pride nazaj na razvojni računalnik → neuspela objava vidna tam, kjer si jo sprožil. **Gesla ne rabi**: restart = eden od štirih ukazov z `NOPASSWD`, nastavi jih `deploy/brez-sudo.sh`.

Enkratna nastavitev: `deploy/arwen-git.sh` (po cevi: `ssh david@192.168.1.46 'bash -s' < deploy/arwen-git.sh`) in na razvojnem računalniku `git remote add arwen david@192.168.1.46:kajros`.

`posodobi.sh` mogoče pognati tudi ročno (`~/kajros/deploy/posodobi.sh ~/kajros`), rabiš za ponovno namestitev istega commita.

**Vlaki rabijo Chrome na arwenu** (od 10. 10. 2026). Zamude vlakov in tire beremo naravnost s potniski.sz.si, ki je za Cloudflarom in spusti le Chrome z oknom; na strežniku mu okno da Xvfb. Enkrat, s sudo: `ssh -t david@192.168.1.46 'sudo bash ~/kajros/deploy/brskalnik.sh'` -- namesti `xvfb` in `google-chrome-stable` (Googlov paket, posodablja ga `apt upgrade`), preizkusi branje v istem peskovniku kot storitev in znova zažene strežnik. Brez tega `/admin` pri zemljevidu SŽ piše „ni Chroma“, vlake pa piše derp.si, kolikor jih ima.

Za majhne gostitelje, ki sprejmejo zip, velja poglavje »Paket za gostitelja« naprej.

## Kako teče na arwenu

Enota `kajros.service` (`deploy/kajros.service`), koda v `/opt/kajros`, podatki v `/var/lib/kajros`, sistemski uporabnik `kajros`.

**Vozni red se osvežuje sam.** V `kajros.service` `KAJROS_REFRESH=subprocess` — uvoz teče v podprocesu, ki po koncu ves pomnilnik vrne sistemu (vrh 54 MB). Na Pelli izklopljeno zaradi 100 MB omejitve.

**Ura mora biti točna.** Obratovalni dan vožnje se ugotavlja z ujemanjem voznorednega okna s trenutnim časom → `systemd-timesyncd` naj teče. Časovni pas sistema ni pomemben — koda povsod uporablja `Europe/Ljubljana`.

**Varnostne kopije** vsak dan ob 2:40 v `/var/lib/kajros/backup/` prek `VACUUM INTO` (`deploy/varnostna-kopija-baze.sh`), stisnjene z `gzip -1`. `VACUUM INTO` je ena bralna transakcija: posnetek je dosleden, zajem piše naprej. `sqlite3 .backup` se je ob vsakem zapisu druge povezave začel znova in se na arwenu 1.–17. 10. 2026 vrtel do 58 min (46 min procesorja). Prvi `VACUUM INTO` 17. 10.: baza 4,9 GB, kopija 4,0 GB, stisnjena 789 MB, 226 s in 2 min procesorja; obnova preizkušena (`PRAGMA quick_check` ok). Ob 2:40, ker ob 3:30 tečeta obrez dnevnika in nočni povzetki. Hranijo se **tri**, ne štirinajst: z vsemi prevozniki baza zraste ~3,4 GB na leto, štirinajst polnih kopij bi zapolnilo kartico. Če ni prostega vsaj toliko, kolikor je baza, in še 2 GB, se kopija preskoči in to zapiše v dnevnik — poln disk ustavi tudi zajem, kopija je le kratkoročna varovalka.

**Zajema se samo tisto, česar kasneje ni mogoče dobiti**: zamude in obvestila. Vreme ima arhiv za nazaj, statistika je izpeljanka `run`. Zgodovine zamud ni od nikoder dobiti nazaj, zato je arwen edini zajem in kopija baze (zgoraj) edina varovalka.


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
| `KAJROS_SZ_ZAMUDE` | 1 | `0` izklopi zamude vlakov z zemljevida SŽ (prek Chroma) |
| `KAJROS_PERONI` | 1 | `0` izklopi tire s table SŽ (prek Chroma) |
| `KAJROS_SZ_CHROME`, `KAJROS_SZ_XVFB` | poišče sam | pot do Chroma in Xvfb, kadar nista v `PATH` |
| `KAJROS_PREHOD_GPS` | `vodi` | prehod postanka iz GPS brez trase: `vodi` piše zamude, `senca` samo meri (`gps_prehod`), `0` izklopi (stari način, lega na traso) |

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
