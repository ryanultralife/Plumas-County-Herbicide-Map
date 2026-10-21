# DPR Groundwater Protection Program — Well Kit analyte list

- **Sender:** CA Dept of Pesticide Regulation, Groundwater Protection Program (email to spraymapca@gmail.com)
- **Received:** 2026-08-07
- **Raw file:** `DPR GW Screens_well kits - consolidated.xlsx` (1 sheet "Consolidated list", 95 rows x 3 cols; not committed)
- **Confidence:** HIGH as a verbatim copy of the agency list. It is **an analyte list only**: no wells, sample dates,
  results, counties or coordinates. It cannot show detects or non-detects.
- **Already published** as `data/dpr_well_kit_analytes.json` (2026-09-07, 94 compounds). This CSV is the same list in
  machine-readable form with flags added.

Output `dpr_gwpp_wellkit_analytes.csv`: compound_as_listed, compound, method_in_development (`**`), marginal, herbicide_key
(the TARGET key from `build/gen_edt_plumas.py`).

Forestry herbicides covered: hexazinone; triclopyr (marked "(marginal)" by DPR). NOT covered: glyphosate, AMPA,
imazapyr, aminopyralid, 2,4-D, clopyralid, sulfometuron-methyl, indaziflam, picloram.
Regenerate: `python normalize_dpr_gwpp.py` (env `SRC=` to point at the xlsx).
