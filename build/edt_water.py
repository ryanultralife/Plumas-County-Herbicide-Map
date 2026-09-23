#!/usr/bin/env python3
"""Drinking-water herbicide testing, county by county, from the State Water Board's EDT Library.

The Plumas pull (build/gen_edt_plumas.py) answered one question with the state's own
records: do the public water systems get tested for the herbicides applied in their
watersheds, and what came back. This runs the same question for any set of counties
in one pass over the bulk files.

Input : the EDT Library SDWIS zips (SDWIS3.zip 2019-2022, SDWIS4.zip 2023-2025,
        SDWIS5.zip 2026-to-date, or any other SDWIS*.zip) under data/raw/edt/
        (git-ignored; download from the Water Board's EDT Library page). Each zip holds
        tab-delimited result files with the same columns as the Plumas extract.
Output: data/water/<county-slug>.json  one summary per county (same shape as the Plumas
                                        summary, plus a per-system list)
        data/water/coverage.json        one line per county: systems, results, which
                                        herbicides were ever tested, detections

The SDWIS zips cover separate year ranges, so rows are not de-duplicated across them;
keep only one copy of each zip in data/raw/edt/.

A row belongs to a county when its "Principal County Served" is that county OR its
system number carries that county's code (CA32xxxxx = Plumas), the same rule the Plumas
pull used. A system serving across a county line can therefore count in both.

Usage:
  python build/edt_water.py --county Placer --county Nevada --county "El Dorado" --county Alpine
  python build/edt_water.py --all                     # all 58 counties
  python build/edt_water.py --all --since 2021-01-01  # limit the sample window
  python build/edt_water.py --county Placer --keep-rows  # also write the filtered rows (TSV)
"""
import argparse, collections, csv, datetime, glob, io, json, os, re, sys, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_edt_plumas import TARGET, classify, to_f, to_date   # one analyte list for every county

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "edt")
OUT = os.path.join(ROOT, "data", "water")
csv.field_size_limit(200000000)

# California county codes (alphabetical, 01-58) as used in water system numbers and PUR.
COUNTIES = ["Alameda", "Alpine", "Amador", "Butte", "Calaveras", "Colusa", "Contra Costa",
    "Del Norte", "El Dorado", "Fresno", "Glenn", "Humboldt", "Imperial", "Inyo", "Kern", "Kings",
    "Lake", "Lassen", "Los Angeles", "Madera", "Marin", "Mariposa", "Mendocino", "Merced", "Modoc",
    "Mono", "Monterey", "Napa", "Nevada", "Orange", "Placer", "Plumas", "Riverside", "Sacramento",
    "San Benito", "San Bernardino", "San Diego", "San Francisco", "San Joaquin", "San Luis Obispo",
    "San Mateo", "Santa Barbara", "Santa Clara", "Santa Cruz", "Shasta", "Sierra", "Siskiyou",
    "Solano", "Sonoma", "Stanislaus", "Sutter", "Tehama", "Trinity", "Tulare", "Tuolumne",
    "Ventura", "Yolo", "Yuba"]
CODE = {c: "%02d" % (i + 1) for i, c in enumerate(COUNTIES)}
BY_CODE = {v: k for k, v in CODE.items()}
BY_UPPER = {c.upper(): c for c in COUNTIES}


def slug(c):
    return re.sub(r"[^a-z0-9]+", "-", c.lower()).strip("-")


def county_of(row, wanted):
    """Every wanted county this row belongs to (principal county served, system-number code)."""
    hit = set()
    pc = BY_UPPER.get((row.get("Principal County Served") or "").strip().upper())
    if pc in wanted:
        hit.add(pc)
    m = re.match(r"CA(\d{2})", (row.get("Water System Number") or "").strip().upper())
    if m and BY_CODE.get(m.group(1)) in wanted:
        hit.add(BY_CODE[m.group(1)])
    return hit


def result_files(zpath):
    """Yield (name, text stream) for each tab-delimited result file in a zip."""
    with zipfile.ZipFile(zpath) as z:
        for info in z.infolist():
            if info.is_dir() or not re.search(r"\.(tab|txt|tsv|csv)$", info.filename, re.I):
                continue
            with z.open(info) as raw:
                yield info.filename, io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")


class County:
    def __init__(self, name):
        self.name = name
        self.rows = 0
        self.systems = {}
        self.analytes = collections.Counter()
        self.first = self.last = None
        self.herb = collections.defaultdict(lambda: {"samples": 0, "systems": set(), "detections": [],
                                                     "first": None, "last": None, "analyte_names": set(),
                                                     "mcl": set(), "dlr": set()})
        self.per_sys = collections.defaultdict(lambda: collections.defaultdict(
            lambda: {"samples": 0, "last": None, "detections": 0}))

    def add(self, row, d):
        self.rows += 1
        sysno = row["Water System Number"].strip()
        s = self.systems.setdefault(sysno, {"name": row["Water System Name"].strip(),
                                            "pop": to_f(row.get("Population Served")),
                                            "class": (row.get("Federal Water System Classification") or "").strip(),
                                            "status": (row.get("System Status") or "").strip(),
                                            "samples": 0, "analytes": set()})
        s["samples"] += 1
        an = row["Analyte Name"].strip()
        s["analytes"].add(an)
        self.analytes[an] += 1
        if d:
            self.first = d if self.first is None or d < self.first else self.first
            self.last = d if self.last is None or d > self.last else self.last
        key = classify(an)
        if not key:
            return
        h = self.herb[key]
        h["samples"] += 1
        h["systems"].add(sysno)
        h["analyte_names"].add(an)
        if (row.get("MCL") or "").strip():
            h["mcl"].add(row["MCL"].strip())
        if (row.get("DLR") or "").strip():
            h["dlr"].add(row["DLR"].strip())
        if d:
            h["first"] = d if h["first"] is None or d < h["first"] else h["first"]
            h["last"] = d if h["last"] is None or d > h["last"] else h["last"]
        ps = self.per_sys[sysno][key]
        ps["samples"] += 1
        if d and (ps["last"] is None or d > ps["last"]):
            ps["last"] = d
        # Only "Less Than Reporting Level" = N with a numeric result is a measured value.
        res = to_f(row.get("Result"))
        if (row.get("Less Than Reporting Level") or "").strip().upper() == "N" and res is not None and res > 0:
            ps["detections"] += 1
            h["detections"].append({"system": sysno, "system_name": s["name"],
                                    "date": d.isoformat() if d else None, "result": res,
                                    "units": (row.get("Units of Measure") or "").strip(),
                                    "mcl": (row.get("MCL") or "").strip(),
                                    "sampling_point": (row.get("Sampling Point Name") or "").strip()})

    def summary(self, source):
        ds = lambda x: x.isoformat() if x else None
        out = {
            "county": self.name, "county_code": CODE[self.name],
            "generated": datetime.date.today().isoformat(), "source": source,
            "rows": self.rows, "systems": len(self.systems),
            "date_range": [ds(self.first), ds(self.last)],
            "distinct_analytes": len(self.analytes), "top_analytes": self.analytes.most_common(25),
            "herbicides": {}, "herbicides_never_tested": [], "system_list": [],
        }
        for key in TARGET:
            h = self.herb.get(key)
            if not h:
                out["herbicides_never_tested"].append(key)
                continue
            out["herbicides"][key] = {
                "analyte_names": sorted(h["analyte_names"]), "samples": h["samples"],
                "systems_tested": len(h["systems"]), "first_sample": ds(h["first"]), "last_sample": ds(h["last"]),
                "detections_above_reporting_level": len(h["detections"]),
                "detections": sorted(h["detections"], key=lambda x: x["date"] or "")[:50],
                "mcl_values_seen": sorted(h["mcl"]), "dlr_values_seen": sorted(h["dlr"]),
            }
        for sysno, s in sorted(self.systems.items(), key=lambda kv: -(kv[1]["pop"] or 0)):
            out["system_list"].append({
                "id": sysno, "name": s["name"], "population": s["pop"], "class": s["class"], "status": s["status"],
                "samples": s["samples"], "distinct_analytes": len(s["analytes"]),
                "herbicides": {k: {"samples": v["samples"], "last": ds(v["last"]), "detections": v["detections"]}
                               for k, v in self.per_sys.get(sysno, {}).items()},
            })
        return out

    def coverage(self):
        tested = {k: v["samples"] for k, v in self.herb.items()}
        return {"county": self.name, "systems": len(self.systems), "results": self.rows,
                "date_range": [self.first.isoformat() if self.first else None,
                               self.last.isoformat() if self.last else None],
                "systems_with_any_herbicide_test": len({s for v in self.herb.values() for s in v["systems"]}),
                "herbicides_tested": dict(sorted(tested.items(), key=lambda kv: -kv[1])),
                "detections": sum(len(v["detections"]) for v in self.herb.values()),
                "file": "data/water/%s.json" % slug(self.name)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--county", action="append", default=[], help="county name; repeat for several")
    ap.add_argument("--all", action="store_true", help="all 58 counties")
    ap.add_argument("--since", help="only samples on/after this date (YYYY-MM-DD)")
    ap.add_argument("--raw", default=RAW, help="folder holding the SDWIS*.zip files (default data/raw/edt)")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--keep-rows", action="store_true", help="also write data/water/rows/<county>.tsv (large; git-ignored)")
    a = ap.parse_args()

    wanted = set(COUNTIES) if a.all else set()
    for c in a.county:
        name = BY_UPPER.get(c.strip().upper())
        if not name:
            ap.error("unknown county: %r" % c)
        wanted.add(name)
    if not wanted:
        ap.error("give --county (repeatable) or --all")
    since = datetime.date.fromisoformat(a.since) if a.since else None
    zips = sorted(glob.glob(os.path.join(a.raw, "SDWIS*.zip")))
    if not zips:
        sys.exit("no SDWIS*.zip under " + a.raw + " (download them from the EDT Library first)")

    acc = {c: County(c) for c in wanted}
    writers, handles = {}, []
    if a.keep_rows:
        os.makedirs(os.path.join(a.out, "rows"), exist_ok=True)
    total = 0
    for zp in zips:
        for fname, fh in result_files(zp):
            r = csv.DictReader(fh, delimiter="\t")
            if not r.fieldnames or "Water System Number" not in r.fieldnames or "Analyte Name" not in r.fieldnames:
                print("  skip (not a result file):", os.path.basename(zp), fname)
                continue
            n = 0
            for row in r:
                total += 1
                hit = county_of(row, wanted)
                if not hit:
                    continue
                d = to_date(row.get("Sample Date"))
                if since and (d is None or d < since):
                    continue
                n += 1
                for c in hit:
                    acc[c].add(row, d)
                    if a.keep_rows:
                        if c not in writers:
                            h = open(os.path.join(a.out, "rows", slug(c) + ".tsv"), "w", encoding="utf-8", newline="")
                            handles.append(h)
                            writers[c] = csv.DictWriter(h, fieldnames=r.fieldnames, delimiter="\t", extrasaction="ignore")
                            writers[c].writeheader()
                        writers[c].writerow(row)
            print("  %s/%s: %d rows kept" % (os.path.basename(zp), fname, n))
    for h in handles:
        h.close()

    source = ("State Water Resources Control Board, Division of Drinking Water - EDT Library SDWIS "
              "extracts (%s), pulled %s" % (", ".join(os.path.basename(z) for z in zips), datetime.date.today().isoformat()))
    os.makedirs(a.out, exist_ok=True)
    for c in sorted(acc):
        p = os.path.join(a.out, slug(c) + ".json")
        with open(p + ".tmp", "w", encoding="utf-8", newline="\n") as f:
            json.dump(acc[c].summary(source), f, indent=1, ensure_ascii=False)
        os.replace(p + ".tmp", p)

    # coverage.json keeps counties from earlier runs; this run replaces only the ones it pulled.
    cp = os.path.join(a.out, "coverage.json")
    cov = {"counties": {}}
    if os.path.exists(cp):
        with open(cp, encoding="utf-8") as f:
            cov = json.load(f)
    cov["about"] = ("Drinking-water compliance testing for the herbicides tracked on spraymapca.org, per county, "
                    "from the State Water Board EDT Library. Built by build/edt_water.py. A county with an empty "
                    "herbicides_tested map had no public-system result for any of them in the window pulled.")
    cov["tracked_herbicides"] = list(TARGET)
    cov["updated"] = datetime.date.today().isoformat()
    for c in acc:
        cov["counties"][c] = acc[c].coverage()
    cov["counties"] = dict(sorted(cov["counties"].items()))
    with open(cp + ".tmp", "w", encoding="utf-8", newline="\n") as f:
        json.dump(cov, f, indent=1, ensure_ascii=False)
    os.replace(cp + ".tmp", cp)

    print("scanned %d rows in %d zip(s)" % (total, len(zips)))
    for c in sorted(acc):
        v = acc[c].coverage()
        tested = ", ".join("%s %d" % kv for kv in v["herbicides_tested"].items()) or "none"
        print("  %-15s systems=%-4d results=%-8d herbicide tests: %s | detections=%d"
              % (c, v["systems"], v["results"], tested, v["detections"]))
    print("wrote", os.path.relpath(a.out, ROOT))


if __name__ == "__main__":
    main()
