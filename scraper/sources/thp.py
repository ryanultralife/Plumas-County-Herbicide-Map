"""
Source module: CAL FIRE Timber Harvest Plans (THP/NTMP) -- private timberland.
THPs frequently specify site-prep / release herbicide use. Queries the CAL FIRE
Timber Harvest ArcGIS service by county.

NOTE: confirm ENDPOINT against the current CAL FIRE Timber Harvest Viewer (ds816)
before a production run; field names below are mapped defensively.
Viewer: https://www.fire.ca.gov/what-we-do/natural-resource-management/forest-practice
"""
import sys, os, time, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lib
try:
    import requests
except ImportError:
    requests = None

# CAL FIRE FRAP Timber Harvest Plans feature service (verify/replace if moved):
ENDPOINT = ("https://egis.fire.ca.gov/arcgis/rest/services/FRAP/"
            "Timber_Harvest_Plans/MapServer/0/query")


def pull(region_key, region):
    if requests is None:
        sys.exit("pip install requests")
    names = "','".join(c["name"].upper() for c in region["counties"])
    rows, pulled = [], time.strftime("%Y-%m-%d")
    params = {"where": f"UPPER(COUNTY) IN ('{names}')", "outFields": "*",
              "returnGeometry": "true", "outSR": "4326", "f": "json"}
    try:
        r = requests.get(ENDPOINT + "?" + urllib.parse.urlencode(params), timeout=120)
        r.raise_for_status()
        d = r.json()
    except Exception as e:
        print(f"  [thp] skipped ({e}); verify ENDPOINT")
        return rows
    for ft in d.get("features", []):
        a = {k.lower(): v for k, v in ft.get("attributes", {}).items()}
        g = ft.get("geometry", {})
        lon = lat = None
        if g.get("rings"):
            ring = g["rings"][0]
            lon = sum(p[0] for p in ring) / len(ring)
            lat = sum(p[1] for p in ring) / len(ring)
        rows.append({
            "app_id": f"thp:{a.get('thp_no') or a.get('objectid')}", "source": "thp",
            "region": region_key, "date": a.get("approval_date") or a.get("submitted"),
            "year": a.get("year"), "lat": lat, "lon": lon, "county": a.get("county"),
            "land_type": "forestry", "owner": a.get("timber_owner") or a.get("owner"),
            "product": None, "active_ingredient": None, "amount": a.get("acres"),
            "unit": "acres", "method": None, "activity": "Timber Harvest Plan",
            "project": a.get("thp_no"), "status": a.get("status") or "plan",
            "url": "https://caltreesplans.resources.ca.gov/caltrees/", "pulled": pulled})
    print(f"  [thp] {len(rows)} plans")
    return rows
