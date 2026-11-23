#!/usr/bin/env python3
"""Review variants: dwelling position in the terrace and roof, rendered walls, reflective coating,
and the effect of a 10% measurement uncertainty on the Monte-Carlo probabilities.

Inputs : inputs/energyplus_variants.csv (../energyplus/run_variants.py)
         ../energyplus/energyplus_colour_check.csv or inputs/energyplus_colour_check.csv
Output : variants_results.json (read by the manuscript tables)
Run in Spyder: runfile('mk_variants.py')  (it runs mk_robust.py first)
"""
import os, csv, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
import mk_robust as M
import lca_inputs as L

def _csv(name):
    for p in (os.path.join(HERE, "inputs", name), os.path.join(HERE, "..", "energyplus", name)):
        if os.path.exists(p):
            return list(csv.DictReader(open(p)))
    raise FileNotFoundError(name)

city = lambda s: L.CITYALIAS[s.strip().lower()]
VAR = {}
for r in _csv("energyplus_variants.csv"):
    VAR.setdefault(r["variant"], {}).setdefault(city(r["city"]), {})[r["material"]] = (float(r["heating_kwh_m2"]), float(r["cooling_kwh_m2"]))
COL = {}
for r in _csv("energyplus_colour_check.csv"):
    COL.setdefault(city(r["city"]), {})[r["material"]] = (float(r["heating_kwh_m2"]), float(r["cooling_kwh_m2"]))

# wall areas: side walls 2 storeys x 12.00 m x 2.8 m each (67.22 m2), bay east wall 1.46 m2, the rest opaque 34.09 m2
SIDE, BAYE = 67.22, 1.46
AW_DET = M.Aw
OTHER = AW_DET - 2 * SIDE - BAYE
AWV = {"det": AW_DET, "det_slab": AW_DET,
       "end": OTHER + SIDE + (SIDE + BAYE) / 2,                 # a party wall is shared: half its area per unit
       "end_w": OTHER + SIDE + BAYE + SIDE / 2,                 # west wall shared instead (orientation check)
       "mid": OTHER + (2 * SIDE + BAYE) / 2, "mid_slab": OTHER + (2 * SIDE + BAYE) / 2}
LABEL = {"det": "Detached (base)", "det_slab": "Detached, uninsulated roof", "end": "End-of-terrace", "end_w": "End-of-terrace (west party wall)",
         "mid": "Mid-terrace", "mid_slab": "Mid-terrace, uninsulated roof"}
SOLID, CC, INS, REF = M.SOLID, M.CC, M.INS, M.REF

def hc_of(v, c, m):
    if v == "det":
        return M.HC[c][m]
    mm = SOLID if m == CC else m
    return VAR[v][c][mm]

def ev(v, c, m, **kw):
    aw0 = M.Aw
    M.Aw = AWV[v]
    try:
        return M.evaluate(c, m, hc=hc_of(v, c, m), hcref=hc_of(v, c, REF), **kw)
    finally:
        M.Aw = aw0

OUT = {"AW": AWV, "LABEL": LABEL, "dwelling": {}, "rendered": {}, "cool_paint": {}, "u10": {}, "household": {}}
for v in AWV:
    OUT["dwelling"][v] = {c: {m: {k: ev(v, c, m)[k] for k in ("dCO2", "dC", "op", "prod", "tr")} for m in M.ALT} for c in M.CLIM}
    OUT.setdefault("dwelling_household", {})[v] = {c: {m: ev(v, c, m, ce=1.2)["dC"] for m in M.ALT} for c in M.CLIM}
    OUT["dwelling"][v]["need"] = {c: {m: sum(hc_of(v, c, m)) for m in M.MATS + [INS]} for c in M.CLIM}

# rendered walls: every alternative at the absorptance of the reference (0.65); the benchmark already has it
for c in M.CLIM:
    OUT["rendered"][c] = {}
    for m in M.ALT:
        mm = SOLID if m == CC else m
        hc = M.HC[c][m] if m == INS else COL[c][mm]
        e = M.evaluate(c, m, hc=hc)
        OUT["rendered"][c][m] = dict(dCO2=e["dCO2"], dC=e["dC"], need=sum(hc))

# reflective coating on the concrete wall (absorptance 0.25), detached base dwelling: operational offset only
for c in M.CLIM:
    hc = VAR["cool_paint"][c][REF]
    dE = M.efin(*M.HC[c][REF]) - M.efin(*hc)
    OUT["cool_paint"][c] = dict(need=sum(hc), need_ref=sum(M.HC[c][REF]), dE=dE, op_t=dE * M.Af * M.T * M.F_GRID / 1000,
                                pv_usd=dE * M.Af * M.CE * M.pvf(M.R) / M.FX)

# household view: subsidised tariff (1.2 MXN/kWh) for every result
for c in M.CLIM:
    OUT["household"][c] = {m: M.SCEN[c][m]["tariff_low"]["dC"] for m in M.ALT}

# Monte-Carlo with a 10% relative standard uncertainty on every measured U (same samples, deviations doubled)
uU10 = {m: 1 + 2 * (M.uU[m] - 1) for m in M.uU}
def dem10(c, m):
    d = M.DER[c][m]; h0, c0 = M.HC[c][m]
    h = np.clip(h0 + d["hU"] * (uU10[m] - 1) + d["hK"] * (M.uK[m] - 1), 0, None)
    cc = np.clip(c0 + d["cU"] * (uU10[m] - 1) + d["cK"] * (M.uK[m] - 1), 0, None)
    return h / M.COP_H + cc / M.cop
for c in M.CLIM:
    eref = dem10(c, REF); OUT["u10"][c] = {}
    for m in M.ALT:
        dE = eref - dem10(c, m)
        tkm = M.MASS[m] / 1000 * M.DIST[c][m]; tkr = M.MASS[REF] / 1000 * M.DIST[c][REF]
        dco2 = (dE * M.Af * M.T * M.fg + (M.g[REF] - M.g[m]) * M.Aw + (tkr - tkm) * M.eT * M.Aw) / 1000
        OUT["u10"][c][m] = dict(pco2=float(np.mean(dco2 > 0)), pco2_5=M.MCR[c][m]["pco2"],
                                p5=float(np.percentile(dco2, 5)), p95=float(np.percentile(dco2, 95)))


# heating with LPG instead of electric resistance (carbon only): IPCC 2006 default 63,100 kg CO2/TJ = 0.227 kg/kWh, appliance efficiency 0.85 (range 0.75-0.95)
EF_LPG = 63100 / 277778.0
OUT["lpg"] = {}
for eta in (0.75, 0.85, 0.95):
    OUT["lpg"][eta] = {}
    for c in M.CLIM:
        OUT["lpg"][eta][c] = {}
        for m in M.ALT:
            (hr, cr), (hx, cx) = M.HC[c][M.REF], M.HC[c][m]
            op = ((hr - hx) * EF_LPG / eta + (cr - cx) / M.COP_C * M.F_GRID) * M.Af * M.T / 1000
            b = M.BASE[c][m]
            OUT["lpg"][eta][c][m] = op + b["prod"] + b["tr"]
json.dump(OUT, open(os.path.join(HERE, "variants_results.json"), "w"), indent=1, default=float)

sh = lambda m: m.split(" (")[0][:14] + (" cc" if "city-cast" in m else "") + (" INS" if "EPS" in m else "")
print("\nAreas (m2) for embodied carbon and cost:", {k: round(v, 1) for k, v in AWV.items()})
for c in M.CLIM:
    print(f"\n=== {c} === dCO2 (t) by dwelling variant | rendered | P(co2>0) 5% vs 10% U")
    print("   ", "".join(f"{v:>10s}" for v in AWV), "  render   p5%  p10%")
    for m in M.ALT:
        print(f" {sh(m):18s}" + "".join(f"{OUT['dwelling'][v][c][m]['dCO2']:10.1f}" for v in AWV)
              + f"{OUT['rendered'][c][m]['dCO2']:9.1f}  {OUT['u10'][c][m]['pco2_5']:.2f}  {OUT['u10'][c][m]['pco2']:.2f}")
    cp = OUT["cool_paint"][c]
    print(" LPG heating (eta 0.85):", {sh(m): round(OUT["lpg"][0.85][c][m], 1) for m in M.ALT})
    print(f" reflective coating on concrete: need {cp['need_ref']:.1f} -> {cp['need']:.1f}, op offset {cp['op_t']:.1f} t, PV {cp['pv_usd']:.0f} USD")
