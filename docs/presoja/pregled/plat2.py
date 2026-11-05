"""Pot `zamude_sz.korak` -> tabla, samo :memory:. Isti podatki kot tests/test_zamude_sz.py."""
import sys
sys.path.insert(0,'.'); sys.path.insert(0,'tests')
from kajros import db, stats, journey, zamude_sz, iz_lege
DAN="2026-09-15"; POLNOC=stats.polnoc(DAN)
def _ura(h,m): return h*3600+m*60
def baza():
    c=db.connect(":memory:"); db.init(c)
    c.executemany("INSERT INTO station(stop_id,name,lat,lon) VALUES(?,?,?,?)",
      [("P","Plave(Železniški)",46.06,13.58),("S","Solkan",45.97,13.65),("N","Nova Gorica",45.95,13.64)])
    c.execute("INSERT INTO trip(trip_id,route_id,train_no,service_id,mode,agency,network,headsign) VALUES('t1','r','LP 4203','s1','vlak','1161','zeleznica','Nova Gorica')")
    c.executemany("INSERT INTO sched(trip_id,stop_seq,stop_id,arr_s,dep_s) VALUES(?,?,?,?,?)",
      [("t1",20,"P",_ura(7,55),_ura(7,56)),("t1",21,"S",_ura(8,7),_ura(8,7)),("t1",22,"N",_ura(8,12),None)])
    c.execute("INSERT INTO service_day(service_id,date) VALUES('s1',?)",(DAN,))
    db.fill_trip_window(c); c.commit(); return c
V={"St_vlaka":"4203","St":1,"Postaja_SZ_OD":"42400","Postaja_SZ_DO":"44700","Relacija":"Jesenice-Nova Gorica","St_postaje":"44710","Postaja":"Solkan","Odhod":"08:46","Koordinate":"13.6497,45.9689","Vrsta":1,"Zamuda_cas":50,"Predviden_prihod":7,"Vrsta_vlaka":"V","Rang":"LP"}
c=baza()
t0=POLNOC+_ura(8,46)+20      # prva vrstica: 20 s po "odhodu"
zamude_sz._odtis="a"; print("korak1",{k:v for k,v in zamude_sz.korak(c,[V],t0).items() if k in("zapisanih","prihodnjih","nepripetih")})
print(dict(c.execute("select stop_seq,delay_dep,feed_ts from run").fetchone()))
# SŽ zamudo dviguje v korakih, Odhod ves čas v prihodnosti (vlak stoji)
for i,(mn,z,odhod) in enumerate([(5,57,"08:53"),(10,62,"08:58"),(20,72,"09:08"),(35,87,"09:23"),(45,97,"09:33")]):
    t=t0+mn*60
    zamude_sz._odtis=f"b{i}"
    v={**V,"Odhod":odhod,"Zamuda_cas":z}
    s=zamude_sz.korak(c,[v],t)
    now_s=int(t-POLNOC)
    lm=stats.last_measured(c,DAN,["t1"],now_s).get("t1")
    tab=journey.board(c,"Plave(Železniški)",DAN,now_s-600,180,"odhodi",150,"zeleznica",now_s)
    tab2=journey.board(c,"Solkan",DAN,now_s-600,180,"odhodi",150,"zeleznica",now_s)
    h=f"{now_s//3600:02d}:{now_s%3600//60:02d}"
    print(f"{h} SŽ +{z} (Odhod {odhod}) prihodnjih={s['prihodnjih']} lm seq={lm and lm['stop_seq']} run +{lm and lm['delay_s']//60} trenutna +{stats.trenutna_zamuda(lm)//60}")
    print("   Plave:", [(r['delay_s']//60,r['delay_kind'],r['expected'][11:16],r['nepotrjen_do']) for r in tab] or "VRSTICE NI", "| Solkan:", [(r['delay_s']//60,r['delay_kind'],r['expected'][11:16]) for r in tab2])
