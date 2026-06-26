-- Public crosswalk: CDPR operator/permit ID -> real permittee NAME.
-- CDPR does not publish operator names; the only source is the County Agricultural
-- Commissioner, obtained via CPRA requests (see records-requests/). Responses are
-- loaded with build/ingest_operator_names.py. The frontend (index.html
-- loadOperatorNames) reads this table and applicatorInfo() prefers a real name over
-- the decoded permit label. Empty until the first county responds.
create table if not exists public.operator_names(
  operator_id text primary key,
  name        text not null,
  entity_type text,   -- government | grower | commercial-applicator | district | utility | ...
  source      text,   -- e.g. 'cac-fresno-2026', 'license', 'manual'
  county      text,
  updated     text
);
grant select on public.operator_names to anon;  -- names are public records
