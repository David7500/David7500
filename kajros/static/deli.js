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

  const NATIVNO = !!(MOST && typeof MOST.deliZacni === "function");

  const S = {
    faza: "miruje",        // miruje | isce | izbira | deli | konec | napaka
    watch: null, rok: null, posiljalec: null, wake: null, anketa: null,
    prva: null, zadnja: null, vrsta: [], id: null, voznja: null,
    kandidati: [], stanje: null, poslanih: 0, sporocilo: "",
  };

  // ---------- besedilo ----------

  function oznaka(k) {
    if (k.network === "avtobus") return `${AGENCY[k.agency] || ""} ${k.train_no}`.trim();
    return k.train_no;
  }

  // "Ljubljana - Maribor" -> "Maribor": potnik isce, kam pelje.
  function cilj(k) {
    const h = k.headsign || "";
    const i = h.lastIndexOf(" - ");
    return i >= 0 ? h.slice(i + 3) : h;
  }

  // Imena v imenovalniku, zato "pri postaji X" in ne "pri X": sklanjati se jih
  // ne da splosno (glej `yourStopHtml` v train.js).
  function kjeText(k, bus) {
    const kraj = bus ? "postajališču" : "postaji";
    if (k.pri) return `pri ${kraj} ${k.pri}`;
    if (k.med) return `med ${bus ? "postajališčema" : "postajama"} ${k.med[0]} in ${k.med[1]}`;
    return "";
  }

  function razdalja(a, b) {
    const k = Math.cos(a.lat * Math.PI / 180);
    const dx = (b.lon - a.lon) * 111195 * k;
    const dy = (b.lat - a.lat) * 111195;
    return Math.hypot(dx, dy);
  }

  // ---------- izris ----------
  //
  // Dve obliki iste stvari: oblika na domaci strani (`deli-oblika`) in
  // vrstica v iskalniku (`deli-kompakt`), kamor clovek pride prvi -- tja, kjer
  // ima shranjeno svojo pot, in prav tam je, ko sede na vlak. V obeh je
  // povabilo en sam gumb; ko potnik zacne, se razpre v kartico.

  const KOMPAKT = el.classList.contains("deli-kompakt");
  // Obliko na domaci strani narise predloga (`home.html`), z risbo, ki v JS
  // nima kaj iskati; stran jo shrani in vrne, ko se deljenje konca.
  const VABILO = el.classList.contains("deli-oblika") ? el.innerHTML : null;
  const OMREZJE = el.dataset.omrezje || null;

  function kartica(oznaka, naslov, besedilo, gumbi) {
    return `<span class="deli-oznaka${oznaka.zivo ? " deli-zivo" : ""}">${oznaka.besedilo}</span>
      <strong class="deli-naslov">${naslov}</strong>
      ${besedilo || ""}
      ${gumbi || ""}`;
  }

  function vrstica(besedilo) {
    return besedilo ? `<span class="deli-besedilo">${besedilo}</span>` : "";
  }

  const POMAGAJ = { besedilo: "Pomagaj drugim" };

  function izrisi() {
    const f = S.faza;
    el.classList.toggle("je-odprt", f !== "miruje");
    if (f === "miruje") {
      if (VABILO !== null) { el.innerHTML = VABILO; return; }
      el.innerHTML = KOMPAKT
        ? `<button type="button" class="deli-vabilo" data-deli="zacni">
             <span>Pelješ se? <b>Deli, kje je vozilo</b></span><span aria-hidden="true">›</span>
           </button>`
        : kartica(POMAGAJ, "Pelješ se? Deli, kje je vozilo.",
            vrstica("Kdor čaka na isti vlak ali avtobus, bo videl, kje je in koliko zamuja."),
            `<button type="button" class="deli-gumb" data-deli="zacni">Deli lego</button>`);
      return;
    }
    if (f === "isce") {
      el.innerHTML = kartica(POMAGAJ, "Iščem, s čim se pelješ …",
        vrstica(escapeHtml(S.sporocilo || "Za smer vožnje rabim dve legi nekaj sekund narazen.")),
        `<button type="button" class="deli-drugo" data-deli="ustavi">Prekliči</button>`);
      return;
    }
    if (f === "izbira") {
      const n = S.kandidati.length;
      const seznam = S.kandidati.map((k, i) => `
        <button type="button" class="deli-kandidat" data-deli="izberi" data-i="${i}">
          <strong>${escapeHtml(oznaka(k))}${cilj(k) ? ` → ${escapeHtml(cilj(k))}` : ""}</strong>
          <span>${escapeHtml(kjeText(k, k.network === "avtobus"))}</span>
        </button>`).join("");
      el.innerHTML = kartica(POMAGAJ,
        n ? (n === 1 ? "Se pelješ s tem?" : "S čim se pelješ?")
          : "Ne najdem vozila, ki bi bilo zdaj tu.",
        n ? "" : vrstica("Poskusi znova, ko se vozilo premakne."),
        `<div class="deli-seznam">${seznam}</div>
         <div class="deli-gumbi">
           <button type="button" class="deli-drugo" data-deli="znova">Poišči znova</button>
           <button type="button" class="deli-drugo" data-deli="ustavi">${n
             ? "Nisem na nobenem" : "Prekliči"}</button>
         </div>`);
      return;
    }
    if (f === "deli") {
      const k = S.voznja;
      const st = S.stanje;
      const kje = st && (st.pri || st.med) ? kjeText(st, k.network === "avtobus") : "";
      const z = st && st.zamuda ? st.zamuda : null;
      el.innerHTML = kartica({ besedilo: "Deliš lego", zivo: true },
        `${escapeHtml(oznaka(k))}${cilj(k) ? ` → ${escapeHtml(cilj(k))}` : ""}`,
        vrstica(kje
          ? `Drugi vidijo: ${escapeHtml(kje)}${z
            ? ` · <b style="color:${delayColor(z)}">${escapeHtml(delayText(z))}</b>` : ""}`
          : "Pošiljam prvo lego …")
        + vrstica(NATIVNO
          ? "Deli tudi, ko je telefon v žepu. Ustavi se sam, ko izstopiš."
          : "Pusti to stran odprto in zaslon prižgan. Ustavi se sam, ko izstopiš."),
        `<button type="button" class="deli-gumb deli-ustavi" data-deli="ustavi">Ustavi</button>`);
      return;
    }
    el.innerHTML = kartica(POMAGAJ, f === "konec" ? "Hvala!" : "Deljenje ne gre",
      vrstica(escapeHtml(S.sporocilo)),
      `<button type="button" class="deli-drugo" data-deli="nazaj">V redu</button>`);
  }

  function napaka(besedilo) {
    pospravi();
    S.faza = "napaka";
    S.sporocilo = besedilo;
    izrisi();
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
      if (S.zadnja && S.zadnja.acc <= DOVOLJ_M * 2) return vprasaj();
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
    el.innerHTML = kartica(POMAGAJ, "Iščem vozila v bližini …");
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
      napaka(e.message);
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
    izstop: "Izstopil si, deljenje se je ustavilo samo.",
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
  // mora ploscica to pokazati, ne povabila k novemu deljenju.
  if (NATIVNO) {
    try {
      const st = JSON.parse(MOST.deliStanje() || "{}");
      if (st.aktivno && st.voznja) {
        S.voznja = st.voznja;
        S.stanje = st.stanje || null;
        S.faza = "deli";
        S.anketa = setInterval(beriNativno, 5000);
      }
    } catch (e) {
      /* stara aplikacija brez deljenja */
    }
  }
  izrisi();
})();
