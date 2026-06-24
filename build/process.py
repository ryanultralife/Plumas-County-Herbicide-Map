# Regenerate map + Tab-4 from BOTH Production-Ag PUR tabs (single-job + monthly-summary).
# Each chemical labeled by type; units normalized; per-dot herbicides, dates, acres.
import pandas as pd, numpy as np, re, json, math, os

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'data', 'Plumas County Pesticide Applications 2021-2024.xlsx')
OUT = os.path.dirname(os.path.abspath(__file__))

# ---------------- product -> (active ingredient, type, dry?) ----------------
# type: H herbicide, I insecticide, F fungicide, A adjuvant, P plant-growth-reg, O other
DRY = True
def classify(name, reg):
    n = (name or '').upper(); r = str(reg or '')
    def has(*xs): return any(x in n for x in xs)
    # --- herbicides ---
    if has('VELPAR'):                         return 'Hexazinone','H',DRY
    if has('ACCORD','ROUNDUP','DUPLICATOR','CORNERSTONE','GLY STAR','FREELEXX','FORESTERS','VOLUNTEER'):
        return 'Glyphosate','H',False
    if has('ROTARY','POLARIS','CAVALIER'):    return 'Imazapyr','H',False
    if has('RAPTOR'):                         return 'Imazamox','H',False
    if has('MILESTONE'):                      return 'Aminopyralid','H',False
    if has('ESPLANADE'):                      return 'Indaziflam','H',False
    if has('CLEANTRAXX'):                     return 'Oxyfluorfen + penoxsulam','H',False
    if has('2,4-D','WEEDAR','SPEEDZONE'):     return '2,4-D','H',False
    if has('SULTRUS'):                        return 'Sulfometuron-methyl (verify)','H',False
    if has('VASTLAN','GARLON'):               return 'Triclopyr','H',False
    if has('CONFRONT'):                       return 'Triclopyr + clopyralid','H',False
    if has('TRANSLINE','LONTREL'):            return 'Clopyralid','H',False
    if has('DICAMBA'):                        return 'Dicamba','H',False
    if has('METRIBUZIN','DIMETRIC'):          return 'Metribuzin','H',DRY
    if has('TELAR'):                          return 'Chlorsulfuron','H',DRY
    if has('PARAQUAT'):                       return 'Paraquat','H',False
    if has('QUICKSILVER','SHARK'):            return 'Carfentrazone-ethyl','H',False
    if has('AXXE'):                           return 'Ammonium nonanoate','H',False
    # --- insecticides / miticides ---
    if has('TOMBSTONE'):                      return 'Bifenthrin','I',False
    if has('LAMBDA-CY','WARRIOR'):            return 'Lambda-cyhalothrin','I',False
    if has('DIMILIN'):                        return 'Diflubenzuron','I',False
    if has('MITE-AWAY'):                      return 'Formic acid (miticide)','I',DRY
    if has('DEVOUR'):                         return 'Insecticide bait (verify)','I',False
    # --- fungicides (mostly golf turf) ---
    if has('DACONIL','INSTRATA'):             return 'Chlorothalonil','F',False
    if has('HEADWAY'):                        return 'Azoxystrobin + propiconazole','F',False
    if has('HERITAGE'):                       return 'Azoxystrobin','F',False
    if has('MEDALLION'):                      return 'Fludioxonil','F',False
    if has('SECURE'):                         return 'Fluazinam','F',False
    if has('VELISTA'):                        return 'Penthiopyrad','F',False
    if has('OCTIVIO'):                        return 'Fungicide (verify)','F',False
    if has('SPORAX'):                         return 'Sodium borate (stump fungicide)','F',DRY
    # --- plant growth regulators (turf) ---
    if has('PRIMO MAXX'):                     return 'Trinexapac-ethyl','P',False
    if has('PROXY'):                          return 'Ethephon','P',False
    # --- wood preservative / other ---
    if has('CELLU-TREAT'):                    return 'Disodium octaborate (wood preservative)','O',DRY
    if has('SPLAT VERB'):                     return 'Pheromone (mating disruptant)','O',DRY
    # --- adjuvants / surfactants (incl. CA adjuvant reg numbers, verify ones) ---
    if has('REIGN','CROSSHAIR'):              return 'Adjuvant (verify)','A',False
    return 'Adjuvant/surfactant','A',False

TYPE_NAME = {'H':'Herbicide','I':'Insecticide','F':'Fungicide','A':'Adjuvant/surfactant',
             'P':'Plant growth regulator','O':'Other'}

# liquid volume -> gallons; weight -> pounds
VOL = {'Gallon':1.0,'Quart':0.25,'Pint':0.125,'Ounce':1/128.0,'Liters':0.264172,'Milliliters':0.000264172}
WT  = {'Pounds':1.0,'Grams':1/453.592,'Ounce':1/16.0}   # Ounce here only used for DRY products
def to_gal_lb(unit, qty, dry):
    u = str(unit)
    if dry:
        if u in WT: return 0.0, qty*WT[u]
        if u in VOL: return qty*VOL[u], 0.0     # unexpected liquid unit on a dry product
        return 0.0, 0.0
    else:
        if u in VOL: return qty*VOL[u], 0.0
        if u in ('Pounds','Grams'): return 0.0, qty*WT[u]   # dry unit on a liquid product
        return 0.0, 0.0

# ---------------- PLSS section centroid (Mount Diablo Meridian) ----------------
BASE_LAT, MERID_LON, MI_LAT = 37.8817, -121.9144, 1/69.0
def centroid(twp, rng, sec):
    try:
        tnum=int(re.match(r'(\d+)',str(twp)).group(1)); tdir=str(twp).strip()[-1].upper()
        rnum=int(re.match(r'(\d+)',str(rng)).group(1)); rdir=str(rng).strip()[-1].upper()
        s=int(float(sec))
    except Exception:
        return None
    if not (1<=s<=36): return None
    row=(s-1)//6
    col=5-((s-1)%6) if row%2==0 else (s-1)%6
    x=col+0.5; y=5.5-row
    me=(rnum-1)*6+x if rdir=='E' else -((rnum-1)*6+(6-x))
    mn=(tnum-1)*6+y if tdir=='N' else -((tnum-1)*6+(6-y))
    lat=BASE_LAT+mn*MI_LAT
    lon=MERID_LON+(me/(69.17*math.cos(math.radians(lat))))
    return round(lat,4), round(lon,4)

def mtrs(r):
    try:    return f"T{str(r['Township']).strip()} R{str(r['Range']).strip()} S{int(float(r['Section']))}"
    except Exception: return ''

# ---------------- load + normalize both tabs ----------------
def load(sheet, src_label, date_col, end_col):
    d = pd.read_excel(SRC, sheet_name=sheet)
    d = d[pd.to_numeric(d['Quantity Used'], errors='coerce').notna()].copy()
    d['src'] = src_label
    d['date'] = pd.to_datetime(d[date_col], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
    d['dend'] = pd.to_datetime(d[end_col], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
    d['qty'] = pd.to_numeric(d['Quantity Used'], errors='coerce').fillna(0.0)
    d['unit'] = d['Quantity Units'].fillna('')
    d['method'] = d['Appl. Method'].fillna('Unspecified') if 'Appl. Method' in d else 'Unspecified'
    d['appl'] = d['Applicator Name'].fillna('') if 'Applicator Name' in d else ''
    cl = d['Product Name'].apply(lambda p: classify(p, None))
    d['ai']=[a for a,_,_ in cl]; d['type']=[t for _,t,_ in cl]; d['dry']=[x for _,_,x in cl]
    gl = [to_gal_lb(u,q,dr) for u,q,dr in zip(d['unit'],d['qty'],d['dry'])]
    d['gal']=[g for g,_ in gl]; d['lb']=[l for _,l in gl]
    d['acres'] = np.where(d['Treated Units'].astype(str).str.upper().eq('ACRES'),
                          pd.to_numeric(d['Treated Amount'],errors='coerce').fillna(0.0), 0.0)
    d['mtrs'] = d.apply(mtrs, axis=1)
    cz = d.apply(lambda r: centroid(r['Township'],r['Range'],r['Section']), axis=1)
    d['lat']=[c[0] if c else None for c in cz]; d['lon']=[c[1] if c else None for c in cz]
    return d

sj = load('Single Job PUR', 'Forestry (single-job)', 'Application Date', 'Application Date')
ms = load('ProdAgMonthlySummary', 'Other operators (monthly)', 'Start Application Date', 'End Application Date')
df = pd.concat([sj, ms], ignore_index=True)
LAYER = {'Forestry (single-job)':'Timber / forestry (2021–24)',
         'Other operators (monthly)':'Other operators (2024)'}

print('=== combined ===')
print('SJ rows', len(sj), '| MS rows', len(ms), '| total', len(df))
print('SJ gal', round(sj.gal.sum(),1), 'lb', round(sj.lb.sum(),1), '| MS gal', round(ms.gal.sum(),1), 'lb', round(ms.lb.sum(),1))
print('ungeocoded (no PLSS):', int(df.lat.isna().sum()), '| mappable:', int(df.lat.notna().sum()))
print('types:', df.groupby('type').agg(n=('type','size'),gal=('gal','sum'),lb=('lb','sum')).round(1).to_dict('index'))

# ---------------- map dots, grouped by source-layer + method + centroid ----------------
geo = df[df.lat.notna()].copy()
methods = {}
for (src, method, lat, lon), g in geo.groupby(['src','method','lat','lon']):
    chems = {}
    for (ai,tp), gg in g[g.type!='A'].groupby(['ai','type']):
        chems[ai] = [round(gg.gal.sum(),1), round(gg.lb.sum(),1), int(len(gg)), tp]
    chem_list = sorted(([k,v[0],v[1],v[2],v[3]] for k,v in chems.items()), key=lambda r:-(r[1]+r[2]))
    perms = '; '.join(sorted(set(str(p) for p in g['Permitee'].dropna())))
    layer = LAYER[src]
    valid = [x for x in list(g['date'])+list(g['dend']) if x]
    methods.setdefault(layer, []).append({
        'Lat':lat,'Lon':lon,'Method':method,
        'Gallons':round(g.gal.sum(),1),'Pounds':round(g.lb.sum(),1),'Apps':int(len(g)),
        'Acres':round(g.acres.sum(),1),'D0':(min(valid) if valid else ''),'D1':(max(valid) if valid else ''),
        'Chems':chem_list,'Adj':round(g[g.type=='A'].gal.sum(),1),'Permittees':perms})
methods = {LAYER['Forestry (single-job)']:methods[LAYER['Forestry (single-job)']],
           LAYER['Other operators (monthly)']:methods[LAYER['Other operators (monthly)']]}
vmax = 930.6
print('\nmap dots:', {k:len(v) for k,v in methods.items()})
json.dump({'methods':methods,'vmax':vmax}, open(os.path.join(OUT,'methods.json'),'w',encoding='utf-8'), separators=(',',':'))

# ---------------- Tab 4: every record (both tabs), dictionary-encoded ----------------
df['report'] = df['src'].map({'Forestry (single-job)':'Forestry (single-job)','Other operators (monthly)':'Other operators (monthly)'})
perms=sorted(set(map(str,df['Permitee'].dropna()))); prods=sorted(set(map(str,df['Product Name'].dropna())))
apps=sorted(set(map(str,df['appl'].replace('',np.nan).dropna()))); ais=sorted(set(df['ai']))
units=sorted(set(map(str,df['unit']))); meths=sorted(set(map(str,df['method']))); reports=sorted(set(df['report']))
pi={v:i for i,v in enumerate(perms)}; pri={v:i for i,v in enumerate(prods)}; api={v:i for i,v in enumerate(apps)}
aii={v:i for i,v in enumerate(ais)}; ui={v:i for i,v in enumerate(units)}; mi={v:i for i,v in enumerate(meths)}; ri={v:i for i,v in enumerate(reports)}
prodMeta=[]
for p in prods:
    s=df[df['Product Name'].astype(str)==p].iloc[0]
    prodMeta.append([str(s['EPA Reg No']) if pd.notna(s['EPA Reg No']) else '', aii[s['ai']], s['type']])
rows=[]
for _,r in df.iterrows():
    rows.append([r['date'], r['mtrs'], pi.get(str(r['Permitee']),-1), pri.get(str(r['Product Name']),-1),
                 round(float(r['qty']),2), ui.get(str(r['unit']),0), mi.get(str(r['method']),0),
                 api.get(str(r['appl']),-1), (str(r['Site Name']) if pd.notna(r.get('Site Name')) else ''),
                 round(float(r['acres']),1), ri.get(r['report'],0)])
tab4={'cols':['Date','Location (MTRS)','Permittee','Product','EPA Reg','Active ingredient','Type','Qty','Units','Method','Acres','Applicator','Report','Site'],
      'perm':perms,'prod':prods,'prodMeta':prodMeta,'appl':apps,'ai':ais,'unit':units,'meth':meths,'report':reports,
      'typeName':TYPE_NAME,'rows':rows,'span':[min(_alld), max(_alld)] if (_alld:=[x for x in list(df['date'])+list(df['dend']) if x]) else ['','']}
json.dump(tab4, open(os.path.join(OUT,'tab4.json'),'w',encoding='utf-8'), separators=(',',':'))
print('tab4 rows:', len(rows), '| products:', len(prods), '| span:', tab4['span'])
print('files:', os.path.getsize(os.path.join(OUT,'methods.json')),'methods,', os.path.getsize(os.path.join(OUT,'tab4.json')),'tab4')
