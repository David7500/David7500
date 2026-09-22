// Živi zemljevid -- edini pogled, ki ga vlaki in avtobusi delita. Skupne
// funkcije so v common.js. Feed na strežniku osvežuje collector.py na
// config.POLL_SECONDS (privzeto 30 s); ta vrednost ni izpostavljena prek
// API-ja, zato je tu ločena kopija privzetka.
const POLL_MS = 30000;

// ---------- zemljevid ----------
//
// Ta zemljevid je MapLibre sam, brez Leafleta (22. 9. 2026). Leaflet nagiba
// ne pozna: ovoj `leaflet-maplibre-gl`, ki ga imajo ostali trije zemljevidi,
// drzi MapLibrovo kamero v Leafletovi ravnini. Nagib od blizu in stavbe v 3D
// sta mogoca samo, ce kamera pripada MapLibru.
//
// MapLibre 6 zna samo WebGL2 in brez njega ta stran zemljevida nima. Esrijeva
// podlaga je rezerva za primer, ko OpenFreeMap ni dosegljiv, ne za brskalnik
// brez WebGL2 -- tudi njo bi risal MapLibre.

const SLOG = document.querySelector('meta[name="kajros-podlaga"]')?.content
  || "/static/podlaga.json";

// MapLibrov zoom je za ena manjsi od Leafletovega (512- proti 256-pikselnim
// ploscicam). Vse meje na tej strani so ostale v Leafletovih enotah, ker so
// tako izmerjene in zapisane, `z` v naslovu pa ker ga delijo tudi drugi
// (`train.js` pelje na `&z=15`). Pretvorba je samo tu.
const LZ = 1;

// Ura in pika svezine v glavi veljata tudi, kadar zemljevida ni.
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

let maplibregl = null;
try {
  if (!imaWebGL2()) throw new Error("brez WebGL2");
  maplibregl = await import(`${MAPLIBRE_POT}/maplibre-gl.mjs`);
} catch (err) {
  brezZemljevida(err);
}

// Stran brez zemljevida pove, kje je odgovor, namesto da ostane prazna.
// Iskalnik in plasti gredo z njim, ker brez zemljevida ne naredijo nicesar.
function brezZemljevida(err) {
  console.warn("zemljevida ni mogoce narisati:", err && err.message);
  document.body.classList.add("brez-zemljevida");
  document.getElementById("map").innerHTML = `<div class="ni-zemljevida">
      <p>Ta brskalnik zemljevida ne zna narisati.</p>
      <p>Odhode in zamude najdeš pri <a href="/app/train">vlakih</a> in
         <a href="/app/bus">avtobusih</a>.</p>
    </div>`;
}

// Nagib sledi priblizku, kot pri Slometu: od dalec je zemljevid raven, od
// Leafletovega z15 se zacne nagibati in pri z17,5 doseze 60°. Stavbe se
// dvignejo hkrati z njim, zato prehod ni skok, ampak prelivanje. Kamero
// nagne `transformCameraUpdate` pri vsaki spremembi, zato ga rocna gesta ne
// premakne -- nagib je lastnost priblizka, ne se ena nastavitev.
const NAGIB_OD = 14;           // MapLibrov zoom
const NAGIB_CEZ = 2.5;
const NAGIB_NAJVEC = 60;

const vklop = {};              // kljuc plasti iz LAYERS -> prizgana

function nagib(z) {
  if (!vklop["3d"]) return 0;
  return NAGIB_NAJVEC * Math.max(0, Math.min(1, (z - NAGIB_OD) / NAGIB_CEZ));
}

// Lego zemljevida hranimo v naslovu: brez tega je "poglej, kje stoji" nemogoce
// deliti, osvezitev strani pa vrne cez vso Slovenijo. Naslov se popravlja
// tiho (`replaceState`), da gumb nazaj ostane gumb nazaj.
const URLQ = new URLSearchParams(location.search);
const startLat = parseFloat(URLQ.get("lat"));
const startLon = parseFloat(URLQ.get("lon"));
const startZ = parseFloat(URLQ.get("z"));
const HAS_START = Number.isFinite(startLat) && Number.isFinite(startLon)
  && Number.isFinite(startZ);

// Brez WebGL2 se modul tu ustavi: vse spodaj je zemljevid. Obljuba, ki se ne
// izpolni nikoli, je edini nacin, da ES modul neha brez napake v konzoli.
if (!maplibregl) await new Promise(() => {});
vklop["3d"] = layerPref("3d", true);

const zacetniZoom = (HAS_START ? startZ : 8) - LZ;
let map;
try {
  map = new maplibregl.Map({
    container: "map",
    style: SLOG,
    center: HAS_START ? [startLon, startLat] : [14.95, 46.05],
    zoom: zacetniZoom,
    pitch: nagib(zacetniZoom),
    maxZoom: 19 - LZ,
    // Robovi stavb v nagibu so brez glajenja nazobcani.
    canvasContextAttributes: { antialias: true },
    transformCameraUpdate: (t) => ({ pitch: nagib(t.zoom) }),
    // Nagib doloca priblizek; gesti, ki bi ga premikali, bi se z njim
    // prepirali. Vrtenje ostane.
    pitchWithRotate: false,
    touchPitch: false,
  });
} catch (err) {
  // `new Map` vrze, kadar WebGL2 obstaja, a ga ni mogoce odpreti.
  brezZemljevida(err);
  await new Promise(() => {});
}

const lz = () => map.getZoom() + LZ;

function mapStateToUrl() {
  const c = map.getCenter();
  const q = new URLSearchParams(location.search);
  q.set("lat", c.lat.toFixed(5));
  q.set("lon", c.lng.toFixed(5));
  q.set("z", String(Math.round(lz() * 100) / 100));
  history.replaceState(null, "", `?${q}`);
}
map.on("moveend", mapStateToUrl);

// ---------- podlaga ----------
//
// Slog je `podlaga.json`, isti kot na ostalih zemljevidih. Plasti, ki so
// samo tukaj (stavbe v 3D in vse nase), se dodajo ob nalaganju.
// Nase plasti imajo predpono `k-`; vse ostalo je podlaga in ta se prizge ali
// ugasne kot celota (`osveziPodlago`).

const STAVBE_3D = "stavbe-3d";
const PRAZNO = { type: "FeatureCollection", features: [] };
let esri = false;
let izrisano = false;
let slojiDodani = false;

map.on("load", () => { izrisano = true; });
map.on("error", (e) => {
  const zakaj = e && e.error && e.error.message;
  // Opis ploscic pred prvim izrisom ni prisel (OpenFreeMap ni dosegljiv):
  // rezerva. Napaka ene ploscice pozneje ni razlog za menjavo.
  if (!izrisano && e.sourceId === "omt") naEsri(zakaj);
  else console.warn("zemljevid:", zakaj);
});

function naEsri(zakaj) {
  if (esri) return;
  esri = true;
  console.warn("vektorska podlaga ni na voljo, velja Esri:", zakaj);
  const pod = map.getLayer("k-proge-obroba") ? "k-proge-obroba" : undefined;
  const ploscice = (sloj) => ({
    type: "raster", tileSize: 256,
    // Esri ima prave ploscice samo do z16; nad tem MapLibre zadnjo raztegne.
    maxzoom: 16,
    tiles: [`${ESRI_CANVAS}/${sloj}/MapServer/tile/{z}/{y}/{x}`],
  });
  map.addSource("esri", { ...ploscice("World_Dark_Gray_Base"), attribution: ESRI_ATTR });
  map.addSource("esri-imena", ploscice("World_Dark_Gray_Reference"));
  map.addLayer({ id: "esri", type: "raster", source: "esri" }, pod);
  map.addLayer({
    id: "esri-imena", type: "raster", source: "esri-imena",
    metadata: { "kajros:napisi": "dodatni" }, paint: { "raster-opacity": 0.9 },
  }, pod);
  osveziPodlago();
}

function vidnost(id, on) {
  if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", on ? "visible" : "none");
}

function nastaviVir(id, data) {
  const vir = map.getSource(id);
  if (vir) vir.setData(data);
}

// Podlaga, dodatna imena in stavbe v 3D. Vse to so plasti v slogu, zato ena
// zanka; `getStyle()` ni primeren, ker vsakic zapise tudi vse
// podatke vseh virov (9 519 postajalisc).
function osveziPodlago() {
  if (!slojiDodani) return;
  for (const id of map.getLayersOrder()) {
    if (id.startsWith("k-")) continue;
    const l = map.getLayer(id);
    const jeEsri = l.source === "esri" || l.source === "esri-imena";
    let on = vklop.base && (esri ? jeEsri : !jeEsri);
    if (l.metadata && l.metadata["kajros:napisi"] === "dodatni") on = on && vklop.labels;
    if (id === STAVBE_3D) on = on && vklop["3d"];
    vidnost(id, on);
  }
}

// Proga je narisana DVAKRAT: široka temna obroba spodaj, svetla črta
// zgoraj. Ena sama črta se je na temni podlagi izgubila, debelejša pa je
// bila videti kot cesta. Obroba jo loči od podlage, ne da bi jo odebelila.
const PROGA = "#7d8899";
const OKROGLO = { "line-join": "round", "line-cap": "round" };

function dodajSloje() {
  // Stavbe od blizu. Visina raste z zoomom od nic do prave (`render_height`
  // iz OpenStreetMap) hkrati z nagibom kamere; od zgoraj so ploskve, kot so
  // bile. Pod napisi, sicer stavba pokrije ime ulice za sabo.
  const prviNapis = map.getLayersOrder().find((id) => map.getLayer(id).type === "symbol");
  map.addLayer({
    id: STAVBE_3D, type: "fill-extrusion", source: "omt", "source-layer": "building",
    minzoom: NAGIB_OD,
    paint: {
      // Barva je ista kot ploskev stavbe v slogu, da je stavba od zgoraj in
      // od strani ena stvar.
      "fill-extrusion-color": map.getPaintProperty("stavba", "fill-color"),
      "fill-extrusion-height": ["interpolate", ["linear"], ["zoom"],
        NAGIB_OD, 0, NAGIB_OD + 2, ["coalesce", ["get", "render_height"], 0]],
      "fill-extrusion-base": ["interpolate", ["linear"], ["zoom"],
        NAGIB_OD, 0, NAGIB_OD + 2, ["coalesce", ["get", "render_min_height"], 0]],
      "fill-extrusion-opacity": ["interpolate", ["linear"], ["zoom"], NAGIB_OD, 0, NAGIB_OD + 1, 0.9],
    },
  }, prviNapis);

  for (const id of ["k-proge", "k-vse-trase", "k-postaje", "k-postajalisca", "k-trasa",
                    "k-trasa-skica", "k-trasa-postaje", "k-najdena", "k-jaz", "k-avtobusi"]) {
    map.addSource(id, { type: "geojson", data: PRAZNO });
  }

  // Vrstni red plasti je vrstni red risanja: proge in postaje spodaj, vozila
  // zgoraj. Brez tega vlak izgine pod progo, po kateri vozi.
  map.addLayer({ id: "k-proge-obroba", type: "line", source: "k-proge", layout: OKROGLO,
                 paint: { "line-color": "#11141a", "line-width": 5.5, "line-opacity": 0.9 } });
  map.addLayer({ id: "k-proge", type: "line", source: "k-proge", layout: OKROGLO,
                 paint: { "line-color": PROGA, "line-width": 2 } });
  map.addLayer({ id: "k-vse-trase", type: "line", source: "k-vse-trase", layout: OKROGLO,
                 paint: { "line-color": ["match", ["get", "network"], "avtobus", BUS_INK, PROGA],
                          "line-width": 1.6, "line-opacity": 0.42 } });
  // Pika brez imena ne pove nicesar; trajna oznaka pri 267 postajah
  // zakrije progo. Zato ime ob dotiku. Polmer 3,4 namesto 2,4: pika
  // 2,4 px je manjsa od prsta in je ni mogoce zadeti.
  map.addLayer({ id: "k-postaje", type: "circle", source: "k-postaje",
                 paint: { "circle-radius": 3.4, "circle-color": "#8b95a4" } });
  map.addLayer({ id: "k-postajalisca", type: "circle", source: "k-postajalisca",
                 minzoom: BUSSTOP_MIN_Z - LZ,
                 paint: { "circle-radius": 3.2, "circle-color": BUS_INK, "circle-opacity": 0.85,
                          "circle-stroke-color": "#0f1115", "circle-stroke-width": 1 } });
  map.addLayer({ id: "k-trasa-obroba", type: "line", source: "k-trasa", layout: OKROGLO,
                 paint: { "line-color": "#0f1115", "line-width": 6, "line-opacity": 0.85 } });
  map.addLayer({ id: "k-trasa", type: "line", source: "k-trasa", layout: OKROGLO,
                 paint: { "line-color": BUS_INK, "line-width": 3, "line-opacity": 0.95 } });
  // Crta skozi postajalisca ni pot po cesti in mora biti videti drugace.
  map.addLayer({ id: "k-trasa-skica", type: "line", source: "k-trasa-skica",
                 paint: { "line-color": BUS_INK, "line-width": 2.5, "line-opacity": 0.7,
                          "line-dasharray": [2, 2] } });
  map.addLayer({ id: "k-trasa-postaje", type: "circle", source: "k-trasa-postaje",
                 paint: { "circle-radius": 3.6, "circle-color": BUS_INK,
                          "circle-stroke-color": "#0f1115", "circle-stroke-width": 1.4 } });
  map.addLayer({ id: "k-najdena", type: "circle", source: "k-najdena",
                 paint: { "circle-radius": 9, "circle-color": "#0f1115", "circle-opacity": 0.6,
                          "circle-stroke-color": "#e7eaf0", "circle-stroke-width": 3 } });
  map.addLayer({ id: "k-jaz-obroc", type: "fill", source: "k-jaz",
                 filter: ["==", ["get", "vrsta"], "obroc"],
                 paint: { "fill-color": ME_COLOR, "fill-opacity": 0.1 } });
  map.addLayer({ id: "k-jaz-rob", type: "line", source: "k-jaz",
                 filter: ["==", ["get", "vrsta"], "obroc"],
                 paint: { "line-color": ME_COLOR, "line-width": 1, "line-opacity": 0.35 } });
  map.addLayer({ id: "k-jaz", type: "circle", source: "k-jaz",
                 filter: ["==", ["get", "vrsta"], "pika"],
                 paint: { "circle-radius": 6, "circle-color": ME_COLOR,
                          "circle-stroke-color": "#ffffff", "circle-stroke-width": 2 } });
}

const stationMarkers = new Map();   // ime postaje -> maplibregl.Marker
let stationsByName = new Map();     // ime postaje -> {stop_id, lat, lon}
let liveTrains = [];
let liveBuses = [];

// Zacetni pogled se prilagodi VOZILOM, ne postajam. Prej je bil okvir
// izracunan iz vseh 9 791 postajalisc -- ta segajo od Breginja do Pinc, torej
// cez vso sirino drzave, in na telefonu (430 px sirine, 900 visine) je zoom
// dolocila sirina: Slovenija je zapolnila trak na sredini, nad njo in pod njo
// pa sta bili Avstrija in Jadran. Stran odgovarja na "kje je zdaj kaj",
// zato okvir dolocajo vozila; kadar so razkropljena po drzavi, je to itak
// spet cela Slovenija.
let pogledPrilagojen = HAS_START;
let vlakiPrispeli = false, vozilaPrispela = false;

function prilagodiPogledVozilom() {
  if (pogledPrilagojen || !vlakiPrispeli || !vozilaPrispela) return;
  const okvir = new maplibregl.LngLatBounds();
  let n = 0;
  for (const t of liveTrains) {
    const st = t.reported_lat != null
      ? { lat: t.reported_lat, lon: t.reported_lon } : stationsByName.get(t.last_stop);
    if (st && st.lat != null) { okvir.extend([st.lon, st.lat]); n += 1; }
  }
  for (const v of liveBuses) if (v.lat != null) { okvir.extend([v.lon, v.lat]); n += 1; }
  pogledPrilagojen = true;
  if (!n) return;                            // ponoci se zgodi; ostane cela drzava
  // maxZoom: dve vozili na isti postaji ne smeta priblizati na ulico.
  map.fitBounds(okvir, { padding: 30, maxZoom: 12 - LZ, animate: false });
}

async function loadStatic() {
  try {
    // Samo železniške postaje: avtobusnih je nekaj tisoč in mreža prog bi
    // izginila pod postajališči.
    const stations = await fetch("/api/stations?network=zeleznica").then((r) => r.json());
    stationsByName = new Map(stations.map((s) => [s.name, s]));
    nastaviVir("k-postaje", tocke(stations.filter((s) => s.lat != null)));
  } catch (err) {
    console.error("postaj ni bilo mogoče naložiti", err);
  }

  try {
    nastaviVir("k-proge", await fetch("/api/network.geojson").then((r) => r.json()));
  } catch (err) {
    console.error("mreže ni bilo mogoče naložiti", err);
  }
}

// Seznam postaj {name, lat, lon} kot tocke z imenom, ki ga pokaze dotik.
function tocke(postaje) {
  return {
    type: "FeatureCollection",
    features: postaje.map((s) => ({
      type: "Feature", properties: { ime: s.name },
      geometry: { type: "Point", coordinates: [s.lon, s.lat] },
    })),
  };
}

// Trasa iz API-ja je seznam kosov [[lat, lon], ...]; kos z eno tocko ni crta.
function kosiVCrto(kosi, lastnosti) {
  return {
    type: "Feature", properties: lastnosti || {},
    geometry: { type: "MultiLineString",
                coordinates: kosi.filter((k) => k && k.length > 1)
                  .map((k) => k.map(([lat, lon]) => [lon, lat])) },
  };
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

// Kartica vozila. Klik na zemljevidu je doslej odprl novo stran -- to je
// veliko za vprasanje "kaj pa je to". Kartica odgovori na mestu in ponudi
// stran tistemu, ki jo res hoce.
// Pri vlaku je stevilka enolicna in prevoznik je vedno SZ, zato ga ne pisemo;
// pri avtobusu je "25" brez prevoznika dvoumna.
function agencyPrefix(v) {
  const ime = AGENCY[v.agency];
  return ime && v.network !== "zeleznica" ? `${ime} ` : "";
}

function vehCardHtml(o) {
  const rows = o.rows.map(([k, v, color]) => `
    <div class="veh-row"><span>${escapeHtml(k)}</span>
      <b${color ? ` style="color:${color}"` : ""}>${v}</b></div>`).join("");
  return `<div class="veh-card">
      <div class="veh-head">
        <span class="veh-no">${escapeHtml(o.no)}</span>${o.badge || ""}
        <span class="veh-headsign">${escapeHtml(o.headsign || "")}</span>
      </div>
      <div class="veh-rows">${rows}</div>
      <a class="veh-open" href="${o.href}" target="_blank" rel="noopener">
        Odpri stran o vozilu →</a>
    </div>`;
}

function tripHref(trainNo, tripId, serviceDate, network) {
  const q = new URLSearchParams();
  if (serviceDate) q.set("date", serviceDate);
  if (tripId) q.set("trip", tripId);
  const pot = network === "avtobus" ? "/app/bus/" : "/app/train/";
  return `${pot}${encodeURIComponent(trainNo)}${q.toString() ? `?${q}` : ""}`;
}

function trainCardHtml(t) {
  const d = bestDelay(t);
  return vehCardHtml({
    no: t.train_no, badge: modeBadgeHtml(t.mode), headsign: t.headsign,
    href: tripHref(t.train_no, t.trip_id, t.service_date, "zeleznica"),
    rows: [
      ["zamuda", delayText(d.value), delayColor(d.value)],
      ["zadnja meritev", escapeHtml(d.where || "—")],
      [d.fromOperator ? "poročal prevoznik" : "izmerjeno",
       t.measured_at ? `ob ${hhmm(t.measured_at)}` : "—"],
    ],
  });
}

function busCardHtml(v) {
  // Zamuda in kraj morata biti iz istega vira: "+15 min" brez postaje, kjer
  // je bila izmerjena, je stevilka brez pomena, ce je vozilo od takrat ze
  // dalec naprej.
  const rows = v.delay_s == null
    ? [["zamuda", "ni meritve"]]
    : [["zamuda", delayText(v.delay_s), delayColor(v.delay_s)],
       ["zadnja meritev", escapeHtml(v.last_stop || "—")]];
  return vehCardHtml({
    no: agencyPrefix(v) + v.train_no, badge: "", headsign: v.headsign,
    href: tripHref(v.train_no, v.trip_id, v.service_date, "avtobus"),
    rows: rows.concat([
      ["hitrost", v.speed_kmh == null ? "ni podatka"
        : v.speed_kmh >= 3 ? `${v.speed_kmh} km/h` : "stoji"],
      ["lega stara", ageHtml(v.age_s)],
    ]),
  });
}

// Oznaka nosi SAMO stevilko. Zamuda je odsla s zemljevida na kartico: kdor
// gleda zemljevid, sprasuje "kje je", ne "koliko zamuja". Iz tega sledi tudi,
// da marker vlaka nima barve lestvice -- barva brez minute poleg sebe bi
// nosila pomen sama, in prav to je v projektu prepovedano.
function trainLineHtml(t) {
  return `<span class="train-label-code">${escapeHtml(t.train_no)}</span>`
    + modeBadgeHtml(t.mode);
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
  return `
    <div class="popup-station">${escapeHtml(g.name)}</div>
    <div class="popup-note">zadnja postaja z meritvijo — ${g.trains.length === 1
      ? "1 vlak" : `${g.trains.length} vlakov`}</div>
    <div class="popup-list">${g.trains.map(trainCardHtml).join("")}</div>`;
}

const TRAIN_INK = "#f0934f";

function trainSize(z) {
  if (z >= 17) return 38;
  if (z >= 13) return 30;
  if (z >= 11) return 24;
  if (z >= 9) return 19;
  return 15;
}

// Vlak od zgoraj, na obrocu. Obroc ni okras: pove, da je to POSTAJA in ne
// izmerjena lega -- feed za vlake GPS nima in marker stoji na zadnji postaji
// z meritvijo. Avtobus obroca nima, ker je njegova lega prava.
function trainSvg(n, s) {
  return `<svg width="${s}" height="${s}" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="11" fill="none"
              stroke="${TRAIN_INK}" stroke-opacity="0.45" stroke-width="1.4"/>
      <rect x="7" y="3.5" width="10" height="17" rx="3.4"
            fill="${TRAIN_INK}" stroke="#0f1115" stroke-width="1.5"/>
      <path d="M8.8 6.6 Q12 5.5 15.2 6.6 L15.2 9.2 Q12 8.2 8.8 9.2 Z"
            fill="#0f1115" fill-opacity="0.7"/>
      <circle cx="9.8" cy="18" r="1" fill="#0f1115" fill-opacity="0.8"/>
      <circle cx="14.2" cy="18" r="1" fill="#0f1115" fill-opacity="0.8"/>
      ${n > 1 ? `<circle cx="19" cy="5" r="4" fill="#0f1115"/>
        <text x="19" y="7.4" text-anchor="middle" font-size="6"
              font-family="monospace" fill="${TRAIN_INK}">${n}</text>` : ""}
    </svg>`;
}

// Vlaki so elementi DOM nad zemljevidom, avtobusi pa plast v njem. Vlakov je
// do nekaj deset in njihova oznaka je vec vrstic besedila z znacko -- to je
// HTML, ki ga plast ne zna; avtobusov je lahko 1 500 in DOM bi pri vsakem
// premiku zemljevida vsakega prestavljal posebej.
function trainMarker(g, s) {
  const el = document.createElement("div");
  el.className = "train-marker";
  el.innerHTML = '<div class="train-icon"></div><div class="train-label"></div>';
  const m = new maplibregl.Marker({ element: el, anchor: "center" })
    .setLngLat([g.station.lon, g.station.lat])
    .setPopup(new maplibregl.Popup({ maxWidth: "280px", offset: s / 2 }));
  m.__icon = el.firstChild;
  m.__label = el.lastChild;
  return m;
}

function renderTrains(trains) {
  // Vlaki NIMAJO GPS lege -- marker je vedno točno na zadnji znani postaji,
  // nikoli interpoliran vzdolž proge. Obroč okoli ikone to pove na pogled.
  const groups = groupByStation(trains);
  const s = trainSize(lz());
  for (const [name, g] of groups) {
    let marker = stationMarkers.get(name);
    if (!marker) {
      marker = trainMarker(g, s);
      if (vklop.train) marker.addTo(map);
      stationMarkers.set(name, marker);
    } else {
      marker.setLngLat([g.station.lon, g.station.lat]);
    }
    const ikona = marker.__icon;
    ikona.style.width = ikona.style.height = `${s}px`;
    ikona.innerHTML = trainSvg(g.trains.length, s);
    marker.__label.innerHTML = groupLabelHtml(g);
    marker.getPopup().setOffset(s / 2).setHTML(groupPopupHtml(g));
    marker.__worst = worstDelay(g.trains);
  }
  for (const [name, marker] of stationMarkers) {
    if (!groups.has(name)) {
      marker.remove();
      stationMarkers.delete(name);
    }
  }
  requestAnimationFrame(declutterLabels);
}

// Velikost ikone vlaka je odvisna od zooma, marker pa se sam ne skalira.
let zoomTimer = null;
map.on("zoomend", () => {
  clearTimeout(zoomTimer);
  zoomTimer = setTimeout(() => renderTrains(liveTrains), 60);
});

// ---------- avtobusi: prava lega iz GPS ----------
// Vlaki v feedu nimajo GPS, avtobusi ga imajo. To sta dve različni stvari na
// isti sliki in ju je treba ločiti tudi na pogled: vlak je krog na postaji,
// avtobus je oblika vozila na izmerjeni legi.

// Barva na zemljevidu pove, CIGAV avtobus je. Izbrane so tako, da se locijo
// tudi pri barvni slepoti: najslabsi par je pri deutan/protan ΔE 9,6 (prag 3)
// in celo pri tritanopiji 4,8 -- preverjeno s scripts/preveri_paleto.py, ne na
// oko. Proti lestvici zamud zelena in oranzna pri deutanu trcita (ΔE 1,2), a
// to ni tezava: vozila locuje OBLIKA (avtobus je puscica, vlak krog), barva pa
// nikoli ne nosi pomena sama -- oznaka poleg nosi ime prevoznika.
const BUS_INK = "#4db97f";                    // privzeto, kadar prevoznik ni znan
const AGENCY_INK = {
  "1118": "#4db97f",   // LPP
  "1123": "#6fb8ff",   // Arriva
  "1119": "#9d7ae0",   // Nomago
  "1121": "#c9a227",   // AP Murska Sobota
};

// LPP je EN prevoznik z dvema viroma: `1118` so primestne linije iz IJPP,
// `lpp` mestne iz lastnega feeda. Na postajaliscu pise oboje "LPP", zato
// morata imeti eno plast, en stevec in eno barvo. Brez tega so mestni
// avtobusi padli med "druge prevoznike" -- na produkciji 104 od 179 zivih
// vozil (7. 9. 2026), torej vecina, in to za stikalom, ki je privzeto
// ugasnjeno in se imenuje, kot da prevoznika ne poznamo.
const agencyKey = (v) => (v && v.agency === "lpp" ? "1118" : v && v.agency);
// Plast avtobusa: prevoznik s svojim stikalom ali "drugi".
const busGroup = (v) => (AGENCY_INK[agencyKey(v)] ? agencyKey(v) : "drugi");
const busInk = (v) => AGENCY_INK[agencyKey(v)] || BUS_INK;
const busKey = (v) => v.trip_id || `${v.train_no}:${v.lat},${v.lon}`;

// Velikost sledi približevanju. Pri pogledu na vso Slovenijo je vozil do sto
// in majhna oblika je edina, ki se ne slepi; ko kdo približa na eno ulico,
// pa je iskal prav to vozilo in mora biti veliko -- vektorska podlaga ostane
// ostra do z19, zato naj bo vozilo takrat priblizno tako veliko kot ulica.
// Pari [Leafletov zoom, px]; vmes velikost tece zvezno.
const BUS_VELIKOST = [[9, 15], [10, 20], [12, 26], [14, 34], [17, 44]];
const BUS_SLIKA = 44;          // px, v katerih je slika narisana (in 2x za ostrino)

// Avtobus od zgoraj: zaobljeno telo, svetlejše vetrobransko steklo spredaj in
// zarezi za kolesi. Puščica je bila premalo -- pri približku je bila videti
// kot pika in se od vlaka ni ločila.
function busSvg(size, moving, ink) {
  const o = moving ? 1 : 0.5;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24">
      <g>
        <rect x="7.5" y="2.5" width="9" height="19" rx="3.2"
              fill="${ink}" fill-opacity="${o}"
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

const busIkona = (ink, moving) => `bus-${ink.slice(1)}-${moving ? "vozi" : "stoji"}`;

// Od blizu je avtobus model v 3D (`avtobusi3d.js`), od dalec ikona. Meja je
// tam, kjer se kamera ze vidno nagne (24° pri Leafletovem z16); od zgoraj bi
// bil model bela skatla, ikona pa pove smer in prevoznika na prvi pogled.
const AVTOBUS_3D_OD = 15;      // MapLibrov zoom
let avtobusi3d = null;
let vozila3d = [];             // kar plast 3D ta hip rise, za dotik

// Model je vecji od resnicnega, sicer bi bil pri z16 dolg sedem pik: tako
// velik kot ikona, ko se prikaze (~36 px), in blizje resnici, ko se
// priblizas (pri z19 1,7-krat).
const povecava3D = (z) => 3.5 * 2 ** (-(z - 16) * 0.5);
const vidni3D = () => !!avtobusi3d && vklop["3d"] && map.getZoom() >= AVTOBUS_3D_OD;

// Slike avtobusov za plast: ena na barvo in stanje (vozi / stoji).
async function dodajAvtobuse() {
  const barve = [...new Set([BUS_INK, ...Object.values(AGENCY_INK)])];
  await Promise.all(barve.flatMap((ink) => [true, false].map(async (moving) => {
    const img = new Image();
    img.src = `data:image/svg+xml;charset=utf-8,${
      encodeURIComponent(busSvg(BUS_SLIKA * 2, moving, ink))}`;
    await img.decode();
    map.addImage(busIkona(ink, moving), img, { pixelRatio: 2 });
  })));
  map.addLayer({
    id: "k-avtobusi", type: "symbol", source: "k-avtobusi",
    layout: {
      "icon-image": ["get", "ikona"],
      "icon-size": ["interpolate", ["linear"], ["zoom"],
        ...BUS_VELIKOST.flatMap(([z, px]) => [z - LZ, px / BUS_SLIKA])],
      "icon-rotate": ["get", "smer"],
      // Vozilo kaze smer voznje glede na sever, ne glede na zaslon. V nagibu
      // ostane obrnjeno proti gledalcu: polozeno na cesto je bilo pri 60° za
      // pol nizje in med stavbami ga je bilo tezko najti.
      "icon-rotation-alignment": "map",
      "icon-pitch-alignment": "viewport",
      // Vsa vozila, vedno: skrito vozilo je vozilo, ki ga ni.
      "icon-allow-overlap": true,
      "icon-ignore-placement": true,
    },
  });
  avtobusi3d = avtobusi3D({
    id: "k-avtobusi-3d",
    inki: { ...AGENCY_INK, drugi: BUS_INK },
    vidna: vidni3D,
    povecava: povecava3D,
  });
  map.addLayer(avtobusi3d.plast);
  uveljavi();
}

// Plasti 3D damo samo vozila v sliki in pas okrog nje: brez tega gre ob
// konici 1 500 modelov skozi risanje na vsak premik.
function posodobi3D() {
  if (!avtobusi3d) return;
  const vidni = new Set(LAYERS.filter((s) => s.ag && vklop[s.key]).map((s) => s.ag));
  const b = map.getBounds();
  const dx = (b.getEast() - b.getWest()) / 2;
  const dy = (b.getNorth() - b.getSouth()) / 2;
  vozila3d = [];
  for (const v of busByKey.values()) {
    const model = busGroup(v);
    if (!vidni.has(model)) continue;
    if (v.lon < b.getWest() - dx || v.lon > b.getEast() + dx
        || v.lat < b.getSouth() - dy || v.lat > b.getNorth() + dy) continue;
    vozila3d.push({ lon: v.lon, lat: v.lat, smer: v.bearing ?? 0, model, kljuc: busKey(v) });
  }
  avtobusi3d.nastavi(vozila3d);
}

// Avtobus v 3D pod prstom. Plast 3D ni v `queryRenderedFeatures`, zato
// preverimo sami: razdalja do lege na zaslonu, polmer pa pol dolzine modela
// (12 m krat povecava), a vsaj za prst.
function zadetek3D(p) {
  if (!vidni3D()) return null;
  const r = Math.max(18, (6 * povecava3D(map.getZoom())) / mppZdaj());
  let naj = null, najd = r;
  for (const a of vozila3d) {
    const q = map.project([a.lon, a.lat]);
    const d = Math.hypot(q.x - p.x, q.y - p.y);
    if (d < najd) { najd = d; naj = a; }
  }
  return naj && { layer: { id: "k-avtobusi" }, properties: { kljuc: naj.kljuc },
                  geometry: { type: "Point", coordinates: [naj.lon, naj.lat] } };
}

function busTooltipHtml(v) {
  return `<div class="train-label-line">`
    + `<span class="train-label-code" style="color:${busInk(v)}">`
    + `${escapeHtml(agencyPrefix(v))}${escapeHtml(v.train_no)}</span>`
    + `<span class="train-label-more">${escapeHtml(v.headsign || "")}</span></div>`
    + `<div class="train-label-more">`
    + `${v.speed_kmh != null ? (v.speed_kmh >= 3 ? `${v.speed_kmh} km/h` : "stoji") : "brez hitrosti"}`
    + ` · lega stara ${ageHtml(v.age_s)}</div>`;
}

let busByKey = new Map();      // kljuc -> vozilo

function renderBuses(list) {
  busByKey = new Map();
  const features = [];
  for (const v of list) {
    if (v.lat == null) continue;
    const kljuc = busKey(v);
    busByKey.set(kljuc, v);
    features.push({
      type: "Feature",
      geometry: { type: "Point", coordinates: [v.lon, v.lat] },
      properties: {
        kljuc, ag: busGroup(v), smer: v.bearing == null ? 0 : v.bearing,
        ikona: busIkona(busInk(v), (v.speed_kmh || 0) >= 3),
      },
    });
  }
  nastaviVir("k-avtobusi", { type: "FeatureCollection", features });
  posodobi3D();
  // Odprta kartica gre z vozilom; ce ga ni vec, gre tudi ona.
  if (kartica && kartica.__kljuc) {
    const v = busByKey.get(kartica.__kljuc);
    if (v) kartica.setLngLat([v.lon, v.lat]).setHTML(busCardHtml(v));
    else kartica.remove();
  }
}

// ---------- dotik in lebdenje ----------
//
// Ime postaje se pokaze na dotik in po petih sekundah odide (`NAME_MS` v
// common.js); brez gumba za zapiranje, ker bi bil na telefonu manjsi od
// prsta. Na napravi z misko se pokaze ze ob lebdenju, kot prej.

const IMENA = ["k-postaje", "k-postajalisca", "k-trasa-postaje", "k-jaz"];
// Dotik zadene, kar je v tem polmeru: pika postaje meri 7 px, prst dosti vec.
const DOTIK_PX = 12;

let kartica = null;            // odprta kartica avtobusa
let imeOkno = null;
let imeCas = null;
let najdenaOkno = null;

// Najblizje, kar je pod prstom: vozilo pred postajo, postaja pred postajo.
function zadetek(p) {
  const v3d = zadetek3D(p);
  if (v3d) return v3d;
  const sloji = ["k-avtobusi", "k-najdena", ...IMENA].filter((id) => map.getLayer(id));
  const r = DOTIK_PX;
  const f = map.queryRenderedFeatures([[p.x - r, p.y - r], [p.x + r, p.y + r]],
                                      { layers: sloji });
  let naj = null, najd = Infinity;
  for (const x of f) {
    if (x.geometry.type !== "Point") continue;
    const q = map.project(x.geometry.coordinates);
    const d = Math.hypot(q.x - p.x, q.y - p.y) + sloji.indexOf(x.layer.id) * 1000;
    if (d < najd) { najd = d; naj = x; }
  }
  return naj;
}

// Metrov na piksel v sredini slike; za velikost modela na zaslonu.
function mppZdaj() {
  return 40075016.686 * Math.cos((map.getCenter().lat * Math.PI) / 180)
    / (512 * 2 ** map.getZoom());
}

function odpriKartico(v) {
  if (kartica) kartica.remove();
  // Model v 3D stoji nad svojo lego; kartica gre nad streho, ne cezenj.
  const nad = vidni3D() ? (3.4 * povecava3D(map.getZoom())) / mppZdaj() : 0;
  kartica = new maplibregl.Popup({ maxWidth: "280px", offset: 14 + nad })
    .setLngLat([v.lon, v.lat]).setHTML(busCardHtml(v)).addTo(map);
  kartica.__kljuc = busKey(v);
  kartica.on("close", () => { kartica = null; });
}

function pokaziIme(f) {
  clearTimeout(imeCas);
  if (imeOkno) imeOkno.remove();
  imeOkno = new maplibregl.Popup({ closeButton: false, className: "kajros-tooltip", offset: 8 })
    .setLngLat(f.geometry.coordinates).setText(f.properties.ime).addTo(map);
  imeCas = setTimeout(() => imeOkno && imeOkno.remove(), NAME_MS);
}

map.on("click", (e) => {
  // Vlak odpre svojo kartico sam (marker s `setPopup`), klik v kartico pa ni
  // klik na zemljevid.
  if (e.originalEvent.target.closest(".maplibregl-marker, .maplibregl-popup")) return;
  const f = zadetek(e.point);
  // Dotik praznega zemljevida zapre spodnjo plosco -- to je najbolj
  // pricakovana gesta in deluje tudi, ce kdo rocaja ne opazi.
  if (!f) { setSheet(false); return; }
  if (lebdi) lebdi.remove();
  if (f.layer.id === "k-avtobusi") {
    const v = busByKey.get(f.properties.kljuc);
    if (v) odpriKartico(v);
  } else if (f.layer.id === "k-najdena") {
    if (najdenaOkno) najdenaOkno.addTo(map);
  } else {
    pokaziIme(f);
  }
});

// Lebdenje samo tam, kjer miska res je: telefon ob dotiku poslje tudi
// posnemani `mousemove` in ime bi se pokazalo dvakrat.
let lebdi = null;
if (matchMedia("(hover: hover)").matches) {
  lebdi = new maplibregl.Popup({ closeButton: false, closeOnClick: false,
                                 className: "kajros-tooltip", offset: 12 });
  map.on("mousemove", (e) => {
    const sloji = ["k-avtobusi", ...IMENA].filter((id) => map.getLayer(id));
    const f = zadetek3D(e.point) || map.queryRenderedFeatures(e.point, { layers: sloji })[0];
    map.getCanvas().style.cursor = f ? "pointer" : "";
    if (!f) { lebdi.remove(); return; }
    const v = f.layer.id === "k-avtobusi" && busByKey.get(f.properties.kljuc);
    if (v) lebdi.setHTML(busTooltipHtml(v));
    else lebdi.setText(f.properties.ime);
    lebdi.setLngLat(f.geometry.coordinates).addTo(map);
  });
  map.on("mouseout", () => lebdi.remove());
}

// ---------- razvrščanje oznak ----------

const labelNoteEl = document.getElementById("label-note");

function declutterLabels() {
  // Oznake vlakov so DOM in se ne izogibajo trkom: v gostih vozliščih se
  // prekrivajo. Požrešno pravilo -- večja zamuda ima prednost, prekrite
  // skrijemo in povemo, koliko jih je.
  const entries = [];
  for (const marker of stationMarkers.values()) {
    const el = marker.__label;
    el.style.display = "";
    entries.push({ el, worst: marker.__worst ?? -Infinity });
  }
  entries.sort((a, b) => b.worst - a.worst);

  const kept = [];
  let hidden = 0;
  const PAD = 2;
  const okvir = map.getContainer().getBoundingClientRect();
  for (const e of entries) {
    const r = e.el.getBoundingClientRect();
    if (!r.width && !r.height) continue;         // ni na zemljevidu
    // Oznaka izven slike ne zakrije nicesar; stela bi se v "skritih" in
    // opomba bi govorila o necem, cesar clovek ne vidi.
    if (r.right < okvir.left || r.left > okvir.right
        || r.bottom < okvir.top || r.top > okvir.bottom) continue;
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

map.on("moveend", () => requestAnimationFrame(declutterLabels));

// ---------- moja lega ----------
//
// Gumb pod priblizevanjem, kot je navada pri zemljevidih. Klik jo poisce in
// priblizka nanjo; drugi klik jo skrije -- to je hkrati "moznost prikaza",
// zato zanjo ni se ene izbire v seznamu plasti.
//
// Lokacije ne zahtevamo sami ob nalaganju (glej `locateMe` v common.js).
let meLoc = null;

function meNote(text) {
  const n = document.getElementById("me-note");
  if (!n) return;
  n.textContent = text || "";
  n.hidden = !text;
  if (text) setTimeout(() => { if (n.textContent === text) n.hidden = true; }, 4000);
}

// Krog v metrih kot mnogokotnik: obroc tocnosti mora v nagibu lezati na tleh
// in rasti s priblizkom, kar krog v pikslih ne zna.
function krog(lat, lon, m, n = 48) {
  const dLat = m / 111320;
  const dLon = m / (111320 * Math.cos(lat * Math.PI / 180));
  const pts = [];
  for (let i = 0; i <= n; i += 1) {
    const a = (i / n) * 2 * Math.PI;
    pts.push([lon + dLon * Math.cos(a), lat + dLat * Math.sin(a)]);
  }
  return pts;
}

// Pika z obrocem tocnosti. Obroc ni okras: GPS v mestu zna zgresiti za sto
// metrov in pika brez njega trdi natancnost, ki je nima (isto kot `drawMe`).
function narisiMe(loc) {
  const features = [];
  if (loc && loc.acc && loc.acc > 25) {
    features.push({ type: "Feature", properties: { vrsta: "obroc" },
                    geometry: { type: "Polygon", coordinates: [krog(loc.lat, loc.lon, loc.acc)] } });
  }
  if (loc) {
    features.push({
      type: "Feature",
      properties: { vrsta: "pika",
                    ime: loc.acc ? `tvoja lega (±${Math.round(loc.acc)} m)` : "tvoja lega" },
      geometry: { type: "Point", coordinates: [loc.lon, loc.lat] },
    });
  }
  nastaviVir("k-jaz", { type: "FeatureCollection", features });
}

let ustaviSledenje = null;

// Gumb na zemljevidu. Videz podeduje od MapLibrove skupine gumbov, da je
// videti kot del zemljevida in ne kot nalepka na njem.
function gumbZemljevida(razred, svg) {
  const el = document.createElement("div");
  el.className = `maplibregl-ctrl maplibregl-ctrl-group ${razred}`;
  const b = document.createElement("button");
  b.type = "button";
  b.innerHTML = svg;
  el.appendChild(b);
  return { el, b };
}

class LocateControl {
  onAdd() {
    const { el, b } = gumbZemljevida("locate-ctl", `<svg width="15" height="15"
        viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
        stroke-linecap="round"><circle cx="12" cy="12" r="3.4"></circle>
        <path d="M12 2v3M12 19v3M2 12h3M19 12h3"></path></svg>`);
    b.title = "Moja lega";
    b.setAttribute("aria-label", "Moja lega");
    b.addEventListener("click", async () => {
      if (meLoc) {                       // drugi klik skrije
        narisiMe(null);
        meLoc = null;
        if (ustaviSledenje) { ustaviSledenje(); ustaviSledenje = null; }
        el.classList.remove("is-on");
        return;
      }
      el.classList.add("is-busy");
      try {
        const loc = await locateMe({ napredek: narisiMe });
        narisiMe(loc);
        meLoc = loc;
        el.classList.add("is-on");
        map.easeTo({ center: [loc.lon, loc.lat], zoom: Math.max(map.getZoom(), 15 - LZ) });
        // Ena lega ni dovolj: prvi popravek GPS pogosto zgresi za sto metrov in
        // ga v naslednjih sekundah popravi, clovek pa se medtem premika. Pogled
        // se NE premika za njim -- zemljevid, ki bezi izpod prsta, je slabsi od
        // pike, ki jo je treba poiskati.
        ustaviSledenje = sledi((l) => { narisiMe(l); meLoc = l; });
      } catch (err) {
        meNote(err.message);
      } finally {
        el.classList.remove("is-busy");
      }
    });
    this.el = el;
    return el;
  }

  onRemove() { this.el.remove(); }
}

// ---------- osvezi zdaj ----------
//
// Vozila se osvezujejo sama in v koraku s strezbo, a tega se na zaslonu ne
// vidi. Kadar vozilo stoji ali feed zaostaja, je slika mirna -- in mirna slika
// je videti enako kot obticala stran. Brez gumba je edini izhod ponovno
// nalaganje cele strani, kar podlago in plasti nalozi znova za nic.
//
// Zanka se ob tem NE podvoji: `zdaj()` pri obeh poizvedbah prekine cakanje in
// ga nastavi na novo.
let vozilaPoll = null;

class OsveziControl {
  onAdd() {
    const { el, b } = gumbZemljevida("osvezi-ctl", `<svg width="15" height="15"
        viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round">
        <path d="M20 11a8 8 0 1 0-1.9 6.2"></path><path d="M20 5v6h-6"></path></svg>`);
    pripniOsvezi(b, [
      () => pollLive(),
      () => (vozilaPoll ? vozilaPoll.zdaj() : Promise.resolve()),
      () => refreshFeedDot(),
    ], meNote);
    b.title = "Osveži zdaj";
    b.setAttribute("aria-label", "Osveži zdaj");
    this.el = el;
    return el;
  }

  onRemove() { this.el.remove(); }
}

// Levo pod priblizevanjem, ne desno pod lego: na telefonu tam ze stoji tipka
// za spodnjo plosco (`.sheet-toggle`, `top: 62px`) in je gumb prekrila --
// videlo se je sele na posnetku v telefonski sirini. Kompas vrne sever;
// zemljevid se da zavrteti z dvema prstoma.
map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-left");
map.addControl(new OsveziControl(), "top-left");
map.addControl(new LocateControl(), "top-right");

// ---------- avtobusna postajalisca ----------
//
// 9 519 postajalisc, 211 kB z gzipom in 167 ms. Zato izbirno, privzeto
// ugasnjeno in nalozeno sele ob prvem vklopu -- enako kot trase.
//
// Risejo se sele od z13 naprej. Izmerjeno na ljubljanskem oknu 1200 x 800:
// pri z13 je v njem 253 postajalisc, pri z12 600, pri z11 pa 1 694 in mreza
// prog izgine pod njimi. Zato ni to pospesek, ampak pravilo prikaza -- ista
// misel kot pri trasah, ki so tudi privzeto ugasnjene.
const BUSSTOP_MIN_Z = 13;
let busStops = null;
let busStopsLoading = false;

const stopNoteEl = document.getElementById("stop-note");
function setStopNote(text) {
  if (!stopNoteEl) return;
  stopNoteEl.textContent = text || "";
  stopNoteEl.hidden = !text;
}

async function loadBusStops() {
  if (busStops || busStopsLoading) return;
  busStopsLoading = true;
  try {
    busStops = (await fetch("/api/stations?network=avtobus").then((r) => r.json()))
      .filter((s) => s.lat != null);
    nastaviVir("k-postajalisca", tocke(busStops));
  } catch (err) {
    console.warn("postajališč ni bilo mogoče naložiti", err);
  } finally {
    busStopsLoading = false;
  }
  renderBusStops();
}

// Plast rise MapLibre sam od praga naprej; tu sta samo stevec in opomba.
function renderBusStops() {
  const el = document.getElementById("n-busstops");
  if (!vklop.busstops) { setStopNote(null); return; }
  if (!busStops) return;
  if (lz() < BUSSTOP_MIN_Z) {
    setStopNote("Postajališča se pokažejo, ko približaš — zdaj bi jih bilo "
      + "toliko, da bi zakrila proge.");
    if (el) el.textContent = "";
    return;
  }
  setStopNote(null);
  const b = map.getBounds();
  let n = 0;
  for (const st of busStops) if (b.contains([st.lon, st.lat])) n += 1;
  if (el) el.textContent = n;
}

let stopTimer = null;
map.on("moveend", () => {
  clearTimeout(stopTimer);
  stopTimer = setTimeout(renderBusStops, 120);   // med vlecenjem ne prestevaj
  posodobi3D();
});

// ---------- plasti ----------
// Zemljevid je edini pogled, ki ga omrežji delita, zato mora biti mogoče
// vsako odložiti -- doslej se je dalo skriti samo avtobuse. Izbira se
// zapomni: kdor gleda vlake, jih gleda tudi jutri.
//
// Ena plast na prevoznika, ne ena skupna. Razlog je merjen: ob 15:10 je bilo
// na zemljevidu 1 530 avtobusov in slika je bila zelena kasa, v kateri se
// posamezno vozilo ni dalo najti. Zdaj je vsak prevoznik svoje potrditveno
// polje, privzeto pa so VSI ugasnjeni -- zemljevid se odpre kot zeleznicni,
// avtobuse prizges, ko jih res isces. `ag` je skupina v `busGroup()`.
//
// Trase vseh vozil na poti so svoja plast in privzeto ugasnjene: gost snop
// crt cez vso Ljubljano odgovarja na vprasanje "kod vozijo linije", ne na
// "kje je moj avtobus" -- in drugo je razlog za obisk te strani.
//
// Dodatna imena krajev (vasi, cetrti, vode) so privzeto ugasnjena: pri
// velikem priblizku bi tekmovala z vozili. Katera so, pove `podlaga.json`.

const LAYERS = [
  { id: "lay-train", key: "train", def: true },
  { id: "lay-lpp", key: "bus-lpp", def: false, ag: "1118" },
  { id: "lay-arriva", key: "bus-arriva", def: false, ag: "1123" },
  { id: "lay-nomago", key: "bus-nomago", def: false, ag: "1119" },
  { id: "lay-apms", key: "bus-apms", def: false, ag: "1121" },
  { id: "lay-bus-other", key: "bus-other", def: false, ag: "drugi" },
  { id: "lay-net", key: "net", def: true, sloji: ["k-proge-obroba", "k-proge"] },
  { id: "lay-routes", key: "routes", def: false, sloji: ["k-vse-trase"] },
  { id: "lay-stations", key: "stations", def: true, sloji: ["k-postaje"] },
  { id: "lay-busstops", key: "busstops", def: false, sloji: ["k-postajalisca"] },
  { id: "lay-labels", key: "labels", def: false },
  { id: "lay-base", key: "base", def: true },
  { id: "lay-3d", key: "3d", def: true },
];

function layerPref(key, def) {
  try {
    const v = localStorage.getItem(`kajros:map-${key}`);
    return v === null ? def : v === "1";
  } catch (err) {
    return def;
  }
}

// Stanje stikal na zemljevid. Pred nalaganjem sloga plasti se ni; takrat
// ostane samo stanje in se uveljavi ob `style.load`.
function uveljavi() {
  if (!slojiDodani) return;
  for (const spec of LAYERS) for (const id of spec.sloji || []) vidnost(id, vklop[spec.key]);
  if (map.getLayer("k-avtobusi")) {
    const ag = LAYERS.filter((s) => s.ag && vklop[s.key]).map((s) => s.ag);
    map.setFilter("k-avtobusi", ["in", ["get", "ag"], ["literal", ag]]);
    map.setLayerZoomRange("k-avtobusi", 0, vklop["3d"] ? AVTOBUS_3D_OD : 24);
  }
  posodobi3D();
  osveziPodlago();
}

function setLayer(spec, on) {
  vklop[spec.key] = on;
  const box = document.getElementById(spec.id);
  if (box) box.checked = on;
  try {
    localStorage.setItem(`kajros:map-${spec.key}`, on ? "1" : "0");
  } catch (err) {
    /* zaseben zavihek ni razlog, da stran ne dela */
  }
  if (spec.key === "train") {
    for (const m of stationMarkers.values()) {
      if (on) m.addTo(map);
      else m.remove();
    }
    if (on) requestAnimationFrame(declutterLabels);
  }
  // Kartica vozila, ki ga ni vec videti, ne sme ostati.
  if (spec.ag && !on && kartica && kartica.__kljuc) {
    const v = busByKey.get(kartica.__kljuc);
    if (v && busGroup(v) === spec.ag) kartica.remove();
  }
  uveljavi();
}

function initLayers() {
  for (const spec of LAYERS) {
    const box = document.getElementById(spec.id);
    setLayer(spec, layerPref(spec.key, spec.def));
    if (spec.key === "busstops" && vklop.busstops) loadBusStops();
    if (box) {
      box.addEventListener("change", () => {
        setLayer(spec, box.checked);
        // Prvi vklop mora tudi kaj narisati -- plast je ob zagonu prazna.
        if (spec.key === "routes" && box.checked && !routesLoaded) loadRoutes();
        if (spec.key === "busstops") {
          if (box.checked) loadBusStops();
          renderBusStops();
        }
        // Nagib se sicer spremeni sele ob naslednjem premiku kamere.
        if (spec.key === "3d") map.easeTo({ pitch: nagib(map.getZoom()), duration: 300 });
      });
    }
  }
}

// ---------- iskanje vozila ----------
// Vprašanje pred zemljevidom ni "kdo danes najbolj zamuja", ampak "kje je moj
// avtobus". Lestvica zamud je odgovarjala na prvo; iskalnik odgovarja na drugo.

const findEl = document.getElementById("find");
const findListEl = document.getElementById("find-list");
let selectedKey = null;

// Postaje v istem iskalniku. "Kje je Celje" je na zemljevidu enako pogosto
// vprašanje kot "kje je moj avtobus", a zemljevid imen postaj ne kaže, dokler
// se jih ne dotakneš -- in avtobusnih postajališč sploh ne, dokler plast ni
// vklopljena. Kazalo je isto kot pri najhitrejši poti (obe omrežji).
let kazaloPostaj = null;
naloziKazalo().then((k) => {
  kazaloPostaj = k;
  if (findEl.value.trim()) renderFind();
});
//: Toliko postaj nad vozili; več jih izrine vozila, po katera je človek prišel.
const NAJVEC_POSTAJ = 4;

// "25" je lahko cigar koli, zato clovek pise "lpp 25" -- in prav to doslej ni
// naslo nicesar, ker je iskalnik poznal samo stevilko in smer. Iscemo po
// celem imenu, kot ga vidi na zaslonu: "LPP 25 Medvode naselje - Zadobrova".
function vehText(v) {
  return `${AGENCY[v.agency] || ""} ${v.train_no} ${v.headsign || ""}`;
}

function findMatches(q) {
  const f = fold(q);
  if (!f) return [];
  // Vec besed pomeni "vse hkrati": "lpp 25" ne sme najti vsakega LPP-ja in
  // vsake petindvajsetice, ampak samo presek.
  const deli = f.split(/\s+/).filter(Boolean);
  const ujame = (v) => {
    const t = fold(vehText(v));
    return deli.every((d) => t.includes(d));
  };
  const out = [];
  for (const v of liveBuses) if (ujame(v)) out.push({ kind: "bus", v });
  for (const t of liveTrains) if (ujame(t)) out.push({ kind: "train", v: t });
  // Zadetek na zacetku stevilke je skoraj vedno tisti, ki ga clovek isce:
  // "25" naj da linijo 25 pred vsemi, ki jo imajo le v imenu smeri.
  const prvi = deli[0];
  out.sort((a, b) => Number(fold(b.v.train_no).startsWith(prvi))
                   - Number(fold(a.v.train_no).startsWith(prvi)));
  const postaje = kazaloPostaj && f.length >= 2
    ? iskalnikKazala(kazaloPostaj, q, NAJVEC_POSTAJ).map((s) => (
      { kind: "postaja", s, vlak: stationsByName.has(s.n) }))
    : [];
  // S številko človek išče linijo ali vlak ("25", "IC 502"), z besedo kraj.
  return (/\d/.test(f) ? [...out, ...postaje] : [...postaje, ...out]).slice(0, 12);
}

function findRowHtml(m) {
  if (m.kind === "postaja") {
    return `<button type="button" class="find-row" data-key="${escapeHtml(m.key)}">
      <span class="find-kind find-kind-postaja"></span>
      <span class="find-no">${escapeHtml(m.s.n)}</span>
      <span class="find-where">${m.vlak ? "železniška postaja" : "postajališče"}</span>
    </button>`;
  }
  const v = m.v;
  const delay = m.kind === "bus" ? v.delay_s : bestDelay(v).value;
  const kje = m.kind === "bus"
    ? (v.last_stop ? `pri ${v.last_stop}` : "GPS lega")
    : bestDelay(v).where;
  return `<button type="button" class="find-row" data-key="${escapeHtml(m.key)}">
      <span class="find-kind find-kind-${m.kind}"></span>
      <span class="find-no">${escapeHtml(agencyPrefix(v))}${escapeHtml(v.train_no)}</span>
      <span class="find-where">${escapeHtml(kje || "")}</span>
      <span class="find-delay" style="color:${delayColor(delay)}">${delayText(delay, true)}</span>
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
    m.key = m.kind === "postaja" ? `p:${m.s.n}`
      : m.kind === "bus" ? `b:${m.v.trip_id || m.v.train_no}`
      : `t:${m.v.trip_id || m.v.train_no}`;
  }
  findListEl.innerHTML = found.length
    ? found.map(findRowHtml).join("")
    : `<div class="find-empty">Ni postaje s tem imenom in ne vozila, ki bi bilo
         zdaj na poti. Vlaki brez meritve in avtobusi brez GPS na zemljevidu ne
         obstajajo.</div>`;
  findListEl.__found = found;
}

function pocistiTraso() {
  for (const id of ["k-trasa", "k-trasa-skica", "k-trasa-postaje"]) nastaviVir(id, PRAZNO);
}

// Trasa izbrane vožnje po cesti oziroma progi (GTFS `shapes.txt`) in njena
// postajališča. Traso rišemo za VSE prevoznike -- uvoz jo hrani v `shape`,
// 2 897 oblik in 10,3 MB, kar je proti bazi enkraten strošek, ki ne raste.
// Kadar je iz kakršnega koli razloga ni, ostane črta skozi postajališča;
// ta ni pot po cesti in videti mora drugače (črtkano).
let trasaSt = 0;

async function drawStops(trainNo, tripId) {
  const st = ++trasaSt;                // hitra druga izbira ne sme dobiti prve trase
  pocistiTraso();
  let trasa = null;
  if (tripId) {
    try {
      const r = await fetch(`/api/trip/${encodeURIComponent(tripId)}/shape`);
      if (r.ok) trasa = (await r.json()).points;
    } catch (err) {
      /* brez trase narišemo postajališča */
    }
  }
  if (st !== trasaSt) return;
  // Kosi, ne tocke -- glej isto opombo v train.js. `trasa.length > 1` je
  // izlocalo 93 % vseh oblik.
  const kosi = (trasa || []).filter((k) => k && k.length > 1);
  if (kosi.length) nastaviVir("k-trasa", kosiVCrto(kosi));
  try {
    const q = tripId ? `?trip=${encodeURIComponent(tripId)}` : "";
    const res = await fetch(
      `/api/train/${encodeURIComponent(trainNo)}${q}`).then((r) => r.json());
    if (st !== trasaSt) return;
    const postaje = (res.timetable || []).filter((s) => s.lat != null && s.lon != null);
    if (!kosi.length && postaje.length > 1) {
      nastaviVir("k-trasa-skica", { type: "Feature", properties: {}, geometry: {
        type: "LineString", coordinates: postaje.map((s) => [s.lon, s.lat]) } });
    }
    nastaviVir("k-trasa-postaje", tocke(postaje));
  } catch (err) {
    /* brez postajališč je trasa še vedno uporabna */
  }
}

// Postaja iz iskalnika: obroč na njej in povezava na odhodno tablo -- to je
// naslednje vprašanje, ko jo človek najde. Mestno postajališče rabi ulico
// (z16), železniška postaja kraj okrog sebe (z14).
function pokaziPostajo(m) {
  const { s, vlak } = m;
  const tabla = `${vlak ? "/app/train" : "/app/bus"}?station=${encodeURIComponent(s.n)}`;
  map.easeTo({ center: [s.lon, s.lat], zoom: Math.max(map.getZoom(), (vlak ? 14 : 16) - LZ) });
  nastaviVir("k-najdena", tocke([{ name: s.n, lat: s.lat, lon: s.lon }]));
  if (najdenaOkno) najdenaOkno.remove();
  najdenaOkno = new maplibregl.Popup({ offset: 12 })
    .setLngLat([s.lon, s.lat])
    .setHTML(`<div class="tt-title">${escapeHtml(s.n)}</div>
      <a class="najdena-tabla" href="${tabla}">odhodi s te postaje ›</a>`)
    .addTo(map);
}

function focusVehicle(key) {
  selectedKey = key;
  const found = findListEl.__found || [];
  const m = found.find((x) => x.key === key);
  if (!m) return;
  for (const b of findListEl.querySelectorAll(".find-row")) {
    b.classList.toggle("is-on", b.dataset.key === key);
  }
  if (m.kind === "postaja") {
    pokaziPostajo(m);
    setSheet(false);
    return;
  }
  if (m.kind === "bus") {
    map.easeTo({ center: [m.v.lon, m.v.lat], zoom: Math.max(map.getZoom(), 14 - LZ) });
    odpriKartico(m.v);
  } else {
    const where = bestDelay(m.v).where;
    const st = m.v.reported_lat != null
      ? { lat: m.v.reported_lat, lon: m.v.reported_lon }
      : stationsByName.get(m.v.last_stop);
    if (st) map.easeTo({ center: [st.lon, st.lat], zoom: Math.max(map.getZoom(), 11 - LZ) });
    const mk = stationMarkers.get(where);
    if (mk && vklop.train && !mk.getPopup().isOpen()) mk.togglePopup();
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
  trasaSt += 1;
  pocistiTraso();
  nastaviVir("k-najdena", PRAZNO);
  if (najdenaOkno) { najdenaOkno.remove(); najdenaOkno = null; }
  renderFind();
  findEl.focus();
});

// ---------- glava in poll ----------

// Napake NE pogoltne. Ritem jih prezre (`pollLiveTiho`), gumb "osvezi" pa
// mora povedati, da odgovora ni bilo -- tiha napaka je natanko tisto, zaradi
// cesar clovek ne ve, ali stran se tece.
async function pollLive() {
  liveTrains = await fetch("/api/live?network=zeleznica").then((r) => r.json());
  document.getElementById("n-train").textContent = liveTrains.length;
  renderTrains(liveTrains);
  vlakiPrispeli = true;
  prilagodiPogledVozilom();
  if (findEl.value.trim()) renderFind();
}

function pollLiveTiho() {
  return pollLive().catch((err) => {
    console.error("/api/live ni uspel", err);
    refreshFeedDot();
  });
}

// Trase se nalozijo SELE, ko jih kdo prizge, in nato osvezujejo z legami --
// pol megabajta za plast, ki je privzeto ugasnjena, ne sme na zicu vsakic.
let routesLoaded = false;

async function loadRoutes() {
  if (!vklop.routes) return;
  try {
    const list = await fetch("/api/shapes/live").then((r) => r.json());
    nastaviVir("k-vse-trase", { type: "FeatureCollection",
      features: list.map((r) => kosiVCrto(r.points, { network: r.network })) });
    routesLoaded = true;
    const el = document.getElementById("n-routes");
    if (el) el.textContent = list.length;
  } catch (err) {
    console.warn("tras ni bilo mogoce naloziti", err);
  }
}

function onVehicles(list) {
  liveBuses = list;
  // Stevec na prevoznika. Vrstica "drugi" se pokaze samo, ce kdo tam res je --
  // sicer je prazna izbira, ki nicesar ne pojasni.
  const poAgenciji = { "1118": 0, "1123": 0, "1119": 0, "1121": 0, drugi: 0 };
  for (const v of liveBuses) poAgenciji[busGroup(v)] += 1;
  const stevec = { "n-lpp": "1118", "n-arriva": "1123",
                   "n-nomago": "1119", "n-apms": "1121" };
  for (const [id, ag] of Object.entries(stevec)) {
    const el = document.getElementById(id);
    if (el) el.textContent = poAgenciji[ag];
  }
  const drugiEl = document.getElementById("n-bus-other");
  if (drugiEl) drugiEl.textContent = poAgenciji.drugi;
  const drugiRow = document.getElementById("row-bus-other");
  if (drugiRow) drugiRow.hidden = poAgenciji.drugi === 0;
  renderBuses(liveBuses);
  vozilaPrispela = true;
  prilagodiPogledVozilom();
  if (findEl.value.trim()) renderFind();
}

// Spodnja plosca na telefonu. Zaprta se odpre na dotik gumba; iskanje jo
// odpre samo (kdor tipka, jo rabi odprto), izbira vozila pa jo zapre, ker je
// naslednje, kar clovek hoce videti, zemljevid.
const sheetBtn = document.getElementById("sheet-toggle");
function setSheet(on) {
  document.body.classList.toggle("sheet-open", on);
  if (sheetBtn) sheetBtn.setAttribute("aria-expanded", String(on));
  // Polja NE fokusiramo sami: na telefonu bi se dvignila tipkovnica in
  // pokrila prav plosco, ki se je pravkar odprla.
}
if (sheetBtn) sheetBtn.addEventListener("click", () => setSheet(true));
const sheetClose = document.getElementById("sheet-close");
if (sheetClose) sheetClose.addEventListener("click", () => setSheet(false));

initLayers();
// Nase plasti gredo na zemljevid, ko je slog tu; `load` bi cakal se na vse
// ploscice podlage in na pocasni zvezi vozila zadrzal za sekunde.
map.once("style.load", async () => {
  dodajSloje();
  slojiDodani = true;
  uveljavi();
  await dodajAvtobuse();
  await loadStatic();
  pollLiveTiho();
  setInterval(pollLiveTiho, POLL_MS);
  // Lega avtobusov ima svoj ritem: feed jo osvežuje na ~30 s, zamude pa se
  // spreminjajo redkeje.
  vozilaPoll = pollVehicles("/api/vehicles", onVehicles);
  loadRoutes();
  setInterval(loadRoutes, 60000);   // trase se spreminjajo pocasneje od leg
});
