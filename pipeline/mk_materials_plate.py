#!/usr/bin/env python3
"""Materials plate: a square photo of each of the six tested wall materials."""
import os
HERE=os.path.dirname(os.path.abspath(__file__))
OUT=HERE; DST=os.path.normpath(os.path.join(HERE,"..","figures")); os.makedirs(DST,exist_ok=True)
import matplotlib.pyplot as plt
from PIL import Image, ImageOps
import style_nat as S; S.apply()




ITEMS=[  # (label, path, sublabel)
 ("Concrete block (reference)",f"{OUT}/assets/mat/concreto.jpg","solid, 0.12 m"),
 ("Adobe-type block",f"{OUT}/assets/mat/adobe.jpg","compressed earth, 0.12 m"),
 ("Volcanic stone (recinto)",f"{OUT}/assets/mat/recinto.jpg","quarried, 0.12 m"),
 ("Tepetate ashlar",f"{OUT}/assets/mat/tepetate.jpg","cut tuff, 0.20 m"),
 ("SBC block (solid)",f"{OUT}/assets/mat/sbc_solid.jpg","35% sargassum, 0.12 m"),
 ("SBC block (hollow)",f"{OUT}/assets/mat/sbc_hollow.jpg","35% sargassum, 0.15 m"),
]
def sq(path,n=760):
    im=Image.open(path).convert("RGB"); im=ImageOps.exif_transpose(im)
    return ImageOps.fit(im,(n,n),Image.LANCZOS,centering=(0.5,0.5))

fig,axes=plt.subplots(2,3,figsize=(7.2,5.3))
for ax,(lab,p,sub) in zip(axes.ravel(),ITEMS):
    ax.imshow(sq(p)); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_edgecolor("#b9b9b9"); s.set_linewidth(0.8)
    ax.set_title(lab,fontsize=9,pad=3,loc="center")
    ax.text(0.5,-0.055,sub,transform=ax.transAxes,ha="center",va="top",fontsize=7.5,color=S.MUT)
plt.tight_layout(h_pad=1.8,w_pad=0.8)
plt.savefig(f"{OUT}/nat_materials.png",dpi=300,facecolor="white",bbox_inches="tight")
import os; __import__("shutil").copy(f"{OUT}/nat_materials.png",f"{DST}/nat_materials.png")
print("materials plate saved")
