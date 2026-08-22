"use strict";

// Svoje okno enega vlaka: ta voznja + zgodovina te poti.
// Barve zamud so projektna ORDINALNA lestvica (en odtenek, monotona svetlost) --
// uporabljena samo tam, kjer odtenek pomeni velikost zamude. Kjer meritve ni,
// nastopi rezervirana barva, ki je lestvica ne uporablja.

const TRAIN_NO = document.body.dataset.trainNo;
const ENC = encodeURIComponent(TRAIN_NO);
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
    const w = el.clientWidth;
    if (!w) return;
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
const state = { run: null, forecast: null, past: null, pastRuns: 0 };

// ---------- ta voznja ----------

const runHeadEl = document.getElementById("run-head");
const runTimelineEl = document.getElementById("run-timeline");
const headsignEl = document.getElementById("train-headsign");
const feedDotEl = document.getElementById("feed-dot");

function runHeadHtml(cur) {
  const d = cur ? stopDelay(cur) : null;
  const color = delayColor(d);
  return `
    <div class="detail-now">
      <div class="detail-now-label">Trenutna zamuda</div>
      <div class="detail-now-value" style="color:${color}">
        <span class="detail-now-n">${delayLabel(d)}</span><span class="detail-now-unit">min</span>
      </div>
      <div class="detail-now-where">
        ${cur
          ? `izmerjeno v <strong>${escapeHtml(cur.name)}</strong> ob ${hhmm(stopActualIso(cur))}`
          : "za ta vlak danes še ni nobene meritve"}
      </div>
      <div class="detail-caveat">
        Meritev ima ločljivost 60 s in je zajeta v prometnem mestu, ne nujno na peronu.
        Vlaki v feedu nimajo GPS — lega je zadnja postaja z meritvijo, ne dejanski položaj.
      </div>
    </div>
  `;
}

async function loadRun() {
  try {
    const { run, forecast, current } = await fetchRunAndForecast(TRAIN_NO);
    state.run = run;
    state.forecast = forecast;
    runHeadEl.innerHTML = runHeadHtml(current);
    runTimelineEl.innerHTML = runTimelineHtml(run.stops, forecast) +
      `<div class="detail-foot">${escapeHtml(run.service_date)} · ${run.stops.length} postaj</div>`;
    feedDotEl.classList.remove("stale");
    renderProfile();
  } catch (err) {
    console.error("vožnje ni bilo mogoče naložiti", err);
    runHeadEl.innerHTML = "";
    runTimelineEl.innerHTML = '<div class="empty-state">za ta vlak danes ni podatkov o vožnji</div>';
    feedDotEl.classList.add("stale");
  }
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

// ---------- graf 1: zamuda po VSEH postajah poti ----------

const KIND = {
  measured: { label: "izmerjeno" },
  eta: { label: "napoved prevoznika" },
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
    const p = { seq: s.stop_seq, name: s.name, past: past.get(s.stop_seq) || null };
    if (cur && s.stop_seq <= cur.stop_seq) {
      if (stopActualIso(s)) { p.kind = "measured"; p.value = stopDelay(s); }
      else { p.kind = "none"; p.value = null; }
    } else if (stopActualIso(s)) {
      p.kind = "eta"; p.value = stopDelay(s);
    } else {
      const f = fc.get(s.stop_seq);
      p.kind = f ? "estimate" : "none";
      p.value = f ? f.predicted_delay_s : null;
      p.samples = f ? f.n_samples : 0;
    }
    return p;
  });
}

function pointColor(p) {
  return p.kind === "measured" ? delayColor(p.value) : ESTIMATE_COLOR;
}

function drawProfile(w, pts) {
  const H = 250;
  const M = { t: 16, r: 16, b: 34, l: 42 };
  const iw = Math.max(40, w - M.l - M.r);
  const ih = H - M.t - M.b;
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
    x: M.l - 8, y: M.t - 4, "text-anchor": "end",
    fill: INK_AXIS, "font-size": 9, "font-family": "'IBM Plex Sans', sans-serif",
  }, "min"));

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
    const c = svgEl("circle", {
      cx: x(i), cy: y(p.value), r: 4.5,
      fill: filled ? pointColor(p) : SURFACE,
      stroke: filled ? SURFACE : ESTIMATE_COLOR, "stroke-width": 2,
    });
    c.addEventListener("mousemove", (ev) => {
      const rows = [`<div class="tt-row"><span>${KIND[p.kind].label}</span><b>${delayLabel(p.value)} min</b></div>`];
      if (p.kind === "estimate") {
        rows.push(`<div class="tt-note">${p.samples > 0
          ? `mediana ${escapeHtml(pluralRuns(p.samples))}`
          : "le prenos trenutne zamude, brez zgodovine"}</div>`);
      }
      if (p.past) {
        rows.push(`<div class="tt-row"><span>povprečje preteklih</span><b>${delayLabel(p.past.mean_s)} min</b></div>`);
        rows.push(`<div class="tt-row"><span>mediana preteklih</span><b>${delayLabel(p.past.median_s)} min</b></div>`);
        rows.push(`<div class="tt-note">${escapeHtml(pluralRuns(p.past.n))}</div>`);
      }
      showTip(`<div class="tt-title">${escapeHtml(p.name)}</div>${rows.join("")}`, ev);
    });
    c.addEventListener("mouseleave", hideTip);
    svg.appendChild(c);
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

  // os x: imena postaj so dolga, zato samo zacetek, konec in vrh
  const labels = [[0, "start"], [pts.length - 1, "end"]];
  for (const [i, anchor] of labels) {
    svg.appendChild(svgEl("text", {
      x: x(i), y: H - 12, "text-anchor": anchor === "start" ? "start" : "end",
      fill: INK_AXIS, "font-size": 10, "font-family": "'IBM Plex Sans', sans-serif",
    }, pts[i].name));
  }
  return svg;
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
  return items.join("");
}

function renderProfile() {
  const sub = document.getElementById("profile-sub");
  const el = document.getElementById("profile-chart");
  const legend = document.getElementById("profile-legend");
  if (!state.run) return;

  const pts = profilePoints();
  // Dovolj je, da ima tocke ena od obeh krivulj: pred odhodom je tekoca prazna,
  // pretekla pa ze pove, kje ta vlak obicajno izgubi cas.
  const nNow = pts.filter((p) => p.value != null).length;
  const nPast = pts.filter((p) => p.past && p.past.mean_s != null).length;
  if (Math.max(nNow, nPast) < 2) {
    sub.textContent = "";
    legend.innerHTML = "";
    el.innerHTML = '<div class="empty-state">premalo točk za profil</div>';
    return;
  }
  sub.textContent = state.pastRuns
    ? `celotna pot, ${pts.length} postaj · povprečje iz ${pluralRuns(state.pastRuns)} pred današnjo`
    : `celotna pot, ${pts.length} postaj · preteklih voženj za primerjavo še ni`;
  legend.innerHTML = profileLegendHtml(pts);
  mountChart(el, (w) => drawProfile(w, pts));
}

// ---------- graf 2: koncna zamuda po dnevih ----------

function drawRuns(w, runs) {
  const H = 190;
  const M = { t: 14, r: 12, b: 30, l: 40 };
  const iw = Math.max(40, w - M.l - M.r);
  const ih = H - M.t - M.b;
  const svg = svgEl("svg", { width: w, height: H, role: "img" });

  const maxV = Math.max(60, ...runs.map((r) => r.final_delay_s));
  const yMax = Math.ceil(maxV / 60 / 5) * 5 * 60 || 300;
  const y = (v) => M.t + ih - (v / yMax) * ih;
  const step = iw / runs.length;
  const bw = Math.min(32, step - 2); // 2px reze med stolpci

  for (let i = 0; i <= 4; i += 1) {
    const v = (yMax / 4) * i;
    svg.appendChild(svgEl("line", {
      x1: M.l, x2: M.l + iw, y1: y(v), y2: y(v),
      stroke: i === 0 ? INK_AXIS : INK_GRID, "stroke-width": 1,
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
  const M = { t: 6, r: 96, b: 6, l: 148 };
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

    const diff = s.actual_kmh - s.sched_kmh;
    svg.appendChild(svgEl("text", {
      x: w - 6, y: cy + 4, "text-anchor": "end",
      fill: "#9aa3b0", "font-size": 11, "font-family": "'IBM Plex Mono', monospace",
    }, `${diff >= 0 ? "+" : "−"}${Math.abs(diff).toFixed(1)} km/h`));
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
    sub.textContent = "stolpec = izmerjeno, črtica = vozni red; samo odseki nad 5 km"
      + (segs.length > shown.length ? ` · prikazanih ${shown.length} od ${segs.length}` : "");
    mountChart(el, (w) => drawSpeeds(w, shown));
  } catch (err) {
    console.error("hitrosti ni bilo mogoče naložiti", err);
    el.innerHTML = '<div class="empty-state">hitrosti ni bilo mogoče naložiti</div>';
  }
}

const speedsFigEl = document.getElementById("fig-speeds");
const speedsToggleEl = document.getElementById("speeds-toggle");

speedsToggleEl.addEventListener("click", () => {
  const open = speedsFigEl.hidden;
  speedsFigEl.hidden = !open;
  speedsToggleEl.classList.toggle("is-on", open);
  speedsToggleEl.setAttribute("aria-expanded", String(open));
  if (open && !speedsLoaded) {
    speedsLoaded = true;
    loadSpeeds();
  } else if (open) {
    redrawers.get(document.getElementById("speeds-chart"))?.();
  }
});

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

// Zgodovina rabi datum tekoce voznje, da ga izpusti iz povprecja -- zato sele
// za njo.
loadRun().then(loadHistory);
setInterval(loadRun, RUN_POLL_MS);
setInterval(loadHistory, HIST_POLL_MS);
loadHeadsign();
