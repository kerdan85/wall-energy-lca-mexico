import os; os.chdir(os.path.dirname(os.path.abspath(__file__)))
import json, sim_engine as S
UT={"Concrete (ref.)":3.00,"Adobe-type block":2.44,"Volcanic stone (recinto)":3.29,"Tepetate ashlar":2.21,"SBC block (solid)":2.59,"SBC block (hollow)":1.99}
meas=json.load(open("sim_results.json")); out={}
for c in S.CLIM:
    out[c]={}
    for m in S.ORDER:
        U,tk,rho,cp=S.MAT[m]; S.MAT[m]=(UT[m],tk,rho,cp)
        r=S.simulate(m,c); S.MAT[m]=(U,tk,rho,cp)
        out[c][m]=float(r["total"])
        print(c[:5],m[:14],f"tab {r['total']:.1f} meas {meas[c][m]['total']:.1f} err {100*(r['total']-meas[c][m]['total'])/meas[c][m]['total']:+.0f}%")
json.dump(out,open("sim_results_tab.json","w"),indent=1)
