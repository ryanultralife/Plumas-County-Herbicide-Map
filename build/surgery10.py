# surgery10: statewide + scoped Data & Trends, region/county scope selector,
# honest applicator-ID decoding. Edits index.html in place (CRLF-safe).
import os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, 'index.html')
s = open(HTML, encoding='utf-8', newline='').read()
shutil.copy(HTML, HTML + '.bak10')
def crlf(x): return x.replace('\r\n', '\n').replace('\n', '\r\n')

ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF5a2h3c2VybW9qc3RpeXJmY252Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIzNTU3MDIsImV4cCI6MjA5NzkzMTcwMn0.XPBmdHPv0CswsHFynPwhjj3DatzlWIXY2DSPGJOz_WQ'

# ---------------------------------------------------------------- new JS block
NEWJS = r'''var map=null, CELLS=null, JURIS=null, OVERLAYS=null;
var SB_URL='https://aykhwsermojstiyrfcnv.supabase.co';
var SB_KEY='__ANON__';
var SCOPE={region:null,county:null};
var SCOPE_REGIONS=[], SCOPE_RC={}, COUNTY_REGION={};
var CLASS_COLORS={herbicide:'#3fae5a',insecticide:'#e0883b',fungicide:'#3f7fe0',fumigant:'#b85cc8',rodenticide:'#c8513f',growth_regulator:'#cac33f',adjuvant:'#6b8276',other:'#9a9a9a',unknown:'#6a6a6a'};
var CLASS_ORDER=['herbicide','insecticide','fungicide','fumigant','rodenticide','growth_regulator','adjuvant','other'];
var SRC_META={pur:{label:'Private - CA PUR',color:'#d6604d'},facts:{label:'Federal - USFS FACTS',color:'#4393c3'},thp:{label:'Timber Harvest Plans',color:'#b2912f'}};
var CA_COUNTY={'01':'Alameda','02':'Alpine','03':'Amador','04':'Butte','05':'Calaveras','06':'Colusa','07':'Contra Costa','08':'Del Norte','09':'El Dorado','10':'Fresno','11':'Glenn','12':'Humboldt','13':'Imperial','14':'Inyo','15':'Kern','16':'Kings','17':'Lake','18':'Lassen','19':'Los Angeles','20':'Madera','21':'Marin','22':'Mariposa','23':'Mendocino','24':'Merced','25':'Modoc','26':'Mono','27':'Monterey','28':'Napa','29':'Nevada','30':'Orange','31':'Placer','32':'Plumas','33':'Riverside','34':'Sacramento','35':'San Benito','36':'San Bernardino','37':'San Diego','38':'San Francisco','39':'San Joaquin','40':'San Luis Obispo','41':'San Mateo','42':'Santa Barbara','43':'Santa Clara','44':'Santa Cruz','45':'Shasta','46':'Sierra','47':'Siskiyou','48':'Solano','49':'Sonoma','50':'Stanislaus','51':'Sutter','52':'Tehama','53':'Trinity','54':'Tulare','55':'Tuolumne','56':'Ventura','57':'Yolo','58':'Yuba'};
// optional resolved-name crosswalk (license / county-CAC), filled in as we confirm names:
var OWNER_NAMES={};

function _byClass(c){var o={};for(var k in c){var cl=k.split('|')[1],v=c[k],n=Array.isArray(v)?v[0]:v,lb=Array.isArray(v)?v[1]:0;if(!o[cl])o[cl]=[0,0];o[cl][0]+=n;o[cl][1]+=lb;}return o;}
function _years(c){var ys=[];for(var k in c){var y=k.split('|')[0];if(y)ys.push(+y);}return ys.length?[Math.min.apply(null,ys),Math.max.apply(null,ys)]:null;}
function _num(v){return Array.isArray(v)?v[0]:v;}
function _fmt(n){return (+n||0).toLocaleString();}
function _lbs(n){n=+n||0;return n>=1e6?(n/1e6).toFixed(n>=1e7?0:1)+'M':n>=1e3?Math.round(n/1e3)+'k':Math.round(n).toString();}
function regionLabel(r){return r?(''+r).replace(/-/g,' ').replace(/\b\w/g,function(c){return c.toUpperCase();}):'';}

/* ----- applicator identity: decode the CDPR operator/permit ID honestly ----- */
function decodeGrowerId(id){
  var s=(''+id).trim(), typ=null, body=s, m=s.match(/^(\d+)([A-Za-z])$/);
  if(m){body=m[1];typ=m[2].toUpperCase();}
  var cc=body.slice(0,2), yy=(body.length>=4?body.slice(2,4):null);
  var county=CA_COUNTY[cc]||null;
  var year=(yy&&/^\d\d$/.test(yy))?(2000+parseInt(yy,10)):null;
  return {county:county, year:year, type:typ, raw:s};
}
function applicatorInfo(id){
  if(id==null||id===''){return {label:'Operator not disclosed in public records',meta:'',tier:'none'};}
  var s=''+id;
  if(OWNER_NAMES[s]){return {label:OWNER_NAMES[s],meta:'name via license / county records',tier:'named'};}
  if(/FOIA|NOT PUBLIC/i.test(s)){return {label:'Operator not disclosed in public records',meta:'',tier:'none'};}
  if(/[A-Za-z]{3,}/.test(s) && !/^\d/.test(s)){return {label:s,meta:'',tier:'named'};}   // e.g. USDA Forest Service
  var d=decodeGrowerId(s);
  if(d.county){
    var meta='CDPR permit'+(d.year?' · '+d.year:'')+(d.type==='R'?' · restricted-materials':'');
    return {label:d.county+' Co. operator #'+s, meta:meta, tier:'decoded'};
  }
  return {label:'Operator #'+s, meta:'CDPR permit', tier:'decoded'};
}
var APPLICATOR_NOTE='California’s public pesticide-use data identifies operators only by a coded CDPR permit number, not a name — the state does not collect operator names; they are held only by county Agricultural Commissioners. We decode each ID to its county, year and permit type.';

function cellPopup(p){
  var byc=_byClass(p.c||{}), yr=_years(p.c||{});
  var h='<b>'+(p.county||'?')+' County</b>'+(p.region?' <span style="color:#777">· '+regionLabel(p.region)+'</span>':'');
  h+='<br><b>'+(+p.n||0).toLocaleString()+'</b> applications'+((+p.lbs)?' · <b>'+(+p.lbs).toLocaleString()+'</b> lb':'')+(yr?' · '+(yr[0]===yr[1]?yr[0]:yr[0]+'–'+yr[1]):'');
  h+='<br><b>By type:</b><ul style="margin:2px 0 3px 15px;padding:0;list-style:none">';
  CLASS_ORDER.concat(['unknown']).forEach(function(cl){if(byc[cl]&&byc[cl][0]){h+='<li><span style="color:'+(CLASS_COLORS[cl]||'#888')+'">●</span> '+cl.replace('_',' ')+' — '+byc[cl][0].toLocaleString()+(byc[cl][1]?' ('+byc[cl][1].toLocaleString()+' lb)':'')+'</li>';}});
  h+='</ul>';
  if(p.ai&&p.ai.length){h+='<b>Top active ingredients:</b><br><span style="color:#444">'+p.ai.slice(0,5).map(function(a){return a[0]+' ('+(+a[1]).toLocaleString()+')';}).join('<br>')+'</span><br>';}
  if(p.src&&Object.keys(p.src).length){var sm=[];Object.keys(p.src).forEach(function(k){sm.push((SRC_META[k]?SRC_META[k].label.replace(/ -.*/,''):k)+' '+_num(p.src[k]).toLocaleString());});h+='<b>Source:</b> '+sm.join(' · ')+'<br>';}
  if(p.owners&&p.owners.length){h+='<b>Top applicators:</b><br><span style="color:#444">'+p.owners.slice(0,5).map(function(o){return applicatorInfo(o[0]).label+' ('+(+o[1]).toLocaleString()+')';}).join('<br>')+'</span>';}
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
function loadJuris(){
  if(JURIS) return Promise.resolve(JURIS);
  var H={apikey:SB_KEY,Authorization:'Bearer '+SB_KEY};
  return fetch(SB_URL+'/rest/v1/juris_agg?select=level,region,county,top_ai,top_owners',{headers:H})
    .then(function(r){if(!r.ok)throw 0;return r.json();})
    .then(function(rows){JURIS=indexJuris(rows);return JURIS;})
    .catch(function(){JURIS=indexJuris([]);return JURIS;});
}
function indexJuris(rows){
  var J={state:null,region:{},county:{}};
  rows.forEach(function(r){if(r.level==='state')J.state=r;else if(r.level==='region')J.region[r.region]=r;else J.county[r.county]=r;});
  return J;
}
function jurisRow(){
  if(!JURIS) return null;
  if(SCOPE.county) return JURIS.county[SCOPE.county]||null;
  if(SCOPE.region) return JURIS.region[SCOPE.region]||null;
  return JURIS.state;
}

/* ----- scope (region / county) ----- */
function buildScopeLists(){
  var regs={}, rc={};
  CELLS.forEach(function(p){if(p.region){regs[p.region]=1;COUNTY_REGION[p.county]=p.region;if(p.county){(rc[p.region]=rc[p.region]||{})[p.county]=1;}}});
  SCOPE_REGIONS=Object.keys(regs).sort();
  SCOPE_RC={};for(var r in rc){SCOPE_RC[r]=Object.keys(rc[r]).sort();}
}
function populateScopeBar(){
  if(!CELLS) return;
  buildScopeLists();
  var rs=document.getElementById('scopeRegion'); if(!rs) return;
  rs.innerHTML='<option value="">All California</option>'+SCOPE_REGIONS.map(function(r){return '<option value="'+r+'">'+regionLabel(r)+'</option>';}).join('');
  rs.value=SCOPE.region||'';
  populateCountyOptions();
}
function populateCountyOptions(){
  var cs=document.getElementById('scopeCounty'); if(!cs) return;
  var list=SCOPE.region?(SCOPE_RC[SCOPE.region]||[]):Object.keys(COUNTY_REGION).sort();
  cs.innerHTML='<option value="">'+(SCOPE.region?'All counties in region':'All counties')+'</option>'+list.map(function(c){return '<option value="'+c+'">'+c+'</option>';}).join('');
  cs.value=SCOPE.county||'';
}
function onScopeRegion(v){setScope(v||null,null);}
function onScopeCounty(v){var r=v?(COUNTY_REGION[v]||SCOPE.region):SCOPE.region; setScope(r,v||null);}
function setScope(region,county){
  SCOPE.region=region||null; SCOPE.county=county||null;
  var rs=document.getElementById('scopeRegion'); if(rs) rs.value=SCOPE.region||'';
  populateCountyOptions();
  var note=document.getElementById('scopeNote');
  if(note) note.textContent=SCOPE.county?(SCOPE.county+' County'):SCOPE.region?regionLabel(SCOPE.region):'Statewide — all 58 counties';
  if(map){rebuildLayers(); fitScope(); updateMapStat();}
  var dv=document.getElementById('dataview'); if(dv&&dv.style.display!=='none') renderData();
}
function scopedCells(){
  if(!CELLS) return [];
  if(SCOPE.county) return CELLS.filter(function(p){return p.county===SCOPE.county;});
  if(SCOPE.region) return CELLS.filter(function(p){return p.region===SCOPE.region;});
  return CELLS;
}

function buildMap(){
  var topo=L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',{maxZoom:17,attribution:'&copy; OpenTopoMap (CC-BY-SA), OpenStreetMap'});
  var carto=L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{attribution:'&copy; OpenStreetMap &copy; CARTO'});
  var sat=L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{attribution:'Esri'});
  map=L.map('map',{center:[37.6,-119.6],zoom:6,preferCanvas:true,layers:[carto]});
  var canvas=L.canvas({padding:0.5});
  var hydro=L.tileLayer('https://basemap.nationalmap.gov/arcgis/rest/services/USGSHydroCached/MapServer/tile/{z}/{y}/{x}',{opacity:.85,maxZoom:16,attribution:'USGS National Map - Hydrography'});
  var overlays={}; var lazy=[];
  function reg(label,builder,on){var g=L.layerGroup();g._builder=builder;overlays[label]=g;if(on){lazy.push(g);}return g;}
  CLASS_ORDER.forEach(function(cl){
    reg('◉ '+cl.replace('_',' '), function(g){scopedCells().forEach(function(p){var cc=_byClass(p.c||{})[cl];if(!cc||!cc[0])return;
      L.circleMarker([p.lat,p.lon],{renderer:canvas,radius:Math.min(2+Math.sqrt(cc[0])/1.3,20),weight:0,fillColor:CLASS_COLORS[cl],fillOpacity:.72}).bindPopup(cellPopup(p),{maxWidth:330}).addTo(g);});}, cl==='herbicide');
  });
  Object.keys(SRC_META).forEach(function(sk){
    reg('▣ '+SRC_META[sk].label, function(g){scopedCells().forEach(function(p){var n=p.src&&p.src[sk]?_num(p.src[sk]):0;if(!n)return;
      L.circleMarker([p.lat,p.lon],{renderer:canvas,radius:Math.min(2+Math.sqrt(n)/1.3,20),color:SRC_META[sk].color,weight:1,fill:false,opacity:.7}).bindPopup(cellPopup(p),{maxWidth:330}).addTo(g);});});
  });
  overlays['Streams & water (USGS)']=hydro;
  OVERLAYS=overlays;
  function ensure(g){if(g&&g._builder&&!g._built){g._builder(g);g._built=true;}}
  map.on('overlayadd',function(e){ensure(e.layer);});
  L.control.layers({'Streets (CARTO)':carto,'Topographic':topo,'Satellite':sat},overlays,{collapsed:true}).addTo(map);
  var lg=L.control({position:'bottomright'});lg.onAdd=function(){var d=L.DomUtil.create('div','legend');
    var rows=CLASS_ORDER.map(function(cl){return '<span class="ring" style="background:'+CLASS_COLORS[cl]+';border:0"></span> '+cl.replace('_',' ');}).join('<br>');
    d.innerHTML='<b>Pesticide class</b> <span style="color:#888">(◉ layers)</span><br>'+rows+'<br><span style="font-size:11px;color:#666">▣ source layers · dot size = count · CA 2020+</span>';return d;};lg.addTo(map);
  document.getElementById('mapStat')&&(document.getElementById('mapStat').textContent='Loading statewide data…');
  loadCells().then(function(){
    lazy.forEach(function(g){ensure(g);g.addTo(map);});
    populateScopeBar(); updateMapStat(); fitScope();
    setTimeout(function(){map.invalidateSize(true);},80);
  }).catch(function(e){var el=document.getElementById('mapStat');if(el)el.textContent='Map data unavailable.';});
}
function rebuildLayers(){
  if(!OVERLAYS) return;
  for(var label in OVERLAYS){var g=OVERLAYS[label];if(g&&g._builder&&g._built){g.clearLayers();g._builder(g);}}
}
function fitScope(){
  if(!map) return;
  var cs=scopedCells();
  if((SCOPE.region||SCOPE.county)&&cs.length){
    var lats=cs.map(function(p){return p.lat;}), lons=cs.map(function(p){return p.lon;});
    map.fitBounds([[Math.min.apply(null,lats),Math.min.apply(null,lons)],[Math.max.apply(null,lats),Math.max.apply(null,lons)]],{padding:[28,28],maxZoom:11});
  } else { map.setView([37.6,-119.6],6); }
}
function updateMapStat(){
  var el=document.getElementById('mapStat'); if(!el) return;
  var cs=scopedCells(), tot=cs.reduce(function(a,p){return a+(+p.n||0);},0);
  var where=SCOPE.county?SCOPE.county+' County':SCOPE.region?regionLabel(SCOPE.region):'statewide';
  el.innerHTML='<b>'+tot.toLocaleString()+'</b> applications · <b>'+cs.length.toLocaleString()+'</b> mapped sections · '+where+' · 2020+';
}

/* ----- Data & Trends (statewide + scoped) ----- */
function barRows(items){
  var max=items.reduce(function(m,it){return Math.max(m,it[1]);},0)||1;
  return '<div class="bars">'+items.map(function(it){
    var w=Math.max(2,Math.round(100*it[1]/max));
    return '<div class="bar"><span class="bl">'+it[0]+'</span><span class="bt"><span class="bf" style="width:'+w+'%;background:'+(it[3]||'#2E5E3A')+'"></span></span><span class="bv">'+_fmt(it[1])+(it[2]?' <span class="bsub">'+it[2]+'</span>':'')+'</span></div>';
  }).join('')+'</div>';
}
function mergeTops(cs,key){
  var m={};cs.forEach(function(p){(p[key]||[]).forEach(function(a){m[a[0]]=(m[a[0]]||0)+(+a[1]||0);});});
  return Object.keys(m).map(function(k){return [k,m[k]];}).sort(function(a,b){return b[1]-a[1];}).slice(0,20);
}
var _dataInit=false;
function renderData(){
  var wrap=document.getElementById('dataWrap'); if(!wrap) return;
  if(!_dataInit){wrap.innerHTML='<p style="color:#777;padding:24px 0">Loading statewide data…</p>';}
  Promise.all([loadCells(),loadJuris()]).then(function(){
    _dataInit=true;
    if(!document.getElementById('scopeRegion')||!document.getElementById('scopeRegion').options.length) populateScopeBar();
    wrap.innerHTML=renderDataHtml();
  }).catch(function(){wrap.innerHTML='<p style="color:#a00;padding:24px 0">Data unavailable. Try reloading.</p>';});
}
function renderDataHtml(){
  var cs=scopedCells(), jr=jurisRow();
  var where=SCOPE.county?SCOPE.county+' County':SCOPE.region?regionLabel(SCOPE.region)+' region':'All California';
  var byYear={},byClass={},byLand={},bySrc={},totN=0,totLbs=0;
  cs.forEach(function(p){
    totN+=(+p.n||0); totLbs+=(+p.lbs||0);
    var c=p.c||{};
    for(var k in c){var pa=k.split('|'),y=pa[0],cl=pa[1]||'unknown',ld=pa[2]||'unknown',v=c[k],n=Array.isArray(v)?v[0]:v,lb=Array.isArray(v)?v[1]:0;
      if(y){byYear[y]=byYear[y]||[0,0];byYear[y][0]+=n;byYear[y][1]+=lb;}
      byClass[cl]=byClass[cl]||[0,0];byClass[cl][0]+=n;byClass[cl][1]+=lb;
      byLand[ld]=byLand[ld]||[0,0];byLand[ld][0]+=n;byLand[ld][1]+=lb;}
    var sc=p.src||{};
    for(var sk in sc){var sv=sc[sk];bySrc[sk]=bySrc[sk]||[0,0];bySrc[sk][0]+=(Array.isArray(sv)?sv[0]:sv);if(Array.isArray(sv))bySrc[sk][1]+=sv[1];}
  });
  var yk=Object.keys(byYear).sort();
  var clk=Object.keys(byClass).sort(function(a,b){return byClass[b][0]-byClass[a][0];});
  var ldk=Object.keys(byLand).sort(function(a,b){return byLand[b][0]-byLand[a][0];}).slice(0,8);
  var srk=Object.keys(bySrc).sort(function(a,b){return bySrc[b][0]-bySrc[a][0];});
  var topAi=(jr&&jr.top_ai&&jr.top_ai.length)?jr.top_ai:mergeTops(cs,'ai');
  var topOwn=(jr&&jr.top_owners&&jr.top_owners.length)?jr.top_owners:mergeTops(cs,'owners');
  var yrspan=yk.length?(yk[0]===yk[yk.length-1]?yk[0]:yk[0]+'–'+yk[yk.length-1]):'—';

  var h=[];
  h.push('<div class="card"><h2>'+where+' — reported pesticide use</h2>');
  h.push('<p class="sub">What the public data shows for the mapped area. Use the selector above to focus on a region or county.</p>');
  h.push('<div class="datedbanner"><b>Mapped snapshot.</b> '+_fmt(totN)+' geocoded pesticide applications ('+yrspan+') from CA Pesticide Use Reports + federal USFS records. Records without usable coordinates are not mapped here; pounds are summed only where the report unit is pounds.</div></div>');

  h.push('<div class="kpis">');
  h.push('<div class="kpi"><div class="n">'+_fmt(totN)+'</div><div class="l">Mapped applications</div></div>');
  h.push('<div class="kpi"><div class="n">'+_lbs(totLbs)+' lb</div><div class="l">Reported pounds applied</div></div>');
  h.push('<div class="kpi"><div class="n">'+_fmt(cs.length)+'</div><div class="l">Mapped ~sections</div></div>');
  h.push('<div class="kpi"><div class="n">'+yrspan+'</div><div class="l">Years covered</div></div>');
  h.push('</div>');

  if(yk.length){h.push('<div class="card"><h2>Applications by year</h2>'+barRows(yk.map(function(y){return [y,byYear[y][0],(byYear[y][1]?_lbs(byYear[y][1])+' lb':''),'#2E5E3A'];}))+'</div>');}

  h.push('<div class="card"><h2>By pesticide class</h2>'+barRows(clk.map(function(cl){return [cl.replace('_',' '),byClass[cl][0],(byClass[cl][1]?_lbs(byClass[cl][1])+' lb':''),CLASS_COLORS[cl]||'#888'];}))+'<p class="note">Class is inferred from the active ingredient.</p></div>');

  if(srk.length){h.push('<div class="card"><h2>By data source</h2>'+barRows(srk.map(function(sk){return [(SRC_META[sk]?SRC_META[sk].label:sk),bySrc[sk][0],'',(SRC_META[sk]?SRC_META[sk].color:'#888')];}))+'</div>');}

  if(ldk.length){h.push('<div class="card"><h2>By land / site type</h2>'+barRows(ldk.map(function(ld){return [ld,byLand[ld][0],'','#6b8276'];}))+'</div>');}

  h.push('<div class="card"><h2>Top active ingredients</h2><table><thead><tr><th>#</th><th>Active ingredient</th><th>Applications</th></tr></thead><tbody>'+
    topAi.slice(0,15).map(function(a,i){return '<tr><td>'+(i+1)+'</td><td>'+a[0]+'</td><td>'+_fmt(a[1])+'</td></tr>';}).join('')+'</tbody></table></div>');

  h.push('<div class="card"><h2>Top applicators</h2><table><thead><tr><th>#</th><th>Operator</th><th>Applications</th></tr></thead><tbody>'+
    topOwn.slice(0,15).map(function(o,i){var inf=applicatorInfo(o[0]);return '<tr><td>'+(i+1)+'</td><td>'+inf.label+(inf.meta?' <span class="om1">'+inf.meta+'</span>':'')+'</td><td>'+_fmt(o[1])+'</td></tr>';}).join('')+
    '</tbody></table><p class="note">'+APPLICATOR_NOTE+'</p></div>');

  return h.join('');
}
'''.replace('__ANON__', ANON)

# ---------------------------------------------------------------- new CSS
NEWCSS = r'''
#scopebar{position:fixed;top:46px;left:0;right:0;height:36px;background:#eef3ee;border-bottom:1px solid #cdd8cd;z-index:1900;display:flex;align-items:center;gap:8px;padding:0 10px;font:13px Arial;box-shadow:0 1px 3px rgba(0,0,0,.12)}
#scopebar .sl{color:#1d3f27;font-weight:bold;flex:0 0 auto}
#scopebar select{font-size:13px;padding:4px 6px;border:1px solid #b9c7b9;border-radius:6px;background:#fff;max-width:40%}
#scopebar button{font-size:12px;padding:4px 9px;border:1px solid #2E5E3A;background:#2E5E3A;color:#fff;border-radius:6px;cursor:pointer;flex:0 0 auto}
#scopebar .sn{color:#666;font-size:12px;margin-left:auto;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:0 1 auto}
.bars{margin:6px 0}
.bar{display:flex;align-items:center;gap:8px;margin:3px 0;font-size:12.5px}
.bar .bl{flex:0 0 32%;text-align:left;color:#333;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-transform:capitalize}
.bar .bt{flex:1;background:#eef0ee;border-radius:4px;height:14px;position:relative}
.bar .bf{position:absolute;left:0;top:0;bottom:0;border-radius:4px}
.bar .bv{flex:0 0 96px;text-align:right;color:#444;font-variant-numeric:tabular-nums}
.bar .bsub{color:#9a9a9a;font-size:11px}
.om1{color:#8a8a8a;font-size:11px;display:block}
@media(max-width:560px){#scopebar .sl{display:none}#scopebar select{max-width:38%}}
'''

# ============================ apply edits ============================
# 1) views top:46 -> 82 (leave room for the scope bar) ; add scope bar styles
a = "#mapview,#dataview,#sciview,#ledgerview{position:fixed;top:46px;left:0;right:0;bottom:0}"
b = "#mapview,#dataview,#sciview,#ledgerview{position:fixed;top:82px;left:0;right:0;bottom:0}"
assert s.count(a) == 1, 'views rule count=' + str(s.count(a))
s = s.replace(a, b)

a2 = "#rawview{position:fixed;top:46px;left:0;right:0;bottom:0;"
b2 = "#rawview{position:fixed;top:82px;left:0;right:0;bottom:0;"
assert s.count(a2) == 1, 'rawview rule count=' + str(s.count(a2))
s = s.replace(a2, b2)

_si = s.index('</style>')   # first (main layout) style block
s = s[:_si] + crlf(NEWCSS) + s[_si:]

# 2) insert the scope bar before #mapview
mv = '<div id="mapview">'
SCOPEBAR = ('<div id="scopebar"><span class="sl">Showing:</span>'
            '<select id="scopeRegion" onchange="onScopeRegion(this.value)" aria-label="Region"><option value="">All California</option></select>'
            '<select id="scopeCounty" onchange="onScopeCounty(this.value)" aria-label="County"><option value="">All counties</option></select>'
            '<button type="button" onclick="onScopeRegion(\'\')">Statewide</button>'
            '<span id="scopeNote" class="sn">Statewide — all 58 counties</span></div>')
assert s.count(mv) == 1
s = s.replace(mv, SCOPEBAR + mv, 1)

# 3) replace the #dataview content (Plumas embedded) with a dynamic container
d0 = s.index('<div id="dataview">')
d1 = s.index('<div id="sciview">')
NEWDATA = '<div id="dataview"><div class="wrap" id="dataWrap"><p style="color:#777;padding:24px 0">Loading statewide data…</p></div></div>\r\n'
s = s[:d0] + NEWDATA + s[d1:]

# 4) replace the JS map block with the new scoped block
j0 = s.index('var map=null, CELLS=null')
j1 = s.index('function show(v){')
assert j0 < j1, 'js block boundaries'
s = s[:j0] + crlf(NEWJS) + s[j1:]

# 5) wire show('data') to render
old_show = " if(v==='ledger')loadLedger();"
new_show = " if(v==='ledger')loadLedger();\r\n if(v==='data')renderData();"
assert s.count(old_show) == 1, 'show hook count=' + str(s.count(old_show))
s = s.replace(old_show, new_show)

open(HTML, 'w', encoding='utf-8', newline='').write(s)
bare = s.count('\n') - s.count('\r\n')
print('OK surgery10. new size:', len(s), '| bare LF:', bare)
