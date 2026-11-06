# Osamelci "V": zamuda na postanku pade za >=10 min pod OBA soseda in se vrne.
import sqlite3,sys,collections
c=sqlite3.connect('file:data/kajros.sqlite?mode=ro',uri=True)
q="""SELECT r.trip_id,t.train_no,r.service_date,r.stop_seq,COALESCE(r.delay_dep,r.delay_arr) d
FROM run r JOIN trip t USING(trip_id) WHERE t.network='zeleznica' AND d IS NOT NULL
ORDER BY r.trip_id,r.service_date,r.stop_seq"""
runs=collections.defaultdict(list)
for tid,no,sd,seq,d in c.execute(q): runs[(tid,no,sd)].append((seq,d))
print('vozenj-dni',len(runs),'od',min(k[2] for k in runs),'do',max(k[2] for k in runs))
V=[];mesec=collections.Counter();vsi=collections.Counter()
for (tid,no,sd),s in runs.items():
    vsi[sd[:7]]+=1
    for i in range(1,len(s)-1):
        a,b,cc=s[i-1][1],s[i][1],s[i+1][1]
        if a-b>=600 and cc-b>=600: V.append((sd,no,s[i][0],a,b,cc)); mesec[sd[:7]]+=1
print('V-osamelcev',len(V))
for m in sorted(vsi): print(' ',m,'osamelcev',mesec[m],'vozenj-dni',vsi[m])
for x in [v for v in V if v[1]=='RG 318']: print(' RG318',x)
print('primeri',V[:8])
nic=sum(1 for v in V if v[4]==0); print('osamelec = 0:',nic,'/',len(V))
od=[v for v in V if v[0]>='2026-10-15']; print('od 15.10.:',len(od),'nic',sum(1 for v in od if v[4]==0), od[:6])
