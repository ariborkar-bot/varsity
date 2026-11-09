-- v346 (Nov 8 2026, owner): take the Starter pick Legendary (Reid Dielman) off Ari Borkar's account right away.
-- The app does the same thing by itself the next time Ari opens it (spRevoke); running this just makes it immediate.
-- Run in the Supabase SQL editor. It only touches docs whose profile name is exactly "Ari Borkar" and that have a Starter pick.
with a as (
  select id from public.docs where coll = 'profiles' and lower(trim(data->>'name')) = 'ari borkar'
)
update public.docs d
   set data = jsonb_set(
                jsonb_set(d.data, array['inv','cards','pc:' || (d.data->'inv'->'fr'->'sp'->>'k'), 'l'], '0'::jsonb, true),
                '{inv,fr,spx}', '1'::jsonb, true),
       updated_at = now()
 where d.coll in ('picks','bb_picks')
   and d.id in (select id from a)
   and d.data->'inv'->'fr'->'sp'->>'k' is not null
returning d.coll, d.id, d.data->'inv'->'fr'->'sp' as starter_pick;

-- v347 (owner): also take the Legendary Isaiah Garcia (Bishop's, card pc:mp461) off Zed Hornby's football account.
-- The app does this by itself on Zed's next app open (cardFix); this makes it immediate.
with z as (
  select id from public.docs where coll = 'profiles' and lower(trim(data->>'name')) = 'zed hornby'
)
update public.docs d
   set data = jsonb_set(
                jsonb_set(d.data, '{inv,cards,pc:mp461,l}', '0'::jsonb, true),
                '{inv,fr,rv}', coalesce(d.data->'inv'->'fr'->'rv','{}'::jsonb) || '{"zh-ig":1}'::jsonb, true),
       updated_at = now()
 where d.coll = 'picks'
   and d.id in (select id from z)
   and (d.data->'inv'->'cards'->'pc:mp461'->>'l') is not null
returning d.id, d.data->'inv'->'cards'->'pc:mp461' as isaiah_garcia_card;

-- v349 (owner): remove EVERY version of Daine Gonzalez (pc:mp556o, pc:mp556d) from Ari Borkar and of Rory Dunn (pc:mp955) from Zed Hornby.
-- The app does this by itself on their next app open (cardFix); this makes it immediate. Each version is set to 0 (= not owned).
create or replace function pg_temp.zero_card(d jsonb, card text) returns jsonb language sql as $$
  select case when d->'inv'->'cards' ? card
    then jsonb_set(d, array['inv','cards',card], (select coalesce(jsonb_object_agg(k, 0), '{}'::jsonb) from jsonb_object_keys(d->'inv'->'cards'->card) k))
    else d end $$;
update public.docs d
   set data = pg_temp.zero_card(pg_temp.zero_card(d.data, 'pc:mp556o'), 'pc:mp556d'), updated_at = now()
 where d.coll = 'picks' and d.id in (select id from public.docs where coll = 'profiles' and lower(trim(data->>'name')) = 'ari borkar')
returning d.id, d.data->'inv'->'cards'->'pc:mp556o' as dg_rb, d.data->'inv'->'cards'->'pc:mp556d' as dg_def;
update public.docs d
   set data = pg_temp.zero_card(d.data, 'pc:mp955'), updated_at = now()
 where d.coll = 'picks' and d.id in (select id from public.docs where coll = 'profiles' and lower(trim(data->>'name')) = 'zed hornby')
returning d.id, d.data->'inv'->'cards'->'pc:mp955' as rory_dunn;

-- v350 (owner): give Rory Dunn back to Zed (any version that was set to 0 goes back to 1), remove every version of
-- Adrian Ismaili (pc:mp798o, pc:mp798d) from Ari and Zed, and give both a new welcome pack (inv.wp = 0).
-- Each fix is marked done in inv.fr.rv so the app does not repeat it. Run the pg_temp.zero_card function above first (same session).
create or replace function pg_temp.unzero_card(d jsonb, card text) returns jsonb language sql as $$
  select case when jsonb_typeof(d->'inv'->'cards'->card) = 'object'
    then jsonb_set(d, array['inv','cards',card], (select coalesce(jsonb_object_agg(k, case when v = '0'::jsonb then '1'::jsonb else v end), '{}'::jsonb) from jsonb_each(d->'inv'->'cards'->card) e(k, v)))
    else d end $$;
update public.docs d
   set data = jsonb_set(jsonb_set(pg_temp.unzero_card(pg_temp.zero_card(pg_temp.zero_card(d.data,'pc:mp798o'),'pc:mp798d'),'pc:mp955'),
                '{inv,wp}', '0'::jsonb, true),
                '{inv,fr,rv}', coalesce(d.data->'inv'->'fr'->'rv','{}'::jsonb) || '{"zh-rd-back":1,"ai-x":1,"wp-2":1}'::jsonb, true),
       updated_at = now()
 where d.coll = 'picks' and d.id in (select id from public.docs where coll = 'profiles' and lower(trim(data->>'name')) = 'zed hornby')
returning d.id, d.data->'inv'->'cards'->'pc:mp955' as rory_dunn;
update public.docs d
   set data = jsonb_set(jsonb_set(pg_temp.zero_card(pg_temp.zero_card(d.data,'pc:mp798o'),'pc:mp798d'),
                '{inv,wp}', '0'::jsonb, true),
                '{inv,fr,rv}', coalesce(d.data->'inv'->'fr'->'rv','{}'::jsonb) || '{"ai-x":1,"wp-2":1}'::jsonb, true),
       updated_at = now()
 where d.coll = 'picks' and d.id in (select id from public.docs where coll = 'profiles' and lower(trim(data->>'name')) = 'ari borkar')
returning d.id;
