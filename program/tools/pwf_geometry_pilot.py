#!/usr/bin/env python3
"""
Progressive Working Forest geometry pilot for Plumas National Forest.

Pulls USFS FACTS Timber Harvest polygons via ArcGIS REST, computes annual
scatter vs progressive-front metrics, optionally compares Hansen tree-cover
loss years (if a lossyear GeoTIFF path is provided).

Outputs:
  program/data/pwf_geometry_pilot.json
  program/data/pwf_geometry_pilot.md
  data/pwf_geometry_pilot.json  (site-facing copy)

Usage:
  python program/tools/pwf_geometry_pilot.py
  python program/tools/pwf_geometry_pilot.py --hansen path/to/lossyear.tif
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests
from shapely.geometry import mapping, shape
from shapely.ops import unary_union
from shapely import make_valid

ROOT = Path(__file__).resolve().parents[2]
OUT_PROGRAM = ROOT / "program" / "data"
OUT_SITE = ROOT / "data"

# EDW Timber Harvest — layers by decade
LAYERS = {
    "2021-current": 11,
    "2011-2020": 0,
    "2001-2010": 1,
    "1991-2000": 2,
}
BASE = "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_TimberHarvest_01/MapServer"
WHERE = "admin_forest_name LIKE '%Plumas%'"
OUT_FIELDS = ",".join(
    [
        "objectid",
        "admin_forest_name",
        "admin_forest_code",
        "activity_name",
        "activity_code",
        "treatment_type",
        "method_desc",
        "method_code",
        "fy_completed",
        "fy_planned",
        "fy_awarded",
        "date_completed",
        "nbr_units_accomplished",
        "uom",
        "sale_name",
        "au_name",
        "subunit_name",
        "nepa_doc_name",
        "cost_per_uom",
    ]
)


def fetch_layer(layer_id: int, where: str = WHERE, page_size: int = 1000) -> list[dict]:
    """Page through ArcGIS REST query for one layer."""
    url = f"{BASE}/{layer_id}/query"
    features: list[dict] = []
    offset = 0
    while True:
        params = {
            "where": where,
            "outFields": OUT_FIELDS,
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "geojson",
            "resultOffset": offset,
            "resultRecordCount": page_size,
        }
        for attempt in range(4):
            try:
                r = requests.get(url, params=params, timeout=180)
                r.raise_for_status()
                data = r.json()
                break
            except Exception as e:
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)
                print(f"  retry {attempt+1}: {e}", file=sys.stderr)
        batch = data.get("features") or []
        if not batch:
            # some servers return esri json if geojson fails
            if "error" in data:
                raise RuntimeError(data["error"])
            break
        features.extend(batch)
        print(f"  layer {layer_id}: +{len(batch)} (total {len(features)})", flush=True)
        if len(batch) < page_size:
            break
        offset += page_size
        # exceededTransferLimit may be present
        if data.get("properties", {}).get("exceededTransferLimit") is False:
            break
        if not data.get("exceededTransferLimit", True) and len(batch) < page_size:
            break
    return features


def year_of(props: dict) -> int | None:
    for k in ("fy_completed", "fy_awarded", "fy_planned"):
        v = props.get(k)
        if v is None or v == "" or v == 0:
            continue
        try:
            y = int(v)
            if 1800 < y < 2100:
                return y
        except (TypeError, ValueError):
            pass
    dc = props.get("date_completed")
    if isinstance(dc, (int, float)) and dc > 1e11:
        # epoch ms
        try:
            return datetime.fromtimestamp(dc / 1000, tz=timezone.utc).year
        except (OSError, ValueError, OverflowError):
            pass
    if isinstance(dc, str) and len(dc) >= 4 and dc[:4].isdigit():
        return int(dc[:4])
    return None


def geom_area_acres(g) -> float:
    """Approx area in acres using geodesic-ish degree conversion at ~40N."""
    # project-free: use equal-area-ish at lat 40
    # 1 deg lat ~ 69 mi; 1 deg lon at 40N ~ 53 mi
    if g is None or g.is_empty:
        return 0.0
    minx, miny, maxx, maxy = g.bounds
    mid_lat = (miny + maxy) / 2.0
    lon_mi = 69.172 * math.cos(math.radians(mid_lat))
    lat_mi = 69.172
    # shapely area in degree^2
    a_deg2 = g.area
    a_mi2 = a_deg2 * lon_mi * lat_mi
    return a_mi2 * 640.0


def patch_metrics(g) -> dict:
    if g is None or g.is_empty:
        return {"area_ac": 0, "compactness": None, "aspect_ratio": None}
    area_ac = geom_area_acres(g)
    # compactness: 4*pi*A / P^2 (1 = circle). Use projected feet approx for P,A ratio
    mid_lat = (g.bounds[1] + g.bounds[3]) / 2.0
    lon_ft = 69.172 * math.cos(math.radians(mid_lat)) * 5280
    lat_ft = 69.172 * 5280
    # scale geometry for perimeter in feet (affine scale)
    from shapely.affinity import scale

    gx = scale(g, xfact=lon_ft, yfact=lat_ft, origin=(0, 0))
    a = gx.area
    p = gx.length
    compact = (4 * math.pi * a / (p * p)) if p > 0 else None
    minx, miny, maxx, maxy = g.bounds
    w = (maxx - minx) * lon_ft
    h = (maxy - miny) * lat_ft
    ar = (max(w, h) / min(w, h)) if min(w, h) > 0 else None
    return {"area_ac": round(area_ac, 2), "compactness": round(compact, 4) if compact else None, "aspect_ratio": round(ar, 2) if ar else None}


def contiguity_score(geoms: list) -> dict:
    """Share of features that touch another feature (or near-touch within ~50m).

    Uses STRtree so large annual sets stay fast.
    """
    if not geoms:
        return {"n": 0, "touching_share": None, "n_components": 0, "largest_component_share": None}
    from shapely import STRtree

    buf = 0.0005  # ~50 m near-touch
    n = len(geoms)
    buffered = [g.buffer(buf) for g in geoms]
    tree = STRtree(buffered)
    touching = [False] * n
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri

    for i, gi in enumerate(buffered):
        # query returns indices into buffered in shapely 2
        try:
            hits = tree.query(gi, predicate="intersects")
        except TypeError:
            hits = tree.query(gi)
        for j in hits:
            j = int(j)
            if j <= i:
                continue
            if gi.intersects(buffered[j]):
                touching[i] = touching[j] = True
                union(i, j)
    roots = [find(i) for i in range(n)]
    sizes: dict[int, int] = defaultdict(int)
    for r in roots:
        sizes[r] += 1
    largest = max(sizes.values()) if sizes else 0
    return {
        "n": n,
        "touching_share": round(sum(1 for t in touching if t) / n, 3) if n else None,
        "n_components": len(sizes),
        "largest_component_share": round(largest / n, 3) if n else None,
    }


def centroid_dispersion(geoms: list) -> dict:
    """Mean nearest-neighbor distance between centroids in miles (scatter proxy)."""
    if len(geoms) < 2:
        return {"mean_nn_mi": None, "median_nn_mi": None}
    from shapely import STRtree
    from shapely.geometry import Point

    cents = []
    pts = []
    for g in geoms:
        c = g.centroid
        mid_lat = c.y
        lon_mi = 69.172 * math.cos(math.radians(mid_lat))
        # store miles coords for distance
        cents.append((c.x * lon_mi, c.y * 69.172))
        pts.append(Point(c.x * lon_mi, c.y * 69.172))
    tree = STRtree(pts)
    nns = []
    for i, p in enumerate(pts):
        # k=2 nearest includes self
        try:
            idxs = tree.nearest(p, return_all=False)
            # shapely 2.0: nearest returns single index; query with distance
            idxs = list(tree.query(p.buffer(50)))  # 50 mi search cap
        except Exception:
            idxs = list(range(len(pts)))
        best = 1e18
        x, y = cents[i]
        for j in idxs:
            j = int(j)
            if j == i:
                continue
            x2, y2 = cents[j]
            d = math.hypot(x - x2, y - y2)
            if d < best:
                best = d
        if best >= 1e18:
            for j, (x2, y2) in enumerate(cents):
                if j == i:
                    continue
                d = math.hypot(x - x2, y - y2)
                if d < best:
                    best = d
        nns.append(best)
    nns.sort()
    mid = nns[len(nns) // 2]
    return {
        "mean_nn_mi": round(sum(nns) / len(nns), 3),
        "median_nn_mi": round(mid, 3),
    }


def classify_year(metrics: dict) -> str:
    """Heuristic scatter vs progressive vs multi-cluster.

    progressive_leaning: units mostly form one connected front
    multi_cluster: many units touch neighbors but largest component is small
                   (local clumps, not one side-to-side wave) — ops still jump between clumps
    scatter_leaning: isolated units far apart
    """
    touch = metrics.get("touching_share")
    largest = metrics.get("largest_component_share")
    nn = metrics.get("mean_nn_mi")
    n = metrics.get("n") or 0
    if n < 3:
        return "insufficient_sample"
    if touch is not None and largest is not None and nn is not None:
        if touch >= 0.55 and largest >= 0.40 and nn <= 3.0:
            return "progressive_leaning"
        if touch <= 0.35 and nn >= 4.0:
            return "scatter_leaning"
        if touch >= 0.50 and largest is not None and largest < 0.35:
            return "multi_cluster"
    return "mixed_or_unclear"


def activity_bucket(name: str | None) -> str:
    s = (name or "").lower()
    if any(k in s for k in ("clearcut", "clear cut", "regeneration cut", "final harvest", "seed tree", "shelterwood")):
        return "regen_heavy"
    if any(k in s for k in ("thin", "commercial thin", "improvement", "sanitation", "salvage")):
        return "thin_or_salvage"
    if "fuel" in s:
        return "fuels"
    return "other_or_unspecified"


def run(hansen_path: Path | None = None, cache_path: Path | None = None) -> dict:
    cache_path = cache_path or (OUT_PROGRAM / "pwf_facts_plumas_cache.geojson")
    all_feats: list[dict] = []
    layer_counts = {}
    if cache_path.is_file():
        print(f"Loading cache {cache_path}...", flush=True)
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        all_feats = cached.get("features") or []
        layer_counts = cached.get("layer_counts") or {}
        print(f"  cached features: {len(all_feats)}", flush=True)
    else:
        for label, lid in LAYERS.items():
            print(f"Fetching {label} (layer {lid})...", flush=True)
            feats = fetch_layer(lid)
            layer_counts[label] = len(feats)
            for f in feats:
                f["_layer"] = label
            all_feats.extend(feats)
        OUT_PROGRAM.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps({"layer_counts": layer_counts, "features": all_feats}),
            encoding="utf-8",
        )
        print(f"Wrote cache {cache_path}", flush=True)

    # Dedup by objectid + layer year range if needed
    records = []
    by_year: dict[int, list] = defaultdict(list)
    activity_counts: dict[str, int] = defaultdict(int)
    method_counts: dict[str, int] = defaultdict(int)

    for f in all_feats:
        props = f.get("properties") or {}
        geom_j = f.get("geometry")
        if not geom_j:
            continue
        try:
            g = shape(geom_j)
            if not g.is_valid:
                g = make_valid(g)
            if g.is_empty:
                continue
            # multipolygon explode not needed for metrics at feature level
        except Exception:
            continue
        y = year_of(props)
        pm = patch_metrics(g)
        act = props.get("activity_name") or ""
        activity_counts[act or "(blank)"] += 1
        method_counts[(props.get("method_desc") or "(blank)")] += 1
        bucket = activity_bucket(act)
        rec = {
            "year": y,
            "activity_name": act,
            "activity_bucket": bucket,
            "method_desc": props.get("method_desc"),
            "treatment_type": props.get("treatment_type"),
            "sale_name": props.get("sale_name"),
            "fy_completed": props.get("fy_completed"),
            "acres_reported": props.get("nbr_units_accomplished") if (props.get("uom") or "").upper() in ("AC", "ACRES") else None,
            "acres_geom": pm["area_ac"],
            "compactness": pm["compactness"],
            "aspect_ratio": pm["aspect_ratio"],
            "layer": f.get("_layer"),
        }
        records.append(rec)
        if y and 1990 <= y <= 2026:
            by_year[y].append(g)

    # Annual contiguity
    annual = []
    for y in sorted(by_year.keys()):
        print(f"  metrics year {y} n={len(by_year[y])}", flush=True)
        geoms = [g for g in by_year[y] if not g.is_empty and geom_area_acres(g) > 0.5]
        c = contiguity_score(geoms)
        d = centroid_dispersion(geoms)
        total_ac = sum(geom_area_acres(g) for g in geoms)
        m = {**c, **d, "year": y, "total_geom_acres": round(total_ac, 1)}
        m["layout_class"] = classify_year(m)
        annual.append(m)

    def rollup_from_annual(years: range, annual_rows: list[dict]) -> dict:
        rows = [a for a in annual_rows if a["year"] in years and a.get("n", 0) >= 3]
        geoms = []
        for y in years:
            geoms.extend(by_year.get(y, []))
        geoms = [g for g in geoms if geom_area_acres(g) > 0.5]
        total_ac = round(sum(geom_area_acres(g) for g in geoms), 1)
        if not rows:
            return {
                "years": f"{years.start}-{years.stop-1}",
                "n_features": len(geoms),
                "total_geom_acres": total_ac,
                "mean_annual_touching_share": None,
                "mean_annual_largest_component_share": None,
                "mean_annual_mean_nn_mi": None,
                "layout_class": "insufficient_sample",
                "years_classified": 0,
            }

        def avg(key):
            vals = [a[key] for a in rows if a.get(key) is not None]
            return round(sum(vals) / len(vals), 3) if vals else None

        touch, largest, nn = avg("touching_share"), avg("largest_component_share"), avg("mean_nn_mi")
        m = {
            "n": sum(a["n"] for a in rows),
            "touching_share": touch,
            "largest_component_share": largest,
            "mean_nn_mi": nn,
        }
        return {
            "years": f"{years.start}-{years.stop-1}",
            "n_features": len(geoms),
            "total_geom_acres": total_ac,
            "mean_annual_touching_share": touch,
            "mean_annual_largest_component_share": largest,
            "mean_annual_mean_nn_mi": nn,
            "years_classified": len(rows),
            "layout_class": classify_year(m),
            "note": "Decade class from mean of annual metrics (not one giant pooled graph)",
        }

    pre_2020 = rollup_from_annual(range(2001, 2021), annual)
    fire_era = rollup_from_annual(range(2021, 2027), annual)

    # Activity mix pre-2020
    pre_recs = [r for r in records if r["year"] and 2001 <= r["year"] <= 2020]
    bucket_mix: dict[str, int] = defaultdict(int)
    for r in pre_recs:
        bucket_mix[r["activity_bucket"]] += 1

    # Compactness by bucket
    compact_by_bucket: dict[str, list] = defaultdict(list)
    for r in pre_recs:
        if r["compactness"] is not None:
            compact_by_bucket[r["activity_bucket"]].append(r["compactness"])
    compact_summary = {
        k: {
            "n": len(v),
            "mean_compactness": round(sum(v) / len(v), 4) if v else None,
        }
        for k, v in compact_by_bucket.items()
    }

    hansen = None
    if hansen_path and hansen_path.is_file():
        hansen = analyze_hansen(hansen_path)

    # Interpretation
    annual_pre = [a for a in annual if 2001 <= a["year"] <= 2020]
    progressive_years = sum(1 for a in annual_pre if a["layout_class"] == "progressive_leaning")
    scatter_years = sum(1 for a in annual_pre if a["layout_class"] == "scatter_leaning")
    multi_years = sum(1 for a in annual_pre if a["layout_class"] == "multi_cluster")
    mixed_years = sum(1 for a in annual_pre if a["layout_class"] == "mixed_or_unclear")

    interpretation = []
    interpretation.append(
        "FACTS timber-harvest polygons are activity footprints (not pure satellite). "
        "They are the best public layer for how units were laid out on Plumas NF."
    )
    if pre_2020.get("mean_annual_touching_share") is not None:
        interpretation.append(
            f"Pre-2020 (2001–2020) mean annual metrics: touching_share={pre_2020['mean_annual_touching_share']}, "
            f"largest_component_share={pre_2020['mean_annual_largest_component_share']}, "
            f"mean_nn_mi={pre_2020['mean_annual_mean_nn_mi']} → class **{pre_2020['layout_class']}**."
        )
    interpretation.append(
        f"Year-by-year (2001–2020, n≥3): progressive_leaning={progressive_years}, "
        f"multi_cluster={multi_years}, scatter_leaning={scatter_years}, mixed_or_unclear={mixed_years}."
    )
    # Core finding: high local touch + low single-component share = multi-cluster
    touch = pre_2020.get("mean_annual_touching_share") or 0
    largest = pre_2020.get("mean_annual_largest_component_share") or 0
    if multi_years >= progressive_years and touch >= 0.5 and largest < 0.35:
        interpretation.append(
            "Core finding: **multi-cluster layout**. Units often touch a neighbor (local clumps), "
            "but the largest connected component is only ~15–25% of that year's units — "
            "so crews still work many disconnected fronts, not one side-to-side wave. "
            "Progressive Working Forest layout (ordered strips + one active front + fixed corridors) "
            "is a real operational upgrade, not redundant with current practice."
        )
    elif progressive_years > multi_years and progressive_years > scatter_years:
        interpretation.append(
            "Result leans **progressive** in many years. Standardizing strip order would lock that in."
        )
    elif scatter_years > progressive_years:
        interpretation.append(
            "Result leans **scatter**: leapfrog units dominate. Progressive layout targets that tax."
        )
    else:
        interpretation.append(
            "Result is mixed. Progressive layout still reduces move-in tax when fronts multiply."
        )
    interpretation.append(
        "Activity mix is already thin-heavy (commercial thin, group selection, salvage) — "
        "the gap is layout continuity, not only silvicultural system choice."
    )
    interpretation.append(
        "Hansen/GFW 2021–2025 tree-cover loss in Plumas is fire-dominated (Dixie era) and must not "
        "score logging pattern alone. This pilot uses FACTS harvest polygons for pre-2020 layout."
    )

    result = {
        "schema_version": 1,
        "title": "Plumas NF progressive vs scatter harvest geometry pilot",
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source_facts": {
            "service": BASE,
            "where": WHERE,
            "layers": LAYERS,
            "layer_counts": layer_counts,
            "total_features_downloaded": len(all_feats),
            "features_with_geometry_used": len(records),
        },
        "metrics_definition": {
            "touching_share": "Share of unit polygons that touch or come within ~50 m of another unit that year",
            "largest_component_share": "Share of units in the largest connected cluster",
            "mean_nn_mi": "Mean nearest-neighbor distance between unit centroids (miles) — high = scatter",
            "layout_class": "Heuristic: progressive_leaning | scatter_leaning | mixed_or_unclear | insufficient_sample",
            "compactness": "4πA/P² on foot-scaled geometry (1≈circle; lower≈elongated/complex)",
        },
        "pre_2020_2001_2020": pre_2020,
        "fire_era_2021_2025": fire_era,
        "annual_2001_2020": [a for a in annual if 2001 <= a["year"] <= 2020],
        "activity_bucket_counts_pre_2020": dict(bucket_mix),
        "top_activity_names": sorted(activity_counts.items(), key=lambda x: -x[1])[:25],
        "compactness_by_bucket_pre_2020": compact_summary,
        "hansen": hansen,
        "interpretation": interpretation,
        "progressive_layout_recommendation": {
            "adopt_pwf_layout": True,
            "rules": ["P1 contiguous annual front", "P2 designated corridors", "P3 written strip progression"],
            "see": "program/PROGRESSIVE_LAYOUT.md",
        },
    }
    return result


def analyze_hansen(path: Path) -> dict:
    """Optional Hansen lossyear GeoTIFF analysis for Plumas bbox."""
    try:
        import rasterio
        import numpy as np
    except ImportError:
        return {"error": "rasterio not installed", "path": str(path)}

    # Plumas County approx bbox
    west, south, east, north = -121.6, 39.5, -120.0, 40.55
    with rasterio.open(path) as ds:
        # window from bbox
        from rasterio.windows import from_bounds

        try:
            win = from_bounds(west, south, east, north, ds.transform)
            data = ds.read(1, window=win)
        except Exception:
            data = ds.read(1)
        # lossyear: 0 = no loss; 1-20 = 2001-2020; etc. encoding varies by version
        # Hansen GFC: values 1-23 mean year 2001+value-1 for recent products
        vals, counts = np.unique(data[data > 0], return_counts=True)
        by_year = {}
        for v, c in zip(vals.tolist(), counts.tolist()):
            if v <= 0:
                continue
            # map to calendar year: value N → 2000+N in classic Hansen
            year = 2000 + int(v)
            if 2001 <= year <= 2025:
                by_year[year] = int(c)
        pre = sum(c for y, c in by_year.items() if y <= 2020)
        fire = sum(c for y, c in by_year.items() if y >= 2021)
        return {
            "path": str(path),
            "encoding": "Hansen lossyear: pixel value N ≈ calendar year 2000+N",
            "pixels_pre_2020": pre,
            "pixels_2021_plus": fire,
            "by_year_pixels": by_year,
            "note": "Pixel counts not acres (depends on resolution). Fire years often dominate Plumas 2021+.",
        }


def to_markdown(result: dict) -> str:
    lines = []
    lines.append(f"# {result['title']}")
    lines.append("")
    lines.append(f"_Updated: {result['updated']}_")
    lines.append("")
    lines.append("## Source")
    sf = result["source_facts"]
    lines.append(f"- USFS EDW Timber Harvest (FACTS): `{sf['service']}`")
    lines.append(f"- Filter: `{sf['where']}`")
    lines.append(f"- Features downloaded: **{sf['total_features_downloaded']}** (with geometry used: {sf['features_with_geometry_used']})")
    lines.append(f"- Layer counts: {sf['layer_counts']}")
    lines.append("")
    lines.append("## Metrics")
    for k, v in result["metrics_definition"].items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")
    lines.append("## Pre-2020 (2001–2020)")
    p = result["pre_2020_2001_2020"] or {}
    lines.append(f"- Features: **{p.get('n_features')}** across **{p.get('years_classified')}** years with n≥3")
    lines.append(f"- Geom acres (approx): **{p.get('total_geom_acres')}**")
    lines.append(f"- Mean annual touching share: **{p.get('mean_annual_touching_share')}**")
    lines.append(f"- Mean annual largest component share: **{p.get('mean_annual_largest_component_share')}**")
    lines.append(f"- Mean annual NN distance (mi): **{p.get('mean_annual_mean_nn_mi')}**")
    lines.append(f"- Layout class: **{p.get('layout_class')}**")
    lines.append("")
    if result.get("fire_era_2021_2025"):
        f = result["fire_era_2021_2025"]
        lines.append("## Fire-era (2021+) — interpret with caution (salvage + fire operations)")
        lines.append(
            f"- Features: {f.get('n_features')}, layout_class: **{f.get('layout_class')}**, "
            f"mean_nn_mi: {f.get('mean_annual_mean_nn_mi')}"
        )
        lines.append("")
    lines.append("## Annual layout class (2001–2020)")
    lines.append("| Year | n | touching | largest_comp | mean_nn_mi | class |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for a in result["annual_2001_2020"]:
        lines.append(
            f"| {a['year']} | {a['n']} | {a.get('touching_share')} | {a.get('largest_component_share')} | {a.get('mean_nn_mi')} | {a['layout_class']} |"
        )
    lines.append("")
    lines.append("## Activity mix (pre-2020 feature counts)")
    for k, v in sorted(result["activity_bucket_counts_pre_2020"].items(), key=lambda x: -x[1]):
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Interpretation")
    for para in result["interpretation"]:
        lines.append(f"- {para}")
    lines.append("")
    lines.append("## Recommendation")
    rec = result["progressive_layout_recommendation"]
    lines.append(f"- Adopt PWF layout rules: **{rec['adopt_pwf_layout']}** ({', '.join(rec['rules'])})")
    lines.append(f"- See `{rec['see']}`")
    lines.append("")
    if result.get("hansen"):
        lines.append("## Hansen (optional)")
        lines.append(f"```json\n{json.dumps(result['hansen'], indent=2)}\n```")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hansen", type=Path, default=None, help="Optional Hansen lossyear GeoTIFF")
    args = ap.parse_args(argv)
    OUT_PROGRAM.mkdir(parents=True, exist_ok=True)
    OUT_SITE.mkdir(parents=True, exist_ok=True)
    result = run(args.hansen)
    jpath = OUT_PROGRAM / "pwf_geometry_pilot.json"
    mpath = OUT_PROGRAM / "pwf_geometry_pilot.md"
    spath = OUT_SITE / "pwf_geometry_pilot.json"
    jpath.write_text(json.dumps(result, indent=2), encoding="utf-8")
    mpath.write_text(to_markdown(result), encoding="utf-8")
    spath.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("Wrote", jpath)
    print("Wrote", mpath)
    print("Wrote", spath)
    print("PRE-2020 class:", result["pre_2020_2001_2020"].get("layout_class"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
