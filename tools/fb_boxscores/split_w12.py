"""Turn the week-12 pull (collect_w12.js) into the files merge.py and apply_tfl.py read.
   python3 split_w12.py Z.b64 ZR.b64   (window.__Z and window.__ZR saved as text)
writes data/games.json (week 12 games), data/rosters.json, data/tfl_w12.txt (TFL/PBU in apply_tfl.py's format).
Then: python3 merge.py --week 12 [write]; python3 apply_tfl.py data/tfl_w12.txt [write]; python3 ../make_basketball.py"""
import base64,gzip,json,re,sys,os,datetime
H=os.path.dirname(os.path.abspath(__file__))
G=json.loads(gzip.decompress(base64.b64decode(open(sys.argv[1]).read().strip())))
R=json.loads(gzip.decompress(base64.b64decode(open(sys.argv[2]).read().strip())))
json.dump(G,open(H+'/data/games.json','w'));json.dump(R,open(H+'/data/rosters.json','w'))
def week(d):m,dd,y=map(int,d.split('-'));return (datetime.date(y,m,dd)-datetime.date(2026,8,17)).days//7+1
def b36(v):
    n=int(v);f=round((v-n)*36);d='0123456789abcdefghijklmnopqrstuvwxyz'
    return d[n]+('.'+d[f] if f else '')
def int36(n):
    d='0123456789abcdefghijklmnopqrstuvwxyz';o=''
    while True:
        o=d[n%36]+o;n//=36
        if not n:return o
labels=[];acc={}
for g in G.values():
    if g.get('nostats') or not g.get('d'):continue
    w=week(g['d'])
    for t in g['t']:
        lb=re.sub(r'\s*\([^)]*\)\s*$','',t['l'])
        if lb not in labels:labels.append(lb)
        ti=labels.index(lb)
        for k,nm,a in t['p']:
            a=a+[0]*(25-len(a))
            if a[23] or a[24]:
                e=acc.setdefault((ti,k.split('|')[1]),{}).setdefault(w,[0,0]);e[0]+=a[23];e[1]+=a[24]
lines=[labels and '|'.join(labels)]
for (ti,car),ws in acc.items():
    lines.append(int36(ti)+'|'+car+'|'+''.join(b36(w)+b36(t)+b36(p) for w,(t,p) in sorted(ws.items())))
open(H+'/data/tfl_w12.txt','w').write('\n'.join(lines)+'\n')
print('games',len(G),'with stats',sum(1 for g in G.values() if not g.get('nostats')),'rosters',len(R),'tfl/pbu players',len(acc))
