---
paths:
  - "android/**"
---
# Aplikacija za Android

Nativni ovoj z WebView na `kajros.app`. Vmesnik **en sam — spletni**; nativno samo, česar splet ne zmore: budilka. Da ni videti kot splet v ovoju, se ureja v CSS strani („Dotik“ v `oznake.md`).

## Zakaj tako

| možnost | zakaj ne |
|---|---|
| PWA | alarma ob uri ne zna (`Notification Triggers` nikoli izdan; Web Push skozi FCM) |
| TWA | rabi Chrome; telefon = razgooglana Volla 22 s Fennecom |
| GeckoView | most do JS moreč; `addJavascriptInterface` = ena vrstica |
| service worker | „nič ne pokaže“ → nedosegljiv strežnik pokrije **nativni zaslon napake**. Izjema od 2. 10. 2026: strani orodne vrstice iz predpomnilnika, ob 5xx Cloudflara lupina brez podatkov |

Razdeljevanje **s strani** `kajros.app/android`; od novembra 2026 tudi **Play** (spodaj).

## Meja zaupanja = `Nastavitve.izvor()`

Povezava zunaj izvora gre v brskalnik, lego dobi le izvor, most (`window.Kajros`) ga preveri ob klicu — `addJavascriptInterface` vidi **vsaka** naložena stran. Sheme ven naštete; `intent:` ni med njimi. Razčlemba z `java.net.URI` (ne `android.net.Uri`): preizkusljivo brez naprave.

## Lastna lega: `retain` vedno `false`

WebView si dovoljenje zapomni sam (`AwGeolocationPermissions … = true`), sistemsko „samo tokrat“ pa poteče → `onGeolocationPermissionsShowPrompt` ni več poklican, lega mrtva za vedno (tri dni tihe okvare). Ob zagonu `GeolocationPermissions.getInstance().clearAll()`; resnica = Androidovo dovoljenje.
* **Most 7 (1.14)**: `dovoljenja().lega` = natančna ali približna (`DeljenjeStoritev.smeLego`); po njej stran lego prižge sama. `onGeolocationPermissionsShowPrompt` odobri tudi samo približno (prej okno ob vsakem klicu). V WebView `navigator.permissions` ni (WebView 124) — resnica je most.
* `Most.zahtevajLego()` → `vklopiLego()`: vedno najprej sistem; odgovor brez okna (< `Lega.BREZ_OKNA_MS` 1 s, izmerjeno 72 in 51 ms) = trajna zavrnitev → nastavitve aplikacije + Toast. Izid `kajrosLega(stanje, nastavitve)`, tudi ob `onResume` po spremembi.
* **Most 8 (1.16)**: `legaZacni()`/`legaUstavi()` → `HitraLega.kt`: zadnja znana lega **vseh** ponudnikov in sprotna `network`/`fused` (2 s), na stran kot `kajrosPopravek({lat, lon, acc, starost_ms})` (starost iz `elapsedRealtimeNanos`). GPS ostane WebView-u (dva poslušalca = dvojna baterija). Teče, dokler kdo na strani lego čaka (`hitraLega` v `common.js`), vedno ustavljena ob `onPause`. Razgooglan telefon `network`/`fused` nima — tam pride samo zadnja znana.
* Most ≤ 6: stran lege ne prižge sama, kartice ni.

## Razdeljevanje (12. 9. 2026)

**8. 11. 2026, David: aplikacija gre v Play**, stran ostane drugi kanal. Gradnja za Play: `targetSdk` 36, AAB, brez samoposodobitve, `REQUEST_INSTALL_PACKAGES` in `USE_EXACT_ALARM`; podpisni ključ = obstoječi, naložen pred prvim nalaganjem (sicer namestitve s strani nikoli ne dobijo posodobitve iz Playa). Vse ovire z viri: `docs/presoja/2026-11-08-nativna/NACRT.md`, faza 0.

| trgovina | ovira |
|---|---|
| F-Droid, IzzyOnDroid | samo prosto programje; koda zaprta |
| Google Play | 25 $, identiteta, **12 preizkuševalcev × 14 dni**, AAB, `targetSdk` 36 |
| Accrescent | zaprto sprejme, rabi pregled in `bundletool` — odprto |

* `android/objavi.sh` zgradi, podpiše, APK + `razlicica.json` z `rsync` na strežnik; `api.py` streže na `/prenos` (`config.PRENOS_DIR` = `${KAJROS_DATA_DIR}/prenos`). Brez mape ni poti. Po **prvi** objavi restart storitve (mount).
* **Podpisni ključ = trajna identiteta** (`podpis.sh`, `~/kajros-android/podpis/`), nikoli v git; geslo v `podpis.properties` zunaj repozitorija; brez njega gradnja naredi nepodpisan APK.
* **Dvig `versionCode` = edini pogoj za posodobitev.**
* **Posodobitev javi aplikacija sama** (`Posodobitev.kt`, enkrat na dan `/api/android/razlicica`):
  * Nič se ne prenese samo; sistemski „Posodobi“ = potnikov drugi klik.
  * **Namesti aplikacija, ne brskalnik** (od 1.6, `Namestitev.kt`): sistemski namestitveni program ob vsaki namestitvi postavi `USE_FULL_SCREEN_INTENT` na `deny`; seja `PackageInstaller` (`SessionParams.setPermissionState`, Android 14+) ga ohrani (`allow`, `installerPackageName=app.kajros`). Vsota SHA-256 iz odgovora pred `commit`.
  * Najprej `canRequestPackageInstalls()` (`REQUEST_INSTALL_PACKAGES`), ob `onResume` namestitev brez drugega klika. **Ne dela** (28. 10. 2026, emulator Android 15, 1.13, 2 od 2): ob `onResume` po vklopu vrne `false`, čeprav `appops` že pravi `allow` (5 s po vklopu) → „Brez dovoljenja …“; gumb „Odpri nastavitve“ nato namesti brez nastavitev.
  * Po uspešni posodobitvi sistem aplikacijo ustavi in je ne odpre znova (emulator: launcher, `MY_PACKAGE_REPLACED` pride, zaslona ni) — potnik vidi „nič se ni zgodilo“.
  * Namešča zaslon „O aplikaciji“ (`AplikacijaDejavnost`, od 1.12) z `Namestitev.Stanje` (odstotek, potrditev, napaka v slovenščini) in gumbom naprej. Okno za potrditev odpre sprejemnik, gumb „Odpri okno za potrditev“ znova (zagon iz ozadja sme biti zavrnjen; namera v `Stanje.Potrdi`). Ob neuspehu stara pot: stran v brskalniku.
  * Različica vidna v meniju Več (`Most.oAplikaciji()`, most 5) in na zaslonu. „Preveri znova“ mimo dnevne meje; dan šteje šele **odgovor**.
  * Do 1.5 vrstica odpre `/android?iz=aplikacija` — stran tam pove „posodabljaš, budilke ostanejo“ in opozorila brskalnika in Play Protecta.
  * Toast od Androida 12 največ dve vrstici.
  * **`stran` in `url` iz odgovora skozi `Nastavitve.jeNas()`.**
  * Preizkus: razvojni strežnik s `KAJROS_BASE_URL=http://10.0.2.2:8001 KAJROS_PRENOS_DIR=<mapa>`, prvi APK `adb install`, `appops set app.kajros REQUEST_INSTALL_PACKAGES allow`. Sistemsko okno z `am start … content://media/…` **ne kot root**.
* **Play Protect** (`developers.google.com/android/play-protect/warning-dev-guidance`): trdo blokira le ob SMS, poslušalcu obvestil, dostopnosti — Kajros nič od tega. Opozorilo odstrani le, da Google aplikacijo pozna; pritožba za „Harmful app blocked“ `support.google.com/googleplay/android-developer/contact/protectappeals`. Seja ga tudi sproži: `STATUS_FAILURE_BLOCKED` → „ustavil jo je Play Protect …“.
* **2027**: Google zahteva preverjenega razvijalca na certificiranih napravah (od 30. 9. 2026 BR, ID, SG, TH; globalno 2027). Volle ne zadeva. Takrat izbrati znova.

## Podpora v Playu (20. 10. 2026)

Play (`answer/9858738` §4) prepove plačilo mimo Googla, tudi prek WebView-a; izjema (`answer/10281818`): napitnina, **100 % ustvarjalcu**, **nič digitalnega v zameno**.
* Nič v zameno (ne značke, ne brez oglasov).
* Samo enkratne donacije; članarin/trgovine na Ko-fi ne bo.
* Provizijo PayPal/Stripe krije David (38 c) — tako povedati ob pregledu.
* Rezerva ob zavrnitvi: skrij kartico in gumb samo v aplikaciji (`.v-aplikaciji` iz `common.js` po `MOST`), ena vrstica CSS, brez novega APK.
* Programi DMA niso potrebni.

## Pošiljanje: `navigator.share` iz aplikacije (1.13, most 6)

`Most.poslji(zapis)` odpre sistemski izbirnik; `common.js` ga obleče v Web Share (`navigator.share`/`canShare`). APK o vsebini ne ve nič — nov gumb ne rabi novega APK.
* Zapis = Web Share (`title` → `EXTRA_SUBJECT`, besedilo `text` + `\n` + `url`).
* **Datoteke** (Level 2): base64, `cache/poslji/<čas>-<n>/<ime>` (10 datotek, 10 MB, starejše od 10 min gredo), lasten neizvožen `Datoteke` (`ContentProvider`), `ClipData` + `FLAG_GRANT_READ_URI_PERMISSION`. Ime skozi `varnoIme()` ob zapisu **in** branju.
* Izid: izbira → obljuba izpolnjena, preklic → `AbortError` (`PendingIntent` na `PoslanoSprejemnik`; `onResume` brez izbire = preklic). `kajrosPoslano(id, izbrano)`. „Kopiraj“ v izbirniku 14+ šteje za preklic.
* Stara aplikacija (most 5) kopira. WhatsApp, Signal, Instagram še niso preizkušeni.

## Lega ne sme skriti aplikacije napravam brez GPS

`ACCESS_*_LOCATION` = privzeto `uses-feature required="true"` (`aapt2 dump badging`). V manifestu `required="false"` za `location`, `location.gps`, `location.network`.

## Nič odvisnosti

Ne AndroidX ne `appcompat` — ogrodje od API 26. APK ~70–80 kB, **nobenega** Googlovega niza (`aapt2 dump strings`: „google“, „firebase“, „gms“ 0). Nova vrstica v `dependencies` rabi razlog.

**`-keepclassmembers` za `@JavascriptInterface` v `proguard-rules.pro` mora ostati** (R8 bi preimenoval most, samo v izdaji). **Vir, bran samo po imenu, rabi `res/raw/keep.xml`** (krčenje virov je vrglo `raw/nezno`, 1.7–1.9 nema; `objavi.sh` APK brez `raw/nezno` zavrne).

## Orodja puščajo

`orodja.sh` postavi vse v `~/kajros-android` in **dokaže**, da drugod nič; `zgradi.sh` dokaz ponovi ob vsaki gradnji. AGP piše `~/.android/analytics.settings` z `userId` — premakne ga **samo `-Duser.home`**. Zato je `user.home` lažni dom: pot do ključa iz okolja (`KAJROS_PODPIS`, `KAJROS_ANDROID`, `HOME`), `zgradi.sh izdaja` izpiše prstni odtis (prej tiho nepodpisan APK). Okolja ne dodajaj na slepo: AGP pade ob več poteh (`ANDROID_PREFS_ROOT`, `ANDROID_SDK_HOME`, `ANDROID_USER_HOME`); emulator rabi `ANDROID_AVD_HOME`.

## Preverjanje

```bash
./zgradi.sh                 # testi JVM + APK + revizija domačega imenika
KAJROS_EMULATOR=1 ./orodja.sh && ./zgradi.sh emulator
./zgradi.sh namesti
adb exec-out screencap -p > ../posnetki/x.png
```

Emulator `default`, **ne** `google_apis`. `variations_seed_loader.cc: Seed missing signature` ni naša napaka.

## Budilka

David: *„uporabnik vnese, koliko časa (x minut) preden pride vlak naj zazvoni (upošteva se zamude); če pa ni povezave, potem zazvoni x minut preden je napovedan vozni red“* in *„uporabnik ne sme zamuditi, raje kej rezerve, če ni zihr“*.

Vse za budilko **shranjeno lokalno** (voznoredna ura). Aritmetika v `Ura.kt`, čista, s testi.

### Dostop in seznam

* Do seznama s prve strani (kartica, glej `strani.md`); v glavi drugih strani ni. „Naslednja budilka“ v sistemu odpre seznam (`AlarmClockInfo` → `BudilkeDejavnost`).
* Ura v sistemskem meniju = **prvo preverjanje** (10 min pred), `setAlarmClock` ena budnica za oboje (`Nacrtovalec`).
* Seznam = kartica kot `.d-bud`: ura 40 sp, stikalo M3, zamuda kot žeton (`Zeton`, `ReplacementSpan`); vklopljena rjava (`m_kont`), ugasnjena siva, deljenje indigo. Besede iste kot `home.js`.
  * Drsi vse razen „Odpri Kajros“; opozorilo o dovoljenjih na vrhu.
  * Stikalo M3 brez AndroidX: `Switch` z `android:thumb`/`track` (`stikalo_*.xml`), `thumbTint`/`trackTint` (`res/color/`).
  * Odstrani vpraša. Okna `TemaOkna` 28 dp. `napaka` `#ffb4ab` (`sev_bad` na rjavi 2,3 : 1).
  * **Enkratna budilka odide s koncem sledenja** (`Budilka.opravljena`: konec sledenja ali poznejši odlog); `Shramba.pocisti` ob `vseZnova` razen zvoneče; `Most.seznam()` in `WidgetBudilke` opravljene preskočita.
  * Odprt seznam se osveži na 30 s.
  * **Ponavljajoča ne zazvoni takoj** (`Ponovitev.prva`): v preteklosti → naslednja iz nabora. **Enkratna zvoni takoj** in list to pove („zvoni **takoj** — 19:01 je že mimo“). Dan izbere `Most.napoved()` po računu `nastavi()`, **brez zamude**.
  * Dnevnik v izdaji: dolg pritisk na „Budilke“, gumb „Kopiraj“. `Dnevnik.kt` 120 vrstic, nikamor ne gre; gumb in naslov strežnika samo v razvojni.
* **Rezerve v računu ni**: `zvoni = voznoredna + zamuda − X`, rezerva je v X. Vlak pred voznim redom ne odpelje (0 od 10 775) → pri vlakih `max(0, zamuda)`; **pri avtobusih ne** (prezgodaj v 25 %).

### Kaj budilko utiša — ne vrni

* **14. 9. 2026 ni zbudila — štiri napake**: (1) veljavnost od voznega reda, ne od zvonjenja z zamudo → `Ura.veljavnost(do, starost)` = korak ob prihodu + zdajšnji korak + 15 s; (2) „čas je tu“ brez vprašanja strežnika → brez omrežja zvoni samo na sveži zamudi ali odlogu; (3) `USE_FULL_SCREEN_INTENT: deny` (14+ ga dobijo le budilke iz trgovine) → `zahtevajZaBudilko` (`ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT`), `cel_zaslon` v `dovoljenja()`; (4) zanka po „Ustavi“ → `prestavljena()` po `max(zdaj, voznoredni)` (`BudilkaTest`).
* **Zvoni obvestilo, ne aplikacija**: storitev iz ozadja Android 16 utiša (`AudioHardening … muted`). Kanal `budilka`: `DEFAULT_ALARM_ALERT_URI`, `USAGE_ALARM`, `FLAG_INSISTENT`, `FOREGROUND_SERVICE_IMMEDIATE`. `ZvonjenjeStoritev` (`systemExempted`, `USE_EXACT_ALARM`) ostane; „Ustavi“ in „Še 2 minuti“ v obvestilu. **Kanala ni mogoče spremeniti** — nov kanal pod novim imenom, stari se v `kanali()` izbriše.
* **Najprej nežno, nato glasno** (1.5): nežno `Ura.NEZNO_MS` (20 s) **pred** uro na `budilka-zacetek`, glasno ob uri na `budilka`. Le budilka, ki zbudi (`Budilka.neznoMs`); odlog spet nežen.
  * Naraščanje v datoteki `res/raw/nezno.mid` (`android/zvok_nezno.py`): harfa, C–Am–F–G po 2 s; glasnost kot krivulja v dBFS (`KRIVULJA`) iz izmerjene `KALIBRACIJA`. Kanal ima zvok **po imenu** (`android.resource://app.kajros/raw/nezno`).
  * Dve obvestili (`OBVESTILO_NEZNO` 4712, `OBVESTILO` 4711); preklop = `startForeground` glasnega, `cancel` nežnega, pod delnim `WakeLock` do glasnega + 10 s. Konec nežnega je že glasen (112) — tišine ni.
  * Nežni del vsaj 20 s tudi, ko je ura mimo (`NAJMANJ_NEZNO_MS`; `NeznoTest`); zadnja budnica na začetku nežnega (`Budilka.zacetekZvonjenja`).
  * Glasnost: `android/zvok_meri.sh` (PCM iz `MidiExtractor` prek `app_process`). Sonivox šum −65 dBFS. Od 1.10 začetek −67, 15 s −44, 20 s −34 — na telefonu dobra (David, 12. 10.). Meri znova le ob spremembi `nezno.mid`, `KRIVULJA` ali kanala.
  * Brez tresenja na začetku; tresenje doda storitev pri 35 % nežnega, `USAGE_ALARM`, sunki 150 ms 70/255 na 2,5 s do 300 ms 200/255 vsako sekundo.
  * Ob vidnem zaslonu zvonjenja glasno na `budilka-zaslon`, nežno na `budilka-zacetek-zaslon` (`DEFAULT`, brez plavajočega obvestila); vidnost `ZvonjenjeStoritev.zaslonViden`.
* **Straža zvoka** (1.10): tipka za glasnost in podrsano obvestilo utišata zvok, budilka ostane. `ZvonjenjeStoritev` na 2 s gleda `AudioManager.activePlaybackConfigurations` (`USAGE_ALARM`); po dveh tihih isto fazo objavi pod drugo številko (4711↔4715, 4712↔4716), največ trikrat, nato zapis v dnevnik.
* **„Preizkusi zvonjenje“** po isti poti kot prava (`ZvonjenjeStoritev.PREIZKUS`, ni v shrambi). `Zvonjenje.zakajTiho()` našteje, kar utiša (obvestila, kanal, glasnost 0, ton „brez“, Ne moti); ob zvonjenju vrstica `zvok: …` v dnevnik.

### Zaslon zvonjenja: Peron (1.6)

Prototip `design/budilka/`: vozilo pripelje, potegneš ga k sebi, budilka utihne. OpenGL ES 2.0 brez knjižnic.
* `Peron.kt` geometrija in `Peron.ustavi()` (`PeronTest`); `Mreza.kt` gradniki.
* `PeronRisar.kt`: Lambert kot three.js r128 `MeshLambertMaterial`; **megla po sliki, ne po ogliščih** (tla 1,6 km).
* `PeronPogled.kt`: začeti na vozilu (rezerva 44 dp), 60 % poti ali sunek ≥ 0,6 dp/ms po ≥ 30 %; ob dvigu šteje **lega iz dviga**. Utihne ob odločitvi.
* Po potegu `DeljenjeStoritev.cakaj` (1.9, `deljenje.md`); „Ustavi“ v obvestilu ne.
* Bralnik zaslona: dvojni dotik (`ACTION_CLICK`) ustavi.
* **Brez prizora navaden gumb „Ustavi“** (1.7): risar ujame vsako izjemo (`varno`), lovilec za `GLThread*`; izjema bi podrla storitev, ki zvoni.
* Animacije sistema ugasnjene → brez vabila.
* Preizkus potegov: `InputManagerGlobal.injectInputEvent` iz `app_process` (`input swipe` ima premor, hitrost 0).

### Preverjanje zamude

* **`/api/departures`, ne `/api/train/{no}/run`** — ta vrne `zamuda: null` za nedosežen postanek. Tabla = številka, ki jo potnik vidi, na njej umerjena rezerva.
* **„Strežnik nima podatka“ ni izpad**: `Budilka.stikObMs` hrani vsak odgovor; `Ura.Vir.NI_PODATKA` = vozni red brez preventive („o zamudi te vožnje še ni podatka“).
* Korak: 5 min daleč, 60 s v 15 min, 30 s v zadnjih 5; blizu ure trikrat zapored. Odgovor starejši od **dveh korakov** = ni povezave: zvonjenje nikoli pozneje od voznega reda; v zadnjih **3,5 min** zazvoni takoj in to pove.
* **„Ni odgovora“ ≠ „danes ne vozi“** (`Preverjevalec.Odgovor`, tri stanja): ponavljajoča molči in se prestavi; enkratna ne.
* Obvestilo ne trdi ure, ki ji račun ni verjel: `Ura.Izid.odhodMs` iz iste odločitve.
* List: shranjena ura + „pri zdajšnjih +5 min bi zvonilo ob 16:56“. Uro računa **Kotlin** (`Most.napoved()`), ne JS.
* Blok „Pri tebi“ zapiše odločitev (`state.tvojaZamudaS`), budilka bere njo.

### Po zvonjenju sledi do odhoda

* Budnica na 2 min (`setExactAndAllowWhileIdle`) osvežuje zamudo; 90 s po odhodu `vseZnova` prestavi ponavljajočo.
* Po zvonjenju zamuda velja dve osvežitvi (4 min 15 s): `Ura.izracunaj(sledenje = odzvonjeno)`.
* **Do kdaj odštevati** = sveža zamuda (brez nje do voznega reda). **Do kdaj slediti** = `Budilka.konecSledenjaMs()` po zadnji znani zamudi. Ena budnica na sam odhod (`SledenjeTest`).
* **Števec na ničli ni odhod**: feed novo zamudo pogosto javi šele, ko bi vozilo že moralo biti tam. Sledenje do potrjenega odhoda (`zamuda.vrsta` „izmerjeno“ → `Budilka.potrjeno`) + 90 s, sicer vlak 10 min, avtobus 5 min (`Ura.SLEDENJE_*`); widget vmes piše „zdaj“, nova zamuda števec spet požene. Izmerjeno 2.–4. 11. 2026: pozneje kot 30 s po ničli vlaki 23,5 % (n = 19 612), avtobusi 32,3 % (11 954); P95 8 in 3,4 min. Do 5. 11. 90 s za oba.

### Ponavljanje

* Nabor dni = bitna maska (pon = bit 0). Naslednji odhod po **zidni uri**, ne +86 400 s (`Ponovitev.kt`, testa za oba prehoda).
* `trip_id` se zavrže; ključ = številka + voznoredna ura.
* Prva ponovitev mora biti v naboru: `Most.nastavi()` poravna, `Nacrtovalec.vseZnova()` popravi shranjene (`Ponovitev.jeVNaboru()`), meja `max(voznja − 1 s, zdaj)`.

### Widgeti

| widget | vprašanje | omrežje | privzeto |
|---|---|---|---|
| `Widget` (odštevanje) | koliko do **moje** vožnje | nič; gumb „preveri“ = `Sprozilec` | 2×1 |
| `WidgetBudilke` (stikala) | katere budilke | nič | 2×2 |
| `WidgetTabla` (odhodna tabla) | kdaj z **moje postaje**; s ciljem: kdaj **do cilja** | `/api/departures?limit=30` ali `/api/connections?od=&limit=30`, na 15 min | 4×2 |
| `WidgetBliznjica` | en dotik do poti, vlakov, avtobusov, zemljevida, ovir, budilk | nič | 1×1 |
| `WidgetIskanje` | „Kam greš?“ (`/app/pot#kam`) in iskalnika omrežij | nič | 4×1 |

* **Velikost odloči vsebino** (`Velikost.kt`, čist JVM, `VelikostTest`): MINI 40×40, PAS 110×40, TRAK 110×64, TRAK_SIROK 240×64, KVADRAT 110×110, SREDNJI 240×110, STOLPEC 110×250, VELIK 240×250 dp. Googlova mreža: pokončno vrstice 102/220/337, ležeče 51/117/184. Izbira = največja, ki se prilega, sicer najmanjša — **isto pravilo kot launcher**.
  * 12+: `RemoteViews(Map<SizeF, RemoteViews>)` (`Izris.odzivno`), launcher izbere sam, brez prebujanja. Prej iz `OPTION_APPWIDGET_*` (pokončno min širina × max višina, ležeče obratno) in `onAppWidgetOptionsChanged`.
  * Seznam (`RemoteCollectionItems`) samo 12+; prej STOLPEC/VELIK nista ponujena. Predloga vrstic `FLAG_MUTABLE`, vrstica `setOnClickFillInIntent`.
  * **Ležeči 2 vrstici = 117 dp**: kar mora ostati, gre na vrh (žeton zamude ob številki, ne v stavek spodaj). Budilke 4×2 na 12+ = seznam: nepremične vrstice bi se odrezale na pol.
  * Ozko (2×2, 2×3): vrstica v dveh vrsticah (ura + zamuda/stikalo, pod njima cilj ali vožnja z dnevi); v eni vrsti je cilj izginil.
  * `minResize` 40 dp povsod; prej 180 → widget ni šel pod 3×2.
* **Pregled brez telefona**: `src/debug/…/PregledWidgetov.kt` (samo razvojni APK), vse velikosti z vzorci: `adb shell am start -n app.kajros/.PregledWidgetov -e kaj odstevanje|budilke|tabla|bliznjica|iskanje -e stanje N`. `-e kaj zivo` veže prave widgete (prej `adb shell appwidget grantbind --package app.kajros`), `-e tapeta svetla|temna` za videz brez podlage. Pod 12 pregled widgete veže sam: velikost je samo v `OPTION_APPWIDGET_*` vezanega widgeta. Posnetki v `posnetki/widgeti/`.
  * Android 9 = AVD `kajros28` (`emulator -avd kajros28 -port 5556 …`, `adb -s emulator-5556`); slika `system-images;android-28;default;x86_64`.
* **Prazen widget ima svojo postavitev** (`w_mini_prazen`, `w_pas_prazen`, `res/values/postavitve.xml`): launcher isto postavitev ob osvežitvi samo popravi (`reapply`) in ostane, česar nova slika ne nastavi — stikalo, rjava podlaga in `Chronometer`, ki šteje čez ničlo naprej (prijava 5. 11. 2026, ponovljeno na emulatorju 15: `-e kaj prehod` v pregledu). Kar ena veja nastavi (vidnost, podlaga, velikost pisave), mora druga postaviti nazaj.
* **RemoteViews ne zna `<View>`**: razmik = `<FrameLayout>`; z `<View>` „Couldn't add widget“.
* **Samodejna velikost** (`autoSizeTextType`): z omejeno širino in višino zanesljiva; pri `wrap_content` samo zmanjša, širina se meri po `textSize` — **brez `textSize` je številka 14 sp**. `setTextViewTextSize` jo izklopi.
* **Odštevanje šteje zadnjo uro** (do 23. 10. dve: „1:05:31“ se ob žetonu na 2×1 in 2×2 ne izide); prej ura odhoda („16:57“, „jutri 06:57“, `Izris.danUra` po koledarju).
  * Zamuda = `odhodMs − voznoredniMs`, **ne `upostevanaS`**: ta ima odšteto potnikovo rezervo — vlak z zamudo je bil „1 min pred redom“.
  * Minuta in razred lokalno (`Tabla.minute`, `Tabla.razred`, meje `stats._razred_zamude`): budilka hrani sekunde, `Ura` presodi svežino.
  * Gumb „preveri“ (4×1, 4×2) = `Sprozilec.PROZI` s `kajros://preveri/<id>`: ista pot kot budnica, svoj `data`, da je ne povozi.
* Barve omrežja (`Izris.ton`): vlak rjav, avtobus zelen; lestvica zamud ista. Žeton zamude na tonski podlagi ima temno podlago (`zeton_temen`; `d_big` na rjavem 2,1 : 1).
* **Videz brez podlage** (tabla, `TablaNastavitev`) samo za 1×1 in trak (`Izris.slog`); večji in pas ostanejo tonski. Svetlo ozadje zaslona iz `WallpaperColors` (12+ `HINT_SUPPORTS_DARK_TEXT`, 8.1+ svetlost glavne barve). Senca je samo v XML → svoje postavitve `w_*_brez*`, **izpeljane iz `w_mini` in `w_trak`**: sprememba tam mora tudi tja. Zamuda = pika razreda + številka v barvi besedila.
* Prva dva brez zahtev; prerišeta `Widgeti.osvezi()` (budilka se spremeni na sedmih mestih) in `Sprozilec`. `onUpdate` (30 min) kliče `Nacrtovalec.vseZnova` — samopopravek obviselih `odzvonjeno`.
* Dotik odštevanja odpre **vožnjo** (`Budilka.naslovVoznje(izvor)`, čist JVM), tabla tablo, vrstica table svojo vožnjo, budilke seznam.
* **`FLAG_UPDATE_CURRENT` + svoj `data`** (`kajros://preklop/<id>`, `kajros://odpri/<koda>`; koda = id widgeta × 20 + n) — `extras` se pri primerjavi namer ne upoštevajo.
* **Stikalo je slika** (`stikalo_slika_*.xml`): `Switch` v RemoteViews šele API 31.
* Odštevanje riše `Chronometer` (`setChronometerCountDown`) v sistemskem procesu; časovnica `elapsedRealtime`.
* Koren postavitve `@android:id/background` (prehod widget → aplikacija, 12+). `previewLayout` = privzeta velikost z vzorcem; zaobljenost `@dimen/widget_rob` (`values-v31`). Opis za bralnik zaslona z uro odhoda.
* **Tabla: 15 min je cilj** — `setInexactRepeating`, `ELAPSED_REALTIME` **brez** `_WAKEUP`; sistem korak raztegne do 25 min. Zato **widget nosi uro podatka**, od 30 min z besedo in rumeno (pas: „ob 14:03“ spredaj); dotik ure osveži. Ko prvi odpelje, se preriše iz shrambe (`naslednjiIzris`, `setWindow`, brez zahteve).
  * Omrežje ne na glavno nit: `goAsync()`.
  * Samo odgovor prepiše stanje; izpad pusti staro tablo.
  * „Ni zveze“ ≠ „te postaje ni“ (`Tabla.Izid`); postaje ni mogoče shraniti brez strežnika.
  * Postaja se izbere (`/api/stations/search`, 250 ms, od dveh črk, predlogi pod poljem); shrani se ime strežnika (`Izid.Odhodi.popravi`). Pri avtobusih tudi `smer` (ključ in napis); `smer: null` = tabla cela; ⇄ na widgetu = druga stran ceste.
  * Odpadla vožnja prečrtana z „odpade“; ovira (prva, ki imenuje progo) = gumb ⚠, na seznamu vrstica.
  * **Cilj (ni nujen) = relacija** (`Nastavitev.cilj`): iste postavitve, vrstica s prihodom („prihod 07:29 · prestop Medvode (tesno) · LP 2435“ — prihod prvi, tropičje sme odrezati številko), ⇄ = druga smer (`obrnjena()`), dotik odpre iskalnik `?from=&to=`. Zveze s prestopom brez zamude (strežnik je ob odhodu ne pove). Odpeljane se izločijo **pred** rezom na 30: strežnik brez `od` vrne cel dan (mestna relacija 115 zvez). S ciljem stran ceste ne velja.
  * **Rez `od` je po pričakovanem odhodu** (`api._odhod_ts`), ne po voznem redu: vlak z zamudo 18 min je bil 12 min po uri že s seznama. `od` skozi epoho (`api._ura_ts`): na dan premika ure je ura stene do treh za uro stran od `dep_s`. Prihod na vrstici = vozni red + zamuda ob odhodu, kot druga vrstica zveze na strani.
  * **Ime** (`Nastavitev.oznaka`, „Domov“) namesto postaj na vseh velikostih, na velikih postaji pod njim. Velja za smer, v kateri je nastavljeno (`oznakaOd`); po ⇄ postaje.
  * `fitsSystemWindows` povozi `padding` — zunanji okvir za odmike, zrak na notranjem; `adjustResize` + `ScrollView`. Nastavitev ima `configChanges`: obrat bi pobrisal izbiro.
  * Ritem (`naRitem`) samo, kadar je tabla na zaslonu; sicer ga ob zagonu telefona pobriše. Do 23. 10. je vsem brez table vsakih 15 min zaman zagnal aplikacijo.
* **Bližnjica** = oblika z domače strani (cvet budilke, detelja zemljevida, `oblika_*.xml` iz `home.html`) z ikono, ime pod njo kot pod ikono launcherja (barva po ozadju zaslona, `w_bliznjica_svetlo`). Ime od 92 dp višine (`Z_IMENOM_DP`), nižje samo oblika. Nastavitev `BliznjicaNastavitev` brez strežnika. „Kam greš?“ ima ime „Pot“: v stolpcu 57 dp se ne izpiše.
* **Iskalna vrstica**: 1×1 povečevalo, ožja od 240 dp brez gumbov omrežij (ležeči 4×1 tudi: 51 dp < `TRAK_SIROK`). Imena widgetov v izbirniku = `android:label` na sprejemniku; brez njega je vsak „kajros“.

### Pasti na napravi

* **Napaka HTTP pride pred `onPageStarted`**: briše stanje samo pri drugem naslovu (`naslovNapake`), sicer potnik vidi Cloudflarovo stran.
* `setAlarmClock` brez dovoljenja vrže `SecurityException` → `setAndAllowWhileIdle`.
* Zagon dejavnosti iz ozadja blokiran: zaslon odpre `fullScreenIntent`, le ko je telefon **zaklenjen**.
* `display` iz razreda premaga `[hidden]`: `.bud-plast` rabi `[hidden] { display: none }`.
* **`URLEncoder` ne v pot** (`+` = plus; `/api/train/LPV+2001/run` 404). `Nastavitve.zaPot()` (`%20`).
