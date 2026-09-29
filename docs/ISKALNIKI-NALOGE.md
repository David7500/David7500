# Iskalniki in AI: kar mora narediti David

Kar se je dalo narediti v kodi, je narejeno in objavljeno (29. 9. 2026, glej
`docs/MERITVE.md`, „Iskalniki“). Spodaj so koraki, ki rabijo tvojo prijavo ali
tvoje ime. Vrstni red je po učinku.

## 1. Google Search Console (15 minut, najpomembnejše)

Brez tega Google za stran ne ve. Gemini in Googlov povzetek z AI berejo samo
Googlov indeks.

1. Odpri <https://search.google.com/search-console> in se prijavi.
2. **Dodaj lastnost → Domena** (levo polje, ne „Predpona URL-ja“) → `kajros.app`.
3. Google pokaže zapis TXT (`google-site-verification=…`). Kopiraj ga.
4. V Cloudflaru: **kajros.app → DNS → Records → Add record**: vrsta `TXT`,
   ime `@`, vsebina = kopirani niz. Shrani.
5. Nazaj v Search Console → **Preveri**. Če ne gre takoj, počakaj nekaj minut.
6. **Zemljevidi strani** → vpiši `sitemap.xml` → Pošlji.
7. **Pregled URL-ja** (iskalna vrstica na vrhu) → za vsakega od spodnjih
   vpiši naslov in pritisni **Zahtevaj indeksiranje**:
   - `https://kajros.app/`
   - `https://kajros.app/vlak/ljubljana/maribor`
   - `https://kajros.app/vlak/ljubljana/koper`
   - `https://kajros.app/avtobus/ljubljana-ap/maribor-ap`
   - `https://kajros.app/primerjava`

## 2. Bing Webmaster Tools (5 minut)

Bing je vir za ChatGPT, Copilot in DuckDuckGo. Prvih 100 naslovov je Bing
prek IndexNow že sprejel, ostale pošlje naslednja objava, ko bo ključ
preverjen. Webmaster Tools doda poročila in potrdi lastništvo.

1. <https://www.bing.com/webmasters> → prijava.
2. **Import from Google Search Console** (po koraku 1) — prenese lastnost in
   zemljevid strani.

## 3. Cloudflare: roboti za učenje modelov (odločitev)

Danes Cloudflare vrača 403 robotom GPTBot, ClaudeBot, CCBot (Common Crawl),
Amazonbot in Bytespider. Iskanje z AI (ChatGPT, Claude, Perplexity) stran
bere; v znanje modelov pa kajros ne pride.

Če hočeš, da model za kajros ve tudi brez iskanja: **kajros.app → AI Crawl
Control** (ali **Security → Bots**) → pri teh robotih izberi **Allow**.
Cena: nekaj več zahtev na arwen.

## 4. Omembe drugod (ko Google pokaže prve strani)

AI na vprašanje „najboljša stran za zamude“ odgovori iz strani, ki o straneh
pišejo. Za zamudil.si je Grok navedel Dnevnik, za brezavta.si Val 202, RTV in
OPSI. Povsod povej, da si avtor.

- **X** — Grok bere X naravnost. Osnutek spodaj.
- **Reddit r/Slovenia** — med najpogosteje citiranimi viri v odgovorih AI.
- **slo-tech.com**, forum.
- **OPSI** (<https://podatki.gov.si>) — seznam aplikacij, ki uporabljajo odprte
  podatke. Kajros uporablja podatke IJPP z NAP; prijava prek obrazca ali
  e-pošte skrbnikom portala.
- **Novinar** — zgodba s številko, ki je nima nihče drug.

Številke v osnutkih so s strani 29. 9. 2026. Pred objavo jih preveri na strani.

### Osnutek za X

> Naredil sem kajros.app: zamude vlakov in avtobusov po Sloveniji v živo in
> koliko vsaka relacija običajno zamuja. Ljubljana → Koper: mediana +15 min,
> v petih minutah pride 2 % vlakov. Brez oglasov, brez računa.
> https://kajros.app/vlak/ljubljana/koper

### Osnutek za Reddit in slo-tech

> **Naslov:** Naredil sem stran, ki beleži, koliko vlaki in avtobusi v
> Sloveniji res zamujajo
>
> Od avgusta zapisujem vsako zamudo, ki jo objavijo prevozniki (odprti podatki
> IJPP prek NAP), za vlake SŽ, medkrajevne avtobuse in mestni LPP. Za vsako
> relacijo in postajo stran pove, koliko običajno zamuja, ne le zdajšnje
> zamude. Nekaj številk:
>
> - Ljubljana → Koper: mediana +15 min, v petih minutah pride 2 % vlakov
> - Ljubljana → Maribor: mediana +9 min
>
> Ima še iskalnik povezav, pot od vrat do vrat z vlakom in avtobusom ter
> aplikacijo za Android z budilko, ki se premakne z zamudo.
>
> https://kajros.app — sem avtor, zanimajo me pripombe in napake.

### Osnutek za novinarja

> **Zadeva:** Koliko res zamujajo vlaki: podatki za vsako relacijo
>
> Pozdravljeni, od avgusta 2026 beležim vsako zamudo vlakov SŽ in
> medkrajevnih avtobusov iz javnih podatkov. Nekaj ugotovitev: na relaciji
> Ljubljana → Koper je mediana zamude ob prihodu 15 minut, v petih minutah
> pride 2 % vlakov. Podatki za vsako relacijo in postajo so javni na
> https://kajros.app. Z veseljem pripravim številke za relacije, ki vas
> zanimajo.

## Ko je narejeno

- V `/admin` sta od 29. 9. 2026 plošči **Od kod pridejo** (Google, Bing,
  ChatGPT …) in **Roboti** (Googlebot, bingbot, OAI-SearchBot …). Po oddaji
  zemljevida strani pričakuj Googlebot v nekaj dneh.
- IndexNow teče sam ob vsaki objavi na arwen, kadar se nabor strani
  spremeni (`deploy/posodobi.sh`, dnevnik `~/kajros-indexnow.log` na arwenu).
