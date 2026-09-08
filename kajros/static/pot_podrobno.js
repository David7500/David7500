/* Ena pot, razložena po korakih.
 *
 * Seznam predlogov odgovarja na „s čim in kdaj". Ta stran na **„kako"**: kod
 * hodiš do postajališča, kje izstopiš in kaj je vmes. Zato dvoje, česar seznam
 * nima — prava pešpot na zemljevidu (ne ravna črta) in vmesni postanki vožnje.
 *
 * Pot je v naslovu, ne v seji: kdor jo komu pošlje, mu pošlje pot, ne svojega
 * brskalnika.
 */

const ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas";
const map = L.map("karta", { zoomControl: true }).setView([46.1, 14.6], 8);
L.tileLayer(`${ESRI}/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}`, {
  maxZoom: 19, maxNativeZoom: 16, attribution: ESRI_ATTR,
}).addTo(map);
L.tileLayer(`${ESRI}/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}`,
            { maxZoom: 19, maxNativeZoom: 16, opacity: 0.9 }).addTo(map);

const potLayer = L.layerGroup().addTo(map);
const jazLayer = L.layerGroup().addTo(map);
const $ = (s) => document.querySelector(s);
const Q = new URLSearchParams(location.search);

const ura = (ts) => new Date(ts * 1000).toLocaleTimeString("sl-SI",
  { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Ljubljana" });

function minute(s) {
  const m = Math.floor(s / 60 + 0.5);
  return m < 60 ? `${m} min` : `${Math.floor(m / 60)} h ${String(m % 60).padStart(2, "0")}`;
}

function razdalja(m) {
  if (m == null) return "";
  return m < 950 ? ` · ${Math.round(m / 10) * 10} m` : ` · ${(m / 1000).toFixed(1)} km`;
}

// ---------------------------------------------------------------- izris

function zamudaHtml(z) {
  if (!z) return "";
  const barva = delayColor(z);
  const vrsta = z.vrsta ? ` <span class="zam-vrsta">${escapeHtml(z.vrsta)}</span>` : "";
  return `<span class="zam" style="color:${barva};border-color:${barva}55">`
    + `${escapeHtml(delayText(z))}</span>${vrsta}`;
}

// Žeton ob izstopu samo takrat, kadar se od vstopnega res razlikuje -- dva
// enaka žetona v isti vrstici sta šum, dva različna pa edino, kar pojasni,
// zakaj je prihod za voznim redom, čeprav vstop ni bil.
function izstopHtml(n) {
  const a = delayMin(n.zamuda);
  const b = delayMin(n.zamuda_izstop);
  if (b == null || a === b) return "";
  return " " + zamudaHtml(n.zamuda_izstop);
}

// Ko izstopiš, te zanima samo zadnji kos poti, ne cela. Zato ima vsak peš
// korak svoj gumb: zemljevid približa nanj in ga pripelje pred oči -- na
// telefonu je zemljevid pod seznamom in bi ga bilo treba iskati z drsenjem.
function hojaGumb(n, i) {
  const zadnja = n.do === null;
  const beseda = n.od === null ? "pot do postajališča"
    : zadnja ? "sem izstopil — pot do cilja"
    : "pot do prestopa";
  return `<button class="hoja-gumb${zadnja ? " je-cilj" : ""}" data-korak="${i}">`
    + `${beseda}</button>`;
}

function hojaHtml(n, i) {
  const od = n.od ? escapeHtml(n.od) : "izhodišče";
  const kam = n.do ? escapeHtml(n.do) : "cilj";
  // Kadar usmerjevalnika ni, poti nismo izračunali in tega ne skrivamo:
  // ravna črta na zemljevidu bi trdila pot, ki je ni.
  const opomba = n.tocke ? "" :
    '<span class="korak-opomba">pešpot ni izračunana — na zemljevidu je zračna črta</span>';
  return `<li class="korak je-hoja">
    <span class="korak-znak" aria-hidden="true">↓</span>
    <div class="korak-telo">
      <div class="korak-vrh">peš <strong>${minute(n.sekunde)}</strong>${razdalja(n.metri)}</div>
      <div class="korak-kam">${od} → ${kam}</div>
      ${opomba}
      ${hojaGumb(n, i)}
    </div></li>`;
}

function voznjaHtml(n) {
  const pot = n.network === "avtobus" ? "bus" : "train";
  const okno = `/app/${pot}/${encodeURIComponent(n.train_no)}?trip=${encodeURIComponent(n.trip_id)}`;
  const odh = n.odhod_ocena || n.odhod;
  const prih = n.prihod_ocena || n.prihod;
  const vr = n.odhod_ocena && n.odhod_ocena !== n.odhod
    ? `<div class="korak-opomba">vozni red ${ura(n.odhod)} → ${ura(n.prihod)}</div>` : "";
  // Vmesni postanki so zaprti: potnika najprej zanima, kje izstopi, in šele
  // potem, kaj je vmes. Prvi in zadnji sta v vrsticah nad in pod, zato ju tu ni.
  const vmes = n.postanki.slice(1, -1);
  const seznam = vmes.length ? `<details class="vmesni">
      <summary>${vmes.length} ${sklon(vmes.length, "postanek")} vmes</summary>
      <ol>${vmes.map((s) => `<li><span class="vm-ura">${
        s.prihod ? ura(s.prihod) : "—"}</span> ${escapeHtml(s.ime)}</li>`).join("")}</ol>
    </details>` : "";
  return `<li class="korak je-voznja">
    <span class="korak-znak" aria-hidden="true">●</span>
    <div class="korak-telo">
      <div class="korak-vrh">
        <a class="noga-linija" href="${okno}">${escapeHtml(n.train_no)}</a>
        ${zamudaHtml(n.zamuda)}
        ${n.headsign ? `<span class="korak-smer">→ ${escapeHtml(n.headsign)}</span>` : ""}
      </div>
      <div class="korak-vstop"><strong>${ura(odh)}</strong> ${escapeHtml(n.od)}</div>
      ${seznam}
      <div class="korak-izstop"><strong>${ura(prih)}</strong> ${escapeHtml(n.do)}
        <span class="korak-kam">izstopiš</span>${izstopHtml(n)}</div>
      ${vr}
    </div></li>`;
}

// Plast na nogo, da se da posamezna približati in poudariti. Brez tega je
// zemljevid ena sama črta in "pokaži mi zadnji kos" ni izvedljivo.
const PLASTI = new Map();      // indeks noge -> {crta, tocke}
let vseMeje = null;

// Prestop stoji MED vožnjama, ki ju veže. Brez rezerve je "prestop" samo
// beseda; z njo je odgovor na edino vprašanje, ki ga potnik tam ima.
function prestopHtml(t, pred, po) {
  const mins = preostanekPrestopa(t.nacrtovano_s, pred && pred.zamuda, po && po.zamuda);
  const nacrt = Math.floor(t.nacrtovano_s / 60 + 0.5);
  const barva = mins == null ? "var(--ink-mute)"
    : mins < 2 ? "var(--sev-bad)" : mins < 5 ? "var(--sev-hard)" : "var(--ok)";
  const pes = t.pes_s >= 60 ? ` · ${minute(t.pes_s)} hoje vmes` : "";
  return `<li class="korak je-prestop">
    <span class="korak-znak" aria-hidden="true">⇄</span>
    <div class="korak-telo" style="color:${barva}">
      ${escapeHtml(mins == null ? `${nacrt} min za prestop` : prestopText(mins))}
      <span class="korak-kam">v ${escapeHtml(t.kje)}${pes}${
        mins == null ? " · brez zamud" : ""}</span>
    </div></li>`;
}

function korakiHtml(p) {
  const voznje = p.noge.filter((n) => n.vrsta === "voznja");
  const out = [];
  p.noge.forEach((n, i) => {
    const v = voznje.indexOf(n);
    if (v > 0 && p.prestopi && p.prestopi[v - 1]) {
      out.push(prestopHtml(p.prestopi[v - 1], voznje[v - 1], n));
    }
    out.push(n.vrsta === "hoja" ? hojaHtml(n, i) : voznjaHtml(n));
  });
  return out.join("");
}

function narisi(p) {
  potLayer.clearLayers();
  PLASTI.clear();
  const meje = [];
  const skice = [];
  p.noge.forEach((n, i) => {
    if (n.vrsta === "hoja") {
      const crta = n.tocke && n.tocke.length > 1 ? n.tocke : [n.od_ll, n.do_ll];
      if (!crta[0] || !crta[1]) return;
      const l = L.polyline(crta, { color: "#2f7fff", weight: 4, dashArray: "4 6",
                                   opacity: 0.95 }).addTo(potLayer);
      PLASTI.set(i, { crta: l, tocke: crta });
      crta.forEach((t) => meje.push(t));
    } else {
      const l = L.polyline([n.od_ll, n.do_ll],
        { color: "#f0934f", weight: 4, opacity: 0.55 }).addTo(potLayer);
      PLASTI.set(i, { crta: l, tocke: [n.od_ll, n.do_ll] });
      skice.push([n, l, i]);
      meje.push(n.od_ll, n.do_ll);
    }
  });
  // Konca poti: kje začneš in kje si doma.
  const prva = p.noge[0];
  const zadnja = p.noge[p.noge.length - 1];
  for (const [ll, barva, opis] of [[prva.od_ll, "#2f7fff", "izhodišče"],
                                   [zadnja.do_ll, "#f0934f", "cilj"]]) {
    if (!ll) continue;
    L.circleMarker(ll, { radius: 7, weight: 3, color: "#ffffff",
                         fillColor: barva, fillOpacity: 1 })
      .addTo(potLayer).bindTooltip(opis);
  }
  vseMeje = meje.length ? L.latLngBounds(meje) : null;
  if (vseMeje) map.fitBounds(vseMeje, { padding: [40, 40], maxZoom: 16 });
  (async () => {
    for (const [n, crta, i] of skice) {
      const t = await trasa(n).catch(() => null);
      if (t) { crta.setLatLngs(t); PLASTI.get(i).tocke = t; }
      crta.setStyle({ opacity: 0.9 });
    }
  })();
}

/** Približaj na eno nogo (ali na vso pot, kadar je `i` `null`). */
function priblizaj(i) {
  for (const [j, plast] of PLASTI) {
    // Ostale ne skrijemo, samo umaknemo: pot brez okolice je brez smisla,
    // pot, ki ji okolica tekmuje, pa neberljiva.
    plast.crta.setStyle({ opacity: i === null || j === i ? 0.9 : 0.25 });
  }
  const cilj = i === null ? vseMeje
    : PLASTI.has(i) ? L.latLngBounds(PLASTI.get(i).tocke) : null;
  if (cilj) map.fitBounds(cilj, { padding: [40, 40], maxZoom: 17 });
  document.querySelectorAll(".hoja-gumb").forEach((b) =>
    b.classList.toggle("je-on", Number(b.dataset.korak) === i));
  $("#cela").hidden = i === null;
  // Na telefonu je zemljevid pod seznamom; gumb brez tega premakne pogled
  // nekam, česar se ne vidi.
  $("#karta").scrollIntoView({ behavior: "smooth", block: "nearest" });
  map.invalidateSize();
}

// ---------------------------------------------------------------- zemljevid

// Cez celo STRAN, ne cez cel zaslon -- isti razlog kot pri oknu voznje:
// fullscreen skrije naslovno vrstico, gumb nazaj in vsak drug orientir, izhod
// pa je tipka, ki je na telefonu ni.
$("#karta-max").addEventListener("click", () => {
  const veliko = !document.body.classList.contains("karta-velika");
  document.body.classList.toggle("karta-velika", veliko);
  $("#karta-max").setAttribute("aria-pressed", String(veliko));
  $("#karta-max").title = veliko ? "Pomanjšaj zemljevid" : "Zemljevid čez celo stran";
  requestAnimationFrame(() => map.invalidateSize());
});

// Med hojo je edino vprašanje "grem v pravo smer". Zato lega TU sledi in se ne
// izmeri enkrat: prvi popravek GPS pogosto zgreši za sto metrov, potnik pa se
// medtem premika.
let sledim = false;
$("#karta-lega").addEventListener("click", async () => {
  const b = $("#karta-lega");
  if (sledim) return;
  b.classList.add("je-iskanje");
  try {
    const loc = await locateMe({ napredek: (l) => drawMe(jazLayer, l) });
    drawMe(jazLayer, loc);
    map.setView([loc.lat, loc.lon], Math.max(map.getZoom(), 16));
    sledi((l) => drawMe(jazLayer, l));
    sledim = true;
    b.classList.add("je-on");
  } catch (e) {
    $("#stanje").textContent = e.message;
    $("#stanje").className = "pot-stanje je-napaka";
  } finally {
    b.classList.remove("je-iskanje");
  }
});

// ---------------------------------------------------------------- nalaganje

function nazajUrl() {
  const q = new URLSearchParams();
  const t = (a, b) => `${Number(Q.get(a)).toFixed(5)},${Number(Q.get(b)).toFixed(5)}`;
  if (Q.get("od_lat")) q.set("od", t("od_lat", "od_lon"));
  if (Q.get("do_lat")) q.set("do", t("do_lat", "do_lon"));
  return q.toString() ? `/app/pot?${q}` : "/app/pot";
}

async function nalozi() {
  $("#nazaj").href = nazajUrl();
  const p = new URLSearchParams();
  for (const k of ["noge", "od_lat", "od_lon", "do_lat", "do_lon", "date"]) {
    if (Q.get(k)) p.set(k, Q.get(k));
  }
  if (!p.get("noge")) {
    $("#stanje").textContent = "Poti v naslovu ni.";
    $("#stanje").className = "pot-stanje je-napaka";
    return;
  }
  $("#stanje").textContent = "Nalagam …";
  try {
    const r = await fetch(`/api/pot/podrobno?${p}`);
    if (!r.ok) {
      const telo = await r.json().catch(() => ({}));
      throw new Error(telo.detail || `strežnik je vrnil ${r.status}`);
    }
    const d = await r.json();
    const pr = d.predlog;
    $("#stanje").textContent = "";
    $("#glava").innerHTML = `
      <div class="podr-ure"><strong>${ura(pr.odhod_ocena || pr.odhod)}</strong>
        → <strong>${ura(pr.prihod_ocena || pr.prihod)}</strong></div>
      <div class="podr-meta">${minute(pr.trajanje_s)}${
        pr.hoje_s >= 60 ? ` · ${minute(pr.hoje_s)} hoje` : ""} · ${
        pr.prestopov === 0 ? "brez prestopa"
          : `${pr.prestopov} ${sklon(pr.prestopov, "prestop")}`} · ${dayLabel(d.datum)}</div>`;
    $("#koraki").innerHTML = korakiHtml(pr);
    narisi(pr);
    $("#koraki").querySelectorAll(".hoja-gumb").forEach((b) => {
      b.addEventListener("click", () => priblizaj(Number(b.dataset.korak)));
    });
    $("#cela").addEventListener("click", () => priblizaj(null));
  } catch (e) {
    $("#stanje").textContent = e.message;
    $("#stanje").className = "pot-stanje je-napaka";
  }
}

nalozi();
