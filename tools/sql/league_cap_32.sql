-- Varsity: leagues hold at most 32 teams (Nov 6 2026). Run once in the Supabase SQL editor (project "varsity").
-- Replaces join_league from league_security_and_account_delete.sql: same behaviour, plus
--   * someone already in the league just gets the league id back (no change), and
--   * a league that already has 32 members raises 'league full' (the app shows "That league is full (32 teams max)").
-- Friend groups (fgroups / bb_fgroups) are not capped.
create or replace function public.join_league(p_coll text, p_code text)
returns text language plpgsql security definer set search_path to 'public' as $$
declare v_id text; v_members jsonb;
begin
  if auth.uid() is null then raise exception 'sign in first' using errcode = '42501'; end if;
  if p_coll not in ('groups','fgroups','bb_groups','bb_fgroups') then raise exception 'bad collection'; end if;
  select id, coalesce(data->'members','{}'::jsonb) into v_id, v_members
    from public.docs where coll = p_coll and data->>'code' = upper(trim(coalesce(p_code,''))) limit 1;
  if v_id is null then return null; end if;
  if v_members ? auth.uid()::text then return v_id; end if;
  if p_coll in ('groups','bb_groups') and (select count(*) from jsonb_object_keys(v_members)) >= 32 then
    raise exception 'league full' using errcode = 'P0001';
  end if;
  update public.docs
     set data = public.jsonb_deep_merge(data, jsonb_build_object('members', jsonb_build_object(auth.uid()::text, (extract(epoch from now())*1000)::bigint))),
         updated_at = now()
   where coll = p_coll and id = v_id;
  return v_id;
end $$;
revoke all on function public.join_league(text,text) from public, anon;
grant execute on function public.join_league(text,text) to authenticated;
