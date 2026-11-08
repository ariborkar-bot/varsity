"""Add tackles for loss (index 23) and passes defensed (index 24) to window.MAXPREPS in index.html (v301).

1. Run collect_tfl.js in the browser pane (any maxpreps.com page); when window.__DONE is 1, save window.__TL (team labels, '|' separated)
   as the first line and window.__T as the rest into data/tfl.txt.
2. python3 apply_tfl.py          -> dry run (what matches, what does not)
   python3 apply_tfl.py write    -> writes index.html (then run tools/make_basketball.py)
Players are matched like merge.py: by career id (id, id+'o', id+'d'), then roster name, then box-score name, within the school.
Two-way players get the numbers on their defense entry. Nothing else in a week's line is touched."""
import json,re,sys,unicodedata,os
from collections import defaultdict,Counter
H=os.path.dirname(os.path.abspath(__file__));ROOT=H+'/../../'
s0=open(ROOT+'index.html').read()
i=s0.index('window.MAXPREPS=')+len('window.MAXPREPS=');j=s0.index('\n',i)
D=json.loads(s0[i:j].rstrip().rstrip(';'));P=D['players']
G=json.load(open(H+'/data/games.json'));R=json.load(open(H+'/data/rosters.json'))
def slug(n):n=unicodedata.normalize('NFKD',n).encode('ascii','ignore').decode().lower();return re.sub(r'[^a-z0-9]+','-',n).strip('-')
schools=set(x['s'] for x in P)
names={}
for g in G.values():
    for t in g.get('t',[]):
        for k,nm,a in t['p']:
            sl,car=k.split('|');names.setdefault(car,slug(sl.replace('-',' ')))
byid={x['id']:x for x in P};by=defaultdict(list)
for x in P:by[(x['s'],slug(x['n']))].append(x)
lines=open(H+'/data/tfl.txt').read().split('\n');labels=lines[0].split('|');rows=[l for l in lines[1:] if l]
tot=Counter();unm=Counter();amb=[];hit=Counter();new=defaultdict(dict)
def pick(sc,car):
    ex=[byid[k] for k in (car,car+'o',car+'d') if k in byid]
    if not ex:
        r0=R.get(car);ex=(by.get((sc,slug(r0[0])),[]) if r0 else []) or by.get((sc,names.get(car,'')),[])
    ex=[x for x in ex if x['p']!='K']
    if not ex:return None
    d=[x for x in ex if x['id'].endswith('d') and x.get('tw')]
    if len(ex)==1 and not ex[0].get('tw'):return ex[0]
    if len(d)==1 and len([x for x in ex if x['id'].endswith('o') and x.get('tw')])==1:return d[0]
    return 'amb'
for r in rows:
    ti,car,e=r.split('|');sc=labels[int(ti,36)]
    ws=[(int(e[k],36),int(e[k+1],36),int(e[k+2],36)) for k in range(0,len(e),3)]
    for w,t,p in ws:tot['tfl']+=t;tot['pbu']+=p
    if sc not in schools:unm['outside:'+sc]+=sum(t+p for _,t,p in ws);continue
    x=pick(sc,car)
    if x is None:unm[sc+'|'+car]+=sum(t+p for _,t,p in ws);new[(sc,car)]=ws;continue
    if x=='amb':amb.append((sc,car));continue
    for w,t,p in ws:
        a=list(x['w'].get(str(w),[]));a+=[0]*(25-len(a));a[23]=t;a[24]=p;x['w'][str(w)]=a;hit['tfl']+=t;hit['pbu']+=p
    x['w']=dict(sorted(x['w'].items(),key=lambda t:int(t[0])))
print('collected',dict(tot),'applied',dict(hit))
print('outside the app:',sorted((k,v) for k,v in unm.items() if k.startswith('outside:'))[:30])
print('players not in app:',[(k,v) for k,v in unm.items() if not k.startswith('outside:')][:60])
print('ambiguous',amb)
if 'write' in sys.argv:
    D['players']=P
    open(ROOT+'index.html','w').write(s0[:i]+json.dumps(D,separators=(',',':'),ensure_ascii=False)+';'+s0[j:]);print('written')
