#!/usr/bin/env python3
"""
Reduced-order dynamic building energy model (ISO 13790:2008 simple hourly, 5R1C)
for the SECTEI case-study dwelling. Takes measured U-values AND thermal inertia
(areal heat capacity) per wall material, so that two walls with the same U but
different mass give different demand and comfort. Runs 6 materials x 3 climates.
"""
import numpy as np

# ----------------------------------------------------------------------
# 1. CASE-STUDY DWELLING GEOMETRY (Casa Los Heroes archetype)
# ----------------------------------------------------------------------
Af   = 73.45          # conditioned floor area [m2]
Aw_g = 176.53         # gross external wall area [m2]
Awin = 12.0           # window area [m2]  (~7% of gross wall, small social-housing windows)
Aw   = Aw_g - Awin    # opaque wall area [m2]
Aroof= Af             # roof area [m2]
Afloor= Af            # ground floor area [m2]
Vol  = Af * 2.5       # conditioned volume [m3]

# fixed envelope elements (not varied by wall material)
U_win  = 5.7; g_win = 0.70          # single glazing, aluminium frame
U_roof = 1.80; rho_roof=2000; cp_roof=900   # uninsulated concrete slab roof
U_floor= 1.20; rho_floor=2000; cp_floor=900 # slab-on-ground
d_eff  = 0.10        # effective (daily) penetration thickness for mass [m]

# internal gains and ventilation (calibrated so concrete-CDMX reproduces the
# companion EnergyPlus baseline, ~47 kWh/m2.yr)
q_int = 5.0                       # internal gains [W/m2 floor] (occupancy+appliances+lighting)
ACH   = 0.5                       # air changes per hour (infiltration+ventilation)
Hve   = 0.33 * ACH * Vol          # ventilation conductance [W/K]

# comfort / control: heating to 20 degC in occupied hours with night setback ->
# effective heating base ~17 degC; cooling to 26 degC
T_heat = 17.04; T_cool = 26.0      # effective setpoints [degC]
T_cmf_lo, T_cmf_hi = 18.0, 27.0   # free-floating comfort band for % comfort hours

# opaque solar / sky terms (ISO 13790)
ALPHA=0.6; RSE=0.04; HR=4.5; DT_SKY=11.0
# ISO 13790 fixed coefficients
his = 3.45; hms = 9.1
Atot = 4.5 * Af                   # total internal surface area [m2]

# ----------------------------------------------------------------------
# 2. WALL MATERIALS  (measured U from Table props; density/cp estimated)
#    kappa = rho*cp*d_eff  -> areal heat capacity [J/m2K]
# ----------------------------------------------------------------------
# name: (U_meas [W/m2K], thickness[m], rho[kg/m3], cp[J/kgK])
MAT = {
 "Concrete (ref.)":        (2.16, 0.12, 1200, 880),
 "Adobe-type block":       (2.07, 0.12, 1600, 1000),
 "Volcanic stone (recinto)":(2.73,0.12, 1400, 900),
 "Tepetate ashlar":        (1.50, 0.20, 1500, 1000),
 "SBC block (solid)":      (1.89, 0.12, 1250, 1000),
 "SBC block (hollow)":     (2.21, 0.15,  900, 1000),  # air voids -> low mass
}
ORDER = list(MAT.keys())

def kappa(rho, cp, t):
    return rho*cp*min(t, d_eff)   # J/m2K

# fixed-element capacities
kap_roof  = kappa(rho_roof, cp_roof, 0.12)
kap_floor = kappa(rho_floor, cp_floor, 0.15)

# ----------------------------------------------------------------------
# 3. CLIMATE GENERATOR (representative hourly TMY-like year, 8760 h)
#    monthly mean air temp + diurnal amplitude + clear-sky solar on window
# ----------------------------------------------------------------------
def climate(name):
    # monthly mean dry-bulb [degC] and diurnal half-amplitude [K], peak GHI [W/m2]
    if name == "CDMX":            # Koppen Cwb, temperate highland, heating-dominated
        Tmon = [13.5,15,16.5,18,18.5,17.5,16.5,16.5,16,15.5,14.5,13.5]
        amp  = 7.0;  ghi = 620; cloud=0.75
    elif name == "Warm-subhumid": # Koppen Aw, cooling-dominated
        Tmon = [23.5,24.5,26.5,28,29,28.5,28,28,27.5,26.5,25,23.5]
        amp  = 6.0;  ghi = 520; cloud=0.60
    elif name == "Hot-arid":      # Koppen BWh, strong cooling + mild winter heating
        Tmon = [17,18.5,20.5,23.5,27.5,32,32.5,32,31,26.5,21,17]
        amp  = 8.0;  ghi = 720; cloud=0.85
    else:
        raise ValueError(name)
    hours=np.arange(8760)
    day=hours//24; hod=hours%24
    month=np.clip((day//30.4).astype(int),0,11)
    Tm=np.array(Tmon)[month]
    # diurnal: min ~06h, max ~15h
    Te = Tm + amp*np.sin(2*np.pi*(hod-9)/24)
    # solar on vertical window (clear-sky bell, daytime only), with cloud factor
    sol = np.where((hod>=7)&(hod<=18), np.sin(np.pi*(hod-7)/11), 0.0)
    Isol_win = ghi*cloud*np.clip(sol,0,None)*0.55   # 0.55 vertical/rough orientation factor
    Ihor = ghi*cloud*np.clip(sol,0,None)
    return Te, Isol_win, Ihor

# ----------------------------------------------------------------------
# 4. 5R1C HOURLY SOLVER (ISO 13790 simple hourly method)
# ----------------------------------------------------------------------
def simulate(matname, climname):
    U,tk,rho,cp = MAT[matname]
    kap_wall = kappa(rho,cp,tk)
    # opaque transmission (walls+roof+floor); windows handled as Htr_w
    Htr_op = U*Aw + U_roof*Aroof + U_floor*Afloor
    Htr_w  = U_win*Awin
    # thermal capacitance of the zone (sum kappa*A of mass-active surfaces)
    areas=[Aw,Aroof,Afloor]; kaps=[kap_wall,kap_roof,kap_floor]
    Cm = sum(k*a for k,a in zip(kaps,areas))             # J/K
    Am = Cm**2 / sum((k**2)*a for k,a in zip(kaps,areas)) # effective mass area m2
    Am = min(Am, Atot)
    Htr_ms = hms*Am
    Htr_em = 1.0/(1.0/Htr_op - 1.0/Htr_ms)
    Htr_is = his*Atot

    Te, Isol, Ihor = climate(climname)
    Phi_int = q_int*Af
    Phi_sol = g_win*Isol*Awin*0.9*0.7   # frame+shading factors
    # opaque elements (ISO 13790 11.3.4): absorbed solar minus extra long-wave loss to the sky
    Phi_sol = Phi_sol + ALPHA*RSE*(U*Aw*Isol + U_roof*Aroof*Ihor) \
              - RSE*HR*DT_SKY*(0.5*U*Aw + 1.0*U_roof*Aroof)
    Phi_i   = Phi_int + Phi_sol          # total gains per hour [W]

    # gain split (ISO 13790)
    Phi_ia = 0.5*Phi_int
    Phi_m  = (Am/Atot)*(0.5*Phi_int + Phi_sol)
    Phi_st = (1 - Am/Atot - Htr_w/(9.1*Atot))*(0.5*Phi_int + Phi_sol)

    Htr_1 = 1.0/(1.0/Hve + 1.0/Htr_is)
    Htr_2 = Htr_1 + Htr_w
    Htr_3 = 1.0/(1.0/Htr_2 + 1.0/Htr_ms)
    Cm_h  = Cm/3600.0

    def air_temp(Tm_prev, te, phi_ia, phi_st, phi_m, PhiHC):
        Tsup=te
        Phi_mtot = (phi_m + Htr_em*te + Htr_3*(phi_st + Htr_w*te
                   + Htr_1*(((phi_ia+PhiHC)/Hve)+Tsup))/Htr_2)
        Tm_t = (Tm_prev*(Cm_h-0.5*(Htr_3+Htr_em)) + Phi_mtot)/(Cm_h+0.5*(Htr_3+Htr_em))
        Tm = 0.5*(Tm_t+Tm_prev)
        Ts = (Htr_ms*Tm + phi_st + Htr_w*te + Htr_1*(Tsup+(phi_ia+PhiHC)/Hve))/(Htr_ms+Htr_w+Htr_1)
        Tair = (Htr_is*Ts + Hve*Tsup + phi_ia + PhiHC)/(Htr_is+Hve)
        return Tair, Tm_t

    Tm_prev = 18.0
    H=np.zeros(8760); C=np.zeros(8760); Tair_free=np.zeros(8760)
    for h in range(8760):
        te=Te[h]; pia=Phi_ia; pst=Phi_st[h]; pm=Phi_m[h]
        # unconditioned air temp
        T0,_ = air_temp(Tm_prev, te, pia, pst, pm, 0.0)
        Tair_free[h]=T0
        if T0 < T_heat:   setp=T_heat
        elif T0 > T_cool: setp=T_cool
        else:
            _,Tm_prev = air_temp(Tm_prev,te,pia,pst,pm,0.0); H[h]=0; C[h]=0; continue
        # ISO interpolation with 10 W/m2 test load
        Phi10=10*Af
        T10,_=air_temp(Tm_prev,te,pia,pst,pm,Phi10)
        PhiHC = Phi10*(setp-T0)/(T10-T0)
        _,Tm_prev = air_temp(Tm_prev,te,pia,pst,pm,PhiHC)
        if PhiHC>0: H[h]=PhiHC
        else: C[h]=-PhiHC
    heat=H.sum()/1000.0/Af       # kWh/m2a
    cool=C.sum()/1000.0/Af
    comfort=100.0*np.mean((Tair_free>=T_cmf_lo)&(Tair_free<=T_cmf_hi))
    peak=max(H.max(),C.max())/Af # W/m2
    return dict(heat=heat,cool=cool,total=heat+cool,comfort=comfort,peak=peak,
                U=U,Cm=Cm/1e6,Am=Am)

# ----------------------------------------------------------------------
# 5. RUN & REPORT
# ----------------------------------------------------------------------
CLIM=["CDMX","Warm-subhumid","Hot-arid"]
if __name__=="__main__":
    import json
    res={}
    for c in CLIM:
        print(f"\n=== {c} ===")
        print(f"{'material':26s} {'U':>4s} {'Cm(MJ)':>7s} {'heat':>6s} {'cool':>6s} {'tot':>6s} {'cmf%':>5s} {'peak':>5s}")
        res[c]={}
        for m in ORDER:
            r=simulate(m,c); res[c][m]=r
            print(f"{m:26s} {r['U']:.2f} {r['Cm']:7.1f} {r['heat']:6.1f} {r['cool']:6.1f} {r['total']:6.1f} {r['comfort']:5.1f} {r['peak']:5.0f}")
    import os; json.dump(res,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'sim_results.json'),'w'),indent=1)
    print("\nsaved sim_results.json")
