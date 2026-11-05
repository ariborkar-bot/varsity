#!/usr/bin/env python3
"""Builds basketball.html from index.html.

The football app is the source of truth. This script copies it, swaps in basketball
positions, scoring, lineups, schedule and the Simulate court, and bakes in the real 2025-26
San Diego Section rosters and season stats (tools/data/bb_2526_players.txt, from MaxPreps) plus a placeholder schedule.

Run:  python3 tools/make_basketball.py            (writes basketball.html next to index.html)
"""
import datetime, json, math, os, random, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'index.html')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'basketball.html')

SHOW_LAST_YEAR = False   # True: weeks 1-4 carry last season's (2025-26) per-game averages. False: every player starts the season at 0.0
PRIOR = 4 if SHOW_LAST_YEAR else 0   # pseudo-weeks before the first real 2026-27 week
START = datetime.date(2026, 11, 9)   # Monday of the week of the first 2026-27 game
GAMES_FILE = os.path.join(ROOT, 'tools', 'data', 'bb_2627_games.txt')

DATA = os.path.join(ROOT, 'tools', 'data', 'bb_2526_players.txt')
POS5 = ['PG', 'SG', 'SF', 'PF', 'C']


def clean_name(n):
    """tidy MaxPreps names: drop nicknames, fix ALL CAPS / lower case, fix a stray capital"""
    n = re.sub(r'\s*[\"\u201c][^\"\u201d]*[\"\u201d]\s*', ' ', n)
    n = re.sub(r'\([^)]*\)', '', n)
    n = n.replace('Runnar', 'Runnar').replace('MigueL', 'Miguel')
    out = []
    for w in n.split():
        if (w.isupper() and len(w) > 2) or w.islower():
            w = '-'.join(x[:1].upper() + x[1:].lower() for x in w.split('-'))
        out.append(w)
    return ' '.join(out).strip()


def load_real():
    """tools/data/bb_2526_players.txt: one '#slug|School|rows' line per team, then one player per line:
    name,grade(1-4, 0=unknown),position,GP,PPG,RPG,APG,SPG,BPG,TPG,3PM per game   (stat fields are missing when MaxPreps has none)"""
    teams, cur = [], None
    for ln in open(DATA, encoding='utf-8').read().split('\n'):
        if not ln.strip():
            continue
        if ln.startswith('#'):
            slug, name, _ = ln[1:].split('|')
            cur = dict(slug=slug, name=name, rows=[])
            teams.append(cur)
            continue
        f = ln.split(',')
        nm = clean_name(f[0])
        if not nm or re.match(r'^(null )?Player( #?\w+)?$', nm):
            continue
        row = dict(n=nm, g=int(f[1] or 0), pos=f[2] if len(f) > 2 else '', gp=0, st=None)
        if len(f) >= 11:
            row['gp'] = int(float(f[3]))
            row['st'] = [float(x) for x in f[4:11]]          # pts reb ast stl blk tov tpm
        if any(r['n'] == nm for r in cur['rows']):
            continue
        cur['rows'].append(row)
    return teams


def assign_positions(rows):
    """MaxPreps lists G / F / W or nothing for many teams. Map to PG SG SF PF C, using the player's own stats where there are some."""
    n_un = 0
    for r in rows:
        if r['pos'] in POS5:
            r['p'] = r['pos']
    rest = [r for r in rows if r['pos'] not in POS5]
    G = sorted([r for r in rest if r['pos'] == 'G'], key=lambda r: -((r['st'] or [0, 0, 0])[2] * 3 + (r['st'] or [0])[0] * .1))
    F = sorted([r for r in rest if r['pos'] == 'F'], key=lambda r: -((r['st'] or [0, 0])[1]))
    for i, r in enumerate(G):
        r['p'] = 'PG' if i < max(1, round(len(G) * .4)) else 'SG'
    for i, r in enumerate(F):
        r['p'] = 'PF' if i < max(1, round(len(F) * .5)) else 'SF'
    for r in rest:
        if r['pos'] == 'W':
            r['p'] = 'SF'
    blank = [r for r in rest if r['pos'] not in ('G', 'F', 'W')]
    cyc = ['SG', 'SF', 'PG', 'PF', 'C']
    for r in blank:
        st = r['st']
        if st and r['gp'] >= 3 and (st[1] or st[2]):
            pts, reb, ast, stl, blk, tov, tpm = st
            r['p'] = 'PG' if (ast >= 2.5 and reb < 5) else 'C' if reb >= 7 else 'PF' if reb >= 5 else 'SG' if tpm >= .8 else 'SF'
        else:
            r['p'] = cyc[n_un % 5]
            n_un += 1
    return rows


def load_games():
    """tools/data/bb_2627_games.txt: the real 2026-27 schedule from MaxPreps. First line NAMES:a|b|c, then one game per line
    'MMDD HHMM home away' where home/away are an index into NAMES or ~Name for a school outside the list.
    A played game ends with the final score, home first: 'MMDD HHMM home away 64-58' (tools/add_scores.py writes these)."""
    lines = open(GAMES_FILE, encoding='utf-8').read().split('\n')
    names = lines[0][6:].split('|')
    nm = lambda t: t[1:] if t.startswith('~') else names[int(t)]
    out, seen = [], {}
    for ln in lines[1:]:
        if not ln.strip():
            continue
        sc = re.search(r' (\d{1,3})-(\d{1,3})$', ln)
        hs = as_ = None
        if sc:
            hs, as_ = int(sc.group(1)), int(sc.group(2))
            ln = ln[:sc.start()]
        md, hm, rest = ln.split(' ', 2)
        if rest.startswith('~'):                       # a school outside the list is the home team: '~Name 12'
            h, a = rest.rsplit(' ', 1)
        else:                                          # '12 34' or '12 ~Name'
            h, a = rest.split(' ', 1)
        h, a = nm(h), nm(a)
        if h == a:
            continue
        mo, dy = int(md[:2]), int(md[2:])
        d = datetime.date(2026 if mo >= 7 else 2027, mo, dy)
        key = (d, frozenset((h, a)))
        if key in seen:                                # the same game listed twice: keep the copy that has a score
            if hs is not None and seen[key]['hs'] is None:
                seen[key].update(h=h, a=a, hs=hs, **{'as': as_})
            continue
        w = PRIOR + 1 + (d - START).days // 7
        seen[key] = dict(w=w, d=d.isoformat(), h=h, a=a, hs=hs, **{'as': as_})
        out.append(seen[key])
    out.sort(key=lambda g: (g['d'], g['h']))
    return out


def build_data():
    r = random.Random(2026)
    real = load_real()
    TEAMS = sorted(t['name'] for t in real)

    # team strength comes from the real scoring: the sum of every listed player's points per game
    ppg = {}
    for t in real:
        ppg[t['name']] = sum(x['st'][0] for x in t['rows'] if x['st'])
    live = [v for v in ppg.values() if v > 0]
    mean = sum(live) / len(live)
    rating = {n: (max(-14, min(14, (v - mean) * .45)) if v > 0 else 0) for n, v in ppg.items()}

    # seniors (grade 4 in 2025-26) graduate before the 2026-27 season, so they are left out. Team strength above still
    # counts them: it is last season's real scoring, the best signal there is for the preseason odds.
    for t in real:
        t['rows'] = [x for x in t['rows'] if x['g'] != 4]

    games = load_games()

    players, pid = [], 3000
    for t in real:
        assign_positions(t['rows'])
        for x in t['rows']:
            pid += 1
            w = {}
            if SHOW_LAST_YEAR and x['st'] and x['gp'] > 0:
                # MaxPreps only has season averages for most teams: every finished week carries the per-game average,
                # and the number of weeks follows games played so a player with 3 games counts for less than one with 30.
                nw = min(PRIOR, max(1, round(x['gp'] / 7)))
                line = [x['st'][0], x['st'][1], x['st'][2], x['st'][3], x['st'][4], x['st'][5], x['st'][6]]
                for wk in range(1, nw + 1):
                    w[str(wk)] = line
            players.append({'id': str(pid), 'n': x['n'], 's': t['name'], 'g': x['g'], 'p': x['p'], 'u': x['p'], 'w': w})
    # hidden preseason order: last season's fantasy points under the current scoring, weighted by games played.
    # It never shows as a stat; it only decides who sits at the top while everyone is at 0.0.
    rank = {}
    for pl, x in [(pl, x) for pl, x in zip(players, [x for t in real for x in t['rows']])]:
        if x['st'] and x['gp'] > 0:
            ppg_, reb, ast, stl, blk, tov, tpm = x['st']
            per = ppg_ + 1.2 * reb + 1.5 * ast + 3 * stl + 3 * blk - 2 * tov
            rank['mp' + pl['id']] = round(per * min(4, max(1, round(x['gp'] / 7))), 1)
    mp = {'through': '2025-26 season', 'games': 0, 'updated': 'MaxPreps 2025-26 season averages', 'players': players}
    seeds = sorted([n for n in TEAMS if ppg[n] > 0], key=lambda t: -rating[t])[:8]
    prior = {n: round(rating[n], 1) for n in TEAMS if rating[n]}
    mp['rank'] = rank
    return mp, games, seeds, TEAMS, prior


GAMES_JS = """<script>
/* Real 2026-27 San Diego Section boys basketball schedule (MaxPreps). Final scores are added by tools/add_scores.py as games are played.
   Week %(first)d is the week of %(start)s (weeks before it, if any, carry last season's averages). */
(function(){
  var G=%(games)s, P=%(prior)d, W=%(weeks)d, st=new Date(%(sy)d,%(sm)d,%(sd)d), now=new Date();
  var wk=Math.floor((new Date(now.getFullYear(),now.getMonth(),now.getDate())-st)/604800000);
  window.BB_CUR=Math.max(P+1,Math.min(W,P+1+wk));
  window.BB_PRIOR=%(prior_ratings)s;
  window.BB_RANK=%(rank)s; window.BB_TOP10=%(top10)s;
  window.VARSITY_GAMES={games:G,brackets:[],bracketName:'CIF San Diego Section playoffs'};
})();
</script>"""


# ----------------------------------------------------------------------------------------------------------------

def line_replace(s, prefix, new, count=1):
    """replace the whole line that starts with `prefix`"""
    out, n = [], 0
    for ln in s.split('\n'):
        if ln.startswith(prefix):
            out.append(new)
            n += 1
        else:
            out.append(ln)
    assert n == count, (prefix, n)
    return '\n'.join(out)


def between(s, start, end, new, keep_end=True):
    i = s.index(start)
    j = s.index(end, i + len(start))
    return s[:i] + new + (s[j:] if keep_end else s[j + len(end):])


def rep(s, a, b, count=1):
    assert s.count(a) == count, (a[:80], s.count(a))
    return s.replace(a, b)


def gameify(s):
    """Basketball has no one-game-a-week rhythm, so the visible word "week" becomes "game".
    Only display wording is touched: identifiers such as weeks, .week and set-week stay as they are."""
    R = [
        (r"\bBye week\b", "No game"),
        (r"every game by week", "every game in date order"),
        (r"\bWk\b", "Game"),
        (r"\bwk (?=\$\{|'\s*\+)", "game "),
        (r"just this week(?:’|')s game", "just this game"),
        (r"\bweek-by-week\b", "game-by-game"),
        (r"\bweekly (scores|matchups)\b", r"game \1"),
        (r"\bWeek\b", "Game"),
        (r"\bweek(?=\s+\$\{|\s*'\s*\+)", "game"),
        (r"\b((?i:this|next|each|every|that|the|a|per|last|in|from|until|for|of|by|up until|into|current)|Best|Projected|Current) week\b", r"\1 game"),
        (r"\bweek(?=[’'](?:s)\b)", "game"),
        (r"\b(finished|Finished|past|later|recent|Stat) weeks\b", lambda m: m.group(1) + " games"),
    ]
    for pat, rp in R:
        s = re.sub(pat, rp, s)
    return s

def transform(s, mp, games, seeds, teams, prior):
    # --- identity ---------------------------------------------------------------------------------------------
    s = rep(s, '<title>Varsity</title>', '<title>Varsity Basketball</title>')
    s = rep(s, '<h1>Varsity</h1><p>High school fantasy football</p>', '<h1>Varsity</h1><p>High school fantasy basketball</p>')
    s = rep(s, 'I play high school football: add my school and position', 'I play high school basketball: add my school and position')
    s = rep(s, 'Classic fantasy football.', 'Classic fantasy basketball.')
    s = rep(s, 'Play high school football?', 'Play high school basketball?')
    s = rep(s, '<a class="sport-opt on" href="index.html', '<a class="sport-opt" href="index.html')
    s = rep(s, '<a class="sport-opt" href="basketball.html', '<a class="sport-opt on" href="basketball.html')

    # --- data: baked-in placeholder players and games ------------------------------------------------------------
    mp = dict(mp)
    rank = mp.pop('rank', {})
    top10 = [k for k, _ in sorted(rank.items(), key=lambda kv: -kv[1])[:10]]
    s = line_replace(s, 'window.MAXPREPS=', 'window.MAXPREPS=' + json.dumps(mp, separators=(',', ':')) + ';')
    weeks = max(g['w'] for g in games)
    g2 = [dict(w=g['w'], d=g['d'], h=g['h'], a=g['a'], hs=g['hs'], **{'as': g['as']}) for g in games]
    s = rep(s, '<script src="games.js" onerror="void 0"></script>',
            GAMES_JS % dict(games=json.dumps(g2, separators=(',', ':')), prior=PRIOR, first=PRIOR + 1, weeks=weeks,
                            start=START.isoformat(), sy=START.year, sm=START.month - 1, sd=START.day,
                            prior_ratings=json.dumps(prior, separators=(',', ':')), rank=json.dumps(rank, separators=(',', ':')), top10=json.dumps(top10)))
    s = rep(s, " The top 4 seeds in the 12-team divisions (II, III, IV) have a first-round bye.", " This bracket is a projection from last season's scoring until the real brackets are posted.")
    s = rep(s, 'const WEEKS=12;', 'const WEEKS=%d;' % weeks)
    # preseason: nobody has played, so every player counts as one game of 0.0 (lists, pools and cards stay full).
    # This switches itself off as soon as any real stat line exists.
    s = rep(s, "function agg(p,scope){\n  const g=scoped(p,scope);\n",
            "let _pk=-1,_pv=true;\nfunction PRE(){if(_pk!==_rev){_pk=_rev;_pv=!players().some(p=>p.games.some(Boolean))}return _pv}\n"
            "function agg(p,scope){\n  const g=scoped(p,scope);\n  if(!g.length&&!p.sample&&PRE())return{n:1,s:sum([]),v:0,unv:false,ver:false};\n")
    s = rep(s, ".sort((a,b)=>b.a.v-a.a.v).slice(0,16)", ".sort((a,b)=>b.a.v-a.a.v||((window.BB_RANK||{})[b.p.key]||0)-((window.BB_RANK||{})[a.p.key]||0)).slice(0,16)")
    s = re.sub(r"\$\{((?:x\.)?a)\.n\} \$\{\1\.n===1\?'game':'games'\}", lambda m: "${PRE()?0:%s.n} ${!PRE()&&%s.n===1?'game':'games'}" % (m.group(1), m.group(1)), s)
    s = rep(s, '<span class="lbl">Games</span><b>${info.a.n}</b>', '<span class="lbl">Games</span><b>${PRE()?0:info.a.n}</b>')
    s = rep(s, 'Average over your ${info.a.n} approved ${info.a.n===1?', 'Average over your ${PRE()?0:info.a.n} approved ${!PRE()&&info.a.n===1?')
    s = rep(s, "const isT10=p=>{if(!p||!p.key)return false;", "const isT10=p=>{if(!p||!p.key)return false;if(PRE())return (window.BB_TOP10||[]).includes(p.key);")
    s = rep(s, ".filter(x=>x.a.n>0).sort((x,y)=>metric(y.a)-metric(x.a));", ".filter(x=>x.a.n>0).sort((x,y)=>metric(y.a)-metric(x.a)||((window.BB_RANK||{})[y.p.key]||0)-((window.BB_RANK||{})[x.p.key]||0)||x.p.name.localeCompare(y.p.name));")
    s = rep(s, "if(fin.length<20){_rg={r:{},H:0,s:12};return _rg}",
            "if(fin.length<20){_rg=window.BB_PRIOR?{r:window.BB_PRIOR,H:3,s:12}:{r:{},H:0,s:12};return _rg}")
    s = rep(s, "const PO_DATES={r1:'2026-11-06',r2:'2026-11-13',r3:'2026-11-20',r4:'2026-11-27'};",
            "const PO_DATES={r1:'2027-02-19',r2:'2027-02-23',r3:'2027-02-26',r4:'2027-03-01'};")
    s = rep(s, "x.n==='Amaree Maye'", "x.n==='nobody'")

    # --- positions, stats and scoring -------------------------------------------------------------------------------
    s = line_replace(s, 'const FILTERS=', "const FILTERS=['ALL','PG','SG','SF','PF','C'];")
    s = line_replace(s, 'const posMatch=', "const posMatch=(p,f)=>f==='ALL'||p.pos===f;")
    s = line_replace(s, 'const PTS=', "const PTS={pts:1,reb:1.2,ast:1.5,stl:3,blk:3,tov:-2,tpm:0};")
    s = line_replace(s, 'const LABEL=', "const LABEL={pts:'Points',reb:'Rebounds',ast:'Assists',stl:'Steals',blk:'Blocks',tov:'Turnovers',tpm:'3-pointers made'};")
    s = line_replace(s, 'const FIELDS=', "const FIELDS=Object.fromEntries(['PG','SG','SF','PF','C'].map(p=>[p,['pts','reb','ast','stl','blk','tov','tpm']]));")
    s = line_replace(s, 'const POSITIONS=', "const POSITIONS=['PG','SG','SF','PF','C'];")
    s = between(s, 'const POS_ALL=[', 'const posOptions=',
                "const POS_ALL=[['PG','Point guard'],['SG','Shooting guard'],['SF','Small forward'],['PF','Power forward'],['C','Center']];\n"
                "const POS_MAP={PG:'PG',SG:'SG',SF:'SF',PF:'PF',C:'C'};\n")
    s = between(s, 'function line(pos,s){', '\nconst SD_SCHOOLS',
                "function line(pos,s){return `${s.pts} pts · ${s.reb} reb · ${s.ast} ast`}\n")
    s = between(s, 'const RAW=[', '\nfunction gen', 'const RAW=[];')
    s = rep(s, "const avg=tg?tp/tg:21;", "const avg=tg?tp/tg:62;")
    s = rep(s, 'LAM=12,CAP=21', 'LAM=12,CAP=30')
    s = rep(s, "'<span class=\"vt mp\">Verified</span>'", "'<span class=\"vt mp\">Season avg</span>'")
    s = line_replace(s, 'const SD_SCHOOLS=', 'const SD_SCHOOLS=' + json.dumps(teams) + '.sort((a,b)=>a.localeCompare(b));')
    s = between(s, 'function projLine(p){', '\nfunction projTag',
                "function projLine(p){\n  const j=proj(p);if(!j.n)return 'No games yet';\n  if(j.info&&j.info.bye)return 'No game this week';\n"
                "  const s=j.stat;return `${s.pts.toFixed(1)} pts · ${s.reb.toFixed(1)} reb · ${s.ast.toFixed(1)} ast`;\n}")
    s = between(s, 'function tickLine(p,a){', '\nfunction updateTicker',
                "function tickLine(p,a){const x=a.s||{},n=v=>Math.round(v||0).toLocaleString();\n"
                "  return `${n(x.pts)} pts · ${n(x.reb)} reb · ${n(x.ast)} ast`}")
    s = rep(s, "const out=['QB','RB','WR','TE','K','DL','LB','DB'].map(pos=>", "const out=['PG','SG','SF','PF','C'].map(pos=>")
    s = rep(s, "pb(['DL','LB','DB'].includes(pos)?'DEF':pos,pos)", "pb(pos,pos)")
    s = rep(s, "const ORD=['QB','RB','WR','TE','DEF','K'],NAMES={QB:'Quarterbacks',RB:'Running backs',WR:'Receivers',TE:'Tight ends',DEF:'Defense',K:'Kickers'};",
            "const ORD=['PG','SG','SF','PF','C'],NAMES={PG:'Point guards',SG:'Shooting guards',SF:'Small forwards',PF:'Power forwards',C:'Centers'};")
    s = rep(s, "const SHORT={", "const SHORT={pts:'Pts',reb:'Reb',ast:'Ast',stl:'Stl',blk:'Blk',tov:'TO',tpm:'3PM',")

    s = rep(s, "const POSF=['ALL','QB','RB','WR','TE','K','DL','LB','DB'];", "const POSF=['ALL','PG','SG','SF','PF','C'];")
    s = rep(s, "San Diego high school fantasy football", "San Diego high school fantasy basketball")
    s = rep(s, "p.pos='QB';p.posLabel='QB'", "void 0")
    s = rep(s, "Default roster: 1 QB, 2 RB, 2 WR, 1 TE, 1 FLEX, 1 DL, 1 LB, 1 DB, 1 K and 3 bench spots.", "Default roster: 1 PG, 1 SG, 1 SF, 1 PF, 1 C, 1 FLEX and 3 bench spots.")
    s = rep(s, "Over or under on player stats like yards, touchdowns and tackles.", "Over or under on player stats like points, rebounds and assists.")
    s = rep(s, "Build your team opens once players have at least 2 games of stats.", "Build your team opens once the season is underway (it starts Nov 14) and players have at least 2 games of stats.")
    s = rep(s, "Default: 1 QB, 2 RB, 2 WR, 1 TE, 1 FLEX, 1 DL, 1 LB, 1 DB, 1 K and 3 bench spots.", "Default: 1 PG, 1 SG, 1 SF, 1 PF, 1 C, 1 FLEX and 3 bench spots.")
    s = rep(s, "const CAP=70,CAP_FULL=140;", "const CAP=60,CAP_FULL=90;")
    s = rep(s, "const ATS_PAY=1.91,ATS_K=3;", "const ATS_PAY=1.91,ATS_K=2.2;")
    s = rep(s, "L=Math.max(-35,Math.min(35,L));", "L=Math.max(-25,Math.min(25,L));")


    # --- lineups ------------------------------------------------------------------------------------------------
    s = between(s, 'const SLOTS_DRAFT=[', 'const slotOk',
                "const SLOTS_DRAFT=[\n  {k:'PG',label:'PG',elig:['PG']},{k:'SG',label:'SG',elig:['SG']},{k:'SF',label:'SF',elig:['SF']},{k:'PF',label:'PF',elig:['PF']},\n"
                "  {k:'C',label:'C',elig:['C']},{k:'FLEX',label:'FLEX',elig:['PG','SG','SF','PF','C']}];\n")
    s = line_replace(s, 'const ROSTER_DEFAULT=', "const ROSTER_DEFAULT={PG:1,SG:1,SF:1,PF:1,C:1,FLEX:1,BN:3};")
    s = line_replace(s, 'const ROSTER_LEGACY=', "const ROSTER_LEGACY={PG:1,SG:1,SF:1,PF:1,C:1,FLEX:0,BN:0};")
    s = line_replace(s, 'const ROSTER_ORDER=', "const ROSTER_ORDER=['PG','SG','SF','PF','C','FLEX','BN'];")
    s = between(s, 'const ROSTER_DEF={', 'const ROSTER_MAX',
                "const ROSTER_DEF={PG:{elig:['PG']},SG:{elig:['SG']},SF:{elig:['SF']},PF:{elig:['PF']},C:{elig:['C']},FLEX:{elig:['PG','SG','SF','PF','C']},\n"
                "  BN:{elig:['PG','SG','SF','PF','C'],bench:true}};\n")
    s = between(s, 'const SLOTS=[', '/* Accepted trades',
                "const SLOTS=SLOTS_DRAFT;\n")
    s = rep(s, "const what=s.bench?'a bench player':s.k==='FLEX'?'a RB, WR or TE':s.k==='DEF'?'a defender':s.k==='K'?'a kicker':s.k==='DL'?'a defensive lineman':s.k==='LB'?'a linebacker':s.k==='DB'?'a defensive back':'a '+s.label;",
            "const what=s.bench?'a bench player':s.k==='FLEX'?'any position':'a '+s.label;")
    s = rep(s, "(s.bench?'bench player':s.k==='FLEX'?'FLEX (RB, WR or TE)':s.k==='DEF'?'defender':s.k==='K'?'kicker':s.k==='DL'?'defensive lineman':s.k==='LB'?'linebacker':s.k==='DB'?'defensive back':s.label)",
            "(s.bench?'bench player':s.k==='FLEX'?'FLEX (any position)':s.label)")
    s = rep(s, "const offS=s=>s.elig.some(e=>['QB','RB','WR','TE'].includes(e)),defS=s=>s.elig.includes('DEF');",
            "const offS=s=>true,defS=s=>false;")
    s = rep(s, "grp('Offense',ST.filter(offS))", "grp('Starters',ST.filter(offS))")
    s = line_replace(s, 'const CURW=', "const CURW=()=>Math.min(WEEKS,Math.max(1,parseInt(S.settings&&S.settings.week,10)||window.BB_CUR||WEEKS));")

    # --- scoring page -------------------------------------------------------------------------------------------
    s = between(s, 'function viewScoring(){', '\n/* ---------- my stats',
                """function viewScoring(){
  const item=(k,label,note)=>`<li><span>${label}${note?`<small>${note}</small>`:''}</span><b class="${PTS[k]<0?'neg':''}">${PTS[k]>0?'+':'−'}${Math.abs(PTS[k])}</b></li>`;
  return `<div class="head"><h2>Scoring</h2><p>Every stat line becomes fantasy points the same way, for every player in the league.</p></div>
  <div class="two">
    <section class="card"><h3>Box score</h3><ul class="rules">
      ${item('pts','Point','3-pointers count as 3 points, with no extra bonus')}${item('reb','Rebound')}${item('ast','Assist')}
      ${item('stl','Steal')}${item('blk','Block')}${item('tov','Turnover')}
    </ul></section>
    <section class="card"><h3>Lineups and matchups</h3>
      <p><b>Snake draft leagues:</b> by default 1 PG, 1 SG, 1 SF, 1 PF, 1 C and 1 FLEX (any position), plus 3 bench spots. Bench players do not count toward your lineup total, but you can swap one into a matching starting spot at any time after the draft. The league owner can change the roster before the draft.</p>
      <p>In a league, you face one other member each week and the higher lineup total wins.</p>
      <p class="muted">Example: 22 points, 8 rebounds, 5 assists, 2 steals, 1 block, 3 turnovers and 2 threes scores 22 + 9.6 + 7.5 + 6 + 3 − 6 = 42.1 points. The threes are already in the 22 points.</p></section>
  </div>`;
}
""")

    # --- brackets: the football brackets name football seeds; basketball starts with none ------------------------------
    T = lambda i: "T(%s,%d)" % (json.dumps(seeds[i - 1]), i)
    s = between(s, 'const PO_DEFS=(()=>{', '\nfunction buildBrackets',
                "const PO_DEFS=(()=>{const T=(n,s)=>({n,s}),W=(r,g)=>({from:[r,g]});return [{div:'Projected Open Division',rounds:["
                "{name:'Quarterfinals',d:PO_DATES.r1,games:[[%s,%s],[%s,%s],[%s,%s],[%s,%s]]},"
                "{name:'Semifinals',d:PO_DATES.r2,games:[[W(0,0),W(0,1)],[W(0,2),W(0,3)]]},"
                "{name:'Championship',d:PO_DATES.r3,games:[[W(1,0),W(1,1)]]}]}]})();" % (T(1), T(8), T(4), T(5), T(2), T(7), T(3), T(6)))

    # --- Simulate: a starting five on one court, 5 respins in all ---------------------------------------------------
    s = between(s, 'const SIM_SLOTS=[', 'const simKey=',
                """const SIM_SLOTS=[
  {k:'PG',label:'PG',elig:['PG']},{k:'SG',label:'SG',elig:['SG']},{k:'SF',label:'SF',elig:['SF']},{k:'PF',label:'PF',elig:['PF']},{k:'C',label:'C',elig:['C']}];
/* spots on the court, as [left %, top %] */
const SIM_POS={C:[50,15],PF:[21,37],SF:[79,37],SG:[27,65],PG:[73,65]};
/* one unit: every respin comes out of the same 5 (left.off) */
const SIM_UNIT=k=>'off';
const SIM_COL={PG:'#E65B28',SG:'#2868E8',SF:'#079B82',PF:'#9655D8',C:'#E0455B',G:'#22A6D9',F:'#E8A317'};
""")
    s = between(s, 'function simBest(){', '\nfunction simStart',
                """function simBest(){
  const seen=new Set(),all=players().filter(p=>p.mp&&agg(p,'season').n>=2).sort((a,b)=>simTot(b)-simTot(a)).filter(p=>{const k=simKey(p);if(seen.has(k))return false;seen.add(k);return true});
  const used=new Set(),list=[];
  for(const sl of SIM_SLOTS){const p=all.find(x=>!used.has(simKey(x))&&sl.elig.includes(x.pos));if(p){used.add(simKey(p));list.push({l:sl.label,p})}}
  return {list,total:list.reduce((t,x)=>t+simTot(x.p),0)};
}
""")
    s = between(s, 'function simField(tab){', '\n/* ---- play a season as a school ---- */', COURT_JS)
    s = rep(s, 'const SIM_SD=22;', 'const SIM_SD=11;')
    s = rep(s, "const tot=Math.max(18,Math.min(84,Math.round(44+8*gauss())));", "const tot=Math.max(80,Math.min(180,Math.round(122+12*gauss())));")
    s = rep(s, 'bonus=Math.max(-8,Math.min(16,z*4.5))', 'bonus=Math.max(-6,Math.min(12,z*3.5))')
    s = rep(s, "left:{off:SIM_RESPINS,def:SIM_RESPINS}", "left:{off:SIM_RESPINS,def:0}")
    s = rep(s, "Draw a full 17-player team, use up to ${SIM_RESPINS} offense and ${SIM_RESPINS} defense respins to swap out players,",
            "Draw a 5-player team, use up to ${SIM_RESPINS} respins to swap out players,")
    s = rep(s, "You get 17 spots: 1 QB, 1 RB, 2 WR, 1 TE and 1 FLEX (RB, WR or TE) on offense, then 4 DL, 3 LB and 4 DB on defense. Everyone is drawn at random from the app, and you get ${SIM_RESPINS} respins for offense and ${SIM_RESPINS} for defense to swap any player for a new one.",
            "You get 5 spots: a starting five of PG, SG, SF, PF and C. Everyone is drawn at random from the app, and you get ${SIM_RESPINS} respins to swap any player for a new one.")
    s = rep(s, "<div><small>Offense respins</small><b>${m.left.off}</b></div><div><small>Defense respins</small><b>${m.left.def}</b></div>",
            "<div><small>Respins</small><b>${m.left.off}</b></div>")
    s = rep(s, "You have ${m.left.off} offense and ${m.left.def} defense ${", "You have ${m.left.off} ${")
    # one court, so no Starters/Bench tabs
    i = s.index('<div class="sim-heads" role="tablist" aria-label="Unit">')
    j = s.index('<div class="sim-board sim-${tab}">', i)
    s = s[:i] + s[j:]
    s = rep(s, "const tab=UI.simTab==='def'?'def':'off',", "const tab='off',")

    # --- Supabase: basketball keeps its own leagues, lineups, picks and settings. Accounts (profiles) are shared. ---------------
    i = s.index('function supaDb(sb){')
    j = s.index('  return{doc,collection:col};', i)
    s = s[:j] + "  const bbp=p=>/^profiles(\\/|$)/.test(p)?p:'bb_'+p;\n  return{doc:p=>doc(bbp(p)),collection:c=>col(bbp(c))};" + s[j + len('  return{doc,collection:col};'):]

    # --- look: hardwood instead of grass ------------------------------------------------------------------------
    k = s.rindex('</style>', 0, s.index('<header class="mast">'))
    s = s[:k] + '</style><style id="bb-theme">' + BB_CSS.replace('__COURT__', COURT_URI) + s[k:]
    return gameify(s)


COURT_JS = r"""function simField(tab){
  const W=400,H=520,F="font-family=\"'Barlow Condensed','Arial Narrow',sans-serif\"";
  const wood=['#c98a45','#c18241'];
  let g=`<defs><radialGradient id="scVig" cx=".5" cy=".42" r=".8"><stop offset=".5" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".55"/></radialGradient>
    <linearGradient id="scLight" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".18"/><stop offset=".5" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>
    <rect width="${W}" height="${H}" fill="${wood[0]}"/>`;
  for(let k=0;k<13;k++)g+=`<rect x="${k*32}" y="0" width="16" height="${H}" fill="${wood[k%2]}"/><rect x="${k*32+16}" y="0" width="16" height="${H}" fill="#b87a3a"/>`;
  const L="#fff6e6",GOLD="#FFC23D";
  /* Varsity-branded floor: navy out-of-bounds frame with gold trim, blue painted lane, gold three-point line, the V gem at the center circle */
  g+=`<path d="M0 0H${W}V${H}H0Z M26 26V${H-26}H374V26Z" fill="#061a4d" fill-rule="evenodd"/><rect x="21" y="21" width="358" height="${H-42}" fill="none" stroke="${GOLD}" stroke-width="2.2" stroke-opacity=".9"/>`;
  if(tab==='off'){
    g+=`<rect x="26" y="26" width="348" height="${H-52}" fill="none" stroke="${L}" stroke-width="3.2"/>`;
    g+=`<path d="M82 26V250H318V26" fill="#1F4FD1" fill-opacity=".78" stroke="${L}" stroke-width="3.2"/>`;
    g+=`<circle cx="200" cy="250" r="62" fill="#0B2A74" fill-opacity=".9" stroke="${GOLD}" stroke-width="3.4"/><image href="logo.png" x="150" y="200" width="100" height="100"/>`;
    g+=`<path d="M50 26V132A150 150 0 0 0 350 132V26" fill="none" stroke="${GOLD}" stroke-width="3.4"/>`;
    g+=`<path d="M170 58h60" stroke="#fff" stroke-width="5" stroke-linecap="round"/><circle cx="200" cy="72" r="11" fill="none" stroke="#ff7a1a" stroke-width="4"/>`;
    g+=`<path d="M160 200h-12M160 168h-12M160 136h-12M240 200h12M240 168h12M240 136h12" stroke="${L}" stroke-width="3"/>`;
    g+=`<text x="200" y="${H-64}" text-anchor="middle" ${F} font-weight="900" font-style="italic" font-size="30" letter-spacing="8" fill="${GOLD}" fill-opacity=".55">VARSITY</text>`;
  }else{
    g+=`<rect x="26" y="26" width="348" height="${H-52}" fill="none" stroke="${L}" stroke-width="3.2"/>`;
    g+=`<rect x="26" y="26" width="348" height="46" fill="#1F4FD1" fill-opacity=".8"/><text x="200" y="58" text-anchor="middle" ${F} font-weight="900" font-style="italic" font-size="26" letter-spacing="9" fill="#fff" fill-opacity=".85">THE BENCH</text>`;
    g+=`<circle cx="200" cy="${H-26}" r="70" fill="#0B2A74" fill-opacity=".9" stroke="${GOLD}" stroke-width="3.4"/><image href="logo.png" x="160" y="${H-82}" width="80" height="80"/>`;
    g+=`<text x="200" y="${H-46}" text-anchor="middle" ${F} font-weight="900" font-style="italic" font-size="30" letter-spacing="8" fill="#fff" fill-opacity=".3">VARSITY</text>`;
  }
  g+=`<rect width="${W}" height="${H}" fill="url(#scLight)"/><rect width="${W}" height="${H}" fill="url(#scVig)"/>`;
  return `<svg class="sb-svg" viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid slice" aria-hidden="true">${g}</svg>`;
}
"""

BB_CSS = r"""
/* basketball: position colors and a hardwood header */
.pos.PG{--c:#E65B28}.pos.SG{--c:#2868E8}.pos.SF{--c:#079B82}.pos.PF{--c:#9655D8}.pos.C{--c:#E0455B}
.sim-board{background:#c98a45!important;border-color:#8b5a25!important}
.mast{background:linear-gradient(90deg,rgba(24,10,0,.62),rgba(24,10,0,.12) 42%,rgba(24,10,0,.12) 62%,rgba(24,10,0,.55)),linear-gradient(180deg,rgba(0,0,0,0) 55%,rgba(20,8,0,.45)),url("__COURT__") center/cover no-repeat!important}
.mast::before,.mast::after,.mast-yards{display:none!important;content:none!important}
.mast .wk,.mast .bell,.sport-sw{background:rgba(26,12,2,.82)!important;border:1px solid rgba(255,236,200,.3)!important}
"""

def _court_uri():
    """One full high-school court (84 x 50 ft, NFHS markings) centred on a long strip of floor. Units are tenths of a foot."""
    import urllib.parse
    L, W = '#fff6e6', 6                      # line colour and stroke width (exaggerated so it reads at banner size)
    floor = ''.join('<rect x="-3580" y="%d" width="8000" height="25" fill="%s"/>' % (-20 + k * 25, '#c98a45' if k % 2 else '#bd7d3c') for k in range(22))
    oob = '<path d="M-3580 -20H4420V520H-3580Z M0 0V500H840V0Z" fill="#6b3f17" fill-opacity=".5" fill-rule="evenodd"/>'
    # left half (baseline at x=0, rim centre at x=53, y=250); mirrored for the right half
    half = (
        '<rect x="0" y="190" width="190" height="120" fill="#1d4fd0" fill-opacity=".5"/>'                      # painted lane (12 ft wide, 19 ft long)
        '<path d="M0 190H190V310H0" fill="none" stroke="%(L)s" stroke-width="%(W)s"/>'                          # lane lines + free-throw line
        '<path d="M190 190A60 60 0 0 1 190 310" fill="#1d4fd0" fill-opacity=".5" stroke="%(L)s" stroke-width="%(W)s"/>'  # free-throw circle, solid half
        '<path d="M190 190A60 60 0 0 0 190 310" fill="none" stroke="%(L)s" stroke-width="%(W)s" stroke-dasharray="11 9"/>'  # dashed half
        '<path d="M0 52.5H53A197.5 197.5 0 0 1 53 447.5H0" fill="none" stroke="%(L)s" stroke-width="%(W)s"/>'    # three-point line, 19 ft 9 in
        '<path d="M40 215V285" stroke="#fff" stroke-width="9" stroke-linecap="round"/>'                          # backboard
        '<path d="M40 250H44" stroke="#ff7a1a" stroke-width="5"/><circle cx="53" cy="250" r="9" fill="none" stroke="#ff7a1a" stroke-width="5"/>'  # rim
        '<path d="M60 180v-10M60 320v10M100 190v-10M100 310v10M140 190v-10M140 310v10" stroke="%(L)s" stroke-width="%(W)s"/>'  # lane hash marks
    ) % {'L': L, 'W': W}
    mid = ('<path d="M420 0V500" stroke="%(L)s" stroke-width="%(W)s"/>'
           '<circle cx="420" cy="250" r="60" fill="#1d4fd0" fill-opacity=".4" stroke="%(L)s" stroke-width="%(W)s"/>') % {'L': L, 'W': W}
    border = '<rect x="0" y="0" width="840" height="500" fill="none" stroke="%s" stroke-width="%d"/>' % (L, W)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="8000" height="540" viewBox="-3580 -20 8000 540" preserveAspectRatio="xMidYMid slice">' + floor + oob + border + half +
           '<g transform="translate(840 0) scale(-1 1)">' + half + '</g>' + mid + '</svg>')
    return 'data:image/svg+xml,' + urllib.parse.quote(svg, safe='')


COURT_URI = _court_uri()


if __name__ == '__main__':
    mp, games, seeds, teams, prior = build_data()
    src = open(SRC, encoding='utf-8').read()
    out = transform(src, mp, games, seeds, teams, prior)
    open(OUT, 'w', encoding='utf-8').write(out)
    print('wrote', OUT, len(out) // 1024, 'KB;', len(mp['players']), 'players,', len(games), 'games')
