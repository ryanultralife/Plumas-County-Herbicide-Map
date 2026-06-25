-- Jurisdiction rollup for index.html's Data & Trends tab + region/county scope selector.
-- One row per jurisdiction at three levels (statewide / region / county) with the EXACT
-- top active ingredients and top applicators (these can't be derived exactly from map_agg's
-- per-cell top-5). The by-year / by-class / by-land / by-source breakdowns are rolled up
-- client-side from the already-loaded map_agg CELLS, so they stay in sync with the map and
-- need no second view here.
--
-- Universe = the MAPPED data (lat/lon present, year>=2020) so every number matches the map.
-- Re-run after each load.  Build with statement_timeout=0 (full-table grouping scans).

drop materialized view if exists public.juris_agg cascade;

create materialized view public.juris_agg as
with
-- exact AI counts at all three levels in one scan (grouping sets)
ai_g as (
  select
    case when grouping(region)=1 then 'state'
         when grouping(county)=1 then 'region' else 'county' end as level,
    region, county, active_ingredient ai, count(*)::bigint c
  from public.applications
  where year between 2020 and 2026 and lat is not null and lon is not null
    and active_ingredient is not null and active_ingredient<>''
    and active_ingredient not ilike '%FOIA%' and active_ingredient not ilike '%not public%'
  group by grouping sets ((active_ingredient),(region,active_ingredient),(region,county,active_ingredient))
),
ai_r as (
  select level, region, county, ai, c,
         row_number() over (partition by level, region, county order by c desc, ai) rn
  from ai_g
),
ai_t as (
  select level, region, county,
         jsonb_agg(jsonb_build_array(ai,c) order by c desc) filter (where rn<=20) top_ai
  from ai_r where rn<=20 group by level, region, county
),
-- exact applicator/owner counts at all three levels in one scan
own_g as (
  select
    case when grouping(region)=1 then 'state'
         when grouping(county)=1 then 'region' else 'county' end as level,
    region, county, owner, count(*)::bigint c
  from public.applications
  where year between 2020 and 2026 and lat is not null and lon is not null
    and owner is not null and owner<>''
  group by grouping sets ((owner),(region,owner),(region,county,owner))
),
own_r as (
  select level, region, county, owner, c,
         row_number() over (partition by level, region, county order by c desc, owner) rn
  from own_g
),
own_t as (
  select level, region, county,
         jsonb_agg(jsonb_build_array(owner,c) order by c desc) filter (where rn<=20) top_owners
  from own_r where rn<=20 group by level, region, county
)
select
  coalesce(a.level,o.level) level,
  coalesce(a.region,o.region) region,
  coalesce(a.county,o.county) county,
  coalesce(a.top_ai,'[]'::jsonb) top_ai,
  coalesce(o.top_owners,'[]'::jsonb) top_owners
from ai_t a
full outer join own_t o
  on a.level=o.level
 and a.region is not distinct from o.region
 and a.county is not distinct from o.county;

create unique index if not exists juris_agg_key
  on public.juris_agg (level, coalesce(region,''), coalesce(county,''));

grant select on public.juris_agg to anon;  -- raw applications stays RLS-private

-- After every load:  refresh materialized view concurrently public.juris_agg;
