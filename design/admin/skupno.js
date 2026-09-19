"use strict";

// Skupna podlaga treh predlogov pregleda: seštevanje obdobij in grafi v SVG.
// Predloge berejo `podatki.js`; prava stran bi isto dobila od strežnika.

const ZDAJ = new Date(PREGLED.zdravje.last_feed_at);
const DAN_MS = 86400000;
const MESECI = ["januar", "februar", "marec", "april", "maj", "junij", "julij",
  "avgust", "september", "oktober", "november", "december"];
const DNI_TEDNA = ["ned", "pon", "tor", "sre", "čet", "pet", "sob"];

const $ = (id) => document.getElementById(id);
const st = (n, d = 0) => (n == null ? "—" : Number(n).toLocaleString("sl-SI",
  { minimumFractionDigits: d, maximumFractionDigits: d }));
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function isoDan(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
function izIso(s) { const [y, m, d] = s.split("-").map(Number); return new Date(y, m - 1, d); }
function dodaj(d, n) { const x = new Date(d); x.setDate(x.getDate() + n); return x; }
function kratkiDan(s) { const d = izIso(s); return `${d.getDate()}. ${d.getMonth() + 1}.`; }
function dolgiDan(s) { const d = izIso(s); return `${DNI_TEDNA[d.getDay()]}, ${d.getDate()}. ${d.getMonth() + 1}. ${d.getFullYear()}`; }

function ms(v) {
  if (v == null) return "—";
  if (v < 1000) return `${st(v)} ms`;
  if (v < 60000) return `${st(v / 1000, 1)} s`;
  return `${st(v / 60000, 1)} min`;
}
function bajti(b) {
  const e = ["B", "kB", "MB", "GB", "TB"]; let i = 0;
  while (b >= 1024 && i < e.length - 1) { b /= 1024; i++; }
  return `${st(b, b < 10 ? 1 : 0)} ${e[i]}`;
}
function pred(ts) {
  const s = Math.max(0, Math.round(ZDAJ.getTime() / 1000 - ts));
  if (s < 90) return `pred ${s} s`;
  if (s < 5400) return `pred ${Math.round(s / 60)} min`;
  return `pred ${st(s / 3600, 1)} h`;
}
/** Razred hitrosti: kar potnik še prenese, kar opazi, kar ga odžene. */
function hitrostRazred(v) {
  if (v == null) return "calm";
  if (v < 1000) return "mild";
  if (v < 5000) return "hard";
  return "bad";
}

// ------------------------------------------------------------- obdobja

const OBDOBJA = { dan: "Dan", teden: "Teden", mesec: "Mesec", leto: "Leto", vse: "Vse" };
const PRVI_DAN = Object.keys(DNEVI).sort()[0];

/** [od, do] obdobja, ki vsebuje `sidro`. Teden začne v ponedeljek. */
function meje(vrsta, sidro) {
  const d = izIso(sidro);
  if (vrsta === "dan") return [sidro, sidro];
  if (vrsta === "teden") {
    const pon = dodaj(d, -((d.getDay() + 6) % 7));
    return [isoDan(pon), isoDan(dodaj(pon, 6))];
  }
  if (vrsta === "mesec") {
    return [isoDan(new Date(d.getFullYear(), d.getMonth(), 1)),
      isoDan(new Date(d.getFullYear(), d.getMonth() + 1, 0))];
  }
  if (vrsta === "leto") return [`${d.getFullYear()}-01-01`, `${d.getFullYear()}-12-31`];
  return [PRVI_DAN, isoDan(ZDAJ)];
}

function premakni(vrsta, sidro, smer) {
  const d = izIso(sidro);
  if (vrsta === "dan") return isoDan(dodaj(d, smer));
  if (vrsta === "teden") return isoDan(dodaj(d, 7 * smer));
  if (vrsta === "mesec") return isoDan(new Date(d.getFullYear(), d.getMonth() + smer, 1));
  if (vrsta === "leto") return isoDan(new Date(d.getFullYear() + smer, 0, 1));
  return sidro;
}

function naslovObdobja(vrsta, sidro) {
  const [od, do_] = meje(vrsta, sidro);
  const d = izIso(sidro);
  if (vrsta === "dan") return dolgiDan(sidro);
  if (vrsta === "teden") return `${kratkiDan(od)} – ${kratkiDan(do_)} ${izIso(do_).getFullYear()}`;
  if (vrsta === "mesec") return `${MESECI[d.getMonth()]} ${d.getFullYear()}`;
  if (vrsta === "leto") return String(d.getFullYear());
  return `od ${kratkiDan(od)} ${izIso(od).getFullYear()}`;
}

function vsota(seznami, kljuc, polja) {
  const m = new Map();
  for (const s of seznami) for (const r of s) {
    const k = r[kljuc];
    const t = m.get(k) || Object.fromEntries([[kljuc, k], ...polja.map((p) => [p, 0])]);
    for (const p of polja) t[p] += r[p] || 0;
    m.set(k, t);
  }
  return [...m.values()];
}

/** Vse, kar zgodovina pokaže za eno obdobje. */
function obdobje(vrsta, sidro) {
  const [od, do_] = meje(vrsta, sidro);
  const dnevi = [];
  for (let d = izIso(od); isoDan(d) <= do_; d = dodaj(d, 1)) dnevi.push(isoDan(d));
  const vrstice = PREGLED.po_dnevih.filter((r) => r.dan >= od && r.dan <= do_);
  const det = dnevi.filter((d) => DNEVI[d]).map((d) => DNEVI[d]);
  const sum = (p) => vrstice.reduce((a, r) => a + (r[p] || 0), 0);
  const ure = vsota(det.map((x) => x.ure), "kljuc", ["zahtev", "ogledov"])
    .sort((a, b) => a.kljuc.localeCompare(b.kljuc));
  const pocasi = vsota(det.map((x) => x.pocasi), "pot", ["zahtev", "napak4", "napak5"]);
  for (const p of pocasi) {
    const vse = det.flatMap((x) => x.pocasi.filter((r) => r.pot === p.pot));
    p.ms_naj = Math.max(...vse.map((r) => r.ms_naj));
    p.ms_povp = vse.reduce((a, r) => a + r.ms_povp * r.zahtev, 0) / Math.max(1, p.zahtev);
  }
  pocasi.sort((a, b) => b.ms_naj - a.ms_naj);
  return {
    vrsta, sidro, od, do: do_, dnevi,
    zDnevi: vrstice.length,
    ljudi: sum("ljudi"), ogledov: sum("ogledov"), zahtev: sum("zahtev"),
    botov: sum("botov"), brez_js: sum("brez_js"),
    po_dnevih: dnevi.map((d) => vrstice.find((r) => r.dan === d) || { dan: d, prazen: true }),
    ure,
    strani: vsota(det.map((x) => x.strani), "pot", ["zahtev", "ljudi"]).sort((a, b) => b.ljudi - a.ljudi),
    pocasi,
    naprave: vsota(det.map((x) => x.naprave), "kljuc", ["ogledov"]).sort((a, b) => b.ogledov - a.ogledov),
    drzave: vsota(det.map((x) => x.drzave), "kljuc", ["ogledov"]).sort((a, b) => b.ogledov - a.ogledov),
    trajanje: vsota(det.map((x) => x.trajanje), "k", ["n"]),
    seje: vsota(det.map((x) => x.seje), "ogledov", ["n"]),
  };
}

/** Sprememba proti prejšnjemu obdobju; brez podatka ne trdi ničesar. */
function razlika(zdaj, prej) {
  if (!prej) return { besedilo: "prej ni podatka", smer: 0 };
  const p = Math.round(100 * (zdaj - prej) / prej);
  return { besedilo: `${p > 0 ? "+" : p < 0 ? "−" : "±"}${Math.abs(p)} % proti prejšnjemu`, smer: Math.sign(p) };
}

// ------------------------------------------------------------- grafi

let _tip;
function tooltip() {
  if (_tip) return _tip;
  _tip = document.createElement("div");
  _tip.className = "graf-tip";
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
    _tip.style.left = `${x}px`; _tip.style.top = `${y}px`;
  });
  return _tip;
}

/**
 * Navpični stolpci z zaobljenim vrhom, sidrani na osnovnico. Prazen dan je
 * šrafiran, ne ničla: „štetja še ni bilo“ ni isto kot „ni prišel nihče“.
 */
function stolpci(vrednosti, { visina = 180, oznake, tip, poudari = -1, crta } = {}) {
  tooltip();
  const n = vrednosti.length;
  const naj = Math.max(1, ...vrednosti.filter((v) => v != null));
  // `undefined` je prihodnost, `null` dan brez štetja.
  const korak = niceStep(naj);
  const vrh = Math.ceil(naj / korak) * korak;
  const W = 1000, H = visina, L = 34, B = oznake ? 22 : 6, T = 8;
  // Pri malo stolpcih je presledek širši, sicer teden izgleda kot trije zidovi.
  const sir = (W - L) / n, rob = n < 12 ? sir * 0.45 : Math.min(6, sir * 0.22);
  const y = (v) => T + (H - T - B) * (1 - v / vrh);
  let s = `<svg class="graf" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img">`;
  s += `<defs><pattern id="srafura" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" stroke="var(--line-firm)" stroke-width="2"/></pattern></defs>`;
  for (let v = 0; v <= vrh; v += korak) {
    s += `<line x1="${L}" x2="${W}" y1="${y(v)}" y2="${y(v)}" class="graf-mreza"/>`;
  }
  vrednosti.forEach((v, i) => {
    const x = L + i * sir + rob / 2, w = sir - rob;
    const t = tip ? tip(i) : "";
    if (v === undefined) return;          // prihodnost: nič, ne šrafura
    if (v == null) {
      s += `<rect x="${x}" y="${T}" width="${w}" height="${H - T - B}" fill="url(#srafura)" opacity=".55" data-tip="${esc(t)}"/>`;
      return;
    }
    const h = Math.max(v > 0 ? 2 : 0, H - B - y(v));
    const r = Math.min(4, w / 2, h);
    const top = H - B - h;
    s += `<rect x="${x - rob / 2}" y="${T}" width="${sir}" height="${H - T - B}" fill="transparent" data-i="${i}" data-tip="${esc(t)}"/>`;
    s += `<path class="graf-stolpec${i === poudari ? " je-poudarek" : ""}" d="M${x},${H - B} V${top + r} q0,-${r} ${r},-${r} h${w - 2 * r} q${r},0 ${r},${r} V${H - B} Z" pointer-events="none"/>`;
  });
  if (crta) {
    const pts = crta.map((v, i) => v == null ? null : `${L + i * sir + sir / 2},${y(v)}`);
    let seg = [];
    const risi = () => { if (seg.length > 1) s += `<polyline class="graf-crta" points="${seg.join(" ")}"/>`; seg = []; };
    pts.forEach((p) => (p ? seg.push(p) : risi())); risi();
  }
  s += `</svg>`;
  // Osi so HTML, ne SVG: `preserveAspectRatio=none` bi črke raztegnil.
  let osY = `<div class="graf-osy">`;
  for (let v = vrh; v >= 0; v -= korak) osY += `<span style="top:${(y(v) / H) * 100}%">${st(v)}</span>`;
  osY += `</div>`;
  let osX = "";
  if (oznake) {
    osX = `<div class="graf-osx" style="padding-left:${(L / W) * 100}%">`;
    oznake.forEach((o) => { osX += `<span>${o}</span>`; });
    osX += `</div>`;
  }
  return `<div class="graf-ovoj" style="height:${H}px">${s}${osY}${osX}</div>`;
}

function niceStep(naj) {
  const surovo = naj / 4;
  const p = 10 ** Math.floor(Math.log10(surovo));
  for (const k of [1, 2, 2.5, 5, 10]) if (k * p >= surovo) return k * p;
  return 10 * p;
}

/** Ena vodoravna vrstica s stolpcem — ime, tir, število, pripis. */
function vrsta(ime, v, naj, desno = "", razred = "") {
  const d = naj > 0 ? Math.max(1.5, (100 * v) / naj) : 0;
  return `<div class="hv${razred ? " " + razred : ""}" data-tip="${esc(`<b>${esc(ime)}</b><br>${st(v)}${desno ? " · " + esc(desno) : ""}`)}">
    <span class="hv-ime" title="${esc(ime)}">${esc(ime)}</span>
    <span class="hv-tir"><span style="width:${d.toFixed(1)}%"></span></span>
    <span class="hv-st">${st(v)}</span>
    <span class="hv-pri">${esc(desno)}</span></div>`;
}

/** Ime poti, kakor ga bere človek, ne usmerjevalnik. */
const IMENA_STRANI = {
  "/": "Domača", "/app/pot": "Iskalnik poti", "/app/pot/podrobno": "Pot · podrobno",
  "/app/bus": "Avtobus", "/app/bus/{train_no}": "Avtobus · vožnja",
  "/app/train": "Vlak", "/app/train/{train_no}": "Vlak · vožnja",
  "/app/map": "Zemljevid", "/app/ovire": "Ovire", "/app/statistika": "Statistika",
  "(neznano)": "(neznano)",
};
const imeStrani = (p) => IMENA_STRANI[p] || p;

const NAPRAVE = { telefon: "telefon", "računalnik": "računalnik", aplikacija: "aplikacija", tablica: "tablica" };

/**
 * Glavni graf obdobja: dan po urah, teden in mesec po dnevih, leto po
 * mesecih, vse po dnevih. Vrne vrednosti, oznake in besedilo za namig.
 */
function podenote(o) {
  if (o.vrsta === "dan") {
    const ure = Object.fromEntries(o.ure.map((u) => [u.kljuc, u]));
    const imaDan = !!DNEVI[o.sidro];
    const zdajUra = o.sidro === isoDan(ZDAJ) ? ZDAJ.getHours() : 23;
    const v = [...Array(24).keys()].map((h) => {
      if (h > zdajUra) return undefined;
      if (!imaDan) return null;
      const u = ure[String(h).padStart(2, "0")];
      return u ? u.ogledov : 0;
    });
    return {
      enota: "ogledov na uro", v,
      oznake: [...Array(24).keys()].map((h) => (h % 3 ? "" : `${h}h`)),
      tip: (i) => v[i] == null ? `${i}:00 · ni podatka` : `<b>${i}:00–${i + 1}:00</b><br>${st(v[i])} ogledov`,
    };
  }
  if (o.vrsta === "leto") {
    const m = MESECI.map((_, k) => new Date(izIso(o.sidro).getFullYear(), k, 1) > ZDAJ ? undefined : null);
    for (const r of o.po_dnevih) if (!r.prazen) {
      const k = izIso(r.dan).getMonth(); m[k] = (m[k] || 0) + r.ljudi;
    }
    return {
      enota: "obiskov na mesec (vsota dnevnih)", v: m,
      oznake: MESECI.map((x) => x.slice(0, 3)),
      tip: (i) => m[i] == null ? `${MESECI[i]} · ni podatka` : `<b>${MESECI[i]}</b><br>${st(m[i])} obiskov`,
    };
  }
  const dni = o.po_dnevih;
  const danes = isoDan(ZDAJ);
  const v = dni.map((r) => (r.dan > danes ? undefined : r.prazen ? null : r.ljudi));
  const redko = dni.length > 14;
  return {
    enota: "ljudi na dan", v,
    oznake: dni.map((r, i) => (!redko || i % 7 === 0) ? kratkiDan(r.dan) : ""),
    tip: (i) => dni[i].prazen ? `${dolgiDan(dni[i].dan)}<br>ni podatka` :
      `<b>${dolgiDan(dni[i].dan)}</b><br>${st(dni[i].ljudi)} ljudi · ${st(dni[i].ogledov)} ogledov`,
  };
}

/** Zadnjih `n` dni do danes, s praznimi, kjer štetja še ni bilo. */
function zadnjihDni(n) {
  const out = [];
  for (let i = n - 1; i >= 0; i--) {
    const d = isoDan(dodaj(ZDAJ, -i));
    out.push(PREGLED.po_dnevih.find((r) => r.dan === d) || { dan: d, prazen: true });
  }
  return out;
}

/** Zdravje zajema kot seznam vrstic z razredom stanja. */
function zdravje() {
  const z = PREGLED.zdravje, s = PREGLED.stroj;
  const star = (ts) => ZDAJ.getTime() / 1000 - ts;
  const razFeed = (ts) => star(ts) < 120 ? "mild" : star(ts) < 600 ? "hard" : "bad";
  // Po omrežjih je v `/api/health` predpomnjeno do 10 min -- zato meja 20 min,
  // sicer bi predpomnilnik sam prižgal rdečo.
  const razOmr = (ts) => star(ts) < 1200 ? "mild" : star(ts) < 3600 ? "hard" : "bad";
  const disk = s.disk_prostih / s.disk_vseh;
  return [
    { ime: "Zajem", vr: pred(z.last_feed_ts), raz: razFeed(z.last_feed_ts) },
    { ime: "· vlaki", vr: pred(z.by_network.zeleznica.last_feed_ts), raz: razOmr(z.by_network.zeleznica.last_feed_ts) },
    { ime: "· avtobusi", vr: pred(z.by_network.avtobus.last_feed_ts), raz: razOmr(z.by_network.avtobus.last_feed_ts) },
    { ime: "Vozil z lego", vr: st(z.vehicles_with_gps), raz: z.vehicles_with_gps > 20 ? "mild" : "hard" },
    { ime: "Senčno merjenje", vr: `${st(100 * z.senca.razresenih / z.senca.vrstic, 1)} % razrešenih`, raz: "mild" },
    { ime: "Disk", vr: `${bajti(s.disk_prostih)} prostih`, raz: disk > 0.15 ? "mild" : disk > 0.05 ? "hard" : "bad" },
    { ime: "Baza", vr: bajti(z.db_bytes), raz: "calm" },
    { ime: "Strežnik teče", vr: `${st(s.teka_s / 3600, 1)} h`, raz: "calm" },
    { ime: "Sporočil", vr: st(PREGLED.sporocila.neprebranih) + " novih", raz: PREGLED.sporocila.neprebranih ? "hard" : "calm" },
    { ime: "Aktivnih ovir", vr: st(z.alerts_active), raz: "calm" },
  ];
}
