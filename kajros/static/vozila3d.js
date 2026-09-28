"use strict";

// Vozila v 3D. Avtobusi na velikem zemljevidu in v oknu voznje: vsak
// prevoznik svoj model in svoje barve, kot jih ima na cesti. Vlaki samo na
// velikem zemljevidu, po vrsti vlaka (glej "vlaki" spodaj). Rise jih
// MapLibrova plast po meri (`type: "custom"`) z golim WebGL2: three.js je
// 172 kB stisnjen (MapLibre 299 kB) in za nekaj skatel ni vreden nove
// odvisnosti; WebGL2 pa MapLibre 6 tako ali tako zahteva.
//
// Model je zlozen iz kvadrov in osmerokotnih koles v metrih: x naprej, y
// levo, z gor, izhodisce na sredini vozila na tleh. Vsa vozila istega
// modela gredo v en klic risanja (instanciranje); na vozilo je le lega,
// smer in merilo.
//
// Barve prevoznikov so z njihovih strani (logotipi in slogi, 22. 9. 2026):
// LPP zelena #8dc63f, Arriva turkizna #33cad6 z vijolicno #2d146e, Nomago
// modra #004899 z rumeno #fbb900, AP Murska Sobota #00a7e7 in #0077be.
// Tip vozila: LPP ima 148 zgibnih od 224 avtobusov (sl.wikipedia), zato je
// njegov model zgibni mestni; ostali trije vozijo predvsem medkrajevne
// linije z visokopodnimi vozili (Arriva je kupila 45 in nato 22
// Mercedes-Benz Intouro, arriva.si).
//
// Streha nosi barvo prevoznika z legende (`AGENCY_INK` v dashboard.js):
// od zgoraj je streha edino, kar se vidi, in brez tega bi bili Nomagov in
// AP-jev avtobus od zgoraj ista bela skatla.

// Od blizu je avtobus model, od dalec ikona. Meja je tam, kjer se kamera ze
// vidno nagne (24° pri Leafletovem z16); od zgoraj bi bil model bela skatla,
// ikona pa pove smer in prevoznika na prvi pogled. Ista na obeh zemljevidih.
const AVTO_3D_OD = 15;         // MapLibrov zoom

// Model je vecji od resnicnega, sicer bi bil pri z16 dolg sedem pik: tako
// velik kot ikona, ko se prikaze (~36 px), in blizje resnici, ko se
// priblizas (pri z19 1,7-krat).
const avtoPovecava = (z) => 3.5 * 2 ** (-(z - 16) * 0.5);

// Resnicna dolzina modela v metrih (glej `avtoModeli`): LPP zgibni, ostali 12 m.
const avtoDolzina = (model) => (model === "1118" ? 18 : 12);

const AVTO_BELA = "#eef1f3";
const AVTO_STEKLO = "#1c2530";
const AVTO_GUMA = "#17191c";
const AVTO_PLATISCE = "#8e979f";
const AVTO_NOTRANJOST = "#101318";
const AVTO_LED = "#ffae1a";
const AVTO_LUC = "#fff4d6";
const AVTO_ZADAJ = "#c9302c";
const AVTO_HARMONIKA = "#2a2e35";

function avtoRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
}

// Kvader med danimi mejami; vsaka ploskev svoja normala (ostri robovi).
function avtoKvader(v, x0, x1, y0, y1, z0, z1, hex) {
  const b = avtoRgb(hex);
  const ploskev = (n, a, b2, c, d) => {
    for (const p of [a, b2, c, a, c, d]) v.push(p[0], p[1], p[2], n[0], n[1], n[2], b[0], b[1], b[2]);
  };
  const P = (x, y, z) => [x, y, z];
  ploskev([1, 0, 0], P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1));
  ploskev([-1, 0, 0], P(x0, y1, z0), P(x0, y0, z0), P(x0, y0, z1), P(x0, y1, z1));
  ploskev([0, 1, 0], P(x1, y1, z0), P(x0, y1, z0), P(x0, y1, z1), P(x1, y1, z1));
  ploskev([0, -1, 0], P(x0, y0, z0), P(x1, y0, z0), P(x1, y0, z1), P(x0, y0, z1));
  ploskev([0, 0, 1], P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1));
  ploskev([0, 0, -1], P(x0, y1, z0), P(x1, y1, z0), P(x1, y0, z0), P(x0, y0, z0));
}

// Kolo: osmerokotna prizma okrog osi y, s platiscem na zunanji strani.
function avtoKolo(v, x, yNotri, yZunaj, r) {
  const g = avtoRgb(AVTO_GUMA);
  const n = 8;
  const tocka = (i, y) => {
    const a = (i / n) * 2 * Math.PI;
    return [x + r * Math.cos(a), y, r + r * Math.sin(a)];
  };
  const tri = (p, nn, b) => { for (const q of p) v.push(q[0], q[1], q[2], nn[0], nn[1], nn[2], b[0], b[1], b[2]); };
  for (let i = 0; i < n; i += 1) {
    const a = ((i + 0.5) / n) * 2 * Math.PI;
    const nn = [Math.cos(a), 0, Math.sin(a)];
    const p0 = tocka(i, yNotri), p1 = tocka(i + 1, yNotri);
    const q0 = tocka(i, yZunaj), q1 = tocka(i + 1, yZunaj);
    tri([p0, p1, q1], nn, g);
    tri([p0, q1, q0], nn, g);
  }
  const zunaj = Math.sign(yZunaj - yNotri);
  const sredina = [x, yZunaj, r];
  for (let i = 0; i < n; i += 1) tri([sredina, tocka(i, yZunaj), tocka(i + 1, yZunaj)], [0, zunaj, 0], g);
  const pl = r * 0.55;
  avtoKvader(v, x - pl, x + pl, Math.min(yZunaj, yZunaj + zunaj * 0.015),
             Math.max(yZunaj, yZunaj + zunaj * 0.015), r - pl, r + pl, AVTO_PLATISCE);
}

/**
 * Odsek karoserije od `x0` (zadaj) do `x1` (spredaj).
 *
 * `pasovi` so [z0, z1, barva] od tal do stekla; pasovi pod `LOK` se pri
 * oseh prekinejo, da se vidi kolo. `o` nosi obliko: sirino, visino stekla,
 * strehe, osi in vrata na desni (-y) strani.
 */
const AVTO_LOK = 1.0;

function avtoOdsek(v, x0, x1, o) {
  const W = o.sirina / 2;
  const loki = o.osi.filter((x) => x > x0 && x < x1).map((x) => [x - 0.68, x + 0.68]);
  // Temna notranjost pod podom: skozi lok se vidi kolo in tema, ne luknja.
  avtoKvader(v, x0 + 0.15, x1 - 0.15, -W + 0.32, W - 0.32, 0.3, AVTO_LOK, AVTO_NOTRANJOST);
  for (const [z0, z1, hex] of o.pasovi) {
    let od = x0;
    const kosi = [];
    if (z1 <= AVTO_LOK + 1e-6) {
      for (const [a, b] of loki) { kosi.push([od, a]); od = b; }
    }
    kosi.push([od, x1]);
    for (const [a, b] of kosi) if (b > a) avtoKvader(v, a, b, -W, W, z0, z1, hex);
  }
  avtoKvader(v, x0, x1, -W, W, o.steklo[0], o.steklo[1], AVTO_STEKLO);
  avtoKvader(v, x0, x1, -W, W, o.steklo[1], o.visina, AVTO_BELA);
  // Stebricki med okni: steklo ni en trak, ampak okna.
  const d = o.razmik;
  for (let x = x1 - 0.9; x > x0 + 0.3; x -= d) {
    for (const s of [-1, 1]) {
      avtoKvader(v, x - 0.06, x + 0.06, s > 0 ? W : -W - 0.012, s > 0 ? W + 0.012 : -W,
                 o.steklo[0], o.steklo[1], AVTO_BELA);
    }
  }
  for (const [xs, sirina] of o.vrata.filter(([xs]) => xs > x0 && xs < x1)) {
    avtoKvader(v, xs - sirina / 2, xs + sirina / 2, -W - 0.02, -W + 0.03,
               0.33, o.steklo[1] - 0.06, AVTO_STEKLO);
  }
  for (const x of o.osi.filter((a) => a > x0 && a < x1)) {
    for (const s of [-1, 1]) avtoKolo(v, x, s * (W - 0.34), s * (W - 0.03), 0.5);
  }
}

function avtoCelo(v, x1, o) {
  const W = o.sirina / 2;
  // Vetrobransko steklo sega nize od stranskih oken.
  avtoKvader(v, x1 - 0.02, x1 + 0.015, -W + 0.1, W - 0.1, o.celo, o.steklo[0], AVTO_STEKLO);
  avtoKvader(v, x1, x1 + 0.03, -W + 0.35, W - 0.35, o.steklo[1] - 0.3, o.steklo[1] - 0.06, AVTO_LED);
  for (const s of [-1, 1]) {
    avtoKvader(v, x1, x1 + 0.03, s > 0 ? W - 0.42 : -W + 0.1, s > 0 ? W - 0.1 : -W + 0.42,
               0.55, 0.72, AVTO_LUC);
  }
}

function avtoRep(v, x0, o) {
  const W = o.sirina / 2;
  // Zadaj je motor: steklo samo zgoraj.
  avtoKvader(v, x0 - 0.03, x0 + 0.02, -W, W, o.pasovi[0][0], o.steklo[0] + 0.7, AVTO_BELA);
  for (const s of [-1, 1]) {
    avtoKvader(v, x0 - 0.05, x0, s > 0 ? W - 0.3 : -W + 0.05, s > 0 ? W - 0.05 : -W + 0.3,
               0.6, 1.3, AVTO_ZADAJ);
  }
}

function avtoStreha(v, x0, x1, o, sirina, visina, hex) {
  avtoKvader(v, x0, x1, -sirina / 2, sirina / 2, o.visina, o.visina + visina, hex);
}

// Zgibni mestni avtobus, 18 m (MAN Lion's City G, ki ga ima LPP najvec).
function avtoZgibni(barve) {
  const v = [];
  const o = {
    sirina: 2.55, visina: 2.95, steklo: [1.0, 2.58], celo: 0.95, razmik: 1.45,
    osi: [6.3, 0.5, -6.6],
    vrata: [[8.1, 1.2], [2.8, 1.2], [-4.4, 1.2]],
    pasovi: barve.pasovi,
  };
  avtoOdsek(v, -2.6, 9.0, o);
  avtoOdsek(v, -9.0, -3.2, o);
  // Harmonika: ozja in temnejsa, da se vidi, da sta to dva dela.
  avtoKvader(v, -3.25, -2.55, -1.15, 1.15, 0.4, 2.85, AVTO_HARMONIKA);
  avtoCelo(v, 9.0, o);
  avtoRep(v, -9.0, o);
  // Plinske jeklenke na strehi sprednjega dela, klima na zadnjem.
  avtoStreha(v, -1.8, 6.2, o, 1.9, 0.32, barve.streha);
  avtoStreha(v, -8.0, -4.6, o, 1.6, 0.26, barve.streha);
  return v;
}

// Medkrajevni avtobus, 12 m, visok pod (Mercedes-Benz Intouro ipd.).
function avtoMedkrajevni(barve, visina = 3.25) {
  const v = [];
  const o = {
    sirina: 2.55, visina, steklo: [1.35, visina - 0.35], celo: 1.05, razmik: 1.6,
    osi: [3.7, -2.5],
    vrata: barve.srednjaVrata ? [[4.9, 1.0], [-0.6, 1.0]] : [[4.9, 1.0]],
    pasovi: barve.pasovi,
  };
  avtoOdsek(v, -6.0, 6.0, o);
  avtoCelo(v, 6.0, o);
  avtoRep(v, -6.0, o);
  avtoStreha(v, -1.6, 1.6, o, 1.8, 0.3, barve.streha);
  return v;
}

// Kljuc je skupina iz `busGroup()` v dashboard.js.
//
// `enotna` pobarva vse, kar je sicer barva prevoznika (pasove in streho), z
// eno barvo -- okno voznje tako rise OCENO lege: barva prevoznika je na
// velikem zemljevidu barva meritve, oblika modela pa ostane prevoznikova.
function avtoModeli(inki, enotna = null) {
  const B = AVTO_BELA;
  const streha = (k) => enotna || inki[k];
  const pasovi = (p) => (enotna ? p.map(([a, b, hex]) => [a, b, hex === B ? B : enotna]) : p);
  return {
    "1118": avtoZgibni({ streha: streha("1118"),
      pasovi: pasovi([[0.3, 0.62, "#8dc63f"], [0.62, 0.7, "#3c8c3c"], [0.7, 1.0, B]]) }),
    "1123": avtoMedkrajevni({ streha: streha("1123"), srednjaVrata: true,
      pasovi: pasovi([[0.35, 0.72, "#33cad6"], [0.72, 0.8, "#2d146e"], [0.8, 1.0, B], [1.0, 1.35, B]]) }),
    "1119": avtoMedkrajevni({ streha: streha("1119"),
      pasovi: pasovi([[0.35, 0.9, "#004899"], [0.9, 1.0, "#fbb900"], [1.0, 1.45, B]]) }, 3.45),
    "1121": avtoMedkrajevni({ streha: streha("1121"), srednjaVrata: true,
      pasovi: pasovi([[0.35, 0.8, "#00a7e7"], [0.8, 0.9, "#0077be"], [0.9, 1.0, B], [1.0, 1.3, B]]) }, 3.2),
    drugi: avtoMedkrajevni({ streha: streha("drugi"),
      pasovi: pasovi([[0.35, 0.8, "#8a939e"], [0.8, 1.0, B], [1.0, 1.35, B]]) }),
  };
}

// ---------- vlaki ----------
//
// Vrsta vlaka (predpona stevilke) garniture ne pove, sestave pa SZ ne
// objavijo nikjer, kjer bi jo lahko brali (28. 9. 2026: ni je v GTFS, ne na
// zemljevidu ne na tabli SZ; `train_details` posrednika vraca 500). Model je
// zato podoba, ki je za vrsto najbolj verjetna, ne trditev o tem vlaku:
// regionalni = Stadler FLIRT (SZ 510/610), ICS = dvonadstropni KISS (313),
// IC, EC, EN in avtovlak = lokomotiva Taurus (541) z vagoni. Razmerja in
// barve s fotografij na Wikimedia Commons (510 012, 510-037, 610-003,
// 313-017, 541-015, EC 211 Sava), na oko.
//
// Po sredini strehe je oranzen pas z legende, iz istega razloga kot pri
// avtobusih: od zgoraj se vidi samo streha, siva streha vlaka pa bi bila od
// strehe avtobusa nelocljiva.

const VLAK_MODRA = "#1f9ad6";      // SZ modra na Stadlerjevih garniturah
const VLAK_TEMNA = "#262a31";      // podvozje, spojke, prehodi med vozovi
const VLAK_RDECA = "#c7282d";      // Taurus 541
const VLAK_SREBRNA = "#c4c9ce";    // vagoni
const VLAK_OPREMA = "#5b626b";     // naprave na strehi
const VLAK_STREHA = "#8d949b";

// Model je vecji od resnicnega, a manj kot avtobus: garnitura je dolga
// 60-100 m, z avtobusno povecavo (3,5-krat pri z16) bi prekrila pol postaje.
// Pri MapLibrovem z15 je FLIRT dolg ~90 pik, od z18 naprej je resnicne
// velikosti.
const vlakPovecava = (z) => Math.max(1, 2.4 * 2 ** (-(z - 15) * 0.5));

// Razmik med vlakoma, ki stojita na isti postaji: tirna razdalja v metrih.
const VLAK_TIR_M = 4.6;

// Model po vrsti vlaka; glej opombo zgoraj, zakaj ne po garnituri.
function vlakModel(t) {
  if (t.mode === "bus") return "bus";
  const vrsta = String(t.train_no || "").split(" ")[0];
  if (vrsta === "ICS") return "kiss";
  if (["IC", "EC", "EN", "AVT"].includes(vrsta)) return "lok";
  return "flirt";
}

// Kolesna dvojica ali dve na podstavnem vozicku, `x` je sredina vozicka.
function vlakVozicek(v, x, W) {
  avtoKvader(v, x - 1.5, x + 1.5, -W + 0.4, W - 0.4, 0.12, 0.42, VLAK_TEMNA);
  for (const xa of [x - 1.1, x + 1.1]) {
    for (const s of [-1, 1]) avtoKolo(v, xa, s * 0.6, s * 0.8, 0.42);
  }
}

/**
 * Voz od `x0` do `x1`. `o.pasovi` so [z0, z1, barva] od tal do strehe brez
 * lukenj (kot pri avtobusu: prekrivajoci se kvadri bi na ploskvah
 * trepetali); pas z barvo `AVTO_STEKLO` dobi stebricke med okni.
 */
function vlakVoz(v, x0, x1, o, streha) {
  const W = o.sirina / 2;
  avtoKvader(v, x0 + 0.2, x1 - 0.2, -W + 0.3, W - 0.3, 0.3, o.pasovi[0][0], AVTO_NOTRANJOST);
  for (const [z0, z1, hex] of o.pasovi) {
    avtoKvader(v, x0, x1, -W, W, z0, z1, hex);
    if (hex !== AVTO_STEKLO) continue;
    for (let x = x1 - 1.0; x > x0 + 0.4; x -= o.razmik) {
      for (const s of [-1, 1]) {
        avtoKvader(v, x - 0.07, x + 0.07, s > 0 ? W : -W - 0.012, s > 0 ? W + 0.012 : -W,
                   z0, z1, o.okvir || AVTO_BELA);
      }
    }
  }
  // Vrata na obeh straneh: vlak ima peron lahko levo ali desno.
  for (const xs of o.vrata(x0, x1)) {
    for (const s of [-1, 1]) {
      avtoKvader(v, xs - 0.65, xs + 0.65, s > 0 ? W : -W - 0.02, s > 0 ? W + 0.02 : -W,
                 o.pasovi[0][0] + 0.1, o.visinaVrat, o.barvaVrat);
    }
  }
  // Streha je siva kot v resnici, barva z legende je pas po sredini: cela
  // oranzna streha je od blizu prevladala nad vozom samim.
  const vrh = o.pasovi[o.pasovi.length - 1][1];
  avtoKvader(v, x0 + 0.15, x1 - 0.15, -W + 0.15, W - 0.15, vrh, vrh + 0.1, VLAK_STREHA);
  avtoKvader(v, x0 + 0.6, x1 - 0.6, -0.75, 0.75, vrh + 0.1, vrh + 0.18, streha);
  for (const xb of o.vozicki(x0, x1)) vlakVozicek(v, xb, W);
}

// Prehod med vozovoma: ozji in temen, da se vidi, kje se voz konca.
function vlakPrehod(v, x0, x1, visina) {
  avtoKvader(v, x0, x1, -1.1, 1.1, 0.45, visina - 0.25, VLAK_TEMNA);
}

// Celo: stopnicast nos namesto zaobljenega -- od blizu se vidi nagnjeno
// steklo, od dalec je vlak se vedno vlak. `s` = +1 spredaj, -1 zadaj.
function vlakNos(v, x, s, n) {
  const X = (a, b) => (s > 0 ? [x + a, x + b] : [x - b, x - a]);
  const W = n.sirina / 2;
  const sred = n.dolzina * 0.62, vrh = n.dolzina * 0.28;
  avtoKvader(v, ...X(0, n.dolzina), -W + 0.15, W - 0.15, 0.35, n.pas, n.spodaj);
  avtoKvader(v, ...X(0, sred), -W + 0.05, W - 0.05, n.pas, n.steklo, n.zgoraj);
  avtoKvader(v, ...X(0, vrh), -W + 0.1, W - 0.1, n.steklo, n.visina, n.zgoraj);
  // Vetrobransko steklo na obeh stopnicah, luci in spojka spodaj.
  avtoKvader(v, ...X(sred - 0.01, sred + 0.02), -W + 0.3, W - 0.3, n.pas + 0.2, n.steklo, AVTO_STEKLO);
  avtoKvader(v, ...X(vrh - 0.01, vrh + 0.02), -W + 0.35, W - 0.35, n.steklo, n.steklo + 0.5, AVTO_STEKLO);
  for (const y of [-W + 0.4, W - 0.7]) {
    avtoKvader(v, ...X(n.dolzina - 0.01, n.dolzina + 0.02), y, y + 0.3, n.pas - 0.32, n.pas - 0.14, AVTO_LUC);
  }
  avtoKvader(v, ...X(n.dolzina, n.dolzina + 0.35), -0.35, 0.35, 0.6, 0.95, VLAK_TEMNA);
}

// Garnitura iz zaporedja vozov, od cela (+x) proti repu; sredina modela je
// sredina garniture, da vlak stoji SREDI postaje, ne s celom na njej.
function vlakGarnitura(dolzine, prehod, zgradi) {
  const skupaj = dolzine.reduce((a, b) => a + b, 0) + prehod * (dolzine.length - 1);
  let x1 = skupaj / 2;
  dolzine.forEach((d, i) => {
    zgradi(i, x1 - d, x1);
    x1 -= d + prehod;
  });
}

// Stadler FLIRT (SZ 510 in 610): nizkopodna garnitura, tri vozovi,
// Jakobsovi vozicki na stikih.
function vlakFlirt(streha) {
  const v = [];
  const o = {
    sirina: 2.88, razmik: 1.45,
    pasovi: [[0.3, 0.55, VLAK_TEMNA], [0.55, 0.9, AVTO_BELA], [0.9, 1.1, VLAK_MODRA],
             [1.1, 2.25, AVTO_STEKLO], [2.25, 3.75, AVTO_BELA]],
    vrata: (x0, x1) => [x0 + 4.5, x1 - 4.5],
    visinaVrat: 2.3, barvaVrat: VLAK_MODRA,
    vozicki: () => [],
  };
  const nos = { dolzina: 1.7, sirina: 2.88, pas: 1.35, steklo: 2.9, visina: 3.75,
                spodaj: AVTO_BELA, zgoraj: VLAK_MODRA };
  const dolzine = [19.5, 18.6, 19.5];
  const stiki = [];
  vlakGarnitura(dolzine, 0.6, (i, x0, x1) => {
    vlakVoz(v, x0, x1, o, streha);
    if (i === 0) vlakNos(v, x1, 1, nos);
    if (i === dolzine.length - 1) vlakNos(v, x0, -1, nos);
    else { vlakPrehod(v, x0 - 0.6, x0, 3.75); stiki.push(x0 - 0.3); }
    if (i === 0) vlakVozicek(v, x1 - 2.6, o.sirina / 2);
    if (i === dolzine.length - 1) vlakVozicek(v, x0 + 2.6, o.sirina / 2);
  });
  for (const x of stiki) vlakVozicek(v, x, o.sirina / 2);
  // Klima in pretvornik na strehi.
  for (const x of [-18, 0, 18]) avtoKvader(v, x - 2.2, x + 2.2, -0.9, 0.9, 3.89, 4.2, VLAK_OPREMA);
  return v;
}

// Stadler KISS (SZ 313): dvonadstropna garnitura, tri vozovi.
function vlakKiss(streha) {
  const v = [];
  const o = {
    sirina: 2.8, razmik: 1.6,
    pasovi: [[0.3, 0.5, VLAK_TEMNA], [0.5, 0.75, AVTO_BELA], [0.75, 1.75, AVTO_STEKLO],
             [1.75, 1.95, AVTO_BELA], [1.95, 2.3, VLAK_MODRA], [2.3, 2.45, AVTO_BELA],
             [2.45, 3.55, AVTO_STEKLO], [3.55, 4.3, AVTO_BELA]],
    vrata: (x0, x1) => [x0 + 6.5, x1 - 6.5],
    visinaVrat: 2.2, barvaVrat: VLAK_MODRA,
    vozicki: (x0, x1) => [x0 + 2.4, x1 - 2.4],
  };
  const nos = { dolzina: 2.0, sirina: 2.8, pas: 1.45, steklo: 3.55, visina: 4.3,
                spodaj: AVTO_BELA, zgoraj: VLAK_MODRA };
  const dolzine = [26.5, 25, 26.5];
  vlakGarnitura(dolzine, 0.7, (i, x0, x1) => {
    vlakVoz(v, x0, x1, o, streha);
    if (i === 0) vlakNos(v, x1, 1, nos);
    if (i === dolzine.length - 1) vlakNos(v, x0, -1, nos);
    else vlakPrehod(v, x0 - 0.7, x0, 4.3);
  });
  return v;
}

// Lokomotiva Taurus (SZ 541) in trije vagoni.
function vlakLokomotiva(streha) {
  const v = [];
  const lok = {
    sirina: 3.0, razmik: 100,
    pasovi: [[0.45, 1.15, VLAK_TEMNA], [1.15, 2.05, VLAK_RDECA], [2.05, 2.2, AVTO_BELA],
             [2.2, 3.75, VLAK_RDECA]],
    vrata: () => [], visinaVrat: 0, barvaVrat: VLAK_TEMNA,
    vozicki: (x0, x1) => [x0 + 3.2, x1 - 3.2],
  };
  const vagon = {
    sirina: 2.83, razmik: 1.9, okvir: VLAK_SREBRNA,
    pasovi: [[0.45, 1.0, VLAK_TEMNA], [1.0, 1.25, VLAK_SREBRNA], [1.25, 1.45, VLAK_MODRA],
             [1.45, 1.6, VLAK_SREBRNA], [1.6, 2.45, AVTO_STEKLO], [2.45, 3.7, VLAK_SREBRNA]],
    vrata: (x0, x1) => [x0 + 1.4, x1 - 1.4],
    visinaVrat: 2.45, barvaVrat: "#8e969e",
    vozicki: (x0, x1) => [x0 + 3.6, x1 - 3.6],
  };
  const nos = { dolzina: 1.0, sirina: 3.0, pas: 2.05, steklo: 3.3, visina: 3.75,
                spodaj: VLAK_RDECA, zgoraj: VLAK_RDECA };
  const dolzine = [17.3, 26.4, 26.4, 26.4];
  vlakGarnitura(dolzine, 0.8, (i, x0, x1) => {
    if (i === 0) {
      vlakVoz(v, x0, x1, lok, streha);
      vlakNos(v, x1, 1, nos);
      vlakNos(v, x0, -1, nos);
      // Okna kabine na obeh koncih in odjemnika toka.
      for (const [a, b] of [[x1 - 1.6, x1 - 0.4], [x0 + 0.4, x0 + 1.6]]) {
        for (const s of [-1, 1]) {
          avtoKvader(v, a, b, s > 0 ? 1.5 : -1.52, s > 0 ? 1.52 : -1.5, 2.4, 3.2, AVTO_STEKLO);
        }
      }
      for (const x of [x0 + 4, x1 - 4]) avtoKvader(v, x - 1.2, x + 1.2, -0.7, 0.7, 3.89, 4.35, VLAK_TEMNA);
    } else {
      vlakPrehod(v, x1, x1 + 0.8, 3.7);
      vlakVoz(v, x0, x1, vagon, streha);
    }
  });
  return v;
}

function vlakModeli(streha) {
  return {
    flirt: vlakFlirt(streha),
    kiss: vlakKiss(streha),
    lok: vlakLokomotiva(streha),
    // Nadomestni prevoz SZ: avtobus, a z oranzno streho -- sodi med vlake.
    bus: avtoMedkrajevni({ streha,
      pasovi: [[0.35, 0.8, "#8a939e"], [0.8, 1.0, AVTO_BELA], [1.0, 1.35, AVTO_BELA]] }),
  };
}

// ---------- plast ----------

const AVTO_VS = `#version 300 es
layout(location = 0) in vec3 a_pos;
layout(location = 1) in vec3 a_norm;
layout(location = 2) in vec3 a_barva;
layout(location = 3) in vec4 a_vozilo;
layout(location = 4) in float a_odmik;
uniform mat4 u_matrix;
uniform float u_povecava;
uniform vec3 u_luc;
out vec3 v_barva;
void main() {
  float s = sin(a_vozilo.z), c = cos(a_vozilo.z);
  vec2 p = vec2(a_pos.x, a_pos.y + a_odmik);
  vec2 v = vec2(p.x * s - p.y * c, p.x * c + p.y * s);
  float k = a_vozilo.w * u_povecava;
  gl_Position = u_matrix * vec4(a_vozilo.x + v.x * k, a_vozilo.y - v.y * k, a_pos.z * k, 1.0);
  vec3 n = vec3(a_norm.x * s - a_norm.y * c, a_norm.x * c + a_norm.y * s, a_norm.z);
  v_barva = min(a_barva * (0.62 + 0.45 * max(dot(n, u_luc), 0.0)), vec3(1.0));
}`;

const AVTO_FS = `#version 300 es
precision mediump float;
in vec3 v_barva;
out vec4 barva;
void main() { barva = vec4(v_barva, 1.0); }`;

/**
 * Plast avtobusov: `inki` so barve streh po prevozniku, `enotna` ena barva
 * namesto barv prevoznikov (glej `avtoModeli`).
 */
function avtobusi3D({ id, inki = {}, enotna = null, vidna, povecava }) {
  return plast3D({ id, modeli: avtoModeli(inki, enotna), vidna, povecava });
}

/**
 * Plast in njen vnos. `modeli` so {kljuc: oglisca}; `vidna()` pove, ali naj
 * plast ta hip rise (zoom, stikalo); `povecava(z)` koliko je vozilo vecje od
 * resnicnega.
 *
 * Vrne `{ plast, nastavi(vozila) }`; vozilo je `{lon, lat, smer, model,
 * odmik}`, smer v stopinjah od severa, `odmik` v metrih levo od lege (vlaka
 * na isti postaji stojita drug ob drugem). Odmik se poveca skupaj z
 * modelom, zato se vozili pri nobenem priblizku ne prekrijeta.
 */
function plast3D({ id, modeli, vidna, povecava }) {
  const kljuci = Object.keys(modeli);
  // Izhodisce v Slovenji: odmiki od njega so majhni in float32 jih nosi na
  // centimeter. Absolutna lega v Mercatorju bi pri z18 trepetala za metre.
  const IZ_X = (14.8 + 180) / 360;
  const IZ_Y = (180 - (180 / Math.PI) * Math.log(Math.tan(Math.PI / 4 + (46.1 * Math.PI) / 360))) / 360;
  const luc = [-0.3, -0.55, 0.78];
  const dl = Math.hypot(...luc);
  const LUC = luc.map((x) => x / dl);

  let map = null;
  let prog = null;
  let uMatrix = null, uPovecava = null, uLuc = null;
  const risbe = {};              // model -> {vao, vozila, n, stevilo, podatki, sveze}

  const plast = {
    id, type: "custom", renderingMode: "3d",
    onAdd(m, gl) {
      map = m;
      const sencilnik = (vrsta, koda) => {
        const s = gl.createShader(vrsta);
        gl.shaderSource(s, koda);
        gl.compileShader(s);
        if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
        return s;
      };
      prog = gl.createProgram();
      gl.attachShader(prog, sencilnik(gl.VERTEX_SHADER, AVTO_VS));
      gl.attachShader(prog, sencilnik(gl.FRAGMENT_SHADER, AVTO_FS));
      gl.linkProgram(prog);
      if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
      uMatrix = gl.getUniformLocation(prog, "u_matrix");
      uPovecava = gl.getUniformLocation(prog, "u_povecava");
      uLuc = gl.getUniformLocation(prog, "u_luc");
      for (const k of kljuci) {
        const vao = gl.createVertexArray();
        gl.bindVertexArray(vao);
        const oglisca = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, oglisca);
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(modeli[k]), gl.STATIC_DRAW);
        for (let i = 0; i < 3; i += 1) {
          gl.enableVertexAttribArray(i);
          gl.vertexAttribPointer(i, 3, gl.FLOAT, false, 36, i * 12);
        }
        const vozila = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, vozila);
        gl.enableVertexAttribArray(3);
        gl.vertexAttribPointer(3, 4, gl.FLOAT, false, 20, 0);
        gl.vertexAttribDivisor(3, 1);
        gl.enableVertexAttribArray(4);
        gl.vertexAttribPointer(4, 1, gl.FLOAT, false, 20, 16);
        gl.vertexAttribDivisor(4, 1);
        gl.bindVertexArray(null);
        const r = risbe[k] || (risbe[k] = { podatki: new Float32Array(0), stevilo: 0, sveze: true });
        Object.assign(r, { vao, vozila, n: modeli[k].length / 9, sveze: true });
      }
    },
    render(gl, args) {
      if (!prog || !vidna()) return;
      const M = args.defaultProjectionData.mainMatrix;
      const m = new Float32Array(16);
      for (let i = 0; i < 12; i += 1) m[i] = M[i];
      for (let r = 0; r < 4; r += 1) m[12 + r] = M[r] * IZ_X + M[4 + r] * IZ_Y + M[12 + r];
      gl.useProgram(prog);
      gl.uniformMatrix4fv(uMatrix, false, m);
      gl.uniform1f(uPovecava, povecava(map.getZoom()));
      gl.uniform3fv(uLuc, LUC);
      for (const k of kljuci) {
        const r = risbe[k];
        if (!r || !r.vao || !r.stevilo) continue;
        gl.bindVertexArray(r.vao);
        if (r.sveze) {
          gl.bindBuffer(gl.ARRAY_BUFFER, r.vozila);
          gl.bufferData(gl.ARRAY_BUFFER, r.podatki, gl.DYNAMIC_DRAW);
          r.sveze = false;
        }
        gl.drawArraysInstanced(gl.TRIANGLES, 0, r.n, r.stevilo);
      }
      gl.bindVertexArray(null);
    },
    onRemove(m, gl) {
      for (const r of Object.values(risbe)) {
        if (r.vao) gl.deleteVertexArray(r.vao);
        r.vao = null;
      }
      if (prog) gl.deleteProgram(prog);
      prog = null;
    },
  };

  function nastavi(vozila) {
    const po = {};
    for (const k of kljuci) po[k] = [];
    for (const a of vozila) {
      const x = (a.lon + 180) / 360;
      const lat = (a.lat * Math.PI) / 180;
      const y = (180 - (180 / Math.PI) * Math.log(Math.tan(Math.PI / 4 + lat / 2))) / 360;
      // Mercatorjeva enota na meter na tej sirini.
      const enota = 1 / (40075016.686 * Math.cos(lat));
      (po[a.model] || po.drugi || po[kljuci[0]])
        .push(x - IZ_X, y - IZ_Y, (a.smer * Math.PI) / 180, enota, a.odmik || 0);
    }
    for (const k of kljuci) {
      const r = risbe[k] || (risbe[k] = {});
      r.podatki = new Float32Array(po[k]);
      r.stevilo = po[k].length / 5;
      r.sveze = true;
    }
    if (map) map.triggerRepaint();
  }

  return { plast, nastavi };
}
