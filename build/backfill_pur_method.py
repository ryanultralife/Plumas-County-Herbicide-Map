#!/usr/bin/env python3
"""Fill applications.method from CDPR's aerial/ground field (AER_GND_IND).

Statewide PUR loads stored method as NULL. The raw year archives still have
the code (A aerial, G ground, F fumigation, C chemigation, O other), and the
Northern Sierra CPRA extract has the same column for 2024. This writes
canonical labels and updates only rows whose method is still null, so county
text values (Alameda) and USFS FACTS "Chemical" stay as they are.

  python build/backfill_pur_method.py                 # scan + write CSV + counts
  DBURL=... python build/backfill_pur_method.py --load
  DBURL=... python build/backfill_pur_method.py --refresh-map
"""
import csv, glob, os, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scraper"))
import lib

csv.field_size_limit(200_000_000)

OUT = os.environ.get("TEMP") or os.environ.get("TMP") or "/tmp"
OUT = os.path.join(OUT, "pur_method_backfill.csv")
PUR = os.path.join(ROOT, "data", "raw", "pur")
CPRA = os.path.join(ROOT, "data", "raw", "cpra", "dpr_data.csv")


def _emit(best, year, use_no, raw, conflicts):
    label = lib.applic_method(raw)
    if not label or not use_no:
        return
    key = (str(year), use_no.strip())
    prev = best.get(key)
    if prev is None:
        best[key] = label
    elif prev != label:
        conflicts[0] += 1


def scan_year(year):
    best = {}
    conflicts = [0]
    files = sorted(glob.glob(os.path.join(PUR, "pur" + year, "**", "udc*.txt"), recursive=True))
    if not files:
        print("no udc files for", year, flush=True)
        return best
    rows = 0
    for path in files:
        with open(path, encoding="latin-1", newline="") as f:
            r = csv.DictReader(f)
            if "aer_gnd_ind" not in (r.fieldnames or []):
                print("  skip (no aer_gnd_ind)", os.path.basename(path), flush=True)
                continue
            for row in r:
                rows += 1
                _emit(best, year, row.get("use_no") or "", row.get("aer_gnd_ind"), conflicts)
        print("  " + os.path.basename(path) + " unique=" + format(len(best), ","), flush=True)
    print(year, "ai-rows", format(rows, ","), "applications", format(len(best), ","),
          "code-conflicts", conflicts[0], flush=True)
    return best


def scan_cpra(years_done):
    """Years the statewide archives don't cover (2024 Northern Sierra)."""
    best = {}
    conflicts = [0]
    if not os.path.exists(CPRA):
        print("no CPRA extract", flush=True)
        return best
    rows = 0
    with open(CPRA, encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        fields = {k.lower(): k for k in (r.fieldnames or [])}
        yk, uk, mk = fields.get("year"), fields.get("use_no"), fields.get("aer_gnd_ind")
        if not (yk and uk and mk):
            print("CPRA extract has no AER_GND_IND", flush=True)
            return best
        for row in r:
            rows += 1
            year = (row.get(yk) or "").strip()
            if year in years_done:
                continue
            _emit(best, year, row.get(uk) or "", row.get(mk), conflicts)
    print("cpra ai-rows", format(rows, ","), "new-year applications", format(len(best), ","),
          "code-conflicts", conflicts[0], flush=True)
    return best


def open_csv():
    f = open(OUT, "w", encoding="utf-8", newline="")
    w = csv.writer(f)
    w.writerow(["app_id", "method"])
    return f, w, collections.Counter()


def append_csv(w, counts, best):
    n = 0
    for (year, use_no), label in best.items():
        w.writerow(["pur:" + year + ":" + use_no, label])
        counts[label] += 1
        n += 1
    return n


def dburl():
    url = os.environ.get("DBURL")
    if url:
        return url
    path = os.path.join(os.path.expanduser("~"), ".pg_dburl")
    raw = open(path, encoding="utf-8").read().strip()
    if raw.lower().startswith("export dburl="):
        raw = raw.split("=", 1)[1].strip().strip('"').strip("'")
    return raw


def run_sql(sql):
    import subprocess, tempfile
    sqlf = tempfile.NamedTemporaryFile("w", delete=False, suffix=".sql", encoding="utf-8")
    sqlf.write(sql)
    sqlf.close()
    try:
        r = subprocess.run(["psql", dburl(), "-v", "ON_ERROR_STOP=1", "-f", sqlf.name],
                           check=False)
        if r.returncode != 0:
            sys.exit(r.returncode)
    finally:
        os.remove(sqlf.name)


def run_sql_out(sql):
    import subprocess, tempfile
    sqlf = tempfile.NamedTemporaryFile("w", delete=False, suffix=".sql", encoding="utf-8")
    sqlf.write(sql)
    sqlf.close()
    try:
        r = subprocess.run(["psql", dburl(), "-v", "ON_ERROR_STOP=1", "-f", sqlf.name],
                           capture_output=True, text=True)
    finally:
        os.remove(sqlf.name)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        sys.exit(r.returncode)
    return r.stdout


def load():
    """Load in small primary-key batches. One 13M-row join was CPU-bound for
    far too long on this table; 25k index lookups per commit finishes."""
    path = OUT.replace("\\", "/")
    run_sql("""
set statement_timeout=0;
drop table if exists public._meth_load;
create table public._meth_load (app_id text primary key, method text);
\\copy public._meth_load (app_id, method) from '{path}' csv header
""".format(path=path))
    done = 0
    while True:
        out = run_sql_out("""
set statement_timeout=0;
with batch as (
  select app_id, method from public._meth_load limit 25000
), upd as (
  update public.applications a
     set method = b.method
    from batch b
   where a.app_id = b.app_id
     and a.method is null
)
delete from public._meth_load m
 using batch b
 where m.app_id = b.app_id;
""")
        n = 0
        for line in out.splitlines():
            if line.startswith("DELETE "):
                n = int(line.split()[1])
        if n <= 0:
            break
        done += n
        if done % 500000 < 25000:
            print("updated", format(done, ","), flush=True)
    run_sql("drop table if exists public._meth_load;")
    print("method backfill committed", format(done, ","), "rows", flush=True)


def refresh_map():
    src = os.path.join(ROOT, "supabase", "map_aggregate.sql")
    sql = open(src, encoding="utf-8").read()
    sql = sql.replace("public.map_agg", "public.map_agg_next")
    sql = sql.replace("map_agg_ll", "map_agg_next_ll")
    sql = "set statement_timeout=0;\n" + sql
    print("building map_agg_next (live map_agg stays up)...", flush=True)
    run_sql(sql)
    print("swapping map_agg_next -> map_agg", flush=True)
    run_sql("""
set statement_timeout=0;
begin;
drop materialized view public.map_agg;
alter materialized view public.map_agg_next rename to map_agg;
alter index public.map_agg_next_ll rename to map_agg_ll;
grant select on public.map_agg to anon;
commit;
select count(*) cells,
       count(*) filter (where meth ? 'aerial') aerial_cells,
       count(*) filter (where meth ? 'ground') ground_cells
  from public.map_agg;
""")


def main():
    if "--refresh-map" in sys.argv:
        refresh_map()
        return
    if "--load-only" in sys.argv:
        if not os.path.exists(OUT):
            sys.exit("missing " + OUT + " — run without --load-only first")
        load()
        try:
            os.remove(OUT)
        except OSError:
            pass
        print("loaded and removed", OUT, flush=True)
        return
    years = []
    for name in sorted(os.listdir(PUR)):
        if name.startswith("pur") and name[3:].isdigit():
            years.append(name[3:])
    out, w, counts = open_csv()
    n = 0
    try:
        for year in years:
            print("scanning", year, flush=True)
            best = scan_year(year)
            n += append_csv(w, counts, best)
            del best
        n += append_csv(w, counts, scan_cpra(set(years)))
    finally:
        out.close()
    print("wrote", format(n, ","), "rows ->", OUT, flush=True)
    for k, v in counts.most_common():
        print("  ", k, format(v, ","), flush=True)
    if n < 1000:
        sys.exit("too few method rows; refusing to load")
    if "--load" in sys.argv:
        load()
        try:
            os.remove(OUT)
        except OSError:
            pass
        print("loaded and removed", OUT, flush=True)


if __name__ == "__main__":
    main()
