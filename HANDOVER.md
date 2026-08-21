# sztrack — stanje projekta

Povzetek za nadaljevanje dela. Vse spodaj je preverjeno na živih podatkih,
ne po spominu.

## Kaj je to

Zajem in analiza **zamud slovenskih vlakov** iz odprtih podatkov. Cilj:
shranjevati zamude, računati hitrosti, delati statistiko po vlakih in
napovedovati zamudo. Prikaz (frontend) še ni izbran.

Veja: `claude/slovenske-zeleznice-api-ql84hf`

## Od kod podatki — preverjena veriga

```
SŽ + IJPP  →  NAP (b2b.nap.si, CC BY-SA 4.0, za registracijo)
                  ↓
           DERP "gtfs-generators" (gitlab.com/derp-si)
                  ↓
   ijpp_gtfs.zip  +  rt.gtfs.derp.si/sources/ijpp/{trip_updates,service_alerts}
```

| Kaj | URL | Velikost | Pogostost |
|---|---|---|---|
| Vozni red (GTFS) | `gitlab.com/api/v4/projects/derp-si%2Fgtfs-generators/packages/generic/IJPP/latest/ijpp_gtfs.zip` | 41 MB | ~1×/dan |
| Zamude (GTFS-RT) | `rt.gtfs.derp.si/sources/ijpp/trip_updates` | 250 KB | 30 s |
| Ovire/obvestila | `rt.gtfs.derp.si/sources/ijpp/service_alerts` | 80 KB | — |

Oba vira podpirata pogojni GET (ETag), zato ob nespremenjenih podatkih ne
prenesemo nič.

**SŽ nimajo javnega API-ja.** `potniski.sz.si` je za Cloudflarom, stari SOAP
(`91.209.49.139/webse/se.asmx`) je mrtev. Uradni odprti podatki so na NAP-u.

## Kaj podatki so in česa ni

Feed pri vlakih nosi **samo `delay`**, brez absolutnega časa prihoda (avtobusi
ga imajo, vlaki ne). Dejanski čas = `vozni red + zamuda`. Iz tega sledi:

* **Ločljivost 60 s**, z `uncertainty: 120`. Hitrosti na kratkih odsekih so
  nesmiselne — `segment_speeds()` upošteva samo odseke ≥ 5 km.
* **Feed je drseče okno** — v enem klicu dobiš le postanke okoli trenutnega
  položaja vlaka. Celo vožnjo sestaviš iz zaporednih pollov.
* **Zamude naprej po progi so napoved, ne meritev.** Popravijo se, ko postaja
  mine; merodajna je zadnja znana vrednost (tabela `run`).
* **Zgodovine ni nikjer.** Če je ne posnameš sam, je ni. Preverjeno: MOTIS
  poizvedba za včeraj vrne `rt=False` in `real == sched`.
* **Ni**: cen, sestave vlaka, perona, zasedenosti, GPS pozicij vlakov
  (`vehicle_positions` vsebuje avtobuse, vlakov ne).
* Mednarodni vlaki (EN/MV) pogosto nimajo realtime pokritja.

## Koda

```
sztrack/
  geo.py         haversine, projekcija postaj na progo, Douglas-Peucker
  db.py          SQLite shema + merge_from() za združevanje baz
  gtfs.py        pogojni prenos zipa, uvoz železniškega dela
  collector.py   poll zamud, razreševanje obratovalnega dne
  stats.py       zgodovina, porazdelitve, hitrosti, napoved
  server.py      lifespan: bootstrap + zajem v ozadnji niti
  api.py         FastAPI endpointi
  cli.py         init / update / poll / show / stats / merge / export
main.py          `app` na ravni modula + `python main.py`
deploy/          systemd enote in install-rpi.sh
design/          štiri oblikovne smeri (artboardi)
seed/sz.sqlite   pripravljen vozni red (1,7 MB)
```

Tabele: `station`, `edge`, `trip`, `sched`, `service_day` (statika) ·
`obs` (dnevnik sprememb), `run` (zadnje stanje na postanek), `alert`.

Piše se **samo ob spremembi vrednosti** — brez tega bi bilo milijone praznih
vrstic.

## Izmerjeno

| | |
|---|---|
| Postaje (železnica) | 267 |
| Odseki | 389, od tega 275 elementarnih |
| Elementarna mreža | 1253,8 km (realna slovenska mreža ~1200–1300) ✅ |
| Vlaki v voznem redu | 723 |
| Uvoz GTFS | 23 s, vrh **54 MB** (pred pretočnim branjem 269 MB) |
| Strežnik ob zagonu | 57–60 MB RSS |
| Po prvem zajemu | 74 MB RSS |
| Osvežitev v istem procesu | vrh **89 MB**, ostane 85 MB |
| Baza po uvozu | 1,7 MB |

Razdalje: postaje projiciramo na polilinijo iz `shapes.txt`, razlika
kumulativnih razdalj je dolžina odseka, mediana čez vse vlake. Razpršenost med
vlaki po istem odseku je **0 m**. To niso uradne km-lege — odstopanje ~2–4 %
(Zidani Most–Ljubljana da 63,63 km proti uradnim ~61 km).

## Kje smo z objavo

**Pella** (`ivoryfalcon.onpella.app`) — zajem je delal, baza je rasla, preživela
je noč pri 58 % RAM. Ampak: javni API vrača **Cloudflare 526 na vseh poteh,
tudi na `/`** — edge ne vzpostavi TLS do izvora. Aplikacija posluša na
`http://0.0.0.0:80`, kot ji naroči `PORT=80`. To je napaka na njihovi strani.
Free paket ima 100 MB RAM in ročno podaljševanje na 16 h.
**Podatke od tam je treba pobrati** (Files → `data/sz.sqlite`) in priliti z
`sztrack merge`.

**Raspberry Pi** — izbrana pot. Prvi poskus namestitve je padel:
`install: cannot stat '/opt/sztrack/seed/sz.sqlite'`, ker je bil `seed/sz.sqlite`
ujet v `.gitignore` (`*.sqlite`) in ga v repozitoriju sploh ni bilo.
Popravljeno: izjema v `.gitignore`, datoteka je zdaj v gitu, skripta pa ima
rezervo — če seeda ni, vozni red sestavi na mestu iz GTFS.

Pi je **armhf/armv6l** (32-bit), Python 3.13, Debian 13. Odvisnosti se
nameščajo prek piwheels; med namestitvijo je bil en `RemoteDisconnected`, zato
ima pip zdaj `--retries 5 --timeout 60`.

## Naslednji koraki

1. Na Piju znova pognati `sudo bash deploy/install-rpi.sh` (idempotentna).
2. Preveriti `curl -s http://localhost:8000/api/health` in `journalctl -u sztrack -f`.
3. S Pelle prenesti `sz.sqlite` in pognati
   `sudo -u sztrack /opt/sztrack/.venv/bin/python -m sztrack.cli merge ~/sz-pella.sqlite`.
4. Ugasniti Pello, da ne zbira vzporedno (ali pustiti — `merge` je varen in idempotenten).
5. Izbrati oblikovno smer in narediti frontend: **Leaflet + OSM rastrske
   ploščice** (uporabnikova izbira; MapLibre in OpenFreeMap sta bila alternativa).

## Odprta vprašanja

* Katera oblikovna smer (A nadzorna soba / B vozni red / C analitika / D sledilnik).
  Platno: https://claude.ai/code/artifact/189e04ee-26e3-4c2e-916a-26da4e9ae709
* Dostop do API-ja od zunaj, ko bo frontend pripravljen — Tailscale ali
  Cloudflare Tunnel. Vrat na usmerjevalniku ne odpirati: API nima avtentikacije.
* Napoved zamude je zaenkrat izhodiščna (prenos zamude + historična mediana
  spremembe na odseku). Za kaj boljšega rabi 2–3 mesece zajema.
