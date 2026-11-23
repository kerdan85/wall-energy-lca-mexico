"""Journal-style (Elsevier/Nature-like) matplotlib setup: Helvetica-class font
(TeX Gyre Heros), Okabe-Ito colourblind-safe palette, thin spines, no on-figure
titles (captions live in the LaTeX)."""
import matplotlib, matplotlib.pyplot as plt
import matplotlib.font_manager as fm

import os
_FD=os.path.join(os.path.dirname(os.path.abspath(__file__)),"fonts")
for _f in ["texgyreheros-regular.otf","texgyreheros-bold.otf","texgyreheros-italic.otf","texgyreheros-bolditalic.otf"]:
    try: fm.fontManager.addfont(os.path.join(_FD,_f))
    except Exception: pass

# Okabe-Ito colourblind-safe palette
BLUE="#3b5266"; VERM="#b07a45"; GREEN="#6f8f7f"; PURPLE="#55505c"; ORANGE="#c2a05c"
SKY="#56B4E9"; PINK="#CC79A7"; INK="#1a1a1a"; MUT="#555555"; GRID="#e2e2e2"
NPG=[VERM,BLUE,GREEN,PURPLE,ORANGE,SKY,PINK,"#7E6148"]   # kept name for compatibility
CLIMCOL={"CDMX":"#33414e","Warm-subhumid":"#93a4ad","Hot-arid":"#c0915a"}
MATCOL={"Tepetate":"#6f8f7f","Adobe":"#a9753f","Concrete":"#8c8c8c","Volcanic stone":"#3f434a","SBC solid":"#c2a05c","SBC hollow":"#dcc79a"}
CLIMLAB={"CDMX":"Mexico City (temperate-highland)","Warm-subhumid":"Mérida (warm-subhumid)",
         "Hot-arid":"Hermosillo (hot-arid)"}

def apply():
    plt.rcParams.update({
        "font.family":"TeX Gyre Heros","mathtext.fontset":"custom",
        "mathtext.rm":"TeX Gyre Heros","mathtext.it":"TeX Gyre Heros:italic",
        "mathtext.bf":"TeX Gyre Heros:bold",
        "font.size":8.5,"axes.titlesize":9,"axes.titleweight":"normal",
        "axes.labelsize":9,"axes.labelcolor":INK,"text.color":INK,
        "axes.edgecolor":"#4d4d4d","axes.linewidth":0.7,
        "xtick.color":"#4d4d4d","ytick.color":"#4d4d4d",
        "xtick.labelsize":8,"ytick.labelsize":8,
        "xtick.direction":"out","ytick.direction":"out",
        "xtick.major.size":3,"ytick.major.size":3,"xtick.major.width":0.7,"ytick.major.width":0.7,
        "axes.grid":False,"axes.axisbelow":True,"grid.color":GRID,"grid.linewidth":0.6,
        "legend.frameon":False,"legend.fontsize":8,"legend.handlelength":1.4,
        "figure.dpi":200,"savefig.dpi":400,"svg.fonttype":"none",
    })

def panel(ax,label,x=-0.11,y=1.03):
    ax.text(x,y,label,transform=ax.transAxes,fontsize=10,fontweight="bold",va="bottom",ha="right")

def despine(ax):
    ax.spines[["top","right"]].set_visible(False)
