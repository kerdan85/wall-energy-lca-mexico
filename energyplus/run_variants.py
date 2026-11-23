"""Dwelling and finish variants requested in review (measured U, present climate, conditioned).

  det_slab   : base geometry (both side walls exposed, as in the companion model) with an uninsulated 100 mm roof slab
  end        : end-of-terrace unit (east wall is a party wall), insulated roof as in the base
  end_w      : end-of-terrace unit with the west wall as the party wall (orientation check)
  mid        : mid-terrace unit (east and west walls are adiabatic party walls), insulated roof as in the base
  mid_slab   : mid-terrace unit with the uninsulated roof slab
  cool_paint : base dwelling, concrete wall with a reflective coating (solar absorptance 0.25)

Writes energyplus_variants.csv (also copied to ../pipeline/inputs).
Usage: python run_variants.py
"""
import csv, os, shutil, sys
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import runner
import run_ep_all as A
import run_extensions as X

HERE = os.path.dirname(os.path.abspath(__file__))
VARIANTS = {"det_slab": dict(roof_slab=True), "end": dict(party_east=True), "end_w": dict(party_west=True), "mid": dict(party_walls=True),
            "mid_slab": dict(party_walls=True, roof_slab=True)}


def walls():
    out = {m: A.wall(um, t, rho, cp, a) for m, (um, ut, t, rho, cp, a) in A.WALLS.items()}
    out[X.INS] = X.insulated(A.WALLS[A.REF][0])
    return out


def jobs():
    J = []
    W = walls()
    for city in A.CITIES:
        for v in VARIANTS:
            for m, w in W.items():
                J.append((city, v, m, w))
        um, ut, t, rho, cp, a = A.WALLS[A.REF]
        J.append((city, "cool_paint", A.REF, A.wall(um, t, rho, cp, 0.25)))
    return J


def go(job):
    city, v, m, w = job
    wx, tm = A.CITIES[city]
    p = dict(A.CALIBRATED, ground_temp=round(tm + 2.7, 1), wall=w, **VARIANTS.get(v, {}))
    r = runner.run(p, city=wx)
    return dict(city=city, variant=v, material=m, heating_kwh_m2=round(r["heat"], 3),
                cooling_kwh_m2=round(r["cool"], 3), severe=r["severe"])


if __name__ == "__main__":
    with Pool(os.cpu_count()) as P:
        res = P.map(go, jobs())
    print("runs", len(res), "severe", sum(r["severe"] for r in res))
    fn = os.path.join(HERE, "energyplus_variants.csv")
    with open(fn, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["city", "variant", "material", "heating_kwh_m2", "cooling_kwh_m2"])
        w.writeheader()
        for r in res:
            w.writerow({k: r[k] for k in w.fieldnames})
    inp = os.path.join(HERE, "..", "pipeline", "inputs")
    if os.path.isdir(inp):
        shutil.copy(fn, inp)
    for r in res:
        print(f'{r["city"]:11s} {r["variant"]:10s} {r["material"]:27s} H {r["heating_kwh_m2"]:7.2f} C {r["cooling_kwh_m2"]:7.2f}')
