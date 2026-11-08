/* node test.send.mjs : runs send.mjs against the in-memory fakes (no network) */
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import { ptMs, parseBbGames } from './plan.mjs';
process.env.SB_FAKE = new URL('./fakes.mjs', import.meta.url).href; process.env.WP_FAKE = process.env.SB_FAKE;
Object.assign(process.env, { SUPABASE_URL: 'x', SUPABASE_SERVICE_KEY: 'x', VAPID_PUBLIC_KEY: 'x', VAPID_PRIVATE_KEY: 'x' });
const F = await import('./fakes.mjs');
const g0 = parseBbGames(fs.readFileSync(new URL('../data/bb_2627_games.txt', import.meta.url), 'utf8')).find(g => g.d === '2026-11-14' && g.t);
const now = ptMs(g0.d, g0.t) - 50 * 6e4;
F.DB.push_subs.push({ endpoint: 'https://p/a'.padEnd(30, 'x'), uid: 'u1', sport: 'bb', school: g0.h, tz: 'America/Los_Angeles', cats: {}, quiet: {}, p256dh: 'p', auth: 'a' },
  { endpoint: 'https://p/gone'.padEnd(30, 'x') + 'gone', uid: 'u2', sport: 'bb', school: g0.h, tz: 'America/Los_Angeles', cats: {}, quiet: {}, p256dh: 'p', auth: 'a' });
const realNow = Date.now; Date.now = () => now;
await import('./send.mjs');
Date.now = realNow;
const poway = F.SENT.filter(s => s.ep.startsWith('https://p/axxx'));
console.log(F.SENT.map(s => s.title + ': ' + s.body));
assert.ok(poway.some(s => s.title === 'Game day' && new RegExp(g0.h + ' plays').test(s.body)), 'game day alert sent');
assert.equal(F.DB.push_subs.length, 1, 'dead phone (410) removed');
assert.ok(F.DB.push_sent.some(r => r.key.startsWith('gs|')), 'marked as sent');
assert.ok(F.DB.push_state[0].last_run, 'last_run saved');
console.log('send.mjs against fakes: ok');
