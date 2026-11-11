-- Varsity Transfer Portal (v419): token-only card auctions. Safe to run more than once.
-- Cards and tokens live in docs picks/<uid> (bb_picks for basketball): inv.cards[id][ver] = 1|0, inv.tp = net tokens from the Portal
-- (escrowed bids are taken out of inv.tp, refunds and sale money are added back). The app adds inv.tp into the token balance.
create table if not exists public.tp_listings(
  id uuid primary key default gen_random_uuid(),
  pre text not null default '',            -- '' football, 'bb_' basketball
  seller text not null,
  card text not null, ver text not null,
  start_bid int not null, buy_now int,
  bid int, bidder text,
  ends_at timestamptz not null,
  status text not null default 'open',     -- open | sold | expired | cancelled
  created_at timestamptz not null default now(),
  done_at timestamptz);
create index if not exists tp_listings_open on public.tp_listings(pre,status,ends_at);
alter table public.tp_listings enable row level security;
drop policy if exists tp_read on public.tp_listings;
create policy tp_read on public.tp_listings for select to authenticated using (true);

create or replace function public.tp_has(p_pre text,p_uid text,p_card text,p_ver text) returns boolean
language plpgsql security definer set search_path=public as $$
declare cur jsonb;
begin
  select data#>array['inv','cards',p_card] into cur from docs where coll=p_pre||'picks' and id=p_uid;
  if cur is null then return false; end if;
  if jsonb_typeof(cur)='string' then return (cur#>>'{}')=p_ver; end if;
  return coalesce((cur->>p_ver) ~ '^[1-9]','f');
end $$;

create or replace function public.tp_card_set(p_pre text,p_uid text,p_card text,p_ver text,p_on int) returns void
language plpgsql security definer set search_path=public as $$
declare cur jsonb;
begin
  select data#>array['inv','cards',p_card] into cur from docs where coll=p_pre||'picks' and id=p_uid;
  if cur is null or jsonb_typeof(cur)='null' then cur:='{}'::jsonb;
  elsif jsonb_typeof(cur)='string' then cur:=jsonb_build_object(cur#>>'{}',1); end if;
  cur:=cur||jsonb_build_object(p_ver,p_on);
  update docs set data=public.jsonb_deep_merge(data,jsonb_build_object('inv',jsonb_build_object('cards',jsonb_build_object(p_card,cur)))),updated_at=now()
   where coll=p_pre||'picks' and id=p_uid;
end $$;

create or replace function public.tp_tok(p_pre text,p_uid text,p_amt int) returns void
language plpgsql security definer set search_path=public as $$
declare t numeric;
begin
  if p_amt=0 or p_uid is null then return; end if;
  select coalesce((data#>>'{inv,tp}')::numeric,0) into t from docs where coll=p_pre||'picks' and id=p_uid;
  update docs set data=public.jsonb_deep_merge(data,jsonb_build_object('inv',jsonb_build_object('tp',coalesce(t,0)+p_amt))),updated_at=now()
   where coll=p_pre||'picks' and id=p_uid;
end $$;

create or replace function public.tp_finish(p_id uuid) returns void
language plpgsql security definer set search_path=public as $$
declare l tp_listings;
begin
  select * into l from tp_listings where id=p_id and status='open' for update;
  if not found then return; end if;
  if l.bidder is not null and not tp_has(l.pre,l.bidder,l.card,l.ver) then
    perform tp_card_set(l.pre,l.bidder,l.card,l.ver,1);
    perform tp_tok(l.pre,l.seller,l.bid-floor(l.bid*0.05)::int);
    update tp_listings set status='sold',done_at=now() where id=l.id;
  else
    if l.bidder is not null then perform tp_tok(l.pre,l.bidder,l.bid); end if;   -- bidder got the card elsewhere: refund
    perform tp_card_set(l.pre,l.seller,l.card,l.ver,1);
    update tp_listings set status='expired',done_at=now() where id=l.id;
  end if;
end $$;

create or replace function public.tp_settle() returns void
language plpgsql security definer set search_path=public as $$
declare r record;
begin
  for r in select id from tp_listings where status='open' and ends_at<=now() limit 200 loop perform tp_finish(r.id); end loop;
  delete from tp_listings where status<>'open' and done_at<now()-interval '7 days';
end $$;

create or replace function public.tp_list(p_pre text,p_card text,p_ver text,p_start int,p_buy int,p_hours int) returns uuid
language plpgsql security definer set search_path=public as $$
declare me text:=auth.uid()::text; nid uuid;
begin
  if me is null or p_pre not in ('','bb_') or p_hours not in (1,6,12,24,48) or p_start<1 or p_start>1000000 then raise exception 'bad listing'; end if;
  if p_buy is not null and p_buy<=p_start then raise exception 'Buy now must be above the starting bid'; end if;
  if (select count(*) from tp_listings where seller=me and status='open')>=20 then raise exception 'You can have 20 listings at a time'; end if;
  if not tp_has(p_pre,me,p_card,p_ver) then raise exception 'You do not own that card'; end if;
  perform tp_card_set(p_pre,me,p_card,p_ver,0);   -- escrow: out of the seller's locker until it sells or ends
  insert into tp_listings(pre,seller,card,ver,start_bid,buy_now,ends_at) values(p_pre,me,p_card,p_ver,p_start,p_buy,now()+make_interval(hours=>p_hours)) returning id into nid;
  return nid;
end $$;

create or replace function public.tp_bid(p_id uuid,p_amt int,p_bal int) returns text
language plpgsql security definer set search_path=public as $$
declare me text:=auth.uid()::text; l tp_listings; need int; own int:=0;
begin
  perform tp_settle();
  select * into l from tp_listings where id=p_id for update;
  if me is null or not found or l.status<>'open' or l.ends_at<=now() then raise exception 'This auction has ended'; end if;
  if l.seller=me then raise exception 'You can not bid on your own card'; end if;
  if tp_has(l.pre,me,l.card,l.ver) then raise exception 'You already own this card'; end if;
  need:=case when l.bid is null then l.start_bid else l.bid+greatest(1,ceil(l.bid*0.05)::int) end;
  if p_amt<need then raise exception 'Bid at least % tokens',need; end if;
  if l.bidder=me then own:=l.bid; end if;
  if p_bal+own<p_amt then raise exception 'Not enough tokens'; end if;
  if l.bidder is not null and l.bidder<>me then perform tp_tok(l.pre,l.bidder,l.bid); end if;
  perform tp_tok(l.pre,me,-(p_amt-own));
  update tp_listings set bid=p_amt,bidder=me,ends_at=case when ends_at-now()<interval '2 minutes' then now()+interval '2 minutes' else ends_at end where id=l.id;
  return 'ok';
end $$;

create or replace function public.tp_buy(p_id uuid,p_bal int) returns text
language plpgsql security definer set search_path=public as $$
declare me text:=auth.uid()::text; l tp_listings; own int:=0;
begin
  perform tp_settle();
  select * into l from tp_listings where id=p_id for update;
  if me is null or not found or l.status<>'open' or l.ends_at<=now() then raise exception 'This auction has ended'; end if;
  if l.buy_now is null then raise exception 'No buy-now price'; end if;
  if l.seller=me then raise exception 'You can not buy your own card'; end if;
  if tp_has(l.pre,me,l.card,l.ver) then raise exception 'You already own this card'; end if;
  if l.bid is not null and l.bid>=l.buy_now then raise exception 'The bid is already at the buy-now price'; end if;
  if l.bidder=me then own:=l.bid; end if;
  if p_bal+own<l.buy_now then raise exception 'Not enough tokens'; end if;
  if l.bidder is not null and l.bidder<>me then perform tp_tok(l.pre,l.bidder,l.bid); end if;
  perform tp_tok(l.pre,me,-(l.buy_now-own));
  update tp_listings set bid=l.buy_now,bidder=me where id=l.id;
  perform tp_finish(l.id);
  return 'ok';
end $$;

create or replace function public.tp_cancel(p_id uuid) returns text
language plpgsql security definer set search_path=public as $$
declare me text:=auth.uid()::text; l tp_listings;
begin
  select * into l from tp_listings where id=p_id and seller=me and status='open' for update;
  if not found then raise exception 'Not found'; end if;
  if l.bid is not null then raise exception 'It already has a bid'; end if;
  perform tp_card_set(l.pre,me,l.card,l.ver,1);
  update tp_listings set status='cancelled',done_at=now() where id=l.id;
  return 'ok';
end $$;

revoke all on function public.tp_has(text,text,text,text),public.tp_card_set(text,text,text,text,int),public.tp_tok(text,text,int),public.tp_finish(uuid) from public,anon,authenticated;
grant execute on function public.tp_settle(),public.tp_list(text,text,text,int,int,int),public.tp_bid(uuid,int,int),public.tp_buy(uuid,int),public.tp_cancel(uuid) to authenticated;
