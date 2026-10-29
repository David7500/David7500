import sqlite3
c = sqlite3.connect("file:/var/tmp/kajros-stat.sqlite?mode=ro", uri=True)
def rep(where, label, group="''"):
    sql = f"""
    SELECT {group} g, COUNT(*) n,
      AVG(ABS(ours_s-actual_s))/60.0, AVG(ABS(actual_s-COALESCE(operator_s,0)))/60.0, SUM(operator_s IS NOT NULL),
      AVG(ABS(actual_s-COALESCE(carry_s,0)))/60.0, AVG(ABS(actual_s))/60.0,
      100.0*AVG(ABS(ours_s-actual_s)<=60), 100.0*AVG(ABS(COALESCE(carry_s,0)-actual_s)<=60), 100.0*AVG(ABS(actual_s)<=60),
      100.0*AVG(ABS(ours_s-actual_s)<=180), 100.0*AVG(ABS(COALESCE(carry_s,0)-actual_s)<=180),
      AVG(ours_s-actual_s)/60.0, AVG(COALESCE(carry_s,0)-actual_s)/60.0
    FROM napoved n JOIN trip t USING(trip_id)
    WHERE actual_s IS NOT NULL AND ours_s IS NOT NULL AND ABS(actual_s) < 10800 AND {where}
    GROUP BY 1 ORDER BY 2 DESC"""
    print(f"## {label}")
    print("   g | n | MAE naš | MAE prev(0 če ni) | n prev | MAE prenos | MAE vozni red | ±1 naš | ±1 prenos | ±1 VR | ±3 naš | ±3 prenos | pristr naš | pristr prenos")
    for r in c.execute(sql).fetchall()[:14]:
        print("  ", " | ".join(f"{x:.2f}" if isinstance(x, float) else str(x) for x in r))
rep("t.network='zeleznica' AND from_seq IS NOT NULL", "vlaki, vozilo že na poti")
rep("t.network='zeleznica' AND from_seq IS NULL", "vlaki, pred odhodom z izhodišča")
rep("t.network='avtobus' AND from_seq IS NOT NULL", "avtobusi na poti, po prevozniku", "t.agency")
rep("t.network='avtobus' AND from_seq IS NULL", "avtobusi pred odhodom, po prevozniku", "t.agency")
rep("t.network='avtobus' AND from_seq IS NOT NULL AND operator_s IS NOT NULL", "avtobusi na poti, kjer ima prevoznik napoved", "t.agency")
rep("t.network='zeleznica' AND from_seq IS NOT NULL", "vlaki na poti po tednu", "strftime('%W', n.service_date)")
rep("t.network='zeleznica' AND from_seq IS NOT NULL AND ABS(current_s) >= 300", "vlaki na poti, zamuda ob pogledu >= 5 min")
