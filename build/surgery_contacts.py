# surgery_contacts: add a "Verify or report" contacts block to each map popup bubble.
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, 'index.html')
s = open(HTML, encoding='utf-8', newline='').read()
def crlf(x): return x.replace('\r\n','\n').replace('\n','\r\n')

BLOCK = r'''var CONTACTS=null;
function loadContacts(){
  if(CONTACTS) return Promise.resolve(CONTACTS);
  return fetch('data/contacts.json').then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(j){CONTACTS=j;return j;}).catch(function(){return null;});
}
function copyEmail(ev,a){ev.preventDefault();ev.stopPropagation();try{navigator.clipboard.writeText(a);var t=ev.target;var o=t.textContent;t.textContent='[copied]';setTimeout(function(){t.textContent=o;},1200);}catch(e){}return false;}
function buildContacts(county){
  if(!CONTACTS) return '';
  var c=CONTACTS.counties&&CONTACTS.counties[county], dpr=CONTACTS.dpr||{}, reps=CONTACTS.reps||{}, air=CONTACTS.air||{};
  var h='<div style="margin-top:7px;border-top:1px solid #e5e5e5;padding-top:5px;font-size:11.5px;line-height:1.5">';
  h+='<b>Verify or raise a concern'+(county?' — '+county+' Co.':'')+'</b>';
  if(c&&c.ag&&c.ag.email){var ag=c.ag;
    h+='<div title="County Agricultural Commissioner: holds the permit records and investigates pesticide-use complaints. Start here.">'
      +'<b>Ag Commissioner</b>'+(ag.officer?' ('+ag.officer+')':'')+': '
      +'<a href="mailto:'+ag.email+'?subject='+encodeURIComponent('SprayMap data question — '+county+' County')+'">'+ag.email+'</a> '
      +'<a href="#" onclick="return copyEmail(event,\''+ag.email+'\')" style="color:#2E5E3A" title="Copy the address to paste into your own email">[copy]</a>'
      +(ag.phone?' · '+ag.phone:'')+'</div>';
  }
  if(c&&c.water){h+='<div title="Regional Water Quality Control Board: runoff, wells, drinking-water concerns"><b>Water</b>: <a href="'+c.water.url+'" target="_blank" rel="noopener">file a water-quality concern</a> ('+(c.water.region||'').replace(/ ?Regional.*/,'')+')</div>';}
  h+='<div title="'+(dpr.note||'')+'"><b>State</b>: <a href="'+(dpr.url||'#')+'" target="_blank" rel="noopener">CA DPR</a> · 1-87-PestLine ('+(dpr.phone||'')+')</div>';
  h+='<div><a href="'+(reps.url||'#')+'" target="_blank" rel="noopener" title="'+(reps.note||'')+'">your state reps</a> · <a href="'+(air.url||'#')+'" target="_blank" rel="noopener" title="'+(air.note||'')+'">air district</a></div>';
  return h+'</div>';
}
'''

# 1) define the contacts helpers right before mergeOwners()
anchor = 'function mergeOwners(owners){'
assert s.count(anchor) == 1, 'mergeOwners anchor=' + str(s.count(anchor))
s = s.replace(anchor, crlf(BLOCK) + anchor, 1)

# 2) load contacts when the map builds
ov = 'OVERLAYS=overlays; loadOperatorNames();'
assert s.count(ov) == 1, 'overlays anchor=' + str(s.count(ov))
s = s.replace(ov, 'OVERLAYS=overlays; loadOperatorNames(); loadContacts();')

# 3) append the contacts block to the cell popup (after the Top applicators line)
own = "join('<br>')+'</span>';}"
assert s.count(own) == 1, 'popup owners anchor=' + str(s.count(own))
s = s.replace(own, "join('<br>')+'</span>';}\r\n  h+=buildContacts(p.county||'');", 1)

open(HTML, 'w', encoding='utf-8', newline='').write(s)
print('OK surgery_contacts. size:', len(s), '| bare LF:', s.count('\n')-s.count('\r\n'))
