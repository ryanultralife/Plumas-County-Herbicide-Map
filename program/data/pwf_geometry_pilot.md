# Plumas NF progressive vs scatter harvest geometry pilot

_Updated: 2026-08-02_

## Source
- USFS EDW Timber Harvest (FACTS): `https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_TimberHarvest_01/MapServer`
- Filter: `admin_forest_name LIKE '%Plumas%'`
- Features downloaded: **4393** (with geometry used: 4212)
- Layer counts: {'2021-current': 432, '2011-2020': 1283, '2001-2010': 920, '1991-2000': 1758}

## Metrics
- **touching_share**: Share of unit polygons that touch or come within ~50 m of another unit that year
- **largest_component_share**: Share of units in the largest connected cluster
- **mean_nn_mi**: Mean nearest-neighbor distance between unit centroids (miles) — high = scatter
- **layout_class**: Heuristic: progressive_leaning | scatter_leaning | mixed_or_unclear | insufficient_sample
- **compactness**: 4πA/P² on foot-scaled geometry (1≈circle; lower≈elongated/complex)

## Pre-2020 (2001–2020)
- Features: **2152** across **20** years with n≥3
- Geom acres (approx): **72588.0**
- Mean annual touching share: **0.653**
- Mean annual largest component share: **0.171**
- Mean annual NN distance (mi): **1.147**
- Layout class: **multi_cluster**

## Fire-era (2021+) — interpret with caution (salvage + fire operations)
- Features: 429, layout_class: **multi_cluster**, mean_nn_mi: 0.795

## Annual layout class (2001–2020)
| Year | n | touching | largest_comp | mean_nn_mi | class |
|---|---:|---:|---:|---:|---|
| 2001 | 65 | 0.585 | 0.092 | 0.559 | multi_cluster |
| 2002 | 29 | 0.138 | 0.069 | 1.6 | mixed_or_unclear |
| 2003 | 27 | 0.593 | 0.259 | 2.365 | multi_cluster |
| 2004 | 16 | 0.688 | 0.312 | 1.95 | multi_cluster |
| 2005 | 15 | 0.0 | 0.067 | 5.783 | scatter_leaning |
| 2006 | 441 | 0.714 | 0.17 | 0.2 | multi_cluster |
| 2007 | 64 | 0.641 | 0.156 | 0.574 | multi_cluster |
| 2008 | 103 | 0.835 | 0.272 | 0.522 | multi_cluster |
| 2009 | 23 | 0.478 | 0.174 | 2.093 | mixed_or_unclear |
| 2010 | 117 | 0.795 | 0.231 | 0.997 | multi_cluster |
| 2011 | 77 | 0.701 | 0.13 | 0.468 | multi_cluster |
| 2012 | 134 | 0.657 | 0.104 | 0.334 | multi_cluster |
| 2013 | 129 | 0.752 | 0.093 | 0.572 | multi_cluster |
| 2014 | 184 | 0.837 | 0.201 | 0.504 | multi_cluster |
| 2015 | 83 | 0.807 | 0.145 | 0.388 | multi_cluster |
| 2016 | 222 | 0.883 | 0.117 | 0.329 | multi_cluster |
| 2017 | 103 | 0.67 | 0.087 | 0.559 | multi_cluster |
| 2018 | 206 | 0.864 | 0.17 | 0.397 | multi_cluster |
| 2019 | 30 | 0.633 | 0.233 | 2.361 | multi_cluster |
| 2020 | 84 | 0.798 | 0.333 | 0.375 | multi_cluster |

## Activity mix (pre-2020 feature counts)
- thin_or_salvage: 1357
- other_or_unspecified: 819
- regen_heavy: 8

## Interpretation
- FACTS timber-harvest polygons are activity footprints (not pure satellite). They are the best public layer for how units were laid out on Plumas NF.
- Pre-2020 (2001–2020) mean annual metrics: touching_share=0.653, largest_component_share=0.171, mean_nn_mi=1.147 → class **multi_cluster**.
- Year-by-year (2001–2020, n≥3): progressive_leaning=0, multi_cluster=17, scatter_leaning=1, mixed_or_unclear=2.
- Core finding: **multi-cluster layout**. Units often touch a neighbor (local clumps), but the largest connected component is only ~15–25% of that year's units — so crews still work many disconnected fronts, not one side-to-side wave. Progressive Working Forest layout (ordered strips + one active front + fixed corridors) is a real operational upgrade, not redundant with current practice.
- Activity mix is already thin-heavy (commercial thin, group selection, salvage) — the gap is layout continuity, not only silvicultural system choice.
- Hansen/GFW 2021–2025 tree-cover loss in Plumas is fire-dominated (Dixie era) and must not score logging pattern alone. This pilot uses FACTS harvest polygons for pre-2020 layout.

## Recommendation
- Adopt PWF layout rules: **True** (P1 contiguous annual front, P2 designated corridors, P3 written strip progression)
- See `program/PROGRESSIVE_LAYOUT.md`

