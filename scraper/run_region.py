#!/usr/bin/env python3
"""
Region runner -- the one command Claude (or you) uses to scrape a region.

  python scraper/run_region.py northern-sierra                 # FACTS (federal), default
  python scraper/run_region.py northern-sierra --sources facts,pur,thp
  python scraper/run_region.py northern-sierra --load-existing data/plumas_nf_herbicide_facts.geojson

Each source normalizes into one SQLite table (data/db/applications.sqlite); the runner
then exports data/exports/<region>.geojson for the map. Re-runnable; rows upsert by id.
"""
import sys, os, json, argparse, importlib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib


def load_existing(cx, region_key, path):
    """Import an already-pulled FACTS-style GeoJSON into the unified table."""
    fc = json.load(open(os.path.join(lib.ROOT, path)))
    rows = []
    for i, ft in enumerate(fc["features"]):
        p = ft["properties"]; lon, lat = ft["geometry"]["coordinates"]
        rows.append({"app_id": f"facts:exist:{i}", "source": p.get("source", "facts").lower(),
            "region": region_key, "date": None, "year": p.get("year"), "lat": lat, "lon": lon,
            "county": p.get("county"), "land_type": p.get("land_type") or lib.classify(
                activity=p.get("activity"), project=p.get("nepa_project")) or "federal",
            "owner": p.get("owner"), "product": None, "active_ingredient": None,
            "amount": p.get("acres"), "unit": "acres", "method": p.get("method"),
            "activity": p.get("activity"), "project": p.get("nepa_project"),
            "status": p.get("status"), "url": None, "pulled": p.get("pulled")})
    return lib.upsert(cx, rows)


def summary(cx, region_key):
    cur = cx.execute("SELECT source,land_type,year FROM applications WHERE region=?", (region_key,))
    by_src, by_land, by_year = collections.Counter(), collections.Counter(), collections.Counter()
    n = 0
    for s, l, y in cur:
        n += 1; by_src[s] += 1; by_land[l] += 1; by_year[y] += 1
    print(f"\n  TOTAL {n} applications in '{region_key}'")
    print("  by source:", dict(by_src))
    print("  by land:  ", dict(by_land))
    print("  by year:  ", dict(sorted((k, v) for k, v in by_year.items() if k)))


def export_all(cx, out_path):
    """Combined statewide GeoJSON across every region."""
    cur = cx.execute("SELECT * FROM applications")
    cols = [d[0] for d in cur.description]; feats = []
    for row in cur:
        r = dict(zip(cols, row))
        if r["lat"] is None or r["lon"] is None:
            continue
        feats.append({"type": "Feature",
                      "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
                      "properties": {k: r[k] for k in r if k not in ("lat", "lon")}})
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    json.dump({"type": "FeatureCollection", "name": "california", "features": feats},
              open(out_path, "w"), separators=(",", ":"))
    return len(feats)


def run_one(cx, key, region, sources):
    for name in [s.strip() for s in sources.split(",") if s.strip()]:
        mod = importlib.import_module(f"sources.{name}")
        print(f"[{name}] {key} ...")
        lib.upsert(cx, mod.pull(key, region))
    out = os.path.join(lib.ROOT, "data", "exports", f"{key}.geojson")
    n = lib.export_geojson(cx, key, out)
    print(f"  exported {n} -> {os.path.relpath(out, lib.ROOT)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("region", help="a region key, or 'all' for the whole state")
    ap.add_argument("--sources", default="facts")
    ap.add_argument("--load-existing")
    ap.add_argument("--no-export", action="store_true")
    args = ap.parse_args()

    regions = lib.load_regions()
    cx = lib.connect()

    if args.load_existing:
        print("loading existing:", args.load_existing)
        print("  wrote", load_existing(cx, args.region, args.load_existing))
        summary(cx, args.region); return

    keys = list(regions) if args.region == "all" else [args.region]
    for k in keys:
        if k not in regions:
            sys.exit(f"unknown region '{k}'. Known: all, {', '.join(regions)}")
    for k in keys:
        print(f"\n===== {k} ({regions[k]['label']}) =====")
        run_one(cx, k, regions[k], args.sources)
        summary(cx, k)

    if args.region == "all":
        out = os.path.join(lib.ROOT, "data", "exports", "california.geojson")
        print(f"\n  STATEWIDE export: {export_all(cx, out)} features -> "
              f"{os.path.relpath(out, lib.ROOT)}")


if __name__ == "__main__":
    main()
