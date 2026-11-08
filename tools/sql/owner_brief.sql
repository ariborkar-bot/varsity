-- Varsity: read-only totals for the daily owner brief.
-- Run once in the Supabase SQL editor (project "varsity"). Safe to run again.
--
-- public.owner_brief(token) returns ONE json object of totals: sign-ups, active users, minutes, sponsor videos,
-- Field Goal / Hoops daily players, 5 Card Draw hands, errors, leagues and members per school.
-- It returns no names, no emails and no user ids. It only answers a caller that sends the secret token:
-- the table below stores a SHA-256 hash of the token, never the token itself.
-- To change the token later: delete the row in brief_keys and insert the hash of a new one.
-- To switch the brief off for good: drop function public.owner_brief(text);

create table if not exists public.brief_keys (h text primary key, note text, created_at timestamptz default now());
alter table public.brief_keys enable row level security;           -- no policies: the API can never read or write this table
revoke all on public.brief_keys from public, anon, authenticated;
insert into public.brief_keys (h, note) values ('6ec478f653b0477ef7c7cf1a777e93e72bd88216ffcb1c17511f83894d9f6092', 'owner brief scheduled task') on conflict (h) do nothing;

create or replace function public.owner_brief(p_token text)
returns jsonb
language plpgsql
security definer
set search_path = public, auth, pg_temp
as $fn$
declare
  -- accounts left out of every number (the two admin accounts). Add the second admin's email here.
  admin_emails text[] := array['zedbhornby@gmail.com'];
  tz   text := 'America/Los_Angeles';
  today date := (now() at time zone 'America/Los_Angeles')::date;
  yday date;
  ts0  bigint;
  res  jsonb;
begin
  if p_token is null or not exists (select 1 from public.brief_keys where h = encode(sha256(convert_to(p_token, 'UTF8')), 'hex')) then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  yday := today - 1;
  ts0  := (extract(epoch from now() - interval '24 hours') * 1000)::bigint;

  with
  acc as (select id::text as uid, created_at from auth.users where lower(coalesce(email, '')) <> all (admin_emails)),
  use_docs as (
    select split_part(coll, '/', 3) as uid, case when coll like 'bb\_%' then 'bb' else 'fb' end as sp, data
      from public.docs where id = 'usage' and (coll like 'data/users/%' or coll like 'bb\_data/users/%')),
  use_ok as (select u.* from use_docs u join acc a on a.uid = u.uid),
  per_user_y as (
    select uid,
           sum(coalesce((data->'days'->>(yday::text))::numeric, 0)) as secs,
           sum(coalesce((data->'ses' ->>(yday::text))::numeric, 0)) as opens,
           sum(coalesce((data->'ads' ->>(yday::text))::numeric, 0)) as ads
      from use_ok group by uid),
  tabs_y as (
    select t.key as tab, sum((t.value)::numeric) as secs
      from use_ok, lateral jsonb_each_text(coalesce(data->'tv'->(yday::text), '{}'::jsonb)) t group by t.key order by 2 desc limit 6),
  fg as (
    select p.id as uid, case when p.coll like 'bb\_%' then 'Hoops' else 'Field Goal' end as g, (p.data->'fg'->'dh'->(yday::text)->>'b')::numeric as best
      from public.docs p join acc a on a.uid = p.id
     where p.coll in ('picks', 'bb_picks') and p.data->'fg'->'dh' ? (yday::text)),
  hands as (
    select p.id as uid, count(*) as n
      from public.docs p join acc a on a.uid = p.id, lateral jsonb_each(coalesce(p.data->'fc', '{}'::jsonb)) h
     where p.coll in ('picks', 'bb_picks') and (h.value->>'at') ~ '^[0-9]+$' and (h.value->>'at')::bigint >= ts0 group by p.id),
  errs as (
    select e.value->>'m' as m, e.value->>'b' as b
      from public.docs d, lateral jsonb_array_elements(coalesce(d.data->'list', '[]'::jsonb)) e
     where d.id = 'errors' and (d.coll like 'data/users/%' or d.coll like 'bb\_data/users/%')
       and (e.value->>'t') ~ '^[0-9]+$' and (e.value->>'t')::bigint >= ts0),
  err_top as (select left(m, 90) as m, count(*) as n from errs group by 1 order by 2 desc limit 3),
  prof as (select p.id as uid, p.data->>'school' as school, p.data->>'role' as role from public.docs p join acc a on a.uid = p.id where p.coll = 'profiles'),
  schools as (select school, count(*) as n from prof where coalesce(school, '') <> '' group by school),
  leagues as (
    select coll, (data->>'kind') as kind, (data->>'createdAt') as c from public.docs where coll in ('groups', 'fgroups', 'bb_groups', 'bb_fgroups'))
  select jsonb_build_object(
    'as_of', to_char(now() at time zone tz, 'YYYY-MM-DD HH24:MI') || ' PT',
    'day_reported', yday,
    'accounts_total', (select count(*) from acc),
    'accounts_with_profile', (select count(*) from prof),
    'players', (select count(*) from prof where role = 'player'),
    'fans', (select count(*) from prof where role = 'fan'),
    'signups_yesterday', (select count(*) from acc where (created_at at time zone tz)::date = yday),
    'signups_today', (select count(*) from acc where (created_at at time zone tz)::date = today),
    'signups_last_7_days', (select count(*) from acc where (created_at at time zone tz)::date >= today - 7 and (created_at at time zone tz)::date < today),
    'active_yesterday', (select count(*) from per_user_y where secs > 0 or opens > 0),
    'active_yesterday_football', (select count(distinct uid) from use_ok where sp = 'fb' and (data->'days' ? (yday::text) or data->'ses' ? (yday::text))),
    'active_yesterday_basketball', (select count(distinct uid) from use_ok where sp = 'bb' and (data->'days' ? (yday::text) or data->'ses' ? (yday::text))),
    'active_last_7_days', (select count(distinct uid) from use_ok u where exists (select 1 from generate_series(1, 7) k where u.data->'days' ? ((today - k)::text) or u.data->'ses' ? ((today - k)::text))),
    'minutes_yesterday', (select round(coalesce(sum(secs), 0) / 60) from per_user_y),
    'app_opens_yesterday', (select coalesce(sum(opens), 0) from per_user_y),
    'sponsor_videos_yesterday', (select coalesce(sum(ads), 0) from per_user_y),
    'top_tabs_yesterday_minutes', coalesce((select jsonb_object_agg(tab, round(secs / 60)) from tabs_y), '{}'::jsonb),
    'daily_game_players_yesterday', jsonb_build_object(
        'field_goal', (select count(*) from fg where g = 'Field Goal'), 'hoops', (select count(*) from fg where g = 'Hoops'),
        'best_field_goal', (select max(best) from fg where g = 'Field Goal'), 'best_hoops', (select max(best) from fg where g = 'Hoops')),
    'five_card_hands_last_24h', (select coalesce(sum(n), 0) from hands),
    'errors_last_24h', (select count(*) from errs),
    'errors_top', coalesce((select jsonb_agg(jsonb_build_object('msg', m, 'n', n)) from err_top), '[]'::jsonb),
    'error_builds_last_24h', coalesce((select jsonb_agg(distinct b) from errs where coalesce(b, '') <> ''), '[]'::jsonb),
    'leagues_total', (select count(*) from leagues),
    'leagues_pick_em', (select count(*) from leagues where kind = 'pk'),
    'leagues_created_last_7_days', (select count(*) from leagues where c ~ '^[0-9]+$' and (c::bigint) >= (extract(epoch from now() - interval '7 days') * 1000)::bigint),
    'schools_with_members', (select count(*) from schools),
    'schools_with_3_plus', (select count(*) from schools where n >= 3),
    'top_schools_by_members', coalesce((select jsonb_agg(jsonb_build_object('school', school, 'members', n)) from (select * from schools order by n desc, school limit 8) s), '[]'::jsonb)
  ) into res;
  return res;
end
$fn$;

revoke all on function public.owner_brief(text) from public;
grant execute on function public.owner_brief(text) to anon, authenticated;
