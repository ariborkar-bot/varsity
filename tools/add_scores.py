#!/usr/bin/env python3
"""Add final scores to the app's game data. Used by the daily score update (a Claude scheduled task) and by hand.

Football scores go into games.js. Basketball scores go into tools/data/bb_2627_games.txt
(after it, run `python3 tools/make_basketball.py` to rebuild basketball.html).

Input: a text file, one game per line, '|' between fields, home team first:
    sport|YYYY-MM-DD|home|home_score|away|away_score|source
    fb|2026-11-13|Carlsbad|35|Santa Fe Christian|21|https://www.si.com/high-school/...
    bb|2026-11-14|Torrey Pines|64|Carlsbad|58|https://...
sport is fb or bb. source is optional (a URL or outlet name, kept only in the report).
For a football playoff game that is not in games.js yet, put 'P:Division name' after the source,
for example ...|https://...|P:Division I
Lines starting with # are ignored.

How a line is used:
  - Team names are matched to the app's names (punctuation, 'Saint'/'St.', 'Mount'/'Mt.' and 'High School'
    are ignored; tools/data/team_aliases.txt holds extra 'Alias=App name' pairs).
  - If the game is already in the schedule (same two teams, date within 3 days for football, 1 day for
    basketball), its score is filled in. Home and away are taken from the schedule; the scores are swapped
    to match if the source listed the teams the other way round.
  - A game that already has a different score is reported as a CONFLICT and left alone unless --force.
  - A game that is not in the schedule is added if at least one team is a San Diego Section school.
  - Anything that cannot be matched is reported as SKIPPED with the reason, and nothing is guessed.

Other commands:
    python3 tools/add_scores.py --pending [YYYY-MM-DD]   games on or before that date (default today, Pacific) with no score yet
    python3 tools/add_scores.py --names fb|bb            the app's team names
    python3 tools/add_scores.py scores.txt --dry-run     show what would change without writing
Exit code 0 on success (even if some lines were skipped), 2 on bad input.
"""
import datetime, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FB_FILE = os.path.join(ROOT, 'games.js')
BB_FILE = os.path.join(ROOT, 'tools', 'data', 'bb_2627_games.txt')
ALIAS_FILE = os.path.join(ROOT, 'tools', 'data', 'team_aliases.txt')
INDEX = os.path.join(ROOT, 'index.html')
FB_WEEK1_MONDAY = datetime.date(2026, 8, 17)     # football week 1 is the week of Aug 17, 2026
LIMITS = {'fb': (0, 130), 'bb': (5, 180)}
WINDOW = {'fb': 3, 'bb': 1}


def today_pacific():
    # Pacific time without tz data: UTC-8 (PST) is close enough for picking a date. VARSITY_TODAY=YYYY-MM-DD overrides it (for tests).
    if os.environ.get('VARSITY_TODAY'):
        return datetime.date.fromisoformat(os.environ['VARSITY_TODAY'])
    return (datetime.datetime.utcnow() - datetime.timedelta(hours=8)).date()


def norm(s):
    s = s.lower().replace('&', ' and ').replace('’', "'")
    s = re.sub(r"[.'`]", '', s)
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    s = re.sub(r'\b(high school|high|hs|school)\b', ' ', s)
    s = re.sub(r'\bsaint\b', 'st', s)
    s = re.sub(r'\bmount\b', 'mt', s)
    return ' '.join(s.split())


def load_aliases():
    out = []
    if os.path.exists(ALIAS_FILE):
        for ln in open(ALIAS_FILE, encoding='utf-8'):
            ln = ln.strip()
            if ln and not ln.startswith('#') and '=' in ln:
                a, b = ln.split('=', 1)
                out.append((norm(a), b.strip()))
    return out


class Names:
    """Matches a name from a news source to one of the app's names."""
    def __init__(self, names, aliases):
        self.names = sorted(set(names))
        self.by = {}
        for n in self.names:
            self.by.setdefault(norm(n), n)
        for a, b in aliases:              # an alias only counts for the sport whose names include its target
            if b in self.names:
                self.by.setdefault(a, b)

    def find(self, raw):
        k = norm(raw)
        if not k:
            return None
        if k in self.by:
            return self.by[k]
        # a unique name that starts with the other one, word by word ('Cathedral' -> 'Cathedral Catholic')
        c = {v for nk, v in self.by.items() if (nk + ' ').startswith(k + ' ') or (k + ' ').startswith(nk + ' ')}
        return c.pop() if len(c) == 1 else None


# ---------- football: games.js ----------
def fb_load():
    s = open(FB_FILE, encoding='utf-8').read()
    i, j = s.index('{'), s.rindex('}')
    return s[:i], json.loads(s[i:j + 1]), s[j + 1:]


def fb_save(head, data, tail):
    open(FB_FILE, 'w', encoding='utf-8').write(head + json.dumps(data, separators=(',', ':'), ensure_ascii=False) + tail)


def fb_sd_schools():
    m = re.search(r'SD_SCHOOLS=(\[[^\]]*\])', open(INDEX, encoding='utf-8').read())
    return json.loads(m.group(1)) if m else []


# ---------- basketball: tools/data/bb_2627_games.txt ----------
SCORE_RE = re.compile(r' (\d{1,3})-(\d{1,3})$')


def bb_load():
    lines = open(BB_FILE, encoding='utf-8').read().split('\n')
    names = lines[0][6:].split('|')
    games = []
    for ln in lines[1:]:
        if not ln.strip():
            continue
        g = {'raw': ln}
        sc = SCORE_RE.search(ln)
        body = ln[:sc.start()] if sc else ln
        g['hs'], g['as'] = (int(sc.group(1)), int(sc.group(2))) if sc else (None, None)
        md, hm, rest = body.split(' ', 2)
        h, a = rest.rsplit(' ', 1) if rest.startswith('~') else rest.split(' ', 1)
        nm = lambda t: t[1:] if t.startswith('~') else names[int(t)]
        mo, dy = int(md[:2]), int(md[2:])
        g.update(md=md, hm=hm, ht=h, at=a, h=nm(h), a=nm(a),
                 d=datetime.date(2026 if mo >= 7 else 2027, mo, dy))
        games.append(g)
    return names, games


def bb_line(g):
    base = '%s %s %s %s' % (g['md'], g['hm'], g['ht'], g['at'])
    return base + (' %d-%d' % (g['hs'], g['as']) if g['hs'] is not None else '')


def bb_save(names, games):
    games.sort(key=lambda g: (g['d'], g['hm']))
    out = ['NAMES:' + '|'.join(names)] + [bb_line(g) for g in games]
    open(BB_FILE, 'w', encoding='utf-8').write('\n'.join(out) + '\n')


# ---------- main ----------
def parse(path):
    rows, bad = [], []
    for n, ln in enumerate(open(path, encoding='utf-8'), 1):
        ln = ln.strip()
        if not ln or ln.startswith('#'):
            continue
        f = [x.strip() for x in ln.split('|')]
        try:
            sp, d, h, hs, a, as_ = f[:6]
            assert sp in ('fb', 'bb'), 'sport must be fb or bb'
            d = datetime.date.fromisoformat(d)
            hs, as_ = int(hs), int(as_)
            lo, hi = LIMITS[sp]
            assert lo <= hs <= hi and lo <= as_ <= hi, 'score out of range'
            assert d <= today_pacific() + datetime.timedelta(days=1), 'date is in the future'
            rows.append(dict(n=n, sp=sp, d=d, h=h, hs=hs, a=a, as_=as_,
                             src=f[6] if len(f) > 6 else '', extra=f[7] if len(f) > 7 else ''))
        except Exception as e:
            bad.append('line %d: %s (%s)' % (n, ln, e))
    return rows, bad


def main(argv):
    force = '--force' in argv
    dry = '--dry-run' in argv
    args = [a for a in argv if not a.startswith('--')]
    aliases = load_aliases()

    if '--names' in argv:
        sp = args[0] if args else 'fb'
        if sp == 'fb':
            _, data, _ = fb_load()
            print('\n'.join(sorted({x for g in data['games'] for x in (g['h'], g['a'])})))
        else:
            names, games = bb_load()
            print('\n'.join(sorted(set(names) | {x for g in games for x in (g['h'], g['a'])})))
        return 0

    if '--pending' in argv:
        upto = datetime.date.fromisoformat(args[0]) if args else today_pacific()
        _, data, _ = fb_load()
        for g in data['games']:
            if g['hs'] is None and datetime.date.fromisoformat(g['d']) <= upto:
                print('fb|%s|%s|?|%s|?' % (g['d'], g['h'], g['a']))
        _, games = bb_load()
        for g in games:
            if g['hs'] is None and g['d'] <= upto:
                print('bb|%s|%s|?|%s|?' % (g['d'].isoformat(), g['h'], g['a']))
        return 0

    if not args:
        print(__doc__)
        return 2
    rows, bad = parse(args[0])
    for b in bad:
        print('BAD    ' + b)

    report, changed = [], {'fb': False, 'bb': False}
    head, fbdata, tail = fb_load()
    bbnames, bbgames = bb_load()
    fb_sd = set(fb_sd_schools())
    fb_names = Names({x for g in fbdata['games'] for x in (g['h'], g['a'])} | fb_sd, aliases)
    bb_names = Names(set(bbnames) | {x for g in bbgames for x in (g['h'], g['a'])}, aliases)

    for r in rows:
        sp = r['sp']
        nms = fb_names if sp == 'fb' else bb_names
        sd = fb_sd if sp == 'fb' else set(bbnames)
        h, a = nms.find(r['h']), nms.find(r['a'])
        tag = '%s %s %s %d, %s %d' % (sp, r['d'], h or r['h'], r['hs'], a or r['a'], r['as_'])
        games = fbdata['games'] if sp == 'fb' else bbgames
        gdate = (lambda g: datetime.date.fromisoformat(g['d'])) if sp == 'fb' else (lambda g: g['d'])
        best = None
        if h and a:
            for g in games:
                if {g['h'], g['a']} == {h, a}:
                    dd = abs((gdate(g) - r['d']).days)
                    if dd <= WINDOW[sp] and (best is None or dd < best[0]):
                        best = (dd, g)
        if best:
            g = best[1]
            hs, as_ = (r['hs'], r['as_']) if g['h'] == h else (r['as_'], r['hs'])
            if g['hs'] == hs and g['as'] == as_:
                report.append('SAME   ' + tag)
                continue
            if g['hs'] is not None and not force:
                report.append('CONFLICT %s (app has %s %s, %s %s; use --force to replace)' % (tag, g['h'], g['hs'], g['a'], g['as']))
                continue
            g['hs'], g['as'] = hs, as_
            changed[sp] = True
            report.append('SCORED ' + tag + ('  [%s]' % r['src'] if r['src'] else ''))
            continue
        # not in the schedule: add it if a San Diego Section school played
        hn, an = h or r['h'], a or r['a']
        if hn not in sd and an not in sd:
            why = 'no San Diego Section school recognised' if (h or a) else 'team names not recognised'
            report.append('SKIPPED %s (%s; add a line to tools/data/team_aliases.txt if a name is spelled differently)' % (tag, why))
            continue
        if hn == an:
            report.append('SKIPPED %s (same team twice)' % tag)
            continue
        if sp == 'fb':
            g = {'w': 1 + (r['d'] - FB_WEEK1_MONDAY).days // 7, 'd': r['d'].isoformat(), 'h': hn, 'a': an,
                 'hs': r['hs'], 'as': r['as_']}
            if r['extra'].startswith('P'):
                g['k'] = 'P'
                if ':' in r['extra']:
                    g['dv'] = r['extra'].split(':', 1)[1].strip()
            pos = max([i + 1 for i, x in enumerate(fbdata['games']) if x['w'] <= g['w']] or [len(fbdata['games'])])
            fbdata['games'].insert(pos, g)              # after the last game of that week, so the file stays in week order
        else:
            tok = lambda n: str(bbnames.index(n)) if n in bbnames else '~' + n
            bbgames.append({'md': r['d'].strftime('%m%d'), 'hm': '0000', 'ht': tok(hn), 'at': tok(an), 'h': hn, 'a': an,
                            'd': r['d'], 'hs': r['hs'], 'as': r['as_']})
        changed[sp] = True
        report.append('ADDED  ' + tag + ('  [%s]' % r['src'] if r['src'] else ''))

    print('\n'.join(report) if report else 'No score lines.')
    if not dry:
        if changed['fb']:
            fb_save(head, fbdata, tail)
        if changed['bb']:
            bb_save(bbnames, bbgames)
    print('%s football: %s, basketball: %s' % ('Would write' if dry else 'Wrote',
                                              'changed' if changed['fb'] else 'no change',
                                              'changed' if changed['bb'] else 'no change'))
    return 2 if bad and not rows else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
