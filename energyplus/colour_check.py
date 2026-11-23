"""Every alternative wall with the solar absorptance of concrete (0.65), to isolate the colour effect.
Usage: python colour_check.py   (needs energyplus_results.csv from run_ep_all.py in this folder)"""
import csv, os
from multiprocessing import Pool
import run_ep_all as A, runner
HERE = os.path.dirname(os.path.abspath(__file__))


def go(j):
    city, m = j; um, ut, t, rho, cp, a = A.WALLS[m]; wx, tm = A.CITIES[city]
    r = runner.run(dict(A.CALIBRATED, ground_temp=round(tm + 2.7, 1), wall=A.wall(um, t, rho, cp, 0.65)), city=wx)
    return city, m, round(r["heat"], 3), round(r["cool"], 3)


if __name__ == "__main__":
    J = [(c, m) for c in A.CITIES for m in A.WALLS if m != A.REF]
    with Pool(os.cpu_count()) as P:
        res = P.map(go, J)
    base = {(r["city"], r["material"]): float(r["heating_kwh_m2"]) + float(r["cooling_kwh_m2"])
            for r in csv.DictReader(open(os.path.join(HERE, "energyplus_results.csv"))) if r["u_set"] == "measured"}
    with open(os.path.join(HERE, "energyplus_colour_check.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["city", "material", "case", "heating_kwh_m2", "cooling_kwh_m2"])
        for c, m, h, cc in res:
            w.writerow([c, m, "abs_0.65", h, cc])
            print(f"{c:12s} {m:26s} own colour {base[(c, m)]:6.1f}  at 0.65 {h + cc:6.1f}  effect {h + cc - base[(c, m)]:+6.1f}")
