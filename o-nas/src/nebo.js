// Nebo, sonce in zračna perspektiva. Barva megle je barva neba v smeri
// pogleda, gostota pada z višino -- jutranja megla leži v dolini, hribi
// nad njo so ostri. Isti izračun je v kupoli neba in v vseh materialih, zato
// se teren na obzorju zlije z nebom brez šiva.
import * as THREE from 'three';
import { lerp } from './orodja.js';

const GLSL_NEBO = /* glsl */`
uniform vec3 uSonce;
uniform vec3 uZenit, uObzorje, uSij, uSoncBarva;
uniform float uMeglaGost, uMeglaVis, uMeglaY0, uOblaki, uCasN, uZvezde, uMeglaMax;
float nhash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float nsum(vec2 p) {
  vec2 i = floor(p), f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  return mix(mix(nhash(i), nhash(i + vec2(1, 0)), f.x), mix(nhash(i + vec2(0, 1)), nhash(i + vec2(1, 1)), f.x), f.y);
}
float nfbm(vec2 p) {
  float s = 0.0, a = 0.5;
  for (int i = 0; i < 4; i++) { s += a * nsum(p); p = p * 2.03 + vec2(1.7, 9.2); a *= 0.5; }
  return s;
}
vec3 neboBarva(vec3 d, float disk) {
  float y = d.y;
  float t = pow(clamp(y, 0.0, 1.0), 0.5);
  vec3 c = mix(uObzorje, uZenit, t);
  float mu = max(dot(d, uSonce), 0.0);
  float nadObz = smoothstep(-0.06, 0.02, uSonce.y);
  c += uSij * (pow(mu, 6.0) * 0.45 + pow(mu, 48.0) * 0.55) * nadObz;
  c += uSoncBarva * smoothstep(0.99955, 0.99985, mu) * 30.0 * disk * nadObz;
  // pod obzorjem: zemeljska izparina
  c = mix(c, uObzorje * 0.82, smoothstep(0.0, -0.12, y));
  return c;
}
vec3 atmosfera(vec3 col, vec3 cam, vec3 v) {
  float dist = length(v);
  vec3 d = v / max(dist, 1e-4);
  float b = uMeglaVis;
  float h0 = max(cam.y - uMeglaY0, -50.0);
  float ry = d.y;
  float k = abs(ry * dist * b) > 1e-4 ? (1.0 - exp(-ry * dist * b)) / (ry * b) : dist;
  float kol = uMeglaGost * exp(-h0 * b) * k;
  float f = 1.0 - exp(-max(kol, 0.0));
  f = min(f, uMeglaMax);
  vec3 m = neboBarva(normalize(vec3(d.x, max(d.y, 0.0) * 0.6, d.z)), 0.0);
  return mix(col, m, f);
}
`;

export const NEBO_GLSL = GLSL_NEBO;

// Stanja dneva; vmesna se dobijo z mešanjem.
export const STANJA = {
  zora: {      // 7.41: sonce 4° nad obzorjem, megla v dolini
    sonceVis: 6.5, sonceAz: 104,
    zenit: '#6f93c4', obzorje: '#e7c9ae', sij: '#ffb36b', soncBarva: '#ffd9a8',
    sonceI: 2.7, sonceC: '#ffc890', nebI: 0.62, nebZg: '#a9c4e6', nebSp: '#6e6252',
    meglaGost: 0.0019, meglaVis: 0.022, meglaY0: 0, meglaMax: 0.97, oblaki: 0.42, zvezde: 0,
    izp: 1.0, okolje: 0.65,
  },
  jutro: {     // 8.05: sonce višje, megla se dviga
    sonceVis: 12, sonceAz: 112,
    zenit: '#5d8cc8', obzorje: '#dcd6cc', sij: '#ffd29a', soncBarva: '#fff0d8',
    sonceI: 2.9, sonceC: '#ffe4bf', nebI: 0.7, nebZg: '#b5cdea', nebSp: '#6f6a5c',
    meglaGost: 0.0009, meglaVis: 0.012, meglaY0: 0, meglaMax: 0.95, oblaki: 0.38, zvezde: 0,
    izp: 1.0, okolje: 0.75,
  },
  noc: {       // 22.40: luna, zvezde, luči postaje
    sonceVis: 28, sonceAz: 210,
    zenit: '#050a16', obzorje: '#17233a', sij: '#30486e', soncBarva: '#9fb4d8',
    sonceI: 0.38, sonceC: '#9db6e8', nebI: 0.24, nebZg: '#2a3c62', nebSp: '#0c0e12',
    meglaGost: 0.0014, meglaVis: 0.016, meglaY0: 0, meglaMax: 0.9, oblaki: 0.2, zvezde: 1,
    izp: 1.15, okolje: 0.35,
  },
};

const tmpA = new THREE.Color(), tmpB = new THREE.Color();
function mesajStanji(a, b, t) {
  const o = {};
  for (const k of Object.keys(a)) {
    if (typeof a[k] === 'string') {
      tmpA.set(a[k]); tmpB.set(b[k]);
      o[k] = tmpA.clone().lerp(tmpB, t);
    } else o[k] = lerp(a[k], b[k], t);
  }
  return o;
}

export class Atmosfera {
  constructor() {
    this.U = {
      uSonce: { value: new THREE.Vector3(0, 0.1, 1) },
      uZenit: { value: new THREE.Color() },
      uObzorje: { value: new THREE.Color() },
      uSij: { value: new THREE.Color() },
      uSoncBarva: { value: new THREE.Color() },
      uMeglaGost: { value: 0.002 },
      uMeglaVis: { value: 0.02 },
      uMeglaY0: { value: 0 },
      uMeglaMax: { value: 1 },
      uOblaki: { value: 0.4 },
      uCasN: { value: 0 },
      uZvezde: { value: 0 },
    };
    const mat = new THREE.ShaderMaterial({
      uniforms: this.U,
      vertexShader: /* glsl */`
        varying vec3 vSmer;
        void main() {
          vSmer = normalize((modelMatrix * vec4(position, 0.0)).xyz);
          vec4 p = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          gl_Position = p.xyww;
        }`,
      fragmentShader: GLSL_NEBO + /* glsl */`
        varying vec3 vSmer;
        void main() {
          vec3 d = normalize(vSmer);
          vec3 c = neboBarva(d, 1.0);
          // oblaki na ravnini 2,5 km, osvetljeni s strani sonca
          if (d.y > 0.01) {
            vec2 p = d.xz / d.y * 2.5 + vec2(uCasN * 0.004, uCasN * 0.0015);
            float n = nfbm(p * 0.55);
            float pokr = smoothstep(1.0 - uOblaki, 1.0 - uOblaki + 0.35, n);
            float mu = max(dot(d, uSonce), 0.0);
            vec3 oc = mix(uObzorje * 1.05, uSij * 1.2 + uZenit * 0.3, 0.35 + 0.65 * pow(mu, 4.0));
            oc = mix(oc, uZenit * 0.6 + uObzorje * 0.5, smoothstep(0.55, 0.95, n) * 0.5);
            c = mix(c, oc, pokr * smoothstep(0.01, 0.12, d.y) * 0.85);
          }
          // zvezde ponoči
          if (uZvezde > 0.0 && d.y > 0.0) {
            vec3 q = d * 420.0;
            vec3 iq = floor(q);
            float h = fract(sin(dot(iq, vec3(12.9898, 78.233, 37.719))) * 43758.5453);
            float z = step(0.9965, h) * smoothstep(0.5, 0.0, length(fract(q) - 0.5));
            c += vec3(0.9, 0.95, 1.0) * z * uZvezde * smoothstep(0.02, 0.25, d.y) * (0.5 + 2.0 * fract(h * 91.0));
          }
          gl_FragColor = vec4(c, 1.0);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`,
      side: THREE.BackSide,
      depthWrite: false,
      depthTest: true,
    });
    this.kupola = new THREE.Mesh(new THREE.SphereGeometry(1, 48, 24), mat);
    this.kupola.scale.setScalar(9000);
    this.kupola.frustumCulled = false;
    this.kupola.renderOrder = -1000;
    this.sonce = new THREE.DirectionalLight('#fff', 2);
    this.sonce.castShadow = true;
    this.sonce.shadow.bias = -0.0003;
    this.sonce.shadow.normalBias = 0.03;
    this.nebesna = new THREE.HemisphereLight('#bcd', '#554', 0.6);
    this.stanje = null;
  }

  // Doda zračno perspektivo materialu (ohrani morebitni lastni onBeforeCompile).
  // Lega v pogledu gre v svoji spremenljivki, ker je nekateri senčilniki
  // (črte, neosvetljeni) nimajo -- sicer bi jih pobelila nadomestna megla.
  popravi(m) {
    if (m.userData.atm || !('fog' in m) || m.isShaderMaterial) return;
    m.userData.atm = true;
    const prej = m.onBeforeCompile;
    const U = this.U;
    m.onBeforeCompile = (sh, r) => {
      if (prej) prej.call(m, sh, r);
      Object.assign(sh.uniforms, U);
      sh.vertexShader = sh.vertexShader
        .replace('#include <fog_pars_vertex>', '#include <fog_pars_vertex>\nvarying vec3 vAtmPog;')
        .replace('#include <fog_vertex>', '#include <fog_vertex>\nvAtmPog = mvPosition.xyz;');
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <fog_pars_fragment>', '#include <fog_pars_fragment>\nvarying vec3 vAtmPog;\n' + GLSL_NEBO)
        .replace('#include <fog_fragment>', '#ifdef USE_FOG\n gl_FragColor.rgb = atmosfera(gl_FragColor.rgb, cameraPosition, (vec4(vAtmPog, 0.0) * viewMatrix).xyz);\n#endif');
    };
    const kljuc = m.customProgramCacheKey.bind(m);
    m.customProgramCacheKey = () => kljuc() + '|atm';
    m.needsUpdate = true;
  }

  nastavi(a, b = null, t = 0) {
    const s = b ? mesajStanji(STANJA[a], STANJA[b], t) : mesajStanji(STANJA[a], STANJA[a], 0);
    const U = this.U;
    const el = THREE.MathUtils.degToRad(s.sonceVis), az = THREE.MathUtils.degToRad(s.sonceAz);
    U.uSonce.value.set(Math.sin(az) * Math.cos(el), Math.sin(el), -Math.cos(az) * Math.cos(el));
    U.uZenit.value.copy(s.zenit);
    U.uObzorje.value.copy(s.obzorje);
    U.uSij.value.copy(s.sij);
    U.uSoncBarva.value.copy(s.soncBarva);
    U.uMeglaGost.value = s.meglaGost;
    U.uMeglaVis.value = s.meglaVis;
    U.uMeglaY0.value = s.meglaY0;
    U.uMeglaMax.value = s.meglaMax;
    U.uOblaki.value = s.oblaki;
    U.uZvezde.value = s.zvezde;
    this.sonce.color.copy(s.sonceC);
    this.sonce.intensity = s.sonceI;
    this.nebesna.color.copy(s.nebZg);
    this.nebesna.groundColor.copy(s.nebSp);
    this.nebesna.intensity = s.nebI;
    this.stanje = s;
    return s;
  }

  // Okolje za odseve: kupola neba v kocko, nato PMREM. Drago (~20 ms),
  // zato samo ob menjavi poglavja.
  okolje(renderer) {
    const sc = new THREE.Scene();
    const k = this.kupola.clone();
    k.scale.setScalar(100);
    sc.add(k);
    // tla pod obzorjem, da odsev spodaj ni nebo
    const tla = new THREE.Mesh(new THREE.CircleGeometry(90, 32), new THREE.MeshBasicMaterial({ color: this.U.uObzorje.value.clone().multiplyScalar(0.35) }));
    tla.rotation.x = -Math.PI / 2; tla.position.y = -2;
    sc.add(tla);
    const pm = new THREE.PMREMGenerator(renderer);
    const tm = renderer.toneMapping;
    renderer.toneMapping = THREE.NoToneMapping;
    const rt = pm.fromScene(sc, 0, 0.1, 400);
    renderer.toneMapping = tm;
    pm.dispose();
    return rt.texture;
  }
}

