# ROADMAP — bin picking tankih prirobnic iz ene kamere

Vse številke v tem dokumentu so izmerjene na sintetičnem setu z ukazom

```
python -m flange_picker.evaluate -n 12 --seed 100
```

Ground truth je znana po konstrukciji (generator `flange_picker/synth.py`).

---

## Zdaj

- [ ] **Vrstni red plasti iz prekrivanja, ne iz globine.** Povratna informacija
  z resnicne slike: prvi kandidat je bil pravi, uvrstitve 2-6 pa so bili
  zakopani kosi. Vzrok je nacelen - globina iz velikosti elipse ima negotovost
  ~2-3 mm, plasti pri 1-2 mm debelih kosih pa so razmaknjene manj od tega.
  Visina zato ne more lociti, kdo je na vrhu. Resitev je 2D sklepanje: kjer se
  obrisa dveh kosov sekata, je zgoraj tisti, ki mu obris tam ni prekinjen.
  Iz teh parnih relacij se sestavi delna urejenost in kosi brez nikogar nad
  seboj so kandidati za prijem. Neodvisno od kalibracije in od f_px.

- [ ] **Poln zaboj: višina Z v načinu `reference_plane: rim`.** X in Y sta
  pravilna (4 mm), Z pa zahteva dober `f_px`; pot prek delovne razdalje v tem
  načinu še ni skladna (uporabi merilo roba namesto dna). Do takrat je način
  eksperimentalen.
- [ ] **Čas obdelave 7.7 s pri 90 kosih** (267 elips). Za takt celice je
  treba fit omejiti na kandidate prave velikosti — velikost kosa v pikslih je
  po detekciji zaboja znana, zato je predfiltriranje poceni.

- [ ] **Preciznost detekcije 96 %.** Preostali lažni kandidati nastanejo v
  gručah prekrivajočih se kosov, kjer razpolavljanje konture rodi vec fitov
  istega roba. Naslednji korak: razbijanje kontur po krivinskih vrhovih in
  združevanje lokov iste elipse namesto slepega razpolavljanja.
- [ ] **Z RMSE 2.0–2.2 mm, odmik ~1.0–1.5 mm.** Omejuje ga sistematični odmik
  lege roba (+0.13 px na zunanjem robu). Iz razmerja premerov ga ni mogoče
  izluščiti (glej K11) — potrebna je referenčna meritev na znanem kosu ali
  model debeline.
- [ ] **`f_px` brez podatka o steni ostaja pri 11.9 %.** Pri navpični kameri je
  to fizikalna meja (K1). Priporočena rešitev je podati `box.wall_height_mm` in
  `box.wall_thickness_mm` (napaka 2.3 %) ali `camera.working_distance_mm` (4 %).

## Naslednje

- [ ] Ocena negotovosti poze iz kovariance fita elipse (namesto današnjega
  hevrističnega množenja faktorjev zaupanja).
- [ ] Korekcija za debelino: pri velikem naklonu je viden bočni rob, kar
  premakne navidezni obris navzven in sistematično zniža oceno Z.
- [ ] Kalibracija sistematičnega odmika roba na referenčnem kosu: eno prirobnico
  položi na prazno dno, izmeri odmik in ga odštej. Trenutno je ta odmik
  +0.13 px (≈ 2.7 mm v Z pri 700 mm) in je edini preostali vir odmika Z.
- [ ] `f` iz razmerja stranic, kadar je le ena izginjajoča točka končna
  (kamera nagnjena okoli ene same osi — pri montaži pogost primer).
- [ ] Detekcija sprijetih/nasedlih prirobnic po dvojnem robu.

## Raziskati

- RANSAC na robnih točkah namesto navadnega fita (odpornost na outlierje).
- Iterativna refinacija poze z reprojekcijo obeh krogov hkrati.
- Hough krogov kot hitra predselekcija (danes gre fit čez vse konture).
- Prava kalibracija s šahovnico kot nadgradnja `autocalib` — edina pot do
  absolutne globine pri strogo navpični kameri (glej ugotovitev K1 spodaj).
- Modeliranje popačenja leče (danes zanemarjeno; pri kakovostni optiki ~1 %).
- Samodejni popravek merila iz premerov prirobnic, kadar preverjanje merila
  pade — nevarno, če na dnu ne leži noben kos, zato danes le opozorilo.
- Časovna integracija: po vsakem pobiranju se scena spremeni le lokalno.

## Končano

### Izmerjene metrike (12 scen, seed 100)

| Metrika | Prvi mejnik | Po izboljšavah | + vrata prekritosti |
|---|---|---|---|
| detekcija — recall (v sliki) | 0.918 | **0.986** | 0.973 |
| detekcija — preciznost | 0.827 | 0.960 | **1.000** |
| okvir zaboja na voljo | 83 % | **100 %** | 100 % |
| ujemanje poze — recall | 0.891 | **0.973** | 0.973 |
| XY RMSE | 0.36 mm | 0.36 mm | **0.26 mm** |
| Z RMSE | 1.97 mm | 2.03 mm | **1.54 mm** |
| naklon RMSE | 2.09° | 1.78° | **1.30°** |
| relativna napaka `f_px` | 11.0 % | 11.9 % | **2.3 %** |
| prvi kandidat je iz vrhnje plasti | 80 % | **83 %** | 83 % |

Zadnji stolpec: z gradientno mero vidnosti in `scoring.max_occlusion`.
Metrike poze so računane le na scenah z veljavnim okvirom; detekcija se meri v
sliki in je zato neodvisna od kalibracije.

### Ugotovitve, ki so oblikovale zasnovo

**K1 — `f_px` pri navpični kameri ni opazljiv.** Če ravnina dna leži
fronto-paralelno, je napačen `f` natanko enakovreden podobnostni preslikavi
scene: dno, prirobnice na njem in vsa razmerja ostanejo skladni. Izmerjeno:
pri kameri z 0° nagiba je cenilka skladnosti po `f` popolnoma ravna (0.000° za
vse `f` med 800 in 2000). Šele nagib kamere naredi problem rešljiv — pri 5°
nagiba je razlika 0.24° za 8 % napake v `f`.
Praktična posledica: za absolutno višino potrebuješ dodatno informacijo. Najboljša
je višina stene zaboja (glej K9, napaka 2.3 %), sledi `camera.working_distance_mm`
(4 %); pomaga tudi nagib kamere za nekaj stopinj.

**K2 — napaka `f` skoraj ne pokvari X, Y in naklona.** Napačen `f` skalira
globino, lateralne koordinate na dnu pa določa homografija, ki `f` ne
potrebuje. Izmerjeno: scene z 28–31 % napako `f` imajo XY RMSE še vedno
1–2 mm. Zato je koda ločena na `frame_confidence` (X, Y, naklon) in
`f_confidence` (absolutno merilo) — in sistem se degradira šele, ko ni
zaboja, ne ko je `f` negotov.

**K3 — nesoglasje koncentričnega para je za oceno `f` prešibko.** Signal je
drugega reda v `r/Z` ≈ 0.03. Izmerjeno na idealnih konikah: 60 % napake v `f`
premakne cenilko za 0.0016 (v enotah rad + relativna razdalja), medtem ko je
šum fita na realni sliki 0.5. Razmerje signal/šum ≈ 1:300. Metoda ostaja v
kodi (`autocalib.refine.method: pair_consistency`) za primerjavo, privzeta pa
je `plane_consensus`, ki je ~100× močnejša. Nesoglasje para se še vedno
uporablja za razreševanje dvoumnosti poze in za oceno zaupanja — tam je
uporabno.

**K4 — CLAHE in bilateralni filter premakneta rob.** Izmerjeno: ob šumu
prestavita vrh gradienta za +0.28 px, kar je pri polmeru 35 px že 0.8 % napake
v Z (≈ 5 mm). Rešitev: Canny na izboljšani sliki odloča, **kje** je rob,
subpikselska lega pa se meri na surovi sliki. Po popravku je odmik +0.13 px.

**K5 — polariteta roba loči prirobnico od sence in luknjo od obrisa.** Pri
kovinskem obrisu svetlost navzven pada (polariteta ≈ −1.0), pri luknji in
vrženi senci pa raste (≈ +1.0). Po velikosti tega ni mogoče ločiti, ker je kos
višje v kupu videti večji. Vgrajeno v parjenje in v izbiro polmera pri
nesparjenih elipsah — brez tega je globina osamljene luknje 2.5-krat napačna.
Ta popravek je dvignil recall poze s 0.55 na 0.89.

**K9 — zgornji rob zaboja je druga ravnina na znani višini in edini vir
absolutnega merila pri navpični kameri.** Za vsako ravnino velja `s = f/Z`,
zato iz `Z_dno − Z_rob = h` sledi `f = h·s_dno·s_rob/(s_rob − s_dno)`. Izmerjeno:
napaka `f` pade z 11.9 % na **2.3 %** (mediana 2.8 %, najslabša 6.0 %), kar je
bolje od prioritete delovne razdalje (4.0 %). Zahteva le višino in debelino
stene — podatka, ki ju uporabnik o svojem zaboju ima.

Dvoje je bilo pri tem bistveno:
- Napaka se **ojači za faktor Z/h ≈ 12**, zato morata biti oba pravokotnika
  izostrena subpikselsko; brez tega je metoda slabša od rezervne vrednosti.
- Potreben je neodvisen test veljavnosti, sicer napačno prepoznan "rob" da
  napako 27–49 %. Dno in rob sta soosna, zato **bočni odmik njunih središč**
  čisto loči dobre ocene (0.0–0.8 mm) od slabih (4.0–8.5 mm).

**K10 — fit stranice se prilepi na napačen vzporedni rob.** Dno in zgornji rob
zaboja sta v sliki le nekaj deset pikslov narazen. Regresija čez širok pas ju
povpreči, izbira najmočnejšega roba pa lahko vzame sosednjega. Pravilno je
vzeti **najbližji dovolj močan** rob: začetna ocena je prior. Brez tega je
izostritev roba odnesla za 13.9 px in podrla oceno `f` iz dveh ravnin.

**K11 — odmik roba je iz razmerja premerov opazljiv le kot skupna komponenta.**
Iz `(a_out − d)/(a_in − d) = D_out/D_in` sledi `d = (R·a_in − a_out)/(R − 1)`.
Ocena je natančna (razpršenost 0.02 px), a izmeri le *skupni* odmik obeh robov;
ta je bil na testnem setu −0.00 px, medtem ko je dejanski zunanji +0.13 px in
notranji +0.04 px. Model razlike po zasnovi ne vidi. Ob premalo parih postane
ocena šumna (+0.24 px pri dveh kosih) in popravek podre ujemanje para, zato je
privzeto **izklopljen** in dodatno varovan s pragom razpršenosti. Za odpravo
preostalega odmika Z je potrebna referenčna meritev na znanem kosu.

**K19 — mera vidnosti je scensko odvisna; absolutni prag ni smiseln.**
Izmerjeno na resnicni fotografiji: popolnoma viden kos doseze surovo vidnost
0.67-0.83, ne 1.0, ker se del obrisa dotika sosedov iste kovine, kjer kontrasta
ni. Absolutni prag 0.75 je zato prepustil 2 kosa od ~30. **Razvrscanje** mere pa
je pravilno - na vrhu so bili res vidni kosi. Resitev je normiranje na najbolje
viden kos v isti sceni (`scoring.occlusion_normalise`); sele tako prag
"10 % prekritosti" pomeni to, kar naj bi. Varovalo: ce je tudi najboljsi kos pod
`occlusion_reference_floor`, se normiranje ne izvede in scena dobi opozorilo.

Ob tem se dvoje:
- Rob se isce v ozkem pasu vzdolz normale (fit ni popoln), kar dvigne vidnost
  dobrih kosov za ~0.1 brez ucinka na prekrite.
- Brez okvira zaboja se clena "visina" in "oddaljenost od sten" izlocita iz
  ocene: visina izhaja iz globine, ta pa ima pri 1-2 mm kosih vecjo negotovost
  od razmika plasti - clen je cist sum. Rangiranje takrat nosita vidnost in
  zaupanje.

**K17 — moj generator kandidatov je bil ozko grlo, ne mera vidnosti.**
Domneval sem, da slabse osvetljeni kosi padejo na meri vidnosti. Meritev na
resnicni fotografiji je to ovrgla: obrisov prave velikosti je sploh nastalo le
**11**, vidnih kosov pa je ~30. Vecina jih nikoli ni prisla do elipse.

Primerjava z uveljavljenimi detektorji na isti sliki:

| detektor | elips prave velikosti | cas |
|---|---|---|
| moj (kontura → fit → razpolovi) | 11 | 7 s |
| `cv2.HoughCircles` | 22 | 0.3 s |
| **`cv2.ximgproc.EdgeDrawing.detectEllipses`** | **30** | **0.1 s** |

EdgeDrawing gradi robne verige po ujemanju smeri gradienta, jih razbije na loke
in loke iste elipse zdruzi — po vzoru ELSD in Fornaciarija. Ravno to manjka
mojemu razpolavljanju konture, kadar je obris razbit na vec kratkih lokov.
Uporabljen je kot drugi vir kandidatov (`ellipse.detector: both`); o tem, kateri
so kosi, se naprej odlocajo polariteta, parjenje in vidnost. Ucinek: parov na
fotografiji 3 → **13**.

Iz iste literature (LSD) je prevzeta se spodnja meja jakosti gradienta iz
**kvantizacijske napake** (ρ = q/sin τ ≈ 5 sivinskih nivojev) namesto praga
glede na kontrast scene, in merilo kontrasta iz **okolice kosa**, ne cele slike.

**K18 — izbira merila sme upostevati le trdne pare.** Ko so dodatni kandidati
vstopili v izbiro pravokotnika zaboja, se je merilo spremenilo in filter
velikosti je zavrnil pravi kos kot "3.7-krat prevelik". Izbira merila zdaj
uposteva le sparjene kandidate z zadostno podprtostjo.

**K16 — vidnost obrisa se najbolje meri iz gradienta, ne iz bližine robnih
točk.** Primerjava štirih mer proti resnični vidnosti (210 kosov na gostih
sintetičnih scenah z vzorčkom na površini):

| mera | korelacija | AUC |
|---|---|---|
| bližina robnih točk (prejšnja) | 0.935 | 0.998 |
| bližina + ujemanje smeri gradienta | 0.983 | 0.999 |
| **radialni gradient vzdolž oboda** | **0.992** | **1.000** |
| profil svetlosti znotraj/zunaj | 0.970 | 0.996 |

Zmagovalka je hkrati najpreprostejša: ne potrebuje robnih točk ne KD-drevesa,
le gradient slike v točkah oboda. Bližina robnih točk je pri perforiranih kosih
zavedena, ker robne točke ležijo povsod po površini — vzorček na kosu je bilo
treba dodati v generator, sicer so bile vse štiri mere videti enako dobre
(AUC 1.000).

Dvoje je bilo pri vgradnji bistveno:
- Predznak mora priti iz same elipse. Obris je svetel znotraj, luknja temna;
  fiksen predznak je zavrgel vse luknje in s tem podrl parjenje.
- Na sintetičnih scenah popolnoma viden kos doseže ~1.0, na resnični fotografiji
  pa 0.81 (fit ni popoln, deli obrisa se dotikajo sosedov enake svetlosti).
  Prag `scoring.max_occlusion` je zato 0.25, ne 0.10.

Učinek na sintetičnem setu: **preciznost detekcije 0.96 → 1.00**, XY RMSE
0.36 → 0.26 mm, Z RMSE 2.03 → 1.54 mm, ob majhni ceni v recallu (0.986 → 0.973
— prav zakopani kosi, ki jih vrata namenoma zavržejo).

**K15 — na resnični fotografiji je bila pravilna le prva uvrstitev.** Zaboj
(koritast, poševne stene, poln do vrha) je razkril troje, česar sintetične
scene niso: pri 8000×6000 kos preseže `max_semi_major_px`; perforirana površina
da 931 elips, od tega ~900 iz vzorčka na kosu; in napačno prepoznana ravnina
dna je nagnila okvir tako, da je naklon narasel s pravih 7-18° na 50-67°.
Prvi dve rešita zmanjšanje slike in predfilter po pričakovani velikosti, tretjo
`box.reference_plane: none`. Kar ostaja odprto, je vrstni red plasti - glej
prvo postavko v `## Zdaj`.

**K13 — poln zaboj je drugačen problem kot redko posut.** Mock-up po realni
fotografiji (90 kosov v več plasteh, vijačne luknje, dno popolnoma pokrito):

| Meritev | Rezultat |
|---|---|
| detekcija vrhnje plasti | 25/30 = **83 %** |
| pravilnih med prvimi 5 kandidati | **5/5** |
| pravilnih med prvimi 10 | **10/10** |
| pravilnih med prvimi 20 | 19/20 |
| kosov z obema robovoma vidnima | 18/30 |
| kosov z vidno le luknjo | 7/30 |
| čas obdelave | 7.7 s |

Trije nauki:
- Preciznost čez celoten seznam (50 %) je zavajajoča — dolgi rep nizko
  uvrščenih zavrne že rangiranje. Merodajna je natančnost prvih N.
- Parjenje pri 18/30 ni napaka algoritma, ampak **fizikalna meja**: v polnem
  zaboju je pri dobri tretjini kosov vidna le luknja. Ti dobijo nizko zaupanje
  in zastavico `orientation_ambiguous` (K8).
- Dno ni vidno, zato koordinatnega sistema iz njega ni. Dodan je način
  `box.reference_plane: rim`, ki za referenco vzame zgornji rob zaboja:
  napaka XY pade s 34 mm na **4 mm**.

**K14 — izboljšava `f` iz scene je nevarna in je izklopljena.** Na redkih
scenah se ne sproži (občutljivost ~0, glej K1 in K3), na gosti sceni pa se je
`plane_consensus` sprožil in dal **f = 3600 namesto 1300** (177 % napake).
Cenilka je pri velikem številu nagnjenih kosov zavedena. Privzeto je zdaj
`autocalib.refine.enabled: false`; zanesljivi viri `f` ostajajo podatek o steni
zaboja, delovna razdalja in izginjajoče točke.

**K12 — preverjanje merila je smiselno le na sparjenih kandidatih.** Obroč
sence je natanko 10 % večji od kosa; ko je vstopil v preverjanje, je to zavrnilo
popolnoma dober okvir (zaboj zaznan na 1.1 px). Ta ena vrstica je dvignila
razpoložljivost okvira z 83 % na 92 %.

**K8 — močno nagnjeni kosi: luknja je tista, ki reši smer nagiba.** Izmerjeno
na kosih, nagnjenih za 45°:

| primer | najden | napaka naklona | napaka azimuta | zrcalni preobrati |
|---|---|---|---|---|
| sam, 8 azimutov × 3 lege | 24/24 | ≤ 3.2° | ≤ 2.8° | 0/24 |
| sam, 38 naključnih poz | 38/38 | — | ≤ 2.9° | **0/38** |
| naslonjen na drug kos (prekritje do 30 mm) | 4/4 | ≤ 1.8° | ≤ 1.7° | 0/4 |
| ob steni (do 22 mm od stene) | 3/3 | ≤ 1.4° | ≤ 0.9° | 0/3 |
| **ista elipsa brez vidne luknje** | — | — | — | **4/8** |

Dokler je luknja vidna, soglasje notranje in zunanje elipse zrcalno rešitev
zanesljivo izloči. Brez luknje pa opore ni: velikost naklona ostane pravilna,
smer pa je približno met kovanca. Zato je dodana zastavica
`orientation_ambiguous`, zaupanje pa pada z naklonom
(`pose.unpaired_ambiguous_tilt_deg`). Pri ravnem kosu zrcalna rešitev sovpada s
pravo, zato se zastavica takrat ne postavi.

Praktična meja naklona je ~65–70°; pri 75° in več kosa ni več mogoče zanesljivo
zaznati (viden je kot črtica).

**K7 — zaupanje mora biti del ocene, ne le poročano ob njej.** Brez tega so se
v degradiranem načinu nesparjeni kandidati (robovi senc, zaupanje 0.25)
uvrstili pred trdno detektirane prirobnice (zaupanje 0.97), ker jim je napačna
globina dala boljšo oceno "višine". Zaupanje je zato uteženi člen ocene
(`scoring.weights.confidence`).

**K6 — koordinatni sistem zaboja ima neizogibno 2-kratno dvoumnost.**
Pravokotnik brez oznak izgleda enako po zasuku za 180°. Fiksirano je le to, da
os X teče vzdolž `box.w_mm`. Za absolutno orientacijo je potrebna oznaka na
enem vogalu ali `box.corners_px` v configu.

### Opravljeno delo

- [x] `autocalib`: detekcija zaboja (konture + Houghova rezerva + ročni vogali),
      izostritev vogalov z ortogonalno regresijo stranic na subpikselskih
      robovih (0.4 px natančnost vogalov), homografija dna, `f` iz izginjajočih
      točk, izboljšava `f` po skladnosti z ravnino dna, izbira pravega
      pravokotnika po premerih prirobnic, preverjanje merila z degradacijo.
- [x] `preprocess`: CLAHE, bilateralni filter, maskiranje spekularnih odsevov.
- [x] `edges`: Canny + subpikselska izostritev po gradientu (Devernay);
      lega se meri na surovi sliki (glej K4).
- [x] `ellipse`: direktni LSQ fit (Halir–Flusser), rekurzivna delitev kontur,
      polariteta roba, parjenje notranje/zunanje elipse.
- [x] `pose`: poza iz kroga z lastno izpeljavo (obe rešitvi), razreševanje
      dvoumnosti s soglasjem notranje in zunanje elipse; numerično preverjeno
      na 150 naključnih pozah (napaka < 1e-3 mm).
- [x] `scoring`: rangiranje po višini, naklonu, prekrivanju, oddaljenosti od
      sten in prostem kolobarju; prijemna točka na sredini najširšega prostega
      loka kolobarja.
- [x] `synth`: generator scen z nadvzorčenjem (brez tega je fit polmera
      pristranski za +0.5 px), perspektivo, senčenjem, odsevi, šumom in
      zlaganjem kosov.
- [x] `pipeline` + `cli.py` + `--debug` overlay-i za vsak korak.
- [x] 56 testov (geometrija, autokalibracija, cevovod, nagnjeni kosi, robni
      primeri) — vsi zeleni.

### Odprto vprašanje za naročnika

Pri `D_out = 40 mm` in `D_in = 16 mm` je kolobar širok **12 mm**, sesalna
čašica pa ima **15 mm**. Čašica torej ne more nalegati v celoti — vedno bo
segala čez luknjo ali čez zunanji rob. Sistem to javi kot opozorilo in
poroča `cup_fit_ratio` (0.8), kandidatov pa ne zavrne, razen če se vklopi
`gripper.require_full_cup_clearance`. Možnosti: manjša čašica (≤ 12 mm),
čašica z zaporo čez luknjo, ali potrditev, da delno naleganje zadošča.
