// Pokrajina ob progi: dolina z njivami, gozdnati griči na severu, Alpe v
// daljavi, vas s cerkvijo na griču, kozolca, mestece s šolo na koncu.
// Vse je izmišljen kraj -- zgodba ne pove, kje.
import * as THREE from 'three';
import { rng, sum2, fbm, zdruzi, M4, M4s, skatla, smooth, clamp, lerp, platno, tekstura } from './orodja.js';
import { teksturaStrehe, strehaGeo } from './postaja.js';

const N1 = sum2(101), N2 = sum2(202), N3 = sum2(303);
export const CERKEV = { x: -1520, z: -430 };
export const SOLA = { x: -3290, z: 62 };
export const POSTAJA2 = { x0: -3330, x1: -3200 };

// Višina terena (m) v točki; tirnica je na y = 0, vznožje grede na -0,85.
export function visina(x, z, proga) {
  const zt = proga.zPriX(Math.max(-3990, Math.min(1390, x)));
  const dz = zt - z;                // > 0 severno od proge
  let h = -0.85 + 1.4 * fbm(N1, x / 380, z / 380, 3);
  // griči na severu
  const sev = smooth(220, 1500, dz);
  h += sev * (110 + 190 * (0.5 + 0.5 * fbm(N2, x / 1100, z / 1100, 4)));
  h += sev * 40 * fbm(N3, x / 260, z / 260, 3);
  // nižji griči na jugu
  const jug = smooth(500, 1700, -dz);
  h += jug * (40 + 80 * (0.5 + 0.5 * fbm(N2, x / 900 + 7, z / 900, 3)));
  // grič s cerkvijo
  const dc = Math.hypot(x - CERKEV.x, z - CERKEV.z);
  h += 34 * Math.exp(-(dc * dc) / (2 * 150 * 150));
  // ob progi ravno
  const ob = smooth(16, 70, Math.abs(dz));
  h = lerp(-0.85, h, ob);
  // trg pri postajah: ulice v višini perona
  const trg = (cx, cz, rx, rz) => {
    const d = Math.max(Math.abs(x - cx) / rx, Math.abs(z - cz) / rz);
    return 1 - smooth(0.75, 1.0, d);
  };
  const t1 = trg(30, 120, 190, 112), t2 = trg(-3260, 150, 200, 140);
  h = lerp(h, 0.25 + 0.6 * fbm(N1, x / 200, z / 200, 2), Math.max(t1, t2) * smooth(9, 14, z - zt));
  // pod tlakom za peronom in poslopjem postaje teren ne sme do tlaka (0,54 m),
  // sicer ploskvi migljata
  if (x > -48 && x < 72 && z - zt > 6 && z - zt < 30) h = Math.min(h, 0.4);
  return h;
}

// Gozd: na pobočjih in v pasovih; isto pravilo uporablja senčilnik terena.
function gozd(x, z, h) {
  const n = fbm(N2, x / 520 + 3.1, z / 520 - 1.7, 3);
  return clamp((n + smooth(8, 60, h) * 0.55 - 0.08) * 3.0);
}

const GLSL_TEREN = /* glsl */`
varying vec3 vSvet;
float th(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float tn(vec2 p) {
  vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(th(i), th(i + vec2(1, 0)), f.x), mix(th(i + vec2(0, 1)), th(i + vec2(1, 1)), f.x), f.y);
}
float tf(vec2 p) { return 0.5 * tn(p) + 0.25 * tn(p * 2.1 + 3.3) + 0.125 * tn(p * 4.3 + 7.1); }
vec3 teren(vec3 w, float gozd, out float hrap) {
  vec2 p = w.xz;
  // njive: zasukana mreža, vsaka parcela svoj posevek
  float kot = 0.35 + 0.5 * tn(p / 900.0);
  mat2 R = mat2(cos(kot), -sin(kot), sin(kot), cos(kot));
  vec2 q = R * p;
  vec2 vel = vec2(96.0, 34.0) * (0.8 + 0.5 * tn(p / 700.0 + 4.0));
  vec2 cel = floor(q / vel);
  float id = th(cel);
  vec2 f = fract(q / vel);
  float meja = min(min(f.x, 1.0 - f.x) * vel.x, min(f.y, 1.0 - f.y) * vel.y);
  vec3 trava = vec3(0.29, 0.37, 0.15), temna = vec3(0.21, 0.27, 0.12);
  vec3 orana = vec3(0.30, 0.23, 0.16), strn = vec3(0.52, 0.45, 0.27), koruza = vec3(0.43, 0.36, 0.21);
  trava = mix(trava, vec3(0.36, 0.38, 0.18), th(cel + 7.0) * 0.6);
  vec3 c = id < 0.35 ? trava : id < 0.5 ? temna : id < 0.68 ? orana : id < 0.84 ? strn : koruza;
  // brazde
  float br = sin(q.y * (id < 0.68 && id > 0.5 ? 9.0 : 3.5)) * 0.5 + 0.5;
  c *= 0.94 + 0.07 * br;
  c *= 0.85 + 0.3 * tf(p / 18.0);
  // živa meja med parcelami
  c = mix(vec3(0.17, 0.2, 0.09), c, smoothstep(0.6, 2.5, meja));
  // gozd: jesenske krošnje, iglavci temni
  float pis = tf(p / 9.0);
  vec3 g = mix(vec3(0.13, 0.19, 0.11), vec3(0.55, 0.32, 0.10), smoothstep(0.35, 0.75, tf(p / 40.0 + 9.0)));
  g = mix(g, vec3(0.62, 0.48, 0.14), smoothstep(0.65, 0.9, pis) * 0.5);
  g *= 0.65 + 0.5 * pis;
  c = mix(c, g, gozd);
  hrap = mix(0.95, 0.9, gozd);
  return c;
}
`;

export function zgradiTeren(proga) {
  const X0 = -4600, X1 = 1800, Z0 = -3200, Z1 = 1800, K = 20;
  const nx = Math.round((X1 - X0) / K), nz = Math.round((Z1 - Z0) / K);
  const g = new THREE.PlaneGeometry(X1 - X0, Z1 - Z0, nx, nz);
  g.rotateX(-Math.PI / 2);
  g.translate((X0 + X1) / 2, 0, (Z0 + Z1) / 2);
  const p = g.attributes.position;
  const gz = new Float32Array(p.count);
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), z = p.getZ(i);
    const h = visina(x, z, proga);
    p.setY(i, h);
    gz[i] = gozd(x, z, h) * smooth(28, 70, Math.abs(proga.zPriX(Math.max(-3990, Math.min(1390, x))) - z));
  }
  g.setAttribute('aGozd', new THREE.BufferAttribute(gz, 1));
  g.computeVertexNormals();
  const m = new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 0.95 });
  m.onBeforeCompile = (sh) => {
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nattribute float aGozd;\nvarying float vGozd;\nvarying vec3 vSvet;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvGozd = aGozd;\nvSvet = (modelMatrix * vec4(position, 1.0)).xyz;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying float vGozd;\n' + GLSL_TEREN + '\nfloat _hr;')
      .replace('#include <color_fragment>', '#include <color_fragment>\ndiffuseColor.rgb = teren(vSvet, vGozd, _hr);')
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\nroughnessFactor = _hr;');
  };
  m.customProgramCacheKey = () => 'teren';
  const mesh = new THREE.Mesh(g, m);
  mesh.receiveShadow = true;
  return mesh;
}

// ---------- drevesa ----------
function geoIglavec() {
  const d = [];
  d.push([new THREE.CylinderGeometry(0.12, 0.18, 2.2, 6), '#4a3626', M4(0, 1.1, 0)]);
  const st = [[1.7, 3.6, 2.4], [1.35, 3.4, 4.4], [0.95, 3.2, 6.3], [0.55, 2.6, 8.0]];
  for (const [r, h, y] of st) d.push([new THREE.ConeGeometry(r, h, 8), '#ffffff', M4(0, y, 0)]);
  return zdruzi(d);
}
function geoIglavecDalec() {
  return zdruzi([[new THREE.ConeGeometry(1.8, 8.6, 5), '#ffffff', M4(0, 4.6, 0)]]);
}
function geoListavecDalec() {
  const g = new THREE.IcosahedronGeometry(2.8, 0);
  g.scale(1, 1.2, 1);
  return zdruzi([[g, '#ffffff', M4(0, 5.2, 0)]]);
}
function geoListavec(seme) {
  const r = rng(seme);
  const kr = new THREE.IcosahedronGeometry(2.6, 1);
  const p = kr.attributes.position;
  const n = sum2(seme);
  for (let i = 0; i < p.count; i++) {
    const v = new THREE.Vector3().fromBufferAttribute(p, i);
    const k = 1 + 0.28 * n(v.x * 0.9 + 3, v.y * 0.9 + v.z * 0.7);
    v.multiplyScalar(k);
    v.y *= 1.15;
    p.setXYZ(i, v.x, v.y, v.z);
  }
  kr.computeVertexNormals();
  const d = [[new THREE.CylinderGeometry(0.16, 0.24, 3.6, 6), '#4d3b2b', M4(0, 1.8, 0)], [kr, '#ffffff', M4(0, 5.0 + r(), 0)]];
  return zdruzi(d);
}

const BARVE_LIST = ['#a8641f', '#c48a2c', '#8c4a1c', '#b5772a', '#6f7a2c', '#5d6b28', '#d0a23a', '#7f3f1a'];
const BARVE_IGL = ['#2d4632', '#26402c', '#33503a', '#2a3f2f'];

export function zgradiDrevesa(proga, prosto = [], gostota = 1) {
  const prost = (x, z) => prosto.some(([px, pz, pr]) => (x - px) ** 2 + (z - pz) ** 2 < pr * pr);
  const sk = new THREE.Group();
  const r = rng(77);
  const geoI = geoIglavec(), geoL = geoListavec(5), geoId = geoIglavecDalec(), geoLd = geoListavecDalec();
  const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.92 });
  // kosi po 500 m: izrez pred kamero in senčno kamero deluje po kosih
  const KOS = 500;
  const kosi = new Map();
  const dodaj = (x, z, iglavec, s, senca, blizu = senca) => {
    const k = `${Math.floor(x / KOS)},${Math.floor(z / KOS)},${iglavec ? 1 : 0},${senca ? 1 : 0},${blizu ? 1 : 0}`;
    if (!kosi.has(k)) kosi.set(k, []);
    kosi.get(k).push([x, z, s]);
  };
  // gozd v pasu do 1,4 km od proge, gostejši bliže
  for (let i = 0; i < 30000 * gostota; i++) {
    const x = -4400 + r() * 5900;
    const zt = proga.zPriX(Math.max(-3990, Math.min(1390, x)));
    const dz = (r() < 0.75 ? -1 : 1) * (35 + Math.pow(r(), 1.6) * 1400);
    const z = zt + dz;
    const h = visina(x, z, proga);
    const gz = gozd(x, z, h);
    if (r() > gz * 0.9) continue;
    if (Math.abs(x - 30) < 220 && z > zt && z < zt + 240) continue;      // mesto pri postaji
    if (Math.abs(x + 3260) < 230 && z > zt && z < zt + 300) continue;    // mesto s šolo
    if (Math.hypot(x - CERKEV.x, z - CERKEV.z) < 70) continue;
    if (prost(x, z)) continue;
    const igl = r() < 0.38 + 0.3 * smooth(40, 200, h);
    dodaj(x, z, igl, 0.75 + r() * 0.75, Math.abs(dz) < 150, Math.abs(dz) < 320 || Math.hypot(x - CERKEV.x, z - CERKEV.z) < 400);
  }
  // posamezna drevesa in drevoredi ob njivah
  for (let i = 0; i < 1600; i++) {
    const x = -4300 + r() * 5600;
    const zt = proga.zPriX(Math.max(-3990, Math.min(1390, x)));
    const z = zt + (r() < 0.5 ? -1 : 1) * (22 + r() * 600);
    if (Math.abs(x - 30) < 200 && z > zt && z < zt + 240) continue;
    if (Math.abs(x + 3260) < 230 && z > zt && z < zt + 300) continue;
    if (prost(x, z)) continue;
    dodaj(x, z, r() < 0.2, 0.7 + r() * 0.6, Math.abs(z - zt) < 160);
  }
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), c = new THREE.Color();
  const up = new THREE.Vector3(0, 1, 0);
  let skupaj = 0;
  for (const [k, seznam] of kosi) {
    const igl = k.split(',')[2] === '1';
    const senca = k.split(',')[3] === '1';
    const blizu = k.split(',')[4] === '1';
    const im = new THREE.InstancedMesh(blizu ? (igl ? geoI : geoL) : (igl ? geoId : geoLd), mat, seznam.length);
    seznam.forEach(([x, z, s], i) => {
      const h = visina(x, z, proga);
      q.setFromAxisAngle(up, r() * Math.PI * 2);
      const sx = s * (0.85 + r() * 0.3);
      m4.compose(new THREE.Vector3(x, h - 0.2, z), q, new THREE.Vector3(sx, s * (igl ? 1.15 + r() * 0.5 : 0.9 + r() * 0.35), sx));
      im.setMatrixAt(i, m4);
      c.set((igl ? BARVE_IGL : BARVE_LIST)[Math.floor(r() * (igl ? 4 : 8))]);
      c.offsetHSL(0, 0, (r() - 0.5) * 0.06);
      im.setColorAt(i, c);
    });
    im.castShadow = senca;
    im.receiveShadow = false;
    im.computeBoundingSphere();
    sk.add(im);
    skupaj += seznam.length;
  }
  sk.userData.stevilo = skupaj;
  return sk;
}

// ---------- hiše ----------
function teksturaHise() {
  const [c, g] = platno(256, 256);
  const [e, eg] = platno(256, 256);
  g.fillStyle = '#ffffff'; g.fillRect(0, 0, 256, 256);
  eg.fillStyle = '#000'; eg.fillRect(0, 0, 256, 256);
  const r = rng(31);
  for (const y of [40, 150]) {
    for (const x of [30, 110, 190]) {
      g.fillStyle = '#d8d2c6'; g.fillRect(x - 4, y - 4, 44, 56);
      g.fillStyle = '#2b2a28'; g.fillRect(x, y, 36, 48);
      g.fillStyle = '#6b4a2f'; g.fillRect(x - 12, y, 10, 48); g.fillRect(x + 38, y, 10, 48);
      if (r() < 0.45) { eg.fillStyle = '#ffcf8a'; eg.fillRect(x + 2, y + 2, 32, 44); }
    }
  }
  return { bar: tekstura(c), emis: tekstura(e) };
}

export function zgradiNaselja(proga) {
  const sk = new THREE.Group();
  const r = rng(55);
  const hise = [];
  const gruca = (cx, cz, n, rad, os = 0) => {
    for (let i = 0, t = 0; i < n && t < n * 8; t++) {
      const a = r() * Math.PI * 2, d = Math.sqrt(r()) * rad;
      const x = cx + Math.cos(a) * d, z = cz + Math.sin(a) * d;
      const zt = proga.zPriX(Math.max(-3990, Math.min(1390, x)));
      if (Math.abs(z - zt) < 26) continue;
      if (hise.some((h) => Math.hypot(h.x - x, h.z - z) < 17)) continue;
      hise.push({ x, z, w: 8 + r() * 4, d: 9 + r() * 3, h: 5.5 + r() * 1.8, rot: os + (r() < 0.5 ? 0 : Math.PI / 2) + (r() - 0.5) * 0.25 });
      i++;
    }
  };
  gruca(60, 120, 46, 175);         // mesto pri postaji (jug)
  gruca(-60, -70, 16, 90);          // za drugim tirom (sever)
  gruca(-1250, 170, 24, 120);       // vas ob progi
  gruca(CERKEV.x + 40, CERKEV.z + 120, 16, 90);
  gruca(-3200, 170, 50, 200);       // mestece s šolo
  gruca(-2400, -260, 12, 80);
  gruca(-600, 260, 10, 70);
  const zidG = new THREE.BoxGeometry(1, 1, 1);
  zidG.translate(0, 0.5, 0);
  const tx = teksturaHise();
  const zidM = new THREE.MeshStandardMaterial({ map: tx.bar, emissiveMap: tx.emis, emissive: '#ffffff', emissiveIntensity: 0, roughness: 0.9 });
  const sG = new THREE.BufferGeometry();
  {
    // dvokapnica čez enotsko kocko: sleme vzdolž x, previs 0,08
    const W = 0.56, D = 0.56, Hh = 0.55;
    const P = [[-W, 0, -D], [W, 0, -D], [W, Hh, 0], [-W, Hh, 0], [W, 0, D], [-W, 0, D]];
    const t = [[0, 3, 2], [0, 2, 1], [4, 2, 3], [4, 3, 5], [5, 3, 0], [1, 2, 4]];
    const pos = [], uv = [];
    for (const tri of t) for (const j of tri) { pos.push(...P[j]); uv.push(P[j][0] * 6, (P[j][1] + Math.abs(P[j][2])) * 6); }
    sG.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    sG.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
    sG.computeVertexNormals();
  }
  const st = teksturaStrehe([160, 70, 46]);
  const sM = new THREE.MeshStandardMaterial({ map: st.bar, normalMap: st.nor, roughness: 0.82 });
  const zIM = new THREE.InstancedMesh(zidG, zidM, hise.length);
  const sIM = new THREE.InstancedMesh(sG, sM, hise.length);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), c = new THREE.Color();
  const up = new THREE.Vector3(0, 1, 0);
  const omet = ['#ece6d8', '#e9dfc4', '#f1ede4', '#e2d3b1', '#dcd6cb', '#efe2c6'];
  const strehe = ['#ffffff', '#e8d6cf', '#c9b8b0', '#f0e4dc'];
  hise.forEach((h, i) => {
    const y = visina(h.x, h.z, proga) - 0.3;
    q.setFromAxisAngle(up, h.rot);
    m4.compose(new THREE.Vector3(h.x, y, h.z), q, new THREE.Vector3(h.w, h.h, h.d));
    zIM.setMatrixAt(i, m4);
    c.set(omet[Math.floor(r() * omet.length)]); zIM.setColorAt(i, c);
    m4.compose(new THREE.Vector3(h.x, y + h.h, h.z), q, new THREE.Vector3(h.w * 1.05, h.w * 0.95, h.d * 1.05));
    sIM.setMatrixAt(i, m4);
    c.set(strehe[Math.floor(r() * strehe.length)]); sIM.setColorAt(i, c);
  });
  for (const im of [zIM, sIM]) { im.castShadow = true; im.receiveShadow = true; im.computeBoundingSphere(); sk.add(im); }
  sk.userData.okna = zidM;
  return sk;
}

// ---------- cerkev na griču ----------
export function zgradiCerkev(proga) {
  const sk = new THREE.Group();
  const bela = new THREE.MeshStandardMaterial({ color: '#efebe2', roughness: 0.85 });
  const st = teksturaStrehe([150, 64, 42]);
  st.bar.repeat.set(0.4, 0.4); st.nor.repeat.set(0.4, 0.4);
  const streha = new THREE.MeshStandardMaterial({ map: st.bar, normalMap: st.nor, roughness: 0.8 });
  const skrilj = new THREE.MeshStandardMaterial({ color: '#3b4146', roughness: 0.55, metalness: 0.3 });
  const temno = new THREE.MeshStandardMaterial({ color: '#1d1f22', roughness: 0.8 });
  const y = visina(CERKEV.x, CERKEV.z, proga) - 0.5;
  const ladja = new THREE.Mesh(new THREE.BoxGeometry(20, 8.5, 9.5), bela);
  ladja.position.set(0, 4.25, 0);
  const sL = new THREE.Mesh(strehaGeo(20, 9.5, 5.2, 0.6), streha);
  sL.position.set(0, 8.5, 0);
  const pres = new THREE.Mesh(new THREE.BoxGeometry(7, 7.2, 7.5), bela);
  pres.position.set(13, 3.6, 0);
  const sP = new THREE.Mesh(strehaGeo(7, 7.5, 3.6, 0.5), streha);
  sP.position.set(13, 7.2, 0);
  const zvon = new THREE.Mesh(new THREE.BoxGeometry(5, 24, 5), bela);
  zvon.position.set(-12, 12, 0);
  const lin = new THREE.Mesh(new THREE.ConeGeometry(3.7, 13, 8), skrilj);
  lin.rotation.y = Math.PI / 8;
  lin.position.set(-12, 24 + 6.5, 0);
  const kriz = new THREE.Mesh(zdruzi([[skatla(0.12, 1.6, 0.12, 0), '#c9a54a'], [skatla(0.12, 0.12, 0.9, 0), '#c9a54a', M4(0, 0.35, 0)]]),
    new THREE.MeshStandardMaterial({ vertexColors: true, metalness: 0.8, roughness: 0.3 }));
  kriz.position.set(-12, 37.8, 0);
  sk.add(ladja, sL, pres, sP, zvon, lin, kriz);
  // line odprtine zvonika in okna ladje
  for (const [dx, dz, ry] of [[2.52, 0, Math.PI / 2], [-2.52, 0, -Math.PI / 2], [0, 2.52, 0], [0, -2.52, Math.PI]]) {
    const o = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 2.6), temno);
    o.position.set(-12 + dx, 20.5, dz); o.rotation.y = ry;
    sk.add(o);
  }
  for (let i = 0; i < 4; i++) {
    for (const s of [-1, 1]) {
      const o = new THREE.Mesh(new THREE.PlaneGeometry(1.3, 3.2), temno);
      o.position.set(-6 + i * 4.2, 5, s * 4.77);
      o.rotation.y = s > 0 ? 0 : Math.PI;
      sk.add(o);
    }
  }
  sk.position.set(CERKEV.x, y, CERKEV.z);
  sk.rotation.y = 0.18;
  sk.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  return sk;
}

// ---------- kozolec (toplar) ----------
export function zgradiKozolec() {
  const d = [];
  const les = '#5d4330', temen = '#4a3626', seno = '#b8a050';
  const L = 13, B = 5.2, Hs = 6.6;
  for (let i = 0; i <= 3; i++) {
    for (const s of [-1, 1]) {
      d.push([skatla(0.32, Hs, 0.32, 0.03), les, M4(-L / 2 + i * (L / 3), Hs / 2, s * B / 2)]);
    }
    d.push([skatla(0.22, 0.25, B + 0.6, 0.02), temen, M4(-L / 2 + i * (L / 3), Hs - 0.3, 0)]);
    d.push([skatla(0.2, 0.22, B, 0.02), temen, M4(-L / 2 + i * (L / 3), 2.3, 0)]);
  }
  // late na obeh stenah
  for (const s of [-1, 1]) {
    for (let k = 0; k < 10; k++) d.push([skatla(L + 0.4, 0.07, 0.08, 0.01), les, M4(0, 0.9 + k * 0.52, s * (B / 2 + 0.18))]);
    // nekaj sena
    for (let k = 0; k < 4; k++) d.push([skatla(L * 0.9, 0.42, 0.18, 0.06), seno, M4(0.3, 1.2 + k * 1.05, s * (B / 2 + 0.3))]);
  }
  d.push([skatla(L + 0.4, 0.2, B - 0.4, 0.02), temen, M4(0, 3.4, 0)]);
  const g = new THREE.Group();
  const kost = new THREE.Mesh(zdruzi(d), new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.92 }));
  const st = teksturaStrehe([118, 70, 50]);
  st.bar.repeat.set(0.5, 0.5); st.nor.repeat.set(0.5, 0.5);
  const streha = new THREE.Mesh(strehaGeo(L + 1.2, B + 1.6, 2.6, 0.2), new THREE.MeshStandardMaterial({ map: st.bar, normalMap: st.nor, roughness: 0.85 }));
  streha.position.y = Hs;
  g.add(kost, streha);
  g.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  return g;
}

// ---------- šola ----------
export function zgradiSolo(proga) {
  const sk = new THREE.Group();
  const pxm = 32, W = 46, Hh = 12.6;
  const [c, g] = platno(W * pxm, Math.round(Hh * pxm));
  const [e, eg] = platno(W * pxm, Math.round(Hh * pxm));
  g.fillStyle = '#e8c87e'; g.fillRect(0, 0, c.width, c.height);
  eg.fillStyle = '#000'; eg.fillRect(0, 0, c.width, c.height);
  g.fillStyle = '#b39a6c'; g.fillRect(0, c.height - 0.9 * pxm, c.width, 0.9 * pxm);
  g.fillStyle = '#f5ead3';
  for (const yy of [0.25, 4.1, 8.0]) g.fillRect(0, yy * pxm, c.width, 0.22 * pxm);
  const r = rng(8);
  for (let k = 0; k < 3; k++) {
    for (let i = 0; i < 14; i++) {
      const x = (1.6 + i * 3.08) * pxm, y = c.height - (1.6 + k * 3.85 + 2.2) * pxm;
      g.fillStyle = '#f5ead3'; g.fillRect(x - 5, y - 5, 1.3 * pxm + 10, 2.2 * pxm + 10);
      g.fillStyle = '#2b3036'; g.fillRect(x, y, 1.3 * pxm, 2.2 * pxm);
      g.fillStyle = '#e9e2d0'; g.fillRect(x + 0.63 * pxm, y, 3, 2.2 * pxm); g.fillRect(x, y + 0.7 * pxm, 1.3 * pxm, 3);
      eg.fillStyle = r() < 0.8 ? '#ffe9c0' : '#000';
      eg.fillRect(x + 2, y + 2, 1.3 * pxm - 4, 2.2 * pxm - 4);
    }
  }
  // vhod s stopnicami in napisom
  g.fillStyle = '#5a3d2b'; g.fillRect(c.width / 2 - 1.2 * pxm, c.height - 3.6 * pxm, 2.4 * pxm, 2.7 * pxm);
  g.fillStyle = '#3a2f26'; g.font = `600 ${0.9 * pxm}px "IBM Plex Sans", sans-serif`; g.textAlign = 'center';
  g.fillText('ŠOLA', c.width / 2, c.height - 4.2 * pxm);
  const fm = new THREE.MeshStandardMaterial({ map: tekstura(c), emissiveMap: tekstura(e), emissive: '#ffffff', emissiveIntensity: 0, roughness: 0.85 });
  const bok = new THREE.MeshStandardMaterial({ color: '#e5c57b', roughness: 0.85 });
  const telo = new THREE.Mesh(new THREE.BoxGeometry(W, Hh, 15), [bok, bok, bok, bok, fm, fm]);
  telo.position.y = Hh / 2;
  const st = teksturaStrehe([120, 58, 40]);
  st.bar.repeat.set(0.5, 0.5); st.nor.repeat.set(0.5, 0.5);
  const streha = new THREE.Mesh(strehaGeo(W, 15, 5.5, 0.7), new THREE.MeshStandardMaterial({ map: st.bar, normalMap: st.nor, roughness: 0.8 }));
  streha.position.y = Hh;
  // zvonec na strehi (majhen stolp)
  const stolp = new THREE.Mesh(new THREE.BoxGeometry(2.4, 3.2, 2.4), new THREE.MeshStandardMaterial({ color: '#f5ead3', roughness: 0.8 }));
  stolp.position.set(0, Hh + 5.2, 0);
  const kapa = new THREE.Mesh(new THREE.ConeGeometry(1.9, 2.6, 4), new THREE.MeshStandardMaterial({ color: '#3d4448', roughness: 0.5, metalness: 0.4 }));
  kapa.rotation.y = Math.PI / 4; kapa.position.set(0, Hh + 8.1, 0);
  sk.add(telo, streha, stolp, kapa);
  const y = visina(SOLA.x, SOLA.z, proga) - 0.2;
  sk.position.set(SOLA.x, y, SOLA.z);
  sk.rotation.y = Math.PI;
  sk.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  sk.userData.okna = fm;
  sk.userData.zvonec = new THREE.Vector3(SOLA.x, y + Hh + 5.2, SOLA.z);
  return sk;
}

// ---------- gore v daljavi ----------
export function zgradiGore() {
  const nT = 256, nR = 26;
  const pos = [], idx = [], vis = [];
  const n = sum2(909);
  for (let j = 0; j <= nR; j++) {
    const rr = 5200 + Math.pow(j / nR, 1.3) * 32000;
    for (let i = 0; i <= nT; i++) {
      const t = (i / nT) * Math.PI * 2;
      const x = Math.cos(t) * rr - 1400, z = Math.sin(t) * rr - 600;
      // sever (z < 0): Alpe, drugod griči
      const sev = smooth(-0.2, 0.75, -Math.sin(t));
      const greben = 1 - Math.abs(fbm(n, x / 5200, z / 5200, 5));
      let h = (180 + 420 * fbm(n, x / 3000 + 9, z / 3000, 4)) * smooth(5200, 9000, rr);
      h += sev * Math.pow(greben, 2.2) * 2600 * smooth(9000, 20000, rr);
      h *= 1 - smooth(30000, 37000, rr);
      pos.push(x, h - 30, z);
      vis.push(h);
    }
  }
  for (let j = 0; j < nR; j++) {
    for (let i = 0; i < nT; i++) {
      const a = j * (nT + 1) + i, b = a + 1, c = a + nT + 1, d = c + 1;
      idx.push(a, c, b, b, c, d);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('aVis', new THREE.Float32BufferAttribute(vis, 1));
  g.setIndex(idx);
  g.computeVertexNormals();
  const m = new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 0.95 });
  m.onBeforeCompile = (sh) => {
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nattribute float aVis;\nvarying float vVis;\nvarying float vNY;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvVis = aVis;\nvNY = normal.y;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying float vVis;\nvarying float vNY;')
      .replace('#include <color_fragment>', `#include <color_fragment>
        vec3 c = mix(vec3(0.16, 0.2, 0.12), vec3(0.32, 0.3, 0.28), smoothstep(900.0, 1500.0, vVis));
        c = mix(c, vec3(0.92, 0.93, 0.95), smoothstep(1750.0, 2000.0, vVis + 160.0 * vNY));
        diffuseColor.rgb = c;`);
  };
  m.customProgramCacheKey = () => 'gore';
  const mesh = new THREE.Mesh(g, m);
  mesh.frustumCulled = false;
  return mesh;
}

// ---------- jutranja megla ----------
// Mehke ploskve nizko nad dolino; barva iz neba (zračna perspektiva), ob
// kameri izginejo, da ni ostrih presekov.
export function zgradiMeglo(U, NEBO) {
  const sk = new THREE.Group();
  const [c, g] = platno(256, 256);
  const n = sum2(404);
  const img = g.createImageData(256, 256);
  for (let y = 0; y < 256; y++) {
    for (let x = 0; x < 256; x++) {
      const v = fbm(n, x / 48, y / 48, 4) * 0.5 + 0.5;
      const dx = (x - 128) / 128, dy = (y - 128) / 128;
      const rob = clamp(1 - Math.sqrt(dx * dx + dy * dy));
      const a = clamp((v - 0.32) * 1.8) * Math.pow(rob, 0.6);
      const i = (y * 256 + x) * 4;
      img.data[i] = img.data[i + 1] = img.data[i + 2] = 255; img.data[i + 3] = a * 255;
    }
  }
  g.putImageData(img, 0, 0);
  const tex = tekstura(c, { srgb: false });
  const mat = new THREE.ShaderMaterial({
    uniforms: { ...U, uTex: { value: tex }, uMoc: { value: 1 } },
    vertexShader: /* glsl */`
      varying vec2 vUv; varying vec3 vW;
      void main() { vUv = uv; vec4 w = modelMatrix * vec4(position, 1.0); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`,
    fragmentShader: NEBO + /* glsl */`
      uniform sampler2D uTex; uniform float uMoc;
      varying vec2 vUv; varying vec3 vW;
      void main() {
        float a = texture2D(uTex, vUv + vec2(uCasN * 0.0004, 0.0)).a;
        vec3 d = normalize(vW - cameraPosition);
        float bl = smoothstep(8.0, 60.0, length(vW - cameraPosition));
        vec3 col = neboBarva(normalize(vec3(d.x, 0.04, d.z)), 0.0) * 1.05;
        gl_FragColor = vec4(col, a * 0.55 * bl * uMoc);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
    transparent: true, depthWrite: false,
  });
  const r = rng(12);
  const mesta = [[400, -60], [180, 60], [-300, 40], [-700, -80], [-1100, 60], [-1500, -120], [-1900, 40], [-2300, -60], [-2700, 30], [800, 20], [-200, -260], [-1000, -340]];
  for (const [x, z] of mesta) {
    const s = 700 + r() * 600;
    const p = new THREE.Mesh(new THREE.PlaneGeometry(s, s * 0.7), mat);
    p.rotation.x = -Math.PI / 2;
    p.rotation.z = r() * Math.PI;
    p.position.set(x, 2 + r() * 7, z);
    p.renderOrder = 5;
    sk.add(p);
  }
  sk.userData.mat = mat;
  return sk;
}
