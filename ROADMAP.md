# ROADMAP — bin picking tankih prirobnic iz ene kamere

Vse številke v tem dokumentu so izmerjene na sintetičnem setu z ukazom

```
python -m flange_picker.evaluate -n 12 --seed 100
```

Ground truth je znana po konstrukciji (generator `flange_picker/synth.py`).

---

## Zdaj

- [ ] **Detekcija dna zaboja je najšibkejši člen.** Na 2 od 12 scen (17 %)
  pravokotnik dna ni najden in sistem se degradira na relativno rangiranje.
  Vzrok: kontura dna se prekine tam, kjer se prirobnica dotika roba, ali pa
  Canny združi rob dna s steno. Ideje: iskanje dna z znanim merilom kot
  predznanjem (iz zgornjega roba napovej, kje mora biti dno), aktivni model
  pravokotnika, ali segmentacija po svetlosti dna namesto po robovih.
- [ ] **Odpoved detekcije pri močnem prekrivanju.** Detekcija v sliki najde
  91.8 % kosov; manjkajo predvsem tisti, ki jim je viden le kratek lok.
  Naslednji korak: razbijanje kontur po krivinskih vrhovih in združevanje
  lokov iste elipse namesto slepega razpolavljanja.
- [ ] **Lažni kandidati (detekcijska preciznost 82.7 %).** Večina jih je robov
  senc in odsevov. Polariteta roba je večino že odstranila; ostanek zahteva
  bodisi RANSAC bodisi preverjanje na ponovni projekciji.

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

| Metrika | Brez prior | Z znano delovno razdaljo (±3 %) |
|---|---|---|
| detekcija — recall (v sliki) | 0.918 | 0.918 |
| detekcija — preciznost | 0.827 | 0.827 |
| okvir zaboja na voljo | 83 % | 83 % |
| XY RMSE | **0.36 mm** | 0.39 mm |
| Z RMSE | **1.97 mm** | 2.43 mm |
| Z odmik (bias) | +1.07 mm | +1.52 mm |
| naklon RMSE | 2.09° | **1.56°** |
| relativna napaka `f_px` | 11.0 % | **4.0 %** |
| prvi kandidat je iz vrhnje plasti | 80 % | 80 % |

Metrike poze so računane le na scenah z veljavnim okvirom; detekcija se meri v
sliki in je zato neodvisna od kalibracije.

### Ugotovitve, ki so oblikovale zasnovo

**K1 — `f_px` pri navpični kameri ni opazljiv.** Če ravnina dna leži
fronto-paralelno, je napačen `f` natanko enakovreden podobnostni preslikavi
scene: dno, prirobnice na njem in vsa razmerja ostanejo skladni. Izmerjeno:
pri kameri z 0° nagiba je cenilka skladnosti po `f` popolnoma ravna (0.000° za
vse `f` med 800 in 2000). Šele nagib kamere naredi problem rešljiv — pri 5°
nagiba je razlika 0.24° za 8 % napake v `f`.
Praktična posledica: za absolutno višino podaj `camera.working_distance_mm`
(zniža napako `f` z 11 % na 5 %) ali nagni kamero za nekaj stopinj.

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
- [x] 34 testov (geometrija, cevovod, robni primeri) — vsi zeleni.

### Odprto vprašanje za naročnika

Pri `D_out = 40 mm` in `D_in = 16 mm` je kolobar širok **12 mm**, sesalna
čašica pa ima **15 mm**. Čašica torej ne more nalegati v celoti — vedno bo
segala čez luknjo ali čez zunanji rob. Sistem to javi kot opozorilo in
poroča `cup_fit_ratio` (0.8), kandidatov pa ne zavrne, razen če se vklopi
`gripper.require_full_cup_clearance`. Možnosti: manjša čašica (≤ 12 mm),
čašica z zaporo čez luknjo, ali potrditev, da delno naleganje zadošča.
