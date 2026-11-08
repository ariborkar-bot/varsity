/* node test.mjs : checks the notification planner with made-up phones and games */
import assert from 'node:assert/strict';
import { plan, ptMs, parts, parseBbGames } from './plan.mjs';
const sub = (o = {}) => Object.assign({ endpoint: 'https://push.example/' + Math.random().toString(36).slice(2) + 'xxxxxxxxxxxxxxxxxxxx', uid: 'u1', sport: 'bb', school: 'Poway', tz: 'America/Los_Angeles', cats: {}, quiet: {} }, o);
const at = (d, hm) => ptMs(d, hm);
const I = (now, subs, extra = {}) => Object.assign({ now, subs, games: { fb: [], bb: [] }, picks: {}, groups: [], names: {}, sent: new Set(), since: now - 6e5 }, extra);
// ptMs: 2026-11-14 7 PM PT is 03:00 UTC on the 15th (PST = UTC-8)
assert.equal(new Date(ptMs('2026-11-14', '19:00')).toISOString(), '2026-11-15T03:00:00.000Z');
assert.equal(new Date(ptMs('2027-03-20', '19:00')).toISOString(), '2027-03-21T02:00:00.000Z');   // daylight time: UTC-7
const bb = [{ d: '2026-11-14', t: '19:00', h: 'Poway', a: 'Ramona', hs: null, as: null }, { d: '2026-11-14', t: '18:00', h: 'Mira Mesa', a: 'Vista', hs: null, as: null }];
// game start: 55 minutes before tip yes, 2 hours before no, already sent no
let s = sub(), r = plan(I(at('2026-11-14', '18:05'), [s], { games: { fb: [], bb } }));
assert.ok(r.some(x => x.cat === 'gstart' && /Poway plays Ramona tonight at 7 PM/.test(x.body)), JSON.stringify(r));
assert.equal(plan(I(at('2026-11-14', '16:30'), [s], { games: { fb: [], bb } })).filter(x => x.cat === 'gstart').length, 0);
const first = plan(I(at('2026-11-14', '18:05'), [s], { games: { fb: [], bb } })).find(x => x.cat === 'gstart');
assert.equal(plan(I(at('2026-11-14', '18:10'), [s], { games: { fb: [], bb }, sent: new Set([s.endpoint + '|' + first.key]) })).filter(x => x.cat === 'gstart').length, 0);
// category off, quiet hours
assert.equal(plan(I(at('2026-11-14', '18:05'), [sub({ cats: { gstart: false, lock: false } })], { games: { fb: [], bb } })).length, 0);
assert.equal(plan(I(at('2026-11-14', '21:30'), [sub({ school: 'Vista' })], { games: { fb: [], bb: [{ ...bb[0], hs: 60, as: 50, h: 'Vista' }] } })).length, 0, 'quiet hours hold the result');
assert.equal(plan(I(at('2026-11-15', '08:05'), [sub({ school: 'Vista' })], { games: { fb: [], bb: [{ ...bb[0], hs: 60, as: 50, h: 'Vista' }] } })).filter(x => x.cat === 'results').length, 1, 'result arrives when quiet hours end');
// results text
r = plan(I(at('2026-11-15', '09:00'), [sub()], { games: { fb: [], bb: [{ ...bb[0], hs: 64, as: 58 }] } }));
assert.ok(r.find(x => x.cat === 'results' && x.body === 'Win: Poway 64, Ramona 58'), JSON.stringify(r));
r = plan(I(at('2026-11-15', '09:00'), [sub({ school: 'Ramona' })], { games: { fb: [], bb: [{ ...bb[0], hs: 64, as: 58 }] } }));
assert.ok(r.find(x => x.body === 'Loss: Poway 64, Ramona 58'));
// 5 Card Draw reminder: 90 minutes before the first tip (6 PM game -> 4:30 PM), skipped when a hand exists
r = plan(I(at('2026-11-14', '16:40'), [sub({ school: 'Nobody' })], { games: { fb: [], bb } }));
assert.ok(r.find(x => x.cat === 'lock' && /closes at the first tip-off, 6 PM/.test(x.body)), JSON.stringify(r));
const slot = Math.round((Date.parse('2026-11-14') - Date.UTC(2026, 10, 1)) / 864e5);
assert.equal(plan(I(at('2026-11-14', '16:40'), [sub({ school: 'Nobody' })], { games: { fb: [], bb }, picks: { 'bb|u1': { fc: { [slot]: { h: [] } } } } })).filter(x => x.cat === 'lock').length, 0);
assert.equal(plan(I(at('2026-11-14', '18:30'), [sub({ school: 'Nobody' })], { games: { fb: [], bb } })).filter(x => x.cat === 'lock').length, 0, 'closed at tip-off');
// Sunday recap at 5 PM PT only
assert.equal(plan(I(at('2026-11-15', '17:10'), [sub({ school: '' })])).filter(x => x.cat === 'recap').length, 1);
assert.equal(plan(I(at('2026-11-15', '15:10'), [sub({ school: '' })])).filter(x => x.cat === 'recap').length, 0);
assert.equal(plan(I(at('2026-11-14', '17:10'), [sub({ school: '' })])).filter(x => x.cat === 'recap').length, 0);
// chat: members except the sender, only new messages, only phones in the same sport
const now = at('2026-11-14', '12:00');
const g = { sport: 'bb', id: 'g1', data: { name: 'Hoop Dreams', members: { u1: 1, u2: 1 }, chat: { m1: { u: 'u2', t: 'who’s starting Cano?', at: now - 1000 }, m0: { u: 'u2', t: 'old', at: now - 9e6 }, m2: { u: 'u1', t: 'mine', at: now - 500 } } } };
r = plan(I(now, [sub({ school: '' }), sub({ uid: 'u2', school: '' }), sub({ uid: 'u1', sport: 'fb', school: '' })], { groups: [g], names: { u2: 'Sam' } }));
assert.equal(r.filter(x => x.cat === 'chat').length, 2);   // u1 gets Sam's message, u2 gets u1's; the football phone and the old message get nothing
assert.ok(r.find(x => x.sub.uid === 'u1' && x.body === 'Sam: who’s starting Cano?'));
assert.ok(r.find(x => x.sub.uid === 'u2' && x.body.endsWith('mine')));
// at most 3 per phone, the rest folded
const many = { sport: 'bb', id: 'g2', data: { name: 'L', members: { u1: 1, u3: 1 }, chat: Object.fromEntries([1, 2, 3, 4, 5].map(i => ['k' + i, { u: 'u3', t: 'hi ' + i, at: now - 100 * i }])) } };
r = plan(I(now, [sub({ school: '' })], { groups: [many], names: { u3: 'Al' } }));
assert.equal(r.length, 3); assert.match(r[2].body, /\(\+2 more\)/); assert.equal(r[2].also.length, 2);
// schedule parser
const t = 'NAMES:Poway|Ramona\n1114 1900 0 1\n1114 0000 ~Outside 0 64-58\n0103 1830 1 0\n';
const gs = parseBbGames(t);
assert.equal(gs.length, 3); assert.equal(gs[0].t, '19:00'); assert.equal(gs[1].h, 'Outside'); assert.equal(gs[1].hs, 64); assert.equal(gs[2].d, '2027-01-03');
console.log('push planner: all checks passed');
