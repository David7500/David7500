// Skupna orodja: matematika časovnice, šum, platna za teksture, geometrija.
import * as THREE from 'three';

export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const smooth = (a, b, x) => {
  const t = clamp((x - a) / (b - a));
  return t * t * (3 - 2 * t);
};
// Mehkejši od smoothstep: brez sunka na koncih, za kamero.
export const smoother = (a, b, x) => {
  const t = clamp((x - a) / (b - a));
  return t * t * t * (t * (t * 6 - 15) + 10);
};
export const okno = (x, a, b, c, d) => smooth(a, b, x) * (1 - smooth(c, d, x));

// Ponovljiv naključni tok (mulberry32): isti svet ob vsakem nalaganju.
export function rng(seme = 1) {
  let a = seme >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Vrednostni šum 2D z mehko interpolacijo, za teren in teksture.
export function sum2(seme = 7) {
  const P = new Uint8Array(512);
  const r = rng(seme);
  const p = [...Array(256).keys()];
  for (let i = 255; i > 0; i--) {
    const j = Math.floor(r() * (i + 1));
    [p[i], p[j]] = [p[j], p[i]];
  }
  for (let i = 0; i < 512; i++) P[i] = p[i & 255];
  const V = new Float32Array(256).map(() => r() * 2 - 1);
  const f = (t) => t * t * t * (t * (t * 6 - 15) + 10);
  return (x, y) => {
    const xi = Math.floor(x), yi = Math.floor(y);
    const xf = x - xi, yf = y - yi;
    const X = xi & 255, Y = yi & 255;
    const a = V[P[P[X] + Y]], b = V[P[P[X + 1] + Y]];
    const c = V[P[P[X] + Y + 1]], d = V[P[P[X + 1] + Y + 1]];
    const u = f(xf), v = f(yf);
    return lerp(lerp(a, b, u), lerp(c, d, u), v);
  };
}

export function fbm(n, x, y, okt = 4, lak = 2, pad = 0.5) {
  let s = 0, a = 1, w = 0;
  for (let i = 0; i < okt; i++) {
    s += n(x, y) * a;
    w += a;
    x *= lak; y *= lak; a *= pad;
  }
  return s / w;
}

export function platno(w, h) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  return [c, c.getContext('2d')];
}

export function tekstura(c, { srgb = true, ponavljaj = false, aniz = 8 } = {}) {
  const t = new THREE.CanvasTexture(c);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  if (ponavljaj) t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.anisotropy = aniz;
  return t;
}

// Normalna karta iz višinske (Sobel), za tlakovce, opeke in balast.
export function normalnaIzVisine(c, moc = 2) {
  const w = c.width, h = c.height;
  const src = c.getContext('2d').getImageData(0, 0, w, h).data;
  const [o, g] = platno(w, h);
  const img = g.createImageData(w, h);
  const H = (x, y) => src[(((y + h) % h) * w + ((x + w) % w)) * 4] / 255;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const dx = (H(x + 1, y - 1) + 2 * H(x + 1, y) + H(x + 1, y + 1)) -
                 (H(x - 1, y - 1) + 2 * H(x - 1, y) + H(x - 1, y + 1));
      const dy = (H(x - 1, y + 1) + 2 * H(x, y + 1) + H(x + 1, y + 1)) -
                 (H(x - 1, y - 1) + 2 * H(x, y - 1) + H(x + 1, y - 1));
      const n = new THREE.Vector3(-dx * moc, dy * moc, 1).normalize();
      const i = (y * w + x) * 4;
      img.data[i] = (n.x * 0.5 + 0.5) * 255;
      img.data[i + 1] = (n.y * 0.5 + 0.5) * 255;
      img.data[i + 2] = (n.z * 0.5 + 0.5) * 255;
      img.data[i + 3] = 255;
    }
  }
  g.putImageData(img, 0, 0);
  return o;
}

// Zaobljena škatla z ostrimi normalami po ploskvah, a mehkimi robovi.
export function skatla(w, h, d, r = 0.02, seg = 2) {
  const g = new THREE.BoxGeometry(w, h, d, 1, 1, 1);
  if (r <= 0) return g;
  // Robovi se zaokrožijo s pomikom oglišč: dovolj za predmete, ki niso
  // v ospredju, in brez knjižnice RoundedBoxGeometry.
  return zaobljena(w, h, d, r, seg);
}

function zaobljena(w, h, d, r, seg) {
  const g = new THREE.BoxGeometry(w, h, d, seg * 2 + 1, seg * 2 + 1, seg * 2 + 1);
  const p = g.attributes.position;
  const v = new THREE.Vector3(), c = new THREE.Vector3();
  const hx = w / 2 - r, hy = h / 2 - r, hz = d / 2 - r;
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i);
    c.set(clamp(v.x, -hx, hx), clamp(v.y, -hy, hy), clamp(v.z, -hz, hz));
    const n = v.clone().sub(c);
    if (n.lengthSq() > 1e-12) v.copy(c).add(n.normalize().multiplyScalar(r));
    p.setXYZ(i, v.x, v.y, v.z);
  }
  g.computeVertexNormals();
  return g;
}

// Združi geometrije z istim naborom atributov; vsaka dobi barvo oglišč.
export function zdruzi(deli) {
  const geo = [];
  for (const [g, barva, m] of deli) {
    let x = g.index ? g.toNonIndexed() : g.clone();
    if (m) x.applyMatrix4(m);
    const n = x.attributes.position.count;
    const col = new Float32Array(n * 3);
    const c = new THREE.Color(barva);
    for (let i = 0; i < n; i++) col.set([c.r, c.g, c.b], i * 3);
    x.setAttribute('color', new THREE.BufferAttribute(col, 3));
    for (const k of Object.keys(x.attributes)) {
      if (!['position', 'normal', 'color', 'uv'].includes(k)) x.deleteAttribute(k);
    }
    if (!x.attributes.uv) x.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(n * 2), 2));
    geo.push(x);
  }
  const skupaj = geo.reduce((s, g) => s + g.attributes.position.count, 0);
  const out = new THREE.BufferGeometry();
  for (const [k, sz] of [['position', 3], ['normal', 3], ['color', 3], ['uv', 2]]) {
    const a = new Float32Array(skupaj * sz);
    let o = 0;
    for (const g of geo) { a.set(g.attributes[k].array, o); o += g.attributes[k].array.length; }
    out.setAttribute(k, new THREE.BufferAttribute(a, sz));
  }
  return out;
}

export const M4 = (x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0, s = 1) => {
  const m = new THREE.Matrix4();
  m.compose(new THREE.Vector3(x, y, z),
            new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz)),
            new THREE.Vector3(s, s, s));
  return m;
};
export const M4s = (x, y, z, sx, sy, sz, rx = 0, ry = 0, rz = 0) => {
  const m = new THREE.Matrix4();
  m.compose(new THREE.Vector3(x, y, z),
            new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz)),
            new THREE.Vector3(sx, sy, sz));
  return m;
};

// Hermitov zlepek skozi ključe {t, v:[...]}, C1 v času (ne v indeksu):
// kamera ne pospeši sunkovito, kadar so ključi neenakomerno razmaknjeni.
// Tangente omeji kot Fritsch-Carlson: kjer se vrednost ustavi ali obrne,
// kamera ne zaniha čez ključ (npr. pod peron po spustu z višine).
export function zlepek(kljuci) {
  const n = kljuci.length;
  const dim = kljuci[0].v.length;
  const tan = kljuci.map((k, i) => {
    if (k.mir) return new Array(dim).fill(0);
    const a = kljuci[Math.max(0, i - 1)], b = kljuci[Math.min(n - 1, i + 1)];
    const dt = b.t - a.t || 1;
    return k.v.map((_, d) => {
      const m = (b.v[d] - a.v[d]) / dt;
      if (i === 0 || i === n - 1) return m;
      const d0 = (k.v[d] - a.v[d]) / (k.t - a.t || 1), d1 = (b.v[d] - k.v[d]) / (b.t - k.t || 1);
      if (d0 * d1 <= 0) return 0;
      const meja = 3 * Math.min(Math.abs(d0), Math.abs(d1));
      return Math.sign(m) * Math.min(Math.abs(m), meja);
    });
  });
  return (t, out = new Array(dim)) => {
    if (t <= kljuci[0].t) { for (let d = 0; d < dim; d++) out[d] = kljuci[0].v[d]; return out; }
    if (t >= kljuci[n - 1].t) { for (let d = 0; d < dim; d++) out[d] = kljuci[n - 1].v[d]; return out; }
    let i = 0;
    while (kljuci[i + 1].t < t) i++;
    const A = kljuci[i], B = kljuci[i + 1];
    const h = B.t - A.t;
    const s = (t - A.t) / h;
    const s2 = s * s, s3 = s2 * s;
    const h00 = 2 * s3 - 3 * s2 + 1, h10 = s3 - 2 * s2 + s;
    const h01 = -2 * s3 + 3 * s2, h11 = s3 - s2;
    for (let d = 0; d < dim; d++) {
      out[d] = h00 * A.v[d] + h10 * h * tan[i][d] + h01 * B.v[d] + h11 * h * tan[i + 1][d];
    }
    return out;
  };
}
