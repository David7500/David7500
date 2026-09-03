# Ikone

Nastanejo iz `scripts/naredi-ikone.sh`, ne ročno.

* `icon-192.png`, `icon-512.png` — zaobljen kvadrat, za PWA in favicon
* `icon-maskable-512.png` — **polna podlaga brez zaobljenih vogalov**, znak
  stisnjen na 66 % (varna cona). Android si obliko izreže sam; če bi mu dali
  zaobljen kvadrat, bi ga obrezal še enkrat in vogali bi se poznali.

**Chromium ne more brati iz `/tmp`.** Prva različica teh ikon je bila zato
posnetek njegove strani z napako `ERR_FILE_NOT_FOUND` — 512 in maskirana sta
imeli enak `md5`, kar je bilo edino, kar je to razkrilo. Vmesne strani zato
nastajajo v `posnetki/`.
