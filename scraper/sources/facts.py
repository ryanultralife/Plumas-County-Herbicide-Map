"""
Source module: USFS FACTS (federal land) via the EDW ArcGIS REST API.
Pulls every chemical-method treatment in the region's counties, Forest Service Region 05.
County-based so a region is just a list of counties (no forest IDs needed).
"""
import sys, os, time, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lib
try:
    import requests
except ImportError:
    requests = None

BASE = ("https://apps.fs.usda.gov/arcx/rest/services/EDW/"
        "EDW_ActivityFactsCommonAttributes_01/MapServer/0/query")
OUTFIELDS = ("objectid,latitude,longitude,activity,method,fiscal_year_completed,"
             "fiscal_year_planned,date_completed,nbr_units_accomplished,nbr_units_planned,"
             "nepa_project_name,admin_district,county_name")


def _page(where, offset):
    params = {"where": where, "outFields": OUTFIELDS, "returnGeometry": "false",
              "f": "json", "resultOffset": offset, "resultRecordCount": 2000}
    r = requests.get(BASE + "?" + urllib.parse.urlencode(params), timeout=180)
    r.raise_for_status()
    return r.json()


def pull(region_key, region):
    if requests is None:
        sys.exit("pip install requests")
    counties = "','".join(c["name"] for c in region["counties"])
    where = f"admin_region='05' AND method='Chemical' AND county_name IN ('{counties}')"
    rows, pulled, offset = [], time.strftime("%Y-%m-%d"), 0
    print(f"  [facts] region 05, counties: {counties}")
    while True:
        d = _page(where, offset)
        feats = d.get("features", [])
        for ft in feats:
            a = ft["attributes"]
            yr = a.get("fiscal_year_completed") or a.get("fiscal_year_planned")
            status = "completed" if (a.get("fiscal_year_completed") or 0) else "planned"
            land = lib.classify(activity=a.get("activity"), project=a.get("nepa_project_name")) or "federal"
            rows.append({
                "app_id": f"facts:{a['objectid']}", "source": "facts", "region": region_key,
                "date": None, "year": yr, "lat": a.get("latitude"), "lon": a.get("longitude"),
                "county": a.get("county_name"), "land_type": land, "owner": "USDA Forest Service",
                "product": None, "active_ingredient": None,
                "amount": a.get("nbr_units_accomplished") or a.get("nbr_units_planned"),
                "unit": "acres", "method": a.get("method"), "activity": a.get("activity"),
                "project": a.get("nepa_project_name"), "status": status,
                "url": "https://www.fs.usda.gov/", "pulled": pulled})
        if not d.get("exceededTransferLimit") and len(feats) < 2000:
            break
        offset += len(feats)
        if not feats:
            break
    print(f"  [facts] {len(rows)} federal treatments")
    return rows
