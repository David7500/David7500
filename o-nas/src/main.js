// O nas v 3D: ena kamera, en svet, ena zgodba. Drsenje premika čas filma
// T; vse na zaslonu je funkcija T, zato se da drseti naprej in nazaj.
import * as THREE from 'three';
import { clamp, lerp, smooth, smoother, okno, zlepek } from './orodja.js';
import { Atmosfera, NEBO_GLSL } from './nebo.js';
import { ustvariProgo, zgradiProgo } from './proga.js';
import { zgradiVlak, KISS } from './vlak.js';
import { zgradiPostajo, zgradiDijaka, URA, TABLA, PERON } from './postaja.js';
import { zgradiTeren, zgradiDrevesa, zgradiNaselja, zgradiCerkev, zgradiKozolec, zgradiSolo, zgradiGore, zgradiMeglo, visina, CERKEV, SOLA } from './pokrajina.js';
import { zgradiKarto } from './karta.js';

const nextFrame = () => new Promise((r) => requestAnimationFrame(() => r()));
const telefon = matchMedia('(pointer: coarse)').matches || innerWidth < 700;
const manjGibanja = matchMedia('(prefers-reduced-motion: reduce)').matches;

// ---------- ura zgodbe (sekunde od polnoči) ----------
const hms = (h, m, s = 0) => h * 3600 + m * 60 + s;
const URA_KLJUCI = [
  [0, hms(7, 41, 24)], [10, hms(7, 41, 59.2)], [11, hms(7, 42, 0)], [14, hms(7, 42, 5)],
  [26, hms(7, 50, 0)], [43, hms(7, 55, 0)], [54, hms(7, 55, 30)], [68, hms(7, 56, 30)],
  [103, hms(8, 0, 0)], [118, hms(8, 13, 0)], [128, hms(8, 14, 0)],
  [206, hms(22, 41, 0)], [240, hms(22, 43, 0)],
];
function casZgodbe(T) {
  const K = URA_KLJUCI;
  if (T <= K[0][0]) return K[0][1];
  for (let i = 0; i < K.length - 1; i++) {
    if (T <= K[i + 1][0]) {
      const t = (T - K[i][0]) / (K[i + 1][0] - K[i][0]);
      if (K[i + 1][1] < K[i][1]) return K[i + 1][1];
      return lerp(K[i][1], K[i + 1][1], t);
    }
  }
  return K[K.length - 1][1];
}
const fmt = (s) => {
  const h = Math.floor(s / 3600) % 24, m = Math.floor(s / 60) % 60;
  return `${String(h).padStart(2, '0')}.${String(m).padStart(2, '0')}`;
};

async function zagon() {
  const platnoEl = document.getElementById('oder');
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas: platnoEl, antialias: true, powerPreference: 'high-performance' });
  } catch (e) {
    document.documentElement.classList.add('brez-3d');
    return;
  }
  const fiksnaDpr = +new URLSearchParams(location.search).get('dpr') || 0;
  const maxDpr = fiksnaDpr || Math.min(devicePixelRatio || 1, telefon ? 1.6 : 2);
  let dpr = fiksnaDpr || Math.min(maxDpr, telefon ? 1.3 : 2);
  renderer.setPixelRatio(dpr);
  renderer.setSize(innerWidth, innerHeight, false);
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.toneMappingExposure = 1.0;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  const napredek = document.querySelector('.nalaganje i');
  // Podatki za Pogl. 3 (~0,9 MB) se nalagajo vzporedno z gradnjo sveta in ne
  // zadržijo prvega kadra; do tja jih bralec ne rabi. Naslove z odtisom
  // vsebine da predloga (`s()` v api.py).
  let karta = null;
  zgradiKarto(platnoEl.dataset)
    .then((k) => { karta = k; })
    .catch((e) => console.warn('kajros: karta se ni naložila', e));
  const korak = async (d) => { if (napredek) napredek.style.width = `${d * 100}%`; await nextFrame(); };

  await Promise.all([
    document.fonts.load('600 92px "IBM Plex Sans"'), document.fonts.load('600 80px "IBM Plex Mono"'),
  ]).catch(() => {});

  // ---------- svet zgodbe ----------
  const svet = new THREE.Scene();
  const atm = new Atmosfera();
  atm.nastavi('zora');
  svet.add(atm.kupola, atm.sonce, atm.sonce.target, atm.nebesna);
  svet.fog = new THREE.Fog('#fff', 1, 2);   // vklopi USE_FOG; barvo in gostoto računa Atmosfera
  atm.sonce.shadow.mapSize.set(telefon ? 1024 : 2048, telefon ? 1024 : 2048);
  await korak(0.1);
  const proga = ustvariProgo();
  const tir = zgradiProgo(proga, { atmU: atm.U, NEBO: NEBO_GLSL });
  svet.add(tir.skupina);
  await korak(0.2);
  const vlak = zgradiVlak();
  svet.add(vlak.skupina);
  await korak(0.3);
  const postaja = zgradiPostajo();
  svet.add(postaja.skupina);
  const dijak = zgradiDijaka();
  svet.add(dijak.skupina);
  await korak(0.4);
  svet.add(zgradiTeren(proga));
  await korak(0.55);
  // brez dreves ob kozolcih in tam, kjer stoji kamera
  const KOZOLCI = [[-2140, -78, 0.15], [-880, -66, -0.1], [-2260, 66, 0.05]];
  const drevesa = zgradiDrevesa(proga, [
    ...KOZOLCI.map(([x, z]) => [x, z, 28]),
    [-1380, 240, 50], [-1425, -60, 45], [-2105, -45, 32], [-2860, 175, 40], [-2990, 160, 40], [-3140, 105, 40], [-3060, 330, 30],
  ], telefon ? 0.7 : 1);
  svet.add(drevesa);
  await korak(0.7);
  const naselja = zgradiNaselja(proga);
  svet.add(naselja, zgradiCerkev(proga));
  for (const [x, z, r] of KOZOLCI) {
    const k = zgradiKozolec();
    k.position.set(x, visina(x, z, proga) - 0.2, z);
    k.rotation.y = r;
    svet.add(k);
  }
  const sola = zgradiSolo(proga);
  svet.add(sola, zgradiGore());
  const megla = zgradiMeglo(atm.U, NEBO_GLSL);
  svet.add(megla);
  // drugi peron in nadstrešek pri šoli
  {
    const p = new THREE.Mesh(new THREE.BoxGeometry(130, 1.4, 5), new THREE.MeshStandardMaterial({ color: '#9a968e', roughness: 0.9 }));
    p.position.set(-3265, PERON.y - 0.7, 1.68 + 2.5);
    p.receiveShadow = true;
    svet.add(p);
  }
  await korak(0.82);
  // žarometi v megli: mehki sij pred lučmi
  const sijMat = new THREE.ShaderMaterial({
    uniforms: { uMoc: { value: 1 } },
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: 'uniform float uMoc; varying vec2 vUv; void main(){ float d = length(vUv - 0.5) * 2.0; float a = exp(-d * d * 5.0) * 0.9 + exp(-d * 18.0) * 0.6; gl_FragColor = vec4(vec3(1.0, 0.95, 0.85) * a * uMoc, 1.0); }',
    transparent: true, blending: THREE.AdditiveBlending, depthWrite: false,
  });
  const siji = [];
  for (const z of [-1.0, 1.0]) {
    const s = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 3.2), sijMat);
    s.renderOrder = 10;
    svet.add(s);
    siji.push({ m: s, z });
  }

  // nočne luči (Pogl. 4): nekaj točkovnih luči ob uri in vlaku; zadnja
  // osvetli dijaka na klopi od zadaj, da v temi ni le silhueta
  const nocneLuci = [];
  for (const [x, y, z, c, i] of [[0, 4.0, 4.6, '#ffd7a0', 26], [-14, 4.0, 4.8, '#ffd7a0', 22], [14, 4.0, 4.8, '#ffd7a0', 22], [-40, 5.6, 7.0, '#ffe2b8', 14], [-17.25, 1.3, 6.55, '#a9c4ff', 1.6], [-18.9, 2.5, 8.9, '#ffd9b0', 2.4]]) {
    const l = new THREE.PointLight(c, 0, 26, 1.6);
    l.position.set(x, y, z);
    svet.add(l);
    nocneLuci.push([l, i]);
  }

  // zračna perspektiva v vse materiale sveta
  svet.traverse((o) => {
    if (!o.material) return;
    for (const m of [].concat(o.material)) atm.popravi(m);
  });
  await korak(0.88);
  const okolja = {};
  atm.nastavi('zora');
  okolja.zora = atm.okolje(renderer);
  atm.nastavi('noc');
  okolja.noc = atm.okolje(renderer);
  atm.nastavi('zora');
  svet.environment = okolja.zora;


  // ---------- kamera ----------
  const kamera = new THREE.PerspectiveCamera(40, innerWidth / innerHeight, 0.05, 60000);

  // Lega vlaka vzdolž proge (s konice) po T.
  const S_POSTAJA = proga.sPriX(-40);
  const S_SOLA = proga.sPriX(-3268);
  function sVlaka(T) {
    if (T < 206) {
      if (T < 28) return S_POSTAJA - 740 - (28 - T) * 98;
      if (T < 43) { const u = (T - 28) / 15; return S_POSTAJA - 740 * (1 - u) * (1 - u); }
      if (T < 68) return S_POSTAJA;
      if (T < 118) return S_POSTAJA + (S_SOLA - S_POSTAJA) * smoother(0, 1, (T - 68) / 50);
      return S_SOLA;
    }
    return S_POSTAJA;
  }
  const nos = new THREE.Vector3(), smerV = new THREE.Vector3(), desno = new THREE.Vector3();
  const UP = new THREE.Vector3(0, 1, 0);
  // ključ v svetu: [x,y,z]; ključ ob vlaku: {v:[naprej, gor, desno]} glede na konico
  const vSvet = (k, T, out) => {
    if (!k.v) return out.set(k[0], k[1], k[2]);
    const s = sVlaka(T);
    proga.tocka(s, nos); proga.smer(s, smerV);
    desno.crossVectors(smerV, UP).normalize();
    return out.copy(nos).addScaledVector(smerV, k.v[0]).addScaledVector(UP, k.v[1]).addScaledVector(desno, k.v[2]);
  };
  const KAMERA = [
    { t: 0, p: [-2.75, 3.12, 2.18], c: [0, 3.3, 3.05], f: 34 },
    { t: 5, p: [-3.3, 3.0, 1.95], c: [0, 3.26, 3.1], f: 35 },
    { t: 13, p: [-7.2, 2.35, 1.3], c: [2.0, 3.25, 3.7], f: 40 },
    { t: 20, p: [-30, 2.3, 5.4], c: [10, 2.9, 2.8], f: 40 },
    { t: 26, p: [-52, 2.25, 6.2], c: [20, 2.6, 1.0], f: 38 },
    { t: 37, p: [-52, 2.2, 6.4], c: [-6, 2.4, 0.6], f: 38 },
    { t: 44, p: [-51.5, 2.0, 6.8], c: [-39, 2.15, 0.2], f: 40, mir: true },
    { t: 49, p: [-15, 3.3, 5.6], c: [1, 3.1, 3.5], f: 42 },
    { t: 54, p: [-12, 3.25, 5.4], c: [2, 3.1, 3.6], f: 42, mir: true },
    { t: 58, p: [-12.4, 1.95, 8.3], c: [-6.6, 1.5, 1.4], f: 38 },
    { t: 64, p: [-11.8, 1.9, 8.0], c: [-6.4, 1.55, 1.2], f: 38 },
    { t: 69, p: [-22, 2.8, 10], c: [-42, 2.2, 0], f: 42 },
    { t: 75, p: { v: [-30, 5, 15] }, c: { v: [-4, 2, 0] }, f: 42 },
    { t: 82, p: { v: [24, 3.2, 10] }, c: { v: [-14, 2.0, 0] }, f: 42 },
    { t: 88, p: { v: [60, 22, 46] }, c: { v: [-30, 2, -20] }, f: 44 },
    { t: 89.4, p: { v: [86, 40, 76] }, c: { v: [-20, 2, -30] }, f: 44 },
    // vožnja v rezih: cerkev na griču, kozolec, mestece s šolo; vlak gre
    // skozi vsak kader od desne proti levi
    { t: 89.5, p: [-1415, 26, -40], c: [-1500, 4, -330], f: 40, rez: true },
    { t: 94, p: [-1440, 25, -48], c: [-1600, 4, -320], f: 40 },
    { t: 94, p: [-2105, 3.2, -45], c: [-2170, 4.5, -125], f: 42, rez: true },
    { t: 100, p: [-2110, 3.4, -48], c: [-2265, 4.5, -110], f: 42 },
    { t: 100, p: [-2860, 48, 175], c: [-3260, 10, 40], f: 42, rez: true },
    { t: 110, p: [-2990, 46, 160], c: [-3270, 8, 40], f: 42 },
    { t: 116, p: [-3140, 46, 105], c: [-3250, 3, 4], f: 44 },
    { t: 122, p: [-3060, 120, 330], c: [-2600, 0, -60], f: 46 },
    { t: 128, p: [-2700, 900, 900], c: [-1800, 0, -100], f: 50 },
    // noč: z višine k peronu, nato k dijaku na klopi
    { t: 206, p: [-30, 34, 48], c: [-6, 2, 2], f: 44, rez: true },
    { t: 213.5, p: [-27.5, 6.5, 16.0], c: [-17, 1.6, 6.2], f: 42 },
    { t: 222, p: [-20.1, 2.05, 8.3], c: [-17.3, 1.4, 6.55], f: 40, mir: true },
    { t: 240, p: [-19.8, 1.98, 8.05], c: [-17.35, 1.38, 6.55], f: 37 },
  ];
  const tA = new THREE.Vector3();
  // rezi: ključ z `rez` začne nov kader, kamera tja skoči (montaža vožnje)
  const kadri = [];
  for (const k of KAMERA) {
    if (k.rez || !kadri.length) kadri.push([]);
    kadri[kadri.length - 1].push(k);
  }
  function kameraVSvetu(T) {
    let kader = kadri[0];
    for (const kd of kadri) if (kd[0].t <= T) kader = kd;
    // ključe preračunaj v svet za ta T, nato Hermite v času
    const P = kader.map((k) => ({ t: k.t, v: vSvet(k.p, T, tA).toArray().concat(vSvet(k.c, T, tA).toArray(), [k.f]), mir: k.mir }));
    if (P.length === 1) return P[0].v;
    return zlepek(P)(T);
  }

  // ---------- drsenje -> T ----------
  const takti = [...document.querySelectorAll('.takt')];
  let meje = [];
  function izmeri() {
    const y0 = scrollY;
    meje = takti.map((el) => {
      const r = el.getBoundingClientRect();
      return { el, top: r.top + y0, h: r.height, t0: +el.dataset.t0, t1: +el.dataset.t1, kart: el.querySelector('.kartica') };
    });
  }
  function Tiz(scroll) {
    const c = scroll + innerHeight * 0.5;
    if (!meje.length) return 0;
    if (c <= meje[0].top) return meje[0].t0;
    for (const m of meje) {
      if (c <= m.top + m.h) return lerp(m.t0, m.t1, clamp((c - m.top) / m.h));
    }
    return meje[meje.length - 1].t1;
  }
  function fadeBesedila() {
    const c = scrollY + innerHeight * 0.5;
    for (const m of meje) {
      if (!m.kart) continue;
      const p = (c - m.top) / m.h;
      const o = manjGibanja ? (p > -0.1 && p < 1.1 ? 1 : 0) : okno(p, -0.02, 0.14, 0.84, 1.0);
      m.kart.style.opacity = o.toFixed(3);
      m.kart.style.transform = `translate3d(0, ${((1 - smooth(-0.02, 0.14, p)) * 18).toFixed(1)}px, 0)`;
    }
  }
  izmeri();
  addEventListener('resize', () => {
    renderer.setSize(innerWidth, innerHeight, false);
    izmeri();
  });
  new ResizeObserver(izmeri).observe(document.body);

  // ---------- oznake v prostoru ----------
  const oznake = [...document.querySelectorAll('.oznaka3d[data-p]')].map((el) => ({
    el, p: new THREE.Vector3(...el.dataset.p.split(',').map(Number)), t0: +el.dataset.t0, t1: +el.dataset.t1,
  }));
  const poglavja = [...document.querySelectorAll('.poglavja a')].map((a) => ({ a, od: +a.dataset.od }));
  let zadnjePoglavje = -1;
  function oznaciPoglavje(T) {
    let k = 0;
    poglavja.forEach((p, i) => { if (T >= p.od - 0.01) k = i; });
    if (k === zadnjePoglavje) return;
    zadnjePoglavje = k;
    poglavja.forEach((p, i) => p.a.setAttribute('aria-current', i === k ? 'true' : 'false'));
  }
  const hud = document.querySelector('.hud-ura');
  const hudCas = hud?.querySelector('b');
  const hudOzn = hud?.querySelector('span');
  const prehod = document.querySelector('.prehod');
  // dejstva za filmom: ko pridejo pod glavo, ta dobi podlago, ura v kotu izgine
  const dodatek = document.querySelector('.dodatek');
  const glava = document.querySelector('.vrh');
  const v4 = new THREE.Vector4();

  // ---------- stanje sveta po T ----------
  const tB = new THREE.Vector3(), sX = new THREE.Vector3(), sY = new THREE.Vector3();
  // Ura postaje kot švicarska podrejena ura: sekundni kazalec teče v
  // realnem času in na vrhu počaka minutni impulz, ki ga prinese drsenje (čas
  // zgodbe). Naprej ujame zgodbo, nazaj se zvezno previje; nikoli ne skoči.
  let uraC = null, uraCas = 0, previja = false;
  function uraKorak(S, cas) {
    const dt = uraCas ? clamp(cas - uraCas, 0, 0.25) : 0;
    uraCas = cas;
    if (uraC === null || Math.abs(S - uraC) > 1800 || manjGibanja) { uraC = S; previja = false; return uraC; }
    const konec = Math.floor(S / 60) * 60 + 60;
    const k = 1 - Math.exp(-dt * 7);
    if (uraC >= konec) previja = true;
    if (previja && uraC > S + 0.3) {
      uraC = Math.max(S, uraC - Math.max(dt * 2, (uraC - S) * k));
    } else if (uraC < S - 0.3) {
      previja = false;
      uraC = Math.min(S, uraC + Math.max(dt, (S - uraC) * k));
    } else {
      previja = false;
      uraC = Math.min(uraC + dt, konec - 1e-3);
    }
    return uraC;
  }
  // Pot dijaka do vrat vmesnega voza in v preddverje (vlak na postaji stoji,
  // zato se izračuna enkrat): čakališče, pred vrati, prag, preddverje,
  // stopnice v zgornjo etažo.
  let potD = null;
  function potDijaka() {
    if (potD) return potD;
    // vlak za trenutek na postajo (kolesa se zavrtijo nazaj, ko se vrne)
    const sZdaj = vlak.zadnjiS();
    vlak.postavi(proga, S_POSTAJA);
    const { xa, xb } = vlak.VRATA, xc = (xa + xb) / 2, X0 = xa - 0.9;
    const pred = vlak.vrataLok(xc, 0, -2.25);
    const tocke = [
      new THREE.Vector3(-8.1, PERON.y, 4.3),
      new THREE.Vector3(lerp(-8.1, pred.x, 0.55), PERON.y, 3.1),
      new THREE.Vector3(pred.x, PERON.y, pred.z),
      vlak.vrataLok(xc, 0.58, -1.3),
      vlak.vrataLok(xc - 0.2, 0.58, -0.45),
      vlak.vrataLok(X0 + 0.45, 0.58, -0.08),
      vlak.vrataLok(X0 - 0.25, 0.58 + 0.25 / 0.27 * 0.245, 0.0),
      vlak.vrataLok(X0 - 1.5, 0.58 + 1.5 / 0.27 * 0.245, 0.0),
    ];
    const krivulja = new THREE.CatmullRomCurve3(tocke, false, 'centripetal', 0.5);
    potD = { krivulja, dolzina: krivulja.getLength() };
    if (sZdaj !== null) vlak.postavi(proga, sZdaj);
    return potD;
  }
  let zadnjaTabla = -1;
  let okoljeZdaj = 'zora';
  function postavi(T, cas) {
    const noc = T >= 206;
    // atmosfera
    if (noc) atm.nastavi('noc');
    else atm.nastavi('zora', 'jutro', smooth(60, 118, T));
    const zelenoOkolje = noc ? 'noc' : 'zora';
    if (zelenoOkolje !== okoljeZdaj) { svet.environment = okolja[zelenoOkolje]; okoljeZdaj = zelenoOkolje; }
    svet.environmentIntensity = atm.stanje.okolje;
    atm.U.uCasN.value = cas;
    renderer.toneMappingExposure = atm.stanje.izp;
    // vlak
    const s = sVlaka(T);
    vlak.postavi(proga, s);
    vlak.nastaviLuci(true, noc ? 1 : smooth(0, 1, 0) * 0.2);
    // sij žarometov: močan v megli, ko vlak prihaja
    proga.tocka(s, nos); proga.smer(s, smerV);
    desno.crossVectors(smerV, UP).normalize();
    const sijM = noc ? 0 : okno(T, 24, 30, 42, 48) * 0.6;
    sijMat.uniforms.uMoc.value = sijM;
    for (const sj of siji) {
      sj.m.visible = sijM > 0.01;
      sj.m.position.copy(nos).addScaledVector(smerV, 0.25).addScaledVector(desno, sj.z).setY(1.56);
      sj.m.lookAt(kamera.position);
    }
    // ura postaje in tabla
    const S = casZgodbe(T);
    postaja.ura.nastavi(uraKorak(S, cas));
    postaja.ura.obraz.emissiveIntensity = noc ? 1.0 : 0.38;
    const zam = noc || S < hms(7, 42, 30) ? 0 : S < hms(7, 46) ? 5 : S < hms(7, 49) ? 10 : 13;
    if (zam !== zadnjaTabla) { postaja.tabla.narisi(zam); zadnjaTabla = zam; }
    // dijak: čaka s telefonom, pospravi ga, gre skozi vrata in po stopnicah
    // gor; ponoči sedi na klopi s prenosnikom
    if (noc) {
      dijak.skupina.visible = true;
      dijak.skupina.position.set(-17.6, PERON.y, 6.98);
      dijak.skupina.rotation.y = Math.PI / 2;
      dijak.poza(0, Math.sin(cas * 0.4) * 0.08, 0, 1);
    } else {
      const pot = potDijaka();
      const u = smooth(57.8, 63.3, T) * 0.55 + clamp((T - 57.8) / 5.5) * 0.45;
      const d = u * pot.dolzina;
      pot.krivulja.getPointAt(Math.min(u, 1), tA);
      pot.krivulja.getTangentAt(Math.min(u, 0.999), tB);
      dijak.skupina.visible = T < 63.4;
      dijak.skupina.position.copy(tA);
      const smerPoti = Math.atan2(-tB.z, tB.x);
      dijak.skupina.rotation.y = lerp(0.35, smerPoti, smooth(57.2, 58.3, T));
      dijak.poza(T > 57.8 ? d : 0, lerp(-0.3, 0.5, okno(T, 3, 6, 40, 46)) * (1 - smooth(57, 58, T)), 1 - smooth(56.8, 57.9, T), 0);
    }
    // vrata: odprejo se ob 56,2, zaprejo ob 63,6
    vlak.odpriVrata(noc ? 0 : smooth(56.2, 57.6, T) * (1 - smooth(63.6, 65.0, T)));
    // luči ponoči
    for (const m of postaja.luci) m.emissiveIntensity = noc ? 2.6 : 0.5;
    for (const m of postaja.fasade) m.emissiveIntensity = noc ? 1.1 : 0;
    naselja.userData.okna.emissiveIntensity = noc ? 0.9 : 0;
    sola.userData.okna.emissiveIntensity = noc ? 0 : okno(T, 98, 104, 120, 128) * 0.25;
    for (const [l, i] of nocneLuci) l.intensity = noc ? i : 0;
    megla.userData.mat.uniforms.uMoc.value = noc ? 0.25 : 1 - smooth(70, 120, T) * 0.6;
    // senčna kamera sledi pogledu; središče zaskoči na mrežo tekslov senčne
    // karte, da robovi senc ob premiku kamere ne migljajo
    const sm = atm.U.uSonce.value;
    const velikost = T > 84 && T < 128 ? 220 : 80;
    const ss = atm.sonce.shadow.camera;
    ss.left = -velikost; ss.right = velikost; ss.top = velikost; ss.bottom = -velikost;
    ss.near = 1; ss.far = 1200; ss.updateProjectionMatrix();
    const cilj = T > 84 && T < 128 ? nos : kamera.position;
    const teksel = (2 * velikost) / atm.sonce.shadow.mapSize.x;
    sX.crossVectors(UP, sm).normalize(); sY.crossVectors(sm, sX);
    tA.set(cilj.x, 0, cilj.z);
    const kx = Math.round(tA.dot(sX) / teksel) * teksel, ky = Math.round(tA.dot(sY) / teksel) * teksel;
    atm.sonce.target.position.set(0, 0, 0).addScaledVector(sX, kx).addScaledVector(sY, ky).addScaledVector(sm, tA.dot(sm));
    atm.sonce.position.copy(atm.sonce.target.position).addScaledVector(sm, 500);
    vlak.kamera(kamera);
  }

  // okvir: subjekt nad besedilom (telefon) ali desno od njega (namizje)
  function okvir(kam = kamera) {
    const w = innerWidth, h = innerHeight;
    kam.aspect = w / h;
    const pokoncno = w / h < 0.85;
    // v uvodu je ura bolj desno (na telefonu višje), da ima velik naslov prostor
    const uvod = smooth(3, 12, T);
    const cx = pokoncno ? 0.5 : lerp(0.67, 0.6, uvod), cy = pokoncno ? lerp(0.33, 0.4, uvod) : 0.5;
    const FW = w * 2 * Math.max(cx, 1 - cx), FH = h * 2 * Math.max(cy, 1 - cy);
    kam.setViewOffset(FW, FH, FW / 2 - cx * w, FH / 2 - cy * h, w, h);
  }

  // ---------- zanka ----------
  let Tcilj = 0, T = 0, zadnji = performance.now(), mirujeOd = 0, prisilni = null;
  let povpMs = 16, stejKadri = 0;
  let pripravljeno = false;
  const kmp = [];
  let pogled = null;   // preizkus: lastna kamera {p, c, f}
  function risi(cas) {
    const k = pogled ? [...pogled.p, ...pogled.c, pogled.f] : kameraVSvetu(T);
    const scenaKarta = T >= 128 && T < 206;
    let hudKarta = null;
    if (!scenaKarta) {
      karta?.skrij();
      const tlaK = T >= 206 ? PERON.y + 1.1 : T > 70 ? visina(k[0], k[2], proga) + 2.2 : -1e9;
      kamera.position.set(k[0], Math.max(k[1], tlaK), k[2]);
      // v uvodu kamera rahlo diha, da prizor ni fotografija
      const dih = manjGibanja ? 0 : 1 - smooth(0, 3, T);
      if (dih > 0) kamera.position.add(tA.set(Math.sin(cas * 0.33) * 0.03, Math.sin(cas * 0.27) * 0.02, Math.cos(cas * 0.21) * 0.02).multiplyScalar(dih));
      kamera.lookAt(k[3], k[4], k[5]);
      // vodoravno vidno polje ne sme biti preozko na telefonu
      const asp = innerWidth / innerHeight;
      const fv = THREE.MathUtils.degToRad(k[6]);
      const potreb = 2 * Math.atan(Math.tan(Math.atan(Math.tan(fv / 2) * 1.6) * 0.78) / asp);
      kamera.fov = THREE.MathUtils.radToDeg(Math.min(Math.max(fv, potreb), THREE.MathUtils.degToRad(78)));
      okvir();
      // bližnja ravnina čim dlje: natančnost globine v daljavi (tir, gramoz)
      kamera.near = clamp(Math.hypot(k[3] - k[0], k[4] - k[1], k[5] - k[2]) * 0.02, 0.15, 0.6);
      kamera.updateProjectionMatrix();
      postavi(T, cas);
      tir.zice.material.uniforms.uLoc.value.set(platnoEl.width, platnoEl.height);
      renderer.render(svet, kamera);
    } else {
      if (karta) hudKarta = karta.risi(renderer, T, cas, okvir);
      else { renderer.setClearColor('#0a0d12', 1); renderer.clear(); }
    }
    // oznake in ura v kotu
    for (const o of oznake) {
      const vid = okno(T, o.t0, o.t0 + 1.5, o.t1 - 1.5, o.t1);
      if (vid <= 0.001 || scenaKarta) { o.el.style.opacity = 0; continue; }
      v4.set(o.p.x, o.p.y, o.p.z, 1).applyMatrix4(kamera.matrixWorldInverse).applyMatrix4(kamera.projectionMatrix);
      const x = (v4.x / v4.w * 0.5 + 0.5) * innerWidth, y = (-v4.y / v4.w * 0.5 + 0.5) * innerHeight;
      o.el.style.opacity = v4.w > 0 ? vid.toFixed(3) : 0;
      o.el.style.transform = `translate3d(${x.toFixed(1)}px, ${y.toFixed(1)}px, 0)`;
    }
    const dodVrh = dodatek ? dodatek.getBoundingClientRect().top : Infinity;
    glava?.classList.toggle('nad-dodatkom', dodVrh < 64);
    if (hud) {
      const vid = (hudKarta ? hudKarta.vid : okno(T, 64, 70, 124, 128) + okno(T, 206, 212, 260, 270))
        * (1 - smooth(innerHeight * 0.9, innerHeight * 0.55, dodVrh));
      hud.style.opacity = vid.toFixed(3);
      if (vid > 0) {
        hudOzn.textContent = hudKarta ? hudKarta.oznaka : 'ura v zgodbi';
        hudCas.textContent = fmt(hudKarta ? hudKarta.cas : uraC ?? casZgodbe(T));
      }
    }
    if (prehod) {
      const a = okno(T, 123, 128, 128, 131.5);
      const b = okno(T, 202, 206, 206, 209);
      prehod.style.opacity = Math.max(a, b).toFixed(3);
      prehod.style.background = a > b ? '#e9e4dc' : '#05070b';
    }
  }

  function zanka() {
    const zdaj = performance.now();
    const dt = Math.min(0.1, (zdaj - zadnji) / 1000);
    zadnji = zdaj;
    Tcilj = prisilni ?? Tiz(scrollY);
    const prej = T;
    T = manjGibanja ? Tcilj : T + (Tcilj - T) * (1 - Math.exp(-dt * 6.5));
    if (Math.abs(Tcilj - T) < 0.002) T = Tcilj;
    fadeBesedila();
    oznaciPoglavje(Tcilj);
    const giba = Math.abs(T - prej) > 1e-4;
    if (giba) mirujeOd = zdaj;
    // v miru 30 sl/s (sekundni kazalec, megla), sicer vsak kader
    if (giba || zdaj - mirujeOd < 400 || stejKadri++ % 2 === 0) {
      // prilagodi ločljivost PRED risanjem: setSize pobriše platno
      if (!fiksnaDpr) {
        if (povpMs > 22 && dpr > 0.75) { dpr = Math.max(0.75, dpr - 0.15); renderer.setPixelRatio(dpr); renderer.setSize(innerWidth, innerHeight, false); povpMs = 16; }
        else if (povpMs < 9 && dpr < maxDpr) { dpr = Math.min(maxDpr, dpr + 0.1); renderer.setPixelRatio(dpr); renderer.setSize(innerWidth, innerHeight, false); povpMs = 14; }
      }
      const t0 = performance.now();
      risi(zdaj / 1000);
      const ms = performance.now() - t0;
      povpMs = povpMs * 0.95 + ms * 0.05;
    }
    if (!pripravljeno) {
      pripravljeno = true;
      document.documentElement.classList.add('pripravljeno');
      window.__pripravljen = true;
    }
    requestAnimationFrame(zanka);
  }
  // senčilnike prevedi med nalaganjem, ne ob prvem drsenju
  try {
    kamera.position.set(-1.5, 3.2, 2.6); kamera.lookAt(0, 3.3, 3.05);
    await renderer.compileAsync(svet, kamera);
  } catch (e) { /* starejši brskalnik: prevede ob prvem kadru */ }
  await korak(1);
  // prvi kader
  izmeri();
  T = Tcilj = Tiz(scrollY);
  risi(performance.now() / 1000);
  requestAnimationFrame(zanka);

  // kljuke za preizkus (CDP)
  window.__film = {
    pojdi(t) { prisilni = t; T = Tcilj = t; risi(performance.now() / 1000); },
    pogled(p, c, f = 40) { pogled = p ? { p, c, f } : null; risi(performance.now() / 1000); },
    skoci() { prisilni = null; T = Tcilj = Tiz(scrollY); fadeBesedila(); risi(performance.now() / 1000); },
    T: () => T,
    kam: (t) => kameraVSvetu(t),
    ura: () => uraC,
    vlakS: (t) => sVlaka(t),
    vlakXZ: (t) => { const v = proga.tocka(sVlaka(t), new THREE.Vector3()); return [Math.round(v.x), Math.round(v.z)]; },
    info: () => ({ drevesa: drevesa.userData.stevilo, dpr, klici: renderer.info.render.calls, tri: renderer.info.render.triangles }),
  };
}

zagon().catch((e) => {
  console.error(e);
  document.documentElement.classList.add('brez-3d');
  window.__pripravljen = true;
});
