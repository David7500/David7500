"use strict";

// Domaca stran: ploscice. Zivih stevilk o omrezju tu ni ("danes obicajno
// +2 min", stevec vozil) -- vsak dan skoraj iste in ne spremenijo nicesar, kar
// bo clovek na tej strani storil. Stevilo ovir ostane, ker pove, ali je danes
// kaj drugace, in pride iz `/api/health`, ki ga stran bere tako ali tako.

async function load() {
  try {
    const h = await fetch("/api/health").then((r) => r.json());
    const n = h.alerts_active;
    if (typeof n === "number") {
      document.getElementById("ovire-n").textContent = n ? String(n) : "";
      document.getElementById("ovire-pod").textContent = n ? "velja zdaj" : "zdaj jih ni";
    }
  } catch (err) {
    /* stevilo ovir je postransko */
  }
}

// ---------- budilke ----------
//
// **Budilke so prva ploscica, ne povezava pod "Še".** Prijavljeno 14. 9. 2026:
// "budilke morajo biti takoj dostopne, ne da isces, kje so". V aplikaciji jih
// beremo iz telefona (`Kajros.seznam()`); uro zvonjenja in odhod izracuna
// Kotlin, ne stran -- dvojnik pravila v JavaScriptu bi se razsel s tistim, kar
// budilka res naredi. V brskalniku budilk ni, ploscica povabi na aplikacijo.

const URA = new Intl.DateTimeFormat("sl-SI",
  { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Ljubljana" });
const DAN = new Intl.DateTimeFormat("sl-SI",
  { weekday: "short", day: "numeric", month: "numeric", timeZone: "Europe/Ljubljana" });
const KRATICE = ["pon", "tor", "sre", "čet", "pet", "sob", "ned"];
//: Koliko drugih budilk pod naslednjo; ostale so v seznamu.
const NAJVEC_DRUGIH = 3;

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

/** Isto poimenovanje kot `Ponovitev.ime()` v aplikaciji. */
function dneviIme(maska) {
  const m = (maska || 0) & 0b1111111;
  if (!m) return "enkratna";
  if (m === 0b1111111) return "vsak dan";
  if (m === 0b0011111) return "vsak delavnik";
  if (m === 0b1100000) return "vikend";
  return KRATICE.filter((_, i) => (m >> i) & 1).join(", ");
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
  return ` <b style="color:${delayColor(s)}">${escapeHtml(delayText(s))}</b>`;
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
  const el = document.getElementById("budilke");
  if (!MOST) {
    el.outerHTML = `<a class="p p-bud p-bud-splet" id="budilke" href="/android">
      <span class="oznaka">Budilka</span>
      <strong class="p-ime">Zbudi te, ko vlak res pelje</strong>
      <small>Če zamuja, zazvoni pozneje. Samo v aplikaciji za Android.</small>
      <span class="bud-vec">Prenesi aplikacijo ›</span></a>`;
    return;
  }
  const zdaj = Date.now();
  const vse = beriBudilke();
  const zive = vse.filter((b) => Math.max(b.voznoredni_ms, odhodOf(b)) > zdaj - 60000);
  const prva = zive.filter((b) => !b.ugasnjena).sort((a, b) => kljucOf(a) - kljucOf(b))[0];

  const vrh = `<div class="bud-vrh"><span class="oznaka">${prva && prva.odzvonjeno
    ? "Zazvonila — do odhoda" : "Naslednja budilka"}</span>
    <button type="button" class="bud-vse" data-vse="1">vse budilke ›</button></div>`;

  if (!prva) {
    el.innerHTML = vrh + `<div class="bud-prazno" data-vse="1">
      <strong>${vse.length ? "Vse budilke so ugasnjene" : "Ni nastavljenih budilk"}</strong>
      Odpri vožnjo in pri svoji postaji pritisni „budilka“.</div>`;
    return;
  }

  const velika = prva.odzvonjeno ? odhodOf(prva) : prva.zvoni_ob_ms;
  const pod = prva.odzvonjeno
    ? `odhod po voznem redu ${URA.format(prva.voznoredni_ms)}${zamudaHtml(prva)}`
    : `odhod ${URA.format(odhodOf(prva))}${zamudaHtml(prva)} · ${dneviIme(prva.dnevi)}`
      + ` · zvoni ${prva.minut_prej} min prej${prva.rezerva_s > 0 ? " + rezerva" : ""}`;
  const druge = zive.filter((b) => b !== prva)
    .sort((a, b) => a.ugasnjena - b.ugasnjena || kljucOf(a) - kljucOf(b));

  el.innerHTML = vrh + `
    <div class="bud-glavna" data-vse="1">
      <div class="bud-ura"><strong>${URA.format(velika)}</strong>
        <em>${dan(velika)} · ${cez(velika)}</em></div>
      ${stikaloHtml(prva)}
      <div class="bud-kaj">${kajHtml(prva)}</div>
      <div class="bud-pod">${pod}</div>
    </div>
    ${druge.slice(0, NAJVEC_DRUGIH).map((b) => `
      <div class="bud-vrsta${b.ugasnjena ? " je-ugasnjena" : ""}">
        <span class="bud-cas">${URA.format(b.zvoni_ob_ms)}</span>
        <span class="bud-opis" data-vse="1">${kajHtml(b)}
          <span>${dan(b.zvoni_ob_ms)} · odhod ${URA.format(odhodOf(b))} · ${dneviIme(b.dnevi)}</span></span>
        ${stikaloHtml(b)}
      </div>`).join("")}`;
}

document.getElementById("budilke").parentElement.addEventListener("click", (ev) => {
  if (!MOST) return;
  const s = ev.target.closest(".stikalo");
  if (s) {
    ev.stopPropagation();
    const vklop = s.getAttribute("aria-checked") !== "true";
    if (MOST.preklopi(s.dataset.id, vklop)) izrisiBudilke();
    return;
  }
  if (ev.target.closest("[data-vse]")) MOST.odpriBudilke();
});

// Budilke se spreminjajo tudi drugje (nativni seznam, zvonjenje), odstevanje
// pa tece samo. Zato ob vrnitvi na stran in vsake pol minute.
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) izrisiBudilke();
});
setInterval(() => { if (!document.hidden) izrisiBudilke(); }, 30000);

// ---------- shranjene poti ----------
//
// Iskalnik jih hrani po omrezju (`kajros:fav`), domaca stran pa je edino mesto
// pred izbiro omrezja -- zato jih bere vse in vsaka znacka nosi svoje omrezje.
// **Samo shranjeno, nic samodejnega**: nedavna iskanja so stran spremenila v
// seznam vsega, kar si kdaj pogledal.
function beri(kljuc) {
  try {
    const all = JSON.parse(localStorage.getItem(kljuc) || "[]");
    return Array.isArray(all) ? all.filter((x) => x && x.net) : [];
  } catch (err) {
    return [];
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

function izrisiPoti() {
  const seen = new Set();
  const poti = [];
  for (const f of beri("kajros:fav")) {
    const k = kljucPoti(f);
    if (seen.has(k)) continue;
    seen.add(k);
    poti.push(f);
    if (poti.length >= 6) break;
  }
  if (!poti.length) return;
  document.getElementById("home-chips").innerHTML = poti.map((f) => `
    <a class="chip chip-${f.net === "avtobus" ? "bus" : "train"}"
       href="${escapeHtml(znackaHref(f))}">
      <span class="chip-star">★</span>
      <span>${escapeHtml(znackaOpis(f))}</span>
    </a>`).join("");
  document.getElementById("home-saved").hidden = false;
}

izrisiBudilke();
izrisiPoti();
load();
