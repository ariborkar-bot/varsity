/* Varsity push: decides which phone notifications are due. Pure functions (no network), so test.mjs can check them.
   Categories match the app's PUSH_CATS: gstart, lock, results, chat, recap. All game times are Pacific. */
export const KICK = '19:00';
const PT = 'America/Los_Angeles';

/* wall-clock parts of an instant in a time zone */
export function parts(ms, tz) {
  const o = {};
  new Intl.DateTimeFormat('en-CA', { timeZone: tz || PT, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', weekday: 'short', hourCycle: 'h23' })
    .formatToParts(new Date(ms)).forEach(x => (o[x.type] = x.value));
  return { date: `${o.year}-${o.month}-${o.day}`, hour: +o.hour, min: +o.minute, dow: o.weekday };
}
/* the instant of a Pacific wall-clock time 'YYYY-MM-DD' + 'HH:MM' */
export function ptMs(date, hm) {
  const guess = Date.parse(`${date}T${hm}:00Z`);
  let ms = guess + 8 * 36e5;
  for (let i = 0; i < 2; i++) { const p = parts(ms, PT); const got = Date.parse(`${p.date}T${String(p.hour).padStart(2, '0')}:${String(p.min).padStart(2, '0')}:00Z`); ms += guess - got; }
  return ms;
}
export const dayNo = d => Math.round((Date.parse(d + 'T00:00:00Z') - Date.UTC(2026, 10, 1)) / 864e5);

/* basketball schedule file: 'NAMES:a|b|c' then 'MMDD HHMM home away [64-58]' (see tools/make_basketball.py load_games) */
export function parseBbGames(txt) {
  const lines = txt.split('\n');
  const names = lines[0].slice(6).split('|');
  const nm = t => (t.startsWith('~') ? t.slice(1) : names[+t]);
  const out = [];
  for (const raw of lines.slice(1)) {
    let ln = raw.trim(); if (!ln) continue;
    let hs = null, as = null;
    const sc = ln.match(/ (\d{1,3})-(\d{1,3})$/);
    if (sc) { hs = +sc[1]; as = +sc[2]; ln = ln.slice(0, sc.index); }
    const [md, hm, rest] = [ln.slice(0, 4), ln.slice(5, 9), ln.slice(10)];
    let h, a;
    if (rest.startsWith('~')) { const i = rest.lastIndexOf(' '); h = rest.slice(0, i); a = rest.slice(i + 1); } else { const i = rest.indexOf(' '); h = rest.slice(0, i); a = rest.slice(i + 1); }
    h = nm(h); a = nm(a); if (h === a) continue;
    const mo = +md.slice(0, 2), dy = +md.slice(2);
    out.push({ d: `${mo >= 7 ? 2026 : 2027}-${String(mo).padStart(2, '0')}-${String(dy).padStart(2, '0')}`, t: hm === '0000' ? '' : hm.slice(0, 2) + ':' + hm.slice(2), h, a, hs, as });
  }
  return out;
}
export function parseFbGames(js) {
  const m = js.match(/window\.VARSITY_GAMES\s*=\s*(\{[\s\S]*\})\s*;?\s*$/m);
  return m ? JSON.parse(m[1]).games : [];
}

const fmtT = hm => { const [h, m] = hm.split(':').map(Number); return `${h % 12 || 12}${m ? ':' + String(m).padStart(2, '0') : ''} ${h < 12 ? 'AM' : 'PM'}`; };
const isGame = (g, sc) => g.h === sc || g.a === sc;
const inQuiet = (sub, ms) => {
  const q = sub.quiet || {}; if (q.on === false) return false;
  const from = q.from == null ? 21 : +q.from, to = q.to == null ? 8 : +q.to; if (from === to) return false;
  const h = parts(ms, sub.tz).hour; return from > to ? (h >= from || h < to) : (h >= from && h < to);
};
const catOn = (sub, c) => (sub.cats || {})[c] !== false;

/* input: { now, subs, games:{fb,bb}, picks:{ 'fb|uid' | 'bb|uid': doc }, groups:[{sport,id,data}], names:{uid:name}, sent:Set('endpoint|key'), since }
   output: [{ sub, key, title, body, tag, url }] */
export function plan(I) {
  const out = [], now = I.now, today = parts(now, PT).date;
  const add = (sub, key, cat, title, body, url) => { if (!I.sent.has(sub.endpoint + '|' + key)) out.push({ sub, key, cat, title, body, tag: 'vs-' + key, url }); };
  const home = s => (s === 'bb' ? 'basketball.html' : '');
  for (const sub of I.subs) {
    if (inQuiet(sub, now)) continue;                       // held: nothing is marked sent, so it arrives when quiet hours end
    const games = I.games[sub.sport] || [], sc = sub.school || '', url = home(sub.sport);
    const mine = sc ? games.filter(g => isGame(g, sc)) : [];
    // game start: from an hour before tip-off until 30 minutes after, once per game
    if (catOn(sub, 'gstart')) for (const g of mine) {
      if (g.d !== today || g.hs != null) continue;
      const tip = ptMs(g.d, g.t || KICK);
      if (now >= tip - 60 * 6e4 && now < tip + 30 * 6e4) add(sub, `gs|${g.d}|${g.h}|${g.a}`, 'gstart', 'Game day', `${sc} plays ${g.h === sc ? g.a : g.h} ${g.t ? (g.t < '17:00' ? 'today at ' : 'tonight at ') + fmtT(g.t) : 'today'}.`, url);
    }
    // results: your school's final score, for 36 hours after the game
    if (catOn(sub, 'results')) for (const g of mine) {
      if (g.hs == null) continue;
      const end = ptMs(g.d, g.t || KICK) + 3 * 36e5;
      if (now >= end - 2 * 36e5 && now < end + 36 * 36e5) {
        const w = g.h === sc ? g.hs > g.as : g.as > g.hs, tie = g.hs === g.as, opp = g.h === sc ? g.a : g.h;
        add(sub, `rs|${g.d}|${g.h}|${g.a}`, 'results', 'Final score', `${tie ? 'Tie' : w ? 'Win' : 'Loss'}: ${g.h} ${g.hs}, ${g.a} ${g.as}${tie ? '' : ''}`, url);
      }
    }
    // picks lock: a 5 Card Draw hand not dealt yet on a day your sport has games (basketball: 90 min before the first tip; football: 4 PM)
    if (catOn(sub, 'lock')) {
      const day = games.filter(g => g.d === today);
      if (day.length) {
        const first = Math.min(...day.map(g => ptMs(g.d, g.t || KICK)));
        const at = sub.sport === 'bb' ? first - 90 * 6e4 : ptMs(today, '16:00');
        const slot = sub.sport === 'bb' ? dayNo(today) : (day[0].w || 0);
        const doc = (I.picks[sub.sport + '|' + sub.uid] || {}).fc || {};
        if (now >= at && now < first && !doc[slot])
          add(sub, `lk|${today}`, 'lock', '5 Card Draw', sub.sport === 'bb' ? `Your hand for today isn’t dealt. It closes at the first tip-off, ${fmtT(day.map(g => g.t || KICK).sort()[0])}.` : `Your week ${slot} hand isn’t dealt yet. Deal in before kickoff.`, url);
      }
    }
    // Sunday recap, between 5 and 6 PM
    if (catOn(sub, 'recap')) {
      const p = parts(now, sub.tz);
      if (p.dow === 'Sun' && p.hour === 17) add(sub, `rc|${p.date}`, 'recap', 'Your week in review', 'The Weekly recap is ready. See how your leagues finished.', url);
    }
  }
  // league chat: new messages since the last run, to every member except the sender
  const bySport = {}; for (const s of I.subs) (bySport[s.sport] = bySport[s.sport] || {})[s.uid] = (bySport[s.sport][s.uid] || []).concat(s);
  for (const g of I.groups) {
    const chat = (g.data && g.data.chat) || {}, mem = (g.data && g.data.members) || {};
    for (const [mid, m] of Object.entries(chat)) {
      if (!m || !m.at || m.at <= I.since || m.at > now) continue;
      for (const uid of Object.keys(mem)) {
        if (uid === m.u) continue;
        for (const sub of (bySport[g.sport] || {})[uid] || []) {
          if (!catOn(sub, 'chat') || inQuiet(sub, now)) continue;
          add(sub, `ch|${g.id}|${mid}`, 'chat', g.data.name || 'League chat', `${(I.names[m.u] || 'Someone')}: ${String(m.t || '').slice(0, 120)}`, home(sub.sport) + '#groups');
        }
      }
    }
  }
  // at most 3 per phone per run: the rest fold into "+N more"
  const per = {}; const res = [];
  for (const n of out) {
    const l = (per[n.sub.endpoint] = per[n.sub.endpoint] || []);
    if (l.length < 3) { l.push(n); res.push(n); } else { l.more = (l.more || 0) + 1; l.extra = (l.extra || []).concat(n); }
  }
  for (const l of Object.values(per)) if (l.more) { const last = l[l.length - 1]; last.body += ` (+${l.more} more)`; last.also = l.extra.map(x => x.key); }
  return res;
}
