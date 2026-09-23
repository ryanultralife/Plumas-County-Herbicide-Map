#!/usr/bin/env python3
"""Nevada, El Dorado and Alpine county operator rosters -> data/incoming/2026-09/{nevada,el-dorado,alpine}-2020-2026.csv

Sources (all CalAgPermits 'Permits, Sites and Commodities' exports, sheet 'PermitSiteCommSearchResults'):
  nevada/PermitSearchResults__13_.xlsx        Nevada County Records Center C008183-092226, released 2026-09-23
                                              (Luci Wilson, Deputy Ag Commissioner). 3,568 site rows, 2020-2026.
  el-dorado/_P010066-092126_-_El_Dorado.xlsx  El Dorado County Public Records Center P010066-092126, released
                                              2026-09-23 (Corrie Larsen, Assistant Ag Commissioner). 11,967 site rows.
  el-dorado/_P010066-092126_-_Alpine.xlsx     Same request; the Alpine County (code 02) permits El Dorado issues.
                                              115 site rows.

Reduced to one row per permit number (latest permit year), which is what the name enricher needs:
right(GROWER_ID, 7) == permit number. Permits issued by other counties are operators working local
ground and are kept, tagged with the delivering county. None of these exports carries an agent column.
The raw xlsx files are git-ignored (data/incoming/**/*.xlsx); this script is the reproducible record.
Same reduction as normalize_mendocino.py.
"""
import csv, io, os, sys, openpyxl, collections

HERE = os.path.dirname(os.path.abspath(__file__))
JOBS = [
    ("nevada/PermitSearchResults__13_.xlsx", "Nevada", "nevada-2020-2026.csv"),
    ("el-dorado/_P010066-092126_-_El_Dorado.xlsx", "El Dorado", "el-dorado-2020-2026.csv"),
    ("el-dorado/_P010066-092126_-_Alpine.xlsx", "Alpine", "alpine-2020-2026.csv"),
]

def clean(v):
    return " ".join(str(v or "").split()).strip()

def run(src, county, out):
    wb = openpyxl.load_workbook(os.path.join(HERE, src), read_only=True, data_only=True)
    ws = wb["PermitSiteCommSearchResults"]
    rows = ws.iter_rows(values_only=True)
    hdr = [clean(h) for h in next(rows)]
    ih = {h: i for i, h in enumerate(hdr)}
    for k in ("Permit Type", "Permit Number", "Permit Year", "Operator"):
        if k not in ih:
            sys.exit(src + ": missing column " + k)
    agent_col = ih.get("Agent Name")
    best = {}
    seen = 0
    for r in rows:
        if r is None or all(v is None for v in r):
            continue
        seen += 1
        pn = clean(r[ih["Permit Number"]])
        if not pn:
            continue
        try:
            py = int(str(r[ih["Permit Year"]])[:4])
        except ValueError:
            py = 0
        name = clean(r[ih["Operator"]]).upper()
        if not name:
            continue
        prev = best.get(pn)
        if prev is None or py > prev["py"]:
            best[pn] = dict(py=py, ptype=clean(r[ih["Permit Type"]]), name=name,
                            agent=clean(r[agent_col]).upper() if agent_col is not None else "")
    dropped = []
    for pn in list(best):
        n = best[pn]["name"]
        if "TEST" in n.split() or n.startswith("TEST ") or "PLACEHOLDER" in n or pn.endswith("99999"):
            dropped.append((pn, n)); del best[pn]
    outp = os.path.join(HERE, out)
    with io.open(outp, "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["operator_id", "name", "entity_type", "county", "agent"])
        for pn in sorted(best):
            b = best[pn]
            w.writerow([pn, b["name"], b["ptype"], county, b["agent"]])
    pref = collections.Counter(pn[:2] for pn in best)
    print(f"{county}: site rows read {seen}; permits written {len(best)}; by issuing county {dict(pref.most_common())}; dropped {dropped}; wrote {out}")

if __name__ == "__main__":
    for src, county, out in JOBS:
        run(src, county, out)
