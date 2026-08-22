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

// ---------- vreme ----------

const WEATHER_INK = "#6f8fa8";

function weatherIconHtml(w, size) {
  if (!w || w.temp_c == null) return "";
  const px = size || 14;
  const a = `width="${px}" height="${px}" viewBox="0 0 24 24" fill="none" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"`;
  if ((w.snowfall_cm || 0) > 0) {
    return `<svg ${a} stroke="#a8d8ff"><path d="M12 16a4.5 4.5 0 0 0 0-9 6 6 0 0 0-11 1.8A3.6 3.6 0 0 0 4.6 16"></path><path d="M8 20h.01M12 21h.01M16 20h.01"></path></svg>`;
  }
  if ((w.precip_mm || 0) >= 0.1) {
    return `<svg ${a} stroke="${WEATHER_INK}"><path d="M12 16a4.5 4.5 0 0 0 0-9 6 6 0 0 0-11 1.8A3.6 3.6 0 0 0 4.6 16"></path><path d="M8 19l-1 2.5M12 19l-1 2.5M16 19l-1 2.5"></path></svg>`;
  }
  if (w.code === 45 || w.code === 48) {
    return `<svg ${a} stroke="#79828f"><path d="M3 9h18M4 13h16M6 17h12"></path></svg>`;
  }
  if (w.code != null && w.code <= 1) {
    return `<svg ${a} stroke="#c8a06a"><circle cx="12" cy="12" r="4.2"></circle><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M18.4 5.6L17 7M7 17l-1.4 1.4"></path></svg>`;
  }
  return `<svg ${a} stroke="#5b6472"><path d="M12 18a5 5 0 0 0 0-10 6.5 6.5 0 0 0-12 2 4 4 0 0 0 4 4h8"></path></svg>`;
}

function num(v, digits) {
  if (v == null) return "—";
  return v.toFixed(digits == null ? 1 : digits).replace(".", ",");
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
  const now = Date.now();
  let found = null;
  for (const s of stops) {
    const iso = stopActualIso(s);
    if (iso && new Date(iso).getTime() <= now) found = s;
  }
  return found;
}

function stopWeatherHtml(w) {
  if (!w || w.temp_c == null) return "";
  return `<span class="stop-weather" title="${escapeHtml(weatherSummary(w))}">` +
    weatherIconHtml(w, 13) +
    `<span class="stop-temp">${num(w.temp_c, 0)}°</span></span>`;
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

function operatorEtaStopHtml(s) {
  // Feed ima za to postajo vrednost, a cas se ni minil -- napoved prevoznika.
  const d = stopDelay(s);
  const color = delayColor(d);
  const eta = hhmm(stopActualIso(s));
  const sched = hhmm(s.sched_dep || s.sched_arr);
  const schedHtml = eta !== sched ? `<span class="stop-sched">${sched}</span>` : "";
  return `
    <div class="stop-row is-eta">
      <div class="stop-rail"><span class="stop-dot is-hollow" style="border-color:${color}"></span><span class="stop-line is-dashed"></span></div>
      <div class="stop-main">
        <div class="stop-name">${escapeHtml(s.name)}</div>
        <div class="stop-times"><span class="stop-actual">${eta}</span>${schedHtml} <span class="stop-tag">napoved prevoznika</span></div>
      </div>
      <div class="stop-delay is-forecast" style="color:${color}">${delayLabel(d)}</div>
    </div>
  `;
}

function forecastStopHtml(s, f) {
  // Feed za to postajo nima nicesar -- ostane nasa ocena. Ce zgodovine na tem
  // odseku ni, je to zgolj prenos trenutne zamude naprej in tako mora tudi pisati.
  const schedIso = s.sched_dep || s.sched_arr;
  const sched = hhmm(schedIso);
  const d = f ? f.predicted_delay_s : null;
  const color = delayColor(d);
  const eta = d != null && schedIso ? hhmm(new Date(new Date(schedIso).getTime() + d * 1000)) : "—";
  const schedHtml = eta !== sched ? `<span class="stop-sched">${sched}</span>` : "";
  const tag = !f ? "brez ocene"
    : f.n_samples > 0 ? `ocena · mediana ${pluralRuns(f.n_samples)}`
    : "ocena · le prenos zamude";
  return `
    <div class="stop-row is-forecast">
      <div class="stop-rail"><span class="stop-dot is-hollow" style="border-color:${color}"></span><span class="stop-line is-dashed"></span></div>
      <div class="stop-main">
        <div class="stop-name">${escapeHtml(s.name)}</div>
        <div class="stop-times"><span class="stop-actual">${eta}</span>${schedHtml} <span class="stop-tag">${escapeHtml(tag)}</span></div>
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
      rows.push('<div class="stop-sep">naprej po progi — napoved, ne meritev</div>');
      seenAheadHead = true;
    }
    // Feedova vrednost za se nedoseženo postajo je napoved prevoznika in ima
    // prednost pred naso historicno oceno; ta pokrije ostanek proge.
    rows.push(stopActualIso(s) ? operatorEtaStopHtml(s) : forecastStopHtml(s, forecastBySeq.get(s.stop_seq)));
  }
  return `<div class="stop-list">${rows.join("")}</div>`;
}

async function fetchRunAndForecast(trainNo, date) {
  const enc = encodeURIComponent(trainNo);
  const q = date ? `?date=${encodeURIComponent(date)}` : "";
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
