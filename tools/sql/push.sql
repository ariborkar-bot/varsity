-- Varsity phone notifications (Web Push). Run once in the Supabase SQL editor.
-- push_subs : one row per phone that turned notifications on (the app saves it through push_save)
-- push_sent : which alert went to which phone, so nobody gets the same one twice
-- push_state: when the sender last ran (the app only relies on the server if this is recent)
-- Nobody can read these tables from the app: they have no policies. The app uses the two functions at the bottom,
-- and the sender (tools/push/send.mjs) uses the service_role key, which bypasses the rules.

create table if not exists public.push_subs (
  endpoint   text primary key,
  uid        uuid not null references auth.users(id) on delete cascade,
  sport      text not null check (sport in ('fb','bb')),
  p256dh     text not null,
  auth       text not null,
  school     text,
  tz         text not null default 'America/Los_Angeles',
  cats       jsonb not null default '{}'::jsonb,
  quiet      jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists push_subs_uid on public.push_subs(uid);

create table if not exists public.push_sent (
  endpoint text not null,
  key      text not null,
  at       timestamptz not null default now(),
  primary key (endpoint, key)
);
create index if not exists push_sent_at on public.push_sent(at);

create table if not exists public.push_state (
  id       int primary key,
  last_run timestamptz,
  sent     int
);

alter table public.push_subs  enable row level security;
alter table public.push_sent  enable row level security;
alter table public.push_state enable row level security;

-- The phone saves (or refreshes) its own subscription. A phone that signs in as someone else moves to that account.
-- Returns when the sender last ran, so the app knows whether the server is doing the sending.
create or replace function public.push_save(
  p_endpoint text, p_sport text, p_p256dh text, p_auth text,
  p_school text, p_tz text, p_cats jsonb, p_quiet jsonb
) returns timestamptz
language plpgsql security definer set search_path = public as $$
declare me uuid := auth.uid();
begin
  if me is null then raise exception 'sign in first'; end if;
  if p_sport not in ('fb','bb') then raise exception 'bad sport'; end if;
  if coalesce(length(p_endpoint),0) < 20 or length(p_endpoint) > 1000 then raise exception 'bad endpoint'; end if;
  insert into public.push_subs(endpoint, uid, sport, p256dh, auth, school, tz, cats, quiet)
  values (p_endpoint, me, p_sport, p_p256dh, p_auth, nullif(left(p_school,80),''), coalesce(nullif(left(p_tz,60),''),'America/Los_Angeles'),
          coalesce(p_cats,'{}'::jsonb), coalesce(p_quiet,'{}'::jsonb))
  on conflict (endpoint) do update
    set uid = me, sport = excluded.sport, p256dh = excluded.p256dh, auth = excluded.auth, school = excluded.school,
        tz = excluded.tz, cats = excluded.cats, quiet = excluded.quiet, updated_at = now();
  return (select last_run from public.push_state where id = 1);
end $$;

-- Turn this phone's notifications off.
create or replace function public.push_remove(p_endpoint text) returns void
language sql security definer set search_path = public as $$
  delete from public.push_subs where endpoint = p_endpoint and uid = auth.uid();
$$;

revoke all on function public.push_save(text,text,text,text,text,text,jsonb,jsonb) from public;
revoke all on function public.push_remove(text) from public;
grant execute on function public.push_save(text,text,text,text,text,text,jsonb,jsonb) to authenticated;
grant execute on function public.push_remove(text) to authenticated;
