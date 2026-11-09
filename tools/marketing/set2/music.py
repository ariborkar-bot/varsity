"""Five original tracks (all synthesized, no samples or licensed music), one per video, each a different genre.
python3 music.py v1 [v2 ...] -> audio/vN.wav (music + sound effects) and audio/vN_sfx.wav (sound effects only, for adding a trending sound in-app)."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from snd import *
OUT = '/home/claude/mk/audio/'; os.makedirs(OUT, exist_ok=True)

def finish(m, name, music_buses, sfx_buses=('sfx',), gains=None, lufs=-11.0):
    gains = gains or {}
    full = m.render(gains, lufsish=lufs)
    write_wav(OUT + name + '.wav', full)
    s = Mix(m.n / SR)
    for b in sfx_buses:
        if b in m.bus: s.bus[b] = m.bus[b].copy()
    if s.bus:
        write_wav(OUT + name + '_sfx.wav', s.render({}, master_drive=0, lufsish=-14))
    print(name, 'peak %.2f rms %.3f' % (np.abs(full).max(), np.sqrt(np.mean(full ** 2))))

# ======================= V1: rage (pack opening) 150 BPM, F# minor =======================
def v1():
    bpm = 150; b = 60 / bpm; bar = 4 * b; s16 = b / 4
    L = 12.8; m = Mix(L)
    DROP = 7.2  # Mythical reveal
    kicks = []
    # lead: bright staccato supersaw arp, F#m / D / A / E
    prog = [['F#5', 'A5', 'C#6', 'E6'], ['D5', 'F#5', 'A5', 'C#6'], ['A4', 'C#5', 'E5', 'A5'], ['E5', 'G#5', 'B5', 'E6']]
    rhythm = [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1]
    order = [0, 1, 2, 1, 3, 2, 1, 0, 2, 3, 1, 2, 0, 2, 3, 1]
    def lead_bar(t0, chord, cutoff, gain=1.0):
        for k in range(16):
            if rhythm[k]:
                nt = chord[order[k] % 4]
                m.add(supersaw(nt, s16 * 1.6, voices=7, detune=.28, cutoff=cutoff, d=.08, s=.35, r=.05, drive=2.2), t0 + k * s16, .55 * gain, bus='lead')
    # bar 1 (0-1.6): filtered lead only + rising hats
    lead_bar(0, prog[0], 2600, 1.5)
    m.add(k808('F#1', length=1.5, drive=3, decay=1.3, tone=1200), 0, .7, bus='bass')
    for k in range(8): m.add(hat(vel=.5 + k * .06), k * b / 2, .5, pan=.3, bus='drums')
    m.add(riser(1.5, 400, 5000, tone=False), .1, .45, bus='sfx')
    # 1.6 rip: impact + full beat for bars 2-3 (1.6-4.8)
    m.add(impact(1.8), 1.6, .8, bus='sfx'); m.add(snap(), 1.6, .8, bus='sfx')
    def beat_bar(t0, chord_i, full=True, roll=False):
        lead_bar(t0, prog[chord_i], 5200)
        kp = [0, 6, 10] if full else [0]
        for k in kp:
            m.add(kick(punch=1.1, top=180, bottom=46), t0 + k * s16, .9, bus='drums'); kicks.append(t0 + k * s16)
        root = ['F#1', 'D1', 'A1', 'E1'][chord_i]
        m.add(k808(root, length=bar * .55, drive=3.2, decay=1.4, tone=1400), t0, .95, bus='bass')
        m.add(k808(root, length=bar * .4, glide=('F#1' if root != 'F#1' else 'A1'), drive=3.2, decay=1.8, tone=1400), t0 + 10 * s16, .8, bus='bass')
        m.add(clap(), t0 + 2 * b, .75, bus='drums'); m.add(snare(tone=210, crack=1.1), t0 + 2 * b, .45, bus='drums')
        for k in range(16):
            if roll and k >= 12:
                for r in range(3): m.add(hat(vel=.7), t0 + k * s16 + r * s16 / 3, .55, pan=.25, bus='drums')
            elif k % 2 == 0 or k in (5, 11): m.add(hat(vel=.9 if k % 4 == 0 else .7), t0 + k * s16, .55, pan=.25, bus='drums')
        m.add(hat(open_=True), t0 + 3.5 * b, .35, pan=-.2, bus='drums')
    beat_bar(1.6, 1); beat_bar(3.2, 2, roll=True)
    # 4.8-7.2: build. drums out, lead filter opens, snare roll + riser, tape stop at the end
    for k in range(6):
        lead_bar_t = 4.8 + k * bar / 4
    seg_n = T(2.4); build = np.zeros((2, seg_n))
    tmp = Mix(2.4)
    for k in range(16 + 8):
        nt = prog[3][order[k % 16] % 4]
        tmp.add(supersaw(nt, s16 * 1.6, detune=.3, cutoff=6000, d=.08, s=.35, r=.05, drive=2.2), k * s16, .5)
    bx = tmp.render({}, master_drive=0, lufsish=-16)
    bx = np.vstack([sweep_lp(bx[0], 500, 9000, 2.2, 40), sweep_lp(bx[1], 500, 9000, 2.2, 40)])
    m.add(bx, 4.8, 1.2, bus='lead')
    for k in range(24):  # snare roll accelerating
        tk = 4.8 + 2.2 * (k / 24) ** .8
        m.add(snare(tone=230, length=.12, crack=.8, body=.3), tk, .12 + .35 * k / 24, bus='drums')
    m.add(riser(2.3, 300, 9000), 4.85, .7, bus='sfx')
    # DROP at 7.2: impact + 2 bars full beat + end
    m.add(impact(2.5), DROP, 1.0, bus='sfx'); m.add(whoosh(.5, up=False), DROP - .02, .5, bus='sfx')
    m.add(ding('C#7', 1.2), DROP + .05, .35, bus='sfx')
    beat_bar(DROP, 0); beat_bar(DROP + bar, 1, roll=True)
    # end card (10.4-12.8): half bar beat then 808 tail + lead echo
    beat_bar(DROP + 2 * bar, 0)
    m.add(k808('F#1', length=1.6, drive=3, decay=1.2), DROP + 3 * bar, .9, bus='bass')
    m.add(supersaw('F#5', .5, cutoff=3000, d=.2, s=.2), DROP + 3 * bar, .5, bus='lead')
    # card flip snaps during the montage (cards flip at ~2.2-3.2s on screen)
    for tk in (2.3, 2.6, 2.9): m.add(snap(), tk, .5, bus='sfx'); m.add(whoosh(.18), tk - .1, .2, bus='sfx')
    m.sidechain('lead', kicks, .55, .16); m.sidechain('bass', kicks, .3, .1)
    m.fx_reverb('lead', .22, 1.6, 3.2, 7000); m.fx_reverb('sfx', .15, 2.5, 2.0, 5000, send_to='sfx')
    m.fx_reverb('drums', .08, 1.0, 5, 6000)
    finish(m, 'v1', ['lead', 'drums', 'bass'], gains={'lead': .9, 'drums': 1.0, 'bass': 1.0, 'sfx': .9})
    json.dump({'bpm': bpm, 'drop': DROP, 'len': L}, open(OUT + 'v1.json', 'w'))

# ======================= V2: jersey club (find your school) 140 BPM, A minor =======================
def v2():
    bpm = 140; b = 60 / bpm; bar = 4 * b; s16 = b / 4; L = 7 * bar; m = Mix(L + .3); kicks = []
    chords = [['A3', 'C4', 'E4'], ['F3', 'A3', 'C4'], ['C4', 'E4', 'G4'], ['G3', 'B3', 'D4']]
    roots = ['A1', 'F1', 'C2', 'G1']
    KP = [0, 4, 8, 11, 14]
    def stabs(t0, ci, cutoff=3500, gain=1.0):
        for k in (0, 3, 6, 10, 12):
            for nt in chords[ci]:
                m.add(pluck(nt, .28, bright=.7, decay=9), t0 + k * s16, .3 * gain, pan=-.2, bus='keys')
                m.add(pluck(nt.replace('3', '4').replace('4', '5') if False else nt, .2, bright=.9, decay=14), t0 + k * s16 + .004, .12 * gain, pan=.3, bus='keys')
    def chops(t0, ci, pattern=(0, 2, 4, 7, 8, 10, 13, 14)):
        mel = {0: ['E5', 'C5', 'A4'], 1: ['C5', 'A4', 'F4'], 2: ['G5', 'E5', 'C5'], 3: ['D5', 'B4', 'G4']}[ci]
        for j, k in enumerate(pattern):
            m.add(vox(mel[j % 3], s16 * 1.3, 'a' if j % 2 == 0 else 'e'), t0 + k * s16, .42, pan=(.25 if j % 2 else -.25), bus='vox')
    def club(t0, ci, flourish=True, chop=True):
        for k in KP:
            m.add(kick(punch=1.2, top=190, bottom=50, length=.32, drive=2.0), t0 + k * s16, .95, bus='drums'); kicks.append(t0 + k * s16)
            m.add(k808(roots[ci], length=.3, drive=1.8, decay=6, tone=600, punch=.5), t0 + k * s16, .7, bus='bass')
        if flourish:
            for r in range(3): m.add(kick(punch=1.1, length=.2, drive=2), t0 + 3 * b + r * b / 3, .8, bus='drums'); kicks.append(t0 + 3 * b + r * b / 3)
        for k in (4, 12): m.add(clap(tone=(1100, 6000)), t0 + k * s16, .75, bus='drums')
        for k in range(16):
            if k % 2 == 1: m.add(hat(vel=.8), t0 + k * s16, .4, pan=.35, bus='drums')
        stabs(t0, ci)
        if chop: chops(t0, ci)
    # bar 1: chops + filtered stabs + kick flourish
    chops(0, 0); stabs(0, 0, gain=.8)
    for r in range(3): m.add(kick(punch=1.1, length=.2, drive=2), 3 * b + r * b / 3, .8, bus='drums')
    m.add(riser(bar * .9, 500, 7000, tone=False), .1, .35, bus='sfx')
    club(bar, 1); club(2 * bar, 2)
    # bar 4: beat switch, half-time, 808 slides, chords held
    t0 = 3 * bar
    m.add(impact(1.6), t0, .55, bus='sfx'); m.add(whoosh(.4, up=False), t0 - .2, .4, bus='sfx')
    m.add(pad(chords[3], bar, cutoff=1800), t0, .55, bus='keys')
    m.add(kick(punch=1.2), t0, .9, bus='drums'); kicks.append(t0)
    m.add(k808('G1', length=bar * .5, glide='D2', drive=3, decay=1.2, tone=1200), t0, .9, bus='bass')
    m.add(clap(), t0 + 2 * b, .8, bus='drums'); m.add(snare(), t0 + 2 * b, .4, bus='drums')
    for k in range(16): m.add(hat(vel=.6 + .3 * (k % 4 == 0)), t0 + k * s16, .35, pan=.3, bus='drums')
    for r in range(6): m.add(hat(vel=.7), t0 + 3 * b + r * b / 6, .35, pan=.3, bus='drums')
    club(4 * bar, 0)
    # bar 6: three slams (beats 1,2,3) then kick triplets
    t0 = 5 * bar
    for k in range(3):
        m.add(impact(.9), t0 + k * b, .55, bus='sfx'); m.add(kick(punch=1.3, top=200), t0 + k * b, 1.0, bus='drums'); kicks.append(t0 + k * b)
        for nt in chords[k % 4]: m.add(pluck(nt, .35, bright=.9, decay=7), t0 + k * b, .35, bus='keys')
        m.add(vox(['A4', 'C5', 'E5'][k], .25, 'a'), t0 + k * b, .5, bus='vox')
    for r in range(6): m.add(kick(punch=1.1, length=.15, drive=2), t0 + 3 * b + r * b / 6, .7, bus='drums'); kicks.append(t0 + 3 * b + r * b / 6)
    club(6 * bar, 0, flourish=False)
    m.add(k808('A1', length=1.0, drive=2.5, decay=2), 7 * bar - .05, .6, bus='bass')
    m.sidechain('keys', kicks, .6, .14); m.sidechain('vox', kicks, .3, .1); m.sidechain('bass', kicks, .2, .08)
    m.fx_reverb('keys', .25, 1.4, 3.5, 6000); m.fx_reverb('vox', .2, 1.2, 4, 7000)
    finish(m, 'v2', [], gains={'keys': .8, 'vox': .9, 'drums': 1.0, 'bass': .9, 'sfx': .8})

# ======================= V3: chiptune trap (Hoops) 160 BPM, E minor =======================
def v3():
    bpm = 160; b = 60 / bpm; bar = 4 * b; s16 = b / 4; L = 10 * bar; m = Mix(L + .3); kicks = []
    prog = [['E4', 'G4', 'B4'], ['C4', 'E4', 'G4'], ['D4', 'F#4', 'A4'], ['B3', 'D4', 'F#4']]
    roots = ['E1', 'C1', 'D1', 'B0']
    melody = ['B5', 'G5', 'E5', 'G5', 'A5', 'B5', 'D6', 'B5', 'A5', 'G5', 'F#5', 'E5', 'F#5', 'G5', 'A5', 'F#5']
    def arp(t0, ci, duty=.125, gain=1.0, oct_up=False):
        ch = prog[ci]
        for k in range(16):
            nt = ch[k % 3] if not oct_up else ch[k % 3][:-1] + str(int(ch[k % 3][-1]) + 1)
            m.add(chip(nt, s16 * .9, duty=duty), t0 + k * s16, .5 * gain, pan=(-.3 if k % 2 else .3), bus='chip')
    def lead(t0, gain=1.0, duty=.5, vib=.012):
        for k in range(0, 16, 2):
            m.add(chip(melody[k], s16 * 1.9, duty=duty, vib=vib), t0 + k * s16, .7 * gain, bus='lead')
    def chipbass(t0, ci):
        for k in (0, 3, 6, 8, 11, 14): m.add(tri_bass(roots[ci], s16 * 1.5), t0 + k * s16, .6, bus='chip')
    def drums(t0, ci, trap=True, roll=False, full=True):
        for k in ([0, 7, 10] if full else [0]):
            m.add(kick(punch=1.1, top=175, length=.35), t0 + k * s16, .85, bus='drums'); kicks.append(t0 + k * s16)
        if trap:
            m.add(k808(roots[ci].replace('0', '1') if roots[ci].endswith('0') else roots[ci], length=bar * .5, drive=2.6, decay=1.5, tone=1100), t0, .8, bus='bass')
        m.add(nsnare(), t0 + 2 * b, .6, bus='drums'); m.add(clap(), t0 + 2 * b, .5, bus='drums')
        for k in range(16):
            if roll and k >= 12:
                for r in range(2): m.add(hat(vel=.7, tone=8500), t0 + k * s16 + r * s16 / 2, .45, pan=.25, bus='drums')
            elif k % 2 == 0: m.add(hat(vel=.85, tone=8500), t0 + k * s16, .45, pan=.25, bus='drums')
    def lvlup(t0):
        for j, nt in enumerate(['E5', 'G5', 'B5', 'E6', 'G6']): m.add(chip(nt, .06, duty=.125), t0 - .3 + j * .055, .55, bus='sfx')
    # bar 1 hook: chip lead + arp + chip drums (no 808)
    lead(0); arp(0, 0, gain=.7)
    for k in (0, 6, 8, 12): m.add(nkick(), k * s16, .7, bus='drums')
    m.add(nsnare(), 2 * b, .5, bus='drums')
    # zones: bars 2..7, each adds or changes something
    for z in range(6):
        t0 = (1 + z) * bar; ci = z % 4
        lvlup(t0) if z > 0 else m.add(chip('E6', .12, duty=.125), t0 - .05, .5, bus='sfx')
        if z == 5:
            # zero gravity: spacey half bar then the full drop
            m.add(pad(['E3', 'B3', 'G4', 'D5'], bar * 2, cutoff=2500), t0, .6, bus='chip')
            for k in range(0, 16, 4): m.add(fm_bell(['E6', 'B5', 'G5', 'D6'][k // 4], 1.0), t0 + k * s16, .35, bus='lead')
            m.add(k808('E1', length=bar, drive=2.5, decay=.9), t0, .8, bus='bass')
            m.add(riser(bar * .9, 400, 8000), t0 + bar * .1, .5, bus='sfx')
            t1 = t0 + bar; m.add(impact(1.6), t1, .6, bus='sfx')
            arp(t1, 0, duty=.25, oct_up=True); lead(t1, 1.1, duty=.25); drums(t1, 0, roll=True); chipbass(t1, 0)
            continue
        arp(t0, ci, duty=[.125, .125, .25, .25, .5][z])
        chipbass(t0, ci)
        drums(t0, ci, trap=z >= 1, roll=z in (2, 4), full=True)
        if z >= 2: lead(t0, .8 + .1 * z, duty=.5 if z < 4 else .25)
    # end card bars 9-10: melody + beat, ending stab
    t0 = 8 * bar
    lead(t0); arp(t0, 1); drums(t0, 1); chipbass(t0, 1)
    t0 = 9 * bar
    arp(t0, 0, gain=.6); m.add(k808('E1', length=1.4, drive=2.5, decay=1.6), t0, .8, bus='bass'); m.add(kick(), t0, .8, bus='drums')
    for j, nt in enumerate(['E5', 'G5', 'B5', 'E6']): m.add(chip(nt, .5 - j * .05, duty=.25, vib=.01), t0 + 2 * b + j * .07, .5, bus='lead')
    m.sidechain('chip', kicks, .5, .12); m.sidechain('lead', kicks, .25, .1)
    m.fx_reverb('lead', .18, 1.0, 4.5, 8000); m.fx_reverb('chip', .1, .8, 6, 8000)
    finish(m, 'v3', [], gains={'chip': .75, 'lead': .9, 'drums': 1.0, 'bass': .95, 'sfx': .7})
def tri_bass(note, length):
    n = T(length); return tri(hz(note) * 2, n) * adsr(n, .002, .05, .8, .03) * .35
def nkick():
    n = T(.18); t = tt(n); return pulse(120 * np.exp(-t * 20) + 40, n, .5) * np.exp(-t * 18) * .4
def nsnare():
    n = T(.18); t = tt(n); x = np.sign(noise(n)); x = np.repeat(x[::6], 6)[:n]
    return x * np.exp(-t * 16) * .3

# ======================= V4: drill (POV meme) 142 BPM, C# minor =======================
def v4():
    bpm = 142; b = 60 / bpm; bar = 4 * b; s16 = b / 4; L = 8 * bar; m = Mix(L + .3); kicks = []
    mel = [('C#5', 0), ('E5', 3), ('D#5', 6), ('B4', 8), ('C#5', 11), ('G#4', 14)]
    mel2 = [('C#5', 0), ('E5', 3), ('F#5', 6), ('E5', 8), ('D#5', 11), ('B4', 14)]
    def melody(t0, which=0, gain=1.0):
        for nt, k in (mel if which == 0 else mel2):
            m.add(epiano(nt, s16 * 3.5), t0 + k * s16, .55 * gain, pan=-.15, bus='keys')
            m.add(fm_bell(nt.replace('5', '6').replace('4', '5'), .7, idx=2, ratio=2, decay=4), t0 + k * s16, .18 * gain, pan=.3, bus='keys')
    def choirbar(t0, ch):
        m.add(np.vstack([choir(ch, bar + .2), choir(ch, bar + .2) * .9]), t0, .45, bus='pad')
    def slide(t0, a, bnote, length):
        m.add(k808(a, length=length, glide=bnote, glide_t=.12, drive=3.2, decay=.8, tone=1500), t0, .95, bus='bass')
    def drill(t0, ci, variant=0):
        # drill snare on beat 3 (half time) and the ghost on 2a/4e; kicks syncopated with the 808
        for k in ([0, 10] if variant == 0 else [0, 7, 11]):
            m.add(kick(punch=1.0, top=150, bottom=45, length=.3, drive=1.4), t0 + k * s16, .7, bus='drums'); kicks.append(t0 + k * s16)
        m.add(snare(tone=220, crack=1.3, body=.5, bright=8000), t0 + 2 * b, .75, bus='drums'); m.add(clap(), t0 + 2 * b, .45, bus='drums')
        m.add(snare(tone=230, length=.12, crack=.6, body=.2), t0 + 15 * s16, .3, bus='drums')
        # drill hats: triplet-feel groups
        pat = [0, 2, 3, 4, 6, 8, 10, 11, 12, 14]
        for k in pat: m.add(hat(vel=.75 if k % 4 else 1.0, tone=8000), t0 + k * s16, .45, pan=.3, bus='drums')
        for r in range(3): m.add(hat(vel=.6, tone=9000), t0 + 13 * s16 + r * s16 * 2 / 3, .35, pan=.3, bus='drums')
        root = ['C#1', 'A0', 'F#1', 'G#0'][ci]
        nxt = ['D#1', 'B0', 'G#1', 'C#1'][ci]
        slide(t0, root, nxt, b * 1.9); slide(t0 + 10 * s16, nxt, root, b * 1.4)
    ch = [['C#4', 'E4', 'G#4'], ['A3', 'C#4', 'E4'], ['F#3', 'A3', 'C#4'], ['G#3', 'B#3' if False else 'C4', 'D#4']]
    # bar 1: melody + choir + 808 slide (no drums), bar 2+: drill
    melody(0); choirbar(0, ch[0]); slide(0, 'C#1', 'E1', bar * .9)
    m.add(riser(bar * .8, 300, 5000, tone=False), .2, .25, bus='sfx')
    for i in range(1, 8):
        t0 = i * bar; ci = i % 4
        if i == 4:  # punchline: drop out on beat 1-2, everything back on 3
            m.add(tape_stop(np.vstack([epiano('C#5', .6), epiano('C#5', .6)]), .5), t0 - .5, .4, bus='keys')
            m.add(impact(1.2), t0 + 2 * b, .6, bus='sfx'); melody(t0 + 2 * b, 1, .7)
            for k in (8, 10, 14): m.add(kick(punch=1.0, top=150, bottom=45, length=.3, drive=1.4), t0 + k * s16, .7, bus='drums'); kicks.append(t0 + k * s16)
            m.add(snare(tone=220, crack=1.3, body=.5, bright=8000), t0 + 2 * b, .75, bus='drums')
            slide(t0 + 2 * b, 'C#1', 'G#1', b * 1.8); choirbar(t0, ch[0])
            continue
        melody(t0, i % 2); choirbar(t0, ch[ci]); drill(t0, ci, variant=i % 2)
    m.add(k808('C#1', length=1.6, drive=3, decay=1.4), L - .05, .0, bus='bass')
    m.sidechain('pad', kicks, .4, .2); m.sidechain('keys', kicks, .2, .1)
    m.fx_reverb('keys', .35, 2.2, 2.2, 5000); m.fx_reverb('pad', .3, 2.5, 1.8, 4000); m.fx_reverb('drums', .07, 1, 5, 6000)
    finish(m, 'v4', [], gains={'keys': .85, 'pad': .7, 'drums': 1.0, 'bass': 1.0, 'sfx': .7})

# ======================= V5: drumline anthem (rivalry) 120 BPM, Bb major =======================
def v5():
    bpm = 120; b = 60 / bpm; bar = 4 * b; s16 = b / 4; L = 6 * bar; m = Mix(L + .5); kicks = []
    def cadence(t0, dense=1.0, roll_end=True):
        acc = [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0]
        for k in range(16):
            v = 1.0 if acc[k] else .45
            if dense < 1 and not acc[k] and k % 2: continue
            m.add(msnare(vel=v), t0 + k * s16, .55 * v, pan=.1, bus='drums')
            if acc[k]: m.add(msnare(vel=.4), t0 + k * s16 - .018, .2, pan=.1, bus='drums')  # flam
        if roll_end:
            for r in range(8): m.add(msnare(length=.08, vel=.5 + r * .06), t0 + 3 * b + r * b / 8, .4, pan=.1, bus='drums')
    def basses(t0, hits):
        for k, nt in hits: m.add(bassdrum(nt), t0 + k * s16, .8, bus='drums'); kicks.append(t0 + k * s16)
    def quads(t0, pattern):
        for k, nt in pattern: m.add(tom(nt, .3), t0 + k * s16, .5, pan=(-.4 + (nt % 4) * .25), bus='drums')
    def brass_hit(t0, chord, length=.45, gain=1.0):
        for nt in chord: m.add(brass(nt, length), t0, .4 * gain, pan=0, bus='brass')
    def crash(t0, gain=.5):
        n = T(2.5); x = hp(noise(n), 3000) * np.exp(-tt(n) * 1.6); m.add(np.vstack([x, np.roll(x, 300)]) * .4, t0, gain, bus='drums')
    BB = ['Bb3', 'D4', 'F4', 'Bb4']; EB = ['Eb4', 'G4', 'Bb4']; F = ['F3', 'A3', 'C4', 'F4']; GM = ['G3', 'Bb3', 'D4', 'G4']
    # bar 1: snare cadence solo, building, crash into bar 2
    cadence(0, .5); quads(0, [(12, 220), (13, 180), (14, 150), (15, 120)])
    # bar 2: full: bass drum unison hits + brass on 1 + 808
    t0 = bar; crash(t0, .6); m.add(impact(1.5), t0, .5, bus='sfx')
    brass_hit(t0, BB, .9, 1.2); m.add(k808('Bb0', length=1.2, drive=2.5, decay=1.5), t0, .8, bus='bass')
    cadence(t0); basses(t0, [(0, 60), (3, 70), (6, 80), (8, 60), (12, 90), (14, 70)])
    m.add(clap(), t0 + b, .6, bus='drums'); m.add(clap(), t0 + 3 * b, .6, bus='drums')
    # bars 3-4: groove with brass riff
    for i, ch in ((2, [EB, F]), (3, [GM, F])):
        t0 = i * bar
        cadence(t0); basses(t0, [(0, 60), (6, 70), (8, 60), (10, 80), (14, 70)])
        quads(t0, [(4, 220), (5, 180), (12, 150), (13, 120)])
        brass_hit(t0, ch[0], .4); brass_hit(t0 + 3 * s16, ch[0], .25, .8); brass_hit(t0 + 2 * b, ch[1], .4); brass_hit(t0 + 2 * b + 3 * s16, ch[1], .6, .9)
        m.add(k808(['Eb1', 'G0'][i - 2], length=b * 1.8, drive=2.5, decay=1.6), t0, .75, bus='bass')
        m.add(k808(['F1', 'F1'][i - 2], length=b * 1.8, drive=2.5, decay=1.6), t0 + 2 * b, .75, bus='bass')
        m.add(clap(), t0 + b, .55, bus='drums'); m.add(clap(), t0 + 3 * b, .55, bus='drums')
    # bar 5: stadium break: stomp stomp clap + snare taps, brass swell
    t0 = 4 * bar
    for beat in range(4):
        tb = t0 + beat * b
        m.add(bassdrum(55, .4), tb, .9, bus='drums'); kicks.append(tb)
        if beat % 2 == 1: m.add(clap(length=.5, n_hits=6), tb, .85, bus='drums')
    m.add(pad(['Bb3', 'D4', 'F4', 'Bb4'], bar, cutoff=2600, a=.8), t0, .5, bus='brass')
    for r in range(16): m.add(msnare(length=.08, vel=.3 + r * .045), t0 + 3 * b + r * b / 16, .45, bus='drums')
    # bar 6: final: big hits on 1, 2&, 4 then ring out
    t0 = 5 * bar; crash(t0, .7); m.add(impact(2.0), t0, .55, bus='sfx')
    for k, ch in ((0, BB), (6, EB), (12, BB)):
        brass_hit(t0 + k * s16, ch, .5 if k < 12 else 1.2, 1.2); m.add(bassdrum(60), t0 + k * s16, .9, bus='drums'); kicks.append(t0 + k * s16)
        for r in range(2): m.add(msnare(vel=1), t0 + k * s16 + r * .02, .5, bus='drums')
    m.add(k808('Bb0', length=1.8, drive=2.5, decay=1.2), t0 + 12 * s16, .85, bus='bass'); crash(t0 + 12 * s16, .6)
    m.sidechain('brass', kicks, .25, .12)
    m.fx_reverb('brass', .3, 2.4, 2.2, 6000); m.fx_reverb('drums', .18, 2.0, 2.6, 7000)
    finish(m, 'v5', [], gains={'brass': .85, 'drums': 1.0, 'bass': .9, 'sfx': .7})

if __name__ == '__main__':
    for a in sys.argv[1:]: globals()[a]()
