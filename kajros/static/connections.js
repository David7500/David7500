"use strict";

// Vstopna stran vlakov in avtobusov (osnutek E, David 24. 10. 2026). Eno
// vprašanje: Od je postaja, Kam ni obvezen. Brez cilja je odgovor tabla
// odhodov s postaje, s ciljem zveze. Skupne funkcije (barve, čas, vreme) so v
// common.js.

const POLL_MS = 30000;

const $ = (id) => document.getElementById(id);
const resultsEl = $("results");
const resultHeadEl = $("result-head");
const vozovnicaEl = $("vozovnica");
const alertsEl = $("alerts");
const pregledEl = $("pregled");

// Katero omrezje isce ta stran. Vlaki in avtobusi imata SVOJO stran, ker
// potnik ve, s cim gre, in ju ne isce skupaj -- mesanje je bilo tudi merljivo
// skodljivo: iskanje "ljublj" je vracalo mestna postajalisca in postajo
// Ljubljana potisnilo iz prvih petih zadetkov.
const NETWORK = document.body.dataset.network || "zeleznica";
const IS_BUS = NETWORK === "avtobus";
const KRAJ = IS_BUS ? "postajališču" : "postaji";

let pollTimer = null;

// Kaj je na zaslonu: `{kind: "ab", from, to, date}` ali `{kind: "board",
// station, date, dir}`. Zvezdica in skrčena vrstica govorita o tem, ne o
// tem, kar človek ravno tipka v odprt obrazec.
let naZaslonu = null;
// Tabla odhodov ali prihodov in ura začetka pridejo samo iz naslova (deljena
// povezava, shranjena pot). Obrazec ju nima več: tabla je odhodi od zdaj.
let tablaKind = "odhodi";
let tablaOb = "";

// ---------- uro in zamudo vedno skupaj ----------
//
// David 24. 10. 2026 ob osnutku: „ni jasno, kaj je vozni red in kaj zamuda“
// -- „1 min“ in pod njim „+2“ je bila uganka. Zato vsak odhod pove tri
// stvari na istem mestu: čez koliko pelje, ob kateri uri res pelje in kaj
// pravi vozni red (prečrtano, kadar se razlikuje), žeton pa razliko z enoto.

/** „čez 4 min“, „čez 1 h 19 min“, „zdaj“. Dlje od treh ur ni več odgovor. */
function cezBesedilo(ms, zdaj) {
  const min = Math.round((ms - zdaj) / 60000);
  if (min < 0 || min >= 180) return "";
  if (min === 0) return "zdaj";
  if (min < 60) return `čez ${min} min`;
  return `čez ${Math.floor(min / 60)} h${min % 60 ? ` ${min % 60} min` : ""}`;
}

/** Kdo pelje, kot ga pozna potnik: „LPP 6“, „Arriva“, „LPV 2004“. */
function oznakaHtml(row) {
  // Nadomestni prevoz SŽ ni linija mestnega prevoza; vijolična oznaka pove,
  // zakaj na železniški strani stoji avtobus.
  if (isBus(row.mode) && row.network === "zeleznica") {
    return `<span class="oz oz-nad">${SVG_BUS}nadomestni</span>`;
  }
  return `<span class="oz">${escapeHtml(row.network === "avtobus" ? imeVoznje(row) : row.train_no)}</span>`;
}

const SVG_BUS = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><rect x="3.5" y="3.5" width="17" height="15" rx="2.6"/><path d="M3.5 10.5h17M6.5 18.6v2.4M17.5 18.6v2.4"/></svg>';
const SVG_ZGODOVINA = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M3.5 12a8.5 8.5 0 1 0 2.5-6M3.5 4v4h4M12 8v4l3 2"/></svg>';
const SVG_PIN = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/></svg>';
const SVG_DESNO = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>';
const SVG_GOR = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 15l6-6 6 6"/></svg>';
const SVG_ZVEZDICA = '<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z"/></svg>';
const SVG_TI = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="3.4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></svg>';

/** Kako je številka nastala, za obliko žetona -- isto kot postanki v oknu
 *  vožnje: meritev nevtralno, ocena in živa napoved v barvi razreda (živa s
 *  piko), „običajno“ črtkano. */
function vrstaZetona(kind) {
  if (kind === "izmerjeno") return "je-meritev";
  if (kind === "živo" || kind === "v živo") return "je-zivo";
  return "je-ocena";
}

/** Žeton zamude z enoto: „+2 min“, „3 min prej“, „točno“ (`oznake.md`). */
function zetonHtml(z, kind) {
  return `<span class="zt ${vrstaZetona(kind)}" style="--z:${delayColor(z)}">${
    escapeHtml(delayMin(z) === 0 ? "točno" : delayText(z))}</span>`;
}

/** Zgodovina, ne napoved za danes: „običajno +4 min“, črtkano. */
function obicajnoHtml(t) {
  return `<span class="zt je-obicajno" style="--z:${delayColor(t.median_s)}">${SVG_ZGODOVINA}običajno ${
    escapeHtml(delayMin(t.median_s) === 0 ? "točno" : delayText(t.median_s))}</span>`;
}

/** „11:42 vozni red ~~11:45~~“; brez številke ali ob ničli „vozni red 11:45“. */
function uraHtml(schedIso, z) {
  const m = z == null ? 0 : delayMin(z);
  if (!m) return `<span class="ura-vr">vozni red <b>${hhmm(schedIso)}</b></span>`;
  return `<span class="ura-vr"><b>${hhmm(pricakovanaUra(schedIso, z))}</b>vozni red <s>${hhmm(schedIso)}</s></span>`;
}

// "brez podatka" samo za odhode v naslednjih 30 minutah -- dlje naprej
// podatka se ne more biti in beseda je sum (isto kot `pot.BREZ_PODATKA_PRED_S`).
const BREZ_PODATKA_PRED_MS = 30 * 60000;

/** Desni del vrstice z uro: žeton, ki pove razliko ali zakaj je ni. */
function zetonVrsticeHtml(o) {
  if (o.odpovedano) return '<span class="zt je-obvoz">odpovedano</span><span class="zt-op">po podatkih prevoznika</span>';
  if (o.obvoz) return `<span class="zt je-obvoz">obvoz · ${o.obvoz === "do" ? "na cilju ne ustavi" : "tu ne ustavi"}</span>`;
  // Ura je LPP-jeva, ne naša: zamude ni, ker ni voznega reda, od katerega bi
  // jo merili. Beseda pove, kako LPP do ure pride (`lpp.VRSTE`).
  if (o.lpp) return `<span class="zt je-vr">${escapeHtml(o.lpp)}</span><span class="zt-op">po LPP</span>`;
  if (o.zamuda) return zetonHtml(o.zamuda, o.kind);
  // Feed za nadomestni prevoz ne poroca nikoli (56 voženj, 0 meritev):
  // „brez podatka“ bi obljubljal stevilko, ki ne pride.
  if (o.nadomestni) return '<span class="zt je-vr">po voznem redu</span><span class="zt-op">zamud za nadomestni ne dobimo</span>';
  if (o.obicajno) return obicajnoHtml(o.obicajno);
  if (o.nowMs && new Date(o.ura).getTime() - o.nowMs <= BREZ_PODATKA_PRED_MS) {
    return '<span class="zt-op">brez podatka</span>';
  }
  return "";
}

// ---------- samodopolnjevanje postaj ----------

// Deljena med polji: `takeIt()` prestavi fokus na naslednje prazno polje in
// tam se seznam ne sme odpreti sam od sebe.
let preskociFokus = false;

function attachSuggest(input, listEl) {
  let items = [];
  let active = -1;
  let seq = 0;
  let izbrano = null;      // ime, ki smo ga sami vpisali v polje (glej `takeIt`)

  // Izbira postaje NE sprozi iskanja: clovek pogosto popravi se drugo polje,
  // vsak vmesni ugib pa je zahteva na streznik za odgovor, ki ga nihce ni
  // prosil. Iskanje sprozi gumb "Poisci" ali sprememba dneva (`poDnevu`).
  //
  // Kar naredimo, je skok na prazno naslednje polje -- to je klik manj in
  // hkrati pove, da vprasanje se ni celo.
  const takeIt = (name) => {
    input.value = name;
    // **Postavitev `.value` je za telefonsko tipkovnico videti kot tipkanje.**
    // Android tipkovnica na to spremembo odgovori z lastnim `input` dogodkom
    // in seznam se odpre nazaj. Zapomnimo si, kaj smo vpisali; dokler polje
    // pise natanko to, ni kaj dopolnjevati.
    izbrano = name;
    close();
    paintClear(input);
    const next = [...input.form.querySelectorAll(".station-field input")]
      .find((el) => el !== input && !el.value.trim());
    if (next) {
      // Zastavica velja samo za ta klic: `focus()` sprozi dogodek sinhrono.
      preskociFokus = true;
      next.focus();
      preskociFokus = false;
    } else {
      input.blur();
    }
  };

  // Bralnik zaslona mora vedeti, da je polje spustni seznam, ali je odprt in
  // katera moznost je izbrana. Brez tega je tipkovnicna izbira nevidna.
  input.setAttribute("role", "combobox");
  input.setAttribute("aria-autocomplete", "list");
  input.setAttribute("aria-expanded", "false");
  input.setAttribute("aria-controls", listEl.id);

  const close = () => {
    // **`seq += 1` tu ni podrobnost, ampak popravek napake.** Zapoznel odgovor
    // bi seznam odprl nazaj -- cez polje, ki ga clovek medtem ze izpolnjuje.
    seq += 1;
    listEl.hidden = true;
    active = -1;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
  };

  const paint = () => {
    if (!items.length) return close();
    // **Seznam se sme odpreti samo nad poljem, ki ima fokus.**
    if (document.activeElement !== input) return close();
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

    // Iz kazala, ce je ze tu: seznam se mora odpirati sproti, ne cez omrezje.
    const iz = izKazala(q);
    if (iz) {
      seq += 1;
      items = iz;
      active = -1;
      return items.length ? paint() : close();
    }

    const mine = ++seq;
    try {
      const res = await fetch(`/api/stations/search?q=${encodeURIComponent(q)}&limit=8&network=${NETWORK}`)
        .then(jsonOk);
      if (mine !== seq) return;       // prehitelo ga je novejse tipkanje
      items = res;
      active = -1;
      paint();
    } catch (err) {
      close();
    }
  };

  input.addEventListener("input", () => {
    paintClear(input);
    if (izbrano !== null && input.value === izbrano) return;   // odmev nase izbire
    izbrano = null;
    query();
  });
  // Fokus sam po sebi ne odpre nicesar, razen ce clovek v prazno polje tapne
  // sam (`takeIt()` fokus prestavi in seznam se ne sme odpreti brez dotika).
  input.addEventListener("focus", () => {
    if (!input.value.trim() && !preskociFokus) query();
    preskociFokus = false;
  });

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

// ---------- kazalo postaj ----------
//
// Kazalo se nalozi enkrat po strani (zeleznica 7 kB, avtobusi 147 kB) in nato
// tece vse v brskalniku. **Vrstni red je isti kot na strezniku**
// (`iskalnikKazala` v common.js, rabi ga tudi pot).

let KAZALO = null;

function naloziKazaloOmrezja() {
  fetch(`/api/stations/index?network=${NETWORK}`)
    .then((r) => (r.ok ? r.json() : null))
    .then((v) => {
      if (Array.isArray(v)) KAZALO = v.map((s) => ({ name: s.n, f: fold(s.n) }));
    })
    .catch(() => { /* ostane streznik */ });
}

function izKazala(q) {
  return KAZALO ? iskalnikKazala(KAZALO, q) : null;
}

// ---------- brisanje vnosa ----------
// Na telefonu je popravek imena postaje sicer sedem pritiskov vracalke. Gumb
// se pokaze samo, kadar je kaj brisati, in ne jemlje tipkovnicnega vrstnega
// reda (`tabindex="-1"`).

function gumbBrisi(input) {
  return input.closest(".station-field").querySelector(".field-clear");
}

function paintClear(input) {
  const btn = gumbBrisi(input);
  if (btn) btn.hidden = !input.value;
}

function attachClear(input) {
  const btn = gumbBrisi(input);
  if (!btn) return;
  btn.addEventListener("mousedown", (ev) => ev.preventDefault());   // obdrzi fokus
  btn.addEventListener("click", () => {
    input.value = "";
    paintClear(input);
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

// ---------- dan ----------
//
// Danes · Jutri · koledar: jutri je daleč najpogostejši „ne danes“ (vožnja
// zjutraj se načrtuje zvečer) in je zdaj en dotik. Drug dan izbere koledar
// telefona; gumb potem pokaže, kateri dan je izbran.

function jutriIso() {
  const d = new Date(`${todayIso()}T12:00:00`);
  d.setDate(d.getDate() + 1);
  return d.toLocaleDateString("sv-SE");
}

function nastaviDan(iso) {
  const dan = iso || todayIso();
  $("date").value = dan;
  const kaj = dan === todayIso() ? "danes" : dan === jutriIso() ? "jutri" : "drug";
  document.querySelectorAll(".dan-g").forEach((b) => {
    b.setAttribute("aria-pressed", String(b.dataset.dan === kaj));
  });
  document.querySelectorAll(".dan-napis").forEach((el) => {
    el.textContent = kaj === "drug" ? dayLabel(dan) : "";
  });
  document.querySelectorAll('.dan-g[data-dan="drug"]').forEach((b) => {
    b.setAttribute("aria-label", kaj === "drug" ? `izbran dan ${dayLabel(dan)}` : "izberi dan");
  });
}

function danNapis(dan) {
  return dan === todayIso() ? "danes" : dan === jutriIso() ? "jutri" : dayLabel(dan);
}

// Dan sproži iskanje takoj (David, 24. 10. 2026): kdor preklopi na jutri,
// hoče jutrišnji odgovor, ne še dotika na „Poišči“ -- pod skrčeno vrstico
// gumba sploh ni. Brez Od ni kaj iskati; dan se samo izbere.
let danPrej = null;

function poDnevu() {
  if ($("date").value === danPrej) return;
  const from = $("from").value.trim();
  if (!from) return;
  const z = naZaslonu;
  // Ista tabla na drug dan obdrži prihode iz naslova; ura „od“ je veljala
  // za prejšnji dan.
  if (z && z.kind === "board" && !$("to").value.trim() && fold(from) === fold(z.station)) {
    tablaOb = "";
    searchBoard(true);
  } else {
    isci();
  }
}

document.querySelectorAll(".dan").forEach((skupina) => skupina.addEventListener("click", (ev) => {
  const b = ev.target.closest(".dan-g");
  if (!b) return;
  danPrej = $("date").value;
  if (b.dataset.dan === "danes") nastaviDan(todayIso());
  else if (b.dataset.dan === "jutri") nastaviDan(jutriIso());
  else {
    // Polje za datum je eno. Izbirnik se na namizju odpre ob njem, zato gre
    // k gumbu, ki ga odpira; skrito (v skrčenem obrazcu) ga ne odpre.
    const vnos = $("date");
    b.closest(".dan-kol").append(vnos);
    try {
      vnos.showPicker();
    } catch (err) {
      // Brez `showPicker` (starejši brskalniki) vsaj fokus: nekateri ob njem
      // odprejo izbirnik sami.
      vnos.focus();
    }
    return;
  }
  poDnevu();
}));
$("date").addEventListener("change", () => {
  nastaviDan($("date").value);
  poDnevu();
});

// ---------- obvestila o ovirah ----------

function alertsHtml(list, note) {
  if (!list || !list.length) return "";
  const items = list.map((a) => {
    // Pri SZ je naslov cela poved in opis jo ponovi; pri LPP je naslov kratek,
    // tisto, kar potnik rabi, pa je prav v opisu. Zato opis pokazemo, ko
    // pove kaj novega, in ne, ko je naslov ze v njem.
    const naslov = alertTitle(a.header);
    const opis = (a.description || "").trim();
    const nov = opis && !naslov.includes(opis) && !opis.includes(naslov);
    // "neznano" ni podatek, ampak prazno polje s slovensko besedo.
    const meta = [a.effect_label, a.cause_label]
      .filter((x) => x && x !== "neznano").map(escapeHtml).join(" · ");
    // Obvoz LPP je na postajališče, ustavijo pa nekatere linije vseeno
    // (Bavarski dvor 17. 10. 2026: 7, 8, 13, 14 da, 2, 6, 9, 27 ne).
    const linije = a.linije && a.linije.length
      ? `<div class="alert-desc">Ne ustavi: ${a.linije.map((l) => escapeHtml(l)).join(", ")}</div>` : "";
    return `
    <div class="alert-item">
      <strong>${escapeHtml(naslov)}</strong>
      ${nov ? `<div class="alert-desc">${escapeHtml(opis)}</div>` : ""}
      ${linije}
      <div class="alert-meta">
        ${meta}${a.url ? `${meta ? " · " : ""}<a href="${escapeHtml(a.url)}" target="_blank" rel="noopener">obvestilo SŽ</a>` : ""}
      </div>
    </div>`;
  }).join("");
  return `<details class="alert-box"${list.length <= 2 ? " open" : ""}>
    <summary class="alert-head">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
        <path d="M12 9v5M12 17.5v.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"></path>
      </svg>
      ${escapeHtml(note)}
      <span class="alert-count">${list.length} ${sklonOvir(list.length)}</span>
    </summary>
    <div class="alert-list">${items}</div>
  </details>`;
}

function sklonOvir(n) {
  const d = n % 100;
  return d === 1 ? "obvestilo" : d === 2 ? "obvestili" : d === 3 || d === 4 ? "obvestila" : "obvestil";
}

// Vozni red ne sega enako dalec: zeleznica do decembra, IJPP avtobusi vec kot
// leto, mestni LPP pa osem dni. Prazen odgovor cez to mejo ni "ta dan nic ne
// vozi", ampak "voznega reda se ni".
function cezMejo(data) {
  return !!(data.vozni_red_do && data.date > data.vozni_red_do);
}

function mejaHtml(data) {
  if (cezMejo(data)) {
    return `<div class="empty-state">
      Za <strong>${escapeHtml(dayLabel(data.date))}</strong> voznega reda še ni.
      Znan je do <strong>${escapeHtml(dayLabel(data.vozni_red_do))}</strong> —
      objavi ga prevoznik, ne kajros.
    </div>`;
  }
  // Delna vrzel: drzavni vozni red (IJPP) sega leto naprej, LPP-jev lastni pa
  // osem dni. Besedilo govori o VIRU in ne o "mestnih linijah": sicer bi si
  // nasprotovalo z znackami "LPP 25", ki so na zaslonu tik pod njim.
  if (IS_BUS && data.lpp_do && data.date > data.lpp_do) {
    return `<div class="note-partial">Za ta dan manjkajo linije, ki so samo v
      LPP-jevem voznem redu — tega uvažamo osem dni naprej, do
      <strong>${escapeHtml(dayLabel(data.lpp_do))}</strong>.
      Državni vozni red je spodaj.</div>`;
  }
  return "";
}

function renderAlerts(list, note) {
  // Osvezitev na 30 s skatlo izrise znova; kar je clovek odprl ali zaprl,
  // naj tako ostane.
  const prej = alertsEl.querySelector(".alert-box");
  const odprta = prej ? prej.open : null;
  alertsEl.innerHTML = alertsHtml(list, note);
  const box = alertsEl.querySelector(".alert-box");
  if (box && odprta !== null) box.open = odprta;
}

// Povezava na eno vožnjo. `trip` gre zraven, ker številka linije pri
// avtobusih ni številka vožnje -- LPP linija 3G ima 388 voženj. `postaja` je
// postaja, na kateri potnik stoji: okno vožnje jo postavi na vrh.
function journeyHref(trainNo, date, tripId, station) {
  const p = new URLSearchParams();
  if (date) p.set("date", date);
  if (tripId) p.set("trip", tripId);
  if (station) p.set("postaja", station);
  const pot = IS_BUS ? "/app/bus/" : "/app/train/";
  return `${pot}${encodeURIComponent(trainNo)}${p.toString() ? `?${p}` : ""}`;
}

// ---------- zveze ----------

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

/** Ali je to nadomestni prevoz SŽ: `mode = bus`, a `network = zeleznica`. */
function jeNadomestni(r) {
  return isBus(r.mode) && r.network === "zeleznica";
}

// Vožnja je "mimo" šele, ko je minil PRIČAKOVANI odhod, ne voznoredni.
// Vlak, ki zamuja pol ure, je ob voznorednem času še vedno na postaji.
function departedMs(c) {
  return new Date(c.expected_dep || c.sched_dep).getTime();
}

// Kar o vožnji poroča potnik, ki je na njej (`deljenje.py`). Imena postaj v
// imenovalniku, kot povsod.
function potnikiHtml(p, bus, prihod) {
  if (!p) return "";
  const kdo = p.n > 1 ? "potniki na vozilu" : "potnik na vozilu";
  let kaj;
  if (p.odpeljal) kaj = `${prihod ? "prispel" : "odpeljal"} ob ${hhmm(p.odpeljal)}`;
  else if (p.mimo) kaj = "je že mimo";
  else if (p.tu) kaj = `je ${bus ? "na postajališču" : "na postaji"}`;
  else if (p.pricakovano) {
    const k = p.kje || {};
    const kje = k.pri ? `pri ${bus ? "postajališču" : "postaji"} ${k.pri}`
      : k.med ? `med ${bus ? "postajališčema" : "postajama"} ${k.med[0]} in ${k.med[1]}` : "";
    kaj = `${kje ? `${kje}, ` : ""}tu okoli ${hhmm(p.pricakovano)}`;
  } else return "";
  return `<span class="potnik">${kdo}: ${escapeHtml(kaj)}</span>`;
}

// Zgornja meja zamude ob zapori ali vlaku pred njim (`zapore.dodatek`).
// Številka v znački ostane ocena: večina vlakov tam ne izgubi nič.
function doHtml(s) {
  return s != null ? `<span class="zt-do">lahko do ${delayLabel(s)} min</span>` : "";
}

/** Dodatne vrstice pod odhodom: nepotrjen, nadomestni, potnik, zapora. */
function opombeHtml(r, morda, schedIso, prihodi) {
  const deli = [
    morda ? nepotrjenHtml(r.expected_dep || r.expected || schedIso, prihodi) : "",
    nadomestniPostanekHtml(r.nadomestni_postanek),
    potekNadomestnegaHtml(r),
    potnikiHtml(r.potniki, r.network === "avtobus", prihodi),
    opozorilaVrsticeHtml(r.opozorila),
    r.is_terminus ? "<span>konec proge</span>" : "",
  ].filter(Boolean);
  return deli.length ? `<span class="od-op">${deli.join("")}</span>` : "";
}

/** Zveza Od–do kot kartica s trakom (osnutek E3). */
function zvezaHtml(c, nowMs, jeNaslednja, data, prva) {
  const dep = departedMs(c);
  const morda = nepotrjen(dep, c.nepotrjen_do, nowMs);
  const mimo = nowMs && dep < nowMs && !morda;
  const zam = c.zamuda;
  const late = zam && delayMin(zam) !== 0;
  const depIso = late ? pricakovanaUra(c.sched_dep, zam) : c.sched_dep;
  // Pričakovani prihod = voznoredni + ista zamuda, torej prenos, ne meritev.
  const arrIso = late && c.sched_arr ? pricakovanaUra(c.sched_arr, zam) : c.sched_arr;
  const cez = nowMs && !mimo && !morda ? cezBesedilo(dep, nowMs) : "";
  const cilj = ciljVoznje(c.headsign);
  const kam = cilj && fold(cilj) !== fold(data.to) ? `<span class="od-cilj">→ ${escapeHtml(lepoIme(cilj))}</span>` : "";
  const o = {
    zamuda: zam, kind: c.delay_kind, nadomestni: jeNadomestni(c), ura: c.sched_dep, nowMs,
    obicajno: zam ? null : c.typical_arr || c.typical_dep,
    obvoz: c.ne_ustavi,
  };
  // Vozni red vedno z urama: prečrtan, kadar se razlikuje, sicer neprečrtan.
  // Sama beseda „vozni red“ ob žetonu „običajno +6 min“ ni povedala, ali je
  // velika ura voznoredna (David jo je 24. 10. 2026 prebral kot zamaknjeno).
  // Ure iz običajne zamude ne računamo -- zgodovina ni napoved za danes.
  const vr = `<span class="ura-vr">vozni red ${late ? "<s>" : ""}${hhmm(c.sched_dep)} → ${
    hhmm(c.sched_arr)}${late ? "</s>" : ""}</span>`;
  const delez = prva && o.obicajno && !zam
    ? `<span class="zt-op">${Math.round(o.obicajno.on_time_share * 100)} % v 5 min</span>` : "";
  return `
    <a class="zk${jeNaslednja ? " je-naslednja" : ""}${mimo ? " je-mimo" : ""}${morda ? " je-nepotrjen" : ""}${c.ne_ustavi ? " je-obvoz" : ""}"
       href="${journeyHref(c.train_no, data.date, c.trip_id, data.from)}">
      <span class="zk-gl">${oznakaHtml(c)}${kam}${tirHtml(c.tir, c.tir_prej)}<span class="sp"></span>${
        cez ? `<span class="zk-cez">${cez}</span>` : ""}</span>
      <span class="zk-trak"><b>${hhmm(depIso)}</b><span class="zk-crta"><i></i><em>${
        durationLabel(c.duration_s)} · ${stopsLabel(c.stops_between)}</em></span><b>${hhmm(arrIso)}</b></span>
      ${jeNaslednja ? `<span class="zk-imena"><span>${escapeHtml(data.from)}</span><span>${escapeHtml(data.to)}</span></span>` : ""}
      <span class="zk-vr">${vr}${zetonVrsticeHtml(o)}${delez}${doHtml(c.do_s)}</span>
      ${opombeHtml(c, morda, c.sched_dep, false)}
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

// Preostali cas za prestop se racuna iz ZAOKROZENIH minut, ne iz sekund.
// Sicer si tri stevilke na zaslonu nasprotujejo: nacrtovano 52 min, prvi vlak
// +5, preostane pa "48". Tudi DRUGI vlak: streznik racuna
// `wait = nacrtovano + zamuda2 - zamuda1` (`journey.py`).
function preostaliPrestop(tr, plannedS) {
  if (plannedS == null || tr.delay1_s == null) return Math.round(tr.wait_s / 60);
  return Math.round(plannedS / 60)
       - Math.round(tr.delay1_s / 60)
       + Math.round((tr.delay2_s || 0) / 60);
}

// "-1 min za prestop" je uganka, beseda ni (`prestopText()` v common.js --
// isto besedilo rabi pot od vrat do vrat).
function transferBadgeHtml(tr, plannedS) {
  if (!tr) return '<span class="zt je-vr">1 prestop</span>';
  const st = TRANSFER_STYLE[tr.status] || TRANSFER_STYLE["brez podatka"];
  const mins = preostaliPrestop(tr, plannedS);
  return `<span class="zt je-prestop" style="--z:${st.color}">${escapeHtml(st.note)}</span>
    <span class="zt-op">${tr.status === "brez podatka"
      ? `${Math.round(plannedS / 60)} min za prestop`
      : `${prestopText(mins)} · ${escapeHtml(tr.source)}`}</span>`;
}

// Tir pri prestopu: kam vlak pripelje in s katerega odpelje naslednji.
function prestopTiriHtml(prej, nasl) {
  const a = prej.tir_prihod;
  const b = nasl.tir;
  if (!a && !b) return "";
  if (a && b) {
    return `<span class="leg-tiri">${tirHtml(a, prej.tir_prihod_prej)} →${
      tirHtml(b, nasl.tir_prej)}</span>`;
  }
  return `<span class="leg-tiri">${a ? "prihod" : "odhod"}${
    tirHtml(a || b, a ? prej.tir_prihod_prej : nasl.tir_prej)}</span>`;
}

// Zamuda vožnje na prestopni postaji, z imenom vožnje („LPP 6: 1 min prej“).
// Zaokrožena ničla ni novica, zato je ni.
function prestopZamudaHtml(voznja, s) {
  if (!delayMin(s)) return "";
  return `<span class="leg-note">${escapeHtml(imeVoznje(voznja))}: ${delayText(s)}</span>`;
}

/** Zveza s prestopom: ista kartica, trak od prvega odhoda do prihoda,
 *  pod njim noge. */
function prestopHtml(t, nowMs, data) {
  const tr = t.transfer;
  const st = TRANSFER_STYLE[(tr && tr.status) || "brez podatka"];
  const planned = Math.round(t.wait_s / 60);
  // Pot ima lahko dve nogi (en prestop) ali stiri (trije prestopi).
  const count = t.transfers != null ? t.transfers : t.legs.length - 1;
  const legs = t.legs.map((l, i) => {
    const next = t.legs[i + 1];
    const wait = next ? Math.round((next.dep_s - l.arr_s) / 60) : null;
    return `
      <span class="leg">
        <span class="leg-time">${hhmm(l.dep)}–${hhmm(l.arr)}</span>
        <span class="leg-train">${escapeHtml(imeVoznje(l))}</span>
        <span class="leg-where">${escapeHtml(lepoIme(l.from))} → ${escapeHtml(lepoIme(l.to))}</span>
      </span>
      ${l.nadomestni_postanek ? `<span class="leg">${nadomestniPostanekHtml(l.nadomestni_postanek)}</span>` : ""}
      ${next ? `<span class="leg is-prestop">
          <span class="leg-wait" style="color:${count === 1 ? st.color : "var(--sev-hard)"}">
            prestop na ${KRAJ} ${escapeHtml(lepoIme(l.to))} · ${wait} min
          </span>
          ${prestopTiriHtml(l, next)}
          ${count === 1 && tr ? prestopZamudaHtml(l, tr.delay1_s) : ""}
          ${count === 1 && tr ? prestopZamudaHtml(next, tr.delay2_s) : ""}
        </span>` : ""}`;
  }).join("");
  // Pri enem prestopu znamo povedati, ali zveza drzi. Pri vec prestopih tega
  // ne racunamo in zato ne trdimo -- pise samo, koliko jih je.
  const badge = count === 1
    ? transferBadgeHtml(tr, t.wait_s)
    : `<span class="zt je-vr">${count} ${count === 2 ? "prestopa" : count === 3 || count === 4 ? "prestopi" : "prestopov"}</span>
       <span class="zt-op">najkrajše čakanje ${planned} min</span>`;
  const cez = nowMs ? cezBesedilo(new Date(t.sched_dep).getTime(), nowMs) : "";
  return `
    <a class="zk je-prestop" href="${journeyHref(t.train1, data.date, t.trip1, data.from)}">
      <span class="zk-gl"><span class="zk-noge">${t.legs.map((l) => oznakaHtml(l)).join('<span class="zk-pus">›</span>')}</span>${
        tirHtml(t.legs[0].tir, t.legs[0].tir_prej)}<span class="sp"></span>${cez ? `<span class="zk-cez">${cez}</span>` : ""}</span>
      <span class="zk-trak"><b>${hhmm(t.sched_dep)}</b><span class="zk-crta"><i></i><em>prek ${
        escapeHtml(lepoIme(t.via))} · ${durationLabel(t.duration_s)}</em></span><b>${hhmm(t.sched_arr)}</b></span>
      <span class="zk-vr"><span class="ura-vr">vozni red ${hhmm(t.sched_dep)} → ${hhmm(t.sched_arr)}</span>${badge}</span>
      <span class="legs">${legs}</span>
    </a>`;
}

/** Neposredne vožnje ni, s postajališča čez cesto pa je (`journey.blizu_z_zvezo`):
 *  Konzorcij vozi samo proti jugu, Pošta 60 m stran do Bavarskega dvora. Ali
 *  pa vožnja pelje mimo cilja, do postajališča ob njem. Imen ne sklanjamo --
 *  „s postajališča Pošta“, ne „s Pošte“. */
function blizuHtml(data) {
  const b = data.blizu;
  if (!b) return "";
  const kraj = IS_BUS ? "postajališča" : "postaje";
  const Kraj = IS_BUS ? "Postajališče" : "Postaja";
  const ime = `<b>${escapeHtml(b.ime)}</b>`;
  const kje = razdaljaBesedilo(b.metrov);
  const [besedilo, gumb] = b.kje === "do"
    ? [`Do cilja ni neposredne vožnje. ${Kraj} ${ime} je ${kje} od cilja in tja pelje.`,
       `Zveze do ${kraj} ${escapeHtml(b.ime)}`]
    : [`Od tu do cilja ni neposredne vožnje. ${Kraj} ${ime} je ${kje} stran in od tam pelje.`,
       `Zveze s ${kraj} ${escapeHtml(b.ime)}`];
  return `<div class="blizu">
      <p>${besedilo}</p>
      <button type="button" class="blizu-g" data-ime="${escapeHtml(b.ime)}" data-kje="${b.kje}">${SVG_DESNO}${gumb}</button>
    </div>`;
}

function renderConnections(data) {
  const list = data.connections || [];
  const legs = data.transfers || [];
  const isToday = data.date === todayIso();
  const nowMs = isToday ? Date.now() : 0;

  resultHeadEl.textContent = `${data.from} → ${data.to}, ${danNapis(data.date)}: ${list.length} ${
    list.length === 1 ? "neposredna vožnja" : "neposrednih"}${legs.length ? `, ${legs.length} s prestopom` : ""}`;

  // Vozovnica pod rezultatom, ne nad njim: potnik najprej hoce vedeti, ali
  // sploh kaj pelje. Samo pri vlakih, ker avtobusne vozovnice SZ ne prodaja.
  vozovnicaEl.innerHTML = IS_BUS ? "" : ticketLinkHtml();

  if (!list.length && !legs.length) {
    if (cezMejo(data)) {
      resultsEl.innerHTML = mejaHtml(data);
      renderAlerts(data.alerts, "Ovire na tej poti");
      return;
    }
    // Strežnik ob praznem izidu išče do treh prestopov (`journey.plan`). Pot
    // od vrat do vrat pa šteje še hojo do drugega postajališča in obe omrežji.
    const kraja = IS_BUS ? "postajališča" : "postaje";
    const vikend = [0, 6].includes(new Date(`${data.date}T12:00:00`).getDay());
    const lega = data.lega || {};
    const pot = lega.od && lega.do
      ? `<a href="/app/pot?od=${lega.od.join(",")}&do=${lega.do.join(",")}">Poišči pot od vrat do vrat</a> — šteje tudi hojo in ${IS_BUS ? "vlake" : "avtobuse"}.`
      : "";
    resultsEl.innerHTML = blizuHtml(data) + `<div class="empty-state">
      Na ta dan ni vožnje od ${kraja} <strong>${escapeHtml(data.from)}</strong>
      do ${kraja} <strong>${escapeHtml(data.to)}</strong> — ne neposredne
      ne s prestopi.<br>
      ${pot} Preveri tudi drug dan${vikend
        ? ` — ${IS_BUS ? "ob koncu tedna vozi manj avtobusov" : "ob koncu tedna vozi bistveno manj vlakov"}`
        : ""}.
    </div>`;
    renderAlerts(data.alerts, "Ovire na tej poti");
    return;
  }

  // Naslednja vozjna je prva, ki se ni odpeljala -- obarvana, sicer enaka
  // ostalim (David 24. 10. 2026: prva ne sme biti „tako drugačna“).
  let nextIdx = -1;
  if (isToday) nextIdx = list.findIndex((c) => departedMs(c) >= nowMs && !c.ne_ustavi);

  // Ze odpeljane vozjne so kontekst, ne izbira. Ostanejo dosegljive -- kdor
  // preverja, ali je zamudil vlak, jih rabi. Nepotrjen odhod ni odpeljan.
  const pred = nextIdx > 0 ? list.slice(0, nextIdx) : nextIdx < 0 && isToday ? list : [];
  const jeMorda = (c) => nepotrjen(departedMs(c), c.nepotrjen_do, nowMs);
  const gone = pred.filter((c) => !jeMorda(c));
  const morda = pred.filter(jeMorda);
  const ahead = nextIdx >= 0 ? list.slice(nextIdx) : isToday ? [] : list;

  const vrstica = (c, naslednja) => zvezaHtml(c, nowMs, naslednja, data, naslednja);
  const prejsnji = gone.map((c) => vrstica(c, false));
  const neposredne = [
    ...morda.map((c) => vrstica(c, false)),
    ...ahead.map((c, i) => vrstica(c, i === 0 && nextIdx >= 0)),
  ];

  // **Prestop gre nad neposredne, kadar prej pripelje.** 25. 9. 2026 je
  // iskalnik Ljubljana -> Maribor na vrhu poudaril LPV 2002 s prihodom ob
  // 23:26, zveza s prestopom pa je pripeljala ob 20:34. Samo danes.
  // Primerja se absolutna pričakovana ura, ne `arr_s` (po polnoči dve polnoči).
  const naslednja = nextIdx >= 0 ? ahead[0] : null;
  const prihodMs = (c) => new Date(c.sched_arr).getTime() + (c.delay_s || 0) * 1000;
  const prihodPrestopaMs = (t) => new Date(t.sched_arr).getTime()
    + ((t.transfer && t.transfer.delay2_s) || 0) * 1000;
  const prestopPrej = isToday && legs.length > 0 && list.length > 0
    && (!naslednja || Math.min(...legs.map(prihodPrestopaMs)) < prihodMs(naslednja));
  const prestopi = [];
  if (legs.length) {
    const most = Math.max(...legs.map((t) => t.transfers || t.legs.length - 1));
    prestopi.push(`<h2 class="isk-naslov">${most === 1
      ? `Z enim prestopom${prestopPrej ? " — prej na cilju" : ""}`
      : "S prestopi — neposredne vožnje ni"}</h2>`);
    prestopi.push(...legs.map((t) => prestopHtml(t, nowMs, data)));
  }
  const rows = prestopPrej
    ? [...prestopi, '<h2 class="isk-naslov">Neposredno</h2>', ...neposredne]
    : [...neposredne, ...prestopi];
  resultsEl.innerHTML = mejaHtml(data) + blizuHtml(data) + kontroleHtml(prejsnji.length, "")
    + prejsnjiSeznamHtml(prejsnji, "zk-seznam") + `<div class="zk-seznam">${rows.join("")}</div>`;
  obnoviMesto();

  renderAlerts(data.alerts, "Ovire na tej poti");
}

// Že odpeljane: dosegljive, a ne pred odgovorom -- kdor preverja, ali je
// zamudil vlak, jih rabi. Gumb stoji v vrstici z razvrstitvijo, seznam pod
// njo, zato ni <details>. Osvezitev na 30 s seznam izrise znova; odprt ostane
// odprt, novo iskanje ga zapre.
let prejsnjiOdprti = false;

function kontroleHtml(n, desno) {
  if (!n && !desno) return "";
  const beseda = n === 1 ? "prejšnji" : n === 2 ? "prejšnja" : n === 3 || n === 4 ? "prejšnji" : "prejšnjih";
  return `<div class="od-kontrole">${n ? `<button type="button" class="past-head" data-prejsnji
      aria-expanded="${prejsnjiOdprti}">${SVG_GOR}${n} ${beseda}</button>` : ""}<span class="sp"></span>${desno}</div>`;
}

function prejsnjiSeznamHtml(vrstice, razred) {
  if (!vrstice.length) return "";
  return `<div class="past-list ${razred}"${prejsnjiOdprti ? "" : " hidden"}>${vrstice.join("")}</div>`;
}

// ---------- tabla ----------

/** Ena vrstica table (osnutek E5): kdo in kam, čez koliko, ura z voznim
 *  redom in žeton. */
function odhodHtml(r, nowMs, isNext, date, station, prihodi) {
  const exp = new Date(r.expected || r.sched).getTime();
  const morda = nepotrjen(exp, r.nepotrjen_do, nowMs);
  const gone = nowMs && exp < nowMs && !morda;
  // Vrstica z LPP-jevega zaslona nima vožnje: tiste, ki ji pripada, v voznem
  // redu ni, povezava na katero koli drugo pa bi odprla napačno.
  const tag = r.trip_id ? "a" : "div";
  // Po obvozu LPP vožnja tu ne ustavi (`api._oznaci_obvoze`), odpovedana ne
  // vozi (`collector.odpovedane`): vrstica ostane, da potnik ve, kam je šel
  // njegov avtobus, a ni odhod -- brez odštevanja, prečrtana.
  const obvoz = !!r.ne_ustavi || !!r.odpovedano;
  const cez = nowMs && !gone && !morda && !obvoz ? cezBesedilo(exp, nowMs) : "";
  const o = {
    zamuda: r.zamuda, kind: r.delay_kind, nadomestni: jeNadomestni(r), ura: r.sched, nowMs,
    obicajno: r.zamuda ? null : r.typical, obvoz: r.ne_ustavi ? "tu" : null,
    odpovedano: r.odpovedano, lpp: r.lpp_vrsta,
  };
  return `
    <${tag} class="od${isNext ? " je-naslednja" : ""}${gone ? " je-mimo" : ""}${morda ? " je-nepotrjen" : ""}${obvoz ? " je-obvoz" : ""}"
       ${r.trip_id ? `href="${journeyHref(r.train_no, r.service_date || date, r.trip_id, station)}"` : ""}>
      <span class="od-gl">${oznakaHtml(r)}<span class="od-cilj">${escapeHtml(lepoIme(r.towards))}</span>${
        tirHtml(r.tir, r.tir_prej)}<span class="sp"></span>${cez ? `<span class="od-cez">${cezHtml(cez)}</span>` : ""}</span>
      <span class="od-ura">${r.lpp_vrsta ? `<span class="ura-vr"><b>${hhmm(r.expected || r.sched)}</b></span>` : uraHtml(r.sched, r.zamuda)}<span class="sp"></span>${
        zetonVrsticeHtml(o)}${doHtml(r.do_s)}</span>
      ${opombeHtml(r, morda && !obvoz, r.sched, prihodi)}
    </${tag}>`;
}

/** „čez 4 min“ z drobnim „čez“: številka nosi odgovor. */
function cezHtml(besedilo) {
  if (!besedilo.startsWith("čez ")) return escapeHtml(besedilo);
  return `<small>čez</small>${escapeHtml(besedilo.slice(4)).replace(/ min$/, "<small> min</small>")}`;
}

/** Tabla po linijah (osnutek E4): ena vrstica na linijo in smer, naslednji
 *  odhod z uro in žetonom, nato še dva. Linije po prvem odhodu, zato je na
 *  vrhu še vedno tisti, ki pelje prvi. Bavarski dvor ima 53 odhodov v pol
 *  ure; kdor čaka svojo linijo, jo tu najde v eni vrstici. */
function linijeHtml(ahead, nowMs, date, station, prihodi) {
  // Obvoz in odpoved sta svoja vrstica: potnik mora videti, kam je šel
  // njegov avtobus, „nato čez“ pa sme šteti samo odhode, ki tu ustavijo.
  const skupine = new Map();
  for (const r of ahead) {
    const stanje = r.odpovedano ? "odpovedano" : r.ne_ustavi ? "obvoz" : "";
    const k = `${oznakaVoznjeBesedilo(r)}|${r.towards}|${r.smer || ""}|${stanje}`;
    if (!skupine.has(k)) skupine.set(k, []);
    skupine.get(k).push(r);
  }
  const vrste = [...skupine.values()];
  const naslednja = vrste.findIndex((s) => !s[0].ne_ustavi && !s[0].odpovedano);
  return vrste.map((s, i) => {
    const prvi = s[0];
    const nato = s.slice(1, 3).map((r) => {
      const ms = new Date(r.expected || r.sched).getTime();
      const c = nowMs ? cezBesedilo(ms, nowMs) : "";
      return c ? c.replace(/^čez /, "") : hhmm(r.expected || r.sched);
    });
    const vrstica = odhodHtml(prvi, nowMs, nowMs && i === naslednja, date, station, prihodi);
    if (!nato.length || prvi.ne_ustavi || prvi.odpovedano) return vrstica;
    const napis = `nato ${nowMs ? "čez " : "ob "}${nato.join(" in ")}`;
    return vrstica.replace(/\s*<\/(a|div)>$/, `<span class="od-nato">${escapeHtml(napis)}</span></$1>`);
  }).join("");
}

function oznakaVoznjeBesedilo(r) {
  return jeNadomestni(r) ? "nadomestni" : r.network === "avtobus" ? imeVoznje(r) : r.train_no;
}

// Zakaj so odhodi neke linije drugačni od ostalih: LPP jo danes vozi mimo
// objavljenega voznega reda (zapora), zato so ure z njegovega zaslona. Ali pa
// zamud mestnega LPP ne dobivamo (`lpp_izpad`) in so ure z zaslona za vse.
function mimoHtml(data) {
  const l = data.mimo_voznega_reda || [];
  if (!l.length) return "";
  if (data.lpp_izpad) {
    return `<div class="note-partial">Zamud mestnih avtobusov LPP ta hip ne dobivamo.
      Prihode kažemo, kot jih napove LPP.</div>`;
  }
  const imena = l.length === 1 ? l[0] : `${l.slice(0, -1).join(", ")} in ${l[l.length - 1]}`;
  const [kdo, glagol] = l.length === 1 ? ["Linija", "ne vozi"]
    : l.length === 2 ? ["Liniji", "ne vozita"] : ["Linije", "ne vozijo"];
  return `<div class="note-partial">${kdo} <strong>${escapeHtml(imena)}</strong>
    danes ${glagol} po voznem redu. Prihode kažemo, kot jih napove LPP.</div>`;
}

// ---------- smer na postajaliscu ----------
//
// Mestno postajalisce je dvoje -- ena stran ceste za vsako smer -- in tabla je
// kazala obe skupaj: na Bavarskem dvoru 53 odhodov v pol ure, polovico z
// druge strani ceste. Strani izracuna streznik (`journey.smeri_postaje`) po
// smeri voznje do naslednjega postanka; tu se samo izbere.
//
// **Filtrira streznik, ne brskalnik** (meja 150 vrstic). Da je preklop vseeno
// takojsen, se iz cele table izbrana stran pokaze takoj, nato pride prava.
// Izbira se zapomni **po postajaliscu** (`smerIzSpomina` v common.js); kljuc,
// ki ga streznik ne pozna vec, se tiho pozabi.

let zadnjaTabla = null;
let izbranaSmer = null;       // kljuc smeri ali null = obe
let smerIzNaslova = null;     // deljena povezava prevlada nad spominom, a le enkrat
let smerIzSpominaPo = false;  // pravo ime pove sele odgovor
let tablaZa = null;           // vnos, za katerega velja `izbranaSmer`
// Zaporedna stevilka zahteve. Osvezitev, ki je bila na poti, ko je clovek
// izbral drugo smer, ne sme njegove izbire povoziti s staro tablo.
let tablaSt = 0;
let zvezeSt = 0;   // isto za zveze: velja samo odgovor zadnje zahteve

function smerVSpomin(postaja, kljuc) {
  try {
    const vse = JSON.parse(localStorage.getItem(SMER_KLJUC) || "{}") || {};
    if (kljuc) vse[postaja] = kljuc;
    else delete vse[postaja];
    localStorage.setItem(SMER_KLJUC, JSON.stringify(vse));
  } catch (e) { /* poln ali zavrnjen localStorage izbire ne podre */ }
}

/** „→ Tobačna“ ali „→ Vič Glince · Jadranska“. Imen se ne sklanja. */
function smerNapis(d) {
  return `→ ${(d.naslednje || []).join(" · ") || "končna"}`;
}

// Mestni LPP doda „v center“ / „iz centra“, kot ju pove LPP-jeva koda
// postajališča (`journey.smeri_postaje`): tako so smer navajeni brati.
function smeriHtml(data) {
  const smeri = data.smeri || [];
  if (smeri.length < 2) return "";
  const gumb = (kljuc, napis, center, obe) => `<button type="button" class="smer-chip${obe ? " je-obe" : ""}"
      data-smer="${escapeHtml(kljuc || "")}" aria-pressed="${String((izbranaSmer || "") === (kljuc || ""))}"
      ><span class="smer-ime">${escapeHtml(napis)}</span>${center ? `<span class="smer-center">${escapeHtml(center)}</span>` : ""}</button>`;
  return `<div class="smeri" role="group" aria-label="Stran ceste, po naslednji postaji">
      ${gumb(null, "Obe", null, true)}
      ${smeri.map((d) => gumb(d.kljuc, smerNapis(d), d.center)).join("")}
    </div>`;
}

function izberiSmer(kljuc) {
  izbranaSmer = kljuc || null;
  if (!zadnjaTabla) return;
  smerVSpomin(zadnjaTabla.station, izbranaSmer);
  const q = new URLSearchParams(location.search);
  if (izbranaSmer) q.set("smer", izbranaSmer);
  else q.delete("smer");
  history.replaceState(null, "", `?${q}`);
  zapomniIskanje(NETWORK);
  // Iz cele table se izbrana stran da pokazati takoj. Iz ze filtrirane ne --
  // druge strani v njej ni, in "v tej smeri ni odhodov" bi bila laz za pol
  // sekunde.
  const takoj = !zadnjaTabla.smer;
  if (takoj) renderBoard(zadnjaTabla);
  searchBoard(false, takoj);
}

// Tabla po vrsti ali po linijah (osnutek E4/E5). Privzeto po vrsti -- tako
// tabla dela od začetka; kdor čaka svojo linijo, enkrat preklopi in tako
// ostane (`kajros:tabla-razvrstitev`). Pri vlakih po linijah nima smisla:
// vsak vlak ima svojo številko.
const RAZVRSTITEV_KLJUC = "kajros:tabla-razvrstitev";
let poLinijah = (() => {
  try {
    return IS_BUS && localStorage.getItem(RAZVRSTITEV_KLJUC) === "linije";
  } catch (e) {
    return false;
  }
})();

function razvrstitevHtml(n) {
  if (!IS_BUS || n < 2) return "";
  const g = (kaj, napis) => `<button type="button" class="razv-g" data-razvrstitev="${kaj}"
      aria-pressed="${String((kaj === "linije") === poLinijah)}">${napis}</button>`;
  return `<div class="razv" role="group" aria-label="Razvrstitev odhodov">${g("linije", "po linijah")}${g("vrsti", "po vrsti")}</div>`;
}

resultsEl.addEventListener("click", (ev) => {
  const blizu = ev.target.closest(".blizu-g");
  if (blizu) {
    $(blizu.dataset.kje === "do" ? "to" : "from").value = blizu.dataset.ime;
    paintAllClears();
    searchAB(true);
    return;
  }
  const p = ev.target.closest("[data-prejsnji]");
  if (p) {
    prejsnjiOdprti = !prejsnjiOdprti;
    p.setAttribute("aria-expanded", String(prejsnjiOdprti));
    const l = resultsEl.querySelector(".past-list");
    if (l) l.hidden = !prejsnjiOdprti;
    return;
  }
  const b = ev.target.closest(".smer-chip, .smer-vse");
  if (b) {
    izberiSmer(b.dataset.smer);
    return;
  }
  const r = ev.target.closest("[data-razvrstitev]");
  if (r) {
    poLinijah = r.dataset.razvrstitev === "linije";
    try {
      localStorage.setItem(RAZVRSTITEV_KLJUC, poLinijah ? "linije" : "vrsti");
    } catch (e) { /* izbira velja vsaj za ta ogled */ }
    if (zadnjaTabla) renderBoard(zadnjaTabla);
  }
});

function renderBoard(data) {
  zadnjaTabla = data;
  const smeri = data.smeri || [];
  // Streznik kljuca ne pozna vec (nov vozni red): tabla je cela, izbira gre.
  if (izbranaSmer && !smeri.some((d) => d.kljuc === izbranaSmer)) {
    smerVSpomin(data.station, null);
    izbranaSmer = null;
  }
  const vse = data.board || [];
  const list = izbranaSmer ? vse.filter((r) => r.smer === izbranaSmer) : vse;
  const isToday = data.date === todayIso();
  const nowMs = isToday ? Date.now() : 0;
  const prihodi = data.kind === "prihodi";

  resultHeadEl.textContent = `${data.station}, ${data.kind} ${danNapis(data.date)}: ${list.length} ${sklon(list.length, data.kind)}`;

  if (!list.length && vse.length) {
    // Druga stran ceste ima odhode, ta ne: to je druga novica kot "od tu nic
    // ne pelje" in ima drugo dejanje.
    resultsEl.innerHTML = mejaHtml(data) + smeriHtml(data) + `<div class="empty-state">
      Na tej strani ceste v tem oknu ni ${escapeHtml(sklon(0, data.kind))}.
      <div class="empty-act">
        <button type="button" class="btn btn-quiet smer-vse" data-smer="">pokaži obe strani</button>
      </div>
    </div>`;
    renderAlerts(data.alerts, `Ovire — ${data.station}`);
    return;
  }

  if (!list.length) {
    // "Poskusi drugo uro" je nasvet, ne dejanje -- ponoci je odgovor vedno
    // isti: jutri zjutraj. Gumb ga opravi.
    const jutri = new Date(data.date + "T12:00:00");
    jutri.setDate(jutri.getDate() + 1);
    const jutriD = jutri.toISOString().slice(0, 10);
    if (cezMejo(data)) {
      resultsEl.innerHTML = mejaHtml(data);
      renderAlerts(data.alerts, `Ovire — ${data.station}`);
      return;
    }
    resultsEl.innerHTML = `<div class="empty-state">
      V tem oknu ${IS_BUS ? "s postajališča" : "s postaje"} <strong>${escapeHtml(data.station)}</strong>
      ni ${escapeHtml(sklon(0, data.kind))}.
      <div class="empty-act">
        <button type="button" class="btn btn-quiet" id="board-tomorrow"
                data-date="${jutriD}">pokaži ${dayLabel(jutriD)} od 05:00</button>
      </div>
    </div>`;
    const gumb = $("board-tomorrow");
    if (gumb) gumb.addEventListener("click", () => {
      nastaviDan(gumb.dataset.date);
      tablaOb = "05:00";
      searchBoard(true);
    });
    alertsEl.innerHTML = "";
    return;
  }

  const vrstica = (r, isNext) => odhodHtml(r, nowMs, isNext, data.date, data.station, prihodi);
  const glava = mejaHtml(data) + mimoHtml(data) + smeriHtml(data);
  if (!isToday) {
    // Drug dan nima "zdaj": vozni red po vrsti, brez poudarka.
    resultsEl.innerHTML = glava + kontroleHtml(0, razvrstitevHtml(list.length))
      + `<div class="od-seznam">${poLinijah ? linijeHtml(list, 0, data.date, data.station, prihodi)
        : list.map((r) => vrstica(r, false)).join("")}</div>`;
    renderAlerts(data.alerts, `Ovire — ${data.station}`);
    return;
  }

  // **Danes je tabla po pricakovani uri, ne po voznem redu** (`razvrstiTablo`
  // v common.js). Poudarek "naslednja" je 25. 9. 2026 dobil LPP 14 z +49 min,
  // ceprav je LPP 13 peljal cez dve minuti.
  const { gone, morda, ahead } = razvrstiTablo(list, nowMs);
  // Poudarek „naslednja“ dobi prva, ki tu res ustavi.
  const prva = ahead.findIndex((r) => !r.ne_ustavi && !r.odpovedano);
  const prejsnji = gone.map((r) => vrstica(r, false));
  const naprej = poLinijah
    ? linijeHtml(ahead, nowMs, data.date, data.station, prihodi)
    : ahead.map((r, i) => vrstica(r, i === prva)).join("");
  resultsEl.innerHTML = glava + kontroleHtml(prejsnji.length, razvrstitevHtml(ahead.length))
    + prejsnjiSeznamHtml(prejsnji, "od-seznam")
    + `<div class="od-seznam">${morda.map((r) => vrstica(r, false)).join("")}${naprej}</div>`;
  renderAlerts(data.alerts, `Ovire — ${data.station}`);
  obnoviMesto();
}

// ---------- mesto na seznamu ob vrnitvi ----------
//
// Brez predpomnilnika strani (bfcache) -- aplikacija za Android, WebView -- se
// je vrnitev iz okna vožnje končala na vrhu seznama, z zaprtimi prejšnjimi
// (presoja 18. 10. 2026: 1 304 px → 0). Mesto gre zato v sessionStorage ob
// odhodu in se postavi po prvem izrisu, samo ob vrnitvi na isto vprašanje.
const MESTO_KLJUC = `kajros:iskalnik-mesto:${NETWORK}`;
let mesto = (() => {
  try {
    const nav = performance.getEntriesByType("navigation")[0];
    if (!nav || nav.type !== "back_forward") return null;
    const m = JSON.parse(sessionStorage.getItem(MESTO_KLJUC));
    return m && m.q === location.search ? m : null;
  } catch (e) {
    return null;
  }
})();
if (mesto) history.scrollRestoration = "manual";

function obnoviMesto() {
  if (!mesto) return;
  const y = mesto.y;
  mesto = null;
  requestAnimationFrame(() => window.scrollTo(0, y));
}

addEventListener("pagehide", () => {
  try {
    sessionStorage.setItem(MESTO_KLJUC, JSON.stringify({
      q: location.search, y: window.scrollY,
      odprto: prejsnjiOdprti,
    }));
  } catch (e) { /* zasebno okno: brez obnove mesta */ }
});

// ---------- vstopni pregled ----------
//
// Pogoste poti samo, dokler človek nima svojih; pri vlakih še povezava na
// ovire. Do 29. 9. 2026 je bila tu še kartica z mediano končne zamude dneva
// (ob 00:03 „avtobusi +839 min“) -- tudi pravilna številka potniku ne pove,
// kdaj mu pelje.
//
// Avtobusni pari NISO ugibani: to je sest najpogostejsih relacij po stevilu
// voznj v zajetem voznem redu (izmerjeno 4. 9. 2026). Preverjeno je tudi, da
// se vsa imena razresijo z `resolve_station`.
const POPULAR_RAIL = [
  ["Ljubljana", "Maribor"],
  ["Ljubljana", "Koper"],
  ["Ljubljana", "Jesenice"],
  ["Ljubljana", "Novo mesto"],
  ["Maribor", "Murska Sobota"],
  ["Celje", "Ljubljana"],
];

const POPULAR_BUS = [
  ["Ljubljana AP", "Kamnik"],
  ["Ljubljana AP", "Škofja Loka"],
  ["Ljubljana AP", "Kranj AP"],
  ["Ljubljana AP", "Vrhnika Voljčeva"],
  ["Grosuplje", "Ljubljana Železna"],
  ["Kamnik", "Ljubljana AP"],
];

const POPULAR = IS_BUS ? POPULAR_BUS : POPULAR_RAIL;

function popularChipsHtml() {
  return `<h2 class="isk-naslov">Pogosto</h2><div class="chips">
      ${POPULAR.map(([a, b]) => `<button type="button" class="route-chip"
          data-from="${escapeHtml(a)}" data-to="${escapeHtml(b)}">${escapeHtml(a)} → ${escapeHtml(b)}</button>`).join("")}
    </div>`;
}

/** Povezava na ovire; samo železnica, avtobusnih ovir ne zajemamo. */
function ovireHtml(n) {
  return `<a class="ov-link" href="/app/ovire">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
          <path d="M12 9v5M12 17.5v.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"></path>
        </svg>
        <span>${n} ${n === 1 ? "veljavno obvestilo" : "veljavnih obvestil"} o ovirah na progah</span>${SVG_DESNO}
      </a>`;
}

let stOvir = null;

function showOverview() {
  naZaslonu = null;
  document.body.classList.remove("ima-izid");
  razlozi();
  resultsEl.innerHTML = "";
  resultHeadEl.textContent = "";
  alertsEl.innerHTML = "";
  vozovnicaEl.innerHTML = "";
  izrisiPregled();
  if (IS_BUS || stOvir !== null) return;
  // Število ovir pride za žetoni; dodamo ga le, če je pregled še na zaslonu.
  fetch("/api/svezina").then(jsonOk).then((d) => {
    stOvir = d.alerts_active || 0;
    izrisiPregled();
  }).catch(() => { /* število ovir je postransko */ });
}

function izrisiPregled() {
  const deli = [];
  if (!IS_BUS && stOvir) deli.push(ovireHtml(stOvir));
  if (!favLoad().length) deli.push(popularChipsHtml());
  pregledEl.innerHTML = deli.join("");
}

pregledEl.addEventListener("click", (ev) => {
  const b = ev.target.closest(".route-chip");
  if (!b) return;
  $("from").value = b.dataset.from;
  $("to").value = b.dataset.to;
  paintAllClears();
  searchAB(true);
});

// ---------- shranjene poti ----------
//
// Potnik vozi isto pot vsak dan. `fav` je "to je moja pot" in ga clovek pove
// sam (zvezdica), `recent` je "tu sem pravkar bil" in se napise sam -- samo za
// predloge imen v praznem polju (`recentStations()`). Oba ločena po omrežju.
//
// Shranjena pot je vrstica z naslednjim odhodom (osnutek E2, David 24. 10.
// 2026: „to mi je všeč“): čez koliko, ura z voznim redom in žeton. Ista koda
// kot Moje poti na domači strani (`odhodiPoti` v common.js).

const FAV_KEY = "kajros:fav";
const FAV_MAX = 8;
const RECENT_KEY = "kajros:recent";
const RECENT_MAX = 6;
const MOJE_OSVEZI_MS = 60000;

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
  const z = naZaslonu;
  if (!z) return null;
  return z.kind === "board"
    ? { net: NETWORK, kind: "board", station: z.station, dir: z.dir }
    : { net: NETWORK, kind: "ab", from: z.from, to: z.to };
}

/** Ali tako postajo sploh poznamo. Ime, ne ugib: iscemo tocno ujemanje po
 *  CELEM kazalu (brez omrezja). Streznik ostane za primer, ko se kazalo ni
 *  nalozeno. */
async function stationExists(name) {
  if (KAZALO) {
    const want = fold(name);
    return KAZALO.some((s) => s.f === want);
  }
  try {
    const res = await fetch(
      `/api/stations/search?q=${encodeURIComponent(name)}&limit=8&network=${NETWORK}`);
    const list = await res.json();
    return Array.isArray(list) && list.some((s) => fold(s.name) === fold(name));
  } catch (err) {
    // Brez omrezja ne zavracamo: shranjevanje ni kriticno, napacen vnos pa
    // se da odstraniti. Zavrniti veljavno pot bi bilo huje.
    return true;
  }
}

async function favToggle() {
  const cur = favCurrent();
  if (!cur) return;
  const list = favLoad();
  const at = list.findIndex((f) => favKey(f) === favKey(cur));

  // **Odstranjevanje se NE preverja.** Ce bi slo skozi isto preverbo kot
  // shranjevanje, bi bila pot z neveljavno postajo -- torej natanko tista,
  // ki jo clovek hoce odstraniti -- edina, ki se je ne da.
  if (at >= 0) {
    list.splice(at, 1);
    favSave(list);
    paintFavButton();
    renderRecents();
    return;
  }

  // Doslej se je shranilo, kar je bilo v polju -- tudi "asdf → qwer".
  const names = cur.kind === "board" ? [cur.station] : [cur.from, cur.to];
  const znane = await Promise.all(names.map(stationExists));
  if (znane.some((v) => !v)) {
    const dan = $("povzetek-dan");
    const prej = dan.textContent;
    dan.textContent = "te postaje ne poznam";
    $("fav-toggle").classList.add("is-refused");
    setTimeout(() => {
      $("fav-toggle").classList.remove("is-refused");
      if (dan.textContent === "te postaje ne poznam") dan.textContent = prej;
    }, 2200);
    return;
  }

  list.unshift(cur);
  favSave(list);
  paintFavButton();
  renderRecents();
}

function paintFavButton() {
  const btn = $("fav-toggle");
  const cur = favCurrent();
  btn.hidden = !cur;
  if (!cur) return;
  const on = favLoad().some((f) => favKey(f) === favKey(cur));
  btn.setAttribute("aria-pressed", String(on));
  btn.title = on ? "odstrani med shranjenimi" : "shrani";
  btn.setAttribute("aria-label", on ? "shranjeno — odstrani" : "shrani");
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
// polju. Vrstni red je vrstni red obiska: zadnja je najverjetnejsa.
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

let mojeSig = null;
let mojeOdhodi = {};    // kljuc -> zadnji izrisani odhod; osvezitev ne utripa

/** Shranjene poti kot vrstice. Zvezdica je svoj gumb (odstrani v dveh
 *  dotikih), ostalo vrstice odpre pot. Vgnezdeni <button> je neveljaven HTML. */
function renderRecents() {
  const saved = favLoad();
  $("moje").hidden = !saved.length;
  const sig = saved.map(favKey).join(",");
  if (sig !== mojeSig) {
    mojeSig = sig;
    $("recents").innerHTML = saved.map((f) => {
      const k = escapeHtml(favKey(f));
      const ime = f.kind === "board"
        ? `${escapeHtml(f.station)}${f.dir === "prihodi" ? " <span>· prihodi</span>" : ""}<span class="mp-smer"></span>`
        : `${escapeHtml(f.from)} <span>→ ${escapeHtml(f.to)}</span>`;
      return `<div class="mp" data-kljuc="${k}">
        <button type="button" class="mp-zvezda" data-fav-del="${k}"
                aria-label="odstrani ${escapeHtml(favLabel(f))} med shranjenimi">${SVG_ZVEZDICA}</button>
        <button type="button" class="mp-odpri" data-fav="${k}">
          <span class="mp-ime">${ime}</span>
          <span class="mp-cez"></span>
          <span class="mp-l2">${mojeOdhodi[favKey(f)] || ""}</span>
        </button>
      </div>`;
    }).join("");
  }
  izrisiPregled();
  osveziMoje();
  // Kartica najbližjega se spremeni v žeton in nazaj, ko se pojavi ali izgine
  // prva shranjena pot.
  if (najblizje.postaja) {
    izrisiNajblizje();
    if (!najblizje.tabla) osveziNajblizje();
  }
}

let mojeTek = 0;

/** Naslednji odhod vsake shranjene poti; danes nič več -- prva jutrišnja. */
async function osveziMoje() {
  const saved = favLoad();
  if (!saved.length || document.hidden) return;
  const moj = ++mojeTek;
  await Promise.all(saved.map(async (f) => {
    const k = favKey(f);
    const zdaj = Date.now();
    let cez = "";
    let l2 = "";
    let smer = null;
    try {
      const danes = await odhodiPoti(f);
      let o = naslednjiOdhodi(danes, zdaj, 1)[0];
      let jutri = false;
      smer = danes.length ? danes[0].smer : null;
      if (!o) {
        o = (await odhodiPoti(f, jutriIso()))[0];
        jutri = true;
      }
      if (o) {
        const ms = new Date(o.pricakovano || o.ura).getTime();
        cez = jutri ? `jutri ob ${hhmm(o.ura)}` : ms < zdaj ? "ni potrditve" : cezBesedilo(ms, zdaj) || hhmm(o.pricakovano || o.ura);
        l2 = `${oznakaHtml(o.vir)}${uraHtml(o.ura, o.zamuda)}<span class="sp"></span>${zetonVrsticeHtml({
          zamuda: o.zamuda, kind: o.vir.delay_kind, nadomestni: o.nadomestni, ura: o.ura,
          nowMs: jutri ? 0 : zdaj, obicajno: o.zamuda ? null : o.obicajno,
        })}`;
      } else {
        l2 = '<span class="zt-op">danes in jutri ne pelje nič</span>';
      }
    } catch (err) {
      l2 = '<span class="zt-op">odhodov ni bilo mogoče naložiti</span>';
    }
    if (moj !== mojeTek) return;
    mojeOdhodi[k] = l2;
    const el = $("recents").querySelector(`.mp[data-kljuc="${CSS.escape(k)}"]`);
    if (!el) return;
    el.querySelector(".mp-cez").innerHTML = cezHtml(cez);
    el.querySelector(".mp-cez").classList.toggle("je-tiho", !cez.startsWith("čez") && cez !== "zdaj");
    el.querySelector(".mp-l2").innerHTML = l2;
    const s = el.querySelector(".mp-smer");
    if (s) s.textContent = smer ? ` → ${smer}` : "";
  }));
}

setInterval(() => {
  if (!document.hidden && $("moje").offsetParent) osveziMoje();
}, MOJE_OSVEZI_MS);
document.addEventListener("visibilitychange", () => {
  if (!document.hidden && $("moje").offsetParent) osveziMoje();
});

function openFav(key) {
  const f = favLoad().find((x) => favKey(x) === key);   // zetoni so samo shranjeni
  if (!f) return;
  nastaviDan(todayIso());
  if (f.kind === "board") {
    $("from").value = f.station;
    $("to").value = "";
    tablaKind = f.dir || "odhodi";
    tablaOb = "";
    paintAllClears();
    searchBoard(true);
  } else {
    $("from").value = f.from;
    $("to").value = f.to;
    paintAllClears();
    searchAB(true);
  }
}

function favRemove(key) {
  const list = favLoad();
  const at = list.findIndex((f) => favKey(f) === key);
  if (at < 0) return;
  list.splice(at, 1);
  favSave(list);
  renderRecents();
  paintFavButton();
}

// Odstranitev naravnost s seznama, v dveh dotikih: prvi zvezdico spremeni v
// „odstrani?“, drugi v treh sekundah odstrani. Zvezdica je velika tarča ob
// robu, po pomoti se ne sme izgubiti pot, ki jo človek vozi vsak dan.
$("recents").addEventListener("click", (ev) => {
  const del = ev.target.closest("[data-fav-del]");
  if (del) {
    if (del.classList.contains("je-potrdi")) {
      favRemove(del.dataset.favDel);
      return;
    }
    del.classList.add("je-potrdi");
    del.innerHTML = "odstrani?";
    setTimeout(() => {
      if (!del.isConnected) return;
      del.classList.remove("je-potrdi");
      del.innerHTML = SVG_ZVEZDICA;
    }, 3000);
    return;
  }
  const odpri = ev.target.closest("[data-fav]");
  if (odpri) openFav(odpri.dataset.fav);
});

// ---------- poizvedbe ----------

// Po iskanju se obrazec skrči v vrstico z vprašanjem, dotik nanjo ga odpre
// (na telefonu je bil odgovor sicer pod pregibom). Samo ob lastnem iskanju
// ali povezavi, nikoli ob osvezitvi: ta bi zaprla obrazec, ki ga clovek
// ravno popravlja. Na namizju obrazec ostane levo in vrstica stoji nad
// odgovorom (CSS).
function zlozi() {
  const z = naZaslonu;
  if (!z) return;
  // Kdor je tapnil shranjeno pot na dnu seznama, mora odgovor videti od
  // začetka; skrčen obrazec stran skrajša in pomik bi ostal sredi odgovora.
  // Mesto ob vrnitvi (`obnoviMesto`) pride za izrisom in to povozi.
  window.scrollTo(0, 0);
  const ime = (s) => `<span class="pz-ime">${escapeHtml(s)}</span>`;
  $("povzetek-pot").innerHTML = z.kind === "ab"
    ? `${ime(z.from)}<span class="pz-pus" aria-hidden="true">→</span>${ime(z.to)}`
    : ime(z.station);
  $("povzetek-dan").textContent = z.kind === "ab" ? danNapis(z.date)
    : `${z.dir} · ${danNapis(z.date)}${tablaOb ? ` od ${tablaOb}` : ""}`;
  $("povzetek-uredi").setAttribute("aria-label",
    `spremeni iskanje: ${$("povzetek-pot").textContent}, ${$("povzetek-dan").textContent}`);
  $("povzetek-swap").hidden = z.kind !== "ab";
  $("povzetek-kam").hidden = z.kind !== "board";
  document.body.classList.toggle("pz-tabla", z.kind === "board");
  document.body.classList.add("zlozeno", "ima-izid");
  paintFavButton();
  // Fokus v skritem polju se izgubi (in tipkovnica telefona ostane odprta
  // cez odgovor); naj ostane pri vprasanju, ki se ga da spet odpreti.
  const f = document.activeElement;
  if (f && f.closest(".isk-obrazec") && !f.offsetParent) {
    $("povzetek-uredi").focus({ preventScroll: true });
  }
}

function razlozi() {
  document.body.classList.remove("zlozeno");
}

function schedulePoll(fn, isToday) {
  clearTimeout(pollTimer);
  if (isToday) pollTimer = setTimeout(fn, POLL_MS);
}

// Iskanje se mora videti TAKOJ, ne sele ko odgovor pride.
function zacniIskanje(kaj) {
  prejsnjiOdprti = !!(mesto && mesto.odprto);
  resultHeadEl.textContent = "";
  alertsEl.innerHTML = "";
  vozovnicaEl.innerHTML = "";
  resultsEl.innerHTML = `<div class="empty-state is-busy">${escapeHtml(kaj)}</div>`;
  document.querySelectorAll(".go").forEach((b) => { b.disabled = true; });
}

function koncajIskanje() {
  document.querySelectorAll(".go").forEach((b) => { b.disabled = false; });
}

/** Gumb „Poišči“: s ciljem zveze, brez njega tabla s postaje Od. */
function isci() {
  const from = $("from").value.trim();
  const to = $("to").value.trim();
  if (!from) {
    $("from").focus();
    return;
  }
  if (to) {
    searchAB(true);
  } else {
    // Iz obrazca je tabla vedno odhodi od zdaj; prihodi in ura pridejo
    // samo s povezavo.
    tablaKind = "odhodi";
    tablaOb = "";
    searchBoard(true);
  }
}

/** `tiho`: osvezitev na 30 s, ne novo iskanje. Do 5. 10. 2026 je vsaka
 *  osvezitev zveze za hip zamenjala z "iščem …" in stran je skocila na vrh.
 *  `vpr`: osvezitev ponovi vprasanje, ki je na zaslonu, ne tistega, ki ga
 *  clovek ravno tipka v odprt obrazec. */
async function searchAB(push, tiho = false, vpr = null) {
  const from = vpr ? vpr.from : $("from").value.trim();
  const to = vpr ? vpr.to : $("to").value.trim();
  const date = vpr ? vpr.date : $("date").value || todayIso();
  if (!from || !to) return;
  if (fold(from) === fold(to)) {
    resultsEl.innerHTML = `<div class="empty-state">Od in Kam sta ${IS_BUS ? "isto postajališče" : "ista postaja"}.</div>`;
    return;
  }
  if (!tiho) {
    // Osvezitev, ki bi se sprozila med novim iskanjem, bi ga prehitela.
    clearTimeout(pollTimer);
    naZaslonu = { kind: "ab", from, to, date };
    remember({ tab: "ab", from, to, date });
  }
  if (push) {
    history.replaceState(null, "", `?${new URLSearchParams({ from, to, date })}`);
    zapomniIskanje(NETWORK);
    zlozi();
  }
  if (!tiho) zacniIskanje(`iščem zveze ${from} → ${to} …`);
  const osvezi = () => searchAB(false, true, { from, to, date });
  // Pozen odgovor starega vprasanja ne sme prepisati novega.
  const moja = ++zvezeSt;

  try {
    const url = `/api/connections?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`
      + `&date=${encodeURIComponent(date)}&network=${NETWORK}`;
    const res = await fetch(url);
    if (moja !== zvezeSt) return;
    // Tiha osvezitev ob napaki pusti stare zveze in poskusi znova -- tudi ob
    // 404 in 5xx (nocni uvoz voznega reda, objava).
    if (tiho && !res.ok) {
      schedulePoll(osvezi, date === todayIso());
      return;
    }
    if (res.status === 404) {
      resultsEl.innerHTML = '<div class="empty-state">Te postaje ne poznam. Začni tipkati in izberi s seznama.</div>';
      razlozi();   // popraviti je treba polje, ne gledati odgovora
      return;
    }
    const data = await res.json();
    if (moja !== zvezeSt) return;
    // Vsak drug neuspeh pove strežnik sam.
    if (!res.ok) {
      resultsEl.innerHTML = `<div class="empty-state">${
        escapeHtml(data && data.detail ? data.detail : "Iskanje ni uspelo.")}</div>`;
      return;
    }
    renderConnections(data);
    schedulePoll(osvezi, data.date === todayIso());
  } catch (err) {
    if (moja !== zvezeSt) return;
    console.error("iskanje ni uspelo", err);
    refreshFeedDot();   // zahteva ni uspela -- naj pika pove, kaj ve
    // Tiha osvezitev pusti stare zveze (imajo uro) in poskusi znova.
    if (tiho) schedulePoll(osvezi, date === todayIso());
    else resultsEl.innerHTML = '<div class="empty-state">Iskanje ni uspelo. Strežnik morda ni dosegljiv.</div>';
  } finally {
    if (moja === zvezeSt) koncajIskanje();
  }
}

/** Tabla s postaje. `tiho`: osvezitev, tabla ostane na zaslonu, dokler ne
 *  pride nova. `vpr`: osvezitev ponovi vprasanje na zaslonu. */
async function searchBoard(push, tiho = false, vpr = null) {
  const station = vpr ? vpr.station : $("from").value.trim();
  const date = vpr ? vpr.date : $("date").value || todayIso();
  const kind = tablaKind;
  const from = tablaOb;
  if (!station) return;
  if (!tiho) {
    clearTimeout(pollTimer);
    naZaslonu = { kind: "board", station, date, dir: kind };
    remember({ tab: "board", station, date, kind, from });
    zacniIskanje(`iščem odhode — ${station} …`);
  }
  // Nova postaja vzame svojo zapomnjeno smer; osvezitev iste obdrzi izbrano.
  if (push || tablaZa !== station) {
    izbranaSmer = IS_BUS ? smerIzNaslova : null;
    smerIzSpominaPo = IS_BUS && !smerIzNaslova;
    smerIzNaslova = null;
    tablaZa = station;
  }
  if (push) {
    // Ura se v naslovu imenuje `ob` in NE `from`: `from` je na tej strani
    // izhodiščna postaja zvez. Eno ime, en pomen; `/api/departures` ostane
    // pri svojem `from`.
    const q = new URLSearchParams({ station, date, kind });
    if (from) q.set("ob", from);
    if (izbranaSmer) q.set("smer", izbranaSmer);
    history.replaceState(null, "", `?${q}`);
    zapomniIskanje(NETWORK);
    zlozi();
  }
  const osvezi = () => searchBoard(false, true, { station, date });

  const moja = ++tablaSt;
  try {
    // Brez ure streznik izbere sam: za danes tri ure naprej od zdaj, za drug
    // dan cel dan. Ura iz naslova to povozi.
    const q = from ? `&from=${encodeURIComponent(from)}&window=360` : "";
    const url = `/api/departures?station=${encodeURIComponent(station)}`
      + `&date=${encodeURIComponent(date)}&kind=${kind}&network=${NETWORK}${q}`
      + (izbranaSmer ? `&smer=${encodeURIComponent(izbranaSmer)}` : "");
    const res = await fetch(url);
    if (moja !== tablaSt) return;
    // Isto kot pri zvezah: tiha osvezitev ob napaki pusti tablo in poskusi znova.
    if (tiho && !res.ok) {
      schedulePoll(osvezi, date === todayIso());
      return;
    }
    if (res.status === 404) {
      resultsEl.innerHTML = '<div class="empty-state">Te postaje ne poznam. Začni tipkati in izberi s seznama.</div>';
      razlozi();
      return;
    }
    if (!res.ok) {
      resultsEl.innerHTML = '<div class="empty-state">Nalaganje ni uspelo.</div>';
      return;
    }
    const data = await res.json();
    if (moja !== tablaSt) return;
    if (smerIzSpominaPo) {
      smerIzSpominaPo = false;
      izbranaSmer = smerIzSpomina(data.station);
    }
    renderBoard(data);
    schedulePoll(osvezi, data.date === todayIso());
  } catch (err) {
    if (moja !== tablaSt) return;
    console.error("tabla ni uspela", err);
    refreshFeedDot();
    // Tiha osvezitev pusti staro tablo: ta ima uro in je uporabna, prazna ni.
    if (tiho) schedulePoll(osvezi, date === todayIso());
    else resultsEl.innerHTML = '<div class="empty-state">Nalaganje ni uspelo.</div>';
  } finally {
    if (moja === tablaSt) koncajIskanje();
  }
}

// Zadnja poizvedba je prva v seznamu nedavnih (ločen po omrežju).
function remember(obj, novo = true) {
  const cur = obj.tab === "board"
    ? { net: NETWORK, kind: "board", station: obj.station, dir: obj.kind }
    : { net: NETWORK, kind: "ab", from: obj.from, to: obj.to };
  recentAdd(cur);
  if (novo) predlagajShranjevanje(cur);
}

// Kdor isto pot ali tablo išče znova (vsaj pol ure pozneje, ne ob osvežitvi),
// dobi ponudbo, da jo shrani na prvo stran. „Ne, hvala“ velja za to pot za
// vedno -- ponudba ne sme nadlegovati.
const PONOVITVE_KEY = "kajros:ponovitve";
const PONOVITEV_RAZMIK_MS = 30 * 60 * 1000;
const PONOVITEV_NAJVEC = 40;

function ponovitve() {
  try {
    const o = JSON.parse(localStorage.getItem(PONOVITVE_KEY) || "{}");
    return o && typeof o === "object" && !Array.isArray(o) ? o : {};
  } catch (err) {
    return {};
  }
}

function shraniPonovitve(o) {
  const kljuci = Object.keys(o).sort((a, b) => (o[b].t || 0) - (o[a].t || 0))
    .slice(0, PONOVITEV_NAJVEC);
  try {
    localStorage.setItem(PONOVITVE_KEY, JSON.stringify(Object.fromEntries(kljuci.map((k) => [k, o[k]]))));
  } catch (err) {
    /* zasebno okno: ponudba pač ne pride */
  }
}

function predlagajShranjevanje(cur) {
  const el = $("predlog-shrani");
  el.hidden = true;
  const k = `${NETWORK}|${favKey(cur)}`;
  const vse = ponovitve();
  const prej = vse[k];
  const zdaj = Date.now();
  const ponudi = prej && !prej.ne && zdaj - prej.t >= PONOVITEV_RAZMIK_MS
    && !favLoad().some((f) => favKey(f) === favKey(cur));
  vse[k] = { t: zdaj, ne: !!(prej && prej.ne) };
  shraniPonovitve(vse);
  if (!ponudi) return;
  el.innerHTML = `<span>${cur.kind === "board" ? "To tablo" : "To pot"} iščeš večkrat.</span>
    <button type="button" class="predlog-da">☆ Shrani na prvo stran</button>
    <button type="button" class="predlog-ne">Ne, hvala</button>`;
  el.hidden = false;
  el.querySelector(".predlog-da").addEventListener("click", () => {
    el.hidden = true;
    favToggle();
  });
  el.querySelector(".predlog-ne").addEventListener("click", () => {
    el.hidden = true;
    const o = ponovitve();
    o[k] = { t: Date.now(), ne: true };
    shraniPonovitve(o);
  });
}

$("fav-toggle").addEventListener("click", favToggle);

// ---------- najbližja postaja ----------
//
// Kadar je lega dovoljena in Od prazen, je nad shranjenimi kartica
// najbližjega postajališča z obema stranema ceste in prvim odhodom z vsake
// (osnutek E1): en dotik do table, brez tipkanja. Brez dovoljenja tih gumb
// „Najbližje postajališče“ -- okna za dovoljenje ne odpremo sami, samo dotik.
//
// Meja 2 km zračne črte. Izmerjeno na 435 044 naslovih iz OSM (22. 10. 2026):
// do 2 km od avtobusnega postajališča je 95,8 % naslovov, od železniške
// postaje 37,7 %. Lega mora biti natančna (`LEGA_DOVOLJ_M`, 100 m): pri taki
// napaki je najbližje drugo postajališče v 6,1 % (vlak 2,1 %).
const NAJBLIZJE_DO_M = 2000;
// Aplikacija stran pusti odprto ure: predlog od doma ni predlog v službi.
const NAJBLIZJE_STARO_MS = 5 * 60000;

const najblizje = { postaja: null, tabla: null, ts: 0, odjava: null, rok: null, stanje: null };

function razdaljaBesedilo(m) {
  return m < 1000 ? `${m} m` : `${(m / 1000).toFixed(1).replace(".", ",")} km`;
}

/** Vrstica ene strani ceste: ime strani, čez koliko in žeton prvega odhoda. */
function stranHtml(napis, center, r, nowMs) {
  const ms = new Date(r.expected || r.sched).getTime();
  const cez = cezBesedilo(ms, nowMs) || hhmm(r.expected || r.sched);
  const zam = r.zamuda ? (delayMin(r.zamuda) === 0 ? "točno" : delayText(r.zamuda)) : "vozni red";
  return `<span class="nb-ime">${escapeHtml(napis)}</span>
    <span class="nb-pod">${center ? `${escapeHtml(center)} · ` : ""}${escapeHtml(zam)}</span>
    <span class="nb-desno">${oznakaHtml(r)}<b>${cezHtml(cez)}</b>${SVG_DESNO}</span>`;
}

function izrisiNajblizje() {
  const el = $("najblizje");
  if ($("from").value.trim()) {
    el.hidden = true;
    return;
  }
  const p = najblizje.postaja;
  if (!p) {
    // Brez dovoljenja tih gumb; kdor je lego zavrnil, ga ne dobi (gumb mu
    // je ne vrne -- nastavitve brskalnika so drugje).
    el.hidden = najblizje.stanje !== "vprasaj";
    el.innerHTML = el.hidden ? "" : `<button type="button" class="nb-vprasaj" id="nb-vprasaj">${SVG_TI}${
      IS_BUS ? "Najbližje postajališče" : "Najbližja postaja"}</button>`;
    return;
  }
  // Kdor ima shranjene poti, ima svoj odgovor spodaj: najbližje je tam en tih
  // žeton (osnutek E2), kartica z obema stranema ceste je za prazno stran (E1).
  if (favLoad().length) {
    el.innerHTML = `<button type="button" class="nb-vprasaj" data-smer="">${SVG_TI}Najbližje: <b>${
      escapeHtml(p.name)}</b> <span>· ${razdaljaBesedilo(p.meters)}</span></button>`;
    el.hidden = false;
    return;
  }
  const nowMs = Date.now();
  const t = najblizje.tabla;
  let vrstice = "";
  if (t && t.board && t.board.length) {
    const prvi = (rows) => razvrstiTablo(rows.filter((r) => !r.ne_ustavi && !r.odpovedano), nowMs).ahead[0];
    const smeri = (t.smeri || []).slice(0, 3);
    const deli = smeri.length >= 2
      ? smeri.map((s) => ({ s, r: prvi(t.board.filter((r) => r.smer === s.kljuc)) })).filter((x) => x.r)
        .map((x) => `<button type="button" class="nb-stran" data-smer="${escapeHtml(x.s.kljuc)}">${
          stranHtml(smerNapis(x.s), x.s.center, x.r, nowMs)}</button>`)
      : [prvi(t.board)].filter(Boolean).map((r) => `<button type="button" class="nb-stran" data-smer="">${
        stranHtml(`→ ${lepoIme(r.towards)}`, null, r, nowMs)}</button>`);
    vrstice = deli.join("");
  }
  el.innerHTML = `<button type="button" class="nb-glava" data-smer="">${SVG_TI}<b>${escapeHtml(p.name)}</b>
      <span>${razdaljaBesedilo(p.meters)} od tebe</span></button>
    ${vrstice ? `<div class="nb-strani">${vrstice}</div>` : ""}`;
  el.hidden = false;
}

function koncajNajblizje() {
  if (najblizje.odjava) { najblizje.odjava(); najblizje.odjava = null; }
  clearTimeout(najblizje.rok);
}

async function obLegiNajblizje(l) {
  if (!l || l.acc > LEGA_DOVOLJ_M) return;
  // Ena natančna lega je dovolj: tabla ni zemljevid in GPS ugasne.
  koncajNajblizje();
  try {
    const list = await fetch(
      `/api/stations/near?lat=${l.lat}&lon=${l.lon}&network=${NETWORK}&limit=1`).then(jsonOk);
    najblizje.postaja = list[0] && list[0].meters <= NAJBLIZJE_DO_M ? list[0] : null;
    najblizje.ts = Date.now();
    najblizje.tabla = null;
    izrisiNajblizje();
    if (najblizje.postaja) osveziNajblizje();
  } catch (err) {
    /* predlog je postranski; brez njega ostane polje */
  }
}

/** Prvi odhodi z najbližjega postajališča: ena zahteva za obe strani. */
async function osveziNajblizje() {
  const p = najblizje.postaja;
  if (!p || favLoad().length) return;
  try {
    const q = new URLSearchParams({ station: p.name, network: NETWORK, limit: "60" });
    najblizje.tabla = await fetch(`/api/departures?${q}`).then(jsonOk);
    izrisiNajblizje();
  } catch (err) {
    /* kartica ostane z imenom */
  }
}

function poisciNajblizje() {
  if (najblizje.odjava || Date.now() - najblizje.ts < NAJBLIZJE_STARO_MS) return;
  najblizje.odjava = LEGA.poslusaj(obLegiNajblizje);
  // GPS, ki v pol minute ne pove dovolj natančno, ne sveti naprej za predlog.
  najblizje.rok = setTimeout(koncajNajblizje, LEGA_ROK_MS);
}

$("najblizje").addEventListener("click", async (ev) => {
  if (ev.target.closest("#nb-vprasaj")) {
    try {
      const l = await poisciMe();
      najblizje.stanje = "dano";
      await obLegiNajblizje(l);
    } catch (err) {
      $("najblizje").innerHTML = `<p class="nb-napaka">${escapeHtml(err.message)}</p>`;
    }
    return;
  }
  const b = ev.target.closest("[data-smer]");
  const p = najblizje.postaja;
  if (!b || !p) return;
  $("from").value = p.name;
  $("to").value = "";
  paintAllClears();
  nastaviDan(todayIso());
  tablaKind = "odhodi";
  tablaOb = "";
  // Izbrana stran ceste gre skozi isto pot kot deljena povezava.
  smerIzNaslova = b.dataset.smer || null;
  searchBoard(true);
});
$("from").addEventListener("input", izrisiNajblizje);

function obStanjuLege(s) {
  najblizje.stanje = s;
  if (s === "dano") poisciNajblizje();
  izrisiNajblizje();
}
LEGA.obStanju(obStanjuLege);
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState !== "visible") return;
  stanjeLege().then(obStanjuLege);
  if (najblizje.postaja && !document.body.classList.contains("zlozeno")) osveziNajblizje();
});
stanjeLege().then(obStanjuLege);
setInterval(() => {
  if (!document.hidden && najblizje.postaja && $("najblizje").offsetParent) osveziNajblizje();
}, MOJE_OSVEZI_MS);

// ---------- obrazec ----------

$("iskanje").addEventListener("submit", (ev) => { ev.preventDefault(); isci(); });

$("swap").addEventListener("click", () => {
  const a = $("from"), b = $("to");
  [a.value, b.value] = [b.value, a.value];
  paintAllClears();
  // Fokus na izhodisce: kdor je gumb dosegel s tipkovnico, mora videti izid.
  a.focus();
  if (a.value && b.value) searchAB(true);
});

// Pot nazaj je najpogostejse drugo vprasanje, zato zamenjava tudi v zlozeni
// vrstici -- brez nje bi bila dva dotika in obrazec cez cel zaslon.
$("povzetek-swap").addEventListener("click", () => {
  const z = naZaslonu;
  if (!z || z.kind !== "ab") return;
  $("from").value = z.to;
  $("to").value = z.from;
  paintAllClears();
  searchAB(true);
});

$("povzetek-uredi").addEventListener("click", () => {
  razlozi();
  izrisiNajblizje();
  window.scrollTo({ top: 0 });
  // Na namizju je obrazec ves čas odprt; dotik vrstice pomeni „popravi“.
  if (innerWidth >= 900) $("from").focus();
});

// Tabla + cilj = zveze: „Kam?“ odpre obrazec s kazalcem v polju Kam.
$("povzetek-kam").addEventListener("click", () => {
  razlozi();
  window.scrollTo({ top: 0 });
  $("to").focus();
});

// ---------- zagon ----------

function restore() {
  const q = new URLSearchParams(location.search);

  // **Polja se ne izpolnijo iz spomina.** Vpise ju samo naslov (deljena
  // povezava). Nedavne postaje ostanejo v spustnem seznamu.
  const station = q.get("station") || "";
  // `from` je tu SAMO izhodiščna postaja. Ura na tabli je `ob`.
  const from = q.get("from") || "";
  const to = q.get("to") || "";

  nastaviDan(q.get("date") || todayIso());
  tablaKind = q.get("kind") === "prihodi" ? "prihodi" : "odhodi";
  tablaOb = q.get("ob") || "";

  // Iskanje iz naslova (deljena povezava, vrnitev) je zadnje iskanje.
  if (station) {
    $("from").value = station;
    $("to").value = "";
    paintAllClears();
    zapomniIskanje(NETWORK);
    smerIzNaslova = q.get("smer");
    searchBoard(true);
  } else if (from && to) {
    $("from").value = from;
    $("to").value = to;
    paintAllClears();
    zapomniIskanje(NETWORK);
    if (fold(from) !== fold(to)) searchAB(true);
    else searchAB(false);
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

const STATION_INPUTS = ["from", "to"];

function paintAllClears() {
  for (const id of STATION_INPUTS) paintClear($(id));
}

for (const id of STATION_INPUTS) {
  attachSuggest($(id), $(`suggest-${id}`));
  attachClear($(id));
}

// Kazalo postaj se nalozi takoj po strani; iskalnik do takrat vprasa streznik.
naloziKazaloOmrezja();
renderRecents();

tickClock();
setInterval(tickClock, 1000);
// Prvi klic opravi `pollWhileVisible` sam (ročni pred njim ga je podvojil).
pollWhileVisible(refreshFeedDot, 30000);
restore();
