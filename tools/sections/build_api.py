"""Build the Varsity read-only API: static JSON files under api/v1/, made from data/sections/*.json.

    python3 tools/sections/build_api.py [--data data/sections] [--out api/v1]

No server and no keys: the files are served by GitHub Pages next to the app
(https://ariborkar-bot.github.io/varsity/api/v1/index.json) and Pages sends CORS headers, so any site or app can fetch them.
Layout (sport is fb or bb):
  index.json                                  every section, counts, links
  sections/<id>/<sport>/teams.json            teams with record, league, division
  sections/<id>/<sport>/standings.json        teams grouped by league, best record first
  sections/<id>/<sport>/games.json            every game
  sections/<id>/<sport>/weeks/<monday>.json   one week of games (Monday's date)
  sections/<id>/<sport>/teams/<team id>.json  one team: record and its games ("mp:123" is written as mp-123)
  sections/<id>/<sport>/players.json          top 500 players by fantasy points (from data/players, see players.py); `columns` names each array slot
Everything is rebuilt from scratch on each run, so a removed team or game disappears. Output is deterministic (sorted keys, no timestamps
except the source's own), so an unchanged data set produces no git diff. See docs/API.md."""
import argparse, datetime, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import players as PL  # noqa: E402
TOP = 500   # players per section and sport in players.json
SPORTS = ('fb', 'bb')
VERSION = 1


def monday(d):
    x = datetime.date.fromisoformat(d)
    return (x - datetime.timedelta(days=x.weekday())).isoformat()


def fid(i):
    return str(i).replace(':', '-')


def final(g):
    return g.get('hs') is not None and g.get('as') is not None


def build_sport(sec, sport, out):
    games = [g for g in sec.get('games', []) if g.get('sport') == sport]
    if not games:
        return None
    schools = {s['id']: s for s in sec.get('schools', [])}
    T = {}

    def team(i, name):
        k = i or 'n:' + name
        if k not in T:
            s = schools.get(i) or {}
            T[k] = {'id': k, 'name': s.get('name') or name, 'city': s.get('city') or '', 'league': s.get('league') or '', 'division': s.get('division') or '',
                    'w': 0, 'l': 0, 't': 0, 'pf': 0, 'pa': 0}
        return T[k]
    for g in games:
        h, a = team(g.get('home_id'), g['home']), team(g.get('away_id'), g['away'])
        if not final(g):
            continue
        for x, f, o in ((h, g['hs'], g['as']), (a, g['as'], g['hs'])):
            x['pf'] += f
            x['pa'] += o
            x['w' if f > o else 'l' if f < o else 't'] += 1
    games.sort(key=lambda g: (g.get('date') or '', g.get('time') or '', g['home']))
    base = os.path.join(out, 'sections', sec['section'], sport)

    def put(rel, obj):
        p = os.path.join(base, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(obj, f, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    pub = lambda g: {k: g.get(k) for k in ('id', 'date', 'time', 'home', 'away', 'home_id', 'away_id', 'hs', 'as', 'forfeit', 'state') if g.get(k) is not None}
    teams = sorted(T.values(), key=lambda t: t['name'])
    put('teams.json', {'section': sec['section'], 'sport': sport, 'teams': teams})
    by = {}
    for t in teams:
        if t['w'] + t['l'] + t['t']:
            by.setdefault(t['league'] or t['division'] or 'Other', []).append(t)
    pct = lambda t: t['w'] / ((t['w'] + t['l'] + t['t']) or 1)
    put('standings.json', {'section': sec['section'], 'sport': sport,
                           'leagues': [{'league': k, 'teams': sorted(v, key=lambda t: (-pct(t), -(t['pf'] - t['pa']), t['name']))} for k, v in sorted(by.items())]})
    put('games.json', {'section': sec['section'], 'sport': sport, 'games': [pub(g) for g in games]})
    weeks = {}
    for g in games:
        if g.get('date'):
            weeks.setdefault(monday(g['date']), []).append(pub(g))
    for w, gs in weeks.items():
        put('weeks/%s.json' % w, {'section': sec['section'], 'sport': sport, 'week': w, 'games': gs})
    for k, t in T.items():
        put('teams/%s.json' % fid(k), {'section': sec['section'], 'sport': sport, 'team': t,
                                      'games': [pub(g) for g in games if (g.get('home_id') or 'n:' + g['home']) == k or (g.get('away_id') or 'n:' + g['away']) == k]})
    return {'teams': len(T), 'games': len(games), 'played': sum(1 for g in games if final(g)), 'weeks': len(weeks)}


def build_players(sec_id, sport, src, out):
    """players.json: the TOP players by fantasy points, as arrays [name, school, pos, games, fp, v1, v2 ...] in `keys` order (smaller than objects)."""
    p = os.path.join(src, '%s.%s.json' % (sec_id, sport))
    if not os.path.exists(p):
        return None
    pl = json.load(open(p, encoding='utf-8'))['players']
    keys = PL.KEYS[sport]
    rows = []
    for cid, e in pl.items():
        t = e['t']
        rows.append((PL.fantasy(t, sport), e, t, cid))
    rows.sort(key=lambda r: (-r[0], r[1]['n']))
    body = [[e['n'], e['s'], (PL.guess_pos(t) if sport == 'fb' else None), e['g'], fp] + [t.get(k, 0) for k in keys] for fp, e, t, cid in rows[:TOP]]
    base = os.path.join(out, 'sections', sec_id, sport)
    os.makedirs(base, exist_ok=True)
    with open(os.path.join(base, 'players.json'), 'w', encoding='utf-8') as f:
        json.dump({'section': sec_id, 'sport': sport, 'total': len(rows), 'keys': keys, 'columns': ['name', 'school', 'pos', 'games', 'fp'] + keys, 'players': body},
                  f, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return len(rows)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default=os.path.join(ROOT, 'data', 'sections'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'api', 'v1'))
    ap.add_argument('--players', default=os.path.join(ROOT, 'data', 'players'))
    a = ap.parse_args(argv)
    if not os.path.isdir(a.data):
        print('no data folder at %s; nothing to build' % a.data)
        return 0
    if os.path.isdir(a.out):
        shutil.rmtree(a.out)
    idx, updated = {}, ''
    for fn in sorted(os.listdir(a.data)):
        if not fn.endswith('.json') or fn == 'index.json':
            continue
        sec = json.load(open(os.path.join(a.data, fn), encoding='utf-8'))
        sec.setdefault('section', fn[:-5])
        updated = max(updated, sec.get('synced') or '')
        info = {s: build_sport(sec, s, a.out) for s in SPORTS}
        for s in SPORTS:
            np = build_players(sec['section'], s, a.players, a.out)
            if np:
                (info.get(s) or info.setdefault(s, {'teams': 0, 'games': 0, 'played': 0, 'weeks': 0}))['players'] = np
        info = {s: v for s, v in info.items() if v}
        if info:
            idx[sec['section']] = {'id': sec['section'], 'partial': bool(sec.get('partial')), 'sports': info,
                                   'links': {s: 'sections/%s/%s/' % (sec['section'], s) for s in info}}
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump({'version': VERSION, 'updated': updated, 'sections': [idx[k] for k in sorted(idx)]}, f, sort_keys=True, separators=(',', ':'))
    print('api: %d sections -> %s' % (len(idx), a.out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
