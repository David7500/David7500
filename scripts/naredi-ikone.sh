#!/usr/bin/env bash
# Ikone aplikacije iz znaka. Poženi po vsaki spremembi logotipa.
#
# Chromium ne more brati iz /tmp (isti razlog, kot da tja ne more pisati),
# zato vmesne strani nastanejo v posnetki/, ki je v .gitignore.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p kajros/static/ikone posnetki

# Slika predogleda bere pisave prek HTTP, torej rabi tekoč strežnik.
# Razlog je pod njeno pripravo spodaj; tu samo preverimo, da je dosegljiv.
OG_BAZA="${OG_BAZA:-http://127.0.0.1:8001}"
export OG_BAZA
if ! curl -fsS -o /dev/null --max-time 5 "$OG_BAZA/static/pisave.css"; then
  echo "  PADE: $OG_BAZA/static/pisave.css ni dosegljiv." >&2
  echo "        Poženi ./scripts/dev-restart.sh ali nastavi OG_BAZA." >&2
  exit 1
fi

./venv/bin/python - <<'PY'
import pathlib
def mark(w=9):
    return ('<path d="M34 24V72" stroke="#e7eaf0" stroke-width="%d"/>'
            '<path d="M66 26L34 50" stroke="#5b6472" stroke-width="%d"/>'
            '<path d="M34 50L66 72" stroke="#f0934f" stroke-width="%d"/>' % (w, w, w))
navadna = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96" fill="none" '
           'stroke-linecap="round"><rect width="96" height="96" rx="21" fill="#0f1115"/>'
           + mark() + '</svg>')
# Maskirana: podlaga cez ves kvadrat, znak na 66 % -- Android si obliko izreze sam.
maskirana = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96" fill="none" '
             'stroke-linecap="round"><rect width="96" height="96" fill="#0f1115"/>'
             '<g transform="translate(48 48) scale(0.66) translate(-48 -48)">'
             + mark() + '</g></svg>')
for ime, svg, px in (("i180", navadna, 180), ("i192", navadna, 192),
                     ("i512", navadna, 512), ("imask", maskirana, 512)):
    pathlib.Path("posnetki/%s.html" % ime).write_text(
        '<meta charset="utf-8"><style>html,body{margin:0;padding:0}'
        'svg{display:block;width:%dpx;height:%dpx}</style>%s' % (px, px, svg))

# Slika za predogled deljene povezave (Open Graph, 1200x630).
#
# Pisave se berejo z **razvojnega streznika**, ne iz datoteke in ne kot
# `data:`. Oboje je bilo preizkuseno in oboje odpove tiho:
#
#   * `file://` chromium zavrne (CORS velja tudi tam);
#   * `data:` mu vzame staticni Mono, **variabilnega Sansa pa ne** -- izmerjeno
#     s stirimi vrsticami druga ob drugi, kjer je bil Sans pikel v piko enak
#     serifni rezervi, Mono pa pravilen.
#
# V obeh primerih je slika nastala in imela pravo velikost v pikah, torej je
# bila videti kot uspeh. Zato spodaj straza, ki vprasa `document.fonts.check()`.
import os
baza = os.environ["OG_BAZA"]
pathlib.Path("posnetki/og.html").write_text(f"""<meta charset="utf-8">
<link rel="stylesheet" href="{baza}/static/pisave.css">
<style>
html,body {{ margin:0; padding:0; }}
body {{ width:1200px; height:630px; background:#0f1115; color:#e7eaf0;
       display:flex; flex-direction:column; justify-content:center;
       padding:0 90px; box-sizing:border-box;
       font-family:'IBM Plex Sans'; }}
.znak {{ display:flex; align-items:center; gap:24px; }}
.ime {{ font:600 76px/1 'IBM Plex Mono'; }}
.vodilo {{ margin-top:34px; font:400 42px/1.35 'IBM Plex Sans';
          color:#e7eaf0; max-width:24ch; }}
.vir {{ margin-top:30px; font:400 26px/1.4 'IBM Plex Sans'; color:#79828f; }}
.crta {{ margin-top:44px; height:6px; width:210px; border-radius:3px;
        background:linear-gradient(90deg,#f0934f,#b85417); }}
#straza {{ position:fixed; left:-9999px; }}
</style>
<div class="znak">
  <svg width="86" height="86" viewBox="0 0 96 96" fill="none" stroke-linecap="round">
    <path d="M34 24V72" stroke="#f0934f" stroke-opacity=".5" stroke-width="9"/>
    <path d="M66 26L34 50" stroke="#f0934f" stroke-opacity=".5" stroke-width="9"/>
    <path d="M34 50L66 72" stroke="#f0934f" stroke-width="9"/>
  </svg>
  <span class="ime">kajros</span>
</div>
<div class="vodilo">Odhodi in zamude slovenskih vlakov in avtobusov.</div>
<div class="vir">Izmerjeni iz odprtih podatkov, ne prepisani od prevoznika.</div>
<div class="crta"></div>
<div id="straza">?</div>
<script>
document.fonts.ready.then(() => {{
  const ok = document.fonts.check("42px 'IBM Plex Sans'")
          && document.fonts.check("600 76px 'IBM Plex Mono'");
  document.getElementById("straza").textContent = ok ? "PISAVA-OK" : "PISAVA-PADE";
}});
</script>
""")
PY

for spec in "i180 180 icon-180" "i192 192 icon-192" "i512 512 icon-512" "imask 512 icon-maskable-512"; do
  set -- $spec
  rm -f "kajros/static/ikone/$3.png"
  timeout 60 chromium --headless --disable-gpu --window-size="$2","$2" \
    --virtual-time-budget=3000 --screenshot="$PWD/kajros/static/ikone/$3.png" \
    "file://$PWD/posnetki/$1.html" >/dev/null 2>&1
  rm -f "posnetki/$1.html"
  # Chromium ob napaki posname SVOJO stran z napako in ta je videti kot uspeh.
  # Zato preverimo velikost slike, ne le obstoja datoteke.
  dejansko=$(file -b "kajros/static/ikone/$3.png" | grep -oE '[0-9]+ x [0-9]+' | tr -d ' ')
  if [ "$dejansko" != "${2}x${2}" ]; then
    echo "  PADE $3.png: ${dejansko:-brez slike}, pricakoval ${2}x${2}" >&2
    exit 1
  fi
  echo "  ok   $3.png  $dejansko"
done

# Slika predogleda stoji v static/, ne v ikone/: ni ikona aplikacije, ampak
# tisto, kar vidi človek, ki mu nekdo pošlje povezavo v Signalu.
rm -f kajros/static/og.png

# Najprej vprasaj stran samo, ali sta se pisavi nalozili. Velikost v pikah
# tega ne pove -- slika s serifno rezervo je enako velika kot prava.
straza=$(timeout 60 chromium --headless --disable-gpu --window-size=1200,630 \
  --virtual-time-budget=5000 --dump-dom "file://$PWD/posnetki/og.html" 2>/dev/null \
  | grep -o 'PISAVA-OK\|PISAVA-PADE' | head -1)
if [ "$straza" != "PISAVA-OK" ]; then
  echo "  PADE og.png: pisava se ni nalozila (${straza:-brez odgovora})" >&2
  exit 1
fi

timeout 60 chromium --headless --disable-gpu --window-size=1200,630 \
  --virtual-time-budget=5000 --screenshot="$PWD/kajros/static/og.png" \
  "file://$PWD/posnetki/og.html" >/dev/null 2>&1
rm -f posnetki/og.html
dejansko=$(file -b kajros/static/og.png | grep -oE '[0-9]+ x [0-9]+' | tr -d ' ')
if [ "$dejansko" != "1200x630" ]; then
  echo "  PADE og.png: ${dejansko:-brez slike}, pricakoval 1200x630" >&2
  exit 1
fi
echo "  ok   og.png  $dejansko  (pisava preverjena)"
