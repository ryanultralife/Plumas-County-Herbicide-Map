#!/usr/bin/env python3
"""Backfill `acres` on existing statewide PUR rows from the CDPR year archives.

Why: statewide 2020-2022 were loaded without acre_treated (only the Northern Sierra
got acres, from a separate backfill). The 2023 load carried acres for every county,
which left the earlier years inconsistent. This fills the gap from the same public
archives (pur_archives/pur{YEAR}.zip) so acres mean the same thing for every year.

Rules:
  * acre_treated is taken ONLY when unit_treated = 'A' (PUR also reports square feet,
    cubic feet, pounds, tons, units - none of those are acres).
  * one application = one use_no; acre_treated is the same on every AI row of that
    use_no, so a dict use_no -> acres is exact.
  * UPDATE fills NULLs only (`acres is null`), so the Northern-Sierra rows that
    already carry acres are untouched and re-running is idempotent.
  * one UPDATE per year with statement_timeout cleared; if the pooler drops the
    connection the year is retried county by county.

Usage:
  python build/backfill_pur_acres.py 2020 2021 2022            # build CSVs only
  DBURL=... python build/backfill_pur_acres.py 2020 2021 2022 --load
"""
import sys, os, csv, glob, json, zipfile, subprocess, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "pur")
csv.field_size_limit(200000000)


def county_names():
    reg = json.load(open(os.path.join(ROOT, "scraper", "regions.json"), encoding="utf-8"))
    return sorted(c["name"] for r in reg["regions"].values() for c in r.get("counties", []))


def ensure_extracted(year):
    d = os.path.join(RAW, "pur" + str(year))
    if glob.glob(os.path.join(d, "**", "udc*.txt"), recursive=True):
        return d
    z = os.path.join(RAW, "pur" + str(year) + ".zip")
    if not os.path.exists(z) or os.path.getsize(z) < 1000000:
        sys.exit("missing or empty archive: " + z)
    print("extracting " + z, flush=True)
    with zipfile.ZipFile(z) as zf:
        zf.extractall(d)
    return d


def build_csv(year):
    d = ensure_extracted(year)
    files = sorted(glob.glob(os.path.join(d, "**", "udc*.txt"), recursive=True))
    acres = {}
    scanned = 0
    for path in files:
        with open(path, encoding="latin-1", newline="") as f:
            for row in csv.DictReader(f):
                scanned += 1
                if (row.get("unit_treated") or "").strip().upper() != "A":
                    continue
                use_no = (row.get("use_no") or "").strip()
                if not use_no or use_no in acres:
                    continue
                try:
                    v = float(row.get("acre_treated"))
                except (TypeError, ValueError):
                    continue
                if v > 0:
                    acres[use_no] = v
    out = os.path.join(RAW, "acres_pur_" + str(year) + ".csv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["app_id", "acres"])
        for use_no, v in acres.items():
            w.writerow(["pur:" + str(year) + ":" + use_no, v])
    print(str(year) + ": scanned " + format(scanned, ",") + " AI-rows -> "
          + format(len(acres), ",") + " applications with acres -> " + out, flush=True)
    return out


def psql(conn, sql, capture=False):
    cmd = ["psql", conn, "-v", "ON_ERROR_STOP=1"]
    if capture:
        cmd.append("-qtA")
    cmd += ["-c", sql]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-400:])
    return r.stdout.strip() if capture else None


def load_year(conn, year, csvpath):
    stage = "stage_acres_" + str(year)
    psql(conn, "drop table if exists " + stage + "; "
               "create unlogged table " + stage + " (app_id text primary key, acres double precision);")
    cp = "\\copy " + stage + " (app_id, acres) from '" + csvpath + "' with (format csv, header true)"
    subprocess.run(["psql", conn, "-v", "ON_ERROR_STOP=1", "-c", cp], check=True)
    n = psql(conn, "select count(*) from " + stage + ";", capture=True)
    print(str(year) + ": staged " + n + " rows", flush=True)

    before = psql(conn, "select count(*) from applications where year=" + str(year)
                  + " and source='pur' and acres is not null;", capture=True)
    sql = ("set statement_timeout = 0; "
           "update applications a set acres = s.acres from " + stage + " s "
           "where a.app_id = s.app_id and a.year = " + str(year)
           + " and a.source = 'pur' and a.acres is null;")
    try:
        psql(conn, sql)
        print(str(year) + ": single-statement update ok", flush=True)
    except RuntimeError as e:
        print(str(year) + ": whole-year update failed (" + str(e)[:120] + "); retrying by county", flush=True)
        for c in county_names():
            csql = ("set statement_timeout = 0; "
                    "update applications a set acres = s.acres from " + stage + " s "
                    "where a.app_id = s.app_id and a.year = " + str(year)
                    + " and a.source = 'pur' and a.county = '" + c.replace("'", "''")
                    + "' and a.acres is null;")
            for attempt in range(3):
                try:
                    psql(conn, csql)
                    break
                except RuntimeError as e2:
                    print("   " + c + " attempt " + str(attempt + 1) + " failed: " + str(e2)[:100], flush=True)
                    time.sleep(5)
    after = psql(conn, "select count(*) from applications where year=" + str(year)
                 + " and source='pur' and acres is not null;", capture=True)
    print(str(year) + ": rows with acres " + before + " -> " + after, flush=True)
    psql(conn, "drop table if exists " + stage + ";")


if __name__ == "__main__":
    years = [int(a) for a in sys.argv[1:] if a.isdigit()] or [2020, 2021, 2022]
    csvs = {y: build_csv(y) for y in years}
    if "--load" in sys.argv:
        conn = os.environ.get("DBURL") or os.environ.get("DATABASE_URL")
        if not conn:
            sys.exit("set DBURL")
        for y in years:
            load_year(conn, y, csvs[y])
