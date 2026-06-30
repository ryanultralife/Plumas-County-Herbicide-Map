#!/usr/bin/env python3
"""Emit Gmail compose-URL (draft) links for the emailable counties, targeting
the spraymapca account (mail/u/1/). Santa Barbara has no email -> skipped (portal)."""
import urllib.parse, json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import gen_records_requests as g

UIDX = 1  # spraymapca@gmail.com is the 2nd account on this Chrome profile
SUBJECT = "California Public Records Act request - pesticide permit holder names"
BODY = """Dear {county} County Agricultural Commissioner,

Under the California Public Records Act (Gov. Code section 7920.000 et seq.), I request copies of the following public records held by your office:

1. The current roster of Operator Identification Numbers / Restricted Materials Permit numbers issued by {county} County (county code {code}), together with the permittee/operator name (business or individual) and mailing city/ZIP for each, for permits active at any time during 2020-2026.

2. If maintained as such, your "Permits, Sites, and Commodities" export (or the equivalent CalAgPermits report) for the same period.

The purpose is to attach real operator names to California Pesticide Use Report records, which CDPR publishes only as coded permit numbers. We are not requesting any confidential application-site detail beyond what is already public in the PUR - only the operator-ID to name correspondence.

Preferred format: a machine-readable file (CSV or Excel); a column of operator/permit IDs and a column of names is sufficient.

This request serves the public interest in government transparency; please waive duplication fees if possible. If costs will exceed $25, please contact me first with an estimate.

Please let me know within the 10-day period (Gov. Code section 7922.535) whether the records exist and when they will be produced.

Thank you,
SprayMap California
spraymapca@gmail.com"""

def main():
    out = []
    for county, n in g.PRIORITY:
        c = g.CONTACTS.get(county, {})
        email = c.get("email")
        if not email:
            continue
        body = BODY.format(county=county, code=g.CC[county])
        url = (f"https://mail.google.com/mail/u/{UIDX}/?view=cm&fs=1"
               f"&to={urllib.parse.quote(email)}"
               f"&su={urllib.parse.quote(SUBJECT)}"
               f"&body={urllib.parse.quote(body)}")
        out.append({"county": county, "to": email, "url": url})
    print(json.dumps(out))

if __name__ == "__main__":
    main()
