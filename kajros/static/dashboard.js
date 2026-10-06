// Živi zemljevid -- edini pogled, ki ga vlaki in avtobusi delita. Skupne
// funkcije so v common.js. Feed na strežniku osvežuje collector.py na
// config.POLL_SECONDS (privzeto 30 s); ta vrednost ni izpostavljena prek
// API-ja, zato je tu ločena kopija privzetka.
const POLL_MS = 30000;

// ---------- zemljevid ----------
//
// Ta zemljevid je MapLibre sam, brez Leafleta (22. 9. 2026). Leaflet nagiba
// ne pozna: ovoj `leaflet-maplibre-gl` je drzal MapLibrovo kamero v
// Leafletovi ravnini. Nagib od blizu in stavbe v 3D sta mogoca samo, ce
// kamera pripada MapLibru.
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

// Podatki gredo na pot takoj, med nalaganjem MapLibra, ne sele ko je slog
// tu. Prej so cakali drug na drugega -- slog, postaje, proge, vlaki, avtobusi,
// po vrsti -- in vozila so se na telefonu pokazala sekunde za podlago.
const zgodaj = {
  postaje: fetch("/api/stations?network=zeleznica").then(jsonOk),
  proge: fetch("/api/network.geojson").then(jsonOk),
  vlaki: fetch("/api/live?network=zeleznica").then(jsonOk),
  vozila: fetch("/api/vehicles"),
};
// Obljuba, ki je nihce ne pocaka, ob napaki ne sme v konzolo kot neujeta;
// napako javi tisti, ki jo prebere.
for (const o of Object.values(zgodaj)) o.catch(() => {});

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
// Vozilo, s katerim je clovek prisel iz okna voznje ("na velik zemljevid").
// Brez tega se je zemljevid odprl na legi avtobusa, plast njegovega
// prevoznika pa je bila lahko ugasnjena -- avtobusa, po katerega je prisel,
// tam ni bilo.
let urlTrip = URLQ.get("trip");
// Vlaki in avtobusi pridejo v ločenih odgovorih; dokler nista oba tu,
// odsotnost vozila iz naslova ne pomeni, da ga ni.
const nalozeno = { vlaki: false, avtobusi: false };

// Brez WebGL2 se modul tu ustavi: vse spodaj je zemljevid. Obljuba, ki se ne
// izpolni nikoli, je edini nacin, da ES modul neha brez napake v konzoli.
if (!maplibregl) await new Promise(() => {});
vklop["3d"] = layerPref("3d", true);

// Pogled se ne premika sam. Do 26. 9. 2026 se je po prihodu vozil prilagodil
// njihovemu okvirju in zemljevid je skocil sekundo ali dve po tem, ko ga je
// clovek ze gledal ("precej neprofesionalno"). Zdaj velja od prvega izrisa:
// pogled iz naslova, sicer zadnji pogled na tej napravi (kot zemljevidi v
// telefonu), sicer cela Slovenija.
const POGLED = "kajros:map-pogled";
const SLOVENIJA = [[13.38, 45.42], [16.61, 46.88]];

function shranjenPogled() {
  try {
    const p = JSON.parse(localStorage.getItem(POGLED) || "null");
    return p && [p.lat, p.lon, p.z].every(Number.isFinite) ? p : null;
  } catch (e) {
    return null;
  }
}

const zacetni = HAS_START ? { lat: startLat, lon: startLon, z: startZ } : shranjenPogled();
const zacetniZoom = zacetni ? zacetni.z - LZ : 0;
let map;
try {
  map = new maplibregl.Map({
    container: "map",
    style: SLOG,
    ...(zacetni
      ? { center: [zacetni.lon, zacetni.lat], zoom: zacetniZoom, pitch: nagib(zacetniZoom) }
      : { bounds: SLOVENIJA, fitBoundsOptions: { padding: 12 } }),
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
  try {
    localStorage.setItem(POGLED, JSON.stringify(
      { lat: +c.lat.toFixed(5), lon: +c.lng.toFixed(5), z: Math.round(lz() * 100) / 100 }));
  } catch (e) {
    /* zasebno okno: zemljevid se odpre cez Slovenijo */
  }
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

// Pot izbranega vozila je od blizu siroka kot to, po cemer vozi: avtobus
// 7,5 m (dva pasova; cesta v podlagi 6-11 m), vlak 3,2 m (en tir s pragovi,
// sosednji tir je 4-5 m stran). Prevozeno je sivo (`ZA_INK`, common.js).
const CESTA_M = 7.5;
const TIR_M = 3.2;

// Trase vseh vozil so v barvi prevoznika, kot njegova vozila; ob izbiri
// stopijo v ozadje, sicer se izbrana pot med njimi izgubi.
const VSE_TRASE_OPACITY = 0.42;


// Sirina zavisi od vozila, izraz s priblizkom pa mora biti na vrhu -- zato
// se ob izbiri vozila zamenja cel izraz (`narisiTraso`), ne vrednost v njem.
function trasaSirina(vlak, obroba = false) {
  const m = (vlak ? TIR_M : CESTA_M) + (obroba ? 1.2 : 0);
  return sirinaM(m, obroba ? [[10, 6], [15, 6.5]] : [[10, 3], [15, 3.5]]);
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

  for (const id of ["k-proge", "k-vse-trase", "k-postaje", "k-postajalisca", "k-izbrano", "k-trasa",
                    "k-zapore", "k-trasa-skica", "k-trasa-postaje", "k-najdena", "k-jaz",
                    "k-avtobusi"]) {
    map.addSource(id, { type: "geojson", data: PRAZNO });
  }

  // Vrstni red plasti je vrstni red risanja: proge in postaje spodaj, vozila
  // zgoraj. Brez tega vlak izgine pod progo, po kateri vozi.
  //
  // **Črte na tleh so pod stavbami** (`na tleh`), tocke in vozila nad njimi.
  // Nad stavbami je bila trasa v nagibu narisana cez hiso, za katero lezi
  // ulica; od blizu, ko je siroka kot cesta, je to videti kot pas cez streho.
  const naTleh = STAVBE_3D;
  // Od blizu podlaga nariše tire sama, vsakega posebej, nasa proga pa je ena
  // crta po enem od njih -- na postaji z desetimi tiri trdi, da vlak vozi po
  // tistem. Zato od Leafletovega z16 pobledi in pri z17,5 izgine; pot
  // izbranega vlaka pokaze `k-trasa`.
  const bledi = (dalec, blizu) => ["interpolate", ["linear"], ["zoom"], 14, dalec, 15, blizu, 16.5, 0];
  map.addLayer({ id: "k-proge-obroba", type: "line", source: "k-proge", layout: OKROGLO,
                 paint: { "line-color": "#11141a", "line-width": 5.5,
                          "line-opacity": bledi(0.9, 0.25) } }, naTleh);
  map.addLayer({ id: "k-proge", type: "line", source: "k-proge", layout: OKROGLO,
                 paint: { "line-color": PROGA, "line-width": 2, "line-opacity": bledi(1, 0.5) } },
               naTleh);
  // Trase vseh vozil: od blizu 2,5 m, tanjse od trase izbranega vozila.
  map.addLayer({ id: "k-vse-trase", type: "line", source: "k-vse-trase", layout: OKROGLO,
                 paint: { "line-color": ["coalesce", ["get", "barva"], PROGA],
                          "line-width": sirinaM(2.5, [[10, 1.2], [15, 1.6]]),
                          "line-opacity": VSE_TRASE_OPACITY } }, naTleh);
  // Pika brez imena ne pove nicesar; trajna oznaka pri 267 postajah
  // zakrije progo. Zato ime ob dotiku. Polmer 3,4 namesto 2,4: pika
  // 2,4 px je manjsa od prsta in je ni mogoce zadeti. Od blizu raste, da
  // ob cesti, siroki 50 px, ni pikica.
  const polmer = (px) => ["interpolate", ["linear"], ["zoom"], 15, px, 18, px * 2];
  map.addLayer({ id: "k-postaje", type: "circle", source: "k-postaje",
                 paint: { "circle-radius": polmer(3.4), "circle-color": "#8b95a4",
                          "circle-pitch-alignment": "map" } });
  // Postajališče je pika v barvi prevoznika (več prevoznikov: `SKUPNA_INK`).
  // Od blizu jo zamenja nadstrešek ob cesti ali znak na drogu -- pika ostane
  // nevidna pod njima, ker je ona tista, ki jo zadene prst (`zadetek`).
  map.addLayer({ id: "k-postajalisca", type: "circle", source: "k-postajalisca",
                 minzoom: BUSSTOP_MIN_Z - LZ, filter: ["==", ["get", "postaja"], 0],
                 paint: { "circle-radius": polmer(3.2), "circle-color": ["get", "barva"],
                          "circle-opacity": PIKA_POD_3D, "circle-stroke-opacity": PIKA_POD_3D,
                          "circle-stroke-color": "#0f1115", "circle-stroke-width": 1,
                          "circle-pitch-alignment": "map" } });
  map.addSource("k-postajalisca-nadstreski", { type: "geojson", data: PRAZNO });
  slojiPostajalisc(map, { vir: "k-postajalisca", nadstresek: "k-nadstresek",
                          postaja: "k-postaje-avtobusne", znak: "k-postajalisca-znak" });
  // Pot izbranega vozila: naprej oranžno (`IZBRANA_INK`), prevozeno sivo (`del`).
  // Siroka kot vozni pas in pod stavbami -- od blizu pokrije cesto, po kateri
  // vozilo pelje, in ne lebdi nad njo.
  map.addLayer({ id: "k-trasa-obroba", type: "line", source: "k-trasa", layout: OKROGLO,
                 paint: { "line-color": "#0f1115", "line-width": trasaSirina(false, true),
                          "line-opacity": 0.75 } }, naTleh);
  map.addLayer({ id: "k-trasa", type: "line", source: "k-trasa", layout: OKROGLO,
                 paint: { "line-color": ["case", ["==", ["get", "del"], "za"], ZA_INK, ["get", "barva"]],
                          "line-width": trasaSirina(false),
                          "line-opacity": ["case", ["==", ["get", "del"], "za"], 0.55, 0.9] } },
               naTleh);
  // Zapore tira (`/api/zapore`): rumena ovir, črtkana, nad progo in nad
  // potjo izbranega vlaka -- zapora na njegovi poti je prav tisto, kar mora
  // potnik videti. Še vedno na tleh: vlaki (DOM in 3D), avtobusi in pike
  // postaj so nad njo, vlak ob zapori se pod črto ne skrije. Debelejša, ko
  // velja zdaj; končana bledi, ker je danes še vedno lahko vzrok zamude.
  const zdajZap = ["get", "velja_zdaj"];
  map.addLayer({ id: "k-zapore-obroba", type: "line", source: "k-zapore",
                 layout: { "line-join": "round" },
                 paint: { "line-color": "#0f1115",
                          "line-width": ["case", zdajZap, 8, 5.5],
                          "line-opacity": ["case", ["==", ["get", "stanje"], "koncano"], 0.45, 0.8] } },
               naTleh);
  map.addLayer({ id: "k-zapore", type: "line", source: "k-zapore",
                 layout: { "line-join": "round" },
                 paint: { "line-color": OVIRA_INK,
                          "line-width": ["case", zdajZap, 4.5, 2.5],
                          "line-dasharray": [1.4, 1.1],
                          "line-opacity": ["case", ["==", ["get", "stanje"], "koncano"], 0.5, 1] } },
               naTleh);
  // Crta skozi postajalisca ni pot po cesti in mora biti videti drugace.
  map.addLayer({ id: "k-trasa-skica", type: "line", source: "k-trasa-skica",
                 paint: { "line-color": IZBRANA_INK, "line-width": 2.5, "line-opacity": 0.7,
                          "line-dasharray": [2, 2] } }, naTleh);
  map.addLayer({ id: "k-trasa-postaje", type: "circle", source: "k-trasa-postaje",
                 paint: { "circle-radius": polmer(3.6), "circle-color": ["coalesce", ["get", "barva"], IZBRANA_INK],
                          "circle-stroke-color": "#0f1115", "circle-stroke-width": 1.4,
                          "circle-pitch-alignment": "map" } });
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

async function loadStatic() {
  try {
    // Samo železniške postaje: avtobusnih je nekaj tisoč in mreža prog bi
    // izginila pod postajališči.
    const stations = await zgodaj.postaje;
    stationsByName = new Map(stations.map((s) => [s.name, s]));
    nastaviVir("k-postaje", tocke(stations.filter((s) => s.lat != null)));
  } catch (err) {
    console.error("postaj ni bilo mogoče naložiti", err);
  }

  try {
    nastaviVir("k-proge", await zgodaj.proge);
  } catch (err) {
    console.error("mreže ni bilo mogoče naložiti", err);
  }
}

// Nadstreške dobijo samo postajališča v sliki in pas okrog nje, kot modeli.
function posodobiNadstreske() {
  if (!map.getSource("k-postajalisca-nadstreski")) return;
  const z = map.getZoom();
  if (!busStops || !vklop.busstops || !vklop["3d"] || z < NADSTRESKI_OD) {
    nastaviVir("k-postajalisca-nadstreski", PRAZNO);
    return;
  }
  const b = map.getBounds();
  const dx = (b.getEast() - b.getWest()) / 2, dy = (b.getNorth() - b.getSouth()) / 2;
  const k = nadstresekK(z);
  const features = [];
  for (const s of busStops) {
    if (s.smer == null || s.postaja) continue;
    if (s.lon < b.getWest() - dx || s.lon > b.getEast() + dx
        || s.lat < b.getSouth() - dy || s.lat > b.getNorth() + dy) continue;
    features.push(...nadstresekKosi(s, k));
  }
  nastaviVir("k-postajalisca-nadstreski", { type: "FeatureCollection", features });
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
    const v = t.delay_s;
    return v != null && v > acc ? v : acc;
  }, -Infinity);
}

// Kje narisati vlak: kjer ga vidita potnika na njem, sicer na postaji, kjer
// po voznem redu in zamudi ta hip stoji, sicer na zadnji postaji z meritvijo.
// Potnikova lega je edina prava lega vlaka, ki jo imamo (`deljenje.py`), a
// samo, kadar se ujemata vsaj dva: en sam je lahko že izstopil in čaka na
// peronu, vlak pa bi stal tam z njim (odločil David, 1. 10. 2026; isto
// pravilo ima okno vožnje). Postanek je sklep (`api._na_postaji`), a boljši
// od prejšnje postaje, na kateri je vlak prej obstal ves postanek.
// Postaje iz prevoznikovega poročila tu ni: to je postaja, KAMOR vlak pelje
// (`api._dodaj_porocila`), do 5. 10. 2026 je stal tam pred prihodom.
const naPotnikovi = (t) => !!(t.potnik && t.potnik.soglasje && t.potnik.lat != null);

function trainPlace(t) {
  if (naPotnikovi(t)) {
    return { key: `potnik:${t.trip_id}`, name: "lega po poročilu potnikov",
             station: { lat: t.potnik.lat, lon: t.potnik.lon } };
  }
  if (t.na_postaji) {
    return { key: `stoji:${t.na_postaji.ime}`, name: t.na_postaji.ime,
             station: { lat: t.na_postaji.lat, lon: t.na_postaji.lon } };
  }
  return { key: t.last_stop, name: t.last_stop, station: stationsByName.get(t.last_stop) };
}

function groupByStation(trains) {
  // Več vlakov stoji na isti postaji -- en marker na postajo, sicer se
  // markerji in oznake v vozliščih (Ljubljana, Zidani Most) prekrivajo.
  const groups = new Map();
  for (const t of trains) {
    const { key, name, station } = trainPlace(t);
    if (!station) continue;
    let g = groups.get(key);
    if (!g) {
      g = { name, station, trains: [], potnik: key.startsWith("potnik:"),
            stoji: key.startsWith("stoji:") };
      groups.set(key, g);
    }
    g.trains.push(t);
  }
  for (const g of groups.values()) {
    g.trains.sort((a, b) => (b.delay_s ?? -1) - (a.delay_s ?? -1));
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
  // `data-trip`: kartica vlaka v oblačku postaje se izbere z dotikom in
  // pobarva svojo pot (`oznaciIzbrano`).
  const izbor = o.trip ? ` data-trip="${escapeHtml(o.trip)}" data-no="${escapeHtml(o.no)}"` : "";
  const on = o.trip && izbrana && izbrana.trip === o.trip ? " is-on" : "";
  return `<div class="veh-card${on}"${izbor}>
      <div class="veh-head">
        <span class="veh-no">${escapeHtml(o.no)}</span>${o.badge || ""}
        <button type="button" class="veh-min" aria-label="Skrči ali razširi kartico"></button>
        <span class="veh-headsign">${escapeHtml(o.headsign || "")}</span>
      </div>
      <div class="veh-rows">${rows}</div>
      ${o.href ? `<a class="veh-open" href="${o.href}" target="_blank" rel="noopener">
        Odpri stran o vozilu →</a>` : ""}
    </div>`;
}

// Kartica prekriva traso, po kateri vozilo pelje -- prav tisto, zaradi česar
// je bilo vozilo kliknjeno (3. 10. 2026, prijava). Zato je prosojna, premakne
// se z vlekom glave in skrči na glavo. Poslušalci so na zunanjem elementu
// oblačka: MapLibre ob vsakem `setHTML` (vsakih 10 s z novo lego) znova ustvari
// `.maplibregl-popup-content`, in kar bi viselo tam, bi izginilo sredi vleka.
// Premik je v `--px`/`--py`, ne v `transform` oblačka: tega nastavlja MapLibre
// sam, ob vsakem premiku vozila.
let karticaSkrcena = false;    // velja za naslednjo odprto kartico

function omogociPremik(oblacek) {
  const el = oblacek.getElement();
  if (!el || el.__premik) return;
  el.__premik = true;
  el.classList.toggle("je-skrcena", karticaSkrcena);
  let x = 0, y = 0, vlek = null, vlecen = false;
  el.addEventListener("pointerdown", (e) => {
    if (e.button > 0 || !e.target.closest(".veh-head, .popup-station")
        || e.target.closest("button")) return;
    vlek = { x0: e.clientX, y0: e.clientY, x, y };
    vlecen = false;
    el.setPointerCapture(e.pointerId);
    e.stopPropagation();       // zemljevid pod kartico se ne sme premikati
  });
  el.addEventListener("pointermove", (e) => {
    if (!vlek) return;
    const dx = e.clientX - vlek.x0, dy = e.clientY - vlek.y0;
    // Prag, da navaden dotik glave ni vlek: kartica vlaka se z dotikom izbere.
    if (!vlecen && Math.hypot(dx, dy) < 5) return;
    vlecen = true;
    x = vlek.x + dx; y = vlek.y + dy;
    el.style.setProperty("--px", `${x}px`);
    el.style.setProperty("--py", `${y}px`);
    el.classList.add("je-premaknjena");     // konica kazala na vozilo ne velja več
  });
  const konec = () => { vlek = null; };
  el.addEventListener("pointerup", konec);
  el.addEventListener("pointercancel", konec);
  // Klik po vleku ni klik: sicer bi spustitev prsta na kartici vlaka izbrala
  // njegovo pot.
  el.addEventListener("click", (e) => {
    if (vlecen) { vlecen = false; e.stopPropagation(); e.preventDefault(); return; }
    if (e.target.closest(".veh-min")) {
      karticaSkrcena = el.classList.toggle("je-skrcena");
      e.stopPropagation();
    }
  }, true);
}

function tripHref(trainNo, tripId, serviceDate, network) {
  const q = new URLSearchParams();
  if (serviceDate) q.set("date", serviceDate);
  if (tripId) q.set("trip", tripId);
  const pot = network === "avtobus" ? "/app/bus/" : "/app/train/";
  return `${pot}${encodeURIComponent(trainNo)}${q.toString() ? `?${q}` : ""}`;
}

function trainCardHtml(t) {
  const p = t.potnik;
  // Z enim poročevalcem sta feed in potnik vsak v svoji vrstici; potnikova
  // lega je lahko pol postaje naprej od zadnje meritve.
  const potnik = p && p.lat != null ? [
    [p.n > 1 ? `${potnikov(p.n)} na vlaku` : "potnik na vlaku",
     `${p.pri ? escapeHtml(`pri postaji ${p.pri}`) : p.med
       ? escapeHtml(`med postajama ${p.med[0]} in ${p.med[1]}`) : "—"}${p.zamuda
       ? ` · <span style="color:${delayColor(p.zamuda)}">${escapeHtml(delayText(p.zamuda))}</span>` : ""}`],
  ] : [];
  return vehCardHtml({
    no: t.train_no, badge: modeBadgeHtml(t.mode), headsign: t.headsign, trip: t.trip_id,
    href: tripHref(t.train_no, t.trip_id, t.service_date, "zeleznica"),
    // Kraj, zamuda in ura iz naše meritve; prevoznikovo poročilo je napoved
    // za postajo pred vlakom, zato svoja vrstica z imenom postaje in uro.
    // Prej je bila zamuda iz poročila, ura pa iz meritve -- „Borovnica,
    // poročal prevoznik ob 20:58“, ob 20:58 pa je bil vlak v Postojni.
    rows: [
      ["zamuda", delayText(t.delay_s), delayColor(t.delay_s)],
      ["zadnja meritev", escapeHtml(t.last_stop || "—")],
      ["izmerjeno", t.measured_at ? `ob ${hhmm(t.measured_at)}` : "—"],
      ...(t.reported_at_station ? [[
        "napoved prevoznika",
        `→ ${escapeHtml(t.reported_at_station)} · <span style="color:${delayColor(t.reported_delay_s)}">${
          escapeHtml(delayText(t.reported_delay_s))}</span> · ob ${
          hhmm(Date.now() - t.reported_age_s * 1000)}`]] : []),
      ...potnik,
    ],
  });
}

function busCardHtml(v) {
  // Zamuda in kraj morata biti iz istega vira: "+15 min" brez postaje, kjer
  // je bila izmerjena, je stevilka brez pomena, ce je vozilo od takrat ze
  // dalec naprej.
  // Brez `trip_id` je vožnja, ki je vozni red ne pozna (LPP ob zapori): ni
  // ure, od katere bi merili zamudo, in ne strani, ki bi jo lahko odprli.
  const rows = !v.trip_id
    ? [["zamuda", "vožnje ni v voznem redu"]]
    : v.delay_s == null
    ? [["zamuda", "ni meritve"]]
    : [["zamuda", delayText(v.delay_s), delayColor(v.delay_s)],
       ["zadnja meritev", escapeHtml(v.last_stop || "—")]];
  return vehCardHtml({
    no: agencyPrefix(v) + v.train_no, badge: "", headsign: v.headsign,
    href: v.trip_id ? tripHref(v.train_no, v.trip_id, v.service_date, "avtobus") : null,
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
  const koliko = g.trains.length === 1 ? "1 vlak" : `${g.trains.length} vlakov`;
  // Ploščica vlaka prekrije piko postaje pod sabo; v vozlišču (Ljubljana,
  // Zidani Most) stoji tam skoraj ves dan. Brez tega gumba do odhodov s
  // postaje z dotikom ne bi prišel.
  const postaja = !g.potnik && stationsByName.has(g.name)
    ? `<button type="button" class="post-odpri" data-postaja="${escapeHtml(g.name)}">
        odhodi s postaje ${escapeHtml(g.name)} ›</button>` : "";
  return `
    <div class="popup-station">${escapeHtml(g.name)}</div>
    <div class="popup-note">${g.potnik
      ? `${potnikov(g.trains[0].potnik.n)} na vlaku ${deliGlagol(g.trains[0].potnik.n)} lego`
      : g.stoji ? `po voznem redu in zamudi zdaj stoji tu — ${koliko}`
      : `zadnja postaja z meritvijo — ${koliko}`}</div>
    <div class="popup-list">${g.trains.map(trainCardHtml).join("")}</div>${postaja}`;
}


function trainSize(z) {
  if (z >= 17) return 38;
  if (z >= 13) return 30;
  if (z >= 11) return 24;
  if (z >= 9) return 19;
  return 15;
}

// Vlak je znak na postaji, ne vozilo: oranzna ploscica z vlakom od spredaj.
// Feed za vlake GPS nima in marker stoji na postaji (zadnji z meritvijo ali
// tisti, kjer po voznem redu zdaj stoji), zato ne sme biti videti kot
// avtobus, ki je vozilo na izmerjeni legi. Zavrnjeno (4. 10. 2026): vlak od
// zgoraj v smeri proge -- "zgleda kot bus"; obroc okoli njega -- spominjal
// je na obroc izbranega avtobusa.
function trainSvg(n, s) {
  return `<svg width="${s}" height="${s}" viewBox="0 0 24 24" overflow="visible">
      <rect x="1" y="1" width="22" height="22" rx="6"
            fill="${TRAIN_INK}" stroke="#0f1115" stroke-width="1.4"/>
      <g transform="translate(12 12) scale(0.82) translate(-12 -12)">
        <rect x="6.5" y="3.5" width="11" height="13" rx="3.2" fill="#0f1115"/>
        <rect x="8.2" y="5.6" width="7.6" height="4.4" rx="1.2" fill="${TRAIN_INK}"/>
        <circle cx="9.3" cy="13.4" r="1.05" fill="${TRAIN_INK}"/>
        <circle cx="14.7" cy="13.4" r="1.05" fill="${TRAIN_INK}"/>
        <path d="M9 17.2 7.4 20.3M15 17.2l1.6 3.1M8 19.1h8"
              stroke="#0f1115" stroke-width="1.5" stroke-linecap="round"/>
      </g>
      ${n > 1 ? `<circle cx="21" cy="3" r="4.2" fill="#0f1115"/>
        <text x="21" y="5.3" text-anchor="middle" font-size="6"
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
  // En vlak na postaji: oblaček takoj pobarva njegovo pot. Več vlakov: pot
  // se izbere z dotikom kartice -- ugibati, katerega je človek hotel, ni naše.
  m.getPopup().on("open", () => {
    omogociPremik(m.getPopup());
    const vlaki = m.__g ? m.__g.trains : [];
    if (vlaki.length === 1) izberi(vlaki[0], true);
  });
  m.getPopup().on("close", () => {
    const vlaki = m.__g ? m.__g.trains : [];
    if (izbrana && izbrana.vlak && vlaki.some((t) => t.trip_id === izbrana.trip)) pocistiTraso();
  });
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
    marker.__g = g;
  }
  for (const [name, marker] of stationMarkers) {
    if (!groups.has(name)) {
      marker.remove();
      stationMarkers.delete(name);
    }
  }
  posodobiVlake3D();
  requestAnimationFrame(declutterLabels);
}

// ---------- vlaki v 3D ----------
// Model samo tam, kjer vlak RES je: stoji na postaji (po voznem redu in
// zamudi) ali potnik na njem deli lego. Vlak med postajama ostane ploščica
// tudi od blizu -- model na zadnji postaji z meritvijo bi trdil, da
// vlak stoji tam, kjer ga že davno ni. Avtobus je v 3D na GPS, vlak mora
// imeti isto pravilo. Meja priblizka je ista kot pri avtobusih.

let vlaki3d = null;
let vlaki3dSeznam = [];        // kar plast ta hip rise, za dotik

const vidniVlaki3D = () => !!vlaki3d && vklop["3d"] && vklop.train
  && map.getZoom() >= AVTOBUS_3D_OD;

function dodajVlake3D() {
  vlaki3d = plast3D({
    id: "k-vlaki-3d",
    modeli: vlakModeli(TRAIN_INK),
    vidna: vidniVlaki3D,
    povecava: vlakPovecava,
  });
  map.addLayer(vlaki3d.plast);
  posodobiVlake3D();
}

const smerVlaka = (t) => (naPotnikovi(t) ? t.potnik.smer
  : t.na_postaji && t.na_postaji.smer) ?? 0;

// Vlak stoji na svoji legi: potnikovi ali na postaji, na pripeti trasi svoje
// vožnje (`api._na_postaji`), ki leži na tiru OSM -- ne na točki postaje,
// ki je pogosto sredi postajnega poslopja.
const legaVlaka = (t, g) => (naPotnikovi(t) ? t.potnik
  : g.stoji && t.na_postaji ? t.na_postaji : g.station);

// Vlak s tirom s table SŽ, ki ga OSM pozna po številki, stoji na njem
// (`na_postaji.tir`, `api._na_svoj_tir`). Ostali na isti postaji stojijo drug
// ob drugem, en tir narazen. Odmik je v okviru modela (levo od smeri
// voznje), zato vlak v nasprotni smeri dobi nasprotni predznak -- sicer bi
// stala na istem tiru.
function posodobiVlake3D() {
  if (!vlaki3d) return;
  const vidni = vidniVlaki3D();
  vlaki3dSeznam = [];
  for (const [kljuc, m] of stationMarkers) {
    const g = m.__g;
    const v3d = g && (g.stoji || g.potnik);
    // Ikona nad modelom bi ga prekrila (element je nad platnom); oznaka ostane.
    m.__icon.style.visibility = vidni && v3d ? "hidden" : "";
    if (!v3d) continue;
    const brezTira = g.trains.filter((t) => !(g.stoji && t.na_postaji && t.na_postaji.tir));
    const ref = smerVlaka(brezTira[0] || g.trains[0]);
    for (const t of g.trains) {
      const lega = legaVlaka(t, g);
      const smer = smerVlaka(t);
      const i = brezTira.indexOf(t);
      let odmik = i < 0 ? 0 : (i - (brezTira.length - 1) / 2) * VLAK_TIR_M;
      const razlika = (((smer - ref) % 360) + 360) % 360;
      if (razlika > 90 && razlika < 270) odmik = -odmik;
      vlaki3dSeznam.push({ lon: lega.lon, lat: lega.lat, smer, model: vlakModel(t), kljuc, odmik });
    }
  }
  vlaki3d.nastavi(vlaki3dSeznam);
}
// Ob vsakem koraku priblizevanja, ne sele ob koncu: sicer bi cez mejo
// model in ikona do konca gibanja stala drug na drugem.
map.on("zoom", posodobiVlake3D);

// Vlak v 3D pod prstom: odpre kartico postaje, isto kot ikona. Polmer je
// pol garniture, a vsaj za prst.
function zadetekVlak3D(p) {
  if (!vidniVlaki3D()) return null;
  const r = Math.max(18, (30 * vlakPovecava(map.getZoom())) / mppZdaj());
  let naj = null, najd = r;
  for (const a of vlaki3dSeznam) {
    const q = map.project([a.lon, a.lat]);
    const d = Math.hypot(q.x - p.x, q.y - p.y);
    if (d < najd) { najd = d; naj = a; }
  }
  return naj && { layer: { id: "k-vlaki-3d" }, properties: { kljuc: naj.kljuc },
                  geometry: { type: "Point", coordinates: [naj.lon, naj.lat] } };
}

// Velikost ikone vlaka je odvisna od zooma, marker pa se sam ne skalira.
let zoomTimer = null;
map.on("zoomend", () => {
  clearTimeout(zoomTimer);
  zoomTimer = setTimeout(() => renderTrains(liveTrains), 60);
});

// ---------- avtobusi: prava lega iz GPS ----------
// Vlaki v feedu nimajo GPS, avtobusi ga imajo. To sta dve različni stvari na
// isti sliki in ju je treba ločiti tudi na pogled: vlak je ploščica na postaji,
// avtobus je oblika vozila na izmerjeni legi.

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
const busKey = (v) => v.trip_id
  || (v.vehicle_id ? `v:${v.vehicle_id}` : `${v.train_no}:${v.lat},${v.lon}`);

// Kje avtobus narisati: na pripeti trasi svoje vožnje, na desnem pasu in v
// smeri ceste (`cesta` iz /api/vehicles, `pripni.na_cesto`), sicer na legi
// GPS. GPS je od osi ceste v mediani 3,8 m; od blizu, ko je cesta široka
// 50 px, je bil avtobus narisan ob cesti ali čeznjo. Meritev ostane v
// `lat`/`lon` -- kartica pove starost lege, ne risbe.
function legaVozila(v) {
  return v.cesta ? { lat: v.cesta[0], lon: v.cesta[1], smer: v.cesta[2] }
    : { lat: v.lat, lon: v.lon, smer: v.bearing ?? 0 };
}

// Velikost sledi približevanju. Pri pogledu na vso Slovenijo je vozil do sto
// in majhna oblika je edina, ki se ne slepi; ko kdo približa na eno ulico,
// pa je iskal prav to vozilo in mora biti veliko -- vektorska podlaga ostane
// ostra do z19, zato naj bo vozilo takrat priblizno tako veliko kot ulica.
// Pari [Leafletov zoom, px]; vmes velikost tece zvezno.
const BUS_VELIKOST = [[9, 15], [10, 20], [12, 26], [14, 34], [17, 44]];
const BUS_SLIKA = 44;          // px, v katerih je slika narisana (in 2x za ostrino)

// Avtobus od zgoraj: zaobljeno telo, svetlo vetrobransko steklo spredaj,
// temno zadnje steklo in zarezi za kolesi. Puščica je bila premalo -- pri
// približku je bila videti kot pika in se od vlaka ni ločila. Steklo spredaj
// je svetlo (4. 10. 2026): temno se pri 15–26 px ni videlo in smeri vožnje ni
// bilo mogoče razbrati. Zgibni LPP v dveh delih je bil zmeden (en dan, 4. 10.),
// zato je telo enodelno za vse.
function busSvg(size, moving, ink) {
  const o = moving ? 1 : 0.5;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24">
      <g>
        <rect x="7.5" y="2.5" width="9" height="19" rx="3.2"
              fill="${ink}" fill-opacity="${o}"
              stroke="#0f1115" stroke-width="1.5"/>
        <path d="M9.1 5.6 Q12 4.3 14.9 5.6 L14.9 7.5 Q12 6.7 9.1 7.5 Z"
              fill="#e9f4ff" fill-opacity="0.95"/>
        <rect x="9.6" y="19.1" width="4.8" height="0.9" rx="0.4" fill="#0f1115" fill-opacity="0.7"/>
        <rect x="6.4" y="6.6" width="1.6" height="3.2" rx="0.7" fill="#0f1115" fill-opacity="0.75"/>
        <rect x="16" y="6.6" width="1.6" height="3.2" rx="0.7" fill="#0f1115" fill-opacity="0.75"/>
        <rect x="6.4" y="15" width="1.6" height="3.2" rx="0.7" fill="#0f1115" fill-opacity="0.75"/>
        <rect x="16" y="15" width="1.6" height="3.2" rx="0.7" fill="#0f1115" fill-opacity="0.75"/>
      </g>
    </svg>`;
}

// Polmer obroča izbranega vozila: pol ikone in malo, od blizu pa dovolj za
// model v 3D (pri MapLibrovem z15 je LPP s povečavo ~27 px od sredine).
function obrocIzbranega(z3d) {
  const ikona = BUS_VELIKOST.map(([z, px]) => [z - LZ, px * 0.5 + 3]);
  if (!z3d) return ["interpolate", ["linear"], ["zoom"], ...ikona.flat()];
  return ["interpolate", ["linear"], ["zoom"],
    ...ikona.filter(([z]) => z < AVTO_3D_OD - 0.5).flat(),
    AVTO_3D_OD - 0.01, 24, AVTO_3D_OD, 30, AVTO_3D_OD + 1, 42, AVTO_3D_OD + 2, 60,
    AVTO_3D_OD + 3, 85];
}

const busIkona = (ink, moving) => `bus-${ink.slice(1)}-${moving ? "vozi" : "stoji"}`;
// Številka linije ob avtobusu od blizu -- samo pri LPP, kjer je to res
// številka, ki jo potnik vidi na postajališču. Pri medkrajevnih je v feedu
// številka vožnje (A6325), ki je ni nikjer na vozilu.
const OZNAKA_OD = 14;          // Leafletov zoom

// Od blizu je avtobus model v 3D (`vozila3d.js`), od dalec ikona. Meja in
// velikost modela sta tam, ker ju rabi tudi okno voznje.
const AVTOBUS_3D_OD = AVTO_3D_OD;
let avtobusi3d = null;
let vozila3d = [];             // kar plast 3D ta hip rise, za dotik

const povecava3D = avtoPovecava;
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
  // Izbrano vozilo ima obroč v barvi izbrane poti: med dvajsetimi enakimi
  // ikonami na cesti sicer ni jasno, čigava je oranžna pot. Tanek obroč s
  // sijem, ne debel kolobar -- ta je bil štorast (4. 10. 2026). Od blizu
  // raste z modelom v 3D (`avtoPovecava`), da ga obkroži, ne prereže.
  const obroc = obrocIzbranega(vklop["3d"]);
  map.addLayer({
    id: "k-izbrano-sij", type: "circle", source: "k-izbrano",
    paint: {
      "circle-radius": obroc, "circle-color": IZBRANA_INK, "circle-opacity": 0.22,
      "circle-blur": 0.55, "circle-pitch-alignment": "map",
    },
  });
  map.addLayer({
    id: "k-izbrano", type: "circle", source: "k-izbrano",
    paint: {
      "circle-radius": obroc, "circle-color": "rgba(0,0,0,0)",
      "circle-stroke-color": IZBRANA_INK, "circle-stroke-width": 1.6,
      "circle-stroke-opacity": 0.95, "circle-pitch-alignment": "map",
    },
  });
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
      // Številka se lahko skrije, kadar bi prekrila drugo; vozilo ne.
      "text-field": ["step", ["zoom"], "", OZNAKA_OD - LZ, ["get", "st"]],
      "text-font": ["Noto Sans Bold"],
      "text-size": 11.5,
      "text-anchor": "left",
      "text-offset": [1.1, 0],
      "text-optional": true,
    },
    paint: {
      "text-color": "#e7eaf0",
      "text-halo-color": "#0f1115",
      "text-halo-width": 1.6,
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
  posodobiVlake3D();
  posodobiNadstreske();
  if (!avtobusi3d) return;
  const vidni = new Set(LAYERS.filter((s) => s.ag && vklop[s.key]).map((s) => s.ag));
  const b = map.getBounds();
  const dx = (b.getEast() - b.getWest()) / 2;
  const dy = (b.getNorth() - b.getSouth()) / 2;
  vozila3d = [];
  for (const v of busByKey.values()) {
    const model = busGroup(v);
    if (!vidni.has(model)) continue;
    const l = legaVozila(v);
    if (l.lon < b.getWest() - dx || l.lon > b.getEast() + dx
        || l.lat < b.getSouth() - dy || l.lat > b.getNorth() + dy) continue;
    vozila3d.push({ lon: l.lon, lat: l.lat, smer: l.smer, model, kljuc: busKey(v) });
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
    const l = legaVozila(v);
    features.push({
      type: "Feature",
      geometry: { type: "Point", coordinates: [l.lon, l.lat] },
      properties: {
        kljuc, ag: busGroup(v), mesto: v.agency === "lpp",
        smer: l.smer,
        ikona: busIkona(busInk(v), (v.speed_kmh || 0) >= 3),
        st: busGroup(v) === "1118" ? v.train_no : "",
      },
    });
  }
  nastaviVir("k-avtobusi", { type: "FeatureCollection", features });
  oznaciIzbranoVozilo();
  posodobi3D();
  // Odprta kartica gre z vozilom; ce ga ni vec, gre tudi ona.
  if (kartica && kartica.__kljuc) {
    const v = busByKey.get(kartica.__kljuc);
    if (v) {
      const l = legaVozila(v);
      kartica.setLngLat([l.lon, l.lat]).setHTML(busCardHtml(v));
    } else {
      kartica.remove();
    }
  }
}

// ---------- dotik in lebdenje ----------
//
// Ime postaje se pokaze na dotik in po petih sekundah odide (`NAME_MS` v
// common.js); brez gumba za zapiranje, ker bi bil na telefonu manjsi od
// prsta. Na napravi z misko se pokaze ze ob lebdenju, kot prej.

const IMENA = ["k-postaje", "k-postajalisca", "k-postaje-avtobusne", "k-postajalisca-znak",
               "k-trasa-postaje", "k-jaz"];
// Dotik zadene, kar je v tem polmeru: pika postaje meri 7 px, prst dosti vec.
const DOTIK_PX = 12;

let kartica = null;            // odprta kartica avtobusa
let imeOkno = null;
let imeCas = null;
let najdenaOkno = null;

// Najblizje, kar je pod prstom: vozilo pred postajo, postaja pred postajo.
function zadetek(p) {
  const v3d = zadetek3D(p) || zadetekVlak3D(p);
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
  const l = legaVozila(v);
  kartica = new maplibregl.Popup({ maxWidth: "280px", offset: 14 + nad })
    .setLngLat([l.lon, l.lat]).setHTML(busCardHtml(v)).addTo(map);
  kartica.__kljuc = busKey(v);
  omogociPremik(kartica);
  const trip = v.trip_id;
  // Pot gre s kartico: zaprta kartica, pobarvana cesta brez razlage ostane
  // uganka.
  kartica.on("close", () => {
    kartica = null;
    if (izbrana && !izbrana.vlak && izbrana.trip === trip) pocistiTraso();
  });
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
  // Pike in vozila imajo prednost pred črto zapore: vlak ob zapori mora ostati
  // dosegljiv.
  const zap = f ? [] : zaporePod(e.point);
  if (zap.length) {
    if (lebdi) lebdi.remove();
    odpriZaporo(zap, e.lngLat);
    return;
  }
  // Dotik praznega zemljevida zapre spodnjo plosco -- to je najbolj
  // pricakovana gesta in deluje tudi, ce kdo rocaja ne opazi.
  if (!f) { setSheet(false); return; }
  if (lebdi) lebdi.remove();
  if (f.layer.id === "k-avtobusi") {
    const v = busByKey.get(f.properties.kljuc);
    if (v) {
      odpriKartico(v);
      izberi(v, false);
    }
  } else if (f.layer.id === "k-vlaki-3d") {
    const m = stationMarkers.get(f.properties.kljuc);
    if (m && !m.getPopup().isOpen()) m.togglePopup();
  } else if (f.layer.id === "k-najdena") {
    if (najdena && najdena.vlak) odpriPostajo(najdena.ime, najdena.ll);
    else if (najdenaOkno) najdenaOkno.addTo(map);
  } else if (f.layer.id === "k-postaje") {
    // Železniška postaja dobi oblaček z odhodi; postajališča in pike na poti
    // izbranega vozila ostanejo pri imenu za pet sekund.
    clearTimeout(imeCas);
    if (imeOkno) imeOkno.remove();
    odpriPostajo(f.properties.ime, f.geometry.coordinates);
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
    const f = zadetek3D(e.point) || zadetekVlak3D(e.point)
      || map.queryRenderedFeatures(e.point, { layers: sloji })[0];
    const zap = f ? [] : zaporePod(e.point);
    map.getCanvas().style.cursor = f || zap.length ? "pointer" : "";
    if (zap.length) {
      lebdi.setText(`zapora tira ${zap.map((q) => q.odsek).join(", ")}`)
        .setLngLat(e.lngLat).addTo(map);
      return;
    }
    if (!f) { lebdi.remove(); return; }
    const v = f.layer.id === "k-avtobusi" && busByKey.get(f.properties.kljuc);
    const m = f.layer.id === "k-vlaki-3d" && stationMarkers.get(f.properties.kljuc);
    if (v) lebdi.setHTML(busTooltipHtml(v));
    else if (m) lebdi.setHTML(groupLabelHtml(m.__g));
    else lebdi.setText(f.properties.ime);
    lebdi.setLngLat(f.geometry.coordinates).addTo(map);
  });
  map.on("mouseout", () => lebdi.remove());
}

// Dotik kartice vlaka v oblačku postaje izbere njegovo pot. Povezava na
// stran vozila ostane povezava.
document.addEventListener("click", (ev) => {
  const p = ev.target.closest(".maplibregl-popup .post-odpri");
  const st = p && stationsByName.get(p.dataset.postaja);
  if (st) {
    odpriPostajo(st.name, [st.lon, st.lat]);
    return;
  }
  const k = ev.target.closest(".maplibregl-popup .veh-card[data-trip]");
  if (!k || ev.target.closest("a")) return;
  const t = liveTrains.find((x) => x.trip_id === k.dataset.trip);
  if (t) izberi(t, true);
});

// ---------- železniška postaja in zapore tira ----------
//
// Dotik železniške postaje je do 5. 10. 2026 pokazal samo ime za pet sekund,
// ista postaja iz iskalnika pa oblaček s povezavo na tablo -- prijava „na
// zemljevidu nimava možnosti za železniške postaje in za ovire“. Zdaj obe poti
// odpreta isti oblaček: naslednji odhodi po ISTIH pravilih kot tabla
// (`razvrstiTablo`, `nepotrjen`, `delayText`, `tirHtml`), zapore tira na
// postaji in pot do cele table. Odhodi se vprašajo šele ob dotiku.

//: Toliko odhodov v oblačku; več jih je na tabli.
const POSTAJA_ODHODOV = 3;

let postajaOkno = null;        // odprt oblaček železniške postaje
let zaporaOkno = null;         // odprt oblaček zapore
let najdena = null;            // postaja iz iskalnika: {ime, ll, vlak}

// Zapore dneva. Stanje („velja zdaj“) računa strežnik ob vsaki strežbi, zato
// se plast osveži na minuto; oblaček postaje jih vzame od tu tudi, kadar je
// plast ugasnjena.
let zapore = null;
let zaporeCas = 0;
const ZAPORE_MS = 60000;

async function naloziZapore(sveze = false) {
  if (!sveze && zapore && Date.now() - zaporeCas < ZAPORE_MS) return zapore;
  zapore = await fetch("/api/zapore").then(jsonOk);
  zaporeCas = Date.now();
  nastaviVir("k-zapore", zapore);
  const n = new Set(zapore.features.map((f) => f.properties.alert_id)).size;
  const el = document.getElementById("n-zapore");
  if (el) el.textContent = n || "";
  return zapore;
}

function naloziZaporeTiho() {
  if (!vklop.zapore) return;
  naloziZapore(true).catch((err) => console.warn("zapor ni bilo mogoče naložiti", err));
}

// Kdaj velja, pove `kdajZapore` v common.js: ista beseda kot na strani ovir.
function zaporaVrsticaHtml(p) {
  return `<div class="zap-vrsta${p.velja_zdaj ? " is-zdaj" : ""}">
      <span class="zap-odsek">zapora tira ${escapeHtml(p.odsek)}</span>
      <span class="zap-kdaj">${escapeHtml(kdajZapore(p))}</span>
    </div>`;
}

// Ena vrstica odhoda, z istimi besedami in barvami kot tabla: ura po
// pričakovani uri, vozni red prečrtan, kadar se razlikujeta za minuto ali več
// (`boardRowHtml`); nadomestni prevoz „po voznem redu“, ker feed zanj ne
// poroča; nepotrjen odhod napol prosojen, z isto besedo.
function odhodHtml(r, nowMs) {
  const pricakovano = r.expected || r.sched;
  const morda = nepotrjen(new Date(pricakovano).getTime(), r.nepotrjen_do, nowMs);
  const off = r.delay_s != null && Math.abs(r.delay_s) >= 60;
  // Tabla je `network=zeleznica`: avtobus na njej je nadomestni prevoz.
  const nadomestni = isBus(r.mode);
  const zamuda = r.zamuda
    ? `<b class="odh-zam" style="color:${delayColor(r.zamuda)}">${escapeHtml(delayText(r.zamuda))}</b>`
    : nadomestni ? '<b class="odh-zam odh-vr">po voznem redu</b>'
    // Brez meritve za ta dan: kako je bilo doslej, z besedo kot na tabli --
    // tanjša številka, ker to ni napoved za danes.
    : r.typical ? `<b class="odh-zam odh-obicajno" style="color:${delayColor(r.typical.median_s)}">${
      escapeHtml(delayText(r.typical.median_s))}</b>`
    : '<b class="odh-zam odh-vr">brez podatka</b>';
  const meta = [
    off ? `<s>${hhmm(r.sched)}</s>` : "",
    tirHtml(r.tir, r.tir_prej),
    r.zamuda && r.delay_kind ? escapeHtml(r.delay_kind) : "",
    !r.zamuda && !nadomestni && r.typical ? `običajno · ${pluralRuns(r.typical.n)}` : "",
    r.do_s != null ? `<span class="opozorilo">lahko do ${delayLabel(r.do_s)} min</span>` : "",
    morda ? nepotrjenHtml(pricakovano, false) : "",
  ].filter(Boolean).join(" ");
  return `<a class="odh${morda ? " is-unconfirmed" : ""}"
       href="${tripHref(r.train_no, r.trip_id, r.service_date, "zeleznica")}">
      <span class="odh-ura"${off ? ` style="color:${delayColor(r.zamuda)}"` : ""}>${hhmm(pricakovano)}</span>
      <span class="odh-kam"><span class="odh-no">${escapeHtml(r.train_no)}</span>${
        modeBadgeHtml(r.mode)} → ${escapeHtml(r.towards || r.destination || "")}</span>
      ${zamuda}
      ${meta ? `<span class="odh-meta">${meta}</span>` : ""}
    </a>`;
}

function postajaHtml(ime, tabla, zap, napaka) {
  let telo;
  if (napaka) {
    telo = '<div class="popup-note">Odhodov ni bilo mogoče naložiti.</div>';
  } else if (!tabla) {
    telo = '<div class="popup-note">nalagam odhode …</div>';
  } else {
    const nowMs = Date.now();
    const { morda, ahead } = razvrstiTablo(tabla.board || [], nowMs);
    const vrste = [...morda, ...ahead].slice(0, POSTAJA_ODHODOV);
    telo = vrste.length
      ? `<div class="odh-seznam">${vrste.map((r) => odhodHtml(r, nowMs)).join("")}</div>`
      : `<div class="popup-note">V naslednjih ${Math.round(tabla.window_min / 60)} urah ni odhodov.</div>`;
  }
  const naPostaji = (zap ? zap.features : []).map((f) => f.properties)
    .filter((p) => p.postaje.includes(ime));
  return `<div class="veh-card postaja-card">
      <div class="veh-head">
        <span class="popup-station">${escapeHtml(ime)}</span>
        <button type="button" class="veh-min" aria-label="Skrči ali razširi kartico"></button>
        <span class="veh-headsign">naslednji odhodi</span>
      </div>
      <div class="veh-rows">${telo}${naPostaji.map(zaporaVrsticaHtml).join("")}</div>
      <a class="veh-open" href="/app/train?station=${encodeURIComponent(ime)}">cela odhodna tabla ›</a>
    </div>`;
}

async function osveziPostajo() {
  const okno = postajaOkno;
  if (!okno) return;
  let tabla = null, zap = null, napaka = false;
  try {
    [tabla, zap] = await Promise.all([
      fetch(`/api/departures?station=${encodeURIComponent(okno.__ime)}&network=zeleznica`)
        .then(jsonOk),
      // Brez zapor je oblaček še vedno odgovor; napaka tu ne sme skriti odhodov.
      naloziZapore().catch(() => null),
    ]);
  } catch (err) {
    console.warn("odhodov ni bilo mogoče naložiti", err);
    napaka = true;
  }
  if (okno !== postajaOkno) return;    // medtem zaprt ali zamenjan
  okno.setHTML(postajaHtml(okno.__ime, tabla, zap, napaka));
}

// Oblaček železniške postaje. Ena pot za dotik pike in izbiro v iskalniku.
function odpriPostajo(ime, ll) {
  zapriOblacke();
  const okno = new maplibregl.Popup({ maxWidth: "300px", offset: 10 })
    .setLngLat(ll).setHTML(postajaHtml(ime, null, zapore, false)).addTo(map);
  okno.__ime = ime;
  postajaOkno = okno;
  omogociPremik(okno);
  okno.on("close", () => { if (postajaOkno === okno) postajaOkno = null; });
  osveziPostajo();
}

// Zapore pod prstom: črta je tanka, zato isti polmer kot pri pikah.
function zaporePod(p) {
  if (!vklop.zapore || !map.getLayer("k-zapore")) return [];
  const r = DOTIK_PX;
  const videne = new Set();
  return map.queryRenderedFeatures([[p.x - r, p.y - r], [p.x + r, p.y + r]],
                                   { layers: ["k-zapore"] })
    .map((f) => f.properties)
    .filter((q) => {
      const k = `${q.alert_id}|${q.odsek}`;
      if (videne.has(k)) return false;
      videne.add(k);
      return true;
    });
}

function odpriZaporo(lastnosti, ll) {
  zapriOblacke();
  // MapLibre lastnosti vrne kot niz, kadar so seznam ali objekt.
  const vse = lastnosti.map((q) => ({
    ...q, okna: typeof q.okna === "string" ? JSON.parse(q.okna) : q.okna }));
  const okno = new maplibregl.Popup({ maxWidth: "300px", offset: 6 })
    .setLngLat(ll)
    .setHTML(`<div class="veh-card zapora-card">
        <div class="veh-head">
          <span class="popup-station">Zapora enega tira</span>
          <button type="button" class="veh-min" aria-label="Skrči ali razširi kartico"></button>
        </div>
        <div class="veh-rows">
          ${vse.map((q) => `<div class="zap-vrsta${q.velja_zdaj ? " is-zdaj" : ""}">
              <span class="zap-odsek">odsek ${escapeHtml(q.odsek)}</span>
              <span class="zap-kdaj">${escapeHtml(kdajZapore(q))}</span>
            </div>`).join("")}
          <div class="popup-note">Vlak lahko tam čaka na križanje.</div>
        </div>
        <a class="veh-open" href="/app/ovire">vse ovire na progi ›</a>
      </div>`)
    .addTo(map);
  zaporaOkno = okno;
  omogociPremik(okno);
  okno.on("close", () => { if (zaporaOkno === okno) zaporaOkno = null; });
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
// metrov in pika brez njega trdi natancnost, ki je nima (isto kot `pkJaz`).
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

// Kar se rise sele od blizje, mora to povedati -- sicer je videti, kot da ga
// ni. Avtobusi in postajalisca si delijo eno opombo, da se nad orodno
// vrstico ne kopicijo.
const stopNoteEl = document.getElementById("stop-note");
function opombaPriblizka() {
  if (!stopNoteEl) return;
  const z = lz();
  const skrito = [];
  if (LAYERS.some((s) => s.ag && vklop[s.key]) && z < AVTOBUSI_OD) skrito.push("Avtobusi");
  else if (vklop["avtobus-lpp"] && z < MESTNI_OD) skrito.push("Mestni avtobusi LPP");
  const postaje = vklop.busstops && busStops && z < BUSSTOP_MIN_Z;
  let text = "";
  if (postaje && !skrito.length) {
    text = "Postajališča se pokažejo, ko približaš — zdaj bi jih bilo "
      + "toliko, da bi zakrila proge.";
  } else if (skrito.length) {
    if (postaje) skrito.push("postajališča");
    text = `${skrito.join(" in ")} se pokažejo, ko približaš.`;
  }
  stopNoteEl.textContent = text;
  stopNoteEl.hidden = !text;
}

async function loadBusStops() {
  if (busStops || busStopsLoading) return;
  busStopsLoading = true;
  try {
    busStops = (await fetch("/api/stations?network=avtobus").then(jsonOk))
      .filter((s) => s.lat != null);
    nastaviVir("k-postajalisca", tockePostajalisc(busStops));
    posodobiNadstreske();
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
  opombaPriblizka();
  if (!vklop.busstops || !busStops) return;
  if (lz() < BUSSTOP_MIN_Z) {
    if (el) el.textContent = "";
    return;
  }
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
// posamezno vozilo ni dalo najti. Zato je vsak prevoznik svoje potrditveno
// polje. `ag` je skupina v `busGroup()`.
//
// Do 1. 10. 2026 so bili avtobusi privzeto ugasnjeni in zemljevid se je
// odprl kot železniški. Prijava s Facebooka: „za vlak lahko spremljaš, kje
// je, pri medmestnih busih pa ne“ -- čeprav ima GPS 90 % njihovih voženj.
// Zdaj so prižgani, kašo pa rešuje približek: avtobus se riše šele tam, kjer
// se ga da ločiti od drugih (`AVTOBUSI_OD`, `MESTNI_OD`), pod tem opomba pove,
// zakaj ga ni.
//
// Ključi shrambe so novi (`avtobus-*`, prej `bus-*`): stara koda je ob vsakem
// odprtju zapisala stanje VSEH stikal, zato je imel vsak, ki je zemljevid
// kdaj odprl, shranjeno „ugasnjeno“, čeprav ni ničesar izbral. Zdaj se zapiše
// samo, kar človek sam prestavi -- privzetek tako doseže vse, ki niso izbirali.
//
// Trase vseh vozil na poti so svoja plast in privzeto ugasnjene: gost snop
// crt cez vso Ljubljano odgovarja na vprasanje "kod vozijo linije", ne na
// "kje je moj avtobus" -- in drugo je razlog za obisk te strani.
//
// Dodatna imena krajev (vasi, cetrti, vode) so privzeto ugasnjena: pri
// velikem priblizku bi tekmovala z vozili. Katera so, pove `podlaga.json`.

// Od katerega (Leafletovega) približka se avtobusi rišejo. Izmerjeno na
// 48-urnem posnetku leg (28.–30. 9. 2026, vrh 970 vozil 30. 9. ob 14:50) kot
// delež vozil, ki jim je drugo vozilo bližje od pol ikone; mediana delavnika
// 6–20 h. Mestni LPP: z11 80 %, z12 61 %, z13 46 %. Vsi ostali: pogled cele
// Slovenije na telefonu (z7,5) 86 %, z8 77 %, z9 61 %, z10 54 %. Prag je pri
// obojih tam, kjer je gneča enaka (61 %) in kjer se na posnetku vozila
// ločijo; kar ostane, so avtobusi, ki stojijo na postajah -- pri z17 še
// vedno 11 %. Na namizju je cela Slovenija ~z9,3, zato so tam medkrajevni
// vidni že ob odprtju.
const AVTOBUSI_OD = 9;
const MESTNI_OD = 12;

const NADSTRESEK_SLOJI = ["tla", "steber", "stena", "streha"].map((d) => `k-nadstresek-${d}`);

const LAYERS = [
  { id: "lay-train", key: "train", def: true },
  { id: "lay-lpp", key: "avtobus-lpp", def: true, ag: "1118" },
  { id: "lay-arriva", key: "avtobus-arriva", def: true, ag: "1123" },
  { id: "lay-nomago", key: "avtobus-nomago", def: true, ag: "1119" },
  { id: "lay-apms", key: "avtobus-apms", def: true, ag: "1121" },
  { id: "lay-bus-other", key: "avtobus-drugi", def: true, ag: "drugi" },
  { id: "lay-net", key: "net", def: true, sloji: ["k-proge-obroba", "k-proge"] },
  { id: "lay-zapore", key: "zapore", def: true, sloji: ["k-zapore-obroba", "k-zapore"] },
  { id: "lay-routes", key: "routes", def: false, sloji: ["k-vse-trase"] },
  { id: "lay-stations", key: "stations", def: true, sloji: ["k-postaje"] },
  { id: "lay-busstops", key: "busstops", def: false,
    sloji: ["k-postajalisca", "k-postaje-avtobusne", "k-postajalisca-znak", ...NADSTRESEK_SLOJI] },
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
  // Brez 3D ni nadstreškov in znakov od blizu: pika ostane na vseh približkih.
  if (map.getLayer("k-postajalisca")) {
    for (const lastnost of ["circle-opacity", "circle-stroke-opacity"]) {
      map.setPaintProperty("k-postajalisca", lastnost, vklop["3d"] ? PIKA_POD_3D : 0.85);
    }
    vidnost("k-postajalisca-znak", vklop.busstops && vklop["3d"]);
  }
  if (map.getLayer("k-avtobusi")) {
    const ag = LAYERS.filter((s) => s.ag && vklop[s.key]).map((s) => s.ag);
    // Filter vidi celoštevilski MapLibrov zoom ploščice, zato sta praga cela.
    map.setFilter("k-avtobusi", ["all",
      ["in", ["get", "ag"], ["literal", ag]],
      [">=", ["zoom"], ["case", ["get", "mesto"], MESTNI_OD - LZ, AVTOBUSI_OD - LZ]]]);
    map.setLayerZoomRange("k-avtobusi", 0, vklop["3d"] ? AVTOBUS_3D_OD : 24);
    for (const id of ["k-izbrano", "k-izbrano-sij"]) {
      map.setPaintProperty(id, "circle-radius", obrocIzbranega(vklop["3d"]));
    }
  }
  posodobi3D();
  osveziPodlago();
  opombaPriblizka();
}

// `zapomni` samo ob človekovi izbiri: kar je stran nastavila sama (privzetek,
// vozilo iz naslova), ni izbira in ne sme prekriti poznejšega privzetka.
function setLayer(spec, on, zapomni = false) {
  vklop[spec.key] = on;
  const box = document.getElementById(spec.id);
  if (box) box.checked = on;
  if (zapomni) {
    try {
      localStorage.setItem(`kajros:map-${spec.key}`, on ? "1" : "0");
    } catch (err) {
      /* zaseben zavihek ni razlog, da stran ne dela */
    }
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
        setLayer(spec, box.checked, true);
        // Prvi vklop mora tudi kaj narisati -- plast je ob zagonu prazna.
        if (spec.key === "routes" && box.checked && !routesLoaded) loadRoutes();
        if (spec.key === "zapore" && box.checked) naloziZapore();
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
  const delay = v.delay_s;
  const kje = m.kind === "bus"
    ? (v.last_stop ? `pri ${v.last_stop}` : "GPS lega")
    : v.last_stop;
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
      : m.kind === "bus" ? `b:${busKey(m.v)}`
      : `t:${m.v.trip_id || m.v.train_no}`;
  }
  findListEl.innerHTML = found.length
    ? found.map(findRowHtml).join("")
    : `<div class="find-empty">Ni postaje s tem imenom in ne vozila, ki bi bilo
         zdaj na poti. Vlaki brez meritve in avtobusi brez GPS na zemljevidu ne
         obstajajo.</div>`;
  findListEl.__found = found;
}

// ---------- pot izbranega vozila ----------
//
// Klik na vozilo (ali izbira v iskalniku) pobarva pot, po kateri pelje:
// naprej oranžno (`IZBRANA_INK`), prevozeno sivo. Trasa je pripeta na ceste in tire
// OSM (`pripni.py`), zato se od blizu ujema s podlago, ne lezi ob njej.
// Trasa velja za VSE prevoznike -- uvoz jo hrani v `shape`, 2 897 oblik.
// Kadar je iz kakršnega koli razloga ni, ostane črta skozi postajališča;
// ta ni pot po cesti in videti mora drugače (črtkano).

let izbrana = null;            // {trip, vlak, barva, kosi, along}
let trasaSt = 0;               // hitra druga izbira ne sme dobiti prve trase

function pocistiTraso() {
  izbrana = null;
  trasaSt += 1;
  for (const id of ["k-trasa", "k-trasa-skica", "k-trasa-postaje", "k-izbrano"]) nastaviVir(id, PRAZNO);
  if (map.getLayer("k-vse-trase")) map.setPaintProperty("k-vse-trase", "line-opacity", VSE_TRASE_OPACITY);
  oznaciIzbrano();
}

// Kje je izbrano vozilo, tako kot je narisano: avtobus na cesti (ali GPS),
// vlak na postaji, kjer stoji ali je bil nazadnje izmerjen.
function legaIzbrane() {
  if (!izbrana) return null;
  if (izbrana.vlak) {
    const t = liveTrains.find((x) => x.trip_id === izbrana.trip);
    const st = t && trainPlace(t).station;
    return st ? [st.lat, st.lon] : null;
  }
  const v = liveBuses.find((x) => x.trip_id === izbrana.trip);
  if (!v || v.lat == null) return null;
  const l = legaVozila(v);
  return [l.lat, l.lon];
}

// Vozilo, ki je od svoje trase dlje od tega, ni na njej (pelje na začetek
// vožnje) -- takrat je vsa pot še pred njim.
const NA_TRASI_M = 300;

// Kje na trasi (kosi [[lat, lon], ...]) je točka. Kadar trasa gre dvakrat
// mimo istega mesta (krožna linija), med enako bližnjimi odseki vzamemo
// tistega, ki je najbliže prejšnji legi vzdolž trase -- vozilo ne skoči za
// pol vožnje naprej; brez prejšnje najzgodnejšega.
function naTrasi(kosi, lat, lon, prej) {
  const kx = 111320 * Math.cos((lat * Math.PI) / 180), ky = 110574;
  const kandidati = [];
  let vzdolz = 0, naj = Infinity;
  kosi.forEach((kos, i) => {
    for (let j = 0; j < kos.length - 1; j += 1) {
      const ax = (kos[j][1] - lon) * kx, ay = (kos[j][0] - lat) * ky;
      const bx = (kos[j + 1][1] - lon) * kx, by = (kos[j + 1][0] - lat) * ky;
      const vx = bx - ax, vy = by - ay;
      const l2 = vx * vx + vy * vy;
      const t = l2 === 0 ? 0 : Math.max(0, Math.min(1, -(ax * vx + ay * vy) / l2));
      const d = Math.hypot(ax + t * vx, ay + t * vy);
      const dol = Math.sqrt(l2);
      kandidati.push({ i, j, t, d, along: vzdolz + t * dol });
      naj = Math.min(naj, d);
      vzdolz += dol;
    }
  });
  const blizu = kandidati.filter((k) => k.d <= naj + 20);
  if (!blizu.length) return null;
  const merilo = prej == null ? (k) => k.along : (k) => Math.abs(k.along - prej);
  return blizu.reduce((a, b) => (merilo(b) < merilo(a) ? b : a));
}

// Trasa razrezana pri vozilu: [prevozeno, naprej].
function razrezi(kosi, k) {
  if (!k) return [[], kosi];
  const kos = kosi[k.i];
  const a = kos[k.j], b = kos[k.j + 1];
  const p = [a[0] + k.t * (b[0] - a[0]), a[1] + k.t * (b[1] - a[1])];
  return [[...kosi.slice(0, k.i), [...kos.slice(0, k.j + 1), p]],
          [[p, ...kos.slice(k.j + 1)], ...kosi.slice(k.i + 1)]];
}

// Obroč okrog izbranega vozila, na isti legi kot je narisano.
function oznaciIzbranoVozilo() {
  const l = izbrana && legaIzbrane();
  nastaviVir("k-izbrano", l ? { type: "Feature", properties: {},
    geometry: { type: "Point", coordinates: [l[1], l[0]] } } : PRAZNO);
}

function narisiTraso() {
  oznaciIzbranoVozilo();
  if (!izbrana || !izbrana.kosi) return;
  const lega = legaIzbrane();
  let k = lega && naTrasi(izbrana.kosi, lega[0], lega[1], izbrana.along);
  if (k && k.d > NA_TRASI_M) k = null;
  if (k) izbrana.along = k.along;
  const [za, naprej] = razrezi(izbrana.kosi, k);
  const lastnosti = { barva: izbrana.barva };
  nastaviVir("k-trasa", { type: "FeatureCollection", features: [
    kosiVCrto(za, { ...lastnosti, del: "za" }),
    kosiVCrto(naprej, { ...lastnosti, del: "naprej" }),
  ] });
}

// Kartica izbranega vlaka v oblačku postaje je obrobljena.
function oznaciIzbrano() {
  for (const el of document.querySelectorAll(".veh-card[data-trip]")) {
    el.classList.toggle("is-on", !!izbrana && el.dataset.trip === izbrana.trip);
  }
}

async function drawStops(trainNo, tripId, vlak = false, barva = IZBRANA_INK) {
  if (izbrana && izbrana.trip === tripId) {
    narisiTraso();
    return;
  }
  pocistiTraso();
  const st = trasaSt;
  izbrana = { trip: tripId, vlak, barva, kosi: null, along: null };
  oznaciIzbrano();
  oznaciIzbranoVozilo();
  map.setPaintProperty("k-vse-trase", "line-opacity", 0.15);
  map.setPaintProperty("k-trasa", "line-width", trasaSirina(vlak));
  map.setPaintProperty("k-trasa-obroba", "line-width", trasaSirina(vlak, true));
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
  if (kosi.length) {
    izbrana.kosi = kosi;
    narisiTraso();
  }
  try {
    const q = tripId ? `?trip=${encodeURIComponent(tripId)}` : "";
    const res = await fetch(
      `/api/train/${encodeURIComponent(trainNo)}${q}`).then(jsonOk);
    if (st !== trasaSt) return;
    const postaje = (res.timetable || []).filter((s) => s.lat != null && s.lon != null);
    if (!kosi.length && postaje.length > 1) {
      nastaviVir("k-trasa-skica", { type: "Feature", properties: {}, geometry: {
        type: "LineString", coordinates: postaje.map((s) => [s.lon, s.lat]) } });
    }
    const pike = tocke(postaje);
    for (const f of pike.features) f.properties.barva = barva;
    nastaviVir("k-trasa-postaje", pike);
  } catch (err) {
    /* brez postajališč je trasa še vedno uporabna */
  }
}

// Pot vozila iz seznama: oranžna, ne glede na vozilo (`IZBRANA_INK`).
function izberi(v, vlak) {
  // Vožnje brez `trip_id` vozni red ne pozna (LPP mimo voznega reda, glej
  // `lpp.na_tablo`): njenih postaj in trase ni, izbira s praznim `trip` pa bi
  // se ujela z vsakim drugim takim vozilom (`legaIzbrane`).
  if (!v.trip_id) { pocistiTraso(); return; }
  drawStops(v.train_no, v.trip_id, vlak, IZBRANA_INK);
}

// Postaja iz iskalnika: obroč na njej in odhodi -- to je naslednje
// vprašanje, ko jo človek najde. Železniška postaja dobi isti oblaček kot ob
// dotiku pike (`odpriPostajo`), postajališče povezavo na tablo. Mestno
// postajališče rabi ulico (z16), železniška postaja kraj okrog sebe (z14).
function pokaziPostajo(m) {
  const { s, vlak } = m;
  const ll = [s.lon, s.lat];
  map.easeTo({ center: ll, zoom: Math.max(map.getZoom(), (vlak ? 14 : 16) - LZ) });
  nastaviVir("k-najdena", tocke([{ name: s.n, lat: s.lat, lon: s.lon }]));
  najdena = { ime: s.n, ll, vlak };
  if (najdenaOkno) najdenaOkno.remove();
  if (vlak) {
    najdenaOkno = null;
    odpriPostajo(s.n, ll);
    return;
  }
  const tabla = `/app/bus?station=${encodeURIComponent(s.n)}`;
  najdenaOkno = new maplibregl.Popup({ offset: 12 })
    .setLngLat([s.lon, s.lat])
    .setHTML(`<div class="tt-title">${escapeHtml(s.n)}</div>
      <a class="najdena-tabla" href="${tabla}">odhodi s te postaje ›</a>`)
    .addTo(map);
}

// Izbira iz iskalnika ni klik na zemljevid, zato MapLibre odprtih oblačkov ne
// zapre sam: postaja iz iskalnika je pristala pod kartico prej izbranega
// vozila, drug čez drugega (5. 10. 2026). Nova izbira zapre prejšnje; trasa
// gre z njimi (`close` kartice in oblačka postaje).
function zapriOblacke() {
  if (kartica) kartica.remove();
  if (najdenaOkno) najdenaOkno.remove();
  if (postajaOkno) postajaOkno.remove();
  if (zaporaOkno) zaporaOkno.remove();
  for (const mk of stationMarkers.values()) {
    if (mk.getPopup().isOpen()) mk.togglePopup();
  }
}

function focusVehicle(key) {
  selectedKey = key;
  const found = findListEl.__found || [];
  const m = found.find((x) => x.key === key);
  if (!m) return;
  zapriOblacke();
  for (const b of findListEl.querySelectorAll(".find-row")) {
    b.classList.toggle("is-on", b.dataset.key === key);
  }
  if (m.kind === "postaja") {
    pokaziPostajo(m);
    setSheet(false);
    return;
  }
  if (m.kind === "bus") {
    const l = legaVozila(m.v);
    map.easeTo({ center: [l.lon, l.lat], zoom: Math.max(map.getZoom(), 14 - LZ) });
    odpriKartico(m.v);
  } else {
    const { key, station: st } = trainPlace(m.v);
    if (st) map.easeTo({ center: [st.lon, st.lat], zoom: Math.max(map.getZoom(), 11 - LZ) });
    const mk = stationMarkers.get(key);
    if (mk && vklop.train && !mk.getPopup().isOpen()) mk.togglePopup();
  }
  izberi(m.v, m.kind !== "bus");
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
  pocistiTraso();
  nastaviVir("k-najdena", PRAZNO);
  najdena = null;
  if (najdenaOkno) { najdenaOkno.remove(); najdenaOkno = null; }
  renderFind();
  findEl.focus();
});

// ---------- glava in poll ----------

// Napake NE pogoltne. Ritem jih prezre (`pollLiveTiho`), gumb "osvezi" pa
// mora povedati, da odgovora ni bilo -- tiha napaka je natanko tisto, zaradi
// cesar clovek ne ve, ali stran se tece.
async function pollLive() {
  // Prvi odgovor je ze na poti od zacetka strani (`zgodaj`).
  const prvi = zgodaj.vlaki;
  zgodaj.vlaki = null;
  liveTrains = await (prvi || fetch("/api/live?network=zeleznica").then(jsonOk));
  document.getElementById("n-train").textContent = liveTrains.length;
  renderTrains(liveTrains);
  if (izbrana && izbrana.vlak) narisiTraso();
  // Odprt oblaček postaje teče z zemljevidom: ura in zamude se premikajo.
  if (postajaOkno) osveziPostajo();
  if (findEl.value.trim()) renderFind();
  nalozeno.vlaki = true;
  pokaziVoziloIzNaslova();
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
    const list = await fetch("/api/shapes/live").then(jsonOk);
    nastaviVir("k-vse-trase", { type: "FeatureCollection",
      features: list.map((r) => kosiVCrto(r.points, {
        network: r.network,
        barva: r.network === "avtobus" ? busInk(r) : PROGA,
      })) });
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
  if (izbrana && !izbrana.vlak) narisiTraso();
  if (findEl.value.trim()) renderFind();
  nalozeno.avtobusi = true;
  pokaziVoziloIzNaslova();
}

// Vozilo iz naslova je človek gledal v oknu vožnje. Njegova plast se prižge
// tudi, če jo je sam ugasnil -- a samo za ta ogled, ne v shrambo -- in kartica
// se odpre, da je takoj jasno, katero vozilo je. Enkrat: naslov ga nato
// izgubi, sicer bi ga osvežitev strani odprla znova, ko ga morda ni več.
function pokaziVoziloIzNaslova() {
  if (!urlTrip) return;
  const v = liveBuses.find((x) => x.trip_id === urlTrip);
  const vlak = !v && liveTrains.find((x) => x.trip_id === urlTrip);
  if (!v && !vlak && !(nalozeno.vlaki && nalozeno.avtobusi)) return;
  urlTrip = null;
  const q = new URLSearchParams(location.search);
  q.delete("trip");
  history.replaceState(null, "", `?${q}`);
  if (vlak) {
    const spec = LAYERS.find((s) => s.key === "train");
    if (spec && !vklop.train) setLayer(spec, true);
    const { key, station: st } = trainPlace(vlak);
    if (st) map.easeTo({ center: [st.lon, st.lat] });
    const mk = stationMarkers.get(key);
    if (mk && !mk.getPopup().isOpen()) mk.togglePopup();
    izberi(vlak, true);
    return;
  }
  if (!v || v.lat == null) return;
  const spec = LAYERS.find((s) => s.ag === busGroup(v));
  if (spec && !vklop[spec.key]) setLayer(spec, true);
  odpriKartico(v);
  izberi(v, false);
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
  dodajVlake3D();
  await loadStatic();
  pollLiveTiho();
  setInterval(pollLiveTiho, POLL_MS);
  // Lega avtobusov ima svoj ritem: feed jo osvežuje na ~30 s, zamude pa se
  // spreminjajo redkeje.
  vozilaPoll = pollVehicles("/api/vehicles", onVehicles, zgodaj.vozila);
  loadRoutes();
  setInterval(loadRoutes, 60000);   // trase se spreminjajo pocasneje od leg
  naloziZaporeTiho();
  setInterval(naloziZaporeTiho, ZAPORE_MS);
});
