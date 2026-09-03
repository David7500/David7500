"use strict";

// Stran "kdaj se splača potovati".
//
// Vprašanje ni "kakšna je statistika", ampak "ob kateri uri naj grem". Zato
// je na vrhu ena poved z odgovorom, spodaj pa razrezi, ki jo utemeljijo.
// Vse tri številke prihajajo iz `/api/stats/breakdowns`, ki je dnevni povzetek
// -- agregata čez vso zgodovino se v zahtevi ne računa.

const NETWORK = document.body.dataset.network || "zeleznica";
const IS_BUS = NETWORK === "avtobus";
const DNI = 90;

// Vrstica z manj kot toliko vožnjami je šum, ne ugotovitev. Meja ni okrogla
// zaradi lepote: pri 12 dneh zajema ima ura z 20 vožnjami manj kot dve na dan
// in ena zamujena garnitura ji premakne mediano čez cel razred.
const MIN_VZOREC = 30;

const el = (id) => document.getElementById(id);

function minute(s) {
  return s == null ? "—" : `${Math.round(s / 60)} min`;
}

// Ura iz feeda je "07"; potnik bere "07:00". Dan v tednu pride že po slovensko.
function imeUre(k) {
  return `${k}:00`;
}

/** Ena vrstica: ime, tir s stolpcem, vrednost, vzorec. */
function vrstica(ime, medianaS, n, najvecS, oznaka) {
  const tanka = n < MIN_VZOREC;
  // Presezek se odreze na 100 % in vrstica dobi znak "gre cez" -- brez tega
  // bi merilo spet doloceval izjemec.
  const surovo = najvecS > 0 ? (medianaS / najvecS) * 100 : 2;
  const delez = Math.max(2, Math.min(100, surovo));
  const cez = surovo > 100;
  const razred = ["stat-vrsta", tanka ? "je-tanka" : "", cez ? "gre-cez" : "",
                  oznaka || ""].filter(Boolean).join(" ");
  return `<div class="${razred}">
    <div class="stat-ime">${escapeHtml(ime)}</div>
    <div class="stat-tir">
      <div class="stat-stolpec" style="width:${delez.toFixed(1)}%;background:${delayColor(medianaS)}"></div>
    </div>
    <div class="stat-vrednost">${minute(medianaS)}</div>
    <div class="stat-n" title="${n} zajetih voženj">${n}×</div>
  </div>`;
}

/** Iz seznama razrezov naredi vrstice; `preslikaj` da ime iz ključa. */
function narisi(cilj, vrstice, preslikaj, poudari) {
  if (!vrstice || !vrstice.length) {
    cilj.innerHTML = `<div class="empty-state">za to omrežje še ni dovolj zajema</div>`;
    return;
  }
  // Merilo postavijo SAMO vrstice z dovolj vzorca. Sicer ena nocna ura z
  // devetimi voznjami in 24 minutami stisne cel dan v pahljace po dve piki --
  // vrstica, ki ji ne verjamemo dovolj za naslov, ne sme voditi slike.
  const zanesljive = vrstice.filter((v) => v.n >= MIN_VZOREC);
  const najvec = Math.max(...(zanesljive.length ? zanesljive : vrstice)
                            .map((v) => v.median_s || 0), 1);
  cilj.innerHTML = vrstice
    .map((v) => vrstica(preslikaj(v.key), v.median_s, v.n, najvec,
                        poudari ? poudari(v) : ""))
    .join("");
}

// Naslov sme primerjati samo ure, ko promet res teče. Brez tega je odgovor
// "ob 03:00 vlaki zamujajo 0 min" -- resničen, a za izbiro poti neuporaben,
// ker takrat skoraj nič ne vozi.
//
// Meja ni izbrana po občutku, ampak izmerjena: delež postankov glede na
// najprometnejšo uro pade s 34 % (04:00) na 4,9 % (03:00) in z 39 % (22:00)
// na 21,6 % (23:00). Prelom je čist, zato prag 25 %.
const DELEZ_PROMETA = 0.25;

/** Najboljša in najslabša vrstica med urami z rednim prometom. */
function skrajni(vrstice) {
  const vse = vrstice || [];
  const najvecN = Math.max(...vse.map((v) => v.n || 0), 1);
  const dobre = vse.filter((v) => v.n >= MIN_VZOREC && v.n >= najvecN * DELEZ_PROMETA);
  if (dobre.length < 2) return null;
  const po = [...dobre].sort((a, b) => a.median_s - b.median_s);
  return { naj: po[0], nic: po[po.length - 1] };
}

// Ure po POSTANKU, ne po odhodu vožnje -- glej `stats.summary_build`.
// Zasilni izhod na `by_hour`, dokler dnevni povzetek ni preračunan.
function urneVrstice(d) {
  return (d.by_stop_hour && d.by_stop_hour.length) ? d.by_stop_hour : (d.by_hour || []);
}

function glava(d) {
  const ure = skrajni(urneVrstice(d));
  const dni = (d.days || []).length;
  const obseg = `<div class="stat-obseg">
      <span>zajetih dni <b>${dni}</b></span>
      <span>voženj <b>${(d.runs || 0).toLocaleString("sl")}</b></span>
      <span>zadnji dan <b>${escapeHtml(d.through || "—")}</b></span>
      <span class="adv-only">izračunano <b>${escapeHtml((d.computed_at || "").replace("T", " ").slice(0, 16))}</b></span>
    </div>`;

  // Brez dovolj vzorca se poved ne napiše. Prazen prostor je boljši od
  // trditve, ki je podatki ne nosijo -- in pri dvanajstih dneh je to blizu.
  if (!ure) {
    el("stat-glava").innerHTML =
      `<div class="stat-poved">Zajema je zaenkrat premalo, da bi katera ura
       izstopala. Spodnji razrezi so že tu, a jih beri z vzorcem vred.</div>${obseg}`;
    return;
  }
  const vozilo = IS_BUS ? "avtobusi" : "vlaki";
  el("stat-glava").innerHTML = `<div class="stat-poved">
      Ob <strong>${imeUre(ure.naj.key)}</strong> ${vozilo} zamujajo
      <strong>${minute(ure.naj.median_s)}</strong>, ob
      <span class="stat-slabo">${imeUre(ure.nic.key)}</span> pa
      <span class="stat-slabo">${minute(ure.nic.median_s)}</span>.
    </div>${obseg}`;
}

function opozoriloDnevi(d) {
  const dni = (d.days || []).length;
  const naTeden = dni / 7;
  const p = el("dnevi-opozorilo");
  if (naTeden < 4) {
    p.className = "stat-pod stat-tanko";
    p.textContent = `Zajema je ${dni} dni, torej ${naTeden.toFixed(1)} ponovitve`
      + ` vsakega dne v tednu. Za trditev "ta dan je najhujši" je to premalo;`
      + ` razlike spodaj so lahko naključje.`;
  } else {
    p.className = "stat-pod";
    p.textContent = "Mediana končne zamude po dnevu v tednu.";
  }
}

function legenda() {
  return `<div class="stat-legenda">
    ${DELAY_RAMP.map((s) => `<span><i style="background:${s.color}"></i>${s.label}</span>`).join("")}
  </div>`;
}

async function zacni() {
  el("vrste-naslov").textContent = IS_BUS ? "Po prevozniku" : "Po vrsti vlaka";
  el("vrste-pod").textContent = IS_BUS
    ? "Mediana končne zamude po prevozniku."
    : "Mediana končne zamude po vrsti vlaka (IC, MV, LP …).";
  try {
    const res = await fetch(`/api/stats/breakdowns?days=${DNI}&network=${NETWORK}`);
    if (!res.ok) throw new Error(res.status);
    const d = await res.json();

    glava(d);
    // Ure zunaj obratovanja so prazne vrstice, ki samo stiskajo ostale.
    narisi(el("ure"), urneVrstice(d).filter((v) => v.n > 0), imeUre, (v) => {
      const s = skrajni(urneVrstice(d));
      if (!s) return "";
      if (v.key === s.naj.key) return "je-najboljsa";
      if (v.key === s.nic.key) return "je-najslabsa";
      return "";
    });
    el("ure").insertAdjacentHTML("afterend", legenda());

    opozoriloDnevi(d);
    narisi(el("dnevi"), d.by_weekday, (k) => k);
    narisi(el("vrste"), d.by_kind, (k) => k);
    narisi(el("dan-za-dnem"), d.by_day, (k) => k.slice(5).replace("-", ". ") + ".");

    el("stat-noga").innerHTML =
      `Končna zamuda vožnje, mediana. Vir: IJPP prek NAP (CC BY-SA 4.0),`
      + ` obdelava DERP. Razrez se izračuna enkrat na dan, ne ob vsakem obisku;`
      + ` čas izračuna je pri "napredno".`;
  } catch (e) {
    el("ure").innerHTML = `<div class="empty-state">podatki trenutno niso dosegljivi</div>`;
  }
}

zacni();
