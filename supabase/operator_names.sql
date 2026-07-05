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
  updated     text,
  agent       text    -- permit "agent of record" (PCA / farm manager) when the county
                      -- roster names one distinct from the operator; see enrich_operator_names.py
);
alter table public.operator_names add column if not exists agent text;

-- Public READ-ONLY. Supabase's default privileges GRANT ALL on new public tables to
-- anon/authenticated, which would let the public anon key INSERT/UPDATE/DELETE/TRUNCATE
-- this table (found + closed 2026-07-01 during the launch audit). Grant only SELECT and
-- explicitly revoke every write privilege. The enrichment pipeline writes via the
-- privileged DBURL, not the anon role.
revoke insert, update, delete, truncate, references, trigger on public.operator_names from anon, authenticated;
grant select on public.operator_names to anon;  -- names are public records
