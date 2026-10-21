#!/usr/bin/env python3
"""Normalize CV Water Board (R5) PRA response rcvd 2026-10-06:
 (a) CEDEN_export_PRA_633.xlsx  -> cvrwqcb-r5/ceden_plumas_results.csv, ceden_stations.csv, ceden_herbicide_results.csv
 (b) Dixie Fire ... DRAFT Results.xlsx (wide) -> cvrwqcb-r5/dixie_fire_DRAFT_results_long.csv, dixie_fire_DRAFT_stations.csv
Lab PDFs (Snake Lake / Gopher Hill, lead & mercury) are NOT parsed; inventoried in README only.
"""
import os, re, sys
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "build"))
from gen_edt_plumas import classify
IN = os.environ.get("SRC_DIR", "/workspace/spraymap-incoming/cvrwqcb-r5")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cvrwqcb-r5")
NONDETECT = {"ND"}            # CEDEN ResultQualCode: not detected
DETECT_EST = {"DNQ", "JF"}    # detected, not quantified / estimated
def ceden():
    c = pd.read_excel(os.path.join(IN, "CEDEN_export_PRA_633.xlsx"))
    c["SAMPLEDATE"] = pd.to_datetime(c.SAMPLEDATE).dt.date
    q = c.RESULTQUALCODE.fillna("").str.strip()
    c["detect_status"] = q.map(lambda x: "non-detect" if x in NONDETECT else "detect-estimated" if x in DETECT_EST
                               else "not-reported" if x == "NR" else "detect" if x in {"=", ">=", "<="} else "unknown")
    c["herbicide_key"] = c.ANALYTE.astype(str).map(lambda a: classify(a.split(",")[0]) or "")
    keep = ["PROGRAM","PARENTPROJECT","PROJECT","STATIONCODE","STATIONNAME","SAMPLEDATE","COLLECTIONTIME","MATRIXNAME",
            "SAMPLETYPECODE","METHODNAME","ANALYTE","FRACTIONNAME","UNIT","RESULT","RESULTQUALCODE","detect_status","MDL","RL",
            "QACODE","SAMPLEAGENCY","LABAGENCY","SUBMITTINGAGENCY","LATITUDE","LONGITUDE","COUNTY","herbicide_key"]
    keep = [k for k in keep if k in c.columns]
    c[keep].to_csv(os.path.join(OUT, "ceden_plumas_results.csv"), index=False)
    st = c.groupby(["STATIONCODE","STATIONNAME"]).agg(lat=("LATITUDE","first"), lon=("LONGITUDE","first"),
          results=("ANALYTE","size"), first=("SAMPLEDATE","min"), last=("SAMPLEDATE","max"),
          programs=("PROGRAM", lambda s: "; ".join(sorted(set(s))))).reset_index()
    st.to_csv(os.path.join(OUT, "ceden_stations.csv"), index=False)
    h = c[c.herbicide_key != ""][keep]; h.to_csv(os.path.join(OUT, "ceden_herbicide_results.csv"), index=False)
    print(f"CEDEN: {len(c)} rows, {len(st)} stations, {c.SAMPLEDATE.min()}..{c.SAMPLEDATE.max()}, counties {sorted(c.COUNTY.unique())}")
    print(" detect_status:", c.detect_status.value_counts().to_dict(), "| missing lat:", int(c.LATITUDE.isna().sum()))
    print(" herbicide/pesticide rows:"); print(h[["STATIONNAME","SAMPLEDATE","ANALYTE","RESULT","UNIT","RESULTQUALCODE","MDL","RL"]].to_string(index=False))
def dixie():
    p = os.path.join(IN, "Dixie Fire Water Quality Monitoring - DRAFT Results.xlsx")
    x = pd.read_excel(p, sheet_name="Dixie Fire WQ 2021-2022", header=None)
    dates = x.iloc[8, 11:].ffill(); locs = x.iloc[9, 11:]
    out, section = [], None
    for i in range(10, len(x)):
        a = x.iloc[i, 0]
        if pd.isna(a) or str(a).startswith(("Notes", "*")) or re.match(r"^\d\s|^J ", str(a)): 
            if str(a).startswith("Notes"): break
            continue
        if x.iloc[i, 1:].isna().all(): section = str(a).strip(); continue
        for j in range(11, x.shape[1]):
            v = x.iloc[i, j]
            if pd.isna(v) or str(v).strip() == "--": continue
            s = str(v).strip()
            m = re.match(r"^([<>]?)\s*([\d,\.]+)\s*(.*)$", s)
            num = float(m.group(2).replace(",", "")) if m else None
            flags = m.group(3).strip() if m else s
            out.append({"status": "DRAFT", "section": section, "analyte": str(a).strip(), "method": x.iloc[i,1],
                        "units": x.iloc[i,2], "fraction": x.iloc[i,3], "sample_date": pd.to_datetime(dates.iloc[j-11]).date(),
                        "station": locs.iloc[j-11], "result_raw": s, "qualifier": m.group(1) if m else "",
                        "value": num, "flags": flags,
                        "detect_status": "non-detect" if (m and m.group(1) == "<") else "detect-estimated" if "J" in flags.split(",") or flags.startswith("J") else "detect",
                        "herbicide_key": classify(str(a)) or ""})
    df = pd.DataFrame(out); df.to_csv(os.path.join(OUT, "dixie_fire_DRAFT_results_long.csv"), index=False)
    s = pd.read_excel(p, sheet_name="Sampling Locations"); s["status"] = "DRAFT"
    s.to_csv(os.path.join(OUT, "dixie_fire_DRAFT_stations.csv"), index=False)
    print(f"DIXIE (DRAFT): {len(df)} results, {df.analyte.nunique()} analytes, stations {sorted(df.station.unique())}, "
          f"{df.sample_date.min()}..{df.sample_date.max()}; detect_status {df.detect_status.value_counts().to_dict()}; herbicide rows {int((df.herbicide_key!='').sum())}")
if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True); ceden(); dixie()
