"use strict";

// Feed na strezniku osvezuje collector.py na config.POLL_SECONDS (privzeto 30 s) --
// ta vrednost ni izpostavljena prek API-ja, zato je tu locena kopija privzetka.
const POLL_MS = 30000;

const DELAY_RAMP = [
  { max: 60, color: "#7c8698" },
  { max: 300, color: "#f2a87e" },
  { max: 900, color: "#e07b45" },
  { max: Infinity, color: "#b85417" },
];

function delayColor(s) {
  if (s == null) return "#6b7480";
  return (DELAY_RAMP.find((step) => s <= step.max) || DELAY_RAMP[DELAY_RAMP.length - 1]).color;
}

function delayLabel(s) {
  // Zamuda je edino, kar feed nosi -- prikazana vedno kot besedilo, ne samo barva.
  if (s == null) return "?";
  const m = Math.round(s / 60);
  return (m > 0 ? "+" : "") + m;
}

function agoLabel(feedTs) {
  if (!feedTs) return "";
  const diffMin = Math.round(Date.now() / 1000 / 60 - feedTs / 60);
  if (diffMin <= 0) return "pred manj kot minuto";
  if (diffMin === 1) return "pred 1 min";
  return `pred ${diffMin} min`;
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

// ---------- zemljevid ----------

const map = L.map("map").setView([46.05, 14.95], 8);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 18,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);

// Brez addTo(map) tukaj -- doda se sele po progah/postajah, da so vlaki narisani zgoraj.
const trainLayer = L.layerGroup();
const trainMarkers = new Map(); // train_no -> L.CircleMarker

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

function trainLabelHtml(t) {
  // Barva na markerju sama ne sme nositi pomena -- vedno zraven pise tudi minuta.
  const color = delayColor(t.delay_s);
  return `<span class="train-label-code">${escapeHtml(t.train_no)}</span>` +
    `<span class="train-label-delay" style="color:${color}">${delayLabel(t.delay_s)}</span>`;
}

function trainPopupHtml(t) {
  const color = delayColor(t.delay_s);
  return `
    <div class="train-popup-head">
      <span class="train-popup-code">${escapeHtml(t.train_no)}</span>
      <span class="train-popup-headsign">${escapeHtml(t.headsign || "")}</span>
    </div>
    <div class="train-popup-delay" style="color:${color}">${delayLabel(t.delay_s)} min</div>
    <div class="train-popup-row">zadnja znana postaja: ${escapeHtml(t.last_stop)}</div>
    <div class="train-popup-note">${agoLabel(t.feed_ts)}</div>
  `;
}

function renderTrains(trains) {
  // Vlaki NIMAJO GPS pozicij -- marker je vedno tocno na zadnji znani postaji,
  // nikoli interpoliran vzdolz proge.
  const seen = new Set();

  for (const t of trains) {
    const station = stationsByName.get(t.last_stop);
    if (!station) {
      console.warn(`postaja "${t.last_stop}" (vlak ${t.train_no}) ni najdena v /api/stations`);
      continue;
    }
    seen.add(t.train_no);
    const color = delayColor(t.delay_s);
    const latlng = [station.lat, station.lon];

    let marker = trainMarkers.get(t.train_no);
    if (!marker) {
      marker = L.circleMarker(latlng, {
        radius: 6, weight: 1.5, color: "#0f1115", fillColor: color, fillOpacity: 1,
      });
      marker.bindTooltip(trainLabelHtml(t), {
        className: "sztrack-tooltip sztrack-label", permanent: true,
        direction: "right", offset: [8, 0],
      });
      marker.bindPopup(trainPopupHtml(t));
      marker.addTo(trainLayer);
      trainMarkers.set(t.train_no, marker);
    } else {
      marker.setLatLng(latlng);
      marker.setStyle({ fillColor: color });
      marker.setTooltipContent(trainLabelHtml(t));
      marker.setPopupContent(trainPopupHtml(t));
    }
  }

  for (const [trainNo, marker] of trainMarkers) {
    if (!seen.has(trainNo)) {
      trainLayer.removeLayer(marker);
      trainMarkers.delete(trainNo);
    }
  }
}

// ---------- stranski seznam ----------

const delayListEl = document.getElementById("delay-list");

function renderSidebar(trains) {
  if (!trains.length) {
    delayListEl.innerHTML = '<div class="empty-state">trenutno ni vlakov v prometu</div>';
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
  const marker = trainMarkers.get(row.dataset.train);
  if (!marker) return;
  map.setView(marker.getLatLng(), Math.max(map.getZoom(), 11));
  marker.openPopup();
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
