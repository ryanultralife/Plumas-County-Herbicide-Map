#!/usr/bin/env python3
"""Ingest the CPRA-obtained DPR PUR extract (2020-2024, five Northern Sierra
counties: Butte, Tehama, Lassen, Plumas, Sierra) into public.applications.

Only NEW years are loaded: 2020-2022 are already present statewide (verified to
<0.4% against this extract), so we filter to 2023-2024 and insert with
ON CONFLICT (app_id) DO NOTHING so a re-run can never duplicate rows.

Column mapping mirrors scraper/sources/pur.py (the authoritative transform):
  app_id            = pur:{YEAR}:{USE_NO}
  owner             = GROWER_ID            product = PRODUCT_NAME
  active_ingredient = CHEMNAME             amount  = LBS_CHM_USED   unit = lbs
  activity          = SITE_CODE            date    = APPLIC_END/START_DT -> MM/DD/YYYY
  lat/lon           = comtrs_centroid(parsed COMTRS)   (null when COMTRS lacks a section)
  county            = Title(COUNTY)        region  = REGION[county]
  land_type         = lib.classify(owner, site) or 'ag'
PUR reports one product per USE_NO but expands to one row per active ingredient;
we collapse to one row per (year,use_no) keeping the AI with the largest
LBS_CHM_USED (deterministic; co-formulated AIs share a chem_class). Amount stays
that single AI's pounds (never summed) — matching the existing table's grain.

Coordinates are section CENTROIDS here; run the water-safe placement afterward
(build/fix_water_coords.py rule) so no 2023-2024 dot lands in a lake.

Usage:
  python build/ingest_dpr_pur.py                 # transform + validate only (no DB)
  DBURL=... python build/ingest_dpr_pur.py --load # stage + insert (dedup) + report
"""
import sys, os, csv, subprocess, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scraper"))
import lib  # comtrs_centroid, classify

csv.field_size_limit(100_000_000)
SRC = os.path.join(ROOT, "data", "raw", "cpra", "dpr_data.csv")
OUT = os.path.join(ROOT, "data", "raw", "cpra", "applications_dpr_2023_2024.csv")
NEW_YEARS = {"2023", "2024"}
REGION = {"Butte": "northern-sierra", "Lassen": "northern-sierra",
          "Plumas": "northern-sierra", "Sierra": "northern-sierra",
          "Tehama": "shasta-cascade"}
COLS = ["app_id", "source", "region", "date", "year", "lat", "lon", "county",
        "land_type", "owner", "product", "active_ingredient", "amount", "unit",
        "method", "activity", "project", "status", "url", "pulled"]

# dpr_data.csv column indices (37-col DPR extract)
I = {"YEAR": 0, "USE_NO": 1, "GROWER_ID": 4, "SITE_CODE": 6, "SITE_NAME": 7,
     "PRODUCT_NAME": 9, "CHEMNAME": 21, "LBS_CHM_USED": 22,
     "APPLIC_START_DT": 27, "APPLIC_END_DT": 28, "COUNTY": 32, "COMTRS": 33}


def parse_comtrs(cm):
    """'04M18N02E26' -> centroid lat/lon. Layout: county(2) mer(1) twp(2) dir(1)
    rng(2) dir(1) sec(2). Anything shorter has no section -> (None, None)."""
    cm = (cm or "").strip()
    if len(cm) != 11:
        return (None, None)
    return lib.comtrs_centroid(cm[2], cm[3:5], cm[5], cm[6:8], cm[8], cm[9:11])


def fmt_date(end, start):
    v = (end or start or "").strip()
    if len(v) >= 10 and v[4] == "-":
        y, m, d = v[:4], v[5:7], v[8:10]
        return f"{m}/{d}/{y}"
    return None


def to_f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def transform():
    best = {}  # (year,use_no) -> (lbs_for_ranking, row_fields)
    scanned = 0
    with open(SRC, encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            scanned += 1
            if row[I["YEAR"]] not in NEW_YEARS:
                continue
            key = (row[I["YEAR"]], row[I["USE_NO"]])
            lbs = to_f(row[I["LBS_CHM_USED"]]) or 0.0
            cur = best.get(key)
            if cur is not None and lbs <= cur[0]:
                continue  # keep the higher-lbs active ingredient
            county = (row[I["COUNTY"]] or "").title()
            lat, lon = parse_comtrs(row[I["COMTRS"]])
            owner = (row[I["GROWER_ID"]] or "").strip()
            site = row[I["SITE_NAME"]] or row[I["SITE_CODE"]]
            rec = {
                "app_id": f"pur:{row[I['YEAR']]}:{row[I['USE_NO']]}",
                "source": "pur", "region": REGION.get(county, ""),
                "date": fmt_date(row[I["APPLIC_END_DT"]], row[I["APPLIC_START_DT"]]),
                "year": row[I["YEAR"]], "lat": lat, "lon": lon, "county": county,
                "land_type": lib.classify(owner=owner, site=site) or "ag",
                "owner": owner, "product": row[I["PRODUCT_NAME"]],
                "active_ingredient": row[I["CHEMNAME"]],
                "amount": to_f(row[I["LBS_CHM_USED"]]), "unit": "lbs",
                "method": None, "activity": row[I["SITE_CODE"]], "project": None,
                "status": "completed", "url": "https://calpip.cdpr.ca.gov/",
                "pulled": time.strftime("%Y-%m-%d")}
            best[key] = (lbs, rec)
    rows = [v[1] for v in best.values()]
    with open(OUT, "w", newline="", encoding="utf-8") as o:
        w = csv.DictWriter(o, fieldnames=COLS)
        w.writeheader()
        for rec in rows:
            w.writerow(rec)
    # validation summary
    import collections
    byc = collections.Counter((r["county"], r["year"]) for r in rows)
    nulls = sum(1 for r in rows if r["lat"] is None)
    reg = collections.Counter(r["region"] for r in rows)
    print(f"scanned {scanned:,} data rows -> {len(rows):,} distinct app_ids (2023-2024)")
    print(f"null-coord (no section in COMTRS): {nulls:,}  ({100*nulls/len(rows):.1f}%)")
    print("region:", dict(reg))
    print("county/year app_ids:")
    for k in sorted(byc):
        print(f"  {k[0]:8} {k[1]}: {byc[k]:,}")
    miss = [r["county"] for r in rows if not r["region"]]
    if miss:
        print("WARNING unmapped counties:", set(miss))
    print(f"-> {OUT}")
    return len(rows)


LOAD_SQL = """
set statement_timeout=0;
create temp table _dpr (like public.applications including defaults);
\\copy _dpr ({cols}) from '{csv}' csv header
select count(*) staged from _dpr;
insert into public.applications ({cols})
  select {cols} from _dpr
on conflict (app_id) do nothing;
select count(*) filter (where year=2023) y2023, count(*) filter (where year=2024) y2024,
       count(*) total_pur_after
from public.applications where source='pur';
"""


def load():
    dburl = os.environ.get("DBURL") or sys.exit("Set DBURL to load.")
    cols = ",".join(COLS)
    sql = "set client_min_messages=warning;\n" + LOAD_SQL.format(cols=cols, csv=OUT.replace(os.sep, "/"))
    sqlf = tempfile.NamedTemporaryFile("w", delete=False, suffix=".sql", encoding="utf-8")
    sqlf.write(sql)
    sqlf.close()
    r = subprocess.run(["psql", dburl, "-v", "ON_ERROR_STOP=1", "-f", sqlf.name],
                       capture_output=True, text=True)
    os.unlink(sqlf.name)
    print(r.stdout.strip())
    if r.returncode != 0:
        sys.exit(r.stderr.strip()[-2000:])


if __name__ == "__main__":
    n = transform()
    if "--load" in sys.argv and n:
        load()
