-- Run once in the Supabase SQL editor (project "varsity") to turn on multiplayer mock drafts.
-- Solo mock drafts against AI work without it.
create policy "read mocks" on public.docs for select to public using (coll = 'mocks');
create policy "create mock" on public.docs for insert to authenticated with check (coll = 'mocks' and (data ->> 'ownerId') = (auth.uid())::text);
create policy "update mock" on public.docs for update to authenticated using (coll = 'mocks') with check (coll = 'mocks');
create policy "delete mock" on public.docs for delete to authenticated using (coll = 'mocks' and ((data ->> 'ownerId') = (auth.uid())::text or is_admin()));
