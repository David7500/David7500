"use strict";

// Domaca stran. Ena zahteva na omrezje in nic vec -- to je razcepisce, ne
// nadzorna plosca; kdor hoce podrobnosti, klikne naprej.

async function load() {
  try {
    const [o, b] = await Promise.all([
      fetch("/api/overview").then((r) => r.json()),
      fetch("/api/overview/bus").then((r) => r.json()),
    ]);
    const nt = o.live_trains || 0;
    const nb = b.live_vehicles || 0;
    document.getElementById("n-train").textContent = nt;
    document.getElementById("n-bus").textContent = nb;
    // Stevili "na poti" sta ze na karticah, 60 px nizje. Ista dva podatka
    // dvakrat sta zapravljena vrstica -- tu zato pove, kako danes vozijo,
    // kar je vprasanje, zaradi katerega je clovek prisel.
    // Zjutraj je danasnji vzorec droben (ob 6:50 nekaj koncanih voznj) in
    // "0 min" iz treh vozenj ni slika dneva. Streznik zato posilja `yesterday`
    // natanko takrat, kadar je danasnjih premalo -- in beseda nad stevilko
    // mora povedati, kateri dan to je.
    const dan = (x) => (x && x.yesterday && x.yesterday.runs ? x.yesterday : x.today);
    const del = (x) => {
      const d = dan(x);
      return d && d.runs ? `${delayLabel(d.median_s)} min` : null;
    };
    const dv = del(o), da = del(b);
    const vceraj = !!(o.yesterday && o.yesterday.runs) || !!(b.yesterday && b.yesterday.runs);
    document.getElementById("home-live").innerHTML = dv || da
      ? `<span class="live-dot"></span>${vceraj ? "včeraj" : "danes"} običajno:`
        + (dv ? ` vlaki <strong>${dv}</strong>` : "")
        + (dv && da ? " ·" : "")
        + (da ? ` avtobusi <strong>${da}</strong>` : "")
      : `<span class="live-dot"></span>zajem teče`;
  } catch (err) {
    document.getElementById("home-live").textContent = "podatki trenutno niso dosegljivi";
  }
  try {
    const h = await fetch("/api/health").then((r) => r.json());
    document.getElementById("home-health").textContent =
      ` · zajetih ${h.runs_recorded.toLocaleString("sl-SI")} meritev v ${h.days_covered} dneh`;
  } catch (err) {
    /* obseg zajema je postranska informacija */
  }
}

// ---------- shranjene in nedavne poti ----------
//
// Iskalnik ju hrani po omrezju (`sztrack:fav`, `sztrack:recent`), domaca stran
// pa je edino mesto pred izbiro omrezja -- zato ju bere obe hkrati in vsaka
// znacka nosi svoje omrezje s sabo. Priljubljene gredo pred nedavne: prve je
// clovek povedal sam, druge se je napisalo samo.
function beri(kljuc) {
  try {
    const all = JSON.parse(localStorage.getItem(kljuc) || "[]");
    return Array.isArray(all) ? all.filter((x) => x && x.net) : [];
  } catch (err) {
    return [];
  }
}

function znackaHref(f) {
  const pot = f.net === "avtobus" ? "/app/bus" : "/app/train";
  const q = new URLSearchParams();
  if (f.kind === "board") {
    q.set("station", f.station);
    if (f.dir) q.set("kind", f.dir);
  } else {
    q.set("from", f.from || "");
    q.set("to", f.to || "");
  }
  return `${pot}?${q}`;
}

function znackaOpis(f) {
  return f.kind === "board"
    ? `${f.station}${f.dir === "prihodi" ? " · prihodi" : ""}`
    : `${f.from} → ${f.to}`;
}

function kljucPoti(f) {
  return `${f.net}|${f.kind === "board"
    ? `b:${f.station}:${f.dir || "odhodi"}` : `a:${f.from}:${f.to}`}`;
}

function izrisiPoti() {
  const seen = new Set();
  const poti = [];
  for (const [vir, list] of [["fav", beri("sztrack:fav")],
                             ["recent", beri("sztrack:recent")]]) {
    for (const f of list) {
      const k = kljucPoti(f);
      if (seen.has(k)) continue;         // priljubljena ne sme se enkrat kot nedavna
      seen.add(k);
      poti.push({ f, vir });
      if (poti.length >= 6) break;
    }
    if (poti.length >= 6) break;
  }
  if (!poti.length) return;              // prazen naslov ne pove nicesar
  document.getElementById("home-chips").innerHTML = poti.map(({ f, vir }) => `
    <a class="chip chip-${f.net === "avtobus" ? "bus" : "train"}"
       href="${escapeHtml(znackaHref(f))}">
      ${vir === "fav" ? '<span class="chip-star">★</span>' : ""}
      <span>${escapeHtml(znackaOpis(f))}</span>
    </a>`).join("");
  document.getElementById("home-saved").hidden = false;
}

izrisiPoti();
load();
