#!/usr/bin/env python3
"""Inventory the Central Valley Water Board (Region 5) PRA #633 FTP posting (2026-10-07) and write the
public, derived outputs. The raw files are NOT in git (held off-repo; sha256 in
data/incoming/2026-10/cvrwqcb-r5/MANIFEST.md). Run against the held copy:

  SRC_DIR=/path/to/ftp-2026-10-07 python build/gen_r5_ftp_records.py

Text comes from pdftotext (poppler) and, for the 3 scanned PDFs, tesseract OCR; spreadsheets via openpyxl.
Writes:
  data/incoming/2026-10/cvrwqcb-r5/ftp_inventory.csv   one row per file (94): type, facility, period,
                                                       parameters found, pesticide terms found
  data/water/r5_wdr_facilities.json                    the map layer (2 permitted facilities + 2 unplaced NPS sites)
No pounds, acres or application records exist in these files, so nothing here touches map_agg.
"""
import csv, hashlib, json, os, re, subprocess, sys, tempfile, glob
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.environ.get("SRC_DIR") or sys.exit("set SRC_DIR to the held ftp-2026-10-07 folder")
INV = os.path.join(ROOT, "data/incoming/2026-10/cvrwqcb-r5/ftp_inventory.csv")
OUT = os.path.join(ROOT, "data/water/r5_wdr_facilities.json")
MANIFEST = os.path.join(ROOT, "data/incoming/2026-10/cvrwqcb-r5/MANIFEST.md")
# One file name carries a possible private surname; MANIFEST.md lists it under a placeholder. Match it by hash so the
# name never appears in the repo.
REDACT_SHA = {"18b02c88a74c3c4ba74b0340f958eee5201c9f09ea13aa965caf42a49e8aa56d": "WDR/Whitehawk Ranch/2019/<redacted-private-name>/file-1.pdf"}

# Pesticide / herbicide vocabulary searched in every file's text (case-insensitive).
PEST = ["herbicid", "pesticid", "glyphosat", "roundup", "triclopyr", "2,4-d", "imazapyr", "hexazinon", "aminopyralid",
        "clopyralid", "sulfometuron", "chlorsulfuron", "atrazin", "simazin", "diuron", "paraquat", "algaecid",
        "copper sulfate", "insecticid", "fungicid", "rodenticid", "weed control", "spray"]
# Monitoring parameters, matched by keyword in the text (what each report measures).
PARAMS = [("flow", r"\bflow"), ("BOD", r"(?-i:\bBOD\b)"), ("suspended solids", r"suspend|\bTSS\b"),
    ("settleable solids", r"settleable"), ("total dissolved solids", r"dissolved solids|\bTDS\b"),
    ("total nitrogen", r"total nitrogen"), ("nitrate", r"nitrate"), ("chloride", r"chloride"), ("sodium", r"\bsodium"),
    ("pH", r"(?-i:\bpH\b)"), ("turbidity", r"turbidity|\bNTU\b"), ("chlorine residual", r"cl2|chlorine"),
    ("coliform bacteria", r"coliform"), ("E. coli", r"e\.\s?coli"), ("enterococci", r"enterococ"),
    ("specific conductance", r"conductance|conductivity"), ("dissolved oxygen", r"dissolved oxygen|oxygen, dissolved"),
    ("water temperature", r"temperature"), ("groundwater elevation / depth", r"groundwater elevation|depth to (ground)?water"),
    ("rainfall", r"rainfall"), ("sludge hauling", r"sludge"), ("arsenic", r"arsenic"), ("copper", r"\bcopper"),
    ("lead", r"\blead\b"), ("zinc", r"\bzinc"), ("antimony", r"antimony"), ("mercury", r"mercury"),
    ("hardness", r"hardness"), ("calcium", r"calcium"), ("magnesium", r"magnesium")]
# Scanned PDFs (no text layer) -> OCR. Keyed by sha256.
OCR = {"e51fe9c196d372b6e5862918081b6e3e70da7cd3fdb74c29ce19f963cbf73a1a", "a2e61611e8a38f8f2c71af262202e5dc42eb7f13266b6b33b6169faf836551d5",
       "18b02c88a74c3c4ba74b0340f958eee5201c9f09ea13aa965caf42a49e8aa56d"}

def text_of(rel, h):
    p = os.path.join(SRC, rel); ext = rel.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        if h in OCR:
            with tempfile.TemporaryDirectory() as td:
                subprocess.run(["pdftoppm", "-r", "200", "-gray", p, os.path.join(td, "p")], check=True)
                return "\n".join(subprocess.run(["tesseract", f, "-"], capture_output=True, text=True).stdout
                                 for f in sorted(glob.glob(os.path.join(td, "p*"))))
        return subprocess.run(["pdftotext", "-layout", p, "-"], capture_output=True, text=True).stdout
    if ext == "xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(p, data_only=True, read_only=True)
        return "\n".join(" | ".join(str(v) for v in r if v is not None) for ws in wb.worksheets for r in ws.iter_rows(values_only=True))
    if ext == "docx":
        return subprocess.run(["pandoc", p, "-t", "plain"], capture_output=True, text=True).stdout
    return ""

def pages(rel):
    if not rel.lower().endswith(".pdf"): return ""
    o = subprocess.run(["pdfinfo", os.path.join(SRC, rel)], capture_output=True, text=True).stdout
    m = re.search(r"Pages:\s+(\d+)", o); return m.group(1) if m else ""

def classify(rel):
    f = rel.split("/")[-1]; low = f.lower()
    if rel.startswith("NPS/"):
        fac = "Snake Lake Shooting Range" if "snakelake" in low else "Gopher Hill" if "gopher" in low else \
              "Dixie Fire stations DF-1..3" if "dixie" in low else "CEDEN (all Plumas stations)" if "ceden" in low else ""
        kind = ("lab report (metals, water)" if low.endswith(".pdf") else "CEDEN export (all Plumas results 2018-2026)" if "export" in low
                else "CEDEN query screenshot" if low.endswith(".png") else "CEDEN query instructions" if low.endswith(".docx")
                else "DRAFT results workbook" if "dixie" in low else "Windows thumbnail cache (not a record)")
        return "NPS", fac, kind
    fac = "Plumas Eureka CSD WWTP #6/#7" if "/Plumas Eureka/" in rel else "Whitehawk Ranch WWTP"
    kind = ("groundwater monitoring report" if "gw monitoring" in low or "groundwater" in low else
            "annual report" if "annual" in low or "jan 2026" in low else
            "quarterly monitoring report" if re.search(r"quarter|quatertly|\bq\d\b", low) else
            "monthly monitoring report" if "month" in low or "bundled" in low else "monitoring report")
    return "WDR", fac, kind

def period(rel):
    f = rel.split("/")[-1]
    q = re.search(r"\(Q(\d)\)|Q(\d) (\d{4})|Quarter\s+(\d)|First|Second|Third|Q(\d)-", f, re.I)
    y = re.findall(r"(20\d\d)", rel)
    yr = y[-1] if y else ""
    if "/Whitehawk Ranch/" in rel: yr = rel.split("/")[2]
    if q:
        n = next((g for g in q.groups() if g), None) or {"first": "1", "second": "2", "third": "3"}.get(q.group(0).lower(), "")
        return f"{yr} Q{n}"
    mo = re.search(r"(Jan|June|July)", f)
    return f"{yr} {mo.group(1)}" if mo else yr

def main():
    want = {}
    for line in open(MANIFEST, encoding="utf-8"):
        m = re.match(r"\| `(.+?)` \| (\d+) \| `([0-9a-f]{64})` \|", line)
        if m: want[m.group(1)] = (int(m.group(2)), m.group(3))
    files = sorted(os.path.relpath(p, SRC) for p in glob.glob(os.path.join(SRC, "**", "*"), recursive=True)
                   if os.path.isfile(p) and not p.endswith((".txt", ".md")))
    rows, seen = [], {}
    for rel in files:
        h = hashlib.sha256(open(os.path.join(SRC, rel), "rb").read()).hexdigest()
        pub = REDACT_SHA.get(h, rel)
        assert pub in want and want[pub][1] == h, ("not in MANIFEST / hash mismatch", pub)
        txt = text_of(rel, h); low = txt.lower()
        unit, fac, kind = classify(rel)
        pest = sorted({t for t in PEST if t in low})
        prm = [n for n, rx in PARAMS if re.search(rx, txt, re.I)]
        rows.append({"path": pub, "bytes": os.path.getsize(os.path.join(SRC, rel)), "sha256": h, "unit": unit,
                     "file_type": rel.rsplit(".", 1)[-1].lower(), "pages": pages(rel), "facility": fac, "doc_kind": kind,
                     "period": period(rel) if unit == "WDR" else "", "text_chars": len(txt),
                     "text_method": "OCR (tesseract)" if h in OCR else ("pdftotext" if rel.endswith(".pdf") else "parsed" if txt else "none"),
                     "parameters_found": "; ".join(prm), "pesticide_terms_found": "; ".join(pest),
                     "duplicate_of": seen.get(h, "")})
        seen.setdefault(h, pub)
    assert len(rows) == 94 and sum(r["bytes"] for r in rows) == 42693978, (len(rows), sum(r["bytes"] for r in rows))
    with open(INV + ".tmp", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    os.replace(INV + ".tmp", INV)

    def fac_summary(name):
        rr = [r for r in rows if r["facility"] == name]
        pp = Counter(p for r in rr for p in r["parameters_found"].split("; ") if p)
        yrs = sorted({r["period"][:4] for r in rr if r["period"][:4].isdigit()})
        return {"files": len(rr), "unique_files": sum(1 for r in rr if not r["duplicate_of"]),
                "doc_kinds": dict(Counter(r["doc_kind"] for r in rr)), "years": [yrs[0], yrs[-1]] if yrs else None,
                "parameters": [p for p, _ in pp.most_common()],
                "pesticide_terms_found": sorted({t for r in rr for t in r["pesticide_terms_found"].split("; ") if t})}
    out = {
        "generated": "2026-11-19",
        "source": "Central Valley Regional Water Quality Control Board (Region 5), PRA #633 production posted to the Water Board FTP 2026-10-07 "
                  "(downloaded 2026-10-21; agency confirmed complete 2026-10-26). Raw files held off-repo; sha256 in "
                  "data/incoming/2026-10/cvrwqcb-r5/MANIFEST.md; per-file inventory in ftp_inventory.csv.",
        "finding": "None of the 94 files contains a pesticide or herbicide result, application record, pounds or acres, apart from the "
                   "CEDEN export (already on the site: Benner Creek 2022 and two paraquat non-detects in 2021). The WDR files are "
                   "small-wastewater-plant monitoring reports; the two NPS lab reports are metals tests.",
        "confidence": "HIGH for contents (read from the Board's own files); MEDIUM for facility points (PLSS section centroids from the "
                      "Board's Notice of Applicability legal description, not surveyed plant locations)",
        "facilities": [
            {"id": "5A320104004", "name": "Plumas Eureka Community Services District wastewater treatment plants #6 and #7",
             "short": "Plumas Eureka CSD WWTP #6/#7", "near": "Blairsden / Graeagle, Poplar Valley Road",
             "related": "Separate record: Plumas Eureka CSD's drinking-water system is where the county's only glyphosate tests were run (14, all below the reporting level; Public water systems layer).",
             "order": "General Order 2014-0153-DWQ-R5332 (small domestic wastewater systems); previously WDRs Order 98-007",
             "discharge": "Treated domestic wastewater to leachfields (community leachfield 'Dynamite Hill' plus two backup leachfields); drainage to the Feather River",
             "lat": 39.7922, "lon": -120.6459,
             "geom": "plss_section_centroid_mean",
             "geom_note": "Mean of the BLM CadNSDI centroids of Sections 4, 5, 8 and 9, T22N R12E MDB&M, the sections the Board's 2020 Notice of Applicability names "
                          "for the plants and leachfields (the notice prints the range as 'R12W'; Plumas County lies east of the Mount Diablo meridian, so R12E). "
                          "Approximate to about half a mile.",
             "noa_url": "https://www.waterboards.ca.gov/centralvalley/board_decisions/adopted_orders/general_orders/2014-0153-dwq_noas/2014-0153-dwq-r5332.pdf",
             "records": fac_summary("Plumas Eureka CSD WWTP #6/#7")},
            {"id": "5A321018001", "name": "Whitehawk Ranch Mutual Water Company wastewater treatment and disposal system",
             "short": "Whitehawk Ranch WWTP", "near": "Clio",
             "order": "General Order 2014-0153-DWQ-R5194 (small domestic wastewater systems, notice of 2015-12-09); previously WDRs Order 92-127",
             "discharge": "Treated domestic wastewater to subsurface disposal and a land-application area; surface-water checks on Sulphur Creek up- and downstream",
             "lat": 39.7245, "lon": -120.5600,
             "geom": "plss_section_centroid",
             "geom_note": "BLM CadNSDI centroid of Section 31, T22N R13E MDB&M, the section the Board's 2015 Notice of Applicability names. Approximate to about half a mile.",
             "noa_url": "https://www.waterboards.ca.gov/centralvalley/board_decisions/adopted_orders/general_orders/2014-0153-dwq_noas/2014-0153-dwq-r5194.pdf",
             "records": fac_summary("Whitehawk Ranch WWTP")}],
        "unlocated": [
            {"name": "Snake Lake Shooting Range", "records": fac_summary("Snake Lake Shooting Range"),
             "sampled": "2024-03-26", "note": "Board Redding Branch water samples WC-1, WC-2 (Babcock Laboratories): arsenic, copper, lead, antimony, zinc, total and dissolved. No pesticide analytes. Not placed: the report gives no coordinates."},
            {"name": "Gopher Hill", "records": fac_summary("Gopher Hill"),
             "sampled": "2024-05-29", "note": "Board Redding Branch water samples WC-1, WC-2, SP-1..3 (Babcock Laboratories, amended 2024-08-15; mercury by EPA 1631E): metals and hardness. No pesticide analytes. Not placed: the report gives no coordinates."}],
        "counts": {"files": len(rows), "bytes": sum(r["bytes"] for r in rows), "by_unit": dict(Counter(r["unit"] for r in rows)),
                   "by_type": dict(Counter(r["file_type"] for r in rows)), "duplicates": sum(1 for r in rows if r["duplicate_of"]),
                   "files_with_pesticide_terms": sorted(r["path"] for r in rows if r["pesticide_terms_found"])},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT + ".tmp", "w", encoding="utf-8") as fh: json.dump(out, fh, indent=1)
    os.replace(OUT + ".tmp", OUT)
    print(json.dumps(out["counts"]), file=sys.stderr)

if __name__ == "__main__":
    main()
