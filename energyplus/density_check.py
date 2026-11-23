"""Reference concrete block with density-matched tabulated conductivities (review check).
k = 0.57 W/mK: medium-weight concrete block, 1400 kg/m3 (SEAI DEAP table, from TGD L, CIBSE Guide A, EN ISO 10456);
k = 0.46 W/mK: linear interpolation to the tested 1200 kg/m3 between the 700 (0.20) and 1400 (0.57) kg/m3 entries.
Writes energyplus_density_check.csv (also to ../pipeline/inputs).  Usage: python density_check.py"""
import csv, os, shutil
from multiprocessing import Pool
import run_ep_all as A, runner
HERE = os.path.dirname(os.path.abspath(__file__))
CASES = {"k0.57_1400": 0.57, "k0.46_1200": 0.46}

def go(j):
    city, case = j; um, ut, t, rho, cp, a = A.WALLS[A.REF]; wx, tm = A.CITIES[city]
    w = dict(t=t, k=CASES[case], rho=rho, cp=cp, abs=a)
    r = runner.run(dict(A.CALIBRATED, ground_temp=round(tm + 2.7, 1), wall=w), city=wx)
    return city, case, 1 / (A.RSUM + t / CASES[case]), round(r["heat"], 3), round(r["cool"], 3)

if __name__ == "__main__":
    with Pool(os.cpu_count()) as P:
        res = P.map(go, [(c, k) for c in A.CITIES for k in CASES])
    fn = os.path.join(HERE, "energyplus_density_check.csv")
    with open(fn, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["city", "case", "U", "heating_kwh_m2", "cooling_kwh_m2"])
        for r in res: w.writerow([r[0], r[1], round(r[2], 3), r[3], r[4]])
    if os.path.isdir(os.path.join(HERE, "..", "pipeline", "inputs")):
        shutil.copy(fn, os.path.join(HERE, "..", "pipeline", "inputs"))
    for r in res: print(r)
