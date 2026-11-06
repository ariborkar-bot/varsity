import numpy as np, wave
SR=44100
rng=np.random.default_rng(7)
def env(n,a=0.002,d=0.2,curve=6):
    t=np.arange(n)/SR;e=np.minimum(1,t/a)*np.exp(-t*curve/max(d,1e-3));return e
def kick(n=int(0.5*SR)):
    t=np.arange(n)/SR;f=45+120*np.exp(-t*28);ph=2*np.pi*np.cumsum(f)/SR
    return np.tanh(2.2*np.sin(ph)*np.exp(-t*5.5))*0.95
def k808(n=int(0.9*SR),note=41.2):
    t=np.arange(n)/SR;f=note*(1+1.5*np.exp(-t*30));ph=2*np.pi*np.cumsum(f)/SR
    return np.tanh(1.6*np.sin(ph))*np.exp(-t*2.2)*0.8
def snare(n=int(0.35*SR)):
    t=np.arange(n)/SR;nz=rng.standard_normal(n);nz=np.convolve(nz,[1,-0.6],'same')
    body=np.sin(2*np.pi*190*t)*np.exp(-t*30)
    return (0.55*nz*np.exp(-t*14)+0.6*body)*0.7
def clap(n=int(0.3*SR)):
    t=np.arange(n)/SR;nz=np.convolve(rng.standard_normal(n),[1,-0.9],'same');e=np.zeros(n)
    for o in [0,0.011,0.022]:
        i=int(o*SR);e[i:]+=np.exp(-(t[:n-i])*60)
    e+=np.exp(-t*12)*0.6
    return nz*e*0.35
def hat(n=int(0.06*SR),open_=False):
    if open_:n=int(0.25*SR)
    t=np.arange(n)/SR;nz=rng.standard_normal(n);hp=np.diff(np.concatenate([[0],nz]))
    return hp*np.exp(-t*(18 if open_ else 90))*0.18
def saw(f,n,det=0.004):
    t=np.arange(n)/SR;o=0
    for d in [-det,0,det]:o=o+2*((t*f*(1+d))%1)-1
    return o/3
def lp(x,a):
    y=np.zeros_like(x);acc=0.0
    # simple one-pole
    from itertools import accumulate
    out=np.empty_like(x);p=0.0
    for i,v in enumerate(x):p+=a*(v-p);out[i]=p
    return out
def place(buf,s,t):
    i=int(t*SR)
    if i>=len(buf):return
    j=min(len(buf),i+len(s));buf[i:j]+=s[:j-i]
def beat(dur,bpm=140,seed=1):
    n=int(dur*SR);L=np.zeros(n);R=np.zeros(n);b=60/bpm;st=b/4
    notes=[41.2,41.2,38.9,46.2]  # E1 E1 D#1 F#1 (minor-ish)
    K=kick();_c=clap();_s=snare();S=np.zeros(max(len(_c),len(_s)));S[:len(_c)]+=_c;S[:len(_s)]+=_s*0.5;H=hat();HO=hat(open_=True)
    bars=int(dur/(4*b))+1
    for bar in range(bars):
        t0=bar*4*b;root=notes[bar%4]
        # half-time trap: kick on 1 and the "and of 2"/variations, clap on 3
        for k in [0,1.75,2.5] if bar%2==0 else [0,0.75,2.5,3.25]:
            place(L,K,t0+k*b);place(R,K,t0+k*b)
        place(L,k808(note=root),t0);place(R,k808(note=root),t0)
        place(L,k808(int(0.5*SR),root),t0+2.5*b);place(R,k808(int(0.5*SR),root),t0+2.5*b)
        place(L,S,t0+2*b);place(R,S*0.9,t0+2*b)
        for i in range(16):
            tt=t0+i*st
            if bar%4==3 and i>=12:  # hat roll
                for r in range(3):place(L if r%2 else R,H*0.8,tt+r*st/3)
            else:
                place(L if i%2 else R,H*(1 if i%4==2 else 0.7),tt)
        if bar%2==1:place(R,HO,t0+3.5*b)
    # dark pluck arp
    arp=[0,3,7,10,12,10,7,3];base=164.8
    for i in range(int(dur/(st*2))):
        tt=i*st*2;bar=int(tt/(4*b));semi=arp[i%8]+[0,0,-1,2][bar%4]
        f=base*2**(semi/12);m=int(0.22*SR);t=np.arange(m)/SR
        tone=(np.sin(2*np.pi*f*t)+0.35*np.sin(2*np.pi*2*f*t)+0.15*np.sign(np.sin(2*np.pi*f*t)))*np.exp(-t*14)*0.11
        place(L,tone*0.9,tt);place(R,tone*0.6,tt+0.012)
    # pad
    for bar in range(bars):
        t0=bar*4*b;root=82.4*2**([0,0,-1,2][bar%4]/12);m=int(4*b*SR)
        tt=np.arange(m)/SR;pad=sum(np.sin(2*np.pi*root*r*tt+r) for r in [1,1.5,2,3])*0.025*np.minimum(1,tt/0.4)*np.minimum(1,(4*b-tt)/0.3)
        place(L,pad,t0);place(R,pad,t0)
    return np.stack([L,R],1)
def whoosh(d=0.45,up=True):
    n=int(d*SR);t=np.arange(n)/SR;nz=rng.standard_normal(n)
    # sweep via varying smoothing
    out=np.empty(n);p=0.0
    for i in range(n):
        a=0.02+0.5*(i/n if up else 1-i/n);p+=a*(nz[i]-p);out[i]=p
    e=np.sin(np.pi*np.minimum(1,t/d))**1.5
    return out*e*0.9
def impact(d=1.0):
    n=int(d*SR);t=np.arange(n)/SR;f=55*np.exp(-t*1.5)+30;ph=2*np.pi*np.cumsum(f)/SR
    boom=np.tanh(2*np.sin(ph))*np.exp(-t*3.5)
    nz=rng.standard_normal(n)*np.exp(-t*18)*0.5
    return (boom*0.9+nz)*0.8
def riser(d=1.2):
    n=int(d*SR);t=np.arange(n)/SR;f=200+1800*(t/d)**2;ph=2*np.pi*np.cumsum(f)/SR
    return (np.sin(ph)*0.12+rng.standard_normal(n)*0.08*(t/d))*(t/d)**1.5
def pop():
    n=int(0.08*SR);t=np.arange(n)/SR;return np.sin(2*np.pi*(900-5000*t)*t)*np.exp(-t*60)*0.4
def tick():
    n=int(0.03*SR);t=np.arange(n)/SR;return np.sin(2*np.pi*2400*t)*np.exp(-t*200)*0.25
def make(path,dur,events,bpm=140,music_gain=0.75,fade=1.2,start_drop=0.0):
    m=beat(dur+2,bpm)[:int(dur*SR)]*music_gain
    if start_drop>0:  # filtered/quiet intro until the drop
        i=int(start_drop*SR);m[:i]*=0.35
    sfx=np.zeros_like(m)
    lib={'whoosh':lambda:whoosh(),'whooshd':lambda:whoosh(up=False),'impact':impact,'riser':riser,'pop':pop,'tick':tick}
    for t,kind,g in events:
        s=lib[kind]()*g
        place(sfx[:,0],s,t);place(sfx[:,1],s,t)
    x=m+sfx;n=len(x);f=int(fade*SR);x[n-f:]*=np.linspace(1,0,f)[:,None]
    x=np.tanh(x*1.1)/np.tanh(1.1);x=x/max(1e-6,np.abs(x).max())*0.89
    with wave.open(path,'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((x*32767).astype('<i2').tobytes())
if __name__=='__main__':
    import time;t=time.time();make('/home/claude/mk/audio/test.wav',8,[(0,'impact',1),(2,'whoosh',0.8),(4,'pop',1)]);print('ok',time.time()-t)
