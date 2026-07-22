# Plumas County PUR export — 2024-01-01 to current (received 2026-07-22)

Public-Records-Act response from the **Plumas-Sierra Counties Department of
Agriculture / Weights & Measures** (Deputy Ag Commissioner **Dax Albrecht**),
answering our request for pesticide use from 2024-current. Arrived in the
spraymapca@gmail.com inbox on 2026-07-22.

| Delivered file | What it is |
|---|---|
| `Plumas PUR from 01-01-24.xlsx` | CalAgPermits PUR export, 3 sheets (raw; **git-ignored**) |
| `PRA response letter 07-14-2026.pdf` | County's official response letter (raw; **git-ignored**) |

The `.xlsx` has three sheets:
- **Single Job PURs** (2,276 product-line rows) — full application detail with
  Permitee (landowner), M/T/R/S section, Application Date, Product + EPA Reg No,
  Quantity, Treated Acres, Applicator, and a unique Document #.
- **Monthly Ag PURs** (220 rows) — monthly ag applications, same shape.
- **Non-Prod. Ag MSPURs** (3,351 rows) — monthly-summary non-production (golf,
  rights-of-way, structural). **No PLSS section → not mappable**; these are the
  county-level-only non-ag records already disclosed in Source Data.

## What we loaded, and why only 2025-2026

The statewide DPR extract already holds Plumas **through 2024**. The two systems
use different record ids, so a plain dedup could not catch the overlap — loading
this file's 2024 rows would silently **double-count** applications already in the
DB. So we load **only 2025 + 2026** (the DB had none), tagged
`source='pur-cac-plumas'` and `app_id='purcac:{Document#}:{COMTRS}'` so the whole
batch is identifiable and reversible (`delete ... where source='pur-cac-plumas'`).

Result: **481 mappable application events** (2025: 378, 2026: 103),
**105,513 lb of active ingredient over 30,293 acres**, 458 forestry / 18 ag / 5
federal, dominated by glyphosate + hexazinone. 19 landowner-years named (Collins
Pine, Sierra Pacific, W.M. Beaty, USDA Plumas NF, Feather River College, ranches).

## How the numbers are derived (no fabrication)

- **Coordinates** — CDPR's Plumas County PLSS shapefile (`CO_MTRS` →
  `CEN_LAT84/CEN_LONG84`); all 196 sections resolve. Cached in
  `_plumas_centroids.json` so the ingest reruns without the shapefile.
- **Pounds** — the county export reports raw volume (gal/oz/lb), not DPR-computed
  pounds. `_regmap.json` gives, per EPA reg_no, the primary active ingredient and
  a **lbs-of-AI-per-unit rate = sum(LBS_CHM_USED)/sum(AMT_PRD_USED)** taken from
  the 2020-2024 DPR extract's own numbers. Adjuvants/spray oils carry no AI and
  never determine a dot. Two reg_nos absent from 2020-2024 DPR are label-resolved
  in the build script (`HARDCODE`): TIDE HEXAZINONE 75 WDG → hexazinone; INAPRO H
  → adjuvant (only ever co-applied with a real herbicide, so never sets a class).
- **Class** — from `active_ingredient` via the DB `chem_class()` function.
- **Names** — landowner (Permitee) upserted into `operator_names` keyed by the
  synthetic GROWER_ID `32{yy}{permit7}` (matches the existing 2020-2024 pattern).

## Reproduce

```
DBURL=... python build/ingest_plumas_cac_pur.py            # transform + validate
DBURL=... python build/ingest_plumas_cac_pur.py --load     # insert + upsert names
```

Committed derived artifacts (so this reruns without the 108 MB DPR csv or the
shapefile): `_regmap.json`, `_plumas_centroids.json`,
`applications_plumas_cac_2025_2026.csv`, `operator_names_plumas_cac.csv`.

After loading: `refresh materialized view concurrently public.map_agg;` +
`refresh materialized view public.juris_agg;`, regenerate
`data/operator_coverage.json`, and bump `CELLS_KEY` in `index.html`.
