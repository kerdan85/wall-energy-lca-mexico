#!/usr/bin/env python3
"""Revision analysis (post peer review): final-energy conversion, discounted cost with
freight, offset decomposition, equal-thickness and U-vs-inertia checks, scenario and
one-at-a-time sensitivity on the decision variables, and end-to-end paired Monte-Carlo.
Writes robust_results.json and prints every number quoted in the manuscript."""
import os
HERE=os.path.dirname(os.path.abspath(__file__))
OUT=HERE; DST=os.path.normpath(os.path.join(HERE,"..","figures")); os.makedirs(DST,exist_ok=True)
import json, numpy as np
import sim_engine as E


CLIM=["CDMX","Warm-subhumid","Hot-arid"]
REF="Concrete (ref.)"
MATS=list(E.MAT.keys()); ALT=[m for m in MATS if m!=REF]
BASEMAT=dict(E.MAT)

# ---------------- base parameters ----------------
Af=73.45; Aw=176.53-4.68-1.87; T=50   # opaque wall area (gross minus glazing and door of the EnergyPlus model)
COP_H=1.0; COP_C=3.0
F_GRID=0.42; CE=3.5; R=0.05; E_T=0.10; C_T=1.0; FX=19.0
PRICE={"Concrete (ref.)":(13,12.5,240),"Adobe-type block":(10,12.5,240),"Volcanic stone (recinto)":(14,12.5,240),
       "Tepetate ashlar":(12,10.0,240),"SBC block (solid)":(20,12.5,240),"SBC block (hollow)":(24,12.5,240)}
A1A3={"Concrete (ref.)":41.0,"Adobe-type block":31.6,"Volcanic stone (recinto)":3.8,
      "Tepetate ashlar":5.2,"SBC block (solid)":53.5,"SBC block (hollow)":42.5}
CV={"Concrete (ref.)":36.3,"Adobe-type block":25.8,"Volcanic stone (recinto)":24.5,
    "Tepetate ashlar":26.1,"SBC block (solid)":24.2,"SBC block (hollow)":26.8}
import lca_inputs
A1A3,CV,LCA_SOURCE=lca_inputs.lca(A1A3,CV)
MASS={m:BASEMAT[m][1]*BASEMAT[m][2] for m in MATS}          # kg/m2 = thickness*rho
DIST={"CDMX":{"Concrete (ref.)":40,"Adobe-type block":20,"Volcanic stone (recinto)":70,"Tepetate ashlar":70,"SBC block (solid)":1637,"SBC block (hollow)":1637},
      "Warm-subhumid":{"Concrete (ref.)":40,"Adobe-type block":20,"Volcanic stone (recinto)":1297,"Tepetate ashlar":1297,"SBC block (solid)":329,"SBC block (hollow)":329},
      "Hot-arid":{"Concrete (ref.)":40,"Adobe-type block":20,"Volcanic stone (recinto)":1900,"Tepetate ashlar":1900,"SBC block (solid)":3521,"SBC block (hollow)":3521}}
UTAB={"Concrete (ref.)":3.00,"Adobe-type block":2.44,"Volcanic stone (recinto)":3.29,"Tepetate ashlar":2.21,"SBC block (solid)":2.59,"SBC block (hollow)":1.99}

def pvf(r,n=T): return n if r==0 else (1-(1+r)**(-n))/r
def sim(U,tk,rho,cp,c):
    E.MAT["_x"]=(U,tk,rho,cp); r=E.simulate("_x",c); del E.MAT["_x"]; return float(r["heat"]),float(r["cool"])
def price(m): b,n,a=PRICE[m]; return b*n+a

# ---------------- simulations ----------------
HC={c:{m:sim(*BASEMAT[m],c) for m in MATS} for c in CLIM}
HCT={c:{m:sim(UTAB[m],*BASEMAT[m][1:],c) for m in MATS} for c in CLIM}
HC_5R1C={c:dict(HC[c]) for c in CLIM}
_EP,_EPT=lca_inputs.energyplus()
ENERGY_SOURCE="5R1C"
if _EP:
    HC={c:{m:tuple(_EP[c][m]) for m in MATS} for c in CLIM}; ENERGY_SOURCE="EnergyPlus"
    if _EPT: HCT={c:{m:tuple(_EPT[c][m]) for m in MATS} for c in CLIM}
# derivatives wrt ln U and ln kappa (central differences): EnergyPlus runs when available, else 5R1C
_PT=lca_inputs.energyplus_perturbations() if _EP else None
DERIV_SOURCE="EnergyPlus" if _PT else "5R1C"
DER={c:{} for c in CLIM}
for c in CLIM:
    for m in MATS:
        U,tk,rho,cp=BASEMAT[m]
        if _PT:
            P=_PT[c][m]; up,um,kp,km=P["U+10"],P["U-10"],P["cp+30"],P["cp-30"]
        else:
            up=sim(U*1.1,tk,rho,cp,c); um=sim(U*0.9,tk,rho,cp,c)
            kp=sim(U,tk,rho,cp*1.3,c); km=sim(U,tk,rho,cp*0.7,c)
        DER[c][m]=dict(hU=(up[0]-um[0])/0.2,cU=(up[1]-um[1])/0.2,hK=(kp[0]-km[0])/0.6,cK=(kp[1]-km[1])/0.6,
                       up=up,um=um,kp=kp,km=km)

def _shift(hc,c,m):
    """Carry a 5R1C perturbation over to the EnergyPlus base (no-op when the 5R1C results are the base)."""
    return tuple(max(0.0,v+HC[c][m][i]-HC_5R1C[c][m][i]) for i,v in enumerate(hc))
if not _PT:
    for c in CLIM:
        for m in MATS:
            for k in ("up","um","kp","km"): DER[c][m][k]=_shift(DER[c][m][k],c,m)

# ---------------- city-cast solid SBC block ----------------
# Same block as the solid SBC (same energy, production carbon and price), but cast in each city:
# only the dried sargassum (35% of the block mass) travels from the coast; cement and sand are
# local (40 km, as for concrete). Implemented as an effective haul distance on the full block mass.
SOLID="SBC block (solid)"; CC="SBC block (solid, city-cast)"; SARG_FRAC=0.35
for c in CLIM:
    HC[c][CC]=HC[c][SOLID]; HCT[c][CC]=HCT[c][SOLID]; DER[c][CC]=DER[c][SOLID]
    DIST[c][CC]=SARG_FRAC*DIST[c][SOLID]+(1-SARG_FRAC)*DIST[c][REF]
A1A3[CC]=A1A3[SOLID]; CV[CC]=CV[SOLID]; MASS[CC]=MASS[SOLID]; PRICE[CC]=PRICE[SOLID]
ORIG_ALT=list(ALT); ALT=ALT+[CC]; MATS_X=MATS+[CC]

# ---------------- insulated benchmark: concrete block + 25 mm EPS external insulation ----------------
# Same block as the reference with an external insulation system (EPS 25 mm, adhesive, base coat, mesh).
INS="Concrete + EPS (insulated)"; INS_COST=280.0      # MXN/m2 installed system (210-400 range, MC below)
EPS_A13,EPS_CV,EPS_SOURCE=lca_inputs.lca_extra("EPS insulation system (25 mm)",6.0,30.0)
EPS_MASS=0.025*15+9.0+0.16                             # kg/m2: EPS, mortar, mesh
_INS=lca_inputs.insulated(INS)
if _INS:
    for c in CLIM:
        P=_INS[c]; HC[c][INS]=P["measured"]; HCT[c][INS]=P["tabulated"]
        up,um,kp,km=P["U+10"],P["U-10"],P["cp+30"],P["cp-30"]
        DER[c][INS]=dict(hU=(up[0]-um[0])/0.2,cU=(up[1]-um[1])/0.2,hK=(kp[0]-km[0])/0.6,cK=(kp[1]-km[1])/0.6,up=up,um=um,kp=kp,km=km)
        DIST[c][INS]=DIST[c][REF]
    A1A3[INS]=A1A3[REF]+EPS_A13
    CV[INS]=100*np.sqrt((CV[REF]/100*A1A3[REF])**2+(EPS_CV/100*EPS_A13)**2)/A1A3[INS]
    MASS[INS]=MASS[REF]+EPS_MASS
    PRICE[INS]=(PRICE[REF][0],PRICE[REF][1],PRICE[REF][2]+INS_COST)
    ALT=ALT+[INS]; MATS_X=MATS_X+[INS]
print("insulated benchmark:",bool(_INS)," EPS system A1-A3",EPS_A13,"kg/m2 (",EPS_SOURCE,")")

# ---------------- biogenic carbon stored in the sargassum (reported separately) ----------------
# EN 15804+A2 (-1/+1): uptake is credited in A1-A3 and released at end of life, so the base case
# (A1-A4 + B6, no end of life) treats it as neutral. Reported here as a temporary-storage indicator.
C_FRAC=(0.30,0.24,0.36)                       # carbon content of dried pelagic sargassum, kg C per kg DW (central, low, high)
BIO={m:tuple(SARG_FRAC*MASS[m]*cf*44/12 for cf in C_FRAC) for m in ("SBC block (solid)","SBC block (hollow)")}   # kg CO2 per m2 wall

def efin(h,c_,cop_c=COP_C,cop_h=COP_H): return h/cop_h+c_/cop_c

def evaluate(c,m,hc=None,hcref=None,a13=None,a13ref=None,e_t=E_T,f=F_GRID,cop_c=COP_C,ce=CE,r=R,c_t=C_T,
             mass=None,dist=None,pr=None,prref=None,cond=1.0,haul_frac=1.0):
    hc=hc or HC[c][m]; hcref=hcref or HC[c][REF]
    a13=A1A3[m] if a13 is None else a13; a13ref=A1A3[REF] if a13ref is None else a13ref
    mass=MASS[m] if mass is None else mass; dist=DIST[c][m] if dist is None else dist
    pr=price(m) if pr is None else pr; prref=price(REF) if prref is None else prref
    dE=(efin(*hcref,cop_c)-efin(*hc,cop_c))*cond                 # kWh/m2/yr final electricity saved
    tkm=mass/1000*dist*haul_frac; tkmref=MASS[REF]/1000*DIST[c][REF]
    op=dE*Af*T*f; prod=(a13ref-a13)*Aw; tr=(tkmref-tkm)*e_t*Aw
    dcap=(pr-prref)*Aw+(tkm-tkmref)*c_t*Aw
    ann=dE*Af*ce
    dC=dcap-ann*pvf(r)
    # discounted payback
    if dcap<=0 and ann>=0: pb=0.0
    elif ann<=0: pb=np.inf
    else:
        pb=np.inf
        for n in range(1,T+1):
            if ann*pvf(r,n)>=dcap: pb=n; break
    return dict(dE=dE,op=op/1000,prod=prod/1000,tr=tr/1000,dCO2=(op+prod+tr)/1000,dcap=dcap,ann=ann,dC=dC,pb=pb,
                simple=(dcap/ann if ann>0 and dcap>0 else (0.0 if dcap<=0 and ann>=0 else np.inf)))

BASE={c:{m:evaluate(c,m) for m in ALT} for c in CLIM}

# operational share (dwelling conditioning vs wall embodied incl. transport)
SHARE={}
for c in CLIM:
    for m in MATS_X:
        op=efin(*HC[c][m])*Af*T*F_GRID; emb=(A1A3[m]+MASS[m]/1000*DIST[c][m]*E_T)*Aw
        SHARE[(c,m)]=op/(op+emb)

# ---------------- scenarios ----------------
HC2050=lca_inputs.climate2050()
SCEN={c:{} for c in CLIM}
for c in CLIM:
    for m in ALT:
        s={}
        s["base"]=BASE[c][m]
        s["grid_decarb"]=evaluate(c,m,f=F_GRID*0.75)             # linear decline to 50% by year 50
        s["no_cond"]=evaluate(c,m,cond=0.0)
        s["half_cond"]=evaluate(c,m,cond=0.5)
        s["cop1"]=evaluate(c,m,cop_c=1.0)
        s["local_sbc"]=evaluate(c,m,haul_frac=(0.35 if ("SBC" in m and m!=CC) else 1.0))
        s["bio_storage"]=dict(s["base"],dCO2=s["base"]["dCO2"]+(BIO.get(m if m!=CC else SOLID,(0,0,0))[0]*Aw/1000))
        s["tariff_low"]=evaluate(c,m,ce=1.2)
        s["r0"]=evaluate(c,m,r=0.0); s["r10"]=evaluate(c,m,r=0.10)
        s["no_freight_cost"]=evaluate(c,m,c_t=0.0)
        if HC2050:
            mm=SOLID if m==CC else m
            s["climate_2050"]=evaluate(c,m,hc=HC2050[c][mm],hcref=HC2050[c][REF])   # whole life in the 2041-2060 climate
            s["climate_mid"]=evaluate(c,m,hc=tuple((a+b)/2 for a,b in zip(HC[c][m],HC2050[c][mm])),
                                      hcref=tuple((a+b)/2 for a,b in zip(HC[c][REF],HC2050[c][REF])))   # linear warming over the life
        SCEN[c][m]=s

# equal thickness: tepetate at 0.12 m (k = 0.40) ; and U-only (reference areal heat capacity)
EQ={}
U12=1/(0.17+0.12/0.40)
for c in CLIM:
    hc=tuple(_PT[c]["Tepetate ashlar"]["equal_thickness"]) if _PT else _shift(sim(U12,0.12,1500,1000,c),c,"Tepetate ashlar")
    EQ[c]=dict(U=U12,hc=hc,ev=evaluate(c,"Tepetate ashlar",hc=hc,mass=180.0))
UONLY={c:{} for c in CLIM}
for c in CLIM:
    for m in ORIG_ALT:
        U,tk,rho,cp=BASEMAT[m]; rr,cc=BASEMAT[REF][2],BASEMAT[REF][3]
        if _PT:   # alternative U on the reference wall; remainder = mass, thickness and colour
            hc=_PT[c][m]["U_only"]; tot=sum(HC[c][REF])-sum(HC[c][m]); uo=sum(HC[c][REF])-sum(hc)
        else:
            hc=sim(U,0.12,rr,cc,c)
            tot=sum(HC_5R1C[c][REF])-sum(HC_5R1C[c][m]); uo=sum(HC_5R1C[c][REF])-sum(hc)
        UONLY[c][m]=dict(total=tot,U_part=uo,k_part=tot-uo)

# ---------------- one-at-a-time sensitivity on dCO2 ----------------
def q(m,p):   # lognormal quantile for A1-A3
    from statistics import NormalDist
    s=np.sqrt(np.log(1+(CV[m]/100)**2)); return float(np.exp(np.log(A1A3[m])-s*s/2+s*NormalDist().inv_cdf(p)))
def qe(p):   # lognormal quantile of the EPS system production carbon
    from statistics import NormalDist
    se=np.sqrt(np.log(1+(EPS_CV/100)**2)); return float(np.exp(np.log(EPS_A13)-se*se/2+se*NormalDist().inv_cdf(p)))
OAT={c:{} for c in CLIM}
for c in CLIM:
    for m in ALT:
        b=BASE[c][m]["dCO2"]; d=DER[c][m]; dr=DER[c][REF]; L=[]
        L.append(("Wall $U$ ±10%",evaluate(c,m,hc=d["um"])["dCO2"]-b,evaluate(c,m,hc=d["up"])["dCO2"]-b))
        L.append(("Reference $U$ ±10%",evaluate(c,m,hcref=dr["um"])["dCO2"]-b,evaluate(c,m,hcref=dr["up"])["dCO2"]-b))
        L.append(("Heat capacity ±30%",evaluate(c,m,hc=d["km"])["dCO2"]-b,evaluate(c,m,hc=d["kp"])["dCO2"]-b))
        if m==INS:   # the insulated wall contains the reference block: only the EPS system is its own production
            L.append(("Production carbon P5–P95",evaluate(c,m,a13=A1A3[REF]+qe(0.95))["dCO2"]-b,evaluate(c,m,a13=A1A3[REF]+qe(0.05))["dCO2"]-b))
            L.append(("Reference production P5–P95",0.0,0.0))
        else:
            L.append(("Production carbon P5–P95",evaluate(c,m,a13=q(m,0.95))["dCO2"]-b,evaluate(c,m,a13=q(m,0.05))["dCO2"]-b))
            L.append(("Reference production P5–P95",evaluate(c,m,a13ref=q(REF,0.05))["dCO2"]-b,evaluate(c,m,a13ref=q(REF,0.95))["dCO2"]-b))
        L.append(("Freight factor 0.06–0.15",evaluate(c,m,e_t=0.15)["dCO2"]-b,evaluate(c,m,e_t=0.06)["dCO2"]-b))
        L.append(("Grid factor 0.25–0.42",evaluate(c,m,f=0.25)["dCO2"]-b,0.0))
        L.append(("Cooling COP 2.5–4",evaluate(c,m,cop_c=4.0)["dCO2"]-b,evaluate(c,m,cop_c=2.5)["dCO2"]-b))
        OAT[c][m]=L

# ---------------- end-to-end paired Monte-Carlo ----------------
N=10000; rng=np.random.default_rng(2026)
MCR={c:{} for c in CLIM}
uU={m:rng.normal(1,0.05,N) for m in MATS}
uK={m:rng.uniform(0.7,1.3,N) for m in MATS}
zc=rng.standard_normal(N)                                    # shared background (cement/energy) component
g={}
for m in MATS:
    s=np.sqrt(np.log(1+(CV[m]/100)**2)); rho=0.5 if m in ("Concrete (ref.)","SBC block (solid)","SBC block (hollow)","Adobe-type block") else 0.0
    z=np.sqrt(rho)*zc+np.sqrt(1-rho)*rng.standard_normal(N)
    g[m]=np.exp(np.log(A1A3[m])-s*s/2+s*z)
for dct in (uU,uK,g): dct[CC]=dct[SOLID]
eT=rng.triangular(0.06,0.10,0.15,N); cT=rng.triangular(0.7,1.0,1.5,N); cop=rng.triangular(2.5,3.0,4.0,N)
fg=rng.uniform(0.25,0.42,N); ce=rng.triangular(1.2,3.5,4.5,N); rr=rng.uniform(0.03,0.08,N)
pf={m:rng.normal(1,0.10,N) for m in MATS}; pf[CC]=pf[SOLID]; pf[INS]=pf[REF]
PV=(1-(1+rr)**(-T))/rr
if INS in ALT:   # drawn last so that the samples of the other walls are unchanged
    uU[INS]=rng.normal(1,0.05,N); uK[INS]=rng.uniform(0.7,1.3,N)
    se=np.sqrt(np.log(1+(EPS_CV/100)**2)); g[INS]=g[REF]+np.exp(np.log(EPS_A13)-se*se/2+se*rng.standard_normal(N))
    ins_cost=rng.uniform(210,400,N)
def dem(c,m):
    d=DER[c][m]; h0,c0=HC[c][m]
    h=np.clip(h0+d["hU"]*(uU[m]-1)+d["hK"]*(uK[m]-1),0,None); cc=np.clip(c0+d["cU"]*(uU[m]-1)+d["cK"]*(uK[m]-1),0,None)
    return h/COP_H+cc/cop
for c in CLIM:
    eref=dem(c,REF)
    for m in ALT:
        dE=eref-dem(c,m)
        tkm=MASS[m]/1000*DIST[c][m]; tkr=MASS[REF]/1000*DIST[c][REF]
        dco2=(dE*Af*T*fg+(g[REF]-g[m])*Aw+(tkr-tkm)*eT*Aw)/1000
        blk=lambda mm: PRICE[mm][0]*PRICE[mm][1]*pf[mm]+(PRICE[REF][2]+ins_cost if mm==INS else PRICE[mm][2])
        dC=(blk(m)-blk(REF))*Aw+(tkm-tkr)*cT*Aw-dE*Af*ce*PV
        MCR[c][m]=dict(p5=float(np.percentile(dco2,5)),p50=float(np.percentile(dco2,50)),p95=float(np.percentile(dco2,95)),
                       pco2=float(np.mean(dco2>0)),pcost=float(np.mean(dC<0)),pww=float(np.mean((dco2>0)&(dC<0))),
                       c5=float(np.percentile(dC,5)),c50=float(np.percentile(dC,50)),c95=float(np.percentile(dC,95)))
# linearisation check: full model at +2 sigma U
chk=[]
for c in CLIM:
    for m in MATS:
        U,tk,rho,cp=BASEMAT[m]; d=DER[c][m]
        if _PT: full=sum(_PT[c][m]["check_U+10_cp+20"]); lin=sum(HC[c][m])+(d["hU"]+d["cU"])*0.1+(d["hK"]+d["cK"])*0.2
        else:   full=sum(sim(U*1.1,tk,rho,cp*1.2,c)); lin=sum(HC_5R1C[c][m])+(d["hU"]+d["cU"])*0.1+(d["hK"]+d["cK"])*0.2
        chk.append(abs(full-lin)/full*100)
# demand uncertainty band from U (±10%) for figure
BAND={c:{m:(sum(DER[c][m]["um"]),sum(DER[c][m]["up"])) for m in MATS_X} for c in CLIM}
# MC table for A1-A3 consistent with the violin figure (seed 7, n=500, same order)
MCF={m:(A1A3[m],CV[m]) for m in sorted(A1A3,key=lambda k:A1A3[k]) if m in MATS}
r7=np.random.default_rng(7); TAB7={}
for m,(mu,cv) in MCF.items():
    s=np.sqrt(np.log(1+(cv/100)**2)); x=r7.lognormal(np.log(mu)-s*s/2,s,500); TAB7[m]=[float(v) for v in np.percentile(x,[5,50,95])]

# ---------------- free-running comfort (EN 16798-1 Cat. II) ----------------
COMFORT=lca_inputs.comfort()
# ---------------- programme scale: national social-housing programme 2025-2030 ----------------
N_PROG=1.8e6                                           # new dwellings (Vivienda para el Bienestar)
SCALE={c:{m:dict(dCO2_Mt=BASE[c][m]["dCO2"]*N_PROG/1e6,dC_bnUSD=BASE[c][m]["dC"]*N_PROG/FX/1e9) for m in ALT} for c in CLIM}

json.dump(dict(COMFORT=COMFORT,SCALE=SCALE,N_PROG=N_PROG,INS=INS,EPS_A13=EPS_A13,EPS_CV=EPS_CV,EPS_SOURCE=EPS_SOURCE,INS_COST=INS_COST,HC2050=HC2050,LCA_SOURCE=LCA_SOURCE,ENERGY_SOURCE=ENERGY_SOURCE,DERIV_SOURCE=DERIV_SOURCE,LIN_ERR=max(chk),CV=CV,A1A3=A1A3,HC=HC,HCT=HCT,BASE=BASE,SCEN=SCEN,EQ=EQ,UONLY=UONLY,OAT=OAT,MC=MCR,BAND=BAND,TAB7=TAB7,
               SHARE={f"{c}|{m}":v for (c,m),v in SHARE.items()},MASS=MASS,DIST=DIST,BIO=BIO,BIO_DWELLING={m:[v*Aw/1000 for v in t] for m,t in BIO.items()},C_FRAC=C_FRAC,AW=Aw),
          open(f"{OUT}/robust_results.json","w"),indent=1,default=float)

# ---------------- report ----------------
sh=lambda m:m.split(" (")[0][:13]
print("SOURCES  production carbon:",LCA_SOURCE," | conditioning needs:",ENERGY_SOURCE," | derivatives:",DERIV_SOURCE)
print("PVF(5%,50)=",round(pvf(R),2)," linearisation max err %",round(max(chk),2))
for c in CLIM:
    print(f"\n=== {c} === thermal heat/cool, total, tab total, err%, final elec, share")
    for m in MATS:
        h,cc=HC[c][m]; tt=sum(HCT[c][m])
        print(f" {sh(m):13s} H{h:6.1f} C{cc:6.1f} tot{h+cc:6.1f} tab{tt:6.1f} err{100*(tt-h-cc)/(h+cc):+5.0f}%  E{efin(h,cc):6.1f}  band{BAND[c][m][0]:6.1f}-{BAND[c][m][1]:6.1f} share{100*SHARE[(c,m)]:5.1f}")
    print("  material      dE    op   prod    tr  dCO2 | dcap     ann     dC   pb(disc) simple | MC p5 p50 p95 P(co2>0) P(dC<0) P(ww)")
    for m in ALT:
        b=BASE[c][m]; k=MCR[c][m]
        print(f"  {sh(m):13s}{b['dE']:5.1f}{b['op']:6.1f}{b['prod']:6.1f}{b['tr']:6.1f}{b['dCO2']:6.1f} |{b['dcap']:8.0f}{b['ann']:7.0f}{b['dC']:9.0f} {b['pb']:5} {b['simple']:6.1f} | {k['p5']:5.1f}{k['p50']:6.1f}{k['p95']:6.1f}  {k['pco2']:.2f} {k['pcost']:.2f} {k['pww']:.2f}  dC[{k['c5']/1000:.0f},{k['c95']/1000:.0f}]k")
    print("  scenarios dCO2: base | grid | nocond | half | cop1 | localSBC || dC(k): base | tariff1.2 | r0 | r10 | nofreight")
    for m in ALT:
        s=SCEN[c][m]
        print(f"  {sh(m):13s}"+"".join(f"{s[k]['dCO2']:7.1f}" for k in ["base","grid_decarb","no_cond","half_cond","cop1","local_sbc"])+" ||"+"".join(f"{s[k]['dC']/1000:8.1f}" for k in ["base","tariff_low","r0","r10","no_freight_cost"]))
    print("  equal-thickness tepetate: U %.2f demand %.1f dCO2 %.1f dC %.0f"%(EQ[c]["U"],sum(EQ[c]["hc"]),EQ[c]["ev"]["dCO2"],EQ[c]["ev"]["dC"]))
    print("  U-only split (thermal saving total / due to U / due to kappa):",{sh(m):(round(v['total'],1),round(v['U_part'],1),round(v['k_part'],1)) for m,v in UONLY[c].items()})
print("\nA1-A3 P5/P50/P95 (seed 7):",{sh(m):[round(x,1) for x in v] for m,v in TAB7.items()})
print("share range",round(100*min(SHARE.values()),1),round(100*max(SHARE.values()),1))
print("biogenic CO2 stored (kg/m2 central,low,high):",{k:[round(x,1) for x in v] for k,v in BIO.items()},"| per dwelling t:",{k:[round(x*Aw/1000,1) for x in v] for k,v in BIO.items()})
for c in CLIM: print(c,"offset with storage credit:",{m[:16]:round(SCEN[c][m]["bio_storage"]["dCO2"],1) for m in ALT if "SBC" in m})
