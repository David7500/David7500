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

// Vrsta je tonski žeton v barvi, ki jo ta stvar nosi povsod: dela rumeno kot
// ovire, nadomestni prevoz vijolično kot njegova oznaka v iskalniku.
const KIND_CLASS = {
  "dela na progi": "je-dela",
  "nadomestni prevoz": "je-nadomestni",
  "združene garniture": "je-zdruzene",
  "obvestilo": "je-obvestilo",
};

// „23. 10. – 24. 10.“; leto le, kadar katera meja ni letos (prenova postaj
// do 2027) -- potem na obeh, sicer bi „1. 1. – 31. 12. 2027“ bral kot eno leto.
function periodLabel(a) {
  if (!a.start_ts && !a.end_ts) return "";
  const leto = new Date().getFullYear();
  const zLetom = [a.start_ts, a.end_ts].some((ts) => ts && new Date(ts * 1000).getFullYear() !== leto);
  const f = (ts) => new Date(ts * 1000).toLocaleDateString("sl-SI", { timeZone: "Europe/Ljubljana",
    day: "numeric", month: "numeric", year: zLetom ? "numeric" : undefined });
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
    return k.danes.map((p) => `<p class="ovira-kdaj is-${p.stanje}">${odsek(p.odsek)}${
      escapeHtml(kdajZapore(p))}</p>`).join("");
  }
  const n = k.naslednjic;
  return `<p class="ovira-kdaj is-ne">${n ? odsek(n.odsek) : ""}${escapeHtml(
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

// Opis prenove postaj Brezovica in Preserje ima 900 znakov; kartica pokaže
// štiri vrstice, ostalo en dotik stran.
const DOLG_OPIS = 320;

function itemHtml(a) {
  const kind = kindOf(a);
  const trains = a.trains || [];
  // Vec kot dvanajst stevilk je stena, ki je nihce ne bere; ostale so en dotik
  // stran. Prej so bile v naprednem pogledu -- da vidis, ali obvestilo zadene
  // tvoj vlak, si moral preklopiti nacin strani (5. 10. 2026).
  const head = trains.slice(0, 12);
  const rest = trains.slice(12);
  const pill = (t) => `<a class="ovira-vlak" href="/app/train/${encodeURIComponent(t)}">${escapeHtml(t)}</a>`;
  const opis = (a.description || "").replace(REP, "");
  const dolg = opis.length > DOLG_OPIS;
  return `
    <article class="ovira">
      <div class="ovira-glava">
        <span class="ovira-vrsta ${KIND_CLASS[kind]}">${escapeHtml(kind)}</span>
        ${a.napovedana ? '<span class="ovira-vrsta je-napovedano">napovedano</span>' : ""}
        <span class="sp"></span>
        <span class="ovira-obdobje">${escapeHtml(periodLabel(a))}</span>
      </div>
      <h3 class="ovira-naslov">${escapeHtml(alertTitle(a.header))}</h3>
      ${kdajHtml(a.kdaj)}
      ${opis ? `<p class="ovira-opis${dolg ? " je-dolg" : ""}">${escapeHtml(opis)}</p>
        ${dolg ? '<button type="button" class="ovira-vec">Preberi vse</button>' : ""}` : ""}
      ${trains.length ? `
        <div class="ovira-vlaki">
          <span class="ovira-vlaki-n">${trains.length} ${sklon(trains.length, "vlak")}</span>
          ${head.map(pill).join("")}
          ${rest.length ? `<span class="ovira-ostali" hidden>${rest.map(pill).join("")}</span>
                           <button type="button" class="ovira-se">+${rest.length} še</button>` : ""}
        </div>` : ""}
      ${nogaHtml(a)}
    </article>`;
}

// Kaj je obvestilo in od kod. Preklopa preprosto/napredno ni več (David,
// 23. 10. 2026); interni ključ obvestila potnika ne zanima, opravičilo na
// koncu vsakega opisa tudi ne (`REP`). „neznano“ je prazno polje.
function nogaHtml(a) {
  const deli = [a.effect_label, a.cause_label].filter((x) => x && x !== "neznano").map(escapeHtml);
  if (a.url) deli.push(`<a href="${escapeHtml(a.url)}" target="_blank" rel="noopener">obvestilo SŽ</a>`);
  return deli.length ? `<div class="ovira-noga">${deli.join(" · ")}</div>` : "";
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
  const se = e.target.closest(".ovira-se");
  if (se) {
    se.previousElementSibling.hidden = false;
    se.remove();
    return;
  }
  const vec = e.target.closest(".ovira-vec");
  if (vec) {
    vec.previousElementSibling.classList.remove("je-dolg");
    vec.remove();
  }
});

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
