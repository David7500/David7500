"use strict";

// Pregled za skrbnika: kdo je bil na strani in ali stroj dela.
//
// Zavihki -- Stanje, Viri, Zgodovina, Sporočila, Obvestila, Deljenje. Vsi
// razen zadnjega berejo en endpoint, `/admin/podatki?od=&do=`. Brez meja vrne
// današnji dan; odgovor vedno nosi še `danes`, `zadnjih30`, zdravje, vire in
// sporočila, zato vsi rabijo en klic, Zgodovina pa enega več za izbrano
// obdobje. Deljenje ima svoj endpoint in ritem (`admin_deljenje.js`).
//
// Kar je na tej strani najlažje narobe prebrati, je vsota dnevnih
// obiskovalcev. Sol se vsak dan zavrže (glej `obisk.py`), zato ista oseba v
// tridesetih dneh šteje tridesetkrat -- nad enim dnem je številka zato
// povsod „obiskov", ne „ljudi".
//
// Oblika je predloga A iz `design/admin/`.

const el = (id) => document.getElementById(id);
const st = (n, d = 0) => (n == null ? "—" : Number(n).toLocaleString("sl-SI",
  { minimumFractionDigits: d, maximumFractionDigits: d }));

const MESECI = ["januar", "februar", "marec", "april", "maj", "junij", "julij",
  "avgust", "september", "oktober", "november", "december"];
const DNI_TEDNA = ["ned", "pon", "tor", "sre", "čet", "pet", "sob"];
const OBDOBJA = { dan: "Dan", teden: "Teden", mesec: "Mesec", leto: "Leto", vse: "Vse" };

/** Ime poti, kakor ga bere človek. Česar ni tu, ostane pot. */
const IMENA_STRANI = {
  "/": "Domača", "/app/pot": "Iskalnik poti", "/app/pot/podrobno": "Pot · podrobno",
  "/app/bus": "Avtobus", "/app/bus/{train_no}": "Avtobus · vožnja",
  "/app/train": "Vlak", "/app/train/{train_no}": "Vlak · vožnja",
  "/app/map": "Zemljevid", "/app/ovire": "Ovire", "/app/statistika": "Statistika",
  "/app/statistika/{omrezje}": "Statistika · avtobus",
  "/vlak/{od}/{cilj}": "Relacija · vlak", "/avtobus/{od}/{cilj}": "Relacija · avtobus",
  "/postaja/{ime}": "Postaja", "/postajalisce/{ime}": "Postajališče",
  "/postaje": "Kazalo postaj", "/postajalisca": "Kazalo postajališč",
  "/o-nas": "O nas", "/primerjava": "Primerjava",
};
const imeStrani = (p) => IMENA_STRANI[p] || p;

// ------------------------------------------------------------------ datumi
//
// Vse v nizih ISO in v lokalnem koledarju: dan je dan obratovanja strežnika
// (`danes_dan`), ne ura brskalnika, ki je lahko v drugem pasu.

function izIso(s) { const [y, m, d] = s.split("-").map(Number); return new Date(y, m - 1, d); }
function vIso(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
function dodaj(s, n) { const d = izIso(s); d.setDate(d.getDate() + n); return vIso(d); }
function kratki(s) { const d = izIso(s); return `${d.getDate()}. ${d.getMonth() + 1}.`; }
function dolgi(s) { const d = izIso(s); return `${DNI_TEDNA[d.getDay()]}, ${d.getDate()}. ${d.getMonth() + 1}. ${d.getFullYear()}`; }

const URA_FMT = new Intl.DateTimeFormat("sl-SI", { timeZone: "Europe/Ljubljana", hour: "numeric", hour12: false });
const zdajUra = () => Number(URA_FMT.format(new Date()));

/** [od, do] obdobja, ki vsebuje `sidro`. Teden začne v ponedeljek. */
function meje(vrsta, sidro) {
  const d = izIso(sidro);
  if (vrsta === "dan") return [sidro, sidro];
  if (vrsta === "teden") { const pon = dodaj(sidro, -((d.getDay() + 6) % 7)); return [pon, dodaj(pon, 6)]; }
  if (vrsta === "mesec") return [vIso(new Date(d.getFullYear(), d.getMonth(), 1)), vIso(new Date(d.getFullYear(), d.getMonth() + 1, 0))];
  if (vrsta === "leto") return [`${d.getFullYear()}-01-01`, `${d.getFullYear()}-12-31`];
  return [prviDan(), danes()];
}

function premakni(vrsta, sidro, smer) {
  const d = izIso(sidro);
  if (vrsta === "dan") return dodaj(sidro, smer);
  if (vrsta === "teden") return dodaj(sidro, 7 * smer);
  if (vrsta === "mesec") return vIso(new Date(d.getFullYear(), d.getMonth() + smer, 1));
  if (vrsta === "leto") return vIso(new Date(d.getFullYear() + smer, 0, 1));
  return sidro;
}

function naslovObdobja(vrsta, sidro) {
  const [od, do_] = meje(vrsta, sidro);
  const d = izIso(sidro);
  if (vrsta === "dan") return dolgi(sidro);
  if (vrsta === "teden") return `${kratki(od)} – ${kratki(do_)} ${izIso(do_).getFullYear()}`;
  if (vrsta === "mesec") return `${MESECI[d.getMonth()]} ${d.getFullYear()}`;
  if (vrsta === "leto") return String(d.getFullYear());
  return `vse od ${kratki(od)} ${izIso(od).getFullYear()}`;
}

function vseDni(od, do_) {
  const out = [];
  for (let d = od; d <= do_; d = dodaj(d, 1)) out.push(d);
  return out;
}

// ------------------------------------------------------------------ oblika

function ms(v) {
  if (v == null) return "—";
  if (v < 1000) return `${st(v)} ms`;
  if (v < 60000) return `${st(v / 1000, 1)} s`;
  return `${st(v / 60000, 1)} min`;
}
/** Pod 1 s je v redu, do 5 s potnik opazi, nad 5 s odneha. */
const msRazred = (v) => (v == null || v < 1000 ? "" : v < 5000 ? "ms-hard" : "ms-bad");

function bajti(b) {
  if (b == null) return "—";
  const e = ["B", "kB", "MB", "GB", "TB"];
  let i = 0;
  while (b >= 1024 && i < e.length - 1) { b /= 1024; i += 1; }
  return `${st(b, b < 10 && i > 0 ? 1 : 0)} ${e[i]}`;
}
function trajanje(s) {
  if (s == null) return "—";
  if (s < 3600) return `${Math.round(s / 60)} min`;
  if (s < 86400) return `${st(s / 3600, 1)} h`;
  return `${st(s / 86400, 1)} dni`;
}
function pred(ts) {
  if (!ts) return "nikoli";
  const s = Math.max(0, Math.round(Date.now() / 1000 - ts));
  if (s < 90) return `pred ${s} s`;
  if (s < 5400) return `pred ${Math.round(s / 60)} min`;
  return `pred ${st(s / 3600, 1)} h`;
}
function prazno(kaj) { return `<div class="adm-prazno">${escapeHtml(kaj)}</div>`; }

/** Sprememba proti prejšnjemu obdobju; brez podatka ne trdi ničesar. */
function razlika(zdaj, prej, dniPrej) {
  if (!dniPrej || !prej) return "prej ni podatka";
  const p = Math.round(100 * (zdaj - prej) / prej);
  const razred = p > 0 ? "gor" : p < 0 ? "dol" : "";
  return `<span class="${razred}">${p > 0 ? "+" : p < 0 ? "−" : "±"}${Math.abs(p)} %</span> proti prejšnjemu`;
}

// ------------------------------------------------------------------ grafi

let _tip = null;
/** En plavajoč namig za vse, kar nosi `data-tip`. Vsebina je naš HTML. */
function namig() {
  if (_tip) return;
  _tip = document.createElement("div");
  _tip.className = "adm-tip";
  _tip.hidden = true;
  document.body.appendChild(_tip);
  document.addEventListener("pointermove", (e) => {
    const t = e.target.closest && e.target.closest("[data-tip]");
    if (!t) { _tip.hidden = true; return; }
    _tip.innerHTML = t.dataset.tip;
    _tip.hidden = false;
    const r = _tip.getBoundingClientRect();
    let x = e.clientX + 14, y = e.clientY - r.height - 10;
    if (x + r.width > innerWidth - 8) x = e.clientX - r.width - 14;
    if (y < 8) y = e.clientY + 16;
    _tip.style.left = `${x}px`;
    _tip.style.top = `${y}px`;
  });
}

function korakOsi(naj) {
  const surovo = naj / 4;
  const p = 10 ** Math.floor(Math.log10(Math.max(surovo, 1)));
  for (const k of [1, 2, 2.5, 5, 10]) if (k * p >= surovo) return Math.max(1, k * p);
  return 10 * p;
}

/**
 * Navpični stolpci, sidrani na osnovnico. Vrednost `null` je dan brez štetja
 * in je šrafiran -- „štetja še ni bilo" ni isto kot „ni prišel nihče".
 * `undefined` je prihodnost in je ni.
 */
function stolpci(vrednosti, { visina = 200, oznake, tip, poudari = -1, klik = false } = {}) {
  namig();
  const n = vrednosti.length;
  const naj = Math.max(1, ...vrednosti.filter((v) => v != null));
  const korak = korakOsi(naj);
  const vrh = Math.ceil(naj / korak) * korak;
  const W = 1000, H = visina, L = 34, B = oznake ? 22 : 6, T = 8;
  // Pri malo stolpcih je presledek širši, sicer teden izgleda kot trije zidovi.
  const sir = (W - L) / n, rob = n < 12 ? sir * 0.45 : Math.min(6, sir * 0.22);
  const y = (v) => T + (H - T - B) * (1 - v / vrh);
  let s = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img">`
    + `<defs><pattern id="adm-sraf" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">`
    + `<line x1="0" y1="0" x2="0" y2="6" stroke="var(--line-firm)" stroke-width="2"/></pattern></defs>`;
  for (let v = 0; v <= vrh; v += korak) s += `<line class="mreza" x1="${L}" x2="${W}" y1="${y(v)}" y2="${y(v)}"/>`;
  vrednosti.forEach((v, i) => {
    if (v === undefined) return;
    const x = L + i * sir + rob / 2, w = sir - rob;
    const t = tip ? escapeHtml(tip(i)) : "";
    if (v === null) {
      s += `<rect x="${x}" y="${T}" width="${w}" height="${H - T - B}" fill="url(#adm-sraf)" opacity=".55" data-tip="${t}"/>`;
      return;
    }
    const h = Math.max(v > 0 ? 2 : 0, H - B - y(v));
    const r = Math.min(4, w / 2, h);
    s += `<rect class="${klik ? "klik" : ""}" x="${x - rob / 2}" y="${T}" width="${sir}" height="${H - T - B}" fill="transparent" data-i="${i}" data-tip="${t}"/>`;
    s += `<path class="stolpec${i === poudari ? " je-poudarek" : ""}" pointer-events="none" `
      + `d="M${x},${H - B} V${H - B - h + r} q0,-${r} ${r},-${r} h${w - 2 * r} q${r},0 ${r},${r} V${H - B} Z"/>`;
  });
  s += "</svg>";
  // Osi so HTML, ne SVG: `preserveAspectRatio=none` bi črke raztegnil.
  let osi = `<div class="adm-osy">`;
  for (let v = vrh; v >= 0; v -= korak) osi += `<span style="top:${(y(v) / H) * 100}%">${st(v)}</span>`;
  osi += "</div>";
  if (oznake) {
    osi += `<div class="adm-osx" style="padding-left:${(L / W) * 100}%">`
      + oznake.map((o) => `<span>${escapeHtml(o)}</span>`).join("") + "</div>";
  }
  return `<div class="adm-graf" style="height:${H}px">${s}${osi}</div>`;
}

/** Ena vodoravna vrstica: ime, tir, število, pripis. */
function vrsta(ime, v, naj, desno = "") {
  const d = naj > 0 ? Math.max(1.5, (100 * v) / naj) : 0;
  const tip = `<b>${escapeHtml(ime)}</b><br>${st(v)}${desno ? ` · ${escapeHtml(desno)}` : ""}`;
  return `<div class="adm-hv" data-tip="${escapeHtml(tip)}">
    <span class="adm-hv-ime">${escapeHtml(ime)}</span>
    <span class="adm-hv-tir"><span style="width:${d.toFixed(1)}%"></span></span>
    <span class="adm-hv-st">${st(v)}</span>
    <span class="adm-hv-pri">${escapeHtml(desno)}</span></div>`;
}

// ------------------------------------------------------------------ gradniki

function ploscica(v, ime, pod, razred = "") {
  return `<div class="adm-k"><div class="adm-k-v ${razred}">${v}</div>
    <div class="adm-k-i">${escapeHtml(ime)}</div><div class="adm-k-d">${pod}</div></div>`;
}

function plosca(razred, naslov, pripis, vsebina, pod = "&nbsp;") {
  return `<section class="adm-plosca ${razred}"><h2>${escapeHtml(naslov)}
    <small>${escapeHtml(pripis)}</small></h2><p class="adm-pod">${pod}</p>${vsebina}</section>`;
}

/** Kar se je odzivalo počasi. `(neznano)` so ugibanja botov in ne naša pot. */
function pocasne(d, n) {
  return (d.endpointi || []).filter((e) => e.pot !== "(neznano)" && e.zahtev > 0)
    .sort((a, b) => b.ms_naj - a.ms_naj).slice(0, n);
}

function razredMs(p) {
  if (!p || !p.n) return "—";
  return p.do == null ? "› 5 s" : `‹ ${ms(p.do)}`;
}

function tabelaPocasnih(d, n) {
  const vrst = pocasne(d, n);
  if (!vrst.length) return prazno("ni zahtev");
  // p95 je razred, ne vrednost (glej `obisk._percentil`): zato „‹ 250 ms".
  return `<div class="adm-ovoj-t"><table class="adm-t"><thead><tr><th>pot</th><th class="n">zahtev</th>
    <th class="n">povprečno</th><th class="n">p95</th><th class="n">najdlje</th><th class="n">4xx</th><th class="n">5xx</th></tr></thead><tbody>
    ${vrst.map((r) => `<tr><td class="pot" title="${escapeHtml(r.pot)}">${escapeHtml(r.pot)}</td>
      <td class="n">${st(r.zahtev)}</td>
      <td class="n ${msRazred(r.ms_povprecje)}">${ms(r.ms_povprecje)}</td>
      <td class="n ${r.p95 && r.p95.n && r.p95.do == null ? "ms-bad" : ""}">${razredMs(r.p95)}</td>
      <td class="n ${msRazred(r.ms_naj)}">${ms(r.ms_naj)}</td>
      <td class="n ${r.napak4 ? "" : "nic"}">${st(r.napak4)}</td>
      <td class="n ${r.napak5 ? "ms-bad" : "nic"}">${st(r.napak5)}</td></tr>`).join("")}
    </tbody></table></div>`;
}

function blokStrani(d, n) {
  const vrst = (d.strani || []).filter((s) => s.zahtev > 0).slice(0, n);
  if (!vrst.length) return prazno("nobene odprte strani");
  const naj = Math.max(1, ...vrst.map((s) => s.ljudi));
  return vrst.map((s) => vrsta(imeStrani(s.pot), s.ljudi, naj, `${st(s.zahtev)}×`)).join("");
}

function blokNaprav(d) {
  const r = d.razrezi || {};
  const nap = r.naprava || [], drz = r.drzava || [];
  if (!nap.length) return prazno("še ni obiska");
  const nv = nap.reduce((a, x) => a + x.ogledov, 0) || 1;
  const nd = drz.reduce((a, x) => a + x.ogledov, 0) || 1;
  // „??" pomeni, da glave o državi ni bilo -- zahteva ni prišla skozi
  // Cloudflare, ampak iz domačega omrežja. To ni neznanka, ampak podatek.
  return nap.map((x) => vrsta(x.kljuc, x.ogledov, nv, `${st(100 * x.ogledov / nv)} %`)).join("")
    + `<div class="adm-razmik"></div>`
    + drz.slice(0, 5).map((x) => vrsta(x.kljuc === "??" ? "domače" : x.kljuc, x.ogledov, nd,
      `${st(100 * x.ogledov / nd)} %`)).join("");
}

// ------------------------------------------------------------ iskalniki in AI
//
// Od 29. 9. 2026. Do tedaj ni bilo mogoče reči, ali nas Google sploh obišče,
// in človek, ki je z iskalnika prišel na pristajalno stran (brez JS), se ni
// štel. Vir je samo ime (Google, ChatGPT), nikoli iskalni niz. Robot je, kar
// se za robota predstavi -- ponarediti zna vsak.

const ROBOT_KAJ = {
  Googlebot: "Google", bingbot: "Bing, ChatGPT, Copilot", "OAI-SearchBot": "iskanje ChatGPT",
  "ChatGPT-User": "ChatGPT odpre na prošnjo", "Claude-User": "Claude odpre na prošnjo",
  "Claude-SearchBot": "iskanje Claude", PerplexityBot: "Perplexity", "Perplexity-User": "Perplexity odpre",
  GPTBot: "učenje OpenAI", ClaudeBot: "učenje Anthropic", CCBot: "Common Crawl",
  DuckAssistBot: "DuckDuckGo AI", Applebot: "Apple, Siri",
};

function blokVirov(d) {
  const v = (d.razrezi || {}).vir || [];
  if (!v.length) return prazno("vsi naravnost");
  const naj = Math.max(1, ...v.map((x) => x.ogledov));
  return v.slice(0, 10).map((x) => vrsta(x.kljuc, x.ogledov, naj)).join("");
}

// -------------------------------------------------------------------- podpora
//
// Od 4. 10. 2026. Klik na „Podari“ gre prek `/donacije/naprej`, ki preusmeri
// na plačilno stran. Klik ni donacija -- plačilo teče pri ponudniku in ga ne
// vidimo --, je pa zgornja meja in edini korak, ki ga lahko izmerimo.

function blokPodpore(d) {
  const p = d.donacije || {};
  if (!p.ogledi && !p.klikov) return prazno("nihče ni odprl /donacije");
  const naj = Math.max(1, p.ljudi, p.klikov_ljudi);
  const delez = p.ljudi ? `${st(100 * p.klikov_ljudi / p.ljudi)} % jih je kliknilo naprej` : "";
  return vrsta("odprlo /donacije", p.ljudi, naj, `${st(p.ogledi)}×`)
    + vrsta("kliknilo Podari", p.klikov_ljudi, naj, `${st(p.klikov)}×`)
    + (delez ? `<div class="adm-pod">${delez}</div>` : "");
}

/** Ogledi po dnevih in virih: kaj je sprožilo vrh. Samo znani viri; kdor pride naravnost, ni v tabeli. */
function tabelaVirovPoDnevih(o) {
  const vrstice = o.vir_po_dnevih || [];
  if (!vrstice.length) return prazno("v tem obdobju ni prihodov z znanega vira");
  const skupaj = new Map();
  for (const r of vrstice) skupaj.set(r.kljuc, (skupaj.get(r.kljuc) || 0) + r.ogledov);
  const stolpec = [...skupaj].sort((a, b) => b[1] - a[1]).slice(0, 4).map(([k]) => k);
  const po = new Map();
  for (const r of vrstice) {
    if (!po.has(r.dan)) po.set(r.dan, {});
    po.get(r.dan)[r.kljuc] = r.ogledov;
  }
  const ljudi = new Map((o.po_dnevih || []).map((r) => [r.dan, r.ljudi]));
  const dni = [...po.keys()].sort().reverse().slice(0, 45);
  return `<div class="adm-ovoj-t"><table class="adm-t"><thead><tr><th>dan</th><th class="n">ljudi</th>
    ${stolpec.map((k) => `<th class="n">${escapeHtml(k)}</th>`).join("")}<th class="n">drugo</th></tr></thead><tbody>
    ${dni.map((dan) => {
      const v = po.get(dan);
      const drugo = Object.entries(v).filter(([k]) => !stolpec.includes(k)).reduce((a, [, n]) => a + n, 0);
      return `<tr><td>${dolgi(dan)}</td><td class="n">${st(ljudi.get(dan))}</td>
        ${stolpec.map((k) => `<td class="n ${v[k] ? "" : "nic"}">${st(v[k] || 0)}</td>`).join("")}
        <td class="n ${drugo ? "" : "nic"}">${st(drugo)}</td></tr>`;
    }).join("")}
    </tbody></table></div>`;
}

function blokRobotov(d) {
  const r = (d.razrezi || {}).robot || [];
  if (!r.length) return prazno("nobenega");
  const naj = Math.max(1, ...r.map((x) => x.zahtev));
  return r.slice(0, 14).map((x) => vrsta(
    ROBOT_KAJ[x.kljuc] ? `${x.kljuc} · ${ROBOT_KAJ[x.kljuc]}` : x.kljuc,
    x.zahtev, naj, st(x.ogledov))).join("");
}

// ------------------------------------------------------------------ aplikacija
//
// Aplikacija za Android se šteje od `aplikacija_od` (24. 9. 2026). Prej je
// ni bilo mogoče ločiti -- dan pred tem je „štetja še ni bilo“, ne „nihče“.
// „Odprlo“ je okno aplikacije (WebView); pripomoček, budilka in preverjanje
// posodobitve tečejo tudi brez tega in so zato posebej.

const PRENOS_IZ = { stran: "nova namestitev", aplikacija: "posodobitev" };
/** `kajros-1.2.apk` -> `1.2`; tuje ime ostane, kot je. */
const imeIzdaje = (f) => { const m = /^kajros-(.+)\.apk$/.exec(f); return m ? m[1] : f; };

function mini(v, ime, razred = "") {
  return `<div><b class="${razred}">${st(v)}</b><span>${escapeHtml(ime)}</span></div>`;
}

/**
 * Številke aplikacije za obdobje `d`: kdo jo je odprl, kdo jo ima samo v
 * ozadju, koliko prenosov in katere različice tečejo. `n` so vsote --
 * današnje ali obdobja -- da isti blok služi obema zavihkoma.
 */
function blokAplikacije(d, n, vecDni) {
  const od = d.aplikacija_od;
  if (!od || od > d.do) return prazno(`Aplikacija se šteje od ${od ? dolgi(od) : "prve objave s tem štetjem"}.`);
  const r = d.razrezi || {};
  const iz = r.prenos_iz || [], izdaje = r.prenos || [], raz = d.razlicice || [];
  const najIz = Math.max(1, ...iz.map((x) => x.zahtev), ...izdaje.map((x) => x.zahtev));
  const vsehRaz = raz.reduce((a, x) => a + x.ljudi, 0) || 1;
  const prenosi = !iz.length ? prazno("ni prenosov")
    : iz.map((x) => vrsta(PRENOS_IZ[x.kljuc] || x.kljuc, x.zahtev, najIz)).join("")
      + (izdaje.length > 1 ? `<div class="adm-razmik"></div>`
        + izdaje.map((x) => vrsta(`različica ${imeIzdaje(x.kljuc)}`, x.zahtev, najIz)).join("") : "");
  const razlicice = !raz.length ? prazno("nihče")
    : raz.map((x) => vrsta(`različica ${x.kljuc}`, x.ljudi, vsehRaz, `${st(100 * x.ljudi / vsehRaz)} %`)).join("");
  return `<div class="adm-app">
    <div class="adm-mini">
      ${mini(n.app, vecDni ? "obiskov v aplikaciji" : "odprlo aplikacijo", "je-poudarek")}
      ${mini(n.ozadje, "samo pripomoček ali budilka")}
      ${mini(n.prenosov, "prenosov")}
    </div>
    <div><h3 class="adm-mali">Prenosi</h3>${prenosi}</div>
    <div><h3 class="adm-mali">Različice v rabi${vecDni ? " · vsota dnevnih" : ""}</h3>${razlicice}</div>
  </div>`;
}

/** Pripis pod naslovom, kadar obdobje sega pred začetek štetja. */
function podAplikacije(d) {
  const od = d.aplikacija_od;
  return od && od > d.od && od <= d.do ? `Šteto od ${escapeHtml(dolgi(od))}; prej aplikacije ni bilo mogoče ločiti.` : "&nbsp;";
}

let vedraApp = [];           // katere dneve nosi vsak stolpec grafov aplikacije

/**
 * Dva grafa: ljudje, ki so aplikacijo odprli, in prenosi. `vedra` so
 * stolpci -- en dan ali, pri letu, en mesec. Stolpec pred začetkom štetja
 * je šrafiran, ne ničla.
 */
function grafiAplikacije(d, vrstice, vedra) {
  vedraApp = vedra;
  const od = d.aplikacija_od;
  const po = new Map(vrstice.map((r) => [r.dan, r]));
  const vsota = (v, f) => {
    if (v.dni[0] > danes()) return undefined;
    const imajo = v.dni.filter((dan) => od && dan >= od && po.has(dan));
    return imajo.length ? imajo.reduce((a, dan) => a + f(po.get(dan)), 0) : null;
  };
  const app = vedra.map((v) => vsota(v, (r) => r.app));
  const ozadje = vedra.map((v) => vsota(v, (r) => r.app_ozadje));
  const pren = vedra.map((v) => vsota(v, (r) => r.prenosov));
  const posod = vedra.map((v) => vsota(v, (r) => r.prenosov_iz_aplikacije));
  const tip = (i, kaj) => (app[i] == null ? `${vedra[i].ime}<br>ni podatka` : `<b>${vedra[i].ime}</b><br>${kaj}`);
  const oznake = vedra.map((v) => v.oznaka);
  return `<div id="graf-app">
    <p class="adm-graf-ime">odprli aplikacijo</p>
    ${stolpci(app, { visina: 130, klik: true,
      tip: (i) => tip(i, `${st(app[i])} odprlo · ${st(ozadje[i])} samo v ozadju`) })}
    <p class="adm-graf-ime">prenosov</p>
    ${stolpci(pren, { visina: 110, oznake, klik: true,
      tip: (i) => tip(i, `${st(pren[i])} prenosov · ${st(posod[i])} posodobitev iz aplikacije`) })}
  </div>`;
}

/** Stolpci za graf obdobja: pri letu meseci, sicer dnevi. */
function vedraObdobja(o) {
  if (izbor.vrsta === "leto") {
    const leto = izIso(o.od).getFullYear();
    return MESECI.map((m, k) => ({
      ime: `${m} ${leto}`, oznaka: m.slice(0, 3),
      dni: vseDni(vIso(new Date(leto, k, 1)), vIso(new Date(leto, k + 1, 0))),
    }));
  }
  const dni = vseDni(o.od, o.do);
  const korak = dni.length > 120 ? 30 : 7;
  return dni.map((dan, i) => ({
    ime: dolgi(dan), dni: [dan], oznaka: dni.length <= 14 || i % korak === 0 ? kratki(dan) : "",
  }));
}

// ------------------------------------------------------------------ viri
//
// Zavihek „Viri“ (od 9. 10. 2026). Prej je bilo zdravje 23 vrstic v eni
// plošči sredi obiska: vir, njegov števec, primerjava dveh virov in disk
// drug ob drugem, brez besede o tem, kaj je vir, kaj daje in kaj storiti, ko
// ne dela. Zdaj ima vsak vir kartico (`viri.py` na strežniku pove, kaj je),
// izid zajema in stroj pa vsak svojo ploščo.
//
// Barve in razloge še vedno računa strežnik (`zdravje.ocena()`): ista pravila
// pošiljajo pošto, dve kopiji mej bi se razšli.

const URA_TS = new Intl.DateTimeFormat("sl-SI", { timeZone: "Europe/Ljubljana", hour: "2-digit", minute: "2-digit" });
const DAN_TS = new Intl.DateTimeFormat("sl-SI", { timeZone: "Europe/Ljubljana", day: "numeric", month: "numeric" });
/** Ura, ob starejšem od 20 h še dan: „16:02“ ali „8. 10. 16:02“. */
function uraTs(ts) {
  if (!ts) return "—";
  const d = new Date(ts * 1000);
  return Date.now() / 1000 - ts > 72000 ? `${DAN_TS.format(d)} ${URA_TS.format(d)}` : URA_TS.format(d);
}
/** Datum ISO kot „12. 12. 2026“. */
const datumIso = (s) => { const d = izIso(s); return `${d.getDate()}. ${d.getMonth() + 1}. ${d.getFullYear()}`; };

const RANG = { "je-slaba": 3, "je-mlacna": 2, "je-dobra": 1, "": 0 };

/** Slovenska množina: mn(2, "branje", "branji", "branja", "branj") -> „2 branji“. */
function mn(n, ena, dve, tri, pet) {
  const k = Math.abs(n) % 100;
  return `${st(n)} ${k === 1 ? ena : k === 2 ? dve : k === 3 || k === 4 ? tri : pet}`;
}
const najslabse = (razredi) => razredi.reduce((a, r) => (RANG[r || ""] > RANG[a] ? r : a), "");

/** Kako se pri katerem viru imenuje žig v bazi (`viri.zapisano`). */
const ZAPIS_IME = {
  derp_zamude: "zadnje branje v bazi", derp_lpp: "zadnje branje v bazi",
  derp_ovire: "angleška ovira nazadnje v feedu", nap: "nit nazadnje zapisala",
  zamude_sz: "nit nazadnje zapisala", zamude_lpp: "nit nazadnje zapisala",
  ovire_sz: "nit nazadnje zapisala",
  peroni: "zadnja prebrana tabla", gtfs_ijpp: "zadnji uvoz", gtfs_lpp: "zadnji uvoz",
  vreme: "zadnji prenos",
};

let preverba = null;        // izid „Preveri vire“: {teče} ali odgovor strežnika
let skokNaVir = null;       // kartica, na katero naj skoči zavihek Viri

/** Chrome za potniski.sz.si (`brskalnik.py`) v eni vrstici. */
function opisBrskalnika(b) {
  if (!b) return "še ni bil zagnan (nihče ga ni rabil)";
  if (!b.tece) {
    return b.napaka ? `ne teče: ${b.napaka}` : b.pot ? "ne teče" : "ni Chroma";
  }
  const izzivi = b.izzivi ? ` · izzivov ${st(b.izzivi)}` : "";
  return `${b.razlicica || "Chrome"} · ${b.zaslon || "?"} · teče od ${uraTs(b.od_ts)}`
    + `${b.pomnilnik ? ` · ${bajti(b.pomnilnik)}` : ""} · zahtev ${st(b.zahtev)}`
    + ` · zagonov ${st(b.zagonov)}${izzivi}`
    + (b.zadnji_preboj_s != null ? ` · zadnji izziv ${st(b.zadnji_preboj_s, 1)} s ob ${uraTs(b.zadnji_preboj_ts)}` : "");
}

function ujemanje(p) {
  return !p || !p.parov ? null
    : `${st(100 * p.v_minuti / p.parov)} % v minuti od ${st(p.parov)} · nad 5 min ${st(p.nad_5_min)}`;
}

/** Vrstice, ki jih pozna samo ta vir: števci iz `/api/health`. */
function podrobnostiVira(kljuc, d) {
  const z = d.zdravje || {};
  const out = [];
  const dodaj = (ime, vr) => { if (vr != null && vr !== "") out.push([ime, vr]); };
  const nez = (vir) => { const n = (z.rt_neznanih || {})[vir]; return n ? `${st(n[0])} od ${st(n[1])}` : null; };
  if (kljuc === "derp_zamude") {
    dodaj("vožnje brez voznega reda", nez("ijpp"));
    const lbz = Object.entries(z.lega_brez_zamude || {}).filter(([, [nf, nz]]) => nf > 0 || nz > 0);
    dodaj("vozila brez feeda zamud", lbz.length ? lbz.map(([ime, [nf, nz, vseh]]) =>
      `${ime} ${st(nf)} od ${st(vseh)}${nz ? `, brez zamude ${st(nz)}` : ""}`).join(" · ") : null);
  } else if (kljuc === "derp_lpp") {
    dodaj("vožnje brez voznega reda", nez("lpp"));
  } else if (kljuc === "ovire_sz") {
    dodaj("ovir zdaj", st(z.alerts_active));
    const os = z.ovire_sz;
    if (os && os.ovir != null) {
      dodaj("na strani", `${st(os.ovir)} ovir · novih ${st(os.novih)} · brez vlakov ${st(os.brez_vezi)}`
        + (os.vezi_spremenjenih ? ` · vezi spremenjenih ${st(os.vezi_spremenjenih)}` : ""));
    }
    dodaj("brskalnik", opisBrskalnika((d.stroj || {}).brskalnik));
  } else if (kljuc === "nap" && z.nap) {
    const nm = z.nap;
    if (nm.vozil != null) {
      dodaj("v odgovoru", `${st(nm.vozil)} vozil · pripetih ${st(nm.pripetih)} · brez vožnje ${st(nm.brez_voznje)}`
        + ` · zapisanih ${st(nm.zapisanih)}`);
    }
    if (nm.derp && nm.skupnih) {
      dodaj("ujemanje z derp.si", `skupnih ${st(nm.skupnih)} · ista vožnja ${st(100 * nm.ista_voznja / nm.skupnih)} %`
        + (nm.isti_cas ? ` · odmik ${st(nm.odmik_m, 1)} m` : "")
        + ` · NAP novejši za ${st(nm.prednost_s)} s · samo NAP ${st(nm.samo_nap)} · samo derp ${st(nm.samo_derp)}`);
    }
    const ok = z.odkloni_24h;
    dodaj("izven trase · 24 h", ok ? `${st(ok.odklonov)} odklonov na ${st(ok.vozenj)} vožnjah` : null);
  } else if (kljuc === "zamude_sz") {
    const zs = z.zamude_sz;
    if (zs && zs.vlakov != null) {
      dodaj("v odgovoru", `${st(zs.vlakov)} vlakov · zapisanih ${st(zs.zapisanih)}`
        + ` · pred odhodom ${st(zs.pred_odhodom)} · na cilju ${st(zs.na_cilju)}`
        + (zs.nepripetih ? ` · nepripetih ${st(zs.nepripetih)}` : "")
        + (zs.nazaj ? ` · nazaj zavrnjenih ${st(zs.nazaj)}` : "")
        + (zs.ponastavljenih ? ` · ponastavitev na cilju ${st(zs.ponastavljenih)}` : ""));
      dodaj("zadnja sprememba", zs.spremenjeno_ts ? pred(zs.spremenjeno_ts) : null);
    }
    dodaj("brskalnik", opisBrskalnika((d.stroj || {}).brskalnik));
  } else if (kljuc === "peroni") {
    dodaj("brskalnik", opisBrskalnika((d.stroj || {}).brskalnik));
  } else if (kljuc === "zamude_lpp" && z.zamude_lpp) {
    const zl = z.zamude_lpp;
    dodaj("v obhodu", `oba ${st(zl.oba)} · samo LPP ${st(zl.samo_lpp)} · živih ${st(zl.zivih)}`
      + ` · brez voznega reda ${st(zl.brez_voznega_reda)} · ${st(zl.postaj)} postajališč`);
    dodaj("ujemanje · 24 h", ujemanje(zl.primerjava));
    // Meritev za odločitev, ali LPP-jeve prihode pripenjati tudi brez derp.si.
    const [a, b, c, e] = zl.po_voznem_redu || [0, 0, 0, 0];
    if (a + b + c + e) dodaj("samo po voznem redu", `zadel ${st(a)} · zgrešil ${st(b)} · dvoumno ${st(c)} · brez ${st(e)}`);
  } else if (kljuc === "gtfs_ijpp") {
    const vr = z.vozni_red || {};
    dodaj("znan do", [vr.zeleznica && `vlaki ${datumIso(vr.zeleznica)}`,
      vr.avtobus && `avtobusi ${datumIso(vr.avtobus)}`].filter(Boolean).join(" · ") || null);
  } else if (kljuc === "gtfs_lpp") {
    const vr = z.vozni_red || {};
    dodaj("znan do", vr.lpp ? datumIso(vr.lpp) : null);
  }
  return out;
}

/** Kratko stanje vira za seznam na zavihku Stanje. */
function kratkoVira(v) {
  const dn = v.dnevnik;
  if (!v.vklopljen) return "izklopljen";
  if (v.razlogi.length) return v.razlogi[0];
  if (dn && dn.zaporednih) return `${dn.napaka} (${dn.zaporednih}×)`;
  if (dn && dn.caka) return `čaka: ${dn.caka}`;
  if (dn && dn.uspeh_ts) return `odgovoril ${pred(dn.uspeh_ts)}`;
  if (v.zapisano) return `${ZAPIS_IME[v.kljuc] || "zapis"} ${pred(v.zapisano)}`;
  return v.nit ? "v tem zagonu še ni bral" : "nihče še ni vprašal";
}

function vrsticaKartice(ime, vr, razred = "") {
  return `<div class="adm-vir-v ${razred}"><span>${escapeHtml(ime)}</span><b>${escapeHtml(vr)}</b></div>`;
}

function karticaVira(v, d) {
  const dn = v.dnevnik;
  const razred = v.vklopljen ? v.razred || "" : "je-izklopljen";
  let h = `<article class="adm-vir ${razred}" id="vir-${v.kljuc}">
    <header><span class="adm-pika ${v.razred || ""}"></span><h3>${escapeHtml(v.ime)}</h3>
      <span class="adm-vir-vloga">${escapeHtml(v.vloga)}</span></header>
    <p class="adm-vir-kaj">${escapeHtml(v.kaj)}</p>`;
  if (!v.vklopljen) {
    return `${h}<p class="adm-vir-razlog">Izklopljen v nastavitvah.</p>${nogaVira(v)}</article>`;
  }
  if (v.razlogi.length) {
    h += v.razlogi.map((r) => `<p class="adm-vir-razlog">${escapeHtml(r)}</p>`).join("");
  }
  h += `<div class="adm-vir-vr">`;
  h += vrsticaKartice("ritem", v.ritem);
  if (dn && dn.caka) h += vrsticaKartice("čaka", `${dn.caka} · od ${uraTs(dn.caka_ts)}`, "je-mlacna");
  // Dnevni vir in vir, ki ga bere podproces: stanje iz baze, ne iz tega procesa.
  const izBaze = dn && dn.iz_baze ? " · zapis v bazi" : "";
  h += vrsticaKartice("zadnji odgovor", dn && dn.uspeh_ts
    ? `${dn.iz_baze ? `${uraTs(dn.uspeh_ts)} · ` : ""}${pred(dn.uspeh_ts)}${dn.nespremenjeno ? " · nespremenjen" : ""}`
      + `${dn.ms != null ? ` · ${ms(dn.ms)}` : ""}${dn.bajtov && dn.iz_baze ? ` · ${bajti(dn.bajtov)}` : ""}${izBaze}`
    : v.nit ? "v tem zagonu še nobenega" : "nihče še ni vprašal");
  if (dn && dn.ura && dn.ura.branj) {
    const u = dn.ura;
    h += vrsticaKartice("zadnja ura", `${mn(u.branj, "branje", "branji", "branja", "branj")} · `
      + `${u.napak ? mn(u.napak, "napaka", "napaki", "napake", "napak") : "brez napak"}`
      + ` · mediana ${ms(u.ms_mediana)}${u.bajtov ? ` · ${bajti(u.bajtov)}` : ""}`, u.napak ? "je-mlacna" : "");
  }
  if (v.zapisano) h += vrsticaKartice(ZAPIS_IME[v.kljuc] || "zadnji zapis", `${uraTs(v.zapisano)} · ${pred(v.zapisano)}`);
  if (dn && dn.napaka_ts) {
    h += vrsticaKartice("zadnja napaka", `${uraTs(dn.napaka_ts)} · ${dn.napaka}${dn.zaporednih ? ` · ${dn.zaporednih}× zapored` : ""}${izBaze}`,
      dn.zaporednih ? "je-slaba" : "");
  }
  if (dn && dn.opomba) h += vrsticaKartice("opomba", dn.opomba);
  if (v.nit) h += vrsticaKartice("nit", v.nit_tece ? `${v.nit} teče` : `${v.nit} NE TEČE`, v.nit_tece ? "" : "je-slaba");
  for (const [ime, vr] of podrobnostiVira(v.kljuc, d)) h += vrsticaKartice(ime, vr);
  const p = preverba && preverba.viri && preverba.viri.find((x) => x.kljuc === v.kljuc);
  if (p) h += vrsticaKartice(`preverjeno ob ${uraTs(preverba.ts)}`, p.opis, p.ok ? "je-dobra" : "je-slaba");
  h += `</div>`;
  if (v.razred === "je-slaba" || v.razred === "je-mlacna" || (dn && dn.zaporednih)) {
    h += `<p class="adm-vir-ukrep"><b>Kaj storiti.</b> ${escapeHtml(v.ukrep)}</p>`;
  }
  return `${h}${nogaVira(v)}</article>`;
}

function nogaVira(v) {
  let kratko = v.naslov;
  try { const u = new URL(v.naslov); kratko = u.host + (u.pathname.length > 1 ? u.pathname : ""); } catch (e) { /* ni naslov */ }
  return `<footer class="adm-vir-noga">
    <span>${escapeHtml(v.izvor)} · licenca ${escapeHtml(v.licenca)}</span>
    <a href="${escapeHtml(v.naslov)}" target="_blank" rel="noopener noreferrer" title="${escapeHtml(v.naslov)}">${escapeHtml(kratko)}</a>
  </footer>`;
}

/** Najhujše stanje in vsi razlogi: za piko v glavi, ploščico in pas na vrhu. */
function skupnoZdravje(d) {
  const r = Object.values(d.razredi || {});
  const razlogi = Object.entries(d.razlogi || {})
    .map(([k, besedilo]) => ({ k, besedilo, razred: (d.razredi || {})[k] }))
    .sort((a, b) => RANG[b.razred] - RANG[a.razred]);
  const slabih = razlogi.filter((x) => x.razred === "je-slaba").length;
  const stoji = slabih <= 1 ? "nekaj stoji" : slabih === 2 ? "dve stvari stojita"
    : slabih <= 4 ? `${slabih} stvari stojijo` : `${slabih} stvari stoji`;
  if (r.includes("je-slaba")) return ["je-slaba", stoji, razlogi];
  if (r.includes("je-mlacna")) return ["je-mlacna", "opozorilo", razlogi];
  return ["je-dobra", "vse dela", razlogi];
}

function pasZdravja(d) {
  const [raz, bes, razlogi] = skupnoZdravje(d);
  let p = "";
  if (preverba && preverba.tece) p = `<p class="adm-pas-prev">Preverjam vse vire hkrati … do 30 s.</p>`;
  else if (preverba && preverba.napaka) p = `<p class="adm-pas-prev je-slaba">Preverjanja ni bilo mogoče izvesti — ${escapeHtml(preverba.napaka)}</p>`;
  else if (preverba) {
    p = `<p class="adm-pas-prev"><b>Preverjeno ob ${uraTs(preverba.ts)}.</b> ${escapeHtml(preverba.sklep)}
      <span class="${preverba.kontrola.ok ? "" : "je-slaba"}">Kontrola: ${escapeHtml(preverba.kontrola.opis)}.</span></p>`;
  }
  return `<section class="adm-plosca s12 adm-pas ${raz}">
    <div class="adm-pas-glava"><span class="adm-pika ${raz}"></span><h2>${escapeHtml(bes[0].toUpperCase() + bes.slice(1))}</h2>
      <button type="button" class="btn adm-gumb" id="preveri-vire" ${preverba && preverba.tece ? "disabled" : ""}>Preveri vire zdaj</button></div>
    ${razlogi.length ? `<ul class="adm-razlogi">${razlogi.map((x) =>
      `<li class="${x.razred}"><span class="adm-pika ${x.razred}"></span>${escapeHtml(x.besedilo)}</li>`).join("")}</ul>`
    : `<p class="adm-pod">Vsi viri odgovarjajo, niti tečejo, disk in vozni red sta v redu.</p>`}
    ${p}
    <p class="adm-pod">Rdeče, ki traja 10 min, gre po pošti (${{
      tece: "vklopljeno", stoji: "<b class=\"je-slaba\">nit pošte ne teče</b> — ponovni zagon strežnika",
      ni: "<b>ni nastavljeno</b> — datoteka <code>.opozorila</code>",
    }[(d.stroj || {}).posta] || "—"}); rumeno samo tu.</p>
  </section>`;
}

/** Izid zajema: ali podatki res pridejo v bazo, ne glede na vir. */
function vrsticeZajema(d) {
  const z = d.zdravje || {}, r = d.razredi || {}, mreze = z.by_network || {};
  const zel = mreze.zeleznica || {}, bus = mreze.avtobus || {}, sen = z.senca || {};
  const nez = Object.entries(z.rt_neznanih || {});
  const lbz = Object.entries(z.lega_brez_zamude || {}).filter(([, [nf, nz]]) => nf > 0 || nz > 0);
  return [
    ["zadnja zamuda v bazi", pred(z.last_feed_ts), r.feed],
    ["vlaki · zadnji zapis", pred(zel.last_feed_ts), r.zeleznica],
    ["avtobusi · zadnji zapis", pred(bus.last_feed_ts), r.avtobus],
    ["vožnje brez voznega reda",
      nez.length ? nez.map(([vir, [n, vseh]]) => `${vir.toUpperCase()} ${st(n)} od ${st(vseh)}`).join(" · ") : "—", r.neznane],
    ["vozila brez feeda zamud", lbz.length ? lbz.map(([ime, [nf, nz, vseh]]) =>
      `${ime} ${st(nf)} od ${st(vseh)}${nz ? `, brez zamude ${st(nz)}` : ""}`).join(" · ") : "—", r.lega_brez_zamude],
    ["vozil z lego", st(z.vehicles_with_gps)],
    ["vlakov / meritev", `${st(zel.trips)} / ${st(zel.runs)}`],
    ["avtobusov / meritev", `${st(bus.trips)} / ${st(bus.runs)}`],
    ["senca napovedi", sen.vrstic ? `${st(100 * sen.razresenih / sen.vrstic, 1)} % razrešenih od ${st(sen.vrstic)}` : "—"],
    ["zajetih dni", st(z.days_covered)],
  ];
}

function vrsticeStroja(d) {
  const z = d.zdravje || {}, m = d.stroj || {}, r = d.razredi || {};
  const disk = m.disk_vseh ? m.disk_prostih / m.disk_vseh : null;
  const zive = m.niti || [];
  const pricakovane = Object.keys(m.pricakovane_niti || {});
  const manjka = pricakovane.filter((n) => !zive.includes(n));
  const nase = zive.filter((n) => n.startsWith("kajros-")).map((n) => n.slice(7));
  return [
    ["prostora na disku", disk == null ? "—" : `${bajti(m.disk_prostih)} (${st(100 * disk)} %)`, r.disk],
    ["WAL", bajti(m.wal_bajtov), r.wal],
    ["baza", bajti(z.db_bytes)],
    ["pomnilnik procesa", bajti(m.rss_bajtov)],
    ["strežnik teče", `${trajanje(m.teka_s)} · od ${uraTs(m.zagon_ts)}`],
    ["niti zajema", !pricakovane.length ? "zajem izklopljen" : manjka.length ? `ne teče: ${manjka.join(", ")}`
      : `teče vseh ${st(pricakovane.length)}`, manjka.length ? "je-slaba" : ""],
    ["vse niti procesa", `${st(zive.length)} · ${nase.join(", ")}`],
    ["brskalnik za potniski.sz.si", opisBrskalnika(m.brskalnik)],
    ["različica", m.razlicica || "—"],
  ];
}

function tabelaVrstic(vrstice) {
  return `<div class="adm-zdr">${vrstice.map(([ime, vr, raz]) =>
    `<div><span class="adm-pika ${raz || ""}"></span><span class="ime">${escapeHtml(ime)}</span>
      <span class="vr">${escapeHtml(vr)}</span></div>`).join("")}</div>`;
}

function blokDnevnika(d) {
  const dn = d.dnevnik || {};
  const imena = Object.fromEntries(((d.viri || {}).seznam || []).map((v) => [v.kljuc, v.ime]));
  const dogodki = (dn.dogodki || []).length
    ? `<ul class="adm-dogodki">${dn.dogodki.map((e) => `<li class="${e.ok ? "je-dobra" : "je-slaba"}">
        <time>${uraTs(e.ts)}</time><b>${escapeHtml(imena[e.kljuc] || e.kljuc)}</b> ${escapeHtml(e.besedilo)}</li>`).join("")}</ul>`
    : prazno("od zagona noben vir ni izpadel");
  const vrstice = (dn.vrstice || []).slice().reverse();
  const dnevnik = vrstice.length
    ? `<ol class="adm-dnevnik">${vrstice.map((v) => `<li><time>${uraTs(v.ts)}</time>${escapeHtml(v.besedilo)}</li>`).join("")}</ol>`
    : prazno("prazen");
  return `<div class="adm-dn-mreza"><div><h3 class="adm-mali">Izpadi in vrnitve virov</h3>${dogodki}</div>
    <div><h3 class="adm-mali">Dnevnik strežnika · najnovejše zgoraj</h3>${dnevnik}</div></div>`;
}

function viriZavihek(d) {
  const vv = d.viri || { skupine: [], seznam: [] };
  let h = `<div class="adm-mreza">${pasZdravja(d)}`;
  for (const [kljuc, ime] of vv.skupine) {
    const viri = vv.seznam.filter((v) => v.skupina === kljuc);
    if (!viri.length) continue;
    h += `<section class="s12 adm-skupina"><h2 class="adm-skupina-ime">${escapeHtml(ime)}</h2>
      <div class="adm-viri">${viri.map((v) => karticaVira(v, d)).join("")}</div></section>`;
  }
  h += plosca("s6", "Zajem", "kaj res pride v bazo, ne glede na vir", tabelaVrstic(vrsticeZajema(d)));
  h += plosca("s6", "Stroj", "tisto, česar baza sama o sebi ne ve", tabelaVrstic(vrsticeStroja(d)));
  h += plosca("s12", "Dnevnik", "od zagona strežnika · v pomnilniku, ne v bazi", blokDnevnika(d));
  return `${h}</div>`;
}

/** Razlogi pod naslovom plošče Viri na zavihku Stanje. */
function razlogiKratko(d) {
  const [, , razlogi] = skupnoZdravje(d);
  return razlogi.length ? razlogi.map((x) => escapeHtml(x.besedilo)).join(" · ") : "Vse dela.";
}

/** Viri na zavihku Stanje: ena vrstica na vir, klik odpre zavihek Viri. */
function blokViriKratko(d) {
  const seznam = (d.viri || {}).seznam || [];
  if (!seznam.length) return prazno("ni podatka");
  return `<div class="adm-viri-kratko">${seznam.map((v) => `
    <a href="#viri" data-vir="${escapeHtml(v.kljuc)}" class="${v.vklopljen ? "" : "je-izklopljen"}">
      <span class="adm-pika ${v.razred || ""}"></span><span class="ime">${escapeHtml(v.ime)}</span>
      <span class="vr">${escapeHtml(kratkoVira(v))}</span></a>`).join("")}</div>`;
}

async function preveriVire() {
  preverba = { tece: true };
  risi();
  try {
    const r = await fetch("/admin/viri/preveri", { credentials: "same-origin" });
    if (!r.ok) throw new Error(`strežnik: ${r.status}`);
    preverba = await r.json();
  } catch (e) {
    preverba = { napaka: e.message };
  }
  risi();
}

/** Ogledi po urah za en dan; ure, ki še niso bile, izpustimo. */
function poUrah(d, dan) {
  const ure = new Map(((d.razrezi || {}).ura || []).map((u) => [Number(u.kljuc), u.ogledov]));
  const do_ = dan === danes() ? zdajUra() : 23;
  const v = Array.from({ length: 24 }, (_, h) => (h > do_ ? undefined : ure.get(h) || 0));
  return {
    v, oznake: v.map((_, h) => (h % 3 ? "" : `${h}h`)),
    tip: (h) => `<b>${h}:00–${h + 1}:00</b><br>${st(v[h])} ogledov`,
  };
}

// ------------------------------------------------------------------ stanje

let zadnji = null;          // odgovor za današnji dan -- Stanje, Sporočila, zdravje
const danes = () => (zadnji ? zadnji.danes_dan : vIso(new Date()));
const prviDan = () => (zadnji && zadnji.prvi_dan) || danes();

function zadnjih30(d) {
  const po = new Map((d.zadnjih30 || []).map((r) => [r.dan, r]));
  return vseDni(dodaj(d.danes_dan, -29), d.danes_dan).map((dan) => po.get(dan) || { dan, prazen: true });
}

function stanje(d) {
  const t = d.danes;
  const mes = zadnjih30(d);
  const vceraj = mes[28];
  const strojev = t.botov + t.brez_js;
  const naj = pocasne(d, 1)[0];
  const pu = poUrah(d, d.danes_dan);
  const [zR, zB] = skupnoZdravje(d);
  return `<div class="adm-mreza">
    <div class="adm-kpi">
      ${ploscica(st(t.ljudi), "ljudi danes", vceraj.prazen ? "včeraj ni podatka" : `včeraj cel dan ${st(vceraj.ljudi)}`, "je-poudarek")}
      ${ploscica(st(t.ogledov), "ogledov strani", t.ljudi ? `${st(t.ogledov / t.ljudi, 1)} na človeka` : "")}
      ${ploscica(st(t.zahtev), "zahtev", "vse, tudi API in stroji")}
      ${ploscica(`${st(strojev + t.ljudi ? 100 * strojev / (strojev + t.ljudi) : 0)} %`, "strojev",
        `${st(t.botov)} botov · ${st(t.brez_js)} brez JS`)}
      ${ploscica(naj ? `<span class="${msRazred(naj.ms_naj)}">${ms(naj.ms_naj)}</span>` : "—",
        "najpočasneje danes", naj ? escapeHtml(naj.pot) : "")}
      <a class="adm-k adm-k-povezava" href="#viri"><div class="adm-k-v"><span class="adm-k-stanje"><span class="adm-pika ${zR}"></span>${
        zR === "je-slaba" ? "stoji" : zR === "je-mlacna" ? "opozorilo" : "dela"}</span></div>
        <div class="adm-k-i">zajem in viri →</div><div class="adm-k-d">${escapeHtml(zB)} · feed ${pred(d.zdravje && d.zdravje.last_feed_ts)}</div></a>
    </div>
    ${plosca("s8", "Zadnjih 30 dni", "ljudi na dan · šrafirano: štetja še ni bilo · klik odpre dan",
      `<div id="graf-30">${stolpci(mes.map((r) => (r.prazen ? null : r.ljudi)), {
        visina: 210, poudari: 29, klik: true,
        oznake: mes.map((r, i) => (i % 5 === 4 ? kratki(r.dan) : "")),
        tip: (i) => mes[i].prazen ? `${dolgi(mes[i].dan)}<br>ni podatka`
          : `<b>${dolgi(mes[i].dan)}</b><br>${st(mes[i].ljudi)} ljudi · ${st(mes[i].ogledov)} ogledov`,
      })}</div>`, "")}
    ${plosca("s4", "Danes po urah", "ogledov", stolpci(pu.v, { visina: 210, oznake: pu.oznake, tip: pu.tip, poudari: zdajUra() }), "")}
    ${plosca("s8", "Aplikacija · zadnjih 30 dni", "na dan · klik odpre dan",
      grafiAplikacije(d, d.zadnjih30 || [], mes.map((r, i) => ({
        ime: dolgi(r.dan), dni: [r.dan], oznaka: i % 5 === 4 ? kratki(r.dan) : "" }))), podAplikacije({ ...d, od: mes[0].dan }))}
    ${plosca("s4", "Aplikacija danes", "za Android",
      blokAplikacije(d, { app: t.app, ozadje: t.app_ozadje, prenosov: t.prenosov }, false),
      "„Odprlo“ je okno aplikacije; pripomoček in budilka tečeta tudi brez tega.")}
    ${plosca("s4", "Katere strani", "danes · ljudi", blokStrani(d, 10), "Številka desno so vsi ogledi, tudi ponovni.")}
    ${plosca("s8", "Kaj je bilo počasno", "danes · po najdaljši zahtevi", tabelaPocasnih(d, 8),
      "Čas v aplikaciji brez omrežja. Rdeče je nad 5 s — tam potnik odneha. p95 je razred, ne točna vrednost.")}
    ${plosca("s4", "S čim in od kod", "danes · ogledi", blokNaprav(d))}
    ${plosca("s8", "Viri", "klik odpre zavihek Viri", blokViriKratko(d),
      razlogiKratko(d))}
    ${plosca("s6", "Od kod pridejo", "danes · ogledi", blokVirov(d), "Z iskalnika, AI ali omrežja; naravnost se ne šteje.")}
    ${plosca("s6", "Roboti", "danes · zahtev · desno strani", blokRobotov(d), "Po predstavitvi, ne preverjeno.")}
    ${plosca("s6", "Podpora", "danes · ljudi", blokPodpore(d), "Klik ni donacija: plačilo teče pri ponudniku.")}
  </div>`;
}

// ------------------------------------------------------------------ zgodovina

let izbor = { vrsta: "dan", sidro: null };
let obdobje = null;          // odgovor za izbrano obdobje

/** Glavni graf obdobja: dan po urah, leto po mesecih, ostalo po dnevih. */
function grafObdobja(o) {
  if (izbor.vrsta === "dan") return { naslov: "Po urah", enota: "ogledov na uro", ...poUrah(o, o.od) };
  const po = new Map(o.po_dnevih.map((r) => [r.dan, r]));
  if (izbor.vrsta === "leto") {
    const leto = izIso(o.od).getFullYear();
    const v = MESECI.map((_, k) => (vIso(new Date(leto, k, 1)) > danes() ? undefined : null));
    for (const r of o.po_dnevih) { const k = izIso(r.dan).getMonth(); v[k] = (v[k] || 0) + r.ljudi; }
    return {
      naslov: "Po mesecih", enota: "obiskov na mesec (vsota dnevnih)", v,
      oznake: MESECI.map((m) => m.slice(0, 3)),
      tip: (i) => v[i] == null ? `${MESECI[i]}<br>ni podatka` : `<b>${MESECI[i]}</b><br>${st(v[i])} obiskov`,
    };
  }
  const dni = vseDni(o.od, o.do);
  const v = dni.map((dan) => (dan > danes() ? undefined : po.has(dan) ? po.get(dan).ljudi : null));
  const redko = dni.length > 14;
  const korak = dni.length > 120 ? 30 : 7;
  return {
    naslov: "Po dnevih", enota: "ljudi na dan · klik odpre dan", v, dni, klik: true,
    oznake: dni.map((dan, i) => (!redko || i % korak === 0 ? kratki(dan) : "")),
    tip: (i) => {
      const r = po.get(dni[i]);
      return r ? `<b>${dolgi(dni[i])}</b><br>${st(r.ljudi)} ljudi · ${st(r.ogledov)} ogledov` : `${dolgi(dni[i])}<br>ni podatka`;
    },
  };
}

function glavaZgodovine() {
  const { vrsta: v, sidro } = izbor;
  const naprej = premakni(v, sidro, 1);
  return `<div class="adm-hist">
    <div class="mode-switch" id="vrste">${Object.entries(OBDOBJA).map(([k, n]) =>
      `<button type="button" data-v="${k}" aria-pressed="${k === v}">${n}</button>`).join("")}</div>
    <div class="adm-korak">
      <button type="button" id="nazaj" ${v === "vse" ? "disabled" : ""} aria-label="prejšnje">‹</button>
      <button type="button" id="na-danes">danes</button>
      <button type="button" id="naprej" ${v === "vse" || meje(v, naprej)[0] > danes() ? "disabled" : ""} aria-label="naslednje">›</button>
    </div>
    <input type="date" class="adm-datum" id="datum" value="${sidro}" min="${prviDan()}" max="${danes()}">
    <h1>${escapeHtml(naslovObdobja(v, sidro))}</h1>
    <span class="adm-opomba">${obdobje ? `${st(obdobje.skupaj.dni)} od ${st(vseDni(obdobje.od, obdobje.do < danes() ? obdobje.do : danes()).length)} dni s podatki · ` : ""}štetje od ${escapeHtml(dolgi(prviDan()))}</span>
  </div>`;
}

function zgodovina() {
  const glava = glavaZgodovine();
  const o = obdobje;
  if (!o) return glava + prazno("nalagam …");
  if (!o.skupaj.dni) {
    return glava + `<div class="adm-plosca">${prazno(`Za to obdobje ni podatkov. Štetje obiska teče od ${dolgi(prviDan())}.`)}</div>`;
  }
  const s = o.skupaj, p = o.prej;
  const enDan = izbor.vrsta === "dan";
  const g = grafObdobja(o);
  const naj = pocasne(o, 1)[0];
  return glava + `<div class="adm-mreza">
    <div class="adm-kpi">
      ${ploscica(st(s.ljudi_vsota), enDan ? "različnih ljudi" : "obiskov",
        `${enDan ? "" : "vsota dnevnih · "}${razlika(s.ljudi_vsota, p.ljudi_vsota, p.dni)}`, "je-poudarek")}
      ${ploscica(st(s.ogledov), "ogledov strani", razlika(s.ogledov, p.ogledov, p.dni))}
      ${ploscica(st(s.ljudi_vsota ? s.ogledov / s.ljudi_vsota : 0, 1), "ogledov na obisk", "")}
      ${ploscica(st(s.zahtev), "zahtev", `${st(s.napak5)} napak strežnika · ${st(s.napak4)} × 4xx`)}
      ${ploscica(st(s.botov_vsota + s.brez_js_vsota), "strojev", `${st(s.botov_vsota)} botov · ${st(s.brez_js_vsota)} brez JS`)}
      ${ploscica(naj ? `<span class="${msRazred(naj.ms_naj)}">${ms(naj.ms_naj)}</span>` : "—",
        "najdaljša zahteva", naj ? escapeHtml(naj.pot) : "")}
    </div>
    ${plosca("s12", g.naslov, g.enota, `<div id="graf-obdobje">${stolpci(g.v, { visina: 220, oznake: g.oznake, tip: g.tip, klik: g.klik })}</div>`, "")}
    ${plosca("s4", "Katere strani", "ljudi · desno vsi ogledi", blokStrani(o, 12))}
    ${plosca("s5", "Počasno", "po najdaljši zahtevi", tabelaPocasnih(o, 9))}
    ${plosca("s3", "S čim in od kod", "ogledi", blokNaprav(o))}
    ${plosca("s6", "Od kod pridejo", "ogledi", blokVirov(o), "Z iskalnika, AI ali omrežja; naravnost se ne šteje.")}
    ${plosca("s6", "Roboti", "zahtev · desno strani", blokRobotov(o), "Po predstavitvi, ne preverjeno.")}
    ${plosca(enDan ? "s12" : "s4", "Podpora", "ljudi", blokPodpore(o), "Klik ni donacija: plačilo teče pri ponudniku.")}
    ${enDan ? "" : plosca("s8", "Od kod po dnevih", "ogledi z znanega vira", tabelaVirovPoDnevih(o), "Kaj je sprožilo vrh. Naravnost se ne šteje.")}
    ${enDan ? "" : plosca("s8", "Aplikacija", izbor.vrsta === "leto" ? "po mesecih" : "po dnevih",
      grafiAplikacije(o, o.po_dnevih, vedraObdobja(o)), podAplikacije(o))}
    ${plosca(enDan ? "s12" : "s4", "Aplikacija za Android", enDan ? "ta dan" : "vsota obdobja",
      blokAplikacije(o, { app: s.app_vsota, ozadje: s.app_ozadje_vsota, prenosov: s.prenosov }, !enDan),
      enDan ? podAplikacije(o) : "Ista naprava šteje enkrat na dan.")}
  </div>`;
}

async function naloziObdobje() {
  const [od, do_] = meje(izbor.vrsta, izbor.sidro);
  const kljuc = `${od}/${do_}`;
  // Današnji dan že imamo: isti odgovor kot Stanje, brez drugega klica.
  if (od === danes() && do_ === danes() && zadnji) { obdobje = zadnji; return; }
  const d = await podatki(`?od=${od}&do=${do_}`);
  // Med čakanjem je lahko skrbnik že kliknil naprej; star odgovor zavržemo.
  if (kljuc === meje(izbor.vrsta, izbor.sidro).join("/")) obdobje = d;
}

// ------------------------------------------------------------------ sporočila

/** Nabiralnik. Edino na tej strani, kar čaka na odgovor človeka. */
function sporocila(d) {
  const s = d.sporocila || {};
  let h = `<section class="adm-plosca"><h2>Sporočila <small>iz obrazca na /stik · odgovarja se ročno iz poštnega odjemalca</small></h2><p class="adm-pod"></p>`;
  if (!s.vklopljeno) return `${h}${prazno("obrazec za stik je izklopljen (KAJROS_STIK_OBRAZEC=0)")}</section>`;
  if (!s.seznam || !s.seznam.length) return `${h}${prazno("nobenega sporočila še ni")}</section>`;
  // Besedilo je vpisal neznanec: gre skozi `escapeHtml` in v `<p>`, nikoli
  // v `innerHTML` kot je. Prelome vrstic ohrani CSS (`white-space`), ne
  // pretvorba v `<br>` -- ta bi bila druga pot, po kateri bi lahko kaj ušlo.
  h += `<div class="adm-sporocila" id="sporocila">${s.seznam.map((v) => `
    <article class="adm-sporocilo${v.prebrano ? " je-prebrano" : ""}" data-id="${v.id}">
      <header class="adm-sp-glava">
        ${v.email
          ? `<a class="adm-sp-od" href="mailto:${encodeURIComponent(v.email)}">${escapeHtml(v.email)}</a>`
          : `<span class="adm-sp-od">anonimno · brez odgovora</span>`}
        <span class="adm-sp-kdaj">${escapeHtml(v.prispelo.slice(0, 16).replace("T", " "))}</span>
        <span class="adm-sp-kje">${escapeHtml([v.drzava, v.naprava].filter(Boolean).join(" · "))}</span>
        <button type="button" class="adm-sp-gumb" data-prebrano="${v.prebrano ? 0 : 1}">
          ${v.prebrano ? "označi kot novo" : "prebrano"}
        </button>
        <button type="button" class="adm-sp-gumb adm-sp-brisi" data-brisi="1">izbriši</button>
      </header>
      <p class="adm-sp-telo">${escapeHtml(v.besedilo)}</p>
    </article>`).join("")}</div>`;
  return `${h}</section>`;
}

async function obSporocilu(e) {
  const gumb = e.target.closest(".adm-sp-gumb");
  if (!gumb) return;
  const id = gumb.closest(".adm-sporocilo").dataset.id;
  // Brisanje je nepovratno in gumb stoji tik ob „prebrano" -- vprašanje je
  // tu zato, ker je zgrešen klik na telefonu cena celega sporočila.
  if (gumb.dataset.brisi && !confirm("Izbrišem to sporočilo? Tega ni mogoče razveljaviti.")) return;
  gumb.disabled = true;
  try {
    await fetch(`/admin/sporocila/${id}`, {
      method: "POST", credentials: "same-origin",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: gumb.dataset.brisi ? "akcija=brisi" : `prebrano=${gumb.dataset.prebrano}`,
    });
    await osvezi();
  } finally {
    gumb.disabled = false;
  }
}

// ------------------------------------------------------------------ obvestila

const OBV_KOMU = [["", "vsem"], ["zeleznica", "vlaki"], ["avtobus", "avtobusi"]];
// Rok od zdaj. „noč“ = 3:00, ko se konča obratovalni dan: „danes je vozni
// red pomanjkljiv“ jutri ne velja več, ob polnoči pa še vozi zadnji vlak.
const OBV_ROKI = [["noc", "do 3:00"], ["24", "24 ur"], ["72", "3 dni"], ["168", "7 dni"]];

/** Osnutek preživi osvežitev: pregled vsako minuto nariše zavihek znova. */
let obvOsnutek = { besedilo: "", omrezje: "", do: "" };

function obvRok(kaj) {
  const d = new Date();
  if (kaj === "noc") {
    if (d.getHours() >= 3) d.setDate(d.getDate() + 1);
    d.setHours(3, 0, 0, 0);
  } else {
    d.setTime(d.getTime() + Number(kaj) * 3600000);
    d.setSeconds(0, 0);
  }
  const dve = (n) => String(n).padStart(2, "0");
  return `${vIso(d)}T${dve(d.getHours())}:${dve(d.getMinutes())}`;
}

function obvCas(iso) { return `${dayLabel(iso.slice(0, 10))} ob ${hhmm(iso)}`; }

function obvObrazec(o) {
  if (!obvOsnutek.do) obvOsnutek.do = obvRok("noc");
  const gumbi = (ime, izbire, izbrana) => izbire.map(([v, n]) =>
    `<button type="button" data-${ime}="${v}" aria-pressed="${v === izbrana}">${n}</button>`).join("");
  return `<section class="adm-plosca adm-obv">
    <h2>Novo obvestilo <small>na vrhu strani, dokler ne poteče ali ga potnik ne zapre</small></h2>
    <p class="adm-pod">Na straneh vlakov samo „vsem“ in „vlaki“, na avtobusnih „vsem“ in „avtobusi“;
      domača stran, zemljevid in pot pokažejo vsa. Največ ${o.najdlje_dni} dni.</p>
    <form id="obv-obrazec" novalidate>
      <textarea id="obv-besedilo" rows="3" maxlength="${o.najdaljse}"
        placeholder="npr. Vozni red avtobusov je danes pomanjkljiv — nekaterih voženj ni.">${escapeHtml(obvOsnutek.besedilo)}</textarea>
      <div class="adm-obv-vrsta"><span>Komu</span>
        <div class="mode-switch" id="obv-komu">${gumbi("komu", OBV_KOMU, obvOsnutek.omrezje)}</div></div>
      <div class="adm-obv-vrsta"><span>Velja do</span>
        <div class="mode-switch" id="obv-roki">${gumbi("rok", OBV_ROKI, "")}</div>
        <input type="datetime-local" id="obv-do" class="adm-datum" value="${obvOsnutek.do}"></div>
      <div class="adm-obv-dno">
        <span class="adm-obv-stevec" id="obv-stevec">${obvOsnutek.besedilo.length} / ${o.najdaljse}</span>
        <span class="adm-obv-izid" id="obv-izid" role="status"></span>
        <button type="submit" class="btn" id="obv-objavi">Objavi</button>
      </div>
    </form>
  </section>
  <section class="adm-plosca adm-obv" id="obv-samodejna-plosca" hidden><h2>Samodejna <small>ta hip na straneh · napisali so jih podatki, ne skrbnik</small></h2>
    <p class="adm-pod">Nastane, ko po voznem redu vozijo vsaj 3 vožnje, podatka o njih pa ni 20 min;
      izgine samo, ko podatki spet pridejo. Umakniti se ga ne da.</p>
    <div id="obv-samodejna" class="adm-sporocila"></div></section>
  <section class="adm-plosca adm-obv"><h2>Objavljena <small>umaknjena in potekla ostanejo, da se ve, kaj je bilo rečeno</small></h2>
    <div id="obv-seznam" class="adm-sporocila"></div></section>`;
}

function obvSeznam(seznam) {
  if (!seznam.length) return prazno("obvestil še ni bilo");
  // Besedilo je pisal skrbnik, a gre vseeno skozi `escapeHtml`: pregled ne
  // sme zaupati ničemur, kar pride iz baze.
  return seznam.map((v) => `
    <article class="adm-sporocilo adm-obvestilo${v.velja ? "" : " je-prebrano"}" data-id="${v.id}">
      <header class="adm-sp-glava">
        <span class="adm-sp-od">${v.velja ? `velja do ${obvCas(v.velja_do)}` : `poteklo ${obvCas(v.velja_do)}`}</span>
        <span class="adm-sp-kje">${v.omrezje === "zeleznica" ? "vlaki" : v.omrezje === "avtobus" ? "avtobusi" : "vsem"}
          · objavljeno ${obvCas(v.objavljeno)}</span>
        ${v.velja
          ? `<button type="button" class="adm-sp-gumb" data-akcija="umakni">umakni</button>`
          : `<button type="button" class="adm-sp-gumb adm-sp-brisi" data-akcija="brisi">izbriši</button>`}
      </header>
      <p class="adm-sp-telo">${escapeHtml(v.besedilo)}</p>
    </article>`).join("");
}

async function obvPosli(polja) {
  const r = await fetch("/admin/obvestila", {
    method: "POST", credentials: "same-origin",
    headers: { "Content-Type": "application/x-www-form-urlencoded", Accept: "application/json" },
    body: new URLSearchParams(polja).toString(),
  });
  if (r.ok) return r.json();
  let razlog = `strežnik: ${r.status}`;
  try { razlog = (await r.json()).detail || razlog; } catch (e) { /* ni JSON */ }
  throw new Error(razlog);
}

function obvPovezi(o) {
  const besedilo = el("obv-besedilo");
  besedilo.addEventListener("input", () => {
    obvOsnutek.besedilo = besedilo.value;
    el("obv-stevec").textContent = `${besedilo.value.length} / ${o.najdaljse}`;
  });
  el("obv-do").addEventListener("change", (e) => { obvOsnutek.do = e.target.value; });
  el("obv-komu").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-komu]");
    if (!b) return;
    obvOsnutek.omrezje = b.dataset.komu;
    el("obv-komu").querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", x === b));
  });
  el("obv-roki").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-rok]");
    if (b) el("obv-do").value = obvOsnutek.do = obvRok(b.dataset.rok);
  });
  el("obv-obrazec").addEventListener("submit", async (e) => {
    e.preventDefault();
    const gumb = el("obv-objavi");
    gumb.disabled = true;
    el("obv-izid").textContent = "";
    try {
      await obvPosli({ akcija: "objavi", besedilo: obvOsnutek.besedilo,
                       omrezje: obvOsnutek.omrezje, do: el("obv-do").value });
      obvOsnutek = { besedilo: "", omrezje: "", do: "" };
      el("vsebina").innerHTML = "";          // obrazec nastane znova, prazen
      await osvezi();
      el("obv-izid").textContent = "Objavljeno.";
    } catch (err) {
      el("obv-izid").textContent = err.message;
      el("obv-izid").classList.add("je-napaka");
    } finally {
      gumb.disabled = false;
    }
  });
  el("obv-seznam").addEventListener("click", async (e) => {
    const gumb = e.target.closest("button[data-akcija]");
    if (!gumb) return;
    const akcija = gumb.dataset.akcija;
    if (akcija === "umakni" && !confirm("Umaknem obvestilo? Potniki ga ne bodo več videli.")) return;
    if (akcija === "brisi" && !confirm("Izbrišem obvestilo iz seznama? Tega ni mogoče razveljaviti.")) return;
    gumb.disabled = true;
    try {
      await obvPosli({ akcija, id: gumb.closest(".adm-obvestilo").dataset.id });
      await osvezi();
    } catch (err) {
      alert(err.message);
      gumb.disabled = false;
    }
  });
}

/** Obrazec nastane enkrat in ostane: osvežitev nariše samo seznam, sicer bi
 *  skrbniku sredi pisanja izginil kazalec. */
function obvestilaRisi(v, d) {
  const o = d.obvestila || { seznam: [], najdaljse: 280, najdlje_dni: 30 };
  if (!el("obv-obrazec")) {
    v.innerHTML = obvObrazec(o);
    obvPovezi(o);
  }
  el("obv-seznam").innerHTML = obvSeznam(o.seznam);
  const sam = o.samodejna || [];
  el("obv-samodejna-plosca").hidden = !sam.length;
  el("obv-samodejna").innerHTML = sam.map((v) => `
    <article class="adm-sporocilo adm-obvestilo">
      <header class="adm-sp-glava"><span class="adm-sp-od">velja, dokler podatkov ni</span>
        <span class="adm-sp-kje">${v.omrezje === "zeleznica" ? "vlaki" : "avtobusi"}</span></header>
      <p class="adm-sp-telo">${escapeHtml(v.besedilo)}</p></article>`).join("");
}

// ------------------------------------------------------------------ noga

function noga(d) {
  const preliv = d.preliv
    ? ` <strong>Števci so se enkrat prelili</strong> (${escapeHtml(d.preliv.slice(0, 16))}) —
        nekdo je preiskoval izmišljene naslove in del zahtev tistega obhoda ni štet.`
    : "";
  el("adm-noga").innerHTML = `
    IP se ne shrani nikoli: obiskovalec je zgoščena vrednost s soljo, ki se ob
    polnoči zavrže. Zato <strong>različnih ljudi čez več dni ni mogoče izračunati</strong>
    — „obiskov" nad enim dnem isto osebo šteje enkrat na dan. Ista naprava na
    drugem omrežju (Wi-Fi ↔ mobilni podatki) je nov obiskovalec.
    <strong>Človek je, kdor je stran pognal</strong>: brskalnik, ki jo samo prenese
    in ne vpraša po podatkih, je štet kot stroj brez JS${d.js_od
      ? ` (od ${escapeHtml(dolgi(d.js_od))}; prej je štel vsak brskalnik)` : ""}.
    Števci gredo v bazo vsakih ${d.stroj ? d.stroj.obisk_od : 60} s.${preliv}`;
}

// ------------------------------------------------------------------ usmerjanje

/** `#zgodovina/teden/2026-09-14` -- stanje je v naslovu, da ga ohrani osvežitev. */
function preberiNaslov() {
  const [zav, v, d] = location.hash.slice(1).split("/");
  const zavihek = ["stanje", "viri", "zgodovina", "sporocila", "obvestila", "deljenje"].includes(zav) ? zav : "stanje";
  if (zavihek === "zgodovina") {
    izbor = {
      vrsta: OBDOBJA[v] ? v : "dan",
      sidro: /^\d{4}-\d{2}-\d{2}$/.test(d || "") ? d : danes(),
    };
  }
  return zavihek;
}

function pojdi(vrsta, sidro) {
  const nov = `#zgodovina/${vrsta}/${sidro}`;
  if (location.hash === nov) risi(); else location.hash = nov;
}

function risi() {
  if (!zadnji) return;
  const zavihek = preberiNaslov();
  document.querySelectorAll("[data-zavihek]").forEach((a) => {
    if (a.dataset.zavihek === zavihek) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  const v = el("vsebina");
  // Deljenje se osvežuje samo in ga osvežitev pregleda ne sme podreti:
  // zemljevid bi vsako minuto nastal znova.
  if (zavihek === "deljenje") { deljenjeOdpri(v); return; }
  deljenjeZapri();
  if (zavihek === "obvestila") { obvestilaRisi(v, zadnji); return; }
  if (zavihek === "sporocila") v.innerHTML = sporocila(zadnji);
  else if (zavihek === "viri") v.innerHTML = viriZavihek(zadnji);
  else if (zavihek === "zgodovina") v.innerHTML = zgodovina();
  else v.innerHTML = stanje(zadnji);
  poveziDogodke();
}

function poveziDogodke() {
  const sp = el("sporocila");
  if (sp) sp.addEventListener("click", obSporocilu);
  const pv = el("preveri-vire");
  if (pv) pv.addEventListener("click", preveriVire);
  // Vir na zavihku Stanje odpre zavihek Viri pri svoji kartici.
  document.querySelectorAll(".adm-viri-kratko a[data-vir]").forEach((a) => {
    a.addEventListener("click", () => { skokNaVir = a.dataset.vir; });
  });
  if (skokNaVir && el(`vir-${skokNaVir}`)) {
    el(`vir-${skokNaVir}`).scrollIntoView({ block: "center" });
    el(`vir-${skokNaVir}`).classList.add("je-izbran");
    skokNaVir = null;
  }
  const g30 = el("graf-30");
  if (g30) {
    const mes = zadnjih30(zadnji);
    g30.querySelectorAll("rect[data-i]").forEach((r) => {
      r.addEventListener("click", () => pojdi("dan", mes[Number(r.dataset.i)].dan));
    });
  }
  const gA = el("graf-app");
  if (gA) {
    // Dan odpre dan, mesec (pri letu) odpre mesec.
    gA.querySelectorAll("rect[data-i]").forEach((r) => {
      const v = vedraApp[Number(r.dataset.i)];
      if (v) r.addEventListener("click", () => pojdi(v.dni.length > 1 ? "mesec" : "dan", v.dni[0]));
    });
  }
  const gO = el("graf-obdobje");
  if (gO && obdobje && izbor.vrsta !== "dan" && izbor.vrsta !== "leto") {
    const dni = vseDni(obdobje.od, obdobje.do);
    gO.querySelectorAll("rect[data-i]").forEach((r) => {
      r.addEventListener("click", () => pojdi("dan", dni[Number(r.dataset.i)]));
    });
  }
  const vrste = el("vrste");
  if (!vrste) return;
  vrste.addEventListener("click", (e) => {
    const b = e.target.closest("button[data-v]");
    if (b) pojdi(b.dataset.v, izbor.sidro);
  });
  el("nazaj").addEventListener("click", () => pojdi(izbor.vrsta, premakni(izbor.vrsta, izbor.sidro, -1)));
  el("naprej").addEventListener("click", () => pojdi(izbor.vrsta, premakni(izbor.vrsta, izbor.sidro, 1)));
  el("na-danes").addEventListener("click", () => pojdi(izbor.vrsta, danes()));
  el("datum").addEventListener("change", (e) => { if (e.target.value) pojdi(izbor.vrsta, e.target.value); });
}

// ------------------------------------------------------------------ nalaganje

async function podatki(poizvedba = "") {
  const r = await fetch(`/admin/podatki${poizvedba}`, { credentials: "same-origin" });
  if (!r.ok) throw new Error(r.status === 403 ? "Napačen žeton." : `strežnik: ${r.status}`);
  return r.json();
}

function pokaziNapako(besedilo) {
  const p = el("adm-napaka");
  p.hidden = !besedilo;
  p.textContent = besedilo || "";
}

/** Današnji odgovor vedno, izbrano obdobje le na zavihku Zgodovina. */
async function osvezi() {
  try {
    zadnji = await podatki();
    // Zdravje zajema se prikaže tudi tedaj -- prav takrat je pregled edino,
    // kar na tej strani sploh pove kaj uporabnega.
    pokaziNapako(zadnji.steje === false
      ? "Štetje obiska je izklopljeno (KAJROS_OBISK=0) — številke se ne dopolnjujejo in so lahko poljubno stare."
      : "");
    if (preberiNaslov() === "zgodovina") await naloziObdobje();
    const s = zadnji.sporocila || {};
    el("sporocil-znacka").hidden = !s.neprebranih;
    el("sporocil-znacka").textContent = s.neprebranih ? String(s.neprebranih) : "";
    // Veljavno obvestilo je nekaj, kar potniki ta hip berejo: značka je
    // opomnik, da ga je treba umakniti, ko ne drži več. Samodejna štejejo
    // zraven, ker jih potnik bere enako.
    const obv = ((zadnji.obvestila || {}).seznam || []).filter((o) => o.velja).length
      + ((zadnji.obvestila || {}).samodejna || []).length;
    el("obvestil-znacka").hidden = !obv;
    el("obvestil-znacka").textContent = obv ? String(obv) : "";
    const zdaj = (zadnji.deljenje && zadnji.deljenje.zdaj) || 0;
    el("deljenje-znacka").hidden = !zdaj;
    el("deljenje-znacka").textContent = zdaj ? String(zdaj) : "";
    const [raz, bes] = skupnoZdravje(zadnji);
    // Značka na zavihku Viri: koliko virov ni zdravih -- rdeča, kadar kaj stoji.
    const nezdravih = ((zadnji.viri || {}).seznam || [])
      .filter((v) => v.razred === "je-slaba" || v.razred === "je-mlacna").length;
    el("viri-znacka").hidden = !nezdravih;
    el("viri-znacka").textContent = nezdravih ? String(nezdravih) : "";
    el("viri-znacka").className = `adm-znacka ${raz === "je-slaba" ? "je-slaba" : "je-mlacna"}`;
    const ura = URA_TS.format(new Date());
    el("osvezeno").innerHTML = `<a href="#viri"><span class="adm-pika ${raz}"></span>${escapeHtml(bes)}</a> · osveženo ${ura}`;
    noga(zadnji);
    risi();
  } catch (e) {
    pokaziNapako(`Pregleda ni bilo mogoče naložiti — ${e.message}`);
  }
}

addEventListener("hashchange", async () => {
  if (preberiNaslov() === "zgodovina") {
    obdobje = null;
    risi();
    try { await naloziObdobje(); } catch (e) { pokaziNapako(`Obdobja ni bilo mogoče naložiti — ${e.message}`); }
  }
  risi();
});

// `pollWhileVisible` prvič sproži takoj, zato tu ni ločenega klica. Minuta je
// ritem, v katerem se števci sploh zapišejo v bazo -- pogosteje ni česa videti,
// in v skritem zavihku se ne osvežuje nič.
pollWhileVisible(osvezi, 60000);
