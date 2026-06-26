# surgery12: add a brown "Spray intensity" map layer (default-on, visual effect)
# and load the operator_names crosswalk so real applicator names appear when present.
import os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, 'index.html')
s = open(HTML, encoding='utf-8', newline='').read()
shutil.copy(HTML, HTML + '.bak12')

# 1) classes no longer default-on (the brown intensity layer becomes the opening view)
a = "}, cl==='herbicide');"
assert s.count(a) == 1, 'herbicide default anchor=' + str(s.count(a))
s = s.replace(a, "}, false);")

# 2) register the brown intensity overlay (default ON) just before the Streams overlay
streams = "overlays['Streams & water (USGS)']=hydro;"
assert s.count(streams) == 1, 'streams anchor=' + str(s.count(streams))
brown = ("reg('▦ Spray intensity (all)', function(g){scopedCells().forEach(function(p){var t=+p.n||0;if(!t)return;"
         "L.circleMarker([p.lat,p.lon],{renderer:canvas,radius:Math.min(3+Math.sqrt(t)/1.2,24),weight:0,"
         "fillColor:'#6b4423',fillOpacity:.5}).bindPopup(cellPopup(p),{maxWidth:330}).addTo(g);});}, true);\r\n  ")
s = s.replace(streams, brown + streams)

# 3) legend note mentions the brown layer
leg = "▣ source layers · dot size = count · CA 2020+"
assert s.count(leg) == 1, 'legend anchor=' + str(s.count(leg))
s = s.replace(leg, "▦ brown = total spray intensity · ▣ source layers · dot size = count · CA 2020+")

# 4) kick off the operator-name crosswalk load when the map builds
ov = "OVERLAYS=overlays;"
assert s.count(ov) == 1, 'overlays anchor=' + str(s.count(ov))
s = s.replace(ov, "OVERLAYS=overlays; loadOperatorNames();")

# 5) define loadOperatorNames() before indexJuris()
ij = "function indexJuris(rows){"
assert s.count(ij) == 1, 'indexJuris anchor=' + str(s.count(ij))
LOADOP = ("var OPNAMES_LOADED=false;\r\n"
  "function loadOperatorNames(){\r\n"
  "  if(OPNAMES_LOADED) return Promise.resolve(OWNER_NAMES);\r\n"
  "  OPNAMES_LOADED=true;\r\n"
  "  var H={apikey:SB_KEY,Authorization:'Bearer '+SB_KEY};\r\n"
  "  return fetch(SB_URL+'/rest/v1/operator_names?select=operator_id,name',{headers:H})\r\n"
  "    .then(function(r){if(!r.ok)throw 0;return r.json();})\r\n"
  "    .then(function(rows){rows.forEach(function(o){if(o.operator_id&&o.name)OWNER_NAMES[o.operator_id]=o.name;});return OWNER_NAMES;})\r\n"
  "    .catch(function(){return OWNER_NAMES;});\r\n"
  "}\r\n")
s = s.replace(ij, LOADOP + ij)

# 6) make Data & Trends / Science / Source Data also wait on operator names
s = s.replace("Promise.all([loadCells(),loadJuris()]).then(function(){\r\n    _dataInit=true;",
              "Promise.all([loadCells(),loadJuris(),loadOperatorNames()]).then(function(){\r\n    _dataInit=true;")
s = s.replace("Promise.all([loadCells(),loadJuris()]).then(function(){\r\n    var cs=scopedCells();",
              "Promise.all([loadCells(),loadJuris(),loadOperatorNames()]).then(function(){\r\n    var cs=scopedCells();")
s = s.replace("loadSamples().then(function(){rawApply();})",
              "Promise.all([loadSamples(),loadOperatorNames()]).then(function(){rawApply();})")

open(HTML, 'w', encoding='utf-8', newline='').write(s)
print('OK surgery12. size:', len(s), '| bare LF:', s.count('\n') - s.count('\r\n'))
