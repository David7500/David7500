"use strict";

// Zavihek „Deljenje" v pregledu: vsako deljenje lege posebej -- seznam,
// zemljevid in podrobnosti izbranega (graf vožnje, prehodi postaj).
//
// Svoj endpoint in svoj ritem (`/admin/deljenje`, na 10 s): preostali
// pregled se osvežuje na minuto, ker gredo števci v bazo na 60 s, lega
// poročevalca pa se premakne na 5. Zato ta zavihek živi sam: `risi()` v
// `admin.js` ga ob vsaki osvežitvi pregleda pusti pri miru, sicer bi
// zemljevid vsako minuto nastal znova in skočil na začetni pogled.
//
// Dan in izbrano deljenje sta v naslovu (`#deljenje/2026-10-11/<oznaka>`),
// da ju ohrani osvežitev in da se dasta poslati. Oznaka ni id deljenja: s
// tem bi lahko kdorkoli deljenju dodajal točke (`deljenje.oznaka`).
//
// Kar je „javno", je natanko to, kar vidijo tabla in zemljevid
// (`deljenje.stanje()`); feed in GPS sta zraven, da se vidi razhajanje.

const DE_OSVEZI_MS = 10000;
// Sled potnika je modra, ker je modra v aplikaciji "lega človeka"
// (`ME_COLOR`); trasa vozila je siva podlaga zanjo, GPS avtobusa zelen kot
// avtobus (`LINE_INK`). Oranžna je tu zamuda in nič drugega.
const DE_TRASA = "#c3cad6";
const DE_DRUGA = "#8a94a6";
const DE_UGASNJENO = "#6b7480";
// Točke z vrzeljo, daljšo od tega, so na grafu ločene: odjemalec pošilja na
// 3--5 s (`deljenje.POSILJANJE_S`), pol minute tišine je predor ali izpad.
const DE_VRZEL_S = 30;

const DE_IZIDI = {
  deli: ["deli zdaj", "točke prihajajo"],
  utihnil: ["utihnil", "brez konca in brez svežih točk: aplikacija zaprta ali brez signala"],
  potnik: ["ustavil", "potnik je deljenje ustavil sam"],
  znova: ["znova", "z istega naslova se je na isti vožnji začelo novo deljenje"],
  izstop: ["izstopil", "tri zaporedne natančne točke izven trase ali odmaknjene, medtem ko vozilo stoji"],
  cilj: ["na cilju", "vozilo je prišlo na zadnjo postajo in stoji"],
  cas: ["predolgo", "deljenje je trajalo dlje od šestih ur"],
};
const DE_ODJEMALCI = {
  splet: ["brskalnik", "brskalnik"],
  aplikacija: ["aplikacija", "aplikacija, stran v oknu"],
  android: ["Android", "aplikacija, storitev v ozadju (deli tudi z ugasnjenim zaslonom)"],
};
const DE_VIRI = {
  domov: "domača stran", iskalnik: "iskalnik", okno: "okno vožnje",
  budilka: "budilka", vodenje: "vodenje do postajališča",
};
const DE_ZAVRNITVE = {
  ni_na_trasi: "ni ob progi", ni_tu: "vozila ni tu", ne_vozi: "ne vozi",
  neznana: "neznana vožnja", drugo: "drugo",
};

let de = null;   // glej `deljenjeOdpri`

const DE_URA_S = new Intl.DateTimeFormat("sl-SI", {
  timeZone: "Europe/Ljubljana", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false,
});
const deUraS = (iso) => (iso ? DE_URA_S.format(new Date(iso)) : "—");
const deUra = (iso) => (iso ? hhmm(iso) : "—");
const deUraTs = (ts) => TIME_FMT.format(new Date(ts * 1000));
const deKm = (m) => `${st(m / 1000, 1)} km`;

function deMediana(a) {
  if (!a.length) return null;
  const s = [...a].sort((x, y) => x - y);
  return s[Math.floor(s.length / 2)];
}

function deOznaka(v) {
  if (v.mode === "bus" && v.network === "avtobus" && AGENCY[v.agency]) {
    return `${AGENCY[v.agency]} ${v.train_no}`;
  }
  return v.train_no || v.trip_id;
}

function deSmer(v) { return v.od && v.do ? `${v.od} – ${v.do}` : v.headsign || ""; }

function deHref(v) {
  const q = new URLSearchParams({ date: v.service_date, trip: v.trip_id });
  const pot = v.network === "avtobus" ? "/app/bus/" : "/app/train/";
  return `${pot}${encodeURIComponent(v.train_no)}?${q}`;
}

function dePovezava(dan, oznaka) {
  return `#deljenje/${dan || "danes"}${oznaka ? `/${oznaka}` : ""}`;
}

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
  return `<span class="de-zam" style="color:${delayColor(z)}">${escapeHtml(delayText(z, kratko))}</span>`;
}

function deIzid(izid) {
  const [ime] = DE_IZIDI[izid] || [izid];
  return `<span class="de-izid de-izid-${escapeHtml(izid)}">${escapeHtml(ime)}</span>`;
}

function deSklon(n, ena, dve, tri, pet) {
  const m = n % 100;
  return m === 1 ? ena : m === 2 ? dve : m === 3 || m === 4 ? tri : pet;
}

/** Vsa deljenja dneva, vsako s svojim vozilom; živa prva, nato najnovejša. */
function deVsa(d) {
  return d.vozila.flatMap((v) => v.deljenja.map((x) => ({ v, x })))
    .sort((a, b) => (b.x.izid === "deli") - (a.x.izid === "deli")
      || (b.x.zacetek || "").localeCompare(a.x.zacetek || ""));
}

function deNajdi(oznaka) {
  return de && de.podatki ? deVsa(de.podatki).find(({ x }) => x.oznaka === oznaka) : null;
}

/** Kje je vozilo na zemljevidu: po javnem stanju, sicer zadnja točka deljenja. */
function deLega(v) {
  if (v.javno && v.javno.lat != null) return [v.javno.lat, v.javno.lon];
  const d = [...v.deljenja].reverse().find((x) => x.lat != null);
  return d ? [d.lat, d.lon] : null;
}

// ------------------------------------------------------------------ glava in ploščice

function deGlava(d) {
  const danes = d.dan === d.danes;
  return `<div class="adm-hist de-glava">
    <div class="adm-korak">
      <button type="button" data-dan="${dodaj(d.dan, -1)}" ${d.dan <= d.prvi_dan ? "disabled" : ""} aria-label="prejšnji dan">‹</button>
      <button type="button" data-dan="danes" ${danes ? "disabled" : ""}>danes</button>
      <button type="button" data-dan="${dodaj(d.dan, 1)}" ${danes ? "disabled" : ""} aria-label="naslednji dan">›</button>
    </div>
    <input type="date" class="adm-datum" id="de-datum" value="${d.dan}" min="${d.prvi_dan}" max="${d.danes}">
    <h1>${escapeHtml(dolgi(d.dan))}</h1>
    <span class="adm-opomba">${danes
      ? "osveži se vsakih 10 s"
      : "pretekli dan: kaj so takrat videli potniki, se ne hrani, zato tu ni živega stanja"}</span>
  </div>`;
}

function deKpi(d) {
  const p = d.povzetek;
  const danes = d.dan === d.danes;
  const vsa = deVsa(d);
  const naj = [...vsa].sort((a, b) => b.x.trajanje_s - a.x.trajanje_s)[0];
  const odj = Object.entries(p.odjemalci || {}).sort((a, b) => b[1] - a[1])
    .map(([k, n]) => `${n} ${(DE_ODJEMALCI[k] || [k])[0]}`).join(" · ");
  const prvi = danes
    ? ploscica(st(p.deli_zdaj), "deli ta hip",
      p.vozil_zdaj ? `na ${st(p.vozil_zdaj)} ${deSklon(p.vozil_zdaj, "vozilu", "vozilih", "vozilih", "vozilih")}` : "nihče",
      p.deli_zdaj ? "je-poudarek" : "")
    : ploscica(st(p.vozil), "vozil", "z vsaj enim deljenjem");
  return `${prvi}
    ${ploscica(st(p.deljenj), "deljenj", escapeHtml(odj) || "&nbsp;")}
    ${ploscica(p.deljenj ? `${st(p.peljalo)} <small>od ${st(p.deljenj)}</small>` : "—", "se je peljalo",
      "šele takrat lega velja za vozilo")}
    ${ploscica(st(p.prehodov_javnih), "prehodov postaj",
      p.prehodov > p.prehodov_javnih ? `+${st(p.prehodov - p.prehodov_javnih)} od potnikov, ki se niso peljali` : "štejejo na tabli")}
    ${ploscica(p.trajanje_s ? trajanje(Math.max(60, p.trajanje_s)) : "—", "skupaj deljeno",
      p.deljenj ? `povprečno ${trajanje(Math.max(60, p.trajanje_s / p.deljenj))}` : "&nbsp;")}
    ${ploscica(naj ? trajanje(Math.max(60, naj.x.trajanje_s)) : "—", "najdaljše",
      naj ? escapeHtml(deOznaka(naj.v)) : "&nbsp;")}`;
}

// ------------------------------------------------------------------ seznam

function deKartica(d, { v, x }) {
  const izbran = de && de.izbrano === x.oznaka;
  const od = deKje(x.od), do_ = deKje(x.do);
  const pot = od ? `${od === do_ ? od : `${od} → ${do_}`}${x.km ? ` · ${st(x.km, 1)} km` : ""}` : "brez sprejete točke";
  const odj = (DE_ODJEMALCI[x.odjemalec] || [x.odjemalec || "?"])[0];
  const stevci = [
    trajanje(Math.max(60, x.trajanje_s)),
    `${st(x.prehodov)} ${deSklon(x.prehodov, "prehod", "prehoda", "prehodi", "prehodov")}`,
  ];
  return `<li><a class="de-k${x.izid === "deli" ? " je-zivo" : ""}${izbran ? " je-izbran" : ""}"
      href="${dePovezava(d.dan === d.danes ? null : d.dan, x.oznaka)}" data-oznaka="${escapeHtml(x.oznaka)}">
    <span class="de-k-vrh">
      <span class="de-k-ura">${deUra(x.zacetek)} – ${deUra(x.zadnja)}</span>
      ${deIzid(x.izid)}
    </span>
    <span class="de-k-ime"><b>${escapeHtml(deOznaka(v))}</b><span class="de-k-smer">${escapeHtml(deSmer(v))}</span></span>
    <span class="de-k-pot">${escapeHtml(pot)}</span>
    <span class="de-k-st">${escapeHtml(stevci.join(" · "))} · ${deZamuda(x.zamuda)} · ${escapeHtml(odj)}</span>
    ${x.peljal ? "" : `<span class="de-k-opoz">ni se peljal — lega ni štela za vozilo</span>`}
  </a></li>`;
}

function deSeznam(d) {
  if (!d.vklopljeno) return prazno("deljenje je izklopljeno (KAJROS_DELI=0)");
  const vsa = deVsa(d);
  if (!vsa.length) return prazno(d.dan === d.danes ? "danes še nihče ni delil lege" : "ta dan nihče ni delil lege");
  const izidi = Object.entries(d.povzetek.izidi).sort((a, b) => b[1] - a[1]);
  const f = de.filter && d.povzetek.izidi[de.filter] ? de.filter : null;
  const gumbi = izidi.length > 1 ? `<div class="de-filter" role="group" aria-label="izid">
    <button type="button" data-filter="" aria-pressed="${!f}">vsa <b>${vsa.length}</b></button>
    ${izidi.map(([k, n]) => `<button type="button" data-filter="${escapeHtml(k)}" aria-pressed="${f === k}">${escapeHtml((DE_IZIDI[k] || [k])[0])} <b>${n}</b></button>`).join("")}
  </div>` : "";
  const prikaz = f ? vsa.filter(({ x }) => x.izid === f) : vsa;
  return `${gumbi}<ul class="de-seznam" id="de-seznam">${prikaz.map((e) => deKartica(d, e)).join("")}</ul>`;
}

// ------------------------------------------------------------------ podrobnosti

function deDejstvo(ime, vrednost, razred = "") {
  return `<div class="${razred}"><dt>${escapeHtml(ime)}</dt><dd>${vrednost}</dd></div>`;
}

function dePodrobno(d) {
  const e = deNajdi(de.izbrano);
  if (!e) return prazno(deVsa(d).length ? "izberi deljenje na seznamu ali zemljevidu" : "ni deljenj");
  const { v, x } = e;
  const p = de.sled && de.sled.oznaka === x.oznaka ? de.sled : null;
  const [izidIme, izidOpis] = DE_IZIDI[x.izid] || [x.izid, ""];
  const odj = DE_ODJEMALCI[x.odjemalec];
  const hitrosti = p ? p.tocke.map((t) => t[4]).filter((h) => h != null) : [];
  const razmik = p && p.tocke.length > 1
    ? deMediana(p.tocke.slice(1).map((t, i) => t[0] - p.tocke[i][0])) : null;
  const peljalPo = x.peljal ? Math.round((new Date(x.peljal) - new Date(x.zacetek)) / 1000) : null;
  const j = v.javno;

  const javno = j ? `<div class="de-javno">
    <div class="de-javno-n">Vozilo zdaj, kot ga vidijo potniki</div>
    <div>${escapeHtml(potnikov(j.n))} · ${j.verodostojno
      ? `<b class="de-verodostojno">verodostojno</b> — tabla in zemljevid kažeta lego in zamudo po potniku`
      : `<b class="de-neverodostojno">ni verodostojno</b> — tabla kaže feed in poročilo potnika vsakega posebej`}</div>
    <div>${escapeHtml(deKje(j))}${j.stoji ? " · stoji" : ""} · zadnja točka ${escapeHtml(deStarost(j.starost_s))}</div>
    <div>zamuda po potniku ${deZamuda(j.zamuda)} · v feedu ${deZamuda(v.feed && v.feed.zamuda)}${v.gps
      ? ` · GPS avtobusa ${escapeHtml(deStarost(v.gps.starost_s))}` : ""}</div>
  </div>` : "";

  const prehodi = x.prehodi.length ? `<div class="adm-ovoj-t"><table class="adm-t de-prehodi">
    <thead><tr><th>postaja</th><th>prihod</th><th>odhod</th></tr></thead>
    <tbody>${x.prehodi.map((h) => `<tr><td class="de-postaja">${escapeHtml(h.ime)}</td>
      <td>${deCasPrehoda(h.prihod, h.prihod_vr, h.zamuda_prihod)}</td>
      <td>${deCasPrehoda(h.odhod, h.odhod_vr, h.zamuda_odhod)}</td></tr>`).join("")}
    </tbody></table></div>`
    : `<p class="de-p-pod">Vozilo ni prečkalo nobene postaje${x.km != null ? ` (prevoženih ${st(x.km, 1)} km)` : ""}.</p>`;

  return `<div class="de-p-glava">
      <div class="de-p-naslov">
        <h2>${escapeHtml(deOznaka(v))} <span>${escapeHtml(deSmer(v))}</span></h2>
        <div class="de-p-cas">${deUra(x.zacetek)} – ${deUra(x.zadnja)} · ${trajanje(Math.max(60, x.trajanje_s))}
          · ${deIzid(x.izid)} <span class="nic">${escapeHtml(izidOpis || izidIme)}</span></div>
      </div>
      <a class="adm-gumb de-p-odpri" href="${escapeHtml(deHref(v))}" target="_blank" rel="noopener">okno vožnje ↗</a>
    </div>
    ${javno}
    <dl class="de-dejstva">
      ${deDejstvo("začetek", `${deUraS(x.zacetek)} <span class="nic">${escapeHtml(deKje(x.od))}</span>`)}
      ${x.peljal ? deDejstvo("peljal se od", `${deUraS(x.peljal)}${peljalPo > 0 ? ` <span class="nic">po ${peljalPo < 90 ? `${peljalPo} s` : trajanje(peljalPo)}</span>` : ""}`)
        : deDejstvo("peljal se", "ne — lega ni štela za vozilo", "je-opoz")}
      ${deDejstvo("zadnja točka", `${deUraS(x.zadnja)} <span class="nic">${escapeHtml(deKje(x.do))}</span>`)}
      ${deDejstvo("zamuda ob zadnji točki", deZamuda(x.zamuda))}
      ${deDejstvo("prevozil", x.km != null ? `${st(x.km, 1)} km` : "—")}
      ${deDejstvo("točk", `${st(x.tock)}${razmik ? ` <span class="nic">na ${razmik} s</span>` : ""}`)}
      ${deDejstvo("natančnost", x.natancnost_m != null ? `povprečno ${st(x.natancnost_m)} m` : "—")}
      ${deDejstvo("odmik od trase", x.odmik_m != null ? `največ ${st(x.odmik_m)} m` : "—")}
      ${deDejstvo("hitrost (telefon)", hitrosti.length
        ? `mediana ${st(deMediana(hitrosti) * 3.6)} · največ ${st(Math.max(...hitrosti) * 3.6)} km/h`
        : x.hitrost_max_kmh != null ? `največ ${st(x.hitrost_max_kmh)} km/h` : "—")}
      ${deDejstvo("odjemalec", escapeHtml(odj ? odj[1] : x.odjemalec || "ni znan"))}
      ${deDejstvo("začel iz", escapeHtml(DE_VIRI[x.vir] || x.vir || "ni povedal"))}
    </dl>
    <h3 class="de-p-h">Graf vožnje</h3>
    <p class="de-p-pod"><span class="de-l de-l-sled"></span>potnik <span class="de-l de-l-prej"></span>preden se je peljal
      <span class="de-l de-l-vr"></span>vozni red · vodoravni razmik med črtama je zamuda, ravna črta je postanek</p>
    <div class="de-graf" id="de-graf">${p ? "" : prazno("nalagam točke …")}</div>
    <div class="de-odcitek" id="de-odcitek">${p && p.tocke.length > 1 ? "z miško ali prstom čez graf za posamezno točko" : "&nbsp;"}</div>
    <h3 class="de-p-h">Prehodi postaj <small>${x.peljal ? "štejejo na tabli kot opažanje" : "ne štejejo: potnik se ni peljal"}
      · prihod je vstop v ${st((p && p.na_postaji_m) || (v.network === "avtobus" ? 60 : 200))} m od postaje, odhod izstop na drugi strani</small></h3>
    ${prehodi}`;
}

function deCasPrehoda(iso, vr, z) {
  if (!iso) return `<span class="nic">—</span>`;
  return `<b class="de-ura-s">${deUraS(iso)}</b> <span class="de-vr">vozni red ${deUra(vr)} ${deZamuda(z, true)}</span>`;
}

// ------------------------------------------------------------------ graf vožnje

/** Kdaj bi bilo vozilo po voznem redu na razdalji `a` (s od epohe). */
function deVoznoredni(post, a) {
  if (!post.length) return null;
  if (a <= post[0].along_m) return post[0].odhod;
  for (let i = 0; i + 1 < post.length; i += 1) {
    const s = post[i], n = post[i + 1];
    if (a <= n.along_m) {
      if (n.along_m <= s.along_m) return s.odhod;
      return s.odhod + (a - s.along_m) / (n.along_m - s.along_m) * (n.prihod - s.odhod);
    }
  }
  return post[post.length - 1].prihod;
}

function deKjeNaGrafu(post, a, r) {
  if (!post.length) return "";
  const naj = post.reduce((b, s) => (Math.abs(s.along_m - a) < Math.abs(b.along_m - a) ? s : b));
  if (Math.abs(naj.along_m - a) <= r) return `pri ${naj.ime}`;
  const za = [...post].reverse().find((s) => s.along_m <= a);
  const pred = post.find((s) => s.along_m > a);
  return za && pred ? `med ${za.ime} in ${pred.ime}` : "";
}

function deGraf(x, p, sirina) {
  const T = p.tocke;
  if (T.length < 2) return { svg: prazno("premalo točk za graf"), opomba: "" };
  const ozko = sirina < 560;
  const W = Math.max(280, sirina), H = ozko ? 250 : 300;
  const L = ozko ? 86 : 150, R = ozko ? 52 : 64, Z = 12, S = 26;
  const post = p.postanki;
  let a0 = Math.min(...T.map((t) => t[1])), a1 = Math.max(...T.map((t) => t[1]));
  const pa = Math.max(120, (a1 - a0) * 0.08);
  a0 -= pa; a1 += pa;
  let t0 = T[0][0], t1 = T[T.length - 1][0];
  // Vozni red na grafu, kadar ga ne stisne: pri uri zamude in treh minutah
  // deljenja bi bile točke ena navpična črta.
  const vr0 = deVoznoredni(post, a0 + pa), vr1 = deVoznoredni(post, a1 - pa);
  let opomba = "";
  if (vr0 != null) {
    const e0 = Math.min(t0, vr0, vr1), e1 = Math.max(t1, vr0, vr1);
    if (e1 - e0 <= Math.max(2.5 * (t1 - t0), 1200)) { t0 = e0; t1 = e1; }
    else opomba = `vozni red je ${trajanje(Math.abs(t0 - vr0))} ${vr0 < t0 ? "prej" : "pozneje"} — zunaj grafa`;
  }
  const pt = Math.max(30, (t1 - t0) * 0.03);
  t0 -= pt; t1 += pt;
  const X = (t) => L + (t - t0) / (t1 - t0) * (W - L - R);
  const Y = (a) => Z + (1 - (a - a0) / (a1 - a0)) * (H - Z - S);
  const f = (n) => n.toFixed(1);

  const deli = [];
  deli.push(`<clipPath id="de-graf-rez"><rect x="${L}" y="${Z}" width="${W - L - R}" height="${H - Z - S}"/></clipPath>`);
  // Časovna os: korak, ki da največ eno oznako na 90 pik.
  const koraki = [60, 120, 300, 600, 900, 1800, 3600, 7200, 10800];
  const korak = koraki.find((k) => (t1 - t0) / k <= (W - L - R) / (ozko ? 64 : 90)) || 21600;
  for (let t = Math.ceil(t0 / korak) * korak; t <= t1; t += korak) {
    deli.push(`<line class="mreza" x1="${f(X(t))}" x2="${f(X(t))}" y1="${Z}" y2="${H - S}"/>`,
      `<text class="os" x="${f(X(t))}" y="${H - S + 16}" text-anchor="middle">${deUraTs(t)}</text>`);
  }
  // Postaje: črta vsaka, ime samo, kadar ne leže na prejšnje.
  let zadnjiY = -99;
  for (const s of post) {
    if (s.along_m < a0 || s.along_m > a1) continue;
    const y = Y(s.along_m);
    deli.push(`<line class="postaja" x1="${L}" x2="${W - R}" y1="${f(y)}" y2="${f(y)}"/>`);
    if (Math.abs(y - zadnjiY) >= 13) {
      const n = ozko ? 12 : 21;
      const ime = s.ime.length > n ? `${s.ime.slice(0, n - 1)}…` : s.ime;
      deli.push(`<text class="ime" x="${L - 8}" y="${f(y + 4)}" text-anchor="end"><title>${escapeHtml(s.ime)}</title>${escapeHtml(ime)}</text>`);
      zadnjiY = y;
    }
  }
  // Vozni red: prihod in odhod na vsaki postaji, vmes ravno.
  if (post.length) {
    const vr = post.flatMap((s) => [[s.prihod, s.along_m], [s.odhod, s.along_m]]);
    deli.push(`<polyline class="vr" clip-path="url(#de-graf-rez)" points="${vr.map(([t, a]) => `${f(X(t))},${f(Y(a))}`).join(" ")}"/>`);
  }
  // Potnik: kos za kosom, pretrgan na vrzelih; pred „peljal se" bledo.
  const peljal = x.peljal ? new Date(x.peljal).getTime() / 1000 : Infinity;
  let kos = [], prej = null;
  const konec = () => {
    if (kos.length > 1) deli.push(`<polyline class="sled${prej ? " je-prej" : ""}" clip-path="url(#de-graf-rez)" points="${kos.join(" ")}"/>`);
    else if (kos.length === 1) deli.push(`<circle class="sled-pika${prej ? " je-prej" : ""}" cx="${kos[0].split(",")[0]}" cy="${kos[0].split(",")[1]}" r="2"/>`);
  };
  T.forEach((t, i) => {
    const xy = `${f(X(t[0]))},${f(Y(t[1]))}`;
    const jePrej = t[0] < peljal;
    const vrzel = i > 0 && t[0] - T[i - 1][0] > DE_VRZEL_S;
    if (i > 0 && (vrzel || jePrej !== prej)) {
      konec();
      kos = vrzel ? [] : [kos[kos.length - 1]];
    }
    prej = jePrej;
    kos.push(xy);
  });
  konec();
  for (const h of x.prehodi) {
    if (h.along_m == null) continue;
    for (const [iso, razred] of [[h.prihod, "prihod"], [h.odhod, "odhod"]]) {
      if (iso) deli.push(`<circle class="prehod je-${razred}" cx="${f(X(new Date(iso).getTime() / 1000))}" cy="${f(Y(h.along_m))}" r="4"/>`);
    }
  }
  const z = T[T.length - 1];
  if (x.zamuda) {
    deli.push(`<text class="zam" x="${f(X(z[0]) + 8)}" y="${f(Y(z[1]) + 4)}" fill="${delayColor(x.zamuda)}">${escapeHtml(delayText(x.zamuda))}</text>`);
  }
  deli.push(`<g class="kazalec" id="de-kazalec" visibility="hidden"><line y1="${Z}" y2="${H - S}"/><circle r="5"/></g>`,
    `<rect class="dotik" x="${L}" y="${Z}" width="${W - L - R}" height="${H - Z - S}"/>`);
  return {
    svg: `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="graf vožnje: čas proti legi na trasi">${deli.join("")}</svg>`,
    opomba, X, Y, t0, t1, L, R, W,
  };
}

function deRisiGraf() {
  const ovoj = el("de-graf");
  const e = deNajdi(de && de.izbrano);
  if (!ovoj || !e || !de.sled || de.sled.oznaka !== e.x.oznaka) return;
  const g = deGraf(e.x, de.sled, ovoj.clientWidth);
  ovoj.innerHTML = g.svg + (g.opomba ? `<div class="de-graf-opomba">${escapeHtml(g.opomba)}</div>` : "");
  const svg = ovoj.querySelector("svg");
  if (!svg || !g.X) return;
  const T = de.sled.tocke, post = de.sled.postanki, r = de.sled.na_postaji_m || 100;
  const kaz = svg.querySelector("#de-kazalec");
  const odc = el("de-odcitek");
  const pokazi = (ev) => {
    const okvir = svg.getBoundingClientRect();
    const t = g.t0 + (ev.clientX - okvir.left - g.L) / (g.W - g.L - g.R) * (g.t1 - g.t0);
    let lo = 0, hi = T.length - 1;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (T[m][0] <= t) lo = m; else hi = m; }
    const tk = Math.abs(T[lo][0] - t) <= Math.abs(T[hi][0] - t) ? T[lo] : T[hi];
    const cx = g.X(tk[0]), cy = g.Y(tk[1]);
    kaz.setAttribute("visibility", "visible");
    kaz.querySelector("line").setAttribute("x1", cx);
    kaz.querySelector("line").setAttribute("x2", cx);
    kaz.querySelector("circle").setAttribute("cx", cx);
    kaz.querySelector("circle").setAttribute("cy", cy);
    const deli = [`<b>${DE_URA_S.format(new Date(tk[0] * 1000))}</b>`, escapeHtml(deKjeNaGrafu(post, tk[1], r)),
      `${deKm(tk[1])} od začetka trase`];
    if (tk[4] != null) deli.push(`${st(tk[4] * 3.6)} km/h`);
    if (tk[3] != null) deli.push(`natančnost ${st(tk[3])} m`);
    deli.push(`odmik ${st(tk[2])} m`);
    if (tk[0] < (e.x.peljal ? new Date(e.x.peljal).getTime() / 1000 : Infinity)) deli.push("preden se je peljal");
    odc.innerHTML = deli.filter(Boolean).join(" · ");
  };
  const dotik = svg.querySelector(".dotik");
  dotik.addEventListener("pointermove", pokazi);
  dotik.addEventListener("pointerdown", pokazi);
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
  for (const id of ["de-trase", "de-sledi", "de-prehodi", "de-konci", "de-gps", "de-vozila"]) {
    map.addSource(id, { type: "geojson", data: PK_PRAZNO });
  }
  const okroglo = { "line-join": "round", "line-cap": "round" };
  const izbrano = ["==", ["get", "izbrano"], true];
  // Črtkana, ker je polna siva črta med cestami podlage izginila.
  map.addLayer({ id: "de-trase", type: "line", source: "de-trase",
                 layout: { "line-join": "round", "line-cap": "butt" },
                 paint: { "line-color": DE_TRASA, "line-width": 2.5, "line-dasharray": [2, 1.5],
                          "line-opacity": 0.9 } });
  map.addLayer({ id: "de-sledi-druge", type: "line", source: "de-sledi", layout: okroglo,
                 filter: ["!", izbrano],
                 paint: { "line-color": DE_DRUGA, "line-width": 3, "line-opacity": 0.75 } });
  map.addLayer({ id: "de-sledi-obroba", type: "line", source: "de-sledi", layout: okroglo,
                 filter: izbrano,
                 paint: { "line-color": "#0f1115", "line-width": 10, "line-opacity": 0.8 } });
  map.addLayer({ id: "de-sledi", type: "line", source: "de-sledi", layout: okroglo,
                 filter: izbrano,
                 paint: { "line-color": ME_COLOR, "line-width": 6 } });
  map.addLayer({ id: "de-prehodi", type: "circle", source: "de-prehodi",
                 paint: { "circle-radius": 5, "circle-color": "#0f1115",
                          "circle-stroke-width": 2.5, "circle-stroke-color": "#e7eaf0" } });
  map.addLayer({ id: "de-prehodi-imena", type: "symbol", source: "de-prehodi",
                 layout: { "text-field": ["get", "ime"], "text-font": ["Noto Sans Regular"],
                           "text-size": 12, "text-anchor": "left", "text-offset": [0.9, 0],
                           "text-optional": true },
                 paint: { "text-color": "#c3cad6", "text-halo-color": "#0f1115", "text-halo-width": 1.6 } });
  map.addLayer({ id: "de-konci", type: "circle", source: "de-konci",
                 paint: {
                   "circle-radius": ["case", izbrano, 7, 4.5],
                   "circle-color": ["case", ["==", ["get", "vrsta"], "zacetek"], "#0f1115",
                                    izbrano, ME_COLOR, DE_DRUGA],
                   "circle-stroke-width": ["case", izbrano, 2.5, 1.5],
                   "circle-stroke-color": ["case", izbrano, "#ffffff", "#0f1115"],
                 } });
  map.addLayer({ id: "de-konci-imena", type: "symbol", source: "de-konci",
                 filter: izbrano,
                 layout: { "text-field": ["get", "napis"], "text-font": ["Noto Sans Bold"],
                           "text-size": 12, "text-anchor": "right", "text-offset": [-1.1, 0] },
                 paint: { "text-color": "#e7eaf0", "text-halo-color": "#0f1115", "text-halo-width": 1.8 } });
  map.addLayer({ id: "de-gps", type: "circle", source: "de-gps",
                 paint: { "circle-radius": 7, "circle-color": "transparent",
                          "circle-stroke-width": 2.5, "circle-stroke-color": LINE_INK,
                          "circle-pitch-alignment": "map" } });
  map.addLayer({ id: "de-vozila", type: "circle", source: "de-vozila",
                 paint: { "circle-radius": 9, "circle-color": ["get", "barva"],
                          "circle-stroke-width": 3, "circle-stroke-color": "#ffffff",
                          "circle-pitch-alignment": "map" } });
  map.addLayer({ id: "de-vozila-imena", type: "symbol", source: "de-vozila",
                 layout: { "text-field": ["get", "oznaka"], "text-font": ["Noto Sans Bold"],
                           "text-size": 13, "text-anchor": "left", "text-offset": [1.2, 0] },
                 paint: { "text-color": "#e7eaf0", "text-halo-color": "#0f1115", "text-halo-width": 1.8 } });
  for (const sloj of ["de-sledi-druge", "de-sledi", "de-konci"]) {
    map.on("click", sloj, (e) => {
      const f = e.features && e.features[0];
      if (f && f.properties.oznaka) location.hash = dePovezava(deDanVNaslovu(), f.properties.oznaka);
    });
    map.on("mouseenter", sloj, () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", sloj, () => { map.getCanvas().style.cursor = ""; });
  }
  de.k = { map, ml };
  if (de.podatki) deNaKarto(de.podatki);
}

function deNaKarto(d) {
  if (!de.k) return;
  const { map } = de.k;
  const trase = [], sledi = [], prehodi = [], konci = [], gps = [], vozila = [];
  for (const v of d.vozila) {
    const zivo = !!v.javno;
    for (const kos of v.trasa) trase.push(pkCrta(kos, {}));
    for (const x of v.deljenja) {
      const izb = x.oznaka === de.izbrano;
      for (const kos of x.sled) sledi.push(pkCrta(kos, { oznaka: x.oznaka, izbrano: izb }));
      // Deljenje z eno samo točko nima sledi, ima pa lego.
      const kosi = x.sled.filter((k) => k.length);
      const zadnji = kosi.length ? kosi[kosi.length - 1].slice(-1)[0] : x.lat != null ? [x.lat, x.lon] : null;
      if (zadnji) {
        const prvi = kosi.length ? kosi[0][0] : null;
        // Živo vozilo ima svojo piko z imenom; drugi napis bi legel nanjo.
        konci.push(pkTocka(zadnji, { oznaka: x.oznaka, izbrano: izb, vrsta: "konec",
                                    napis: x.izid === "deli" ? "" : `${deUra(x.zadnja)} · ${(DE_IZIDI[x.izid] || [x.izid])[0]}` }));
        if (izb && prvi) konci.push(pkTocka(prvi, { oznaka: x.oznaka, izbrano: true, vrsta: "zacetek",
                                            napis: `začetek ${deUra(x.zacetek)}` }));
      }
      if (izb) for (const h of x.prehodi) prehodi.push(pkTocka([h.lat, h.lon], { ime: h.ime }));
    }
    if (zivo && v.gps) gps.push(pkTocka([v.gps.lat, v.gps.lon], {}));
    const ll = zivo && deLega(v);
    if (ll) {
      vozila.push(pkTocka(ll, {
        oznaka: v.javno.n > 1 ? `${deOznaka(v)} · ${v.javno.n}` : deOznaka(v),
        barva: delayColor(v.javno.zamuda),
      }));
    }
  }
  pkVir(map, "de-trase", trase);
  pkVir(map, "de-sledi", sledi);
  pkVir(map, "de-prehodi", prehodi);
  pkVir(map, "de-konci", konci);
  pkVir(map, "de-gps", gps);
  pkVir(map, "de-vozila", vozila);
  // Pogled se postavi ob izbiri, ne ob vsakih novih podatkih: sicer bi
  // zemljevid na deset sekund trgal izpod rok (isto pravilo kot v oknu vožnje).
  if (de.pogled !== de.izbrano) {
    const e = deNajdi(de.izbrano);
    const tocke = e ? [...e.x.sled.flat(), ...e.x.prehodi.map((h) => [h.lat, h.lon])] : [];
    if (!tocke.length && e) { const ll = e.x.lat != null ? [e.x.lat, e.x.lon] : deLega(e.v); if (ll) tocke.push(ll); }
    if (tocke.length) {
      pkPrilagodi(map, tocke, { maxZoom: 14, padding: 70, duration: de.pogled == null ? 0 : 600 });
      de.pogled = de.izbrano;
    } else if (de.pogled == null && sledi.length) {
      pkPrilagodi(map, sledi.flatMap((s) => s.geometry.coordinates.map(([lo, la]) => [la, lo])),
        { maxZoom: 12, padding: 60, duration: 0 });
      de.pogled = de.izbrano;
    }
  }
}

// ------------------------------------------------------------------ lijak

// Lijak po dnevih (`deljenje.lijak`): kje se ljudje ustavijo. Iskanje je
// ena zahteva po kandidatih (tudi „Poišči znova“), ne en človek.
const DE_LIJAK = [
  ["kandidati", "iskanj z vozilom"],
  ["kandidati:0", "brez vozila"],
  ["zacetek", "začetkov"],
  ["zavrnjen", "zavrnjenih"],
  ["peljal", "peljalo se"],
];

function deLijak(d) {
  const dnevi = d.lijak || [];
  if (!dnevi.length) return prazno("v zadnjih dveh tednih nihče ni iskal vozila");
  // Začetki in zavrnitve so razrezani (`zacetek:android`, `zavrnjen:ni_tu`):
  // v celici vsota, pod njo razrez -- oblaček se na telefonu ne odpre.
  const razrez = (x, k) => Object.entries(x).filter(([dd]) => dd.startsWith(`${k}:`))
    .sort((a, b) => b[1] - a[1]);
  const ime = (k, del) => (k === "zacetek" ? (DE_ODJEMALCI[del] || [del])[0] : DE_ZAVRNITVE[del] || del);
  const celica = (x, k) => {
    const deli = k === "zacetek" || k === "zavrnjen" ? razrez(x, k) : [];
    const n = deli.length ? deli.reduce((a, [, m]) => a + m, 0) : x[k] || 0;
    const pod = deli.map(([dd, m]) => `${escapeHtml(ime(k, dd.slice(k.length + 1)))} ${m}`).join(" · ");
    return `<td class="n">${n ? st(n) : `<span class="nic">0</span>`}${pod ? `<div class="de-razrez">${pod}</div>` : ""}</td>`;
  };
  return `<div class="adm-ovoj-t"><table class="adm-t de-lijak">
    <thead><tr><th>dan</th>${DE_LIJAK.map(([, i]) => `<th class="n">${i}</th>`).join("")}</tr></thead>
    <tbody>${dnevi.map(({ dan, dogodki: x }) => `<tr${dan === d.dan ? ` class="je-izbran"` : ""}>
      <td class="de-cas"><a href="${dePovezava(dan === d.danes ? null : dan)}">${escapeHtml(`${DNI_TEDNA[izIso(dan).getDay()]} ${kratki(dan)}`)}</a></td>
      ${DE_LIJAK.map(([k]) => celica(x, k)).join("")}</tr>`).join("")}
    </tbody></table></div>`;
}

// ------------------------------------------------------------------ okvir

function deOkvir() {
  return `<div id="de-glava"></div>
  <div class="adm-mreza de-mreza">
    <div class="adm-kpi" id="de-kpi"></div>
    <section class="adm-plosca s4 de-plosca-seznam">
      <h2>Deljenja <small>vsako je en telefon na eni vožnji · živa na vrhu</small></h2>
      <div id="de-vozila"></div>
    </section>
    <div class="s8 de-desno">
      <section class="adm-plosca de-plosca-karta">
        <div class="de-karta" id="de-karta"></div>
        <div class="de-legenda">
          <span><i class="de-l de-l-sled"></i>izbrano deljenje</span>
          <span><i class="de-l de-l-druga"></i>druga deljenja</span>
          <span><i class="de-l de-l-postaja"></i>postaja, ki jo je prečkal</span>
          <span><i class="de-l de-l-trasa"></i>trasa vozila, kjer kdo deli zdaj</span>
          <span><i class="de-l de-l-gps"></i>GPS avtobusa iz feeda</span>
        </div>
        <p class="adm-pod">Sled je del trase med prvo in zadnjo sprejeto točko: surovih koordinat ne hranimo. Pika s polnim belim robom je vozilo, kot ga vidijo potniki, barva je zamuda.</p>
      </section>
      <section class="adm-plosca de-podrobno" id="de-podrobno"></section>
    </div>
    <section class="adm-plosca s12">
      <h2>Lijak <small>zadnjih 14 dni · klik na dan odpre njegova deljenja</small></h2>
      <p class="adm-pod">Iskanje je ena zahteva po vozilih v bližini, ne en človek. „Peljalo se“: deljenje, ki je doseglo hitrost vozila — šele od tod lega enega potnika velja za vozilo.</p>
      <div id="de-lijak"></div>
    </section>
  </div>`;
}

// ------------------------------------------------------------------ življenje

/** `#deljenje/2026-10-11/<oznaka>`; „danes" in prazno sta isto. */
function deIzNaslova() {
  const [, dan, oznaka] = location.hash.slice(1).split("/");
  return {
    dan: /^\d{4}-\d{2}-\d{2}$/.test(dan || "") ? dan : null,
    izbrano: /^[0-9a-f]{12}$/.test(oznaka || "") ? oznaka : null,
  };
}

function deDanVNaslovu() { return de && de.dan; }

async function deNalozi() {
  const q = new URLSearchParams();
  if (de.dan) q.set("dan", de.dan);
  if (de.izbrano) q.set("izbrano", de.izbrano);
  const moj = ++de.st;
  const r = await fetch(`/admin/deljenje${q.toString() ? `?${q}` : ""}`, { credentials: "same-origin" });
  if (!r.ok) throw new Error(r.status === 403 ? "Napačen žeton." : `strežnik: ${r.status}`);
  const d = await r.json();
  // Med čakanjem je skrbnik izbral drugo ali zaprl zavihek: odgovor ni več njegov.
  if (!de || moj !== de.st) return;
  de.podatki = d;
  de.nalozeno = `${d.dan}|${de.izbrano}`;
  if (d.podrobno) de.sled = d.podrobno;
  if (!deNajdi(de.izbrano)) {
    // Brez izbire (ali izbira z drugega dne): živo deljenje, sicer najnovejše.
    const prvo = deVsa(d)[0];
    if (prvo) {
      de.izbrano = prvo.x.oznaka;
      history.replaceState(null, "", dePovezava(de.dan, de.izbrano));
      deRisi();
      await deNalozi();
      return;
    }
  }
  deRisi();
}

function deRisi() {
  const d = de.podatki;
  if (!d) return;
  if (de.glava !== `${d.dan}|${d.prvi_dan}|${d.danes}`) {
    el("de-glava").innerHTML = deGlava(d);
    de.glava = `${d.dan}|${d.prvi_dan}|${d.danes}`;
  }
  el("de-kpi").innerHTML = deKpi(d);
  el("de-vozila").innerHTML = deSeznam(d);
  el("de-lijak").innerHTML = deLijak(d);
  // Podrobnosti se prepišejo samo, kadar se je kaj spremenilo: sicer bi
  // odčitek grafa pod prstom na deset sekund izginil.
  const e = deNajdi(de.izbrano);
  const odtis = JSON.stringify([de.izbrano, e && e.x, e && e.v.javno, e && e.v.feed, de.sled && de.sled.oznaka,
    de.sled && de.sled.tocke.length]);
  if (odtis !== de.odtis) {
    el("de-podrobno").innerHTML = dePodrobno(d);
    de.odtis = odtis;
    deRisiGraf();
  }
  if (d.dan === d.danes) {
    el("deljenje-znacka").hidden = !d.povzetek.deli_zdaj;
    el("deljenje-znacka").textContent = d.povzetek.deli_zdaj ? String(d.povzetek.deli_zdaj) : "";
  }
  deNaKarto(d);
}

/** Naslov se je spremenil (klik na kartico, dan, nazaj): sledi mu. */
function deSledi() {
  const { dan, izbrano } = deIzNaslova();
  const danSpremenjen = dan !== de.dan;
  if (!danSpremenjen && izbrano === de.izbrano) return;
  de.dan = dan;
  de.izbrano = izbrano;
  if (danSpremenjen) { de.podatki = null; de.filter = null; de.pogled = null; }
  if (de.podatki) deRisi();
  // Na ozkem zaslonu je zemljevid nad seznamom ali pod njim: kartica, ki jo
  // je kdo pritisnil, mora pokazati, kaj je izbrala.
  if (de.skoci) {
    de.skoci = false;
    if (matchMedia("(max-width: 1100px)").matches) {
      el("de-karta").scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }
  deNalozi().catch((e) => pokaziNapako(`Deljenja ni bilo mogoče naložiti — ${e.message}`));
}

/** Odpre zavihek v `koren`; če je že odprt, le sledi naslovu. */
function deljenjeOdpri(koren) {
  if (de && el("de-karta") && koren.contains(el("de-karta"))) { deSledi(); return; }
  deljenjeZapri();
  koren.innerHTML = deOkvir();
  const { dan, izbrano } = deIzNaslova();
  de = { koren, k: null, poll: null, podatki: null, sled: null, dan, izbrano, filter: null,
         pogled: null, st: 0, nalozeno: null, glava: null, odtis: null, skoci: false, velikost: null };
  // Vsebina se prepiše na deset sekund, poslušalci pa so na korenu in preživijo.
  koren.addEventListener("click", deKlik);
  koren.addEventListener("change", deSprememba);
  de.velikost = () => {
    clearTimeout(de.velikostT);
    de.velikostT = setTimeout(() => { if (de) deRisiGraf(); }, 150);
  };
  addEventListener("resize", de.velikost);
  // Napako pobriše samo, če je bila njegova: opozorilo pregleda (štetje
  // izklopljeno) ni njegovo.
  let napaka = false;
  de.poll = pollWhileVisible(async () => {
    // Pretekli dan se ne spreminja: ko je naložen, ni česa osveževati.
    if (de.podatki && de.podatki.dan !== de.podatki.danes && de.nalozeno === `${de.podatki.dan}|${de.izbrano}`) return;
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
  const dan = e.target.closest("button[data-dan]");
  if (dan) {
    const cilj = dan.dataset.dan;
    location.hash = dePovezava(cilj === "danes" || cilj === (de.podatki && de.podatki.danes) ? null : cilj);
    return;
  }
  const f = e.target.closest("button[data-filter]");
  if (f) {
    de.filter = f.dataset.filter || null;
    el("de-vozila").innerHTML = deSeznam(de.podatki);
    return;
  }
  if (e.target.closest("a.de-k")) de.skoci = true;
}

function deSprememba(e) {
  if (e.target.id === "de-datum" && e.target.value) {
    const d = de.podatki;
    location.hash = dePovezava(d && e.target.value === d.danes ? null : e.target.value);
  }
}

function deljenjeZapri() {
  if (!de) return;
  if (de.poll) de.poll.stop();
  de.koren.removeEventListener("click", deKlik);
  de.koren.removeEventListener("change", deSprememba);
  removeEventListener("resize", de.velikost);
  if (de.k) de.k.map.remove();
  de = null;
}
