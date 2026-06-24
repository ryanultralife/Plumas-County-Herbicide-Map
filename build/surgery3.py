# Round 3: combined dataset on the map (source layers, typed popups, acres) + Source Data tab rebuild.
import json, os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT,'index.html'); B = os.path.dirname(os.path.abspath(__file__))
html = open(HTML, encoding='utf-8').read(); shutil.copy(HTML, HTML+'.bak3')
methods = json.load(open(os.path.join(B,'methods.json'),encoding='utf-8'))['methods']
tab4 = open(os.path.join(B,'tab4.json'),encoding='utf-8').read()

def cut(start_anchor, end_anchor, include_end, newtext, after=None):
    """Replace html[i:j] where i=start of start_anchor, j=end of end_anchor (or start of it)."""
    global html
    i = html.index(start_anchor)
    j0 = html.index(end_anchor, i + len(start_anchor) if after is None else i+after)
    j = j0 + (len(end_anchor) if include_end else 0)
    html = html[:i] + newtext + html[j:]

def rep(old, new):
    global html
    assert html.count(old) == 1, f'MATCH {html.count(old)} for {old[:60]!r}'
    html = html.replace(old, new)

# 1) methods blob
cut('var methods=', ', mstyle=', False, 'var methods='+json.dumps(methods, separators=(',',':')))

# 2) popupHtml (typed, with acres, empty-date safe)
POPUP = r'''function popupHtml(layer,p){var TN={H:'Herbicides',I:'Insecticides',F:'Fungicides',P:'Plant growth regulators',O:'Other'},ORD=['H','I','F','P','O'];
var dt=(!p.D0)?'not specified':(p.D0===p.D1?p.D0:p.D0+' – '+p.D1);
var h='<b>'+layer+'</b><br><b>Method:</b> '+p.Method+'<br><b>Dates applied:</b> '+dt;
if(p.Chems&&p.Chems.length){ORD.forEach(function(tc){var lst=p.Chems.filter(function(c){return c[4]===tc;});if(!lst.length)return;
 h+='<br><b>'+TN[tc]+':</b><ul style="margin:2px 0 2px 16px;padding:0">';
 lst.forEach(function(c){var a=[];if(c[1])a.push(c[1]+' gal');if(c[2])a.push(c[2]+' lb');
  h+='<li>'+c[0]+' — '+a.join(' + ')+' <span style="color:#777">('+c[3]+(c[3]>1?' apps':' app')+')</span></li>';});
 h+='</ul>';});}else{h+='<br><i>no pesticides recorded</i><br>';}
if(p.Adj>0)h+='<span style="color:#777;font-size:12px">+ '+p.Adj+' gal adjuvants/surfactants (not pesticides)</span><br>';
var tot=[];if(p.Gallons>0)tot.push(p.Gallons+' gal');if(p.Pounds>0)tot.push(p.Pounds+' lb');
h+='<b>Total here:</b> '+(tot.join(' · ')||'0')+' · '+p.Apps+(p.Apps>1?' applications':' application');
if(p.Acres>0)h+='<br><b>Treated area:</b> '+p.Acres+' acre-treatments';
h+='<br><b>Permittee(s):</b> '+p.Permittees;return h;}
'''
cut('function popupHtml(', 'function buildMap(){', False, POPUP)

# 3) overlays loop -> layers keyed by source, stroke by method
OVERLAYS = r'''var overlays={};
 Object.keys(methods).forEach(function(layer){var grp=L.layerGroup();
  methods[layer].forEach(function(p){var st=mstyle[p.Method]||{stroke:'#888',w:0.8};
   L.circleMarker([p.Lat,p.Lon],{radius:4+Math.sqrt(p.Gallons)/3.5,color:st.stroke,weight:st.w,fillColor:col(p.Gallons),fillOpacity:.85})
    .bindPopup(popupHtml(layer,p),{maxWidth:340,minWidth:215}).addTo(grp);});
  var n=methods[layer].reduce(function(a,p){return a+p.Apps;},0);overlays[layer+' ('+n+' apps)']=grp;grp.addTo(map);});'''
cut('var overlays={};', 'if(st.on)grp.addTo(map);});', True, OVERLAYS)

# 4) Source Data tab: type filter options + a report (source) filter
rep('<select id="rawtype" onchange="rawApply()"><option value="">All types</option><option value="H">Herbicides</option><option value="A">Adjuvants/surfactants</option><option value="I">Insecticides</option></select>',
    '<select id="rawtype" onchange="rawApply()"><option value="">All types</option><option value="H">Herbicides</option><option value="I">Insecticides</option><option value="F">Fungicides</option><option value="P">Plant growth regulators</option><option value="A">Adjuvants/surfactants</option><option value="O">Other</option></select>'
    '<select id="rawreport" onchange="rawApply()"><option value="">All sources</option><option>Forestry (single-job)</option><option>Other operators (monthly)</option></select>')

# 5) Source Data banner text
rep('<b>2,800 records, 29 Jul 2021 &ndash; 2 Nov 2024.</b> Not real-time; the record ends in late 2024. Active ingredients are derived from the EPA registration numbers so you can verify them.',
    '<b>3,044 located applications</b> from both Production-Ag reports: forestry single-job (2021&ndash;2024) plus other operators&rsquo; 2024 monthly summaries. Not real-time. Active ingredients are derived from the EPA registration numbers so you can verify them. (Non-production-ag records have no location and aren&rsquo;t mapped; the raw files are in the repo&rsquo;s <code>data/</code> folder.)')

# 6) Data tab banner: note the map/source include more than the forestry charts
rep('any &lsquo;growth&rsquo; describes that window only.</div>',
    'any &lsquo;growth&rsquo; describes that window only. These charts cover the <b>timber/forestry</b> (single-job) records; the <b>Map</b> and <b>Source Data</b> tabs also include other operators&rsquo; 2024 applications.</div>')

# 7) TAB4 data + renderRaw rebuilt for the new 14-column schema
TAB4JS = '\nvar TAB4=__TAB4__;\n' + r'''var _rawRows=null,_rawSort=0,_rawDir=-1;
function _rawDecode(){if(_rawRows)return _rawRows;var T=TAB4,o=[];
 for(var i=0;i<T.rows.length;i++){var r=T.rows[i],pm=T.prodMeta[r[3]]||['',-1,''];
  o.push([r[0],r[1],T.perm[r[2]]||'',T.prod[r[3]]||'',pm[0]||'',T.ai[pm[1]]||'',(T.typeName[pm[2]]||pm[2]||''),r[4],T.unit[r[5]]||'',T.meth[r[6]]||'',r[9],T.appl[r[7]]||'',T.report[r[10]]||'',r[8]||'',pm[2]||'']);}
 _rawRows=o;return o;}
var RAWCOLS=['Date','Location (MTRS)','Permittee','Product','EPA Reg','Active ingredient','Type','Qty','Units','Method','Acres','Applicator','Source','Site'];
var RAWNUM={7:1,10:1};
function renderRaw(){var b=document.getElementById('rawbody');if(b&&b.getAttribute('data-init'))return;_rawDecode();
 var hh='';for(var i=0;i<RAWCOLS.length;i++)hh+='<th onclick="rawSort('+i+')">'+RAWCOLS[i]+' ⇅</th>';
 document.getElementById('rawhead').innerHTML=hh;if(b)b.setAttribute('data-init','1');rawApply();}
function rawSort(i){if(_rawSort===i)_rawDir=-_rawDir;else{_rawSort=i;_rawDir=1;}rawApply();}
function rawFiltered(){var q=(document.getElementById('rawq').value||'').toLowerCase();
 var mf=document.getElementById('rawmeth').value,tf=document.getElementById('rawtype').value,rf=document.getElementById('rawreport').value;
 var rows=_rawDecode().filter(function(r){if(mf&&r[9]!==mf)return false;if(tf&&r[14]!==tf)return false;if(rf&&r[12]!==rf)return false;
  if(q){var s=(r[0]+' '+r[1]+' '+r[2]+' '+r[3]+' '+r[4]+' '+r[5]+' '+r[6]+' '+r[9]+' '+r[11]+' '+r[12]+' '+r[13]).toLowerCase();if(s.indexOf(q)<0)return false;}return true;});
 var c=_rawSort,d=_rawDir;rows.sort(function(a,b){var x=a[c],y=b[c];if(RAWNUM[c]){x=+x;y=+y;}else{x=(''+x).toLowerCase();y=(''+y).toLowerCase();}return x<y?-d:x>y?d:0;});
 return rows;}
function rawApply(){var rows=rawFiltered(),cap=1500,n=rows.length,show=Math.min(n,cap),out=[];
 for(var i=0;i<show;i++){var r=rows[i];out.push('<tr><td>'+(r[0]||'<span style=\"color:#bbb\">—</span>')+'</td><td>'+r[1]+'</td><td>'+r[2]+'</td><td>'+r[3]+'</td><td>'+r[4]+'</td><td>'+r[5]+'</td><td>'+r[6]+'</td><td style="text-align:right">'+r[7]+'</td><td>'+r[8]+'</td><td>'+r[9]+'</td><td style="text-align:right">'+(r[10]||'')+'</td><td>'+r[11]+'</td><td>'+r[12]+'</td><td>'+r[13]+'</td></tr>');}
 document.getElementById('rawbody').innerHTML=out.join('');
 document.getElementById('rawcount').innerHTML='Showing '+show.toLocaleString()+' of '+n.toLocaleString()+' matching records'+(n>cap?' (refine your search to see the rest)':'')+'. Full dataset: '+TAB4.rows.length.toLocaleString()+' located records.';}
function rawCSV(){var rows=rawFiltered(),lines=[RAWCOLS.join(',')];
 for(var i=0;i<rows.length;i++){var r=rows[i],cells=[];for(var j=0;j<14;j++){var v=''+(r[j]==null?'':r[j]);if(/[",\n]/.test(v))v='"'+v.replace(/"/g,'""')+'"';cells.push(v);}lines.push(cells.join(','));}
 var blob=new Blob([lines.join('\n')],{type:'text/csv;charset=utf-8'});var a=document.createElement('a');
 a.href=URL.createObjectURL(blob);a.download='plumas_pesticide_records.csv';document.body.appendChild(a);a.click();a.remove();}
'''
TAB4JS = TAB4JS.replace('__TAB4__', tab4)
cut('var TAB4=', '</script>', False, TAB4JS)

open(HTML,'w',encoding='utf-8').write(html)
print('OK round3. size:', len(html))
