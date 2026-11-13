"""Player stats for every section from MaxPreps game box scores. Run on a GitHub Actions runner or any machine that can reach maxpreps.com.

    python3 tools/sections/players.py --sport fb [--cache .mpcache] [--delay 1.0] [--max-games N] [--max-minutes M] [--data data/sections] [--out data/players]

Reads the games the collector saved in data/sections/*.json (played games with a box-score url), fetches each box score once, adds the
players' lines up per player and writes data/players/<section>.<sport>.json plus data/players/<sport>.done.json (the games already counted),
so a later run only fetches new games and a run cut short by --max-minutes loses nothing. The page format and the football stat mapping
are the same ones tools/fb_boxscores/collect.js has used for San Diego since Nov 5 (the box page's embedded 'teams' / 'statsByTeamId' JSON).
Basketball column names are matched by name (BB_COLS); columns that match nothing are listed at the end of the run so the map can be fixed.
A player's section is the section of the school the box score lists them for (found by matching the team name against the game's two teams),
so players from a game against another section land in their own section. Positions are guessed from the stats (football: QB, RB, WR, DEF, K;
basketball: none) until rosters are collected. Totals are never double counted: a game is in the done list only after its lines were added."""
import argparse, json, os, re, sys, time, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import maxpreps as M  # noqa: E402

BASE = 'https://www.maxpreps.com'
FB_KEYS = ['passYd', 'passTD', 'int', 'rushYd', 'rushTD', 'rec', 'recYd', 'recTD', 'fumLost', 'tkl', 'sack', 'dInt', 'ff', 'fr', 'dTD', 'retTD',
           'xpm', 'xpMiss', 'fgm', 'fgMiss', 'puntYd', 'in20', 'punts', 'tfl', 'pbu']
BB_KEYS = ['pts', 'reb', 'ast', 'stl', 'blk', 'tov', 'tpm']
KEYS = {'fb': FB_KEYS, 'bb': BB_KEYS}
FB_PTS = {'passYd': .04, 'passTD': 4, 'int': -2, 'rushYd': .1, 'rushTD': 6, 'rec': 1, 'recYd': .1, 'recTD': 6, 'fumLost': -2, 'tkl': 1.25, 'sack': 3, 'dInt': 5,
          'ff': 4, 'fr': 3, 'dTD': 6, 'retTD': 6, 'xpm': 1, 'xpMiss': -1, 'fgm': 3, 'fgMiss': -1, 'puntYd': 0, 'in20': 1, 'punts': 0, 'tfl': 2, 'pbu': 2}
BB_PTS = {'pts': 1, 'reb': 1.2, 'ast': 1.5, 'stl': 3, 'blk': 3, 'tov': -2, 'tpm': 0}
# basketball: normalised column name (lower case letters and digits) -> app key. The first matching column of a player wins.
BB_COLS = {'points': 'pts', 'pts': 'pts', 'totalpoints': 'pts', 'rebounds': 'reb', 'totalrebounds': 'reb', 'reb': 'reb', 'totreb': 'reb',
           'assists': 'ast', 'ast': 'ast', 'steals': 'stl', 'stl': 'stl', 'blocks': 'blk', 'blockedshots': 'blk', 'blk': 'blk', 'blocksnum': 'blk',
           'turnovers': 'tov', 'tov': 'tov', 'to': 'tov', 'threepointersmade': 'tpm', 'threepointfieldgoalsmade': 'tpm', '3ptmade': 'tpm',
           '3pm': 'tpm', 'threepointfgm': 'tpm', 'fg3m': 'tpm', 'threepointersnum': 'tpm'}


# ---------------------------------------------------------------- parsing (offline-testable)
def rsc_text(html):
    out = []
    for m in re.finditer(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', html):
        try:
            out.append(json.loads('"' + m.group(1) + '"'))
        except ValueError:
            pass
    return ''.join(out)


def stats_obj(text):
    """The box score's stats object ({teams, statsByTeamId}) or None when the page has no stats."""
    k = text.find('{"teams":[')
    if k < 0:
        return None
    ls = text.rfind('\n', 0, k) + 1
    le = text.find('\n', k)
    line = text[ls:le if le >= 0 else len(text)]
    try:
        return json.loads(line[line.index(':') + 1:])[3]
    except (ValueError, IndexError):
        return None


def _num(x):
    try:
        v = float(x)
        return 0.0 if v != v else v
    except (TypeError, ValueError):
        return 0.0


def _rows(sg):
    st = sg.get('stats')
    if not st:
        return
    names = [c['name'] for c in st['columns']]
    ni = names.index('Name') if 'Name' in names else -1
    if ni < 0:
        return
    for r in st.get('rows') or []:
        nc = r['columns'][ni]
        m = re.search(r'athletes/([^/]+)/\?careerid=(\w+)', nc.get('href') or '')
        if m:
            yield m.group(2), nc.get('value') or '', names, r['columns']


def football_lines(o):
    """-> [(team label, {careerid: {'n': name, 'k': {key: value}}})] from one box score."""
    out = []
    for tm in o.get('teams') or []:
        S = (o.get('statsByTeamId') or {}).get(tm['id'])
        P = {}
        if S:
            for grp in S.get('groups') or []:
                for sg in grp.get('subgroups') or []:
                    for cid, name, N, C in _rows(sg):
                        p = P.setdefault(cid, {'n': name, 'k': {}})
                        k = p['k']
                        v = lambda n: _num(C[N.index(n)]['value']) if n in N else 0.0
                        add = lambda key, x: k.__setitem__(key, k.get(key, 0) + x) if x else None
                        g = sg.get('name')
                        if g == 'Passing': add('passYd', v('PassingYards')); add('passTD', v('PassingTD')); add('int', v('PassingInt'))
                        elif g == 'Rushing': add('rushYd', v('RushingYards')); add('rushTD', v('RushingTDNum'))
                        elif g == 'Receiving': add('rec', v('ReceivingNum')); add('recYd', v('ReceivingYards')); add('recTD', v('ReceivingTDNum'))
                        elif g == 'Offensive Fumbles and Pancake Blocks': add('fumLost', v('OffensiveFumblesLost'))
                        elif g == 'Tackles': add('tkl', v('TotalTackles')); add('tfl', v('TacklesForLoss'))
                        elif g == 'Sacks': add('sack', v('Sacks'))
                        elif g == 'Defensive Statistics': add('dInt', v('INTs')); add('ff', v('CausedFumbles')); add('fr', v('FumbleRecoveries')); add('pbu', v('PassesDefensed'))
                        elif g == 'Touchdowns': add('dTD', v('FumbleReturnedTDNum') + v('IntReturnedTDNum')); add('retTD', v('PuntReturnedTDNum') + v('KickoffReturnedTDNum'))
                        elif g == 'PATs and Field Goals':
                            pm, fm = v('PATKickingMade'), v('FGMade')
                            add('xpm', pm); add('xpMiss', v('PATKickingAtt') - pm); add('fgm', fm); add('fgMiss', v('FGAttempted') - fm)
                        elif g == 'Punts': add('puntYd', v('PuntYards')); add('in20', v('PuntInside20')); add('punts', v('PuntNum'))
        out.append((tm.get('label') or '', {c: p for c, p in P.items() if p['k']}))
    return out


def basketball_lines(o, unknown=None):
    out = []
    for tm in o.get('teams') or []:
        S = (o.get('statsByTeamId') or {}).get(tm['id'])
        P = {}
        if S:
            for grp in S.get('groups') or []:
                for sg in grp.get('subgroups') or []:
                    for cid, name, N, C in _rows(sg):
                        p = P.setdefault(cid, {'n': name, 'k': {}})
                        for i, cn in enumerate(N):
                            if cn == 'Name':
                                continue
                            key = BB_COLS.get(re.sub(r'[^a-z0-9]', '', cn.lower()))
                            if key is None:
                                if unknown is not None and not re.search(r'name|jersey|number|^gp$|games', cn, re.I):
                                    unknown[(sg.get('name'), cn)] = unknown.get((sg.get('name'), cn), 0) + 1
                            elif key not in p['k']:
                                p['k'][key] = _num(C[i]['value'])
        out.append((tm.get('label') or '', {c: p for c, p in P.items() if any(p['k'].values())}))
    return out


def team_school(label, game):
    """Which of the game's two teams a box-score team label is: 'home' / 'away' / None."""
    lb = M.norm(re.sub(r'\s*\([^)]*\)\s*$', '', label))
    for side in ('home', 'away'):
        if lb and lb == M.norm(game[side]):
            return side
    for side in ('home', 'away'):
        n = M.norm(game[side])
        if lb and n and (lb.startswith(n) or n.startswith(lb)):
            return side
    return None


def guess_pos(t):
    """Football position from season totals."""
    g = lambda k: t.get(k, 0)
    if g('passYd') >= 50 or g('passTD'):
        return 'QB'
    if g('xpm') + g('fgm') + g('xpMiss') + g('fgMiss') + g('punts') >= 2 and g('tkl') < 5 and g('rushYd') + g('recYd') < 30:
        return 'K'
    off = g('rushYd') + g('recYd') + 10 * (g('rushTD') + g('recTD'))
    if off > 20 and off >= 3 * (g('tkl') + 3 * g('sack')):
        return 'RB' if g('rushYd') >= g('recYd') else 'WR'
    if g('tkl') or g('sack') or g('dInt') or g('tfl') or g('pbu'):
        return 'DEF'
    return 'RB' if g('rushYd') >= g('recYd') and g('rushYd') else ('WR' if g('recYd') else None)


def fantasy(t, sport):
    if sport == 'bb':
        return round(sum(t.get(k, 0) * w for k, w in BB_PTS.items()), 1)
    s = sum(t.get(k, 0) * w for k, w in FB_PTS.items())
    n = t.get('punts', 0)
    if not n:
        s += t.get('puntYd', 0) * .05
    return round(s, 1)   # punt tiers are per game in the app; the API uses the season total only for ranking


# ---------------------------------------------------------------- the crawl
def box_url(g):
    u = g.get('url') or ''
    if not u:
        return None
    if u.startswith('/'):
        u = BASE + u
    if not u.startswith(BASE + '/'):
        return None
    return u + ('&' if '?' in u else '?') + 'tab=Stats'


def load_sections(data_dir):
    secs = {}
    for fn in sorted(os.listdir(data_dir)):
        if fn.endswith('.json') and fn != 'index.json':
            d = json.load(open(os.path.join(data_dir, fn), encoding='utf-8'))
            secs[d.get('section') or fn[:-5]] = d
    return secs


def run(a, log=print, fetcher=None):
    sport = a.sport
    secs = load_sections(a.data)
    if not secs:
        log('no section data in %s; run the schools-and-games collector first' % a.data)
        return 2
    sec_of, games = {}, {}
    for sid, d in secs.items():
        for sc in d.get('schools', []):
            sec_of[sc['id']] = sid
        for g in d.get('games', []):
            if g.get('sport') == sport and g.get('hs') is not None and g.get('as') is not None and g['id'] not in games:
                games[g['id']] = g
    os.makedirs(a.out, exist_ok=True)
    done_path = os.path.join(a.out, sport + '.done.json')
    done = set(json.load(open(done_path))) if os.path.exists(done_path) else set()
    store = {}   # section -> {pid: player}
    for sid in secs:
        p = os.path.join(a.out, '%s.%s.json' % (sid, sport))
        store[sid] = json.load(open(p, encoding='utf-8'))['players'] if os.path.exists(p) else {}
    todo = sorted((g for g in games.values() if g['id'] not in done and box_url(g)), key=lambda g: (g.get('date') or '', g['id']))
    log('%s: %d played games, %d already counted, %d to fetch (%d have no box-score link)' % (sport, len(games), len(done), len(todo),
        sum(1 for g in games.values() if g['id'] not in done and not box_url(g))))
    if a.max_games:
        todo = todo[:a.max_games]
    fetcher = fetcher or M.Fetcher(delay=a.delay, cache=None, max_age_h=0, log=log)
    unknown, stat = {}, {'fetched': 0, 'nostats': 0, 'unmatched_team': 0, 'notfound': 0}
    stop, t0 = None, time.time()

    def save():
        now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        for sid, pl in store.items():
            if pl:
                tmp = os.path.join(a.out, '%s.%s.json.tmp' % (sid, sport))
                json.dump({'section': sid, 'sport': sport, 'synced': now, 'players': pl}, open(tmp, 'w', encoding='utf-8'), sort_keys=True, ensure_ascii=False, separators=(',', ':'))
                os.replace(tmp, os.path.join(a.out, '%s.%s.json' % (sid, sport)))
        json.dump(sorted(done), open(done_path + '.tmp', 'w'), separators=(',', ':'))
        os.replace(done_path + '.tmp', done_path)

    for i, g in enumerate(todo):
        if a.max_minutes and time.time() - t0 > a.max_minutes * 60:
            stop = 'time limit (%s min)' % a.max_minutes
            break
        url = box_url(g)
        try:
            if not fetcher.allowed(url):
                stop = 'robots.txt disallows box score pages'
                break
            o = stats_obj(rsc_text(fetcher._open(url)))
        except M.NotFound:
            stat['notfound'] += 1
            done.add(g['id'])
            continue
        except M.Blocked as e:
            stop = 'STOPPED: %s' % e
            break
        stat['fetched'] += 1
        if not o:
            stat['nostats'] += 1
            done.add(g['id'])
            continue
        for label, P in (football_lines(o) if sport == 'fb' else basketball_lines(o, unknown)):
            side = team_school(label, g)
            sc_id = g.get(side + '_id') if side else None
            sid = sec_of.get(sc_id)
            if not sid:
                stat['unmatched_team'] += 1
                continue
            school = g[side]
            for cid, p in P.items():
                e = store[sid].setdefault(cid, {'n': p['n'], 's': school, 'i': sc_id, 'g': 0, 't': {}})
                e['g'] += 1
                for k, v in p['k'].items():
                    e['t'][k] = round(e['t'].get(k, 0) + v, 2)
        done.add(g['id'])
        if stat['fetched'] % 200 == 0:
            save()
            log('  %d/%d box scores, %d players so far' % (i + 1, len(todo), sum(len(v) for v in store.values())))
    save()
    log('done: %s. fetched %d, no stats on page %d, team not matched %d, not found %d' % (stop or 'all requested games read', stat['fetched'], stat['nostats'], stat['unmatched_team'], stat['notfound']))
    for sid, pl in sorted(store.items()):
        if pl:
            log('  %-14s %6d players' % (sid, len(pl)))
    if unknown:
        log('basketball columns that matched nothing (add to BB_COLS if they are stats): ' + '; '.join('%s/%s x%d' % (k[0], k[1], n) for k, n in sorted(unknown.items(), key=lambda x: -x[1])[:25]))
    return 1 if (stop or '').startswith('STOPPED') and not stat['fetched'] else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sport', required=True, choices=['fb', 'bb'])
    ap.add_argument('--data', default=os.path.join(os.path.dirname(os.path.dirname(HERE)), 'data', 'sections'))
    ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.dirname(HERE)), 'data', 'players'))
    ap.add_argument('--delay', type=float, default=1.0)
    ap.add_argument('--max-games', type=int, default=0)
    ap.add_argument('--max-minutes', type=float, default=0)
    a = ap.parse_args()
    return run(a)


if __name__ == '__main__':
    sys.exit(main())
