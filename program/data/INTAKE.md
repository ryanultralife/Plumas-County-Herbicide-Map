# Cost & harvest data intake (for concurrent agents)

**Goal:** Fill absolute cost / loss numbers for every major logging method until the Working Forests tab can show a complete comparison without hand-waving.

**Canonical machine file (site reads this):**  
`data/working_forests_costs.json`  
(served statically next to `data/ledger.json`)

**Do not:** invent numbers, touch PUR/Supabase ingest, or claim Plumas owner net profit without a source.

---

## Confidence grades (required on every value)

| Grade | Meaning |
|---|---|
| **A** | Official CA schedule or stable public harvest series |
| **B** | Peer-reviewed / multi-study regional range |
| **C** | Illustrative only |
| **D** | Gap — use `null` |

---

## Priority fills (highest first)

1. **Logging $/MBF** — clearcut vs commercial thin (local LTO or published CA appraisal).  
2. **Release $/ac** — broadcast chemical vs manual vs mechanical.  
3. **Plant $/ac** — green clearcut vs post-fire.  
4. **CalTREES** — Plumas acres + volume **by silvicultural method**.  
5. **Mill delivered $/MBF** by sort (pond value).  
6. **USFS Plumas** cut/sold + appraisal worksheets.  

When you fill a field in JSON:

- Set `low` / `mid` / `high` as available.  
- Set `confidence`, `source`, `source_url` or citation, `year_context`.  
- Move the id off `next_fills_priority` if closed.  
- Bump root `"updated"` date.  
- One-line note in `CONTINUATION.md` under Working Forests.

---

## Parallel work boundaries

| Lane | Owner-ish | Files |
|---|---|---|
| PUR / map / operators | Existing spraymap pipeline | `build/`, `scraper/`, Supabase |
| Working Forests costs | This program | `data/working_forests_costs.json`, `program/` |
| Site chrome | Either | `index.html` workview + `loadWfCosts()` |

If both land JSON edits, merge carefully — prefer additive fills of `null` fields over rewrites of A-grade series.

---

## Validation

```bash
python program/tools/cost_ledger.py
python program/tools/cost_ledger.py --json-check
```

Site: open Working Forests tab → **Costs & losses** section should load the JSON (or show offline note).
