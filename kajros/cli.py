"""Ukazna vrstica: python -m kajros.cli <ukaz>"""
from __future__ import annotations

import os
import argparse
import json
import sys
from pathlib import Path

from . import (alerts, backtest, config, collector, db, gtfs, hoja, journey,
               ocena, pot, stats, weather)


def cmd_init(args):
    conn = db.connect()
    db.init(conn)
    print(f"baza pripravljena: {config.DB_PATH}")


def cmd_update(args):
    conn = db.connect()
    db.init(conn)
    path = gtfs.download(conn, force=args.force)
    # Mestni LPP je drug zip in se prenese, tudi ce je IJPP nespremenjen: to
    # sta razlicna vira in vsak se osvezuje po svoje.
    lpp = gtfs.download_lpp(conn, force=args.force) if config.LPP_ENABLED else None
    if config.LPP_ENABLED and lpp is None:
        lpp = config.DATA_DIR / "lpp_gtfs.zip"
        if not lpp.exists():
            lpp = None
    if path is None:
        if lpp is None:
            print("vozni red nespremenjen (HTTP 304) -- uvoz preskocen")
            return
        # LPP se je spremenil, IJPP ne -- uvoziti je treba oba, ker uvoz
        # staticne tabele zamenja v celoti.
        path = config.DATA_DIR / "ijpp_gtfs.zip"
        if not path.exists():
            path = gtfs.download(conn, force=True)
    print(f"prenesen {path} ({path.stat().st_size / 1e6:.1f} MB), uvazam ...")
    print(json.dumps(gtfs.import_static(conn, path, lpp_zip=lpp), indent=2))


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


def cmd_backtest(args):
    conn = db.connect()
    if args.day_offset:
        res = backtest.evaluate_day_offset(conn)
        print(f"nalog: {res['tasks']}\n")
    elif args.operator:
        res = backtest.evaluate_operator(conn)
        if not res.get("tasks"):
            print("premalo dnevnika za primerjavo -- pozeni 'poll' nekaj dni")
            return
        print(f"nalog, kjer je feed ze imel vrednost za cilj: {res['tasks']}\n")
    else:
        res = backtest.evaluate(conn, by_horizon=args.by_horizon,
                                network=args.network)
        print(f"omrezje: {args.network} · dni: {len(res['days'])}"
              f" · nalog: {res['tasks']}\n")

    print(f"{'model':26s}{'MAE':>9}{'mediana':>10}{'v 5 min':>10}{'odklon':>10}")
    for name, sc in res["models"].items():
        print(f"{name:26s}{sc['mae_s'] / 60:>8.2f}m{sc['median_s'] / 60:>9.2f}m"
              f"{sc['within_5min']:>10.1%}{sc['bias_s'] / 60:>9.2f}m")

    if res.get("by_horizon"):
        print("\npo oddaljenosti (postankov naprej):")
        names = list(res["by_horizon"])
        print("  " + "".join(f"{n:>18s}" for n in ["postankov"] + names))
        horizons = sorted(res["by_horizon"][names[0]])
        for h in horizons[:12]:
            cells = "".join(f"{res['by_horizon'][n][h]['mae_s'] / 60:>17.2f}m" for n in names)
            print(f"  {h:>18d}{cells}")


def _vrstica_modela(ime, m):
    if not m.get("n"):
        return f"{ime:24s}{'—':>10}"
    # `strosek` je pri skupnem izrezu None, ker sta razmika omrezij razlicna in
    # mesanica ne pomeni nicesar.
    s = m.get("strosek_min")
    return (f"{ime:24s}{m['mae_min']:>9.2f}m{m['v5min']:>9.1f}%"
            f"{m['podcenjenih']:>9.1f}%{m.get('precenjenih', 0):>9.1f}%"
            f"{m['odklon_min']:>9.2f}m"
            f"{(f'{s:>9.2f}m' if s is not None else f'{chr(8212):>10}')}{m['n']:>8d}")


def cmd_ocena(args):
    """Kako dobra je bila napoved, ki jo je potnik RES videl."""
    conn = db.connect()
    ocena.init(conn)
    if args.tick:
        print(json.dumps(ocena.tick(conn), indent=2, ensure_ascii=False))
        return
    r = ocena.report(conn, days=args.days, network=args.network)
    # Ne "od <meja okna>": senca ima lahko dva dneva v tridesetdnevnem oknu.
    razpon = (f"{r['prvi_dan']} .. {r['zadnji_dan']}" if r.get("prvi_dan")
              else "brez podatkov")
    print(f"senca {razpon} · pokritih obratovalnih dni {r.get('pokritih_dni', 0)}"
          f" · razrešenih vrstic {r['vrstic']} · čaka na resnico {r['cakajo']}")
    if not r["vrstic"]:
        print("\nŠe nič razrešenega. Senca teče ob strežniku; prvi izidi so čez"
              " dobro uro.")
        return

    modeli = (("naša ocena", "nasa"), ("naša brez prevoznika", "nasa_brez_prevoznika"),
              ("prevoznik", "prevoznik"), ("prenos zamude", "prenos"))

    def blok(naslov, x):
        print(f"\n{naslov}")
        print(f"{'model':24s}{'MAE':>10}{'v 5 min':>10}"
              f"{'podcenj.':>10}{'precenj.':>10}{'odklon':>10}{'strošek':>10}{'n':>8}")
        for ime, kljuc in modeli:
            print(_vrstica_modela(ime, x[kljuc]))
        molci = x.get("prevoznik_molci")
        if molci:
            print(f"  prevoznik za ta postanek ni imel vrednosti v {molci} % primerov;")
            print("  spodaj isti izrez za vse tri -- primerjava na razlicnih vzorcih")
            print("  meri tudi razliko med vzorcema:")
            for ime, kljuc in modeli:
                print("  " + _vrstica_modela(ime, x["parno"][kljuc]))

    # Brez tega se stolpca bereta kot poljubni odstotek. Prag je pri obeh
    # isti, sicer nista primerljiva -- ta past je tu ze bila.
    print("\npodcenj. / precenj. = zgrešeno za več kot potnikovo rezervo (5 min)")
    print("v eno oziroma drugo smer. Nevarna je PRECENITEV: potnik pride prepozno")
    print("in vozilo je že odpeljalo. Podcenitev pomeni čakanje, ne zamujenega vozila.")

    blok("SKUPAJ", r["skupaj"])
    for net, x in r["po_omrezju"].items():
        blok(net.upper(), x)
    for ime, x in r["po_zamudi"].items():
        blok(f"ZAMUDA OB POGLEDU {ime}", x)


def cmd_prune(args):
    conn = db.connect()
    db.init(conn)
    print(f"brišem dnevnik `obs`: železnica starejša od {args.rail_days} dni, "
          f"avtobusi od {args.bus_days}. `run` ostane nedotaknjen.")
    print(json.dumps(collector.prune_obs(conn, args.rail_days, args.bus_days),
                     indent=2, ensure_ascii=False))


def cmd_collect(args):
    """Zajem brez streznika. Za stroj, ki samo polni bazo."""
    from . import server           # uvozimo sele tu -- `server` potegne gtfs
    if args.no_alerts:
        os.environ["KAJROS_ALERT_SECONDS"] = "0"
    if args.weather:
        os.environ.setdefault("KAJROS_WEATHER", "1")
    else:
        os.environ["KAJROS_WEATHER"] = "0"
    os.environ.setdefault("KAJROS_SUMMARIES", "0")
    os.environ.setdefault("KAJROS_POSITIONS", "0")
    if args.interval:
        os.environ["KAJROS_POLL_SECONDS"] = str(args.interval)
    server.run_collector()


def cmd_summarize(args):
    """Znova izracunaj dnevne razreze statistike.

    V strezniku to opravi ozadnja nit enkrat na dan; tu je za rocni zagon in
    za cron na stroju, kjer strezniku zajem ne tece.
    """
    conn = db.connect()
    db.init(conn)
    for row in stats.refresh_summaries(conn, windows=(args.days,)):
        print(f"{row['network']:>10s}  {row['kind']:<14s} {args.days:>4d} dni  "
              f"{row['runs'] or 0:>8,} voženj  {row['took_ms']:>7d} ms")


def cmd_seed(args):
    conn = db.connect()
    db.init(conn)
    omr = None if args.network == "vse" else args.network
    print(json.dumps(db.build_seed(conn, Path(args.out), omr),
                     indent=2, ensure_ascii=False))


def cmd_repair(args):
    conn = db.connect()
    db.init(conn)
    izid = collector.rebuild_run(conn)
    # Meritev brez svoje voznje je nevidna, ne izgubljena -- a ucinek je isti:
    # vsaka poizvedba gre skozi `JOIN trip`, ker je omrezje tam. Nastane, kadar
    # uvoz voznega reda izbrise voznjo, ki ima meritve. Pove se tu, ker je to
    # ukaz za "popravi podatke"; ceni ga je poln pregled `run`, zato ne sodi
    # v vsako zahtevo.
    sirote = conn.execute(
        "SELECT COUNT(*) FROM run r LEFT JOIN trip t USING (trip_id) "
        "WHERE t.trip_id IS NULL").fetchone()[0]
    izid["osirotelih_meritev"] = sirote
    if sirote:
        izid["kako_popraviti"] = (
            "prilij bazo s stroja, ki ima starejsi vozni red "
            "(`kajros merge`) -- ta vrne tudi voznje z meritvami")
    print(json.dumps(izid, indent=2, ensure_ascii=False))


def cmd_pespoti(args):
    """Izmeri peš poti med bližnjimi postajališči (rabi peš usmerjevalnik)."""
    conn = db.connect()
    db.init(conn)
    izid = hoja.zgradi_pespoti(conn, znova=args.znova, javi=print)
    print(json.dumps(izid, indent=2, ensure_ascii=False))


def cmd_pot(args):
    """Pot od vrat do vrat. Točki sta `lat,lon` -- kot ju da zemljevid."""
    def tocka(niz):
        a, b = niz.split(",")
        return float(a), float(b)

    conn = db.connect()
    db.init(conn)
    dan = args.dan or journey.today()
    if args.ob:
        h, m = (int(x) for x in args.ob.split(":")[:2])
        odhod_s = h * 3600 + m * 60
    else:
        odhod_s = journey.now_seconds()
    izid = pot.isci(conn, tocka(args.od), tocka(args.do), dan, odhod_s)
    if args.json:
        print(json.dumps(izid, indent=2, ensure_ascii=False))
        return
    print(f"{dan}, od {odhod_s // 3600:02d}:{odhod_s % 3600 // 60:02d} · "
          f"{izid['izhodisc']} izhodišč, {izid['ciljev']} ciljev · "
          f"hoja: {izid['vir_hoje']} · {izid['trajalo_ms']} ms")
    if not izid["predlogi"]:
        print("  brez predlogov")
    for p in izid["predlogi"]:
        # Zaokrozuj enako kot zaslon (`floor(x + 0,5)`), sicer ista pot tu in
        # tam pise drugo minuto.
        print(f"\n  {_ura(p['odhod'])} -> {_ura(p['prihod'])}   "
              f"{(p['trajanje_s'] + 30) // 60} min · hoje {(p['hoje_s'] + 30) // 60} min · "
              f"{p['prestopov']} prestopov")
        for n in p["noge"]:
            if n["vrsta"] == "hoja":
                print(f"      peš {(n['sekunde'] + 30) // 60:3d} min  "
                      f"{n.get('od') or '(izhodišče)'} -> {n.get('do') or '(cilj)'}")
            else:
                print(f"      {n['train_no']:12} {_ura(n['odhod'])} {n['od']}"
                      f"  ->  {_ura(n['prihod'])} {n['do']}")


def _ura(ts):
    from datetime import datetime
    return datetime.fromtimestamp(ts, pot.TZ).strftime("%H:%M")


def cmd_alerts(args):
    conn = db.connect()
    db.init(conn)
    if args.fetch:
        print(json.dumps(alerts.poll_once(conn), indent=2, ensure_ascii=False))
        return
    if args.live:
        rows = alerts.live_delays(conn)
        if not rows:
            print("danes se ni porocil o zamudi")
            return
        print(f"{'vlak':<12}{'zamuda':>8}  prometno mesto")
        for r in rows:
            mark = "!" if r["severe"] else " "
            print(f"{r['train_no']:<12}{r['delay_min']:>6} min{mark} {r['station']}")
        return
    rows = alerts.active(conn)
    if not rows:
        print("ni veljavnih obvestil -- pozeni 'alerts --fetch'")
        return
    for r in rows:
        print(f"- {r['header']}")
        print(f"  {r['effect_label'] or r['effect']} · {r['cause_label'] or r['cause']}"
              f" · {len(r['trains'])} vlakov")


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
    p = argparse.ArgumentParser(prog="kajros", description=__doc__)
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
    a.add_argument("source", help="pot do druge kajros.sqlite")
    a.set_defaults(func=cmd_merge)

    a = sub.add_parser("weather", help="dopolni vreme za nazaj (Open-Meteo)")
    a.add_argument("--days", type=int, default=7, help="koliko dni nazaj do danes")
    a.add_argument("--show", action="store_true", help="samo izpisi, kaj je ze shranjeno")
    a.set_defaults(func=cmd_weather)

    a = sub.add_parser("backtest", help="izmeri napako napovedi (izpuscanje enega dne)")
    a.add_argument("--operator", action="store_true",
                   help="primerjaj prevoznikovo napoved s prenosom zamude")
    a.add_argument("--day-offset", action="store_true",
                   help="ali stanje mreze na ta dan izboljsa napoved (ne izboljsa)")
    a.add_argument("--by-horizon", action="store_true", help="razclenjeno po oddaljenosti")
    a.add_argument("--network", default=backtest.NETWORK,
                   choices=("zeleznica", "avtobus"),
                   help="katero omrezje meriti (privzeto zeleznica)")
    a.set_defaults(func=cmd_backtest)

    a = sub.add_parser("ocena", help="kako dobra je bila napoved, ki jo je potnik videl")
    a.add_argument("--days", type=int, default=30)
    a.add_argument("--network", choices=("zeleznica", "avtobus"),
                   help="samo eno omrezje (privzeto obe)")
    a.add_argument("--tick", action="store_true",
                   help="pozeni en obhod rocno (posnetek + resevanje)")
    a.set_defaults(func=cmd_ocena)

    a = sub.add_parser("prune", help="pobrisi stare vrstice dnevnika `obs`")
    a.add_argument("--rail-days", type=int, default=collector.OBS_KEEP_DAYS)
    a.add_argument("--bus-days", type=int, default=collector.OBS_KEEP_DAYS_BUS)
    a.set_defaults(func=cmd_prune)

    a = sub.add_parser(
        "collect",
        help="zajem brez streznika (za stroj, ki samo polni bazo)",
        description="Zajema samo tisto, cesar se kasneje ne da dobiti: zamude in "
                    "obvestila. Vreme ima arhiv za nazaj, statistika pa se izracuna "
                    "iz `run` kadarkoli in kjerkoli -- zato oboje privzeto odpade.")
    a.add_argument("--interval", type=int, help="sekunde med zajemi (privzeto 30)")
    a.add_argument("--no-alerts", action="store_true",
                   help="brez obvestil o ovirah (izgubis edini vir vzroka zamude)")
    a.add_argument("--weather", action="store_true",
                   help="dopolnjuj tudi vreme (na sibkem stroju nepotrebno)")
    a.set_defaults(func=cmd_collect)

    a = sub.add_parser("summarize", help="znova izracunaj dnevne razreze statistike")
    a.add_argument("--days", type=int, default=90, help="sirina okna (privzeto 90)")
    a.set_defaults(func=cmd_summarize)

    a = sub.add_parser("seed", help="zgradi prilozeno bazo za namestitev (samo vozni red)")
    a.add_argument("--out", default="seed/kajros.sqlite")
    # Z avtobusi je seme 53 MB, torej vec od samega GTFS zipa (41 MB), ki bi ga
    # namestitev sicer prenesla -- glej `db.build_seed`.
    a.add_argument("--network", default="zeleznica",
                   help="katero omrezje naj bo v semenu; 'vse' za vsa")
    a.set_defaults(func=cmd_seed)

    a = sub.add_parser("repair", help="znova zgradi `run` iz dnevnika `obs`")
    a.set_defaults(func=cmd_repair)

    a = sub.add_parser("pespoti", help="izmeri pes poti med bliznjimi postajalisci")
    a.add_argument("--znova", action="store_true", help="pobrisi in izracunaj vse")
    a.set_defaults(func=cmd_pespoti)

    a = sub.add_parser("pot", help="pot od vrat do vrat (tocki sta lat,lon)")
    a.add_argument("--od", required=True, help="izhodisce kot lat,lon")
    a.add_argument("--do", required=True, help="cilj kot lat,lon")
    a.add_argument("--ob", help="HH:MM; privzeto zdaj")
    a.add_argument("--dan", help="prometni dan; privzeto danes")
    a.add_argument("--json", action="store_true")
    a.set_defaults(func=cmd_pot)

    a = sub.add_parser("alerts", help="obvestila o ovirah in zive zamude")
    a.add_argument("--fetch", action="store_true", help="poberi feed zdaj")
    a.add_argument("--live", action="store_true", help="zadnja porocila o zamudi po vlakih")
    a.set_defaults(func=cmd_alerts)

    a = sub.add_parser("export", help="izvozi GeoJSON mreze in postaj")
    a.add_argument("--out", default="export")
    a.add_argument("--all-edges", action="store_true", help="vkljuci tudi preskoke hitrih vlakov")
    a.set_defaults(func=cmd_export)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
