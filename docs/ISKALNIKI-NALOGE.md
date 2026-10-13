# Iskalniki in AI: kar mora narediti David

Kar se je dalo narediti v kodi, je narejeno in objavljeno (29. 9. 2026, glej
`docs/MERITVE.md`, „Iskalniki“). Spodaj so koraki, ki rabijo tvojo prijavo ali
tvoje ime. Vrstni red je po učinku.

## 1. Google Search Console (15 minut, najpomembnejše)

**Narejeno 29. 9. 2026:** lastnost `kajros.app` je obstajala, zemljevid strani
je oddan (1 984 strani), indeksiranje zahtevano za vseh pet strani spodaj.
Koraki ostanejo za primer, ko bo treba ponoviti.

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

**Narejeno 29. 9. 2026:** uvoz iz Search Console lastnosti vrste „domena“ ne
najde, zato je stran dodana ročno (`https://kajros.app/`) z oznako
`msvalidate.01` na domači strani (oznaka mora ostati). Lastništvo potrjeno,
`https://kajros.app/sitemap.xml` oddan pod **Sitemaps**.

1. <https://www.bing.com/webmasters> → prijava.
2. **Import from Google Search Console** (po koraku 1) — prenese lastnost in
   zemljevid strani.

## 3. Cloudflare: roboti za učenje modelov (odločitev)

**Narejeno 29. 9. 2026:** roboti za učenje so spuščeni. Nastavitev je v
**Security → Settings → Configure AI bot policies → Training: Allow**
(posamezna stikala v AI Crawl Control so zaklenjena, dokler velja ta
politika). `robots.txt` nosi `ai-train=yes`. Nazaj: isto mesto, „Disallow“.

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

Številke v osnutkih za X in novinarja so s strani 29. 9. 2026, za Reddit s
13. 10. 2026. Pred objavo jih preveri na strani.

### Osnutek za X

> Naredil sem kajros.app: zamude vlakov in avtobusov po Sloveniji v živo in
> koliko vsaka relacija običajno zamuja. Ljubljana → Koper: mediana +15 min,
> v petih minutah pride 2 % vlakov. Brez oglasov, brez računa.
> https://kajros.app/vlak/ljubljana/koper

### Osnutek za Reddit in slo-tech

Osveženo 13. 10. 2026 (vzorec 21. 8.–13. 10.). Za Reddit: objava s sliko
`posnetki/reddit-novo-mesto.png` (vrh pristajalne strani, 412 px; tabele
odhodov namenoma ni na sliki, glej opombo spodaj). Povezava brez `utm`:
Reddit s spleta pošlje `Referer` (v /admin „Reddit“), aplikacija Reddit
`com.reddit.frontpage`.

> **Naslov:** Od avgusta beležim zamude vlakov in avtobusov po Sloveniji. V
> Novo mesto pride v petih minutah le vsak šesti vlak.
>
> Naveličal sem se ugibanja, koliko bo vlak zamujal, zato sem naredil
> kajros.app. Od avgusta shranjuje vsako zamudo, ki jo objavijo SŽ,
> medkrajevni avtobusi (Arriva, Nomago …) in LPP, in za vsako relacijo pove,
> koliko običajno zamuja, ne le, koliko zamuja zdaj.
>
> Nekaj številk (21. 8.–13. 10.):
>
> - vlak Ljubljana → Novo mesto: običajno +15 min, v petih minutah pride
>   17 % (553 voženj)
> - vlak Ljubljana → Koper: +17 min, v petih minutah 4 % (139 voženj)
> - vlak Ljubljana → Maribor: +9 min, 37 % (496 voženj)
> - vlak Ljubljana → Kranj: +1 min, 74 % — da ni vse slabo
> - avtobus Ljubljana → Maribor: +10 min, 40 % (220 voženj)
>
> Poleg tega: zemljevid vlakov in avtobusov v živo, iskalnik povezav, pot od
> vrat do vrat z vlakom in avtobusom ter aplikacija za Android z budilko, ki
> se premakne, kadar vlak zamuja. Brez oglasov in brez računa.
>
> https://kajros.app
>
> Sem avtor. Zanima me, kaj manjka in kaj ne dela.

**Objavljeno 13. 10. 2026 zvečer** na r/Slovenia (oznaka „Website“, račun
u/kajros00-00). r/promet (43K obiskovalcev na teden) čez nekaj dni z
drugačnim poudarkom, ne iste objave.

### Osnutek za slo-tech (13. 10. 2026)

**Objavljeno 13. 10. 2026:** https://slo-tech.com/forum/t857650 (račun „kajros“).

Nova tema v **Loži** (največ obiska; „Na cesti“ je o avtomobilih). Slo-tech
pošlje `Referer`, v /admin „Slo-Tech“. Ozadje: tema „Slovenske železnice“
(`slo-tech.com/forum/t370036`) je živa, tam pozneje odgovor s povezavo na
relacijo, ko kdo potoži nad svojo progo.

> **Naslov:** Zamude vlakov in avtobusov: od avgusta beležim vsako
>
> Od avgusta zbiram zamude slovenskega javnega prevoza: vlake SŽ, medkrajevne
> avtobuse (Arriva, Nomago, AP Murska Sobota …) in mestni LPP. Vir so odprti
> podatki IJPP z NAP (CC BY-SA 4.0), za mestni LPP še njihovi podatki.
> Prevozniki zamude objavljajo sproti, hrani pa jih nihče, zato jih hranim
> sam. V 54 dneh se je nabralo okoli 18 milijonov zapisanih sprememb zamud.
>
> Iz tega stran za vsako relacijo pove, koliko običajno zamuja, ne le, koliko
> zamuja zdaj (21. 8.–13. 10.):
>
> - vlak Ljubljana → Novo mesto: običajno +15 min, v petih minutah pride
>   17 % (553 voženj)
> - vlak Ljubljana → Koper: +17 min, 4 % (139 voženj)
> - vlak Ljubljana → Maribor: +9 min, 37 % (496 voženj)
> - vlak Ljubljana → Kranj: +1 min, 74 %
> - avtobus Ljubljana → Maribor: +10 min, 40 % (220 voženj)
>
> Kaj še zna:
>
> - zemljevid vlakov in avtobusov v živo
> - iskalnik povezav s prestopi, z zamudami v živo
> - pot od vrat do vrat z vlakom in avtobusom, z vodenjem po pešpoti
> - napoved zamude za postaje naprej po progi, iz zgodovine iste vožnje
> - aplikacija za Android (APK s strani) z budilko, ki se premakne, ko vlak
>   zamuja
>
> Tehnično: Python (FastAPI) in SQLite, prikaz v navadnem JS, zemljevid
> MapLibre, pešpoti z lastnim OSRM. Napoved preverjam za nazaj: kaj je stran
> pokazala 25 minut pred odhodom in kaj se je potem res zgodilo.
>
> Brez oglasov in brez računa: https://kajros.app
>
> Zanimajo me pripombe in napake, posebej z relacij, s katerimi se vozite
> sami.

**Opomba ob objavi 13. 10. 2026:** tabela „Odhodi danes“ na pristajalni
strani pri že odpeljanih vlakih kaže zamudo **ob odhodu** iz izhodišča,
naslov nad njo pa običajno zamudo **ob prihodu**. Pri Ljubljana → Novo mesto
je tisti dan stolpec kazal „0 min“ pri vseh vlakih, RG 609 pa je v Novo
mesto prišel z +28 min. Kdor s slike klikne na stran, vidi nasprotje.

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
