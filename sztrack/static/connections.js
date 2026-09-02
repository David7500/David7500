"use strict";

// Vstopna stran. Dve vprašanji na isti strani: "od kod do kam" in "kaj gre
// s te postaje". Skupne funkcije (barve, čas, vreme) so v common.js.

const POLL_MS = 30000;

const $ = (id) => document.getElementById(id);
const resultsEl = $("results");
const resultHeadEl = $("result-head");
const alertsEl = $("alerts");
const feedDotEl = $("feed-dot");

// Katero omrezje isce ta stran. Vlaki in avtobusi imata SVOJO stran, ker
// potnik ve, s cim gre, in ju ne isce skupaj -- mesanje je bilo tudi merljivo
// skodljivo: iskanje "ljublj" je vracalo mestna postajalisca in postajo
// Ljubljana potisnilo iz prvih petih zadetkov.
const NETWORK = document.body.dataset.network || "zeleznica";
const IS_BUS = NETWORK === "avtobus";

let pollTimer = null;
let activeTab = "ab";

// Vstopna stran nima preklopa preprosto/napredno. Ce je vprasanje "kdaj mi
// pelje vlak", je izbira med dvema odgovoroma sama po sebi breme: potnik ne ve,
// kaj mu drugi pogled skriva, in dokler ne ve, ga ni razloga vklopiti. Kar je
// bilo tu naprednega, je bodisi razumljivo vsakomur (in je zdaj vedno vidno)
// bodisi ni sodilo na to stran (stevilka postanka, prevoznikova napoved).
// Okno ene voznje preklop obdrzi -- tam gre za eno vozjno in ne vec za izbiro.
loadHealth();

async function loadHealth() {
  const el = $("foot-health");
  if (!el || el.dataset.done) return;
  try {
    const h = await fetch("/api/health").then((r) => r.json());
    // Po omrezju, ne skupno: na strani vlakov je stevilka avtobusnih meritev
    // le zavajajoca -- enako kot vse drugo na tej strani.
    const mine = (h.by_network || {})[NETWORK] || {};
    const runs = mine.runs != null ? mine.runs : h.runs_recorded;
    el.textContent =
      ` · zajetih ${runs.toLocaleString("sl-SI")} meritev v ${h.days_covered} dneh` +
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

  // Kaj naredimo z izbrano postajo. Izbira postaje NE sprozi iskanja: pri
  // "Od-do" clovek pogosto popravi se drugo polje ali dan, vsak vmesni ugib
  // pa je zahteva na streznik za odgovor, ki ga nihce ni prosil. Iskanje
  // sprozi gumb "Poisci" in nic drugega.
  //
  // Kar naredimo, je skok na prazno naslednje polje -- to je klik manj in
  // hkrati pove, da vprasanje se ni celo.
  const takeIt = (name) => {
    input.value = name;
    close();
    paintClear(input);
    paintFavButton();
    const next = [...input.form.querySelectorAll(".station-field input")]
      .find((el) => el !== input && !el.value.trim());
    if (next) next.focus();
    else input.blur();
  };

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
      if (s.recent) li.classList.add("is-recent");
      li.innerHTML = highlight(s.name, q);
      li.addEventListener("mousedown", (ev) => {
        ev.preventDefault();          // ne izgubi fokusa pred klikom
        takeIt(s.name);
      });
      return li;
    }));
    listEl.hidden = false;
    input.setAttribute("aria-expanded", "true");
    if (active >= 0) input.setAttribute("aria-activedescendant", `${listEl.id}-${active}`);
    else input.removeAttribute("aria-activedescendant");
  };

  // Prazno polje ni nic za pokazati -- razen ce clovek tu ze je bil. Postaje
  // iz prejsnjih iskanj so v tem primeru najboljsi ugib, kar ga imamo.
  const query = async () => {
    const q = input.value.trim();
    if (!q) {
      seq += 1;                       // razveljavi morebitno tekoco zahtevo
      items = recentStations();
      active = -1;
      if (!items.length) return close();
      return paint();
    }
    if (q.length < 2) return close();
    const mine = ++seq;
    try {
      const res = await fetch(`/api/stations/search?q=${encodeURIComponent(q)}&limit=8&network=${NETWORK}`)
        .then((r) => r.json());
      if (mine !== seq) return;       // prehitelo ga je novejse tipkanje
      items = res;
      active = -1;
      paint();
    } catch (err) {
      close();
    }
  };

  input.addEventListener("input", () => { paintClear(input); query(); });
  input.addEventListener("focus", () => { if (!input.value.trim()) query(); });

  input.addEventListener("keydown", (ev) => {
    if (listEl.hidden) return;
    if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {
      ev.preventDefault();
      active = (active + (ev.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
      paint();
    } else if (ev.key === "Enter" && active >= 0) {
      ev.preventDefault();
      takeIt(items[active].name);
    } else if (ev.key === "Escape") {
      close();
    }
  });

  input.addEventListener("blur", () => setTimeout(close, 120));
  paintClear(input);
}

// ---------- brisanje vnosa ----------
// Na telefonu je popravek imena postaje sicer sedem pritiskov vracalke. Gumb
// se pokaze samo, kadar je kaj brisati, in ne jemlje tipkovnicnega vrstnega
// reda (`tabindex="-1"`) -- pot skozi obrazec s tipkovnico ostane ista.

function paintClear(input) {
  const btn = input.parentElement.querySelector(".field-clear");
  if (btn) btn.hidden = !input.value;
}

function attachClear(input) {
  const btn = input.parentElement.querySelector(".field-clear");
  if (!btn) return;
  btn.addEventListener("mousedown", (ev) => ev.preventDefault());   // obdrzi fokus
  btn.addEventListener("click", () => {
    input.value = "";
    paintClear(input);
    paintFavButton();
    input.focus();
    input.dispatchEvent(new Event("input"));    // odpre nedavne postaje
  });
}

function highlight(name, q) {
  const i = fold(name).indexOf(fold(q));
  if (i < 0 || !q) return escapeHtml(name);
  return escapeHtml(name.slice(0, i)) +
    "<mark>" + escapeHtml(name.slice(i, i + q.length)) + "</mark>" +
    escapeHtml(name.slice(i + q.length));
}

// ---------- obvestila o ovirah ----------

function alertsHtml(list, note) {
  if (!list || !list.length) return "";
  const items = list.map((a) => `
    <div class="alert-item">
      <strong>${escapeHtml(alertTitle(a.header))}</strong>
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
// `postaja` je postaja, na kateri potnik stoji -- okno vozjne jo zna
// izpostaviti ("pri tebi ob 17:47, +12 min"). Brez nje mora clovek sam iskati
// svojo vrstico med tridesetimi postanki, in to na telefonu.
function journeyHref(trainNo, date, tripId, station) {
  const p = new URLSearchParams();
  if (date) p.set("date", date);
  if (tripId) p.set("trip", tripId);
  if (station) p.set("postaja", station);
  // Pot mora ustrezati omrezju: `/app/train/25` za mestno linijo 25 je
  // napacen naslov, ki ga bo nekdo delil naprej. Streznik zna popraviti, a
  // preusmeritev je zahteva vec in v naslovni vrstici za hip napacen naslov.
  const pot = IS_BUS ? "/app/bus/" : "/app/train/";
  return `${pot}${encodeURIComponent(trainNo)}${p.toString() ? `?${p}` : ""}`;
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
    <div class="conn-where">točnih ${Math.round(t.on_time_share * 100)} %</div>`;
}

function delayChipHtml(delay, kind, at) {
  if (delay == null) return '<span class="chip chip-none">brez podatka</span>';
  const color = delayColor(delay);
  const forecast = kind && kind !== "izmerjeno";
  // "-4 min" je za potnika uganka, "4 min prej" ni. Barva ostane siva: to res
  // ni zamuda -- a prav zato mora povedati beseda, kar barva ne bo.
  const early = isEarly(delay);
  return `<span class="chip${forecast ? " chip-forecast" : ""}${early ? " chip-early" : ""}"
        style="color:${color};border-color:${color}44">
      <span class="chip-n">${early ? Math.abs(Math.round(delay / 60)) : delayLabel(delay)}</span>
      <span class="chip-unit">${early ? "min prej" : "min"}</span>
    </span>
    ${kind ? `<div class="conn-where">${escapeHtml(kind)}${at
      ? (kind === "ocena" ? ` — vozilo je pri postaji ${escapeHtml(at)}`
                          : ` na postaji ${escapeHtml(at)}`)
      : ""}</div>` : ""}`;
}

// Vožnja je "mimo" šele, ko je minil PRIČAKOVANI odhod, ne voznoredni.
// Vlak, ki zamuja pol ure, je ob voznorednem času še vedno na postaji in je
// še vedno možnost -- prav to je razlika, ki jo aplikacija o zamudah dolguje.
function departedMs(c) {
  return new Date(c.expected_dep || c.sched_dep).getTime();
}

function connectionRowHtml(c, nowMs, isNext, date, odKod) {
  const gone = nowMs && departedMs(c) < nowMs;
  const late = c.delay_s != null && Math.abs(c.delay_s) >= 60;
  const color = delayColor(c.delay_s);
  const cd = isNext && nowMs ? countdownLabel(c.expected_dep || c.sched_dep, nowMs) : "";

  // Pricakovani prihod = voznoredni + ista zamuda, torej prenos, ne meritev.
  const expArr = late && c.sched_arr
    ? hhmm(new Date(new Date(c.sched_arr).getTime() + c.delay_s * 1000).toISOString())
    : null;

  return `
    <a class="conn-row${gone ? " is-gone" : ""}${isNext ? " is-next" : ""}${late ? " has-delay" : ""}"
       href="${journeyHref(c.train_no, date, c.trip_id, odKod)}">
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
        <div class="conn-no">${escapeHtml(c.train_no)}${isBus(c.mode)
          ? ` ${lineBadgeHtml(c)}`
          : ""}</div>
        <div class="conn-headsign">${escapeHtml(c.headsign || "")}</div>
      </div>
      <div class="conn-delay">${c.delay_s != null
        ? delayChipHtml(c.delay_s, c.delay_kind, c.delay_at)
        : typicalChipHtml(c.typical_arr || c.typical_dep)}</div>
      <div class="conn-meta">
        ${cd ? `<span class="countdown">${cd}</span>` : ""}
        <span>${durationLabel(c.duration_s)}</span>
        <span>${stopsLabel(c.stops_between)}</span>
        <span>neposredno</span>
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

function transferRowHtml(t, nowMs, date, odKod) {
  const tr = t.transfer;
  const st = TRANSFER_STYLE[(tr && tr.status) || "brez podatka"];
  const planned = Math.round(t.wait_s / 60);
  const actual = tr && tr.wait_s != null ? Math.round(tr.wait_s / 60) : null;
  // Pot ima lahko dve nogi (en prestop) ali stiri (trije prestopi) -- prikaz
  // ne sme predpostavljati dveh. Prestop se izpise ZA vsako nogo razen zadnje.
  const count = t.transfers != null ? t.transfers : t.legs.length - 1;

  const legs = t.legs.map((l, i) => {
    const next = t.legs[i + 1];
    const wait = next ? Math.round((next.dep_s - l.arr_s) / 60) : null;
    return `
      <div class="leg">
        <span class="leg-time">${hhmm(l.dep)}–${hhmm(l.arr)}</span>
        <span class="leg-train">${escapeHtml(l.train_no)}</span>
        <span class="leg-where">${escapeHtml(l.from)} → ${escapeHtml(l.to)}</span>
      </div>
      ${next ? `<div class="leg">
          <span class="leg-wait" style="color:${count === 1 ? st.color : "var(--sev-hard)"}">
            prestop na postaji ${escapeHtml(l.to)} · ${wait} min
          </span>
          ${count === 1 && tr && tr.delay1_s
            ? `<span class="leg-note">prvi vlak ${delayLabel(tr.delay1_s)} min</span>` : ""}
        </div>` : ""}`;
  }).join("");

  // Pri enem prestopu znamo povedati, ali zveza drzi (imamo meritev obeh
  // vlakov na prestopni postaji). Pri vec prestopih tega ne racunamo in zato
  // ne trdimo -- pise samo, koliko jih je.
  const badge = count === 1
    ? transferBadgeHtml(tr, t.wait_s)
    : `<span class="transfer-badge" style="color:var(--ink-mute);border-color:var(--line-firm)">
         ${count} ${count === 2 ? "prestopa" : count === 3 || count === 4 ? "prestopi" : "prestopov"}
       </span>
       <div class="conn-where">najkrajše čakanje ${planned} min</div>`;

  return `
    <a class="conn-row is-transfer" style="border-left-color:${count === 1 ? st.color : "var(--line-firm)"}"
       href="${journeyHref(t.train1, date, t.trip1, odKod)}">
      <div class="conn-times">
        <div class="conn-clock">
          <span class="conn-dep">${hhmm(t.sched_dep)}</span>
          <span class="conn-dash">–</span>
          <span class="conn-arr">${hhmm(t.sched_arr)}</span>
        </div>
      </div>
      <div class="conn-train">
        <div class="conn-no">${t.legs.map((l) => escapeHtml(l.train_no)).join(" → ")}</div>
        <div class="conn-headsign">prek ${escapeHtml(t.via)}</div>
      </div>
      <div class="conn-delay">${badge}</div>
      <div class="conn-meta">
        <span>${durationLabel(t.duration_s)}</span>
        ${count === 1 ? `<span>načrtovano ${planned} min za prestop</span>` : ""}
      </div>
      <div class="legs">${legs}</div>
    </a>`;
}

function renderConnections(data) {
  const list = data.connections || [];
  const legs = data.transfers || [];
  const isToday = data.date === todayIso();
  const nowMs = isToday ? Date.now() : 0;

  paintFavButton();
  resultHeadEl.innerHTML =
    `<span><strong>${escapeHtml(data.from)}</strong> → <strong>${escapeHtml(data.to)}</strong></span>
     <span>${dayLabel(data.date)}</span>
     <span>${list.length} ${list.length === 1 ? "neposredna vožnja" : "neposrednih"}${legs.length
        ? ` · ${legs.length} s ${legs.some((t) => (t.transfers || 1) > 1) ? "prestopi" : "prestopom"}`
        : ""}</span>`;

  if (!list.length && !legs.length) {
    // "od Metlika do Bohinjska Bistrica" je napačno; sklanja se "postaja",
    // ime ostane v imenovalniku -- ista rešitev kot pri "na postaji X".
    resultsEl.innerHTML = `<div class="empty-state">
      Na ta dan ni vožnje od postaje <strong>${escapeHtml(data.from)}</strong>
      do postaje <strong>${escapeHtml(data.to)}</strong> — ne neposredne
      ne z enim prestopom.<br>
      sztrack išče največ en prestop; z dvema morda gre. Preveri tudi drug dan —
      ${IS_BUS ? "ob koncu tedna vozi manj avtobusov" : "ob koncu tedna vozi bistveno manj vlakov"}.
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
      ${gone.map((c) => connectionRowHtml(c, nowMs, false, data.date, data.from)).join("")}
    </details>`);
  }
  rows.push(...ahead.map((c, i) => connectionRowHtml(c, nowMs, i === 0 && nextIdx >= 0, data.date, data.from)));
  if (legs.length) {
    // Naslov naj pove, kaj je spodaj: en prestop ali vec. Ko en prestop ne
    // da nicesar, iscemo naprej in rezultat je lahko tri- ali stirinozen.
    const most = Math.max(...legs.map((t) => t.transfers || t.legs.length - 1));
    rows.push(`<div class="result-head"><span>${most === 1
      ? "Z enim prestopom"
      : "S prestopi — neposredne vožnje ni"}</span></div>`);
    rows.push(...legs.map((t) => transferRowHtml(t, nowMs, data.date, data.from)));
  }
  resultsEl.innerHTML = rows.join("");

  renderAlerts(data.alerts, "Na tej poti so obvestila o ovirah");
}

function boardRowHtml(r, nowMs, isNext, date, station) {
  const gone = nowMs && new Date(r.expected || r.sched).getTime() < nowMs;
  // Ne "zamuja", ampak "ne vozi po voznem redu": mestni avtobus je pogosto
  // PREZGODEN in doslej se to ni videlo nikjer -- vrstica je kazala samo
  // voznoredno uro. Prav ta primer potnik zamudi, ker pride ob njej.
  const off = r.delay_s != null && Math.abs(r.delay_s) >= 60;
  const color = delayColor(r.delay_s);
  const cd = isNext && nowMs ? countdownLabel(r.expected || r.sched, nowMs) : "";
  return `
    <a class="board-row${gone ? " is-gone" : ""}${isNext ? " is-next" : ""}${off ? " has-delay" : ""}"
       href="${journeyHref(r.train_no, date, r.trip_id, station)}">
      <div>
        <div class="board-time">${hhmm(r.sched)}</div>
        ${off ? `<div class="board-expected" style="color:${color}">${hhmm(r.expected)}</div>` : ""}
      </div>
      <div>
        <div class="board-towards">
          ${isBus(r.mode) && r.network === "avtobus" ? lineBadgeHtml(r) : ""}
          <span>${escapeHtml(r.towards)}</span>
        </div>
        <div class="board-train">${isBus(r.mode) && r.network === "avtobus"
          ? ""
          : `${escapeHtml(r.train_no)} `}${isBus(r.mode) && r.network === "zeleznica"
          ? lineBadgeHtml(r) + " "
          : ""}${r.headsign ? escapeHtml(r.headsign) : ""}</div>
      </div>
      <div class="conn-delay">${r.delay_s != null
        ? delayChipHtml(r.delay_s, r.delay_kind, r.delay_from)
        : typicalChipHtml(r.typical, r.typical_from)}</div>
      <div class="board-meta">
        ${cd ? `<span class="countdown">${cd}</span>` : ""}
        ${r.is_terminus ? "<span>konec proge</span>" : ""}
      </div>
    </a>`;
}

// Preklop smeri drzi vrednost v skritem polju, da ostane `.value` isti kot
// pri prejsnjem `<select>`.
function setBoardKind(v) {
  const el = $("board-kind");
  if (el) el.value = v;
  document.querySelectorAll("#board-kind-seg button").forEach((b) => {
    b.setAttribute("aria-pressed", String(b.dataset.kind === v));
  });
}

function renderBoard(data) {
  const list = data.board || [];
  const isToday = data.date === todayIso();
  const nowMs = isToday ? Date.now() : 0;

  paintFavButton();
  resultHeadEl.innerHTML =
    `<span><strong>${escapeHtml(data.station)}</strong></span>
     <span>${data.kind}</span><span>${dayLabel(data.date)}</span>
     <span>${list.length} ${sklon(list.length, data.kind)}${data.window_min >= 1440
        ? " ta dan"
        : ` od ${String(Math.floor(data.from_s / 3600)).padStart(2, "0")}:${String(Math.floor(data.from_s % 3600 / 60)).padStart(2, "0")}, ${Math.round(data.window_min / 60)} h naprej`}</span>`;

  if (!list.length) {
    // "Poskusi drugo uro" je nasvet, ne dejanje -- ponoci je odgovor vedno
    // isti: jutri zjutraj. Gumb ga opravi.
    const jutri = new Date(data.date + "T12:00:00");
    jutri.setDate(jutri.getDate() + 1);
    const jutriIso = jutri.toISOString().slice(0, 10);
    resultsEl.innerHTML = `<div class="empty-state">
      V tem oknu s postaje <strong>${escapeHtml(data.station)}</strong>
      ni ${escapeHtml(sklon(0, data.kind))}.
      <div class="empty-act">
        <button type="button" class="btn btn-quiet" id="board-tomorrow"
                data-date="${jutriIso}">pokaži ${dayLabel(jutriIso)} od 05:00</button>
      </div>
    </div>`;
    const gumb = $("board-tomorrow");
    if (gumb) gumb.addEventListener("click", () => {
      $("board-date").value = gumb.dataset.date;
      $("board-time").value = "05:00";
      searchBoard(true);
    });
    alertsEl.innerHTML = "";
    return;
  }

  let nextIdx = -1;
  if (isToday) nextIdx = list.findIndex((r) => new Date(r.expected || r.sched).getTime() >= nowMs);
  resultsEl.innerHTML = list.map((r, i) => boardRowHtml(r, nowMs, i === nextIdx, data.date, data.station)).join("");
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

  return `
    <section class="overview">
      <div class="chips chips-top">
        ${POPULAR.map(([a, b]) => `<button type="button" class="route-chip"
            data-from="${escapeHtml(a)}" data-to="${escapeHtml(b)}">${escapeHtml(a)} → ${escapeHtml(b)}</button>`).join("")}
      </div>

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
            · najslabša ${delayLabel(day.worst_s)} min
          </div>
        </div>` : ""}

      ${o.disruptions ? `<a class="ov-link" href="/app/ovire">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M12 9v5M12 17.5v.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"></path>
        </svg>
        ${o.disruptions} veljavnih obvestil o ovirah na progah
      </a>` : ""}

    </section>`;
}

// Avtobusni pregled govori o SEDANJOSTI, ne o zgodovini: zajem je nov in
// vsaka številka o preteklosti bi obljubljala več, kot ve. Zato koliko jih
// vozi, koliko jih ima GPS in kako hitro se premikajo -- to o njih res vemo.
function busOverviewHtml(o) {
  return `
    <section class="overview">
      <div class="ov-head">
        <h2>Kako vozijo avtobusi</h2>
        <span class="ov-sub">${o.live_vehicles} zdaj na poti</span>
      </div>

      ${o.today && o.today.runs ? `
        <div class="ov-card">
          <div class="ov-card-head">
            <span>Končna zamuda, danes</span>
            <strong style="color:${delayColor(o.today.median_s)}">mediana ${delayLabel(o.today.median_s)} min</strong>
          </div>
          ${bucketBarHtml(o.today.buckets, o.today.runs)}
          <div class="ov-card-foot">
            ${o.today.runs} zajetih voženj · točnih ${Math.round(o.today.on_time_share * 100)} %
            ${o.with_gps ? `· ${o.with_gps} vozil oddaja svojo lego` : ""}
          </div>
        </div>` : `
        <div class="ov-card">
          <div class="ov-card-foot">Danes še ni dovolj zajetih voženj za sliko dneva.</div>
        </div>`}
    </section>`;
}

async function showOverview() {
  if (IS_BUS) {
    try {
      const o = await fetch("/api/overview/bus").then((r) => r.json());
      resultsEl.innerHTML = busOverviewHtml(o);
    } catch (err) {
      resultsEl.innerHTML = '<div class="empty-state">Vpiši postajališče ali izhodišče in cilj.</div>';
    }
    return;
  }
  try {
    const o = await fetch("/api/overview").then((r) => r.json());
    resultsEl.innerHTML = overviewHtml(o);
    resultsEl.querySelectorAll(".route-chip").forEach((b) => {
      b.addEventListener("click", () => {
        setTab("ab");
        $("from").value = b.dataset.from;
        $("to").value = b.dataset.to;
        paintAllClears();
        searchAB(true);
      });
    });
  } catch (err) {
    resultsEl.innerHTML = '<div class="empty-state">Vpiši izhodišče in cilj ali izberi postajo.</div>';
  }
}


// ---------- shranjene in nedavne poti ----------
// Potnik vozi isto pot vsak dan. Zadnje iskanje smo si zapomnili ze prej, a
// eno samo -- kdor ima sluzbo in tesco, ima dve. Hranimo jih po omrezjih,
// ker sta strani loceni in bi mesan seznam vodil nazaj v isto zmedo.
//
// Dva seznama, ker sta dve vprasanji: `fav` je "to je moja pot" in ga clovek
// pove sam (zvezdica), `recent` je "tu sem pravkar bil" in se napise sam.
// Oba sta pod iskalnikom in ne v pregledu: pregled prva poizvedba pobrise
// prav takrat, ko bi seznam rabil za naslednjo.

const FAV_KEY = "sztrack:fav";
const FAV_MAX = 8;
const RECENT_KEY = "sztrack:recent";
const RECENT_MAX = 6;

function favLoad() {
  try {
    const all = JSON.parse(localStorage.getItem(FAV_KEY) || "[]");
    return Array.isArray(all) ? all.filter((f) => f && f.net === NETWORK) : [];
  } catch (err) {
    return [];
  }
}

function favSave(list) {
  try {
    const others = (JSON.parse(localStorage.getItem(FAV_KEY) || "[]") || [])
      .filter((f) => f && f.net !== NETWORK);
    localStorage.setItem(FAV_KEY, JSON.stringify([...others, ...list.slice(0, FAV_MAX)]));
  } catch (err) {
    /* zaseben zavihek ni razlog, da stran ne dela */
  }
}

function favKey(f) {
  return f.kind === "board" ? `b:${f.station}:${f.dir || "odhodi"}` : `a:${f.from}:${f.to}`;
}

function favLabel(f) {
  return f.kind === "board"
    ? `${f.station}${f.dir === "prihodi" ? " · prihodi" : ""}`
    : `${f.from} → ${f.to}`;
}

function favCurrent() {
  if (activeTab === "board") {
    const station = $("station").value.trim();
    return station ? { net: NETWORK, kind: "board", station, dir: $("board-kind").value } : null;
  }
  const from = $("from").value.trim();
  const to = $("to").value.trim();
  return from && to ? { net: NETWORK, kind: "ab", from, to } : null;
}

function favToggle() {
  const cur = favCurrent();
  if (!cur) return;
  const list = favLoad();
  const at = list.findIndex((f) => favKey(f) === favKey(cur));
  if (at >= 0) list.splice(at, 1);
  else list.unshift(cur);
  favSave(list);
  paintFavButton();
  renderRecents();
}

function paintFavButton() {
  const btn = $("fav-toggle");
  if (!btn) return;
  const cur = favCurrent();
  btn.hidden = !cur;
  if (!cur) return;
  const on = favLoad().some((f) => favKey(f) === favKey(cur));
  btn.setAttribute("aria-pressed", String(on));
  btn.title = on ? "odstrani med shranjenimi" : "shrani to pot";
  btn.textContent = on ? "★ shranjeno" : "☆ shrani";
}

function recentLoad() {
  try {
    const all = JSON.parse(localStorage.getItem(RECENT_KEY) || "[]");
    return Array.isArray(all) ? all.filter((f) => f && f.net === NETWORK) : [];
  } catch (err) {
    return [];
  }
}

function recentAdd(entry) {
  const list = recentLoad();
  if (list.length && favKey(list[0]) === favKey(entry)) return false;   // ista kot prej
  const rest = list.filter((f) => favKey(f) !== favKey(entry));
  try {
    const others = (JSON.parse(localStorage.getItem(RECENT_KEY) || "[]") || [])
      .filter((f) => f && f.net !== NETWORK);
    localStorage.setItem(RECENT_KEY,
      JSON.stringify([...others, entry, ...rest.slice(0, RECENT_MAX - 1)]));
  } catch (err) {
    return false;
  }
  return true;
}

// Imena postaj iz prejsnjih iskanj -- to je vse, kar znamo ponuditi praznemu
// polju. Vrstni red je vrstni red obiska, ne abecedni: zadnja je najverjetnejsa.
function recentStations() {
  const seen = new Set();
  const out = [];
  for (const f of recentLoad()) {
    for (const name of [f.station, f.from, f.to]) {
      if (!name || seen.has(name)) continue;
      seen.add(name);
      out.push({ name, recent: true });
    }
  }
  return out.slice(0, 6);
}

function chipHtml(f, saved) {
  return `<button type="button" class="route-chip${saved ? " fav-chip" : ""}"
      data-fav="${escapeHtml(favKey(f))}">${saved ? "★ " : ""}${escapeHtml(favLabel(f))}</button>`;
}

let recentsSig = null;

function renderRecents() {
  const el = $("recents");
  if (!el) return;
  const cur = favCurrent();
  const curKey = cur ? favKey(cur) : null;
  const saved = favLoad();
  const savedKeys = new Set(saved.map(favKey));
  // Zeton za poizvedbo, ki je pravkar odprta, je klik nikamor -- in na
  // telefonu vrstica zetonov drugo vsebino potiska navzdol.
  const recent = recentLoad()
    .filter((f) => !savedKeys.has(favKey(f)) && favKey(f) !== curKey);

  // Tabla se osvezuje vsakih 30 s. Ce se seznam ni spremenil, ga ne
  // prerisujemo -- sicer bi zetoni pod prstom utripali.
  const sig = `${saved.map(favKey).join(",")}|${recent.map(favKey).join(",")}`;
  if (sig === recentsSig) return;
  recentsSig = sig;

  el.innerHTML = saved.length || recent.length
    ? `<div class="chips">
        ${saved.map((f) => chipHtml(f, true)).join("")}
        ${recent.map((f) => chipHtml(f, false)).join("")}
      </div>`
    : "";
  wireFavChips(el);
}

function openFav(key) {
  const f = [...favLoad(), ...recentLoad()].find((x) => favKey(x) === key);
  if (!f) return;
  if (f.kind === "board") {
    setTab("board");
    $("station").value = f.station;
    setBoardKind(f.dir || "odhodi");
    paintAllClears();
    searchBoard(true);
  } else {
    setTab("ab");
    $("from").value = f.from;
    $("to").value = f.to;
    paintAllClears();
    searchAB(true);
  }
}

function wireFavChips(root) {
  root.querySelectorAll("[data-fav]").forEach((b) => {
    b.addEventListener("click", () => openFav(b.dataset.fav));
  });
}

// ---------- poizvedbe ----------

// Na telefonu je obrazec cel zaslon in odgovor pade pod pregib: po pritisku
// na "Poisci" clovek vidi isto sliko kot prej. Pomik naredimo samo ob lastnem
// iskanju -- ob osvezitvi vsakih 30 s bi stran skakala med branjem.
function revealResults() {
  if (window.innerWidth > 720) return;
  const bar = document.querySelector(".result-bar");
  if (!bar) return;
  if (bar.getBoundingClientRect().top < window.innerHeight * 0.75) return;
  bar.scrollIntoView({ behavior: "smooth", block: "start" });
}

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
    const url = `/api/connections?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`
      + `&date=${encodeURIComponent(date)}&network=${NETWORK}`;
    const res = await fetch(url);
    if (res.status === 404) {
      resultsEl.innerHTML = '<div class="empty-state">Te postaje ne poznam. Začni tipkati in izberi s seznama.</div>';
      return;
    }
    const data = await res.json();
    renderConnections(data);
    if (push) revealResults();
    schedulePoll(() => searchAB(false), data.date === todayIso());
  } catch (err) {
    console.error("iskanje ni uspelo", err);
    refreshFeedDot();   // zahteva ni uspela -- naj pika pove, kaj ve
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
      + `&date=${encodeURIComponent(date)}&kind=${kind}&network=${NETWORK}${q}`;
    const res = await fetch(url);
    if (res.status === 404) {
      resultsEl.innerHTML = '<div class="empty-state">Te postaje ne poznam. Začni tipkati in izberi s seznama.</div>';
      return;
    }
    const data = await res.json();
    renderBoard(data);
    if (push) revealResults();
    schedulePoll(() => searchBoard(false), data.date === todayIso());
  } catch (err) {
    console.error("tabla ni uspela", err);
    refreshFeedDot();   // zahteva ni uspela -- naj pika pove, kaj ve
    resultsEl.innerHTML = '<div class="empty-state">Nalaganje ni uspelo.</div>';
  }
}

// Doslej je bila zapomnjena poizvedba svoj zapis (`sztrack:last`) in ta NI
// bil locen po omrezju: kdor je na /app iskal Celje–Ljubljana in nato odprl
// /app/bus, je tam dobil isto vprasanje, resemo na avtobusnem omrezju
// ("Ljubljana AP") in prazen odgovor. Zdaj je zadnja poizvedba preprosto
// prva v seznamu nedavnih, ta pa je po omrezju locen ze od zacetka.
function remember(obj) {
  const cur = obj.tab === "board"
    ? { net: NETWORK, kind: "board", station: obj.station, dir: obj.kind }
    : { net: NETWORK, kind: "ab", from: obj.from, to: obj.to };
  recentAdd(cur);
  renderRecents();
}

// ---------- postajališča v bližini ----------
// Za mestni avtobus je to najpogostejši način, kako človek najde postajo:
// imena ne ve, ve pa, kje stoji.

function nearMeUnavailable(msg) {
  resultHeadEl.innerHTML = "";
  resultsEl.innerHTML = `<div class="empty-state">${escapeHtml(msg)}</div>`;
}

async function showNearby() {
  if (!navigator.geolocation) {
    return nearMeUnavailable("Brskalnik ne pozna lokacije.");
  }
  // Brskalniki dovolijo lokacijo samo na HTTPS ali localhostu. Po HTTP na
  // domacem naslovu klic tiho odpove, zato to povemo vnaprej in ne cakamo.
  if (!window.isSecureContext) {
    return nearMeUnavailable(
      "Lokacija je na voljo samo prek HTTPS ali na localhostu. "
      + "Vpiši ime postajališča.");
  }
  resultsEl.innerHTML = '<div class="empty-state">iščem lokacijo …</div>';

  navigator.geolocation.getCurrentPosition(async (pos) => {
    const { latitude, longitude } = pos.coords;
    try {
      const list = await fetch(
        `/api/stations/near?lat=${latitude}&lon=${longitude}&network=${NETWORK}&limit=8`
      ).then((r) => r.json());
      if (!list.length) {
        return nearMeUnavailable(IS_BUS
          ? "V treh kilometrih ni postajališča."
          : "V treh kilometrih ni železniške postaje.");
      }
      resultHeadEl.innerHTML = `<span>Najbližja ${IS_BUS ? "postajališča" : "postaje"}</span>
        <span>zračna razdalja, ne po poti</span>`;
      resultsEl.innerHTML = `<div class="near-list">${list.map((x) => `
        <button type="button" class="near-row" data-name="${escapeHtml(x.name)}">
          <span class="near-name">${escapeHtml(x.name)}</span>
          <span class="near-dist">${x.meters < 1000
            ? `${x.meters} m`
            : `${(x.meters / 1000).toFixed(1).replace(".", ",")} km`}</span>
        </button>`).join("")}</div>`;
      resultsEl.querySelectorAll(".near-row").forEach((b) => {
        b.addEventListener("click", () => {
          $("station").value = b.dataset.name;
          paintAllClears();
          searchBoard(true);
        });
      });
    } catch (err) {
      nearMeUnavailable("Postajališč ni bilo mogoče poiskati.");
    }
  }, (err) => {
    nearMeUnavailable(err.code === err.PERMISSION_DENIED
      ? "Dostop do lokacije je zavrnjen. Vpiši ime postajališča."
      : "Lokacije ni bilo mogoče dobiti.");
  }, { enableHighAccuracy: false, timeout: 8000, maximumAge: 60000 });
}

$("near-me").addEventListener("click", showNearby);
$("fav-toggle").addEventListener("click", favToggle);

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
  // Gumb za shranjevanje se nanasa na trenutno poizvedbo; ob preklopu zavihka
  // je ta druga in gumb mora to pokazati (ali izginiti, ce polja so prazna).
  paintFavButton();
  clearTimeout(pollTimer);
}

document.querySelector(".tabs").addEventListener("click", (ev) => {
  const b = ev.target.closest(".tab");
  if (!b) return;
  setTab(b.dataset.tab);
  const board = b.dataset.tab === "board";
  if (board && $("station").value) searchBoard(true);
  else if (!board && $("from").value && $("to").value) searchAB(true);
  // Prazna polja ne pomenijo prazne strani: `setTab` je rezultate pobrisal,
  // zato vrnemo pregled. Brez tega preklop zavihka pokaze bel prostor.
  else showOverview();
});

$("search-ab").addEventListener("submit", (ev) => { ev.preventDefault(); searchAB(true); });
$("search-board").addEventListener("submit", (ev) => { ev.preventDefault(); searchBoard(true); });

$("swap").addEventListener("click", () => {
  const a = $("from"), b = $("to");
  [a.value, b.value] = [b.value, a.value];
  paintAllClears();
  // Fokus na izhodisce: kdor je gumb dosegel s tipkovnico, mora videti izid.
  a.focus();
  if (a.value && b.value) searchAB(true);
});

// Preklop smeri: kadar je tabla ze na zaslonu, jo takoj osvezi -- gumb, ki
// vidno stanje pusti pri miru, je videti kot okvara. Dokler ni izida, samo
// zapise izbiro (isto pravilo kot pri predlogah postaj: isce samo gumb).
document.querySelectorAll("#board-kind-seg button").forEach((b) => {
  b.addEventListener("click", () => {
    setBoardKind(b.dataset.kind);
    if ($("station").value.trim() && resultsEl.querySelector(".board-row, .empty-state")) {
      searchBoard(true);
    }
  });
});

// ---------- zagon ----------

function restore() {
  const q = new URLSearchParams(location.search);
  const saved = recentLoad()[0] || null;
  const wasBoard = saved && saved.kind === "board";

  const station = q.get("station") || (wasBoard ? saved.station : "");
  const from = q.get("from") || (saved && saved.from) || "";
  const to = q.get("to") || (saved && saved.to) || "";

  $("date").value = q.get("date") || todayIso();
  $("board-date").value = q.get("date") || todayIso();
  setBoardKind(q.get("kind") || (wasBoard && saved.dir) || "odhodi");
  $("board-time").value = q.get("from") || "";
  $("from").value = from;
  $("to").value = to;
  $("station").value = station;
  paintAllClears();

  const wantBoard = q.has("station") || (!q.has("from") && wasBoard);
  if (wantBoard && station) {
    setTab("board");
    searchBoard(false);
  } else if (from && to) {
    // Polji sta izpolnjeni iz spomina ali naslova, iskanja pa NE sprozimo,
    // razen ce je pot prislo iz naslova (deljena povezava -- tam je odgovor
    // prav to, po kar je clovek prisel). Vrnitev na stran je drugo: takrat
    // je vprasanje samo predlog in odgovor caka na "Poisci".
    setTab("ab");
    if (q.has("from") && q.has("to")) searchAB(false);
    else showOverview();
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

const STATION_INPUTS = ["from", "to", "station"];

function paintAllClears() {
  for (const id of STATION_INPUTS) paintClear($(id));
}

for (const id of STATION_INPUTS) {
  attachSuggest($(id), $(`suggest-${id}`));
  attachClear($(id));
}
renderRecents();

tickClock();
setInterval(tickClock, 1000);
refreshFeedDot();
pollWhileVisible(refreshFeedDot, 30000);
restore();
