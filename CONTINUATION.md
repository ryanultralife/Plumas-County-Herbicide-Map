# SprayMap California — Continuation / Handoff

_Snapshot: **2026-08-02**. `main` tip **`7045041`**; main checkout, the claude worktree and `origin/main` are all in sync. Deploys via Vercel from `main`._

## What this is
A single static **`index.html`** (Leaflet + 5 tabs) backed by **Supabase Postgres**, mapping California's reported pesticide use. Spine = **Plumas + the Northern Sierra** (Butte, Tehama, Lassen, Plumas, Sierra); statewide context around it. Run by the **Plumas Grassroots Collective** — a **registered CA nonprofit** (state filing + EIN, July 2026). Transparency is the point: name the operators, show pounds/acres, and publish the org's own spending.

## Live
- **LAUNCHED 2026-07-10** at **`spraymapca.org`** (canonical; `www` is the production host, apex 308s to it). Vercel project `plumas-county-herbicide-map`, team `ryan-vukichs-projects`, auto-deploys from `main`.
- **Vercel Web Analytics** is wired (first-party `<script defer src="/_vercel/insights/script.js">` + `window.va` stub, PR #2 → `4b1b12b`). ⚠️ It only collects once **Analytics is Enabled in the Vercel dashboard** — verify that.

## Backend — source of truth is Supabase, NOT git
Connect: `source C:/Users/ryanv/.pg_dburl` (sets `$DBURL`; **secret — never echo/commit**), then `psql "$DBURL"`. Only the public anon key lives in `index.html` (read-only views).

| Object | State |
|---|---|
| `public.applications` | **12,012,484** rows (pur 12,001,289 · pur-cac-plumas 481 · facts 10,714). Statewide PUR **2020–2022**; **2023–2024 for the 5 NS counties**; **Plumas 2025–2026** from the county's own PUR export. `acres` populated for NS only. |
| `public.map_agg` | **29,418** cells, one per ~PLSS section (`round(lat/lon,3)`). Drives the map. |
| `public.juris_agg` | region/county rollups; `top_owners` = `[owner, count, lbs]`. |
| `public.operator_names` | **37,664** ids named. Statewide **76.0%** of mapped applications (Imperial 0.6%->100% via the Aug county roster). |
| `public.section_ownership` (JSON, not a table) | `data/section_ownership.json` — 940 USFS / 228 inholding sections. |

**Client cache key is `CELLS_KEY='map_agg:v9-plumas2026:...'`** — bump it in `index.html` whenever `map_agg`'s *data* changes, not just its columns (the built-in revalidation only compares row **count**, so a coordinate-only change can slip through).

## ⚠️ Hard-won gotchas — read before touching anything

**Coordinates / PLSS**
- A PUR `owner` (GROWER_ID) is `[county 2][year 2][county 2][permit 5]`, e.g. `54205410929`. **`right(owner,7)` = the county permit number** published in CAC rosters. This join is the backbone of operator naming.
- `scraper/lib.py::_section_offset` had its **serpentine inverted** (PLSS numbers from the NE corner; EVEN rows mirror). It placed dots a **median 3.7 mi** (max 5.7) off. Fixed — but coordinates in the DB are now **true PLSS centroids**, so the approximation is only a fallback.
- Spine coords came from **BLM CadNSDI** (`gis.blm.gov/caarcgis/.../BLM_CA_CADNSDI/FeatureServer/2`, `returnCentroid=true`, FRSTDIVID = `CA210{tt}0{N/S}0{rrr}0{E/W}0SN{ss}0`). BLM **omits land-grant/unsurveyed areas**, so Butte/Tehama valley came from **CDPR's own PLSS** (`calpip.cdpr.ca.gov/content/groundwater/shapefiles/{County}_County_PLSS_NAD83AlbersCA.zip`) which ships **precomputed `CEN_LAT84`/`CEN_LONG84` + `CO_MTRS`** — a pure attribute join, no GIS math.
- `applications` stores **no comtrs** — re-derivation must join `dpr_data.csv` (year, use_no) → app_id.
- Reversal backups: `data/raw/cpra/coord_backup_pre_plss.csv`, `coord_backup_valley_preupgrade.csv`.

**Operator names — the trap**
- County rosters carry **7-digit permit numbers**; `applications.owner` is **11 chars**. `build/ingest_operator_names.py` stores the id **as-is** → rows that never join. **Use `build/enrich_operator_names.py`**, which joins `right(owner,7)=permnum` and inserts the full owner id (one per year). Add new deliveries as CSVs under `data/incoming/<month>/` (auto-picked up by its `incoming_local()` source) and run:
  `DBURL=... python build/enrich_operator_names.py --only incoming_local`

**Postgres / tooling**
- The pooler + the 2-minute tool timeout kill long statements → **run loads, refreshes and `select distinct owner` scans in a background shell**.
- `refresh materialized view concurrently public.map_agg` takes **~9 min**. **`juris_agg` cannot refresh CONCURRENTLY** (no unique index) — and it's **county-grouped, so coordinate-only changes don't affect it**.
- Operator-name changes need **no matview refresh** — the client loads `operator_names` directly and revalidates on count+updated.

**Editing `index.html` (≈370 KB, CRLF)**
- The Read tool refuses it; use Grep to locate and Python to patch. Match with `\r\n` in multi-line patterns.
- **`open(path,'w')` truncates before writing — a mid-write exception leaves the file EMPTY** (this happened; recovered via `git checkout`). Always write to `path+".tmp"` then `os.replace`.
- Don't `print()` non-ASCII on Windows (cp1252 `UnicodeEncodeError`); put emoji in HTML as entities (`&#127794;`) rather than `\uXXXX` escapes in JS.

**Gmail (spraymapca@gmail.com)**
- The **Gmail MCP connector is bound to the wrong account** (`ryan@mechanical-battery.com`). Reach spraymapca only via **Chrome (claude-in-chrome) at `mail.google.com/mail/u/1/`** — u/0 is ryanvukich@gmail.com — and **verify the account in the tab title before acting**.
- The Gmail tab **freezes under automation** (screenshots time out, submit clicks get eaten). Reload before each compose, use the **inline** Compose (not `?view=cm`), and re-open a draft to confirm it saved.
- `file_upload` only accepts files **the user shared** — an agent-generated file can't be uploaded (this blocked automating the Gmail filter import; `gmail-filters-spraymapca.xml` is in the main repo for manual import via Settings → Filters → Import filters).

## What happened since launch (`4b1b12b`..`6362983`, 10 commits)
- **Coordinate rebuild** — 364,732 NS coords → true PLSS centroids; water-safe placement re-run (only 1 landed in water); `lib.py` serpentine fixed.
- **Valley upgrade** — 148,938 Butte/Tehama coords → CDPR PLSS centroids (from ~1 mi approximation to exact).
- **Statewide map fix** — dots no longer flash out on scope change (fit view first, build once, suppress the redundant `moveend` rebuild); zoom<7 capped at the busiest **2,500** sections. Also **popups no longer vanish on click** statewide - the `moveend` LOD rebuild clears every marker, so a popup's own autoPan was killing the marker it was attached to; the rebuild is now held while a popup is open and runs on `popupclose`.
- **Landowner + ownership** — popups relabeled **"Landowner / permittee"** with conservative ownership-class chips (Private timberland / Federal-USFS / Golf / Gov / Ranch / Farm), plus **spatial** USFS point-in-polygon tagging + a soft mismatch note.
- **Non-ag surfaced** — `data/nonag_coverage.json`: 66,412 county-level-only records (structural PC / ROW / landscape) that have no section and can't be mapped, now disclosed in Source Data with named Plumas applicators.
- **Dates unified** — map stat shows the **actual** scoped year span (clamped to 2024 so FACTS *planned* years don't masquerade as reported use); coverage framed as living.
- **Mobile parity** — class-colored dots, all 8 per-class layers, full collapsible legend; map-stat opens on load, static ▸ arrow, reliable tap-to-close (hover scoped to `@media (hover:hover)`); layers control has its own ▸ collapse arrow.
- **July roster ingest** — Tulare/Madera/San Joaquin: **Tulare 3.2% → 90.3%** named (+778k apps), Madera 16.3% → 92.3%; statewide **63.1% → 73.3%**.
- **Plumas 2025–2026** — county PRA PUR export (Dax Albrecht, Plumas-Sierra Ag Dept, 2026-07-22) loaded as source `pur-cac-plumas`: **481 application events, 105,513 lb, 30,293 ac** (glyphosate + hexazinone; 458 forestry / 18 ag / 5 federal). Only **2025–2026** loaded — the DPR extract already holds Plumas ≤2024, so loading the file's 2024 would double-count (different id systems). Pounds derived from **DPR's own per-product AI rates** (`build/ingest_plumas_cac_pur.py` + committed `_regmap.json`/`_plumas_centroids.json`); coords from CDPR Plumas PLSS. The year label now shows **reported** use through 2026 (FACTS planned years, which carry acres not lbs, stay excluded).
- **Aug 2026 audit + deliveries** (commits 394d2b4/71ff22f/7045041) - (a) **Imperial roster** ingested: 8 CalAgPermits exports (2019-2027), 406 permits -> Imperial **0.6%->100% named**, statewide **73.3%->76.0%**; fixed a case-sensitive permit join in `enrich_operator_names.py` (`upper(right(owner,7))=permit`, for lowercase permit suffixes like Imperial `...131488n`). (b) **13 CPRA drafts staged** (unsent) in the spraymapca Drafts for the biggest un-requested naming gaps (Butte, Tehama, Ventura, LA, San Bernardino, Santa Clara, Alameda, Sonoma, SLO, San Benito, Sacramento, Glenn, Solano); letters committed at `records-requests/letters/14-25`. (c) **Water-monitoring gap surfaced**: Central Valley RWQCB (R5) records for the Dixie Fire/Greenville watershed show 3 stations monitored for post-fire recovery (sediment/metals/nutrients/bacteria) but **no herbicide analytes** - new Science card "Is the water tested for these herbicides? Not yet." (`data/water_monitoring.json`).
- **Org rename** — Plumas Grassroots **Collective**; site says "a registered California nonprofit" and **deliberately makes no 501(c)(3) / tax-deductible claim**.

## Automation
**`spraymap-data-asks-monthly`** (SKILL.md at `C:\Users\ryanv\.claude\scheduled-tasks\spraymap-data-asks-monthly\`) runs the **1st of each month, 9am**. It finds coverage gaps, scans the spraymapca inbox via **Chrome** (verifying the account), and **DRAFTS** the next CPRA asks + a summary — **never sends, never mutates the DB, never ingests**. Falls back to `records-requests/outbox/`. Its July run produced the Tulare/Madera/San Joaquin deliveries. (The 4 older `scrape-*` tasks are unrelated grocery scrapers, disabled since April.)

## Local files (gitignored — needed for re-loads)
`data/raw/cpra/`: `dpr_data.csv` (108 MB, CDPR extract 2020–2024, 5 NS counties), `dpr_vukich_spraymap_26-637.xlsx`, `fresno_permits.csv`, `applications_dpr_2023_2024.csv`, `acres_backfill.csv`, the coord backups, `ns_plss_centroids.csv`. `data/incoming/2026-07/` keeps the **normalized CSVs + README + `normalize.py`** in git; the raw `.xlsx`/`.zip` are ignored.

## Open / pending
1. **Enable Web Analytics** in the Vercel dashboard (script is live; no data until then).
2. **Donations** — flip `DONATE_CONFIG.comingSoon=false` + set a Givebutter/Donorbox URL. **Do not add tax-deductible wording** without an IRS 501(c)(3) determination letter.
3. **Gmail filters** — import `gmail-filters-spraymapca.xml` manually (agent upload is sandbox-blocked). Buckets: Records / Community / Finance / Press / Legal.
4. **Remaining CPRA gaps** — Ventura, Imperial, Madera(+) drafts sit in `records-requests/outbox/`; Los Angeles has no prepared letter. Statewide PUR is still **2020–2022** outside the NS spine.
5. **Statewide acres** — only NS has `acres`; a statewide re-derive needs the PUR archives (heavy).
6. **FRAP/parcel ownership** — only USFS point-in-polygon is done; CAL FIRE FRAP + assessor-parcel owner names are unbuilt (parcel owner names are **PII** — the project's stance is class-not-name).
7. **Ledger bookkeeping** — founder-paid domain as expense vs in-kind; whether to list shared Vercel hosting.
8. **Held cleanup (needs confirm)** — `build/process.py`, `build/facts.py`, old sync scripts, stub PDFs in `data/receipts/`, stale `data/agg/` offline fallback.

## Constraints (persist)
DB password **only** in `C:/Users/ryanv/.pg_dburl` — never commit or echo. Only the anon key in client HTML. **Never destructively mutate the shared DB; never duplicate data** (dedup by `app_id` / upsert on `operator_id`). The Transparency page stays honest — no fabricated figures, every ledger entry ties to a real receipt, and **no claim of tax-exempt status until it exists**. Sending email, submitting portals, and downloading files are **permission-gated** — prepare and ask.

## Plumas Working Forests (2026-08-02)
- **Program docs:** `program/` (README, full program, prescription standard, economics with pass/fail tests, stakeholders, pilot, policy asks, sources).
- **Stance:** case for industry to evaluate; implementation is owners' timber/business/land; volume parity **unproven** until CalTREES/mill data; publish FAIL if numbers don't work.
- **Site:** 6th nav tab **Working Forests** (`#workview`, `show('work')`). No DB changes.
- **Tool:** `python program/tools/volume_sketch.py` (illustrative T1 MBF sketch only).

## Cost ledger (same branch, 2026-08-02)
- `data/working_forests_costs.json` — absolute Plumas harvest (BBER A), CDTFA IHV (A), thin/fuels cost ranges (B), explicit D gaps for logging/release/plant/owner net.
- Site Working Forests tab section **Costs & losses** loads that JSON (`loadWfCosts`).
- Concurrent fills: `program/data/INTAKE.md`; validate with `python program/tools/cost_ledger.py --json-check`.
- Do not invent dollars; other instances may be filling PUR/operator data in parallel — stay off their lanes.

## Wholesale chain fill (2026-08-02 cont.)
- Filled stump-to-truck, delivered log, haul, biomass, residual stumpage worked examples from TCSI/MB&G Sierra study (B) + Chang thinning synthesis.
- Still D: plant, chemical release, manual release, full owner net, live 2026 mill quotes, lumber wholesale.
- Gaps closed: 5 A/B lines -> 12 A/B lines in cost ledger.
## Full gap-close pass (2026-08-02)
- Mill-gate proxies (Inland 2025 + coast DF ref), Plumas haul-to-Quincy/Lincoln, plant+chem vs manual practice bands, lumber futures + conversion band, modeled owner net/ac cases.
- Cost line items: 0 D remaining (13 A/B + 5 C). Upgrade C with SPI quotes / sealed release bids when available.

## Done-for-v1 (2026-08-02)
- WA DNR Eastside Mar 2026 mill-gate prices; USFS Plumas PTSAR FY2026 Q1; FOIA drafts in records-requests/letters/14-working-forests-unit-costs.md; program_complete_for_v1=true.

