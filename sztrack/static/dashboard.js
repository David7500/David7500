"use strict";

// Ziva nadzorna slika mreze. Skupne funkcije so v common.js.
// Feed na strezniku osvezuje collector.py na config.POLL_SECONDS (privzeto 30 s) --
// ta vrednost ni izpostavljena prek API-ja, zato je tu locena kopija privzetka.
const POLL_MS = 30000;

function openTrainWindow(trainNo) {
  // Posamezen vlak dobi svoje okno -- tam je poleg te voznje se zgodovina.
  window.open(`/app/train/${encodeURIComponent(trainNo)}`, `sztrack-${trainNo}`);
}

// ---------- zemljevid ----------

const map = L.map("map").setView([46.05, 14.95], 8);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 18,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);

// Brez addTo(map) tukaj -- doda se sele po progah/postajah, da so vlaki narisani zgoraj.
const trainLayer = L.layerGroup();
const stationMarkers = new Map(); // ime postaje -> L.CircleMarker

let stationsByName = new Map(); // ime postaje -> {stop_id, lat, lon}

async function loadStatic() {
  try {
    const stations = await fetch("/api/stations").then((r) => r.json());
    stationsByName = new Map(stations.map((s) => [s.name, s]));

    const stationLayer = L.layerGroup();
    const latlngs = [];
    for (const s of stations) {
      L.circleMarker([s.lat, s.lon], {
        radius: 2, color: "#3d434f", fillColor: "#3d434f", fillOpacity: 1,
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
      style: { color: "#2a2f38", weight: 1.5 },
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
  return trains.reduce((acc, t) => (t.delay_s != null && t.delay_s > acc ? t.delay_s : acc), -Infinity);
}

function groupByStation(trains) {
  // Vec vlakov stoji na isti postaji -- en marker na postajo, sicer se markerji
  // in njihove oznake v vozliscih (Ljubljana, Zidani Most) prekrivajo.
  const groups = new Map();
  for (const t of trains) {
    const station = stationsByName.get(t.last_stop);
    if (!station) {
      console.warn(`postaja "${t.last_stop}" (vlak ${t.train_no}) ni najdena v /api/stations`);
      continue;
    }
    let g = groups.get(t.last_stop);
    if (!g) {
      g = { name: t.last_stop, station, trains: [] };
      groups.set(t.last_stop, g);
    }
    g.trains.push(t);
  }
  for (const g of groups.values()) {
    g.trains.sort((a, b) => (b.delay_s ?? -1) - (a.delay_s ?? -1));
  }
  return groups;
}

function trainLineHtml(t) {
  // Barva na markerju sama ne sme nositi pomena -- vedno zraven pise tudi minuta.
  return `<span class="train-label-code">${escapeHtml(t.train_no)}</span>` +
    `<span class="train-label-delay" style="color:${delayColor(t.delay_s)}">${delayLabel(t.delay_s)}</span>`;
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
    <button class="popup-train" data-train="${escapeHtml(t.train_no)}">
      <span class="popup-train-code">${escapeHtml(t.train_no)}</span>
      <span class="popup-train-headsign">${escapeHtml(t.headsign || "")}</span>
      <span class="popup-train-delay" style="color:${delayColor(t.delay_s)}">${delayLabel(t.delay_s)}</span>
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
          openTrainWindow(marker.__trains[0].train_no);
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
  openTrainWindow(btn.dataset.train);
});

// ---------- stranski seznam ----------

const delayListEl = document.getElementById("delay-list");

function renderSidebar(trains) {
  if (!trains.length) {
    delayListEl.innerHTML = '<div class="empty-state">trenutno ni vlakov na progi</div>';
    return;
  }
  const top = trains.slice(0, 15); // /api/live je ze razvrscen padajoce po delay_s
  delayListEl.innerHTML = top.map((t) => {
    const color = delayColor(t.delay_s);
    return `
      <div class="delay-row" data-train="${escapeHtml(t.train_no)}">
        <span class="delay-dot" style="background:${color}"></span>
        <div class="delay-info">
          <div class="delay-train">${escapeHtml(t.train_no)}</div>
          <div class="delay-stop">${escapeHtml(t.last_stop)}</div>
        </div>
        <div class="delay-value" style="color:${color}">${delayLabel(t.delay_s)}</div>
      </div>
    `;
  }).join("");
}

delayListEl.addEventListener("click", (ev) => {
  const row = ev.target.closest(".delay-row");
  if (!row) return;
  openTrainWindow(row.dataset.train);
});

// ---------- glava: stevec vlakov, ura, indikator svezine ----------

const feedDotEl = document.getElementById("feed-dot");
const trainCountEl = document.getElementById("train-count-n");

async function pollLive() {
  try {
    const trains = await fetch("/api/live").then((r) => r.json());
    trainCountEl.textContent = trains.length;
    renderSidebar(trains);
    renderTrains(trains);
    feedDotEl.classList.remove("stale");
  } catch (err) {
    console.error("/api/live ni uspel", err);
    feedDotEl.classList.add("stale");
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

loadStatic().then(() => {
  pollLive();
  setInterval(pollLive, POLL_MS);
});
