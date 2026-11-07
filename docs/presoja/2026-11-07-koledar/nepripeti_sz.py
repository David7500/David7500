import sqlite3, zlib, json, datetime, collections
from zoneinfo import ZoneInfo
TZ = ZoneInfo("Europe/Ljubljana")
d = sqlite3.connect("file:/var/lib/kajros/dosje.sqlite?mode=ro", uri=True)
k = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
def stev(n): return n.split()[-1].lstrip("0") if n else ""
def kljuc(i): return i.replace("(Železniški)", "").strip().casefold()
OBJAVA = datetime.datetime(2026, 11, 6, 14, 45, 35, tzinfo=TZ).timestamp()
tela = {}
def telo(o):
    if o not in tela:
        tela[o] = json.loads(zlib.decompress(d.execute("SELECT vsebina FROM telo WHERE odtis=?", (o,)).fetchone()[0]))
    return tela[o]
# vožnje po številki in dnevu
voz = collections.defaultdict(list)
for tid, tn, dan in k.execute("SELECT t.trip_id, t.train_no, d.date FROM trip t JOIN service_day d USING(service_id) WHERE t.network='zeleznica' AND t.mode!='bus' AND d.date BETWEEN '2026-10-30' AND '2026-11-08'"):
    voz[(stev(tn), dan)].append((tid, tn))
postanki = {}
def post(tid):
    if tid not in postanki:
        postanki[tid] = k.execute("SELECT x.stop_seq, s.name, x.arr_s, x.dep_s FROM sched x JOIN station s USING(stop_id) WHERE trip_id=? ORDER BY stop_seq", (tid,)).fetchall()
    return postanki[tid]
vse = d.execute("SELECT vozilo, ts, trip_id, dan, razlogi, telo, sprotno FROM stanje WHERE vir='sz' AND vozilo LIKE 'vlak-%' AND ts >= ? ORDER BY vozilo, ts", (datetime.datetime(2026,10,31,tzinfo=TZ).timestamp(),)).fetchall()
dogodki = []
for i, (v, ts, tid, dan, raz, to, spr) in enumerate(vse):
    if "nepripet" not in raz: continue
    j = i + 1
    while j < len(vse) and vse[j][0] == v and "nepripet" in vse[j][4]: j += 1
    if i > 0 and vse[i-1][0] == v and "nepripet" in vse[i-1][4]: continue   # nadaljevanje epizode
    konec = vse[j][1] if j < len(vse) and vse[j][0] == v else None
    nasl = vse[j] if j < len(vse) and vse[j][0] == v else None
    s = json.loads(spr) if spr else {}; b = telo(to)
    n = v[5:]; dt = datetime.datetime.fromtimestamp(ts, TZ); dn = dt.date().isoformat(); vc = (dt.date()-datetime.timedelta(days=1)).isoformat()
    kand = voz.get((n, dn), []) + voz.get((n, vc), [])
    pk = kljuc(s.get("Postaja") or "")
    if not kand: vzrok = "ni_v_voznem_redu"
    elif s.get("Vrsta") not in (1, 2): vzrok = f"vrsta_{s.get('Vrsta')}"
    elif s.get("Vrsta") == 1 and not any(kljuc(p[1]) == pk for t, _ in kand for p in post(t)[1:]): vzrok = "ime_postaje"
    else: vzrok = "ura"
    # derp.si v epizodi: obs, ki smo jih videli med ts in koncem
    derp = []
    if kand and konec:
        for t, _ in kand:
            derp += k.execute("SELECT stop_seq, delay_arr, delay_dep, observed_at FROM obs WHERE trip_id=? AND observed_at BETWEEN ? AND ?", (t, ts, konec + 30)).fetchall()
    nz = json.loads(nasl[6]).get("Zamuda_cas") if nasl and nasl[6] and nasl[2] else None
    dogodki.append(dict(n=n, rang=b.get("Rang"), rel=b.get("Relacija"), cas=dt.strftime("%m-%d %H:%M:%S"), po=ts >= OBJAVA,
        trajanje=(konec - ts) if konec else None, vzrok=vzrok, postaja=s.get("Postaja"), odhod=s.get("Odhod"), vrsta=s.get("Vrsta"),
        zamuda=s.get("Zamuda_cas"), kand=[t for t, _ in kand], derp=[(r[0], r[1], r[2]) for r in derp], naslednja_pripeta=nz))
json.dump(dogodki, open("/var/tmp/koledar-nepripeti.json", "w"), ensure_ascii=False, indent=0)
print("epizod", len(dogodki))
c = collections.Counter((e["vzrok"], e["po"]) for e in dogodki); print(sorted(c.items()))
c = collections.Counter((e["vzrok"], e["postaja"]) for e in dogodki if e["vzrok"] != "ni_v_voznem_redu"); print(c.most_common(15))
c = collections.Counter((e["n"], e["rang"], e["rel"]) for e in dogodki if e["vzrok"] == "ni_v_voznem_redu"); print(c.most_common(15))
tr = sorted(e["trajanje"] for e in dogodki if e["trajanje"] is not None); print("trajanje s: n", len(tr), "med", tr[len(tr)//2] if tr else None, "p90", tr[int(len(tr)*.9)] if tr else None, "max", tr[-1] if tr else None)
