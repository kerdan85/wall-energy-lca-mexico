# Wall materials for urban housing: energy simulation + LCA framework

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24485678.svg)](https://doi.org/10.5281/zenodo.24485678)

Code and data for the article:

> García Kerdán I., Pérez Pastrana L.E., Gori V. *Integrated energy simulation and life cycle assessment of sustainable construction materials for urban housing: from measured U-values to whole-life carbon and cost.* Energy (under review).

The framework links four stages: **(1)** measured wall transmittance → **(2)** a calibrated EnergyPlus model of a social-housing dwelling in three Mexican climates → **(3)** production carbon (A1–A3) from Brightway/ecoinvent plus transport (A4) and operation (B6) → **(4)** carbon offset and net present cost against a concrete-block reference, with Monte Carlo, scenario and sensitivity analyses.

Seven walls are compared: lightweight concrete block (reference), stabilised earth block, volcanic stone (*recinto*), *tepetate* ashlar, and solid, hollow and city-cast sargassum-based concrete (SBC) blocks, plus an **insulated concrete benchmark** (the reference block with 25 mm EPS external insulation). The cities are Mexico City, Mérida and Hermosillo. Every wall is assessed **with air conditioning** (energy, carbon, cost) and **free-running** (adaptive thermal comfort, EN 16798-1), in the **present** and the **2041–2060 climate** (CMIP6 SSP2-4.5), and the results are scaled to the 1.8 million dwellings of the national housing programme.

---

## Contents

1. [What you need: software and licences](#1-what-you-need-software-and-licences)
2. [Folder structure](#2-folder-structure)
3. [Level 1: reproduce every number and figure (no licence)](#3-level-1-reproduce-every-number-and-figure-no-licence)
4. [Level 2: re-run the EnergyPlus simulations (free software)](#4-level-2-re-run-the-energyplus-simulations-free-software)
5. [Level 3: re-run the LCA (ecoinvent licence)](#5-level-3-re-run-the-lca-ecoinvent-licence)
6. [Using the framework for your own walls or cities](#6-using-the-framework-for-your-own-walls-or-cities)
7. [Troubleshooting](#7-troubleshooting)
8. [Licences, credits and citation](#8-licences-credits-and-citation)

---

## 1. What you need: software and licences

The repository is built so that **each level only needs what the level before it needed, plus one thing**. The results of the expensive or licensed steps are stored as tables, so you can stop at any level.

| Level | What it does | Software | Licence | Time |
|---|---|---|---|---|
| 1 | Recomputes all offsets, costs, Monte Carlo, scenarios and the 13 data figures from the stored tables | Python 3.10+ with numpy, matplotlib, Pillow | None (all open source) | ~15 s |
| 2 | Re-runs the 36 EnergyPlus cases and 108 derivative runs, the insulated benchmark, the free-running comfort runs and the 2050 runs (84 more); replays the calibration | Level 1 + **EnergyPlus 25.1** | None (EnergyPlus is free, BSD-3) | ~5 min (2 cores) to 15 min |
| 3 | Recomputes production carbon A1–A3 (six impact categories, 1,000 Monte Carlo runs) | Level 1 + **Brightway 2.5** + **ecoinvent 3.9.1 cut-off** | **ecoinvent licence required** (paid; free for some academic users in low- and middle-income countries) | ~10 min with scikit-umfpack, several hours without |

**No ecoinvent licence?** You can still do everything in Levels 1 and 2. The ecoinvent-based results enter the analysis only through one small table, `pipeline/inputs/lca_a1a3.csv`, which is included. You can also replace that table with production-carbon values from any other source (EPDs, another database, your own inventory): see [Section 6](#6-using-the-framework-for-your-own-walls-or-cities).

**DesignBuilder** (commercial) was used for the original model only. It is **not** needed: the EnergyPlus model is rebuilt in Python (`energyplus/build_idf.py`) and calibrated against the 13 DesignBuilder runs, whose summary results are stored in `energyplus/db_runs.json`.

---

## 2. Folder structure

```
wall-energy-lca-mexico/
├── README.md                 this tutorial
├── environment.yml           Python environment for Levels 1–2
├── environment-brightway.yml Python environment for Level 3
├── energyplus/               LEVEL 2
│   ├── build_idf.py          writes the IDF of the case-study dwelling (11 zones, 73.45 m²)
│   ├── runner.py             runs one case, finds EnergyPlus automatically
│   ├── run_36.py             calibrated operation settings (CALIBRATED)
│   ├── run_ep_all.py         all runs of the paper → energyplus_results.csv, energyplus_perturbations.csv
│   ├── calib.py              replays the 13 DesignBuilder runs, prints NMBE and CV(RMSE)
│   ├── run_extensions.py     insulated benchmark, free-running comfort, 2050 climate (morphs the weather files)
│   ├── run_variants.py       end- and mid-terrace units, uninsulated roof, reflective coating on concrete
│   ├── colour_check.py       optional: removes the effect of wall colour (absorptance 0.65 for all)
│   ├── db_runs.json          summary results of the original DesignBuilder runs
│   ├── example/              one ready-made IDF (open it in EnergyPlus / IDF Editor)
│   ├── weather/              the three TMYx weather files, with credits; weather/2050/ the morphed files
│   └── *.csv                 the EnergyPlus results used in the paper
├── pipeline/                 LEVEL 1
│   ├── run_all.py            ← run this: reproduces everything
│   ├── mk_robust.py          offsets, costs, Monte Carlo, scenarios, sensitivity
│   ├── mk_variants.py        dwelling variants, rendered walls, 10% U uncertainty, LPG heating (Tables S12–S17)
│   ├── lca_inputs.py         reads the tables in inputs/
│   ├── mk_*.py               one script per figure group
│   ├── sim_engine.py         simplified 5R1C model (fallback only)
│   ├── inputs/               the tables that link the levels
│   │   ├── energyplus_results.csv        ← from Level 2
│   │   ├── energyplus_perturbations.csv  ← from Level 2
│   │   ├── energyplus_insulated.csv      ← from Level 2 (run_extensions.py)
│   │   ├── energyplus_comfort.csv        ← from Level 2 (run_extensions.py)
│   │   ├── energyplus_2050.csv           ← from Level 2 (run_extensions.py)
│   │   └── lca_a1a3.csv                  ← from Level 3 (aggregated results, no ecoinvent data)
│   ├── brightway/            LEVEL 3
│   │   └── brightway_acv_paper.py
│   ├── robust_results.json   all numbers reported in the paper
│   └── assets/, fonts/       photographs and fonts used by the figures
└── figures/                  output of run_all.py (the figures of the paper)
```

The tables in `pipeline/inputs/` are the only connection between the levels. If you re-run Level 2 or 3, they are overwritten, and running Level 1 again propagates the change to every number and figure.

---

## 3. Level 1: reproduce every number and figure (no licence)

### 3.1 Install Python (once)

If you already have Anaconda or Miniconda, skip to 3.2. Otherwise install **Miniconda** from https://docs.conda.io/en/latest/miniconda.html (or Anaconda, which includes Spyder).

### 3.2 Create the environment (once)

Open **Anaconda Prompt** (Windows) or **Terminal** (macOS/Linux), go to the repository folder and run:

```bash
cd path/to/wall-energy-lca-mexico
conda env create -f environment.yml
conda activate wall-lca
```

If you prefer pip: `pip install numpy matplotlib pillow`.

### 3.3 Run

**From a terminal:**
```bash
cd pipeline
python run_all.py
```

**From Spyder:** open `pipeline/run_all.py` and press **Run (F5)**. (In Anaconda Navigator, select the `wall-lca` environment before launching Spyder.)

### 3.4 What you get

- `figures/`: the 13 data figures of the paper (`nat_*.png`).
- `pipeline/robust_results.json`: every number in the paper's tables, including offsets, costs, Monte Carlo intervals, scenarios and sensitivity.
- The console prints, among other things:
  ```
  SOURCES  production carbon: brightway  | conditioning needs: EnergyPlus  | derivatives: EnergyPlus
  ```
  This confirms that the stored EnergyPlus and Brightway results were used. If a table is missing, the script falls back to built-in values and says so.

The Monte Carlo uses a fixed seed, so the results are identical on every machine.

---

## 4. Level 2: re-run the EnergyPlus simulations (free software)

### 4.1 Install EnergyPlus 25.1 (once)

Download **EnergyPlus 25.1.0** from https://energyplus.net/downloads (or https://github.com/NREL/EnergyPlus/releases/tag/v25.1.0) and install it with the default options.

| System | Default install folder (found automatically) |
|---|---|
| Windows | `C:\EnergyPlusV25-1-0\energyplus.exe` |
| macOS | `/Applications/EnergyPlus-25-1-0/energyplus` |
| Linux | `/usr/local/EnergyPlus-25-1-0/energyplus` |

If you installed it elsewhere, tell the scripts where it is with the environment variable `ENERGYPLUS_EXE`:

```bash
# macOS / Linux
export ENERGYPLUS_EXE=/path/to/energyplus
# Windows (Anaconda Prompt)
set ENERGYPLUS_EXE=C:\path\to\energyplus.exe
```

Other EnergyPlus versions are likely to work, but the published results were produced with 25.1.0. A different version may change the last digit of the results.

### 4.2 Check the installation

```bash
cd energyplus
python runner.py
```
This prints where EnergyPlus was found and the heating and cooling of one test case (kWh/m²), and keeps the run folder in `energyplus/runs/base/` so you can inspect it.

### 4.3 Replay the calibration (optional)

```bash
python calib.py
```
This compares the rebuilt model with the 13 original DesignBuilder runs and should end with:
```
{'nmbe_h': -7.25, 'cvrmse_h': 15.22, 'rmse_c': 1.96, 'cvrmse_t': 14.14, 'nmbe_t': -1.63}
```
These are the NMBE and CV(RMSE) reported in the paper (ASHRAE Guideline 14).

### 4.4 Run all the cases of the paper

```bash
python run_ep_all.py
```
This runs 144 simulations in parallel (6 walls × 3 cities × 2 U-value sets, plus the derivative runs used by the Monte Carlo). It writes `energyplus_results.csv` and `energyplus_perturbations.csv` in `energyplus/` and **copies them to `pipeline/inputs/`**. Then run the extensions:

```bash
python run_extensions.py
```
This writes the morphed 2041–2060 weather files to `weather/2050/` (dry-bulb shifted by +1.52 K in Mexico City and Hermosillo, +1.36 K in Mérida, relative humidity kept), and runs the insulated benchmark (7 cases × 3 cities), every wall free-running in both climates (scored against the EN 16798-1 Category II adaptive band from EnergyPlus's SQLite output), and every wall conditioned in the 2050 climate. It writes `energyplus_insulated.csv`, `energyplus_comfort.csv` and `energyplus_2050.csv`, again copied to `pipeline/inputs/`.

For the dwelling and finish variants of the revised paper (Tables S14–S18):

```bash
python run_variants.py
```
This runs 108 cases (detached unit with a bare roof slab, end-of-terrace units with the east or the west wall shared, mid-terrace units with and without it, and the concrete wall with a reflective coating) and writes `energyplus_variants.csv`, copied to `pipeline/inputs/` (with `colour_check.py` writing `energyplus_colour_check.csv` for the rendered-wall case). Then run `pipeline/mk_variants.py` (in Spyder: open it and press F5), which writes `variants_results.json`. It also computes the Mexico City offsets with LPG instead of electric heating (IPCC default emission factor, appliance efficiency 0.75–0.95; Table S17).

`density_check.py` reruns the reference block with density-matched tabulated conductivities (0.57 and 0.46 W m⁻¹ K⁻¹; Table S18) and writes `energyplus_density_check.csv`.

Then go back to Level 1 (`python ../pipeline/run_all.py`) to propagate the results.

On Windows, run the script from a terminal rather than from the Spyder console, because Python's multiprocessing does not work reliably inside Spyder on Windows.

### 4.5 Look at the model

`energyplus/example/CasaLosHeroes_MexicoCity_tepetate_measured.idf` is a complete input file. Open it with the IDF Editor or EP-Launch that come with EnergyPlus, or run it directly:
```bash
energyplus -w weather/MEX_MEX_Fes.Cuautitlan.766700_TMYx.epw -d out example/CasaLosHeroes_MexicoCity_tepetate_measured.idf
```

---

## 5. Level 3: re-run the LCA (ecoinvent licence)

> **You need a valid ecoinvent licence** (https://ecoinvent.org/offerings/licences/). The ecoinvent licence terms do not allow its data to be redistributed, so **this repository contains no ecoinvent inventory data**: only the script and its aggregated results (`lca_a1a3.csv`, kg CO₂-eq and other indicators per m² of wall).

### 5.1 Create the Brightway environment (once)

Keep Brightway in its own environment; it has many dependencies.
```bash
conda env create -f environment-brightway.yml
conda activate brightway
```
`scikit-umfpack` is the fast sparse solver. It is optional, but without it the 1,000-iteration Monte Carlo takes hours instead of minutes.

### 5.2 Import ecoinvent (once)

```bash
cd pipeline/brightway
python brightway_acv_paper.py --setup
```
This creates the Brightway project `sectei_walls_lca` and downloads **ecoinvent 3.9.1 cut-off** with your ecoinvent username and password (through `bw2io.import_ecoinvent_release`). It also installs the impact methods.

**If you already have ecoinvent in another Brightway project**, open `brightway_acv_paper.py` and set `CONFIG["PROJECT"]` and `CONFIG["EI_DB"]` to your names. To list them:
```python
import bw2data as bd
print(bd.projects)
bd.projects.set_current("your project"); print(bd.databases)
```

**If you have another ecoinvent version** (e.g. 3.10 or 3.11), set `EI_DB`, `BIOSPHERE` and `EI_VERSION` accordingly. Dataset names occasionally change between versions; the script stops with a clear message if one is not found, and you can look for the replacement with:
```bash
python brightway_acv_paper.py --search "concrete block"
```
Results will differ slightly from the paper (which used 3.9.1).

### 5.3 Run

```bash
python brightway_acv_paper.py
```
The script prints the impact methods it selected (ReCiPe 2016 v1.03 midpoint (H) no LT; human toxicity from EF v3.0 / USEtox, in CTUh), then writes:

- `pipeline/inputs/lca_a1a3.csv`: the table the pipeline reads (safe to share).
- `pipeline/inputs/lca_brightway_full.xlsx`: inventory, contribution analysis and Monte Carlo samples. This file contains ecoinvent-derived process detail, so **do not publish it**. It is excluded by `.gitignore`.

To re-run only one item (for example the EPS insulation system of the benchmark) and keep the other rows of `lca_a1a3.csv`:
```bash
python brightway_acv_paper.py --only "EPS insulation system (25 mm)"
```
If this row is absent, `mk_robust.py` uses a literature default of 6.0 kg CO₂-eq/m² (CV 30%) and says so in the console.

Then run Level 1 again.

---

## 6. Using the framework for your own walls or cities

The framework is general: any wall, any climate with an EPW file, any source of production carbon. What to change, and where:

| To change | Edit | Notes |
|---|---|---|
| Wall properties (U, thickness, density, specific heat, absorptance) | `WALLS` in `energyplus/run_ep_all.py` | Then run Level 2 |
| Cities / weather | Put the EPW in `energyplus/weather/`, add it to `WX` in `runner.py` and to `CITIES` in `run_ep_all.py` (with its annual mean temperature, used for the ground) | Free TMYx files for ~17,000 locations: climate.onebuilding.org |
| Production carbon without ecoinvent | Edit `pipeline/inputs/lca_a1a3.csv`: `gwp_mean` (kg CO₂-eq/m²) and `gwp_cv_pct` (uncertainty, %) per wall; the other columns are only used for the multi-criteria figure | Values from EPDs: kg CO₂-eq per kg × kg per m² of wall |
| Prices, electricity tariff, discount rate, grid emission factor, cooling COP | `PRICE`, `CE`, `R`, `F_GRID`, `COP_C` at the top of `pipeline/mk_robust.py` | |
| Transport distances (source → city) | `DIST` in `pipeline/mk_robust.py` | Road distances, km |
| Biogenic carbon of the sargassum blocks | `SARG_FRAC`, `C_FRAC` in `pipeline/mk_robust.py` | Reported separately, not in the offset |
| Insulation of the benchmark (thickness, conductivity, cost) | `EPS`, `RENDER` in `energyplus/run_extensions.py`; `INS_COST` in `pipeline/mk_robust.py` | |
| Future-climate warming | `DT2050` in `energyplus/run_extensions.py` | K added to the hourly dry-bulb |
| Programme size | `N_PROG` in `pipeline/mk_robust.py` | Dwellings |

The wall names (e.g. `"SBC block (solid)"`) are used as keys across the scripts. When you add a wall, use the same name everywhere.

---

## 7. Troubleshooting

| Problem | Solution |
|---|---|
| `EnergyPlus not found` | Install EnergyPlus 25.1 or set `ENERGYPLUS_EXE` (Section 4.1) |
| `EnergyPlus produced no results in …` | Open `eplusout.err` in that run folder; the most common cause is a wrong path to the weather file |
| `run_ep_all.py` hangs in Spyder (Windows) | Run it from Anaconda Prompt |
| Console says `using the 5R1C model results` | `pipeline/inputs/energyplus_results.csv` is missing or incomplete; restore it or re-run Level 2 |
| Brightway: `MissingIntermediateData` | The project has no processed ecoinvent database; run `--setup` or point `CONFIG` to the right project |
| Brightway: very slow Monte Carlo | `conda install -n brightway -c conda-forge scikit-umfpack` |
| Brightway: dataset not found | Your ecoinvent version names it differently; use `--search` and edit `PROXY` / `SHARED` |
| Fonts look different in the figures | The scripts register the TeX Gyre fonts in `pipeline/fonts/`; if matplotlib caches old fonts, delete its cache folder (`python -c "import matplotlib; print(matplotlib.get_cachedir())"`) |

---

## 8. Licences, credits and citation

- **Code:** MIT licence (`LICENSE`).
- **Data and figures:** CC BY 4.0 (`LICENSE-DATA.md`).
- **Weather files:** TMYx files by Climate.OneBuilding.Org, redistributed unmodified with credit (the files in `weather/2050/` are derived from them by a temperature shift). Please cite *Lawrie L.K., Crawley D.B. (2022). Development of Global Typical Meteorological Years (TMYx). http://climate.onebuilding.org*. See `energyplus/weather/README.md`.
- **EnergyPlus:** U.S. Department of Energy / NREL, BSD-3 licence, https://energyplus.net.
- **Brightway:** Mutel C. (2017). Brightway: an open source framework for life cycle assessment. *J. Open Source Softw.* 2(12):236. BSD licence.
- **ecoinvent:** Wernet G. et al. (2016). The ecoinvent database version 3. *Int. J. LCA* 21:1218–1230. Licensed; not included.
- **Fonts:** TeX Gyre Termes and Heros, GUST Font License.
- **Measured U-values:** García Kerdán I., Gori V., Pérez Pastrana L.E., et al. (2026). The impact of controlled-chamber U-value measurements on building energy modelling. *Buildings* 16:3731.

**Funding:** Secretaría de Educación, Ciencia, Tecnología e Innovación de la Ciudad de México (SECTEI), agreement SECTEI/105/2025.

**How to cite:** please cite the article and this repository: García Kerdán I., Pérez Pastrana L.E., Gori V. (2026). *Integrated energy simulation and life cycle assessment of sustainable construction materials for urban housing: code and data*. Zenodo. https://doi.org/10.5281/zenodo.24485678

**Contact:** Iván García Kerdán, Tecnologico de Monterrey, School of Engineering and Sciences, Mexico City, Mexico.
