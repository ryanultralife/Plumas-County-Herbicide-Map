# Economics & Volume Parity

**Purpose:** State how we test whether Working Forests can support **current harvest levels** and a viable business — and how we report failure.

**Rule:** Until local Plumas / Northern Sierra inputs replace defaults, all numeric examples are **illustrative**. They are scaffolding for the test, not proof.

---

## 1. What “works for industry” means

All of the following over a defined landscape and period (default: **ownership or district, 10 years**):

| Test | Pass if |
|---|---|
| **T1 Volume** | Working-forest MBF (+ contracted biomass cubic where mills count it) ≥ baseline clearcut-system MBF on the same land base |
| **T2 Mill** | Sort mix is actually purchased (no stranded log decks) |
| **T3 Logger** | Enough acres/days at rates crews will take |
| **T4 Owner NPV** | Owner accepts multi-entry cash flow vs clearcut pulse (their hurdle rate — not ours) |
| **T5 Chemical** | Broadcast free-to-grow lbs ≈ 0 under the Standard |

**If T1–T4 fail, the industrial case fails.** T5 alone is not a business case.

---

## 2. Cost structure (qualitative, both systems)

### Clearcut + plant + chemical release (status quo pathway)

| Item | Direction |
|---|---|
| Logging $/MBF | Often **lower** (simple unit, high volume/acre) |
| Site prep + plant | Material cost |
| Herbicide release | **Low $/ac** relative to manual; this is why it is common |
| Road / layout | Spike with large units |
| Cash flow | Large pulse, then long wait |
| Risk | Social license, fire in young plantations, reforestation liability |

### Working forest (thin + small gaps + mechanical/manual)

| Item | Direction |
|---|---|
| Logging $/MBF | Often **higher** (partial cut, more careful ops) |
| More acres/year | Can raise **total** logger revenue even if $/MBF rises |
| Release | Mechanical/manual **higher $/ac** unless design reduces need |
| Cash flow | Smaller, **more frequent** entries |
| Co-products | Biomass/chips may make or break thin economics |
| Co-pay | Fuels / Forest Health / stewardship $ can close gaps on public-benefit acres |

**Industry already knows this tradeoff.** The open question is whether Plumas-scale markets and cost-share make T1–T4 pass.

---

## 3. Volume parity method

### Baseline (B)

For the land base and 10-year window:

\[
\text{MBF}_B = \sum (\text{acres regenerated harvest}_t \times \text{MBF/ac}_t) + \text{other commercial volume}
\]

Sources: CalTREES / THP completion, company reports, USFS cut/sold, FACTS timber volumes.

### Working forest (W)

\[
\text{MBF}_W = \sum (\text{thin acres}_{t} \times \text{MBF/ac thin}) + \sum (\text{gap acres}_{t} \times \text{MBF/ac gap}) + \text{biomass credited}
\]

With re-entry: the same acre may contribute in year 0 and year 20 — only count harvests **inside** the 10-year window unless you extend the window and say so.

### Parity

\[
\text{Parity ratio} = \text{MBF}_W / \text{MBF}_B
\]

- **≥ 1.0** → volume thesis supported for that scenario.  
- **&lt; 1.0** → thesis **fails** unless acres or MBF/ac assumptions change and are re-validated.  
- Publish the ratio and the inputs; do not hide a fail.

### Illustrative sketch only

```text
Example (NOT Plumas-validated):
  Baseline: 1,000 ac clearcut / 10 yr × 30 MBF/ac     = 30,000 MBF
  Working:  4,000 ac thin / 10 yr × 8 MBF/ac          = 32,000 MBF
  Parity ratio ≈ 1.07  → passes T1 in this toy model
```

Replace every number with local data before any public “we can match harvest levels” claim.

Tool: `python program/tools/volume_sketch.py --help`

---

## 4. Data we need (and do not yet have in-repo)

| Input | Why | Status |
|---|---|---|
| Plumas / nearby **mill capacity** and sort prices | T2 | **Gap** — interview / public reports |
| Contract logging rates thin vs clearcut | T3 | **Gap** |
| Owner stumpage expectations | T4 | **Gap** (confidential) |
| CalTREES harvest acres by method | Baseline | **Gap** — next data pull |
| USFS cut/sold + FACTS | Public baseline | Partial (FACTS on map; volumes need compile) |
| Chemical $/ac vs mechanical $/ac local bids | Cost gap | **Gap** |
| Biomass offtake reliability | Thin economics | **Gap** — plant status changes |

**spraymapca already has:** private herbicide use intensity (PUR) — the chemical side of the status quo cost/impact picture, not the MBF side.

---

## 5. Side-by-side template (fill later)

| Line | Clearcut system | Working forest | Source |
|---|---|---|---|
| Acres/year commercial | | | |
| MBF/ac | | | |
| MBF/year | | | |
| Logging $/MBF | | | |
| Regen + release $/ac | | | |
| Herbicide lbs/ac | (PUR / plan) | 0 broadcast | |
| Net $/ac to owner | | | |
| 10-yr MBF | | | |
| Parity ratio | 1.00 | **?** | |

Until filled: **do not assert T1 pass for Plumas.**

---

## 6. When subsidies are honest

Public cost-share (CAL FIRE Forest Health, GGRF, IRA/IIJA, stewardship contracts, SNC, etc.) is legitimate when:

- The public is buying **fire, water, or habitat** outcomes beyond private timber NPV; and  
- The gap is measured (mechanical release − chemical release, or thin deficit vs no treatment).

Subsidies are **not** a substitute for T2 (mill won’t buy the log). Paying to cut wood no one can process fails the industry case.

---

## 7. Reporting standard for this program

| Finding | Public language |
|---|---|
| Parity ≥ 1, costs acceptable to owner | “Data support Working Forests at landscape volume for [unit/ownership].” |
| Parity &lt; 1 | “Under current assumptions, Working Forests **do not** match baseline harvest; options: more acres, different product mix, or accept lower MBF.” |
| Data missing | “**Insufficient data** — no volume claim.” |
| Owner rejects NPV | “Silviculture may work; **business case rejected by owner** — their land, their call.” |

Honesty on a fail is part of the program’s credibility — same as spraymapca’s honesty on FOIA gaps for federal chemicals.
