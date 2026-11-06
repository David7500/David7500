/* Grafi statistike (`_stat.html`, makro `graf`): poteg s prstom ali miško
 * izbere stolpec pod seboj, odčitek se izpiše nad grafom.
 *
 * Stran je brez tega skripta cela -- izris in izpis sta na strežniku in v CSS
 * (`:focus` stolpca, `attr(data-o)`), dotik na stolpec dela tudi tako. Tu je
 * samo, česar CSS ne zna: najbližji stolpec, ker je tridesetina kartice pod
 * prstom težko zadeti (in nizek stolpec skoraj nemogoče), in poteg čez graf
 * brez dvigovanja prsta. Izbira je fokus in ne razred, da je izpis vedno en
 * sam: fokus ima lahko le en element.
 */

for (const graf of document.querySelectorAll(".st-graf")) {
  const stolpci = [...graf.querySelectorAll("[data-o]")];
  if (!stolpci.length) continue;

  const izberi = (x) => {
    let naj = null;
    let razdalja = Infinity;
    for (const s of stolpci) {
      const r = s.getBoundingClientRect();
      const d = Math.abs(x - (r.left + r.width / 2));
      if (d < razdalja) {
        razdalja = d;
        naj = s;
      }
    }
    if (naj && document.activeElement !== naj) naj.focus({ preventScroll: true });
  };

  // Brskalnik bi ob dotiku dal fokus elementu pod prstom (ali nikomur, če je
  // prst nad nizkim stolpcem); fokus damo sami najbližjemu.
  graf.addEventListener("pointerdown", (e) => {
    e.preventDefault();
    izberi(e.clientX);
  });
  // `touch-action: pan-y` (statistika.css): navpični poteg drsi stran, vodoravni
  // pride sem.
  graf.addEventListener("pointermove", (e) => {
    if (e.pointerType === "mouse" || e.buttons) izberi(e.clientX);
  });
  graf.addEventListener("pointerleave", (e) => {
    if (e.pointerType === "mouse" && graf.contains(document.activeElement)) document.activeElement.blur();
  });
}
