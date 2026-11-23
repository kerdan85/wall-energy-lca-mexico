# -*- coding: utf-8 -*-
"""
Production carbon (modules A1-A3) of 1 m2 of each wall - Brightway 2.5 + ecoinvent 3.9.1 cut-off.

THIS SCRIPT NEEDS AN ECOINVENT LICENCE. Everything else in the repository runs without it,
because the results of this script are already stored in ../inputs/lca_a1a3.csv.
See the README, section "Re-running the LCA (ecoinvent licence)".

What it does
  * foreground: wall masses per m2 (density x as-built thickness, Table 3 of the paper) and the
    mix of each block, linked to ecoinvent background datasets (PROXY, SHARED below);
  * deterministic LCIA in six categories and a 1,000-iteration Monte Carlo on climate change;
  * transport to site (A4) and operation (B6) are NOT here: ../mk_robust.py adds them city by city;
  * biogenic carbon is neutral here; the storage in the sargassum is reported separately (mk_robust.py).

Outputs (in ../inputs/)
  lca_a1a3.csv              read by ../run_all.py  (aggregated results: can be shared)
  lca_brightway_full.xlsx   inventory, contributions, MC samples (contains ecoinvent-derived
                            process detail: keep it private, it is excluded by .gitignore)

Run from a terminal in the 'brightway' conda environment (environment-brightway.yml):
  python brightway_acv_paper.py --setup        # first time: creates the project, imports ecoinvent
  python brightway_acv_paper.py --search "concrete block"   # browse proxies
  python brightway_acv_paper.py                # the run (about 10 min with scikit-umfpack, hours without)
  python brightway_acv_paper.py --only "EPS insulation system (25 mm)"   # one item; other rows kept
  python brightway_acv_paper.py --project MY_PROJECT ...                 # use an existing project
In Spyder: runfile("brightway_acv_paper.py", args='--only "EPS insulation system (25 mm)"')
"""
import math, sys, csv
from pathlib import Path
import numpy as np
import pandas as pd
import bw2data as bd
import bw2calc as bc
try:
    import bw2io as bi
except Exception:
    bi = None

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "inputs"; OUT.mkdir(exist_ok=True)

# Change PROJECT / EI_DB if your Brightway project or ecoinvent database has another name
# (list them with: import bw2data as bd; print(bd.projects); bd.projects.set_current("x"); print(bd.databases)).
CONFIG = dict(PROJECT="sectei_walls_lca", FG_DB="fg_walls_energy_paper",
              EI_DB="ecoinvent-3.9.1-cutoff", BIOSPHERE="ecoinvent-3.9.1-biosphere",
              EI_VERSION="3.9.1", N_MONTECARLO=1000, SEED=42)   # 1,000 iterations, as in the paper
if "--project" in sys.argv:   # use an existing Brightway project, e.g. --project SECTEI_ACV_5065c25
    CONFIG["PROJECT"] = sys.argv[sys.argv.index("--project") + 1]

# ---------------------------------------------------------------------------------------------
# Walls: mass per m2 = density x thickness, exactly as in Table 3 of the manuscript.
# The keys are the names the Python pipeline expects - do not change them.
# ---------------------------------------------------------------------------------------------
WALLS = {
    "Concrete (ref.)":          dict(mass=144.0, kind="proxy"),
    "Adobe-type block":         dict(mass=192.0, kind="earth"),
    "Volcanic stone (recinto)": dict(mass=168.0, kind="proxy"),
    "Tepetate ashlar":          dict(mass=300.0, kind="proxy"),
    "SBC block (solid)":        dict(mass=150.0, kind="sbc"),
    "SBC block (hollow)":       dict(mass=135.0, kind="sbc"),
    # insulation layer of the insulated benchmark (added to the concrete wall by ../mk_robust.py)
    "EPS insulation system (25 mm)": dict(mass=None, kind="eps"),
}

# Background proxies (ecoinvent 3.9.1 names; other versions may rename them: check with --search).
#   - Concrete: the tested block is a 1,200 kg/m3 lightweight-aggregate block. "concrete production,
#     25MPa" is normal-weight concrete; look for a lightweight concrete BLOCK dataset and prefer it.
#   - Recinto and tepetate: quarried and cut stone; "gravel production, crushed" is only a proxy.
#     Look for a natural/dimension stone dataset (quarrying + sawing).
PROXY = {
    "Concrete (ref.)":          dict(name="concrete production, 25MPa", product="concrete, 25MPa", loc="RoW", density=2300.0),
    "Volcanic stone (recinto)": dict(name="gravel production, crushed", product="gravel, crushed", loc="RoW", density=None),
    "Tepetate ashlar":          dict(name="gravel production, crushed", product="gravel, crushed", loc="RoW", density=None),
}
SHARED = dict(
    cement=dict(name="cement production, Portland", product="cement, Portland", loc="RoW"),
    sand=dict(name="gravel and sand quarry operation", product="sand", loc="RoW"),
    electricity=dict(name="market for electricity, low voltage", product="electricity, low voltage", loc="MX"),
)
# Mix designs (mass fractions of the finished block).
#   Earth block: cement-stabilised compressed earth. The earth itself is modelled as sand quarrying
#   (extraction only); pressing energy as electricity.
EARTH_MIX = dict(cement=0.08, earth=0.92, press_kwh_per_kg=0.01)
#   Sargassum-based concrete: 35% sargassum (taken as dry mass), oven-dried; drying energy as electricity.
SBC_MIX = dict(cement=0.15, sand=0.50, sargassum=0.35, drying_kwh_per_kg_sargassum=0.30)

# External insulation system per m2 of wall: 25 mm EPS (15 kg/m3), adhesive + reinforced base coat
# (cement mortar), glass-fibre mesh. Each entry lists alternative ecoinvent names, tried in order.
EPS_SYSTEM = [
    ("EPS board 25 mm", 0.375, [dict(name="polystyrene foam slab production", product="polystyrene foam slab"),
                                dict(name="market for polystyrene foam slab", product="polystyrene foam slab")]),
    ("adhesive and base coat (cement mortar)", 9.0, [dict(name="cement mortar production", product="cement mortar"),
                                                     dict(name="market for cement mortar", product="cement mortar"),
                                                     dict(name="base plaster production", product="base plaster")]),
    ("glass-fibre mesh", 0.16, [dict(name="glass fibre production", product="glass fibre"),
                                dict(name="market for glass fibre", product="glass fibre")]),
]

GSD = dict(mass=1.05, energy=1.15)   # geometric standard deviations of the foreground quantities

# Impact methods: the script picks the best match for each category and PRINTS what it chose.
#   Paper: ReCiPe 2016 v1.03 midpoint (H) no LT; human toxicity from EF v3.0 (USEtox), CTUh.
DESIRED = {
    "gwp":            ["climate change", "gwp100"],
    "water":          ["water", "consumption"],
    "acidification":  ["terrestrial acidification"],
    "eutrophication": ["freshwater eutrophication"],
    "human_toxicity": ["human toxicity", "non-carcinogenic"],
    "fossil":         ["fossil fuel"],        
}
PREFER = "ReCiPe 2016"


def setup():
    bd.projects.set_current(CONFIG["PROJECT"])
    if bi is None:
        raise ImportError("bw2io is not installed")
    if CONFIG["EI_DB"] not in bd.databases:
        bi.import_ecoinvent_release(version=CONFIG["EI_VERSION"], system_model="cutoff")   # asks for your ecoinvent username and password
    print("Project ready:", CONFIG["PROJECT"], "| databases:", list(bd.databases))


def search(text, n=15):
    bd.projects.set_current(CONFIG["PROJECT"])
    for a in bd.Database(CONFIG["EI_DB"]).search(text, limit=n):
        print(f"  {a['name']} | {a.get('reference product', '')} | {a.get('location', '')} | {a.get('unit', '')}")


def resolve_methods():
    res = {}
    for label, kws in DESIRED.items():
        cand = []
        for m in bd.methods:
            s = " | ".join(m).lower()
            if all(k in s for k in kws):
                unit = str(bd.methods[m].get("unit", "")).lower()
                pts = (10 if PREFER.lower() in s else 0) + (3 if "(h)" in s else 0) - (8 if "obsolete" in s else 0) - (4 if "superseded" in s else 0)
                pts -= 50 if "endpoint" in s else 0                       # midpoint indicators only
                if label == "human_toxicity" and "ctu" in unit:           # USEtox-based, CTUh, as in Table 5
                    pts += 30
                cand.append((pts, m))
        if not cand:
            raise RuntimeError(f"No impact method found for '{label}' (keywords {kws}). List them with bd.methods.")
        cand.sort(key=lambda x: x[0], reverse=True); res[label] = cand[0][1]
    return res


def find(spec):
    db = bd.Database(CONFIG["EI_DB"])
    cands = [a for a in db if spec["name"] in a["name"] and spec.get("product", "") in a.get("reference product", "")]
    if not cands:
        raise ValueError(f"No ecoinvent activity matches {spec}. Use --search \"{spec['name']}\".")
    pref = lambda a: (0 if a.get("location") == spec.get("loc") else 1 if a.get("location") == "MX" else 2 if a.get("location") == "RoW" else 3 if a.get("location") == "GLO" else 4, a["name"])
    cands.sort(key=pref); return cands[0]


def find_any(specs):
    for sp in specs:
        try:
            return find(dict(sp, loc=sp.get("loc", "RoW")))
        except ValueError:
            continue
    raise ValueError(f"None of these ecoinvent activities was found: {[sp['name'] for sp in specs]}. Use --search.")


def logn(amount, gsd):
    return dict(amount=amount, uncertainty_type=2, loc=math.log(abs(amount)), scale=math.log(gsd)) if amount else dict(amount=0.0)


def build_foreground():
    cem, sand, elec = find(SHARED["cement"]), find(SHARED["sand"]), find(SHARED["electricity"])
    if CONFIG["FG_DB"] in bd.databases:
        del bd.databases[CONFIG["FG_DB"]]
    data, inventory = {}, []
    for name, w in WALLS.items():
        key = (CONFIG["FG_DB"], name); m = w["mass"]; ex = []
        def add(act, amount, gsd, what, unit):
            ex.append({"input": act.key, "type": "technosphere", **logn(amount, gsd)})
            inventory.append(dict(material=name, flow=what, amount_per_m2=amount, unit=unit, dataset=act["name"],
                                  reference_product=act.get("reference product", ""), location=act.get("location", "")))
        if w["kind"] == "proxy":
            p = PROXY[name]; act = find(p); unit = (act.get("unit") or "kilogram").lower()
            if unit.startswith("cubic"):
                add(act, m / p["density"], GSD["mass"], "material (proxy, by mass)", "m3")
            else:
                add(act, m, GSD["mass"], "material (proxy)", "kg")
        elif w["kind"] == "earth":
            add(cem, EARTH_MIX["cement"] * m, GSD["mass"], "cement (stabiliser)", "kg")
            add(sand, EARTH_MIX["earth"] * m, GSD["mass"], "earth (as sand quarrying)", "kg")
            add(elec, EARTH_MIX["press_kwh_per_kg"] * m, GSD["energy"], "pressing electricity", "kWh")
        elif w["kind"] == "eps":
            for what, amount, specs in EPS_SYSTEM:
                add(find_any(specs), amount, GSD["mass"], what, "kg")
        elif w["kind"] == "sbc":
            sarg = SBC_MIX["sargassum"] * m
            add(cem, SBC_MIX["cement"] * m, GSD["mass"], "cement", "kg")
            add(sand, SBC_MIX["sand"] * m, GSD["mass"], "sand", "kg")
            add(elec, SBC_MIX["drying_kwh_per_kg_sargassum"] * sarg, GSD["energy"], "drying energy (as electricity)", "kWh")
            inventory.append(dict(material=name, flow="sargassum (burden-free residue, biogenic carbon neutral)", amount_per_m2=sarg,
                                  unit="kg", dataset="-", reference_product="-", location="MX"))
        data[key] = {"name": name, "unit": "m2 wall (A1-A3)", "exchanges": [{"input": key, "amount": 1.0, "type": "production"}] + ex}
    bd.Database(CONFIG["FG_DB"]).write(data)
    return pd.DataFrame(inventory)


def run():
    bd.projects.set_current(CONFIG["PROJECT"])
    methods = resolve_methods()
    print("Impact methods used (report these in the paper):")
    for k, m in methods.items():
        print(f"   {k:15s} {m}   [{bd.methods[m].get('unit', '')}]")
    inv = build_foreground(); fg = bd.Database(CONFIG["FG_DB"])
    acts = {a["name"]: a for a in fg}
    if ONLY:
        acts = {k: v for k, v in acts.items() if k in ONLY}
    # deterministic, six categories
    det = {}
    print("Deterministic results ...", flush=True)
    for name, act in acts.items():
        lca = bc.LCA({act: 1}, methods["gwp"]); lca.lci(); row = {}
        for k, m in methods.items():
            lca.switch_method(m); lca.lcia(); row[k] = lca.score
        det[name] = row
    # contribution of each foreground input to GWP
    contrib = []
    for name, act in acts.items():
        lca = bc.LCA({act: 1}, methods["gwp"]); lca.lci(); lca.lcia(); total = lca.score
        for e in act.exchanges():
            if e["type"] != "technosphere" or e["amount"] == 0: continue
            lca.lci(demand={e.input.id: e["amount"]}); lca.lcia()   # bw2calc 2.x wants the integer id
            contrib.append(dict(material=name, input=e.input["name"], gwp=lca.score, share_pct=100 * lca.score / total))
    # Monte-Carlo on GWP
    np.random.seed(CONFIG["SEED"]); mc = {}
    for name, act in acts.items():
        lca = bc.LCA({act: 1}, methods["gwp"], use_distributions=True); lca.lci(); lca.lcia(); v = []
        import time; t0 = time.time()
        for i in range(CONFIG["N_MONTECARLO"]):
            next(lca); v.append(lca.score)
            if (i + 1) % 50 == 0:
                print(f"      {name}: {i + 1}/{CONFIG['N_MONTECARLO']}  ({time.time() - t0:.0f} s)", flush=True)
        mc[name] = v; print(f"   Monte-Carlo done: {name}")
    mc = pd.DataFrame(mc)
    # ---- the file the pipeline reads ----
    cols = ["material", "gwp_mean", "gwp_cv_pct", "gwp", "water", "acidification", "eutrophication", "human_toxicity", "fossil"]
    old = {}
    if ONLY and (OUT / "lca_a1a3.csv").exists():   # keep the rows of the walls not re-run
        with open(OUT / "lca_a1a3.csv", newline="", encoding="utf-8") as f:
            old = {r["material"]: r for r in csv.DictReader(f)}
    with open(OUT / "lca_a1a3.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(cols)
        for name in WALLS:
            if name in acts:
                s = mc[name]; d = det[name]
                w.writerow([name, s.mean(), 100 * s.std() / s.mean(), d["gwp"], d["water"], d["acidification"], d["eutrophication"], d["human_toxicity"], d["fossil"]])
            elif name in old:
                w.writerow([old[name][c] for c in cols])
    summ = pd.DataFrame({"mean": mc.mean(), "median": mc.median(), "CV_pct": 100 * mc.std() / mc.mean(), "P5": mc.quantile(0.05), "P95": mc.quantile(0.95)})
    xlsx = OUT / ("lca_brightway_full.xlsx" if not ONLY else "lca_brightway_extra.xlsx")
    with pd.ExcelWriter(xlsx, engine="openpyxl") as xw:
        pd.DataFrame(det).T.to_excel(xw, sheet_name="A1-A3 per m2 wall")
        summ.to_excel(xw, sheet_name="Monte-Carlo GWP summary")
        inv.to_excel(xw, sheet_name="Inventory per m2 wall", index=False)
        pd.DataFrame(contrib).to_excel(xw, sheet_name="GWP contribution", index=False)
        pd.DataFrame([dict(category=k, method=" | ".join(m), unit=bd.methods[m].get("unit", "")) for k, m in methods.items()]).to_excel(xw, sheet_name="Methods used", index=False)
        mc.to_excel(xw, sheet_name="Monte-Carlo samples", index=False)
    print(summ.round(2).to_string())
    print("\nWritten:", OUT / "lca_a1a3.csv", "and", xlsx)
    print("Next: run ../run_all.py")


def _arg_after(flag):
    """Value after a flag, joining words (Spyder's runfile splits args on spaces and keeps quotes)."""
    if flag not in sys.argv: return None
    words = []
    for w in sys.argv[sys.argv.index(flag) + 1:]:
        if w.startswith("--"): break
        words.append(w)
    return " ".join(words).strip("\"' ")

_only = _arg_after("--only")
ONLY = [n for n in WALLS if any(n.lower().startswith(o.strip().lower()) for o in _only.split(";"))] if _only else None
if _only and not ONLY:
    raise SystemExit(f"--only '{_only}' matches no item. Items: {list(WALLS)}")
if ONLY: print("Running only:", ONLY)

if __name__ == "__main__":
    if "--setup" in sys.argv:
        setup()
    elif "--search" in sys.argv:
        search(_arg_after("--search"))
    else:
        run()
