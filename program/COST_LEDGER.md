# Plumas Working Forests — method costs, harvest baseline, and gaps
Updated: 2026-08-02 · schema 1

Absolute figures below are the best public numbers we can cite so far. Confidence grades: A = official CA schedule or county harvest series; B = peer-reviewed or multi-study regional range; C = illustrative placeholder; D = known gap (null). Net owner profit by method is D until local bids and stumpage actuals land. Other agents: fill nulls via program/data/INTAKE.md — do not invent.

## Plumas harvest (MBF)
Source: University of Montana BBER Forest Industry Research — Timber Harvest for Plumas County, California [A]
- Latest 2024: **156,371** MBF (private share 83%)
- Avg total 2018–2020 (pre-spike): 108,161 MBF
- Avg total 2021–2023 (fire years): 294,531 MBF

## Cost line items
| ID | Label | Range | Unit | Conf |
|---|---|---|---|---|
| `thin_ops_western_us` | Forest thinning operations (Western US literature range) | 307–1737 | USD_per_acre | B |
| `ca_full_fuels_package` | CA full fuels package (planning + thin + pile burn) — order of magnitude | 2000–2500 (mid 2250) | USD_per_acre | B |
| `pile_burn_western` | Pile burning (Western US range) | 409–735 | USD_per_acre | B |
| `logging_system_stumpage_penalty_skyline` | CDTFA skyline vs tractor — tax IHV deduction (proxy for higher yard cost) | 100–100 (mid 100) | USD_per_MBF | A |
| `logging_system_stumpage_penalty_helicopter` | CDTFA helicopter vs tractor — tax IHV deduction | 350–350 (mid 350) | USD_per_MBF | A |
| `herbicide_release_chemical` | Broadcast herbicide site-prep / release (chemical free-to-grow) | — | USD_per_acre | D |
| `manual_mechanical_release` | Manual / mechanical release (no broadcast herbicide) | — | USD_per_acre | D |
| `plant_seedlings` | Planting (seedlings + plant labor) | — | USD_per_acre | D |
| `clearcut_logging_per_mbf` | Clearcut / high-volume regen harvest logging cost | — | USD_per_MBF | D |
| `partial_cut_logging_per_mbf` | Partial cut / commercial thin logging cost | — | USD_per_MBF | D |
| `mill_delivered_log_price` | Mill-delivered log price by sort (pond value) | — | USD_per_MBF | D |
| `owner_net_per_acre` | Net revenue to landowner after logging, haul, regen, release | — | USD_per_acre | D |

**Filled (A/B with numbers): 5 · Gaps (D): 7**

## Next fills
- Local LTO logging $/MBF clearcut vs thin (or anonymized bid ranges)
- Plant + chemical release $/ac vs manual/mechanical release $/ac (industrial or CAL FIRE unit costs)
- CalTREES harvest acres/volume by silvicultural method for Plumas
- Mill delivered prices by sort (or public price reports)
- USFS Plumas cut/sold and contract appraisal worksheets

