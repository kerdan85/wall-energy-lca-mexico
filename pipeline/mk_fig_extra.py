#!/usr/bin/env python3
"""Decomposition of the lifetime offset and abatement cost (figures added in revision 2).
Needs robust_results.json (mk_robust.py) and variants_results.json (mk_variants.py).
Run in Spyder: runfile('mk_fig_extra.py')"""
import os, json, shutil, numpy as np, matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import style_nat as S; S.apply()
HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.normpath(os.path.join(HERE, "..", "figures")); os.makedirs(DST, exist_ok=True)
R = json.load(open(os.path.join(HERE, "robust_results.json")))
V = json.load(open(os.path.join(HERE, "variants_results.json")))
CLIM = ["CDMX", "Warm-subhumid", "Hot-arid"]; FX = 19.0
INS = "Concrete + EPS (insulated)"; CC = "SBC block (solid, city-cast)"
ORD = [INS, "Tepetate ashlar", "Adobe-type block", CC, "SBC block (solid)", "SBC block (hollow)", "Volcanic stone (recinto)"]
NAME = {INS: "Insulated concrete", "Tepetate ashlar": "Tepetate ashlar", "Adobe-type block": "Earth block", CC: "SBC block (city-cast)",
        "SBC block (solid)": "SBC block (solid)", "SBC block (hollow)": "SBC block (hollow)", "Volcanic stone (recinto)": "Volcanic stone"}
INK = S.INK; COMP = {"op": ("Operation (B6)", "#6d9cba"), "prod": ("Production (A1–A3)", "#3d4650"), "tr": ("Transport (A4)", "#b07a45")}

# ---------- Figure: decomposition of the lifetime offset ----------
fig, axes = plt.subplots(1, 3, figsize=(7.4, 3.5), sharey=True)
y = np.arange(len(ORD))[::-1]
for k, c in enumerate(CLIM):
    ax = axes[k]
    for yi, m in zip(y, ORD):
        b = R["BASE"][c][m]; pos, neg = 0.0, 0.0
        for key in ("op", "prod", "tr"):
            v = b[key]
            if v >= 0: ax.barh(yi, v, left=pos, height=0.62, color=COMP[key][1], linewidth=0, zorder=3); pos += v
            else: ax.barh(yi, v, left=neg, height=0.62, color=COMP[key][1], linewidth=0, zorder=3); neg += v
        ax.plot(b["dCO2"], yi, marker="D", ms=4.2, color="white", mec=INK, mew=0.9, zorder=5)
        ax.text(max(pos, b["dCO2"], 0) + 3.5, yi, f"{b['dCO2']:+.0f}", va="center", ha="left", fontsize=6.3, color=INK)
    ax.axvline(0, color=INK, lw=0.6, zorder=4)
    ax.set_yticks(y); ax.set_yticklabels([NAME[m] for m in ORD], fontsize=7)
    ax.set_xlim(-75, 72); ax.xaxis.grid(True, color=S.GRID, lw=0.5, zorder=0)
    ax.set_xlabel("t CO$_2$-eq per dwelling (50 years)", fontsize=7.4)
    S.despine(ax); S.panel(ax, "abc"[k], x=-0.02, y=1.02)
    ax.text(0.5, 1.02, S.CLIMLAB[c].split(" (")[0], transform=ax.transAxes, ha="center", va="bottom", fontsize=8.5)
H = [Patch(fc=COMP[k][1], label=COMP[k][0]) for k in ("op", "prod", "tr")] + \
    [Line2D([], [], marker="D", ls="none", color="white", mec=INK, mew=0.9, ms=4.5, label="Net offset")]
fig.legend(handles=H, loc="lower center", ncol=4, fontsize=7, frameon=False, bbox_to_anchor=(0.55, -0.005))
plt.tight_layout(rect=(0, 0.06, 1, 1)); plt.savefig(os.path.join(HERE, "nat_decomp.png")); plt.close()

# ---------- Figure: abatement cost ----------
# Shown in full colour only where the detached-dwelling offset is robust (Monte-Carlo P(dCO2>0) >= 0.9);
# other options with a positive base-case offset are drawn as small grey crosses (indicative only).
# Mid-terrace values (deterministic) are shown only for walls whose detached offset is robust.
WALLS = [INS, "Tepetate ashlar", "Adobe-type block", CC, "SBC block (solid)", "SBC block (hollow)"]
MK = {"CDMX": "o", "Warm-subhumid": "s", "Hot-arid": "^"}; OFF = {"CDMX": 0.22, "Warm-subhumid": 0.0, "Hot-arid": -0.22}
PMIN = 0.9
fig, ax = plt.subplots(figsize=(7.0, 3.6))
yy = np.arange(len(WALLS))[::-1]
for yi, m in zip(yy, WALLS):
    for c in CLIM:
        p = R["MC"][c][m]["pco2"]
        for var, filled in (("det", True), ("mid", False)):
            d = V["dwelling"][var][c][m]
            if d["dCO2"] <= 0.5: continue
            ac = d["dC"] / FX / d["dCO2"]; col = S.CLIMCOL[c]; x = np.clip(ac, -400, 700)
            if p < PMIN:
                if filled: ax.plot(x, yi + OFF[c], marker="x", ms=5, ls="none", color="#9a9a9a", mew=1.0, zorder=3)
                continue
            ax.plot(x, yi + OFF[c], marker=MK[c], ms=6.5 if filled else 6.0, ls="none",
                    color=col if filled else "white", mec=col, mew=1.2, zorder=4)
ax.axvline(0, color=INK, lw=0.7, zorder=3)
ax.axvline(190, color=S.MUT, lw=0.8, ls=(0, (4, 3)), zorder=2)
ax.text(198, yy[2] - 0.2, "Social cost of carbon\n(190 USD t$^{-1}$)", fontsize=6.6, color=S.MUT, va="top", ha="left")
ax.text(-395, yy[-1] - 0.5, "saves money", fontsize=6.6, color=S.MUT, va="center", ha="left", style="italic")
ax.text(15, yy[-1] - 0.5, "costs money", fontsize=6.6, color=S.MUT, va="center", ha="left", style="italic")
ax.set_yticks(yy); ax.set_yticklabels([NAME[m] for m in WALLS], fontsize=7.4); ax.set_ylim(yy[-1] - 0.8, yy[0] + 0.6)
ax.set_xlim(-400, 700); ax.xaxis.grid(True, color=S.GRID, lw=0.5, zorder=0)
ax.set_xlabel("Abatement cost (USD per t CO$_2$-eq avoided; societal view, 5%, 50 years)", fontsize=7.6)
S.despine(ax)
H = [Line2D([], [], marker=MK[c], ls="none", color=S.CLIMCOL[c], mec=S.CLIMCOL[c], ms=6, label=S.CLIMLAB[c].split(" (")[0]) for c in CLIM] + \
    [Line2D([], [], marker="o", ls="none", color="#777777", ms=6, label="Detached unit"),
     Line2D([], [], marker="o", ls="none", color="white", mec="#777777", mew=1.2, ms=6, label="Mid-terrace unit"),
     Line2D([], [], marker="x", ls="none", color="#9a9a9a", mew=1.0, ms=5, label="Offset not robust (P < 0.9)")]
ax.legend(handles=H, loc="lower right", fontsize=6.6, frameon=False, ncol=1)
plt.tight_layout(); plt.savefig(os.path.join(HERE, "nat_abatement.png")); plt.close()

for f in ("nat_decomp.png", "nat_abatement.png"): shutil.copy(os.path.join(HERE, f), os.path.join(DST, f))
# table of abatement costs for the text
for c in CLIM:
    print(c, {NAME[m]: {v: (round(V["dwelling"][v][c][m]["dCO2"], 1), round(V["dwelling"][v][c][m]["dC"] / FX / V["dwelling"][v][c][m]["dCO2"]) if V["dwelling"][v][c][m]["dCO2"] > 0.5 else None) for v in ("det", "mid")} for m in WALLS})
print("extra figures saved")
