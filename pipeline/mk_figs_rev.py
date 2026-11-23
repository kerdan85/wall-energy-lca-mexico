#!/usr/bin/env python3
"""Revision figures from robust_results.json: operational demand (+U band, tabulated error),
lifetime offset with Monte-Carlo interval, cost-carbon quadrant, OAT sensitivity of the offset."""
import os
HERE=os.path.dirname(os.path.abspath(__file__))
OUT=HERE; DST=os.path.normpath(os.path.join(HERE,"..","figures")); os.makedirs(DST,exist_ok=True)
import json, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, os
from matplotlib.patches import Rectangle, Patch
import matplotlib.lines as ml
import style_nat as S; S.apply()


INK,MUT,GREEN,VERM=S.INK,S.MUT,S.GREEN,S.VERM
R=json.load(open(f"{OUT}/robust_results.json"))
CLIM=["CDMX","Warm-subhumid","Hot-arid"]; LAB=[S.CLIMLAB[c] for c in CLIM]
REF="Concrete (ref.)"
ORD=["Tepetate ashlar","SBC block (solid)","Adobe-type block","Concrete (ref.)","SBC block (hollow)","Volcanic stone (recinto)"]
ALT=[m for m in ORD if m!=REF]; ALT.insert(ALT.index("SBC block (solid)")+1,"SBC block (solid, city-cast)")
SH={"Concrete (ref.)":"Concrete","Adobe-type block":"Earth\nblock","Volcanic stone (recinto)":"Volcanic\nstone",
    "Tepetate ashlar":"Tepetate","SBC block (solid)":"SBC\nsolid","SBC block (hollow)":"SBC\nhollow","SBC block (solid, city-cast)":"SBC solid\ncity-cast"}
def gy(ax): ax.grid(axis="y",zorder=0); ax.set_axisbelow(True)

# ---------- operational ----------
fig,(a,b)=plt.subplots(1,2,figsize=(7.3,3.2),gridspec_kw={"width_ratios":[1.15,1]})
x=np.arange(len(ORD)); w=0.26
for i,c in enumerate(CLIM):
    v=np.array([sum(R["HC"][c][m]) for m in ORD]); lo=np.array([R["BAND"][c][m][0] for m in ORD]); hi=np.array([R["BAND"][c][m][1] for m in ORD])
    a.bar(x+(i-1)*w,v,w,color=S.CLIMCOL[c],label=LAB[i],linewidth=0,zorder=3)
    a.errorbar(x+(i-1)*w,v,yerr=[v-lo,hi-v],fmt="none",ecolor=INK,elinewidth=0.6,capsize=1.4,capthick=0.6,zorder=4)
    for xi,vv,hh in zip(x+(i-1)*w,v,hi): a.text(xi,hh+2.5,f"{vv:.0f}",ha="center",va="bottom",fontsize=5.2,color=MUT)
    e=[100*(sum(R["HCT"][c][m])-sum(R["HC"][c][m]))/sum(R["HC"][c][m]) for m in ORD]
    bb=b.bar(x+(i-1)*w,e,w,color=S.CLIMCOL[c],linewidth=0,zorder=3)
    b.bar_label(bb,labels=[f"{k:+.0f}" for k in e],padding=1.2,fontsize=5.2,color=MUT)
for ax in (a,b):
    ax.set_xticks(x); ax.set_xticklabels([SH[m] for m in ORD],fontsize=6.8); S.despine(ax); gy(ax)
a.set_ylabel("Annual heating + cooling need\n(kWh m$^{-2}$ yr$^{-1}$, thermal)"); a.set_ylim(0,1.38*max(v for c in R["BAND"] for m in R["BAND"][c] for v in R["BAND"][c][m]))
a.legend(loc="upper left",fontsize=6.6,handlelength=1.0,borderaxespad=0.2)
b.axhline(0,color=INK,lw=0.8); b.set_ylabel("Error of tabulated-input prediction (%)"); b.set_ylim(-18,66)
S.panel(a,"a",x=-0.16); S.panel(b,"b",x=-0.17)
plt.tight_layout(); plt.savefig(f"{OUT}/nat_operclimate.png"); plt.close()

# ---------- offset with MC interval ----------
fig,ax=plt.subplots(figsize=(6.4,3.4)); x=np.arange(len(ALT))
for i,c in enumerate(CLIM):
    v=np.array([R["BASE"][c][m]["dCO2"] for m in ALT]); p5=np.array([R["MC"][c][m]["p5"] for m in ALT]); p95=np.array([R["MC"][c][m]["p95"] for m in ALT])
    ax.bar(x+(i-1)*w,v,w,color=S.CLIMCOL[c],label=LAB[i],linewidth=0,zorder=3)
    for xi,lo,hi in zip(x+(i-1)*w,p5,p95):
        ax.plot([xi,xi],[lo,hi],color=INK,lw=0.7,zorder=4)
        for qv in (lo,hi): ax.plot([xi-0.05,xi+0.05],[qv,qv],color=INK,lw=0.7,zorder=4)
    for xi,vv,lo,hi in zip(x+(i-1)*w,v,p5,p95):
        ax.text(xi,(hi+1.2 if vv>=0 else lo-1.2),(f"{vv:+.0f}" if abs(vv)>=0.5 else "0").replace("-","\u2212"),ha="center",va="bottom" if vv>=0 else "top",fontsize=5.6,color=MUT)
ax.axhline(0,color=INK,lw=0.9)
ax.set_xticks(x); ax.set_xticklabels([SH[m] if m=="SBC block (solid, city-cast)" else SH[m].replace("\n"," ") for m in ALT],fontsize=7.2)
ax.set_ylabel("Lifetime CO$_2$ offset vs concrete\n(t CO$_2$-eq per dwelling, 50 yr)")
ax.set_ylim(-60,54); S.despine(ax); gy(ax)
h,l=ax.get_legend_handles_labels(); h.append(ml.Line2D([],[],color=INK,lw=0.8,marker="_",ms=5)); l.append("Monte-Carlo P5–P95")
ax.legend(h,l,loc="upper right",fontsize=6.6,handlelength=1.1)
plt.tight_layout(); plt.savefig(f"{OUT}/nat_offsetclimate.png"); plt.close()

# ---------- cost-carbon quadrant ----------
FX=19.0
MCOL={"Tepetate ashlar":S.MATCOL["Tepetate"],"Adobe-type block":S.MATCOL["Adobe"],"SBC block (solid)":S.MATCOL["SBC solid"],"SBC block (hollow)":"#b9a26a","Volcanic stone (recinto)":S.MATCOL["Volcanic stone"]}
NAME={"Tepetate ashlar":"Tepetate","Adobe-type block":"Earth block","SBC block (solid)":"SBC solid","SBC block (hollow)":"SBC hollow","Volcanic stone (recinto)":"Volcanic stone","SBC block (solid, city-cast)":"SBC solid, city-cast"}
MK={"CDMX":"o","Warm-subhumid":"s","Hot-arid":"^"}
LOFF={"Tepetate ashlar":(8,-2,"left",0),"Adobe-type block":(-6,7,"right",0),"SBC block (solid)":(6,7,"left",0),
      "SBC block (hollow)":(6,-10,"left",2),"Volcanic stone (recinto)":(-4,-12,"right",0)}
fig,ax=plt.subplots(figsize=(5.8,4.2))
xlo,xhi,ylo,yhi=-140,160,-27,47
ax.add_patch(Rectangle((xlo,0),-xlo,yhi,fc=GREEN,alpha=0.07,lw=0,zorder=0)); ax.add_patch(Rectangle((0,ylo),xhi,-ylo,fc=VERM,alpha=0.07,lw=0,zorder=0))
ax.axhline(0,color=INK,lw=0.7); ax.axvline(0,color=INK,lw=0.7)
for m in MCOL:
    xs=[R["BASE"][c][m]["dC"]/1000 for c in CLIM]; ys=[R["BASE"][c][m]["dCO2"] for c in CLIM]
    o=np.argsort(xs); ax.plot(np.array(xs)[o],np.array(ys)[o],color=MCOL[m],lw=0.8,alpha=0.5,zorder=2)
    for c,xv,yv in zip(CLIM,xs,ys):
        k=R["MC"][c][m]
        ax.plot([k["c5"]/1000,k["c95"]/1000],[yv,yv],color=MCOL[m],lw=0.6,alpha=0.55,zorder=3)
        ax.plot([xv,xv],[k["p5"],k["p95"]],color=MCOL[m],lw=0.6,alpha=0.55,zorder=3)
        ax.scatter([xv],[yv],marker=MK[c],s=34,color=MCOL[m],edgecolor="white",lw=0.6,zorder=4)
    dx,dy,ha,ii=LOFF[m]
    ax.annotate(NAME[m],(xs[ii],ys[ii]),textcoords="offset points",xytext=(dx,dy),ha=ha,fontsize=7.4,color=MCOL[m],fontweight="bold",zorder=6)
ax.scatter([0],[0],marker="D",s=26,color=INK,zorder=5)
kw=dict(transform=ax.transAxes,fontsize=6.8,fontweight="bold")
ax.text(0.02,0.975,"WIN–WIN\nsaves money, less carbon",ha="left",va="top",color="#4f6f60",**kw)
ax.text(0.98,0.975,"PAY TO ABATE\ncosts more, less carbon",ha="right",va="top",color="#777",**kw)
ax.text(0.98,0.025,"LOSE–LOSE\ncosts more, more carbon",ha="right",va="bottom",color="#8a5a2b",**kw)
ax.text(0.02,0.345,"saves money, more carbon",ha="left",va="top",color="#777",**kw)
ax.set_xlim(xlo,xhi); ax.set_ylim(ylo,yhi)
ax.set_xlabel("Net present cost relative to concrete (10$^3$ MXN per dwelling, 50 yr, 5% real)")
ax.set_ylabel("Lifetime CO$_2$ offset relative to concrete\n(t CO$_2$-eq per dwelling)")
top=ax.secondary_xaxis("top",functions=(lambda v:v/FX,lambda v:v*FX)); top.set_xlabel("10$^3$ USD per dwelling",fontsize=7.5); top.tick_params(labelsize=7)
ax.spines["right"].set_visible(False)
hs=[ml.Line2D([],[],marker=MK[c],color="#666",ls="",ms=5,label=S.CLIMLAB[c].split(" (")[0]) for c in CLIM]
hs+=[ml.Line2D([],[],marker="D",color=INK,ls="",ms=4,label="Concrete (reference)"),ml.Line2D([],[],color="#888",lw=0.8,label="P5–P95")]
ax.legend(handles=hs,loc="lower left",fontsize=6.6,handletextpad=0.3,borderaxespad=0.3,ncol=2,columnspacing=0.8)
plt.tight_layout(); plt.savefig(f"{OUT}/nat_costcarbon.png"); plt.close()

# ---------- OAT sensitivity of the offset ----------
PAN=["Tepetate ashlar","Adobe-type block","SBC block (solid)","SBC block (solid, city-cast)","SBC block (hollow)","Volcanic stone (recinto)"]
fig,axes=plt.subplots(2,3,figsize=(7.4,5.3)); axs=axes.ravel()
labs=[p[0] for p in R["OAT"]["CDMX"][PAN[0]]]; ny=len(labs); hh=0.25
for ax,m in zip(axs,PAN):
    for i,c in enumerate(CLIM):
        for j,(lab,lo,hi) in enumerate(R["OAT"][c][m]):
            y=ny-1-j+(1-i)*hh
            ax.barh(y,hi-lo,left=lo,height=hh*0.9,color=S.CLIMCOL[c],linewidth=0,zorder=3)
    ax.axvline(0,color=INK,lw=0.8,zorder=4)
    ax.set_yticks(range(ny)); ax.set_yticklabels(labs[::-1] if ax in (axs[0],axs[3]) else [],fontsize=6.2)
    ax.set_title(NAME[m]+"  (base "+" / ".join(("%+.0f"%v if abs(v)>=0.5 else "0") for v in (R["BASE"][c][m]["dCO2"] for c in CLIM)).replace("-","\u2212")+" t)",fontsize=7.2,loc="left")
    for s in ["top","right","left"]: ax.spines[s].set_visible(False)
    ax.tick_params(axis="y",length=0); ax.grid(axis="x",zorder=0); ax.set_axisbelow(True); ax.tick_params(axis="x",labelsize=6.5)
    lim=max(abs(v) for c in CLIM for p in R["OAT"][c][m] for v in p[1:])*1.12; ax.set_xlim(-lim,lim)
fig.legend(handles=[Patch(fc=S.CLIMCOL[c],label=S.CLIMLAB[c]) for c in CLIM],loc="lower center",ncol=3,fontsize=7.2,frameon=False,bbox_to_anchor=(0.5,0.0))
fig.supxlabel("Change in lifetime CO$_2$ offset relative to the base case (t CO$_2$-eq per dwelling)",fontsize=8.2,y=0.05)
plt.tight_layout(rect=[0,0.07,1,1]); plt.savefig(f"{OUT}/nat_sensitivity.png"); plt.close()

# ---------- measured vs tabulated U (with expanded uncertainty) ----------
BLUE=S.BLUE
Um={"Concrete (ref.)":2.16,"Adobe-type block":2.07,"Volcanic stone (recinto)":2.73,"Tepetate ashlar":1.50,"SBC block (solid)":1.89,"SBC block (hollow)":2.21}
Ut={"Concrete (ref.)":3.00,"Adobe-type block":2.44,"Volcanic stone (recinto)":3.29,"Tepetate ashlar":2.21,"SBC block (solid)":2.59,"SBC block (hollow)":1.99}
o1=sorted(Um,key=lambda m:Um[m]); fig,ax=plt.subplots(figsize=(5.6,3.3)); x=np.arange(6); w=0.38
ax.bar(x-w/2,[Ut[m] for m in o1],w,color="#c9ced2",linewidth=0,label="Tabulated or declared",zorder=3)
ax.bar(x+w/2,[Um[m] for m in o1],w,color=BLUE,linewidth=0,label="Measured (heat-flow meter)",zorder=3)
ax.errorbar(x+w/2,[Um[m] for m in o1],yerr=[0.10*Um[m] for m in o1],fmt="none",ecolor=INK,elinewidth=0.7,capsize=2,capthick=0.7,zorder=4)
for xi,m in zip(x,o1):
    d=100*(Um[m]-Ut[m])/Ut[m]; ax.text(xi+w/2,Um[m]*1.10+0.05,(f"{d:+.0f}%").replace("-","\u2212"),ha="center",va="bottom",fontsize=6.8,color=INK)
ax.set_xticks(x); ax.set_xticklabels([SH[m] for m in o1],fontsize=7.2); ax.set_ylabel("Wall transmittance $U$ (W m$^{-2}$ K$^{-1}$)")
ax.set_ylim(0,3.9); S.despine(ax); gy(ax)
h,l=ax.get_legend_handles_labels(); h.append(ml.Line2D([],[],color=INK,lw=0.8,marker="_",ms=5)); l.append("Expanded uncertainty (±10%)")
ax.legend(h,l,loc="upper left",fontsize=6.6,handlelength=1.1)
plt.tight_layout(); plt.savefig(f"{OUT}/nat_thermal.png"); plt.close()

# ---------- embodied carbon by city: production + transport ----------
A1=R["A1A3"]
DIST={c:[R["DIST"][c][m] for m in KEY] for c in CLIM} if False else None
KEY=["Concrete (ref.)","Adobe-type block","Volcanic stone (recinto)","Tepetate ashlar","SBC block (solid)","SBC block (hollow)","SBC block (solid, city-cast)"]
DIST={c:tuple(R["DIST"][c][m] for m in KEY) for c in CLIM}
ORDT=ORD[:2]+["SBC block (solid, city-cast)"]+ORD[2:]
fig,axes=plt.subplots(1,3,figsize=(7.3,3.1),sharey=True)
for k,c in enumerate(CLIM):
    ax=axes[k]; d=dict(zip(KEY,DIST[c])); prod=[A1[m] for m in ORDT]; tr=[R["MASS"][m]/1000*d[m]*0.10 for m in ORDT]; xx=np.arange(len(ORDT))
    ax.bar(xx,prod,color="#4a5560",label="Production (A1–A3)",linewidth=0,zorder=3)
    b=ax.bar(xx,tr,bottom=prod,color=S.VERM,label="Transport (A4)",linewidth=0,zorder=3)
    ax.bar_label(b,labels=[f"{p+t:.0f}" for p,t in zip(prod,tr)],padding=1.5,fontsize=6,color=INK)
    ax.set_xticks(xx); ax.set_xticklabels([SH[m].replace("\n"," ") for m in ORDT],rotation=40,ha="right",fontsize=6.8)
    S.panel(ax,"abc"[k],x=-0.02,y=1.02); ax.text(0.5,1.02,S.CLIMLAB[c].split(" (")[0],transform=ax.transAxes,ha="center",va="bottom",fontsize=8.5)
    S.despine(ax); gy(ax); ax.set_ylim(0,124)
    if k==0: ax.set_ylabel("Embodied carbon\n(kg CO$_2$-eq m$^{-2}$ wall)")
axes[2].legend(loc="upper right",fontsize=7,handlelength=1.1)
plt.tight_layout(); plt.savefig(f"{OUT}/nat_transport.png"); plt.close()

# ---------- production carbon: Monte-Carlo violin ----------
_SN={"Concrete (ref.)":"Concrete","Adobe-type block":"Adobe","Volcanic stone (recinto)":"Volcanic stone","Tepetate ashlar":"Tepetate","SBC block (solid)":"SBC solid","SBC block (hollow)":"SBC hollow"}
MCv={_SN[m]:(R["A1A3"][m],R["CV"][m]) for m in sorted(R["A1A3"],key=lambda k:R["A1A3"][k]) if m in _SN}
rng=np.random.default_rng(7); order=sorted(MCv,key=lambda m:MCv[m][0]); samp={}
for m,(mu,cv) in MCv.items():
    sg=np.sqrt(np.log(1+(cv/100)**2)); samp[m]=rng.lognormal(np.log(mu)-sg*sg/2,sg,500)
fig,ax=plt.subplots(figsize=(5.2,3.2)); xx=np.arange(6)
vp=ax.violinplot([samp[m] for m in order],positions=xx,widths=0.8,showextrema=False)
for bd,m in zip(vp["bodies"],order): bd.set_facecolor(S.MATCOL[m]); bd.set_alpha(0.45); bd.set_edgecolor(S.MATCOL[m]); bd.set_linewidth(0.6)
for xi,m in zip(xx,order):
    p5,p95=np.percentile(samp[m],[5,95]); ax.plot([xi,xi],[p5,p95],color=INK,lw=0.9,zorder=4)
    for qv in (p5,p95): ax.plot([xi-0.07,xi+0.07],[qv,qv],color=INK,lw=0.9,zorder=4)
    ax.scatter([xi],[MCv[m][0]],s=16,color="white",edgecolor=INK,lw=0.9,zorder=5); ax.text(xi+0.16,MCv[m][0],f"{MCv[m][0]:.1f}",fontsize=6.5,va="center",color=INK)
ax.set_xticks(xx); ax.set_xticklabels([m.replace("Adobe","Earth block") for m in order],fontsize=7.2); ax.set_ylim(0,108)
ax.set_ylabel("Production carbon, A1–A3\n(kg CO$_2$-eq m$^{-2}$ wall)"); S.despine(ax); gy(ax)
ax.legend(handles=[ml.Line2D([],[],marker="o",mfc="white",mec=INK,color=INK,lw=0.9,ms=4,label="mean and P5–P95")],loc="upper left",fontsize=6.8)
plt.tight_layout(); plt.savefig(f"{OUT}/nat_embodied.png"); plt.close()

for f in ["nat_thermal","nat_transport","nat_embodied","nat_operclimate","nat_offsetclimate","nat_costcarbon","nat_sensitivity"]: __import__("shutil").copy(f"{OUT}/{f}.png",f"{DST}/{f}.png")
print("ok")
