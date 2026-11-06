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
// Pot, na kateri si (`NA_POTI` v common.js): `?na-poti` jo vzame iz shrambe,
// ne iz naslova -- trak na drugih straneh vodi sem brez vsega drugega. Kar
// bere naslov spodaj (kraja, dan, hitrost), dobi njene vrednosti.
const NA_POTI_NACIN = Q.has("na-poti");
const AKTIVNA = NA_POTI_NACIN ? NA_POTI.beri() : null;
if (AKTIVNA) {
  for (const [k, v] of Object.entries(AKTIVNA.spec)) if (v != null) Q.set(k, String(v));
  if (AKTIVNA.vprasanje && AKTIVNA.vprasanje.rok) Q.set("rok", String(AKTIVNA.vprasanje.rok));
}
// Hitrost na koncih poti: hoja ali kolo. Ista, s katero je strežnik računal
// minute -- druga bi dala vodenju drugo uro prihoda kot seznamu.
const KMH = Number(Q.get("kmh")) || 5;
const KOLO = KMH > 7;

let K = null;
let PREDLOG = null;
// Ali je pot "zdaj": samo takrat ima smisel odštevati do odhoda in osveževati
// zamude. Pove strežnik -- prej je stran sklepala iz "dan je danes", in nočna
// vožnja, ki nosi včerajšnji prometni dan, je ostala brez obojega.
let ZIVO = false;
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
  if (znak === "ura") return ovoj('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>');
  if (znak === "bus") {
    return ovoj('<rect x="4" y="3.5" width="16" height="14.5" rx="2.6"/>'
      + '<path d="M4 10.5h16M7.5 18.5v2.5M16.5 18.5v2.5M8 14.5h.01M16 14.5h.01"/>');
  }
  if (znak === "vlak") {
    return ovoj('<rect x="6" y="3" width="12" height="14" rx="3"/>'
      + '<path d="M6 10h12M9 21l-2 2M15 21l2 2M9.5 20h5"/>');
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
    + `${escapeHtml(delayMin(z) === 0 ? "točno" : delayText(z))}</span>${vrsta}`;
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

function kmhNoge(i) {
  return jeKolo(i) ? KMH : 5;
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
  return `<li class="korak je-hoja" data-noga="${i}">
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

function voznjaHtml(n, i) {
  const pot = n.network === "avtobus" ? "bus" : "train";
  // Kot iz iskalnika zvez: dan predloga (nočni avtobus je včerajšnji) in
  // postajališče vstopa, da okno pokaže "Pri tebi" -- brez tega je človek
  // svoje postajališče iskal med 39 postanki, vse z "brez ocene".
  const q = new URLSearchParams({ trip: n.trip_id, postaja: n.od });
  if (PREDLOG && PREDLOG.datum) q.set("date", PREDLOG.datum);
  const okno = `/app/${pot}/${encodeURIComponent(n.train_no)}?${q}`;
  const odh = n.odhod_ocena || n.odhod;
  const prih = n.prihod_ocena || n.prihod;
  const vr = n.odhod_ocena && n.odhod_ocena !== n.odhod
    ? `<div class="korak-opomba">vozni red ${ura(n.odhod)} → ${ura(n.prihod)}</div>` : "";
  // Vmesni postanki so zaprti: potnika najprej zanima, kje izstopi, in šele
  // potem, kaj je vmes. Prvi in zadnji sta v vrsticah nad in pod, zato ju tu ni.
  const vmes = (n.postanki || []).slice(1, -1);
  const seznam = vmes.length ? `<details class="vmesni">
      <summary>${vmes.length} ${sklon(vmes.length, "postanek")} vmes</summary>
      <ol>${vmes.map((s) => `<li><span class="vm-ura">${
        s.prihod ? ura(s.prihod) : "—"}</span> ${escapeHtml(s.ime)}</li>`).join("")}</ol>
    </details>` : "";
  const kdo = imeVoznje(n);
  return `<li class="korak je-voznja" data-noga="${i}">
    <span class="korak-znak" aria-hidden="true">●</span>
    <div class="korak-telo">
      <div class="korak-vrh">
        <a class="noga-linija" href="${okno}">${escapeHtml(kdo)}</a>
        ${zamudaHtml(n.zamuda, n.brez_podatka)}
        ${n.headsign ? `<span class="korak-smer">→ ${escapeHtml(lepoIme(n.headsign))}</span>` : ""}
      </div>
      <div class="korak-vstop"><strong>${ura(odh)}</strong> ${escapeHtml(n.od)}</div>
      ${n.od_postanek ? nadomestniPostanekHtml({ opis: n.od_postanek }) : ""}
      ${seznam}
      <div class="korak-izstop"><strong>${ura(prih)}</strong> ${escapeHtml(n.do)}
        <span class="korak-kam">izstop</span>${izstopHtml(n)}</div>
      ${n.do_postanek ? nadomestniPostanekHtml({ opis: n.do_postanek }) : ""}
      ${vr}
    </div></li>`;
}

// Prestop stoji MED vožnjama, ki ju veže. Brez rezerve je "prestop" samo
// beseda; z njo je odgovor na edino vprašanje, ki ga potnik tam ima.
function prestopHtml(t, pred, po) {
  const mins = rezervaPrestopa(t, pred, po);
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
      ${tveganjeHtml(t)}
    </div></li>`;
}

// Tveganje prestopa: ista govorica kot na seznamu predlogov (common.js).
function tveganjeHtml(t) {
  if (!t.tveganje) return "";
  return `<div class="korak-tveganje"><span class="tveganje ${STOPNJA_RAZRED[t.tveganje.stopnja] || ""}">${
    escapeHtml(t.tveganje.stopnja)}</span> ${escapeHtml(prestopDrzi(t))}</div>`;
}

function korakiHtml(p) {
  const voznje = p.noge.filter((n) => n.vrsta === "voznja");
  const out = [];
  p.noge.forEach((n, i) => {
    const v = voznje.indexOf(n);
    if (v > 0 && p.prestopi && p.prestopi[v - 1]) {
      out.push(prestopHtml(p.prestopi[v - 1], voznje[v - 1], n));
    }
    out.push(n.vrsta === "hoja" ? hojaHtml(n, i) : voznjaHtml(n, i));
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
  // Trase tudi brez zemljevida: pot, na kateri si, iz njih ve, ali se pelješ.
  nalozTrase(p);
  if (!K) return;
  // Postajališča vstopa in izstopa z imeni; start in cilj sta svoji oznaki.
  const f = [];
  for (const n of p.noge) {
    if (n.vrsta !== "voznja") continue;
    if (n.od_ll) f.push(pkTocka(n.od_ll, { vrsta: "postaja", ime: n.od }));
    if (n.do_ll) f.push(pkTocka(n.do_ll, { vrsta: "postaja", ime: n.do }));
  }
  pkVir(K.map, "k-tocke", f);
  const [a, b] = [odKod(), doKod()];
  pkKonca(K, { lat: a[0], lon: a[1] }, { lat: b[0], lon: b[1] });
  risiCrte();
  if (!V.aktivno) priblizaj(null, false);
}

/** Trase voženj namesto skic. Brez omrežja ostane skica in se naloži, ko se
 *  omrežje vrne; vožnja, ki trase na strežniku nima, ostane ravna črta
 *  (`ravna`) -- ta pa ni dokaz, kje se pelješ (`trasaVoznje`). */
async function nalozTrase(p) {
  // `nalaga`: trasa še pride -- pot, na kateri si, do takrat ne gre po uri
  // (`korakNaPoti`), sicer bi ob odprtju preskočila čakanje na zamujeno vozilo.
  const cakajo = p.noge.map((n, i) => n.vrsta === "voznja" && CRTE[i] && CRTE[i].skica);
  cakajo.forEach((da, i) => { if (da) CRTE[i].nalaga = true; });
  for (let i = 0; i < p.noge.length; i += 1) {
    if (!cakajo[i]) continue;
    let t;
    try {
      t = await trasa(p.noge[i]);
    } catch (e) {
      if (PREDLOG === p && CRTE[i]) CRTE[i].nalaga = false;
      continue;                              // brez omrežja: znova ob `online`
    }
    if (PREDLOG !== p || !CRTE[i]) return;   // medtem druga pot
    CRTE[i] = t ? { vrsta: "voznja", tocke: t } : { vrsta: "voznja", tocke: CRTE[i].tocke, ravna: true };
    risiCrte();
  }
}
addEventListener("online", () => { if (PREDLOG) nalozTrase(PREDLOG); });

/** Približaj na eno nogo (ali na vso pot, kadar je `i` `null`). */
function priblizaj(i, pomakni = true) {
  if (!K) return;
  const tocke = i === null
    ? CRTE.filter(Boolean).flatMap((c) => c.tocke).concat([odKod(), doKod()])
    : (CRTE[i] ? CRTE[i].tocke : []);
  pkPrilagodi(K.map, tocke, { maxZoom: i === null ? PK_BREZ_NAGIBA : 16.5, padding: 40,
                              bearing: 0, animate: pomakni });
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

// Lega teče sama, kadar je dovoljenje dano (`LEGA` v common.js, prijava ob
// koncu datoteke); pogled se zanjo ne premakne, razen med vodenjem.
let JAZ = null;
// Smer telefona (kompas), kadar jo pozna. Brez nje se zemljevid pri vodenju
// obrne po poti, ne po telefonu.
let KOMPAS = null;

function obLegi(loc) {
  JAZ = loc;
  if (K) pkJaz(K.map, loc);
  $("#karta-lega").classList.toggle("je-on", !!loc);
  posodobiVse(false);
}

/** Pot, na kateri si, ali vodenje po eni pešpoti. */
function posodobiVse(skok) {
  if (NP.aktivno && naPotiPoteklo(AKTIVNA, Date.now())) {
    // Na cilju ali dolgo po prihodu: pot gre sama. Kdor ravno gleda, jo vidi
    // končano -- stran mu ne pobegne izpod prsta.
    NA_POTI.koncaj();
    if (document.hidden) location.replace(nazajUrl());
    else potKoncana();
    return;
  }
  if (NP.aktivno) {
    korakNaPoti();
    risiNaPoti(skok);
  } else {
    posodobi(skok);
  }
}

// Lega na dotik (gumb, „vodi me“). Med hojo je edino vprašanje "grem v pravo
// smer", zato po tem lega sledi in se ne izmeri enkrat: prvi popravek GPS
// pogosto zgreši za sto metrov. `lega` je tekoče iskanje -- dva dotika ne
// začneta dveh.
let lega = null;
function zacniLego() {
  if (lega) return lega;
  $("#karta-lega").classList.add("je-iskanje");
  lega = poisciMe().finally(() => {
    lega = null;
    $("#karta-lega").classList.remove("je-iskanje");
  });
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

function azimut(a, b) {
  const r = Math.PI / 180;
  const dl = (b[1] - a[1]) * r;
  const y = Math.sin(dl) * Math.cos(b[0] * r);
  const x = Math.cos(a[0] * r) * Math.sin(b[0] * r)
    - Math.sin(a[0] * r) * Math.cos(b[0] * r) * Math.cos(dl);
  return (Math.atan2(y, x) / r + 360) % 360;
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
  listaj: 0, puscica: null, zaklep: null, osvezi: null, zamude: null, zacel: false,
};

// Dokler nisi bil na poti, je nisi začel: "vodi me do cilja" se pogosto
// pritisne še na vlaku. Takrat pot ni "zašla", ampak je pred tabo -- pokaže se
// njen začetek, preračuna pa ni. 35 m in ne 60: vozilo pogosto pelje mimo
// pešpoti do cilja, s 60 m je to štelo za "začel" in preračunalo pot sredi
// vožnje v 69 od 70 simuliranih voženj (30. 9. 2026), s 35 m v nobeni.
const NA_POTI_M = 35;
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
  V.kum = kumulative(V.tocke);
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
  deliOb(i);
}

// ---------------------------------------------------------------- deljenje ob vožnji
//
// Vodenje do postajališča je trenutek, ko aplikacija ve, s katerim vozilom se
// boš peljal (David, 6. 10. 2026). Kdor je deljenje ob vožnji vklopil, mu
// aplikacija počaka, da se pelje, in šele nato deli lego vozila
// (`DeljenjeStoritev.cakaj`); kdor ga ni, mu ga tu ponudimo. Brskalnik tega
// ne zna: lege z ugasnjenim zaslonom ne dobiva.

const DELI = Boolean(MOST && MOST.razlicica() >= 4);
// Vodenje, ki se začne več kot pol ure pred odhodom, ni pot do vozila zdaj.
const CAKAJ_PRED_S = 30 * 60;

function deliStanje() {
  try {
    return JSON.parse(MOST.deliObVoznji() || "{}");
  } catch (e) {
    return {};
  }
}

function deliOb(i) {
  const el = $("#vod-deli");
  const nv = DELI && ZIVO ? nogaVozila(i) : null;
  const odh = nv && (nv.odhod_ocena || nv.odhod);
  const cez = odh ? odh - Date.now() / 1000 : null;
  if (!nv || cez > CAKAJ_PRED_S || cez < -5 * 60) { el.hidden = true; return; }
  const kdo = escapeHtml(imeVoznje(nv));
  const st = deliStanje();
  if (st.vklopljeno && st.lega) {
    const ok = MOST.cakajVkrcanje(JSON.stringify({
      trip_id: nv.trip_id, service_date: PREDLOG.datum, network: nv.network,
      train_no: nv.train_no, headsign: lepoIme(nv.headsign || ""), agency: nv.agency,
      lat: nv.od_ll[0], lon: nv.od_ll[1], odhod_ms: odh * 1000,
    }));
    el.innerHTML = ok ? `Ko boš na ${kdo}, bo kajros anonimno delil njegovo lego. `
      + '<button type="button" data-deli="ne">Ne tokrat</button>' : "";
  } else {
    el.innerHTML = `Pomagaj drugim: ko boš na ${kdo}, lahko kajros anonimno deli `
      + 'njegovo lego. <button type="button" data-deli="da">Vklopi</button>';
  }
  el.hidden = !el.innerHTML;
}

$("#vod-deli").addEventListener("click", (e) => {
  const b = e.target.closest("[data-deli]");
  if (!b) return;
  if (b.dataset.deli === "ne") {
    MOST.deliUstavi();
    $("#vod-deli").textContent = "Tokrat ne.";
    return;
  }
  MOST.nastaviDeliObVoznji(true);
  // Dovoljenje za lego je okno sistema; počakamo na odgovor in poskusimo znova.
  let poskusov = 0;
  const cakaj = setInterval(() => {
    poskusov += 1;
    if (deliStanje().lega || poskusov > 60) {
      clearInterval(cakaj);
      deliOb(V.i);
    }
  }, 1000);
});

function koncajVodenje() {
  V.aktivno = false;
  clearInterval(V.osvezi);
  clearTimeout(V.zamude);
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
  const a = tockaNaTrasi(V.tocke, V.kum, vzdolz);
  const b = tockaNaTrasi(V.tocke, V.kum, vzdolz + 25);
  return razdaljaM(a, b) > 1 ? azimut(a, b) : (K ? K.map.getBearing() : 0);
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

// Koledarski dan odhoda, ne prometni dan: nočni avtobus ob 00:05 nosi
// včerajšnji datum, v glavi pa mora pisati dan, ko potnik gre od doma.
function danOdhoda(pr) {
  return new Date(pr.odhod * 1000).toLocaleDateString("sv-SE", { timeZone: "Europe/Ljubljana" });
}

function voziloHtml(nv, ostaneS) {
  const kdo = imeVoznje(nv);
  const odh = nv.odhod_ocena || nv.odhod;
  const zam = nv.zamuda ? " " + zamudaHtml(nv.zamuda) : "";
  let vrstica = `<strong>${escapeHtml(kdo)}</strong> ${
    nv.headsign ? `→ ${escapeHtml(lepoIme(nv.headsign))} ` : ""}odpelje ob <strong>${ura(odh)}</strong>${zam}`;
  // Odštevanje samo za pot, ki je zdaj: za jutrišnjo je "čez 1 080 minut" šum.
  if (!ZIVO) return vrstica;
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
    const p = projekcijaNaTraso(V.tocke, V.kum, JAZ.lat, JAZ.lon);
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
  const doKonca = JAZ ? razdaljaM([JAZ.lat, JAZ.lon], konec) : Infinity;
  // Prispel si, ko je konec bližje od točnosti lege -- a vsaj 15 m, sicer bi
  // GPS v mestu tu in tam "prispel" dvajset metrov pred postajo.
  const prag = Math.max(15, Math.min(JAZ ? JAZ.acc || 15 : 15, 35));
  if (JAZ && (doKonca <= prag || (ostane <= prag && odmik < IZVEN_M))) {
    if (!V.prispel && navigator.vibrate) navigator.vibrate([120, 80, 120]);
    V.prispel = true;
  }
  const nv = nogaVozila(V.i);
  const hitrost = kmhNoge(V.i) / 3.6;
  const ostaneS = ostane / hitrost;

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
      escapeHtml(n.do || "")}</strong> · ${dolzina(skupaj)} · ${cas(skupaj / hitrost)}`;
  }
  $("#vod-vozilo").innerHTML = nv ? voziloHtml(nv, V.prispel ? 0 : ostaneS) : "";
  $("#vod-vozilo").hidden = !nv;

  // Kaj po tem: ob vozilu "ko izstopiš, vodi me naprej", na cilju konec. Na
  // poti gre stran naprej sama (`korakNaPoti`) in gumbe postavi `risiPlosco`.
  const dalje = naslednjaHoja(V.i);
  if (!NP.aktivno) {
    $("#vod-dalje").hidden = !(V.prispel && dalje !== null);
    if (dalje !== null) {
      $("#vod-dalje").textContent = `ko izstopiš: vodi me ${kamBeseda(PREDLOG.noge[dalje])}`;
      $("#vod-dalje").dataset.vodi = dalje;
    }
    $("#vod-konec").textContent = V.prispel && dalje === null ? "končano" : "končaj";
  }
  $("#vod-sledi").hidden = V.sledi || !vodim;
  const opomba = $("#vod-opomba");
  if (NP.aktivno && NP.opomba) {
    // Na poti ima prednost opomba poti (prestop, ki ne drži, stare zamude):
    // prepis vsako sekundo bi pojedel dotik na njenem gumbu.
  } else if (dalec) {
    opomba.textContent = `Pot se začne ${dolzina(razdaljaM([JAZ.lat, JAZ.lon], V.tocke[0]))}`
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

  // Zašel: odmik večji od dvojne točnosti in od praga, trikrat zapored -- šum
  // GPS se vleče čez več zaporednih popravkov. Simulacija na 200 pešpoteh
  // (30. 9. 2026, šum 15 m): lažnih preračunov 149 namesto 630 na 305 km,
  // pravo zaidenje zaznano pri 41 m namesto 32 m (mediana).
  if (vodim && V.zacel && !V.prispel && odmik > Math.max(IZVEN_M, 2 * (JAZ.acc || 0))
      && (JAZ.acc || 0) < 60) {
    V.izven += 1;
    if (V.izven >= 3 && Date.now() - V.preracun > PRERACUN_MS) preracunaj();
  } else {
    V.izven = 0;
  }
}

async function preracunaj() {
  V.preracun = Date.now();
  const konec = V.tocke[V.tocke.length - 1];
  const p = new URLSearchParams({ od_lat: JAZ.lat.toFixed(6), od_lon: JAZ.lon.toFixed(6),
                                  do_lat: konec[0].toFixed(6), do_lon: konec[1].toFixed(6),
                                  kmh: kmhNoge(V.i) });
  try {
    const r = await fetch(`/api/pot/hoja?${p}`);
    if (!r.ok) return;
    const d = await r.json();
    if (!V.aktivno || !d.tocke || d.tocke.length < 2) return;
    CRTE[V.i] = { vrsta: "hoja", tocke: d.tocke };
    V.tocke = d.tocke;
    V.kum = kumulative(d.tocke);
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
  clearTimeout(V.zamude);
  if (!V.aktivno || !ZIVO) return;
  try {
    const r = await fetch(`/api/pot/podrobno?${naslovPodrobno()}&geometrija=0`);
    if (r.ok) {
      const d = await r.json();
      // Po vožnji, ne po indeksu: pešpot iz matrike je lahko drugače dolga
      // in kratka hoja (pod minuto) odpade -- indeksi se tedaj zamaknejo.
      d.predlog.noge.forEach((n) => {
        const moja = PREDLOG.noge.find((m) => m.vrsta === "voznja"
          && m.trip_id === n.trip_id && m.od_seq === n.od_seq);
        if (n.vrsta !== "voznja" || !moja) return;
        for (const k of ["zamuda", "zamuda_izstop", "odhod_ocena", "prihod_ocena", "brez_podatka"]) {
          moja[k] = n[k];
        }
      });
      posodobi(false, true);
    }
  } catch (e) { /* naslednjič */ }
  // Ena sama veriga: `zacniVodenje` se kliče tudi med vodenjem ("ko izstopiš:
  // vodi me do cilja"), in vsak klic je prej začel svojo -- na tretji nogi so
  // tri osveževale isto pot, vsaka z OSRM za vsako pešpot.
  clearTimeout(V.zamude);
  if (V.aktivno) V.zamude = setTimeout(osveziZamude, 30000);
}

$("#vod-konec").addEventListener("click", () => (NP.aktivno ? koncajPot() : koncajVodenje()));
$("#vod-sledi").addEventListener("click", () => { V.sledi = true; posodobiVse(true); });
$("#vod-dalje").addEventListener("click", () => {
  if (NP.aktivno) naprejRocno();
  else zacniVodenje(Number($("#vod-dalje").dataset.vodi));
});
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

// ---------------------------------------------------------------- na poti
//
// Izbrana pot (`NA_POTI` v common.js) kot navigacija: zemljevid čez vso
// stran, zgoraj, kaj zdaj, spodaj plošča s celo potjo, ki se zloži v vrstico.
// Korak (hoja, čakanje, vožnja, cilj) pove lega, kadar jo imamo, sicer ura --
// sam od sebe nikoli nazaj. Napredek se shrani, da ga zaprta aplikacija ne
// pozabi (prijava 22. 10. 2026: na prvem avtobusu ni več vedel, kje prestopi).

const NP = {
  aktivno: false, koraki: [], k: 0, trasa: {},
  vozilo: null, vozilaTrip: null, vozilaZanka: null, voziloOznaka: null,
  voziloNoga: null, vozilo3d: {}, zoom3D: false,
  najavljen: -1, zamujeno: null, odlozi: 0, zacel: false,
  kameraOb: 0, potrdi: 0, zamenjaj: 0, osvezi: null, ura: null,
  // Pot ni več v voznem redu (404); zadnja napaka osvežitve; napaka lege;
  // do kdaj ura ne premika koraka (vrnitev na stran, osvežitev še teče).
  niVec: false, napaka: null, legaNapaka: null, cakaOsvezitev: 0, opomba: null,
};
//: Lega, starejša od tega, o koraku ne odloča -- takrat velja ura.
const NP_LEGA_SVEZA_MS = 60000;
//: Vozilo, ki ga čakaš, je morda odpeljalo brez tebe toliko po pričakovanem
//: odhodu (z zamudo), ko te lega še ni videla na njem. Z lego vozila, ki je
//: že za postajališčem, prej; brez nje šele po petih minutah.
const NP_ZAMUJENO_S = 150;
const NP_ZAMUJENO_BREZ_VOZILA_S = 300;
//: Od toliko metrov pred izstopom „izstopi na naslednji“ in tresljaj.
const NP_IZSTOP_M = 500;
//: Lega šteje za korak šele toliko pred začetkom poti.
const NP_LEGA_PRED_S = 30 * 60;
//: Zamude, starejše od tega, so na plošči z besedo (osvežitev je na 30 s).
const NP_STARO_MS = 2 * 60000;
const NP_PLOSCA_KLJUC = "kajros:na-poti-plosca";

function svezaLega() {
  return JAZ && Date.now() - (JAZ.ts || 0) < NP_LEGA_SVEZA_MS && (JAZ.acc || 999) <= 150 ? JAZ : null;
}

/** Trasa vožnje z lego postankov vzdolž nje; `null`, dokler je le skica. */
function trasaVoznje(i) {
  const c = CRTE[i];
  if (!c || c.skica || c.ravna || !c.tocke || c.tocke.length < 2) return null;
  if (NP.trasa[i] && NP.trasa[i].tocke === c.tocke) return NP.trasa[i];
  const kum = kumulative(c.tocke);
  const postaje = (PREDLOG.noge[i].postanki || []).filter((x) => x.ll).map((x) => {
    const pr = projekcijaNaTraso(c.tocke, kum, x.ll[0], x.ll[1]);
    return { ...x, vzdolz: pr.vzdolz, odmik: pr.odmik };
  }).filter((x) => x.odmik <= 80);
  NP.trasa[i] = { tocke: c.tocke, kum, postaje };
  return NP.trasa[i];
}

/** Kje na trasi vožnje je potnik: `{vzdolz, odmik}` ali `null`. */
function naTrasi(i, l) {
  const tr = trasaVoznje(i);
  return tr && l ? projekcijaNaTraso(tr.tocke, tr.kum, l.lat, l.lon) : null;
}

/** Ali se potnik pelje z vožnjo koraka `r`: na njeni trasi, za vstopom, v
 *  gibanju. `strogo` je za vožnjo za prestopom: lega ob prestopnem
 *  postajališču je lahko še v prvem vozilu, ki tja pripelje -- šele 120 m po
 *  trasi drugega in ne pred njegovim odhodom. */
function seVozi(r, l, zdaj, prag, strogo = false) {
  const s = NP.koraki[r];
  const n = PREDLOG.noge[s.i];
  const na = naTrasi(s.i, l);
  if (!na || na.odmik > prag || zdaj < (n.odhod_ocena || n.odhod) - (strogo ? 60 : 180)) {
    return false;
  }
  const tr = trasaVoznje(s.i);
  const konec = tr.kum[tr.kum.length - 1];
  return na.vzdolz < konec - 15 && (na.vzdolz >= 120 || (!strogo && (l.hitrost || 0) >= 3));
}

/** Korak, ki ga dokazuje lega, ali `null`. Gleda le naprej od `k`. */
function korakIzLege(l, zdaj, k) {
  const koraki = NP.koraki;
  const ll = [l.lat, l.lon];
  const prag = Math.max(35, Math.min(l.acc || 35, 80));
  // Na cilju šele za zadnjo vožnjo: avtobus, ki pelje mimo vrat pred
  // izstopom, ali pot za zvečer, izbrana doma, nista prihod.
  const zadnja = koraki.map((s) => s.vrsta).lastIndexOf("voznja");
  if (k > zadnja && razdaljaM(ll, doKod()) <= prag) return koraki.length - 1;
  const korak = koraki[k];
  const hitrost = l.hitrost || 0;
  const r = koraki.findIndex((s, j) => j >= k && s.vrsta === "voznja");
  if (r < 0) return null;                   // pred tabo je le še hoja do cilja
  const n = PREDLOG.noge[koraki[r].i];
  if (korak.vrsta === "voznja") {
    // Izstop: ob izstopnem postajališču počasi, ali na trasi že na njenem koncu.
    const na = naTrasi(korak.i, l);
    const tr = trasaVoznje(korak.i);
    if (razdaljaM(ll, n.do_ll) <= prag + 20 && hitrost < 2) return k + 1;
    if (na && tr && na.odmik <= prag && na.vzdolz >= tr.kum[tr.kum.length - 1] - 15
        && hitrost < 2) return k + 1;
    // Na naslednji vožnji, ne da bi te videli na prestopu -- z dokazom.
    const r2 = koraki.findIndex((s, j) => j > k && s.vrsta === "voznja");
    return r2 > 0 && seVozi(r2, l, zdaj, prag, true) ? r2 : null;
  }
  if (seVozi(r, l, zdaj, prag)) return r;
  // Ob vstopnem postajališču čakaš (čakanje je vedno tik pred vožnjo).
  if (korak.vrsta === "hoja" && razdaljaM(ll, n.od_ll) <= prag + 10) return r - 1;
  return null;
}

function korakNaPoti() {
  const zdaj = Date.now() / 1000;
  const koraki = NP.koraki;
  if (!koraki.length) return;
  let k = NP.k;
  // Lega o koraku odloča šele blizu začetka: doma zjutraj ni korak večerne poti.
  const l = zdaj >= koraki[0].od - NP_LEGA_PRED_S ? svezaLega() : null;
  if (l) {
    const iz = korakIzLege(l, zdaj, k);
    if (iz != null && iz > k) k = iz;
    // Vodenje po pešpoti ve, kdaj si na koncu hoje (`V.prispel`).
    if (koraki[k].vrsta === "hoja" && V.i === koraki[k].i && V.prispel) k += 1;
    // Brez trase lega vožnje ne dokaže (zemljevida ni, trasa se ni naložila):
    // takrat gre pot naprej tudi po uri, kot brez lege -- sicer obstane pred
    // vozilom, na katerem potnik že sedi.
    const r = koraki.findIndex((s, j) => j >= k && s.vrsta === "voznja");
    const c = r >= 0 ? CRTE[koraki[r].i] : null;
    if (c && !c.nalaga && !trasaVoznje(koraki[r].i) && poUri()) {
      k = Math.max(k, korakPoCasu(koraki, zdaj));
    }
  } else if (poUri()) {
    k = Math.max(k, korakPoCasu(koraki, zdaj));
  }
  if (k !== NP.k) nastaviKorak(Math.min(k, koraki.length - 1));
  preveriZamujeno(l, zdaj);
}

/** Ali sme ura premakniti korak. Ob vrnitvi na stran so zamude stare, korak
 *  pa nazaj ne gre: najprej osvežitev (`osveziNaPoti`), nato ura. */
function poUri() {
  return Date.now() >= NP.cakaOsvezitev;
}

function nastaviKorak(k) {
  NP.k = k;
  NP.zamujeno = null;
  const korak = NP.koraki[k];
  if (korak.vrsta === "hoja") pripraviNogo(korak.i);
  else V.i = korak.vrsta === "cilj" ? -1 : korak.i;
  if (korak.vrsta === "cilj" && !(AKTIVNA.stanje && AKTIVNA.stanje.cilj_ob)) {
    AKTIVNA.stanje = { ...(AKTIVNA.stanje || {}), cilj_ob: Date.now() };
    if (navigator.vibrate) navigator.vibrate([120, 80, 120]);
  }
  V.sledi = true;
  risiCrte();
  voziloKoraka();
  shraniNaPoti();
  // Deljenje ob vožnji (aplikacija): pred vozilom, ki ga čakaš.
  if (korak.vrsta === "hoja" || korak.vrsta === "cakanje") {
    deliOb(korak.vrsta === "hoja" ? korak.i : korak.i - 1);
  } else {
    $("#vod-deli").hidden = true;
  }
}

/** Ročni korak naprej: „sem na vozilu“, „izstopil sem“, „grem“. */
function naprejRocno() {
  const korak = NP.koraki[NP.k];
  if (NP.k === 0 && korak.vrsta === "hoja" && !NP.zacel) {
    NP.zacel = true;
    risiNaPoti(true);
    return;
  }
  if (NP.zamujeno != null) {
    nastaviKorak(NP.zamujeno);
  } else if (NP.k < NP.koraki.length - 1) {
    nastaviKorak(NP.k + 1);
  }
  risiNaPoti(true);
}

function preveriZamujeno(l, zdaj) {
  NP.zamujeno = null;
  const korak = NP.koraki[NP.k];
  if (!ZIVO || !l || !korak || (korak.vrsta !== "hoja" && korak.vrsta !== "cakanje")) return;
  if (Date.now() < NP.odlozi) return;
  const r = NP.koraki.findIndex((s, j) => j >= NP.k && s.vrsta === "voznja");
  if (r < 0) return;
  const n = PREDLOG.noge[NP.koraki[r].i];
  const odh = n.odhod_ocena || n.odhod;
  if (zdaj < odh + NP_ZAMUJENO_S) return;
  // Vozilo z lego je odpeljalo, kadar je na trasi že za vstopnim postajališčem.
  const v = NP.vozilo;
  const tr = trasaVoznje(NP.koraki[r].i);
  if (!tr) return;                // brez trase lega ne pove, ali si na njem
  if (v && NP.vozilaTrip === n.trip_id) {
    const pv = projekcijaNaTraso(tr.tocke, tr.kum, v.lat, v.lon);
    if (pv.odmik > 150 || pv.vzdolz < 100) return;
  } else if (zdaj < odh + NP_ZAMUJENO_BREZ_VOZILA_S) {
    return;
  }
  NP.zamujeno = r;
}

/** Postaje vožnje pred tabo do izstopa: po legi na trasi, sicer po uri. */
function postajeNaprej(i, zdaj) {
  const n = PREDLOG.noge[i];
  const vse = (n.postanki || []).slice(1);
  const l = svezaLega();
  const na = naTrasi(i, l);
  const tr = trasaVoznje(i);
  if (na && tr && na.odmik <= 120 && tr.postaje.length >= 2) {
    const naprej = tr.postaje.filter((x) => x.vzdolz > na.vzdolz + 20 && x.stop_seq !== n.od_seq);
    return { postaje: naprej, doIzstopa: Math.max(0, tr.kum[tr.kum.length - 1] - na.vzdolz) };
  }
  const zam = ((n.zamuda_izstop || n.zamuda) || {}).s || 0;
  return { postaje: vse.filter((x) => (x.prihod || x.odhod || 0) + zam > zdaj - 30), doIzstopa: null };
}

/** Prestop za vožnjo tega koraka (ali prvo za njim): kaj pride potem. */
function nato(korak) {
  if (korak.vrsta === "cilj") return null;
  const voznje = PREDLOG.noge.filter((n) => n.vrsta === "voznja");
  const v = voznje.findIndex((n) => PREDLOG.noge.indexOf(n) >= korak.i);
  if (v < 0 || v + 1 >= voznje.length || !PREDLOG.prestopi || !PREDLOG.prestopi[v]) return null;
  return { prestop: PREDLOG.prestopi[v], pred: voznje[v], po: voznje[v + 1] };
}

/** Prestop pred tabo, ki po zamudah zdaj ne drži. */
function ogrozenPrestop() {
  const voznje = PREDLOG.noge.filter((n) => n.vrsta === "voznja");
  const korak = NP.koraki[NP.k];
  for (let v = 1; v < voznje.length; v += 1) {
    const t = PREDLOG.prestopi && PREDLOG.prestopi[v - 1];
    // Prestop, katerega drugo vozilo je že za tabo (čakaš nanj ali se z njim
    // pelješ), ni več pred tabo; med hojo do njega pa še je.
    if (!t || !t.tveganje || PREDLOG.noge.indexOf(voznje[v]) <= korak.i) continue;
    const mins = rezervaPrestopa(t, voznje[v - 1], voznje[v]);
    if ((mins != null && mins < 0) || (t.tveganje.vir === "zdaj" && t.tveganje.p < 0.5)) {
      return { t, mins };
    }
  }
  return null;
}

/** Vozilo, ki ga čakaš: kdaj odpelje in, kadar ima lego, kako daleč je. Ura
 *  sama ne pove „je že odpeljal“ -- zamujeno vozilo je pogosto še na poti. */
function cakanjeHtml(n, zdaj) {
  const odh = n.odhod_ocena || n.odhod;
  let s = `<strong>${escapeHtml(imeVoznje(n))}</strong> odpelje ob <strong>${ura(odh)}</strong>${
    n.zamuda ? " " + zamudaHtml(n.zamuda) : ""}`;
  if (NP.vozilo && NP.vozilaTrip === n.trip_id && n.od_ll) {
    s += ` · vozilo je ${dolzina(razdaljaM([NP.vozilo.lat, NP.vozilo.lon], n.od_ll))} od postajališča`;
  } else if (odh > zdaj + 45) {
    s += ` · čez ${minute(odh - zdaj)}`;
  }
  return s;
}

function zamudaBeseda(z) {
  if (!z || delayMin(z) === 0) return "";
  return ` (${delayText(z, true)})`;
}

/** Zgornja kartica za korak, ki ni hoja: kaj zdaj, in koliko časa. */
function risiKorak(korak, n, pred, zdaj) {
  const man = $("#vod-manever");
  man.classList.remove("je-pozor");
  $("#vod-listaj").hidden = true;
  const znak = (x) => znakSvg(x && x.network === "zeleznica" ? "vlak" : "bus", 38);
  if (pred) {
    const v = nogaVozila(korak.i);
    $("#vod-znak").innerHTML = znakSvg("ura", 38);
    $("#vod-razdalja").textContent = cezPoti(korak.od, zdaj);
    $("#vod-navodilo").textContent = `Odidi ob ${ura(korak.od)}`;
    $("#vod-ulica").textContent = v
      ? `${minute(n.sekunde)} ${jeKolo(korak.i) ? "s kolesom" : "peš"} do ${v.od} · ${imeVoznje(v)} ob ${
        ura(v.odhod_ocena || v.odhod)}` : "";
    return;
  }
  if (korak.vrsta === "cilj") {
    $("#vod-znak").innerHTML = znakSvg("cilj", 38);
    $("#vod-razdalja").textContent = "";
    $("#vod-navodilo").textContent = "Na cilju si";
    $("#vod-ulica").textContent = `ob ${ura(korak.od)} po načrtu`;
    return;
  }
  if (NP.zamujeno != null) {
    const z = PREDLOG.noge[NP.koraki[NP.zamujeno].i];
    man.classList.add("je-pozor");
    $("#vod-znak").innerHTML = znak(z);
    $("#vod-razdalja").textContent = "";
    $("#vod-navodilo").textContent = `Si zamudil ${imeVoznje(z)}?`;
    $("#vod-ulica").textContent = NP.vozilo && NP.vozilaTrip === z.trip_id
      ? "Po legi je že odpeljal s postajališča."
      : `Po zadnjem podatku bi odpeljal ob ${ura(z.odhod_ocena || z.odhod)}.`;
    return;
  }
  if (korak.vrsta === "cakanje") {
    const odh = n.odhod_ocena || n.odhod;
    $("#vod-znak").innerHTML = znak(n);
    $("#vod-razdalja").textContent = odh > zdaj ? cezPoti(odh, zdaj) : "prihaja";
    $("#vod-navodilo").textContent = `${imeVoznje(n)}${n.headsign ? ` → ${lepoIme(n.headsign)}` : ""}`;
    $("#vod-ulica").textContent = `${n.od} · ${ura(odh)}${zamudaBeseda(n.zamuda)}`;
    return;
  }
  // Vožnja: koliko postaj še in kje izstopiš.
  const prih = n.prihod_ocena || n.prihod;
  const { postaje, doIzstopa } = postajeNaprej(korak.i, zdaj);
  const st = Math.max(1, postaje.length);
  const naslednja = st <= 1 || (doIzstopa != null && doIzstopa <= NP_IZSTOP_M && st <= 2);
  $("#vod-znak").innerHTML = znak(n);
  $("#vod-razdalja").textContent = naslednja ? "izstopi" : `še ${st} ${sklon(st, "postaja")}`;
  $("#vod-navodilo").textContent = naslednja ? `Na naslednji izstopi: ${n.do}` : `Izstopi na ${n.do}`;
  $("#vod-ulica").textContent = `ob ${ura(prih)}${!naslednja && postaje[0]
    ? ` · naslednja ${postaje[0].ime}` : ""}`;
  man.classList.toggle("je-pozor", naslednja);
  if (naslednja && NP.najavljen !== korak.i) {
    NP.najavljen = korak.i;
    if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
  }
}

/** Kamera za korak, ki ni hoja; hojo vodi `posodobi`. */
function kameraNaPoti(korak, n, pred, skok) {
  if (!K || !V.sledi) return;
  // Med dvema premikoma vsaj tri sekunde: lega pride vsako sekundo, kamera,
  // ki se ves čas premika, je ne pustí brati.
  if (!skok && Date.now() - NP.kameraOb < 3000) return;
  NP.kameraOb = Date.now();
  const l = svezaLega();
  if (pred) {
    priblizaj(null, false);
    return;
  }
  if (korak.vrsta === "cilj") {
    const [a, b] = doKod();
    K.map.easeTo({ center: [b, a], zoom: 16.5 - PK_LZ, bearing: 0, duration: 900 });
    return;
  }
  if (korak.vrsta === "cakanje") {
    const v = NP.vozilo;
    const tocke = [n.od_ll, l && [l.lat, l.lon], v && razdaljaM([v.lat, v.lon], n.od_ll) < 4000
      && [v.lat, v.lon]].filter(Boolean);
    pkPrilagodi(K.map, tocke.length > 1 ? tocke : [n.od_ll, n.od_ll],
                { maxZoom: 16.5, padding: 60, bearing: 0, duration: 900 });
    return;
  }
  // Vožnja: za tabo, kadar te lega vidi na trasi; sicer za vozilom.
  const tr = trasaVoznje(korak.i);
  const na = naTrasi(korak.i, l);
  let kje = null;
  let vzdolz = null;
  if (na && na.odmik <= 150) {
    kje = [l.lat, l.lon];
    vzdolz = na.vzdolz;
  } else if (NP.vozilo && NP.vozilaTrip === n.trip_id) {
    kje = [NP.vozilo.lat, NP.vozilo.lon];
  } else if (tr) {
    // Brez obojega po uri: delež poti med odhodom in prihodom.
    const odh = n.odhod_ocena || n.odhod, prih = n.prihod_ocena || n.prihod;
    const f = Math.max(0, Math.min(1, (Date.now() / 1000 - odh) / Math.max(60, prih - odh)));
    vzdolz = f * tr.kum[tr.kum.length - 1];
    kje = tockaNaTrasi(tr.tocke, tr.kum, vzdolz);
  }
  if (!kje) return;
  const smer = tr && vzdolz != null ? smerTrase(tr.tocke, tr.kum, vzdolz, 60) : null;
  const h = K.map.getContainer().clientHeight;
  K.map.easeTo({ center: [kje[1], kje[0]], zoom: 15.6 - PK_LZ,
                 bearing: smer ?? K.map.getBearing(),
                 padding: { top: Math.round(h * 0.3), bottom: 0, left: 0, right: 0 }, duration: 1000 });
}

/** Spodnja plošča na poti: vrstica, ko je zložena, in vsa pot, ko ni. */
function risiPlosco(korak, pred, zdaj) {
  const n = PREDLOG.noge[korak.i];
  const naprej = nato(korak);
  const ogrozen = ZIVO ? ogrozenPrestop() : null;
  // Vrstica ob puščici: kar pride za tem korakom -- prestop s tveganjem ali cilj.
  let vrstica;
  if (naprej && korak.vrsta !== "cilj") {
    const t = naprej.prestop;
    vrstica = `Nato <strong>${escapeHtml(imeVoznje(naprej.po))}</strong> ob ${
      ura(naprej.po.odhod_ocena || naprej.po.odhod)} v ${escapeHtml(t.kje)}${t.tveganje
      ? ` <span class="tveganje ${STOPNJA_RAZRED[t.tveganje.stopnja] || ""}">${escapeHtml(t.tveganje.stopnja)}</span>`
      : ""}`;
  } else {
    vrstica = `Na cilju ob <strong>${ura(PREDLOG.prihod_ocena || PREDLOG.prihod)}</strong>${
      ZIVO ? "" : ` · ${escapeHtml(dayLabel(danOdhoda(PREDLOG)))}`}`;
  }
  $("#vod-povzetek").innerHTML = vrstica;

  if (korak.vrsta !== "hoja" || pred) {
    $("#vod-cilj").innerHTML = korak.vrsta === "voznja" && n.headsign
      ? `${escapeHtml(imeVoznje(n))} → ${escapeHtml(lepoIme(n.headsign))}${n.zamuda ? " " + zamudaHtml(n.zamuda) : ""}`
      : "";
    const v = korak.vrsta === "cakanje" || pred ? (pred ? nogaVozila(korak.i) : n) : null;
    $("#vod-vozilo").innerHTML = !v ? "" : pred ? voziloHtml(v, n.sekunde) : cakanjeHtml(v, zdaj);
    $("#vod-vozilo").hidden = !v;
  }
  // Ena opomba, po pomembnosti, vsakič znova -- prej je ostala tudi, ko ni več
  // veljala (stara „brez povezave“ po vrnitvi omrežja).
  const op = $("#vod-opomba");
  let html = "";
  let razred = "vod-opomba";
  const staro = ZIVO ? Date.now() - (AKTIVNA.osvezeno || AKTIVNA.sprejeto) : 0;
  if (ogrozen) {
    const t = ogrozen.t;
    html = `<strong>Prestop v ${escapeHtml(t.kje)} morda ne bo držal</strong>${
      ogrozen.mins != null && ogrozen.mins < 0 ? `: zmanjka ${-ogrozen.mins} min` : ""}. `
      + '<button type="button" data-nova="prestop">Poišči drugo pot</button>';
    razred += " je-opozorilo";
    // Tresljaj enkrat na prestop, tudi čez znova odprto stran: verjetnost se
    // ob vsaki osvežitvi premakne, prestop pa je isti.
    const kljuc = `${PREDLOG.prestopi.indexOf(t)}:${t.kje}`;
    if ((AKTIVNA.stanje || {}).opozorjen !== kljuc) {
      if (navigator.vibrate) navigator.vibrate([300, 150, 300]);
      AKTIVNA.stanje = { ...(AKTIVNA.stanje || {}), opozorjen: kljuc };
      shraniNaPoti();
    }
  } else if (NP.niVec) {
    // Vozni red se uvaža vsak dan; jutrišnja vožnja ima lahko drug id.
    html = 'Vozni red se je spremenil in te poti ni več. '
      + '<button type="button" data-nova="znova">Poišči jo znova</button>';
    razred += " je-opozorilo";
  } else if (NP.legaNapaka) {
    html = escapeHtml(NP.legaNapaka);
  } else if (staro > NP_STARO_MS && korak.vrsta !== "cilj") {
    html = `${NP.napaka ? `${NP.napaka} — z` : "Z"}amude so izpred ${Math.round(staro / 60000)} min.`;
    razred += " je-staro";
  } else if (!svezaLega() && korak.vrsta !== "cilj" && ZIVO) {
    // Brez lege stran ne ve, ali si na vozilu: gre po uri, korak pa lahko
    // potrdiš sam. Okna za dovoljenje ne odpremo sami -- samo ta dotik.
    html = 'Brez lege gre pot naprej po uri. <button type="button" data-lega>Pokaži, kje sem</button>';
  }
  // Med hojo piše v isto vrstico tudi vodenje po pešpoti (`posodobi`); svojo
  // opombo pot prepozna po oznaki in jo napiše znova le, kadar je ni.
  if (html !== NP.opomba || (html && !op.querySelector(":scope > [data-np]"))) {
    if (html) op.innerHTML = `<span data-np>${html}</span>`;
    else if (NP.opomba) op.textContent = "";
    NP.opomba = html;
  }
  op.className = html ? razred : "vod-opomba";

  // Gumbi: en glavni za ta korak, „nova pot“ in konec.
  const dalje = $("#vod-dalje");
  // „Grem zdaj“ samo, kadar je odhod blizu -- za jutrišnjo pot je vabilo k
  // vodenju, ki ga še ni.
  const beseda = NP.niVec ? ""
    : pred ? (korak.od - zdaj < 30 * 60 ? "grem zdaj" : "")
    : NP.zamujeno != null ? "sem na vozilu"
    : korak.vrsta === "cakanje" ? "sem na vozilu"
    : korak.vrsta === "voznja" ? "izstopil sem"
    : korak.vrsta === "hoja" && !svezaLega() ? "naprej" : "";
  dalje.textContent = beseda;
  dalje.hidden = !beseda;
  $("#vod-nova").hidden = korak.vrsta === "cilj";
  // Zložena plošča kaže le glavni gumb; ob zamujenem vozilu ali prestopu, ki
  // ne drži, je „nova pot od tu“ prav tako glavni.
  $("#vod-nova").classList.toggle("je-nujno", NP.zamujeno != null || !!ogrozen);
  const konec = $("#vod-konec");
  if (!NP.potrdi) konec.textContent = korak.vrsta === "cilj" ? "končano" : "končaj pot";
  konec.classList.toggle("je-potrdi", !!NP.potrdi);
  $("#vod-sledi").hidden = V.sledi;

  // Vsa pot, trenutni korak poudarjen.
  document.querySelectorAll("#koraki .korak[data-noga]").forEach((el) => {
    el.classList.toggle("je-zdaj", Number(el.dataset.noga) === korak.i && korak.vrsta !== "cilj");
    el.classList.toggle("je-mimo", Number(el.dataset.noga) < korak.i || korak.vrsta === "cilj");
  });
}

function risiNaPoti(skok) {
  if (!NP.aktivno || !PREDLOG || !NP.koraki.length) return;
  const zdaj = Date.now() / 1000;
  const korak = NP.koraki[NP.k];
  const n = PREDLOG.noge[korak.i];
  const pred = NP.k === 0 && korak.vrsta === "hoja" && zdaj < korak.od - 60 && !NP.zacel;
  document.body.dataset.korak = pred ? "pred" : korak.vrsta;
  if (korak.vrsta === "hoja" && !pred && NP.zamujeno == null) {
    if (V.i !== korak.i) pripraviNogo(korak.i);
    posodobi(skok);                 // vodenje po pešpoti, kot doslej
  } else {
    risiKorak(korak, n, pred, zdaj);
    kameraNaPoti(korak, n, pred, skok);
    // „Ti“ tudi med čakanjem in vožnjo: puščica iz vodenja ostane edina
    // oznaka tebe, smer je smer vožnje (zemljevid je obrnjen vanjo).
    const l = svezaLega();
    if (l && K) {
      const na = korak.vrsta === "voznja" ? naTrasi(korak.i, l) : null;
      const tr = na && trasaVoznje(korak.i);
      const smer = tr ? smerTrase(tr.tocke, tr.kum, na.vzdolz, 60) : null;
      puscica([l.lat, l.lon], smer ?? l.smer ?? KOMPAS ?? K.map.getBearing());
    }
  }
  risiPlosco(korak, pred, zdaj);
}

// ---- vozilo, ki ga čakaš ali na katerem si

function voziloKoraka() {
  const korak = NP.koraki[NP.k];
  const r = NP.koraki.findIndex((s, j) => j >= NP.k && s.vrsta === "voznja");
  const n = r >= 0 && korak.vrsta !== "cilj" ? PREDLOG.noge[NP.koraki[r].i] : null;
  const trip = ZIVO && n ? n.trip_id : null;
  if (trip === NP.vozilaTrip) return;
  if (NP.vozilaZanka) NP.vozilaZanka.stop();
  NP.vozilaZanka = null;
  NP.vozilo = null;
  NP.vozilaTrip = trip;
  risiVozilo(n);
  if (!trip) return;
  NP.vozilaZanka = pollVehicles(`/api/vehicles?trip=${encodeURIComponent(trip)}`, (d) => {
    if (NP.vozilaTrip !== trip) return;
    NP.vozilo = Array.isArray(d) && d.length ? d[0] : null;
    risiVozilo(n);
  });
}

// Kot na drugih zemljevidih: od daleč vozilo od zgoraj v smeri vožnje, od
// blizu model v 3D (`vozila3d.js`). Prej pilula z imenom -- edina oznaka
// vozila, ki se ni ujemala z nobenim drugim zemljevidom (David, 23. 10. 2026).
// Ikona je element nad platnom in bi model prekrila, zato ne oboje hkrati.
const np3D = () => !!K && K.map.getZoom() >= AVTO_3D_OD;

function risiVozilo(n) {
  if (!K) return;
  const v = NP.vozilo;
  NP.voziloNoga = n;
  if (!v || !n) {
    if (NP.voziloOznaka) { NP.voziloOznaka.remove(); NP.voziloOznaka = null; }
    postaviVozilo3D();
    return;
  }
  const vlak = n.network === "zeleznica";
  if (!NP.voziloOznaka) {
    const el = document.createElement("div");
    el.className = "np-vozilo";
    NP.voziloOznaka = new K.ml.Marker({
      element: el, rotationAlignment: "map", pitchAlignment: "viewport",
    }).setLngLat([v.lon, v.lat]).addTo(K.map);
    if (!NP.zoom3D) {
      NP.zoom3D = true;
      K.map.on("zoom", postaviVozilo3D);
    }
  }
  const el = NP.voziloOznaka.getElement();
  el.title = imeVoznje(n);
  el.innerHTML = voziloSvg(30, (v.speed_kmh || 0) >= 3,
    vlak ? TRAIN_INK : AGENCY_INK[agencijaModela(n)] || BUS_INK, { vlak });
  NP.voziloOznaka.setLngLat([v.lon, v.lat]).setRotation(v.bearing || 0);
  postaviVozilo3D();
}

// Mestni LPP ima v voznem redu svoj ID, model in barvo pa deli s primestnim.
const agencijaModela = (n) => (n.agency === "lpp" ? "1118" : n.agency);

function postaviVozilo3D() {
  const v = NP.vozilo, n = NP.voziloNoga;
  const vlak = !!n && n.network === "zeleznica";
  const blizu = !!v && !!n && !!NP.voziloOznaka && np3D();
  if (NP.voziloOznaka) NP.voziloOznaka.getElement().hidden = blizu;
  for (const [k, p] of Object.entries(NP.vozilo3d)) {
    if (!blizu || k !== (vlak ? "vlak" : "avto")) p.nastavi([]);
  }
  if (!blizu) return;
  const model = vlak ? vlakModel(n) : AGENCY_INK[agencijaModela(n)] ? agencijaModela(n) : "drugi";
  plastVozila(vlak).nastavi([{ lon: v.lon, lat: v.lat, smer: v.bearing || 0, model }]);
}

// Plast nastane ob prvem vozilu od blizu: senčilnik ni zastonj, pot vso pot
// peš ali od daleč ga ne rabi. Pod „ti“, nad potjo in postajališči.
function plastVozila(vlak) {
  const k = vlak ? "vlak" : "avto";
  if (!NP.vozilo3d[k]) {
    NP.vozilo3d[k] = vlak
      ? plast3D({ id: "np-vlak-3d", modeli: vlakModeli(TRAIN_INK), vidna: np3D,
                  povecava: vlakPovecava })
      : avtobusi3D({ id: "np-avto-3d", inki: { ...AGENCY_INK, drugi: BUS_INK }, vidna: np3D,
                     povecava: avtoPovecava });
    K.map.addLayer(NP.vozilo3d[k].plast, "k-jaz");
  }
  return NP.vozilo3d[k];
}

// ---- osvežitev, shramba, konec

/** Zamude in tveganje z zadnjega odgovora v pot, ki je na zaslonu. */
function prepisiZamude(d) {
  d.predlog.noge.forEach((n) => {
    const moja = PREDLOG.noge.find((m) => m.vrsta === "voznja"
      && m.trip_id === n.trip_id && m.od_seq === n.od_seq);
    if (n.vrsta !== "voznja" || !moja) return;
    for (const k of ["zamuda", "zamuda_izstop", "odhod_ocena", "prihod_ocena", "brez_podatka",
                     "na_poti"]) {
      moja[k] = n[k];
    }
  });
  for (const k of ["odhod_ocena", "prihod_ocena", "prestopi", "zanesljivost"]) {
    PREDLOG[k] = d.predlog[k];
  }
}

function shraniNaPoti() {
  if (!AKTIVNA) return;
  AKTIVNA.predlog = PREDLOG;
  AKTIVNA.stanje = { ...(AKTIVNA.stanje || {}), korak: NP.k };
  NA_POTI.zapisi(AKTIVNA);
}

async function osveziNaPoti() {
  if (!NP.aktivno || !ZIVO || NP.niVec) return;
  let r;
  try {
    r = await fetch(`/api/pot/podrobno?${naslovPodrobno()}&geometrija=0`);
  } catch (e) {
    NP.napaka = "Brez povezave";
  }
  if (r && r.status === 404) NP.niVec = true;   // vožnje po novem voznem redu ni več
  else if (r && !r.ok) NP.napaka = "Strežnik ne odgovarja";
  if (!r || !r.ok) {
    NP.cakaOsvezitev = 0;
    posodobiVse(false);
    return;
  }
  prepisiZamude(await r.json());
  NP.napaka = null;
  NP.cakaOsvezitev = 0;
  // Ure korakov so se z zamudami premaknile; napredek ostane.
  NP.koraki = korakiPoti(PREDLOG);
  AKTIVNA.osvezeno = Date.now();
  shraniNaPoti();
  posodobiVse(false);
}

/** Osveževanje zamud na poti: vsakih 30 s in ob vrnitvi na stran takoj
 *  (`pollWhileVisible`). Le za pot, ki je zdaj -- in ta to postane tudi med
 *  odprto stranjo (jutrišnja pot, odprta zvečer). */
function zivoZanka() {
  if (NP.aktivno && ZIVO && !NP.osvezi) NP.osvezi = pollWhileVisible(osveziNaPoti, 30000);
}

document.addEventListener("visibilitychange", () => {
  if (!document.hidden && NP.aktivno && ZIVO) NP.cakaOsvezitev = Date.now() + 4000;
});

/** Kje si po poti, kadar lege ni: na postajališču, s katerega greš, ali na
 *  tistem, kjer izstopiš; pred prvim korakom doma. */
function kjeSiPoPoti() {
  const korak = NP.koraki[NP.k];
  const n = korak && PREDLOG.noge[korak.i];
  if (!n || korak.vrsta === "cilj") return doKod();
  if (korak.vrsta === "cakanje") return n.od_ll;
  if (korak.vrsta === "voznja") return n.do_ll;
  return n.od_ll || odKod();
}

/** Nova pot do istega cilja, z istim rokom: zamujeno, prestop ne drži. */
function novaPot(odKje) {
  const q = new URLSearchParams();
  const l = svezaLega();
  const od = odKje || (l ? [l.lat, l.lon] : kjeSiPoPoti());
  q.set("od", `${od[0].toFixed(5)},${od[1].toFixed(5)}`);
  q.set("do", `${Number(Q.get("do_lat")).toFixed(5)},${Number(Q.get("do_lon")).toFixed(5)}`);
  const rok = AKTIVNA && AKTIVNA.vprasanje && AKTIVNA.vprasanje.rok;
  if (rok && rok > Date.now() / 1000) {
    q.set("tam", ura(rok));
    const dan = new Date(rok * 1000).toLocaleDateString("sv-SE", { timeZone: "Europe/Ljubljana" });
    if (dan !== todayIso()) q.set("dan", dan);
  }
  if (KOLO) q.set("kolo", "1");
  if (Q.get("hoje")) q.set("hoje", Q.get("hoje"));
  // Seznam ve, da je to nadomestna pot: izbrana zamenja tekočo brez vprašanja.
  q.set("nova", "1");
  location.href = `/app/pot?${q}`;
}

/** Potekla pot na zaslonu: vodenje se ustavi, koraki ostanejo za pogled nazaj. */
function potKoncana() {
  NP.aktivno = false;
  clearInterval(NP.ura);
  if (NP.osvezi) NP.osvezi.stop();
  if (NP.vozilaZanka) NP.vozilaZanka.stop();
  NP.vozilaTrip = null;
  NP.vozilo = null;
  risiVozilo(null);
  if (NP.korakiDom) NP.korakiDom.appendChild($("#koraki"));
  document.body.classList.remove("na-poti");
  delete document.body.dataset.korak;
  koncajVodenje();
  $("#stanje").className = "pot-stanje";
  $("#stanje").innerHTML = `Pot je končana. <a href="${escapeHtml(nazajUrl())}">Nova pot ›</a>`;
}

function koncajPot() {
  // Pot, ki ostane čez zaprto aplikacijo, se ne konča z enim zgrešenim
  // dotikom: prvi vpraša, drugi v štirih sekundah konča.
  const gumb = $("#vod-konec");
  const korak = NP.koraki[NP.k];
  if (korak.vrsta !== "cilj" && !NP.potrdi) {
    gumb.textContent = "res končam?";
    gumb.classList.add("je-potrdi");
    NP.potrdi = setTimeout(() => { NP.potrdi = 0; risiNaPoti(false); }, 4000);
    return;
  }
  clearTimeout(NP.potrdi);
  NA_POTI.koncaj();
  NP.aktivno = false;
  location.replace(nazajUrl());
}

function zloziPlosco(zlozena) {
  $("#vod-spodaj").classList.toggle("je-zlozena", zlozena);
  $("#vod-rocaj").setAttribute("aria-expanded", String(!zlozena));
  $("#vod-rocaj").setAttribute("aria-label", zlozena ? "pokaži vso pot" : "skrij podrobnosti");
  try { localStorage.setItem(NP_PLOSCA_KLJUC, zlozena ? "1" : "0"); } catch (e) { /* ni nujno */ }
}

$("#vod-rocaj").addEventListener("click", () =>
  zloziPlosco(!$("#vod-spodaj").classList.contains("je-zlozena")));
// Poteg ročaja navzdol zloži, navzgor razpre -- kot spodnja plošča v Androidu.
(() => {
  let y0 = null;
  const r = $("#vod-rocaj");
  r.addEventListener("pointerdown", (e) => { y0 = e.clientY; });
  r.addEventListener("pointerup", (e) => {
    if (y0 == null) return;
    const dy = e.clientY - y0;
    y0 = null;
    if (Math.abs(dy) < 24) return;
    e.preventDefault();
    zloziPlosco(dy > 0);
  });
})();

document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-nova]");
  if (!b) return;
  // Vozni red se je spremenil: isto vprašanje kot prej, od istega kraja.
  if (b.dataset.nova === "znova") {
    novaPot(odKod());
    return;
  }
  // Pri prestopu, ki ne drži, od kraja prestopa -- tam boš, ko izstopiš.
  const t = b.dataset.nova === "prestop" && ogrozenPrestop();
  const pr = t && PREDLOG.noge.find((n) => n.vrsta === "voznja" && n.do === t.t.kje);
  novaPot(pr && pr.do_ll);
});
$("#vod-nova").addEventListener("click", () => novaPot(null));
document.addEventListener("click", (e) => {
  if (!e.target.closest("[data-lega]")) return;
  prosiZaSmer();
  zacniLego().then(() => {
    NP.legaNapaka = null;
    posodobiVse(true);
  }).catch((err) => {
    NP.legaNapaka = err.message;
    posodobiVse(false);
  });
});

function zacniNaPoti() {
  NP.aktivno = true;
  NP.koraki = korakiPoti(PREDLOG);
  NP.k = Math.min((AKTIVNA.stanje && AKTIVNA.stanje.korak) || 0, NP.koraki.length - 1);
  V.aktivno = true;
  V.sledi = true;
  document.body.classList.add("vodenje", "na-poti");
  $("#vod-manever").hidden = false;
  $("#vod-spodaj").hidden = false;
  $("#vod-pot").hidden = false;
  NP.korakiDom = $("#koraki").parentNode;
  $("#vod-pot").appendChild($("#koraki"));
  // Privzeto zložena: med potjo je zemljevid pomembnejši od seznama, vrstica
  // pod njim pa pove, kar je treba vedeti (vozilo z rezervo, kaj pride).
  let zlozena = true;
  try { zlozena = localStorage.getItem(NP_PLOSCA_KLJUC) !== "0"; } catch (e) { /* zložena */ }
  zloziPlosco(zlozena);
  zakleniZaslon();
  const korak = NP.koraki[NP.k];
  if (korak.vrsta === "hoja") pripraviNogo(korak.i);
  else V.i = korak.vrsta === "cilj" ? -1 : korak.i;
  voziloKoraka();
  risiCrte();
  requestAnimationFrame(() => {
    if (K) K.map.resize();
    posodobiVse(true);
  });
  // Ura teče tudi, ko stojiš: odštevanje in korak po uri se premikata sama.
  NP.ura = setInterval(() => {
    if (document.hidden) return;
    // Pot, odprta dan prej, postane živa sama: zamude, vozilo, opozorila.
    if (!ZIVO && DATUM && jeZdaj(DATUM)) {
      ZIVO = true;
      zivoZanka();
      voziloKoraka();
    }
    posodobiVse(false);
  }, 5000);
  // Prvo osvežitev opravi `nalozi`; zanka začne pol minute za njo.
  setTimeout(zivoZanka, 30000);
}

// Pot, ki jo je kdo poslal ali odprl s seznama, se da izbrati tudi tu. Ista,
// ki je že izbrana, se nadaljuje z napredkom; druga tekočo zamenja šele na
// drugi dotik -- kot pri seznamu (`pot.js` `sprejmi`).
$("#zacni").addEventListener("click", () => {
  if (!PREDLOG) return;
  const izbrana = NA_POTI.beri();
  if (izbrana && izbrana.spec.noge === Q.get("noge")) {
    location.assign(NA_POTI_STRAN);
    return;
  }
  const gumb = $("#zacni");
  if (izbrana && !NP.zamenjaj) {
    gumb.textContent = "zamenjam tekočo pot?";
    NP.zamenjaj = setTimeout(() => { NP.zamenjaj = 0; gumb.textContent = "Začni pot"; }, 4000);
    return;
  }
  clearTimeout(NP.zamenjaj);
  const spec = {};
  for (const k of ["noge", "od_lat", "od_lon", "do_lat", "do_lon", "kmh"]) {
    if (Q.get(k)) spec[k] = k === "noge" ? Q.get(k) : Number(Q.get(k));
  }
  spec.date = PREDLOG.datum;
  const ok = NA_POTI.zapisi({
    v: 1, sprejeto: Date.now(), spec, predlog: PREDLOG, osvezeno: Date.now(),
    vprasanje: { rok: Q.get("rok") ? Number(Q.get("rok")) : null, kmh: KMH,
                 hoje: Q.get("hoje") ? Number(Q.get("hoje")) : null, dan: Q.get("dan") || null },
    stanje: { korak: 0 },
  });
  if (ok) location.replace(NA_POTI_STRAN);
});

// ---------------------------------------------------------------- nalaganje

function naslovPodrobno() {
  const p = new URLSearchParams();
  for (const k of ["noge", "od_lat", "od_lon", "do_lat", "do_lon", "date", "kmh", "rok"]) {
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
  // Dan vprašanja, ne dan vožnje: ponoči je nočni avtobus včerajšnji, seznam
  // pa je bil iskan za danes. Stare povezave `dan` nimajo in sta ista.
  const dan = Q.get("dan") || Q.get("date");
  if (dan && dan !== todayIso()) q.set("dan", dan);
  if (KOLO) q.set("kolo", "1");
  if (Q.get("hoje")) q.set("hoje", Q.get("hoje"));
  return q.toString() ? `/app/pot?${q}` : "/app/pot";
}

// „‹ nazaj na predloge“ je korak nazaj, kadar smo prišli s seznama: brskalnik
// ga vrne celega, z imeni krajev in mestom na seznamu. Prej je bila nova
// navigacija: zgodovina je rasla, sistemski nazaj je vodil spet sem (zanka
// seznam ↔ podrobnosti), polja pa so imela koordinate (presoja 18. 10. 2026).
// Isto s strani zvez (iskalnik vlakov in avtobusov): dotik zveze s prestopi
// odpre to stran (`journey.dopolni_pot`), nazaj pa gre na zveze, ne na pot od
// vrat do vrat z istima postajama.
const PRISEL_S = (() => {
  try {
    const r = document.referrer && new URL(document.referrer);
    if (!r || r.origin !== location.origin) return null;
    if (r.pathname === "/app/pot") return "pot";
    if (r.pathname === "/app/train" || r.pathname === "/app/bus") return "zveze";
  } catch (e) { /* neveljaven referrer: ni naša stran */ }
  return null;
})();
if (PRISEL_S === "zveze") $("#nazaj").textContent = "‹ nazaj na zveze";

$("#nazaj").addEventListener("click", (ev) => {
  if (PRISEL_S && history.length > 1) {
    ev.preventDefault();
    history.back();
  }
});

// Pošlji pot: naslov nosi vožnje in oba kraja, prejemnik dobi isto pot. Dan
// mora biti zraven -- brez njega (danes ga naslov ne nosi) bi jutri odprl
// jutrišnje vožnje z istimi id-ji ali „vožnje ta dan ni“. Imena krajev ne gredo
// v besedilo (`stavekPoti`); `utm_source=poslano` kot v oknu vožnje.
let DATUM = null;
$("#poslji").addEventListener("click", async () => {
  if (!PREDLOG) return;
  const url = new URL(location.href);
  if (DATUM && !url.searchParams.get("date")) url.searchParams.set("date", DATUM);
  url.searchParams.set("utm_source", "poslano");
  const b = $("#poslji");
  const rez = await posljiPovezavo(document.title, stavekPoti(PREDLOG), url.toString());
  if (rez !== "kopirano" && rez !== "ni šlo") return;
  b.querySelector("span").textContent = rez;
  b.classList.add("je-poslano");
  setTimeout(() => {
    b.querySelector("span").textContent = "Pošlji";
    b.classList.remove("je-poslano");
  }, 2500);
});

/** Pot na zaslon: glava, koraki, zemljevid. Na poti dvakrat -- iz shrambe
 *  takoj, nato sveža s strežnika. */
function prikazi(pr, datum) {
  PREDLOG = pr;
  DATUM = datum;
  $("#poslji").hidden = false;
  $("#stanje").textContent = "";
  $("#glava").innerHTML = `
    <div class="podr-ure"><strong>${ura(pr.odhod_ocena || pr.odhod)}</strong>
      → <strong>${ura(pr.prihod_ocena || pr.prihod)}</strong></div>
    <div class="podr-meta">${minute(trajanjePrikaz(pr))}${
      pr.hoje_s >= 60 ? ` · ${minute(pr.hoje_s)} ${KOLO ? "do postaj" : "hoje"}` : ""} · ${
      pr.prestopov === 0 ? "brez prestopa"
        : `${pr.prestopov} ${sklon(pr.prestopov, "prestop")}`} · ${dayLabel(danOdhoda(pr))}</div>`;
  $("#koraki").innerHTML = korakiHtml(pr);
  NP.trasa = {};
  narisi(pr);
  // Pot, ki je že izbrana, se nadaljuje; druga se izbere.
  const izbrana = !NA_POTI_NACIN && NA_POTI.beri();
  const zacni = $("#zacni");
  zacni.hidden = NA_POTI_NACIN;
  if (izbrana && izbrana.spec.noge === Q.get("noge")) zacni.textContent = "Nadaljuj pot";
}

/** Ali je pot „zdaj“ -- isto pravilo kot strežnikov `zivo` (`api._zdaj_za_dan`). */
function jeZdaj(datum) {
  const vceraj = new Date(`${todayIso()}T12:00:00`);
  vceraj.setDate(vceraj.getDate() - 1);
  const ura_ = Number(new Date().toLocaleTimeString("sv-SE", { timeZone: "Europe/Ljubljana",
                                                               hour: "2-digit" }));
  return datum === todayIso() || (datum === vceraj.toLocaleDateString("sv-SE") && ura_ < 4);
}

async function nalozi() {
  $("#nazaj").href = nazajUrl();
  if (NA_POTI_NACIN && !AKTIVNA) {
    $("#stanje").innerHTML = 'Nisi na nobeni poti — izbrana je končana ali je potekla. '
      + '<a href="/app/pot">Poišči pot ›</a>';
    return;
  }
  const p = naslovPodrobno();
  if (!p.get("noge")) {
    $("#stanje").textContent = "Poti v naslovu ni.";
    $("#stanje").className = "pot-stanje je-napaka";
    return;
  }
  // Na poti je zadnja shranjena pot takoj na zaslonu, tudi brez omrežja --
  // aplikacija se odpre sredi vožnje, v predoru ali ob slabem signalu.
  // Tudi kartica s seznama (brez postankov) pove, kje izstopiš in kam
  // prestopiš -- prva podrobna osvežitev jo dopolni.
  const izShrambe = !!AKTIVNA && AKTIVNA.predlog.noge.length > 0;
  const polna = izShrambe && AKTIVNA.predlog.noge.some((n) => n.postanki);
  if (izShrambe) {
    ZIVO = jeZdaj(AKTIVNA.spec.date);
    prikazi(AKTIVNA.predlog, AKTIVNA.spec.date);
    zacniNaPoti();
  } else {
    $("#stanje").textContent = "Nalagam …";
  }
  try {
    const r = await fetch(`/api/pot/podrobno?${p}`);
    if (!r.ok) {
      const telo = await r.json().catch(() => ({}));
      const e = new Error(telo.detail || `strežnik je vrnil ${r.status}`);
      e.status = r.status;
      throw e;
    }
    const d = await r.json();
    ZIVO = Boolean(d.zivo);
    if (izShrambe) {
      if (polna) prepisiZamude(d);
      else prikazi(d.predlog, d.datum);
      NP.koraki = korakiPoti(PREDLOG);
      AKTIVNA.osvezeno = Date.now();
      shraniNaPoti();
      voziloKoraka();               // strežnik zna reči „zdaj“ drugače kot ura
      posodobiVse(!polna);
    } else {
      prikazi(d.predlog, d.datum);
    }
  } catch (e) {
    if (izShrambe) {
      // Pot je na zaslonu iz shrambe; plošča pove, kaj je narobe in kako
      // stare so zamude (`risiPlosco`).
      if (e.status === 404) NP.niVec = true;
      else NP.napaka = e.status ? "Strežnik ne odgovarja" : "Brez povezave";
      posodobiVse(false);
      return;
    }
    $("#stanje").className = "pot-stanje je-napaka";
    $("#stanje").textContent = e.status ? e.message
      : "Brez povezave — pot se naloži, ko bo omrežje.";
  }
}

$("#koraki").addEventListener("click", (e) => {
  const v = e.target.closest("[data-vodi]");
  if (v) {
    const i = Number(v.dataset.vodi);
    if (NP.aktivno) {
      // Na poti je „vodi me“ skok na ta korak: potnik ve, kje je.
      const k = NP.koraki.findIndex((s) => s.vrsta === "hoja" && s.i === i);
      if (k >= 0) {
        NP.zacel = true;
        nastaviKorak(k);
        risiNaPoti(true);
      }
    } else {
      zacniVodenje(i);
    }
    return;
  }
  const b = e.target.closest(".hoja-gumb[data-korak]");
  if (b) {
    V.sledi = false;
    priblizaj(Number(b.dataset.korak));
  }
});
$("#cela").addEventListener("click", () => priblizaj(null));

nalozi();
LEGA.poslusaj(obLegi);
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
    if (V.aktivno && e.originalEvent) {
      V.sledi = false;
      $("#vod-sledi").hidden = !JAZ && !NP.aktivno;
    }
  });
  if (JAZ) pkJaz(K.map, JAZ);
  if (PREDLOG) narisi(PREDLOG);
});
