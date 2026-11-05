#!/usr/bin/env python3
"""Builds basketball.html from index.html.

The football app is the source of truth. This script copies it, swaps in basketball
positions, scoring, lineups, schedule and the Simulate court, and bakes in placeholder
players and games (made up, so the layout can be seen working before real box scores exist).

Run:  python3 tools/make_basketball.py            (writes basketball.html next to index.html)
"""
import json, math, os, random, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'index.html')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'basketball.html')

CUR = 7          # the placeholder season is "in week 7": weeks 1-6 are finished, 7-12 are still to play
WEEKS = 12

TEAMS = ["Bishop's", "Cathedral Catholic", "La Jolla Country Day", "Torrey Pines", "Carlsbad", "Mission Hills", "Helix",
         "Lincoln", "Morse", "Oceanside", "Rancho Bernardo", "Santa Fe Christian", "Mater Dei Catholic", "Vista",
         "Grossmont", "El Camino", "Granite Hills", "Hoover", "Madison", "Mira Mesa", "Poway", "Point Loma", "San Marcos",
         "Scripps Ranch", "Steele Canyon", "Valley Center", "Westview", "Eastlake", "Otay Ranch", "Chula Vista",
         "Bonita Vista", "Coronado", "La Costa Canyon", "Ramona", "Escondido", "Fallbrook", "Christian High", "Del Norte",
         "Mount Miguel", "University City"]

FIRST = ["Marcus", "Jalen", "Dante", "Elijah", "Mateo", "Noah", "Isaiah", "Caleb", "Xavier", "Andre", "Tyrese", "Julian",
         "Malik", "Devin", "Aiden", "Ezra", "Omar", "Kai", "Jordan", "Cameron", "Terrell", "Rafael", "Diego", "Jaden",
         "Trey", "Micah", "Landon", "Bryce", "Ryder", "Zion", "Nico", "Anthony", "Darius", "Gabe", "Hunter", "Ibrahim",
         "Jayce", "Kobe", "Leo", "Miles", "Nate", "Owen", "Parker", "Quincy", "Reese", "Sean", "Tobias", "Victor",
         "Wesley", "Yusuf", "Zach", "Brandon", "Colby", "Derek", "Emilio", "Finn", "Grant", "Hayden", "Ivan", "Jace"]
LAST = ["Alvarez", "Brooks", "Coleman", "Dawson", "Escobar", "Foster", "Garcia", "Hughes", "Ibarra", "Jenkins", "Kim",
        "Lopez", "Mitchell", "Nguyen", "Ortega", "Pierce", "Quintero", "Reyes", "Santos", "Tran", "Underwood", "Vega",
        "Walker", "Xiong", "Yamada", "Zimmerman", "Aoki", "Bennett", "Castillo", "Doyle", "Ellis", "Flores", "Grant",
        "Holloway", "Ito", "Jimenez", "Kealoha", "Lindqvist", "Moreno", "Nakamura", "Okafor", "Pruitt", "Ramos",
        "Sandoval", "Tate", "Valdez", "Whitfield", "Yee", "Abbott", "Barrera", "Cruz", "Dixon", "Enriquez", "Fields",
        "Gomez", "Hendrickson", "Ingram", "Jordan", "Knight", "Lacey", "Mendoza", "Nelson", "Orozco", "Park", "Rivera",
        "Soto", "Thomas", "Vaughn", "Washington", "Young", "Zamora"]

POS = ['PG', 'SG', 'SF', 'PF', 'C']
REB = dict(PG=3.2, SG=3.6, SF=5.2, PF=7.6, C=9.4)
AST = dict(PG=5.6, SG=3.0, SF=2.5, PF=1.9, C=1.3)
STL = dict(PG=1.9, SG=1.6, SF=1.3, PF=1.0, C=0.8)
BLK = dict(PG=0.2, SG=0.3, SF=0.6, PF=1.0, C=1.9)
TOV = dict(PG=3.0, SG=2.3, SF=2.0, PF=1.9, C=1.8)
TPR = dict(PG=.13, SG=.14, SF=.10, PF=.05, C=.01)          # three pointers made per point scored
# the nine-man rotation: five starters and four off the bench, with each player's share of the team's points
ROT = [('PG', .25), ('SG', .21), ('SF', .17), ('PF', .13), ('C', .10), ('PG', .05), ('SG', .04), ('SF', .03), ('PF', .02)]


def build_data():
    r = random.Random(2026)

    def pois(lam):
        L, k, p = math.exp(-lam), 0, 1.0
        while True:
            k += 1
            p *= r.random()
            if p <= L:
                return k - 1

    rating = {t: r.gauss(0, 5) for t in TEAMS}
    games, seen = [], set()
    for w in range(1, WEEKS + 1):
        for _ in range(80):
            order = TEAMS[:]
            r.shuffle(order)
            pairs = [(order[i], order[i + 1]) for i in range(0, len(order), 2)]
            if not any(frozenset(p) in seen for p in pairs):
                break
        for h, a in pairs:
            seen.add(frozenset((h, a)))
            if r.random() < .5:
                h, a = a, h
            g = dict(w=w, h=h, a=a, hs=None, **{'as': None}, dow=r.choice([0, 1, 1, 3, 3, 3]))
            if w < CUR:
                m = rating[h] - rating[a] + 3 + r.gauss(0, 10)
                tot = max(90, min(170, r.gauss(122, 12)))
                hs, as_ = round((tot + m) / 2), round((tot - m) / 2)
                if hs == as_:
                    hs += 1
                g['hs'], g['as'] = hs, as_
            games.append(g)

    names_used, players, pid = set(), [], 3000
    for t in TEAMS:
        boost = r.uniform(.8, 1.25)
        roster = []
        for i, (pos, share) in enumerate(ROT):
            while True:
                n = r.choice(FIRST) + ' ' + r.choice(LAST)
                if (n, t) not in names_used:
                    names_used.add((n, t))
                    break
            talent = max(.55, min(1.6, r.lognormvariate(0, .3))) * (boost if i < 2 else 1)
            roster.append(dict(n=n, pos=pos, share=share * talent, g=(r.choice([2, 3, 3, 4, 4]) if i < 5 else r.choice([1, 2, 2, 3]))))
        for p in roster:
            pid += 1
            p['id'] = str(pid)
            p['w'] = {}
        for g in games:
            if g['hs'] is None or t not in (g['h'], g['a']):
                continue
            tp = g['hs'] if g['h'] == t else g['as']
            play = [p for p in roster if r.random() > .05]
            wts = [p['share'] * r.lognormvariate(0, .28) for p in play]
            s = sum(wts)
            pts = [round(tp * x / s) for x in wts]
            pts[pts.index(max(pts))] += tp - sum(pts)
            for p, pt in zip(play, pts):
                sc = (p['share'] / .18) ** .7
                reb = pois(REB[p['pos']] * sc * r.uniform(.7, 1.3))
                ast = pois(AST[p['pos']] * sc * r.uniform(.6, 1.4))
                stl = pois(STL[p['pos']] * sc * .8)
                blk = pois(BLK[p['pos']] * sc * .8)
                tov = pois(TOV[p['pos']] * sc * .8)
                tpm = min(pt // 3, pois(pt * TPR[p['pos']]))
                p['w'][str(g['w'])] = [max(pt, 0), reb, ast, stl, blk, tov, tpm]
        for p in roster:
            players.append({'id': p['id'], 'n': p['n'], 's': t, 'g': p['g'], 'p': p['pos'], 'u': p['pos'], 'w': p['w']})
    done = sum(1 for g in games if g['hs'] is not None)
    mp = {'through': 'Week %d' % (CUR - 1), 'games': done, 'updated': 'Placeholder data', 'players': players}
    seeds = sorted(TEAMS, key=lambda t: -rating[t])[:8]
    return mp, games, seeds


GAMES_JS = """<script>
/* PLACEHOLDER basketball schedule: made-up games between real San Diego Section schools, so the layout can be seen working.
   Dates are set relative to today: weeks 1-%(prev)d are finished, week %(cur)d is next. */
(function(){
  var G=%(games)s, cur=%(cur)d, now=new Date(), pad=function(n){return(n<10?'0':'')+n};
  G.forEach(function(g){var t=new Date(now.getFullYear(),now.getMonth(),now.getDate()+(g.w-cur)*7+2+g.dow);
    g.d=t.getFullYear()+'-'+pad(t.getMonth()+1)+'-'+pad(t.getDate());delete g.dow});
  window.BB_CUR=cur;
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


def transform(s, mp, games, seeds):
    # --- identity ---------------------------------------------------------------------------------------------
    s = rep(s, '<title>Varsity</title>', '<title>Varsity Basketball</title>')
    s = rep(s, '<h1>Varsity</h1><p>High school fantasy football</p>', '<h1>Varsity</h1><p>High school fantasy basketball</p>')
    s = rep(s, 'I play high school football: add my school and position', 'I play high school basketball: add my school and position')
    s = rep(s, 'Classic fantasy football.', 'Classic fantasy basketball.')
    s = rep(s, 'Play high school football?', 'Play high school basketball?')
    s = rep(s, '<a class="sport-opt on" href="index.html', '<a class="sport-opt" href="index.html')
    s = rep(s, '<a class="sport-opt" href="basketball.html', '<a class="sport-opt on" href="basketball.html')

    # --- data: baked-in placeholder players and games ------------------------------------------------------------
    s = line_replace(s, 'window.MAXPREPS=', 'window.MAXPREPS=' + json.dumps(mp, separators=(',', ':')) + ';')
    g2 = [dict(w=g['w'], h=g['h'], a=g['a'], hs=g['hs'], **{'as': g['as']}, dow=g['dow']) for g in games]
    s = rep(s, '<script src="games.js" onerror="void 0"></script>',
            GAMES_JS % dict(games=json.dumps(g2, separators=(',', ':')), cur=CUR, prev=CUR - 1))
    s = rep(s, "x.n==='Amaree Maye'", "x.n==='nobody'")

    # --- positions, stats and scoring -------------------------------------------------------------------------------
    s = line_replace(s, 'const FILTERS=', "const FILTERS=['ALL','PG','SG','SF','PF','C'];")
    s = line_replace(s, 'const posMatch=', "const posMatch=(p,f)=>f==='ALL'||p.pos===f;")
    s = line_replace(s, 'const PTS=', "const PTS={pts:1,reb:1.2,ast:1.5,stl:3,blk:3,tov:-1,tpm:.5};")
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
    s = rep(s, "'<span class=\"vt mp\">Verified</span>'", "'<span class=\"vt un\">Sample</span>'")
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

    s = rep(s, "posOptions(pr.posLabel||pos||'RB')", "posOptions(pr.posLabel||pos||'PG')")
    s = rep(s, "const POSF=['ALL','QB','RB','WR','TE','K','DL','LB','DB'];", "const POSF=['ALL','PG','SG','SF','PF','C'];")
    s = rep(s, "San Diego high school fantasy football", "San Diego high school fantasy basketball")
    s = rep(s, "pos:'RB',agree:false", "pos:'PG',agree:false", 2)
    s = rep(s, "p.pos='QB';p.posLabel='QB'", "void 0")
    s = rep(s, "Default roster: one each of QB, RB, TE, DL, LB, DB and K, plus 2 WR.", "Default roster: one each of PG, SG, SF, PF, C and a FLEX.")
    s = rep(s, "Default: 1 QB, 2 RB, 2 WR, 1 TE, 1 FLEX, 1 DL, 1 LB, 1 DB, 1 K and 3 bench spots.", "Default: 1 PG, 1 SG, 1 SF, 1 PF, 1 C, 1 FLEX and 3 bench spots.")
    s = rep(s, "const CAP=70,CAP_FULL=140;", "const CAP=60,CAP_FULL=90;")
    s = rep(s, "const ATS_PAY=1.91,ATS_K=3;", "const ATS_PAY=1.91,ATS_K=2.2;")
    s = rep(s, "L=Math.max(-35,Math.min(35,L));", "L=Math.max(-25,Math.min(25,L));")

    s = rep(s, "  const sample=!MP&&!S.settings.hideSample;",
            "  b.push('<p class=\"note\"><span class=\"pill pending\">Sample data</span><span>These basketball players and games are made up so you can try the layout. Real box scores come later.</span></p>');\n  const sample=!MP&&!S.settings.hideSample;")

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
      ${item('pts','Point')}${item('tpm','3-pointer made','bonus on top of its 3 points')}${item('reb','Rebound')}${item('ast','Assist')}
      ${item('stl','Steal')}${item('blk','Block')}${item('tov','Turnover')}
    </ul></section>
    <section class="card"><h3>Lineups and matchups</h3>
      <p><b>Snake draft leagues:</b> by default 1 PG, 1 SG, 1 SF, 1 PF, 1 C and 1 FLEX (any position), plus 3 bench spots. Bench players do not count toward your lineup total, but you can swap one into a matching starting spot at any time after the draft. The league owner can change the roster before the draft.</p>
      <p>In a league, you face one other member each week and the higher lineup total wins.</p>
      <p class="muted">Example: 22 points, 8 rebounds, 5 assists, 2 steals, 1 block, 3 turnovers and 2 threes scores 22 + 9.6 + 7.5 + 6 + 3 − 3 + 1 = 46.1 points.</p></section>
  </div>`;
}
""")

    # --- brackets: the football brackets name football seeds; basketball starts with none ------------------------------
    T = lambda i: "T(%s,%d)" % (json.dumps(seeds[i - 1]), i)
    s = between(s, 'const PO_DEFS=(()=>{', '\nfunction buildBrackets',
                "const PO_DEFS=(()=>{const T=(n,s)=>({n,s}),W=(r,g)=>({from:[r,g]});return [{div:'Open Division',rounds:["
                "{name:'Quarterfinals',d:PO_DATES.r1,games:[[%s,%s],[%s,%s],[%s,%s],[%s,%s]]},"
                "{name:'Semifinals',d:PO_DATES.r2,games:[[W(0,0),W(0,1)],[W(0,2),W(0,3)]]},"
                "{name:'Championship',d:PO_DATES.r3,games:[[W(1,0),W(1,1)]]}]}]})();" % (T(1), T(8), T(4), T(5), T(2), T(7), T(3), T(6)))

    # --- Simulate: ten players on a half court ---------------------------------------------------------------------
    s = between(s, 'const SIM_SLOTS=[', 'const simKey=',
                """const SIM_SLOTS=[
  {k:'PG',label:'PG',elig:['PG']},{k:'SG',label:'SG',elig:['SG']},{k:'SF',label:'SF',elig:['SF']},{k:'PF',label:'PF',elig:['PF']},{k:'C',label:'C',elig:['C']},
  {k:'BG1',label:'G',elig:['PG','SG']},{k:'BG2',label:'G',elig:['PG','SG']},{k:'BF1',label:'F',elig:['SF','PF']},{k:'BF2',label:'F',elig:['SF','PF']},{k:'BC',label:'C',elig:['C','PF']}];
/* spots on the court, as [left %, top %]. The starters and the bench each get a court of their own. */
const SIM_POS={C:[50,15],PF:[21,37],SF:[79,37],SG:[27,65],PG:[73,65],BG1:[27,20],BG2:[73,20],BF1:[27,50],BF2:[73,50],BC:[50,80]};
const SIM_UNIT=k=>['PG','SG','SF','PF','C'].includes(k)?'off':'def';
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
    s = rep(s, "Draw a full 17-player team, use up to ${SIM_RESPINS} offense and ${SIM_RESPINS} defense respins to swap out players,",
            "Draw a 10-player team, use up to ${SIM_RESPINS} starter and ${SIM_RESPINS} bench respins to swap out players,")
    s = rep(s, "You get 17 spots: 1 QB, 1 RB, 2 WR, 1 TE and 1 FLEX (RB, WR or TE) on offense, then 4 DL, 3 LB and 4 DB on defense. Everyone is drawn at random from the app, and you get ${SIM_RESPINS} respins for offense and ${SIM_RESPINS} for defense to swap any player for a new one.",
            "You get 10 spots: a starting five of PG, SG, SF, PF and C, then a bench of 2 guards, 2 forwards and a center. Everyone is drawn at random from the app, and you get ${SIM_RESPINS} respins for the starters and ${SIM_RESPINS} for the bench to swap any player for a new one.")
    s = rep(s, "<div><small>Offense respins</small><b>${m.left.off}</b></div><div><small>Defense respins</small><b>${m.left.def}</b></div>",
            "<div><small>Starter respins</small><b>${m.left.off}</b></div><div><small>Bench respins</small><b>${m.left.def}</b></div>")
    s = rep(s, "You have ${m.left.off} offense and ${m.left.def} defense ${", "You have ${m.left.off} starter and ${m.left.def} bench ${")
    s = rep(s, "[['off','Offense'],['def','Defense']]", "[['off','Starters'],['def','Bench']]")

    # --- Supabase: basketball keeps its own leagues, lineups, picks and settings. Accounts (profiles) are shared. ---------------
    i = s.index('function supaDb(sb){')
    j = s.index('  return{doc,collection:col};', i)
    s = s[:j] + "  const bbp=p=>/^profiles(\\/|$)/.test(p)?p:'bb_'+p;\n  return{doc:p=>doc(bbp(p)),collection:c=>col(bbp(c))};" + s[j + len('  return{doc,collection:col};'):]

    # --- look: hardwood instead of grass ------------------------------------------------------------------------
    k = s.rindex('</style>', 0, s.index('<header class="mast">'))
    s = s[:k] + '</style><style id="bb-theme">' + BB_CSS.replace('__COURT__', COURT_URI) + s[k:]
    return s


COURT_JS = r"""function simField(tab){
  const W=400,H=520,F="font-family=\"'Barlow Condensed','Arial Narrow',sans-serif\"";
  const wood=['#c98a45','#c18241'];
  let g=`<defs><radialGradient id="scVig" cx=".5" cy=".42" r=".8"><stop offset=".5" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".55"/></radialGradient>
    <linearGradient id="scLight" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".18"/><stop offset=".5" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>
    <rect width="${W}" height="${H}" fill="${wood[0]}"/>`;
  for(let k=0;k<13;k++)g+=`<rect x="${k*32}" y="0" width="16" height="${H}" fill="${wood[k%2]}"/><rect x="${k*32+16}" y="0" width="16" height="${H}" fill="#b87a3a"/>`;
  const L="#fff6e6";
  if(tab==='off'){
    g+=`<rect x="26" y="26" width="348" height="${H-52}" fill="none" stroke="${L}" stroke-width="3.2"/>`;
    g+=`<path d="M82 26V250H318V26" fill="#1d4fd0" fill-opacity=".38" stroke="${L}" stroke-width="3.2"/>`;
    g+=`<circle cx="200" cy="250" r="62" fill="none" stroke="${L}" stroke-width="3.2" stroke-dasharray="9 7"/><path d="M138 250A62 62 0 0 0 262 250" fill="none" stroke="${L}" stroke-width="3.2"/>`;
    g+=`<path d="M50 26V132A150 150 0 0 0 350 132V26" fill="none" stroke="${L}" stroke-width="3.2"/>`;
    g+=`<path d="M170 58h60" stroke="#fff" stroke-width="5" stroke-linecap="round"/><circle cx="200" cy="72" r="11" fill="none" stroke="#ff7a1a" stroke-width="4"/>`;
    g+=`<path d="M160 200h-12M160 168h-12M160 136h-12M240 200h12M240 168h12M240 136h12" stroke="${L}" stroke-width="3"/>`;
    g+=`<text x="200" y="${H-64}" text-anchor="middle" ${F} font-weight="900" font-style="italic" font-size="30" letter-spacing="8" fill="#fff" fill-opacity=".3">VARSITY</text>`;
  }else{
    g+=`<rect x="26" y="26" width="348" height="${H-52}" fill="none" stroke="${L}" stroke-width="3.2"/>`;
    g+=`<rect x="26" y="26" width="348" height="46" fill="#1d4fd0" fill-opacity=".5"/><text x="200" y="58" text-anchor="middle" ${F} font-weight="900" font-style="italic" font-size="26" letter-spacing="9" fill="#fff" fill-opacity=".85">THE BENCH</text>`;
    g+=`<circle cx="200" cy="${H-26}" r="70" fill="none" stroke="${L}" stroke-width="3.2"/>`;
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
    import urllib.parse
    L = '#fff6e6'
    planks = ''.join('<rect x="%d" y="0" width="40" height="170" fill="%s"/>' % (i * 40, '#c98a45' if i % 2 else '#bd7d3c') for i in range(40))
    half = ('<path d="M0 8H150A92 92 0 0 1 150 162H0" fill="none" stroke="%s" stroke-width="3" opacity=".8"/>'
            '<rect x="0" y="42" width="170" height="86" fill="#1d4fd0" fill-opacity=".28" stroke="%s" stroke-width="3" opacity=".9"/>'
            '<circle cx="170" cy="85" r="30" fill="none" stroke="%s" stroke-width="3" opacity=".8"/>') % (L, L, L)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 170" preserveAspectRatio="xMidYMid slice">' + planks + half +
           '<g transform="translate(1600 0) scale(-1 1)">' + half + '</g>'
           '<path d="M800 0V170" stroke="%s" stroke-width="3" opacity=".85"/><circle cx="800" cy="85" r="46" fill="none" stroke="%s" stroke-width="3" opacity=".85"/></svg>') % (L, L)
    return 'data:image/svg+xml,' + urllib.parse.quote(svg, safe='')


COURT_URI = _court_uri()


if __name__ == '__main__':
    mp, games, seeds = build_data()
    src = open(SRC, encoding='utf-8').read()
    out = transform(src, mp, games, seeds)
    open(OUT, 'w', encoding='utf-8').write(out)
    print('wrote', OUT, len(out) // 1024, 'KB;', len(mp['players']), 'players,', len(games), 'games')
