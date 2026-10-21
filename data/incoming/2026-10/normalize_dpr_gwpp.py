#!/usr/bin/env python3
"""Normalize DPR Groundwater Protection Program 'Well Kit' analyte list (rcvd 2026-08-07).
The file is an ANALYTE LIST only (no wells, samples, results, dates or coordinates).
Out: dpr-gwpp/dpr_gwpp_wellkit_analytes.csv
"""
import os, re, sys, csv
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "build"))
from gen_edt_plumas import classify
SRC = os.environ.get("SRC", "/workspace/spraymap-incoming/dpr-gwpp/DPR GW Screens_well kits - consolidated.xlsx")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dpr-gwpp")
FORESTRY = ["glyphosate","AMPA","triclopyr","imazapyr","aminopyralid","2,4-D","hexazinone","clopyralid","sulfometuron-methyl","indaziflam","picloram"]
def main():
    os.makedirs(OUT, exist_ok=True)
    df = pd.read_excel(SRC, header=None)
    rows = []
    for raw in df.iloc[1:, 0].dropna().astype(str):
        r = raw.strip()
        name = re.sub(r"\*\*|\((?i:marginal)\)", "", r).strip()
        rows.append({"compound_as_listed": r, "compound": name,
                     "method_in_development": "**" in r,
                     "marginal": "marginal" in r.lower(),
                     "herbicide_key": classify(name) or ""})
    with open(os.path.join(OUT, "dpr_gwpp_wellkit_analytes.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    keys = {r["herbicide_key"] for r in rows}
    print(f"{len(rows)} compounds; dev-method {sum(r['method_in_development'] for r in rows)}; marginal {sum(r['marginal'] for r in rows)}")
    print("forestry herbicides covered:", [k for k in FORESTRY if k in keys])
    print("NOT covered:", [k for k in FORESTRY if k not in keys])
    print("all TARGET keys matched:", sorted(k for k in keys if k))
if __name__ == "__main__": main()
