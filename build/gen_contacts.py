#!/usr/bin/env python3
"""
Build data/contacts.json — per-county "verify or raise a concern" contacts, shown
in each map popup. Sources: the dig-all-and-contacts workflow result (CDFA county
Ag Commissioner directory + 9 Regional Water Boards + CDPR). State reps + air
districts use the official address/locator lookups (district != county, so a
lookup is the honest link).

Usage:  python build/gen_contacts.py <workflow_output.json>
"""
import os, sys, json, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[1] if len(sys.argv) > 1 else None
if not src or not os.path.exists(src):
    sys.exit("Pass the workflow output json path.")
d = json.load(open(src, encoding="utf-8"))
r = d.get("result", d)

def norm(s): return re.sub(r"\(.*?\)", "", str(s or "")).strip().lower()

# county -> Ag Commissioner
counties = {}
for c in (r.get("agcomm") or {}).get("contacts", []):
    nm = (c.get("county") or "").strip()
    if not nm: continue
    counties[nm] = {"ag": {"officer": c.get("officer"), "email": c.get("email"), "phone": c.get("phone")}}

# attach Regional Water Board per county
CALEPA = "https://calepa.ca.gov/enforcement/complaints/"
regions = (r.get("water") or {}).get("regions", [])
cnames = {norm(k): k for k in counties}
for reg in regions:
    rn = reg.get("region"); url = reg.get("complaint_url") or CALEPA
    for rc in reg.get("counties", []):
        key = cnames.get(norm(rc))
        if key and "water" not in counties[key]:
            counties[key]["water"] = {"region": rn, "url": url}
for k in counties:
    counties[k].setdefault("water", {"region": "Regional Water Quality Control Board", "url": CALEPA})

cd = r.get("cdpr") or {}
out = {
    "dpr": {
        "phone": cd.get("phone") or "1-877-378-5463",
        "url": cd.get("url") or "https://www.cdpr.ca.gov/docs/dept/comguide/contact_county.htm",
        "note": "Call 1-87-PestLine (1-877-378-5463) — routes to your County Agricultural Commissioner.",
    },
    "reps": {"url": "https://findyourrep.legislature.ca.gov/",
             "note": "Find your CA state Senator & Assembly Member by address."},
    "air": {"url": "https://ww2.arb.ca.gov/california-air-districts",
            "note": "Local air district — pesticide drift, odor, air quality."},
    "counties": counties,
}
path = os.path.join(ROOT, "data", "contacts.json")
json.dump(out, open(path, "w", encoding="utf-8"), indent=1)
print(f"Wrote {path}: {len(counties)} counties, "
      f"{sum(1 for c in counties.values() if c['ag'].get('email'))} with AgComm email")
