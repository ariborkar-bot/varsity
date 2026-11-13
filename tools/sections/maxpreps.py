"""MaxPreps collector: schedules and final scores for a section's teams, read from the JSON each MaxPreps team page embeds
(<script id="__NEXT_DATA__">). Written for the owner's data permission; keep it polite and swap it for a licensed feed when one exists.

It has to run on a computer with normal internet (the owner's), NOT in the cloud workspace, whose network is allowlisted.

How it works
  - Start from seed team pages, read each team's /schedule/ page, decode its games, and follow opponent team links
    that belong to the section (name allow-list), so one seed finds the whole section.
  - MaxPreps stores each game as a positional array. FIELDS below names the positions we use; every row is checked
    (ids, date, scores vs. W/L code, score text found in MaxPreps' own summary sentence). If more than 20% of a page's
    rows fail, FormatChanged is raised instead of writing wrong data.
  - Manners: one request at a time, delay between requests (default 2 s + jitter), honest User-Agent, robots.txt respected,
    on-disk cache (default 12 h) so re-runs do not refetch, and it STOPS at the first 403/429/503 (Blocked) rather than retrying.
Positions (contest row r, team row t) were verified on 2026-11-13 against known results (see test_maxpreps.py):
  r[1] contest id, r[11] start time, r[18] game page url, r[28] state text, r[29] summary sentence, r[37] and r[38] team rows
  t[1] school id, t[5] W/L/T, t[6] score, t[11] 1=away 0=home (2 when not set, e.g. neutral playoff), t[13] team url, t[14] name, t[15] city, t[16] state
"""
import collections, datetime, hashlib, json, os, random, re, time, urllib.error, urllib.parse, urllib.request, urllib.robotparser

BASE = 'https://www.maxpreps.com'
UA = 'VARSITY-collector/1.0 (+%s)' % os.environ.get('VARSITY_CONTACT', 'https://github.com/ariborkar-bot/varsity')
NEXT_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)
TEAM_URL_RE = re.compile(r'^https://www\.maxpreps\.com/[a-z]{2}/[a-z0-9-]+/[a-z0-9-]+/(football|basketball)/$')
UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')


class Blocked(Exception):
    """The site refused us (403/429/503) or robots.txt disallows the page. Stop and wait; never hammer."""


class NotFound(Exception):
    """One page does not exist (404/410), for example a school with no team in that sport. Skip it and carry on."""


class FormatChanged(Exception):
    """MaxPreps changed its page format; do not write data."""


def norm(name):
    return re.sub(r'[^a-z0-9]', '', (name or '').lower().replace('high school', '').replace('saint', 'st'))


def next_data(html):
    m = NEXT_RE.search(html)
    if not m:
        raise FormatChanged('no __NEXT_DATA__ in page')
    return json.loads(m.group(1))


def _score(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.strip().isdigit():
        return int(v)
    return None


def decode_contests(contests, sport):
    """-> (games, rejects, checked). Games are dicts; unplayed games have hs/as None.
    home/away come from t[11] (0 home, 1 away). When MaxPreps has not set it (neutral site, not yet scheduled) the page's
    own team is listed first as 'home' and ha is False."""
    games, rejects, checked = [], [], 0
    for r in contests or []:
        try:
            if not isinstance(r, list) or len(r) < 39:
                raise ValueError('short row')
            if r[28] == 'ContestState is Deleted.':
                continue
            checked += 1
            cid, start = r[1], str(r[11])
            date = start[:10]
            if not UUID_RE.match(str(cid)) or not re.fullmatch(r'\d{4}-\d\d-\d\d', date):
                raise ValueError('bad id or date')
            a, b = r[37], r[38]
            for t in (a, b):
                if not isinstance(t, list) or len(t) < 17 or not isinstance(t[14], str) or not t[14] or not UUID_RE.match(str(t[1])):
                    raise ValueError('bad team row')
            if sorted([a[11], b[11]]) == [0, 1]:
                home, away, ha = (a, b, True) if a[11] == 0 else (b, a, True)
            else:
                home, away, ha = a, b, False
            hs, as_ = _score(home[6]), _score(away[6])
            if (hs is None) != (as_ is None):
                raise ValueError('only one score')
            if hs is not None:
                code = 'T' if hs == as_ else ('W' if hs > as_ else 'L')
                if home[5] and home[5] != code:
                    raise ValueError('W/L code disagrees with score')
                summ = r[29] or ''
                forfeit = 'forfeit' in summ.lower()   # MaxPreps records a placeholder score (2-0) and the sentence has no score
                if summ and not forfeit and ('%d-%d' % (max(hs, as_), min(hs, as_))) not in summ:
                    raise ValueError('score not in summary')
            else:
                forfeit = False
            games.append({'id': 'mp:' + cid, 'sport': sport, 'date': date, 'time': start[11:16], 'home': home[14], 'away': away[14],
                          'home_id': 'mp:' + home[1], 'away_id': 'mp:' + away[1], 'hs': hs, 'as': as_, 'ha': ha, 'forfeit': forfeit,
                          'state': (r[28] or '').replace('ContestState is ', '').rstrip('.'), 'url': r[18] if isinstance(r[18], str) else None})
        except (ValueError, TypeError, IndexError, KeyError) as e:
            rejects.append((str(r[1])[:8] if isinstance(r, list) and len(r) > 1 else '?', str(e)))
    if checked >= 3 and len(rejects) / checked > 0.2:
        raise FormatChanged('%d of %d rows failed checks: %s' % (len(rejects), checked, rejects[:3]))
    return games, rejects, checked


def team_meta(pp):
    """The page's own team: id and its section / league / division (pp.teamContext.data)."""
    d = ((pp.get('teamContext') or {}).get('data')) or {}
    return {'team_id': d.get('teamId'), 'section': d.get('sectionName'), 'league': d.get('leagueName'), 'division': d.get('sectionDivisionName')}


def teams_in(contests):
    """Every team seen on a schedule: {school_id: {name, city, state, url}}."""
    out = {}
    for r in contests or []:
        if not isinstance(r, list) or len(r) < 39 or r[28] == 'ContestState is Deleted.':
            continue
        for t in (r[37], r[38]):
            try:
                if UUID_RE.match(str(t[1])) and t[14]:
                    out['mp:' + t[1]] = {'name': t[14], 'city': t[15], 'state': t[16], 'url': t[13] if isinstance(t[13], str) else None}
            except (TypeError, IndexError):
                pass
    return out


class Fetcher:
    def __init__(self, delay=2.0, cache=None, max_age_h=12, log=print):
        self.delay, self.cache, self.max_age, self.log = delay, cache, max_age_h * 3600, log
        self.last = 0.0
        self.rp = None
        if cache:
            os.makedirs(cache, exist_ok=True)

    def _open(self, url):
        wait = self.delay + random.uniform(0, self.delay * 0.4) - (time.time() - self.last)
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/html', 'Accept-Encoding': 'identity'})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            if e.code in (403, 429, 503):
                raise Blocked('HTTP %d from %s' % (e.code, url))
            if e.code in (404, 410):
                raise NotFound('HTTP %d from %s' % (e.code, url))
            raise
        except (urllib.error.URLError, OSError) as e:
            raise Blocked('cannot reach %s (%s)' % (url, getattr(e, 'reason', e)))
        finally:
            self.last = time.time()

    def allowed(self, url):
        if self.rp is None:
            rp = urllib.robotparser.RobotFileParser()
            try:
                rp.parse(self._open(BASE + '/robots.txt').splitlines())
            except NotFound:
                rp.parse([])   # no robots.txt: nothing disallowed
            # Blocked (site refused us or unreachable) propagates and stops the run; self.rp stays unset so the next page retries
            self.rp = rp
        return self.rp.can_fetch(UA, url)

    def schedule(self, team_url):
        """-> {'contests': [...rows], 'meta': {team_id, section, league, division}} for a team's /schedule/ page (cached)."""
        if not TEAM_URL_RE.match(team_url):
            raise ValueError('not a MaxPreps team url: ' + team_url)
        url = team_url + 'schedule/'
        path = os.path.join(self.cache, hashlib.sha1(url.encode()).hexdigest() + '.json') if self.cache else None
        if path and os.path.exists(path) and time.time() - os.path.getmtime(path) < self.max_age:
            c = json.load(open(path))
            return {'contests': c['contests'], 'meta': c.get('meta') or {}}
        if not self.allowed(url):
            raise Blocked('robots.txt disallows ' + url)
        pp = next_data(self._open(url))['props']['pageProps']
        contests = pp.get('contests')
        if not isinstance(contests, list):
            raise FormatChanged('no contests list on ' + url)
        meta = team_meta(pp)
        if path:
            json.dump({'url': url, 'contests': contests, 'meta': meta}, open(path, 'w'))
        return {'contests': contests, 'meta': meta}


def crawl(seeds, sport, names=None, state='CA', max_teams=300, fetcher=None, log=print, fresh_after=None):
    """Snowball from seed team urls. names = set of norm()ed team names to stay inside (None = whole state, capped by max_teams).
    -> (teams, games, report)."""
    fetcher = fetcher or Fetcher(log=log)
    if fresh_after is None:
        fresh_after = (datetime.date.today() - datetime.timedelta(days=150)).isoformat()
    queue, seen, games, teams = collections.deque(seeds), set(), {}, {}
    report = {'pages': 0, 'rejects': 0, 'blocked': None, 'skipped_not_in_names': 0}
    while queue and len(seen) < max_teams:
        url = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        try:
            page = fetcher.schedule(url)
            contests, meta = page['contests'], page.get('meta') or {}
        except FormatChanged as e:
            report['format_skips'] = report.get('format_skips', 0) + 1
            log('  SKIPPED (format): %s: %s' % (url.split('/maxpreps.com')[-1], e))
            if report['format_skips'] > max(5, report['pages'] * 0.03):
                report['blocked'] = 'format changed: %d of %d pages failed the checks' % (report['format_skips'], report['pages'])
                log('STOPPED: ' + report['blocked'])
                break
            continue
        except NotFound as e:
            log('  skipped (not found): %s' % e)
            continue
        except Blocked as e:
            report['blocked'] = str(e)
            log('STOPPED: %s' % e)
            break
        report['pages'] += 1
        try:
            gs, rej, n = decode_contests(contests, sport)
        except FormatChanged as e:
            # one odd page (a team whose rows fail the checks) is skipped and logged; many means MaxPreps changed, so stop
            report['format_skips'] = report.get('format_skips', 0) + 1
            log('  SKIPPED (format): %s: %s' % (url.split('/maxpreps.com')[-1], e))
            if report['format_skips'] > max(5, report['pages'] * 0.03):
                report['blocked'] = 'format changed: %d of %d pages failed the checks' % (report['format_skips'], report['pages'])
                log('STOPPED: ' + report['blocked'])
                break
            continue
        report['rejects'] += len(rej)
        if len(gs) >= 3 and max(g['date'] for g in gs) < fresh_after:
            report['blocked'] = 'stale pages: newest game on %s is %s (before %s); this network may be served an old copy' % (url, max(g['date'] for g in gs), fresh_after)
            log('STOPPED: ' + report['blocked'])
            break
        for g in gs:
            games.setdefault(g['id'], g)
        for sid, t in teams_in(contests).items():
            teams.setdefault(sid, t)
        if meta.get('team_id') and 'mp:' + meta['team_id'] in teams:
            teams['mp:' + meta['team_id']].update({k: meta.get(k) for k in ('section', 'league', 'division')})
        for sid, t in teams_in(contests).items():
            if t['state'] != state or not t['url'] or not TEAM_URL_RE.match(t['url']) or t['url'] in seen:
                continue
            if names is not None and norm(t['name']) not in names:
                report['skipped_not_in_names'] += 1
                continue
            queue.append(t['url'])
        log('  %s: %d games (%d rows rejected), queue %d%s' % (url.split('/maxpreps.com')[-1], len(gs), len(rej), len(queue), (' REJECTED: ' + '; '.join('%s %s' % r for r in rej[:3])) if rej else ''))
    report['teams_crawled'] = len(seen)
    return teams, games, report
