"use strict";

// Deljenje lege: kdor se pelje, pove drugim, kje je vozilo.
//
// Potnik ne vpisuje, na cem je. Stran vzame dve legi nekaj sekund narazen --
// iz njiju je tudi smer, ki loci vlak proti Mariboru od vlaka proti Ljubljani
// na istem tiru -- in streznik vrne vozila, ki bi bila po voznem redu in
// zamudi ravno tu (`deljenje.kandidati`). Potnik izbere, od tedaj stran
// posilja tocke, dokler ne ustavi, izstopi ali voznja ne pride na cilj.
//
// **Brskalnik lege z ugasnjenim zaslonom ne posilja**, service worker je
// nima. Zato Wake Lock drzi zaslon prizgan, dokler je stran spredaj, in
// stran to potniku pove. V aplikaciji za Android deljenje prevzame nativna
// storitev in dela tudi v zepu (`MOST.deliZacni`).

(() => {
  const el = document.getElementById("deli");
  if (!el) return;

  //: Kako pogosto stran poslje nabrane tocke. Tocka pa se nabere ob vsakem
  //: popravku GPS -- posiljanje v paketih ne izgubi natancnosti. Toliko kot
  //: mali zemljevid v oknu voznje vprasa (`deljenje.POSILJANJE_S`).
  const POSLJI_MS = 5000;
  //: Najmanjsi razmik tock; streznik gostejsih ne sprejme (`RAZMIK_S`).
  const RAZMIK_MS = 3000;
  //: Druga lega za smer: toliko casa ali toliko metrov po prvi.
  const SMER_MS = 8000;
  const SMER_M = 40;
  //: Dlje od tega brez uporabne lege je napaka, ne cakanje.
  const ISCI_ROK_MS = 30000;
  //: Lega, slabsa od tega, ni za izbiro vozila.
  const DOVOLJ_M = 120;
  //: Najvec tock v vrsti, ko ni povezave; starejse odpadejo.
  const NAJVEC_V_VRSTI = 60;
  //: Zamudo kandidata povemo sele od tod; manj je vsakdanje in gumb samo
  //: podaljsa. Velika pove, da je to verjetno prejsnja voznja iste linije.
  const ZAMUDA_POVEJ_S = 180;

  const NATIVNO = !!(MOST && typeof MOST.deliZacni === "function");

  const S = {
    faza: "miruje",        // miruje | isce | izbira | deli | konec | napaka
    watch: null, rok: null, posiljalec: null, wake: null, anketa: null,
    prva: null, zadnja: null, vrsta: [], id: null, voznja: null,
    kandidati: [], stanje: null, poslanih: 0, sporocilo: "",
  };

  // ---------- besedilo ----------

  function oznaka(k) {
    return imeVoznje(k);
  }

  // "Ljubljana - Maribor" -> "Maribor": potnik isce, kam pelje.
  function cilj(k) {
    const h = k.headsign || "";
    const i = h.lastIndexOf(" - ");
    return lepoIme(i >= 0 ? h.slice(i + 3) : h);
  }

  // Imena v imenovalniku, zato "pri postaji X" in ne "pri X": sklanjati se jih
  // ne da splosno (glej `yourStopHtml` v train.js).
  function kjeText(k, bus) {
    const kraj = bus ? "postajališču" : "postaji";
    if (k.pri) return `pri ${kraj} ${k.pri}`;
    if (k.med) return `med ${bus ? "postajališčema" : "postajama"} ${k.med[0]} in ${k.med[1]}`;
    return "";
  }

  // Po čem ločiš dve vožnji z istim imenom: ura odhoda z izhodišča in
  // zamuda, ki bi jo vozilo imelo, če bi bil na njem (`deljenje.kandidati`).
  // Dve liniji Arrive proti Ljubljani sta bili brez tega dva enaka gumba.
  function uraText(k) {
    if (!k.odhod || !k.odhod.ura) return "";
    const z = k.zamuda_s;
    return `odhod ${hhmm(k.odhod.ura)} iz ${k.odhod.postaja}${
      z != null && Math.abs(z) >= ZAMUDA_POVEJ_S ? ` · zdaj ${delayText(z)}` : ""}`;
  }

  function razdalja(a, b) {
    const k = Math.cos(a.lat * Math.PI / 180);
    const dx = (b.lon - a.lon) * 111195 * k;
    const dy = (b.lat - a.lat) * 111195;
    return Math.hypot(dx, dy);
  }

  // ---------- izris ----------
  //
  // Tri oblike iste stvari: oblika na domaci strani (`deli-oblika`), vrstica
  // v iskalniku (`deli-kompakt`), kamor clovek pride prvi, in vrstica v oknu
  // voznje (`deli-okno`), kjer vozilo ze poznamo in izbire ni. Povabilo je en
  // sam gumb; ko potnik zacne, se razpre v kartico v barvi deljenja (indigo,
  // kot oblika "Deli lego"). Zasloni po prototipu, ki ga je David potrdil
  // 11. 10. 2026 (platno "Deljenje lege: zasloni").

  const KOMPAKT = el.classList.contains("deli-kompakt");
  const OKNO = el.classList.contains("deli-okno");
  // Obliko na domaci strani narise predloga (`home.html`), z risbo, ki v JS
  // nima kaj iskati; stran jo shrani in vrne, ko se deljenje konca.
  const VABILO = el.classList.contains("deli-oblika") ? el.innerHTML : null;
  const OMREZJE = el.dataset.omrezje || null;
  //: Od kod je potnik zacel (`deljenje.VIRI`), za lijak v pregledu.
  const VIR = OKNO ? "okno" : KOMPAKT ? "iskalnik" : "domov";

  // Voznja, ki jo okno voznje pozna -- `train.js` jo zapise v data-*.
  function fiksna() {
    const d = el.dataset;
    if (!OKNO || !d.trip || !d.dan) return null;
    return { trip_id: d.trip, service_date: d.dan, network: d.omrezje || "zeleznica",
             mode: d.mode || "", train_no: d.st || "", headsign: d.smer || "",
             agency: d.prevoznik || null };
  }

  // "vlak" ali "avtobus" (tudi nadomestni): sklanja se pravilno z obrazili
  // -a (rodilnik) in -u (mestnik) -- tega vlaka, na avtobusu.
  const vozilo = (k) => (k && isBus(k.mode) ? "avtobus" : "vlak");
  // Cigav podatek tvoja zamuda zamenja: nadomestni prevoz ga nima nobenega.
  function zamenja(k) {
    if (k.network === "avtobus") return "zadnji podatek prevoznika";
    return isBus(k.mode) ? "vozni red" : "zadnji podatek SŽ";
  }

  function ink(k) {
    if (!isBus(k.mode)) return TRAIN_INK;
    if (k.network === "zeleznica") return "#b48ad8";      // nadomestni prevoz
    return AGENCY_INK[k.agency === "lpp" ? "1118" : k.agency] || BUS_INK;
  }

  const SVG_VLAK = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><rect x="6" y="3" width="12" height="14" rx="3"/>
    <path d="M6 11h12M9 21l2-4M15 21l-2-4"/></svg>`;
  const SVG_BUS = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    stroke-width="1.8" aria-hidden="true"><rect x="5" y="3" width="14" height="15" rx="3"/>
    <path d="M5 11h14M8 21v-3M16 21v-3"/></svg>`;
  const SVG_VALOVI = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="2.2"/>
    <path d="M8 8a5.6 5.6 0 0 0 0 8M16 8a5.6 5.6 0 0 1 0 8M5.2 5.2a9.6 9.6 0 0 0 0 13.6M18.8 5.2a9.6 9.6 0 0 1 0 13.6"/></svg>`;
  const SVG_OKO = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    stroke-width="1.8" aria-hidden="true"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/>
    <circle cx="12" cy="12" r="3"/></svg>`;
  const SVG_KLJUKA = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    stroke-width="3" stroke-linecap="round" aria-hidden="true"><path d="M5 12l5 5 9-10"/></svg>`;
  const SVG_NAPREJ = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>`;

  // "ta vlak gleda 12 ljudi" -- glagol in samostalnik se ujemata s številom,
  // odločata zadnji dve števki (kot `potnikov`).
  function gledaText(n, kaj) {
    const d = n % 100;
    if (d === 1) return `ta ${kaj} gleda ${n} človek`;
    if (d === 2) return `ta ${kaj} gledata ${n} človeka`;
    if (d === 3 || d === 4) return `ta ${kaj} gledajo ${n} ljudje`;
    return `ta ${kaj} gleda ${n} ljudi`;
  }

  function gledaloText(n, kaj) {
    const d = n % 100;
    if (d === 1) return `človek je gledal ta ${kaj}`;
    if (d === 2) return `človeka sta gledala ta ${kaj}`;
    if (d === 3 || d === 4) return `ljudje so gledali ta ${kaj}`;
    return `ljudi je gledalo ta ${kaj}`;
  }

  function odhodovText(n, bus) {
    const d = n % 100;
    const s = bus ? "postajališč" : "postaj";
    if (d === 1) return `potrjen odhod s ${bus ? "postajališča" : "postaje"}`;
    if (d === 2) return `potrjena odhoda s ${s}`;
    if (d === 3 || d === 4) return `potrjeni odhodi s ${s}`;
    return `potrjenih odhodov s ${s}`;
  }

  function stojiText(st) {
    if (!st || !st.stoji) return "";
    const m = st.stoji_s != null ? Math.floor(st.stoji_s / 60) : 0;
    return m >= 1 ? `stoji ${m} min` : "stoji";
  }

  const hitrostText = (st) => (st && !st.stoji && st.hitrost_ms >= 3
    ? `${Math.round(st.hitrost_ms * 3.6)} km/h` : "");

  // Zamuda nosi barvo lestvice, zato na podlagi strani: temna oranžna
  // (`--d-big`) na indigu ne doseže kontrasta (2,8 : 1).
  const zamudaHtml = (z, cls = "deli-zam") => (z
    ? `<b class="${cls}" style="color:${delayColor(z)}">${escapeHtml(delayText(z))}</b>` : "");

  function naslovVoznje(k) {
    return `${escapeHtml(oznaka(k))}${cilj(k) ? ` → ${escapeHtml(cilj(k))}` : ""}`;
  }

  function vrstica(besedilo, cls = "deli-besedilo") {
    return besedilo ? `<span class="${cls}">${besedilo}</span>` : "";
  }

  const oznakaHtml = (besedilo, zivo) =>
    `<span class="deli-oznaka${zivo ? " deli-zivo" : ""}">${besedilo}</span>`;

  // Brskalnik lege z ugasnjenim zaslonom ne pošilja; aplikacija jo.
  function nasvetHtml(konec) {
    if (NATIVNO) {
      return konec ? `<div class="deli-nasvet">Z budilko se deljenje začne samo, ko vstopiš.
          Vklopiš ga v seznamu budilk: <b>Ko se peljem, pomagaj drugim</b>.</div>` : "";
    }
    return `<div class="deli-nasvet"><span>${konec
        ? "V aplikaciji za Android deliš tudi s telefonom v žepu, z budilko pa se deljenje začne samo, ko vstopiš."
        : "Pusti to stran odprto in zaslon prižgan. Ko se zaslon ugasne, brskalnik lege ne pošilja več."}</span>
      <a href="/android">${konec ? "Aplikacija za Android"
        : "V aplikaciji za Android deliš tudi s telefonom v žepu"} ${SVG_NAPREJ}</a></div>`;
  }

  function kandidatHtml(k, i, n) {
    const prvi = i === 0 && n > 1;
    return `
      <button type="button" class="deli-kandidat${prvi ? " je-prvi" : ""}" data-deli="izberi" data-i="${i}">
        <span class="deli-ikona" style="background:${ink(k)}">${isBus(k.mode) ? SVG_BUS : SVG_VLAK}</span>
        <span class="deli-kand-besedilo">
          <strong>${naslovVoznje(k)}</strong>
          ${vrstica(escapeHtml(kjeText(k, k.network === "avtobus")), "")}
          ${uraText(k) ? `<span>${escapeHtml(uraText(k))}</span>` : ""}
        </span>
        ${prvi ? '<span class="deli-znacka">najbolj verjetno</span>' : ""}
      </button>`;
  }

  // Deliš, a drugi te še ne vidijo: poročilo ni verodostojno, dokler se
  // vozilo ne pelje (`deljenje.stanje`). Dva koraka povesta, kaj že velja in
  // kaj pride, ko vozilo spelje.
  function cakaHtml(k, st) {
    const bus = k.network === "avtobus";
    const kje = st && (st.pri || st.med) ? kjeText(st, bus) : "";
    const pod = st
      ? `Zdaj ${st.stoji ? "stoji " : ""}${escapeHtml(kje)}${st.zamuda ? " · " + zamudaHtml(st.zamuda) : ""}`
      : "Pošiljam prvo lego …";
    const v = vozilo(k);
    return oznakaHtml("Deliš lego", true)
      + `<strong class="deli-naslov">${naslovVoznje(k)}</strong>`
      + vrstica(pod, "deli-pod")
      + `<ol class="deli-koraki">
          <li class="${st ? "je-opravljen" : ""}"><span class="deli-korak">${st ? SVG_KLJUKA : ""}</span>
            <span>Tvoja lega je na progi tega ${v}a.<small>Na tabli že piše: potnik na ${v}u.</small></span></li>
          <li><span class="deli-korak"></span>
            <span>Ko ${v} spelje, te pokažemo na zemljevidu.<small>Takrat tvoja zamuda zamenja ${zamenja(k)}.</small></span></li>
        </ol>`
      + nasvetHtml(false)
      + `<button type="button" class="deli-gumb" data-deli="ustavi">Ustavi</button>`;
  }

  // Drugi te vidijo: vozilo je na zemljevidu na tvoji legi, tvoja zamuda je
  // na tablah. Število gledalcev je razlog, da deljenja ne ustaviš.
  function voziHtml(k, st) {
    const bus = k.network === "avtobus";
    const v = vozilo(k);
    const n = st.jaz ? st.jaz.gledajo : 0;
    const kje = [kjeText(st, bus), stojiText(st) || hitrostText(st)].filter(Boolean).join(" · ");
    return `<div class="deli-vrh">${oznakaHtml("Drugi te vidijo", true)}${n
        ? `<span class="deli-gledajo">${SVG_OKO}${escapeHtml(gledaText(n, v))}</span>` : ""}</div>`
      + `<strong class="deli-naslov">${naslovVoznje(k)}</strong>`
      + vrstica(escapeHtml(kje), "deli-pod")
      + (st.zamuda ? `<div class="deli-zamuda">${zamudaHtml(st.zamuda, "deli-zam deli-zam-velika")}
          <span>tvoja zamuda je zdaj na tablah</span></div>` : "")
      + (OKNO ? "" : `<a class="deli-povezava" href="/app/map?trip=${encodeURIComponent(k.trip_id)}">
          poglej na zemljevidu ${SVG_NAPREJ}</a>`)
      + `<button type="button" class="deli-gumb" data-deli="ustavi">Ustavi</button>`
      + vrstica(`Ustavi se samo, ko izstopiš ali je ${v} na cilju.`, "deli-mala");
  }

  function hvalaHtml() {
    const k = S.voznja || {};
    const bus = isBus(k.mode);
    const jaz = (S.stanje && S.stanje.jaz) || null;
    const ploscice = [];
    if (jaz) {
      const min = Math.round(jaz.trajanje_s / 60);
      ploscice.push([min >= 1 ? `${min} min` : "< 1 min", "deljenja"]);
      if (jaz.odhodov) ploscice.push([String(jaz.odhodov), odhodovText(jaz.odhodov, k.network === "avtobus")]);
      if (jaz.gledalo) ploscice.push([String(jaz.gledalo), gledaloText(jaz.gledalo, bus ? "avtobus" : "vlak")]);
    }
    return `<strong class="deli-naslov deli-hvala">Hvala!</strong>`
      + vrstica(escapeHtml(S.sporocilo), "deli-pod")
      + (ploscice.length ? `<div class="deli-stevila">${ploscice.map(([st, kaj]) =>
          `<div><b>${escapeHtml(st)}</b><span>${escapeHtml(kaj)}</span></div>`).join("")}</div>` : "")
      + nasvetHtml(true)
      + `<button type="button" class="deli-gumb" data-deli="nazaj">V redu</button>`;
  }

  function izrisi() {
    const f = S.faza;
    el.classList.toggle("je-odprt", f !== "miruje");
    if (f === "miruje") {
      if (VABILO !== null) { el.innerHTML = VABILO; return; }
      if (OKNO) {
        const k = fiksna();
        const v = vozilo(k || { mode: el.dataset.mode });
        el.innerHTML = `<button type="button" class="deli-vrstica" data-deli="zacni">
            ${SVG_VALOVI}
            <span class="deli-vrstica-besedilo"><b>Si na tem ${v}u? Deli, kje je</b>
              <span>Kdor čaka na ${v === "vlak" ? "peronu" : "postajališču"}, bo videl, kje ${v} res je.</span></span>
            ${SVG_NAPREJ}
          </button>`;
        return;
      }
      el.innerHTML = KOMPAKT
        ? `<button type="button" class="deli-vabilo" data-deli="zacni">
             <span>Pelješ se? <b>Deli, kje je vozilo</b></span><span aria-hidden="true">›</span>
           </button>`
        : oznakaHtml("Pomagaj drugim") + `<strong class="deli-naslov">Pelješ se? Deli, kje je vozilo.</strong>`
          + vrstica("Kdor čaka na isti vlak ali avtobus, bo videl, kje je in koliko zamuja.")
          + `<button type="button" class="deli-gumb" data-deli="zacni">Deli lego</button>`;
      return;
    }
    if (f === "isce") {
      el.innerHTML = oznakaHtml("Pomagaj drugim")
        + `<strong class="deli-naslov">${OKNO ? "Iščem tvojo lego …" : "Iščem, s čim se pelješ …"}</strong>`
        + vrstica(escapeHtml(S.sporocilo || (OKNO ? "Preverim, ali si ob progi tega vozila."
          : "Za smer vožnje rabim dve legi nekaj sekund narazen.")))
        + `<button type="button" class="deli-drugo" data-deli="ustavi">Prekliči</button>`;
      return;
    }
    if (f === "izbira") {
      const n = S.kandidati.length;
      el.innerHTML = oznakaHtml("Pomagaj drugim")
        + `<strong class="deli-naslov">${n ? (n === 1 ? "Se pelješ s tem?" : "S čim se pelješ?")
          : "Ne najdem vozila, ki bi bilo zdaj tu."}</strong>`
        + (n > 1 ? vrstica(`${n === 2 ? "Dve vozili sta" : n <= 4 ? `${n} vozila so` : `${n} vozil je`}
            po voznem redu ta hip tu, kjer si ti.`) : n ? "" : vrstica("Poskusi znova, ko se vozilo premakne."))
        + `<div class="deli-seznam">${S.kandidati.map((k, i) => kandidatHtml(k, i, n)).join("")}</div>
           <div class="deli-gumbi">
             <button type="button" class="deli-drugo" data-deli="ustavi">${n
               ? "Nisem na nobenem" : "Prekliči"}</button>
             <button type="button" class="deli-drugo" data-deli="znova">Poišči znova</button>
           </div>`
        + (n ? vrstica("Hitreje gre iz okna vožnje: tam veš, na katerem vozilu si, in izbire ni.",
          "deli-mala") : "");
      return;
    }
    if (f === "deli") {
      const st = S.stanje;
      el.innerHTML = st && st.verodostojno ? voziHtml(S.voznja, st) : cakaHtml(S.voznja, st);
      return;
    }
    if (f === "konec") {
      el.innerHTML = hvalaHtml();
      return;
    }
    el.innerHTML = oznakaHtml("Pomagaj drugim")
      + `<strong class="deli-naslov">Deljenje ne gre</strong>`
      + vrstica(escapeHtml(S.sporocilo))
      + `<button type="button" class="deli-drugo" data-deli="nazaj">V redu</button>`;
  }

  function napaka(besedilo) {
    pospravi();
    S.faza = "napaka";
    S.sporocilo = besedilo;
    izrisi();
  }

  // Zavrnitev začetka iz okna vožnje pove, kaj storiti: kdor čaka na peronu,
  // deli, ko vstopi (`deljenje.Zavrnjeno.koda`).
  function zavrnjeno(e) {
    const k = S.voznja || fiksna();
    if (OKNO && k && (e.koda === "ni_tu" || e.koda === "ne_vozi")) {
      return napaka(`Ta ${vozilo(k)} ta hip ni tu, kjer si ti. Deli, ko vstopiš.`);
    }
    if (OKNO && k && e.koda === "ni_na_trasi") {
      return napaka(`Nisi ob progi tega ${vozilo(k)}a. Deliš lahko, ko si na njem.`);
    }
    return napaka(e.message);
  }

  // ---------- lega ----------

  function lega(p) {
    return {
      lat: p.coords.latitude, lon: p.coords.longitude, acc: p.coords.accuracy,
      t: p.timestamp || Date.now(),
      v: p.coords.speed != null && isFinite(p.coords.speed) ? p.coords.speed : null,
    };
  }

  function obLegi(p) {
    const l = lega(p);
    S.zadnja = l;
    if (S.faza === "isce") {
      if (l.acc > DOVOLJ_M) {
        S.sporocilo = `Lega je še nenatančna (±${Math.round(l.acc)} m) …`;
        izrisi();
        return;
      }
      // Okno vožnje vožnjo pozna: ena dobra lega je dovolj, da strežnik
      // preveri, ali je potnik ob progi in vozilo tu.
      if (fiksna()) return izberi(fiksna());
      if (!S.prva) { S.prva = l; return; }
      if (l.t - S.prva.t >= SMER_MS || razdalja(S.prva, l) >= SMER_M) vprasaj();
      return;
    }
    if (S.faza === "deli" && !NATIVNO) {
      const zadnja = S.vrsta[S.vrsta.length - 1];
      if (zadnja && l.t - zadnja.t < RAZMIK_MS) return;
      S.vrsta.push(l);
      if (S.vrsta.length > NAJVEC_V_VRSTI) S.vrsta.splice(0, S.vrsta.length - NAJVEC_V_VRSTI);
    }
  }

  // Samo zavrnjeno dovoljenje je dokoncno. "Lege ni" in iztek sta med
  // sledenjem prehodna (predor, prvi popravek) in jih brskalnik javi tudi
  // takrat, ko naslednji popravek pride cez sekundo; kadar ga ne, to pove
  // rok iskanja (`ISCI_ROK_MS`).
  function obNapakiLege(e) {
    if (e.code !== 1) return;
    napaka("Dostop do lege je zavrnjen. Dovoli ga v nastavitvah strani.");
  }

  function spremljaj() {
    if (S.watch !== null) return;
    S.watch = navigator.geolocation.watchPosition(obLegi, obNapakiLege,
      { enableHighAccuracy: true, maximumAge: 0 });
  }

  // ---------- potek ----------

  async function post(telo) {
    const r = await fetch("/api/deli", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(telo),
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) {
      const e = new Error(d.napaka || d.detail || `napaka ${r.status}`);
      e.status = r.status;
      e.koda = d.koda || null;
      throw e;
    }
    return d;
  }

  function zacni() {
    if (!navigator.geolocation) return napaka("Ta brskalnik lege ne pozna.");
    if (!window.isSecureContext) {
      return napaka(`Lega dela samo prek varne povezave. Odpri kajros.app.`);
    }
    S.faza = "isce";
    S.prva = null;
    S.sporocilo = "";
    izrisi();
    spremljaj();
    clearTimeout(S.rok);
    S.rok = setTimeout(() => {
      if (S.faza !== "isce") return;
      // Ena dobra lega je boljsa od nobene: brez smeri so kandidati oba vlaka.
      if (S.zadnja && S.zadnja.acc <= DOVOLJ_M * 2) return fiksna() ? izberi(fiksna()) : vprasaj();
      napaka("GPS se ni odzval. Pod streho pogosto nima signala — poskusi ob oknu.");
    }, ISCI_ROK_MS);
  }

  async function vprasaj() {
    if (S.faza !== "isce" && S.faza !== "izbira") return;
    clearTimeout(S.rok);
    const l = S.zadnja;
    const prej = S.prva && S.prva !== l ? { lat: S.prva.lat, lon: S.prva.lon } : null;
    S.faza = "izbira";
    S.kandidati = [];
    el.innerHTML = oznakaHtml("Pomagaj drugim")
      + `<strong class="deli-naslov">Iščem vozila v bližini …</strong>`;
    try {
      const d = await post({ lat: l.lat, lon: l.lon, acc: l.acc, prej });
      S.kandidati = d.kandidati || [];
      // Na avtobusni strani je potnik najverjetneje na avtobusu: vozila tega
      // omrezja gredo naprej, vrstni red znotraj njih pa ostane streznikov.
      if (OMREZJE) {
        S.kandidati.sort((a, b) => (a.network !== OMREZJE) - (b.network !== OMREZJE));
      }
      izrisi();
    } catch (e) {
      napaka(e.message);
    }
  }

  async function izberi(k) {
    S.voznja = k;
    S.faza = "deli";
    S.id = null;
    S.stanje = null;
    S.vrsta = S.zadnja ? [S.zadnja] : [];
    izrisi();
    if (NATIVNO) {
      // Storitev v aplikaciji ima svojo lego in poslje sama. Stran le bere,
      // kaj je poslala -- dvojno posiljanje bi bila dva "potnika".
      ustaviLego();
      // Cel kandidat gre zraven: `deliStanje()` ga vrne in ploscica ga po
      // vrnitvi na stran izrise enako kot ob izbiri.
      const ok = MOST.deliZacni(JSON.stringify({ ...k, oznaka: oznaka(k), cilj: cilj(k) }));
      if (!ok) return napaka("Aplikacija deljenja ni mogla začeti. Dovoli ji lego.");
      S.anketa = setInterval(beriNativno, 5000);
      beriNativno();
      return;
    }
    await drziZaslon();
    await poslji();
    S.posiljalec = setInterval(poslji, POSLJI_MS);
  }

  async function poslji(zadnjic) {
    if (S.faza !== "deli" || NATIVNO) return;
    if (!S.vrsta.length && !zadnjic) return;
    const tocke = S.vrsta.splice(0);
    try {
      const d = await post({
        trip_id: S.voznja.trip_id, service_date: S.voznja.service_date,
        deljenje: S.id, tocke: tocke.length ? tocke : [S.zadnja], konec: !!zadnjic,
        vir: S.id ? undefined : VIR,
      });
      S.id = d.deljenje;
      S.stanje = d.stanje;
      S.poslanih += d.sprejetih || 0;
      if (d.konec && !zadnjic) return koncaj(d.konec);
      izrisi();
    } catch (e) {
      // Brez povezave (predor): tocke gredo nazaj v vrsto in cakajo.
      if (!e.status) {
        S.vrsta = tocke.concat(S.vrsta).slice(-NAJVEC_V_VRSTI);
        return;
      }
      zavrnjeno(e);
    }
  }

  function beriNativno() {
    let st = {};
    try {
      st = JSON.parse(MOST.deliStanje() || "{}");
    } catch (e) {
      st = {};
    }
    if (st.stanje) S.stanje = st.stanje;
    if (st.konec) return koncaj(st.konec);
    if (!st.aktivno) return koncaj("potnik");
    izrisi();
  }

  const KONCI = {
    izstop: "Deljenje se je ob izstopu ustavilo samo.",
    cilj: "Vožnja je na cilju, deljenje se je ustavilo samo.",
    cas: "Deljenje se je po šestih urah ustavilo samo.",
    potnik: "Deljenje je ustavljeno.",
    napaka: "Strežnik deljenja ni več sprejel. Morda vožnja ne vozi več.",
    lega: "Aplikacija nima dovoljenja za lego.",
  };

  function koncaj(razlog) {
    pospravi();
    S.faza = "konec";
    S.sporocilo = KONCI[razlog] || KONCI.potnik;
    izrisi();
  }

  async function ustavi() {
    if (S.faza === "deli") {
      if (NATIVNO) MOST.deliUstavi();
      else await poslji(true);
      return koncaj("potnik");
    }
    pospravi();
    S.faza = "miruje";
    izrisi();
  }

  function ustaviLego() {
    if (S.watch !== null) navigator.geolocation.clearWatch(S.watch);
    S.watch = null;
  }

  function pospravi() {
    ustaviLego();
    clearTimeout(S.rok);
    clearInterval(S.posiljalec);
    clearInterval(S.anketa);
    S.posiljalec = null;
    S.anketa = null;
    if (S.wake) S.wake.release().catch(() => {});
    S.wake = null;
  }

  // Wake Lock drzi zaslon prizgan, dokler je stran spredaj. Brskalnik ga ob
  // skritju strani sprosti sam, zato ga ob vrnitvi zahtevamo znova.
  async function drziZaslon() {
    if (!("wakeLock" in navigator) || document.hidden) return;
    try {
      S.wake = await navigator.wakeLock.request("screen");
    } catch (e) {
      S.wake = null;
    }
  }

  document.addEventListener("visibilitychange", () => {
    if (document.hidden || S.faza !== "deli" || NATIVNO) return;
    drziZaslon();
    poslji();
  });

  el.addEventListener("click", (ev) => {
    const b = ev.target.closest("[data-deli]");
    if (!b) return;
    const kaj = b.dataset.deli;
    if (kaj === "zacni") zacni();
    else if (kaj === "ustavi") ustavi();
    else if (kaj === "znova") { S.faza = "isce"; S.prva = S.zadnja; izrisi(); spremljaj(); vprasaj(); }
    else if (kaj === "izberi") izberi(S.kandidati[Number(b.dataset.i)]);
    else if (kaj === "nazaj") { S.faza = "miruje"; izrisi(); }
  });

  // Aplikacija deli tudi, ko je stran zaprta. Ob vrnitvi na domaco stran
  // mora ploscica to pokazati, ne povabila k novemu deljenju. V oknu voznje
  // samo, kadar aplikacija deli prav to voznjo -- `train.js` jo pove z
  // dogodkom `deli-voznja`, ko jo nalozi.
  function nadaljujNativno() {
    if (!NATIVNO || S.faza !== "miruje") return;
    try {
      const st = JSON.parse(MOST.deliStanje() || "{}");
      if (!st.aktivno || !st.voznja) return;
      if (OKNO && (!fiksna() || st.voznja.trip_id !== fiksna().trip_id)) return;
      S.voznja = st.voznja;
      S.stanje = st.stanje || null;
      S.faza = "deli";
      S.anketa = setInterval(beriNativno, 5000);
    } catch (e) {
      /* stara aplikacija brez deljenja */
    }
  }

  el.addEventListener("deli-voznja", () => {
    nadaljujNativno();
    izrisi();
  });
  nadaljujNativno();
  izrisi();
})();
