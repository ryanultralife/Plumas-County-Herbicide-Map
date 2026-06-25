-- Map aggregation for Supabase/Postgres.
-- Collapses the millions of rows in `applications` into one row per ~PLSS section
-- (rounded lat/lon), with a year|class|land cross-tab + top active ingredients baked
-- in as JSON — the shape map.html expects. Re-run after each load.

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
    round(sum(case when unit = 'Pounds' then coalesce(amount, 0) else 0 end)::numeric, 1) as lbs,
    max(county)             as county,
    max(region)             as region
  from public.applications
  where lat is not null and lon is not null and year >= 2020
  group by 1, 2, 3
),
agg as (
  select lat, lon, max(county) county, max(region) region,
         sum(cnt)::int n, round(sum(lbs)::numeric,1) lbs,
         jsonb_object_agg(ck, to_jsonb(array[cnt::numeric, lbs])) as c
  from cells group by lat, lon
),
ai_ranked as (
  select round(lat::numeric,3) lat, round(lon::numeric,3) lon, active_ingredient ai, count(*) c,
         row_number() over (partition by round(lat::numeric,3), round(lon::numeric,3) order by count(*) desc) rn
  from public.applications
  where lat is not null and lon is not null and year >= 2020
    and active_ingredient is not null and active_ingredient <> ''
    and active_ingredient not ilike '%FOIA%' and active_ingredient not ilike '%not public%'
  group by 1, 2, 3
),
ai_top as (
  select lat, lon, jsonb_agg(jsonb_build_array(ai, c) order by c desc) filter (where rn <= 5) as ai
  from ai_ranked group by lat, lon
)
select a.lat, a.lon, a.county, a.region, a.n, a.lbs, a.c, coalesce(t.ai, '[]'::jsonb) as ai
from agg a left join ai_top t using (lat, lon);

create unique index if not exists map_agg_ll on public.map_agg (lat, lon);

-- expose the aggregated view (read-only) to the public anon role for the map;
-- the base `applications` table stays private (RLS, no anon grant).
grant select on public.map_agg to anon;

-- After every load:  refresh materialized view concurrently public.map_agg;
