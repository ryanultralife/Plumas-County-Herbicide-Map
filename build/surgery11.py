# surgery11: make Source Data tab statewide+scoped (live app_samples) and add a
# scoped callout to the Herbicides & Science tab. CRLF-safe, string-anchored.
import os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, 'index.html')
s = open(HTML, encoding='utf-8', newline='').read()
shutil.copy(HTML, HTML + '.bak11')
def crlf(x): return x.replace('\r\n', '\n').replace('\n', '\r\n')

# 1) Science scoped callout card (filled by renderSciScope)
sci_anchor = '<div id="sciview"><div class="wrap">'
assert s.count(sci_anchor) == 1, 'sci anchor=' + str(s.count(sci_anchor))
s = s.replace(sci_anchor, sci_anchor + '<div class="card" id="sciScope" style="border-left:4px solid #2E5E3A"></div>', 1)

# 2) Replace the whole #rawview block (Plumas TAB4 table) with a live, scoped sample UI
r0 = s.index('<div id="rawview">')
r1 = s.index('<div id="ledgerview">')
NEWRAW = ('<div id="rawview"><div class="wrap">'
  '<div class="datedbanner"><b>Source data &mdash; record sample.</b> A reviewable sample of the <b>largest reported applications</b> (top 80 per county by amount) for the area chosen in the selector above, drawn live from the project database. The complete dataset is 11.8M+ records; for full county records use the records-request templates in the repo.</div>'
  '<div class="rawctrls">'
  '<input id="rawq" type="search" placeholder="Search ingredient, product, applicator, county…" oninput="rawApply()">'
  '<select id="rawsrc" onchange="rawApply()"><option value="">All sources</option><option value="pur">Private — CA PUR</option><option value="facts">Federal — USFS FACTS</option></select>'
  '<button type="button" onclick="rawCSV()">Download CSV</button>'
  '</div>'
  '<div id="rawcount" class="note"></div>'
  '<div style="overflow:auto;max-height:none"><table class="rawtbl"><thead><tr id="rawhead"></tr></thead><tbody id="rawbody"></tbody></table></div>'
  '</div></div>\r\n')
s = s[:r0] + NEWRAW + s[r1:]

# 3) show() hooks: add sci callout (raw already calls renderRaw)
show_old = " if(v==='data')renderData();"
assert s.count(show_old) == 1, 'show hook=' + str(s.count(show_old))
s = s.replace(show_old, show_old + "\r\n if(v==='sci')renderSciScope();")

# 4) setScope: refresh raw + sci when visible
ss_old = "var dv=document.getElementById('dataview'); if(dv&&dv.style.display!=='none') renderData();"
assert s.count(ss_old) == 1, 'setScope hook=' + str(s.count(ss_old))
ss_new = (ss_old +
  "\r\n  var rv=document.getElementById('rawview'); if(rv&&rv.style.display!=='none'){RAW_ROWS=null; renderRaw();}" +
  "\r\n  var sv=document.getElementById('sciview'); if(sv&&sv.style.display!=='none') renderSciScope();")
s = s.replace(ss_old, ss_new)

# 5) Append new functions before the final </script> (these override the old TAB4 raw fns)
NEWFUNCS = r'''
/* ----- Herbicides & Science: scoped callout ----- */
function renderSciScope(){
  var el=document.getElementById('sciScope'); if(!el) return;
  el.innerHTML='<p style="color:#777;margin:0">Loading…</p>';
  Promise.all([loadCells(),loadJuris()]).then(function(){
    var cs=scopedCells();
    var where=SCOPE.county?SCOPE.county+' County':SCOPE.region?regionLabel(SCOPE.region):'California';
    if(!cs.length){el.innerHTML='<h2>'+where+'</h2><p class="sub">No mapped applications for this area.</p>';return;}
    var byc={}, tot=0;
    cs.forEach(function(p){var b=_byClass(p.c||{});for(var k in b){byc[k]=(byc[k]||0)+b[k][0];}tot+=(+p.n||0);});
    var topClass=Object.keys(byc).sort(function(a,b){return byc[b]-byc[a];})[0]||'';
    var herb=byc.herbicide?Math.round(100*byc.herbicide/tot):0;
    var jr=jurisRow(), topAi=(jr&&jr.top_ai&&jr.top_ai[0])?jr.top_ai[0][0]:null;
    el.innerHTML='<h2>What this means for '+where+'</h2>'+
      '<p><b>'+tot.toLocaleString()+'</b> reported pesticide applications (2020–2026). Most-applied class: <b>'+(topClass||'—').replace('_',' ')+'</b>'+
      (byc.herbicide?' &middot; herbicides are '+herb+'% of applications here':'')+
      (topAi?'. Most-applied active ingredient: <b>'+topAi+'</b>':'')+'.</p>'+
      '<p class="sub">The science below is general; the Plumas examples show how these chemicals play out in one heavily-sprayed area. Use the selector above to re-scope the headline figures.</p>';
  }).catch(function(){el.innerHTML='';});
}

/* ----- Source Data: live, scoped record sample (overrides the old TAB4 table) ----- */
var RAWCOLS2=['Date','County','Active ingredient','Product','Amount','Unit','Method','Applicator','Source'];
var RAW_ROWS=null, RAW_SCOPEKEY=null;
if(typeof _rawSort==='undefined'){var _rawSort=-1, _rawDir=1;}
function rawScopeKey(){return (SCOPE.county||'')+'|'+(SCOPE.region||'');}
function loadSamples(){
  var key=rawScopeKey();
  if(RAW_ROWS && RAW_SCOPEKEY===key) return Promise.resolve(RAW_ROWS);
  var H={apikey:SB_KEY,Authorization:'Bearer '+SB_KEY};
  var url=SB_URL+'/rest/v1/app_samples?select=date,county,region,active_ingredient,product,amount,unit,method,owner,source';
  if(SCOPE.county) url+='&county=eq.'+encodeURIComponent(SCOPE.county);
  else if(SCOPE.region) url+='&region=eq.'+encodeURIComponent(SCOPE.region);
  url+='&limit=6000';
  return fetch(url,{headers:H}).then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(rows){RAW_ROWS=rows;RAW_SCOPEKEY=key;return rows;});
}
function rawRowVals(r){return [r.date||'', r.county||'', r.active_ingredient||'', r.product||'', (r.amount!=null?(+r.amount):''), r.unit||'', r.method||'', applicatorInfo(r.owner).label, (SRC_META[r.source]?SRC_META[r.source].label:(r.source||''))];}
function renderRaw(){
  var head=document.getElementById('rawhead'); if(!head) return;
  head.innerHTML=RAWCOLS2.map(function(c,i){return '<th onclick="rawSort('+i+')">'+c+' ⇅</th>';}).join('');
  var b=document.getElementById('rawbody'); if(b) b.innerHTML='<tr><td colspan="9" style="padding:16px;color:#777">Loading records…</td></tr>';
  loadSamples().then(function(){rawApply();}).catch(function(){var bb=document.getElementById('rawbody'); if(bb) bb.innerHTML='<tr><td colspan="9" style="padding:16px;color:#a00">Records unavailable.</td></tr>';});
}
function rawFiltered(){
  var q=((document.getElementById('rawq')||{}).value||'').toLowerCase(), sf=((document.getElementById('rawsrc')||{}).value||'');
  var rows=(RAW_ROWS||[]).filter(function(r){
    if(sf && r.source!==sf) return false;
    if(q){var s2=(r.date+' '+r.county+' '+r.active_ingredient+' '+r.product+' '+r.method+' '+applicatorInfo(r.owner).label).toLowerCase(); if(s2.indexOf(q)<0) return false;}
    return true;});
  if(_rawSort>=0){var c=_rawSort,d=_rawDir; rows=rows.slice().sort(function(a,b){var x=rawRowVals(a)[c],y=rawRowVals(b)[c]; if(c===4){x=+x||0;y=+y||0;}else{x=(''+x).toLowerCase();y=(''+y).toLowerCase();} return x<y?-d:x>y?d:0;});}
  return rows;
}
function rawSort(i){if(_rawSort===i)_rawDir=-_rawDir;else{_rawSort=i;_rawDir=1;}rawApply();}
function rawApply(){
  var rows=rawFiltered(), cap=2000, n=rows.length, show=Math.min(n,cap), out=[];
  for(var i=0;i<show;i++){var v=rawRowVals(rows[i]); out.push('<tr><td>'+v[0]+'</td><td>'+v[1]+'</td><td>'+v[2]+'</td><td>'+v[3]+'</td><td style="text-align:right">'+(v[4]!==''?(+v[4]).toLocaleString(undefined,{maximumFractionDigits:3}):'')+'</td><td>'+v[5]+'</td><td>'+v[6]+'</td><td>'+v[7]+'</td><td>'+v[8]+'</td></tr>');}
  var b=document.getElementById('rawbody'); if(b) b.innerHTML=out.join('')||'<tr><td colspan="9" style="padding:16px;color:#777">No records match.</td></tr>';
  var where=SCOPE.county?SCOPE.county+' County':SCOPE.region?regionLabel(SCOPE.region):'statewide';
  var el=document.getElementById('rawcount'); if(el) el.textContent='Showing '+show.toLocaleString()+' of '+n.toLocaleString()+' sample records for '+where+' (largest applications per county by amount).';
}
function rawCSV(){
  var rows=rawFiltered(), lines=[RAWCOLS2.join(',')];
  rows.forEach(function(r){var v=rawRowVals(r), cells=v.map(function(x){x=''+(x==null?'':x); return /[",\n]/.test(x)?'"'+x.replace(/"/g,'""')+'"':x;}); lines.push(cells.join(','));});
  var blob=new Blob([lines.join('\n')],{type:'text/csv;charset=utf-8'}); var a=document.createElement('a');
  a.href=URL.createObjectURL(blob); a.download='spraymap_sample_'+((SCOPE.county||SCOPE.region||'statewide').replace(/\s+/g,'_'))+'.csv'; document.body.appendChild(a); a.click(); a.remove();
}
'''
si = s.rindex('</script>')
s = s[:si] + crlf(NEWFUNCS) + s[si:]

open(HTML, 'w', encoding='utf-8', newline='').write(s)
print('OK surgery11. size:', len(s), '| bare LF:', s.count('\n') - s.count('\r\n'))
