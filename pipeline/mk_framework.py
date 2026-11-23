#!/usr/bin/env python3
"""Figure 1 - methodology: four stage tiles (photo / model / LCA / result) on top of a full process flow chart."""
import os
HERE=os.path.dirname(os.path.abspath(__file__))
OUT=HERE; DST=os.path.normpath(os.path.join(HERE,"..","figures")); os.makedirs(DST,exist_ok=True)
import json, glob, numpy as np, matplotlib.pyplot as plt, os
from PIL import Image, ImageChops, ImageOps
from matplotlib.patches import Rectangle, Polygon, FancyBboxPatch
import style_nat as S; S.apply()


INK="#1c1c1c"; MUT="#6a6a6a"; LINE="#2b2b2b"; DARK="#33414e"; ACC="#8a5a2b"
def trim(path):
    im=Image.open(path).convert("RGB"); bb=ImageChops.difference(im,Image.new("RGB",im.size,(255,255,255))).getbbox(); return im.crop(bb)
LOGO={"eplus":trim(f"{OUT}/assets/logo_energyplus.png"),"bw":trim(f"{OUT}/assets/logo_brightway.png"),"eco":trim(f"{OUT}/assets/logo_ecoinvent.png")}
FW,FH=7.4,8.4
fig=plt.figure(figsize=(FW,FH)); bg=fig.add_axes([0,0,1,1]); bg.set_xlim(0,1); bg.set_ylim(0,1); bg.axis("off")
X0=[0.035,0.280,0.525,0.770]; CW=0.195; C=[x+CW/2 for x in X0]; TY,TH=0.818,0.128
HEAD=["MEASURE","SIMULATE","ASSESS","INTEGRATE"]
for i,x in enumerate(X0):
    bg.add_patch(Rectangle((x-0.008,0.022),CW+0.016,0.742,fc="none",ec="#b5b5b5",lw=0.7,ls=(0,(1,2.2)),zorder=0))
    bg.text(x,0.978,f"0{i+1}",fontsize=17,color="#c4c4c4",fontweight="bold",va="center"); bg.text(x+0.052,0.981,HEAD[i],fontsize=9.2,color=INK,fontweight="bold",va="center")
    bg.add_patch(Rectangle((x,TY),CW,TH,fc="white",ec=LINE,lw=0.7,zorder=1))
def fitimg(ax,im,cx=0.5,cy=0.5):
    bb=ax.get_position(); asp=(bb.width*FW)/(bb.height*FH); W,H=im.size
    ch=int(min(H,W/asp)); cw=int(ch*asp); l=int((W-cw)*cx); t=int((H-ch)*cy); ax.imshow(im.crop((l,t,l+cw,t+ch))); ax.axis("off")
a=fig.add_axes([X0[0]+0.001,TY+0.001,CW-0.002,TH-0.002]); fitimg(a,ImageOps.exif_transpose(Image.open(f"{OUT}/assets/04_muro_instrumentado_tabique.jpg")).convert("RGB"),0.5,0.45)
a=fig.add_axes([X0[1]+0.001,TY+0.001,CW-0.002,TH-0.002]); db=Image.open(f"{OUT}/assets/house_db.png"); fitimg(a,db.crop((int(db.size[0]*0.12),int(db.size[1]*0.12),int(db.size[0]*0.92),db.size[1])),0.45,0.5)
# LCA tile
ax2=fig.add_axes([X0[2]+0.02,TY+0.012,CW-0.034,TH*0.60]); _J=json.load(open(f"{OUT}/robust_results.json")); MC=[(_J["A1A3"][m],_J["CV"][m]) for m in ["Volcanic stone (recinto)","Tepetate ashlar","Adobe-type block","Concrete (ref.)","SBC block (hollow)","SBC block (solid)"]]; rng=np.random.default_rng(7)
vp=ax2.violinplot([rng.lognormal(np.log(m)-np.log(1+(c/100)**2)/2,np.sqrt(np.log(1+(c/100)**2)),500) for m,c in MC],showextrema=False,widths=0.85)
for b,k in zip(vp["bodies"],["Volcanic stone","Tepetate","Adobe","Concrete","SBC hollow","SBC solid"]): b.set_facecolor(S.MATCOL[k]); b.set_alpha(0.9); b.set_edgecolor("none")
ax2.set_xticks([]); ax2.set_yticks([]); ax2.patch.set_alpha(0); ax2.set_ylabel("kg CO$_2$-eq m$^{-2}$",fontsize=5.2,labelpad=1)
for sp in ["top","right"]: ax2.spines[sp].set_visible(False)
for k,lab in enumerate(["A1–A3","A4","B6"]):
    bg.add_patch(Rectangle((X0[2]+0.012+k*0.044,TY+TH-0.030),0.040,0.022,fc=DARK if k!=1 else ACC,ec="none",zorder=3)); bg.text(X0[2]+0.032+k*0.044,TY+TH-0.019,lab,ha="center",va="center",color="white",fontsize=5.6,fontweight="bold",zorder=4)
# quadrant tile
_R=json.load(open(f"{OUT}/robust_results.json"))["BASE"]; e={c:{m:{"dCap":v["dC"]/176.53,"annual":0.0,"offset":v["dCO2"]} for m,v in _R[c].items()} for c in _R}; ax4=fig.add_axes([X0[3]+0.022,TY+0.014,CW-0.034,TH-0.026])
for m,k in [("Tepetate ashlar","Tepetate"),("Adobe-type block","Adobe"),("SBC block (solid)","SBC solid"),("SBC block (hollow)","SBC hollow"),("Volcanic stone (recinto)","Volcanic stone")]:
    xs=[(e[c][m]["dCap"]*176.53-e[c][m]["annual"]*50)/1000 for c in e]; ys=[e[c][m]["offset"] for c in e]; o=np.argsort(xs)
    ax4.plot(np.array(xs)[o],np.array(ys)[o],color=S.MATCOL[k],lw=0.7); ax4.scatter(xs,ys,s=8,color=S.MATCOL[k],edgecolor=INK,lw=0.25,zorder=3)
ax4.axhline(0,color=INK,lw=0.6); ax4.axvline(0,color=INK,lw=0.6); ax4.set_xlim(-140,160); ax4.set_ylim(-27,47); ax4.set_xticks([]); ax4.set_yticks([]); ax4.patch.set_alpha(0)
ax4.set_xlabel("net cost $\\rightarrow$",fontsize=5.2,labelpad=1); ax4.set_ylabel("CO$_2$ offset $\\rightarrow$",fontsize=5.2,labelpad=1)
for sp in ax4.spines.values(): sp.set_visible(False)
# tools row
TR=0.790
def logo(key,x,h):
    im=LOGO[key]; ar=im.size[0]/im.size[1]; ww=h*ar*FH/FW; la=fig.add_axes([x,TR-h/2,ww,h]); la.imshow(im); la.axis("off"); return x+ww
bg.text(X0[0],TR+0.007,"Heat-flow meter (TRSYS20)",fontsize=6.4,color=INK,va="center",fontweight="bold"); bg.text(X0[0],TR-0.011,"ISO 9869-1 · ISO 6946",fontsize=6,color=MUT,va="center")
xe=logo("eplus",X0[1],0.040); bg.text(xe+0.006,TR+0.007,"DesignBuilder model",fontsize=6,color=MUT,va="center"); bg.text(xe+0.006,TR-0.011,"$\\rightarrow$ EnergyPlus 25.1 model",fontsize=6.4,color=INK,va="center",fontweight="bold")
xe=logo("bw",X0[2],0.042); logo("eco",xe+0.012,0.020)
bg.text(X0[3],TR+0.007,"$\\Delta$CO$_2$ = operation + embodied",fontsize=6.2,color=INK,va="center",fontweight="bold"); bg.text(X0[3],TR-0.011,"$\\Delta C$ = capital $-$ energy saved",fontsize=6.2,color=INK,va="center",fontweight="bold")

# ------------------------- flow chart -------------------------
R={k:0.722-0.0805*i for i,k in enumerate(range(1,10))}   # rows 1..9
W_,H_=0.168,0.046; FS=6.0
def node(x,y,txt,kind="proc",w=W_,h=H_):
    if kind=="proc": bg.add_patch(Rectangle((x-w/2,y-h/2),w,h,fc="white",ec=LINE,lw=0.8,zorder=3))
    elif kind=="data":
        sk=0.012; bg.add_patch(Polygon([(x-w/2+sk,y+h/2),(x+w/2,y+h/2),(x+w/2-sk,y-h/2),(x-w/2,y-h/2)],closed=True,fc="white",ec=LINE,lw=0.8,zorder=3))
    elif kind=="term": bg.add_patch(FancyBboxPatch((x-w/2+0.012,y-h/2),w-0.024,h,boxstyle="round,pad=0,rounding_size=0.02",fc="white",ec=LINE,lw=0.8,zorder=3,mutation_aspect=FW/FH))
    elif kind=="dec": bg.add_patch(Polygon([(x,y+h/2),(x+w/2,y),(x,y-h/2),(x-w/2,y)],closed=True,fc="white",ec=LINE,lw=0.9,zorder=3))
    elif kind=="out": bg.add_patch(Rectangle((x-w/2,y-h/2),w,h,fc=DARK,ec=DARK,lw=0.8,zorder=3))
    bg.text(x,y,txt,ha="center",va="center",fontsize=FS,color="white" if kind=="out" else INK,zorder=4,linespacing=1.15,fontweight="bold" if kind=="out" else "normal")
def arrow(pts,lab=None,lp=None,col=LINE,ls="-"):
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    if len(pts)>2: bg.plot(xs[:-1],ys[:-1],color=col,lw=0.8,ls=ls,zorder=2,solid_joinstyle="miter")
    bg.annotate("",xy=pts[-1],xytext=pts[-2],arrowprops=dict(arrowstyle="-|>",color=col,lw=0.8,ls=ls,shrinkA=0,shrinkB=0,mutation_scale=7),zorder=2)
    if lab: bg.text(lp[0],lp[1],lab,fontsize=5.4,color=MUT,ha="center",va="center",zorder=5,style="italic",bbox=dict(fc="white",ec="none",pad=0.6))
h2=H_/2; c1,c2,c3,c4=C
# column 1
node(c1,R[1],"Six wall materials\n(1 m$^2$ test walls)","term"); node(c1,R[2],"Two-room chamber test\n$\\Delta T\\approx$13 K, heat-flow meter")
node(c1,R[3],"3 estimators\nagree within 5%?","dec",w=0.16,h=0.066); node(c1,R[4],"Measured $U$, assigned $\\kappa$\n(input set 1)","data"); node(c1,R[5],"Tabulated $U$\n(input set 2)","data")
arrow([(c1,R[1]-h2),(c1,R[2]+h2)]); arrow([(c1,R[2]-h2),(c1,R[3]+0.033)]); arrow([(c1,R[3]-0.033),(c1,R[4]+h2)],"yes",(c1+0.016,R[3]-0.041))
arrow([(c1-0.08,R[3]),(c1-0.092,R[3]),(c1-0.092,R[2]),(c1-W_/2,R[2])],"no: longer\nwindow",(c1-0.071,R[3]+0.034))
bg.text(c1,R[5]-0.040,"ISO 10456 · ASHRAE · literature",fontsize=5.2,color=MUT,ha="center")
# column 2
node(c2,R[1],"DesignBuilder model\n(companion study)","data"); node(c2,R[2],"Rebuild in EnergyPlus,\ncalibrate to 13 runs"); node(c2,R[3],"TMYx weather files\n(3 cities)","data")
node(c2,R[4],"EnergyPlus simulation\n6 materials $\\times$ 3 climates $\\times$ 2 sets",h=0.05); node(c2,R[5],"Annual demand\n$D_{meas}$ and $D_{tab}$","data"); node(c2,R[6],"Error of tabulated inputs\n$(D_{tab}-D_{meas})/D_{meas}$","out")
for a_,b_ in [(1,2),(2,3)]: arrow([(c2,R[a_]-h2),(c2,R[b_]+h2)])
arrow([(c2,R[3]-h2),(c2,R[4]+0.025)]); arrow([(c2,R[4]-0.025),(c2,R[5]+h2)]); arrow([(c2,R[5]-h2),(c2,R[6]+h2)])
arrow([(c1+W_/2-0.006,R[4]),(c2-W_/2,R[4])]); arrow([(c1+W_/2-0.006,R[5]),(c2-0.05,R[5]+0.012),(c2-0.05,R[4]-0.025)]) if False else arrow([(c1+W_/2-0.006,R[5]),(X0[1]-0.012,R[5]),(X0[1]-0.012,R[4]-0.014),(c2-W_/2,R[4]-0.014)])
# column 3
node(c3,R[1],"Material inventory +\necoinvent background","data"); node(c3,R[2],"Production A1–A3\nMonte Carlo, $n$ = 1,000"); node(c3,R[3],"Transport A4 = $m\\,d\\,e_T$\nroad distance source$\\rightarrow$city")
node(c3,R[4],"Operation B6 = $E\\,A_f\\,N\\,f$\n(grid emission factor)"); node(c3,R[5],"Whole-life carbon\nper material and city","data"); node(c3,R[7],"Monte-Carlo, sensitivity\nand scenario analyses","out")
for a_,b_ in [(1,2),(2,3),(3,4),(4,5)]: arrow([(c3,R[a_]-h2),(c3,R[b_]+h2)])
arrow([(c3,R[5]-h2),(c3,R[7]+h2)],col="#8a8a8a",ls=(0,(3,2)))
arrow([(c2+W_/2,R[4]),(c3-W_/2,R[4])],"$D_{meas}$",((c2+c3)/2,R[4]+0.011))
# column 4
node(c4,R[1],"Installed wall cost $p$\nelectricity tariff $c_e$","data"); node(c4,R[2],"Net present cost $\\Delta C$\nvs concrete"); node(c4,R[5],"Lifetime offset $\\Delta$CO$_2$\nvs concrete")
node(c4,R[6],"$\\Delta$CO$_2$ > 0 ?","dec",w=0.14,h=0.058); node(c4,R[7],"$\\Delta C$ < 0 ?","dec",w=0.14,h=0.058)
arrow([(c4,R[1]-h2),(c4,R[2]+h2)]); arrow([(c3+W_/2-0.006,R[5]),(c4-W_/2,R[5])]); arrow([(c4,R[5]-h2),(c4,R[6]+0.029)]); arrow([(c4,R[6]-0.029),(c4,R[7]+0.029)],"yes",(c4+0.016,R[6]-0.037))
arrow([(c4+W_/2,R[2]),(0.981,R[2]),(0.981,R[7]),(c4+0.07,R[7])]); arrow([(c2+W_/2,R[4]+0.016),(X0[2]-0.012,R[4]+0.016),(X0[2]-0.012,(R[1]+R[2])/2),(X0[3]-0.012,(R[1]+R[2])/2),(X0[3]-0.012,R[2]),(c4-W_/2,R[2])],col="#8a8a8a",ls=(0,(3,2)))
yo=R[9]+0.012
node(0.640,yo,"NO OFFSET\nmore carbon than concrete","out",w=0.165); node(0.822,yo,"WIN–WIN\ncheaper,\nless carbon","out",w=0.104,h=0.06); node(0.935,yo,"PAY TO\nABATE","out",w=0.09,h=0.06)
arrow([(c4-0.07,R[6]),(0.752,R[6]),(0.752,yo+0.052),(0.640,yo+0.052),(0.640,yo+h2)],"no",(c4-0.085,R[6]+0.010))
arrow([(c4-0.07,R[7]),(0.790,R[7]),(0.790,yo+0.03)],"yes",(0.790+0.016,R[7]-0.03)); arrow([(c4,R[7]-0.029),(c4,R[8]),(0.935,R[8]),(0.935,yo+0.03)],"no",(0.935+0.013,R[8]-0.02))
# legend of symbols (free area, lower left)
lx,ly=X0[0]+0.012,R[8]+0.03
bg.text(lx,ly+0.03,"SYMBOLS",fontsize=5.8,color=MUT,fontweight="bold")
for k,(kind,lab) in enumerate([("proc","process / calculation"),("data","data or intermediate result"),("dec","check / decision"),("out","reported result")]):
    y=ly-0.028*k; node(lx+0.022,y,"",kind,w=0.04,h=0.017 if kind!="dec" else 0.022); bg.text(lx+0.052,y,lab,fontsize=5.8,color=INK,va="center")
bg.plot([lx-0.004,lx+0.03],[ly-0.028*4,ly-0.028*4],color="#8a8a8a",lw=0.8,ls=(0,(3,2))); bg.text(lx+0.052,ly-0.028*4,"secondary data flow",fontsize=5.8,color=INK,va="center")
bg.text(c2,R[7]+0.012,"Loop over 6 materials, 3 climates\nand 2 input sets (36 runs)",fontsize=5.8,color=MUT,ha="center",va="center",style="italic")
# extension runs (revision 2): insulated benchmark, free-running comfort, 2050 weather
node(c2,R[8],"Extension runs: +25 mm EPS\nbenchmark, free-running,\n2050 morphed weather","proc",h=0.058)
node(c2,R[9]+0.012,"Overheating degree-hours\nand 2050 demand","out")
arrow([(c2,R[7]-0.012),(c2,R[8]+0.029)]); arrow([(c2,R[8]-0.029),(c2,R[9]+0.012+h2)])
arrow([(c2+W_/2,R[8]),(X0[2]-0.012,R[8]),(X0[2]-0.012,R[7]),(c3-W_/2,R[7])],col="#8a8a8a",ls=(0,(3,2)))
plt.savefig(f"{OUT}/nat_framework.png",dpi=350,facecolor="white"); __import__("shutil").copy(f"{OUT}/nat_framework.png",f"{DST}/nat_framework.png"); print("framework saved")
