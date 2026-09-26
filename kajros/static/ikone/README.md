# Ikone

Nastanejo iz `scripts/naredi-ikone.sh`, ne ročno.

* `icon-192.png`, `icon-512.png` — zaobljen kvadrat, za PWA in favicon
* `icon-maskable-512.png` — **polna podlaga brez zaobljenih vogalov**, znak stisnjen na 66 % (varna cona). Android obliko izreže sam; zaobljen kvadrat bi obrezal še enkrat → vogali vidni.

**Chromium ne more brati iz `/tmp`.** Prva različica ikon zato = posnetek njegove strani z napako `ERR_FILE_NOT_FOUND` — 512 in maskirana imeli enak `md5`, edini znak napake. Vmesne strani zato nastajajo v `posnetki/`.
