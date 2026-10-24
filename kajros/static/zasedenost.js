// Zasedenost po poročilih potnikov (`zasedenost.py`): gumb „Kako polno?“ v
// vrstici Pomagaj drugim ob deljenju lege in razdelek pod njo, ki ga gumb odpre
// (David, 23. 10. 2026; prej razdelek na dnu okna, ki ga ni videl nihče: 1--6
// poročil na dan ob ~250 ljudeh v oknih voženj). Gumb pove, kar o zasedenosti
// vemo, tudi zaprt. Potnik javi z enim dotikom; komentar gre skozi `/stik` v
// nabiralnik in je javen šele, ko ga skrbnik objavi.
//
// Vožnjo in privzeto postajo pove okno (`train.js`, `posodobiZasedenost`) z
// dogodkom `zas-voznja`. Razdelek je svoj element zunaj časovnice, ki jo okno
// na 30 s preriše -- izbira bi sicer izginila potniku pod prsti.
(() => {
  const el = document.getElementById("zasedenost");
  const gumb = document.getElementById("pomoc-zas");
  if (!el || !gumb) return;
  // Kateri razdelek vrstice je odprt, nosi vrstica (`deli.js`, `odpri`).
  const pomoc = gumb.closest(".pomoc");
  const odprto = () => pomoc.dataset.odprto === "zas";

  const OSVEZI_MS = 60000;
  // Kot `zasedenost.PREKLIC_S`: od zadnjega dotika.
  const PREKLIC_MS = 10 * 60000;
  // `stik.py` zavrne žeton, mlajši od 4 s, in starejši od 2 h. Osvežitev na
  // minuto bi vsakič prinesla nov žeton, opomba v 4 s po njej pa bi padla.
  const ZETON_NAJDLJE_S = 90 * 60;
  const S = {
    trip: null, dan: null, privzeta: null,
    izbrana: null,          // postaja, ki jo je izbral potnik ali na kateri je javil
    d: null,                // zadnji odgovor `/api/zasedenost`
    oddano: null,           // kar je ta naprava javila za ta odhod
    izbiraPostaje: false,
    opomba: "", opombaOdprta: false, opombaPoslana: false, opombeOdprte: false,
    potrdiNiVzel: false,
    sporocilo: null,
    zaposlen: false,
    zeton: null,
  };
  let poller = null;

  function nakljucno() {
    const b = new Uint8Array(16);
    crypto.getRandomValues(b);
    return Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("");
  }

  // Id naprave za „en glas na odhod na dan“. Strežnik ga ne shrani (samo
  // zgoščeno v pomnilniku). Nastane šele ob prvem poročilu: kdor nikoli ne
  // javi, ga nima. Brez shrambe velja do zaprtja strani.
  let napravaId = null;
  function naprava() {
    if (napravaId) return napravaId;
    try {
      napravaId = localStorage.getItem("kajros:naprava");
      if (!/^[0-9a-f]{32}$/.test(napravaId || "")) {
        napravaId = nakljucno();
        localStorage.setItem("kajros:naprava", napravaId);
      }
    } catch (e) {
      napravaId = nakljucno();
    }
    return napravaId;
  }

  const postaja = () => S.izbrana || S.privzeta;

  // Polnost vozila: okna se polnijo, pri „vrsta zunaj“ ljudje ob njem. Ista
  // risba kot v prototipu, ki ga je David potrdil 21. 10. 2026.
  function glif(n, velikost = 32) {
    const polno = [0, 2, 3, 4, 4][n - 1];
    const x0 = n === 5 ? 0 : 5.5;
    let okna = "";
    for (let i = 0; i < 4; i++) {
      okna += `<rect x="${4 + i * 6}" y="6.5" width="4" height="6" rx="1" `
        + (i < polno ? `fill="currentColor"/>`
          : `fill="none" stroke="currentColor" stroke-width="1" opacity=".5"/>`);
    }
    const zunaj = n === 5 ? [33.2, 37.6].map((cx) =>
      `<circle cx="${cx}" cy="8.4" r="1.7" fill="currentColor"/>`
      + `<rect x="${cx - 1.4}" y="11" width="2.8" height="8" rx="1.4" fill="currentColor"/>`).join("") : "";
    return `<svg width="${velikost}" height="${Math.round(velikost * 26 / 40)}" viewBox="0 0 40 26" aria-hidden="true">`
      + `<g transform="translate(${x0} 0)">`
      + `<rect x="1.5" y="3" width="27" height="17" rx="3.5" fill="none" stroke="currentColor" stroke-width="1.6"/>`
      + `${okna}<circle cx="8" cy="21.6" r="2.1" fill="currentColor"/>`
      + `<circle cx="22" cy="21.6" r="2.1" fill="currentColor"/></g>${zunaj}</svg>`;
  }

  const datumKratko = (iso) => `${+iso.slice(8, 10)}. ${+iso.slice(5, 7)}.`;
  const stopnja = (n) => S.d.stopnje[n - 1];

  // ------------------------------------------------------------- gumb

  // Ljudje: „Polno?“, dokler o tem odhodu ne vemo nič.
  const SVG_LJUDJE = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor"'
    + ' stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    + '<path d="M16 20v-1.5a3.5 3.5 0 0 0-3.5-3.5h-5A3.5 3.5 0 0 0 4 18.5V20"/><circle cx="10" cy="8" r="3.5"/>'
    + '<path d="M20 20v-1.5a3.5 3.5 0 0 0-2.5-3.35M15.5 4.6a3.5 3.5 0 0 1 0 6.8"/></svg>';
  const velika = (t) => t.charAt(0).toUpperCase() + t.slice(1);

  // Gumb v skupini dejanj (osnutek E, platno „Polno? — kaj pokaže gumb“) sam
  // pove, kar vemo: najprej potnikovo poročilo, nato kar je danes nevarno
  // (vrsta zunaj, poln prejšnji -- rdeče), nato običajno, nato zadnje današnje.
  // Ena beseda pod risbo, cel stavek v `title` in za bralnik zaslona.
  function gumbHtml(d) {
    const ok = okno(d);
    const o = d.obicajno;
    const danesZunaj = d.danes.find((x) => x.stopnja === 5);
    const zadnje = d.danes[d.danes.length - 1];
    let n = 0, ime = "Polno?", pod, opozorilo = false;
    if (S.oddano && !S.oddano.prejsnji) {
      n = S.oddano.stopnja;
      ime = `Javil si: ${stopnja(n)}`;
      pod = `zapisano: ${stopnja(n)}`;
    } else if (danesZunaj) {
      n = 5;
      ime = "Vrsta zunaj";
      pod = `danes ob ${danesZunaj.ura} vrsta zunaj`;
      opozorilo = true;
    } else if (d.prejsnji) {
      n = d.prejsnji.stopnja;
      ime = "Prejšnji poln";
      pod = `prejšnji ob ${d.prejsnji.ura} ${n === 5 ? "poln, vrsta zunaj" : "poln"}`;
      opozorilo = true;
    } else if (o) {
      n = o.mediana;
      ime = `Običajno ${stopnja(n)}`;
      pod = `običajno ${stopnja(n)}${o.mediana >= 4 && o.prej ? ` · pridi ${o.prej.nasvet_min} min prej` : ""}`;
    } else if (zadnje) {
      n = zadnje.stopnja;
      ime = velika(stopnja(n));
      pod = `danes ob ${zadnje.ura} ${stopnja(n)}`;
    } else {
      pod = ok.po ? "poročila potnikov" : ok.pred ? `javiš od ${ok.odUra}` : "javi z enim dotikom";
    }
    gumb.classList.toggle("je-opozorilo", opozorilo);
    gumb.title = `Kako polno? ${pod}`;
    gumb.setAttribute("aria-label", `Kako polno? ${pod}`);
    return `${n ? glif(n, 30) : SVG_LJUDJE}<span class="pomoc-ime">${escapeHtml(ime)}</span>`;
  }

  // Kar velja za ta odhod, pod uro na vrhu okna (`#zas-namig`): danes vrsta
  // zunaj ali poln prejšnji (rdeče), sicer pri običajno polnem „pridi N min
  // prej“ (rumeno). Današnje poročilo samo pove gumb.
  const namigEl = document.getElementById("zas-namig");
  const SVG_NAMIG = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"'
    + ' stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/>'
    + '<path d="M12 7.5V12l3 2"/></svg>';
  function namig(d) {
    if (!namigEl) return;
    const o = d && d.vklopljeno ? d.obicajno : null;
    const danesZunaj = d && d.vklopljeno ? d.danes.find((x) => x.stopnja === 5) : null;
    let html = "", razred = "";
    if (danesZunaj) {
      html = `<b>danes ob ${danesZunaj.ura} vrsta zunaj</b>`;
      razred = "je-rdece";
    } else if (d && d.vklopljeno && d.prejsnji) {
      html = `<b>prejšnji ob ${d.prejsnji.ura} poln</b>${d.prejsnji.stopnja === 5 ? ", vrsta zunaj" : ""}`;
      razred = "je-rdece";
    } else if (o && o.mediana >= 4 && o.prej) {
      html = `<b>pridi ${o.prej.nasvet_min} min prej</b>, običajno ${escapeHtml(stopnja(o.mediana))}`;
      razred = "je-rumeno";
    }
    namigEl.className = `ov-namig ${razred}`;
    namigEl.innerHTML = html ? `${SVG_NAMIG}<span>${html}</span>` : "";
    namigEl.hidden = !html;
  }

  // ------------------------------------------------------------ razdelek

  function okno(d) {
    const zdaj = Date.now() / 1000;
    const [pred, po, zunaj] = d.okno;
    return { pred: zdaj < d.odhod_ts - pred, po: zdaj > d.odhod_ts + po,
             zunajPrezgodaj: zdaj < d.odhod_ts - zunaj,
             odUra: hhmm(new Date((d.odhod_ts - pred) * 1000).toISOString()) };
  }

  function stopnjeHtml(d, ok) {
    const izbrana = S.oddano && !S.oddano.prejsnji ? S.oddano.stopnja : 0;
    return `<div class="zas-stopnje" role="group" aria-label="Kako polno je zdaj">${d.stopnje.map((ime, i) => {
      const n = i + 1;
      const onemogoceno = ok.pred || (n === 5 && ok.zunajPrezgodaj) || S.zaposlen;
      return `<button type="button" class="zas-stopnja${n === izbrana ? " je-izbrana" : ""}"
          data-stopnja="${n}" aria-pressed="${n === izbrana}"${onemogoceno ? " disabled" : ""}>
          ${glif(n)}<span>${escapeHtml(ime)}</span></button>`;
    }).join("")}</div>`;
  }

  function obicajnoHtml(o) {
    const deli = [];
    for (let n = 5; n >= 1; n--) {
      const k = o.stopnje[n - 1];
      if (!k) continue;
      const besedilo = `${escapeHtml(stopnja(n))} ${k}×`;
      deli.push(n === o.mediana ? `<b>${besedilo}</b>` : besedilo);
    }
    let h = `<p class="zas-pod">Običajno ${escapeHtml(o.kdaj)} med ${o.od} in ${o.do}: ${deli.join(", ")}.`;
    if (o.prej) {
      const razpon = o.prej.od_min === o.prej.do_min ? o.prej.do_min : `${o.prej.od_min}–${o.prej.do_min}`;
      h += ` Poln je bil že ${razpon} min pred odhodom.`;
    }
    const obdobje = o.prvi === o.zadnji ? datumKratko(o.prvi) : `${datumKratko(o.prvi)}–${datumKratko(o.zadnji)}`;
    return `${h} <span class="zas-tiho">${o.porocil} ${sklon(o.porocil, "porocilo")}, ${obdobje}</span></p>`;
  }

  function izrisi() {
    const d = S.d;
    namig(d);
    if (!d || !d.vklopljeno) {
      el.hidden = gumb.hidden = true;
      return;
    }
    gumb.hidden = false;
    gumb.innerHTML = gumbHtml(d);
    gumb.setAttribute("aria-expanded", String(odprto()));
    el.hidden = !odprto();
    // Potnik piše ali izbira postajo: osvežitev mu ne sme vzeti polja.
    if (el.contains(document.activeElement) && /^(TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) return;
    const ok = okno(d);
    let h = `<div class="zas-glava"><h2 class="zas-naslov">${ok.po ? "Kako polno je bilo?" : "Kako polno je zdaj?"}</h2>`;
    h += S.izbiraPostaje
      ? `<select class="zas-izbira" aria-label="Postaja">${d.postaje.map((p) =>
          `<option value="${escapeHtml(p.ime)}"${p.ime === d.postaja ? " selected" : ""}>${escapeHtml(lepoIme(p.ime))} · ${p.ura}</option>`).join("")}</select>`
      : `<button type="button" class="zas-postaja" data-akcija="postaja">${escapeHtml(lepoIme(d.postaja))} · <u>spremeni</u></button>`;
    h += "</div>";
    if (!ok.po) h += stopnjeHtml(d, ok);
    if (ok.pred) h += `<p class="zas-pod zas-tiho">Javiš lahko od ${ok.odUra} naprej, ko je vozilo na postaji ali na poti.</p>`;

    if (S.oddano) {
      const kaj = S.oddano.prejsnji
        ? `prejšnji ob ${S.oddano.prejsnji.ura} te ni vzel`
        : `${escapeHtml(stopnja(S.oddano.stopnja))}, ${escapeHtml(lepoIme(S.oddano.postaja))}`;
      h += `<p class="zas-hvala"><b>Hvala,</b> zapisano ob ${S.oddano.ura}: ${kaj}.
        ${Date.now() - S.oddano.t < PREKLIC_MS
          ? `<button type="button" class="zas-tiho-gumb" data-akcija="preklic">prekliči</button>` : ""}</p>`;
    }
    if (S.sporocilo) {
      h += `<p class="zas-hvala${S.sporocilo.napaka ? " je-napaka" : ""}">${escapeHtml(S.sporocilo.napaka || S.sporocilo.ok)}</p>`;
    }

    const danes = d.danes.filter((x) => !S.oddano || x.ura !== S.oddano.ura || x.stopnja !== S.oddano.stopnja);
    if (danes.length) {
      h += `<p class="zas-pod">Danes javljeno: ${danes.map((x) =>
        `${x.ura} ${escapeHtml(stopnja(x.stopnja))}${x.postaja !== d.postaja ? ` (${escapeHtml(lepoIme(x.postaja))})` : ""}`).join(" · ")}</p>`;
    }
    if (d.obicajno) h += obicajnoHtml(d.obicajno);
    else if (d.zgodovina.length) {
      h += `<p class="zas-pod">Ta odhod, ${d.odhod}: ${d.zgodovina.map((z) =>
        `${z.dan} ${datumKratko(z.datum)} ${escapeHtml(stopnja(z.stopnja))}${z.postaja !== d.postaja ? ` (${escapeHtml(lepoIme(z.postaja))})` : ""}`).join(" · ")}</p>`;
    } else if (!danes.length && !S.oddano && !ok.po) {
      h += `<p class="zas-pod zas-tiho">Še nihče ni javil. En dotik pomaga tistim, ki čakajo na naslednjega.</p>`;
    }
    // Javi tuj odhod, zato dva koraka: povezava se je na telefonu oddala ob
    // dotiku med drsenjem (David, 21. 10. 2026).
    if (d.te_ni_vzel && !ok.po && !(S.oddano && S.oddano.prejsnji)) {
      const p = `${escapeHtml(d.te_ni_vzel.oznaka)} ob ${d.te_ni_vzel.ura}`;
      h += S.potrdiNiVzel
        ? `<div class="zas-potrdi"><p>Javim, da te ${p} zaradi gneče ni vzel?</p>
            <div class="zas-gumbi"><button type="button" class="zas-gumb" data-akcija="ni-vzel-da"${S.zaposlen ? " disabled" : ""}>Da, javi</button>
            <button type="button" class="zas-drugo" data-akcija="ni-vzel-ne">Ne</button></div></div>`
        : `<button type="button" class="zas-povezava" data-akcija="ni-vzel">Te prejšnji (${p}) ni vzel?</button>`;
    }

    // Komentar samo k današnji ali včerajšnji vožnji (`zasedenost.preveri_opombo`).
    const vceraj = new Date(Date.now() - 86400000).toLocaleDateString("sv-SE", { timeZone: "Europe/Ljubljana" });
    const smeOpombo = S.zeton && (S.dan === todayIso() || S.dan === vceraj) && !S.opombaPoslana;
    if (smeOpombo && (S.opombaOdprta || S.oddano)) {
      h += `<textarea class="zas-polje" maxlength="280" aria-label="Opomba za druge potnike"
          placeholder="Opomba za druge potnike (neobvezno): kje je bila vrsta, je prišel še en ${OMREZJE === "avtobus" ? "avtobus" : "vlak"} …">${escapeHtml(S.opomba)}</textarea>
        <div class="zas-vrsta"><span class="zas-tiho">Brez imen. Pokaže se, ko jo pregledamo.</span>
        <button type="button" class="zas-gumb" data-akcija="opomba"${S.zaposlen ? " disabled" : ""}>Pošlji</button></div>`;
    }
    const dodaj = smeOpombo && !S.opombaOdprta && !S.oddano
      ? `<button type="button" class="zas-povezava" data-akcija="odpri-opombo">Dodaj opombo za druge potnike</button>` : "";
    // Prazen „Opombe potnikov (0)“ je obljuba brez vsebine: brez opomb samo gumb.
    if (d.opombe.length) {
      h += `<details class="zas-opombe"${S.opombeOdprte ? " open" : ""}>
        <summary>Opombe potnikov (${d.opombe.length})</summary>
        ${d.opombe.map((o) => `<div class="zas-opomba"><small>${o.dan} ${datumKratko(o.datum)} · ${escapeHtml(lepoIme(o.postaja))}</small>`
          + `<p>${escapeHtml(o.besedilo)}</p><a class="zas-prijavi" href="/stik?prijava=${o.id}">Prijavi</a></div>`).join("")}
        ${dodaj}
      </details>`;
    } else {
      h += dodaj;
    }
    h += `<p class="zas-noga">Kar javiš, objavimo brez imena pod CC BY-SA 4.0. <a href="/zasebnost#zasedenost">Zasebnost</a></p>`;
    el.innerHTML = h;
  }

  // --------------------------------------------------------------- strežnik

  async function nalozi() {
    if (!S.trip) return;
    const q = new URLSearchParams({ trip: S.trip, date: S.dan });
    if (postaja()) q.set("postaja", postaja());
    const trip = S.trip;
    const d = await jsonOk(await fetch(`/api/zasedenost?${q}`));
    if (trip !== S.trip) return;          // medtem druga vožnja
    S.d = d;
    const izdan = S.zeton ? +S.zeton.split(".")[0] : 0;
    if (!d.zeton) S.zeton = null;
    else if (Date.now() / 1000 - izdan > ZETON_NAJDLJE_S) S.zeton = d.zeton;
    izrisi();
  }

  async function posljiPorocilo(telo) {
    const r = await fetch("/api/zasedenost", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ service_date: S.dan, postaja: S.d.postaja, naprava: naprava(), ...telo }),
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(j.napaka || "Ni uspelo. Poskusi znova.");
    return j;
  }

  async function dejanje(fn) {
    if (S.zaposlen) return;
    S.zaposlen = true;
    S.sporocilo = null;
    try {
      await fn();
    } catch (e) {
      S.sporocilo = { napaka: e.message || "Ni uspelo. Poskusi znova." };
    } finally {
      S.zaposlen = false;
    }
    izrisi();
    if (poller) poller.zdaj().catch(() => {});
  }

  function javi(n) {
    return dejanje(async () => {
      const j = await posljiPorocilo({ trip_id: S.trip, stopnja: n });
      S.oddano = { ...j, trip: S.trip, prejsnji: null, t: Date.now() };
      // Postaja ostane, kjer je potnik javil, tudi ko vozilo pelje naprej.
      S.izbrana = j.postaja;
    });
  }

  function niVzel() {
    const p = S.d.te_ni_vzel;
    return dejanje(async () => {
      const j = await posljiPorocilo({ trip_id: p.trip_id, stopnja: 5 });
      S.oddano = { ...j, trip: p.trip_id, prejsnji: p, t: Date.now() };
      S.izbrana = j.postaja;
    });
  }

  function preklici() {
    const o = S.oddano;
    return dejanje(async () => {
      await posljiPorocilo({ trip_id: o.trip, preklic: true });
      S.oddano = null;
    });
  }

  function posljiOpombo() {
    const besedilo = S.opomba.trim();
    if (!besedilo) return;
    return dejanje(async () => {
      const r = await fetch("/stik", {
        method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          opomba_trip: S.oddano ? S.oddano.trip : S.trip, opomba_datum: S.dan,
          opomba_postaja: S.d.postaja, besedilo, zeton: S.zeton, naslov: "",
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(j.napaka || "Opombe ni bilo mogoče poslati.");
      S.opomba = "";
      S.opombaOdprta = false;
      S.opombaPoslana = true;
      S.sporocilo = { ok: "Hvala. Opomba se pokaže, ko jo pregledamo." };
    });
  }

  gumb.addEventListener("click", () => {
    pomoc.dataset.odprto = odprto() ? "" : "zas";
    pomoc.dispatchEvent(new Event("pomoc"));
    izrisi();
    if (!el.hidden) {
      el.scrollIntoView({ block: "nearest",
        behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    }
  });
  // Drug razdelek vrstice se je odprl: ta se zapre.
  pomoc.addEventListener("pomoc", () => { if (!odprto()) izrisi(); });

  el.addEventListener("click", (e) => {
    const g = e.target.closest("button");
    if (!g || g.disabled) return;
    if (g.dataset.stopnja) return javi(+g.dataset.stopnja);
    switch (g.dataset.akcija) {
      case "postaja": S.izbiraPostaje = true; izrisi(); el.querySelector(".zas-izbira").focus(); break;
      case "ni-vzel": S.potrdiNiVzel = true; izrisi(); break;
      case "ni-vzel-ne": S.potrdiNiVzel = false; izrisi(); break;
      case "ni-vzel-da": S.potrdiNiVzel = false; niVzel(); break;
      case "preklic": preklici(); break;
      case "opomba": posljiOpombo(); break;
      case "odpri-opombo": S.opombaOdprta = true; izrisi(); el.querySelector(".zas-polje").focus(); break;
      default: break;
    }
  });
  // Odprte opombe ostanejo odprte, ko osvežitev razdelek nariše znova.
  el.addEventListener("toggle", (e) => {
    if (e.target.classList.contains("zas-opombe")) S.opombeOdprte = e.target.open;
  }, true);
  el.addEventListener("input", (e) => {
    if (e.target.classList.contains("zas-polje")) S.opomba = e.target.value;
  });
  el.addEventListener("change", (e) => {
    if (!e.target.classList.contains("zas-izbira")) return;
    S.izbrana = e.target.value;
    S.izbiraPostaje = false;
    e.target.blur();
    if (poller) poller.zdaj().catch(() => {});
  });

  el.addEventListener("zas-voznja", () => {
    const d = el.dataset;
    const nova = d.trip !== S.trip || d.dan !== S.dan;
    const premik = d.privzeta !== S.privzeta && !S.izbrana;
    Object.assign(S, { trip: d.trip, dan: d.dan, privzeta: d.privzeta });
    if (nova) {
      // Druga vožnja: nič od prejšnje ne sme ostati, ne odgovor ne osnutek --
      // dotik pred novim odgovorom bi poslal novo vožnjo s staro postajo.
      Object.assign(S, { izbrana: null, oddano: null, sporocilo: null, opombaPoslana: false,
                         d: null, opomba: "", opombaOdprta: false, izbiraPostaje: false,
                         potrdiNiVzel: false });
      el.hidden = gumb.hidden = true;
    }
    if (!poller) poller = pollWhileVisible(nalozi, OSVEZI_MS);
    else if (nova || premik) poller.zdaj().catch(() => {});
  });
})();
