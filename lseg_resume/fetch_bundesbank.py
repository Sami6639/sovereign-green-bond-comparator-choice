import urllib.request,re,html,json,concurrent.futures,time
from pathlib import Path
p=Path('lseg_resume/bundesbank_official');p.mkdir(exist_ok=True);base='https://www.bundesbank.de'
def fetch(i):
 u=base+f'/action/en/810710/bbksearch?pageNumString={i}';s=urllib.request.urlopen(u,timeout=40).read().decode();return [(base+html.unescape(h),i) for h in re.findall(r'href="([^"]+)"',s) if h.endswith('.xlsx') and re.search(r'/202[0-6]-',h)]
links=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
 for a in ex.map(fetch,range(16)):links+=a
links=list(dict(links).items());print('links',len(links),flush=True)
def download(x):
 u,i=x;n=u.split('/')[-1];f=p/n
 if not f.exists():f.write_bytes(urllib.request.urlopen(u,timeout=40).read())
 return {'url':u,'file':str(f),'bytes':f.stat().st_size,'index_page':i}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:r=list(ex.map(download,links))
(p/'sources.json').write_text(json.dumps(r,indent=2));print('done',len(r),flush=True)
