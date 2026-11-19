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

**Herbicide rows: 4, all listed in CEDEN under "Sierra Pacific Industries Research", Benner Creek ~2.5 km above Lake Almanor (40.33099, -121.2355), 2022-10-03:**
glyphosate ND (MDL 2.1 / RL 5 ug/L), imazapyr ND (0.46/1), aminopyralid ND (0.025/0.1), **hexazinone DNQ 0.0013 ug/L** (QA-flagged, low-confidence: batch NCL_SPI_41918_W_PEST comment "QAO: MS/MSD and LCS %R out" - spike recoveries out of range)
(detected below the RL of 0.005). The Region 5 Water Board has said this result came from research done independently by Sierra Pacific Industries, and that the Board cannot confirm a link to any program or permit (Region 5 Water Board PRA reply, 2026-11-10, logged in PR #23). Also paraquat ND x2 (ILRP / Sacramento Valley Coalition, MF Feather above Grizzly Cr, 2021-03/04).
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

## 4. FTP production, all 94 files (inventoried 2026-11-19; confidence: HIGH for contents)
Raw files held off-repo; sha256 in `MANIFEST.md`. `build/gen_r5_ftp_records.py` (run with `SRC_DIR=` the held folder) reads every
file (pdftotext; tesseract OCR for the 3 scanned PDFs; openpyxl; pandoc) and writes `ftp_inventory.csv` and `data/water/r5_wdr_facilities.json`.
It checks every file against the MANIFEST hashes and the 94-file / 42,693,978-byte total.

| Group | Files | What it is |
|---|---:|---|
| NPS | 8 | CEDEN export + query screenshot + instructions (section 1 above), Dixie Fire DRAFT workbook (section 2), 3 lab PDFs (section 3), 1 `Thumbs.db` (not a record) |
| WDR / Plumas Eureka CSD (WDID 5A320104004) | 31 | 25 quarterly + 6 monthly wastewater monitoring reports, 2015-2026 (30 xlsx, 2 PDF incl. 1 scanned) |
| WDR / Whitehawk Ranch MWC (WDID 5A321018001) | 55 | 39 quarterly, 14 annual, 2 groundwater monitoring reports, 2017-2026 (all PDF; 2 scanned; 1 exact duplicate: `2026/Jan 2026 Reporting.pdf` = `2025/2025 Annual Report to CRWQCB.pdf`) |

**Pesticide / herbicide search** (23 terms incl. herbicide, pesticide, glyphosate, triclopyr, 2,4-D, imazapyr, hexazinone, aminopyralid,
paraquat, atrazine, diuron, algaecide, spray): hits in **one file only**, the CEDEN export (Benner Creek 2022 x4, paraquat 2021 x2, both
already described above). The WDR reports measure flow, BOD, suspended/settleable/dissolved solids, nitrogen/nitrate, chloride, sodium, pH,
turbidity, chlorine residual, coliform/E. coli/enterococci, conductance, DO, temperature, groundwater levels and sludge hauling.
Snake Lake Shooting Range (2024-03-26) and Gopher Hill (2024-05-29) are metals tests (arsenic, copper, lead, antimony, zinc; mercury by EPA 1631E).
**No pounds, acres or application records anywhere, so nothing goes into `map_agg`.**

**On the map:** the 47 CEDEN stations at their CEDEN coordinates (orange ring = herbicide/pesticide result on file); the two WDR plants at the
PLSS section(s) named in each Board Notice of Applicability (BLM CadNSDI centroids, about half a mile; the Plumas Eureka notice prints
"R12W", corrected to R12E); Dixie DF-1..3 moved to the Board's own sheet coordinates. Snake Lake and Gopher Hill are **not placed**: the lab
reports give no coordinates. Private names: none published; one file name is shown only as `<redacted-private-name>` (matched by hash).
