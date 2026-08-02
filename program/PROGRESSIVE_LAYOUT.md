# Progressive layout — cut without “jumping the forest”

**Version:** 2026-08-02 · Plumas Working Forests extension  
**Problem this solves:** Multi-entry thinning can keep canopy and skip spray — but if units are scattered, **loggers and trucks bounce** across the ownership: repeated move-in, cold equipment, wasted road time, high $/MBF. Industry hates that as much as communities hate clearcut+spray grids.

**Answer:** Yes — there is a further optimization: **keep the Working Forest silviculture (thin + small gaps + no broadcast spray), but lay it out as a progressive, continuous front** — march side-to-side (or strip-to-strip) like a slow “wave,” not random darts on a map.

This is **spatial and operational design**, not a different product. Mills still get logs; residual forest still reads as forest.

---

## 1. What “jumping around” costs

| Cost of scatter | Why it hurts |
|---|---|
| Move-in / move-out | Low-boy, loader, crew setup each unit |
| Road reopen / brush-out | Same spur used years later after regrowth |
| Short production runs | Never get into full-shift rhythm |
| Haul inefficiency | Partial loads, long empty reposition |
| Supervision | Forester/LTO covering disconnected landings |

Research and practice are consistent: **shorter average extraction distance + higher volume removed per operating day** lowers $/MBF. Scattered light thins on tiny polygons fight both.

---

## 2. Methodologies that march through the forest

### A. Progressive strip / sequential strip system (classic)

- Divide the working circle into **parallel strips** (or contour-aligned strips on slopes).
- Harvest **one strip (or a few adjacent strips)** completely under the silvicultural rule for that entry, then move to the **next strip in sequence**.
- Next entry cycle (e.g. 15–25 years later): return to the **same progression order**, or offset one strip (checker/advance).
- Visual: a **front that walks** across the compartment, not a random salt-and-pepper of units.

**Fits Working Forest when each strip is:** matrix thin + optional small gaps inside the strip — **not** a clearcut plantation strip.

### B. Boom-corridor / CTL corridor thinning (equipment-native “side to side”)

- Cut-to-length harvester works **corridors** of fixed boom reach (often ~10–20 m patterns in dense young stands — Nordic “boom corridor thinning”).
- Machine advances **systematically** along corridors; residual trees stay between corridors.
- Excellent for **dense second-growth / fuels** where random single-tree selection is slow.
- Documented productivity gains vs ad-hoc thinning in dense stands (Nordic and Western research on corridor width and cost).

**Plumas fit:** young post-fire plantations and overstocked second-growth on tractor ground; less ideal for large legacy mixed-conifer without adaptation.

### C. Designated skid-trail / skyline corridor grid (fixed extraction skeleton)

- Permanently (or multi-entry) **designated skid trails or skyline corridors** laid once.
- Every entry uses the **same extraction skeleton** — crew “marches” corridor by corridor, landing-centered.
- Reduces residual damage and **eliminates reinventing access** each visit.
- USFS/OSU thinning cost work: **minimize skid distance**; layout is half the economics.

### D. Landscape “wave” scheduling (compartment-level)

- Ownership or watershed split into **compartments** (e.g. 500–2,000 ac).
- Annual cut is a **contiguous block of compartments** along a planned path (ridge system, road loop, or fire-break network).
- Next year: **adjacent** compartments — continuous wood flow without leapfrogging 40 miles.
- Multi-entry volume still works: when the wave returns in 15–30 years, the same path is reused.

### E. Hybrid: “thinning front + retention cells” (recommended Plumas package)

Combine:

1. **Fixed road / trail / corridor skeleton** (design once).  
2. **Annual progressive front** of 1–3 adjacent strips/compartments.  
3. **Inside the front:** Working Forest Standard (VDT matrix, gaps ≤2 ac, skips, **no broadcast free-to-grow chemistry**).  
4. **Outside the front:** rest — no “spot” commercial entries unless hazard/fire emergency.  
5. **Return interval** for the wave: planned (e.g. 15–30 years), not opportunistic scatter.

**Logger experience:** “We work this side of the district this season, move the front, come back next decade on the same roads.”  
**Community experience:** continuous canopy; no clearcut patches + spray; harvest is **visible as a moving zone**, not random holes.

---

## 3. How this differs from status-quo industrial layout

| | Clearcut plantation grid | Scatter thin (bad multi-entry) | **Progressive Working Forest** |
|---|---|---|---|
| Spatial pattern | Large adjacent regen blocks | Random small units | Ordered strips / wave |
| Crew movement | Efficient within big units | Jumping | Efficient *and* ordered |
| Canopy | Removed for decades | Kept but ops messy | Kept + ops clean |
| Spray free-to-grow | Common | Variable | Out of Standard |
| Mill feed | Pulse then quiet | Erratic | Steady annual front |

---

## 4. Satellite and remote-sensing evidence (what we can see)

### 4.1 What satellites are good for

| Product | Resolution | Useful for |
|---|---|---|
| **Hansen / GFW tree-cover loss** (Landsat 30 m, annual) | Stand-scale clearings, fire, large harvest | **When and where canopy dropped** — not silvicultural method |
| **Sentinel-2 / HLS** | 10–30 m, frequent | Finer timing of disturbance |
| **Planet / high-res** (where licensed) | ~3–5 m | Patch shape, road/skid, small openings |
| **USFS FACTS / TIM** (agency GIS, not pure satellite) | Activity polygons | Harvest/fuels **activity type** if attributed |
| **CalTREES** (admin) | Plan polygons | Legal harvest method if fields complete |

### 4.2 Plumas / Sierra constraint (critical)

For **2021–2025**, Global Forest Watch / UMD tree-cover loss for Plumas is **dominated by wildfire** (Dixie and related), not orderly commercial thinning. Public summaries put large natural-forest loss in that window (order of **~170 kha** tree-cover loss in natural forest 2021–2025 for Plumas in GFW-style dashboards — **almost all fire-driven**, not “logger pattern”).

**Implication:** You **cannot** reverse-engineer “optimal strip logging” from 2021–2025 Hansen loss alone in Plumas — fire swamps the signal. Pre-2020 and post-recovery windows + **FACTS timber harvest polygons** + **CalTREES** are the right stack to separate:

- clearcut-shaped rectangles  
- thin (harder to see at 30 m)  
- fire  
- salvage

### 4.3 Pilot results (Plumas NF FACTS, 2026-08-02)

**Tool:** `python program/tools/pwf_geometry_pilot.py`  
**Outputs:** `program/data/pwf_geometry_pilot.json` · `.md` · `data/pwf_geometry_pilot.json` (site)

Pulled **4,393** USFS FACTS Timber Harvest polygons for Plumas National Forest (layers 1991–current).

| Period | Features | Mean annual touching | Mean largest component | Mean NN (mi) | Class |
|---|---:|---:|---:|---:|---|
| **2001–2020** | 2,152 | **0.65** | **0.17** | **1.15** | **multi_cluster** |
| 2021–2026 | 429 | 0.63 | 0.24 | 0.80 | multi_cluster (salvage/fire ops — caution) |

**Meaning:**

- Units often **touch a neighbor** (not pure isolated darts).  
- But the **largest connected component is only ~17%** of that year’s units on average — so harvest runs as **many small clumps**, not **one side-to-side wave**.  
- Crews still **jump between clumps** (the operational tax you named).  
- Activity mix is already **thin / group selection / salvage–heavy** — the gap is **layout continuity**, not only “do more commercial thin.”

Year-level table and full metrics: `program/data/pwf_geometry_pilot.md`.

**Hansen / GFW:** 2021–2025 Plumas tree-cover loss remains **fire-dominated**; this pilot intentionally scores **FACTS harvest polygons** for layout, not Hansen alone.

### 4.4 Optional next data builds

1. Hansen pre-2020 lossyear (optional canopy context) via GeoTIFF + `--hansen`.  
2. CalTREES private THP footprints (same contiguity metrics off-forest).  
3. Road-network leapfrog score (distance between annual clumps along haul routes).

### 4.4 Open data pointers

- GFW / Global Nature Watch tree cover loss: https://www.globalnaturewatch.org/ (Plumas dashboard under USA → California → Plumas)  
- Hansen GFC (Earth Engine): `UMD/hansen/global_forest_change_*`  
- USFS FACTS / geodata: https://data.fs.usda.gov/geodata/edw/datasets.php  
- CalTREES: https://caltreesplans.resources.ca.gov/caltrees/  
- Literature: corridor thinning cost (e.g. Western/CTL studies; Nordic boom-corridor methods); USFS thinning cost series (skid distance, volume removed)

---

## 5. Operational standard add-on (for the Plumas Working Forest Standard)

When claiming **Progressive Working Forest** layout:

| Rule | Spec |
|---|---|
| **P1 Contiguous annual front** | ≥70% of year’s commercial acres share a boundary with another treated acre that year or form one connected road-shed |
| **P2 Fixed extraction skeleton** | Designated skid/skyline corridors mapped; reused next entry |
| **P3 Strip or compartment order** | Written progression map for 10–30 years (wave path) |
| **P4 No orphan units** | No commercial unit >X road-miles from the active front without hazard justification |
| **P5 Silviculture** | Still PRESCRIPTION_STANDARD (matrix/gaps/skips; no broadcast free-to-grow) |
| **P6 Monitoring** | GPS machine tracks or daily landing logs optional; annual map of treated strips |

Violating P1–P4 while keeping thin silviculture = **Working Forest silviculture without progressive ops** (ecology maybe OK, **logger economics worse**).

---

## 6. Economics link (why industry should care)

From cost ledger (see `data/working_forests_costs.json`):

- Thin already costs **more $/MBF** at low volume/ac than heavy regen.  
- **Scatter multiplies that penalty** (move-in, short days).  
- Progressive front **does not remove** the low-MBF/ac issue but **cuts the layout tax**.  
- Cable/skyline: corridor reuse is even more valuable (setup cost high).

**Hypothesis to test with local LTO quotes:**  
`$/MBF_progressive_thin < $/MBF_scatter_thin` by enough that multi-entry NPV approaches clearcut+chem after spray avoidance and multi-entry volume.

Mark **C** until Plumas LTO time-and-motion or bid comparison exists.

---

## 7. Recommended Plumas package (optimized end-state)

**Name:** Progressive Working Forest (PWF)

1. **Silviculture:** Plumas Working Forest Standard (thin + small gaps + natural regen preference + no broadcast free-to-grow chemistry).  
2. **Layout:** Progressive strip / compartment wave + designated corridors.  
3. **Equipment:** Prefer CTL or thinning-configured ground on gentle slopes; skyline with **fixed corridor grid** on steep.  
4. **Scheduling:** One active front per ownership/road-shed per year; mills get predictable annual volume from the front.  
5. **Evidence plan:** Pre-2020 Hansen + FACTS + CalTREES geometry study; FOIA unit costs (already drafted).  
6. **Honesty:** Fire years dominate recent satellite loss — do not over-read 2021–2025 canopy loss as logging pattern.

---

## 8. What we are *not* claiming

- That progressive strips alone match clearcut volume without enough acres or re-entry.  
- That 30 m satellite can currently map “thin vs clearcut” cleanly across Plumas without agency overlays.  
- That owners must adopt this — still their timber, their business, their land.  
- That fire salvage follows the same wave logic (emergency can break the front — document exceptions).

---

## 9. Implementation steps (next)

| Step | Owner | Status |
|---|---|---|
| Publish this methodology | Repo / Working Forests tab | **This file** |
| Add PWF layout rules to PRESCRIPTION_STANDARD | Repo | Optional next patch |
| Hansen pre-2020 + FACTS geometry pilot | Data agent | Not built |
| LTO quote: progressive vs scatter thin | Industry conversation | Open |
| Site section “Progressive layout” | index.html | Optional next patch |
