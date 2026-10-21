#!/usr/bin/env python3
"""Append one load to data/ingest_log.json (feeds the map's "new data" bubble).

Run it after every load that changes what the site shows: new application rows,
operator names, water-testing records, or a fix to rows already on the map.
The date is the day the data went live; the summary is plain language with the
real numbers from the load (no estimates).

Usage:
  python build/log_ingest.py --county Placer --county Nevada --kind applications \
      --source "CDPR Pesticide Use Report 2022" --rows 25062 \
      --summary "25,062 Placer and Nevada 2022 application rows." [--date 2026-09-19] [--request placer]
"""
import argparse, datetime, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "ingest_log.json")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--county", action="append", required=True, help="county name as on the map; repeat for several")
    ap.add_argument("--kind", required=True)
    ap.add_argument("--source", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--rows", type=int)
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--request", help="id of the matching row in data/records_requests.json")
    a = ap.parse_args()
    with open(PATH, encoding="utf-8") as f:
        log = json.load(f)
    if a.kind not in log["kinds"]:
        ap.error("--kind must be one of: " + ", ".join(log["kinds"]))
    datetime.date.fromisoformat(a.date)
    row = {"date": a.date, "counties": a.county, "kind": a.kind, "source": a.source, "summary": a.summary}
    if a.rows is not None: row["rows"] = a.rows
    if a.request: row["request_id"] = a.request
    log["loads"].append(row)
    log["loads"].sort(key=lambda r: r["date"], reverse=True)   # stable: same-day rows keep their order
    log["updated"] = max(log.get("updated", ""), a.date)
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(log, f, indent=2, ensure_ascii=False); f.write("\n")
    os.replace(tmp, PATH)
    print("logged:", a.date, a.kind, ", ".join(a.county))

if __name__ == "__main__":
    main()
