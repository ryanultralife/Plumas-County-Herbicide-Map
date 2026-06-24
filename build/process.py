# Regenerate map dots (with per-dot herbicide + dates) and Tab-4 raw data from source.
import pandas as pd, numpy as np, re, json, math, os

SRC = r'C:\Users\ryanv\Downloads\Plumas County Pesticide Applications 2021-2024 (1).xlsx'
OUT = os.path.dirname(__file__)

# ---- product -> (active ingredient, type) ----
# type: H=Herbicide, I=Insecticide, A=Adjuvant/surfactant
def classify(name):
    n = (name or '').upper()
    def has(*xs): return any(x in n for x in xs)
    if has('VELPAR'):                                   return 'Hexazinone','H'
    if has('ACCORD','ROUNDUP','DUPLICATOR','CORNERSTONE','GLY STAR','FREELEXX','FORESTERS'):
        return 'Glyphosate','H'
    if has('ROTARY','POLARIS','CAVALIER'):              return 'Imazapyr','H'
    if has('MILESTONE'):                                return 'Aminopyralid','H'
    if has('ESPLANADE'):                                return 'Indaziflam','H'
    if has('CLEANTRAXX'):                               return 'Oxyfluorfen + penoxsulam','H'
    if has('2,4-D'):                                    return '2,4-D','H'
    if has('SULTRUS'):                                  return 'Sulfometuron-methyl (verify)','H'
    if has('VASTLAN','GARLON'):                         return 'Triclopyr','H'
    if has('TRANSLINE'):                                return 'Clopyralid','H'
    if has('DICAMBA'):                                  return 'Dicamba','H'
    if has('TOMBSTONE'):                                return 'Bifenthrin','I'
    if has('REIGN'):                                    return 'Adjuvant (verify)','A'
    if has('CROSSHAIR'):                                return 'Adjuvant (verify)','A'
    # everything else (MSO, spreaders, oils, buffers, drift agents)
    return 'Adjuvant/surfactant','A'

# ---- PLSS section centroid (Mount Diablo Meridian) ----
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

df = pd.read_excel(SRC, sheet_name='Single Job PUR')
df = df.dropna(subset=['Application Date','Quantity Used'])           # drop the 2 empty rows
df['date'] = pd.to_datetime(df['Application Date']).dt.strftime('%Y-%m-%d')
df['qty']  = pd.to_numeric(df['Quantity Used'], errors='coerce').fillna(0.0)
df['unit'] = df['Quantity Units'].fillna('')
df['method'] = df['Appl. Method'].fillna('Unspecified')
ai_type = df['Product Name'].apply(classify)
df['ai']   = [a for a,_ in ai_type]
df['type'] = [t for _,t in ai_type]
# liquid gallons-equivalent: Gallon as-is, Ounce/128 (fluid oz), Pounds excluded
df['gal'] = np.where(df['unit'].eq('Gallon'), df['qty'],
             np.where(df['unit'].eq('Ounce'), df['qty']/128.0, 0.0))
df['lb']  = np.where(df['unit'].eq('Pounds'), df['qty'], 0.0)
def mtrs(r):
    try:    return f"T{str(r['Township']).strip()} R{str(r['Range']).strip()} S{int(float(r['Section']))}"
    except Exception: return ''
df['mtrs'] = df.apply(mtrs, axis=1)
cz = df.apply(lambda r: centroid(r['Township'],r['Range'],r['Section']), axis=1)
df['lat'] = [c[0] if c else None for c in cz]
df['lon'] = [c[1] if c else None for c in cz]

# ================= RECONCILIATION =================
print('=== RECONCILE (target: gal 58,662 / lb 76,204 / apps 2,800) ===')
print('rows used:', len(df))
print('total gal:', round(df.gal.sum(),1), '| total lb:', round(df.lb.sum(),1), '| apps:', len(df))
yr = df.assign(y=df.date.str[:4]).groupby('y').agg(gal=('gal','sum'),lb=('lb','sum'),n=('gal','size'))
print(yr.round(1).to_string())
print('herbicide-only gal:', round(df[df.type=='H'].gal.sum(),1))
print('adjuvant gal:', round(df[df.type=='A'].gal.sum(),1), '| insecticide gal:', round(df[df.type=='I'].gal.sum(),1))
print('\n=== AI active-ingredient PRODUCT totals (as-reported, gal & lb) ===')
print(df.groupby('ai').agg(gal=('gal','sum'),lb=('lb','sum'),apps=('gal','size')).round(1).sort_values('gal',ascending=False).to_string())

# ================= MAP: enriched methods =================
geo = df[df.lat.notna()].copy()
methods = {}
for (method, lat, lon), g in geo.groupby(['method','lat','lon']):
    chems = {}
    for (ai,tp), gg in g[g.type.isin(['H','I'])].groupby(['ai','type']):
        chems[ai] = [round(gg.gal.sum(),1), round(gg.lb.sum(),1), int(len(gg)), tp]
    chem_list = sorted(([k,v[0],v[1],v[2],v[3]] for k,v in chems.items()),
                       key=lambda r:-(r[1]+r[2]))
    adj = round(g[g.type=='A'].gal.sum(),1)
    perms = '; '.join(sorted(set(str(p) for p in g['Permitee'].dropna())))
    methods.setdefault(method, []).append({
        'Lat':lat,'Lon':lon,
        'Gallons':round(g.gal.sum(),1),'Pounds':round(g.lb.sum(),1),'Apps':int(len(g)),
        'D0':g.date.min(),'D1':g.date.max(),
        'Chems':chem_list,'Adj':adj,'Permittees':perms })
# stable order: Ground, Aircraft, Unspecified
order = {'Ground':0,'Aircraft':1,'Unspecified':2}
methods = {k:methods[k] for k in sorted(methods, key=lambda k:order.get(k,9))}
truemax = max(p['Gallons'] for arr in methods.values() for p in arr)
vmax = 930.6  # preserve original color-scale ceiling (legend: "high 931+")
print('\nmap dots:', sum(len(v) for v in methods.values()), '| methods:', {k:len(v) for k,v in methods.items()}, '| true max gal:', round(truemax,1), '| vmax(scale):', vmax)
with open(os.path.join(OUT,'methods.json'),'w',encoding='utf-8') as f:
    json.dump({'methods':methods,'vmax':vmax}, f, separators=(',',':'))

# ================= TAB 4: dictionary-encoded raw records =================
perms = sorted(set(str(p) for p in df['Permitee'].dropna()))
prods = sorted(set(str(p) for p in df['Product Name'].dropna()))
apps  = sorted(set(str(a) for a in df['Applicator Name'].dropna()))
ais   = sorted(set(df['ai']))
units = ['Gallon','Pounds','Ounce','']
meths = ['Ground','Aircraft','Unspecified']
pi={v:i for i,v in enumerate(perms)}; pri={v:i for i,v in enumerate(prods)}
api={v:i for i,v in enumerate(apps)}; aii={v:i for i,v in enumerate(ais)}
ui={v:i for i,v in enumerate(units)}; mi={v:i for i,v in enumerate(meths)}
prod_meta=[]  # [epareg, aiIdx, type] per product
prod_first={}
for p in prods:
    sub=df[df['Product Name'].astype(str)==p].iloc[0]
    prod_meta.append([str(sub['EPA Reg No']) if pd.notna(sub['EPA Reg No']) else '', aii[sub['ai']], sub['type']])
rows=[]
for _,r in df.iterrows():
    rows.append([r['date'], r['mtrs'], pi.get(str(r['Permitee']),-1),
                 pri.get(str(r['Product Name']),-1), round(float(r['qty']),2),
                 ui.get(r['unit'],3), mi.get(r['method'],2),
                 api.get(str(r['Applicator Name']),-1),
                 (str(r['Site Name']) if pd.notna(r['Site Name']) else '')])
tab4={'cols':['Date','Location (MTRS)','Permittee','Product','Active ingredient','Qty','Units','Method','Applicator','Site'],
      'perm':perms,'prod':prods,'prodMeta':prod_meta,'appl':apps,'ai':ais,
      'unit':units,'meth':meths,'rows':rows,
      'span':[df.date.min(),df.date.max()]}
with open(os.path.join(OUT,'tab4.json'),'w',encoding='utf-8') as f:
    json.dump(tab4, f, separators=(',',':'))
print('\ntab4 rows:', len(rows), '| products:', len(prods), '| permittees:', len(perms), '| applicators:', len(apps))
print('date span:', tab4['span'])
print('files written:', os.path.getsize(os.path.join(OUT,'methods.json')),'bytes methods,',
      os.path.getsize(os.path.join(OUT,'tab4.json')),'bytes tab4')
