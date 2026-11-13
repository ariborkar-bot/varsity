"""Shared code for per-section data: registry reader, adapters, upsert with correction tracking, coverage.

Normalized section data (one JSON file per section, see README.md):
  {"section": "southern", "synced": "ISO time", "source": "mock|feed",
   "schools": [{"id","name"}],
   "players": [{"id","name","school","sport","pos","grade"}],
   "games":   [{"id","sport","date","home","away","hs","as"}],      # hs/as are null until final
   "lines":   [{"game","player","stats":{...},"v":1}]}               # v goes up every time a stat line is corrected
"""
import json, os, random, re, zlib, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDEX = os.path.join(ROOT, 'index.html')
DATA_DIR = os.path.join(ROOT, 'data', 'sections')
BAR = 0.90   # a section can go live when this share of its schools has a roster, games and stats

SPORT_MIN_ROSTER = {'fb': 11, 'bb': 5}


def registry():
    """Read SECTIONS from index.html so there is one source of truth: {id: {name, full, state, status}}."""
    s = open(INDEX, encoding='utf-8').read()
    out = {}
    for m in re.finditer(r"\{id:'([a-z-]+)',name:'([^']*)',full:'([^']*)',state:'(\w+)',status:'(\w+)'", s):
        out[m.group(1)] = {'name': m.group(2), 'full': m.group(3), 'state': m.group(4), 'status': m.group(5)}
    if not out:
        raise SystemExit('could not read SECTIONS from index.html')
    return out


# ---------------------------------------------------------------- adapters
class Adapter:
    """A data source. fetch() returns normalized data (see module docstring) for one section."""
    name = 'base'

    def fetch(self, section, sports):
        raise NotImplementedError


class MockAdapter(Adapter):
    """Fake, deterministic sample data so the whole pipeline can be tested before a real feed exists.
    Every name starts with 'MOCK' so it can never be mistaken for real schools or players.
    correct=N changes N stat lines, to test correction tracking on a second run."""
    name = 'mock'

    def __init__(self, n_schools=12, correct=0):
        self.n_schools, self.correct = n_schools, correct

    def fetch(self, section, sports):
        rng = random.Random(zlib.crc32(section.encode()))
        schools = [{'id': f'{section}:s{i:02d}', 'name': f'MOCK {section} High {i:02d}'} for i in range(1, self.n_schools + 1)]
        players, games, lines = [], [], []
        for sp in sports:
            per = SPORT_MIN_ROSTER[sp] + 3
            for sc in schools:
                for k in range(per):
                    players.append({'id': f"{sc['id']}:{sp}{k:02d}", 'name': f"MOCK Player {sc['id'][-2:]}-{k:02d}", 'school': sc['name'],
                                    'sport': sp, 'pos': (['QB', 'RB', 'WR', 'DL', 'LB', 'DB', 'K', 'TE'] if sp == 'fb' else ['PG', 'SG', 'SF', 'PF', 'C'])[k % (8 if sp == 'fb' else 5)],
                                    'grade': rng.choice([9, 10, 11, 12])})
            for g in range(self.n_schools * 3):
                a, b = rng.sample(schools, 2)
                day = datetime.date(2026, 9, 1) + datetime.timedelta(days=g * (3 if sp == 'fb' else 2))
                done = g < self.n_schools * 2
                hs, as_ = (rng.randint(0, 45), rng.randint(0, 45)) if sp == 'fb' else (rng.randint(35, 80), rng.randint(35, 80))
                games.append({'id': f'{section}:{sp}{g:03d}', 'sport': sp, 'date': day.isoformat(), 'home': a['name'], 'away': b['name'],
                              'hs': hs if done else None, 'as': as_ if done else None})
                if done:
                    for team in (a, b):
                        for p in [p for p in players if p['school'] == team['name'] and p['sport'] == sp][:6]:
                            st = ({'pts': rng.randint(0, 30), 'reb': rng.randint(0, 12), 'ast': rng.randint(0, 9), 'stl': rng.randint(0, 4),
                                   'blk': rng.randint(0, 3), 'to': rng.randint(0, 5)} if sp == 'bb' else
                                  {'rush_yds': rng.randint(0, 150), 'rec_yds': rng.randint(0, 120), 'pass_yds': rng.randint(0, 250) if p['pos'] == 'QB' else 0,
                                   'td': rng.randint(0, 3), 'tkl': rng.randint(0, 12)})
                            lines.append({'game': f'{section}:{sp}{g:03d}', 'player': p['id'], 'stats': st, 'v': 1})
        for i in range(min(self.correct, len(lines))):
            ln = lines[i * 7 % len(lines)]
            k = sorted(ln['stats'])[0]
            ln['stats'][k] += 1
        return {'section': section, 'source': 'mock', 'schools': schools, 'players': players, 'games': games, 'lines': lines}


class FeedAdapter(Adapter):
    """Placeholder for the real licensed feed. Fill fetch() once the provider and format are known:
    call their API, map their ids to ours (school/player/game ids above), return the normalized dict.
    Keep the license terms (what may be stored and shown) in README.md next to this file."""
    name = 'feed'

    def fetch(self, section, sports):
        raise SystemExit('FeedAdapter is not written yet: it needs the licensed provider, its format and credentials.')


SEED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'seeds')


def _read_lines(path):
    return [l.strip() for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#')] if os.path.exists(path) else []


class MaxPrepsAdapter(Adapter):
    """Schedules and final scores from MaxPreps team pages (see maxpreps.py; run it on the owner's computer, not in the cloud).
    Seeds: tools/sections/seeds/<section>.txt, lines 'fb|<team url>' or 'bb|<team url>'. Teams to stay inside:
    tools/sections/seeds/<section>.names.txt (one school name per line); for san-diego the app's own school list is used.
    Gives schools and games only: rosters and box-score stat lines are not collected yet, so coverage will say so."""
    name = 'maxpreps'

    def __init__(self, delay=2.0, cache=None, max_teams=300, max_age_h=12, seeds_file=None):
        self.delay, self.cache, self.max_teams, self.max_age_h, self.seeds_file = delay, cache, max_teams, max_age_h, seeds_file

    def _names(self, section):
        import maxpreps as M
        names = _read_lines(os.path.join(SEED_DIR, section + '.names.txt'))
        if not names and section == 'san-diego':
            m = re.search(r"const SD_SCHOOLS=(\[.*?\]);", open(INDEX, encoding='utf-8').read())
            names = json.loads(m.group(1)) if m else []
            al = os.path.join(ROOT, 'tools', 'data', 'team_aliases.txt')
            for line in _read_lines(al):
                if '=' in line and line.split('=', 1)[1].strip() in names:
                    names.append(line.split('=', 1)[0].strip())
        return {M.norm(n) for n in names} if names else None

    def fetch(self, section, sports):
        import maxpreps as M
        seeds = {'fb': [], 'bb': []}
        for line in _read_lines(self.seeds_file or os.path.join(SEED_DIR, section + '.txt')):
            sp, _, url = line.partition('|')
            if sp in seeds and url:
                seeds[sp].append(url.strip())
        names = self._names(section)
        if names is None and section != 'california':
            print('  note: no names list for %s, so the crawl may wander the whole state (capped at %d teams)' % (section, self.max_teams))
        fetcher = M.Fetcher(delay=self.delay, cache=self.cache, max_age_h=self.max_age_h)
        schools, games, blocked = {}, {}, None
        for sp in sports:
            if not seeds[sp]:
                print('  no %s seeds for %s' % (sp, section)); continue
            print('%s %s:' % (section, sp))
            teams, g, rep = M.crawl(seeds[sp], sp, names=names, max_teams=self.max_teams, fetcher=fetcher)
            print('  crawled %d teams, %d games, %d rows rejected%s' % (rep['teams_crawled'], len(g), rep['rejects'], ', STOPPED: ' + rep['blocked'] if rep['blocked'] else ''))
            blocked = blocked or rep['blocked']
            for sid, t in teams.items():
                if names is None or M.norm(t['name']) in names:
                    schools[sid] = {'id': sid, 'name': t['name'], 'city': t['city'], 'section': t.get('section'), 'league': t.get('league'), 'division': t.get('division')}
            games.update(g)
        return {'section': section, 'source': 'maxpreps', 'schools': list(schools.values()), 'players': [], 'games': list(games.values()), 'lines': [],
                'partial': bool(blocked)}


def split_by_section(data):
    """One crawl of all California -> {section id: normalized data}. A school's section is the one MaxPreps lists on its team page
    ('San Diego Section' -> 'san-diego', matched against the registry). A game goes into every section that has one of its teams.
    Also returns {unmatched section name: [schools]} so a name the registry does not know is visible, never silently dropped."""
    ids = {v['full'].replace('CIF ', '').strip(): k for k, v in registry().items()}
    sec_of, unmatched = {}, {}
    for sc in data['schools']:
        slug = ids.get(sc.get('section') or '')
        if slug:
            sec_of[sc['id']] = slug
        else:
            unmatched.setdefault(sc.get('section') or '(no section on page)', []).append(sc['name'])
    out = {}
    for slug in sorted(set(sec_of.values())):
        mine = {i for i, v in sec_of.items() if v == slug}
        out[slug] = {'section': slug, 'source': data.get('source'), 'players': [], 'lines': [],
                     'schools': [sc for sc in data['schools'] if sc['id'] in mine],
                     'games': [g for g in data['games'] if g.get('home_id') in mine or g.get('away_id') in mine]}
    return out, unmatched


ADAPTERS = {'mock': MockAdapter, 'feed': FeedAdapter, 'maxpreps': MaxPrepsAdapter}


# ---------------------------------------------------------------- upsert
def upsert(old, new):
    """Merge fresh data into the previous file by id. Returns (merged, changes).
    A stat line whose stats differ from the old ones is a CORRECTION: its v goes up and it is listed in changes,
    so the app (or an admin) knows which players to rescore."""
    changes = {'added_games': 0, 'score_changed': [], 'corrected': [], 'added_lines': 0}
    old = old or {}
    og = {g['id']: g for g in old.get('games', [])}
    for g in new['games']:
        o = og.get(g['id'])
        if not o:
            changes['added_games'] += 1
        elif (o['hs'], o['as']) != (g['hs'], g['as']) and o['hs'] is not None:
            changes['score_changed'].append(g['id'])
    ol = {(l['game'], l['player']): l for l in (old or {}).get('lines', [])}
    for l in new['lines']:
        o = ol.get((l['game'], l['player']))
        if not o:
            changes['added_lines'] += 1
            l['v'] = 1
        elif o['stats'] != l['stats']:
            l['v'] = o['v'] + 1
            changes['corrected'].append({'game': l['game'], 'player': l['player'], 'v': l['v']})
        else:
            l['v'] = o['v']
    # merge by id: anything the feed did not send this time (an incremental fetch) is kept, never silently dropped
    def merge(key, oldl, newl):
        d = {key(x): x for x in oldl}
        d.update({key(x): x for x in newl})
        return list(d.values())
    merged = dict(new)
    merged['schools'] = merge(lambda x: x['id'], old.get('schools', []), new['schools'])
    merged['players'] = merge(lambda x: x['id'], old.get('players', []), new['players'])
    merged['games'] = merge(lambda x: x['id'], old.get('games', []), new['games'])
    merged['lines'] = merge(lambda x: (x['game'], x['player']), old.get('lines', []), new['lines'])
    return merged, changes


# ---------------------------------------------------------------- coverage
def coverage(data):
    """Per school: roster big enough, has games, has stat lines. Returns (rows, share_ready, ready)."""
    sports = sorted({p['sport'] for p in data['players']} | {g['sport'] for g in data['games']})
    rows = []
    lp = {l['player'] for l in data['lines']}
    for sc in data['schools']:
        for sp in sports:
            pl = [p for p in data['players'] if p['school'] == sc['name'] and p['sport'] == sp]
            gm = [g for g in data['games'] if g['sport'] == sp and sc['name'] in (g['home'], g['away'])]
            rows.append({'school': sc['name'], 'sport': sp, 'roster': len(pl) >= SPORT_MIN_ROSTER[sp],
                         'games': len(gm) > 0, 'stats': any(p['id'] in lp for p in pl)})
    full = sum(1 for r in rows if r['roster'] and r['games'] and r['stats'])
    share = full / len(rows) if rows else 0.0
    return rows, share, share >= BAR


def load(path):
    return json.load(open(path, encoding='utf-8')) if os.path.exists(path) else None


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    json.dump(data, open(tmp, 'w', encoding='utf-8'), separators=(',', ':'), sort_keys=True)
    os.replace(tmp, path)
