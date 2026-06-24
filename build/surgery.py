# Apply all edits to index.html in one pass, with assertions on every replacement.
import json, os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT,'index.html')
B    = os.path.dirname(os.path.abspath(__file__))
html = open(HTML, encoding='utf-8').read()
shutil.copy(HTML, HTML+'.bak')

def rep(old, new, n=1):
    global html
    c = html.count(old)
    assert c == n, f'MATCH {c}!={n} for: {old[:70]!r}'
    html = html.replace(old, new, 1 if n==1 else -1)

methods = json.load(open(os.path.join(B,'methods.json'),encoding='utf-8'))['methods']
tab4    = open(os.path.join(B,'tab4.json'),encoding='utf-8').read()

# ---------- 1) CSS: shrink nav font for 4 tabs; add new styles before </style> ----------
rep('#nav button{flex:1;height:46px;border:0;background:transparent;color:#cfe3d2;font:bold 15px Arial}',
    '#nav button{flex:1;height:46px;border:0;background:transparent;color:#cfe3d2;font:bold 12px Arial;padding:0 2px;line-height:1.1}')

NEWCSS = (
'.datedbanner{background:#fff7e6;border:1px solid #ffd591;border-left:4px solid #fd8d3c;border-radius:8px;padding:10px 12px;margin-bottom:14px;font-size:13px;color:#5c3b00;line-height:1.45}'
'#rawview{position:fixed;top:46px;left:0;right:0;bottom:0;overflow:auto;background:#f4f6f4;display:none;-webkit-overflow-scrolling:touch}'
'.rawctrls{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 8px}'
'.rawctrls input,.rawctrls select,.rawctrls button{font-size:13px;padding:7px 9px;border:1px solid #cfd8cf;border-radius:6px;background:#fff}'
'.rawctrls input{flex:1 1 220px}'
'.rawctrls button{background:#2E5E3A;color:#fff;border-color:#2E5E3A;cursor:pointer;font-weight:bold}'
'.rawtbl{border-collapse:collapse;width:100%;font-size:12px}'
'.rawtbl th,.rawtbl td{border:1px solid #e3e3e3;padding:4px 7px;text-align:left;white-space:nowrap}'
'.rawtbl th{position:sticky;top:0;background:#2E5E3A;color:#fff;cursor:pointer;user-select:none}'
'.rawtbl td{color:#222}'
'.rawtbl tbody tr:nth-child(even){background:#fafbfa}'
)
rep('.note{font-size:12px;color:#888;margin-top:6px}</style>',
    '.note{font-size:12px;color:#888;margin-top:6px}'+NEWCSS+'</style>')

# ---------- 2) Nav: add 4th button ----------
rep('<button id="bsci" onclick="show(\'sci\')">Herbicides &amp; Science</button></div>',
    '<button id="bsci" onclick="show(\'sci\')">Herbicides &amp; Science</button>'
    '<button id="braw" onclick="show(\'raw\')">Source Data</button></div>')

# ---------- 3) Dated banner at top of Data tab ----------
rep('<div id="dataview"><div class="wrap">',
    '<div id="dataview"><div class="wrap">'
    '<div class="datedbanner"><b>Historical snapshot.</b> These charts summarize <b>2,800 reported applications from 29 Jul 2021 &ndash; 2 Nov 2024</b> (California DPR Pesticide Use Reports). The data is <b>not real-time</b> and ends in late 2024; any &lsquo;growth&rsquo; describes that window only.</div>')

# ---------- 4) Fix the "by weight" error (prose) ----------
rep('By <b>weight</b>, the single largest is <b>hexazinone</b> (Velpar), a soil herbicide notable for moving readily into groundwater.',
    'By active-ingredient weight it very likely leads as well. The data are a mix, though &mdash; and the chemical that stands out for <i>local</i> risk is <b>hexazinone</b> (Velpar), applied as a dry solid and the dominant <b>soil-applied, water-mobile</b> herbicide here, notable for leaching into groundwater. (Liquid gallons and dry pounds measure different things and aren&rsquo;t added together, so we rank glyphosate first by volume and flag hexazinone as the key water-mover rather than calling either &lsquo;largest by weight&rsquo;.)')

# ---------- 5) Fix science table numbers (hexazinone true total; triclopyr) ----------
rep('<td>Hexazinone</td><td>0</td><td>75,304</td><td>272</td>',
    '<td>Hexazinone</td><td>0</td><td>76,204</td><td>273</td>')
rep('<td>Triclopyr</td><td>28</td><td>0</td><td>5</td>',
    '<td>Triclopyr</td><td>20</td><td>0</td><td>4</td>')
rep("<p class=\"note\">Liquids (gallons) and solids (pounds) aren't summed.",
    "<p class=\"note\">Figures are <b>formulated product as applied</b> grouped by active ingredient (e.g., Velpar DF is ~75% hexazinone), not pure active-ingredient mass. Liquids (gallons) and solids (pounds) aren't summed.")

# ---------- 6) Map legend: note the data window ----------
rep('style="border:2px solid #0050b3"></span> Aircraft\';return d;};',
    'style="border:2px solid #0050b3"></span> Aircraft<br><span style="font-size:11px;color:#666">Applications 2021&ndash;2024</span>\';return d;};')

# ---------- 7) Popup: define popupHtml() before buildMap; swap the bindPopup call ----------
POPUP = (
"function popupHtml(m,p){var dt=(p.D0===p.D1)?p.D0:(p.D0+' \\u2013 '+p.D1);"
"var h='<b>Method:</b> '+m+'<br><b>Dates applied:</b> '+dt+'<br><b>Herbicide(s) sprayed here:</b>';"
"if(p.Chems&&p.Chems.length){h+='<ul style=\"margin:3px 0 4px 16px;padding:0\">';"
"for(var i=0;i<p.Chems.length;i++){var c=p.Chems[i],a=[];if(c[1])a.push(c[1]+' gal');if(c[2])a.push(c[2]+' lb');"
"h+='<li>'+c[0]+(c[4]=='I'?' <i>(insecticide)</i>':'')+' \\u2014 '+a.join(' + ')+' <span style=\"color:#777\">('+c[3]+(c[3]>1?' applications':' application')+')</span></li>';}"
"h+='</ul>';}else{h+=' <i>none recorded</i><br>';}"
"if(p.Adj>0)h+='<span style=\"color:#777;font-size:12px\">+ '+p.Adj+' gal tank-mixed adjuvants/surfactants (not herbicides)</span><br>';"
"h+='<b>Total here:</b> '+p.Gallons+' gal'+(p.Pounds>0?(' \\u00b7 '+p.Pounds+' lb'):'')+' \\u00b7 '+p.Apps+' applications';"
"h+='<br><b>Permittee(s):</b> '+p.Permittees;return h;}\n"
)
rep('function buildMap(){', POPUP+'function buildMap(){')
rep(".bindPopup('<b>Method:</b> '+m+'<br><b>Gallons:</b> '+p.Gallons+'<br><b>Pounds:</b> '+p.Pounds+'<br><b>Applications:</b> '+p.Apps+'<br><b>Permittee(s):</b> '+p.Permittees).addTo(grp);",
    ".bindPopup(popupHtml(m,p),{maxWidth:330,minWidth:210}).addTo(grp);")

# ---------- 8) show(): register raw tab + lazy-render ----------
rep("var views={map:'mapview',data:'dataview',sci:'sciview'},btns={map:'bmap',data:'bdata',sci:'bsci'};",
    "var views={map:'mapview',data:'dataview',sci:'sciview',raw:'rawview'},btns={map:'bmap',data:'bdata',sci:'bsci',raw:'braw'};")
rep("if(v==='map'){if(!map)buildMap();",
    "if(v==='raw')renderRaw();\n if(v==='map'){if(!map)buildMap();")

# ---------- 9) Insert #rawview just before the main <script> ----------
RAWVIEW = (
'<div id="rawview"><div class="wrap">'
'<div class="datedbanner"><b>Source data &mdash; historical snapshot.</b> Every row below is a real reported application from the California DPR Pesticide Use Reports. <b>2,800 records, 29 Jul 2021 &ndash; 2 Nov 2024.</b> Not real-time; the record ends in late 2024. Active ingredients are derived from the EPA registration numbers so you can verify them.</div>'
'<div class="card"><h2>Every recorded application (2021&ndash;2024)</h2>'
'<p class="sub">Search, click a column to sort, filter by method or type, or download the CSV to review it yourself.</p>'
'<div class="rawctrls">'
'<input id="rawq" placeholder="Search product, ingredient, applicator, location…" oninput="rawApply()">'
'<select id="rawmeth" onchange="rawApply()"><option value="">All methods</option><option>Ground</option><option>Aircraft</option><option>Unspecified</option></select>'
'<select id="rawtype" onchange="rawApply()"><option value="">All types</option><option value="H">Herbicides</option><option value="A">Adjuvants/surfactants</option><option value="I">Insecticides</option></select>'
'<button onclick="rawCSV()">Download CSV</button></div>'
'<div id="rawcount" class="note"></div>'
'<div id="rawtblwrap" style="overflow-x:auto"><table class="rawtbl"><thead><tr id="rawhead"></tr></thead><tbody id="rawbody"></tbody></table></div>'
'</div></div></div>\n'
)
rep('<script>\nvar methods=', RAWVIEW+'<script>\nvar methods=')

# ---------- 10) Replace the methods blob (index-based; the old blob is huge) ----------
i = html.index('var methods='); j = html.index(', mstyle=')
html = html[:i] + 'var methods=' + json.dumps(methods, separators=(',',':')) + html[j:]

# ---------- 11) Tab-4 data + renderRaw(), injected before </body> ----------
TAB4SCRIPT = '<script>\nvar TAB4=__TAB4__;\n' + r'''
var _rawRows=null,_rawSort=0,_rawDir=-1;
function _rawDecode(){if(_rawRows)return _rawRows;var T=TAB4,o=[];
 for(var i=0;i<T.rows.length;i++){var r=T.rows[i],pm=T.prodMeta[r[3]]||['',-1,''];
  o.push([r[0],r[1],T.perm[r[2]]||'',T.prod[r[3]]||'',pm[0]||'',T.ai[pm[1]]||'',r[4],T.unit[r[5]]||'',T.meth[r[6]]||'',T.appl[r[7]]||'',r[8]||'',pm[2]||'']);}
 _rawRows=o;return o;}
var RAWCOLS=['Date','Location (MTRS)','Permittee','Product','EPA Reg','Active ingredient','Qty','Units','Method','Applicator','Site'];
function renderRaw(){var b=document.getElementById('rawbody');if(b&&b.getAttribute('data-init'))return;_rawDecode();
 var hh='';for(var i=0;i<RAWCOLS.length;i++)hh+='<th onclick="rawSort('+i+')">'+RAWCOLS[i]+' ⇅</th>';
 document.getElementById('rawhead').innerHTML=hh;if(b)b.setAttribute('data-init','1');rawApply();}
function rawSort(i){if(_rawSort===i)_rawDir=-_rawDir;else{_rawSort=i;_rawDir=1;}rawApply();}
function rawFiltered(){var q=(document.getElementById('rawq').value||'').toLowerCase();
 var mf=document.getElementById('rawmeth').value,tf=document.getElementById('rawtype').value;
 var rows=_rawDecode().filter(function(r){if(mf&&r[8]!==mf)return false;if(tf&&r[11]!==tf)return false;
  if(q){var s=(r[0]+' '+r[1]+' '+r[2]+' '+r[3]+' '+r[4]+' '+r[5]+' '+r[8]+' '+r[9]+' '+r[10]).toLowerCase();if(s.indexOf(q)<0)return false;}return true;});
 var c=_rawSort,d=_rawDir;rows.sort(function(a,b){var x=a[c],y=b[c];if(c===6){x=+x;y=+y;}else{x=(''+x).toLowerCase();y=(''+y).toLowerCase();}return x<y?-d:x>y?d:0;});
 return rows;}
function rawApply(){var rows=rawFiltered(),cap=1200,n=rows.length,show=Math.min(n,cap),out=[];
 for(var i=0;i<show;i++){var r=rows[i];out.push('<tr><td>'+r[0]+'</td><td>'+r[1]+'</td><td>'+r[2]+'</td><td>'+r[3]+'</td><td>'+r[4]+'</td><td>'+r[5]+'</td><td style="text-align:right">'+r[6]+'</td><td>'+r[7]+'</td><td>'+r[8]+'</td><td>'+r[9]+'</td><td>'+r[10]+'</td></tr>');}
 document.getElementById('rawbody').innerHTML=out.join('');
 document.getElementById('rawcount').innerHTML='Showing '+show.toLocaleString()+' of '+n.toLocaleString()+' matching records'+(n>cap?' (refine your search to see the rest)':'')+'. Full dataset: 2,800 records.';}
function rawCSV(){var rows=rawFiltered(),lines=[RAWCOLS.join(',')];
 for(var i=0;i<rows.length;i++){var r=rows[i],cells=[];for(var j=0;j<11;j++){var v=''+r[j];if(/[",\n]/.test(v))v='"'+v.replace(/"/g,'""')+'"';cells.push(v);}lines.push(cells.join(','));}
 var blob=new Blob([lines.join('\n')],{type:'text/csv;charset=utf-8'});var a=document.createElement('a');
 a.href=URL.createObjectURL(blob);a.download='plumas_pesticide_records_2021-2024.csv';document.body.appendChild(a);a.click();a.remove();}
</script>'''
TAB4SCRIPT = TAB4SCRIPT.replace('__TAB4__', tab4)
rep('</script></body></html>', '</script>\n'+TAB4SCRIPT+'\n</body></html>')

open(HTML,'w',encoding='utf-8').write(html)
print('OK. new size:', len(html), 'bytes (was', os.path.getsize(HTML+'.bak'),')')
