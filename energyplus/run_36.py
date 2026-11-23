"""Run the 36 EnergyPlus cases (6 walls x 2 U sets x 3 cities) with the calibrated model
with the first-pass wall data. Superseded by run_ep_all.py; kept because it
defines CALIBRATED, the calibrated operation settings, used by every other script."""
import csv, json, os, sys
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import runner

R = lambda a, b: set(range(a, b))
NIGHT = R(20, 24) | R(0, 7)
CALIBRATED = dict(
    hvac_hours={"bed": NIGHT, "common": R(7, 23), "kitchen": R(7, 23), "circ": R(7, 23), "toilet": R(7, 23)},
    cool_hours={"bed": NIGHT, "common": R(15, 23), "kitchen": R(16, 23), "circ": R(16, 23), "toilet": R(16, 23)},
    heat_sp=18.0, heat_sb=12.0, cool_sp=25.0, cool_sb=28.0,
    natvent_ach=5.0, natvent_setpoint=24.0, infiltration_ach=0.7, oa_per_person=0.008, dst=False, timestep=2)

# sustainable-walls-uvalues v1.0: thickness, density, cp, solar absorptance, k measured, k literature
WALLS = {
    "Concrete (ref.)":          (0.12, 2300, 880, 0.65, 0.41, 1.74),
    "Adobe-type block":         (0.12, 1300, 1000, 0.55, 0.38, 0.50),
    "Volcanic stone (recinto)": (0.12, 1900, 850, 0.85, 0.61, 0.90),
    "Tepetate ashlar":          (0.20, 1500, 900, 0.45, 0.40, 0.70),
    "SBC block (solid)":        (0.12, 1450, 1000, 0.60, 0.33, 0.55),
    "SBC block (hollow)":       (0.15, 1300, 1000, 0.60, 0.53, 0.45),
}
# EPW, annual mean dry-bulb; ground under slab = annual mean + 2.7 K (gives the 18 degC of the DesignBuilder model in CDMX)
CITIES = {"Mexico City": ("CDMX", 15.3), "Merida": ("Merida", 26.5), "Hermosillo": ("Hermosillo", 24.4)}


def u_iso(t, k):
    return 1.0 / (0.13 + t / k + 0.04)


def case(arg):
    city, mat, uset = arg
    t, rho, cp, a, km, kl = WALLS[mat]
    k = km if uset == "measured" else kl
    wx, tmean = CITIES[city]
    p = dict(CALIBRATED, ground_temp=round(tmean + 2.7, 1), wall=dict(t=t, k=k, rho=rho, cp=cp, abs=a))
    r = runner.run(p, city=wx, tag=f"final_{wx}_{uset}_{mat.split()[0]}_{mat.split()[-1].strip('()')}")
    return dict(city=city, material=mat, u_set=uset, u_value=round(u_iso(t, k), 2),
                heating_kwh_m2=round(r["heat"], 2), cooling_kwh_m2=round(r["cool"], 2),
                u_energyplus=r["Uf"], severe=r["severe"])


if __name__ == "__main__":
    args = [(c, m, u) for c in CITIES for u in ("measured", "tabulated") for m in WALLS]
    with Pool(os.cpu_count()) as P:
        res = P.map(case, args)
    out = sys.argv[1] if len(sys.argv) > 1 else "energyplus_results.csv"
    with open(out, "w", newline="") as f:
        f.write("# EnergyPlus 25.1.0 runs of the rebuilt Casa Los Heroes model (calibrated to the 13 original\n")
        f.write("# DesignBuilder runs, Mexico City). kWh per m2 of 73.45 m2. u_value: ISO 6946 air-to-air (Rsi 0.13, Rse 0.04).\n")
        w = csv.DictWriter(f, fieldnames=["city", "material", "u_set", "u_value", "heating_kwh_m2", "cooling_kwh_m2",
                                          "u_energyplus"])
        w.writeheader()
        for r in res:
            w.writerow({k: r[k] for k in w.fieldnames})
    print("severe errors:", sum(r["severe"] for r in res))
    for r in res:
        print(f'{r["city"]:12s} {r["u_set"]:9s} {r["material"]:26s} U {r["u_value"]:4.2f}  H {r["heating_kwh_m2"]:6.2f}  C {r["cooling_kwh_m2"]:6.2f}')
