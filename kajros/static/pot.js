/* Najhitrejša pot: iz točke na zemljevidu do druge točke.
 *
 * Edina stran, ki se ne začne pri postaji, ampak pri **točki**: potnik ve, kje
 * stoji, ne pa, s katere postaje mu pelje. Zato sta vhoda dva kraja in ne dve
 * imeni, iskanje pa teče čez obe omrežji.
 *
 * Naslova ne iščemo. Geokodiranje pomeni tujo storitev, ki ob vsakem tipkanju
 * izve, kam greš — in prav temu se ta projekt izogiba. Kraj se izbere na
 * zemljevidu, iz lastne lege ali po imenu postaje, ki jo že poznamo.
 */

// `ESRI_ATTR` je v `common.js` -- druga razglasitev bi bila `SyntaxError` in
// stran ne bi delala nic.
const ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas";

const map = L.map("karta", { zoomControl: true }).setView([46.1, 14.6], 8);
L.tileLayer(`${ESRI}/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}`, {
  maxZoom: 19, maxNativeZoom: 16, attribution: ESRI_ATTR,
}).addTo(map);
// Napisi so tu SVETLI, drugace kot na velikem zemljevidu. Tam imena tekmujejo
// z vozili, ki so edini razlog za tisto stran; tu je vprašanje "kje je to" in
// brez berljivih imen se človek na zemljevidu ne znajde. Plast je ista, le
// posvetljena -- Esri svetlejše različice napisov nima.
L.tileLayer(`${ESRI}/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}`,
            { maxZoom: 19, maxNativeZoom: 16, className: "napisi-svetlo" }).addTo(map);

const tockeLayer = L.layerGroup().addTo(map);
const potLayer = L.layerGroup().addTo(map);
const jazLayer = L.layerGroup().addTo(map);

// Kaj bo pobral naslednji klik na zemljevid. Brez tega bi bil klik dvoumen:
// prvi klik postavi izhodišče, drugi cilj, tretji pa nič ne pomeni.
const S = { od: null, do: null, arm: "od", izidi: null, izbran: 0, jaz: null };

const $ = (s) => document.querySelector(s);
const stanje = $("#pot-stanje");
const izidiEl = $("#pot-izidi");

function povej(besedilo, vrsta) {
  stanje.className = "pot-stanje" + (vrsta ? " je-" + vrsta : "");
  stanje.textContent = besedilo || "";
}

// ---------------------------------------------------------------- hoja po meri

// Koliko minut hoje potnik dovoli. "Po meri" odkrije polje s številko; meji
// sta isti kot na endpointu, ker bi polje, ki dovoli več od strežnika, lagalo.
function hojeMin() {
  const izbira = $("#hoje").value;
  if (izbira !== "po-meri") return Number(izbira);
  const n = Number($("#hoje-meri").value);
  return Number.isFinite(n) && n >= 3 ? Math.min(45, Math.round(n)) : 25;
}

function nastaviHoje(minut) {
  const sel = $("#hoje");
  const polje = $("#hoje-meri");
  if ([...sel.options].some((o) => o.value === String(minut))) {
    sel.value = String(minut);
    polje.hidden = true;
    return;
  }
  sel.value = "po-meri";
  polje.value = minut;
  polje.hidden = false;
}

// ---------------------------------------------------------------- kraji

function narisiTocke(premakni = true) {
  tockeLayer.clearLayers();
  for (const kaj of ["od", "do"]) {
    const t = S[kaj];
    if (!t) continue;
    L.circleMarker([t.lat, t.lon], {
      radius: 8, weight: 3, color: "#ffffff",
      fillColor: kaj === "od" ? "#2f7fff" : "#f0934f",
      fillOpacity: 1,
    }).addTo(tockeLayer).bindTooltip(kaj === "od" ? "od kod" : "kam");
  }
  if (!premakni) return;
  if (S.od && S.do) {
    map.fitBounds(L.latLngBounds([[S.od.lat, S.od.lon], [S.do.lat, S.do.lon]]),
                  { padding: [50, 50], maxZoom: 14 });
  } else if (S.od || S.do) {
    const t = S.od || S.do;
    map.setView([t.lat, t.lon], Math.max(map.getZoom(), 13));
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
}

function oznaciArm() {
  document.querySelectorAll(".tocka").forEach((el) => {
    el.classList.toggle("je-arm", el.dataset.kaj === S.arm);
  });
}

map.on("click", (e) => postavi(S.arm, { lat: e.latlng.lat, lon: e.latlng.lng }));

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
// zemljevidu — na telefonu je to klik, ki hiše ne zadene, in prav zaradi tega
// je bila ta stran za vsakodnevno rabo nerodna.
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
// da jo postaviš (dotik na žeton) in odtakneš zvezdico. Dve poti do istega
// dejanja bi pri dveh poljih pomenili dvanajst gumbov za šest točk.
function oznaciZvezde() {
  for (const kaj of ["od", "do"]) {
    const b = document.querySelector(`.tocka[data-kaj="${kaj}"] .tocka-shrani`);
    const t = S[kaj];
    // **Zvezdica opisuje postavljeno točko, ne besedila v polju.** Med
    // tipkanjem polje že govori o drugem kraju, točka pa je še stara — in
    // zvezdica je takrat trdila „★ shranjeno“ nad tujim imenom. Dotik nanjo
    // bi odstranil točko, ki je človek sploh ni gledal, zato je dotlej ni.
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
// in enkrat cilj, in dotik mora povedati, kam gre. En sam seznam bi bil isti
// ugib kot klik na zemljevid brez oznake, kateri klik gre kam.
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
  // Ime postaje je dober privzetek; „moja lega“ in koordinate nista ime kraja.
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

// ---------------------------------------------------------------- iskanje postaj
//
// Kazalo se naloži ENKRAT in išče se v brskalniku. Poizvedba na strežnik je
// bila za obe omrežji izmerjeno 1,35 s na razvojnem računalniku -- okoli pet
// na arwenu, in to na vsak pritisk tipke. Postaje se ne spreminjajo vsak dan.

const KAZALO_KLJUC = "kajros:kazalo-vse";
const KAZALO_VELJA_MS = 12 * 3600 * 1000;
let KAZALO = null;

async function naloziKazalo() {
  try {
    const shranjeno = JSON.parse(localStorage.getItem(KAZALO_KLJUC) || "null");
    if (shranjeno && Date.now() - shranjeno.ts < KAZALO_VELJA_MS) {
      KAZALO = shranjeno.v.map((s) => ({ ...s, f: fold(s.n) }));
      return;
    }
  } catch (e) { /* pokvarjen zapis: preberemo znova */ }
  try {
    const r = await fetch("/api/stations/index?network=vse&koordinate=1");
    if (!r.ok) return;
    const v = await r.json();
    KAZALO = v.map((s) => ({ ...s, f: fold(s.n) }));
    try {
      localStorage.setItem(KAZALO_KLJUC, JSON.stringify({ ts: Date.now(), v }));
    } catch (e) { /* poln ali zavrnjen localStorage ni napaka */ }
  } catch (e) { /* brez kazala ostane zemljevid */ }
}

function zapriZadetke(kaj) {
  const ul = document.querySelector(`.tocka[data-kaj="${kaj}"] .tocka-zadetki`);
  ul.hidden = true;
  ul.innerHTML = "";
}

function pripniIskanje(kaj) {
  const vnos = $(`#q-${kaj}`);
  const ul = document.querySelector(`.tocka[data-kaj="${kaj}"] .tocka-zadetki`);
  const isci_ = () => {
    oznaciZvezde();          // polje se je razšlo s točko: zvezdica gre stran
    const q = vnos.value.trim();
    if (q.length < 2 || !KAZALO) return zapriZadetke(kaj);
    const najdbe = iskalnikKazala(KAZALO, q);
    ul.innerHTML = najdbe.map((s, i) =>
      `<li><button type="button" data-i="${i}">${escapeHtml(s.n)}</button></li>`).join("");
    ul.hidden = najdbe.length === 0;
    ul.querySelectorAll("button").forEach((b) => {
      b.addEventListener("click", () => {
        const s = najdbe[Number(b.dataset.i)];
        postavi(kaj, { lat: s.lat, lon: s.lon, ime: s.n });
      });
    });
  };
  vnos.addEventListener("input", isci_);
  vnos.addEventListener("focus", () => { S.arm = kaj; oznaciArm(); isci_(); });
}

// ---------------------------------------------------------------- moja lega

let ustaviSledenje = null;

function risiJaz(loc) {
  S.jaz = loc;
  drawMe(jazLayer, loc);
}

function zacniSledenje() {
  if (ustaviSledenje) return;
  ustaviSledenje = sledi(risiJaz);
}

document.querySelectorAll(".tocka").forEach((el) => {
  const kaj = el.dataset.kaj;
  pripniIskanje(kaj);
  // Žetoni se prerišejo ob vsaki spremembi, zato posluša blok in ne žeton:
  // poslušalec, pripet ob izrisu, bi se ob petem shranjevanju pripel petkrat.
  el.addEventListener("click", (e) => {
    const z = e.target.closest(".tocka-zeton");
    if (!z) return;
    const t = tockeBeri()[Number(z.dataset.i)];
    if (t) postavi(kaj, { lat: t.lat, lon: t.lon, ime: t.ime });
  });
  el.querySelector(".tocka-ime-vnos").addEventListener("keydown", (e) => {
    if (e.key === "Enter") shraniTocko(kaj);
    // Enter tu ne sme iskati — iskanje je drugo vprašanje od poimenovanja.
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
        return;
      }
      // GPS brez omrežnega določanja lege rabi lahko pol minute. Molk je v
      // tem času videti kot pokvarjen gumb, zato povemo, kje smo -- vključno
      // s trenutno natančnostjo, ki je edino merilo, ali se sploh premika.
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
        // Sledenje teče naprej: prvi popravek GPS pogosto zgreši za sto metrov
        // in ga v naslednjih sekundah popravi, potnik pa se medtem premika.
        zacniSledenje();
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

// Cez celo STRAN, ne cez cel zaslon -- isti razlog kot pri oknu voznje:
// fullscreen vzame ves monitor in skrije naslovno vrstico, gumb nazaj in vsak
// drug orientir, izhod pa je tipka, ki je na telefonu ni.
function velikost(veliko) {
  document.body.classList.toggle("karta-velika", veliko);
  const b = $("#karta-max");
  b.setAttribute("aria-pressed", String(veliko));
  b.title = veliko ? "Pomanjšaj zemljevid" : "Zemljevid čez celo stran";
  requestAnimationFrame(() => map.invalidateSize());
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

function zamudaHtml(z) {
  if (!z) return "";
  const barva = delayColor(z);
  return `<span class="zam" style="color:${barva};border-color:${barva}55">`
    + `${escapeHtml(delayText(z, true))}</span>`;
}

// Veriga poti v eni vrstici: "peš 12 › LPV 2268 +5 › peš 7". Prej je bila
// vsaka noga svoja vrstica z urami in postajami -- štirje predlogi so dali
// dvajset vrstic, med katerimi ni bilo mogoče izbirati na pogled. Podrobnosti
// so na svoji strani; tu šteje, s čim greš in koliko hodiš.
// Rezerva prestopa mora ostati v verigi. Brez nje "1 prestop" ne pove, ali
// zveza drži -- in prav to je edino, zaradi česar je prestop vreden pozornosti.
function prestopHtml(t, pred, po) {
  const mins = preostanekPrestopa(t.nacrtovano_s, pred && pred.zamuda, po && po.zamuda);
  if (mins == null) {
    const n = Math.floor(t.nacrtovano_s / 60 + 0.5);
    return `<span class="v-prestop">${n} min za prestop</span>`;
  }
  const barva = mins < 2 ? "var(--sev-bad)" : mins < 5 ? "var(--sev-hard)" : "var(--ok)";
  return `<span class="v-prestop" style="color:${barva}">${
    escapeHtml(prestopText(mins))}</span>`;
}

function verigaHtml(p) {
  const voznje = p.noge.filter((n) => n.vrsta === "voznja");
  const cleni = [];
  for (const n of p.noge) {
    const i = voznje.indexOf(n);
    if (i > 0 && p.prestopi && p.prestopi[i - 1]) {
      cleni.push(prestopHtml(p.prestopi[i - 1], voznje[i - 1], n));
    }
    if (n.vrsta === "hoja") {
      cleni.push(`<span class="v-hoja">peš ${Math.floor(n.sekunde / 60 + 0.5)}</span>`);
      continue;
    }
    const kdo = AGENCY[n.agency];
    const oznaka = kdo ? `${kdo} ${n.train_no}` : n.train_no;
    cleni.push(`<span class="v-linija">${escapeHtml(oznaka)}</span>${zamudaHtml(n.zamuda)}`);
  }
  return cleni.join('<span class="v-loc" aria-hidden="true">›</span>');
}

// Naslov podrobne strani. Vožnje so v naslovu, ne v seji: pot mora ostati
// deljiva, in kdor jo komu pošlje, mu pošlje pot, ne svojega brskalnika.
function podrobnoUrl(p) {
  const noge = p.noge.filter((n) => n.vrsta === "voznja")
    .map((n) => `${n.trip_id}:${n.od_seq}:${n.do_seq}`).join(";");
  if (!noge) return null;            // pot vso pot peš nima česa razložiti
  const q = new URLSearchParams({
    noge, od_lat: S.od.lat, od_lon: S.od.lon,
    do_lat: S.do.lat, do_lon: S.do.lon,
  });
  return `/app/pot/podrobno?${q}`;
}

function predlogHtml(p, i) {
  const prestopi = p.prestopov === 0
    ? (p.noge.some((n) => n.vrsta === "voznja") ? "brez prestopa" : "vso pot peš")
    : `${p.prestopov} ${sklon(p.prestopov, "prestop")}`;
  const zamudno = p.prihod_ocena && p.prihod_ocena !== p.prihod
    ? ` · <span class="p-vr">vozni red ${ura(p.odhod)} → ${ura(p.prihod)}</span>` : "";
  const url = podrobnoUrl(p);
  const znacka = url ? "a" : "article";
  const kam = url ? ` href="${url}"` : "";
  return `<${znacka} class="predlog${i === 0 ? " je-prvi" : ""}" data-i="${i}"${kam}>
    <div class="p-ure">
      <strong>${ura(p.odhod_ocena || p.odhod)}</strong>
      <span class="p-pusc" aria-hidden="true">→</span>
      <strong>${ura(p.prihod_ocena || p.prihod)}</strong>
      <span class="p-traj">${minute(p.trajanje_s)}</span>
    </div>
    <div class="p-veriga">${verigaHtml(p)}</div>
    <div class="p-meta">${prestopi}${p.hoje_s >= 60
      ? ` · ${minute(p.hoje_s)} hoje` : ""}${zamudno}</div>
  </${znacka}>`;
}

// Ravna črta med postajama ni proga. Zato se najprej nariše kot skica, nato
// pa jo zamenja prava trasa iz `shape` -- ista, ki jo riše zemljevid.
let izrisZeton = 0;
async function narisiPot(p) {
  const moj = ++izrisZeton;
  potLayer.clearLayers();
  if (!p) return;
  const skice = [];
  for (const n of p.noge) {
    const a = n.od_ll || (S.od && [S.od.lat, S.od.lon]);
    const b = n.do_ll || (S.do && [S.do.lat, S.do.lon]);
    if (!a || !b) continue;
    // Hoja je črtkana, vožnja polna: potnik mora na prvi pogled videti, kje
    // ga nese vozilo in kje njegove noge.
    const crta = L.polyline([a, b], n.vrsta === "hoja"
      ? { color: "#2f7fff", weight: 3, dashArray: "4 6", opacity: 0.9 }
      : { color: "#f0934f", weight: 4, opacity: 0.55 }).addTo(potLayer);
    if (n.vrsta === "voznja") skice.push([n, crta]);
  }
  for (const [n, crta] of skice) {
    const t = await trasa(n).catch(() => null);
    if (moj !== izrisZeton) return;      // vmes je bil izbran drug predlog
    if (!t) { crta.setStyle({ opacity: 0.9 }); continue; }
    crta.setLatLngs(t);
    crta.setStyle({ opacity: 0.9 });
  }
}

// Kaj bi pomagalo, kadar z vozilom ni ničesar. Meja hoje velja do postaje;
// kadar je prvo uporabno postajališče tik čez njo, je to ugotovitev in ne
// ugibanje. Da bi s tem pot res nastala, ne obljubljamo -- postajališče v
// dosegu še ni zveza, in tako tudi piše.
function nasvetHtml(n) {
  if (!n) return "";
  if (n.ni_zveze) {
    return ' <span class="nasvet">Postajališča so v dosegu, zveze med njimi ta '
      + "čas ni.</span>";
  }
  return ` <span class="nasvet">Najbližje postajališče je <strong>${n.vec_hoje_min} min</strong>`
    + ` hoje — <button type="button" id="vec-hoje" data-min="${n.vec_hoje_min}">`
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

// Ura, ki je danes že mimo, ni napaka — včasih človek res gleda nazaj — a mora
// biti povedano. Doslej je stran na vprašanje „ob 06:00“ ob treh popoldne
// vrnila jutranje odhode, kot da so pred tabo, in nič na zaslonu ni namignilo,
// da gleda v preteklost.
function zeMimo() {
  const ob = $("#ob").value;
  if (!ob) return false;                        // prazno pomeni „zdaj“
  if (($("#dan").value || todayIso()) !== todayIso()) return false;
  // „HH:MM“ se primerja kot niz, ker sta obe uri po ljubljanskem času in
  // enako dolgi -- datuma iz njiju ni treba sestavljati.
  return ob < TIME_FMT.format(new Date());
}

function mimoHtml() {
  if (!zeMimo()) return "";
  return ' <span class="nasvet">Ta ura je danes že mimo — predlogi so za nazaj.'
    + ' <button type="button" id="od-zdaj">poišči od zdaj</button></span>';
}

function pripniMimo() {
  const b = document.getElementById("od-zdaj");
  if (!b) return;
  b.addEventListener("click", () => { $("#ob").value = ""; isci(); });
}

function izrisi(izid) {
  S.izidi = izid;
  S.izbran = 0;
  const mimo = mimoHtml();
  if (!izid.predlogi.length) {
    izidiEl.innerHTML = "";
    povej("", "prazno");
    stanje.innerHTML = "Za ta čas ni poti. Poskusi pozneje ali dovoli več hoje."
      + mimo;
    pripniMimo();
    potLayer.clearLayers();
    return;
  }
  // Vir hoje ni podrobnost: zasilna ocena je izmerjeno mediano 6 minut
  // predolga, in kdor tega ne ve, bere številke kot izmerjene.
  const opomba = izid.vir_hoje === "osrm" ? ""
    : " · hoja je <strong>ocena</strong>, ker usmerjevalnik ne odgovarja";
  povej("");
  // Kadar je hoja edino, kar imamo, je treba povedati zakaj -- sicer je videti
  // kot da smo prezrli avtobus, ki ga v resnici ni.
  if (izid.predlogi.length === 1 && izid.predlogi[0].edina) {
    stanje.innerHTML = "Z vozilom ni poti, ki bi bila hitrejša od hoje."
      + ` · ${dayLabel(izid.datum)}${opomba}${nasvetHtml(izid.nasvet)}${mimo}`;
    pripniNasvet();
  } else {
    stanje.innerHTML = `${izid.predlogi.length} ${sklon(izid.predlogi.length, "predlog")}`
      + ` · ${dayLabel(izid.datum)}${opomba}${mimo}`;
  }
  pripniMimo();
  izidiEl.innerHTML = izid.predlogi.map((p, i) => predlogHtml(p, i)).join("");
  // Kartica je povezava na podrobno stran, zato klik ne sme izbirati. Na
  // zemljevidu se pot pokaže ob dotiku ali fokusu -- to ne odvzame klika in
  // na telefonu ne naredi ničesar, kar bi bilo v napoto.
  izidiEl.querySelectorAll(".predlog").forEach((el) => {
    const pokazi = () => {
      S.izbran = Number(el.dataset.i);
      izidiEl.querySelectorAll(".predlog").forEach((x) =>
        x.classList.toggle("je-izbran", Number(x.dataset.i) === S.izbran));
      narisiPot(izid.predlogi[S.izbran]);
    };
    el.addEventListener("mouseenter", pokazi);
    el.addEventListener("focus", pokazi);
  });
  narisiPot(izid.predlogi[0]);
}

// ---------------------------------------------------------------- poizvedba

async function isci() {
  if (!S.od || !S.do) {
    povej("Manjka " + (!S.od ? "izhodišče" : "cilj") + ".", "napaka");
    return;
  }
  const p = new URLSearchParams({
    od_lat: S.od.lat, od_lon: S.od.lon, do_lat: S.do.lat, do_lon: S.do.lon,
    hoje: hojeMin(),
  });
  if ($("#ob").value) p.set("ob", $("#ob").value);
  if ($("#dan").value) p.set("date", $("#dan").value);
  povej("Iščem …", null);
  izidiEl.innerHTML = "";
  vUrl();
  try {
    const r = await fetch(`/api/pot?${p}`);
    if (!r.ok) {
      const telo = await r.json().catch(() => ({}));
      throw new Error(telo.detail || `strežnik je vrnil ${r.status}`);
    }
    izrisi(await r.json());
  } catch (e) {
    povej(e.message, "napaka");
  }
}

$("#hoje").addEventListener("change", () => {
  const polje = $("#hoje-meri");
  polje.hidden = $("#hoje").value !== "po-meri";
  if (!polje.hidden) {
    if (!polje.value) polje.value = 25;
    polje.focus();
    polje.select();
  }
});
$("#hoje-meri").addEventListener("keydown", (e) => { if (e.key === "Enter") isci(); });
$("#isci").addEventListener("click", isci);
document.querySelectorAll(".tocka-vnos").forEach((el) =>
  el.addEventListener("keydown", (e) => { if (e.key === "Enter") isci(); }));

// ---------------------------------------------------------------- naslov strani
//
// Pot mora biti deljiva. Brez tega je edini nacin, da nekomu poves, kako priti
// do tebe, opis s stavki -- in prav to je stran, ki naj bi ga nadomestila.

function vUrl() {
  const q = new URLSearchParams();
  if (S.od) q.set("od", `${S.od.lat.toFixed(5)},${S.od.lon.toFixed(5)}`);
  if (S.do) q.set("do", `${S.do.lat.toFixed(5)},${S.do.lon.toFixed(5)}`);
  if ($("#ob").value) q.set("ob", $("#ob").value);
  // Današnjega dne v naslov ne pišemo: deljena povezava brez dneva pomeni
  // „danes“ in jutri odgovori na jutrišnji dan, kar je skoraj vedno mišljeno.
  if ($("#dan").value && $("#dan").value !== todayIso()) q.set("dan", $("#dan").value);
  if (hojeMin() !== 25) q.set("hoje", hojeMin());
  // Velikost zemljevida gre v naslov: kdor pot deli, deli tudi pogled nanjo,
  // in ponovno nalaganje ne vrne zemljevida v okence.
  if (document.body.classList.contains("karta-velika")) q.set("karta", "velika");
  history.replaceState(null, "", q.toString() ? `?${q}` : location.pathname);
}

function izUrl() {
  const q = new URLSearchParams(location.search);
  const tocka = (niz) => {
    const [a, b] = String(niz).split(",").map(Number);
    return Number.isFinite(a) && Number.isFinite(b) ? { lat: a, lon: b } : null;
  };
  let imamo = false;
  for (const kaj of ["od", "do"]) {
    const t = q.get(kaj) && tocka(q.get(kaj));
    if (!t) continue;
    // Naslov nosi samo koordinate; kadar so tvoje, jim ime pripiše brskalnik
    // sam — „dom“ pove več kot 46.05611, 14.50577.
    const s = shranjenaZa(t);
    if (s) t.ime = s.ime;
    S[kaj] = t;
    $(`#q-${kaj}`).value = napisTocke(t);
    imamo = true;
  }
  if (q.get("ob")) $("#ob").value = q.get("ob");
  $("#dan").value = q.get("dan") || todayIso();
  if (q.get("hoje")) nastaviHoje(Number(q.get("hoje")));
  if (q.get("karta") === "velika") velikost(true);
  S.arm = S.od ? "do" : "od";
  if (imamo) narisiTocke();
  return S.od && S.do;
}

pripniDnevnePuscice();
// Kadar je odgovor že na zaslonu, ga spremenjeno vprašanje osveži; dokler ga
// ni, išče samo gumb — vsak vmesni ugib je zahteva za odgovor, ki ga nihče ni
// prosil (isto pravilo kot na vstopni strani).
for (const id of ["#dan", "#ob"]) {
  $(id).addEventListener("change", () => { if (S.izidi) isci(); });
}

oznaciArm();
povej("Klikni na zemljevid ali vpiši postajo.", null);
naloziKazalo();
const izPovezave = izUrl();
izrisiTocke();                 // zvezdice vedo za kraja šele, ko ju naslov postavi
if (izPovezave) isci();
