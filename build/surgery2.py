# Editorial round 2: Dixie/acres, glyphosate credibility, Science-tab spine + reorder.
import os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT,'index.html')
html = open(HTML, encoding='utf-8').read()
shutil.copy(HTML, HTML+'.bak2')

def rep(old, new):
    global html
    assert html.count(old) == 1, f'MATCH {html.count(old)} for: {old[:70]!r}'
    html = html.replace(old, new)

# ===== A) Dixie Fire + acres denominator (Data tab) =====
rep('<div class="kpi"><div class="n">260%</div><div class="l">Gallons growth 2021&rarr;2024</div></div>',
    '<div class="kpi"><div class="n">260%</div><div class="l">Gallons growth 2021&rarr;2024</div></div>'
    '<div class="kpi"><div class="n">257,400</div><div class="l">Acre-treatments, 2021&ndash;2024 (repeat passes counted each time)</div></div>')

DIXIE = (
'<div class="card"><h2>Why the sharp rise? Post-fire reforestation</h2>'
'<p class="sub">The near-quadrupling of spraying from 2021 to 2024 tracks recovery from the 2021 Dixie Fire.</p>'
'<p>Reported volume climbs from ~6,400 gallons (2021) to ~22,900 (2024), and treated area from ~18,000 to ~103,000 acres a year. That timing lines up with replanting after the <b>Dixie Fire</b> (13 Jul &ndash; 25 Oct 2021), which burned about <b>963,000 acres</b> across Plumas and four neighboring counties &mdash; the largest single wildfire in California history &mdash; and destroyed roughly three-quarters of the town of Greenville. On industrial timberland, burned ground is replanted with conifer seedlings and then sprayed to suppress competing brush and grass (&lsquo;site prep&rsquo; and &lsquo;release&rsquo;) so the seedlings survive. Almost all of the use here is on land held by industrial timber owners (Sierra Pacific Industries, Collins Pine, W.M. Beaty, and a few ranches), consistent with that fire-recovery pattern.</p>'
'<p class="amt">Across 2021&ndash;2024 the data cover about <b>257,400 acre-treatments</b> &mdash; roughly <b>0.23 gallons of liquid product</b> and <b>0.30 pounds of dry product</b> per acre-treatment. Per-acre rates are modest; the concern is the <b>scale and repetition</b> on a fire-altered watershed above a community on wells and springs.</p>'
'<p class="note">&lsquo;Acre-treatments&rsquo; sum each application&rsquo;s treated area, so ground sprayed several times is counted several times &mdash; the standard Pesticide-Use-Report measure, not unique acres burned or owned.</p></div>'
)
rep('<div class="card"><h2>Yearly totals &amp; trend</h2>', DIXIE+'<div class="card"><h2>Yearly totals &amp; trend</h2>')

# ===== B) Glyphosate credibility tweaks =====
rep('EPA withdrew that interim decision and is still re-evaluating.',
    'EPA withdrew that interim decision and is still re-evaluating, and now expects to issue its final glyphosate registration decision in 2026. One nuance often lost in this fight: IARC assesses <b>hazard</b> (whether a chemical <i>can</i> cause cancer at some dose), while EPA assesses <b>risk</b> (whether it does at real-world exposures) &mdash; part of why two serious bodies can land in different places.')

rep('recent advocacy reviews also raise soil-microbe and PFAS-related concerns that warrant scrutiny.',
    'some reviews also raise soil-microbe concerns that warrant further study.')

rep('is a potent "amebicide" &mdash; it kills soil amoebae, important microbial predators that drive nutrient cycling.',
    'has been reported to harm soil amoebae &mdash; microbial predators that help drive nutrient cycling.')

# ===== C) Science-tab spine card + reorder (hexazinone before glyphosate) =====
SPINE = (
'<div class="card sci"><h2>The short version</h2>'
'<p>If you read nothing else, here is the argument in order of what matters most <i>here</i>:</p>'
'<p><b>1. Use is large and rising.</b> Herbicide volume nearly quadrupled from 2021 to 2024, driven by replanting after the 2021 Dixie Fire (see <b>Data &amp; Trends</b>).</p>'
'<p><b>2. The dominant chemicals here are the water-mobile ones.</b> The most-used are <b>hexazinone</b> and <b>glyphosate</b>, with <b>imazapyr</b> third &mdash; and hexazinone and imazapyr are exactly the chemicals that leach and move through soil and water. They are going onto a forested watershed above a rural community on <b>wells and springs</b>.</p>'
'<p><b>3. The biggest unknowns are what isn&rsquo;t tested:</b> the surfactants and &lsquo;inert&rsquo; co-formulants (often more toxic than the active ingredient), real-world tank-mix synergy, and the cumulative, year-after-year load on one watershed.</p>'
'<p><b>4. The largest ecological effect is probably indirect:</b> removing plants removes the base of the food web &mdash; flowers for pollinators, host plants for insects, food for birds and fish.</p>'
'<p class="note">The contested glyphosate&ndash;cancer question (below) is one thread of this story, not the headline &mdash; it is the most dose-dependent and the least specific to Plumas. The chemical-by-chemical detail that follows is a reference appendix.</p></div>'
)
rep('<div id="sciview"><div class="wrap"><div class="card sci"><h2>The chemicals actually being sprayed</h2>',
    '<div id="sciview"><div class="wrap">'+SPINE+'<div class="card sci"><h2>The chemicals actually being sprayed</h2>')

# swap Glyphosate <-> Hexazinone card blocks
gi = html.index('<div class="card sci"><h2>Glyphosate</h2>')
hi = html.index('<div class="card sci"><h2>Hexazinone</h2>')
ii = html.index('<div class="card sci"><h2>Imazapyr</h2>')
assert gi < hi < ii, 'unexpected card order'
gly = html[gi:hi]; hex_ = html[hi:ii]
html = html[:gi] + hex_ + gly + html[ii:]

open(HTML,'w',encoding='utf-8').write(html)
print('OK round2. size:', len(html))
