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

Razdeljevanje: samopodpisan APK s `kajros.app`, kasneje F-Droid. Brez Play
Store in brez Googlovega računa.

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

## Nič odvisnosti

Ne AndroidX, ne `appcompat`. Vse potrebno je v ogrodju od API 26: `WebView`,
`AlarmManager`, `NotificationChannel`, `Ringtone`. Zato je izdajni APK **50 kB**
(7. 9. 2026; 28 kB pred budilko in njenim vmesnikom) in v njem ni **nobenega**
Googlovega niza — preverjeno z `aapt2 dump strings`, 0 zadetkov za
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

Če zadnji uspešen odgovor ni mlajši od **30 s**, velja, da povezave ni. Takrat:

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
