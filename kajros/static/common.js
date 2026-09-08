"use strict";

// Skupno za /app in /app/train/{st}. Nalozi se pred dashboard.js oz. train.js.

// Preimenovanje sztrack -> kajros (3. 9. 2026) je premaknilo tudi kljuce v
// localStorage. Brez tega bi shranjene poti, nedavne iskanja in izbrani nacin
// prikaza ob prvem obisku tiho izginili -- za uporabnika izguba podatkov, ki
// je ni povzrocil. Selitev je enkratna in samo kopira; starega ne brise, da se
// da na staro razlicico se vrniti. **Odstrani po 1. 12. 2026.**
(function preseliKljuce() {
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const star = localStorage.key(i);
      if (!star || !star.startsWith("sztrack:")) continue;
      const nov = "kajros:" + star.slice("sztrack:".length);
      if (localStorage.getItem(nov) === null) {
        localStorage.setItem(nov, localStorage.getItem(star));
      }
    }
  } catch (e) {
    // Zasebno okno ali blokiran dostop do shrambe: selitev ni nujna.
  }
})();

// Meje so v MINUTAH in barva se doloci iz iste zaokrozene vrednosti, kot jo
// izpise `delayLabel`. Prej so bile v sekundah (<= 60 s = tocno) in 61 s je
// pisalo "+1" oranzno, 60 s pa "+1" sivo -- ista stevilka, dve barvi. Barva
// ne sme pripovedovati druge zgodbe kot stevilka poleg nje.
const DELAY_RAMP = [
  { maxMin: 0, color: "#7c8698", label: "točno" },
  { maxMin: 5, color: "#f2a87e", label: "1–5 min" },
  { maxMin: 15, color: "#e07b45", label: "5–15 min" },
  { maxMin: Infinity, color: "#b85417", label: "nad 15 min" },
];

// Barva po razredu, ki ga doloci STREZNIK. Pragovi so pravilo in zivijo v
// `stats.opis_zamude()`; barva je oblikovanje in sme biti tu.
const RAZRED_BARVA = {
  "tocno": "#7c8698", "1-5": "#f2a87e", "5-15": "#e07b45", "nad-15": "#b85417",
};

// **Vse spodnje funkcije sprejmejo dvoje**: streznikov objekt `zamuda`
// (`{s, min, razred, vrsta, prezgodaj}`) ali gole sekunde. Objekt ima minuto
// in razred ze izracunana po enem samem pravilu na strezniku -- glej
// `stats.opis_zamude()`. Sekunde ostanejo za mesta, kjer streznik objekta
// (se) ne poslje; racun je tam isti, a je to podvojeno pravilo in naj se ne
// siri. Nov odjemalec (Android) naj bere samo objekt.
function delayMin(z) {
  if (z == null) return null;
  if (typeof z === "object") return z.min;
  return Math.round(z / 60);
}

function delayColor(z) {
  if (z == null) return "#6b7480";
  if (typeof z === "object" && z.razred) return RAZRED_BARVA[z.razred] || "#6b7480";
  const min = delayMin(z);
  return (DELAY_RAMP.find((step) => min <= step.maxMin) || DELAY_RAMP[DELAY_RAMP.length - 1]).color;
}

function delayLabel(z) {
  // Feed ima locljivost 60 s -- zaokrozimo na minute in sekund ne kazemo nikoli.
  const m = delayMin(z);
  if (m == null) return "?";
  return (m > 0 ? "+" : "") + m;
}

// "-5 min" je za potnika uganka, "5 min prej" ni. Barva ostane siva, ker to
// res ni zamuda -- in prav zato mora povedati beseda. `kratko` je za ozke
// stolpce, kjer za "min" ni prostora.
function delayText(z, kratko) {
  const m = delayMin(z);
  if (m == null) return kratko ? "?" : "? min";
  // Prag mora biti na ZAOKROZENI minuti, ne na sekundah. Pri `s <= -60` je
  // -45 s dalo "-1", ker `delayLabel` zaokrozi -- ista minuta, dva zapisa.
  if (m <= -1) return kratko ? `${-m} prej` : `${-m} min prej`;
  return kratko ? delayLabel(z) : `${delayLabel(z)} min`;
}

// Ali je vrednost "prezgodaj". Streznik to ze pove (`zamuda.prezgodaj`),
// sicer po isti zaokrozeni minuti kot `delayText`.
// "-1 min za prestop" je natanko primer, ko zveza NE drzi -- torej tisti, kjer
// mora potnik razumeti brez ugibanja. Nicla ni "0 min za prestop" (videti kot
// podatek), ampak "brez rezerve". Uporabljata iskalnik zvez in pot.
function prestopText(mins) {
  if (mins < 0) return `zmanjka ${Math.abs(mins)} min`;
  if (mins === 0) return "brez rezerve";
  return `${mins} min za prestop`;
}

/** Koliko minut ostane za prestop, ali `null`, kadar zamud ne poznamo.
 *
 * Racuna se iz ZAOKROZENIH minut, ne iz sekund: vse tri stevilke stojijo na
 * zaslonu druga ob drugi in bralec, ki jih sesteje, mora priti do iste. Ista
 * past kot pri razredu zamude.
 */
function preostanekPrestopa(nacrtovanoS, zamudaPrvega, zamudaDrugega) {
  const d1 = delayMin(zamudaPrvega);
  const d2 = delayMin(zamudaDrugega);
  if (d1 == null || d2 == null) return null;
  return Math.floor(nacrtovanoS / 60 + 0.5) - d1 + d2;
}

function isEarly(z) {
  if (z == null) return false;
  if (typeof z === "object") return !!z.prezgodaj;
  return delayMin(z) <= -1;
}

const TIME_FMT = new Intl.DateTimeFormat("sl-SI", {
  timeZone: "Europe/Ljubljana", hour: "2-digit", minute: "2-digit", hour12: false,
});

// Danasnji prometni dan po ljubljanskem casu. "sv-SE" je najkrajsa pot do
// ISO oblike; `toISOString()` bi dal UTC in bi se cez polnoc zlagal za dan.
const todayIso = () => new Date().toLocaleDateString("sv-SE", { timeZone: "Europe/Ljubljana" });

function hhmm(iso) {
  return iso ? TIME_FMT.format(new Date(iso)) : "—";
}

const DATE_FMT = new Intl.DateTimeFormat("sl-SI", {
  timeZone: "Europe/Ljubljana", day: "numeric", month: "numeric",
});

function dayLabel(isoDate) {
  return isoDate ? DATE_FMT.format(new Date(isoDate + "T12:00:00")) : "—";
}

// Navedba podlage. Pogoj rabe pri Esriju in OpenStreetMap, zato je na VSAKEM
// zemljevidu, tudi na 260 px velikem v oknu voznje.
const ESRI_ATTR = 'podlaga &copy; <a href="https://www.esri.com/">Esri</a>, HERE, Garmin, '
  + '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';

// Naslovi obvestil SŽ kricijo in ponavljajo znacko nad sabo: "DELA NA PROGI:
// Obcasna zapora ..." stoji pod zetonom "dela na progi". Predpono odrezemo --
// v sestih od sestnajstih obvestil je ista beseda dvakrat, v verzalkah.
function alertTitle(header) {
  const m = /^[A-ZČŠŽĆĐ][A-ZČŠŽĆĐ0-9 .\-]{2,40}:\s*/.exec(header || "");
  const t = m ? header.slice(m[0].length) : (header || "");
  return t.charAt(0).toUpperCase() + t.slice(1);
}

// Slovenscina ima dvojino in rodilnik mnozine, zato "0 odhodi" in "2 vlakov"
// nista pravilna. Oblike so [1, 2, 3-4, 0 in 5+]; odloca n mod 100.
const SKLONI = {
  odhodi: ["odhod", "odhoda", "odhodi", "odhodov"],
  prihodi: ["prihod", "prihoda", "prihodi", "prihodov"],
  vlak: ["vlak", "vlaka", "vlaki", "vlakov"],
  voznja: ["vožnja", "vožnji", "vožnje", "voženj"],
  prestop: ["prestop", "prestopa", "prestopi", "prestopov"],
  predlog: ["predlog", "predloga", "predlogi", "predlogov"],
  postanek: ["postanek", "postanka", "postanki", "postankov"],
};

function sklon(n, kljuc) {
  const o = SKLONI[kljuc] || SKLONI.vlak;
  const m = Math.abs(n) % 100;
  return m === 1 ? o[0] : m === 2 ? o[1] : (m === 3 || m === 4) ? o[2] : o[3];
}

// Isto sklanjanje kot `journey._fold` v Pythonu: brez tega se iskanje in
// poudarek ne ujameta pri sumnikih ("sentjur" proti "Šentjur"). Bilo je
// prepisano v dveh datotekah -- ista funkcija dvakrat je ista napaka dvakrat.
function fold(s) {
  return String(s).normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

function pluralRuns(n) {
  if (!n) return "brez zajete vožnje";
  if (n === 1) return "1 vožnja";
  if (n === 2) return "2 vožnji";
  if (n === 3) return "3 vožnje";
  if (n === 4) return "4 vožnje";
  return `${n} voženj`;
}

// ---------- znak, da se nekaj dogaja ----------
//
// Na slabi povezavi je klik izgledal, kot da ni delal: stara vsebina je
// ostala na zaslonu in nic se ni premaknilo tudi petnajst sekund. Zato ena
// sama crta na vrhu strani, ki tece, dokler je katerakoli zahteva v teku.
//
// Ovijemo `fetch` in ne vsakega klicatelja posebej: klicnih mest je cez
// trideset, in tisto, ki bi ga kdo pozabil, bi bilo ravno najpocasnejse.
//
// **Crta se pokaze sele po 400 ms.** Hitre zahteve (in tiste v ozadju, ki
// tecejo na 30 s) tako ne utripajo -- kar se zgodi hitro, ne rabi obvestila.
(function () {
  const izvirni = window.fetch;
  if (typeof izvirni !== "function") return;
  let vTeku = 0;
  let cakalec = null;
  let crta = null;

  const pokazi = () => {
    if (crta) return;
    crta = document.createElement("div");
    crta.className = "nalaganje";
    crta.setAttribute("role", "status");
    crta.setAttribute("aria-label", "nalagam");
    document.body.appendChild(crta);
  };
  const skrij = () => {
    if (cakalec) { clearTimeout(cakalec); cakalec = null; }
    if (crta) { crta.remove(); crta = null; }
  };

  window.fetch = function (...args) {
    vTeku += 1;
    if (vTeku === 1 && !cakalec) cakalec = setTimeout(pokazi, 400);
    return izvirni.apply(this, args).finally(() => {
      vTeku -= 1;
      if (vTeku <= 0) { vTeku = 0; skrij(); }
    });
  };
})();

// ---------- most do nativne aplikacije ----------
//
// `window.Kajros` obstaja SAMO v aplikaciji za Android. V brskalniku ga ni in
// nic, kar je vezano nanj, ne sme nastati -- gumb za budilko, ki ne dela, je
// slabsi od gumba, ki ga ni.
//
// `razlicica()` ni vljudnost: stran se posodobi takoj, aplikacija pa cez
// mesec, zato mora stran vedeti, s cim govori, preden karkoli poklice.
const MOST = (() => {
  const k = window.Kajros;
  if (!k || typeof k.razlicica !== "function") return null;
  try {
    return k.razlicica() >= 1 ? k : null;
  } catch (e) {
    return null;
  }
})();

// ---------- pika o zivosti ----------
// Pika je doslej kazala, ali je ODGOVOR prisel, ne ali so PODATKI sveži.
// Če zajem odmre, API pa tece naprej, bi ostala zelena in bi trdila nekaj,
// česar ne ve. Zdaj bere `last_feed_at` iz stanja zajema.

// Feed se osvezuje na 30 s. Trikratnik je dovolj, da ena izpuscena zahteva
// ne prizge opozorila, in dovolj malo, da odmrl zajem opazimo v minuti.
const FEED_STALE_S = 90;

async function refreshFeedDot() {
  const dot = document.getElementById("feed-dot");
  if (!dot) return;
  try {
    const h = await fetch("/api/health").then((r) => r.json());
    const age = h.last_feed_ts ? Date.now() / 1000 - h.last_feed_ts : Infinity;
    const stale = age > FEED_STALE_S;
    dot.classList.toggle("stale", stale);
    dot.title = h.last_feed_at
      ? `zadnji zajem ob ${hhmm(h.last_feed_at)}${stale ? ` — pred ${Math.round(age / 60)} min` : ""}`
      : "zajema še ni bilo";
  } catch (err) {
    dot.classList.add("stale");
    dot.title = "strežnik ni dosegljiv";
  }
}

// ---------- osvezevanje, ki ve za vidnost strani ----------
//
// Aplikacija je predvsem telefonska. Navaden `setInterval` tam tece naprej,
// ko je stran v ozadju -- to je poraba baterije in prenosa za sliko, ki je
// nihce ne gleda. Ob vrnitvi pa clovek gleda vrednost, staro do pol minute,
// in prav takrat je najbolj pomembna: stoji na peronu.
//
// Zato: v ozadju ne osvezujemo, ob vrnitvi osvezimo TAKOJ. Enako ob vrnitvi
// omrezja -- telefon, ki je bil v predoru, ima sicer prazno stran, dokler ne
// potece naslednji interval.
function pollWhileVisible(fn, ms) {
  let timer = null;
  let zadnji = 0;

  const tick = async () => {
    zadnji = Date.now();
    try {
      await fn();
    } catch (err) {
      /* posamezna zahteva sme spodleteti; ritem se ne sme ustaviti */
    }
    if (!document.hidden) timer = setTimeout(tick, ms);
  };

  const wake = () => {
    if (document.hidden) {
      clearTimeout(timer);
      timer = null;
      return;
    }
    if (timer) return;                    // ze tece
    // Ce je od zadnjega osvezevanja minilo manj kot pol intervala, ne
    // podvajamo zahteve -- kratek preklop med aplikacijama ni razlog zanjo.
    const potekel = Date.now() - zadnji >= ms / 2;
    timer = setTimeout(tick, potekel ? 0 : ms - (Date.now() - zadnji));
  };

  document.addEventListener("visibilitychange", wake);
  window.addEventListener("online", wake);
  wake();
  return { stop: () => { clearTimeout(timer); timer = null; } };
}

// ---------- preprosto / napredno ----------
// Isto na vseh straneh, zato tu in ne trikrat. Napreden pogled ni druga stran:
// je razred na <body>, ki odkrije elemente z razredom `adv-only`.
//
// Izbira gre v localStorage, da preklop drzi cez strani. Naslov jo lahko
// povozi (`?pogled=napredno`) -- brez tega naprednega pogleda ni mogoce
// deliti s povezavo, kar je pri strani s stevilkami prva stvar, ki jo kdo
// hoce narediti.

const MODE_KEY = "kajros:mode";

function applyMode(mode, onChange) {
  document.body.classList.toggle("is-advanced", mode === "advanced");
  for (const b of document.querySelectorAll("#mode-switch button")) {
    b.setAttribute("aria-pressed", String(b.dataset.mode === mode));
  }
  try {
    localStorage.setItem(MODE_KEY, mode);
  } catch (err) {
    /* zaseben zavihek ni razlog, da stran ne dela */
  }
  if (onChange) onChange(mode);
}

function initMode(onChange) {
  const asked = new URLSearchParams(location.search).get("pogled");
  let mode = asked === "napredno" ? "advanced" : asked === "preprosto" ? "simple" : null;
  if (!mode) {
    try {
      mode = localStorage.getItem(MODE_KEY) || "simple";
    } catch (err) {
      mode = "simple";
    }
  }
  const box = document.getElementById("mode-switch");
  if (box) {
    box.addEventListener("click", (ev) => {
      const b = ev.target.closest("button[data-mode]");
      if (b) applyMode(b.dataset.mode, onChange);
    });
  }
  applyMode(mode, onChange);
}

// ---------- vlak ali nadomestni prevoz ----------
// Nadomestni prevoz je v istem iskalniku kot vlaki, ker je na tej relaciji
// edina dejanska povezava. Prav zato mora biti oznaka nedvoumna: potnik, ki
// caka na peronu avtobus, ga zamudi.

function isBus(mode) {
  return mode === "bus";
}

// Prevoznik po GTFS agency_id. Pri avtobusu je oznaka linije brez prevoznika
// dvoumna: "25" je lahko LPP ali kaj drugega.
const AGENCY = {
  "1161": "SŽ",
  "1118": "LPP",
  "1123": "Arriva",
  "1119": "Nomago",
  "1121": "AP MS",
  // Mestni LPP je drug vir z besednim `agency_id` (glej `config.LPP_*`).
  "lpp": "LPP",
};

// Ena barva za vse avtobusne linije, in ne barva iz vira.
//
// Prvi razlog je bil, da so vsi LPP-jevi `route_color` ista zelena
// prevoznika. **To za mestni LPP ne velja** -- ta ima 27 razlicnih barv in
// to so prave barve linij, ki jih Ljubljancani poznajo. Razlog je zdaj drug
// in izmerjen: na nasi podlagi (#0f1115) jih **14 od 27 ne dosega 4,5 : 1**,
// stiri so pod 3 : 1, `#1f1d1d` pa pri 1,13 : 1 -- torej nevidna. Nasa
// zelena je pri 7,70 : 1.
//
// Barvati polovico linij po viru in polovico enotno bi bilo slabse od
// enotnega: barva bi takrat pomenila dvoje. Ime linije nosi oznaka sama;
// barva samo pove, cigav avtobus je, zato je v zetonu vedno tudi prevoznik.
const LINE_INK = "#4db97f";

function lineBadgeHtml(row) {
  if (!isBus(row.mode)) return "";
  // Na zeleznicni strani avtobus pomeni NADOMESTNI PREVOZ -- torej "namesto
  // vlaka, ki tu ne vozi". To ni linija mestnega prevoza in ne sme biti
  // videti kot ona; potnik mora prebrati, zakaj tu stoji avtobus.
  if (row.network === "zeleznica") {
    return `<span class="mode-bus" title="namesto vlaka, ki na tej relaciji ne vozi">
      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3.5" y="3.5" width="17" height="15" rx="2.6"></rect>
        <path d="M3.5 10.5h17M3.5 5.8 1.4 6.8M20.5 5.8l2.1 1M6.5 18.6v2.4M17.5 18.6v2.4"></path>
        <circle cx="8" cy="14.6" r="0.9" fill="currentColor" stroke="none"></circle>
        <circle cx="16" cy="14.6" r="0.9" fill="currentColor" stroke="none"></circle>
      </svg>
      nadomestni prevoz
    </span>`;
  }
  const who = AGENCY[row.agency];
  const label = who ? `${who} ${row.train_no}` : row.train_no;
  return `<span class="line-badge" style="color:${LINE_INK};border-color:${LINE_INK}55">
    ${escapeHtml(label)}</span>`;
}

function modeBadgeHtml(mode) {
  if (!isBus(mode)) return "";
  return `<span class="mode-bus" title="nadomestni prevoz namesto vlaka">
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor"
         stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3.5" y="3.5" width="17" height="15" rx="2.6"></rect>
      <path d="M3.5 10.5h17M3.5 5.8 1.4 6.8M20.5 5.8l2.1 1M6.5 18.6v2.4M17.5 18.6v2.4"></path>
      <circle cx="8" cy="14.6" r="0.9" fill="currentColor" stroke="none"></circle>
      <circle cx="16" cy="14.6" r="0.9" fill="currentColor" stroke="none"></circle>
    </svg>
    avtobus
  </span>`;
}

// ---------- vozovnica ----------

const SZ_TRGOVINA = "https://eshop.sz.si/";

/** Povezava na spletno trgovino SŽ. Relacije ni mogoce podati -- glej
 *  `train.vozovnicaHtml()` za razlog. */
function ticketLinkHtml() {
  return `<a class="ticket-link" href="${SZ_TRGOVINA}" target="_blank"
      rel="noopener noreferrer"
      title="Spletna trgovina SŽ. Relacije ni mogoče podati v naslovu, zato jo tam vpišeš sam.">
      Kupi vozovnico na <strong>eshop.sz.si</strong>
      <span class="ticket-note">relacijo vpišeš tam</span>
    </a>`;
}

// ---------- vreme ----------

const WEATHER_INK = "#6f8fa8";

function weatherIconHtml(w, size, tint) {
  if (!w || w.temp_c == null) return "";
  const px = size || 14;
  // Oblika pove, KAJ je (dez, sneg, megla), barva pa KAKO hudo je.
  const c = tint || (w.severity_label ? severityColor(w.severity_label) : null);
  const a = `width="${px}" height="${px}" viewBox="0 0 24 24" fill="none" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"`;
  if ((w.snowfall_cm || 0) > 0) {
    return `<svg ${a} stroke="${c || '#a8d8ff'}"><path d="M12 16a4.5 4.5 0 0 0 0-9 6 6 0 0 0-11 1.8A3.6 3.6 0 0 0 4.6 16"></path><path d="M8 20h.01M12 21h.01M16 20h.01"></path></svg>`;
  }
  if ((w.precip_mm || 0) >= 0.1) {
    return `<svg ${a} stroke="${c || WEATHER_INK}"><path d="M12 16a4.5 4.5 0 0 0 0-9 6 6 0 0 0-11 1.8A3.6 3.6 0 0 0 4.6 16"></path><path d="M8 19l-1 2.5M12 19l-1 2.5M16 19l-1 2.5"></path></svg>`;
  }
  if (w.code === 45 || w.code === 48) {
    return `<svg ${a} stroke="${c || '#79828f'}"><path d="M3 9h18M4 13h16M6 17h12"></path></svg>`;
  }
  if (w.code != null && w.code <= 1) {
    return `<svg ${a} stroke="${c || '#c8a06a'}"><circle cx="12" cy="12" r="4.2"></circle><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M18.4 5.6L17 7M7 17l-1.4 1.4"></path></svg>`;
  }
  return `<svg ${a} stroke="${c || '#5b6472'}"><path d="M12 18a5 5 0 0 0 0-10 6.5 6.5 0 0 0-12 2 4 4 0 0 0 4 4h8"></path></svg>`;
}

function num(v, digits) {
  if (v == null) return "—";
  return v.toFixed(digits == null ? 1 : digits).replace(".", ",");
}

// Semafor, ne lestvica enega odtenka: stopnje se morajo lociti na prvi pogled.
// Tople barve tu ne trkajo z lestvico zamud, ker je v pogledu Vreme zamuda
// narisana nevtralno. Enako kot v weather.py.
const SEVERITY_STYLE = {
  "mirne": "#6b7480",
  "blage": "#5aa87d",
  "zahtevne": "#d9b33c",
  "hude": "#d1495b",
};
const SEVERITY_ORDER = ["mirne", "blage", "zahtevne", "hude"];

function severityColor(scoreOrLabel) {
  if (typeof scoreOrLabel === "string") return SEVERITY_STYLE[scoreOrLabel] || "#3d434f";
  const s = scoreOrLabel;
  if (s == null) return "#3d434f";
  if (s <= 0) return SEVERITY_STYLE["mirne"];
  if (s <= 3) return SEVERITY_STYLE["blage"];
  if (s <= 6) return SEVERITY_STYLE["zahtevne"];
  return SEVERITY_STYLE["hude"];
}

function severityTitle(w) {
  if (!w || w.severity == null) return "";
  const parts = (w.severity_parts || []).map((x) => `${x.what} +${x.points}`).join(", ");
  return `razmere ${w.severity}/10 · ${w.severity_label}` +
    (parts ? ` (${parts})` : "") + ` — ${weatherSummary(w)}`;
}

function weatherSummary(w) {
  if (!w || w.temp_c == null) return "";
  const bits = [];
  if ((w.snowfall_cm || 0) > 0) bits.push(`sneg ${num(w.snowfall_cm)} cm`);
  else if ((w.precip_mm || 0) >= 0.1) bits.push(`dež ${num(w.precip_mm)} mm`);
  else bits.push("brez padavin");
  bits.push(`${num(w.temp_c)} °C`);
  if (w.wind_gust_kmh != null) bits.push(`sunki ${num(w.wind_gust_kmh, 0)} km/h`);
  return bits.join(" · ");
}

// ---------- ena voznja: skupno branje /api/train/{st}/run ----------

// Sekunde, ker jih risanje grafov in izracuni rabijo kot stevilo. Pravilo
// `COALESCE(delay_dep, delay_arr)` -- in NE obratno, ker je `departure.delay`
// izpolnjen pri vseh prevoznikih, `arrival.delay` pa ne -- je na strezniku
// (`stats.opis_zamude()`); tu ga ne ponavljamo, le beremo. Rezerva velja za
// odgovore, ki objekta se nimajo.
function stopDelay(s) {
  if (s && s.zamuda) return s.zamuda.s;
  return s.delay_dep != null ? s.delay_dep : s.delay_arr;
}

/** Streznikova odlocitev za postanek, kadar je na voljo. */
function stopZamuda(s) {
  return (s && s.zamuda) || null;
}

function stopActualIso(s) {
  return s.actual_dep || s.actual_arr;
}

function lastMeasured(run) {
  // Mejo med meritvijo in napovedjo pove STREZNIK (`last_measured_seq`), ne
  // ta koda. Prej je bilo isto pravilo napisano dvakrat -- v `stats.py` in tu
  // -- in dve razlicici istega pravila se prej ali slej razideta. Razlika bi
  // bila tiha: prikaz bi feedovo napoved za se nedosezen postanek pokazal kot
  // izmerjeno zamudo, in po zapisu v CLAUDE.md je bila ta napaka na zaslonu
  // ze dvakrat.
  //
  // `run` je cel odgovor `/api/train/{no}/run`, ne samo postanki.
  const seq = run && run.last_measured_seq;
  if (seq == null) return null;
  return (run.stops || []).find((s) => s.stop_seq === seq) || null;
}

function stopWeatherHtml(w, isForecast) {
  if (!w || w.severity == null) return "";
  // Potnika ne zanima 0,4 mm/h -- zanima ga, ali so razmere hude. Surove
  // stevilke ostanejo v naslovu in v oknu ob grafu.
  //
  // Pri postajah naprej po progi je to NAPOVED (Open-Meteo forecast), ne
  // izmerjeno stanje. Razlika je vidna -- crtkan rob in beseda v naslovu --
  // ker bi enak zeton pomenil, da o prihodnosti vemo enako kot o preteklosti.
  const color = severityColor(w.severity_label);
  const loud = w.severity_label === "zahtevne" || w.severity_label === "hude";
  const title = (isForecast ? "napoved · " : "") + severityTitle(w);
  // Zeton nikoli ne pokaze gole stopnje. "0" potniku ne pove nic -- to je bilo
  // ze popravljeno -- a "1" prav tako ne: stevilka brez enote in brez lestvice
  // je uganka, razlaga pa je v `title`, ki ga na telefonu ni mogoce doseci.
  //
  // Zato: do vkljucno "blagih" (<= 3) pise TEMPERATURA, ki nekaj pove sama po
  // sebi, od "zahtevnih" naprej pa BESEDA, ki pove, kaj je narobe. Barva ostane
  // ista lestvica; beseda je samo tam, kjer je kaj za povedati, in takih
  // postankov je malo, zato sirina ni tezava.
  const tiho = w.severity <= 3;
  const znak = tiho
    ? (w.temp_c != null ? `${Math.round(w.temp_c)}°` : "")
    : w.severity_label;
  // Ze prevozene postaje so v preprostem pogledu skrite; kadar so vidne
  // (napredni pogled), mirno vreme za nazaj ne pove nicesar in gre v ozadje.
  const quiet = tiho ? " is-quiet" + (isForecast ? "" : " adv-only") : "";
  return `<span class="stop-weather${loud ? " is-loud" : ""}${isForecast ? " is-forecast" : ""}${quiet}"` +
    ` title="${escapeHtml(title)}"` +
    (loud ? ` style="background:${color}1f;border-color:${color}66"` : "") + `>` +
    weatherIconHtml(w, 13) +
    `<span class="stop-sev"${tiho ? "" : ` style="color:${color}"`}>${znak}</span></span>`;
}

// Postanek, na katerem se zamuda spremeni. Vlak ne odide vedno takrat, ko
// pride: na Most na Soci ima LP 4219 v voznem redu devet minut postanka
// (krizanje na enotirni progi), zato prispe +10 in odide +3. Ena sama
// stevilka na vrstico to skrije in v grafu nastane skok, ki je videti
// nemogoc -- prav to vprasanje je sprozilo tale izpis.
//
// Redko, a ne zanemarljivo: 406 postankov v voznem redu ima nad dve minuti
// zadrzevanja, in v devetih dneh zajema se prihodna in odhodna zamuda
// razlikujeta pri 1 307 postankih (362 od tega za pet minut ali vec).
// Beseda za vozilo. Postanek opisuje stran, ki ve, ali gleda vlak, avtobus
// ali nadomestni prevoz -- "vlak je stal 4 min" pod mestno linijo 25 ni le
// netocno, ampak zveni kot napaka programa.
let VEHICLE_NOUN = "vlak";

function setVehicleNoun(noun) {
  VEHICLE_NOUN = noun || "vlak";
}

function dwellSplit(s) {
  const a = s.delay_arr;
  const b = s.delay_dep;
  // Na IZHODISCU prihoda ni: vozilo tam zacne. Feed vseeno posilja vrednost
  // in ta je smet -- LPP 25 je 30. 8. na Medvodah naselju porocal prihod
  // -267 s ob odhodu -2 s, na drugi voznji istega dne celo -1771 s. Iz tega
  // je prikaz sestavil zgodbo "stal 4 min namesto 0". Zgodbe o dogodku, ki
  // se ni zgodil, ni.
  if (s.stop_seq === 1) return null;
  if (a == null || b == null || Math.abs(a - b) < 60) return null;
  if (s.arr_s == null || s.dep_s == null) return null;
  const sched = (s.dep_s - s.arr_s) / 60;          // voznoredno zadrzevanje
  return {
    arr: a, dep: b,
    sched: Math.round(sched),
    real: Math.round(sched + (b - a) / 60),
    gained: Math.round((a - b) / 60),
  };
}

// Dolg postanek pred potnikom: povej, na cem ocena stoji. Model racuna, da bo
// vlak postanek skrajsal na dve minuti -- to je skrita predpostavka, ki zna
// biti mocno mimo (RG 1604 v Ljubljani: vozni red 21 min, model 2, resnica 7).
// Zato pokazemo, koliko ta vlak tam RES stoji, kadar zamuja.
const DWELL_SHOW_S = 300;

function dwellPlanHtml(s) {
  if (!s || !s.sched_dwell_s || s.sched_dwell_s < DWELL_SHOW_S) return "";
  const red = Math.round(s.sched_dwell_s / 60);
  if (s.typical_dwell_s == null) {
    return `<div class="stop-dwell">vozni red tu čaka ${red} min</div>`;
  }
  const res = Math.round(s.typical_dwell_s / 60);
  return `<div class="stop-dwell">vozni red tu čaka ${red} min;`
    + ` ${VEHICLE_NOUN === "vlak" ? "ta vlak" : "ta " + VEHICLE_NOUN},`
    + ` kadar zamuja, stoji običajno <strong>${res}</strong>`
    + `<span class="adv-only"> (${escapeHtml(pluralRuns(s.dwell_samples))})</span></div>`;
}

function dwellNoteHtml(d) {
  if (d.gained > 0) {
    return `vozni red tu čaka ${d.sched} min, ${VEHICLE_NOUN} je stal ${Math.max(d.real, 0)}`
      + ` — nadoknadil ${d.gained} min`;
  }
  return `${VEHICLE_NOUN} je stal ${d.real} min namesto ${d.sched}`
    + ` — izgubil ${-d.gained} min`;
}

function measuredStopHtml(s, isCurrent, w) {
  const d = stopDelay(s);
  const color = delayColor(d);
  const actual = hhmm(stopActualIso(s));
  const sched = hhmm(s.sched_dep || s.sched_arr);
  const schedHtml = actual !== sched ? `<span class="stop-sched">${sched}</span>` : "";
  const split = dwellSplit(s);

  // Vsak par (beseda + cas + vozni red) je svoj nedeljiv kos: na telefonu se
  // sme vrstica prelomiti MED prihodom in odhodom, ne pa sredi enega od njiju.
  const leg = (lab, act, sch) =>
    `<span class="stop-leg"><span class="stop-lab">${lab}</span> `
    + `<span class="stop-actual">${hhmm(act)}</span>`
    + `<span class="stop-sched">${hhmm(sch)}</span></span>`;
  const times = split
    ? leg("prihod", s.actual_arr, s.sched_arr) + leg("odhod", s.actual_dep, s.sched_dep)
    : `<span class="stop-actual">${actual}</span>${schedHtml}`;
  const delay = split
    ? `<span style="color:${delayColor(split.arr)}">${delayLabel(split.arr)}</span>`
      + `<span class="stop-arrow">→</span>`
      + `<span style="color:${delayColor(split.dep)}">${delayLabel(split.dep)}</span>`
    : `<span style="color:${color}">${delayText(d, true)}</span>`;

  return `
    <div class="stop-row${isCurrent ? " is-current" : ""}">
      <div class="stop-rail"><span class="stop-dot" style="background:${color}"></span><span class="stop-line"></span></div>
      <div class="stop-main">
        <div class="stop-name">${escapeHtml(s.name)}</div>
        <div class="stop-times">${times}</div>
        ${split ? `<div class="stop-dwell">${escapeHtml(dwellNoteHtml(split))}</div>` : ""}
      </div>
      ${stopWeatherHtml(w)}
      <div class="stop-delay">${delay}</div>
    </div>
  `;
}

// Postanek, katerega ura si nasprotuje z vecino ostalih na tej vozjni.
// Odlocitev je strezenikova (`stats.oznaci_neskladne`) in pride v
// `zamuda.vrsta`: pravilo gleda celo vozjno, zato ga odjemalec ne more
// ponoviti po vrsticah -- in dve razlicici istega pravila sta tiha napaka.
function jeNeskladen(s) {
  return !!(s.zamuda && s.zamuda.vrsta === "neskladno");
}

// Ziva napoved mestnega LPP (`data.lpp.si`). To NI nasa ocena in ni meritev:
// je prevoznikova napoved, izracunana iz lege vozila -- ista vrsta stevilke,
// kot jo nosi derp.si, le da se osvezi na 10-30 s namesto na ~90 s.
// Odlocitev je strezenikova (`api._lpp_zivo`), tu jo samo preberemo.
function zivaNapoved(s) {
  return s && s.zamuda && s.zamuda.vrsta === "živo" ? s.zamuda : null;
}

function gapStopHtml(s) {
  const sched = hhmm(s.sched_dep || s.sched_arr);
  // "Brez meritve" in "podatek si nasprotuje" nista isto: prvo pomeni, da ni
  // prislo nic, drugo, da je prislo in bilo nemogoce -- naslednja postaja
  // PRED prejsnjo. Stevilke zato tu ni, povemo pa, zakaj je ni.
  const zast = jeNeskladen(s);
  return `
    <div class="stop-row is-muted">
      <div class="stop-rail"><span class="stop-dot is-hollow"></span><span class="stop-line"></span></div>
      <div class="stop-main">
        <div class="stop-name">${escapeHtml(s.name)}</div>
        <div class="stop-times"><span class="stop-sched-plain">${sched}</span> <span class="stop-tag">${
          zast ? "ura si nasprotuje" : "brez meritve"}</span></div>
        ${zast ? `<div class="stop-times adv-only"><span class="stop-tag">feed je zadnjič rekel ${
          delayText(stopDelay(s))}, kar bi pomenilo vožnjo nazaj</span></div>` : ""}
      </div>
      <div class="stop-delay is-none">—</div>
    </div>
  `;
}

function forecastStopHtml(s, f, w) {
  // Postaja, ki je vlak se ni dosegel. Uporabimo LASTNO oceno, ne vrednosti
  // iz feeda -- ta je za postanke naprej izmerjeno slaba (glej backtest.py):
  //
  //   feed pravi 0, vlak pa zdaj zamuja >= 5 min:  napaka 18,5 min, v 5 min  6 %
  //   prenos trenutne zamude naprej:               napaka  1,6 min, v 5 min 91 %
  //
  // Feed za se nedosezene postanke pogosto objavi niclo, dokler nima prave
  // napovedi. Prevoznikovo stevilko zato pokazemo le v naprednem pogledu,
  // da ni skrita, a nanjo ne racunamo.
  const schedIso = s.sched_dep || s.sched_arr;
  const sched = hhmm(schedIso);
  // Kadar ocene ni -- voznja se ni zacela, zato ni cesa prenasati naprej --
  // o njej vseeno nekaj vemo: kako je vozila doslej. Brez tega je bilo v oknu
  // voznje povsod "?" in "brez ocene", medtem ko je iskalnik za ISTO voznjo
  // pisal "obicajno 0 min, 16 voznj". Ni napoved za ta dan; je opis preteklih
  // voznj in zeton to pove z besedo "obicajno", ne "ocena".
  // Ziva prevoznikova napoved ima prednost pred nasim modelom -- ne zato, ker
  // bi bila nacelno boljsa, ampak ker je pri mestnem LPP nasa zgodovina
  // zgrajena iz NAPOVEDI: feed poslje samo postanke pred vozilom, zato v
  // `run` meritve nikoli ni. Ziva stevilka pride iz lege vozila ta hip.
  const zivo = zivaNapoved(s);
  const t = !zivo && !f && s.typical ? s.typical : null;
  const d = zivo ? zivo.s : f ? f.predicted_delay_s : t ? t.median_s : null;
  const color = delayColor(d);
  const eta = d != null && schedIso ? hhmm(new Date(new Date(schedIso).getTime() + d * 1000)) : "—";
  const schedHtml = eta !== sched ? `<span class="stop-sched">${sched}</span>` : "";
  // Kadar prevoznik napove VEC od nase ocene, je njegova stevilka merjeno
  // skoraj tocna (MAE 0,21 min proti nasim 2,66) -- takrat ve za nekaj, cesar
  // iz zgodovine ni mogoce vedeti. Povejmo, da stevilka pride od njega.
  const tag = zivo ? (s.eta_min != null ? `LPP v živo · čez ${s.eta_min} min` : "LPP v živo")
    : !f ? (t ? "običajno" : "brez ocene")
    : f.from_operator ? "prevoznik napoveduje več"
    : f.n_samples > 0 ? `ocena · mediana ${pluralRuns(f.n_samples)}`
    : "ocena · le prenos zamude";
  // "ocena - mediana 11 vozenj" je stala v vsaki vrstici naprej po progi:
  // sest enakih zetonov pod seboj, medtem ko locilna vrstica nad njimi ze
  // pove "naprej po progi -- ocena, ne meritev". Stevilo vzorcev je podatek
  // za radovednega, ne za potnika, zato v preprostem pogledu odpade.
  // Ostanejo zetoni, ki povedo nekaj DRUGEGA: da napoveduje prevoznik, da
  // ocene ni ali da za njo ni zgodovine.
  const rutinska = !zivo && !!f && !f.from_operator && f.n_samples > 0;
  const feedSaid = stopDelay(s);
  return `
    <div class="stop-row is-forecast">
      <div class="stop-rail"><span class="stop-dot is-hollow" style="border-color:${color}"></span><span class="stop-line is-dashed"></span></div>
      <div class="stop-main">
        <div class="stop-name">${escapeHtml(s.name)}</div>
        <div class="stop-times"><span class="stop-actual">${eta}</span>${schedHtml} <span class="stop-tag${rutinska ? " adv-only" : ""}">${escapeHtml(tag)}</span></div>
        ${dwellPlanHtml(s)}
        ${feedSaid != null && !zivo && !(f && f.from_operator)
          ? `<div class="stop-times adv-only"><span class="stop-tag">prevoznik napoveduje ${delayLabel(feedSaid)} min</span></div>`
          : ""}
        ${f && f.from_operator ? `<div class="stop-times adv-only"><span class="stop-tag">naša ocena bi bila ${delayLabel(f.own_delay_s)} min</span></div>` : ""}
        ${zivo && f ? `<div class="stop-times adv-only"><span class="stop-tag">naša ocena bi bila ${delayLabel(f.predicted_delay_s)} min</span></div>` : ""}
        ${t ? `<div class="stop-times adv-only"><span class="stop-tag">mediana ${pluralRuns(t.n)}${
          t.od_seq ? `, merjeno na postaji ${escapeHtml(t.od_ime)}` : ""}</span></div>` : ""}
      </div>
      ${stopWeatherHtml(w, true)}
      <div class="stop-delay is-forecast" style="color:${color}">${delayText(d, true)}</div>
    </div>
  `;
}

function runTimelineHtml(stops, forecast, weatherBySeq, opts) {
  // Meja pride s streznikom in jo poda klicatelj (`opts.run`), ker jo pozna
  // samo cel odgovor `/api/train/{no}/run`, ne seznam postankov.
  const cur = lastMeasured((opts && opts.run) || null);
  const forecastBySeq = new Map((forecast || []).map((f) => [f.stop_seq, f]));
  const wx = weatherBySeq || new Map();
  const highlight = (opts && opts.highlight) || null;

  // Preprosti pogled kaze samo, kar je pred potnikom: trenutno lego in naprej.
  // Postaje, ki jih je vozilo ze prevozilo, so odgovor na drugo vprasanje --
  // "kako je bilo" -- in ta sodi v napredni pogled. Kadar je voznja koncana in
  // naprej ni nicesar, pokazemo vse: prazen seznam ne pove nicesar.
  let from = null;
  if (opts && opts.aheadOnly && cur) {
    const zadnji = stops.length ? stops[stops.length - 1].stop_seq : 0;
    if (cur.stop_seq < zadnji) from = cur.stop_seq;
  }
  const shown = from == null ? stops : stops.filter((s) => s.stop_seq >= from);

  // Koliko postaj je vlak ze prevozil, ne pove nicesar, kar bi potnik rabil:
  // seznam se zacne pri vozilu in to je vidno samo po sebi.
  const rows = [];
  let seenAheadHead = false;
  for (const s of shown) {
    const isHi = highlight != null && s.stop_seq === highlight;
    let html;
    if (cur && s.stop_seq <= cur.stop_seq) {
      html = stopActualIso(s) && !jeNeskladen(s)
        ? measuredStopHtml(s, s.stop_seq === cur.stop_seq, wx.get(s.stop_seq))
        : gapStopHtml(s);
    } else {
      if (!seenAheadHead) {
        rows.push('<div class="stop-sep">naprej po progi — ocena, ne meritev</div>');
        seenAheadHead = true;
      }
      html = forecastStopHtml(s, forecastBySeq.get(s.stop_seq), wx.get(s.stop_seq));
    }
    rows.push(isHi ? html.replace('class="stop-row', 'class="stop-row is-yours') : html);
  }
  return `<div class="stop-list">${rows.join("")}</div>`;
}

async function fetchRunAndForecast(trainNo, date, tripId) {
  const enc = encodeURIComponent(trainNo);
  // `trip` je nujen pri avtobusih: stevilka linije ni stevilka voznje.
  const p = new URLSearchParams();
  if (date) p.set("date", date);
  if (tripId) p.set("trip", tripId);
  const q = p.toString() ? `?${p}` : "";
  const res = await fetch(`/api/train/${enc}/run${q}`);
  // Stevilka, ki je ne poznamo, in dan brez meritev nista isto: prvo je
  // zastarela ali polomljena povezava, drugo pravi podatek o pravi vozjni.
  // Prikaz je oboje pisal kot "na ta dan ni podatkov" in s tem trdil, da
  // vozjna obstaja.
  if (!res.ok) {
    const e = new Error(`run ${res.status}`);
    e.status = res.status;
    throw e;
  }
  const run = await res.json();

  const cur = lastMeasured(run);
  // Dokler vlak se ni odpeljal, meritve ni, feed pa ima za prvo postajo ze
  // napoved. Oceno za naprej takrat zgradimo na njej -- ozaljsana je z oznako
  // "ocena", da nihce ne bere napovedi na napovedi kot izmerjeno.
  let base = cur;
  if (!base) {
    for (const s of run.stops) if (stopDelay(s) != null) { base = s; break; }
  }

  let forecast = [];
  const lastSeq = run.stops.length ? run.stops[run.stops.length - 1].stop_seq : 0;
  if (base && stopDelay(base) != null && base.stop_seq < lastSeq) {
    try {
      // Prikazani dan izpustimo iz ucenja -- isto kot pri zgodovini.
      const p = await fetch(
        `/api/train/${enc}/predict?stop_seq=${base.stop_seq}&delay_s=${stopDelay(base)}`
        + `&exclude_date=${encodeURIComponent(run.service_date)}`
        // Brez `trip` se model pri avtobusu uci iz vseh voznj te linije,
        // obeh smeri skupaj. Pri vlaku je isti trip in sprememba nicesar.
        + (run.trip_id ? `&trip=${encodeURIComponent(run.trip_id)}` : "")
      ).then((r) => (r.ok ? r.json() : null));
      forecast = (p && p.forecast) || [];
    } catch (err) {
      console.warn("napovedi ni bilo mogoče naložiti", err);
    }
  }
  return { run, forecast, current: cur };
}

// ---------- ime postaje na dotik ----------

// Postajalisce brez imena je pika, trajen oblacek pa cez pol Ljubljane
// pobrise zemljevid pod sabo. Zato: ime se pokaze ob dotiku in cez pet sekund
// samo odide. Brez gumba za zapiranje -- ta bi bil na telefonu manjsi od
// prsta in bi zahteval drugi, natancnejsi dotik od tistega, ki je ime odprl.
const NAME_MS = 5000;

function bindFlashName(marker, name) {
  marker.bindTooltip(name, {
    className: "kajros-tooltip", direction: "top", offset: [0, -4],
  });
  marker.on("click", (e) => {
    // Brez tega dotik na postajo velja tudi za dotik na zemljevid in ta
    // na telefonu zapre spodnjo plosco.
    if (e.originalEvent) L.DomEvent.stopPropagation(e.originalEvent);
    clearTimeout(marker.__nameT);
    marker.openTooltip();
    marker.__nameT = setTimeout(() => marker.closeTooltip(), NAME_MS);
  });
  return marker;
}

// ---------- starost lege, ki tece sama ----------

// "lega stara 59 s" je stala pri miru, dokler ni prisel naslednji poll, in
// nato skocila nazaj na 38. Starost je edina stevilka na strani, ki se
// spreminja tudi takrat, ko se ne zgodi nic, zato jo mora steti brskalnik:
// strezniska vrednost je izhodisce, mi pa pristevamo cas od trenutka, ko je
// odgovor prispel. Ura odjemalca v racun NE gre -- merimo razliko dveh
// lastnih meritev, zato zamik ure ne skodi.
function ageText(baseS, sinceMs) {
  const s = Math.max(0, Math.round(baseS + (Date.now() - sinceMs) / 1000));
  return s < 100 ? `${s} s` : `${Math.round(s / 60)} min`;
}

// Vrne HTML, ki se osvezuje sam. Iscemo po razredu in ne po registru, ker se
// kartica na zemljevidu gradi iz niza HTML in nanjo ni kam obesiti sklica.
function ageHtml(ageS) {
  const t = Date.now();
  // Naslov namesto opombe: stevilka je videti kot nas zaostanek, pa ni --
  // izmerjeno dodamo mediano 0 s, ostalo je starost, s katero lego dobimo.
  return `<span class="age-live" data-base="${ageS}" data-since="${t}"`
    + ` title="čas od meritve GPS v vozilu; feed nam jo pošlje že okoli pol minute staro">`
    + `${ageText(ageS, t)}</span>`;
}

setInterval(() => {
  // V ozadju ne risemo: sekundnik za sliko, ki je nihce ne gleda, je poraba
  // baterije. Ob vrnitvi je prva vrednost pravilna, ker se racuna, ne steje.
  if (document.visibilityState === "hidden") return;
  for (const el of document.querySelectorAll(".age-live")) {
    el.textContent = ageText(+el.dataset.base, +el.dataset.since);
  }
}, 1000);

// ---------- osvezevanje leg ----------

// Lege beremo **v koraku s strezbo**, ne na slepo. Odgovor nosi glavo
// `X-Osvezi-Cez`: cez koliko sekund bo streznik feed prebral znova. Slep
// ritem je polovico svojega casa cakal na podatek, ki je v bazi ze lezal --
// izmerjeno je bilo to 10 od 45 sekund starosti pike na zaslonu.
//
// Vrne funkcijo za ustavitev. Klic tece, dokler je stran vidna: telefon v
// zepu ne sme spraševati, ker odgovora nihce ne gleda -- to je hkrati
// najcenejsi prihranek na strezniku, kar jih je.
function pollVehicles(url, onData) {
  let timer = null;
  let ustavljen = false;

  async function tick() {
    if (ustavljen) return;
    if (document.visibilityState === "hidden") {
      timer = setTimeout(tick, 5000);   // skrita stran samo caka, ne sprasuje
      return;
    }
    let cez = 10;
    try {
      const r = await fetch(url);
      const h = parseInt(r.headers.get("X-Osvezi-Cez"), 10);
      if (Number.isFinite(h)) cez = h;
      onData(await r.json());
    } catch (err) {
      cez = 30;                         // ob napaki ne tolcemo naprej
      console.warn("leg vozil ni bilo mogoče naložiti", err);
    }
    if (ustavljen) return;
    // Zamik 0-2 s: sto brskalnikov ne sme udariti v isti trenutek. Spodnja
    // meja 3 s velja, kadar streznik zaostaja in glava pade na 1.
    timer = setTimeout(tick, Math.max(3, cez + 1) * 1000 + Math.random() * 2000);
  }

  // Ob vrnitvi na stran vprasaj takoj: prva stvar, ki jo clovek pogleda, je
  // kje je vozilo, in cakati nanjo cel cikel je slabse kot ena zahteva vec.
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && !ustavljen) {
      clearTimeout(timer);
      tick();
    }
  });

  tick();
  return () => { ustavljen = true; clearTimeout(timer); };
}

// ---------- trase voznj ----------
//
// Rabita ju obe strani poti: seznam predlogov in podrobni prikaz.
// Ravna crta med postajama ni proga in bi trdila pot, ki je ni.

// Trase voznj, predpomnjene po vožnji. Statika, ki se med uvozi ne spremeni.
const TRASE = new Map();

function najblizji(tocke, ll) {
  let naj = -1, najd = Infinity;
  for (let i = 0; i < tocke.length; i += 1) {
    const dy = tocke[i][0] - ll[0], dx = (tocke[i][1] - ll[1]) * 0.694;
    const d = dy * dy + dx * dx;
    if (d < najd) { najd = d; naj = i; }
  }
  return naj;
}

async function trasa(n) {
  if (!n.trip_id || !n.od_ll || !n.do_ll) return null;
  if (!TRASE.has(n.trip_id)) {
    TRASE.set(n.trip_id, (async () => {
      const r = await fetch(`/api/trip/${encodeURIComponent(n.trip_id)}/shape`);
      if (!r.ok) return null;
      const deli = (await r.json()).points || [];
      // Trasa je lahko večdelna; za izrez vzamemo najdaljši del.
      return deli.reduce((a, b) => (b.length > a.length ? b : a), []);
    })());
  }
  const del = await TRASE.get(n.trip_id);
  if (!del || del.length < 2) return null;
  const i = najblizji(del, n.od_ll), j = najblizji(del, n.do_ll);
  if (i === j) return null;
  const kos = del.slice(Math.min(i, j), Math.max(i, j) + 1);
  return i <= j ? kos : kos.reverse();
}


// ---------- iskanje po kazalu postaj ----------
//
// Postaje se ne spreminjajo vsak dan, iskanje pa je bilo za `network=vse`
// izmerjeno 1,35 s na razvojnem racunalniku -- torej okoli pet na arwenu, in
// to na VSAK pritisk tipke. Zato se kazalo naloze enkrat in isce se tu.
//
// Razvrscanje mora biti isto kot na strezniku (`journey.search_stations`):
// tocno ime, nato zacetek imena ali besede, nato kjerkoli, znotraj razreda pa
// odloca promet -- kazalo je po njem ze urejeno. Dve razlicici tega bi za isto
// crko dali dva razlicna seznama.

function zacetekBesede(folded, needle) {
  let i = folded.indexOf(needle);
  while (i >= 0) {
    if (i === 0 || folded[i - 1] === " ") return true;
    i = folded.indexOf(needle, i + 1);
  }
  return false;
}

/** `kazalo` so predmeti z zlozenim imenom v `.f`; vrne najvec `limit` zadetkov. */
function iskalnikKazala(kazalo, q, limit = 8) {
  const needle = fold(String(q).trim());
  if (!needle) return [];
  const tocno = [];
  const zacetek = [];
  const kjerkoli = [];
  for (const s of kazalo) {
    if (s.f === needle) tocno.push(s);
    else if (s.f.startsWith(needle)) zacetek.push(s);
    else if (s.f.indexOf(needle) < 0) continue;
    // Zacetek besede je za potnika enako dober zadetek kot zacetek imena --
    // izmerjeno, glej `_razred()` v journey.py. Zato v isto vedro.
    else if (zacetekBesede(s.f, needle)) zacetek.push(s);
    else kjerkoli.push(s);
    if (tocno.length + zacetek.length >= limit && kjerkoli.length >= limit) break;
  }
  return [...tocno, ...zacetek, ...kjerkoli].slice(0, limit);
}

// ---------- moja lega ----------
//
// Prikaz lastne lege je na obeh zemljevidih ista stvar, zato zivi tu.
// Lokacije NE zahtevamo sami ob nalaganju: dovoljenje, ki ga nihce ni prosil,
// je vsiljivo in ga brskalnik ob zavrnitvi pogosto zapomni za vedno. Zahteva
// se sele ob dotiku gumba.
//
// Modra `#2f7fff` ne nastopa v nobeni lestvici -- ne med zamudami (oranzna),
// ne v semaforju razmer, in je dovolj nasicena, da se loci od blede `#a8d8ff`,
// ki pomeni oceno. Modro proti oranzni loci tudi vsaka oblika barvne slepote.
const ME_COLOR = "#2f7fff";

// Deset sekund in `enableHighAccuracy` je bilo premalo. Na telefonu brez
// Googlovih storitev (razgooglana Volla) ni omreznega dolocanja lege -- ostane
// gol GPS, ki iz hladnega stanja rabi desetine sekund, v stavbi pa pogosto
// nikoli. `getCurrentPosition` je zato izteklo in povedalo samo "ni bilo
// mogoce dobiti", kar je za iskanje vzroka neuporabno.
//
// Zato troje: `watchPosition` (prvi fix vzame takoj, ko pride, in ne caka na
// iztek), daljsi rok, in **razlicna sporocila za razlicne vzroke** -- zavrnjeno
// dovoljenje, GPS brez signala in iztek niso ista tezava.
const LEGA_ROK_MS = 25000;
//: Ko je lega natancnejsa od tega, je ni treba izboljsevati. GPS v mestu se
//: ustali okoli 10-30 m; prva groba lega iz baznih postaj zna biti 1-2 km.
const LEGA_DOVOLJ_M = 100;

function locateMe(opts) {
  const { rok = LEGA_ROK_MS, dovolj = LEGA_DOVOLJ_M, napredek } = opts || {};
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      return reject(new Error("Brskalnik ne pozna lokacije."));
    }
    // Brskalniki dovolijo lokacijo samo na HTTPS ali localhostu. Po HTTP na
    // domacem naslovu klic tiho odpove, zato to povemo vnaprej in imenujemo
    // naslov -- sicer clovek isce napako pri sebi.
    if (!window.isSecureContext) {
      return reject(new Error(
        `Lokacija dela samo prek HTTPS; na ${location.host} je brskalnik ne da. `
        + "Odpri kajros.app."));
    }

    let id = null;
    let koncano = false;
    let najboljsa = null;

    const konec = (napaka) => {
      if (koncano) return;
      koncano = true;
      clearTimeout(cas);
      if (id !== null) navigator.geolocation.clearWatch(id);
      if (najboljsa) return resolve(najboljsa);   // groba lega je boljsa od nobene
      reject(napaka || new Error("Lokacije ni bilo mogoče dobiti."));
    };

    const cas = setTimeout(() => konec(new Error(
      `GPS se ni odzval v ${Math.round(rok / 1000)} s. Pod streho pogosto ne `
      + "dobi signala — poskusi zunaj ali izberi kraj na zemljevidu.")), rok);

    id = navigator.geolocation.watchPosition(
      (p) => {
        const l = { lat: p.coords.latitude, lon: p.coords.longitude,
                    acc: p.coords.accuracy };
        if (!najboljsa || l.acc < najboljsa.acc) najboljsa = l;
        if (napredek) napredek(l);
        // Prvi fix je lahko iz bazne postaje in gresi za kilometer; pocakamo
        // na boljsega, dokler je se cas.
        if (l.acc <= dovolj) konec(null);
      },
      (e) => konec(new Error(
        e.code === 1 ? "Dostop do lokacije je zavrnjen — dovoli ga v nastavitvah strani."
        : e.code === 2 ? "Naprava lege ne zna dobiti (GPS ugasnjen ali brez signala)."
        : `GPS se ni odzval v ${Math.round(rok / 1000)} s.`)),
      // `maximumAge: 0`: brez tega brskalnik vrne do minuto star popravek in
      // prvi klik pokaze, kje si bil, ne kje si. Ujeto v zivo.
      { enableHighAccuracy: true, timeout: rok, maximumAge: 0 },
    );
  });
}

/** Neprekinjeno sledenje: `cb(lega)` ob vsakem popravku, vrne ustavitev.
 *
 * Ena lega ob kliku ni dovolj -- GPS prvi popravek pogosto zgresi za sto
 * metrov in ga v naslednjih sekundah popravi, potnik pa se medtem premika.
 */
function sledi(cb) {
  if (!navigator.geolocation || !window.isSecureContext) return () => {};
  const id = navigator.geolocation.watchPosition(
    (p) => cb({ lat: p.coords.latitude, lon: p.coords.longitude,
                acc: p.coords.accuracy }),
    () => {},                       // tiho: gumb "lega" je tisti, ki porocá
    { enableHighAccuracy: true, maximumAge: 0 },
  );
  return () => navigator.geolocation.clearWatch(id);
}

// Pika z obrocem tocnosti. Obroc ni okras: GPS v mestu zna zgresiti za sto
// metrov in pika brez njega trdi natancnost, ki je nima -- ista napaka, kot
// bi bila pika vozila brez "lega stara N s".
function drawMe(group, loc) {
  group.clearLayers();
  if (loc.acc && loc.acc > 25) {
    L.circle([loc.lat, loc.lon], {
      radius: loc.acc, color: ME_COLOR, weight: 1, opacity: 0.35,
      fillColor: ME_COLOR, fillOpacity: 0.1, interactive: false,
    }).addTo(group);
  }
  const pika = L.circleMarker([loc.lat, loc.lon], {
    radius: 6, color: "#ffffff", weight: 2,
    fillColor: ME_COLOR, fillOpacity: 1,
  }).addTo(group);
  bindFlashName(pika, loc.acc ? `tvoja lega (±${Math.round(loc.acc)} m)` : "tvoja lega");
  return pika;
}
