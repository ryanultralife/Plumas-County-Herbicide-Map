# Plumas data — provenance & status

## plumas_nf_herbicide_facts.geojson / .csv  (FEDERAL land — PRIMARY)
- **Source:** USDA Forest Service EDW, *Activity FACTS Common Attributes* layer
  (`EDW_ActivityFactsCommonAttributes_01/0`).
- **Filter:** `fs_unit_id='0511'` (Plumas NF) AND `method='Chemical'`, FY2020+.
- **Pulled:** 2026-06-24.
- **Records:** 296 herbicide/chemical treatment points; **109 carry full detail**
  (acres, NEPA project, ranger district); 6 are planned (not yet completed).
- **Fields:** activity, year, status (completed/planned), acres, nepa_project,
  district, detail (full|basic).
- **Completeness:** PARTIAL — the in-app fetch tool caps response size, so each
  full-field page truncates (~29 records). This captured 296 of ~398 points and
  full detail on 109. **Run `scripts/pull_facts.py` on a networked machine for 100%**
  (all completed + planned, every field). The sandbox here has no outbound network.
- **NEPA projects seen:** Moonlight Fire Invasive Plant Treatment, PG&E Herbicide
  Vegetation Management Program, Storrie/Rich Fire invasive plant treatment,
  Moonlight Fire Area Restoration, Mt. Hough–South Park trail project.
- **Activity mix:** ~63% *Invasives – Pesticide Application*, ~25% *Right of Way
  Maintenance*, ~14% *Tree Release and Weed*, plus *Site Prep – Chemical*.

> `plumas_nf_herbicide_facts_2020-2025.geojson/.csv` is the earlier basic-only
> extract (lat/lon/activity/year). The file above supersedes it.

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
