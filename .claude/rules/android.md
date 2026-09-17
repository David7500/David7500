---
paths:
  - "android/**"
---

# Aplikacija za Android

Nativni ovoj z WebView na `kajros.app`. Vmesnik ostane **en sam — spletni**;
nativno je samo tisto, česar splet ne zmore. To je zaenkrat ena stvar: budilka.

## Zakaj tako in ne drugače

| možnost | zakaj ne |
|---|---|
| PWA | alarma ob določeni uri ne zna. `Notification Triggers` je bil v Chromu preizkušen in **nikoli izdan**, `Periodic Background Sync` dela v urah in je vezan na Chrome, Web Push gre skozi FCM (Google) in bi zahteval buden strežnik |
| TWA | zahteva Chrome kot ponudnika. Telefon je razgooglana Volla 22 s Fennecom — TWA bi pomenil namestiti Chromium |
| GeckoView | most do JavaScripta je z njim moreč; `addJavascriptInterface` na WebView je ena vrstica. To je bilo odločilno, ne hitrost |
| service worker | David: „ne zaenkrat pač nič ne pokaže". Posledica je, da nedosegljivega strežnika ne pokrije splet — pokrije ga **nativni zaslon napake** |

Razdeljevanje: **prenos s strani** `kajros.app/android`. Brez trgovine in brez
Googlovega računa.

## Meja zaupanja je ena sama funkcija

`Nastavitve.izvor()` pove, katera stran je naša. Vse drugo jo bere:

* povezava zunaj tega izvora se **ne odpre v WebView**, ampak v brskalniku;
* dovoljenje za lego dobi samo ta izvor;
* most (`window.Kajros`) ga bo preveril ob vsakem klicu.

To ni pedantnost: `addJavascriptInterface` je viden **vsaki** strani, ki jo
WebView naloži. Zato so tudi sheme, ki smejo ven, naštete — `intent:` ni med
njimi, ker je znana pot, s katero tuja stran odpre poljubno dejavnost.

Razčlenjevanje gre skozi `java.net.URI`, **ne** `android.net.Uri`: prvi je
navaden JVM in ga je mogoče preizkusiti brez naprave. Varnostno pravilo brez
testov ni pravilo.

## Lastna lega: WebView si dovoljenje zapomni sam

To je stalo tri dni tihe okvare. Izmerjeno na telefonu 9. 9. 2026:

```
WebViewProfilePrefsDefault.xml  AwGeolocationPermissions%https://kajros.app/ = true
dumpsys package app.kajros      ACCESS_FINE_LOCATION: granted=false … ONE_TIME
```

Sistemsko dovoljenje je bilo „samo tokrat“ in je poteklo; WebViewov **lasten**
zapis je ostal. Ker je ta rekel „dovoljeno“, `onGeolocationPermissionsShowPrompt`
ni bil vec poklican — in to je edini kraj, kjer aplikacija zaprosi Android.
Lega je odpovedala za vedno in se sama ni mogla rešiti.

Zato: **`retain` je vedno `false`**, ob zagonu pa
`GeolocationPermissions.getInstance().clearAll()`. Vir resnice je Androidovo
dovoljenje, ne WebViewov spomin. Preverjeno: po popravku ostane shramba prazna
(`<map />`) tudi potem, ko potnik lego dovoli.

## Razdeljevanje: zakaj ni trgovine (12. 9. 2026)

| trgovina | ovira |
|---|---|
| F-Droid (glavni), IzzyOnDroid | sprejmeta **samo prosto programje**; koda je zaprta (3. 9. 2026) |
| Google Play | račun, 25 $, identiteta, **12 preizkuševalcev × 14 dni** (osebni račun po 13. 11. 2023), AAB, od 31. 8. 2026 `targetSdk` 36 |
| Accrescent | zaprto kodo sprejme, a rabi pregled in `bundletool` — ostaja odprto |

Zato **stran `/android`**: podpisan APK, vsota SHA-256, navodilo v treh
korakih. Pot: `android/objavi.sh` zgradi in podpiše, prepiše APK v mapo z
`razlicica.json`, `rsync` jo pošlje na strežnik, `api.py` mapo streže na
`/prenos` (`config.PRENOS_DIR` = `${KAJROS_DATA_DIR}/prenos`). Če mape ni,
poti ni, stran pa pove, da izdaje še ni.

Mapa je v podatkovnem imeniku in ne v `/srv`, ker je ta po `brez-sudo.sh` že
skupinsko pisljiv in ga enota sme brati — objava je zato navaden `rsync` kot
`david`, brez sudota in brez spremembe enote v `/etc`. Mount nastane ob
zagonu, zato je po **prvi** objavi potreben restart storitve.

**Podpisni ključ je trajna identiteta aplikacije** (`podpis.sh`,
`~/kajros-android/podpis/`): brez njega posodobitve ni in vsak uporabnik bi
moral aplikacijo odstraniti in namestiti znova. V gitu ga ni in ne sme biti;
`build.gradle.kts` bere geslo iz `podpis.properties` **zunaj** repozitorija,
in če datoteke ni, gradnja še vedno teče in naredi nepodpisan APK — merjenje
velikosti zato ne zahteva ključa.

**Dvig `versionCode` je edini pogoj, da posodobitev sploh pride do telefona.**
`versionName` je za ljudi in ne pomeni ničesar.

**Zunaj trgovine mora na posodobitev opozoriti aplikacija sama**
(`Posodobitev.kt`): enkrat na dan vpraša `/api/android/razlicica` in ob večji
kodi pokaže vrstico s povezavo na stran. Dvoje je pri tem pravilo:

* **Nič se ne prenese ali namesti samo.** `REQUEST_INSTALL_PACKAGES` ta
  aplikacija nima in ga ne sme dobiti — tiho nameščanje iz omrežja je natanko
  to, pred čimer Android svari.
* **Naslov iz odgovora gre skozi `Nastavitve.jeNas()`.** Odgovor je podatek s
  strežnika; tudi naš strežnik ne sme odpreti povezave drugam samo zato, ker
  jo je vrnil. Ista meja zaupanja kot pri povezavah v WebView.

**Zaradi preverjanja ob zagonu je 2027 vreden zaznamka**: Google od
30. 9. 2026 zahteva **preverjenega razvijalca** za namestitev na certificiranih
napravah (Brazilija, Indonezija, Singapur, Tajska; globalno 2027). Naprave brez
Googlove certifikacije (razgooglana Volla) to ne zadeva, navadnega telefona pa
bo. Takrat bo treba izbrati znova; do tedaj ta pot dela.

## Dovoljenje za lego skrije aplikacijo napravam brez GPS

`ACCESS_*_LOCATION` pomeni **privzeto `uses-feature required="true"`** —
izmerjeno z `aapt2 dump badging`:

```
uses-implied-feature: name='android.hardware.location'
  reason='requested ACCESS_COARSE_LOCATION … ACCESS_FINE_LOCATION permission'
```

Trgovina tako aplikacijo skrije vsaki napravi brez GPS, čeprav brez lege dela
vse razen gumba „kje sem“. Zato so v manifestu tri izrecne vrstice
`uses-feature … required="false"` (`location`, `location.gps`,
`location.network`). To se ne vidi nikjer, dokler se ne pogleda z `aapt2`.

## Nič odvisnosti

Ne AndroidX, ne `appcompat`. Vse potrebno je v ogrodju od API 26: `WebView`,
`AlarmManager`, `NotificationChannel`, `Ringtone`. Zato je objavljeni APK **70 kB**
(71 822 B podpisan, 61 854 B pred podpisom; 12. 9. 2026, prej 50 kB 7. 9. in
28 kB pred budilko z vmesnikom) in v njem ni
**nobenega** Googlovega niza — preverjeno z `aapt2 dump strings`, 0 zadetkov za
„google", „firebase" in „gms".
Če se v `dependencies` kdaj pojavi vrstica, mora biti zraven razlog.

`-keepclassmembers` za `@JavascriptInterface` v `proguard-rules.pro` **mora
ostati**: R8 bi metode mostu sicer preimenoval in `Kajros.nastavi()` bi tiho
ne obstajal — samo v izdajni različici.

## Orodja puščajo, in to je treba loviti sproti

`orodja.sh` postavi vse v `~/kajros-android` in **dokaže**, da drugod ni nič.
Trije primeri, ki jih je dokaz ujel, so v [docs/MERITVE.md](../../docs/MERITVE.md).
Najhujši: AGP ob vsaki gradnji naredi `~/.android/analytics.settings` z
obstojnim `userId`; premakne ga **samo `-Duser.home`**, ne `ANDROID_USER_HOME`
in ne `HOME`.

Zato ta dokaz ni enkraten — `zgradi.sh` ga ponovi ob vsaki gradnji in pade,
če kaj uide.

**Ista izolacija je enkrat že skrila podpisni ključ.** `build.gradle.kts` je
mapo iskal prek `System.getProperty("user.home")`, ta pa je zaradi
`-Duser.home` **lažni dom** (`~/kajros-android/domov`). Ključ je obstajal,
gradnja ga ni našla in je **tiho** naredila nepodpisan APK — brez opozorila,
ker je nepodpisana izdaja veljavna. Zato se pot bere iz okolja (`KAJROS_PODPIS`,
`KAJROS_ANDROID`, `HOME`), `zgradi.sh izdaja` pa po gradnji izpiše prstni odtis
podpisa: ime datoteke (`app-release.apk` proti `app-release-unsigned.apk`) je
edini drugi znak, in tega je lahko spregledati.

Spremenljivk okolja ne dodajaj na slepo: AGP pade, če najde več različnih poti
do svoje mape (`ANDROID_PREFS_ROOT`, `ANDROID_SDK_HOME`, `ANDROID_USER_HOME`).
Emulator pa `ANDROID_USER_HOME` sploh ne bere in rabi `ANDROID_AVD_HOME`.

## Preverjanje

```bash
./zgradi.sh                 # testi JVM + APK + revizija domačega imenika
KAJROS_EMULATOR=1 ./orodja.sh && ./zgradi.sh emulator
./zgradi.sh namesti
adb exec-out screencap -p > ../posnetki/x.png
```

Emulatorjeva slika je `default`, **ne** `google_apis` — AOSP brez Googlovih
storitev, ista izbira kot pri telefonu.

`variations_seed_loader.cc: Seed missing signature` v dnevniku ni naša napaka:
to je WebViewova lastna konfiguracija, ki je na AOSP ni.

## Budilka

Davidovo pravilo, dobesedno: *„uporabnik vnese, koliko časa (x minut) preden
pride vlak naj zazvoni (upošteva se zamude); če pa ni povezave, potem zazvoni
x minut preden je napovedan vozni red"* in *„uporabnik ne sme zamuditi, raje
kej rezerve, če ni zihr"*.

Vse, kar budilka rabi, je **shranjeno lokalno** — predvsem voznoredna ura.
Če bi jo bilo treba pridobiti, bi nadomestna pot rabila ravno tisto, česar
takrat ni.

**Aritmetika je v `Ura.kt` in je čista** (brez Androida), da jo je mogoče
preizkusiti brez naprave. Tam je vse, kar je mogoče narediti narobe.

### Do seznama budilk se pride samo s prve strani

Na domači strani je **prva ploščica** in kaže naslednjo budilko s stikali
(`home.js` bere `Most.seznam()`, dotik odpre `odpriBudilke()`); glej
`strani.md`. V glavi drugih strani je **ni** (odločeno 14. 9. 2026): budilka se
nastavi v oknu vožnje, seznam pa je pregled. Tudi „naslednja budilka" v
vrhnjem meniju sistema odpre seznam (`AlarmClockInfo` → `BudilkeDejavnost`),
ne glavne strani, ki o budilki ne pove ničesar.

Ura v vrhnjem meniju je **prvo preverjanje** (10 min pred zvonjenjem), ne
zvonjenje — `setAlarmClock` je ena budnica za oboje, glej `Nacrtovalec`.

### Budilka 14. 9. 2026 ni zbudila — štiri napake naenkrat

RG 318, Ljubljana Polje 7:31, X = 20 + 3 min rezerve, vlak +20 min. Obvestilo
ob 7:08 „zamude ni bilo mogoče preveriti — zvonim prej", zvonjenje šele, ko je
potnik ob 7:30 sam vzel telefon, in po „Ustavi" znova in znova.
Sistemski dnevnik je bil zvečer že prepisan; vzrok je sestavljen iz
`dumpsys appops`, `dumpsys alarm` in kode, nato potrjen s preizkusom na telefonu.

1. **Veljavnost je bila merjena od voznega reda, ne od zvonjenja z zamudo.**
   Preverjanje je teklo na 5 minut (do zvonjenja jih je bilo še 20), meja pa
   je bila izračunana od 7:08 in je znašala 75 s — vsak podatek je bil izpad.
   Zdaj `Ura.veljavnost(do, starost)` = korak ob prihodu podatka + zdajšnji
   korak + 15 s, oboje od ure zvonjenja z zamudo. Test:
   `velika zamuda ne skrajsa veljavnosti na vozni red`.
2. **Bližnjica „čas je tu, zvoni" je zazvonila brez vprašanja strežnika.** Zdaj
   zvoni brez omrežja samo, kadar ura stoji na sveži zamudi ali odlogu.
3. **Zvonil je zaslon, zaslon pa se ni odprl.** `USE_FULL_SCREEN_INTENT: deny`
   — Android 14+ ga sam da le budilkam **iz trgovine**. Obvestilo kanala brez
   zvoka je bilo tiho. Glej naslednji razdelek.
4. **Zanka po „Ustavi".** `prestavljena()` je iskala naslednji odhod po
   *zdaj* — ta je bil isti vlak ob 7:35, zvonjenje v preteklosti, torej takoj
   znova. Zdaj po `max(zdaj, voznoredni)`. Test: `BudilkaTest`.

### Zvoni obvestilo, ne aplikacija

Po popravku 3 je zvok najprej predvajala storitev v ospredju — in Android 16
ga je utišal. Izmerjeno na telefonu 14. 9. 2026 ob 20:03:55:

```
AS.AudioService: AudioHardening background playback would be muted for app.kajros (10024), level: full
AudioPlaybackConfiguration … u/pid:10024 state:started … usage=USAGE_ALARM … muted
```

Storitev, zagnana iz ozadja, za zvok ni „v ospredju". Zato zdaj zvok predvaja
**sistem**: kanal `budilka` ima zvok `DEFAULT_ALARM_ALERT_URI` z
`USAGE_ALARM`, obvestilo `FLAG_INSISTENT` (ponavlja, dokler obvestila ni) in
`FOREGROUND_SERVICE_IMMEDIATE`. Preizkus ob 20:39: zazvonilo, `AudioHardening`
v dnevniku ni bilo, „Ustavi" ob 20:40:09, brez ponovitve.

`ZvonjenjeStoritev` (vrsta `systemExempted`, pripada aplikacijam z
`USE_EXACT_ALARM`) ostane samo zato, ker obvestila storitve ni mogoče podrsati
stran — odmahnjena budilka je tiha budilka. Gumba „Ustavi" in „Še 2 minuti" sta
v obvestilu, ker zaslona brez dovoljenja ni.

**Kanalu zvoka ni mogoče spremeniti, ko obstaja.** Zato je kanal preimenovan
(`zbudi` → `budilka`) in stari se ob vsakem `kanali()` izbriše.

Dovoljenje za cel zaslon se zdaj zaprosi (`zahtevajZaBudilko`, 14+:
`ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT`), stran ga pozna kot `cel_zaslon`
v `dovoljenja()`, seznam budilk pa pove, kadar manjka.

### „Strežnik nima podatka" ni izpad povezave

Drugi preizkus (LPV 2002, Ljubljana je začetna postaja) je zazvonil
preventivno ob prvem preverjanju: `vozi, zamuda neznana → preventiva`. Tabla
za vlak, ki se še ni premaknil, vrne `zamuda: null`, in to je bilo isto kot brez
odgovora. Zdaj `Budilka.stikObMs` hrani **vsak** odgovor, `Ura.Vir.NI_PODATKA`
pa pomeni vozni red **brez** preventive in s stavkom „o zamudi te vožnje še ni
podatka". Preventiva ostane samo za primer, ko strežnika ni bilo mogoče vprašati.

### Po zvonjenju budilka sledi vozilu do odhoda

Vprašanje po zvonjenju je „koliko imam še do vlaka", zato widget odšteva do
**odhoda** odzvonjene budilke (odhod in ne prihod: potnik lovi trenutek, ko
vlak spelje). Ista budnica se po zvonjenju nastavi na vsaki 2 minuti
(`setExactAndAllowWhileIdle`, ne `setAlarmClock` — to ni budilka) in osveži
zamudo; 90 s po odhodu `vseZnova` ponavljajočo prestavi na naslednji dan.
Prej se je prestavila takoj ob zvonjenju in widget je kazal jutrišnji odhod.

### Dotik widgeta odpre vožnjo, ne domače strani

Widget odgovarja na „koliko časa imam še“; naslednje vprašanje je „in kje je
zdaj“. Domača stran nanj ne odgovori in do njega je od tam še dvakrat treba
klikniti — ravno takrat, ko potnik hiti. Zato pelje na **okno tiste vožnje**,
isti naslov kot gumb „Odpri vožnjo“ v seznamu budilk.

Naslov sestavlja `Budilka.naslovVoznje(izvor)`. Vzame niz in ne `Context`, da je
čist JVM in ima teste — ta naslov je bil že enkrat narobe (`+` namesto `%20` v
poti) in na napravi se to vidi šele kot „vlak s to številko ne obstaja“.

**`FLAG_UPDATE_CURRENT` tu ni okras.** `extras` se pri primerjavi namer ne
upoštevajo, zato bi widget brez njega odpiral prvo vožnjo, kar jih je kdaj
kazal. Ista past kot pri `PendingIntent` budilk, le da se tam rešuje z `data`.

Brez budilke ni kam peljati in ostane domača stran.

### Trije widgeti, tri vprašanja

| widget | vprašanje | omrežje |
|---|---|---|
| `Widget` (odštevanje) | koliko časa je še do **moje** vožnje | nič — računa iz shranjene budilke |
| `WidgetBudilke` (seznam s stikali) | katere budilke so nastavljene in ali jutri sploh grem | nič |
| `WidgetTabla` (odhodna tabla) | kdaj mi pelje z **moje postaje** | `/api/departures`, na 15 min |

**Prva dva ne pošljeta nobene zahteve.** Vse, kar kažeta, je v telefonu, zato
delata tudi takrat, ko strežnika ni — in `updatePeriodMillis` imata `0`, ker se
ura zvonjenja med dvema spremembama budilk ne premakne. Prerišejo ju
`Widgeti.osvezi()` in `Sprozilec`, ko se budilka tako ali tako zbudi.

`Widgeti.osvezi()` obstaja zato, ker se budilka spremeni na sedmih mestih,
widgeta, ki jo kažeta, pa sta dva. Tretji bi tiho zamrznil povsod, kjer bi ga
kdo pozabil dodati.

**Stikalo je napis, ne `Switch`.** `setCompoundButtonChecked` je šele API 31,
aplikacija pa gre od 26 — `Switch` v `RemoteViews` bi na starejšem telefonu
podrl risanje, ne le izgledal drugače. Pilula nosi **stanje**
(„vklopljena“ / „ugasnjena“), ne dejanja: tako se bere kot stikalo in ne kot
gumb, ki bi lahko pomenil oboje.

Vsako stikalo ima svoj `data` (`kajros://preklop/<id>`). Brez tega bi
`FLAG_UPDATE_CURRENT` vsa tri združil v eno in vsako bi preklopilo isto
budilko — `extras` se pri primerjavi namer ne upoštevajo. Ista past kot pri
budnicah v `Nacrtovalec`. Preverjeno na emulatorju: dotik prve vrstice je
ugasnil prvo budilko in pustil drugi dve pri miru.

### Odhodna tabla: 15 minut je cilj, ne obljuba

`updatePeriodMillis` tega ne zmore — sistemski minimum je 30 minut. Zato ima
tabla svojo budnico, `setInexactRepeating` z `ELAPSED_REALTIME` (**brez**
`_WAKEUP`): spečega telefona ne budimo zaradi table, ki je nihče ne gleda.

Koliko to res je, je izmerjeno in ne domnevano (`dumpsys alarm`, Android 15):
`repeatInterval=900000`, a `whenElapsed=+13m46s` proti `maxWhenElapsed=+25m1s`
— sistem sme korak raztegniti na 25 minut in ga združiti z drugimi alarmi.
Podrobnosti v [docs/MERITVE.md](../../docs/MERITVE.md).

**Zato widget nosi uro podatka.** Od 30 minut naprej to pove z besedo in
pordeči. Številka brez ure bi trdila svežino, ki je ta ritem ne more
zagotoviti — in „+4 min“ izpred pol ure je videti enako kot „+4 min“ izpred pol
minute. Dotik ure osveži takoj.

Troje, kar velja pri tem:

* **Omrežje ne sme na glavno nit.** `onReceive` teče na njej in
  `NetworkOnMainThreadException` bi widget podrl. Nit drži pokonci `goAsync()`
  — ta v `onUpdate` deluje, ker ta teče znotraj `onReceive`. Brez njega sme
  sistem proces ubiti sredi zahteve.
* **Samo odgovor prepiše shranjeno stanje.** Izpad zveze pusti pri miru, kar
  widget že kaže: stara tabla z uro je uporabna, prazna ni.
* **„Ni zveze“ in „te postaje ni“ nista isto** (`Tabla.Izid`, ista razlika kot
  v `Preverjevalec.Odgovor`). Prvo je začasno in postaje ne sme zavreči, drugo
  je tipkarska napaka in jo mora nastavitev povedati takoj. Postaje zato ni
  mogoče shraniti, ne da bi jo strežnik prej našel — widget, ki bi ostal
  prazen, je za potnika okvara aplikacije in ne napaka izpred treh dni.

Ime postaje razreši strežnik (`resolve_station()`), isto kot stran. Svoj seznam
postaj v telefonu bi bil drugo pravilo za isto stvar in bi se ob naslednjem
uvozu voznega reda razšel.

**`fitsSystemWindows` povozi `padding`.** Nastavitvena dejavnost je imela na
prvem posnetku naslov prilepljen na levi rob zaslona, čeprav je imel korenski
pogled `padding="20dp"`. Zunanji okvir je zato samo za odmike sistema, zrak pa
je na notranjem — isto kot v `budilke.xml`. Ob tem je bil gumb „Poišči in
shrani“ pod tipkovnico; rešita ga `adjustResize` in `ScrollView`.

### Kaj je widget dolgoval smernicam (17. 9. 2026)

Preverjeno proti Googlovim smernicam za widgete; štiri stvari so manjkale:

| kaj | zakaj |
|---|---|
| `previewLayout` (12+) | izbirnik je kazal **ikono aplikacije**, ne widgeta. Človek izbira tisto, kar vidi. `previewImage` ostane za starejše |
| `minResizeWidth/Height` | brez njiju sme launcher widget stisniti poljubno globoko in podnapis tiho odreže |
| sistemski `system_app_widget_background_radius` | trdih 18 dp je bilo na Androidu 12+ edino, kar se ni ujemalo z ostalimi widgeti. Zdaj `@dimen/widget_rob`, ki ima v `values-v31` sistemsko vrednost |
| `setContentDescription` | bralnik zaslona je prebral samo stoparico, ki je brez konteksta gola številka. `Chronometer` se ne da prebrati, zato je ura odhoda v opisu |

Kar je bilo **že prav**: `description`, `targetCellWidth/Height`,
`updatePeriodMillis` na sistemskem minimumu (30 min), `exported="false"`,
odštevanje v sistemskem procesu.

Kar ostaja **zavestno drugače**: widget je temen ne glede na temo naprave
(`values-night` aplikacija nima nikjer, ker je stran temna) in ne uporablja
Material You barv — te so v AndroidX, odvisnosti pa ta aplikacija nima.

Cena vsega tega je **1 472 B** (izdajni APK 79 394 → 80 866 B).

### Dnevnik budilk

`Dnevnik.kt` hrani zadnjih 120 vrstic (preverjanje in izid, zvonjenje in
ali je cel zaslon dovoljen, ustavitev, odlog, napake) v telefonu; prebere se
v seznamu budilk. Ne gre nikamor. Brez njega je bilo treba vzrok budilke, ki ni
zbudila, sklepati iz kode.

### Rezervo določi potnik, ne aplikacija

`zvoni = voznoredna + zamuda − X`. **Rezerve v računu ni** (odločeno
6. 9. 2026): v X je že. Meritev, da bi 5 minut prihranilo tretjino zamujenih
vlakov in dve tretjini avtobusov, ostaja — a je zapisana v vmesniku, kjer se
X izbira, ne vgrajena v formulo.

Kar ostaja iz meritve v kodi, je eno: **vlak pred voznim redom ne odpelje**
(0 primerov od 10 775), zato je pri vlakih zamuda omejena na `max(0, zamuda)`.
Pri avtobusih te omejitve NI in je ne sme biti — ti prezgodaj gredo v 25 %
primerov.

### Izpad povezave ima svoje pravilo

Zamuda se preverja do konca, korak pa se krajša: 5 min daleč, 60 s znotraj
petnajstih minut, 30 s v zadnjih petih. Blizu ure poskusi trikrat zapored.

Če zadnji odgovor strežnika ni mlajši od **dveh korakov** (glej spodaj, „štiri
napake"), velja, da povezave ni. Takrat:

* zvonjenje se **nikoli ne načrtuje pozneje od voznega reda** — sicer bi
  dvajset minut stara „+15" držala uro, tudi ko vlak vmes nadoknadi;
* v zadnjih **3,5 minute** pred zvonjenjem budilka zazvoni **takoj** in to
  pove. Cena je do 3,5 minute spanca, in samo takrat, ko povezave res ni.

### Ponavljanje: zidna ura, ne 86 400 sekund

Nabor dni je bitna maska (ponedeljek = bit 0). Naslednji odhod se poišče po
**uri po zidni uri**; prištevanje enega dne v milisekundah je narobe dvakrat na
leto, ker ima dan ob prehodu 23 ali 25 ur. `Ponovitev.kt` je zato čist JVM in
ima teste za oba prehoda.

`trip_id` se pri ponovitvi **zavrže**: naslednji dan je vožnja druga (LPP linija
3G ima 388 voženj). Ključ je takrat številka + voznoredna ura, ne `stop_seq` —
sezonska različica ima lahko drugačen vrstni red postankov.

### Prva ponovitev mora biti v naboru, ne šele druga

Stran pošlje uro vožnje, ki jo je človek **gledal**, in ta ni nujno na dan iz
nabora. Izmerjeno 12. 9. 2026: izbrana `tor + sre`, stran je kazala ponedeljek
14. 9., in budilka bi prvič zazvonila v **ponedeljek** — zunaj vzorca.
`prestavljena()` to popravi šele po zvonjenju, kar je prepozno.

Zato `Most.nastavi()` prvo ponovitev poravna, `Nacrtovalec.vseZnova()` pa
poravna tudi budilke, ki so v shrambi že nastale narobe
(`Ponovitev.jeVNaboru()`). Meja je `max(voznja − 1 s, zdaj)`: prvo pusti vožnjo
pri miru, kadar njen dan v naboru je, drugo poskrbi, da vožnja, ki je danes že
mimo, skoči na naslednji dan iz nabora.

### „Ni odgovora“ in „danes ne vozi“ nista isti izid

`Preverjevalec.Odgovor` ima tri stanja namenoma. Če tabla odgovori in te vožnje
na njej **ni**, ponavljajoča budilka molči in se prestavi — nedeljski alarm za
delavniški vlak je natanko tisto, zaradi česar ljudje budilke ugasnejo za vedno.
Pri **enkratni** budilki se to ne dela: tam je vožnjo za določen dan izbral
človek, in če je izginila z voznega reda, je to novica, ne razlog za tišino.

### Kje budilka bere zamudo

**`/api/departures`, ne `/api/train/{no}/run`.** Prva izbira je bila druga in
je bila napačna: `run` vrne `zamuda: null` za vsak postanek, ki ga feed še ni
dosegel — torej ravno za tistega, na katerem potnik čaka. Izmerjeno na EN 414:
Zidani Most je imel napoved prevoznika, Ljubljana pa nič, medtem ko je tabla
kazala +24 min iz naše ocene.

Odhodna tabla vrne natanko številko, ki jo potnik vidi. **Na njej je umerjena
tudi rezerva** (senca meri `ours_s`, kar je isti izračun `stats.predict`), zato
bi vsak drug vir pomenil, da rezerva varuje pred napako, ki je ne merimo.

### Obvestilo ne sme trditi ure, ki ji račun ni verjel

Ta napaka je bila na zaslonu: naslov „ob 22:34" (iz zamude) in pod njim
„po voznem redu — zamude nisem mogel preveriti". Zato `Ura.Izid` nosi
`odhodMs`, ki ga izračuna **ista odločitev** kot uro zvonjenja.

### Widget odšteva sam, mi ga ne rišemo

Sekunde riše `Chronometer` s `setChronometerCountDown` — v **sistemskem**
procesu. Widget, ki bi ga risali mi, bi zahteval prebujanje vsako sekundo.
Njegova časovnica je `elapsedRealtime`, ne epoch; razliko je treba prišteti.

`onUpdate` (vsakih 30 min, kar je sistemski minimum) kliče `Nacrtovalec.vseZnova`.
To ni okrasek: ponavljajoča budilka, ki je odzvonila in je nihče ni ustavil,
bi sicer ostala `odzvonjeno` za vedno — widget bi pisal „ni budilke“, jutrišnji
alarm pa ne bi bil nastavljen. Sistem nas zaradi widgeta tako ali tako zbudi;
to je najcenejši kraj za samopopravek.

### Prikaz ne sme obljubiti ure, ki je ni v shrambi

List budilke je pisal „zvoni ob 16:56“, seznam budilk pa „16:51“ — ker se
budilka shrani **brez** zamude (vpraša jo šele deset minut pred zvonjenjem).
Zdaj sta v listu dve vrstici: shranjena ura, ki velja tudi brez omrežja, in
pod njo „pri zdajšnjih +5 min bi zvonilo ob 16:56“.

Uro računa **Kotlin** (`Most.napoved()` → `Ura`), ne stran. Dvojnik tega
pravila v JavaScriptu bi se razšel s tistim, kar budilka res naredi.

### Zamuda pri potnikovem postanku je ena sama

`/api/train/{no}/run` vrne `zamuda: null` za vsak še nedosežen postanek — torej
ravno za potnikovega. Budilka je zato računala z ničlo, medtem ko je dva prsta
višje pisalo „+5 min“ (izmerjeno na LPV 2268, 9. 9. 2026: prikaz 17:24, budilka
17:19). Blok „Pri tebi“ si svojo odločitev zato zapiše (`state.tvojaZamudaS`)
in budilka bere **njo**, ne podatka pod njo.

### Pasti, ki so se pokazale šele na napravi

* **Napaka HTTP pride pred `onPageStarted`, ne za njim.** Izmerjeno
  12. 9. 2026 na 525: `httpError` je zastavico postavil, `onPageStarted` iste
  navigacije jo je pobrisal, `onPageFinished` pa je nativni zaslon skril —
  potnik je videl Cloudflarovo angleško stran. Zato `onPageStarted` briše
  stanje samo pri **drugem** naslovu (`naslovNapake`). Ta primer ni redek:
  kadar arwen ne teče, Cloudflare vrne 52x za vsako zahtevo.
* **`setAlarmClock` brez dovoljenja vrže `SecurityException`.** Od Androida 12
  točen alarm ni pravica. Ujet je in nadomeščen s `setAndAllowWhileIdle` —
  slabša budilka je boljša od podrte aplikacije.
* **`PendingIntent` brez `data` se zlije v enega.** `extras` se pri primerjavi
  ne upoštevajo, zato bi `FLAG_UPDATE_CURRENT` vse budilke združil v eno.
  Ločuje jih `kajros://budilka/<id>`.
* **Zagon dejavnosti iz ozadja je blokiran** (`Background activity launch
  blocked!` v dnevniku). Zaslon odpre obvestilo s `fullScreenIntent`, ne naš
  `startActivity` — in to le, kadar je telefon **zaklenjen**; sicer je to
  navadno obvestilo. Preizkušeno z `locksettings set-pin`.
* **`display` iz razreda premaga `[hidden]`** iz brskalnikovega sloga.
  `.bud-plast` brez `[hidden] { display: none }` leži čez vso stran in požira
  vsak klik — tudi v brskalniku, kjer gumba za budilko sploh ni.
* **`URLEncoder` ne sodi v pot naslova.** Je obrazčno kodiranje in presledek
  zapiše kot `+`; v poizvedbi je to prav, v poti pa je `+` dobesedni plus.
  Gumb „Odpri vožnjo“ je zato odprl `/app/train/LPV+2001` in stran je pisala
  „vlak s to številko ne obstaja“. Izmerjeno na produkciji 12. 9. 2026:
  `/api/train/LPV+2001/run` → **404**, `/api/train/LPV%202001/run` → **200**.
  Za oboje se uporablja `Nastavitve.zaPot()`, ker je `%20` veljaven tudi v
  poizvedbi — eno pravilo je manj priložnosti za napako kot dve.
