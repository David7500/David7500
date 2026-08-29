"use strict";

// Ziva nadzorna slika mreze. Skupne funkcije so v common.js.
// Feed na strezniku osvezuje collector.py na config.POLL_SECONDS (privzeto 30 s) --
// ta vrednost ni izpostavljena prek API-ja, zato je tu locena kopija privzetka.
const POLL_MS = 30000;

function openTrainWindow(trainNo, tripId, serviceDate) {
  // Posamezen vlak dobi svoje okno -- tam je poleg te voznje se zgodovina.
  //
  // `trip` in `date` gresta zraven, kadar ju poznamo: stevilka linije pri
  // avtobusu ni enolicna, devet vlakov pa ima sezonske razlicice. Brez njiju
  // bi se okno odprlo na glavni razlicici, ne na tisti, ki si jo kliknil.
  const q = new URLSearchParams();
  if (serviceDate) q.set("date", serviceDate);
  if (tripId) q.set("trip", tripId);
  window.open(
    `/app/train/${encodeURIComponent(trainNo)}${q.toString() ? `?${q}` : ""}`,
    `sztrack-${trainNo}`,
  );
}

// ---------- zemljevid ----------

const map = L.map("map").setView([46.05, 14.95], 8);

// Ostajamo pri OpenStreetMap. CARTO dark_all od nekod zahteva kljuc in
// ploscice pride s cez pol zaslona napisom "API KEY REQUIRED"; pri zunanjem
// viru je to vedno mogoce, zato raje nic novega.
//
// Podlago potemnimo v CSS (glej .leaflet-tile v dashboard.css). To ni samo
// okras: na svetli podlagi oranzen vlak tekmuje z zeleno pokrajino in rdecimi
// cestami, se pravi z barvami, ki ne pomenijo nicesar. Podlaga naj bo brez
// barve, barvo nosijo podatki.
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 18,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);

// Brez addTo(map) tukaj -- doda se sele po progah/postajah, da so vlaki narisani zgoraj.
const trainLayer = L.layerGroup();
// Avtobusi so svoja plast: imajo PRAVO lego iz GPS, ne zadnje postaje z
// meritvijo. Ceste, po katerih vozijo, so ze na podlagi, zato pika ni v praznem.
const busLayer = L.layerGroup();
const stationMarkers = new Map(); // ime postaje -> L.CircleMarker

let stationsByName = new Map(); // ime postaje -> {stop_id, lat, lon}

async function loadStatic() {
  try {
    // Samo zelezniske postaje: ko so v bazi tudi avtobusi, bi jih LPP dodal
    // tisoc in mreza prog bi izginila pod postajalisci.
    const stations = await fetch("/api/stations?network=zeleznica").then((r) => r.json());
    stationsByName = new Map(stations.map((s) => [s.name, s]));

    const stationLayer = L.layerGroup();
    const latlngs = [];
    for (const s of stations) {
      L.circleMarker([s.lat, s.lon], {
        radius: 2, color: "#78818f", fillColor: "#78818f", fillOpacity: 1,
        weight: 0, interactive: false,
      }).addTo(stationLayer);
      latlngs.push([s.lat, s.lon]);
    }
    stationLayer.addTo(map);
    if (latlngs.length) map.fitBounds(latlngs, { padding: [24, 24] });
  } catch (err) {
    console.error("postaj ni bilo mogoče naložiti", err);
  }

  try {
    const geojson = await fetch("/api/network.geojson").then((r) => r.json());
    // L.geoJSON sam pretvori [lon, lat] iz GeoJSON-a v Leafletov [lat, lon].
    L.geoJSON(geojson, {
      // Proga mora biti svetlejsa od podlage, ne temnejsa: podlaga je zdaj
      // temna in #2a2f38 se je v njej izgubila. Nevtralna siva, ker odtenek
      // v tem prikazu ne pomeni nicesar -- pomen nosijo vlaki na njej.
      style: { color: "#5b6472", weight: 1.4, opacity: 0.85 },
      interactive: false,
    }).addTo(map);
  } catch (err) {
    console.error("mreže ni bilo mogoče naložiti", err);
  }

  trainLayer.addTo(map);
}

// ---------- vlaki na zemljevidu ----------

function worstDelay(trains) {
  // null (brez meritve) se ne sme obnasati kot 0 -- zato -Infinity kot izhodisce.
  return trains.reduce((acc, t) => {
    const v = bestDelay(t).value;
    return v != null && v > acc ? v : acc;
  }, -Infinity);
}


// Kraj in zamuda morata biti iz istega vira. Prevoznikovo porocilo pozna
// prometno mesto in je obicajno svezje; nasa `run` pozna samo voznoredne
// postanke. Kadar imamo oboje, vzamemo prevoznikovo -- a nikoli pol enega
// in pol drugega, sicer pise "Dobova" ob zamudi, izmerjeni v Sevnici.
function bestDelay(t) {
  if (t.reported_lat != null) {
    return {
      value: t.reported_delay_s,
      where: t.reported_at_station,
      ageS: t.reported_age_s,
      fromOperator: true,
    };
  }
  return { value: t.delay_s, where: t.last_stop, ageS: t.age_s, fromOperator: false };
}

function groupByStation(trains) {
  // Vec vlakov stoji na isti postaji -- en marker na postajo, sicer se markerji
  // in njihove oznake v vozliscih (Ljubljana, Zidani Most) prekrivajo.
  const groups = new Map();
  for (const t of trains) {
    // Prevoznikovo prometno mesto je tocnejse od nase zadnje prevozene
    // postaje: zamuda se meri tudi tam, kjer vlak ne ustavlja, in prav to
    // mesto feed imenuje. Uporabimo ga, kadar ga poznamo kot postajo.
    const useReported = t.reported_lat != null;
    const where = useReported ? t.reported_at_station : t.last_stop;
    const station = useReported
      ? { lat: t.reported_lat, lon: t.reported_lon }
      : stationsByName.get(t.last_stop);
    if (!station) {
      console.warn(`postaja "${where}" (vlak ${t.train_no}) ni najdena v /api/stations`);
      continue;
    }
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
  // Barva na markerju sama ne sme nositi pomena -- vedno zraven pise tudi minuta.
  return `<span class="train-label-code">${escapeHtml(t.train_no)}</span>` +
    modeBadgeHtml(t.mode) +
    `<span class="train-label-delay" style="color:${delayColor(bestDelay(t).value)}">${delayLabel(bestDelay(t).value)}</span>`;
}

function groupLabelHtml(g) {
  const shown = g.trains.slice(0, 3).map((t) => `<div class="train-label-line">${trainLineHtml(t)}</div>`);
  if (g.trains.length > 3) {
    shown.push(`<div class="train-label-more">…in še ${g.trains.length - 3}</div>`);
  }
  return shown.join("");
}

function groupPopupHtml(g) {
  const rows = g.trains.map((t) => `
    <button class="popup-train" data-train="${escapeHtml(t.train_no)}" data-trip="${escapeHtml(t.trip_id || "")}"
            data-date="${escapeHtml(t.service_date || "")}">
      <span class="popup-train-code">${escapeHtml(t.train_no)}</span>${modeBadgeHtml(t.mode)}
      <span class="popup-train-headsign">${escapeHtml(t.headsign || "")}</span>
      <span class="popup-train-delay" style="color:${delayColor(bestDelay(t).value)}">${delayLabel(bestDelay(t).value)}</span>
    </button>
  `).join("");
  const measured = g.trains.map((t) => t.measured_at).filter(Boolean).sort().pop();
  return `
    <div class="popup-station">${escapeHtml(g.name)}</div>
    <div class="popup-note">zadnja postaja z meritvijo — ${g.trains.length === 1 ? "1 vlak" : `${g.trains.length} vlakov`}</div>
    <div class="popup-list">${rows}</div>
    <div class="popup-note">${measured ? `nazadnje izmerjeno ob ${hhmm(measured)} · ` : ""}klikni vlak za svoje okno</div>
  `;
}

function renderTrains(trains) {
  // Vlaki NIMAJO GPS pozicij -- marker je vedno tocno na zadnji znani postaji,
  // nikoli interpoliran vzdolz proge.
  const groups = groupByStation(trains);

  for (const [name, g] of groups) {
    const worst = worstDelay(g.trains);
    const color = delayColor(worst === -Infinity ? null : worst);
    const latlng = [g.station.lat, g.station.lon];

    let marker = stationMarkers.get(name);
    if (!marker) {
      marker = L.circleMarker(latlng, {
        radius: g.trains.length > 1 ? 7 : 6, weight: 1.5,
        color: "#0f1115", fillColor: color, fillOpacity: 1,
      });
      // interactive: true doda oznaki razred leaflet-interactive in jo registrira
      // kot cilj markerja -- brez tega klik na oznako ne sprozi nicesar.
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

// ---------- razvrscanje oznak ----------

const labelNoteEl = document.getElementById("label-note");

function declutterLabels() {
  // Leaflet ne izogiba trkom med trajnimi oznakami. Rise jih po vrsti dodajanja,
  // zato se v gostih vozliscih prekrivajo. Pozresno pravilo: vecja zamuda ima
  // prednost, prekrite oznake skrijemo in uporabniku povemo, koliko jih je --
  // podatek ostane dosegljiv s klikom na marker ali z blizjim pogledom.
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
    if (!r.width && !r.height) continue; // se ni izrisano
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
    labelNoteEl.textContent = `${hidden} ${hidden === 1 ? "oznaka skrita" : "oznak skritih"} zaradi prekrivanja — približaj ali klikni marker`;
    labelNoteEl.hidden = false;
  } else {
    labelNoteEl.hidden = true;
  }
}

map.on("zoomend moveend", () => requestAnimationFrame(declutterLabels));

// Klik na vlak v popupu odpre njegovo okno.
document.addEventListener("click", (ev) => {
  const btn = ev.target.closest(".popup-train");
  if (!btn) return;
  map.closePopup();
  openTrainWindow(btn.dataset.train, btn.dataset.trip, btn.dataset.date);
});

// ---------- stranski seznam ----------

const delayListEl = document.getElementById("delay-list");

function renderSidebar(trains) {
  if (!trains.length) {
    delayListEl.innerHTML = '<div class="empty-state">trenutno ni vlakov na progi</div>';
    return;
  }
  // Lestvica mora biti urejena po isti vrednosti, kot jo pokaze -- /api/live
  // razvrsca po nasi zamudi, tu pa lahko prevlada prevoznikova.
  const top = [...trains]
    .sort((a, b) => (bestDelay(b).value ?? -1) - (bestDelay(a).value ?? -1))
    .slice(0, 15);
  delayListEl.innerHTML = top.map((t) => {
    const d = bestDelay(t);
    const color = delayColor(d.value);
    const stale = d.ageS != null && d.ageS > 1200;
    return `
      <div class="delay-row" data-train="${escapeHtml(t.train_no)}" data-trip="${escapeHtml(t.trip_id || "")}"
            data-date="${escapeHtml(t.service_date || "")}">
        <span class="delay-dot" style="background:${color}"></span>
        <div class="delay-info">
          <div class="delay-train">${escapeHtml(t.train_no)}</div>
          <div class="delay-stop">${escapeHtml(d.where)}${stale
            ? ` · <span class="stale-note">star ${Math.round(d.ageS / 60)} min</span>` : ""}</div>
        </div>
        <div class="delay-value" style="color:${color}">${delayLabel(d.value)}</div>
      </div>
    `;
  }).join("");
}

delayListEl.addEventListener("click", (ev) => {
  const row = ev.target.closest(".delay-row");
  if (!row) return;
  openTrainWindow(row.dataset.train, row.dataset.trip, row.dataset.date);
});

// ---------- avtobusi: prava lega iz GPS ----------
// Vlaki v feedu nimajo GPS, avtobusi ga imajo. Zato sta to dve razlicni
// stvari na isti sliki in ju je treba lociti tudi na pogled: vlak je krog
// na postaji, avtobus je pušcica v smeri vožnje.

const BUS_INK = "#4db97f";

function busMarker(v) {
  const angle = v.bearing == null ? 0 : v.bearing;
  const moving = (v.speed_kmh || 0) >= 3;
  const icon = L.divIcon({
    className: "bus-marker",
    html: `<svg width="18" height="18" viewBox="0 0 24 24"
                style="transform:rotate(${angle}deg)">
        <path d="M12 3 L18 20 L12 16 L6 20 Z"
              fill="${BUS_INK}" fill-opacity="${moving ? 1 : 0.45}"
              stroke="#0f1115" stroke-width="1.4" stroke-linejoin="round"/>
      </svg>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
  const m = L.marker([v.lat, v.lon], { icon, keyboard: false });
  // Puscica je bila doslej samo oznaka. Klik naj odpre voznjo, kot pri vlaku;
  // `trip_id` je nujen, ker stevilka linije ni stevilka voznje.
  m.on("click", () => openTrainWindow(v.train_no, v.trip_id, v.service_date));
  m.bindTooltip(
    `<div class="train-label-line">` +
      `<span class="train-label-code" style="color:${BUS_INK}">${escapeHtml(v.train_no)}</span>` +
      `<span class="train-label-more">${escapeHtml(v.headsign || "")}</span></div>` +
      `<div class="train-label-more">${v.speed_kmh != null ? `${v.speed_kmh} km/h` : "brez hitrosti"}` +
      ` · lega stara ${v.age_s} s</div>`,
    { className: "sztrack-tooltip", direction: "top", offset: [0, -8] },
  );
  return m;
}

// Zemljevid je edini pogled, ki ga vlaki in avtobusi delita, zato mora biti
// mogoce enega odloziti. Izbira se zapomni -- kdor gleda vlake, jih gleda
// tudi jutri.
let busVisible = true;
try {
  busVisible = localStorage.getItem("sztrack:map-bus") !== "0";
} catch (err) {
  /* zaseben zavihek */
}

function setBusVisible(on) {
  busVisible = on;
  if (on) {
    if (!map.hasLayer(busLayer)) busLayer.addTo(map);
  } else if (map.hasLayer(busLayer)) {
    map.removeLayer(busLayer);
  }
  const btn = document.getElementById("bus-toggle");
  if (btn) btn.setAttribute("aria-pressed", String(on));
  try {
    localStorage.setItem("sztrack:map-bus", on ? "1" : "0");
  } catch (err) {
    /* zaseben zavihek */
  }
}

async function loadVehicles() {
  try {
    const list = await fetch("/api/vehicles").then((r) => r.json());
    busLayer.clearLayers();
    for (const v of list) busLayer.addLayer(busMarker(v));
    if (list.length && busVisible && !map.hasLayer(busLayer)) busLayer.addTo(map);
    const leg = document.getElementById("legend-bus");
    if (leg) leg.hidden = !list.length;
    const btn = document.getElementById("bus-toggle");
    if (btn) {
      btn.hidden = !list.length;
      btn.textContent = `${list.length} avtobusov`;
    }
  } catch (err) {
    console.warn("lege vozil ni bilo mogoce nalozit", err);
  }
}

// ---------- glava: stevec vlakov, ura, indikator svezine ----------

const feedDotEl = document.getElementById("feed-dot");
const trainCountEl = document.getElementById("train-count-n");

async function pollLive() {
  try {
    const trains = await // Zemljevid rise zelezniska mreza in postaje; avtobusi nimajo ne enega
    // ne drugega, zato bi njihovi markerji viseli v praznem. Steti jih v
    // glavo, risati pa ne, bi bilo se slabse.
    fetch("/api/live?network=zeleznica").then((r) => r.json());
    trainCountEl.textContent = trains.length;
    renderSidebar(trains);
    renderTrains(trains);
  } catch (err) {
    console.error("/api/live ni uspel", err);
    refreshFeedDot();
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
setInterval(refreshFeedDot, 30000);

loadStatic().then(() => {
  pollLive();
  setInterval(pollLive, POLL_MS);
  // Lega avtobusov ima svoj ritem: feed jo osvezuje na ~30 s, zamude pa se
  // spreminjajo redkeje. Ce avtobusov v bazi ni, seznam je prazen in plast
  // ostane skrita.
  const toggle = document.getElementById("bus-toggle");
  if (toggle) toggle.addEventListener("click", () => setBusVisible(!busVisible));
  setBusVisible(busVisible);
  loadVehicles();
  setInterval(loadVehicles, 20000);
});
