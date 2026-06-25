# Round 7: add USGS streams/water overlay (toggleable) + a "Data sources & coverage" panel.
import os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT,'index.html'); html = open(HTML, encoding='utf-8').read()
shutil.copy(HTML, HTML+'.bak7')

def rep(old, new):
    global html
    assert html.count(old) == 1, f'MATCH {html.count(old)} for {old[:55]!r}'
    html = html.replace(old, new)

# 1) USGS hydrography overlay (off by default; toggle to see treatments vs waterways)
HYDRO = (" var hydro=L.tileLayer('https://basemap.nationalmap.gov/arcgis/rest/services/USGSHydroCached/MapServer/tile/{z}/{y}/{x}',{opacity:.85,maxZoom:16,attribution:'USGS The National Map — Hydrography'});\n"
         " overlays['Streams & water (USGS)']=hydro;\n"
         " var tl=L.layerGroup();towns.forEach")
rep(' var tl=L.layerGroup();towns.forEach', HYDRO)

# 2) "Data sources & coverage" card on the Science tab (after the spine, before the chemicals intro)
CARD = ('<div class="card sci"><h2>Where this data comes from &mdash; and where it doesn&rsquo;t</h2>'
 '<p>This map combines the public records that exist, and is honest about the gaps.</p>'
 '<h3>Private land &mdash; full chemical detail</h3>'
 '<p>California <b>Pesticide Use Reporting (PUR)</b>, filed with the County Agricultural Commissioner and DPR. Covers private timberland, ranches, golf courses and the like &mdash; with the actual product, <b>active ingredient, amount, and location</b>. This is the bulk of the map (the warm-colored dots).</p>'
 '<h3>Federal land (Plumas National Forest) &mdash; activities, not chemicals</h3>'
 '<p>USDA Forest Service <b>FACTS</b> activity records (the blue &lsquo;Federal&rsquo; layer): treatment activity, NEPA project, acres, year and location &mdash; but <b>not the chemical or quantity</b>. The Forest Service has said active-ingredient and amount data require a records request, so those show &lsquo;FOIA pending.&rsquo;</p>'
 '<h3>What&rsquo;s still missing</h3>'
 '<p>Federal chemical/quantity data (FOIA to USFS Region&nbsp;5), the most recent local permits/NOIs (county Ag Commissioner), and additional counties/years are being requested or added. Toggle the <b>Streams &amp; water</b> layer on the map to see treatments relative to waterways.</p>'
 '<p class="note">Coverage: private PUR 2021&ndash;2024 (2020/2025 refresh pending); federal FACTS 2020&ndash;2029 (includes planned treatments). A historical snapshot, not real-time. Full source inventory and draft records-requests are in the project repo.</p></div>')
rep('<div class="card sci"><h2>The chemicals actually being sprayed</h2>',
    CARD + '<div class="card sci"><h2>The chemicals actually being sprayed</h2>')

open(HTML,'w',encoding='utf-8').write(html)
print('OK round7. size:', len(html))
