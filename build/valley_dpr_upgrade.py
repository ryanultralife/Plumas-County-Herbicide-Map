"""Valley upgrade: replace corrected-approx fallback coords with authoritative DPR
PLSS section centroids (CEN_LAT84/CEN_LONG84, joined by CO_MTRS). Reads the Phase-A
staging, upgrades every src='approx_fixed' app whose section is in a DPR county file."""
import shapefile, glob, os, csv, collections
SCRATCH = os.path.dirname(os.path.abspath(__file__))
ROOT = r"C:\Users\ryanv\Projects\Plumas-County-Herbicide-Map\.claude\worktrees\suspicious-sammet-763560"
RESTAGE = os.path.join(ROOT, "data", "raw", "cpra", "coord_restage_plss.csv")
OUT = os.path.join(SCRATCH, "valley_restage.csv")

# 1) which counties do the fallback (approx_fixed) apps live in?
fb_counties = collections.Counter()
fb_comtrs = set()
with open(RESTAGE) as f:
    for row in csv.DictReader(f):
        if row["src"] == "approx_fixed":
            fb_counties[row["county"]] += 1
            fb_comtrs.add(row["comtrs"])
print("fallback apps by county:", dict(fb_counties))
print("distinct fallback sections:", len(fb_comtrs))

# 2) build CO_MTRS -> (lat84,lon84) from the DPR county shapefiles we have (+ download more if needed)
CTY_FILE = {"Butte": "Butte_PLSS", "Tehama": "Tehama_PLSS"}
import urllib.request, zipfile
def ensure_county(cty):
    d = os.path.join(SCRATCH, cty + "_PLSS")
    if os.path.isdir(d) and glob.glob(os.path.join(d, "**", "*.shp"), recursive=True):
        return d
    z = os.path.join(SCRATCH, cty + "_PLSS.zip")
    url = f"https://calpip.cdpr.ca.gov/content/groundwater/shapefiles/{cty}_County_PLSS_NAD83AlbersCA.zip"
    urllib.request.urlretrieve(url, z); zipfile.ZipFile(z).extractall(d)
    return d

cent = {}
for cty in set(fb_counties) | {"Butte", "Tehama"}:
    try:
        d = ensure_county(cty)
    except Exception as e:
        print(f"  (no DPR file for {cty}: {e})"); continue
    shp = glob.glob(os.path.join(d, "**", "*.shp"), recursive=True)[0]
    r = shapefile.Reader(shp)
    fld = [f[0] for f in r.fields[1:]]
    iM, iLa, iLo = fld.index("CO_MTRS"), fld.index("CEN_LAT84"), fld.index("CEN_LONG84")
    for rec in r.records():
        cent[rec[iM]] = (round(float(rec[iLa]), 6), round(float(rec[iLo]), 6))
    print(f"  {cty}: {len(r)} sections loaded")

# 3) upgrade fallback apps
have = sum(1 for cm in fb_comtrs if cm in cent)
print(f"\nfallback sections resolvable via DPR grid: {have}/{len(fb_comtrs)}")
n = miss = 0
with open(RESTAGE) as f, open(OUT, "w", newline="") as o:
    w = csv.writer(o); w.writerow(["app_id", "lat", "lon", "comtrs", "county"])
    for row in csv.DictReader(f):
        if row["src"] != "approx_fixed":
            continue
        c = cent.get(row["comtrs"])
        if not c:
            miss += 1; continue
        w.writerow([row["app_id"], c[0], c[1], row["comtrs"], row["county"]]); n += 1
print(f"upgraded apps written: {n:,}   still-missing (no DPR section): {miss:,}")
print("wrote", OUT)
