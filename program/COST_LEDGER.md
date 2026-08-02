# Plumas Working Forests — method costs, harvest baseline, and gaps
Updated: 2026-08-02 · schema 1

Absolute figures: best public/published numbers. Grades A official CA; B published industry/regional (not live Plumas SPI contract); C multi-source practice range or derived; D gap. Wholesale chain now includes 2025 Inland log-price proxy, Plumas haul-to-Quincy estimates, plant/release practice ranges, lumber wholesale snapshot. Owner full net still modeled not audited. See program/data/INTAKE.md.

## Plumas harvest (MBF)
Source: University of Montana BBER Forest Industry Research — Timber Harvest for Plumas County, California [A]
- Latest 2024: **156,371** MBF (private share 83%)
- Avg total 2018–2020 (pre-spike): 108,161 MBF
- Avg total 2021–2023 (fire years): 294,531 MBF

## Cost line items
| ID | Label | Range | Unit | Conf |
|---|---|---|---|---|
| `thin_ops_western_us` | Forest thinning operations (Western US literature range) | 307–1737 (mid 840) | USD_per_acre | B |
| `ca_full_fuels_package` | CA full fuels package (planning + thin + pile burn) — order of magnitude | 2000–2500 (mid 2250) | USD_per_acre | B |
| `pile_burn_western` | Pile burning (Western US range) | 409–735 | USD_per_acre | B |
| `clearcut_logging_per_mbf` | Heavy removal / regen harvest stump-to-truck (tractor, 20–40+ MBF/ac) | 90–110 (mid 100) | USD_per_MBF | B |
| `partial_cut_logging_per_mbf` | Partial cut / commercial thin stump-to-truck (tractor, 3–14 MBF/ac) | 125–180 (mid 150) | USD_per_MBF | B |
| `haul_sawtimber_per_mbf` | Haul landing→mill (sawtimber), distance-dependent | 33.0–120.0 (mid 45.0) | USD_per_MBF | B |
| `mill_delivered_log_price` | Mill-delivered log price (pond / gate) — common Sierra sorts | 300–550 (mid 400) | USD_per_MBF | B |
| `mill_lumber_wholesale` | Lumber wholesale / futures (mill output) | 450–620 (mid 555) | USD_per_MBF_lumber | B |
| `mill_conversion_cost` | Sawmill conversion cost (rough, per log-MBF) | 120–320 (mid 200) | USD_per_MBF | C |
| `biomass_delivered_price` | Biomass delivered price (plant gate) | 40–40 (mid 40) | USD_per_BDT | B |
| `biomass_logging_chip` | Biomass stump-to-chip (logging + chipping, before haul) | 33–33 (mid 33) | USD_per_BDT | B |
| `logging_system_stumpage_penalty_skyline` | CDTFA skyline vs tractor — tax IHV deduction (proxy for higher yard cost) | 100–100 (mid 100) | USD_per_MBF | A |
| `logging_system_stumpage_penalty_helicopter` | CDTFA helicopter vs tractor — tax IHV deduction | 350–350 (mid 350) | USD_per_MBF | A |
| `owner_residual_stumpage_sawlog` | Illustrative residual stumpage (delivered − log − haul) before regen | 135.0–215.0 (mid 190.0) | USD_per_MBF | B |
| `plant_seedlings` | Planting (seedlings + plant labor) | 250–900 (mid 450) | USD_per_acre | C |
| `herbicide_release_chemical` | Broadcast herbicide site-prep / release (chemical free-to-grow) | 50–250 (mid 120) | USD_per_acre | C |
| `manual_mechanical_release` | Manual / mechanical release (no broadcast herbicide) | 250–1000 (mid 500) | USD_per_acre | C |
| `owner_net_per_acre` | Net revenue to landowner after logging, haul, regen, release | 520.0–5820.0 | USD_per_acre | C |

**Filled (A/B with numbers): 13 · Gaps (D): 0**

## Next fills
- SPI Quincy / Lincoln confidential or published delivered price sheets (upgrade C/B proxy to A for Plumas)
- Sealed or FOIA plant+herbicide unit costs from industrial THPs or USFS contracts (upgrade C practice bands)
- GPS truck time samples Plumas landings → Quincy scales
- CalTREES harvest by silvicultural method
- Sawmill recovery factor + residual chip credit for accurate mill margin

