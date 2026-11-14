"""Offline checks for players.py (synthetic pages shaped like the MaxPreps box-score payload). python3 -I tools/sections/test_players.py"""
import json, os, sys, tempfile, types
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import players as P
import maxpreps as M

n = 0
def check(ok, msg):
    global n
    n += 1
    if not ok:
        print('FAIL:', msg); sys.exit(1)

def col(name): return {'name': name}
def row(name, cid, vals): return {'columns': [{'value': name, 'href': '/athletes/%s/?careerid=%s' % (name.lower().replace(' ', '-'), cid)}] + [{'value': str(v)} for v in vals]}
def sub(name, cols, rows): return {'name': name, 'stats': {'columns': [col('Name')] + [col(c) for c in cols], 'rows': rows}}
def page(obj):
    text = 'junk\n1:["$","div",null,' + json.dumps(obj, separators=(',', ':')) + ']\nmore'
    return '<html><script>self.__next_f.push([1,"' + json.dumps(text)[1:-1] + '"])</script></html>'

fb = {'teams': [{'id': 'A', 'label': 'Alpha (Town, CA)'}, {'id': 'B', 'label': 'Beta (Other, CA)'}], 'statsByTeamId': {
    'A': {'groups': [{'subgroups': [
        sub('Passing', ['PassingYards', 'PassingTD', 'PassingInt'], [row('Quin Back', 'q1', [210, 2, 1])]),
        sub('Rushing', ['RushingYards', 'RushingTDNum'], [row('Quin Back', 'q1', [15, 0]), row('Rex Runner', 'r1', [88, 1])]),
        sub('Tackles', ['TotalTackles', 'TacklesForLoss'], [row('Dan Def', 'd1', [9, 2])]),
        sub('Defensive Statistics', ['INTs', 'CausedFumbles', 'FumbleRecoveries', 'PassesDefensed'], [row('Dan Def', 'd1', [1, 0, 0, 3])]),
        sub('PATs and Field Goals', ['PATKickingMade', 'PATKickingAtt', 'FGMade', 'FGAttempted'], [row('Kai Kicker', 'k1', [3, 4, 1, 2])])]}]},
    'B': {'groups': [{'subgroups': [sub('Receiving', ['ReceivingNum', 'ReceivingYards', 'ReceivingTDNum'], [row('Will Wide', 'w1', [5, 70, 1])])]}]}}}
o = P.stats_obj(P.rsc_text(page(fb)))
check(o and len(o['teams']) == 2, 'stats object found in the embedded payload')
L = dict(P.football_lines(o))
a = L['Alpha (Town, CA)']
check(a['q1']['k'] == {'passYd': 210, 'passTD': 2, 'int': 1, 'rushYd': 15}, 'QB passing and rushing add up: %s' % a['q1'])
check(a['d1']['k'] == {'tkl': 9, 'tfl': 2, 'dInt': 1, 'pbu': 3}, 'defense with TFL and PBU: %s' % a['d1'])
check(a['k1']['k'] == {'xpm': 3, 'xpMiss': 1, 'fgm': 1, 'fgMiss': 1}, 'kicker makes and misses: %s' % a['k1'])
check(L['Beta (Other, CA)']['w1']['k'] == {'rec': 5, 'recYd': 70, 'recTD': 1}, 'receiver')
check(P.stats_obj('no stats here') is None, 'page without stats gives None')
check(P.guess_pos(a['q1']['k']) == 'QB' and P.guess_pos(a['d1']['k']) == 'DEF' and P.guess_pos(a['k1']['k']) == 'K' and P.guess_pos(a['r1']['k']) == 'RB', 'positions guessed')
check(P.fantasy({'passYd': 100, 'passTD': 1}, 'fb') == 8.0, 'football fantasy points')
check(P.fantasy({'pts': 10, 'reb': 5, 'ast': 2}, 'bb') == 19.0, 'basketball fantasy points')

bb = {'teams': [{'id': 'A', 'label': 'Alpha (Town, CA)'}], 'statsByTeamId': {'A': {'groups': [{'subgroups': [
    sub('Scoring', ['Points', 'ThreePointFieldGoalsMade', 'Mystery'], [row('Hoop Star', 'h1', [22, 3, 9])]),
    sub('Rebounding', ['TotalRebounds', 'OffensiveRebounds'], [row('Hoop Star', 'h1', [8, 2])]),
    sub('Other', ['Assists', 'Steals', 'Blocks', 'Turnovers'], [row('Hoop Star', 'h1', [4, 2, 1, 3])])]}]}}}
unk = {}
(lb, pl), = P.basketball_lines(P.stats_obj(P.rsc_text(page(bb))), unk)
check(pl['h1']['k'] == {'pts': 22, 'tpm': 3, 'reb': 8, 'ast': 4, 'stl': 2, 'blk': 1, 'tov': 3}, 'basketball columns mapped: %s' % pl['h1']['k'])
check(('Scoring', 'Mystery') in unk and ('Rebounding', 'OffensiveRebounds') in unk, 'unmatched columns reported')

g = {'home': 'Alpha', 'away': 'Beta'}
check(P.team_school('Alpha (Town, CA)', g) == 'home' and P.team_school('Beta High School (Other, CA)', {'home': 'Alpha', 'away': 'Beta'}) == 'away' and P.team_school('Zed (X, CA)', g) is None, 'team label matching')
check(P.box_url({'url': '/games/10-02-2026/football-26/a-vs-b.htm?c=XYZ'}).endswith('?c=XYZ&tab=Stats') and P.box_url({}) is None and P.box_url({'url': 'https://evil.example/x'}) is None, 'box urls')

# end to end: two sections, a cross-section game, incremental run
class F:
    def __init__(s): s.urls = []
    def allowed(s, u): return True
    def _open(s, u): s.urls.append(u); return page(fb)
tmp = tempfile.mkdtemp()
d, out = os.path.join(tmp, 'sections'), os.path.join(tmp, 'players')
os.makedirs(d)
games = [{'id': 'mp:g1', 'sport': 'fb', 'date': '2026-09-04', 'home': 'Alpha', 'away': 'Beta', 'home_id': 'mp:A', 'away_id': 'mp:B', 'hs': 28, 'as': 14,
          'url': '/games/09-04-2026/football-26/alpha-vs-beta.htm?c=G1'},
         {'id': 'mp:g2', 'sport': 'fb', 'date': '2026-09-11', 'home': 'Alpha', 'away': 'Gamma', 'home_id': 'mp:A', 'away_id': None, 'hs': None, 'as': None, 'url': '/games/x?c=G2'},
         {'id': 'mp:g3', 'sport': 'bb', 'date': '2026-09-05', 'home': 'Alpha', 'away': 'Beta', 'home_id': 'mp:A', 'away_id': 'mp:B', 'hs': 50, 'as': 40, 'url': '/games/y?c=G3'}]
json.dump({'section': 'one', 'schools': [{'id': 'mp:A', 'name': 'Alpha'}], 'games': games}, open(os.path.join(d, 'one.json'), 'w'))
json.dump({'section': 'two', 'schools': [{'id': 'mp:B', 'name': 'Beta'}], 'games': games[:1]}, open(os.path.join(d, 'two.json'), 'w'))
json.dump({'sections': {}}, open(os.path.join(d, 'index.json'), 'w'))
args = types.SimpleNamespace(sport='fb', data=d, out=out, delay=0, max_games=0, max_minutes=0, workers=3)
f = F()
logs = []
check(P.run(args, logs.append, f) == 0, 'run ok')
check(len(f.urls) == 1 and f.urls[0].endswith('?c=G1&tab=Stats'), 'played football game fetched once, unplayed and basketball ignored: %s' % f.urls)
one = json.load(open(os.path.join(out, 'one.fb.json')))['players']
two = json.load(open(os.path.join(out, 'two.fb.json')))['players']
check(set(one) == {'q1', 'r1', 'd1', 'k1'} and set(two) == {'w1'}, 'each team lands in its own section: %s %s' % (set(one), set(two)))
check(one['q1']['s'] == 'Alpha' and one['q1']['g'] == 1 and one['q1']['t']['passYd'] == 210, 'player totals')
f2 = F()
P.run(args, logs.append, f2)
check(f2.urls == [], 'second run fetches nothing (game already counted)')
one2 = json.load(open(os.path.join(out, 'one.fb.json')))['players']
check(one2['q1']['t']['passYd'] == 210 and one2['q1']['g'] == 1, 'no double counting on rerun')
games[1].update(hs=7, **{'as': 0}); games[1]['away_id'] = 'mp:B'; games[1]['away'] = 'Beta'
json.dump({'section': 'one', 'schools': [{'id': 'mp:A', 'name': 'Alpha'}], 'games': games}, open(os.path.join(d, 'one.json'), 'w'))
P.run(args, logs.append, F())
one3 = json.load(open(os.path.join(out, 'one.fb.json')))['players']
check(one3['q1']['g'] == 2 and one3['q1']['t']['passYd'] == 420, 'a newly played game is added on top')
print('ok: %d checks passed' % n)
