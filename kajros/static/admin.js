"use strict";

// Pregled za skrbnika: kdo je bil na strani in ali stroj dela.
//
// Vse pride iz enega klica `/admin/podatki`. Ena zahteva in ne šest: stran
// odpre en človek nekajkrat na dan, zato je vsaka delitev na endpointe samo
// več kode in več priložnosti, da se dve številki razideta.
//
// Kar je na tej strani najlažje narobe prebrati, je vsota dnevnih
// obiskovalcev. Sol se vsak dan zavrže (glej `obisk.py`), zato ista oseba v
// tridesetih dneh šteje tridesetkrat -- številka je zato povsod označena kot
// „obiskov", ne kot „ljudi", razen za en sam dan.

const el = (id) => document.getElementById(id);

let dni = 30;

function stevilo(n) {
  return (n == null ? 0 : n).toLocaleString("sl-SI");
}

function bajti(b) {
  if (b == null) return "—";
  const e = ["B", "kB", "MB", "GB", "TB"];
  let i = 0;
  while (b >= 1024 && i < e.length - 1) { b /= 1024; i += 1; }
  return `${num(b, b < 10 && i > 0 ? 1 : 0)} ${e[i]}`;
}

function trajanje(s) {
  if (s == null) return "—";
  if (s < 3600) return `${Math.round(s / 60)} min`;
  if (s < 86400) return `${num(s / 3600, 1)} h`;
  return `${num(s / 86400, 1)} dni`;
}

/** Odzivni čas je razred, ne vrednost -- povej to z znakom, ne z videzom. */
function razredMs(p) {
  if (!p || !p.n) return "—";
  return p.do == null ? "› 5 s" : `‹ ${p.do} ms`;
}

/** Ena vrstica s stolpcem. Isti gradnik kot na strani „kdaj se splača". */
function vrstica(ime, vrednost, delezOd, desno, barva) {
  const delez = delezOd > 0 ? Math.max(2, Math.min(100, (vrednost / delezOd) * 100)) : 2;
  return `<div class="stat-vrsta">
    <div class="stat-ime" title="${escapeHtml(ime)}">${escapeHtml(ime)}</div>
    <div class="stat-tir">
      <div class="stat-stolpec" style="width:${delez.toFixed(1)}%;background:${barva || "var(--accent)"}"></div>
    </div>
    <div class="stat-vrednost">${stevilo(vrednost)}</div>
    <div class="stat-n">${desno == null ? "" : escapeHtml(String(desno))}</div>
  </div>`;
}

function prazno(kaj) {
  return `<div class="empty-state">${escapeHtml(kaj)}</div>`;
}

// ------------------------------------------------------------------ prikaz

function ploscice(d) {
  const danes = d.danes || {};
  const s = d.skupaj || {};
  // Delež botov pove, koliko od tega sploh so ljudje. Brez njega je „120
  // obiskovalcev" lahko en sam iskalnik, ki je prišel stokrat z drugega IP.
  const botDelez = (s.ljudi_vsota + s.botov_vsota) > 0
    ? Math.round(100 * s.botov_vsota / (s.ljudi_vsota + s.botov_vsota)) : 0;
  // Obdobje je vedno 7, 30 ali 90 -- zato „dneh" in nobenega sklanjanja.
  // Prva različica je pisala „v 1 dneh", ker je štela dneve s podatkom in ne
  // izbranega okna; številka je bila prava, poved pa pokvarjena.
  const kart = [
    ["je-poudarek", stevilo(danes.ljudi), "različnih danes",
     `${stevilo(danes.ogledov)} ogledov strani`],
    ["", stevilo(s.ljudi_vsota), `obiskov v ${d.dni} dneh`,
     "vsota dnevnih, ne različnih ljudi"],
    ["", stevilo(s.ogledov), "ogledov strani",
     `od ${stevilo(s.zahtev)} zahtev skupaj`],
    ["", `${botDelez} %`, "od tega botov",
     `${stevilo(s.botov_vsota)} strojnih obiskov`],
    [s.napak5 > 0 ? "je-poudarek" : "", stevilo(s.napak5), "napak strežnika",
     `${stevilo(s.napak4)} × 4xx (napačen naslov)`],
  ];
  el("ploscice").innerHTML = kart.map(([razred, st, ime, pod]) =>
    `<div class="adm-ploscica ${razred}">
       <span class="adm-st">${escapeHtml(String(st))}</span>
       <span class="adm-ime">${escapeHtml(ime)}</span>
       <span class="adm-pod">${escapeHtml(pod)}</span>
     </div>`).join("");
}

function poDnevih(d) {
  const vrstice = d.po_dnevih || [];
  if (!vrstice.length) { el("po-dnevih").innerHTML = prazno("še nič zajetega"); return; }
  const naj = Math.max(...vrstice.map((v) => v.ljudi), 1);
  // `dayLabel` in ne surovi ISO datum: „2026-09-12" se je v stolpcu z imeni
  // rezal na „2026-09…", torej je bila odrezana prav tista polovica, ki
  // vrstico loči od sosednje.
  // Od zadaj: zadnji dan je tisti, zaradi katerega stran odpreš.
  el("po-dnevih").innerHTML = vrstice.slice().reverse()
    .map((v) => vrstica(dayLabel(v.dan), v.ljudi, naj, `${stevilo(v.ogledov)}×`)).join("");
}

function strani(d) {
  const vrstice = (d.strani || []).filter((v) => v.zahtev > 0);
  if (!vrstice.length) { el("strani").innerHTML = prazno("nobene odprte strani"); return; }
  const naj = Math.max(...vrstice.map((v) => v.ljudi), 1);
  el("strani").classList.add("dolge-oznake");
  el("strani").innerHTML = vrstice
    .map((v) => vrstica(v.pot, v.ljudi, naj, `${stevilo(v.zahtev)}×`)).join("");
}

function razrezi(d) {
  const r = d.razrezi || {};
  // **Vseh 24 ur, tudi praznih.** Sicer je ura z edinim obiskom videti kot
  // edina ura, ki obstaja, in iz slike ni mogoče videti, da so ostale ničle
  // in ne manjkajoč podatek.
  const poUri = new Map((r.ura || []).map((v) => [v.kljuc, v.zahtev]));
  const najU = Math.max(...poUri.values(), 1);
  el("ure").innerHTML = Array.from({ length: 24 }, (_, h) => {
    const k = String(h).padStart(2, "0");
    return vrstica(`${k}:00`, poUri.get(k) || 0, najU, null);
  }).join("");

  const nap = r.naprava || [];
  const najN = Math.max(...nap.map((v) => v.zahtev), 1);
  el("naprave").innerHTML = nap.length
    ? nap.map((v) => vrstica(v.kljuc, v.zahtev, najN, `${stevilo(v.ogledov)}×`)).join("")
    : prazno("še ni obiska");

  // „??" pomeni, da glave o državi ni bilo -- torej zahteva ni prišla skozi
  // Cloudflare, ampak iz domačega omrežja. To ni neznanka, ampak podatek.
  const drz = (r.drzava || []).map((v) => ({ ...v, ime: v.kljuc === "??" ? "domače" : v.kljuc }));
  const najD = Math.max(...drz.map((v) => v.zahtev), 1);
  el("drzave").innerHTML = drz.length
    ? drz.slice(0, 10).map((v) => vrstica(v.ime, v.zahtev, najD, null)).join("")
    : "";
}

function endpointi(d) {
  const vrstice = d.endpointi || [];
  if (!vrstice.length) { el("endpointi").innerHTML = ""; return; }
  const celica = (v, razred) => `<td class="${razred || ""}">${v}</td>`;
  el("endpointi").innerHTML = `
    <thead><tr>
      <th>pot</th><th>zahtev</th><th>mediana</th><th>p95</th>
      <th>najdlje</th><th>4xx</th><th>5xx</th>
    </tr></thead>
    <tbody>${vrstice.map((v) => `
      <tr class="${v.napak5 > 0 ? "je-slaba" : ""}">
        ${celica(escapeHtml(v.pot))}
        ${celica(stevilo(v.zahtev))}
        ${celica(razredMs(v.p50))}
        ${celica(razredMs(v.p95), v.p95 && v.p95.do == null ? "adm-mlacno" : "")}
        ${celica(`${stevilo(Math.round(v.ms_naj))} ms`,
                 v.ms_naj > 5000 ? "adm-mlacno" : "")}
        ${celica(stevilo(v.napak4), v.napak4 ? "" : "adm-nic")}
        ${celica(stevilo(v.napak5), v.napak5 ? "adm-slabo" : "adm-nic")}
      </tr>`).join("")}
    </tbody>`;
}

function zdravje(d) {
  const z = d.zdravje || {};
  const m = d.stroj || {};
  const starost = z.last_feed_ts ? (Date.now() / 1000 - z.last_feed_ts) : null;
  // Ista meja kot v nogi potniških strani (`common.FEED_STALE_S`): zajem
  // bere vsakih 30 s, zato je 90 s že tretji zgrešeni obhod.
  const feedRazred = starost == null ? "je-slaba"
    : starost > FEED_STALE_S ? "je-slaba" : "je-dobra";
  const diskDelez = m.disk_vseh ? m.disk_prostih / m.disk_vseh : null;
  const diskRazred = diskDelez == null ? "" : diskDelez < 0.08 ? "je-slaba"
    : diskDelez < 0.2 ? "je-mlacna" : "je-dobra";
  const mreze = z.by_network || {};
  const senca = z.senca || {};
  const vrstice = [
    ["zadnja zamuda iz feeda", starost == null ? "nikoli" : `pred ${Math.round(starost)} s`, feedRazred],
    ["vozil z lego", stevilo(z.vehicles_with_gps), ""],
    ["aktivnih obvestil", stevilo(z.alerts_active), ""],
    ["vlakov / meritev", `${stevilo((mreze.zeleznica || {}).trips)} / ${stevilo((mreze.zeleznica || {}).runs)}`, ""],
    ["avtobusov / meritev", `${stevilo((mreze.avtobus || {}).trips)} / ${stevilo((mreze.avtobus || {}).runs)}`, ""],
    ["zajetih dni", stevilo(z.days_covered), ""],
    ["baza", bajti(z.db_bytes), ""],
    ["prostora na disku", `${bajti(m.disk_prostih)} (${Math.round((diskDelez || 0) * 100)} %)`, diskRazred],
    ["senca napovedi", `${stevilo(senca.razresenih)} / ${stevilo(senca.vrstic)} razrešenih`, ""],
    ["strežnik teče", trajanje(m.teka_s), ""],
  ];
  el("zdravje").innerHTML = vrstice.map(([kaj, koliko, razred]) =>
    `<div class="adm-vrsta ${razred}">
       <span class="adm-kaj">${escapeHtml(kaj)}</span>
       <span class="adm-koliko">${escapeHtml(String(koliko))}</span>
     </div>`).join("");
}

function noga(d) {
  const opozorilo = d.preliv
    ? ` <strong>Števci so se enkrat prelili</strong> (${escapeHtml(d.preliv.slice(0, 16))}) —
        nekdo je preiskoval izmišljene naslove in del zahtev tistega obhoda ni štet.`
    : "";
  el("adm-noga").innerHTML = `
    IP se ne shrani nikoli: obiskovalec je zgoščena vrednost s soljo, ki se ob
    polnoči zavrže. Zato <strong>mesečnih različnih ljudi ni mogoče izračunati</strong>
    — vsota nad ${d.dni} dnevi isto osebo šteje enkrat na dan. Števci gredo v
    bazo vsakih ${d.stroj ? d.stroj.obisk_od : 60} s; obdobje ${escapeHtml(d.od)} – ${escapeHtml(d.do)}.${opozorilo}`;
}

// ------------------------------------------------------------------ zagon

/** Nabiralnik. Edino na tej strani, kar čaka na odgovor človeka. */
function sporocila(d) {
  const s = d.sporocila || {};
  const znacka = el("sporocil-znacka");
  znacka.hidden = !s.neprebranih;
  znacka.textContent = s.neprebranih ? `${s.neprebranih} novih` : "";

  const cilj = el("sporocila");
  if (!s.vklopljeno) {
    cilj.innerHTML = prazno("obrazec za stik je izklopljen (KAJROS_STIK_OBRAZEC=0)");
    return;
  }
  if (!s.seznam || !s.seznam.length) {
    cilj.innerHTML = prazno("nobenega sporočila še ni");
    return;
  }
  // Besedilo je vpisal neznanec: gre skozi `escapeHtml` in v `<p>`, nikoli
  // v `innerHTML` kot je. Prelome vrstic ohrani CSS (`white-space`), ne
  // pretvorba v `<br>` -- ta bi bila druga pot, po kateri bi lahko kaj ušlo.
  cilj.innerHTML = s.seznam.map((v) => `
    <article class="adm-sporocilo${v.prebrano ? " je-prebrano" : ""}" data-id="${v.id}">
      <header class="adm-sp-glava">
        <a class="adm-sp-od" href="mailto:${encodeURIComponent(v.email)}">${escapeHtml(v.email)}</a>
        <span class="adm-sp-kdaj">${escapeHtml(v.prispelo.slice(0, 16).replace("T", " "))}</span>
        <span class="adm-sp-kje">${escapeHtml([v.drzava, v.naprava].filter(Boolean).join(" · "))}</span>
        <button type="button" class="adm-sp-gumb" data-prebrano="${v.prebrano ? 0 : 1}">
          ${v.prebrano ? "označi kot novo" : "prebrano"}
        </button>
        <button type="button" class="adm-sp-gumb adm-sp-brisi" data-brisi="1">izbriši</button>
      </header>
      <p class="adm-sp-telo">${escapeHtml(v.besedilo)}</p>
    </article>`).join("");
}

el("sporocila").addEventListener("click", async (e) => {
  const gumb = e.target.closest(".adm-sp-gumb");
  if (!gumb) return;
  const id = gumb.closest(".adm-sporocilo").dataset.id;
  // Brisanje je nepovratno in gumb stoji tik ob „prebrano" -- vprašanje je
  // tu zato, ker je zgrešen klik na telefonu cena celega sporočila.
  if (gumb.dataset.brisi && !confirm("Izbrišem to sporočilo? Tega ni mogoče razveljaviti.")) return;
  gumb.disabled = true;
  try {
    await fetch(`/admin/sporocila/${id}`, {
      method: "POST", credentials: "same-origin",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: gumb.dataset.brisi ? "akcija=brisi" : `prebrano=${gumb.dataset.prebrano}`,
    });
    await nalozi();
  } finally {
    gumb.disabled = false;
  }
});


async function nalozi() {
  try {
    const r = await fetch(`/admin/podatki?dni=${dni}`, { credentials: "same-origin" });
    if (!r.ok) throw new Error(r.status === 403 ? "Napačen žeton." : `strežnik: ${r.status}`);
    const d = await r.json();
    const p = el("adm-napaka");
    // Zdravje zajema se prikaže tudi tedaj -- prav takrat je pregled edino,
    // kar na tej strani sploh pove kaj uporabnega.
    p.hidden = d.steje !== false;
    if (!p.hidden) {
      p.textContent = "Štetje obiska je izklopljeno (KAJROS_OBISK=0) — "
        + "spodnje številke se ne dopolnjujejo in so lahko poljubno stare.";
    }
    ploscice(d); poDnevih(d); strani(d); razrezi(d); endpointi(d);
    sporocila(d); zdravje(d); noga(d);
  } catch (e) {
    const p = el("adm-napaka");
    p.hidden = false;
    p.textContent = `Pregleda ni bilo mogoče naložiti — ${e.message}`;
  }
}

el("obdobje").addEventListener("click", (e) => {
  const gumb = e.target.closest("button[data-dni]");
  if (!gumb) return;
  dni = Number(gumb.dataset.dni);
  el("obdobje").querySelectorAll("button").forEach((b) =>
    b.setAttribute("aria-pressed", String(b === gumb)));
  nalozi();
});

// `pollWhileVisible` prvič sproži takoj, zato tu ni ločenega klica. Minuta je
// ritem, v katerem se števci sploh zapišejo v bazo -- pogosteje ni česa videti,
// in v skritem zavihku se ne osvežuje nič.
pollWhileVisible(nalozi, 60000);
