# Round 5: add federal FACTS records to the Source Data tab (table + Source/Type filters).
import os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT,'index.html'); B = os.path.dirname(os.path.abspath(__file__))
html = open(HTML, encoding='utf-8').read(); shutil.copy(HTML, HTML+'.bak5')
tab4 = open(os.path.join(B,'tab4.json'),encoding='utf-8').read()

def rep(old, new):
    global html
    assert html.count(old) == 1, f'MATCH {html.count(old)} for {old[:60]!r}'
    html = html.replace(old, new)

# 1) replace the embedded TAB4 blob (now includes federal rows)
i = html.index('var TAB4='); j = html.index('\nvar _rawRows=null', i)
html = html[:i] + 'var TAB4=' + tab4 + ';' + html[j:]

# 2) header label: Location no longer always MTRS (federal rows carry county)
rep("var RAWCOLS=['Date','Location (MTRS)','Permittee','Product','EPA Reg','Active ingredient','Type','Qty','Units','Method','Acres','Applicator','Source','Site'];",
    "var RAWCOLS=['Date','Location','Permittee','Product','EPA Reg','Active ingredient','Type','Qty','Units','Method','Acres','Applicator','Source','Site'];")

# 3) Source filter: add federal
rep('<option>Other operators (monthly)</option></select>',
    '<option>Other operators (monthly)</option><option>Federal (USFS FACTS)</option></select>')

# 4) Type filter: add federal-activity code
rep('<option value="O">Other</option></select>',
    '<option value="O">Other</option><option value="X">Federal activity</option></select>')

# 5) banner: updated counts + scope
rep('<b>3,044 located applications</b> from both Production-Ag reports: forestry single-job (2021&ndash;2024) plus other operators&rsquo; 2024 monthly summaries.',
    '<b>3,340 records:</b> 3,044 private Production-Ag applications (forestry single-job 2021&ndash;2024 + other operators&rsquo; 2024 monthly summaries) and 296 federal Plumas NF treatments (USFS FACTS, 2020&ndash;2025). Filter by <b>Source</b> to separate them.')

# 6) section title year range
rep('<h2>Every recorded application (2021&ndash;2024)</h2>',
    '<h2>Every recorded application (2020&ndash;2025)</h2>')

open(HTML,'w',encoding='utf-8').write(html)
print('OK round5. size:', len(html))
