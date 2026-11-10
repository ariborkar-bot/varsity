"""Build varsity_ovr.xlsx: a Madden-style OVR (40-99) for every player in the app.
usage: python3 tools/ovr/make_ovr.py <dir with fb.json + bb.json> <out dir>   (writes varsity_football_ovr.xlsx and varsity_basketball_ovr.xlsx)
fb.json / bb.json = players() dumped from the football / basketball preview (name, school, pos, sub, gr, gp, tot, inj).
Football: per-game fantasy points (the app's pts()), shrunk toward the position mean (k=2 games), percentile among the same
position group. Basketball: per-game fantasy (pt+1.2reb+1.5ast+3stl+3blk-2tov) from 2025-26 MaxPreps, shrunk (k=3 games),
percentile among all players; no stat line = 0.6 x the average (low-confidence estimate). OVR is a bell curve over the percentile:
ROUND(mean + sd * NORMSINV(pct)) clamped to floor..ceiling, all four as editable cells on the Notes sheet (floor 40 per the owner, ceiling 99)."""
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

rows = []   # dict(name, school, sport, pos, gr, gp, score, pct, status)
fb = json.load(open(os.path.join(D, 'fb.json')))
K = 2
grp = {}
for p in fb: grp.setdefault(p['sub'], []).append(p)
for g, L in grp.items():
    mu = sum(p['tot'] for p in L) / max(1, sum(p['gp'] for p in L))
    sc = [(i, (p['tot'] + K * mu) / (p['gp'] + K)) for i, p in enumerate(L)]
    pc = pctiles(sc); S = dict(sc)
    for i, p in enumerate(L):
        rows.append(dict(name=p['name'], school=p['school'], sport='Football', pos=p['sub'], gr=p['gr'], gp=p['gp'], score=round(S[i], 2), pct=pc[i], status='Out' if p['inj'] else ''))
bbapp = json.load(open(os.path.join(D, 'bb.json')))
stats = {}
for t in mb.load_real():
    for r in t['rows']:
        if r['st'] and r['gp']:
            pt, rb, a, st, bk, tov, _ = r['st']
            stats[(t['name'], r['n'])] = (r['gp'], pt + 1.2 * rb + 1.5 * a + 3 * st + 3 * bk - 2 * tov)
KB = 3
have = [stats[(p['school'], p['name'])] for p in bbapp if (p['school'], p['name']) in stats]
mu = sum(g * f for g, f in have) / sum(g for g, f in have)
sc = []
for i, p in enumerate(bbapp):
    s = stats.get((p['school'], p['name']))
    sc.append((i, (s[0] * s[1] + KB * mu) / (s[0] + KB) if s else .6 * mu))
pc = pctiles(sc); S = dict(sc)
nostat = 0
for i, p in enumerate(bbapp):
    s = stats.get((p['school'], p['name'])); nostat += 0 if s else 1
    rows.append(dict(name=p['name'], school=p['school'], sport='Basketball', pos=p['pos'], gr=p['gr'], gp=s[0] if s else 0, score=round(S[i], 2), pct=pc[i], status=''))
print('football', len(fb), 'basketball', len(bbapp), 'bb without stat line', nostat)

def build(sport):
  wb = Workbook(); nt = wb.active; nt.title = 'Notes'
  AR = 'Arial'
  hdr = Font(name=AR, bold=True, color='FFFFFF'); fill = PatternFill('solid', fgColor='1B2A4A')
  nt['A1'] = 'Varsity %s OVR sheet' % sport; nt['A1'].font = Font(name=AR, bold=True, size=14)
  nt['A3'] = 'Floor (lowest OVR)'; nt['B3'] = 40
  nt['A4'] = 'Ceiling (highest OVR)'; nt['B4'] = 99
  nt['A5'] = 'Mean (the average player)'; nt['B5'] = 64
  nt['A6'] = 'Spread (standard deviation)'; nt['B6'] = 12
  for r in (3, 4, 5, 6): nt.cell(r, 2).font = Font(name=AR, color='0000FF'); nt.cell(r, 2).fill = PatternFill('solid', fgColor='FFFF00'); nt.cell(r, 1).font = Font(name=AR)
  allnotes = ['OVR = Mean + Spread x (how many standard deviations the player is above or below average, from his percentile), rounded and kept between Floor and Ceiling, so most players land in the 50s-70s, 90+ is rare and nobody is below 40. Blue/yellow cells are inputs: change them and every OVR recalculates.',
   'Percentile = where the player ranks among his peers (0 = worst, 1 = best) on the Rating score column.',
   'Football: Rating score = fantasy points per game from MaxPreps box scores (the app scoring), shrunk toward the position average (2 games of average added) so one big game does not make a star. Peers = same position (QB, RB, WR, TE, DL, LB, DB, K).',
   'Basketball: Rating score = points + 1.2 rebounds + 1.5 assists + 3 steals + 3 blocks - 2 turnovers per game from 2025-26 MaxPreps, shrunk (3 games of average added). Peers = every basketball player. Players with no 2025-26 stat line (%d of %d) get 0.6 x the average, so they sit below the middle (low confidence).' % (nostat, len(bbapp)),
   'Games = games with stats behind the rating (football 2026, basketball 2025-26). Few games = low confidence.',
   'Status Out = listed as out in the app this week. Basketball grades are 2026-27 (moved up one year); 0 = unknown.',
   'Source: MaxPreps box scores and season stats already in the app (stats.js, tools/data/bb_2526_players.txt). Built by tools/ovr/make_ovr.py.']
  yr = '2026 season' if sport == 'Football' else '2025-26 season (the latest basketball stats; 2026-27 has not started)'
  notes = [allnotes[0], allnotes[1], allnotes[2 if sport == 'Football' else 3], 'Ratings use only this season (%s), per game, never career or season totals, so a player is not rated higher just for playing more games.' % yr] + allnotes[4:]
  for i, t in enumerate(notes): c = nt.cell(8 + i, 1, t); c.font = Font(name=AR); c.alignment = Alignment(wrap_text=True, vertical='top'); nt.merge_cells(start_row=8 + i, start_column=1, end_row=8 + i, end_column=6); nt.row_dimensions[8 + i].height = 48
  nt.column_dimensions['A'].width = 40; [nt.column_dimensions[c].__setattr__('width', 14) for c in 'BCDEF']
  H = ['#', 'Name', 'School', 'Sport', 'Pos', 'Grade', 'Games', 'Rating score', 'Peer percentile', 'OVR', 'Status']
  W = [6, 24, 26, 11, 7, 7, 8, 13, 15, 8, 9]
  def sheet(title, items):
      ws = wb.create_sheet(title); ws.append(H)
      for c in ws[1]: c.font = hdr; c.fill = fill; c.alignment = Alignment(horizontal='center')
      items = sorted(items, key=lambda r: (-r['pct'], r['name']))
      for i, r in enumerate(items, 1):
          n = i + 1
          ws.append([i, r['name'], r['school'], r['sport'], r['pos'], r['gr'], r['gp'], r['score'], round(r['pct'], 4), f'=MAX(Notes!$B$3,MIN(Notes!$B$4,ROUND(Notes!$B$5+Notes!$B$6*NORMSINV(I{n}),0)))', r['status']])
      for row in ws.iter_rows(min_row=2):
          for c in row: c.font = Font(name=AR)
          row[9].font = Font(name=AR, bold=True)
      for k, w in enumerate(W, 1): ws.column_dimensions[get_column_letter(k)].width = w
      ws.freeze_panes = 'C2'; ws.auto_filter.ref = f'A1:K{len(items) + 1}'
  sheet('Players', [r for r in rows if r['sport'] == sport])
  wb.move_sheet('Notes', offset=1)
  wb.save(os.path.join(OUTD, 'varsity_%s_ovr.xlsx' % sport.lower()))

os.makedirs(OUTD, exist_ok=True)
build('Football'); build('Basketball')
