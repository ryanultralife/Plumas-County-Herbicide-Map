#!/usr/bin/env python3
"""
Build small, map-ready static files from the big applications DB (Supabase export
or the local SQLite). One pass via SQL GROUP BY -> data/agg/:
  aggregated.geojson  - one point per ~section centroid, with n/lbs/gal/acres and
                        sparse by-class / by-year / by-land breakdowns + top AIs
  summary.json        - headline totals (by class/year/land/region/source)
  scores.json         - per-jurisdiction DATA-TRANSPARENCY / COVERAGE score

Usage:  python build/aggregate.py [DB_PATH] [OUT_DIR]
Reads the DB read-only. Default DB = the backup copy; default out = repo data/agg.
"""
import sqlite3, json, os, sys, collections, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB   = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\ryanv\plumas_db_backup\applications.sqlite"
OUT  = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "data", "agg")
PREC = 3   # ~110 m; merges identical section centroids

# ---- chemical class from active-ingredient name (curated top AIs + keyword fallback) ----
def chem_class(ai):
    s = (ai or "").upper()
    if not s: return "unknown"
    def has(*xs): return any(x in s for x in xs)
    if has("GLYPHOSATE","GLUFOSINATE","OXYFLUORFEN","PENDIMETHALIN","INDAZIFLAM","RIMSULFURON",
           "SAFLUFENACIL","CLETHODIM","SETHOXYDIM","CARFENTRAZONE","PYRAFLUFEN","TRIFLURALIN",
           "PARAQUAT","DIURON","2,4-D","DICAMBA","ATRAZINE","SIMAZINE","METOLACHLOR","FLUMIOXAZIN",
           "HALOSULFURON","IMAZAPYR","IMAZAMOX","TRICLOPYR","CLOPYRALID","AMINOPYRALID","HEXAZINONE",
           "NORFLURAZON","PROMETON","BROMACIL","FLAZASULFURON","SULFOMETURON","NAPROPAMIDE",
           "OXYFLUORFEN","METRIBUZIN","LINURON","PRODIAMINE","ISOXABEN","MESOTRIONE","TOPRAMEZONE",
           "FLUROXYPYR","MCPA","BENTAZON","ETHALFLURALIN","S-METOLACHLOR","PRONAMIDE","DIQUAT"):
        return "herbicide"
    if has("-THRIN","-CLOPRID","IMIDACLOPRID","ABAMECTIN","SPINOSAD","SPINETORAM","SPIROTETRAMAT",
           "FIPRONIL","INDOXACARB","CHLORANTRANILIPROLE","METHOXYFENOZIDE","DINOTEFURAN","THIAMETHOXAM",
           "METHOMYL","ACETAMIPRID","PYRIPROXYFEN","SULFOXAFLOR","CYANTRANILIPROLE","FLUPYRADIFURONE",
           "PYRETHRIN","AZADIRACHTIN","MALATHION","CHLORPYRIFOS","CARBARYL","OXAMYL","DIAZINON",
           "BUPROFEZIN","ETOXAZOLE","BIFENAZATE","CYFLUMETOFEN","FLONICAMID","CLOFENTEZINE","NALED",
           "EMAMECTIN","TOLFENPYRAD","SPIRODICLOFEN","HEXYTHIAZOX","PYMETROZINE","ESFENVALERATE",
           "FENPROPATHRIN","METHIDATHION","PHOSMET","ACEPHATE","DIMETHOATE","SPINETORAM","NOVALURON"):
        return "insecticide/miticide"
    if has("-STROBIN","-CONAZOLE","AZOXYSTROBIN","MANCOZEB","CHLOROTHALONIL","COPPER","SULFUR",
           "PHOSPHITE","BOSCALID","FLUOPYRAM","CAPTAN","MYCLOBUTANIL","DIFENOCONAZOLE","FLUDIOXONIL",
           "IPRODIONE","METALAXYL","MEFENOXAM","CYPRODINIL","FENHEXAMID","ZIRAM","THIOPHANATE",
           "PROPICONAZOLE","TEBUCONAZOLE","FLUTRIAFOL","CYAZOFAMID","MANDIPROPAMID","FENBUCONAZOLE",
           "QUINOXYFEN","TRIFLUMIZOLE","POLYOXIN","FOSETYL","DODINE","FLUAZINAM","PENTHIOPYRAD"):
        return "fungicide"
    if has("DIPHACINONE","BRODIFACOUM","BROMADIOLONE","CHLOROPHACINONE","WARFARIN","ZINC PHOSPHIDE",
           "CHOLECALCIFEROL","DIFETHIALONE","STRYCHNINE"):
        return "rodenticide"
    if has("1,3-DICHLOROPROPENE","METAM","CHLOROPICRIN","DAZOMET","METHYL BROMIDE","TELONE",
           "DITHIOCARBAMATE","SODIUM TETRATHIOCARBONATE"):
        return "fumigant"
    if has("MINERAL OIL","PETROLEUM","SOAP","KAOLIN","POLYETHER","FATTY ACID","SILICONE","SPRAY OIL"):
        return "oil/adjuvant"
    if has("GIBBERELL","ETHEPHON","PACLOBUTRAZOL","ABSCISIC","MEPIQUAT","TRINEXAPAC","1-METHYLCYCLOPROPENE","CYTOKININ"):
        return "growth regulator"
    return "other"

VOL = {"Gallon":1.0,"Quart":0.25,"Pint":0.125,"Ounce":1/128.0,"Liters":0.264172,"Milliliters":0.000264172}

def is_chem_known(ai):
    s=(ai or "").strip()
    return bool(s) and "FOIA" not in s.upper() and "NOT PUBLIC" not in s.upper()

def main():
    os.makedirs(OUT, exist_ok=True)
    cx = sqlite3.connect("file:///" + DB.replace("\\","/") + "?mode=ro", uri=True, timeout=120)
    cx.execute("PRAGMA temp_store=MEMORY")

    # ---------- aggregation: pre-group in SQL, roll up per cell in Python ----------
    cells = {}
    q = ("SELECT ROUND(lat,?) la, ROUND(lon,?) lo, county, region, year, land_type, source, "
         "active_ingredient, unit, SUM(CASE WHEN amount IS NULL THEN 0 ELSE amount END) amt, COUNT(*) c "
         "FROM applications WHERE lat IS NOT NULL AND lon IS NOT NULL AND year>=2020 "
         "GROUP BY la,lo,county,region,year,land_type,source,active_ingredient,unit")
    grp = 0
    for la,lo,county,region,year,land,source,ai,unit,amt,c in cx.execute(q, (PREC,PREC)):
        grp += 1
        k=(la,lo)
        cell=cells.get(k)
        if cell is None:
            cell=cells[k]={"county":county,"region":region,"n":0,"lbs":0.0,"gal":0.0,"acres":0.0,
                           "cls":collections.Counter(),"yr":collections.Counter(),
                           "land":collections.Counter(),"ai":collections.Counter()}
        cell["n"]+=c
        cls=chem_class(ai)
        cell["cls"][cls]+=c
        if year: cell["yr"][str(int(year))]+=c
        cell["land"][land or "unknown"]+=c
        if is_chem_known(ai): cell["ai"][ai]+=c
        a=float(amt or 0)
        if source=="facts": cell["acres"]+=a
        elif unit in VOL:   cell["gal"]+=a*VOL[unit]
        else:               cell["lbs"]+=a   # Pounds (and any non-volume unit)

    feats=[]
    for (la,lo),c in cells.items():
        feats.append({"type":"Feature","geometry":{"type":"Point","coordinates":[lo,la]},
            "properties":{"county":c["county"],"region":c["region"],"n":c["n"],
                "lbs":round(c["lbs"],1),"gal":round(c["gal"],1),"acres":round(c["acres"],1),
                "cls":dict(c["cls"]),"yr":dict(c["yr"]),"land":dict(c["land"]),
                "ai":c["ai"].most_common(5)}})
    json.dump({"type":"FeatureCollection","name":"aggregated","prec":PREC,"features":feats},
              open(os.path.join(OUT,"aggregated.geojson"),"w"), separators=(",",":"))

    # ---------- summary ----------
    summ={"by_class":collections.Counter(),"by_year":{},"by_land":{},"by_region":{},"by_source":{},"total":0}
    for c in cells.values():
        for k,v in c["cls"].items(): summ["by_class"][k]+=v
    for col,key in [("year","by_year"),("land_type","by_land"),("region","by_region"),("source","by_source")]:
        for v,n in cx.execute(f"SELECT {col},COUNT(*) FROM applications WHERE year>=2020 GROUP BY {col}"):
            summ[key][str(v)]=n
    summ["total"]=cx.execute("SELECT COUNT(*) FROM applications WHERE year>=2020").fetchone()[0]
    summ["by_class"]=dict(summ["by_class"])
    json.dump(summ, open(os.path.join(OUT,"summary.json"),"w"), indent=1)

    # ---------- transparency / coverage scores ----------
    def grade(s): return "A" if s>=85 else "B" if s>=70 else "C" if s>=55 else "D" if s>=40 else "F"
    def label(s): return "Well-documented" if s>=70 else "Partial" if s>=55 else "Sparse" if s>=40 else "Minimal"
    def recency(maxyr):
        if not maxyr: return 0
        return max(0,min(100,100-(2023-int(maxyr))*20))   # 2023+ =100, -20/yr older
    def score_rows(group_cols):
        cols=",".join(group_cols)
        q=(f"SELECT {cols}, COUNT(*) n, "
           "SUM(CASE WHEN active_ingredient IS NOT NULL AND active_ingredient!='' AND active_ingredient NOT LIKE '%FOIA%' AND active_ingredient NOT LIKE '%not public%' THEN 1 ELSE 0 END) chem, "
           "SUM(CASE WHEN amount IS NOT NULL AND amount>0 AND unit IS NOT NULL AND unit!='' THEN 1 ELSE 0 END) amt, "
           "SUM(CASE WHEN lat IS NOT NULL AND lon IS NOT NULL THEN 1 ELSE 0 END) geo, "
           "MAX(year) my, COUNT(DISTINCT source) src "
           f"FROM applications WHERE year>=2020 GROUP BY {cols}")
        out={}
        for row in cx.execute(q):
            *keys,n,chem,amt,geo,my,src=row
            if not n: continue
            c_chem=100*chem/n; c_amt=100*amt/n; c_geo=100*geo/n
            c_rec=recency(my); c_src=50 if src<=1 else 80 if src==2 else 100
            comp=round(0.35*c_chem+0.20*c_amt+0.20*c_rec+0.15*c_src+0.10*c_geo,1)
            entry={"n":n,"score":comp,"grade":grade(comp),"label":label(comp),
                   "components":{"chem":round(c_chem),"amount":round(c_amt),"recency":c_rec,
                                 "sources":c_src,"geocoded":round(c_geo)},
                   "latest_year":my,"n_sources":src}
            out["|".join(str(k) for k in keys)]=entry
        return out
    scores={"method":"Data-transparency / coverage score (0-100): how complete the PUBLIC data is for a "
                      "jurisdiction. 35% chemical disclosed, 20% amount+unit, 20% recency, 15% source breadth, 10% geocoded.",
            "weights":{"chem":35,"amount":20,"recency":20,"sources":15,"geocoded":10},
            "regions":score_rows(["region"]),
            "counties":score_rows(["county"]),
            "sectors":score_rows(["county","land_type"])}
    json.dump(scores, open(os.path.join(OUT,"scores.json"),"w"), separators=(",",":"))

    sz=lambda f: os.path.getsize(os.path.join(OUT,f))
    print(f"SQL groups: {grp:,} -> map points: {len(feats):,}")
    print(f"aggregated.geojson {sz('aggregated.geojson'):,}B | summary.json {sz('summary.json'):,}B | scores.json {sz('scores.json'):,}B")
    print("by_class:", summ["by_class"])
    print("counties scored:", len(scores["counties"]), "| sample (best/worst):")
    cs=sorted(scores["counties"].items(), key=lambda kv:-kv[1]["score"])
    for k,v in cs[:3]+cs[-3:]: print(f"   {k}: {v['score']} {v['grade']} ({v['label']}) chem={v['components']['chem']}%")

if __name__=="__main__":
    main()
