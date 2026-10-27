"use strict";

// Skupno za /app in /app/train/{st}. Nalozi se pred dashboard.js oz. train.js.

// Preimenovanje sztrack -> kajros (3. 9. 2026) je premaknilo tudi kljuce v
// localStorage. Brez tega bi shranjene poti, nedavne iskanja in izbrani nacin
// prikaza ob prvem obisku tiho izginili -- za uporabnika izguba podatkov, ki
// je ni povzrocil. Selitev je enkratna in samo kopira; starega ne brise, da se
// da na staro razlicico se vrniti. **Odstrani po 1. 12. 2026.**
(function preseliKljuce() {
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const star = localStorage.key(i);
      if (!star || !star.startsWith("sztrack:")) continue;
      const nov = "kajros:" + star.slice("sztrack:".length);
      if (localStorage.getItem(nov) === null) {
        localStorage.setItem(nov, localStorage.getItem(star));
      }
    }
  } catch (e) {
    // Zasebno okno ali blokiran dostop do shrambe: selitev ni nujna.
  }
})();

// Meje so v MINUTAH in barva se doloci iz iste zaokrozene vrednosti, kot jo
// izpise `delayLabel`. Prej so bile v sekundah (<= 60 s = tocno) in 61 s je
// pisalo "+1" oranzno, 60 s pa "+1" sivo -- ista stevilka, dve barvi. Barva
// ne sme pripovedovati druge zgodbe kot stevilka poleg nje.
const DELAY_RAMP = [
  { maxMin: 0, color: "#7c8698", label: "točno" },
  { maxMin: 5, color: "#f2a87e", label: "1–5 min" },
  { maxMin: 15, color: "#e07b45", label: "5–15 min" },
  { maxMin: Infinity, color: "#b85417", label: "nad 15 min" },
];

// Barva po razredu, ki ga doloci STREZNIK. Pragovi so pravilo in zivijo v
// `stats.opis_zamude()`; barva je oblikovanje in sme biti tu.
const RAZRED_BARVA = {
  "tocno": "#7c8698", "1-5": "#f2a87e", "5-15": "#e07b45", "nad-15": "#b85417",
};

// **Vse spodnje funkcije sprejmejo dvoje**: streznikov objekt `zamuda`
// (`{s, min, razred, vrsta, prezgodaj}`) ali gole sekunde. Objekt ima minuto
// in razred ze izracunana po enem samem pravilu na strezniku -- glej
// `stats.opis_zamude()`. Sekunde ostanejo za mesta, kjer streznik objekta
// (se) ne poslje; racun je tam isti, a je to podvojeno pravilo in naj se ne
// siri. Nov odjemalec (Android) naj bere samo objekt.
function delayMin(z) {
  if (z == null) return null;
  if (typeof z === "object") return z.min;
  return Math.round(z / 60);
}

function delayColor(z) {
  if (z == null) return "#6b7480";
  if (typeof z === "object" && z.razred) return RAZRED_BARVA[z.razred] || "#6b7480";
  const min = delayMin(z);
  return (DELAY_RAMP.find((step) => min <= step.maxMin) || DELAY_RAMP[DELAY_RAMP.length - 1]).color;
}

function delayLabel(z) {
  // Feed ima locljivost 60 s -- zaokrozimo na minute in sekund ne kazemo nikoli.
  const m = delayMin(z);
  if (m == null) return "?";
  return (m > 0 ? "+" : "") + m;
}

// "-5 min" je za potnika uganka, "5 min prej" ni. Barva ostane siva, ker to
// res ni zamuda -- in prav zato mora povedati beseda. `kratko` je za ozke
// stolpce, kjer za "min" ni prostora.
function delayText(z, kratko) {
  const m = delayMin(z);
  if (m == null) return kratko ? "?" : "? min";
  // Prag mora biti na ZAOKROZENI minuti, ne na sekundah. Pri `s <= -60` je
  // -45 s dalo "-1", ker `delayLabel` zaokrozi -- ista minuta, dva zapisa.
  if (m <= -1) return kratko ? `${-m} prej` : `${-m} min prej`;
  return kratko ? delayLabel(z) : `${delayLabel(z)} min`;
}

// Ali je vrednost "prezgodaj". Streznik to ze pove (`zamuda.prezgodaj`),
// sicer po isti zaokrozeni minuti kot `delayText`.
// "-1 min za prestop" je natanko primer, ko zveza NE drzi -- torej tisti, kjer
// mora potnik razumeti brez ugibanja. Nicla ni "0 min za prestop" (videti kot
// podatek), ampak "brez rezerve". Uporabljata iskalnik zvez in pot.
function prestopText(mins) {
  if (mins < 0) return `zmanjka ${Math.abs(mins)} min`;
  if (mins === 0) return "brez rezerve";
  return `${mins} min za prestop`;
}

/** Koliko minut ostane za prestop, ali `null`, kadar zamud ne poznamo.
 *
 * Racuna se iz ZAOKROZENIH minut, ne iz sekund: vse tri stevilke stojijo na
 * zaslonu druga ob drugi in bralec, ki jih sesteje, mora priti do iste. Ista
 * past kot pri razredu zamude.
 */
function preostanekPrestopa(nacrtovanoS, zamudaPrvega, zamudaDrugega) {
  const d1 = delayMin(zamudaPrvega);
  const d2 = delayMin(zamudaDrugega);
  if (d1 == null || d2 == null) return null;
  return Math.floor(nacrtovanoS / 60 + 0.5) - d1 + d2;
}

/** Trajanje poti med urama, ki ju stran pokaže. `trajanje_s` je po voznem
 * redu; kadar prva vožnja zamuja, zadnja pa ne (ali obratno), je stalo
 * "18:45 → 19:43 · 1 h 34" (30. 9. 2026). */
function trajanjePrikaz(p) {
  return (p.prihod_ocena || p.prihod) - (p.odhod_ocena || p.odhod);
}

/** Pot od vrat do vrat v enem stavku, za sporočilo ob poslani povezavi:
 * „Odhod ob 07:31 · LPP 6 (Bavarski dvor 07:36) › RG 318 · na cilju ob 08:52“.
 *
 * Imen krajev ni: kraj je lahko shranjena točka („dom“), in povezava ne sme
 * povedati, da je tista točka tvoj dom (strani.md). Vstopno postajališče je
 * javno ime -- pove, kje se dobita. Ure so te s kartice. */
function stavekPoti(p) {
  const u = (ts) => new Date(ts * 1000).toLocaleTimeString("sl-SI",
    { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Ljubljana" });
  const odhod = p.odhod_ocena || p.odhod;
  const dan = new Date(odhod * 1000).toLocaleDateString("sv-SE", { timeZone: "Europe/Ljubljana" });
  const voznje = p.noge.filter((n) => n.vrsta === "voznja");
  const veriga = voznje.map((n, i) => (i === 0
    ? `${imeVoznje(n)} (${n.od} ${u(n.odhod_ocena || n.odhod)})` : imeVoznje(n))).join(" › ");
  return [`Odhod${dan === todayIso() ? "" : ` ${dayLabel(dan)}`} ob ${u(odhod)}`,
          veriga || "peš", `na cilju ob ${u(p.prihod_ocena || p.prihod)}`].join(" · ");
}

/** Rezerva prestopa na poti od vrat do vrat, po urah, ki jih stran kaže.
 *
 * Prva vožnja šteje z zamudo ob IZSTOPU -- vmes rezervo porabi ali izgubi --,
 * vožnja brez podatka pa po voznem redu, tako kot jo pokaže ura. Prej je
 * veljala zamuda ob vstopu in "ne vemo" pri eni sami vožnji je skril tudi
 * znano zamudo druge (30. 9. 2026: 18 od 112 prestopov za 3 min ali več
 * drugače od ur na strani). `null`, kadar ne vemo za nobeno.
 */
function rezervaPrestopa(t, pred, po) {
  const z1 = pred && (pred.zamuda_izstop || pred.zamuda);
  const z2 = po && po.zamuda;
  if (delayMin(z1) == null && delayMin(z2) == null) return null;
  return preostanekPrestopa(t.nacrtovano_s, z1 == null ? 0 : z1, z2 == null ? 0 : z2);
}

/** Ura ob zamudi, kot jo zaslon pokaže: vozni red + ZAOKROŽENA minuta (ISO).
 *
 * Prej vozni red + sekunde: `hhmm` je sekunde odrezal, žeton pa minuto
 * zaokrožil -- „21:42 ~~21:45~~ · 2 min prej“. Isto pravilo kot strežnikov
 * `stats.ura_z_zamudo` (presoja 18. 10. 2026). */
function pricakovanaUra(schedIso, z) {
  return new Date(new Date(schedIso).getTime() + delayMin(z) * 60000).toISOString();
}

function isEarly(z) {
  if (z == null) return false;
  if (typeof z === "object") return !!z.prezgodaj;
  return delayMin(z) <= -1;
}

const TIME_FMT = new Intl.DateTimeFormat("sl-SI", {
  timeZone: "Europe/Ljubljana", hour: "2-digit", minute: "2-digit", hour12: false,
});

// Danasnji prometni dan po ljubljanskem casu. "sv-SE" je najkrajsa pot do
// ISO oblike; `toISOString()` bi dal UTC in bi se cez polnoc zlagal za dan.
const todayIso = () => new Date().toLocaleDateString("sv-SE", { timeZone: "Europe/Ljubljana" });

function hhmm(iso) {
  return iso ? TIME_FMT.format(new Date(iso)) : "—";
}

const DATE_FMT = new Intl.DateTimeFormat("sl-SI", {
  timeZone: "Europe/Ljubljana", day: "numeric", month: "numeric",
});

function dayLabel(isoDate) {
  return isoDate ? DATE_FMT.format(new Date(isoDate + "T12:00:00")) : "—";
}

// ---------- podlaga zemljevida ----------
//
// **Vektorska podlaga OpenFreeMap** (22. 9. 2026): odprta koda, brez kljuca,
// brez registracije in brez omejitve ogledov, podatki OpenStreetMap. Risanje
// je MapLibre sam na vseh zemljevidih -- velikem (`dashboard.js`), obeh
// straneh poti in v oknu voznje (`pot_karta.js`) --, ker Leaflet kamere ne
// zna nagniti. Od tu rabijo samo konstante.
//
// Prej je bil Esri "Dark Gray Canvas": prave ploscice samo do z16, imena ulic
// vpecena v podlago in brez moznosti, da bi se ugasnila posebej. Vektorska
// podlaga je ostra pri vsakem priblizku, barve so iz `base.css`, napisi pa so
// svoje plasti (`podlaga.json`, `metadata.kajros:napisi`).
//
// **Esri ostane rezerva**, kadar slog ali opis ploscic pade pred prvim
// izrisom. Brez WebGL2 pa zemljevida ni: MapLibre 6 ga zahteva in tudi Esri
// bi risal on.
const ESRI_ATTR = 'podlaga &copy; <a href="https://www.esri.com/">Esri</a>, HERE, Garmin, '
  + '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';
const ESRI_CANVAS = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas";
// Razlicica je v POTI in ne v poizvedbi: `maplibre-gl.mjs` uvaza sosedi po
// relativnem imenu, Cloudflare pa statiko na robu drzi stiri ure. Ob nadgradnji
// bi sicer nova glava dobila staro telo.
const MAPLIBRE_POT = "/static/maplibre-6.10.0";

function imaWebGL2() {
  try {
    return !!document.createElement("canvas").getContext("webgl2");
  } catch (e) {
    return false;
  }
}

// MapLibrova stisnjena navedba vira (i) je ob nalaganju razprta in se zapre
// šele ob vleki: na telefonu je trak „OpenFreeMap © OpenMapTiles …“ ležal čez
// zemljevid, dokler se ga ni premaknilo (David, 22. 10. 2026: „mora biti
// privzeto zagrnjen“). Smernice OSMF (Licence/Attribution Guidelines) dovolijo
// navedbo zapreti sama po petih sekundah in je ne zahtevajo ob vsakem odprtju,
// dokler jo (i) odpre. Zato razprta samo prvič na napravi, pet sekund.
const NAVEDBA_MS = 5000;
const NAVEDBA_KLJUC = "kajros:navedba";

function zapriNavedbo(map) {
  const el = map.getContainer().querySelector(".maplibregl-ctrl-attrib");
  if (!el) return;
  let cas = null;
  const razprta = () => {
    let videna = false;
    try {
      videna = localStorage.getItem(NAVEDBA_KLJUC) === "1";
      localStorage.setItem(NAVEDBA_KLJUC, "1");
    } catch (e) { /* zasebno okno: vsakič pet sekund */ }
    const zapri = () => el.classList.remove("maplibregl-compact-show");
    if (videna) zapri();
    else cas = setTimeout(zapri, NAVEDBA_MS);
  };
  // MapLibre jo razpre šele, ko pridejo viri z navedbo (`styledata`), ne ob
  // `new Map` -- zato čakamo na razred, ne na dogodek zemljevida.
  if (el.classList.contains("maplibregl-compact-show")) {
    razprta();
  } else {
    const opazovalec = new MutationObserver(() => {
      if (!el.classList.contains("maplibregl-compact-show")) return;
      opazovalec.disconnect();
      razprta();
    });
    opazovalec.observe(el, { attributes: true, attributeFilter: ["class"] });
  }
  // Kdor se je navedbe dotaknil, jo upravlja sam.
  el.addEventListener("click", () => clearTimeout(cas), { once: true });
}

// Naslovi obvestil SŽ kricijo in ponavljajo znacko nad sabo: "DELA NA PROGI:
// Obcasna zapora ..." stoji pod zetonom "dela na progi". Predpono odrezemo --
// v sestih od sestnajstih obvestil je ista beseda dvakrat, v verzalkah.
function alertTitle(header) {
  const m = /^[A-ZČŠŽĆĐ][A-ZČŠŽĆĐ0-9 .\-]{2,40}:\s*/.exec(header || "");
  const t = m ? header.slice(m[0].length) : (header || "");
  return t.charAt(0).toUpperCase() + t.slice(1);
}

// Slovenscina ima dvojino in rodilnik mnozine, zato "0 odhodi" in "2 vlakov"
// nista pravilna. Oblike so [1, 2, 3-4, 0 in 5+]; odloca n mod 100.
const SKLONI = {
  odhodi: ["odhod", "odhoda", "odhodi", "odhodov"],
  prihodi: ["prihod", "prihoda", "prihodi", "prihodov"],
  vlak: ["vlak", "vlaka", "vlaki", "vlakov"],
  voznja: ["vožnja", "vožnji", "vožnje", "voženj"],
  prestop: ["prestop", "prestopa", "prestopi", "prestopov"],
  postanek: ["postanek", "postanka", "postanki", "postankov"],
  postaja: ["postaja", "postaji", "postaje", "postaj"],
  navodilo: ["navodilo", "navodili", "navodila", "navodil"],
  porocilo: ["poročilo", "poročili", "poročila", "poročil"],
  ovira: ["ovira", "oviri", "ovire", "ovir"],
};

function sklon(n, kljuc) {
  const o = SKLONI[kljuc] || SKLONI.vlak;
  const m = Math.abs(n) % 100;
  return m === 1 ? o[0] : m === 2 ? o[1] : (m === 3 || m === 4) ? o[2] : o[3];
}

// Isto sklanjanje kot `journey._fold` v Pythonu: brez tega se iskanje in
// poudarek ne ujameta pri sumnikih ("sentjur" proti "Šentjur"). Bilo je
// prepisano v dveh datotekah -- ista funkcija dvakrat je ista napaka dvakrat.
function fold(s) {
  return String(s).normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

// "1 potnik, 2 potnika, 3 potniki, 5 potnikov" -- odlocata zadnji dve
// stevki, isto kot `pristanek.stevnik()`.
function potnikov(n) {
  const d = n % 100;
  if (d === 1) return `${n} potnik`;
  if (d === 2) return `${n} potnika`;
  if (d === 3 || d === 4) return `${n} potniki`;
  return `${n} potnikov`;
}

// Glagol se ujema s številom: "2 potnika delita", "3 potniki delijo",
// "5 potnikov deli".
function deliGlagol(n) {
  const d = n % 100;
  return d === 2 ? "delita" : d === 3 || d === 4 ? "delijo" : "deli";
}

function pluralRuns(n) {
  if (!n) return "brez zajete vožnje";
  if (n === 1) return "1 vožnja";
  if (n === 2) return "2 vožnji";
  if (n === 3) return "3 vožnje";
  if (n === 4) return "4 vožnje";
  return `${n} voženj`;
}

// ---------- znak, da se nekaj dogaja ----------
//
// Na slabi povezavi je klik izgledal, kot da ni delal: stara vsebina je
// ostala na zaslonu in nic se ni premaknilo tudi petnajst sekund. Zato ena
// sama crta na vrhu strani, ki tece, dokler je katerakoli zahteva v teku.
//
// Ovijemo `fetch` in ne vsakega klicatelja posebej: klicnih mest je cez
// trideset, in tisto, ki bi ga kdo pozabil, bi bilo ravno najpocasnejse.
//
// **Crta se pokaze sele po 400 ms.** Hitre zahteve (in tiste v ozadju, ki
// tecejo na 30 s) tako ne utripajo -- kar se zgodi hitro, ne rabi obvestila.
(function () {
  const izvirni = window.fetch;
  if (typeof izvirni !== "function") return;
  let vTeku = 0;
  let cakalec = null;
  let crta = null;

  const pokazi = () => {
    if (crta) return;
    crta = document.createElement("div");
    crta.className = "nalaganje";
    crta.setAttribute("role", "status");
    crta.setAttribute("aria-label", "nalagam");
    document.body.appendChild(crta);
  };
  const skrij = () => {
    if (cakalec) { clearTimeout(cakalec); cakalec = null; }
    if (crta) { crta.remove(); crta = null; }
  };

  window.fetch = function (...args) {
    vTeku += 1;
    if (vTeku === 1 && !cakalec) cakalec = setTimeout(pokazi, 400);
    return izvirni.apply(this, args).finally(() => {
      vTeku -= 1;
      if (vTeku <= 0) { vTeku = 0; skrij(); }
    });
  };
})();

// ---------- most do nativne aplikacije ----------
//
// `window.Kajros` obstaja SAMO v aplikaciji za Android. V brskalniku ga ni in
// nic, kar je vezano nanj, ne sme nastati -- gumb za budilko, ki ne dela, je
// slabsi od gumba, ki ga ni.
//
// `razlicica()` ni vljudnost: stran se posodobi takoj, aplikacija pa cez
// mesec, zato mora stran vedeti, s cim govori, preden karkoli poklice.
const MOST = (() => {
  const k = window.Kajros;
  if (!k || typeof k.razlicica !== "function") return null;
  try {
    return k.razlicica() >= 1 ? k : null;
  } catch (e) {
    return null;
  }
})();
// Slog, ki velja samo v aplikaciji (dolg pritisk na povezavo, base.css).
if (MOST) document.documentElement.classList.add("v-aplikaciji");

// ---------- navigator.share v aplikaciji ----------
// WebView sistemskega izbirnika nima. Aplikacija ga od mostu 6 odpre sama
// (`Most.poslji`), tu ga oblečemo v spletni standard: stran pošilja z
// `navigator.share` kot v brskalniku, tudi datoteke, in nova vsebina ne rabi
// novega APK (David, 13. 10. 2026). Preklic je `AbortError` kot v Chromu;
// izid aplikacija javi, ko se potnik vrne (`kajrosPoslano`).
if (MOST && !navigator.share && MOST.razlicica() >= 6) {
  const cakajo = new Map();
  window.kajrosPoslano = (id, izbrano) => {
    const c = cakajo.get(id);
    if (!c) return;
    cakajo.delete(id);
    if (izbrano) c.ok();
    else c.ne(new DOMException("Pošiljanje preklicano", "AbortError"));
  };
  const base64 = (f) => new Promise((ok, ne) => {
    const r = new FileReader();
    r.onload = () => ok(String(r.result).split(",", 2)[1] || "");
    r.onerror = () => ne(r.error);
    r.readAsDataURL(f);
  });
  navigator.canShare = (p) => !!p && ["title", "text", "url"].some((k) => p[k] != null)
    || !!(p && p.files && p.files.length);
  navigator.share = async (p = {}) => {
    if (!navigator.canShare(p)) throw new TypeError("Ni česa poslati");
    const files = await Promise.all([...(p.files || [])].map(async (f) => (
      { name: f.name, type: f.type, data: await base64(f) })));
    const id = MOST.poslji(JSON.stringify({ title: p.title, text: p.text, url: p.url, files }));
    // Prazen id: preveč datotek ali ni zapisa. Kot brskalnik, ki ne more.
    if (!id) throw new DOMException("Pošiljanje ni mogoče", "NotAllowedError");
    return new Promise((ok, ne) => cakajo.set(id, { ok, ne }));
  };
}

// ---------- O aplikaciji ----------
//
// Različica in posodobitev sta nativni zaslon (`AplikacijaDejavnost`), do
// katerega vodi vrstica v meniju Več. Do 1.12 ju ni bilo mogoče pogledati
// nikjer. Starejša aplikacija metode nima in vrstica ostane skrita.
function pripniOAplikaciji() {
  const a = document.querySelector(".vec-aplikacija");
  if (!a || !MOST || MOST.razlicica() < 5) return;
  document.documentElement.classList.add("ima-o-aplikaciji");
  const r = navigator.userAgent.match(/Kajros\/([\d.]+)/);
  if (r) a.querySelector("small").textContent = r[1];
  a.addEventListener("click", (e) => {
    // Pred poslušalcem lista, ki bi šel na `href`.
    e.preventDefault();
    e.stopPropagation();
    document.getElementById("vec")?.hidePopover?.();
    MOST.oAplikaciji();
  });
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", pripniOAplikaciji);
else pripniOAplikaciji();

// ---------- orodna vrstica se odzove takoj ----------
//
// Nova stran se izriše šele, ko je naložena (izmerjeno 2. 10. 2026: od dotika
// do slike ~190 ms tudi iz predpomnilnika, prek omrežja dvakrat toliko), do
// takrat pa je bila na zaslonu nespremenjena stara. Nativna vrstica pilulo
// premakne ob dotiku, zato jo tudi ta. Na domači strani izbrane ni: tam bi
// tretja pilula z imenom vrstico prenapolnila, pritisk pokaže plast `:active`.
document.addEventListener("click", (e) => {
  const g = e.target.closest?.(".orodna-g");
  if (!g || g.classList.contains("is-on") || e.defaultPrevented || e.button !== 0
      || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
  const prej = g.parentElement.querySelector(".is-on");
  if (!prej) return;
  prej.classList.remove("is-on");
  g.classList.add("is-on");
  // Nazaj na to stran iz predpomnilnika (gumb nazaj) mora biti izbrana
  // spet ona, ne cilj, kamor je človek medtem šel.
  addEventListener("pageshow", function nazaj(ev) {
    removeEventListener("pageshow", nazaj);
    if (!ev.persisted) return;
    g.classList.remove("is-on");
    prej.classList.add("is-on");
  });
});

// ---------- tipkovnica prekrije orodno vrstico ----------
//
// Aplikacija (`adjustResize`) in Firefox ob tipkovnici skrčita okno, in
// vrstica, pripeta na dno, je skočila nad tipkovnico -- čez polje, v katerega
// človek tipka (David, 22. 10. 2026: „naj ostane spodaj in jo tipkovnica
// prekrije“). Chrome okna ne skrči in vrstica že ostane pod tipkovnico.
// Tipkovnica = okno vsaj za `TIPKOVNICA_PX` nižje od najvišjega pri isti
// širini, medtem ko ima fokus polje za vnos; sama višina ne zadošča (vrstica
// naslova v brskalniku se skrije in pokaže), sam fokus pa ne (tipka nazaj
// tipkovnico zapre, fokus ostane).
const TIPKOVNICA_PX = 150;
(() => {
  const najvisje = new Map();          // širina okna -> največja višina
  const piše = () => {
    const el = document.activeElement;
    return !!el && (el.isContentEditable || el.tagName === "TEXTAREA"
      || (el.tagName === "INPUT" && !/^(button|checkbox|radio|range|submit|reset|color|file|image)$/
        .test(el.type)));
  };
  const preveri = () => {
    const w = innerWidth, h = innerHeight;
    najvisje.set(w, Math.max(najvisje.get(w) || 0, h));
    document.documentElement.classList.toggle("tipkovnica",
      piše() && najvisje.get(w) - h >= TIPKOVNICA_PX);
  };
  addEventListener("resize", preveri);
  document.addEventListener("focusin", preveri);
  // Ob izgubi fokusa je novi aktivni element znan šele po dogodku.
  document.addEventListener("focusout", () => setTimeout(preveri, 0));
  preveri();
})();

// ---------- meni Več: nazaj in poteg navzdol ----------
//
// List odpre in zapre `popover` sam (`_vec.html`), brez skripta. Tu je samo,
// kar ima spodnji list v Androidu in ga splet sam ne zna: tipka nazaj ga
// zapre, namesto da bi zapustila stran, in poteg navzdol tudi. Zato ob
// odprtju vnos v zgodovino; zaprt list ga vzame nazaj, da tipka nazaj potem
// ne bi „ničesar naredila“. Povezava v listu gre najprej nazaj čez ta vnos in
// šele nato na cilj -- sicer bi v zgodovini ostal mrtev korak.
//
// List je na koncu `<body>`, za skripti (`_vec.html` pove, zakaj), zato šele
// po razčlenitvi strani.
function pripniMeniVec() {
  const vec = document.getElementById("vec");
  if (!vec || typeof vec.showPopover !== "function") return;
  let vZgodovini = false;
  let cilj = null;
  vec.addEventListener("toggle", (e) => {
    if (e.newState === "open") {
      history.pushState({ vec: true }, "");
      vZgodovini = true;
    } else if (vZgodovini) {
      vZgodovini = false;
      history.back();
    }
  });
  addEventListener("popstate", () => {
    if (vZgodovini) {
      vZgodovini = false;
      vec.hidePopover();
    }
    if (cilj) {
      const c = cilj;
      cilj = null;
      location.href = c;
    }
  });
  vec.addEventListener("click", (e) => {
    const a = e.target.closest("a[href]");
    if (!a || !vZgodovini || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    e.preventDefault();
    cilj = a.href;
    vec.hidePopover();
  });

  // Poteg navzdol: list sledi prstu, nad 80 px se zapre. Samo, kadar je
  // vsebina lista na vrhu -- sicer poteg pomeni drsenje po njej.
  let y0 = null;
  let dy = 0;
  vec.addEventListener("touchstart", (e) => {
    if (vec.scrollTop > 0) return;
    y0 = e.touches[0].clientY;
    dy = 0;
  }, { passive: true });
  vec.addEventListener("touchmove", (e) => {
    if (y0 === null) return;
    dy = Math.max(0, e.touches[0].clientY - y0);
    vec.style.transition = "none";
    vec.style.transform = `translateY(${dy}px)`;
  }, { passive: true });
  vec.addEventListener("touchend", () => {
    if (y0 === null) return;
    y0 = null;
    // Prehod nazaj pred zapiranjem: list gre dol od tam, kjer ga je pustil
    // prst, ne skoči najprej nazaj gor.
    vec.style.transition = "";
    if (dy > 80) vec.hidePopover();
    vec.style.transform = "";
  });
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", pripniMeniVec);
else pripniMeniVec();

// ---------- zadnje iskanje ----------
//
// Puščica ‹ v oknu vožnje in pilula Vlaki/Avtobusi v orodni vrstici sta
// vodili na goli `/app/bus` -- iskalnik je bil prazen, brez polj in izida
// (prijava 18. 10. 2026: „ko daš nazaj, se vnos resetira“; 3 od 3 iskanj).
// Zdaj vodita na zadnje iskanje tega omrežja v tem zavihku. sessionStorage,
// ne localStorage: po zaprtju zavihka ali aplikacije se polja iz spomina ne
// izpolnijo (`connections.restore()`), deljena povezava pa ga ne prinese.
const ZADNJE_ISKANJE = "kajros:zadnje-iskanje:";
const ISKALNIK = { zeleznica: "/app/train", avtobus: "/app/bus" };

function zapomniIskanje(omrezje) {
  try {
    sessionStorage.setItem(ZADNJE_ISKANJE + omrezje, location.pathname + location.search);
  } catch (e) { /* zasebno okno: pilula ostane gola pot */ }
}

function zadnjeIskanje(omrezje) {
  try {
    return sessionStorage.getItem(ZADNJE_ISKANJE + omrezje);
  } catch (e) {
    return null;
  }
}

// Pilula vodi na zadnje iskanje z vsake strani razen z iskalnika samega:
// tam je dotik lastne pilule „začni znova“, kot pri zavihkih aplikacije.
function pripniZadnjeIskanje() {
  for (const [omrezje, pot] of Object.entries(ISKALNIK)) {
    if (location.pathname === pot) continue;
    const zadnje = zadnjeIskanje(omrezje);
    if (!zadnje) continue;
    document.querySelectorAll(`.orodna a[href="${pot}"]`).forEach((a) => a.setAttribute("href", zadnje));
  }
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", pripniZadnjeIskanje);
else pripniZadnjeIskanje();


/** Telo odgovora kot JSON -- a samo uspešnega. Napaka FastAPI je tudi JSON
 *  (`{detail}`) in bi jo stran sicer brala kot podatke. */
function jsonOk(r) {
  if (!r.ok) throw new Error(`${r.url}: HTTP ${r.status}`);
  return r.json();
}

// ---------- pika o zivosti ----------
// Pika je doslej kazala, ali je ODGOVOR prisel, ne ali so PODATKI sveži.
// Če zajem odmre, API pa tece naprej, bi ostala zelena in bi trdila nekaj,
// česar ne ve. Zdaj bere `last_feed_at` iz stanja zajema.

// Feed se osvezuje na 30 s. Trikratnik je dovolj, da ena izpuscena zahteva
// ne prizge opozorila, in dovolj malo, da odmrl zajem opazimo v minuti.
const FEED_STALE_S = 90;

async function refreshFeedDot() {
  const dot = document.getElementById("feed-dot");
  if (!dot) return;
  try {
    const h = await fetch("/api/svezina").then(jsonOk);
    const age = h.last_feed_ts ? Date.now() / 1000 - h.last_feed_ts : Infinity;
    const stale = age > FEED_STALE_S;
    dot.classList.toggle("stale", stale);
    dot.title = h.last_feed_at
      ? `zadnji zajem ob ${hhmm(h.last_feed_at)}${stale ? ` — pred ${Math.round(age / 60)} min` : ""}`
      : "zajema še ni bilo";
  } catch (err) {
    dot.classList.add("stale");
    dot.title = "strežnik ni dosegljiv";
  }
}

// ---------- osvezevanje, ki ve za vidnost strani ----------
//
// Aplikacija je predvsem telefonska. Navaden `setInterval` tam tece naprej,
// ko je stran v ozadju -- to je poraba baterije in prenosa za sliko, ki je
// nihce ne gleda. Ob vrnitvi pa clovek gleda vrednost, staro do pol minute,
// in prav takrat je najbolj pomembna: stoji na peronu.
//
// Zato: v ozadju ne osvezujemo, ob vrnitvi osvezimo TAKOJ. Enako ob vrnitvi
// omrezja -- telefon, ki je bil v predoru, ima sicer prazno stran, dokler ne
// potece naslednji interval.
function pollWhileVisible(fn, ms) {
  let timer = null;
  let zadnji = 0;
  let ustavljen = false;
  // Ritem je lahko funkcija: okno vožnje med vožnjo vpraša pogosteje kot pred njo.
  const korak = () => (typeof ms === "function" ? ms() : ms);

  // Naslednji korak si naroči samo, če ga medtem ni naročil kdo drug
  // (`zdaj`, `wake`) -- sicer tečeta dve verigi in vsaka zahteva gre dvakrat.
  const tick = async () => {
    timer = null;
    zadnji = Date.now();
    try {
      await fn();
    } catch (err) {
      /* posamezna zahteva sme spodleteti; ritem se ne sme ustaviti */
    }
    if (!document.hidden && !ustavljen && !timer) timer = setTimeout(tick, korak());
  };

  const wake = () => {
    if (document.hidden) {
      clearTimeout(timer);
      timer = null;
      return;
    }
    if (timer) return;                    // ze tece
    // Ce je od zadnjega osvezevanja minilo manj kot pol intervala, ne
    // podvajamo zahteve -- kratek preklop med aplikacijama ni razlog zanjo.
    const potekel = Date.now() - zadnji >= korak() / 2;
    timer = setTimeout(tick, potekel ? 0 : korak() - (Date.now() - zadnji));
  };

  // Stran, vrnjena iz predpomnilnika brskalnika (tipka nazaj): časovnik je
  // med zamrznitvijo stal, zato bi stari podatki čakali še ostanek koraka.
  const vrnjena = (ev) => {
    if (!ev.persisted) return;
    clearTimeout(timer);
    timer = null;
    wake();
  };

  document.addEventListener("visibilitychange", wake);
  window.addEventListener("online", wake);
  window.addEventListener("pageshow", vrnjena);
  wake();
  return {
    // Za zmeraj: brez odjave bi ga prva vrnitev na zavihek zbudila znova,
    // korak, ki ravno čaka na odgovor, pa bi si naročil naslednjega.
    stop: () => {
      ustavljen = true;
      clearTimeout(timer);
      timer = null;
      document.removeEventListener("visibilitychange", wake);
      window.removeEventListener("online", wake);
      window.removeEventListener("pageshow", vrnjena);
    },
    // Takoj, ne ob naslednjem koraku -- to je gumb "osvezi" pod prstom. Za
    // razliko od `tick` napake NE pogoltne: gumb mora povedati, ali je
    // odgovor prisel.
    zdaj: async () => {
      clearTimeout(timer);
      timer = null;
      zadnji = Date.now();
      try {
        return await fn();
      } finally {
        if (!document.hidden && !timer && !ustavljen) timer = setTimeout(tick, korak());
      }
    },
  };
}

// ---------- puscici za dan ----------
//
// Premakneta datum za dan naprej ali nazaj. Prazno polje pomeni danes -- tako
// ga berejo tudi vse poizvedbe -- zato je prvi pritisk "jutri" oziroma
// "vceraj", naslednji pa naprej po dnevih.
//
// Racunamo ob POLDNEVU in ne ob polnoci: dan ob prehodu na zimski cas traja
// 25 ur, pristevanje 86 400 000 ms bi ostalo v istem dnevu, ura 12 pa nikoli
// ne pade cez rob dneva.
//
// Tu in ne na strani, ker imata polje z dnevom zdaj dve strani (iskalnik zvez
// in pot); dve razlicici istega racuna bi se ob prvem prehodu casa razsli.
function pripniDnevnePuscice(koren) {
  for (const btn of (koren || document).querySelectorAll("[data-day-for]")) {
    const input = document.getElementById(btn.dataset.dayFor);
    if (!input) continue;
    const korak = Number(btn.dataset.step) || 1;
    btn.addEventListener("click", () => {
      const d = new Date(`${input.value || todayIso()}T12:00:00`);
      d.setDate(d.getDate() + korak);
      input.value = d.toLocaleDateString("sv-SE");
      // Stran mora izvedeti, da se je dan spremenil -- brez tega je poizvedba
      // po dotiku na puscico se vedno za prejsnji dan.
      input.dispatchEvent(new Event("change", { bubbles: true }));
    });
  }
}

// ---------- vlak ali nadomestni prevoz ----------
// Nadomestni prevoz je v istem iskalniku kot vlaki, ker je na tej relaciji
// edina dejanska povezava. Prav zato mora biti oznaka nedvoumna: potnik, ki
// caka na peronu avtobus, ga zamudi.

function isBus(mode) {
  return mode === "bus";
}

// Prevoznik po GTFS agency_id. Pri avtobusu je oznaka linije brez prevoznika
// dvoumna: "25" je lahko LPP ali kaj drugega.
const AGENCY = {
  "1161": "SŽ",
  "1118": "LPP",
  "1123": "Arriva",
  "1119": "Nomago",
  "1121": "AP MS",
  // Mestni LPP je drug vir z besednim `agency_id` (glej `config.LPP_*`).
  "lpp": "LPP",
  // Mestni Maribor in Kranj, vsak svoj vir (`marprom.py`, `kranj.py`).
  "marprom": "Marprom",
  "kranj": "Kranj",
};

// ---------- ime vožnje, kot ga vidi potnik ----------
//
// Pri medkrajevnih prevoznikih IJPP je `train_no` šifra linije iz registra
// (A6346, N0239, M2015): ista za obe smeri (A6135 vozi Škofja Loka ↔
// Železniki) in na avtobusu je ni. Iskalnik je pisal „A6346 Arriva A6346“.
// Potnik pozna prevoznika in kam avtobus pelje. LPP je drugače: „LPP 25“
// piše na avtobusu in ostane. Nadomestni prevoz in vlaki ostanejo pri
// številki. Iskanje po šifri na zemljevidu dela naprej (`vehText`).
const SIFRA_LINIJE = new Set(["1123", "1119", "1121"]);

function jeMedkrajevni(row) {
  return row.network === "avtobus" && SIFRA_LINIJE.has(String(row.agency));
}

/** Kam pelje: zadnji kos „A - B“. Krožna („Novo mesto - Obrh - Novo mesto“,
 *  564 od 17 846 medkrajevnih voženj) pove vmesno postajo in „in nazaj“ --
 *  „→ Novo mesto“ iz Novega mesta bi bil nesmisel. */
function ciljVoznje(headsign) {
  const d = (headsign || "").split(" - ").map((x) => x.trim()).filter(Boolean);
  if (!d.length) return "";
  if (d.length > 2 && d[0] === d[d.length - 1]) return `${d[Math.floor(d.length / 2)]} in nazaj`;
  return d[d.length - 1];
}

// ---------- imena, kot jih piše LPP ----------
//
// LPP smeri in končna postajališča piše z velikimi črkami in s tehničnimi
// priponami: „BEŽIGRAD (ŽELEZNA) - ZOO - C. STOŽICE P+R_obvoz“. Na zaslonu
// „Bežigrad (Železna) – Zoo – C. Stožice P+R (obvoz)“. Besede, ki niso v celoti
// velike, ostanejo, kot so („NS RUDNIK (po Vilharjevi)“), zato se imena drugih
// prevoznikov ne spremenijo. Isto pravilo kot `pristanek.lepo_ime`.
const KRATICE = new Set(["P+R", "BTC", "SŽ", "ZD", "NS", "AP", "OŠ", "UKC", "LPP", "IMP", "KPL", "AMZS", "TC"]);
// Občna imena v imenih sosesk z malo: Zelena jama, Dolgi most, Tuji grm.
const MALA_IMENA = new Set(["naselje", "jama", "most", "grm", "log", "dvor", "kolodvor",
  "cesta", "ulica", "trg", "vas", "breg", "hrib", "pri", "na", "v", "ob", "pod", "nad", "za", "in"]);

function lepoIme(niz) {
  if (!niz) return "";
  const t = String(niz).replace(/_obvoz$/i, " (obvoz)").replace(/\s*-\s+|\s+-\s*/g, " – ");
  return t.split(" – ").map((del) => {
    let prva = true;
    return del.replace(/[\p{L}+]+/gu, (w) => {
      const zacetek = prva;
      prva = false;
      if (w !== w.toUpperCase() || w.length < 2 || KRATICE.has(w)) return w;
      const male = w.toLocaleLowerCase("sl");
      if (!zacetek && MALA_IMENA.has(male)) return male;
      return male.charAt(0).toLocaleUpperCase("sl") + male.slice(1);
    });
  }).join(" – ");
}

/** „LPP 25“, „Arriva“ / „Arriva → Bohinj Ukanc“ (`sCiljem`, kjer smeri ne
 *  pove nič drugega), „IC 503“. */
function imeVoznje(row, sCiljem = false) {
  if (row.network !== "avtobus") return row.train_no;
  const kdo = AGENCY[row.agency];
  if (jeMedkrajevni(row)) {
    const cilj = sCiljem ? ciljVoznje(row.headsign) : "";
    return `${kdo || "avtobus"}${cilj ? ` → ${cilj}` : ""}`;
  }
  return kdo ? `${kdo} ${row.train_no}` : row.train_no;
}

// Ena barva za vse avtobusne linije, in ne barva iz vira.
//
// Prvi razlog je bil, da so vsi LPP-jevi `route_color` ista zelena
// prevoznika. **To za mestni LPP ne velja** -- ta ima 27 razlicnih barv in
// to so prave barve linij, ki jih Ljubljancani poznajo. Razlog je zdaj drug
// in izmerjen: na nasi podlagi (#0f1115) jih **14 od 27 ne dosega 4,5 : 1**,
// stiri so pod 3 : 1, `#1f1d1d` pa pri 1,13 : 1 -- torej nevidna. Nasa
// zelena je pri 7,70 : 1.
//
// Barvati polovico linij po viru in polovico enotno bi bilo slabse od
// enotnega: barva bi takrat pomenila dvoje. Ime linije nosi oznaka sama;
// barva samo pove, cigav avtobus je, zato je v zetonu vedno tudi prevoznik.
const LINE_INK = "#4db97f";

// ---------- barve zemljevidov ----------
// Veliki zemljevid in okno vožnje si jih delita.

// Barva na zemljevidu pove, CIGAV avtobus je. Izbrane so tako, da se locijo
// tudi pri barvni slepoti: najslabsi par je pri deutan/protan ΔE 9,6 (prag 3)
// in celo pri tritanopiji 4,8 -- preverjeno s scripts/preveri_paleto.py, ne na
// oko. Proti lestvici zamud zelena in oranzna pri deutanu trcita (ΔE 1,2), a
// to ni tezava: vozila locuje OBLIKA (avtobus je puscica, vlak krog), barva pa
// nikoli ne nosi pomena sama -- oznaka poleg nosi ime prevoznika.
const BUS_INK = "#4db97f";                    // privzeto, kadar prevoznik ni znan
const AGENCY_INK = {
  "1118": "#4db97f",   // LPP
  "1123": "#6fb8ff",   // Arriva
  "1119": "#9d7ae0",   // Nomago
  "1121": "#c9a227",   // AP Murska Sobota
  // Marprom in Kranj v zeleni mestnega LPP: vsi so mestni in se na
  // zemljevidu ne srečajo (Maribor, Kranj, Ljubljana), zato barva ne more
  // pomeniti napačnega prevoznika -- peta barva bi pri barvni slepoti
  // trčila z obstoječimi. Loči ju ime na kartici in vrstica v legendi.
  "marprom": "#4db97f",
  "kranj": "#4db97f",
};

// Pot izbranega vozila in vozila v oknu vožnje je v barvi kajrosa (oranžna
// znaka), ne v barvi vozila: v barvi prevoznika se je med enako obarvanimi
// trasami LPP izgubila (4. 10. 2026). Ista oranžna kot vlak -- izbrana pot
// vlaka je bila tako ali tako oranžna; od prevoznikov se loči tudi pri barvni
// slepoti (`preveri_paleto.py`).
const IZBRANA_INK = "#f0934f";

// Prevoženi del poti izbranega vozila.
const ZA_INK = "#8b95a4";
// Zadnja IZMERJENA lega vozila, ki je narisano na oceni (okno vožnje,
// izbrani avtobus na velikem zemljevidu): rdeča pika s svetlim obročem.
// Rdeča ni iz nobene lestvice (ne zamud, ne razmer), tu ne more pomeniti
// drugega.
const MERITEV_INK = "#ff4d5e";
// Vozilo na OCENI lege: prosojno telo (nariše ga zemljevid sam) s črtkanim
// svetlim obrisom čez temnega, ki ga loči od podlage. Meritev od ocene loči
// oblika, ne barva -- vozilo ostane v barvi prevoznika (4. 10. 2026).
const obrisOcene = (rect) => `<rect ${rect} fill="none" stroke="#0f1115" stroke-width="2.4"/>
      <rect ${rect} fill="none" stroke="#f4f6fa" stroke-width="1.2" stroke-dasharray="2.4 1.6"/>`;
// Vlak na zemljevidu: oznaka, model in pot.
const TRAIN_INK = "#f0934f";
// Zapora tira na zemljevidu: ista rumena kot opozorila o ovirah na straneh
// (`oznake.md`). Od lestvice zamud in prevoznikov ločena tudi pri barvni
// slepoti (`preveri_paleto.py`, najslabše proti 1–5 min ΔE 5,2), a jo loči
// predvsem oblika: črtkana črta, ne vozilo in ne žeton.
const OVIRA_INK = "#f2d36b";

function lineBadgeHtml(row) {
  if (!isBus(row.mode)) return "";
  // Na zeleznicni strani avtobus pomeni NADOMESTNI PREVOZ -- torej "namesto
  // vlaka, ki tu ne vozi". To ni linija mestnega prevoza in ne sme biti
  // videti kot ona; potnik mora prebrati, zakaj tu stoji avtobus.
  if (row.network === "zeleznica") {
    return `<span class="mode-bus" title="namesto vlaka, ki na tej relaciji ne vozi">
      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3.5" y="3.5" width="17" height="15" rx="2.6"></rect>
        <path d="M3.5 10.5h17M3.5 5.8 1.4 6.8M20.5 5.8l2.1 1M6.5 18.6v2.4M17.5 18.6v2.4"></path>
        <circle cx="8" cy="14.6" r="0.9" fill="currentColor" stroke="none"></circle>
        <circle cx="16" cy="14.6" r="0.9" fill="currentColor" stroke="none"></circle>
      </svg>
      <span class="mode-bus-beseda">nadomestni prevoz</span>
    </span>`;
  }
  return `<span class="line-badge" style="color:${LINE_INK};border-color:${LINE_INK}55">
    ${escapeHtml(imeVoznje(row))}</span>`;
}

function modeBadgeHtml(mode) {
  if (!isBus(mode)) return "";
  return `<span class="mode-bus" title="nadomestni prevoz namesto vlaka">
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor"
         stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3.5" y="3.5" width="17" height="15" rx="2.6"></rect>
      <path d="M3.5 10.5h17M3.5 5.8 1.4 6.8M20.5 5.8l2.1 1M6.5 18.6v2.4M17.5 18.6v2.4"></path>
      <circle cx="8" cy="14.6" r="0.9" fill="currentColor" stroke="none"></circle>
      <circle cx="16" cy="14.6" r="0.9" fill="currentColor" stroke="none"></circle>
    </svg>
    avtobus
  </span>`;
}

// ---------- vozovnica ----------

const SZ_TRGOVINA = "https://eshop.sz.si/";

/** Povezava na spletno trgovino SŽ. Relacije ni mogoce podati -- glej
 *  `train.vozovnicaHtml()` za razlog. */
function ticketLinkHtml() {
  return `<a class="ticket-link" href="${SZ_TRGOVINA}" target="_blank"
      rel="noopener noreferrer"
      title="Spletna trgovina SŽ. Relacije ni mogoče podati v naslovu, zato jo tam vpišeš sam.">
      Kupi vozovnico na <strong>eshop.sz.si</strong>
      <span class="ticket-note">relacijo vpišeš tam</span>
    </a>`;
}

// ---------- vreme ----------

const WEATHER_INK = "#6f8fa8";

function weatherIconHtml(w, size, tint) {
  if (!w || w.temp_c == null) return "";
  const px = size || 14;
  // Oblika pove, KAJ je (dez, sneg, megla), barva pa KAKO hudo je.
  const c = tint || (w.severity_label ? severityColor(w.severity_label) : null);
  const a = `width="${px}" height="${px}" viewBox="0 0 24 24" fill="none" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"`;
  if ((w.snowfall_cm || 0) > 0) {
    return `<svg ${a} stroke="${c || '#a8d8ff'}"><path d="M12 16a4.5 4.5 0 0 0 0-9 6 6 0 0 0-11 1.8A3.6 3.6 0 0 0 4.6 16"></path><path d="M8 20h.01M12 21h.01M16 20h.01"></path></svg>`;
  }
  if ((w.precip_mm || 0) >= 0.1) {
    return `<svg ${a} stroke="${c || WEATHER_INK}"><path d="M12 16a4.5 4.5 0 0 0 0-9 6 6 0 0 0-11 1.8A3.6 3.6 0 0 0 4.6 16"></path><path d="M8 19l-1 2.5M12 19l-1 2.5M16 19l-1 2.5"></path></svg>`;
  }
  if (w.code === 45 || w.code === 48) {
    return `<svg ${a} stroke="${c || '#79828f'}"><path d="M3 9h18M4 13h16M6 17h12"></path></svg>`;
  }
  if (w.code != null && w.code <= 1) {
    return `<svg ${a} stroke="${c || '#c8a06a'}"><circle cx="12" cy="12" r="4.2"></circle><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M18.4 5.6L17 7M7 17l-1.4 1.4"></path></svg>`;
  }
  return `<svg ${a} stroke="${c || '#5b6472'}"><path d="M12 18a5 5 0 0 0 0-10 6.5 6.5 0 0 0-12 2 4 4 0 0 0 4 4h8"></path></svg>`;
}

function num(v, digits) {
  if (v == null) return "—";
  return v.toFixed(digits == null ? 1 : digits).replace(".", ",");
}

// Semafor, ne lestvica enega odtenka: stopnje se morajo lociti na prvi pogled.
// Tople barve tu ne trkajo z lestvico zamud, ker je v pogledu Vreme zamuda
// narisana nevtralno. Meje stopenj so iste kot oznake v `weather.severity()`.
//
// Preverjeno z validatorjem palete na temni podlagi: najslabsi par med sabo je
// #d1495b <-> #6b7480 (protan ΔE 6,1), kar je dovoljeno le ob dodatnem zapisu --
// zato stopnja povsod nosi tudi stevilko in ime.
const SEVERITY_STYLE = {
  "mirne": "#6b7480",
  "blage": "#5aa87d",
  "zahtevne": "#d9b33c",
  "hude": "#d1495b",
};
const SEVERITY_ORDER = ["mirne", "blage", "zahtevne", "hude"];

function severityColor(scoreOrLabel) {
  if (typeof scoreOrLabel === "string") return SEVERITY_STYLE[scoreOrLabel] || "#3d434f";
  const s = scoreOrLabel;
  if (s == null) return "#3d434f";
  if (s <= 0) return SEVERITY_STYLE["mirne"];
  if (s <= 3) return SEVERITY_STYLE["blage"];
  if (s <= 6) return SEVERITY_STYLE["zahtevne"];
  return SEVERITY_STYLE["hude"];
}

function severityTitle(w) {
  if (!w || w.severity == null) return "";
  const parts = (w.severity_parts || []).map((x) => `${x.what} +${x.points}`).join(", ");
  return `razmere ${w.severity}/10 · ${w.severity_label}` +
    (parts ? ` (${parts})` : "") + ` — ${weatherSummary(w)}`;
}

function weatherSummary(w) {
  if (!w || w.temp_c == null) return "";
  const bits = [];
  if ((w.snowfall_cm || 0) > 0) bits.push(`sneg ${num(w.snowfall_cm)} cm`);
  else if ((w.precip_mm || 0) >= 0.1) bits.push(`dež ${num(w.precip_mm)} mm`);
  else bits.push("brez padavin");
  bits.push(`${num(w.temp_c)} °C`);
  if (w.wind_gust_kmh != null) bits.push(`sunki ${num(w.wind_gust_kmh, 0)} km/h`);
  return bits.join(" · ");
}

// ---------- ena voznja: skupno branje /api/train/{st}/run ----------

// Sekunde, ker jih risanje grafov in izracuni rabijo kot stevilo. Pravilo
// `COALESCE(delay_dep, delay_arr)` -- in NE obratno, ker je `departure.delay`
// izpolnjen pri vseh prevoznikih, `arrival.delay` pa ne -- je na strezniku
// (`stats.opis_zamude()`); tu ga ne ponavljamo, le beremo. Rezerva velja za
// odgovore, ki objekta se nimajo.
function stopDelay(s) {
  if (s && s.zamuda) return s.zamuda.s;
  return s.delay_dep != null ? s.delay_dep : s.delay_arr;
}

/** Streznikova odlocitev za postanek, kadar je na voljo. */
function stopZamuda(s) {
  return (s && s.zamuda) || null;
}

function stopActualIso(s) {
  return s.actual_dep || s.actual_arr;
}

function lastMeasured(run) {
  // Mejo med meritvijo in napovedjo pove STREZNIK (`last_measured_seq`), ne
  // ta koda. Prej je bilo isto pravilo napisano dvakrat -- v `stats.py` in tu
  // -- in dve razlicici istega pravila se prej ali slej razideta. Razlika bi
  // bila tiha: prikaz bi feedovo napoved za se nedosezen postanek pokazal kot
  // izmerjeno zamudo, in po zapisu v CLAUDE.md je bila ta napaka na zaslonu
  // ze dvakrat.
  //
  // `run` je cel odgovor `/api/train/{no}/run`, ne samo postanki.
  const seq = run && run.last_measured_seq;
  if (seq == null) return null;
  return (run.stops || []).find((s) => s.stop_seq === seq) || null;
}

function stopWeatherHtml(w, isForecast) {
  if (!w || w.severity == null) return "";
  // Potnika ne zanima 0,4 mm/h -- zanima ga, ali so razmere hude. Surove
  // stevilke ostanejo v naslovu in v oknu ob grafu.
  //
  // Pri postajah naprej po progi je to NAPOVED (Open-Meteo forecast), ne
  // izmerjeno stanje. Razlika je vidna -- crtkan rob in beseda v naslovu --
  // ker bi enak zeton pomenil, da o prihodnosti vemo enako kot o preteklosti.
  const color = severityColor(w.severity_label);
  const loud = w.severity_label === "zahtevne" || w.severity_label === "hude";
  const title = (isForecast ? "napoved · " : "") + severityTitle(w);
  // Zeton nikoli ne pokaze gole stopnje. "0" potniku ne pove nic -- to je bilo
  // ze popravljeno -- a "1" prav tako ne: stevilka brez enote in brez lestvice
  // je uganka, razlaga pa je v `title`, ki ga na telefonu ni mogoce doseci.
  //
  // Zato: do vkljucno "blagih" (<= 3) pise TEMPERATURA, ki nekaj pove sama po
  // sebi, od "zahtevnih" naprej pa BESEDA, ki pove, kaj je narobe. Barva ostane
  // ista lestvica; beseda je samo tam, kjer je kaj za povedati, in takih
  // postankov je malo, zato sirina ni tezava.
  const tiho = w.severity <= 3;
  const znak = tiho
    ? (w.temp_c != null ? `${Math.round(w.temp_c)}°` : "")
    : w.severity_label;
  // Mirno vreme za nazaj ne pove nicesar: na ze prevozenih postajah ga ni.
  if (tiho && !isForecast) return "";
  const quiet = tiho ? " is-quiet" : "";
  return `<span class="stop-weather${loud ? " is-loud" : ""}${isForecast ? " is-forecast" : ""}${quiet}"` +
    ` title="${escapeHtml(title)}"` +
    (loud ? ` style="background:${color}1f;border-color:${color}66"` : "") + `>` +
    weatherIconHtml(w, 13) +
    `<span class="stop-sev"${tiho ? "" : ` style="color:${color}"`}>${znak}</span></span>`;
}

// Postanek, na katerem se zamuda spremeni. Vlak ne odide vedno takrat, ko
// pride: na Most na Soci ima LP 4219 v voznem redu devet minut postanka
// (krizanje na enotirni progi), zato prispe +10 in odide +3. Ena sama
// stevilka na vrstico to skrije in v grafu nastane skok, ki je videti
// nemogoc -- prav to vprasanje je sprozilo tale izpis.
//
// Redko, a ne zanemarljivo: 406 postankov v voznem redu ima nad dve minuti
// zadrzevanja, in v devetih dneh zajema se prihodna in odhodna zamuda
// razlikujeta pri 1 307 postankih (362 od tega za pet minut ali vec).
// Beseda za vozilo. Postanek opisuje stran, ki ve, ali gleda vlak, avtobus
// ali nadomestni prevoz -- "vlak je stal 4 min" pod mestno linijo 25 ni le
// netocno, ampak zveni kot napaka programa.
let VEHICLE_NOUN = "vlak";

function setVehicleNoun(noun) {
  VEHICLE_NOUN = noun || "vlak";
}

function dwellSplit(s) {
  const a = s.delay_arr;
  const b = s.delay_dep;
  // Na IZHODISCU prihoda ni: vozilo tam zacne. Feed vseeno posilja vrednost
  // in ta je smet -- LPP 25 je 30. 8. na Medvodah naselju porocal prihod
  // -267 s ob odhodu -2 s, na drugi voznji istega dne celo -1771 s. Iz tega
  // je prikaz sestavil zgodbo "stal 4 min namesto 0". Zgodbe o dogodku, ki
  // se ni zgodil, ni.
  if (s.stop_seq === 1) return null;
  if (a == null || b == null || Math.abs(a - b) < 60) return null;
  if (s.arr_s == null || s.dep_s == null) return null;
  const sched = (s.dep_s - s.arr_s) / 60;          // voznoredno zadrzevanje
  return {
    arr: a, dep: b,
    sched: Math.round(sched),
    real: Math.round(sched + (b - a) / 60),
    gained: Math.round((a - b) / 60),
  };
}

// Dolg postanek pred potnikom: povej, na cem ocena stoji. Model racuna, da bo
// vlak postanek skrajsal na dve minuti -- to je skrita predpostavka, ki zna
// biti mocno mimo (RG 1604 v Ljubljani: vozni red 21 min, model 2, resnica 7).
// Zato pokazemo, koliko ta vlak tam RES stoji, kadar zamuja.
const DWELL_SHOW_S = 300;

function dwellNoteHtml(d) {
  if (d.gained > 0) {
    return `vozni red tu čaka ${d.sched} min, ${VEHICLE_NOUN} je stal ${Math.max(d.real, 0)}`
      + ` — nadoknadil ${d.gained} min`;
  }
  return `${VEHICLE_NOUN} je stal ${d.real} min namesto ${d.sched}`
    + ` — izgubil ${-d.gained} min`;
}

// Tir s table SŽ (`peroni.py`). Kadar ga ni, ni nič -- vir je tretja oseba in
// sme izginiti. Sprememba čez dan se napiše z besedo, ne le z barvo: prav
// potnik, ki svoj vlak pozna, gre sicer na stari peron.
function tirHtml(tir, prej) {
  if (!tir) return "";
  return `<span class="tir${prej ? " is-changed" : ""}">tir ${escapeHtml(tir)}${
    prej ? ` · prej ${escapeHtml(prej)}` : ""}</span>`;
}

// "Odpeljal" je pri vlaku skoraj vedno sklep iz ure, ne opažanje. Kadar vlak
// čaka na prejšnji postaji in feed zamude ne osveži, ura laže: vrstica je šla
// med odpeljane, vlak pa je šele prihajal. Do `nepotrjen_do` zato ostane med
// živimi in pove, da je odhod sklep. Mejo postavi strežnik
// (`stats.nepotrjen_do`); tu je le ura, ker teče tudi med osvežitvama.
function nepotrjen(pricakovanoMs, doIso, nowMs) {
  return !!(nowMs && doIso && pricakovanoMs < nowMs
            && nowMs <= new Date(doIso).getTime());
}

function nepotrjenHtml(iso, prihod) {
  return `<span class="nepotrjen">po zadnjem podatku bi ${prihod ? "prispel" : "odpeljal"}
      ob ${hhmm(iso)}, potrditve ni</span>`;
}

/** Današnja tabla po PRIČAKOVANI uri: odpeljane, nepotrjene in prihajajoče.
 *
 * Po voznem redu je 25. 9. 2026 na Bavarskem dvoru na vrhu stal LPP 14 z
 * 12:46 in +49 min, pod njim deset že odpeljanih -- odpeljanost je bila po
 * pričakovani uri, vrstni red pa ne. Nepotrjen odhod ni odpeljan: ostane
 * viden, pred naslednjim. Isto pravilo za odhodno tablo (`connections.js`)
 * in oblaček postaje na zemljevidu (`dashboard.js`).
 */
function razvrstiTablo(list, nowMs) {
  const kdaj = (r) => new Date(r.expected || r.sched).getTime();
  const po = [...list].sort((a, b) => kdaj(a) - kdaj(b)
    || new Date(a.sched).getTime() - new Date(b.sched).getTime());
  const jeMorda = (r) => nepotrjen(kdaj(r), r.nepotrjen_do, nowMs);
  return {
    gone: po.filter((r) => kdaj(r) < nowMs && !jeMorda(r)),
    morda: po.filter((r) => kdaj(r) < nowMs && jeMorda(r)),
    ahead: po.filter((r) => kdaj(r) >= nowMs),
  };
}

// ---------- odhodi shranjene poti ----------
//
// Shranjena pot (`kajros:fav`) z naslednjim odhodom stoji na dveh mestih: na
// domači strani (Moje poti) in v iskalniku (Shranjeno). Ena koda, sicer bi
// isti odhod na eni strani veljal za odpeljanega, na drugi ne.

const SMER_KLJUC = "kajros:smer";

/** Stran ceste, ki jo je potnik na tabli postajališča izbral (iskalnik). */
function smerIzSpomina(postaja) {
  try {
    return (JSON.parse(localStorage.getItem(SMER_KLJUC) || "{}") || {})[postaja] || null;
  } catch (e) {
    return null;
  }
}

/** Odhodi poti v enotni obliki, ne glede na to, ali je zveza A-B ali tabla.
 *  Brez `datum` velja danes. `vir` je vrstica strežnika (oznaka vožnje, vrsta
 *  številke), `smer` ime izbrane strani ceste. */
async function odhodiPoti(f, datum) {
  const network = f.net === "avtobus" ? "avtobus" : "zeleznica";
  if (f.kind === "board") {
    const q = new URLSearchParams({ station: f.station, kind: f.dir || "odhodi", network });
    if (datum) q.set("date", datum);
    const smer = smerIzSpomina(f.station);
    if (smer) q.set("smer", smer);
    const d = await fetch(`/api/departures?${q}`).then(jsonOk);
    const izbrana = (d.smeri || []).find((s) => s.kljuc === d.smer);
    const imeSmeri = izbrana ? (izbrana.naslednje || []).join(" · ") : null;
    // Po obvozu LPP tu ne ustavi (`ne_ustavi`), odpovedana ne vozi: ni odhod.
    return (d.board || []).filter((r) => !r.ne_ustavi && !r.odpovedano).map((r) => ({
      ura: r.sched, pricakovano: r.expected, zamuda: r.zamuda, nepotrjen_do: r.nepotrjen_do,
      kam: lepoIme(r.towards), nadomestni: isBus(r.mode) && r.network === "zeleznica",
      obicajno: r.typical, smer: imeSmeri, vir: r,
    }));
  }
  const q = new URLSearchParams({ from: f.from, to: f.to, network, with_transfers: "false" });
  if (datum) q.set("date", datum);
  const d = await fetch(`/api/connections?${q}`).then(jsonOk);
  return (d.connections || []).filter((c) => !c.ne_ustavi).map((c) => ({
    ura: c.sched_dep, pricakovano: c.expected_dep, zamuda: c.zamuda, nepotrjen_do: c.nepotrjen_do,
    kam: null, nadomestni: isBus(c.mode) && c.network === "zeleznica",
    obicajno: c.typical_arr || c.typical_dep, smer: null, vir: c,
  }));
}

// Mimo je sele, ko je minil PRICAKOVANI odhod; nepotrjen odhod (vlak, o
// katerem feed molci) ostane do `nepotrjen_do`, isto kot na tabli. Vrstni red
// po pričakovani uri, kot tabla (`razvrstiTablo`): API vrne voznoredno, in
// LPP 14 z +49 min ni naslednji, ko LPP 13 pelje čez dve minuti.
function naslednjiOdhodi(odhodi, zdaj, koliko) {
  const kdaj = (o) => new Date(o.pricakovano || o.ura).getTime();
  return odhodi.filter((o) => kdaj(o) >= zdaj
    || (o.nepotrjen_do && zdaj <= new Date(o.nepotrjen_do).getTime()))
    .sort((a, b) => kdaj(a) - kdaj(b)).slice(0, koliko);
}

/** Kje lahko vlak naprej po progi izgubi čas (`zapore.py`).
 *
 * Ni napoved: ob zapori tira je mediana izgube 0 -- kateri vlak bo čakal na
 * križanje, se ne ve. Zato beseda in izmerjeno tveganje, številka zamude
 * ostane. Imena postaj v imenovalniku, ker se jih ne da splošno sklanjati.
 */
function opozoriloBesedilo(o, kratko) {
  if (o.vrsta === "zapora") {
    const t = o.tveganje;
    const min = (s) => Math.round(s / 60);
    const razpon = t && t.izgubilo
      ? (min(t.najmanj_s) === min(t.najvec_s) ? `${min(t.najvec_s)}` : `${min(t.najmanj_s)}–${min(t.najvec_s)}`)
      : "";
    return `Zapora enega tira ${o.odsek} do ${o.do_ure}: vlak lahko tam čaka na križanje.`
      + (!t ? ""
        : t.izgubilo
          ? ` Ob prejšnjih dneh te zapore je tam ${t.izgubilo} od ${t.prehodov} vlakov izgubilo ${razpon} min.`
          : ` Ob prejšnjih dneh te zapore tam ni nobeden od ${t.prehodov} vlakov izgubil 5 min ali več.`);
  }
  const m = Math.round(o.izguba_s / 60);
  return kratko
    ? `pred njim ${o.vlak} izgubil ${m} min (${o.odsek})`
    : `Vlak pred njim, ${o.vlak}, je ob ${hhmm(o.ob)} na odseku ${o.odsek} izgubil ${m} min.`;
}

// V vrstici table je prostora za eno vrstico: zapore skupaj, vlak pred njim
// posebej.
function opozorilaVrsticeHtml(list) {
  if (!list || !list.length) return "";
  const zap = list.filter((o) => o.vrsta === "zapora").map((o) => o.odsek);
  const ostala = list.filter((o) => o.vrsta !== "zapora");
  return [
    ...(zap.length ? [`zapora tira ${zap.join(", ")}`] : []),
    ...ostala.map((o) => opozoriloBesedilo(o, true)),
  ].map((t) => `<span class="opozorilo">${escapeHtml(t)}</span>`).join(" · ");
}

// Ure zapore tira v slovenskem zapisu s piko, kot na tabli („do 13.30“).
function oknaZapore(okna) {
  return okna.map((o) => (o.ves_dan ? "ves dan" : `${o.od}–${o.do}`)).join(", ");
}

// „danes 8.00–16.00 · velja zdaj“ / „· začne ob 8.00“ / „· končano“. Ena
// beseda za isto zaporo na zemljevidu (oblaček črte in postaje) in na strani
// ovir; okna in stanje izračuna strežnik ob vsaki strežbi (`zapore.stanje`).
function kdajZapore(p) {
  const danes = p.dan === todayIso();
  const stanje = p.stanje === "zdaj" ? "velja zdaj"
    : p.stanje === "koncano" ? "končano"
    : danes ? `začne ob ${p.zacne}` : "";
  return [`${danes ? "danes" : dayLabel(p.dan)} ${oknaZapore(p.okna)}`, stanje]
    .filter(Boolean).join(" · ");
}

// ---------- kje ustavi nadomestni avtobus ----------
// Vozni red postavi nadomestni avtobus na tir, kjer ga ni: v Ljubljani stoji
// na peronih 37-39 avtobusne postaje, v Jevnici na postajaliscu Senozeti ob
// krozniscu. Kje res stoji, pove samo SZ na svoji strani (`nadomestni.py`,
// 274 postaj); brez tega potnik caka na napacnem peronu.
function nadomestniPostanekHtml(p) {
  if (!p) return "";
  return `<span class="nadomestni-postanek" title="kje ustavi nadomestni avtobus (po SŽ)">
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"
         stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z"></path>
      <circle cx="12" cy="10" r="2.3"></circle>
    </svg>
    <span><span class="za-bralnik">nadomestni avtobus ustavlja: </span>${escapeHtml(p.opis)}</span></span>`;
}

// Nadomestni avtobusi ob isti uri so lahko hitri in počasni (Logatec 4.35:
// 42 in 75 min do Ljubljane). Številka vožnje tega ne pove, trajanje pove.
function potekNadomestnegaHtml(r) {
  if (r.voznja_s == null || r.postankov == null) return "";
  const min = Math.round(r.voznja_s / 60);
  const vmes = r.postankov === 0 ? "brez postankov" : `${r.postankov} ${sklon(r.postankov, "postanek")}`;
  return `<span class="potek-nadomestnega">vožnja ${min} min · ${vmes}</span>`;
}

// Postanek, katerega ura si nasprotuje z vecino ostalih na tej vozjni.
// Odlocitev je strezenikova (`stats.oznaci_neskladne`) in pride v
// `zamuda.vrsta`: pravilo gleda celo vozjno, zato ga odjemalec ne more
// ponoviti po vrsticah -- in dve razlicici istega pravila sta tiha napaka.
function jeNeskladen(s) {
  return !!(s.zamuda && s.zamuda.vrsta === "neskladno");
}

// Ziva napoved mestnega LPP (`data.lpp.si`). To NI nasa ocena in ni meritev:
// je prevoznikova napoved, izracunana iz lege vozila -- ista vrsta stevilke,
// kot jo nosi derp.si, le da se osvezi na 10-30 s namesto na ~90 s.
// Odlocitev je strezenikova (`api._lpp_zivo`), tu jo samo preberemo.
function zivaNapoved(s) {
  return s && s.zamuda && s.zamuda.vrsta === "živo" ? s.zamuda : null;
}

// Napoved naprej je odvisna od izhodišča in zamude, od zgodovine (ves dan ista)
// in od prevoznikove napovedi, ki pride na 30 s (derp.si). Okno vožnje vpraša
// na 10 s, zato isti odgovor vzame znova, dokler ni starejši od 30 s in se
// izhodišče ne premakne: pol manj zahtev za isto sliko.
const NAPOVED_VELJA_MS = 30000;
let zadnjaNapoved = null;

async function fetchRunAndForecast(trainNo, date, tripId) {
  const enc = encodeURIComponent(trainNo);
  // `trip` je nujen pri avtobusih: stevilka linije ni stevilka voznje.
  const p = new URLSearchParams();
  if (date) p.set("date", date);
  if (tripId) p.set("trip", tripId);
  const q = p.toString() ? `?${p}` : "";
  const res = await fetch(`/api/train/${enc}/run${q}`);
  // Stevilka, ki je ne poznamo, in dan brez meritev nista isto: prvo je
  // zastarela ali polomljena povezava, drugo pravi podatek o pravi vozjni.
  // Prikaz je oboje pisal kot "na ta dan ni podatkov" in s tem trdil, da
  // vozjna obstaja.
  if (!res.ok) {
    const e = new Error(`run ${res.status}`);
    e.status = res.status;
    throw e;
  }
  const run = await res.json();

  const cur = lastMeasured(run);
  // Dokler vlak se ni odpeljal, meritve ni, feed pa ima za prvo postajo ze
  // napoved. Oceno za naprej takrat zgradimo na njej -- ozaljsana je z oznako
  // "ocena", da nihce ne bere napovedi na napovedi kot izmerjeno.
  let base = cur;
  if (!base) {
    for (const s of run.stops) if (stopDelay(s) != null) { base = s; break; }
  }

  // Kadar je porocilo potnikov na vozilu verodostojno, je njihova zamuda
  // svezejsa od feedove in napoved tece od njihove lege (`deljenje.stanje`,
  // odlocitev 25. 9. 2026, za enega potnika 11. 10.). Sicer ostane feedova.
  const pp = run.potniki;
  const izPotnikov = pp && pp.verodostojno && pp.stop_seq != null && pp.zamuda_s != null;
  const odSeq = izPotnikov ? pp.stop_seq : base && base.stop_seq;
  // Kadar SŽ pove višjo zamudo od zadnje prevožene postaje (vlak stoji med
  // postajama), napoved teče od nje -- ista številka kot v glavi okna.
  const odZamude = izPotnikov ? pp.zamuda_s
    : cur && run.trenutna ? run.trenutna.zamuda.s : base && stopDelay(base);

  let forecast = [];
  const lastSeq = run.stops.length ? run.stops[run.stops.length - 1].stop_seq : 0;
  if (odSeq != null && odZamude != null && odSeq < lastSeq) {
    // Prikazani dan izpustimo iz ucenja -- isto kot pri zgodovini.
    const url = `/api/train/${enc}/predict?stop_seq=${odSeq}&delay_s=${odZamude}`
      + `&exclude_date=${encodeURIComponent(run.service_date)}`
      // Brez `trip` se model pri avtobusu uci iz vseh voznj te linije,
      // obeh smeri skupaj. Pri vlaku je isti trip in sprememba nicesar.
      + (run.trip_id ? `&trip=${encodeURIComponent(run.trip_id)}` : "");
    try {
      if (zadnjaNapoved && zadnjaNapoved.url === url
          && Date.now() - zadnjaNapoved.ob < NAPOVED_VELJA_MS) {
        forecast = zadnjaNapoved.forecast;
      } else {
        const p = await fetch(url).then((r) => (r.ok ? r.json() : null));
        forecast = (p && p.forecast) || [];
        if (p) zadnjaNapoved = { url, ob: Date.now(), forecast };
      }
    } catch (err) {
      console.warn("napovedi ni bilo mogoče naložiti", err);
    }
  }
  return { run, forecast, current: cur };
}

// ---------- ime postaje na dotik ----------

// Postajalisce brez imena je pika, trajen oblacek pa cez pol Ljubljane
// pobrise zemljevid pod sabo. Zato: ime se pokaze ob dotiku in cez pet sekund
// samo odide. Brez gumba za zapiranje -- ta bi bil na telefonu manjsi od
// prsta in bi zahteval drugi, natancnejsi dotik od tistega, ki je ime odprl.
const NAME_MS = 5000;

// ---------- starost lege, ki tece sama ----------

// "lega stara 59 s" je stala pri miru, dokler ni prisel naslednji poll, in
// nato skocila nazaj na 38. Starost je edina stevilka na strani, ki se
// spreminja tudi takrat, ko se ne zgodi nic, zato jo mora steti brskalnik:
// strezniska vrednost je izhodisce, mi pa pristevamo cas od trenutka, ko je
// odgovor prispel. Ura odjemalca v racun NE gre -- merimo razliko dveh
// lastnih meritev, zato zamik ure ne skodi.
function ageText(baseS, sinceMs) {
  const s = Math.max(0, Math.round(baseS + (Date.now() - sinceMs) / 1000));
  return s < 100 ? `${s} s` : `${Math.round(s / 60)} min`;
}

// Vrne HTML, ki se osvezuje sam. Iscemo po razredu in ne po registru, ker se
// kartica na zemljevidu gradi iz niza HTML in nanjo ni kam obesiti sklica.
function ageHtml(ageS) {
  const t = Date.now();
  // Naslov namesto opombe: stevilka je videti kot nas zaostanek, pa ni --
  // izmerjeno dodamo mediano 0 s, ostalo je starost, s katero lego dobimo.
  return `<span class="age-live" data-base="${ageS}" data-since="${t}"`
    + ` title="čas od meritve GPS v vozilu; feed nam jo pošlje že okoli pol minute staro">`
    + `${ageText(ageS, t)}</span>`;
}

setInterval(() => {
  // V ozadju ne risemo: sekundnik za sliko, ki je nihce ne gleda, je poraba
  // baterije. Ob vrnitvi je prva vrednost pravilna, ker se racuna, ne steje.
  if (document.visibilityState === "hidden") return;
  for (const el of document.querySelectorAll(".age-live")) {
    el.textContent = ageText(+el.dataset.base, +el.dataset.since);
  }
}, 1000);

// ---------- geometrija vzdolž črte ----------
//
// Okno vožnje po trasi, vodenje po pešpoti, vlak s potnikom na velikem
// zemljevidu. Ena kopija za vse -- prej sta imeli strani vsaka svojo, z
// drugačno konstanto za meter.

function metriNaStopinjo(lat) {
  return { lat: 111320, lon: 111320 * Math.cos(lat * Math.PI / 180) };
}

function razdaljaM(a, b) {
  const k = metriNaStopinjo((a[0] + b[0]) / 2);
  const dy = (a[0] - b[0]) * k.lat;
  const dx = (a[1] - b[1]) * k.lon;
  return Math.sqrt(dx * dx + dy * dy);
}

// Kumulativne dolzine vzdolz trase, izracunane enkrat ob nalaganju.
function kumulative(pts) {
  const out = [0];
  for (let i = 1; i < pts.length; i++) out.push(out[i - 1] + razdaljaM(pts[i - 1], pts[i]));
  return out;
}

// Najblizja tocka na trasi: kako dalec vzdolz nje lezi in kako dalec od nje
// je iskana tocka. Odmik je merilo zaupanja -- velik pomeni, da tocka tej
// trasi ne pripada in racun po poti nima smisla.
function projekcijaNaTraso(pts, cums, lat, lon) {
  const k = metriNaStopinjo(lat);
  let najOdmik = Infinity, vzdolz = 0;
  for (let i = 0; i < pts.length - 1; i++) {
    const [ay, ax] = pts[i], [by, bx] = pts[i + 1];
    const vx = (bx - ax) * k.lon, vy = (by - ay) * k.lat;
    const wx = (lon - ax) * k.lon, wy = (lat - ay) * k.lat;
    const len2 = vx * vx + vy * vy;
    const t = len2 === 0 ? 0 : Math.max(0, Math.min(1, (wx * vx + wy * vy) / len2));
    const odmik = razdaljaM([lat, lon], [ay + t * (by - ay), ax + t * (bx - ax)]);
    if (odmik < najOdmik) {
      najOdmik = odmik;
      vzdolz = cums[i] + t * (cums[i + 1] - cums[i]);
    }
  }
  return { vzdolz, odmik: najOdmik };
}

// Tocka, ki lezi `cilj` metrov vzdolz trase.
function tockaNaTrasi(pts, cums, dolzina) {
  const cilj = Math.max(0, Math.min(dolzina, cums[cums.length - 1]));
  for (let i = 0; i < cums.length - 1; i++) {
    if (cilj >= cums[i] && cilj <= cums[i + 1]) {
      const d = cums[i + 1] - cums[i];
      const f = d === 0 ? 0 : (cilj - cums[i]) / d;
      return [pts[i][0] + f * (pts[i + 1][0] - pts[i][0]),
              pts[i][1] + f * (pts[i + 1][1] - pts[i][1])];
    }
  }
  return pts[pts.length - 1];
}

// ---------- ocena lege med dvema meritvama ----------
//
// Lega je ob strezbi ze ~30 s stara (izmerjeno), kar je pri 30 km/h cetrt
// kilometra. Piko zato premaknemo naprej po trasi za `hitrost x starost`.
//
// Izmerjeno na 79 primerih (razmik 15-60 s), napaka proti dejanski naslednji
// legi: pika pri miru mediana 63 m in 63 % v 100 m, premik po smeri 36 m in
// 72 %, **premik po trasi 30 m in 80 %**. Trasa je boljsa od smeri, ker cesta
// zavija, vozilo pa ne pove, da bo zavilo.
//
// Ocena, ne meritev -- zato se ne premika, kadar vozilo stoji ali kadar ni na
// tej trasi, in podnapis pove, da je ocenjena.
const OCENA_MAX_ODMIK_M = 120;
// Vozilo, ki je od svoje trase dlje od tega, ni na njej: pelje na začetek
// vožnje ali pa lega ni njegova (feed vozilo prišteje drugi vožnji). Na
// velikem zemljevidu je takrat vsa pot še pred njim, v oknu vožnje razdalje
// po poti ne računamo. 22. 10. 2026 od 109 mestnih LPP 105 v 50 m, 2 dlje od
// 2 km (oba na končni, prišteta naslednji ali prejšnji vožnji).
const NA_TRASI_M = 300;
// Od toliko metrov med oceno in meritvijo besedilo pove „ocenjeno iz lege
// pred N s“ namesto „lega stara N s“; bliže je to ista točka na zaslonu.
const OCENA_VIDNA_M = 40;

// Smer trase pri `s` metrih, v stopinjah od severa: od tocke `pol` metrov
// zadaj do tocke `pol` metrov spredaj. Brez dolzine vrne null.
function smerTrase(pts, cums, s, pol) {
  const a = tockaNaTrasi(pts, cums, s - pol);
  const b = tockaNaTrasi(pts, cums, s + pol);
  const k = metriNaStopinjo((a[0] + b[0]) / 2);
  const dx = (b[1] - a[1]) * k.lon, dy = (b[0] - a[0]) * k.lat;
  if (Math.hypot(dx, dy) < 0.5) return null;
  return (Math.atan2(dx, dy) * 180 / Math.PI + 360) % 360;
}

// Med dvema legama avtobus ne vozi ves cas -- na postajaliscih stoji, in
// `hitrost x starost` ga zato odnese predalec. Izmerjeno na 139 parih
// zaporednih leg (150 vozil, 1. 9. zvecer), napaka proti dejanski naslednji
// legi -- rez na 35 parih, kjer na poti RES lezi postajalisce:
//
//   razlicica                mediana   povprecje   v 100 m
//   premik po trasi (prej)    109 m      136 m      46 %
//   ustavi pri prvi postaji    59 m      110 m      69 %
//   **postanek 15 s**          53 m       99 m      71 %
//
// Cez vse pare 54 -> 45 m mediane in 69 -> 76 % v 100 m. Med 10 in 20 s je
// rezultat raven (povprecje 84,4 / 83,0 / 83,6 m), zato 15 s ni izbrano
// natancno, ampak je sredina izmerjene ravnine -- isto kot `MIN_DWELL_S`.
const POSTANEK_S = 15;
// Vlak stoji dlje. Izmerjeno 1. 10. 2026 na točkah treh deljenj na vlakih
// (LPV 2010, RG 318, LPV 2221; 202--273 parov), napaka proti legi, ki jo je
// potnik poslal pozneje, mediana: po 60 s 79 m s 15 s postanka in 61 m s 45,
// po 120 s 354 in 192 m. Po 30 s ni razlike (31 m).
const POSTANEK_VLAK_S = 45;
// Postajalisce, na katerem vozilo ze stoji, ne steje se enkrat.
const ZA_SABO_M = 15;

// Kje je vozilo priblizno ZDAJ. Brez trase ali med mirovanjem vrne izmerjeno
// lego -- ocena, ki ne ve, kam naprej, ni boljsa od meritve. `vzdolz` je
// ocena na trasi v metrih, pri izmerjeni legi null. `tr` = trasa vožnje
// ({trasa, cums, postaje, vlak}): okno vožnje ima eno, veliki zemljevid
// po eno za vsak vlak s potnikom.
function ocenaNaTrasi(tr, v, starostS) {
  const izmerjena = { kje: [v.lat, v.lon], vzdolz: null };
  if (!tr.trasa || !v.speed_ms || v.speed_ms < 1) return izmerjena;
  const { vzdolz, odmik } = projekcijaNaTraso(tr.trasa, tr.cums, v.lat, v.lon);
  if (odmik > OCENA_MAX_ODMIK_M) return izmerjena;

  // Vozi s trenutno hitrostjo, na vsakem vmesnem postajaliscu porabi postanek.
  let ostanek = starostS, kje = vzdolz;
  for (const p of (tr.postaje || [])) {
    if (p <= vzdolz + ZA_SABO_M) continue;
    const doPostaje = (p - kje) / v.speed_ms;
    if (doPostaje >= ostanek) break;
    ostanek -= doPostaje + (tr.vlak ? POSTANEK_VLAK_S : POSTANEK_S);
    kje = p;
    if (ostanek <= 0) break;
  }
  const cilj = kje + Math.max(0, ostanek) * v.speed_ms;
  return { kje: tockaNaTrasi(tr.trasa, tr.cums, cilj), vzdolz: cilj };
}

// Kje vzdolz trase lezijo postanki -- ocena lege se na njih ustavi. Postaja,
// ki je od trase vec kot 60 m, tej trasi ne pripada (napacen kos, obvoz) in
// bi oceno ustavila na napacnem mestu. `postaje` = [{lat, lon}, ...].
function postankiNaTrasi(trasa, cums, postaje) {
  return postaje
    .filter((s) => s.lat != null && s.lon != null)
    .map((s) => projekcijaNaTraso(trasa, cums, s.lat, s.lon))
    .filter((r) => r.odmik <= 60)
    .map((r) => r.vzdolz)
    .sort((a, b) => a - b);
}

// Kam je obrnjeno vozilo na oceni: po TRASI, ne po smeri iz feeda. Ta je
// stara toliko kot lega (~30 s), in avtobus, ki ga je ocena odpeljala cez
// ovinek, je z njo stal pocez na cesto. Izmerjeno na 324 parih zaporednih
// leg LPP (31 vozil, 25. 9. 2026 ob 19h, razmik 10-90 s), napaka proti
// smeri, ki jo feed pove ob naslednji legi (ta se s traso na dejanski
// legi ujema: 95 % v 15°, torej je dobro merilo):
//
//   smer na oceni            mediana   v 20°   nad 45°
//   iz feeda (prej)            5,6°     74 %    12,3 %
//   **po trasi, tetiva ±35 m** 2,4°     87 %     8,0 %
//
// Kar ostane nad 45° (26 parov), je napaka LEGE, ne smeri: v 16 je ocena od
// resnice vzdolz trase vec kot 100 m, v ostalih je projekcija padla na
// nasprotni krak trase ali pa vozilo po svoji trasi pelje nazaj (12D, 69).
//
// `pol` je pol dolzine NARISANEGA vozila v metrih (ve ga zemljevid, ki ga
// rise: ikona ali povecan model), zato oba konca lezita na trasi tudi v
// ovinku. Natancnosti dolzina tetive skoraj ne spremeni -- od 0 do +-150 m
// je v 20° med 84 in 87 % -- zato je izbrana po sliki. `lega` je izid
// `ocenaNaTrasi`, `tr` njena trasa.
function smerNaOceni(tr, v, lega, pol) {
  const iz = v.bearing || 0;
  if (lega.vzdolz == null) return iz;
  return smerTrase(tr.trasa, tr.cums, lega.vzdolz, pol) ?? iz;
}

// ---------- osvezevanje leg ----------

// Lege beremo **v koraku s strezbo**, ne na slepo. Odgovor nosi glavo
// `X-Osvezi-Cez`: cez koliko sekund bo streznik feed prebral znova. Slep
// ritem je polovico svojega casa cakal na podatek, ki je v bazi ze lezal --
// izmerjeno je bilo to 10 od 45 sekund starosti pike na zaslonu.
//
// Vrne `{ stop, zdaj }`. Klic tece, dokler je stran vidna: telefon v
// zepu ne sme spraševati, ker odgovora nihce ne gleda -- to je hkrati
// najcenejsi prihranek na strezniku, kar jih je.
function pollVehicles(url, onData, prva = null) {
  let timer = null;
  let ustavljen = false;

  // Ena zahteva. Napake NE pogoltne -- ritem jo sme prezreti, gumb "osvezi"
  // pa mora povedati, da odgovora ni bilo. Vrne, cez koliko sekund vprasati
  // znova. `prva` = odgovor, ki ga je stran zacela cakati ze prej (zemljevid).
  async function poizvedi() {
    const r = await (prva || fetch(url));
    prva = null;
    const h = parseInt(r.headers.get("X-Osvezi-Cez"), 10);
    const podatki = await r.json();
    onData(podatki);
    return Number.isFinite(h) ? h : 10;
  }

  async function tick() {
    if (ustavljen) return;
    if (document.visibilityState === "hidden") {
      timer = setTimeout(tick, 5000);   // skrita stran samo caka, ne sprasuje
      return;
    }
    let cez = 10;
    try {
      cez = await poizvedi();
    } catch (err) {
      cez = 30;                         // ob napaki ne tolcemo naprej
      console.warn("leg vozil ni bilo mogoče naložiti", err);
    }
    if (ustavljen) return;
    // Zamik 0-2 s: sto brskalnikov ne sme udariti v isti trenutek. Spodnja
    // meja 3 s velja, kadar streznik zaostaja in glava pade na 1.
    timer = setTimeout(tick, Math.max(3, cez + 1) * 1000 + Math.random() * 2000);
  }

  // Ob vrnitvi na stran vprasaj takoj: prva stvar, ki jo clovek pogleda, je
  // kje je vozilo, in cakati nanjo cel cikel je slabse kot ena zahteva vec.
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && !ustavljen) {
      clearTimeout(timer);
      tick();
    }
  });

  tick();
  return {
    stop: () => { ustavljen = true; clearTimeout(timer); },
    // Ista oblika kot pri `pollWhileVisible`: obe zanki zna gumb "osvezi"
    // pognati z istim klicem in mu ni treba vedeti, katera je katera.
    zdaj: async () => {
      clearTimeout(timer);
      try {
        return await poizvedi();
      } finally {
        if (!ustavljen) timer = setTimeout(tick, 10000);
      }
    },
  };
}

// ---------- gumb "osvezi" ----------
//
// Zemljevid se osvezuje sam, a tega se ne vidi. Ko vozilo dve minuti stoji,
// clovek ne loci mirnega podatka od obticale strani -- in edino, kar mu takrat
// preostane, je ponovno nalozi vso stran. Gumb ne pohitri nicesar: pove, da se
// je pravkar vprasalo, in ob kateri uri je bil odgovor.
//
// Zato tudi ne izgine po uspehu. Ura zadnje osvezitve je odgovor na "ali to se
// tece", in ta je koristen, ko se nic ne premika.

const OSVEZI_URA = new Intl.DateTimeFormat("sl-SI", {
  timeZone: "Europe/Ljubljana", hour: "2-digit", minute: "2-digit",
  second: "2-digit", hour12: false,
});

/**
 * `opravila` so funkcije, ki vrnejo obljubo; gumb je zaseden, dokler niso vse
 * koncane. Prej je "osvezeno ob" pisalo pred podatkom, kar je natanko tista
 * laz, ki jo naj bi gumb odpravil.
 *
 * `opomba` je neobvezen izpis na zaslon (zemljevid ima za to svojo vrstico);
 * naslov gumba dobi isto besedilo tudi brez nje.
 */
function pripniOsvezi(el, opravila, opomba) {
  if (!el) return;
  let tece = false;

  const povej = (t, napaka) => {
    el.title = t;
    el.setAttribute("aria-label", t);
    el.classList.toggle("is-fail", !!napaka);
    if (opomba) opomba(t);
  };

  el.addEventListener("click", async (ev) => {
    ev.preventDefault();
    if (tece) return;                     // dvojni dotik ni dve zahtevi
    tece = true;
    el.classList.add("is-busy");
    try {
      await Promise.all(opravila.map((f) => f()));
      povej(`osveženo ob ${OSVEZI_URA.format(new Date())}`, false);
    } catch (err) {
      povej("osvežitev ni uspela — ni zveze s strežnikom", true);
    } finally {
      tece = false;
      el.classList.remove("is-busy");
    }
  });
}

// ---------- trase voznj ----------
//
// Rabita ju obe strani poti: seznam predlogov in podrobni prikaz.
// Ravna crta med postajama ni proga in bi trdila pot, ki je ni.

// Trase voznj, predpomnjene po vožnji. Statika, ki se med uvozi ne spremeni.
const TRASE = new Map();

/** Najbližja točka na črti: odsek `i`, delež `u` na njem in točka sama. */
function naCrti(tocke, ll) {
  const kx = Math.cos(ll[0] * Math.PI / 180);
  let naj = { i: 0, u: 0, d: Infinity, tocka: tocke[0] };
  for (let i = 0; i < tocke.length - 1; i += 1) {
    const ax = (tocke[i][1] - ll[1]) * kx, ay = tocke[i][0] - ll[0];
    const bx = (tocke[i + 1][1] - ll[1]) * kx, by = tocke[i + 1][0] - ll[0];
    const dx = bx - ax, dy = by - ay;
    const l2 = dx * dx + dy * dy;
    const u = l2 ? Math.max(0, Math.min(1, -(ax * dx + ay * dy) / l2)) : 0;
    const d = (ax + u * dx) ** 2 + (ay + u * dy) ** 2;
    if (d < naj.d) {
      naj = { i, u, d, tocka: [tocke[i][0] + u * (tocke[i + 1][0] - tocke[i][0]),
                               tocke[i][1] + u * (tocke[i + 1][1] - tocke[i][1])] };
    }
  }
  return naj;
}

/**
 * Trasa vožnje med vstopom in izstopom, od postajališča do postajališča.
 *
 * Rez je na **projekciji** postajališča na traso, ne na najbližjem ogljišču:
 * ogljišča so ponekod sto metrov narazen in črta se je začela sredi ulice,
 * obroč postajališča pa je stal ob njej (Drama → Križanke, 23. 9. 2026). In
 * na obeh koncih je kratek priključek do postajališča samega -- LPP ima
 * postajališče na pločniku, traso pa na sredini ceste, in brez njega je bila
 * pot na zemljevidu pretrgana.
 */
async function trasa(n) {
  if (!n.trip_id || !n.od_ll || !n.do_ll) return null;
  if (!TRASE.has(n.trip_id)) {
    const obljuba = (async () => {
      const r = await fetch(`/api/trip/${encodeURIComponent(n.trip_id)}/shape`);
      if (!r.ok) return null;
      const deli = (await r.json()).points || [];
      // Trasa je lahko večdelna; za izrez vzamemo najdaljši del.
      return deli.reduce((a, b) => (b.length > a.length ? b : a), []);
    })();
    TRASE.set(n.trip_id, obljuba);
    // Brez omrežja zavrnjena ne sme ostati: stran, odprta v predoru, bi bila
    // do konca brez trase (pot, na kateri si, iz nje ve, ali se pelješ).
    obljuba.catch(() => TRASE.delete(n.trip_id));
  }
  const del = await TRASE.get(n.trip_id);
  if (!del || del.length < 2) return null;
  const a = naCrti(del, n.od_ll), b = naCrti(del, n.do_ll);
  const pa = a.i + a.u, pb = b.i + b.u;
  if (pa === pb) return null;
  const vmes = pa < pb ? del.slice(a.i + 1, b.i + 1) : del.slice(b.i + 1, a.i + 1).reverse();
  // Projekcija, ki je le nekaj deset metrov od postajališča, bi s
  // priključkom narisala kljukico (tja in nazaj ob obroču); takrat gre črta
  // s postajališča kar na naslednje ogljišče.
  const blizu = (x) => Math.sqrt(x.d) * 111320 < 35;
  return [n.od_ll, ...(blizu(a) ? [] : [a.tocka]), ...vmes,
          ...(blizu(b) ? [] : [b.tocka]), n.do_ll];
}

// ---------- iskanje po kazalu postaj ----------
//
// Postaje se ne spreminjajo vsak dan, iskanje pa je bilo za `network=vse`
// izmerjeno 1,35 s na razvojnem racunalniku -- torej okoli pet na arwenu, in
// to na VSAK pritisk tipke. Zato se kazalo naloze enkrat in isce se tu.
//
// Razvrscanje mora biti isto kot na strezniku (`journey.search_stations`):
// tocno ime, nato zacetek imena ali besede, nato kjerkoli, znotraj razreda pa
// odloca promet -- kazalo je po njem ze urejeno. Dve razlicici tega bi za isto
// crko dali dva razlicna seznama.

function zacetekBesede(folded, needle) {
  let i = folded.indexOf(needle);
  while (i >= 0) {
    if (i === 0 || folded[i - 1] === " ") return true;
    i = folded.indexOf(needle, i + 1);
  }
  return false;
}

/** `kazalo` so predmeti z zlozenim imenom v `.f`; vrne najvec `limit` zadetkov. */
function iskalnikKazala(kazalo, q, limit = 8) {
  const needle = fold(String(q).trim());
  if (!needle) return [];
  const tocno = [];
  const zacetek = [];
  const kjerkoli = [];
  for (const s of kazalo) {
    if (s.f === needle) tocno.push(s);
    else if (s.f.startsWith(needle)) zacetek.push(s);
    else if (s.f.indexOf(needle) < 0) continue;
    // Zacetek besede je za potnika enako dober zadetek kot zacetek imena --
    // izmerjeno, glej `_razred()` v journey.py. Zato v isto vedro.
    else if (zacetekBesede(s.f, needle)) zacetek.push(s);
    else kjerkoli.push(s);
    if (tocno.length + zacetek.length >= limit && kjerkoli.length >= limit) break;
  }
  return [...tocno, ...zacetek, ...kjerkoli].slice(0, limit);
}

// Kazalo postaj obeh omrezij se nalozi ENKRAT in isce se v brskalniku.
// Poizvedba na streznik je bila za obe omrezji izmerjeno 1,35 s na razvojnem
// racunalniku -- okoli pet na arwenu, in to na vsak pritisk tipke. Postaje se
// ne spreminjajo vsak dan. Rabita ga najhitrejsa pot in veliki zemljevid, zato
// je tu: dve kopiji predpomnilnika bi se razsli pri prvi spremembi oblike.
const KAZALO_KLJUC = "kajros:kazalo-vse";
const KAZALO_VELJA_MS = 12 * 3600 * 1000;
let kazaloObljuba = null;

/** Vrne obljubo seznama `{n, t, lat, lon, f}` ali `null`, ce ga ni bilo mogoce dobiti. */
function naloziKazalo() {
  if (kazaloObljuba) return kazaloObljuba;
  kazaloObljuba = (async () => {
    try {
      const shranjeno = JSON.parse(localStorage.getItem(KAZALO_KLJUC) || "null");
      if (shranjeno && Date.now() - shranjeno.ts < KAZALO_VELJA_MS) {
        return shranjeno.v.map((s) => ({ ...s, f: fold(s.n) }));
      }
    } catch (e) { /* pokvarjen zapis: preberemo znova */ }
    try {
      const r = await fetch("/api/stations/index?network=vse&koordinate=1");
      if (!r.ok) return null;
      const v = await r.json();
      try {
        localStorage.setItem(KAZALO_KLJUC, JSON.stringify({ ts: Date.now(), v }));
      } catch (e) { /* poln ali zavrnjen localStorage ni napaka */ }
      return v.map((s) => ({ ...s, f: fold(s.n) }));
    } catch (e) {
      return null;
    }
  })();
  return kazaloObljuba;
}

// ---------- širina črte v metrih ----------
//
// Trasa je bila 3 px pri vsakem približku. Pri Leafletovem z19 je piksel
// 0,21 m, torej trasa 0,6 m na cesti, široki 7 m -- od blizu tanka črta ob
// cesti namesto ceste (prijava 2. 10. 2026). Od MapLibrovega z16 naprej je
// zato širina v metrih in raste s približkom kot cesta pod njo, od daleč pa
// ostane v pikslih, da se vidi. 1 m = 65 536 / 54 307 px pri z16 na 46° š.;
// po Sloveniji (45,4°–46,9°) se to spremeni za 2 %.
const PX_NA_M_Z16 = 65536 / 54307;

// `dalec`: pari [MapLibrov zoom, px] do z15 vključno.
function sirinaM(metrov, dalec = [[10, 2], [15, 3]]) {
  const [zz, pz] = dalec[dalec.length - 1];
  return ["interpolate", ["exponential", 2], ["zoom"],
    ...dalec.flat(),
    ...(zz < 16 ? [16, Math.max(pz, metrov * PX_NA_M_Z16)] : []),
    22, metrov * PX_NA_M_Z16 * 64];
}

// ---------- moja lega ----------
//
// Prikaz lastne lege je na vseh zemljevidih ista stvar, zato živi tu: stanje
// dovoljenja (`stanjeLege`), sledenje (`LEGA`), lega na dotik gumba
// (`poisciMe`) in vklop s kartice na domači strani (`vklopiLego`).
//
// **Okna za dovoljenje stran ne odpre sama.** Dovoljenje, ki ga nihče ni
// prosil, je vsiljivo in ga brskalnik ob zavrnitvi pogosto zapomni za vedno.
// Vprašanje sproži samo dotik: gumb lege ali „Vklopi“ na domači strani.
//
// **Kadar pa je dovoljenje že dano, lega teče sama** (David, 22. 10. 2026).
// Do takrat jo je bilo treba na vsakem zemljevidu prižgati z gumbom, tudi
// kadar je bila dovoljena -- „če je prižgana, še ne pomeni, da je
// aktivirana“. Sama se prižge samo pika; pogled ostane, kjer je, k tebi ga
// premakne gumb.
//
// Modra `#2f7fff` ne nastopa v nobeni lestvici -- ne med zamudami (oranzna),
// ne v semaforju razmer, in je dovolj nasicena, da se loci od blede `#a8d8ff`,
// ki pomeni oceno. Modro proti oranzni loci tudi vsaka oblika barvne slepote.
const ME_COLOR = "#2f7fff";

// Deset sekund in `enableHighAccuracy` je bilo premalo. Na telefonu brez
// Googlovih storitev (razgooglana Volla) ni omreznega dolocanja lege -- ostane
// gol GPS, ki iz hladnega stanja rabi desetine sekund, v stavbi pa pogosto
// nikoli. `getCurrentPosition` je zato izteklo in povedalo samo "ni bilo
// mogoce dobiti", kar je za iskanje vzroka neuporabno.
//
// Zato troje: `watchPosition` (prvi fix vzame takoj, ko pride, in ne caka na
// iztek), daljsi rok, in **razlicna sporocila za razlicne vzroke** -- zavrnjeno
// dovoljenje, GPS brez signala in iztek niso ista tezava.
const LEGA_ROK_MS = 25000;
//: Ko je lega natancnejsa od tega, je ni treba izboljsevati. GPS v mestu se
//: ustali okoli 10-30 m; prva groba lega iz baznih postaj zna biti 1-2 km.
const LEGA_DOVOLJ_M = 100;

function locateMe(opts) {
  const { rok = LEGA_ROK_MS, dovolj = LEGA_DOVOLJ_M, napredek } = opts || {};
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      return reject(new Error("Brskalnik ne pozna lokacije."));
    }
    // Brskalniki dovolijo lokacijo samo na HTTPS ali localhostu. Po HTTP na
    // domacem naslovu klic tiho odpove, zato to povemo vnaprej in imenujemo
    // naslov -- sicer clovek isce napako pri sebi.
    if (!window.isSecureContext) {
      return reject(new Error(
        `Lokacija dela samo prek HTTPS; na ${location.host} je brskalnik ne da. `
        + "Odpri kajros.app."));
    }

    let id = null;
    let koncano = false;
    let najboljsa = null;

    const konec = (napaka) => {
      if (koncano) return;
      koncano = true;
      clearTimeout(cas);
      if (id !== null) navigator.geolocation.clearWatch(id);
      if (najboljsa) return resolve(najboljsa);   // groba lega je boljsa od nobene
      reject(napaka || new Error("Lokacije ni bilo mogoče dobiti."));
    };

    const cas = setTimeout(() => konec(new Error(
      `GPS se ni odzval v ${Math.round(rok / 1000)} s. Pod streho pogosto ne `
      + "dobi signala — poskusi zunaj ali izberi kraj na zemljevidu.")), rok);

    id = navigator.geolocation.watchPosition(
      (p) => {
        const l = { lat: p.coords.latitude, lon: p.coords.longitude,
                    acc: p.coords.accuracy };
        if (!najboljsa || l.acc < najboljsa.acc) najboljsa = l;
        if (napredek) napredek(l);
        // Prvi fix je lahko iz bazne postaje in gresi za kilometer; pocakamo
        // na boljsega, dokler je se cas.
        if (l.acc <= dovolj) konec(null);
      },
      (e) => konec(new Error(
        e.code === 1 ? `Dostop do lokacije je zavrnjen — dovoli ga v nastavitvah ${MOST ? "aplikacije" : "strani"}.`
        : e.code === 2 ? "Naprava lege ne zna dobiti (GPS ugasnjen ali brez signala)."
        : `GPS se ni odzval v ${Math.round(rok / 1000)} s.`)),
      // `maximumAge: 0`: brez tega brskalnik vrne do minuto star popravek in
      // prvi klik pokaze, kje si bil, ne kje si. Ujeto v zivo.
      { enableHighAccuracy: true, timeout: rok, maximumAge: 0 },
    );
  });
}

//: Lega, starejša od tega, ob vrnitvi na stran ni več tvoja: v minuti hoje
//: (5 km/h, `hoja.KMH`) se premakneš za 83 m, približno `LEGA_DOVOLJ_M`.
const LEGA_STARA_MS = 60000;
//: Gumb lege vzame lego sledenja, kadar je mlajša od tega, in ne čaka znova
//: na GPS, ki jo je pravkar povedal.
const LEGA_SVEZA_MS = 30000;
const STANJE_DOVOLJENJA = { granted: "dano", prompt: "vprasaj", denied: "zavrnjeno" };

/**
 * Lastna lega za vso stran: eno sledenje (`watchPosition`), ki ga delijo vsi
 * zemljevidi na njej.
 *
 * Teče, dokler je kdo prijavljen (`poslusaj`), stran vidna in lega dovoljena:
 * dovoljenje je dano ali pa je lega ta ogled že prišla (gumb, `potrdi`).
 * Skrita stran GPS ugasne: pike v žepu ne gleda nihče, baterija pa teče.
 */
const LEGA = (() => {
  const narocniki = new Set();      // `cb(lega | null)`
  const opazovalci = new Set();     // `cb(stanje)` ob spremembi dovoljenja
  let stanje = null;                // `null`: še nismo vprašali
  let branje = null;
  let dovoljenje = null;            // `PermissionStatus` brskalnika
  let potrjeno = false;
  let id = null;
  let zadnja = null;
  let cakaIzid = null;              // `vklopi()` v aplikaciji čaka na `kajrosLega`

  // V aplikaciji je resnica Androidovo dovoljenje (`Most.dovoljenja`). WebView
  // si ga ne zapomni (`retain = false`, android.md), `navigator.permissions`
  // pa v njem sploh ni (WebView 124, 22. 10. 2026). Trajne zavrnitve stran ne
  // loči: „Vklopi“ najprej vpraša sistem, ta pa ob trajni zavrnitvi odgovori
  // brez okna in aplikacija odpre svoje nastavitve. Aplikacija pred mostom 7
  // stanja ne pove: tam lega ostane na dotik.
  const izMostu = () => {
    if (MOST.razlicica() < 7) return "neznano";
    let d = {};
    try { d = JSON.parse(MOST.dovoljenja() || "{}"); } catch (e) { /* prazno */ }
    return d.lega ? "dano" : "vprasaj";
  };

  async function preberi() {
    if (!navigator.geolocation || !window.isSecureContext) return "neznano";
    if (MOST) return izMostu();
    if (!navigator.permissions) return "neznano";
    try {
      if (!dovoljenje) {
        dovoljenje = await navigator.permissions.query({ name: "geolocation" });
        // Dovoljenje, dano drugje (gumb, kartica, Deli lego), prižge sledenje
        // tudi tu; preklicano ga ugasne.
        dovoljenje.addEventListener("change", () =>
          nastavi(STANJE_DOVOLJENJA[dovoljenje.state] || "neznano"));
      }
      return STANJE_DOVOLJENJA[dovoljenje.state] || "neznano";
    } catch (e) {
      return "neznano";
    }
  }

  function osvezi() {
    if (!branje) branje = preberi().then((s) => { branje = null; nastavi(s); return s; });
    return branje;
  }

  // `potrjeno` velja tudi ob „vprasaj“: Firefox ob dovoljenju brez „zapomni
  // si“ ostane pri `prompt`, lega pa ta ogled dela. Prekliče ga samo prehod
  // z „dano“ (dovoljenje preklicano) ali zavrnitev.
  const sme = () => stanje === "dano" || (potrjeno && stanje !== "zavrnjeno");

  function nastavi(s) {
    const prej = stanje;
    stanje = s;
    if (s !== "dano" && (prej === "dano" || s === "zavrnjeno")) potrjeno = false;
    if (sme()) zazeni();
    else pozabi();
    if (s !== prej) for (const cb of opazovalci) cb(s);
  }

  function zazeni() {
    if (id !== null || !narocniki.size || document.visibilityState === "hidden" || !sme()) return;
    // `maximumAge: 0` iz istega razloga kot v `locateMe`. Roka ni: sledenje
    // čaka, kolikor je treba, in o izteku nima komu poročati.
    id = navigator.geolocation.watchPosition(obPopravku, obNapaki,
      { enableHighAccuracy: true, maximumAge: 0 });
  }

  function ustavi() {
    if (id === null) return;
    navigator.geolocation.clearWatch(id);
    id = null;
  }

  function pozabi() {
    ustavi();
    if (!zadnja) return;
    zadnja = null;
    for (const cb of narocniki) cb(null);
  }

  // Vsaka lega, tudi iz `locateMe`, je dokaz, da dovoljenje je.
  function sporoci(l) {
    potrjeno = true;
    zadnja = { ...l, ts: Date.now() };
    for (const cb of narocniki) cb(zadnja);
  }

  function obPopravku(p) {
    // Smer in hitrost sta za vodenje po pešpoti: GPS smer gibanja pozna samo
    // med hojo, kompas telefona pa tudi na mestu. Na mestu je `heading` po
    // specifikaciji `NaN`, ne `null` -- in `??` na NaN ne pade na kompas.
    sporoci({ lat: p.coords.latitude, lon: p.coords.longitude, acc: p.coords.accuracy,
              smer: Number.isFinite(p.coords.heading) ? p.coords.heading : null,
              hitrost: p.coords.speed });
  }

  // Brez signala sledenje teče naprej in molči: vzrok pove gumb lege
  // (`locateMe`). Zavrnjeno dovoljenje ga ustavi.
  function obNapaki(e) {
    if (e.code !== 1) return;
    potrjeno = false;
    pozabi();
    osvezi();
  }

  function obVrnitvi() {
    if (zadnja && Date.now() - zadnja.ts > LEGA_STARA_MS) pozabi();
    // Dovoljenje se je medtem lahko spremenilo (nastavitve aplikacije ali
    // brskalnika); `nastavi` nato sledenje prižge znova.
    if (narocniki.size || opazovalci.size) osvezi();
  }
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") ustavi();
    else obVrnitvi();
  });
  // Stran iz predpomnilnika nazaj (gumb nazaj) je stara stran, ki se vrača.
  addEventListener("pageshow", (e) => { if (e.persisted) obVrnitvi(); });

  if (MOST && MOST.razlicica() >= 7) {
    // Izid sistemskega okna ali vrnitve iz nastavitev (`GlavnaDejavnost.izidLege`).
    window.kajrosLega = (s, nastavitve) => {
      nastavi(s);
      if (cakaIzid) { cakaIzid({ stanje: s, nastavitve: !!nastavitve }); cakaIzid = null; }
    };
  }

  return {
    /** `cb(lega)` ob vsakem popravku, `cb(null)`, ko lege ni več. Vrne odjavo. */
    poslusaj(cb) {
      narocniki.add(cb);
      // Zadnjo lego dobi takoj za prijavo, ko ima klicatelj odjavo že v rokah.
      const z = zadnja;
      if (z) queueMicrotask(() => { if (narocniki.has(cb) && zadnja === z) cb(z); });
      if (stanje === null) osvezi();
      else zazeni();
      return () => {
        narocniki.delete(cb);
        if (!narocniki.size) ustavi();
      };
    },
    obStanju(cb) { opazovalci.add(cb); },
    stanje: osvezi,
    get zadnja() { return zadnja; },
    sporoci,
    /** Gumb lege je lego dobil: dovoljenje je zdaj gotovo dano. */
    potrdi() {
      potrjeno = true;
      zazeni();
    },
    vklopi() {
      if (MOST) {
        if (MOST.razlicica() < 7) return Promise.resolve({ stanje: "neznano" });
        return new Promise((ok) => {
          cakaIzid = ok;
          MOST.zahtevajLego();
        });
      }
      // Brskalnik vpraša sam ob prvem klicu. Šteje samo dovoljenje, zato
      // groba lega brez GPS: odgovor pride takoj, ne čez pol minute.
      return new Promise((ok) => {
        navigator.geolocation.getCurrentPosition(
          (p) => { obPopravku(p); ok({ stanje: "dano" }); },
          (e) => ok({ stanje: e.code === 1 ? "zavrnjeno" : "dano" }),
          { enableHighAccuracy: false, maximumAge: Infinity, timeout: LEGA_ROK_MS });
      }).then((izid) => {
        osvezi();
        return izid;
      });
    },
  };
})();

/** Ali sme stran lego brati, ne da bi koga kaj vprašala: `dano`, `vprasaj`,
 *  `zavrnjeno` (brskalnik; odklene ga nastavitev strani v brskalniku) ali
 *  `neznano` (tega ne vemo, zato lega teče samo na dotik). */
function stanjeLege() {
  return LEGA.stanje();
}

/**
 * Lega za gumb lege: zadnja iz sledenja, kadar je sveža in natančna, sicer
 * nova (`locateMe`, ki ob prvem dotiku sproži vprašanje za dovoljenje). Po
 * uspehu sledenje teče naprej za vse prijavljene.
 */
async function poisciMe(opts) {
  const z = LEGA.zadnja;
  if (z && Date.now() - z.ts < LEGA_SVEZA_MS && z.acc <= LEGA_DOVOLJ_M) {
    LEGA.potrdi();
    return z;
  }
  const napredek = opts && opts.napredek;
  const loc = await locateMe({ ...opts, napredek: (l) => { LEGA.sporoci(l); if (napredek) napredek(l); } });
  LEGA.potrdi();
  return loc;
}

/** „Vklopi“ na kartici domače strani; vrne `{stanje, nastavitve}`. */
function vklopiLego() {
  return LEGA.vklopi();
}

// ---------- pošlji povezavo ----------
// Okno vožnje in povabilo na domači strani. Kjer sistemskega izbirnika ni
// (aplikacija pred 1.13, Firefox na računalniku), se povezava kopira. Vrne
// „poslano“, „kopirano“, „preklicano“ ali „ni šlo“.
async function posljiPovezavo(naslov, besedilo, url) {
  if (navigator.share) {
    try {
      await navigator.share({ title: naslov, text: besedilo, url });
      return "poslano";
    } catch (err) {
      if (err.name === "AbortError") return "preklicano";   // premislil si je
    }
  }
  try {
    await navigator.clipboard.writeText(`${besedilo}\n${url}`);
    return "kopirano";
  } catch (err) {
    return "ni šlo";
  }
}

// ---------- pot, na kateri si ----------
//
// Izbrana pot od vrat do vrat ostane, dokler je potnik ne konča ali ne
// poteče: tudi čez zaprto aplikacijo in brskanje po drugih straneh, kot pri
// navigaciji. Prijava 22. 10. 2026: na prvem avtobusu je pozabil, kje
// prestopi, ker je vmes pogledal drugam in predloga ni bilo več.
//
// Samo v tej napravi (localStorage). Kam kdo gre, ne gre nikamor; strežnik ob
// osvežitvi dobi iste vožnje in koordinate kot ob iskanju.
//
// Zapis: `{v, sprejeto, vprasanje: {od, do, rok, hoje, kmh, dan}, spec: {noge,
// od_lat, od_lon, do_lat, do_lon, date, kmh}, predlog, osvezeno, stanje}`.
// `predlog` je zadnji odgovor `/api/pot/podrobno` (sprva kartica s seznama),
// `stanje` napredek, ki ga vodi stran poti (`pot_podrobno.js`).

const NA_POTI_KLJUC = "kajros:na-poti";
//: Koliko po pričakovanem prihodu pot še velja, kadar potnik ni rekel, da je
//: na cilju. Pričakovani prihod že nosi znano zamudo; ostanek je za zamudo,
//: ki je feed ne pozna, in za pogled nazaj, kje si izstopil.
const NA_POTI_PO_PRIHODU_MS = 45 * 60000;
//: Na cilju gre pot sama čez toliko -- pogled nazaj, ne seznam za ves dan.
const NA_POTI_NA_CILJU_MS = 10 * 60000;
//: Kadar je potnik po napredku še na poti do zadnjega vozila ali na njem:
//: ura prihoda je morda stara (stran poti ni bila odprta), vlak z zamudo pa
//: pot ne sme izbrisati sredi vožnje.
const NA_POTI_NA_VOZILU_MS = 2 * 3600000;
const NA_POTI_STRAN = "/app/pot/podrobno?na-poti=1";

const NA_POTI = {
  /** Pot, na kateri si, ali `null`. Potekla se ob branju pozabi. */
  beri() {
    let a = null;
    try {
      a = JSON.parse(localStorage.getItem(NA_POTI_KLJUC));
    } catch (e) {
      return null;
    }
    if (!a || a.v !== 1 || !a.predlog || !Array.isArray(a.predlog.noge) || !a.spec) return null;
    if (naPotiPoteklo(a, Date.now())) {
      NA_POTI.koncaj();
      return null;
    }
    return a;
  },
  zapisi(a) {
    try {
      localStorage.setItem(NA_POTI_KLJUC, JSON.stringify(a));
      return true;
    } catch (e) {
      return false;     // zasebno okno ali polna shramba: pot velja ta ogled
    }
  },
  koncaj() {
    try { localStorage.removeItem(NA_POTI_KLJUC); } catch (e) { /* ni je bilo */ }
  },
};

function naPotiPoteklo(a, zdajMs) {
  const st = a.stanje || {};
  if (st.cilj_ob && zdajMs - st.cilj_ob > NA_POTI_NA_CILJU_MS) return true;
  const koraki = korakiPoti(a.predlog);
  const zadnja = koraki.map((x) => x.vrsta).lastIndexOf("voznja");
  const naVozilu = st.korak > 0 && st.korak <= zadnja;
  return zdajMs > (a.predlog.prihod_ocena || a.predlog.prihod) * 1000
    + (naVozilu ? NA_POTI_NA_VOZILU_MS : NA_POTI_PO_PRIHODU_MS);
}

/**
 * Pot kot zaporedje korakov, kot jih potnik doživi: hoja, čakanje, vožnja,
 * cilj. `{vrsta, i, od, do}`: `i` je indeks noge v `p.noge`, `od` in `do`
 * sta pričakovani uri (sekunde epoch) z znanimi zamudami.
 *
 * Hoja pred prvo vožnjo se začne ob odhodu od doma, vsaka druga ob prihodu
 * prejšnje vožnje; kar ostane do naslednjega odhoda, je čakanje.
 */
function korakiPoti(p) {
  const out = [];
  let t = p.odhod_ocena || p.odhod;
  p.noge.forEach((n, i) => {
    if (n.vrsta === "hoja") {
      out.push({ vrsta: "hoja", i, od: t, do: t + n.sekunde });
      t += n.sekunde;
      return;
    }
    const odh = n.odhod_ocena || n.odhod;
    const prih = n.prihod_ocena || n.prihod;
    // Čakanje je tudi brez minute rezerve: na postajališču si, vozila še ni.
    out.push({ vrsta: "cakanje", i, od: t, do: Math.max(t, odh) });
    out.push({ vrsta: "voznja", i, od: odh, do: prih });
    t = prih;
  });
  out.push({ vrsta: "cilj", i: p.noge.length, od: t, do: t });
  return out;
}

// Tveganje prestopa (`pot.pripni_tveganje`): stopnja z besedo in vzorec.
// Ista govorica na seznamu predlogov, v predogledu in na poti -- zato tu.
const STOPNJA_RAZRED = { zanesljivo: "je-zanesljivo", tvegano: "je-tvegano",
                         "zelo tvegano": "je-zelo-tvegano" };

/** „držal 27 od 29 dni“ -- vzorec ob številki. Z manj kot tremi dnevi je
 *  številka večinoma delež podobnih prestopov („takšen“); ko je prvo vozilo
 *  na poti, verjetnost po zamudah zdaj. */
function prestopDrzi(t) {
  const tv = t.tveganje;
  if (tv.vir === "zdaj") return `po zamudah zdaj drži v ${Math.round(tv.p * 100)} %`;
  if (tv.dni >= 3) return `držal ${tv.drzal} od ${tv.dni} dni`;
  return `takšen drži v ${Math.round(tv.p * 100)} %`;
}

/** Korak, na katerem si po uri: prvi, ki se še ni končal -- a ne cilj. Ta
 *  je iz lege ali dotika: ura ob vrnitvi na stran je lahko iz stare zamude in
 *  „na cilju si“ bi potnika sredi zamujene vožnje poslal z vlaka. */
function korakPoCasu(koraki, zdajS) {
  const k = koraki.findIndex((x) => x.do > zdajS);
  const zadnji = Math.max(0, koraki.length - 2);
  return k < 0 ? zadnji : Math.min(k, zadnji);
}

/** Vožnja, h kateri vodi korak (hoja ali čakanje pred njo, ali ona sama). */
function voznjaKoraka(p, korak) {
  for (let j = korak.i; j < p.noge.length; j += 1) {
    if (p.noge[j].vrsta === "voznja") return p.noge[j];
  }
  return null;
}

const URA_POTI = (ts) => new Date(ts * 1000).toLocaleTimeString("sl-SI",
  { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Ljubljana" });

/** „čez 6 min“, „čez 1 h 20“, „zdaj“; drug dan „jutri“ ali datum -- a ne
 *  ponoči: nočni avtobus ob 00:05 je ob 23:50 „čez 15 min“, ne „jutri“. */
function cezPoti(ts, zdajS) {
  const dan = new Date(ts * 1000).toLocaleDateString("sv-SE", { timeZone: "Europe/Ljubljana" });
  if (dan !== todayIso() && Math.abs(ts - zdajS) >= 6 * 3600) {
    const jutri = new Date(`${todayIso()}T12:00:00`);
    jutri.setDate(jutri.getDate() + 1);
    return dan === jutri.toLocaleDateString("sv-SE") ? "jutri" : dayLabel(dan);
  }
  const m = Math.round((ts - zdajS) / 60);
  if (m <= 0) return "zdaj";
  return m < 60 ? `čez ${m} min` : `čez ${Math.floor(m / 60)} h ${String(m % 60).padStart(2, "0")}`;
}

/**
 * Kaj je naslednje, v eni vrstici: `{glavno, ura, cez, vrsta}`. Za trak na
 * drugih straneh in za glavo plošče na poti. Kadar napredka ne ve stran poti
 * (`a.stanje.korak`), velja ura -- in besedilo mora držati tudi, če potnik
 * vozilo čaka dlje, kot piše: zato ob vožnji ime vozila IN kraj izstopa.
 */
function naslednjeNaPoti(a, zdajS) {
  const p = a.predlog;
  const koraki = korakiPoti(p);
  const k = Math.max(korakPoCasu(koraki, zdajS),
                     Math.min((a.stanje && a.stanje.korak) || 0, koraki.length - 1));
  const korak = koraki[k];
  const n = p.noge[korak.i];
  const v = voznjaKoraka(p, korak);
  const prva = k === 0 && zdajS < korak.od - 60;
  if (korak.vrsta === "cilj") {
    return { vrsta: "cilj", glavno: "Na cilju", ura: URA_POTI(korak.od), cez: "" };
  }
  if (prva) {
    return { vrsta: "pred", glavno: `Odidi ob ${URA_POTI(korak.od)}`,
             ura: v ? `${imeVoznje(v)} ob ${URA_POTI(v.odhod_ocena || v.odhod)}` : "",
             cez: cezPoti(korak.od, zdajS) };
  }
  if (korak.vrsta === "voznja") {
    const prih = n.prihod_ocena || n.prihod;
    return { vrsta: "voznja", glavno: `Izstopi: ${n.do}`,
             ura: `${imeVoznje(n)} · ${URA_POTI(prih)}`, cez: cezPoti(prih, zdajS) };
  }
  if (!v) {
    return { vrsta: "hoja", glavno: "Do cilja", ura: `na cilju ob ${URA_POTI(p.prihod_ocena || p.prihod)}`,
             cez: cezPoti(p.prihod_ocena || p.prihod, zdajS) };
  }
  const odh = v.odhod_ocena || v.odhod;
  const prestop = p.noge.slice(0, p.noge.indexOf(v)).some((x) => x.vrsta === "voznja");
  return { vrsta: korak.vrsta,
           glavno: `${prestop ? "Prestopi na" : ""} ${imeVoznje(v)} ob ${URA_POTI(odh)}`.trim(),
           ura: v.od, cez: cezPoti(odh, zdajS) };
}

// Trak „na poti“ nad orodno vrstico, na vseh straneh z njo razen strani poti
// same: kot „vrni se v navigacijo“ -- en dotik nazaj, in tudi brez dotika
// pove, kje izstopiš. Brez omrežja: ure so iz zadnje osvežitve.
(function trakNaPoti() {
  const naStraniPoti = location.pathname === "/app/pot/podrobno"
    && new URLSearchParams(location.search).has("na-poti");
  if (!document.querySelector(".orodna") || naStraniPoti) return;
  let el = null;
  const risi = () => {
    const a = NA_POTI.beri();
    document.documentElement.classList.toggle("ima-pot", !!a);
    if (!a) {
      if (el) { el.remove(); el = null; }
      return;
    }
    const s = naslednjeNaPoti(a, Date.now() / 1000);
    if (!el) {
      el = document.createElement("a");
      el.className = "na-poti-trak";
      el.href = NA_POTI_STRAN;
      document.body.appendChild(el);
    }
    el.dataset.vrsta = s.vrsta;
    el.setAttribute("aria-label", `Tvoja pot: ${s.glavno}, ${s.ura} ${s.cez}`.trim());
    el.innerHTML = `<span class="npt-znak" aria-hidden="true"></span>
      <span class="npt-besedilo"><strong>${escapeHtml(s.glavno)}</strong>${
        s.ura ? `<span>${escapeHtml(s.ura)}</span>` : ""}</span>
      ${s.cez ? `<span class="npt-cez">${escapeHtml(s.cez)}</span>` : ""}`;
  };
  risi();
  setInterval(() => { if (!document.hidden) risi(); }, 20000);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) risi(); });
  // Druga stran (zavihek) je pot končala ali izbrala novo.
  addEventListener("storage", (e) => { if (e.key === NA_POTI_KLJUC) risi(); });
  addEventListener("pageshow", (e) => { if (e.persisted) risi(); });
})();

// ---------- dnevi rabe ----------
// Na katere dni je bil kajros odprt, zadnjih deset. Bere jih povabilo na
// domači strani (`home.js`): novincu, ki še ne ve, ali stran dela, ga ne
// ponudimo. Ostane v brskalniku, kot pove /zasebnost.
const DNEVI_KLJUC = "kajros:dnevi";
const DNEVI_SPOMIN = 10;

function dneviRabe() {
  try {
    const v = JSON.parse(localStorage.getItem(DNEVI_KLJUC) || "[]");
    return Array.isArray(v) ? v : [];
  } catch (e) {
    return [];
  }
}

(function zapisiDan() {
  const danes = todayIso();
  const v = dneviRabe();
  if (v[0] === danes) return;
  try {
    localStorage.setItem(DNEVI_KLJUC, JSON.stringify(
      [danes, ...v.filter((d) => d !== danes)].slice(0, DNEVI_SPOMIN)));
  } catch (e) { /* zasebno okno: povabila pač ni */ }
})();

// ---------- obvestila skrbnika ----------
// Kar kajros ve o sebi in podatki tega ne povedo sami: „vozni red avtobusov
// je danes pomanjkljiv". Piše jih skrbnik v /admin (`obvestila.py`). Stran
// ima zanje mesto `[data-obvestila="<omrežje>"]`; kjer ga ni, ni obvestil.
//
// Nalaga jih brskalnik in ne predloga, ker aplikacija za Android stran pusti
// odprto ure in dneve: obvestilo, objavljeno medtem, se mora pokazati, ko se
// potnik vrne, ne šele ob naslednjem nalaganju.

const OBV_SKRITA = "kajros:obvestila-skrita";
// Zaprtih si zapomnimo toliko najnovejših. Številke rastejo, zato starejše
// od teh ne morejo biti več veljavne.
const OBV_SPOMIN = 50;
const OBV_OMREZJE = { zeleznica: "vlaki", avtobus: "avtobusi" };

function obvSkrita() {
  try {
    const v = JSON.parse(localStorage.getItem(OBV_SKRITA) || "[]");
    return Array.isArray(v) ? v : [];
  } catch (e) {
    return [];     // zasebno okno: zaprto obvestilo se pokaže znova, nič hujšega
  }
}

function obvSkrij(id) {
  const v = [...new Set([id, ...obvSkrita()])].sort((a, b) => b - a).slice(0, OBV_SPOMIN);
  try { localStorage.setItem(OBV_SKRITA, JSON.stringify(v)); } catch (e) { /* glej zgoraj */ }
}

/** „danes ob 11:20“ ali „27. 9. ob 11:20“ -- obvestilo brez časa se ne da
 *  presoditi: včerajšnje „zamude manjkajo“ danes morda ne velja več. */
function obvKdaj(iso) {
  const dan = new Date(iso).toLocaleDateString("sv-SE", { timeZone: "Europe/Ljubljana" });
  return `${dan === todayIso() ? "danes" : dayLabel(dan)} ob ${hhmm(iso)}`;
}

function obvestiloHtml(o, vseOmrezje) {
  const komu = vseOmrezje && o.omrezje ? ` · ${OBV_OMREZJE[o.omrezje]}` : "";
  return `<div class="obvestilo" data-id="${o.id}">
    <svg class="obv-znak" width="20" height="20" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
      <circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.6v.01"/>
    </svg>
    <div class="obv-telo">
      <div class="obv-glava">Obvestilo kajrosa${komu} · ${escapeHtml(obvKdaj(o.objavljeno))}</div>
      <p class="obv-besedilo">${escapeHtml(o.besedilo)}</p>
    </div>
    <button type="button" class="obv-zapri" aria-label="Zapri obvestilo">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>
    </button>
  </div>`;
}

(function obvestila() {
  const mesto = document.querySelector("[data-obvestila]");
  if (!mesto) return;
  const omrezje = mesto.dataset.obvestila || "vse";
  let zadnje = "";

  const nalozi = async () => {
    const r = await fetch(`/api/obvestila?network=${encodeURIComponent(omrezje)}`);
    if (!r.ok) return;
    const skrita = new Set(obvSkrita());
    const vidna = (await r.json()).obvestila.filter((o) => !skrita.has(o.id));
    // Isto kot prej se ne riše znova: pasica bi utripnila ob vsaki vrnitvi.
    const odtis = JSON.stringify(vidna);
    if (odtis === zadnje) return;
    zadnje = odtis;
    mesto.innerHTML = vidna.map((o) => obvestiloHtml(o, omrezje === "vse")).join("");
    mesto.hidden = !vidna.length;
  };

  mesto.addEventListener("click", (e) => {
    const gumb = e.target.closest(".obv-zapri");
    if (!gumb) return;
    const kartica = gumb.closest(".obvestilo");
    obvSkrij(Number(kartica.dataset.id));
    kartica.remove();
    zadnje = "";
    mesto.hidden = !mesto.querySelector(".obvestilo");
  });

  // Pet minut, dokler je stran vidna, in ob vrnitvi nanjo, če je od zadnjega
  // branja minilo več kot pol tega. Pogosteje ni treba: obvestilo pove
  // stanje za ure, ne za minute.
  pollWhileVisible(nalozi, 5 * 60000);
})();

// Service worker. Registrira se sam in samo tam, kjer sme.
//
// `isSecureContext` je pogoj brskalnika, ne nas: po `http://192.168.1.164:8001`
// `navigator.serviceWorker` sploh ne obstaja (izmerjeno). Preverjanje je tu
// zato, da razvoj po omrežnem naslovu ne meče napak v konzolo -- ta mora
// ostati prazna, ker jo `preveri.sh` bere kot merilo.
if ("serviceWorker" in navigator && window.isSecureContext) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  });
}
