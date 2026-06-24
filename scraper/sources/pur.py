"""
Source module: California DPR Pesticide Use Reporting (PUR) -- PRIVATE/ag/utility/rail land.
Downloads the statewide annual archives, keeps only the region's counties, joins the
product + chemical lookup tables, derives lat/lon from the PLSS section, and normalizes.

PUR archive: https://files.cdpr.ca.gov/pub/outgoing/pur_archives/pur{YEAR}.zip
Each ~150-260 MB; latest posted year is 2023. Run locally (large download).
"""
import sys, os, io, csv, zipfile, glob, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lib
try:
    import requests
except ImportError:
    requests = None

ARCHIVE = "https://files.cdpr.ca.gov/pub/outgoing/pur_archives/pur{y}.zip"
YEARS = [2020, 2021, 2022, 2023]
RAW = os.path.join(lib.ROOT, "data", "raw", "pur")
csv.field_size_limit(10_000_000)


def _download(year):
    os.makedirs(RAW, exist_ok=True)
    z = os.path.join(RAW, f"pur{year}.zip")
    if not os.path.exists(z):
        url = ARCHIVE.format(y=year)
        print(f"  [pur] downloading {url}")
        with requests.get(url, stream=True, timeout=600) as r:
            r.raise_for_status()
            with open(z, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
    d = os.path.join(RAW, f"pur{year}")
    if not os.path.isdir(d):
        with zipfile.ZipFile(z) as zf:
            zf.extractall(d)
    return d


def _load_lookup(folder, name, key, val):
    """Build {key: val} from a DPR lookup file (product.txt / chemical.txt) if present."""
    out = {}
    for path in glob.glob(os.path.join(folder, "**", name), recursive=True):
        for row in csv.DictReader(open(path, encoding="latin-1")):
            row = {k.lower(): v for k, v in row.items()}
            if key in row and val in row:
                out[row[key]] = row[val]
        break
    return out


def _col(row, *names):
    for n in names:
        if n in row and row[n] not in (None, ""):
            return row[n]
    return None


def pull(region_key, region):
    if requests is None:
        sys.exit("pip install requests")
    county_codes = {c["pur"]: c["name"] for c in region["counties"]}
    rows, pulled = [], time.strftime("%Y-%m-%d")
    for year in YEARS:
        folder = _download(year)
        prod = _load_lookup(folder, "product.txt", "prodno", "product_name")
        chem = _load_lookup(folder, "chemical.txt", "chem_code", "chemname")
        # comprehensive use files; column names are header-driven (lowercased)
        data_files = [p for p in glob.glob(os.path.join(folder, "**", "*.txt"), recursive=True)
                      if os.path.basename(p).lower().startswith(("udc", "pur"))]
        for path in data_files:
            for row in csv.DictReader(open(path, encoding="latin-1")):
                row = {k.lower(): v for k, v in row.items()}
                cc = _col(row, "county_cd", "county_code")
                if cc not in county_codes:
                    continue
                lat, lon = lib.comtrs_centroid(
                    _col(row, "base_ln_mer", "baseline_meridian"),
                    _col(row, "township"), _col(row, "tship_dir", "township_dir"),
                    _col(row, "range"), _col(row, "range_dir"),
                    _col(row, "section"))
                prodno = _col(row, "prodno", "product_no")
                chemcd = _col(row, "chem_code")
                site = _col(row, "site_name", "site_code")
                owner = _col(row, "applic_name", "grower_id", "permit_holder")
                land = lib.classify(owner=owner, site=site) or "ag"
                rows.append({
                    "app_id": f"pur:{year}:{_col(row,'use_no','record_id') or len(rows)}",
                    "source": "pur", "region": region_key,
                    "date": _col(row, "applic_dt", "application_date"),
                    "year": year, "lat": lat, "lon": lon, "county": county_codes[cc],
                    "land_type": land, "owner": owner,
                    "product": prod.get(prodno, prodno),
                    "active_ingredient": chem.get(chemcd, chemcd),
                    "amount": _col(row, "lbs_chm_used", "lbs_prd_used"),
                    "unit": "lbs", "method": _col(row, "applic_method"),
                    "activity": site, "project": None, "status": "completed",
                    "url": "https://calpip.cdpr.ca.gov/", "pulled": pulled})
        print(f"  [pur] {year}: {sum(1 for r in rows if r['year']==year)} region records")
    return rows
