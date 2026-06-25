# Rewrite index.html's #mapview to a statewide Supabase-backed map:
# class layers + source layers + streams overlay, rich per-section popups. Keeps the tabs.
import os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, 'index.html')
s = open(HTML, encoding='utf-8', newline='').read()
shutil.copy(HTML, HTML+'.bak9')
def crlf(x): return x.replace('\n', '\r\n')

ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF5a2h3c2VybW9qc3RpeXJmY252Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIzNTU3MDIsImV4cCI6MjA5NzkzMTcwMn0.XPBmdHPv0CswsHFynPwhjj3DatzlWIXY2DSPGJOz_WQ'

NEW = r'''var map=null, CELLS=null;
var SB_URL='https://aykhwsermojstiyrfcnv.supabase.co';
var SB_KEY='__ANON__';
var CLASS_COLORS={herbicide:'#3fae5a',insecticide:'#e0883b',fungicide:'#3f7fe0',fumigant:'#b85cc8',rodenticide:'#c8513f',growth_regulator:'#cac33f',adjuvant:'#6b8276',other:'#9a9a9a',unknown:'#6a6a6a'};
var CLASS_ORDER=['herbicide','insecticide','fungicide','fumigant','rodenticide','growth_regulator','adjuvant','other'];
var SRC_META={pur:{label:'Private — CA PUR',color:'#d6604d'},facts:{label:'Federal — USFS FACTS',color:'#4393c3'},thp:{label:'Timber Harvest Plans',color:'#b2912f'}};
function _byClass(c){var o={};for(var k in c){var cl=k.split('|')[1],v=c[k],n=Array.isArray(v)?v[0]:v,lb=Array.isArray(v)?v[1]:0;if(!o[cl])o[cl]=[0,0];o[cl][0]+=n;o[cl][1]+=lb;}return o;}
function _years(c){var ys=[];for(var k in c){var y=k.split('|')[0];if(y)ys.push(+y);}return ys.length?[Math.min.apply(null,ys),Math.max.apply(null,ys)]:null;}
function _num(v){return Array.isArray(v)?v[0]:v;}
function cellPopup(p){
  var byc=_byClass(p.c||{}), yr=_years(p.c||{});
  var h='<b>'+(p.county||'?')+' County</b>'+(p.region?' <span style="color:#777">· '+p.region+'</span>':'');
  h+='<br><b>'+(+p.n||0).toLocaleString()+'</b> applications'+((+p.lbs)?' · <b>'+(+p.lbs).toLocaleString()+'</b> lb':'')+(yr?' · '+(yr[0]===yr[1]?yr[0]:yr[0]+'–'+yr[1]):'');
  h+='<br><b>By type:</b><ul style="margin:2px 0 3px 15px;padding:0;list-style:none">';
  CLASS_ORDER.concat(['unknown']).forEach(function(cl){if(byc[cl]&&byc[cl][0]){h+='<li><span style="color:'+(CLASS_COLORS[cl]||'#888')+'">●</span> '+cl.replace('_',' ')+' — '+byc[cl][0].toLocaleString()+(byc[cl][1]?' ('+byc[cl][1].toLocaleString()+' lb)':'')+'</li>';}});
  h+='</ul>';
  if(p.ai&&p.ai.length){h+='<b>Top active ingredients:</b><br><span style="color:#444">'+p.ai.slice(0,5).map(function(a){return a[0]+' ('+(+a[1]).toLocaleString()+')';}).join('<br>')+'</span><br>';}
  if(p.src&&Object.keys(p.src).length){var sm=[];Object.keys(p.src).forEach(function(k){sm.push((SRC_META[k]?SRC_META[k].label.replace(/ —.*/,''):k)+' '+_num(p.src[k]).toLocaleString());});h+='<b>Source:</b> '+sm.join(' · ')+'<br>';}
  if(p.owners&&p.owners.length){h+='<b>Top applicators:</b><br><span style="color:#444">'+p.owners.slice(0,5).map(function(o){return o[0]+' ('+(+o[1]).toLocaleString()+')';}).join('<br>')+'</span>';}
  return h;
}
function loadCells(){
  if(CELLS) return Promise.resolve(CELLS);
  var H={apikey:SB_KEY,Authorization:'Bearer '+SB_KEY};
  function page(from,acc){
    return fetch(SB_URL+'/rest/v1/map_agg?select=lat,lon,county,region,n,lbs,c,ai,src,owners',{headers:Object.assign({Range:from+'-'+(from+999)},H)})
      .then(function(r){if(!r.ok)throw 0;return r.json();})
      .then(function(rows){acc=acc.concat(rows);return rows.length<1000?acc:page(from+1000,acc);});
  }
  return page(0,[]).then(function(rows){if(!rows.length)throw 0;CELLS=rows;return CELLS;})
    .catch(function(){return fetch('data/agg/aggregated.geojson').then(function(r){return r.json();}).then(function(g){
      CELLS=g.features.map(function(f){var o=Object.assign({},f.properties);o.lat=f.geometry.coordinates[1];o.lon=f.geometry.coordinates[0];return o;});return CELLS;});});
}
function buildMap(){
  var topo=L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',{maxZoom:17,attribution:'&copy; OpenTopoMap (CC-BY-SA), OpenStreetMap'});
  var carto=L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{attribution:'&copy; OpenStreetMap &copy; CARTO'});
  var sat=L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{attribution:'Esri'});
  map=L.map('map',{center:[37.6,-119.6],zoom:6,preferCanvas:true,layers:[carto]});
  var canvas=L.canvas({padding:0.5});
  var hydro=L.tileLayer('https://basemap.nationalmap.gov/arcgis/rest/services/USGSHydroCached/MapServer/tile/{z}/{y}/{x}',{opacity:.85,maxZoom:16,attribution:'USGS National Map — Hydrography'});
  var overlays={}; var lazy=[];
  function reg(label,builder,on){var g=L.layerGroup();g._builder=builder;overlays[label]=g;if(on){lazy.push(g);}return g;}
  CLASS_ORDER.forEach(function(cl){
    reg('◉ '+cl.replace('_',' '), function(g){CELLS.forEach(function(p){var cc=_byClass(p.c||{})[cl];if(!cc||!cc[0])return;
      L.circleMarker([p.lat,p.lon],{renderer:canvas,radius:Math.min(2+Math.sqrt(cc[0])/1.3,20),weight:0,fillColor:CLASS_COLORS[cl],fillOpacity:.72}).bindPopup(cellPopup(p),{maxWidth:330}).addTo(g);});}, cl==='herbicide');
  });
  Object.keys(SRC_META).forEach(function(sk){
    reg('▣ '+SRC_META[sk].label, function(g){CELLS.forEach(function(p){var n=p.src&&p.src[sk]?_num(p.src[sk]):0;if(!n)return;
      L.circleMarker([p.lat,p.lon],{renderer:canvas,radius:Math.min(2+Math.sqrt(n)/1.3,20),weight:0,color:SRC_META[sk].color,weight:1,fill:false,opacity:.7}).bindPopup(cellPopup(p),{maxWidth:330}).addTo(g);});});
  });
  overlays['Streams & water (USGS)']=hydro;
  function ensure(g){if(g&&g._builder&&!g._built){g._builder(g);g._built=true;}}
  map.on('overlayadd',function(e){ensure(e.layer);});
  L.control.layers({'Streets (CARTO)':carto,'Topographic':topo,'Satellite':sat},overlays,{collapsed:true}).addTo(map);
  var lg=L.control({position:'bottomright'});lg.onAdd=function(){var d=L.DomUtil.create('div','legend');
    var rows=CLASS_ORDER.map(function(cl){return '<span class="ring" style="background:'+CLASS_COLORS[cl]+';border:0"></span> '+cl.replace('_',' ');}).join('<br>');
    d.innerHTML='<b>Pesticide class</b> <span style="color:#888">(◉ layers)</span><br>'+rows+'<br><span style="font-size:11px;color:#666">▣ source layers · dot size = count · CA 2020+</span>';return d;};lg.addTo(map);
  document.getElementById('mapStat')&&(document.getElementById('mapStat').textContent='Loading statewide data…');
  loadCells().then(function(){
    lazy.forEach(function(g){ensure(g);g.addTo(map);});
    var tot=CELLS.reduce(function(a,p){return a+(+p.n||0);},0);
    var el=document.getElementById('mapStat'); if(el) el.innerHTML='<b>'+tot.toLocaleString()+'</b> pesticide applications · <b>'+CELLS.length.toLocaleString()+'</b> mapped sections statewide · 2020+';
    setTimeout(function(){map.invalidateSize(true);},80);
  }).catch(function(e){var el=document.getElementById('mapStat');if(el)el.textContent='Map data unavailable.';});
}
'''.replace('__ANON__', ANON)

# add a stat bar to the map view (top-center, clear of zoom/layers/legend/donate)
mv_old = '<div id="mapview"><div id="map"></div></div>'
mv_new = ('<div id="mapview"><div id="map"></div>'
          '<div id="mapStat" style="position:absolute;left:50%;transform:translateX(-50%);top:8px;z-index:1500;'
          'background:rgba(255,255,255,.93);border-radius:8px;padding:5px 12px;font:13px Arial;color:#1d3f27;'
          'box-shadow:0 1px 5px rgba(0,0,0,.3);white-space:nowrap">Loading…</div></div>')
assert s.count(mv_old) == 1, 'mapview anchor count=' + str(s.count(mv_old))
s = s.replace(mv_old, mv_new)

i = s.index('var methods=')
j = s.index('function show(v){')
old = s[i:j]
assert 'var methods=' in old and 'function buildMap' in old, 'boundary check failed'
s = s[:i] + crlf(NEW) + s[j:]
open(HTML, 'w', encoding='utf-8', newline='').write(s)
print('OK surgery9. new size:', len(s), '| CRLF kept (bare LF):', s.count('\n')-s.count('\r\n'))
