# Objava

**Postavitev od 4. 9. 2026 je trojna** in vsak stroj ima svojo nalogo:

| stroj | naslov | naloga |
|---|---|---|
| prenosnik `arwen` | `192.168.1.46` | **streže** `kajros.app` in zajema sam |
| malina (Pi Zero W) | `192.168.1.166` | zajem, teče ves čas, **varovalo** |
| ta računalnik | — | razvoj |

Zakaj oboje zajema: prikaz mora biti živ, poteg pa je star toliko, kolikor je
star zadnji poteg. Ko prenosnik nekaj časa ne teče, se vrzel zapolni z
`deploy/zapolni-vrzel.sh` (bere z maline, nikoli ne piše nanjo). Malina zato
ostane prižgana: prenosnik se zapira in seli, ona ne.

**Posodobitev prenosnika:** `~/kajros/deploy/posodobi.sh` na njem — izpiše
nameščeni commit, prepiše kodo v `/opt/kajros`, jo znova zažene in počaka na
`/api/health`. Kodo v `~/kajros` osveži razvojni računalnik z `rsync`.
**Gesla ne rabi**: restart je eden od štirih ukazov z `NOPASSWD`, ki jih
nastavi `deploy/brez-sudo.sh`.

Starejši `~/posodobi.sh` je **odstranjen 12. 9. 2026**: posodabljal je prek
`install-rpi.sh` in je zato zahteval sudo geslo, ki ga v seji brez terminala
ni mogoče vpisati. Podrobnosti in past z `/tmp` na malini so v
`.claude/rules/objava.md`.

Spodaj je namestitev na Raspberry Pi; za majhne gostitelje, ki sprejmejo zip,
velja poglavje »Paket za gostitelja« naprej.

## Raspberry Pi

> ### Enkratno: prva namestitev po preimenovanju v Kajros
>
> Malina teče staro kodo pod imenom `sztrack` in bo tekla naprej, dokler tega
> ne pogeneš. Zajem medtem **ne trpi** — `potegni.sh` staro pot sam najde.
>
> Vir je že prenesen v `~/kajros-src` (3. 9. 2026). Manjka samo korak s sudom:
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
> Kaj naredi: preseli `/var/lib/sztrack/sz.sqlite` (z `-wal` in `-shm`) v
> `/var/lib/kajros/kajros.sqlite`, ugasne in onemogoči `sztrack-zajem`,
> postavi `kajros-zajem`. Selitev je preizkušena v peskovniku, na sami malini
> **ne** — zato po zagonu preveri:
>
> ```bash
> systemctl is-active kajros-zajem          # active
> sqlite3 /var/lib/kajros/kajros.sqlite 'SELECT COUNT(*) FROM run'
> ```
>
> Če se kaj zalomi, stara baza ni izbrisana, ampak premaknjena — nazaj gre z
> `mv /var/lib/kajros/kajros.sqlite /var/lib/sztrack/sz.sqlite` in
> `systemctl enable --now sztrack-zajem`.
>
> Ta odstavek odstrani, ko bo opravljeno.


Za ta projekt je Pi boljši od brezplačnih gostiteljev iz enega razloga:
zajem mora teči **neprekinjeno**, ker zgodovine zamud ni mogoče dobiti za nazaj.
Brezplačni paketi bodisi zaspijo, bodisi zavržejo disk, bodisi zahtevajo ročno
podaljševanje. Pi ne dela nič od tega.

### Namestitev

```bash
sudo bash deploy/install-rpi.sh
```

Skripta je idempotentna — poženeš jo lahko znova za posodobitev. Naredi:

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

Iz domačega omrežja je dosegljiv na `http://<ip-pija>:8000/docs`.

### Kaj je na Pi drugače

**Vozni red se osvežuje sam.** V `kajros.service` je `KAJROS_REFRESH=subprocess` —
uvoz teče v podprocesu, ki po koncu ves pomnilnik vrne sistemu (vrh 54 MB).
Na Pelli je bilo to izklopljeno zaradi 100 MB omejitve.

**Ura mora biti točna.** Obratovalni dan vožnje se ugotavlja z ujemanjem
voznorednega okna s trenutnim časom, zato naj `systemd-timesyncd` teče.
Časovni pas sistema ni pomemben — koda povsod uporablja `Europe/Ljubljana`.

**Zapisovanje je majhno.** Piše se samo ob spremembi zamude, torej nekaj tisoč
vrstic na dan; za SD kartico zanemarljivo. Če imaš USB SSD, je vseeno boljše
mesto — nastavi `KAJROS_DATA_DIR` nanj v enoti storitve.

**Varnostne kopije** nastanejo vsak dan ob 3:30 v `/var/lib/kajros/backup/`
prek `sqlite3 .backup`, kar je konsistentno tudi med pisanjem, in se stisnejo
z `gzip -1` (~3,1× manjše, merjeno). Hranijo se **tri**, ne štirinajst: z vsemi
prevozniki zraste baza ~3,4 GB na leto in štirinajst polnih kopij bi kartico
zapolnilo. Če bi po kopiji ostalo manj kot 2 GB prostega, se ta preskoči in to
zapiše v dnevnik — polna kartica ustavi tudi zajem, kopija pa je le
kratkoročna varovalka.

**Dolgoročni arhiv je računalnik**, ki bazo potegne dol (`kajros merge`), ne
Pi. Kartice odpovedo.

## Samo zajem, brez strežnika

Kadar naj stroj le polni bazo — da lahko računalnik ugasneš — se namesti
`kajros-zajem.service` namesto strežnika:

```bash
sudo KAJROS_MODE=zajem KAJROS_AGENCIES=1118,1123,1119,1121 bash deploy/install-rpi.sh
```

Zajema se **samo tisto, česar kasneje ni mogoče dobiti**: zamude in obvestila.
Vreme ima arhiv za nazaj, statistika je izpeljanka `run` — oboje se izračuna
tam, kjer je baza. Lege vozil ni, ker je samo "zdaj" in se ne hrani.

`KAJROS_AGENCIES` se zapiše v enoto in ob spremembi sproži ponovni uvoz voznega
reda (`--force`; brez tega bi ETag rekel "nespremenjeno"). Uvoz **zamenja samo
statične tabele** — `obs` in `run` ostaneta.

### Prenos zajema s prejšnjega gostitelja

Zajeto drugje se ne sme izgubiti. Prenesi staro `kajros.sqlite` in jo prilij:

```bash
sudo -u kajros /opt/kajros/.venv/bin/python -m kajros.cli merge ~/sz-pella.sqlite
```

```json
{"source_observations": 271, "observations_added": 271,
 "runs_touched": 222, "observations_total": 727, "days_covered": 2}
```

Postopek je varen tudi, če sta bazi nekaj časa tekli vzporedno: meritve so
ključene po `(trip_id, service_date, stop_seq, feed_ts)`, zato se podvojene
tiho zavržejo, v `run` pa obvelja zapis z novejšim `feed_ts`. Ponovni zagon
istega ukaza doda 0 vrstic.

### Dostop od zunaj

Za zajem ni potreben — Pi sam kliče ven. Ko bo frontend rabil API z interneta,
je najmanj dela s Tailscalom (zasebno omrežje, brez odpiranja vrat) ali s
Cloudflare Tunnelom (javno, s samodejnim HTTPS in brez javnega IP-ja).
Vrat na usmerjevalniku ne odpiraj — API nima avtentikacije.

## Paket za gostitelja

En sam proces streže API in hkrati zajema zamude — ločenega delavca ni.
Zajem teče v ozadnji niti, ki jo zažene FastAPI ob zagonu.

### Vsebina paketa

```
main.py            vstopna točka: uvicorn na $PORT
requirements.txt   fastapi, uvicorn, requests, gtfs-realtime-bindings
Procfile           web: python main.py
kajros/           koda
seed/kajros.sqlite     pripravljen vozni red (1,7 MB) za takojšen zagon
```

### Zagon

Delujeta oba načina — kar koli od tega gostitelj že uporablja:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT   # gostitelj vodi strežnik (Pella)
python main.py                                 # strežnik zaženemo sami
```

`app` je zato izpostavljen na ravni modula `main`. Če gostitelj javi
`Error loading ASGI app. Attribute "app" not found in module "main"`, pomeni,
da poganja prvo obliko — in prav zato je `app` tam.

Pri drugi obliki se vrata preberejo iz `PORT`; če ga ni, uporabi 8000.

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

Če baze še ni, se prekopira `seed/kajros.sqlite` — zagon je takojšen. Če je tudi
seed ni, si vozni red prenese sam (41 MB, uvoz ~23 s pri polnem jedru; na 0,1
jedra računaj nekaj minut) in zip nato pobriše.

**Obstoječa baza se nikoli ne povozi.** Ponovna objava paketa torej ne izbriše
zajete zgodovine — dokler je `KAJROS_DATA_DIR` na disku, ki preživi objavo.

### Poraba

Merjeno na tem paketu:

| | |
|---|---|
| RSS ob zagonu (s priloženo bazo) | **60 MB** |
| RSS po prvem zajemu | **74 MB** |
| Uvoz GTFS (vrh) | **54 MB**, 23 s |
| Baza po uvozu | 1,7 MB |
| Promet | 250 KB / 30 s + 41 MB enkrat na dan |

Pri 100 MB pomnilnika ostane okoli 25 MB rezerve. Če jo bo zmanjkalo, je prvi
korak `KAJROS_POLL_SECONDS=60` in izogibanje `/api/network.geojson` v vroči zanki
(odgovor je ~1 MB — postavi ga raje kot statično datoteko prek `kajros export`).

### Zakaj je osveževanje voznega reda privzeto izklopljeno

Uvoz GTFS je najdražji trenutek v življenju procesa. Izmerjeno na tem paketu:

| način | vrh pomnilnika | opomba |
|---|---|---|
| `inprocess` | **89 MB** | in ostane pri 85 MB — Python aren skoraj ne vrne sistemu |
| `subprocess` | 54 MB v otroku **poleg 57 MB starša** = ~111 MB skupaj | oboje je hkrati rezidentno |
| `off` | — | privzeto |

Pri 100 MB pomnilnika nobena od obeh ni varna: proces bi ob osvežitvi lahko
dobil OOM, in to vsak dan ob isti uri. Zato je privzeto `off`.

Vozni red osvežiš tako, da drugje pognaš `kajros update`, novo `kajros.sqlite`
daš v `seed/` in objaviš paket — obstoječa baza se ne povozi, ker se seed
uporabi le, kadar baze še ni. (Za to je treba staro bazo enkrat odstraniti
oziroma preimenovati.) Vsebinsko se vozni red spremeni nekajkrat na leto.

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

Po ponovnem zagonu gostitelja poglej prav to: če `runs_recorded` pade nazaj
na 0, disk ne preživi zagona in zbrano se izgublja.

### Trajnost diska je pogoj

Zgodovine zamud ni od nikoder dobiti nazaj — GTFS-RT nosi samo trenutno stanje.
Če gostitelj ob vsaki objavi ali ponovnem zagonu zavrže disk, se zbrano izgubi.
Pred resnim zajemom preveri, ali `KAJROS_DATA_DIR` preživi ponovni zagon, in si
uredi občasno kopijo `kajros.sqlite`.
