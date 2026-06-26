#!/usr/bin/env python3
"""
Generate California Public Records Act (CPRA) request letters to county
Agricultural Commissioners asking for the permit/operator-ID -> permittee NAME
crosswalk. This is the only public source of operator names: CDPR does not collect
or publish them (see memory/applicator-ids). Responses get ingested into the
public.operator_names table via build/ingest_operator_names.py, after which real
names appear automatically in the map popups + Data & Trends + Source Data.

Usage:  python build/gen_records_requests.py
Writes: records-requests/letters/<rank>-<county>.md  (one per priority county)
"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "records-requests", "letters")
DATE = "June 26, 2026"
SENDER = "spraymapca@gmail.com"
# Verified county Agricultural Commissioner contacts (researched + verified 2026-06-26,
# mostly against the CDFA statewide commissioner directory). county -> {email, method, source}
CONTACTS = {
 "Monterey":      {"email":"agcomm@co.monterey.ca.us",   "method":"Email, or county NextRequest portal https://countyofmontereyca.nextrequest.com/", "source":"CDFA commissioner directory + countyofmonterey.gov"},
 "Fresno":        {"email":"fresnoag@fresnocountyca.gov", "method":"Email, or NextRequest portal https://fresnocountyca.nextrequest.com/",            "source":"CDFA directory + fresnocountyca.gov"},
 "Tulare":        {"email":"aginfo@tularecounty.ca.gov",  "method":"Email, or NextRequest portal https://countyoftulareca.nextrequest.com/",          "source":"CDFA directory"},
 "Kern":          {"email":"agcomm@kerncounty.com",       "method":"Email, or NextRequest portal https://kerncountyca.nextrequest.com/",              "source":"kernred.co.kern.ca.us + CDFA directory"},
 "San Joaquin":   {"email":"stocktonag2@sjgov.org",       "method":"Email (no online portal)",                                                        "source":"sjgov.org AgComm contact page"},
 "Santa Barbara": {"email":None,                          "method":"No AgComm email published — submit via county Public Records Center portal https://santabarbaracountyca.govqa.us/ and route to the Agricultural Commissioner", "source":"countyofsb.org records page"},
 "Stanislaus":    {"email":"agcom50@stancounty.com",      "method":"Email or mail (office records form on stanag.org; no third-party portal)",        "source":"stanag.org public-information-records page"},
 "Merced":        {"email":"agdeptemail@co.merced.ca.us", "method":"Email (no online portal)",                                                        "source":"CDFA directory + countyofmerced.com"},
 "Ventura":       {"email":"webmaster@venturacounty.gov", "method":"Primary: NextRequest portal https://ventura.nextrequest.com/ directed to the Agricultural Commissioner; general email as fallback", "source":"venturacounty.gov Clerk of the Board records page"},
 "Riverside":     {"email":"agdept@rivco.org",            "method":"Email, or county NextRequest portal https://riversidecountyca.nextrequest.com/",   "source":"CDFA directory + rivcoawm.org"},
 "Madera":        {"email":"MaderaPUE@maderacounty.com",  "method":"Email the Pesticide Use Enforcement division (no portal). Please re-confirm — county site blocks automated checks", "source":"maderacounty.com PUE pages + CalAgPermits"},
 "Imperial":      {"email":"pue@co.imperial.ca.us",       "method":"Email the Pesticide Use Enforcement division (general office: agcom@co.imperial.ca.us)", "source":"agcom.imperialcounty.org PUE page"},
 "Plumas":        {"email":"willovieira@countyofplumas.com", "method":"Email the Agricultural Commissioner (Willo Vieira) directly (no online portal)", "source":"plumascounty.us Pesticide Use Records page"},
}

# CDPR county codes (leading 2 digits of every operator/permit ID)
CC = {"Monterey":"27","Fresno":"10","Tulare":"54","Kern":"15","San Joaquin":"39",
      "Santa Barbara":"42","Stanislaus":"50","Merced":"24","Ventura":"56",
      "Riverside":"33","Madera":"20","Imperial":"13","Plumas":"32"}
# priority order (by mapped applications 2020-2026); Plumas added as the home county
PRIORITY = [("Monterey",1774025),("Fresno",984830),("Tulare",858909),("Kern",595559),
            ("San Joaquin",525789),("Santa Barbara",493682),("Stanislaus",410267),
            ("Merced",329492),("Ventura",323902),("Riverside",283601),("Madera",281595),
            ("Imperial",265655),("Plumas",None)]

LETTER = """# Public Records Act request — {county} County Agricultural Commissioner

**To:** {county} County Agricultural Commissioner / Sealer of Weights & Measures
**Send to:** {recipient}

**From:** SprayMap California — public pesticide-transparency project <{sender}>
**Date:** {date}
**Re:** California Public Records Act request — pesticide permit holder names

Dear Commissioner,

Under the California Public Records Act (Gov. Code § 7920.000 *et seq.*), I request
copies of the following public records held by your office:

1. The current roster of **Operator Identification Numbers / Restricted Materials
   Permit numbers** issued by {county} County (county code **{code}**), together with
   the **permittee / operator name** (business or individual) and mailing city/ZIP
   for each, for permits active at any time during **2020–2026**.

2. If maintained as such, your **"Permits, Sites, and Commodities"** export (or the
   equivalent CalAgPermits report) covering the same period.

The purpose is to attach real operator names to California Pesticide Use Report
records, which CDPR publishes only as coded permit numbers. We are not requesting
any confidential application-site detail beyond what is already public in the PUR —
only the operator-ID → name correspondence.

**Preferred format:** a machine-readable file (CSV or Excel). A column of operator/
permit IDs and a column of names is sufficient.

**Fee waiver / costs:** This request serves the public interest in government
transparency; please waive duplication fees if possible. If costs will exceed $25,
please contact me first with an estimate.

Please let me know within the 10-day statutory period (Gov. Code § 7922.535) whether
the records exist and when they will be produced. If any portion is withheld, please
cite the specific exemption.

Thank you,

SprayMap California
*Reply to: {sender}*

---
*Generated by build/gen_records_requests.py. {county} = {n} mapped applications, 2020–2026.*
"""

README = """# Records requests — getting real operator names

California's public Pesticide Use Reports identify the operator only by a coded
**Operator Identification Number / permit number** (leading 2 digits = county code).
CDPR does **not** collect or publish operator names — by their own statement, names
are held only by the **County Agricultural Commissioner**. So real names can only be
obtained per county, via a Public Records Act (CPRA) request. (See
`memory/applicator-ids` for the full decode + research.)

## Workflow
1. **Generate letters:** `python build/gen_records_requests.py` → `letters/*.md`
   (one per priority county, ordered by spray volume; Plumas included as home county).
2. **Send** each letter. The recipient (verified county Ag Commissioner email or
   records portal) and the sender (spraymapca@gmail.com) are already filled in.
   Counties with no published AgComm email (e.g. Santa Barbara) use a public-records
   portal — submit there and route the request to the Agricultural Commissioner.
   Madera's address should be re-confirmed (its county site blocks automated checks).
3. **When a county replies** with a permit-ID → name file, normalize it to a CSV with
   at least `operator_id,name` (optionally `entity_type,county`) and ingest:
   `DBURL=... python build/ingest_operator_names.py path/to/county.csv --county "Fresno" --source "cac-fresno-2026"`
4. Names then appear automatically everywhere the site shows applicators (the
   frontend loads `public.operator_names` and `applicatorInfo()` prefers a real name).

## Priority counties (by mapped applications, 2020–2026)
Monterey, Fresno, Tulare, Kern, San Joaquin, Santa Barbara, Stanislaus, Merced,
Ventura, Riverside, Madera, Imperial — plus Plumas (home county).

## Notes
- The operator ID decodes as: [reporting county 2][permit year 2][home county 2][permit 5] + optional permit-type letter (R = restricted-materials).
- We only ask for the operator-ID → name correspondence, not confidential site detail.
"""

def main():
    os.makedirs(OUT, exist_ok=True)
    for i, (county, n) in enumerate(PRIORITY, 1):
        c = CONTACTS.get(county, {})
        rec = c.get("email") or "(no public email found — confirm via the county Ag Commissioner site)"
        if c.get("method"): rec += f"  ·  records method: {c['method']}"
        if c.get("source"): rec += f"  ·  source: {c['source']}"
        body = LETTER.format(county=county, code=CC[county], date=DATE, sender=SENDER,
                             recipient=rec, n=(f"{n:,}" if n else "the project's home county"))
        fn = os.path.join(OUT, f"{i:02d}-{county.lower().replace(' ','-')}.md")
        open(fn, "w", encoding="utf-8").write(body)
    open(os.path.join(ROOT, "records-requests", "README.md"), "w", encoding="utf-8").write(README)
    print(f"Wrote {len(PRIORITY)} letters to {OUT} + README")

if __name__ == "__main__":
    main()
