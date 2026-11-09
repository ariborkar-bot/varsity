"""Week 12 update (Nov 8, 2026): MaxPreps added Week 12 box scores after the first pull (Foothills Christian, Mission Bay,
Classical Academy, and a corrected Mater Dei Catholic). Same rules as merge.py, but only week 12 and only the lines in
data/g12_lines.txt (school label|career id|box name|23 numbers). Run:
   python3 merge_w12.py          -> dry run
   python3 merge_w12.py write    -> writes window.MAXPREPS in stats.js
Then run apply_tfl.py data/tfl_w12.txt write (tackles for loss and pass breakups are not part of the 23 numbers, and this
merge resets them for the players it touches), then tools/make_basketball.py."""
import json,re,sys,unicodedata,datetime
from collections import defaultdict,Counter
import os
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..')+'/'
s=open(ROOT+'stats.js').read()
i=s.index('window.MAXPREPS=')+len('window.MAXPREPS=');j=s.index('\n',i)
D=json.loads(s[i:j].rstrip().rstrip(';'));P=D['players']
G={}
for ln in open(os.path.dirname(os.path.abspath(__file__))+'/data/g12_lines.txt'):
    ln=ln.rstrip('\n')
    if not ln:continue
    lab,car,nm,arr=ln.split('|');g=G.setdefault(lab,{'d':'11-6-2026','t':[{'l':lab,'p':[]}]})
    g['t'][0]['p'].append(['%s|%s'%(re.sub(r'[^a-z0-9]+','-',nm.lower()).strip('-'),car),nm,[float(x) if '.' in x else int(x) for x in arr.split(',')]])
R=json.load(open(''+os.path.dirname(os.path.abspath(__file__))+'/data/rosters.json'))    # {career:[pos,grade]}
def slug(n):n=unicodedata.normalize('NFKD',n).encode('ascii','ignore').decode().lower();return re.sub(r'[^a-z0-9]+','-',n).strip('-')
schools=set(x['s'] for x in P)
def week(d):m,dd,y=map(int,d.split('-'));return (datetime.date(y,m,dd)-datetime.date(2026,8,17)).days//7+1
# team label -> school
lab=Counter()
for g in G.values():
    for t in g.get('t',[]):lab[re.sub(r'\s*\([^)]*\)\s*$','',t['l'])]+=1
unmatched=sorted((n,c) for n,c in lab.items() if n not in schools)
# new season data
new=defaultdict(lambda:defaultdict(lambda:[0]*23))   # (school,slug,career)->week->arr
names={};slugs={}
covered=defaultdict(set)  # school->weeks with a box score
for g in G.values():
    if not g.get('d') or g.get('nostats'):continue
    w=week(g['d'])
    if w!=12:continue
    for t in g['t']:
        sc=re.sub(r'\s*\([^)]*\)\s*$','',t['l'])
        if sc not in schools:continue
        if t['p']:covered[sc].add(w)
        for k,nm,a in t['p']:
            sl,car=k.split('|');sl=slug(sl.replace('-',' '));key=(sc,car);names.setdefault(key,nm);slugs.setdefault(key,sl)
            acc=new[key][w]
            for ix,v in enumerate(a):acc[ix]+=v
print('unmatched labels (not in app):',[x for x in unmatched][:40])
print('app schools without box scores:',sorted(schools-set(covered)))
OFF=list(range(0,9))+[15];DEF=list(range(9,15));KICK=list(range(16,23))
PTS=[.04,4,-2,.1,6,1,.1,6,-2,1,3,5,3,2,6,6,1,-1,3,-1,0,1,0]
def pts(a):return sum(a[i]*PTS[i] for i in range(min(len(a),23)))
def part(a,cols):b=[0]*23
def pick(a,cols):
    b=[0]*23
    for c in cols:
        if c<len(a):b[c]=a[c]
    return b
def trim(b):
    b=list(b)
    while b and not b[-1]:b.pop()
    if not b:return None
    b=[int(x) if float(x).is_integer() else x for x in b]
    return b+[0]*(15-len(b)) if len(b)<15 else b
# index existing
by=defaultdict(list);byid={}
for x in P:
    byid[x['id']]=x
    by[(x['s'],slug(x['n']))].append(x)
stats=Counter();changes=[];removed=[]
def setweeks(x,wk,cols,sc):
    """replace weeks covered by box scores for this entry"""
    old=x['w'];res={}
    for w,a in old.items():
        if int(w) not in covered[sc]:res[w]=a
    for w,a in wk.items():
        b=trim(pick(a,cols))
        if b:res[str(w)]=b
    for w in old:
        if int(w) in covered[sc] and w not in res and any(old[w]):removed.append((x['n'],sc,w,old[w]))
    for w in res:
        if w not in old:changes.append(('add',x['n'],sc,w))
        elif res[w]!=old[w]:changes.append(('chg',x['n'],sc,w,old[w],res[w]))
    x['w']=dict(sorted(res.items(),key=lambda t:int(t[0])))
GR={'Fr.':1,'So.':2,'Jr.':3,'Sr.':4}
def posof(car,season):
    r=R.get(car);ps=[p.strip().upper() for p in (r[2] if r else '').split(',') if p.strip()]
    for p in ps:
        if p in('QB','RB','WR','TE'):return p,p
        if p in('FB',):return 'RB','RB'
        if p in('DL','DE','DT','NT','NG'):return 'DEF','DL'
        if p in('LB','ILB','OLB','MLB'):return 'DEF','LB'
        if p in('CB','S','SS','FS','DB'):return 'DEF','DB'
        if p in('K','P'):return 'K','K'
    t=[sum(a[i] for a in season.values()) for i in range(23)]
    if t[0]>max(t[3],t[6]):return 'QB','QB'
    if t[3]>=t[6] and t[3]>0:return 'RB','RB'
    if t[6]>0 or t[5]>0:return 'WR','WR'
    if t[10]>=1:return 'DEF','DL'
    if t[11]>0:return 'DEF','DB'
    return 'DEF','LB'
added=[];amb=[]
for (sc,car),wk in new.items():
    sl=slugs[(sc,car)]
    tot=[sum(a[i] for a in wk.values()) for i in range(23)]
    off=any(tot[i] for i in OFF);de=any(tot[i] for i in DEF);kick=any(tot[i] for i in KICK)
    r0=R.get(car);ex=[byid[k] for k in (car,car+'o',car+'d') if k in byid] or (by.get((sc,slug(r0[0])),[]) if r0 else []) or by.get((sc,sl),[])
    ex=[x for x in ex if x['p']!='K']
    r=R.get(car);g=GR.get(r[1]) if r else None
    nm=r[0] if r else names[(sc,car)]
    if ex:
        stats['matched']+=1
        o=[x for x in ex if x['id'].endswith('o') and x.get('tw')];d=[x for x in ex if x['id'].endswith('d') and x.get('tw')]
        single=[x for x in ex if not x.get('tw')]
        if len(o)==1 and len(d)==1 and not single:setweeks(o[0],wk,OFF,sc);setweeks(d[0],wk,DEF,sc)
        elif len(single)==1 and not o and not d:setweeks(single[0],wk,OFF+DEF,sc)
        else:stats['ambiguous']+=1;amb.append((nm,sc,[x['id'] for x in ex]))
    elif off or de:
        stats['new']+=1
        p,u=posof(car,wk)
        po=sum(pts(pick(a,OFF)) for a in wk.values());pd=sum(pts(pick(a,DEF)) for a in wk.values())
        base={'n':nm,'s':sc}
        if g:base['g']=g
        if off and de and po>=4 and pd>=4:
            po_,pu_=(p,u) if p!='DEF' and p!='K' else posof('',{w:pick(a,OFF) for w,a in wk.items()})
            if po_=='DEF':po_,pu_='WR','WR'
            pd_,du_=(p,u) if p=='DEF' else ('DEF',posof('',{w:pick(a,DEF) for w,a in wk.items()})[1])
            xo=dict(base,id=car+'o',p=po_,u=pu_,tw=1,w={});xd=dict(base,id=car+'d',p=pd_,u=du_,tw=1,w={})
            setweeks(xo,wk,OFF,sc);setweeks(xd,wk,DEF,sc);P.extend([xo,xd]);added+=[xo,xd]
        else:
            if p=='K':p,u=posof('',wk)
            if de and not off and p!='DEF':p,u='DEF',posof('',wk)[1]
            if off and not de and p=='DEF':p,u=posof('',wk)
            x=dict(base,id=car,p=p,u=u,w={});setweeks(x,wk,OFF+DEF,sc);P.append(x);added.append(x)
    if kick:
        k=byid.get('k'+car)
        if not k:
            k={'id':'k'+car,'n':names[(sc,car)],'s':sc,'p':'K','u':'K','w':{}};P.append(k);byid['k'+car]=k;stats['newK']+=1;added.append(k)
        setweeks(k,wk,KICK,sc)
print(dict(stats),'changes',Counter(c[0] for c in changes),'removed weeks',len(removed))
for c in [c for c in changes if c[1]=='Malachi Gutierrez']:print(c)

import random
print('ambiguous',amb);print('chg samples');[print(c) for c in random.Random(1).sample([c for c in changes if c[0]=='chg'],8)]
print('removed');[print(r) for r in removed[:21]]
print('added players sample',[(x['n'],x['s'],x['p'],x['u'],len(x['w'])) for x in added[:12]])
pad=lambda a:(list(a)+[0]*23)[:23]
real=[c for c in changes if c[0]=='add' or pad(c[4])!=pad(c[5])]
print('real changes',Counter(c[0] for c in real))
# points delta per player (season)
s0=open(ROOT+'stats.js').read()
old={x['id']:x for x in json.loads(s0[i:j].rstrip().rstrip(';'))['players']}
def season(x):return sum(pts(pad(a)) for a in x['w'].values())
deltas=sorted(((season(x)-season(old[x['id']]) if x['id'] in old else season(x)),x['n'],x['s'],len(old[x['id']]['w']) if x['id'] in old else 0,len(x['w'])) for x in P)
print('biggest gains',[ (round(d,1),n,s,a,b) for d,n,s,a,b in deltas[-12:]])
print('biggest drops',[ (round(d,1),n,s,a,b) for d,n,s,a,b in deltas[:8]])
g=[x for x in P if x['n']=='Malachi Gutierrez'][0];print(g)
if 'write' in sys.argv:
    D['players']=P;D['updated']=datetime.date.today().strftime('%b %-d, %Y')
    out=s0[:i]+json.dumps(D,separators=(',',':'),ensure_ascii=False)+';'+s0[j:]
    open(ROOT+'stats.js','w').write(out);print('written')
