"use strict";

// Vstopna stran. Dve vprašanji na isti strani: "od kod do kam" in "kaj gre
// s te postaje". Skupne funkcije (barve, čas, vreme) so v common.js.

const POLL_MS = 30000;

const $ = (id) => document.getElementById(id);
const resultsEl = $("results");
const resultHeadEl = $("result-head");
const alertsEl = $("alerts");
const feedDotEl = $("feed-dot");

const todayIso = () => new Date().toLocaleDateString("sv-SE", { timeZone: "Europe/Ljubljana" });

let pollTimer = null;
let activeTab = "ab";

// Preklop pogleda je skupen vsem stranem in zivi v common.js.
initMode((mode) => { if (mode === "advanced") loadHealth(); });

async function loadHealth() {
  const el = $("foot-health");
  if (!el || el.dataset.done) return;
  try {
    const h = await fetch("/api/health").then((r) => r.json());
    el.textContent =
      ` · zajetih ${h.observations.toLocaleString("sl-SI")} meritev v ${h.days_covered} dneh` +
      (h.last_feed_at ? `, zadnja ob ${hhmm(h.last_feed_at)}` : "");
    el.dataset.done = "1";
  } catch (err) {
    /* stanje zajema je postranska informacija */
  }
}

// ---------- samodopolnjevanje postaj ----------

function attachSuggest(input, listEl) {
  let items = [];
  let active = -1;
  let seq = 0;

  // Bralnik zaslona mora vedeti, da je polje spustni seznam, ali je odprt in
  // katera moznost je izbrana. Brez tega je tipkovnicna izbira nevidna.
  input.setAttribute("role", "combobox");
  input.setAttribute("aria-autocomplete", "list");
  input.setAttribute("aria-expanded", "false");
  input.setAttribute("aria-controls", listEl.id);

  const close = () => {
    listEl.hidden = true;
    active = -1;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
  };

  const paint = () => {
    if (!items.length) return close();
    const q = input.value.trim();
    listEl.replaceChildren(...items.map((s, i) => {
      const li = document.createElement("li");
      li.id = `${listEl.id}-${i}`;
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", String(i === active));
      li.className = i === active ? "is-active" : "";
      li.innerHTML = highlight(s.name, q);
      li.addEventListener("mousedown", (ev) => {
        ev.preventDefault();          // ne izgubi fokusa pred klikom
        input.value = s.name;
        close();
        input.form.requestSubmit();
      });
      return li;
    }));
    listEl.hidden = false;
    input.setAttribute("aria-expanded", "true");
    if (active >= 0) input.setAttribute("aria-activedescendant", `${listEl.id}-${active}`);
    else input.removeAttribute("aria-activedescendant");
  };

  input.addEventListener("input", async () => {
    const q = input.value.trim();
    if (q.length < 2) return close();
    const mine = ++seq;
    try {
      const res = await fetch(`/api/stations/search?q=${encodeURIComponent(q)}&limit=8`)
        .then((r) => r.json());
      if (mine !== seq) return;       // prehitelo ga je novejse tipkanje
      items = res;
      active = -1;
      paint();
    } catch (err) {
      close();
    }
  });

  input.addEventListener("keydown", (ev) => {
    if (listEl.hidden) return;
    if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {
      ev.preventDefault();
      active = (active + (ev.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
      paint();
    } else if (ev.key === "Enter" && active >= 0) {
      ev.preventDefault();
      input.value = items[active].name;
      close();
      input.form.requestSubmit();
    } else if (ev.key === "Escape") {
      close();
    }
  });

  input.addEventListener("blur", () => setTimeout(close, 120));
}

function highlight(name, q) {
  const i = fold(name).indexOf(fold(q));
  if (i < 0 || !q) return escapeHtml(name);
  return escapeHtml(name.slice(0, i)) +
    "<mark>" + escapeHtml(name.slice(i, i + q.length)) + "</mark>" +
    escapeHtml(name.slice(i + q.length));
}

// Isto sklanjanje kot v journey.py: brez tega bi se poudarek pri "sentjur"
// ujel na napacnem mestu ali sploh ne.
function fold(s) {
  return s.normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

// ---------- obvestila o ovirah ----------

function alertsHtml(list, note) {
  if (!list || !list.length) return "";
  const items = list.map((a) => `
    <div class="alert-item">
      <strong>${escapeHtml(a.header || "")}</strong>
      <div class="alert-meta">
        ${escapeHtml(a.effect_label || "")}${a.cause_label ? ` · ${escapeHtml(a.cause_label)}` : ""}
        ${a.url ? ` · <a href="${escapeHtml(a.url)}" target="_blank" rel="noopener">obvestilo SŽ</a>` : ""}
      </div>
    </div>`).join("");
  return `<details class="alert-box"${list.length <= 2 ? " open" : ""}>
    <summary class="alert-head">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <path d="M12 9v5M12 17.5v.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"></path>
      </svg>
      ${escapeHtml(note)}
      <span class="alert-count">— ${list.length} ${list.length === 1 ? "obvestilo" : "obvestil"}</span>
    </summary>
    <div class="alert-list">${items}</div>
  </details>`;
}

function renderAlerts(list, note) {
  // Obvestila pride ze urejena s streznika: najprej tista, ki imenujejo
  // postajo s te poti. Prikaz jih samo izpise.
  alertsEl.innerHTML = alertsHtml(list, note);
}

// Povezava na eno vožnjo. `trip` gre zraven, ker številka linije pri
// avtobusih ni številka vožnje -- LPP linija 3G ima 388 voženj.
function journeyHref(trainNo, date, tripId) {
  const p = new URLSearchParams();
  if (date) p.set("date", date);
  if (tripId) p.set("trip", tripId);
  return `/app/train/${encodeURIComponent(trainNo)}${p.toString() ? `?${p}` : ""}`;
}

// ---------- izpis ----------

function durationLabel(s) {
  const m = Math.round(s / 60);
  const h = Math.floor(m / 60);
  return h ? `${h} h ${String(m % 60).padStart(2, "0")} min` : `${m} min`;
}

function stopsLabel(n) {
  if (n === 1) return "1 postaja";
  if (n === 2) return "2 postaji";
  if (n === 3 || n === 4) return `${n} postaje`;
  return `${n} postaj`;
}

function countdownLabel(iso, nowMs) {
  const min = Math.round((new Date(iso).getTime() - nowMs) / 60000);
  if (min < 0 || min > 90) return "";
  if (min === 0) return "zdaj";
  return `čez ${min} min`;
}

function typicalChipHtml(t, fromStop) {
  // Za dan, ki se ni prisel, meritve ni -- povemo pa lahko, kako je bilo
  // doslej. To NI napoved za ta dan in oznaka mora to jasno povedati.
  if (!t) return '<span class="chip chip-none">brez podatka</span>';
  const color = delayColor(t.median_s);
  return `<span class="chip chip-forecast" style="color:${color};border-color:${color}44">
      <span class="chip-n">${delayLabel(t.median_s)}</span><span class="chip-unit">min</span>
    </span>
    <div class="conn-where">običajno · ${pluralRuns(t.n)}</div>
    ${fromStop ? `<div class="conn-where">merjeno na postaji ${escapeHtml(fromStop)}</div>` : ""}
    <div class="conn-where adv-only">točnih ${Math.round(t.on_time_share * 100)} % · p90 ${delayLabel(t.p90_s)} min</div>`;
}

function delayChipHtml(delay, kind, at) {
  if (delay == null) return '<span class="chip chip-none">brez podatka</span>';
  const color = delayColor(delay);
  const forecast = kind && kind !== "izmerjeno";
  return `<span class="chip${forecast ? " chip-forecast" : ""}" style="color:${color};border-color:${color}44">
      <span class="chip-n">${delayLabel(delay)}</span><span class="chip-unit">min</span>
    </span>
    ${kind ? `<div class="conn-where">${escapeHtml(kind)}${at ? ` na postaji ${escapeHtml(at)}` : ""}</div>` : ""}`;
}

// Vožnja je "mimo" šele, ko je minil PRIČAKOVANI odhod, ne voznoredni.
// Vlak, ki zamuja pol ure, je ob voznorednem času še vedno na postaji in je
// še vedno možnost -- prav to je razlika, ki jo aplikacija o zamudah dolguje.
function departedMs(c) {
  return new Date(c.expected_dep || c.sched_dep).getTime();
}

function connectionRowHtml(c, nowMs, isNext, date) {
  const gone = nowMs && departedMs(c) < nowMs;
  const late = c.delay_s != null && c.delay_s >= 60;
  const color = delayColor(c.delay_s);
  const cd = isNext && nowMs ? countdownLabel(c.expected_dep || c.sched_dep, nowMs) : "";

  // Pricakovani prihod = voznoredni + ista zamuda. To je prenos, ne meritev,
  // zato v naprednem pogledu pise, od kod je.
  const expArr = late && c.sched_arr
    ? hhmm(new Date(new Date(c.sched_arr).getTime() + c.delay_s * 1000).toISOString())
    : null;

  return `
    <a class="conn-row${gone ? " is-gone" : ""}${isNext ? " is-next" : ""}${late ? " has-delay" : ""}"
       href="${journeyHref(c.train_no, date, c.trip_id)}">
      <div class="conn-times">
        <div class="conn-clock">
          <span class="conn-dep">${hhmm(c.sched_dep)}</span>
          <span class="conn-dash">–</span>
          <span class="conn-arr">${hhmm(c.sched_arr)}</span>
        </div>
        ${late ? `<div class="conn-expected" style="color:${color}">
            <span>${hhmm(c.expected_dep)}</span><span class="conn-dash">–</span><span>${expArr || "?"}</span>
          </div>` : ""}
      </div>
      <div class="conn-train">
        <div class="conn-no">${isBus(c.mode)
          ? lineBadgeHtml(c)
          : escapeHtml(c.train_no)}</div>
        <div class="conn-headsign">${escapeHtml(c.headsign || "")}</div>
      </div>
      <div class="conn-delay">${c.delay_s != null
        ? delayChipHtml(c.delay_s, c.delay_kind, c.delay_at)
        : typicalChipHtml(c.typical_arr || c.typical_dep)}</div>
      <div class="conn-meta">
        ${cd ? `<span class="countdown">${cd}</span>` : ""}
        <span>${durationLabel(c.duration_s)}</span>
        <span>${stopsLabel(c.stops_between)}</span>
        <span class="adv-only">neposredno</span>
      </div>
    </a>`;
}

// Zveza, ki je ne drzi, ni povezava. Barva je semafor razmer, ne lestvica
// zamud: to ni "koliko", ampak "ali gre" -- druga vrsta vprasanja.
const TRANSFER_STYLE = {
  "drži": { color: "var(--sev-mild)", note: "zveza drži" },
  "tesno": { color: "var(--sev-hard)", note: "tesno" },
  "ne drži": { color: "var(--sev-bad)", note: "zveza ne drži" },
  "brez podatka": { color: "var(--ink-faint)", note: "brez podatka o zamudi" },
};

function transferBadgeHtml(tr, plannedS) {
  if (!tr) return '<span class="tag">1 prestop</span>';
  const st = TRANSFER_STYLE[tr.status] || TRANSFER_STYLE["brez podatka"];
  const mins = Math.round(tr.wait_s / 60);
  return `<span class="transfer-badge" style="color:${st.color};border-color:${st.color}55">
      ${escapeHtml(st.note)}
    </span>
    <div class="conn-where">${tr.status === "brez podatka"
      ? `${Math.round(plannedS / 60)} min za prestop`
      : `${mins} min za prestop · ${escapeHtml(tr.source)}`}</div>`;
}

function transferRowHtml(t, nowMs, date) {
  const tr = t.transfer;
  const st = TRANSFER_STYLE[(tr && tr.status) || "brez podatka"];
  const planned = Math.round(t.wait_s / 60);
  const actual = tr && tr.wait_s != null ? Math.round(tr.wait_s / 60) : null;

  const legs = t.legs.map((l, i) => `
    <div class="leg">
      <span class="leg-time">${hhmm(l.dep)}–${hhmm(l.arr)}</span>
      <span class="leg-train">${escapeHtml(l.train_no)}</span>
      <span class="leg-where">${escapeHtml(l.from)} → ${escapeHtml(l.to)}</span>
    </div>
    ${i === 0 ? `<div class="leg">
        <span class="leg-wait" style="color:${st.color}">
          prestop na postaji ${escapeHtml(t.via)} · ${actual != null && actual !== planned
            ? `${actual} min (po voznem redu ${planned})`
            : `${planned} min`}
        </span>
        ${tr && tr.delay1_s ? `<span class="leg-note">prvi vlak ${delayLabel(tr.delay1_s)} min</span>` : ""}
      </div>` : ""}
  `).join("");

  return `
    <a class="conn-row is-transfer" style="border-left-color:${st.color}"
       href="${journeyHref(t.train1, date, t.trip1)}">
      <div class="conn-times">
        <div class="conn-clock">
          <span class="conn-dep">${hhmm(t.sched_dep)}</span>
          <span class="conn-dash">–</span>
          <span class="conn-arr">${hhmm(t.sched_arr)}</span>
        </div>
      </div>
      <div class="conn-train">
        <div class="conn-no">${escapeHtml(t.train1)} → ${escapeHtml(t.train2)}</div>
        <div class="conn-headsign">prestop na postaji ${escapeHtml(t.via)}</div>
      </div>
      <div class="conn-delay">${transferBadgeHtml(tr, t.wait_s)}</div>
      <div class="conn-meta">
        <span>${durationLabel(t.duration_s)}</span>
        <span class="adv-only">načrtovano ${planned} min za prestop</span>
      </div>
      <div class="legs">${legs}</div>
    </a>`;
}

function renderConnections(data) {
  const list = data.connections || [];
  const legs = data.transfers || [];
  const isToday = data.date === todayIso();
  const nowMs = isToday ? Date.now() : 0;

  resultHeadEl.innerHTML =
    `<span><strong>${escapeHtml(data.from)}</strong> → <strong>${escapeHtml(data.to)}</strong></span>
     <span>${dayLabel(data.date)}</span>
     <span>${list.length} ${list.length === 1 ? "neposredna vožnja" : "neposrednih"}${legs.length ? ` · ${legs.length} s prestopom` : ""}</span>`;

  if (!list.length && !legs.length) {
    resultsEl.innerHTML = `<div class="empty-state">
      Na ta dan ni vožnje od <strong>${escapeHtml(data.from)}</strong>
      do <strong>${escapeHtml(data.to)}</strong> — ne neposredne ne z enim prestopom.<br>
      Preveri drug dan; ob koncu tedna vozi bistveno manj vlakov.
    </div>`;
    renderAlerts(data.alerts, "Na tej poti so obvestila o ovirah");
    return;
  }

  // Naslednja vozjna je prva, ki se ni odpeljala. Prav to clovek isce, zato
  // je poudarjena, ne le prva po vrsti.
  let nextIdx = -1;
  if (isToday) nextIdx = list.findIndex((c) => departedMs(c) >= nowMs);

  // Ze odpeljane vozjne so kontekst, ne izbira. Ostanejo dosegljive -- kdor
  // preverja, ali je zamudil vlak, jih rabi -- a ne stojijo pred odgovorom.
  const gone = nextIdx > 0 ? list.slice(0, nextIdx) : [];
  const ahead = nextIdx >= 0 ? list.slice(nextIdx) : list;

  const rows = [];
  if (gone.length) {
    rows.push(`<details class="past-box"><summary class="past-head">
        pokaži ${gone.length} ${gone.length === 1 ? "prejšnjo vožnjo" : "prejšnjih"}
      </summary>
      ${gone.map((c) => connectionRowHtml(c, nowMs, false, data.date)).join("")}
    </details>`);
  }
  rows.push(...ahead.map((c, i) => connectionRowHtml(c, nowMs, i === 0 && nextIdx >= 0, data.date)));
  if (legs.length) {
    rows.push(`<div class="result-head"><span>Z enim prestopom</span></div>`);
    rows.push(...legs.map((t) => transferRowHtml(t, nowMs, data.date)));
  }
  resultsEl.innerHTML = rows.join("");

  renderAlerts(data.alerts, "Na tej poti so obvestila o ovirah");
}

function boardRowHtml(r, nowMs, isNext, date) {
  const gone = nowMs && new Date(r.expected || r.sched).getTime() < nowMs;
  const late = r.delay_s != null && r.delay_s >= 60;
  const color = delayColor(r.delay_s);
  const cd = isNext && nowMs ? countdownLabel(r.expected || r.sched, nowMs) : "";
  return `
    <a class="board-row${gone ? " is-gone" : ""}${isNext ? " is-next" : ""}${late ? " has-delay" : ""}"
       href="${journeyHref(r.train_no, date, r.trip_id)}">
      <div>
        <div class="board-time">${hhmm(r.sched)}</div>
        ${late ? `<div class="board-expected" style="color:${color}">${hhmm(r.expected)}</div>` : ""}
      </div>
      <div>
        <div class="board-towards">
          ${isBus(r.mode) ? lineBadgeHtml(r) : ""}
          <span>${escapeHtml(r.towards)}</span>
        </div>
        <div class="board-train">${isBus(r.mode) ? "" : `${escapeHtml(r.train_no)} `}${r.headsign ? escapeHtml(r.headsign) : ""}</div>
      </div>
      <div class="conn-delay">${r.delay_s != null
        ? delayChipHtml(r.delay_s, r.delay_from ? "izmerjeno" : null, r.delay_from)
        : typicalChipHtml(r.typical, r.typical_from)}</div>
      <div class="board-meta">
        ${cd ? `<span class="countdown">${cd}</span> · ` : ""}
        ${r.is_origin ? '<span class="adv-only">izhodišče — feed odhodne zamude ne poroča</span> ' : ""}
        <span class="adv-only">postanek ${r.stop_seq}${r.is_terminus ? " · konec" : ""}</span>
      </div>
    </a>`;
}

function renderBoard(data) {
  const list = data.board || [];
  const isToday = data.date === todayIso();
  const nowMs = isToday ? Date.now() : 0;

  resultHeadEl.innerHTML =
    `<span><strong>${escapeHtml(data.station)}</strong></span>
     <span>${data.kind}</span><span>${dayLabel(data.date)}</span>
     <span>${list.length} ${data.kind}${data.window_min >= 1440
        ? " ta dan"
        : ` od ${String(Math.floor(data.from_s / 3600)).padStart(2, "0")}:${String(Math.floor(data.from_s % 3600 / 60)).padStart(2, "0")}, ${Math.round(data.window_min / 60)} h naprej`}</span>`;

  if (!list.length) {
    resultsEl.innerHTML = `<div class="empty-state">
      V tem oknu s postaje <strong>${escapeHtml(data.station)}</strong> ni ${escapeHtml(data.kind)}.<br>
      Poskusi večje časovno okno ali drug dan.
    </div>`;
    alertsEl.innerHTML = "";
    return;
  }

  let nextIdx = -1;
  if (isToday) nextIdx = list.findIndex((r) => new Date(r.expected || r.sched).getTime() >= nowMs);
  resultsEl.innerHTML = list.map((r, i) => boardRowHtml(r, nowMs, i === nextIdx, data.date)).join("");
  renderAlerts(data.alerts, `Obvestila o ovirah — ${data.station}`);
}


// ---------- vstopni pregled ----------
// Brez tega je prva stran prazen obrazec. "Kako vozijo vlaki danes" je pri
// prometni aplikaciji enako pogosto vprasanje kot vprasanje o svoji poti.

const POPULAR = [
  ["Ljubljana", "Maribor"],
  ["Ljubljana", "Koper"],
  ["Ljubljana", "Jesenice"],
  ["Ljubljana", "Novo mesto"],
  ["Maribor", "Murska Sobota"],
  ["Celje", "Ljubljana"],
];

function bucketBarHtml(b, total) {
  const order = [["točno", 60], ["1–5 min", 300], ["5–15 min", 900], ["nad 15 min", 1800]];
  const segs = order.map(([label, ref]) => {
    const n = b[label] || 0;
    if (!n) return "";
    const pct = (n / total) * 100;
    return `<span class="bucket" style="width:${pct}%;background:${delayColor(ref)}"
              title="${escapeHtml(label)}: ${n}"></span>`;
  }).join("");
  const keys = order.map(([label, ref]) => `<span class="bucket-key">
      <span class="bucket-dot" style="background:${delayColor(ref)}"></span>
      ${escapeHtml(label)} <b>${b[label] || 0}</b></span>`).join("");
  return `<div class="bucket-bar">${segs}</div><div class="bucket-keys">${keys}</div>`;
}

function overviewHtml(o) {
  // Streznik da `yesterday` samo takrat, kadar je danasnji vzorec premajhen.
  const useYesterday = o.yesterday && o.yesterday.runs;
  const day = useYesterday ? o.yesterday : o.today;
  const dayNote = useYesterday ? "včeraj" : "danes";

  const live = (o.live_worst || []).map((t) => {
    const color = delayColor(t.delay_s);
    // Kje je vlak, pove prevoznik natancneje od nas: prometno mesto pogosto
    // ni voznoredni postanek.
    // Kraj in starost morata biti iz istega vira, sicer pise "Dobova" in
    // "meritev stara 40 min", ceprav je porocilo o Dobovi staro 11 minut.
    const fromOperator = !!t.reported_at_station;
    const where = fromOperator ? t.reported_at_station : t.last_stop;
    const age = fromOperator ? t.reported_age_s : t.age_s;
    const stale = age != null && age > 1200;
    return `<a class="live-row" href="/app/train/${encodeURIComponent(t.train_no)}">
      <span class="live-no">${escapeHtml(t.train_no)}</span>
      <span class="live-where">${escapeHtml(where)}</span>
      <span class="live-delay" style="color:${color}">${delayLabel(t.delay_s)} min</span>
      ${stale ? `<span class="stale-note">podatek star ${Math.round(age / 60)} min</span>` : ""}
    </a>`;
  }).join("");

  return `
    <section class="overview">
      <div class="ov-head">
        <h2>Kako vozijo vlaki</h2>
        <span class="ov-sub">${o.live_trains} ${o.live_trains === 1 ? "vlak" : "vlakov"} zdaj na progi</span>
      </div>

      ${day && day.runs ? `
        <div class="ov-card">
          <div class="ov-card-head">
            <span>Končna zamuda, ${dayNote}</span>
            <strong style="color:${delayColor(day.median_s)}">mediana ${delayLabel(day.median_s)} min</strong>
          </div>
          ${bucketBarHtml(day.buckets, day.runs)}
          <div class="ov-card-foot">
            ${day.runs} zajetih voženj · točnih ${Math.round(day.on_time_share * 100)} %
            <span class="adv-only">· p90 ${delayLabel(day.p90_s)} min · najslabša ${delayLabel(day.worst_s)} min</span>
          </div>
        </div>` : ""}

      ${live ? `<div class="ov-card">
        <div class="ov-card-head"><span>Največje zamude zdaj</span></div>
        <div class="live-list">${live}</div>
      </div>` : ""}

      ${o.disruptions ? `<a class="ov-link" href="/app/ovire">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M12 9v5M12 17.5v.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"></path>
        </svg>
        ${o.disruptions} veljavnih obvestil o ovirah na progah
      </a>` : ""}

      <div class="ov-head"><h2>Pogoste relacije</h2></div>
      <div class="chips">
        ${POPULAR.map(([a, b]) => `<button type="button" class="route-chip"
            data-from="${escapeHtml(a)}" data-to="${escapeHtml(b)}">${escapeHtml(a)} → ${escapeHtml(b)}</button>`).join("")}
      </div>
    </section>`;
}

async function showOverview() {
  try {
    const o = await fetch("/api/overview").then((r) => r.json());
    resultsEl.innerHTML = overviewHtml(o);
    resultsEl.querySelectorAll(".route-chip").forEach((b) => {
      b.addEventListener("click", () => {
        $("from").value = b.dataset.from;
        $("to").value = b.dataset.to;
        setTab("ab");
        $("from").value = b.dataset.from;
        $("to").value = b.dataset.to;
        searchAB(true);
      });
    });
  } catch (err) {
    resultsEl.innerHTML = '<div class="empty-state">Vpiši izhodišče in cilj ali izberi postajo.</div>';
  }
}

// ---------- poizvedbe ----------

function schedulePoll(fn, isToday) {
  clearTimeout(pollTimer);
  if (isToday) pollTimer = setTimeout(fn, POLL_MS);
}

async function searchAB(push) {
  const from = $("from").value.trim();
  const to = $("to").value.trim();
  const date = $("date").value || todayIso();
  if (!from || !to) return;
  if (fold(from) === fold(to)) {
    resultsEl.innerHTML = '<div class="empty-state">Izhodišče in cilj sta ista postaja.</div>';
    return;
  }
  remember({ tab: "ab", from, to, date });
  if (push) history.replaceState(null, "", `?${new URLSearchParams({ from, to, date })}`);

  try {
    const url = `/api/connections?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}&date=${encodeURIComponent(date)}`;
    const res = await fetch(url);
    if (res.status === 404) {
      resultsEl.innerHTML = '<div class="empty-state">Te postaje ne poznam. Začni tipkati in izberi s seznama.</div>';
      return;
    }
    const data = await res.json();
    renderConnections(data);
    feedDotEl.classList.remove("stale");
    schedulePoll(() => searchAB(false), data.date === todayIso());
  } catch (err) {
    console.error("iskanje ni uspelo", err);
    feedDotEl.classList.add("stale");
    resultsEl.innerHTML = '<div class="empty-state">Iskanje ni uspelo. Strežnik morda ni dosegljiv.</div>';
  }
}

async function searchBoard(push) {
  const station = $("station").value.trim();
  const date = $("board-date").value || todayIso();
  const kind = $("board-kind").value;
  const from = $("board-time").value;
  if (!station) return;
  remember({ tab: "board", station, date, kind, from });
  if (push) {
    const q = new URLSearchParams({ station, date, kind });
    if (from) q.set("from", from);
    history.replaceState(null, "", `?${q}`);
  }

  try {
    // Brez ure streznik izbere sam: za danes tri ure naprej od zdaj, za drug
    // dan cel dan. Vpisana ura to povozi.
    const q = from ? `&from=${encodeURIComponent(from)}&window=360` : "";
    const url = `/api/departures?station=${encodeURIComponent(station)}`
      + `&date=${encodeURIComponent(date)}&kind=${kind}${q}`;
    const res = await fetch(url);
    if (res.status === 404) {
      resultsEl.innerHTML = '<div class="empty-state">Te postaje ne poznam. Začni tipkati in izberi s seznama.</div>';
      return;
    }
    const data = await res.json();
    renderBoard(data);
    feedDotEl.classList.remove("stale");
    schedulePoll(() => searchBoard(false), data.date === todayIso());
  } catch (err) {
    console.error("tabla ni uspela", err);
    feedDotEl.classList.add("stale");
    resultsEl.innerHTML = '<div class="empty-state">Nalaganje ni uspelo.</div>';
  }
}

function remember(obj) {
  try {
    localStorage.setItem("sztrack:last", JSON.stringify(obj));
  } catch (err) {
    /* zaseben zavihek */
  }
}

// ---------- zavihka ----------

function setTab(tab) {
  activeTab = tab;
  for (const b of document.querySelectorAll(".tab")) {
    const on = b.dataset.tab === tab;
    b.classList.toggle("is-on", on);
    b.setAttribute("aria-selected", String(on));
  }
  $("search-ab").hidden = tab !== "ab";
  $("search-board").hidden = tab !== "board";
  resultsEl.innerHTML = "";
  resultHeadEl.innerHTML = "";
  alertsEl.innerHTML = "";
  clearTimeout(pollTimer);
}

document.querySelector(".tabs").addEventListener("click", (ev) => {
  const b = ev.target.closest(".tab");
  if (!b) return;
  setTab(b.dataset.tab);
  if (b.dataset.tab === "board" && $("station").value) searchBoard(true);
  if (b.dataset.tab === "ab" && $("from").value && $("to").value) searchAB(true);
});

$("search-ab").addEventListener("submit", (ev) => { ev.preventDefault(); searchAB(true); });
$("search-board").addEventListener("submit", (ev) => { ev.preventDefault(); searchBoard(true); });

$("swap").addEventListener("click", () => {
  const a = $("from"), b = $("to");
  [a.value, b.value] = [b.value, a.value];
  // Fokus na izhodisce: kdor je gumb dosegel s tipkovnico, mora videti izid.
  a.focus();
  if (a.value && b.value) searchAB(true);
});

// ---------- zagon ----------

function restore() {
  const q = new URLSearchParams(location.search);
  let saved = null;
  try {
    saved = JSON.parse(localStorage.getItem("sztrack:last") || "null");
  } catch (err) {
    /* pokvarjen zapis ni razlog, da stran ne dela */
  }

  const station = q.get("station") || (saved && saved.tab === "board" ? saved.station : "");
  const from = q.get("from") || (saved && saved.from) || "";
  const to = q.get("to") || (saved && saved.to) || "";

  $("date").value = q.get("date") || todayIso();
  $("board-date").value = q.get("date") || todayIso();
  $("board-kind").value = q.get("kind") || (saved && saved.kind) || "odhodi";
  $("board-time").value = q.get("from") || "";
  $("from").value = from;
  $("to").value = to;
  $("station").value = station;

  const wantBoard = q.has("station") || (!q.has("from") && saved && saved.tab === "board");
  if (wantBoard && station) {
    setTab("board");
    searchBoard(false);
  } else if (from && to) {
    setTab("ab");
    searchAB(false);
  } else {
    showOverview();
  }
}

function tickClock() {
  $("clock").textContent = new Intl.DateTimeFormat("sl-SI", {
    timeZone: "Europe/Ljubljana", hour: "2-digit", minute: "2-digit",
    second: "2-digit", hour12: false,
  }).format(new Date());
}

attachSuggest($("from"), $("suggest-from"));
attachSuggest($("to"), $("suggest-to"));
attachSuggest($("station"), $("suggest-station"));

tickClock();
setInterval(tickClock, 1000);
restore();
