-- v2: baseline + recompute RPC so donation_totals = baseline + sum(Completed events).
-- Both the real-time webhook and the daily job call the same recompute -> always consistent.
-- Additive/idempotent; no destructive changes.

create table if not exists public.donation_baseline (
  effort text primary key,
  gross  numeric(12,2) not null default 0,
  net    numeric(12,2) not null default 0,
  count  integer       not null default 0
);

-- Pre-automation figures (the $5 Water testing gift received before the webhook existed).
insert into public.donation_baseline (effort, gross, net, count) values
  ('SprayMap California', 0, 0, 0),
  ('Water testing',       5, 4.37, 1),
  ('Goat grazing',        0, 0, 0)
on conflict (effort) do nothing;

-- Recompute totals = baseline + sum(Completed events), for every baseline effort.
create or replace function public.recompute_donation_totals()
  returns void
  language plpgsql
  security definer
  set search_path = public
as $$
begin
  insert into public.donation_totals (effort, gross, net, count, updated_at)
  select b.effort,
         b.gross + coalesce(e.g, 0),
         b.net   + coalesce(e.n, 0),
         b.count + coalesce(e.c, 0),
         now()
  from public.donation_baseline b
  left join (
    select effort, sum(gross) g, sum(net) n, count(*) c
    from public.donation_events
    where status = 'Completed'
    group by effort
  ) e on e.effort = b.effort
  on conflict (effort) do update
    set gross = excluded.gross,
        net   = excluded.net,
        count = excluded.count,
        updated_at = now();
end
$$;

-- Only the server-side service_role should recompute; keep it off the public API.
revoke all on function public.recompute_donation_totals() from public, anon, authenticated;
grant execute on function public.recompute_donation_totals() to service_role;

-- Establish totals from the baseline now (events table is empty at first).
select public.recompute_donation_totals();

notify pgrst, 'reload schema';
