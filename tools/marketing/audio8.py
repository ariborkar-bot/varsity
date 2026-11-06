"""Phonk-style beat for video 8 (140 BPM): filtered cowbell intro under the group chat, full drop when the app opens.
Everything is synthesized here, so there is no licensed music in the video."""
import numpy as np, wave, sys
from scipy.signal import butter, sosfilt
SR=44100;BPM=140;B=60/BPM;S16=B/4
rng=np.random.default_rng(3)
def T(n):return np.arange(n)/SR
def place(buf,s,t,g=1.0):
    i=int(round(t*SR))
    if i>=len(buf) or i<0:return
    j=min(len(buf),i+len(s));buf[i:j]+=s[:j-i]*g
def filt(x,kind,f,order=2):
    sos=butter(order,f,btype=kind,fs=SR,output='sos');return sosfilt(sos,x)
def kick():
    n=int(.45*SR);t=T(n);f=48+150*np.exp(-t*35);ph=2*np.pi*np.cumsum(f)/SR
    return np.tanh(3*np.sin(ph)*np.exp(-t*7))*.9+np.exp(-t*400)*rng.standard_normal(n)*.15
def bass808(n,f0,glide_to=None):
    t=T(n);f=f0*np.ones(n)
    if glide_to:f=f0+(glide_to-f0)*np.clip((t-.12)/.12,0,1)
    ph=2*np.pi*np.cumsum(f)/SR
    return np.tanh(2.6*np.sin(ph))*np.minimum(1,t/.004)*np.exp(-t*1.6)*.75
def snare():
    n=int(.3*SR);t=T(n);nz=filt(rng.standard_normal(n),'high',1500)
    return (nz*np.exp(-t*16)*.6+np.sin(2*np.pi*185*t)*np.exp(-t*28)*.5)*.8
def clap():
    n=int(.28*SR);t=T(n);nz=filt(rng.standard_normal(n),'band',[900,3500]);e=np.zeros(n)
    for o in [0,.009,.019]:i=int(o*SR);e[i:]+=np.exp(-t[:n-i]*70)
    return nz*(e+np.exp(-t*10)*.5)*.55
def hat(open_=False):
    n=int((.22 if open_ else .05)*SR);t=T(n);nz=filt(rng.standard_normal(n),'high',7000)
    return nz*np.exp(-t*(14 if open_ else 110))*.32
def cowbell(f,d=.28):
    n=int(d*SR);t=T(n);sq=lambda fr:np.sign(np.sin(2*np.pi*fr*t))
    x=(sq(f)+sq(f*1.48))*.5;x=filt(x,'band',[f*.9,f*4])
    return x*np.exp(-t*9)*np.minimum(1,t/.002)*.5
def ding():   # iMessage-like receive: two soft bell tones
    n=int(.5*SR);t=T(n)
    a=np.sin(2*np.pi*1318*t)*np.exp(-t*9);b=np.sin(2*np.pi*1760*t)*np.exp(-np.maximum(0,t-.07)*9)*(t>.07)
    return (a+b*.9)*.36
def swoosh():  # sent message
    n=int(.28*SR);t=T(n);nz=rng.standard_normal(n);f=np.linspace(600,3200,n)
    out=np.zeros(n);
    for k in range(4):seg=slice(k*n//4,(k+1)*n//4);out[seg]=filt(nz[seg],'band',[f[seg][0],f[seg][0]*1.6],1)
    return out*np.sin(np.pi*t/t[-1])*.5
def whoosh(d=.42,up=True):
    n=int(d*SR);t=T(n);nz=rng.standard_normal(n);out=np.zeros(n);K=8
    for k in range(K):
        fr=(k+1)/K if up else 1-k/K;seg=slice(k*n//K,(k+1)*n//K);out[seg]=filt(nz[seg],'band',[200+3000*fr,600+6000*fr],1)
    return out*np.sin(np.pi*np.minimum(1,t/d))**1.4*.9
def impact(d=1.1):
    n=int(d*SR);t=T(n);f=60*np.exp(-t*2)+28;ph=2*np.pi*np.cumsum(f)/SR
    return (np.tanh(2.5*np.sin(ph))*np.exp(-t*3)+filt(rng.standard_normal(n),'low',3000)*np.exp(-t*14)*.6)*.85
def revcym(d=1.0):
    n=int(d*SR);t=T(n);nz=filt(rng.standard_normal(n),'high',4000);return nz*(t/d)**3*.5
def tap():
    n=int(.04*SR);t=T(n);return np.sin(2*np.pi*1900*t)*np.exp(-t*180)*.35+filt(rng.standard_normal(n),'high',3000)*np.exp(-t*300)*.2
def coin():   # cha-ching
    n=int(.7*SR);t=T(n);x=np.zeros(n)
    for i,(f,at) in enumerate([(2093,0),(2637,.07),(3136,.14)]):
        k=int(at*SR);tt=T(n-k);x[k:]+=np.sin(2*np.pi*f*tt)*np.exp(-tt*7)*.25
    return x+filt(rng.standard_normal(n),'high',6000)*np.exp(-t*20)*.15
def lock():
    n=int(.12*SR);t=T(n);return (np.sin(2*np.pi*900*t)*np.exp(-t*80)+filt(rng.standard_normal(n),'band',[1500,5000])*np.exp(-t*90)*.6)*.5
def music(dur,drop,brk,end_hit):
    n=int(dur*SR);M=np.zeros(n);I=np.zeros(n)   # M = drum/bass (after drop), I = cowbell+hats (all the way)
    E4,G4,A4,B4,D5,E5=329.6,392.0,440.0,493.9,587.3,659.3
    # classic phonk cowbell riff over 2 bars of 16ths (None = rest)
    riff=[E5,None,E5,None,D5,None,E5,None,B4,None,D5,None,E5,None,None,E5, G4,None,G4,None,A4,None,B4,None,D5,None,B4,None,A4,None,G4,None]
    roots=[41.2,41.2,49.0,36.7]   # E1 E1 G1 D1 per bar
    nb=int(dur/B)+8
    for i in range(nb*4):
        t=i*S16;bar=i//16;s=i%16
        nt=riff[i%32]
        if nt:place(I,cowbell(nt),t,.9 if s%4==0 else .7)
        place(I,hat(),t,.55 if s%2 else .9)
        if True:
            if s in (0,10) or (bar%2 and s==7):place(M,kick(),t)
            if s in (4,12):place(M,clap(),t);place(M,snare(),t,.5)
            if s==0:
                r=roots[bar%4];place(M,bass808(int(1.6*B*SR),r,r*1.5 if bar%4==3 else None),t)
            if s==10:place(M,bass808(int(.9*B*SR),roots[bar%4]),t,.8)
            if bar%4==3 and s>=12:place(M,hat(),t+S16/2,.7)
            if s==14 and bar%2==0:place(M,hat(True),t,.6)
    # intro and break: cowbells/hats low-passed and quieter
    L=I.copy();MM=M.copy()
    for a,b in [(0,drop),(brk,end_hit)]:   # muffled "next room" sound under the chat, opening up a little toward the drop
        i,j=int(a*SR),int(b*SR);ramp=np.linspace(0.0,1.0,j-i)
        L[i:j]=filt(I[i:j],'low',1400)*(1.0+.2*ramp);MM[i:j]=filt(M[i:j],'low',380,4)*(.7+.25*ramp)
    return MM*.85+L*.75
def build(path,dur,drop,brk,end_hit,events):
    mus=music(dur,drop,brk,end_hit)
    sfx=np.zeros(len(mus))
    lib={'ding':ding,'swoosh':swoosh,'whoosh':whoosh,'whooshd':lambda:whoosh(up=False),'impact':impact,'rev':revcym,'tap':tap,'coin':coin,'lock':lock,'kick':kick}
    for t,k,g in events:place(sfx,lib[k](),t,g)
    x=mus+sfx;f=int(.35*SR);x[-f:]*=np.linspace(1,0,f)
    x=np.tanh(x*1.2)/np.tanh(1.2);x=x/np.abs(x).max()*.84
    st=np.stack([x,np.concatenate([[0]*int(.004*SR),x[:-int(.004*SR)]])*.96+x*.04],1)  # tiny stereo width
    with wave.open(path,'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((st*32767).astype('<i2').tobytes())
if __name__=='__main__':
    import json;cfg=json.load(open(sys.argv[1]));build(cfg['out'],cfg['dur'],cfg['drop'],cfg['brk'],cfg['end_hit'],cfg['events']);print('ok')
