import urllib.request,re,html,json,concurrent.futures
from pathlib import Path
import pandas as pd
p=Path('lseg_resume/bundesbank_official');raw=p/'terms_html';raw.mkdir(exist_ok=True);d=pd.read_parquet(p/'official_all.parquet');isins=sorted(d['isin'].unique())
def one(isin):
 u='https://www.deutsche-finanzagentur.de/en/federal-securities/factsheet/isin/'+isin;f=raw/(isin+'.html')
 try:
  if not f.exists():f.write_bytes(urllib.request.urlopen(u,timeout=25).read())
  s=f.read_text();title=html.unescape(re.findall(r'<h1[^>]*>(.*?)</h1>',s,re.S)[0]);text=html.unescape(re.sub('<[^>]+>',' ',s));text=re.sub(r'\s+',' ',text)
  def val(label,end):
   a=text.split(label,1)
   return a[1].split(end,1)[0].strip() if len(a)>1 else None
  coupon=val('Coupon in %','Payable');start=val('Interest calculated from','First interest payment');first=val('First interest payment','Interest calculation');m=re.search(r'Maturity (\d{2}\.\d{2}\.\d{4})',text)
  return {'isin':isin,'url':u,'title':title,'coupon':coupon,'accrual_start':start,'first_coupon':first,'maturity':m.group(1) if m else None,'status':'fetched'}
 except Exception as e:return {'isin':isin,'url':u,'status':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
 rows=[]
 for r in ex.map(one,isins):
  rows.append(r)
  if len(rows)%24==0:print(len(rows),flush=True)
pd.DataFrame(rows).to_csv(p/'official_terms_raw.csv',index=False);(p/'terms_manifest.json').write_text(json.dumps(rows,indent=2));print('done',len(rows),flush=True)
