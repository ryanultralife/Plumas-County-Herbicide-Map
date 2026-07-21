# Incoming county permit data — July 2026

Pulled from the spraymapca@gmail.com inbox on 2026-07-21. Source files are kept
verbatim; the `*.csv` files are the normalized `operator_id,name` extracts ready
for `build/ingest_operator_names.py`.

| Source file | From | Received | Normalized CSV | Unique IDs |
|---|---|---|---|---|
| `sanjoaquin/2025 Permits Commodities.xlsx` | Monica Hernandez, San Joaquin Co. Ag Comm. | Jul 13 | `sanjoaquin-2025.csv` | 1,698 |
| `sanjoaquin/2026 Permits Commodities.xlsx` | Monica Hernandez, San Joaquin Co. Ag Comm. | Jul 13 | `sanjoaquin-2026.csv` | 1,663 |
| `Madera County Permits Sites Commodities 2020 to 2026.xlsx` | William Griffin, Madera Co. Ag Comm. | Jul 13 | `madera-2020-2026.csv` | 1,059 |
| `Spraymap California Data Request.xlsx` | Tulare Co. via NextRequest #26-638 | Jul 13 | `tulare-2020-2026.csv` | 3,290 |

All four are CalAgPermits "Permits, Sites and Commodities" exports. Normalization
(`normalize.py`) takes the `Permit Number` and `Operator` columns, dedupes on permit
number, and carries `Permit Type` through as `entity_type`.

Leading-2-digit sanity check passed: 39xxxxx (San Joaquin), 20xxxxx (Madera),
54xxxxx (Tulare) dominate each file, with a small tail of out-of-county permittees.

## To ingest

```
DBURL="postgres://..." python build/ingest_operator_names.py \
  data/incoming/2026-07/tulare-2020-2026.csv --county "Tulare" --source "cac-tulare-2026"
```
...and likewise for the other three (`--county "San Joaquin" --source "cac-sanjoaquin-2025"`, etc.).

**Note:** `build/ingest_operator_names.py` is not on the current branch — it only exists
under `.claude/worktrees/`. Merge or copy it into `build/` before running the above.
