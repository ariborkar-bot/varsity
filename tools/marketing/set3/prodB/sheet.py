import sys,os
from PIL import Image
d=sys.argv[1];out=sys.argv[2];fs=sorted(f for f in os.listdir(d) if f.endswith('.jpg'));n=int(sys.argv[3]) if len(sys.argv)>3 else 8
pick=[fs[int(i*(len(fs)-1)/(n-1))] for i in range(n)]
W=270;H=480;S=Image.new('RGB',(W*min(n,8),H*((n+7)//8)))
for i,f in enumerate(pick):S.paste(Image.open(os.path.join(d,f)).resize((W,H)),((i%8)*W,(i//8)*H))
S.save(out,quality=75);print(pick)
