# Plumas data — provenance & status

## plumas_nf_herbicide_facts.geojson / .csv  (FEDERAL land — PRIMARY)
- **Source:** USDA Forest Service EDW, *Activity FACTS Common Attributes* layer
  (`EDW_ActivityFactsCommonAttributes_01/0`).
- **Filter:** `fs_unit_id='0511'` (Plumas NF) AND `method='Chemical'`, FY2020+.
- **Pulled:** 2026-06-24.
- **Records:** 296 herbicide/chemical treatment points; **109 carry full detail**
  (acres, NEPA project, ranger district); 6 are planned (not yet completed).
- **Fields:** activity, year, status (completed/planned), acres, nepa_project,
  district, detail (full|basic).
- **Completeness:** PARTIAL — the in-app fetch tool caps response size, so each
  full-field page truncates (~29 records). This captured 296 of ~398 points and
  full detail on 109. **Run `scripts/pull_facts.py` on a networked machine for 100%**
  (all completed + planned, every field). The sandbox here has no outbound network.
- **NEPA projects seen:** Moonlight Fire Invasive Plant Treatment, PG&E Herbicide
  Vegetation Management Program, Storrie/Rich Fire invasive plant treatment,
  Moonlight Fire Area Restoration, Mt. Hough–South Park trail project.
- **Activity mix:** ~63% *Invasives – Pesticide Application*, ~25% *Right of Way
  Maintenance*, ~14% *Tree Release and Weed*, plus *Site Prep – Chemical*.

> `plumas_nf_herbicide_facts_2020-2025.geojson/.csv` is the earlier basic-only
> extract (lat/lon/activity/year). The file above supersedes it.

### To get the COMPLETE + richer dataset
Run on any networked machine (no URL/size caps):
```
pip install requests
python scripts/pull_facts.py
```
This writes `plumas_nf_herbicide_facts.geojson` + `.csv` with all completed **and**
planned chemical treatments, including acres, NEPA project, and ranger district.

## Not yet scraped (documented in the source inventory spreadsheet)
- **SOPA** planned actions — `https://www.fs.usda.gov/sopa/components/reports/sopa-110511-YYYY-MM.html`
- **NEPA project docs** (incl. Community Protection Project, project 62873)
- **Chemical name & quantity on federal land** — FOIA only (draft request prepared)
- **Private land (CA PUR)** — already in the map; refresh via CalPIP for 2020 + 2025

The map's existing private-land dots come from CA Pesticide Use Reporting (PUR);
this federal FACTS layer is the new public-land complement.

## ledger.json  (PUBLIC TRANSPARENCY LEDGER)
Feeds the **Transparency** tab in `index.html`. The app fetches this file at runtime,
so updating it (and publishing) updates the live ledger - exactly like the map data.

- **Shape:** `{ org, updated, currency, note, donations[], expenses[], hours[] }`
  - `donations[]`: `date, source, gross, fees, type (Unrestricted|Restricted-Testing), platform, src, srcLabel`
  - `expenses[]`:  `date, payee, bucket (Operations|Testing|Admin), amount, via, src, srcLabel`
  - `hours[]`:     `date, person, task, role, hours, rate, approvedBy, src, srcLabel`
- **Click-through sources:** every entry may carry `src` (a URL or repo-relative path)
  and `srcLabel` (link text). These render as verifiable links in the ledger. Put
  backing documents in `data/receipts/` and reference them with a relative path,
  e.g. `data/receipts/2026-07-15-norcal-lab-invoice.pdf`.
- **Computed in the app (do not store):** net = gross - fees; hours $ value = hours x rate;
  cash on hand = net donations - total expenses. Logged hours are labor record only -
  the cash paid for them is entered once under Expenses (Operations), so no double-count.

### Update it
```
python scripts/ledger_tool.py summary          # show current totals
python scripts/ledger_tool.py add-donation ...  # see --help for all flags
python scripts/ledger_tool.py add-expense ...
python scripts/ledger_tool.py add-hours ...
```
Then run `publish-data.ps1` to commit + push (it already stages the whole `data/` folder).
The standalone `Transparency_Ledger_Template.xlsx` in the repo root is an optional
offline bookkeeping copy; `data/ledger.json` is the source of truth for the website.

## receipts/  (backing documents)
Source documents linked from `ledger.json`. The seed entries point to PLACEHOLDER PDFs -
replace each with the real receipt/invoice/award letter/chain-of-custody form, keeping
the same filename (or update the `src` path in `ledger.json`).
