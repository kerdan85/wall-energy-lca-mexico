"""Reproduce every number and data figure of the manuscript from the input tables.

Spyder: open this file and press Run (F5).   Terminal: python run_all.py
Needs only numpy, matplotlib and Pillow (see environment.yml). No EnergyPlus and no
ecoinvent licence are needed: the EnergyPlus results and the ecoinvent-based production
carbon are read from the tables in inputs/ (see README, "Three ways to use this repository").

Figures are written to ../figures ; the numbers go to robust_results.json and the console.
"""
import os, sys, runpy
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE); sys.path.insert(0, HERE)
os.makedirs(os.path.join(HERE, "..", "figures"), exist_ok=True)
STEPS = [("sim_engine.py", "simplified hourly 5R1C model (fallback only, used if the EnergyPlus tables are missing)"),
         ("sim_tab.py", "same, with tabulated U"),
         ("mk_robust.py", "offsets, costs, scenarios, sensitivity, Monte Carlo -> robust_results.json"),
         ("mk_figs_rev.py", "U values, demand, production carbon, transport, offsets, sensitivity"),
         ("mk_fig_quadrant.py", "carbon and cost bars"),
         ("mk_fig_comfort.py", "free-running comfort"),
         ("mk_variants.py", "dwelling variants, rendered walls, 10% U uncertainty -> variants_results.json"),
         ("mk_fig_extra.py", "decomposition of the offset and abatement cost"),
         ("mk_map.py", "map of sources, cities and climates"),
         ("mk_figs_v3.py", "case-study dwelling, system boundary, multi-criteria"),
         ("mk_materials_plate.py", "materials plate"),
         ("mk_framework.py", "methodological framework")]
for f, what in STEPS:
    print("\n" + "=" * 70 + f"\n{f}: {what}\n" + "=" * 70)
    runpy.run_path(os.path.join(HERE, f), run_name="__main__")
print("\nDone. Figures are in", os.path.normpath(os.path.join(HERE, "..", "figures")))
