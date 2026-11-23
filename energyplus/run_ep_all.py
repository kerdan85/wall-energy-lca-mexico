"""All EnergyPlus runs used by the manuscript pipeline.

Writes, in the output folder:
  energyplus_results.csv        6 walls x 2 U sets x 3 cities (heating, cooling kWh/m2 of 73.45 m2)
  energyplus_perturbations.csv  derivative and check runs used by mk_robust.py
Wall inputs follow the manuscript (Tables 3-4): thickness, density, specific heat, measured and
tabulated U (ISO 6946, Rsi 0.13, Rse 0.04), with the solar absorptance of the
sustainable-walls-uvalues dataset (colour of the unrendered unit).
"""
import csv, os, sys
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import runner
from run_36 import CALIBRATED

# U measured, U tabulated, thickness, density, cp, solar absorptance
WALLS = {
    "Concrete (ref.)":          (2.16, 3.00, 0.12, 1200, 880, 0.65),
    "Adobe-type block":         (2.07, 2.44, 0.12, 1600, 1000, 0.55),
    "Volcanic stone (recinto)": (2.73, 3.29, 0.12, 1400, 900, 0.85),
    "Tepetate ashlar":          (1.50, 2.21, 0.20, 1500, 1000, 0.45),
    "SBC block (solid)":        (1.89, 2.59, 0.12, 1250, 1000, 0.60),
    "SBC block (hollow)":       (2.21, 1.99, 0.15, 900, 1000, 0.60),
}
REF = "Concrete (ref.)"
CITIES = {"Mexico City": ("CDMX", 15.3), "Merida": ("Merida", 26.5), "Hermosillo": ("Hermosillo", 24.4)}
RSUM = 0.17


def k_of(U, t):
    return t / (1.0 / U - RSUM)


def wall(U, t, rho, cp, a):
    return dict(t=t, k=round(k_of(U, t), 5), rho=rho, cp=cp, abs=a)


def jobs():
    J = []
    for city in CITIES:
        for m, (um, ut, t, rho, cp, a) in WALLS.items():
            J += [(city, m, "measured", wall(um, t, rho, cp, a)),
                  (city, m, "tabulated", wall(ut, t, rho, cp, a)),
                  (city, m, "U+10", wall(um * 1.1, t, rho, cp, a)),
                  (city, m, "U-10", wall(um * 0.9, t, rho, cp, a)),
                  (city, m, "cp+30", wall(um, t, rho, cp * 1.3, a)),
                  (city, m, "cp-30", wall(um, t, rho, cp * 0.7, a)),
                  (city, m, "check_U+10_cp+20", wall(um * 1.1, t, rho, cp * 1.2, a))]
            if m != REF:   # alternative U on the reference wall (thickness, mass, colour of concrete)
                _, _, tr, rr, cr, ar = WALLS[REF]
                J.append((city, m, "U_only", wall(um, tr, rr, cr, ar)))
        # tepetate at the reference thickness, same conductivity
        um, ut, t, rho, cp, a = WALLS["Tepetate ashlar"]
        k = k_of(um, t)
        J.append((city, "Tepetate ashlar", "equal_thickness", dict(t=0.12, k=round(k, 5), rho=rho, cp=cp, abs=a)))
    return J


def run(job):
    city, m, case, w = job
    wx, tmean = CITIES[city]
    p = dict(CALIBRATED, ground_temp=round(tmean + 2.7, 1), wall=w)
    tag = f"ep_{wx}_{case}_{m.split()[0]}_{m.split()[-1].strip('()')}".replace("+", "p").replace("-", "m")
    r = runner.run(p, city=wx, tag=tag)
    return dict(city=city, material=m, case=case, k=w["k"], t=w["t"], rho=w["rho"], cp=w["cp"], abs=w["abs"],
                heating_kwh_m2=round(r["heat"], 3), cooling_kwh_m2=round(r["cool"], 3), severe=r["severe"])


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    outdir = sys.argv[1] if len(sys.argv) > 1 else here
    with Pool(os.cpu_count()) as P:
        res = P.map(run, jobs())
    print("runs", len(res), "severe errors", sum(r["severe"] for r in res))
    with open(os.path.join(outdir, "energyplus_results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["city", "material", "u_set", "u_value", "heating_kwh_m2", "cooling_kwh_m2"])
        w.writeheader()
        for r in res:
            if r["case"] in ("measured", "tabulated"):
                um, ut = WALLS[r["material"]][:2]
                w.writerow(dict(city=r["city"], material=r["material"], u_set=r["case"],
                                u_value=um if r["case"] == "measured" else ut,
                                heating_kwh_m2=round(r["heating_kwh_m2"], 2), cooling_kwh_m2=round(r["cooling_kwh_m2"], 2)))
    with open(os.path.join(outdir, "energyplus_perturbations.csv"), "w", newline="") as f:
        fn = ["city", "material", "case", "t", "k", "rho", "cp", "abs", "heating_kwh_m2", "cooling_kwh_m2"]
        w = csv.DictWriter(f, fieldnames=fn)
        w.writeheader()
        for r in res:
            w.writerow({k: r[k] for k in fn})
    # hand the two tables to the analysis pipeline
    inputs = os.path.join(here, "..", "pipeline", "inputs")
    if os.path.isdir(inputs) and os.path.abspath(outdir) != os.path.abspath(inputs):
        import shutil
        for fn in ("energyplus_results.csv", "energyplus_perturbations.csv"):
            shutil.copy(os.path.join(outdir, fn), os.path.join(inputs, fn))
        print("copied to", os.path.normpath(inputs))
    for r in res:
        if r["case"] in ("measured", "tabulated"):
            print(f'{r["city"]:12s} {r["case"]:9s} {r["material"]:26s} H {r["heating_kwh_m2"]:7.2f} C {r["cooling_kwh_m2"]:7.2f}')
