import pandas as pd,numpy as np,json
from pathlib import Path
from scipy.optimize import least_squares,brentq
from dateutil.easter import easter
from datetime import date,timedelta
p=Path('lseg_resume/bundesbank_official')
h=[]
for y in range(2019,2028):
 e=easter(y);h += [date(y,1,1),e-timedelta(days=2),e+timedelta(days=1),date(y,5,1),date(y,12,25),date(y,12,26)]
cal=np.busdaycalendar(holidays=np.array(h,dtype='datetime64[D]'))
def settlement(dt):return pd.Timestamp(np.busday_offset(np.datetime64(dt.date()),2,roll='forward',busdaycal=cal))
def cf(mat,c,sd,first,start):
 dates=[mat];last=mat
 while True:
  prev=last-pd.DateOffset(years=1)
  if prev<=sd:break
  dates.append(prev);last=prev
 dates=sorted(dates);tt=(dates[0]-sd).days/(dates[0]-prev).days+np.arange(len(dates));vv=np.full(len(tt),c,dtype=float);vv[-1]+=100
 keep=np.array([dd>=first for dd in dates])
 if first>sd and c>0:
  end=first;fraction=0.
  while end>start:
   begin=end-pd.DateOffset(years=1);fraction+=(end-max(start,begin)).days/(end-begin).days;end=begin
  for j,dd in enumerate(dates):
   if dd==first:vv[j]=c*fraction+(100 if dd==mat else 0)
 return tt[keep],vv[keep]
# NS/Svensson fixed decay loadings.4coefficients estimated from observed conventional dirty prices only.
def basis(t,tau1=1.0,tau2=5.0):
 a=(1-np.exp(-t/tau1))/(t/tau1);b=(1-np.exp(-t/tau2))/(t/tau2)
 return np.column_stack([np.ones(len(t)),a,a-np.exp(-t/tau1),b-np.exp(-t/tau2)])

import pandas as pd,numpy as np,json
from pathlib import Path
p=Path('lseg_resume/bundesbank_official');d=pd.read_parquet(p/'official_all_verified.parquet');q=pd.read_parquet(p/'official_twins_verified.parquet');d=d[d.date<'2026-11-01'];q=q[q.date<'2026-11-01'];greens=set(q.isin_g)
def dur(row):
 sd=settlement(row.date);y=row.yield_pct/100
 if row.maturity<=sd or not np.isfinite(y) or y<=-1:return np.nan
 t,v=cf(row.maturity,row.coupon,sd,row.first_verified,row.start_verified);pv=v/(1+y)**t
 return float((pv*t).sum()/pv.sum()/(1+y))
d['duration']=d.apply(dur,axis=1);d.to_parquet(p/'official_duration_verified.parquet',index=False);c=d[~d['isin'].isin(greens)&~d.description.str.contains('DBRI|BUNDEI|INDEX|ILB',case=False,na=False)&d.yield_pct.notna()&(d.date<d.maturity)];q=q.merge(d[['isin','date','duration']],left_on=['isin_g','date'],right_on=['isin','date'],validate='one_to_one');out=[]
for dt,gr in q.groupby('date'):
 pool=c[c.date==dt]
 for _,r in gr.iterrows():
  a=pool[(pool['isin']!=r.isin_c)&((pool.maturity-r.maturity).dt.days.abs()<=731)].copy();a['dd']=a.duration-r.duration;a=a.dropna(subset=['dd']).sort_values(['dd','isin'],key=lambda x:x.abs() if x.name=='dd' else x)
  if a.empty:continue
  v={'date':dt,'green':r.isin_g,'duration_nearest_error_bp':100*(r.yield_pct_c-a.iloc[0].yield_pct)};lo=a[a.dd<0].sort_values('dd').tail(1);hi=a[a.dd>0].sort_values('dd').head(1)
  if len(lo) and len(hi):
   l,h=lo.iloc[0],hi.iloc[0];w=-l.dd/(h.dd-l.dd);v['duration_interp_error_bp']=100*(r.yield_pct_c-(l.yield_pct+w*(h.yield_pct-l.yield_pct)))
  out.append(v)
s=pd.read_parquet(p/'matching_benchmark.parquet').merge(pd.DataFrame(out),on=['date','green'],validate='one_to_one');s.to_parquet(p/'duration_verified_benchmark.parquet',index=False);cols=['error_bp','interp_error_bp','duration_nearest_error_bp','duration_interp_error_bp'];common=s.dropna(subset=cols);rows=[]
for sample,ss in [('available',s),('common',common)]:
 for col in cols:
  z=ss.dropna(subset=[col]);rows.append({'sample':sample,'method':col,'n':len(z),'pairs':z.green.nunique(),'pair_balanced_MAE':z.groupby('green')[col].apply(lambda x:x.abs().mean()).mean(),'median_abs_error':z[col].abs().median()})
pd.DataFrame(rows).to_csv(p/'duration_verified_summary.csv',index=False);print(pd.DataFrame(rows).to_string(index=False))
