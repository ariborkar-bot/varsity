/* in-memory stand-ins for supabase-js and web-push, used only by test.send.mjs */
export const DB = { push_subs: [], push_sent: [], push_state: [], docs: [] };
export const SENT = [];
export function createClient() {
  return { from(t) {
    const q = { t, f: [], sel: false, op: null, rows: null, rng: null };
    const run = () => {
      let rows = DB[t].slice();
      for (const f of q.f) rows = rows.filter(f);
      if (q.op === 'delete') { DB[t] = DB[t].filter(r => !q.f.every(f => f(r))); return { data: null, error: null }; }
      if (q.op === 'upsert') {
        for (const r of q.rows) {
          const k = t === 'push_state' ? 'id' : null;
          const ex = DB[t].findIndex(x => k ? x[k] === r[k] : (x.endpoint === r.endpoint && x.key === r.key));
          if (ex >= 0) { if (!q.ign) DB[t][ex] = { ...DB[t][ex], ...r }; } else DB[t].push({ at: new Date().toISOString(), ...r });
        }
        return { data: null, error: null };
      }
      if (q.rng) rows = rows.slice(q.rng[0], q.rng[1] + 1).slice(0, 1000);
      return { data: q.single ? (rows[0] || null) : rows, error: null };
    };
    const b = { select: () => b, order: () => b, limit: () => b, eq: (c, v) => (q.f.push(r => r[c] === v), b), in: (c, v) => (q.f.push(r => v.includes(r[c])), b),
      gte: (c, v) => (q.f.push(r => r[c] >= v), b), lt: (c, v) => (q.f.push(r => r[c] < v), b), range: (a, z) => (q.rng = [a, z], b), maybeSingle: () => (q.single = true, b),
      delete: () => (q.op = 'delete', b), upsert: (rows, o) => (q.op = 'upsert', q.rows = Array.isArray(rows) ? rows : [rows], q.ign = !!(o && o.ignoreDuplicates), b),
      then: (res, rej) => { try { res(run()); } catch (e) { rej(e); } } };
    return b;
  } };
}
export default { setVapidDetails() {}, async sendNotification(sub, body) { if (/gone/.test(sub.endpoint)) { const e = new Error('gone'); e.statusCode = 410; throw e; } SENT.push({ ep: sub.endpoint, ...JSON.parse(body) }); } };
