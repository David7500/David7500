# Raziskava za nativno aplikacijo Kajros in objavo v Google Play (8. 11. 2026)

Zapisano sproti med raziskavo. Zanesljivost: »uradni vir« = prebrana uradna stran (povzetek prek orodja za branje strani, zato datuma strani večinoma ni); »sklepam« = moj sklep iz več virov.

## A1. Dostop do produkcije za nov osebni račun

Odgovor: Velja še. Osebni računi, ustvarjeni po 13. 11. 2023, morajo pred produkcijo izvesti zaprti preizkus z vsaj 12 preizkuševalci, ki so vključeni neprekinjeno vsaj 14 dni. Kdor se izpiše in vpiše nazaj, mora spet nabrati 14 zaporednih dni. Nato v konzoli »Apply for production« izpolni vprašalnik o treh sklopih: o zaprtem preizkusu (kako težko je bilo najti preizkuševalce, angažiranost, povzetek povratnih informacij), o aplikaciji (ciljna publika, vrednost, ocena namestitev v prvem letu) in o pripravljenosti za produkcijo. Pregled traja običajno do 7 dni, lahko dlje; če je preizkuševalcev premalo ali premalo aktivni, zahtevajo nadaljevanje preizkusa.

Za Kajros: če račun še ni odprt in preizkus ne teče, objava »prihodnji teden« ni mogoča: 14 dni + do 7 dni pregleda = najmanj tri tedne od trenutka, ko je 12 preizkuševalcev vključenih. Zmanjša se samo, če je bil račun odprt pred 13. 11. 2023 ali če je organizacijski (organizacijski račun zahteva D-U-N-S in prav tako, glede na stran, ni vezan na to pravilo; tega nisem preveril, zato »sklepam«). Preizkuševalci morajo imeti račun Google in Play; uporabniki brez Googlovih storitev v štetje ne gredo.

Vir: https://support.google.com/googleplay/android-developer/answer/14151465 (brez datuma strani). Zanesljivost: uradni vir.

## A2. Ciljna raven API

Odgovor: Od 31. 8. 2026 morajo nove aplikacije in posodobitve ciljati Android 16 (API 36) ali višje. Razširitev je bilo mogoče zahtevati do 1. 11. 2026, torej je že mimo. Obstoječe aplikacije morajo za nove uporabnike na novih Androidih ciljati vsaj API 35. Datuma naslednjega dviga stran ne navaja (po dosedanjem ritmu pričakujem avgust 2027 za API 37; to je »sklepam«).

Za Kajros: `targetSdk 35` NE zadošča za novo aplikacijo. Treba je na `targetSdk 36` in `compileSdk 36`, kar spremeni obnašanje (glej B6: obvezen edge-to-edge, predvidljiv »nazaj«, velik zaslon). To je ena od stvari, ki lahko ustavi objavo prihodnji teden. Stran sama pravi, da se povzetek in tabele na njej v pragovih za obstoječe aplikacije razlikujejo, zato v Play Console preveri »Policy status«.

Vir: https://support.google.com/googleplay/android-developer/answer/11926878 (brez datuma). Zanesljivost: uradni vir.

## A11. Preverjanje razvijalcev (Android developer verification)

Odgovor: Odprto za vse razvijalce od marca 2026. Uveljavitev: 30. 9. 2026 v Braziliji, Indoneziji, Singapurju in Tajski; stran navaja tudi 2027 za svetovno širitev (EU in Slovenija zato v 2027, natančen datum ni najden). Aplikacije na certificiranih napravah morajo biti registrirane pri preverjenem razvijalcu, sicer jih ni mogoče namestiti. Pri aplikacijah iz Playa so po poročilih večinoma že pokrite (samodejna registracija), a uradna stran tega izrecno ne pove (»ni najdeno«, kako natančno velja za paket in ključ). Prva faza preverja namestitve iz sedmih trgovin (Google Play, HONOR, OPPO, Samsung Galaxy Store, Transsion Palm, vivo, Xiaomi GetApps). Nadaljnje stalne poti: napredni postopek za »power userje« in ADB. »Limited distribution account«: brez pristojbine, neomejeno aplikacij na do 20 naprav, brez osebnega dokumenta; polni račun 25 $, organizacije rabijo D-U-N-S (do 28 dni).

Za Kajros: razdeljevanje APK s strani `kajros.app/android` bo v 2027 v EU potrebovalo registriran paket `app.kajros` s tistim ključem pri preverjenem razvijalcu. Ker bo isti paket in ključ v Playu, je to najlažje urediti z istim razvijalskim računom; ni nujno za prihodnji teden. Ob podpisu Play App Signing z lastnim ključem (glej A3) je ključ isti na obeh poteh.

Viri: https://support.google.com/android-developer-console/answer/16561738 (brez datuma); poročanje (Android Authority, GSMArena, junij 2026) prek iskalnika. Zanesljivost: uradni vir za rokove in račune, sklepam za Play kritje in EU.

## A3. Play App Signing za že razdeljeno aplikacijo

Odgovor: Pri novi aplikaciji prvo nalaganje samodejno vpiše aplikacijo v Play App Signing z Googlovim ključem. Pred uvedbo v odprti preizkus ali produkcijo pa je mogoče pritisniti »Change key« in uporabiti drug ključ iz računa ali lasten ključ (naložen s PEPK, šifrirana kopija). Po objavi v odprtem preizkusu ali produkciji se ključ za podpisovanje ne da več zamenjati. Ključ za nalaganje (upload key) je ločen in ga Google lahko ponastavi; če izgubiš lasten podpisni ključ, ki si ga dal Googlu, ga ni mogoče ponastaviti. Ključ je mogoče enkrat letno nadgraditi (velja za namestitve na Androidu 17+), nato je treba na novo registrirati prstne odtise pri ponudnikih API. Če je ključ Googlov, lahko iz konzole prenesem univerzalni APK, podpisan z njim, in ga razdelim tudi zunaj Playa.

Za Kajros: dve poti. (1) Naložiti obstoječi lastni ključ prek PEPK in ustvariti nov ključ za nalaganje: namestitev iz Playa in s strani sta potem podpisani enako, zato posodobitev med potema deluje in `PackageInstaller` ne naleti na neujemanje podpisa. To je edina pot, ki ohrani obstoječe namestitve s strani. (2) Googlov ključ: namestitve s strani s starim ključem se ne bodo mogle posodobiti iz Playa (Android zavrne drugačen podpis); uporabnik bi moral odstraniti in ponovno namestiti, in izgubi se podatke. Odločitev je nepovratna ob prvi objavi v odprtem preizkusu/produkciji; zato jo je treba sprejeti PRED prvim zunanjim izdajanjem. Izrecnega stavka »nepovratno za vpis« stran ne vsebuje (sklepam).

Vir: https://support.google.com/googleplay/android-developer/answer/9842756 (brez datuma). Zanesljivost: uradni vir, razen označenega sklepa.

**Preverjeno v glavni seji (8. 11. 2026), dobesedno s strani:** »Your app will be automatically enrolled in quantum-ready, hybrid signing with Google-generated keys.« in »Advanced developers who want to manage their own key can change this default before a release is rolled out in the open testing or production track.« Lasten ključ se naloži z možnostjo »Provide a copy of your app signing key«. Za zaprti preizkus stran ne pove ničesar; ker pa bi preizkuševalec s Googlovo podpisano gradnjo pozneje naletel na drug podpis, je ključ treba izbrati ob ustvarjanju aplikacije, pred prvim nalaganjem.

## A5. Točni alarmi

Odgovor: `USE_EXACT_ALARM` sme samo aplikacija, katere jedro je natančno časovno dejanje; navedena primera sta budilka/časovnik in koledar z obvestili o dogodkih. Zahteva izpolnjeno deklaracijo v Play Console (goo.gle/play-permission-decl-form); neustrezne zavrnejo z odstranitvijo možnosti objave. Za druge primere pravilo napoti na `SCHEDULE_EXACT_ALARM`, ki ga uporabnik odobri sam.

Za Kajros: »budilka za odhod vlaka« je po dobesednem besedilu budilka (jedro aplikacije so zamude in vozni red, ne budilka; zato je tveganje, da pregledovalec reče, da budilka ni jedro). Varneje: deklarirati samo `SCHEDULE_EXACT_ALARM` (uporabnik odobri v nastavitvah, `canScheduleExactAlarms()`) ali deklarirati `USE_EXACT_ALARM` z opisom, da je budilka odhoda osrednja funkcija. Dve hkrati deklarirani dovoljenji sta podvojitev; uradni vir ne pove, da je to kršitev (»ni najdeno«), a `USE_EXACT_ALARM` zavrnitev lahko ustavi celo izdajo. Priporočilo: za Play gradnjo samo `SCHEDULE_EXACT_ALARM` in nadomestek z neizrecnim alarmom, če je zavrnjen.

Vir: https://support.google.com/googleplay/android-developer/answer/16558241 (brez datuma). Zanesljivost: uradni vir za pravilo, sklepam za ujemanje s Kajrosom.

## A4. Samoposodobitev mimo Playa in `REQUEST_INSTALL_PACKAGES`

Odgovor: Pravilo Device and Network Abuse: aplikacija, razdeljena prek Playa, se »ne sme spreminjati, zamenjati ali posodabljati z nobenim drugim načinom kot z Googlovim mehanizmom posodobitev«; prav tako ne sme prenašati izvršljive kode (dex, JAR, .so) iz drugih virov. Izjema je koda, ki teče v navideznem stroju ali tolmaču (npr. JavaScript v WebView). `REQUEST_INSTALL_PACKAGES` je dovoljen le aplikacijam, kjer je nameščanje paketov jedro namena (brskalniki, sporočanje s prilogami, upravljalniki datotek, upravljanje naprav podjetij, varnostno kopiranje, selitev telefona), z deklaracijo v Play Console. Samoposodobitev med dovoljenimi rabami ni navedena.

Za Kajros: Play gradnja mora biti brez `REQUEST_INSTALL_PACKAGES` in brez kode `PackageInstaller`/samoposodobitve (tudi neaktivne; pregledovalci in samodejna analiza iščejo dovoljenje v manifestu). Ločena gradnja za stran (drug flavor, isti paket `app.kajros`, isti ključ) je tehnično mogoča in po besedilu pravil ne krši ničesar, ker pravilo velja za aplikacijo, razdeljeno prek Playa; izrecne potrditve za »dva flavorja« nisem našel (»sklepam«). Pogoj: flavor za Play dejansko ne vsebuje nobene poti do namestitve.

Viri: https://support.google.com/googleplay/android-developer/answer/9888379 ; https://support.google.com/googleplay/android-developer/answer/12085295 (obe brez datuma). Zanesljivost: uradni vir; flavor = sklepam.

## A6. `USE_FULL_SCREEN_INTENT`

Odgovor: Od Androida 14 je posebno dovoljenje. Samodejno ga dobi samo aplikacija, katere jedro so alarm ali sprejem klicev; od 22. 1. 2025 je privzeto vklopljeno samo za take. Deklaracijo »core functionality« je treba izpolniti na strani App content (obvezno od 31. 5. 2024). Brez odobritve mora aplikacija uporabnika sama vprašati (nastavitve `ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT`) in elegantno degradirati: obvestilo z visoko prednostjo (heads-up) namesto celozaslonskega zvonjenja. `canUseFullScreenIntent()` na strani Play politike ni omenjen (»ni najdeno« tam; je API v dokumentaciji Androida).

Za Kajros: budilka odhoda je »alarm«, a jedro Kajrosa je zamuda; deklariraj kot alarm, a pripravi opis. Ob zavrnitvi obvezen padec na heads-up obvestilo.

Vir: https://support.google.com/googleplay/android-developer/answer/13392821 (brez datuma strani, ima 22. 1. 2025). Zanesljivost: uradni vir.

## A7. Storitve v ospredju

Odgovor: V Play Console (Policy > App content) je za vsak tip treba navesti opis funkcije, vpliv na uporabnika, če se opravilo odloži ali prekine, povezavo do videa in primer uporabe. Za `location` so primeri: user-initiated location sharing (npr. »vehicle activity tracking«, video naj pokaže, kako uporabnik funkcijo zažene), navigacija, geofencing. Za `systemExempted` v Playovi strani opisa ni; Android dokumentacija pravi, da ga smejo uporabljati samo sistemske aplikacije, Device Owner itd. in »aplikacije, ki imajo dovoljenje `SCHEDULE_EXACT_ALARM` ali `USE_EXACT_ALARM`«; drugače sistem vrže `ForegroundServiceTypeNotAllowedException`.

Za Kajros: `location` ustreza »user-initiated location sharing« (video: potnik vklopi deljenje, lega gre ven). `systemExempted` je dovoljen samo, dokler gradnja drži dovoljenje za točen alarm; če se za Play odločimo za alarm brez `USE_EXACT_ALARM`/`SCHEDULE_EXACT_ALARM`, je ta tip prepovedan in ne gre; alternativa je `specialUse` z razlago v manifestu (pregleda jo človek v Play Console) ali zvonjenje brez storitve v ospredju. Za Play gradnjo je torej `SCHEDULE_EXACT_ALARM` + `systemExempted` skladno po dokumentaciji, pri čemer je dovoljenje lahko uporabniško odklonjeno (takrat tudi tip pade, zato preveri `canScheduleExactAlarms()` pred storitvijo).

Viri: https://support.google.com/googleplay/android-developer/answer/13392821 ; https://developer.android.com/develop/background-work/services/fgs/service-types . Zanesljivost: uradni vir; posledica za Kajros = sklepam.

## A8. Lega: razkritje, soglasje, Data safety

Odgovor: Lokacija naprave je v politiki User Data »personal and sensitive data«. Vidno razkritje (prominent disclosure) je obvezno, kadar uporaba lahko preseže pričakovanja uporabnika (npr. zbiranje v ozadju); mora biti v aplikaciji, med normalno rabo, takoj pred zahtevo za dovoljenje, z dejanskim pritrdilnim dejanjem (»Sprejmem«); zapustitev zaslona, gumb Nazaj ali domov ni soglasje; samo politika zasebnosti ne zadošča. Predlagana oblika: »[Ta aplikacija] zbira/pošilja [vrsta podatka] za [funkcija], [v katerem primeru].« Data safety: lega, poslana z naprave, tudi na lasten strežnik, je »collected«. Natančna (`ACCESS_FINE_LOCATION`, < 3 km²) in približna sta ločeni kategoriji. »Shared« je samo prenos tretji osebi; prenos na uporabnikovo izrecno dejanje ali po razkritju in soglasju se ne šteje za deljenje. Zbiranje je »optional«, če lahko vsi uporabniki aplikacijo uporabljajo brez njega. Obvezna je politika zasebnosti.

Za Kajros: deljenje lege je izbirno in sproži ga uporabnik; Data safety: Location, precise, collected, optional, namen: App functionality; shared: ne, če drugi vidijo samo vozilo, ne uporabnika (pazi: druga potnika vidita lego vozila, ki je izpeljana iz uporabnikove lege; vseeno napiši v razkritje, da se lega pošilja na strežnik Kajros in da jo vidijo drugi kot lego vozila). Pred sistemskim oknom za lego mora biti naš zaslon z razkritjem in gumbom (ni dovolj, da pove stran WebView, razen če je naš nativni zaslon). Sklepam, da WebView `geolocation` ne sme sprožiti sistemskega okna brez našega razkritja.

Vira: https://support.google.com/googleplay/android-developer/answer/10144311 ; https://support.google.com/googleplay/android-developer/answer/10787469 . Zanesljivost: uradni vir; posledica = sklepam.

## A10 (delno). Zavajanje in vladne povezave

Odgovor: Politika Deceptive Behavior (Misrepresentation): lastnosti aplikacije v seznamu ne smejo lažno trditi, da je aplikacija uradna ali povezana z državo; »Don't impersonate other apps, brands, or government entities.« Posebnega pravila o obvezni izjavi »nismo vladna aplikacija« na tej strani ni našel; izrecno besedilo o državnih podatkih ni najdeno v tem viru.

Za Kajros: v opisu in na zaslonu naj piše »Kajros ni uradna aplikacija SŽ, LPP ali države; podatki: NAP (CC BY-SA 4.0)«. Imena prevoznikov uporabi opisno, ne v naslovu, ikoni, barvah ali logotipih. Izogni se poimenovanju »SŽ« v imenu aplikacije.

Vir: https://support.google.com/googleplay/android-developer/answer/9888077 (brez datuma). Zanesljivost: uradni vir za Misrepresentation; navedba vira in preostalo = sklepam.

## A13. Donacije prek zunanje povezave (Ko-fi)

Odgovor: Izjema v politiki Payments (točka 3) velja samo za »tax exempt donations« (donacije davčno oproščenim organizacijam), pri katerih se Play Billing ne sme uporabiti. Napitnin ali donacij razvijalcu brez davčne oprostitve stran ne obravnava (»ni najdeno«). Točka 4 prepoveduje v aplikaciji (vključno z WebView, gumbi, povezavami, oglasi, vpisnimi tokovi in seznamom v Playu) usmerjati uporabnike na plačilni način mimo Play Billing, razen v programih za zunanje povezave v določenih državah. Dogodek, ki to potrjuje v praksi: AnkiDroid je septembra 2026 prejel zahtevo Googla, naj odstrani povezavo za donacije (Open Collective) ali bo odstranjen iz Playa, ker prejemnik po njihovi presoji ni davčno oproščen; 501(c)(6) potrdilo ni zadostilo; razvijalci so povezavo odstranili pod protestom (poročano 1. 9. 2026, sekundarni vir, izid ni znan).

Za Kajros (ustavi objavo, če se prezre): `kajros.app/donacije` in kartica cilja na `/` se prikažeta v WebView znotraj Play aplikacije, kar je »povezava v WebView na drug plačilni način«. Ko-fi ni davčno oproščen prejemnik. Zato mora Play gradnja donacije skriti v celoti (kartica na `/`, stran `/donacije`, povezava v meniju, besedilo »Podpri«) in ne sme omenjati Ko-fi; stran jo lahko pozna po uporabniškem agentu ali pripetem parametru (pazi: pravila o skrivanju za preglednik pregledovalca = Behavior Transparency, torej mora biti skrivanje enako za vse uporabnike Play gradnje). Donacije ostanejo na spletu in v APK s strani. Sklepam, da prav to Google od AnkiDroid zahteva.

Viri: https://support.google.com/googleplay/android-developer/answer/9858738 (brez datuma); https://zeli.app/story/49520022 (1. 9. 2026, sekundarno poročilo). Zanesljivost: pravilo = uradni vir; izvedba in tveganje = sklepam.

**Popravek glavne seje (8. 11. 2026): sklep »mora skriti« je prestrog.** Točka 3.2 pravila Payments našteva »peer-to-peer payments, online auctions, and tax exempt donations«. Pogosta vprašanja (https://support.google.com/googleplay/android-developer/answer/10281818) pod »Do direct tips or contributions from user to creator require Play's billing system?« pravijo: »In cases where 100% of the tip or contribution from a user goes to the creator and the payment does not grant access to any digital content or services, then we regard this as a peer-to-peer payment and use of Google Play's billing system is not required.« Izjema za napitnino torej obstaja in to je podlaga odločitve z 20. 10. 2026 (`.claude/rules/android.md`, »Podpora v Playu«). Ni pa jasno, ali Google za ustvarjalca šteje tudi razvijalca same aplikacije; primer AnkiDroid kaže, da ga lahko ne. Skrivanje v kanalu `play` je zato varnejša izbira, ne obveznost.

## A9. WebView lastne strani: Minimum Functionality, Webviews and Affiliate Spam

Odgovor: Uradne strani pravil nisem uspel prebrati (stran Spam, Functionality, and User Experience ni bila dosegljiva prek orodja). Iz Googlovega bloga (Android Developers Blog, oktober 2020, še vedno napoti na Policy Center): aplikacije, ki so samo WebView obstoječe spletne strani, poslane predvsem z namenom prometa in ne zanimive aplikacijske izkušnje, so »webview spam« in se odstranijo; tanke ali pokvarjene aplikacije se označijo tudi po Minimum Functionality. Nasvet Googla: vprašaj se, kaj lahko uporabnik v aplikaciji naredi ali naredi bolje kot v spletu, in to zgradi.

Za Kajros: nativni deli (budilka, widgeti, deljenje lege, zvonjenje) so natanko takšna dodana vrednost; v opisu in na posnetkih zaslona jih izpostavi (budilka na zaslonu, widgeti, obvestila), ne samo spletnih zaslonov. Tveganje zavrnitve »samo WebView« je nižje, če prvi zagon in vsaj ena jedrna pot (npr. iskanje odhoda in nastavitev budilke) sta nativna. Izkušenj razvijalcev 2025-2026 zanesljivo nisem našel (»ni najdeno«).

Vir: https://android-developers.googleblog.com/2020/10/developer-tips-and-guides-common-policy.html (oktober 2020). Zanesljivost: uradni vir (stari); današnje besedilo = ni najdeno.

## B6. Spremembe ob `targetSdk 36`

Odgovor (vse uradni vir, Android 16 behavior changes, brez datuma strani):
- Edge-to-edge: odjava (`windowOptOutEdgeToEdgeEnforcement`) je za cilj 36 onemogočena na Androidu 16; aplikacija mora sama obdelati sistemske vložke (insets). Za WebView to pomeni, da mora ovoj pravilno upoštevati vložke ali zagotoviti `padding` (CSS `env(safe-area-inset-*)` in `viewport-fit=cover`), sicer vsebina leze pod vrstico stanja in navigacijo.
- Predvidljivi »nazaj«: za cilj 36 na Androidu 16 se `onBackPressed` ne kliče več in `KEYCODE_BACK` se ne pošilja. Če Kajros za zgodovino WebView prestreza `onBackPressed`, mora preiti na `OnBackPressedCallback`/`OnBackInvokedCallback` (ali začasno `android:enableOnBackInvokedCallback="false"`).
- Velik zaslon (smallest width >= 600 dp): `screenOrientation`, `resizableActivity` in razmerje stranic se ignorirajo; aplikacija zapolni celotno okno. Začasna odjava je `PROPERTY_COMPAT_ALLOW_RESTRICTED_RESIZABILITY`, ki za cilj 37 ne bo več veljala. Če je Kajros zaklenjen na pokonci, je treba preizkusiti tablice in zložljive telefone.
- Drugo: `elegantTextHeight` ni več veljaven (druga razporeditev besedila), `scheduleAtFixedRate` po zamujenih izvedbah požene samo eno; Local Network Permission (`NEARBY_WIFI_DEVICES`) je za zdaj opt-in; Kajros govori samo z internetom, torej ni prizadet (sklepam). Nič od tega ne zadeva točnih alarmov, vendar pregled `AlarmManager` po ciljni ravni 36 ni bil preverjen (ni najdeno).

Vir: https://developer.android.com/about/versions/16/behavior-changes-16 . Zanesljivost: uradni vir; posledica za Kajros = sklepam.

## B1. Jetpack Compose in Material 3

Odgovor: Najnovejši BOM po strani je 2026.09.00 (material3 1.4.0, foundation/runtime 1.12.1). Stabilni material3 je 1.4.0; 1.5.0 je v fazi release candidate (1.5.0-rc01, 4. 11. 2026; beta02 21. 10. 2026), stabilna pričakovana kmalu (sklepam). Stanje M3 Expressive v 1.5.0 prednastavkih: ButtonGroup stabilen (alpha22, 17. 6. 2026), FloatingToolbar stabilen (alpha22), MotionScheme stabilen (alpha15, 25. 2. 2026), LoadingIndicator in MaterialShapes ponovno eksperimentalna (alpha19, 6. 5. 2026: »Revert MaterialShapes and LoadingIndicator promotions to stable«). Najmanjšega minSdk stran ne navaja (»ni najdeno«; Compose praviloma zahteva 23, Kajrosov 26 je dovolj, sklepam). Opozorilo: alpha različice so v septembru 2026 začasno zahtevale compileSdk 37; v alpha23 so zahtevo odstranili.

Za Kajros: nativni zasloni na `material3 1.4.0` ali 1.5.0 (ko bo stabilen); Expressive eksperimentalno za LoadingIndicator/MaterialShapes z `@OptIn`. Ker je Play zahteva cilj 36, `compileSdk 36` zadošča.

Viri: https://developer.android.com/develop/ui/compose/bom/bom-mapping ; https://developer.android.com/jetpack/androidx/releases/compose-material3 (datumi izdaj v tabeli). Zanesljivost: uradni vir (preslikava BOM, deloma ugotovljena iz razporeda vrstic).

## B5. Android 16 Live Updates (ProgressStyle)

Odgovor (delno): Android 16 uvaja `Notification.ProgressStyle` za »uporabniško sprožene poti od začetka do konca« (primeri: prevoz, dostava, navigacija) s segmenti in točkami ter ikono sledilnika; za prikaz kot promovirano obvestilo je treba izpolniti »promoted visibility« zahteve (podrobnosti v dokumentaciji obvestil, nisem prebral). Navedeno je tudi, da se mora napredek posodabljati pogosto in natančno. Vzorec: github.com/android/platform-samples (user-interface/live-updates). Seznam proizvajalcev, ki jih kažejo (Samsung Now Bar itd.), in novosti Androida 17: ni najdeno.

Za Kajros: sklepam, da je »vlak prihaja, +3 min« primeren kandidat za zaupanja vredno uporabniško sprožen opravilo (spremljam vožnjo) in ga lahko zapišemo z `ProgressStyle` za Android 16+, s sklopom običajnega obvestila na starejših napravah.

Vir: https://developer.android.com/about/versions/16/features/progress-centric-notifications . Zanesljivost: uradni vir za API; primernost = sklepam.

## A12. Obvezno za vpis v trgovino

Odgovor (iz uradne strani o grafiki; ostalo manjka): ikona 512 x 512 px, 32-bitni PNG z alfa, največ 1024 KB; funkcijska grafika (feature graphic) 1024 x 500 px, JPEG ali 24-bitni PNG brez alfe; posnetki zaslona najmanj dva skupaj za objavo, vsak 320 do 3840 px na stranico, daljša stranica največ dvakrat daljša od krajše, do 8 na vrsto naprave; za tablice 7" in 10" (če jih ciljamo) najmanj 4 posnetki, 1080 do 7680 px, 16:9 ali 9:16; kratek opis največ 80 znakov. Naslov, polni opis, ocena vsebine (IARC vprašalnik), ciljna publika, izjava o oglasih, Data safety in povezava do politike zasebnosti (obvezna za Data safety) na tej strani niso bili najdeni v prebranem delu: »ni najdeno« v tem pregledu, a Data safety in politika zasebnosti sta potrjena v A8. Brisanje računa ni potrebno, ker Kajros nima računov (sklepam; deljenje lege je anonimno).

Vir: https://support.google.com/googleplay/android-developer/answer/9866151 (brez datuma). Zanesljivost: uradni vir za mere; seznam = deloma ni najdeno.

## A14. Konkurenca v Playu

Odgovor: Najden je le uradni »Grem z vlakom« (SŽ, paket com.margento.sz.slovenskezeleznice): vozni redi domačih vlakov in nakup vozovnic (kartica, Moneta), slovensko in angleško; zamude so v zavihku »Zamude in ovire« in jih SŽ objavi, ko jih zna. Ocene, števila namestitev in pritožb nisem uspel prebrati (izpis iskalnika jih ni vseboval); nativen ali WebView ni ugotovljeno. Za LPP, Arriva, Nomago in zamudil.si ni najdeno ničesar (iskalnik ni vrnil rezultatov; ne pomeni, da aplikacij ni). Spomin projekta (konkurenca-zamudil): zamudil.si ima napoved = prenos zamude, ima perone in sestavo vlaka; Play-prisotnost ni preverjena.

Vir: https://play.google.com/store/apps/details?id=com.margento.sz.slovenskezeleznice . Zanesljivost: delno; ocene in namestitve = ni najdeno. Uporabljenih iskanj: 2 od 4.

## B2. Navigation 3

Odgovor: `androidx.navigation3` stabilni 1.2.1, alfa 1.3.0-alpha04 (4. 11. 2026). Torej stabilna knjižnica za Compose (sklepam: primernejša od `navigation-compose` za nov projekt; primerjalne izjave Googla v tem viru nisem bral).

Vir: https://developer.android.com/jetpack/androidx/releases/navigation3 . Zanesljivost: uradni vir za različice.

## B3. MapLibre Native Android in ovoj za Compose

Odgovor: Zadnja Android izdaja na GitHubu: `android-v2026.11.2-globe` (2. 11. 2026, pre-release); zadnja stabilna oznaka `android-v13.7.1` (15. 10. 2026), ki je dodala eksperimentalni C vtičnik za lastne vrste slojev (samo artefakti `-with-plugin-api`). Naložitev 3D modelov ni omenjena; zato Kajrosovih lastnih WebGL slojev (GL JS) ni mogoče neposredno prenesti: v Native bi bilo treba pisati lasten sloj prek vtičnika (C/OpenGL ali Vulkan), kar je veliko dela. Podpora za globe v slogu (`"projection": {"type":"globe"}`). Velikost na ABI: ni najdeno. `maplibre-compose` (ovoj za Compose Multiplatform): Android beta, iOS beta, Desktop alpha, Web alpha; »manjše izdaje lahko vsebujejo prelomne spremembe«; zadnja številka različice, branje sloga JSON in lastni sloji: ni najdeno. Sklepam: slog JSON (MapLibre style spec) je skupen GL JS in Native, vendar sta funkcije različni (lastni sloji, 3D), zato je treba karto preizkusiti, preden se zaveže selitev.

Viri: https://github.com/maplibre/maplibre-native/releases ; https://github.com/maplibre/maplibre-compose . Zanesljivost: uradni vir za različice in status; slog JSON in lastni sloji = sklepam.

## B4. Widgeti: Glance proti RemoteViews

Odgovor: ni najdeno v tem pregledu (preveril nisem). Iz splošnega znanja (neuradno, neprever.): Glance je Compose API, ki ob izrisu še vedno proizvaja RemoteViews; prednosti so enotni jezik z aplikacijo in lažje odzivne velikosti, slabosti odvisnost od knjižnice AndroidX in omejen nabor komponent. Kajrosovih pet obstoječih widgetov z RemoteViews deluje; selitev se ob prehodu na Compose splača samo, če želimo deliti kodo tem; ne nujno za objavo.

Zanesljivost: »sklepam« (brez vira).

## B7. Velikost in zagon

Odgovor: ni najdeno v tem pregledu. Sklepam iz splošnega znanja: Compose z R8 prinese nekaj MB več; Baseline Profile pospeši hladen zagon pri Compose za okoli 20-30 % (neuradna številka, neprever.). Kajros nima knjižnic AndroidX; prehod doda odvisnosti. Meri po izdelavi.

## B8. Potisna obvestila brez Googla

Odgovor: UnifiedPush je živ: 5-letnica, F-Droid, 8. 1. 2026; vzdrževalec dela polni delovni čas od konca 2024; ntfy podprt kot distributer od 2022; specifikacija zahteva šifriranje in VAPID. Za »spremljaj mojo vožnjo 30 min« je lastno preverjanje (AlarmManager z točnim alarmom ali storitev v ospredju, ki jo uporabnik zažene, ali WorkManager) po mojem sklepu dovolj, ker je uporabniško sprožena kratka sled; Doze lahko zamakne WorkManager, zato je za uro-natančnost potreben točen alarm ali storitev v ospredju. Stanje ntfy aplikacije 2026 ni najdeno.

Vir: https://f-droid.org/2026/01/08/unifiedpush-5-years.html (8. 1. 2026). Zanesljivost: uradni vir za UnifiedPush; Doze posledica = sklepam.

## B9. Kotlin Multiplatform in Compose Multiplatform za iOS

Odgovor: JetBrains je Compose Multiplatform za iOS razglasil za stabilnega in pripravljenega za produkcijo v izdaji 1.8.0 (maj 2025); poznejši članki (februar 2026) to obravnavajo kot ustaljeno. Trenutne različice nisem potrdil. Priporočilo (sklepam): če je iOS »kdaj pozneje«, delitev poslovne logike (Kotlin Multiplatform) je zrelejša poti kot deljenje UI; za Kajros je glavni dobiček zaenkrat to, da so podatki že na strežniku in je iOS mogoče izdelati kot PWA ali WebView.

Vir: https://blog.jetbrains.com/kotlin/2025/05/compose-multiplatform-1-8-0-released-compose-multiplatform-for-ios-is-stable-and-production-ready/ (maj 2025). Zanesljivost: uradni vir za 1.8.0; ostalo = sklepam.

## B10. Hibrid »nativna lupina + spletni zasloni« (Hotwire Native)

Odgovor: ni najdeno (iskanje ni vrnilo ničesar o Hotwire Native za Android). Iz splošnega znanja (neuradno): Hotwire Native (nasledniku Turbo Native) je namenjen natanko postopni selitvi: spletni zasloni v nativni navigaciji z nativnimi zasloni po poteh, brez preoblikovanja. Zrelost 2026: ni preverjeno. Isti učinek z obstoječim WebView in nativnimi zasloni dosežemo tudi sami.

Zanesljivost: »sklepam« (brez vira).

## Povzetek ustavljalcev objave

1. A1: račun po 13. 11. 2023 rabi zaprti preizkus 12 ljudi x 14 dni in nato pregled do 7 dni. Brez tega »prihodnji teden« ni mogoč.
2. A2: nove aplikacije od 31. 8. 2026 morajo ciljati API 36; Kajros je na 35. B6 našteva posledice.
3. A4: Play gradnja brez `REQUEST_INSTALL_PACKAGES` in brez samoposodobitve.
4. A13: donacije (Ko-fi) v WebView so tveganje (AnkiDroid, 1. 9. 2026), čeprav izjema za napitnino ustvarjalcu obstaja (popravek v A13); v Play gradnji jih je varneje skriti.
5. A3: ključ za podpisovanje se odloči pred prvim izdajanjem; za ohranitev namestitev s strani naložiti lasten ključ (PEPK).
6. A5/A6/A7: deklaracije za točni alarm, full-screen intent, storitve v ospredju (`systemExempted` samo z dovoljenjem za točen alarm).
7. A8: vidno razkritje pred sistemskim oknom za lego, Data safety: natančna lega, zbrana, izbirna.
