#!/usr/bin/env python3
"""
Identify real operator names for CDPR PUR GROWER_IDs using the public
permit-holder datasets that some County Agricultural Commissioners publish.

Key insight (verified against our data): a PUR GROWER_ID like 27222700348 is
[reporting county 2][permit year 2][home-county+permit 7]. The trailing 7 chars
(2700348) ARE the county "permit number" published in those datasets, with the
leading 2 digits = the operator's home county. So:  right(owner,7) == PermNum.

This fetches each available county dataset -> {permnum: name}, writes a combined
CSV, then (in SQL) joins right(owner,7)=permnum across ALL our GROWER_IDs and
upserts (grower_id -> name) into public.operator_names. After that, the frontend's
loadOperatorNames() shows the real name everywhere (map popups, Data & Trends,
Source Data), overriding the coded ID.

Usage:  DBURL="postgres://..." python build/enrich_operator_names.py
"""
import os, sys, csv, io, json, zipfile, urllib.request, urllib.parse, subprocess, tempfile

UA = {"User-Agent": "Mozilla/5.0 (SprayMap transparency project)"}

def fetch(url, timeout=120):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read()

def norm_perm(v):
    s = str(v).split(".")[0]               # handle "3200530.0" float-style ids
    s = "".join(ch for ch in s if ch.isdigit())
    return s.zfill(7) if s else None

def clean_name(n):
    n = " ".join(str(n or "").split()).strip().strip(",").upper()
    return n if n and n not in ("NULL", "NONE", "N/A") else None

rows = {}   # permnum -> (name, county, source)   first non-empty wins
def add(permnum, name, county, source):
    p, nm = norm_perm(permnum), clean_name(name)
    if p and nm and p not in rows:
        rows[p] = (nm, county, source)

# ---------- Monterey (27): ArcGIS FeatureServer ----------
def monterey():
    base = ("https://services2.arcgis.com/nOGTdfb4kF4dZljH/arcgis/rest/services/"
            "2020RanchMapAtlasDataOD/FeatureServer/0/query")
    off, got = 0, 0
    while True:
        url = (base + "?where=1%3D1&outFields=PermNum,Permittee&returnGeometry=false"
               "&f=json&resultRecordCount=2000&resultOffset=" + str(off))
        d = json.loads(fetch(url))
        feats = d.get("features", [])
        if not feats:
            break
        for f in feats:
            a = f.get("attributes", {})
            add(a.get("PermNum"), a.get("Permittee"), "Monterey", "monterey-ranch-atlas-2020")
        got += len(feats); off += len(feats)
        if not d.get("exceededTransferLimit") and len(feats) < 2000:
            break
    return got

# ---------- Kern (15): zipped CSV ----------
def kern():
    import openpyxl
    z = zipfile.ZipFile(io.BytesIO(fetch("http://www.kernag.com/ep/permit-use/20_29/2024_kern_permit.zip")))
    xn = [n for n in z.namelist() if n.lower().endswith(".xlsx")]
    if not xn:
        return 0
    wb = openpyxl.load_workbook(io.BytesIO(z.read(xn[0])), read_only=True, data_only=True)
    ws = wb.active
    hdr = None; pi = oi = None; n = 0
    for row in ws.iter_rows(values_only=True):
        if hdr is None:
            hdr = [str(c or "").strip() for c in row]
            for i, h in enumerate(hdr):
                if h == "Permit Number": pi = i
                if h == "Permittee": oi = i
            if pi is None or oi is None:
                hdr = None
            continue
        if pi < len(row) and oi < len(row):
            add(row[pi], row[oi], "Kern", "kern-permits-2024"); n += 1
    return n

# ---------- Stanislaus (50): ArcGIS Hub open data (CSV download) ----------
def stanislaus():
    base = ("https://services.arcgis.com/EeYBJFxLdUojipYa/arcgis/rest/services/"
            "Permit_Sites_and_Commodities_Open_Data/FeatureServer/7/query")
    where = urllib.parse.quote("Permit_Type IN ('Op-Id','RMP')")
    off, n = 0, 0
    while True:
        url = (base + "?where=" + where + "&outFields=Permit_Number,Operator&returnGeometry=false"
               "&f=json&resultRecordCount=2000&resultOffset=" + str(off))
        d = json.loads(fetch(url))
        feats = d.get("features", [])
        if not feats:
            break
        for f in feats:
            a = f.get("attributes", {})
            add(a.get("Permit_Number"), a.get("Operator"), "Stanislaus", "stanislaus-permits")
        n += len(feats); off += len(feats)
        if not d.get("exceededTransferLimit") and len(feats) < 2000:
            break
    return n

# ---------- San Joaquin (39): XLSX ----------
def san_joaquin():
    try:
        import openpyxl
    except ImportError:
        print("  (san_joaquin skipped: openpyxl not installed)")
        return 0
    raw = fetch("https://www.sjgov.org/docs/default-source/agricultural-commissioner-documents/"
                "pur-business-lic/permits/permits-2024-.xlsx?sfvrsn=8d6c9a21_6")
    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    ws = wb.active
    hdr = None; pi = oi = None; n = 0
    for row in ws.iter_rows(values_only=True):
        if hdr is None:
            hdr = [str(c or "").strip() for c in row]
            for i, h in enumerate(hdr):
                if h == "Permit Number": pi = i
                if h == "Operator": oi = i
            if pi is None or oi is None:
                hdr = None
            continue
        if pi < len(row) and oi < len(row):
            add(row[pi], row[oi], "San Joaquin", "sanjoaquin-permits-2024")
            n += 1
    return n

# ---------- Plumas (32) + others already obtained: local records-request CSVs ----------
def plumas_local():
    n = 0
    for fn, pcol, ncol in [("data/single_job_pur.csv", "Permit #", "Permitee"),
                           ("data/prodag_monthly_summary.csv", "Permit #", "Permitee"),
                           ("data/nonprod_ag_mspur.csv", "Permit #", "Permittee")]:
        try:
            with open(fn, newline="", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    add(row.get(pcol), row.get(ncol), "Plumas", "plumas-records-2021-2024")
                    n += 1
        except FileNotFoundError:
            pass
    return n

def main():
    dburl = os.environ.get("DBURL")
    if not dburl:
        sys.exit("Set DBURL in the environment.")
    for label, fn in [("plumas_local", plumas_local), ("monterey", monterey), ("kern", kern),
                      ("stanislaus", stanislaus), ("san_joaquin", san_joaquin)]:
        try:
            c = fn(); print(f"  {label}: {c:,} source rows fetched")
        except Exception as e:
            print(f"  {label}: FAILED ({type(e).__name__}: {e})")
    print(f"Total distinct permit numbers with names: {len(rows):,}")
    if not rows:
        sys.exit("No name data fetched.")

    tmp = tempfile.NamedTemporaryFile("w", delete=False, newline="", suffix=".csv", encoding="utf-8")
    w = csv.writer(tmp)
    for p, (nm, cty, src) in rows.items():
        w.writerow([p, nm, cty, src])
    tmp.close()

    sql = f"""
create temp table _perm (permnum text, name text, county text, source text);
\\copy _perm from '{tmp.name.replace(os.sep,'/')}' csv
insert into public.operator_names (operator_id, name, entity_type, source, county, updated)
select a.owner, p.name, null, p.source, p.county, current_date::text
from (select distinct owner from public.applications
      where owner is not null and length(owner)>=7 and owner ~ '[0-9]') a
join _perm p on right(a.owner,7) = p.permnum
on conflict (operator_id) do update set
  name=excluded.name, source=excluded.source, county=excluded.county, updated=excluded.updated;
select count(*) as operator_ids_named from public.operator_names;
"""
    sqlf = tempfile.NamedTemporaryFile("w", delete=False, suffix=".sql", encoding="utf-8")
    sqlf.write("set statement_timeout=0;\n" + sql)
    sqlf.close()
    r = subprocess.run(["psql", dburl, "-v", "ON_ERROR_STOP=1", "-f", sqlf.name],
                       capture_output=True, text=True)
    os.unlink(tmp.name); os.unlink(sqlf.name)
    print(r.stdout.strip())
    if r.returncode != 0:
        sys.exit(r.stderr.strip())

if __name__ == "__main__":
    main()
