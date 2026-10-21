"""Build data/water/ceden_plumas.json from the normalized CEDEN Plumas (CVRWQCB R5 PRA, rec'd 2026-10-06) CSVs
in data/incoming/2026-10/cvrwqcb-r5/. Dixie Fire results are labelled DRAFT by the Board and flagged draft here."""
import csv, json, os
from collections import Counter, defaultdict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data/incoming/2026-10/cvrwqcb-r5")
OUT = os.path.join(ROOT, "data/water/ceden_plumas.json")
rd = lambda f: list(csv.DictReader(open(os.path.join(D, f), encoding="utf-8")))
res, st, herb = rd("ceden_plumas_results.csv"), rd("ceden_stations.csv"), rd("ceden_herbicide_results.csv")
dx, dxs = rd("dixie_fire_DRAFT_results_long.csv"), rd("dixie_fire_DRAFT_stations.csv")
# QA notes not carried in the normalized CSV; source: data/water/ceden_pra633_benner_qa.csv (verbatim extract of
# CEDEN_export_PRA_633.xlsx LABBATCH/BATCHCOMMENTS). Asserted against that CSV below so the flag stays checkable.
QA_NOTES = {("518BENNER", "2022-10-03", "hexazinone"): {"qa_flag": 'QA-flagged: the lab batch\'s spike-recovery checks (matrix spike/duplicate and lab control sample, CEDEN batch comment "QAO: MS/MSD and LCS %R out") were out of range, so this trace is low-confidence',
    "lab_batch": "NCL_SPI_41918_W_PEST", "batch_comment": "QAO: MS/MSD and LCS %R out"}}
_qa = [r for r in csv.reader(open(os.path.join(ROOT, "data/water/ceden_pra633_benner_qa.csv"), encoding="utf-8")) if r and not r[0].startswith("#")]
_qa = [dict(zip(_qa[0], r)) for r in _qa[1:]]
for (_sc, _dt, _k), _n in QA_NOTES.items():
    assert any(r["STATIONCODE"] == _sc and r["SAMPLEDATE"].startswith(_dt) and r["LABBATCH"] == _n["lab_batch"]
               and r["BATCHCOMMENTS"] == _n["batch_comment"] for r in _qa), (_sc, _dt, _k)
    _n["qa_source"] = "data/water/ceden_pra633_benner_qa.csv"
hs = defaultdict(list)
for h in herb:
    hs[h["STATIONCODE"]].append({"date": h["SAMPLEDATE"], "analyte": h["ANALYTE"], "key": h["herbicide_key"],
        "result": float(h["RESULT"]) if h["RESULT"] else None, "qual": h["RESULTQUALCODE"], "detect_status": h["detect_status"],
        **QA_NOTES.get((h["STATIONCODE"], h["SAMPLEDATE"], h["herbicide_key"]), {}),
        "mdl": h["MDL"] or None, "rl": h["RL"] or None, "unit": h["UNIT"], "program": h["PROGRAM"]})
stations = [{"code": s["STATIONCODE"], "name": s["STATIONNAME"], "lat": float(s["lat"]), "lon": float(s["lon"]),
             "results": int(s["results"]), "first": s["first"], "last": s["last"], "programs": s["programs"],
             "herbicide_tested": s["STATIONCODE"] in hs, "herbicide_results": hs.get(s["STATIONCODE"], []), "draft": False}
            for s in st]
dcount = Counter(r["station"] for r in dx)
for s in dxs:
    stations.append({"code": s["Sample Location"], "name": s["Location Description"], "lat": float(s["Lat"]), "lon": float(s["Long"]),
                     "results": dcount[s["Sample Location"]], "programs": "CVRWQCB Dixie Fire WQ Monitoring (DRAFT)",
                     "herbicide_tested": False, "herbicide_results": [], "draft": True})
dates = sorted(r["SAMPLEDATE"] for r in res)
out = {"source": "Central Valley Regional Water Quality Control Board (R5) PRA response, CEDEN export (Plumas, 2018-01-01..2026-09-16)",
       "received": "2026-10-06", "confidence": "HIGH (CEDEN); MEDIUM for Dixie Fire (Board-labelled DRAFT)",
       "summary": {"results": len(res), "stations": len(st), "date_range": [dates[0], dates[-1]],
                   "detect_status": dict(Counter(r["detect_status"] for r in res)),
                   "herbicide_results": len(herb), "herbicide_sampling_events": len({(h["STATIONCODE"], h["SAMPLEDATE"]) for h in herb}),
                   "herbicide_detects": sum(h["detect_status"] != "non-detect" for h in herb),
                   "never_tested": ["triclopyr", "2,4-D"],
                   "dixie_draft": {"draft": True, "results": len(dx), "herbicide_results": sum(bool(r["herbicide_key"]) for r in dx)}},
       "stations": stations}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w"), indent=1); print(OUT, out["summary"])
