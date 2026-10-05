/* Najhitrejša pot: od vrat do vrat.
 *
 * Edina stran, ki se ne začne pri postaji, ampak pri **kraju**: potnik ve,
 * kje stoji in kam gre, ne pa, s katere postaje mu pelje. Kraj je naslov,
 * ulica, kraj, postaja, shranjena točka, lastna lega ali klik na zemljevid;
 * iskanje teče čez obe omrežji.
 *
 * Naslovi so iz NAŠEGA kazala (`/api/naslovi`), ne iz tujega geokodirnika:
 * ta bi ob vsakem pritisku tipke izvedel, kam kdo gre.
 *
 * Vprašanje časa je PRIHOD, ne odhod: „kdaj moraš biti tam" -- čim prej, ali
 * do ure. Pri roku je prvi predlog tisti, s katerim od doma odideš najpozneje.
 */

const $ = (s) => document.querySelector(s);
const stanje = $("#pot-stanje");
const izidiEl = $("#pot-izidi");

// Kaj bo pobral naslednji klik na zemljevid. Brez tega bi bil klik dvoumen:
// prvi klik postavi izhodišče, drugi cilj, tretji pa nič ne pomeni.
const S = { od: null, do: null, arm: "od", izidi: null, izbran: 0, jaz: null, kdaj: "zdaj" };

let K = null;                  // { map, ml } ali null, dokler/ker ga ni

function povej(besedilo, vrsta) {
  stanje.className = "pot-stanje" + (vrsta ? " je-" + vrsta : "");
  stanje.textContent = besedilo || "";
}

// ---------------------------------------------------------------- nastavitve

function hojeMin() {
  const n = Number($("#hoje").value);
  return Number.isFinite(n) && n >= 3 ? Math.min(45, Math.round(n)) : 25;
}

// Vrednost iz naslova, ki je med izbirami ni, dobi svojo izbiro -- sicer bi
// deljena povezava s 30 minutami tiho iskala s 25.
function nastaviHoje(minut) {
  const sel = $("#hoje");
  if (![...sel.options].some((o) => o.value === String(minut))) {
    const o = document.createElement("option");
    o.value = String(minut);
    o.textContent = `${minut} min`;
    sel.appendChild(o);
  }
  sel.value = String(minut);
}

const kolo = () => $("#kolo").checked;
const KOLO_KMH = 15;

function nastaviKdaj(kdaj, fokus) {
  S.kdaj = kdaj;
  document.querySelectorAll("[data-kdaj]").forEach((b) =>
    b.setAttribute("aria-pressed", String(b.dataset.kdaj === kdaj)));
  $(".kdaj-do").hidden = kdaj !== "do";
  // "Čim prej" je danes: dan brez ure je vprašanje brez odgovora.
  if (kdaj === "zdaj") $("#dan").value = todayIso();
  if (kdaj === "do" && fokus && !$("#tam").value) $("#tam").focus();
}

document.querySelectorAll("[data-kdaj]").forEach((b) => {
  b.addEventListener("click", () => {
    const prej = S.kdaj;
    nastaviKdaj(b.dataset.kdaj, true);
    if (S.izidi && prej !== S.kdaj && (S.kdaj === "zdaj" || $("#tam").value)) isci();
  });
});

// ---------------------------------------------------------------- kraja na zemljevidu

function narisiTocke(premakni = true) {
  if (!K) return;
  pkKonca(K, S.od, S.do);
  const f = [];
  // Postajališča izbrane poti, da je vstop in izstop videti brez branja.
  const p = S.izidi && S.izidi.predlogi[S.izbran];
  if (p) {
    for (const n of p.noge) {
      if (n.vrsta !== "voznja") continue;
      if (n.od_ll) f.push(pkTocka(n.od_ll, { vrsta: "postaja", ime: n.od }));
      if (n.do_ll) f.push(pkTocka(n.do_ll, { vrsta: "postaja", ime: n.do }));
    }
  }
  pkVir(K.map, "k-tocke", f);
  if (!premakni) return;
  if (S.od && S.do) {
    pkPrilagodi(K.map, [[S.od.lat, S.od.lon], [S.do.lat, S.do.lon]]);
  } else if (S.od || S.do) {
    const t = S.od || S.do;
    K.map.easeTo({ center: [t.lon, t.lat], zoom: Math.max(K.map.getZoom(), 14 - PK_LZ) });
  }
}

// Kaj piše v polju za ta kraj. Ena funkcija, ker je isti zapis stal na treh
// mestih (postavitev, branje naslova, zvezdica) in se je razšel takoj, ko je
// shranjena točka dobila ime.
function napisTocke(t) {
  return t ? (t.ime || `${t.lat.toFixed(5)}, ${t.lon.toFixed(5)}`) : "";
}

function postavi(kaj, tocka) {
  S[kaj] = tocka;
  $(`#q-${kaj}`).value = napisTocke(tocka);
  zapriZadetke(kaj);
  narisiTocke();
  // Prvi klik postavi izhodišče, naslednji cilj -- brez tega bi moral človek
  // pred vsakim klikom povedati, kaj postavlja.
  S.arm = S.od && !S.do ? "do" : kaj === "od" ? "do" : "od";
  oznaciArm();
  oznaciZvezde();
  // Kadar je odgovor že na zaslonu, nov kraj pomeni novo vprašanje.
  if (S.izidi && S.od && S.do) isci();
}

function oznaciArm() {
  document.querySelectorAll(".tocka").forEach((el) => {
    el.classList.toggle("je-arm", el.dataset.kaj === S.arm);
  });
}

// Pot nazaj je isto vprašanje z zamenjanima koncema. Kadar je odgovor že na
// zaslonu, se poišče takoj — gumb, ki vidno stanje pusti pri miru, je videti
// kot okvara (isto pravilo kot pri zamenjavi postaj v iskalniku zvez).
$("#zamenjaj").addEventListener("click", () => {
  [S.od, S.do] = [S.do, S.od];
  for (const kaj of ["od", "do"]) $(`#q-${kaj}`).value = napisTocke(S[kaj]);
  // Naslednji klik na zemljevid gre v prazno polje, ne tja, kamor je meril prej.
  S.arm = !S.od ? "od" : !S.do ? "do" : S.arm;
  oznaciArm();
  oznaciZvezde();
  narisiTocke(false);      // pogled ostane, kjer je: premaknili sta se le vlogi
  vUrl();
  if (S.izidi) isci();
});

// ---------------------------------------------------------------- shranjene točke
//
// Potnik hodi isto pot vsak dan, kraj pa je moral vsakič znova zadeti na
// zemljevidu — na telefonu je to klik, ki hiše ne zadene.
//
// **Točke ostanejo v brskalniku.** Kje kdo stanuje, je najobčutljivejši
// podatek, ki ga ta aplikacija sploh lahko drži. Strežnik dobi samo
// koordinate, ki jih poizvedba nosi tako ali tako (`/api/pot?od_lat=…`), ime
// pa nikamor — tudi v naslov strani ne, da deljena povezava ne pove, da je
// tista točka tvoj dom.

const TOCKE_KLJUC = "kajros:tocke";
const TOCKE_MAX = 6;
// Ujemanje je po razdalji, ne po enakosti: naslov nosi pet decimalk, lega iz
// GPS pa vse. 1e-4 stopinje je ~11 m — isto dvorišče, ne ista ulica.
const TOCKA_PRAG = 1e-4;

function tockeBeri() {
  try {
    const v = JSON.parse(localStorage.getItem(TOCKE_KLJUC) || "[]");
    return Array.isArray(v)
      ? v.filter((t) => t && t.ime && Number.isFinite(t.lat) && Number.isFinite(t.lon))
      : [];
  } catch (e) {
    return [];                 // pokvarjen zapis ni razlog, da stran ne dela
  }
}

function tockeZapisi(seznam) {
  try {
    localStorage.setItem(TOCKE_KLJUC, JSON.stringify(seznam.slice(0, TOCKE_MAX)));
  } catch (e) { /* zaseben zavihek ali polna shramba: stran dela naprej */ }
}

function shranjenaZa(t) {
  if (!t) return null;
  return tockeBeri().find((s) => Math.abs(s.lat - t.lat) < TOCKA_PRAG
                              && Math.abs(s.lon - t.lon) < TOCKA_PRAG) || null;
}

// Zvezdica govori isto kot v iskalniku zvez (`fav-toggle`): en gumb pove
// stanje in ga preklopi. Križca na žetonu zato ni — točka se odstrani tako,
// da jo postaviš (dotik na žeton) in odtakneš zvezdico.
function oznaciZvezde() {
  for (const kaj of ["od", "do"]) {
    const b = document.querySelector(`.tocka[data-kaj="${kaj}"] .tocka-shrani`);
    const t = S[kaj];
    // **Zvezdica opisuje postavljeno točko, ne besedila v polju.** Med
    // tipkanjem polje že govori o drugem kraju, točka pa je še stara.
    b.hidden = !t || $(`#q-${kaj}`).value.trim() !== napisTocke(t);
    if (b.hidden) continue;
    const s = shranjenaZa(t);
    b.textContent = s ? "★ shranjeno" : "☆ shrani";
    b.title = s ? `odstrani „${s.ime}“ med shranjenimi`
                : "shrani to točko (dom, služba …)";
    b.setAttribute("aria-pressed", String(!!s));
  }
}

// Žetoni so pod OBEMA poljema, ne enkrat na stran: „dom“ je enkrat izhodišče
// in enkrat cilj, in dotik mora povedati, kam gre.
function izrisiTocke() {
  const shranjene = tockeBeri();
  for (const kaj of ["od", "do"]) {
    const ul = document.querySelector(`.tocka[data-kaj="${kaj}"] .tocke-shranjene`);
    ul.innerHTML = shranjene.map((t, i) => `<li><button type="button"
      class="tocka-zeton" data-i="${i}">★ ${escapeHtml(t.ime)}</button></li>`).join("");
    ul.hidden = shranjene.length === 0;
  }
  oznaciZvezde();
}

function odpriIme(kaj) {
  const box = document.querySelector(`.tocka[data-kaj="${kaj}"] .tocka-ime`);
  const vnos = box.querySelector(".tocka-ime-vnos");
  // Ime iz iskanja je dober privzetek; „moja lega“ in koordinate nista.
  const t = S[kaj];
  vnos.value = t && t.ime && t.ime !== "moja lega" ? t.ime : "";
  box.hidden = false;
  vnos.focus();
  vnos.select();
}

function shraniTocko(kaj) {
  const box = document.querySelector(`.tocka[data-kaj="${kaj}"] .tocka-ime`);
  const ime = box.querySelector(".tocka-ime-vnos").value.trim();
  const t = S[kaj];
  if (!t || !ime) return;
  const seznam = tockeBeri();
  // Isto ime je isti kraj: druga „služba“ ni druga služba, ampak popravek
  // prve. Brez tega bi seznam tiho zrasel v dva žetona z istim napisom.
  const at = seznam.findIndex((s) => fold(s.ime) === fold(ime));
  if (at >= 0) {
    seznam[at] = { ime, lat: t.lat, lon: t.lon };
  } else if (seznam.length >= TOCKE_MAX) {
    povej(`Shranjenih je že ${TOCKE_MAX} točk — eno odstrani, preden dodaš novo.`,
          "napaka");
    return;
  } else {
    seznam.push({ ime, lat: t.lat, lon: t.lon });
  }
  tockeZapisi(seznam);
  box.hidden = true;
  // Polje odslej kaže IME, ne koordinat — to je bil ves namen.
  S[kaj] = { ...t, ime };
  $(`#q-${kaj}`).value = ime;
  izrisiTocke();
}

function odstraniTocko(kaj) {
  const s = shranjenaZa(S[kaj]);
  if (!s) return;
  tockeZapisi(tockeBeri().filter((x) => fold(x.ime) !== fold(s.ime)));
  izrisiTocke();
}

// ---------------------------------------------------------------- iskanje kraja
//
// Troje virov v enem seznamu: shranjene točke, postaje (kazalo v brskalniku,
// `common.naloziKazalo()`) in naslovi, ulice, kraji in imenovane točke z
// našega strežnika. Postaje so iz svojega kazala, ker imajo promet -- „Kamnik"
// mora najprej dati postajo, na katero človek misli.

let KAZALO = null;
const ZADETKI = { od: [], do: [] };
const IZBRAN_Z = { od: -1, do: -1 };

function zapriZadetke(kaj) {
  const ul = $(`#z-${kaj}`);
  ul.hidden = true;
  ul.innerHTML = "";
  ZADETKI[kaj] = [];
  IZBRAN_Z[kaj] = -1;
  $(`#q-${kaj}`).setAttribute("aria-expanded", "false");
}

// Okolica iskanja: drugi konec poti, lastna lega, sicer sredina zemljevida,
// če je dovolj blizu. Brez tega „Trubarjeva 5" pomeni katerokoli Trubarjevo.
function okolica(kaj) {
  const drugi = S[kaj === "od" ? "do" : "od"];
  if (drugi) return drugi;
  if (S.jaz) return S.jaz;
  if (K && K.map.getZoom() + PK_LZ >= 10) {
    const c = K.map.getCenter();
    return { lat: c.lat, lon: c.lng };
  }
  return null;
}

const VRSTA_BESEDA = { postaja: "postaja", ulica: "ulica", shranjena: "shranjena" };

function zadetekHtml(z, i, izbran) {
  const vrsta = VRSTA_BESEDA[z.vrsta];
  const pod = [vrsta, z.pod].filter(Boolean).join(" · ");
  return `<li role="option" aria-selected="${izbran}"><button type="button" data-i="${i}"
      class="${izbran ? "je-izbran" : ""}"><span class="z-znak z-${z.vrsta}" aria-hidden="true"></span>
      <span class="z-besedilo"><span class="z-ime">${escapeHtml(z.ime)}</span>${
        pod ? `<span class="z-pod">${escapeHtml(pod)}</span>` : ""}</span></button></li>`;
}

function izrisiZadetke(kaj) {
  const ul = $(`#z-${kaj}`);
  const z = ZADETKI[kaj];
  ul.innerHTML = z.map((x, i) => zadetekHtml(x, i, i === IZBRAN_Z[kaj])).join("");
  ul.hidden = z.length === 0;
  $(`#q-${kaj}`).setAttribute("aria-expanded", String(!ul.hidden));
}

const iskanjeNaslovov = { od: null, do: null };

/** Zadetki, ki so že v brskalniku: shranjene točke in postaje. */
function lokalniZadetki(q) {
  const niz = fold(q.trim());
  return {
    shranjene: tockeBeri().filter((t) => fold(t.ime).startsWith(niz))
      .map((t) => ({ vrsta: "shranjena", ime: t.ime, pod: "", lat: t.lat, lon: t.lon })),
    postaje: (KAZALO ? iskalnikKazala(KAZALO, q, 3) : [])
      .map((s) => ({ vrsta: "postaja", ime: s.n, pod: "", lat: s.lat, lon: s.lon })),
  };
}

async function zadetkiZa(kaj, q, signal) {
  const niz = fold(q.trim());
  const { shranjene, postaje } = lokalniZadetki(q);
  let naslovi = [];
  if (niz.length >= 2) {
    const p = new URLSearchParams({ q });
    const o = okolica(kaj);
    if (o) { p.set("lat", o.lat.toFixed(4)); p.set("lon", o.lon.toFixed(4)); }
    try {
      const r = await fetch(`/api/naslovi?${p}`, { signal });
      if (r.ok) naslovi = (await r.json()).zadetki || [];
    } catch (e) {
      if (e.name === "AbortError") throw e;
      // Brez naslovov stran išče po postajah -- kot pred kazalom naslovov.
    }
  }
  // S številko človek išče naslov; brez nje najprej postajo ali kraj.
  const sStevilko = /\d/.test(q);
  const vsi = sStevilko ? [...shranjene, ...naslovi, ...postaje]
                        : [...shranjene, ...postaje, ...naslovi];
  return vsi.slice(0, 9);
}

let zakasnitev = null;

function pripniIskanje(kaj) {
  const vnos = $(`#q-${kaj}`);
  const isci_ = () => {
    oznaciZvezde();          // polje se je razšlo s točko: zvezdica gre stran
    const q = vnos.value.trim();
    clearTimeout(zakasnitev);
    if (iskanjeNaslovov[kaj]) iskanjeNaslovov[kaj].abort();
    if (q.length < 2 || q === napisTocke(S[kaj])) return zapriZadetke(kaj);
    // Postaje so v brskalniku in so takoj; naslovi pridejo s strežnika in
    // se ne sprašujejo na vsak pritisk tipke.
    const { shranjene, postaje } = lokalniZadetki(q);
    ZADETKI[kaj] = [...shranjene, ...postaje];
    IZBRAN_Z[kaj] = -1;
    izrisiZadetke(kaj);
    zakasnitev = setTimeout(async () => {
      const ac = new AbortController();
      iskanjeNaslovov[kaj] = ac;
      try {
        ZADETKI[kaj] = await zadetkiZa(kaj, q, ac.signal);
        if (vnos.value.trim() !== q) return;
        IZBRAN_Z[kaj] = -1;
        izrisiZadetke(kaj);
      } catch (e) { /* prekinjeno: človek tipka naprej */ }
    }, 160);
  };
  vnos.addEventListener("input", isci_);
  vnos.addEventListener("focus", () => { S.arm = kaj; oznaciArm(); isci_(); });
  vnos.addEventListener("keydown", (e) => {
    const z = ZADETKI[kaj];
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      if (!z.length) return;
      e.preventDefault();
      IZBRAN_Z[kaj] = (IZBRAN_Z[kaj] + (e.key === "ArrowDown" ? 1 : z.length - 1)) % z.length;
      izrisiZadetke(kaj);
      return;
    }
    if (e.key === "Escape") { zapriZadetke(kaj); return; }
    if (e.key !== "Enter") return;
    e.preventDefault();
    // Enter izbere zadetek, če je seznam odprt; sicer išče pot.
    if (z.length) {
      izberi(kaj, z[Math.max(0, IZBRAN_Z[kaj])]);
      return;
    }
    isci();
  });
  // `mousedown` in ne `click`: klik bi prišel šele po `blur`, ki seznam zapre.
  $(`#z-${kaj}`).addEventListener("mousedown", (e) => {
    const b = e.target.closest("button[data-i]");
    if (!b) return;
    e.preventDefault();
    izberi(kaj, ZADETKI[kaj][Number(b.dataset.i)]);
  });
  vnos.addEventListener("blur", () => setTimeout(() => zapriZadetke(kaj), 150));
}

function izberi(kaj, z) {
  if (!z) return;
  postavi(kaj, { lat: z.lat, lon: z.lon, ime: z.ime });
  // Naslednje prazno polje dobi fokus: od kod -> kam -> gumb.
  const drugi = kaj === "od" ? "do" : "od";
  if (!S[drugi]) $(`#q-${drugi}`).focus();
}

/** Kraj za polje, v katerem je besedilo, a ne izbran zadetek: prvi zadetek.
 *  Brez tega je „Poišči" po tipkanju naslova vrnil „manjka cilj". */
async function razresi(kaj) {
  const q = $(`#q-${kaj}`).value.trim();
  if (S[kaj] && q === napisTocke(S[kaj])) return true;
  if (!q) {
    // Izbrisano polje ni "prejšnja točka": iskanje s staro točko bi tiho
    // odgovorilo na vprašanje, ki ga potnik ni več postavil.
    S[kaj] = null;
    narisiTocke(false);
    oznaciZvezde();
    return false;
  }
  if (q.length < 2) return false;
  try {
    const z = await zadetkiZa(kaj, q);
    if (!z.length) return false;
    S[kaj] = { lat: z[0].lat, lon: z[0].lon, ime: z[0].ime };
    $(`#q-${kaj}`).value = z[0].ime;
    zapriZadetke(kaj);
    narisiTocke(false);
    oznaciZvezde();
    return true;
  } catch (e) {
    return false;
  }
}

// ---------------------------------------------------------------- moja lega

let ustaviSledenje = null;

function risiJaz(loc) {
  S.jaz = loc;
  if (K) pkJaz(K.map, loc);
}

document.querySelectorAll(".tocka").forEach((el) => {
  const kaj = el.dataset.kaj;
  pripniIskanje(kaj);
  // Žetoni se prerišejo ob vsaki spremembi, zato posluša blok in ne žeton.
  el.addEventListener("click", (e) => {
    const z = e.target.closest(".tocka-zeton");
    if (!z) return;
    const t = tockeBeri()[Number(z.dataset.i)];
    if (t) postavi(kaj, { lat: t.lat, lon: t.lon, ime: t.ime });
  });
  el.querySelector(".tocka-ime-vnos").addEventListener("keydown", (e) => {
    if (e.key === "Enter") shraniTocko(kaj);
    if (e.key === "Escape") el.querySelector(".tocka-ime").hidden = true;
  });
  el.querySelectorAll(".tocka-gumb").forEach((b) => {
    b.addEventListener("click", async () => {
      if (b.dataset.akcija === "shrani") {
        if (shranjenaZa(S[kaj])) odstraniTocko(kaj);
        else odpriIme(kaj);
        return;
      }
      if (b.dataset.akcija === "ime-shrani") {
        shraniTocko(kaj);
        return;
      }
      if (b.dataset.akcija === "karta") {
        S.arm = kaj;
        oznaciArm();
        povej("Klikni na zemljevid.", null);
        $("#karta").scrollIntoView({ behavior: "smooth", block: "nearest" });
        return;
      }
      // GPS brez omrežnega določanja lege rabi lahko pol minute. Molk je v
      // tem času videti kot pokvarjen gumb, zato povemo, kje smo.
      povej("Iščem tvojo lego … (GPS zna rabiti pol minute)", null);
      try {
        const loc = await locateMe({
          napredek: (l) => {
            risiJaz(l);
            povej(`Iščem tvojo lego … zaenkrat na ${Math.round(l.acc)} m`, null);
          },
        });
        risiJaz(loc);
        postavi(kaj, { lat: loc.lat, lon: loc.lon, ime: "moja lega" });
        // Sledenje teče naprej: prvi popravek GPS pogosto zgreši za sto metrov.
        if (!ustaviSledenje) ustaviSledenje = sledi(risiJaz);
        povej(loc.acc > 200
          ? `Lega je natančna na ${Math.round(loc.acc)} m — po potrebi popravi na zemljevidu.`
          : "");
      } catch (e) {
        povej(e.message, "napaka");
      }
    });
  });
});

// ---------------------------------------------------------------- zemljevid na veliko

// Čez celo STRAN, ne čez cel zaslon -- isti razlog kot pri oknu vožnje:
// fullscreen skrije naslovno vrstico, gumb nazaj in vsak drug orientir, izhod
// pa je tipka, ki je na telefonu ni.
function velikost(veliko) {
  document.body.classList.toggle("karta-velika", veliko);
  const b = $("#karta-max");
  b.setAttribute("aria-pressed", String(veliko));
  b.title = veliko ? "Pomanjšaj zemljevid" : "Zemljevid čez celo stran";
  requestAnimationFrame(() => K && K.map.resize());
}

$("#karta-max").addEventListener("click", () => {
  velikost(!document.body.classList.contains("karta-velika"));
  vUrl();
});

// ---------------------------------------------------------------- izris predlogov

const ura = (ts) => new Date(ts * 1000).toLocaleTimeString("sl-SI",
  { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Ljubljana" });

function minute(s) {
  const m = Math.floor(s / 60 + 0.5);
  return m < 60 ? `${m} min` : `${Math.floor(m / 60)} h ${String(m % 60).padStart(2, "0")}`;
}

// Brez podatka ni isto kot točno. Prazno mesto ob liniji se bere kot „vozi po
// voznem redu“ -- ista beseda kot v iskalniku zvez.
function zamudaHtml(n) {
  const z = n.zamuda;
  if (!z) return n.brez_podatka ? '<span class="zam zam-brez">brez podatka</span>' : "";
  const barva = delayColor(z);
  return `<span class="zam" style="color:${barva};border-color:${barva}55">`
    + `${escapeHtml(delayText(z, true))}</span>`;
}

// Rezerva prestopa mora ostati v verigi. Brez nje "1 prestop" ne pove, ali
// zveza drži -- in prav to je edino, zaradi česar je prestop vreden pozornosti.
function prestopHtml(t, pred, po) {
  const mins = rezervaPrestopa(t, pred, po);
  if (mins == null) {
    const n = Math.floor(t.nacrtovano_s / 60 + 0.5);
    return `<span class="v-prestop">${n} min za prestop</span>`;
  }
  const barva = mins < 2 ? "var(--sev-bad)" : mins < 5 ? "var(--sev-hard)" : "var(--ok)";
  return `<span class="v-prestop" style="color:${barva}">${
    escapeHtml(prestopText(mins))}</span>`;
}

// Kolo je samo na koncih poti; prestop na postaji je hoja s kolesom ob sebi.
function besedaHoje(p, i) {
  const konec = i === 0 || i === p.noge.length - 1;
  return konec && S.izidi && S.izidi.kmh > 7 ? "kolo" : "peš";
}

// Veriga poti v eni vrstici: "peš 12 › LPV 2268 +5 › peš 7". Prej je bila
// vsaka noga svoja vrstica z urami in postajami -- štirje predlogi so dali
// dvajset vrstic, med katerimi ni bilo mogoče izbirati na pogled.
function verigaHtml(p) {
  const voznje = p.noge.filter((n) => n.vrsta === "voznja");
  const cleni = [];
  p.noge.forEach((n, i) => {
    const v = voznje.indexOf(n);
    if (v > 0 && p.prestopi && p.prestopi[v - 1]) {
      cleni.push(prestopHtml(p.prestopi[v - 1], voznje[v - 1], n));
    }
    if (n.vrsta === "hoja") {
      cleni.push(`<span class="v-hoja">${besedaHoje(p, i)} ${Math.floor(n.sekunde / 60 + 0.5)}</span>`);
      return;
    }
    const kdo = AGENCY[n.agency];
    const oznaka = kdo ? `${kdo} ${n.train_no}` : n.train_no;
    cleni.push(`<span class="v-linija">${escapeHtml(oznaka)}</span>${zamudaHtml(n)}`);
  });
  return cleni.join('<span class="v-loc" aria-hidden="true">›</span>');
}

// Naslov podrobne strani. Vožnje so v naslovu, ne v seji: pot mora ostati
// deljiva, in kdor jo komu pošlje, mu pošlje pot, ne svojega brskalnika.
function podrobnoUrl(p) {
  const noge = p.noge.filter((n) => n.vrsta === "voznja")
    .map((n) => `${n.trip_id}:${n.od_seq}:${n.do_seq}`).join(";");
  if (!noge) return null;            // pot vso pot peš nima česa razložiti
  const q = new URLSearchParams({
    noge, od_lat: S.od.lat.toFixed(5), od_lon: S.od.lon.toFixed(5),
    do_lat: S.do.lat.toFixed(5), do_lon: S.do.lon.toFixed(5),
  });
  // Dan je del poti: jutrišnja vožnja z današnjim dnem je druga vožnja ali
  // nobena. To je dan PREDLOGA, ne vprašanja -- ponoči je nočni avtobus
  // včerajšnji, in z dnem vprašanja so podrobnosti kazale jutrišnjo vožnjo ob
  // isti uri. Dan vprašanja gre posebej (`dan`), za pot nazaj na seznam.
  const vprasanje = S.izidi && S.izidi.datum;
  const dan = p.datum || vprasanje;
  if (dan && dan !== todayIso()) q.set("date", dan);
  if (vprasanje && vprasanje !== dan) q.set("dan", vprasanje);
  if (S.izidi && S.izidi.kmh > 7) q.set("kmh", S.izidi.kmh);
  // Meja hoje je del vprašanja: brez nje je "nazaj na predloge" iskal z 25 min.
  if (hojeMin() !== 25) q.set("hoje", hojeMin());
  if (S.izidi && S.izidi.prihod_do) q.set("tam", ura(S.izidi.prihod_do));
  return `/app/pot/podrobno?${q}`;
}

// Pri roku je prvo vprašanje "kdaj moram od doma", drugo "koliko rezerve
// imam". Rezerva je rok minus prihod, po uri, ki jo kartica kaže.
function rokHtml(p, i) {
  const rok = S.izidi && S.izidi.prihod_do;
  if (!rok || S.izidi.ne_ujames) return "";
  const prihod = p.prihod_ocena || p.prihod;
  if (p.prepozno) {
    return `<span class="p-rok je-pozno">po napovedi ${minute(prihod - rok)} prepozno</span>`;
  }
  const rezerva = rok - prihod;
  const beseda = rezerva < 60 ? "točno ob roku" : `${minute(rezerva)} pred rokom`;
  return `${i === 0 ? '<span class="p-rok je-zadnji">najpozneje</span>' : ""}`
    + `<span class="p-rok">${beseda}</span>`;
}

function predlogHtml(p, i) {
  const brezVozila = !p.noge.some((n) => n.vrsta === "voznja");
  const prestopi = p.prestopov === 0
    ? (brezVozila ? (S.izidi.kmh > 7 ? "vso pot s kolesom" : "vso pot peš") : "brez prestopa")
    : `${p.prestopov} ${sklon(p.prestopov, "prestop")}`;
  const zamudno = p.prihod_ocena && p.prihod_ocena !== p.prihod
    ? ` · <span class="p-vr">vozni red ${ura(p.odhod)} → ${ura(p.prihod)}</span>` : "";
  const url = podrobnoUrl(p);
  const znacka = url ? "a" : "article";
  const kam = url ? ` href="${url}"` : "";
  const hoje = p.hoje_s >= 60 && !brezVozila
    ? ` · ${minute(p.hoje_s)} ${S.izidi.kmh > 7 ? "do postaj" : "hoje"}` : "";
  return `<${znacka} class="predlog${i === 0 ? " je-prvi" : ""}${p.prepozno ? " je-pozno" : ""}"
      data-i="${i}"${kam}>
    <div class="p-ure">
      <strong>${ura(p.odhod_ocena || p.odhod)}</strong>
      <span class="p-pusc" aria-hidden="true">→</span>
      <strong>${ura(p.prihod_ocena || p.prihod)}</strong>
      <span class="p-traj">${minute(trajanjePrikaz(p))}</span>
    </div>
    <div class="p-veriga">${verigaHtml(p)}</div>
    <div class="p-meta">${rokHtml(p, i)}${prestopi}${hoje}${zamudno}</div>
  </${znacka}>`;
}

// Ravna črta med postajama ni proga. Zato se najprej nariše kot skica, nato
// pa jo zamenja prava trasa iz `shape` -- ista, ki jo riše zemljevid.
let izrisZeton = 0;
async function narisiPot(p) {
  const moj = ++izrisZeton;
  if (!K) return;
  if (!p) { pkVir(K.map, "k-pot", []); narisiTocke(false); return; }
  const crte = p.noge.map((n) => {
    const a = n.od_ll || (S.od && [S.od.lat, S.od.lon]);
    const b = n.do_ll || (S.do && [S.do.lat, S.do.lon]);
    if (!a || !b) return null;
    return { n, tocke: [a, b], vrsta: n.vrsta };
  }).filter(Boolean);
  const risi = (prosojnost) => pkVir(K.map, "k-pot", crte.map((c) =>
    pkCrta(c.tocke, { vrsta: c.vrsta, prosojnost: c.vrsta === "voznja" ? prosojnost : 0.95 })));
  risi(0.55);
  narisiTocke(false);
  for (const c of crte) {
    if (c.vrsta !== "voznja") continue;
    const t = await trasa(c.n).catch(() => null);
    if (moj !== izrisZeton) return;      // vmes je bil izbran drug predlog
    if (t) c.tocke = t;
  }
  risi(0.9);
}

// Kaj bi pomagalo, kadar z vozilom ni ničesar. Meja velja do postaje; kadar je
// prvo uporabno postajališče tik čez njo, je to ugotovitev in ne ugibanje.
// Da bi s tem pot res nastala, ne obljubljamo -- postajališče v dosegu še ni
// zveza, in tako tudi piše.
function nasvetHtml(n) {
  if (!n) return "";
  if (n.ni_zveze) {
    return ' <span class="nasvet">Postajališča so v dosegu, zveze med njimi ta '
      + "čas ni.</span>";
  }
  return ` <span class="nasvet">Najbližje postajališče je <strong>${n.vec_hoje_min} min</strong>`
    + ` daleč — <button type="button" id="vec-hoje" data-min="${n.vec_hoje_min}">`
    + "poskusi s toliko</button>, čeprav zveza s tem ni zagotovljena.</span>";
}

function pripniNasvet() {
  const b = document.getElementById("vec-hoje");
  if (!b) return;
  b.addEventListener("click", () => {
    nastaviHoje(Number(b.dataset.min));
    isci();
  });
}

// Dan v stavku: "danes" se ne piše, drug dan pa vedno -- rok "do 8:00" je
// brez dneva uganka, če iščeš za jutri.
function danBeseda(datum) {
  return datum === todayIso() ? "" : ` · ${dayLabel(datum)}`;
}

function naslovIzida(izid) {
  const opomba = izid.vir_hoje === "osrm" ? ""
    : " · pot do postaje je <strong>ocena</strong>, ker usmerjevalnik ne odgovarja";
  if (izid.ne_ujames) {
    const prvi = izid.predlogi[0];
    const kdaj = prvi ? ura(prvi.prihod_ocena || prvi.prihod) : null;
    return `<span class="izid-naslov je-pozno">Do ${ura(izid.prihod_do)} ne prideš več.</span>`
      + (kdaj ? ` Najhitreje si tam ob <strong>${kdaj}</strong>${
        izid.danes_ni ? danBeseda(izid.datum) : ""}.` : "") + opomba;
  }
  // Zvečer, ko danes ne pelje nič več, so predlogi jutrišnji -- to mora
  // stati v naslovu, kartice nosijo samo uri.
  if (izid.danes_ni) {
    return `<span class="izid-naslov">Danes ne pelje nič več. Prve zveze${
      danBeseda(izid.datum)}</span>${opomba}`;
  }
  if (izid.prihod_do) {
    const prvi = izid.predlogi[0];
    const odidi = prvi ? ` Odidi najpozneje ob <strong>${ura(prvi.odhod_ocena || prvi.odhod)}</strong>.` : "";
    return `<span class="izid-naslov">Da boš tam do ${ura(izid.prihod_do)}${
      danBeseda(izid.datum)}</span>${odidi}${opomba}`;
  }
  return `<span class="izid-naslov">Najhitreje na cilju${danBeseda(izid.datum)}</span>${opomba}`;
}

function izrisi(izid) {
  S.izidi = izid;
  S.izbran = 0;
  if (!izid.predlogi.length) {
    izidiEl.innerHTML = "";
    povej("", "prazno");
    stanje.innerHTML = (izid.prihod_do
      ? `Do ${ura(izid.prihod_do)}${danBeseda(izid.datum)} ni poti. Poskusi poznejšo uro`
      : "Za ta čas ni poti. Poskusi pozneje")
      + " ali dovoli več do postaje." + nasvetHtml(izid.nasvet);
    pripniNasvet();
    narisiPot(null);
    return;
  }
  povej("");
  // Kadar je hoja edino, kar imamo, je treba povedati zakaj -- sicer je videti
  // kot da smo prezrli avtobus, ki ga v resnici ni.
  if (izid.predlogi.length === 1 && izid.predlogi[0].edina) {
    stanje.innerHTML = naslovIzida(izid)
      + ' <span class="nasvet">Z vozilom ni poti, ki bi bila hitrejša.</span>'
      + nasvetHtml(izid.nasvet);
    pripniNasvet();
  } else {
    stanje.innerHTML = naslovIzida(izid);
  }
  izidiEl.innerHTML = izid.predlogi.map((p, i) => predlogHtml(p, i)).join("");
  // Kartica je povezava na podrobno stran, zato klik ne sme izbirati. Na
  // zemljevidu se pot pokaže ob dotiku ali fokusu.
  izidiEl.querySelectorAll(".predlog").forEach((el) => {
    const pokazi = () => {
      if (S.izbran === Number(el.dataset.i)) return;
      S.izbran = Number(el.dataset.i);
      izidiEl.querySelectorAll(".predlog").forEach((x) =>
        x.classList.toggle("je-izbran", Number(x.dataset.i) === S.izbran));
      narisiPot(izid.predlogi[S.izbran]);
    };
    el.addEventListener("mouseenter", pokazi);
    el.addEventListener("focus", pokazi);
  });
  narisiPot(izid.predlogi[0]);
  if (K) {
    const p = izid.predlogi[0];
    pkPrilagodi(K.map, [[S.od.lat, S.od.lon], [S.do.lat, S.do.lon],
                        ...p.noge.flatMap((n) => [n.od_ll, n.do_ll])]);
  }
}

// ---------------------------------------------------------------- poizvedba

let poizvedba = null;

async function isci() {
  povej("Iščem …", null);
  const [a, b] = await Promise.all([razresi("od"), razresi("do")]);
  if (!a || !b) {
    const kaj = !a ? "od" : "do";
    povej($(`#q-${kaj}`).value.trim()
      ? `„${$(`#q-${kaj}`).value.trim()}“ ne najdem — poskusi drugače ali izberi na zemljevidu.`
      : `Manjka ${kaj === "od" ? "izhodišče" : "cilj"}.`, "napaka");
    return;
  }
  if (S.kdaj === "do" && !$("#tam").value) {
    povej("Vpiši uro, do katere moraš biti tam.", "napaka");
    $("#tam").focus();
    return;
  }
  const p = new URLSearchParams({
    od_lat: S.od.lat, od_lon: S.od.lon, do_lat: S.do.lat, do_lon: S.do.lon,
    hoje: hojeMin(),
  });
  if (kolo()) p.set("kmh", KOLO_KMH);
  if (S.kdaj === "do") {
    p.set("prihod", $("#tam").value);
    if ($("#dan").value) p.set("date", $("#dan").value);
  }
  izidiEl.innerHTML = "";
  vUrl();
  const kljuc = String(p);
  const shranjen = S.obnovi ? prebraniIzid(kljuc) : null;
  S.obnovi = false;
  if (shranjen) {
    izrisi(shranjen.izid);
    window.scrollTo(0, shranjen.y || 0);
    return;
  }
  if (poizvedba) poizvedba.abort();
  poizvedba = new AbortController();
  try {
    const r = await fetch(`/api/pot?${p}`, { signal: poizvedba.signal });
    if (!r.ok) {
      const telo = await r.json().catch(() => ({}));
      throw new Error(telo.detail || `strežnik je vrnil ${r.status}`);
    }
    const izid = await r.json();
    izrisi(izid);
    shraniIzid(kljuc, izid);
  } catch (e) {
    if (e.name !== "AbortError") povej(e.message, "napaka");
  }
}

// ---------------------------------------------------------------- nazaj s podrobnosti
//
// Kdor odpre predlog in se vrne, hoče isti seznam na istem mestu, ne novega
// iskanja: brskalnik strani iz predpomnilnika ne vrne (zemljevid, odprte
// povezave), zato je seznam iskal znova ali pa je moral potnik spet pritisniti
// "Poišči". Seznam gre v sessionStorage -- samo ta zavihek, koordinate so tako
// ali tako v naslovu -- in se ob vrnitvi pokaže takoj, dokler je svež in prvi
// predlog še ni odpeljal.
const SHRAMBA = "kajros:pot-izid";
const SVEZE_MS = 5 * 60 * 1000;

function shraniIzid(kljuc, izid) {
  try {
    sessionStorage.setItem(SHRAMBA, JSON.stringify({ kljuc, t: Date.now(), izid, y: 0 }));
  } catch (e) { /* zasebno okno ali poln prostor: brez obnove */ }
}

function prebraniIzid(kljuc) {
  try {
    const s = JSON.parse(sessionStorage.getItem(SHRAMBA));
    if (!s || s.kljuc !== kljuc || Date.now() - s.t > SVEZE_MS) return null;
    const prvi = s.izid.predlogi[0];
    if (prvi && (prvi.odhod_ocena || prvi.odhod) * 1000 < Date.now() - 60000) return null;
    return s;
  } catch (e) {
    return null;
  }
}

// Mesto na seznamu: brez tega se vrneš na vrh, čeprav si odprl četrti predlog.
addEventListener("pagehide", () => {
  try {
    const s = JSON.parse(sessionStorage.getItem(SHRAMBA));
    if (s) sessionStorage.setItem(SHRAMBA, JSON.stringify({ ...s, y: window.scrollY }));
  } catch (e) { /* brez obnove mesta */ }
});

$("#isci").addEventListener("click", isci);
$("#tam").addEventListener("keydown", (e) => { if (e.key === "Enter") isci(); });
// Kadar je odgovor že na zaslonu, ga spremenjeno vprašanje osveži; dokler ga
// ni, išče samo gumb (isto pravilo kot na vstopni strani).
for (const id of ["#dan", "#tam", "#hoje", "#kolo"]) {
  $(id).addEventListener("change", () => {
    if (id === "#dan" && $("#dan").value !== todayIso() && S.kdaj !== "do") nastaviKdaj("do", true);
    if (S.izidi && (S.kdaj === "zdaj" || $("#tam").value)) isci();
  });
}

// ---------------------------------------------------------------- naslov strani
//
// Pot mora biti deljiva. Brez tega je edini način, da nekomu poveš, kako priti
// do tebe, opis s stavki -- in prav to je stran, ki naj bi ga nadomestila.

function vUrl() {
  const q = new URLSearchParams();
  if (S.od) q.set("od", `${S.od.lat.toFixed(5)},${S.od.lon.toFixed(5)}`);
  if (S.do) q.set("do", `${S.do.lat.toFixed(5)},${S.do.lon.toFixed(5)}`);
  if (S.kdaj === "do" && $("#tam").value) {
    q.set("tam", $("#tam").value);
    // Današnjega dne v naslov ne pišemo: deljena povezava brez dneva pomeni
    // „danes“ in jutri odgovori na jutrišnji dan, kar je skoraj vedno mišljeno.
    if ($("#dan").value && $("#dan").value !== todayIso()) q.set("dan", $("#dan").value);
  }
  if (hojeMin() !== 25) q.set("hoje", hojeMin());
  if (kolo()) q.set("kolo", "1");
  // Velikost zemljevida gre v naslov: kdor pot deli, deli tudi pogled nanjo.
  if (document.body.classList.contains("karta-velika")) q.set("karta", "velika");
  history.replaceState(null, "", q.toString() ? `?${q}` : location.pathname);
}

function izUrl() {
  const q = new URLSearchParams(location.search);
  const tocka = (niz) => {
    const [a, b] = String(niz).split(",").map(Number);
    return Number.isFinite(a) && Number.isFinite(b) ? { lat: a, lon: b } : null;
  };
  for (const kaj of ["od", "do"]) {
    const t = q.get(kaj) && tocka(q.get(kaj));
    if (!t) continue;
    // Naslov nosi samo koordinate; kadar so tvoje, jim ime pripiše brskalnik
    // sam — „dom“ pove več kot 46.05611, 14.50577.
    const s = shranjenaZa(t);
    if (s) t.ime = s.ime;
    S[kaj] = t;
    $(`#q-${kaj}`).value = napisTocke(t);
  }
  $("#dan").value = q.get("dan") || todayIso();
  if (q.get("tam")) {
    $("#tam").value = q.get("tam");
    nastaviKdaj("do");
    $("#dan").value = q.get("dan") || todayIso();
  } else {
    nastaviKdaj("zdaj");
  }
  if (q.get("hoje")) nastaviHoje(Number(q.get("hoje")));
  $("#kolo").checked = q.get("kolo") === "1";
  if (q.get("karta") === "velika") velikost(true);
  S.arm = S.od ? "do" : "od";
  return S.od && S.do;
}

// ---------------------------------------------------------------- zagon

pripniDnevnePuscice();
oznaciArm();
naloziKazalo().then((k) => { KAZALO = k; });
const izPovezave = izUrl();
izrisiTocke();                 // zvezdice vedo za kraja šele, ko ju naslov postavi
// „Kam greš?“ z domače strani: človek je ravno odgovoril na „kam“, kazalec pa
// je stal v Od kod (5. 10. 2026). Zdaj v Kam; Od kod dobi lego samo, kadar jo
// je brskalnik tej strani že dovolil -- vprašanja za dovoljenje ne sprožimo sami.
if (location.hash === "#kam" && !izPovezave) {
  history.replaceState(null, "", location.pathname + location.search);
  S.arm = "do";
  oznaciArm();
  $("#q-do").focus();
  if (navigator.permissions) {
    navigator.permissions.query({ name: "geolocation" }).then((p) => {
      if (p.state === "granted" && !S.od) {
        document.querySelector('.tocka[data-kaj="od"] [data-akcija="lega"]').click();
      }
    }).catch(() => {});
  }
}
povej(izPovezave ? "" : "Vpiši naslov ali postajo, ali klikni na zemljevid.", null);
S.obnovi = izPovezave;         // samo ob odprtju strani, ne ob "Poišči"
if (izPovezave) isci();

pkUstvari($("#karta")).then((k) => {
  if (!k) {
    // Seznam predlogov dela tudi brez zemljevida; povemo, zakaj ga ni.
    document.body.classList.add("brez-zemljevida");
    $("#karta").innerHTML = '<p class="ni-zemljevida">Ta brskalnik zemljevida ne zna narisati.'
      + " Predlogi in koraki delajo tudi brez njega.</p>";
    return;
  }
  K = k;
  K.map.addControl(new K.ml.NavigationControl({ visualizePitch: true }), "top-left");
  K.map.on("click", (e) => {
    // Dotik oznake ali postajališča ni nov kraj -- sicer bi klik na "Cilj"
    // cilj premaknil pod prst.
    if (e.originalEvent.target.closest(".maplibregl-marker")) return;
    if (K.map.queryRenderedFeatures(e.point, { layers: ["k-tocke"] }).length) return;
    postavi(S.arm, { lat: e.lngLat.lat, lon: e.lngLat.lng });
  });
  if (S.jaz) pkJaz(K.map, S.jaz);
  if (S.izidi && S.izidi.predlogi.length) {
    narisiPot(S.izidi.predlogi[S.izbran]);
    const p = S.izidi.predlogi[S.izbran];
    pkPrilagodi(K.map, [[S.od.lat, S.od.lon], [S.do.lat, S.do.lon],
                        ...p.noge.flatMap((n) => [n.od_ll, n.do_ll])],
                { animate: false });
  } else {
    narisiTocke();
  }
});
