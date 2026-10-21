# Central Valley Water Board (R5) — PRA response, CEDEN export + Dixie Fire DRAFT

- **Sender:** Central Valley Regional Water Quality Control Board (R5). Dixie sheet contact: George Low. Analysis by Babcock Laboratories.
- **Received:** 2026-10-06
- **Raw files** (not committed): `CEDEN_export_PRA_633.xlsx`, `CEDEN_query_PRA_633.png`, `CEDEN records Instructions.docx`,
  `Dixie Fire Water Quality Monitoring - DRAFT Results.xlsx`, 3 lab PDFs.

## 1. CEDEN export (confidence: HIGH, public CEDEN data)
Query per the instructions docx: Regional Board Central Valley, County Plumas, 2018-01-01 to 2026-09-16, water-chemistry category.
2,066 rows, 94 cols, 47 stations, all `COUNTY=PLUMAS`, sample dates 2018-04-07 to 2026-07-21. Every row has LATITUDE/LONGITUDE.
Matrices: samplewater 1,923, benthic 116, air 27. Programs: SWAMP 842, USFS MIS 689, DWR 225, ILRP 100, FERC 80, Plumas Corp 74, SPI Research 56.
Mostly field parameters, nutrients, ions and solids. `detect_status` comes from RESULTQUALCODE
(`=`/`>=`/`<=` detect, ND non-detect, DNQ/JF detect-estimated, NR not-reported). Field measurements count as "detect".

**Herbicide rows: 4, all Sierra Pacific Industries Research 2022, Benner Creek ~2.5 km above Lake Almanor (40.33099, -121.2355), 2022-10-03:**
glyphosate ND (MDL 2.1 / RL 5 ug/L), imazapyr ND (0.46/1), aminopyralid ND (0.025/0.1), **hexazinone DNQ 0.0013 ug/L** (QA-flagged, low-confidence: batch NCL_SPI_41918_W_PEST comment "QAO: MS/MSD and LCS %R out" - spike recoveries out of range)
(detected below the RL of 0.005). Also paraquat ND x2 (ILRP / Sacramento Valley Coalition, MF Feather above Grizzly Cr, 2021-03/04).
`herbicide_key` does not flag paraquat because it is not in TARGET.
No triclopyr or 2,4-D anywhere.
Outputs: `ceden_plumas_results.csv` (all rows, 26 cols), `ceden_stations.csv`, `ceden_herbicide_results.csv`.

## 2. Dixie Fire Water Quality Monitoring — **DRAFT / PRELIMINARY** (confidence: MEDIUM, labelled draft by the Board)
The sheet header says "PRELIMINARY RESULTS" and "All results presented here are considered draft". Stations DF-1/2/3 (lat/lon on the
"Sampling Locations" sheet), 7 dates 2021-09-28 to 2022-04-05. Field parameters, minerals, nutrients, bacteria, total and dissolved metals, PAHs and PCBs.
**No herbicide analytes.** Converted from wide to long: 1,045 results, 58 analyte/fraction rows (non-detect 526, detect 414, J-estimated 105).
Footnote digits after a value (e.g. `<0.20 1`) are kept in `flags`. Every row has `status=DRAFT`.
Outputs: `dixie_fire_DRAFT_results_long.csv`, `dixie_fire_DRAFT_stations.csv`. This appears to be the spreadsheet version of
the July 2026 `Dixie Fire WQ Sampling Results.pdf` (2026-08/water-board), and adds PAHs and PCBs that `water_monitoring.json` does not list (unverified).

## 3. Lab PDFs (not parsed)
Babcock / State Board R5 Redding Branch, project RWB5-R_FY22/23_General: Snake Lake Shooting Range (2024-03-26, lead) and
Gopher Hill (2024-05-29, mercury plus an amended report). These look like shooting-range and mine-site metals; no herbicides seen in text grep.

Regenerate: `python normalize_cvrwqcb_ceden.py` (env `SRC_DIR=`).
