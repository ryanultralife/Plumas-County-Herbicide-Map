# Port Donate + Transparency onto the CURRENT index.html (which has Source Data).
# Preserves CRLF line endings. Applies the spec's 8 discrete edits.
import os, json, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT,'index.html')
s = open(HTML, encoding='utf-8', newline='').read()      # newline='' preserves \r\n
shutil.copy(HTML, HTML+'.bak8')
LEDGER = json.dumps(json.load(open(os.path.join(ROOT,'data','ledger.json'),encoding='utf-8')), separators=(',',':'))

def crlf(x): return x.replace('\n','\r\n')
def rep(old, new):
    global s
    o = crlf(old)
    assert s.count(o) == 1, f'MATCH {s.count(o)} for {old[:55]!r}'
    s = s.replace(o, crlf(new))

# --- Edit 1: nav button (+ shrink font for 5 tabs) ---
rep('<button id="braw" onclick="show(\'raw\')">Source Data</button></div>',
    '<button id="braw" onclick="show(\'raw\')">Source Data</button><button id="bled" onclick="show(\'ledger\')">Transparency</button></div>')
rep('font:bold 12px Arial;padding:0 2px;line-height:1.1}',
    'font:bold 11px Arial;padding:0 2px;line-height:1.1}')

# --- Edit 2: register #ledgerview in the two view rules ---
rep('#mapview,#dataview,#sciview{position:fixed;top:46px;left:0;right:0;bottom:0}',
    '#mapview,#dataview,#sciview,#ledgerview{position:fixed;top:46px;left:0;right:0;bottom:0}')
rep('#dataview,#sciview{overflow:auto;background:#f4f6f4;display:none;-webkit-overflow-scrolling:touch}',
    '#dataview,#sciview,#ledgerview{overflow:auto;background:#f4f6f4;display:none;-webkit-overflow-scrolling:touch}')

# --- Edit 3: the view container (before the main script) ---
rep('<script>\nvar methods=',
    '<div id="ledgerview"><div class="wrap" id="ledgerWrap"><p style="color:#777;padding:20px 0">Loading ledger…</p></div></div>\n<script>\nvar methods=')

# --- Edit 4 + 7: ledger CSS + donate CSS, before </head> ---
LEDGER_CSS = '<style>#ledgerview .ltitle{font-size:20px;color:#1d3f27;margin:2px 0 2px}#ledgerview .lsub{color:#777;font-size:13px;margin:0 0 12px}.bdg{display:inline-block;font-size:11px;padding:2px 7px;border-radius:10px;color:#fff;white-space:nowrap}.bOperations{background:#2E5E3A}.bTesting{background:#2E8B8B}.bAdmin{background:#8a6d3b}#ledgerview td a,#ledgerview .src a{color:#0050b3}#ledgerview .src{color:#bbb}.lupd{font-size:12px;color:#888;margin:-6px 0 12px}</style>'
DONATE_CSS = r'''<style>
#donateBubble{position:fixed;left:16px;bottom:18px;z-index:2500;border:0;cursor:pointer;
  background:#fd8d3c;color:#fff;font:bold 15px Arial;padding:11px 18px;border-radius:30px;
  box-shadow:0 3px 10px rgba(0,0,0,.35);display:flex;align-items:center;gap:7px;transition:transform .12s,background .12s}
#donateBubble:hover{background:#e8761f;transform:translateY(-2px)}
#donateBubble .dheart{font-size:15px;line-height:1}
#donateOverlay{display:none;position:fixed;inset:0;z-index:3000;background:rgba(20,30,22,.55);
  align-items:center;justify-content:center;padding:16px}
#donateModal{background:#fff;border-radius:14px;max-width:460px;width:100%;max-height:90vh;overflow:auto;
  padding:22px 22px 16px;position:relative;box-shadow:0 12px 40px rgba(0,0,0,.4)}
#donateClose{position:absolute;top:10px;right:12px;border:0;background:transparent;font-size:26px;line-height:1;
  color:#888;cursor:pointer}#donateClose:hover{color:#333}
#donateTitle{margin:0 28px 6px 0;font-size:19px;color:#1d3f27}
#donateBlurb{margin:0 0 14px;font-size:13.5px;color:#555;line-height:1.5}
#donateFoot{margin:14px 0 0;font-size:11.5px;color:#999;text-align:center}
.donateBtn{display:block;text-align:center;background:#2E5E3A;color:#fff;text-decoration:none;font:bold 16px Arial;
  padding:14px;border-radius:10px}.donateBtn:hover{background:#234a2d}
.donateSetup{background:#f4f6f4;border-left:4px solid #fd8d3c;border-radius:8px;padding:12px 14px;font-size:13.5px;color:#444;line-height:1.5}
.donateSetup p{margin:8px 0 0}.donateSetup code{background:#e7ece7;padding:1px 5px;border-radius:4px;font-size:12.5px}
.donateSetup a{color:#0050b3}.donateHint{color:#666;font-size:12.5px}
@media(max-width:600px){#donateBubble{left:12px;bottom:14px;padding:10px 15px;font-size:14px}}
</style>'''
rep('</head>', LEDGER_CSS + DONATE_CSS + '</head>')

# --- Edit 5: show() router (keep raw; add ledger + loadLedger) ---
rep("""function show(v){
 var views={map:'mapview',data:'dataview',sci:'sciview',raw:'rawview'},btns={map:'bmap',data:'bdata',sci:'bsci',raw:'braw'};
 for(var k in views){document.getElementById(views[k]).style.display=(k===v)?'block':'none';
  document.getElementById(btns[k]).classList.toggle('active',k===v);}
 if(v==='raw')renderRaw();
 if(v==='map'){if(!map)buildMap();setTimeout(function(){map.invalidateSize(true);},100);}}""",
"""function show(v){
 var views={map:'mapview',data:'dataview',sci:'sciview',raw:'rawview',ledger:'ledgerview'},btns={map:'bmap',data:'bdata',sci:'bsci',raw:'braw',ledger:'bled'};
 for(var k in views){document.getElementById(views[k]).style.display=(k===v)?'block':'none';
  document.getElementById(btns[k]).classList.toggle('active',k===v);}
 if(v==='raw')renderRaw();
 if(v==='ledger')loadLedger();
 if(v==='map'){if(!map)buildMap();setTimeout(function(){map.invalidateSize(true);},100);}}""")

# --- Edit 6 + 8: Transparency JS (+LEDGER_SEED) and Donate JS, inside main <script> ---
TRANSPARENCY = r'''
/* ===== Transparency ledger (added) ===== */
var LEDGER_SEED=__LEDGER_SEED__;
var _ledgerLoaded=false;
function loadLedger(){
  if(_ledgerLoaded) return; _ledgerLoaded=true;
  fetch('data/ledger.json',{cache:'no-store'})
    .then(function(r){ if(!r.ok) throw 0; return r.json(); })
    .then(function(d){ renderLedger(d); })
    .catch(function(){ renderLedger(typeof LEDGER_SEED!=='undefined'?LEDGER_SEED:{}); });
}
function _money(n){ n=+n||0; return (n<0?'-$':'$')+Math.abs(n).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2}); }
function _m0(n){ n=+n||0; return (n<0?'-$':'$')+Math.abs(n).toLocaleString(undefined,{maximumFractionDigits:0}); }
function _n1(n){ return (+n||0).toLocaleString(undefined,{maximumFractionDigits:1}); }
function _esc(s){ s=(s==null?'':''+s); return s.replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
function _srcLink(x){
  if(!x||!x.src) return '<span class="src">&mdash;</span>';
  var lbl=_esc(x.srcLabel||'Source');
  return '<a href="'+_esc(x.src)+'" target="_blank" rel="noopener">'+lbl+' &#8599;</a>';
}
function renderLedger(d){
  d=d||{}; var don=d.donations||[],exp=d.expenses||[],hrs=d.hours||[];
  var gross=0,fees=0; don.forEach(function(x){gross+=(+x.gross||0);fees+=(+x.fees||0);});
  var net=gross-fees;
  var spent=0,byB={Operations:0,Testing:0,Admin:0};
  exp.forEach(function(x){var a=+x.amount||0;spent+=a;if(byB[x.bucket]!=null)byB[x.bucket]+=a;});
  var cash=net-spent;
  var hours=0,labor=0; hrs.forEach(function(x){var h=+x.hours||0,r=+x.rate||0;hours+=h;labor+=h*r;});
  var dUn=0,dRe=0; don.forEach(function(x){var n=(+x.gross||0)-(+x.fees||0); if(x.type==='Restricted-Testing')dRe+=n; else dUn+=n;});
  function pct(a){return spent>0?(100*a/spent).toFixed(1)+'%':'0.0%';}
  var h='';
  h+='<div class="ltitle">Transparency Ledger</div>';
  h+='<div class="lsub">Every dollar in, every dollar out, and every hour billed &mdash; each figure links to its source document.</div>';
  h+='<div class="lupd">Last updated '+_esc(d.updated||'')+(d.org?' &middot; '+_esc(d.org):'')+'</div>';
  h+='<div class="kpis">';
  h+='<div class="kpi"><div class="n">'+_m0(net)+'</div><div class="l">Net donations received</div></div>';
  h+='<div class="kpi"><div class="n">'+_m0(spent)+'</div><div class="l">Total spent</div></div>';
  h+='<div class="kpi"><div class="n">'+_m0(cash)+'</div><div class="l">Cash on hand</div></div>';
  h+='<div class="kpi"><div class="n">'+_n1(hours)+'</div><div class="l">Hours logged</div></div>';
  h+='</div>';
  h+='<div class="card"><h2>Where the money goes</h2><p class="sub">Spending by purpose.</p>';
  h+='<table><tr><th style="text-align:left">Purpose</th><th>Spent</th><th>% of spend</th></tr>';
  [['Operations (incl. billed hours)','Operations'],['Testing (labs, supplies, contractors)','Testing'],['Admin (fees, filings, insurance)','Admin']].forEach(function(b){
    h+='<tr><td style="text-align:left">'+b[0]+'</td><td>'+_m0(byB[b[1]])+'</td><td>'+pct(byB[b[1]])+'</td></tr>';});
  h+='<tr class="tot"><td style="text-align:left">Total</td><td>'+_m0(spent)+'</td><td>'+(spent>0?'100%':'0%')+'</td></tr></table>';
  h+='<p class="note">Donations restricted to testing: '+_m0(dRe)+' &middot; unrestricted: '+_m0(dUn)+'. Logged labor value: '+_m0(labor)+' at a blended '+(hours>0?_money(labor/hours):'$0.00')+'/hr.</p></div>';
  h+='<div class="card"><h2>Donations in</h2><p class="sub">Net = gross minus platform &amp; processing fees.</p>';
  h+='<table><tr><th>Date</th><th style="text-align:left">Source</th><th>Gross</th><th>Fees</th><th>Net</th><th style="text-align:left">Type</th><th style="text-align:left">Doc</th></tr>';
  don.slice().reverse().forEach(function(x){var n=(+x.gross||0)-(+x.fees||0);
    h+='<tr><td>'+_esc(x.date)+'</td><td style="text-align:left">'+_esc(x.source)+'</td><td>'+_money(x.gross)+'</td><td>'+_money(x.fees)+'</td><td>'+_money(n)+'</td><td style="text-align:left">'+_esc(x.type||'')+'</td><td style="text-align:left">'+_srcLink(x)+'</td></tr>';});
  if(!don.length) h+='<tr><td colspan="7" style="text-align:center;color:#999">No donations logged yet.</td></tr>';
  h+='</table></div>';
  h+='<div class="card"><h2>Expenses out</h2><p class="sub">Every payment, tagged by purpose, with a source document.</p>';
  h+='<table><tr><th>Date</th><th style="text-align:left">Payee / description</th><th style="text-align:left">Bucket</th><th>Amount</th><th style="text-align:left">Doc</th></tr>';
  exp.slice().reverse().forEach(function(x){
    h+='<tr><td>'+_esc(x.date)+'</td><td style="text-align:left">'+_esc(x.payee)+'</td><td style="text-align:left"><span class="bdg b'+_esc(x.bucket)+'">'+_esc(x.bucket)+'</span></td><td>'+_money(x.amount)+'</td><td style="text-align:left">'+_srcLink(x)+'</td></tr>';});
  if(!exp.length) h+='<tr><td colspan="5" style="text-align:center;color:#999">No expenses logged yet.</td></tr>';
  h+='</table></div>';
  h+='<div class="card"><h2>Hours logged</h2><p class="sub">Labor contributed; $ value = hours &times; board-approved rate. Cash actually paid for this work appears under Expenses &rarr; Operations, so nothing is double-counted.</p>';
  h+='<table><tr><th>Date</th><th style="text-align:left">Person</th><th style="text-align:left">Task</th><th>Hours</th><th>Rate</th><th>$ value</th><th style="text-align:left">Doc</th></tr>';
  hrs.slice().reverse().forEach(function(x){var hh=+x.hours||0,r=+x.rate||0;
    h+='<tr><td>'+_esc(x.date)+'</td><td style="text-align:left">'+_esc(x.person)+'</td><td style="text-align:left">'+_esc(x.task)+'</td><td>'+_n1(hh)+'</td><td>'+_money(r)+'</td><td>'+_money(hh*r)+'</td><td style="text-align:left">'+_srcLink(x)+'</td></tr>';});
  if(!hrs.length) h+='<tr><td colspan="7" style="text-align:center;color:#999">No hours logged yet.</td></tr>';
  h+='</table></div>';
  h+='<div class="card"><p class="note">'+_esc(d.note||'')+'</p></div>';
  document.getElementById('ledgerWrap').innerHTML=h;
}
'''.replace('__LEDGER_SEED__', LEDGER)

DONATE = r'''
/* ===== Donate feature (added) ===== */
window.DONATE_CONFIG = {
  platform: 'givebutter',
  givebutterCampaignUrl: '',
  givebutterAccount: '',
  givebutterWidgetId: '',
  donorboxUrl: '',
  title: 'Support Plumas Waterway Testing',
  blurb: 'Donations fund independent water-quality testing in Plumas County. Operating hours are billed transparently; the rest goes straight to testing.'
};
(function(){
  var C = window.DONATE_CONFIG;
  var bubble = document.createElement('button');
  bubble.id = 'donateBubble'; bubble.type = 'button';
  bubble.setAttribute('aria-label','Donate');
  bubble.innerHTML = '<span class="dheart">&#10084;</span> Donate';
  bubble.onclick = openDonate;
  document.body.appendChild(bubble);
  var overlay = document.createElement('div');
  overlay.id = 'donateOverlay';
  overlay.innerHTML =
    '<div id="donateModal" role="dialog" aria-modal="true" aria-labelledby="donateTitle">' +
      '<button id="donateClose" type="button" aria-label="Close">&times;</button>' +
      '<h2 id="donateTitle"></h2>' +
      '<p id="donateBlurb"></p>' +
      '<div id="donateBody"></div>' +
      '<p id="donateFoot">Secure donation processing. You will receive a tax receipt by email.</p>' +
    '</div>';
  document.body.appendChild(overlay);
  overlay.addEventListener('click', function(e){ if(e.target===overlay) closeDonate(); });
  document.getElementById('donateClose').onclick = closeDonate;
  document.addEventListener('keydown', function(e){ if(e.key==='Escape') closeDonate(); });
  var loaded = false;
  function buildBody(){
    var body = document.getElementById('donateBody');
    document.getElementById('donateTitle').textContent = C.title;
    document.getElementById('donateBlurb').textContent = C.blurb;
    if (C.platform === 'givebutter' && C.givebutterAccount && C.givebutterWidgetId){
      if(!loaded){
        var sc=document.createElement('script');
        sc.src='https://widgets.givebutter.com/latest.umd.cjs?acct='+encodeURIComponent(C.givebutterAccount)+'&p=other';
        sc.async=true; document.head.appendChild(sc); loaded=true;
      }
      body.innerHTML='<givebutter-widget id="'+C.givebutterWidgetId+'"></givebutter-widget>';
      return;
    }
    if (C.platform === 'givebutter' && C.givebutterCampaignUrl){
      body.innerHTML='<a class="donateBtn" target="_blank" rel="noopener" href="'+C.givebutterCampaignUrl+'">Donate securely &rarr;</a>';
      return;
    }
    if (C.platform === 'donorbox' && C.donorboxUrl){
      body.innerHTML='<iframe src="'+C.donorboxUrl+'" name="donorbox" allowpaymentrequest="allowpaymentrequest" seamless frameborder="0" scrolling="no" height="640" width="100%" style="max-width:100%;min-width:250px;max-height:none"></iframe>';
      return;
    }
    body.innerHTML=
      '<div class="donateSetup">' +
        '<b>Donate button is ready &mdash; one step left.</b>' +
        '<p>Create a free <a href="https://givebutter.com" target="_blank" rel="noopener">Givebutter</a> ' +
        'account (or <a href="https://donorbox.org" target="_blank" rel="noopener">Donorbox</a>), then open ' +
        '<code>index.html</code> and paste your campaign link into <code>DONATE_CONFIG</code> near the bottom of the file.</p>' +
        '<p class="donateHint">Tip: in Givebutter, enable &ldquo;optional donor tips&rdquo; and &ldquo;let donors cover fees&rdquo; so the org keeps ~100% of each gift.</p>' +
      '</div>';
  }
  function openDonate(){ buildBody(); overlay.style.display='flex'; document.body.style.overflow='hidden'; }
  function closeDonate(){ overlay.style.display='none'; document.body.style.overflow=''; }
  window.openDonate=openDonate; window.closeDonate=closeDonate;
})();
'''
rep('setTimeout(fix,300);', 'setTimeout(fix,300);\n' + TRANSPARENCY + DONATE)

open(HTML,'w',encoding='utf-8',newline='').write(s)
print('OK round8. size:', len(s), '| CRLF kept:', s.count('\r\n'), '| bare LF:', s.count('\n')-s.count('\r\n'))
