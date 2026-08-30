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
    document.getElementById("home-live").innerHTML =
      `<span class="live-dot"></span>`
      + `zdaj na poti <strong>${nt}</strong> ${nt === 1 ? "vlak" : "vlakov"}`
      + ` in <strong>${nb}</strong> ${nb === 1 ? "avtobus" : "avtobusov"}`;
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

load();
