"""Run one EnergyPlus case and return annual heating and cooling (kWh per m2 of 73.45 m2).

EnergyPlus is located in this order:
  1. the environment variable ENERGYPLUS_EXE (full path to the energyplus executable);
  2. `energyplus` on the PATH;
  3. the default install folders of EnergyPlus 25.1 on Windows, macOS and Linux.
"""
import csv, glob, os, shutil, subprocess, sys, uuid
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_idf as B

WEATHER = os.path.join(HERE, "weather")
WX = {"CDMX": os.path.join(WEATHER, "MEX_MEX_Fes.Cuautitlan.766700_TMYx.epw"),
      "Hermosillo": os.path.join(WEATHER, "MEX_SON_Hermosillo.761600_TMYx.epw"),
      "Merida": os.path.join(WEATHER, "MEX_YUC_Merida-Rejon.Intl.AP.766440_TMYx.epw")}
RUNS = os.path.join(HERE, "runs")


def find_energyplus():
    exe = os.environ.get("ENERGYPLUS_EXE")
    if exe and os.path.isfile(exe):
        return exe
    exe = shutil.which("energyplus")
    if exe:
        return exe
    pats = [r"C:\EnergyPlusV25-1-0\energyplus.exe", r"C:\EnergyPlusV*\energyplus.exe",
            "/Applications/EnergyPlus-25-1-0/energyplus", "/Applications/EnergyPlus-*/energyplus",
            "/usr/local/EnergyPlus-25-1-0/energyplus", "/usr/local/EnergyPlus-*/energyplus"]
    for p in pats:
        hits = sorted(glob.glob(p))
        if hits:
            return hits[-1]
    raise FileNotFoundError("EnergyPlus not found. Install EnergyPlus 25.1 or set ENERGYPLUS_EXE "
                            "to the full path of the energyplus executable (see README).")


EP = None


def run(params, city="CDMX", tag=None, keep=False):
    global EP
    EP = EP or find_energyplus()
    tag = tag or uuid.uuid4().hex[:8]
    d = os.path.join(RUNS, tag); os.makedirs(d, exist_ok=True)
    idf = os.path.join(d, "in.idf")
    with open(idf, "w") as f:
        f.write(B.build(params))
    subprocess.run([EP, "-w", WX[city], "-d", d, idf], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    tbl = os.path.join(d, "eplustbl.csv")
    if not os.path.isfile(tbl):
        raise RuntimeError(f"EnergyPlus produced no results in {d}; see eplusout.err there.")
    res = {}
    for x in csv.reader(open(tbl)):
        if len(x) > 13 and x[0] == "" and x[1] in ("Heating", "Cooling") and x[1] not in res:
            res[x[1]] = sum(float(v) for v in x[2:16] if v.strip())
        if len(x) > 3 and x[1] == "PB:Z1_E" and "Uf" not in res:
            res["Uf"] = float(x[6]) if len(x) > 6 else None
    res["severe"] = open(os.path.join(d, "eplusout.err")).read().count("** Severe")
    res["heat"] = res.pop("Heating") / B.AREA_NORM
    res["cool"] = res.pop("Cooling") / B.AREA_NORM
    if not keep:
        shutil.rmtree(d, ignore_errors=True)
    return res


if __name__ == "__main__":
    print("EnergyPlus:", find_energyplus())
    print(run({}, tag="base", keep=True))
