"use strict";

// Stran z ovirami. Obvestil je nekaj deset in vsako visi na desetinah vlakov,
// zato je filtriranje po besedilu tu bolj koristno kot razvrscanje po datumu.

const listEl = document.getElementById("list");
const countEl = document.getElementById("count");
const qEl = document.getElementById("q");

let all = [];

// Naslovi obvestil so oblike "DELA NA PROGI: ...", "Vozni red nadomestnega
// prevoza: ...", "OBVESTILO: ...". Vrsta je uporabnejsa od ucinka iz feeda,
// ki je pri skoraj vseh enak ("spremenjen promet").
function kindOf(a) {
  const h = fold(a.header || "");
  if (h.startsWith("dela na progi")) return "dela na progi";
  if (h.includes("nadomestn") || h.includes("avtobusni prevoz")) return "nadomestni prevoz";
  if (h.includes("zdruzen")) return "združene garniture";
  return "obvestilo";
}

const KIND_COLOR = {
  "dela na progi": "#d9b33c",
  "nadomestni prevoz": "#e07b45",
  "združene garniture": "#5aa87d",
  "obvestilo": "#79828f",
};

function periodLabel(a) {
  if (!a.start_ts && !a.end_ts) return "";
  const f = (ts) => new Date(ts * 1000).toLocaleDateString("sl-SI",
    { timeZone: "Europe/Ljubljana", day: "numeric", month: "numeric", year: "numeric" });
  if (a.start_ts && a.end_ts) return `${f(a.start_ts)} – ${f(a.end_ts)}`;
  return a.start_ts ? `od ${f(a.start_ts)}` : `do ${f(a.end_ts)}`;
}

// Vsak opis se konca z isto vljudnostjo in naslovom strani SŽ (ta je ze
// povezava v nogi kartice). Petnajstkrat prebrano nikoli.
const REP = /\s*Potnikom se opravičujemo[\s\S]*$/;

function itemHtml(a) {
  const kind = kindOf(a);
  const color = KIND_COLOR[kind];
  const trains = a.trains || [];
  // Vec kot dvanajst stevilk je stena, ki je nihce ne bere; ostale so za
  // napreden pogled.
  const head = trains.slice(0, 12);
  const rest = trains.slice(12);
  return `
    <article class="alert-card">
      <div class="alert-card-top">
        <span class="kind-tag" style="color:${color};border-color:${color}55">${escapeHtml(kind)}</span>
        ${a.napovedana ? '<span class="kind-tag is-later">napovedano</span>' : ""}
        <span class="alert-period">${escapeHtml(periodLabel(a))}</span>
      </div>
      <h3 class="alert-card-title">${escapeHtml(alertTitle(a.header))}</h3>
      <p class="alert-card-body">${escapeHtml((a.description || "").replace(REP, ""))}
        ${REP.test(a.description || "")
          ? `<span class="adv-only">${escapeHtml((REP.exec(a.description) || [""])[0].trim())}</span>` : ""}</p>
      ${trains.length ? `
        <div class="alert-trains">
          <span class="alert-trains-label">${trains.length} ${sklon(trains.length, "vlak")}:</span>
          ${head.map((t) => `<a class="train-pill" href="/app/train/${encodeURIComponent(t)}">${escapeHtml(t)}</a>`).join("")}
          ${rest.length ? `<span class="adv-only">${rest.map((t) => `<a class="train-pill" href="/app/train/${encodeURIComponent(t)}">${escapeHtml(t)}</a>`).join("")}</span>
                           <span class="more-note">+${rest.length} še (napredni pogled)</span>` : ""}
        </div>` : ""}
      <div class="alert-card-foot adv-only">
        ${escapeHtml(a.effect_label || "")}${a.cause_label ? ` · ${escapeHtml(a.cause_label)}` : ""}
        · <code>${escapeHtml(a.alert_id)}</code>
        ${a.url ? ` · <a href="${escapeHtml(a.url)}" target="_blank" rel="noopener">obvestilo SŽ</a>` : ""}
      </div>
    </article>`;
}

function render() {
  const q = fold(qEl.value.trim());
  const shown = q
    ? all.filter((a) => fold(`${a.header} ${a.description} ${(a.trains || []).join(" ")}`).includes(q))
    : all;

  // "40 veljavnih" bi bilo neresnicno: 24 od njih se ni zacelo. Stevec zato
  // loci, tako kot okno voznje.
  const pozneje = all.filter((a) => a.napovedana).length;
  countEl.textContent = q
    ? `${shown.length} od ${all.length}`
    : pozneje
      ? `${all.length - pozneje} veljavnih, ${pozneje} napovedanih`
      : `${all.length} veljavnih`;

  listEl.innerHTML = shown.length
    ? shown.map(itemHtml).join("")
    : '<div class="empty-state">Za ta filter ni obvestila.</div>';
}

qEl.addEventListener("input", render);

// Preklop pogleda je skupen vsem stranem in zivi v common.js.
initMode();

fetch("/api/alerts")
  .then((r) => r.json())
  .then((data) => {
    // Najprej dela in nadomestni prevozi -- ta dvoje potnika res zadeva.
    const rank = { "dela na progi": 0, "nadomestni prevoz": 1, "združene garniture": 2, "obvestilo": 3 };
    // Veljavno pred napovedanim: potnika najprej zadeva to, kar velja danes.
    all = data.sort((a, b) => (a.napovedana ? 1 : 0) - (b.napovedana ? 1 : 0) ||
                              rank[kindOf(a)] - rank[kindOf(b)] ||
                              (b.trains || []).length - (a.trains || []).length);
    render();
  })
  .catch(() => {
    listEl.innerHTML = '<div class="empty-state">Obvestil ni bilo mogoče naložiti.</div>';
  });
