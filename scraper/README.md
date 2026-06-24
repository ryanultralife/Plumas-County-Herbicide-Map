# Statewide pesticide-data scraper

A region-by-region pipeline that pulls **all herbicide/pesticide use — public and
private land** across California into one normalized table the map and Claude can query.

## How it flows

```
regions.json ─┐
              ├─►  run_region.py  ──►  source modules  ──►  one SQLite table  ──►  GeoJSON export
sources/      ─┘   (orchestrator)     facts / pur / thp    data/db/             data/exports/
```

Every source normalizes to the **same row shape** (`lib.COLUMNS`): one row = one
application/treatment with `date, lat, lon, county, land_type, owner, product,
active_ingredient, amount, unit, method, activity, project, status, source`.
Rows upsert by `app_id`, so re-running is safe and incremental.

## Run it

```bash
pip install requests                          # one-time
python scraper/run_region.py northern-sierra                    # FACTS (federal)
python scraper/run_region.py northern-sierra --sources facts,pur,thp   # everything
```

Outputs: `data/db/applications.sqlite` (all regions, all sources) and
`data/exports/<region>.geojson` (what the map loads). The sync watcher commits them.

## Sources (`scraper/sources/`)

| Module | Coverage | Land | Notes |
|---|---|---|---|
| `facts.py` | USFS FACTS chemical treatments, per national forest | federal | Live ArcGIS API; proven. |
| `pur.py` | CA DPR Pesticide Use Reporting, per county, 2020–2023 | private / ag / utility / **railroad** | Downloads ~200 MB/yr; derives lat/lon from PLSS section. |
| `thp.py` | CAL FIRE Timber Harvest Plans, per county | private forestry | Verify ArcGIS endpoint before production run. |

`land_type` is auto-classified (`lib.classify`): federal, utility (PG&E/SCE),
**railroad** (Union Pacific/BNSF), roadside (Caltrans/ROW), forestry, rangeland, ag.
This is how railroad + utility spraying gets separated out.

## Add a region

Edit `regions.json` — add counties (CA codes 01–58) and the national forests
(`fs_unit_id`) in that region — then `python scraper/run_region.py <key> --sources facts,pur,thp`.
Work one region at a time; they all accumulate in the same database.

## Current status (Northern Sierra pilot)

`data/db/applications.sqlite` is seeded with **296 federal FACTS treatments**
(Plumas NF; Lassen + Tahoe queued — 1,649 more chemical records confirmed via API).
PUR and THP modules are built and ready; run them on a networked machine to add the
private/ag/utility/railroad side (the sandbox here has no outbound network).

## Note on this sandbox
SQLite journaling and large-file reads are unreliable on the network mount used in the
Cowork session, so the DB is built on local disk and copied in. On your Windows disk
none of that applies — `run_region.py` writes straight to `data/db/`.
