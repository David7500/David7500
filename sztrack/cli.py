"""Ukazna vrstica: python -m sztrack.cli <ukaz>"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import config, collector, db, gtfs, stats, weather


def cmd_init(args):
    conn = db.connect()
    db.init(conn)
    print(f"baza pripravljena: {config.DB_PATH}")


def cmd_update(args):
    conn = db.connect()
    db.init(conn)
    path = gtfs.download(conn, force=args.force)
    if path is None:
        print("vozni red nespremenjen (HTTP 304) -- uvoz preskocen")
        return
    print(f"prenesen {path} ({path.stat().st_size / 1e6:.1f} MB), uvazam ...")
    print(json.dumps(gtfs.import_static(conn, path), indent=2))


def cmd_poll(args):
    conn = db.connect()
    db.init(conn)
    if args.once:
        print(json.dumps(collector.poll_once(conn), indent=2))
    else:
        print(f"zajem vsakih {args.interval or config.POLL_SECONDS} s (Ctrl-C za konec)")
        collector.run_forever(conn, args.interval)


def cmd_show(args):
    conn = db.connect()
    rows = stats.run_detail(conn, args.train_no, args.date) if args.date else \
        stats.timetable(conn, args.train_no)
    if not rows:
        sys.exit(f"vlak {args.train_no} ne obstaja")
    for r in rows:
        if args.date:
            delay = r["delay_arr"] if r["delay_arr"] is not None else r["delay_dep"]
            mark = f"{delay // 60:+3d} min" if delay is not None else "     -"
            sched = (r["sched_arr"] or r["sched_dep"] or "")[11:16]
            print(f"{r['stop_seq']:>3}  {r['name']:<26} {sched}  {mark}")
        else:
            print(f"{r['stop_seq']:>3}  {r['name']:<26} {r['arr_s']}")


def cmd_stats(args):
    conn = db.connect()
    rows = stats.network_stats(conn, args.days)[: args.limit]
    if not rows:
        print("se ni zajetih podatkov -- pozeni 'poll' nekaj dni")
        return
    print(f"{'vlak':<12}{'voženj':>7}{'mediana':>10}{'p90':>8}{'najslabse':>11}{'tocnost':>9}")
    for r in rows:
        print(f"{r['train_no']:<12}{r['runs']:>7}{r['median_s'] / 60:>9.1f}m"
              f"{r['p90_s'] / 60:>7.1f}m{r['max_s'] / 60:>10.1f}m{r['on_time_share']:>9.0%}")


def cmd_merge(args):
    conn = db.connect()
    db.init(conn)
    print(json.dumps(db.merge_from(conn, Path(args.source)), indent=2, ensure_ascii=False))


def cmd_weather(args):
    conn = db.connect()
    db.init(conn)
    if args.show:
        rows = weather.covered_days(conn)
        if not rows:
            print("vremena se ni -- pozeni 'weather --days 7'")
            return
        print(f"{'dan':<12}{'vir':<10}{'celic':>7}{'vrstic':>8}")
        for r in rows:
            print(f"{r['day']:<12}{r['source']:<10}{r['cells']:>7}{r['rows_n']:>8}")
        return
    print(json.dumps(weather.backfill(conn, args.days), indent=2, ensure_ascii=False))


def cmd_export(args):
    conn = db.connect()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "network.geojson").write_text(
        json.dumps(stats.network_geojson(conn, not args.all_edges), ensure_ascii=False)
    )
    (out / "stations.json").write_text(json.dumps(stats.stations(conn), ensure_ascii=False))
    print(f"zapisano v {out}/")


def main(argv=None):
    p = argparse.ArgumentParser(prog="sztrack", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="ustvari bazo").set_defaults(func=cmd_init)

    a = sub.add_parser("update", help="prenesi in uvozi vozni red (samo ce se je spremenil)")
    a.add_argument("--force", action="store_true", help="prenesi tudi ce je nespremenjen")
    a.set_defaults(func=cmd_update)

    a = sub.add_parser("poll", help="zajemaj zamude")
    a.add_argument("--once", action="store_true", help="en sam poll in izhod")
    a.add_argument("--interval", type=int, help=f"sekund med klici (privzeto {config.POLL_SECONDS})")
    a.set_defaults(func=cmd_poll)

    a = sub.add_parser("show", help="izpisi vozni red ali konkretno voznjo")
    a.add_argument("train_no", help='npr. "LPV 2206"')
    a.add_argument("--date", help="YYYY-MM-DD; brez tega izpise samo vozni red")
    a.set_defaults(func=cmd_show)

    a = sub.add_parser("stats", help="lestvica vlakov po zamudi")
    a.add_argument("--days", type=int, default=90)
    a.add_argument("--limit", type=int, default=25)
    a.set_defaults(func=cmd_stats)

    a = sub.add_parser("merge", help="prilij zajem iz druge baze (npr. s prejsnjega gostitelja)")
    a.add_argument("source", help="pot do druge sz.sqlite")
    a.set_defaults(func=cmd_merge)

    a = sub.add_parser("weather", help="dopolni vreme za nazaj (Open-Meteo)")
    a.add_argument("--days", type=int, default=7, help="koliko dni nazaj do danes")
    a.add_argument("--show", action="store_true", help="samo izpisi, kaj je ze shranjeno")
    a.set_defaults(func=cmd_weather)

    a = sub.add_parser("export", help="izvozi GeoJSON mreze in postaj")
    a.add_argument("--out", default="export")
    a.add_argument("--all-edges", action="store_true", help="vkljuci tudi preskoke hitrih vlakov")
    a.set_defaults(func=cmd_export)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
