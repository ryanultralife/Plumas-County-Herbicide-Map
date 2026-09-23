# Tahoe-area water asks — 2026-09-23

Nothing sent. Review, fill the two VERIFY recipients, then send from spraymapca@gmail.com.

What we learned from Plumas: water districts and the Division of Drinking Water answered by
pointing to the public EDT Library, which holds every public system's **treated-water
compliance** results. So these letters don't ask for that; we pull it ourselves with
`build/edt_water.py`. They ask for what the state files **don't** hold: surface-water,
lake and source-water testing, and herbicide-permit monitoring.

| # | To | Covers | Recipient |
|---|---|---|---|
| 1 | Lahontan RWQCB (Region 6) | Tahoe basin, Truckee, Carson, Walker (east slope) | **VERIFY** — Board's public-records contact |
| 2 | Tahoe Water Suppliers Association | Raw lake-intake testing; Tahoe Keys herbicide-test monitoring | **VERIFY** — tahoewater.org |
| 3 | Central Valley RWQCB (Region 5) | West slope of Placer, Nevada, El Dorado, Alpine | Courtney.Kasich@Waterboards.ca.gov (answered our Plumas letter) |

Signed as Taylor Durgan, Executive Director, matching the Sep 19 Tahoe letters.

## Before sending: run the state pull
```
python build/edt_water.py --county Placer --county Nevada --county "El Dorado" --county Alpine
```
(needs the SDWIS zips in `data/raw/edt/`, already there from the Plumas pull). It writes
`data/water/<county>.json` and `data/water/coverage.json`. If a county's treated water was
never tested for the herbicides applied there, that's the Plumas finding again, and worth
one line in letter 1 or 3.

## Next, if the state pull shows no herbicide testing
Large raw-water agencies that draw from these watersheds: Placer County Water Agency,
Nevada Irrigation District, El Dorado Irrigation District, South Tahoe PUD. Same letter as
#2, addressed to each. Recipients to be verified.
