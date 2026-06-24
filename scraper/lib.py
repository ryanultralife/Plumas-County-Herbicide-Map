"""
Shared library for the region scraper: unified schema, SQLite I/O, GeoJSON export,
land-type classification, and PLSS section -> lat/lon centroid (for PUR data).

One row = one pesticide/herbicide application or chemical treatment, from any source.
"""
import sqlite3, json, os, math, re

# ---- canonical columns every source normalizes to ----
COLUMNS = [
    "app_id", "source", "region", "date", "year", "lat", "lon", "county",
    "land_type", "owner", "product", "active_ingredient", "amount", "unit",
    "method", "activity", "project", "status", "url", "pulled",
]

DDL = """
CREATE TABLE IF NOT EXISTS applications (
  app_id TEXT PRIMARY KEY,
  source TEXT, region TEXT, date TEXT, year INTEGER,
  lat REAL, lon REAL, county TEXT, land_type TEXT, owner TEXT,
  product TEXT, active_ingredient TEXT, amount REAL, unit TEXT,
  method TEXT, activity TEXT, project TEXT, status TEXT, url TEXT, pulled TEXT
);
CREATE INDEX IF NOT EXISTS ix_region ON applications(region);
CREATE INDEX IF NOT EXISTS ix_year   ON applications(year);
CREATE INDEX IF NOT EXISTS ix_land   ON applications(land_type);
CREATE INDEX IF NOT EXISTS ix_ai     ON applications(active_ingredient);
"""

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# DB path can be overridden via SCRAPER_DB (useful if the repo lives on a network
# mount where SQLite journaling fails; build locally, then copy the .sqlite in).
DB_PATH = os.environ.get("SCRAPER_DB") or os.path.join(ROOT, "data", "db", "applications.sqlite")


def connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    cx = sqlite3.connect(DB_PATH)
    cx.executescript(DDL)
    return cx


def upsert(cx, rows):
    """rows = list of dicts using COLUMNS keys. Returns count written."""
    q = ("INSERT OR REPLACE INTO applications (%s) VALUES (%s)"
         % (",".join(COLUMNS), ",".join("?" * len(COLUMNS))))
    cx.executemany(q, [[r.get(c) for c in COLUMNS] for r in rows])
    cx.commit()
    return len(rows)


def export_geojson(cx, region, out_path):
    cur = cx.execute("SELECT * FROM applications WHERE region=?", (region,))
    cols = [d[0] for d in cur.description]
    feats = []
    for row in cur:
        r = dict(zip(cols, row))
        if r["lat"] is None or r["lon"] is None:
            continue
        props = {k: r[k] for k in r if k not in ("lat", "lon")}
        feats.append({"type": "Feature",
                      "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
                      "properties": props})
    fc = {"type": "FeatureCollection", "name": f"pesticide applications - {region}",
          "features": feats}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    json.dump(fc, open(out_path, "w"), separators=(",", ":"))
    return len(feats)


# ---- land-type classification (shared across sources) ----
def classify(owner="", activity="", project="", site=""):
    s = " ".join(str(x or "").upper() for x in (owner, activity, project, site))
    if re.search(r"RAIL|UNION PACIFIC|BNSF|BURLINGTON|RAILWAY", s):       return "railroad"
    if re.search(r"PG&E|PACIFIC GAS|EDISON|\bSCE\b|UTILITY|ELECTRIC|TRANSMISSION|POWERLINE|GAS CO", s):
        return "utility"
    if re.search(r"CALTRANS|ROADSIDE|RIGHT OF WAY|ROAD MAINT|HIGHWAY", s): return "roadside"
    if re.search(r"FOREST|TIMBER|SILVICULTUR|REFOREST|PLANTATION", s):     return "forestry"
    if re.search(r"RANGE|PASTURE|GRAZ", s):                                return "rangeland"
    if re.search(r"LANDSCAPE|STRUCTURAL|RIGHTS|N-PRODUCTION|REGULATORY", s): return "other"
    return ""  # caller sets a default (federal for FACTS, ag for PUR commodity sites)


# ---- PLSS section centroid -> approx lat/lon (for PUR COMTRS) ----
# California base & meridian origins (lat, lon of the initial point).
MERIDIANS = {
    "M": (37.8817, -121.9144),   # Mount Diablo
    "S": (34.1208, -116.9258),   # San Bernardino
    "H": (40.4422, -124.1275),   # Humboldt
}
# section (1-36) center offset within a township, in miles east/north of township SW corner.
def _section_offset(sec):
    sec = int(sec)
    if not 1 <= sec <= 36:
        return None
    idx = sec - 1
    row = idx // 6                     # 0 = top (north)
    col = idx % 6
    if row % 2 == 1:                   # serpentine numbering
        col = 5 - col
    east = col + 0.5                   # miles from west edge
    north = (5 - row) + 0.5            # miles from south edge
    return east, north


def comtrs_centroid(base_mer, twp, twp_dir, rng, rng_dir, sec):
    """Approximate section-center lat/lon. base_mer in {M,S,H}. Consistent with the
    project's existing PLSS approximation; swap in a precise centroid table if needed."""
    try:
        b = MERIDIANS.get(str(base_mer).upper()[:1])
        if not b:
            return (None, None)
        blat, blon = b
        t = int(re.match(r"\d+", str(twp)).group())
        r = int(re.match(r"\d+", str(rng)).group())
        off = _section_offset(sec)
        if off is None:
            return (None, None)
        e_mi, n_mi = off
        # township SW corner relative to base
        north_mi = (t - 1) * 6 + n_mi
        east_mi = (r - 1) * 6 + e_mi
        if str(twp_dir).upper().startswith("S"): north_mi = -north_mi
        if str(rng_dir).upper().startswith("W"): east_mi = -east_mi
        lat = blat + north_mi / 69.0
        lon = blon + east_mi / (69.0 * math.cos(math.radians(blat)))
        return (round(lat, 5), round(lon, 5))
    except Exception:
        return (None, None)


def load_regions():
    return json.load(open(os.path.join(os.path.dirname(__file__), "regions.json")))["regions"]
