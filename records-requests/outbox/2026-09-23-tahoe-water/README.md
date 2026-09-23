# Tahoe-area water asks — 2026-09-23

Nothing sent. Review, then save as drafts / send from spraymapca@gmail.com.

What we learned from Plumas: water districts and the Division of Drinking Water answered by
pointing to the public EDT Library, which holds every public system's **treated-water
compliance** results. So these letters don't ask for that; we pull it ourselves with
`build/edt_water.py`. They ask for what the state files **don't** hold: surface-water,
lake and source-water testing, and herbicide-permit monitoring.

| # | To | Covers | Recipient (where it came from) |
|---|---|---|---|
| 1 | Lahontan RWQCB (Region 6) | Tahoe basin, Truckee, Carson, Walker (east slope) | RB6S-PRA@waterboards.ca.gov (Board's public-records page) |
| 2 | Tahoe Water Suppliers Association | Raw lake-intake testing; Tahoe Keys herbicide-test monitoring | drinktahoetap@ivgid.org (TWSA program materials; ED Madonna Dunbar) |
| 3 | Central Valley RWQCB (Region 5) | West slope of Placer, Nevada, El Dorado, Alpine | Courtney.Kasich@Waterboards.ca.gov (answered our Plumas letter) |
| 4 | Placer County Water Agency | American River / canal intakes | clerk@pcwa.net (PCWA records-request form) |
| 5 | Nevada Irrigation District | Yuba-Bear reservoirs and canals | customerservice@nidwater.com (**general inbox**; NID lists no records address) |
| 6 | El Dorado Irrigation District | Jenkinson/Folsom, canals | PublicRecordsRequest@EID.org (EID records page; JustFOIA portal also works) |
| 7 | South Tahoe PUD | Tahoe basin wells | mguttry@stpud.us (Clerk of the Board, per STPUD records policy; a staff address, may change) |

**One-click drafts:** open `compose.html` in the Chrome profile where spraymapca@gmail.com is account u/1.
Each link opens a filled Gmail compose window; closing it saves the draft. Check the tab title first.
(The Gmail connector in Claude sessions is bound to ryan@mechanical-battery.com, so drafts were
not created there.)

Signed as Taylor Durgan, Executive Director, matching the Sep 19 Tahoe letters.

## Before sending: run the state pull
```
python build/edt_water.py --county Placer --county Nevada --county "El Dorado" --county Alpine
```
(needs the SDWIS zips in `data/raw/edt/`, already there from the Plumas pull). It writes
`data/water/<county>.json` and `data/water/coverage.json`. If a county's treated water was
never tested for the herbicides applied there, that's the Plumas finding again, and worth
one line in letter 1 or 3.
