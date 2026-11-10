-- Run once in the Supabase SQL editor (owner). Admin unlock (PIN) now lasts 30 days instead of 12 hours, so admin pages
-- (announcements, controls, dashboards) keep working without signing in again. Also extends the sessions that exist now.
CREATE OR REPLACE FUNCTION public.admin_unlock(p_username text, p_pin text)
 RETURNS text
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'auth'
AS $function$
declare r text; n text := upper(trim(coalesce(p_username,'')));
begin
  r := public.admin_verify_pin(p_pin);
  if r <> 'ok' then return r; end if;
  if n not in ('ZH_VARSITY_ADMIN','AB_VARSITY_ADMIN') then return 'wrong'; end if;
  delete from public.admin_attempts where uid=auth.uid();
  insert into public.admin_sessions(uid,expires_at,username) values (auth.uid(), now()+interval '30 days', n)
    on conflict (uid) do update set expires_at=excluded.expires_at, username=excluded.username;
  return 'ok';
end $function$;
update public.admin_sessions set expires_at = greatest(expires_at, now()+interval '30 days');
