#!/usr/bin/env python3
"""Enkratno čiščenje: lažne ničle zemljevida SŽ v `run`, 10.–16. 10. 2026.

SŽ na vsake 3–4 min za en odgovor del vlakov pokaže po voznem redu, z
zamudo 0. Do popravka (16. 10. 2026 ob 14:36:54, `zamude_sz.zapisi`, tretje
varovalo) smo jih zapisovali kot meritev. Ničla po zamudi od 5 min naprej je
bila 1.–6. 10. (prek posrednika) v 0,45–1,24 % vrstic vlakov, 11.–16. 10. v
4,7–7,5 % -- devet od desetih je napaka. Prikaz jih je izpuščal, model,
„običajna zamuda“, končna zamuda in senca pa ne.

Pobriše vrstico v `run` in `sz_zamuda` in razrešitev sence (`napoved`), ki
stoji na njej. Dnevnik `obs` ostane: je zapis tega, kar smo videli, in
`kajros repair` pobrisane vrstice ne vrne (piše le v obstoječe). Postanek
ostane brez meritve -- raje to kot lažna točnost. Pravih okrevanj na nič
gre s tem ~10 % pobrisanih, kolikor jih je bilo pred 10. 10.

Brez `--zapisi` samo prešteje. Na arwenu (`david` je v skupini `kajros`):

    cd /opt/kajros && .venv/bin/python scripts/pocisti_nicle_sz.py --baza /var/lib/kajros/kajros.sqlite
    cd /opt/kajros && .venv/bin/python scripts/pocisti_nicle_sz.py --baza /var/lib/kajros/kajros.sqlite --zapisi

16. 10. 2026 ob 15:50 je štetje dalo 2 336 ničel na 651 vožnjah.

Ko je pognan, skripta odide (rok 31. 10. 2026).
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, ".")
from kajros import config, db                       # noqa: E402

OD, DO = "2026-10-10", "2026-10-16"
#: Ponovni zagon s popravkom (journal na arwenu): od tod je ničla potrjena.
POPRAVEK_TS = int(datetime(2026, 10, 16, 14, 36, 54,
                           tzinfo=ZoneInfo(config.TIMEZONE)).timestamp())

_IZBOR = """
WITH r AS (
    SELECT r.trip_id, r.service_date, r.stop_seq, r.feed_ts,
           COALESCE(r.delay_dep, r.delay_arr) AS d,
           MAX(COALESCE(r.delay_dep, r.delay_arr, 0)) OVER (
               PARTITION BY r.trip_id, r.service_date ORDER BY r.stop_seq
               ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS prej
    FROM run r JOIN trip t ON t.trip_id = r.trip_id
    WHERE t.network = 'zeleznica' AND t.mode != 'bus'
      AND r.service_date BETWEEN :od AND :do
)
SELECT r.trip_id, r.service_date, r.stop_seq
FROM r JOIN sz_zamuda z ON z.trip_id = r.trip_id AND z.service_date = r.service_date
                       AND z.stop_seq = r.stop_seq AND z.delay_s = 0
WHERE r.d = 0 AND r.prej >= 300 AND r.feed_ts < :do_ts
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--zapisi", action="store_true", help="res pobriši (sicer samo prešteje)")
    ap.add_argument("--baza", default=str(config.DB_PATH))
    a = ap.parse_args()
    # Štetje samo bere: sme ga pognati vsak, tudi `david` ob tekoči storitvi.
    conn = (db.connect(a.baza) if a.zapisi
            else sqlite3.connect(f"file:{a.baza}?mode=ro", uri=True))
    kljuci = [tuple(r) for r in conn.execute(_IZBOR, {"od": OD, "do": DO, "do_ts": POPRAVEK_TS})]
    po_dnevih: dict[str, int] = {}
    for _, dan, _ in kljuci:
        po_dnevih[dan] = po_dnevih.get(dan, 0) + 1
    voznj = len({(t, d) for t, d, _ in kljuci})
    print(f"lažnih ničel {len(kljuci)} na {voznj} vožnjah: "
          + ", ".join(f"{d} {n}" for d, n in sorted(po_dnevih.items())))
    if not a.zapisi:
        print("nič pobrisano -- za brisanje dodaj --zapisi")
        return 0
    with conn:
        n_run = n_sz = n_nap = 0
        for k in kljuci:
            pogoj = "trip_id = ? AND service_date = ? AND stop_seq = ?"
            n_run += conn.execute(f"DELETE FROM run WHERE {pogoj}", k).rowcount
            n_sz += conn.execute(f"DELETE FROM sz_zamuda WHERE {pogoj}", k).rowcount
            n_nap += conn.execute(f"DELETE FROM napoved WHERE {pogoj}", k).rowcount
    print(f"pobrisano: run {n_run}, sz_zamuda {n_sz}, napoved {n_nap}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
