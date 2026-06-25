-- Map aggregation for Supabase/Postgres.
-- One row per ~PLSS section (rounded lat/lon) for index.html's statewide map:
--   c   = year|class|land cross-tab -> [cnt,lbs]   (drives class layers + by-class/year popup)
--   src = source -> [cnt,lbs]                       (drives source layers: pur/facts/thp)
--   ai  = top-5 active ingredients [name,cnt]
--   owners = top-5 owners/applicators [name,cnt]
-- Re-run after each load.

drop materialized view if exists public.map_agg;

create materialized view public.map_agg as
with cells as (
  select round(lat::numeric,3) lat, round(lon::numeric,3) lon,
    coalesce(year::text,'')||'|'||coalesce(public.chem_class(active_ingredient),'unknown')||'|'||coalesce(land_type,'unknown') as ck,
    count(*)::int cnt,
    round(sum(case when unit='Pounds' then coalesce(amount,0) else 0 end)::numeric,1) lbs,
    max(county) county, max(region) region
  from public.applications where lat is not null and lon is not null and year>=2020
  group by 1,2,3
),
agg as (
  select lat, lon, max(county) county, max(region) region, sum(cnt)::int n,
         round(sum(lbs)::numeric,1) lbs, jsonb_object_agg(ck, to_jsonb(array[cnt::numeric,lbs])) c
  from cells group by lat, lon
),
src_agg as (
  select lat, lon, jsonb_object_agg(source, arr) src from (
    select round(lat::numeric,3) lat, round(lon::numeric,3) lon, coalesce(source,'?') source,
           array[count(*)::numeric, round(sum(case when unit='Pounds' then coalesce(amount,0) else 0 end)::numeric,1)] arr
    from public.applications where lat is not null and lon is not null and year>=2020 group by 1,2,3
  ) s group by lat, lon
),
ai_ranked as (
  select round(lat::numeric,3) lat, round(lon::numeric,3) lon, active_ingredient ai, count(*) c,
         row_number() over (partition by round(lat::numeric,3),round(lon::numeric,3) order by count(*) desc) rn
  from public.applications where lat is not null and lon is not null and year>=2020
    and active_ingredient is not null and active_ingredient<>''
    and active_ingredient not ilike '%FOIA%' and active_ingredient not ilike '%not public%'
  group by 1,2,3
),
ai_top as (select lat, lon, jsonb_agg(jsonb_build_array(ai,c) order by c desc) filter (where rn<=5) ai from ai_ranked group by lat, lon),
own_ranked as (
  select round(lat::numeric,3) lat, round(lon::numeric,3) lon, owner, count(*) c,
         row_number() over (partition by round(lat::numeric,3),round(lon::numeric,3) order by count(*) desc) rn
  from public.applications where lat is not null and lon is not null and year>=2020 and owner is not null and owner<>''
  group by 1,2,3
),
own_top as (select lat, lon, jsonb_agg(jsonb_build_array(owner,c) order by c desc) filter (where rn<=5) owners from own_ranked group by lat, lon)
select a.lat, a.lon, a.county, a.region, a.n, a.lbs, a.c,
       coalesce(t.ai,'[]'::jsonb) ai, coalesce(s.src,'{}'::jsonb) src, coalesce(o.owners,'[]'::jsonb) owners
from agg a
  left join ai_top  t using (lat, lon)
  left join src_agg s using (lat, lon)
  left join own_top o using (lat, lon);

create unique index if not exists map_agg_ll on public.map_agg (lat, lon);
grant select on public.map_agg to anon;  -- raw applications table stays RLS-private

-- After every load:  refresh materialized view concurrently public.map_agg;
