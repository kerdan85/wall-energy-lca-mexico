"""Rebuild the Casa Los Heroes DesignBuilder model as an EnergyPlus 25.1 IDF.

Geometry, constructions, glazing and internal-gain densities are taken from the
EnergyPlus summary tables written by the original DesignBuilder runs (db_runs.json) and
from the DesignBuilder model. Operation (schedules, ventilation) follows the DesignBuilder
dwelling templates and is calibrated against the 13 original Mexico City runs (calib.py).
"""
import math

W = 3.5                                   # house width (x, east-west), m
H = 2.8                                   # floor-to-floor height, m
GF = [("Z1", 3.9114), ("Z4", 1.5829), ("Z5", 2.3714), ("Z2", 1.0571), ("Z3", 3.0800)]  # south -> north
UF = [("Z1", 3.9114), ("Z4", 1.5829), ("Z5", 1.3400), ("Z2", 2.0886), ("Z3", 3.0800)]
BAY_X0, BAY_D = 1.432, 0.522              # upper-floor south bay (BLOCK1), x 1.432-3.5, y -0.522-0

# net floor area [m2] and volume [m3] of each zone as modelled by DesignBuilder (Zone Summary)
ZONE_AV = {"PB:Z1": (11.27, 31.55), "PB:Z4": (4.44, 12.43), "PB:Z3": (8.69, 24.34), "PB:Z5": (6.89, 19.29),
           "PB:Z2": (2.81, 7.86), "PA:Z1": (11.50, 31.04), "PA:Z4": (4.44, 11.99), "PA:Z3": (8.69, 23.47),
           "PA:Z5": (3.69, 9.95), "PA:Z2": (6.01, 16.24), "BAY": (0.41, 1.08)}
AREA_NORM = 73.45                         # m2, conditioned area used to normalise results in the papers
# room use of each zone (DesignBuilder dwelling activities)
USE = {"PB:Z1": "common", "PB:Z4": "common", "PB:Z3": "kitchen", "PB:Z5": "bed", "PB:Z2": "circ",
       "PA:Z1": "bed", "PA:Z4": "bed", "PA:Z3": "toilet", "PA:Z5": "bed", "PA:Z2": "circ", "BAY": "common"}
# lighting W/m2, m2 per person, equipment W/m2 (Zone Summary of the DesignBuilder runs)
GAINS = {"common": (5.0, 50.90, 2.16), "kitchen": (7.5, 42.19, 30.28), "bed": (5.0, 43.59, 3.58),
         "circ": (5.0, 64.50, 1.57), "toilet": (5.0, 41.12, 1.61)}


def fmt(obj, fields):
    s = obj + ",\n"
    for i, f in enumerate(fields):
        s += "    " + str(f) + (";\n" if i == len(fields) - 1 else ",\n")
    return s + "\n"


def verts(pts):
    return [len(pts)] + [f"{p[0]:.4f},{p[1]:.4f},{p[2]:.4f}" for p in pts]


def wall_pts(A, B, z0, z1):
    """A=left, B=right bottom corners seen from outside; returns UL, LL, LR, UR."""
    return [(A[0], A[1], z1), (A[0], A[1], z0), (B[0], B[1], z0), (B[0], B[1], z1)]


def floor_pts(x0, x1, y0, y1, z):   # normal down
    return [(x0, y0, z), (x0, y1, z), (x1, y1, z), (x1, y0, z)]


def roof_pts(x0, x1, y0, y1, z):    # normal up
    return [(x0, y1, z), (x0, y0, z), (x1, y0, z), (x1, y1, z)]


def schedule_compact(name, typ, rules):
    """rules: list of (daytype string, [(until_hour, value), ...]) for the whole year."""
    f = [name, typ, "Through: 12/31"]
    for dt, prof in rules:
        f.append("For: " + dt)
        for hh, v in prof:
            f += [f"Until: {hh:02d}:00", v]
    return fmt("Schedule:Compact", f)


def hourly_profile(on_hours, base=0.0, scale=1.0):
    """on_hours: set of hours (0-23) at value 1; others at base; returned as until-list."""
    vals = [(1.0 if h in on_hours else base) * scale for h in range(24)]
    out, cur = [], vals[0]
    for h in range(1, 25):
        if h == 24 or abs(vals[h] - cur) > 1e-9:
            out.append((h, round(min(cur, 1.0), 4)))
            if h < 24:
                cur = vals[h]
    return out


def build(params):
    p = dict(DEFAULTS)
    p.update(params)
    o = []
    o.append(fmt("Version", ["25.1"]))
    o.append(fmt("SimulationControl", ["No", "No", "No", "No", "Yes", "No", 1]))
    o.append(fmt("Building", ["Casa Los Heroes", 0, "Suburbs", 0.04, 0.4, "FullExterior", 25, 6]))
    o.append(fmt("ShadowCalculation", ["PolygonClipping", "Periodic", 20, 15000]))
    o.append(fmt("SurfaceConvectionAlgorithm:Inside", ["TARP"]))
    o.append(fmt("SurfaceConvectionAlgorithm:Outside", ["DOE-2"]))
    o.append(fmt("HeatBalanceAlgorithm", ["ConductionTransferFunction", 200]))
    o.append(fmt("Timestep", [p["timestep"]]))
    o.append(fmt("RunPeriod", ["Annual", 1, 1, "", 12, 31, "", "Sunday", "No", "No", "No", "Yes", "Yes"]))
    if p["dst"]:
        o.append(fmt("RunPeriodControl:DaylightSavingTime", ["1st Sunday in April", "Last Sunday in October"]))
    o.append(fmt("GlobalGeometryRules", ["UpperLeftCorner", "Counterclockwise", "World"]))
    gt = p["ground_temp"]
    o.append(fmt("Site:GroundTemperature:BuildingSurface", [gt] * 12))

    # ---------------- materials and constructions ----------------
    wm = p["wall"]   # dict t, k, rho, cp, abs; optional "outer": list of extra layers (t, k, rho, cp), outside first
    wall_layers = []
    for i, (t_, k_, r_, c_) in enumerate(wm.get("outer", [])):
        a_ = wm["abs"] if i == 0 else 0.6
        o.append(fmt("Material", [f"WALL_OUT{i}", "MediumRough", t_, k_, r_, c_, 0.9, a_, a_]))
        wall_layers.append(f"WALL_OUT{i}")
    o.append(fmt("Material", ["WALL_MAT", "MediumRough", wm["t"], wm["k"], wm["rho"], wm["cp"], 0.9,
                              wm["abs"], wm["abs"]]))
    wall_layers.append("WALL_MAT")
    mats = [
        ("ASPHALT", 0.010, 0.70, 2100, 1000, 0.85), ("ROOF_INSUL", 0.1445, 0.0381, 12, 840, 0.6),
        ("PLASTERBOARD", 0.013, 0.25, 900, 1000, 0.6), ("FLOOR_INSUL", 0.1327, 0.04, 15, 1400, 0.6),
        ("CAST_CONCRETE", 0.100, 1.13, 2000, 1000, 0.6), ("SCREED", 0.070, 0.41, 1200, 840, 0.6),
        ("TIMBER_FLOOR", 0.030, 0.14, 650, 1200, 0.6), ("INT_FLOOR_CONC", 0.100, 1.40, 2100, 840, 0.6),
        ("GYPSUM", 0.025, 0.25, 900, 1000, 0.5), ("DOOR_WOOD", 0.035, 0.19, 700, 2390, 0.6)]
    for n, t, k, r, c, a in mats:
        o.append(fmt("Material", [n, "MediumRough", t, k, r, c, 0.9, a, a]))
    o.append(fmt("Material:AirGap", ["AIRGAP", 0.15]))
    o.append(fmt("WindowMaterial:Glazing", ["CLEAR_6MM", "SpectralAverage", "", 0.006, 0.775, 0.071, 0.071,
                                            0.881, 0.080, 0.080, 0, 0.84, 0.84, 0.9]))
    cons = [("EXT_WALL", wall_layers), ("FLAT_ROOF", ["ASPHALT", "ROOF_INSUL", "PLASTERBOARD"]),
            ("GROUND_FLOOR", ["FLOOR_INSUL", "CAST_CONCRETE", "SCREED", "TIMBER_FLOOR"]),
            ("EXT_FLOOR", ["FLOOR_INSUL", "CAST_CONCRETE", "SCREED", "TIMBER_FLOOR"]),
            ("INT_FLOOR", ["INT_FLOOR_CONC"]), ("INT_CEILING", ["INT_FLOOR_CONC"]),
            ("PARTITION", ["GYPSUM", "AIRGAP", "GYPSUM"]), ("EXT_DOOR", ["DOOR_WOOD"]),
            ("WIN_SGL", ["CLEAR_6MM"])]
    for n, L in cons:
        o.append(fmt("Construction", [n] + L))
    o.append(fmt("WindowProperty:FrameAndDivider", ["FRAME", 0.04, 0, 0, 9.5, 1, 0.7, 0.7, 0.9, "DividedLite",
                                                     0.045, 0, 1, 0, 0, 9.5, 1, 0.7, 0.7, 0.9]))

    # ---------------- schedules ----------------
    o.append(fmt("ScheduleTypeLimits", ["Fraction", 0, 1, "Continuous"]))
    o.append(fmt("ScheduleTypeLimits", ["Any", "", "", "Continuous"]))
    allday = lambda v: [("AllDays", [(24, v)])]
    o.append(schedule_compact("ON", "Fraction", allday(1)))
    o.append(schedule_compact("ACT", "Any", allday(p["activity_W"])))
    for use, hrs in p["hvac_hours"].items():
        on = hourly_profile(hrs)
        o.append(schedule_compact(f"{use}_HEAT_SP".upper(), "Any",
                                  [("AllDays", [(h, p["heat_sp"] if v > 0.5 else p["heat_sb"]) for h, v in on])]))
        onc = hourly_profile(p["cool_hours"].get(use, hrs) if p.get("cool_hours") else hrs)
        o.append(schedule_compact(f"{use}_COOL_SP".upper(), "Any",
                                  [("AllDays", [(h, p["cool_sp"] if v > 0.5 else p["cool_sb"]) for h, v in onc])]))
        o.append(fmt("ThermostatSetpoint:DualSetpoint", [f"{use}_DUALSP".upper(), f"{use}_HEAT_SP".upper(),
                                                         f"{use}_COOL_SP".upper()]))
    o.append(schedule_compact("DUAL", "Any", allday(4)))
    # natural ventilation availability: summer months only (May-Sep) during occupied/day hours
    nv = ["NATVENT", "Fraction"] + ([] if p.get("natvent_allyear") else
                                    ["Through: 4/30", "For: AllDays", "Until: 24:00", 0]) + ["Through: 9/30", "For: AllDays"]
    for hh, v in hourly_profile(p["natvent_hours"]):
        nv += [f"Until: {hh:02d}:00", v]
    if p.get("natvent_allyear"):
        nv += ["Through: 12/31", "For: AllDays"] + sum([[f"Until: {hh:02d}:00", v] for hh, v in hourly_profile(p["natvent_hours"])], [])
    else:
        nv += ["Through: 12/31", "For: AllDays", "Until: 24:00", 0]
    o.append(fmt("Schedule:Compact", nv))
    o.append(schedule_compact("NV_TMIN", "Any", allday(p["natvent_setpoint"])))
    for use, prof in SCHED.items():
        for kind in ("occ", "light", "equip"):
            o.append(schedule_compact(f"{use}_{kind}".upper(), "Fraction", [("AllDays", prof[kind])]))

    o.append(fmt("DesignSpecification:OutdoorAir", ["OA_SPEC", "Flow/Person", p["oa_per_person"], 0, 0, 0]))

    # ---------------- zones and surfaces ----------------
    surfaces, subs = [], []

    def add_zone(zn):
        a, v = ZONE_AV[zn]
        o.append(fmt("Zone", [zn, 0, 0, 0, 0, 1, 1, "autocalculate", v, a]))

    def surf(name, typ, cons_, zone, bc, bco, sun, wind, pts):
        surfaces.append(fmt("BuildingSurface:Detailed", [name, typ, cons_, zone, "", bc, bco, sun, wind,
                                                          "autocalculate"] + verts(pts)))

    def interzone(n1, z1, n2, z2, typ1, typ2, pts1, c1, c2):
        surf(n1, typ1, c1, z1, "Surface", n2, "NoSun", "NoWind", pts1)
        surf(n2, typ2, c2, z2, "Surface", n1, "NoSun", "NoWind", list(reversed(pts1)))

    def storey(prefix, layout, z0):
        y = 0.0
        bounds = []
        for zid, d in layout:
            zn = f"{prefix}:{zid}"
            add_zone(zn)
            y0, y1 = y, y + d
            bounds.append((zn, y0, y1))
            surf(f"{zn}_E", "Wall", "EXT_WALL", zn, "Outdoors", "", "SunExposed", "WindExposed",
                 wall_pts((W, y0), (W, y1), z0, z0 + H))
            surf(f"{zn}_W", "Wall", "EXT_WALL", zn, "Outdoors", "", "SunExposed", "WindExposed",
                 wall_pts((0, y1), (0, y0), z0, z0 + H))
            y = y1
        return bounds

    gb = storey("PB", GF, 0.0)
    ub = storey("PA", UF, H)
    add_zone("BAY")
    # ground floors and roofs
    for zn, y0, y1 in gb:
        surf(f"{zn}_FLOOR", "Floor", "GROUND_FLOOR", zn, "Ground", "", "NoSun", "NoWind",
             floor_pts(0, W, y0, y1, 0.0))
    for zn, y0, y1 in ub:
        surf(f"{zn}_ROOF", "Roof", "FLAT_ROOF", zn, "Outdoors", "", "SunExposed", "WindExposed",
             roof_pts(0, W, y0, y1, 2 * H))
    # south and north end walls
    surf("PB:Z1_S", "Wall", "EXT_WALL", "PB:Z1", "Outdoors", "", "SunExposed", "WindExposed",
         wall_pts((0, 0), (W, 0), 0, H))
    surf("PB:Z3_N", "Wall", "EXT_WALL", "PB:Z3", "Outdoors", "", "SunExposed", "WindExposed",
         wall_pts((W, gb[-1][2]), (0, gb[-1][2]), 0, H))
    surf("PA:Z3_N", "Wall", "EXT_WALL", "PA:Z3", "Outdoors", "", "SunExposed", "WindExposed",
         wall_pts((W, ub[-1][2]), (0, ub[-1][2]), H, 2 * H))
    surf("PA:Z1_S", "Wall", "EXT_WALL", "PA:Z1", "Outdoors", "", "SunExposed", "WindExposed",
         wall_pts((0, 0), (BAY_X0, 0), H, 2 * H))
    # partitions between consecutive zones of each storey (wall of zone i facing north)
    for b in (gb, ub):
        for (za, _, ya1), (zb, _, _) in zip(b[:-1], b[1:]):
            interzone(f"{za}_PN", za, f"{zb}_PS", zb, "Wall", "Wall",
                      wall_pts((W, ya1), (0, ya1), b is ub and H or 0, (b is ub and H or 0) + H),
                      "PARTITION", "PARTITION")
    # intermediate floor: split by overlap of ground and upper zones
    k = 0
    for gz, gy0, gy1 in gb:
        for uz, uy0, uy1 in ub:
            a, c = max(gy0, uy0), min(gy1, uy1)
            if c - a > 1e-3:
                k += 1
                interzone(f"{gz}_CEIL{k}", gz, f"{uz}_FLOOR{k}", uz, "Ceiling", "Floor",
                          roof_pts(0, W, a, c, H), "INT_CEILING", "INT_FLOOR")
    # bay (BLOCK1) on the upper floor, south
    x0, x1, yb = BAY_X0, W, -BAY_D
    surf("BAY_S", "Wall", "EXT_WALL", "BAY", "Outdoors", "", "SunExposed", "WindExposed",
         wall_pts((x0, yb), (x1, yb), H, 2 * H))
    surf("BAY_E", "Wall", "EXT_WALL", "BAY", "Outdoors", "", "SunExposed", "WindExposed",
         wall_pts((x1, yb), (x1, 0), H, 2 * H))
    surf("BAY_W", "Wall", "EXT_WALL", "BAY", "Outdoors", "", "SunExposed", "WindExposed",
         wall_pts((x0, 0), (x0, yb), H, 2 * H))
    surf("BAY_FLOOR", "Floor", "EXT_FLOOR", "BAY", "Outdoors", "", "NoSun", "WindExposed",
         floor_pts(x0, x1, yb, 0, H))
    surf("BAY_ROOF", "Roof", "FLAT_ROOF", "BAY", "Outdoors", "", "SunExposed", "WindExposed",
         roof_pts(x0, x1, yb, 0, 2 * H))
    interzone("PA:Z1_PBAY", "PA:Z1", "BAY_PN", "BAY", "Wall", "Wall",
              wall_pts((x0, 0), (x1, 0), H, 2 * H), "PARTITION", "PARTITION")
    # windows (glass area as in the DesignBuilder runs) and door, south facade
    def window(name, parent, x0_, wdt, z0_, hgt, y=0.0):
        subs.append(fmt("FenestrationSurface:Detailed", [name, "Window", "WIN_SGL", parent, "", "autocalculate",
                                                         "FRAME", 1] + verts(wall_pts((x0_, y), (x0_ + wdt, y), z0_, z0_ + hgt))))
    window("PB:Z1_WIN", "PB:Z1_S", 0.35, 1.45, 0.85, 1.331 * 1.032)
    window("PA:Z1_WIN", "PA:Z1_S", 0.12, 1.15, H + 0.50, 1.927 * 1.0)
    subs.append(fmt("FenestrationSurface:Detailed", ["PB:Z1_DOOR", "Door", "EXT_DOOR", "PB:Z1_S", "", "autocalculate",
                                                     "", 1] + verts(wall_pts((2.35, 0), (3.25, 0), 0.0, 2.078))))
    o += surfaces + subs

    # ---------------- internal gains, infiltration, ventilation, HVAC ----------------
    zones = [z for z, _, _ in gb] + [z for z, _, _ in ub] + ["BAY"]
    for zn in zones:
        use = USE[zn]
        lpd, m2pp, epd = GAINS[use]
        U = use.upper()
        o.append(fmt("People", [f"{zn}_PEOPLE", zn, f"{U}_OCC", "Area/Person", "", "", m2pp, 0.3,
                                "autocalculate", "ACT"]))
        o.append(fmt("Lights", [f"{zn}_LIGHTS", zn, f"{U}_LIGHT", "Watts/Area", "", lpd, "", 0, 0.42, 0.18, 1]))
        o.append(fmt("ElectricEquipment", [f"{zn}_EQUIP", zn, f"{U}_EQUIP", "Watts/Area", "", epd, "", 0, 0.2, 0]))
        o.append(fmt("ZoneInfiltration:DesignFlowRate", [f"{zn}_INF", zn, "ON", "AirChanges/Hour", "", "", "",
                                                         p["infiltration_ach"], 1, 0, 0, 0]))
        if p["natvent_ach"] > 0:
            o.append(fmt("ZoneVentilation:DesignFlowRate", [f"{zn}_NV", zn, "NATVENT", "AirChanges/Hour", "", "", "",
                                                            p["natvent_ach"], "Natural", 0, 1, 1, 0, 0, 0,
                                                            -100, "NV_TMIN", 100, "", p["natvent_dT"], "", -100, "", 100, "", 40]))
        if not p.get("free_running"):
            o.append(fmt("ZoneControl:Thermostat", [f"{zn}_TSTAT", zn, "DUAL", "ThermostatSetpoint:DualSetpoint", f"{U}_DUALSP"]))
            o.append(fmt("ZoneHVAC:EquipmentConnections", [zn, f"{zn}_EQLIST", f"{zn}_INLET", "", f"{zn}_AIR", f"{zn}_RET"]))
            o.append(fmt("ZoneHVAC:EquipmentList", [f"{zn}_EQLIST", "SequentialLoad", "ZoneHVAC:IdealLoadsAirSystem",
                                                    f"{zn}_IDEAL", 1, 1, "", ""]))
            o.append(fmt("ZoneHVAC:IdealLoadsAirSystem", [f"{zn}_IDEAL", "", f"{zn}_INLET", "", "", 35, 13, 0.0156, 0.0077,
                                                          "NoLimit", "", "", "NoLimit", "", "", "", "", "ConstantSensibleHeatRatio",
                                                          0.7, "None", "OA_SPEC", "", "None", "NoEconomizer", "None", 0, 0]))
    o.append(fmt("OutputControl:Table:Style", ["CommaAndHTML", "JtoKWH"]))
    o.append(fmt("Output:Table:SummaryReports", ["AnnualBuildingUtilityPerformanceSummary", "EnvelopeSummary",
                                                 "InputVerificationandResultsSummary", "SensibleHeatGainSummary",
                                                 "OutdoorAirSummary"]))
    o.append(fmt("Output:Variable", ["*", "Zone Ideal Loads Supply Air Total Heating Energy", "RunPeriod"]))
    o.append(fmt("Output:Variable", ["*", "Zone Ideal Loads Supply Air Total Cooling Energy", "RunPeriod"]))
    o.append(fmt("Output:Variable", ["*", "Zone Ideal Loads Supply Air Total Heating Energy", "Monthly"]))
    if p.get("free_running"):
        o.append(fmt("Output:Variable", ["*", "Zone Operative Temperature", "Hourly"]))
        o.append(fmt("Output:Variable", ["Environment", "Site Outdoor Air Drybulb Temperature", "Hourly"]))
        o.append(fmt("Output:SQLite", ["Simple"]))
    o.append(fmt("Output:Diagnostics", ["DisplayExtraWarnings"]))
    return "".join(o)


# ---------------- occupancy / lighting / equipment profiles (24 h, every day) ----------------
# Shapes follow typical dwelling use; magnitudes are scaled so weekly full-load hours equal those
# of the DesignBuilder runs (Lighting Summary and Sensible Heat Gain Summary of eplustbl files).
def flh_scaled(on, flh_week, base=0.0):
    raw = sum((1.0 if h in on else base) for h in range(24)) * 7
    return hourly_profile(on, base, flh_week / raw)


R = lambda a, b: set(range(a, b))
SCHED = {
    "common":  {"occ": hourly_profile(R(7, 9) | R(16, 23)), "light": flh_scaled(R(6, 9) | R(15, 23), 73.99),
                "equip": flh_scaled(R(6, 9) | R(15, 24), 116.6, base=0.5)},
    "kitchen": {"occ": hourly_profile(R(7, 8) | R(13, 14) | R(18, 21)), "light": flh_scaled(R(7, 8) | R(13, 14) | R(18, 23), 49.0),
                "equip": flh_scaled(R(7, 8) | R(13, 14) | R(18, 22), 36.0)},
    "bed":     {"occ": hourly_profile(R(0, 7) | R(22, 24)), "light": flh_scaled(R(6, 7) | R(18, 24), 49.0),
                "equip": flh_scaled(R(18, 24), 54.0, base=0.25)},
    "circ":    {"occ": hourly_profile(R(7, 9) | R(17, 23), 0.0), "light": flh_scaled(R(6, 9) | R(16, 24), 68.95),
                "equip": flh_scaled(R(6, 9) | R(16, 24), 71.6)},
    "toilet":  {"occ": hourly_profile(R(6, 8) | R(20, 22)), "light": flh_scaled(R(6, 9) | R(18, 23), 56.0),
                "equip": flh_scaled(R(6, 9) | R(18, 23), 53.0)},
}

ALLDAY = set(range(24))
DEFAULTS = dict(timestep=2, ground_temp=18.0, activity_W=108, dst=True,
                hvac_hours={u: ALLDAY for u in ("common", "kitchen", "bed", "circ", "toilet")},
                heat_sp=18.0, heat_sb=12.0, cool_sp=25.0, cool_sb=28.0, natvent_hours=R(8, 22), natvent_setpoint=24.0, natvent_ach=1.0, natvent_dT=0.0,
                oa_per_person=0.008, infiltration_ach=0.7,
                wall=dict(t=0.20, k=0.40, rho=1500, cp=900, abs=0.45))

if __name__ == "__main__":
    open("test.idf", "w").write(build({}))
    print("wrote test.idf")
