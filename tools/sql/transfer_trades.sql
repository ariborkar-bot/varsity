-- Varsity Transfer Portal: card-for-card trades (v437). Run once in the Supabase SQL editor, after transfer_portal.sql. Safe to run more than once.
-- A proposer's card is held (escrow) while the offer is pending, like an auction listing. The other player accepts or declines,
-- the proposer can cancel, and an offer nobody answers for 7 days ends and the card goes back.
create table if not exists public.tp_trades(
  id uuid primary key default gen_random_uuid(),
  pre text not null default '',            -- '' football, 'bb_' basketball
  from_uid text not null, to_uid text not null,
  give_card text not null, give_ver text not null,   -- what the proposer gives (held while pending)
  want_card text not null, want_ver text not null,   -- what the proposer asks for
  status text not null default 'pending',  -- pending | accepted | declined | cancelled | expired
  created_at timestamptz not null default now(),
  done_at timestamptz);
create index if not exists tp_trades_to on public.tp_trades(pre,to_uid,status);
create index if not exists tp_trades_from on public.tp_trades(pre,from_uid,status);
alter table public.tp_trades enable row level security;
drop policy if exists tr_read on public.tp_trades;
create policy tr_read on public.tp_trades for select to authenticated using (from_uid=auth.uid()::text or to_uid=auth.uid()::text);

create or replace function public.tp_trade_offer(p_pre text,p_to text,p_give text,p_gv text,p_want text,p_wv text) returns uuid
language plpgsql security definer set search_path=public as $$
declare me text:=auth.uid()::text; nid uuid;
begin
  if me is null or p_pre not in ('','bb_') or p_to is null or p_to=me then raise exception 'bad trade'; end if;
  if (select count(*) from tp_trades where from_uid=me and status='pending')>=10 then raise exception 'You can have 10 open offers at a time'; end if;
  if not tp_has(p_pre,me,p_give,p_gv) then raise exception 'You do not own the card you are offering'; end if;
  if not tp_has(p_pre,p_to,p_want,p_wv) then raise exception 'They no longer own that card'; end if;
  if tp_has(p_pre,p_to,p_give,p_gv) then raise exception 'They already own the card you are offering'; end if;
  if tp_has(p_pre,me,p_want,p_wv) then raise exception 'You already own the card you are asking for'; end if;
  perform tp_card_set(p_pre,me,p_give,p_gv,0);   -- escrow
  insert into tp_trades(pre,from_uid,to_uid,give_card,give_ver,want_card,want_ver) values(p_pre,me,p_to,p_give,p_gv,p_want,p_wv) returning id into nid;
  return nid;
end $$;

create or replace function public.tp_trade_accept(p_id uuid) returns text
language plpgsql security definer set search_path=public as $$
declare me text:=auth.uid()::text; t tp_trades;
begin
  select * into t from tp_trades where id=p_id and to_uid=me and status='pending' for update;
  if not found then raise exception 'This offer is no longer open'; end if;
  if not tp_has(t.pre,me,t.want_card,t.want_ver) then raise exception 'You no longer own the card they asked for'; end if;
  if tp_has(t.pre,me,t.give_card,t.give_ver) then raise exception 'You already own the card they are offering'; end if;
  if tp_has(t.pre,t.from_uid,t.want_card,t.want_ver) then raise exception 'They already got that card another way'; end if;
  perform tp_card_set(t.pre,me,t.want_card,t.want_ver,0);
  perform tp_card_set(t.pre,me,t.give_card,t.give_ver,1);
  perform tp_card_set(t.pre,t.from_uid,t.want_card,t.want_ver,1);
  update tp_trades set status='accepted',done_at=now() where id=t.id;
  return 'ok';
end $$;

create or replace function public.tp_trade_close(p_id uuid,p_status text) returns void
language plpgsql security definer set search_path=public as $$
declare t tp_trades;
begin
  select * into t from tp_trades where id=p_id and status='pending' for update;
  if not found then return; end if;
  perform tp_card_set(t.pre,t.from_uid,t.give_card,t.give_ver,1);   -- the held card goes back to the proposer
  update tp_trades set status=p_status,done_at=now() where id=t.id;
end $$;

create or replace function public.tp_trade_decline(p_id uuid) returns text
language plpgsql security definer set search_path=public as $$
begin
  if not exists(select 1 from tp_trades where id=p_id and to_uid=auth.uid()::text and status='pending') then raise exception 'This offer is no longer open'; end if;
  perform tp_trade_close(p_id,'declined'); return 'ok';
end $$;

create or replace function public.tp_trade_cancel(p_id uuid) returns text
language plpgsql security definer set search_path=public as $$
begin
  if not exists(select 1 from tp_trades where id=p_id and from_uid=auth.uid()::text and status='pending') then raise exception 'This offer is no longer open'; end if;
  perform tp_trade_close(p_id,'cancelled'); return 'ok';
end $$;

create or replace function public.tp_trade_settle() returns void
language plpgsql security definer set search_path=public as $$
declare r record;
begin
  for r in select id from tp_trades where status='pending' and created_at<now()-interval '7 days' limit 200 loop perform tp_trade_close(r.id,'expired'); end loop;
  delete from tp_trades where status<>'pending' and done_at<now()-interval '14 days';
end $$;

revoke all on function public.tp_trade_close(uuid,text) from public,anon,authenticated;
grant execute on function public.tp_trade_offer(text,text,text,text,text,text),public.tp_trade_accept(uuid),public.tp_trade_decline(uuid),public.tp_trade_cancel(uuid),public.tp_trade_settle() to authenticated;
