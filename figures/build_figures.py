from pathlib import Path
import numpy as np,pandas as pd,json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'lseg_resume/bundesbank_official'; OUT=Path(__file__).resolve().parent
s=pd.read_parquet(SRC/'fair_shared_common_sample.parquet')
cols=['error_bp','interp_error_bp','duration_nearest_error_bp','duration_interp_error_bp','NSS6_verified_error_bp']
labels=['Nearest maturity','Maturity interpolation','Nearest duration','Duration interpolation','Cash-flow NSS']
colors=['#444444','#0072B2','#E69F00','#009E73','#CC79A7'];styles=['-','--',':','-.','-']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.labelsize':10,'svg.fonttype':'none','pdf.fonttype':42})
def save(fig,name):
 fig.savefig(OUT/(name+'.png'),dpi=400,bbox_inches='tight',facecolor='white');fig.savefig(OUT/(name+'.pdf'),bbox_inches='tight');fig.savefig(OUT/(name+'.svg'),bbox_inches='tight');plt.close(fig)
u=json.loads((SRC/'fair_shared_uncertainty.json').read_text());rows=[]
fig,ax=plt.subplots(figsize=(6.8,3.25))
for k,(col,label,color) in enumerate(zip(cols,labels,colors)):
 m=s.groupby('green')[col].apply(lambda a:a.abs().mean()).mean();lo,hi=u['CIs'][col];y=4-k
 ax.errorbar(m,y,xerr=[[m-lo],[hi-m]],fmt='o',color=color,capsize=4,markersize=6);ax.text(hi+.08,y,f'{m:.2f}',va='center',fontsize=9);rows.append([col,m,lo,hi])
ax.set_yticks(range(5),labels[::-1]);ax.set_xlim(0,4.65);ax.set_xlabel('Pair-balanced mean absolute error (basis points)');ax.grid(axis='x',alpha=.18);fig.tight_layout();save(fig,'Figure_1_accuracy')
pd.DataFrame(rows,columns=['method','MAE_bp','CI_lower','CI_upper']).to_csv(OUT/'figure1_data.csv',index=False)
fig,ax=plt.subplots(figsize=(6.8,3.4));grid=np.linspace(0,12,481);out={'absolute_error_bp':grid}
for col,label,color,ls in zip(cols,labels,colors,styles):
 cdf=np.mean([np.searchsorted(np.sort(a.abs().to_numpy()),grid,side='right')/len(a) for _,a in s.groupby('green')[col]],axis=0);out[col]=cdf
 ax.plot(grid,100*cdf,label=label,color=color,ls=ls,lw=1.8)
ax.set(xlabel='Absolute reconstruction error (basis points)',ylabel='Pair-balanced cumulative share (%)',xlim=(0,12),ylim=(0,101));ax.grid(alpha=.18);ax.legend(loc='lower right',frameon=False,fontsize=9);fig.tight_layout();save(fig,'Figure_2_distribution');pd.DataFrame(out).to_csv(OUT/'figure2_data.csv',index=False)
fig,ax=plt.subplots(figsize=(6.8,3.4));rows=[]
for col,label,color,ls in zip(cols,labels,colors,styles):
 xx=np.arange(0,2.01,.1);yy=[]
 for tol in xx:
  ref=s.true_gap_bp;approx=ref+s[col];den=(ref.abs()>tol).sum();num=((ref.abs()>tol)&(approx.abs()>tol)&(np.sign(ref)!=np.sign(approx))).sum();rate=100*num/den;yy.append(rate);rows.append([col,tol,int(den),int(num),rate])
 ax.plot(xx,yy,label=label,color=color,ls=ls,lw=1.8)
ax.set(xlabel='Symmetric tolerance around zero (basis points)',ylabel='Opposite-sign share (%)',xlim=(0,2),ylim=(0,35));ax.grid(alpha=.18);ax.legend(frameon=False,fontsize=9);fig.tight_layout();save(fig,'Figure_3_sign');pd.DataFrame(rows,columns=['method','tolerance_bp','reference_eligible','opposite','percent']).to_csv(OUT/'figure3_data.csv',index=False)
(OUT/'README.txt').write_text('Figures use the harmonized 8,872 pair-day sample across ten German twins, 4 November 2020 to 30 October 2026. All plots are generated from actual stored predictions. No fitted parameters or observations were changed.\nFigure 1: equal-twin MAE and percentile intervals from existing 1,944 valid circular calendar-block resamples.\nFigure 2: empirical absolute-error CDF with equal weight to each twin; axis displays 0–12 bp, not truncation of underlying data.\nFigure 3: opposing spreads both beyond tolerance divided by reference spreads beyond tolerance; each pair-day equally weighted.\nRun with numpy pandas pyarrow matplotlib, from any folder. Source SHA256: '+hashlib.sha256((SRC/'fair_shared_common_sample.parquet').read_bytes()).hexdigest())
print('Created three figures in PNG PDF SVG and supporting CSVs')
