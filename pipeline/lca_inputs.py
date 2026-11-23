"""Input tables. If the files below exist in pipeline/inputs they replace the built-in values;
if they do not, the built-in values are used and a warning is printed.

inputs/lca_a1a3.csv        written by brightway/brightway_acv_paper.py
    material,gwp_mean,gwp_cv_pct,gwp,water,acidification,eutrophication,human_toxicity,fossil
inputs/energyplus_results.csv   written by ../energyplus/run_ep_all.py (also energyplus_perturbations.csv)
    city,material,u_set,heating_kwh_m2,cooling_kwh_m2      (u_set = measured or tabulated)
"""
import os, csv
HERE=os.path.dirname(os.path.abspath(__file__)); INP=os.path.join(HERE,"inputs")
MATS=["Concrete (ref.)","Adobe-type block","Volcanic stone (recinto)","Tepetate ashlar","SBC block (solid)","SBC block (hollow)"]
SHORT={"Concrete (ref.)":"Concrete","Adobe-type block":"Adobe","Volcanic stone (recinto)":"Volcanic stone","Tepetate ashlar":"Tepetate","SBC block (solid)":"SBC solid","SBC block (hollow)":"SBC hollow"}
CITIES=["CDMX","Warm-subhumid","Hot-arid"]
CITYALIAS={"mexico city":"CDMX","cdmx":"CDMX","merida":"Warm-subhumid","mérida":"Warm-subhumid","warm-subhumid":"Warm-subhumid","hermosillo":"Hot-arid","hot-arid":"Hot-arid"}

def _rows(name):
    p=os.path.join(INP,name)
    if not os.path.exists(p): return None
    with open(p,newline="",encoding="utf-8-sig") as f:
        return [r for r in csv.DictReader(f) if (r.get("material") or "").strip() and not (r.get("material") or "").startswith("#")]

def lca(default_a1a3,default_cv):
    """Return (A1A3, CV, source) keyed by the long material names."""
    rows=_rows("lca_a1a3.csv")
    if not rows:
        print("[lca_inputs] inputs/lca_a1a3.csv not found -> using BUILT-IN PLACEHOLDER production carbon"); return dict(default_a1a3),dict(default_cv),"placeholder"
    a,c={},{}
    for r in rows:
        m=r["material"].strip()
        if m in MATS: a[m]=float(r["gwp_mean"]); c[m]=float(r["gwp_cv_pct"])
    missing=[m for m in MATS if m not in a]
    if missing: raise ValueError(f"inputs/lca_a1a3.csv lacks: {missing}")
    print("[lca_inputs] production carbon read from inputs/lca_a1a3.csv (Brightway)"); return a,c,"brightway"

def multicat(default_absd):
    """Return {short name:[gwp,water,acid,eutro,tox,fossil]} for the multi-criteria figure."""
    rows=_rows("lca_a1a3.csv")
    if not rows: return default_absd
    out={}
    for r in rows:
        m=r["material"].strip()
        if m in MATS: out[SHORT[m]]=[float(r[k]) for k in ("gwp","water","acidification","eutrophication","human_toxicity","fossil")]
    return out if len(out)==6 else default_absd

def energyplus():
    """Return ({city:{material:(heat,cool)}} measured, same tabulated) or (None,None)."""
    rows=_rows("energyplus_results.csv")
    if not rows: 
        print("[lca_inputs] inputs/energyplus_results.csv not found -> using the 5R1C model results"); return None,None
    meas={c:{} for c in CITIES}; tab={c:{} for c in CITIES}
    for r in rows:
        c=CITYALIAS.get(r["city"].strip().lower()); m=r["material"].strip()
        if c is None or m not in MATS or not r["heating_kwh_m2"].strip(): continue
        (meas if r["u_set"].strip().lower().startswith("meas") else tab)[c][m]=(float(r["heating_kwh_m2"]),float(r["cooling_kwh_m2"]))
    full=lambda d:all(len(d[c])==6 for c in CITIES)
    if not full(meas): print("[lca_inputs] energyplus_results.csv incomplete for measured U -> using the 5R1C model results"); return None,None
    print("[lca_inputs] conditioning needs read from inputs/energyplus_results.csv (EnergyPlus)")
    return meas,(tab if full(tab) else None)

def energyplus_perturbations():
    """Return {city:{material:{case:(heat,cool)}}} from inputs/energyplus_perturbations.csv, or None.
    Cases: U+10, U-10, cp+30, cp-30, check_U+10_cp+20, U_only (alternatives), equal_thickness (tepetate)."""
    rows=_rows("energyplus_perturbations.csv")
    if not rows: return None
    out={c:{} for c in CITIES}
    for r in rows:
        c=CITYALIAS.get(r["city"].strip().lower()); m=r["material"].strip()
        if c is None or m not in MATS: continue
        out[c].setdefault(m,{})[r["case"].strip()]=(float(r["heating_kwh_m2"]),float(r["cooling_kwh_m2"]))
    need={"U+10","U-10","cp+30","cp-30"}
    if not all(need<=set(out[c].get(m,{})) for c in CITIES for m in MATS):
        print("[lca_inputs] energyplus_perturbations.csv incomplete -> derivatives from the 5R1C model"); return None
    print("[lca_inputs] derivatives and checks read from inputs/energyplus_perturbations.csv (EnergyPlus)")
    return out
