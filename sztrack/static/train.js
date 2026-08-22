"use strict";

// Svoje okno enega vlaka: ta voznja + zgodovina te poti.
// Barve zamud so projektna ORDINALNA lestvica (en odtenek, monotona svetlost) --
// uporabljena samo tam, kjer koder pomeni velikost zamude. Hitrost ni zamuda,
// zato je narisana nevtralno, z voznim redom kot referenco.

const TRAIN_NO = document.body.dataset.trainNo;
const ENC = encodeURIComponent(TRAIN_NO);
const RUN_POLL_MS = 30000;
const HIST_POLL_MS = 600000;

const INK_LINE = "#4a515c";
const INK_GRID = "#23272f";
const INK_AXIS = "#79828f";
const INK_BAR = "#3d434f";
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
const redrawers = [];

function mountChart(el, draw) {
  const render = () => {
    const w = el.clientWidth;
    if (!w) return;
    el.replaceChildren(draw(w));
  };
  redrawers.push(render);
  render();
}

let resizeTimer = null;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => redrawers.forEach((f) => f()), 120);
});

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
    runHeadEl.innerHTML = runHeadHtml(current);
    runTimelineEl.innerHTML = runTimelineHtml(run.stops, forecast) +
      `<div class="detail-foot">${escapeHtml(run.service_date)} · ${run.stops.length} postaj</div>`;
    feedDotEl.classList.remove("stale");
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

// ---------- graf 1: profil zamude po postajah ----------

function drawProfile(w, byStop) {
  const H = 240;
  const M = { t: 14, r: 16, b: 34, l: 40 };
  const iw = Math.max(40, w - M.l - M.r);
  const ih = H - M.t - M.b;

  const svg = svgEl("svg", { width: w, height: H, role: "img" });
  const maxV = Math.max(60, ...byStop.map((d) => Math.max(d.median_s, d.p90_s || 0)));
  const yMax = Math.ceil(maxV / 60 / 5) * 5 * 60 || 300;
  const x = (i) => M.l + (byStop.length === 1 ? iw / 2 : (i * iw) / (byStop.length - 1));
  const y = (v) => M.t + ih - (v / yMax) * ih;

  // mreza in os -- recesivno
  const ticks = 4;
  for (let i = 0; i <= ticks; i += 1) {
    const v = (yMax / ticks) * i;
    svg.appendChild(svgEl("line", {
      x1: M.l, x2: M.l + iw, y1: y(v), y2: y(v),
      stroke: i === 0 ? INK_AXIS : INK_GRID, "stroke-width": 1,
    }));
    svg.appendChild(svgEl("text", {
      x: M.l - 8, y: y(v) + 4, "text-anchor": "end",
      fill: INK_AXIS, "font-size": 10, "font-family": "'IBM Plex Mono', monospace",
    }, `${Math.round(v / 60)}`));
  }
  svg.appendChild(svgEl("text", {
    x: M.l - 8, y: M.t - 3, "text-anchor": "end",
    fill: INK_AXIS, "font-size": 9, "font-family": "'IBM Plex Sans', sans-serif",
  }, "min"));

  // pas mediana -> p90 (pri eni voznji se sesede v nic -- tako mora biti)
  const hasBand = byStop.some((d) => (d.p90_s || 0) > d.median_s);
  if (hasBand) {
    const up = byStop.map((d, i) => `${x(i)},${y(d.p90_s)}`).join(" ");
    const down = byStop.map((d, i) => `${x(i)},${y(d.median_s)}`).reverse().join(" ");
    svg.appendChild(svgEl("polygon", {
      points: `${up} ${down}`, fill: "#e07b45", "fill-opacity": 0.14, stroke: "none",
    }));
  }

  // crta skozi mediane
  svg.appendChild(svgEl("polyline", {
    points: byStop.map((d, i) => `${x(i)},${y(d.median_s)}`).join(" "),
    fill: "none", stroke: INK_LINE, "stroke-width": 2,
    "stroke-linejoin": "round", "stroke-linecap": "round",
  }));

  // tocke: barva nosi razred zamude, stevilka je v oznaki oz. v tooltipu
  const maxIdx = byStop.reduce((best, d, i) => (d.median_s > byStop[best].median_s ? i : best), 0);
  byStop.forEach((d, i) => {
    const c = svgEl("circle", {
      cx: x(i), cy: y(d.median_s), r: 4.5,
      fill: delayColor(d.median_s), stroke: SURFACE, "stroke-width": 2,
    });
    c.addEventListener("mousemove", (ev) => showTip(
      `<div class="tt-title">${escapeHtml(d.name)}</div>` +
      `<div class="tt-row"><span>mediana</span><b>${delayLabel(d.median_s)} min</b></div>` +
      (d.p90_s > d.median_s ? `<div class="tt-row"><span>p90</span><b>${delayLabel(d.p90_s)} min</b></div>` : "") +
      `<div class="tt-row"><span>najslabše</span><b>${delayLabel(d.max_s)} min</b></div>` +
      `<div class="tt-note">${escapeHtml(pluralRuns(d.n))}</div>`, ev));
    c.addEventListener("mouseleave", hideTip);
    svg.appendChild(c);
  });

  // neposredne oznake samo tam, kjer nekaj povedo: vrh in cilj
  const labelAt = new Set([maxIdx, byStop.length - 1]);
  labelAt.forEach((i) => {
    const d = byStop[i];
    svg.appendChild(svgEl("text", {
      x: x(i), y: y(d.median_s) - 10, "text-anchor": i === byStop.length - 1 ? "end" : "middle",
      fill: "#e7eaf0", "font-size": 11, "font-weight": 600,
      "font-family": "'IBM Plex Mono', monospace",
    }, delayLabel(d.median_s)));
  });

  // os x: samo prva, zadnja in vrh -- imena postaj so dolga
  const xLabels = [[0, "start"], [byStop.length - 1, "end"]];
  if (maxIdx !== 0 && maxIdx !== byStop.length - 1) xLabels.push([maxIdx, "middle"]);
  for (const [i, anchor] of xLabels) {
    svg.appendChild(svgEl("text", {
      x: x(i), y: H - 12,
      "text-anchor": anchor === "start" ? "start" : anchor === "end" ? "end" : "middle",
      fill: INK_AXIS, "font-size": 10, "font-family": "'IBM Plex Sans', sans-serif",
    }, byStop[i].name));
  }
  return svg;
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

// ---------- graf 3: hitrost po odsekih ----------

function drawSpeeds(w, segs) {
  const rowH = 30;
  const M = { t: 6, r: 96, b: 6, l: 148 };
  const H = M.t + M.b + segs.length * rowH;
  const iw = Math.max(40, w - M.l - M.r);
  const svg = svgEl("svg", { width: w, height: H, role: "img" });
  const maxV = Math.max(...segs.map((s) => Math.max(s.actual_kmh, s.sched_kmh))) * 1.05;

  segs.forEach((s, i) => {
    const yTop = M.t + i * rowH;
    const cy = yTop + rowH / 2;
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

// ---------- sestavljanje zgodovine ----------

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

async function loadHistory() {
  // Zgodovina se osvezuje -- brez tega bi se ob vsakem osvezitvi nabral se en
  // set izrisovalcev in resize bi risal cez stare zaprtja.
  redrawers.length = 0;
  let h;
  try {
    h = await fetch(`/api/train/${ENC}/history?days=90`).then((r) => r.json());
  } catch (err) {
    console.error("zgodovine ni bilo mogoče naložiti", err);
    return;
  }

  const n = h.runs_observed || 0;
  const first = h.runs && h.runs.length ? h.runs[0].service_date : null;
  document.getElementById("hist-note").innerHTML = n
    ? `Zajetih ${escapeHtml(pluralRuns(n))}${first ? `, od ${escapeHtml(first)}` : ""}.` +
      (n < 10 ? " <strong>Premalo za porazdelitev</strong> — številke spodaj opisujejo teh nekaj voženj, ne značilnega dne." : "")
    : "Za to pot še ni zajete nobene vožnje.";

  renderTiles(h);

  // graf 1
  const byStop = (h.by_stop || []).filter((d) => d.median_s != null);
  const profSub = document.getElementById("profile-sub");
  const profEl = document.getElementById("profile-chart");
  if (byStop.length >= 2) {
    profSub.textContent = n === 1
      ? "ena zajeta vožnja — to je njen potek, ne povprečje"
      : "črta = mediana, senca = razpon do p90";
    mountChart(profEl, (w) => drawProfile(w, byStop));
  } else {
    profSub.textContent = "";
    profEl.innerHTML = '<div class="empty-state">premalo postaj z meritvijo za profil</div>';
  }

  // graf 2
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
    runsEl.innerHTML = '<div class="empty-state">ni zajete vožnje</div>';
  }

  // graf 3
  const speedsSub = document.getElementById("speeds-sub");
  const speedsEl = document.getElementById("speeds-chart");
  try {
    const raw = await fetch(`/api/speeds?train_no=${ENC}`).then((r) => r.json());
    const segs = aggregateSpeeds(raw);
    if (segs.length) {
      const shown = segs.slice(0, 12);
      speedsSub.textContent = "stolpec = izmerjeno, črtica = vozni red; samo odseki nad 5 km"
        + (segs.length > shown.length ? ` · prikazanih ${shown.length} od ${segs.length}` : "");
      mountChart(speedsEl, (w) => drawSpeeds(w, shown));
    } else {
      speedsSub.textContent = "";
      speedsEl.innerHTML = '<div class="empty-state">ni odseka nad 5 km z dvema meritvama</div>';
    }
  } catch (err) {
    console.error("hitrosti ni bilo mogoče naložiti", err);
    speedsEl.innerHTML = '<div class="empty-state">hitrosti ni bilo mogoče naložiti</div>';
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

loadRun();
setInterval(loadRun, RUN_POLL_MS);
loadHistory();
setInterval(loadHistory, HIST_POLL_MS);
loadHeadsign();
