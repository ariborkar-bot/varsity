"""Small music engine for the Nov 8 video set. Everything is synthesized here (no samples, no licensed music).
Stereo float buffers at 44.1 kHz. Instruments return mono or stereo arrays; Mix.add() places them at a time with gain/pan."""
import numpy as np, wave
from scipy import signal
SR = 44100
rng = np.random.default_rng(1234)

def T(sec): return int(round(sec * SR))
def tt(n): return np.arange(n) / SR
def midi(n): return 440.0 * 2 ** ((n - 69) / 12)
NOTE = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}
def n2m(s):  # 'C#4' -> midi
    p, o = (s[:2], s[2:]) if len(s) > 2 and s[1] in '#b' else (s[:1], s[1:])
    return 12 * (int(o) + 1) + NOTE[p]
def hz(s): return midi(n2m(s)) if isinstance(s, str) else midi(s)

# ---------- filters ----------
def _sos(kind, f, order=2, q=None):
    f = np.atleast_1d(f)
    if kind == 'bp': return signal.butter(order, [max(20, f[0]), min(SR / 2 - 100, f[1])], 'bandpass', fs=SR, output='sos')
    return signal.butter(order, min(SR / 2 - 100, max(20, f[0])), {'lp': 'lowpass', 'hp': 'highpass'}[kind], fs=SR, output='sos')
def lp(x, f, order=2): return signal.sosfilt(_sos('lp', f, order), x, axis=-1)
def hp(x, f, order=2): return signal.sosfilt(_sos('hp', f, order), x, axis=-1)
def bp(x, lo, hi, order=2): return signal.sosfilt(_sos('bp', (lo, hi), order), x, axis=-1)
def sweep_lp(x, f0, f1, curve=2.0, steps=48):
    """time-varying low-pass by crossfading blocks (cheap and smooth enough for builds)"""
    n = len(x); out = np.zeros_like(x); edges = np.linspace(0, n, steps + 1).astype(int)
    zi = None; sos_prev = None
    for k in range(steps):
        a, b = edges[k], edges[k + 1]; fr = f0 * (f1 / f0) ** ((k / max(1, steps - 1)) ** curve)
        sos = _sos('lp', fr, 2)
        if zi is None: zi = signal.sosfilt_zi(sos) * 0
        out[a:b], zi = signal.sosfilt(sos, x[a:b], zi=zi)
    return out
def peak_eq(x, f, gain_db, q=1.0):
    A = 10 ** (gain_db / 40); w = 2 * np.pi * f / SR; al = np.sin(w) / (2 * q)
    b = [1 + al * A, -2 * np.cos(w), 1 - al * A]; a = [1 + al / A, -2 * np.cos(w), 1 - al / A]
    return signal.lfilter(b, a, x, axis=-1)

# ---------- envelopes / oscillators ----------
def adsr(n, a=.005, d=.1, s=.7, r=.1, hold=None):
    t = tt(n); hold = (n / SR - r) if hold is None else hold
    e = np.where(t < a, t / max(a, 1e-4), np.where(t < a + d, 1 - (1 - s) * (t - a) / max(d, 1e-4), s))
    rel = np.clip((t - hold) / max(r, 1e-4), 0, 1); return e * (1 - rel)
def expd(n, k): return np.exp(-tt(n) * k)
def phase(freq, n):
    f = np.broadcast_to(np.asarray(freq, float), (n,)) if np.ndim(freq) else np.full(n, float(freq))
    return 2 * np.pi * np.cumsum(f) / SR
def saw_blep(freq, n, ph0=0.0):
    """band-limited-ish saw via PolyBLEP"""
    f = np.full(n, float(freq)) if np.ndim(freq) == 0 else np.asarray(freq, float)
    dt = f / SR; ph = (ph0 + np.cumsum(dt)) % 1.0; y = 2 * ph - 1
    m1 = ph < dt; tt1 = ph[m1] / dt[m1]; y[m1] -= tt1 + tt1 - tt1 * tt1 - 1
    m2 = ph > 1 - dt; tt2 = (ph[m2] - 1) / dt[m2]; y[m2] -= tt2 * tt2 + tt2 + tt2 + 1
    return y
def pulse(freq, n, duty=.5):
    f = np.full(n, float(freq)) if np.ndim(freq) == 0 else np.asarray(freq, float)
    ph = np.cumsum(f / SR) % 1.0; return np.where(ph < duty, 1.0, -1.0) - (2 * duty - 1)
def tri(freq, n):
    ph = (np.cumsum(np.full(n, float(freq)) / SR)) % 1.0; return 4 * np.abs(ph - .5) - 1
def noise(n): return rng.standard_normal(n)
def sat(x, drive=1.0): return np.tanh(x * drive) / np.tanh(drive) if drive > 0 else x

# ---------- drums ----------
def kick(punch=1.0, length=.45, top=170, bottom=48, drive=1.6, click=.5):
    n = T(length); t = tt(n); f = bottom + (top - bottom) * np.exp(-t * 32)
    body = np.sin(phase(f, n)) * np.exp(-t * (6.5 / length * .45))
    cl = hp(noise(n), 2500) * np.exp(-t * 250) * click
    return sat((body + cl) * punch, drive) * .95
def k808(note='F1', length=1.2, glide=None, glide_t=.08, drive=2.2, decay=1.6, punch=1.0, tone=900):
    """808: sine + octave harmonic, quick pitch drop at the start, optional glide to another note mid-way"""
    n = T(length); t = tt(n); f0 = hz(note); f = np.full(n, f0)
    if glide is not None:
        f1 = hz(glide); g0 = T(glide[1] if isinstance(glide, tuple) else length * .45) if False else T(length * .5)
        ramp = np.clip((t - t[g0]) / glide_t, 0, 1); f = f0 * (f1 / f0) ** ramp
    f = f * (1 + .9 * np.exp(-t * 45) * punch)
    ph = phase(f, n); x = np.sin(ph) + .25 * np.sin(2 * ph)
    env = np.minimum(1, t / .002) * np.exp(-t * decay)
    y = sat(x * env * 1.1, drive); y = lp(y, tone)
    return y * .9
def snare(tone=190, length=.32, crack=1.0, body=.6, bright=6500):
    n = T(length); t = tt(n)
    nz = bp(noise(n), 1500, bright) * np.exp(-t * 17) * crack
    b = np.sin(phase(tone * (1 + .4 * np.exp(-t * 60)), n)) * np.exp(-t * 28) * body
    return sat((nz * .9 + b), 1.4) * .7
def clap(length=.35, spread=.012, n_hits=4, tone=(900, 5200)):
    n = T(length); t = tt(n); e = np.zeros(n)
    for k in range(n_hits):
        i = T(k * spread * (1 + .3 * rng.random())); e[i:] += np.exp(-(t[:n - i]) * 140) * (.8 if k < n_hits - 1 else 1)
    e += np.exp(-t * 18) * .35 * (t > spread * (n_hits - 1))
    return bp(noise(n), *tone) * e * .8
HATF = np.array([205.3, 304.4, 369.6, 522.7, 540.0, 800.0]) * 1.7
def hat(length=.05, open_=False, tone=7500, vel=1.0):
    n = T(.32 if open_ else length); t = tt(n)
    x = sum(pulse(f, n) for f in HATF) / 6 + .35 * noise(n)
    x = hp(bp(x, tone * .8, 16000), tone, 2)
    return x * np.exp(-t * (11 if open_ else 75)) * .35 * vel
def rim(length=.06):
    n = T(length); t = tt(n)
    return (np.sin(phase(1700, n)) * .6 + bp(noise(n), 2000, 6000) * .5) * np.exp(-t * 110) * .5
def tom(note=100, length=.4, drive=1.2):
    n = T(length); t = tt(n); f = note * (1 + .6 * np.exp(-t * 25))
    return sat(np.sin(phase(f, n)) * np.exp(-t * 7) + bp(noise(n), 200, 2000) * np.exp(-t * 60) * .3, drive) * .8
def shaker(length=.08):
    n = T(length); t = tt(n); return hp(noise(n), 6000) * (np.sin(np.pi * np.clip(t / length, 0, 1)) ** 2) * .15
def cowbell(length=.35):
    n = T(length); t = tt(n); x = pulse(587, n) + pulse(845, n)
    return bp(x, 500, 3500) * np.exp(-t * 9) * .25
def msnare(length=.2, vel=1.0):
    """marching snare: tight, high, very bright with a ring"""
    n = T(length); t = tt(n)
    nz = bp(noise(n), 2500, 11000) * np.exp(-t * 32)
    ring = np.sin(phase(330, n)) * np.exp(-t * 40) * .5 + np.sin(phase(520, n)) * np.exp(-t * 55) * .25
    return sat((nz + ring) * vel, 1.8) * .6
def bassdrum(note=70, length=.5):
    n = T(length); t = tt(n); f = note * (1 + .3 * np.exp(-t * 30))
    return sat(np.sin(phase(f, n)) * np.exp(-t * 6) + lp(noise(n), 600) * np.exp(-t * 40) * .4, 1.3) * .9

# ---------- tonal instruments ----------
def supersaw(note, length, voices=7, detune=.22, cutoff=4500, env_amt=.0, a=.004, d=.25, s=.7, r=.12, drive=1.4, stereo=True):
    n = T(length); f = hz(note); L = np.zeros(n); R = np.zeros(n)
    for v in range(voices):
        dv = (v - (voices - 1) / 2) / ((voices - 1) / 2 + 1e-9) * detune
        x = saw_blep(f * 2 ** (dv / 12), n, rng.random())
        pan = (v / (voices - 1)) if voices > 1 else .5
        L += x * (1 - pan * .8 if stereo else 1); R += x * (.2 + pan * .8 if stereo else 1)
    e = adsr(n, a, d, s, r)
    L = lp(L / voices * 2, cutoff); R = lp(R / voices * 2, cutoff)
    return np.vstack([sat(L * e, drive), sat(R * e, drive)]) * .5
def pluck(note, length=.6, bright=.5, decay=6):
    n = T(length); f = hz(note); t = tt(n)
    x = saw_blep(f, n) * .6 + pulse(f * 1.005, n, .3) * .4
    cut = 500 + 6000 * bright * np.exp(-t * 18)
    y = sweep_lp(x, 500 + 6000 * bright, 600, 1, 16) if True else x
    return y * np.exp(-t * decay) * .5
def chip(note, length, duty=.25, vib=0.0, a=.002, r=.04):
    n = T(length); f = hz(note) * (1 + vib * np.sin(2 * np.pi * 6 * tt(n)) * np.clip(tt(n) / .15 - .3, 0, 1))
    return pulse(f, n, duty) * adsr(n, a, .05, .85, r) * .22
def fm_bell(note, length=1.2, idx=3.0, ratio=3.5, decay=3):
    n = T(length); t = tt(n); f = hz(note)
    mod = np.sin(2 * np.pi * f * ratio * t) * idx * np.exp(-t * decay * 1.5)
    return np.sin(2 * np.pi * f * t + mod) * np.exp(-t * decay) * .4
def epiano(note, length=1.0):
    n = T(length); t = tt(n); f = hz(note)
    mod = np.sin(2 * np.pi * f * t) * 1.2 * np.exp(-t * 4)
    x = np.sin(2 * np.pi * f * t + mod) * np.exp(-t * 2.2) + .15 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 9)
    return x * adsr(n, .002, .3, .8, .15) * .4
def pad(notes, length, cutoff=1400, detune=.12, a=.4, r=.6):
    n = T(length); L = np.zeros(n); R = np.zeros(n)
    for nt in notes:
        for k, dv in enumerate((-detune, 0, detune)):
            x = saw_blep(hz(nt) * 2 ** (dv / 12), n, rng.random())
            if k == 0: L += x
            elif k == 2: R += x
            else: L += x * .6; R += x * .6
    e = adsr(n, a, .2, 1, r)
    return np.vstack([lp(L, cutoff), lp(R, cutoff)]) * e / (len(notes) * 2) * .7
def brass(note, length, cutoff=2600, scoop=True):
    n = T(length); t = tt(n); f = hz(note) * (1 - (.03 * np.exp(-t * 30) if scoop else 0))
    x = (saw_blep(f, n) + saw_blep(f * 1.003, n) + .5 * saw_blep(f * .5, n)) / 2.5
    env = adsr(n, .015, .12, .75, .08)
    y = sweep_lp(x, 400, cutoff, .5, 12) if length < .6 else lp(x, cutoff)
    return sat(y * env, 1.3) * .5
def choir(notes, length, a=.3, r=.5):
    """dark 'ahh' pad: pulse through vowel formants"""
    n = T(length); out = np.zeros(n)
    for nt in notes:
        f = hz(nt); x = pulse(f * (1 + .004 * np.sin(2 * np.pi * 5 * tt(n))), n, .5) + saw_blep(f * 1.004, n)
        out += bp(x, 650, 1100) * 1.0 + bp(x, 2400, 2900) * .3
    return out * adsr(n, a, .2, 1, r) / len(notes) * .45
def vox(note, length, vowel='a', a=.004, r=.05):
    """vocal-chop style 'hey/ah' for jersey club: buzz through two formants with a quick pitch flick"""
    F = {'a': (800, 1200), 'e': (500, 1900), 'o': (500, 850), 'i': (320, 2300)}[vowel]
    n = T(length); t = tt(n); f = hz(note) * (1 + .06 * np.exp(-t * 40))
    x = saw_blep(f, n) * .7 + pulse(f, n, .3) * .3
    y = bp(x, F[0] * .8, F[0] * 1.25) + .7 * bp(x, F[1] * .85, F[1] * 1.2) + .15 * hp(noise(n), 5000) * np.exp(-t * 60)
    return sat(y * adsr(n, a, .08, .8, r), 1.5) * .6

# ---------- sound effects ----------
def riser(length=2.0, f0=300, f1=6000, tone=True):
    n = T(length); t = tt(n); k = t / length
    nz = noise(n); out = np.zeros(n); steps = 40; edges = np.linspace(0, n, steps + 1).astype(int)
    for i in range(steps):
        a, b = edges[i], edges[i + 1]; fc = f0 * (f1 / f0) ** (i / steps)
        out[a:b] = bp(nz[max(0, a - 2000):b], fc * .7, fc * 1.4)[-(b - a):]
    out *= k ** 1.5
    if tone: out += saw_blep(110 * 2 ** (k * 3), n) * .15 * k ** 2
    return out * .6
def whoosh(length=.45, up=True):
    n = T(length); t = tt(n); k = t / length; env = np.sin(np.pi * k) ** 2
    nz = noise(n); out = np.zeros(n); steps = 20; edges = np.linspace(0, n, steps + 1).astype(int)
    for i in range(steps):
        a, b = edges[i], edges[i + 1]; fc = (400 * 12 ** (i / steps)) if up else (5000 / 12 ** (i / steps))
        out[a:b] = bp(nz[max(0, a - 1500):b], fc * .6, fc * 1.6)[-(b - a):]
    return out * env * .7
def impact(length=2.2):
    n = T(length); t = tt(n)
    boom = np.sin(phase(32 + 90 * np.exp(-t * 12), n)) * np.exp(-t * 2.2)
    crack = bp(noise(n), 800, 9000) * np.exp(-t * 14)
    return sat(boom * 1.2 + crack * .5, 1.6) * .9
def snap(length=.05):
    n = T(length); t = tt(n); return bp(noise(n), 1500, 9000) * np.exp(-t * 160) * .6
def ding(note='E6', length=.8):
    n = T(length); t = tt(n); f = hz(note)
    return (np.sin(2 * np.pi * f * t) + .4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 8)) * np.exp(-t * 5) * .3
def tape_stop(x, length=.5):
    """slow a stereo/mono buffer to a stop (used before drops)"""
    n = x.shape[-1]; m = T(length); rate = np.linspace(1, 0, m) ** 1.2
    pos = np.concatenate([np.cumsum(rate), np.zeros(0)]); pos = pos[pos < n - 1]
    if x.ndim == 1: return np.interp(pos, np.arange(n), x)
    return np.vstack([np.interp(pos, np.arange(n), c) for c in x])

# ---------- mixing ----------
def reverb_ir(length=2.0, decay=2.8, tone=6000, predelay=.015):
    n = T(length); t = tt(n)
    L = lp(noise(n), tone) * np.exp(-t * decay); R = lp(noise(n), tone) * np.exp(-t * decay)
    pd = T(predelay); L = np.concatenate([np.zeros(pd), L])[:n]; R = np.concatenate([np.zeros(pd), R])[:n]
    return np.vstack([L, R]) / np.sqrt(np.sum(L ** 2) + 1e-9) * .5
class Mix:
    def __init__(s, seconds):
        s.n = T(seconds); s.bus = {}
    def _b(s, name):
        if name not in s.bus: s.bus[name] = np.zeros((2, s.n))
        return s.bus[name]
    def add(s, x, at, gain=1.0, pan=0.0, bus='main'):
        b = s._b(bus); i = T(at)
        if i >= s.n: return
        x = np.asarray(x)
        if x.ndim == 1:
            l, r = np.cos((pan + 1) * np.pi / 4) * 1.414, np.sin((pan + 1) * np.pi / 4) * 1.414; x = np.vstack([x * l, x * r])
        if i < 0: x = x[:, -i:]; i = 0
        j = min(s.n, i + x.shape[1]); b[:, i:j] += x[:, :j - i] * gain
    def sidechain(s, bus, times, depth=.7, release=.18, attack=.004):
        if bus not in s.bus: return
        g = np.ones(s.n); t = tt(T(release * 3))
        shape = 1 - depth * np.where(t < attack, t / attack, np.exp(-(t - attack) / (release / 3)))
        for at in times:
            i = T(at); j = min(s.n, i + len(shape)); g[i:j] = np.minimum(g[i:j], shape[:j - i])
        s.bus[bus] *= g
    def fx_reverb(s, bus, wet=.25, length=2.0, decay=2.8, tone=6000, send_to='main'):
        if bus not in s.bus: return
        ir = reverb_ir(length, decay, tone); x = s.bus[bus]
        w = np.vstack([signal.fftconvolve(x[0], ir[0])[:s.n], signal.fftconvolve(x[1], ir[1])[:s.n]])
        s._b(send_to); s.bus[send_to] += w * wet
    def render(s, bus_gain=None, master_drive=1.3, target_peak=.89, lufsish=-10.0):
        bus_gain = bus_gain or {}
        out = sum(b * bus_gain.get(k, 1.0) for k, b in s.bus.items())
        out = hp(out, 28, 2)
        out = out / (np.abs(out).max() + 1e-9)
        out = sat(out, master_drive) if master_drive else out
        # loudness: peak-normalize, then push into a soft clipper until RMS reaches the target (at most +8 dB of push)
        out = out / (np.abs(out).max() + 1e-9)
        tgt = 10 ** (lufsish / 20); g = 1.0
        for _ in range(12):
            y = np.tanh(out * g) / np.tanh(g)
            r = np.sqrt(np.mean(y ** 2))
            if r >= tgt or g > 2.5: break
            g *= 1.15
        out = y * target_peak
        return out
def write_wav(path, x):
    x = np.clip(x, -1, 1); y = (x.T * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y.tobytes())
