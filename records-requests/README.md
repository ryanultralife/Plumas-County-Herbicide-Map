# Records requests — getting real operator names

California's public Pesticide Use Reports identify the operator only by a coded
**Operator Identification Number / permit number** (leading 2 digits = county code).
CDPR does **not** collect or publish operator names — by their own statement, names
are held only by the **County Agricultural Commissioner**. So real names can only be
obtained per county, via a Public Records Act (CPRA) request. (See
`memory/applicator-ids` for the full decode + research.)

## Workflow
1. **Generate letters:** `python build/gen_records_requests.py` → `letters/*.md`
   (one per priority county, ordered by spray volume; Plumas included as home county).
2. **Send** each letter to that county's Agricultural Commissioner (address via
   https://www.cacasa.org/county-directory/ or CDPR's portal
   https://cdprca.nextrequest.com). Fill in your reply email first.
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
