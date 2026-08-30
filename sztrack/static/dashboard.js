"use strict";

// Živi zemljevid -- edini pogled, ki ga vlaki in avtobusi delita. Skupne
// funkcije so v common.js. Feed na strežniku osvežuje collector.py na
// config.POLL_SECONDS (privzeto 30 s); ta vrednost ni izpostavljena prek
// API-ja, zato je tu ločena kopija privzetka.
const POLL_MS = 30000;

function openTrainWindow(trainNo, tripId, serviceDate, network) {
  // Posamezno vozilo dobi svoje okno -- tam je poleg te vožnje še zgodovina.
  // `trip` in `date` gresta zraven, kadar ju poznamo: številka linije pri
  // avtobusu ni enolična, devet vlakov pa ima sezonske različice.
  const q = new URLSearchParams();
  if (serviceDate) q.set("date", serviceDate);
  if (tripId) q.set("trip", tripId);
  const pot = network === "avtobus" ? "/app/bus/" : "/app/train/";
  window.open(
    `${pot}${encodeURIComponent(trainNo)}${q.toString() ? `?${q}` : ""}`,
    `sztrack-${trainNo}`,
  );
}

// ---------- podlaga ----------

const map = L.map("map", { zoomControl: true }).setView([46.05, 14.95], 8);

// Lego zemljevida hranimo v naslovu: brez tega je "poglej, kje stoji" nemogoce
// deliti, osvezitev strani pa vrne cez vso Slovenijo. Naslov se popravlja
// tiho (`replaceState`), da gumb nazaj ostane gumb nazaj.
function mapStateToUrl() {
  const c = map.getCenter();
  const q = new URLSearchParams(location.search);
  q.set("lat", c.lat.toFixed(5));
  q.set("lon", c.lng.toFixed(5));
  q.set("z", String(map.getZoom()));
  history.replaceState(null, "", `?${q}`);
}

const URLQ = new URLSearchParams(location.search);
const startLat = parseFloat(URLQ.get("lat"));
const startLon = parseFloat(URLQ.get("lon"));
const startZ = parseInt(URLQ.get("z"), 10);
const HAS_START = Number.isFinite(startLat) && Number.isFinite(startLon)
  && Number.isFinite(startZ);
if (HAS_START) map.setView([startLat, startLon], startZ);
map.on("moveend zoomend", mapStateToUrl);

// Esri "Dark Gray Canvas" je razdeljen na DVE plasti: podlago brez napisov in
// oznake posebej. Prav to je razlog za zamenjavo -- OSM ima napise vpecene v
// ploscico in jih ni mogoce ugasniti, pri velikem priblizku pa ime vsake
// ulice tekmuje z vozili, ki so edini razlog za to stran.
//
// CARTO (dark_nolabels) zna isto, a ploscice pridejo z napisom "API KEY
// REQUIRED" cez pol zaslona -- preverjeno, ne uporabljati brez kljuca.
const ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas";
const ESRI_ATTR = 'podlaga &copy; <a href="https://www.esri.com/">Esri</a>, HERE, Garmin, '
  + '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';

const baseLayer = L.tileLayer(`${ESRI}/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}`, {
  maxZoom: 16, attribution: ESRI_ATTR,
}).addTo(map);

// Dodatna imena (kraji, znamenitosti). Podlaga sama ima pri velikem
// priblizku ze imena ulic in teh ni mogoce ugasniti: brezplacne podlage brez
// napisov ni -- CARTO `*_nolabels` pride z vodnim zigom "API KEY REQUIRED",
// wmflabs je ugasnjen, Wikimedia zunanjo rabo zavraca (403). Zato dvoje, kar
// res dela: to plast se da izklopiti, podlago pa v celoti odloziti.
const labelLayer = L.tileLayer(
  `${ESRI}/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}`,
  { maxZoom: 16, opacity: 0.9 },
);

// Vrstni red plasti je vrstni red risanja: proge in postaje spodaj, vozila
// zgoraj. Brez tega vlak izgine pod progo, po kateri vozi.
const netLayer = L.layerGroup().addTo(map);
const stationLayer = L.layerGroup().addTo(map);
const routeLayer = L.layerGroup().addTo(map);   // postajališča izbrane vožnje
const trainLayer = L.layerGroup().addTo(map);
const busLayer = L.layerGroup().addTo(map);

const stationMarkers = new Map();   // ime postaje -> L.CircleMarker
let stationsByName = new Map();     // ime postaje -> {stop_id, lat, lon}
let liveTrains = [];
let liveBuses = [];

async function loadStatic() {
  try {
    // Samo železniške postaje: avtobusnih je nekaj tisoč in mreža prog bi
    // izginila pod postajališči.
    const stations = await fetch("/api/stations?network=zeleznica").then((r) => r.json());
    stationsByName = new Map(stations.map((s) => [s.name, s]));
    const latlngs = [];
    for (const s of stations) {
      L.circleMarker([s.lat, s.lon], {
        radius: 2.4, color: "#8b95a4", fillColor: "#8b95a4", fillOpacity: 1,
        weight: 0, interactive: false,
      }).addTo(stationLayer);
      latlngs.push([s.lat, s.lon]);
    }
    if (latlngs.length && !HAS_START) map.fitBounds(latlngs, { padding: [24, 24] });
  } catch (err) {
    console.error("postaj ni bilo mogoče naložiti", err);
  }

  try {
    const geojson = await fetch("/api/network.geojson").then((r) => r.json());
    // Proga je narisana DVAKRAT: široka temna obroba spodaj, svetla črta
    // zgoraj. Ena sama črta se je na temni podlagi izgubila, debelejša pa je
    // bila videti kot cesta. Obroba jo loči od podlage, ne da bi jo odebelila.
    L.geoJSON(geojson, {
      style: { color: "#11141a", weight: 5.5, opacity: 0.9 }, interactive: false,
    }).addTo(netLayer);
    L.geoJSON(geojson, {
      style: { color: "#7d8899", weight: 2, opacity: 1 }, interactive: false,
    }).addTo(netLayer);
  } catch (err) {
    console.error("mreže ni bilo mogoče naložiti", err);
  }
}

// ---------- vlaki ----------

function worstDelay(trains) {
  // null (brez meritve) se ne sme obnašati kot 0 -- zato -Infinity kot izhodišče.
  return trains.reduce((acc, t) => {
    const v = bestDelay(t).value;
    return v != null && v > acc ? v : acc;
  }, -Infinity);
}

// Kraj in zamuda morata biti iz istega vira. Prevoznikovo poročilo pozna
// prometno mesto in je običajno svežje; naša `run` pozna samo voznoredne
// postanke. Kadar imamo oboje, vzamemo prevoznikovo -- a nikoli pol enega
// in pol drugega, sicer piše "Dobova" ob zamudi, izmerjeni v Sevnici.
function bestDelay(t) {
  if (t.reported_lat != null) {
    return {
      value: t.reported_delay_s, where: t.reported_at_station,
      ageS: t.reported_age_s, fromOperator: true,
    };
  }
  return { value: t.delay_s, where: t.last_stop, ageS: t.age_s, fromOperator: false };
}

function groupByStation(trains) {
  // Več vlakov stoji na isti postaji -- en marker na postajo, sicer se
  // markerji in oznake v vozliščih (Ljubljana, Zidani Most) prekrivajo.
  const groups = new Map();
  for (const t of trains) {
    const useReported = t.reported_lat != null;
    const where = useReported ? t.reported_at_station : t.last_stop;
    const station = useReported
      ? { lat: t.reported_lat, lon: t.reported_lon }
      : stationsByName.get(t.last_stop);
    if (!station) continue;
    let g = groups.get(where);
    if (!g) {
      g = { name: where, station, trains: [] };
      groups.set(where, g);
    }
    g.trains.push(t);
  }
  for (const g of groups.values()) {
    g.trains.sort((a, b) => (bestDelay(b).value ?? -1) - (bestDelay(a).value ?? -1));
  }
  return groups;
}

function trainLineHtml(t) {
  // Barva na markerju sama ne sme nositi pomena -- vedno zraven piše minuta.
  return `<span class="train-label-code">${escapeHtml(t.train_no)}</span>`
    + modeBadgeHtml(t.mode)
    + `<span class="train-label-delay" style="color:${delayColor(bestDelay(t).value)}">`
    + `${delayLabel(bestDelay(t).value)}</span>`;
}

function groupLabelHtml(g) {
  const shown = g.trains.slice(0, 3)
    .map((t) => `<div class="train-label-line">${trainLineHtml(t)}</div>`);
  if (g.trains.length > 3) {
    shown.push(`<div class="train-label-more">…in še ${g.trains.length - 3}</div>`);
  }
  return shown.join("");
}

function groupPopupHtml(g) {
  const rows = g.trains.map((t) => `
    <button class="popup-train" data-train="${escapeHtml(t.train_no)}"
            data-trip="${escapeHtml(t.trip_id || "")}"
            data-date="${escapeHtml(t.service_date || "")}">
      <span class="popup-train-code">${escapeHtml(t.train_no)}</span>${modeBadgeHtml(t.mode)}
      <span class="popup-train-headsign">${escapeHtml(t.headsign || "")}</span>
      <span class="popup-train-delay" style="color:${delayColor(bestDelay(t).value)}">${delayLabel(bestDelay(t).value)}</span>
    </button>`).join("");
  const measured = g.trains.map((t) => t.measured_at).filter(Boolean).sort().pop();
  return `
    <div class="popup-station">${escapeHtml(g.name)}</div>
    <div class="popup-note">zadnja postaja z meritvijo — ${g.trains.length === 1 ? "1 vlak" : `${g.trains.length} vlakov`}</div>
    <div class="popup-list">${rows}</div>
    <div class="popup-note">${measured ? `nazadnje izmerjeno ob ${hhmm(measured)} · ` : ""}klikni vlak za svoje okno</div>`;
}

function renderTrains(trains) {
  // Vlaki NIMAJO GPS lege -- marker je vedno točno na zadnji znani postaji,
  // nikoli interpoliran vzdolž proge.
  const groups = groupByStation(trains);
  for (const [name, g] of groups) {
    const worst = worstDelay(g.trains);
    const color = delayColor(worst === -Infinity ? null : worst);
    const latlng = [g.station.lat, g.station.lon];

    let marker = stationMarkers.get(name);
    if (!marker) {
      marker = L.circleMarker(latlng, {
        radius: g.trains.length > 1 ? 7 : 6, weight: 1.6,
        color: "#0f1115", fillColor: color, fillOpacity: 1,
      });
      // interactive: true doda oznaki razred leaflet-interactive in jo
      // registrira kot cilj -- brez tega klik na oznako ne sproži ničesar.
      marker.bindTooltip(groupLabelHtml(g), {
        className: "sztrack-tooltip sztrack-label", permanent: true,
        direction: "right", offset: [8, 0], interactive: true,
      });
      marker.bindPopup(groupPopupHtml(g));
      marker.on("click", () => {
        if (marker.__trains.length === 1) {
          marker.closePopup();
          const t0 = marker.__trains[0];
          openTrainWindow(t0.train_no, t0.trip_id, t0.service_date);
        }
      });
      marker.addTo(trainLayer);
      stationMarkers.set(name, marker);
    } else {
      marker.setStyle({ fillColor: color, radius: g.trains.length > 1 ? 7 : 6 });
      marker.setTooltipContent(groupLabelHtml(g));
      marker.setPopupContent(groupPopupHtml(g));
    }
    marker.__trains = g.trains;
    marker.__worst = worst;
  }
  for (const [name, marker] of stationMarkers) {
    if (!groups.has(name)) {
      trainLayer.removeLayer(marker);
      stationMarkers.delete(name);
    }
  }
  requestAnimationFrame(declutterLabels);
}

// ---------- avtobusi: prava lega iz GPS ----------
// Vlaki v feedu nimajo GPS, avtobusi ga imajo. To sta dve različni stvari na
// isti sliki in ju je treba ločiti tudi na pogled: vlak je krog na postaji,
// avtobus je oblika vozila na izmerjeni legi.

const BUS_INK = "#4db97f";

// Velikost sledi približevanju. Pri pogledu na vso Slovenijo je vozil do sto
// in majhna oblika je edina, ki se ne slepi; ko kdo približa na eno ulico,
// pa je iskal prav to vozilo in mora biti veliko.
function busSize(z) {
  if (z >= 14) return 34;
  if (z >= 12) return 26;
  if (z >= 10) return 20;
  return 15;
}

// Avtobus od zgoraj: zaobljeno telo, svetlejše vetrobransko steklo spredaj in
// zarezi za kolesi. Puščica je bila premalo -- pri približku je bila videti
// kot pika in se od vlaka ni ločila.
function busSvg(size, moving) {
  const o = moving ? 1 : 0.5;
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24">
      <g>
        <rect x="7.5" y="2.5" width="9" height="19" rx="3.2"
              fill="${BUS_INK}" fill-opacity="${o}"
              stroke="#0f1115" stroke-width="1.5"/>
        <path d="M9.2 5.6 Q12 4.4 14.8 5.6 L14.8 7.4 Q12 6.6 9.2 7.4 Z"
              fill="#0f1115" fill-opacity="0.65"/>
        <rect x="6.4" y="6.6" width="1.6" height="3.2" rx="0.7" fill="#0f1115" fill-opacity="0.75"/>
        <rect x="16" y="6.6" width="1.6" height="3.2" rx="0.7" fill="#0f1115" fill-opacity="0.75"/>
        <rect x="6.4" y="15" width="1.6" height="3.2" rx="0.7" fill="#0f1115" fill-opacity="0.75"/>
        <rect x="16" y="15" width="1.6" height="3.2" rx="0.7" fill="#0f1115" fill-opacity="0.75"/>
      </g>
    </svg>`;
}

function busIcon(v, z) {
  const size = busSize(z);
  const angle = v.bearing == null ? 0 : v.bearing;
  const moving = (v.speed_kmh || 0) >= 3;
  return L.divIcon({
    className: "bus-marker",
    html: `<div style="transform:rotate(${angle}deg);width:${size}px;height:${size}px">`
      + busSvg(size, moving) + "</div>",
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

function busTooltipHtml(v) {
  return `<div class="train-label-line">`
    + `<span class="train-label-code" style="color:${BUS_INK}">${escapeHtml(v.train_no)}</span>`
    + `<span class="train-label-more">${escapeHtml(v.headsign || "")}</span></div>`
    + `<div class="train-label-more">`
    + `${v.speed_kmh != null ? (v.speed_kmh >= 3 ? `${v.speed_kmh} km/h` : "stoji") : "brez hitrosti"}`
    + ` · lega stara ${v.age_s} s</div>`;
}

const busMarkers = new Map();       // trip_id -> L.Marker

function renderBuses(list) {
  const z = map.getZoom();
  const seen = new Set();
  for (const v of list) {
    const key = v.trip_id || `${v.train_no}:${v.lat},${v.lon}`;
    seen.add(key);
    let m = busMarkers.get(key);
    if (!m) {
      m = L.marker([v.lat, v.lon], { icon: busIcon(v, z), keyboard: false });
      m.on("click", () => openTrainWindow(
        m.__v.train_no, m.__v.trip_id, m.__v.service_date, "avtobus"));
      m.bindTooltip(busTooltipHtml(v), {
        className: "sztrack-tooltip", direction: "top", offset: [0, -10],
      });
      m.addTo(busLayer);
      busMarkers.set(key, m);
    } else {
      m.setLatLng([v.lat, v.lon]);
      m.setIcon(busIcon(v, z));
      m.setTooltipContent(busTooltipHtml(v));
    }
    m.__v = v;
  }
  for (const [key, m] of busMarkers) {
    if (!seen.has(key)) {
      busLayer.removeLayer(m);
      busMarkers.delete(key);
    }
  }
}

// Ob spremembi priblizka je treba ikone prerisati -- velikost je odvisna od
// zooma, Leaflet pa ikon sam ne skalira.
let zoomTimer = null;
map.on("zoomend", () => {
  clearTimeout(zoomTimer);
  zoomTimer = setTimeout(() => renderBuses(liveBuses), 60);
});

// ---------- razvrščanje oznak ----------

const labelNoteEl = document.getElementById("label-note");

function declutterLabels() {
  // Leaflet ne izogiba trkom med trajnimi oznakami: riše jih po vrsti
  // dodajanja, zato se v gostih vozliščih prekrivajo. Požrešno pravilo --
  // večja zamuda ima prednost, prekrite skrijemo in povemo, koliko jih je.
  const entries = [];
  for (const marker of stationMarkers.values()) {
    const tooltip = marker.getTooltip();
    const el = tooltip && tooltip.getElement();
    if (!el) continue;
    el.style.display = "";
    entries.push({ el, worst: marker.__worst ?? -Infinity });
  }
  entries.sort((a, b) => b.worst - a.worst);

  const kept = [];
  let hidden = 0;
  const PAD = 2;
  for (const e of entries) {
    const r = e.el.getBoundingClientRect();
    if (!r.width && !r.height) continue;         // še ni izrisano
    const box = { l: r.left - PAD, t: r.top - PAD, r: r.right + PAD, b: r.bottom + PAD };
    const clash = kept.some((k) => !(box.r < k.l || box.l > k.r || box.b < k.t || box.t > k.b));
    if (clash) {
      e.el.style.display = "none";
      hidden += 1;
    } else {
      kept.push(box);
    }
  }
  if (hidden > 0) {
    labelNoteEl.textContent = `${hidden} ${hidden === 1 ? "oznaka skrita" : "oznak skritih"}`
      + " zaradi prekrivanja — približaj ali klikni marker";
    labelNoteEl.hidden = false;
  } else {
    labelNoteEl.hidden = true;
  }
}

map.on("zoomend moveend", () => requestAnimationFrame(declutterLabels));

document.addEventListener("click", (ev) => {
  const btn = ev.target.closest(".popup-train");
  if (!btn) return;
  map.closePopup();
  openTrainWindow(btn.dataset.train, btn.dataset.trip, btn.dataset.date);
});

// ---------- plasti ----------
// Zemljevid je edini pogled, ki ga omrežji delita, zato mora biti mogoče
// vsako odložiti -- doslej se je dalo skriti samo avtobuse. Izbira se
// zapomni: kdor gleda vlake, jih gleda tudi jutri.

const LAYERS = [
  { id: "lay-train", key: "train", layer: () => trainLayer, def: true },
  { id: "lay-bus", key: "bus", layer: () => busLayer, def: true },
  { id: "lay-net", key: "net", layer: () => netLayer, def: true },
  { id: "lay-stations", key: "stations", layer: () => stationLayer, def: true },
  { id: "lay-labels", key: "labels", layer: () => labelLayer, def: false },
  { id: "lay-base", key: "base", layer: () => baseLayer, def: true },
];

function layerPref(key, def) {
  try {
    const v = localStorage.getItem(`sztrack:map-${key}`);
    return v === null ? def : v === "1";
  } catch (err) {
    return def;
  }
}

function setLayer(spec, on) {
  const layer = spec.layer();
  if (on && !map.hasLayer(layer)) layer.addTo(map);
  if (!on && map.hasLayer(layer)) map.removeLayer(layer);
  const box = document.getElementById(spec.id);
  if (box) box.checked = on;
  try {
    localStorage.setItem(`sztrack:map-${spec.key}`, on ? "1" : "0");
  } catch (err) {
    /* zaseben zavihek ni razlog, da stran ne dela */
  }
}

// Podlaga naj bo tiho: imena ulic so na njej vpecena in pri velikem
// priblizku tekmujejo z vozili, ki so edini razlog za to stran. Zatemnitev
// jih potisne nazaj, geometrija cest pa ostane -- to je edino, kar se brez
// placljive podlage da narediti.
function setQuiet(on) {
  document.body.classList.toggle("map-quiet", on);
  const box = document.getElementById("lay-quiet");
  if (box) box.checked = on;
  try {
    localStorage.setItem("sztrack:map-quiet", on ? "1" : "0");
  } catch (err) {
    /* zaseben zavihek */
  }
}

function initLayers() {
  const quietBox = document.getElementById("lay-quiet");
  setQuiet(layerPref("quiet", true));
  if (quietBox) quietBox.addEventListener("change", () => setQuiet(quietBox.checked));
  for (const spec of LAYERS) {
    const box = document.getElementById(spec.id);
    setLayer(spec, layerPref(spec.key, spec.def));
    if (box) box.addEventListener("change", () => setLayer(spec, box.checked));
  }
}

// ---------- iskanje vozila ----------
// Vprašanje pred zemljevidom ni "kdo danes najbolj zamuja", ampak "kje je moj
// avtobus". Lestvica zamud je odgovarjala na prvo; iskalnik odgovarja na drugo.

const findEl = document.getElementById("find");
const findListEl = document.getElementById("find-list");
let selectedKey = null;

function findMatches(q) {
  const f = fold(q);
  if (!f) return [];
  const out = [];
  for (const v of liveBuses) {
    if (fold(v.train_no).startsWith(f) || fold(v.headsign || "").includes(f)) {
      out.push({ kind: "bus", v });
    }
  }
  for (const t of liveTrains) {
    if (fold(t.train_no).includes(f) || fold(t.headsign || "").includes(f)) {
      out.push({ kind: "train", v: t });
    }
  }
  return out.slice(0, 12);
}

function findRowHtml(m) {
  const v = m.v;
  const delay = m.kind === "bus" ? v.delay_s : bestDelay(v).value;
  const kje = m.kind === "bus"
    ? (v.last_stop ? `pri ${v.last_stop}` : "GPS lega")
    : bestDelay(v).where;
  return `<button type="button" class="find-row" data-key="${escapeHtml(m.key)}">
      <span class="find-kind find-kind-${m.kind}"></span>
      <span class="find-no">${escapeHtml(v.train_no)}</span>
      <span class="find-where">${escapeHtml(kje || "")}</span>
      <span class="find-delay" style="color:${delayColor(delay)}">${delayLabel(delay)}</span>
    </button>`;
}

function renderFind() {
  const q = findEl.value.trim();
  document.getElementById("find-clear").hidden = !q;
  if (!q) {
    findListEl.innerHTML = "";
    return;
  }
  const found = findMatches(q);
  for (const m of found) {
    m.key = m.kind === "bus"
      ? `b:${m.v.trip_id || m.v.train_no}`
      : `t:${m.v.trip_id || m.v.train_no}`;
  }
  findListEl.innerHTML = found.length
    ? found.map(findRowHtml).join("")
    : `<div class="find-empty">Med vozili, ki so zdaj na poti, tega ni.
         Vlaki brez meritve in avtobusi brez GPS na zemljevidu ne obstajajo.</div>`;
  findListEl.__found = found;
}

// Trasa izbrane vožnje po cesti oziroma progi (GTFS `shapes.txt`) in njena
// postajališča. Traso rišemo za VSE prevoznike -- uvoz jo hrani v `shape`,
// 2 897 oblik in 10,3 MB, kar je proti bazi enkraten strošek, ki ne raste.
// Kadar je iz kakršnega koli razloga ni, ostane črta skozi postajališča;
// ta ni pot po cesti in videti mora drugače (črtkano).
async function drawStops(trainNo, tripId) {
  routeLayer.clearLayers();
  let trasa = null;
  if (tripId) {
    try {
      const r = await fetch(`/api/trip/${encodeURIComponent(tripId)}/shape`);
      if (r.ok) trasa = (await r.json()).points;
    } catch (err) {
      /* brez trase narišemo postajališča */
    }
  }
  if (trasa && trasa.length > 1) {
    L.polyline(trasa, { color: "#0f1115", weight: 6, opacity: 0.85 }).addTo(routeLayer);
    L.polyline(trasa, { color: BUS_INK, weight: 3, opacity: 0.95 }).addTo(routeLayer);
  }
  try {
    const q = tripId ? `?trip=${encodeURIComponent(tripId)}` : "";
    const res = await fetch(
      `/api/train/${encodeURIComponent(trainNo)}${q}`).then((r) => r.json());
    const pts = (res.timetable || [])
      .filter((s) => s.lat != null && s.lon != null)
      .map((s) => [s.lat, s.lon]);
    if (!trasa && pts.length > 1) {
      L.polyline(pts, { color: BUS_INK, weight: 2.5, opacity: 0.7, dashArray: "5 5" })
        .addTo(routeLayer);
    }
    for (const p of pts) {
      L.circleMarker(p, {
        radius: 3.2, color: "#0f1115", weight: 1.4,
        fillColor: BUS_INK, fillOpacity: 1, interactive: false,
      }).addTo(routeLayer);
    }
  } catch (err) {
    /* brez postajališč je trasa še vedno uporabna */
  }
}

function focusVehicle(key) {
  selectedKey = key;
  const found = findListEl.__found || [];
  const m = found.find((x) => x.key === key);
  if (!m) return;
  for (const b of findListEl.querySelectorAll(".find-row")) {
    b.classList.toggle("is-on", b.dataset.key === key);
  }
  if (m.kind === "bus") {
    map.setView([m.v.lat, m.v.lon], Math.max(map.getZoom(), 14), { animate: true });
    const mk = busMarkers.get(m.v.trip_id);
    if (mk) mk.openTooltip();
  } else {
    const where = bestDelay(m.v).where;
    const st = m.v.reported_lat != null
      ? { lat: m.v.reported_lat, lon: m.v.reported_lon }
      : stationsByName.get(m.v.last_stop);
    if (st) map.setView([st.lat, st.lon], Math.max(map.getZoom(), 11), { animate: true });
    const mk = stationMarkers.get(where);
    if (mk) mk.openPopup();
  }
  drawStops(m.v.train_no, m.v.trip_id);
  setSheet(false);        // naslednje, kar clovek hoce videti, je zemljevid
}

findEl.addEventListener("input", renderFind);
findListEl.addEventListener("click", (ev) => {
  const b = ev.target.closest(".find-row");
  if (b) focusVehicle(b.dataset.key);
});
document.getElementById("find-clear").addEventListener("click", () => {
  findEl.value = "";
  selectedKey = null;
  routeLayer.clearLayers();
  renderFind();
  findEl.focus();
});

// ---------- glava in poll ----------

const feedDotEl = document.getElementById("feed-dot");

async function pollLive() {
  try {
    liveTrains = await fetch("/api/live?network=zeleznica").then((r) => r.json());
    document.getElementById("n-train").textContent = liveTrains.length;
    renderTrains(liveTrains);
    if (findEl.value.trim()) renderFind();
  } catch (err) {
    console.error("/api/live ni uspel", err);
    refreshFeedDot();
  }
}

async function loadVehicles() {
  try {
    liveBuses = await fetch("/api/vehicles").then((r) => r.json());
    document.getElementById("n-bus").textContent = liveBuses.length;
    renderBuses(liveBuses);
    if (findEl.value.trim()) renderFind();
  } catch (err) {
    console.warn("lege vozil ni bilo mogoče naložiti", err);
  }
}

function tickClock() {
  document.getElementById("clock").textContent = new Intl.DateTimeFormat("sl-SI", {
    timeZone: "Europe/Ljubljana", hour: "2-digit", minute: "2-digit",
    second: "2-digit", hour12: false,
  }).format(new Date());
}

tickClock();
setInterval(tickClock, 1000);
refreshFeedDot();
setInterval(refreshFeedDot, 30000);

// Spodnja plosca na telefonu. Zaprta se odpre na dotik gumba; iskanje jo
// odpre samo (kdor tipka, jo rabi odprto), izbira vozila pa jo zapre, ker je
// naslednje, kar clovek hoce videti, zemljevid.
const sheetBtn = document.getElementById("sheet-toggle");
function setSheet(on) {
  document.body.classList.toggle("sheet-open", on);
  if (sheetBtn) sheetBtn.setAttribute("aria-expanded", String(on));
  if (on) setTimeout(() => findEl.focus(), 180);
}
if (sheetBtn) {
  sheetBtn.addEventListener("click", () =>
    setSheet(!document.body.classList.contains("sheet-open")));
}

initLayers();
loadStatic().then(() => {
  pollLive();
  setInterval(pollLive, POLL_MS);
  // Lega avtobusov ima svoj ritem: feed jo osvežuje na ~30 s, zamude pa se
  // spreminjajo redkeje.
  loadVehicles();
  setInterval(loadVehicles, 20000);
});
