# Round 4: add the federal USFS FACTS layer (public land) to the map.
import json, os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT,'index.html'); B = os.path.dirname(os.path.abspath(__file__))
html = open(HTML, encoding='utf-8').read(); shutil.copy(HTML, HTML+'.bak4')
facts = open(os.path.join(B,'facts.json'),encoding='utf-8').read()

def rep(old, new):
    global html
    assert html.count(old) == 1, f'MATCH {html.count(old)} for {old[:60]!r}'
    html = html.replace(old, new)

# 1) embed FACTS data right after the methods/mstyle/towns/vmax declaration
rep('vmax=930.6, map=null;', 'vmax=930.6, map=null;\nvar FACTS=__FACTS__;')
html = html.replace('__FACTS__', facts)

# 2) factsPopup() before buildMap
FP = r'''function factsPopup(p){var ST={c:'completed',p:'planned'},CO={P:'Plumas',B:'Butte',L:'Lassen'};
var h='<b>Federal land — Plumas National Forest</b><br><span style="color:#777;font-size:12px">USDA Forest Service FACTS (public-land activity record)</span>';
h+='<br><b>Activity:</b> '+(FACTS.act[p[4]]||'—');
if(p[5]>=0&&FACTS.prj[p[5]])h+='<br><b>Project:</b> '+FACTS.prj[p[5]];
h+='<br><b>Year:</b> '+(p[2]||'n/a')+' <span style="color:#777">('+(ST[p[6]]||'')+')</span>';
if(p[3])h+='<br><b>Treated area:</b> '+p[3]+' acres';
h+='<br><b>County:</b> '+(CO[p[7]]||p[7]);
h+='<br><b>Active ingredient:</b> <i>not in public FACTS data — Region 5 FOIA pending</i>';return h;}
'''
rep('function buildMap(){', FP+'function buildMap(){')

# 3) build the federal layer inside buildMap, before town labels
FED = (" var fgrp=L.layerGroup();\n"
       " FACTS.pts.forEach(function(p){L.circleMarker([p[0],p[1]],{radius:4+Math.sqrt(p[3]||0)/2.2,color:'#08306b',weight:1,fillColor:'#3182bd',fillOpacity:.8})\n"
       "  .bindPopup(factsPopup(p),{maxWidth:300}).addTo(fgrp);});\n"
       " overlays['Federal · Plumas NF (FACTS, '+FACTS.pts.length+' sites)']=fgrp;fgrp.addTo(map);\n"
       " var tl=L.layerGroup();towns.forEach")
rep(' var tl=L.layerGroup();towns.forEach', FED)

# 4) legend: federal swatch + update the date note
rep('<br><span style="font-size:11px;color:#666">Applications 2021&ndash;2024</span>\'',
    '<br><b>Federal</b><br><span class="ring" style="background:#3182bd;border:1px solid #08306b"></span> Plumas NF (FACTS), sized by acres<br><span style="font-size:11px;color:#666">Private 2021&ndash;2024 · Federal 2020&ndash;2025</span>\'')

open(HTML,'w',encoding='utf-8').write(html)
print('OK round4. size:', len(html))
