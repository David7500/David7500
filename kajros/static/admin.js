"use strict";

// Pregled za skrbnika: kdo je bil na strani in ali stroj dela.
//
// Štirje zavihki -- Stanje, Zgodovina, Sporočila, Deljenje. Prvi trije imajo
// en endpoint, `/admin/podatki?od=&do=`. Brez meja vrne današnji dan; odgovor
// vedno nosi še `danes`, `zadnjih30`, zdravje in sporočila, zato Stanje in
// Sporočila rabita en klic, Zgodovina pa enega več za izbrano obdobje.
// Deljenje ima svoj endpoint in ritem (`admin_deljenje.js`).
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

/** Zdravje zajema in stroja kot vrstice s piko stanja. */
function vrsticeZdravja(d) {
  const z = d.zdravje || {}, m = d.stroj || {}, mreze = z.by_network || {};
  const zdaj = Date.now() / 1000;
  // Ista meja kot v nogi potniških strani (`common.FEED_STALE_S`): zajem
  // bere vsakih 30 s, zato je 90 s že tretji zgrešeni obhod.
  const feed = !z.last_feed_ts || zdaj - z.last_feed_ts > FEED_STALE_S ? "je-slaba" : "je-dobra";
  // Po omrežjih je `/api/health` predpomnjen do 10 min, zato meja 20 min --
  // sicer bi predpomnilnik sam prižgal rdečo.
  const omr = (ts) => !ts ? "je-slaba" : zdaj - ts < 1200 ? "je-dobra" : zdaj - ts < 3600 ? "je-mlacna" : "je-slaba";
  const disk = m.disk_vseh ? m.disk_prostih / m.disk_vseh : null;
  const diskR = disk == null ? "" : disk < 0.08 ? "je-slaba" : disk < 0.2 ? "je-mlacna" : "je-dobra";
  const zel = mreze.zeleznica || {}, bus = mreze.avtobus || {}, sen = z.senca || {};
  // Vožnje iz feeda, ki jih vozni red ne pozna, zajem zavrže. 22. 9. 2026 jih
  // je bilo 16 od 662 (2,4 %) -- tri linije LPP brez vsake zamude; ostanek
  // po popravku na arwenu 5 od 538 (0,9 %).
  //
  // Rdeče šele pri vsaj treh vožnjah IN 2 %, kot spodaj pri legi. 28. 9. 2026
  // ob 23:42 je bila vsa stran rdeča zaradi ene same vožnje: Nomagov N0152,
  // nagrobnik brez voznega reda, ki ga feed še nosi -- 1 od 29, ker ponoči
  // vozi malo voženj. Podnevi bi bila ista vožnja 1 od ~600.
  const nez = Object.entries(z.rt_neznanih || {});
  const nezSlabo = nez.some(([, [n, vseh]]) => n >= 3 && vseh && n / vseh >= 0.02);
  const nezR = !nez.length ? "" : nezSlabo ? "je-slaba"
    : nez.some(([, [n]]) => n > 0) ? "je-mlacna" : "je-dobra";
  // Obratno: vozilo vozi in ima lego, feed zamud pa ga ne nosi. Od 21. do
  // 25. 9. 2026 ~430 Nomagovih voženj na dan, števec zgoraj pa zelen. Na
  // vožnjah, ki jih feed nosi, je bilo takih 0 od 295. Trojka je [ne v feedu,
  // brez zamude, vseh]: `iz_lege` vrzel zapolni, zato je napaka vira rumena,
  // rdeče pa je šele to, kar vidi potnik -- vozilo brez vsake zamude.
  //
  // Rdeče šele pri vsaj treh vozilih IN 5 % prevoznika. Po zapolnitvi ostane
  // nekaj voženj, ki so odpeljale pozno in še niso prevozile drugega
  // postanka (izhodišča `iz_lege` ne meri): 25. 9. po objavi Nomago 1-2 od
  // ~100, takoj po restartu 5 od 104 (4,8 %), preden je `iz_lege` dohitel.
  // Samo z deležem 2 % je bila vrstica -- in s tem vsa stran -- rdeča zaradi
  // dveh avtobusov. Pred zapolnitvijo je bilo 8 od 91 (8,8 %).
  const lbz = Object.entries(z.lega_brez_zamude || {}).filter(([, [nf, nz]]) => nf > 0 || nz > 0);
  const lbzSlabo = lbz.some(([, [, nz, vseh]]) => nz >= 3 && vseh && nz / vseh >= 0.05);
  const lbzR = !z.lega_brez_zamude ? "" : lbzSlabo ? "je-slaba" : lbz.length ? "je-mlacna" : "je-dobra";
  // Dva vira zamud vlakov (`zamude_sz`). 28. 9. 2026 je derp.si z voznim
  // redom DUJPP izgubil vse vlake, zemljevid SŽ jih je imel. Rumeno, kadar
  // manjka eden od virov -- zamude so, a le iz enega; kadar ni nobenega,
  // je rdeča že vrstica „vlaki · zadnji zapis“. Nit bere vsako minuto, zato
  // je vir po petih minutah brez odgovora obstal.
  const zs = z.zamude_sz;
  const zsStoji = zs && (!zs.ts || zdaj - zs.ts > 300);
  const zsEden = zs && !zsStoji && !zs.oba && (zs.samo_sz || zs.samo_derp);
  const zsR = !zs ? "" : zsStoji || zsEden ? "je-mlacna" : zs.oba ? "je-dobra" : "";
  const zsVr = !zs ? "—" : zsStoji
    ? `zemljevid SŽ ne odgovarja ${pred(zs.napaka_ts || zs.ts)}${zs.napaka ? `: ${zs.napaka}` : ""}`
    : `oba ${st(zs.oba)} · samo SŽ ${st(zs.samo_sz)} · samo derp ${st(zs.samo_derp)}`
      + (zs.nepripetih ? ` · nepripetih ${st(zs.nepripetih)}` : "");
  // Brez barve, dokler ne vemo, kakšno razhajanje je običajno.
  const pr = zs && zs.primerjava;
  const prVr = !pr || !pr.parov ? "—"
    : `${st(100 * pr.v_minuti / pr.parov)} % v minuti od ${st(pr.parov)} · nad 5 min ${st(pr.nad_5_min)}`;
  return [
    ["zadnja zamuda iz feeda", pred(z.last_feed_ts), feed],
    ["vlaki · zadnji zapis", pred(zel.last_feed_ts), omr(zel.last_feed_ts)],
    ["avtobusi · zadnji zapis", pred(bus.last_feed_ts), omr(bus.last_feed_ts)],
    ["vozil z lego", st(z.vehicles_with_gps), ""],
    ["vlakov / meritev", `${st(zel.trips)} / ${st(zel.runs)}`, ""],
    ["avtobusov / meritev", `${st(bus.trips)} / ${st(bus.runs)}`, ""],
    ["vožnje brez voznega reda",
      nez.length ? nez.map(([vir, [n, vseh]]) => `${vir.toUpperCase()} ${st(n)} od ${st(vseh)}`).join(" · ") : "—",
      nezR],
    ["vozila brez feeda zamud",
      lbz.length ? lbz.map(([ime, [nf, nz, vseh]]) =>
        `${ime} ${st(nf)} od ${st(vseh)}${nz ? `, brez zamude ${st(nz)}` : ""}`).join(" · ") : "—",
      lbzR],
    ["vlaki · vira zamud", zsVr, zsR],
    ["ujemanje virov · 24 h", prVr, ""],
    ["senca napovedi", sen.vrstic ? `${st(100 * sen.razresenih / sen.vrstic, 1)} % od ${st(sen.vrstic)}` : "—", ""],
    ["aktivnih obvestil", st(z.alerts_active), ""],
    ["prostora na disku", `${bajti(m.disk_prostih)} (${st(100 * (disk || 0))} %)`, diskR],
    ["baza", bajti(z.db_bytes), ""],
    ["zajetih dni", st(z.days_covered), ""],
    ["strežnik teče", trajanje(m.teka_s), ""],
  ];
}

function blokZdravja(d) {
  return `<div class="adm-zdr">${vrsticeZdravja(d).map(([ime, vr, raz]) =>
    `<div><span class="adm-pika ${raz}"></span><span class="ime">${escapeHtml(ime)}</span>
      <span class="vr">${escapeHtml(vr)}</span></div>`).join("")}</div>`;
}

/** Najhujše stanje med vrsticami zdravja -- za piko v glavi. */
function skupnoZdravje(d) {
  const r = vrsticeZdravja(d).map((v) => v[2]);
  if (r.includes("je-slaba")) return ["je-slaba", "nekaj stoji"];
  if (r.includes("je-mlacna")) return ["je-mlacna", "opozorilo"];
  return ["je-dobra", "vse dela"];
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
      ${ploscica(`<span style="display:inline-flex;align-items:center;gap:10px"><span class="adm-pika ${zR}" style="width:12px;height:12px"></span>${zB}</span>`,
        "zajem in stroj", `zadnji feed ${pred(d.zdravje && d.zdravje.last_feed_ts)}`)}
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
    ${plosca("s8", "Zdravje", "isto kot /api/health", blokZdravja(d))}
    ${plosca("s6", "Od kod pridejo", "danes · ogledi", blokVirov(d), "Z iskalnika, AI ali omrežja; naravnost se ne šteje.")}
    ${plosca("s6", "Roboti", "danes · zahtev · desno strani", blokRobotov(d), "Po predstavitvi, ne preverjeno.")}
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
        <a class="adm-sp-od" href="mailto:${encodeURIComponent(v.email)}">${escapeHtml(v.email)}</a>
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
  const zavihek = ["stanje", "zgodovina", "sporocila", "obvestila", "deljenje"].includes(zav) ? zav : "stanje";
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
  else if (zavihek === "zgodovina") v.innerHTML = zgodovina();
  else v.innerHTML = stanje(zadnji);
  poveziDogodke();
}

function poveziDogodke() {
  const sp = el("sporocila");
  if (sp) sp.addEventListener("click", obSporocilu);
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
    // opomnik, da ga je treba umakniti, ko ne drži več.
    const obv = ((zadnji.obvestila || {}).seznam || []).filter((o) => o.velja).length;
    el("obvestil-znacka").hidden = !obv;
    el("obvestil-znacka").textContent = obv ? String(obv) : "";
    const zdaj = (zadnji.deljenje && zadnji.deljenje.zdaj) || 0;
    el("deljenje-znacka").hidden = !zdaj;
    el("deljenje-znacka").textContent = zdaj ? String(zdaj) : "";
    const [raz, bes] = skupnoZdravje(zadnji);
    const ura = new Intl.DateTimeFormat("sl-SI", { timeZone: "Europe/Ljubljana", hour: "2-digit", minute: "2-digit" }).format(new Date());
    el("osvezeno").innerHTML = `<span class="adm-pika ${raz}"></span>${escapeHtml(bes)} · osveženo ${ura}`;
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
