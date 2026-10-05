// Proga: krivulja, tirnice, pragovi, gramozna greda in vozna mreža.
// Vlak vozi od vzhoda (x > 0) proti zahodu; s raste v smeri vožnje.
import * as THREE from 'three';
import { platno, tekstura, normalnaIzVisine, rng, sum2, fbm, zdruzi, M4, skatla } from './orodja.js';

export const TIR = 0.7175;   // pol tirne širine do sredine glave

// Kontrolne točke od vzhoda proti zahodu; postaja (x = 0) je na ravnem.
const KT = [
  [1400, 0], [900, 0], [500, 0], [250, 0], [0, 0], [-250, 0], [-480, 0],
  [-800, -25], [-1150, -120], [-1550, -190], [-1950, -170], [-2350, -80],
  [-2750, -15], [-3050, 0], [-3300, 0], [-3600, 0], [-4000, 0],
];

export function ustvariProgo() {
  const krivulja = new THREE.CatmullRomCurve3(KT.map(([x, z]) => new THREE.Vector3(x, 0, z)), false, 'centripetal');
  krivulja.arcLengthDivisions = 4000;
  const L = krivulja.getLength();
  // tabela s -> u za hitro iskanje (krivulja.getUtoTmapping je počasen)
  const N = 4000;
  const tocke = [], smeri = [];
  for (let i = 0; i <= N; i++) {
    const u = i / N;
    tocke.push(krivulja.getPointAt(u));
    smeri.push(krivulja.getTangentAt(u));
  }
  const tocka = (s, o = new THREE.Vector3()) => {
    const f = Math.min(Math.max(s / L, 0), 1) * N;
    const i = Math.min(Math.floor(f), N - 1), t = f - i;
    return o.lerpVectors(tocke[i], tocke[i + 1], t);
  };
  const smer = (s, o = new THREE.Vector3()) => {
    const f = Math.min(Math.max(s / L, 0), 1) * N;
    const i = Math.min(Math.floor(f), N - 1), t = f - i;
    return o.lerpVectors(smeri[i], smeri[i + 1], t).normalize();
  };
  // s pri danem x (proga je monotona po x)
  const sPriX = (x) => {
    let a = 0, b = L;
    for (let k = 0; k < 40; k++) {
      const m = (a + b) / 2;
      if (tocka(m).x > x) a = m; else b = m;
    }
    return (a + b) / 2;
  };
  // z proge pri x (tabela na 2 m), za oddaljenost terena od proge
  const ZX0 = -4000, ZX1 = 1400, ZK = 2;
  const zTab = new Float32Array(Math.round((ZX1 - ZX0) / ZK) + 1);
  for (let i = 0; i < zTab.length; i++) zTab[i] = tocka(sPriX(ZX0 + i * ZK)).z;
  const zPriX = (x) => {
    const f = (Math.min(Math.max(x, ZX0), ZX1) - ZX0) / ZK;
    const i = Math.min(Math.floor(f), zTab.length - 2), t = f - i;
    return zTab[i] * (1 - t) + zTab[i + 1] * t;
  };
  return { L, tocka, smer, sPriX, zPriX, krivulja };
}

// Bočni vektor (desno glede na smer vožnje, proti jugu na postaji).
const UP = new THREE.Vector3(0, 1, 0);
export function bok(t, o = new THREE.Vector3()) { return o.crossVectors(t, UP).normalize(); }

function teksturaGramoza() {
  const n = sum2(11), r = rng(5);
  const S = 256;
  const [c, g] = platno(S, S);
  const img = g.createImageData(S, S);
  // kamenčki: Voronoi-like celice z naključnim tonom
  const tocke = [...Array(260)].map(() => [r() * S, r() * S, 0.55 + r() * 0.45, r()]);
  for (let y = 0; y < S; y++) {
    for (let x = 0; x < S; x++) {
      let d1 = 1e9, d2 = 1e9, ton = 0, odt = 0;
      for (const [px, py, t, o] of tocke) {
        for (const [ox, oy] of [[0, 0], [S, 0], [-S, 0], [0, S], [0, -S]]) {
          const d = (x - px - ox) ** 2 + (y - py - oy) ** 2;
          if (d < d1) { d2 = d1; d1 = d; ton = t; odt = o; } else if (d < d2) d2 = d;
        }
      }
      const rob = Math.sqrt(d2) - Math.sqrt(d1);
      const v = Math.min(1, rob / 5) * ton * (0.85 + 0.15 * fbm(n, x / 9, y / 9, 3));
      const i = (y * S + x) * 4;
      const rjava = odt > 0.8 ? 1 : 0;
      img.data[i] = (118 + 40 * rjava) * v + 18;
      img.data[i + 1] = (114 + 22 * rjava) * v + 17;
      img.data[i + 2] = (108 + 4 * rjava) * v + 16;
      img.data[i + 3] = 255;
    }
  }
  g.putImageData(img, 0, 0);
  // višina za normalno karto: svetlost kamenčka
  const nm = normalnaIzVisine(c, 3);
  return { barva: tekstura(c, { ponavljaj: true }), normala: tekstura(nm, { srgb: false, ponavljaj: true }) };
}

// Trak vzdolž proge s prerezom `prerez` [[bok, y, v]...]; u teče vzdolž.
function trak(proga, s0, s1, korak, prerez, odmik = 0, uMer = 1) {
  const pos = [], uv = [], idx = [];
  const p = new THREE.Vector3(), t = new THREE.Vector3(), b = new THREE.Vector3();
  const n = Math.ceil((s1 - s0) / korak);
  const K = prerez.length;
  for (let i = 0; i <= n; i++) {
    const s = s0 + ((s1 - s0) * i) / n;
    proga.tocka(s, p); proga.smer(s, t); bok(t, b);
    for (const [l, y, v] of prerez) {
      pos.push(p.x + b.x * (l + odmik), y, p.z + b.z * (l + odmik));
      uv.push(s / uMer, v);
    }
    if (i < n) {
      for (let k = 0; k < K - 1; k++) {
        const a = i * K + k, c = a + K;
        idx.push(a, c, a + 1, a + 1, c, c + 1);
      }
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

export function zgradiProgo(proga, { atmU, NEBO } = {}) {
  const sk = new THREE.Group();
  const L = proga.L;
  const gr = teksturaGramoza();
  gr.barva.repeat.set(1, 1);
  // gramozna greda: vrh 3,9 m, brežine do terena
  const greda = trak(proga, 0, L, 2, [
    [-3.4, -0.85, 0], [-2.0, -0.22, 0.32], [2.0, -0.22, 0.68], [3.4, -0.85, 1],
  ], 0, 4);
  const gMat = new THREE.MeshStandardMaterial({ map: gr.barva, normalMap: gr.normala, normalScale: new THREE.Vector2(1.2, 1.2), roughness: 0.95, color: '#c9c4bc' });
  gMat.map.repeat.set(1, 3); gMat.normalMap.repeat.set(1, 3);
  const gM = new THREE.Mesh(greda, gMat);
  gM.receiveShadow = true;
  sk.add(gM);
  // tirnice: prerez glave, vrata in noge (desno in levo)
  const tirnica = [
    [-0.075, -0.17, 0], [0.075, -0.17, 0.1], [0.075, -0.155, 0.2], [0.012, -0.14, 0.3], [0.010, -0.04, 0.4],
    [0.036, -0.03, 0.5], [0.036, -0.004, 0.6], [0.026, 0, 0.7], [-0.026, 0, 0.8], [-0.036, -0.004, 0.9],
    [-0.036, -0.03, 0.92], [-0.010, -0.04, 0.94], [-0.012, -0.14, 0.96], [-0.075, -0.155, 0.98], [-0.075, -0.17, 1],
  ];
  const tMat = new THREE.MeshStandardMaterial({ color: '#7d6a5a', metalness: 0.75, roughness: 0.42 });
  // vrh glave je spoliran (svetlejši, gladek); v daljavi se zlije z rjo, da
  // tanek svetel pas ne miglja
  tMat.onBeforeCompile = (sh) => {
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <color_fragment>', `#include <color_fragment>
        float _vrh = smoothstep(0.86, 0.97, dot(normalize(vNormal), normalize((viewMatrix * vec4(0.0, 1.0, 0.0, 0.0)).xyz)))
                   * (1.0 - smoothstep(35.0, 140.0, length(vViewPosition)));
        diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.74, 0.75, 0.77), _vrh);`)
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\nfloat _dal = smoothstep(30.0, 150.0, length(vViewPosition));\nroughnessFactor = mix(mix(roughnessFactor, 0.2, _vrh), 0.8, _dal);')
      .replace('#include <metalnessmap_fragment>', '#include <metalnessmap_fragment>\nmetalnessFactor = mix(mix(metalnessFactor, 1.0, _vrh), 0.3, _dal);');
  };
  tMat.customProgramCacheKey = () => 'tirnica';
  // tirnica leži na pragovih, ti v gramozu: ploskve so si v daljavi bližje,
  // kot zmore globinski medpomnilnik -- zamik po plasteh, da ne migljajo
  tMat.polygonOffset = true; tMat.polygonOffsetFactor = -2; tMat.polygonOffsetUnits = -2;
  for (const st of [-TIR, TIR]) {
    const g = trak(proga, 0, L, 2, tirnica.map(([l, y, v]) => [l + st, y, v]), 0, 1);
    const m = new THREE.Mesh(g, tMat);
    m.castShadow = false; m.receiveShadow = true;
    sk.add(m);
  }

  // pragovi: betonski, 2,6 m, vsakih 0,6 m; v kosih po 300 m zaradi izreza
  const pragG = skatla(0.26, 0.19, 2.6, 0.02);
  const pragMat = new THREE.MeshStandardMaterial({ color: '#a7a39b', roughness: 0.9 });
  // pragovi na 0,6 m v daljavi dajo moire; tam se zlijejo z gramozom
  pragMat.onBeforeCompile = (sh) => {
    sh.fragmentShader = sh.fragmentShader.replace('#include <color_fragment>',
      '#include <color_fragment>\ndiffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.45, 0.43, 0.4), smoothstep(25.0, 110.0, length(vViewPosition)));');
  };
  pragMat.customProgramCacheKey = () => 'prag';
  pragMat.polygonOffset = true; pragMat.polygonOffsetFactor = -1; pragMat.polygonOffsetUnits = -1;
  const KOS = 300;
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), t = new THREE.Vector3();
  const r = rng(3);
  for (let s0 = 0; s0 < L; s0 += KOS) {
    const n = Math.floor(Math.min(KOS, L - s0) / 0.6);
    const im = new THREE.InstancedMesh(pragG, pragMat, n);
    for (let i = 0; i < n; i++) {
      const s = s0 + i * 0.6;
      proga.tocka(s, p); proga.smer(s, t);
      q.setFromAxisAngle(UP, Math.atan2(-t.z, t.x) + (r() - 0.5) * 0.01);
      p.y = -0.24;
      m4.compose(p, q, new THREE.Vector3(1, 1, 1));
      im.setMatrixAt(i, m4);
    }
    im.receiveShadow = true;
    im.computeBoundingSphere();
    sk.add(im);
  }

  // vozna mreža: drogovi na severni strani (nasproti perona), konzola čez
  // tir, nosilka, vozni vod v cikcaku
  const RAZ = 55;
  // drog stoji 0,8 m pod tirnico: lokalni y = svetovni + 0,8. Konzola nese
  // nosilko (6,62 m) na koncu poševne cevi, vozni vod (5,5 m) visi na
  // ročici z navpične cevi.
  const nag = Math.atan2(0.7, 3.4);
  const drogG = zdruzi([
    [skatla(0.22, 8.2, 0.22, 0.01), '#8e9496', M4(0, 4.1, 0)],
    [skatla(0.5, 0.25, 0.5, 0.02), '#7f8486', M4(0, 0.1, 0)],
    [new THREE.CylinderGeometry(0.035, 0.035, 3.6, 6), '#7c8183', M4(0, 7.8, 1.7, Math.PI / 2, 0, 0)],
    [new THREE.CylinderGeometry(0.04, 0.04, Math.hypot(3.4, 0.7), 6), '#7c8183', M4(0, 7.15, 1.7, Math.PI / 2 - nag, 0, 0)],
    [new THREE.CylinderGeometry(0.025, 0.025, 0.93, 6), '#7c8183', M4(0, 6.865, 2.6)],
    [new THREE.CylinderGeometry(0.018, 0.018, 0.95, 6), '#7c8183', M4(0, 6.33, 3.075, Math.PI / 2, 0, 0)],
    [new THREE.CylinderGeometry(0.05, 0.05, 0.4, 8), '#a5462f', M4(0, 7.8, 0.35, Math.PI / 2, 0, 0)],
    [new THREE.CylinderGeometry(0.05, 0.05, 0.35, 8), '#a5462f', M4(0, 6.87, 0.35, Math.PI / 2 - nag, 0, 0)],
  ]);
  const drogMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.6, metalness: 0.5 });
  const nDrog = Math.floor((L - 20) / RAZ);
  const drogIM = new THREE.InstancedMesh(drogG, drogMat, nDrog);
  const b = new THREE.Vector3();
  for (let i = 0; i < nDrog; i++) {
    const s = i * RAZ + 10;
    proga.tocka(s, p); proga.smer(s, t); bok(t, b);
    const lega = p.clone().addScaledVector(b, 3.3);
    lega.y = -0.8;
    // lokalni +z (konzola) gleda proti tiru
    q.setFromAxisAngle(UP, Math.atan2(-t.z, t.x) + Math.PI);
    m4.compose(lega, q, new THREE.Vector3(1, 1, 1));
    drogIM.setMatrixAt(i, m4);
  }
  drogIM.castShadow = true;
  drogIM.computeBoundingSphere();
  sk.add(drogIM);
  // žice: vozni vod 5,5 m v cikcaku ±0,2 m, nosilka 6,6 m s povesom, obešala
  const VOD_Y = 5.5, NOS_Y = 6.62;
  const seg = [];
  const tocka = (s, odm, y) => { proga.tocka(s, p); proga.smer(s, t); bok(t, b); return p.clone().addScaledVector(b, odm).setY(y); };
  const cik = (s) => { const k = (s - 10) / RAZ; return 0.2 * (1 - 2 * Math.abs((k % 2) - 1)); };
  const poves = (s) => { const f = ((s - 10) / RAZ) % 1; return NOS_Y - 0.5 * 4 * f * (1 - f); };
  const KOR = 3.0;
  for (let s = 10; s < 10 + (nDrog - 1) * RAZ - 1e-6; s += KOR) {
    const s1 = Math.min(s + KOR, 10 + (nDrog - 1) * RAZ);
    seg.push(tocka(s, cik(s), VOD_Y), tocka(s1, cik(s1), VOD_Y));
    const f0 = ((s - 10) / RAZ) % 1;
    const y1 = Math.abs(((s1 - 10) / RAZ) % 1) < 1e-6 ? NOS_Y : poves(s1);
    seg.push(tocka(s, cik(s) * 0.3, f0 < 1e-6 ? NOS_Y : poves(s)), tocka(s1, cik(s1) * 0.3, y1));
  }
  for (let s = 10 + 4.5; s < 10 + (nDrog - 1) * RAZ; s += 9) {
    seg.push(tocka(s, cik(s), VOD_Y), tocka(s, cik(s) * 0.3, poves(s)));
  }
  const zice = zgradiZice(seg, atmU, NEBO);
  sk.add(zice);
  return { skupina: sk, VOD_Y, zice };
}

// Žice kot trak čez zaslon: vsaj 1,2 piksla široke, tanjše postanejo
// prosojne (pokritost = širina / piksel) namesto da bi se trgale in utripale.
// Odsek, ki seka bližnjo ravnino, se pred projekcijo odreže (kot LineMaterial).
function zgradiZice(tocke, U, NEBO) {
  const n = tocke.length / 2;
  const A = new Float32Array(n * 4 * 3), B = new Float32Array(n * 4 * 3), K = new Float32Array(n * 4 * 2);
  const idx = new Uint32Array(n * 6);
  for (let i = 0; i < n; i++) {
    const a = tocke[2 * i], b = tocke[2 * i + 1];
    for (let v = 0; v < 4; v++) {
      const o = (i * 4 + v) * 3;
      A.set([a.x, a.y, a.z], o); B.set([b.x, b.y, b.z], o);
      K.set([v >> 1, v & 1 ? 1 : -1], (i * 4 + v) * 2);
    }
    idx.set([i * 4, i * 4 + 2, i * 4 + 1, i * 4 + 1, i * 4 + 2, i * 4 + 3], i * 6);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(A, 3));
  g.setAttribute('aB', new THREE.BufferAttribute(B, 3));
  g.setAttribute('aK', new THREE.BufferAttribute(K, 2));
  g.setIndex(new THREE.BufferAttribute(idx, 1));
  const mat = new THREE.ShaderMaterial({
    uniforms: { ...U, uLoc: { value: new THREE.Vector2(1000, 1000) }, uSir: { value: 0.014 }, uBarva: { value: new THREE.Color('#2c2824') } },
    vertexShader: /* glsl */`
      attribute vec3 aB; attribute vec2 aK;
      uniform vec2 uLoc; uniform float uSir;
      varying float vPokr, vPx, vS; varying vec3 vW;
      void main() {
        vec4 a = viewMatrix * vec4(position, 1.0), b = viewMatrix * vec4(aB, 1.0);
        float near = projectionMatrix[3][2] / (projectionMatrix[2][2] - 1.0);
        float zn = -near * 1.01;
        if (a.z > zn && b.z > zn) { gl_Position = vec4(2.0, 2.0, 2.0, 1.0); return; }
        if (a.z > zn) a.xyz = mix(a.xyz, b.xyz, (zn - a.z) / (b.z - a.z));
        if (b.z > zn) b.xyz = mix(b.xyz, a.xyz, (zn - b.z) / (a.z - b.z));
        vec4 ca = projectionMatrix * a, cb = projectionMatrix * b;
        vec2 sa = ca.xy / ca.w * uLoc * 0.5, sb = cb.xy / cb.w * uLoc * 0.5;
        vec2 smer = sb - sa;
        smer = length(smer) > 1e-5 ? normalize(smer) : vec2(1.0, 0.0);
        vec2 nor = vec2(-smer.y, smer.x);
        vec4 c = aK.x < 0.5 ? ca : cb;
        vec3 v = aK.x < 0.5 ? a.xyz : b.xyz;
        float px = uSir * projectionMatrix[1][1] * uLoc.y * 0.5 / max(-v.z, 1e-3);
        float w = max(px, 1.25);
        vPokr = px / w; vPx = w; vS = aK.y;
        c.xy += nor * aK.y * w * 0.5 / (uLoc * 0.5) * c.w;
        vW = aK.x < 0.5 ? position : aB;
        gl_Position = c;
      }`,
    fragmentShader: NEBO + /* glsl */`
      uniform vec3 uBarva;
      varying float vPokr, vPx, vS; varying vec3 vW;
      void main() {
        float rob = clamp((1.0 - abs(vS)) * vPx * 0.5 + 0.5, 0.0, 1.0);
        vec3 col = uBarva + neboBarva(vec3(0.0, 1.0, 0.0), 0.0) * 0.05;
        col = atmosfera(col, cameraPosition, vW - cameraPosition);
        gl_FragColor = vec4(col, vPokr * rob);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
    transparent: true, depthWrite: false,
  });
  const m = new THREE.Mesh(g, mat);
  m.frustumCulled = false;
  m.renderOrder = 2;
  return m;
}
