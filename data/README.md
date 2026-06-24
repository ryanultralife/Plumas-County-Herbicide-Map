# Plumas data — provenance & status

## plumas_nf_herbicide_facts_2020-2025.geojson / .csv  (FEDERAL land — NEW)
- **Source:** USDA Forest Service EDW, *Activity FACTS Common Attributes* layer
  (`EDW_ActivityFactsCommonAttributes_01/0`).
- **Filter:** `fs_unit_id='0511'` (Plumas NF) AND `method='Chemical'` AND `fiscal_year_completed >= 2020`.
- **Pulled:** 2026-06-24.
- **Records:** 276 unique completed herbicide/chemical treatment points, FY2020–2025.
- **Completeness:** PARTIAL — this in-app pull captured 311 of 398 completed records
  (the data API response was capped mid-scrape). It also does **not** yet include
  acres, NEPA project name, or planned (future) treatments.
- **Activity mix (of the captured set):** ~61% *Invasives – Pesticide Application*,
  ~25% *Right of Way Maintenance*, ~14% *Tree Release and Weed*.

### To get the COMPLETE + richer dataset
Run on any networked machine (no URL/size caps):
```
pip install requests
python scripts/pull_facts.py
```
This writes `plumas_nf_herbicide_facts.geojson` + `.csv` with all completed **and**
planned chemical treatments, including acres, NEPA project, and ranger district.

## Not yet scraped (documented in the source inventory spreadsheet)
- **SOPA** planned actions — `https://www.fs.usda.gov/sopa/components/reports/sopa-110511-YYYY-MM.html`
- **NEPA project docs** (incl. Community Protection Project, project 62873)
- **Chemical name & quantity on federal land** — FOIA only (draft request prepared)
- **Private land (CA PUR)** — already in the map; refresh via CalPIP for 2020 + 2025

The map's existing private-land dots come from CA Pesticide Use Reporting (PUR);
this federal FACTS layer is the new public-land complement.
