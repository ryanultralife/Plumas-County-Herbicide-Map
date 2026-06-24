"""
Source module: USFS FACTS (federal land) via the EDW ArcGIS REST API.
Pulls every chemical-method treatment for each national forest in a region.
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
PROJECT_URL = "https://www.fs.usda.gov/project/plumas/"  # generic FACTS reference


def _page(unit, offset):
    params = {"where": f"fs_unit_id='{unit}' AND method='Chemical'",
              "outFields": OUTFIELDS, "returnGeometry": "false", "f": "json",
              "resultOffset": offset, "resultRecordCount": 2000}
    r = requests.get(BASE + "?" + urllib.parse.urlencode(params), timeout=120)
    r.raise_for_status()
    return r.json()


def pull(region_key, region):
    """Return normalized rows for all forests in the region."""
    if requests is None:
        sys.exit("pip install requests")
    rows, pulled = [], time.strftime("%Y-%m-%d")
    for f in region["forests"]:
        unit = f["fs_unit_id"]
        offset = 0
        print(f"  [facts] {f['name']} ({unit}) ...", end="", flush=True)
        while True:
            d = _page(unit, offset)
            feats = d.get("features", [])
            for ft in feats:
                a = ft["attributes"]
                yr = a.get("fiscal_year_completed") or a.get("fiscal_year_planned")
                status = "completed" if (a.get("fiscal_year_completed") or 0) else "planned"
                land = lib.classify(activity=a.get("activity"), project=a.get("nepa_project_name")) or "federal"
                rows.append({
                    "app_id": f"facts:{a['objectid']}", "source": "facts", "region": region_key,
                    "date": None, "year": yr, "lat": a.get("latitude"), "lon": a.get("longitude"),
                    "county": a.get("county_name"), "land_type": land, "owner": f["name"],
                    "product": None, "active_ingredient": None,
                    "amount": a.get("nbr_units_accomplished") or a.get("nbr_units_planned"),
                    "unit": "acres", "method": a.get("method"), "activity": a.get("activity"),
                    "project": a.get("nepa_project_name"), "status": status,
                    "url": PROJECT_URL, "pulled": pulled})
            if not d.get("exceededTransferLimit") and len(feats) < 2000:
                break
            offset += len(feats)
            if not feats:
                break
        print(f" {sum(1 for r in rows if r['owner']==f['name'])} records")
    return rows
