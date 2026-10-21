-- Network sign-ups (mailing list + action list) from the site's Donate / Contact / Network
-- modal and from people who email spraymapca@gmail.com asking to be added.
-- Additive only: CREATE ... IF NOT EXISTS. Apply once with: psql "$DBURL" -f build/network_signups_schema.sql
--
-- PRIVATE: names and emails are personal data. RLS on, NO policies, and every privilege
-- revoked from anon/authenticated, so the public anon key in index.html can neither read
-- nor write this table. Only the service role writes (api/network-signup.js on Vercel)
-- and the DBURL owner reads (build/network_signup.py, psql).

create table if not exists public.network_signups (
  email           text primary key,                 -- stored lower-cased; one row per person
  name            text,
  lists           text[] not null default '{}',     -- 'mailing' (events + updates), 'action' (work parties)
  source          text not null default 'site',     -- site | email | event | manual
  note            text,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  unsubscribed_at timestamptz,                      -- set instead of deleting, so a re-import can't re-add them
  constraint network_signups_email_lower check (email = lower(email)),
  constraint network_signups_email_shape check (email ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
  constraint network_signups_lists_known check (lists <@ array['mailing','action']::text[])
);

alter table public.network_signups enable row level security;
revoke all on public.network_signups from anon, authenticated;

-- Upsert that MERGES lists instead of overwriting them, keeps the first created_at and
-- source, and never re-subscribes someone who unsubscribed. Called by the API and the CLI.
create or replace function public.network_signup(p_email text, p_name text, p_lists text[], p_source text, p_note text default null)
returns text language plpgsql security definer set search_path = public as $$
declare e text := lower(btrim(p_email)); r public.network_signups; existed boolean;
begin
  select * into r from public.network_signups where email = e;
  existed := found;
  if existed and r.unsubscribed_at is not null then return 'unsubscribed'; end if;
  insert into public.network_signups(email, name, lists, source, note)
  values (e, nullif(btrim(p_name),''), coalesce(p_lists,'{}'), coalesce(nullif(p_source,''),'site'), p_note)
  on conflict (email) do update set
    name       = coalesce(excluded.name, network_signups.name),
    lists      = array(select distinct unnest(network_signups.lists || excluded.lists) order by 1),
    note       = coalesce(excluded.note, network_signups.note),
    updated_at = now();
  return case when existed then 'updated' else 'added' end;
end $$;
revoke all on function public.network_signup(text,text,text[],text,text) from public, anon, authenticated;
grant execute on function public.network_signup(text,text,text[],text,text) to service_role;

notify pgrst, 'reload schema';
