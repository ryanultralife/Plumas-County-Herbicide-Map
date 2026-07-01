#!/usr/bin/env python3
"""Merge per-county CA state legislators (from the reps workflow) into data/contacts.json."""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[1]
d = json.load(open(src, encoding="utf-8"))
r = d.get("result", d)

def clean(members):
    out = []
    for m in (members or []):
        nm = (m.get("name") or "").strip()
        if not nm or nm.lower() == "vacant":
            continue
        out.append({"name": nm, "district": m.get("district"),
                    "party": (m.get("party") or "")[:1].upper() or None, "url": m.get("url")})
    return out

byc = {}
for batch in (r.get("reps") or []):
    for c in (batch.get("reps") or []):
        nm = (c.get("county") or "").strip()
        if not nm:
            continue
        byc[nm] = {"senate": clean(c.get("senate")), "assembly": clean(c.get("assembly"))}

path = os.path.join(ROOT, "data", "contacts.json")
data = json.load(open(path, encoding="utf-8"))
n = 0
for county, reps in byc.items():
    if county in data["counties"]:
        data["counties"][county]["reps"] = reps
        n += 1
    else:
        data["counties"].setdefault(county, {})["reps"] = reps
json.dump(data, open(path, "w", encoding="utf-8"), indent=1)
tot_s = sum(len(v.get("reps", {}).get("senate", [])) for v in data["counties"].values())
tot_a = sum(len(v.get("reps", {}).get("assembly", [])) for v in data["counties"].values())
print(f"Merged reps into {n} counties. senate entries={tot_s}, assembly entries={tot_a}")
