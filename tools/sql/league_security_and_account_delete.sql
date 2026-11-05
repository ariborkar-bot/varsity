-- Varsity: league security, basketball parity, and self-service account deletion.
-- Run once in the Supabase SQL editor (project "varsity").

-- 1. Joining a league by invite code goes through this function, so non-members never need write access to a league.
create or replace function public.join_league(p_coll text, p_code text)
returns text language plpgsql security definer set search_path to 'public' as $$
declare v_id text;
begin
  if auth.uid() is null then raise exception 'sign in first' using errcode = '42501'; end if;
  if p_coll not in ('groups','fgroups','bb_groups','bb_fgroups') then raise exception 'bad collection'; end if;
  select id into v_id from public.docs where coll = p_coll and data->>'code' = upper(trim(coalesce(p_code,''))) limit 1;
  if v_id is null then return null; end if;
  update public.docs
     set data = public.jsonb_deep_merge(data, jsonb_build_object('members', jsonb_build_object(auth.uid()::text, (extract(epoch from now())*1000)::bigint))),
         updated_at = now()
   where coll = p_coll and id = v_id;
  return v_id;
end $$;
revoke all on function public.join_league(text,text) from public, anon;
grant execute on function public.join_league(text,text) to authenticated;

-- 2. Only a league's owner, its members, or an admin can change it (football and basketball).
drop policy if exists "update league" on public.docs;
create policy "update league" on public.docs for update to authenticated
  using (coll in ('groups','fgroups','bb_groups','bb_fgroups')
         and ((data->>'ownerId') = auth.uid()::text or (data->'members'->>(auth.uid()::text)) is not null or public.is_admin()))
  with check (coll in ('groups','fgroups','bb_groups','bb_fgroups'));

drop policy if exists "create league" on public.docs;
create policy "create league" on public.docs for insert to authenticated
  with check (coll in ('groups','fgroups','bb_groups','bb_fgroups') and (data->>'ownerId') = auth.uid()::text);

drop policy if exists "delete league" on public.docs;
create policy "delete league" on public.docs for delete to authenticated
  using (coll in ('groups','fgroups','bb_groups','bb_fgroups') and ((data->>'ownerId') = auth.uid()::text or public.is_admin()));

-- 3. Basketball gets the same per-user rules as football (it uses bb_-prefixed collections; profiles are shared).
drop policy if exists "write own docs" on public.docs;
create policy "write own docs" on public.docs for all to public
  using (((coll in ('profiles','games','lineups','queue','picks','bb_games','bb_lineups','bb_queue','bb_picks')) and id = auth.uid()::text)
         or coll = 'data/users/' || auth.uid()::text or coll = 'bb_data/users/' || auth.uid()::text or public.is_admin())
  with check (((coll in ('profiles','games','lineups','queue','picks','bb_games','bb_lineups','bb_queue','bb_picks')) and id = auth.uid()::text)
         or coll = 'data/users/' || auth.uid()::text or coll = 'bb_data/users/' || auth.uid()::text or public.is_admin());

drop policy if exists "read app data" on public.docs;
create policy "read app data" on public.docs for select to public
  using (coll in ('profiles','games','verified','lineups','groups','fgroups','queue','picks',
                  'bb_games','bb_verified','bb_lineups','bb_groups','bb_fgroups','bb_queue','bb_picks')
         or coll = 'data/users/' || auth.uid()::text or coll = 'bb_data/users/' || auth.uid()::text);

-- 4. Delete my account: removes the user's own data, hands leagues they own to another member (or removes empty ones),
--    takes them out of every league, then deletes the login.
create or replace function public.delete_my_account()
returns void language plpgsql security definer set search_path to 'public', 'auth' as $$
declare u text := auth.uid()::text; r record; heir text;
begin
  if auth.uid() is null then raise exception 'sign in first' using errcode = '42501'; end if;
  for r in select coll, id, data from public.docs where coll in ('groups','fgroups','bb_groups','bb_fgroups') and data->>'ownerId' = u loop
    select k into heir from jsonb_each(coalesce(r.data->'members','{}'::jsonb)) as m(k, v)
      where k <> u and jsonb_typeof(v) <> 'null' order by v::text limit 1;
    if heir is null then
      delete from public.docs where coll = r.coll and id = r.id;
    else
      update public.docs set data = jsonb_set(data, '{ownerId}', to_jsonb(heir)), updated_at = now() where coll = r.coll and id = r.id;
    end if;
  end loop;
  update public.docs set data = data #- array['members', u], updated_at = now()
   where coll in ('groups','fgroups','bb_groups','bb_fgroups') and data->'members' ? u;
  delete from public.docs
   where (coll in ('profiles','games','lineups','queue','picks','verified','bb_games','bb_lineups','bb_queue','bb_picks','bb_verified') and id = u)
      or coll = 'data/users/' || u or coll = 'bb_data/users/' || u;
  delete from auth.users where id = auth.uid();
end $$;
revoke all on function public.delete_my_account() from public, anon;
grant execute on function public.delete_my_account() to authenticated;
