"""Generate data/nonag_coverage.json: the county-level-only (non-ag) applications
that have no PLSS section and so aren't on the map -- counted by category, with
the named Plumas operators from the original county Excel. Honest surfacing of the
~57% of some counties' records that the section-based map necessarily omits."""
import csv, collections, json, os
csv.field_size_limit(100_000_000)
ROOT = r"C:\Users\ryanv\Projects\Plumas-County-Herbicide-Map\.claude\worktrees\suspicious-sammet-763560"
SRC = os.path.join(ROOT, "data", "raw", "cpra", "dpr_data.csv")
XLSX = os.path.join(ROOT, "data", "Plumas County Pesticide Applications 2021-2024.xlsx")
OUT = os.path.join(ROOT, "data", "nonag_coverage.json")
YEAR, USE_NO, SITEN, AGNON, COUNTY, COMTRS = 0, 1, 7, 24, 32, 33
NS = {"BUTTE", "TEHAMA", "LASSEN", "PLUMAS", "SIERRA"}

# 1) count county-level-only (no 11-char section) non-ag apps by county + site category
cty = collections.defaultdict(lambda: {"count": 0, "cats": collections.Counter()})
seen = set()
with open(SRC, encoding="utf-8") as f:
    r = csv.reader(f); next(r)
    for row in r:
        if len(row) <= COMTRS: continue
        c = (row[COUNTY] or "").strip().upper()
        if c not in NS: continue
        cm = (row[COMTRS] or "").strip()
        if len(cm) == 11: continue                 # has a section -> already mapped
        if (row[AGNON] or "").strip().lower() != "non-ag": continue
        key = (row[YEAR], row[USE_NO])
        if key in seen: continue
        seen.add(key)
        name = c.title()
        cty[name]["count"] += 1
        cat = (row[SITEN] or "OTHER").strip().title()
        cty[name]["cats"][cat] += 1

# 2) Plumas non-ag operator names from the original county Excel (Non-Prod sheet)
plumas_ops = []
try:
    import openpyxl
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb["Non-Prod Ag MSPUR"]
    rows = ws.iter_rows(values_only=True); hdr = list(next(rows))
    oi = hdr.index("Operator")
    ops = collections.Counter()
    for r in rows:
        v = (str(r[oi]).strip() if r[oi] else "")
        if v: ops[v] += 1
    plumas_ops = [o for o, _ in ops.most_common()]
except Exception as e:
    print("(excel ops skipped:", e, ")")

out = {"note": "Applications reported to the county at county level only (no PLSS section) -- mostly non-production uses in town/roadside, which the section-based map cannot place. Not part of the forestry-herbicide story this map focuses on, but shown here for completeness.",
       "counties": {}}
for name, d in cty.items():
    out["counties"][name] = {"count": d["count"],
                             "top_categories": [[k, v] for k, v in d["cats"].most_common(6)]}
out["counties"].setdefault("Plumas", {"count": 0, "top_categories": []})
out["counties"]["Plumas"]["operators"] = plumas_ops
with open(OUT, "w") as f:
    json.dump(out, f, indent=1)
tot = sum(d["count"] for d in cty.values())
print(f"NS county-level-only non-ag apps: {tot:,}")
for name, d in sorted(cty.items()):
    print(f"  {name}: {d['count']:,}  top: {[k for k,_ in d['cats'].most_common(3)]}")
print(f"Plumas named non-ag operators: {len(plumas_ops)}")
print("wrote", OUT)
