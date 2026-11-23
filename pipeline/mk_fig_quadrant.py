#!/usr/bin/env python3
"""Cost and carbon relative to concrete as paired bars: carbon offset (top) and net present cost
(bottom) for each material, one column per city, coloured by the resulting verdict."""
import os
HERE=os.path.dirname(os.path.abspath(__file__))
OUT=HERE; DST=os.path.normpath(os.path.join(HERE,"..","figures")); os.makedirs(DST,exist_ok=True)
import json, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, shutil
from matplotlib.patches import Patch
import matplotlib.lines as ml
import style_nat as S; S.apply()


R=json.load(open(f"{OUT}/robust_results.json")); INK=S.INK; MUT=S.MUT
CLIM=["CDMX","Warm-subhumid","Hot-arid"]
MATS=["Tepetate ashlar","Adobe-type block","SBC block (solid)","SBC block (solid, city-cast)","SBC block (hollow)","Volcanic stone (recinto)"]
INS="Concrete + EPS (insulated)"
if INS in R["BASE"]["CDMX"]: MATS=[INS]+MATS
NAME={"Tepetate ashlar":"Tepetate","Adobe-type block":"Earth block","SBC block (solid)":"SBC solid","SBC block (hollow)":"SBC hollow","Volcanic stone (recinto)":"Volcanic stone","SBC block (solid, city-cast)":"SBC solid, city-cast","Concrete + EPS (insulated)":"Insulated concrete"}
WW="#6f8f7f"; PA="#8fa3b5"; NO="#b98a5a"
def verdict(b):
    if b["dCO2"]>0.5 and b["dC"]<0: return WW
    if b["dCO2"]>0.5: return PA
    return NO
mn=lambda v,d=0:(f"{v:+.{d}f}" if abs(v)>=(0.5 if d==0 else 0.05) else "0").replace("-","−")
fig,axes=plt.subplots(2,3,figsize=(7.4,4.9),sharey=True,sharex="row")
y=np.arange(len(MATS))[::-1]
for j,c in enumerate(CLIM):
    for i,(key,lo,hi,sc) in enumerate([("dCO2","p5","p95",1.0),("dC","c5","c95",1e-3/19.0)]):
        ax=axes[i,j]
        for yy,m in zip(y,MATS):
            b=R["BASE"][c][m]; q=R["MC"][c][m]; v=b[key]*sc; a,z=q[lo]*sc,q[hi]*sc
            ax.barh(yy,v,height=0.62,color=verdict(b),linewidth=0,zorder=3)
            ax.plot([a,z],[yy,yy],color=INK,lw=0.8,zorder=4)
            for e in (a,z): ax.plot([e,e],[yy-0.12,yy+0.12],color=INK,lw=0.8,zorder=4)
            right=max(v,z)>abs(min(v,a)) or v>=0
            xt=(max(v,z) if v>=0 else min(v,a)); pad=(1.2 if i==0 else 0.2)*(1 if v>=0 else -1)
            ax.text(xt+pad,yy,mn(v,i),ha="left" if v>=0 else "right",va="center",fontsize=6.6,color=INK,zorder=5)
        ax.axvline(0,color=INK,lw=0.8,zorder=5)
        ax.set_yticks(y); ax.set_yticklabels([NAME[m] for m in MATS],fontsize=7.6); ax.tick_params(axis="y",length=0); ax.tick_params(axis="x",labelsize=6.8)
        for s in ("top","right","left"): ax.spines[s].set_visible(False)
        ax.grid(axis="x",zorder=0); ax.set_ylim(-0.6,len(MATS)-0.4)
        if MATS[0]==INS: ax.axhline(len(MATS)-1.5,color=MUT,lw=0.6,ls=(0,(2,2)),zorder=2)
        if i==0: ax.set_title(S.CLIMLAB[c].split(" (")[0],fontsize=8.8,pad=6); ax.set_xlim(-60,68)
        else: ax.set_xlim(-10.5,14.5)
axes[0,1].set_xlabel("Lifetime CO$_2$ offset relative to concrete (t CO$_2$-eq per dwelling)   positive = less carbon $\\rightarrow$",fontsize=7.6)
axes[1,1].set_xlabel("Net present cost relative to concrete (10$^3$ USD per dwelling, 50 yr, 5% real)   $\\leftarrow$ negative = saves money",fontsize=7.6)

fig.legend(handles=[Patch(fc=WW,label="Less carbon and cheaper"),Patch(fc=PA,label="Less carbon at a net cost"),Patch(fc=NO,label="No carbon benefit"),
                    ml.Line2D([],[],color=INK,lw=0.8,marker="|",ms=5,label="P5–P95 (Monte-Carlo)")],
           loc="lower center",ncol=4,fontsize=7.2,frameon=False,handlelength=1.2,columnspacing=1.6,bbox_to_anchor=(0.5,-0.005))
plt.tight_layout(rect=[0.02,0.055,1,1],h_pad=1.4,w_pad=0.8); fig.text(0.012,0.955,"a",fontsize=10,fontweight="bold"); fig.text(0.012,0.50,"b",fontsize=10,fontweight="bold"); plt.savefig(f"{OUT}/nat_costcarbon.png"); shutil.copy(f"{OUT}/nat_costcarbon.png",f"{DST}/nat_costcarbon.png"); print("ok")
