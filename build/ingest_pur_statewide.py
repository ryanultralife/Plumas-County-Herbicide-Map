#!/usr/bin/env python3
"""Ingest a full CDPR statewide PUR year archive (pur{YEAR}.zip) into public.applications.

Why this exists: scraper/sources/pur.py filters to one region's counties. The site holds
statewide 2020-2022 plus a Northern-Sierra spine for 2023-2024. CDPR published the raw
2023 archive, so this loads 2023 for ALL 58 counties in the same shape as the existing
statewide rows.

Row shape is matched field-for-field against an existing pur:2022 row:
  app_id = pur:{year}:{use_no}      source = 'pur'      unit = 'lbs'
  owner  = grower_id (11-char GROWER_ID)    activity = site_code    method = NULL
  date   = MM/DD/YYYY               status = 'completed'
  lat/lon= PLSS section centroid (lib.comtrs_centroid), NULL when the section is missing
  acres  = acre_treated, only when unit_treated = 'A'

PUR emits one row per ACTIVE INGREDIENT per application. The table's grain is one row per
application, so we collapse on (year, use_no) keeping the AI with the largest lbs_chm_used.
That matches build/ingest_dpr_pur.py exactly. Amount is that single AI's pounds, never a sum.

Insert is ON CONFLICT (app_id) DO NOTHING, so re-running can never duplicate, and the
Northern-Sierra 2023 rows already loaded from the CPRA extract win over these.

Usage:
  python build/ingest_pur_statewide.py 2023               # transform + validate, no DB
  DBURL=... python build/ingest_pur_statewide.py 2023 --load
"""
import sys, os, csv, glob, json, subprocess, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scraper"))
import lib

csv.field_size_limit(200000000)

COLS = ["app_id", "source", "region", "date", "year", "lat", "lon", "county",
        "land_type", "owner", "product", "active_ingredient", "amount", "unit",
        "method", "activity", "project", "status", "url", "pulled", "acres"]

MONTHS = {"JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06",
          "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"}


def county_maps():
    """county_cd -> (Title-case county name, region key) for all 58 counties."""
    reg = json.load(open(os.path.join(ROOT, "scraper", "regions.json"), encoding="utf-8"))
    out = {}
    for key, r in reg["regions"].items():
        for c in r.get("counties", []):
            out[str(c["pur"]).zfill(2)] = (c["name"], key)
    return out


def fmt_date(v):
    """'01-AUG-2023' -> '08/01/2023' (the format already in the table)."""
    v = (v or "").strip().upper()
    if len(v) == 11 and v[2] == "-" and v[6] == "-":
        mm = MONTHS.get(v[3:6])
        if mm:
            return mm + "/" + v[:2] + "/" + v[7:]
    return None


def to_f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def transform(year, outpath):
    cmap = county_maps()
    base = os.path.join(ROOT, "data", "raw", "pur", "pur" + str(year))
    files = sorted(p for p in glob.glob(os.path.join(base, "**", "udc*.txt"), recursive=True))
    if not files:
        sys.exit("no udc files under " + base + " - unzip pur" + str(year) + ".zip first")

    best = {}
    scanned = 0
    skipped_county = 0
    no_section = 0
    pulled = time.strftime("%Y-%m-%d")

    for path in files:
        with open(path, encoding="latin-1", newline="") as f:
            for row in csv.DictReader(f):
                scanned += 1
                cc = (row.get("county_cd") or "").strip().zfill(2)
                hit = cmap.get(cc)
                if not hit:
                    skipped_county += 1
                    continue
                county, region = hit
                use_no = (row.get("use_no") or "").strip()
                if not use_no:
                    continue
                lbs = to_f(row.get("lbs_chm_used")) or 0.0
                prev = best.get(use_no)
                if prev is not None and prev[0] >= lbs:
                    continue

                lat, lon = lib.comtrs_centroid(
                    row.get("base_ln_mer"), row.get("township"), row.get("tship_dir"),
                    row.get("range"), row.get("range_dir"), row.get("section"))
                if lat is None:
                    no_section += 1

                acres = None
                if (row.get("unit_treated") or "").strip().upper() == "A":
                    acres = to_f(row.get("acre_treated"))

                owner = (row.get("grower_id") or "").strip() or None
                site_name = (row.get("site_name") or "").strip() or None
                land = lib.classify(owner=owner, site=site_name) or "ag"

                best[use_no] = (lbs, [
                    "pur:" + str(year) + ":" + use_no, "pur", region,
                    fmt_date(row.get("applic_dt")),
                    year, lat, lon, county, land, owner,
                    (row.get("product_name") or "").strip(),
                    (row.get("chemname") or "").strip(),
                    to_f(row.get("lbs_chm_used")), "lbs",
                    None, (row.get("site_code") or "").strip() or None,
                    None, "completed", "https://calpip.cdpr.ca.gov/", pulled, acres,
                ])
        print("  [" + os.path.basename(path) + "] scanned=" + format(scanned, ",")
              + " kept=" + format(len(best), ","), flush=True)

    with open(outpath, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for _, r in best.values():
            w.writerow(r)

    with_ll = sum(1 for _, r in best.values() if r[5] is not None)
    with_ac = sum(1 for _, r in best.values() if r[20] is not None)
    n = max(len(best), 1)
    print("")
    print("scanned AI-rows  : " + format(scanned, ","))
    print("other/unmapped   : " + format(skipped_county, ","))
    print("applications     : " + format(len(best), ","))
    print("  with lat/lon   : " + format(with_ll, ",") + " (" + format(100.0 * with_ll / n, ".1f") + "%)")
    print("  with acres     : " + format(with_ac, ",") + " (" + format(100.0 * with_ac / n, ".1f") + "%)")
    print("  no PLSS section: " + format(no_section, ",") + " AI-rows")
    print("wrote " + outpath)
    return len(best)


def run_sql(conn, sql, capture=False):
    cmd = ["psql", conn, "-v", "ON_ERROR_STOP=1", "-c", sql]
    if capture:
        cmd.insert(2, "-qtA")
        return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    subprocess.run(cmd, check=True)
    return None


def load(csvpath, year, conn):
    stage = "stage_pur_" + str(year)
    run_sql(conn, "drop table if exists " + stage + "; "
                  "create unlogged table " + stage + " (like applications including defaults);")
    print("staging table created; copying...", flush=True)
    cp = "\\copy " + stage + " (" + ",".join(COLS) + ") from '" + csvpath + \
         "' with (format csv, header true)"
    subprocess.run(["psql", conn, "-v", "ON_ERROR_STOP=1", "-c", cp], check=True)
    n = int(run_sql(conn, "select count(*) from " + stage + ";", capture=True).strip())
    print("staged rows: " + format(n, ","), flush=True)

    before = int(run_sql(conn, "select count(*) from applications;", capture=True).strip())
    # statement_timeout must be cleared in the SAME session as the insert; a multi-million
    # row insert through the pooler exceeds the default limit.
    run_sql(conn, "set statement_timeout = 0; "
            "insert into applications (" + ",".join(COLS) + ") select "
            + ",".join(COLS) + " from " + stage + " on conflict (app_id) do nothing;")
    after = int(run_sql(conn, "select count(*) from applications;", capture=True).strip())
    print("applications: " + format(before, ",") + " -> " + format(after, ",")
          + "  (+" + format(after - before, ",") + ")")
    run_sql(conn, "drop table if exists " + stage + ";")
    return after - before


if __name__ == "__main__":
    year = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 2023
    out = os.path.join(ROOT, "data", "raw", "pur",
                       "applications_pur_" + str(year) + "_statewide.csv")
    if "--load-only" not in sys.argv:
        transform(year, out)
    if "--load" in sys.argv or "--load-only" in sys.argv:
        conn = os.environ.get("DBURL") or os.environ.get("DATABASE_URL")
        if not conn:
            sys.exit("set DBURL")
        load(out, year, conn)
