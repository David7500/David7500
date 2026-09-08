/* Pot od vrat do vrat.
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
L.tileLayer(`${ESRI}/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}`,
            { maxZoom: 19, maxNativeZoom: 16, opacity: 0.9 }).addTo(map);

const tockeLayer = L.layerGroup().addTo(map);
const potLayer = L.layerGroup().addTo(map);

// Kaj bo pobral naslednji klik na zemljevid. Brez tega bi bil klik dvoumen:
// prvi klik postavi izhodišče, drugi cilj, tretji pa nič ne pomeni.
const S = { od: null, do: null, arm: "od", izidi: null, izbran: 0 };

const $ = (s) => document.querySelector(s);

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
const stanje = $("#pot-stanje");
const izidiEl = $("#pot-izidi");

function povej(besedilo, vrsta) {
  stanje.className = "pot-stanje" + (vrsta ? " je-" + vrsta : "");
  stanje.textContent = besedilo || "";
}

// ---------------------------------------------------------------- kraji

function narisiTocke() {
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
  if (S.od && S.do) {
    map.fitBounds(L.latLngBounds([[S.od.lat, S.od.lon], [S.do.lat, S.do.lon]]),
                  { padding: [50, 50], maxZoom: 14 });
  } else if (S.od || S.do) {
    const t = S.od || S.do;
    map.setView([t.lat, t.lon], Math.max(map.getZoom(), 13));
  }
}

function postavi(kaj, tocka) {
  S[kaj] = tocka;
  const vnos = $(`#q-${kaj}`);
  vnos.value = tocka.ime || `${tocka.lat.toFixed(5)}, ${tocka.lon.toFixed(5)}`;
  zapriZadetke(kaj);
  narisiTocke();
  // Prvi klik postavi izhodišče, naslednji cilj -- brez tega bi moral človek
  // pred vsakim klikom povedati, kaj postavlja.
  S.arm = S.od && !S.do ? "do" : kaj === "od" ? "do" : "od";
  oznaciArm();
}

function oznaciArm() {
  document.querySelectorAll(".tocka").forEach((el) => {
    el.classList.toggle("je-arm", el.dataset.kaj === S.arm);
  });
}

map.on("click", (e) => postavi(S.arm, { lat: e.latlng.lat, lon: e.latlng.lng }));

// ---------------------------------------------------------------- iskanje postaj

function zapriZadetke(kaj) {
  const ul = document.querySelector(`.tocka[data-kaj="${kaj}"] .tocka-zadetki`);
  ul.hidden = true;
  ul.innerHTML = "";
}

let casovnik = null;
function pripniIskanje(kaj) {
  const vnos = $(`#q-${kaj}`);
  const ul = document.querySelector(`.tocka[data-kaj="${kaj}"] .tocka-zadetki`);
  vnos.addEventListener("input", () => {
    clearTimeout(casovnik);
    const q = vnos.value.trim();
    if (q.length < 2) return zapriZadetke(kaj);
    casovnik = setTimeout(async () => {
      // `network=vse`: tu sta vlak in avtobus lahko v isti verigi, zato bi
      // delitev na omrežji skrila polovico krajev.
      const r = await fetch(`/api/stations/search?q=${encodeURIComponent(q)}&network=vse&limit=8`);
      if (!r.ok) return;
      const najdbe = await r.json();
      ul.innerHTML = najdbe.map((s, i) =>
        `<li><button data-i="${i}">${escapeHtml(s.name)}</button></li>`).join("");
      ul.hidden = najdbe.length === 0;
      ul.querySelectorAll("button").forEach((b) => {
        b.addEventListener("click", () => {
          const s = najdbe[Number(b.dataset.i)];
          postavi(kaj, { lat: s.lat, lon: s.lon, ime: s.name });
        });
      });
    }, 180);
  });
  vnos.addEventListener("focus", () => { S.arm = kaj; oznaciArm(); });
}

document.querySelectorAll(".tocka").forEach((el) => {
  const kaj = el.dataset.kaj;
  pripniIskanje(kaj);
  el.querySelectorAll(".tocka-gumb").forEach((b) => {
    b.addEventListener("click", async () => {
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
          napredek: (l) => povej(`Iščem tvojo lego … zaenkrat na ${Math.round(l.acc)} m`, null),
        });
        postavi(kaj, { lat: loc.lat, lon: loc.lon, ime: "moja lega" });
        povej(loc.acc > 200
          ? `Lega je natančna na ${Math.round(loc.acc)} m — po potrebi popravi na zemljevidu.`
          : "");
      } catch (e) {
        povej(e.message, "napaka");
      }
    });
  });
});

// ---------------------------------------------------------------- izris predlogov

const ura = (ts) => new Date(ts * 1000).toLocaleTimeString("sl-SI",
  { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Ljubljana" });

function minute(s) {
  const m = Math.floor(s / 60 + 0.5);
  return m < 60 ? `${m} min` : `${Math.floor(m / 60)} h ${String(m % 60).padStart(2, "0")}`;
}

// Zeton zamude. Barva nikoli sama: poleg nje sta minuta IN beseda o tem, od
// kod je -- "izmerjeno" in "ocena" nista ista trditev.
function zamudaHtml(z) {
  if (!z) return "";
  const barva = delayColor(z);
  const vrsta = z.vrsta ? ` <span class="zam-vrsta">${escapeHtml(z.vrsta)}</span>` : "";
  return `<span class="zam" style="color:${barva};border-color:${barva}55">`
    + `${escapeHtml(delayText(z))}</span>${vrsta}`;
}

function nogaHtml(n, sama) {
  if (n.vrsta === "hoja") {
    // Puscica in ne "od X do Y": imena postaj se v slovenscini sklanjajo in
    // splosnega pravila zanje ni. "do Grosuplje" je napacno, "do Grosupljega"
    // pa bi moral nekdo znati izpeljati iz "Grosuplje" -- in za "Bavarski
    // dvor" ali "Vic Glince" to ne bi delalo.
    const kam = n.do ? escapeHtml(n.do) : "cilj";
    const od = n.od ? escapeHtml(n.od) : "izhodišče";
    return `<li class="noga je-hoja">
      <span class="noga-znak" aria-hidden="true">↓</span>
      <span class="noga-telo">peš <strong>${minute(n.sekunde)}</strong>
        <span class="noga-kam">${od} → ${kam}</span></span></li>`;
  }
  const pot = n.network === "avtobus" ? "bus" : "train";
  const povezava = `/app/${pot}/${encodeURIComponent(n.train_no)}?trip=${encodeURIComponent(n.trip_id)}`;
  // Ura, ki jo potnik dozivi, je glavna; voznoredna ostane vidna poleg nje,
  // ker je edino, kar drzi, ce se zamuda vmes spremeni.
  const odh = n.odhod_ocena || n.odhod;
  const prih = n.prihod_ocena || n.prihod;
  const vr = !sama && n.odhod_ocena && n.odhod_ocena !== n.odhod
    ? `<span class="noga-vr">vozni red ${ura(n.odhod)} → ${ura(n.prihod)}</span>` : "";
  return `<li class="noga je-voznja">
    <span class="noga-znak" aria-hidden="true">●</span>
    <span class="noga-telo">
      <span class="noga-vrh">
        <a class="noga-linija" href="${povezava}">${escapeHtml(n.train_no)}</a>
        ${zamudaHtml(n.zamuda)}
      </span>
      <span class="noga-ure"><strong>${ura(odh)}</strong> ${escapeHtml(n.od)}
        → <strong>${ura(prih)}</strong> ${escapeHtml(n.do)}</span>
      ${vr}
    </span></li>`;
}

// Preostanek prestopa se racuna iz ZAOKROZENIH minut, ne iz sekund: na
// zaslonu stojijo vse tri stevilke druga ob drugi in bralec, ki jih sesteje,
// mora priti do iste. Ista past kot pri razredu zamude.
function prestopHtml(t, pred, po) {
  const nacrt = Math.floor(t.nacrtovano_s / 60 + 0.5);
  const d1 = delayMin(pred && pred.zamuda);
  const d2 = delayMin(po && po.zamuda);
  const znano = d1 != null && d2 != null;
  const mins = znano ? nacrt - d1 + d2 : nacrt;
  const barva = !znano ? "var(--ink-mute)" : mins < 2 ? "var(--sev-bad)"
    : mins < 5 ? "var(--sev-hard)" : "var(--ok)";
  const pes = t.pes_s >= 60 ? ` · ${minute(t.pes_s)} hoje vmes` : "";
  return `<li class="noga je-prestop">
    <span class="noga-znak" aria-hidden="true">⇄</span>
    <span class="noga-telo" style="color:${barva}">
      ${escapeHtml(znano ? prestopText(mins) : `${nacrt} min za prestop`)}
      <span class="noga-kam">v ${escapeHtml(t.kje)}${pes}${znano ? "" : " · brez zamud"}</span>
    </span></li>`;
}

// Prestop stoji MED nogama, ki ju veze -- ne v svojem seznamu pod potjo,
// kjer bi bralec moral sam ugotoviti, na kateri prestop se nanasa.
function nogeHtml(p) {
  const voznje = p.noge.filter((n) => n.vrsta === "voznja");
  const out = [];
  for (const n of p.noge) {
    const i = voznje.indexOf(n);
    if (i > 0 && p.prestopi && p.prestopi[i - 1]) {
      out.push(prestopHtml(p.prestopi[i - 1], voznje[i - 1], n));
    }
    out.push(nogaHtml(n, voznje.length === 1));
  }
  return out.join("");
}

// Kadar se ura z zamudo razlikuje od voznorednega, mora bralec videti obe --
// sicer ne ve, ali gleda vozni red ali napoved.
function zamudno(p) {
  if (!p.prihod_ocena || p.prihod_ocena === p.prihod) return "";
  return ` <span class="predlog-vr">vozni red ${ura(p.odhod)} → ${ura(p.prihod)}</span>`;
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
  if ($("#ob").value) q.set("date", S.izidi ? S.izidi.datum : "");
  return `/app/pot/podrobno?${q}`;
}

function predlogHtml(p, i, izbran) {
  const prestopi = p.prestopov === 0
    ? (p.noge.some((n) => n.vrsta === "voznja") ? "brez prestopa" : "vso pot peš")
    : `${p.prestopov} ${sklon(p.prestopov, "prestop")}`;
  const url = podrobnoUrl(p);
  const znacka = url ? "a" : "article";
  const kam = url ? ` href="${url}"` : "";
  return `<${znacka} class="predlog${i === izbran ? " je-izbran" : ""}" data-i="${i}"${kam}>
    <header class="predlog-glava">
      <span class="predlog-ure"><strong>${ura(p.odhod_ocena || p.odhod)}</strong>
        → <strong>${ura(p.prihod_ocena || p.prihod)}</strong>${zamudno(p)}</span>
      <span class="predlog-meta">${minute(p.trajanje_s)}${p.hoje_s >= 60
        ? ` · ${minute(p.hoje_s)} hoje` : ""} · ${prestopi}</span>
    </header>
    <ol class="noge">${nogeHtml(p)}</ol>
    ${url ? '<span class="predlog-vec">podrobno →</span>' : ""}
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

function izrisi(izid) {
  S.izidi = izid;
  S.izbran = 0;
  if (!izid.predlogi.length) {
    izidiEl.innerHTML = "";
    povej("Za ta čas ni poti. Poskusi pozneje ali dovoli več hoje.", "prazno");
    potLayer.clearLayers();
    return;
  }
  // Vir hoje ni podrobnost: zasilna ocena je izmerjeno mediano 6 minut
  // predolga, in kdor tega ne ve, bere številke kot izmerjene.
  const opomba = izid.vir_hoje === "osrm" ? ""
    : " · hoja je <strong>ocena</strong>, ker usmerjevalnik ne odgovarja";
  povej("");
  stanje.innerHTML = `${izid.predlogi.length} ${sklon(izid.predlogi.length, "predlog")}`
    + ` · ${dayLabel(izid.datum)}${opomba}`;
  izidiEl.innerHTML = izid.predlogi.map((p, i) => predlogHtml(p, i, 0)).join("");
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
  if (hojeMin() !== 25) q.set("hoje", hojeMin());
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
    if (t) { S[kaj] = t; $(`#q-${kaj}`).value = `${t.lat.toFixed(5)}, ${t.lon.toFixed(5)}`; imamo = true; }
  }
  if (q.get("ob")) $("#ob").value = q.get("ob");
  if (q.get("hoje")) nastaviHoje(Number(q.get("hoje")));
  S.arm = S.od ? "do" : "od";
  if (imamo) narisiTocke();
  return S.od && S.do;
}

oznaciArm();
povej("Klikni na zemljevid ali vpiši postajo.", null);
if (izUrl()) isci();
