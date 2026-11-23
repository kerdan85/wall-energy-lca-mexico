# Weather files

The three EnergyPlus weather files (EPW) are TMYx typical meteorological years from
**Climate.OneBuilding.Org**, redistributed here unmodified so that the simulations can be
reproduced exactly. All credit for these files belongs to their authors.

| City | File | Station (WMO) |
|---|---|---|
| Mexico City | `MEX_MEX_Fes.Cuautitlan.766700_TMYx.epw` | Cuautitlán, 766700 |
| Mérida | `MEX_YUC_Merida-Rejon.Intl.AP.766440_TMYx.epw` | Mérida–Rejón Intl. AP, 766440 |
| Hermosillo | `MEX_SON_Hermosillo.761600_TMYx.epw` | Hermosillo, 761600 |

**Source:** https://climate.onebuilding.org (North and Central America → Mexico).

**Please cite:** Lawrie, L.K., Crawley, D.B. (2022). *Development of Global Typical Meteorological
Years (TMYx).* http://climate.onebuilding.org

TMYx files are built from the hourly records of NOAA's Integrated Surface Database (ISD) with the
ISO 15927-4 typical-year method; recent releases take solar radiation from the ERA5 reanalysis.
The files are not covered by this repository's licences. Their terms are set by Climate.OneBuilding.Org;
if you reuse them, download them from the source and cite the authors as above.

The Mexico City file is the one used by the original DesignBuilder model and in the companion
measurement study.
