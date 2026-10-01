---
paths:
  - "kajros/collector.py"
  - "kajros/alerts.py"
  - "kajros/gtfs.py"
  - "kajros/db.py"
  - "kajros/peroni.py"
  - "kajros/zamude_sz.py"
  - "kajros/iz_lege.py"
---

# Kaj feed pošlje in kje laže

Vse spodnje **izmerjeno na živem feedu**, ne domnevano. Kdor pravilo spreminja, naj izmeri znova in številko zapiše sem. Kar velja za strežbo (starost leg, predpomnilnik, meja žive vožnje): `.claude/rules/strezba.md`.

**Vlaki in avtobusi ne pošiljajo istega.** Izmerjeno na živem feedu, po prevozniku (delež postankov v enem klicu):

| | `arrival.delay` | `departure.delay` | absolutni čas | `uncertainty` | `vehicle.id` |
|---|---|---|---|---|---|
| SŽ | 100 % | 100 % | **0 %** | 100 % | ne |
| Arriva | 61 % | 100 % | 92 % | 0 % | da |
| Nomago | 42 % | 100 % | 97 % | 0 % | da |
| LPP | 39 % | 99 % | 100 % | 0 % | da |
| AP MS | 31 % | 100 % | 94 % | 0 % | da |

Iz tega dvoje:

* **Nikoli ne beri `stu.arrival.delay` naravnost.** Protobuf za neizpolnjeno polje vrne 0 = videti „točno". Ta napaka je v bazo zapisala 11 906 od 20 523 avtobusnih vrstic (58 %) kot točne; delež točnih **84,3 % namesto 71,2 %**. Železnica: nobena vrstica prizadeta. Uporabljaj `collector._delay_of()`: polje preveri, ob absolutnem času zamudo **izračuna** — preverjeno proti poročani odhodni zamudi: mediana razlike −9 s, 87 % v eni minuti.
* **Povsod `COALESCE(delay_dep, delay_arr)`, ne obratno.** `departure.delay` izpolnjen pri vseh prevoznikih ~100 %.

Feed pri vlakih nosi **samo `delay`**, brez absolutnega časa. Dejanski čas = `vozni red + zamuda`. Iz tega:

* **Ločljivost 60 s**, `uncertainty: 120`. Ne kaži sekund. Hitrosti samo na odsekih ≥ 5 km (`segment_speeds()` že filtrira).
* **Feed = drseče okno** — en klic da le postanke okoli trenutnega položaja. Celo vožnjo sestavljamo iz zaporednih pollov.
* **Meja med meritvijo in napovedjo = `stats.last_measured()`.** Vsak prikaz z zamudo jo mora upoštevati: kar je za zadnjim prevoženim postankom, je feedova napoved. Napaka že dvakrat -- v `/api/live` in v odhodni tabli, kjer je IC 502 pri +17 min v Borovnici na tabli v Litiji pisal **0 min**. Potnik bi bral, da je vlak točen.

* **Enotna zamuda čez vso vožnjo pri avtobusih sumljiva, a ni dokaz.** Merjeno na 3 636 vožnjah z ≥5 zajetimi postanki: **železnica** — enotna zamuda pogosta (19,7 % voženj), a **nikoli nad 60 min** (vlak ves čas dve minuti pozen). **Avtobusi** — enotnih le 2,2 % voženj, a **11 od teh 20 je nad 60 min**; od 19 avtobusnih voženj z zamudo nad uro jih je 11 takih. A6345: 7 800 s enako na vseh 46 postankih.

  **Prikaza za to (še) ni namenoma.** Feed te zapise pošilja z današnjim `start_date` → naša razrešitev obratovalnega dne ni kriva; enotna zamuda fizično mogoča: vozilo odpelje pozno, nato vozi po voznem redu. Devet dni in dvajset primerov premalo za pravilo, ki bi skrival podatke. Razrešila bi sled skozi `obs`: ali se postanki v zaporednih pollih premikajo. Do takrat velja samo `api.MAX_LIVE_DELAY_S`.

* **Iz `obs` se ne da ugotoviti, kdaj je bila vrednost nazadnje POTRJENA.** Dnevnik piše samo ob spremembi (`OBS_MIN_DELTA_S`) → zadnji zapis = zadnja *sprememba*, ne potrditev; feed isto vrednost pošilja naprej vsakih 30 s, mi je ne zapišemo. Posledica: za nazaj **ni mogoče ločiti meritve od napovedi, ki se ni nikoli popravila.** Živi prikaz reši `stats.last_measured()` (vozni red + zamuda ≤ zdaj), zgodovina ne more.

  Primer: RG 1604 ima v `run` na Ljubljani Zalogu 15, 2, 7, 14, 13, 11, 16 min — na **štirih od osmih dni natanko toliko, kolikor zamuda ob prihodu v Ljubljano** = feedova napoved izpred postaje. Na Litiji, 19 min pozneje: 0, 2, 6, 0, 1, 1, 2, ujema se z Zagorjem za njo. +13 na Zalogu in +1 v Litiji fizično nemogoče, a iz zapisa se ne vidi, katera je napoved.

  **Preizkušeno in ne pomaga:** vsiliti modelovo fiziko zaporedju napovedi (v točki j ne moreš biti bolj pozen, kot boš v j+1, plus rezerva vmes). MAE 1,92 → 1,96 min, delež v petih minutah 91,0 → 90,8 %. Rezerva je tudi v voznem času, ne le v postankih → pravilo prereže preveč pravih okrevanj.

* **Ne verjemi ničli, ki jo feed vrne za en klic.** Pri 14 % postankov z >2 zapisoma vzorec X, 0, X v razmiku ene minute. Zamuda med dvema klicema ne more pasti za več, kot je vmes minilo časa. `run` ničlo po zamudi ≥ 5 min sprejme šele, ko jo potrdi drugi zaporedni poll (`collector.is_zero_blip`); `obs` obdrži vse. Isto varovalo pri določanju lege vlaka -- sicer (vozni red + 0) pomeni, da je postanek že minil, in vlak na zemljevidu skoči naprej.
* **Odhodni zamudi na dolgem postanku ne verjemi.** Feed jo objavi kot ničlo, preden vlak pride, in pogosto ne popravi. Ujeto v živo 29. 8.: RG 1604 v Ljubljani prihod +19 in **odhod 0** — dve minuti stanja — na Ljubljani Zalogu 8 min pozneje **+5**, sedem minut stanja. Oboje hkrati ne drži; tokrat prvič vemo, katera stran je napačna: Zalog in Litija (+3) skladna med sabo, odhodna ničla ne z nikomer.

  Isti vzorec na tej postaji **pet dni od devetih**. `stats.typical_dwell()` zato dan šteje le, kadar sta naslednja dva postanka skladna (razlika pod 2 min), postanek pa izračuna iz **naslednjega** postanka, ne iz odhodne vrednosti. RG 1604 v Ljubljani: štirje uporabni dnevi od devetih, postanki 7, 9, 11 in 17 min proti 21 po voznem redu.

* **Zamuda ni ena številka na postanek: prihodna in odhodna se lahko razlikujeta.** Vlak ne odide takrat, ko pride. LP 4219 ima na Mostu na Soči po voznem redu **9 min postanka** (20:38 → 20:47, križanje na enotirni bohinjski progi): 29. 8. pripeljal +10, odpeljal +3 — stal 2 min namesto 9. Feed je oboje povedal (`prihod 600 / odhod 180`).

  Redko, a ne zanemarljivo: 406 postankov po voznem redu ima >2 min zadrževanja; v devetih dneh se prihodna in odhodna zamuda razlikujeta pri 1 307 postankih, od tega 362 za ≥5 min.

  Prikaz kaže `COALESCE(delay_dep, delay_arr)` = **odhodno**. Prav — potnika zanima, kdaj gre vlak naprej — a ena številka na vrstico naredi v grafu videti nemogoč prepad („kako je zamuda padla za osem minut med dvema postajama"). Zato: kadar se številki razlikujeta za ≥1 min, vrstica pokaže **obe** (`+10 → +3`) z razlago postanka; krivulja gre v naslednjo postajo na **prihodno** vrednost in pade **navpično** na postaji. Padec se je zgodil tam, ne na odseku.

* **Zamuda je izmerjena v prometnem mestu, ne nujno na postaji.** Ime mesta **imamo** -- v `SZ-DELAY-*` obvestilih ("Vlak EC 79 ima izjemno zamudo 161 min ob prihodu na postajo Sevnica"). `run` pozna samo voznoredne postanke → edini vir. Hrani se v `delay_report`.

  Prevoznikovo poročilo je tudi **svežejše od naše meritve**: na 64 primerjanih vožnjah novejše v 97 %, mediana razlike +40 s. Zato ga zemljevid in glava okna vožnje postavita pred našo vrednost -- a kraj in zamuda morata biti **iz istega vira**, sicer piše "Dobova" ob zamudi, izmerjeni v Sevnici.

  Zaporedje teh poročil = **dnevnik vožnje**, kakršnega nikjer drugje ni: IC 503 šel s +6 v Ormožu na +29 v Litiji, v Borovnici nadoknadil 8 min, do Postojne spet zdrsnil na +25. V oknu vožnje, napredni pogled.

* **Zgodovine ni nikjer.** Če je ne posnamemo sami, je ni.
* **Zakaj vlak zamuja, pove `service_alerts`.** `SZ-OVIRA-*` = dela na progi, nadomestni prevozi, združene garniture, vezani na `route_id` (1 : 1 s tripom → znamo pripeti na številko vlaka). Avgusta 2026 ~45 hkrati -- nadomestni prevoz Ljubljana–Logatec in Divača–Koper do 12. decembra, zapore enega tira Celje–Šentjur, Poljčane–Pragersko, Maribor–Hoče. **To pojasni, zakaj so zamude v zajetih dneh tako velike.**

* **Odpovedi niso strukturirane.** GTFS-RT ima `schedule_relationship` (CANCELED, SKIPPED), a SŽ ga ne uporablja -- v vseh zajetih zapisih `SCHEDULED`. Odpoved sporočijo z besedilom obvestila ("Vlak vozi samo do postaje Ljubljana Šiška", `effect = 6`). Zajem polje šteje in ob prvi neničelni vrednosti zavpije v dnevnik; prikaza namenoma še ni — bil bi prikaz za podatek, ki ne obstaja.

* **Ko feed izgubi vozilo, začne objavljati uro namesto zamude.** Za postanke, ki jih je vozilo *že prevozilo*, objavi vrednost, ki raste natanko minuto na minuto. Ujeto v živo 30. 8., LPP 25 (vožnja 452632, Poliklinika): ob 12:19:36 prihod +58 s, odhod +126 s — prava meritev z **različnima** vrednostma — ob 12:23:48 skok na +482, sedem klicev zapored rast natanko +60 s na +60 s do **+842 (+14 min)**, ob 12:30:29 vrnitev na +58/+126. Vozilo ves čas že davno mimo.

  V zajetem takih zaporedij **11 827 pri 947 vožnjah**. Pojasni tudi odprto vprašanje o **enotni zamudi čez vso vožnjo**: Nomagov N6571 s 27 060 s na vseh postankih je natanko ta vzorec, ujet po ustavitvi (4 od 12 takih voženj imajo zaporedje v `obs`; pri ostalih smo se priključili, ko je vrednost že zmrznila).

  Varovalka `collector.undoes_passing`: zavrne vrednost, ki bi postanek, za katerega smo **že zapisali meritev** o prevozu pred >120 s, prestavila nazaj v prihodnost. `obs` obdrži vse; čaka samo `run`.

  **Prva različica pravila je bila preširoka, merljivo.** Brez dodatnega pogoja je vzela pravo dvourno zamudo nočnega vlaka: EN 1276 je 28. 8. ob 00:03 imel za Celje zapisano `0/0` — feedova napoved pred prihodom, ne meritev — in ob 01:57 pravih +114 min. Zato **za dokaz o prevozu šteje samo zapis z različnima vrednostma za prihod in odhod**: te feed za nerazrešen postanek ne objavi. Ista past v projektu zapisana že dvakrat („ne verjemi ničli, ki jo feed vrne za en klic").

  Učinek `kajros repair` na 10 dneh zajema: **852 vrstic** v `run`, od tega 277 avtobusnih (mediana 51 min, največ 11 h) in **300 železniških** (mediana 14 min, največ 80 min). Povprečna zamuda pri avtobusih pade z 9,8 na 8,8 min, pri železnici s 6,7 na 6,5. Železniški primeri isti vzorec: LPV 2252 22. 8. ob 08:23 v Zagorju izmerjen s prihodom +2, odhodom +1; uro in četrt pozneje feed zanj objavil +79 min.

  **`repair` popravlja samo postanke, na katerih je varovalka sprožila.** Prej je čez `run` prepisal ves ponovljeni dnevnik — ker `obs` beleži le spremembe nad `OBS_MIN_DELTA_S`, je 16 696 vrstic zamenjal za do minuto grobejše, da bi popravil 4 217 pokvarjenih. Popravilo mora popravljati, ne glajenja.

* **Feed objavlja zamudo za vožnjo, ki se še ni začela — to je zamuda PREJŠNJE vožnje istega vozila.** LPP 25 (452632) 30. 8.: postanek Medvode novo naselje ima vozni red 11:41, feed pa je zanj od 11:11 objavljal +8, +10, +11, +12, +13 in ob 11:33:55 **+14 min** — vsakič čas, ki je bil še v prihodnosti = napoved. Ob 11:35:44 popravil na 0, avtobus odpeljal skoraj točno.

  `run` je obtičal na +14, ker je popravek zavrnil `is_zero_blip`: čaka na potrditev druge ničle, feed pa ničlo povedal **enkrat samkrat**, drseče okno šlo naprej. V grafu: devet postaj pri +14, nato **padec za 15 min v enem koraku** — tam se je končala napoved in začela meritev.

  Zato `collector.is_forecast`: vrednost, ki ob nastanku postanek postavlja v prihodnost, **ni meritev**, ničla, ki jo popravlja, ni blip. Merilo brez prostih parametrov.

* **Zgodovina poti mora biti zamejena na `trip_id`.** `stats.history()` je filtrirala po `train_no` in gradila profil po `stop_seq` — **zaporedni številki** postanka. Pri LPP liniji 25 (217 voženj) se je pod „postanek 2" sešlo *Medvode novo naselje* (drugi postanek proti Zadobrovi, povprečje +7 min) in *Novo Polje* (drugi postanek v **nasprotni smeri**, +1 min) — dva kraja pod eno oznako; stolpec je pisal „1 vožnja" nad 850 meritvami iz 25 voženj. Isto velja za devet vlakov s sezonskimi različicami.

  Železnica brez posledic: **0 od 663 številk z meritvami ima več kot eno vožnjo**. Avtobusi: 205 od 242, največ 42.

  Ista funkcija edina v projektu brala `delay_arr` pred `delay_dep` — obratno od pravila povsod drugod. Popravljeno.

* **Na izhodišču prihoda ni.** Feed ga za `stop_seq = 1` vseeno pošlje = smet: LPP 25 je 30. 8. na Medvodah naselju poročal prihod −267 s ob odhodu −2 s, na drugi vožnji istega dne −1771 s. Prikaz je sestavil „vlak je stal 4 min namesto 0 — izgubil 4 min" = zgodba o dogodku, ki se ni zgodil. `common.dwellSplit()` zdaj prvi postanek preskoči.

* **Ni** cen, sestave vlaka, zasedenosti. Mednarodni vlaki (EN/MV) pogosto brez realtime pokritja. **Tira v feedu ni** -- je s table SŽ, glej spodaj.

Izjema **vreme**: Open-Meteo ima arhiv za nazaj, zato ga ni treba zbirati vnaprej — `kajros weather` ga dopolni za že zajete zamude kadarkoli.

## Kar je pri avtobusih drugače

* **Veriga vozila = edini vir odgovora, kje je avtobus, ki se še ni začel.** `trips.txt` nosi `block_id` -- zaporedje voženj istega fizičnega vozila. Ga imajo **samo avtobusi** (vseh 789 voženj SŽ brez) in tudi tam le 7 547 od 20 736 voženj (36 %), v 1 385 blokih. Veriga resnična: med zaporednima vožnjama le 0,9 % prekrivanj, mediana postanka 14 min, v 69 % se konec ene ujema z začetkom naslednje. Isti `block_id` pri več `service_id` (788 od 1385), zato se sosed **išče po obratovalnem dnevu**, ne po `service_id`.

  Merjeno ob 20:22: od 25 voženj, ki so se začenjale v naslednji uri in pol, jih je 17 imelo prejšnjo vožnjo v bloku, 11 od teh svežo GPS lego. Edini način, da o avtobusu pred odhodom kaj povemo -- takrat ni ne zamude ne lege, vozilo pa obstaja.

  **Zamude prejšnje vožnje ne prenašaj naprej.** Izmerjeno na 195 parih zajetih voženj: prenos zamude MAE 4,53 min, „predpostavi točno" 2,29 min -- prenos **slabši od nevednosti**. Vozilo zamudo med vožnjama nadoknadi: kadar prejšnja zamuja ≥ 5 min (mediana 12 min) in ima vmes 15--60 min postanka, se na naslednjo prenese 11 %. Zato je prejšnja vožnja v prikazu **dejstvo o vozilu** („zdaj pri postajališču X, na prejšnji vožnji +1 min"), ne napoved odhoda; prikaz to pove.

* **`bikes_allowed` v celotnem GTFS ničla.** Vseh 20 736 voženj petih agencij ima `0` = „ni podatka". Polje obstaja, podatka ni -- uvoz ga ne bere, v shemi ga ni. Isto `wheelchair_accessible`, ki ga `trips.txt` sploh nima. Če se spremeni, je oboje en stolpec dela.

## Mestni LPP je drug feed in laže drugače

Mestnih linij LPP (1, 2, 3, 6, 11, 14, 20, 22, nočne) **v IJPP ni** — nosi le primestne (40–84). Uvoz iz LPP-jevega lastnega GTFS (`avl.lpp.si/transit/api/gtfs`, 31 prog), živi del iz `rt.gtfs.derp.si/sources/lpp/all` — **isti derp.si** kot IJPP, drug vir. Oboje odprto, brez ključa.

**`delay` v tem feedu vedno 0.** Izmerjeno dvakrat — nedelja 22:00 (2 721 postankov) in ponedeljkova konica 07:11 (2 604): nobena zamuda neničelna, `trip_update.delay` nikjer izpolnjen. **Kdor bi ga bral, bi zapisal, da mestni LPP nikoli ne zamuja.**

Zamuda v **absolutnih napovedanih časih** (1 882 od 4 517 postankov), kar `_delay_of()` že pokriva — bere `.time`, odšteje vozni red. Točno primer, za katerega funkcija obstaja.

Kakovost boljša od avtobusov v IJPP: mediana 0, p95 +7 min, p99 +23 min, nad 30 min 0,65 % in **vse iz ene same vožnje**; nad 2 h ničesar. IJPP-jev avtobusni feed imel 2 541 vrstic nad 4 h.

`trip_id` = trojni UUID (`service|?|trip`), ujemanje 1 : 1 z `avl.lpp.si`, **ne** z NAP. Uvoz okna osmih dni, ker ima LPP svojo vožnjo za vsak datum: cel mesec 62 989 voženj in 1,6 milijona postankov.

**Ujemanje 1 : 1 ni zagotovljeno.** 1. 10. 2026 je feed nosil 37–41 od ~225 voženj (17 %, linije 14, 6, 2, 27, 11, 7) s srednjim UUID-jem, ki ga ni v nobenem voznem redu: ne v zipu `avl.lpp.si` (izvoz 01:06, ves dan isti), ne v derpovem `lpp_gtfs.zip` z gitlaba (istih 63 669 voženj), ne v bazi izpred uvoza (varnostna kopija 03:32: 0 od 37). Tretji del (vzorec) je znan. Isti izvoz je na teh linijah dal nov id 424 današnjim vožnjam (6: 133, 2: 95, 11: 81, 14: 58, 27: 28, 11B: 22, 7: 7) — feed ne nosi ne starih ne novih, ampak tretje. Zajem zavrže zamudo **in lego**: linija 14 do 17. ure 47 ujetih voženj, 30. 9. ves dan 147. Para po vzorcu in uri ni: 18 od 37 brez enega samega časa, od ostalih 8 z enim kandidatom, ti z „zamudo“ do 29 min — ugibanje. Obvestila LPP za ta dan ni. Pregled je bil prav rdeč (`neznane`), pošta šla ob 08:37.

**Imena postajališč se pišejo drugače.** 12 % samih velikih črk („ČRNUČE"), IJPP normalno — ker vse teče po imenu, sta to dve postaji. Uvoz jih poenoti, a samo kadar sta zapisa tudi fizično na istem mestu (500 m): med 24 takimi pari jih je 14 v razmiku 3–215 m, deset 0,8–111,6 km; „Celje" in „Čelje" 112 km narazen. Glej `gtfs._poenoti_imena()`.

**Pošilja samo postanke PRED vozilom.** Izmerjeno 7. 9. 2026 s projekcijo lege vozila na postaje vožnje: vozilo 174 m od postaje 8 (od 26), `stop_time_update` samo za 9–26. Posledica težja od zapisa: pri mestnem LPP v `run` **nikoli ni meritve** — vedno le zadnja napoved pred prehodom (mediana 42 s pred njim, p90 27 s po njem). IJPP drugače: 56 % voženj ima v seznamu še prvi postanek, prevoženi postanki se osvežujejo.

Kdor bo računal kakovost napovedi po omrežjih, mora vedeti: pri LPP primerja napoved z napovedjo.

**Obvoz se konča tako, da ga feed neha pošiljati** — `end_ts` ostane v prihodnosti. „Postaja Bavarski dvor na obvozu — vozilo se ne bo ustavilo“ nazadnje v feedu 22. 9. 2026 ob 22:31, `end_ts` decembra; tabla najprometnejšega postajališča v Ljubljani ga kazala še 25. 9. Od 4 „veljavnih“ obvozov 2 taka. Zato `ingest_lpp()` ob vsakem branju zapiše `meta.lpp_obvestila_prebrana`, `for_stops()` pa obvoz pokaže samo, če viden največ 10 min pred tem branjem (`OBVOZ_REZERVA_S`). Meja = branje, ne ura: če zajem stoji, ostane zadnje znano. Ponoči, ko feed voženj nima, obvozov ni — tudi avtobusov ne.

## Nov vozni red, stari id-ji v feedu

**Feed v živo ima svojo kopijo voznega reda, ne osveži je hkrati z nami.**
22. 9. 2026: linije LPP 25, 12D, 15 (prevoznik 1118 v IJPP) dobile novo storitev `…260922…` z novimi id-ji od istega dne. Uvoz ob 04:23 stare vožnje spremenil v nagrobnike brez `sched`; feed pa vseh 12 vozil teh linij še popoldne javljal pod **starimi** id-ji (452xxx, 468xxx, 460xxx). Zajem jih zavrgel (`trip_id not in windows`), nove vožnje brez zamude in lege — 0 od 62 voženj linije 25 z vrstico v `run`.

Posledica na zaslonu: iskalnik poti ob 15:20 ponudil 25 s Tržnice Moste ob 15:28, LPP pisal, da pride čez 25 minut. Vozilo te vožnje ob 16:01 na koncu proge, ki bi jo po voznem redu doseglo ob 15:41; sosednja vožnja ob 16:14 v feedu +18 do +20 min.

**Nov vozni red ni le preštevilčen.** Vozni čas linije 25 padel s 65 na 52 minut, nekateri odhodi premaknjeni. Par zato ni „isti id + konstanta", ampak `gtfs.povezi_zamenjave()`: ista linija in prevoznik, skupen dan, vsaj 60 % postankov v istem vrstnem redu (po `stop_id`, ne `stop_seq`), najmanjši premik na **prvem skupnem postanku**, največ 10 min, vsaka nova vožnja največ enkrat. Zamenjava 22. 9.: **195 od 210** izginulih voženj dobi par (12D 85/85, 25 88/88, N0315 3/3, 15 pa 19/34 — odhodi premaknjeni za 15–30 min, para ne ugibamo). Mediana primerjave po vsej progi bi bila napačno merilo: pri pravih parih zaradi krajšega voznega časa naraste do 17 min.

**Zamuda se preračuna, ne prepiše** (`collector.zamuda_po_zamenjavi`): feedova vrednost = razlika do STAREGA voznega reda, zato se ohrani ura in odšteje nov. Staro 15:29 +20 = 15:49, po novem 15:28 → +21.

Preverjeno na arwenu po popravku: v minuti 161 vrstic `run` za linijo 25, neznanih v IJPP 5 od 538. Za Tržnico Moste zajem ob 16:36 dal vožnji s 16:31 +467 s, torej 16:38:47; LPP ob 16:37:30 pisal „čez 1 min".

**Id vožnje v IJPP feedu pride iz naprave na vozilu, ne od derp.si.** `derp-si/ijpp-rt` (gitlab) ga vzame iz NAP SIRI (`VehicleJourneyRef`, sistem Realis) in samo pretvori. Stari id-ji = vozilo ima še stari plan voženj — kdaj ga zamenjajo, ni odvisno od derp.si ne od nas.

**Linija 15 dokazuje, da par ni vedno mogoč.** LPP-jev lastni vozni red (data.lpp.si) se 22. 9. ujema z novim IJPP (Stanežiče → Sora 15 od 15 odhodov, obratno 13 od 14; izjema 15:35 pri LPP proti 15:50 v IJPP). Avtobus ob 17:45 pri LPP vozil v živo (`type 0`), v IJPP feedu ga ni **pod nobenim id-jem** — ne starim ne novim, v okolici proge nobenega vozila linije 15. Takega vozila nobeno pravilo povezovanja ne reši; edini živi vir zanj: data.lpp.si. Isti dan feed od 16:31 naprej za linijo 15 molčal.

**Vozilo vozi NOV vozni red, feed mu pripne najbližji stari id — prevod to popravi.** Izmerjeno 22. 9. na 14 vzorcih lege vozila, ki ga je feed vodil kot staro vožnjo 21:20 (460289): odmik od **novega** voznega reda (478164, 21:25) 0 do +2 min, od starega +3 do +7. Feedova zamuda +345 s, `run` po prevodu zapisal **+45 s** — vrednost, ki se ujema z resnico, ne s starim voznim redom. Dokaz, da je prevod prek ure pravilen tudi ko se vozni red premakne.

**Širiti mejo 10 minut se ne izplača.** Pri liniji 15 od 16:31 do 21:40 v feed prišla ena sama vožnja od šestih, ki bi jih večja meja lahko povezala, in ta bila povezana že tako. Manjka **vozilo v feedu**, ne pravilo.

**Zip brez prevoznika se zavrne** (`gtfs.izginuli_prevozniki`). 28. 9. 2026 je DUJPP (`dujpp.si/gtfs/dujpp-ijpp.zip`, derp.si ga le prenese) objavil 783 prog SŽ in **0 voženj**; uvoz ob 04:22 pobrisal vozni red vseh 726 vlakov, tabla za Ljubljano „postaje ne poznam“. Feed zamud in leg ob 08:13 ni imel nobenega vlaka (0 od 560 vnosov) — z uvozom tega ne popraviš, stari vozni red pa vsaj pokaže odhode. Meja je nič, ne delež: LPP v IJPP med 30. 8. in 28. 9. padel s 3 060 na 556 voženj (−82 %) brez opažene napake — prag v deležu bi bil ugibanje.

Isti zip je imel **pomešane trase** in izgubil LPP primestni: prvi postanek več kot 2 km od začetka trase pri 74–100 % voženj vsakega avtobusnega prevoznika (Arriva 6 429 od 7 821; zip 30. 8.: 1–7 %), LPP v IJPP za 28. 9. 281 voženj namesto 1 215. Posledica: `iz_lege` obstal (vozilo 55–145 km od „svoje“ trase), napačne trase na zemljevidu, 33 voženj v feedu brez voznega reda. Zato druga varovalka `gtfs.tuje_trase`: prevoznik z ≥ 20 vožnjami s traso in več kot polovico tujih → zip zavrnjen. Preverjeno na obeh zipih: 28. 9. zavrnjen v 9 s, 30. 8. uvožen.

**Par nastane samo ob uvozu**, ker je stari vozni red takrat še v bazi — pozneje ga ni. Če je uvoz že tekel brez tega (arwen 22. 9.): `kajros zamenjave <razpakirana varnostna kopija izpred uvoza>`.

**Kar še ostane neznano, se šteje.** `ingest` vrne `neznanih`, zajem zapiše v `meta` (`rt_neznanih`, `lpp_rt_neznanih`, oblika `n/vseh`), pregled za skrbnika pokaže med zdravjem. Ob zamenjavi 22. 9. v IJPP 16 od 662 (2,4 %); prag za rdečo 2 %. Brez števca se je napaka videla šele, ko je potnik čakal na avtobus.

**Obratne napake števec ne vidi: vožnje, ki jih feed zamud sploh ne nosi.** Od 21. 9. 2026 IJPP `trip_updates` nima **nobene** vožnje z veljavnostjo od 21. 9. naprej — Nomago ~430 na dan (11 % njegovih), Arriva 51 — v `vehicle_positions` pa ista vozila so, pod novimi id-ji (25. 9. ob 11:16: 22 vozil, nobeno v `trip_updates`). Vožnje z veljavnostjo od 7. in 14. 9. imajo zamude normalno. Najverjetneje derp.si za zamude ima star vozni red: lega ga ne rabi, zamuda na postanek pa ga. Tabla pri teh vožnjah pisala „brez podatka“, četudi vozilo vozilo in videli na zemljevidu. Izmerjeno in razčlenjeno v `docs/MERITVE.md` (25. 9. 2026).

Pregled to kaže kot `lega_brez_zamude` (`collector`), trojka [ne v feedu zamud, brez vsake zamude, vozil z lego] po prevozniku. Števca dva, ker vrzel zapolnjujemo sami in prvi sicer ne bi več videl napake vira.

**Kar feed zamud izpušča, izmerimo iz lege** (`iz_lege.py`): lega na traso, prehod postanka med dvema legama, največ 60 s narazen, zapis v `run` in `obs` kot iz feeda, s časom lege po prehodu. Na vožnjah z obojim se s feedom ujema v 92 % na minuto natančno (izmerjeno v `docs/MERITVE.md`). Izhodišča ne meri. Teče samo s strežnikom: `kajros collect` na malini leg ne bere (`KAJROS_POSITIONS=0`), izklop `KAJROS_ZAMUDA_IZ_LEGE=0`. Vožnja, ki jo feed zamud v zadnjih 5 min omeni, gre mimo -- iz lege se piše samo tam, kjer feeda ni. Odgovor 304 = ista vsebina: vožnje zadnjega branja tega vira ostanejo "v feedu" (`iz_lege.feed_nespremenjen`).

**Zgodovina gre čez zamenjavo** (`db.PREDNIKI_SQL`): običajna zamuda, okno vožnje in model štejejo tudi meritve stare vožnje, prevedene na nov vozni red. Brez tega je bila vožnja z novim id-jem tri dni „brez podatka“.

## Vožnja, obratovalni dan in dnevnik

`trip.start_s` / `trip.end_s` = **prvi odhod in zadnji prihod vožnje**, izpeljana iz `sched`, shranjena v `trip`, ker ju rabi najbolj vroča poizvedba — "kaj se zdaj vozi". Polni ju `db.fill_trip_window()` ob uvozu GTFS in migraciji. Kdor vstavlja vožnje mimo uvoza (test, ročni popravek), ju mora zapolniti, sicer vožnja **ni na seznamu živih**.

**Feed občasno objavi vožnjo z JUTRIŠNJIM obratovalnim dnem.** Izmerjeno 31. 8.: 44 vrstic v `run` (0,026 %) v **dveh** vožnjah ima `service_date` v prihodnosti — Nomagov N6507 z voznorednim odhodom 04:25 in enotno zamudo 48 240 s (13,4 h) na vseh postankih. Isti vzorec kot pri N6571: feed zamenja prometni dan, razliko objavi kot zamudo.

**Pravila za to ni namenoma.** Vseh 44 vrstic ima zamudo nad 6 h, zato jih `api.MAX_LIVE_DELAY_S` že drži izven živega prikaza. Dve vožnji = premalo za varovalko ob zajemu — isti razlog kot pri enotni zamudi čez vso vožnjo. Meri se z `SELECT COUNT(*) FROM run WHERE service_date > date('now','localtime')`; če delež zraste, je čas za pravilo.

**Vožnja z zamudo nad `api.MAX_LIVE_DELAY_S` (6 h) ni živa.** Pravilo prikaza, ne pospešek. Pri železnici ni zamude čez tri ure (najhujša EC 79 z 2,9 h); pri avtobusih je nad šest ur 0,67 % vrstic in te niso zamude — Nomagov N6571 je imel 27 060 s enako na vseh 44 postankih vožnje ob 04:15 = feedova zamenjava prometnega dne.

`trip.block_id` = veriga voženj istega vozila (glej zgoraj). Indeks `trip_block` je **delen** (`WHERE block_id IS NOT NULL`): dve tretjini voženj in vsi vlaki ga nimajo, v indeksu nimajo kaj iskati.

Tabele: `station`, `edge`, `trip`, `sched`, `service_day` (statika) · `obs` (dnevnik sprememb), `run` (zadnje stanje na postanek) · `weather` · `alert` + `alert_entity` (ovire) · `delay_report` (kje in koliko, po prevozniku).

Zajem piše **samo ob spremembi vrednosti**, sprememba pa mora biti vsaj `collector.OBS_MIN_DELTA_S` (60 s) od zadnje **zapisane**. Prikaz ima ločljivost ene minute, sekund ne kaže nikoli, feed sam prilaga `uncertainty: 120` -- sprememba za 15 s = šum, ne sprememba.

Vlaki poročajo v celih minutah: **1,6 zapisa na postanek**. Mestni avtobusi **23,3**, z mediano spremembe 15 s — 14 000 vrstic na uro za nihanje, ki ga ne pokažemo. Brez praga bi vlaki + LPP dali ~1,5 GB na leto, z vsemi prevozniki 8,7 GB.

Primerjava z zadnjo **zapisano** vrednostjo, ne s prejšnjo prebrano, da se počasno lezenje sešteva in ne izgine. `run` ostane točen -- prag velja samo za dnevnik.

**Dnevnik se obrezuje, `run` nikoli.** Tudi s pragom z vsemi prevozniki nastane ~300 000 vrstic `obs` na dan; železnica 4 000 = 1 %. Vrstica stane 79 B (41 B tabela + 38 B ključ, merjeno z `dbstat`) — 24 MB na dan, 8,7 GB na leto brez obrezovanja. Zato dve meji (`collector.prune_obs`, dnevno ob osvežitvi vremena, ali `kajros prune`): železnica 90 dni, avtobusi 14. Železnica = jedro, njen dnevnik poceni; pri avtobusih za prikaz zadošča `run`. `run` = zgodovina, iz katere živijo statistika, "običajna zamuda" in backtest -- se ne briše.

Disk, izmerjeno (`dbstat`, 69 B na vrstico): `run` dobi največ toliko vrstic, kolikor je na dan prevoženih postankov -- železnica 7 832, avtobusi 134 859. Na leto 0,2 GB proti 3,4 GB.

**Dolgoročno raste `run`, ne `obs`.** Dnevnik se z obrezovanjem ustali pri ~356 MB (železnica 90 dni = 28 MB, avtobusi 14 dni = 327 MB), naprej ne raste. `run` raste za vedno, po enem letu ga prekaša desetkrat. **Lega vozil ne stane nič**: `vehicle_now` = upsert na vožnjo, starejše od ure se brišejo -- sled se ne hrani. Zavestna izbira, ne spregled: `run` je edino, iz česar se da kasneje karkoli izračunati, brisati ga = brisati projekt. Če bo treba, najprej avtobusni `run`, ne železniški.

## Obvestila SŽ: kaj feed res pošlje (izmerjeno 4. 9. 2026)

* **Razčlemba živih zamud pokrije vse.** 474 `SZ-DELAY` obvestil, **474 razčlenjenih (100 %)**. Regex v `parse_delay_text()` ni približek, ampak opis oblike, ki jo SŽ res uporablja.
* **Poln zapis je v `description`, ne v `header`.** Glava „Vlak zamuja 13 min“ — brez številke vlaka in postaje. `ingest` bere `parse_delay_text(desc) or parse_delay_text(header)`; vrstni red ni kozmetičen: pri obratnem se razčleni **nič**.
* **Vsa poročila so `prihod`.** 31 196 vrstic v `delay_report`, nobene z `odhod`; izjemnih (`severe`) 2 369. Veja za odhod v kodi doslej ni nikoli stekla — ostane, ker je poceni, a nanjo se ne zanašaj.
* **Vrste „drugo“ ni.** Vsa obvestila `SZ-DELAY` (474) ali `SZ-OVIRA` (123); `_kind()` tretje veje doslej ni potreboval.
* **Vsako obvestilo ima natanko eno obdobje veljavnosti.** Vseh 102 v živem feedu; glej varovalo `vec_obdobij` v `ingest()`.

## Lege so stare, in to ni naša zamuda

`seen_ts` = `vehicle.timestamp` **iz feeda**, ne čas našega branja — namenoma, ker prikaz trdi „lega stara N" in mora biti to res starost meritve.

Pri mestnem LPP je normalna starost **57–147 s**: lega je ob pakiranju stara mediano 35 s, feed se osveži šele vsakih ~90 s (vsa vozila hkrati, v paketu), naš 30-sekundni cikel doda do 30 s. Izmerjeno 7. 9. 2026, podrobnosti in razrez po členih v [docs/MERITVE.md](../../docs/MERITVE.md).

Preden kdo išče napako pri sebi: primerjaj `seen_ts`, ki ga strežemo, s `vehicle.timestamp` v feedu ta hip. Ob zadnji meritvi ujemanje **99 od 99**.

LPP feed **nima `ETag` ne `Last-Modified`**: pogojna zahteva ni mogoča, vsak zajem prenese vseh 315 kB.

## Tir s table SŽ (`peroni.py`, od 25. 9. 2026)

Ne GTFS ne NeTEx ne feed tira nimajo. Ima ga tabla prihodov in odhodov na potniski.sz.si (za Cloudflarom); beremo jo prek `api.modra.ninja/sz` („improviziran API“ tretje osebe, isti vir uporablja brezavta.si). Zato:

* **Tir je dodatek.** Pokaže se samo, kadar ga je potrdilo ZADNJE branje postaje in to branje ni zamujeno za več kot dva razmika (`peroni.tiri`). Ugasne se s `KAJROS_PERONI=0`, nič drugega ne sme pasti.
* **Ena tabla je 13-17 s** (predpomnilnik vira 60 s). Bere jo SVOJA nit, ena postaja naenkrat -- v zajemni zanki bi zamaknila zamude.
* **Tir je lastnost postaje, ne vlaka.** Od 20 izmerjenih postaj ga je 14 imelo pri vseh vlakih, 6 (Jesenice, Novo mesto, Kranj, Dobova, Trbovlje, Škofja Loka) pri nobenem. Postaja brez tira se preveri enkrat na dan.
* **Vseh postaj na deset minut ena nit ne zmore** (~20 s na tablo, 266 postaj). Razmik po prometu: Ljubljana, Maribor, Celje vsakih `KAJROS_PERONI_SECONDS` (600 s), majhne postaje redkeje, najdlje 2 h.
* **Tabla kaže samo vlake, ki še pridejo** (tudi zamujene), zato se bere čez ves dan. Mednarodnih 1472, 210, 211, 79, 350 na njej ni.
* **Ključ = koledarski dan table + številka brez vrste**, ne prometni dan, ne `trip_id`: vlak ob 00:30 je na tabli naslednjega dne.
* **Tir se čez dan spreminja.** `prvi` ostane, `tir` se posodablja; prikaz razliko napiše z besedo („prej 6-A“). brezavta.si kaže „običajni“ tir iz zgodovine; v Ljubljani se je razlikoval od table pri 8 od 121 vlakov.

## Zamude vlakov z zemljevida SŽ (`zamude_sz.py`, od 28. 9. 2026)

Drugi vir poleg derp.si. Tistega dne je derp.si z zipom DUJPP izgubil vse vlake (zamude, `SZ-DELAY`, surovi `…/data/raw/sz/rt/trip-updates` 0 vnosov) — **derp.si pri vlakih visi na voznem redu DUJPP**. Zemljevid vlakov s potniski.sz.si (`api.modra.ninja/sz/lokacije`, isti posrednik kot tir) vlak vodi po **številki**, zato ga zip ne prizadene.

Izmerjeno 28. 9. 2026, 08:59–09:08, 17 branj po 30 s:

* **`raw_odhod` = voznoredni odhod s postaje PRED `naslednja_postaja` + `zamuda_min`**, na minuto, pri vseh 12 ročno preverjenih vlakih. Zamuda je torej odhodna zamuda zadnjega prevoženega postanka; enakost je hkrati preizkus, da je vlak pripet na pravo vožnjo in dan (sezonske različice z isto številko). Brez ujemanja se vlak ne pripne.
* **Pripetih 574 od 647 vrstic vlakov** (89 %). Ostanek brez izjeme upravičen: 42 z odhodom v prihodnosti (vlak stoji na postaji ali pred izhodiščem — zemljevid ob prihodu že pokaže naslednjo postajo), 31 brez naslednje postaje (na cilju). Nadomestni avtobusi (34) se ne štejejo: zamuda 0 v točki postaje je izračun.
* Odgovor se spremeni ~vsako minuto (9 različnih v 17 branjih). Zamuda se med odsekom lahko popravi (10 od 556 zaporednih parov) — vrstica v `sz_zamuda` in `run` drži zadnjo, kot pri derp.si.

**Kam gre:** vsaka pripeta vrednost v `sz_zamuda` (zadnje stanje na postanek). V `run` in `obs` samo, kadar derp.si vožnje ne nosi (`iz_lege.brez_feeda`, ista meja kot zamuda iz lege) — tedaj `v_run = 1`. Kadar nosita oba, `run` ostane derp.si-jev in `kajros primerjava` / pregled („ujemanje virov · 24 h“) pokažeta razhajanja. **Kdo ima prav, še ni odločeno**: primerjav do objave ni bilo, ker derp.si vlakov ni imel. Nit čaka, da zajem derp.si prebere feed (`iz_lege.feed_prebran`), sicer bi bil ob zagonu vsak vlak „samo SŽ“.

## Napaka pisanja: najprej `conn.rollback()`

Vsaka nit ima svojo povezavo in vsak `except` okoli pisanja najprej razveljavi. Python ob napaki transakcije ne zapre; prvo branje v njej zamrzne posnetek, nato vsako pisanje vrne „database is locked“ (SQLITE_BUSY_SNAPSHOT) — za vedno, čakanje ne pomaga. 1. 10. 2026 je nočno vzdrževanje ob 3:30 drlo pisanje dlje od 30 s: nit zemljevida SŽ stala 4,3 h, WAL zrasel na 5,4 GB (za odprtim posnetkom ga ni mogoče prepisati), disk na 8 %. Od takrat `journal_size_limit` 64 MB v `db.connect()`, da se WAL po ponastavitvi skrči. Preizkus: `test_nit_po_zaklenjeni_bazi_ne_obstane`.
