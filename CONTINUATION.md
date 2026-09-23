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

**Client cache key is `CELLS_KEY='map_agg:v10-adjuvants:...'`** — bump it in `index.html` whenever `map_agg`'s *data* changes, not just its columns (the built-in revalidation only compares row **count**, so a coordinate-only change can slip through).

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

## Open / pending (refreshed 2026-09-14)
1. **Enable Web Analytics** in the Vercel dashboard (script is live; no data until then).
2. **Donations** are LIVE (PayPal, three hosted buttons, real-time IPN + daily reconcile). Still open, all user-side:
   set `PAYPAL_CLIENT_ID`/`PAYPAL_CLIENT_SECRET` in Vercel to enable the daily API backfill; CT-1 charitable
   registration; the 501(c)(3) application. **No tax-deductible wording until the IRS letter.**
3. **Gmail filters** - import `gmail-filters-spraymapca.xml` manually (agent upload is sandbox-blocked).
4. **Records requests** - 47 rows in `data/records_requests.json`. User-side actions:
   - SEND the CARB draft (in spraymapca Drafts) and the Tehama receipt reply (also in Drafts).
   - PORTALS, text ready in `records-requests/outbox/`: CAL FIRE Forest Health grant records (GovQA), BLM
     California FOIA (FOIA.gov), San Benito / San Luis Obispo / Ventura operator names.
   - Email Solano's filled PRA form; Los Angeles needs a signed form.
   - Sign in to Alameda's NextRequest portal (#26-763): PUR 2020-present, Sites 2020-present, RMP/OPIDs 2026
     are uploaded and waiting. The PUR file may feed `applications`, not only operator_names.
   - Kings and Yuba operator-name letters still need verified recipients.
   - Follow up DPR's Groundwater Protection Program referral if nothing arrives by early October.
5. **Statewide acres** - 2023 carries acres for every county. 2020-2022 backfill from the CDPR archives
   (`build/backfill_pur_acres.py`) run 2026-09-14; see the section at the bottom for the result.
6. **CDPR PUR 2024** - not published (`pur2024.zip` 404s as of 2026-09-14). Check monthly.
7. **FRAP/parcel ownership** - only USFS point-in-polygon is done; CAL FIRE FRAP + assessor-parcel owner names
   are unbuilt (parcel owner names are **PII** - the project's stance is class-not-name).
8. **Ledger bookkeeping** - founder-paid domain as expense vs in-kind; whether to list shared Vercel hosting.
9. **Held cleanup (needs confirm)** - `build/process.py`, `build/facts.py`, old sync scripts, stub PDFs in
   `data/receipts/`, stale `data/agg/` offline fallback.
10. **Carbon angle** - internal memo `program/carbon-angle-first-take.md`. The central accounting claim was
    verified cell-by-cell in CARB's own calculator on 2026-09-14 (understory debit keyed to site-prep acres
    only). Not site copy; publish only as an accounting-transparency piece, never a tonnage or dollar figure.

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

## Working Forests tab — HIDDEN (2026-09-05)
Hidden at the user's request, code intact. To re-enable: (1) remove `style="display:none"` from `#bwork` in the nav;
(2) in the `DEEPLINK` parser restore `forests:'work'` in `ALIAS` and `work:1` in the tab whitelist;
(3) delete the `if(v==='work')v='map';` guard at the top of `show()`. The goat-grazing card lives on that tab, so it is hidden too.

## Map class labels
`clsLabel(cl)` is the single display helper — `unknown` renders as **"not reported"** (record omits product/AI;
mostly federal FACTS rows). The map key now lists a "not reported" row so gray dots are explained.

## Records-request tracker (2026-09-05)
`data/records_requests.json` is the canonical per-request log (agency, county, program, channel, ref, sent, status, received, outcome, effect, notes; status vocabulary in the file). Rendered on the **Source Data** tab as "Records requests — the paper trail" (`renderRecordsRequests()`); rows `sent`/`acknowledged` with no reply >30 days show as **follow-up due**. The monthly `spraymap-data-asks-monthly` task reads/updates it (never deletes rows; never marks `ingested` — a human does after loading). Office-level agency names only — never staff names/emails. Also fixed: `?tab=` deep links now apply after DOMContentLoaded (tab renderers live in later script blocks, so an early `show()` used to leave the tab empty on arrival).

## Records requests — Sept 2026 batch (2026-09-06/07)
Tracker is now **44 rows**. Five new agencies added and drafted (`records-requests/outbox/new-agencies-2026-09/`):
Sierra Valley GMD (Sierra County named it as the agency that actually holds the basin's wells), Caltrans D2 and
Plumas County Public Works (roadside spraying by route/postmile and road name — county PUR totals never say *where*
along a highway), BLM California PUPs, and Mendocino AgComm operator names.
**16 letters sit unsent in the spraymapca Drafts folder**; the user sends. BLM is portal-only (no draft).

**Draft-verification gotcha:** Gmail autosave is not proof the fields landed. Two drafts were found damaged —
one had lost its To *and* Subject, another had a stray second recipient. Re-open every draft and read back
`[data-hovercard-id]` and `input[name=subjectbox]` before calling a drafting session done.

## DPR Well Kit analyte list (2026-09-07)
`data/dpr_well_kit_analytes.json` — the 94 compounds DPR's Groundwater Protection Program screens for in its
statewide domestic-well sampling, verbatim from the spreadsheet DPR emailed us on Aug 7.
**It covers hexazinone, and triclopyr marked "(marginal)". It does not cover glyphosate, AMPA, imazapyr,
aminopyralid, clopyralid or sulfometuron-methyl.** That is the state pesticide regulator's own screen missing
the herbicides being applied across the Plumas National Forest footprint. It is a third independent confirmation
of the Science tab's "the water isn't tested for these" finding, alongside the Central Valley Water Board and
Sierra County. **Not yet surfaced on the site** — it belongs on the Science tab beside the two county answers.
Reading it required unzipping the xlsx inside the Gmail tab (`DecompressionStream('deflate-raw')` over the ZIP
local headers, then the `<t>` nodes of `sharedStrings.xml`); the preview pane virtualizes to ~50 rows and looks
complete when it is not, and the JS bridge blocks base64 payloads.

## Statewide PUR 2023 loaded (2026-09-07)
The table is **15,854,861 rows**, not 12.0M. Every county now has **2020-2023**; 2024 is still
Northern-Sierra-only because CDPR has not published `pur2024.zip` yet (it 404s - check monthly).

- **Where the raw data actually lives:** `files.cdpr.ca.gov/pub/outgoing/**pur_archives**/pur2023.zip`
  (260 MB). The path `pub/outgoing/pur/data/2023_pur_report_textfiles*` holds only summary reports,
  not application records. Do not go looking there.
- **Loader:** `build/ingest_pur_statewide.py <year> [--load]`. Takes a whole year for all 58 counties.
  One row per application, keeping the largest-pounds active ingredient (never a sum), matching
  `build/ingest_dpr_pur.py`. Inserts `ON CONFLICT (app_id) DO NOTHING`.
- **The dedup trap:** the Northern Sierra already held 2023 from the CPRA extract, and both sources
  key `pur:{year}:{use_no}` in the same integer space. **Verify overlap by set intersection against a
  dump of the existing app_ids before inserting.** A psql `IN (...)` spot check reported 1/200 when
  the truth was 200/200. Actual result: 79,441 of 80,164 NS rows already present and skipped, 723 new,
  0 collisions among 3,841,654 non-NS rows, 0 duplicate app_ids after the load.
- **Always do these three in the same sitting**, or the site publishes a false regression:
  1. plain `refresh materialized view` (NOT concurrently) for map_agg, juris_agg, app_samples;
  2. water-safe placement for the new rows (94 sections were in lakes; 22 fully-water kept at centre,
     72 moved within-section, 5,686 rows updated; map cells in water back to 0);
  3. `enrich_operator_names.py` then `gen_operator_coverage.py` - coverage read 63.2% right after the
     load purely because the denominator grew, and came back to **79.5%** (up from 77.8%) once the
     2023 GROWER_IDs were matched.
- Site copy: six places that said the statewide data stops at 2022 now say 2023, the "years covered"
  note explains 2024 is the Northern-Sierra year, and `CELLS_KEY` is **v11-pur2023**.
- Partially closes open item 5 (statewide acres): 2023 carries `acre_treated` for 79.6% of rows.
  2020-2022 still have acres only for the Northern Sierra.

## Statewide acres backfilled for 2020-2022 (2026-09-14)
`build/backfill_pur_acres.py 2020 2021 2022 --load` filled `acres` from the CDPR year archives
(`pur_archives/pur{YEAR}.zip`, 160-190 MB each, kept under `data/raw/pur/`, gitignored). Only
`acre_treated` rows with `unit_treated = 'A'` count; only NULLs are filled, so the Northern-Sierra
rows that already had acres are untouched and a re-run is a no-op.

| year | rows with acres | share |
|---|---|---|
| 2020 | 3,435,033 of 4,204,326 | 81.7% |
| 2021 | 3,189,667 of 3,968,669 | 80.4% |
| 2022 | 2,929,752 of 3,660,707 | 80.0% |
| 2023 | 3,122,920 of 3,922,636 | 79.6% (from the Sept 7 load) |

Each year ran as one UPDATE (about 25 minutes per year through the pooler; a county-by-county retry
exists if the connection drops). `map_agg` refreshed afterwards - it is the only view that carries
acres. Open item 5 is closed; the remaining ~20% per year are applications the state reports in
square feet, cubic feet, pounds or units rather than acres.

## Map "Type" filter (aerial / ground / fumigation / other) - 2026-09-22
The scopebar above the map has a **Type** select (`#scopeMethod`, `onScopeMethod`, deep link `?method=aerial`).
It filters on `map_agg.meth`, a per-cell jsonb of application type -> [count, lbs] built from
`applications.method` (canonical labels from CDPR `AER_GND_IND`, backfilled by `build/backfill_pur_method.py`).

**Why it looked broken:** the page code shipped (commit 60d49e2) before the database view was rebuilt.
The client requests `map_agg?select=...,meth`; when that column is missing PostgREST answers 400 and the
page *silently* falls back to the old column set, so the map renders, the Type menu shows, and choosing
Aerial does nothing (the map stat says "application type is still loading" forever). Nothing in the
console makes this obvious. **Any change to `supabase/map_aggregate.sql` must be followed by a rebuild:**

    DBURL=... python build/backfill_pur_method.py --refresh-map

That builds `map_agg_next`, then swaps it in inside one transaction (drop old, rename, rename index,
re-grant select to anon), so the public map never goes dark. A plain `refresh materialized view` is NOT
enough when columns change. Verify from the public side, not just psql:

    curl "$SB_URL/rest/v1/map_agg?select=lat,lon,meth&limit=1" -H "apikey: $SB_KEY" -H "Authorization: Bearer $SB_KEY"

A 200 with a `meth` object means the Type filter is live; a 400 "column map_agg.meth does not exist"
means the page is on its fallback. `CELLS_KEY` is already `v14-method`; browsers that cached the
fallback under the v13 key pick up the real data on their next load without a key bump.


## State drinking-water compliance records for Plumas (2026-09-22)
DDW answered PRA #638 by pointing to its public EDT Library bulk files instead of producing a county
extract, so we pulled them: `SDWIS3.zip` (2019-2022), `SDWIS4.zip` (2023-2025), `SDWIS5.zip` (2026-),
about 800 MB, under `data/raw/edt/` (git-ignored; re-download from the EDT Library page). A streaming
filter on "Principal County Served" = PLUMAS or system number `CA32*` gives 15,037 rows
(`data/incoming/2026-09/edt-plumas/plumas_sdwis_2019_2026.tsv`, committed); `build/gen_edt_plumas.py`
writes `summary.json`. Findings on the Science tab: 184 systems, 174 analytes, glyphosate tested 14 times
at one system (Plumas Eureka CSD, all below the 25 ppb reporting level), no other forestry herbicide
ever tested in the county. Re-run when SDWIS5 is refreshed (roughly quarterly).

## Plumas public water systems on the map (2026-09-22)
Layer "Public water systems - state test records (Plumas)", on by default, built from
`data/water_systems_plumas.json` (loader `loadWaterSystems()`, builder registered next to the
Water Board station layer in `buildMap()`). One entry per system in the state compliance pull
(175 of 184 located): **42 at the centroid of the state's mapped service area** (SWRCB "California
Drinking Water System Area Boundaries" FeatureServer, `service_area_centroid`, with area_km2) and
**133 with no public boundary grouped into one marker per town** (`town_centroid_approx`, OSM place
centroid via Nominatim). Nine systems had no public address at all and are listed under `unlocated`
in the JSON, deliberately not placed. Popups carry each system's test record from
`data/incoming/2026-09/edt-plumas/systems.json` (results, analytes, date span, herbicide tests).
The builder is async-from-cache and idempotent, so `rebuildLayers()` is safe. Regenerate by
re-running the EDT summary, then re-merging stats into the JSON (see the 2026-09-22 session notes).

## Live share-preview count (2026-09-23)
`middleware.js` (Vercel middleware, matcher `/` only) rewrites the `description` and `og:description`
meta tags with the live mapped-application total for link-preview and search bots only (UA regex);
humans get the static file. The number comes from `public.map_totals()` (see `supabase/map_totals.sql`),
a read-only function over `map_agg` that anon may call: `POST /rest/v1/rpc/map_totals` -> `{mapped, cells,
lbs, as_of}`. Cached in the edge instance for an hour; any failure falls open to the static page. The
static tags keep a rounded fallback ("13 million") - do not hand-edit it to a precise figure again.
Test: `curl -A facebookexternalhit/1.1 https://www.spraymapca.org/ -D -` and look for
`X-Spraymap-Live-Count`. Facebook and X cache previews: after a data load, re-scrape the URL in the
Facebook Sharing Debugger / X Card Validator to refresh what they show.

## New-data bubble (2026-09-23)
- Floating pill above the donate bubble; follows the "Showing:" county/region. Shows the latest load for that area with a **NEW** tag while under 7 days old; tapping it lists recent loads plus the records requests still open for the area.
- Source: **`data/ingest_log.json`** (committed, like `records_requests.json`). Started with the week of Sep 17-23 only; no older backfill by decision.
- **After every load that changes the site, append a row:** `python build/log_ingest.py --county <County> --kind applications|names|water|fix --source "..." --rows N --summary "..." [--request <tracker id>]`. Real numbers only.
