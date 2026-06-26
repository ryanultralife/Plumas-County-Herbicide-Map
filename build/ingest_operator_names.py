#!/usr/bin/env python3
"""
Ingest a county Agricultural Commissioner's permit-ID -> name file into
public.operator_names, so real applicator names appear on the map.

Usage:
  DBURL="postgres://..." python build/ingest_operator_names.py response.csv \
      --county "Fresno" --source "cac-fresno-2026"

The input CSV needs at least an operator-ID column and a name column. Common header
names are auto-detected (operator_id/permit/permit_no/grower_id/id ; name/permittee/
business/operator/company). Rows are upserted on operator_id.
"""
import os, sys, csv, subprocess, tempfile, argparse, datetime

ID_KEYS   = ("operator_id","permit","permit_no","permit_number","grower_id","oin","id")
NAME_KEYS = ("name","permittee","permittee_name","business","business_name","operator","company","grower")
TYPE_KEYS = ("entity_type","type","category")

def pick(header, keys):
    low = {h.lower().strip(): h for h in header}
    for k in keys:
        if k in low: return low[k]
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--county", default="")
    ap.add_argument("--source", default="cac")
    args = ap.parse_args()
    dburl = os.environ.get("DBURL")
    if not dburl:
        sys.exit("Set DBURL (the Supabase connection string) in the environment.")

    with open(args.csv, newline="", encoding="utf-8-sig") as f:
        rdr = csv.DictReader(f)
        idc, namec = pick(rdr.fieldnames, ID_KEYS), pick(rdr.fieldnames, NAME_KEYS)
        typc = pick(rdr.fieldnames, TYPE_KEYS)
        if not idc or not namec:
            sys.exit(f"Could not find ID/name columns in {rdr.fieldnames}")
        updated = datetime.date.today().isoformat()
        rows = []
        for r in rdr:
            oid = (r.get(idc) or "").strip()
            nm  = (r.get(namec) or "").strip()
            if not oid or not nm: continue
            rows.append((oid, nm, (r.get(typc) or "").strip() if typc else "",
                         args.source, args.county, updated))
    if not rows:
        sys.exit("No usable rows found.")

    tmp = tempfile.NamedTemporaryFile("w", delete=False, newline="", suffix=".csv", encoding="utf-8")
    w = csv.writer(tmp)
    for row in rows: w.writerow(row)
    tmp.close()

    sql = f"""
create temp table _op_in (operator_id text, name text, entity_type text, source text, county text, updated text);
\\copy _op_in from '{tmp.name.replace(os.sep, "/")}' csv
insert into public.operator_names (operator_id, name, entity_type, source, county, updated)
select operator_id, name, nullif(entity_type,''), source, nullif(county,''), updated from _op_in
on conflict (operator_id) do update set
  name=excluded.name, entity_type=excluded.entity_type, source=excluded.source,
  county=excluded.county, updated=excluded.updated;
select count(*) as ingested from _op_in;
"""
    p = subprocess.run(["psql", dburl, "-v", "ON_ERROR_STOP=1", "-c", sql],
                       capture_output=True, text=True)
    os.unlink(tmp.name)
    print(p.stdout.strip())
    if p.returncode != 0:
        sys.exit(p.stderr.strip())
    print(f"Ingested {len(rows)} operator names for {args.county or 'county'} (source={args.source}).")

if __name__ == "__main__":
    main()
