"use strict";

// Vstopna stran: od postaje do postaje. Skupne funkcije so v common.js.
const POLL_MS = 30000;

const fromEl = document.getElementById("from");
const toEl = document.getElementById("to");
const dateEl = document.getElementById("date");
const formEl = document.getElementById("search");
const resultsEl = document.getElementById("results");
const resultHeadEl = document.getElementById("result-head");
const feedDotEl = document.getElementById("feed-dot");

const todayIso = () => new Date().toLocaleDateString("sv-SE", { timeZone: "Europe/Ljubljana" });

let pollTimer = null;
let lastQuery = null;

// ---------- postaje za samodopolnjevanje ----------

async function loadStations() {
  try {
    const stations = await fetch("/api/stations").then((r) => r.json());
    const dl = document.getElementById("stations");
    dl.replaceChildren(...stations.map((s) => {
      const o = document.createElement("option");
      o.value = s.name;
      return o;
    }));
  } catch (err) {
    console.error("postaj ni bilo mogoče naložiti", err);
  }
}

// ---------- izpis ----------

function durationLabel(s) {
  const m = Math.round(s / 60);
  const h = Math.floor(m / 60);
  return h ? `${h} h ${String(m % 60).padStart(2, "0")} min` : `${m} min`;
}

function delayChipHtml(c) {
  if (c.delay_s == null) {
    return '<span class="chip chip-none">brez podatka</span>';
  }
  const color = delayColor(c.delay_s);
  const isForecast = c.delay_kind !== "izmerjeno";
  // Stevilka in kraj meritve gresta vedno zraven -- barva sama ne sme nositi pomena.
  return `<span class="chip${isForecast ? " chip-forecast" : ""}" style="color:${color};border-color:${color}44">
    <span class="chip-n">${delayLabel(c.delay_s)}</span>
    <span class="chip-unit">min</span>
  </span>
  <div class="chip-where">${escapeHtml(c.delay_kind)}${c.delay_at ? ` v ${escapeHtml(c.delay_at)}` : ""}</div>`;
}

function connectionRowHtml(c, nowMs) {
  const dep = new Date(c.sched_dep).getTime();
  const gone = dep < nowMs;
  const expected = c.expected_dep && c.expected_dep !== c.sched_dep ? hhmm(c.expected_dep) : null;
  return `
    <a class="conn-row${gone ? " is-gone" : ""}" href="/app/train/${encodeURIComponent(c.train_no)}" target="_blank" rel="noopener">
      <div class="conn-times">
        <div class="conn-clock">
          <span class="conn-dep">${hhmm(c.sched_dep)}</span>
          <span class="conn-dash">–</span>
          <span class="conn-arr">${hhmm(c.sched_arr)}</span>
        </div>
        <div class="conn-dur">${durationLabel(c.duration_s)} · ${c.stops_between} ${c.stops_between === 1 ? "postaja" : "postaj"}</div>
      </div>
      <div class="conn-train">
        <div class="conn-no">${escapeHtml(c.train_no)}</div>
        <div class="conn-headsign">${escapeHtml(c.headsign || "")}</div>
      </div>
      <div class="conn-delay">
        ${delayChipHtml(c)}
        ${expected ? `<div class="conn-expected">predviden odhod ${expected}</div>` : ""}
      </div>
    </a>
  `;
}

function renderResults(data) {
  const list = data.connections || [];
  const isToday = data.date === todayIso();
  const nowMs = Date.now();

  resultHeadEl.innerHTML = list.length
    ? `<strong>${escapeHtml(data.from)}</strong> → <strong>${escapeHtml(data.to)}</strong> ·
       ${escapeHtml(data.date)} · ${list.length} ${list.length === 1 ? "vožnja" : "voženj"}`
    : "";

  if (!list.length) {
    resultsEl.innerHTML = `<div class="empty-state">
      Na ta dan ni neposredne vožnje od <strong>${escapeHtml(data.from)}</strong>
      do <strong>${escapeHtml(data.to)}</strong>.<br>
      sztrack ne računa prestopov — išče samo vlake, ki peljejo čez obe postaji.
    </div>`;
    return;
  }

  resultsEl.innerHTML = list.map((c) => connectionRowHtml(c, isToday ? nowMs : 0)).join("");

  // Skoci na prvo vozjo, ki se ni odpeljala -- tisto uporabnik isce.
  if (isToday) {
    const next = resultsEl.querySelector(".conn-row:not(.is-gone)");
    if (next) next.scrollIntoView({ block: "center" });
  }
}

// ---------- iskanje ----------

async function search(push) {
  const from = fromEl.value.trim();
  const to = toEl.value.trim();
  const date = dateEl.value || todayIso();
  if (!from || !to) return;
  if (from === to) {
    resultsEl.innerHTML = '<div class="empty-state">izhodišče in cilj sta ista postaja</div>';
    return;
  }

  lastQuery = { from, to, date };
  localStorage.setItem("sztrack:last", JSON.stringify(lastQuery));
  if (push) {
    const q = new URLSearchParams({ from, to, date });
    history.replaceState(null, "", `?${q}`);
  }

  try {
    const url = `/api/connections?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}&date=${encodeURIComponent(date)}`;
    const data = await fetch(url).then((r) => r.json());
    renderResults(data);
    feedDotEl.classList.remove("stale");
  } catch (err) {
    console.error("iskanje ni uspelo", err);
    feedDotEl.classList.add("stale");
    resultsEl.innerHTML = '<div class="empty-state">iskanje ni uspelo</div>';
  }

  clearTimeout(pollTimer);
  if (date === todayIso()) pollTimer = setTimeout(() => search(false), POLL_MS);
}

formEl.addEventListener("submit", (ev) => {
  ev.preventDefault();
  search(true);
});

document.getElementById("swap").addEventListener("click", () => {
  [fromEl.value, toEl.value] = [toEl.value, fromEl.value];
  if (fromEl.value && toEl.value) search(true);
});

// ---------- zagon: URL, nato zadnje iskanje ----------

function restore() {
  const q = new URLSearchParams(location.search);
  let from = q.get("from");
  let to = q.get("to");
  let date = q.get("date");
  if (!from || !to) {
    try {
      const saved = JSON.parse(localStorage.getItem("sztrack:last") || "null");
      if (saved) ({ from, to } = saved);
    } catch (err) {
      /* pokvarjen zapis ni razlog, da stran ne dela */
    }
  }
  fromEl.value = from || "";
  toEl.value = to || "";
  dateEl.value = date || todayIso();
  if (fromEl.value && toEl.value) search(false);
}

function tickClock() {
  const fmt = new Intl.DateTimeFormat("sl-SI", {
    timeZone: "Europe/Ljubljana", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false,
  });
  document.getElementById("clock").textContent = fmt.format(new Date());
}

tickClock();
setInterval(tickClock, 1000);
loadStations().then(restore);
