// Pogl. 3: Slovenija od zgoraj. Relief, meja, železnice in avtobusne trase,
// vsaka vožnja enega jutra (1. 10. 2026, 7.00-8.00) kot pika z barvo zamude,
// zamude IC 351 Ljubljana-Maribor po dnevih kot zavesa nad progo.
// Enota je kilometer; višine trikrat povečane.
import * as THREE from 'three';
import { LineSegments2 } from 'three/examples/jsm/lines/LineSegments2.js';
import { LineSegmentsGeometry } from 'three/examples/jsm/lines/LineSegmentsGeometry.js';
import { LineMaterial } from 'three/examples/jsm/lines/LineMaterial.js';
import { clamp, lerp, smooth, okno, zlepek } from './orodja.js';

const E = 3.0;           // povečava višin
// Temna lestvica zamud (oznake.md) iz spremenljivk v base.css, da je paleta
// na enem mestu; zapisane vrednosti so le rezerva, kadar sloga ni.
const BARVE_ZAM = (() => {
  const css = getComputedStyle(document.documentElement);
  return [['--d-ontime', '#7c8698'], ['--d-small', '#f2a87e'], ['--d-mid', '#e07b45'], ['--d-big', '#b85417']]
    .map(([k, rez]) => css.getPropertyValue(k).trim() || rez);
})();

// Slike s podatki: brez pretvorbe barv, sicer se vrednosti spremenijo.
async function naloziPodatke(src) {
  const blob = await (await fetch(src)).blob();
  const bmp = await createImageBitmap(blob, { colorSpaceConversion: 'none', premultiplyAlpha: 'none' });
  const c = document.createElement('canvas');
  c.width = bmp.width; c.height = bmp.height;
  const g = c.getContext('2d', { willReadFrequently: true });
  g.drawImage(bmp, 0, 0);
  return { w: bmp.width, h: bmp.height, px: g.getImageData(0, 0, bmp.width, bmp.height).data };
}

// razred zamude iz zaokrožene minute, kot na strani (floor(x + 0,5))
function razred(sek) {
  const m = Math.floor(sek / 60 + 0.5);
  return m <= 0 ? 0 : m <= 5 ? 1 : m <= 15 ? 2 : 3;
}

// poti: naslovi datotek s podatki (data-karta, data-podatki, data-relief na platnu)
export async function zgradiKarto(poti) {
  const [meta, pod, rel] = await Promise.all([fetch(poti.karta).then((r) => r.json()), naloziPodatke(poti.podatki), naloziPodatke(poti.relief)]);
  const i16 = new Int16Array(meta.n_int16);
  for (let i = 0; i < meta.n_int16; i++) i16[i] = pod.px[i * 4] * 256 + pod.px[i * 4 + 1] - 32768;
  const ENOTA = meta.enota / 1000;   // km na enoto
  const R = meta.relief;

  // višine na CPE (za polaganje črt in pik)
  const px = rel.px;
  const H = new Float32Array(R.nx * R.nz), MASKA = new Float32Array(R.nx * R.nz);
  for (let i = 0; i < R.nx * R.nz; i++) { H[i] = (px[i * 4] * 256 + px[i * 4 + 1]) * R.skala; MASKA[i] = px[i * 4 + 2] / 255; }
  const x0 = R.x0 / 1000, x1 = R.x1 / 1000, z0 = R.z0 / 1000, z1 = R.z1 / 1000;
  function visinaKm(x, z) {
    const fx = clamp((x - x0) / (x1 - x0) * R.nx - 0.5, 0, R.nx - 1.001);
    const fz = clamp((z - z0) / (z1 - z0) * R.nz - 0.5, 0, R.nz - 1.001);
    const i = Math.floor(fx), j = Math.floor(fz), tx = fx - i, tz = fz - j;
    const a = H[j * R.nx + i], b = H[j * R.nx + i + 1], c = H[(j + 1) * R.nx + i], d = H[(j + 1) * R.nx + i + 1];
    return ((a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + d * tx) * tz) / 1000 * E;
  }
  // višinska tekstura: polovična plavajoča vejica, linearno filtriranje
  const hf = new Uint16Array(R.nx * R.nz * 2);
  for (let i = 0; i < R.nx * R.nz; i++) { hf[i * 2] = THREE.DataUtils.toHalfFloat(H[i]); hf[i * 2 + 1] = THREE.DataUtils.toHalfFloat(MASKA[i]); }
  const visTex = new THREE.DataTexture(hf, R.nx, R.nz, THREE.RGFormat, THREE.HalfFloatType);
  visTex.magFilter = visTex.minFilter = THREE.LinearFilter;
  visTex.flipY = false;
  visTex.needsUpdate = true;

  const scena = new THREE.Scene();
  const OZADJE = new THREE.Color('#05080d');
  scena.background = OZADJE;
  const kamera = new THREE.PerspectiveCamera(42, 1, 0.05, 3000);

  // ---------- relief ----------
  const W = x1 - x0, D = z1 - z0;
  const rg = new THREE.PlaneGeometry(W, D, Math.round(R.nx / 2), Math.round(R.nz / 2));
  rg.rotateX(-Math.PI / 2);
  rg.translate((x0 + x1) / 2, 0, (z0 + z1) / 2);
  const uRel = {
    uVis: { value: visTex }, uE: { value: E }, uTexel: { value: new THREE.Vector2(1 / R.nx, 1 / R.nz) },
    uKm: { value: new THREE.Vector2(W / R.nx, D / R.nz) }, uOzadje: { value: OZADJE }, uSvetlost: { value: 1 },
    uX0: { value: new THREE.Vector4(x0, z0, W, D) },
  };
  const relief = new THREE.Mesh(rg, new THREE.ShaderMaterial({
    uniforms: uRel,
    vertexShader: /* glsl */`
      uniform sampler2D uVis; uniform float uE; uniform vec4 uX0;
      varying vec2 vUv; varying vec3 vW;
      void main() {
        vec3 p = position;
        vUv = vec2((p.x - uX0.x) / uX0.z, (p.z - uX0.y) / uX0.w);
        p.y = texture2D(uVis, vUv).r / 1000.0 * uE;
        vW = p;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
      }`,
    fragmentShader: /* glsl */`
      uniform sampler2D uVis; uniform float uE; uniform vec2 uTexel; uniform vec2 uKm; uniform vec3 uOzadje; uniform float uSvetlost;
      varying vec2 vUv; varying vec3 vW;
      void main() {
        vec2 s = texture2D(uVis, vUv).rg;
        float h = s.r, maska = smoothstep(0.15, 0.85, s.g);
        float hl = texture2D(uVis, vUv - vec2(uTexel.x, 0.0)).r, hr = texture2D(uVis, vUv + vec2(uTexel.x, 0.0)).r;
        float hd = texture2D(uVis, vUv - vec2(0.0, uTexel.y)).r, hu = texture2D(uVis, vUv + vec2(0.0, uTexel.y)).r;
        vec3 n = normalize(vec3((hl - hr) / 1000.0 * uE / (2.0 * uKm.x), 1.0, (hd - hu) / 1000.0 * uE / (2.0 * uKm.y)));
        float sv = max(dot(n, normalize(vec3(-0.55, 0.72, -0.42))), 0.0);
        float sv2 = max(dot(n, normalize(vec3(0.5, 0.6, 0.6))), 0.0);
        vec3 nizko = vec3(0.034, 0.046, 0.066), visoko = vec3(0.15, 0.17, 0.205);
        vec3 c = mix(nizko, visoko, smoothstep(150.0, 2400.0, h));
        c *= 0.38 + 0.95 * sv + 0.14 * sv2;
        // plastnice vsakih 100 m, krepkejše vsakih 500 m
        float k = h / 100.0, w = fwidth(k);
        float pl = 1.0 - smoothstep(0.0, w * 1.3, abs(fract(k - 0.5) - 0.5));
        float k5 = h / 500.0, w5 = fwidth(k5);
        float pl5 = 1.0 - smoothstep(0.0, w5 * 1.6, abs(fract(k5 - 0.5) - 0.5));
        c += vec3(0.30, 0.40, 0.55) * (pl * 0.045 + pl5 * 0.09) * maska * step(60.0, h);
        // zunaj države skoraj ozadje: Slovenija lebdi
        c = mix(uOzadje * 1.15 + c * 0.16, c, maska);
        // robovi domene v ozadje
        float rob = smoothstep(0.0, 0.1, vUv.x) * smoothstep(1.0, 0.9, vUv.x) * smoothstep(0.0, 0.12, vUv.y) * smoothstep(1.0, 0.88, vUv.y);
        c = mix(uOzadje, c, rob) * uSvetlost;
        gl_FragColor = vec4(c, 1.0);
        #include <colorspace_fragment>
      }`,
  }));
  scena.add(relief);

  // ---------- črte ----------
  const LJ = meta.mesta.find((m) => m[0] === 'Ljubljana');
  const sredisce = new THREE.Vector2(LJ[1] / 1000, LJ[2] / 1000);
  const razkritje = (m, uRaz) => {
    m.onBeforeCompile = (sh) => {
      sh.uniforms.uRaz = uRaz;
      sh.uniforms.uSr = { value: sredisce };
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', '#include <common>\nuniform vec2 uSr; varying float vRaz;')
        .replace('vec4 start = modelViewMatrix * vec4( instanceStart, 1.0 );',
          'vRaz = mix(distance(instanceStart.xz, uSr), distance(instanceEnd.xz, uSr), position.y < 0.5 ? 0.0 : 1.0);\nvec4 start = modelViewMatrix * vec4( instanceStart, 1.0 );');
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', '#include <common>\nuniform float uRaz; varying float vRaz;')
        .replace('vec4 diffuseColor = vec4( diffuse, alpha );',
          'if (vRaz > uRaz) discard;\nvec4 diffuseColor = vec4( diffuse * (1.0 + 2.5 * smoothstep(uRaz - 9.0, uRaz, vRaz)), alpha );');
    };
  };
  const uRazP = { value: 0 }, uRazB = { value: 0 };
  // železnice
  const pos = [];
  let o = 0;
  const pr = i16.subarray(0, meta.dolzina_prog);
  while (o < pr.length) {
    const n = pr[o++];
    let prej = null;
    for (let k = 0; k < n; k++) {
      const x = pr[o++] * ENOTA, z = pr[o++] * ENOTA;
      const y = visinaKm(x, z) + 0.06;
      if (prej) pos.push(...prej, x, y, z);
      prej = [x, y, z];
    }
  }
  const progeG = new LineSegmentsGeometry().setPositions(pos);
  const progeM = new LineMaterial({ color: '#ffd6ae', linewidth: 1.9, transparent: true, opacity: 0.95, depthWrite: false });
  const sijM = new LineMaterial({ color: '#f0934f', linewidth: 7, transparent: true, opacity: 0.16, depthWrite: false, blending: THREE.AdditiveBlending });
  razkritje(progeM, uRazP); razkritje(sijM, uRazP);
  const proge = new LineSegments2(progeG, progeM);
  const progeSij = new LineSegments2(progeG, sijM);
  proge.renderOrder = 3; progeSij.renderOrder = 2;
  scena.add(progeSij, proge);
  // avtobusne trase: tanke, hladne
  const bpos = [];
  const bu = i16.subarray(meta.dolzina_prog, meta.dolzina_prog + meta.n_bus * 4);
  const BM = 0.24;   // km na celico
  for (let k = 0; k < bu.length; k += 4) {
    const xa = bu[k] * BM, za = bu[k + 1] * BM, xb = bu[k + 2] * BM, zb = bu[k + 3] * BM;
    bpos.push(xa, visinaKm(xa, za) + 0.04, za, xb, visinaKm(xb, zb) + 0.04, zb);
  }
  const busG = new LineSegmentsGeometry().setPositions(bpos);
  const busM = new LineMaterial({ color: '#6f8fb3', linewidth: 0.9, transparent: true, opacity: 0.32, depthWrite: false });
  razkritje(busM, uRazB);
  const bus = new LineSegments2(busG, busM);
  bus.renderOrder = 1;
  scena.add(bus);
  // meja
  const ob = meta.obris;
  const mpos = [];
  for (let k = 0; k < ob.length; k += 2) {
    const a = k, b = (k + 2) % ob.length;
    const xa = ob[a] / 1000, za = ob[a + 1] / 1000, xb = ob[b] / 1000, zb = ob[b + 1] / 1000;
    mpos.push(xa, visinaKm(xa, za) + 0.1, za, xb, visinaKm(xb, zb) + 0.1, zb);
  }
  const mejaM = new LineMaterial({ color: '#c8d3e4', linewidth: 1.2, transparent: true, opacity: 0.45, depthWrite: false, dashed: true, dashSize: 1.2, gapSize: 0.8 });
  const mejaG = new LineSegmentsGeometry().setPositions(mpos);
  const meja = new LineSegments2(mejaG, mejaM);
  meja.computeLineDistances();
  scena.add(meja);
  const crte = [progeM, sijM, busM, mejaM];

  // ---------- vožnje ----------
  const vo = i16.subarray(meta.dolzina_prog + meta.n_bus * 4, meta.dolzina_prog + meta.n_bus * 4 + meta.dolzina_vozenj);
  const voznje = [];
  o = 0;
  while (o < vo.length) {
    const vrsta = vo[o++], n = vo[o++];
    const t = new Float32Array(n), x = new Float32Array(n), z = new Float32Array(n), d = new Float32Array(n);
    for (let k = 0; k < n; k++) { t[k] = vo[o++]; x[k] = vo[o++] * ENOTA; z[k] = vo[o++] * ENOTA; d[k] = vo[o++] * 10; }
    voznje.push({ vrsta, t, x, z, d });
  }
  const N = voznje.length;
  const pp = new Float32Array(N * 3), pc = new Float32Array(N * 3), ps = new Float32Array(N);
  const tg = new THREE.BufferGeometry();
  tg.setAttribute('position', new THREE.BufferAttribute(pp, 3));
  tg.setAttribute('color', new THREE.BufferAttribute(pc, 3));
  tg.setAttribute('aVel', new THREE.BufferAttribute(ps, 1));
  const uPike = { uDpr: { value: 1 }, uVid: { value: 0 } };
  const pike = new THREE.Points(tg, new THREE.ShaderMaterial({
    uniforms: uPike,
    vertexShader: /* glsl */`
      attribute float aVel; uniform float uDpr; varying vec3 vC; varying float vV;
      void main() {
        vC = color; vV = aVel;
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = aVel * uDpr * clamp(230.0 / -mv.z, 0.9, 2.6);
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: /* glsl */`
      uniform float uVid; varying vec3 vC; varying float vV;
      void main() {
        if (vV <= 0.0) discard;
        float d = length(gl_PointCoord - 0.5) * 2.0;
        float jedro = 1.0 - smoothstep(0.28, 0.4, d);
        float sij = exp(-d * d * 4.0) * 0.7;
        float a = max(jedro, sij) * uVid;
        if (a < 0.01) discard;
        gl_FragColor = vec4(mix(vC, vec3(1.0), jedro * 0.25), a);
        #include <colorspace_fragment>
      }`,
    vertexColors: true, transparent: true, depthWrite: false,
  }));
  pike.frustumCulled = false;
  pike.renderOrder = 5;
  scena.add(pike);
  const barve = BARVE_ZAM.map((c) => new THREE.Color(c));
  function postaviVoznje(tr) {
    for (let i = 0; i < N; i++) {
      const v = voznje[i];
      const n = v.t.length;
      if (tr < v.t[0] || tr > v.t[n - 1]) { ps[i] = 0; continue; }
      let a = 0, b = n - 1;
      while (b - a > 1) { const m = (a + b) >> 1; if (v.t[m] <= tr) a = m; else b = m; }
      const f = v.t[b] > v.t[a] ? (tr - v.t[a]) / (v.t[b] - v.t[a]) : 0;
      const x = v.x[a] + (v.x[b] - v.x[a]) * f, z = v.z[a] + (v.z[b] - v.z[a]) * f;
      const dz = v.d[a] + (v.d[b] - v.d[a]) * f;
      pp[i * 3] = x; pp[i * 3 + 1] = visinaKm(x, z) + 0.18; pp[i * 3 + 2] = z;
      const c = barve[v.vrsta === 0 ? razred(dz) : razred(dz)];
      pc[i * 3] = c.r; pc[i * 3 + 1] = c.g; pc[i * 3 + 2] = c.b;
      ps[i] = v.vrsta === 0 ? 12 : v.vrsta === 2 ? 4.2 : 5.2;
    }
    tg.attributes.position.needsUpdate = true;
    tg.attributes.color.needsUpdate = true;
    tg.attributes.aVel.needsUpdate = true;
  }

  // ---------- zavesa zamud IC 351 ----------
  const vr = meta.vrsta;
  const pot = [];
  for (let k = 0; k < vr.pot.length; k += 2) pot.push([vr.pot[k] / 1000, vr.pot[k + 1] / 1000]);
  const dol = [0];
  for (let k = 1; k < pot.length; k++) dol.push(dol[k - 1] + Math.hypot(pot[k][0] - pot[k - 1][0], pot[k][1] - pot[k - 1][1]));
  // lega postaj na poti: najbližja točka
  const sPost = vr.postaje.map(([, x, z]) => {
    let best = 0, bd = 1e9;
    pot.forEach(([px2, pz2], k) => { const dd = Math.hypot(px2 - x / 1000, pz2 - z / 1000); if (dd < bd) { bd = dd; best = k; } });
    return dol[best];
  });
  const MIN = 0.55;   // km na minuto zamude
  const zamudaPri = (vrstica, s) => {
    // linearno med postajama z zapisom
    let prej = null, nasl = null;
    for (let k = 0; k < sPost.length; k++) {
      if (vrstica[k] == null) continue;
      if (sPost[k] <= s) prej = k;
      if (sPost[k] >= s && nasl === null) nasl = k;
    }
    if (prej === null && nasl === null) return null;
    if (prej === null) return vrstica[nasl];
    if (nasl === null) return vrstica[prej];
    if (sPost[nasl] === sPost[prej]) return vrstica[prej];
    const f = (s - sPost[prej]) / (sPost[nasl] - sPost[prej]);
    return vrstica[prej] + (vrstica[nasl] - vrstica[prej]) * f;
  };
  const zavesa = new THREE.Group();
  const tla = pot.map(([x, z]) => visinaKm(x, z) + 0.12);
  const dniCrte = [];
  for (const [, vrstica] of vr.dnevi) {
    const p = [];
    for (let k = 0; k < pot.length - 1; k++) {
      const a = zamudaPri(vrstica, dol[k]), b = zamudaPri(vrstica, dol[k + 1]);
      if (a == null || b == null) continue;
      p.push(pot[k][0], tla[k] + (a / 60) * MIN, pot[k][1], pot[k + 1][0], tla[k + 1] + (b / 60) * MIN, pot[k + 1][1]);
    }
    dniCrte.push(...p);
  }
  const dniG = new LineSegmentsGeometry().setPositions(dniCrte);
  const dniM = new LineMaterial({ color: '#f2a87e', linewidth: 1.1, transparent: true, opacity: 0.22, depthWrite: false });
  zavesa.add(new LineSegments2(dniG, dniM));
  // mediana po točkah poti in ploskev pod njo
  const med = pot.map((_, k) => {
    const v = vr.dnevi.map(([, r]) => zamudaPri(r, dol[k])).filter((x) => x != null).sort((a, b) => a - b);
    return v.length ? v[Math.floor(v.length / 2)] : 0;
  });
  const medPos = [];
  for (let k = 0; k < pot.length - 1; k++) medPos.push(pot[k][0], tla[k] + med[k] / 60 * MIN, pot[k][1], pot[k + 1][0], tla[k + 1] + med[k + 1] / 60 * MIN, pot[k + 1][1]);
  const medM = new LineMaterial({ color: '#f0934f', linewidth: 3.2, transparent: true, depthWrite: false });
  zavesa.add(new LineSegments2(new LineSegmentsGeometry().setPositions(medPos), medM));
  {
    const ppz = [], ix = [], al = [];
    pot.forEach(([x, z], k) => { ppz.push(x, tla[k], z, x, tla[k] + med[k] / 60 * MIN, z); al.push(0, 1); });
    for (let k = 0; k < pot.length - 1; k++) { const a = k * 2; ix.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
    const zg = new THREE.BufferGeometry();
    zg.setAttribute('position', new THREE.Float32BufferAttribute(ppz, 3));
    zg.setAttribute('aA', new THREE.Float32BufferAttribute(al, 1));
    zg.setIndex(ix);
    const zm = new THREE.ShaderMaterial({
      uniforms: { uVid: { value: 1 } },
      vertexShader: 'attribute float aA; varying float vA; void main(){ vA = aA; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
      fragmentShader: 'uniform float uVid; varying float vA; void main(){ gl_FragColor = vec4(vec3(0.94,0.58,0.31), (0.05 + 0.32 * vA) * uVid); }',
      transparent: true, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending,
    });
    zavesa.add(new THREE.Mesh(zg, zm));
    zavesa.userData.zm = zm;
  }
  // navpične črte pri postajah
  const nav = [];
  sPost.forEach((s, k) => {
    let best = 0;
    dol.forEach((d, i) => { if (Math.abs(d - s) < Math.abs(dol[best] - s)) best = i; });
    nav.push(pot[best][0], tla[best], pot[best][1], pot[best][0], tla[best] + 7.5, pot[best][1]);
  });
  const navM = new LineMaterial({ color: '#c8d3e4', linewidth: 0.8, transparent: true, opacity: 0.35, depthWrite: false, dashed: true, dashSize: 0.3, gapSize: 0.3 });
  const navL = new LineSegments2(new LineSegmentsGeometry().setPositions(nav), navM);
  navL.computeLineDistances();
  zavesa.add(navL);
  zavesa.visible = false;
  scena.add(zavesa);
  const zavesaM = [dniM, medM, navM];

  // ---------- budilka: utripajoči krogi ----------
  const budilka = new THREE.Group();
  const bx = LJ[1] / 1000, bz = LJ[2] / 1000, by = visinaKm(bx, bz) + 0.2;
  const krogi = [];
  for (let k = 0; k < 3; k++) {
    const m = new THREE.Mesh(new THREE.RingGeometry(0.92, 1.0, 64), new THREE.MeshBasicMaterial({ color: '#f0934f', transparent: true, depthWrite: false, side: THREE.DoubleSide }));
    m.rotation.x = -Math.PI / 2;
    m.position.set(bx, by, bz);
    budilka.add(m);
    krogi.push(m);
  }
  scena.add(budilka);

  // ---------- oznake mest ----------
  const plast = document.createElement('div');
  plast.className = 'karta-oznake';
  document.body.appendChild(plast);
  const oznake = meta.mesta.map(([ime, x, z]) => {
    const el = document.createElement('div');
    el.className = 'mesto';
    el.textContent = ime;
    plast.appendChild(el);
    const xx = x / 1000, zz = z / 1000;
    return { el, p: new THREE.Vector3(xx, visinaKm(xx, zz) + 0.3, zz), ime };
  });
  const posebne = [];
  const dodajOznako = (html, x, z, dvig, razred2) => {
    const el = document.createElement('div');
    el.className = 'oznaka3d ' + (razred2 || '');
    el.innerHTML = `<span>${html}</span>`;
    plast.appendChild(el);
    const o2 = { el, p: new THREE.Vector3(x, visinaKm(x, z) + dvig, z) };
    posebne.push(o2);
    return o2;
  };
  const st = vr.stat;
  const konec = vr.postaje[vr.postaje.length - 1];
  const oznVrsta = dodajOznako(`<em>${vr.ime}</em><b>Ljubljana → Maribor · ${st.dni} dni</b>`, konec[1] / 1000, konec[2] / 1000, 8.5, '');
  const oznBud = dodajOznako('<em>budilka</em><b>7.15 → 7.22</b>', bx, bz, 2.2, 'oranzna');

  // ---------- kamera ----------
  const K = [
    { t: 128, p: [4, 430, 270], c: [8, 0, -4], f: 40 },
    { t: 137, p: [-4, 215, 205], c: [6, 0, 0], f: 40 },
    { t: 146, p: [-30, 150, 175], c: [6, 0, 2], f: 40 },
    { t: 157, p: [40, 150, 175], c: [6, 0, 2], f: 40 },
    { t: 168, p: [95, 95, 95], c: [14, 0, -8], f: 40 },
    { t: 177, p: [62, 48, 62], c: [22, 3, -22], f: 40, mir: true },
    { t: 186, p: [4, 26, 40], c: [-20, 0, 4], f: 40 },
    { t: 193, p: [-14, 11, 20], c: [-23.5, 0, 6], f: 40 },
    { t: 200, p: [-19.5, 7, 15.5], c: [-23.6, 0.2, 6.6], f: 40 },
    { t: 206, p: [-23.3, 2.4, 9.2], c: [-23.7, 0.2, 6.8], f: 40 },
  ];
  const kz = zlepek(K.map((k) => ({ t: k.t, v: [...k.p, ...k.c, k.f], mir: k.mir })));
  const v4 = new THREE.Vector4();
  let zadnjaDpr = 0;

  function risi(r, T, cas, okvir) {
    const k = kz(T);
    kamera.position.set(k[0], k[1], k[2]);
    kamera.lookAt(k[3], k[4], k[5]);
    kamera.fov = k[6];
    kamera.near = Math.max(0.02, k[1] * 0.02);
    okvir(kamera);
    kamera.updateProjectionMatrix();
    const w = innerWidth, h = innerHeight;
    for (const m of [...crte, ...zavesaM]) m.resolution.set(w, h);
    const dpr = r.getPixelRatio();
    if (dpr !== zadnjaDpr) { uPike.uDpr.value = dpr; zadnjaDpr = dpr; }
    // razkritje omrežja od Ljubljane navzven
    uRazP.value = lerp(0, 260, smooth(129, 141, T));
    uRazB.value = lerp(0, 260, smooth(134, 146, T));
    // jutro: 6.55 do 8.00 (sekunde od 7.00)
    const tr = T < 146 ? lerp(-300, 0, smooth(138, 146, T)) : T < 168 ? lerp(0, 3600, (T - 146) / 22) : 3600 + (T - 168) * 18;
    postaviVoznje(tr);
    uPike.uVid.value = smooth(139, 145, T) * (1 - 0.55 * okno(T, 169, 173, 182, 186));
    // zavesa
    const zv = okno(T, 168, 173, 184, 188);
    zavesa.visible = zv > 0.001;
    zavesa.scale.y = 1;
    for (const m of zavesaM) m.opacity = m === medM ? zv : m === navM ? zv * 0.35 : zv * 0.22;
    zavesa.userData.zm.uniforms.uVid.value = zv;
    // budilka
    const bv = okno(T, 195, 197.5, 204, 206);
    budilka.visible = bv > 0.001;
    krogi.forEach((m, i) => {
      const f = ((cas * 0.6 + i / 3) % 1);
      m.scale.setScalar(0.3 + f * 3.2);
      m.material.opacity = (1 - f) * 0.8 * bv;
    });
    // oznake
    plast.style.opacity = 1;
    const vidMesta = smooth(140, 146, T) * (1 - smooth(203, 205.5, T));
    for (const o2 of oznake) postaviOznako(o2, vidMesta * (o2.ime === 'Ljubljana' || T < 184 ? 1 : 0.4));
    postaviOznako(oznVrsta, zv);
    postaviOznako(oznBud, bv);
    r.render(scena, kamera);
    const vidUra = okno(T, 144, 147, 168, 171);
    return vidUra > 0 ? { vid: vidUra, oznaka: 'četrtek, 1. 10. 2026', cas: 7 * 3600 + clamp(tr, 0, 3600) } : null;
  }
  function postaviOznako(o2, vid) {
    if (vid <= 0.001) { o2.el.style.opacity = 0; return; }
    v4.set(o2.p.x, o2.p.y, o2.p.z, 1).applyMatrix4(kamera.matrixWorldInverse).applyMatrix4(kamera.projectionMatrix);
    const x = (v4.x / v4.w * 0.5 + 0.5) * innerWidth, y = (-v4.y / v4.w * 0.5 + 0.5) * innerHeight;
    o2.el.style.opacity = v4.w > 0 ? vid.toFixed(3) : 0;
    o2.el.style.transform = `translate3d(${x.toFixed(1)}px, ${y.toFixed(1)}px, 0)`;
  }
  function skrij() { plast.style.opacity = 0; }
  return { risi, skrij, meta };
}
