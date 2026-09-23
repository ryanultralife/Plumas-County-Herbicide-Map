#!/usr/bin/env python3
"""Summarize the State Water Board's drinking-water compliance results for Plumas County.

Input : data/incoming/2026-09/edt-plumas/plumas_sdwis_2019_2026.tsv
        (rows for water systems whose "Principal County Served" is PLUMAS or whose
         system number starts CA32, streamed out of the EDT Library files SDWIS3.zip
         2019-2022, SDWIS4.zip 2023-2025 and SDWIS5.zip 2026-to-date; the zips live
         under data/raw/edt/ and are git-ignored)
Output: data/incoming/2026-09/edt-plumas/summary.json  (committed; feeds the Science tab)

The question this answers, with the state's own records: do Plumas public water systems
get tested for the herbicides applied in their watersheds, and if so what came back.

Interpretation rules (from the EDT data dictionary):
  * "Less Than Reporting Level" = Y means the lab did not detect the analyte above its
    reporting level; the Result column is then blank or the level itself. Only rows with
    that flag = N and a numeric Result carry a real measured value.
  * DLR = the state Detection Limit for purposes of Reporting; MCL = maximum contaminant
    level where one exists.
"""
import csv, io, os, sys, json, collections, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "incoming", "2026-09", "edt-plumas", "plumas_sdwis_2019_2026.tsv")
OUT = os.path.join(ROOT, "data", "incoming", "2026-09", "edt-plumas", "summary.json")
csv.field_size_limit(200000000)

# Herbicides applied in the Plumas National Forest footprint (PUR + USFS project records),
# plus the common regulated herbicides a compliance panel might carry.
TARGET = {
    "glyphosate": ["GLYPHOSATE"],
    "AMPA": ["AMPA", "AMINOMETHYLPHOSPHONIC"],
    "hexazinone": ["HEXAZINONE"],
    "imazapyr": ["IMAZAPYR"],
    "aminopyralid": ["AMINOPYRALID"],
    "triclopyr": ["TRICLOPYR"],
    "clopyralid": ["CLOPYRALID"],
    "sulfometuron-methyl": ["SULFOMETURON"],
    "indaziflam": ["INDAZIFLAM"],
    "oxyfluorfen": ["OXYFLUORFEN"],
    "atrazine": ["ATRAZINE"],
    "simazine": ["SIMAZINE"],
    "2,4-D": ["2,4-D", "2,4 D", "2,4-DICHLOROPHENOXY"],
    "diuron": ["DIURON"],
    "bromacil": ["BROMACIL"],
    "picloram": ["PICLORAM"],
    "dicamba": ["DICAMBA"],
    "alachlor": ["ALACHLOR"],
    "metolachlor": ["METOLACHLOR"],
    "dalapon": ["DALAPON"],
    "dinoseb": ["DINOSEB"],
    "pentachlorophenol": ["PENTACHLOROPHENOL"],
    "bentazon": ["BENTAZON"],
    "molinate": ["MOLINATE"],
    "thiobencarb": ["THIOBENCARB"],
}
# The systems our water letters went to (State system numbers, county 32).
NAMED = {
    "CA3210009": "Chester PUD",
    "CA3210003": "City of Portola",
    "CA3210001": "Indian Valley CSD (Greenville)",
    "CA3210004": "American Valley CSD (Quincy)",
    "CA3210008": "East Quincy Services District",
    "CA3210005": "Graeagle Water Company",
    "CA3210006": "Lake Almanor Country Club MWC",
    "CA3210010": "Hamilton Branch CSD",
}


def to_f(v):
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def to_date(v):
    v = (v or "").strip()
    for fmt in ("%m-%d-%Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(v, fmt).date()
        except ValueError:
            pass
    return None


def classify(analyte):
    a = analyte.upper()
    for key, needles in TARGET.items():
        if any(n in a for n in needles):
            return key
    return None


def main():
    if not os.path.exists(SRC):
        sys.exit("missing " + SRC)
    rows = 0
    systems = {}
    analytes = collections.Counter()
    dates = []
    herb = collections.defaultdict(lambda: {"samples": 0, "systems": set(), "detections": [],
                                            "first": None, "last": None, "analyte_names": set(),
                                            "mcl": set(), "dlr": set()})
    per_system_herb = collections.defaultdict(lambda: collections.defaultdict(lambda: {"samples": 0, "last": None, "detections": 0}))
    with io.open(SRC, encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            rows += 1
            sysno = row["Water System Number"].strip()
            systems.setdefault(sysno, {"name": row["Water System Name"].strip(),
                                        "pop": to_f(row["Population Served"]),
                                        "samples": 0, "analytes": set()})
            systems[sysno]["samples"] += 1
            an = row["Analyte Name"].strip()
            systems[sysno]["analytes"].add(an)
            analytes[an] += 1
            d = to_date(row["Sample Date"])
            if d:
                dates.append(d)
            key = classify(an)
            if not key:
                continue
            h = herb[key]
            h["samples"] += 1
            h["systems"].add(sysno)
            h["analyte_names"].add(an)
            if row.get("MCL", "").strip():
                h["mcl"].add(row["MCL"].strip())
            if row.get("DLR", "").strip():
                h["dlr"].add(row["DLR"].strip())
            if d:
                h["first"] = d if h["first"] is None or d < h["first"] else h["first"]
                h["last"] = d if h["last"] is None or d > h["last"] else h["last"]
            ps = per_system_herb[sysno][key]
            ps["samples"] += 1
            if d and (ps["last"] is None or d > ps["last"]):
                ps["last"] = d
            lt = row.get("Less Than Reporting Level", "").strip().upper()
            res = to_f(row.get("Result"))
            if lt == "N" and res is not None and res > 0:
                ps["detections"] += 1
                h["detections"].append({"system": sysno, "system_name": systems[sysno]["name"],
                                         "date": d.isoformat() if d else None, "result": res,
                                         "units": row.get("Units of Measure", "").strip(),
                                         "mcl": row.get("MCL", "").strip(),
                                         "sampling_point": row.get("Sampling Point Name", "").strip()})

    def dser(x):
        return x.isoformat() if x else None

    out = {
        "generated": datetime.date.today().isoformat(),
        "source": ("State Water Resources Control Board, Division of Drinking Water - EDT Library "
                   "(SDWIS extracts SDWIS3 2019-2022, SDWIS4 2023-2025, SDWIS5 2026-present, "
                   "downloaded 2026-09-22), filtered to Plumas County systems"),
        "how_we_got_here": ("Our records request to DDW District 62 (PRA ID #638) was answered on "
                            "2026-09-17 by pointing to these public bulk files rather than producing "
                            "a county extract; we pulled and filtered them ourselves."),
        "rows": rows,
        "systems": len(systems),
        "date_range": [dser(min(dates)) if dates else None, dser(max(dates)) if dates else None],
        "distinct_analytes": len(analytes),
        "top_analytes": analytes.most_common(25),
        "herbicides": {},
        "herbicides_never_tested": [],
        "named_systems": {},
    }
    for key in TARGET:
        if key in herb:
            h = herb[key]
            out["herbicides"][key] = {
                "analyte_names": sorted(h["analyte_names"]),
                "samples": h["samples"],
                "systems_tested": len(h["systems"]),
                "first_sample": dser(h["first"]),
                "last_sample": dser(h["last"]),
                "detections_above_reporting_level": len(h["detections"]),
                "detections": sorted(h["detections"], key=lambda x: (x["date"] or ""))[:50],
                "mcl_values_seen": sorted(h["mcl"]),
                "dlr_values_seen": sorted(h["dlr"]),
            }
        else:
            out["herbicides_never_tested"].append(key)
    for sysno, label in NAMED.items():
        s = systems.get(sysno)
        out["named_systems"][sysno] = {
            "label": label,
            "in_records": bool(s),
            "system_name": s["name"] if s else None,
            "samples": s["samples"] if s else 0,
            "distinct_analytes": len(s["analytes"]) if s else 0,
            "herbicides": {k: {"samples": v["samples"], "last": dser(v["last"]), "detections": v["detections"]}
                           for k, v in per_system_herb.get(sysno, {}).items()},
        }
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("rows", rows, "| systems", len(systems), "| analytes", len(analytes),
          "| dates", out["date_range"])
    for k, v in out["herbicides"].items():
        print("  %-20s samples=%-6d systems=%-3d detections=%-3d last=%s" %
              (k, v["samples"], v["systems_tested"], v["detections_above_reporting_level"], v["last_sample"]))
    print("  never tested:", ", ".join(out["herbicides_never_tested"]))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
