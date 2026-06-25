# Round 6: swap in the COMPLETE federal FACTS (440) on map + table; update popup/banner/legend.
import os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT,'index.html'); B = os.path.dirname(os.path.abspath(__file__))
html = open(HTML, encoding='utf-8').read(); shutil.copy(HTML, HTML+'.bak6')
facts = open(os.path.join(B,'facts.json'),encoding='utf-8').read()
tab4  = open(os.path.join(B,'tab4.json'),encoding='utf-8').read()

def rep(old, new):
    global html
    assert html.count(old) == 1, f'MATCH {html.count(old)} for {old[:55]!r}'
    html = html.replace(old, new)

# 1) FACTS blob
i = html.index('var FACTS='); j = html.index('\nfunction popupHtml', i)
html = html[:i] + 'var FACTS=' + facts + ';' + html[j:]

# 2) factsPopup -> use FACTS.co[] for county + "NEPA project" label
FP = r'''function factsPopup(p){var ST={c:'completed',p:'planned'};
var h='<b>Federal land — Plumas National Forest</b><br><span style="color:#777;font-size:12px">USDA Forest Service FACTS (public-land activity record)</span>';
h+='<br><b>Activity:</b> '+(FACTS.act[p[4]]||'—');
if(p[5]>=0&&FACTS.prj[p[5]])h+='<br><b>NEPA project:</b> '+FACTS.prj[p[5]];
h+='<br><b>Year:</b> '+(p[2]||'n/a')+' <span style="color:#777">('+(ST[p[6]]||'')+')</span>';
if(p[3])h+='<br><b>Treated area:</b> '+p[3]+' acres';
h+='<br><b>County:</b> '+(FACTS.co[p[7]]||'');
h+='<br><b>Active ingredient:</b> <i>not in public FACTS data — Region 5 FOIA pending</i>';return h;}
'''
ci = html.index('function factsPopup('); cj = html.index('function buildMap(', ci)
html = html[:ci] + FP + html[cj:]

# 3) TAB4 blob (now 3,484 incl. 440 federal)
ti = html.index('var TAB4='); tj = html.index('\nvar _rawRows=null', ti)
html = html[:ti] + 'var TAB4=' + tab4 + ';' + html[tj:]

# 4) Source Data banner counts
rep('<b>3,340 records:</b> 3,044 private Production-Ag applications (forestry single-job 2021&ndash;2024 + other operators&rsquo; 2024 monthly summaries) and 296 federal Plumas NF treatments (USFS FACTS, 2020&ndash;2025).',
    '<b>3,484 records:</b> 3,044 private Production-Ag applications (forestry single-job 2021&ndash;2024 + other operators&rsquo; 2024 monthly summaries) and 440 federal Plumas NF treatments (USFS FACTS, 2020&ndash;2029, incl. planned).')

# 5) legend date note
rep('Private 2021&ndash;2024 · Federal 2020&ndash;2025</span>',
    'Private 2021&ndash;2024 · Federal 2020&ndash;2029</span>')

open(HTML,'w',encoding='utf-8').write(html)
print('OK round6. size:', len(html))
