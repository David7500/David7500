"use strict";

// Domaca stran (Material 3 Expressive, osnutek G). Zivih stevilk o omrezju tu ni ("danes obicajno
// +2 min", stevec vozil, od 1. 10. 2026 tudi stevila ovir ne) -- vsak dan skoraj
// iste in ne spremenijo nicesar, kar bo clovek na tej strani storil.

// ---------- budilke ----------
//
// **Budilka je prva kartica, ne povezava pod "Še".** Prijavljeno 14. 9. 2026:
// "budilke morajo biti takoj dostopne, ne da isces, kje so". V aplikaciji jih
// beremo iz telefona (`Kajros.seznam()`); uro zvonjenja in odhod izracuna
// Kotlin, ne stran -- dvojnik pravila v JavaScriptu bi se razsel s tistim, kar
// budilka res naredi.
//
// **Kartica je samo, kadar je budilka** (osnutek 1, 1. 10. 2026). Prej je bila
// vedno, tudi prazna ("Ni nastavljenih budilk"), in z dnevi v krogih ter se
// tremi budilkami najvecji element strani -- prijavljeno kot "preveč
// overwhelming". Kdor ima budilke, a so vse ugasnjene, dobi kartico s
// seznamom, sicer jih s prve strani ne bi mogel vec prizgati. Kadar kartice
// ni, je budilka oblika ob zemljevidu (`#bud-oblika`): v brskalniku vabilo na
// aplikacijo, v aplikaciji brez budilk vhod v seznam.

const URA = new Intl.DateTimeFormat("sl-SI",
  { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Ljubljana" });
const DAN = new Intl.DateTimeFormat("sl-SI",
  { weekday: "short", day: "numeric", month: "numeric", timeZone: "Europe/Ljubljana" });

function datumLj(ms) {
  return new Date(ms).toLocaleDateString("sv-SE", { timeZone: "Europe/Ljubljana" });
}

/** "danes", "jutri" ali "pet. 18. 9." -- ura brez dneva je pri budilki dvoumna. */
function dan(ms) {
  const d = datumLj(ms);
  if (d === todayIso()) return "danes";
  if (d === datumLj(Date.now() + 86400000)) return "jutri";
  return DAN.format(new Date(ms));
}

function cez(ms) {
  const min = Math.round((ms - Date.now()) / 60000);
  if (min < 1) return "zdaj";
  if (min < 60) return `čez ${min} min`;
  const h = Math.floor(min / 60);
  return h < 24 ? `čez ${h} h ${min % 60} min` : `čez ${Math.round(h / 24)} d`;
}

function beriBudilke() {
  try {
    const a = JSON.parse(MOST.seznam() || "[]");
    return Array.isArray(a) ? a : [];
  } catch (e) {
    return [];
  }
}

// Aplikacija 1.0 ne poslje `odhod_ms` in `vir`; takrat velja vozni red.
const odhodOf = (b) => b.odhod_ms || b.voznoredni_ms;
// Po zvonjenju je vprasanje odhod, ne zvonjenje (isto pravilo kot widget).
const kljucOf = (b) => (b.odzvonjeno ? odhodOf(b) : b.zvoni_ob_ms);

function zamudaHtml(b) {
  if (b.vir === "ni_podatka") return " · o zamudi še ni podatka";
  if (b.vir !== "zamuda") return b.vir ? " · zamuda še ni preverjena" : "";
  const s = Math.round((odhodOf(b) - b.voznoredni_ms) / 1000);
  // Po zaokrozeni minuti, ne po sekundah (oznake.md): 45 s je "+1", ne "tocno".
  if (delayMin(s) === 0) return " · vozi točno";
  return ` <b class="bud-zam" style="color:${delayColor(s)}">${escapeHtml(delayText(s))}</b>`;
}

function stikaloHtml(b) {
  return `<button type="button" class="stikalo" role="switch" data-id="${escapeHtml(b.id)}"
    aria-checked="${!b.ugasnjena}" aria-label="${b.ugasnjena ? "vklopi" : "ugasni"} budilko"></button>`;
}

function kajHtml(b) {
  const kraj = b.smer ? `${b.postaja} → ${b.smer}` : b.postaja;
  return escapeHtml(b.train_no ? `${b.train_no} · ${kraj}` : kraj);
}

function izrisiBudilke() {
  if (!MOST) return;
  const el = document.getElementById("budilke");
  const zdaj = Date.now();
  const vse = beriBudilke();
  el.hidden = !vse.length;
  document.getElementById("bud-oblika").hidden = !!vse.length;
  if (!vse.length) return;
  const zive = vse.filter((b) => Math.max(b.voznoredni_ms, odhodOf(b)) > zdaj - 60000);
  const prva = zive.filter((b) => !b.ugasnjena).sort((a, b) => kljucOf(a) - kljucOf(b))[0];
  const gumbVse = `<button type="button" class="bud-vse" data-vse="1">Vse budilke${
    vse.length > 1 ? ` (${vse.length})` : ""}</button>`;

  if (!prva) {
    el.innerHTML = `<div class="bud-opis" data-vse="1"><span class="bud-nad">Budilke</span>
      <span class="bud-kaj">Vse budilke so ugasnjene</span></div>${gumbVse}`;
    return;
  }

  const velika = prva.odzvonjeno ? odhodOf(prva) : prva.zvoni_ob_ms;
  const kdaj = prva.odzvonjeno ? "Zazvonila · odhod" : `Budilka · ${dan(velika)}`;
  const pod = prva.odzvonjeno
    ? `odhod po voznem redu ${URA.format(prva.voznoredni_ms)}${zamudaHtml(prva)}`
    : `odhod ${URA.format(odhodOf(prva))}${zamudaHtml(prva)}`;

  // Vožnja pod uro čez vso širino: ob uri in stikalu je ostalo 170 pik in
  // "LPV 2010 · Kranj → Ljubljana" se je lomil v tri vrstice.
  el.innerHTML = `
    <div class="bud-vrsta" data-vse="1">
      <span class="bud-ura">${URA.format(velika)}</span>
      <span class="bud-nad">${kdaj}<br>${cez(velika)}</span>
      ${stikaloHtml(prva)}
    </div>
    <div class="bud-opis" data-vse="1">
      <span class="bud-kaj">${kajHtml(prva)}</span>
      <span class="bud-nad">${pod}</span>
    </div>
    ${gumbVse}`;
}

document.querySelector(".domov").addEventListener("click", (ev) => {
  if (!MOST || !ev.target.closest("#budilke")) return;
  const s = ev.target.closest(".stikalo");
  if (s) {
    ev.stopPropagation();
    const vklop = s.getAttribute("aria-checked") !== "true";
    if (MOST.preklopi(s.dataset.id, vklop)) izrisiBudilke();
    return;
  }
  if (ev.target.closest("[data-vse]")) MOST.odpriBudilke();
});

// V aplikaciji oblika ne vabi na prenos, ampak odpre seznam budilk.
if (MOST) {
  const obl = document.getElementById("bud-oblika");
  obl.querySelector(".d-obl-ime").textContent = "Budilke";
  obl.querySelector(".d-obl-pod").textContent = "ni nastavljenih";
  obl.addEventListener("click", (ev) => {
    ev.preventDefault();
    MOST.odpriBudilke();
  });
}

// Budilke se spreminjajo tudi drugje (nativni seznam, zvonjenje), odstevanje
// pa tece samo. Zato ob vrnitvi na stran in vsake pol minute.
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) izrisiBudilke();
});
setInterval(() => { if (!document.hidden) izrisiBudilke(); }, 30000);

// ---------- moje poti ----------
//
// Shranjene poti iz iskalnika (`kajros:fav`) z naslednjima odhodoma in zamudo
// (osnutek A, 1. 10. 2026). Prej so bile znacke z imeni, ki so samo odprle
// iskalnik -- domaca stran ni odgovorila na nic. To ni ziva stevilka o omrezju
// (te so odsle 12. 9.), ampak o tvoji poti. Iskalnik jih hrani po omrezju,
// domaca stran je edino mesto pred izbiro omrezja, zato bere vse.
// **Samo shranjeno, nic samodejnega**: nedavna iskanja so stran spremenila v
// seznam vsega, kar si kdaj pogledal.
//
// Ena zahteva na pot, brez prestopov: `/api/connections` je na arwenu
// izmerjeno 40-90 ms in okrog 20 kB.

const NAJVEC_POTI = 6;
const ODHODOV = 2;
// "brez podatka" samo za odhode v naslednjih 30 minutah -- dlje naprej
// podatka se ne more biti in beseda je sum (isto kot `pot.BREZ_PODATKA_PRED_S`).
const BREZ_PODATKA_PRED_MS = 30 * 60000;
const OSVEZI_POTI_MS = 60000;
const SMER_KLJUC = "kajros:smer";

function beri(kljuc) {
  try {
    const all = JSON.parse(localStorage.getItem(kljuc) || "[]");
    return Array.isArray(all) ? all.filter((x) => x && x.net) : [];
  } catch (err) {
    return [];
  }
}

/** Stran ceste, ki si jo potnik na tabli izbral (iskalnik, `kajros:smer`). */
function smerTable(postaja) {
  try {
    return (JSON.parse(localStorage.getItem(SMER_KLJUC) || "{}") || {})[postaja] || null;
  } catch (e) {
    return null;
  }
}

function znackaHref(f) {
  const pot = f.net === "avtobus" ? "/app/bus" : "/app/train";
  const q = new URLSearchParams();
  if (f.kind === "board") {
    q.set("station", f.station);
    if (f.dir) q.set("kind", f.dir);
  } else {
    q.set("from", f.from || "");
    q.set("to", f.to || "");
  }
  return `${pot}?${q}`;
}

function znackaOpis(f) {
  return f.kind === "board"
    ? `${f.station}${f.dir === "prihodi" ? " · prihodi" : ""}`
    : `${f.from} → ${f.to}`;
}

function kljucPoti(f) {
  return `${f.net}|${f.kind === "board"
    ? `b:${f.station}:${f.dir || "odhodi"}` : `a:${f.from}:${f.to}`}`;
}

const ZVEZDICA = `<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
  <path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z"/></svg>`;
const PUSICA = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
  stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>`;

function mojePoti() {
  const videne = new Set();
  const poti = [];
  for (const f of beri("kajros:fav")) {
    const k = kljucPoti(f);
    if (videne.has(k) || (f.kind === "board" ? !f.station : !(f.from && f.to))) continue;
    videne.add(k);
    poti.push(f);
    if (poti.length >= NAJVEC_POTI) break;
  }
  return poti;
}

/** Odhodi poti v enotni obliki, ne glede na to, ali je zveza A-B ali tabla.
 *  Brez `datum` velja danes. */
async function odhodiPoti(f, datum) {
  const network = f.net === "avtobus" ? "avtobus" : "zeleznica";
  if (f.kind === "board") {
    const q = new URLSearchParams({ station: f.station, kind: f.dir || "odhodi", network });
    if (datum) q.set("date", datum);
    const smer = smerTable(f.station);
    if (smer) q.set("smer", smer);
    const d = await fetch(`/api/departures?${q}`).then(jsonOk);
    return (d.board || []).map((r) => ({
      ura: r.sched, pricakovano: r.expected, zamuda: r.zamuda, nepotrjen_do: r.nepotrjen_do,
      kam: lepoIme(r.towards), nadomestni: isBus(r.mode) && r.network === "zeleznica",
    }));
  }
  const q = new URLSearchParams({ from: f.from, to: f.to, network, with_transfers: "false" });
  if (datum) q.set("date", datum);
  const d = await fetch(`/api/connections?${q}`).then(jsonOk);
  return (d.connections || []).map((c) => ({
    ura: c.sched_dep, pricakovano: c.expected_dep, zamuda: c.zamuda, nepotrjen_do: c.nepotrjen_do,
    kam: null, nadomestni: isBus(c.mode) && c.network === "zeleznica",
  }));
}

// Mimo je sele, ko je minil PRICAKOVANI odhod; nepotrjen odhod (vlak, o
// katerem feed molci) ostane do `nepotrjen_do`, isto kot v iskalniku.
function naslednjiOdhodi(odhodi, zdaj) {
  return odhodi.filter((o) => new Date(o.pricakovano || o.ura).getTime() >= zdaj
    || (o.nepotrjen_do && zdaj <= new Date(o.nepotrjen_do).getTime())).slice(0, ODHODOV);
}

function zamudaPoti(o, zdaj) {
  if (o.zamuda) {
    const besedilo = delayMin(o.zamuda) === 0 ? "točno" : delayText(o.zamuda);
    return `<span class="d-pot-zam" style="color:${delayColor(o.zamuda)}">${escapeHtml(besedilo)}</span>`;
  }
  // Feed za nadomestni prevoz ne poroca nikoli; "brez podatka" bi obljubljal
  // stevilko, ki ne pride.
  if (o.nadomestni) return '<span class="d-pot-zam d-pot-brez">po voznem redu</span>';
  if (new Date(o.ura).getTime() - zdaj <= BREZ_PODATKA_PRED_MS) {
    return '<span class="d-pot-zam d-pot-brez">brez podatka</span>';
  }
  return "";
}

function odhodiHtml(odhodi, zdaj, jutri) {
  return (jutri ? '<span class="d-pot-cez">jutri</span>' : "") + odhodi.map((o, i) => {
    const pricakovano = new Date(o.pricakovano || o.ura).getTime();
    const kdaj = i || jutri ? "" : pricakovano < zdaj ? "potrditve odhoda ni" : cez(pricakovano);
    return `<span class="d-pot-o"><span class="d-pot-ura">${hhmm(o.ura)}</span>${
      zamudaPoti(o, zdaj)}${o.kam && !i ? `<span class="d-pot-kam">→ ${escapeHtml(o.kam)}</span>` : ""}${
      kdaj ? `<span class="d-pot-cez">${kdaj}</span>` : ""}</span>`;
  }).join("");
}

function izrisiPoti() {
  const poti = mojePoti();
  document.getElementById("moje-prazno").hidden = poti.length > 0;
  const el = document.getElementById("moje-poti");
  el.innerHTML = poti.map((f, i) => `
    <a class="d-pot d-pot-${f.net === "avtobus" ? "bus" : "vlak"}" href="${escapeHtml(znackaHref(f))}">
      <span class="d-pot-glava">${ZVEZDICA}<span class="d-pot-ime">${escapeHtml(znackaOpis(f))}</span>${PUSICA}</span>
      <span class="d-pot-odh" id="pot-odh-${i}"></span>
    </a>`).join("");
  osveziOdhode(poti);
  return poti;
}

let mojeZadnje = [];
function osveziOdhode(poti) {
  mojeZadnje = poti;
  poti.forEach(async (f, i) => {
    let html;
    try {
      const zdaj = Date.now();
      const danes = naslednjiOdhodi(await odhodiPoti(f), zdaj);
      if (danes.length) {
        html = odhodiHtml(danes, zdaj, false);
      } else {
        // Danes ne pelje nic vec: prva jutrisnja, kot `danes_ni` pri poti.
        // Ob 23:20 je bila sicer prazna vsaka kartica, prav ko clovek
        // zvecer gleda, kdaj gre zjutraj.
        const jutri = (await odhodiPoti(f, datumLj(zdaj + 86400000))).slice(0, ODHODOV);
        html = jutri.length ? odhodiHtml(jutri, zdaj, true)
          : '<span class="d-pot-nic">danes in jutri ne pelje nič</span>';
      }
    } catch (err) {
      html = '<span class="d-pot-nic">odhodov ni bilo mogoče naložiti</span>';
    }
    const el = document.getElementById(`pot-odh-${i}`);
    if (el && mojeZadnje === poti) el.innerHTML = html;
  });
}

document.addEventListener("visibilitychange", () => {
  if (!document.hidden && mojeZadnje.length) osveziOdhode(mojeZadnje);
});
setInterval(() => {
  if (!document.hidden && mojeZadnje.length) osveziOdhode(mojeZadnje);
}, OSVEZI_POTI_MS);

// ---------- zemljevid vnaprej ----------
//
// Zemljevid je najtezja stran (MapLibre 1,1 MB, stisnjeno okrog 300 kB). V
// aplikaciji ga domaca stran potegne v predpomnilnik, ko nima drugega dela,
// da se ob odprtju ne caka na knjiznico (zelja 26. 9. 2026: "fetchal bi ze,
// ko odpres aplikacijo"). V brskalniku ne: tam bi prenos placal vsak
// obiskovalec domace strani, tudi kdor zemljevida ne odpre.
function zemljevidVnaprej() {
  for (const href of (document.querySelector(".domov").dataset.vnaprej || "").split(" ")) {
    if (!href) continue;
    const l = document.createElement("link");
    l.rel = "prefetch";
    l.href = href;
    document.head.appendChild(l);
  }
}

function kasneje() {
  if ("requestIdleCallback" in window) requestIdleCallback(zemljevidVnaprej, { timeout: 4000 });
  else setTimeout(zemljevidVnaprej, 2000);
}

izrisiBudilke();
izrisiPoti();
if (MOST) {
  if (document.readyState === "complete") kasneje();
  else addEventListener("load", kasneje, { once: true });
}
