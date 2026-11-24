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

# ---------- Figure: cost-effectiveness map (replaces the abatement-cost dot plot) ----------
# x: lifetime offset (t CO2-eq per dwelling), y: net present cost (k USD, societal view).
# Lines through the origin are iso-abatement-cost lines (0 and 190 USD/t); points below a line abate at a lower cost.
# Filled marker: detached dwelling; open marker: mid-terrace; a thin line joins the two for each wall.
WALLS = [INS, "Tepetate ashlar", "Adobe-type block", CC, "SBC block (solid)", "SBC block (hollow)", "Volcanic stone (recinto)"]
WCOL = {INS: "#3b5266", "Tepetate ashlar": S.MATCOL["Tepetate"], "Adobe-type block": S.MATCOL["Adobe"], CC: "#8a6d2f",
        "SBC block (solid)": S.MATCOL["SBC solid"], "SBC block (hollow)": "#b9a26a", "Volcanic stone (recinto)": S.MATCOL["Volcanic stone"]}
WMK = {INS: "s", "Tepetate ashlar": "o", "Adobe-type block": "D", CC: "P", "SBC block (solid)": "v", "SBC block (hollow)": "^", "Volcanic stone (recinto)": "X"}
SHORT = {INS: "Insulated", "Tepetate ashlar": "Tepetate", "Adobe-type block": "Earth", CC: "SBC city-cast",
         "SBC block (solid)": "SBC solid", "SBC block (hollow)": "SBC hollow", "Volcanic stone (recinto)": "Volcanic"}
fig, axes = plt.subplots(1, 3, figsize=(7.4, 3.6), sharey=True)
XL, YL = (-16, 62), (-7.0, 5.5)
for k, c in enumerate(CLIM):
    ax = axes[k]
    ax.fill_between([0, XL[1]], YL[0], 0, color="#eef3ef", zorder=0, lw=0)
    ax.axhline(0, color=INK, lw=0.6, zorder=1); ax.axvline(0, color=INK, lw=0.6, zorder=1)
    xs = np.linspace(0, XL[1], 10)
    ax.plot(xs, 190 * xs / 1000, color=S.MUT, lw=0.8, ls=(0, (4, 3)), zorder=1)
    ax.text(26, 190 * 26 / 1000 + 0.15, "190 USD t$^{-1}$", fontsize=6.0, color=S.MUT, ha="right", va="bottom")
    for m in WALLS:
        d = V["dwelling"]["det"][c][m]; q = V["dwelling"]["mid"][c][m]
        if m == "Volcanic stone (recinto)" and d["dCO2"] < XL[0]:
            continue
        xd, yd = d["dCO2"], d["dC"] / FX / 1000; xm, ym = q["dCO2"], q["dC"] / FX / 1000
        ax.plot([xd, xm], [yd, ym], color=WCOL[m], lw=0.7, alpha=0.6, zorder=2)
        ax.plot(xm, ym, marker=WMK[m], ms=5.0, ls="none", color="white", mec=WCOL[m], mew=1.0, zorder=3)
        ax.plot(xd, yd, marker=WMK[m], ms=6.0, ls="none", color=WCOL[m], mec="white", mew=0.5, zorder=4)
        DY = {("Warm-subhumid", INS): 0.5, ("Warm-subhumid", "Tepetate ashlar"): -0.35,
              ("Warm-subhumid", "SBC block (solid)"): 0.3, ("Warm-subhumid", CC): -0.3}
        DXL = {("Warm-subhumid", INS): -2.0, ("Hot-arid", INS): -1.5}
        if xd > 8:
            dx = DXL.get((c, m), 1.6); ha = "right" if dx < 0 else "left"
            ax.text(xd + dx, yd + DY.get((c, m), 0), SHORT[m], fontsize=6.0, color=INK, va="center", ha=ha, zorder=5)
    ax.set_xlim(*XL); ax.set_ylim(*YL); ax.grid(True, color=S.GRID, lw=0.5, zorder=0)
    ax.set_xlabel("Lifetime offset (t CO$_2$-eq per dwelling)", fontsize=7.2)
    S.despine(ax); S.panel(ax, "abc"[k], x=-0.02, y=1.02)
    ax.text(0.5, 1.02, S.CLIMLAB[c].split(" (")[0], transform=ax.transAxes, ha="center", va="bottom", fontsize=8.5)
    ax.text(1.0, YL[0] + 0.25, "less carbon, saves money", fontsize=6.0, color="#4f6f60", ha="left", va="bottom", style="italic")
axes[0].set_ylabel("Net present cost (k USD per dwelling)\nnegative = saving", fontsize=7.4)
H = [Line2D([], [], marker=WMK[m], ls="none", color=WCOL[m], mec="white", ms=6, label=SHORT[m]) for m in WALLS] + \
    [Line2D([], [], marker="o", ls="none", color="#777777", ms=6, label="Detached"),
     Line2D([], [], marker="o", ls="none", color="white", mec="#777777", mew=1.0, ms=5, label="Mid-terrace"),
     Line2D([], [], color=S.MUT, lw=0.8, ls=(0, (4, 3)), label="190 USD t$^{-1}$")]
fig.legend(handles=H, loc="lower center", ncol=5, fontsize=6.6, frameon=False, bbox_to_anchor=(0.53, -0.01), columnspacing=1.2, handletextpad=0.3)
plt.tight_layout(rect=(0, 0.11, 1, 1)); plt.savefig(os.path.join(HERE, "nat_abatement.png")); plt.close()

for f in ("nat_decomp.png", "nat_abatement.png"): shutil.copy(os.path.join(HERE, f), os.path.join(DST, f))
# table of abatement costs for the text
for c in CLIM:
    print(c, {NAME[m]: {v: (round(V["dwelling"][v][c][m]["dCO2"], 1), round(V["dwelling"][v][c][m]["dC"] / FX / V["dwelling"][v][c][m]["dCO2"]) if V["dwelling"][v][c][m]["dCO2"] > 0.5 else None) for v in ("det", "mid")} for m in WALLS})
print("extra figures saved")
