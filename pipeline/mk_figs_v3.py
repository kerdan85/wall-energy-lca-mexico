#!/usr/bin/env python3
"""v3: EN 15804 module grid (system boundary), multi-criteria dot plot, case-study figure."""
import os
HERE=os.path.dirname(os.path.abspath(__file__))
OUT=HERE; DST=os.path.normpath(os.path.join(HERE,"..","figures")); os.makedirs(DST,exist_ok=True)
import numpy as np, matplotlib.pyplot as plt, os
from matplotlib.patches import Rectangle
from PIL import Image
import style_nat as S; S.apply()

INK=S.INK; MUT=S.MUT

# ---------------- system boundary: EN 15804 module declaration grid ----------------
# Conventional EN 15978 / EPD layout: per-stage light colours, thin black grid, serif type.
import glob as _g, matplotlib.font_manager as _fm
for _f in _g.glob("/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyretermes-*.otf")+_g.glob(os.path.join(HERE,"fonts","texgyretermes-*.otf")):
    try: _fm.fontManager.addfont(_f)
    except Exception: pass
with plt.rc_context({"font.family":"serif","font.serif":["TeX Gyre Termes","STIXGeneral","DejaVu Serif"],"mathtext.fontset":"stix"}):
    fig,ax=plt.subplots(figsize=(7.3,2.75)); ax.axis("off"); ax.set_xlim(-0.05,17.25); ax.set_ylim(-3.1,5.45)
    MODS=[("A1","Raw material\nsupply"),("A2","Transport"),("A3","Manufacturing"),("A4","Transport\nto site"),("A5","Construction,\ninstallation"),
          ("B1","Use"),("B2","Maintenance"),("B3","Repair"),("B4","Replacement"),("B5","Refurbishment"),("B6","Operational\nenergy"),("B7","Operational\nwater"),
          ("C1","Demolition"),("C2","Transport"),("C3","Waste\nprocessing"),("C4","Disposal"),("D","Reuse,\nrecovery,\nrecycling")]
    INC={"A1","A2","A3","A4","B6"}
    GR=[("Product\nstage",0,3,"#dbe4f0"),("Construction\nstage",3,5,"#f8e1cf"),("Use stage",5,12,"#e3efdc"),("End-of-life stage",12,16,"#fbf0c9"),("Beyond\nthe\nboundary",16,17,"#e6e6e6")]
    K="#000000"; LW=0.6
    for name,a_,b_,col in GR:
        ax.add_patch(Rectangle((a_,4.1),b_-a_,1.25,fc=col,ec=K,lw=LW)); ax.text((a_+b_)/2,4.72,name,ha="center",va="center",fontsize=7.6 if b_-a_>1 else 5.9,linespacing=0.95)
        for i in range(a_,b_):
            c,n=MODS[i]; inc=c in INC
            ax.add_patch(Rectangle((i,3.35),1,0.75,fc=col,ec=K,lw=LW)); ax.text(i+0.5,3.725,c,ha="center",va="center",fontsize=8.2,fontweight="bold")
            ax.add_patch(Rectangle((i,1.0),1,2.35,fc="white",ec=K,lw=LW)); ax.text(i+0.5,2.175,n,ha="center",va="center",fontsize=6.2,rotation=90,linespacing=0.95)
            ax.add_patch(Rectangle((i,0.2),1,0.8,fc=(col if inc else "white"),ec=K,lw=LW))
            ax.text(i+0.5,0.6,"X" if inc else "MND",ha="center",va="center",fontsize=8.6 if inc else 6.0,fontweight="bold" if inc else "normal",color=K if inc else "#6b6b6b")
    # declared boundaries (heavy outline) and their functional units
    for a_,b_ in ((0,4),(10,11)): ax.add_patch(Rectangle((a_,0.2),b_-a_,3.9,fc="none",ec=K,lw=1.6))
    def bracket(a_,b_,y,txt):
        ax.plot([a_+0.05,a_+0.05,b_-0.05,b_-0.05],[y+0.25,y,y,y+0.25],color=K,lw=0.9)
        ax.text(a_+0.05,y-0.32,txt,ha="left",va="top",fontsize=7.6)
    bracket(0,4,-0.35,"Embodied assessment (A1–A4); functional unit: 1 m$^2$ of external wall")
    bracket(0,11,-1.75,"Integrated assessment (A1–A4 + B6); functional unit: the dwelling over a 50-year service life")
    ax.text(17.0,-2.95,"X = module declared;  MND = module not declared",ha="right",va="bottom",fontsize=6.8,style="italic")
    plt.savefig(f"{OUT}/nat_boundary.png",bbox_inches="tight",dpi=400); plt.close()

# ---------------- multi-criteria: dot plot + single score ----------------
cats=["Climate change","Water use","Acidification","Eutrophication","Human toxicity","Fossil resources"]
absd={"Concrete":[35.3,0.061,0.067,4.5e-4,6.2e-7,4.06],"Adobe":[27.7,0.043,0.048,3.3e-4,4.5e-7,5.64],"Volcanic stone":[3.4,0.082,0.0085,9.2e-5,1.4e-7,0.78],
      "Tepetate":[4.7,0.108,0.0112,1.2e-4,2.0e-7,1.11],"SBC solid":[47.9,0.074,0.090,6.0e-4,1.4e-6,9.62],"SBC hollow":[37.7,0.058,0.071,4.8e-4,1.1e-6,7.57]}
import lca_inputs; absd=lca_inputs.multicat(absd)
ref=absd["Concrete"]; rel={m:[absd[m][j]/ref[j] for j in range(6)] for m in absd}; score={m:float(np.mean(rel[m])) for m in absd}
MK={"Tepetate":"o","Volcanic stone":"s","Adobe":"D","SBC hollow":"^","SBC solid":"v"}
fig,(a,b)=plt.subplots(1,2,figsize=(7.3,3.0),gridspec_kw={"width_ratios":[1.55,1]})
for j in range(6):
    y=5-j; v=[rel[m][j] for m in MK]; a.plot([min(v),max(v)],[y,y],color="#cfcfcf",lw=1.2,zorder=1)
    for m in MK: a.scatter([rel[m][j]],[y],marker=MK[m],s=30,color=S.MATCOL[m],edgecolor=INK,lw=0.5,zorder=3,label=(m.replace("Adobe","Earth block") if j==0 else None))
a.axvline(1,color=INK,lw=0.8,ls=(0,(4,3))); a.text(1.03,5.62,"concrete",fontsize=6.3,color=MUT,va="center")
a.set_xscale("log"); a.set_xlim(0.07,3.4); a.set_xticks([0.1,0.2,0.5,1,2]); a.set_xticklabels(["0.1","0.2","0.5","1","2"])
a.set_yticks(range(6)); a.set_yticklabels(cats[::-1],fontsize=7.4); a.set_ylim(-0.6,5.9)
a.set_xlabel("Impact relative to concrete (log scale)"); a.grid(axis="x",zorder=0); S.despine(a); a.tick_params(axis="y",length=0)
a.legend(loc="lower center",bbox_to_anchor=(0.5,1.0),ncol=5,fontsize=6.4,handletextpad=0.1,columnspacing=0.8,frameon=False)
order=sorted(score,key=lambda m:score[m]); yy=np.arange(len(order))
b.barh(yy,[score[m] for m in order],color=[S.MATCOL[m] for m in order],edgecolor=INK,lw=0.4,height=0.62,zorder=3)
b.axvline(1,color=INK,lw=0.8,ls=(0,(4,3)))
for i,m in enumerate(order): b.text(score[m]+0.04,i,f"{score[m]:.2f}",va="center",fontsize=7)
b.set_yticks(yy); b.set_yticklabels([m.replace("Adobe","Earth block") for m in order],fontsize=7.4); b.set_xlim(0,1.95); b.set_xlabel("Equal-weight score (concrete = 1)"); S.despine(b); b.grid(axis="x",zorder=0); b.tick_params(axis="y",length=0)
S.panel(a,"a",x=-0.30,y=1.0); S.panel(b,"b",x=-0.34,y=1.0)
plt.tight_layout(); plt.savefig(f"{OUT}/nat_multicat.png"); plt.close()

# ---------------- case study: photograph, DesignBuilder model, wall build-up ----------------
ph=Image.open(f"{OUT}/assets/house_photo.png"); db=Image.open(f"{OUT}/assets/house_db.png")
# crop away the burned-in panel tags of the source figure
ph=ph.crop((0,int(ph.size[1]*0.12),ph.size[0],ph.size[1])); db=db.crop((int(db.size[0]*0.10),int(db.size[1]*0.10),db.size[0],db.size[1]))
fig=plt.figure(figsize=(7.3,2.75))
a1=fig.add_axes([0.005,0.03,0.285,0.88]); a1.imshow(ph); a1.axis("off")
a2=fig.add_axes([0.305,0.03,0.375,0.88]); a2.imshow(db); a2.axis("off")
a3=fig.add_axes([0.695,0.02,0.305,0.93]); a3.set_xlim(0,1); a3.set_ylim(0,1); a3.axis("off")
# two-room chamber: warm room | test wall | cold room
WARM="#f4e6d8"; COLD="#e1e9f0"; WALL="#c9bfae"; MORT="#efe9df"
a3.add_patch(Rectangle((0.02,0.30),0.40,0.56,fc=WARM,ec=INK,lw=0.6))
a3.add_patch(Rectangle((0.58,0.30),0.40,0.56,fc=COLD,ec=INK,lw=0.6))
wx,ww=0.42,0.16
a3.add_patch(Rectangle((wx,0.30),ww,0.56,fc=WALL,ec=INK,lw=0.8))
for k in range(1,6):                                    # mortar bed joints
    yy=0.30+k*0.56/6; a3.plot([wx,wx+ww],[yy,yy],color=MORT,lw=1.4)
a3.text(0.22,0.80,"Warm room\n30 °C",ha="center",va="top",fontsize=6.4,color=INK)
a3.text(0.78,0.80,"Cold room\n17 °C",ha="center",va="top",fontsize=6.4,color=INK)
a3.text(0.50,0.885,"Test wall (~1 m$^2$)",ha="center",va="bottom",fontsize=6.2,color=INK)
# heat-flux plate and surface thermocouples
a3.add_patch(Rectangle((wx-0.022,0.50),0.022,0.12,fc="#33414e",ec="none"))
a3.annotate("heat-flux\nplate, $q$",xy=(wx-0.022,0.60),xytext=(0.17,0.62),fontsize=5.8,ha="center",va="center",color=INK,
            arrowprops=dict(arrowstyle="-",color=INK,lw=0.5))
for xx,lab,tx in ((wx-0.004,"$T_{si}$",0.30),(wx+ww+0.004,"$T_{se}$",0.70)):
    a3.plot([xx],[0.44],"o",ms=3.2,color="#8a5a2b"); a3.annotate(lab,xy=(xx,0.44),xytext=(tx,0.40),fontsize=6.4,ha="center",va="center",color=INK,arrowprops=dict(arrowstyle="-",color=INK,lw=0.5))
for xx,lab in ((0.10,"$T_i$"),(0.90,"$T_e$")):
    a3.plot([xx],[0.52],"^",ms=3.4,color=INK); a3.text(xx,0.47,lab,ha="center",va="top",fontsize=6.2,color=INK)
a3.annotate("",xy=(0.72,0.66),xytext=(0.28,0.66),arrowprops=dict(arrowstyle="-|>",color="#8a5a2b",lw=1.4))
# reduction
a3.text(0.50,0.215,"$\\Lambda=\\sum q\\,/\\sum (T_{si}-T_{se})$",ha="center",va="center",fontsize=6.8,color=INK)
a3.text(0.50,0.115,"$U=1/(1/\\Lambda+R_{si}+R_{se})$",ha="center",va="center",fontsize=6.8,color=INK)
a3.text(0.50,0.025,"ISO 9869-1 · ISO 6946",ha="center",va="center",fontsize=5.6,color=MUT)
for ax_,l in ((a1,"a"),(a2,"b"),(a3,"c")): ax_.text(0.0,1.04 if ax_ is not a3 else 0.985,l,transform=ax_.transAxes,fontsize=10,fontweight="bold",va="bottom" if ax_ is not a3 else "top")
plt.savefig(f"{OUT}/nat_house3d.png",dpi=350,facecolor="white"); plt.close()
for f in ["nat_boundary","nat_multicat","nat_house3d"]: __import__("shutil").copy(f"{OUT}/{f}.png",f"{DST}/{f}.png")
print("v3 done")
