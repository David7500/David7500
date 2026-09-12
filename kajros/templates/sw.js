/* Service worker. Predloga -- streže ga `api.sw()`, ki vanjo vpiše različico.
 *
 * Napisan je šele zdaj in ne prej, ker se po `http://` ne more registrirati
 * (izmerjeno: `isSecureContext` je po omrežnem naslovu `false`). Do
 * Cloudflarovega tunela bi bil mrtva koda.
 *
 * ENO PRAVILO JE NAD VSEMI: `/api/` se ne predpomni nikoli.
 *
 * Ta projekt meri zamude. Zamuda iz predpomnilnika je laž -- in to najhujša
 * vrsta, ker je videti kot podatek in nosi uro. Potnik, ki bi videl „+2 min"
 * izpred pol ure, bi zamudil vlak, o katerem misli, da ima čas. Zato gre vsaka
 * zahteva pod `/api/` naravnost v omrežje in tam, kjer omrežja ni, odgovora
 * preprosto ni -- prikaz to že zna povedati.
 */

const RAZLICICA = "{{ razlicica }}";
const LUPINA = `kajros-lupina-${RAZLICICA}`;
const STATIKA = `kajros-statika-${RAZLICICA}`;
const STRANI = `kajros-strani-${RAZLICICA}`;

// Kar mora biti na voljo takoj in na vsaki strani. Ostala statika se nabere
// med rabo: vnaprejšnji prenos vsega bi bil ~800 kB mobilnih podatkov za
// strani, ki jih ta obiskovalec morda nikoli ne odpre.
const LUPINA_FILE = {{ lupina | tojson }};

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(LUPINA).then((c) => c.addAll(LUPINA_FILE))
                                .then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  // Naslovi statike nosijo odtis vsebine, zato se stari vnosi ne povozijo,
  // ampak kopičijo. Ob novi različici gredo vsi ven naenkrat.
  e.waitUntil(caches.keys()
    .then((k) => Promise.all(k.filter((n) => !n.endsWith(RAZLICICA))
                              .map((n) => caches.delete(n))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;   // ploščice, tuji viri

  // Meritve, lege in vse živo. Brez predpomnilnika, brez izjeme.
  if (url.pathname.startsWith("/api/")) return;

  // Pregled za skrbnika ne sme pustiti sledi na napravi.
  if (url.pathname.startsWith("/admin")) return;

  // Statika je po odtisu vsebine nespremenljiva: ko je enkrat tu, je prava.
  if (url.pathname.startsWith("/static/")) {
    e.respondWith(caches.match(req).then((zadetek) => zadetek || fetch(req)
      .then((odgovor) => {
        if (odgovor.ok) {
          const kopija = odgovor.clone();
          caches.open(STATIKA).then((c) => c.put(req, kopija));
        }
        return odgovor;
      })));
    return;
  }

  // Strani: najprej omrežje, ker vsebujejo tudi številke. Predpomnilnik je
  // rezerva za predor in dvigalo, ne vir resnice.
  if (req.mode === "navigate") {
    e.respondWith(fetch(req)
      .then((odgovor) => {
        if (odgovor.ok) {
          const kopija = odgovor.clone();
          caches.open(STRANI).then((c) => c.put(req, kopija));
        }
        return odgovor;
      })
      .catch(() => caches.match(req)
        .then((zadetek) => zadetek || caches.match("/brez-omrezja"))));
  }
});
