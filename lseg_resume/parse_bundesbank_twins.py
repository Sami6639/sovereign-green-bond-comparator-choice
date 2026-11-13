import pandas as pd,numpy as np,json,re
from pathlib import Path
p=Path('lseg_resume/bundesbank_official');out=[];errors=[]
for f in sorted(p.glob('*.xlsx')):
 try:
  x=pd.ExcelFile(f)
  for sh in x.sheet_names:
   try:date=pd.to_datetime(sh,format='%d.%m.%Y')
   except:continue
   file_year,file_month=map(int,f.name[:7].split('-'))
   if date.year!=file_year or date.month!=file_month:
    errors.append([f.name,sh,'sheet date corrected using file year/month']);date=pd.Timestamp(year=file_year,month=file_month,day=date.day)
   d=x.parse(sh,header=None)
   if d.shape[1]==11:
    d=d[d[0].astype(str).str.fullmatch('DE000')].copy()
    if d[2].isna().any():errors.append([f.name,sh,'missing ISIN checksum rows excluded',int(d[2].isna().sum())])
    d=d[d[2].notna()]
    d[0]=d[0].astype(str)+d[1].map(lambda v:str(int(v)).zfill(6) if isinstance(v,(float,int)) else str(v).strip())+d[2].map(lambda v:str(int(v)))
    d=d[[0,3,4,5,6,7,8,9,10]]
   elif d.shape[1]==9:
    d=d[d[0].astype(str).str.fullmatch('DE[A-Z0-9]{10}')].copy()
   else:errors.append([f.name,sh,'columns'+str(d.shape[1])]);continue
   d.columns=['isin','coupon','description','maturity','residual','volume_bn','price','yield_pct','dirty'];d['date']=date;d['source_file']=f.name;out.append(d)
 except Exception as e:errors.append([f.name,str(e)])
d=pd.concat(out,ignore_index=True);d['maturity']=pd.to_datetime(d.maturity,errors='coerce',format='mixed',dayfirst=True)
for c in ['coupon','volume_bn','price','yield_pct','dirty']:d[c]=pd.to_numeric(d[c],errors='coerce')
d['description']=d['description'].astype(str);d['residual']=d['residual'].astype(str)
# Official green ISIN list including matured2025 bond; preserve all, never select based on yield.
green=['DE0001030708','DE0001030716','DE0001030724','DE0001030732','DE0001030740','DE0001030757','DE000BU3Z005','DE000BU35025','DE000BU3Z047','DE000BU3F007']
d=d.drop_duplicates(['isin','date']);g=d[d['isin'].isin(green)];c=d[~d['isin'].isin(green)];q=g.merge(c,on=['date','maturity','coupon'],suffixes=('_g','_c'));q=q[q.groupby(['isin_g','date']).isin_c.transform('size')==1].copy();q['gap_bp']=100*(q.yield_pct_g-q.yield_pct_c);q=q[(q.date<q.maturity)&q.gap_bp.notna()]
d.to_parquet(p/'official_all.parquet',index=False);q.to_parquet(p/'official_twins.parquet',index=False)
s=q.groupby(['isin_g','isin_c','maturity']).agg(n=('gap_bp','size'),first=('date','min'),last=('date','max'),median_bp=('gap_bp','median'),mean_bp=('gap_bp','mean')).reset_index();s.to_csv(p/'twin_summary.csv',index=False)
(p/'parse_audit.json').write_text(json.dumps({'files':len(list(p.glob('*.xlsx'))),'rows':len(d),'errors':errors,'pair_rows':len(q)},indent=2));print(s.to_string(index=False));print('errors',len(errors),'rows',len(d),'pairs',len(q))
