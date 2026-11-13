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
d=pd.read_parquet(p/'official_all_verified.parquet');q=pd.read_parquet(p/'official_twins_verified.parquet');d=d[(d.date<'2026-11-01')&~d.description.str.contains('index|DBRI|BUNDEI|ILB',case=False,na=False)].copy();q=q[q.date<'2026-11-01'];greens=set(q.isin_g);targets=set(q.isin_c);out=[];diag=[];validation=[]
for i,(dt,x) in enumerate(d.groupby('date')):
 if dt not in set(q.date):continue
 sd=settlement(dt);x=x[(x.maturity>sd)&x.dirty.notna()&x.yield_pct.notna()].copy();records={}
 for r in x.itertuples():
  t,v=cf(r.maturity,r.coupon,sd,r.first_verified,r.start_verified);yp=r.yield_pct/100
  predicted=(v/(1+yp)**t).sum();price_error=predicted-r.dirty
  records[r.isin]=(t,v,r,price_error);validation.append({'date':dt,'isin':r.isin,'dirty_price_error':price_error})
 # Gate convention mismatches >1cent per100; documented and all excluded retained.
 train=[v for k,v in records.items() if k not in greens|targets and abs(v[3])<=.01]
 if len(train)<12:continue
 lengths=np.array([len(v[0]) for v in train]);t=np.concatenate([v[0] for v in train]);cash=np.concatenate([v[1] for v in train]);b=basis(t);inds=np.repeat(np.arange(len(train)),lengths);prices=np.array([v[2].dirty for v in train]);dollar_duration=np.array([sum(v[1]*v[0]/(1+v[2].yield_pct/100)**(v[0]+1)) for v in train]);weights=np.maximum(dollar_duration,25)
 def residual(beta):
  pv=cash*np.exp(-t*(basis(t,beta[4],beta[5])@beta[:4]));pred=np.bincount(inds,weights=pv,minlength=len(train));return (pred-prices)/weights
 fits=[least_squares(residual,[.02,-.01,0,0,t1,t2],bounds=([-.1,-.3,-.3,-.3,.1,.1],[.2,.3,.3,.3,30,30]),max_nfev=250,ftol=1e-8,xtol=1e-8,gtol=1e-8) for t1,t2 in [(.5,3),(1,5),(2,10)]]
 fit=min(fits,key=lambda f:np.sum(f.fun**2))
 maturities=[v[2].maturity for v in train];minm,maxm=min(maturities),max(maturities);diag.append({'date':dt,'train_n':len(train),'success':fit.success,'train_yield_weighted_RMSE_bp':10000*np.sqrt(np.mean(fit.fun**2))})
 for row in q[q.date==dt].itertuples():
  if row.isin_c not in records:continue
  tt,v,r,pe=records[row.isin_c]
  if not(minm<=r.maturity<=maxm) or abs(pe)>.01 or not fit.success:continue
  pred=float(np.sum(v*np.exp(-tt*(basis(tt,fit.x[4],fit.x[5])@fit.x[:4]))))
  try:y=brentq(lambda y:np.sum(v/(1+y)**tt)-pred,-.1,.5)*100
  except ValueError:continue
  out.append({'date':dt,'green':row.isin_g,'true_twin':row.isin_c,'curve_error_bp':100*(r.yield_pct-y),'curve_yield_pct':y,'train_n':len(train),'price_reconstruction_error':pe})
 if i%200==0:print(i,len(out),flush=True)
pd.DataFrame(out).to_parquet(p/'cashflow_nss_verified_benchmark.parquet',index=False);pd.DataFrame(diag).to_csv(p/'cashflow_nss_verified_diagnostics.csv',index=False);v=pd.DataFrame(validation);v.to_parquet(p/'cashflow_verified_convention_checks.parquet',index=False);print('done',len(out),'convention quantiles',v.dirty_price_error.abs().quantile([.5,.9,.99,1]).to_dict(),'pass',int((v.dirty_price_error.abs()<=.01).sum()),'of',len(v),flush=True)
