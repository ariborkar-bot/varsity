#!/usr/bin/env python3
"""Offline tests for maxpreps.py. The fixture is Bishop's 2026 football schedule exactly as MaxPreps served it on 2026-11-13
(only the fields we read). Run: python3 tools/sections/test_maxpreps.py"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maxpreps as M

B = '9d14d198-9976-4ed2-872d-047b9f317035'
BURL = 'https://www.maxpreps.com/ca/la-jolla/bishops-knights/football/'


def team(sid, text, code, score, name, city, away, url=None):
    t = [None] * 32
    t[1], t[3], t[5], t[6], t[11], t[13], t[14], t[15], t[16] = sid, text, code, score, away, url or ('https://www.maxpreps.com/ca/%s/%s/football/' % (city.lower().replace(' ', '-'), name.lower().replace(' ', '-').replace("'", ''))), name, city, 'CA'
    return t


def row(cid, start, state, summary, a, b):
    r = [None] * 41
    r[1], r[11], r[18], r[28], r[29], r[37], r[38] = cid, start, 'https://www.maxpreps.com/ca/football/game/x/?c=' + cid, state, summary, a, b
    return r


def played(cid, start, b_away, b_score, o_id, o_name, o_city, o_score, summary):
    bc = 'T' if b_score == o_score else ('W' if b_score > o_score else 'L')
    oc = {'W': 'L', 'L': 'W', 'T': 'T'}[bc]
    return row(cid, start, '', summary,
               team(B, '%s %d-%d' % (bc, max(b_score, o_score), min(b_score, o_score)), bc, b_score, "Bishop's", 'La Jolla', 1 if b_away else 0, BURL),
               team(o_id, '', oc, o_score, o_name, o_city, 0 if b_away else 1))


FIX = [
    row('00777c17-4eb2-4322-a04e-f2e7cb332eec', '2026-08-15T13:00:00', 'ContestState is Deleted.', '', team(B, '', None, None, "Bishop's", 'La Jolla', 0), team('b8768f8d-d9f5-425c-a385-dd55623a0f36', '', None, None, 'Brawley', 'Brawley', 1)),
    played('94025099-8a9e-4d70-88bd-cc2552217bb2', '2026-08-21T19:00:00', False, 17, '673c037d-ae98-4fa1-a388-b127758ac382', 'Valley Center', 'Valley Center', 34, "On 8/21, the Valley Center varsity football team won their away non-conference game against Bishop's (La Jolla, CA) by a score of 34-17."),
    played('438a9c6e-de47-4734-9479-e73a430ebc30', '2026-08-28T19:00:00', True, 45, 'cced71fd-7626-472c-b23d-25187e78b508', 'Coronado', 'Coronado', 7, "On 8/28, the Bishop's varsity football team won their away non-conference game against Coronado (CA) by a score of 45-7."),
    played('e2d8f5d6-59ed-40e2-885c-0810652a5d25', '2026-09-04T19:00:00', True, 3, 'fdcaffe2-f6d5-450a-b17f-af4b52e2a651', 'Christian', 'El Cajon', 17, "On 9/4, the Bishop's varsity football team lost their away non-conference game against Christian (El Cajon, CA) by a score of 17-3."),
    played('0f2b2d50-3e36-4435-b8a0-88a6451376c7', '2026-09-12T18:00:00', False, 21, '3d2daff6-3984-4b0f-9ed8-201fdc18edd2', 'Don Lugo', 'Chino', 7, "On 9/12, the Don Lugo varsity football team lost their away non-conference game against Bishop's (La Jolla, CA) by a score of 21-7."),
    played('a2e3debe-9d63-499b-b5ef-1a4d4c97f736', '2026-09-25T19:00:00', True, 35, 'c24601db-aee8-4989-ba5d-bfbf0a91b927', 'La Jolla Country Day', 'La Jolla', 0, "On 9/25, the Bishop's varsity football team won their away conference game against La Jolla Country Day (La Jolla, CA) by a score of 35-0."),
    played('da223b30-d956-47ab-bb39-bd610d9126b4', '2026-10-02T19:00:00', True, 37, 'f8c33d57-a1ba-4322-aac1-acb5b2698e4d', 'Coastal Academy', 'Oceanside', 36, "On 10/2, the Bishop's varsity football team won their away non-conference game against Coastal Academy (Oceanside, CA) by a score of 37-36."),
    played('9c1b52cf-42e7-4191-bdcc-5de800ec72f6', '2026-10-10T19:00:00', False, 34, '298c4785-f891-44e1-bcd2-66d03a3374b7', 'Army-Navy', 'Carlsbad', 6, "On 10/10, the Army-Navy varsity football team lost their away conference game against Bishop's (La Jolla, CA) by a score of 34-6."),
    played('3e1e59ab-c1b5-4820-8b62-02660f7920e9', '2026-10-23T19:15:00', True, 14, '82e8c29f-1537-4887-b1b8-dd4aca6a2573', 'Classical Academy', 'Escondido', 12, "On 10/23, the Bishop's varsity football team won their away non-conference game against Classical Academy (Escondido, CA) by a score of 14-12."),
    played('2103645b-8e57-497d-b71a-e36481a3149b', '2026-10-30T19:00:00', False, 13, '351e2ce0-7021-4bc9-9b29-665923a9b21b', 'Santa Fe Christian', 'Solana Beach', 42, "On 10/30, the Santa Fe Christian varsity football team won their away conference game against Bishop's (La Jolla, CA) by a score of 42-13."),
    row('3add3ebc-af2b-4840-b99b-a324097c80ca', '2026-11-13T19:00:00', 'ContestState is Pregame.', "The Mission Bay varsity football team has a neutral playoff game vs.  Bishop's (La Jolla, CA) today @ 7p.",
        team(B, '', None, None, "Bishop's", 'La Jolla', 2, BURL), team('f2ec9dd0-0f24-4161-a2c3-2a9df393f220', '', None, None, 'Mission Bay', 'San Diego', 2)),
]

ok = 0


def check(cond, msg):
    global ok
    if not cond:
        print('FAIL:', msg)
        sys.exit(1)
    ok += 1


# 1. decoding the real page
games, rej, n = M.decode_contests(FIX, 'fb')
check(n == 10 and len(games) == 10 and not rej, 'decodes all 10 live rows with no rejects: %s %s' % (len(games), rej))
g = {x['date']: x for x in games}
check((g['2026-09-12']['home'], g['2026-09-12']['away'], g['2026-09-12']['hs'], g['2026-09-12']['as']) == ("Bishop's", 'Don Lugo', 21, 7), '9/12 home/away and score')
check((g['2026-08-28']['home'], g['2026-08-28']['away'], g['2026-08-28']['hs'], g['2026-08-28']['as']) == ('Coronado', "Bishop's", 7, 45), '8/28 Bishop\'s was away')
check(g['2026-11-13']['hs'] is None and g['2026-11-13']['ha'] is False and g['2026-11-13']['state'] == 'Pregame', 'pregame neutral game: no score, ha False')
check(all(x['ha'] for d, x in g.items() if d != '2026-11-13'), 'home/away known for every played game')

# 2. cross-check against the app's own games.js (home/away and scores) where names match
gj = os.path.join(os.path.dirname(__file__), '..', '..', 'games.js')
if os.path.exists(gj):
    s = open(gj, encoding='utf-8').read()
    app = json.loads(s[s.index('{'):s.rindex('}') + 1])['games']
    idx = {(a['d'], a['h'], a['a']): a for a in app}
    hit = bad = 0
    for x in games:
        a = idx.get((x['date'], x['home'], x['away']))
        if a and x['hs'] is not None:
            hit += 1
            if (a['hs'], a['as']) != (x['hs'], x['as']):
                bad += 1
    print('  games.js cross-check: %d games matched by date+home+away, %d with different scores' % (hit, bad))
    check(bad == 0, 'scores agree with games.js')

# forfeit: MaxPreps records 2-0 and its sentence has no score; keep the game, flag it
ff = played('07ec2a5e-0000-4000-8000-000000000001', '2026-10-08T19:00:00', True, 0, '351e2ce0-7021-4bc9-9b29-665923a9b21b', 'Santa Fe Christian', 'Solana Beach', 2,
            "On 10/8, the Santa Fe Christian varsity football team won by forfeit in their away conference game against Bishop's (La Jolla, CA).")
gf, rf, _ = M.decode_contests([ff], 'fb')
check(len(gf) == 1 and not rf and gf[0]['forfeit'] and (gf[0]['hs'], gf[0]['as']) == (2, 0), 'a forfeit is kept and flagged')
check(not any(x['forfeit'] for x in games), 'normal games are not forfeits')

# 3. bad rows are rejected, never written; a format change raises instead of producing garbage
bad_row = json.loads(json.dumps(FIX[2]))
bad_row[37][6] = 99
games2, rej2, _ = M.decode_contests([bad_row] + FIX[3:], 'fb')
check(len(games2) == 8 and len(rej2) == 1, 'a row whose score is not in its summary is rejected')
shifted = [[None] + r for r in FIX[1:]]
try:
    M.decode_contests(shifted, 'fb')
    check(False, 'shifted columns must raise')
except M.FormatChanged:
    check(True, 'shifted columns raise FormatChanged')

# 4. crawl: follows only allowed opponents, validates urls, stops on Blocked
class Fake:
    def __init__(self, pages, block_after=None):
        self.pages, self.n, self.block_after = pages, 0, block_after

    def schedule(self, url):
        self.n += 1
        if self.block_after is not None and self.n > self.block_after:
            raise M.Blocked('HTTP 429')
        return {'contests': self.pages.get(url, []), 'meta': {'team_id': B, 'section': 'San Diego Section', 'league': 'Coastal', 'division': 'SDS Division 1-5'} if url == BURL else {}}


names = {M.norm(x) for x in ("Bishop's", 'Coronado', 'Christian', 'Don Lugo')}
f = Fake({BURL: FIX})
teams, cg, rep = M.crawl([BURL], 'fb', names=names, fetcher=f, log=lambda *_: None)
queued = {u for u in f.pages} | {BURL}
check(rep['teams_crawled'] == 4 and f.n == 4, 'crawl visits the seed and only the 3 allowed opponents (got %d)' % rep['teams_crawled'])
check(len(cg) == 10, 'games are deduplicated by contest id')
f2 = Fake({BURL: FIX}, block_after=1)
_, _, rep2 = M.crawl([BURL], 'fb', names=None, fetcher=f2, log=lambda *_: None)
check(rep2['blocked'] and rep2['pages'] == 1, 'crawl stops at the first Blocked')
try:
    M.Fetcher().schedule('https://evil.example.com/ca/x/y/football/')
    check(False, 'foreign url must be refused')
except ValueError:
    check(True, 'non-MaxPreps team url is refused')
class Fake404(Fake):
    def schedule(self, url):
        if 'coronado' in url:
            raise M.NotFound('HTTP 404')
        return super().schedule(url)


f3 = Fake404({BURL: FIX})
_, g3, rep3 = M.crawl([BURL], 'fb', names=names, fetcher=f3, log=lambda *_: None)
check(rep3['blocked'] is None and len(g3) == 10, 'a 404 on one team page is skipped and the crawl carries on')
check(teams['mp:' + B].get('section') == 'San Diego Section' and teams['mp:' + B].get('league') == 'Coastal', 'the crawl tags a crawled team with its section and league')

# stale pages (an old copy served by a cache or another network) stop the crawl
stale = [json.loads(json.dumps(r)) for r in FIX]
f4 = Fake({BURL: stale})
_, _, rep4 = M.crawl([BURL], 'fb', names=names, fetcher=f4, log=lambda *_: None, fresh_after='2027-01-01')
check(rep4['blocked'] and 'stale' in rep4['blocked'], 'old pages are refused as stale')
print('ok: %d checks passed' % ok)
