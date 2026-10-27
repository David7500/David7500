"use strict";

// Svoje okno enega vlaka: ta voznja + zgodovina te poti.
// Barve zamud so projektna ORDINALNA lestvica (en odtenek, monotona svetlost) --
// uporabljena samo tam, kjer odtenek pomeni velikost zamude. Kjer meritve ni,
// nastopi rezervirana barva, ki je lestvica ne uporablja.

const TRAIN_NO = document.body.dataset.trainNo;
// Omrežje te strani. Znano je takoj, `state.network` pa šele iz odgovora.
const OMREZJE = document.body.dataset.network || "zeleznica";
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

// Kako pogosto okno vpraša po vožnji. Med vožnjo na 10 s (prej 30): SŽ zamudo
// preračuna na 15 s, derp.si pošlje na 30 s, zajem oboje bere sproti -- nova
// številka je tako na zaslonu v nekaj sekundah, ne v pol minute (David,
// 24. 10. 2026: „nove informacije morajo biti hitro vidne“). Pred odhodom in
// po cilju se nič ne spremeni tako hitro.
const RITEM_VOZI_MS = 10000;
const RITEM_MIRUJE_MS = 60000;
const ritemOkna = () => (!state.run || voziAliKmalu(state.run) ? RITEM_VOZI_MS : RITEM_MIRUJE_MS);
// Zanka vožnje; gumb „osveži“ na zemljevidu jo sproži takoj (`initOsvezi`).
let oknoPoll = null;

// Stanje okna: vožnja, ocena naprej, vreme po postankih in veriga vozila.
// `novicaOb` = trenutek zadnje novice o vožnji po uri TE naprave (iz `tiho_s`
// ob odgovoru: ura strežnika in telefona se lahko razlikujeta); `brezZveze` od
// prve neuspele osvežitve; `vrh` = kar je bilo na vrhu, da se sprememba vidi.
const state = { run: null, forecast: null, weather: new Map(),
                mode: "vlak", network: "zeleznica", agency: null,
                current: null, chain: null, prevozene: false,
                novicaOb: null, brezZveze: null, odziv: null, vrh: null };

// ---------- ta voznja ----------

const runHeadEl = document.getElementById("run-head");
const runTimelineEl = document.getElementById("run-timeline");
const headsignEl = document.getElementById("train-headsign");
const trakEl = document.getElementById("ov-trak");
const stanjeKjeEl = document.getElementById("ov-stanje-kje");
const stanjeSvezEl = document.getElementById("ov-stanje-svez");
const kartaOdstEl = document.getElementById("ov-karta-odst");


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

// Nazaj na tisto stran, s katere se pride: iskalnik vlakov ali avtobusov,
// z zadnjim iskanjem, ne prazen (`zadnjeIskanje`).
function applyNetworkWording() {
  const back = document.querySelector(".back-link");
  if (back && state.network === "avtobus") {
    back.setAttribute("href", zadnjeIskanje("avtobus") || "/app/bus");
    const label = back.querySelector("span");
    if (label) label.textContent = "avtobusi";
  }
}

// Puščica ‹ je korak nazaj, kadar smo prišli z naše strani (iskalnik, tabla,
// zemljevid, pot) -- brskalnik vrne stran z vnosom, izidom in mestom na
// seznamu, kot sistemska tipka. S tuje povezave je to zadnje iskanje v tem
// zavihku ali goli iskalnik. Prej vedno goli: nov vnos v zgodovini, prazna
// polja, in sistemski nazaj je potem vodil spet v okno vožnje.
(function pripniPuscico() {
  const back = document.querySelector(".back-link");
  if (!back) return;
  const zadnje = zadnjeIskanje(OMREZJE);
  if (zadnje) back.setAttribute("href", zadnje);
  back.addEventListener("click", (ev) => {
    let nasa = false;
    try {
      nasa = !!document.referrer && new URL(document.referrer).origin === location.origin;
    } catch (e) { /* neveljaven referrer: ni naša stran */ }
    if (nasa && history.length > 1) {
      ev.preventDefault();
      history.back();
    }
  });
})();

// Koliko casa sme meritev veljati za "trenutno". Cez to je vrednost zgodovina
// in prikaz mora to povedati -- "+20 min" ob polnoci, izmerjeno ob 17h, je laz.
const FRESH_S = 20 * 60;

// Koliko sekund tisine feeda o ENI voznji je ze nenormalno.
//
// To ni isto kot `FRESH_S`. Ta meri starost domnevnega prehoda (vozni red plus
// zamuda), tisina pa starost NOVICE. Razlika je bila 8. 9. 2026 na zaslonu:
// LPV 2001 je ob 07:00 kazal "+6 min, izmerjeno, pred 5 min", pri cemer je
// bila zadnja novica o njem stara 7 minut -- feed je nato po 24 minutah
// tisine povedal +29. Potnik na Ljubljani Polje je gledal prazen tir.
//
// Prag je izmerjen: voznje, ki so v feedu, se osvezujejo z mediano 45 s,
// p90 59 s in najvec 343 s (733 voznj, 8. 9. 2026). Tri minute tisine so
// torej ze izjema, ne ritem.
const TIHO_S = 180;

function trajanje(sekund) {
  const min = Math.round(sekund / 60);
  if (min < 1) return `${Math.round(sekund)} s`;
  if (min < 60) return `${min} min`;
  const h = Math.floor(min / 60);
  return `${h} h ${String(min % 60).padStart(2, "0")} min`;
}

// Voznja, ki se ni zacela, NI voznja brez podatkov -- to je razlika, ki jo
// potnik bere kot "aplikacija ne dela" proti "avtobus se ni odpeljal".
function odhodPrvega() {
  const first = state.run && state.run.stops && state.run.stops[0];
  const iso = first && (first.sched_dep || first.sched_arr);
  return iso && new Date(iso).getTime() > Date.now() ? iso : null;
}

function notStartedText() {
  const iso = odhodPrvega();
  if (iso) {
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
  // "Se ni nobene meritve" je res, a je stalo tik nad petnajstimi vrsticami
  // "LPP v zivo - cez N min" in se je bralo kot "ne vemo nicesar". Ista past
  // kot pri "mestnih linij LPP ni" nad zetoni LPP 25: poved mora govoriti o
  // TEM, cesar ni, in takoj povedati, kaj je namesto tega.
  if (state.run && state.run.zivi_vir) {
    return `meritve za to vožnjo še ni — ure so
            <strong>živa napoved ${escapeHtml(state.run.zivi_vir)}</strong>`;
  }
  // Za pretekli dan ni „še“: ta dan je mimo.
  const mimo = state.run && state.run.service_date < todayIso();
  return `za ${vehicleWord()} na ta dan ${mimo ? "" : "še "}ni nobene meritve`;
}

// Nadomestni prevoz SZ: `mode = bus`, a `network = zeleznica`. Na tej relaciji
// zamenjuje vlak, zato sodi med vlake -- podatkov v realnem casu pa nima.
function jeNadomestni() {
  return isBus(state.mode) && state.network === "zeleznica";
}

// Potnik na vozilu deli lego (`deljenje.py`). Vlak GPS-a nima in feed pove le,
// katero postajo je nazadnje prevozil -- poročilo pove, kje je zdaj. Z enim
// poročevalcem stoji ZRAVEN feedove številke, ne namesto nje.
function potnikiKjeText(p) {
  const bus = isBus(state.mode) && state.network === "avtobus";
  if (p.pri) return `pri ${bus ? "postajališču" : "postaji"} ${p.pri}`;
  if (p.med) return `med ${bus ? "postajališčema" : "postajama"} ${p.med[0]} in ${p.med[1]}`;
  return "";
}

// „stoji 3 min“: koliko časa, pove `deljenje.stanje` (`stoji_s`); pod
// minuto samo „stoji“.
const stojiMin = (p) => (p.stoji_s >= 60 ? `stoji ${Math.floor(p.stoji_s / 60)} min` : "stoji");

// „Tu okoli 09:40“ je prenos potnikove zamude. Kadar je poročilo verodostojno,
// teče ocena naprej že od njegove lege (`fetchRunAndForecast`) in ura ob
// postanku je ista beseda -- druga ura zraven bi bila dve resnici v vsaki
// vrstici. Ostane, kadar je potnik edini glas poleg feeda.
function potnikPostanekText(sp) {
  if (!sp) return "";
  if (sp.odpeljal) return `potnik na vozilu: odpeljal ob ${hhmm(sp.odpeljal)}`;
  if (sp.mimo) return "potnik na vozilu: je že mimo";
  if (sp.tu) return `potnik na vozilu: ${vehicleNoun()} je tu`;
  const pp = state.run && state.run.potniki;
  if (sp.pricakovano && !(pp && pp.verodostojno)) return `potnik na vozilu: tu okoli ${hhmm(sp.pricakovano)}`;
  return "";
}

// Postanek, ki ga je potnik izbral -- tisti, na katerem stoji. Iscemo po
// imenu, ker isto ime nosi vec `stop_id` (mestno postajalisce ima svojega za
// vsako smer) in ker naslov nosi ime, ne ida.
function yourStop(stops) {
  if (!URL_STATION || !stops) return null;
  const want = fold(URL_STATION);
  return stops.find((s) => fold(s.name) === want) || null;
}

// Najnovejša beseda o vožnji s POZNEJŠEGA postanka.
//
// Kadar številka za potnikovo postajo ni potrjena (zamrznjena napoved), feed pa
// je medtem o vožnji povedal nekaj bistveno drugega, sta na zaslonu dve
// resnici. 9. 9. 2026 je bilo prav to: pri Polju "+4 min, podatek ob 06:50",
// za Ljubljano pa "+15 min ob 07:03" -- in +15 je bilo 120 s od resnice, +4 pa
// 780 s. Katera drži, se **ne da ugotoviti** (izmerjeno: prenos poznejše
// vrednosti nazaj je slabši v 921 primerih od 1 662), zato prikaz ne izbira,
// ampak pokaže obe.
const RAZKRIJ_RAZLIKO_S = 300;

function novejsaBeseda(s, stops) {
  if (!s.feed_ts) return null;
  let naj = null;
  for (const x of stops) {
    if (x.stop_seq <= s.stop_seq || !x.feed_ts || x.feed_ts <= s.feed_ts) continue;
    if (!naj || x.feed_ts > naj.feed_ts) naj = x;
  }
  if (!naj || naj.zamuda == null || s.zamuda == null) return null;
  return Math.abs(naj.zamuda.s - s.zamuda.s) >= RAZKRIJ_RAZLIKO_S ? naj : null;
}

// ---------- vrh okna: odštevanje do postanka, o katerem človek sprašuje ----------
//
// Osnutek E (David, 23. 10. 2026): na vrhu je en postanek in koliko je še do
// njega. S table ali iskalnika je to potnikova postaja (`postaja` v naslovu),
// pred odhodom izhodišče („kdaj odpelje“), sicer cilj vožnje -- kdor ima
// poslano povezavo, nekoga čaka tam.

function ciljOkna() {
  const stops = state.run.stops;
  const tvoj = yourStop(stops);
  if (tvoj) return { s: tvoj, kaj: "tvoj" };
  if (!state.current && odhodPrvega()) return { s: stops[0], kaj: "odhod" };
  return { s: stops[stops.length - 1], kaj: "cilj" };
}

/**
 * Kaj vemo o enem postanku: zamuda, pričakovana ura in beseda, od kod je.
 *
 * Pravila iz `oznake.md`: „izmerjeno“ samo, kadar je feed vrednost potrdil po
 * prehodu (odloči strežnik, `stats.potrjen_prehod`), sicer „zadnji podatek“.
 * Neskladna vrednost je ocena, ne „izmerjena“ ničla pod vlakom, ki zamuja pol
 * ure. Naprej ima prednost živa napoved LPP (pri mestnem LPP je naša zgodovina
 * iz napovedi), nato naša ocena, nato zgodovina („običajno“, ni napoved za ta
 * dan), sicer vozni red.
 */
function vrednostNaPostanku(s) {
  const cur = state.current;
  const schedIso = s.sched_dep || s.sched_arr;
  const ura = (d) => (schedIso && d != null ? pricakovanaUra(schedIso, d) : schedIso);
  if (cur && s.stop_seq <= cur.stop_seq && !jeNeskladen(s)) {
    const d = stopDelay(s);
    const potrjen = !!(s.zamuda && s.zamuda.vrsta === "izmerjeno");
    return { mimo: true, d, z: stopZamuda(s), kdaj: ura(d) || stopActualIso(s),
             znak: potrjen ? "izmerjeno" : "zadnji podatek" };
  }
  const zivo = zivaNapoved(s);
  if (zivo) return { mimo: false, d: zivo.s, z: zivo, kdaj: ura(zivo.s), znak: "v živo" };
  const f = (state.forecast || []).find((x) => x.stop_seq === s.stop_seq);
  if (f) return { mimo: false, d: f.predicted_delay_s, z: null, kdaj: ura(f.predicted_delay_s), znak: "ocena", f };
  if (s.typical) {
    return { mimo: false, d: s.typical.median_s, z: null, kdaj: ura(s.typical.median_s),
             znak: "običajno", t: s.typical };
  }
  return { mimo: false, d: null, z: null, kdaj: schedIso, znak: "vozni red" };
}

// Ura je mimo, prehoda pa nihče ni potrdil: nekaj minut je vozilo res „zdaj“
// tam, potem bi beseda lagala (IC 503 brez ene meritve je ob 23.45 kazal
// „zdaj“ za 12.28). Meja kot na tabli, `stats.NEPOTRJEN_ODHOD_S`.
const NEPOTRJEN_MIN = 20;

/** Koliko še do pričakovane ure. Računa se ob vsakem izrisu (na 15 s), ker
 *  ura teče tudi, ko novih podatkov ni. */
function odstevanje(v, kaj) {
  if (v.mimo) return { beseda: kaj === "cilj" ? "na cilju" : "mimo" };
  const min = Math.round((new Date(v.kdaj).getTime() - Date.now()) / 60000);
  if (min <= -NEPOTRJEN_MIN) return { beseda: state.current ? "ni potrditve" : "ni podatkov" };
  if (min <= 0) return { beseda: "zdaj" };
  if (min < 60) return { n: String(min), enota: "min" };
  return { n: `${Math.floor(min / 60)} h`, enota: min % 60 ? `${min % 60} min` : "" };
}

// Vrh okna se izračuna enkrat, rišeta ga dva: velika oblika in kartica na
// zemljevidu avtobusa. Budilka bere isto številko (`budZamuda`): dve številki
// za isti postanek sta se že razšli (LPV 2268, 9. 9. 2026: prikaz 17:24,
// budilka 17:19).
function vrhOkna() {
  const { s, kaj } = ciljOkna();
  const v = vrednostNaPostanku(s);
  state.tvojaZamudaS = v.d != null ? Math.round(v.d) : null;
  state.tvojZnak = v.znak;
  state.tvojPostanek = s.stop_seq;
  return { s, kaj, v, o: odstevanje(v, kaj) };
}

const OBLIKA_ODST = '<svg class="ov-oblika" viewBox="0 0 88 88" aria-hidden="true"><path d="M44.0 1.2L46.8 1.8L49.4 3.4L51.7 5.1L54.1 6.2L56.8 6.4L59.7 6.1L62.7 6.1L65.4 6.9L67.5 8.8L69.0 11.5L70.2 14.2L71.7 16.3L73.8 17.8L76.5 19.0L79.2 20.5L81.1 22.6L81.9 25.3L81.9 28.3L81.6 31.2L81.8 33.9L82.9 36.3L84.6 38.6L86.2 41.2L86.8 44.0L86.2 46.8L84.6 49.4L82.9 51.7L81.8 54.1L81.6 56.8L81.9 59.7L81.9 62.7L81.1 65.4L79.2 67.5L76.5 69.0L73.8 70.2L71.7 71.7L70.2 73.8L69.0 76.5L67.5 79.2L65.4 81.1L62.7 81.9L59.7 81.9L56.8 81.6L54.1 81.8L51.7 82.9L49.4 84.6L46.8 86.2L44.0 86.8L41.2 86.2L38.6 84.6L36.3 82.9L33.9 81.8L31.2 81.6L28.3 81.9L25.3 81.9L22.6 81.1L20.5 79.2L19.0 76.5L17.8 73.8L16.3 71.7L14.2 70.2L11.5 69.0L8.8 67.5L6.9 65.4L6.1 62.7L6.1 59.7L6.4 56.8L6.2 54.1L5.1 51.7L3.4 49.4L1.8 46.8L1.2 44.0L1.8 41.2L3.4 38.6L5.1 36.3L6.2 33.9L6.4 31.2L6.1 28.3L6.1 25.3L6.9 22.6L8.8 20.5L11.5 19.0L14.2 17.8L16.3 16.3L17.8 14.2L19.0 11.5L20.5 8.8L22.6 6.9L25.3 6.1L28.3 6.1L31.2 6.4L33.9 6.2L36.3 5.1L38.6 3.4L41.2 1.8Z"/></svg>';
const SVG_PIN = '<svg class="ov-pin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21s-6.5-5.6-6.5-11.2a6.5 6.5 0 0 1 13 0C18.5 15.4 12 21 12 21z"/><circle cx="12" cy="9.8" r="2.3"/></svg>';
const SVG_TIR = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M8 3 6 21M16 3l2 18M7.5 8h9M7 13h10M6.5 18h11"/></svg>';
const SVG_URA = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/></svg>';
const SVG_VLAK = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><rect x="6" y="3" width="12" height="14" rx="3"/><path d="M6 10h12M9 21l-2 2M15 21l2 2M9.5 20h5"/></svg>';
const SVG_BUS = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><rect x="3.5" y="3.5" width="17" height="15" rx="2.6"/><path d="M3.5 10.5h17M6.5 18.6v2.4M17.5 18.6v2.4"/></svg>';
const svgVozila = () => (isBus(state.mode) ? SVG_BUS : SVG_VLAK);

// Žeton zamude na vrhu: polna barva razreda (`oznake.md`), beseda iz
// `delayText` („3 min prej“, ne „-3“). Najtemnejši razred dobi svetlo
// besedilo, sicer ne doseže kontrasta. „Običajno“ je zgodovina, ne napoved za
// danes -- črtkan obris namesto polne barve, beseda zraven.
function zamudaCipHtml(v) {
  if (jeNadomestni()) return '<span class="ov-zam je-vr">po voznem redu</span>';
  if (v.d == null) return "";
  const z = v.z || v.d;
  const obicajno = v.znak === "običajno";
  const temna = v.z ? v.z.razred === "nad-15" : delayMin(v.d) > 15;
  // Ničla je beseda, kot v seznamu in v stavku pod vrhom: „0 min“ je uganka.
  return `<span class="ov-zam${obicajno ? " je-obicajno" : ""}${temna ? " je-temna" : ""}"
    style="--z:${delayColor(z)}">${escapeHtml(delayMin(z) === 0 ? "točno" : delayText(z))}</span>`;
}

// Beseda, od kod je številka. Brez nje je „+9 min“ videti kot meritev, prav
// pri postanku, ki ga potnik dejansko prebere.
function vrstaHtml(znak) {
  if (jeNadomestni()) return "";
  if (znak === "v živo") return '<span class="ov-vrsta je-zivo"><i aria-hidden="true"></i>v živo</span>';
  return `<span class="ov-vrsta${znak === "ocena" ? " je-ocena" : znak === "običajno" ? " je-obicajno" : ""}">${
    escapeHtml(znak)}</span>`;
}

// Tir s table SŽ ob imenu postaje; sprememba z besedo (`oznake.md`, „Tir“).
function tirCipHtml(s) {
  if (!s.tir) return "";
  return `<span class="ov-tir${s.tir_prej ? " je-spremenjen" : ""}">${SVG_TIR}tir ${escapeHtml(s.tir)}${
    s.tir_prej ? ` · prej ${escapeHtml(s.tir_prej)}` : ""}</span>`;
}

// Vreme na postanku z vrha ob uri, ko bo vozilo tam (`/weather`: model za
// celico 8 x 8 km, napoved, zato črtkan rob): ikona in temperatura, od
// „zahtevnih“ razmer beseda (`oznake.md`, „Semafor razmer“). Za prevoženi
// postanek ga ni -- tam je odgovor že zamuda. Kdor čaka zunaj, ve, ali vzame
// dežnik; kdor čaka zamudo, vidi, kakšno je vreme ob njej (vreme kot vzrok
// zamude čaka zajem, `CLAUDE.md`).
function vremeHtml(s, v) {
  const w = state.weather.get(s.stop_seq);
  if (!w || w.temp_c == null || v.mimo) return "";
  const glasno = w.severity_label === "zahtevne" || w.severity_label === "hude";
  return `<span class="ov-vreme${glasno ? " je-glasno" : ""}" title="${escapeHtml(`napoved · ${severityTitle(w)}`)}"${
    glasno ? ` style="--sev:${severityColor(w.severity_label)}"` : ""}>${weatherIconHtml(w, 15)}${
    Math.round(w.temp_c)}°${glasno ? ` · ${escapeHtml(w.severity_label)}` : ""}</span>`;
}

// Kar je na vrhu, se ob novi številki za trenutek dvigne (`je-novo`):
// osveževanje se sicer ne vidi (David, 24. 10. 2026). Odštevanje ne šteje --
// to teče samo od sebe.
function podpisVrha(vrh) {
  const { s, v } = vrh;
  return [s.stop_seq, hhmm(v.kdaj), v.d == null ? "" : delayMin(v.d), v.znak].join("|");
}

function oznakaCilja(kaj, v) {
  return kaj === "tvoj" ? "Pri tebi" : kaj === "odhod" ? "Odhod" : v.mimo ? "Na cilju" : "Cilj";
}

function odstevanjeHtml(o) {
  return o.beseda ? `<span class="ov-odst-beseda">${o.beseda}</span>`
    : `<span class="ov-odst-cez">čez</span><span class="ov-odst-n">${o.n}</span>`
      + (o.enota ? `<span class="ov-odst-e">${o.enota}</span>` : "");
}

function odstevanjeBesedilo(o) {
  return o.beseda || `čez ${o.n}${o.enota ? ` ${o.enota}` : ""}`;
}

function heroHtml(vrh, novo) {
  const { s, kaj, v, o } = vrh;
  const run = state.run;
  const sched = hhmm(s.sched_dep || s.sched_arr);
  const cas = hhmm(v.kdaj);
  const vrstice = [];
  // Zgornja meja ob zapori ali vlaku pred njim (`zapore.dodatek`): ocena
  // ostane, ker večina vlakov tam ne izgubi nič -- a lahko pride tudi tako pozno.
  const dod = !v.mimo && v.d != null && run.dodatek ? run.dodatek[s.stop_seq] : null;
  if (dod) {
    vrstice.push(`<p class="ov-dod">lahko tudi do ${hhmm(pricakovanaUra(s.sched_dep || s.sched_arr, v.d + dod))}
      (${escapeHtml(delayText(v.d + dod))})</p>`);
  }
  // Dve resnici: nepotrjena številka in bistveno drugačna novejša beseda.
  if (v.mimo && v.znak === "zadnji podatek") {
    const n = novejsaBeseda(s, run.stops);
    // Ime postaje v oklepaj, ne v stavek: sklanjati se ga ne da splošno.
    if (n) {
      vrstice.push(`<p class="ov-op">novejša beseda o vožnji: <strong>${escapeHtml(delayText(n.zamuda))}</strong>
        (${escapeHtml(lepoIme(n.name))}, ${hhmm(new Date(n.feed_ts * 1000).toISOString())})</p>`);
    }
  }
  const potnik = potnikPostanekText(s.potniki);
  if (potnik) vrstice.push(`<p class="ov-op">${escapeHtml(potnik)}</p>`);
  if (s.nadomestni_postanek) vrstice.push(`<p class="ov-op">${nadomestniPostanekHtml(s.nadomestni_postanek)}</p>`);
  return `
    <div class="ov-vrh">
      <div class="ov-odst${o.beseda ? " je-beseda" : ""}" role="img" aria-label="${escapeHtml(odstevanjeBesedilo(o))}">
        ${OBLIKA_ODST}${odstevanjeHtml(o)}
      </div>
      <div class="ov-info">
        <div class="ov-kje">${SVG_PIN}<span>${oznakaCilja(kaj, v)}</span><b>${escapeHtml(lepoIme(s.name))}</b></div>
        <div class="ov-ura${novo ? " je-novo" : ""}"><span class="ov-ura-cas">${cas}</span>${zamudaCipHtml(v)}</div>
        <div class="ov-cipi">${tirCipHtml(s)}${vrstaHtml(v.znak)}${cas !== sched
          ? `<span class="ov-vr">vozni red <s>${sched}</s></span>` : ""}${vremeHtml(s, v)}</div>
      </div>
    </div>
    ${vrstice.join("")}`;
}

// Isti vrh, stisnjen na zemljevid avtobusa (osnutek E): odštevanje, postanek,
// ura, žeton. Desni spodnji kot ostane prost za navedbo vira (i).
function kartaOdstHtml(vrh, novo) {
  const { s, kaj, v, o } = vrh;
  const sched = hhmm(s.sched_dep || s.sched_arr);
  const cas = hhmm(v.kdaj);
  return `
    <div class="ov-ko-n">${odstevanjeHtml(o)}</div>
    <div class="ov-ko-info">
      <span class="ov-ko-kje">${SVG_PIN}${kaj === "tvoj" ? "" : `${oznakaCilja(kaj, v)} · `}${escapeHtml(lepoIme(s.name))}</span>
      <span class="ov-ko-ura">${cas}${cas !== sched ? ` <s>${sched}</s>` : ""}${vremeHtml(s, v)}</span>
    </div>
    <div class="ov-ko-desno${novo ? " je-novo" : ""}">${zamudaCipHtml(v)}${vrstaHtml(v.znak)}</div>`;
}

// ---------- kje je vozilo zdaj ----------

// V stavku cela beseda („+27 min“, „2 min prej“, „točno“); kratka je za stolpec.
const zamudaVStavku = (z) => (z == null ? ""
  : ` · <b class="ov-zt" style="color:${delayColor(z)}">${escapeHtml(delayMin(z) === 0 ? "točno" : delayText(z))}</b>`);

// Kadar je poročilo potnikov na vozilu verodostojno (eden, ki se pelje, ali
// dva, ki se ujemata; `deljenje.stanje`), je izmerjeno zdaj in ima prednost
// pred feedom (David, 25. 9. 2026, za enega 11. 10.). SŽ pove višjo zamudo od
// zadnje prevožene postaje, kadar vlak stoji ali izgublja med postajama -- ta
// je trenutna (LPV 2417 16. 10. 2026).
function stanjeKjeHtml() {
  const run = state.run;
  const cur = state.current;
  // Nadomestni prevoz: feed zanje ne poroča nikoli (0 meritev v 56 vožnjah),
  // zato „ne poroča“, ne „še ni“ (`strani.md`).
  if (jeNadomestni()) return "<span>za nadomestni prevoz feed <strong>ne poroča zamud</strong> — velja vozni red</span>";
  const pp = run.potniki;
  if (pp && pp.verodostojno && pp.lat != null) {
    return `<span><span class="ov-potnik">po poročilu ${pp.n > 1 ? "potnikov" : "potnika"}</span>
      ${escapeHtml(potnikiKjeText(pp))}${pp.stoji ? ` · ${stojiMin(pp)}` : ""} ${zamudaVStavku(pp.zamuda)}</span>`;
  }
  const sz = cur && run.trenutna;
  if (sz) {
    return `<span><span class="ov-tiho">po podatkih SŽ ob ${hhmm(new Date(sz.ts * 1000).toISOString())}</span>${
      sz.proti ? ` proti postaji <b>${escapeHtml(sz.proti)}</b>` : ""} ${zamudaVStavku(sz.zamuda)}</span>`;
  }
  if (cur) {
    // Ista razlika kot pri postanku: „izmerjeno“ samo, kadar je feed vrednost
    // potrdil PO prehodu, sicer zadnji podatek s te postaje.
    const potrjen = !!(cur.zamuda && cur.zamuda.vrsta === "izmerjeno");
    return `<span><span class="ov-tiho">${potrjen ? "izmerjeno" : "zadnji podatek"}</span>
      <b>${escapeHtml(lepoIme(cur.name))}</b> <span class="ov-tiho">${hhmm(stopActualIso(cur))}</span>
      ${zamudaVStavku(stopZamuda(cur) || stopDelay(cur))}</span>`;
  }
  // Vožnja se še ni začela: pri avtobusu je lahko vozilo na prejšnji vožnji.
  const veriga = vehicleChainHtml();
  if (veriga || odhodPrvega()) return veriga;
  return `<span class="ov-tiho">${notStartedText()}</span>`;
}

// Starost, ki teče sama (`.age-live` v common.js), od trenutka po uri te
// naprave. Brez naslova `ageHtml`, ta govori o GPS.
function zivaStarost(odMs) {
  const t = Date.now();
  return `<span class="age-live" data-base="${Math.max(0, (t - odMs) / 1000)}" data-since="${t}">${
    ageText(Math.max(0, (t - odMs) / 1000), t)}</span>`;
}

const SVG_BREZ_ZVEZE = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M2 8.5a15 15 0 0 1 20 0M5.5 12a10 10 0 0 1 13 0M9 15.5a5 5 0 0 1 6 0"/><path d="M12 19h.01M3 3l18 18"/></svg>';

// Kako svež je, kar okno kaže. Šteje NOVICA o vožnji (`zadnja_beseda`), ne
// ura domnevnega prehoda: prva pove, kdaj smo nazadnje kaj izvedeli. Starost
// teče sama; okno vpraša na 10 s, zato „novica pred 8 s“ pove tudi, da se
// stran osvežuje. Brez zveze to pove in od kdaj so podatki na zaslonu.
function svezinaHtml() {
  const run = state.run;
  const cur = state.current;
  if (state.brezZveze) {
    return `<span class="ov-staro">${SVG_BREZ_ZVEZE}brez zveze · podatki od ${
      hhmm(new Date(state.odziv).toISOString())}</span>`;
  }
  if (!cur || jeNadomestni()) return "";
  const pp = run.potniki;
  if (pp && pp.verodostojno && pp.lat != null && state.potnikOb) {
    return `<span class="ov-tiho"><span class="ov-potnik">potnik</span> pred ${zivaStarost(state.potnikOb)}</span>`;
  }
  if (run.tiho_s != null && run.tiho_s > TIHO_S) {
    return `<span class="ov-staro">${SVG_URA}${escapeHtml(trajanje(run.tiho_s))} brez novic</span>`;
  }
  return state.novicaOb ? `<span class="ov-tiho">novica pred ${zivaStarost(state.novicaOb)}</span>` : "";
}

// ---------- trak vožnje ----------
//
// Od izhodišča do cilja, vozilo in tvoja postaja na njem (osnutek E za vlak:
// „zemljevida ne rabim, je itak samo tir“). Merilo je vozni red, ne število
// postaj: dolg skok brez postanka je dolg. Vlak lege nima -- med zadnjo
// prevoženo in naslednjo postajo stoji po uri, nikoli čisto na njiju. Prevoženo
// je polna črta, naprej črtkana, ker je ocena.
const TRAK_ROB = 0.22;

// Kje je vozilo po poročilu potnika (`deljenje.stanje`): na postaji ali med
// dvema, v razmerju zračnih razdalj -- trak ni zemljevid, merilo je ura.
function legaPotnikaNaTraku(pp, stops, x) {
  const i = stops.findIndex((s) => s.stop_seq === pp.stop_seq);
  if (i < 0) return null;
  const a = stops[i];
  const b = stops[i + 1];
  if (pp.pri || !b || a.lat == null || b.lat == null) return x(a);
  const da = razdaljaM([a.lat, a.lon], [pp.lat, pp.lon]);
  const db = razdaljaM([pp.lat, pp.lon], [b.lat, b.lon]);
  return x(a) + (da + db > 0 ? da / (da + db) : 0.5) * (x(b) - x(a));
}

function trakHtml() {
  const stops = state.run.stops;
  if (stops.length < 2) return "";
  const t = (s) => new Date(s.sched_dep || s.sched_arr).getTime();
  const t0 = t(stops[0]);
  const t1 = t(stops[stops.length - 1]);
  if (!(t1 > t0)) return "";
  const x = (s) => Math.min(1, Math.max(0, (t(s) - t0) / (t1 - t0)));
  const pct = (f) => `${(f * 100).toFixed(1)}%`;
  const cur = state.current;
  const pp = state.run.potniki;
  const izPotnika = !!(pp && pp.verodostojno && pp.lat != null);
  let xv = izPotnika ? legaPotnikaNaTraku(pp, stops, x) : null;
  if (xv == null && cur) {
    const i = stops.indexOf(cur);
    const nasl = stops[i + 1];
    if (!nasl) xv = 1;
    else {
      const od = new Date(vrednostNaPostanku(cur).kdaj).getTime();
      const pride = new Date(vrednostNaPostanku(nasl).kdaj).getTime();
      const del = pride > od ? (Date.now() - od) / (pride - od) : 0.5;
      xv = x(cur) + Math.min(0.85, Math.max(0.15, del)) * (x(nasl) - x(cur));
    }
  }
  const tvoj = yourStop(stops);
  const xt = tvoj ? x(tvoj) : null;
  const prvi = stops[0];
  const zadnji = stops[stops.length - 1];
  const ime = (s, razred, slog) => `<span class="ov-trak-ime ${razred}"${slog ? ` style="${slog}"` : ""}>
      <b>${escapeHtml(lepoIme(s.name))}</b><span>${hhmm(vrednostNaPostanku(s).kdaj)}</span></span>`;
  const tvojNaRobu = tvoj && (tvoj === prvi || tvoj === zadnji);
  return `<div class="ov-trak" aria-hidden="true">
      <div class="ov-trak-crta">
        <span class="ov-trak-za" style="width:${pct(xv == null ? 0 : xv)}"></span>
        <span class="ov-trak-konec je-zacetek"></span><span class="ov-trak-konec je-cilj"></span>
        ${xt != null ? `<span class="ov-trak-tvoj" style="left:${pct(xt)}"></span>` : ""}
        ${xv != null ? `<span class="ov-trak-vozilo${izPotnika ? " je-potnik" : ""}" style="left:${pct(xv)}">${svgVozila()}</span>` : ""}
      </div>
      <div class="ov-trak-imena">
        ${ime(prvi, `je-levo${tvoj === prvi ? " je-tvoj" : ""}`)}
        ${tvoj && !tvojNaRobu && xt > TRAK_ROB && xt < 1 - TRAK_ROB ? ime(tvoj, "je-tvoj je-sredina", `left:${pct(xt)}`) : ""}
        ${ime(zadnji, `je-desno${tvoj === zadnji ? " je-tvoj" : ""}`)}
      </div>
    </div>`;
}

// ---------- budilka ----------
//
// Samo v aplikaciji (`MOST`): v brskalniku gumba ni, ker nativnega alarma ni.
// Gumb je prvi v skupini dejanj in meri na postanek z vrha okna (`ciljOkna`):
// tvojo postajo, pred odhodom izhodišče, sicer cilj -- zvoni pred prihodom.

const BUD_KLJUC = "kajros:budilka";
const BUD_MINUT = [10, 15, 25, 40];
const BUD_REZERVA_S = 180;
// Ponedeljek je bit 0, nedelja bit 6 -- ista maska kot `Ponovitev.kt`.
const BUD_DNEVI = ["pon", "tor", "sre", "čet", "pet", "sob", "ned"];
const BUD_DELAVNIKI = 0b0011111;
const BUD_VSI = 0b1111111;

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

const budGumb = document.getElementById("pomoc-bud");
const SVG_ZVONEC = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 16v-5a6 6 0 0 1 12 0v5l1.5 2h-15z"/><path d="M10 20.5a2 2 0 0 0 4 0"/></svg>';

function posodobiBudilko() {
  if (!budGumb) return;
  if (!MOST || !state.run) {
    budGumb.hidden = true;
    return;
  }
  const { s } = ciljOkna();
  // **Za postanek, ki je mimo, budilke ni.** Vozilo je tu že bilo; alarm bi
  // zazvonil takoj in v prazno. Preizkušeno: nastavljena na LPP 19I štiri
  // minute po odhodu je zazvonila v isti sekundi.
  //
  // Ponavljajoča je izjema: ta ne meri na današnjo vožnjo, ampak na jutrišnjo,
  // in prav zato jo nastaviš, ko na peronu ugotoviš, da bi jo rabil.
  const obstoj = budilkeZaPostanek(s)[0];
  if (vrednostNaPostanku(s).mimo && !obstoj) {
    budGumb.hidden = true;
    return;
  }
  budGumb.hidden = false;
  budGumb.dataset.budilka = String(s.stop_seq);
  budGumb.classList.toggle("is-on", !!obstoj);
  budGumb.innerHTML = `${SVG_ZVONEC}<span class="pomoc-ime">${obstoj
    ? `ob ${hhmm(new Date(obstoj.zvoni_ob_ms).toISOString())}` : "Budilka"}</span>`;
}

function budDneviHtml(dnevi) {
  const chip = (oznaka, val, on, kaj) =>
    `<button type="button" class="bud-izbira bud-dan${on ? " is-on" : ""}"
       data-${kaj}="${val}">${oznaka}</button>`;
  return BUD_DNEVI.map((d, i) => chip(d, i, (dnevi >> i) & 1, "dan")).join("")
    + chip("delavniki", BUD_DELAVNIKI, dnevi === BUD_DELAVNIKI, "nabor")
    + chip("vsak dan", BUD_VSI, dnevi === BUD_VSI, "nabor");
}

/**
 * Zamuda, s katero budilka računa: **ista, kot jo blok „Pri tebi" pokaže.**
 *
 * `run` je za še nedosežen postanek prazen (`zamuda: null`), zato bi surova
 * vrednost pomenila nič — in budilka bi zvonila po voznem redu za vlak, ki
 * na zaslonu piše +5. Zato beremo odločitev prikaza in ne podatka pod njim.
 */
function budZamuda(s) {
  if (state.tvojPostanek === s.stop_seq && state.tvojaZamudaS != null) {
    return state.tvojaZamudaS;
  }
  const d = stopDelay(s);
  return d != null ? d : 0;
}

/**
 * Kaj bo budilka naredila. Račun je v aplikaciji (`Ura`), ne tu.
 *
 * **Dve vrstici, ker sta dve resnici.** Budilka se shrani brez zamude —
 * zamudo vpraša strežnik šele deset minut pred zvonjenjem, ker je do takrat
 * itak druga. Prva vrstica je torej ura, ki je zapisana in ki velja tudi, če
 * omrežja takrat ne bo; druga pove, kam bi se premaknila, če bo zamuda takšna
 * kot zdaj. Ena sama vrstica bi eno od tega zamolčala — in prvi zaslon te
 * strani je obljubljal 16:56, seznam budilk pa je pisal 16:51.
 */
function budNapovedHtml(s) {
  const plast = document.getElementById("budilka");
  if (!plast || !MOST || typeof MOST.napoved !== "function") return "";
  const schedIso = s.sched_dep || s.sched_arr;
  const dnevi = Number(plast.dataset.dnevi || 0);
  const skupno = {
    voznoredni_ms: new Date(schedIso).getTime(),
    minut_prej: budMinut(plast),
    rezerva_s: budRezerva() ? BUD_REZERVA_S : 0,
    omrezje: state.network,
    dnevi: dnevi,
  };
  const vprasaj = (zamuda) => {
    try {
      return JSON.parse(MOST.napoved(JSON.stringify(
        Object.assign({ zamuda_s: zamuda }, skupno))) || "{}");
    } catch (e) {
      return {};
    }
  };
  const po = vprasaj(0);
  if (!po.zvoni_ob_ms) return "";

  // Aplikacija od 12. 10. 2026 vrne tudi vožnjo, za katero bo prvič zvonila:
  // ponavljajoča, ki bi danes zazvonila v preteklost, začne naslednjič.
  // Starejša ga ne vrne in takrat velja današnja.
  const prvic = po.voznoredni_ms || skupno.voznoredni_ms;
  const drugDan = budDatum(prvic) !== budDatum(skupno.voznoredni_ms);
  const ura = hhmm(new Date(po.zvoni_ob_ms).toISOString());
  const cez = Math.round((po.zvoni_ob_ms - Date.now()) / 60000);
  // Današnja zamuda velja samo za današnjo vožnjo.
  const zamuda = drugDan ? 0 : budZamuda(s);
  const z = zamuda ? vprasaj(zamuda) : null;
  const zUra = z && z.zvoni_ob_ms ? hhmm(new Date(z.zvoni_ob_ms).toISOString()) : null;
  const dniHtml = dnevi ? ` · ${escapeHtml(imeDni(dnevi))}` : "";

  // Ura v preteklosti je bila "zvoni ob 19:01 · zdaj" -- in budilka je
  // zazvonila v pol minute (RG 18, 12. 10. 2026). Kdor tega ne hoče, mora to
  // vedeti, preden pritisne Nastavi.
  if (!drugDan && cez <= 0) {
    // Z zamudo, ki jo vozilo zdaj ima, je ura lahko še pred nami: prvo
    // preverjanje jo bo dobilo. Brez podatka zvoni takoj.
    if (z && z.zvoni_ob_ms > Date.now()) {
      return `zvoni ob <strong>${zUra}</strong> · pri zdajšnjih ${escapeHtml(delayText(zamuda))}${dniHtml}`
        + `<div class="bud-napoved-drugo">po voznem redu bi zvonilo ob ${ura} — če zamude
          takrat ne bo mogoče preveriti, zazvoni takoj</div>`;
    }
    return `zvoni <strong>takoj</strong> — ${ura} je že mimo${dniHtml}`;
  }

  let html = `zvoni ob <strong>${ura}</strong>`
    + (drugDan ? ` · prvič ${escapeHtml(budDan(po.zvoni_ob_ms))}` : ` · čez ${minLabel(cez * 60)}`)
    + dniHtml;
  if (zUra && z.zvoni_ob_ms !== po.zvoni_ob_ms) {
    html += `<div class="bud-napoved-drugo">zamudo preverim tik pred zvonjenjem —
      pri zdajšnjih ${escapeHtml(delayText(zamuda))} bi zvonilo ob ${zUra}</div>`;
  }
  return html;
}

const budDatum = (ms) => new Date(ms).toLocaleDateString("sv-SE", { timeZone: "Europe/Ljubljana" });
const BUD_DAN = new Intl.DateTimeFormat("sl-SI",
  { weekday: "short", day: "numeric", month: "numeric", timeZone: "Europe/Ljubljana" });

/** "jutri" ali "pon. 19. 10." -- kot `dan()` na domači strani. */
function budDan(ms) {
  return budDatum(ms) === budDatum(Date.now() + 86400000) ? "jutri" : BUD_DAN.format(new Date(ms));
}

/** Slovensko ime nabora dni. Isto pravilo kot `Ponovitev.ime()` v aplikaciji. */
function imeDni(dnevi) {
  if (!dnevi) return "enkratna";
  if (dnevi === BUD_VSI) return "vsak dan";
  if (dnevi === BUD_DELAVNIKI) return "vsak delavnik";
  if (dnevi === 0b1100000) return "vikend";
  return BUD_DNEVI.filter((_, i) => (dnevi >> i) & 1).join(", ");
}

/**
 * Kam vozilo pelje. `run` `headsign` nima (preverjeno: ključa ni v odgovoru),
 * zadnja postaja vožnje pa je natanko to — in v seznamu budilk je „→ Ljubljana"
 * edino, po čemer ločiš jutranji vlak od popoldanskega v isti smeri.
 */
function smerVoznje() {
  const stops = (state.run && state.run.stops) || [];
  return stops.length ? lepoIme(stops[stops.length - 1].name) : "";
}

function budMinut(plast) {
  const poMeri = document.getElementById("bud-meri");
  return poMeri && !poMeri.hidden
    ? Math.min(240, Math.max(1, Math.round(Number(poMeri.value) || 25)))
    : Number(plast.dataset.minut || 25);
}

function budRezerva() {
  return !!(document.getElementById("bud-rezerva") || {}).checked;
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
  // `cel_zaslon` pozna šele aplikacija 1.1; starejša ga ne pošlje in tam ga
  // ne smemo šteti za manjkajočega, sicer bi opozorilo viselo za vedno.
  const manjka = !dovoljenja.obvestila || !dovoljenja.tocni_alarmi
    || dovoljenja.cel_zaslon === false;

  const shranjeno = JSON.parse(
    localStorage.getItem(BUD_KLJUC) || '{"minut":25,"zbudi":true,"rezerva":true}');
  const obstoj = budilkeZaPostanek(s)[0];
  const minut = obstoj ? obstoj.minut_prej : shranjeno.minut;
  const zbudi = obstoj ? obstoj.zbudi : shranjeno.zbudi;
  const rezerva = obstoj ? obstoj.rezerva_s > 0 : shranjeno.rezerva !== false;
  // Ponavljanja si NE zapomnimo med budilkami: koliko prej hočeš zvonjenje, je
  // navada, kateri vlak voziš vsak dan, pa ni.
  const dnevi = obstoj ? (obstoj.dnevi || 0) : 0;
  const poMeri = !BUD_MINUT.includes(minut);
  const schedIso = s.sched_dep || s.sched_arr;
  const smer = smerVoznje();
  // Ista številka in ista beseda kot dva prsta višje v bloku „Pri tebi“ —
  // list, ki bi tu molčal, bi izgledal, kot da budilka o zamudi ne ve nič.
  const zamuda = state.tvojPostanek === s.stop_seq && state.tvojaZamudaS != null
    ? `${state.tvojZnak} ${delayText(state.tvojaZamudaS)}` : null;

  plast.innerHTML = `
    <div class="bud-ozadje" data-zapri="1"></div>
    <div class="bud-list" role="dialog" aria-label="Budilka">
      <div class="bud-naslov">Budilka — ${escapeHtml(s.name)}</div>
      <div class="bud-pod">${escapeHtml(TRAIN_NO)}${smer ? ` → ${escapeHtml(smer)}` : ""}
        · po voznem redu ob ${hhmm(schedIso)}${zamuda ? ` · ${escapeHtml(zamuda)}` : ""}</div>

      <div class="bud-vrsta">Zvoni koliko prej</div>
      <div class="bud-izbire" data-skupina="minut">
        ${BUD_MINUT.map((m) => `<button type="button" class="bud-izbira${
          !poMeri && m === minut ? " is-on" : ""}" data-minut="${m}">${m} min</button>`).join("")}
        <button type="button" class="bud-izbira${poMeri ? " is-on" : ""}"
                data-po-meri="1">po meri</button>
        <input type="number" class="bud-meri" id="bud-meri" min="1" max="240" step="1"
               inputmode="numeric" value="${minut}" ${poMeri ? "" : "hidden"}
               aria-label="minut prej">
      </div>

      <div class="bud-vrsta">Ponovi <span class="bud-namig">brez izbire = samo tokrat</span></div>
      <div class="bud-izbire bud-dnevi" data-skupina="dnevi">${budDneviHtml(dnevi)}</div>

      <div class="bud-vrsta">Kako</div>
      <div class="bud-izbire" data-skupina="kako">
        <button type="button" class="bud-izbira${zbudi ? "" : " is-on"}" data-zbudi="0">obvesti</button>
        <button type="button" class="bud-izbira${zbudi ? " is-on" : ""}" data-zbudi="1">zbudi me</button>
      </div>

      <label class="bud-rezerva">
        <input type="checkbox" id="bud-rezerva" ${rezerva ? "checked" : ""}>
        <span>še 3 minute rezerve</span>
      </label>

      <div class="bud-napoved" id="bud-napoved"></div>

      ${manjka ? `<button type="button" class="bud-dovoli" data-dovoli="1">
        Android budilki še ne dovoli vsega, kar rabi — uredi</button>` : ""}

      <div class="bud-dno">
        ${obstoj ? `<button type="button" class="btn-quiet bud-brisi" data-brisi="${obstoj.id}">Odstrani</button>` : ""}
        <button type="button" class="btn-quiet" data-zapri="1">Prekliči</button>
        <button type="button" class="btn" data-shrani="${s.stop_seq}">${obstoj ? "Zamenjaj" : "Nastavi"}</button>
      </div>
    </div>`;
  plast.hidden = false;
  plast.dataset.minut = String(minut);
  plast.dataset.zbudi = zbudi ? "1" : "0";
  plast.dataset.dnevi = String(dnevi);
  plast.dataset.stop = String(stopSeq);
  osveziNapoved();
}

/** Vrstica "zvoni ob ...". Prerise se ob vsaki spremembi v listu. */
function osveziNapoved() {
  const plast = document.getElementById("budilka");
  const polje = document.getElementById("bud-napoved");
  if (!plast || !polje) return;
  const s = (state.run && state.run.stops || [])
    .find((x) => x.stop_seq === Number(plast.dataset.stop));
  polje.innerHTML = s ? budNapovedHtml(s) : "";
}

function zapriBudilko() {
  const plast = document.getElementById("budilka");
  if (plast) { plast.hidden = true; plast.innerHTML = ""; }
}

function shraniBudilko(stopSeq) {
  const plast = document.getElementById("budilka");
  const s = (state.run && state.run.stops || []).find((x) => x.stop_seq === stopSeq);
  if (!plast || !s || !MOST) return;
  const minut = budMinut(plast);
  const zbudi = plast.dataset.zbudi === "1";
  const rezerva = budRezerva();
  const dnevi = Number(plast.dataset.dnevi || 0);
  localStorage.setItem(BUD_KLJUC, JSON.stringify({ minut, zbudi, rezerva }));

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
    // Zamuda gre zraven, da most ve, ali je odhod ze mimo: vozni red sam
    // tega ne pove, kadar vozilo zamuja.
    zamuda_s: budZamuda(s),
    minut_prej: minut,
    zbudi: zbudi,
    rezerva_s: rezerva ? BUD_REZERVA_S : 0,
    dnevi: dnevi,
    smer: smerVoznje(),
  }));
  if (!id) {
    // Most zavrne odhod, ki je mimo. To se zgodi le, ce je stran starejsa
    // od aplikacije -- sicer gumba za tak postanek sploh ni.
    const opomba = plast.querySelector(".bud-pod");
    if (opomba) opomba.textContent = "Ta odhod je že mimo — budilke ni mogoče nastaviti.";
    return;
  }
  zapriBudilko();
  renderRunHead();
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
    // Dnevi so preklopi, ne izbira ene med mnogimi: vsak sam zase.
    if (izbira.dataset.dan !== undefined) {
      const bit = 1 << Number(izbira.dataset.dan);
      plast.dataset.dnevi = String(Number(plast.dataset.dnevi || 0) ^ bit);
      prerisiDneve(plast);
      osveziNapoved();
      return;
    }
    if (izbira.dataset.nabor !== undefined) {
      const nabor = Number(izbira.dataset.nabor);
      // Drugi pritisk na isti nabor ga sname: sicer iz "vsak dan" ni poti nazaj
      // na enkratno, razen z odklikanjem sedmih dni.
      plast.dataset.dnevi = String(
        Number(plast.dataset.dnevi || 0) === nabor ? 0 : nabor);
      prerisiDneve(plast);
      osveziNapoved();
      return;
    }
    const skupina = izbira.parentElement;
    skupina.querySelectorAll(".bud-izbira").forEach((b) => b.classList.remove("is-on"));
    izbira.classList.add("is-on");
    const meri = document.getElementById("bud-meri");
    if (izbira.dataset.minut) {
      plast.dataset.minut = izbira.dataset.minut;
      if (meri) meri.hidden = true;
    }
    if (izbira.dataset.poMeri && meri) { meri.hidden = false; meri.focus(); }
    if (izbira.dataset.zbudi) plast.dataset.zbudi = izbira.dataset.zbudi;
    osveziNapoved();
    return;
  }
  const dovoli = ev.target.closest("[data-dovoli]");
  if (dovoli) { MOST.zahtevajDovoljenja(); zapriBudilko(); return; }
  const brisi = ev.target.closest("[data-brisi]");
  if (brisi) { MOST.odstrani(brisi.dataset.brisi); zapriBudilko(); renderRunHead(); return; }
  const shrani = ev.target.closest("[data-shrani]");
  if (shrani) shraniBudilko(Number(shrani.dataset.shrani));
});

function prerisiDneve(plast) {
  const vrsta = plast.querySelector('[data-skupina="dnevi"]');
  if (vrsta) vrsta.innerHTML = budDneviHtml(Number(plast.dataset.dnevi || 0));
}

// Minute po meri in rezerva se ne kliknejo, ampak vtipkajo -- napoved mora
// slediti tudi njima.
document.addEventListener("input", (ev) => {
  if (ev.target.id === "bud-meri" || ev.target.id === "bud-rezerva") osveziNapoved();
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
  const prev = state.chain && state.chain.prev;
  // Prejsnjo voznjo kazemo samo, dokler ta se ni zacela -- potem je vozilo tu
  // in "kje je" ni vec vprasanje.
  if (!prev || state.current != null) return "";
  const gps = prev.gps;
  // "pri" sme veljati samo za nekaj sto metrov. Dlje povemo razdaljo, in
  // sicer zracno -- vozilo je lahko onstran reke in cestna pot je daljsa.
  const ime = gps && (gps.at_stop || gps.near_stop);
  const dalec = gps && !gps.at_stop && gps.near_m != null && gps.near_m > 500;
  const kje = !gps ? null
    : !ime ? "lega znana"
    : dalec ? `zdaj ${(gps.near_m / 1000).toFixed(1).replace(".", ",")} km od
               <strong>${escapeHtml(lepoIme(ime))}</strong> (zračno)`
            : `zdaj pri postajališču <strong>${escapeHtml(lepoIme(ime))}</strong>`;
  // Zamude prejšnje vožnje ne kažemo: z njo je bil prikaz videti kot napoved
  // za to vožnjo, ta pa jo med postankom večinoma nadoknadi (glej zgoraj) --
  // in razlaga zraven je bila tri vrstice besedila.
  return `<span class="chain"><span class="chain-tag">vozilo</span>
      ${kje ? `${kje} · ` : ""}še na <a href="${chainLink(prev)}">prejšnji vožnji</a></span>`;
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
 * Golo „7“ potnik bere kot sedem ovir danes. Izmerjeno 4. 9. 2026 na
 * LPV 2250: sedem obvestil, od tega se jih je pet začelo šele 7.–19. 9.
 */
function stevecOvir(list) {
  const zdaj = Date.now();
  const pozneje = list.filter((a) => a.start_ts && a.start_ts * 1000 > zdaj).length;
  const danes = list.length - pozneje;
  return { danes, pozneje };
}

// Ovire so gumb v skupini dejanj (osnutek E): število na gumbu, seznam v
// razdelku pod skupino. Edini vir odgovora, ZAKAJ vlak zamuja -- vse drugo v
// bazi pove le koliko.
const pomocEl = document.getElementById("pomoc");
const ovireGumb = document.getElementById("pomoc-ovire");
const ovireEl = document.getElementById("train-alerts");
const SVG_OVIRA = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 9v5M12 17.5v.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/></svg>';

async function loadAlerts() {
  let list = [];
  try {
    list = await fetch(`/api/train/${ENC}/alerts`).then((r) => (r.ok ? r.json() : []));
  } catch (err) {
    list = [];
  }
  if (!list.length) {
    ovireGumb.hidden = true;
    ovireEl.innerHTML = "";
    return;
  }
  const { danes, pozneje } = stevecOvir(list);
  ovireGumb.innerHTML = `${SVG_OVIRA}<span class="pomoc-ime">${danes
    ? `${danes} ${sklon(danes, "ovira")}` : `${pozneje} pozneje`}</span>`;
  ovireGumb.setAttribute("aria-label", `Ovire na progi: ${danes} zdaj, ${pozneje} pozneje`);
  ovireGumb.hidden = false;
  ovireEl.innerHTML = `
    <div class="ov-ovire-glava">Ovire na progi <span>${danes} zdaj${pozneje ? `, ${pozneje} pozneje` : ""}</span></div>
    <div class="alert-list">${list.map((a) => `
      <div class="alert-item">
        <strong>${escapeHtml(alertTitle(a.header))}</strong>
        <div class="alert-meta">${veljavnostHtml(a)}${escapeHtml(a.effect_label || "")}${a.cause_label ? ` · ${escapeHtml(a.cause_label)}` : ""}
        ${a.url ? ` · <a href="${escapeHtml(a.url)}" target="_blank" rel="noopener">obvestilo SŽ</a>` : ""}</div>
      </div>`).join("")}</div>
    <a class="ov-ovire-vse" href="/app/ovire">vse ovire</a>`;
}

ovireGumb.addEventListener("click", () => {
  pomocEl.dataset.odprto = pomocEl.dataset.odprto === "ovire" ? "" : "ovire";
  pomocEl.dispatchEvent(new Event("pomoc"));
});
pomocEl.addEventListener("pomoc", () => {
  const odprto = pomocEl.dataset.odprto === "ovire";
  ovireEl.hidden = !odprto;
  ovireGumb.setAttribute("aria-expanded", String(odprto));
});

// Povezana skupina (M3): zunanja gumba sta zaobljena, notranji le malo. Kateri
// so vidni, se menja (budilka samo v aplikaciji, deljenje samo, ko vožnja
// vozi, ovire samo z ovirami), zato robove postavi vidnost, ne predloga.
function uredSkupino() {
  const vidni = [...pomocEl.querySelectorAll(".pomoc-gumb")].filter((g) => !g.hidden);
  vidni.forEach((g, i) => {
    g.classList.toggle("je-prvi", i === 0);
    g.classList.toggle("je-zadnji", i === vidni.length - 1);
  });
}
new MutationObserver(uredSkupino).observe(pomocEl.querySelector(".pomoc-vrsta"),
  { attributes: true, attributeFilter: ["hidden"], subtree: true });
uredSkupino();

// Glava: oznaka in kam vožnja pelje. Vlak ima vrsto in številko že s
// strežnika („LPV“ · „2002“), podnaslov je relacija. Avtobus: oznaka, kot je
// na vozilu („LPP 25“; medkrajevni prevoznik, šifre linije na avtobusu ni),
// naslov smer, podnaslov cela pot. Nadomestni prevoz se pove z besedo v
// naslovu -- kdor pride s povezave, mora takoj vedeti, da čaka avtobus.
function renderGlava(run) {
  const znacka = document.getElementById("ov-znacka");
  const ime = document.getElementById("ov-ime");
  const stops = run.stops || [];
  const prvi = stops[0];
  const zadnji = stops[stops.length - 1];
  if (run.network === "avtobus") {
    znacka.textContent = imeVoznje(run);
    znacka.className = "ov-znacka je-bus";
    const ink = AGENCY_INK[String(run.agency)] || LINE_INK;
    znacka.style.setProperty("--prevoznik", ink);
    znacka.style.setProperty("--prevoznik-tekst", besediloNaInk(ink));
    znacka.hidden = false;
    const cilj = ciljVoznje(run.headsign);
    ime.textContent = cilj ? `→ ${lepoIme(cilj)}` : "";
    headsignEl.textContent = lepoIme(run.headsign || "");
  } else {
    if (isBus(run.mode)) {
      znacka.textContent = "nadomestni prevoz";
      znacka.className = "ov-znacka je-nadomestni";
      znacka.hidden = false;
      ime.textContent = TRAIN_NO;
    }
    headsignEl.textContent = prvi && zadnji
      ? `${lepoIme(prvi.name)} → ${lepoIme(zadnji.name)}` : lepoIme(run.headsign || "");
  }
}

async function loadRun() {
  try {
    // Hkrati: veriga vozila (`block_id`) je samo pri avtobusih (SŽ je nimajo)
    // in samo pred odhodom -- potem je vozilo na tej vožnji in prejšnja ni več
    // vprašanje (`vehicleChainHtml`); z osvežitvijo na 10 s bi bila to vsakič
    // ena zahteva zastonj.
    const [, izid] = await Promise.all([
      OMREZJE === "avtobus" && !state.current ? loadChain() : null,
      fetchRunAndForecast(TRAIN_NO, URL_DATE, URL_TRIP),
    ]);
    const { run, forecast, current } = izid;
    state.mode = run.mode;
    state.network = run.network || "zeleznica";
    setVehicleNoun(vehicleNoun());     // besedo o postanku pise common.js
    state.agency = run.agency || null;
    applyNetworkWording();
    // Smer iz te vožnje. Prej iz `/api/live` po številki linije: pri mestni
    // liniji je bila prva najdena vožnja pogosto v nasprotni smeri (LPP 14
    // Bokalce → Savlje je imela v glavi „Savlje – Bokalce“, 18. 10. 2026).
    renderGlava(run);
    state.run = run;
    state.forecast = forecast;
    state.current = current;
    // Kdaj je bila zadnja novica, po uri te naprave: starost pod vrhom tako
    // teče naprej tudi med osvežitvama in ob prerisu ne skoči nazaj.
    const zdaj = Date.now();
    state.novicaOb = run.tiho_s != null ? zdaj - run.tiho_s * 1000 : null;
    state.potnikOb = run.potniki && run.potniki.starost_s != null
      ? zdaj - run.potniki.starost_s * 1000 : null;
    state.brezZveze = null;
    state.odziv = zdaj;
    renderRunHead(true);
    renderTimeline();
    loadPosition();     // lega avtobusa: GPS, sicer potnik na njem
    // Zemljevid avtobusa nastane ob prvem odgovoru, nato vsak odgovor
    // prestavi prevoženo, vozilo s prejšnje vožnje in pilulo.
    if (OMREZJE === "avtobus") pripraviKarto().then((ok) => { if (ok) posodobiKarto(); });
  } catch (err) {
    // Vožnja je že na zaslonu: neuspela osvežitev (predor, slab signal,
    // strežnik se ravno posodablja) je ne pobriše -- okno pove, da je brez
    // zveze in od kdaj so podatki. Z osvežitvijo na 10 s bi sicer vsak
    // predor pustil prazno stran.
    if (state.run && !(err && err.status === 404)) {
      if (!state.brezZveze) console.warn("osvežitev vožnje ni uspela", err);
      state.brezZveze = state.brezZveze || Date.now();
      renderRunHead();
      return;
    }
    console.error("vožnje ni bilo mogoče naložiti", err);
    runHeadEl.innerHTML = "";
    // Brez odgovora (ni omrežja) ni isto kot odgovor „ni podatkov“: zanka
    // čez 10 s poskusi znova in stran se napolni sama.
    runTimelineEl.innerHTML = err && err.status === 404
      ? `<div class="empty-state">${vehicleNoun()} s to številko ne obstaja —
         morda je povezava zastarela ali pa je številka z drugega omrežja</div>`
      : err && err.status
        ? '<div class="empty-state">za to vožnjo na ta dan ni podatkov</div>'
        : '<div class="empty-state">ni zveze s strežnikom — poskušam znova …</div>';
  }
}

// ---------- pošlji vožnjo ----------
// Kdor nekoga čaka z vlaka, mu pošlje povezavo. Predogled v Messengerju ali
// WhatsAppu pove stanje ob pošiljanju (`api._stanje_za_predogled`), besedilo
// zraven isto z uro. Kjer Web Share ni (aplikacija pred 1.13), se kopira.
// `utm_source=poslano`: sporočilne aplikacije glave `Referer` ne pošljejo,
// brez oznake je prejemnik v /admin obisk brez vira (`obisk._VIRI`).
const posljiEl = document.getElementById("poslji");

function besediloZaPoslati() {
  const naslov = posljiEl.dataset.naslov;
  const cur = state.current;
  if (!cur) return naslov;
  const m = delayMin(stopDelay(cur));
  const stanje = m === 0 ? "vozi točno" : m > 0 ? `zamuja ${m} min` : `vozi ${-m} min prej`;
  return `${naslov}: ${stanje} (zadnji podatek s postaje ${cur.name} ob ${
    hhmm(stopActualIso(cur))})`;
}

// Gumb je ikona; potrdilo („kopirano“) je oblaček pod njim, 2,5 s.
function potrdiPoslano(beseda) {
  posljiEl.dataset.potrdilo = beseda;
  posljiEl.classList.add("je-poslano");
  setTimeout(() => posljiEl.classList.remove("je-poslano"), 2500);
}

posljiEl.addEventListener("click", async () => {
  const url = new URL(location.href);
  url.searchParams.delete("postaja");   // „pri tebi“ je pošiljateljeva postaja
  url.searchParams.set("utm_source", "poslano");
  const izid = await posljiPovezavo(document.title, besediloZaPoslati(), url.toString());
  if (izid === "kopirano" || izid === "ni šlo") potrdiPoslano(izid);
});

// ---------- deli, kje je ----------
// Gumb „Deli, kje je“ v vrstici Pomagaj drugim (`deli.js`). Okno vožnje vožnjo
// pozna, zato potnik ne izbira med kandidati. Samo, ko vožnja vozi ali
// odpelje v 30 min (odločil David 11. 10. 2026): kdor gleda jutrišnji vlak
// ali tistega, ki je že na cilju, z njim nima kaj početi.
const deliEl = document.getElementById("deli");
const deliGumb = document.getElementById("pomoc-deli");
const DELI_PRED_MS = 30 * 60 * 1000;
const DELI_PO_CILJU_MS = 10 * 60 * 1000;

function voziAliKmalu(run) {
  const stops = run.stops || [];
  const prvi = stops[0], zadnji = stops[stops.length - 1];
  const od = prvi && (prvi.sched_dep || prvi.sched_arr);
  const doIso = zadnji && (zadnji.sched_arr || zadnji.sched_dep);
  if (!od || !doIso) return false;
  const zamuda = state.current ? (stopDelay(state.current) || 0) * 1000 : 0;
  const zdaj = Date.now();
  return zdaj >= new Date(od).getTime() - DELI_PRED_MS
    && zdaj <= new Date(doIso).getTime() + Math.max(zamuda, 0) + DELI_PO_CILJU_MS;
}

function posodobiDeli() {
  const run = state.run;
  if (!deliEl || !run || !run.trip_id) return;
  const d = deliEl.dataset;
  const nova = d.trip !== run.trip_id;
  Object.assign(d, { trip: run.trip_id, dan: run.service_date, omrezje: state.network,
                     mode: run.mode || "", st: run.train_no || TRAIN_NO,
                     smer: run.headsign || "", prevoznik: run.agency || "" });
  // Deljenje, ki teče (deliš ali hvala), ostane, tudi ko vožnja konča.
  if (deliGumb) deliGumb.hidden = !deliEl.classList.contains("je-odprt") && !voziAliKmalu(run);
  if (nova) deliEl.dispatchEvent(new Event("deli-voznja"));
}

// Razdelek o zasedenosti (`zasedenost.js`) dobi vožnjo in postajo od okna:
// postajo „pri tebi“, sicer tisto, do katere vozilo pride naslednjo, pred
// odhodom izhodišče. Kdor je ostal na postaji, pride s table, ta pa postajo nosi.
const zasEl = document.getElementById("zasedenost");

function posodobiZasedenost() {
  const run = state.run;
  if (!zasEl || !run || !run.trip_id) return;
  const tvoja = yourStop(run.stops);
  const meja = run.last_measured_seq;
  // Na cilju se ne vstopa: po zadnji meritvi na koncu ostane predzadnja.
  const naslednja = meja == null ? null
    : run.stops.find((s) => s.stop_seq > meja && s !== run.stops[run.stops.length - 1])
      || run.stops[run.stops.length - 2];
  const postaja = (tvoja || naslednja || run.stops[0]).name;
  const d = zasEl.dataset;
  const nova = d.trip !== run.trip_id || d.dan !== run.service_date || d.privzeta !== postaja;
  Object.assign(d, { trip: run.trip_id, dan: run.service_date, privzeta: postaja });
  if (nova) zasEl.dispatchEvent(new Event("zas-voznja"));
}

// `nova` = izris ob novem odgovoru (ne ob tiktakanju odštevanja): samo takrat
// se sprememba na vrhu pokaže.
function renderRunHead(nova) {
  const run = state.run;
  if (!run) return;
  posljiEl.hidden = false;
  posodobiDeli();
  posodobiZasedenost();
  const vrh = vrhOkna();
  const podpis = podpisVrha(vrh);
  const novo = !!(nova && state.vrh && state.vrh !== podpis);
  if (nova) state.vrh = podpis;
  runHeadEl.innerHTML = heroHtml(vrh, novo);
  kartaOdstEl.innerHTML = kartaOdstHtml(vrh, novo);
  trakEl.innerHTML = trakHtml();
  // Na cilju vse pove vrh; „8 h brez novic“ pod njim bi bil alarm brez razloga.
  const naCilju = state.current === run.stops[run.stops.length - 1];
  stanjeKjeEl.parentElement.hidden = naCilju;
  stanjeKjeEl.innerHTML = naCilju ? "" : stanjeKjeHtml();
  stanjeSvezEl.innerHTML = naCilju ? "" : svezinaHtml();
  posodobiBudilko();
  document.getElementById("train-opozorila").innerHTML = opozorilaHtml(run.opozorila);
}

// Odštevanje in lega vlaka na traku tečeta tudi, ko novih podatkov ni.
setInterval(() => {
  if (state.run && document.visibilityState !== "hidden") renderRunHead();
}, 15000);

// Zapora tira ali vlak pred njim, ki je izgubil čas (`zapore.py`). Odprto, ne
// zloženo kot obvestila SŽ: velja za to vožnjo danes, ne za progo na splošno.
function opozorilaHtml(list) {
  if (!list || !list.length) return "";
  return `<div class="alert-box">
      <div class="alert-head">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M12 9v5M12 17.5v.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"></path>
        </svg>
        Možna dodatna zamuda
      </div>
      <div class="alert-list">${list.map((o) => `
        <div class="alert-item">${escapeHtml(opozoriloBesedilo(o, false))}</div>`).join("")}</div>
    </div>`;
}

// ---------- postanki na črti ----------
//
// Osnutek E (ikone in črta iz B): debela črta, prevoženo polno in sivo, naprej
// črtkano -- ocena, ne meritev --, vozilo med zadnjo prevoženo in naslednjo
// postajo. Prevožene so zložene (odgovor na drugo vprašanje, „kako je bilo“),
// razen zadnje, ki pove, od kod je številka. Brez ločilne vrstice „naprej po
// progi — ocena“: to pove črtkana črta in beseda na vrhu.

// Žeton ničle je beseda, kot na Mojih poteh: „0“ brez enote je uganka.
const zamudaKratka = (z) => (delayMin(z) === 0 ? "točno" : delayText(z, true));

function cipHtml(z, razred) {
  return `<span class="ov-p-zam ${razred}" style="--z:${delayColor(z)}">${escapeHtml(zamudaKratka(z))}</span>`;
}

const casHtml = (cas, sched) => `<span class="ov-p-cas"><b>${cas}</b>${cas !== sched ? `<s>${sched}</s>` : ""}</span>`;

// Dolg postanek pred potnikom: na čem ocena stoji. Model računa, da bo vlak
// postanek skrajšal; koliko ta vlak tam res stoji, kadar zamuja, pove zgodovina
// (`typical_dwell_s`). Kratko, ker je v vrstici.
function postanekVoznegaReda(s) {
  if (!s.sched_dwell_s || s.sched_dwell_s < DWELL_SHOW_S) return "";
  const red = Math.round(s.sched_dwell_s / 60);
  return s.typical_dwell_s == null ? `postanek ${red} min`
    : `postanek ${red} min · z zamudo običajno ${Math.round(s.typical_dwell_s / 60)}`;
}

function vrsticaHtml(s, o) {
  const run = state.run;
  const schedIso = s.sched_dep || s.sched_arr;
  const sched = hhmm(schedIso);
  const opombe = [];
  if (s.tir) opombe.push(tirHtml(s.tir, s.tir_prej));
  let cas;
  let cip = "";
  if (o.mimo) {
    // Prikazana ura = vozni red + zaokrožena minuta žetona (`pricakovanaUra`).
    if (stopActualIso(s) && !jeNeskladen(s)) {
      const d = stopDelay(s);
      cas = casHtml(hhmm(d != null && schedIso ? pricakovanaUra(schedIso, d) : stopActualIso(s)), sched);
      cip = cipHtml(stopZamuda(s) || d, "je-meritev");
      const split = dwellSplit(s);
      if (split) opombe.push(escapeHtml(dwellNoteHtml(split)));
    } else {
      // „Brez meritve“ in „podatek si nasprotuje“ nista isto: prvo pomeni, da
      // ni prišlo nič, drugo, da je prišlo nemogoče.
      cas = casHtml(sched, sched);
      opombe.push(jeNeskladen(s) ? "ura si nasprotuje" : "brez meritve");
    }
  } else {
    const v = vrednostNaPostanku(s);
    cas = casHtml(hhmm(v.kdaj), sched);
    if (v.d != null && !jeNadomestni()) {
      cip = cipHtml(v.z || v.d, v.znak === "običajno" ? "je-obicajno"
        : v.znak === "v živo" ? "je-zivo" : "je-ocena");
    }
    // Kadar prevoznik napove več od naše ocene, je njegova številka skoraj
    // točna (MAE 0,21 min proti 2,66) -- povej, da je njegova. Enkrat, kjer se
    // začne (`seznamHtml`): pri mestnem LPP je to sicer vsaka vrstica.
    if (o.napovedPrevoznika) opombe.push("napoved prevoznika");
    const dwell = postanekVoznegaReda(s);
    if (dwell) opombe.push(dwell);
    const dod = v.d != null && run.dodatek ? run.dodatek[s.stop_seq] : null;
    if (dod) opombe.push(`<span class="ov-p-do">lahko do ${escapeHtml(delayLabel(v.d + dod))}</span>`);
    // Razmere naprej samo, kadar so zahtevne ali hude: mirno vreme v vsaki
    // vrstici je šum ob številki, zaradi katere je človek tu.
    const w = state.weather.get(s.stop_seq);
    if (w && (w.severity_label === "zahtevne" || w.severity_label === "hude")) opombe.push(stopWeatherHtml(w, true));
  }
  const potnik = potnikPostanekText(s.potniki);
  if (potnik) opombe.push(escapeHtml(potnik));
  return `<div class="ov-p${o.mimo ? " je-mimo" : ""}${o.tvoj ? " je-tvoj" : ""}">
      <span class="ov-p-crta" data-gor="${o.gor}" data-dol="${o.dol}"><i class="ov-p-pika"></i></span>
      <span class="ov-p-ime"><span class="ov-p-naziv">${escapeHtml(lepoIme(s.name))}</span>${
        opombe.length ? `<span class="ov-p-op">${opombe.join(" · ")}</span>` : ""}${
        s.nadomestni_postanek ? nadomestniPostanekHtml(s.nadomestni_postanek) : ""}</span>
      ${cas}
      ${cip || '<span class="ov-p-zam je-prazno"></span>'}
    </div>`;
}

// Vozilo na črti: med zadnjo prevoženo in naslednjo. Kje točno, pove potnik
// na vozilu ali SŽ („proti postaji“); sicer samo, kam pelje.
function voziloVrsticaHtml(nasl) {
  const run = state.run;
  const pp = run.potniki;
  const bus = isBus(state.mode) && state.network === "avtobus";
  // Lega od potnika v barvi deljenja (indigo), kot povsod, kjer jo kažemo.
  const izPotnika = !!(pp && pp.verodostojno && pp.lat != null && potnikiKjeText(pp));
  const kje = izPotnika ? potnikiKjeText(pp)
    : run.trenutna && run.trenutna.proti ? `proti postaji ${run.trenutna.proti}`
    : `proti ${bus ? "postajališču" : "postaji"} ${lepoIme(nasl.name)}`;
  return `<div class="ov-p ov-vozilo${izPotnika ? " je-potnik" : ""}">
      <span class="ov-p-crta" data-gor="za" data-dol="naprej"><i class="ov-vozilo-ikona">${svgVozila()}</i></span>
      <span class="ov-vozilo-kje">${escapeHtml(kje)}${izPotnika ? " · po poročilu potnika" : ""}</span>
    </div>`;
}

// „10 prevoženih“: postaja je ženskega spola, postajališče srednjega.
function prevozenihBesedilo(n) {
  const obl = state.network === "avtobus"
    ? ["prevoženo", "prevoženi", "prevožena", "prevoženih"]
    : ["prevožena", "prevoženi", "prevožene", "prevoženih"];
  const m = n % 100;
  return `${n} ${m === 1 ? obl[0] : m === 2 ? obl[1] : m === 3 || m === 4 ? obl[2] : obl[3]}`;
}

const SVG_NAVZDOL = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>';

function seznamHtml() {
  const stops = state.run.stops;
  const cur = state.current;
  const tvoj = yourStop(stops);
  const curSeq = cur ? cur.stop_seq : null;
  const prevozene = curSeq == null ? [] : stops.filter((s) => s.stop_seq < curSeq);
  const vidne = [...(state.prevozene ? prevozene : []),
                 ...stops.filter((s) => curSeq == null || s.stop_seq >= curSeq)];
  const jeZa = (s) => curSeq != null && s.stop_seq <= curSeq;
  const vrstice = [];
  let odPrevoznika = false;
  vidne.forEach((s, i) => {
    const nasl = vidne[i + 1];
    const gor = i > 0 || s !== stops[0] ? (jeZa(s) ? "za" : "naprej") : "nic";
    const dol = !nasl ? "nic" : jeZa(nasl) || s.stop_seq === curSeq ? "za" : "naprej";
    const f = jeZa(s) ? null : vrednostNaPostanku(s).f;
    const op = !!(f && f.from_operator);
    vrstice.push(vrsticaHtml(s, { gor, dol, mimo: jeZa(s), tvoj: s === tvoj, napovedPrevoznika: op && !odPrevoznika }));
    odPrevoznika = op;
    if (s.stop_seq === curSeq && nasl) vrstice.push(voziloVrsticaHtml(nasl));
  });
  const naslov = state.network === "avtobus" ? "Postajališča" : "Postanki";
  const gumb = prevozene.length
    ? `<button type="button" class="ov-prevozene" data-prevozene aria-expanded="${state.prevozene}">${
      state.prevozene ? "skrij prevožene" : prevozenihBesedilo(prevozene.length)}${SVG_NAVZDOL}</button>` : "";
  return `<div class="ov-p-glava"><h2 class="ov-p-naslov">${naslov}</h2>${gumb}</div>
    <div class="ov-seznam">${vrstice.join("")}</div>`;
}

runTimelineEl.addEventListener("click", (ev) => {
  if (!ev.target.closest("[data-prevozene]")) return;
  state.prevozene = !state.prevozene;
  renderTimeline();
});

// Navedba vira mora povedati, CIGAV podatek je na zaslonu -- doslej je pisalo
// "IJPP prek NAP" tudi pod mestnim LPP, ki v IJPP-ju sploh ni. Vozni red
// mestnih linij je LPP-jev lastni GTFS, zivi prihodi pa pridejo z
// `data.lpp.si` in takrat mora biti to zapisano, ne skrito za DERP. Zamude in
// tir vlaka beremo naravnost s strani SŽ (`zamude_sz.py`, `peroni.py`);
// nadomestni prevoz ima samo vozni red.
function viriHtml(run) {
  if (run.network === "zeleznica" && !isBus(run.mode)) {
    return "vozni red IJPP prek NAP (CC BY-SA 4.0), zamude in tir SŽ";
  }
  if (run.agency === "marprom") {
    return "vozni red in lege vozil Marprom (vozniredi.marprom.si), zamude iz leg";
  }
  if (run.agency === "kranj") {
    return "vozni red Mestne občine Kranj (Ridango), lege prek DERP, zamude iz leg";
  }
  if (run.agency !== "lpp") {
    return "IJPP prek NAP (CC BY-SA 4.0), obdelava DERP";
  }
  const zivo = run.zivi_vir ? ", živi prihodi data.lpp.si" : "";
  return `LPP (avl.lpp.si), obdelava DERP${zivo}`;
}

function renderTimeline() {
  const run = state.run;
  if (!run) return;
  // Vira sta navedena tu in ne v opombi nad postanki: navedba je pogoj rabe
  // (IJPP CC BY-SA 4.0, Open-Meteo CC BY 4.0), ne razlaga za potnika.
  runTimelineEl.innerHTML = seznamHtml() + vozovnicaHtml(run)
    + `<div class="detail-foot">${escapeHtml(run.service_date)} · ${run.stops.length} ${sklon(run.stops.length, "postanek")}
      · ${viriHtml(run)} · vreme Open-Meteo (CC BY 4.0)</div>`;
}

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

// ---------- zemljevid ene voznje ----------
// "Kje je zdaj" je pri avtobusu prvo vprasanje in nanj zna odgovoriti samo
// GPS, zato ima avtobus zemljevid na vrhu okna, z lego ali brez nje (osnutek
// E). Vlak ga nima: tir ne gre drugam, kje je vlak, pove trak.
//
// Zemljevid je MapLibre sam, kot veliki zemljevid in obe strani poti
// (`pot_karta.js`): od blizu se kamera nagne in stavbe se dvignejo.
//
// Knjiznica in njen slog se naložita samo v oknu avtobusa: okno vlaka ne
// vleče 300 kB, ki jih ne bo nikoli uporabilo.

let slogMapLibre = null;

// Slog mora biti v glavi, preden zemljevid nastane -- sicer platno dobi
// napacno velikost (glej `pkNaloziMapLibre`). In PRED nasimi: oblacki v
// dashboard.css imajo isto specificnost kot MapLibrovi in zmaga poznejsi.
function naloziSlogMapLibre() {
  if (!slogMapLibre) {
    slogMapLibre = new Promise((ok) => {
      const css = document.createElement("link");
      css.rel = "stylesheet";
      css.href = `${MAPLIBRE_POT}/maplibre-gl.css`;
      // Brez sloga zemljevid se vedno rise, le kontrole so nerazporejene.
      css.onload = ok;
      css.onerror = ok;
      document.head.insertBefore(css, document.head.querySelector('link[rel="stylesheet"]'));
    });
  }
  return slogMapLibre;
}

// Trasa avtobusa in njegova lega gresta na pot ob odprtju, vzporedno z `/run`.
// Prej so lega, knjižnica in trasa čakale druga na drugo za `/run`: vozilo je
// prišlo na zemljevid 0,5-0,8 s za postanki (arwen, presoja 18. 10. 2026).
// Avtobus ima zemljevid vedno (osnutek E), zato gre knjižnica na pot takoj,
// ne šele z lego.
//
// Obljuba trase stoji od začetka: zanka lege isti odgovor zna prebrati prej,
// zemljevid je tedaj traso vprašal še enkrat (dvojna zahteva ob prvem odprtju,
// arwen 19. 10. 2026).
const zgodaj = { lega: null, trasa: null };
if (OMREZJE === "avtobus" && URL_TRIP) {
  naloziSlogMapLibre();
  pkNaloziMapLibre();
  zgodaj.trasa = fetch(`/api/trip/${encodeURIComponent(URL_TRIP)}/shape`).catch(() => null);
  if (!URL_DATE) zgodaj.lega = fetch(`/api/vehicles?trip=${encodeURIComponent(URL_TRIP)}`);
}

const runMap = { map: null, ml: null, marker: null, trasa: null, cums: null,
                 postaje: null, v: null, since: 0, loc: null, nastaja: null,
                 avto3d: null, lega: null, vir: null, veriga: null, prvaLega: null, sledi: true };

// ---------- ocena lege med dvema meritvama ----------
// Pravilo in meritve so v common.js (`ocenaNaTrasi`): isto oceno ima veliki
// zemljevid za vlak s potnikom in za izbrani avtobus z izmerjeno hitrostjo.
const ocenjenaLega = (v, starostS) => ocenaNaTrasi(runMap, v, starostS);

// Pol dolzine NARISANEGA vozila v metrih: tetiva, po kateri gleda vozilo na
// oceni (`smerNaOceni` v common.js, tam meritev). Model je povecan (pri z15
// zgibni meri 89 m), ikona ~24 px.
function polVozila(v) {
  const z = runMap.map.getZoom();
  return !run3D()
    ? 12 * (40075016.686 * Math.cos(v.lat * Math.PI / 180)) / (512 * 2 ** z)
    : (avtoDolzina(modelVozila(v)) / 2) * avtoPovecava(z);
}

// Ista oblika in ista barva kot na velikem zemljevidu: avtobus v barvi
// prevoznika. Do 4. 10. 2026 je bilo vozilo tu svetlo modro (`ESTIMATE_COLOR`,
// "tu meritve ni") -- odkar je Arriva na velikem zemljevidu modra, se je LPP
// bral kot Arriva. Da vozilo stoji na OCENI lege in ne na meritvi, zdaj
// povesta prosojnost in crtkan svetel obris; meritev je rdeca pika. Pod
// crtkanim obrisom je temen, da se loci od podlage.
function inkVozila(v) {
  const ag = v && v.agency === "lpp" ? "1118" : v && v.agency;
  return AGENCY_INK[ag] || BUS_INK;
}

function busSvg(moving, ink) {
  const s = 30;
  const telo = 'x="7.5" y="2.5" width="9" height="19" rx="3.2"';
  return `<svg width="${s}" height="${s}" viewBox="0 0 24 24" aria-hidden="true">
      <rect ${telo} fill="${ink}" fill-opacity="${moving ? 0.55 : 0.32}"/>
      ${obrisOcene(telo)}
      <path d="M9.4 5.9 Q12 4.8 14.6 5.9 L14.6 7.5 Q12 6.8 9.4 7.5 Z"
            fill="#e9f4ff" fill-opacity="0.9"/>
    </svg>`;
}

const RUN_PRAZNO = { type: "FeatureCollection", features: [] };

function runVir(id, features) {
  const v = runMap.map && runMap.map.getSource(id);
  if (v) v.setData({ type: "FeatureCollection", features });
}

// Ime na dotik in po petih sekundah proc -- isto kot `pot_karta.js`. Dotik
// zadene, kar je v 12 px od prsta, kot na velikem zemljevidu: pika postaje
// je manjsa od prsta.
const RUN_ZADETEK_PX = 12;
const RUN_IMENA = ["run-gps", "run-tvoja", "k-jaz", "run-postaje", "run-postaje-avtobusne",
                   "run-postaje-znak"];

function runImeNaDotik() {
  const { map, ml } = runMap;
  let oblacek = null;
  const zadetek = (p) => map.queryRenderedFeatures(
    [[p.x - RUN_ZADETEK_PX, p.y - RUN_ZADETEK_PX], [p.x + RUN_ZADETEK_PX, p.y + RUN_ZADETEK_PX]],
    { layers: RUN_IMENA.filter((id) => map.getLayer(id)) });
  const ime = (f) => {
    if (f.layer.id === "k-jaz") {
      const acc = runMap.loc && runMap.loc.acc;
      return acc ? `tvoja lega (±${Math.round(acc)} m)` : "tvoja lega";
    }
    return f.properties.ime;
  };
  map.on("click", (e) => {
    // Prednost po vrstnem redu v RUN_IMENA: meritev pred postajo, ker pika
    // lege pogosto lezi na postajaliscu.
    const vsi = zadetek(e.point);
    const f = RUN_IMENA.map((id) => vsi.find((x) => x.layer.id === id)).find(Boolean);
    if (!f || !ime(f)) return;
    if (oblacek) oblacek.remove();
    oblacek = new ml.Popup({ closeButton: false, className: "kajros-tooltip", offset: 8 })
      .setLngLat(f.geometry.coordinates).setText(ime(f)).addTo(map);
    const moj = oblacek;
    setTimeout(() => moj.remove(), NAME_MS);
  });
  map.on("mousemove", (e) => {
    map.getCanvas().style.cursor = zadetek(e.point).length ? "pointer" : "";
  });
}

// Plasti okna voznje gredo POD plasti `pot_karta.js`: te nosijo lastno lego,
// ki mora ostati nad traso.
const RUN_POD = "k-voznja-obroba";

// Pot naprej v barvi omrežja, kot črta postankov pod zemljevidom (osnutek E;
// pri avtobusu zelena). Prej oranžna kot izbrano vozilo na velikem zemljevidu
// -- tam jo loči od drugih poti, tu je pot ena sama.
const barvaPoti = () => getComputedStyle(document.body).getPropertyValue("--accent-lit").trim()
  || IZBRANA_INK;

async function ustvariRunMap() {
  const wrap = document.getElementById("run-map-wrap");
  const el = document.getElementById("run-map");
  // Trasa po cesti gre na pot pred knjižnico, ne za njo.
  const zacetaTrasa = state.run.trip_id === URL_TRIP ? zgodaj.trasa : null;
  zgodaj.trasa = null;
  const trasaP = Promise.resolve(zacetaTrasa)
    .then((r) => r || fetch(`/api/trip/${encodeURIComponent(state.run.trip_id)}/shape`))
    .then((r) => (r.ok ? r.json() : null))
    .then((d) => (d ? d.points : null))
    .catch(() => null);           // brez trase narisemo postajalisca
  // MapLibre izmeri okvir ob nastanku; skrit okvir meri 0 x 0.
  wrap.hidden = false;
  await naloziSlogMapLibre();
  // Zemljevid je ELEMENT na strani, ne stran, zato geste, ki bi ukradle
  // pomikanje strani, tu ne veljajo: en prst in kolesce pomikata stran, dva
  // prsta in Ctrl + kolesce zemljevid. Vlecenje z misko strani ne pomika in
  // ostane zemljevidu. Brez dodatnih imen: okvir gleda eno vožnjo, imena ulic
  // so v podlagi sami. Prvi pogled postavi `zacetniPogled`.
  const prvi = state.run.stops.find((s) => s.lat != null);
  const v = runMap.v;
  const sredisce = v ? [v.lat, v.lon] : prvi ? [prvi.lat, prvi.lon] : [46.05, 14.51];
  const k = await pkUstvari(el, { sredisce, zoom: 14, dodatnaImena: false, sodelovanje: true });
  if (!k) return false;
  const { map, ml } = k;
  runMap.map = map;
  runMap.ml = ml;
  // Mali zemljevid se ne vrti: sever, ki ga dva prsta nehote zasučeta, je v
  // okvirju ene vožnje samo zmeda, kompasa za vrnitev pa osnutek nima.
  map.dragRotate.disable();
  map.touchZoomRotate.disableRotation();
  map.on("dragstart", () => { runMap.sledi = false; });
  // Gumba + in − samo pod miško: na telefonu približujeta dva prsta (osnutek E
  // ima ob zemljevidu le „čez celo stran“ in „moja lega“).
  if (matchMedia("(pointer: fine)").matches) {
    map.addControl(new ml.NavigationControl({ showCompass: false }), "top-right");
    wrap.classList.add("ima-povecavo");
  }
  // Navedba vira je v okvirju 260 px odprta pokrila spodnjo osmino, cez traso.
  // Zlozena ostane gumb (i), kot je na drugih zemljevidih po prvem premiku.
  const navedba = el.querySelector(".maplibregl-ctrl-attrib");
  navedba?.classList.remove("maplibregl-compact-show");
  // Gumb (i) gre zgoraj desno nad naše gumbe: spodaj leži odštevanje čez vso
  // širino (osnutek E) -- ob njem je bilo na 360 px ime postanka odrezano.
  // Navedba mora ostati vidna, je pogoj rabe podlage.
  const desnoZgoraj = el.querySelector(".maplibregl-ctrl-top-right");
  if (navedba && desnoZgoraj) desnoZgoraj.prepend(navedba);

  // Trasa po cesti. Kadar je ni, ostane crta skozi postajalisca -- ta ni pot
  // in mora biti videti drugace (crtkano).
  const trasa = await trasaP;
  // `trasa` je seznam KOSOV, ne tock: uvoz jo razreze tam, kjer je v GTFS
  // razmik nad kilometer. Pogoj `trasa.length > 1` je bil napisan se za
  // ravno listo tock in je zato izlocil vsako enodelno traso -- 2 706 od
  // 2 897 oblik, torej 93 %. Proga se ni risala skoraj nikoli.
  const kosi = (trasa || []).filter((kos) => kos && kos.length > 1);
  if (kosi.length) {
    // Za projekcijo vzamemo najdaljsi kos -- vozilo je skoraj vedno na njem.
    const kos = kosi.reduce((a, b) => (b.length > a.length ? b : a));
    runMap.trasa = kos;
    runMap.cums = kumulative(kos);
    runMap.kosi = kosi;
    runMap.kosIdx = kosi.indexOf(kos);
  }
  const postaje = (state.run.stops || []).filter((s) => s.lat != null && s.lon != null);
  const pts = postaje.map((s) => [s.lat, s.lon]);
  if (runMap.trasa) runMap.postaje = postankiNaTrasi(runMap.trasa, runMap.cums, postaje);

  const crte = kosi.length ? kosi.map((kos) => pkCrta(kos, { vrsta: "trasa" }))
    : pts.length > 1 ? [pkCrta(pts, { vrsta: "skozi" })] : [];
  for (const id of ["run-trasa", "run-postaje", "run-postaje-nadstreski", "run-tvoja", "run-gps"]) {
    map.addSource(id, { type: "geojson", data: RUN_PRAZNO });
  }
  const okroglo = { "line-join": "round", "line-cap": "round" };
  // Trasa na tleh: od blizu široka kot cesta (`sirinaM`), pod stavbami -- nad
  // njimi je bila v nagibu narisana čez hišo, za katero leži ulica. Pike in
  // vozilo ostanejo nad stavbami (`RUN_POD`).
  const naTleh = map.getLayer("stavbe-3d") ? "stavbe-3d" : RUN_POD;
  const pot = barvaPoti();
  map.addLayer({ id: "run-trasa-obroba", type: "line", source: "run-trasa", layout: okroglo,
                 filter: ["==", ["get", "vrsta"], "trasa"],
                 paint: { "line-color": "#0f1115", "line-width": sirinaM(7.7, [[10, 6], [15, 6]]),
                          "line-opacity": 0.85 } },
               naTleh);
  // Prevoženo sivo (`narisiRunTraso`), naprej v barvi omrežja.
  const za = ["==", ["get", "del"], "za"];
  map.addLayer({ id: "run-trasa", type: "line", source: "run-trasa", layout: okroglo,
                 filter: ["==", ["get", "vrsta"], "trasa"],
                 paint: { "line-color": ["case", za, ZA_INK, pot],
                          "line-width": sirinaM(6.5, [[10, 3], [15, 3]]),
                          "line-opacity": ["case", za, 0.55, 0.95] } },
               naTleh);
  map.addLayer({ id: "run-skozi", type: "line", source: "run-trasa",
                 filter: ["==", ["get", "vrsta"], "skozi"],
                 paint: { "line-color": pot, "line-width": 2.5, "line-opacity": 0.7,
                          "line-dasharray": [2, 2] } },
               naTleh);
  // Pike so bile nekoc neme tocke na zemljevidu. Ime ob dotiku je edini
  // nacin, da se izve, katera postaja to je -- trajne oznake bi na mestni
  // liniji zakrile progo pod sabo. Kot na črti pod zemljevidom: naprej obroč
  // v barvi poti, prevoženo sivo. Od blizu nadstrešek ali znak namesto pike,
  // kot na velikem zemljevidu (`slojiPostajalisc`); pika ostane nevidna, ker
  // jo zadene prst.
  const mimo = ["==", ["get", "mimo"], 1];
  map.addLayer({ id: "run-postaje", type: "circle", source: "run-postaje",
                 paint: { "circle-radius": ["case", mimo, 3.4, 4.2],
                          "circle-color": ["case", mimo, ZA_INK, "#0f1115"],
                          "circle-stroke-color": ["case", mimo, "#0f1115", pot],
                          "circle-stroke-width": ["case", mimo, 1.4, 2.4],
                          "circle-opacity": PIKA_POD_3D, "circle-stroke-opacity": PIKA_POD_3D,
                          "circle-pitch-alignment": "map" } },
               RUN_POD);
  slojiPostajalisc(map, { vir: "run-postaje", nadstresek: "run-nadstresek",
                          postaja: "run-postaje-avtobusne", znak: "run-postaje-znak" });
  // Postaja, na kateri stoji potnik, mora biti vidna -- brez nje je to
  // zemljevid o vozilu in ne o njegovi poti. Zato z imenom, trajno: bela z
  // obročem v barvi poti, kot v osnutku.
  map.addLayer({ id: "run-tvoja", type: "circle", source: "run-tvoja",
                 paint: { "circle-radius": 7, "circle-color": "#f4f6fa",
                          "circle-stroke-color": pot, "circle-stroke-width": 3,
                          "circle-pitch-alignment": "map" } },
               RUN_POD);
  map.addLayer({ id: "run-tvoja-ime", type: "symbol", source: "run-tvoja",
                 layout: { "text-field": ["get", "ime"], "text-font": ["Noto Sans Bold"],
                           "text-size": 13, "text-anchor": "left", "text-offset": [1.1, 0],
                           "text-allow-overlap": true },
                 paint: { "text-color": "#f4f6fa", "text-halo-color": "#0f1115",
                          "text-halo-width": 1.6 } },
               RUN_POD);
  // Zadnja RESNICNA meritev je edina trdna tocka na tem zemljevidu, zato je
  // polna in vidna -- ne bleda. Rdeca s svetlim obrocem, ki jo loci od poti
  // pod njo. Rdeca ni iz nobene lestvice -- ne iz zamud in ne iz razmer --
  // zato tu ne more pomeniti nicesar drugega. Rise se VEDNO: kadar vozilo
  // stoji, jo oblika vozila pokrije. Plast je zadnja med nasimi, da je 3 px
  // siroka trasa ne prereze.
  map.addLayer({ id: "run-gps", type: "circle", source: "run-gps",
                 paint: { "circle-radius": 5.5, "circle-color": MERITEV_INK,
                          "circle-stroke-color": "#e7eaf0", "circle-stroke-width": 2,
                          "circle-stroke-opacity": 0.95, "circle-pitch-alignment": "map" } },
               RUN_POD);

  // Od blizu model v 3D, kot na velikem zemljevidu: zemljevid se tu nagne
  // enako, ploska ikona pa je med dvignjenimi stavbami ostala ploska. Model
  // je v barvah prevoznika, kot na velikem zemljevidu (do 4. 10. 2026 v barvi
  // ocene); da stoji na oceni, pove podnapis „ocena · GPS pred …“.
  runMap.avto3d = avtobusi3D({ id: "run-avtobus-3d", inki: { ...AGENCY_INK, drugi: BUS_INK },
                               vidna: run3D, povecava: avtoPovecava });
  map.addLayer(runMap.avto3d.plast, RUN_POD);
  map.on("zoom", () => postavi3D());

  runVir("run-trasa", crte);
  runMap.postajeOdBlizu = postaje;
  postaviRunNadstreske();
  map.on("zoomend", postaviRunNadstreske);
  const yours = yourStop(state.run.stops);
  if (yours && yours.lat != null) {
    runVir("run-tvoja", [pkTocka([yours.lat, yours.lon], { ime: lepoIme(yours.name) })]);
    // Ime na tisti strani pike, kjer je prostor: ob desnem robu levo od nje.
    // Ob robu okvirja je bilo odrezano („no Šiška“).
    const stran = () => {
      const levo = map.project([yours.lon, yours.lat]).x > el.clientWidth / 2;
      map.setLayoutProperty("run-tvoja-ime", "text-anchor", levo ? "right" : "left");
      map.setLayoutProperty("run-tvoja-ime", "text-offset", [levo ? -1.1 : 1.1, 0]);
    };
    map.on("moveend", stran);
    stran();
  }
  runImeNaDotik();
  return true;
}

const run3D = () => !!runMap.map && runMap.map.getZoom() >= AVTO_3D_OD;

// Nadstreški postajališč te vožnje -- nekaj deset, zato vsi naenkrat, znova
// le ob spremembi približka (povečava `nadstresekK`).
function postaviRunNadstreske() {
  const { map, postajeOdBlizu } = runMap;
  if (!map || !postajeOdBlizu) return;
  const z = map.getZoom();
  const k = z < NADSTRESKI_OD ? null : nadstresekK(z);
  if (k === runMap.nadstresekK) return;
  runMap.nadstresekK = k;
  runVir("run-postaje-nadstreski", k == null ? [] : postajeOdBlizu
    .filter((s) => s.smer != null && !s.postaja)
    .flatMap((s) => nadstresekKosi(s, k)));
}

// Pot pred vozilom v barvi omrežja, prevožena siva. Razrez je pri oceni lege,
// brez lege pri zadnji meritvi (`posodobiKarto`). Osveži se ob novih podatkih
// in ko ocena odpelje za 30 m, ne vsako sekundo: `setData` na telefonu ni
// zastonj.
const RAZREZ_M = 30;

function narisiRunTraso(vzdolz) {
  const { kosi, kosIdx, trasa, cums } = runMap;
  if (!kosi || !kosi.length) return;
  runMap.razrez = vzdolz;
  const crte = [];
  kosi.forEach((kos, i) => {
    if (i !== kosIdx || vzdolz == null) {
      const del = vzdolz != null && i < kosIdx ? "za" : "naprej";
      crte.push(pkCrta(kos, { vrsta: "trasa", del }));
      return;
    }
    let j = 0;
    while (j < cums.length - 2 && cums[j + 1] <= vzdolz) j += 1;
    const p = tockaNaTrasi(trasa, cums, vzdolz);
    const prevozeno = [...trasa.slice(0, j + 1), p];
    const naprej = [p, ...trasa.slice(j + 1)];
    if (prevozeno.length > 1) crte.push(pkCrta(prevozeno, { vrsta: "trasa", del: "za" }));
    if (naprej.length > 1) crte.push(pkCrta(naprej, { vrsta: "trasa", del: "naprej" }));
  });
  runVir("run-trasa", crte);
}

// Model in ikona se ne rišeta hkrati: ikona je element nad platnom in bi
// model prekrila. Skupina modela je prevoznik (`avtoModeli`), LPP pa v legah
// nosi ime namesto ID-ja.
function postavi3D(lega) {
  const { v, avto3d, marker } = runMap;
  if (!avto3d || !marker) return;
  const na = lega || runMap.lega;
  if (!na) return;
  runMap.lega = na;
  const zdaj3D = run3D();
  marker.getElement().hidden = zdaj3D;
  avto3d.nastavi(zdaj3D ? [{ lon: na.kje[1], lat: na.kje[0], smer: na.smer,
                             model: modelVozila(v) }] : []);
}

const modelVozila = (v) => {
  const ag = v.agency === "lpp" ? "1118" : v.agency;
  return AGENCY_INK[ag] ? ag : "drugi";
};

// ---------- zemljevid avtobusa: vedno ----------
//
// Osnutek E (David, 24. 10. 2026: „zmenila sva se, da mora biti zemljevid“):
// avtobus ima zemljevid na vrhu okna tudi brez lege -- pot vožnje,
// postajališča in tvoje. Vozilo pride nanj, ko je lega; pred odhodom vozilo s
// prejšnje vožnje, kadar ima GPS. Brez WebGL2 ostaneta odštevanje in trak.
// Vlak zemljevida nima („je itak samo tir“): kje je, pove trak.

function pripraviKarto() {
  if (runMap.nastaja) return runMap.nastaja;
  // Razred pred nastankom, da MapLibre okvir izmeri v pravi višini.
  document.body.classList.add("ima-karto");
  runMap.nastaja = ustvariRunMap().then(async (ok) => {
    if (!ok) {
      document.body.classList.remove("ima-karto");
      document.getElementById("run-map-wrap").hidden = true;
      return false;
    }
    initFullscreen();
    initLocate();
    initOsvezi();
    // Prvi pogled počaka prvi odgovor o legi (največ 1,5 s): pot cele
    // vožnje, ki se po pol sekunde zamenja z vozilom, je skok pod prstom.
    await Promise.race([runMap.prvaLega || Promise.resolve(),
                        new Promise((ok2) => setTimeout(ok2, 1500))]);
    zacetniPogled();
    posodobiKarto();
    return true;
  }).catch((err) => {
    console.error("zemljevida ni bilo mogoče narisati", err);
    document.body.classList.remove("ima-karto");
    document.getElementById("run-map-wrap").hidden = true;
    return false;
  });
  return runMap.nastaja;
}

// Prvi pogled: vozilo in tvoje postajališče, kadar sta, sicer vozilo s
// prejšnje vožnje in izhodišče, sicer vsa pot. Potem se pogled ne premika sam
// (`zemljevid.md`), razen ko vozilo uide iz okvira. Spodaj je prostor za
// odštevanje, zgoraj za pilulo in gumbe.
const POGLED_ODMIK = { top: 64, bottom: 116, left: 28, right: 64 };

function zacetniPogled() {
  const stops = state.run.stops.filter((s) => s.lat != null);
  const tvoj = yourStop(state.run.stops);
  const tocke = [];
  const prev = !state.current && state.chain && state.chain.prev;
  if (runMap.v) tocke.push([runMap.v.lat, runMap.v.lon]);
  else if (prev && prev.gps && prev.gps.lat != null) {
    tocke.push([prev.gps.lat, prev.gps.lon]);
    if (stops.length) tocke.push([stops[0].lat, stops[0].lon]);
  }
  if (tvoj && tvoj.lat != null && !vrednostNaPostanku(tvoj).mimo) tocke.push([tvoj.lat, tvoj.lon]);
  pkPrilagodi(runMap.map, tocke.length ? tocke : stops.map((s) => [s.lat, s.lon]),
              { padding: POGLED_ODMIK, animate: false });
}

// Kar se spremeni z odgovorom o vožnji: prevožena postajališča, pot za
// vozilom, kadar lege ni (do zadnje meritve), vozilo s prejšnje vožnje in
// pilula. Z lego pot reže ocena lege (`postaviVozilo`).
function posodobiKarto() {
  if (!runMap.map || !state.run) return;
  const cur = state.current;
  const postaje = runMap.postajeOdBlizu || [];
  const tocke = tockePostajalisc(postaje).features;
  tocke.forEach((f, i) => {
    f.properties.mimo = cur && postaje[i].stop_seq <= cur.stop_seq ? 1 : 0;
  });
  runVir("run-postaje", tocke);
  if (!runMap.v) {
    let vzdolz = null;
    if (cur && cur.lat != null && runMap.trasa) {
      const p = projekcijaNaTraso(runMap.trasa, runMap.cums, cur.lat, cur.lon);
      if (p.odmik <= POSTAJA_OB_TRASI_M) vzdolz = p.vzdolz;
    }
    narisiRunTraso(vzdolz);
  }
  postaviVoziloVerige();
  posodobiPilulo();
}

// Avtobus, ki še ni odpeljal, je pogosto na prejšnji vožnji (`block_id`,
// `vehicleChainHtml`): kje je zdaj, pove njegov GPS. Okrogla značka, ne
// oblika vozila na tej poti -- tu še ne vozi.
function postaviVoziloVerige() {
  const prev = !state.current && !runMap.v && state.chain && state.chain.prev;
  const gps = prev && prev.gps;
  if (!gps || gps.lat == null) {
    if (runMap.veriga) runMap.veriga.remove();
    runMap.veriga = null;
    return;
  }
  if (!runMap.veriga) {
    const el = document.createElement("div");
    el.className = "ov-veriga-vozilo";
    el.innerHTML = SVG_BUS;
    runMap.veriga = new runMap.ml.Marker({ element: el }).setLngLat([gps.lon, gps.lat])
      .addTo(runMap.map);
  }
  runMap.veriga.setLngLat([gps.lon, gps.lat]);
  runMap.veriga.getElement().title = `vozilo zdaj tu · konča vožnjo ${prev.train_no}`;
}

async function drawRunMap(v) {
  runMap.v = v;
  runMap.since = Date.now();
  if (runMap.veriga) runMap.veriga.remove();
  runMap.veriga = null;
  // Lega pride vsakih nekaj sekund, zemljevid pa nastaja dlje (knjiznica,
  // slog, trasa). Skupna obljuba: druga lega ne naredi drugega zemljevida.
  if (!(await pripraviKarto())) {
    // Brez WebGL2: odštevanje in trak ostaneta, starost lege pod njima.
    podnapis(v, 0);
    return;
  }
  postaviVozilo(true);
}

// `nova` loci osvezitev PODATKOV od sekundnega premika pike. Podnapis se sme
// prepisati samo ob novih podatkih: `ageHtml()` ob vsakem izpisu postavi novo
// izhodisce, zato ga je sekundno prepisovanje ponastavljalo na izvorno
// vrednost -- stevilka je stala, sekundna zanka v common.js jo je vmes
// povecala, naslednji izris pa povozil. Videti je bilo kot utripanje.
function postaviVozilo(nova) {
  const v = runMap.v;
  if (!v || !runMap.map) return;
  const moving = (v.speed_kmh || 0) >= 3;
  const starost = v.age_s + (Date.now() - runMap.since) / 1000;
  const lega = ocenjenaLega(v, starost);
  lega.smer = smerNaOceni(runMap, v, lega, polVozila(v));
  const { kje } = lega;
  const odmik = razdaljaM(kje, [v.lat, v.lon]);

  if (!runMap.marker) {
    const el = document.createElement("div");
    el.className = "run-bus";
    // Smer je glede na sever in se vrti z zemljevidom; v nagibu vozilo stoji
    // obrnjeno proti gledalcu, kot na velikem zemljevidu.
    runMap.marker = new runMap.ml.Marker({
      element: el, rotationAlignment: "map", pitchAlignment: "viewport",
    }).setLngLat([kje[1], kje[0]]).addTo(runMap.map);
  }
  runMap.marker.setLngLat([kje[1], kje[0]]).setRotation(lega.smer);
  const el = runMap.marker.getElement();
  if (el.dataset.vozi !== String(moving)) {
    el.dataset.vozi = String(moving);
    el.innerHTML = busSvg(moving, inkVozila(v));
  }
  // Izmerjena lega se spremeni samo z novim odgovorom; `setData` vsako
  // sekundo bi MapLibre silil, da vir na telefonu predeluje brez razloga.
  if (nova) runVir("run-gps", [pkTocka([v.lat, v.lon], { ime: meritevIme() })]);
  postavi3D(lega);
  if (lega.vzdolz != null && (nova || runMap.razrez == null
      || Math.abs(lega.vzdolz - runMap.razrez) > RAZREZ_M)) {
    narisiRunTraso(lega.vzdolz);
  }

  if (runMap.sledi) drziVozilo(kje);

  // Vozilo se premika, torej se razdalja spreminja tudi brez novega dotika.
  posodobiPilulo();

  if (nova) podnapis(v, odmik);
}

// Pogled gre za vozilom, dokler ga človek ne povleče (kot izbrani avtobus na
// velikem zemljevidu, `drziVSliki`), in to samo, ko vozilo uide iz vidnega
// dela okvira: čez rob ali pod kartico odštevanja -- tam je ocena lege
// izginila, okvir pa jo je še štel za vidno. Sicer ga sekundni premik ne
// premika, da ga ne trga izpod prsta.
function drziVozilo(kje) {
  const { map } = runMap;
  if (map.isMoving()) return;
  // Velikost iz platna, ne iz postavitve: ta bi se vsako sekundo preračunala.
  const k = map.getCanvas(), r = map.getPixelRatio();
  const w = k.width / r, h = k.height / r;
  const p = map.project([kje[1], kje[0]]);
  const dno = p.y > h / 2 && kartaOdstEl.offsetHeight ? kartaOdstEl.offsetTop : h;
  if (p.x >= 0 && p.x <= w && p.y >= 0 && p.y <= dno) return;
  const o = POGLED_ODMIK;
  map.panBy([p.x - (o.left + (w - o.left - o.right) / 2), p.y - (o.top + (h - o.top - o.bottom) / 2)],
            { duration: 500 });
}

const meritevIme = () => (runMap.vir === "potniki" ? "zadnje poročilo potnikov"
  : "zadnja izmerjena lega");

const SVG_GPS = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/><circle cx="12" cy="12" r="8"/></svg>';

// Pod zemljevidom desno: od kod je lega in kako stara (osnutek E: „GPS pred
// 40 s“). Ocena lege pove to z besedo -- legende pod zemljevidom ni več, na
// sliki jo loči oblika (prosojno, črtkan obris; meritev je rdeča pika).
// Velja tudi brez zemljevida (brskalnik brez WebGL2).
function podnapis(v, odmik) {
  const n = v.potnikov || 1;
  const vir = runMap.vir === "potniki"
    ? `<span class="ov-potnik">${n === 1 ? "potnik" : escapeHtml(potnikov(n))}</span>` : "GPS";
  document.getElementById("run-map-sub").innerHTML = `${SVG_GPS}<span>${
    odmik > OCENA_VIDNA_M ? "ocena · " : ""}${vir} pred ${ageHtml(v.age_s)}</span>`;
}

// Med dvema meritvama pika drsi naprej. To ni okras: vozilo se v 30 s pri
// 30 km/h premakne cetrt kilometra, in prav to je vprasanje, zaradi katerega
// je clovek odprl to stran.
setInterval(() => {
  if (document.visibilityState === "hidden") return;
  if (runMap.marker) postaviVozilo(false);
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
  // Cez celo stran ni nicesar krasti: zemljevid JE stran, zato en prst in
  // kolesce pripadata njemu.
  if (runMap.map) {
    if (on) runMap.map.cooperativeGestures.disable();
    else runMap.map.cooperativeGestures.enable();
  }
  if (btn) {
    btn.setAttribute("aria-pressed", String(on));
    btn.title = on ? "Pomanjšaj" : "Čez celo stran";
  }
  // MapLibre meri okvir sam in ga po spremembi velikosti ne premeri.
  if (runMap.map) requestAnimationFrame(() => runMap.map.resize());
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
    el.innerHTML = `<span class="slabo">${!v ? "Vozilo lege še nima, zato razdalje ni mogoče izmeriti."
      : "Za to vožnjo trase ni, zato razdalje po poti ni mogoče izmeriti."}</span>`;
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
  // Lega daleč od poti ni lega na poti: projekcija bi iz avtobusa na
  // avtocesti naredila „še 420 m“ (prijava 22. 10. 2026).
  const meritev = projekcijaNaTraso(runMap.trasa, runMap.cums, v.lat, v.lon);
  if (meritev.odmik > NA_TRASI_M) {
    el.innerHTML = `<span class="slabo">Vozilo je ${razdaljaText(meritev.odmik)} od poti `
      + "te vožnje, zato razdalje po poti ni mogoče izmeriti.</span>";
    el.hidden = false;
    return;
  }
  const { kje } = ocenjenaLega(v, starost);
  const vozilo = projekcijaNaTraso(runMap.trasa, runMap.cums, kje[0], kje[1]);
  const d = vozilo.vzdolz - jaz.vzdolz;
  // "je 1,5 km pred tvojo lego" se bere dvoumno -- lahko kot "ze mimo tebe".
  // Zato povemo, koliko POTI mu ostane, in loceno, ce je ze mimo.
  el.innerHTML = d <= 0
    ? `${svgVozila()}<span>še <strong>${razdaljaText(-d)}</strong> do tebe</span>`
    : `${svgVozila()}<span>že mimo tebe · <strong>${razdaljaText(d)}</strong> naprej</span>`;
  el.hidden = false;
}

// Brez tvoje lege je „do mene“ tvoje postajališče (`postaja` v naslovu, s
// table): koliko poti ima vozilo še do njega. Isti račun po trasi in ista
// ocenjena lega kot zgoraj; daleč od trase ali za vozilom se ne pove nič.
const POSTAJA_OB_TRASI_M = 150;

function razdaljaDoPostaje() {
  const el = document.getElementById("run-map-me-line");
  const tvoj = state.run && yourStop(state.run.stops);
  if (!el || runMap.loc) return;
  // Brez trase ali postajališča pilula izgine -- sicer bi obstala beseda izpred
  // lege („lege vozila ni“) ob vozilu, ki je že na zemljevidu.
  if (!runMap.v || !runMap.trasa || !tvoj || tvoj.lat == null || vrednostNaPostanku(tvoj).mimo) {
    el.hidden = true;
    return;
  }
  const v = runMap.v;
  if (projekcijaNaTraso(runMap.trasa, runMap.cums, v.lat, v.lon).odmik > NA_TRASI_M) {
    el.hidden = true;
    return;
  }
  const { kje } = ocenjenaLega(v, v.age_s + (Date.now() - runMap.since) / 1000);
  const vozilo = projekcijaNaTraso(runMap.trasa, runMap.cums, kje[0], kje[1]);
  const postaja = projekcijaNaTraso(runMap.trasa, runMap.cums, tvoj.lat, tvoj.lon);
  const d = postaja.vzdolz - vozilo.vzdolz;
  if (postaja.odmik > POSTAJA_OB_TRASI_M || d < 0) {
    el.hidden = true;
    return;
  }
  el.innerHTML = `${svgVozila()}<span>še <strong>${razdaljaText(d)}</strong> do postajališča</span>`;
  el.hidden = false;
}

// Kadar lega pride sama (dovoljenje dano, `LEGA`), se razdalja pokaže samo,
// kadar jo je mogoče izmeriti: „od te proge si 40 km stran“ je odgovor na
// vprašanje, ki ga nihče ni postavil. Po dotiku gumba (`runMap.legaGumb`)
// povemo tudi, zakaj je ni.
function razdaljaDoMene(loc) {
  izracunajRazdaljo(loc);
  const el = document.getElementById("run-map-me-line");
  if (el && !runMap.legaGumb && el.querySelector(".slabo")) el.hidden = true;
}

// Pilula zgoraj levo: koliko poti ima vozilo še do tebe ali do tvojega
// postajališča. Brez lege vozila pove, zakaj ga na zemljevidu ni -- prazen
// zemljevid brez besede je videti kot okvara.
function posodobiPilulo() {
  const el = document.getElementById("run-map-me-line");
  if (!el || !state.run) return;
  if (runMap.v) {
    if (runMap.loc) razdaljaDoMene(runMap.loc);
    else razdaljaDoPostaje();
    return;
  }
  // Odgovor na dotik gumba „moja lega“ ostane, dokler vozila ni.
  if (runMap.legaGumb && el.querySelector(".slabo")) return;
  const t = pilulaBrezVozila();
  el.innerHTML = t;
  el.hidden = !t;
}

function pilulaBrezVozila() {
  const run = state.run;
  const stops = run.stops;
  if (state.current && state.current === stops[stops.length - 1]) return "";
  const prev = !state.current && state.chain && state.chain.prev;
  if (prev && prev.gps && prev.gps.lat != null) {
    return `${svgVozila()}<span>še na prejšnji vožnji</span>`;
  }
  const odhod = odhodPrvega();
  if (odhod) return `${svgVozila()}<span>odpelje ob <strong>${hhmm(odhod)}</strong></span>`;
  if (run.service_date !== todayIso()) return "";
  return `${svgVozila()}<span class="slabo">lege vozila ni</span>`;
}

function initLocate() {
  const btn = document.getElementById("run-map-me");
  if (!btn) return;
  btn.hidden = false;
  // Vprasanje "kako dalec je vozilo od mene" se med cakanjem spreminja na
  // obeh straneh, zato lega sledi; ena izmerjena bi po petih minutah lagala.
  // Pogled se zanjo ne premakne -- ostane pri vozilu.
  LEGA.poslusaj((l) => {
    runMap.loc = l;
    pkJaz(runMap.map, l);
    posodobiPilulo();
  });
  btn.addEventListener("click", async () => {
    runMap.legaGumb = true;
    const el = document.getElementById("run-map-me-line");
    el.innerHTML = '<span class="slabo">iščem lokacijo …</span>';
    el.hidden = false;
    try {
      const loc = await poisciMe();
      // Pogled naj zajame OBOJE -- vprasanje je razmerje med tabo in vozilom,
      // ne ena ali druga tocka.
      if (runMap.marker) {
        const ll = runMap.marker.getLngLat();
        pkPrilagodi(runMap.map, [[loc.lat, loc.lon], [ll.lat, ll.lng]],
                    { padding: POGLED_ODMIK, maxZoom: 16 });
      } else {
        runMap.map.easeTo({ center: [loc.lon, loc.lat], zoom: 15 - PK_LZ });
      }
      izracunajRazdaljo(loc);
    } catch (err) {
      el.innerHTML = `<span class="slabo">${escapeHtml(err.message)}</span>`;
    }
  });
}

/**
 * Gumb "osvezi" ob zemljevidu voznje.
 *
 * Vprasanje pred tem zemljevidom je "kje je zdaj", odgovor pa se osvezuje sam.
 * Kadar vozilo stoji, se to na zaslonu ne vidi -- mirna pika je videti enako
 * kot obticala stran. Osvezi OBOJE: lego in zamudo, ker sta na tej strani en
 * sam odgovor.
 */
function initOsvezi() {
  const btn = document.getElementById("run-map-osvezi");
  if (!btn) return;
  btn.hidden = false;
  pripniOsvezi(btn, [
    () => (runMap.poll ? runMap.poll.zdaj() : Promise.resolve()),
    // `loadRun` napake ne vrže (stran ostane, pove „brez zveze“); gumb jo
    // mora povedati sam.
    async () => {
      await (oknoPoll ? oknoPoll.zdaj() : loadRun());
      if (state.brezZveze) throw new Error("brez zveze");
    },
  ]);
  btn.title = "Osveži zdaj";
  btn.setAttribute("aria-label", "Osveži zdaj");
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
  // Lego ima samo avtobus (GPS ali potnik na njem); vlak in nadomestni
  // prevoz zemljevida nimata, kje je vlak s potnikom, pove trak.
  if (!trip || !state.run || OMREZJE !== "avtobus") return;
  // Lega obstaja samo za tekoci dan; za ogled preteklega dne je vprasanje
  // "kje je zdaj" brez pomena.
  if (state.run.service_date !== todayIso()) return;
  // Prej se je lega nalozila ENKRAT in nikoli vec: kdor je okno pustil odprto,
  // je gledal, kje je bil avtobus ob odprtju strani. Prav tu je vprasanje
  // "kje je zdaj" najbolj neposredno, zato se osvezuje v koraku s strezbo:
  // ritem pove streznik (`X-Osvezi-Cez`) -- GPS na 10 s, potniki na 5 s.
  // **Ena zanka na vožnjo, ne ena na osvežitev.** `loadPosition` se klice iz
  // `loadRun`, ta pa tece vsakih 10 s -- brez te varovalke je stran po desetih
  // minutah imela dvajset vzporednih poizvedb po legi, vsaka na ~10 s.
  if (runMap.pollTrip === trip) return;
  if (runMap.poll) runMap.poll.stop();
  runMap.pollTrip = trip;
  const prva = trip === URL_TRIP ? zgodaj.lega : null;
  zgodaj.lega = null;
  let prvaOk;
  runMap.prvaLega = new Promise((ok) => { prvaOk = ok; });
  runMap.poll = pollVehicles(`/api/vehicles?trip=${encodeURIComponent(trip)}`, (list) => {
    const v = list[0];
    if (v) {
      runMap.vir = v.vir === "potniki" ? "potniki" : "gps";
      drawRunMap(v);
    } else if (runMap.vir === "potniki") {
      skrijVozilo();
    }
    prvaOk();
  }, prva);
}

// Vozilo brez GPS (~10 % avtobusov) ima lego samo od potnikov na njem, in to
// le, kadar je poročilo verodostojno (`api._vozilo_po_potnikih`). Med
// poročili drsi po trasi: izmerjeno 1. 10. 2026 na 273 točkah treh deljenj,
// napaka po 30 s mediana 31 m proti 244 m za piko na zadnjem poročilu. Ko se
// poročila postarajo ali razidejo, vozilo izgine z zemljevida (zemljevid
// ostane): vozilo na legi izpred petih minut bi trdilo, da je tam. GPS
// avtobusa pa ostane na zadnji legi, kot je bil.
function skrijVozilo() {
  runMap.vir = null;
  runMap.v = null;
  if (runMap.marker) runMap.marker.remove();
  runMap.marker = null;
  if (runMap.avto3d) runMap.avto3d.nastavi([]);
  runVir("run-gps", []);
  document.getElementById("run-map-sub").innerHTML = "";
  posodobiKarto();
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
    }
  } catch (err) {
    console.error("vremena ni bilo mogoče naložiti", err);
  }
}

loadWeather();
// Ovire so samo pri železnici (tudi nadomestni prevoz je `zeleznica`).
if (OMREZJE === "zeleznica") loadAlerts();

// Ena zanka: prej je `loadRun` tekel dvakrat hkrati (zanka ga sproži takoj, in
// še ročni klic), z njim vse njegove zahteve -- polovica dela strežnika za
// okno vožnje. Ura in pika živosti v glavi sta šli z osnutkom E: svežino pove
// vrstica pod vrhom (`svezinaHtml`), izpad zajema obvestilo na vrhu.
oknoPoll = pollWhileVisible(loadRun, ritemOkna);
