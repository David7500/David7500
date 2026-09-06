"use strict";

// Svoje okno enega vlaka: ta voznja + zgodovina te poti.
// Barve zamud so projektna ORDINALNA lestvica (en odtenek, monotona svetlost) --
// uporabljena samo tam, kjer odtenek pomeni velikost zamude. Kjer meritve ni,
// nastopi rezervirana barva, ki je lestvica ne uporablja.

const TRAIN_NO = document.body.dataset.trainNo;
const ENC = encodeURIComponent(TRAIN_NO);
// Datum iz naslova: povezava z iskalnika kaze na konkreten prometni dan.
// Brez njega bi klik na vcerajsnjo vozjno odprl danasnjo.
const URL_PARAMS = new URLSearchParams(location.search);
const URL_DATE = URL_PARAMS.get("date") || null;
// Id voznje: stevilka linije pri avtobusih ni enolicna.
const URL_TRIP = URL_PARAMS.get("trip") || null;
// Postaja, s katere je potnik prisel (odhodna tabla, iskalnik zvez). Okno jo
// izpostavi -- brez tega mora clovek svojo vrstico iskati med tridesetimi
// postanki, in to na telefonu.
const URL_STATION = URL_PARAMS.get("postaja") || null;
const DATE_Q = (() => {
  const p = new URLSearchParams();
  if (URL_DATE) p.set("date", URL_DATE);
  if (URL_TRIP) p.set("trip", URL_TRIP);
  return p.toString() ? `?${p}` : "";
})();

const RUN_POLL_MS = 30000;
const HIST_POLL_MS = 600000;

// Rezervirano za "to ni meritev". Preverjeno z validatorjem palete proti vsem
// stiriv barvam lestvice zamud: najslabsi par ΔE 16,4 (deutan) -- lahko locljivo.
const ESTIMATE_COLOR = "#a8d8ff";

const INK_LINE = "#4a515c";
const INK_GRID = "#23272f";
const INK_AXIS = "#79828f";
const PAST_COLOR = "#79828f";
const SURFACE = "#14161a";

const tooltipEl = document.getElementById("tooltip");

function showTip(html, ev) {
  tooltipEl.innerHTML = html;
  tooltipEl.hidden = false;
  const pad = 12;
  const r = tooltipEl.getBoundingClientRect();
  let x = ev.clientX + pad;
  let y = ev.clientY + pad;
  if (x + r.width > window.innerWidth - 8) x = ev.clientX - r.width - pad;
  if (y + r.height > window.innerHeight - 8) y = ev.clientY - r.height - pad;
  tooltipEl.style.left = `${x}px`;
  tooltipEl.style.top = `${y}px`;
}

function hideTip() {
  tooltipEl.hidden = true;
}

// Korak osi naj bo cela minuta iz znanega nabora -- sicer os pokaze 0, 4, 8, 11, 15.
const NICE_MIN = [1, 2, 5, 10, 15, 20, 30, 60, 120];

function niceTicks(maxSeconds, wanted) {
  const maxMin = Math.max(1, maxSeconds / 60);
  const step = NICE_MIN.find((m) => maxMin / m <= (wanted || 5)) || NICE_MIN[NICE_MIN.length - 1];
  const top = Math.ceil(maxMin / step) * step;
  const out = [];
  for (let m = 0; m <= top; m += step) out.push(m * 60);
  return { top: top * 60, values: out };
}

function svgEl(name, attrs, text) {
  const el = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const [k, v] of Object.entries(attrs || {})) el.setAttribute(k, v);
  if (text != null) el.textContent = text;
  return el;
}

// Graf se prerise ob spremembi sirine -- pisava tako ostane v pravi velikosti,
// namesto da bi jo viewBox skaliral.
const redrawers = new Map();

function mountChart(el, draw) {
  const render = () => {
    // clientWidth steje tudi padding kartice -- brez odstevanja je SVG vsakic
    // za 24 px sirsi od prostora in spodaj zraste vodoravni drsnik.
    const cs = getComputedStyle(el);
    const w = Math.floor(el.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight));
    if (w <= 0) return;
    el.replaceChildren(draw(w));
  };
  redrawers.set(el, render);
  render();
}

let resizeTimer = null;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => redrawers.forEach((f) => f()), 120);
});

// Skupno stanje: profil zamude potrebuje tekoco voznjo IN zgodovino, ki se
// nalagata loceno in z razlicnim ritmom.
const state = { run: null, forecast: null, past: null, pastRuns: 0,
                weather: new Map(), report: null,
                mode: "vlak", network: "zeleznica", agency: null,
                current: null, chain: null };
// Katera postaja je pod misko -- deljeno med grafoma, da se oznaka ne izgubi
// ob preklopu pogleda.
let hoverSeq = null;

// ---------- ta voznja ----------

const runHeadEl = document.getElementById("run-head");
const runTimelineEl = document.getElementById("run-timeline");
const headsignEl = document.getElementById("train-headsign");
const feedDotEl = document.getElementById("feed-dot");


// Prikaz mora govoriti o tem, kar je pred potnikom. "Vlak je od takrat verjetno
// že pripeljal" pod mestno linijo 47 ni le netočno -- zveni kot napaka programa.

function vehicleNoun() {
  if (!isBus(state.mode)) return "vlak";
  return state.network === "zeleznica" ? "nadomestni prevoz" : "avtobus";
}

function vehicleWord() {
  if (!isBus(state.mode)) return "ta vlak";
  return state.network === "zeleznica" ? "ta prevoz" : "ta avtobus";
}

// Kratko in samo tisto, kar spremeni potnikovo ravnanje. Ostalo je bilo
// razlaga o virih podatkov na mestu, kjer clovek gleda svojo voznjo.
function caveatText() {
  if (!isBus(state.mode)) {
    return "Zamuda je izmerjena v prometnem mestu, ne nujno na peronu.";
  }
  if (state.network === "zeleznica") {
    return "Nadomestni prevoz: čakaj na postajališču, ne na peronu.";
  }
  return "Lega je izmerjena z GPS, zamuda ima ločljivost ene minute.";
}

// Nazaj na tisto stran, s katere se pride: iskalnik vlakov ali avtobusov.
function applyNetworkWording() {
  const back = document.querySelector(".back-link");
  if (back && state.network === "avtobus") {
    back.setAttribute("href", "/app/bus");
    const label = back.querySelector("span");
    if (label) label.textContent = "avtobusi";
  }
}

// Koliko casa sme meritev veljati za "trenutno". Cez to je vrednost zgodovina
// in prikaz mora to povedati -- "+20 min" ob polnoci, izmerjeno ob 17h, je laz.
const FRESH_S = 20 * 60;

function ageLabel(iso) {
  const min = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (min < 1) return "pravkar";
  if (min < 60) return `pred ${min} min`;
  const h = Math.floor(min / 60);
  return `pred ${h} h ${String(min % 60).padStart(2, "0")} min`;
}

// Voznja, ki se ni zacela, NI voznja brez podatkov -- to je razlika, ki jo
// potnik bere kot "aplikacija ne dela" proti "avtobus se ni odpeljal".
function notStartedText() {
  const first = state.run && state.run.stops && state.run.stops[0];
  const iso = first && (first.sched_dep || first.sched_arr);
  if (iso && new Date(iso).getTime() > Date.now()) {
    return `${vehicleNoun()} se še ni odpeljal — po voznem redu ob
            <strong>${hhmm(iso)}</strong>`;
  }
  // Za NADOMESTNI prevoz SZ beseda "se" laze: feed zanje ne poroca nikoli.
  // Izmerjeno 4. 9. 2026: 56 nadomestnih voznj v voznem redu, **0 meritev**
  // v petnajstih dneh zajema, medtem ko je pri pravih vlakih pokritost 99,5 %.
  // Potnik, ki caka na stevilko, caka zaman -- in prav to mu je treba povedati.
  if (jeNadomestni()) {
    return `za nadomestni prevoz feed <strong>ne poroča zamud</strong> —
            velja vozni red`;
  }
  return `za ${vehicleWord()} na ta dan še ni nobene meritve`;
}

// Nadomestni prevoz SZ: `mode = bus`, a `network = zeleznica`. Na tej relaciji
// zamenjuje vlak, zato sodi med vlake -- podatkov v realnem casu pa nima.
function jeNadomestni() {
  return isBus(state.mode) && state.network === "zeleznica";
}

function runHeadHtml(cur) {
  const bus = isBus(state.mode);   // glej vehicleNoun() za besedilo
  // Strezniku pustimo odlocitev (minuta, razred, prezgodaj); tu se le risze.
  const z = cur ? stopZamuda(cur) : null;
  const d = cur ? stopDelay(cur) : null;
  const wx = cur ? state.weather.get(cur.stop_seq) : null;
  const color = delayColor(z || d);
  const atIso = cur ? stopActualIso(cur) : null;
  const ageS = atIso ? (Date.now() - new Date(atIso).getTime()) / 1000 : null;
  const stale = ageS != null && ageS > FRESH_S;
  // "-6 min" je uganka, beseda ni -- in prezgoden avtobus je za potnika hujsa
  // novica od zamude: pride ob objavljeni uri in vozila ni vec. Smer nosi
  // NASLOV ("Vozi prezgodaj"), stevilka pa velikost: "Trenutna zamuda" nad
  // "6 min prej" si nasprotuje, "6 min prej" pod njim pa besedo ponovi.
  const early = isEarly(z || d);

  // Prevoznikovo porocilo pozna prometno mesto, ki ga nas vozni red nima --
  // zamuda se meri tudi tam, kjer vlak ne ustavlja.
  const rep = state.report;

  return `
    <div class="detail-now">
      <div class="detail-now-label">${
        stale ? "Zadnja znana zamuda" : early ? "Vozi prezgodaj" : "Trenutna zamuda"}</div>
      <div class="detail-now-value" style="color:${color}">
        <span class="detail-now-n">${early ? Math.abs(delayMin(z || d)) : delayLabel(z || d)}</span>
        <span class="detail-now-unit">min</span>
      </div>
      <div class="detail-now-where">
        ${cur
          ? `izmerjeno na postaji <strong>${escapeHtml(cur.name)}</strong> ob ${hhmm(atIso)}`
          : notStartedText()}
      </div>
      ${atIso ? `<div class="${stale ? "stale-note" : "detail-now-age"}">
        ${stale ? "⚠ " : ""}${escapeHtml(ageLabel(atIso))}${stale
          ? ` — ${vehicleNoun()} je od takrat verjetno že pripeljal`
          : ""}
      </div>` : ""}
      ${rep ? `<div class="detail-report adv-only">
        Prevoznik poroča <strong style="color:${delayColor(rep.delay_min * 60)}">${rep.delay_min > 0 ? "+" : ""}${rep.delay_min} min</strong>
        ob ${escapeHtml(rep.event)}u na postajo <strong>${escapeHtml(rep.station)}</strong>
        ${rep.severe ? '<span class="tag">izjemna zamuda</span>' : ""}
      </div>` : ""}
      ${wx && wx.severity != null ? `
        <div class="detail-weather">
          ${weatherIconHtml(wx, 15)}
          <span>razmere <strong style="color:${severityColor(wx.severity_label)}">${wx.severity}/10</strong> · ${escapeHtml(wx.severity_label)}</span>
        </div>
        <div class="detail-weather-raw">${escapeHtml(weatherSummary(wx))}</div>` : ""}
      <div class="detail-caveat adv-only">
        ${caveatText()}
      </div>
    </div>
  `;
}

// Postanek, ki ga je potnik izbral -- tisti, na katerem stoji. Iscemo po
// imenu, ker isto ime nosi vec `stop_id` (mestno postajalisce ima svojega za
// vsako smer) in ker naslov nosi ime, ne ida.
function yourStop(stops) {
  if (!URL_STATION || !stops) return null;
  const want = fold(URL_STATION);
  return stops.find((s) => fold(s.name) === want) || null;
}

// "Kdaj pride po mene in koliko bo takrat zamujal" -- edino vprasanje, ki ga
// ima potnik na peronu. Zato je to prva stvar v oknu, nad vsem drugim.
function yourStopHtml(stops, forecast, current) {
  const s = yourStop(stops);
  if (!s) return "";
  const passed = current && s.stop_seq <= current.stop_seq;
  const f = (forecast || []).find((x) => x.stop_seq === s.stop_seq);
  const schedIso = s.sched_dep || s.sched_arr;

  let d = null;
  let kdaj = null;
  // Beseda gre NAD stevilko, ne pod cas: "+9 min" brez nje je videti kot
  // meritev, in prav ta postanek je edini, ki ga potnik dejansko prebere.
  let znak = "ocena";
  let odkod = "";
  if (passed) {
    d = stopDelay(s);
    kdaj = stopActualIso(s);
    znak = "izmerjeno";
    odkod = `${vehicleNoun()} je tu že bil`;
  } else if (f) {
    d = f.predicted_delay_s;
    kdaj = schedIso && d != null
      ? new Date(new Date(schedIso).getTime() + d * 1000).toISOString() : schedIso;
    odkod = f.n_samples > 0 ? `mediana ${pluralRuns(f.n_samples)}` : "prenos trenutne zamude";
  } else {
    kdaj = schedIso;
    znak = "vozni red";
    odkod = "ocene še ni";
  }
  const color = delayColor(d);
  const sched = hhmm(schedIso);
  const cas = hhmm(kdaj);

  return `
    <div class="yours">
      <div class="yours-label">Pri tebi — ${escapeHtml(s.name)}</div>
      <div class="yours-line">
        <span class="yours-time" style="color:${color}">${cas}</span>
        ${cas !== sched ? `<span class="yours-sched">${sched}</span>` : ""}
        <span class="yours-delay-box">
          <span class="yours-kind">${escapeHtml(znak)}</span>
          <span class="yours-delay" style="color:${color}">${delayText(d)}</span>
        </span>
      </div>
      <div class="yours-tag">${escapeHtml(odkod)}</div>
      ${budilkaGumbHtml(s)}
    </div>`;
}

// ---------- budilka ----------
//
// Samo v aplikaciji (`MOST`): v brskalniku gumba ni, ker nativnega alarma ni.
// Sedi v bloku "Pri tebi", ker je tam ze vse, kar budilka rabi -- ta voznja,
// ta postanek in njegova voznoredna ura.

const BUD_KLJUC = "kajros:budilka";
const BUD_MINUT = [10, 15, 25, 40];

function budilkeZaPostanek(s) {
  if (!MOST) return [];
  try {
    return JSON.parse(MOST.seznam() || "[]")
      .filter((b) => b.stop_seq === s.stop_seq && b.train_no === TRAIN_NO
                     && !b.odzvonjeno);
  } catch (e) {
    return [];
  }
}

function budilkaGumbHtml(s) {
  if (!MOST) return "";
  const obstoj = budilkeZaPostanek(s)[0];
  const oznaka = obstoj
    ? `budilka ob ${hhmm(new Date(obstoj.zvoni_ob_ms).toISOString())}`
    : "budilka";
  return `<button type="button" class="bud-gumb${obstoj ? " is-on" : ""}"
      data-budilka="${s.stop_seq}">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2" stroke-linecap="round" aria-hidden="true">
        <path d="M12 3a6 6 0 0 0-6 6v4l-1.5 3h15L18 13V9a6 6 0 0 0-6-6zM10 20a2 2 0 0 0 4 0"/>
      </svg>
      <span>${escapeHtml(oznaka)}</span>
    </button>`;
}

// Nastavitve budilke NISO v `#run-head`: tega prikaz vsakih 30 s prerise in
// izbira bi izginila potniku pod prsti. Zato so v svojem sloju.
function odpriBudilko(stopSeq) {
  const s = (state.run && state.run.stops || []).find((x) => x.stop_seq === stopSeq);
  if (!s || !MOST) return;
  const plast = document.getElementById("budilka");
  if (!plast) return;

  let dovoljenja = {};
  try { dovoljenja = JSON.parse(MOST.dovoljenja() || "{}"); } catch (e) { /* prazno */ }
  const manjka = !dovoljenja.obvestila || !dovoljenja.tocni_alarmi;

  const shranjeno = JSON.parse(localStorage.getItem(BUD_KLJUC) || '{"minut":25,"zbudi":true}');
  const obstoj = budilkeZaPostanek(s)[0];
  const minut = obstoj ? obstoj.minut_prej : shranjeno.minut;
  const zbudi = obstoj ? obstoj.zbudi : shranjeno.zbudi;
  const schedIso = s.sched_dep || s.sched_arr;

  plast.innerHTML = `
    <div class="bud-ozadje" data-zapri="1"></div>
    <div class="bud-list" role="dialog" aria-label="Budilka">
      <div class="bud-naslov">Budilka — ${escapeHtml(s.name)}</div>
      <div class="bud-pod">${escapeHtml(TRAIN_NO)} · po voznem redu ob ${hhmm(schedIso)}</div>

      <div class="bud-vrsta">Zvoni koliko prej</div>
      <div class="bud-izbire" data-skupina="minut">
        ${BUD_MINUT.map((m) => `<button type="button" class="bud-izbira${
          m === minut ? " is-on" : ""}" data-minut="${m}">${m} min</button>`).join("")}
      </div>

      <div class="bud-vrsta">Kako</div>
      <div class="bud-izbire" data-skupina="kako">
        <button type="button" class="bud-izbira${zbudi ? "" : " is-on"}" data-zbudi="0">obvesti</button>
        <button type="button" class="bud-izbira${zbudi ? " is-on" : ""}" data-zbudi="1">zbudi me</button>
      </div>

      <div class="bud-opomba">Zvoni ob <strong>voznoredni uri + zamuda − ${minut} min</strong>,
        zamudo pa preverja vse pogosteje, bližje ko je ura. Če povezave ni, zazvoni malo
        prej in to pove.<br>
        Rezerva je v tvojem času: izmerjeno je, da bi bila prikazana zamuda prekratka
        v tretjini primerov pri vlakih in dveh tretjinah pri avtobusih — pet minut več
        to spravi pod dvajsetino.</div>

      ${manjka ? `<button type="button" class="bud-dovoli" data-dovoli="1">
        Android še ne dovoli obvestil ali točnih alarmov — uredi</button>` : ""}

      <div class="bud-dno">
        ${obstoj ? `<button type="button" class="btn-quiet bud-brisi" data-brisi="${obstoj.id}">Odstrani</button>` : ""}
        <button type="button" class="btn-quiet" data-zapri="1">Prekliči</button>
        <button type="button" class="btn" data-shrani="${s.stop_seq}">${obstoj ? "Zamenjaj" : "Nastavi"}</button>
      </div>
    </div>`;
  plast.hidden = false;
  plast.dataset.minut = String(minut);
  plast.dataset.zbudi = zbudi ? "1" : "0";
}

function zapriBudilko() {
  const plast = document.getElementById("budilka");
  if (plast) { plast.hidden = true; plast.innerHTML = ""; }
}

function shraniBudilko(stopSeq) {
  const plast = document.getElementById("budilka");
  const s = (state.run && state.run.stops || []).find((x) => x.stop_seq === stopSeq);
  if (!plast || !s || !MOST) return;
  const minut = Number(plast.dataset.minut || 25);
  const zbudi = plast.dataset.zbudi === "1";
  localStorage.setItem(BUD_KLJUC, JSON.stringify({ minut, zbudi }));

  // Obstojeco budilko za isti postanek zamenjamo, ne podvojimo -- dve zvonjenji
  // za isti vlak sta napaka, ne dvojna varnost.
  budilkeZaPostanek(s).forEach((b) => MOST.odstrani(b.id));

  // Uro pretvori JS, ne Kotlin: brskalnik ta niz ze zna brati, in razclenjevanje
  // datumov v dveh jezikih je nacin, kako se stvari razidejo.
  const schedIso = s.sched_dep || s.sched_arr;
  const id = MOST.nastavi(JSON.stringify({
    train_no: TRAIN_NO,
    trip: (state.run && state.run.trip_id) || null,
    omrezje: state.network,
    postaja: s.name,
    stop_seq: s.stop_seq,
    dan: (state.run && state.run.service_date) || "",
    voznoredni_ms: new Date(schedIso).getTime(),
    minut_prej: minut,
    zbudi: zbudi,
    smer: (state.run && state.run.headsign) || "",
  }));
  zapriBudilko();
  if (id) renderRunHead();
}

document.addEventListener("click", (ev) => {
  const gumb = ev.target.closest("[data-budilka]");
  if (gumb) { odpriBudilko(Number(gumb.dataset.budilka)); return; }
  const plast = document.getElementById("budilka");
  if (!plast || plast.hidden) return;

  const zapri = ev.target.closest("[data-zapri]");
  if (zapri) { zapriBudilko(); return; }
  const izbira = ev.target.closest(".bud-izbira");
  if (izbira) {
    const skupina = izbira.parentElement;
    skupina.querySelectorAll(".bud-izbira").forEach((b) => b.classList.remove("is-on"));
    izbira.classList.add("is-on");
    if (izbira.dataset.minut) plast.dataset.minut = izbira.dataset.minut;
    if (izbira.dataset.zbudi) plast.dataset.zbudi = izbira.dataset.zbudi;
    return;
  }
  const dovoli = ev.target.closest("[data-dovoli]");
  if (dovoli) { MOST.zahtevajDovoljenja(); zapriBudilko(); return; }
  const brisi = ev.target.closest("[data-brisi]");
  if (brisi) { MOST.odstrani(brisi.dataset.brisi); zapriBudilko(); renderRunHead(); return; }
  const shrani = ev.target.closest("[data-shrani]");
  if (shrani) shraniBudilko(Number(shrani.dataset.shrani));
});

// ---------- veriga vozila ----------

// Odgovor na vprasanje, ki ga zamuda ne more dati: KJE JE MOJ AVTOBUS, ki se
// se ni zacel voziti. Takrat zanj ni ne zamude ne lege -- vozilo pa obstaja
// in je na prejsnji voznji, kjer GPS ima. Vlaki tega nimajo: `block_id` je
// samo v avtobusnem delu GTFS.
//
// Zamude prejsnje voznje NE prenasamo naprej. Izmerjeno na 195 parih:
// prenos MAE 4,53 min, "predpostavi tocno" 2,29 min -- torej je prenos slabsi
// od nevednosti, ker vozilo zamudo med voznjama nadoknadi. Zato je spodaj
// dejstvo o vozilu, ne napoved o odhodu.

function chainLink(leg) {
  const p = new URLSearchParams();
  if (state.run && state.run.service_date) p.set("date", state.run.service_date);
  p.set("trip", leg.trip_id);
  const pot = state.network === "avtobus" ? "/app/bus/" : "/app/train/";
  return `${pot}${encodeURIComponent(leg.train_no)}?${p}`;
}

function minLabel(sec) {
  const m = Math.round(sec / 60);
  return m >= 60 ? `${Math.floor(m / 60)} h ${String(m % 60).padStart(2, "0")} min`
                 : `${m} min`;
}

function vehicleChainHtml() {
  const c = state.chain;
  if (!c || (!c.prev && !c.next)) return "";
  const started = state.current != null;
  const prev = c.prev;
  const parts = [];

  // Prejsnjo voznjo kazemo samo, dokler ta se ni zacela -- potem je vozilo tu
  // in "kje je" ni vec vprasanje.
  if (prev && !started) {
    const gps = prev.gps;
    // "pri" sme veljati samo za nekaj sto metrov. Dlje povemo razdaljo, in
    // sicer zracno -- vozilo je lahko onstran reke in cestna pot je daljsa.
    const ime = gps && (gps.at_stop || gps.near_stop);
    const dalec = gps && !gps.at_stop && gps.near_m != null && gps.near_m > 500;
    const kje = !gps ? null
      : !ime ? "lega znana"
      : dalec ? `zdaj ${(gps.near_m / 1000).toFixed(1)} km od
                 <strong>${escapeHtml(ime)}</strong> (zračno)`
              : `zdaj pri postajališču <strong>${escapeHtml(ime)}</strong>`;
    const zam = prev.delay_s != null
      ? `<span style="color:${delayColor(prev.delay_s)}">${delayLabel(prev.delay_s)} min</span>`
        + `<span class="adv-only"> (izmerjeno v ${escapeHtml(prev.delay_stop || "?")})</span>`
      : null;
    parts.push(`
      <div class="chain-line">
        <span class="chain-tag">vozilo</span>
        <span>${kje ? kje + " · " : ""}konča vožnjo
          <a href="${chainLink(prev)}">${escapeHtml(prev.train_no)}</a>
          ${prev.headsign ? escapeHtml(prev.headsign) : ""}${zam ? ", zamuja " + zam : ""}</span>
      </div>
      ${prev.layover_s != null ? `<div class="chain-sub">vmes ${minLabel(prev.layover_s)} postanka —
        zamuda prejšnje vožnje <strong>ni</strong> napoved za tvojo, vozilo jo med
        postankom večinoma nadoknadi</div>` : ""}`);
  }

  const napredne = parts.length === 0;      // ostane samo "nato", ki je adv-only
  if (c.next) {
    parts.push(`
      <div class="chain-line adv-only">
        <span class="chain-tag">nato</span>
        <span>isto vozilo nadaljuje kot
          <a href="${chainLink(c.next)}">${escapeHtml(c.next.train_no)}</a>
          ${c.next.headsign ? escapeHtml(c.next.headsign) : ""}</span>
      </div>`);
  }
  // Okvir mora izginiti skupaj s svojo vsebino. Kadar je edina vrstica
  // `adv-only`, je v preprostem pogledu ostal prazen obrobljen pravokotnik --
  // skatla brez ničesar v njej je videti kot napaka programa.
  if (!parts.length) return "";
  return `<div class="chain${napredne ? " adv-only" : ""}">${parts.join("")}</div>`;
}

async function loadChain() {
  // Prazno pri vlakih in pri dveh tretjinah avtobusnih voznj -- `block_id`
  // ima v GTFS le tretjina. Zato tiho: manjkajoc podatek ni napaka.
  try {
    const r = await fetch(`/api/train/${ENC}/vehicle${DATE_Q}`)
      .then((x) => (x.ok ? x.json() : null));
    state.chain = r && (r.prev || r.next) ? r : null;
  } catch (err) {
    state.chain = null;
  }
}

async function loadReport() {
  // Zadnje porocilo prevoznika o tej voznji: koliko in KJE. Prometno mesto
  // pogosto ni voznoredni postanek, zato ga iz `run` ni mogoce dobiti.
  try {
    const r = await fetch(`/api/train/${ENC}/reports${DATE_Q}`).then((x) => (x.ok ? x.json() : null));
    const list = (r && r.reports) || [];
    state.report = list.length ? list[list.length - 1] : null;
  } catch (err) {
    state.report = null;
  }
}

/** Kdaj ovira sploh velja.
 *
 * `for_train` filtrira samo `end_ts >= zdaj`, ne pa `start_ts <= zdaj` — in
 * to je namerno: nadomestni prevoz, ki se začne v petek, je za potnika, ki
 * gleda četrtkov vlak, uporabna vest. Brez datuma pa je zavajajoča: izmerjeno
 * 4. 9. 2026 je bilo od 48 ovir v tem oknu **32 takih, ki se še niso
 * začele** (začetek 5.–7. 9.). Zato tiste dobijo „velja od D. M.“, da se
 * ločijo od tega, kar velja danes.
 */
function veljavnostHtml(a) {
  if (!a.start_ts) return "";
  if (a.start_ts * 1000 <= Date.now()) return "";
  const d = new Date(a.start_ts * 1000).toLocaleDateString("sl-SI", {
    timeZone: "Europe/Ljubljana", day: "numeric", month: "numeric",
  });
  return `<span class="alert-later">velja od ${escapeHtml(d)}</span> · `;
}

/** Koliko jih velja DANES in koliko šele pozneje.
 *
 * Golo „— 7“ potnik bere kot sedem ovir danes. Izmerjeno 4. 9. 2026 na
 * LPV 2250: sedem obvestil, od tega se jih je pet začelo šele 7.–19. 9.
 * Razčlenitev je v naslovu, ker škatla ni odprta, kadar jih je več kot dve —
 * torej natanko takrat, ko je razlika največja.
 */
function stevecOvir(list) {
  const zdaj = Date.now();
  const pozneje = list.filter((a) => a.start_ts && a.start_ts * 1000 > zdaj).length;
  if (!pozneje) return `— ${list.length}`;
  const danes = list.length - pozneje;
  return danes
    ? `— ${danes} zdaj, ${pozneje} pozneje`
    : `— ${pozneje}, vse šele pozneje`;
}

async function loadAlerts() {
  // Edini vir odgovora, ZAKAJ vlak zamuja. Vse drugo v bazi pove le koliko.
  const box = document.getElementById("train-alerts");
  try {
    const list = await fetch(`/api/train/${ENC}/alerts`).then((r) => (r.ok ? r.json() : []));
    if (!list.length) { box.innerHTML = ""; return; }
    box.innerHTML = `<details class="alert-box"${list.length <= 2 ? " open" : ""}>
      <summary class="alert-head">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M12 9v5M12 17.5v.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"></path>
        </svg>
        Obvestila o ovirah na tej poti
        <span class="alert-count">${stevecOvir(list)}</span>
      </summary>
      <div class="alert-list">${list.map((a) => `
        <div class="alert-item">
          <strong>${escapeHtml(alertTitle(a.header))}</strong>
          <div class="alert-meta">${veljavnostHtml(a)}${escapeHtml(a.effect_label || "")}${a.cause_label ? ` · ${escapeHtml(a.cause_label)}` : ""}
          ${a.url ? ` · <a href="${escapeHtml(a.url)}" target="_blank" rel="noopener">obvestilo SŽ</a>` : ""}</div>
          <div class="alert-body adv-only">${escapeHtml((a.description || "").slice(0, 400))}</div>
        </div>`).join("")}</div>
    </details>`;
  } catch (err) {
    box.innerHTML = "";
  }
}

async function loadRun() {
  try {
    await Promise.all([loadReport(), loadChain()]);
    const { run, forecast, current } = await fetchRunAndForecast(TRAIN_NO, URL_DATE, URL_TRIP);
    // Nadomestni prevoz mora biti viden v naslovu, ne sele v vrstici postaj:
    // kdor pride sem s povezave, mora takoj vedeti, da caka avtobus.
    state.mode = run.mode;
    state.network = run.network || "zeleznica";
    setVehicleNoun(vehicleNoun());     // besedo o postanku pise common.js
    state.agency = run.agency || null;
    if (isBus(run.mode)) {
      document.getElementById("train-mode").innerHTML = lineBadgeHtml(run);
    }
    applyNetworkWording();
    state.run = run;
    state.forecast = forecast;
    state.current = current;
    renderRunHead();
    renderTimeline();
    renderProfile();
    loadPosition();     // ziv zemljevid; pri vlaku tiho odpade, ker lege ni
  } catch (err) {
    console.error("vožnje ni bilo mogoče naložiti", err);
    runHeadEl.innerHTML = "";
    runTimelineEl.innerHTML =
      '<div class="empty-state">za to vožnjo na ta dan ni podatkov</div>';
    refreshFeedDot();   // zahteva ni uspela -- naj pika pove, kaj ve
  }
}

// Glava okna: postanek potnika, trenutna zamuda in veriga vozila. Svoja
// funkcija, ker jo prerisujeta dva vira (vozjna in vreme) in mora biti obakrat
// enaka -- dva neodvisna izrisa sta se ze razsla.
function renderRunHead() {
  const run = state.run;
  if (!run) return;
  // Dokler voznja ni zacela, je "kje je vozilo" edini pravi odgovor in gre
  // nad prazen okvir trenutne zamude; potem je vozilo tu in gre pod.
  const veriga = vehicleChainHtml();
  const cur = state.current;
  runHeadEl.innerHTML = yourStopHtml(run.stops, state.forecast, cur)
    + (cur ? runHeadHtml(cur) + veriga : veriga + runHeadHtml(cur));
}

// Casovnica se med pogledoma razlikuje, zato je svoja funkcija: preklop je
// mora prerisati, ne le odkriti skritih elementov.
function renderTimeline() {
  const run = state.run;
  if (!run) return;
  const yours = yourStop(run.stops);
  runTimelineEl.innerHTML =
    runTimelineHtml(run.stops, state.forecast, state.weather, {
      run,
      aheadOnly: !document.body.classList.contains("is-advanced"),
      highlight: yours ? yours.stop_seq : null,
    }) +
    vozovnicaHtml(run) +
    // Vira sta navedena tu in ne v opombi nad casovnico: navedba je pogoj
    // rabe (IJPP CC BY-SA 4.0, Open-Meteo CC BY 4.0), ne razlaga za potnika.
    `<div class="detail-foot">${escapeHtml(run.service_date)} · ${run.stops.length} postaj
      · IJPP prek NAP (CC BY-SA 4.0), obdelava DERP · vreme Open-Meteo (CC BY 4.0)</div>`;
}

// ---------- zgodovina: stevilke ----------

function tileHtml(label, value, sub, color) {
  return `
    <div class="tile">
      <div class="tile-label">${escapeHtml(label)}</div>
      <div class="tile-value"${color ? ` style="color:${color}"` : ""}>${value}</div>
      <div class="tile-sub">${escapeHtml(sub || "")}</div>
    </div>
  `;
}

function renderTiles(h) {
  const n = h.runs_observed || 0;
  const s = h.summary || {};
  if (!n) {
    document.getElementById("hist-tiles").innerHTML =
      '<div class="empty-state">za to pot še ni nobene zajete vožnje</div>';
    return;
  }
  // Pri eni sami voznji mediana ni mediana -- povej, kaj stevilka v resnici je.
  const medLabel = n === 1 ? "Končna zamuda" : "Mediana končne zamude";
  const tiles = [
    tileHtml(medLabel, delayLabel(s.median_final_s), pluralRuns(n), delayColor(s.median_final_s)),
    tileHtml("Najslabša vožnja", delayLabel(s.worst_final_s), "končna zamuda", delayColor(s.worst_final_s)),
    tileHtml("Delež v 5 min", `${Math.round((s.on_time_share || 0) * 100)} %`,
             "končna zamuda do 5 min"),
  ];
  // Prag 5: pod tem p90 ni percentil, ampak druga najvisja vrednost.
  //
  // Pri majhnem vzorcu p90 in "najslabsa" po zaokrozevanju na minute pogosto
  // pokazeta ISTO stevilko -- izmerjeno 4. 9. 2026 na zeleznici: 40 % pri
  // 3-4 voznjah, 23 % pri 5-9, 17 % pri 10-14, 0 % nad 15. To ni napaka, ki
  // bi jo bilo treba skriti: `_pct` interpolira in vrednosti se res zblizata,
  // oznaki pa povesta, kaj je kaj. Cela sekcija je poleg tega `adv-only`.
  if (n >= 5) {
    tiles.splice(2, 0, tileHtml("p90", delayLabel(s.p90_final_s), "9 od 10 voženj do tega",
                                delayColor(s.p90_final_s)));
  }
  document.getElementById("hist-tiles").innerHTML = tiles.join("");
}

// ---------- skupno: tarca za misko cez vso visino ----------

// Pika s polmerom 4,5 px je pretezka tarca -- na 29 postajah je zadetek
// loterija. Vsaka postaja dobi nevidno obmocje cez vso visino grafa.
function addHoverBands(svg, xs, top, height, seqs, onHover) {
  if (xs.length < 2) return;
  const step = (xs[xs.length - 1] - xs[0]) / (xs.length - 1);
  xs.forEach((cx, i) => {
    const band = svgEl("rect", {
      x: cx - step / 2, y: top, width: step, height,
      fill: seqs[i] === hoverSeq ? "rgba(255,255,255,0.035)" : "transparent",
    });
    band.addEventListener("mousemove", (ev) => {
      if (hoverSeq !== seqs[i]) {
        hoverSeq = seqs[i];
        redrawers.forEach((f) => f());
      }
      onHover(i, ev);
    });
    band.addEventListener("mouseleave", () => {
      hideTip();
    });
    svg.appendChild(band);
  });
}

function crosshair(svg, x, top, bottom) {
  svg.appendChild(svgEl("line", {
    x1: x, x2: x, y1: top, y2: bottom,
    stroke: "#3d434f", "stroke-width": 1, "stroke-dasharray": "3 3",
  }));
}

function weatherTipRows(w) {
  if (!w || w.temp_c == null) return "";
  const head = w.severity == null ? "" :
    `<div class="tt-row"><span>razmere</span><b style="color:${severityColor(w.severity_label)}">${w.severity}/10 ${escapeHtml(w.severity_label)}</b></div>`;
  // Indeks brez razclenitve je crna skatla -- iz cesa je sestavljen, mora biti vidno.
  const parts = (w.severity_parts || []).map((x) =>
    `<div class="tt-row is-part"><span>${escapeHtml(x.what)}</span><b>+${x.points}</b></div>`).join("");
  const raw = (w.snowfall_cm || 0) > 0
    ? `<div class="tt-row"><span>sneg</span><b>${num(w.snowfall_cm)} cm</b></div>`
    : `<div class="tt-row"><span>padavine</span><b>${num(w.precip_mm)} mm/h</b></div>`;
  return head + parts + `<div class="tt-split"></div>` + raw +
    `<div class="tt-row"><span>temperatura</span><b>${num(w.temp_c)} °C</b></div>` +
    `<div class="tt-row"><span>sunki vetra</span><b>${num(w.wind_gust_kmh, 0)} km/h</b></div>`;
}

// ---------- graf 1: zamuda po VSEH postajah poti ----------

const KIND = {
  measured: { label: "izmerjeno" },
  estimate: { label: "ocena (prenos zamude)" },
  none: { label: "brez podatka" },
};

// Nakup vozovnice je pri SŽ na `eshop.sz.si`. Relacije v naslov ni mogoce
// podati: obrazec trgovine je POST z internimi ID-ji postaj, GET parametri se
// tiho ignorirajo. Poskusili smo tudi `potniski.sz.si/vozni-redi-results/`,
// ki GET res sprejme -- a gumb tam pelje v trgovino BREZ prenesene relacije,
// tako da bi bil ovinek brez koristi (uporabnikova ugotovitev 3. 9. 2026).
// Zato: povezava na trgovino in poved, da relacijo vpises tam.
//
// Samo za zeleznicno omrezje. Nadomestni prevoz SZ je zraven (mode = bus, a
// network = zeleznica): to je SZ storitev in vozovnica velja. Pri mestnih in
// medkrajevnih avtobusih vsak prevoznik prodaja sam.
function vozovnicaHtml(run) {
  if (!run || run.network !== "zeleznica") return "";
  return ticketLinkHtml();
}

function profilePoints() {
  // Vse postaje poti, ne samo tiste z meritvijo -- graf mora pokazati celo pot.
  const stops = state.run.stops;
  const cur = lastMeasured(state.run);
  const fc = new Map((state.forecast || []).map((f) => [f.stop_seq, f]));
  const past = state.past || new Map();

  return stops.map((s) => {
    const p = {
      seq: s.stop_seq, name: s.name,
      past: past.get(s.stop_seq) || null,
      wx: state.weather.get(s.stop_seq) || null,
    };
    if (cur && s.stop_seq <= cur.stop_seq) {
      if (stopActualIso(s)) {
        p.kind = "measured";
        p.value = stopDelay(s);
        // Kadar vlak ne odide takrat, ko pride (voznoredno krizanje), sta to
        // dve razlicni stevilki. Brez prihodne je padec videti, kot da se je
        // zgodil na odseku -- zgodil pa se je NA postaji.
        const split = dwellSplit(s);
        p.arrival = split ? split.arr : null;
        p.dwell = split;
      } else { p.kind = "none"; p.value = null; }
    } else {
      // Naprej po progi vedno nasa ocena, tudi ce feed ze ima vrednost:
      // izmerjeno je prevoznikova napoved za postanke naprej precej slabsa
      // od prenosa trenutne zamude (backtest.py). Njegovo stevilko obdrzimo
      // v oknu ob dotiku, da ni skrita.
      const f = fc.get(s.stop_seq);
      p.kind = f ? "estimate" : "none";
      p.value = f ? f.predicted_delay_s : null;
      p.samples = f ? f.n_samples : 0;
      p.feedSaid = stopDelay(s);
      // Rezerva, ki jo model porabi prav na tej postaji: ocena za prihod je
      // za toliko visja od ocene za odhod. Brez tega je padec videti, kot da
      // se je zgodil na odseku -- enako kot pri meritvah.
      p.arrival = f && f.slack_here_s ? f.predicted_delay_s + f.slack_here_s : null;
      p.slackHere = f ? f.slack_here_s || 0 : 0;
    }
    return p;
  });
}

function stopTipHtml(p) {
  const rows = [];
  if (p.value != null) {
    rows.push(`<div class="tt-row"><span>${KIND[p.kind].label}</span><b>${delayLabel(p.value)} min</b></div>`);
    if (p.kind === "estimate") {
      rows.push(`<div class="tt-note">${p.samples > 0
        ? `mediana ${escapeHtml(pluralRuns(p.samples))}`
        : "le prenos trenutne zamude, brez zgodovine"}</div>`);
      if (p.feedSaid != null) {
        rows.push(`<div class="tt-row is-part"><span>prevoznik napoveduje</span><b>${delayLabel(p.feedSaid)} min</b></div>`);
      }
    }
  } else {
    rows.push('<div class="tt-row"><span>zamuda</span><b>—</b></div>');
  }
  if (p.past) {
    rows.push(`<div class="tt-row"><span>povprečje preteklih</span><b>${delayLabel(p.past.mean_s)} min</b></div>`);
    rows.push(`<div class="tt-note">${escapeHtml(pluralRuns(p.past.n))}</div>`);
  }
  const wxRows = weatherTipRows(p.wx);
  return `<div class="tt-title">${escapeHtml(p.name)}</div>${rows.join("")}` +
    (wxRows ? `<div class="tt-split"></div>${wxRows}` : "");
}

// Vreme ni svoj pogled: v isti sliki lezi pod zamudo, ker vprasanje ni "kaksno
// je vreme", ampak "je zamuda tam, kjer je bilo vreme hudo".
//
// Lestvici sta dve in namenoma nista pomesani. Validator palete pove, zakaj:
// rumena razmer (#d9b33c) proti svetli oranzni zamud (#f2a87e) je pri deutanu
// ΔE 5,5 -- premalo, ce bi bili v istem registru. Zato zamuda ostane crta s
// pikami zgoraj, razmere pa so stolpci v locenem pasu pod grafom, in vsak
// stolpec od stopnje 4 naprej nosi svojo stevilko: barva sama nikoli ne odloca.
const SEV_STRIP_H = 38;
const SEV_GAP = 18;

// Koliko pik mora biti med prihodom in odhodom, da poleg navpicnice narisemo
// se PRAZEN KROGEC prihoda. Krogec meri v premeru 10 pik, polna pika odhoda 11
// -- pri manjsem razmiku se prekrijeta, navpicnica med njima izgine pod njima
// in videti je kot dva nepovezana krogca. Navpicnica se v takem primeru risze
// vseeno: enominutni padec je resnicen podatek in kot stopnica ob piki je
// viden, kot par krogcev pa ne.
const MIN_SPLIT_PX = 15;

//: Koliko prostora rabi ena postaja, da je krivulja se krivulja in ne crta.
const MIN_STOP_PX = 30;

function drawProfile(w, pts) {
  const hasWx = pts.some((p) => p.wx && p.wx.severity != null);
  // Desni rob mora nositi zadnjo tocko, njeno oznako, njen stolpec razmer in
  // napis nad pasom. Pri 16 px je bilo vse to na robu okvirja in odrezano.
  const M = { t: 26, r: 46, b: 34, l: 46 };
  const ih = 200;
  const stripTop = M.t + ih + SEV_GAP;
  const stripBot = stripTop + SEV_STRIP_H;
  const bottom = hasWx ? stripBot : M.t + ih;
  const H = bottom + M.b;
  const iw = Math.max(40, w - M.l - M.r);
  const svg = svgEl("svg", { width: w, height: H, role: "img" });

  const vals = [];
  for (const p of pts) {
    if (p.value != null) vals.push(p.value);
    if (p.past && p.past.mean_s != null) vals.push(p.past.mean_s);
  }
  const maxV = Math.max(60, ...vals);
  const minV = Math.min(0, ...vals);
  const yTop = Math.ceil(maxV / 60 / 5) * 5 * 60 || 300;
  const yBot = Math.floor(minV / 60 / 5) * 5 * 60;
  const span = yTop - yBot || 300;
  const x = (i) => M.l + (pts.length === 1 ? iw / 2 : (i * iw) / (pts.length - 1));
  const y = (v) => M.t + ih - ((v - yBot) / span) * ih;

  const ticks = 5;
  for (let i = 0; i <= ticks; i += 1) {
    const v = yBot + (span / ticks) * i;
    svg.appendChild(svgEl("line", {
      x1: M.l, x2: M.l + iw, y1: y(v), y2: y(v),
      stroke: Math.abs(v) < 1 ? INK_AXIS : INK_GRID, "stroke-width": 1,
    }));
    svg.appendChild(svgEl("text", {
      x: M.l - 8, y: y(v) + 4, "text-anchor": "end",
      fill: INK_AXIS, "font-size": 10, "font-family": "'IBM Plex Mono', monospace",
    }, `${Math.round(v / 60)}`));
  }
  svg.appendChild(svgEl("text", {
    x: M.l - 8, y: M.t - 11, "text-anchor": "end",
    fill: INK_AXIS, "font-size": 9, "font-family": "'IBM Plex Sans', sans-serif",
  }, "min"));

  const hoverIdx = pts.findIndex((p) => p.seq === hoverSeq);
  if (hoverIdx >= 0) crosshair(svg, x(hoverIdx), M.t, bottom);

  // povprecje preteklih voznj -- referenca v ozadju, brez markerjev
  const pastPts = pts.map((p, i) => (p.past && p.past.mean_s != null ? [i, p.past.mean_s] : null));
  let segment = [];
  for (const item of [...pastPts, null]) {
    if (item) { segment.push(`${x(item[0])},${y(item[1])}`); continue; }
    if (segment.length > 1) {
      svg.appendChild(svgEl("polyline", {
        points: segment.join(" "), fill: "none", stroke: PAST_COLOR, "stroke-width": 1.5,
        "stroke-dasharray": "5 4", "stroke-linejoin": "round",
      }));
    }
    segment = [];
  }

  // tekoca voznja -- polna crta skozi meritve, crtkana skozi ocene
  for (let i = 0; i < pts.length - 1; i += 1) {
    const a = pts[i];
    const b = pts[i + 1];
    if (a.value == null || b.value == null) continue;
    const guessed = a.kind !== "measured" || b.kind !== "measured";
    // Odsek se konca pri PRIHODNI zamudi naslednje postaje, ne pri odhodni:
    // kar se zgodi med postajama, je voznja, kar se zgodi na postaji, je
    // postanek. Padec potem narise navpicnica spodaj, tam, kjer se je res
    // zgodil.
    // Odsek se konca pri PRIHODNI vrednosti -- kar se zgodi med postajama, je
    // voznja. Padec potem nariše navpicnica na postaji, tudi ce je majhen.
    const konec = b.arrival != null ? b.arrival : b.value;
    svg.appendChild(svgEl("line", {
      x1: x(i), y1: y(a.value), x2: x(i + 1), y2: y(konec),
      stroke: guessed ? ESTIMATE_COLOR : INK_LINE, "stroke-width": 2,
      "stroke-dasharray": guessed ? "4 4" : null, "stroke-linecap": "round",
    }));
  }

  // Sprememba zamude NA postaji: navpicnica od prihoda do odhoda in prazen
  // krogec pri prihodu. Redko (3 % postankov), a prav to je vprasanje, ki ga
  // graf sicer pusti odprto -- "kako je zamuda padla za osem minut naenkrat".
  pts.forEach((p, i) => {
    if (p.arrival == null || p.value == null) return;
    const ocena = p.kind === "estimate";
    const barva = ocena ? ESTIMATE_COLOR : delayColor(p.arrival);
    svg.appendChild(svgEl("line", {
      x1: x(i), y1: y(p.arrival), x2: x(i), y2: y(p.value),
      stroke: barva, "stroke-width": 2, "stroke-linecap": "round",
      "stroke-dasharray": ocena ? "4 4" : null,
    }));
    // Krogec prihoda samo, kadar je zanj prostor; sicer je navpicnica stopnica
    // ob piki odhoda in se bere sama.
    if (Math.abs(y(p.arrival) - y(p.value)) >= MIN_SPLIT_PX) {
      svg.appendChild(svgEl("circle", {
        cx: x(i), cy: y(p.arrival), r: 4,
        fill: SURFACE, stroke: barva, "stroke-width": 2,
      }));
    }
  });

  pts.forEach((p, i) => {
    if (p.value == null) return;
    const filled = p.kind !== "estimate";
    const on = p.seq === hoverSeq;
    svg.appendChild(svgEl("circle", {
      cx: x(i), cy: y(p.value), r: on ? 7 : 4.5,
      fill: filled ? (p.kind === "measured" ? delayColor(p.value) : ESTIMATE_COLOR) : SURFACE,
      stroke: on ? "#e7eaf0" : (filled ? SURFACE : ESTIMATE_COLOR), "stroke-width": 2,
    }));
  });

  // neposredne oznake samo tam, kjer nekaj povedo: vrh in cilj
  const withVal = pts.map((p, i) => [p, i]).filter(([p]) => p.value != null);
  if (withVal.length) {
    const maxIdx = withVal.reduce((best, cur) => (cur[0].value > best[0].value ? cur : best))[1];
    const lastIdx = withVal[withVal.length - 1][1];
    new Set([maxIdx, lastIdx]).forEach((i) => {
      svg.appendChild(svgEl("text", {
        x: x(i), y: y(pts[i].value) - 10,
        "text-anchor": i === pts.length - 1 ? "end" : "middle",
        fill: "#e7eaf0", "font-size": 11, "font-weight": 600,
        "font-family": "'IBM Plex Mono', monospace",
      }, delayLabel(pts[i].value)));
    });
  }

  if (hasWx) drawSeverityStrip(svg, pts, x, iw, M.l, stripTop, stripBot);

  drawStopAxis(svg, pts, x, iw, H);

  addHoverBands(svg, pts.map((_, i) => x(i)), M.t - 6, bottom - M.t + 12,
                pts.map((p) => p.seq),
                (i, ev) => showTip(stopTipHtml(pts[i]), ev));
  return svg;
}

// Na osi so doslej stali samo zacetek in konec. Pri 25 postajah to pomeni,
// da bralec vidi skok zamude, ne more pa povedati, KJE se je zgodil -- prav
// to pa je vprasanje. Vmesne oznake postavimo tako gosto, kot dopusca sirina.
const AXIS_LABEL_PX = 74;

function drawStopAxis(svg, pts, x, iw, H) {
  const y = H - 12;
  const put = (i, anchor) => {
    const name = pts[i].name.length > 14 ? `${pts[i].name.slice(0, 13)}…` : pts[i].name;
    svg.appendChild(svgEl("text", {
      x: x(i), y, "text-anchor": anchor,
      fill: pts[i].seq === hoverSeq ? "#e7eaf0" : INK_AXIS,
      "font-size": 10, "font-family": "'IBM Plex Sans', sans-serif",
    }, name));
  };
  put(0, "start");
  if (pts.length > 1) put(pts.length - 1, "end");

  const fits = Math.floor(iw / AXIS_LABEL_PX);
  if (fits < 3 || pts.length < 4) return;
  const step = Math.ceil((pts.length - 1) / fits);
  for (let i = step; i < pts.length - 1; i += step) {
    // Ob krajiscih ne podvajaj -- oznaki bi se prekrivali.
    if (x(i) - x(0) < AXIS_LABEL_PX || x(pts.length - 1) - x(i) < AXIS_LABEL_PX) continue;
    put(i, "middle");
  }
}


function drawSeverityStrip(svg, pts, x, iw, left, top, bot) {
  svg.appendChild(svgEl("line", {
    x1: left, x2: left + iw, y1: bot, y2: bot, stroke: INK_AXIS, "stroke-width": 1,
  }));
  svg.appendChild(svgEl("text", {
    x: left + iw, y: top - 5, "text-anchor": "end", fill: INK_AXIS, "font-size": 9,
    "font-family": "'IBM Plex Sans', sans-serif",
  }, `razmere ob ${vehicleNoun() === "vlak" ? "vlaku" : "vozilu"}, 0–10`));

  const step = pts.length > 1 ? iw / (pts.length - 1) : iw;
  const bw = Math.max(2, Math.min(18, step * 0.62));
  const worst = pts.reduce((a, b) =>
    ((b.wx && b.wx.severity != null && (!a || b.wx.severity > a.wx.severity)) ? b : a), null);

  pts.forEach((p, i) => {
    if (!p.wx || p.wx.severity == null) return;
    const h = Math.max(1.5, (p.wx.severity / 10) * (bot - top));
    const on = p.seq === hoverSeq;
    // Prvi in zadnji stolpec bi pol sirine molela cez os; drzimo ju znotraj.
    const bx = Math.min(Math.max(x(i) - bw / 2, left), left + iw - bw);
    svg.appendChild(svgEl("rect", {
      x: bx, y: bot - h, width: bw, height: h, rx: 2,
      fill: severityColor(p.wx.severity_label),
      stroke: on ? "#e7eaf0" : "none", "stroke-width": on ? 1.5 : 0,
    }));
    // Stevilka na vseh, ki nekaj pomenijo -- ce se ne prilegajo vse, vsaj najhujsa.
    const fits = step >= 17;
    if (p.wx.severity >= 4 && (fits || p === worst)) {
      svg.appendChild(svgEl("text", {
        x: x(i), y: bot - h - 4, "text-anchor": "middle",
        fill: "#9aa3b0", "font-size": 9, "font-family": "'IBM Plex Mono', monospace",
      }, String(p.wx.severity)));
    }
  });
}

function profileLegendHtml(pts) {
  const kinds = new Set(pts.filter((p) => p.value != null).map((p) => p.kind));
  const items = [];
  if (kinds.has("measured")) {
    items.push(`<span class="lg"><span class="lg-ramp"></span>izmerjeno (odtenek = velikost zamude)</span>`);
  }
  if (kinds.has("eta")) {
    items.push(`<span class="lg"><span class="lg-dot" style="background:${ESTIMATE_COLOR}"></span>napoved prevoznika</span>`);
  }
  if (kinds.has("estimate")) {
    items.push(`<span class="lg"><span class="lg-dot is-hollow" style="border-color:${ESTIMATE_COLOR}"></span>ocena (mediana te poti)</span>`);
  }
  if (pts.some((p) => p.arrival != null)) {
    items.push('<span class="lg"><span class="lg-dot is-hollow" style="border-color:#9aa3b0"></span>'
      + 'prihod (kjer se zamuda spremeni na postaji)</span>');
  }
  if (pts.some((p) => p.past)) {
    items.push(`<span class="lg"><span class="lg-dash" style="border-color:${PAST_COLOR}"></span>povprečje preteklih voženj</span>`);
  }
  if (pts.some((p) => p.wx && p.wx.severity != null)) {
    items.push('<span class="lg-break"></span><span class="lg is-cap">stolpci spodaj</span>');
    for (const lab of SEVERITY_ORDER) {
      items.push(`<span class="lg"><span class="lg-swatch" style="background:${SEVERITY_STYLE[lab]}"></span>${lab}</span>`);
    }
  }
  return items.join("");
}

// Ena poved. Kar je bilo tu prej -- iz cesa je stopnja sestavljena, kako
// velika je celica modela -- se vidi ob dotiku stolpca; napisano dvakrat je
// bilo dvakrat prebrano nikoli.
const WEATHER_NOTE =
  "Razmere 0–10 opisujejo vreme, <strong>niso napoved zamude</strong>.";

function renderProfile() {
  const sub = document.getElementById("profile-sub");
  const el = document.getElementById("profile-chart");
  const legend = document.getElementById("profile-legend");
  const note = document.getElementById("weather-note");
  if (!state.run) return;

  const pts = profilePoints();
  // Dovolj je, da ima tocke ena od obeh krivulj: pred odhodom je tekoca prazna,
  // pretekla pa ze pove, kje ta vlak obicajno izgubi cas.
  const nNow = pts.filter((p) => p.value != null).length;
  const nPast = pts.filter((p) => p.past && p.past.mean_s != null).length;
  if (Math.max(nNow, nPast) < 2) {
    sub.textContent = "";
    legend.innerHTML = "";
    note.hidden = true;
    el.innerHTML = '<div class="empty-state">premalo točk za profil</div>';
    return;
  }

  const withWx = pts.filter((p) => p.wx && p.wx.severity != null);
  const worst = withWx.length ? withWx.reduce((a, b) => (b.wx.severity > a.wx.severity ? b : a)) : null;
  sub.textContent = (state.pastRuns
    ? `celotna pot, ${pts.length} postaj · povprečje iz ${pluralRuns(state.pastRuns)} pred današnjo`
    : `celotna pot, ${pts.length} postaj · preteklih voženj za primerjavo še ni`)
    + (worst ? ` · najhujše razmere ${worst.wx.severity}/10 na postaji ${worst.name}` : "")
    + " · miška kjerkoli nad stolpcem postaje";
  legend.innerHTML = profileLegendHtml(pts);
  note.innerHTML = WEATHER_NOTE;
  note.hidden = !withWx.length;
  // Na telefonu je 29 postaj na 390 px deset pik na postajo -- krivulja je
  // stisnjena v crto in na osi sta samo zacetek in konec. Graf zato dobi
  // najmanjso sirino na postajo in se, kadar je ozko, VODORAVNO PREMIKA
  // (`.fig-body` ima `overflow-x: auto`). Bolje je drseti kot ne videti.
  mountChart(el, (w) => drawProfile(Math.max(w, MIN_STOP_PX * pts.length + 92), pts));
  el.classList.toggle("is-wide", el.clientWidth < MIN_STOP_PX * pts.length + 92);
}

// ---------- graf 2: koncna zamuda po dnevih ----------

//: Najozji stolpec, ki je se stolpec in ne crta.
const MIN_BAR_PX = 7;

function drawRuns(w, runs, onSlice) {
  const H = 190;
  const M = { t: 14, r: 12, b: 30, l: 40 };
  const iw = Math.max(40, w - M.l - M.r);
  const ih = H - M.t - M.b;
  const svg = svgEl("svg", { width: w, height: H, role: "img" });

  // Pri pol leta zajema bi bilo 180 stolpcev na 300 px, torej 1,7 px na dan
  // in 180 datumov drug cez drugega. Zato pokazemo zadnjih toliko, kolikor
  // jih gre citljivo noter, in povemo, koliko jih je vseh -- graf, ki se ne
  // da brati, ni graf.
  const zmore = Math.max(6, Math.floor(iw / MIN_BAR_PX));
  const vsi = runs.length;
  runs = runs.slice(-zmore);
  if (onSlice) onSlice(runs.length, vsi);

  const ticks = niceTicks(Math.max(60, ...runs.map((r) => r.final_delay_s)), 5);
  const yMax = ticks.top;
  const y = (v) => M.t + ih - (v / yMax) * ih;
  const step = iw / runs.length;
  const bw = Math.min(32, step - 2); // 2px reze med stolpci

  for (const v of ticks.values) {
    svg.appendChild(svgEl("line", {
      x1: M.l, x2: M.l + iw, y1: y(v), y2: y(v),
      stroke: v === 0 ? INK_AXIS : INK_GRID, "stroke-width": 1,
    }));
    svg.appendChild(svgEl("text", {
      x: M.l - 8, y: y(v) + 4, "text-anchor": "end",
      fill: INK_AXIS, "font-size": 10, "font-family": "'IBM Plex Mono', monospace",
    }, `${Math.round(v / 60)}`));
  }

  runs.forEach((r, i) => {
    const cx = M.l + step * i + step / 2;
    const h = Math.max(2, M.t + ih - y(r.final_delay_s));
    const rect = svgEl("rect", {
      x: cx - bw / 2, y: y(r.final_delay_s), width: bw, height: h,
      rx: 4, fill: delayColor(r.final_delay_s),
    });
    rect.addEventListener("mousemove", (ev) => showTip(
      `<div class="tt-title">${escapeHtml(r.service_date)}</div>` +
      `<div class="tt-row"><span>končna</span><b>${delayLabel(r.final_delay_s)} min</b></div>` +
      `<div class="tt-row"><span>največja med potjo</span><b>${delayLabel(r.max_delay_s)} min</b></div>` +
      `<div class="tt-note">${r.stops_observed} postaj z meritvijo</div>`, ev));
    rect.addEventListener("mouseleave", hideTip);
    svg.appendChild(rect);

  });

  // Datumi pod stolpci: toliko, kolikor jih gre brez prekrivanja. Vsak
  // datum rabi ~34 px; kadar jih je vec, pisemo vsakega k-tega in vedno
  // zadnjega -- ta je "danes" in je edini, ki ga clovek isce.
  const naK = Math.max(1, Math.ceil(34 / step));
  runs.forEach((r, i) => {
    if (i % naK !== 0 && i !== runs.length - 1) return;
    svg.appendChild(svgEl("text", {
      x: M.l + step * i + step / 2, y: H - 10, "text-anchor": "middle",
      fill: INK_AXIS, "font-size": 10, "font-family": "'IBM Plex Sans', sans-serif",
    }, dayLabel(r.service_date)));
  });
  return svg;
}

// ---------- zemljevid ene voznje ----------
// "Kje je zdaj" je pri avtobusu prvo vprasanje in nanj zna odgovoriti samo
// GPS. Vlaki lege nimajo, zato zanje tega okvira ni -- prazen bi obljubljal
// podatek, ki ne obstaja.
//
// Leaflet se nalozi SELE, ko je lega res na voljo: sicer bi vsako okno vlaka
// vleklo knjiznico, ki je ne bo nikoli uporabilo.

let leafletReady = null;

function loadLeaflet() {
  if (leafletReady) return leafletReady;
  leafletReady = new Promise((resolve, reject) => {
    const css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
    document.head.appendChild(css);
    const js = document.createElement("script");
    js.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    js.onload = resolve;
    js.onerror = reject;
    document.head.appendChild(js);
  });
  return leafletReady;
}

const runMap = { map: null, marker: null, line: null, stops: null,
                 trasa: null, cums: null, postaje: null, v: null, since: 0,
                 me: null, loc: null, gps: null, prosto: false };

// ---------- ocena lege med dvema meritvama ----------
//
// Lega je ob strezbi ze ~30 s stara (izmerjeno), kar je pri 30 km/h cetrt
// kilometra. Piko zato premaknemo naprej po trasi za `hitrost x starost`.
//
// Izmerjeno na 79 primerih (razmik 15-60 s), napaka proti dejanski naslednji
// legi: pika pri miru mediana 63 m in 63 % v 100 m, premik po smeri 36 m in
// 72 %, **premik po trasi 30 m in 80 %**. Trasa je boljsa od smeri, ker cesta
// zavija, vozilo pa ne pove, da bo zavilo.
//
// Ocena, ne meritev -- zato se ne premika, kadar vozilo stoji ali kadar ni na
// tej trasi, in podnapis pove, da je ocenjena.
const OCENA_MAX_ODMIK_M = 120;

function metriNaStopinjo(lat) {
  return { lat: 111320, lon: 111320 * Math.cos(lat * Math.PI / 180) };
}

function razdaljaM(a, b) {
  const k = metriNaStopinjo((a[0] + b[0]) / 2);
  const dy = (a[0] - b[0]) * k.lat;
  const dx = (a[1] - b[1]) * k.lon;
  return Math.sqrt(dx * dx + dy * dy);
}

// Kumulativne dolzine vzdolz trase, izracunane enkrat ob nalaganju.
function kumulative(pts) {
  const out = [0];
  for (let i = 1; i < pts.length; i++) out.push(out[i - 1] + razdaljaM(pts[i - 1], pts[i]));
  return out;
}

// Najblizja tocka na trasi: kako dalec vzdolz nje lezi in kako dalec od nje
// je iskana tocka. Odmik je merilo zaupanja -- velik pomeni, da tocka tej
// trasi ne pripada in racun po poti nima smisla.
function projekcijaNaTraso(pts, cums, lat, lon) {
  const k = metriNaStopinjo(lat);
  let najOdmik = Infinity, vzdolz = 0;
  for (let i = 0; i < pts.length - 1; i++) {
    const [ay, ax] = pts[i], [by, bx] = pts[i + 1];
    const vx = (bx - ax) * k.lon, vy = (by - ay) * k.lat;
    const wx = (lon - ax) * k.lon, wy = (lat - ay) * k.lat;
    const len2 = vx * vx + vy * vy;
    const t = len2 === 0 ? 0 : Math.max(0, Math.min(1, (wx * vx + wy * vy) / len2));
    const odmik = razdaljaM([lat, lon], [ay + t * (by - ay), ax + t * (bx - ax)]);
    if (odmik < najOdmik) {
      najOdmik = odmik;
      vzdolz = cums[i] + t * (cums[i + 1] - cums[i]);
    }
  }
  return { vzdolz, odmik: najOdmik };
}

// Tocka, ki lezi `cilj` metrov vzdolz trase.
function tockaNaTrasi(pts, cums, dolzina) {
  const cilj = Math.max(0, Math.min(dolzina, cums[cums.length - 1]));
  for (let i = 0; i < cums.length - 1; i++) {
    if (cilj >= cums[i] && cilj <= cums[i + 1]) {
      const d = cums[i + 1] - cums[i];
      const f = d === 0 ? 0 : (cilj - cums[i]) / d;
      return [pts[i][0] + f * (pts[i + 1][0] - pts[i][0]),
              pts[i][1] + f * (pts[i + 1][1] - pts[i][1])];
    }
  }
  return pts[pts.length - 1];
}

// Med dvema legama avtobus ne vozi ves cas -- na postajaliscih stoji, in
// `hitrost x starost` ga zato odnese predalec. Izmerjeno na 139 parih
// zaporednih leg (150 vozil, 1. 9. zvecer), napaka proti dejanski naslednji
// legi -- rez na 35 parih, kjer na poti RES lezi postajalisce:
//
//   razlicica                mediana   povprecje   v 100 m
//   premik po trasi (prej)    109 m      136 m      46 %
//   ustavi pri prvi postaji    59 m      110 m      69 %
//   **postanek 15 s**          53 m       99 m      71 %
//
// Cez vse pare 54 -> 45 m mediane in 69 -> 76 % v 100 m. Med 10 in 20 s je
// rezultat raven (povprecje 84,4 / 83,0 / 83,6 m), zato 15 s ni izbrano
// natancno, ampak je sredina izmerjene ravnine -- isto kot `MIN_DWELL_S`.
const POSTANEK_S = 15;
// Postajalisce, na katerem vozilo ze stoji, ne steje se enkrat.
const ZA_SABO_M = 15;

// Kje je vozilo priblizno ZDAJ. Brez trase ali med mirovanjem vrne izmerjeno
// lego -- ocena, ki ne ve, kam naprej, ni boljsa od meritve.
function ocenjenaLega(v, starostS) {
  if (!runMap.trasa || !v.speed_ms || v.speed_ms < 1) return [v.lat, v.lon];
  const { vzdolz, odmik } = projekcijaNaTraso(runMap.trasa, runMap.cums, v.lat, v.lon);
  if (odmik > OCENA_MAX_ODMIK_M) return [v.lat, v.lon];

  // Vozi s trenutno hitrostjo, na vsakem vmesnem postajaliscu porabi postanek.
  let ostanek = starostS, kje = vzdolz;
  for (const p of (runMap.postaje || [])) {
    if (p <= vzdolz + ZA_SABO_M) continue;
    const doPostaje = (p - kje) / v.speed_ms;
    if (doPostaje >= ostanek) break;
    ostanek -= doPostaje + POSTANEK_S;
    kje = p;
    if (ostanek <= 0) break;
  }
  const cilj = kje + Math.max(0, ostanek) * v.speed_ms;
  return tockaNaTrasi(runMap.trasa, runMap.cums, cilj);
}

// Ista oblika kot na velikem zemljevidu -- avtobus je vozilo, ne pika, in
// kaze v smer voznje.
// Na tem zemljevidu vozilo NI meritev, ampak ocena, zato ni zeleno: zelena je
// v projektu barva izmerjenega (postajalisca, trasa), `ESTIMATE_COLOR` pa je
// rezervirana prav za "tu meritve ni". Prosojnost pove isto se enkrat, za
// tistega, ki barv ne loci.
function busDivIcon(bearing, moving) {
  const s = 30;
  return L.divIcon({
    className: "bus-marker",
    html: `<div style="transform:rotate(${bearing || 0}deg);width:${s}px;height:${s}px">
      <svg width="${s}" height="${s}" viewBox="0 0 24 24">
        <rect x="7.5" y="2.5" width="9" height="19" rx="3.2" fill="${ESTIMATE_COLOR}"
              fill-opacity="${moving ? 0.78 : 0.45}" stroke="#0f1115" stroke-width="1.5"/>
        <path d="M9.2 5.6 Q12 4.4 14.8 5.6 L14.8 7.4 Q12 6.6 9.2 7.4 Z"
              fill="#0f1115" fill-opacity="0.55"/>
      </svg></div>`,
    iconSize: [s, s], iconAnchor: [s / 2, s / 2],
  });
}

async function drawRunMap(v) {
  const wrap = document.getElementById("run-map-wrap");
  await loadLeaflet();

  const prvic = !runMap.map;
  if (prvic) {
    // Zemljevid je ELEMENT na strani, ne stran, zato geste, ki bi ukradle
    // pomikanje strani, tu ne veljajo -- a samo tiste, ki ga res ukradejo.
    // Kolesce ne priblizuje (klasicna nadloga: kazalec zaide cez zemljevid in
    // stran se neha pomikati), pac pa Ctrl/Cmd + kolesce. `dragging` pa ostane
    // VKLOPLJEN: vlecenje z misko strani ne pomika in ni v konfliktu z nicimer.
    // Preklopi ga `initDragPolicy()`, in sicer po VHODNI NAPRAVI, ne po
    // napravi nasploh -- prenosnik z zaslonom na dotik mora imeti oboje.
    runMap.map = L.map("run-map", {
      zoomControl: false, scrollWheelZoom: false,
      // Navedba podlage je pogoj rabe (Esri in OpenStreetMap), ne okras --
      // `attributionControl: false` jo je odstranil s cele strani. Ostane,
      // le brez Leafletove lastne oznake, ker okvir meri 260 px.
      attributionControl: true,
    }).setView([v.lat, v.lon], 14);
    runMap.map.attributionControl.setPrefix("");
    L.control.zoom({ position: "topright" }).addTo(runMap.map);
    // Esri ima prave ploscice do z16; nad tem raztegnemo zadnjo (glej dashboard).
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/"
      + "World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
      { maxZoom: 19, maxNativeZoom: 16, attribution: ESRI_ATTR })
      .addTo(runMap.map);

    // Trasa po cesti oziroma progi. Kadar je ni, ostane crta skozi
    // postajalisca -- ta ni pot in mora biti videti drugace (crtkano).
    let trasa = null;
    try {
      const r = await fetch(`/api/trip/${encodeURIComponent(state.run.trip_id)}/shape`);
      if (r.ok) trasa = (await r.json()).points;
    } catch (err) {
      /* brez trase narisemo postajalisca */
    }
    // `trasa` je seznam KOSOV, ne tock: uvoz jo razreze tam, kjer je v GTFS
    // razmik nad kilometer. Pogoj `trasa.length > 1` je bil napisan se za
    // ravno listo tock in je zato izlocil vsako enodelno traso -- 2 706 od
    // 2 897 oblik, torej 93 %. Proga se ni risala skoraj nikoli.
    const kosi = (trasa || []).filter((k) => k && k.length > 1);
    if (kosi.length) {
      L.polyline(kosi, { color: "#0f1115", weight: 6, opacity: 0.85 }).addTo(runMap.map);
      runMap.line = L.polyline(kosi, { color: "#4db97f", weight: 3, opacity: 0.95 })
        .addTo(runMap.map);
      // Za projekcijo vzamemo najdaljsi kos -- vozilo je skoraj vedno na njem.
      const kos = kosi.reduce((a, b) => (b.length > a.length ? b : a));
      runMap.trasa = kos;
      runMap.cums = kumulative(kos);
    }
    const postaje = (state.run.stops || []).filter((s) => s.lat != null && s.lon != null);
    const pts = postaje.map((s) => [s.lat, s.lon]);
    // Kje vzdolz trase lezijo postanki -- ocena lege se na njih ustavi.
    // Postaja, ki je od trase vec kot 60 m, tej trasi ne pripada (napacen
    // kos, obvoz) in bi oceno ustavila na napacnem mestu.
    if (runMap.trasa) {
      runMap.postaje = postaje
        .map((s) => projekcijaNaTraso(runMap.trasa, runMap.cums, s.lat, s.lon))
        .filter((r) => r.odmik <= 60)
        .map((r) => r.vzdolz)
        .sort((a, b) => a - b);
    }
    if (!kosi.length && pts.length > 1) {
      runMap.line = L.polyline(pts, {
        color: "#4db97f", weight: 2.5, opacity: 0.55, dashArray: "5 5",
      }).addTo(runMap.map);
    }
    if (postaje.length) {
      // Pike so bile `interactive: false` in zato nema tocka na zemljevidu.
      // Ime ob dotiku je edini nacin, da se izve, katera postaja to je --
      // trajne oznake bi na mestni liniji zakrile progo pod sabo.
      runMap.stops = L.layerGroup(postaje.map((s) => bindFlashName(
        L.circleMarker([s.lat, s.lon], {
          radius: 3.6, color: "#0f1115", weight: 1.4,
          fillColor: "#4db97f", fillOpacity: 1,
        }), s.name))).addTo(runMap.map);
    }

    // Postaja, na kateri stoji potnik, mora biti vidna -- brez nje je to
    // zemljevid o vozilu in ne o njegovi poti.
    const yours = yourStop(state.run.stops);
    if (yours && yours.lat != null) {
      L.circleMarker([yours.lat, yours.lon], {
        radius: 6, color: "#0f1115", fillColor: "#f0934f", fillOpacity: 1, weight: 2,
      }).addTo(runMap.map).bindTooltip(yours.name, {
        className: "kajros-tooltip", permanent: true, direction: "right", offset: [8, 0],
      });
    }
  }

  runMap.v = v;
  runMap.since = Date.now();
  postaviVozilo(prvic, true);

  document.getElementById("run-map-full").href =
    `/app/map?lat=${v.lat.toFixed(5)}&lon=${v.lon.toFixed(5)}&z=15`;
  wrap.hidden = false;
  // Okvir je bil skrit, ko je Leaflet meril prostor -- brez tega je siv.
  if (prvic) {
    requestAnimationFrame(() => runMap.map.invalidateSize());
    initFullscreen();
    initWheelZoom();
    initDragPolicy();
    initLocate();
  }
}

// `nova` loci osvezitev PODATKOV od sekundnega premika pike. Podnapis se sme
// prepisati samo ob novih podatkih: `ageHtml()` ob vsakem izpisu postavi novo
// izhodisce, zato ga je sekundno prepisovanje ponastavljalo na izvorno
// vrednost -- stevilka je stala, sekundna zanka v common.js jo je vmes
// povecala, naslednji izris pa povozil. Videti je bilo kot utripanje.
function postaviVozilo(prvic, nova) {
  const v = runMap.v;
  if (!v || !runMap.map) return;
  const moving = (v.speed_kmh || 0) >= 3;
  const starost = v.age_s + (Date.now() - runMap.since) / 1000;
  const kje = ocenjenaLega(v, starost);
  const odmik = razdaljaM(kje, [v.lat, v.lon]);

  if (!runMap.marker) {
    runMap.marker = L.marker(kje, { icon: busDivIcon(v.bearing, moving) }).addTo(runMap.map);
  } else {
    runMap.marker.setLatLng(kje);
    runMap.marker.setIcon(busDivIcon(v.bearing, moving));
  }

  // Zadnja RESNICNA meritev je edina trdna tocka na tem zemljevidu, zato je
  // polna in vidna -- ne bleda. Riše se VEDNO: kadar se ocena ni premaknila
  // (vozilo stoji), jo oblika vozila pokrije in dveh oznak ni videti, opomba
  // pod zemljevidom pa ostane resnicna v obeh primerih.
  if (!runMap.gps) {
    // Rdeca s svetlim obrocem: postajalisca in trasa so zeleni, zato se
    // zelena pika med njimi izgubi. Rdeca ni iz nobene lestvice -- ne iz
    // zamud in ne iz razmer -- zato tu ne more pomeniti nicesar drugega.
    runMap.gps = L.circleMarker([v.lat, v.lon], {
      radius: 5.5, color: "#e7eaf0", weight: 2, opacity: 0.95,
      fillColor: "#ff4d5e", fillOpacity: 1,
    }).addTo(runMap.map);
    bindFlashName(runMap.gps, "zadnja izmerjena lega");
  } else {
    runMap.gps.setLatLng([v.lat, v.lon]);
  }
  // Crta in pika sta v isti plasti (overlayPane) in vrstni red risanja je
  // vrstni red dodajanja. Trasa se doda enkrat, pika enkrat -- a postajalisca
  // vmes, zato jo eksplicitno dvignemo. Sicer 3 px siroka trasa prerezhe piko
  // in ta je videti kot del proge.
  runMap.gps.bringToFront();

  // Pogled premaknemo samo, kadar vozilo uide iz okvira -- sicer bi ga
  // sekundno osvezevanje trgalo izpod prsta.
  const ll = L.latLng(kje);
  if (prvic || !runMap.map.getBounds().contains(ll)) runMap.map.panTo(ll);

  // Vozilo se premika, torej se razdalja spreminja tudi brez novega dotika.
  if (runMap.loc) izracunajRazdaljo(runMap.loc);

  if (nova) {
    document.getElementById("run-map-sub").innerHTML =
      `${moving ? `${v.speed_kmh} km/h` : "stoji"} · `
      + (odmik > 40 ? `ocenjeno iz lege pred ${ageHtml(v.age_s)}`
                    : `lega stara ${ageHtml(v.age_s)}`);
  }
}

// Med dvema meritvama pika drsi naprej. To ni okras: vozilo se v 30 s pri
// 30 km/h premakne cetrt kilometra, in prav to je vprasanje, zaradi katerega
// je clovek odprl to stran.
setInterval(() => {
  if (document.visibilityState === "hidden") return;
  if (runMap.marker) postaviVozilo(false, false);
}, 1000);

// Zemljevid cez celo STRAN, ne cez cel zaslon. Fullscreen API vzame ves
// monitor in skrije brskalnik -- za "hocem videti vec zemljevida" je to
// prevec: clovek izgubi naslovno vrstico, gumb nazaj in vsak drug orientir,
// izhod pa je tipka, ki je na telefonu ni. Razred na okviru naredi isto
// koristno stvar in nic od tega.
function setMapMax(on) {
  const wrap = document.getElementById("run-map-wrap");
  const btn = document.getElementById("run-map-fs");
  if (!wrap) return;
  wrap.classList.toggle("is-max", on);
  // Cez celo stran ni nicesar krasti: zemljevid JE stran, zato oboje prosto.
  runMap.prosto = on;
  if (runMap.map) {
    if (on) { runMap.map.dragging.enable(); runMap.map.scrollWheelZoom.enable(); }
    else { runMap.map.scrollWheelZoom.disable(); }
  }
  if (btn) {
    btn.setAttribute("aria-pressed", String(on));
    btn.title = on ? "Pomanjšaj" : "Čez celo stran";
  }
  // Leaflet meri okvir sam in ga po spremembi velikosti ne premeri.
  if (runMap.map) requestAnimationFrame(() => runMap.map.invalidateSize());
}

// Ctrl/Cmd + kolesce priblizuje tudi v vgrajenem zemljevidu. Na sledilni
// ploscici brskalnik sipanje prstov posilja prav kot `wheel` s `ctrlKey`,
// zato ista koda pokrije oboje. Namig se pokaze SAMO ob poskusu brez tipke --
// takrat, ko clovek res ne ve, zakaj se nic ne zgodi.
// En prst mora pomikati STRAN, miska pa zemljevid. Zato preklapljamo po
// vhodni napravi ob vsakem dotiku oziroma pritisku, ne enkrat za vselej.
//
// Poslusamo v ZAJEMNI fazi na ovoju: Leaflet svoj `touchstart` obesi na
// zabojnik zemljevida in ga dobi v mehurcni fazi, torej za nami. Ce dragging
// izklopimo prej, Leaflet svojega poslusalca sploh nima vec in vlecenja ne
// zacne. Obratno pri miski.
//
// Dva prsta zemljevid vseeno pomikata in priblizujeta -- to opravi
// `touchZoom`, ki med sirjenjem prstov premika tudi sredisce.
function initDragPolicy() {
  const wrap = document.getElementById("run-map-wrap");
  if (!wrap || !runMap.map) return;
  const nastavi = (naj) => {
    if (runMap.prosto) return;             // cez celo stran je vse prosto
    if (naj) runMap.map.dragging.enable();
    else runMap.map.dragging.disable();
  };
  wrap.addEventListener("touchstart", () => nastavi(false),
                        { capture: true, passive: true });
  wrap.addEventListener("mousedown", () => nastavi(true), { capture: true });
}

function initWheelZoom() {
  const el = runMap.map && runMap.map.getContainer();
  if (!el) return;
  let namigT = null;
  el.addEventListener("wheel", (e) => {
    if (runMap.map.scrollWheelZoom.enabled()) return;   // razsirjen pogled
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault();
      runMap.map.setZoomAround(runMap.map.mouseEventToContainerPoint(e),
                               runMap.map.getZoom() + (e.deltaY < 0 ? 1 : -1));
      return;
    }
    const n = document.getElementById("run-map-hint");
    if (!n) return;
    n.hidden = false;
    clearTimeout(namigT);
    namigT = setTimeout(() => { n.hidden = true; }, 2200);
  }, { passive: false });
}

// ---------- moja lega na malem zemljevidu ----------
//
// Vprasanje ni "kako dalec je vozilo zracno", ampak "koliko poti ima se do
// mene". Zato oboje projiciramo na traso in odstejemo razdalji vzdolz nje:
// zracna crta cez Golovec je pri mestnem avtobusu lahko trikrat krajsa od
// prave in bi obljubljala prihod, ki ga ne bo.
//
// Kadar clovek ni ob tej progi, racuna ne delamo. Meja je 1 km: blok ali dva
// stran se je "pri postajaliscu", cez to pa projekcija ni vec smiselna in
// stevilka bi bila izmisljena.
const OB_PROGI_M = 1000;

function razdaljaText(m) {
  // Decimalno vejico, ne pike: "1.5 km" je angleski zapis.
  if (m >= 10000) return `${Math.round(m / 1000)} km`;
  if (m >= 950) return `${(m / 1000).toFixed(1).replace(".", ",")} km`;
  return `${Math.round(m / 10) * 10} m`;
}

function izracunajRazdaljo(loc) {
  const el = document.getElementById("run-map-me-line");
  if (!el) return;
  const v = runMap.v;
  if (!v || !runMap.trasa) {
    el.innerHTML = '<span class="slabo">Za to vožnjo trase ni, zato razdalje '
      + 'po poti ni mogoče izmeriti.</span>';
    el.hidden = false;
    return;
  }
  const jaz = projekcijaNaTraso(runMap.trasa, runMap.cums, loc.lat, loc.lon);
  if (jaz.odmik > OB_PROGI_M) {
    el.innerHTML = `<span class="slabo">Od te proge si ${razdaljaText(jaz.odmik)} `
      + `stran, zato razdalje po poti ni mogoče izmeriti.</span>`;
    el.hidden = false;
    return;
  }
  // Vozilo jemljemo na OCENJENI legi -- isti, ki je narisana. Dve stevilki o
  // istem vozilu, ena s slike in ena iz besedila, se ne smeta razhajati.
  const starost = v.age_s + (Date.now() - runMap.since) / 1000;
  const kje = ocenjenaLega(v, starost);
  const vozilo = projekcijaNaTraso(runMap.trasa, runMap.cums, kje[0], kje[1]);
  const d = vozilo.vzdolz - jaz.vzdolz;
  // "je 1,5 km pred tvojo lego" se bere dvoumno -- lahko kot "ze mimo tebe".
  // Zato povemo, koliko POTI mu ostane, in loceno, ce je ze mimo.
  el.innerHTML = d <= 0
    ? `Do tebe ima še <strong>${razdaljaText(-d)}</strong> poti.`
    : `Tvojo lego je že prevozil — <strong>${razdaljaText(d)}</strong> naprej po poti.`;
  el.hidden = false;
}

function initLocate() {
  const btn = document.getElementById("run-map-me");
  if (!btn) return;
  btn.hidden = false;
  btn.addEventListener("click", async () => {
    const el = document.getElementById("run-map-me-line");
    el.innerHTML = '<span class="slabo">iščem lokacijo …</span>';
    el.hidden = false;
    try {
      const loc = await locateMe();
      if (!runMap.me) runMap.me = L.layerGroup().addTo(runMap.map);
      drawMe(runMap.me, loc);
      // Pogled naj zajame OBOJE -- vprasanje je razmerje med tabo in vozilom,
      // ne ena ali druga tocka.
      if (runMap.marker) {
        runMap.map.fitBounds(
          L.latLngBounds([[loc.lat, loc.lon], runMap.marker.getLatLng()]),
          { padding: [40, 40], maxZoom: 16 });
      } else {
        runMap.map.setView([loc.lat, loc.lon], 15);
      }
      runMap.loc = loc;
      izracunajRazdaljo(loc);
    } catch (err) {
      el.innerHTML = `<span class="slabo">${escapeHtml(err.message)}</span>`;
    }
  });
}

function initFullscreen() {
  const btn = document.getElementById("run-map-fs");
  if (!btn) return;
  btn.hidden = false;
  btn.addEventListener("click", () => {
    const wrap = document.getElementById("run-map-wrap");
    setMapMax(!(wrap && wrap.classList.contains("is-max")));
  });
  // Escape je pricakovan izhod, tudi ce gumb ostane viden.
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") setMapMax(false);
  });
}

function loadPosition() {
  const trip = (state.run && state.run.trip_id) || URL_TRIP;
  if (!trip || !state.run) return;
  // Lega obstaja samo za tekoci dan; za ogled preteklega dne je vprasanje
  // "kje je zdaj" brez pomena.
  if (state.run.service_date !== todayIso()) return;
  // Prej se je lega nalozila ENKRAT in nikoli vec: kdor je okno pustil odprto,
  // je gledal, kje je bil avtobus ob odprtju strani. Prav tu je vprasanje
  // "kje je zdaj" najbolj neposredno, zato se osvezuje v koraku s strezbo.
  pollVehicles(`/api/vehicles?trip=${encodeURIComponent(trip)}`, (list) => {
    if (list.length) drawRunMap(list[0]);
  });
}

// ---------- vreme ----------

async function loadWeather() {
  try {
    const res = await fetch(`/api/train/${ENC}/weather${DATE_Q}`);
    if (!res.ok) return;
    const data = await res.json();
    state.weather = new Map((data.stops || []).map((s) => [s.stop_seq, s]));
    // Vreme pride pozneje kot voznja -- kar je ze izrisano, je treba osveziti.
    // Po ISTI poti kot `loadRun`: prej je to risalo po svoje in ob neugodnem
    // vrstnem redu odgovorov pobrisalo blok "pri tebi" in verigo vozila,
    // casovnico pa izrisalo brez omejitve na postaje naprej.
    if (state.run) {
      renderRunHead();
      renderTimeline();
      renderProfile();
    }
  } catch (err) {
    console.error("vremena ni bilo mogoče naložiti", err);
  }
}

// ---------- zgodovina ----------

async function loadHistory() {
  let h;
  const today = state.run ? state.run.service_date : null;
  try {
    // `trip` je nujen, ne okrasen: brez njega zgodovina zdruzi vse voznje te
    // stevilke in pri avtobusu pomesa obe smeri pod isto zaporedno stevilko.
    const q = (today ? `&exclude_date=${encodeURIComponent(today)}` : "")
      + ((state.run && state.run.trip_id) || URL_TRIP
          ? `&trip=${encodeURIComponent((state.run && state.run.trip_id) || URL_TRIP)}` : "");
    h = await fetch(`/api/train/${ENC}/history?days=90${q}`).then((r) => r.json());
  } catch (err) {
    console.error("zgodovine ni bilo mogoče naložiti", err);
    return;
  }

  state.pastRuns = h.runs_observed || 0;
  state.past = new Map((h.by_stop || []).map((b) => [b.stop_seq, b]));

  const first = h.runs && h.runs.length ? h.runs[0].service_date : null;
  document.getElementById("hist-note").innerHTML = state.pastRuns
    ? `Zajetih ${escapeHtml(pluralRuns(state.pastRuns))} pred današnjo${first ? `, od ${escapeHtml(first)}` : ""}.` +
      (state.pastRuns < 10 ? " <strong>Premalo za porazdelitev</strong> — številke spodaj opisujejo teh nekaj voženj, ne značilnega dne." : "")
    : "Pred današnjo vožnjo za to pot še ni zajete nobene druge.";

  renderTiles(h);
  renderProfile();

  const runs = (h.runs || []).filter((r) => r.final_delay_s != null);
  const runsSub = document.getElementById("runs-sub");
  const runsEl = document.getElementById("runs-chart");
  if (runs.length >= 3) {
    mountChart(runsEl, (w) => drawRuns(w, runs, (n, vsi) => {
      runsSub.textContent = n < vsi
        ? `ena vožnja = en stolpec · zadnjih ${n} od ${vsi} zajetih`
        : "ena vožnja = en stolpec";
    }));
  } else if (runs.length) {
    // Pod tremi voznjami stolpci ne povedo nic vec kot seznam -- in namigujejo
    // na trend, ki ga ni.
    runsSub.textContent = "premalo voženj za graf — naštete so vse";
    runsEl.innerHTML = runs.map((r) => `
      <div class="run-row">
        <span class="run-date">${escapeHtml(r.service_date)}</span>
        <span class="run-meta">${r.stops_observed} postaj z meritvijo</span>
        <span class="run-value" style="color:${delayColor(r.final_delay_s)}">${delayLabel(r.final_delay_s)}</span>
      </div>`).join("");
  } else {
    runsSub.textContent = "";
    runsEl.innerHTML = '<div class="empty-state">ni druge zajete vožnje</div>';
  }
}

// ---------- smer vlaka iz /api/live, ura ----------

async function loadHeadsign() {
  try {
    const live = await fetch("/api/live").then((r) => r.json());
    const me = live.find((t) => t.train_no === TRAIN_NO);
    if (me && me.headsign) headsignEl.textContent = me.headsign;
  } catch (err) {
    /* smer je postranska -- brez nje stran deluje naprej */
  }
}

function tickClock() {
  const fmt = new Intl.DateTimeFormat("sl-SI", {
    timeZone: "Europe/Ljubljana", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false,
  });
  document.getElementById("clock").textContent = fmt.format(new Date());
}

tickClock();
setInterval(tickClock, 1000);
refreshFeedDot();
pollWhileVisible(refreshFeedDot, 30000);

// Zgodovina rabi datum tekoce voznje, da ga izpusti iz povprecja -- zato sele
// za njo.

initMode(() => {
  renderTimeline();     // preprosto kaze samo naprej, napredno vso pot
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => redrawers.forEach((f) => f()), 60);
});

loadWeather();
loadAlerts();
loadHeadsign();

// Zgodovina rabi datum tekoce voznje, da ga izpusti iz povprecja ("zajetih N
// PRED danasnjo"), zato sele za prvim `loadRun`. Vzporeden zagon bi danasnjo
// voznjo stel v svoje lastno povprecje.
pollWhileVisible(loadRun, RUN_POLL_MS);
loadRun().then(() => pollWhileVisible(loadHistory, HIST_POLL_MS));
