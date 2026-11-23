"""Replay the 13 original DesignBuilder runs (Mexico City) with the rebuilt model and report
NMBE and CV(RMSE) as in ASHRAE Guideline 14.  Usage: python calib.py"""
import json,sys,os
from multiprocessing import Pool
import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import runner
db=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'db_runs.json')))
# thickness, density, cp per DB wall (sustainable-walls dataset / materials DB); k from the run's own no-film U
PROPS={'block_hueco-rosa':(0.12,1300,1000),'concreto_hueco':(0.12,1300,880),'concreto_solido':(0.12,2300,880),
 'recinto_negro':(0.12,1900,850),'rojo':(0.14,1800,880),'sbc_solid':(0.12,1450,1000),'sbc_hollow':(0.15,1300,1000),
 'sillar_tepetate':(0.20,1500,900)}
CASES=[]
for k,r in db.items():
    if k=='tabique_concreto_solido_real': continue   # mislabeled duplicate of block hueco rosa
    base=k.replace('tabique_','').replace('_REAL','')
    t,rho,cp=PROPS[base]
    CASES.append(dict(name=k,wall=dict(t=t,k=round(r['Unf']*t,4),rho=rho,cp=cp,abs=round(1-r['refl'],2)),H=r['heat_m2'],C=r['cool_m2']))
def one(a):
    params,c=a
    pp=dict(params); pp['wall']=c['wall']
    r=runner.run(pp,tag=None)
    return c['name'],r['heat'],r['cool'],c['H'],c['C']
def evaluate(params,verbose=True):
    with Pool(min(len(CASES),os.cpu_count())) as P: out=P.map(one,[(params,c) for c in CASES])
    import math
    eh=[h-H for _,h,c,H,C in out]; ec=[c-C for _,h,c,H,C in out]; et=[(h+c)-(H+C) for _,h,c,H,C in out]
    mH=sum(H for *_,H,C in out)/len(out); mT=sum(H+C for *_,H,C in out)/len(out)
    rm=lambda e:math.sqrt(sum(x*x for x in e)/len(e))
    stats=dict(nmbe_h=100*sum(eh)/len(eh)/mH, cvrmse_h=100*rm(eh)/mH, rmse_c=rm(ec), cvrmse_t=100*rm(et)/mT, nmbe_t=100*sum(et)/len(et)/mT)
    if verbose:
        for n,h,c,H,C in out: print(f"  {n:32s} H {h:6.2f} vs {H:6.2f}   C {c:6.2f} vs {C:6.2f}")
        print('  ',{k:round(v,2) for k,v in stats.items()})
    return stats,out
if __name__=='__main__':
    from run_36 import CALIBRATED
    evaluate(dict(CALIBRATED, ground_temp=18.0))
