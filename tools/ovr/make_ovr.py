"""Build varsity_ovr.xlsx: a Madden-style OVR (40-99) for every player in the app.
usage: python3 tools/ovr/make_ovr.py <dir with fb.json + bb.json> <out dir>   (writes varsity_football_ovr.xlsx and varsity_basketball_ovr.xlsx)
fb.json / bb.json = players() dumped from the football / basketball preview (name, school, pos, sub, gr, gp, tot, inj).
Football: per-game fantasy points (the app's pts()), shrunk toward the position mean (k=2 games), percentile among the same
position group. Basketball: per-game fantasy (pt+1.2reb+1.5ast+3stl+3blk-2tov) from 2025-26 MaxPreps, shrunk (k=3 games),
percentile among all players; no stat line = 0.6 x the average (low-confidence estimate). OVR is a bell curve over the percentile:
ROUND(mean + sd * NORMSINV(pct)) clamped to floor..ceiling, all four as editable cells on the Notes sheet (floor 45 per the owner, ceiling 99)."""
import sys, json, os, io, contextlib, importlib.util
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
D, OUTD = sys.argv[1], sys.argv[2]
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
spec = importlib.util.spec_from_file_location('mb', os.path.join(ROOT, 'tools', 'make_basketball.py')); mb = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()): spec.loader.exec_module(mb)

def pctiles(items):
    """items: list of (idx, score) -> {idx: percentile in (0,1)} with ties averaged"""
    s = sorted(items, key=lambda x: x[1]); n = len(s); out = {}; i = 0
    while i < n:
        j = i
        while j + 1 < n and s[j + 1][1] == s[i][1]: j += 1
        for k in range(i, j + 1): out[s[k][0]] = ((i + j) / 2 + .5) / n
        i = j + 1
    return out

FBKEY = {'QB': ['passYd', 'passTD', 'rushYd'], 'RB': ['rushYd', 'rushTD', 'recYd'], 'WR': ['recYd', 'rec', 'recTD'], 'TE': ['recYd', 'rec', 'recTD'],
         'DL': ['sack', 'tfl', 'tkl'], 'LB': ['tkl', 'tfl', 'sack'], 'DB': ['tkl', 'dInt', 'pbu'], 'DEF': ['tkl', 'tfl', 'sack', 'dInt'], 'K': ['fgm', 'xpm']}
FBLAB = dict(passYd='pass yd', passTD='pass TD', rushYd='rush yd', rushTD='rush TD', recYd='rec yd', rec='rec', recTD='rec TD', sack='sack', tfl='TFL', tkl='tkl', dInt='INT', pbu='PBU', fgm='FG', xpm='PAT')
BBKEY = {'PG': [2, 0, 3], 'SG': [0, 6, 3], 'SF': [0, 1, 3], 'PF': [1, 0, 4], 'C': [1, 4, 0]}   # indices into [pts reb ast stl blk tov tpm]
BBLAB = ['pts', 'reb', 'ast', 'stl', 'blk', 'tov', '3pm']
def keyrank(L, vals):
    """L: list of players, vals: list of lists of the key-stat totals -> (mean percentile of the key stats, per player)"""
    m = len(vals[0]); ps = [pctiles([(i, v[j]) for i, v in enumerate(vals)]) for j in range(m)]
    return [sum(ps[j][i] for j in range(m)) / m for i in range(len(L))]
def sos_fb():
    g = json.load(open(os.path.join(D, 'fbgames.json'))); w = {}; n = {}
    for h, a, hs, as_ in g:
        if hs is None or as_ is None: continue
        for t, f, ag in ((h, hs, as_), (a, as_, hs)):
            n[t] = n.get(t, 0) + 1; w[t] = w.get(t, 0) + (1 if f > ag else .5 if f == ag else 0)
    strength = {t: (w[t] + 1) / (n[t] + 2) for t in n}   # Laplace-smoothed win%
    opp = {}
    for h, a, hs, as_ in g:
        if hs is None or as_ is None: continue
        opp.setdefault(h, []).append(strength.get(a, .5)); opp.setdefault(a, []).append(strength.get(h, .5))
    return {t: sum(v) / len(v) for t, v in opp.items()}
def sos_bb():
    d = json.load(open(os.path.join(D, 'bbsched.json'))); prior = d['prior']; opp = {}
    for h, a in d['games']:
        opp.setdefault(h, []).append(prior.get(a, 0)); opp.setdefault(a, []).append(prior.get(h, 0))
    return {t: sum(v) / len(v) for t, v in opp.items()}
def school_pct(sos):
    pc = pctiles(list(enumerate(sos.values()))); names = list(sos)
    return {names[i]: pc[i] for i in range(len(names))}
SCH_FB = school_pct(sos_fb()); SCH_BB = school_pct(sos_bb())
# Owner overrides (Nov 10): Raw OVR typed in by hand for these players (yellow cell); the 99 cap still applies, so Raw 110 = a top-10 99
MANUAL = {('Paisios Polamalu', 'St. Augustine', 'RB'): (110, 'set to 99'), ('Daine Gonzalez', 'Classical Academy', 'RB'): (94, 'set to 94'),
          ('Courtney Miller-Thompson', 'Granite Hills', 'WR'): (100.847707, 'swapped with Deandre Eleby (WR)'), ('Deandre Eleby', 'Morse', 'WR'): (97.710369, 'swapped with Courtney Miller-Thompson'),
          ('Owen Dorros', 'La Jolla Country Day', 'WR'): (89.32224, 'swapped with DJ Ferguson (WR)'), ('Dj Ferguson', 'University City', 'WR'): (90.009279, 'swapped with Owen Dorros'),
          ('Caden Bessler', 'La Jolla Country Day', 'LB'): (80, 'set to 80'),
          ('Zachary Benitez', 'Granite Hills', 'QB'): (96, 'set to 96'), ('Thomas Dietrich', 'University City', 'QB'): (94, 'set to 94'),
          ('Dax Labrum', 'Santa Fe Christian', 'QB'): (97, 'set to 97'), ('Gaige Weddle', 'Rancho Bernardo', 'QB'): (94, 'set to 94'),
          ('Timothy Cox', 'Clairemont', 'QB'): (90, 'set to 90'), ('Santonio Urena', 'Imperial', 'QB'): (91, 'set to 91'),
          ('Madin Gardini', 'Patrick Henry', 'QB'): (95, 'set to 95'), ('Tyler Holmes', 'Grossmont', 'QB'): (92, 'set to 92'), ('Logan Nelson', 'Madison', 'DL'): (98, 'set to 98'),
          ('Davon Dunn', 'Lincoln', 'DB'): (96, 'set to 96'), ('Devin Davis', 'Lincoln', 'DB'): (93, 'set to 93'), ('Gaige Weddle', 'Rancho Bernardo', 'DB'): (109, 'set to 99'),
          ("T'Marrion Williams", 'Valhalla', 'WR'): (87, 'set to 87')}
rows = []   # dict(name, school, sport, pos, gr, gp, score, pct, status)
fb = json.load(open(os.path.join(D, 'fb.json')))
K = 2
# The app has no position for ~375 defenders: estimate DL/LB/DB from their stat mix (model trained on defenders whose position is known)
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
def _f(p):
    s = p['st']; g = max(p['gp'], 1); t = s['tkl']
    return [t / g, s['tfl'] / g, s['sack'] / g, s['dInt'] / g, s['pbu'] / g, s['ff'] / g, s['fr'] / g, s['sack'] / (t + 1), s['tfl'] / (t + 1), s['dInt'] / (t + 1), s['pbu'] / (t + 1)]
_known = [p for p in fb if p['pos'] == 'DEF' and p['sub'] in ('DL', 'LB', 'DB')]
_unk = [p for p in fb if p['pos'] == 'DEF' and p['sub'] not in ('DL', 'LB', 'DB')]
_m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)).fit(np.array([_f(p) for p in _known]), [p['sub'] for p in _known])
for p, q in zip(_unk, _m.predict(np.array([_f(p) for p in _unk]))): p['sub'] = str(q); p['est'] = True
# Owner position fixes (Nov 10): (name, school, current defensive position) -> position
POS_FIX = {('Marvin Jones III', 'La Jolla Country Day', 'LB'): 'DB'}
for p in fb:
    q = POS_FIX.get((p['name'], p['school'], p['sub']))
    if q: p['sub'] = q; p['fixed'] = True
grp = {}
for p in fb: grp.setdefault(p['sub'], []).append(p)
for g, L in grp.items():
    mu = sum(p['tot'] for p in L) / max(1, sum(p['gp'] for p in L))
    sc = [(i, (p['tot'] + K * mu) / (p['gp'] + K)) for i, p in enumerate(L)]
    pc = pctiles(sc); S = dict(sc); pt = pctiles([(i, p['tot']) for i, p in enumerate(L)])
    ks = FBKEY.get(g, FBKEY['DEF']); kr = keyrank(L, [[p['st'].get(k, 0) for k in ks] for p in L])
    for i, p in enumerate(L):
        rows.append(dict(name=p['name'], school=p['school'], sport='Football', pos=p['sub'], gr=p['gr'], gp=p['gp'], score=round(S[i], 2), tot=round(p['tot'], 1), pcg=pc[i], pct_t=pt[i], pct_k=kr[i], pct_s=SCH_FB.get(p['school'], .5), keys=' · '.join('%s %s' % (round(p['st'].get(k, 0)), FBLAB[k]) for k in ks), status=' · '.join(x for x in ('Out' if p['inj'] else '', 'Position estimated' if p.get('est') else '', 'Position set to DB (owner)' if p.get('fixed') else '') if x)))
bbapp = json.load(open(os.path.join(D, 'bb.json')))
stats = {}
for t in mb.load_real():
    for r in t['rows']:
        if r['st'] and r['gp']:
            pt, rb, a, st, bk, tov, _ = r['st']
            stats[(t['name'], r['n'])] = (r['gp'], pt + 1.2 * rb + 1.5 * a + 3 * st + 3 * bk - 2 * tov, r['st'])
KB = 3
have = [stats[(p['school'], p['name'])] for p in bbapp if (p['school'], p['name']) in stats]
mu = sum(g * f for g, f, _ in have) / sum(g for g, f, _ in have)
sc = []
for i, p in enumerate(bbapp):
    s = stats.get((p['school'], p['name']))
    sc.append((i, (s[0] * s[1] + KB * mu) / (s[0] + KB) if s else .6 * mu))
pc = pctiles(sc); S = dict(sc)
totv = [(i, (stats[(p['school'], p['name'])][0] * stats[(p['school'], p['name'])][1]) if (p['school'], p['name']) in stats else 0) for i, p in enumerate(bbapp)]
pt = pctiles(totv); TV = dict(totv)
bbk = {}
for pos in set(p['pos'] for p in bbapp):
    idx = [i for i, p in enumerate(bbapp) if p['pos'] == pos]; ks = BBKEY.get(pos, BBKEY['SF'])
    def tot(i, k):
        s_ = stats.get((bbapp[i]['school'], bbapp[i]['name']));
        return s_[0] * s_[2][k] if s_ else 0
    kr = keyrank(idx, [[tot(i, k) for k in ks] for i in idx])
    for n_, i in enumerate(idx): bbk[i] = (kr[n_], ' · '.join('%s %s' % (round(tot(i, k)), BBLAB[k]) for k in ks))
nostat = 0
for i, p in enumerate(bbapp):
    s = stats.get((p['school'], p['name'])); nostat += 0 if s else 1
    rows.append(dict(name=p['name'], school=p['school'], sport='Basketball', pos=p['pos'], gr=p['gr'], gp=s[0] if s else 0, score=round(S[i], 2), tot=round(TV[i], 1), pcg=pc[i], pct_t=pt[i], pct_k=bbk[i][0], pct_s=SCH_BB.get(p['school'], .5), keys=bbk[i][1], status=''))
print('football', len(fb), 'basketball', len(bbapp), 'bb without stat line', nostat)

def build(sport):
  wb = Workbook(); nt = wb.active; nt.title = 'Notes'
  AR = 'Arial'
  hdr = Font(name=AR, bold=True, color='FFFFFF'); fill = PatternFill('solid', fgColor='1B2A4A')
  nt['A1'] = 'Varsity %s OVR sheet' % sport; nt['A1'].font = Font(name=AR, bold=True, size=14)
  nt['A3'] = 'Floor (lowest OVR)'; nt['B3'] = 45
  nt['A4'] = 'Ceiling (highest OVR)'; nt['B4'] = 99
  nt['A5'] = 'Mean (the average player)'; nt['B5'] = 70
  nt['A6'] = 'Spread (standard deviation)'; nt['B6'] = 11
  nt['A7'] = 'Weight: points per game'; nt['B7'] = 0.376
  nt['A8'] = 'Weight: season total points'; nt['B8'] = 0.282
  nt['A9'] = 'Weight: rank in his position\'s key stats'; nt['B9'] = 0.282
  nt['A10'] = 'Weight: schedule strength'; nt['B10'] = 0.06
  nt['A11'] = 'Most players allowed at the ceiling (99)'; nt['B11'] = 10
  nt['A12'] = 'QB bonus (OVR points added to every QB)'; nt['B12'] = 3 if sport == 'Football' else 0
  nt['A13'] = 'DB adjustment (every DB OVR is multiplied by this; 0.97 = 3% lower)'; nt['B13'] = 0.97 if sport == 'Football' else 1
  for r in (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13): nt.cell(r, 2).font = Font(name=AR, color='0000FF'); nt.cell(r, 2).fill = PatternFill('solid', fgColor='FFFF00'); nt.cell(r, 1).font = Font(name=AR)
  allnotes = ['OVR = Mean + Spread x (how many standard deviations the player is above or below average, from his percentile), rounded and kept between Floor and Ceiling, so most players land in the 60s-80s, 90+ is rare and nobody is below 45. Blue/yellow cells are inputs: change them and every OVR recalculates.',
   'Four percentiles (0 = worst, 1 = best among his peers): (1) fantasy points per game, (2) total fantasy points this season (rewards playing more and scoring more) and (3) his rank in the stats that matter at his position, the average percentile of the Position stats columns, and (4) schedule strength. Schedule-strength percentile (default weight 6%) = how tough his school’s schedule is compared with other schools: football = the average win% of the opponents it played this season (counting only completed games, smoothed so 1-0 is not 100%); basketball = the average 2025-26 scoring margin of the opponents on its 2026-27 schedule. Division is not used on its own because the app only has division brackets for some schools; strength of schedule captures the same thing. Weighted score = the four percentiles combined with the yellow weights (37.6%/28.2%/28.2%/6% by default, they do not have to add to 1). Because averaging squeezes everyone toward the middle, the weighted scores are re-ranked among his peers (Combined percentile) and OVR comes from that (Raw OVR = mean + spread x his standard deviations above average). Only the top N players in the sport by Raw OVR (the yellow cell, 10) can be a 99; everyone else is capped at 98, so the best player at a position is near the ceiling and the worst at the floor (45). Key stats: QB pass yd, pass TD, rush yd; RB rush yd, rush TD, rec yd; WR/TE rec yd, rec, rec TD; DL sack, TFL, tkl; LB tkl, TFL, sack; DB tkl, INT, PBU; DEF tkl, TFL, sack, INT; K FG, PAT; basketball PG ast, pts, stl; SG pts, 3pm, stl; SF pts, reb, stl; PF reb, pts, blk; C reb, blk, pts (season totals).',
   'Football: Pts per game = fantasy points per game from MaxPreps box scores (the app scoring), shrunk toward the position average (2 games of average added) so one big game does not make a star. Peers = same position (QB, RB, WR, TE, DL, LB, DB, K).',
   'Basketball: Pts per game = points + 1.2 rebounds + 1.5 assists + 3 steals + 3 blocks - 2 turnovers per game from 2025-26 MaxPreps, shrunk (3 games of average added). Peers = every basketball player. Players with no 2025-26 stat line (%d of %d) get 0.6 x the average, so they sit below the middle (low confidence).' % (nostat, len(bbapp)),
   'Games = games with stats behind the rating (football 2026, basketball 2025-26). Few games = low confidence.',
   'One tab per position (best OVR first, # = rank within the position, highest OVR first); the last tab lists everyone. Position estimated = the app had no DL/LB/DB position for this defender, so it was guessed from his stats. Manual OVR = set by the owner (yellow Raw OVR cell). In football every QB gets a small bonus (Notes B12) and every DB is lowered 3% (Notes B13), both owner choices. Status Out = listed as out in the app this week. Basketball grades are 2026-27 (moved up one year); 0 = unknown.',
   'Source: MaxPreps box scores and season stats already in the app (stats.js, tools/data/bb_2526_players.txt). Built by tools/ovr/make_ovr.py.']
  yr = '2026 season' if sport == 'Football' else '2025-26 season (the latest basketball stats; 2026-27 has not started)'
  notes = [allnotes[0], allnotes[1], allnotes[2 if sport == 'Football' else 3], 'Ratings use only this season (%s). Season total fantasy pts = fantasy points per game x games (basketball totals use the 2025-26 averages).' % yr] + allnotes[4:]
  for i, t in enumerate(notes): c = nt.cell(15 + i, 1, t); c.font = Font(name=AR); c.alignment = Alignment(wrap_text=True, vertical='top'); nt.merge_cells(start_row=15 + i, start_column=1, end_row=15 + i, end_column=6); nt.row_dimensions[15 + i].height = 48
  nt.column_dimensions['A'].width = 40; [nt.column_dimensions[c].__setattr__('width', 14) for c in 'BCDEF']
  H = ['#', 'Name', 'OVR', 'School', 'Sport', 'Pos', 'Grade', 'Games', 'Fantasy pts per game (adj.)', 'Season total fantasy pts', 'Per-game percentile', 'Total percentile', 'Position-stats percentile', 'Schedule-strength percentile', 'Weighted score', 'Combined percentile', 'Raw OVR (before cap)', 'Status', 'Position stats (season totals)']
  W = [6, 24, 8, 26, 11, 7, 7, 8, 16, 16, 14, 13, 16, 17, 12, 14, 14, 9, 42]
  NN = len([r for r in rows if r['sport'] == sport]) + 1   # last data row of the All players tab
  def pctf(n):
      # where the weighted score ranks among his peers (football: same position; basketball: all players), ties split; read from the All players tab
      A = "'All players'!"
      if sport == 'Football':
          return (f'=(COUNTIFS({A}$F$2:$F${NN},F{n},{A}$O$2:$O${NN},"<"&O{n})+0.5*COUNTIFS({A}$F$2:$F${NN},F{n},{A}$O$2:$O${NN},O{n}))/COUNTIFS({A}$F$2:$F${NN},F{n})')
      return f'=(COUNTIF({A}$O$2:$O${NN},"<"&O{n})+0.5*COUNTIF({A}$O$2:$O${NN},O{n}))/COUNT({A}$O$2:$O${NN})'
  def sheet(title, items):
      ws = wb.create_sheet(title); ws.append(H)
      for c in ws[1]: c.font = hdr; c.fill = fill; c.alignment = Alignment(horizontal='center')
      wsc = lambda r: .376 * r['pcg'] + .282 * r['pct_t'] + .282 * r['pct_k'] + .06 * r['pct_s']
      # rows are listed highest OVR first (final OVR from the first, recalculated pass: see ORDER), ties by Raw OVR
      items = sorted(items, key=lambda r: (-ORDER.get((r['name'], r['school'], r['pos'], r['score'], r['tot']), (0, 0))[0], -ORDER.get((r['name'], r['school'], r['pos'], r['score'], r['tot']), (0, 0))[1], -wsc(r), r['name']))
      for i, r in enumerate(items, 1):
          n = i + 1
          ws.append([i, r['name'], f"=MAX(Notes!$B$3,MIN(IF(COUNTIF('All players'!$Q$2:$Q${NN},\">\"&Q{n})<Notes!$B$11,Notes!$B$4,Notes!$B$4-1),ROUND(Q{n},0)))", r['school'], r['sport'], r['pos'], r['gr'], r['gp'], r['score'], r['tot'], round(r['pcg'], 4), round(r['pct_t'], 4), round(r['pct_k'], 4), round(r['pct_s'], 4), f'=(Notes!$B$7*K{n}+Notes!$B$8*L{n}+Notes!$B$9*M{n}+Notes!$B$10*N{n})/(Notes!$B$7+Notes!$B$8+Notes!$B$9+Notes!$B$10)', pctf(n), (f'=(Notes!$B$5+Notes!$B$6*NORMSINV(P{n}))*Notes!$B$13' if r['pos'] == 'DB' else f'=Notes!$B$5+Notes!$B$6*NORMSINV(P{n})' + ('+Notes!$B$12' if r['pos'] == 'QB' else '')), r['status'], r['keys']])
      for row in ws.iter_rows(min_row=2):
          for c in row: c.font = Font(name=AR)
          row[2].font = Font(name=AR, bold=True); row[2].alignment = Alignment(horizontal='center'); row[16].number_format = '0.0'
          mk = MANUAL.get((row[1].value, row[3].value, row[5].value))
          if mk: row[16].value = mk[0]; row[16].fill = PatternFill('solid', start_color='FFFF00'); row[17].value = ' · '.join(x for x in (row[17].value, 'Manual OVR: ' + mk[1]) if x)
      for k, w in enumerate(W, 1): ws.column_dimensions[get_column_letter(k)].width = w
      ws.freeze_panes = 'D2'; ws.auto_filter.ref = f'A1:S{len(items) + 1}'
  order = ['QB', 'RB', 'WR', 'TE', 'DL', 'LB', 'DB', 'K'] if sport == 'Football' else ['PG', 'SG', 'SF', 'PF', 'C']
  mine = [r for r in rows if r['sport'] == sport]
  for pos in order:
      L = [r for r in mine if r['pos'] == pos]
      if L: sheet(pos, L)
  sheet('All players', mine)   # last tab: everyone, best first
  wb.move_sheet('Notes', offset=len(wb.sheetnames) - 1)
  wb.save(os.path.join(OUTD, 'varsity_%s_ovr.xlsx' % sport.lower()))

os.makedirs(OUTD, exist_ok=True)
# Two passes so rows can be listed by final OVR (a formula): build, recalculate with LibreOffice, read each OVR, build again in that order.
import glob, subprocess
from openpyxl import load_workbook
ORDER = {}
RECALC = os.environ.get('RECALC') or (glob.glob(os.path.expanduser('~/.claude/skills/synced/*/xlsx/scripts/recalc.py')) or [''])[0]
for sport in ('Football', 'Basketball'):
    build(sport)
    f = os.path.join(OUTD, 'varsity_%s_ovr.xlsx' % sport.lower())
    if not RECALC: print('no recalc.py: rows stay in weighted-score order'); continue
    subprocess.run([sys.executable, RECALC, f, '900'], check=True, capture_output=True)
    for row in load_workbook(f, data_only=True)['All players'].iter_rows(min_row=2, values_only=True):
        ORDER[(row[1], row[3], row[5], row[8], row[9])] = (row[2] or 0, row[16] or 0)
    build(sport)
