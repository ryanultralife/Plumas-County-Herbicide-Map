import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT,'index.html')
h = open(HTML, encoding='utf-8').read()
old = "+p.Apps+' applications';h+='<br><b>Permittee"
new = "+p.Apps+(p.Apps>1?' applications':' application');h+='<br><b>Permittee"
assert h.count(old) == 1, f'count={h.count(old)}'
open(HTML,'w',encoding='utf-8').write(h.replace(old,new))
print('plural fixed')
