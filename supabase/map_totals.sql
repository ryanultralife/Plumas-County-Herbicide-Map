-- Live site totals for the share/search metadata (read by middleware.js) and any client.
-- Reads only the public map_agg view, so anon may call it. Cheap: ~37k rows.
create or replace function public.map_totals()
returns json
language sql
stable
as $$
  select json_build_object(
    'mapped', coalesce(sum(n), 0)::bigint,
    'cells',  count(*)::bigint,
    'lbs',    round(coalesce(sum(lbs), 0)::numeric, 0),
    'as_of',  now()
  )
  from public.map_agg;
$$;
revoke all on function public.map_totals() from public;
grant execute on function public.map_totals() to anon, authenticated, service_role;
