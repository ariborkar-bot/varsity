import sys
from PIL import Image
d,a,b,st,out=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),sys.argv[5]
idx=list(range(a,b,st));cols=8;w,h=200,355
S=Image.new('RGB',(cols*w,((len(idx)+cols-1)//cols)*(h+20)),'white')
from PIL import ImageDraw
D=ImageDraw.Draw(S)
for k,i in enumerate(idx):
    im=Image.open(f'{d}/f{i:04d}.jpg').resize((w,h));x,y=(k%cols)*w,(k//cols)*(h+20);S.paste(im,(x,y+20));D.text((x+4,y+4),str(i),fill='black')
S.save(out,quality=80)
