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

// Ali zapora velja danes (`kdaj`, `zapore.kdaj`). Obdobje obvestila pokriva
// vse dni, zapora pa velja le nekatere in le ob nekaterih urah. Besedilo je
// isto kot v oblačku zapore na zemljevidu (`kdajZapore`). Obvestilo, ki ga
// strežnik ne razume celega, `kdaj` nima in ne dobi nič.
function kdajHtml(k) {
  if (!k) return "";
  // Pri enem odseku ga pove že naslov obvestila.
  const odsek = (o) => (k.odsekov > 1 ? `<span class="kdaj-odsek">odsek ${escapeHtml(o)}</span>` : "");
  if (k.danes.length) {
    return k.danes.map((p) => `<p class="alert-kdaj is-${p.stanje}">${odsek(p.odsek)}${
      escapeHtml(kdajZapore(p))}</p>`).join("");
  }
  const n = k.naslednjic;
  return `<p class="alert-kdaj is-ne">${n ? odsek(n.odsek) : ""}${escapeHtml(
    ["danes ne velja", n ? `naslednjič ${dayLabel(n.dan)}, ${oknaZapore(n.okna)}` : ""]
      .filter(Boolean).join(" · "))}</p>`;
}

// Med veljavnimi najprej, kar velja danes (zdaj, pozneje, že končano), nato
// tista, za katera ne vemo, nazadnje tista, ki danes po besedilu ne veljajo.
const KDAJ_RANG = { zdaj: 0, pozneje: 1, koncano: 2 };
function kdajRang(a) {
  if (!a.kdaj) return 3;
  if (!a.kdaj.danes.length) return 4;
  return Math.min(...a.kdaj.danes.map((p) => KDAJ_RANG[p.stanje]));
}

function itemHtml(a) {
  const kind = kindOf(a);
  const color = KIND_COLOR[kind];
  const trains = a.trains || [];
  // Vec kot dvanajst stevilk je stena, ki je nihce ne bere; ostale so en dotik
  // stran. Prej so bile v naprednem pogledu -- da vidis, ali obvestilo zadene
  // tvoj vlak, si moral preklopiti nacin strani (5. 10. 2026).
  const head = trains.slice(0, 12);
  const rest = trains.slice(12);
  const pill = (t) => `<a class="train-pill" href="/app/train/${encodeURIComponent(t)}">${escapeHtml(t)}</a>`;
  return `
    <article class="alert-card">
      <div class="alert-card-top">
        <span class="kind-tag" style="color:${color};border-color:${color}55">${escapeHtml(kind)}</span>
        ${a.napovedana ? '<span class="kind-tag is-later">napovedano</span>' : ""}
        <span class="alert-period">${escapeHtml(periodLabel(a))}</span>
      </div>
      <h3 class="alert-card-title">${escapeHtml(alertTitle(a.header))}</h3>
      ${kdajHtml(a.kdaj)}
      <p class="alert-card-body">${escapeHtml((a.description || "").replace(REP, ""))}
        ${REP.test(a.description || "")
          ? `<span class="adv-only">${escapeHtml((REP.exec(a.description) || [""])[0].trim())}</span>` : ""}</p>
      ${trains.length ? `
        <div class="alert-trains">
          <span class="alert-trains-label">${trains.length} ${sklon(trains.length, "vlak")}:</span>
          ${head.map(pill).join("")}
          ${rest.length ? `<span class="alert-vec" hidden>${rest.map(pill).join("")}</span>
                           <button type="button" class="vec-vlakov">+${rest.length} še</button>` : ""}
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
listEl.addEventListener("click", (e) => {
  const b = e.target.closest(".vec-vlakov");
  if (!b) return;
  b.previousElementSibling.hidden = false;
  b.remove();
});

// Preklop pogleda je skupen vsem stranem in zivi v common.js.
initMode();

fetch("/api/alerts")
  .then(jsonOk)
  .then((data) => {
    // Najprej dela in nadomestni prevozi -- ta dvoje potnika res zadeva.
    const rank = { "dela na progi": 0, "nadomestni prevoz": 1, "združene garniture": 2, "obvestilo": 3 };
    // Veljavno pred napovedanim: potnika najprej zadeva to, kar velja danes.
    // Med veljavnimi isto po besedilu zapore (`kdajRang`): 5. 10. 2026 sta
    // bili od 8 veljavnih del na progi le 2 danes, „Laze – Ljubljana Zalog“
    // (30. 9. in 11. 10.) pa je bila po številu vlakov druga kartica.
    all = data.sort((a, b) => (a.napovedana ? 1 : 0) - (b.napovedana ? 1 : 0) ||
                              (a.napovedana ? 0 : kdajRang(a) - kdajRang(b)) ||
                              rank[kindOf(a)] - rank[kindOf(b)] ||
                              (b.trains || []).length - (a.trains || []).length);
    render();
  })
  .catch(() => {
    listEl.innerHTML = '<div class="empty-state">Obvestil ni bilo mogoče naložiti.</div>';
  });
