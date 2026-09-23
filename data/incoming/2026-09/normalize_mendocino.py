#!/usr/bin/env python3
"""Mendocino County operator roster -> data/incoming/2026-09/mendocino-2020-2026.csv

Source: 'Mendocino Permits 2020-2026.xlsx', released 2026-09-22 on the county's
NextRequest portal (request #26-2419, the follow-up asking for Mendocino-issued,
county-code-23 permits after the first response turned out to be Sacramento-issued
ones). A CalAgPermits 'Permits, Sites and Commodities' export: 11,040 site rows on
sheet 'PermitSiteCommSearchResults' (sheet 'Search Criteria' is the query stub).

Reduced to one row per permit number (latest permit year), which is what the name
enricher needs: right(GROWER_ID, 7) == permit number. Permits issued by other
counties (49 Sonoma, 54 Tulare, 58 Yuba) are operators working Mendocino ground and
are kept. The raw xlsx is git-ignored (data/incoming/**/*.xlsx); this script is
the reproducible record.
"""
import csv, io, os, sys, openpyxl, collections

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "mendocino", "Mendocino Permits 2020-2026.xlsx")
OUT = os.path.join(HERE, "mendocino-2020-2026.csv")

def clean(v):
    return " ".join(str(v or "").split()).strip()

def main():
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    ws = wb["PermitSiteCommSearchResults"]
    rows = ws.iter_rows(values_only=True)
    hdr = [clean(h) for h in next(rows)]
    ih = {h: i for i, h in enumerate(hdr)}
    need = ["Permit Type", "Permit Number", "Permit Year", "Operator", "Agent Name", "City", "Zip", "Ag/Non-Ag"]
    missing = [k for k in need if k not in ih]
    if missing:
        sys.exit("missing columns: " + ", ".join(missing))
    best = {}
    seen_rows = 0
    for r in rows:
        if r is None or all(v is None for v in r):
            continue
        seen_rows += 1
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
                            agent=clean(r[ih["Agent Name"]]).upper(),
                            city=clean(r[ih["City"]]), zip=clean(r[ih["Zip"]]),
                            ag=clean(r[ih["Ag/Non-Ag"]]))
    # drop obvious placeholders / test permits
    dropped = []
    for pn in list(best):
        n = best[pn]["name"]
        if "TEST" in n.split() or n.startswith("TEST ") or "PLACEHOLDER" in n or pn.endswith("99999"):
            dropped.append((pn, n)); del best[pn]
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["operator_id", "name", "entity_type", "county", "agent"])
        for pn in sorted(best):
            b = best[pn]
            w.writerow([pn, b["name"], b["ptype"], "Mendocino", b["agent"]])
    pref = collections.Counter(pn[:2] for pn in best)
    n_ag = sum(1 for b in best.values() if b["agent"])
    print("site rows read:", seen_rows)
    print("permits written:", len(best), "| with agent:", n_ag, "| by issuing county:", dict(pref.most_common()))
    print("dropped as test/placeholder:", dropped)
    print("wrote", OUT)

if __name__ == "__main__":
    main()
