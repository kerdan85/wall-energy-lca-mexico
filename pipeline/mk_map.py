#!/usr/bin/env python3
"""Sourcing map on real Koppen-Geiger classes (0.5 deg grid, Rubel & Kottek via kgc) and Natural Earth
outlines, both recovered from the vector map of the companion Energies paper (map_real.json),
with OSRM road routes, sources and cities."""
import os
HERE=os.path.dirname(os.path.abspath(__file__))
OUT=HERE; DST=os.path.normpath(os.path.join(HERE,"..","figures")); os.makedirs(DST,exist_ok=True)
import json, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.patheffects as pe, matplotlib.lines as ml
from matplotlib.patches import Patch, PathPatch, Rectangle
from matplotlib.path import Path
import style_nat as S; S.apply()


INK=S.INK; MUT=S.MUT
D=json.load(open(f"{OUT}/map_real.json")); routes=json.load(open(f"{OUT}/mexico_routes.json"))
CC=[('Af','#0b5fa5'),('Am','#2a78d6'),('Aw','#86b6ef'),('As','#b7d3f6'),('BWh','#c9462c'),('BWk','#eb8f6a'),('BSh','#eda100'),('BSk','#f5cf73'),
    ('Cwa','#1baf7a'),('Cwb','#7fd1ae'),('Cfa','#008300'),('Cfb','#6fb86f'),('Csa','#c9d64f'),('Csb','#e4eb9a')]
CM=dict(CC)
LB=dict(Af='Af  tropical rainforest',Am='Am  tropical monsoon',Aw='Aw  tropical savanna',As='As  tropical, dry summer',BWh='BWh  hot desert',BWk='BWk  cold desert',
        BSh='BSh  hot steppe',BSk='BSk  cold steppe',Cwa='Cwa  temperate, dry winter, hot summer',Cwb='Cwb  temperate, dry winter, warm summer',
        Cfa='Cfa  temperate, no dry season, hot summer',Cfb='Cfb  temperate, no dry season, warm summer',Csa='Csa  temperate, dry hot summer',Csb='Csb  temperate, dry warm summer')
SARG="#111111"; VOLC="#5a2d82"; VLINE="#e9c46a"
halo=[pe.withStroke(linewidth=2.4,foreground="white")]
fig,ax=plt.subplots(figsize=(7.4,4.25))
ax.set_facecolor("#ffffff")
for p in D["neigh"]:
    a=np.array(p); ax.fill(a[:,0],a[:,1],fc="#f0efec",ec="#c9c8c2",lw=0.4,zorder=1)
verts=[];codes=[]
for p in D["mex"]:
    a=np.array(p); verts+=a.tolist(); codes+=[Path.MOVETO]+[Path.LINETO]*(len(a)-1)
clip=PathPatch(Path(verts,codes),transform=ax.transData,fc="none",ec="#3a3a38",lw=0.7,zorder=4); ax.add_patch(clip)
used=set()
for x,y,k in D["cells"]:
    used.add(k); r=ax.add_patch(Rectangle((x-0.25,y-0.25),0.5,0.5,fc=CM[k],ec=CM[k],lw=0.15,alpha=0.82,zorder=2)); r.set_clip_path(clip)
for x,y,t in [(-101.5,31.9,"UNITED STATES"),(-90.3,15.2,"GUATEMALA"),(-88.6,17.3,"BELIZE")]:
    ax.text(x,y,t,fontsize=5.6,color="#9a968c",ha="center",va="center",zorder=1.5)
for x,y,t in [(-93.0,25.0,"Gulf of Mexico"),(-112.0,20.0,"Pacific Ocean")]:
    ax.text(x,y,t,fontsize=6.4,color="#9bb0ba",style="italic",ha="center",va="center")
# routes
for key,r in routes.items():
    xs=[c[0] for c in r["coords"]]; ys=[c[1] for c in r["coords"]]
    if r["src"]=="sargassum":
        ax.plot(xs,ys,color="white",lw=4.2,zorder=5,solid_capstyle="round"); ax.plot(xs,ys,color=SARG,lw=2.8,zorder=6,solid_capstyle="round")
for key,r in routes.items():
    xs=[c[0] for c in r["coords"]]; ys=[c[1] for c in r["coords"]]
    if r["src"]=="volcanic":
        ax.plot(xs,ys,color="#e9c46a",lw=1.1,zorder=7,dashes=(3.0,2.2))
CHIP={"sarg_cdmx":(-94.6,20.25,SARG),"sarg_mer":(-88.2,22.3,SARG),"sarg_her":(-103.6,26.6,SARG),"volc_mer":(-92.6,16.9,VOLC),"volc_her":(-108.6,24.6,VOLC)}
for k,(x,y,c) in CHIP.items():
    ax.text(x,y,f"{routes[k]['km']:,} km",fontsize=6.4,color=c,ha="center",va="center",fontweight="bold",zorder=9,bbox=dict(boxstyle="round,pad=0.2",fc="white",ec=c,lw=0.6))
# nodes
V=(-98.90,19.50); Sg=(-86.87,20.85)
ax.scatter(*V,marker="*",s=190,color=VOLC,edgecolor="white",lw=0.9,zorder=10); ax.scatter(*Sg,marker="*",s=190,color=SARG,edgecolor="white",lw=0.9,zorder=10)
def cls(lon,lat):
    return min(D["cells"],key=lambda c:(c[0]-lon)**2+(c[1]-lat)**2)[2]
CIT={"Mexico City":(-99.13,19.43,(-102.6,16.0)),"Mérida":(-89.62,20.97,(-91.0,23.9)),"Hermosillo":(-110.96,29.07,(-107.6,31.2))}
for nm,(x,y,(lx,ly)) in CIT.items():
    ax.plot(x,y,"o",ms=6.5,mfc="#fcfcfb",mec="#0b0b0b",mew=1.3,zorder=11)
    ax.annotate(f"{nm}\n{cls(x,y)}",(x,y),(lx,ly),fontsize=7.6,fontweight="bold",ha="center",va="center",zorder=12,
                arrowprops=dict(arrowstyle="-",lw=0.7,color="#0b0b0b"),bbox=dict(fc="#fcfcfb",ec="#8a8984",lw=0.5,boxstyle="round,pad=0.22"))
    print(nm,cls(x,y))
ax.annotate("Volcanic-belt quarries\n(recinto, tepetate)",V,(-104.2,21.6),fontsize=6.6,color=VOLC,fontweight="bold",ha="center",va="center",zorder=12,
            arrowprops=dict(arrowstyle="-",lw=0.6,color=VOLC),bbox=dict(fc="white",ec="none",alpha=0.85,boxstyle="round,pad=0.15"))
ax.annotate("Sargassum landings and\nSBC block plant",Sg,(-88.6,26.3),fontsize=6.6,color=SARG,fontweight="bold",ha="center",va="center",zorder=12,
            arrowprops=dict(arrowstyle="-",lw=0.6,color=SARG))
# scale bar
kml=111.32*np.cos(np.radians(23)); x0,y0=-117.6,15.0; seg=500/kml
ax.plot([x0,x0+seg],[y0,y0],color=INK,lw=1.2,zorder=12)
for xx in (x0,x0+seg): ax.plot([xx,xx],[y0,y0+0.2],color=INK,lw=1.0,zorder=12)
ax.text(x0+seg/2,y0+0.3,"500 km",ha="center",va="bottom",fontsize=6.2,color=INK)
# legends
order=[c for c,_ in CC if c in used]
h1=[ml.Line2D([],[],marker="*",color="w",mfc="#444",ms=9,ls="",label="Material source"),
    ml.Line2D([],[],marker="o",color="w",mfc="w",mec=INK,mew=1.2,ms=5.5,ls="",label="Case-study city"),
    ml.Line2D([],[],color=SARG,lw=2.8,label="SBC block route (road)"),
    (ml.Line2D([],[],color=SARG,lw=2.8),ml.Line2D([],[],color=VLINE,lw=1.1,dashes=(3.0,2.2)))]
lg1=ax.legend(handles=h1,labels=["Material source","Case-study city","SBC block route (road)","Shared with volcanic stone\nand tepetate route (road)"],loc="upper left",bbox_to_anchor=(1.0,1.0),fontsize=6.6,frameon=False,title="Supply",title_fontsize=7,alignment="left")
ax.add_artist(lg1)
ax.legend(handles=[Patch(fc=CM[c],alpha=0.82,label=LB[c]) for c in order],loc="lower left",bbox_to_anchor=(1.0,-0.02),fontsize=6.4,frameon=False,
          title="Köppen–Geiger class",title_fontsize=7,alignment="left",labelspacing=0.32)
ax.set_xlim(-118.5,-86); ax.set_ylim(14,33); ax.set_aspect(1.08)
ax.set_xticks(range(-115,-85,5)); ax.set_xticklabels([f"{abs(v)}°W" for v in range(-115,-85,5)],fontsize=6.5)
ax.set_yticks(range(15,35,5)); ax.set_yticklabels([f"{v}°N" for v in range(15,35,5)],fontsize=6.5)
for s in ("top","right"): ax.spines[s].set_visible(False)
ax.tick_params(length=2.5)
fig.savefig(f"{OUT}/nat_map.png",dpi=400,facecolor="white",bbox_inches="tight")
import shutil; shutil.copy(f"{OUT}/nat_map.png",f"{DST}/nat_map.png"); print("map saved")
