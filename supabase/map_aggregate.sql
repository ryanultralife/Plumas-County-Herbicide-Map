-- Map aggregation for Supabase/Postgres.
-- Collapses the millions of rows in `applications` into one row per ~PLSS section
-- (rounded lat/lon), with a year|class|land cross-tab baked in as JSON — the same
-- shape map.html already expects. Run this in the Supabase SQL editor.
--
-- Assumes the table is `public.applications` with the project's standard columns
-- (lat, lon, county, region, year, land_type, chem_class, amount, source).
-- Adjust names below if your loader used different ones.

drop materialized view if exists public.map_agg;

create materialized view public.map_agg as
with cells as (
  select
    round(lat::numeric, 3)  as lat,
    round(lon::numeric, 3)  as lon,
    coalesce(year::text, '') || '|' ||
      coalesce(chem_class, 'unknown') || '|' ||
      coalesce(land_type, 'unknown')  as ck,
    count(*)::int           as cnt,
    round(sum(case when source = 'pur'   then coalesce(amount, 0) else 0 end)::numeric, 1) as lbs,
    max(county)             as county,
    max(region)             as region
  from public.applications
  where lat is not null and lon is not null and year >= 2020
  group by 1, 2, 3
)
select
  lat, lon,
  max(county)                          as county,
  max(region)                          as region,
  sum(cnt)::int                        as n,
  round(sum(lbs)::numeric, 1)          as lbs,
  jsonb_object_agg(ck, to_jsonb(array[cnt::numeric, lbs])) as c
from cells
group by lat, lon;

-- unique index lets you REFRESH ... CONCURRENTLY after each data load
create unique index if not exists map_agg_ll on public.map_agg (lat, lon);

-- expose the aggregated view (read-only) to the public anon role for the map;
-- the base `applications` table stays private (do NOT grant it to anon).
grant select on public.map_agg to anon;

-- After every load:  refresh materialized view concurrently public.map_agg;
