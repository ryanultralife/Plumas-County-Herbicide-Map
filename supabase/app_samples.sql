-- Anon-readable RECORD SAMPLE for index.html's Source Data tab.
-- Live record queries over the 11.8M-row table exceed the anon statement timeout
-- (region-level ~11s), and the raw table is RLS-private. So we precompute a small,
-- representative sample: the top 80 reported applications by amount per county
-- (the most significant sprays), which is what a reviewer most wants to see.
-- ~58 counties x 80 = ~4,600 rows. Region/state scope = filter by region / all.
-- Re-run after each load.

drop materialized view if exists public.app_samples cascade;

create materialized view public.app_samples as
select region, county, date, year, active_ingredient, product, amount, unit, method, owner, source
from (
  select region, county, date, year, active_ingredient, product, amount, unit, method, owner, source,
         row_number() over (partition by county order by amount desc nulls last) rn
  from public.applications
  where year between 2020 and 2026 and lat is not null and lon is not null
) t
where rn <= 80;

create index if not exists app_samples_county on public.app_samples (county);
create index if not exists app_samples_region on public.app_samples (region);
grant select on public.app_samples to anon;  -- a curated sample only; raw table stays RLS-private

-- After every load:  refresh materialized view concurrently public.app_samples;  (needs a unique index; just drop+recreate via this file)
