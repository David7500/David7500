/* Zemljevid obeh strani poti: seznama predlogov in poti po korakih.
 *
 * MapLibre sam, brez Leafleta, kot veliki zemljevid (22. 9. 2026): od blizu se
 * kamera nagne in stavbe se dvignejo -- in prav od blizu se po poti hodi.
 * Vodenje po pešpoti je kamera za hrbtom pešca; Leaflet je ne zna nagniti.
 *
 * Klasičen skript in ne modul: naslovi statike nosijo odtis vsebine (`s()`),
 * uvoz modula po relativnem imenu pa bi ga izgubil in service worker bi
 * stregel staro datoteko (ista past, kot jo opisuje `api._razlicica`).
 *
 * Brez WebGL2 zemljevida ni. Obe strani delata tudi brez njega -- seznam in
 * koraki so v plošči --, zato stran to pove in gre naprej.
 */

// MapLibrov zoom je za ena manjši od Leafletovega (512-pikselne ploščice).
// Meje na teh straneh so zapisane v Leafletovih enotah, kot na velikem
// zemljevidu; pretvorba je samo tu.
const PK_LZ = 1;

// Nagib sledi približku, isto kot na velikem zemljevidu: od daleč raven, od
// Leafletovega z15 se nagiba in pri z17,5 doseže 60°.
const PK_NAGIB_OD = 14;
const PK_NAGIB_CEZ = 2.5;
const PK_NAGIB_NAJVEC = 60;

// Hoja je modra in črtkana, vožnja oranžna in polna: potnik mora na prvi
// pogled videti, kje ga nese vozilo in kje njegove noge.
const PK_HOJA = "#2f7fff";
const PK_VOZNJA = "#f0934f";
const PK_PRAZNO = { type: "FeatureCollection", features: [] };

function pkNagib(z) {
  return PK_NAGIB_NAJVEC * Math.max(0, Math.min(1, (z - PK_NAGIB_OD) / PK_NAGIB_CEZ));
}

let pkKnjiznica = null;

// Slog MapLibra je v glavi predloge, ne dodan tu: zemljevid, ustvarjen pred
// njim, dobi napačno velikost platna.
function pkNaloziMapLibre() {
  if (!pkKnjiznica) pkKnjiznica = import(`${MAPLIBRE_POT}/maplibre-gl.mjs`);
  return pkKnjiznica;
}

/** Krog v metrih kot mnogokotnik [lon, lat]: v nagibu mora ležati na tleh. */
function pkKrog(lat, lon, m, n = 40) {
  const dLat = m / 111320;
  const dLon = m / (111320 * Math.cos(lat * Math.PI / 180));
  const pts = [];
  for (let i = 0; i <= n; i += 1) {
    const a = (i / n) * 2 * Math.PI;
    pts.push([lon + dLon * Math.cos(a), lat + dLat * Math.sin(a)]);
  }
  return pts;
}

/**
 * Zemljevid v elementu `el`: `{ map, ml }` ali `null`, kadar ga ni mogoče
 * narisati. Viri `k-pot` (črte), `k-tocke` (postajališča vstopa in izstopa) in
 * `k-jaz` (lastna lega) so dodani in prazni; start in cilj riše `pkKonca()`.
 *
 * `opts` rabi okno vožnje (`train.js`): `sredisce` [lat, lon] in `zoom` v
 * Leafletovih enotah, `dodatnaImena` in `sodelovanje` (geste, ki strani ne
 * ukradejo pomikanja -- zemljevid je tam element na strani, ne stran).
 */
async function pkUstvari(el, opts) {
  const { sredisce = [46.1, 14.6], zoom = 8, dodatnaImena = true,
          sodelovanje = false } = opts || {};
  if (!imaWebGL2()) return null;
  let ml;
  try {
    ml = await pkNaloziMapLibre();
  } catch (e) {
    console.warn("MapLibre se ni naložil:", e && e.message);
    return null;
  }
  const slog = document.querySelector('meta[name="kajros-podlaga"]')?.content
    || "/static/podlaga.json";
  let map;
  try {
    map = new ml.Map({
      container: el, style: slog,
      center: [sredisce[1], sredisce[0]], zoom: zoom - PK_LZ, maxZoom: 19 - PK_LZ,
      canvasContextAttributes: { antialias: true },
      // Nagib je lastnost približka, ne gesta -- isto kot na velikem
      // zemljevidu. Vrtenje ostane: pri vodenju je sever redko zgoraj.
      transformCameraUpdate: (t) => ({ pitch: pkNagib(t.zoom) }),
      pitchWithRotate: false, touchPitch: false,
      attributionControl: { compact: true },
      cooperativeGestures: sodelovanje,
      locale: {
        "CooperativeGesturesHandler.WindowsHelpText": "Ctrl + kolešček približa · ali razširi zemljevid",
        "CooperativeGesturesHandler.MacHelpText": "⌘ + kolešček približa · ali razširi zemljevid",
        "CooperativeGesturesHandler.MobileHelpText": "Zemljevid premakneš z dvema prstoma",
      },
    });
  } catch (e) {
    console.warn("zemljevida ni mogoče odpreti:", e && e.message);
    return null;
  }

  let izrisano = false;
  map.on("error", (e) => {
    // Opis ploščic pred prvim izrisom ni prišel (OpenFreeMap ni dosegljiv):
    // rezerva, kot na velikem zemljevidu. Napaka ene ploščice pozneje ni razlog.
    if (!izrisano && e.sourceId === "omt") pkEsri(map);
    else console.warn("zemljevid:", e && e.error && e.error.message);
  });
  await new Promise((ok) => map.once("load", ok));
  izrisano = true;

  // Stavbe od blizu, pod napisi -- sicer stavba pokrije ime ulice za sabo.
  const prviNapis = map.getLayersOrder().find((id) => map.getLayer(id).type === "symbol");
  if (map.getLayer("stavba")) {
    map.addLayer({
      id: "stavbe-3d", type: "fill-extrusion", source: "omt", "source-layer": "building",
      minzoom: PK_NAGIB_OD,
      paint: {
        "fill-extrusion-color": map.getPaintProperty("stavba", "fill-color"),
        "fill-extrusion-height": ["interpolate", ["linear"], ["zoom"],
          PK_NAGIB_OD, 0, PK_NAGIB_OD + 2, ["coalesce", ["get", "render_height"], 0]],
        "fill-extrusion-base": ["interpolate", ["linear"], ["zoom"],
          PK_NAGIB_OD, 0, PK_NAGIB_OD + 2, ["coalesce", ["get", "render_min_height"], 0]],
        "fill-extrusion-opacity": ["interpolate", ["linear"], ["zoom"],
          PK_NAGIB_OD, 0, PK_NAGIB_OD + 1, 0.85],
      },
    }, prviNapis);
  }
  // Dodatna imena krajev so tu prižgana, drugače kot na velikem zemljevidu:
  // tam tekmujejo z vozili, tu je vprašanje "kje je to".
  for (const id of dodatnaImena ? map.getLayersOrder() : []) {
    const l = map.getLayer(id);
    if (l.metadata && l.metadata["kajros:napisi"] === "dodatni") {
      map.setLayoutProperty(id, "visibility", "visible");
    }
  }

  for (const id of ["k-pot", "k-tocke", "k-jaz"]) {
    map.addSource(id, { type: "geojson", data: PK_PRAZNO });
  }
  const okroglo = { "line-join": "round", "line-cap": "round" };
  // Vožnja od blizu široka kot cesta (`sirinaM`): trasa je pripeta na OSM in
  // pokrije cesto, po kateri vozilo pelje, ne tanke črte ob njej.
  map.addLayer({ id: "k-voznja-obroba", type: "line", source: "k-pot", layout: okroglo,
                 filter: ["==", ["get", "vrsta"], "voznja"],
                 paint: { "line-color": "#0f1115", "line-width": sirinaM(6, [[10, 7], [15, 7]]),
                          "line-opacity": ["coalesce", ["get", "prosojnost"], 0.85] } });
  map.addLayer({ id: "k-voznja", type: "line", source: "k-pot", layout: okroglo,
                 filter: ["==", ["get", "vrsta"], "voznja"],
                 paint: { "line-color": PK_VOZNJA, "line-width": sirinaM(5, [[10, 4], [15, 4]]),
                          "line-opacity": ["coalesce", ["get", "prosojnost"], 0.9] } });
  map.addLayer({ id: "k-hoja-obroba", type: "line", source: "k-pot", layout: okroglo,
                 filter: ["==", ["get", "vrsta"], "hoja"],
                 paint: { "line-color": "#0f1115", "line-width": 7,
                          "line-opacity": ["*", 0.6, ["coalesce", ["get", "prosojnost"], 1]] } });
  // Črtkana: pot je pešpot, ne proga. Pri vodenju pa je debelejša, ker je
  // takrat edina stvar na zemljevidu, ki šteje.
  map.addLayer({ id: "k-hoja", type: "line", source: "k-pot",
                 layout: { "line-join": "round", "line-cap": "butt" },
                 filter: ["==", ["get", "vrsta"], "hoja"],
                 paint: { "line-color": PK_HOJA,
                          "line-width": ["coalesce", ["get", "sirina"], 4],
                          "line-dasharray": [1.4, 1.2],
                          "line-opacity": ["coalesce", ["get", "prosojnost"], 0.95] } });
  map.addLayer({ id: "k-jaz-obroc", type: "fill", source: "k-jaz",
                 filter: ["==", ["get", "vrsta"], "obroc"],
                 paint: { "fill-color": ME_COLOR, "fill-opacity": 0.1 } });
  map.addLayer({ id: "k-jaz-rob", type: "line", source: "k-jaz",
                 filter: ["==", ["get", "vrsta"], "obroc"],
                 paint: { "line-color": ME_COLOR, "line-width": 1, "line-opacity": 0.35 } });
  // Postajališče je obroč v barvi vožnje, z imenom od blizu: kje vstopiš in
  // kje izstopiš, mora biti vidno brez dotika. Polna modra je samo "ti".
  map.addLayer({ id: "k-tocke", type: "circle", source: "k-tocke",
                 paint: {
                   "circle-radius": 6, "circle-color": "#0f1115",
                   "circle-stroke-width": 3, "circle-stroke-color": PK_VOZNJA,
                   "circle-pitch-alignment": "map",
                 } });
  map.addLayer({ id: "k-tocke-imena", type: "symbol", source: "k-tocke",
                 minzoom: 13 - PK_LZ,
                 layout: {
                   "text-field": ["get", "ime"], "text-font": ["Noto Sans Bold"],
                   "text-size": 12, "text-anchor": "left", "text-offset": [0.9, 0],
                   "text-optional": true,
                 },
                 paint: { "text-color": "#f5c7a3", "text-halo-color": "#0f1115",
                          "text-halo-width": 1.6 } });
  map.addLayer({ id: "k-jaz", type: "circle", source: "k-jaz",
                 filter: ["==", ["get", "vrsta"], "pika"],
                 paint: { "circle-radius": 7, "circle-color": ME_COLOR,
                          "circle-stroke-color": "#ffffff", "circle-stroke-width": 2.5,
                          "circle-pitch-alignment": "map" } });

  // Ime točke na dotik; po petih sekundah odide (`NAME_MS`).
  let oblacek = null;
  map.on("click", "k-tocke", (e) => {
    const f = e.features && e.features[0];
    if (!f || !f.properties.ime) return;
    if (oblacek) oblacek.remove();
    oblacek = new ml.Popup({ closeButton: false, className: "kajros-tooltip", offset: 10 })
      .setLngLat(f.geometry.coordinates).setText(f.properties.ime).addTo(map);
    const moj = oblacek;
    setTimeout(() => moj.remove(), NAME_MS);
  });
  map.on("mouseenter", "k-tocke", () => { map.getCanvas().style.cursor = "pointer"; });
  map.on("mouseleave", "k-tocke", () => { map.getCanvas().style.cursor = ""; });

  return { map, ml };
}

// Start in cilj sta oznaki DOM in ne krogca v plasti: morata biti vidna od
// daleč, nad vsem drugim in z besedo -- obroč velikosti postajališča se je
// med ulicami izgubil (23. 9. 2026). Cilj je žebljiček, ki v nagibu stoji
// pokonci; start svetel krog. Besedi sta splošni, ne ime kraja: "dom" ne sodi
// na zaslon, ki ga kdo gleda čez ramo.
const PK_KONCA = { od: null, do: null };

function pkKonecEl(kaj) {
  const el = document.createElement("div");
  el.className = `pk-konec pk-${kaj}`;
  el.innerHTML = kaj === "od"
    ? `<svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
         <circle cx="12" cy="12" r="9.5" fill="#e7eaf0" stroke="#0f1115" stroke-width="2.5"/>
         <circle cx="12" cy="12" r="3.6" fill="#0f1115"/></svg><span class="pk-napis">Start</span>`
    : `<svg width="30" height="38" viewBox="0 0 30 38" aria-hidden="true">
         <path d="M15 37s12-12.2 12-22A12 12 0 0 0 3 15c0 9.8 12 22 12 22z"
               fill="${PK_VOZNJA}" stroke="#0f1115" stroke-width="2.5"/>
         <circle cx="15" cy="15" r="4.6" fill="#0f1115"/></svg><span class="pk-napis">Cilj</span>`;
  return el;
}

/** Postavi (ali umakne) oznaki starta in cilja; `od`, `do` sta `{lat, lon}` ali `null`. */
function pkKonca(k, od, do_) {
  if (!k) return;
  for (const [kaj, t] of [["od", od], ["do", do_]]) {
    if (!t) {
      if (PK_KONCA[kaj]) { PK_KONCA[kaj].remove(); PK_KONCA[kaj] = null; }
      continue;
    }
    if (!PK_KONCA[kaj]) {
      PK_KONCA[kaj] = new k.ml.Marker({
        element: pkKonecEl(kaj), anchor: kaj === "od" ? "center" : "bottom",
        pitchAlignment: "viewport", rotationAlignment: "viewport",
      }).setLngLat([t.lon, t.lat]).addTo(k.map);
    }
    PK_KONCA[kaj].setLngLat([t.lon, t.lat]);
  }
}

function pkEsri(map) {
  if (map.getSource("esri")) return;
  console.warn("vektorska podlaga ni na voljo, velja Esri");
  const ploscice = (sloj) => ({
    type: "raster", tileSize: 256, maxzoom: 16,
    tiles: [`${ESRI_CANVAS}/${sloj}/MapServer/tile/{z}/{y}/{x}`],
  });
  map.addSource("esri", { ...ploscice("World_Dark_Gray_Base"), attribution: ESRI_ATTR });
  map.addSource("esri-imena", ploscice("World_Dark_Gray_Reference"));
  const prvi = map.getLayersOrder()[0];
  map.addLayer({ id: "esri", type: "raster", source: "esri" }, prvi);
  map.addLayer({ id: "esri-imena", type: "raster", source: "esri-imena",
                 paint: { "raster-opacity": 0.9 } }, prvi);
}

function pkVir(map, id, features) {
  const v = map && map.getSource(id);
  if (v) v.setData({ type: "FeatureCollection", features });
}

function pkCrta(tocke, lastnosti) {
  // Naše točke so [lat, lon] (tako jih vrača strežnik), MapLibre bere [lon, lat].
  return { type: "Feature", properties: lastnosti,
           geometry: { type: "LineString", coordinates: tocke.map((t) => [t[1], t[0]]) } };
}

function pkTocka(ll, lastnosti) {
  return { type: "Feature", properties: lastnosti,
           geometry: { type: "Point", coordinates: [ll[1], ll[0]] } };
}

/** Lastna lega z obročem točnosti. Obroč ni okras: GPS v mestu zna zgrešiti
 *  za sto metrov in pika brez njega trdi natančnost, ki je nima. */
function pkJaz(map, loc) {
  const f = [];
  if (loc && loc.acc && loc.acc > 25) {
    f.push({ type: "Feature", properties: { vrsta: "obroc" },
             geometry: { type: "Polygon", coordinates: [pkKrog(loc.lat, loc.lon, loc.acc)] } });
  }
  if (loc) f.push(pkTocka([loc.lat, loc.lon], { vrsta: "pika" }));
  pkVir(map, "k-jaz", f);
}

/** Okvir seznama točk [lat, lon] za `fitBounds`. */
function pkOkvir(tocke) {
  let s = 90, j = -90, z = 180, v = -180;
  for (const t of tocke) {
    if (!t) continue;
    s = Math.min(s, t[0]); j = Math.max(j, t[0]);
    z = Math.min(z, t[1]); v = Math.max(v, t[1]);
  }
  return s <= j ? [[z, s], [v, j]] : null;
}

// `fitBounds` računa okvir za ravno kamero, nagib pa pride šele za njim
// (`transformCameraUpdate`) in spodnji rob odreže -- cilj je stal pod robom
// zemljevida. Zato je pregled največ Leafletov z15, kjer nagiba še ni, in
// ožji pogled ima spodaj več prostora.
const PK_BREZ_NAGIBA = PK_NAGIB_OD + PK_LZ;

function pkPrilagodi(map, tocke, opts) {
  const o = pkOkvir(tocke);
  if (!o || !map) return;
  const { maxZoom = PK_BREZ_NAGIBA, padding = 50, ...ostalo } = opts || {};
  const odmik = maxZoom > PK_BREZ_NAGIBA && typeof padding === "number"
    ? { top: padding, left: padding, right: padding, bottom: padding * 2.5 } : padding;
  map.fitBounds(o, { padding: odmik, maxZoom: maxZoom - PK_LZ, ...ostalo });
}

// ---------------------------------------------------------------- geometrija
//
// Vzdolž črte: okno vožnje po trasi, vodenje po pešpoti. Ena kopija za obe
// strani -- prej sta imeli vsaka svojo, z drugačno konstanto za meter.

function metriNaStopinjo(lat) {
  return { lat: 111320, lon: 111320 * Math.cos(lat * Math.PI / 180) };
}

function razdaljaM(a, b) {
  const k = metriNaStopinjo((a[0] + b[0]) / 2);
  const dy = (a[0] - b[0]) * k.lat;
  const dx = (a[1] - b[1]) * k.lon;
  return Math.sqrt(dx * dx + dy * dy);
}

// Kumulativne dolzine vzdolz trase, izracunane enkrat ob nalaganju.
function kumulative(pts) {
  const out = [0];
  for (let i = 1; i < pts.length; i++) out.push(out[i - 1] + razdaljaM(pts[i - 1], pts[i]));
  return out;
}

// Najblizja tocka na trasi: kako dalec vzdolz nje lezi in kako dalec od nje
// je iskana tocka. Odmik je merilo zaupanja -- velik pomeni, da tocka tej
// trasi ne pripada in racun po poti nima smisla.
function projekcijaNaTraso(pts, cums, lat, lon) {
  const k = metriNaStopinjo(lat);
  let najOdmik = Infinity, vzdolz = 0;
  for (let i = 0; i < pts.length - 1; i++) {
    const [ay, ax] = pts[i], [by, bx] = pts[i + 1];
    const vx = (bx - ax) * k.lon, vy = (by - ay) * k.lat;
    const wx = (lon - ax) * k.lon, wy = (lat - ay) * k.lat;
    const len2 = vx * vx + vy * vy;
    const t = len2 === 0 ? 0 : Math.max(0, Math.min(1, (wx * vx + wy * vy) / len2));
    const odmik = razdaljaM([lat, lon], [ay + t * (by - ay), ax + t * (bx - ax)]);
    if (odmik < najOdmik) {
      najOdmik = odmik;
      vzdolz = cums[i] + t * (cums[i + 1] - cums[i]);
    }
  }
  return { vzdolz, odmik: najOdmik };
}

// Tocka, ki lezi `cilj` metrov vzdolz trase.
function tockaNaTrasi(pts, cums, dolzina) {
  const cilj = Math.max(0, Math.min(dolzina, cums[cums.length - 1]));
  for (let i = 0; i < cums.length - 1; i++) {
    if (cilj >= cums[i] && cilj <= cums[i + 1]) {
      const d = cums[i + 1] - cums[i];
      const f = d === 0 ? 0 : (cilj - cums[i]) / d;
      return [pts[i][0] + f * (pts[i + 1][0] - pts[i][0]),
              pts[i][1] + f * (pts[i + 1][1] - pts[i][1])];
    }
  }
  return pts[pts.length - 1];
}
