# SprayMap California — Continuation / Handoff

_Snapshot: 2026-07-08. Branch `claude/suspicious-sammet-763560`, all work committed + pushed to `main` (tip `2384442`). Deploys via Vercel from `main`._

## What this is
A single static **`index.html`** (Leaflet map + tabs) backed by **Supabase Postgres**, mapping California's reported pesticide/herbicide use. Spine = **Plumas + the Northern Sierra** (Butte, Tehama, Lassen, Plumas, Sierra); statewide context around it. The organization behind it is the **Plumas Grassroots Cooperative** (organizing as a CA nonprofit — not yet incorporated). Public transparency is the whole point: name operators, show pounds/acres, track the org's own spending.

## Live / deploy
- Vercel project **`plumas-county-herbicide-map`** (team `ryan-vukichs-projects`), auto-deploys from `main`. Live now at `plumas-county-herbicide-map.vercel.app`.
- **Domain `spraymapca.org` is wired** (bought on GoDaddy 2026-07-08, order #4131715574, $10.19). Vercel has `spraymapca.org` (308→www) + `www.spraymapca.org` (production). GoDaddy DNS set: **A `@` → 76.76.21.21**, **CNAME `www` → cname.vercel-dns.com**. `www` was already resolving to Vercel; the apex was still on GoDaddy's cached parking IP at snapshot time — **verify it has flipped + Vercel shows "Valid" + SSL issued** (should be automatic within ~1h of the DNS change).

## Backend (source of truth = Supabase, NOT git)
- Connect: `source C:/Users/ryanv/.pg_dburl` (sets `$DBURL`; **secret — never echo/commit**), then `psql "$DBURL"`. Anon key is public in `index.html` (safe; read-only views only).
- **`public.applications`** — 12,012,003 rows (pur 12,001,289 · facts 10,714). Statewide PUR = 2020–2022; **2023–2024 exists only for the 5 Northern Sierra counties** (167,587 rows loaded this session from the CDPR CPRA extract, DPR request #26-637). New column **`acres`** populated for those 5 counties (366,067 rows); statewide acres would need a re-derive from the PUR archives.
- **`map_agg`** matview (drives the map) — now includes `acres`; client cache key is **`map_agg:v6-acres`** (bump `CELLS_KEY` in index.html if its SELECT columns change).
- **`juris_agg`** matview — `top_owners` is now 3-element `[owner, count, lbs]` (Top-operators table sorts by either).
- **`operator_names`** — 29,593 IDs named (statewide 63.1%, Plumas 76.9%); join is `right(applications.owner,7) = county permit number`.
- **After any data load:** `refresh materialized view concurrently public.map_agg, public.juris_agg;` (+ `public.app_samples`). Rebuild (drop+create) only when the view's columns change. Pooler kills statements >~2min → run refreshes/loads in a background shell; single autocommit statements commit server-side even if the client drops.

## This session's work (commits `a54764d`..`2384442`)
- **Data:** loaded DPR 2023–2024 for the 5 NS counties (deduped, water-safe coords, 0 dots in water); added `acres` + backfilled NS; re-ran operator-name enrichment (added the fuller Fresno CPRA roster).
- **Map:** dots sized by **pounds** (not count); default is one **"All applications"** layer (per-class layers are optional toggles, desktop-only); legend + layer control roll up; **streams/waterways always on, not a toggle**; top **applications stat collapses to an ⓘ chip** (hover/tap to read).
- **Popups:** show acres treated + avg lb/acre (NS cells); **federal USFS contacts** on national-forest cells (Region 5 + 19 forests, county→forest map).
- **Mobile:** content cards on Data/Science/Transparency roll up (tap heading).
- **Data & Trends:** Top operators sortable by count or pounds (default pounds).
- **Transparency:** added the **Plumas Grassroots Cooperative mission/vision** (from Taylor Durgan's founding doc); ledger is now **real** (sample data dropped) — first real bill = the GoDaddy domain ($10.19, founder-paid); **workers/contractors shown by role/code, not name** (orgs + amounts in full); **donate button = "coming soon"**; **project contact = spraymapca@gmail.com** (mission card + donate modal).

## Local files (gitignored — needed for re-loads, not in repo)
`data/raw/cpra/`: `dpr_data.csv` (108MB, the full CDPR extract, 2020–2024, 5 counties), `dpr_vukich_spraymap_26-637.xlsx` (80MB original), `fresno_PermitSearchResults-ALL.xlsx` + `fresno_permits.csv` (Fresno CPRA roster, 355k rows), `applications_dpr_2023_2024.csv`, `acres_backfill.csv`, `federal_contacts_usfs.json`. Key build scripts: `build/ingest_dpr_pur.py` (canonical DPR loader), `build/fix_water_coords.py`, `build/enrich_operator_names.py`.

## Open / pending (next session)
1. **Domain:** confirm `spraymapca.org` apex resolves to Vercel + cert issued; then update canonical/OG URLs in `index.html` (currently `plumas-county-herbicide-map.vercel.app`) to `spraymapca.org`.
2. **Data-asks (CPRA)** — see memory `data-asks.md`: reply to **San Joaquin** (Monica Hernandez) with scope; resubmit **Tulare** via `countyoftulareca.nextrequest.com`; **Kern** (kernag.com) + **Stanislaus** (open-data-stancounty-gis.hub.arcgis.com) are self-serve downloads not yet ingested. All replies/downloads are permission-gated.
3. **Statewide acres** — re-derive from PUR archives if wanted (heavy; archives not cached locally).
4. **Ledger bookkeeping (user's call):** treat founder-paid domain as expense (current, cash −$10.19) vs in-kind ($0); whether to list Vercel Pro hosting (shared account).
5. **Donate:** set `DONATE_CONFIG.comingSoon=false` + a Givebutter/Donorbox URL when giving opens.
6. **Held repo cleanup (needs confirm):** `build/process.py`, `build/facts.py`, old sync scripts (`sync.bat`, `sync-watch.ps1`, `scrape-all.bat`, `publish-data.ps1`); orphaned stub PDFs in `data/receipts/`; the DB `_water` table (harmless).
7. **Offline fallback `data/agg/`** is stale (2020–2022, no acres) — only used if Supabase is down; regenerate if desired.

## Constraints (persist)
DB password only in `C:/Users/ryanv/.pg_dburl`, never commit. Only the anon key in client HTML. Never destructively mutate the shared DB; never duplicate data (dedup by `app_id`). Transparency page must stay honest — no fabricated figures; every ledger entry ties to a real receipt.
