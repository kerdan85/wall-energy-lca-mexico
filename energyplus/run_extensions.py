"""Extensions to the main runs (revision 2):

  1. Insulated concrete benchmark: the reference block with 25 mm of EPS and a 5 mm render on the
     outside (external thermal insulation composite system), conditioned like every other wall.
  2. Free-running comfort: every wall with no heating or cooling (natural ventilation all year),
     scored against the adaptive comfort model of EN 16798-1 (Category II: +3 K / -4 K).
  3. Mid-century climate: the three weather files shifted by the CMIP6 SSP2-4.5 warming for
     2041-2060 (relative humidity kept), conditioned and free-running.

Writes, in this folder and in ../pipeline/inputs:
  energyplus_insulated.csv   insulated wall: measured / tabulated / U+-10 / cp+-30 / check, 3 cities
  energyplus_comfort.csv     free-running comfort, every wall, present and 2050 climate
  energyplus_2050.csv        conditioned need, every wall, 2050 climate
Usage: python run_extensions.py
"""
import csv, math, os, sqlite3, shutil, sys, uuid
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_idf as B
import runner
from run_ep_all import WALLS, CITIES, REF, wall, k_of, RSUM
from run_36 import CALIBRATED

INS = "Concrete + EPS (insulated)"
EPS = (0.025, 0.035, 15.0, 1400.0)       # thickness m, k W/mK, density kg/m3, cp J/kgK
RENDER = (0.005, 0.70, 1500.0, 1000.0)   # polymer-modified base coat and finish

# CMIP6 SSP2-4.5, 2041-2060 vs 1995-2014, annual mean warming of the AR6 reference region
# (Almazroui et al. 2021, Table 2, M9 ensemble): NCA 1.52 K, SCA 1.36 K
DT2050 = {"CDMX": 1.52, "Merida": 1.36, "Hermosillo": 1.52}
WX2050 = {k: os.path.join(HERE, "weather", "2050", os.path.basename(v).replace("_TMYx", "_TMYx_2050SSP245"))
          for k, v in runner.WX.items()}


def insulated(U_core, cp_scale=1.0, U_target=None):
    """Concrete core (from its own U), EPS and render outside. If U_target is given, the EPS
    conductivity is adjusted so that the whole wall reaches it (used for the U+-10% runs)."""
    _, _, t, rho, cp, a = WALLS[REF]
    core = wall(U_core, t, rho, cp * cp_scale, a)
    eps = list(EPS)
    if U_target:
        r_needed = 1 / U_target - RSUM - t / core["k"] - RENDER[0] / RENDER[1]
        eps[1] = round(EPS[0] / r_needed, 5)
    core["outer"] = [RENDER, tuple(eps)]
    return core


def u_of(w):
    r = RSUM + w["t"] / w["k"] + sum(l[0] / l[1] for l in w.get("outer", []))
    return 1 / r


def all_walls(case="measured"):
    out = {}
    for m, (um, ut, t, rho, cp, a) in WALLS.items():
        out[m] = wall(um if case == "measured" else ut, t, rho, cp, a)
    um, ut = WALLS[REF][:2]
    out[INS] = insulated(um if case == "measured" else ut)
    return out


# ---------------- weather morphing (shift method, Belcher et al. 2005) ----------------
def dewpoint(T, RH):
    a, b = 17.625, 243.04
    g = math.log(max(RH, 1) / 100) + a * T / (b + T)
    return b * g / (a - g)


def morph(src, dst, dT):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    lines = open(src).read().splitlines()
    out = []
    for i, ln in enumerate(lines):
        if i < 8:
            if i == 6 and ln.startswith("COMMENTS 2"):
                ln = f"COMMENTS 2,Dry-bulb shifted by +{dT} K (CMIP6 SSP2-4.5 2041-2060, regional mean); RH kept; dew point recomputed"
            out.append(ln); continue
        f = ln.split(",")
        T = float(f[6]) + dT; RH = float(f[8])
        f[6] = f"{T:.1f}"; f[7] = f"{dewpoint(T, RH):.1f}"
        out.append(",".join(f))
    open(dst, "w").write("\n".join(out) + "\n")


def epw_daily_means(path):
    T = [float(l.split(",")[6]) for l in open(path).read().splitlines()[8:]]
    return [sum(T[d * 24:(d + 1) * 24]) / 24 for d in range(365)], T


# ---------------- adaptive comfort (EN 16798-1, Category II) ----------------
def occ24(use):
    prof = B.SCHED[use]["occ"]; v = []; h0 = 0
    for h, val in prof:
        v += [val] * (h - h0); h0 = h
    return v


AREA = sum(a for a, _ in B.ZONE_AV.values())


def comfort(sql, epw):
    daily, _ = epw_daily_means(epw)
    trm = []; r = daily[-1]                      # start from the last day (typical year wraps)
    for _ in range(2):                            # spin-up one year
        trm = []
        for d in range(365):
            trm.append(r); r = 0.8 * r + 0.2 * daily[d]
    con = sqlite3.connect(sql)
    q = """SELECT d.KeyValue, r.Value FROM ReportData r JOIN ReportDataDictionary d
           ON r.ReportDataDictionaryIndex=d.ReportDataDictionaryIndex
           WHERE d.Name='Zone Operative Temperature' ORDER BY d.KeyValue, r.TimeIndex"""
    data = {}
    for k, v in con.execute(q):
        data.setdefault(k.upper(), []).append(v)
    con.close()
    tot = above = below = dh_above = dh_below = 0.0
    for zn, (area, _) in B.ZONE_AV.items():
        vals = data[zn.upper()]; occ = occ24(B.USE[zn])
        for i, top in enumerate(vals[:8760]):
            w = occ[i % 24] * area
            if w == 0: continue
            t = trm[i // 24]
            hi = 0.33 * min(max(t, 10.0), 30.0) + 18.8 + 3   # Category II upper limit (Trm 10-30 degC)
            lo = 0.33 * min(max(t, 15.0), 30.0) + 18.8 - 4   # Category II lower limit (Trm 15-30 degC)
            tot += w
            if top > hi: above += w; dh_above += w * (top - hi)
            elif top < lo: below += w; dh_below += w * (lo - top)
    return dict(pct_above=100 * above / tot, pct_below=100 * below / tot,
                kh_above=dh_above / AREA, kh_below=dh_below / AREA)   # area-weighted degree-hours, occupied hours


def run_free(params, wx_path):
    tag = "fr_" + uuid.uuid4().hex[:8]; d = os.path.join(runner.RUNS, tag); os.makedirs(d, exist_ok=True)
    idf = os.path.join(d, "in.idf")
    open(idf, "w").write(B.build(dict(params, free_running=True, natvent_allyear=True)))
    import subprocess
    subprocess.run([runner.find_energyplus(), "-w", wx_path, "-d", d, idf], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    res = comfort(os.path.join(d, "eplusout.sql"), wx_path)
    res["severe"] = open(os.path.join(d, "eplusout.err")).read().count("** Severe")
    shutil.rmtree(d, ignore_errors=True)
    return res


def run_cond(params, wx_path):
    """Conditioned run on an arbitrary weather file (runner.run uses the city keys)."""
    key = "_tmp_" + uuid.uuid4().hex[:6]
    runner.WX[key] = wx_path
    return runner.run(params, city=key)


def job(j):
    kind, city, m, case, w, clim = j
    wx, tmean = CITIES[city]
    path = runner.WX[wx] if clim == "present" else WX2050[wx]
    gt = round(tmean + 2.7 + (0 if clim == "present" else DT2050[wx]), 1)
    p = dict(CALIBRATED, ground_temp=gt, wall=w)
    if kind == "free":
        r = run_free(p, path)
        return dict(kind=kind, city=city, material=m, case=case, climate=clim, **r)
    r = run_cond(p, path)
    return dict(kind=kind, city=city, material=m, case=case, climate=clim,
                heating_kwh_m2=round(r["heat"], 3), cooling_kwh_m2=round(r["cool"], 3), severe=r["severe"], U=round(u_of(w), 3))


def jobs():
    J = []
    um, ut = WALLS[REF][:2]
    _, _, t, rho, cp, a = WALLS[REF]
    u_ins = u_of(insulated(um))
    for city in CITIES:
        # 1. insulated benchmark, conditioned, present climate
        J += [("cond", city, INS, "measured", insulated(um), "present"),
              ("cond", city, INS, "tabulated", insulated(ut), "present"),
              ("cond", city, INS, "U+10", insulated(um, U_target=u_ins * 1.1), "present"),
              ("cond", city, INS, "U-10", insulated(um, U_target=u_ins * 0.9), "present"),
              ("cond", city, INS, "cp+30", insulated(um, cp_scale=1.3), "present"),
              ("cond", city, INS, "cp-30", insulated(um, cp_scale=0.7), "present"),
              ("cond", city, INS, "check_U+10_cp+20", insulated(um, cp_scale=1.2, U_target=u_ins * 1.1), "present")]
        for m, w in all_walls().items():
            J += [("free", city, m, "measured", w, "present"), ("free", city, m, "measured", w, "2050"),
                  ("cond", city, m, "measured", w, "2050")]
    return J


if __name__ == "__main__":
    for k, src in runner.WX.items():
        morph(src, WX2050[k], DT2050[k])
    print("EnergyPlus:", runner.find_energyplus())
    J = jobs(); print(len(J), "runs")
    with Pool(os.cpu_count()) as P:
        res = P.map(job, J)
    print("severe errors", sum(r["severe"] for r in res))
    ins = [r for r in res if r["kind"] == "cond" and r["climate"] == "present"]
    fut = [r for r in res if r["kind"] == "cond" and r["climate"] == "2050"]
    fr = [r for r in res if r["kind"] == "free"]
    outs = {"energyplus_insulated.csv": (ins, ["city", "material", "case", "U", "heating_kwh_m2", "cooling_kwh_m2"]),
            "energyplus_2050.csv": (fut, ["city", "material", "case", "U", "heating_kwh_m2", "cooling_kwh_m2"]),
            "energyplus_comfort.csv": (fr, ["city", "material", "climate", "pct_above", "pct_below", "kh_above", "kh_below"])}
    inputs = os.path.join(HERE, "..", "pipeline", "inputs")
    for fn, (rows, cols) in outs.items():
        with open(os.path.join(HERE, fn), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
            for r in rows:
                w.writerow({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})
        if os.path.isdir(inputs): shutil.copy(os.path.join(HERE, fn), os.path.join(inputs, fn))
    for r in ins: print(f'{r["city"]:12s} {r["case"]:18s} U {r["U"]:.3f}  H {r["heating_kwh_m2"]:7.2f} C {r["cooling_kwh_m2"]:7.2f}')
    for r in sorted(fr, key=lambda r: (r["climate"], r["city"], r["material"])):
        print(f'{r["climate"]:7s} {r["city"]:12s} {r["material"]:28s} above {r["pct_above"]:5.1f}%  below {r["pct_below"]:5.1f}%  Kh+ {r["kh_above"]:7.0f} Kh- {r["kh_below"]:7.0f}')
    for r in fut: print(f'2050 {r["city"]:12s} {r["material"]:28s} H {r["heating_kwh_m2"]:7.2f} C {r["cooling_kwh_m2"]:7.2f}')
