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

/** Vrne obljubo shranjenih poti, ki imajo danes ali jutri kak odhod. */
function izrisiPoti() {
  const poti = mojePoti();
  document.getElementById("moje-prazno").hidden = poti.length > 0;
  const el = document.getElementById("moje-poti");
  el.innerHTML = poti.map((f, i) => `
    <a class="d-pot d-pot-${f.net === "avtobus" ? "bus" : "vlak"}" href="${escapeHtml(znackaHref(f))}">
      <span class="d-pot-glava">${ZVEZDICA}<span class="d-pot-ime">${escapeHtml(znackaOpis(f))}</span>${PUSICA}</span>
      <span class="d-pot-odh" id="pot-odh-${i}"></span>
    </a>`).join("");
  return osveziOdhode(poti).then((ima) => poti.filter((f, i) => ima[i]));
}

let mojeZadnje = [];
function osveziOdhode(poti) {
  mojeZadnje = poti;
  return Promise.all(poti.map(async (f, i) => {
    let html;
    let ima = false;
    try {
      const zdaj = Date.now();
      const danes = naslednjiOdhodi(await odhodiPoti(f), zdaj, ODHODOV);
      if (danes.length) {
        html = odhodiHtml(danes, zdaj, false);
        ima = true;
      } else {
        // Danes ne pelje nic vec: prva jutrisnja, kot `danes_ni` pri poti.
        // Ob 23:20 je bila sicer prazna vsaka kartica, prav ko clovek
        // zvecer gleda, kdaj gre zjutraj.
        const jutri = (await odhodiPoti(f, datumLj(zdaj + 86400000))).slice(0, ODHODOV);
        ima = jutri.length > 0;
        html = ima ? odhodiHtml(jutri, zdaj, true)
          : '<span class="d-pot-nic">danes in jutri ne pelje nič</span>';
      }
    } catch (err) {
      html = '<span class="d-pot-nic">odhodov ni bilo mogoče naložiti</span>';
    }
    const el = document.getElementById(`pot-odh-${i}`);
    if (el && mojeZadnje === poti) el.innerHTML = html;
    return ima;
  }));
}

document.addEventListener("visibilitychange", () => {
  if (!document.hidden && mojeZadnje.length) osveziOdhode(mojeZadnje);
});
setInterval(() => {
  if (!document.hidden && mojeZadnje.length) osveziOdhode(mojeZadnje);
}, OSVEZI_POTI_MS);

// ---------- povabilo ----------
//
// Od ust do ust se ne vidi: sporočilne aplikacije glave `Referer` ne
// pošljejo, 29. 9.-12. 10. 2026 je bilo 88 % ogledov brez znanega vira.
// Kartica ponudi, da potnik pošlje stran SVOJE poti (konkretno, ne "deli
// kajros"), povezava nosi `utm_source=povabilo` (`obisk._VIRI`). Samo kdor
// ima shranjeno pot in je kajros odprl vsaj na štiri dni (`dneviRabe` v
// common.js): novinec še ne ve, ali stran dela. Kartica, ne sistemsko
// obvestilo: oglas v obvestilu je razlog za odstranitev aplikacije, budilka
// pa mora ostati vredna zaupanja. "Pošlji", ne "Deli" -- to je deljenje lege.
//
// Pošlje se pristajalna stran, ne iskalnik: izriše jo strežnik in predogled
// v sporočilu nosi relacijo in običajno zamudo. Pot brez neposredne vožnje
// ("danes in jutri ne pelje nič") se ne ponudi -- njena stran je prazna.

const POVABILO_KLJUC = "kajros:povabilo";
const POVABILO_PO_DNEH = 4;
// "Ne zdaj" utihne za dva meseca, poslano za štiri: povabilo ne sme nadlegovati.
const POVABILO_PREMOR_MS = { ne: 60 * 86400000, poslano: 120 * 86400000 };

// Isto kot `pristanek.slug()`: šumnike zloži `fold()`, ostalo postane vezaj.
const slug = (ime) => fold(ime).replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

function povabiloUtisano() {
  try {
    const o = JSON.parse(localStorage.getItem(POVABILO_KLJUC) || "null");
    return !!o && Date.now() - o.t < (POVABILO_PREMOR_MS[o.kaj] || 0);
  } catch (e) {
    return false;
  }
}

function utisajPovabilo(kaj) {
  try {
    localStorage.setItem(POVABILO_KLJUC, JSON.stringify({ kaj, t: Date.now() }));
  } catch (e) { /* zasebno okno: kartica se pokaže znova */ }
}

function povabiloZa(f) {
  const bus = f.net === "avtobus";
  if (f.kind === "board") {
    const kje = `${bus ? "postajališča" : "postaje"} ${f.station}`;
    return {
      pot: `/${bus ? "postajalisce" : "postaja"}/${slug(f.station)}`,
      kartica: `Pošlji mu odhode in zamude s ${kje}.`,
      besedilo: `Odhodi in zamude s ${kje} v živo`,
    };
  }
  const rel = `${f.from} → ${f.to}`;
  return {
    pot: `/${bus ? "avtobus" : "vlak"}/${slug(f.from)}/${slug(f.to)}`,
    kartica: `Pošlji mu zamude za ${rel}.`,
    besedilo: `Zamude ${bus ? "avtobusov" : "vlakov"} ${rel} v živo`,
  };
}

const POSLJI_ZNAK = `<svg class="d-pov-znak" width="20" height="20" viewBox="0 0 24 24" fill="none"
  stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"
  aria-hidden="true"><path d="M21 3 10.5 13.5M21 3l-6.5 18-4-7.5L3 9.5z"/></svg>`;

function ponudiPovabilo(sOdhodi) {
  const f = sOdhodi[0];
  if (!f || povabiloUtisano() || dneviRabe().length < POVABILO_PO_DNEH) return;
  const p = povabiloZa(f);
  const el = document.getElementById("povabilo");
  el.innerHTML = `${POSLJI_ZNAK}
    <div class="d-pov-telo">
      <p class="d-pov-nasl">Se s tabo vozi še kdo?</p>
      <p class="d-pov-besedilo">${escapeHtml(p.kartica)}</p>
      <div class="d-pov-gumbi">
        <button type="button" class="d-pov-poslji">Pošlji</button>
        <button type="button" class="d-pov-ne">Ne zdaj</button>
      </div>
    </div>`;
  el.hidden = false;
  el.querySelector(".d-pov-ne").addEventListener("click", () => {
    el.hidden = true;
    utisajPovabilo("ne");
  });
  el.querySelector(".d-pov-poslji").addEventListener("click", async () => {
    const url = `${location.origin}${p.pot}?utm_source=povabilo`;
    const izid = await posljiPovezavo(p.besedilo, p.besedilo, url);
    if (izid === "preklicano") return;
    const telo = el.querySelector(".d-pov-telo");
    if (izid === "ni šlo") {
      // Ne izbirnika ne odložišča (brskalnik brez dovoljenja): povezava za ročno kopiranje.
      telo.querySelector(".d-pov-besedilo").innerHTML =
        `Kopiranje ni uspelo. Povezava: <span class="d-pov-url">${escapeHtml(url)}</span>`;
      return;
    }
    utisajPovabilo("poslano");
    telo.innerHTML = izid === "kopirano"
      ? '<p class="d-pov-nasl">Povezava je kopirana</p><p class="d-pov-besedilo">Prilepi jo v sporočilo.</p>'
      : '<p class="d-pov-nasl">Hvala!</p>';
    setTimeout(() => { el.hidden = true; }, 5000);
  });
}

// ---------- lega na zemljevidih ----------
//
// Lega teče sama, kadar je dovoljena (`LEGA` v common.js); kdor je še ni
// dovolil, dobi tu tiho kartico (David, 22. 10. 2026). Vprašanje sproži šele
// „Vklopi“: v aplikaciji sistemsko okno, ob trajni zavrnitvi nastavitve
// aplikacije, v brskalniku poziv brskalnika.
//
// Komu ne: zavrnjeno v brskalniku (to je nastavitev strani v brskalniku in je
// gumb ne popravi), stran brez varnega konteksta in aplikacija pred mostom 7
// (`stanjeLege` „neznano“). Stara aplikacija po vklopu lege zemljevidom ne bi
// znala prižgati sama, kartica pa bi to obljubila.

const LEGA_KARTICA_KLJUC = "kajros:lega-kartica";
// "Ne zdaj" in zavrnitev utihneta za dva meseca, kot povabilo.
const LEGA_KARTICA_PREMOR_MS = 60 * 86400000;

const LEGA_ZNAK = `<svg class="d-pov-znak" width="20" height="20" viewBox="0 0 24 24" fill="none"
  stroke="currentColor" stroke-width="1.9" stroke-linecap="round" aria-hidden="true">
  <circle cx="12" cy="12" r="3.2"/><circle cx="12" cy="12" r="8"/>
  <path d="M12 1.5v2.5M12 20v2.5M1.5 12h2.5M20 12h2.5"/></svg>`;

function legaKarticaUtisana() {
  try {
    const o = JSON.parse(localStorage.getItem(LEGA_KARTICA_KLJUC) || "null");
    return !!o && Date.now() - o.t < LEGA_KARTICA_PREMOR_MS;
  } catch (e) {
    return false;
  }
}

function utisajLegaKartico() {
  try {
    localStorage.setItem(LEGA_KARTICA_KLJUC, JSON.stringify({ t: Date.now() }));
  } catch (e) { /* zasebno okno: kartica se pokaže znova */ }
}


async function ponudiLego() {
  const el = document.getElementById("lega");
  if (!el || legaKarticaUtisana() || await stanjeLege() !== "vprasaj") return;
  el.innerHTML = `${LEGA_ZNAK}
    <div class="d-pov-telo">
      <p class="d-pov-nasl">Pokaži, kje si, na zemljevidih</p>
      <p class="d-pov-besedilo">Zemljevid te pokaže sam, iskalnik ponudi najbližjo postajo. Lege ne shranimo.</p>
      <div class="d-pov-gumbi">
        <button type="button" class="d-pov-poslji">Vklopi</button>
        <button type="button" class="d-pov-ne">Ne zdaj</button>
      </div>
    </div>`;
  el.hidden = false;
  let vklopljena = false;
  const potrdi = () => {
    if (vklopljena) return;
    vklopljena = true;
    el.querySelector(".d-pov-telo").innerHTML = '<p class="d-pov-nasl">Lega je vklopljena</p>'
      + '<p class="d-pov-besedilo">Na zemljevidih boš modra pika.</p>';
    setTimeout(() => { el.hidden = true; }, 4000);
  };
  // Dovoljenje, dano drugje (Deli lego, nastavitve), kartico odvzame.
  LEGA.obStanju((s) => {
    if (el.hidden) return;
    if (s === "dano") potrdi();
    else if (s !== "vprasaj") el.hidden = true;
  });
  el.querySelector(".d-pov-ne").addEventListener("click", () => {
    el.hidden = true;
    utisajLegaKartico();
  });
  el.querySelector(".d-pov-poslji").addEventListener("click", async () => {
    const izid = await vklopiLego();
    if (izid.stanje === "dano") return potrdi();
    // Ob trajni zavrnitvi je aplikacija odprla svoje nastavitve; kartica
    // počaka, da se potnik vrne (`LEGA.obStanju`).
    if (izid.nastavitve) return;
    // Rekel je ne: jutri ga ne sprašujmo znova.
    el.hidden = true;
    utisajLegaKartico();
  });
}

// ---------- podpora ----------
//
// Cilj zbiranja (`config.CILJ`, 20. 10. 2026). Vsota pride iz `/api/podpora`,
// ne iz HTML: to stran streže service worker iz predpomnilnika. Zaprta
// kartica ostane zaprta do novega cilja (`kljuc`), ne za vedno in ne za dan.
// Gumb pelje na `/donacije`, ne naravnost na Ko-fi: tam piše, za kaj je
// denar in kdo ga pobere.

const PODPORA_KLJUC = "kajros:podpora";

const evri = (centi) => (centi / 100).toLocaleString("sl-SI",
  { minimumFractionDigits: centi % 100 ? 2 : 0, maximumFractionDigits: 2 });

// Ista oblika kot seznam na `/donacije` (Jinja): besedo za desni rob da
// strežnik (`donacije._koraki`).
const koraki = (ks) => `<ol class="pod-koraki">${ks.map((k) => `
  <li class="pod-k pod-k-${k.stanje}"${k.stanje === "zdaj" ? ' aria-current="step"' : ""}>
    <span class="pod-k-ime">${escapeHtml(k.ime)}</span><span class="pod-k-kdaj">${escapeHtml(k.kdaj)}</span></li>`).join("")}
</ol>`;

async function izrisiPodporo() {
  const el = document.getElementById("podpora");
  if (!el) return;
  let c;
  try {
    const r = await fetch("/api/podpora");
    if (!r.ok) return;
    c = await r.json();
  } catch (e) {
    return;                       // brez omrežja kartice ni -- ni nujna
  }
  try {
    if (localStorage.getItem(PODPORA_KLJUC) === c.kljuc) return;
  } catch (e) { /* zasebno okno: kartica se pokaže */ }
  const glava = (zapri) => `
    <div class="d-pod-glava">
      <p class="d-pov-nasl">${escapeHtml(c.namen)}</p>
      <button type="button" class="d-pod-zapri" aria-label="${zapri}">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>
      </button>
    </div>`;
  const delez = Math.min(100, (100 * c.zbrano_centov) / c.cilj_centov);
  // Cilj dosežen (9. 11. 2026): prošnje ni več, kartica piše napredek namena.
  // Gumba Podpri tu ni; `/donacije` ostane v meniju. Napis nosi znesek
  // cilja, ne vsoto (David 9. 11. 2026: „zbrali ste 30 €, ne 34“).
  if (c.koraki && c.koraki.length) el.innerHTML = `${glava("Skrij do naslednjega koraka")}
    <p class="pod-hvala">Zbrali ste ${evri(c.cilj_centov)} €. Hvala!</p>
    ${koraki(c.koraki)}`;
  else el.innerHTML = `${glava("Skrij do novega cilja")}
    <div class="pod-trak" role="progressbar" aria-label="Zbrano" aria-valuemin="0"
      aria-valuemax="${c.cilj_centov / 100}" aria-valuenow="${c.zbrano_centov / 100}"><span style="width:${delez.toFixed(1)}%"></span></div>
    <p class="pod-stevilka"><b>${evri(c.zbrano_centov)} €</b> od ${evri(c.cilj_centov)} €${
      c.zbrano_centov >= c.cilj_centov ? " · cilj dosežen, hvala!" : ""}</p>
    <p class="d-pov-besedilo">Kajros je brez oglasov in ga vzdržuje <a class="d-pod-mi" href="/o-nas">ena oseba</a>.</p>
    <div class="d-pov-gumbi"><a class="d-pov-poslji" href="/donacije">Podpri</a></div>`;
  el.hidden = false;
  el.querySelector(".d-pod-zapri").addEventListener("click", () => {
    el.hidden = true;
    try {
      localStorage.setItem(PODPORA_KLJUC, c.kljuc);
    } catch (e) { /* zasebno okno: ob naslednjem obisku se pokaže znova */ }
  });
}

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
izrisiPoti().then(ponudiPovabilo);
ponudiLego();
izrisiPodporo();
if (MOST) {
  if (document.readyState === "complete") kasneje();
  else addEventListener("load", kasneje, { once: true });
}
