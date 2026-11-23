#!/usr/bin/env python3
"""Free-running comfort (no heating or cooling): degree-hours outside the EN 16798-1 Category II
adaptive band during occupied hours, too cold (left) and too warm (right), present and 2050 climate."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = HERE; DST = os.path.normpath(os.path.join(HERE, "..", "figures")); os.makedirs(DST, exist_ok=True)
import json, shutil, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import style_nat as S; S.apply()

R = json.load(open(f"{OUT}/robust_results.json")); CF = R.get("COMFORT")
if not CF:
    print("no comfort results: figure skipped"); raise SystemExit
INK, MUT = S.INK, S.MUT
CLIM = ["CDMX", "Warm-subhumid", "Hot-arid"]
MATS = ["Concrete (ref.)", "Concrete + EPS (insulated)", "Adobe-type block", "Tepetate ashlar",
        "SBC block (solid)", "SBC block (hollow)", "Volcanic stone (recinto)"]
NAME = {"Concrete (ref.)": "Concrete (ref.)", "Concrete + EPS (insulated)": "Insulated concrete", "Adobe-type block": "Earth block",
        "Tepetate ashlar": "Tepetate", "SBC block (solid)": "SBC solid", "SBC block (hollow)": "SBC hollow",
        "Volcanic stone (recinto)": "Volcanic stone"}
COLD, WARM = "#7d9bb5", "#c08a55"
fig, axes = plt.subplots(1, 3, figsize=(7.4, 3.3), sharey=True)
y = np.arange(len(MATS))[::-1]; h = 0.36
for k, c in enumerate(CLIM):
    ax = axes[k]
    for yy, m in zip(y, MATS):
        p, f = CF["present"][c][m], CF["2050"][c][m]
        ax.barh(yy + h / 2, -p["kh_below"] / 1000, h, color=COLD, lw=0, zorder=3)
        ax.barh(yy + h / 2, p["kh_above"] / 1000, h, color=WARM, lw=0, zorder=3)
        ax.barh(yy - h / 2, -f["kh_below"] / 1000, h, fc="white", ec=COLD, lw=0.8, hatch="////", zorder=3)
        ax.barh(yy - h / 2, f["kh_above"] / 1000, h, fc="white", ec=WARM, lw=0.8, hatch="////", zorder=3)
        tot = (p["kh_below"] + p["kh_above"]) / 1000
        ax.text(0.98, yy + h / 2, f"{tot:.1f}", transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=6.2, color=INK)
    ax.axvline(0, color=INK, lw=0.8, zorder=4)
    ax.set_yticks(y); ax.set_yticklabels([NAME[m] for m in MATS], fontsize=7.4); ax.tick_params(axis="y", length=0)
    ax.axhline(len(MATS) - 1.5, color=MUT, lw=0.5, ls=(0, (2, 2)))
    for s_ in ("top", "right", "left"): ax.spines[s_].set_visible(False)
    ax.grid(axis="x", zorder=0); ax.set_axisbelow(True); ax.tick_params(axis="x", labelsize=6.8)
    lim = max(max(CF[cl][c][m]["kh_below"], CF[cl][c][m]["kh_above"]) for cl in ("present", "2050") for m in MATS) / 1000 * 1.12
    ax.set_xlim(-lim, lim * 1.18)
    ax.set_xticks(ax.get_xticks()); ax.set_xticklabels([f"{abs(v):g}" for v in ax.get_xticks()])
    ax.set_xlim(-lim, lim * 1.18)
    ax.set_title(S.CLIMLAB[c].split(" (")[0], fontsize=8.8, pad=6)
    S.panel(ax, "abc"[k], x=-0.04 if k else -0.42, y=1.03)
    ax.text(0.98, 1.0, "total", transform=ax.transAxes, ha="right", va="bottom", fontsize=6.2, color=MUT)
fig.text(0.57, 0.12, "Degree-hours outside the adaptive comfort band, occupied hours (10$^3$ K h yr$^{-1}$)   $\\leftarrow$ too cold  |  too warm $\\rightarrow$", fontsize=7.8, ha="center")
fig.legend(handles=[Patch(fc=COLD, label="Too cold, present climate"), Patch(fc=WARM, label="Too warm, present climate"),
                    Patch(fc="white", ec=MUT, hatch="////", label="2041–2060 climate (SSP2-4.5)")],
           loc="lower center", ncol=3, fontsize=7.0, frameon=False, bbox_to_anchor=(0.57, 0.0))
fig.subplots_adjust(left=0.15, right=0.99, top=0.88, bottom=0.25, wspace=0.12)   # explicit layout (tight_layout is unreliable here across matplotlib versions)
plt.savefig(f"{OUT}/nat_comfort.png"); shutil.copy(f"{OUT}/nat_comfort.png", f"{DST}/nat_comfort.png"); print("comfort saved")
