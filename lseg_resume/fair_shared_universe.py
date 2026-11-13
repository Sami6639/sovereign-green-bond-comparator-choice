import pandas as pd,numpy as np,json
from pathlib import Path
p=Path('lseg_resume/bundesbank_official')
d=pd.read_parquet(p/'official_duration_verified.parquet');q=pd.read_parquet(p/'official_twins_verified.parquet');q=q[q.date<'2026-11-01']
checks=pd.read_parquet(p/'cashflow_verified_convention_checks.parquet')
d=d.merge(checks,on=['isin','date'],validate='one_to_one')
excluded=set(q.isin_g)|set(q.isin_c)
c=d[~d['isin'].isin(excluded)&(d.dirty_price_error.abs()<=.01)&~d.description.str.contains('DBRI|BUNDEI|INDEX|ILB',case=False,na=False)&d.yield_pct.notna()&(d.date<d.maturity)].copy()
q=q.merge(d[['isin','date','duration']],left_on=['isin_g','date'],right_on=['isin','date'],how='left',validate='one_to_one')
# Green records are absent in NSS validation, so obtain duration directly.
d0=pd.read_parquet(p/'official_duration_verified.parquet');q=q.drop(columns='duration').merge(d0[['isin','date','duration']],left_on=['isin_g','date'],right_on=['isin','date'],validate='one_to_one',suffixes=('','_dur'))
out=[]
for dt,gr in q.groupby('date'):
 pool=c[c.date==dt]
 for r in gr.itertuples():
  a=pool[((pool.maturity-r.maturity).dt.days.abs()<=731)].copy();a['distance']=(a.maturity-r.maturity).dt.days;a['dd']=a.duration-r.duration
  if a.empty:continue
  a=a.sort_values(['distance','isin'],key=lambda x:x.abs() if x.name=='distance' else x)
  v={'date':dt,'green':r.isin_g,'true_twin':r.isin_c,'true_gap_bp':r.gap_bp,'error_bp':100*(r.yield_pct_c-a.iloc[0].yield_pct),'alternative':a.iloc[0]['isin']}
  for axis,name in [('distance','interp_error_bp'),('dd','duration_interp_error_bp')]:
   lo=a[a[axis]<0].sort_values([axis,'isin']).tail(1);hi=a[a[axis]>0].sort_values([axis,'isin']).head(1)
   if len(lo) and len(hi):
    l,h=lo.iloc[0],hi.iloc[0];w=-l[axis]/(h[axis]-l[axis]);v[name]=100*(r.yield_pct_c-l.yield_pct-w*(h.yield_pct-l.yield_pct))
  a=a.dropna(subset=['dd']).sort_values(['dd','isin'],key=lambda x:x.abs() if x.name=='dd' else x)
  if len(a):v['duration_nearest_error_bp']=100*(r.yield_pct_c-a.iloc[0].yield_pct)
  out.append(v)
s=pd.DataFrame(out).merge(pd.read_parquet(p/'cashflow_nss_verified_benchmark.parquet')[['date','green','curve_error_bp']],on=['date','green'],validate='one_to_one').rename(columns={'curve_error_bp':'NSS6_verified_error_bp'})
cols=['error_bp','interp_error_bp','duration_nearest_error_bp','duration_interp_error_bp','NSS6_verified_error_bp'];s=s.dropna(subset=cols);s.to_parquet(p/'fair_shared_common_sample.parquet',index=False)
rows=[]
for col in cols:
 rows.append({'method':col,'n':len(s),'pairs':s.green.nunique(),'pair_balanced_MAE':s.groupby('green')[col].apply(lambda x:x.abs().mean()).mean(),'median_abs_error':s[col].abs().median(),'pair_balanced_RMSE':np.sqrt(s.groupby('green')[col].apply(lambda x:(x*x).mean()).mean())})
pd.DataFrame(rows).to_csv(p/'fair_shared_metrics.csv',index=False)
sg=[]
for col in cols:
 approx=s.true_gap_bp+s[col]
 for tol in [0,.5,1,2]:
  eligible=s.true_gap_bp.abs()>tol
  both_outside=eligible&(approx.abs()>tol)
  opp=both_outside&(np.sign(s.true_gap_bp)!=np.sign(approx))
  sg.append({'method':col,'tolerance':tol,'reference_eligible':int(eligible.sum()),'both_outside':int(both_outside.sum()),'opposite':int(opp.sum()),'rate':float(opp.sum()/eligible.sum()),'both_outside_rate':float(opp.sum()/both_outside.sum()) if both_outside.any() else np.nan})
pd.DataFrame(sg).to_csv(p/'fair_shared_sign.csv',index=False)
# Shared calendar moving blocks; equal-weight twins within each draw.
s['month']=s.date.dt.to_period('M');months=pd.period_range(s.month.min(),s.month.max(),freq='M');pairs=sorted(s.green.unique());arr=np.zeros((len(months),len(pairs),len(cols)));cnt=np.zeros((len(months),len(pairs)))
for (m,g),z in s.groupby(['month','green']):
 i=months.get_loc(m);j=pairs.index(g);arr[i,j]=z[cols].abs().sum().values;cnt[i,j]=len(z)
rng=np.random.default_rng(20261113);draw=[]
for _ in range(2000):
 starts=rng.integers(0,len(months),size=int(np.ceil(len(months)/3)));idx=np.concatenate([(np.arange(3)+j)%len(months) for j in starts])[:len(months)];ct=cnt[idx].sum(axis=0)
 if (ct==0).any():continue
 draw.append((arr[idx].sum(axis=0)/ct[:,None]).mean(axis=0))
a=np.array(draw);result={'n':len(s),'pairs':len(pairs),'date_min':str(s.date.min().date()),'date_max':str(s.date.max().date()),'valid_draws':len(a),'CIs':{col:np.quantile(a[:,i],[.025,.975]).tolist() for i,col in enumerate(cols)},'nearest_minus_duration_interp_CI':np.quantile(a[:,0]-a[:,3],[.025,.975]).tolist()}
(p/'fair_shared_uncertainty.json').write_text(json.dumps(result,indent=2));loo=[]
for pair in pairs:
 z=s[s.green!=pair];loo.append({'omitted':pair,**{col:z.groupby('green')[col].apply(lambda x:x.abs().mean()).mean() for col in cols}})
pd.DataFrame(loo).to_csv(p/'fair_shared_leave_one_out.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False));print(json.dumps(result,indent=2));print(pd.DataFrame(sg).to_string(index=False))
