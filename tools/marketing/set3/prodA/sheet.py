import sys,subprocess,os
from PIL import Image,ImageDraw
v,out=sys.argv[1],sys.argv[2];ts=[float(x) for x in sys.argv[3:]]
ims=[]
for t in ts:
    p=f'/tmp/sh_{t:.2f}.jpg';subprocess.run(['ffmpeg','-y','-v','error','-ss',str(t),'-i',v,'-frames:v','1','-q:v','3',p],check=True)
    im=Image.open(p).resize((324,576));d=ImageDraw.Draw(im);d.rectangle([0,0,70,24],fill='black');d.text((4,4),f'{t:.2f}s',fill='white');ims.append(im)
S=Image.new('RGB',(324*4,576*((len(ims)+3)//4)),'white')
for i,im in enumerate(ims):S.paste(im,((i%4)*324,(i//4)*576))
S.save(out,quality=85);print(out)
