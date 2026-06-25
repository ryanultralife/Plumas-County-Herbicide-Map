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

# CAL FIRE Timber Harvesting Plans (All) WGS84 hosted feature layer [ds816].
# Verified 2026-06; fields: COUNTY, THP_YEAR, THP_NUM, TIMBEROWNR/LANDOWNER,
# GIS_ACRES, SILVI_CAT/SILVI_1 (silviculture), PLAN_STAT, APPROVED.
ENDPOINT = ("https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/ArcGIS/rest/services/"
            "CAL_FIRE_Timber_Harvesting_Plans_All_WGS84/FeatureServer/0/query")
MIN_YEAR = 2020


def _page(where, offset):
    params = {"where": where, "outFields": "*", "returnGeometry": "true",
              "outSR": "4326", "f": "json", "resultOffset": offset, "resultRecordCount": 1000}
    r = requests.get(ENDPOINT + "?" + urllib.parse.urlencode(params), timeout=180)
    r.raise_for_status()
    return r.json()


def pull(region_key, region):
    if requests is None:
        sys.exit("pip install requests")
    # this layer stores COUNTY as a 3-letter code (Plumas->PLU, Butte->BUT, ...)
    codes = "','".join(c["name"][:3].upper() for c in region["counties"])
    where = f"COUNTY IN ('{codes}') AND THP_YEAR>={MIN_YEAR}"
    rows, pulled, offset = [], time.strftime("%Y-%m-%d"), 0
    while True:
        try:
            d = _page(where, offset)
        except Exception as e:
            print(f"  [thp] skipped ({e}); verify ENDPOINT")
            return rows
        feats = d.get("features", [])
        for ft in feats:
            a = {k.lower(): v for k, v in ft.get("attributes", {}).items()}
            g = ft.get("geometry", {})
            lon = lat = None
            if g.get("rings"):
                ring = g["rings"][0]
                lon = sum(p[0] for p in ring) / len(ring)
                lat = sum(p[1] for p in ring) / len(ring)
            silvi = " / ".join(x for x in (a.get("silvi_cat"), a.get("silvi_1")) if x)
            rows.append({
                "app_id": f"thp:{a.get('thp_num') or a.get('objectid')}", "source": "thp",
                "region": region_key, "date": a.get("approved"), "year": a.get("thp_year"),
                "lat": lat, "lon": lon, "county": a.get("county"), "land_type": "forestry",
                "owner": a.get("timberownr") or a.get("landowner"),
                "product": None, "active_ingredient": None, "amount": a.get("gis_acres"),
                "unit": "acres", "method": None,
                "activity": "Timber Harvest Plan" + (f" ({silvi})" if silvi else ""),
                "project": str(a.get("thp_num") or ""), "status": a.get("plan_stat") or "plan",
                "url": "https://caltreesplans.resources.ca.gov/caltrees/", "pulled": pulled})
        if not d.get("exceededTransferLimit") and len(feats) < 1000:
            break
        offset += len(feats)
        if not feats:
            break
    print(f"  [thp] {len(rows)} plans")
    return rows
