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
rows = []   # dict(name, school, sport, pos, gr, gp, score, pct, status)
fb = json.load(open(os.path.join(D, 'fb.json')))
K = 2
grp = {}
for p in fb: grp.setdefault(p['sub'], []).append(p)
for g, L in grp.items():
    mu = sum(p['tot'] for p in L) / max(1, sum(p['gp'] for p in L))
    sc = [(i, (p['tot'] + K * mu) / (p['gp'] + K)) for i, p in enumerate(L)]
    pc = pctiles(sc); S = dict(sc); pt = pctiles([(i, p['tot']) for i, p in enumerate(L)])
    ks = FBKEY.get(g, FBKEY['DEF']); kr = keyrank(L, [[p['st'].get(k, 0) for k in ks] for p in L])
    for i, p in enumerate(L):
        rows.append(dict(name=p['name'], school=p['school'], sport='Football', pos=p['sub'], gr=p['gr'], gp=p['gp'], score=round(S[i], 2), tot=round(p['tot'], 1), pcg=pc[i], pct_t=pt[i], pct_k=kr[i], keys=' · '.join('%s %s' % (round(p['st'].get(k, 0)), FBLAB[k]) for k in ks), status='Out' if p['inj'] else ''))
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
    rows.append(dict(name=p['name'], school=p['school'], sport='Basketball', pos=p['pos'], gr=p['gr'], gp=s[0] if s else 0, score=round(S[i], 2), tot=round(TV[i], 1), pcg=pc[i], pct_t=pt[i], pct_k=bbk[i][0], keys=bbk[i][1], status=''))
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
  nt['A7'] = 'Weight: points per game'; nt['B7'] = 0.4
  nt['A8'] = 'Weight: season total points'; nt['B8'] = 0.3
  nt['A9'] = 'Weight: rank in his position\'s key stats'; nt['B9'] = 0.3
  for r in (3, 4, 5, 6, 7, 8, 9): nt.cell(r, 2).font = Font(name=AR, color='0000FF'); nt.cell(r, 2).fill = PatternFill('solid', fgColor='FFFF00'); nt.cell(r, 1).font = Font(name=AR)
  allnotes = ['OVR = Mean + Spread x (how many standard deviations the player is above or below average, from his percentile), rounded and kept between Floor and Ceiling, so most players land in the 60s-80s, 90+ is rare and nobody is below 45. Blue/yellow cells are inputs: change them and every OVR recalculates.',
   'Three percentiles (0 = worst, 1 = best among his peers): (1) fantasy points per game, (2) total fantasy points this season (rewards playing more and scoring more) and (3) his rank in the stats that matter at his position, the average percentile of the Position stats columns. Weighted score = the three percentiles combined with the yellow weights (40%/30%/30% by default, they do not have to add to 1). Because averaging squeezes everyone toward the middle, the weighted scores are re-ranked among his peers (Combined percentile) and OVR comes from that, so the best player at a position is near the ceiling and the worst at the floor (45). Key stats: QB pass yd, pass TD, rush yd; RB rush yd, rush TD, rec yd; WR/TE rec yd, rec, rec TD; DL sack, TFL, tkl; LB tkl, TFL, sack; DB tkl, INT, PBU; DEF tkl, TFL, sack, INT; K FG, PAT; basketball PG ast, pts, stl; SG pts, 3pm, stl; SF pts, reb, stl; PF reb, pts, blk; C reb, blk, pts (season totals).',
   'Football: Pts per game = fantasy points per game from MaxPreps box scores (the app scoring), shrunk toward the position average (2 games of average added) so one big game does not make a star. Peers = same position (QB, RB, WR, TE, DL, LB, DB, K).',
   'Basketball: Pts per game = points + 1.2 rebounds + 1.5 assists + 3 steals + 3 blocks - 2 turnovers per game from 2025-26 MaxPreps, shrunk (3 games of average added). Peers = every basketball player. Players with no 2025-26 stat line (%d of %d) get 0.6 x the average, so they sit below the middle (low confidence).' % (nostat, len(bbapp)),
   'Games = games with stats behind the rating (football 2026, basketball 2025-26). Few games = low confidence.',
   'One tab per position (best OVR first, # = rank within the position); the last tab lists everyone. DEF = defensive players MaxPreps does not split into DL/LB/DB. Status Out = listed as out in the app this week. Basketball grades are 2026-27 (moved up one year); 0 = unknown.',
   'Source: MaxPreps box scores and season stats already in the app (stats.js, tools/data/bb_2526_players.txt). Built by tools/ovr/make_ovr.py.']
  yr = '2026 season' if sport == 'Football' else '2025-26 season (the latest basketball stats; 2026-27 has not started)'
  notes = [allnotes[0], allnotes[1], allnotes[2 if sport == 'Football' else 3], 'Ratings use only this season (%s). Season total fantasy pts = fantasy points per game x games (basketball totals use the 2025-26 averages).' % yr] + allnotes[4:]
  for i, t in enumerate(notes): c = nt.cell(11 + i, 1, t); c.font = Font(name=AR); c.alignment = Alignment(wrap_text=True, vertical='top'); nt.merge_cells(start_row=11 + i, start_column=1, end_row=11 + i, end_column=6); nt.row_dimensions[11 + i].height = 48
  nt.column_dimensions['A'].width = 40; [nt.column_dimensions[c].__setattr__('width', 14) for c in 'BCDEF']
  H = ['#', 'Name', 'School', 'Sport', 'Pos', 'Grade', 'Games', 'Fantasy pts per game (adj.)', 'Season total fantasy pts', 'Per-game percentile', 'Total percentile', 'Position-stats percentile', 'Weighted score', 'Combined percentile', 'OVR', 'Status', 'Position stats (season totals)']
  W = [6, 24, 26, 11, 7, 7, 8, 16, 16, 14, 13, 16, 12, 14, 8, 9, 42]
  NN = len([r for r in rows if r['sport'] == sport]) + 1   # last data row of the All players tab
  def pctf(n):
      # where the weighted score ranks among his peers (football: same position; basketball: all players), ties split; read from the All players tab
      A = "'All players'!"
      if sport == 'Football':
          return (f'=(COUNTIFS({A}$E$2:$E${NN},E{n},{A}$M$2:$M${NN},"<"&M{n})+0.5*COUNTIFS({A}$E$2:$E${NN},E{n},{A}$M$2:$M${NN},M{n}))/COUNTIFS({A}$E$2:$E${NN},E{n})')
      return f'=(COUNTIF({A}$M$2:$M${NN},"<"&M{n})+0.5*COUNTIF({A}$M$2:$M${NN},M{n}))/COUNT({A}$M$2:$M${NN})'
  def sheet(title, items):
      ws = wb.create_sheet(title); ws.append(H)
      for c in ws[1]: c.font = hdr; c.fill = fill; c.alignment = Alignment(horizontal='center')
      items = sorted(items, key=lambda r: (-(.4 * r['pcg'] + .3 * r['pct_t'] + .3 * r['pct_k']), r['name']))
      for i, r in enumerate(items, 1):
          n = i + 1
          ws.append([i, r['name'], r['school'], r['sport'], r['pos'], r['gr'], r['gp'], r['score'], r['tot'], round(r['pcg'], 4), round(r['pct_t'], 4), round(r['pct_k'], 4), f'=(Notes!$B$7*J{n}+Notes!$B$8*K{n}+Notes!$B$9*L{n})/(Notes!$B$7+Notes!$B$8+Notes!$B$9)', pctf(n), f'=MAX(Notes!$B$3,MIN(Notes!$B$4,ROUND(Notes!$B$5+Notes!$B$6*NORMSINV(N{n}),0)))', r['status'], r['keys']])
      for row in ws.iter_rows(min_row=2):
          for c in row: c.font = Font(name=AR)
          row[14].font = Font(name=AR, bold=True)
      for k, w in enumerate(W, 1): ws.column_dimensions[get_column_letter(k)].width = w
      ws.freeze_panes = 'C2'; ws.auto_filter.ref = f'A1:Q{len(items) + 1}'
  order = ['QB', 'RB', 'WR', 'TE', 'DL', 'LB', 'DB', 'DEF', 'K'] if sport == 'Football' else ['PG', 'SG', 'SF', 'PF', 'C']
  mine = [r for r in rows if r['sport'] == sport]
  for pos in order:
      L = [r for r in mine if r['pos'] == pos]
      if L: sheet(pos, L)
  sheet('All players', mine)   # last tab: everyone, best first
  wb.move_sheet('Notes', offset=len(wb.sheetnames) - 1)
  wb.save(os.path.join(OUTD, 'varsity_%s_ovr.xlsx' % sport.lower()))

os.makedirs(OUTD, exist_ok=True)
build('Football'); build('Basketball')
