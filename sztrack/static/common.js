"use strict";

// Skupno za /app in /app/train/{st}. Nalozi se pred dashboard.js oz. train.js.

const DELAY_RAMP = [
  { max: 60, color: "#7c8698", label: "točno" },
  { max: 300, color: "#f2a87e", label: "1–5 min" },
  { max: 900, color: "#e07b45", label: "5–15 min" },
  { max: Infinity, color: "#b85417", label: "nad 15 min" },
];

function delayColor(s) {
  if (s == null) return "#6b7480";
  return (DELAY_RAMP.find((step) => s <= step.max) || DELAY_RAMP[DELAY_RAMP.length - 1]).color;
}

function delayLabel(s) {
  // Feed ima locljivost 60 s -- zaokrozimo na minute in sekund ne kazemo nikoli.
  if (s == null) return "?";
  const m = Math.round(s / 60);
  return (m > 0 ? "+" : "") + m;
}

const TIME_FMT = new Intl.DateTimeFormat("sl-SI", {
  timeZone: "Europe/Ljubljana", hour: "2-digit", minute: "2-digit", hour12: false,
});

function hhmm(iso) {
  return iso ? TIME_FMT.format(new Date(iso)) : "—";
}

const DATE_FMT = new Intl.DateTimeFormat("sl-SI", {
  timeZone: "Europe/Ljubljana", day: "numeric", month: "numeric",
});

function dayLabel(isoDate) {
  return isoDate ? DATE_FMT.format(new Date(isoDate + "T12:00:00")) : "—";
}

// "danes ob 05:12" / "včeraj ob 05:12" / "26. 8. ob 05:12".
// Absolutni datum je pri predpomnjenem izracunu pomembnejsi od "pred 3 urami":
// bralec hoce vedeti, do katerega dne stevilka sega, ne kako stara je.
function stampLabel(iso) {
  if (!iso) return "—";
  const t = new Date(iso);
  const dayKey = (d) => DATE_FMT.format(d);
  const now = new Date();
  const yday = new Date(now.getTime() - 86400000);
  const when = dayKey(t) === dayKey(now) ? "danes"
             : dayKey(t) === dayKey(yday) ? "včeraj"
             : `${dayKey(t)}`;
  return `${when} ob ${TIME_FMT.format(t)}`;
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

function pluralRuns(n) {
  if (!n) return "brez zajete vožnje";
  if (n === 1) return "1 vožnja";
  if (n === 2) return "2 vožnji";
  if (n === 3) return "3 vožnje";
  if (n === 4) return "4 vožnje";
  return `${n} voženj`;
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
    const h = await fetch("/api/health").then((r) => r.json());
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

// ---------- preprosto / napredno ----------
// Isto na vseh straneh, zato tu in ne trikrat. Napreden pogled ni druga stran:
// je razred na <body>, ki odkrije elemente z razredom `adv-only`.
//
// Izbira gre v localStorage, da preklop drzi cez strani. Naslov jo lahko
// povozi (`?pogled=napredno`) -- brez tega naprednega pogleda ni mogoce
// deliti s povezavo, kar je pri strani s stevilkami prva stvar, ki jo kdo
// hoce narediti.

const MODE_KEY = "sztrack:mode";

function applyMode(mode, onChange) {
  document.body.classList.toggle("is-advanced", mode === "advanced");
  for (const b of document.querySelectorAll("#mode-switch button")) {
    b.setAttribute("aria-pressed", String(b.dataset.mode === mode));
  }
  try {
    localStorage.setItem(MODE_KEY, mode);
  } catch (err) {
    /* zaseben zavihek ni razlog, da stran ne dela */
  }
  if (onChange) onChange(mode);
}

function initMode(onChange) {
  const asked = new URLSearchParams(location.search).get("pogled");
  let mode = asked === "napredno" ? "advanced" : asked === "preprosto" ? "simple" : null;
  if (!mode) {
    try {
      mode = localStorage.getItem(MODE_KEY) || "simple";
    } catch (err) {
      mode = "simple";
    }
  }
  const box = document.getElementById("mode-switch");
  if (box) {
    box.addEventListener("click", (ev) => {
      const b = ev.target.closest("button[data-mode]");
      if (b) applyMode(b.dataset.mode, onChange);
    });
  }
  applyMode(mode, onChange);
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
};

// Vsi LPP-jevi route_color so ista zelena prevoznika, ne barva linije, zato
// barva ne loci linij in je ne sme. Ime linije nosi oznaka sama; barva samo
// pove, cigav avtobus je. Zato je v zetonu vedno tudi ime prevoznika.
const LINE_INK = "#4db97f";

function lineBadgeHtml(row) {
  if (!isBus(row.mode)) return "";
  // Na zeleznicni strani avtobus pomeni NADOMESTNI PREVOZ -- torej "namesto
  // vlaka, ki tu ne vozi". To ni linija mestnega prevoza in ne sme biti
  // videti kot ona; potnik mora prebrati, zakaj tu stoji avtobus.
  if (row.network === "zeleznica") {
    return `<span class="mode-bus" title="namesto vlaka, ki na tej relaciji ne vozi">
      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="4" width="16" height="13" rx="2"></rect>
        <path d="M4 11h16M8 21l-1 1M16 21l1 1M7 17v3M17 17v3"></path>
      </svg>
      nadomestni prevoz
    </span>`;
  }
  const who = AGENCY[row.agency];
  const label = who ? `${who} ${row.train_no}` : row.train_no;
  return `<span class="line-badge" style="color:${LINE_INK};border-color:${LINE_INK}55">
    ${escapeHtml(label)}</span>`;
}

function modeBadgeHtml(mode) {
  if (!isBus(mode)) return "";
  return `<span class="mode-bus" title="nadomestni prevoz namesto vlaka">
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor"
         stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="4" width="16" height="13" rx="2"></rect>
      <path d="M4 11h16M8 21l-1 1M16 21l1 1M7 17v3M17 17v3"></path>
      <circle cx="8" cy="14" r="1" fill="currentColor" stroke="none"></circle>
      <circle cx="16" cy="14" r="1" fill="currentColor" stroke="none"></circle>
    </svg>
    avtobus
  </span>`;
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
// narisana nevtralno. Enako kot v weather.py.
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

function stopDelay(s) {
  return s.delay_dep != null ? s.delay_dep : s.delay_arr;
}

function stopActualIso(s) {
  return s.actual_dep || s.actual_arr;
}

function lastMeasured(stops) {
  // Feed nosi vrednost tudi za postaje, ki jih vlak se ni dosegel -- to je
  // napoved prevoznika, ne meritev. Za izmerjeno steje samo postaja, katere
  // (voznored + zamuda) cas je ze minil.
  //
  // Nicla za se nedosezen postanek je pri tem past: (voznored + 0) je pri
  // zamujajocem vlaku ze minil in postaja bi se stela za prevozeno. Zamuda
  // med sosednjima postajama ne pade z dvajsetih minut na nic, zato tako
  // vrstico preskocimo -- isto pravilo kot v collector.py in /api/live.
  const now = Date.now();
  let found = null;
  let prevMax = 0;
  for (const s of stops) {
    const d = stopDelay(s);
    const iso = stopActualIso(s);
    if (iso && new Date(iso).getTime() <= now && !(d === 0 && prevMax >= 300)) {
      found = s;
    }
    if (d != null && d > prevMax) prevMax = d;
  }
  return found;
}

function stopWeatherHtml(w) {
  if (!w || w.severity == null) return "";
  // Potnika ne zanima 0,4 mm/h -- zanima ga, ali so razmere hude. Surove
  // stevilke ostanejo v naslovu in v oknu ob grafu.
  const color = severityColor(w.severity_label);
  const loud = w.severity_label === "zahtevne" || w.severity_label === "hude";
  return `<span class="stop-weather${loud ? " is-loud" : ""}" title="${escapeHtml(severityTitle(w))}"` +
    (loud ? ` style="background:${color}1f;border-color:${color}66"` : "") + `>` +
    weatherIconHtml(w, 13) +
    `<span class="stop-sev" style="color:${color}">${w.severity}</span></span>`;
}

function measuredStopHtml(s, isCurrent, w) {
  const d = stopDelay(s);
  const color = delayColor(d);
  const actual = hhmm(stopActualIso(s));
  const sched = hhmm(s.sched_dep || s.sched_arr);
  const schedHtml = actual !== sched ? `<span class="stop-sched">${sched}</span>` : "";
  return `
    <div class="stop-row${isCurrent ? " is-current" : ""}">
      <div class="stop-rail"><span class="stop-dot" style="background:${color}"></span><span class="stop-line"></span></div>
      <div class="stop-main">
        <div class="stop-name">${escapeHtml(s.name)}</div>
        <div class="stop-times"><span class="stop-actual">${actual}</span>${schedHtml}</div>
      </div>
      ${stopWeatherHtml(w)}
      <div class="stop-delay" style="color:${color}">${delayLabel(d)}</div>
    </div>
  `;
}

function gapStopHtml(s) {
  const sched = hhmm(s.sched_dep || s.sched_arr);
  return `
    <div class="stop-row is-muted">
      <div class="stop-rail"><span class="stop-dot is-hollow"></span><span class="stop-line"></span></div>
      <div class="stop-main">
        <div class="stop-name">${escapeHtml(s.name)}</div>
        <div class="stop-times"><span class="stop-sched-plain">${sched}</span> <span class="stop-tag">brez meritve</span></div>
      </div>
      <div class="stop-delay is-none">—</div>
    </div>
  `;
}

function forecastStopHtml(s, f) {
  // Postaja, ki je vlak se ni dosegel. Uporabimo LASTNO oceno, ne vrednosti
  // iz feeda -- ta je za postanke naprej izmerjeno slaba (glej backtest.py):
  //
  //   feed pravi 0, vlak pa zdaj zamuja >= 5 min:  napaka 18,5 min, v 5 min  6 %
  //   prenos trenutne zamude naprej:               napaka  1,6 min, v 5 min 91 %
  //
  // Feed za se nedosezene postanke pogosto objavi niclo, dokler nima prave
  // napovedi. Prevoznikovo stevilko zato pokazemo le v naprednem pogledu,
  // da ni skrita, a nanjo ne racunamo.
  const schedIso = s.sched_dep || s.sched_arr;
  const sched = hhmm(schedIso);
  const d = f ? f.predicted_delay_s : null;
  const color = delayColor(d);
  const eta = d != null && schedIso ? hhmm(new Date(new Date(schedIso).getTime() + d * 1000)) : "—";
  const schedHtml = eta !== sched ? `<span class="stop-sched">${sched}</span>` : "";
  const tag = !f ? "brez ocene"
    : f.n_samples > 0 ? `ocena · mediana ${pluralRuns(f.n_samples)}`
    : "ocena · le prenos zamude";
  const feedSaid = stopDelay(s);
  return `
    <div class="stop-row is-forecast">
      <div class="stop-rail"><span class="stop-dot is-hollow" style="border-color:${color}"></span><span class="stop-line is-dashed"></span></div>
      <div class="stop-main">
        <div class="stop-name">${escapeHtml(s.name)}</div>
        <div class="stop-times"><span class="stop-actual">${eta}</span>${schedHtml} <span class="stop-tag">${escapeHtml(tag)}</span></div>
        ${feedSaid != null ? `<div class="stop-times adv-only"><span class="stop-tag">feed pravi ${delayLabel(feedSaid)} min</span></div>` : ""}
      </div>
      <div class="stop-delay is-forecast" style="color:${color}">${delayLabel(d)}</div>
    </div>
  `;
}

function runTimelineHtml(stops, forecast, weatherBySeq) {
  const cur = lastMeasured(stops);
  const forecastBySeq = new Map((forecast || []).map((f) => [f.stop_seq, f]));
  const wx = weatherBySeq || new Map();
  const rows = [];
  let seenAheadHead = false;
  for (const s of stops) {
    if (cur && s.stop_seq <= cur.stop_seq) {
      rows.push(stopActualIso(s)
        ? measuredStopHtml(s, s.stop_seq === cur.stop_seq, wx.get(s.stop_seq))
        : gapStopHtml(s));
      continue;
    }
    if (!seenAheadHead) {
      rows.push('<div class="stop-sep">naprej po progi — ocena, ne meritev</div>');
      seenAheadHead = true;
    }
    rows.push(forecastStopHtml(s, forecastBySeq.get(s.stop_seq)));
  }
  return `<div class="stop-list">${rows.join("")}</div>`;
}

async function fetchRunAndForecast(trainNo, date, tripId) {
  const enc = encodeURIComponent(trainNo);
  // `trip` je nujen pri avtobusih: stevilka linije ni stevilka voznje.
  const p = new URLSearchParams();
  if (date) p.set("date", date);
  if (tripId) p.set("trip", tripId);
  const q = p.toString() ? `?${p}` : "";
  const res = await fetch(`/api/train/${enc}/run${q}`);
  if (!res.ok) throw new Error(`run ${res.status}`);
  const run = await res.json();

  const cur = lastMeasured(run.stops);
  // Dokler vlak se ni odpeljal, meritve ni, feed pa ima za prvo postajo ze
  // napoved. Oceno za naprej takrat zgradimo na njej -- ozaljsana je z oznako
  // "ocena", da nihce ne bere napovedi na napovedi kot izmerjeno.
  let base = cur;
  if (!base) {
    for (const s of run.stops) if (stopDelay(s) != null) { base = s; break; }
  }

  let forecast = [];
  const lastSeq = run.stops.length ? run.stops[run.stops.length - 1].stop_seq : 0;
  if (base && stopDelay(base) != null && base.stop_seq < lastSeq) {
    try {
      const p = await fetch(
        `/api/train/${enc}/predict?stop_seq=${base.stop_seq}&delay_s=${stopDelay(base)}`
      ).then((r) => (r.ok ? r.json() : null));
      forecast = (p && p.forecast) || [];
    } catch (err) {
      console.warn("napovedi ni bilo mogoče naložiti", err);
    }
  }
  return { run, forecast, current: cur };
}
