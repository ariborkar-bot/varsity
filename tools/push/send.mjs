/* Varsity push sender. Run every 5 minutes by .github/workflows/push.yml (or by hand: node send.mjs).
   Reads the phones that turned on notifications (public.push_subs), works out what is due (plan.mjs), sends it with Web Push and
   remembers what it sent (public.push_sent) so nobody gets the same alert twice.
   Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (service_role key), VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY. DRY=1 prints instead of sending. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
/* SB_FAKE / WP_FAKE: test.send.mjs swaps in an in-memory database and a recording sender */
const { createClient } = await import(process.env.SB_FAKE || '@supabase/supabase-js');
const webpush = (await import(process.env.WP_FAKE || 'web-push')).default;
import { plan, parseBbGames, parseFbGames } from './plan.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..', '..');
const { SUPABASE_URL, SUPABASE_SERVICE_KEY, VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, DRY } = process.env;
if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY || !VAPID_PUBLIC_KEY || !VAPID_PRIVATE_KEY) { console.error('Missing SUPABASE_URL, SUPABASE_SERVICE_KEY, VAPID_PUBLIC_KEY or VAPID_PRIVATE_KEY'); process.exit(1); }
webpush.setVapidDetails('https://ariborkar-bot.github.io/varsity/', VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY);
const sb = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY, { auth: { persistSession: false } });
const must = r => { if (r.error) throw new Error(r.error.message); return r.data; };
/* the server returns at most 1000 rows per request: read page by page. mk() builds a fresh query each time (ordered, so pages don't overlap) */
async function all(mk) { const out = []; for (let i = 0; ; i += 1000) { const rows = must(await mk().range(i, i + 999)); out.push(...rows); if (rows.length < 1000) return out; } }

const now = Date.now();
const state = (must(await sb.from('push_state').select('last_run').eq('id', 1).maybeSingle()) || {}).last_run;
const since = state ? Math.min(now, Date.parse(state)) - 2 * 6e4 : now - 10 * 6e4;     // chat: 2 minutes of overlap, duplicates are filtered by push_sent

const subs = await all(() => sb.from('push_subs').select('*').order('endpoint'));
const games = {
  fb: parseFbGames(fs.readFileSync(path.join(root, 'games.js'), 'utf8')),
  bb: parseBbGames(fs.readFileSync(path.join(root, 'tools', 'data', 'bb_2627_games.txt'), 'utf8')),
};

/* hands: only needed for the "picks lock" reminder */
const picks = {};
for (const sport of ['fb', 'bb']) {
  const ids = [...new Set(subs.filter(s => s.sport === sport && (s.cats || {}).lock !== false).map(s => s.uid))];
  for (let i = 0; i < ids.length; i += 200) {
    const rows = must(await sb.from('docs').select('id,data').eq('coll', sport === 'bb' ? 'bb_picks' : 'picks').in('id', ids.slice(i, i + 200)));
    rows.forEach(r => (picks[sport + '|' + r.id] = { fc: (r.data || {}).fc || {} }));
  }
}

/* leagues with chat messages since the last run */
const groups = [];
const names = {};
for (const sport of ['fb', 'bb']) {
  const iso = new Date(since - 60 * 6e4).toISOString();
  const rows = await all(() => sb.from('docs').select('id,data,updated_at').eq('coll', sport === 'bb' ? 'bb_groups' : 'groups').gte('updated_at', iso).order('id'));
  rows.forEach(r => groups.push({ sport, id: r.id, data: r.data }));
}
const senders = [...new Set(groups.flatMap(g => Object.values((g.data && g.data.chat) || {}).filter(m => m && m.at > since).map(m => m.u)))];
for (let i = 0; i < senders.length; i += 200) must(await sb.from('docs').select('id,data').eq('coll', 'profiles').in('id', senders.slice(i, i + 200))).forEach(r => (names[r.id] = (r.data || {}).name || ''));

/* what was already sent (last 3 days is plenty: every alert's window is shorter) */
const sentRows = await all(() => sb.from('push_sent').select('endpoint,key').gte('at', new Date(now - 3 * 864e5).toISOString()).order('endpoint').order('key'));
const sent = new Set(sentRows.map(r => r.endpoint + '|' + r.key));

const due = plan({ now, subs, games, picks, groups, names, sent, since });
console.log(`${subs.length} phones, ${due.length} alerts due${DRY ? ' (dry run)' : ''}`);

const done = [], gone = [];
for (const n of due) {
  const body = JSON.stringify({ title: n.title, body: n.body, tag: n.tag, url: n.url });
  if (DRY) { console.log(`  → ${n.sub.school || '-'} (${n.sub.sport}) [${n.cat}] ${n.title}: ${n.body}`); continue; }
  try {
    await webpush.sendNotification({ endpoint: n.sub.endpoint, keys: { p256dh: n.sub.p256dh, auth: n.sub.auth } }, body, { TTL: 3 * 3600, urgency: 'normal' });
    done.push({ endpoint: n.sub.endpoint, key: n.key });
    (n.also || []).forEach(k => done.push({ endpoint: n.sub.endpoint, key: k }));
  } catch (e) {
    if (e.statusCode === 404 || e.statusCode === 410) gone.push(n.sub.endpoint);          // the phone turned notifications off or removed the app
    else console.error('send failed', e.statusCode || '', String(e.body || e.message).slice(0, 120));
  }
}
if (!DRY) {
  if (done.length) must(await sb.from('push_sent').upsert(done, { onConflict: 'endpoint,key', ignoreDuplicates: true }));
  const deadEps = [...new Set(gone)];
  for (const ep of deadEps) must(await sb.from('push_subs').delete().eq('endpoint', ep));
  must(await sb.from('push_sent').delete().lt('at', new Date(now - 10 * 864e5).toISOString()));
  must(await sb.from('push_state').upsert({ id: 1, last_run: new Date(now).toISOString(), sent: done.length }));
}
console.log(`sent ${done.length}, removed ${new Set(gone).size} dead phones`);
