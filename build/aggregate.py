#!/usr/bin/env python3
"""
Build small, map-ready static files from the big applications DB (Supabase export
or the local SQLite). Output matches what map.html expects:
  data/agg/aggregated.geojson - one point per ~section centroid; properties:
       county, region, n, c={ "YEAR|class|land": [count, lbs] }, ai=[[name,count],...]
  data/agg/summary.json       - headline totals
  data/agg/scores.json        - per-jurisdiction DATA-TRANSPARENCY / COVERAGE score

Usage:  python build/aggregate.py [DB_PATH] [OUT_DIR]
Reads the DB read-only. Default DB = the backup copy; default out = repo data/agg.
"""
import sqlite3, json, os, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB   = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\ryanv\plumas_db_backup\applications.sqlite"
OUT  = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "data", "agg")
PREC = 3

# chemical class -> names MUST match index.html CLASS_COLORS keys.
# Keep these patterns in sync with supabase/chem_class.sql.
import re as _re
_HERB = _re.compile(r"GLYPHOSATE|GLUFOSINATE|OXYFLUORFEN|PENDIMETHALIN|INDAZIFLAM|SAFLUFENACIL|CLETHODIM|SETHOXYDIM|CARFENTRAZONE|PYRAFLUFEN|TRIFLURALIN|PARAQUAT|DIURON|2,4-D|DICAMBA|ATRAZINE|SIMAZINE|METOLACHLOR|FLUMIOXAZIN|IMAZAPYR|IMAZAMOX|IMAZETHAPYR|IMAZAQUIN|TRICLOPYR|CLOPYRALID|AMINOPYRALID|HEXAZINONE|NORFLURAZON|BROMACIL|NAPROPAMIDE|METRIBUZIN|LINURON|PRODIAMINE|ISOXABEN|MESOTRIONE|FLUROXYPYR|\bMCPA\b|BENTAZON|PRONAMIDE|PROPYZAMIDE|DIQUAT|BENSULIDE|CHLORTHAL|PROPANIL|SULFURON|METURON|QUIZALOFOP|FLUAZIFOP|FENOXAPROP|OXADIAZON|OXADIARGYL|SULFENTRAZONE|FOMESAFEN|ACIFLUORFEN|LACTOFEN|ORYZALIN|DITHIOPYR|FLURIDONE|TOPRAMEZONE|TEMBOTRIONE|PYROXASULFONE|DIMETHENAMID|ACETOCHLOR|ALACHLOR|ETHALFLURALIN|FLUMETSULAM|HALAUXIFEN|FLORASULAM|PICLORAM|CYCLOATE|MOLINATE|THIOBENCARB|TRIBENURON")
_INSECT = _re.compile(r"THRIN|CLOPRID|IMIDACLOPRID|ABAMECTIN|SPINOSAD|SPINETORAM|SPIROTETRAMAT|SPIROMESIFEN|SPIRODICLOFEN|FIPRONIL|INDOXACARB|CHLORANTRANILIPROLE|CYANTRANILIPROLE|TETRANILIPROLE|CYCLANILIPROLE|METHOXYFENOZIDE|TEBUFENOZIDE|CHROMAFENOZIDE|DINOTEFURAN|THIAMETHOXAM|CLOTHIANIDIN|ACETAMIPRID|METHOMYL|PYRIPROXYFEN|FENOXYCARB|KINOPRENE|HYDROPRENE|METHOPRENE|SULFOXAFLOR|FLUPYRADIFURONE|FLUPYRIMIN|TRIFLUMEZOPYRIM|PYRETHRIN|PIPERONYL|AZADIRACHTIN|NEEM|MALATHION|CHLORPYRIFOS|CARBARYL|OXAMYL|DIAZINON|ACEPHATE|DIMETHOATE|NALED|BUPROFEZIN|ETOXAZOLE|BIFENAZATE|FLONICAMID|EMAMECTIN|MILBEMECTIN|HEXYTHIAZOX|PYMETROZINE|NOVALURON|LUFENURON|DIFLUBENZURON|CYROMAZINE|CHLORFENAPYR|CYFLUMETOFEN|FENPYROXIMATE|ACEQUINOCYL|PROPARGITE|FENBUTATIN|METAFLUMIZONE|AFIDOPYROPEN|TOLFENPYRAD|BROFLANILIDE|ISOCYCLOSERAM|THURINGIENSIS|BEAUVERIA|METARHIZIUM|BURKHOLDERIA|CHROMOBACTERIUM|\bBORIC\b|BORATE|DIATOMACEOUS")
_FUNG = _re.compile(r"STROBIN|CONAZOLE|MANCOZEB|CHLOROTHALONIL|COPPER|\bSULFUR\b|PHOSPHITE|FOSETYL|BOSCALID|FLUOPYRAM|FLUOPICOLIDE|CAPTAN|FOLPET|MYCLOBUTANIL|FLUDIOXONIL|IPRODIONE|METALAXYL|MEFENOXAM|CYPRODINIL|PYRIMETHANIL|FENHEXAMID|ZIRAM|THIRAM|METIRAM|THIOPHANATE|FLUAZINAM|PENTHIOPYRAD|FLUXAPYROXAD|PYDIFLUMETOFEN|ISOFETAMID|MANDIPROPAMID|CYAZOFAMID|CYMOXANIL|ZOXAMIDE|FAMOXADONE|FENAMIDONE|DIMETHOMORPH|VALIFENALATE|ETHABOXAM|OXATHIAPIPROLIN|PROPAMOCARB|DODINE|FLUTRIAFOL|FLUTOLANIL|TOLCLOFOS|METRAFENONE|QUINOXYFEN|CYFLUFENAMID|ACIBENZOLAR|POLYOXIN|BICARBONATE|PEROXYACETIC|HYDROGEN PEROXIDE|IMAZALIL|PROCHLORAZ|TRIFLUMIZOLE|SEDAXANE|BENZOVINDIFLUPYR|SUBTILIS|AMYLOLIQUEFACIENS|\bPUMILUS\b|REYNOUTRIA|MANDESTROBIN")
_RODENT = _re.compile(r"DIPHACINONE|BRODIFACOUM|DIFENACOUM|BROMADIOLONE|FLOCOUMAFEN|CHLOROPHACINONE|WARFARIN|ZINC PHOSPHIDE|CHOLECALCIFEROL|DIFETHIALONE|BROMETHALIN|STRYCHNINE")
_FUMI = _re.compile(r"1,3-DICHLOROPROPENE|METAM|CHLOROPICRIN|DAZOMET|METHYL BROMIDE|METHYL IODIDE|TELONE|DITHIOCARBAMATE|ISOTHIOCYANATE|SULFURYL|ALUMINUM PHOSPHIDE|MAGNESIUM PHOSPHIDE|PHOSPHINE")
_ADJ = _re.compile(r"MINERAL OIL|PETROLEUM|\bSOAP\b|KAOLIN|FATTY ACID|SPRAY OIL|POLYOXYETHYLENE|NONYLPHENOL|ALCOHOL ETHOXYLATE|LECITHIN|POLYDIMETHYLSILOXANE|SORBITAN|POLYETHYLENE GLYCOL")
_PGR = _re.compile(r"GIBBERELL|ETHEPHON|PACLOBUTRAZOL|ABSCISIC|MEPIQUAT|TRINEXAPAC|FORCHLORFENURON|PROHEXADION|CHLORMEQUAT|FLUMETRALIN|DAMINOZIDE|CYCLANILIDE|NAPHTHALENEACETIC|METHYLCYCLOPROPENE")
_ADJ_PROD = _re.compile(r"SURFACTANT|ADJUVANT|SPREADER|STICKER|\bMSO\b|\bNIS\b|\bCOC\b|CROP OIL|SEED OIL|METHYLATED|ORGANOSILICONE|SILICONE|SILWET|NONIONIC|WETTING|PENETRANT|ANTIFOAM|DEFOAM|FOAM FIGHTER|BUFFER|ACIDIFIER|DYNE-AMIC|LI 700|SYL-TAC|SYL-COAT|LIBERATE|KINETIC|NU FILM|NU-FILM|ACTIVATOR 90|LATRON|MSO CONCENTRATE|PRO 90")

def chem_class(ai):
    s = (ai or "").upper()
    if not s: return "unknown"
    if _HERB.search(s): return "herbicide"
    if _INSECT.search(s): return "insecticide"
    if _FUNG.search(s): return "fungicide"
    if _RODENT.search(s): return "rodenticide"
    if _FUMI.search(s): return "fumigant"
    if _ADJ.search(s): return "adjuvant"
    if _PGR.search(s): return "growth_regulator"
    return "other"

def chem_class_pa(ai, product):
    if ai and ai.strip(): return chem_class(ai)
    p = (product or "").upper()
    if not p: return "unknown"
    if _ADJ_PROD.search(p): return "adjuvant"
    return "unknown"

def is_chem_known(ai):
    s=(ai or "").strip()
    return bool(s) and "FOIA" not in s.upper() and "NOT PUBLIC" not in s.upper()

def main():
    os.makedirs(OUT, exist_ok=True)
    cx = sqlite3.connect("file:///" + DB.replace("\\","/") + "?mode=ro", uri=True, timeout=120)
    cx.execute("PRAGMA temp_store=MEMORY")

    cells = {}
    q = ("SELECT ROUND(lat,?) la, ROUND(lon,?) lo, county, region, year, land_type, source, "
         "active_ingredient, product, unit, SUM(CASE WHEN amount IS NULL THEN 0 ELSE amount END) amt, COUNT(*) c "
         "FROM applications WHERE lat IS NOT NULL AND lon IS NOT NULL AND year>=2020 AND year<=2026 "
         "GROUP BY la,lo,county,region,year,land_type,source,active_ingredient,product,unit")
    grp = 0
    for la,lo,county,region,year,land,source,ai,product,unit,amt,c in cx.execute(q, (PREC,PREC)):
        grp += 1
        cell = cells.get((la,lo))
        if cell is None:
            cell = cells[(la,lo)] = {"county":county,"region":region,"n":0,
                                     "c":collections.defaultdict(lambda:[0,0.0]),
                                     "ai":collections.Counter()}
        cell["n"] += c
        ck = f"{int(year) if year else ''}|{chem_class_pa(ai, product)}|{land or 'unknown'}"
        e = cell["c"][ck]; e[0] += c
        if (unit or "").lower() == "lbs": e[1] += float(amt or 0)
        if is_chem_known(ai): cell["ai"][ai] += c

    feats=[]
    for (la,lo),c in cells.items():
        combo = {k:[v[0], round(v[1],1)] for k,v in c["c"].items()}
        feats.append({"type":"Feature","geometry":{"type":"Point","coordinates":[lo,la]},
            "properties":{"county":c["county"],"region":c["region"],"n":c["n"],
                          "c":combo,"ai":c["ai"].most_common(5)}})
    json.dump({"type":"FeatureCollection","name":"aggregated","prec":PREC,"features":feats},
              open(os.path.join(OUT,"aggregated.geojson"),"w"), separators=(",",":"))

    # summary
    summ={"by_class":collections.Counter(),"by_year":{},"by_land":{},"by_region":{},"by_source":{}}
    for c in cells.values():
        for k,v in c["c"].items(): summ["by_class"][k.split("|")[1]] += v[0]
    for col,key in [("year","by_year"),("land_type","by_land"),("region","by_region"),("source","by_source")]:
        for v,n in cx.execute(f"SELECT {col},COUNT(*) FROM applications WHERE year>=2020 AND year<=2026 GROUP BY {col}"):
            summ[key][str(v)] = n
    summ["total"]=cx.execute("SELECT COUNT(*) FROM applications WHERE year>=2020 AND year<=2026").fetchone()[0]
    summ["by_class"]=dict(summ["by_class"])
    json.dump(summ, open(os.path.join(OUT,"summary.json"),"w"), indent=1)

    # transparency / coverage scores
    def grade(s): return "A" if s>=85 else "B" if s>=70 else "C" if s>=55 else "D" if s>=40 else "F"
    def label(s): return "Well-documented" if s>=70 else "Partial" if s>=55 else "Sparse" if s>=40 else "Minimal"
    def recency(my): return 0 if not my else max(0,min(100,100-(2023-int(my))*20))
    def score_rows(group_cols):
        cols=",".join(group_cols)
        q=(f"SELECT {cols}, COUNT(*) n, "
           "SUM(CASE WHEN active_ingredient IS NOT NULL AND active_ingredient!='' AND active_ingredient NOT LIKE '%FOIA%' AND active_ingredient NOT LIKE '%not public%' THEN 1 ELSE 0 END) chem, "
           "SUM(CASE WHEN amount IS NOT NULL AND amount>0 AND unit IS NOT NULL AND unit!='' THEN 1 ELSE 0 END) amt, "
           "SUM(CASE WHEN lat IS NOT NULL AND lon IS NOT NULL THEN 1 ELSE 0 END) geo, MAX(year) my, COUNT(DISTINCT source) src "
           f"FROM applications WHERE year>=2020 AND year<=2026 GROUP BY {cols}")
        out={}
        for row in cx.execute(q):
            *keys,n,chem,amt,geo,my,src=row
            if not n: continue
            cc,ca,cg=100*chem/n,100*amt/n,100*geo/n; cr=recency(my); csrc=50 if src<=1 else 80 if src==2 else 100
            comp=round(0.35*cc+0.20*ca+0.20*cr+0.15*csrc+0.10*cg,1)
            out["|".join(str(k) for k in keys)]={"n":n,"score":comp,"grade":grade(comp),"label":label(comp),
                "components":{"chem":round(cc),"amount":round(ca),"recency":cr,"sources":csrc,"geocoded":round(cg)},
                "latest_year":my,"n_sources":src}
        return out
    scores={"method":"Data-transparency/coverage (0-100): how complete the PUBLIC data is for a jurisdiction. "
                      "35% chemical disclosed, 20% amount+unit, 20% recency, 15% source breadth, 10% geocoded.",
            "weights":{"chem":35,"amount":20,"recency":20,"sources":15,"geocoded":10},
            "regions":score_rows(["region"]),"counties":score_rows(["county"]),"sectors":score_rows(["county","land_type"])}
    json.dump(scores, open(os.path.join(OUT,"scores.json"),"w"), separators=(",",":"))

    sz=lambda f: os.path.getsize(os.path.join(OUT,f))
    print(f"SQL groups {grp:,} -> {len(feats):,} points | aggregated.geojson {sz('aggregated.geojson'):,}B "
          f"summary {sz('summary.json'):,}B scores {sz('scores.json'):,}B")
    print("by_class:", summ["by_class"])

if __name__=="__main__":
    main()
