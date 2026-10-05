// Stadler KISS, SŽ serija 313/318: dvonadstropna garnitura s tremi vozovi
// (UIC 2'Bo'+2'2'+Bo'2'), širina 2,80 m, višina 4,63 m (sl.wikipedia).
// Mere in barve s fotografij na Wikimedia Commons (313-001, -002, -008,
// -010, -016, -017, -018): višine na boku umerjene na višino vrat in
// strehe (313-002 s strani), čelo na širino 2,80 m (313-010 od spredaj).
//
// Karoserija je ena ploskev na voz: obroči prereza vzdolž voza in čelo kot
// višinsko polje x = f(y, z) z luknjo za spenjačo. Poslikava (okna, vrata,
// pasovi, maska, luči) je v senčilniku iz lokalnih koordinat, ne v
// teksturi -- ostra od blizu in brez prenosa slik.
import * as THREE from 'three';
import { clamp, lerp, platno, tekstura, zdruzi, M4, skatla } from './orodja.js';

export const KISS = {
  sir: 1.40,          // polovica širine
  Lc: 27.0,           // čelni voz z nosom
  Lv: 26.0,           // vmesni voz
  rega: 0.9,          // prehod med vozovoma
  aVozF: 5.1,         // vrtišče sprednjega podstavnega vozička od konice
  rVoz: 2.85,         // vrtišče od konca voza
  medOsjem: 2.4,
  rKolo: 0.46,
};
KISS.dolzina = KISS.Lc * 2 + KISS.Lv + KISS.rega * 2;

const BARVE = {
  modra: '#1a9be6',
  bela: '#e8e6df',
  streha: '#3d4247',
  crna: '#0b0d10',
  steklo: '#0b1117',
  temna: '#23272b',
};

// Višine na boku (m nad tirnico).
const H = {
  pasSp: [0.93, 1.11],      // spodnji modri pas
  crn: [1.11, 2.50],        // črn pas dvonadstropnega dela
  okSp: [1.13, 1.76],       // okna spodnje etaže
  pasZg: [2.50, 2.68],      // zgornja modra črta
  okZg: [2.86, 3.80],       // okna zgornje etaže (na nagnjenem boku)
  vrata: [0.45, 2.48],
  okV: [1.14, 2.09],        // okenci v vratih
  okVm: [1.74, 2.45],       // okna vmesne etaže nad vozički
  streha: 4.34,
};
const SPENJ = { z: 0.64, y0: 0.45, y1: 1.33, glob: 0.86 };   // odprtina za spenjačo

// ---------- prerez ----------
const DNO = 0.30;
const LOMI = [0.45, 0.645, 0.93, 1.11, 1.125, 1.30, 1.33, 1.42, 1.565, 1.63, 1.70, 1.72,
  1.90, 2.07, 2.20, 2.31, 2.38, 2.50, 2.68, 2.75];
const LOMI_ZG = [2.86, 3.15, 3.45, 3.53, 3.76, 3.84, 3.88, 4.05, 4.07];
function polprofil() {
  const W = KISS.sir, P = [];
  const r0 = 0.12;
  for (let k = 0; k <= 4; k++) {
    const t = -Math.PI / 2 + (k / 4) * (Math.PI / 2);
    P.push([W - r0 + r0 * Math.cos(t), DNO + r0 + r0 * Math.sin(t)]);
  }
  let ys = [];
  for (let y = 0.5; y < 2.75; y += 0.1) ys.push(+y.toFixed(3));
  ys = [...new Set([...ys, ...LOMI])].filter((y) => y > DNO + r0 + 0.01).sort((a, b) => a - b);
  for (const y of ys) P.push([W, y]);
  // nagnjen zgornji bok od 2,75 m: zgornja okna gledajo rahlo navzgor
  let yz = [];
  for (let y = 2.85; y < 4.1; y += 0.1) yz.push(+y.toFixed(3));
  yz = [...new Set([...yz, ...LOMI_ZG, 4.10])].sort((a, b) => a - b);
  for (const y of yz) P.push([lerp(W, 1.24, (y - 2.75) / 1.35), y]);
  const R = 0.30;
  for (let k = 1; k <= 7; k++) {
    const t = (k / 8) * (Math.PI / 2);
    P.push([0.94 + R * Math.cos(t), 4.10 + R * Math.sin(t)]);
  }
  return P;
}
const PP = polprofil();
const N = PP.length;
const Y_VRH = 4.40, W_VRH = 0.94;
const U = (() => {
  const u = [];
  for (let i = 0; i <= 24; i++) u.push(Math.sin((Math.PI / 2) * (2 * i / 24 - 1)));
  const r = SPENJ.z / KISS.sir;
  for (const x of [-r, r, -0.1, 0.1]) u.push(x);
  return [...new Set(u.map((x) => +x.toFixed(5)))].sort((a, b) => a - b);
})();
const M = U.length - 1;
const krona = (z) => Y_VRH + 0.05 * (1 - (z / W_VRH) ** 2);

function normalaProfila(j) {
  const a = PP[Math.max(0, j - 1)], b = PP[Math.min(N - 1, j + 1)];
  const dz = b[0] - a[0], dy = b[1] - a[1];
  const l = Math.hypot(dz, dy) || 1;
  return [dy / l, -dz / l];   // [nz, ny] navzven
}
// Točka boka pri danem dnu: pod dnom odrezana, vogal pri visokem dnu oster.
function tockaBoka(j, dno) {
  const [w, y] = PP[j];
  const ostro = dno > DNO + 0.05 && y < dno + 0.12;
  return { w: ostro ? KISS.sir : w, y: Math.max(y, dno), pod: y < dno };
}

// ---------- čelo ----------
// Odmik od konice nazaj pri višini y. Odbijača spodaj sta najbolj spredaj;
// nad njima polica (1,30-1,33 m), luči in brada so umaknjeni, steklo je
// nagnjeno, zgoraj krožni lok z vodoravno tangento ob strehi.
const D_TOCKE = [[0.30, 0.04], [0.45, 0.02], [0.80, 0.0], [1.30, 0.0], [1.33, 0.13], [1.42, 0.15],
  [1.70, 0.21], [2.07, 0.38], [2.38, 0.47], [3.45, 1.02], [3.84, 1.25], [4.05, 1.40]];
const LOK = (() => {
  const y0 = 4.05, d0 = 1.40, s = 0.72, n = Math.hypot(s, 1);
  const R = (Y_VRH - y0) / (1 - s / n);
  return { R, cd: d0 + R / n, cy: y0 - (s / n) * R, y0 };
})();
const nagib = (() => {
  const T = D_TOCKE, n = [];
  for (let k = 0; k < T.length; k++) {
    if (k === T.length - 1) { n.push(0.72); continue; }
    if (k === 0) { n.push((T[1][1] - T[0][1]) / (T[1][0] - T[0][0])); continue; }
    const d0 = (T[k][1] - T[k - 1][1]) / (T[k][0] - T[k - 1][0]);
    const d1 = (T[k + 1][1] - T[k][1]) / (T[k + 1][0] - T[k][0]);
    n.push(d0 * d1 <= 0 ? 0 : (2 * d0 * d1) / (d0 + d1));
  }
  return n;
})();
function dCelo(y) {
  if (y >= LOK.y0) {
    const q = Math.max(0, LOK.R * LOK.R - (Math.min(y, Y_VRH) - LOK.cy) ** 2);
    return LOK.cd - Math.sqrt(q);
  }
  const T = D_TOCKE;
  let i = 0;
  while (i < T.length - 2 && y > T[i + 1][0]) i++;
  const [y0, v0] = T[i], [y1, v1] = T[i + 1];
  const h = y1 - y0, t = clamp((y - y0) / h);
  const t2 = t * t, t3 = t2 * t;
  return (2 * t3 - 3 * t2 + 1) * v0 + (t3 - 2 * t2 + t) * h * nagib[i] +
         (-2 * t3 + 3 * t2) * v1 + (t3 - t2) * h * nagib[i + 1];
}
function sirinaPri(y) {
  if (y >= Y_VRH) return W_VRH;
  if (y <= PP[0][1]) return PP[0][0];
  for (let j = 0; j < N - 1; j++) {
    if (y <= PP[j + 1][1]) {
      const t = (y - PP[j][1]) / (PP[j + 1][1] - PP[j][1] || 1);
      return lerp(PP[j][0], PP[j + 1][0], clamp(t));
    }
  }
  return lerp(PP[N - 1][0], W_VRH, clamp((y - PP[N - 1][1]) / (Y_VRH - PP[N - 1][1])));
}
// Tloris: odbijača z ostrejšima vogaloma, zgoraj bolj zaobljen nos.
function cCelo(y, z) {
  const W = y < 0.45 ? KISS.sir : sirinaPri(y);
  let Rz, Rx, lok;
  if (y <= 1.315) { Rz = 0.30; Rx = 0.17; lok = 0.03; } else {
    const t = clamp((y - 1.33) / 1.1);
    Rz = lerp(0.46, 0.66, t); Rx = lerp(0.30, 0.56, t); lok = 0.07;
  }
  Rz = Math.min(Rz, W * 0.7);
  const a = Math.min(Math.abs(z), W);
  let c = lok * (a / W) ** 2;
  const a0 = W - Rz;
  if (a > a0) c += Rx * (1 - Math.sqrt(Math.max(0, 1 - ((a - a0) / Rz) ** 2)));
  return c;
}
export const odmikCela = (y, z) => dCelo(y) + cCelo(y, z);

// ---------- karoserija ----------
function karoserija(L, celni) {
  const pos = [], nor = [], liv = [], idx = [];
  const nizko = 0.32, visoko = 1.0, kab = 0.45;
  const obroci = celni
    ? [[0, visoko], [4.5, visoko], [4.65, nizko], [L - 6.82, nizko], [L - 6.67, visoko],
       [L - 3.25, visoko], [L - 3.1, kab], [L - 2.9, kab]]
    : [[0, visoko], [4.5, visoko], [4.65, nizko], [L - 4.65, nizko], [L - 4.5, visoko], [L, visoko]];
  const ring = (x, dno, celo) => {
    const R = [];
    const X = (y, z) => (celo ? L - odmikCela(y, z) : x);
    for (let j = 0; j < N; j++) {
      const t = tockaBoka(j, dno);
      const [nz, ny] = normalaProfila(j);
      R.push([X(t.y, -t.w), t.y, -t.w, 0, t.pod ? 0 : ny, t.pod ? -1 : -nz, -0.5]);
    }
    for (let i = 0; i <= M; i++) {
      const z = U[i] * W_VRH;
      R.push([X(Y_VRH, z), krona(z), z, 0, 1, 0, 0]);
    }
    for (let j = N - 1; j >= 0; j--) {
      const t = tockaBoka(j, dno);
      const [nz, ny] = normalaProfila(j);
      R.push([X(t.y, t.w), t.y, t.w, 0, t.pod ? 0 : ny, t.pod ? 1 : nz, 0]);
    }
    const wd = dno > DNO + 0.05 ? KISS.sir : PP[0][0];
    for (let i = M; i >= 0; i--) {
      const z = U[i] * wd;
      R.push([X(dno, z), dno, z, 0, -1, 0, 0]);
    }
    return R;
  };
  const vsi = obroci.map(([x, d]) => ring(x, d, false));
  if (celni) vsi.push(ring(0, kab, true));
  const K = vsi[0].length;
  for (const R of vsi) {
    for (const [x, y, z, nx, ny, nz, st] of R) {
      pos.push(x, y, z); nor.push(nx, ny, nz); liv.push(x, y, st);
    }
  }
  for (let r = 0; r < vsi.length - 1; r++) {
    for (let k = 0; k < K - 1; k++) {
      const a = r * K + k, b = a + 1, c = a + K, d = c + 1;
      idx.push(a, b, c, b, d, c);
    }
  }
  const pokrov = (r, obrni) => {
    const R = vsi[r];
    const c = pos.length / 3;
    const x = R[0][0];
    pos.push(x, 2.3, 0); nor.push(obrni ? 1 : -1, 0, 0); liv.push(x, 2.3, 2);
    const s = pos.length / 3;
    for (const [px, py, pz] of R) { pos.push(px, py, pz); nor.push(obrni ? 1 : -1, 0, 0); liv.push(px, py, 2); }
    for (let k = 0; k < K - 1; k++) {
      if (obrni) idx.push(c, s + k, s + k + 1); else idx.push(c, s + k + 1, s + k);
    }
  };
  pokrov(0, false);
  if (!celni) pokrov(vsi.length - 1, true);

  if (celni) {
    // čelo: vrstice so točke boka (enako odrezane kot zadnji obroč) in streha
    const s = pos.length / 3;
    const vrst = [];
    for (let j = 0; j < N; j++) { const t = tockaBoka(j, kab); vrst.push([t.w, t.y]); }
    vrst.push([W_VRH, Y_VRH]);
    const R = vrst.length;
    const eps = 1e-3;
    for (let j = 0; j < R; j++) {
      const [w, y0] = vrst[j];
      for (let i = 0; i <= M; i++) {
        const z = U[i] * w;
        const y = j === R - 1 ? krona(z) : y0;
        const x = L - odmikCela(y, z);
        const ya = Math.max(y - eps, kab), yb = Math.min(y + eps, Y_VRH);
        let dy = yb > ya ? (odmikCela(yb, z) - odmikCela(ya, z)) / (yb - ya) : 0;
        // na polici (stopnici) normala gleda navzgor
        const zz = clamp(z, -w + eps, w - eps);
        const dz = (odmikCela(y, zz + eps) - odmikCela(y, zz - eps)) / (2 * eps);
        const n = new THREE.Vector3(1, Math.min(dy, 60), Math.max(-60, Math.min(60, dz))).normalize();
        pos.push(x, y, z); nor.push(n.x, n.y, n.z); liv.push(z, y, 1);
      }
    }
    const rz = SPENJ.z / KISS.sir + 1e-4;
    for (let j = 0; j < R - 1; j++) {
      const ya = vrst[j][1], yb = vrst[j + 1][1];
      const vLuknji = ya >= SPENJ.y0 - 1e-4 && yb <= SPENJ.y1 + 1e-4;
      for (let i = 0; i < M; i++) {
        if (vLuknji && Math.abs(U[i]) <= rz && Math.abs(U[i + 1]) <= rz) continue;
        const a = s + j * (M + 1) + i, b = a + 1, c = a + M + 1, d = c + 1;
        idx.push(a, c, b, b, c, d);
      }
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
  g.setAttribute('aLiv', new THREE.Float32BufferAttribute(liv, 3));
  g.setIndex(idx);
  return g;
}

// Odprtina za spenjačo: stene, strop in zadnja stena (temne).
function odprtina(L) {
  const pos = [], idx = [];
  const { z: Z, y0, y1, glob } = SPENJ;
  const xz = L - glob;
  const quad = (a, b, c, d) => {
    const s = pos.length / 3;
    pos.push(...a, ...b, ...c, ...d);
    idx.push(s, s + 1, s + 2, s, s + 2, s + 3);
  };
  const n = 8;
  for (let k = 0; k < n; k++) {
    const ya = lerp(y0, y1, k / n), yb = lerp(y0, y1, (k + 1) / n);
    for (const sz of [-1, 1]) {
      const fa = L - odmikCela(ya, sz * Z), fb = L - odmikCela(yb, sz * Z);
      if (sz > 0) quad([fa, ya, Z], [xz, ya, Z], [xz, yb, Z], [fb, yb, Z]);
      else quad([xz, ya, -Z], [fa, ya, -Z], [fb, yb, -Z], [xz, yb, -Z]);
    }
  }
  for (let k = 0; k < n; k++) {
    const za = lerp(-Z, Z, k / n), zb = lerp(-Z, Z, (k + 1) / n);
    const fa = L - odmikCela(y1, za), fb = L - odmikCela(y1, zb);
    quad([fa, y1, za], [fb, y1, zb], [xz, y1, zb], [xz, y1, za]);
  }
  quad([xz, y0, -Z], [xz, y1, -Z], [xz, y1, Z], [xz, y0, Z]);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

// ---------- poslikava ----------
const GLSL_LIV = /* glsl */`
varying vec3 vLiv;
varying vec3 vLok;         // lega na vozu (m): x vzdolž, y gor, z čez
varying vec3 vNorLok;
uniform float uL;
uniform float uCelni;
uniform float uNoc;
uniform float uSvetloba;
uniform float uZarometi;   // 1 = čelo spredaj (beli žarometi)
uniform float uRdece;      // 1 = čelo zadaj (rdeči luči)
uniform sampler2D uNapisi;
uniform vec3 cModra, cBela, cStreha, cCrna, cSteklo, cTemna;
uniform vec3 uKam;         // kamera v koordinatah voza
uniform vec4 uVrata;       // odprta vrata na levi: x0, x1, odprtost
uniform mat3 uRot;         // voz -> svet
uniform vec4 uStrop;       // nadstrešek postaje: x0, x1, z0, z1
uniform float uStropY, uStropLuc;
uniform vec3 uStropBarva;
varying vec3 vSvetPos;
// prepustnost zatemnjenega stekla
const vec3 PREPUSTNOST = vec3(0.50, 0.55, 0.54);

float aa;
// okno v vratih pod točko: robova vrat v koordinati, ki jo je dobila vrata(),
// in ali je ta koordinata zrcaljena (uL - x)
float gVrO = 0.0, gVrA = 0.0, gVrB = 0.0, gVrZ = 0.0;
float gP0 = 0.0, gP1 = 0.0, gOkA = 0.0, gOkB = 0.0;
float pasY(float y, float a, float b) { return smoothstep(a - aa, a + aa, y) - smoothstep(b - aa, b + aa, y); }
float sdSkatla(vec2 p, vec2 a, vec2 b, float r) {
  vec2 c = (a + b) * 0.5, h = (b - a) * 0.5;
  vec2 q = abs(p - c) - h + r;
  return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r;
}
float skatla2(vec2 p, vec2 a, vec2 b, float r) { return 1.0 - smoothstep(-aa, aa, sdSkatla(p, a, b, r)); }
float krog(vec2 p, vec2 c, float r) { return 1.0 - smoothstep(-aa, aa, length(p - c) - r); }

struct Liv { vec3 col; float rough; vec3 emis; float coat; float spec; float zun; vec3 dz; };

float vrstaOken(float x, float y, float p0, float p1, float sir, float y0, float y1, float r, float nag, out float id) {
  float dol = p1 - p0;
  float n = max(1.0, floor(dol / 1.95 + 0.3));
  float kor = dol / n;
  float k = clamp(floor((x - p0) / kor), 0.0, n - 1.0);
  id = k + floor(p0 * 7.0);
  float c = p0 + (k + 0.5) * kor + (y - (y0 + y1) * 0.5) * nag;
  return skatla2(vec2(x, y), vec2(c - sir * 0.5, y0), vec2(c + sir * 0.5, y1), r);
}
void vrata(float x, float y, float a, float b, float zrc, inout vec3 col, inout float steklo) {
  float portal = skatla2(vec2(x, y), vec2(a - 0.07, 0.40), vec2(b + 0.07, 2.57), 0.10);
  col = mix(col, cCrna * 1.4, portal);
  float m = skatla2(vec2(x, y), vec2(a, 0.46), vec2(b, 2.48), 0.05);
  col = mix(col, cModra, m);
  float c = (a + b) * 0.5;
  float reza = (1.0 - smoothstep(0.007, 0.007 + aa, abs(x - c))) * m;
  col = mix(col, cCrna, reza);
  float l = (c - a) * 0.5;
  float o1 = skatla2(vec2(x, y), vec2(a + l - 0.11, 1.14), vec2(a + l + 0.11, 2.09), 0.08);
  float o2 = skatla2(vec2(x, y), vec2(c + l - 0.11, 1.14), vec2(c + l + 0.11, 2.09), 0.08);
  float ob = max(o1, o2);
  if (ob > gVrO) { gVrO = ob; gVrA = a; gVrB = b; gVrZ = zrc; }
  steklo = max(steklo, ob);
}

// ---- notranjost za steklom ----
// Žarek iz kamere skozi točko na steklu v škatlo etaže (»interior mapping«):
// daljna stena z okni, tla, strop z lučmi, sedeži 2 + 2 v predelih po oknih,
// tu in tam potnik. Brez geometrije, a s pravo paralakso.
float hashN(vec3 p) { return fract(sin(dot(p, vec3(12.9898, 78.233, 37.719))) * 43758.5453); }
float mehko(float d) { return 1.0 - smoothstep(-0.006, 0.006, d); }
float naslon(vec2 q, float yF) {
  return max(mehko(sdSkatla(q, vec2(0.31, yF + 0.40), vec2(0.775, yF + 1.18), 0.08)),
             mehko(sdSkatla(q, vec2(0.795, yF + 0.40), vec2(1.255, yF + 1.18), 0.08)));
}
float potnik(vec2 q, float zc, float yF) {
  float glava = 1.0 - smoothstep(0.9, 1.0, length((q - vec2(zc, yF + 1.25)) / vec2(0.086, 0.11)));
  float trup = mehko(sdSkatla(q, vec2(zc - 0.20, yF + 0.46), vec2(zc + 0.20, yF + 1.10), 0.10));
  return max(glava, trup);
}
vec3 barvaJakne(float h) {
  return h < 0.22 ? vec3(0.05, 0.055, 0.065) : h < 0.4 ? vec3(0.24, 0.07, 0.06) : h < 0.58 ? vec3(0.07, 0.12, 0.2)
       : h < 0.76 ? vec3(0.26, 0.25, 0.23) : h < 0.9 ? vec3(0.1, 0.16, 0.1) : vec3(0.42, 0.3, 0.12);
}
vec3 barvaLas(float h) {
  return h < 0.4 ? vec3(0.06, 0.04, 0.03) : h < 0.7 ? vec3(0.02) : h < 0.9 ? vec3(0.17, 0.1, 0.05) : vec3(0.42, 0.32, 0.17);
}
// okno na daljni steni: isti razpored kot na bližnji
float oknoDalec(vec3 H, float tip) {
  float id;
  if (tip < 1.5) return vrstaOken(H.x, H.y, gP0 + 0.2, gP1 - 0.2, 1.36, ${H.okSp[0]}, ${H.okSp[1]}, 0.10, 0.0, id);
  if (tip < 2.5) return vrstaOken(H.x, H.y, gP0 - 0.35, gP1 + 0.35, 1.80, ${H.okZg[0]}, ${H.okZg[1]}, 0.16, 0.10, id);
  if (tip < 4.5) return skatla2(H.xy, vec2(gOkA, ${H.okVm[0]}), vec2(gOkB, ${H.okVm[1]}), 0.10);
  float l = (gVrB - gVrA) * 0.25, c = (gVrA + gVrB) * 0.5;
  return max(skatla2(H.xy, vec2(gVrA + l - 0.11, 1.14), vec2(gVrA + l + 0.11, 2.09), 0.08),
             skatla2(H.xy, vec2(c + l - 0.11, 1.14), vec2(c + l + 0.11, 2.09), 0.08));
}
vec3 notranjost(vec3 P, vec3 D, float x0, float x1, float yF, float yC, float W,
                float b0, float kor, float sedezi, float tip, out float zun) {
  zun = 0.0;
  float sz = P.z < 0.0 ? 1.0 : -1.0;          // proti daljni steni
  if (D.z * sz <= 1e-4) return vec3(0.0);
  float tH = (sz * W - P.z) / D.z;
  int kaj = 0;                                // 0 stena, 1 strop, 2 tla, 3 čelna stena, 4 sedež
  if (D.y > 1e-4) { float t = (yC - P.y) / D.y; if (t < tH) { tH = t; kaj = 1; } }
  else if (D.y < -1e-4) { float t = (yF - P.y) / D.y; if (t < tH) { tH = t; kaj = 2; } }
  if (D.x > 1e-4) { float t = (x1 - P.x) / D.x; if (t < tH) { tH = t; kaj = 3; } }
  else if (D.x < -1e-4) { float t = (x0 - P.x) / D.x; if (t < tH) { tH = t; kaj = 3; } }
  vec3 col = vec3(0.0);
  if (sedezi > 0.5 && abs(D.x) > 1e-4) {
    float sx = D.x > 0.0 ? 1.0 : -1.0;
    float k0 = floor((P.x - b0) / kor);
    for (int j = 0; j < 4; j++) {
      float k = k0 + float(j) * sx;
      float a = b0 + k * kor, b = a + kor;
      if (b < x0 || a > x1) break;
      float tb = tH; vec3 cb = vec3(0.0); bool zad = false;
      for (int i = 0; i < 4; i++) {
        float xp = i == 0 ? a + 0.08 : i == 1 ? a + 0.36 : i == 2 ? b - 0.36 : b - 0.08;
        float t = (xp - P.x) / D.x;
        if (t <= 0.0 || t >= tb) continue;
        vec3 Q = P + D * t;
        vec2 q = vec2(abs(Q.z), Q.y);
        if (i == 0 || i == 3) {
          if (naslon(q, yF) > 0.5) {
            tb = t; zad = true;
            float hs = hashN(vec3(k, sign(Q.z), float(i) + uL));
            cb = mix(vec3(0.075, 0.12, 0.24), vec3(0.12, 0.18, 0.33), step(yF + 0.98, Q.y)) * (0.88 + 0.24 * hs);
          }
        } else {
          float zc = q.x < 0.785 ? 0.54 : 1.025;
          float smer = i == 1 ? 1.0 : -1.0;           // A gleda v +x, B v -x
          float h = hashN(vec3(k * 3.1 + zc, sign(Q.z), smer + uL));
          if (h < 0.3 && potnik(q, zc, yF) > 0.5) {
            tb = t; zad = true;
            bool obraz = smer * D.x < 0.0;
            vec3 lasje = barvaLas(fract(h * 37.0));
            if (Q.y > yF + 1.13) cb = obraz && Q.y < yF + 1.28 ? vec3(0.5, 0.35, 0.26) : lasje;
            else cb = barvaJakne(fract(h * 91.0));
          }
        }
      }
      // sedišča
      if (D.y < -1e-4) {
        float t = (yF + 0.45 - P.y) / D.y;
        if (t > 0.0 && t < tb) {
          vec3 Q = P + D * t;
          float az = abs(Q.z);
          bool vx = (Q.x > a + 0.08 && Q.x < a + 0.56) || (Q.x > b - 0.56 && Q.x < b - 0.08);
          if (vx && az > 0.31 && az < 1.255) { tb = t; zad = true; cb = vec3(0.085, 0.13, 0.26); }
        }
      }
      if (zad) { tH = tb; col = cb; kaj = 4; break; }
    }
  }
  vec3 H = P + D * tH;
  float vis = clamp((H.y - yF) / max(yC - yF, 0.1), 0.0, 1.0);
  float sv = mix(0.30, 0.62, uNoc) * (0.62 + 0.5 * vis);
  if (kaj == 0) {
    float ok = oknoDalec(H, tip);
    vec3 st = mix(vec3(0.30, 0.31, 0.33), vec3(0.74, 0.72, 0.67), smoothstep(yF + 0.30, yF + 0.36, H.y));
    col = st * sv * (1.0 - ok);
    zun = ok;
  } else if (kaj == 1) {
    float luc = 1.0 - smoothstep(0.04, 0.055, abs(abs(H.z) - 0.46));
    col = vec3(0.82, 0.82, 0.8) * sv + vec3(1.0, 0.94, 0.84) * luc * mix(0.30, 0.62, uNoc) * 3.2;
  } else if (kaj == 2) {
    col = mix(vec3(0.22, 0.23, 0.25), vec3(0.3, 0.31, 0.33), 1.0 - step(0.30, abs(H.z))) * sv;
  } else if (kaj == 3) {
    col = vec3(0.66, 0.65, 0.62) * sv;
  } else {
    col *= sv * 1.1;
  }
  return col;
}

// Žarometna skupina na čelu (az = |z|): okrogel žaromet zunaj, LED polje
// znotraj, ohišje s poševnim notranjim robom.
void lucCela(float az, float y, inout vec3 col, inout vec3 emis, inout float rough) {
  float notr = 0.49 + (y - 1.42) * 0.70;          // notranji poševni rob
  float vrh = 1.63 + (az - 0.49) * 0.11;
  float ohis = smoothstep(notr - aa, notr + aa, az) * (1.0 - smoothstep(1.15 - aa, 1.15 + aa, az))
             * smoothstep(1.42 - aa, 1.42 + aa, y) * (1.0 - smoothstep(vrh - aa, vrh + aa, y));
  col = mix(col, cCrna, ohis);
  rough = mix(rough, 0.12, ohis);
  // okrogel žaromet s sedmimi diodami
  vec2 p = vec2(az, y), c = vec2(1.0, 1.555);
  float zar = krog(p, c, 0.083);
  float diode = 0.0;
  diode = max(diode, krog(p, c, 0.017));
  for (int i = 0; i < 6; i++) {
    float t = float(i) * 1.0472 + 0.5236;
    diode = max(diode, krog(p, c + vec2(cos(t), sin(t)) * 0.048, 0.016));
  }
  col = mix(col, vec3(0.28, 0.29, 0.30), zar * ohis);
  col = mix(col, vec3(0.75), diode * zar);
  emis += vec3(1.0, 0.97, 0.9) * (diode * 6.0 + zar * 0.8) * uZarometi * uSvetloba;
  // LED polje: pike v mreži
  float polje = smoothstep(notr + 0.05 - aa, notr + 0.05 + aa, az) * (1.0 - smoothstep(0.87 - aa, 0.87 + aa, az))
              * smoothstep(1.47 - aa, 1.47 + aa, y) * (1.0 - smoothstep(1.61 - aa, 1.61 + aa, y));
  vec2 g = fract(vec2(az, y) / 0.018) - 0.5;
  float pika = 1.0 - smoothstep(0.22, 0.36, length(g));
  vec3 rd = vec3(1.0, 0.08, 0.05) * uRdece * 4.0 + vec3(1.0, 0.85, 0.7) * uZarometi * 1.2;
  col = mix(col, vec3(0.16, 0.08, 0.08), polje * 0.6);
  emis += rd * pika * polje * uSvetloba;
}

Liv liv() {
  vec3 p = vLiv;
  aa = max(0.0025, length(fwidth(p.xy)) * 0.8);
  Liv L;
  L.col = cBela; L.rough = 0.33; L.emis = vec3(0.0); L.coat = 0.7; L.spec = 0.04; L.zun = 0.0; L.dz = vec3(0.0, 0.0, 1.0);
  float steklo = 0.0, tipOkna = 0.0, wOkna = 0.0;
  float korSp = 1.95, korZg = 1.95;

  if (p.z > 1.5) {
    L.col = cTemna; L.rough = 0.7; L.coat = 0.0;
    return L;
  }
  if (p.z > 0.5) {
    // ---- čelo: p.x = z, p.y = y ----
    float az = abs(p.x), y = p.y;
    vec3 col = cModra;
    // spodaj belo: odbijača, polica, kotna pasova ob lučeh
    float brada = 0.49 + (y - 1.33) * 0.70;
    float belo = 1.0 - smoothstep(1.33 - aa, 1.33 + aa, y);
    belo = max(belo, (1.0 - smoothstep(1.42 - aa, 1.42 + aa, y)) * smoothstep(brada - aa, brada + aa, az));
    belo = max(belo, (1.0 - smoothstep(1.72 - aa, 1.72 + aa, y)) * smoothstep(1.14 - aa, 1.14 + aa, az));
    col = mix(col, cBela, belo);
    // črna maska: brada stekla (V), steklo, tabla, zgornji del z mrežo
    float vV = 2.07 + 0.24 * clamp(az / 0.98, 0.0, 1.0);
    float sir = 0.98 - max(0.0, y - 2.38) * 0.05;
    float maska = smoothstep(vV - aa, vV + aa, y) * (1.0 - smoothstep(sir - aa, sir + aa, az)) * (1.0 - smoothstep(3.46 - aa, 3.46 + aa, y));
    float sirZg = y < 3.84 ? 0.84 : 0.62 - (y - 3.84) * 0.25;
    maska = max(maska, smoothstep(3.44 - aa, 3.44 + aa, y) * (1.0 - smoothstep(sirZg - aa, sirZg + aa, az)));
    col = mix(col, cCrna, maska);
    float vs = skatla2(vec2(az, y), vec2(-0.96, 2.40), vec2(0.96 - (y - 2.4) * 0.05, 3.43), 0.10);
    float tabla = skatla2(vec2(az, y), vec2(-0.66, 3.52), vec2(0.66, 3.77), 0.04);
    float zgLuc = skatla2(vec2(az, y), vec2(-0.27, 3.88), vec2(0.27, 4.08), 0.07);
    float mreza = skatla2(vec2(az, y), vec2(-0.30, 4.12), vec2(0.30, 4.40), 0.04);
    col = mix(col, cTemna * (0.6 + 0.9 * step(0.5, fract(y * 34.0))), mreza);
    steklo = max(max(vs, tabla * 0.6), zgLuc * 0.8);
    L.col = col; L.rough = mix(0.30, 0.18, maska);
    lucCela(az, y, L.col, L.emis, L.rough);
    // logotip in številka iz atlasa
    vec2 uvL = vec2(-p.x / 0.84 + 0.5, (y - 1.715) / 0.215);
    if (uvL.x > 0.0 && uvL.x < 1.0 && uvL.y > 0.0 && uvL.y < 1.0) {
      float a = texture2D(uNapisi, vec2(uvL.x * 0.5, 0.5 + uvL.y * 0.5)).a;
      L.col = mix(L.col, cBela, a);
    }
    vec2 uvN = vec2(-p.x / 0.50 + 0.5, (y - 1.445) / 0.10);
    if (uvN.x > 0.0 && uvN.x < 1.0 && uvN.y > 0.0 && uvN.y < 1.0) {
      float a = texture2D(uNapisi, vec2(uvN.x * 0.5, 0.25 + uvN.y * 0.25)).a;
      L.col = mix(L.col, cBela, a);
    }
    vec2 uvT = vec2(-p.x / 1.30 + 0.5, (y - 3.53) / 0.23);
    if (uvT.x > 0.0 && uvT.x < 1.0 && uvT.y > 0.0 && uvT.y < 1.0) {
      vec4 t = texture2D(uNapisi, vec2(0.5 + uvT.x * 0.5, 0.75 + uvT.y * 0.25));
      L.emis += t.rgb * 2.4 * uSvetloba;
    }
    // zgornja signalna luč: LED pike
    vec2 g = fract(vec2(az, y) / 0.02) - 0.5;
    L.emis += vec3(1.0, 0.95, 0.85) * (1.0 - smoothstep(0.2, 0.35, length(g))) * skatla2(vec2(az, y), vec2(-0.12, 3.92), vec2(0.12, 4.04), 0.0) * uZarometi * 1.5 * uSvetloba;
  } else {
    // ---- bok: p.x = x vzdolž voza, p.y = višina, p.z < 0 = leva stran ----
    float x = p.x, y = p.y;
    float a = uL - x;
    float e = uCelni > 0.5 ? x : min(x, uL - x);
    // vrata, skozi katera vstopa dijak: odprtina v karoseriji, za njo preddverje
    if (uVrata.z > 0.001 && p.z < -0.25 && x > uVrata.x && x < uVrata.y && y > 0.44 && y < 2.50) discard;
    vec3 col = cBela;
    float streha = smoothstep(${H.streha.toFixed(2)} - aa, ${H.streha.toFixed(2)} + aa, y);
    float zac = uCelni > 0.5 ? 3.62 : -1.0;
    col = mix(col, cModra, max(pasY(y, ${H.pasZg[0]}, ${H.pasZg[1]}) * step(zac, a), pasY(y, ${H.pasSp[0]}, ${H.pasSp[1]}) * step(zac + 0.9, a)));
    // dvonadstropni del med vrati
    float p0 = 5.95;
    float p1 = uCelni > 0.5 ? uL - 8.05 : uL - 5.95;
    gP0 = p0; gP1 = p1;
    korSp = (p1 - p0 - 0.4) / max(1.0, floor((p1 - p0 - 0.4) / 1.95 + 0.3));
    korZg = (p1 - p0 + 0.7) / max(1.0, floor((p1 - p0 + 0.7) / 1.95 + 0.3));
    float vPasu = step(p0, x) * step(x, p1);
    col = mix(col, cCrna * 1.5, pasY(y, ${H.crn[0]}, ${H.crn[1]}) * vPasu);
    float id;
    float sp = vrstaOken(x, y, p0 + 0.2, p1 - 0.2, 1.36, ${H.okSp[0]}, ${H.okSp[1]}, 0.10, 0.0, id) * vPasu;
    col = mix(col, cCrna, vrstaOken(x, y, p0 + 0.2, p1 - 0.2, 1.46, ${H.okSp[0]} - 0.04, ${H.okSp[1]} + 0.05, 0.13, 0.0, id) * vPasu);
    steklo = max(steklo, sp);
    if (sp > wOkna) { wOkna = sp; tipOkna = 1.0; }
    // zgornja okna: črn okvir z zaobljenima koncema, okna z rahlo nagnjenimi stebrički
    float q0 = p0 - 0.45, q1 = p1 + 0.45;
    float okvirZg = skatla2(vec2(x, y), vec2(q0, ${H.okZg[0]} - 0.06), vec2(q1, ${H.okZg[1]} + 0.06), 0.34);
    col = mix(col, cCrna, okvirZg);
    float zgo = vrstaOken(x, y, q0 + 0.1, q1 - 0.1, 1.80, ${H.okZg[0]}, ${H.okZg[1]}, 0.16, 0.10, id) * okvirZg;
    steklo = max(steklo, zgo);
    if (zgo > wOkna) { wOkna = zgo; tipOkna = 2.0; }
    // okna vmesne etaže nad vozički
    float okv = skatla2(vec2(e, y), vec2(1.55, ${H.okVm[0]}), vec2(3.35, ${H.okVm[1]}), 0.10);
    col = mix(col, cCrna, skatla2(vec2(e, y), vec2(1.49, ${H.okVm[0]} - 0.06), vec2(3.41, ${H.okVm[1]} + 0.06), 0.13));
    steklo = max(steklo, okv);
    if (okv > wOkna) { wOkna = okv; tipOkna = 3.0; }
    if (uCelni > 0.5) {
      vrata(a, y, 6.75, 8.05, 1.0, col, steklo);
      vrata(x, y, 4.65, 5.95, 0.0, col, steklo);
      // modro polje za kabino: sprednji rob nagnjen naprej (vrh bliže nosu)
      float rob = 4.75 - (y - ${H.pasSp[0]}) * 0.62;
      float polje = smoothstep(rob - aa, rob + aa, a) * (1.0 - smoothstep(6.68 - aa, 6.68 + aa, a)) * pasY(y, ${H.pasSp[0]}, ${H.pasZg[1]});
      col = mix(col, cModra, polje);
      float okP = skatla2(vec2(a, y), vec2(5.05, ${H.okVm[0]}), vec2(6.30, ${H.okVm[1]}), 0.10);
      col = mix(col, cCrna, skatla2(vec2(a, y), vec2(4.99, ${H.okVm[0]} - 0.06), vec2(6.36, ${H.okVm[1]} + 0.06), 0.13));
      steklo = max(steklo, okP);
      if (okP > wOkna) { wOkna = okP; tipOkna = 4.0; }
      // napis na polju
      vec2 uvS = vec2((p.z < -0.25 ? (a - 4.25) : (6.45 - a)) / 2.2, (y - 1.20) / 0.22);
      if (uvS.x > 0.0 && uvS.x < 1.0 && uvS.y > 0.0 && uvS.y < 1.0) {
        float t = texture2D(uNapisi, vec2(0.5 + uvS.x * 0.5, 0.5 + uvS.y * 0.25)).a;
        col = mix(col, cBela, t * polje);
      }
      // kabina: veliko okno s poševnim sprednjim robom, ozko okno v vratih
      float rk = 1.15 + (y - 2.2) * 0.55;
      float kok = smoothstep(rk - aa, rk + aa, a) * skatla2(vec2(a, y), vec2(1.0, 2.2), vec2(2.35, 3.15), 0.12);
      float kvo = skatla2(vec2(a, y), vec2(2.52, 2.2), vec2(2.95, 3.15), 0.09);
      float sv = (1.0 - smoothstep(0.006, 0.006 + aa, abs(a - 2.43))) + (1.0 - smoothstep(0.006, 0.006 + aa, abs(a - 3.16)));
      col = mix(col, cCrna * 2.0, sv * step(0.62, y) * (1.0 - step(3.32, y)) * 0.8);
      steklo = max(steklo, max(kok, kvo));
      // modra kapa nosu: krivulja od luči navzgor in nazaj, nato vodoravno
      float t = clamp((a - 0.42) / 2.4, 0.0, 1.0);
      float spodaj = a < 0.42 ? 1.72 : 1.72 + 2.06 * sin(t * 1.5708);
      float konec = 6.6 - (y - 3.78) * 2.2;
      float kapa = smoothstep(spodaj - aa, spodaj + aa, y) * (1.0 - smoothstep(konec - aa, konec + aa, a));
      col = mix(col, cModra, kapa);
      // mreža prezračevanja na kapi
      float mz = skatla2(vec2(a, y), vec2(4.5, 3.95), vec2(5.35, 4.28), 0.04);
      col = mix(col, cTemna * (0.6 + 0.8 * step(0.5, fract(a * 22.0))), mz);
      col = mix(col, cCrna * 2.5, skatla2(vec2(a, y), vec2(5.55, 3.98), vec2(6.05, 4.26), 0.03));
      streha *= step(1.9, a);
    } else {
      vrata(x, y, 4.65, 5.95, 0.0, col, steklo);
      vrata(uL - x, y, 4.65, 5.95, 1.0, col, steklo);
    }
    if (gVrO > wOkna) { wOkna = gVrO; tipOkna = 5.0; }
    col = mix(col, cStreha, streha);
    // umazanija spodaj: zavorni prah
    col *= mix(0.84, 1.0, smoothstep(0.35, 0.95, y));
    L.col = col;
    L.rough = mix(0.33, 0.55, streha);
    L.coat = 0.7 * (1.0 - streha);
  }
  if (steklo > 0.0) {
    // zatemnjeno steklo: odsev po Fresnelu, skozenj notranjost etaže
    L.col = mix(L.col, cSteklo, steklo);
    L.rough = mix(L.rough, 0.05, steklo);
    L.coat = mix(L.coat, 0.0, steklo);
    L.spec = mix(L.spec, 0.04, steklo);
    if (tipOkna > 0.5) {
      vec3 P = vLok, D = normalize(vLok - uKam);
      float zun = 0.0;
      vec3 n = vec3(0.0);
      if (tipOkna < 1.5) {
        n = notranjost(P, D, gP0 + 0.05, gP1 - 0.05, 0.50, 2.38, 1.30, gP0 + 0.2, korSp, 1.0, 1.0, zun);
      } else if (tipOkna < 2.5) {
        n = notranjost(P, D, gP0 - 0.35, gP1 + 0.35, 2.58, 4.15, 1.22, gP0 - 0.35, korZg, 1.0, 2.0, zun);
      } else {
        // koordinata od konca voza navznoter (pri zadnjem koncu zrcaljena)
        bool zr = tipOkna < 3.5 ? (uCelni < 0.5 && P.x > uL * 0.5) : tipOkna < 4.5 ? true : gVrZ > 0.5;
        vec3 Pe = P, De = D;
        if (zr) { Pe.x = uL - P.x; De.x = -D.x; }
        if (tipOkna < 3.5) {
          gOkA = 1.55; gOkB = 3.35;
          n = notranjost(Pe, De, 0.15, 4.55, 1.22, 3.55, 1.30, 1.45, 2.0, 1.0, 3.0, zun);
        } else if (tipOkna < 4.5) {
          gOkA = 5.05; gOkB = 6.30;
          n = notranjost(Pe, De, 4.75, 6.65, 1.22, 3.55, 1.30, 4.78, 1.84, 1.0, 4.0, zun);
        } else {
          n = notranjost(Pe, De, gVrA - 0.85, gVrB + 0.85, 0.60, 2.50, 1.30, 0.0, 1.0, 0.0, 5.0, zun);
        }
      }
      float cosT = abs(dot(D, normalize(vNorLok)));
      float F = 0.04 + 0.96 * pow(1.0 - cosT, 5.0);
      float prep = (1.0 - F) * steklo;
      L.emis += n * PREPUSTNOST * prep;
      L.zun = zun * prep;
      L.dz = D;
    }
  }
  return L;
}
`;
// Odsev nadstreška postaje v karoseriji in steklu: kar bi se odbilo v nebo,
// pod nadstreškom zadene njegovo spodnjo ploskev s svetlobnima trakovoma.
const GLSL_ODSEV = /* glsl */`
#if defined( RE_IndirectSpecular )
{
  vec3 Rs = inverseTransformDirection(reflect(-geometryViewDir, geometryNormal), viewMatrix);
  if (Rs.y > 0.02) {
    float t = (uStropY - vSvetPos.y) / Rs.y;
    if (t > 0.0) {
      vec2 h = vSvetPos.xz + Rs.xz * t;
      float zak = smoothstep(uStrop.x - 1.0, uStrop.x + 1.0, h.x) * (1.0 - smoothstep(uStrop.y - 1.0, uStrop.y + 1.0, h.x))
                * smoothstep(uStrop.z - 0.25, uStrop.z + 0.25, h.y) * (1.0 - smoothstep(uStrop.w - 0.25, uStrop.w + 0.25, h.y));
      float tr = (1.0 - smoothstep(0.05, 0.09, abs(h.y - 3.1))) + (1.0 - smoothstep(0.05, 0.09, abs(h.y - 6.0)));
      vec3 s = uStropBarva + vec3(1.0, 0.95, 0.86) * tr * uStropLuc;
      radiance = mix(radiance, s, zak);
      #ifdef USE_CLEARCOAT
        clearcoatRadiance = mix(clearcoatRadiance, s, zak);
      #endif
    }
  }
}
#endif
`;
// Kar gre skozi daljno okno ven: okolje v smeri pogleda, skozi dve stekli.
const GLSL_SKOZI = /* glsl */`
#ifdef USE_ENVMAP
  if (LV.zun > 0.001) totalEmissiveRadiance += LV.zun * PREPUSTNOST * PREPUSTNOST * textureCubeUV(envMap, envMapRotation * normalize(uRot * LV.dz), 0.3).rgb * envMapIntensity;
#endif
`;

function atlasNapisov() {
  const [c, g] = platno(1024, 512);
  g.clearRect(0, 0, 1024, 512);
  // Logotip SŽ: dva enaka lika, drugi zasukan za 180° (obris s fotografije
  // 313-010, širina : višina = 2,8 : 1).
  g.fillStyle = '#fff';
  const lik = [[90, 340], [255, 170], [575, 170], [715, 35], [800, 120], [580, 340]];
  const nar = (pts) => { g.beginPath(); pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath(); g.fill(); };
  const sx = 512 / 1425, sy = 256 / 515;
  const v = (x, y) => [x * sx, y * sy];
  nar(lik.map(([x, y]) => v(x, y)));
  nar(lik.map(([x, y]) => v(1425 - x, 515 - y)));
  // Številka garniture.
  g.font = '500 104px "IBM Plex Sans", Arial, sans-serif';
  g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillText('313-005', 256, 322);
  // Napis na boku z malim logotipom.
  g.save();
  g.translate(512, 128);
  const ms = 0.075;
  g.translate(8, 18);
  const lv = (x, y) => [x * ms * 1.2, y * ms * 1.2];
  nar(lik.map(([x, y]) => lv(x, y)));
  nar(lik.map(([x, y]) => lv(1425 - x, 515 - y)));
  g.restore();
  g.font = '500 54px "IBM Plex Sans", Arial, sans-serif';
  g.textAlign = 'left';
  g.fillText('Slovenske železnice', 650, 176);
  // Smerna tabla: oranžni LED na črnem, pikčasto.
  const [t, tg] = platno(512, 128);
  tg.fillStyle = '#000'; tg.fillRect(0, 0, 512, 128);
  tg.fillStyle = '#fff';
  tg.font = '600 78px "IBM Plex Mono", monospace';
  tg.textAlign = 'center'; tg.textBaseline = 'middle';
  tg.fillText('V ŠOLO', 256, 66);
  const src = tg.getImageData(0, 0, 512, 128).data;
  g.fillStyle = '#000';
  g.fillRect(512, 0, 512, 128);
  const k = 6;
  for (let y = 0; y < 128; y += k) {
    for (let x = 0; x < 512; x += k) {
      const val = src[((y + 3) * 512 + x + 3) * 4];
      g.fillStyle = val > 90 ? '#ffa31a' : '#1a0d00';
      g.beginPath(); g.arc(512 + x + 3, y + 3, val > 90 ? 2.4 : 1.4, 0, Math.PI * 2); g.fill();
    }
  }
  return tekstura(c, { srgb: true, aniz: 8 });
}

let ATLAS = null;
function materialKaroserije(L, celni, skupni, luci = { zar: 0, rdece: 0 }) {
  const m = new THREE.MeshPhysicalMaterial({
    color: '#ffffff', roughness: 0.35, metalness: 0.0,
    clearcoat: 0.7, clearcoatRoughness: 0.1,
  });
  const u = {
    uL: { value: L }, uCelni: { value: celni ? 1 : 0 },
    uNoc: skupni.uNoc, uSvetloba: skupni.uSvetloba,
    uZarometi: { value: luci.zar }, uRdece: { value: luci.rdece },
    uNapisi: { value: ATLAS },
    cModra: { value: new THREE.Color(BARVE.modra) },
    cBela: { value: new THREE.Color(BARVE.bela) },
    cStreha: { value: new THREE.Color(BARVE.streha) },
    cCrna: { value: new THREE.Color(BARVE.crna) },
    cSteklo: { value: new THREE.Color(BARVE.steklo) },
    cTemna: { value: new THREE.Color(BARVE.temna) },
    uKam: { value: new THREE.Vector3(0, 2, -20) },
    uRot: { value: new THREE.Matrix3() },
    uVrata: { value: new THREE.Vector4(0, 0, 0, 0) },
    uStrop: skupni.uStrop, uStropY: skupni.uStropY, uStropLuc: skupni.uStropLuc, uStropBarva: skupni.uStropBarva,
  };
  m.userData.u = u;
  m.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, u);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nattribute vec3 aLiv;\nvarying vec3 vLiv;\nvarying vec3 vLok;\nvarying vec3 vNorLok;\nvarying vec3 vSvetPos;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvLiv = aLiv;\nvLok = position;\nvNorLok = normal;\nvSvetPos = (modelMatrix * vec4(position, 1.0)).xyz;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\n' + GLSL_LIV + '\nLiv LV;')
      .replace('#include <color_fragment>', '#include <color_fragment>\nLV = liv();\ndiffuseColor.rgb = LV.col;')
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\nroughnessFactor = LV.rough;')
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += LV.emis;')
      .replace('#include <lights_physical_fragment>', '#include <lights_physical_fragment>\nmaterial.clearcoat = LV.coat;\nmaterial.specularColor = max(material.specularColor, vec3(LV.spec));')
      .replace('#include <lights_fragment_maps>', '#include <lights_fragment_maps>\n' + GLSL_ODSEV)
      .replace('#include <lights_fragment_end>', '#include <lights_fragment_end>\n' + GLSL_SKOZI);
  };
  m.customProgramCacheKey = () => 'kiss-liv';
  return m;
}

// ---------- spodnji del čela: mreži, predpražnik, spenjača ----------
function mrezaOdbijaca() {
  // temen okvir z vodoravnimi rebri (posnetek 313-010: sedem reber)
  const d = [];
  d.push([skatla(0.035, 0.48, 0.37, 0.05), '#25282c', M4(0.0175, 0, 0)]);
  const rebro = new THREE.Shape();
  rebro.moveTo(0, -0.028); rebro.lineTo(0.03, -0.028); rebro.lineTo(0.055, -0.012); rebro.lineTo(0.055, 0.018);
  rebro.lineTo(0.035, 0.028); rebro.lineTo(0, 0.028); rebro.closePath();
  const rg = new THREE.ExtrudeGeometry(rebro, { depth: 0.33, bevelEnabled: false });
  rg.translate(0, 0, -0.165);
  for (let i = 0; i < 7; i++) d.push([rg, '#33373c', M4(0.02, -0.2 + i * 0.0665, 0)]);
  return zdruzi(d);
}

function predprazink(L) {
  // trapezna plošča pod odbijačema, spodaj umaknjena
  const pos = [];
  const T = [[0.45, 1.30, L - 0.06], [0.12, 0.98, L - 0.22]];
  const g = new THREE.BufferGeometry();
  const v = (y, z, x) => [x, y, z];
  const [[ya, za, xa], [yb, zb, xb]] = T;
  const d = 0.07;
  const P = [v(ya, -za, xa), v(ya, za, xa), v(yb, zb, xb), v(yb, -zb, xb),
             v(ya, -za, xa - d), v(ya, za, xa - d), v(yb, zb, xb - d), v(yb, -zb, xb - d)];
  const F = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [3, 7, 6, 2], [0, 4, 7, 3], [1, 2, 6, 5]];
  for (const [a, b, c2, e] of F) pos.push(...P[a], ...P[b], ...P[c2], ...P[a], ...P[c2], ...P[e]);
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.computeVertexNormals();
  return g;
}

function spenjaca(L) {
  const d = [];
  const y = 0.92, zc = -0.03;
  const kov = '#6c7074', tem = '#24272a', crn = '#121416';
  d.push([new THREE.CylinderGeometry(0.085, 0.1, 0.95, 14), tem, M4(L - 0.42, y, zc, 0, 0, Math.PI / 2)]);
  // meh (rdečkast gumijast zaščitni meh na posnetku 313-017)
  const meh = [];
  for (let i = 0; i <= 10; i++) meh.push(new THREE.Vector2(0.15 + (i % 2) * 0.035, i * 0.03));
  const mg = new THREE.LatheGeometry(meh, 18);
  d.push([mg, '#2b2a2c', M4(L - 0.78, y, zc, 0, 0, -Math.PI / 2)]);
  // glava: siva plošča z lijakom in čepom
  d.push([skatla(0.12, 0.36, 0.44, 0.02), kov, M4(L + 0.08, y, zc)]);
  d.push([new THREE.CylinderGeometry(0.105, 0.105, 0.03, 20), crn, M4(L + 0.145, y, zc + 0.1, 0, 0, Math.PI / 2)]);
  d.push([new THREE.TorusGeometry(0.105, 0.018, 8, 22), '#55595d', M4(L + 0.145, y, zc + 0.1, 0, Math.PI / 2, 0)]);
  d.push([new THREE.CylinderGeometry(0.09, 0.09, 0.05, 18), '#5d6165', M4(L + 0.16, y, zc - 0.11, 0, 0, Math.PI / 2)]);
  d.push([skatla(0.06, 0.03, 0.1, 0.005), '#2a2d30', M4(L + 0.2, y, zc - 0.11)]);
  // električna spojka zgoraj (črna omarica z rumenima opozoriloma)
  d.push([skatla(0.26, 0.12, 0.46, 0.02), '#1d1f22', M4(L + 0.02, y + 0.25, zc)]);
  for (const s of [-1, 1]) d.push([new THREE.CircleGeometry(0.022, 3), '#e8b400', M4(L + 0.152, y + 0.26, zc + s * 0.15, 0, Math.PI / 2, Math.PI / 2)]);
  // cevi in vzvod
  d.push([new THREE.TorusGeometry(0.14, 0.022, 8, 16, Math.PI), crn, M4(L - 0.05, y - 0.3, zc - 0.12, 0, Math.PI / 2, Math.PI)]);
  d.push([new THREE.TorusGeometry(0.12, 0.02, 8, 16, Math.PI), crn, M4(L - 0.1, y - 0.28, zc + 0.16, 0, Math.PI / 2, Math.PI)]);
  d.push([new THREE.CylinderGeometry(0.014, 0.014, 0.42, 6), '#7b7f83', M4(L + 0.22, y - 0.2, zc + 0.06, 0.55, 0, 0.35)]);
  return zdruzi(d);
}

// ---------- podstavni voziček ----------
function kolo() {
  const r = KISS.rKolo;
  const t = [[0.0, -0.07], [r - 0.05, -0.07], [r, -0.065], [r, 0.04], [r + 0.03, 0.045],
             [r + 0.03, 0.065], [r - 0.06, 0.07], [r - 0.08, 0.03], [0.16, 0.025],
             [0.13, 0.08], [0.0, 0.08]];
  const g = new THREE.LatheGeometry(t.map(([x, y]) => new THREE.Vector2(x, y)), 28);
  g.rotateX(Math.PI / 2);
  return g;
}

function vozicek(pogonski) {
  const sk = new THREE.Group();
  const jeklo = [];
  const temna = '#2c3035', siva = '#4a5057', guma = '#16171a', rumena = '#9c8a45';
  const B = KISS.medOsjem / 2;
  const oblika = new THREE.Shape();
  oblika.moveTo(-1.55, 0.62); oblika.lineTo(-1.05, 0.62); oblika.lineTo(-0.7, 0.44); oblika.lineTo(0.7, 0.44);
  oblika.lineTo(1.05, 0.62); oblika.lineTo(1.55, 0.62); oblika.lineTo(1.55, 0.84); oblika.lineTo(1.0, 0.84);
  oblika.lineTo(0.65, 0.70); oblika.lineTo(-0.65, 0.70); oblika.lineTo(-1.0, 0.84); oblika.lineTo(-1.55, 0.84);
  oblika.closePath();
  const nos = new THREE.ExtrudeGeometry(oblika, { depth: 0.16, bevelEnabled: true, bevelThickness: 0.015, bevelSize: 0.015, bevelSegments: 1 });
  for (const s of [-1, 1]) jeklo.push([nos, temna, M4(0, 0, s * 1.0 - 0.08)]);
  jeklo.push([skatla(0.5, 0.2, 1.9, 0.03), temna, M4(0, 0.52, 0)]);
  for (const xa of [-B, B]) {
    for (const s of [-1, 1]) {
      jeklo.push([skatla(0.34, 0.28, 0.22, 0.04), siva, M4(xa, KISS.rKolo, s * 1.04)]);
      jeklo.push([new THREE.CylinderGeometry(0.1, 0.1, 0.22, 10), rumena, M4(xa + 0.22 * Math.sign(xa), 0.70, s * 1.04)]);
      jeklo.push([new THREE.CylinderGeometry(0.075, 0.075, 0.16, 10), siva, M4(xa, KISS.rKolo, s * 1.18, Math.PI / 2)]);
    }
  }
  for (const s of [-1, 1]) {
    jeklo.push([new THREE.CylinderGeometry(0.27, 0.29, 0.24, 18), guma, M4(0, 0.96, s * 0.98)]);
    jeklo.push([new THREE.CylinderGeometry(0.045, 0.045, 1.3, 8), '#5d636a', M4(0, 0.78, s * 1.27, 0, 0, Math.PI / 2)]);
  }
  if (pogonski) {
    for (const xa of [-B, B]) jeklo.push([skatla(0.62, 0.5, 0.95, 0.05), '#33373c', M4(xa * 0.42, 0.45, 0.15)]);
  } else {
    for (const xa of [-B, B]) {
      for (const s of [-1, 1]) jeklo.push([new THREE.CylinderGeometry(0.31, 0.31, 0.05, 20), '#5a5f66', M4(xa, KISS.rKolo, s * 0.3, Math.PI / 2)]);
    }
  }
  const okvir = new THREE.Mesh(zdruzi(jeklo), new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.62, metalness: 0.35 }));
  okvir.castShadow = true;
  sk.add(okvir);
  const k = kolo();
  const os = new THREE.CylinderGeometry(0.085, 0.085, 1.5, 12);
  os.rotateX(Math.PI / 2);
  const dvojicaG = zdruzi([[k, '#9aa0a6', M4(0, 0, 0.75)], [k, '#9aa0a6', M4(0, 0, -0.75, 0, Math.PI, 0)], [os, '#3a3e43']]);
  const kolMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.32, metalness: 0.9 });
  const dvojici = [];
  for (const xa of [-B, B]) {
    const d = new THREE.Mesh(dvojicaG, kolMat);
    d.position.set(xa, KISS.rKolo, 0);
    d.castShadow = true;
    sk.add(d);
    dvojici.push(d);
  }
  sk.userData.dvojici = dvojici;
  return sk;
}

// ---------- odjemnik toka ----------
function odjemnik() {
  const g = new THREE.Group();
  const mat = new THREE.MeshStandardMaterial({ color: '#8b9198', roughness: 0.4, metalness: 0.7 });
  const izo = new THREE.MeshStandardMaterial({ color: '#7a2f24', roughness: 0.55 });
  const temn = new THREE.MeshStandardMaterial({ color: '#2a2e33', roughness: 0.6, metalness: 0.3 });
  for (const [x, z] of [[-0.5, -0.45], [-0.5, 0.45], [0.5, -0.45], [0.5, 0.45]]) {
    const i = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.07, 0.26, 10), izo);
    i.position.set(x, 0.13, z); g.add(i);
  }
  const podn = new THREE.Mesh(skatla(1.3, 0.08, 1.05, 0.02), temn);
  podn.position.y = 0.3; g.add(podn);
  const spodnja = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.045, 1.0, 8), mat);
  const zgornja = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.03, 1.0, 8), mat);
  const glava = new THREE.Group();
  for (const dz of [-0.11, 0.11]) {
    const l = new THREE.Mesh(skatla(0.06, 0.05, 1.5, 0.01), new THREE.MeshStandardMaterial({ color: '#31343a', roughness: 0.5 }));
    l.position.x = dz; glava.add(l);
  }
  for (const s of [-1, 1]) {
    const rog = new THREE.Mesh(new THREE.TorusGeometry(0.16, 0.012, 6, 12, Math.PI / 2), mat);
    rog.position.set(0, -0.16, s * 0.75); rog.rotation.y = Math.PI / 2; rog.rotation.z = s > 0 ? 0 : Math.PI / 2;
    glava.add(rog);
  }
  g.add(spodnja, zgornja, glava);
  g.userData.dvigni = (h) => {
    const y0 = 0.30, x0 = -0.2;
    const L1 = 1.2, L2 = 1.3;
    const ty = Math.max(0.12, h - y0), tx = -0.35;
    const d = Math.hypot(tx - x0, ty);
    const a1 = Math.atan2(ty, tx - x0) - Math.acos(clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1));
    const kx = x0 + L1 * Math.cos(a1), ky = y0 + L1 * Math.sin(a1);
    const post = (m, ax, ay, bx, by) => {
      m.position.set((ax + bx) / 2, (ay + by) / 2, 0);
      m.rotation.z = Math.atan2(by - ay, bx - ax) - Math.PI / 2;
      m.scale.y = Math.hypot(bx - ax, by - ay);
    };
    post(spodnja, x0, y0, kx, ky);
    post(zgornja, kx, ky, tx, y0 + ty);
    glava.position.set(tx, y0 + ty + 0.03, 0);
  };
  g.userData.dvigni(1.0);
  g.traverse((o) => { if (o.isMesh) o.castShadow = true; });
  return g;
}

// ---------- preddverje za vrati, skozi katera vstopi dijak ----------
// Tla v višini perona z rumenim robom, nasprotna vrata z okencema, drog,
// luč, odprtina k stopnicam v zgornjo etažo. Vidno samo, ko so vrata odprta.
function zgradiPreddverje(xa, xb, skupni) {
  const sk = new THREE.Group();
  const xc = (xa + xb) / 2, X0 = xa - 0.9, X1 = xb + 0.9;
  const kos = (x0, y0, z0, x1, y1, z1, c) => [new THREE.BoxGeometry(x1 - x0, y1 - y0, z1 - z0), c, M4((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)];
  const d = [
    kos(X0, 0.50, -1.37, X1, 0.58, 1.37, '#41454a'),            // tla
    kos(xa, 0.58, -1.37, xb, 0.586, -1.27, '#d8a817'),          // rumena robova
    kos(xa, 0.58, 1.27, xb, 0.586, 1.37, '#d8a817'),
    kos(xa - 0.02, 0.555, -1.43, xb + 0.02, 0.587, -1.30, '#8e949a'),   // prag
    kos(xa, 0.44, -1.42, xb, 0.555, -1.36, '#16181b'),
    kos(X0, 2.50, -1.37, X1, 2.58, 1.37, '#d5d6d3'),            // strop
    kos(X0, 0.58, 1.33, X1, 2.50, 1.37, '#c5c8c9'),             // daljna stena
    kos(xa, 0.58, 1.31, xb, 2.48, 1.33, '#33475f'),             // nasprotna vrata
    kos(xc - 0.006, 0.58, 1.304, xc + 0.006, 2.48, 1.31, '#121416'),
    kos(xa - 0.07, 0.44, -1.42, xa, 2.56, -1.29, '#2b2e33'),     // podboji
    kos(xb, 0.44, -1.42, xb + 0.07, 2.56, -1.29, '#2b2e33'),
    kos(xa - 0.07, 2.48, -1.42, xb + 0.07, 2.56, -1.29, '#2b2e33'),
    // stena proti dvonadstropnemu delu z odprtino k stopnicam
    kos(X0 - 0.05, 0.58, -1.37, X0, 2.50, -0.56, '#cfd2d4'),
    kos(X0 - 0.05, 0.58, 0.56, X0, 2.50, 1.37, '#cfd2d4'),
    kos(X0 - 0.05, 2.22, -0.56, X0, 2.50, 0.56, '#cfd2d4'),
    kos(X0 - 0.06, 0.58, -0.58, X0 + 0.01, 2.24, -0.55, '#8b9196'),
    kos(X0 - 0.06, 0.58, 0.55, X0 + 0.01, 2.24, 0.58, '#8b9196'),
    kos(X0 - 0.06, 2.21, -0.58, X0 + 0.01, 2.24, 0.58, '#8b9196'),
    kos(X0 + 0.002, 2.27, -0.42, X0 + 0.014, 2.43, 0.42, '#0c0d0f'),
    // stopnišče
    kos(X0 - 2.6, 0.58, -0.62, X0 - 0.05, 4.1, -0.56, '#c7cacc'),
    kos(X0 - 2.6, 0.58, 0.56, X0 - 0.05, 4.1, 0.62, '#c7cacc'),
    kos(X0 - 2.65, 2.4, -0.62, X0 - 2.6, 4.1, 0.62, '#cfd2d4'),
    kos(X0 - 2.6, 4.1, -0.62, X0 - 0.05, 4.16, 0.62, '#d5d6d3'),
    kos(X1, 0.58, -1.37, X1 + 0.05, 2.50, 1.37, '#cfd2d4'),     // stena proti koncu voza
  ];
  for (let i = 0; i < 8; i++) {
    const v = 0.58 + 0.245 * (i + 1);
    d.push(kos(X0 - 0.27 * (i + 1), 0.58, -0.55, X0 - 0.27 * i, v, 0.55, '#555a60'));
    d.push(kos(X0 - 0.27 * i - 0.035, v - 0.012, -0.55, X0 - 0.27 * i, v + 0.002, 0.55, '#d8a817'));
  }
  const notrMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.72 });
  // notranja luč brez luči: osnovna barva sveti s svetlostjo notranjosti
  notrMat.onBeforeCompile = (sh) => {
    sh.uniforms.uNotrSv = skupni.uNotrSv;
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform float uNotrSv;')
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += diffuseColor.rgb * uNotrSv;');
  };
  notrMat.customProgramCacheKey = () => 'preddverje';
  const stat = new THREE.Mesh(zdruzi(d), notrMat);
  stat.receiveShadow = true;
  sk.add(stat);
  // luči in okenci nasprotnih vrat
  const lucMat = new THREE.MeshStandardMaterial({ color: '#000', emissive: '#fff3df', emissiveIntensity: 2.2 });
  const l = (xb - xa) * 0.25;
  const svet = zdruzi([
    kos(xc - 0.55, 2.486, -0.30, xc + 0.55, 2.50, 0.30, '#fff'),
    kos(X0 - 2.0, 4.085, -0.06, X0 - 0.6, 4.10, 0.06, '#fff'),
  ]);
  sk.add(new THREE.Mesh(svet, lucMat));
  const zunajMat = new THREE.MeshStandardMaterial({ color: '#000', emissive: '#c4d1dc', emissiveIntensity: 0.8 });
  const okenci = zdruzi([
    kos(xa + l - 0.11, 1.14, 1.298, xa + l + 0.11, 2.09, 1.305, '#fff'),
    kos(xc + l - 0.11, 1.14, 1.298, xc + l + 0.11, 2.09, 1.305, '#fff'),
  ]);
  sk.add(new THREE.Mesh(okenci, zunajMat));
  // drogovi ob vratih in ograja stopnic
  const kovMat = new THREE.MeshStandardMaterial({ color: '#c3c8cd', metalness: 0.8, roughness: 0.3 });
  const dr = [];
  for (const [x, z] of [[xa + 0.08, -1.2], [xb - 0.08, -1.2], [xa + 0.08, 1.2], [xb - 0.08, 1.2]]) {
    dr.push([new THREE.CylinderGeometry(0.018, 0.018, 1.92, 10), '#c3c8cd', M4(x, 1.54, z)]);
  }
  const dol = Math.hypot(2.2, 1.9);
  dr.push([new THREE.CylinderGeometry(0.02, 0.02, dol, 8), '#c3c8cd', M4(X0 - 1.1, 2.45, -0.5, 0, 0, Math.atan2(2.2, 1.9))]);
  sk.add(new THREE.Mesh(zdruzi(dr), kovMat));
  // smerni napis nad odprtino (iz atlasa: LED »V ŠOLO«)
  const nap = new THREE.PlaneGeometry(0.8, 0.2);
  const uv = nap.attributes.uv;
  for (let i = 0; i < uv.count; i++) uv.setXY(i, 0.5 + uv.getX(i) * 0.5, 0.75 + uv.getY(i) * 0.25);
  const napis = new THREE.Mesh(nap, new THREE.MeshStandardMaterial({ color: '#000', emissive: '#ffffff', emissiveMap: ATLAS, emissiveIntensity: 1.6 }));
  napis.rotation.y = Math.PI / 2;
  napis.position.set(X0 + 0.016, 2.35, 0);
  sk.add(napis);
  sk.visible = false;
  sk.userData = { zunajMat, lucMat };
  return sk;
}

// Krili vrat: vtično-drsna, najprej malo ven, nato vsako na svojo stran.
function zgradiKrili(xa, xb) {
  const [kc, g2] = platno(64, 200);
  g2.fillStyle = BARVE.modra; g2.fillRect(0, 0, 64, 200);
  g2.fillStyle = '#0b0f14'; g2.beginPath(); g2.roundRect(22, 66, 20, 94, 8); g2.fill();
  const kMat = new THREE.MeshPhysicalMaterial({ map: tekstura(kc), roughness: 0.3, clearcoat: 0.7 });
  const xc = (xa + xb) / 2, w = (xb - xa) / 2;
  const sk = new THREE.Group();
  const krila = [-1, 1].map((st) => {
    const k = new THREE.Mesh(new THREE.BoxGeometry(w, 2.02, 0.025), kMat);
    k.position.set(xc + st * w / 2, 0.46 + 1.01, -1.42);
    k.userData = { x: xc + st * w / 2, st };
    k.castShadow = true;
    sk.add(k);
    return k;
  });
  sk.visible = false;
  sk.userData.krila = krila;
  return sk;
}

// ---------- celotna garnitura ----------
export function zgradiVlak() {
  ATLAS = ATLAS || atlasNapisov();
  const skupni = {
    uNoc: { value: 0 }, uSvetloba: { value: 1 }, uNotrSv: { value: 0.24 },
    // nadstrešek postaje (postaja.js): x, z, višina spodnje ploskve
    uStrop: { value: new THREE.Vector4(-31, 31, 2.35, 7.4) }, uStropY: { value: 4.1 },
    uStropLuc: { value: 0.6 }, uStropBarva: { value: new THREE.Color(0.15, 0.145, 0.14) },
  };
  const geoC = karoserija(KISS.Lc, true);
  const geoV = karoserija(KISS.Lv, false);
  const matA = materialKaroserije(KISS.Lc, true, skupni, { zar: 1, rdece: 0 });
  const matC = materialKaroserije(KISS.Lc, true, skupni, { zar: 0, rdece: 1 });
  const matV = materialKaroserije(KISS.Lv, false, skupni);
  const skupina = new THREE.Group();
  skupina.name = 'vlak';
  const detajlMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.55, metalness: 0.25 });
  const temnaMat = new THREE.MeshStandardMaterial({ color: '#141618', roughness: 0.85, side: THREE.DoubleSide });
  const predMat = new THREE.MeshStandardMaterial({ color: '#1b1d20', roughness: 0.6, metalness: 0.2, side: THREE.DoubleSide });
  const mrezaG = mrezaOdbijaca();

  function spodajCelo(voz, L) {
    voz.add(new THREE.Mesh(odprtina(L), temnaMat));
    const p = new THREE.Mesh(predprazink(L), predMat); p.castShadow = true; voz.add(p);
    for (const s of [-1, 1]) {
      const zc = s * 0.955, yc = 0.885;
      const m = new THREE.Mesh(mrezaG, detajlMat);
      m.position.set(L - odmikCela(yc, zc), yc, zc);
      m.rotation.y = -Math.atan2(odmikCela(yc, zc + 0.02) - odmikCela(yc, zc - 0.02), 0.04);
      m.castShadow = true;
      voz.add(m);
    }
    const sp = new THREE.Mesh(spenjaca(L), detajlMat);
    sp.castShadow = true;
    voz.add(sp);
    // brisalec na steklu
    const br = new THREE.Mesh(skatla(0.025, 0.85, 0.03, 0.008), new THREE.MeshStandardMaterial({ color: '#0d0d0e', roughness: 0.5 }));
    const yb = 2.75, zb = -0.42;
    br.position.set(L - odmikCela(yb, zb) + 0.03, yb, zb);
    br.rotation.z = Math.atan2(1, 0.51) - Math.PI / 2;
    br.rotation.x = 0.45;
    voz.add(br);
  }

  function streha(L, celni) {
    const d = [];
    const siva = '#5b6168', temna = '#3d4248';
    if (celni) {
      d.push([skatla(3.4, 0.16, 1.3, 0.05), temna, M4(2.4, 4.44, 0)]);
      d.push([skatla(2.0, 0.14, 1.2, 0.05), siva, M4(L - 7.2, 4.46, 0)]);
    } else {
      d.push([skatla(2.6, 0.2, 1.5, 0.06), siva, M4(2.3, 4.45, 0)]);
      d.push([skatla(2.6, 0.2, 1.5, 0.06), siva, M4(L - 2.3, 4.45, 0)]);
    }
    const m = new THREE.Mesh(zdruzi(d), detajlMat);
    m.castShadow = true;
    return m;
  }

  function prehod() {
    const d = [];
    for (let i = 0; i < 7; i++) d.push([skatla(0.08, 3.3, 2.35, 0.03), i % 2 ? '#1c1e21' : '#2a2d31', M4(-0.42 + i * 0.14, 2.5, 0)]);
    const m = new THREE.Mesh(zdruzi(d), detajlMat);
    m.castShadow = true;
    return m;
  }

  const vozovi = [];
  const opis = [
    { L: KISS.Lc, celni: true, obrnjen: false, mat: matA },
    { L: KISS.Lv, celni: false, obrnjen: false, mat: matV },
    { L: KISS.Lc, celni: true, obrnjen: true, mat: matC },
  ];
  for (const o of opis) {
    const voz = new THREE.Group();
    const notr = new THREE.Group();
    const tel = new THREE.Mesh(o.celni ? geoC : geoV, o.mat);
    tel.castShadow = true; tel.receiveShadow = true;
    notr.add(tel);
    notr.add(streha(o.L, o.celni));
    if (o.celni) spodajCelo(notr, o.L);
    notr.position.x = -o.L / 2;
    voz.add(notr);
    if (o.obrnjen) voz.rotation.y = Math.PI;
    const ov = new THREE.Group();
    ov.add(voz);
    skupina.add(ov);
    vozovi.push({ ...o, ovoj: ov, notr });
  }
  const pant = odjemnik();
  pant.position.set(4.2, 4.40, 0);
  pant.rotation.y = Math.PI;
  pant.userData.dvigni(1.07);
  vozovi[2].notr.add(pant);
  const pant2 = odjemnik();
  pant2.position.set(4.2, 4.40, 0);
  pant2.rotation.y = Math.PI;
  pant2.userData.dvigni(0.2);
  vozovi[0].notr.add(pant2);

  const prehodi = [prehod(), prehod()];
  prehodi.forEach((p) => skupina.add(p));
  const vozicki = [];
  const dodajV = (pog) => { const v = vozicek(pog); skupina.add(v); vozicki.push(v); return v; };
  const vs = [dodajV(false), dodajV(true), dodajV(false), dodajV(false), dodajV(true), dodajV(false)];

  const tA = new THREE.Vector3(), tB = new THREE.Vector3(), sm = new THREE.Vector3();
  const up = new THREE.Vector3(0, 1, 0);
  const zz = new THREE.Vector3(), yy = new THREE.Vector3();
  const mat4 = new THREE.Matrix4();
  let prevS = null, kot = 0;
  const usmeri = (o, smer) => {
    zz.crossVectors(smer, up).normalize();
    yy.crossVectors(zz, smer).normalize();
    mat4.makeBasis(smer, yy, zz);
    o.quaternion.setFromRotationMatrix(mat4);
  };
  function postavi(proga, sCelo) {
    const { Lc, Lv, rega, aVozF, rVoz } = KISS;
    const zac = [sCelo, sCelo - Lc - rega, sCelo - Lc - rega - Lv - rega];
    const vrtisca = [
      [zac[0] - aVozF, zac[0] - Lc + rVoz],
      [zac[1] - rVoz, zac[1] - Lv + rVoz],
      [zac[2] - rVoz, zac[2] - Lc + aVozF],
    ];
    vozovi.forEach((v, i) => {
      const [sf, sr] = vrtisca[i];
      proga.tocka(sf, tA); proga.tocka(sr, tB);
      sm.subVectors(tA, tB).normalize();
      const xf = i === 2 ? (v.L / 2 - rVoz) : v.L / 2 - (i === 0 ? aVozF : rVoz);
      const xr = i === 2 ? -(v.L / 2 - aVozF) : -(v.L / 2 - rVoz);
      const t = (0 - xr) / (xf - xr);
      v.ovoj.position.lerpVectors(tB, tA, t);
      usmeri(v.ovoj, sm);
    });
    for (let k = 0; k < 2; k++) {
      const s = zac[k + 1] + rega / 2;
      proga.tocka(s, tA); proga.smer(s, sm);
      prehodi[k].position.copy(tA);
      usmeri(prehodi[k], sm);
    }
    const ss = vrtisca.flat();
    if (prevS !== null) kot -= (sCelo - prevS) / KISS.rKolo;
    prevS = sCelo;
    ss.forEach((s, i) => {
      proga.tocka(s, tA); proga.smer(s, sm);
      vs[i].position.copy(tA);
      usmeri(vs[i], sm);
      for (const d of vs[i].userData.dvojici) d.rotation.z = kot;
    });
  }
  // vrata vmesnega voza ob peronu (spredaj levo), skozi katera vstopi dijak
  const VA = KISS.Lv - 5.95, VB = KISS.Lv - 4.65;
  const preddverje = zgradiPreddverje(VA, VB, skupni);
  const krili = zgradiKrili(VA, VB);
  vozovi[1].notr.add(preddverje, krili);
  function odpriVrata(odpr) {
    matV.userData.u.uVrata.value.set(VA, VB, odpr, 0);
    preddverje.visible = krili.visible = odpr > 0.001;
    const ven = smoothstep01(odpr / 0.18);
    for (const k of krili.userData.krila) {
      k.position.x = k.userData.x + k.userData.st * 0.63 * smoothstep01((odpr - 0.12) / 0.88);
      k.position.z = -1.42 - 0.045 * ven;
    }
  }
  // lega vrat v svetu (za pot dijaka): lokalna točka voza B
  const vrataLok = (x, y, z, out = new THREE.Vector3()) => {
    vozovi[1].notr.updateWorldMatrix(true, false);
    return vozovi[1].notr.localToWorld(out.set(x, y, z));
  };

  function nastaviLuci(spredaj = true, noc = 0) {
    skupni.uNoc.value = noc;
    skupni.uNotrSv.value = lerp(0.24, 0.55, noc);
    skupni.uStropLuc.value = lerp(0.6, 2.4, noc);
    skupni.uStropBarva.value.setRGB(lerp(0.15, 0.2, noc), lerp(0.145, 0.17, noc), lerp(0.14, 0.13, noc));
    preddverje.userData.zunajMat.emissiveIntensity = lerp(0.8, 0.05, noc);
    matA.userData.u.uZarometi.value = spredaj ? 1 : 0;
  }
  // kamera v koordinatah vsakega voza (notranjost za okni) in zasuk voz -> svet
  const inv = new THREE.Matrix4();
  function kamera(kam) {
    for (const v of vozovi) {
      v.notr.updateWorldMatrix(true, false);
      const u = v.mat.userData.u;
      inv.copy(v.notr.matrixWorld).invert();
      u.uKam.value.copy(kam.position).applyMatrix4(inv);
      u.uRot.value.setFromMatrix4(v.notr.matrixWorld);
    }
  }
  return { skupina, postavi, nastaviLuci, skupni, vozovi, pant, odpriVrata, vrataLok, kamera, zadnjiS: () => prevS, VRATA: { xa: VA, xb: VB } };
}
const smoothstep01 = (t) => { const x = clamp(t); return x * x * (3 - 2 * x); };
