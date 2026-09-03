#!/usr/bin/env bash
# Ikone aplikacije iz znaka. Poženi po vsaki spremembi logotipa.
#
# Chromium ne more brati iz /tmp (isti razlog, kot da tja ne more pisati),
# zato vmesne strani nastanejo v posnetki/, ki je v .gitignore.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p kajros/static/ikone posnetki

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
