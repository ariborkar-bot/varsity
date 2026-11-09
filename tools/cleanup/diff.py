import sys,os,json
from PIL import Image,ImageChops
a,b=sys.argv[1],sys.argv[2];bad=[]
la=json.load(open(f'{a}/log.json'));lb=json.load(open(f'{b}/log.json'))
for f in sorted(os.listdir(a)):
    if not f.endswith('.png'):continue
    if not os.path.exists(f'{b}/{f}'):bad.append((f,'missing'));continue
    A=Image.open(f'{a}/{f}').convert('RGB');B=Image.open(f'{b}/{f}').convert('RGB')
    if A.size!=B.size:bad.append((f,'size',A.size,B.size));continue
    bb=ImageChops.difference(A,B).getbbox()
    if bb:bad.append((f,'diff',bb))
newerr={k:v for k,v in lb.items() if v and v!=la.get(k)}
print('compared',len([f for f in os.listdir(a) if f.endswith('.png')]),'different',len(bad));[print(' ',x) for x in bad[:40]]
print('new errors',json.dumps(newerr)[:800])
