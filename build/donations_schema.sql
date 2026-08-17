-- Donation totals + event log for the auto-updating Transparency donations display.
-- Additive only: CREATE ... IF NOT EXISTS, seed with ON CONFLICT DO NOTHING.
-- Site (anon key) reads donation_totals; the /api functions (service role) write.

create table if not exists public.donation_totals (
  effort      text primary key,
  gross       numeric(12,2) not null default 0,
  net         numeric(12,2) not null default 0,
  count       integer       not null default 0,
  updated_at  timestamptz   not null default now()
);

create table if not exists public.donation_events (
  txn_id      text primary key,          -- PayPal transaction id (idempotency key)
  effort      text not null,
  button_id   text,                      -- PayPal hosted_button_id, if present
  item_name   text,                      -- raw PayPal item_name (attribution source)
  gross       numeric(10,2) not null default 0,
  fee         numeric(10,2) not null default 0,
  net         numeric(10,2) not null default 0,
  currency    text default 'USD',
  status      text,                      -- Completed / Pending / etc.
  source      text default 'ipn',        -- ipn | reconcile | manual
  raw         jsonb,                     -- full PayPal payload (confirms attribution)
  created_at  timestamptz not null default now()
);

-- Seed the three efforts with the real figures known as of 2026-08-17
-- (Water testing: one $5.00 gift, ~$4.37 net after fees; others $0).
insert into public.donation_totals (effort, gross, net, count) values
  ('SprayMap California', 0, 0, 0),
  ('Water testing',       5, 4.37, 1),
  ('Goat grazing',        0, 0, 0)
on conflict (effort) do nothing;

-- Row-level security: public may READ totals only; nobody writes via the anon/public API.
alter table public.donation_totals enable row level security;
alter table public.donation_events enable row level security;

drop policy if exists donation_totals_public_read on public.donation_totals;
create policy donation_totals_public_read
  on public.donation_totals for select
  to anon, authenticated
  using (true);
-- No policies on donation_events => not readable/writable via anon/authenticated.
-- The service_role key (used only server-side in the Vercel functions) bypasses RLS.

grant select on public.donation_totals to anon, authenticated;

-- PostgREST: reload schema cache so the new table is exposed immediately.
notify pgrst, 'reload schema';
