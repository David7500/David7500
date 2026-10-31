"""Samo branje. Kar brez produkcije ne gre: id-ji nagrobnikov, derp = NAP po vzroku, zasedenost, luknje vozil.
Argument: DAN (privzeto 2026-11-01) [--baza POT]."""
import argparse
import json
import sqlite3

ap = argparse.ArgumentParser()
ap.add_argument("dan", nargs="?", default="2026-11-01")
ap.add_argument("--baza", default="/var/lib/kajros/kajros.sqlite")
a = ap.parse_args()
c = sqlite3.connect(f"file:{a.baza}?mode=ro", uri=True)
m = json.loads((c.execute("SELECT value FROM meta WHERE key = 'nap'").fetchone() or ["{}"])[0])
print("meta.nap:", {k: m.get(k) for k in ("ts", "vozil", "brez_id", "starih", "naprej", "brez_lege", "pripetih", "brez_voznje",
                                          "brez_dneva", "prezgodaj", "skupnih", "ista_voznja", "samo_nap", "samo_derp")})
print("senca:", m.get("senca"))
print("nagrobnikov (start_s NULL) med medkrajevnimi:", c.execute(
    "SELECT COUNT(*) FROM trip WHERE start_s IS NULL AND agency IN ('1119','1121','1123')").fetchone()[0])
for n in m.get("nepripeti") or []:
    t = c.execute("SELECT start_s, agency FROM trip WHERE trip_id = ?", (n.get("nasa"),)).fetchone()
    print("  nepripet:", n.get("vozilo"), n.get("razlog"), n.get("voznja"), n.get("nasa"),
          "ni v trip" if t is None else ("NAGROBNIK" if t[0] is None else "ima okno"))
if not c.execute("SELECT 1 FROM sqlite_master WHERE name = 'pripis_senca'").fetchone():
    raise SystemExit("tabele pripis_senca ni")
print("vrstic sence", c.execute("SELECT COUNT(*) FROM pripis_senca WHERE dan = ?", (a.dan,)).fetchone()[0])
print("vzrok, vrstic, vozil, parov, derp = NAP, derp = naša, derp prazen, derp NULL:")
for r in c.execute(
        "SELECT vzrok, COUNT(*), COUNT(DISTINCT vozilo), SUM(nasa_voznja IS NOT NULL), SUM(derp_voznja = nap_voznja), "
        "SUM(derp_voznja = nasa_voznja), SUM(derp_voznja = ''), SUM(derp_voznja IS NULL) "
        "FROM pripis_senca WHERE dan = ? GROUP BY 1", (a.dan,)):
    print("  ", r)
print("par: naša = NAP / naša != NAP po vzroku:", c.execute(
    "SELECT vzrok, SUM(nasa_voznja = nap_voznja), SUM(nasa_voznja != nap_voznja) FROM pripis_senca "
    "WHERE dan = ? AND nasa_voznja IS NOT NULL GROUP BY 1", (a.dan,)).fetchall())
print("nagrobnik v vrsticah: NAP", c.execute(
    "SELECT COUNT(*), COUNT(DISTINCT s.vozilo) FROM pripis_senca s JOIN trip t ON t.trip_id = s.nap_voznja "
    "WHERE s.dan = ? AND t.start_s IS NULL", (a.dan,)).fetchone(), "derp", c.execute(
    "SELECT COUNT(*), COUNT(DISTINCT s.vozilo) FROM pripis_senca s JOIN trip t ON t.trip_id = s.derp_voznja "
    "WHERE s.dan = ? AND t.start_s IS NULL", (a.dan,)).fetchone())
# Zasedenost: delež voženj voznega reda, na katere je NAP ta dan pripel vozilo (ostale so „proste“ in jih lahko dobi stoječe vozilo).
vr = c.execute("SELECT COUNT(*) FROM trip t JOIN service_day sd ON sd.service_id = t.service_id AND sd.date = ? "
               "WHERE t.agency IN ('1119','1121','1123') AND t.start_s IS NOT NULL", (a.dan,)).fetchone()[0]
nap = c.execute("SELECT COUNT(DISTINCT o.trip_id) FROM straza_opazeno o JOIN trip t ON t.trip_id = o.trip_id "
                "JOIN service_day sd ON sd.service_id = t.service_id AND sd.date = ? "
                "WHERE o.dan = ? AND o.vir = 'nap' AND o.trip_id != ''", (a.dan, a.dan)).fetchone()[0]
print(f"voženj po voznem redu {vr}, z NAP-ovim vozilom do zdaj {nap}")
