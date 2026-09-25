"use strict";

// Zavihek „Deljenje" v pregledu: vozila, na katerih potniki danes delijo
// lego, na zemljevidu in v seznamu.
//
// Svoj endpoint in svoj ritem (`/admin/deljenje`, na 10 s): preostali
// pregled se osvežuje na minuto, ker gredo števci v bazo na 60 s, lega
// poročevalca pa se premakne na 10. Zato ta zavihek živi sam: `risi()` v
// `admin.js` ga ob vsaki osvežitvi pregleda pusti pri miru, sicer bi
// zemljevid vsako minuto nastal znova in skočil na začetni pogled.
//
// Kar je „javno", je natanko to, kar vidijo tabla in zemljevid
// (`deljenje.stanje()`); feed in GPS sta zraven, da se vidi razhajanje.

const DE_OSVEZI_MS = 10000;
// Sled potnika je modra, ker je modra v aplikaciji "lega človeka"
// (`ME_COLOR`); trasa vozila je siva podlaga zanjo, GPS avtobusa zelen kot
// avtobus (`LINE_INK`). Oranžna je tu zamuda in nič drugega.
const DE_TRASA = "#c3cad6";
const DE_UGASNJENO = "#6b7480";

const DE_IZIDI = {
  deli: ["deli", "točke prihajajo"],
  utihnil: ["utihnil", "brez konca in brez svežih točk: aplikacija zaprta ali brez signala"],
  potnik: ["ustavil", "potnik je deljenje ustavil sam"],
  izstop: ["izstopil", "tri zaporedne natančne točke izven trase"],
  cilj: ["na cilju", "vozilo je prišlo na zadnjo postajo in stoji"],
  cas: ["predolgo", "deljenje je trajalo dlje od šestih ur"],
};

let de = null;   // { koren, k, poll, podatki, izbran, oblacek, pogled }

function deOznaka(v) {
  if (v.mode === "bus" && v.network === "avtobus" && AGENCY[v.agency]) {
    return `${AGENCY[v.agency]} ${v.train_no}`;
  }
  return v.train_no || v.trip_id;
}

function deKljuc(v) { return `${v.trip_id}|${v.service_date}`; }

function deHref(v) {
  const q = new URLSearchParams({ date: v.service_date, trip: v.trip_id });
  const pot = v.network === "avtobus" ? "/app/bus/" : "/app/train/";
  return `${pot}${encodeURIComponent(v.train_no)}?${q}`;
}

function deUra(iso) { return iso ? hhmm(iso) : "—"; }

function deStarost(s) {
  if (s == null) return "";
  if (s < 90) return `pred ${s} s`;
  return `pred ${Math.round(s / 60)} min`;
}

function deKje(j) {
  if (!j) return "";
  if (j.pri) return `pri ${j.pri}`;
  if (j.med) return `med ${j.med[0]} in ${j.med[1]}`;
  return "";
}

function deZamuda(z, kratko) {
  if (!z) return `<span class="nic">—</span>`;
  return `<span style="color:${delayColor(z)}">${escapeHtml(delayText(z, kratko))}</span>`;
}

function deIzid(izid) {
  const [ime, opis] = DE_IZIDI[izid] || [izid, ""];
  return `<span class="de-izid de-izid-${escapeHtml(izid)}" title="${escapeHtml(opis)}">${escapeHtml(ime)}</span>`;
}

/** Kje je vozilo na zemljevidu: po javnem stanju, sicer zadnja točka deljenja. */
function deLega(v) {
  if (v.javno && v.javno.lat != null) return [v.javno.lat, v.javno.lon];
  const d = [...v.deljenja].reverse().find((x) => x.lat != null);
  return d ? [d.lat, d.lon] : null;
}

// ------------------------------------------------------------------ plošče

function deKpi(d) {
  const p = d.povzetek;
  const naj = d.vozila.flatMap((v) => v.deljenja.map((x) => ({ v, x })))
    .sort((a, b) => b.x.trajanje_s - a.x.trajanje_s)[0];
  const izidi = Object.entries(p.izidi).sort((a, b) => b[1] - a[1])
    .map(([k, n]) => `${n} ${(DE_IZIDI[k] || [k])[0]}`).join(" · ");
  return `
    ${ploscica(st(p.deli_zdaj), "deli ta hip", p.vozil_zdaj ? `na ${st(p.vozil_zdaj)} ${p.vozil_zdaj === 1 ? "vozilu" : "vozilih"}` : "nihče", "je-poudarek")}
    ${ploscica(st(p.vozil), "vozil danes", "z vsaj eno sprejeto točko ali začetkom")}
    ${ploscica(st(p.deljenj), "deljenj danes", escapeHtml(izidi) || "&nbsp;")}
    ${ploscica(st(p.tock), "točk danes", "projicirane na traso")}
    ${ploscica(st(p.prehodov), "prehodov danes", "prihodi in odhodi s postaj")}
    ${ploscica(naj ? trajanje(naj.x.trajanje_s) : "—", "najdaljše deljenje", naj ? escapeHtml(deOznaka(naj.v)) : "&nbsp;")}`;
}

function deVozilo(v) {
  const j = v.javno;
  const n = v.deljenja.length;
  const tock = v.deljenja.reduce((a, x) => a + x.tock, 0);
  const vrstice = [];
  if (j) {
    vrstice.push(`${escapeHtml(potnikov(j.n))}${j.soglasje ? ` · <b class="de-soglasje">soglasje</b>` : ""}
      · ${escapeHtml(deKje(j))}${j.stoji ? " · stoji" : ""} · ${escapeHtml(deStarost(j.starost_s))}`);
    vrstice.push(`potniki ${deZamuda(j.zamuda)} · feed ${deZamuda(v.feed && v.feed.zamuda)}`
      + (v.gps ? ` · GPS ${escapeHtml(deStarost(v.gps.starost_s))}` : ""));
  } else {
    const zadnje = v.deljenja[v.deljenja.length - 1];
    vrstice.push(`zadnje ob ${deUra(zadnje.zadnja)} · ${deIzid(zadnje.izid)} · potniki ${deZamuda(zadnje.zamuda)}`);
  }
  vrstice.push(`${n} ${n === 1 ? "deljenje" : n === 2 ? "deljenji" : n < 5 ? "deljenja" : "deljenj"} · ${st(tock)} točk
    · <a href="${escapeHtml(deHref(v))}" target="_blank" rel="noopener">odpri vožnjo →</a>`);
  return `<li class="de-v${j ? " je-zivo" : ""}${de && de.izbran === deKljuc(v) ? " je-izbran" : ""}" data-kljuc="${escapeHtml(deKljuc(v))}">
    <div class="de-v-glava">
      <span class="de-pika" style="background:${j ? delayColor(j.zamuda) : "transparent"}"></span>
      <b>${escapeHtml(deOznaka(v))}</b>
      <span class="de-smer">${escapeHtml(v.od && v.do ? `${v.od} – ${v.do}` : v.headsign || "")}</span>
      ${j ? `<span class="de-zivo">živo</span>` : ""}
    </div>
    ${vrstice.map((x) => `<div class="de-v-vr">${x}</div>`).join("")}
  </li>`;
}

function deSeznam(d) {
  if (!d.vozila.length) return prazno("danes še nihče ni delil lege");
  return `<ul class="de-seznam" id="de-seznam">${d.vozila.map(deVozilo).join("")}</ul>`;
}

function deTabela(d) {
  const vrste = d.vozila.flatMap((v) => v.deljenja.map((x) => ({ v, x })))
    .sort((a, b) => (b.x.zacetek || "").localeCompare(a.x.zacetek || ""));
  if (!vrste.length) return prazno("ni deljenj");
  return `<div class="adm-ovoj-t"><table class="adm-t">
    <thead><tr><th>začetek</th><th>zadnja točka</th><th>vozilo</th><th class="n">trajanje</th>
      <th class="n">točk</th><th class="n">prehodov</th><th>izid</th><th class="n">zamuda po potniku</th></tr></thead>
    <tbody>${vrste.map(({ v, x }) => `<tr>
      <td class="de-cas">${deUra(x.zacetek)}</td><td class="de-cas">${deUra(x.zadnja)}</td>
      <td><a class="de-na-karti" href="#deljenje" data-kljuc="${escapeHtml(deKljuc(v))}">${escapeHtml(deOznaka(v))}</a>
        <span class="nic">${escapeHtml(v.headsign || "")}</span></td>
      <td class="n">${x.trajanje_s ? trajanje(Math.max(60, x.trajanje_s)) : "—"}</td>
      <td class="n">${st(x.tock)}</td><td class="n">${st(x.prehodov)}</td>
      <td>${deIzid(x.izid)}</td><td class="n">${deZamuda(x.zamuda, true)}</td></tr>`).join("")}
    </tbody></table></div>`;
}

function deOkvir() {
  return `<div class="adm-mreza">
    <div class="adm-kpi" id="de-kpi"></div>
    <section class="adm-plosca s8 de-plosca-karta">
      <h2>Zemljevid <small>modro: kar so potniki prevozili · sivo črtkano: trasa vozila, na katerem kdo deli · zeleni obroč: GPS avtobusa iz feeda</small></h2>
      <p class="adm-pod">Pika je lega vozila, kot jo vidi javnost; barva je zamuda po poročilu. Votla pika je deljenje, ki ne teče več.</p>
      <div class="de-karta" id="de-karta"></div>
    </section>
    <section class="adm-plosca s4">
      <h2>Vozila <small>danes · živa na vrhu · klik pokaže na zemljevidu</small></h2>
      <p class="adm-pod">„Potniki" je zamuda, ki jo pokažeta tabla in zemljevid; „feed" zadnja izmerjena iz zajema.</p>
      <div id="de-vozila"></div>
    </section>
    <section class="adm-plosca s12">
      <h2>Današnja deljenja <small>eno deljenje je en telefon na eni vožnji · id se ne kaže, ker ne pove ničesar</small></h2>
      <p class="adm-pod"></p>
      <div id="de-tabela"></div>
    </section>
  </div>`;
}

// ------------------------------------------------------------------ zemljevid

async function deKarta() {
  const el_ = el("de-karta");
  const k = await pkUstvari(el_, { sredisce: [46.12, 14.82], zoom: 9, dodatnaImena: false });
  if (!de || !el_.isConnected) { if (k) k.map.remove(); return; }
  if (!k) {
    el_.innerHTML = prazno("zemljevida ni: brskalnik nima WebGL2");
    return;
  }
  const { map, ml } = k;
  for (const id of ["de-trase", "de-sledi", "de-gps", "de-vozila"]) {
    map.addSource(id, { type: "geojson", data: PK_PRAZNO });
  }
  const okroglo = { "line-join": "round", "line-cap": "round" };
  // Črtkana, ker je polna siva črta med cestami podlage izginila.
  map.addLayer({ id: "de-trase", type: "line", source: "de-trase",
                 layout: { "line-join": "round", "line-cap": "butt" },
                 paint: { "line-color": DE_TRASA, "line-width": 2.5, "line-dasharray": [2, 1.5],
                          "line-opacity": 0.9 } });
  map.addLayer({ id: "de-sledi-obroba", type: "line", source: "de-sledi", layout: okroglo,
                 paint: { "line-color": "#0f1115", "line-width": 7, "line-opacity": 0.7 } });
  map.addLayer({ id: "de-sledi", type: "line", source: "de-sledi", layout: okroglo,
                 paint: { "line-color": ME_COLOR, "line-width": 4,
                          "line-opacity": ["case", ["get", "zivo"], 0.95, 0.45] } });
  map.addLayer({ id: "de-gps", type: "circle", source: "de-gps",
                 paint: { "circle-radius": 7, "circle-color": "transparent",
                          "circle-stroke-width": 2.5, "circle-stroke-color": LINE_INK,
                          "circle-pitch-alignment": "map" } });
  map.addLayer({ id: "de-vozila", type: "circle", source: "de-vozila",
                 paint: {
                   "circle-radius": ["case", ["get", "zivo"], 8, 6],
                   "circle-color": ["case", ["get", "zivo"], ["get", "barva"], "#0f1115"],
                   "circle-stroke-width": 2.5,
                   "circle-stroke-color": ["case", ["get", "zivo"], "#ffffff", DE_UGASNJENO],
                   "circle-pitch-alignment": "map",
                 } });
  map.addLayer({ id: "de-vozila-imena", type: "symbol", source: "de-vozila",
                 layout: {
                   "text-field": ["get", "oznaka"], "text-font": ["Noto Sans Bold"],
                   "text-size": 12, "text-anchor": "left", "text-offset": [1.1, 0],
                   // Ob gneči ostanejo imena živih; ostala so v seznamu.
                   "symbol-sort-key": ["case", ["get", "zivo"], 0, 1],
                 },
                 paint: { "text-color": ["case", ["get", "zivo"], "#e7eaf0", "#9aa3b2"],
                          "text-halo-color": "#0f1115", "text-halo-width": 1.6 } });
  map.on("click", "de-vozila", (e) => {
    const f = e.features && e.features[0];
    if (f) deIzberi(f.properties.kljuc, false);
  });
  map.on("mouseenter", "de-vozila", () => { map.getCanvas().style.cursor = "pointer"; });
  map.on("mouseleave", "de-vozila", () => { map.getCanvas().style.cursor = ""; });
  de.k = { map, ml };
  if (de.podatki) deNaKarto(de.podatki);
}

function deNaKarto(d) {
  if (!de.k) return;
  const { map } = de.k;
  const trase = [], sledi = [], gps = [], vozila = [];
  for (const v of d.vozila) {
    const zivo = !!v.javno;
    for (const kos of v.trasa) trase.push(pkCrta(kos, {}));
    for (const x of v.deljenja) {
      for (const kos of x.sled) sledi.push(pkCrta(kos, { zivo: x.izid === "deli" }));
    }
    if (zivo && v.gps) gps.push(pkTocka([v.gps.lat, v.gps.lon], {}));
    const ll = deLega(v);
    if (ll) {
      vozila.push(pkTocka(ll, {
        kljuc: deKljuc(v), zivo, oznaka: zivo && v.javno.n > 1 ? `${deOznaka(v)} · ${v.javno.n}` : deOznaka(v),
        barva: zivo ? delayColor(v.javno.zamuda) : DE_UGASNJENO,
      }));
    }
  }
  pkVir(map, "de-trase", trase);
  pkVir(map, "de-sledi", sledi);
  pkVir(map, "de-gps", gps);
  pkVir(map, "de-vozila", vozila);
  // Pogled se postavi enkrat, ob prvih podatkih; pozneje bi zemljevid na
  // deset sekund trgal izpod rok (isto pravilo kot v oknu vožnje).
  if (!de.pogled && vozila.length) {
    const zive = vozila.filter((f) => f.properties.zivo);
    const tocke = (zive.length ? zive : vozila).map((f) => [f.geometry.coordinates[1], f.geometry.coordinates[0]]);
    pkPrilagodi(map, tocke, { maxZoom: 12, padding: 60, duration: 0 });
    de.pogled = true;
  }
  deOblacek();
}

/** Oblaček izbranega vozila; ob novih podatkih se prepiše, ne zapre. */
function deOblacek() {
  if (!de.k || !de.izbran || !de.podatki) return;
  const v = de.podatki.vozila.find((x) => deKljuc(x) === de.izbran);
  const ll = v && deLega(v);
  if (!ll) { if (de.oblacek) de.oblacek.remove(); return; }
  const j = v.javno;
  const html = `<div class="de-obl">
    <b>${escapeHtml(deOznaka(v))}</b> <span class="nic">${escapeHtml(v.headsign || "")}</span>
    ${j ? `<div>${escapeHtml(potnikov(j.n))}${j.soglasje ? " · soglasje" : ""} · ${escapeHtml(deKje(j))}</div>
      <div>potniki ${deZamuda(j.zamuda)} · feed ${deZamuda(v.feed && v.feed.zamuda)}</div>
      <div class="nic">zadnja točka ${escapeHtml(deStarost(j.starost_s))}</div>`
      : `<div class="nic">zadnje deljenje ob ${deUra(v.deljenja[v.deljenja.length - 1].zadnja)}</div>`}
    <a href="${escapeHtml(deHref(v))}" target="_blank" rel="noopener">odpri vožnjo →</a></div>`;
  if (!de.oblacek || !de.oblacek.isOpen()) {
    // Brez fokusa: med letom je vozilo še zunaj okvirja, in fokus na
    // oblačku tam je pomaknil stran in platno pod zemljevidom.
    de.oblacek = new de.k.ml.Popup({ offset: 12, maxWidth: "300px", focusAfterOpen: false })
      .addTo(de.k.map);
    const moj = de.oblacek;
    moj.on("close", () => { if (de && de.oblacek === moj) { de.izbran = null; deOznaciIzbrano(); } });
  }
  de.oblacek.setLngLat([ll[1], ll[0]]).setHTML(html);
}

function deOznaciIzbrano() {
  document.querySelectorAll("#de-seznam .de-v").forEach((li) => {
    li.classList.toggle("je-izbran", !!de && li.dataset.kljuc === de.izbran);
  });
}

function deIzberi(kljuc, leti) {
  de.izbran = kljuc;
  deOznaciIzbrano();
  const v = de.podatki && de.podatki.vozila.find((x) => deKljuc(x) === kljuc);
  const ll = v && deLega(v);
  if (leti && ll && de.k) {
    de.k.map.flyTo({ center: [ll[1], ll[0]], zoom: Math.max(de.k.map.getZoom(), 12 - PK_LZ) });
  }
  deOblacek();
}

// ------------------------------------------------------------------ življenje

async function deNalozi() {
  const r = await fetch("/admin/deljenje", { credentials: "same-origin" });
  if (!r.ok) throw new Error(r.status === 403 ? "Napačen žeton." : `strežnik: ${r.status}`);
  const d = await r.json();
  if (!de) return;
  de.podatki = d;
  if (!d.vklopljeno) {
    el("de-vozila").innerHTML = prazno("deljenje je izklopljeno (KAJROS_DELI=0)");
  } else {
    el("de-vozila").innerHTML = deSeznam(d);
  }
  el("de-kpi").innerHTML = deKpi(d);
  el("de-tabela").innerHTML = deTabela(d);
  el("deljenje-znacka").hidden = !d.povzetek.deli_zdaj;
  el("deljenje-znacka").textContent = d.povzetek.deli_zdaj ? String(d.povzetek.deli_zdaj) : "";
  deNaKarto(d);
}

/** Odpre zavihek v `koren`; če je že odprt, ne naredi nič. */
function deljenjeOdpri(koren) {
  if (de && el("de-karta") && koren.contains(el("de-karta"))) return;
  deljenjeZapri();
  koren.innerHTML = deOkvir();
  de = { koren, k: null, poll: null, podatki: null, izbran: null, oblacek: null, pogled: false };
  // Seznam in tabela se prepišeta na deset sekund, poslušalec pa je na
  // korenu in preživi.
  koren.addEventListener("click", deKlik);
  // Napako pobriše samo, če je bila njegova: opozorilo pregleda (štetje
  // izklopljeno) ni njegovo.
  let napaka = false;
  de.poll = pollWhileVisible(async () => {
    try {
      await deNalozi();
      if (napaka) pokaziNapako("");
      napaka = false;
    } catch (e) {
      pokaziNapako(`Deljenja ni bilo mogoče naložiti — ${e.message}`);
      napaka = true;
    }
  }, DE_OSVEZI_MS);
  deKarta();
}

function deKlik(e) {
  if (e.target.closest("a[target]")) return;
  const t = e.target.closest(".de-v, .de-na-karti");
  if (!t) return;
  e.preventDefault();
  deIzberi(t.dataset.kljuc, true);
  if (t.classList.contains("de-na-karti")) el("de-karta").scrollIntoView({ behavior: "smooth", block: "center" });
}

function deljenjeZapri() {
  if (!de) return;
  if (de.poll) de.poll.stop();
  de.koren.removeEventListener("click", deKlik);
  if (de.k) de.k.map.remove();
  de = null;
}
