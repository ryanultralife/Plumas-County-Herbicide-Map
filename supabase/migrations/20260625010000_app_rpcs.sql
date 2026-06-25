-- RPCs powering the unified drill-down app (Data & Trends + Source Data tabs).
-- SECURITY DEFINER so the public anon role gets SCOPED aggregates/records without the
-- raw RLS-private `applications` table being exposed. Backed by the region/county/year
-- indexes; county/region scopes are fast. Statewide default should use the precomputed
-- static summary.json / map_agg instead of calling app_summary with no scope.

-- Scoped summary: counts by year/class/land/source + top products/AIs/owners + totals.
create or replace function public.app_summary(p_region text default null, p_county text default null)
returns jsonb language sql stable security definer set search_path = public as $$
  with f as (
    select * from applications
    where year >= 2020
      and (p_region is null or region = p_region)
      and (p_county is null or county = p_county)
  )
  select jsonb_build_object(
    'scope', jsonb_build_object('region', p_region, 'county', p_county),
    'total', (select count(*) from f),
    'lbs',   (select round(coalesce(sum(case when unit='Pounds' then amount else 0 end),0)::numeric,1) from f),
    'acres', (select round(coalesce(sum(case when source='facts' then amount else 0 end),0)::numeric,1) from f),
    'by_year',   (select coalesce(jsonb_object_agg(y::text,n),'{}'::jsonb) from (select year y,count(*) n from f where year is not null group by year) t),
    'by_class',  (select coalesce(jsonb_object_agg(c,n),'{}'::jsonb) from (select chem_class(active_ingredient) c,count(*) n from f group by 1) t),
    'by_land',   (select coalesce(jsonb_object_agg(coalesce(land_type,'unknown'),n),'{}'::jsonb) from (select land_type,count(*) n from f group by land_type) t),
    'by_source', (select coalesce(jsonb_object_agg(source,n),'{}'::jsonb) from (select source,count(*) n from f group by source) t),
    'top_ai',    (select coalesce(jsonb_agg(jsonb_build_array(active_ingredient,n)),'[]'::jsonb) from (select active_ingredient,count(*) n from f where active_ingredient is not null and active_ingredient<>'' group by 1 order by n desc limit 15) t),
    'top_products', (select coalesce(jsonb_agg(jsonb_build_array(product,n)),'[]'::jsonb) from (select product,count(*) n from f where product is not null group by 1 order by n desc limit 15) t),
    'top_owners',(select coalesce(jsonb_agg(jsonb_build_array(owner,n)),'[]'::jsonb) from (select owner,count(*) n from f where owner is not null group by 1 order by n desc limit 15) t)
  );
$$;
grant execute on function public.app_summary(text,text) to anon;

-- Scoped + paginated raw records for the Source Data tab.
create or replace function public.app_records(
  p_region text default null, p_county text default null, p_class text default null,
  p_q text default null, p_limit int default 500, p_offset int default 0)
returns table(date text, county text, region text, land_type text, source text,
              product text, active_ingredient text, chem_class text, amount double precision,
              unit text, method text, owner text, project text, year integer)
language sql stable security definer set search_path = public as $$
  select a.date, a.county, a.region, a.land_type, a.source, a.product, a.active_ingredient,
         public.chem_class(a.active_ingredient), a.amount, a.unit, a.method, a.owner, a.project, a.year
  from applications a
  where a.year >= 2020
    and (p_region is null or a.region = p_region)
    and (p_county is null or a.county = p_county)
    and (p_class  is null or public.chem_class(a.active_ingredient) = p_class)
    and (p_q is null or a.product ilike '%'||p_q||'%' or a.active_ingredient ilike '%'||p_q||'%' or a.owner ilike '%'||p_q||'%')
  order by a.year desc nulls last, a.date desc nulls last
  limit least(coalesce(p_limit,500), 2000) offset coalesce(p_offset,0);
$$;
grant execute on function public.app_records(text,text,text,text,int,int) to anon;

-- distinct regions/counties for the drill-down selector (cheap, indexed)
create or replace function public.jurisdictions()
returns table(region text, county text, n bigint)
language sql stable security definer set search_path = public as $$
  select region, county, count(*) from applications where year>=2020 group by region, county order by region, county;
$$;
grant execute on function public.jurisdictions() to anon;
