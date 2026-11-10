"""Producer B tracks for videos 6-10 (all synthesized). python3 musicB.py v6 v7 ...  -> audio/vN.wav and audio/vN_sfx.wav"""
import sys,os,json,numpy as np
sys.path.insert(0,'/home/claude/mk')
from snd import *
OUT='/home/claude/mk2/prodB/audio/'
def finish(m,name,gains=None,lufs=-11.0,drive=1.3):
    full=m.render(gains or {},master_drive=drive,lufsish=lufs);write_wav(OUT+name+'.wav',full)
    s=Mix(m.n/SR)
    if 'sfx' in m.bus:s.bus['sfx']=m.bus['sfx'].copy()
    else:s.bus['sfx']=np.zeros((2,m.n))
    sx=s.bus['sfx']
    if np.abs(sx).max()>1e-6:sx=sx/np.abs(sx).max()*.7
    write_wav(OUT+name+'_sfx.wav',sx)
    print(name,'peak %.2f rms %.3f len %.2f'%(np.abs(full).max(),np.sqrt(np.mean(full**2)),m.n/SR))
def ks(note,length,bright=.6,decay=.996):
    """Karplus-Strong plucked string (clean electric guitar-ish)"""
    n=T(length);f=hz(note);N=max(2,int(SR/f));buf=lp(noise(N),1500+7000*bright)
    out=np.zeros(n);b=buf.copy()
    for i in range(n):
        j=i%N;out[i]=b[j];b[j]=decay*.5*(b[j]+b[(j+1)%N])
    return lp(out,5000)*.5
def ks_fast(note,length,bright=.6,decay=.996):
    n=T(length);f=hz(note);N=max(2,int(round(SR/f)));buf=lp(noise(N),1500+7000*bright)
    reps=n//N+2;out=np.zeros(reps*N);cur=buf.copy()
    for r in range(reps):
        out[r*N:(r+1)*N]=cur;cur=decay*.5*(cur+np.roll(cur,-1))
    return lp(out[:n],5000)*.5*np.minimum(1,np.linspace(40,0,n))
def tap(length=.07):
    """soft real-sounding screen tap: short damped knock"""
    n=T(length);t=tt(n);return (bp(noise(n),900,3500)*np.exp(-t*90)*.5+np.sin(2*np.pi*190*t)*np.exp(-t*60)*.35)
def guitar_chord(notes,length,drive=4.0,cut=2600):
    n=T(length);x=np.zeros(n)
    for k,nt in enumerate(notes):
        x+=saw_blep(hz(nt)*(1+.002*k),n,rng.random())+.5*saw_blep(hz(nt)*1.004,n,rng.random())
    x=sat(lp(x/len(notes),cut)*1.0,drive);x=lp(peak_eq(x,1600,4,1.2),4200)
    return x*adsr(n,.004,.2,.85,.12)*.35
# ============ V6: deadpan, 90 BPM minimal, A minor ============
def v6():
    L=9.0;m=Mix(L);b=60/90;s16=b/4;kicks=[]
    # 0-3.0 room tone + faint drone
    n=T(3.05);t=tt(n)
    room=lp(noise(n),900)*.02+np.sin(2*np.pi*55*t)*.025*np.minimum(1,t/1.2)
    m.add(room,0,1,bus='amb')
    # 3.0: the hit
    H=3.0
    m.add(k808('A1',length=2.9,drive=2.8,decay=.75,tone=900),H,1.0,bus='bass');m.add(kick(punch=1.3,top=150,bottom=42,length=.6),H,1.0,bus='drums');kicks.append(H)
    m.add(impact(1.6),H,.25,bus='drums')
    # beat 3.0 -> 8.33
    for k in range(8):
        t0=H+k*b
        if t0>=8.33:break
        if k%2==0:m.add(kick(punch=1.1,top=140,bottom=44,length=.45),t0,.85,bus='drums');kicks.append(t0)
        if k%2==1:m.add(rim(),t0,.55,pan=.15,bus='drums')
        if k%4==1:m.add(kick(punch=.9,length=.3),t0+2*s16,.6,bus='drums')
        for j in (1,3):m.add(hat(vel=.45,tone=8000),t0+j*s16,.22,pan=-.3,bus='drums')
    for at in (5.333,5.5):m.add(hat(vel=.7,tone=8000),at,.32,pan=-.3,bus='drums')   # fill the gap before the lock
    for k,(nt,at) in enumerate([('A1',H+4*b),('C2',H+6*b),('G1',H+7*b)]):
        m.add(k808(nt,length=b*1.6,drive=2.4,decay=1.6,tone=800),at,.75,bus='bass')
    m.add(k808('A1',length=.5,drive=2,decay=3,tone=700),8.0,.6,bus='bass')
    # soft taps (Over at 4.4, Lock at 6.0)
    for at,v in ((4.4,.9),(5.2,.7),(5.667,.9)):m.add(tap(),at,v,bus='sfx')   # Over, 25 chip, lock (lock on the beat)
    m.sidechain('bass',kicks[1:],.35,.1)
    m.fx_reverb('drums',.06,.8,6,5000)
    finish(m,'v6',gains={'amb':1.0,'drums':1.0,'bass':1.0,'sfx':.6},lufs=-13,drive=1.1)
# ============ V7: muted house, 120 BPM, A minor, drop 8.0 ============
def v7():
    L=12.4;m=Mix(L);b=.5;bar=2.0;s16=b/4;kicks=[];DROP=8.0
    chords=[['A3','C4','E4','G4'],['F3','A3','C4','E4'],['C4','E4','G4','B4'],['G3','B3','D4','F#4']]
    roots=['A1','F1','C2','G1']
    stab=Mix(L)
    for bi in range(6):
        t0=bi*bar;ci=bi%4
        for k in (2,6,10,14) if bi<4 else (2,5,6,10,13,14):
            for nt in chords[ci]:stab.add(epiano(nt,.35),t0+k*s16,.32,pan=-.15,bus='k')
            for nt in chords[ci][:3]:stab.add(pluck(nt.replace('3','4').replace('4','5') if False else nt,.25,bright=.6,decay=10),t0+k*s16,.12,pan=.2,bus='k')
    sx=stab.render({},master_drive=0,lufsish=-18)[:, :T(DROP)]
    # filter opens 0->8: 400 -> 6000 Hz, pauses 6.0-6.5
    seg1=np.vstack([sweep_lp(c[:T(6.0)],350,2600,2.0,40) for c in sx]);seg2=np.vstack([lp(c[T(6.0):T(6.5)],2600) for c in sx]);seg3=np.vstack([sweep_lp(c[T(6.5):],2600,7000,1.5,24) for c in sx])
    m.add(np.hstack([seg1,seg2,seg3]),0,1.1,bus='keys')
    # four on the floor from 2.0 (muted), shaker
    for k in range(int(DROP/b)):
        t0=k*b
        if t0>=2.0 and not (6.0<=t0<6.5):m.add(lp(kick(punch=1,top=140,bottom=46,length=.35),900 if t0<4 else 2500),t0,.8,bus='drums');kicks.append(t0)
        if t0>=4.0:m.add(shaker(),t0+b/2,.35,pan=.3,bus='drums')
    m.add(riser(1.8,300,5000,tone=False),6.2,.45,bus='fx')
    # drop: full groove 8.0 -> 11.0, warm stabs, bass, claps, open hats
    for bi in range(2):
        t0=DROP+bi*bar;ci=bi
        for k in range(4):m.add(kick(punch=1.15,top=150,bottom=45,length=.4),t0+k*b,.95,bus='drums');kicks.append(t0+k*b)
        for k in (1,3):m.add(clap(),t0+k*b,.6,bus='drums')
        for k in range(4):m.add(hat(open_=True,vel=.8),t0+k*b+b/2,.3,pan=-.25,bus='drums')
        for k in range(16):
            if k%2==1:m.add(hat(vel=.6),t0+k*s16,.2,pan=.25,bus='drums')
        for k in (2,6,10,14):
            for nt in chords[ci]:m.add(epiano(nt,.4),t0+k*s16,.35,bus='keys')
            m.add(supersaw(chords[ci][2],.22,voices=5,cutoff=3500,d=.1,s=.3),t0+k*s16,.25,bus='keys')
        for k in (0,3,6,8,11,14):m.add(k808(roots[ci],length=.22,drive=1.6,decay=8,tone=500,punch=.4),t0+k*s16,.75,bus='bass')
    m.add(impact(1.8),DROP,.35,bus='fx')
    t0=DROP+2*bar
    m.add(kick(punch=1.1),t0,.9,bus='drums');kicks.append(t0)
    m.add(pad(chords[0],2.2,cutoff=1800),t0,.6,bus='keys');m.add(k808('A1',length=1.6,drive=2,decay=1.5),t0,.7,bus='bass')
    m.sidechain('keys',kicks,.55,.16);m.sidechain('bass',kicks,.35,.1)
    m.fx_reverb('keys',.22,1.8,3,6500);m.fx_reverb('drums',.05,.8,6,6000)
    finish(m,'v7',gains={'keys':.9,'drums':1.0,'bass':1.0,'fx':.7},lufs=-11)
# ============ V8: synth-pop 141 BPM, G minor, drop 3.40 ============
def v8():
    b=60/141;bar=4*b;s16=b/4;DROP=8*b;L=24*b+.4;m=Mix(L);kicks=[]
    ch=[['G3','Bb3','D4'],['Eb3','G3','Bb3'],['Bb3','D4','F4'],['F3','A3','C4']];roots=['G1','Eb1','Bb1','F1']
    # before: thin plucks + muted kick
    for bi in range(2):
        t0=bi*bar;ci=bi*2%4
        for k in range(16):
            if k%2==0:m.add(pluck(ch[ci][(k//2)%3].replace('3','5').replace('4','5'),.2,bright=.3,decay=12),t0+k*s16,.22,pan=(-.3 if k%4 else .3),bus='keys')
        for k in range(4):m.add(lp(kick(punch=.8,length=.25),600),t0+k*b,.5,bus='drums')
    m.add(riser(bar*.9,400,6000,tone=False),bar+.1,.35,bus='fx')
    # drop at 3.40: wide supersaws, claps, sub; 3 bars to the end card at 8.51
    for bi in range(3):
        t0=DROP+bi*bar;ci=bi%4
        for nt in ch[ci]:
            m.add(supersaw(nt.replace('3','4').replace('4','4'),bar*.98,voices=7,detune=.25,cutoff=5200,d=.3,s=.75,r=.08),t0,.28,bus='keys')
        for k in (0,3,6,8,11,14):
            m.add(supersaw(ch[ci][k%3].replace('3','5').replace('4','5'),s16*1.4,voices=5,cutoff=6500,d=.06,s=.3,r=.04),t0+k*s16,.18,pan=(.3 if k%2 else -.3),bus='lead')
        for k in range(4):m.add(kick(punch=1.2,top=170,bottom=46,length=.35),t0+k*b,.95,bus='drums');kicks.append(t0+k*b)
        for k in (1,3):m.add(clap(),t0+k*b,.7,bus='drums');m.add(snare(tone=200,crack=.8),t0+k*b,.25,bus='drums')
        for k in range(8):m.add(hat(vel=.7 if k%2 else .5),t0+k*b/2,.3,pan=.25,bus='drums')
        m.add(k808(roots[ci],length=bar*.9,drive=2.2,decay=1.0,tone=900),t0,.8,bus='bass')
    m.add(impact(1.6),DROP,.4,bus='fx')
    t0=DROP+3*bar
    if t0<L:[m.add(supersaw(nt,1.9,cutoff=3200,d=.8,s=.7,r=.6),t0,.6,bus='pad') for nt in ('G3','Bb3','D4','G4')];m.add(k808('G1',length=1.0,drive=2,decay=2),t0,.7,bus='bass');m.add(kick(punch=1.2),t0,.9,bus='drums')
    m.sidechain('keys',kicks,.6,.15);m.sidechain('lead',kicks,.4,.1);m.sidechain('bass',kicks,.3,.08)
    m.fx_reverb('keys',.25,1.6,3,7000);m.fx_reverb('lead',.2,1.2,4,8000)
    finish(m,'v8',gains={'keys':.9,'lead':.8,'drums':1.0,'bass':1.0,'fx':.7},lufs=-10.5)
# ============ V9: pop-rock 154 BPM, E minor, drop 9.35 ============
def v9():
    b=60/154;bar=4*b;e8=b/2;L=10*bar+.3;m=Mix(L);kicks=[];DROP=6*bar
    prog=[('E2',['E3','G3','B3']),('C2',['C3','E3','G3']),('G2',['G3','B3','D4']),('D2',['D3','F#3','A3'])]
    riff=['E5','G5','B5','A5']
    for bi in range(10):
        t0=bi*bar;r,chd=prog[bi%4];full=bi>=6;endc=bi>=9
        stop=(bi==5)
        if endc:
            m.add(guitar_chord(['E3','B3','E4','G4'],bar,drive=3),t0,.8,bus='gtr');m.add(kick(punch=1.2),t0,1,bus='drums');m.add(snare(crack=1.2),t0,.0,bus='drums')
            m.add(hat(open_=True,vel=1.0,length=1.0),t0,.4,bus='drums');m.add(bassdrum(41,1.2),t0,.6,bus='bass');continue
        # bass 8ths
        for k in range(8):
            if stop and k>=6:break
            m.add(lp(saw_blep(hz(r),T(e8*.9))*adsr(T(e8*.9),.003,.05,.8,.03),900)*.5,t0+k*e8,.55 if not full else .9,bus='bass')
        # drums
        for k in range(4):
            if stop and k==3:break
            m.add(kick(punch=1.1,top=150,bottom=50,length=.3),t0+k*b if k in (0,2) else t0+k*b+e8,.9 if k in(0,2) else .6,bus='drums');kicks.append(t0+k*b)
            if k in (1,3):m.add(snare(tone=200,crack=1.0,body=.7),t0+k*b,.7,bus='drums')
        nh=16 if full else 8
        for k in range(nh):
            tk=t0+k*bar/nh
            if stop and tk>=t0+3*b:break
            m.add(hat(vel=.6+.25*(k%2==0)),tk,.3,pan=.3,bus='drums')
        # rhythm guitar chugs (palm-muted) + riff on beat 1
        for k in range(8):
            if stop and k>=6:break
            m.add(guitar_chord([chd[0],chd[2]],e8*.7,drive=4,cut=1800 if not full else 3200),t0+k*e8,.22 if not full else .5,pan=-.35,bus='gtr')
            if full:m.add(guitar_chord(chd,e8*.9,drive=5,cut=3400),t0+k*e8+.01,.4,pan=.4,bus='gtr')
        m.add(brass(riff[bi%4],b*.9,cutoff=3000),t0,.3 if not full else .5,pan=.25,bus='lead');m.add(brass(riff[(bi+1)%4],b*.45,cutoff=2600),t0+b*1.5,.3,pan=.25,bus='lead')
        if full and bi in (6,8):m.add(hat(open_=True,vel=1.0,length=.9),t0,.45,pan=-.2,bus='drums')
    m.add(impact(1.2),DROP,.3,bus='fx');m.add(tom(90,.3),DROP-b*.5,.5,bus='drums');m.add(tom(70,.3),DROP-b*.25,.5,bus='drums')
    m.sidechain('gtr',kicks,.25,.08);m.fx_reverb('drums',.07,.9,5,6000);m.fx_reverb('lead',.18,1.2,4,6000)
    finish(m,'v9',gains={'bass':.9,'drums':1.0,'gtr':.9,'lead':.7,'fx':.6},lufs=-10.5)
# ============ V10: alt-rock, 158 half-time feel, D major, band at 12.15 ============
def v10():
    b=60/158;hbar=8*b;L=18.4;m=Mix(L)
    prog=[('D',['D3','A3','D4','F#4','A4','F#4','D4','A3']),('A',['A2','E3','A3','C#4','E4','C#4','A3','E3']),('Bm',['B2','F#3','B3','D4','F#4','D4','B3','F#3']),('G',['G2','D3','G3','B3','D4','B3','G3','D3'])]
    roots={'D':'D2','A':'A1','Bm':'B1','G':'G1'}
    chords={'D':['D3','A3','D4','F#4'],'A':['A2','E3','A3','C#4'],'Bm':['B2','F#3','B3','D4'],'G':['G2','D3','G3','B3']}
    END=15.2
    for bi in range(6):
        t0=bi*hbar;nm,arp=prog[bi%4]
        if t0>=END:break
        # clean arpeggio 8ths (KS)
        for k in range(8):
            m.add(ks_fast(arp[k],b*3,bright=.55,decay=.9965),t0+k*b,.55,pan=(-.25 if k%2 else .25),bus='clean')
        if t0>=6.1-.01 and t0<12.1:  # floor tom pulse
            for k in range(0,8,2):m.add(tom(75,.5,drive=1.1),t0+k*b,.5,bus='drums')
            m.add(lp(saw_blep(hz(roots[nm]),T(hbar))*adsr(T(hbar),.05,.3,.6,.2),300)*.45,t0,.6,bus='bass')
        if t0>=12.1:  # full band, half-time drums
            m.add(guitar_chord(chords[nm],hbar*.98,drive=5,cut=3000),t0,.75,pan=-.45,bus='dist');m.add(guitar_chord(chords[nm],hbar*.98,drive=5,cut=2800),t0+.012,.75,pan=.45,bus='dist')
            for k in (0,4):m.add(kick(punch=1.2,top=130,bottom=45,length=.5),t0+k*b,1,bus='drums')
            m.add(kick(punch=1,length=.4),t0+2.5*b,.6,bus='drums')
            m.add(snare(tone=180,crack=1.2,body=.9,length=.5),t0+4*b,.85,bus='drums')
            for k in range(8):m.add(hat(open_=k%2==1,vel=.7,length=.25),t0+k*b,.25,pan=.3,bus='drums')
            m.add(hat(open_=True,vel=1,length=1.6,tone=6000),t0,.4,pan=-.3,bus='drums')
            m.add(lp(saw_blep(hz(roots[nm]),T(hbar))*adsr(T(hbar),.01,.3,.8,.2),500)*.5,t0,.7,bus='bass')
    # ringing final chord at END
    m.add(guitar_chord(chords['D'],3.0,drive=4,cut=2800),END,.7,pan=-.4,bus='dist');m.add(guitar_chord(chords['D'],3.0,drive=4,cut=2600),END+.01,.7,pan=.4,bus='dist')
    m.add(kick(punch=1.2),END,1,bus='drums');m.add(hat(open_=True,vel=1,length=2.5,tone=5500),END,.45,bus='drums')
    for k,nt in enumerate(['D3','A3','D4','F#4','A4']):m.add(ks_fast(nt,3.0,bright=.6,decay=.9975),END+k*.03,.4,bus='clean')
    # fade the very end
    for bus in m.bus.values():
        n0=T(END+.6);fade=np.linspace(1,0,bus.shape[1]-n0)**1.5;bus[:,n0:]*=fade
    m.fx_reverb('clean',.35,2.5,2.2,6000);m.fx_reverb('dist',.18,1.6,3,5000);m.fx_reverb('drums',.12,1.5,3,6000)
    finish(m,'v10',gains={'clean':1.0,'dist':.8,'drums':1.0,'bass':.9},lufs=-12)
for a in sys.argv[1:]:globals()[a]()
