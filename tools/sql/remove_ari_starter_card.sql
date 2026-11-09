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
