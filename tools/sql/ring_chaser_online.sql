-- Run once in the Supabase SQL editor (project "varsity") to turn on online Ring Chaser
-- (Find an opponent / party codes). Playing the AI works without it.
-- Live 1v1 matches are docs in collections 'rcm' (football) and 'bb_rcm' (basketball).
create policy "read rc match" on public.docs for select to authenticated
  using (coll in ('rcm','bb_rcm'));
create policy "create rc match" on public.docs for insert to authenticated
  with check (coll in ('rcm','bb_rcm') and (data->>'host') = auth.uid()::text and (data->>'st') = 'wait' and (data->>'guest') is null);
create policy "update rc match" on public.docs for update to authenticated
  using (coll in ('rcm','bb_rcm') and ((data->>'host') = auth.uid()::text or (data->>'guest') = auth.uid()::text))
  with check (coll in ('rcm','bb_rcm') and ((data->>'host') = auth.uid()::text or (data->>'guest') = auth.uid()::text));
create policy "delete rc match" on public.docs for delete to authenticated
  using (coll in ('rcm','bb_rcm') and ((data->>'host') = auth.uid()::text or (data->>'guest') = auth.uid()::text or is_admin()));

-- Join a match: by party code, or (no code) the oldest open public match.
-- p_mine = your own waiting public match while you search: if someone already joined it, it is returned;
-- otherwise you only join matches opened before yours (so two searchers never grab each other), and yours is closed.
-- Also clears matches untouched for 2 days.
create or replace function public.rc_claim(p_coll text, p_code text default null, p_mine text default null)
returns text language plpgsql security definer set search_path = public as $$
declare
  me text := auth.uid()::text;
  nowms bigint := (extract(epoch from now()) * 1000)::bigint;
  mine jsonb; mc bigint; tid text;
begin
  if me is null or p_coll not in ('rcm','bb_rcm') then return null; end if;
  delete from docs where coll = p_coll and updated_at < now() - interval '2 days';
  if p_mine is not null then
    select data into mine from docs where coll = p_coll and id = p_mine and data->>'host' = me for update;
    if mine is null then return null; end if;
    if mine->>'st' <> 'wait' then return p_mine; end if;
    mc := case when mine->>'c' ~ '^\d{1,15}$' then (mine->>'c')::bigint else 0 end;
  end if;
  if p_code is not null then
    select id into tid from docs
     where coll = p_coll and data->>'st' = 'wait' and data->>'code' = upper(trim(p_code)) and data->>'host' <> me
       and data->>'hb' ~ '^\d{1,15}$' and (data->>'hb')::bigint > nowms - 120000
     limit 1 for update skip locked;
  else
    select id into tid from docs
     where coll = p_coll and data->>'st' = 'wait' and data->>'pub' = 'true' and data->>'host' <> me
       and data->>'hb' ~ '^\d{1,15}$' and (data->>'hb')::bigint > nowms - 30000
       and data->>'c' ~ '^\d{1,15}$' and (mc is null or (data->>'c')::bigint < mc)
     order by (data->>'c')::bigint limit 1 for update skip locked;
  end if;
  if tid is null then return null; end if;
  update docs set data = data || jsonb_build_object('guest', me, 'st', 'live', 'at', nowms), updated_at = now()
   where coll = p_coll and id = tid;
  if p_mine is not null then
    update docs set data = data || jsonb_build_object('st', 'gone'), updated_at = now() where coll = p_coll and id = p_mine;
  end if;
  return tid;
end $$;
revoke all on function public.rc_claim(text, text, text) from public, anon;
grant execute on function public.rc_claim(text, text, text) to authenticated;
