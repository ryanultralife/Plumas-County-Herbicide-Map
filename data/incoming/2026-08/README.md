# Incoming county records — August 2026

## Imperial County grower/operator roster (received 2026-07-31)

CPRA response from the **Imperial County Ag Commissioner** (Lupe Orozco) — 8
CalAgPermits "Permits, Sites & Commodities" exports, one per permit year
**2019-2020 → 2026-2027** (`Imperial County Growers-Crops <yr>.xlsx`, raw files
git-ignored). Imperial was one of the largest naming gaps (0.6% named, 274k
unnamed applications).

`imperial-2019-2027.csv` is the normalized `operator_id,name,entity_type,county,agent`
extract (Permit Number → Operator, carrying Agent Name + Permit Type), deduped
across all 8 years (newest wins): **406 distinct permits, 405 with an
agent-of-record**.

Ingested via **`build/enrich_operator_names.py --only incoming_local`** (joins
`upper(right(owner,7)) = permit`). Two fixes landed with this batch:
- Added `Imperial: "13"` to `COUNTY_CODE` (home-county name priority).
- **Case-insensitive join** — some Imperial GROWER_IDs carry a *lowercase*
  permit-type suffix (e.g. `1321131488n`) while the roster normalizes to
  uppercase; `upper(right(owner,7))` makes them match. Without this, the
  lowercase-suffix permits (thousands of apps) would never have joined.
- `incoming_local()` now carries the `agent` column through.

Result: **Imperial 0.6% → 100.0% named** (265,651 of 265,655 apps); statewide
named coverage **73.3% → 76.0%**. Operator-name changes need no matview refresh
(the client loads `operator_names` directly and revalidates on count + updated).
