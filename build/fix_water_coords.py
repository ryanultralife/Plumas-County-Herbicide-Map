#!/usr/bin/env python3
"""Water-safe, section-faithful coordinates for the statewide PUR points.

THE RULE: a dot must never leave its reported ~1-sq-mi PLSS section. California
publishes pesticide use only to the section, so the dot marks that square mile:
 - normally at the section CENTER (scraper/lib.py comtrs_centroid, cos(point-lat));
 - if the center renders in a lake/reservoir, at the farthest-inland point of the
   SAME section's land portion (ST_MaximumInscribedCircle of section minus water)
   so it sits on land without migrating to some other shoreline;
 - if the whole section is water (historic lakebeds: Tule Lake sumps, receded
   Salton Sea), it stays at the center — the "water" there is stale hydrography
   and the farming is real.
This supersedes an earlier snap-to-nearest-shore approach, which wrongly walked
dots OUT of their sections (e.g. Collins Pine forestry onto the Lake Almanor
peninsula). Popups display the coordinate + a resolution disclaimer.

Requires: DBURL env; PostGIS enabled. Downloads PUR archives per year if missing
(https://files.cdpr.ca.gov/pub/outgoing/pur_archives/, ~170-190MB each) and
deletes each after staging — disk-safe on a nearly-full drive. Loads NHD
waterbodies (lakes+reservoirs >=0.5 km2, CA bbox) into _water if absent.
Idempotent: safe to re-run end to end.
"""
import sys, os, io, csv, json, zipfile, subprocess, tempfile, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scraper"))
import lib   # comtrs_centroid (fixed cos(point-lat))

csv.field_size_limit(100_000_000)
RAW = os.environ.get("PUR_RAW", r"C:/Users/ryanv/pur_rescrape")
YEARS = [2020, 2021, 2022]
ARCHIVE = "https://files.cdpr.ca.gov/pub/outgoing/pur_archives/pur{y}.zip"
DBURL = os.environ.get("DBURL") or sys.exit("Set DBURL")
NHD = ("https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/12/query"
       "?where=FTYPE+IN+(390,436)+AND+AREASQKM%3E%3D0.5"
       "&geometry=-124.5,32.5,-114.1,42.0&geometryType=esriGeometryEnvelope&inSR=4326"
       "&spatialRel=esriSpatialRelIntersects&outFields=OBJECTID,GNIS_NAME,FTYPE,AREASQKM"
       "&returnGeometry=true&outSR=4326&orderByFields=OBJECTID&resultRecordCount=250&f=geojson")


def psql(*sqls):
    cmd = ["psql", DBURL, "-v", "ON_ERROR_STOP=1"]
    for s in sqls:
        cmd += ["-c", s]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout.strip()[-1500:], flush=True)
    if r.returncode != 0:
        sys.exit(r.stderr.strip()[-1500:])
    return r.stdout


def ensure_water():
    have = subprocess.run(["psql", DBURL, "-tAc", "select to_regclass('public._water') is not null"],
                          capture_output=True, text=True).stdout.strip()
    if have == "t":
        print("[water] _water present"); return
    print("[water] fetching NHD lake/reservoir polygons")
    rows, seen = [], set()
    for off in (0, 250, 500, 750):
        d = json.loads(urllib.request.urlopen(NHD + f"&resultOffset={off}", timeout=180).read())
        for f in d.get("features", []):
            gid = (f.get("properties") or {}).get("OBJECTID") or f.get("id")
            if gid in seen or not f.get("geometry"):
                continue
            seen.add(gid)
            p = f["properties"]
            rows.append([gid, p.get("GNIS_NAME") or "", p.get("AREASQKM") or 0, json.dumps(f["geometry"])])
    tmp = tempfile.NamedTemporaryFile("w", delete=False, newline="", suffix=".csv", encoding="utf-8")
    csv.writer(tmp, lineterminator="\n").writerows(rows); tmp.close()
    psql("drop table if exists _water_raw; create unlogged table _water_raw(gid int, name text, area float8, gj text);")
    subprocess.run(["psql", DBURL, "-v", "ON_ERROR_STOP=1",
                    "-c", f"\\copy _water_raw(gid,name,area,gj) from '{tmp.name.replace(os.sep, '/')}' csv"],
                   check=True, capture_output=True, text=True)
    psql("set statement_timeout=0;"
         "drop table if exists _water cascade;"
         "create table _water as select gid,name,area,"
         " ST_Multi(ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(gj),4326))) geom from _water_raw;"
         "create index _water_gix on _water using gist(geom); analyze _water; drop table _water_raw;")
    os.unlink(tmp.name)
    print(f"[water] loaded {len(rows)} polygons")


def stage_centroids():
    """Per-year to survive a nearly-full disk: download if missing -> derive CSV ->
    \\copy append into _cc -> delete CSV -> delete zip."""
    os.makedirs(RAW, exist_ok=True)
    psql("drop table if exists _cc; create unlogged table _cc(app_id text, lat float8, lon float8);")
    for year in YEARS:
        zp = os.path.join(RAW, f"pur{year}.zip")
        if not os.path.exists(zp):
            print(f"[{year}] downloading archive", flush=True)
            urllib.request.urlretrieve(ARCHIVE.format(y=year), zp)
        out = os.path.join(RAW, f"cc_{year}.csv")
        n = 0
        with open(out, "w", newline="", encoding="utf-8") as o, zipfile.ZipFile(zp) as z:
            w = csv.writer(o, lineterminator="\n")
            for name in z.namelist():
                bn = name.split("/")[-1].lower()
                if not (bn.startswith(("udc", "pur")) and bn.endswith(".txt")):
                    continue
                with z.open(name) as raw:
                    for row in csv.DictReader(io.TextIOWrapper(raw, encoding="latin-1")):
                        row = {k.lower(): v for k, v in row.items()}
                        use_no = row.get("use_no") or row.get("record_id")
                        if not use_no:
                            continue
                        lat, lon = lib.comtrs_centroid(
                            row.get("base_ln_mer") or row.get("baseline_meridian"),
                            row.get("township"), row.get("tship_dir") or row.get("township_dir"),
                            row.get("range"), row.get("range_dir"), row.get("section"))
                        if lat is None:
                            continue
                        w.writerow([f"pur:{year}:{use_no}", lat, lon]); n += 1
        subprocess.run(["psql", DBURL, "-v", "ON_ERROR_STOP=1",
                        "-c", f"\\copy _cc(app_id,lat,lon) from '{out.replace(os.sep, '/')}' csv"],
                       check=True, capture_output=True, text=True)
        os.unlink(out); os.unlink(zp)
        print(f"[{year}] staged {n:,} centroids (zip+csv removed)", flush=True)
    psql("set statement_timeout=0; create index _cc_id on _cc(app_id); analyze _cc;")


PHASE_A = """
set statement_timeout=0;
-- restore every geocoded PUR row to its exact section centroid (undoes any prior snap)
update public.applications a set lat=c.lat, lon=c.lon
from _cc c
where a.app_id=c.app_id and a.source='pur' and a.lat is not null
  and (a.lat is distinct from c.lat or a.lon is distinct from c.lon);
"""

PHASE_B = """
set statement_timeout=0;
drop table if exists _fix;
create table _fix as
with cent as (               -- distinct section centers whose MAP position (3-dec cell) is in water
  select distinct c.lat, c.lon from _cc c
  where exists (select 1 from _water w where ST_Contains(w.geom,
        ST_SetSRID(ST_MakePoint(round(c.lon::numeric,3)::float8, round(c.lat::numeric,3)::float8),4326)))
), box as (
  select lat, lon,
    ST_MakeEnvelope(lon-1.0/(138.34*cos(radians(lat))), lat-0.0072464,
                    lon+1.0/(138.34*cos(radians(lat))), lat+0.0072464, 4326) env
  from cent
), land as (
  select b.lat, b.lon,
    ST_Difference(b.env, coalesce(
      (select ST_Union(w.geom) from _water w where ST_Intersects(w.geom, b.env)),
      ST_GeomFromText('POLYGON EMPTY',4326))) g
  from box b
)
select lat old_lat, lon old_lon,
  case when ST_IsEmpty(g) then lat
       else round(ST_Y((ST_MaximumInscribedCircle(g)).center)::numeric,5)::float8 end new_lat,
  case when ST_IsEmpty(g) then lon
       else round(ST_X((ST_MaximumInscribedCircle(g)).center)::numeric,5)::float8 end new_lon,
  ST_IsEmpty(g) fully_water
from land;
-- apply within-section land placement (exact-equality join: values share the same source doubles)
update public.applications a set lat=f.new_lat, lon=f.new_lon
from _fix f
where a.source='pur' and a.lat=f.old_lat and a.lon=f.old_lon and not f.fully_water;
select count(*) sections_touching_water, count(*) filter (where fully_water) fully_water_kept_at_center from _fix;
"""

VERIFY = """
set statement_timeout=0;
refresh materialized view concurrently public.map_agg;
select count(*) cells_in_water_excl_fullywater, coalesce(sum(m.n),0) apps
from public.map_agg m
where exists (select 1 from _water w where ST_Contains(w.geom, ST_SetSRID(ST_MakePoint(m.lon,m.lat),4326)))
  and not exists (select 1 from _fix f where f.fully_water
                  and round(f.old_lat::numeric,3)::float8=m.lat and round(f.old_lon::numeric,3)::float8=m.lon);
"""


def main():
    ensure_water()
    stage_centroids()
    print("[A] restoring section centroids", flush=True); psql(PHASE_A)
    print("[B] within-section land placement", flush=True); psql(PHASE_B)
    print("[verify] refresh map_agg + water check", flush=True); psql(VERIFY)
    psql("drop table if exists _cc; drop table if exists _snap; drop table if exists _pts;"
         "drop table if exists _water_test; drop table if exists _ncb; drop table if exists _nc;")
    print("done", flush=True)


if __name__ == "__main__":
    main()
