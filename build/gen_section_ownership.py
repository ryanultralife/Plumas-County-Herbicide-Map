"""Spatial ownership tag for each Northern-Sierra map cell: point-in-polygon
against USFS BasicOwnership polygons (USFS-owned vs private inholding vs outside
NF). Output data/section_ownership.json keyed by "lat,lon" (3-dec, matching cells)
-> {c: 'usfs'|'inholding'|'private', f: forestName}. Used to enrich popups and
flag operator/owner mismatches. Complements the name-based ownership chip."""
import requests, json, os, subprocess
ROOT = r"C:\Users\ryanv\Projects\Plumas-County-Herbicide-Map\.claude\worktrees\suspicious-sammet-763560"
OUT = os.path.join(ROOT, "data", "section_ownership.json")
U = "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_BasicOwnership_01/MapServer/0/query"
BBOX = "-121.9,39.3,-119.8,41.3"

# 1) fetch USFS ownership polygons (geojson) for the NS bbox
r = requests.get(U, params={"where": "1=1", "geometry": BBOX, "geometryType": "esriGeometryEnvelope",
    "inSR": "4326", "spatialRel": "esriSpatialRelIntersects",
    "outFields": "ownerclassification,forestname", "returnGeometry": "true", "maxAllowableOffset": "0.002", "outSR": "4326", "f": "geojson"}, timeout=90)
gj = r.json()
polys = []  # (ownerclass, forest, list-of-rings) ; ring = list of (lon,lat)
for ft in gj.get("features", []):
    pr = ft.get("properties", {}); g = ft.get("geometry") or {}
    oc = (pr.get("ownerclassification") or "").upper(); fn = pr.get("forestname") or ""
    geoms = g.get("coordinates", [])
    if g.get("type") == "Polygon": geoms = [geoms]
    for poly in geoms:
        for ring in poly:  # first ring = outer; treat all as boundaries
            polys.append((oc, fn, [(c[0], c[1]) for c in ring]))
print(f"USFS ownership rings: {len(polys)}  classes: {set(p[0] for p in polys)}")

def pip(x, y, ring):
    inside = False; n = len(ring); j = n - 1
    for i in range(n):
        xi, yi = ring[i]; xj, yj = ring[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi):
            inside = not inside
        j = i
    return inside

def classify(lon, lat):
    hitFS = hitNon = None
    for oc, fn, ring in polys:
        if pip(lon, lat, ring):
            if "FOREST SERVICE" in oc or oc == "FS" or oc == "USDA FOREST SERVICE":
                hitFS = fn
            elif "NON" in oc:
                hitNon = fn
    if hitFS: return ("usfs", hitFS)
    if hitNon: return ("inholding", hitNon)
    return ("private", "")

# 2) NS map cells from the DB
dburl = os.environ["DBURL"]
q = "copy (select round(lat::numeric,3), round(lon::numeric,3) from public.map_agg where county in ('Butte','Tehama','Lassen','Plumas','Sierra')) to stdout with csv"
out = subprocess.run(["psql", dburl, "-c", q], capture_output=True, text=True).stdout.strip().splitlines()
cells = [tuple(l.split(",")) for l in out if l]
print(f"NS cells: {len(cells)}")

res = {}
cnt = {"usfs": 0, "inholding": 0, "private": 0}
for lat, lon in cells:
    c, f = classify(float(lon), float(lat))
    cnt[c] += 1
    if c != "private":
        res[f"{float(lat):.3f},{float(lon):.3f}"] = {"c": c, "f": f}
print("classification:", cnt)
json.dump({"note": "Per-section land ownership from USFS BasicOwnership (point-in-polygon on the ~1 sq-mi section centroid). Absent key = private/other (outside National Forest ownership).",
           "cells": res}, open(OUT, "w"))
print("wrote", OUT, "keyed cells:", len(res))
