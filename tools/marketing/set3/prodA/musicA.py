"""Producer A: five original synthesized tracks for videos 1-5 (no samples, no licensed music).
python3 musicA.py m1 m2 ... -> audio/mN.wav (music + soft sfx) and audio/mN_sfx.wav (sfx only, for the no-music cut)."""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from snd import *
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio') + '/'
os.makedirs(OUT, exist_ok=True)

def finish(m, name, gains=None, lufs=-12.0, drive=1.2):
    full = m.render(gains or {}, master_drive=drive, lufsish=lufs)
    write_wav(OUT + name + '.wav', full)
    s = Mix(m.n / SR)
    if 'sfx' in m.bus: s.bus['sfx'] = m.bus['sfx'].copy()
    if s.bus and np.abs(s.bus['sfx']).max() > 0:
        x = s.bus['sfx']; x = x / (np.abs(x).max() + 1e-9) * .5
        write_wav(OUT + name + '_sfx.wav', x)
    else:
        write_wav(OUT + name + '_sfx.wav', np.zeros((2, m.n)))
    print(name, 'len %.2f peak %.2f rms %.3f' % (m.n / SR, np.abs(full).max(), np.sqrt(np.mean(full ** 2))))

def vinyl(n):
    """quiet vinyl hiss + sparse crackle"""
    x = lp(hp(noise(n), 1500), 7000) * .02
    idx = rng.integers(0, n, n // 2500)
    for i in idx:
        L = min(60, n - i); x[i:i + L] += rng.standard_normal(L) * np.exp(-np.arange(L) / 8) * .25
    return x

def keytap():
    n = T(.035); t = tt(n)
    return (bp(noise(n), 1800, 6500) * np.exp(-t * 260) * .5 + np.sin(2 * np.pi * 180 * t) * np.exp(-t * 120) * .3)

# ======================= M1: lo-fi, 92 BPM, D minor (comment your school) =======================
def m1():
    bpm = 92; b = 60 / bpm; bar = 4 * b; s16 = b / 4
    L = 19 * b + .5; m = Mix(L)
    prog = [['D3', 'F3', 'A3', 'C4', 'E4'], ['A#2', 'D3', 'F3', 'A3', 'C4'], ['G2', 'A#2', 'D3', 'F3', 'A3'], ['A2', 'C#3', 'E3', 'G3', 'B3']]
    roots = ['D2', 'A#1', 'G1', 'A1']
    m.add(vinyl(m.n), 0, .7, bus='keys')
    for i in range(5):
        t0 = i * bar; ch = prog[i % 4]
        if t0 >= 17 * b - .01: break
        for k, nt in enumerate(ch):  # rolled rhodes chord
            m.add(epiano(nt, bar * .95), t0 + k * .018, .32, pan=-.3 + k * .15, bus='keys')
        for k, nt in enumerate(ch[1:4]):  # little answer on beat 3.5
            m.add(epiano(nt, b * 1.2), t0 + 2.5 * b + k * .02, .16, pan=.2, bus='keys')
        m.add(lp(tri(hz(roots[i % 4]), T(bar * .9)) * adsr(T(bar * .9), .01, .3, .7, .2), 900), t0, .55, bus='bass')
        m.add(lp(tri(hz(roots[i % 4]), T(b * .9)) * adsr(T(b * .9), .01, .2, .6, .1), 900), t0 + 3 * b, .45, bus='bass')
    kicks = []
    for k in range(17):
        t0 = k * b
        if k >= 8 and k < 17:  # kick comes in on the #1 result (beat 8 = 5.22 s)
            if k % 2 == 0:
                m.add(lp(kick(punch=.9, length=.35, top=120, bottom=45, drive=1.2, click=.15), 3000), t0, .75, bus='drums'); kicks.append(t0)
            if k % 4 == 3:
                m.add(lp(kick(punch=.8, length=.3, top=120, bottom=45, drive=1.2, click=.1), 3000), t0 + 2 * s16, .55, bus='drums'); kicks.append(t0 + 2 * s16)
        if k % 2 == 1 and k < 17:
            m.add(lp(rim(), 5000), t0 + .02, .45, pan=.15, bus='drums')
        if k >= 4 and k < 17:
            for j in (0, 2):
                m.add(lp(hat(vel=.5 if j else .7), 8000), t0 + j * s16 + (.012 if j else 0), .35, pan=.3, bus='drums')
    # end card: chord rings out
    for k, nt in enumerate(prog[0]):
        m.add(epiano(nt, 2.0), 17 * b + k * .02, .3, bus='keys')
    m.add(lp(tri(hz('D2'), T(1.6)) * adsr(T(1.6), .01, .3, .6, .3), 900), 17 * b, .5, bus='bass')
    # soft key taps while typing (screen frames: 'hoover' from 2.62 s, 'carlsbad' from 7.2 s)
    for k in range(6): m.add(keytap(), 3.025 + k * .2083, .55, bus='sfx')
    for k in range(8): m.add(keytap(), 7.357 + k * .055, .4, bus='sfx')
    m.sidechain('keys', kicks, .25, .2); m.sidechain('bass', kicks, .3, .15)
    m.fx_reverb('keys', .3, 2.2, 2.6, 4500)
    out = m.render({'keys': 1.0, 'bass': .9, 'drums': .85, 'sfx': .5}, master_drive=0.8, lufsish=-15)
    out = lp(out, 9000)
    write_wav(OUT + 'm1.wav', out)
    sx = m.bus['sfx'] / (np.abs(m.bus['sfx']).max() + 1e-9) * .4; write_wav(OUT + 'm1_sfx.wav', sx)
    print('m1 len %.2f' % L)

# ======================= M2: dark R&B, 100 BPM, G minor (top 10 walk-in) =======================
def m2():
    bpm = 100; b = .6; bar = 2.4; s16 = b / 4; DROP = 6.0
    L = 15.6; m = Mix(L + .3); kicks = []
    prog = [['G3', 'A#3', 'D4', 'F4'], ['D#3', 'G3', 'A#3', 'D4'], ['A#2', 'D3', 'F3', 'A3'], ['F3', 'A3', 'C4', 'D#4']]
    roots = ['G1', 'D#1', 'A#0', 'F1']
    # intro 0-6.0: filtered pad + snaps on 2 and 4
    for i in range(3):
        t0 = i * bar; x = pad(prog[i % 4], bar + .3, cutoff=900, a=.3, r=.4)
        m.add(x, t0, 2.4, bus='intro')
        m.add(k808(roots[i % 4], length=bar, drive=1.4, decay=.8, tone=350), t0, .45, bus='intro')
    m.add(k808('G1', length=2.0, drive=1.5, decay=.9, tone=400), 0, .5, bus='bass')
    for k in range(10):
        if k % 2 == 1: m.add(snap(.06), k * b, .9, pan=-.2, bus='intro')
    # reversed swell into the drop
    sw = riser(1.6, 200, 3000, tone=False)[::-1][::-1]
    m.add(sw, DROP - 1.6, .35, bus='pad')
    rv = lp(noise(T(1.2)), 6000) * np.linspace(0, 1, T(1.2)) ** 3 * .25
    m.add(rv, DROP - 1.2, .8, bus='pad')
    # drop 6.0 -> 13.2: full
    def full_bar(t0, ci, last=False):
        m.add(pad(prog[ci], bar + .2, cutoff=2600, a=.05, r=.4), t0, .85, bus='pad')
        for k, nt in enumerate(prog[ci][1:]):  # bell motif
            m.add(fm_bell(nt.replace('3', '5').replace('4', '5'), .9, idx=1.5, ratio=2, decay=3), t0 + (k * 3 + 2) * s16 * 2, .22, pan=(-.3 + k * .3), bus='keys')
        m.add(k808(roots[ci], length=b * 2.6, drive=2.4, decay=1.3, tone=900), t0, .95, bus='bass')
        m.add(k808(roots[ci], length=b * 1.2, drive=2.4, decay=2, tone=900), t0 + 2.75 * b, .75, bus='bass')
        for k in (0, 7, 10):
            if last and k > 8: continue
            m.add(kick(punch=1.0, length=.4, top=130, bottom=42, drive=1.5, click=.2), t0 + k * s16, .85, bus='drums'); kicks.append(t0 + k * s16)
        for k in (4, 12):
            if last and k == 12: continue
            m.add(clap(length=.4), t0 + k * s16, .55, bus='drums'); m.add(snap(), t0 + k * s16, .4, bus='drums')
        for k in range(16):
            if last and k >= 12: continue
            if k % 2 == 0 or k in (13, 15): m.add(hat(vel=.75 if k % 4 == 0 else .5, tone=8500), t0 + k * s16, .35, pan=.3, bus='drums')
    full_bar(DROP, 0); full_bar(DROP + bar, 1); full_bar(DROP + 2 * bar, 2, last=True)
    # beat 4 of the #1 bar (13.0) drops out: just the pad tail. End card 13.2: low bell + 808 + pad
    m.add(pad(prog[0], 2.4, cutoff=1200, a=.02, r=1.0), 13.2, .8, bus='pad')
    m.add(k808('G1', length=2.2, drive=2.2, decay=1.2, tone=700), 13.2, .9, bus='bass')
    m.add(kick(punch=1, length=.5, top=130, bottom=42, click=.2), 13.2, .85, bus='drums')
    m.add(fm_bell('G5', 2.0, idx=1.2, ratio=2, decay=1.8), 13.2, .3, bus='keys')
    m.sidechain('pad', kicks, .4, .2); m.sidechain('keys', kicks, .2, .15)
    m.fx_reverb('pad', .25, 2.6, 2.4, 4000); m.fx_reverb('keys', .4, 2.6, 2.2, 5000); m.fx_reverb('drums', .08, 1.0, 5, 6000); m.fx_reverb('intro', .35, 2.6, 2.0, 4000)
    out = m.render({'pad': .8, 'keys': .9, 'bass': 1.0, 'drums': .9, 'intro': 1.0}, master_drive=1.1, lufsish=-13)
    write_wav(OUT + 'm2.wav', out); write_wav(OUT + 'm2_sfx.wav', np.zeros_like(out))
    print('m2 peak %.2f' % np.abs(out).max())

# ======================= M3: phonk / montagem, 130 BPM, F minor (pause and pick) =======================
def bellnote(note, length):
    """distorted cowbell-ish lead (montagem style): two detuned square partials, band-passed, saturated"""
    n = T(length); t = tt(n); f = hz(note)
    x = pulse(f, n, .5) + .6 * pulse(f * 1.48, n, .5)
    y = bp(x, f * .8, min(9000, f * 6)) * np.exp(-t * 7)
    return sat(y * 2.2, 2.0) * .28
def m3():
    bpm = 130; b = 60 / bpm; bar = 4 * b; s16 = b / 4
    L = 9 * bar + .1; m = Mix(L + .2); kicks = []
    KP = [0, 3, 6, 10, 12]
    mel = [('F5', 0), ('F5', 2), ('G#5', 3), ('F5', 6), ('D#5', 8), ('C5', 10), ('D#5', 11), ('F5', 12), ('C5', 14)]
    mel2 = [('C6', 0), ('A#5', 2), ('G#5', 3), ('G5', 6), ('G#5', 8), ('F5', 10), ('G5', 11), ('G#5', 12), ('A#5', 14)]
    roots = ['F1', 'C#1', 'D#1', 'C1']
    def bar_(t0, i, stop=True, freeze=.25):
        """one game per bar: full groove, last beat tape-stops (the 'pause')"""
        tmp = Mix(bar + .4); kk = []
        for k in KP:
            tmp.add(kick(punch=1.2, top=180, bottom=46, length=.28, drive=2.4), k * s16, .9, bus='d'); kk.append(k * s16)
            tmp.add(k808(roots[i % 4], length=s16 * 2.4, drive=4.5, decay=3, tone=1800, punch=.6), k * s16, .8, bus='b')
        for k in (4, 12): tmp.add(clap(length=.25, tone=(1200, 7000)), k * s16, .7, bus='d')
        for k in range(16): tmp.add(hat(vel=1.0 if k % 2 == 0 else .5, tone=9000), k * s16, .3, pan=.3, bus='d')
        for nt, k in (mel if i % 2 == 0 else mel2): tmp.add(bellnote(nt, s16 * 1.8), k * s16, .7, pan=-.15, bus='l')
        tmp.sidechain('l', kk, .3, .1)
        x = tmp.render({}, master_drive=0, lufsish=-14)
        if stop:
            cut = T(3 * b)
            head = x[:, :cut]; tail = tape_stop(x[:, cut:], .3)
            x = np.hstack([head, tail])
        m.add(x, t0, 1.0, bus='main')
        kicks.extend(t0 + k for k in kk)
    # bar 0 (hook): bell melody alone over muffled kick pattern, no stop
    for nt, k in mel: m.add(bellnote(nt, s16 * 1.8), k * s16, .7, pan=-.15, bus='l0')
    for k in KP: m.add(lp(kick(length=.25, drive=2), 700), k * s16, .7, bus='l0')
    m.add(riser(bar * .6, 500, 6000, tone=False), bar * .4, .25, bus='l0')
    for i in range(1, 7):  # six games
        bar_(i * bar, i, stop=True)
    # bar 6 (game 6) gets a drum fill instead of a plain groove: add conga-ish toms over its last beat
    for r, nt in enumerate([220, 200, 180, 160, 150, 140, 130, 120]):
        m.add(tom(nt, .12), 6 * bar + 3 * b + r * b / 8, .45, bus='l0')
    bar_(7 * bar, 0, stop=False)   # tap + locked in
    # end card 8*bar: break, one 808 hit + bell
    m.add(k808('F1', length=1.6, drive=4, decay=1.4, tone=1500), 8 * bar, .9, bus='l0')
    m.add(bellnote('F5', .6), 8 * bar, .6, bus='l0'); m.add(bellnote('C6', .5), 8 * bar + b, .4, bus='l0')
    m.fx_reverb('l0', .15, 1.4, 3, 6000)
    out = m.render({'main': 1.0, 'l0': 1.0}, master_drive=1.3, lufsish=-11.5)
    write_wav(OUT + 'm3.wav', out); write_wav(OUT + 'm3_sfx.wav', np.zeros_like(out))
    print('m3 len %.2f peak %.2f' % (L, np.abs(out).max()))

# ======================= M4: piano -> trap, 72 BPM, C minor (newsprint story) =======================
def piano(note, length=2.0, vel=1.0):
    n = T(length); t = tt(n); f = hz(note)
    x = (np.sin(2 * np.pi * f * t) + .45 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 1.5) + .2 * np.sin(2 * np.pi * 3.01 * f * t) * np.exp(-t * 3)
         + .08 * np.sin(2 * np.pi * 4.02 * f * t) * np.exp(-t * 5))
    ham = lp(noise(n), 3000) * np.exp(-t * 90) * .06
    env = np.minimum(1, t / .004) * (np.exp(-t * 1.1) * .8 + np.exp(-t * 6) * .2)
    return lp((x * env + ham) * vel, 2500 + 2500 * vel) * .35
def m4():
    bpm = 72; b = 60 / bpm; bar = 4 * b; s16 = b / 4; DROP = 4 * bar
    L = 20.0; m = Mix(L + .5); kicks = []
    prog = [['C3', 'G3', 'D#4', 'G4'], ['G#2', 'D#3', 'C4', 'G4'], ['D#3', 'A#3', 'D4', 'G4'], ['G2', 'D3', 'B3', 'F4']]
    melody = ['G4', 'D#4', 'C4', 'D#4', 'G4', 'G#4', 'G4', 'F4']
    def piano_bar(t0, ci, vel=.8, mel=True, bus='p'):
        ch = prog[ci % 4]
        m.add(piano(ch[0], bar + 1, vel), t0, .9, pan=-.1, bus=bus)
        for k, nt in enumerate(ch[1:]): m.add(piano(nt, bar, vel * .8), t0 + .03 * k, .6, pan=-.1 + k * .1, bus=bus)
        if mel:
            for k in range(4):
                nt = melody[(ci * 2 + k) % 8]
                m.add(piano(nt.replace('4', '5'), b * 1.6, vel * .7), t0 + k * b + (b / 2 if k % 2 else 0), .45, pan=.2, bus=bus)
    for i in range(4): piano_bar(i * bar, i, vel=.75, mel=(i % 2 == 1), bus='pi')
    # sub swell under bars 2-3 (6.67-13.3)
    n = T(2 * bar); t = tt(n)
    sub = np.sin(2 * np.pi * hz('C1') * t) * (t / (2 * bar)) ** 2 * .5
    m.add(sub, 2 * bar, .6, bus='b')
    m.add(riser(1.6, 200, 4000, tone=False), DROP - 1.6, .25, bus='p')
    # DROP 13.33: trap
    for i in range(2):
        t0 = DROP + i * bar
        piano_bar(t0, i, vel=.9, mel=True)
        root = ['C1', 'G#0'][i]
        m.add(k808(root, length=b * 2.2, drive=2.6, decay=1.0, tone=900), t0, 1.0, bus='b')
        m.add(k808(root, length=b * 1.4, glide='G1' if i == 0 else 'D#1', drive=2.6, decay=1.4, tone=900), t0 + 2.5 * b, .8, bus='b')
        for k in (0, 10):
            m.add(kick(punch=1.1, length=.45, top=140, bottom=44, drive=1.6, click=.3), t0 + k * s16, .85, bus='d'); kicks.append(t0 + k * s16)
        m.add(clap(length=.45), t0 + 2 * b, .6, bus='d'); m.add(snare(tone=200, length=.3), t0 + 2 * b, .3, bus='d')
        for k in range(16):
            v = .7 if k % 2 == 0 else .45
            m.add(hat(vel=v, tone=8500), t0 + k * s16, .3, pan=.3, bus='d')
            if i == 1 and k in (13, 14, 15):
                for r in range(2): m.add(hat(vel=.5), t0 + k * s16 + r * s16 / 2, .25, pan=.3, bus='d')
    # paper stamp thud on the drop (sfx)
    st = lp(noise(T(.25)), 900) * np.exp(-tt(T(.25)) * 30) * .8 + np.sin(2 * np.pi * 70 * tt(T(.25))) * np.exp(-tt(T(.25)) * 25) * .6
    m.add(st, DROP, .7, bus='sfx')
    # end: one piano note rings out
    m.add(piano('C4', 4, .7), DROP + 2 * bar, .8, bus='p'); m.add(piano('C3', 4, .6), DROP + 2 * bar, .6, bus='p')
    m.sidechain('p', kicks, .2, .2)
    m.fx_reverb('p', .45, 3.0, 1.6, 5000); m.fx_reverb('pi', .45, 3.0, 1.6, 5000); m.fx_reverb('d', .06, 1.0, 5, 6000)
    full = m.render({'p': 1.0, 'pi': 3.2, 'b': .95, 'd': .85, 'sfx': .7}, master_drive=1.0, lufsish=-13)
    write_wav(OUT + 'm4.wav', full)
    sx = m.bus['sfx'] / (np.abs(m.bus['sfx']).max() + 1e-9) * .5; write_wav(OUT + 'm4_sfx.wav', sx)
    print('m4 peak %.2f' % np.abs(full).max())

# ======================= M5: music box -> hip-hop, 150 BPM, Eb major (it's time) =======================
def musicbox(note, length=1.4):
    n = T(length); t = tt(n); f = hz(note)
    x = np.sin(2 * np.pi * f * t) + .3 * np.sin(2 * np.pi * f * 4.1 * t) * np.exp(-t * 12) + .15 * np.sin(2 * np.pi * f * 6.3 * t) * np.exp(-t * 20)
    return x * np.exp(-t * 3.2) * np.minimum(1, t / .002) * .3
def bounce():
    """ball-on-hardwood thud for the kick layer: short low body + woody click"""
    n = T(.18); t = tt(n)
    return (np.sin(2 * np.pi * (95 + 60 * np.exp(-t * 40)) * t) * np.exp(-t * 28) + bp(noise(n), 900, 3000) * np.exp(-t * 180) * .35) * .8
def m5():
    bpm = 150; b = .4; bar = 1.6; s16 = b / 4; DROP = 3.2
    L = 13.0; m = Mix(L + .2); kicks = []
    tune = ['G5', 'A#5', 'D#6', 'D6', 'A#5', 'G5', 'F5', 'D#5']
    for k, nt in enumerate(tune):
        m.add(musicbox(nt), k * b, 1.3, pan=.15 * (-1) ** k, bus='box0')
    for k, nt in enumerate(['D#4', 'G4', 'A#4']):
        m.add(musicbox(nt, 2.4), k * .01, .7, bus='box0')
    m.add(lp(noise(T(3.0)), 9000) * 0, 0, 1, bus='box')
    for k in range(16):  # sleigh-bell shimmer, very soft
        m.add(hp(noise(T(.05)), 7000) * np.exp(-tt(T(.05)) * 60) * .5, k * b / 2, .25, pan=.4, bus='box')
    m.add(choir(['D#5', 'G5', 'A#5'], .85, a=.25, r=.15), 2.4, 1.2, bus='box0')
    # DROP: hip-hop at 150 (half-time feel), Eb - Cm - Ab - Bb
    prog = [['D#3', 'G3', 'A#3'], ['C3', 'D#3', 'G3'], ['G#2', 'C3', 'D#3'], ['A#2', 'D3', 'F3']]
    roots = ['D#1', 'C1', 'G#0', 'A#0']
    nb = int((L - DROP) / bar) + 1
    for i in range(nb):
        t0 = DROP + i * bar
        if t0 >= L - .05: break
        ci = i % 4; last = t0 + bar > L - .2
        for nt in prog[ci]: m.add(brass(nt.replace('2', '4').replace('3', '4'), b * .9, cutoff=3000), t0, .22, pan=-.2, bus='keys'); m.add(brass(nt.replace('2', '4').replace('3', '4'), b * .5, cutoff=3000), t0 + 2.5 * b, .18, pan=.2, bus='keys')
        m.add(k808(roots[ci], length=b * 1.8, drive=2.4, decay=2, tone=1000), t0, .9, bus='bass')
        m.add(k808(roots[ci], length=b * 1.1, drive=2.4, decay=2.4, tone=1000), t0 + 2.75 * b, .7, bus='bass')
        for k in (0, 6, 9):
            if last and k > 6: continue
            m.add(kick(punch=1.15, length=.35, top=160, bottom=48, drive=1.8), t0 + k * s16, .85, bus='drums'); kicks.append(t0 + k * s16)
            m.add(bounce(), t0 + k * s16, .3, bus='drums')
        if not last or True:
            m.add(snare(tone=230, length=.22, crack=1.2, body=.4, bright=8000), t0 + 2 * b, .7, bus='drums')
            if not last: m.add(snare(tone=230, length=.22, crack=1.2, body=.4, bright=8000), t0 + 2 * b + 0, 0, bus='drums')
        for k in range(16):
            if last and k > 8: break
            m.add(hat(vel=.8 if k % 2 == 0 else .45, tone=8500), t0 + k * s16, .3, pan=.3, bus='drums')
        for k, nt in enumerate(tune[:4] if i % 2 == 0 else tune[4:]):
            m.add(musicbox(nt, .8), t0 + k * b, .3, pan=.3, bus='box')
    # hard stop at 13.0: everything cut, one 808 tail
    kicks = [k for k in kicks if k < L]; m.sidechain('keys', kicks, .35, .12); m.sidechain('box', kicks, .2, .12)
    m.fx_reverb('box', .35, 2.2, 2.2, 7000); m.fx_reverb('box0', .4, 2.4, 2.0, 7000); m.fx_reverb('drums', .07, .8, 5, 6000)
    out = m.render({'box': .9, 'box0': 1.0, 'keys': .9, 'bass': 1.0, 'drums': 1.0}, master_drive=1.2, lufsish=-12)
    cut = T(12.95); out[:, cut:] *= np.linspace(1, 0, out.shape[1] - cut) ** 4
    write_wav(OUT + 'm5.wav', out); write_wav(OUT + 'm5_sfx.wav', np.zeros_like(out))
    print('m5 peak %.2f' % np.abs(out).max())

if __name__ == '__main__':
    for a in sys.argv[1:]: globals()[a]()
