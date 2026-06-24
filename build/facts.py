# Build the federal (USFS FACTS) map layer from the scraper's unified export.
# Reads the scraper-owned export (not copied into this branch -> no data duplication).
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))          # build/
WT   = os.path.dirname(HERE)                                # worktree root
MAIN = os.path.abspath(os.path.join(WT, '..', '..', '..')) # main repo root (worktree is <root>/.claude/worktrees/<name>)
CANDS = [os.path.join(WT,'data','exports','northern-sierra.geojson'),
         os.path.join(MAIN,'data','exports','northern-sierra.geojson'),
         os.path.join(os.getcwd(),'data','exports','northern-sierra.geojson')]
src = next((c for c in CANDS if os.path.exists(c)), None)
assert src, 'export not found in: '+str(CANDS)
d = json.load(open(src, encoding='utf-8'))
facts = [f for f in d['features']
         if f['properties'].get('source')=='facts' and f.get('geometry') and f['geometry'].get('coordinates')]
acts = sorted({(f['properties'].get('activity') or '') for f in facts})
prjs = sorted({p for p in (f['properties'].get('project') for f in facts) if p})
ai = {v:i for i,v in enumerate(acts)}; pj = {v:i for i,v in enumerate(prjs)}
CO = {'Plumas':'P','Butte':'B','Lassen':'L'}
pts = []
for f in facts:
    pr = f['properties']; c = f['geometry']['coordinates']
    pts.append([round(c[1],5), round(c[0],5), pr.get('year') or '', round(pr.get('amount') or 0,1),
                ai[pr.get('activity') or ''], (pj[pr['project']] if pr.get('project') else -1),
                ('p' if pr.get('status')=='planned' else 'c'), CO.get(pr.get('county'), pr.get('county') or '')])
out = {'act':acts,'prj':prjs,'pts':pts,'pulled':(facts[0]['properties'].get('pulled','') if facts else '')}
json.dump(out, open(os.path.join(HERE,'facts.json'),'w',encoding='utf-8'), separators=(',',':'))
print('source:', src)
print('facts pts:', len(pts), '| activities:', len(acts), '| projects:', len(prjs),
      '| acres:', round(sum(p[3] for p in pts),1), '| planned:', sum(1 for p in pts if p[6]=='p'))
