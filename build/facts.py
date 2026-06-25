# Build the federal (USFS FACTS) map layer from the COMPLETE Plumas NF file
# (data/plumas_nf_herbicide_facts.geojson, produced by scripts/pull_facts.py).
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
WT   = os.path.dirname(HERE)
MAIN = os.path.abspath(os.path.join(WT, '..', '..', '..'))
CANDS = [os.path.join(WT,'data','plumas_nf_herbicide_facts.geojson'),
         os.path.join(MAIN,'data','plumas_nf_herbicide_facts.geojson'),
         os.path.join(os.getcwd(),'data','plumas_nf_herbicide_facts.geojson')]
src = next((c for c in CANDS if os.path.exists(c)), None)
assert src, 'federal file not found in: '+str(CANDS)
d = json.load(open(src, encoding='utf-8'))
feats = [f for f in d['features'] if f.get('geometry') and f['geometry'].get('coordinates')]

def g(p, *keys):
    for k in keys:
        v = p.get(k)
        if v not in (None, ''): return v
    return ''

acts = sorted({(g(f['properties'],'activity') or '') for f in feats})
prjs = sorted({p for p in (g(f['properties'],'nepa_project','project') for f in feats) if p})
cos  = sorted({(g(f['properties'],'county') or '') for f in feats})
ai = {v:i for i,v in enumerate(acts)}; pj = {v:i for i,v in enumerate(prjs)}; ci = {v:i for i,v in enumerate(cos)}
pts = []
for f in feats:
    p = f['properties']; c = f['geometry']['coordinates']
    proj = g(p,'nepa_project','project')
    pts.append([round(c[1],5), round(c[0],5), g(p,'year') or '', round(float(g(p,'acres') or 0),1),
                ai[g(p,'activity') or ''], (pj[proj] if proj else -1),
                ('p' if g(p,'status')=='planned' else 'c'), ci[g(p,'county') or '']])
out = {'act':acts,'prj':prjs,'co':cos,'pts':pts}
json.dump(out, open(os.path.join(HERE,'facts.json'),'w',encoding='utf-8'), separators=(',',':'))
print('source:', os.path.relpath(src, MAIN))
print('facts pts:', len(pts), '| activities:', len(acts), '| projects:', len(prjs), '| counties:', cos,
      '| acres:', round(sum(p[3] for p in pts),1), '| planned:', sum(1 for p in pts if p[6]=='p'))
