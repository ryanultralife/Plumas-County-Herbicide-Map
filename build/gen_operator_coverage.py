#!/usr/bin/env python3
"""Generate data/operator_coverage.json — the per-county share of mapped
applications that have an identifiable operator NAME (via public.operator_names),
plus HOW those names are available for each county:

  access = "download"  -> the county publishes a public permit roster we ingest
                          (see build/enrich_operator_names.py)
  access = "request"   -> no open roster; names come only from cross-county
                          matches + public-records (CPRA) requests

Feeds the site's "Operator identification" panel (index.html renderDataHtml).
Run AFTER enrich_operator_names.py. Usage: DBURL=... python build/gen_operator_coverage.py
"""
import os, sys, json, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Counties whose names we ingest from a public, downloadable permit roster.
PUBLIC_ROSTER = {
    "Plumas", "Monterey", "Kern", "Stanislaus", "San Joaquin", "Riverside",
    "Santa Barbara", "Contra Costa", "Napa", "San Diego", "Santa Cruz",
    "Colusa", "Yolo", "Fresno", "Merced", "Kings", "Sutter",
}

SQL = (
    "set statement_timeout=0;\n"
    "select a.county, count(*) apps, count(o.name) named, coalesce(max(j.region),'') region\n"
    "from public.applications a\n"
    "left join public.operator_names o on o.operator_id=a.owner\n"
    "left join (select distinct county, region from public.juris_agg where county is not null) j\n"
    "       on j.county=a.county\n"
    "where a.lat is not null and a.county is not null\n"
    "group by a.county order by a.county;"
)


def main():
    dburl = os.environ.get("DBURL")
    if not dburl:
        sys.exit("Set DBURL in the environment.")
    r = subprocess.run(["psql", dburl, "-tAF", "\t", "-c", SQL],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(r.stderr.strip())

    counties, tot_apps, tot_named = {}, 0, 0
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line or "\t" not in line:
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        county, apps, named = parts[0], int(parts[1]), int(parts[2])
        region = parts[3] if len(parts) > 3 else ""
        pct = round(100.0 * named / apps, 1) if apps else 0
        tot_apps += apps
        tot_named += named
        # "download" only where a public roster exists AND actually covers a
        # meaningful share (Fresno's public layer is 278 permits / 0.6% -> "request").
        access = "download" if (county in PUBLIC_ROSTER and pct >= 20) else "request"
        counties[county] = {
            "apps": apps, "named": named, "pct": pct,
            "region": region, "access": access,
        }

    out = {
        "generated": None,  # stamped by caller/git; scripts can't call Date.now()
        "statewide": {
            "apps": tot_apps,
            "named": tot_named,
            "pct": round(100.0 * tot_named / tot_apps, 1) if tot_apps else 0,
            "public_counties": sorted(c for c, e in counties.items() if e["access"] == "download"),
        },
        "counties": counties,
    }
    path = os.path.join(ROOT, "data", "operator_coverage.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print("wrote %s : %d counties, statewide %.1f%% (%d of %d)"
          % (path, len(counties), out["statewide"]["pct"], tot_named, tot_apps))


if __name__ == "__main__":
    main()
