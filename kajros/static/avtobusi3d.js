"use strict";

// Avtobusi v 3D na velikem zemljevidu: vsak prevoznik svoj model in svoje
// barve, kot jih ima na cesti. Rise jih MapLibrova plast po meri
// (`type: "custom"`) z golim WebGL2: three.js je 172 kB stisnjen (MapLibre
// 299 kB) in za nekaj skatel ni vreden nove odvisnosti; WebGL2 pa MapLibre 6
// tako ali tako zahteva.
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
function avtoModeli(inki) {
  const B = AVTO_BELA;
  return {
    "1118": avtoZgibni({ streha: inki["1118"],
      pasovi: [[0.3, 0.62, "#8dc63f"], [0.62, 0.7, "#3c8c3c"], [0.7, 1.0, B]] }),
    "1123": avtoMedkrajevni({ streha: inki["1123"], srednjaVrata: true,
      pasovi: [[0.35, 0.72, "#33cad6"], [0.72, 0.8, "#2d146e"], [0.8, 1.0, B], [1.0, 1.35, B]] }),
    "1119": avtoMedkrajevni({ streha: inki["1119"],
      pasovi: [[0.35, 0.9, "#004899"], [0.9, 1.0, "#fbb900"], [1.0, 1.45, B]] }, 3.45),
    "1121": avtoMedkrajevni({ streha: inki["1121"], srednjaVrata: true,
      pasovi: [[0.35, 0.8, "#00a7e7"], [0.8, 0.9, "#0077be"], [0.9, 1.0, B], [1.0, 1.3, B]] }, 3.2),
    drugi: avtoMedkrajevni({ streha: inki.drugi,
      pasovi: [[0.35, 0.8, "#8a939e"], [0.8, 1.0, B], [1.0, 1.35, B]] }),
  };
}

const AVTO_VS = `#version 300 es
layout(location = 0) in vec3 a_pos;
layout(location = 1) in vec3 a_norm;
layout(location = 2) in vec3 a_barva;
layout(location = 3) in vec4 a_vozilo;
uniform mat4 u_matrix;
uniform float u_povecava;
uniform vec3 u_luc;
out vec3 v_barva;
void main() {
  float s = sin(a_vozilo.z), c = cos(a_vozilo.z);
  vec2 v = vec2(a_pos.x * s - a_pos.y * c, a_pos.x * c + a_pos.y * s);
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
 * Plast in njen vnos. `vidna()` pove, ali naj plast ta hip rise (zoom,
 * stikalo); `povecava(z)` koliko je vozilo vecje od resnicnega.
 *
 * Vrne `{ plast, nastavi(vozila) }`; vozilo je `{lon, lat, smer, model}`,
 * smer v stopinjah od severa.
 */
function avtobusi3D({ id, inki, vidna, povecava }) {
  const modeli = avtoModeli(inki);
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
        gl.vertexAttribPointer(3, 4, gl.FLOAT, false, 16, 0);
        gl.vertexAttribDivisor(3, 1);
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
      (po[a.model] || po.drugi).push(x - IZ_X, y - IZ_Y, (a.smer * Math.PI) / 180, enota);
    }
    for (const k of kljuci) {
      const r = risbe[k] || (risbe[k] = {});
      r.podatki = new Float32Array(po[k]);
      r.stevilo = po[k].length / 4;
      r.sveze = true;
    }
    if (map) map.triggerRepaint();
  }

  return { plast, nastavi };
}
