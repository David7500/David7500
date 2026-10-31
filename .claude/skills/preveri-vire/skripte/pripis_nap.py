"""Senca pripisa NAP (`nap.Senca`, tabela `pripis_senca`) proti derp.si in
proti NAP-u samemu. Argumenti: DAN [--baza POT] [--primerov N] [--senca POT].

Vrstica sence = vozilo, ki ga NAP ni pripel (ali ga je na vožnjo, ki se še
ni začela ali je končana > 45 min), ob enem računu (največ enkrat na minuto).

* derp.si ob istem branju (`derp_voznja`): isto / drugo / derp nima / derp ni
  bral. Brez para: „mi nimamo“, kadar derp.si vožnjo ima (in ali je to samo
  NAP-ova prijava, ki jo derp.si ponovi), sicer „nihče“.
* NAP sam: ali je vozilo isti dan kdaj pripel na našo vožnjo
  (`straza_opazeno`, vir 'nap') in kdaj (`lega`: prej / pozneje kot senca).

Zagon (samo branje): scp na arwen, nato
  ssh david@192.168.1.46 '/opt/kajros/.venv/bin/python -I /tmp/pripis_nap.py 2026-11-01'
"""
import argparse
import collections
import functools
import sqlite3
import time

ap = argparse.ArgumentParser()
ap.add_argument("dan")
ap.add_argument("--baza", default="/var/lib/kajros/kajros.sqlite")
ap.add_argument("--primerov", type=int, default=6)
ap.add_argument("--senca", help="pripis_senca iz druge datoteke (ponovitev), ostalo iz --baza")
a = ap.parse_args()
conn = sqlite3.connect(f"file:{a.baza}?mode=ro", uri=True)
if a.senca:
    conn.execute("ATTACH ? AS senca", (f"file:{a.senca}?mode=ro",))


def ura(ts):
    return time.strftime("%H:%M", time.localtime(ts))


if not a.senca and not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE name = 'pripis_senca'").fetchone():
    print("tabele pripis_senca ni: senca še ni objavljena na tej bazi")
    nap = conn.execute("SELECT COUNT(DISTINCT vozilo) FROM straza_opazeno "
                       "WHERE dan = ? AND vir = 'nap' AND trip_id = ''", (a.dan,)).fetchone()[0]
    print(f"{a.dan}: NAP je {nap} vozil vsaj enkrat videl brez vožnje (straza_opazeno)")
    raise SystemExit(0)

agencija = dict(conn.execute("SELECT trip_id, agency FROM trip"))
okno = {r[0]: (r[1], r[2]) for r in conn.execute("SELECT trip_id, start_s, end_s FROM trip")}
nap_dan = {(r[0], r[1]) for r in conn.execute(
    "SELECT vozilo, trip_id FROM straza_opazeno WHERE dan = ? AND vir = 'nap' AND trip_id != ''",
    (a.dan,))}
vrstice = conn.execute(
    "SELECT ts, vozilo, vzrok, nap_voznja, nasa_voznja, nas_dan, razlog, zamuda_s, kandidatov, "
    "derp_voznja FROM pripis_senca WHERE dan = ? ORDER BY ts", (a.dan,)).fetchall()
if not vrstice:
    print(f"{a.dan}: v pripis_senca ni vrstic")
    raise SystemExit(0)


@functools.lru_cache(maxsize=None)
def _lega(vozilo, trip, dan):
    return conn.execute("SELECT MIN(ts), MAX(ts) FROM lega WHERE service_date = ? AND trip_id = ? "
                        "AND vozilo = ?", (dan, trip, vozilo)).fetchone()


def lega_nap(vozilo, trip, dan, ts):
    """Kdaj je `lega` vozilo imela na tej vožnji: prej / pozneje / nikoli."""
    r = _lega(vozilo, trip, dan)
    if r[0] is None:
        return "nikoli"
    return "pozneje" if r[1] > ts else "prej"


izid = collections.Counter()           # (vzrok, prevoznik, kategorija) -> vrstic
vozila = collections.defaultdict(set)
razlogi = collections.Counter()
primeri = collections.defaultdict(list)
for ts, voz, vzrok, nap_t, nasa, nas_dan, razlog, zam, kand, derp in vrstice:
    prev = agencija.get(nasa or nap_t, "?")
    if nasa:
        if derp is None:
            kat = "par · derp ni bral"
        elif derp == nasa:
            kat = "par · isto kot derp"
        elif derp == "":
            kat = "par · derp nima"
        else:
            kat = "par · derp drugo"
        nap_kat = ("NAP isti dan, lega " + lega_nap(voz, nasa, nas_dan, ts)
                   if (voz, nasa) in nap_dan else "NAP nikoli")
        izid[(vzrok, prev, nap_kat)] += 1
    else:
        razlogi[(vzrok, razlog)] += 1
        if derp:
            kat = "brez · mi nimamo, derp = NAP" if derp == nap_t else "brez · mi nimamo, derp drugo"
        else:
            kat = "brez · nihče"
    izid[(vzrok, prev, kat)] += 1
    vozila[(vzrok, prev, kat)].add(voz)
    if kat in ("par · derp drugo", "brez · mi nimamo, derp drugo", "brez · mi nimamo, derp = NAP") \
            and len(primeri[kat]) < a.primerov and all(p[0] != voz for p in primeri[kat]):
        primeri[kat].append((voz, ura(ts), vzrok, nap_t, nasa, derp, razlog, zam, kand))

print(f"{a.dan}: {len(vrstice)} računov, {len({v[1] for v in vrstice})} vozil, "
      f"{ura(vrstice[0][0])}-{ura(vrstice[-1][0])}")
print(f"{'vzrok':13} {'prev':5} {'kategorija':34} {'vrstic':>7} {'vozil':>6}")
for k in sorted(izid):
    print(f"{k[0]:13} {k[1]:5} {k[2]:34} {izid[k]:7} {len(vozila[k]) if k in vozila else '':>6}")
print("brez para po razlogu:", dict(sorted(razlogi.items())))
pari = [v for v in vrstice if v[4]]
if pari:
    z = sorted(v[7] for v in pari)
    print(f"par: {len(pari)} vrstic, odmik od voznega reda p10 {z[len(z) // 10]} s, "
          f"mediana {z[len(z) // 2]} s, p90 {z[9 * len(z) // 10]} s")
for kat, seznam in primeri.items():
    print(f"\n{kat} (vozilo, ura, vzrok, NAP, naša, derp, razlog, odmik s, kandidatov):")
    for p in seznam:
        # Nagrobnik (vožnja brez `sched`) ima `start_s` NULL.
        okna = [f"{t} {okno[t][0] // 3600:02d}:{okno[t][0] % 3600 // 60:02d}"
                if okno.get(t, (None,))[0] is not None else str(t) for t in p[3:6]]
        print("  ", p[:3], "·", " / ".join(okna), "·", p[6:])
