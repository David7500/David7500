// Postaja: peron, nadstrešek, ura, odhodna tabla, poslopje, luči, klopi.
// Tir 1 leži na osi x (z = 0), peron je južno (z > 0), poslopje za njim.
import * as THREE from 'three';
import { platno, tekstura, normalnaIzVisine, rng, sum2, fbm, zdruzi, M4, M4s, skatla, clamp, lerp } from './orodja.js';

export const PERON = { z0: 1.68, z1: 8.2, y: 0.55, x0: -95, x1: 95 };
export const URA = { x: 0, y: 3.32, z: 3.05, r: 0.40 };
export const TABLA = { x: 5.2, y: 3.38, z: 4.3 };

// ---------- teksture ----------
function teksturaPerona() {
  // 2 m vzdolž × 6,52 m čez: tlakovci 40 cm, bel robnik, rumena črta, vodilna pot
  const W = 512, Hh = 1664;
  const [c, g] = platno(W, Hh);
  const [hc, hg] = platno(W, Hh);
  const n = sum2(21), r = rng(9);
  const pxm = 256;   // pik na meter
  g.fillStyle = '#9b9890'; g.fillRect(0, 0, W, Hh);
  hg.fillStyle = '#808080'; hg.fillRect(0, 0, W, Hh);
  const t = 0.4 * pxm;
  for (let y = 0.32 * pxm; y < Hh; y += t) {
    for (let x = 0; x < W; x += t) {
      const v = 140 + r() * 26 - 13;
      g.fillStyle = `rgb(${v},${v - 3},${v - 9})`;
      g.fillRect(x + 2, y + 2, t - 4, t - 4);
      hg.fillStyle = '#9a9a9a';
      hg.fillRect(x + 3, y + 3, t - 6, t - 6);
    }
  }
  // robnik (0,32 m), rumena črta pri 0,85 m, vodilna rebra pri 1,1 m
  g.fillStyle = '#d9d6cd'; g.fillRect(0, 0, W, 0.32 * pxm);
  hg.fillStyle = '#b0b0b0'; hg.fillRect(0, 0, W, 0.32 * pxm);
  g.fillStyle = '#e3b419'; g.fillRect(0, 0.82 * pxm, W, 0.10 * pxm);
  g.fillStyle = '#cfcbc0'; g.fillRect(0, 1.02 * pxm, W, 0.4 * pxm);
  for (let x = 0; x < W; x += 18) {
    hg.fillStyle = '#c8c8c8'; hg.fillRect(x + 3, 1.04 * pxm, 9, 0.36 * pxm);
    g.fillStyle = '#e2ded3'; g.fillRect(x + 3, 1.04 * pxm, 9, 0.36 * pxm);
  }
  // umazanija in madeži
  const img = g.getImageData(0, 0, W, Hh);
  for (let y = 0; y < Hh; y++) {
    for (let x = 0; x < W; x++) {
      const i = (y * W + x) * 4;
      const m = 0.9 + 0.12 * fbm(n, x / 60, y / 60, 4) + 0.04 * (r() - 0.5);
      img.data[i] *= m; img.data[i + 1] *= m; img.data[i + 2] *= m;
    }
  }
  g.putImageData(img, 0, 0);
  const bar = tekstura(c, { ponavljaj: true });
  const nor = tekstura(normalnaIzVisine(hc, 2.2), { srgb: false, ponavljaj: true });
  return { bar, nor };
}

function teksturaUre() {
  const S = 1024;
  const [c, g] = platno(S, S);
  const R = S / 2;
  const grad = g.createRadialGradient(R, R, 0, R, R, R);
  grad.addColorStop(0, '#fbfbf8'); grad.addColorStop(0.85, '#f1f0ea'); grad.addColorStop(1, '#d9d7cf');
  g.fillStyle = grad;
  g.beginPath(); g.arc(R, R, R, 0, Math.PI * 2); g.fill();
  g.translate(R, R);
  for (let i = 0; i < 60; i++) {
    g.save();
    g.rotate((i / 60) * Math.PI * 2);
    g.fillStyle = '#121212';
    if (i % 5 === 0) g.fillRect(-R * 0.034, -R * 0.94, R * 0.068, R * 0.24);
    else g.fillRect(-R * 0.011, -R * 0.94, R * 0.022, R * 0.075);
    g.restore();
  }
  return tekstura(c, { aniz: 16 });
}

// Odhodna tabla: LED pike, jantarne na črnem. Besedilo se nariše znova le,
// ko se spremeni zamuda.
function ustvariTablo() {
  const W = 1024, Hh = 300;
  const [c, g] = platno(W, Hh);
  const [t, tg] = platno(W, Hh);
  const tex = tekstura(c, { aniz: 8 });
  let zadnje = null;
  function narisi(zamuda, ura = '07:42') {
    const kljuc = zamuda + ura;
    if (kljuc === zadnje) return;
    zadnje = kljuc;
    tg.fillStyle = '#000'; tg.fillRect(0, 0, W, Hh);
    tg.fillStyle = '#fff';
    tg.textBaseline = 'middle';
    tg.font = '600 46px "IBM Plex Mono", monospace';
    tg.fillText('ODHOD', 36, 52); tg.fillText('SMER', 270, 52); tg.fillText('TIR', 880, 52);
    tg.font = '600 92px "IBM Plex Mono", monospace';
    tg.fillText(ura, 30, 150);
    tg.fillText('V šolo', 300, 150);
    tg.fillText('1', 905, 150);
    tg.font = '600 62px "IBM Plex Mono", monospace';
    if (zamuda > 0) tg.fillText(`zamuda ${zamuda} min`, 300, 245);
    const src = tg.getImageData(0, 0, W, Hh).data;
    g.fillStyle = '#050403'; g.fillRect(0, 0, W, Hh);
    const k = 6;
    for (let y = 0; y < Hh; y += k) {
      for (let x = 0; x < W; x += k) {
        const v = src[((y + 3) * W + x + 3) * 4];
        const vrsta = y > 200 ? '#ff7a1a' : '#ffb21f';
        g.fillStyle = v > 100 ? vrsta : '#140b02';
        g.beginPath(); g.arc(x + 3, y + 3, v > 100 ? 2.5 : 1.5, 0, Math.PI * 2); g.fill();
      }
    }
    tex.needsUpdate = true;
  }
  narisi(0);
  return { tex, narisi };
}

function teksturaFasade(sirina, nadstropja, okna, opts = {}) {
  // fasada v slogu južne železnice: pastelni omet, bele obrobe, zeleno-rjava okna
  const pxm = 48;
  const W = Math.round(sirina * pxm), Hh = Math.round((nadstropja * 3.6 + 1.0) * pxm);
  const [c, g] = platno(W, Hh);
  const [e, eg] = platno(W, Hh);
  const r = rng(opts.seme || 4), n = sum2(opts.seme || 4);
  g.fillStyle = opts.omet || '#e6d6b4'; g.fillRect(0, 0, W, Hh);
  eg.fillStyle = '#000'; eg.fillRect(0, 0, W, Hh);
  // podstavek in venci
  g.fillStyle = opts.podstavek || '#b7ab94'; g.fillRect(0, Hh - 0.7 * pxm, W, 0.7 * pxm);
  for (let k = 1; k < nadstropja; k++) {
    const y = Hh - (0.7 + k * 3.6) * pxm;
    g.fillStyle = '#f2ecdf'; g.fillRect(0, y - 6, W, 12);
  }
  g.fillStyle = '#f4efe4'; g.fillRect(0, 0, W, 0.35 * pxm);
  const razmik = sirina / okna;
  for (let k = 0; k < nadstropja; k++) {
    for (let i = 0; i < okna; i++) {
      const cx = (i + 0.5) * razmik * pxm;
      const yb = Hh - (0.7 + k * 3.6 + 0.9) * pxm;
      const w = 1.15 * pxm, h = (k === 0 && opts.loki ? 2.1 : 1.6) * pxm;
      const vrata = k === 0 && opts.vrata && opts.vrata.includes(i);
      const hh = vrata ? 2.6 * pxm : h;
      const yy = vrata ? Hh - 0.7 * pxm - hh : yb - h;
      g.fillStyle = '#f6f2e8';
      g.fillRect(cx - w / 2 - 7, yy - 7, w + 14, hh + 14);
      if (k === 0 && opts.loki) { g.beginPath(); g.arc(cx, yy, w / 2 + 7, Math.PI, 0); g.fill(); }
      g.fillStyle = vrata ? '#3d4a3a' : '#283035';
      g.fillRect(cx - w / 2, yy, w, hh);
      if (k === 0 && opts.loki) { g.beginPath(); g.arc(cx, yy, w / 2, Math.PI, 0); g.fill(); }
      if (!vrata) {
        g.fillStyle = '#e9e4d8';
        g.fillRect(cx - 2, yy, 4, hh);
        g.fillRect(cx - w / 2, yy + hh * 0.38, w, 4);
        // ponoči nekatera okna svetijo
        if (r() < (opts.svetijo ?? 0.35)) {
          eg.fillStyle = `rgb(${200 + r() * 55},${150 + r() * 50},${80 + r() * 40})`;
          eg.fillRect(cx - w / 2 + 3, yy + 3, w - 6, hh - 6);
        }
      }
    }
  }
  const img = g.getImageData(0, 0, W, Hh);
  for (let y = 0; y < Hh; y++) {
    for (let x = 0; x < W; x++) {
      const i = (y * W + x) * 4;
      const m = 0.93 + 0.09 * fbm(n, x / 40, y / 40, 3) - 0.06 * Math.max(0, (y - Hh * 0.8) / (Hh * 0.2)) * 0;
      img.data[i] *= m; img.data[i + 1] *= m; img.data[i + 2] *= m;
    }
  }
  g.putImageData(img, 0, 0);
  return { bar: tekstura(c), emis: tekstura(e) };
}

export function teksturaStrehe(barva = [150, 66, 44]) {
  const W = 256, Hh = 256;
  const [c, g] = platno(W, Hh);
  const [h, hg] = platno(W, Hh);
  const r = rng(13);
  const vr = 32, st = 24;
  for (let y = 0; y < Hh; y += vr) {
    const zam = (y / vr) % 2 ? st / 2 : 0;
    for (let x = -st; x < W + st; x += st) {
      const v = 0.82 + r() * 0.3;
      g.fillStyle = `rgb(${barva[0] * v | 0},${barva[1] * v | 0},${barva[2] * v | 0})`;
      g.fillRect(x + zam, y, st - 1, vr);
      const gr = hg.createLinearGradient(0, y, 0, y + vr);
      gr.addColorStop(0, '#202020'); gr.addColorStop(1, '#d0d0d0');
      hg.fillStyle = gr; hg.fillRect(x + zam, y, st - 1, vr);
      hg.fillStyle = '#404040'; hg.fillRect(x + zam + st - 2, y, 2, vr);
    }
  }
  return { bar: tekstura(c, { ponavljaj: true }), nor: tekstura(normalnaIzVisine(h, 2.5), { srgb: false, ponavljaj: true }) };
}

// Šotorasta streha nad pravokotnikom w × d (sleme vzdolž daljše stranice),
// višina h; UV v metrih vzdolž kapa in po strmini.
export function strehaGeo(w, d, h, previs = 0.5) {
  let W = w / 2 + previs, D = d / 2 + previs;
  const obrni = D > W;
  if (obrni) [W, D] = [D, W];
  const k = D, f = Math.hypot(k, h) / k;
  const r0 = [-W + k, h, 0], r1 = [W - k, h, 0];
  const ploskve = [
    [[W, 0, -D], [-W, 0, -D], r0, r1],
    [[-W, 0, D], [W, 0, D], r1, r0],
    [[-W, 0, -D], [-W, 0, D], r0],
    [[W, 0, D], [W, 0, -D], r1],
  ];
  const pos = [], uv = [];
  const uvT = (p, i) => (i < 2 ? [p[0], (D - Math.abs(p[2])) * f] : [p[2], (W - Math.abs(p[0])) * f]);
  ploskve.forEach((P, i) => {
    const tri = P.length === 4 ? [[0, 1, 2], [0, 2, 3]] : [[0, 1, 2]];
    for (const t of tri) for (const j of t) { pos.push(...P[j]); uv.push(...uvT(P[j], i)); }
  });
  if (obrni) for (let i = 0; i < pos.length; i += 3) { const x = pos[i]; pos[i] = -pos[i + 2]; pos[i + 2] = x; }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.computeVertexNormals();
  return g;
}

// ---------- ura ----------
function zgradiUro() {
  const sk = new THREE.Group();
  const r = URA.r;
  const ohisje = new THREE.MeshStandardMaterial({ color: '#2a2d31', roughness: 0.38, metalness: 0.6 });
  const obroc = new THREE.Mesh(new THREE.CylinderGeometry(r + 0.04, r + 0.04, 0.17, 64, 1, true), ohisje);
  obroc.rotation.z = Math.PI / 2;
  const rob = new THREE.Mesh(new THREE.TorusGeometry(r + 0.025, 0.02, 12, 64), ohisje);
  const rob2 = rob.clone();
  rob.rotation.y = Math.PI / 2; rob.position.x = 0.085;
  rob2.rotation.y = Math.PI / 2; rob2.position.x = -0.085;
  sk.add(obroc, rob, rob2);
  const tex = teksturaUre();
  const obraz = new THREE.MeshStandardMaterial({ map: tex, emissiveMap: tex, emissive: '#fff8ea', emissiveIntensity: 0.35, roughness: 0.6 });
  const kazalci = [];
  const crna = new THREE.MeshStandardMaterial({ color: '#0e0e0e', roughness: 0.5 });
  const rdeca = new THREE.MeshStandardMaterial({ color: '#c81e14', roughness: 0.45, emissive: '#3a0500' });
  const senca = new THREE.MeshBasicMaterial({ color: '#000', transparent: true, opacity: 0.16, depthWrite: false });
  const kazalec = (dol, sirA, sirB, rep = 0) => {
    const s = new THREE.Shape();
    s.moveTo(-sirA / 2, -rep); s.lineTo(sirA / 2, -rep); s.lineTo(sirB / 2, dol); s.lineTo(-sirB / 2, dol); s.closePath();
    return new THREE.ExtrudeGeometry(s, { depth: 0.004, bevelEnabled: false });
  };
  const sekundni = () => {
    const s = new THREE.Shape();
    s.moveTo(-0.0035, -0.11 * r / 0.4); s.lineTo(0.0035, -0.11 * r / 0.4); s.lineTo(0.002, r * 0.86); s.lineTo(-0.002, r * 0.86); s.closePath();
    const g = new THREE.ExtrudeGeometry(s, { depth: 0.003, bevelEnabled: false });
    const k = new THREE.CylinderGeometry(0.022, 0.022, 0.003, 24);
    k.rotateX(Math.PI / 2); k.translate(0, -0.085 * r / 0.4, 0.0015);
    return zdruzi([[g, '#c81e14'], [k, '#c81e14']]);
  };
  for (const stran of [1, -1]) {
    const f = new THREE.Group();
    const disk = new THREE.Mesh(new THREE.CircleGeometry(r, 72), obraz);
    f.add(disk);
    const ure = new THREE.Mesh(kazalec(r * 0.64, 0.036, 0.026, r * 0.16), crna);
    const min = new THREE.Mesh(kazalec(r * 0.9, 0.028, 0.017, r * 0.18), crna);
    const sek = new THREE.Mesh(sekundni(), new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.45, emissive: '#2a0400' }));
    ure.position.z = 0.006; min.position.z = 0.011; sek.position.z = 0.016;
    // mehke sence kazalcev na številčnici (globina pri bližnjem posnetku)
    const sU = new THREE.Mesh(ure.geometry, senca), sM = new THREE.Mesh(min.geometry, senca), sS = new THREE.Mesh(sek.geometry, senca);
    for (const s of [sU, sM, sS]) { s.position.set(0.006, -0.008, 0.0015); s.scale.set(1.04, 1.02, 0.2); }
    const piko = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.006, 16), crna);
    piko.rotation.x = Math.PI / 2; piko.position.z = 0.02;
    f.add(sU, sM, sS, ure, min, sek, piko);
    // steklo: le odsev
    const steklo = new THREE.Mesh(new THREE.CircleGeometry(r + 0.005, 64), new THREE.MeshPhysicalMaterial({
      color: '#ffffff', transparent: true, opacity: 0.08, roughness: 0.05, metalness: 0, clearcoat: 1, depthWrite: false,
    }));
    steklo.position.z = 0.03;
    f.add(steklo);
    f.rotation.y = stran > 0 ? -Math.PI / 2 : Math.PI / 2;
    f.position.x = stran * -0.07;
    sk.add(f);
    kazalci.push({ ure, min, sek, sU, sM, sS });
  }
  // nosilec iz nadstreška
  const nos = new THREE.Mesh(zdruzi([
    [new THREE.CylinderGeometry(0.025, 0.025, 0.55, 10), '#2a2d31', M4(0, r + 0.32, 0)],
    [skatla(0.06, 0.06, 0.3, 0.01), '#2a2d31', M4(0, r + 0.6, 0)],
  ]), new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.4, metalness: 0.6 }));
  sk.add(nos);
  sk.position.set(URA.x, URA.y, URA.z);
  sk.traverse((o) => { if (o.isMesh && o.material !== senca) o.castShadow = true; });
  // čas v sekundah od polnoči; sekundni kazalec se ustavi na vrhu (švicarski
  // posnemki ur: 58,5 s kroži, nato počaka na minutni impulz)
  function nastavi(sek) {
    const h = Math.floor(sek / 3600) % 12, m = Math.floor(sek / 60) % 60, s = sek % 60;
    const kS = s < 58.5 ? (s / 58.5) * Math.PI * 2 : 0;
    const kM = (m / 60) * Math.PI * 2;
    const kH = ((h + m / 60) / 12) * Math.PI * 2;
    for (const k of kazalci) {
      k.ure.rotation.z = -kH; k.min.rotation.z = -kM; k.sek.rotation.z = -kS;
      k.sU.rotation.z = -kH; k.sM.rotation.z = -kM; k.sS.rotation.z = -kS;
    }
  }
  return { skupina: sk, nastavi, obraz };
}

// ---------- dijak ----------
// Stiliziran, brez obraza, 1,75 m: kavbojke, jopa s kapuco, oranžen
// nahrbtnik (barva znaka). Sklepi v kolkih, kolenih, gležnjih, ramah in
// komolcih, da hodi in sedi; gleda v smer +x, stopala na y = 0.
// Postava »močan« (izbral David med tremi, 5. 10. 2026): prsi = polovična
// širina prsnega koša, globina = sploščenost trupa, nad/pod = polmera nadlakti
// in podlakti, trap = trapezasti mišici ob vratu, kolk = razmik kolkov.
export const POSTAVA = { prsi: 0.199, pas: 0.153, globina: 0.69, nad: 0.062, pod: 0.049, vrat: 0.054, stegno: 0.079, meca: 0.058, trap: 0.014, kolk: 0.095 };
// Ud kot zožena kapsula od 0 navzdol do -dol: polmer r0 zgoraj, r1 spodaj,
// rS je mišica (biceps, meča) pri deležu dolžine tS.
function ud(r0, r1, dol, seg = 10, rS = 0, tS = 0.4) {
  const t = [];
  for (let i = 0; i <= 6; i++) { const a = (i / 6) * Math.PI / 2; t.push(new THREE.Vector2(r1 * Math.sin(a), -dol - r1 * Math.cos(a))); }
  if (rS) {
    for (const [f, r] of [[0.8, lerp(r1, rS, 0.55)], [tS + 0.12, rS * 0.985], [tS, rS], [tS * 0.45, lerp(r0, rS, 0.7)]]) t.push(new THREE.Vector2(r, -dol * f));
  }
  for (let i = 0; i <= 6; i++) { const a = (i / 6) * Math.PI / 2; t.push(new THREE.Vector2(r0 * Math.cos(a), r0 * Math.sin(a))); }
  return new THREE.LatheGeometry(t, seg);
}
// Zaslon prenosnika: urejevalnik s kodo (temna tema), dijak razvija kajros.
function zaslonKoda() {
  const [c, g] = platno(512, 320);
  g.fillStyle = '#1d2127'; g.fillRect(0, 0, 512, 320);
  g.fillStyle = '#252a31'; g.fillRect(0, 0, 512, 22); g.fillRect(0, 22, 34, 298);
  g.fillStyle = '#f0934f'; g.fillRect(40, 4, 90, 14);
  const V = [
    [['#c678dd', 'def '], ['#61afef', 'zamuda'], ['#abb2bf', '(vlak, postaja):']],
    [['#7f848e', '    # koliko vlak res zamuja']],
    [['#abb2bf', '    red = urnik[vlak][postaja]']],
    [['#abb2bf', '    res = meritve.zadnja(vlak)']],
    [['#c678dd', '    return '], ['#abb2bf', 'res - red']],
    [],
    [['#c678dd', 'for '], ['#abb2bf', 'vlak '], ['#c678dd', 'in '], ['#61afef', 'vlaki_danes'], ['#abb2bf', '():']],
    [['#abb2bf', '    z = '], ['#61afef', 'zamuda'], ['#abb2bf', '(vlak, '], ['#98c379', '"šola"'], ['#abb2bf', ')']],
    [['#61afef', '    zapisi'], ['#abb2bf', '(vlak, z)']],
    [],
    [['#7f848e', '# +13 min']],
  ];
  g.font = '500 17px "IBM Plex Mono", monospace';
  g.textBaseline = 'middle';
  V.forEach((vr, i) => {
    const y = 40 + i * 25;
    g.fillStyle = '#5c6370'; g.fillText(String(i + 1).padStart(2, ' '), 6, y);
    let x = 44;
    for (const [b, t] of vr) { g.fillStyle = b; g.fillText(t, x, y); x += g.measureText(t).width; }
  });
  g.fillStyle = '#abb2bf'; g.fillRect(44 + 11 * 10.2, 40 + 10 * 25 - 9, 2, 18);
  return tekstura(c, { aniz: 4 });
}

export function zgradiDijaka(P = POSTAVA) {
  const sk = new THREE.Group();
  const mat = (c, r = 0.75) => new THREE.MeshStandardMaterial({ color: c, roughness: r });
  const kavbojke = mat('#2c3850'), jopa = mat('#4a5461', 0.85), koza = mat('#dcae92', 0.62), lasje = mat('#3a2a1e', 0.8);
  const nahrbtnik = mat('#f0934f', 0.7), pas = mat('#b9622c', 0.7), copati = mat('#e6e4df', 0.6), podplat = mat('#9c9890', 0.7);
  const telo = new THREE.Group();
  sk.add(telo);
  const KOLK = 0.89;
  const V2 = (t) => t.map(([r, y]) => new THREE.Vector2(r, y));
  // boki in trup (jopa), prerez sploščen v globino
  const boki = new THREE.Mesh(new THREE.LatheGeometry(V2([[0, 0.78], [P.pas - 0.03, 0.79], [P.pas - 0.012, 0.84], [P.pas - 0.014, 0.9], [0, 0.92]]), 18), kavbojke);
  boki.scale.set(0.66, 1, 1);
  const trup = new THREE.Mesh(new THREE.LatheGeometry(V2([[0, 0.835], [P.pas + 0.002, 0.84], [P.pas + 0.009, 0.9], [P.pas + 0.006, 0.97], [P.pas, 1.05],
    [lerp(P.pas, P.prsi, 0.45), 1.15], [P.prsi - 0.008, 1.26], [P.prsi, 1.34], [P.prsi - 0.02 + P.trap * 0.6, 1.41],
    [0.11 + P.trap, 1.455], [0.05 + P.trap * 0.5, 1.475], [0, 1.476]]), 22), jopa);
  trup.scale.set(P.globina, 1, 1);
  // kapuca nagubana za vratom: od zadaj pokrije tudi vrat
  const kapuca = new THREE.Mesh((() => { const g = new THREE.TorusGeometry(0.088 + P.trap * 0.8, 0.044 + P.trap * 0.3, 8, 14, Math.PI); g.rotateX(Math.PI / 2); g.rotateY(-Math.PI / 2); g.scale(1, 1.05, 1.05); return g; })(), jopa);
  kapuca.position.set(-0.02, 1.468, 0);
  const vrat = new THREE.Mesh(new THREE.CylinderGeometry(P.vrat, P.vrat * 1.12, 0.1, 14), koza);
  vrat.position.y = 1.5;
  const glava = new THREE.Group();
  glava.position.y = 1.54;
  const g = new THREE.Mesh(new THREE.SphereGeometry(0.1, 24, 18), koza);
  g.scale.set(0.92, 1.1, 0.84); g.position.set(0.012, 0.085, 0);
  const l = new THREE.Mesh(new THREE.SphereGeometry(0.106, 24, 16, 0, Math.PI * 2, 0, Math.PI * 0.56), lasje);
  l.scale.set(0.95, 1.08, 0.9); l.position.set(0.0, 0.1, 0); l.rotation.z = 0.42;
  // lasje zadaj do tilnika: od zadaj in v temi se ne vidi koža glave
  const lZ = new THREE.Mesh(new THREE.SphereGeometry(0.104, 20, 14, -Math.PI / 2, Math.PI, 0, Math.PI * 0.74), lasje);
  lZ.scale.set(0.95, 1.1, 0.89); lZ.position.set(0.006, 0.088, 0);
  // ušesi in šiška: obris glave od strani in od zadaj ni le jajce
  for (const z of [-1, 1]) {
    const u = new THREE.Mesh(new THREE.SphereGeometry(0.022, 10, 8), koza);
    u.scale.set(0.9, 1.5, 0.55); u.position.set(-0.004, 0.075, z * 0.083);
    glava.add(u);
  }
  const sis = new THREE.Mesh(new THREE.SphereGeometry(0.06, 14, 10, 0, Math.PI * 2, 0, Math.PI * 0.5), lasje);
  sis.scale.set(0.9, 0.55, 1.3); sis.position.set(0.055, 0.15, 0); sis.rotation.z = -0.5;
  glava.add(g, l, lZ, sis);
  // nahrbtnik z naramnicama; na klopi ga odloži poleg sebe
  const xHrbta = P.prsi * P.globina;
  const nahr = new THREE.Group();
  const nahrT = new THREE.Mesh(skatla(0.15, 0.4, 0.29, 0.05), nahrbtnik);
  const zep = new THREE.Mesh(skatla(0.05, 0.16, 0.22, 0.03), pas);
  zep.position.set(-0.085, -0.09, 0);
  nahr.add(nahrT, zep);
  const nahrX = -(xHrbta + 0.07);
  nahr.position.set(nahrX, 1.17, 0);
  telo.add(boki, trup, kapuca, vrat, glava, nahr);
  const naramnice = [];
  for (const z of [-1, 1]) {
    const n = new THREE.Mesh(skatla(0.014, 0.3, 0.042, 0.006), pas);
    n.position.set(xHrbta - 0.006, 1.2, z * (0.085 + P.trap)); n.rotation.z = 0.08;
    const r = new THREE.Mesh(skatla(xHrbta * 2 + 0.02, 0.014, 0.042, 0.006), pas);
    r.position.set(0.0, 1.43 + P.trap * 0.5, z * (0.09 + P.trap));
    telo.add(n, r);
    naramnice.push(n, r);
  }
  // noge
  const noge = [];
  for (const s of [-1, 1]) {
    const kolk = new THREE.Group();
    kolk.position.set(0, KOLK, s * P.kolk);
    kolk.add(new THREE.Mesh(ud(P.stegno, P.stegno * 0.72, 0.43, 12, P.stegno * 1.03, 0.3), kavbojke));
    const koleno = new THREE.Group(); koleno.position.y = -0.43;
    koleno.add(new THREE.Mesh(ud(P.meca * 0.9, P.meca * 0.66, 0.415, 12, P.meca, 0.3), kavbojke));
    const gleznjar = new THREE.Group(); gleznjar.position.y = -0.415;
    const cop = new THREE.Mesh(skatla(0.25, 0.07, 0.094, 0.03), copati); cop.position.set(0.055, -0.03, 0);
    const pod = new THREE.Mesh(skatla(0.255, 0.022, 0.098, 0.01), podplat); pod.position.set(0.055, -0.064, 0);
    gleznjar.add(cop, pod);
    koleno.add(gleznjar);
    kolk.add(koleno);
    telo.add(kolk);
    noge.push({ kolk, koleno, gleznjar });
  }
  // roki: rama (odmik od telesa) -> zamah (z deltoidom) -> komolec
  const roki = [];
  const odmik = 0.07 + (P.nad - 0.047) * 1.5;
  for (const s of [-1, 1]) {
    const rama = new THREE.Group();
    rama.position.set(0, 1.375, s * (P.prsi + P.nad - 0.024));
    rama.rotation.x = -s * odmik;
    const zamah = new THREE.Group();
    // vrh nadlakti je deltoid: debelejša kapica, ki se zlije z ramo
    zamah.add(new THREE.Mesh(ud(P.nad * 1.14, P.nad * 0.78, 0.27, 12, P.nad * 1.06, 0.45), jopa));
    const komolec = new THREE.Group(); komolec.position.y = -0.27;
    komolec.add(new THREE.Mesh(ud(P.pod, P.pod * 0.76, 0.23, 12, P.pod * 1.05, 0.25), jopa));
    const dlan = new THREE.Mesh(new THREE.SphereGeometry(0.045, 12, 10), koza);
    dlan.scale.set(0.42, 1.75, 0.88); dlan.position.set(0.004, -0.305, 0);
    komolec.add(dlan);
    zamah.add(komolec);
    rama.add(zamah);
    telo.add(rama);
    roki.push({ rama, zamah, komolec, dlan });
  }
  const tel = new THREE.Mesh(skatla(0.009, 0.15, 0.072, 0.008), new THREE.MeshStandardMaterial({ color: '#111', roughness: 0.3, emissive: '#5c7da8', emissiveIntensity: 0.6 }));
  tel.position.set(0.035, -0.32, 0); tel.rotation.z = -0.2;
  roki[1].komolec.add(tel);
  // prenosnik za nočni prizor: podnožje na stegnih, pokrov odprt nazaj
  const alu = new THREE.MeshStandardMaterial({ color: '#9aa0a6', roughness: 0.35, metalness: 0.6 });
  const pren = new THREE.Group();
  const spodaj = new THREE.Mesh(skatla(0.24, 0.018, 0.33, 0.006), alu);
  const pokr = new THREE.Group();
  const hrbet = new THREE.Mesh(skatla(0.012, 0.21, 0.33, 0.005), alu);
  hrbet.position.set(0.006, 0.105, 0);
  const zaslon = new THREE.Mesh(new THREE.PlaneGeometry(0.31, 0.19), new THREE.MeshStandardMaterial({ color: '#000', emissive: '#ffffff', emissiveMap: zaslonKoda(), emissiveIntensity: 1.15 }));
  zaslon.rotation.y = -Math.PI / 2;
  zaslon.position.set(-0.002, 0.108, 0);
  pokr.add(hrbet, zaslon);
  pokr.position.set(0.12, 0.009, 0);
  pokr.rotation.z = -0.3;
  pren.add(spodaj, pokr);
  pren.visible = false;
  telo.add(pren);
  sk.traverse((o) => { if (o.isMesh) o.castShadow = true; });
  // korak: prehojena pot v metrih (en cikel = dva koraka = 1,4 m);
  // gleda: zasuk glave; telefon, sedi: 0..1
  function poza(korak = 0, gleda = 0, telefon = 1, sedi = 0) {
    const f = (korak / 1.4) * Math.PI * 2;
    const hodi = korak > 0 ? 1 - sedi : 0;
    noge.forEach((n, i) => {
      const fi = f + (i ? Math.PI : 0);
      const kolk = 0.4 * Math.sin(fi) * hodi;
      const koleno = -(0.06 + 0.8 * Math.max(0, Math.cos(fi)) ** 2) * hodi;
      n.kolk.rotation.z = kolk * (1 - sedi) + sedi * 1.48;
      n.koleno.rotation.z = koleno * (1 - sedi) - sedi * 1.5;
      n.gleznjar.rotation.z = -(n.kolk.rotation.z + n.koleno.rotation.z) * (hodi ? 0.75 : 1);
    });
    roki.forEach((r, i) => {
      const fi = f + (i ? 0 : Math.PI);
      const tl = i === 1 ? telefon : 0;
      const zamah = 0.32 * Math.sin(fi) * hodi;
      // sede: dlani na tipkovnici prenosnika
      r.zamah.rotation.z = (zamah * (1 - tl) + tl * 0.25) * (1 - sedi) + sedi * 0.25;
      r.komolec.rotation.z = ((0.18 + 0.2 * Math.max(0, Math.sin(fi)) * hodi) * (1 - tl) + tl * 1.75) * (1 - sedi) + sedi * 0.78;
      r.rama.rotation.x = -(i ? 1 : -1) * (odmik - tl * 0.1);
    });
    tel.visible = sedi < 0.5;
    pren.visible = sedi > 0.5;
    for (const n of naramnice) n.visible = sedi < 0.5;
    if (sedi > 0.5) { nahr.position.set(-0.04, 1.035, -0.52); nahr.rotation.set(0, 0.35, 0); }
    else { nahr.position.set(nahrX, 1.17, 0); nahr.rotation.set(0, 0, 0); }
    // sedi: kolki na sedežu klopi (0,475 m + debelina stegna)
    telo.position.y = sedi * -0.36 + (hodi ? -0.018 * Math.abs(Math.sin(f)) : 0);
    telo.rotation.y = hodi * 0.05 * Math.sin(f);
    pren.position.set(0.27, KOLK + 0.009 + P.stegno, 0);
    glava.rotation.y = gleda;
    glava.rotation.z = -0.42 * telefon * (1 - sedi) - sedi * 0.32;
  }
  poza(0);
  return { skupina: sk, poza, tel, zaslon };
}

// ---------- postaja ----------
export function zgradiPostajo() {
  const sk = new THREE.Group();
  const r = rng(17);
  // peron: zgornja plošča in sprednji zid
  const pt = teksturaPerona();
  pt.bar.repeat.set((PERON.x1 - PERON.x0) / 2, 1);
  pt.nor.repeat.copy(pt.bar.repeat);
  const sir = PERON.z1 - PERON.z0, dol = PERON.x1 - PERON.x0;
  const vrhG = new THREE.PlaneGeometry(dol, sir);
  vrhG.rotateX(-Math.PI / 2);
  // u vzdolž x, v čez (0 ob robu)
  const uv = vrhG.attributes.uv;
  for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i), 1 - uv.getY(i));
  const vrh = new THREE.Mesh(vrhG, new THREE.MeshStandardMaterial({ map: pt.bar, normalMap: pt.nor, roughness: 0.88 }));
  vrh.material.map.wrapT = THREE.ClampToEdgeWrapping;
  vrh.position.set((PERON.x0 + PERON.x1) / 2, PERON.y, (PERON.z0 + PERON.z1) / 2);
  vrh.receiveShadow = true;
  sk.add(vrh);
  const beton = new THREE.MeshStandardMaterial({ color: '#8f8b83', roughness: 0.92 });
  const zid = new THREE.Mesh(new THREE.BoxGeometry(dol, 1.45, sir), beton);
  zid.position.set((PERON.x0 + PERON.x1) / 2, PERON.y - 0.75, (PERON.z0 + PERON.z1) / 2);
  zid.receiveShadow = true;
  sk.add(zid);
  // previs robnika nad tirom
  // vrh robnika 1 cm pod ploščo perona: ista višina bi migljala
  const robnik = new THREE.Mesh(new THREE.BoxGeometry(dol, 0.12, 0.34), new THREE.MeshStandardMaterial({ color: '#cfccc4', roughness: 0.8 }));
  robnik.position.set((PERON.x0 + PERON.x1) / 2, PERON.y - 0.07, PERON.z0 + 0.13);
  robnik.receiveShadow = true;
  sk.add(robnik);
  // klančina na koncih
  for (const s of [-1, 1]) {
    const k = new THREE.Mesh(new THREE.BoxGeometry(8, 0.1, sir), beton);
    k.position.set(s * (dol / 2 + 3.6), PERON.y - 0.32, (PERON.z0 + PERON.z1) / 2);
    k.rotation.z = s * 0.07;
    k.receiveShadow = true;
    sk.add(k);
  }

  // nadstrešek: stebri, plošča, svetlobna trakova
  const NX0 = -31, NX1 = 31, NZ0 = 2.35, NZ1 = 7.4, NY = PERON.y + 3.55;
  const kovina = new THREE.MeshStandardMaterial({ color: '#3a3f45', roughness: 0.5, metalness: 0.55 });
  const plosca = new THREE.Mesh(skatla(NX1 - NX0, 0.28, NZ1 - NZ0, 0.03), new THREE.MeshStandardMaterial({ color: '#d4d2cc', roughness: 0.7 }));
  plosca.position.set(0, NY + 0.14, (NZ0 + NZ1) / 2);
  plosca.castShadow = true; plosca.receiveShadow = true;
  const obroba = new THREE.Mesh(skatla(NX1 - NX0 + 0.1, 0.34, 0.08, 0.02), kovina);
  obroba.position.set(0, NY + 0.15, NZ0);
  sk.add(plosca, obroba);
  const stebri = new THREE.InstancedMesh(skatla(0.2, NY - PERON.y, 0.2, 0.02), kovina, 9);
  const m4 = new THREE.Matrix4();
  for (let i = 0; i < 9; i++) {
    m4.makeTranslation(NX0 + 3 + i * 7, PERON.y + (NY - PERON.y) / 2, 6.3);
    stebri.setMatrixAt(i, m4);
  }
  stebri.castShadow = true;
  sk.add(stebri);
  const lucMat = new THREE.MeshStandardMaterial({ color: '#fff', emissive: '#fff3dc', emissiveIntensity: 0.6 });
  for (const z of [3.1, 6.0]) {
    const tr = new THREE.Mesh(new THREE.BoxGeometry(NX1 - NX0 - 2, 0.04, 0.16), lucMat);
    tr.position.set(0, NY - 0.02, z);
    sk.add(tr);
  }

  // ura in tabla
  const ura = zgradiUro();
  sk.add(ura.skupina);
  const tabla = ustvariTablo();
  const tablaSk = new THREE.Group();
  const ohis = new THREE.Mesh(skatla(2.3, 0.72, 0.16, 0.03), new THREE.MeshStandardMaterial({ color: '#202327', roughness: 0.45, metalness: 0.4 }));
  const zasl = new THREE.MeshStandardMaterial({ color: '#000', emissive: '#ffffff', emissiveMap: tabla.tex, emissiveIntensity: 1.5, roughness: 0.25, map: tabla.tex });
  for (const s of [1, -1]) {
    const z = new THREE.Mesh(new THREE.PlaneGeometry(2.14, 0.6), zasl);
    z.position.z = s * 0.081;
    if (s < 0) z.rotation.y = Math.PI;
    tablaSk.add(z);
  }
  const drogT = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.3, 8), kovina);
  for (const dx of [-0.8, 0.8]) { const d = drogT.clone(); d.position.set(dx, 0.5, 0); tablaSk.add(d); }
  tablaSk.add(ohis);
  tablaSk.rotation.y = -Math.PI / 2;
  tablaSk.position.set(TABLA.x, TABLA.y, TABLA.z);
  sk.add(tablaSk);

  // svetilke ob peronu zunaj nadstreška
  const svG = zdruzi([
    [new THREE.CylinderGeometry(0.05, 0.07, 5.6, 10), '#3a3f45', M4(0, 2.8, 0)],
    [skatla(0.7, 0.1, 0.22, 0.03), '#3a3f45', M4(-0.25, 5.62, 0)],
  ]);
  const svM = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.5, metalness: 0.5 });
  const xs = [];
  for (let x = -88; x <= 88; x += 16) if (Math.abs(x) > 33) xs.push(x);
  const svIM = new THREE.InstancedMesh(svG, svM, xs.length);
  const glG = new THREE.BoxGeometry(0.6, 0.03, 0.16);
  const glIM = new THREE.InstancedMesh(glG, new THREE.MeshStandardMaterial({ color: '#fff', emissive: '#ffe2b0', emissiveIntensity: 0.4 }), xs.length);
  xs.forEach((x, i) => {
    m4.makeTranslation(x, PERON.y, 7.0);
    svIM.setMatrixAt(i, m4);
    m4.makeTranslation(x - 0.25, PERON.y + 5.56, 7.0);
    glIM.setMatrixAt(i, m4);
  });
  svIM.castShadow = true;
  sk.add(svIM, glIM);

  // klopi pod nadstreškom
  const klopG = zdruzi([
    [skatla(1.8, 0.05, 0.42, 0.01), '#8b5a35', M4(0, 0.45, 0)],
    [skatla(1.8, 0.4, 0.05, 0.01), '#8b5a35', M4(0, 0.75, 0.2, -0.12, 0, 0)],
    [skatla(0.06, 0.45, 0.4, 0.01), '#2f3338', M4(-0.75, 0.22, 0)],
    [skatla(0.06, 0.45, 0.4, 0.01), '#2f3338', M4(0.75, 0.22, 0)],
  ]);
  const klopM = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.7 });
  // klopi med stebri nadstreška (stebri na x = -28 + 7i)
  for (const x of [-17.5, 10.5, 24.5]) {
    const k = new THREE.Mesh(klopG, klopM);
    k.position.set(x, PERON.y, 6.9);
    k.castShadow = true;
    sk.add(k);
  }
  // oznaka tira "1"
  const [oc, og] = platno(128, 128);
  og.fillStyle = '#f4f4f0'; og.fillRect(0, 0, 128, 128);
  og.strokeStyle = '#1b3f8b'; og.lineWidth = 8; og.strokeRect(4, 4, 120, 120);
  og.fillStyle = '#1b3f8b'; og.font = '600 92px "IBM Plex Sans", sans-serif'; og.textAlign = 'center'; og.textBaseline = 'middle';
  og.fillText('1', 64, 70);
  const oznM = new THREE.MeshStandardMaterial({ map: tekstura(oc), roughness: 0.6 });
  for (const x of [-36, 36]) {
    const o = new THREE.Group();
    const dr = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 3.2, 8), kovina); dr.position.y = 1.6;
    const pl = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.5, 0.5), [kovina, kovina, kovina, kovina, oznM, oznM]);
    pl.position.y = 2.9;
    const p2 = pl.clone(); p2.rotation.y = Math.PI / 2; p2.position.y = 2.9;
    o.add(dr, p2);
    o.position.set(x, PERON.y, 2.9);
    o.traverse((m) => { if (m.isMesh) m.castShadow = true; });
    sk.add(o);
  }

  // poslopje postaje (južna železnica: pastelni omet, šotorasta streha)
  const PO = { x: 0, z: 17.5, w: 30, d: 10, h: 8.2 };
  const fas = teksturaFasade(PO.w, 2, 9, { loki: true, vrata: [4], seme: 3 });
  const fasS = teksturaFasade(PO.d, 2, 3, { loki: true, seme: 5 });
  const fasMat = (t) => new THREE.MeshStandardMaterial({ map: t.bar, emissiveMap: t.emis, emissive: '#ffffff', emissiveIntensity: 0, roughness: 0.85 });
  const mDolg = fasMat(fas), mKrat = fasMat(fasS);
  const telo = new THREE.Mesh(new THREE.BoxGeometry(PO.w, PO.h, PO.d), [mKrat, mKrat, beton, beton, mDolg, mDolg]);
  telo.position.set(PO.x, PERON.y + PO.h / 2 - 0.3, PO.z);
  telo.castShadow = true; telo.receiveShadow = true;
  sk.add(telo);
  const st = teksturaStrehe();
  st.bar.repeat.set(0.5, 0.5); st.nor.repeat.set(0.5, 0.5);
  const strM = new THREE.MeshStandardMaterial({ map: st.bar, normalMap: st.nor, roughness: 0.8 });
  const streha = new THREE.Mesh(strehaGeo(PO.w, PO.d, 3.4, 0.7), strM);
  streha.position.set(PO.x, PERON.y + PO.h - 0.3, PO.z);
  streha.castShadow = true; streha.receiveShadow = true;
  sk.add(streha);
  for (const dx of [-9, 7]) {
    const d = new THREE.Mesh(skatla(0.6, 1.6, 0.6, 0.02), new THREE.MeshStandardMaterial({ color: '#b9a98f', roughness: 0.9 }));
    d.position.set(dx, PERON.y + PO.h + 2.2, PO.z + 1.5);
    d.castShadow = true;
    sk.add(d);
  }
  // prizidek
  const pr = new THREE.Mesh(new THREE.BoxGeometry(9, 4.6, 8), [mKrat, mKrat, beton, beton, mDolg, mDolg]);
  pr.position.set(PO.x + PO.w / 2 + 4.5, PERON.y + 2.0, PO.z + 0.6);
  pr.castShadow = true; pr.receiveShadow = true;
  const prS = new THREE.Mesh(strehaGeo(9, 8, 2.2, 0.5), strM);
  prS.position.set(PO.x + PO.w / 2 + 4.5, PERON.y + 4.3, PO.z + 0.6);
  prS.castShadow = true;
  sk.add(pr, prS);
  // prostor med peronom in poslopjem: tlak
  const ploscad = new THREE.Mesh(new THREE.PlaneGeometry(70, 6), new THREE.MeshStandardMaterial({ color: '#8a8780', roughness: 0.95 }));
  ploscad.rotation.x = -Math.PI / 2;
  ploscad.position.set(5, PERON.y - 0.01, 10.6);
  ploscad.receiveShadow = true;
  sk.add(ploscad);

  return { skupina: sk, ura, tabla, fasade: [mDolg, mKrat], luci: [lucMat, glIM.material] };
}
