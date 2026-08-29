"use strict";

// Svoje okno enega vlaka: ta voznja + zgodovina te poti.
// Barve zamud so projektna ORDINALNA lestvica (en odtenek, monotona svetlost) --
// uporabljena samo tam, kjer odtenek pomeni velikost zamude. Kjer meritve ni,
// nastopi rezervirana barva, ki je lestvica ne uporablja.

const TRAIN_NO = document.body.dataset.trainNo;
const ENC = encodeURIComponent(TRAIN_NO);
// Datum iz naslova: povezava z iskalnika kaze na konkreten prometni dan.
// Brez njega bi klik na vcerajsnjo vozjno odprl danasnjo.
const URL_PARAMS = new URLSearchParams(location.search);
const URL_DATE = URL_PARAMS.get("date") || null;
// Id voznje: stevilka linije pri avtobusih ni enolicna.
const URL_TRIP = URL_PARAMS.get("trip") || null;
// Postaja, s katere je potnik prisel (odhodna tabla, iskalnik zvez). Okno jo
// izpostavi -- brez tega mora clovek svojo vrstico iskati med tridesetimi
// postanki, in to na telefonu.
const URL_STATION = URL_PARAMS.get("postaja") || null;
const DATE_Q = (() => {
  const p = new URLSearchParams();
  if (URL_DATE) p.set("date", URL_DATE);
  if (URL_TRIP) p.set("trip", URL_TRIP);
  return p.toString() ? `?${p}` : "";
})();

const RUN_POLL_MS = 30000;
const HIST_POLL_MS = 600000;

// Rezervirano za "to ni meritev". Preverjeno z validatorjem palete proti vsem
// stiriv barvam lestvice zamud: najslabsi par ΔE 16,4 (deutan) -- lahko locljivo.
const ESTIMATE_COLOR = "#a8d8ff";

const INK_LINE = "#4a515c";
const INK_GRID = "#23272f";
const INK_AXIS = "#79828f";
const INK_BAR = "#3d434f";
const PAST_COLOR = "#79828f";
const TEMP_COLOR = "#b8724a";
const SURFACE = "#14161a";

const tooltipEl = document.getElementById("tooltip");

function showTip(html, ev) {
  tooltipEl.innerHTML = html;
  tooltipEl.hidden = false;
  const pad = 12;
  const r = tooltipEl.getBoundingClientRect();
  let x = ev.clientX + pad;
  let y = ev.clientY + pad;
  if (x + r.width > window.innerWidth - 8) x = ev.clientX - r.width - pad;
  if (y + r.height > window.innerHeight - 8) y = ev.clientY - r.height - pad;
  tooltipEl.style.left = `${x}px`;
  tooltipEl.style.top = `${y}px`;
}

function hideTip() {
  tooltipEl.hidden = true;
}

// Korak osi naj bo cela minuta iz znanega nabora -- sicer os pokaze 0, 4, 8, 11, 15.
const NICE_MIN = [1, 2, 5, 10, 15, 20, 30, 60, 120];

function niceTicks(maxSeconds, wanted) {
  const maxMin = Math.max(1, maxSeconds / 60);
  const step = NICE_MIN.find((m) => maxMin / m <= (wanted || 5)) || NICE_MIN[NICE_MIN.length - 1];
  const top = Math.ceil(maxMin / step) * step;
  const out = [];
  for (let m = 0; m <= top; m += step) out.push(m * 60);
  return { top: top * 60, values: out };
}

function svgEl(name, attrs, text) {
  const el = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const [k, v] of Object.entries(attrs || {})) el.setAttribute(k, v);
  if (text != null) el.textContent = text;
  return el;
}

// Graf se prerise ob spremembi sirine -- pisava tako ostane v pravi velikosti,
// namesto da bi jo viewBox skaliral.
const redrawers = new Map();

function mountChart(el, draw) {
  const render = () => {
    // clientWidth steje tudi padding kartice -- brez odstevanja je SVG vsakic
    // za 24 px sirsi od prostora in spodaj zraste vodoravni drsnik.
    const cs = getComputedStyle(el);
    const w = Math.floor(el.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight));
    if (w <= 0) return;
    el.replaceChildren(draw(w));
  };
  redrawers.set(el, render);
  render();
}

let resizeTimer = null;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => redrawers.forEach((f) => f()), 120);
});

// Skupno stanje: profil zamude potrebuje tekoco voznjo IN zgodovino, ki se
// nalagata loceno in z razlicnim ritmom.
const state = { run: null, forecast: null, past: null, pastRuns: 0,
                weather: new Map(), report: null,
                mode: "vlak", network: "zeleznica", agency: null,
                current: null };
// Katera postaja je pod misko -- deljeno med grafoma, da se oznaka ne izgubi
// ob preklopu pogleda.
let hoverSeq = null;

// ---------- ta voznja ----------

const runHeadEl = document.getElementById("run-head");
const runTimelineEl = document.getElementById("run-timeline");
const headsignEl = document.getElementById("train-headsign");
const feedDotEl = document.getElementById("feed-dot");


// Prikaz mora govoriti o tem, kar je pred potnikom. "Vlak je od takrat verjetno
// že pripeljal" pod mestno linijo 47 ni le netočno -- zveni kot napaka programa.

function vehicleNoun() {
  if (!isBus(state.mode)) return "vlak";
  return state.network === "zeleznica" ? "nadomestni prevoz" : "avtobus";
}

function vehicleWord() {
  if (!isBus(state.mode)) return "ta vlak";
  return state.network === "zeleznica" ? "ta prevoz" : "ta avtobus";
}

function caveatText() {
  if (!isBus(state.mode)) {
    return "Meritev ima ločljivost 60 s in je zajeta v prometnem mestu, ne nujno na peronu. "
      + "Vlaki v feedu nimajo GPS — lega je zadnja postaja z meritvijo, ne dejanski položaj.";
  }
  if (state.network === "zeleznica") {
    return "Nadomestni prevoz vozi po cesti in po svojem voznem redu, ne po železniškem. "
      + "Čakaj na postajališču, ne na peronu.";
  }
  return "Mestni avtobus ima GPS, zato je njegova lega na zemljevidu izmerjena, "
    + "ne sklepana. Zamude so iz istega feeda kot pri vlakih, z ločljivostjo ene minute.";
}

// Nazaj na tisto stran, s katere se pride: iskalnik vlakov ali avtobusov.
function applyNetworkWording() {
  const back = document.querySelector(".back-link");
  if (back && state.network === "avtobus") {
    back.setAttribute("href", "/app/bus");
    const label = back.querySelector("span");
    if (label) label.textContent = "avtobusi";
  }
}

// Koliko casa sme meritev veljati za "trenutno". Cez to je vrednost zgodovina
// in prikaz mora to povedati -- "+20 min" ob polnoci, izmerjeno ob 17h, je laz.
const FRESH_S = 20 * 60;

function ageLabel(iso) {
  const min = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (min < 1) return "pravkar";
  if (min < 60) return `pred ${min} min`;
  const h = Math.floor(min / 60);
  return `pred ${h} h ${String(min % 60).padStart(2, "0")} min`;
}

function runHeadHtml(cur) {
  const bus = isBus(state.mode);   // glej vehicleNoun() za besedilo
  const d = cur ? stopDelay(cur) : null;
  const wx = cur ? state.weather.get(cur.stop_seq) : null;
  const color = delayColor(d);
  const atIso = cur ? stopActualIso(cur) : null;
  const ageS = atIso ? (Date.now() - new Date(atIso).getTime()) / 1000 : null;
  const stale = ageS != null && ageS > FRESH_S;

  // Prevoznikovo porocilo pozna prometno mesto, ki ga nas vozni red nima --
  // zamuda se meri tudi tam, kjer vlak ne ustavlja.
  const rep = state.report;

  return `
    <div class="detail-now">
      <div class="detail-now-label">${stale ? "Zadnja znana zamuda" : "Trenutna zamuda"}</div>
      <div class="detail-now-value" style="color:${color}">
        <span class="detail-now-n">${delayLabel(d)}</span><span class="detail-now-unit">min</span>
      </div>
      <div class="detail-now-where">
        ${cur
          ? `izmerjeno na postaji <strong>${escapeHtml(cur.name)}</strong> ob ${hhmm(atIso)}`
          : `za ${vehicleWord()} na ta dan še ni nobene meritve`}
      </div>
      ${atIso ? `<div class="${stale ? "stale-note" : "detail-now-age"}">
        ${stale ? "⚠ " : ""}${escapeHtml(ageLabel(atIso))}${stale
          ? ` — ${vehicleNoun()} je od takrat verjetno že pripeljal`
          : ""}
      </div>` : ""}
      ${rep ? `<div class="detail-report">
        Prevoznik poroča <strong style="color:${delayColor(rep.delay_min * 60)}">${rep.delay_min > 0 ? "+" : ""}${rep.delay_min} min</strong>
        ob ${escapeHtml(rep.event)}u na postajo <strong>${escapeHtml(rep.station)}</strong>
        ${rep.severe ? '<span class="tag">izjemna zamuda</span>' : ""}
      </div>` : ""}
      ${wx && wx.severity != null ? `
        <div class="detail-weather">
          ${weatherIconHtml(wx, 15)}
          <span>razmere <strong style="color:${severityColor(wx.severity_label)}">${wx.severity}/10</strong> · ${escapeHtml(wx.severity_label)}</span>
        </div>
        <div class="detail-weather-raw">${escapeHtml(weatherSummary(wx))}</div>` : ""}
      <div class="detail-caveat">
        ${caveatText()}
      </div>
    </div>
  `;
}

// Postanek, ki ga je potnik izbral -- tisti, na katerem stoji. Iscemo po
// imenu, ker isto ime nosi vec `stop_id` (mestno postajalisce ima svojega za
// vsako smer) in ker naslov nosi ime, ne ida.
function yourStop(stops) {
  if (!URL_STATION || !stops) return null;
  const want = fold(URL_STATION);
  return stops.find((s) => fold(s.name) === want) || null;
}

// "Kdaj pride po mene in koliko bo takrat zamujal" -- edino vprasanje, ki ga
// ima potnik na peronu. Zato je to prva stvar v oknu, nad vsem drugim.
function yourStopHtml(stops, forecast, current) {
  const s = yourStop(stops);
  if (!s) return "";
  const passed = current && s.stop_seq <= current.stop_seq;
  const f = (forecast || []).find((x) => x.stop_seq === s.stop_seq);
  const schedIso = s.sched_dep || s.sched_arr;

  let d = null;
  let kdaj = null;
  let znak = "";
  if (passed) {
    d = stopDelay(s);
    kdaj = stopActualIso(s);
    znak = "izmerjeno";
  } else if (f) {
    d = f.predicted_delay_s;
    kdaj = schedIso && d != null
      ? new Date(new Date(schedIso).getTime() + d * 1000).toISOString() : schedIso;
    znak = f.n_samples > 0 ? `ocena · mediana ${pluralRuns(f.n_samples)}` : "ocena";
  } else {
    kdaj = schedIso;
    znak = "po voznem redu — ocene še ni";
  }
  const color = delayColor(d);
  const sched = hhmm(schedIso);
  const cas = hhmm(kdaj);

  return `
    <div class="yours">
      <div class="yours-label">Pri tebi — ${escapeHtml(s.name)}</div>
      <div class="yours-line">
        <span class="yours-time" style="color:${color}">${cas}</span>
        ${cas !== sched ? `<span class="yours-sched">${sched}</span>` : ""}
        <span class="yours-delay" style="color:${color}">${delayLabel(d)} min</span>
      </div>
      <div class="yours-tag">${escapeHtml(znak)}${passed
        ? ` — ${vehicleNoun()} je tu že bil` : ""}</div>
    </div>`;
}

async function loadReport() {
  // Zadnje porocilo prevoznika o tej voznji: koliko in KJE. Prometno mesto
  // pogosto ni voznoredni postanek, zato ga iz `run` ni mogoce dobiti.
  try {
    const r = await fetch(`/api/train/${ENC}/reports${DATE_Q}`).then((x) => (x.ok ? x.json() : null));
    const list = (r && r.reports) || [];
    state.report = list.length ? list[list.length - 1] : null;
  } catch (err) {
    state.report = null;
  }
}

async function loadAlerts() {
  // Edini vir odgovora, ZAKAJ vlak zamuja. Vse drugo v bazi pove le koliko.
  const box = document.getElementById("train-alerts");
  try {
    const list = await fetch(`/api/train/${ENC}/alerts`).then((r) => (r.ok ? r.json() : []));
    if (!list.length) { box.innerHTML = ""; return; }
    box.innerHTML = `<details class="alert-box"${list.length <= 2 ? " open" : ""}>
      <summary class="alert-head">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M12 9v5M12 17.5v.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"></path>
        </svg>
        Obvestila o ovirah na tej poti
        <span class="alert-count">— ${list.length}</span>
      </summary>
      <div class="alert-list">${list.map((a) => `
        <div class="alert-item">
          <strong>${escapeHtml(a.header || "")}</strong>
          <div class="alert-meta">${escapeHtml(a.effect_label || "")}${a.cause_label ? ` · ${escapeHtml(a.cause_label)}` : ""}
          ${a.url ? ` · <a href="${escapeHtml(a.url)}" target="_blank" rel="noopener">obvestilo SŽ</a>` : ""}</div>
          <div class="alert-body adv-only">${escapeHtml((a.description || "").slice(0, 400))}</div>
        </div>`).join("")}</div>
    </details>`;
  } catch (err) {
    box.innerHTML = "";
  }
}

async function loadRun() {
  try {
    await loadReport();
    const { run, forecast, current } = await fetchRunAndForecast(TRAIN_NO, URL_DATE, URL_TRIP);
    // Nadomestni prevoz mora biti viden v naslovu, ne sele v vrstici postaj:
    // kdor pride sem s povezave, mora takoj vedeti, da caka avtobus.
    state.mode = run.mode;
    state.network = run.network || "zeleznica";
    state.agency = run.agency || null;
    if (isBus(run.mode)) {
      document.getElementById("train-mode").innerHTML = lineBadgeHtml(run);
    }
    applyNetworkWording();
    state.run = run;
    state.forecast = forecast;
    state.current = current;
    runHeadEl.innerHTML = yourStopHtml(run.stops, forecast, current) + runHeadHtml(current);
    renderTimeline();
    renderProfile();
  } catch (err) {
    console.error("vožnje ni bilo mogoče naložiti", err);
    runHeadEl.innerHTML = "";
    runTimelineEl.innerHTML =
      '<div class="empty-state">za to vožnjo na ta dan ni podatkov</div>';
    refreshFeedDot();   // zahteva ni uspela -- naj pika pove, kaj ve
  }
}

// Casovnica se med pogledoma razlikuje, zato je svoja funkcija: preklop je
// mora prerisati, ne le odkriti skritih elementov.
function renderTimeline() {
  const run = state.run;
  if (!run) return;
  const yours = yourStop(run.stops);
  runTimelineEl.innerHTML =
    runTimelineHtml(run.stops, state.forecast, state.weather, {
      aheadOnly: !document.body.classList.contains("is-advanced"),
      highlight: yours ? yours.stop_seq : null,
    }) +
    `<div class="detail-foot">${escapeHtml(run.service_date)} · ${run.stops.length} postaj</div>`;
}

// ---------- zgodovina: stevilke ----------

function tileHtml(label, value, sub, color) {
  return `
    <div class="tile">
      <div class="tile-label">${escapeHtml(label)}</div>
      <div class="tile-value"${color ? ` style="color:${color}"` : ""}>${value}</div>
      <div class="tile-sub">${escapeHtml(sub || "")}</div>
    </div>
  `;
}

function renderTiles(h) {
  const n = h.runs_observed || 0;
  const s = h.summary || {};
  if (!n) {
    document.getElementById("hist-tiles").innerHTML =
      '<div class="empty-state">za to pot še ni nobene zajete vožnje</div>';
    return;
  }
  // Pri eni sami voznji mediana ni mediana -- povej, kaj stevilka v resnici je.
  const medLabel = n === 1 ? "Končna zamuda" : "Mediana končne zamude";
  const tiles = [
    tileHtml(medLabel, delayLabel(s.median_final_s), pluralRuns(n), delayColor(s.median_final_s)),
    tileHtml("Najslabša vožnja", delayLabel(s.worst_final_s), "končna zamuda", delayColor(s.worst_final_s)),
    tileHtml("Delež točnih", `${Math.round((s.on_time_share || 0) * 100)} %`,
             "končna zamuda do 5 min"),
  ];
  if (n >= 5) {
    tiles.splice(2, 0, tileHtml("p90", delayLabel(s.p90_final_s), "9 od 10 voženj do tega",
                                delayColor(s.p90_final_s)));
  }
  document.getElementById("hist-tiles").innerHTML = tiles.join("");
}

// ---------- skupno: tarca za misko cez vso visino ----------

// Pika s polmerom 4,5 px je pretezka tarca -- na 29 postajah je zadetek
// loterija. Vsaka postaja dobi nevidno obmocje cez vso visino grafa.
function addHoverBands(svg, xs, top, height, seqs, onHover) {
  if (xs.length < 2) return;
  const step = (xs[xs.length - 1] - xs[0]) / (xs.length - 1);
  xs.forEach((cx, i) => {
    const band = svgEl("rect", {
      x: cx - step / 2, y: top, width: step, height,
      fill: seqs[i] === hoverSeq ? "rgba(255,255,255,0.035)" : "transparent",
    });
    band.addEventListener("mousemove", (ev) => {
      if (hoverSeq !== seqs[i]) {
        hoverSeq = seqs[i];
        redrawers.forEach((f) => f());
      }
      onHover(i, ev);
    });
    band.addEventListener("mouseleave", () => {
      hideTip();
    });
    svg.appendChild(band);
  });
}

function crosshair(svg, x, top, bottom) {
  svg.appendChild(svgEl("line", {
    x1: x, x2: x, y1: top, y2: bottom,
    stroke: "#3d434f", "stroke-width": 1, "stroke-dasharray": "3 3",
  }));
}

function weatherTipRows(w) {
  if (!w || w.temp_c == null) return "";
  const head = w.severity == null ? "" :
    `<div class="tt-row"><span>razmere</span><b style="color:${severityColor(w.severity_label)}">${w.severity}/10 ${escapeHtml(w.severity_label)}</b></div>`;
  // Indeks brez razclenitve je crna skatla -- iz cesa je sestavljen, mora biti vidno.
  const parts = (w.severity_parts || []).map((x) =>
    `<div class="tt-row is-part"><span>${escapeHtml(x.what)}</span><b>+${x.points}</b></div>`).join("");
  const raw = (w.snowfall_cm || 0) > 0
    ? `<div class="tt-row"><span>sneg</span><b>${num(w.snowfall_cm)} cm</b></div>`
    : `<div class="tt-row"><span>padavine</span><b>${num(w.precip_mm)} mm/h</b></div>`;
  return head + parts + `<div class="tt-split"></div>` + raw +
    `<div class="tt-row"><span>temperatura</span><b>${num(w.temp_c)} °C</b></div>` +
    `<div class="tt-row"><span>sunki vetra</span><b>${num(w.wind_gust_kmh, 0)} km/h</b></div>`;
}

// ---------- graf 1: zamuda po VSEH postajah poti ----------

const KIND = {
  measured: { label: "izmerjeno" },
  estimate: { label: "ocena (prenos zamude)" },
  none: { label: "brez podatka" },
};

function profilePoints() {
  // Vse postaje poti, ne samo tiste z meritvijo -- graf mora pokazati celo pot.
  const stops = state.run.stops;
  const cur = lastMeasured(stops);
  const fc = new Map((state.forecast || []).map((f) => [f.stop_seq, f]));
  const past = state.past || new Map();

  return stops.map((s) => {
    const p = {
      seq: s.stop_seq, name: s.name,
      past: past.get(s.stop_seq) || null,
      wx: state.weather.get(s.stop_seq) || null,
    };
    if (cur && s.stop_seq <= cur.stop_seq) {
      if (stopActualIso(s)) { p.kind = "measured"; p.value = stopDelay(s); }
      else { p.kind = "none"; p.value = null; }
    } else {
      // Naprej po progi vedno nasa ocena, tudi ce feed ze ima vrednost:
      // izmerjeno je prevoznikova napoved za postanke naprej precej slabsa
      // od prenosa trenutne zamude (backtest.py). Njegovo stevilko obdrzimo
      // v oknu ob dotiku, da ni skrita.
      const f = fc.get(s.stop_seq);
      p.kind = f ? "estimate" : "none";
      p.value = f ? f.predicted_delay_s : null;
      p.samples = f ? f.n_samples : 0;
      p.feedSaid = stopDelay(s);
    }
    return p;
  });
}

function stopTipHtml(p) {
  const rows = [];
  if (p.value != null) {
    rows.push(`<div class="tt-row"><span>${KIND[p.kind].label}</span><b>${delayLabel(p.value)} min</b></div>`);
    if (p.kind === "estimate") {
      rows.push(`<div class="tt-note">${p.samples > 0
        ? `mediana ${escapeHtml(pluralRuns(p.samples))}`
        : "le prenos trenutne zamude, brez zgodovine"}</div>`);
      if (p.feedSaid != null) {
        rows.push(`<div class="tt-row is-part"><span>feed pravi</span><b>${delayLabel(p.feedSaid)} min</b></div>`);
      }
    }
  } else {
    rows.push('<div class="tt-row"><span>zamuda</span><b>—</b></div>');
  }
  if (p.past) {
    rows.push(`<div class="tt-row"><span>povprečje preteklih</span><b>${delayLabel(p.past.mean_s)} min</b></div>`);
    rows.push(`<div class="tt-note">${escapeHtml(pluralRuns(p.past.n))}</div>`);
  }
  const wxRows = weatherTipRows(p.wx);
  return `<div class="tt-title">${escapeHtml(p.name)}</div>${rows.join("")}` +
    (wxRows ? `<div class="tt-split"></div>${wxRows}` : "");
}

// Vreme ni svoj pogled: v isti sliki lezi pod zamudo, ker vprasanje ni "kaksno
// je vreme", ampak "je zamuda tam, kjer je bilo vreme hudo".
//
// Lestvici sta dve in namenoma nista pomesani. Validator palete pove, zakaj:
// rumena razmer (#d9b33c) proti svetli oranzni zamud (#f2a87e) je pri deutanu
// ΔE 5,5 -- premalo, ce bi bili v istem registru. Zato zamuda ostane crta s
// pikami zgoraj, razmere pa so stolpci v locenem pasu pod grafom, in vsak
// stolpec od stopnje 4 naprej nosi svojo stevilko: barva sama nikoli ne odloca.
const SEV_STRIP_H = 38;
const SEV_GAP = 18;

function drawProfile(w, pts) {
  const hasWx = pts.some((p) => p.wx && p.wx.severity != null);
  const M = { t: 26, r: 16, b: 34, l: 42 };
  const ih = 200;
  const stripTop = M.t + ih + SEV_GAP;
  const stripBot = stripTop + SEV_STRIP_H;
  const bottom = hasWx ? stripBot : M.t + ih;
  const H = bottom + M.b;
  const iw = Math.max(40, w - M.l - M.r);
  const svg = svgEl("svg", { width: w, height: H, role: "img" });

  const vals = [];
  for (const p of pts) {
    if (p.value != null) vals.push(p.value);
    if (p.past && p.past.mean_s != null) vals.push(p.past.mean_s);
  }
  const maxV = Math.max(60, ...vals);
  const minV = Math.min(0, ...vals);
  const yTop = Math.ceil(maxV / 60 / 5) * 5 * 60 || 300;
  const yBot = Math.floor(minV / 60 / 5) * 5 * 60;
  const span = yTop - yBot || 300;
  const x = (i) => M.l + (pts.length === 1 ? iw / 2 : (i * iw) / (pts.length - 1));
  const y = (v) => M.t + ih - ((v - yBot) / span) * ih;

  const ticks = 5;
  for (let i = 0; i <= ticks; i += 1) {
    const v = yBot + (span / ticks) * i;
    svg.appendChild(svgEl("line", {
      x1: M.l, x2: M.l + iw, y1: y(v), y2: y(v),
      stroke: Math.abs(v) < 1 ? INK_AXIS : INK_GRID, "stroke-width": 1,
    }));
    svg.appendChild(svgEl("text", {
      x: M.l - 8, y: y(v) + 4, "text-anchor": "end",
      fill: INK_AXIS, "font-size": 10, "font-family": "'IBM Plex Mono', monospace",
    }, `${Math.round(v / 60)}`));
  }
  svg.appendChild(svgEl("text", {
    x: M.l - 8, y: M.t - 11, "text-anchor": "end",
    fill: INK_AXIS, "font-size": 9, "font-family": "'IBM Plex Sans', sans-serif",
  }, "min"));

  const hoverIdx = pts.findIndex((p) => p.seq === hoverSeq);
  if (hoverIdx >= 0) crosshair(svg, x(hoverIdx), M.t, bottom);

  // povprecje preteklih voznj -- referenca v ozadju, brez markerjev
  const pastPts = pts.map((p, i) => (p.past && p.past.mean_s != null ? [i, p.past.mean_s] : null));
  let segment = [];
  for (const item of [...pastPts, null]) {
    if (item) { segment.push(`${x(item[0])},${y(item[1])}`); continue; }
    if (segment.length > 1) {
      svg.appendChild(svgEl("polyline", {
        points: segment.join(" "), fill: "none", stroke: PAST_COLOR, "stroke-width": 1.5,
        "stroke-dasharray": "5 4", "stroke-linejoin": "round",
      }));
    }
    segment = [];
  }

  // tekoca voznja -- polna crta skozi meritve, crtkana skozi ocene
  for (let i = 0; i < pts.length - 1; i += 1) {
    const a = pts[i];
    const b = pts[i + 1];
    if (a.value == null || b.value == null) continue;
    const guessed = a.kind !== "measured" || b.kind !== "measured";
    svg.appendChild(svgEl("line", {
      x1: x(i), y1: y(a.value), x2: x(i + 1), y2: y(b.value),
      stroke: guessed ? ESTIMATE_COLOR : INK_LINE, "stroke-width": 2,
      "stroke-dasharray": guessed ? "4 4" : null, "stroke-linecap": "round",
    }));
  }

  pts.forEach((p, i) => {
    if (p.value == null) return;
    const filled = p.kind !== "estimate";
    const on = p.seq === hoverSeq;
    svg.appendChild(svgEl("circle", {
      cx: x(i), cy: y(p.value), r: on ? 7 : 4.5,
      fill: filled ? (p.kind === "measured" ? delayColor(p.value) : ESTIMATE_COLOR) : SURFACE,
      stroke: on ? "#e7eaf0" : (filled ? SURFACE : ESTIMATE_COLOR), "stroke-width": 2,
    }));
  });

  // neposredne oznake samo tam, kjer nekaj povedo: vrh in cilj
  const withVal = pts.map((p, i) => [p, i]).filter(([p]) => p.value != null);
  if (withVal.length) {
    const maxIdx = withVal.reduce((best, cur) => (cur[0].value > best[0].value ? cur : best))[1];
    const lastIdx = withVal[withVal.length - 1][1];
    new Set([maxIdx, lastIdx]).forEach((i) => {
      svg.appendChild(svgEl("text", {
        x: x(i), y: y(pts[i].value) - 10,
        "text-anchor": i === pts.length - 1 ? "end" : "middle",
        fill: "#e7eaf0", "font-size": 11, "font-weight": 600,
        "font-family": "'IBM Plex Mono', monospace",
      }, delayLabel(pts[i].value)));
    });
  }

  if (hasWx) drawSeverityStrip(svg, pts, x, iw, M.l, stripTop, stripBot);

  drawStopAxis(svg, pts, x, iw, H);

  addHoverBands(svg, pts.map((_, i) => x(i)), M.t - 6, bottom - M.t + 12,
                pts.map((p) => p.seq),
                (i, ev) => showTip(stopTipHtml(pts[i]), ev));
  return svg;
}

// Na osi so doslej stali samo zacetek in konec. Pri 25 postajah to pomeni,
// da bralec vidi skok zamude, ne more pa povedati, KJE se je zgodil -- prav
// to pa je vprasanje. Vmesne oznake postavimo tako gosto, kot dopusca sirina.
const AXIS_LABEL_PX = 74;

function drawStopAxis(svg, pts, x, iw, H) {
  const y = H - 12;
  const put = (i, anchor) => {
    const name = pts[i].name.length > 14 ? `${pts[i].name.slice(0, 13)}…` : pts[i].name;
    svg.appendChild(svgEl("text", {
      x: x(i), y, "text-anchor": anchor,
      fill: pts[i].seq === hoverSeq ? "#e7eaf0" : INK_AXIS,
      "font-size": 10, "font-family": "'IBM Plex Sans', sans-serif",
    }, name));
  };
  put(0, "start");
  if (pts.length > 1) put(pts.length - 1, "end");

  const fits = Math.floor(iw / AXIS_LABEL_PX);
  if (fits < 3 || pts.length < 4) return;
  const step = Math.ceil((pts.length - 1) / fits);
  for (let i = step; i < pts.length - 1; i += step) {
    // Ob krajiscih ne podvajaj -- oznaki bi se prekrivali.
    if (x(i) - x(0) < AXIS_LABEL_PX || x(pts.length - 1) - x(i) < AXIS_LABEL_PX) continue;
    put(i, "middle");
  }
}


function drawSeverityStrip(svg, pts, x, iw, left, top, bot) {
  svg.appendChild(svgEl("line", {
    x1: left, x2: left + iw, y1: bot, y2: bot, stroke: INK_AXIS, "stroke-width": 1,
  }));
  svg.appendChild(svgEl("text", {
    x: left + iw, y: top - 5, "text-anchor": "end", fill: INK_AXIS, "font-size": 9,
    "font-family": "'IBM Plex Sans', sans-serif",
  }, `razmere ob ${vehicleNoun() === "vlak" ? "vlaku" : "vozilu"}, 0–10`));

  const step = pts.length > 1 ? iw / (pts.length - 1) : iw;
  const bw = Math.max(2, Math.min(18, step * 0.62));
  const worst = pts.reduce((a, b) =>
    ((b.wx && b.wx.severity != null && (!a || b.wx.severity > a.wx.severity)) ? b : a), null);

  pts.forEach((p, i) => {
    if (!p.wx || p.wx.severity == null) return;
    const h = Math.max(1.5, (p.wx.severity / 10) * (bot - top));
    const on = p.seq === hoverSeq;
    svg.appendChild(svgEl("rect", {
      x: x(i) - bw / 2, y: bot - h, width: bw, height: h, rx: 2,
      fill: severityColor(p.wx.severity_label),
      stroke: on ? "#e7eaf0" : "none", "stroke-width": on ? 1.5 : 0,
    }));
    // Stevilka na vseh, ki nekaj pomenijo -- ce se ne prilegajo vse, vsaj najhujsa.
    const fits = step >= 17;
    if (p.wx.severity >= 4 && (fits || p === worst)) {
      svg.appendChild(svgEl("text", {
        x: x(i), y: bot - h - 4, "text-anchor": "middle",
        fill: "#9aa3b0", "font-size": 9, "font-family": "'IBM Plex Mono', monospace",
      }, String(p.wx.severity)));
    }
  });
}

function profileLegendHtml(pts) {
  const kinds = new Set(pts.filter((p) => p.value != null).map((p) => p.kind));
  const items = [];
  if (kinds.has("measured")) {
    items.push(`<span class="lg"><span class="lg-ramp"></span>izmerjeno (odtenek = velikost zamude)</span>`);
  }
  if (kinds.has("eta")) {
    items.push(`<span class="lg"><span class="lg-dot" style="background:${ESTIMATE_COLOR}"></span>napoved prevoznika</span>`);
  }
  if (kinds.has("estimate")) {
    items.push(`<span class="lg"><span class="lg-dot is-hollow" style="border-color:${ESTIMATE_COLOR}"></span>ocena (prenos zamude)</span>`);
  }
  if (pts.some((p) => p.past)) {
    items.push(`<span class="lg"><span class="lg-dash" style="border-color:${PAST_COLOR}"></span>povprečje preteklih voženj</span>`);
  }
  if (pts.some((p) => p.wx && p.wx.severity != null)) {
    items.push('<span class="lg-break"></span><span class="lg is-cap">stolpci spodaj</span>');
    for (const lab of SEVERITY_ORDER) {
      items.push(`<span class="lg"><span class="lg-swatch" style="background:${SEVERITY_STYLE[lab]}"></span>${lab}</span>`);
    }
  }
  return items.join("");
}

const WEATHER_NOTE =
  "Stopnja razmer 0–10 je sešteta iz padavin, snega, sunkov vetra, megle, nevihte in mraza — " +
  "razčlenitev je vidna ob dotiku postaje. <strong>Ni napoved zamude</strong> in ne trdi vzroka: " +
  "opisuje vreme. Vrednost je modelska za celico 8 × 8 km ob uri, ko je vlak na tej postaji, " +
  "ne meritev na peronu.";

function renderProfile() {
  const sub = document.getElementById("profile-sub");
  const el = document.getElementById("profile-chart");
  const legend = document.getElementById("profile-legend");
  const note = document.getElementById("weather-note");
  if (!state.run) return;

  const pts = profilePoints();
  // Dovolj je, da ima tocke ena od obeh krivulj: pred odhodom je tekoca prazna,
  // pretekla pa ze pove, kje ta vlak obicajno izgubi cas.
  const nNow = pts.filter((p) => p.value != null).length;
  const nPast = pts.filter((p) => p.past && p.past.mean_s != null).length;
  if (Math.max(nNow, nPast) < 2) {
    sub.textContent = "";
    legend.innerHTML = "";
    note.hidden = true;
    el.innerHTML = '<div class="empty-state">premalo točk za profil</div>';
    return;
  }

  const withWx = pts.filter((p) => p.wx && p.wx.severity != null);
  const worst = withWx.length ? withWx.reduce((a, b) => (b.wx.severity > a.wx.severity ? b : a)) : null;
  sub.textContent = (state.pastRuns
    ? `celotna pot, ${pts.length} postaj · povprečje iz ${pluralRuns(state.pastRuns)} pred današnjo`
    : `celotna pot, ${pts.length} postaj · preteklih voženj za primerjavo še ni`)
    + (worst ? ` · najhujše razmere ${worst.wx.severity}/10 na postaji ${worst.name}` : "")
    + " · miška kjerkoli nad stolpcem postaje";
  legend.innerHTML = profileLegendHtml(pts);
  note.innerHTML = WEATHER_NOTE;
  note.hidden = !withWx.length;
  mountChart(el, (w) => drawProfile(w, pts));
}

// ---------- graf 2: koncna zamuda po dnevih ----------

function drawRuns(w, runs) {
  const H = 190;
  const M = { t: 14, r: 12, b: 30, l: 40 };
  const iw = Math.max(40, w - M.l - M.r);
  const ih = H - M.t - M.b;
  const svg = svgEl("svg", { width: w, height: H, role: "img" });

  const ticks = niceTicks(Math.max(60, ...runs.map((r) => r.final_delay_s)), 5);
  const yMax = ticks.top;
  const y = (v) => M.t + ih - (v / yMax) * ih;
  const step = iw / runs.length;
  const bw = Math.min(32, step - 2); // 2px reze med stolpci

  for (const v of ticks.values) {
    svg.appendChild(svgEl("line", {
      x1: M.l, x2: M.l + iw, y1: y(v), y2: y(v),
      stroke: v === 0 ? INK_AXIS : INK_GRID, "stroke-width": 1,
    }));
    svg.appendChild(svgEl("text", {
      x: M.l - 8, y: y(v) + 4, "text-anchor": "end",
      fill: INK_AXIS, "font-size": 10, "font-family": "'IBM Plex Mono', monospace",
    }, `${Math.round(v / 60)}`));
  }

  runs.forEach((r, i) => {
    const cx = M.l + step * i + step / 2;
    const h = Math.max(2, M.t + ih - y(r.final_delay_s));
    const rect = svgEl("rect", {
      x: cx - bw / 2, y: y(r.final_delay_s), width: bw, height: h,
      rx: 4, fill: delayColor(r.final_delay_s),
    });
    rect.addEventListener("mousemove", (ev) => showTip(
      `<div class="tt-title">${escapeHtml(r.service_date)}</div>` +
      `<div class="tt-row"><span>končna</span><b>${delayLabel(r.final_delay_s)} min</b></div>` +
      `<div class="tt-row"><span>največja med potjo</span><b>${delayLabel(r.max_delay_s)} min</b></div>` +
      `<div class="tt-note">${r.stops_observed} postaj z meritvijo</div>`, ev));
    rect.addEventListener("mouseleave", hideTip);
    svg.appendChild(rect);

    svg.appendChild(svgEl("text", {
      x: cx, y: H - 10, "text-anchor": "middle",
      fill: INK_AXIS, "font-size": 10, "font-family": "'IBM Plex Sans', sans-serif",
    }, dayLabel(r.service_date)));
  });
  return svg;
}

// ---------- graf 3: hitrost po odsekih (na zahtevo) ----------

function drawSpeeds(w, segs) {
  const rowH = 30;
  // Levi rob po najdaljsem imenu odseka -- fiksnih 148 px je rezalo zacetke.
  const longest = segs.reduce((n, s) => Math.max(n, `${s.from} → ${s.to}`.length), 0);
  const M = { t: 6, r: 108, b: 6, l: Math.min(270, Math.max(150, longest * 6.1 + 14)) };
  const H = M.t + M.b + segs.length * rowH;
  const iw = Math.max(40, w - M.l - M.r);
  const svg = svgEl("svg", { width: w, height: H, role: "img" });
  const maxV = Math.max(...segs.map((s) => Math.max(s.actual_kmh, s.sched_kmh))) * 1.05;

  segs.forEach((s, i) => {
    const top = M.t + i * rowH;
    const cy = top + rowH / 2;
    svg.appendChild(svgEl("text", {
      x: M.l - 10, y: cy + 4, "text-anchor": "end",
      fill: "#9aa3b0", "font-size": 11, "font-family": "'IBM Plex Sans', sans-serif",
    }, `${s.from} → ${s.to}`));

    const bw = (s.actual_kmh / maxV) * iw;
    const bar = svgEl("rect", {
      x: M.l, y: cy - 7, width: Math.max(2, bw), height: 14, rx: 4, fill: INK_BAR,
    });
    bar.addEventListener("mousemove", (ev) => showTip(
      `<div class="tt-title">${escapeHtml(s.from)} → ${escapeHtml(s.to)}</div>` +
      `<div class="tt-row"><span>izmerjeno</span><b>${s.actual_kmh.toFixed(1)} km/h</b></div>` +
      `<div class="tt-row"><span>vozni red</span><b>${s.sched_kmh.toFixed(1)} km/h</b></div>` +
      `<div class="tt-row"><span>odsek</span><b>${s.km.toFixed(1)} km</b></div>` +
      `<div class="tt-note">${escapeHtml(pluralRuns(s.n))}</div>`, ev));
    bar.addEventListener("mouseleave", hideTip);
    svg.appendChild(bar);

    // vozni red kot referenca, ne kot druga serija
    const rx = M.l + (s.sched_kmh / maxV) * iw;
    svg.appendChild(svgEl("line", {
      x1: rx, x2: rx, y1: cy - 11, y2: cy + 11, stroke: INK_AXIS, "stroke-width": 2,
    }));

    // Stolpec se imenuje "hitrost po odsekih", zato mora stevilka biti
    // HITROST. Prej je tu pisalo odstopanje od voznega reda (+/-) -- to je
    // druga kolicina in ob besedi "km/h" jo je bilo brati kot hitrost samo.
    // Odstopanje ostane, a manjse in za njo.
    const diff = s.actual_kmh - s.sched_kmh;
    svg.appendChild(svgEl("text", {
      x: w - 46, y: cy + 4, "text-anchor": "end",
      fill: "#c9d1dc", "font-size": 11.5, "font-family": "'IBM Plex Mono', monospace",
    }, `${s.actual_kmh.toFixed(0)} km/h`));
    svg.appendChild(svgEl("text", {
      x: w - 6, y: cy + 4, "text-anchor": "end",
      fill: Math.abs(diff) < 1 ? "#79828f" : diff < 0 ? "#dd6a26" : "#5aa87d",
      "font-size": 10, "font-family": "'IBM Plex Mono', monospace",
    }, Math.abs(diff) < 0.5 ? "0"
        : `${diff > 0 ? "+" : "−"}${Math.abs(diff).toFixed(0)}`));
  });
  return svg;
}

function medianOf(xs) {
  const a = [...xs].sort((p, q) => p - q);
  const m = Math.floor(a.length / 2);
  return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
}

function aggregateSpeeds(rows) {
  const by = new Map();
  for (const r of rows) {
    const key = `${r.from}→${r.to}`;
    let g = by.get(key);
    if (!g) {
      g = { from: r.from, to: r.to, km: r.km, sched_kmh: r.sched_kmh, actual: [] };
      by.set(key, g);
    }
    g.actual.push(r.actual_kmh);
  }
  return [...by.values()].map((g) => ({
    from: g.from, to: g.to, km: g.km, sched_kmh: g.sched_kmh,
    actual_kmh: medianOf(g.actual), n: g.actual.length,
  }));
}

let speedsLoaded = false;

async function loadSpeeds() {
  const sub = document.getElementById("speeds-sub");
  const el = document.getElementById("speeds-chart");
  try {
    const raw = await fetch(`/api/speeds?train_no=${ENC}`).then((r) => r.json());
    const segs = aggregateSpeeds(raw);
    if (!segs.length) {
      sub.textContent = "";
      el.innerHTML = '<div class="empty-state">ni odseka nad 5 km z dvema meritvama</div>';
      return;
    }
    const shown = segs.slice(0, 12);
    sub.textContent = "stolpec in številka = izmerjena hitrost, črtica = vozni red, desno odstopanje v km/h; samo odseki nad 5 km"
      + (segs.length > shown.length ? ` · prikazanih ${shown.length} od ${segs.length}` : "");
    mountChart(el, (w) => drawSpeeds(w, shown));
  } catch (err) {
    console.error("hitrosti ni bilo mogoče naložiti", err);
    el.innerHTML = '<div class="empty-state">hitrosti ni bilo mogoče naložiti</div>';
  }
}

// ---------- hitrost: zlozena vsebina ----------

// Hitrost ni svoj pogled in tudi ne zavihek ob zamudi: je isti podatek v drugi
// enoti, zato lezi spodaj zaprta in se nalozi sele, ko jo kdo odpre.
const speedsDrawer = document.getElementById("speeds-drawer");

speedsDrawer.addEventListener("toggle", () => {
  if (!speedsDrawer.open) return;
  if (!speedsLoaded) {
    speedsLoaded = true;
    loadSpeeds();
    return;
  }
  // Zaprt graf ima sirino 0 -- ob odprtju ga je treba izrisati znova.
  requestAnimationFrame(() => redrawers.forEach((f) => f()));
});

// ---------- vreme ----------

async function loadWeather() {
  try {
    const res = await fetch(`/api/train/${ENC}/weather${DATE_Q}`);
    if (!res.ok) return;
    const data = await res.json();
    state.weather = new Map((data.stops || []).map((s) => [s.stop_seq, s]));
    // Vreme pride pozneje kot voznja -- kar je ze izrisano, je treba osveziti.
    if (state.run) {
      const cur = lastMeasured(state.run.stops);
      runHeadEl.innerHTML = runHeadHtml(cur);
      runTimelineEl.innerHTML = runTimelineHtml(state.run.stops, state.forecast, state.weather) +
        `<div class="detail-foot">${escapeHtml(state.run.service_date)} · ${state.run.stops.length} postaj</div>`;
      renderProfile();
    }
  } catch (err) {
    console.error("vremena ni bilo mogoče naložiti", err);
  }
}

// ---------- zgodovina ----------

async function loadHistory() {
  let h;
  const today = state.run ? state.run.service_date : null;
  try {
    const q = today ? `&exclude_date=${encodeURIComponent(today)}` : "";
    h = await fetch(`/api/train/${ENC}/history?days=90${q}`).then((r) => r.json());
  } catch (err) {
    console.error("zgodovine ni bilo mogoče naložiti", err);
    return;
  }

  state.pastRuns = h.runs_observed || 0;
  state.past = new Map((h.by_stop || []).map((b) => [b.stop_seq, b]));

  const first = h.runs && h.runs.length ? h.runs[0].service_date : null;
  document.getElementById("hist-note").innerHTML = state.pastRuns
    ? `Zajetih ${escapeHtml(pluralRuns(state.pastRuns))} pred današnjo${first ? `, od ${escapeHtml(first)}` : ""}.` +
      (state.pastRuns < 10 ? " <strong>Premalo za porazdelitev</strong> — številke spodaj opisujejo teh nekaj voženj, ne značilnega dne." : "")
    : "Pred današnjo vožnjo za to pot še ni zajete nobene druge.";

  renderTiles(h);
  renderProfile();

  const runs = (h.runs || []).filter((r) => r.final_delay_s != null);
  const runsSub = document.getElementById("runs-sub");
  const runsEl = document.getElementById("runs-chart");
  if (runs.length >= 3) {
    runsSub.textContent = "ena vožnja = en stolpec";
    mountChart(runsEl, (w) => drawRuns(w, runs));
  } else if (runs.length) {
    // Pod tremi voznjami stolpci ne povedo nic vec kot seznam -- in namigujejo
    // na trend, ki ga ni.
    runsSub.textContent = "premalo voženj za graf — naštete so vse";
    runsEl.innerHTML = runs.map((r) => `
      <div class="run-row">
        <span class="run-date">${escapeHtml(r.service_date)}</span>
        <span class="run-meta">${r.stops_observed} postaj z meritvijo</span>
        <span class="run-value" style="color:${delayColor(r.final_delay_s)}">${delayLabel(r.final_delay_s)}</span>
      </div>`).join("");
  } else {
    runsSub.textContent = "";
    runsEl.innerHTML = '<div class="empty-state">ni druge zajete vožnje</div>';
  }
}

// ---------- smer vlaka iz /api/live, ura ----------

async function loadHeadsign() {
  try {
    const live = await fetch("/api/live").then((r) => r.json());
    const me = live.find((t) => t.train_no === TRAIN_NO);
    if (me && me.headsign) headsignEl.textContent = me.headsign;
  } catch (err) {
    /* smer je postranska -- brez nje stran deluje naprej */
  }
}

function tickClock() {
  const fmt = new Intl.DateTimeFormat("sl-SI", {
    timeZone: "Europe/Ljubljana", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false,
  });
  document.getElementById("clock").textContent = fmt.format(new Date());
}

tickClock();
setInterval(tickClock, 1000);
refreshFeedDot();
pollWhileVisible(refreshFeedDot, 30000);

// Zgodovina rabi datum tekoce voznje, da ga izpusti iz povprecja -- zato sele
// za njo.
// Stare povezave s ?view=hitrost naj se odprejo na hitrosti, ne v prazno.
if (new URLSearchParams(location.search).get("view") === "hitrost") {
  speedsDrawer.open = true;
}

// Preklop pogleda je skupen vsem stranem in zivi v common.js. Grafi se morajo
// ob preklopu prerisati: napreden pogled spremeni sirino stolpca.
const toAdvBtn = document.getElementById("to-advanced");
if (toAdvBtn) {
  toAdvBtn.addEventListener("click", () => {
    // Isti preklop kot v glavi -- klik na gumb mora premakniti tudi njo.
    const b = document.querySelector('#mode-switch [data-mode="advanced"]');
    if (b) b.click();
    document.getElementById("fig-profile").scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

initMode(() => {
  renderTimeline();     // preprosto kaze samo naprej, napredno vso pot
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => redrawers.forEach((f) => f()), 60);
});

loadWeather();
loadAlerts();
loadHeadsign();

// Zgodovina rabi datum tekoce voznje, da ga izpusti iz povprecja ("zajetih N
// PRED danasnjo"), zato sele za prvim `loadRun`. Vzporeden zagon bi danasnjo
// voznjo stel v svoje lastno povprecje.
pollWhileVisible(loadRun, RUN_POLL_MS);
loadRun().then(() => pollWhileVisible(loadHistory, HIST_POLL_MS));
