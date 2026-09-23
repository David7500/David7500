/* Ena pot, razložena po korakih -- in vodenje po njenih pešpoteh.
 *
 * Seznam predlogov odgovarja na „s čim in kdaj". Ta stran na **„kako"**: kod
 * hodiš do postajališča, kje izstopiš in kaj je vmes. Peš korak ima vodenje:
 * zemljevid od blizu in nagnjen, obrnjen v smer hoje, zgoraj naslednji zavoj,
 * spodaj koliko je še in ali ujameš vozilo.
 *
 * Pot je v naslovu, ne v seji: kdor jo komu pošlje, mu pošlje pot, ne svojega
 * brskalnika.
 */

const $ = (s) => document.querySelector(s);
const Q = new URLSearchParams(location.search);
// Hitrost na koncih poti: hoja ali kolo. Ista, s katero je strežnik računal
// minute -- druga bi dala vodenju drugo uro prihoda kot seznamu.
const KMH = Number(Q.get("kmh")) || 5;
const HITROST_MS = KMH / 3.6;
const KOLO = KMH > 7;

let K = null;
let PREDLOG = null;
let DATUM = null;
// Črte na zemljevidu po nogah: vodenje eno poudari, preračun eno zamenja.
const CRTE = [];

const ura = (ts) => new Date(ts * 1000).toLocaleTimeString("sl-SI",
  { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Ljubljana" });

function minute(s) {
  const m = Math.floor(s / 60 + 0.5);
  return m < 60 ? `${m} min` : `${Math.floor(m / 60)} h ${String(m % 60).padStart(2, "0")}`;
}

function dolzina(m) {
  if (m == null) return "";
  if (m < 20) return `${Math.max(5, Math.round(m / 5) * 5)} m`;
  return m < 950 ? `${Math.round(m / 10) * 10} m` : `${(m / 1000).toFixed(1).replace(".", ",")} km`;
}

// ---------------------------------------------------------------- znaki navodil

// Puščica zavoja: steblo gor, nato krak v smeri zavoja. Kot je glede na smer
// hoje, ne na sever -- "levo" je levo od tebe.
const ZNAK_KOT = {
  start: 0, naravnost: 0, "rahlo-desno": 45, desno: 90, "ostro-desno": 135,
  "rahlo-levo": -45, levo: -90, "ostro-levo": -135,
};

function znakSvg(znak, px = 30) {
  const ovoj = (telo) => `<svg width="${px}" height="${px}" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"
    aria-hidden="true">${telo}</svg>`;
  if (znak === "cilj") {
    return ovoj('<path d="M12 22s7-6.4 7-12a7 7 0 0 0-14 0c0 5.6 7 12 7 12z"/>'
      + '<circle cx="12" cy="10" r="2.4"/>');
  }
  if (znak === "krozisce") {
    return ovoj('<circle cx="12" cy="10" r="4.5"/><path d="M12 22v-7.5M16.2 7.6 20 4M16 4h4v4"/>');
  }
  if (znak === "nazaj") {
    return ovoj('<path d="M8 22V10a4 4 0 0 1 8 0v7"/><path d="M13 14l3 3 3-3"/>');
  }
  const r = (ZNAK_KOT[znak] || 0) * Math.PI / 180;
  const tx = 12 + 8 * Math.sin(r);
  const ty = 12 - 8 * Math.cos(r);
  const krak = (a) => `${(tx - 5 * Math.sin(r + a)).toFixed(2)} ${(ty + 5 * Math.cos(r + a)).toFixed(2)}`;
  return ovoj(`<path d="M12 22V12L${tx.toFixed(2)} ${ty.toFixed(2)}"/>`
    + `<path d="M${krak(0.65)}L${tx.toFixed(2)} ${ty.toFixed(2)}L${krak(-0.65)}"/>`);
}

// ---------------------------------------------------------------- izris korakov

// Brez podatka ni isto kot točno -- glej `pot.js`, isto pravilo.
function zamudaHtml(z, brez) {
  if (!z) return brez ? '<span class="zam zam-brez">brez podatka</span>' : "";
  const barva = delayColor(z);
  const vrsta = z.vrsta ? ` <span class="zam-vrsta">${escapeHtml(z.vrsta)}</span>` : "";
  return `<span class="zam" style="color:${barva};border-color:${barva}55">`
    + `${escapeHtml(delayText(z))}</span>${vrsta}`;
}

// Žeton ob izstopu samo takrat, kadar se od vstopnega res razlikuje -- dva
// enaka žetona v isti vrstici sta šum, dva različna pa edino, kar pojasni,
// zakaj je prihod za voznim redom, čeprav vstop ni bil.
function izstopHtml(n) {
  const a = delayMin(n.zamuda);
  const b = delayMin(n.zamuda_izstop);
  if (b == null || a === b) return "";
  return " " + zamudaHtml(n.zamuda_izstop);
}

// Kolo je samo na koncih poti; prestop na postaji je hoja s kolesom ob sebi.
function jeKolo(i) {
  return KOLO && (i === 0 || i === PREDLOG.noge.length - 1);
}

function kamBeseda(n) {
  return n.od === null ? "do postajališča" : n.do === null ? "do cilja" : "do prestopa";
}

function navodilaHtml(n) {
  const k = (n.koraki || []).filter((x) => x.znak !== "cilj");
  if (k.length < 2) return "";
  return `<details class="vmesni navodila">
      <summary>${k.length} ${sklon(k.length, "navodilo")}</summary>
      <ol>${k.map((x) => `<li>${znakSvg(x.znak, 14)}<span>${escapeHtml(x.besedilo)}${
        x.ulica ? ` <span class="nav-ulica">${escapeHtml(x.ulica)}</span>` : ""}</span>
        <span class="nav-m">${dolzina(x.metri)}</span></li>`).join("")}</ol>
    </details>`;
}

function hojaHtml(n, i) {
  const od = n.od ? escapeHtml(n.od) : "izhodišče";
  const kam = n.do ? escapeHtml(n.do) : "cilj";
  // Kadar usmerjevalnika ni, poti nismo izračunali in tega ne skrivamo:
  // ravna črta na zemljevidu bi trdila pot, ki je ni.
  const opomba = n.tocke ? "" :
    '<span class="korak-opomba">pešpot ni izračunana — na zemljevidu je zračna črta</span>';
  return `<li class="korak je-hoja">
    <span class="korak-znak" aria-hidden="true">↓</span>
    <div class="korak-telo">
      <div class="korak-vrh">${jeKolo(i) ? "s kolesom" : "peš"} <strong>${
        minute(n.sekunde)}</strong>${n.metri ? ` · ${dolzina(n.metri)}` : ""}</div>
      <div class="korak-kam">${od} → ${kam}</div>
      ${opomba}
      <div class="korak-gumbi">
        <button type="button" class="vodi-gumb" data-vodi="${i}">
          <svg width="12" height="12" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 2 20 21 12 16.5 4 21Z" fill="currentColor"/></svg>
          vodi me ${kamBeseda(n)}</button>
        <button type="button" class="hoja-gumb" data-korak="${i}">pokaži</button>
      </div>
      ${navodilaHtml(n)}
    </div></li>`;
}

function voznjaHtml(n) {
  const pot = n.network === "avtobus" ? "bus" : "train";
  const okno = `/app/${pot}/${encodeURIComponent(n.train_no)}?trip=${encodeURIComponent(n.trip_id)}`;
  const odh = n.odhod_ocena || n.odhod;
  const prih = n.prihod_ocena || n.prihod;
  const vr = n.odhod_ocena && n.odhod_ocena !== n.odhod
    ? `<div class="korak-opomba">vozni red ${ura(n.odhod)} → ${ura(n.prihod)}</div>` : "";
  // Vmesni postanki so zaprti: potnika najprej zanima, kje izstopi, in šele
  // potem, kaj je vmes. Prvi in zadnji sta v vrsticah nad in pod, zato ju tu ni.
  const vmes = n.postanki.slice(1, -1);
  const seznam = vmes.length ? `<details class="vmesni">
      <summary>${vmes.length} ${sklon(vmes.length, "postanek")} vmes</summary>
      <ol>${vmes.map((s) => `<li><span class="vm-ura">${
        s.prihod ? ura(s.prihod) : "—"}</span> ${escapeHtml(s.ime)}</li>`).join("")}</ol>
    </details>` : "";
  const kdo = AGENCY[n.agency] ? `${AGENCY[n.agency]} ${n.train_no}` : n.train_no;
  return `<li class="korak je-voznja">
    <span class="korak-znak" aria-hidden="true">●</span>
    <div class="korak-telo">
      <div class="korak-vrh">
        <a class="noga-linija" href="${okno}">${escapeHtml(kdo)}</a>
        ${zamudaHtml(n.zamuda, n.brez_podatka)}
        ${n.headsign ? `<span class="korak-smer">→ ${escapeHtml(n.headsign)}</span>` : ""}
      </div>
      <div class="korak-vstop"><strong>${ura(odh)}</strong> ${escapeHtml(n.od)}</div>
      ${seznam}
      <div class="korak-izstop"><strong>${ura(prih)}</strong> ${escapeHtml(n.do)}
        <span class="korak-kam">izstop</span>${izstopHtml(n)}</div>
      ${vr}
    </div></li>`;
}

// Prestop stoji MED vožnjama, ki ju veže. Brez rezerve je "prestop" samo
// beseda; z njo je odgovor na edino vprašanje, ki ga potnik tam ima.
function prestopHtml(t, pred, po) {
  const mins = preostanekPrestopa(t.nacrtovano_s, pred && pred.zamuda, po && po.zamuda);
  const nacrt = Math.floor(t.nacrtovano_s / 60 + 0.5);
  const barva = mins == null ? "var(--ink-mute)"
    : mins < 2 ? "var(--sev-bad)" : mins < 5 ? "var(--sev-hard)" : "var(--ok)";
  const pes = t.pes_s >= 60 ? ` · ${minute(t.pes_s)} hoje vmes` : "";
  return `<li class="korak je-prestop">
    <span class="korak-znak" aria-hidden="true">⇄</span>
    <div class="korak-telo" style="color:${barva}">
      ${escapeHtml(mins == null ? `${nacrt} min za prestop` : prestopText(mins))}
      <span class="korak-kam">v ${escapeHtml(t.kje)}${pes}${
        mins == null ? " · brez zamud" : ""}</span>
    </div></li>`;
}

function korakiHtml(p) {
  const voznje = p.noge.filter((n) => n.vrsta === "voznja");
  const out = [];
  p.noge.forEach((n, i) => {
    const v = voznje.indexOf(n);
    if (v > 0 && p.prestopi && p.prestopi[v - 1]) {
      out.push(prestopHtml(p.prestopi[v - 1], voznje[v - 1], n));
    }
    out.push(n.vrsta === "hoja" ? hojaHtml(n, i) : voznjaHtml(n));
  });
  return out.join("");
}

// ---------------------------------------------------------------- zemljevid

function odKod() { return [Number(Q.get("od_lat")), Number(Q.get("od_lon"))]; }
function doKod() { return [Number(Q.get("do_lat")), Number(Q.get("do_lon"))]; }

function risiCrte() {
  if (!K) return;
  pkVir(K.map, "k-pot", CRTE.map((c, i) => {
    if (!c) return null;
    const aktivna = V.aktivno && i === V.i;
    const odmaknjena = V.aktivno && !aktivna;
    return pkCrta(c.tocke, {
      vrsta: c.vrsta,
      prosojnost: odmaknjena ? 0.3 : c.skica ? 0.55 : 0.92,
      sirina: aktivna ? 7 : 4,
    });
  }).filter(Boolean));
}

function narisi(p) {
  CRTE.length = 0;
  p.noge.forEach((n, i) => {
    if (n.vrsta === "hoja") {
      const t = n.tocke && n.tocke.length > 1 ? n.tocke : [n.od_ll, n.do_ll];
      CRTE[i] = t[0] && t[1] ? { vrsta: "hoja", tocke: t } : null;
    } else {
      CRTE[i] = { vrsta: "voznja", tocke: [n.od_ll, n.do_ll], skica: true };
    }
  });
  if (!K) return;
  // Postajališča vstopa in izstopa. Polna modra je samo "ti", izhodišče je
  // prazen obroč, postajališče obroč v barvi vožnje, cilj polna oranžna.
  const f = [];
  for (const n of p.noge) {
    if (n.vrsta !== "voznja") continue;
    if (n.od_ll) f.push(pkTocka(n.od_ll, { vrsta: "postaja", ime: n.od }));
    if (n.do_ll) f.push(pkTocka(n.do_ll, { vrsta: "postaja", ime: n.do }));
  }
  f.push(pkTocka(odKod(), { vrsta: "izhodisce", ime: "izhodišče" }));
  f.push(pkTocka(doKod(), { vrsta: "cilj", ime: "cilj" }));
  pkVir(K.map, "k-tocke", f);
  risiCrte();
  if (!V.aktivno) priblizaj(null, false);
  (async () => {
    for (let i = 0; i < p.noge.length; i += 1) {
      const n = p.noge[i];
      if (n.vrsta !== "voznja") continue;
      const t = await trasa(n).catch(() => null);
      if (t) CRTE[i] = { vrsta: "voznja", tocke: t };
      else CRTE[i].skica = false;
      risiCrte();
    }
  })();
}

/** Približaj na eno nogo (ali na vso pot, kadar je `i` `null`). */
function priblizaj(i, pomakni = true) {
  if (!K) return;
  const tocke = i === null
    ? CRTE.filter(Boolean).flatMap((c) => c.tocke).concat([odKod(), doKod()])
    : (CRTE[i] ? CRTE[i].tocke : []);
  pkPrilagodi(K.map, tocke, { maxZoom: i === null ? 16 : 17, padding: 40, bearing: 0,
                              animate: pomakni });
  document.querySelectorAll(".hoja-gumb[data-korak]").forEach((b) =>
    b.classList.toggle("je-on", Number(b.dataset.korak) === i));
  $("#cela").hidden = i === null;
  // Na telefonu je zemljevid pod seznamom; gumb brez tega premakne pogled
  // nekam, česar se ne vidi.
  if (pomakni) $("#karta").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// Čez celo STRAN, ne čez cel zaslon -- isti razlog kot pri oknu vožnje:
// fullscreen skrije naslovno vrstico, gumb nazaj in vsak drug orientir, izhod
// pa je tipka, ki je na telefonu ni.
$("#karta-max").addEventListener("click", () => {
  const veliko = !document.body.classList.contains("karta-velika");
  document.body.classList.toggle("karta-velika", veliko);
  $("#karta-max").setAttribute("aria-pressed", String(veliko));
  $("#karta-max").title = veliko ? "Pomanjšaj zemljevid" : "Zemljevid čez celo stran";
  requestAnimationFrame(() => K && K.map.resize());
});

// ---------------------------------------------------------------- lega in smer

let JAZ = null;
let ustaviSledenje = null;
// Smer telefona (kompas), kadar jo pozna. Brez nje se zemljevid pri vodenju
// obrne po poti, ne po telefonu.
let KOMPAS = null;

function obLegi(loc) {
  JAZ = loc;
  if (K) pkJaz(K.map, loc);
  $("#karta-lega").classList.add("je-on");
  posodobi(false);
}

let lega = null;
function zacniLego() {
  if (lega) return lega;
  $("#karta-lega").classList.add("je-iskanje");
  lega = locateMe({ napredek: obLegi }).then((loc) => {
    obLegi(loc);
    // Med hojo je edino vprašanje "grem v pravo smer". Zato lega sledi in se
    // ne izmeri enkrat: prvi popravek GPS pogosto zgreši za sto metrov.
    ustaviSledenje = sledi(obLegi);
    return loc;
  }).catch((e) => {
    lega = null;
    throw e;
  }).finally(() => $("#karta-lega").classList.remove("je-iskanje"));
  return lega;
}

function poslusajSmer() {
  const obdelaj = (e) => {
    let h = null;
    if (typeof e.webkitCompassHeading === "number") h = e.webkitCompassHeading;   // iOS
    else if (e.absolute && e.alpha != null) h = 360 - e.alpha;
    if (h == null) return;
    const zaslon = (screen.orientation && screen.orientation.angle) || 0;
    KOMPAS = (h + zaslon) % 360;
  };
  // `deviceorientationabsolute` je proti severu; navaden `deviceorientation`
  // v Chromu je proti legi ob nalaganju in bi kazal naključno smer.
  if ("ondeviceorientationabsolute" in window) {
    window.addEventListener("deviceorientationabsolute", obdelaj);
  } else {
    window.addEventListener("deviceorientation", obdelaj);
  }
}

let smerProsena = false;
// iOS da smer neba samo na izrecno prošnjo iz dotika -- klic mora biti pred
// prvim `await` v poslušalcu klika.
function prosiZaSmer() {
  if (smerProsena) return;
  smerProsena = true;
  if (typeof DeviceOrientationEvent !== "undefined"
      && typeof DeviceOrientationEvent.requestPermission === "function") {
    DeviceOrientationEvent.requestPermission().then((o) => {
      if (o === "granted") poslusajSmer();
    }).catch(() => {});
  } else {
    poslusajSmer();
  }
}

$("#karta-lega").addEventListener("click", async () => {
  prosiZaSmer();
  try {
    const loc = await zacniLego();
    if (K && !V.aktivno) {
      K.map.easeTo({ center: [loc.lon, loc.lat], zoom: Math.max(K.map.getZoom(), 16 - PK_LZ) });
    }
  } catch (e) {
    $("#stanje").textContent = e.message;
    $("#stanje").className = "pot-stanje je-napaka";
  }
});

// ---------------------------------------------------------------- geometrija

function metri(a, b) {
  const r = Math.PI / 180;
  const s = Math.sin((b[0] - a[0]) * r / 2) ** 2
    + Math.cos(a[0] * r) * Math.cos(b[0] * r) * Math.sin((b[1] - a[1]) * r / 2) ** 2;
  return 12742000 * Math.asin(Math.sqrt(s));
}

function azimut(a, b) {
  const r = Math.PI / 180;
  const dl = (b[1] - a[1]) * r;
  const y = Math.sin(dl) * Math.cos(b[0] * r);
  const x = Math.cos(a[0] * r) * Math.sin(b[0] * r)
    - Math.sin(a[0] * r) * Math.cos(b[0] * r) * Math.cos(dl);
  return (Math.atan2(y, x) / r + 360) % 360;
}

function kumulativa(t) {
  const k = [0];
  for (let i = 1; i < t.length; i += 1) k.push(k[i - 1] + metri(t[i - 1], t[i]));
  return k;
}

/** Najbližja točka na poti: koliko je prehojeno in kako daleč je pot. */
function projekcija(t, kum, p) {
  const kx = 111320 * Math.cos(p[0] * Math.PI / 180);
  const ky = 110540;
  let naj = { odmik: Infinity, vzdolz: 0 };
  for (let i = 0; i < t.length - 1; i += 1) {
    const ax = (t[i][1] - p[1]) * kx, ay = (t[i][0] - p[0]) * ky;
    const bx = (t[i + 1][1] - p[1]) * kx, by = (t[i + 1][0] - p[0]) * ky;
    const dx = bx - ax, dy = by - ay;
    const l2 = dx * dx + dy * dy;
    const u = l2 ? Math.max(0, Math.min(1, -(ax * dx + ay * dy) / l2)) : 0;
    const d = Math.hypot(ax + u * dx, ay + u * dy);
    if (d < naj.odmik) naj = { odmik: d, vzdolz: kum[i] + u * (kum[i + 1] - kum[i]) };
  }
  return naj;
}

function tockaNa(t, kum, m) {
  if (m <= 0) return t[0];
  for (let i = 1; i < t.length; i += 1) {
    if (kum[i] >= m) {
      const u = (m - kum[i - 1]) / Math.max(1e-9, kum[i] - kum[i - 1]);
      return [t[i - 1][0] + u * (t[i][0] - t[i - 1][0]), t[i - 1][1] + u * (t[i][1] - t[i - 1][1])];
    }
  }
  return t[t.length - 1];
}

// ---------------------------------------------------------------- vodenje
//
// Kamera za hrbtom: zemljevid od blizu in nagnjen (Leafletov z18 je 60°),
// obrnjen v smer hoje, tvoja lega v spodnji tretjini -- pred tabo je več
// poti kot za tabo. Zgoraj je samo naslednji zavoj, spodaj koliko je še in
// ali ujameš vozilo.

const V = {
  aktivno: false, i: -1, tocke: [], kum: [], koraki: [],
  sledi: true, izven: 0, preracun: 0, najavljen: -1, prispel: false,
  listaj: 0, puscica: null, zaklep: null, osvezi: null, zacel: false,
};

// Dokler nisi bil na poti, je nisi začel: "vodi me do cilja" se pogosto
// pritisne še na vlaku. Takrat pot ni "zašla", ampak je pred tabo -- pokaže se
// njen začetek, preračuna pa ni.
const NA_POTI_M = 60;
const DALEC_M = 150;

// Odmik od poti, pri katerem je človek zares drugje in ne le GPS v šumu.
const IZVEN_M = 35;
// Kako pogosto sme preračun vprašati strežnik: zavoj v napačno ulico ne sme
// sprožiti deset zahtev v desetih sekundah.
const PRERACUN_MS = 20000;

function nogaVozila(i) {
  const n = PREDLOG.noge[i + 1];
  return n && n.vrsta === "voznja" ? n : null;
}

/** Naslednji peš korak po vožnji, ki sledi tej hoji: "ko izstopiš, vodi me naprej". */
function naslednjaHoja(i) {
  for (let j = i + 1; j < PREDLOG.noge.length; j += 1) {
    if (PREDLOG.noge[j].vrsta === "hoja" && PREDLOG.noge[j - 1].vrsta === "voznja") return j;
  }
  return null;
}

function pripraviNogo(i) {
  const n = PREDLOG.noge[i];
  V.i = i;
  V.tocke = CRTE[i] ? CRTE[i].tocke : [n.od_ll || odKod(), n.do_ll || doKod()];
  V.kum = kumulativa(V.tocke);
  V.koraki = (n.koraki || []).slice();
  V.prispel = false;
  V.izven = 0;
  V.najavljen = -1;
  V.listaj = 0;
  V.zacel = false;
}

function zacniVodenje(i) {
  prosiZaSmer();
  pripraviNogo(i);
  V.aktivno = true;
  V.sledi = true;
  document.body.classList.add("vodenje");
  $("#vod-manever").hidden = false;
  $("#vod-spodaj").hidden = false;
  zakleniZaslon();
  risiCrte();
  requestAnimationFrame(() => {
    if (K) K.map.resize();
    posodobi(true);
  });
  zacniLego().catch((e) => {
    $("#vod-opomba").textContent = e.message;
  });
  clearInterval(V.osvezi);
  // Ura teče tudi, ko stojiš: odštevanje do odhoda se mora premikati samo.
  V.osvezi = setInterval(() => posodobi(false, true), 5000);
  osveziZamude();
}

function koncajVodenje() {
  V.aktivno = false;
  clearInterval(V.osvezi);
  document.body.classList.remove("vodenje");
  $("#vod-manever").hidden = true;
  $("#vod-spodaj").hidden = true;
  if (V.puscica) { V.puscica.remove(); V.puscica = null; }
  if (K && K.map.getLayer("k-jaz")) K.map.setLayoutProperty("k-jaz", "visibility", "visible");
  if (V.zaklep) { V.zaklep.release().catch(() => {}); V.zaklep = null; }
  risiCrte();
  requestAnimationFrame(() => {
    if (K) K.map.resize();
    priblizaj(V.i, false);
  });
}

// Zaslon med vodenjem ne sme ugasniti -- telefon v roki, ki se po pol minute
// zatemni, ni vodenje. Kjer brskalnik tega ne zna, ostane privzeto.
async function zakleniZaslon() {
  try {
    if ("wakeLock" in navigator && !V.zaklep) V.zaklep = await navigator.wakeLock.request("screen");
  } catch (e) { /* baterija ali pravilnik: brez zaklepa */ }
}
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible" && V.aktivno) {
    V.zaklep = null;
    zakleniZaslon();
  }
});

/** Smer kamere: smer gibanja iz GPS med hojo, sicer kompas, sicer pot sama.
 *  Pri listanju je smer vedno pot -- telefon v roki doma ne gleda po ulici. */
function smerKamere(vzdolz, vodim) {
  if (vodim && JAZ.smer != null && !Number.isNaN(JAZ.smer) && (JAZ.hitrost || 0) > 0.7) {
    return JAZ.smer;
  }
  if (vodim && KOMPAS != null) return KOMPAS;
  const a = tockaNa(V.tocke, V.kum, vzdolz);
  const b = tockaNa(V.tocke, V.kum, vzdolz + 25);
  return metri(a, b) > 1 ? azimut(a, b) : (K ? K.map.getBearing() : 0);
}

function puscica(ll, smer) {
  if (!K) return;
  if (!V.puscica) {
    const el = document.createElement("div");
    el.className = "vod-jaz";
    el.innerHTML = `<svg width="30" height="30" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="10" fill="${ME_COLOR}" stroke="#fff" stroke-width="2"/>
      <path d="M12 5.5 16.5 16 12 13.4 7.5 16Z" fill="#fff"/></svg>`;
    V.puscica = new K.ml.Marker({ element: el, rotationAlignment: "map",
                                  pitchAlignment: "map" });
    V.puscica.setLngLat([ll[1], ll[0]]).addTo(K.map);
    // Pika pod puščico bi bila druga "ti" na isti točki.
    K.map.setLayoutProperty("k-jaz", "visibility", "none");
  }
  V.puscica.setLngLat([ll[1], ll[0]]).setRotation(smer);
}

function voziloHtml(nv, ostaneS) {
  const kdo = AGENCY[nv.agency] ? `${AGENCY[nv.agency]} ${nv.train_no}` : nv.train_no;
  const odh = nv.odhod_ocena || nv.odhod;
  const zam = nv.zamuda ? " " + zamudaHtml(nv.zamuda) : "";
  let vrstica = `<strong>${escapeHtml(kdo)}</strong> ${
    nv.headsign ? `→ ${escapeHtml(nv.headsign)} ` : ""}odpelje ob <strong>${ura(odh)}</strong>${zam}`;
  // Odštevanje samo za danes: za jutrišnjo pot je "čez 1 080 minut" šum.
  if (DATUM !== todayIso()) return vrstica;
  const cez = odh - Date.now() / 1000;
  const rezerva = cez - ostaneS;
  if (cez < -60) return vrstica + ' · <span class="vod-stanje je-slabo">je že odpeljal</span>';
  const razred = rezerva < 0 ? "je-slabo" : rezerva < 180 ? "je-tesno" : "je-dobro";
  const beseda = rezerva < 0 ? `pohiti — ${minute(-rezerva)} premalo`
    : rezerva < 60 ? "brez rezerve" : `${minute(rezerva)} rezerve`;
  return `${vrstica} · čez ${minute(Math.max(0, cez))}`
    + ` <span class="vod-stanje ${razred}">${beseda}</span>`;
}

function prikaziManever(k, razdalja) {
  const n = PREDLOG.noge[V.i];
  $("#vod-znak").innerHTML = znakSvg(k ? k.znak : "naravnost", 38);
  $("#vod-razdalja").textContent = razdalja;
  // Konec poti ni "na cilju", dokler nisi tam: pove, kaj te čaka.
  if (k && k.znak === "cilj") {
    $("#vod-navodilo").textContent = n.do ? "Postajališče" : "Cilj";
    $("#vod-ulica").textContent = n.do || "";
    return;
  }
  $("#vod-navodilo").textContent = k ? k.besedilo : "Naravnost";
  $("#vod-ulica").textContent = k ? k.ulica : "";
}

function cas(s) {
  return s < 45 ? "manj kot minuto" : minute(s);
}

function posodobi(skok, samoBesedilo) {
  if (!V.aktivno || !PREDLOG) return;
  const n = PREDLOG.noge[V.i];
  const skupaj = V.kum[V.kum.length - 1] || 0;
  let vzdolz = 0;
  let odmik = null;
  if (JAZ) {
    const p = projekcija(V.tocke, V.kum, [JAZ.lat, JAZ.lon]);
    vzdolz = p.vzdolz;
    odmik = p.odmik;
    if (odmik <= NA_POTI_M) V.zacel = true;
  }
  // Daleč od poti, ki je še nisi začel: kot brez lege -- listaš po navodilih.
  const dalec = JAZ && !V.zacel && odmik > DALEC_M;
  const vodim = JAZ && !dalec;
  if (dalec) vzdolz = 0;
  const ostane = Math.max(0, skupaj - vzdolz);
  const konec = V.tocke[V.tocke.length - 1];
  const doKonca = JAZ ? metri([JAZ.lat, JAZ.lon], konec) : Infinity;
  // Prispel si, ko je konec bližje od točnosti lege -- a vsaj 15 m, sicer bi
  // GPS v mestu tu in tam "prispel" dvajset metrov pred postajo.
  const prag = Math.max(15, Math.min(JAZ ? JAZ.acc || 15 : 15, 35));
  if (JAZ && (doKonca <= prag || (ostane <= prag && odmik < IZVEN_M))) {
    if (!V.prispel && navigator.vibrate) navigator.vibrate([120, 80, 120]);
    V.prispel = true;
  }
  const nv = nogaVozila(V.i);
  const ostaneS = ostane / HITROST_MS;

  $("#vod-listaj").hidden = vodim || V.koraki.length < 2;
  if (V.prispel) {
    $("#vod-znak").innerHTML = znakSvg("cilj", 38);
    $("#vod-razdalja").textContent = "";
    $("#vod-navodilo").textContent = n.do ? "Tu je postajališče" : "Na cilju si";
    $("#vod-ulica").textContent = n.do || "";
    $("#vod-cilj").textContent = "";
  } else if (vodim) {
    const k = V.koraki.find((x) => x.znak !== "start" && x.od_zacetka > vzdolz + 3);
    const d = k ? k.od_zacetka - vzdolz : ostane;
    const ki = k ? V.koraki.indexOf(k) : -1;
    // Tresljaj tik pred zavojem: pogled na zaslon ni vedno mogoč.
    if (k && d < 20 && V.najavljen !== ki && k.znak !== "cilj") {
      V.najavljen = ki;
      if (navigator.vibrate) navigator.vibrate(60);
    }
    prikaziManever(k, d < 12 ? "zdaj" : `čez ${dolzina(d)}`);
    $("#vod-cilj").innerHTML = `${n.do ? "Do postajališča" : "Do cilja"} <strong>${
      escapeHtml(n.do || "")}</strong> · ${dolzina(ostane)} · ${cas(ostaneS)}`;
  } else {
    const k = V.koraki[V.listaj];
    prikaziManever(k, V.koraki.length ? `${V.listaj + 1} / ${V.koraki.length}` : "");
    $("#vod-cilj").innerHTML = `${n.do ? "Do postajališča" : "Do cilja"} <strong>${
      escapeHtml(n.do || "")}</strong> · ${dolzina(skupaj)} · ${cas(skupaj / HITROST_MS)}`;
  }
  $("#vod-vozilo").innerHTML = nv ? voziloHtml(nv, V.prispel ? 0 : ostaneS) : "";
  $("#vod-vozilo").hidden = !nv;

  // Kaj po tem: ob vozilu "ko izstopiš, vodi me naprej", na cilju konec.
  const dalje = naslednjaHoja(V.i);
  $("#vod-dalje").hidden = !(V.prispel && dalje !== null);
  if (dalje !== null) {
    $("#vod-dalje").textContent = `ko izstopiš: vodi me ${kamBeseda(PREDLOG.noge[dalje])}`;
    $("#vod-dalje").dataset.vodi = dalje;
  }
  $("#vod-konec").textContent = V.prispel && dalje === null ? "končano" : "končaj";
  $("#vod-sledi").hidden = V.sledi || !vodim;
  const opomba = $("#vod-opomba");
  if (dalec) {
    opomba.textContent = `Pot se začne ${dolzina(metri([JAZ.lat, JAZ.lon], V.tocke[0]))}`
      + ` od tebe${n.od ? ` (${n.od})` : ""} — do takrat lahko listaš po navodilih.`;
  } else if (!JAZ && !opomba.textContent) {
    opomba.textContent = "Čakam na tvojo lego … medtem lahko listaš po navodilih.";
  } else if (JAZ && opomba.dataset.trajno !== "1") {
    opomba.textContent = "";
  }

  if (samoBesedilo || !K) return;
  const kje = vodim ? [JAZ.lat, JAZ.lon]
    : (V.koraki[V.listaj] && V.koraki[V.listaj].ll) || V.tocke[0];
  const od = vodim ? vzdolz : (V.koraki[V.listaj] ? V.koraki[V.listaj].od_zacetka : 0);
  const smer = smerKamere(od, vodim);
  if (JAZ) puscica([JAZ.lat, JAZ.lon], vodim ? smer : (JAZ.smer ?? KOMPAS ?? 0));
  if (V.sledi) {
    const h = K.map.getContainer().clientHeight;
    K.map.easeTo({
      center: [kje[1], kje[0]], bearing: smer, zoom: 17.3 - PK_LZ,
      // Lega v spodnji tretjini: pred tabo je več poti kot za tabo.
      padding: { top: Math.round(h * 0.38), bottom: 0, left: 0, right: 0 },
      duration: skok ? 900 : 700,
    });
  }

  // Zašel: odmik večji od točnosti in od praga, dvakrat zapored -- en sam
  // skok GPS ni razlog za novo pot.
  if (vodim && V.zacel && !V.prispel && odmik > Math.max(IZVEN_M, JAZ.acc || 0)
      && (JAZ.acc || 0) < 60) {
    V.izven += 1;
    if (V.izven >= 2 && Date.now() - V.preracun > PRERACUN_MS) preracunaj();
  } else {
    V.izven = 0;
  }
}

async function preracunaj() {
  V.preracun = Date.now();
  const konec = V.tocke[V.tocke.length - 1];
  const p = new URLSearchParams({ od_lat: JAZ.lat.toFixed(6), od_lon: JAZ.lon.toFixed(6),
                                  do_lat: konec[0].toFixed(6), do_lon: konec[1].toFixed(6),
                                  kmh: KMH });
  try {
    const r = await fetch(`/api/pot/hoja?${p}`);
    if (!r.ok) return;
    const d = await r.json();
    if (!V.aktivno || !d.tocke || d.tocke.length < 2) return;
    CRTE[V.i] = { vrsta: "hoja", tocke: d.tocke };
    V.tocke = d.tocke;
    V.kum = kumulativa(d.tocke);
    V.koraki = d.koraki || [];
    V.najavljen = -1;
    V.izven = 0;
    // Nova pot se začne na najbližji poti, ki je lahko tudi 60 m stran (sredi
    // travnika). Dokler nisi na njej, je "nisi začel" -- sicer bi jo odmik
    // vsakih dvajset sekund preračunal znova.
    V.zacel = false;
    risiCrte();
    const op = $("#vod-opomba");
    op.textContent = "Pot je preračunana od tu.";
    op.dataset.trajno = "1";
    setTimeout(() => { op.dataset.trajno = ""; op.textContent = ""; }, 5000);
    posodobi(false);
  } catch (e) { /* brez omrežja ostane stara pot */ }
}

// Zamude se med hojo spreminjajo; odštevanje do odhoda mora slediti. Hoja
// sama se ne osvežuje -- preračunana pot bi se sicer vrnila na staro.
async function osveziZamude() {
  if (!V.aktivno || DATUM !== todayIso()) return;
  try {
    const r = await fetch(`/api/pot/podrobno?${naslovPodrobno()}`);
    if (r.ok) {
      const d = await r.json();
      d.predlog.noge.forEach((n, i) => {
        const moja = PREDLOG.noge[i];
        if (n.vrsta !== "voznja" || !moja || moja.trip_id !== n.trip_id) return;
        for (const k of ["zamuda", "zamuda_izstop", "odhod_ocena", "prihod_ocena", "brez_podatka"]) {
          moja[k] = n[k];
        }
      });
      posodobi(false, true);
    }
  } catch (e) { /* naslednjič */ }
  if (V.aktivno) setTimeout(osveziZamude, 30000);
}

$("#vod-konec").addEventListener("click", koncajVodenje);
$("#vod-sledi").addEventListener("click", () => { V.sledi = true; posodobi(true); });
$("#vod-dalje").addEventListener("click", () => zacniVodenje(Number($("#vod-dalje").dataset.vodi)));
$("#vod-prej").addEventListener("click", () => {
  V.listaj = Math.max(0, V.listaj - 1);
  V.sledi = true;
  posodobi(true);
});
$("#vod-naprej").addEventListener("click", () => {
  V.listaj = Math.min(V.koraki.length - 1, V.listaj + 1);
  V.sledi = true;
  posodobi(true);
});

// ---------------------------------------------------------------- nalaganje

function naslovPodrobno() {
  const p = new URLSearchParams();
  for (const k of ["noge", "od_lat", "od_lon", "do_lat", "do_lon", "date", "kmh"]) {
    if (Q.get(k)) p.set(k, Q.get(k));
  }
  return p;
}

function nazajUrl() {
  const q = new URLSearchParams();
  const t = (a, b) => `${Number(Q.get(a)).toFixed(5)},${Number(Q.get(b)).toFixed(5)}`;
  if (Q.get("od_lat")) q.set("od", t("od_lat", "od_lon"));
  if (Q.get("do_lat")) q.set("do", t("do_lat", "do_lon"));
  // Nazaj na isto vprašanje: rok, dan in kolo so del njega.
  if (Q.get("tam")) q.set("tam", Q.get("tam"));
  if (Q.get("date")) q.set("dan", Q.get("date"));
  if (KOLO) q.set("kolo", "1");
  return q.toString() ? `/app/pot?${q}` : "/app/pot";
}

async function nalozi() {
  $("#nazaj").href = nazajUrl();
  const p = naslovPodrobno();
  if (!p.get("noge")) {
    $("#stanje").textContent = "Poti v naslovu ni.";
    $("#stanje").className = "pot-stanje je-napaka";
    return;
  }
  $("#stanje").textContent = "Nalagam …";
  try {
    const r = await fetch(`/api/pot/podrobno?${p}`);
    if (!r.ok) {
      const telo = await r.json().catch(() => ({}));
      throw new Error(telo.detail || `strežnik je vrnil ${r.status}`);
    }
    const d = await r.json();
    const pr = d.predlog;
    PREDLOG = pr;
    DATUM = d.datum;
    $("#stanje").textContent = "";
    $("#glava").innerHTML = `
      <div class="podr-ure"><strong>${ura(pr.odhod_ocena || pr.odhod)}</strong>
        → <strong>${ura(pr.prihod_ocena || pr.prihod)}</strong></div>
      <div class="podr-meta">${minute(pr.trajanje_s)}${
        pr.hoje_s >= 60 ? ` · ${minute(pr.hoje_s)} ${KOLO ? "do postaj" : "hoje"}` : ""} · ${
        pr.prestopov === 0 ? "brez prestopa"
          : `${pr.prestopov} ${sklon(pr.prestopov, "prestop")}`} · ${dayLabel(d.datum)}</div>`;
    $("#koraki").innerHTML = korakiHtml(pr);
    narisi(pr);
    $("#koraki").addEventListener("click", (e) => {
      const v = e.target.closest("[data-vodi]");
      if (v) { zacniVodenje(Number(v.dataset.vodi)); return; }
      const b = e.target.closest(".hoja-gumb[data-korak]");
      if (b) priblizaj(Number(b.dataset.korak));
    });
    $("#cela").addEventListener("click", () => priblizaj(null));
  } catch (e) {
    $("#stanje").textContent = e.message;
    $("#stanje").className = "pot-stanje je-napaka";
  }
}

nalozi();
pkUstvari($("#karta")).then((k) => {
  if (!k) {
    document.body.classList.add("brez-zemljevida");
    $("#karta").innerHTML = '<p class="ni-zemljevida">Ta brskalnik zemljevida ne zna narisati.'
      + " Koraki in navodila delajo tudi brez njega.</p>";
    return;
  }
  K = k;
  K.map.addControl(new K.ml.NavigationControl({ visualizePitch: true }), "top-left");
  // Kdor zemljevid premakne s prstom, hoče pogledati drugam: kamera mu ne sme
  // skočiti nazaj ob naslednjem popravku lege. "Sledi mi" jo vrne.
  K.map.on("dragstart", (e) => {
    if (V.aktivno && e.originalEvent) { V.sledi = false; $("#vod-sledi").hidden = !JAZ; }
  });
  if (JAZ) pkJaz(K.map, JAZ);
  if (PREDLOG) narisi(PREDLOG);
});
