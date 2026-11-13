import pandas as pd,numpy as np,json
from pathlib import Path
p=Path('lseg_resume/bundesbank_official');d=pd.read_parquet(p/'official_all.parquet');q=pd.read_parquet(p/'official_twins.parquet');d=d[d.date<'2026-11-01'];q=q[q.date<'2026-11-01'];greens=set(q.isin_g);c=d[~d['isin'].isin(greens)].copy()
# Official descriptions identify inflation-linked DBRI / BUNDEI; require nominal common prefixes and finite yield.
c=c[~c.description.str.contains('DBRI|BUNDEI|INDEX|ILB',case=False,na=False)];c=c[c.yield_pct.notna()&(c.date<c.maturity)]
rows=[]
for dt,gr in q.groupby('date'):
 pool=c[c.date==dt]
 for _,r in gr.iterrows():
  a=pool[pool['isin']!=r.isin_c].copy();a['distance']=(a.maturity-r.maturity).dt.days;a=a[a.distance.abs()<=731].sort_values(['distance','isin'],key=lambda x:x.abs() if x.name=='distance' else x)
  if a.empty:continue
  t=a.iloc[0];base={'date':dt,'green':r.isin_g,'true_twin':r.isin_c,'true_gap_bp':r.gap_bp,'alternative':t['isin'],'maturity_gap_days':int(t.distance),'approx_gap_bp':100*(r.yield_pct_g-t.yield_pct),'error_bp':100*(r.yield_pct_c-t.yield_pct)}
  co=a[np.isclose(a.coupon,r.coupon)];base['coupon_match_error_bp']=100*(r.yield_pct_c-co.iloc[0].yield_pct) if len(co) else np.nan
  lo=a[a.distance<0].sort_values('distance').tail(1);hi=a[a.distance>0].sort_values('distance').head(1)
  if len(lo) and len(hi):
   l,h=lo.iloc[0],hi.iloc[0];w=-l.distance/(h.distance-l.distance);pred=l.yield_pct+w*(h.yield_pct-l.yield_pct);base['interp_error_bp']=100*(r.yield_pct_c-pred);base['slope_bp_per_year']=100*(h.yield_pct-l.yield_pct)/(h.distance-l.distance)*365.25
  rows.append(base)
s=pd.DataFrame(rows);s['sign_disagree']=(np.sign(s.true_gap_bp)!=np.sign(s.approx_gap_bp));s.to_parquet(p/'matching_benchmark.parquet',index=False)
r={'n':len(s),'pairs':s.green.nunique(),'median_abs_error_bp':s.error_bp.abs().median(),'p90_abs_error_bp':s.error_bp.abs().quantile(.9),'sign_disagreement_fraction':s.sign_disagree.mean(),'interpolation_median_abs_error_bp':s.interp_error_bp.abs().median(),'interpolation_n':int(s.interp_error_bp.notna().sum()),'coupon_matched_n':int(s.coupon_match_error_bp.notna().sum()),'coupon_matched_median_abs_error_bp':s.coupon_match_error_bp.abs().median()};(p/'matching_benchmark_summary.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2));print(c.description.drop_duplicates().head(20).tolist())
