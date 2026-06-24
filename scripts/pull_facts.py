#!/usr/bin/env python3
"""
Pull USFS FACTS herbicide/chemical treatment records for the Plumas National Forest
straight from the Forest Service EDW ArcGIS REST API, and write GeoJSON + CSV to data/.

Why this exists: the in-app fetch tool caps URL length and truncates large responses,
so it can only grab a partial set. Run this on any networked machine (no caps) to get
the COMPLETE + richer dataset (acres, NEPA project, ranger district, planned vs done).

Usage:
    python scripts/pull_facts.py
    (requires:  pip install requests)

Re-run anytime new data lands ("as it comes in"); then publish-data.ps1 commits it.
"""
import json, csv, urllib.parse, os, sys
try:
    import requests
except ImportError:
    sys.exit("Install requests first:  pip install requests")

BASE = ("https://apps.fs.usda.gov/arcx/rest/services/EDW/"
        "EDW_ActivityFactsCommonAttributes_01/MapServer/0/query")
PLUMAS = "0511"          # FACTS fs_unit_id for Plumas National Forest
MIN_YEAR = 2020
OUTDIR = os.path.join(os.path.dirname(__file__), "..", "data")

FIELDS = ["latitude", "longitude", "activity", "activity_code", "method",
          "treatment_name", "nbr_units_accomplished", "nbr_units_planned",
          "date_completed", "fiscal_year_completed", "fiscal_year_planned",
          "nepa_project_name", "nepa_doc_type", "admin_district",
          "county_name", "ownership", "activity_remarks"]

def fetch(where):
    """Page through all matching records (2000/page)."""
    out, offset = [], 0
    while True:
        params = {"where": where, "outFields": ",".join(FIELDS),
                  "returnGeometry": "false", "f": "json",
                  "resultOffset": offset, "resultRecordCount": 2000}
        r = requests.get(BASE + "?" + urllib.parse.urlencode(params), timeout=120)
        r.raise_for_status()
        d = r.json()
        if "error" in d:
            sys.exit("API error: " + json.dumps(d["error"]))
        feats = d.get("features", [])
        out += [f["attributes"] for f in feats]
        if not d.get("exceededTransferLimit") and len(feats) < 2000:
            break
        offset += len(feats)
        if not feats:
            break
    return out

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    where = ("fs_unit_id='%s' AND method='Chemical' AND "
             "(fiscal_year_completed>=%d OR fiscal_year_planned>=%d)"
             % (PLUMAS, MIN_YEAR, MIN_YEAR))
    print("Querying EDW FACTS for Plumas NF chemical treatments ...")
    recs = fetch(where)
    print("  retrieved %d records" % len(recs))

    # split completed vs planned, drop rows without coordinates
    def status(r):
        return "completed" if (r.get("fiscal_year_completed") or 0) >= MIN_YEAR else "planned"
    recs = [r for r in recs if r.get("latitude") and r.get("longitude")]

    # GeoJSON
    fc = {"type": "FeatureCollection",
          "name": "Plumas NF herbicide/chemical treatments (USFS FACTS, FY%d+)" % MIN_YEAR,
          "_provenance": {"source": "USDA Forest Service EDW Activity FACTS Common Attributes",
                          "url": BASE, "where": where},
          "features": []}
    for r in recs:
        fc["features"].append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["longitude"], r["latitude"]]},
            "properties": {
                "activity": r.get("activity"),
                "treatment": r.get("treatment_name"),
                "year": r.get("fiscal_year_completed") or r.get("fiscal_year_planned"),
                "status": status(r),
                "acres": r.get("nbr_units_accomplished") or r.get("nbr_units_planned"),
                "method": r.get("method"),
                "nepa_project": r.get("nepa_project_name"),
                "district": r.get("admin_district"),
                "county": r.get("county_name"),
                "ownership": r.get("ownership"),
                "land": "Federal (Plumas NF)",
                "remarks": r.get("activity_remarks"),
                "source": "USFS FACTS"}})
    json.dump(fc, open(os.path.join(OUTDIR, "plumas_nf_herbicide_facts.geojson"), "w"), indent=1)

    # CSV
    cols = ["latitude", "longitude", "activity", "treatment_name", "method",
            "fiscal_year_completed", "fiscal_year_planned", "date_completed",
            "nbr_units_accomplished", "nbr_units_planned", "nepa_project_name",
            "admin_district", "county_name", "ownership", "activity_remarks"]
    with open(os.path.join(OUTDIR, "plumas_nf_herbicide_facts.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(cols)
        for r in recs:
            w.writerow([r.get(c) for c in cols])

    done = sum(1 for r in recs if status(r) == "completed")
    print("  wrote %d features  (%d completed, %d planned)" % (len(recs), done, len(recs) - done))
    print("Output: data/plumas_nf_herbicide_facts.geojson  +  .csv")

if __name__ == "__main__":
    main()
