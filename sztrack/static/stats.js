"use strict";

// Razrezi zajetega. Grafi so ročno risan SVG brez knjižnice, kot povsod v tem
// projektu -- oblike so preproste in knjižnica bi prinesla več teže kot koristi.

const $ = (id) => document.getElementById(id);

const INK_AXIS = "#79828f";
const INK_GRID = "#23272f";

// Vrsta vlaka je predpona številke. Brez razlage je to šifra.
const KIND_LABEL = {
  LP: "LP — lokalni potniški",
  LPV: "LPV — lokalni potniški (vlak)",
  RG: "RG — regionalni",
  IC: "IC — InterCity",
  ICS: "ICS — InterCity Slovenija",
  EC: "EC — EuroCity",
  MV: "MV — mednarodni",
  EN: "EN — EuroNight",
  MO: "MO — motorni",
  AVT: "AVT — avtovlak",
  LRG: "LRG — regionalni",
  "nadomestni bus": "nadomestni prevoz",
};

function svgEl(name, attrs, text) {
  const el = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v != null) el.setAttribute(k, v);
  }
  if (text != null) el.textContent = text;
  return el;
}

// ---------- vodoravni stolpci: mediana zamude + trak porazdelitve ----------
// Dve številki na vrstico, ne ena: mediana pove tipično vožnjo, trak pa,
// kako razpršene so. Vlak z mediano 5 min je nekaj drugega, če je polovica
// voženj točnih in polovica pol ure v zamudi.

function barsHtml(rows, labelOf) {
  if (!rows.length) return '<div class="empty-state">premalo zajetih voženj za ta rez</div>';
  const maxMedian = Math.max(60, ...rows.map((r) => r.median_s || 0));
  // Vsi stolpci pomnozeni z isto vrednostjo: razmerja ostanejo, najdaljsemu
  // pa ostane prostor za stevilko. Brez tega "+22 min" pade cez stolpec
  // "tocnih" in se dve stevilki prekrivata.
  const SCALE = 0.8;

  return `<div class="bars">${rows.map((r) => {
    const label = labelOf ? labelOf(r) : r.key;
    const width = ((r.median_s || 0) / maxMedian) * 100 * SCALE;
    const color = delayColor(r.median_s);
    const total = r.n;
    const segs = [["točno", 60], ["1–5 min", 300], ["5–15 min", 900], ["nad 15 min", 1800]]
      .map(([name, ref]) => {
        const n = r.buckets[name] || 0;
        if (!n) return "";
        return `<span class="bucket" style="width:${(n / total) * 100}%;background:${delayColor(ref)}"
                  title="${escapeHtml(name)}: ${n} voženj"></span>`;
      }).join("");

    return `
      <div class="bar-row">
        <div class="bar-label">${escapeHtml(label)}</div>
        <div class="bar-track">
          <div class="bar-fill" style="width:${width}%;background:${color}"></div>
          <span class="bar-value" style="color:${color}">${delayLabel(r.median_s)} min</span>
        </div>
        <div class="bar-share">${Math.round(r.on_time_share * 100)} %</div>
        <div class="bar-n">${r.n}</div>
        <div class="bar-dist">${segs}</div>
      </div>`;
  }).join("")}
    <div class="bar-head">
      <span></span><span>mediana končne zamude</span><span>točnih</span><span>voženj</span>
    </div>
  </div>`;
}

// ---------- krivulja čez ure ----------

function hourChart(rows) {
  if (rows.length < 3) return '<div class="empty-state">premalo ur z dovolj vožnjami</div>';
  const w = Math.max(320, Math.min(880, document.getElementById("by-hour").clientWidth - 4));
  const M = { t: 18, r: 14, b: 40, l: 40 };
  const ih = 150;
  const iw = w - M.l - M.r;
  const H = M.t + ih + M.b;
  const svg = svgEl("svg", { width: w, height: H, role: "img",
                             "aria-label": "mediana zamude po uri odhoda" });

  const maxV = Math.max(300, ...rows.map((r) => r.median_s || 0));
  const top = Math.ceil(maxV / 60 / 2) * 2 * 60;
  // Os je URA, ne zaporedna številka vrstice. Ure, ki nimajo dovolj voženj,
  // v podatkih manjkajo; če bi risali po zaporedju, bi bila luknja od 00 do
  // 03 videti kot en korak in krivulja bi lagala o tem, kaj je izmerjeno.
  const hours = rows.map((r) => Number(r.key));
  const x = (h) => M.l + ((h - 0) / 23) * iw;
  const y = (v) => M.t + ih - (v / top) * ih;

  for (let i = 0; i <= 4; i += 1) {
    const v = (top / 4) * i;
    svg.appendChild(svgEl("line", { x1: M.l, x2: M.l + iw, y1: y(v), y2: y(v),
                                    stroke: i === 0 ? INK_AXIS : INK_GRID, "stroke-width": 1 }));
    svg.appendChild(svgEl("text", { x: M.l - 8, y: y(v) + 4, "text-anchor": "end",
                                    fill: INK_AXIS, "font-size": 10,
                                    "font-family": "'IBM Plex Mono', monospace" },
                          `${Math.round(v / 60)}`));
  }
  svg.appendChild(svgEl("text", { x: M.l - 8, y: M.t - 6, "text-anchor": "end", fill: INK_AXIS,
                                  "font-size": 9, "font-family": "'IBM Plex Sans', sans-serif" },
                        "min"));

  // Debelina crte nosi stevilo voznj: tanka crta = malo vzorcev, in bralec
  // naj vidi, kje je krivulja slabo podprta.
  const maxN = Math.max(...rows.map((r) => r.n));
  for (let i = 0; i < rows.length - 1; i += 1) {
    const a = rows[i];
    const b = rows[i + 1];
    // Sosednji uri povežemo, luknje ne: med 00 in 03 ni izmerjenega ničesar.
    if (hours[i + 1] - hours[i] > 1) continue;
    svg.appendChild(svgEl("line", {
      x1: x(hours[i]), y1: y(a.median_s || 0),
      x2: x(hours[i + 1]), y2: y(b.median_s || 0),
      stroke: "#4a515c", "stroke-width": 1 + 2 * (Math.min(a.n, b.n) / maxN),
      "stroke-linecap": "round",
    }));
  }
  rows.forEach((r, i) => {
    const c = svgEl("circle", { cx: x(hours[i]), cy: y(r.median_s || 0), r: 3.5,
                                fill: delayColor(r.median_s) });
    c.appendChild(svgEl("title", {},
      `${r.key}:00 — mediana ${delayLabel(r.median_s)} min, ` +
      `${Math.round(r.on_time_share * 100)} % točnih, ${r.n} voženj`));
    svg.appendChild(c);
  });
  for (let h = 0; h <= 23; h += 3) {
    svg.appendChild(svgEl("text", { x: x(h), y: H - 22, "text-anchor": "middle",
                                    fill: INK_AXIS, "font-size": 10,
                                    "font-family": "'IBM Plex Mono', monospace" },
                          String(h).padStart(2, "0")));
  }
  svg.appendChild(svgEl("text", { x: M.l + iw / 2, y: H - 6, "text-anchor": "middle",
                                  fill: INK_AXIS, "font-size": 10,
                                  "font-family": "'IBM Plex Sans', sans-serif" },
                        "ura odhoda z izhodišča"));
  return svg;
}

// ---------- tile ----------

function tileHtml(label, value, sub, color) {
  return `<div class="tile">
    <div class="tile-label">${escapeHtml(label)}</div>
    <div class="tile-value"${color ? ` style="color:${color}"` : ""}>${value}</div>
    <div class="tile-sub">${escapeHtml(sub || "")}</div>
  </div>`;
}

// ---------- zagon ----------

// Preklop pogleda je skupen vsem stranem in zivi v common.js.
initMode();

// Katero omrežje kaže stran. Skupna številka bi bila povprečje vlaka in
// mestnega avtobusa, kar ne opisuje ne enega ne drugega.
let NET = "zeleznica";

async function load() {
  const [b, ranking] = await Promise.all([
    fetch(`/api/stats/breakdowns?network=${NET}`).then((r) => r.json()),
    fetch(`/api/stats?days=90&network=${NET}`).then((r) => r.json()),
  ]);

  const allRuns = b.runs;
  const onTime = b.by_day.reduce((acc, d) => acc + d.on_time_share * d.n, 0) / Math.max(allRuns, 1);
  const medians = b.by_day.map((d) => d.median_s).sort((x, y) => x - y);
  const overallMedian = medians.length ? medians[Math.floor(medians.length / 2)] : null;

  const what = NET === "avtobus" ? "avtobusnih voženj" : "voženj";
  $("lead").innerHTML = allRuns
    ? `Iz lastnega zajema: <strong>${allRuns.toLocaleString("sl-SI")}</strong> ${what}
       v <strong>${b.days.length}</strong> ${b.days.length === 1 ? "dnevu" : "dneh"},
       od ${escapeHtml(b.days[0] || "—")}.
       Vsaka vožnja prispeva svojo <strong>končno</strong> zamudo — tisto, s katero
       pripelje na cilj.`
    : `Za to omrežje še ni zajetih voženj. Zajem avtobusov se je začel danes;
       številke se bodo nabrale same.`;
  $("kind-title").textContent = NET === "avtobus" ? "Po prevozniku" : "Po vrsti vlaka";
  $("worst-title").textContent = NET === "avtobus"
    ? "Linije z največjo mediano zamude"
    : "Vlaki z največjo mediano zamude";

  $("tiles").innerHTML = [
    tileHtml("Zajetih voženj", allRuns.toLocaleString("sl-SI"), `v ${b.days.length} dneh`),
    tileHtml("Mediana dneva", `${delayLabel(overallMedian)} min`, "mediana čez dneve",
             delayColor(overallMedian)),
    tileHtml("Delež točnih", `${Math.round(onTime * 100)} %`, "končna zamuda do 5 min"),
  ].join("");

  $("by-kind").innerHTML = barsHtml(b.by_kind, (r) => KIND_LABEL[r.key] || r.key);
  $("by-hour").replaceChildren(hourChart(b.by_hour));
  $("by-weekday").innerHTML = barsHtml(b.by_weekday);
  $("by-day").innerHTML = barsHtml(b.by_day, (r) => dayLabel(r.key));

  const weekdayN = b.by_weekday.reduce((a, r) => a + r.n, 0);
  $("dow-note").textContent = b.by_weekday.length < 7
    ? `Zajetih je ${b.days.length} dni, zato nekateri dnevi še nimajo dovolj voženj in jih ni na seznamu.`
    : `Vsi dnevi imajo vzorec (skupaj ${weekdayN} voženj), a pri ${b.days.length} dneh zajema ` +
      "je vsak dan v tednu zastopan le enkrat ali dvakrat — razlike med njimi so še sum.";

  const worst = ranking.filter((r) => r.runs >= 3).slice(0, 20);
  $("worst").innerHTML = `<div class="rank">${worst.map((r) => `
    <a class="rank-row" href="/app/train/${encodeURIComponent(r.train_no)}">
      <span class="rank-no">${escapeHtml(r.train_no)}</span>
      <span class="rank-val" style="color:${delayColor(r.median_s)}">${delayLabel(r.median_s)} min</span>
      <span class="rank-sub">p90 ${delayLabel(r.p90_s)} · najslabša ${delayLabel(r.max_s)} · ${pluralRuns(r.runs)}</span>
    </a>`).join("")}</div>`;
}

function reload() {
  load().catch((err) => {
    console.error(err);
    $("lead").textContent = "Statistike ni bilo mogoče naložiti.";
  });
}

document.querySelector(".tabs").addEventListener("click", (ev) => {
  const b = ev.target.closest(".tab");
  if (!b || b.dataset.net === NET) return;
  NET = b.dataset.net;
  for (const t of document.querySelectorAll(".tab")) {
    const on = t.dataset.net === NET;
    t.classList.toggle("is-on", on);
    t.setAttribute("aria-selected", String(on));
  }
  reload();
});

reload();

let resizeTimer = null;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => reload(), 200);
});
