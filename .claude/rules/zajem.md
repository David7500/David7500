---
paths:
  - "sztrack/collector.py"
  - "sztrack/alerts.py"
  - "sztrack/gtfs.py"
  - "sztrack/db.py"
---

# Kaj feed pošlje in kje laže

Vse spodnje je **izmerjeno na živem feedu**, ne domnevano. Kdor katero od teh
pravil spreminja, naj izmeri znova in številko zapiše sem. Kar iz tega velja
za strežbo (starost leg, predpomnilnik, meja žive vožnje), je v
`.claude/rules/strezba.md`.

**Vlaki in avtobusi ne pošiljajo istega.** Izmerjeno na živem feedu, po
prevozniku (delež postankov v enem klicu):

| | `arrival.delay` | `departure.delay` | absolutni čas | `uncertainty` | `vehicle.id` |
|---|---|---|---|---|---|
| SŽ | 100 % | 100 % | **0 %** | 100 % | ne |
| Arriva | 61 % | 100 % | 92 % | 0 % | da |
| Nomago | 42 % | 100 % | 97 % | 0 % | da |
| LPP | 39 % | 99 % | 100 % | 0 % | da |
| AP MS | 31 % | 100 % | 94 % | 0 % | da |

Iz tega dvoje, kar velja spoštovati:

* **Nikoli ne beri `stu.arrival.delay` naravnost.** Protobuf za neizpolnjeno
  polje vrne 0, kar je videti kot „točno". Prav ta napaka je v bazo zapisala
  11 906 od 20 523 avtobusnih vrstic (58 %) kot točne; delež točnih je bral
  **84,3 % namesto 71,2 %**. Pri železnici ni prizadeta nobena vrstica.
  Uporabljaj `collector._delay_of()`, ki polje preveri in ob absolutnem času
  zamudo **izračuna** — preverjeno proti poročani odhodni zamudi: mediana
  razlike −9 s, 87 % v eni minuti.
* **Zato povsod `COALESCE(delay_dep, delay_arr)`, ne obratno.**
  `departure.delay` je izpolnjen pri vseh prevoznikih stoodstotno.

Feed pri vlakih nosi **samo `delay`**, brez absolutnega časa. Dejanski čas =
`vozni red + zamuda`. Iz tega:

* **Ločljivost 60 s**, `uncertainty: 120`. Ne kaži sekund. Hitrosti samo na
  odsekih ≥ 5 km (`segment_speeds()` to že filtrira).
* **Feed je drseče okno** — en klic da le postanke okoli trenutnega položaja.
  Celo vožnjo sestavljamo iz zaporednih pollov.
* **Meja med meritvijo in napovedjo je `stats.last_measured()`.** Vsak prikaz,
  ki kaže zamudo, jo mora upoštevati: kar je za zadnjim prevoženim postankom,
  je feedova napoved. Ta napaka je bila že dvakrat -- v `/api/live` in v
  odhodni tabli, kjer je IC 502 pri +17 min v Borovnici na tabli v Litiji
  pisal **0 min**. Potnik bi bral, da je vlak točen.

* **Enotna zamuda čez vso vožnjo je pri avtobusih sumljiva, a ni dokaz.**
  Merjeno na 3 636 vožnjah z vsaj petimi zajetimi postanki: pri **železnici**
  je enotna zamuda pogosta (19,7 % voženj), a **nikoli nad 60 min** — to je
  vlak, ki je ves čas dve minuti pozen. Pri **avtobusih** je enotnih le 2,2 %
  voženj, a **11 od teh 20 je nad 60 min**, in od 19 avtobusnih voženj z
  zamudo nad uro jih je 11 takih. A6345 je imel 7 800 s enako na vseh 46
  postankih.

  **Prikaza za to (še) ni namenoma.** Feed te zapise pošilja z današnjim
  `start_date`, torej naša razrešitev obratovalnega dne ni kriva, in enotna
  zamuda je fizično mogoča: vozilo odpelje pozno in nato vozi po voznem redu.
  Devet dni in dvajset primerov je premalo za pravilo, ki bi skrival podatke.
  Kar bi to razrešilo, je sled skozi `obs`: ali se postanki v zaporednih
  pollih premikajo. Do takrat velja samo `api.MAX_LIVE_DELAY_S`.

* **Iz `obs` se ne da ugotoviti, kdaj je bila vrednost nazadnje POTRJENA.**
  Dnevnik piše samo ob spremembi (`OBS_MIN_DELTA_S`), zato je zadnji zapis
  zadnja *sprememba*, ne zadnja potrditev — feed isto vrednost pošilja naprej
  vsakih 30 s, mi je ne zapišemo. Posledica: za nazaj **ni mogoče ločiti
  meritve od napovedi, ki se ni nikoli popravila.** Živi prikaz to reši z
  `stats.last_measured()` (vozni red + zamuda ≤ zdaj), zgodovina pa ne more.

  Kako se to pokaže: RG 1604 ima v `run` na Ljubljani Zalogu 15, 2, 7, 14, 13,
  11, 16 min — na **štirih od osmih dni natanko toliko, kolikor je bila zamuda
  ob prihodu v Ljubljano**, torej feedova napoved izpred postaje. Na Litiji,
  devetnajst minut pozneje, so vrednosti 0, 2, 6, 0, 1, 1, 2 in se ujemajo z
  Zagorjem za njo. Biti +13 na Zalogu in +1 v Litiji je fizično nemogoče, a iz
  zapisa samega se ne vidi, katera od obeh je napoved.

  **Preizkušeno in ne pomaga:** vsiliti modelovo fiziko zaporedju napovedi
  (v točki j ne moreš biti bolj pozen, kot boš v j+1, plus rezerva vmes).
  MAE 1,92 → 1,96 min, delež v petih minutah 91,0 → 90,8 %. Rezerva je tudi v
  voznem času, ne le v postankih, zato pravilo prereže preveč pravih okrevanj.

* **Ne verjemi ničli, ki jo feed vrne za en klic.** Pri 14 % postankov z več
  kot dvema zapisoma se pojavi vzorec X, 0, X v razmiku ene minute. Zamuda med
  dvema klicema ne more pasti za več, kot je vmes minilo časa. `run` zato ničlo
  po zamudi ≥ 5 min sprejme šele, ko jo potrdi drugi zaporedni poll
  (`collector.is_zero_blip`); dnevnik `obs` obdrži vse. Isto varovalo velja pri
  določanju lege vlaka -- sicer (vozni red + 0) pomeni, da je postanek že minil,
  in vlak na zemljevidu skoči naprej.
* **Odhodni zamudi na dolgem postanku ne verjemi.** Feed jo objavi kot ničlo,
  še preden vlak pride, in je pogosto ne popravi. Ujeto v živo 29. 8.: RG 1604
  je imel v Ljubljani zapisan prihod +19 in **odhod 0** — torej dve minuti
  stanja — na Ljubljani Zalogu osem minut pozneje pa **+5**, torej sedem minut
  stanja. Oboje hkrati ne drži, in tokrat prvič vemo, katera stran je napačna:
  Zalog in Litija (+3) sta skladna med sabo, odhodna ničla ni skladna z nikomer.

  Isti vzorec je na tej postaji **pet dni od devetih**. `stats.typical_dwell()`
  zato dan sploh šteje le, kadar sta naslednja dva postanka skladna med sabo
  (razlika pod 2 min), postanek pa izračuna iz **naslednjega** postanka, ne iz
  odhodne vrednosti. RG 1604 v Ljubljani: štirje uporabni dnevi od devetih,
  postanki 7, 9, 11 in 17 min proti 21 po voznem redu.

* **Zamuda ni ena številka na postanek: prihodna in odhodna sta lahko različni.**
  Vlak ne odide takrat, ko pride. LP 4219 ima na Mostu na Soči v voznem redu
  **devet minut postanka** (20:38 → 20:47, križanje na enotirni bohinjski
  progi): 29. 8. je pripeljal +10 in odpeljal +3 — stal je dve minuti namesto
  devetih. Feed je oboje tudi povedal (`prihod 600 / odhod 180`).

  Redko, a ne zanemarljivo: 406 postankov v voznem redu ima nad dve minuti
  zadrževanja, in v devetih dneh se prihodna in odhodna zamuda razlikujeta pri
  1 307 postankih, od tega 362 za pet minut ali več.

  Prikaz kaže `COALESCE(delay_dep, delay_arr)`, torej **odhodno**. To je prav —
  potnika zanima, kdaj gre vlak naprej — a ena številka na vrstico naredi v
  grafu prepad, ki je videti nemogoč („kako je zamuda padla za osem minut med
  dvema postajama"). Zato: kadar se številki razlikujeta za minuto ali več,
  vrstica pokaže **obe** (`+10 → +3`) z razlago postanka, krivulja pa gre v
  naslednjo postajo na **prihodno** vrednost in pade **navpično** na postaji.
  Padec se je zgodil tam, ne na odseku.

* **Zamuda je izmerjena v prometnem mestu, ne nujno na postaji.** Ime tega
  mesta **imamo** -- v `SZ-DELAY-*` obvestilih ("Vlak EC 79 ima izjemno zamudo
  161 min ob prihodu na postajo Sevnica"). `run` pozna samo voznoredne postanke,
  zato je to edini vir. Hrani se v `delay_report`.

  Prevoznikovo poročilo je tudi **svežejše od naše meritve**: izmerjeno na 64
  primerjanih vožnjah je novejše v 97 % primerov, mediana razlike +40 s. Zato
  ga zemljevid in glava okna vožnje postavita pred našo vrednost -- a kraj in
  zamuda morata biti **iz istega vira**, sicer piše "Dobova" ob zamudi,
  izmerjeni v Sevnici.

  Zaporedje teh poročil je **dnevnik vožnje**, kakršnega ni nikjer drugje:
  IC 503 je šel s +6 v Ormožu na +29 v Litiji, v Borovnici nadoknadil osem
  minut in do Postojne spet zdrsnil na +25. V oknu vožnje, napredni pogled.

* **Zgodovine ni nikjer.** Če je ne posnamemo sami, je ni.
* **Zakaj vlak zamuja, pove `service_alerts`.** `SZ-OVIRA-*` so dela na progi,
  nadomestni prevozi in združene garniture, vezani na `route_id` (ta je 1 : 1
  s tripom, zato jih znamo pripeti na številko vlaka). Avgusta 2026 jih je bilo
  ~45 hkrati -- nadomestni prevoz Ljubljana–Logatec in Divača–Koper do
  12. decembra, zapore enega tira Celje–Šentjur, Poljčane–Pragersko,
  Maribor–Hoče. **To pojasni, zakaj so zamude v zajetih dneh tako velike.**

* **Odpovedi niso strukturirane.** GTFS-RT ima za to `schedule_relationship`
  (CANCELED, SKIPPED), a SŽ ga ne uporablja -- v vseh zajetih zapisih je
  vrednost `SCHEDULED`. Odpoved sporočijo z besedilom obvestila ("Vlak vozi
  samo do postaje Ljubljana Šiška", `effect = 6`). Zajem polje vseeno šteje in
  ob prvi neničelni vrednosti zavpije v dnevnik; prikaza zanj namenoma še ni,
  ker bi bil to prikaz za podatek, ki ne obstaja.

* **Ko feed izgubi vozilo, začne objavljati uro namesto zamude.** Za postanke,
  ki jih je vozilo *že prevozilo*, zna objaviti vrednost, ki raste natanko za
  minuto na minuto. Ujeto v živo 30. 8., LPP 25 (vožnja 452632, Poliklinika):
  ob 12:19:36 prihod +58 s in odhod +126 s — prava meritev z **različnima**
  vrednostma — nato ob 12:23:48 skok na +482 in sedem klicev zapored rast
  natanko +60 s na +60 s do **+842 (+14 min)**, ob 12:30:29 pa vrnitev na
  +58/+126. Vozilo je bilo ves ta čas že davno mimo.

  V zajetem je takih zaporedij **11 827 pri 947 vožnjah**. To pojasni tudi
  doslej odprto vprašanje o **enotni zamudi čez vso vožnjo**: Nomagov N6571 s
  27 060 s na vseh postankih je natanko ta vzorec, ujet po tem, ko se je
  ustavil (4 od 12 takih voženj imajo zaporedje v `obs`; pri ostalih smo se
  priključili šele po tem, ko je vrednost že zmrznila).

  Varovalka je `collector.undoes_passing`: zavrne vrednost, ki bi postanek,
  za katerega smo **že zapisali meritev** o prevozu pred več kot 120 s,
  prestavila nazaj v prihodnost. Dnevnik `obs` obdrži vse; čaka samo `run`.

  **Prva različica pravila je bila preširoka in to je bilo merljivo.**
  Brez dodatnega pogoja je vzela pravo dvourno zamudo nočnega vlaka: EN 1276
  je 28. 8. ob 00:03 imel za Celje zapisano `0/0` — feedovo napoved pred
  prihodom, ne meritev — in ob 01:57 pravih +114 min. Zato **za dokaz o
  prevozu šteje samo zapis z različnima vrednostma za prihod in odhod**: te
  feed za nerazrešen postanek ne objavi. Ista past je v projektu zapisana že
  dvakrat („ne verjemi ničli, ki jo feed vrne za en klic").

  Učinek `sztrack repair` na 10 dneh zajema: **852 vrstic** v `run`, od tega
  277 avtobusnih (mediana 51 min, največ 11 h) in **300 železniških**
  (mediana 14 min, največ 80 min). Povprečna zamuda pade pri avtobusih z 9,8
  na 8,8 min, pri železnici s 6,7 na 6,5. Železniški primeri so isti vzorec:
  LPV 2252 je bil 22. 8. ob 08:23 v Zagorju izmerjen s prihodom +2 in
  odhodom +1, uro in četrt pozneje pa je feed zanj objavil +79 min.

  **`repair` popravlja samo postanke, na katerih je varovalka sprožila.**
  Prej je čez `run` prepisal ves ponovljeni dnevnik — in ker `obs` beleži le
  spremembe nad `OBS_MIN_DELTA_S`, je s tem 16 696 vrstic zamenjal za do
  minuto grobejše, da bi popravil 4 217 pokvarjenih. Popravilo mora
  popravljati, ne glajenja.

* **Feed objavlja zamudo za vožnjo, ki se še ni začela — in to je zamuda
  PREJŠNJE vožnje istega vozila.** LPP 25 (452632) 30. 8.: postanek Medvode
  novo naselje ima vozni red 11:41, feed pa je zanj že od 11:11 objavljal
  +8, +10, +11, +12, +13 in ob 11:33:55 **+14 min** — vsakič čas, ki je bil
  takrat še v prihodnosti, torej napoved. Ob 11:35:44 je vrednost popravil
  na 0 in avtobus je odpeljal skoraj točno.

  `run` je vseeno obtičal na +14, ker je popravek zavrnil `is_zero_blip`:
  ta čaka na potrditev druge ničle, feed pa je ničlo povedal **enkrat
  samkrat** in drseče okno je šlo naprej. V grafu je bilo to videti kot
  devet postaj pri +14 in nato **padec za petnajst minut v enem koraku** —
  tam se je končala napoved in začela meritev.

  Zato `collector.is_forecast`: vrednost, ki ob svojem nastanku postanek
  postavlja v prihodnost, **ni meritev**, in ničla, ki jo popravlja, ni blip.
  Merilo je brez prostih parametrov.

* **Zgodovina poti mora biti zamejena na `trip_id`.** `stats.history()` je
  filtrirala po `train_no` in gradila profil po `stop_seq` — po **zaporedni
  številki** postanka. Pri LPP liniji 25 (217 voženj) se je pod „postanek 2"
  sešlo *Medvode novo naselje* (drugi postanek proti Zadobrovi, povprečje
  +7 min) in *Novo Polje* (drugi postanek v **nasprotni smeri**, +1 min) —
  dva različna kraja pod eno oznako, in stolpec je pisal „1 vožnja" nad 850
  meritvami iz 25 voženj. Isto velja za devet vlakov s sezonskimi različicami.

  Pri železnici je to brez posledic: **0 od 663 številk z meritvami ima več
  kot eno vožnjo**. Pri avtobusih jih ima 205 od 242, največ 42.

  Ista funkcija je edina v projektu brala `delay_arr` pred `delay_dep` —
  natanko obratno od pravila, ki velja povsod drugod. Popravljeno.

* **Na izhodišču prihoda ni.** Feed ga za `stop_seq = 1` vseeno pošlje in je
  smet: LPP 25 je 30. 8. na Medvodah naselju poročal prihod −267 s ob odhodu
  −2 s, na drugi vožnji istega dne −1771 s. Prikaz je iz tega sestavil
  „vlak je stal 4 min namesto 0 — izgubil 4 min", torej zgodbo o dogodku, ki
  se ni zgodil. `common.dwellSplit()` zdaj prvi postanek preskoči.

* **Ni** cen, sestave vlaka, perona, zasedenosti. Mednarodni vlaki (EN/MV)
  pogosto brez realtime pokritja.

Izjema je **vreme**: Open-Meteo ima arhiv za nazaj, zato ga ni treba zbirati
vnaprej — `sztrack weather` ga dopolni za že zajete zamude kadarkoli.

## Kar je pri avtobusih drugače

* **Veriga vozila je edini vir odgovora, kje je avtobus, ki se še ni začel.**
  `trips.txt` nosi `block_id` -- zaporedje voženj istega fizičnega vozila.
  Imajo ga **samo avtobusi** (vseh 789 voženj SŽ je brez) in tudi tam le
  7 547 od 20 736 voženj (36 %), v 1 385 blokih. Veriga je resnična: med
  zaporednima vožnjama je le 0,9 % prekrivanj, mediana postanka 14 min, v
  69 % se konec ene ujema z začetkom naslednje. Isti `block_id` nastopa pri
  več `service_id` (788 od 1385), zato se sosed **išče po obratovalnem dnevu**,
  ne po `service_id`.

  Merjeno ob 20:22: od 25 voženj, ki so se začenjale v naslednji uri in pol,
  jih je 17 imelo prejšnjo vožnjo v bloku in 11 od teh svežo GPS lego. To je
  edini način, da o avtobusu pred odhodom sploh kaj povemo -- zanj takrat ni
  ne zamude ne lege, vozilo pa obstaja.

  **Zamude prejšnje vožnje ne prenašaj naprej.** Izmerjeno na 195 parih
  zajetih voženj: prenos zamude MAE 4,53 min, „predpostavi točno" 2,29 min --
  prenos je torej **slabši od nevednosti**. Vozilo zamudo med vožnjama
  nadoknadi: kadar prejšnja zamuja ≥ 5 min (mediana 12 min) in ima vmes
  15--60 min postanka, se na naslednjo prenese 11 %. Zato je prejšnja vožnja
  v prikazu **dejstvo o vozilu** („zdaj pri postajališču X, na prejšnji vožnji
  +1 min"), ne napoved odhoda, in prikaz to tudi pove.

* **`bikes_allowed` je v celotnem GTFS ničla.** Vseh 20 736 voženj petih
  agencij ima `0` = „ni podatka". Polje obstaja, podatka ni -- zato ga uvoz
  ne bere in ga v shemi ni. Isto velja za `wheelchair_accessible`, ki ga
  `trips.txt` sploh nima. Če se to kdaj spremeni, je oboje en stolpec dela.

## Vožnja, obratovalni dan in dnevnik

`trip.start_s` / `trip.end_s` sta **prvi odhod in zadnji prihod vožnje**,
izpeljana iz `sched`, a shranjena v `trip`, ker ju rabi najbolj vroča
poizvedba — "kaj se zdaj vozi". Polni ju `db.fill_trip_window()` ob uvozu
GTFS in ob migraciji. Kdor vstavlja vožnje mimo uvoza (test, ročni popravek),
ju mora zapolniti, sicer vožnja **ni na seznamu živih**.

**Feed občasno objavi vožnjo z JUTRIŠNJIM obratovalnim dnem.** Izmerjeno
31. 8.: 44 vrstic v `run` (0,026 %) v **dveh** vožnjah ima `service_date` v
prihodnosti — Nomagov N6507 z voznorednim odhodom 04:25 in enotno zamudo
48 240 s (13,4 h) na vseh postankih. To je isti vzorec kot pri N6571: feed
zamenja prometni dan in razliko objavi kot zamudo.

**Pravila za to ni namenoma.** Vseh 44 vrstic ima zamudo nad 6 h, torej jih
`api.MAX_LIVE_DELAY_S` že drži izven živega prikaza. Dve vožnji sta premalo
za varovalko ob zajemu — isti razlog kot pri enotni zamudi čez vso vožnjo.
Meri se z `SELECT COUNT(*) FROM run WHERE service_date > date('now','localtime')`;
če delež kdaj zraste, je čas za pravilo.

**Vožnja, ki zamuja več kot `api.MAX_LIVE_DELAY_S` (6 h), ni živa.** To je
pravilo prikaza, ne pospešek. Pri železnici ni nobene zamude čez tri ure
(najhujša EC 79 z 2,9 h); pri avtobusih je nad šest ur 0,67 % vrstic in te
niso zamude — Nomagov N6571 je imel 27 060 s enako na vseh 44 postankih
vožnje, ki je vozila ob 04:15, kar je feedova zamenjava prometnega dne.

`trip.block_id` je veriga voženj istega vozila (glej zgoraj). Indeks
`trip_block` je **delen** (`WHERE block_id IS NOT NULL`): dve tretjini voženj
in vsi vlaki ga nimajo in v indeksu nimajo kaj iskati.

Tabele: `station`, `edge`, `trip`, `sched`, `service_day` (statika) ·
`obs` (dnevnik sprememb), `run` (zadnje stanje na postanek) · `weather` ·
`alert` + `alert_entity` (ovire) · `delay_report` (kje in koliko, po prevozniku).

Zajem piše **samo ob spremembi vrednosti**, in sprememba mora biti vsaj
`collector.OBS_MIN_DELTA_S` (60 s) od zadnje **zapisane**. Prikaz ima
ločljivost ene minute in sekund ne kaže nikoli, feed sam prilaga
`uncertainty: 120` -- sprememba za petnajst sekund torej ni sprememba, ampak
šum.

Pri vlakih to nič ne spremeni: ti poročajo v celih minutah in imajo **1,6
zapisa na postanek**. Pri mestnih avtobusih pa **23,3**, z mediano spremembe
15 sekund — 14 000 vrstic na uro za nihanje, ki ga ne pokažemo. Brez praga bi
vlaki + LPP dali ~1,5 GB na leto, z vsemi prevozniki pa 8,7 GB.

Primerjamo z zadnjo **zapisano** vrednostjo, ne s prejšnjo prebrano, da se
počasno lezenje sešteva in ne izgine. `run` ostane točen -- prag velja samo
za dnevnik.

**Dnevnik se obrezuje, `run` nikoli.** Tudi s pragom nastane z vsemi
prevozniki ~300 000 vrstic `obs` na dan; železnica jih naredi 4 000, torej 1 %.
Ena vrstica stane 79 B (41 B tabela + 38 B ključ, merjeno z `dbstat`) — torej
24 MB na dan in 8,7 GB na leto brez obrezovanja. Zato dve meji (`collector.prune_obs`, dnevno ob osvežitvi
vremena, ali `sztrack prune`): železnica 90 dni, avtobusi 14. Železnica je
jedro in njen dnevnik je poceni; pri avtobusih za prikaz zadošča `run`.
`run` je zgodovina, iz katere živijo statistika, "običajna zamuda" in
backtest -- te se ne briše.

Kar to pomeni za disk, izmerjeno (`dbstat`, 69 B na vrstico): `run` dobi
največ toliko vrstic, kolikor je na dan prevoženih postankov -- železnica
7 832, avtobusi 134 859. Na leto je to 0,2 GB proti 3,4 GB.

**Dolgoročno raste `run`, ne `obs`.** Dnevnik se z obrezovanjem ustali pri
~356 MB (železnica 90 dni = 28 MB, avtobusi 14 dni = 327 MB) in naprej ne
raste. `run` pa raste za vedno in ga po enem letu prekaša za desetkrat.
**Lega vozil ne stane nič**: `vehicle_now` je upsert na vožnjo in starejše od
ure se brišejo -- sled se ne hrani. Zavestna izbira, ne
spregled: `run` je edino, iz česar se da kasneje karkoli izračunati, in
brisati ga pomeni brisati projekt. Če bo kdaj treba, je najprej na vrsti
avtobusni `run`, ne železniški.
