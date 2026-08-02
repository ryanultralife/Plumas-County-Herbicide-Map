# Plumas Working Forests — method costs, harvest baseline, and gaps
Updated: 2026-08-02 · schema 1

Absolute figures are the best public / published numbers we can cite. Confidence: A=official CA schedule or county harvest series; B=published regional industry study (not a live Plumas bid); C=illustrative; D=gap (null). Wholesale chain uses Tahoe-Central Sierra / French Meadows delivered-log and logging schedules (MB&G 2020) — Sierra-adjacent, not Plumas-confidential contracts. Net owner profit still requires local haul distance + actual mill quotes. Do not invent; fill via program/data/INTAKE.md.

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
| `haul_sawtimber_per_mbf` | Haul landing→mill (sawtimber), distance-dependent | 49.0–120.0 (mid 66.0) | USD_per_MBF | B |
| `mill_delivered_log_price` | Mill-delivered log price (pond / gate) — common Sierra sorts | 400–550 (mid 425) | USD_per_MBF | B |
| `biomass_delivered_price` | Biomass delivered price (plant gate) | 40–40 (mid 40) | USD_per_BDT | B |
| `biomass_logging_chip` | Biomass stump-to-chip (logging + chipping, before haul) | 33–33 (mid 33) | USD_per_BDT | B |
| `logging_system_stumpage_penalty_skyline` | CDTFA skyline vs tractor — tax IHV deduction (proxy for higher yard cost) | 100–100 (mid 100) | USD_per_MBF | A |
| `logging_system_stumpage_penalty_helicopter` | CDTFA helicopter vs tractor — tax IHV deduction | 350–350 (mid 350) | USD_per_MBF | A |
| `owner_residual_stumpage_sawlog` | Illustrative residual stumpage (delivered − log − haul) before regen | 154.0–234.0 (mid 209.0) | USD_per_MBF | B |
| `herbicide_release_chemical` | Broadcast herbicide site-prep / release (chemical free-to-grow) | — | USD_per_acre | D |
| `manual_mechanical_release` | Manual / mechanical release (no broadcast herbicide) | — | USD_per_acre | D |
| `plant_seedlings` | Planting (seedlings + plant labor) | — | USD_per_acre | D |
| `owner_net_per_acre` | Net revenue to landowner after logging, haul, regen, release | — | USD_per_acre | D |

**Filled (A/B with numbers): 12 · Gaps (D): 4**

## Next fills
- Live 2025–2026 mill gate log prices (Quincy/Lincoln/Anderson sorts) — replace TCSI ~2018 delivered table
- Plant + chemical release \$/ac vs manual/mechanical (industrial or CAL FIRE unit costs) — still D
- Plumas-specific haul times to SPI Quincy vs Lincoln
- CalTREES harvest acres/volume by silvicultural method for Plumas
- Random Lengths or mill lumber wholesale + conversion cost (mill margin layer)
- USFS R5 LogCost/HaulCost sample appraisals for Plumas NF sales

