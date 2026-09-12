"use strict";

// Domaca stran. Razcepisce, ne nadzorna plosca; kdor hoce podrobnosti, klikne
// naprej.
//
// **Zivih stevilk tu ni.** Bili sta dve: "danes obicajno: vlaki +2 min ·
// avtobusi +1 min" in stevec vozil "na poti" pri vsaki kartici. Prva je vsak
// dan skoraj ista, torej ne spremeni nicesar, kar bo clovek na tej strani
// storil; druga je podatek o omrezju in ne o njegovi poti. Z njima sta odpadli
// dve zahtevi od treh -- `/api/overview` in `/api/overview/bus` sta bili
// najdrazji na strani, ki je samo razcepisce.

async function load() {
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
// Iskalnik ju hrani po omrezju (`kajros:fav`, `kajros:recent`), domaca stran
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

// **Samo shranjeno, nic samodejnega.** Prej so bile tu tudi nedavne poti, ki
// se napisejo same ob vsakem iskanju -- tudi ob enem samem pogledu na odhodno
// tablo. Domaca stran je s tem postala seznam vsega, kar si kdaj pogledal,
// odstraniti pa se ni dalo nicesar: kriz je samo na shranjenih.
function izrisiPoti() {
  const seen = new Set();
  const poti = [];
  for (const f of beri("kajros:fav")) {
    const k = kljucPoti(f);
    if (seen.has(k)) continue;
    seen.add(k);
    poti.push(f);
    if (poti.length >= 6) break;
  }
  if (!poti.length) return;              // prazen naslov ne pove nicesar
  document.getElementById("home-chips").innerHTML = poti.map((f) => `
    <a class="chip chip-${f.net === "avtobus" ? "bus" : "train"}"
       href="${escapeHtml(znackaHref(f))}">
      <span class="chip-star">★</span>
      <span>${escapeHtml(znackaOpis(f))}</span>
    </a>`).join("");
  document.getElementById("home-saved").hidden = false;
}

izrisiPoti();
load();
