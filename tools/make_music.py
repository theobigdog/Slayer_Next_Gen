"""Composes and renders SLAYER's music into assets/music/*.ogg.

Every note is written below and synthesized here (no samples), so the music is all our own,
under the same CC BY-NC-SA 4.0 licence as the rest of the game's art and writing.

The game only plays the .ogg files, so players never need any of this. To change the music:
    pip install numpy soundfile          (a dev-only extra, not in requirements.txt)
    python tools\\make_music.py           (renders every song)
    python tools\\make_music.py tavern    (just one)
then play the game, or open the .ogg files in any music player.

How a song is written (see SONGS at the bottom):
    "bpm", "beats" per bar, "steps" per beat (2 = eighth notes; a 6/8 jig is 2 beats of 3 steps),
    "bars", and its parts. Each part has an instrument, a volume, a pan (-1 left .. 1 right) and
    "bars": one string per bar, repeated in order to fill the song. Each token is one step:
        d5 = a note (also f#4, bb3)   d3+a3 = a chord   - = keep holding   . = rest
        a "!" on the end = accent, a "'" = soft
    Drum letters: k kick, b bodhran (frame drum), x its rim tap, s snare, h hat, t low tom, g gong,
    c clinking glasses, w brush, p and q timpani (on D and A).
Looping songs are exactly their bars long; note tails and the reverb wrap round to the start,
so the loop has no seam.
"""
import sys
from pathlib import Path

import numpy as np

try:
    import soundfile
except ImportError:
    sys.exit('This needs soundfile to write .ogg files:  pip install numpy soundfile')

RATE = 32000
OUT = Path(__file__).resolve().parent.parent / 'assets' / 'music'
rng = np.random.default_rng(1349)

NOTE = {'c': 0, 'd': 2, 'e': 4, 'f': 5, 'g': 7, 'a': 9, 'b': 11}


def midi(tok):
    pc, i = NOTE[tok[0]], 1
    if tok[i:i + 1] == '#':
        pc, i = pc + 1, i + 1
    elif tok[i:i + 1] == 'b' and len(tok) > i + 1:
        pc, i = pc - 1, i + 1
    return 12 * (int(tok[i:]) + 1) + pc


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# ---------- instruments: each returns a mono note as a numpy array ----------

def envelope(n, attack, release_n, hold_n):
    env = np.ones(n)
    a = max(int(attack * RATE), 1)
    env[:a] = np.linspace(0, 1, a) if a < n else np.linspace(0, 1, n)[:a]
    if release_n > 0 and hold_n < n:
        env[hold_n:] *= np.linspace(1, 0, n - hold_n)
    return env


def additive(f, dur, weights, attack=0.02, release=0.12, vib=(5.5, 0.0, 0.0), bright=None, scoop=None):
    """A sum of harmonics. vib = (rate Hz, depth, delay s): vibrato that swells in after the delay.
    scoop = (how flat, seconds): the note starts that much flat and slides up into tune."""
    hold = int(dur * RATE)
    n = hold + int(release * RATE)
    t = np.arange(n) / RATE
    rate, depth, delay = vib
    swell = np.clip((t - delay) / 0.3, 0, 1) if depth else 0
    inst_f = f * (1 + depth * swell * np.sin(2 * np.pi * rate * t + rng.uniform(0, 6)))
    if scoop:
        inst_f = inst_f * (1 - scoop[0] * np.clip(1 - t / scoop[1], 0, 1) ** 2)
    phase = 2 * np.pi * np.cumsum(inst_f) / RATE
    out = np.zeros(n)
    for k, w in enumerate(weights, start=1):
        if f * k > RATE * 0.45 or w == 0:
            continue
        part = w * np.sin(k * phase)
        if bright is not None:
            part *= bright ** (k - 1)
        out += part
    return out * envelope(n, attack, n - hold, hold)


def fiddle(f, dur, vel):
    w = [1 / k * (1.4 if 3 <= k <= 6 else 1.0) for k in range(1, 16)]
    note = additive(f, dur, w, attack=0.035, release=0.1, vib=(5.8, 0.006, 0.18))
    bow = rng.normal(0, 1, len(note))
    bow = np.convolve(bow, np.ones(6) / 6, 'same') * 0.04 * envelope(len(note), 0.02, 0, len(note))
    return (note * 0.35 + bow) * vel


def whistle(f, dur, vel):
    note = additive(f, dur, [1, 0.12, 0.05], attack=0.03, release=0.08, vib=(6.0, 0.004, 0.25))
    breath = np.convolve(rng.normal(0, 1, len(note)), np.ones(4) / 4, 'same') * 0.05
    return (note * 0.5 + breath * envelope(len(note), 0.03, 0, len(note))) * vel


def drone(f, dur, vel):
    # a reedy bagpipe-ish drone: strong odd harmonics, nasal and buzzy
    w = [1, 0.45, 0.8, 0.3, 0.55, 0.2, 0.35, 0.12, 0.2, 0.08]
    return additive(f, dur, w, attack=0.15, release=0.3, vib=(4.0, 0.0015, 0.0)) * 0.2 * vel


def brass(f, dur, vel):
    hold = int(dur * RATE)
    n = hold + int(0.15 * RATE)
    t = np.arange(n) / RATE
    bright = 0.35 + 0.45 * np.clip(t / 0.06, 0, 1) - 0.15 * np.clip((t - 0.06) / 0.3, 0, 1)
    w = [1 / k for k in range(1, 14)]
    return additive(f, dur, w, attack=0.025, release=0.15, vib=(5.0, 0.003, 0.3), bright=bright) * 0.4 * vel


def strings(f, dur, vel):
    out = 0
    for cents in (-7, 0, 7):
        out = out + additive(f * 2 ** (cents / 1200), dur, [1 / k for k in range(1, 10)], attack=0.25, release=0.5,
                             vib=(5.0, 0.004, 0.2))
    return out * 0.12 * vel


def choir(f, dur, vel):
    out = 0
    for cents in (-9, 0, 9):
        out = out + additive(f * 2 ** (cents / 1200), dur, [0.8, 0.7, 0.55, 0.35, 0.18, 0.1, 0.06], attack=0.4,
                             release=0.7, vib=(5.2, 0.006, 0.0))
    return out * 0.14 * vel


def bell(f, dur, vel):
    n = int(2.5 * RATE)
    t = np.arange(n) / RATE
    out = np.zeros(n)
    for ratio, amp, decay in ((1, 1, 1.2), (2.76, 0.5, 2.5), (5.4, 0.3, 5), (8.93, 0.15, 9)):
        out += amp * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t * decay)
    out[:60] *= np.linspace(0, 1, 60)
    return out * 0.25 * vel


def pluck(f, dur, vel, decay=0.996, bright=0.7, seconds=None):
    """A plucked string (Karplus-Strong), worked out a whole period at a time."""
    n = int((seconds or max(dur + 0.3, 0.6)) * RATE)
    p = max(int(RATE / f), 2)
    burst = rng.uniform(-1, 1, p)
    burst = burst * bright + np.convolve(burst, [0.5, 0.5], 'same') * (1 - bright)
    out = np.zeros(n + p)
    out[:p] = burst
    for start in range(p, n + p, p):
        prev = out[start - p:start]
        nxt = 0.5 * (prev + np.roll(prev, 1)) * decay
        end = min(start + p, n + p)
        out[start:end] = nxt[:end - start]
    out = out[:n]
    fade = min(int(0.05 * RATE), n)
    out[-fade:] *= np.linspace(1, 0, fade)
    return out * 0.6 * vel


def lute(f, dur, vel):
    return pluck(f, dur, vel, decay=0.995, bright=0.55)


def cello_pizz(f, dur, vel):
    return pluck(f, dur, vel, decay=0.998, bright=0.3)


def reed(f, dur, vel):
    """A wheezy, sleazy clarinet that scoops up into every note."""
    w = [1, 0.08, 0.55, 0.06, 0.35, 0.05, 0.22, 0.04, 0.12, 0.03, 0.07]
    note = additive(f, dur, w, attack=0.06, release=0.15, vib=(4.5, 0.008, 0.25), scoop=(0.04, 0.12))
    breath = np.convolve(rng.normal(0, 1, len(note)), np.ones(5) / 5, 'same') * 0.035
    return (note * 0.4 + breath * envelope(len(note), 0.06, 0, len(note))) * vel


def squeezebox(f, dur, vel):
    """A tired old accordion: three reeds a little out of tune with each other."""
    w = [1, 0.7, 0.5, 0.45, 0.3, 0.25, 0.18, 0.12, 0.1, 0.07]
    out = 0
    for cents in (-12, 0, 14):
        out = out + additive(f * 2 ** (cents / 1200), dur, w, attack=0.03, release=0.08)
    return out * 0.11 * vel


def tuba(f, dur, vel):
    return additive(f, dur, [1, 0.6, 0.32, 0.18, 0.1, 0.05], attack=0.04, release=0.12,
                    vib=(4.0, 0.002, 0.3), scoop=(0.025, 0.06)) * 0.6 * vel


def honky(f, dur, vel):
    """A beat-up tavern piano: two strings per note, neither of them in tune."""
    secs = max(dur + 0.5, 1.0)
    a = pluck(f * 2 ** (-10 / 1200), dur, vel, decay=0.997, bright=0.85, seconds=secs)
    b = pluck(f * 2 ** (13 / 1200), dur, vel, decay=0.997, bright=0.85, seconds=secs)
    return (a + b) * 0.55


def harp(f, dur, vel):
    """A harp: a bright pluck that rings a long time."""
    return pluck(f, dur, vel, decay=0.9985, bright=0.5, seconds=max(dur + 1.2, 1.6)) * 0.8


def xylo(f, dur, vel):
    """A xylophone: a hard mallet on a wooden bar, dry and plinky."""
    n = int(0.5 * RATE)
    t = np.arange(n) / RATE
    out = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * d) for r, a, d in ((1, 1, 11), (3.93, 0.4, 28), (9.2, 0.15, 60)))
    out[:30] *= np.linspace(0, 1, 30)
    return out * 0.4 * vel


def saw(f, dur, vel):
    """Section strings played hard and short (the wolves' sawing): quick to speak, unlike the slow 'strings' pad."""
    out = 0
    for cents in (-6, 6):
        out = out + additive(f * 2 ** (cents / 1200), dur, [1 / k for k in range(1, 14)], attack=0.012, release=0.07,
                             vib=(5.5, 0.002, 0.15))
    return out * 0.16 * vel


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, 'same')


def drum(kind, vel):
    length = {'k': 0.4, 'b': 0.45, 'x': 0.06, 's': 0.25, 'h': 0.06, 't': 0.6, 'g': 3.5, 'c': 0.7,
              'w': 0.3, 'p': 1.6, 'q': 1.6}.get(kind, 0.2)
    n = int(length * RATE)
    t = np.arange(n) / RATE
    noise = rng.normal(0, 1, n)
    hiss = np.diff(noise, prepend=0)  # high-passed
    if kind == 'k':
        ph = 2 * np.pi * np.cumsum(45 + 110 * np.exp(-t * 30)) / RATE
        out = np.sin(ph) * np.exp(-t * 8) + noise * 0.1 * np.exp(-t * 150)
    elif kind == 'b':  # bodhran: a deep, skin-y thump
        ph = 2 * np.pi * np.cumsum(70 + 60 * np.exp(-t * 25)) / RATE
        out = np.sin(ph) * np.exp(-t * 7) * 0.9 + np.convolve(noise, np.ones(8) / 8, 'same') * 0.3 * np.exp(-t * 30)
    elif kind == 'x':  # the rim of the frame drum: a dry tap
        out = hiss * 0.25 * np.exp(-t * 60) + np.sin(2 * np.pi * 900 * t) * 0.2 * np.exp(-t * 80)
    elif kind == 's':
        out = np.sin(2 * np.pi * 190 * t) * 0.45 * np.exp(-t * 22) + hiss * 0.35 * np.exp(-t * 16)
    elif kind == 'h':
        out = hiss * 0.18 * np.exp(-t * 70)
    elif kind == 't':  # a big low war drum
        ph = 2 * np.pi * np.cumsum(55 + 40 * np.exp(-t * 10)) / RATE
        out = np.sin(ph) * np.exp(-t * 5) + np.convolve(noise, np.ones(12) / 12, 'same') * 0.25 * np.exp(-t * 20)
    elif kind == 'g':  # gong: a wash of clashing partials
        out = np.zeros(n)
        for ratio, amp in ((1, 1), (1.47, 0.7), (2.09, 0.6), (2.56, 0.5), (3.2, 0.4), (4.1, 0.3)):
            out += amp * np.sin(2 * np.pi * 82 * ratio * t + rng.uniform(0, 6)) * np.exp(-t * (0.8 + ratio * 0.3))
        out += hiss * 0.15 * np.exp(-t * 3)
        out[:80] *= np.linspace(0, 1, 80)
        out *= 0.35
    elif kind == 'c':  # two glasses clinking somewhere across the room
        out = np.zeros(n)
        for delay, amp in ((0.0, 1.0), (rng.uniform(0.05, 0.12), 0.5)):
            f0 = rng.uniform(2200, 3200)
            tt = np.clip(t - delay, 0, None)
            ring = sum(a * np.sin(2 * np.pi * f0 * r * tt) * np.exp(-tt * d)
                       for r, a, d in ((1, 1, 9), (2.41, 0.5, 14), (3.93, 0.3, 22)))
            out += amp * ring * (t >= delay)
        out *= 0.12
    elif kind in 'pq':  # timpani: p on D, q on the A below
        f0 = 73.4 if kind == 'p' else 55.0
        out = sum(a * np.sin(2 * np.pi * f0 * r * t) * np.exp(-t * d) for r, a, d in ((1, 1, 2.2), (1.5, 0.5, 3), (1.99, 0.3, 4)))
        out += lowpass(noise, 6) * 0.3 * np.exp(-t * 40)
        out *= 0.9
    elif kind == 'w':  # a brush swished across the snare
        env = np.clip(t / 0.03, 0, 1) * np.exp(-t * 14)
        out = lowpass(hiss, 3) * 0.3 * env
    else:
        out = np.zeros(n)
    return out * vel


INSTRUMENTS = {'fiddle': fiddle, 'whistle': whistle, 'drone': drone, 'brass': brass, 'strings': strings,
               'choir': choir, 'bell': bell, 'lute': lute, 'pizz': cello_pizz, 'reed': reed,
               'squeezebox': squeezebox, 'tuba': tuba, 'honky': honky, 'harp': harp, 'xylo': xylo, 'saw': saw}


# ---------- putting a song together ----------

def parse(part, bars, bar_steps, transpose=0):
    events, last, drums = [], None, part['inst'] == 'drums'
    shift = 12 * part.get('oct', 0) + transpose
    for b in range(bars):
        tokens = part['bars'][b % len(part['bars'])].split()
        for s in range(bar_steps):
            tok = tokens[s] if s < len(tokens) else '.'
            step = b * bar_steps + s
            if tok == '-':
                if last is not None:
                    last[1] += 1
                continue
            if tok == '.':
                last = None
                continue
            vel = 0.75
            if tok.endswith('!'):
                vel, tok = 1.0, tok[:-1]
            elif tok.endswith("'"):
                vel, tok = 0.45, tok[:-1]
            pitches = tok.split('+') if drums else [midi(p) + shift for p in tok.split('+')]
            last = [step, 1, pitches, vel]
            events.append(last)
    return events


def reverb(buf, seconds, wet, looping):
    """A smooth hall: the sound convolved with a decaying burst of noise (circular for a loop: no seam)."""
    n = len(buf)
    ir_n = int(seconds * RATE)
    t = np.arange(ir_n) / RATE
    out = buf.copy()
    for ch in range(2):
        ir = rng.normal(0, 1, ir_n) * np.exp(-t * 6.9 / seconds)
        ir = np.convolve(ir, np.ones(6) / 6, 'same')   # darker tail
        ir[:int(0.015 * RATE)] = 0                      # a little pre-delay
        ir /= np.sqrt((ir ** 2).sum())
        size = n if looping else n + ir_n
        spec = np.fft.rfft(buf[:, ch], size) * np.fft.rfft(ir, size)
        wet_sig = np.fft.irfft(spec, size)[:n]
        out[:, ch] += wet * wet_sig
    return out


def wobbly(n, sr, every, low=0.0, high=1.0):
    """A slow random wander between low and high, a new target every `every` seconds."""
    points = rng.uniform(low, high, int(n / sr / every) + 3)
    return np.interp(np.arange(n) / sr / every, np.arange(len(points)), points)


def murmur(n, voices=7, syllable=0.16, pitch=(85, 165), talking=True):
    """A room full of low talk: pitched 'voices' babbling through shifting vowels, no words in them.
    syllable: seconds each; talking=False: they never stop to listen (Happy's runes).
    Worked out at 8 kHz (talk has nothing up high), then stretched to RATE. Loops: the end fades into the start."""
    sr, fade = 8000, 8000
    m = n * sr // RATE + fade
    t = np.arange(m) / sr
    vowels = np.array([(730, 1090), (530, 1840), (300, 870), (570, 840), (440, 1020), (660, 1700)])
    out = np.zeros((m, 2))
    for _ in range(voices):
        f0 = rng.uniform(*pitch) * (1 + 0.07 * (wobbly(m, sr, 0.12) - 0.5) + 0.05 * (wobbly(m, sr, 1.5) - 0.5))
        phase = 2 * np.pi * np.cumsum(f0) / sr
        syll = rng.integers(0, len(vowels), int(m / sr / syllable) + 3)
        pos = t / syllable
        f1 = np.interp(pos, np.arange(len(syll)), vowels[syll, 0])
        f2 = np.interp(pos, np.arange(len(syll)), vowels[syll, 1])
        voice = np.zeros(m)
        for k in range(1, 18):
            fk = k * f0
            amp = np.exp(-((fk - f1) / 140) ** 2) + 0.6 * np.exp(-((fk - f2) / 220) ** 2) + 0.15 / k
            voice += amp * np.sin(k * phase) * (fk < sr * 0.45)
        # syllables, and a voice that talks for a few seconds then listens for a few
        gate = np.clip(np.sin(np.pi * pos) ** 2 * 1.3, 0, 1) * (wobbly(m, sr, 0.16, 0.2, 1.0))
        talks = np.clip((wobbly(m, sr, 2.5, -1, 1.6)) * 3, 0, 1) if talking else 1
        voice *= gate * talks
        pan = rng.uniform(-0.8, 0.8)
        out[:, 0] += voice * np.sqrt(0.5 * (1 - pan))
        out[:, 1] += voice * np.sqrt(0.5 * (1 + pan))
    ramp = np.linspace(0, 1, fade)[:, None]
    out[:fade] = out[:fade] * np.sqrt(ramp) + out[-fade:] * np.sqrt(1 - ramp)   # the tail fades into the start
    out = out[:m - fade]
    big = np.stack([np.interp(np.arange(n) * sr / RATE, np.arange(len(out)), out[:, ch]) for ch in range(2)], 1)
    big = np.stack([lowpass(big[:, ch], 3) for ch in range(2)], 1)
    return big / np.sqrt((big ** 2).mean()) * 0.17


def wow(buf, cents, cycles):
    """A seasick wobble in pitch, like a warped old record: `cycles` slow wobbles per loop (so it still loops)."""
    n = len(buf)
    i = np.arange(n)
    depth = 2 ** (cents / 1200) - 1
    pos = (i + depth * n / (2 * np.pi * cycles) * np.sin(2 * np.pi * cycles * i / n)) % n
    return np.stack([np.interp(pos, np.arange(n + 1), np.append(buf[:, ch], buf[0, ch])) for ch in range(2)], 1)


def render(song):
    spb = song.get('steps', 2)
    bar_steps = song.get('beats', 4) * spb
    step_s = 60.0 / song['bpm'] / spb
    looping = song.get('loop', True)
    frames = int(round(song['bars'] * bar_steps * step_s * RATE))
    n = frames if looping else frames + int(song.get('tail', 3.5) * RATE)
    buf = np.zeros((n, 2))
    for part in song['parts']:
        vol, pan = part.get('vol', 0.5), part.get('pan', 0.0)
        gains = vol * np.sqrt(0.5 * (1 - pan)), vol * np.sqrt(0.5 * (1 + pan))
        sway = part.get('sway', 0.0)  # seconds of drunken slop in when each note lands
        for step, length, pitches, vel in parse(part, song['bars'], bar_steps, song.get('transpose', 0)):
            start = int(round((step * step_s + abs(rng.normal(0, sway))) * RATE))
            for p in pitches:
                if part['inst'] == 'drums':
                    note = drum(p, vel)
                else:
                    note = INSTRUMENTS[part['inst']](hz(p), length * step_s, vel)
                idx = (start + np.arange(len(note)))
                if looping:
                    idx %= n
                else:
                    keep = idx < n
                    idx, note = idx[keep], note[keep]
                np.add.at(buf[:, 0], idx, note * gains[0])
                np.add.at(buf[:, 1], idx, note * gains[1])
    if song.get('murmur'):
        buf += murmur(n) * song['murmur']
    level = 0.17 * song.get('level', 1.0)   # how loud it sits; 1 = like every other song
    if song.get('extra'):   # sounds that aren't notes (giggles, scratching, Happy's runes), at a set level over the music
        buf *= level / np.sqrt((buf ** 2).mean())
        buf += song['extra'](n, looping)
    buf = reverb(buf, song.get('reverb', 1.6), song.get('wet', 0.25), looping)
    if song.get('wow'):
        buf = wow(buf, *song['wow'])
    if song.get('grit'):    # driven hard, like an amp turned up too far
        buf = np.tanh(buf / np.sqrt((buf ** 2).mean()) * 0.17 * song['grit'])
    # Match loudness between songs, then a soft limiter so peaks round off instead of clipping.
    if not song.get('fixed'):   # (the basin's two halves keep the level set before the reverb, so they match)
        buf *= level / np.sqrt((buf ** 2).mean())
    buf = np.tanh(buf * 1.2) / 1.2
    return buf.astype(np.float32)


# ---------- the songs (all original) ----------

TAVERN_TUNE = [
    # A part
    "d5 e5 f#5 a5 - f#5", "g5 f#5 e5 d5 - b4", "a4 d5 d5 f#5 e5 d5", "e5 - - a4 - -",
    "d5 e5 f#5 a5 - b5", "a5 f#5 d5 e5 - f#5", "g5 e5 c5 d5 b4 a4", "d5 - - d5 - -",
    # B part
    "a5 - b5 a5 f#5 d5", "a5 - b5 a5 - f#5", "g5 - a5 g5 e5 c5", "g5 - a5 g5 - e5",
    "f#5 e5 d5 e5 f#5 a5", "g5 f#5 e5 c5 - e5", "d5 f#5 e5 d5 b4 a4", "d5 - - - - .",
]
TAVERN_CHORDS = ["d3+a3", "g3+d4", "d3+a3", "a2+e3", "d3+a3", "d3+a3", "c3+g3", "d3+a3",
                 "d3+a3", "d3+a3", "c3+g3", "c3+g3", "d3+a3", "c3+g3", "d3+a3", "d3+a3"]

# Inside the Devil's Brew: A minor, a drunk 3/4 waltz.
SEEDY_CHORDS = ['Am', 'Am', 'E7', 'E7', 'Am', 'Am', 'Dm', 'E7', 'Dm', 'Dm', 'Am', 'Am', 'F', 'E7', 'Am', 'E7']
SEEDY_BASS = {'Am': ('a1', 'e2'), 'E7': ('e2', 'b1'), 'Dm': ('d2', 'a1'), 'F': ('f1', 'c2')}
SEEDY_VOICING = {'Am': 'a3+c4+e4', 'E7': 'g#3+b3+d4', 'Dm': 'a3+d4+f4', 'F': 'a3+c4+f4'}
SEEDY_TUNE = [
    "e4 - a4 - b4 c5", "b4 - a4 - - .", "g#4 - b4 - d5 -", "c5 b4 - - . .",
    "e4 - a4 - b4 c5", "e5 - d5 c5 b4 a4", "f4 - a4 - d5 c5", "b4 - g#4 - e4 .",
    "d5 - f5 - e5 d5", "c5 - a4 - - .", "c5 - e5 - d5 c5", "b4 - a4 - - .",
    "a4 - c5 - f5 e5", "d5 - b4 - g#4 -", "a4 - - e4 a4 -", "b4 - g#4 - e4 -",
]
REST3 = '. . . . . .'

SONGS = {
    # Happy's grimy tavern, from the moment the party walks in: a lurching drunk waltz on a wheezy clarinet,
    # an accordion and a tuba, then a busted piano, under a room full of muttering and clinking glasses.
    # The whole thing wobbles like a warped record.
    'seedy': {
        'bpm': 80, 'beats': 3, 'steps': 2, 'bars': 32, 'wet': 0.3, 'reverb': 1.8, 'murmur': 0.22, 'wow': (9, 24),
        'parts': [
            {'inst': 'reed', 'vol': 0.85, 'pan': 0.2, 'sway': 0.015, 'bars': SEEDY_TUNE + [REST3] * 16},
            {'inst': 'honky', 'vol': 0.75, 'pan': -0.15, 'sway': 0.02, 'bars': [REST3] * 16 + SEEDY_TUNE},
            {'inst': 'reed', 'vol': 0.35, 'pan': 0.3, 'oct': -1, 'sway': 0.015, 'bars': [REST3] * 16 + SEEDY_TUNE},
            {'inst': 'tuba', 'vol': 0.8, 'pan': 0.0, 'sway': 0.01,
             'bars': [f"{SEEDY_BASS[c][i % 2]}! - . . . ." for i, c in enumerate(SEEDY_CHORDS)]},
            {'inst': 'squeezebox', 'vol': 0.6, 'pan': -0.35, 'sway': 0.02,
             'bars': [f". . {SEEDY_VOICING[c]} . {SEEDY_VOICING[c]}' ." for c in SEEDY_CHORDS]},
            {'inst': 'drums', 'vol': 0.45, 'pan': 0.1, 'bars': [". . w . w' .", ". . w . w' w'"]},
            {'inst': 'drums', 'vol': 0.6, 'pan': 0.5,
             'bars': [REST3, ". . . . c' .", REST3, REST3, ". c' . . . .", REST3, REST3, REST3, ". . . c .",
                      REST3, REST3]},
        ]},

    # The title and the party screens (and the loot after the Happy fight): a rowdy jig.
    # D mixolydian, 6/8, fiddle with a bagpipe drone, a lute strumming and a bodhran.
    'tavern': {
        'bpm': 116, 'beats': 2, 'steps': 3, 'bars': 32, 'wet': 0.18, 'reverb': 1.2,
        'parts': [
            {'inst': 'fiddle', 'vol': 0.9, 'pan': 0.15, 'bars': TAVERN_TUNE},
            {'inst': 'whistle', 'vol': 0.45, 'pan': -0.3, 'oct': 1,
             'bars': ['. . . . . .'] * 16 + TAVERN_TUNE[8:] + TAVERN_TUNE[8:]},
            {'inst': 'lute', 'vol': 0.5, 'pan': -0.4,
             'bars': [f"{c} . {c}' {c} . {c}'" for c in TAVERN_CHORDS]},
            {'inst': 'drone', 'vol': 0.5, 'pan': 0.0, 'bars': ["d2+a2 - - - - -"]},
            {'inst': 'drums', 'vol': 0.6, 'pan': 0.1,
             'bars': ["b! . x b . x", "b . x b x x", "b! . x b . x", "b x x b! x x"]},
        ]},

    # Down in the dungeon between fights: dripping, creaking, something breathing in the dark.
    # D phrygian, slow.
    'dungeon': {
        'bpm': 66, 'beats': 4, 'steps': 2, 'bars': 16, 'wet': 0.45, 'reverb': 3.0,
        'parts': [
            {'inst': 'strings', 'vol': 0.8, 'pan': -0.1, 'bars': [
                "d3+a3 - - - - - - -", "d3+a3 - - - - - - -", "eb3+bb3 - - - - - - -", "d3+a3 - - - - - - -",
                "c3+g3 - - - - - - -", "bb2+f3 - - - - - - -", "eb3+bb3 - - - - - - -", "d3+a3 - - - - - - -"]},
            {'inst': 'drone', 'vol': 0.35, 'bars': ["d1+a1 - - - - - - -"]},
            {'inst': 'pizz', 'vol': 0.7, 'pan': 0.25, 'bars': [
                "d3 . . . . . a2 .", ". . f3 . . e3 . .", "eb3 . . . . . bb2 .", "d3 . . . . . . .",
                "c3 . . . . . g2 .", "bb2 . . d3 . . . .", "eb3 . . . d3 . c#3 .", "d3 . . . . . . ."]},
            {'inst': 'fiddle', 'vol': 0.45, 'pan': 0.2, 'oct': -1, 'bars': [
                ". . . . . . . .", ". . . . . . . .", ". . . . . . . .", ". . . . . . . .",
                ". . . . . . . .", ". . . . . . . .", ". . . . . . . .", ". . . . . . . .",
                "a4 - - - bb4 - - -", "a4 - g4 - f4 - - -", "g4 - - - f4 - eb4 -", "d4 - - - - - - -",
                "e4 - - - f4 - - -", "d4 - - - bb3 - - -", "c4 - eb4 - d4 - c#4 -", "d4 - - - - - - ."]},
            {'inst': 'bell', 'vol': 0.4, 'pan': 0.6, 'bars': [
                ". . . . . . d6' .", ". . . . . . . .", ". . a5' . . . . .", ". . . . . . . .",
                ". . . . . f6' . .", ". . . . . . . .", ". eb6' . . . . . .", ". . . . . . . a5'"]},
            {'inst': 'drums', 'vol': 0.5, 'bars': [
                "t . . t' . . . .", ". . . . . . . .", "t . . t' . . . .", ". . . . . . . ."]},
        ]},

    # Every fight: a galloping war march. E minor.
    'battle': {
        'bpm': 152, 'beats': 4, 'steps': 2, 'bars': 16, 'wet': 0.16, 'reverb': 1.4,
        'parts': [
            {'inst': 'strings', 'vol': 1.0, 'pan': -0.2, 'bars': [
                "e2 e2 e3 e2 g2 e2 a2 b2", "e2 e2 e3 e2 g2 e2 b2 a2", "c3 c3 c4 c3 e3 c3 g2 c3", "d3 d3 d4 d3 f#3 d3 a2 d3",
                "e2 e2 e3 e2 g2 e2 a2 b2", "e2 e2 e3 e2 g2 e2 b2 a2", "c3 c3 c4 c3 a2 a2 a3 a2", "b2 b2 b3 b2 d#3 b2 f#3 b2"]},
            {'inst': 'brass', 'vol': 0.75, 'pan': 0.15, 'bars': [
                "e4+b4! - . . . . . .", ". . . . e4+b4 . g4+d5! -", "c4+g4! - . . . . . .", "d4+a4 - . . f#4+d5! - - -",
                "e4+b4! - . . . . . .", ". . . . e4+b4 . g4+d5! -", "a3+e4! - . . c4+e4 . . .", "b3+f#4! - - - d#4+f#4 - - -"]},
            {'inst': 'fiddle', 'vol': 0.75, 'pan': 0.3, 'bars': [
                ". . . . . . . .", ". . . . . . . .", ". . . . . . . .", ". . . . . . . .",
                ". . . . . . . .", ". . . . . . . .", ". . . . . . . .", ". . . . . . . .",
                "b5 - a5 g5 f#5 - e5 -", "g5 - f#5 e5 d#5 - b4 -", "e5 - f#5 g5 a5 - g5 -", "f#5 - - - a5 - - -",
                "b5 - a5 g5 f#5 - e5 -", "g5 - b5 - e6 - - -", "c6 - b5 a5 g5 - f#5 -", "d#5 - f#5 - b5 - - -"]},
            {'inst': 'drums', 'vol': 0.8, 'bars': [
                "k! h s h k k s h", "k h s h k k s s'", "k! h s h k k s h", "k h s h t t t t",
                "k! h s h k k s h", "k h s h k k s s'", "k! h s h k k s h", "s s s s t! . t! ."]},
        ]},

    # A fight won: a quick fiddle flourish and a brass hurrah.
    'victory': {
        'bpm': 140, 'beats': 4, 'steps': 2, 'bars': 2, 'loop': False, 'wet': 0.25,
        'parts': [
            {'inst': 'fiddle', 'vol': 0.8, 'bars': ["d5 e5 f#5 a5 d6 - - .", ". . . . . . . ."]},
            {'inst': 'brass', 'vol': 0.8, 'bars': [". . . . . . a4+d5+f#5! -", "a4+d5+f#5+a5! - - - - - - -"]},
            {'inst': 'drums', 'vol': 0.8, 'bars': ["k . . . s s s s", "k! . . . . . . ."]},
        ]},

    # A wipe: a doleful sag and a gong.
    'defeat': {
        'bpm': 72, 'beats': 4, 'steps': 2, 'bars': 2, 'loop': False, 'wet': 0.4, 'reverb': 2.5,
        'parts': [
            {'inst': 'brass', 'vol': 0.7, 'bars': ["a3 - - g3 - - f3 -", "e3 - - - - - - ."]},
            {'inst': 'strings', 'vol': 0.6, 'bars': ["d3+f3 - - - - - - -", "a2+c#3+e3 - - - - - - -"]},
            {'inst': 'drums', 'vol': 0.8, 'bars': ["t! . . . . . . .", "g . . . . . . ."]},
        ]},
}

# ---------- the songs added Nov 17 (Ted's notes) ----------

def arps(chords, pattern, steps):
    """A bar of broken chord per chord: pattern picks chord tones by index (0 = the lowest), '.' rests."""
    bars = []
    for c in chords:
        notes = c.split('+')
        bars.append(' '.join(notes[int(p)] if p != '.' else '.' for p in pattern.split()))
        assert len(pattern.split()) == steps
    return bars


def oompah(chords, low, high):
    """Tuba roots on the beat, the squeezebox chord off it: 'oom-pah oom-pah'."""
    return ([f"{low[c][0]}! . {low[c][1]} . {low[c][0]}! . {low[c][1]} ." for c in chords],
            [f". {high[c]} . {high[c]}' . {high[c]} . {high[c]}'" for c in chords])


# Happy's resurrection: D major, slow and tender, a harp rippling under a whistle, strings, a choir coming in,
# and under it all Happy muttering his runes.
RES_CHORDS = ['D', 'Bm', 'G', 'A', 'D', 'F#m', 'G', 'A', 'Bm', 'G', 'D', 'A', 'G', 'A', 'D', 'D']
RES_TRIADS = {'D': 'd3+a3+d4+f#4+a4', 'Bm': 'b2+f#3+b3+d4+f#4', 'G': 'g2+d3+g3+b3+d4', 'A': 'a2+e3+a3+c#4+e4',
              'F#m': 'f#2+c#3+f#3+a3+c#4'}
RES_PAD = {'D': 'd4+f#4+a4', 'Bm': 'd4+f#4+b4', 'G': 'd4+g4+b4', 'A': 'c#4+e4+a4', 'F#m': 'c#4+f#4+a4'}
RES_TUNE = ["f#5 - - - e5 - d5 -", "d5 - - - - - b4 -", "b4 - d5 - g5 - f#5 -", "e5 - - - - - . .",
            "f#5 - - - a5 - f#5 -", "e5 - - - c#5 - a4 -", "b4 - - - d5 - e5 -", "e5 - - - - - . .",
            "d5 - - - f#5 - b5 -", "a5 - - - g5 - d5 -", "f#5 - - - e5 - d5 -", "c#5 - - - - - e5 -",
            "d5 - - - b4 - d5 -", "e5 - - - f#5 - e5 -", "d5 - - - - - - -", ". . . . . . . ."]
REST4 = '. . . . . . . .'

# The loot, The Stash, the forge and the stat raises, until the party drops down the hole: a jolly oom-pah.
JOLLY_CHORDS = ['G', 'G', 'D', 'D', 'G', 'G', 'C', 'D', 'G', 'G', 'C', 'C', 'G', 'D', 'G', 'G']
JOLLY_LOW = {'G': ('g2', 'd2'), 'D': ('d2', 'a1'), 'C': ('c2', 'g1')}
JOLLY_HIGH = {'G': 'g3+b3+d4', 'D': 'f#3+a3+d4', 'C': 'g3+c4+e4'}
JOLLY_TUNE = ["d5 - b4 d5 g5 - d5 -", "b4 - g4 b4 d5 - - -", "c5 - a4 c5 f#5 - e5 -", "d5 - c5 - a4 - - -",
              "d5 - b4 d5 g5 - b5 -", "a5 g5 f#5 g5 d5 - - -", "e5 - g5 - c5 - e5 -", "a4 - f#4 - d4 - - -",
              "g5 - - f#5 g5 - d5 -", "b4 - d5 - g5 - - -", "e5 - - d5 e5 - g5 -", "c5 - e5 - g5 - - -",
              "b4 - d5 - g5 - b4 -", "a4 - c5 - f#5 - a5 -", "g5 - d5 - b4 - d5 -", "g5 - - - g4 - . ."]

# The Krazy Kobolds: E minor, a skittering xylophone and plucked bass, goofy but creepy, with a sneaky
# bassoon, a ghostly choir and giggling in the dark.
KOB_CHORDS = ['Em', 'Em', 'Am', 'B', 'Em', 'Em', 'C', 'B', 'Am', 'Am', 'Em', 'Em', 'C', 'B', 'Em', 'Em']
KOB_BASS = {'Em': "e2 . b2 . e2 . b2 .", 'Am': "a2 . e3 . a2 . e3 .", 'B': "b1 . f#2 . b1 . d#2 .",
            'C': "c2 . g2 . c2 . g2 ."}
KOB_PAD = {'Em': 'e4+g4+b4', 'Am': 'e4+a4+c5', 'B': 'd#4+f#4+b4', 'C': 'e4+g4+c5'}
KOB_TUNE = ["e5 . g5 . b5 . a#5 b5", "g5 . e5 . . . d#5 e5", "c6 . a5 . e5 . a5 c6", "b5 . . a5 f#5 . d#5 .",
            "e5 . g5 . b5 . a#5 b5", "e6 . b5 . g5 . e5 .", "e5 f5 e5 d#5 e5 . g5 .", "f#5 . d#5 . b4 . . .",
            "a5 . c6 . a5 . e5 .", "f5 . e5 . d#5 . e5 .", "g5 . b5 . e6 . b5 .", "g5 a5 g5 f#5 e5 . . .",
            "e5 . g5 . c6 . b5 .", "a5 . f#5 . d#5 . b4 .", "e5 . . . b4 . . .", "e5 g5 b5 e6 . . . ."]

# The wolves: D minor, driving and grim: low strings sawing away in sixteenths, horns, timpani, a choir.
WOLF_CHORDS = ['Dm', 'Dm', 'Bb', 'A', 'Dm', 'Dm', 'Gm', 'A', 'Bb', 'C', 'Dm', 'A', 'Gm', 'A', 'Dm', 'A']
WOLF_LOW = {'Dm': ('d2', 'f2', 'a2'), 'Bb': ('bb1', 'd2', 'f2'), 'A': ('a1', 'c#2', 'e2'), 'Gm': ('g1', 'bb1', 'd2'),
            'C': ('c2', 'e2', 'g2')}
WOLF_HIGH = {'Dm': 'd5+e5+f5+a5+d6', 'Bb': 'd5+f5+g5+bb5+d6', 'A': 'c#5+e5+g5+a5+c#6', 'Gm': 'd5+g5+a5+bb5+d6',
             'C': 'c5+e5+f5+g5+c6'}
WOLF_PAD = {'Dm': 'd4+f4+a4', 'Bb': 'd4+f4+bb4', 'A': 'c#4+e4+a4', 'Gm': 'd4+g4+bb4', 'C': 'e4+g4+c5'}
WOLF_HORNS = ["d4 - - - - - - - a3 - - - d4 - - -", "f4 - - - e4 - - - d4 - - - c#4 - - -",
              "d4 - - - - - - - bb3 - - - - - - -", "a3 - - - - - - - c#4 - - - e4 - - -",
              "a4 - - - - - - - f4 - - - d4 - - -", "a4 - - - bb4 - - - a4 - - - f4 - - -",
              "g4 - - - - - - - d4 - - - bb3 - - -", "a3 - - - c#4 - - - e4 - - - a4 - - -",
              "f4 - - - - - - - d4 - - - f4 - - -", "g4 - - - - - - - e4 - - - c4 - - -",
              "a4 - - - - - - - d5 - - - c5 - - -", "c#5 - - - - - - - - - - - . . . .",
              "bb4 - - - a4 - - - g4 - - - d4 - - -", "e4 - - - f4 - - - g4 - - - c#4 - - -",
              "d4 - - - - - - - - - - - - - - -", "a3 - - - - - - - c#4 - - - e4 - - -"]
REST16 = ' '.join(['.'] * 16)


def wolf_saw(c):
    r, third, fifth = WOLF_LOW[c]
    return ' '.join([f'{r}!', r, fifth, r, third, r, fifth, r] * 2)


def wolf_run(c):
    n = WOLF_HIGH[c].split('+')
    return ' '.join(n + n[::-1][1:] + n[1:] + n[::-1][1:4])


NEW_SONGS = {
    # Happy enraged: the battle march, a half step up, faster, with low brass hammering and toms pounding.
    'enraged': {
        'bpm': 184, 'beats': 4, 'steps': 2, 'bars': 16, 'wet': 0.14, 'reverb': 1.2, 'transpose': 1, 'grit': 2.2,
        'parts': SONGS['battle']['parts'] + [
            {'inst': 'brass', 'vol': 0.65, 'pan': -0.1, 'bars': [
                f"{r}! . {r}! . {r}! {r}! {r}! ." for r in ('e2', 'e2', 'c2', 'd2', 'e2', 'e2', 'a1', 'b1')]},
            {'inst': 'choir', 'vol': 0.55, 'bars': [f"{c} - - - - - - -" for c in (
                'e4+g4+b4', 'e4+g4+b4', 'e4+g4+c5', 'd4+f#4+a4', 'e4+g4+b4', 'e4+g4+b4', 'e4+a4+c5', 'd#4+f#4+b4')]},
            {'inst': 'drums', 'vol': 0.7, 'pan': -0.2, 'bars': ["t! . t . t! . t .", "t! . t . t! t t t"]},
        ]},

    # While Happy brings them back: tender and magical, his runes muttered underneath.
    'resurrection': {
        'bpm': 63, 'beats': 4, 'steps': 2, 'bars': 16, 'wet': 0.45, 'reverb': 3.0,
        'extra': lambda n, looping: np.stack([mutter(n)] * 2, 1) * 0.2,
        'parts': [
            {'inst': 'harp', 'vol': 0.7, 'pan': -0.3, 'bars': arps([RES_TRIADS[c] for c in RES_CHORDS], "0 1 2 3 4 3 2 1", 8)},
            {'inst': 'strings', 'vol': 0.55, 'pan': 0.1, 'bars': [f"{RES_PAD[c]} - - - - - - -" for c in RES_CHORDS]},
            {'inst': 'whistle', 'vol': 0.7, 'pan': 0.2, 'bars': RES_TUNE},
            {'inst': 'choir', 'vol': 0.5, 'bars': [REST4] * 8 + [f"{RES_PAD[c]} - - - - - - -" for c in RES_CHORDS[8:]]},
            {'inst': 'bell', 'vol': 0.3, 'pan': 0.6, 'bars': [
                ". . . . . . a6' .", REST4, ". . f#6' . . . . .", REST4, ". . . . . . d7' .", REST4,
                ". . . . b6' . . .", REST4]},
        ]},

    # The goodies: a jolly oom-pah, from Happy's loot right down the hole.
    'goodies': {
        'bpm': 132, 'beats': 4, 'steps': 2, 'bars': 32, 'wet': 0.16, 'reverb': 1.1,
        'parts': [
            {'inst': 'fiddle', 'vol': 0.8, 'pan': 0.15, 'bars': JOLLY_TUNE},
            {'inst': 'whistle', 'vol': 0.45, 'pan': -0.3, 'oct': 1, 'bars': [REST4] * 16 + JOLLY_TUNE},
            {'inst': 'tuba', 'vol': 0.75, 'bars': oompah(JOLLY_CHORDS, JOLLY_LOW, JOLLY_HIGH)[0]},
            {'inst': 'squeezebox', 'vol': 0.55, 'pan': -0.35, 'bars': oompah(JOLLY_CHORDS, JOLLY_LOW, JOLLY_HIGH)[1]},
            {'inst': 'bell', 'vol': 0.25, 'pan': 0.5, 'bars': [REST4] * 16 + [
                "g6' . . . d6' . . .", REST4, "f#6' . . . a6' . . .", REST4]},
            {'inst': 'drums', 'vol': 0.55, 'bars': ["k . s h k . s h", "k . s h k k s s'"]},
        ]},

    # Down in the basin: near silence, a drip, then scratching (louder and closer all the time) and giggles.
    # Plays once (72 s), then 'lurk_loop' carries on at full creep until the Kobolds attack (Slayer_Music.THEN).
    'lurk': {
        'bpm': 60, 'beats': 4, 'steps': 2, 'bars': 18, 'loop': False, 'tail': 0.2, 'wet': 0.5, 'reverb': 3.2,
        'level': 0.45, 'fixed': True, 'extra': lambda n, looping: haunt(n, looping, (0.06, 1.0), 0.35),
        'parts': [
            {'inst': 'strings', 'vol': 0.5, 'bars': ["d2+a2 - - - - - - -", "d2+a2 - - - - - - -", "eb2+a2 - - - - - - -",
                                                    "d2+a2 - - - - - - -"]},
            {'inst': 'bell', 'vol': 0.35, 'pan': 0.6, 'bars': [". . . . . . d6' .", REST4, ". . a5' . . . . .", REST4,
                                                              REST4, ". eb6' . . . . . .", REST4, REST4]},
            {'inst': 'pizz', 'vol': 0.5, 'pan': -0.3, 'bars': ["d2 . . . . . . .", REST4, REST4, ". . . . eb2 . . ."]},
        ]},
    'lurk_loop': {
        'bpm': 60, 'beats': 4, 'steps': 2, 'bars': 8, 'wet': 0.5, 'reverb': 3.2,
        'level': 0.45, 'fixed': True, 'extra': lambda n, looping: haunt(n, looping, (1.0, 1.0), 0.0),
        'parts': [
            {'inst': 'strings', 'vol': 0.5, 'bars': ["d2+a2 - - - - - - -", "d2+a2 - - - - - - -", "eb2+a2 - - - - - - -",
                                                    "d2+a2 - - - - - - -"]},
            {'inst': 'bell', 'vol': 0.35, 'pan': 0.6, 'bars': [". . . . . . d6' .", REST4, ". . a5' . . . . .", REST4,
                                                              REST4, ". eb6' . . . . . .", REST4, REST4]},
            {'inst': 'pizz', 'vol': 0.5, 'pan': -0.3, 'bars': ["d2 . . . . . . .", REST4, REST4, ". . . . eb2 . . ."]},
            {'inst': 'drums', 'vol': 0.35, 'bars': ["t . . t' . . . .", REST4]},   # a heartbeat, now
        ]},

    # The Krazy Kobold fight.
    'kobolds': {
        'bpm': 138, 'beats': 4, 'steps': 2, 'bars': 32, 'wet': 0.3, 'reverb': 2.0,
        'extra': lambda n, looping: giggles(n, looping, 5, 0.3),
        'parts': [
            {'inst': 'xylo', 'vol': 0.85, 'pan': 0.25, 'bars': KOB_TUNE},
            {'inst': 'pizz', 'vol': 0.9, 'pan': -0.2, 'bars': [KOB_BASS[c] for c in KOB_CHORDS]},
            {'inst': 'reed', 'vol': 0.5, 'pan': -0.35, 'oct': -2, 'bars': [REST4] * 16 + KOB_TUNE},
            {'inst': 'choir', 'vol': 0.35, 'pan': 0.4, 'bars': [f"{KOB_PAD[c]} - - - - - - -" for c in KOB_CHORDS]},
            {'inst': 'whistle', 'vol': 0.3, 'pan': 0.6, 'oct': 1, 'bars': [REST4] * 7 + ["b5 - - - - - a#5 -"] + [REST4] * 7
                                                                           + ["e5 - - - - - d#5 -"]},
            {'inst': 'drums', 'vol': 0.6, 'bars': ["k . x x s' . x .", "k . x . s' x x x"]},
        ]},

    # The wolf pack.
    'wolves': {
        'bpm': 132, 'beats': 4, 'steps': 4, 'bars': 32, 'wet': 0.28, 'reverb': 2.2,
        'parts': [
            {'inst': 'saw', 'vol': 0.85, 'pan': -0.25, 'bars': [wolf_saw(c) for c in WOLF_CHORDS]},
            {'inst': 'brass', 'vol': 0.8, 'pan': 0.15, 'bars': WOLF_HORNS},
            {'inst': 'saw', 'vol': 0.5, 'pan': 0.35, 'bars': [REST16] * 16 + [wolf_run(c) for c in WOLF_CHORDS]},
            {'inst': 'choir', 'vol': 0.5, 'bars': [REST16] * 16 + [f"{WOLF_PAD[c]} " + ' '.join(['-'] * 15) for c in WOLF_CHORDS]},
            {'inst': 'drums', 'vol': 0.85, 'bars': [
                "p! . . . . . . . q . . . p . p p", "p! . . . . . . . q . . . p . . .",
                "p! . . . . . . . q . . . p . p p", "q! . . . q . . . q . q . q q q q",
                "p! . . . . . . . q . . . p . p p", "p! . . . . . . . q . . . p . . .",
                "p! . . . . . . . q . . . p . p p", "p p p p p p p p p p p p q! . . .",
                "g . . . . . . . q . . . p . p p", "p! . . . . . . . q . . . p . . .",
                "p! . . . . . . . q . . . p . p p", "q! . . . q . . . q . q . q q q q",
                "p! . . . . . . . q . . . p . p p", "p! . . . . . . . q . . . p . . .",
                "p! . . . . . . . q . . . p . p p", "p p p p p p p p p p p p q! . . ."]},
        ]},
}


def scatter(n, looping, make, rate, seed, pan=0.8):
    """Sounds dropped in at random, about rate(fraction of the way through) per second, each panned somewhere.
    make(r, how far along) -> a mono sound. In a loop they wrap round to the start."""
    r = np.random.default_rng(seed)
    out = np.zeros((n, 2))
    t = r.exponential(1 / max(rate(0), 0.05))
    while t * RATE < n:
        s = make(r, t * RATE / n)
        p = r.uniform(-pan, pan)
        idx = int(t * RATE) + np.arange(len(s))
        if looping:
            idx %= n
        else:
            keep = idx < n
            idx, s = idx[keep], s[keep]
        np.add.at(out[:, 0], idx, s * np.sqrt(0.5 * (1 - p)))
        np.add.at(out[:, 1], idx, s * np.sqrt(0.5 * (1 + p)))
        t += r.exponential(1 / max(rate(t * RATE / n), 0.05))
    return out


def haunt(n, looping, ramp, giggle_from):
    """The basin: scratches that come more often and louder as `ramp` goes from its first value to its second, and
    giggles once it's giggle_from of the way in."""
    def level(x):   # slow at first, then closing in fast
        return ramp[0] + (ramp[1] - ramp[0]) * x ** 1.8
    scratches = scatter(n, looping, lambda r, x: scratch(r) * 0.24 * (0.15 + 0.85 * level(x)),
                        lambda x: 0.035 + 0.6 * level(x) ** 1.5, 31)
    laughs = scatter(n, looping, lambda r, x: giggle(r) * 0.13 * (0.4 + 0.6 * level(x)) * (x >= giggle_from),
                     lambda x: 0.25 * level(x), 37)
    return scratches + laughs


def giggles(n, looping, per_minute, level):
    return scatter(n, looping, lambda r, x: giggle(r) * level * 0.4, lambda x: per_minute / 60, 41)


def mutter(n):
    """Happy's runes: a low voice muttering fast, under his breath, the whole time."""
    return murmur(n, voices=2, syllable=0.085, pitch=(90, 112), talking=False).mean(1)


SONGS.update(NEW_SONGS)


# ---------- sound effects (assets/sounds) ----------

def stutter(n, chunk_s, chance):
    """On/off in random little chunks: a contact that won't make up its mind."""
    chunks = (rng.random(int(n / (chunk_s * RATE)) + 2) < chance).astype(float)
    return lowpass(np.repeat(chunks, int(chunk_s * RATE))[:n], 40)


def tube_buzz(n):
    """A fluorescent tube's ballast: a nasty 120 Hz buzz with a rattle in it."""
    t = np.arange(n) / RATE
    s = np.sin(2 * np.pi * 120 * t)
    hum = np.sign(s) * np.abs(s) ** 0.3 * 0.5 + 0.35 * np.sin(2 * np.pi * 240 * t + 0.5)
    hiss = np.diff(rng.normal(0, 1, n), prepend=0)
    rattle = hiss * 0.3 * (0.5 + 0.5 * np.sin(2 * np.pi * 120 * t)) ** 6
    return lowpass(hum, 3) + rattle


def sfx_buzz():
    """The tube buzzing, exactly one second long (120 whole cycles) so it loops without a seam."""
    n = RATE
    crackle = np.zeros(n)
    crackle[rng.integers(0, n, 25)] = rng.uniform(-1, 1, 25)
    crackle = np.convolve(crackle, np.exp(-np.arange(200) / 30), 'same')
    return tube_buzz(n) + crackle * 0.4


def sfx_zap():
    """The tube flashing on for an instant: a crackling buzz that stutters and dies."""
    n = int(0.16 * RATE)
    t = np.arange(n) / RATE
    hiss = np.diff(rng.normal(0, 1, n), prepend=0)
    out = (tube_buzz(n) * 1.3 + hiss * 0.5 * np.exp(-t * 40)) * np.exp(-t * 18) * stutter(n, 0.008, 0.7)
    out[:40] *= np.linspace(0, 1, 40)
    return out


def sfx_tink():
    """The starter clicking: a tiny metallic tick."""
    n = int(0.08 * RATE)
    t = np.arange(n) / RATE
    f0 = rng.uniform(3400, 4200)
    return sum(a * np.sin(2 * np.pi * f0 * r * t) * np.exp(-t * d)
               for r, a, d in ((1, 1, 70), (1.62, 0.6, 110), (2.5, 0.4, 160))) * 0.5


def sfx_catch():
    """The tube finally catching: a thunk from the ballast and the buzz swelling to full."""
    n = int(1.2 * RATE)
    t = np.arange(n) / RATE
    thunk = np.sin(2 * np.pi * np.cumsum(60 + 50 * np.exp(-t * 30)) / RATE) * np.exp(-t * 12)
    thunk += lowpass(rng.normal(0, 1, n), 10) * 0.4 * np.exp(-t * 35)
    swell = np.clip(t / 0.08, 0, 1) * (0.45 + 0.75 * np.exp(-t * 4)) * np.clip((1.2 - t) / 0.3, 0, 1)
    return thunk * 0.9 + tube_buzz(n) * swell + sfx_tink_at(n, 0.0)


def sfx_tink_at(n, at):
    out = np.zeros(n)
    tink = sfx_tink()
    i = int(at * RATE)
    out[i:i + len(tink)] = tink[:n - i]
    return out


def sfx_door():
    """A heavy old tavern door: a long creak, then it thuds shut behind you and the latch drops."""
    creak_s, n = 1.5, int(2.6 * RATE)
    t = np.arange(n) / RATE
    # the hinge sticking and slipping: little bumps, faster and slower as the door swings
    rate = 35 + 70 * wobbly(n, RATE, 0.25) + 25 * np.sin(np.pi * np.clip(t / creak_s, 0, 1))
    ticks = np.diff(np.floor(np.cumsum(rate) / RATE), prepend=0) > 0
    loud = np.sin(np.pi * np.clip(t / creak_s, 0, 1)) ** 0.6 * wobbly(n, RATE, 0.15, 0.5, 1.0)
    bumps = ticks * loud * rng.uniform(0.6, 1.0, n)
    ir_t = np.arange(int(0.06 * RATE)) / RATE
    wood = sum(a * np.sin(2 * np.pi * f * ir_t) * np.exp(-ir_t * d)
               for f, a, d in ((320, 1, 45), (650, 0.8, 55), (1150, 0.55, 70), (1900, 0.35, 90), (2750, 0.2, 120)))
    creak = np.convolve(bumps, wood, 'full')[:n] * 0.35
    # the slam: a low thud through the floorboards, then the latch
    at = 1.75
    tt = np.clip(t - at, 0, None)
    thud = (np.sin(2 * np.pi * np.cumsum(55 + 45 * np.exp(-tt * 25)) / RATE) * np.exp(-tt * 9)
            + lowpass(rng.normal(0, 1, n), 14) * 0.5 * np.exp(-tt * 25)) * (t >= at)
    latch = sfx_tink_at(n, at + 0.17) * 0.8
    out = creak + thud * 0.8 + latch
    return out


# ---------- combat sounds: voices (no words, just noises) and elements ----------

VOWELS = {  # formants (F1, F2, F3) in Hz
    'uh': (640, 1190, 2390), 'oh': (450, 800, 2830), 'oo': (330, 870, 2240), 'ah': (750, 1250, 2600),
    'ee': (310, 2700, 3300), 'eh': (550, 1900, 2600), 'mm': (250, 900, 2200), 'aw': (600, 950, 2500),
}


def band(x, lo, hi):
    """Keep only lo..hi Hz (a brick-wall filter done in one FFT)."""
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / RATE)
    spec[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(spec, len(x))


def curve(n, points):
    """A value gliding through points [(fraction of the way, value), ...]."""
    xs, ys = zip(*points)
    return np.interp(np.linspace(0, 1, n), xs, ys)


def voice(seconds, pitch, vowels, scale=1.0, breath=0.1, rough=0.0, attack=0.01, release=0.08, tilt=1.0):
    """A wordless voice: a buzzing throat (harmonics of the pitch) shaped by the mouth (vowel formants).
    pitch and vowels are [(fraction, value), ...] glides; scale shifts the formants (smaller heads, higher)."""
    n = int(seconds * RATE)
    t = np.arange(n) / RATE
    f0 = curve(n, pitch) * (1 + rough * (wobbly(n, RATE, 0.012) - 0.5))
    phase = 2 * np.pi * np.cumsum(f0) / RATE
    formants = [curve(n, [(x, VOWELS[v][i] * scale) for x, v in vowels]) for i in range(3)]
    out = np.zeros(n)
    for k in range(1, 60):
        fk = k * f0
        if fk.min() > RATE * 0.45:
            break
        amp = sum(a * np.exp(-((fk - F) / bw) ** 2)
                  for F, a, bw in zip(formants, (1.0, 0.7, 0.35), (110, 160, 240)))
        out += (amp + 0.04) / k ** tilt * np.sin(k * phase) * (fk < RATE * 0.45)
    if rough:  # a gravelly throat: the level stutters quickly
        out *= 1 - rough * 2 * wobbly(n, RATE, 1 / max(f0.mean() / 2, 20))
    air = band(rng.normal(0, 1, n), formants[0].mean() * 0.8, formants[1].mean() * 1.6)
    out = out / (np.abs(out).max() + 1e-9) + breath * air / (np.abs(air).max() + 1e-9)
    env = np.clip(t / attack, 0, 1) * np.clip((seconds - t) / release, 0, 1)
    return out * env


def sweep_band(x, fc, q=2.0):
    """x through a band-pass whose centre glides along fc (Hz, one per sample): a swish, a sweep, a 'shwoop'."""
    f = 2 * np.sin(np.pi * np.clip(fc, 30, 5000) / RATE)
    damp = 1 / q
    low = bp = 0.0
    out = np.empty(len(x))
    for i in range(len(x)):
        high = x[i] - low - damp * bp
        bp += f[i] * high
        low += f[i] * bp
        out[i] = bp
    return out


def at(n, pieces):
    """Lay sounds out on one track: pieces = [(start seconds, sound), ...]."""
    out = np.zeros(n)
    for start, s in pieces:
        i = int(start * RATE)
        if i < n:
            out[i:i + len(s)] += s[:n - i]
    return out


def fade(x, inn=0.005, out=0.05):
    t = np.arange(len(x)) / RATE
    return x * np.clip(t / inn, 0, 1) * np.clip((t[-1] - t) / out, 0, 1)


def norm(x):
    return x / (np.abs(x).max() + 1e-9)


def thud(seconds=0.5, low=55, drop=45, decay=9):
    """Something heavy hitting the floor."""
    n = int(seconds * RATE)
    t = np.arange(n) / RATE
    return (np.sin(2 * np.pi * np.cumsum(low + drop * np.exp(-t * 25)) / RATE) * np.exp(-t * decay)
            + lowpass(rng.normal(0, 1, n), 14) * 0.5 * np.exp(-t * 25))


def fricative(seconds, lo=1200, hi=6000):
    """The 'ff' on the end of OOF: breath through teeth."""
    n = int(seconds * RATE)
    return fade(band(rng.normal(0, 1, n), lo, hi), 0.02, seconds * 0.7)


# Heroines and dwarves don't share a throat: the women sit about an octave up (300-600 Hz), with smaller
# heads (formants scaled up), breathier and softer; the men are low, gravelly and more forward.
WOMAN = dict(scale=1.22, breath=0.28, rough=0.02, tilt=1.15)
MAN = dict(scale=0.92, breath=0.22, tilt=0.85)


def ouch(kind, i):
    """One take of a voice. Each kind has a few takes, so the same noise doesn't come round every time."""
    r = np.random.default_rng(1000 * len(kind) + 17 * i + ord(kind[0]))
    j = r.uniform(0.93, 1.07)

    def P(pts):
        return [(x, p * j) for x, p in pts]

    if kind == 'grunt':  # a dwarf taking a hit: OOOF / UGGGH / HURK / OWF
        if i == 0:
            v = voice(0.3, P([(0, 140), (0.3, 128), (1, 95)]), [(0, 'oh'), (0.5, 'oo'), (1, 'oo')], rough=0.15,
                      release=0.05, **MAN)
            return np.concatenate([v, fricative(0.13) * 0.35])
        if i == 1:
            return voice(0.55, P([(0, 128), (0.2, 120), (1, 78)]), [(0, 'uh'), (0.7, 'uh'), (1, 'aw')], rough=0.4,
                         release=0.15, **MAN)
        if i == 2:
            return voice(0.24, P([(0, 165), (0.5, 140), (1, 110)]), [(0, 'uh'), (1, 'aw')], rough=0.25,
                         release=0.015, **MAN)
        v = voice(0.32, P([(0, 150), (0.25, 135), (1, 90)]), [(0, 'aw'), (0.6, 'oh'), (1, 'oo')], rough=0.2,
                  release=0.04, **MAN)
        return np.concatenate([v, fricative(0.1) * 0.3])
    if kind == 'dwarf_die':  # AAAARGH... and down he goes
        secs = r.uniform(0.9, 1.1)
        v = voice(secs, P([(0, 150), (0.25, 178), (0.6, 150), (1, 68)]),
                  [(0, 'ah'), (0.5, 'ah'), (0.8, 'aw'), (1, 'uh')], rough=0.35, attack=0.03, release=0.3, **MAN)
        return at(int((secs + 0.6) * RATE), [(0, v), (secs - 0.05, thud() * 0.8)])
    if kind == 'kobold':  # a Kobold: a squeaky little yip
        v = ['ee', 'eh', 'ah'][i % 3]
        return voice(r.uniform(0.12, 0.18), P([(0, 420), (0.3, 520), (1, 330)]),
                     [(0, v), (1, 'uh')], scale=1.3, breath=0.2, rough=0.05, release=0.04)
    if kind == 'kobold_die':  # eeeeyaaaa...
        return voice(r.uniform(0.45, 0.6), P([(0, 650), (0.25, 920), (1, 250)]), [(0, 'ee'), (0.4, 'ah'), (1, 'uh')],
                     scale=1.35, breath=0.25, rough=0.06, release=0.15)
    if kind == 'yelp':  # a wolf: a sharp yelp
        return voice(r.uniform(0.18, 0.26), P([(0, 600), (0.2, 1050), (1, 520)]),
                     [(0, 'ah'), (0.5, 'aw'), (1, 'oo')], scale=1.15, breath=0.35, rough=0.06, release=0.07)
    if kind == 'wolf_die':  # a yelp that trails off into a whimper
        yelp = voice(0.2, P([(0, 650), (0.25, 1100), (1, 600)]), [(0, 'ah'), (1, 'oo')], scale=1.15, breath=0.35,
                     release=0.03)
        whine = voice(0.75, P([(0, 720), (0.3, 640), (0.6, 690), (1, 380)]), [(0, 'oo'), (1, 'mm')], scale=1.15,
                      breath=0.45, rough=0.05, attack=0.05, release=0.3)
        return np.concatenate([yelp, np.zeros(int(0.08 * RATE)), whine * 0.8])
    if kind == 'groan':  # a heroine taking a hit: OW! / UNNH / AH! / EUGH
        takes = [(0.28, [(0, 430), (0.25, 530), (1, 370)], [(0, 'ah'), (0.5, 'aw'), (1, 'oo')]),
                 (0.33, [(0, 370), (0.4, 390), (1, 310)], [(0, 'uh'), (0.6, 'uh'), (1, 'mm')]),
                 (0.24, [(0, 510), (0.2, 570), (1, 430)], [(0, 'ah'), (1, 'ah')]),
                 (0.34, [(0, 410), (0.3, 450), (1, 330)], [(0, 'eh'), (0.5, 'uh'), (1, 'mm')])]
        secs, pitch, vowels = takes[i % 4]
        return voice(secs * r.uniform(0.95, 1.1), P(pitch), vowels, attack=0.015, release=0.1, **WOMAN)
    if kind == 'heroine_die':  # a heroine going down for good: a falling cry, then the floor
        secs = r.uniform(0.75, 0.95)
        start = [520, 480, 560][i % 3]
        v = voice(secs, P([(0, start), (0.2, start * 1.15), (1, start * 0.6)]),
                  [(0, ['ah', 'eh', 'ah'][i % 3]), (0.5, 'aw'), (1, 'oh')], attack=0.02, release=0.3, **WOMAN)
        return at(int((secs + 0.55) * RATE), [(0, v), (secs - 0.1, thud(low=70, drop=50) * 0.45)])
    if kind == 'scream':  # a heroine too scared to move: a short, sharp scream
        secs = r.uniform(0.45, 0.6)
        top = [950, 1050, 880][i % 3]
        v = voice(secs, P([(0, top * 0.75), (0.12, top), (0.75, top * 0.97), (1, top * 0.8)]),
                  [(0, 'ah'), (0.6, ['ah', 'eh', 'ee'][i % 3]), (1, 'eh')], scale=1.25, breath=0.32, rough=0.04,
                  attack=0.02, release=0.12, tilt=1.0)
        return v * (1 + 0.12 * np.sin(2 * np.pi * 7 * np.arange(len(v)) / RATE))   # a nervous wobble in it
    if kind == 'squeal':  # a heroine healed: a happy little squeal
        if i % 3 == 2:  # a two-part "ee-hee!"
            a = voice(0.13, [(0, 560 * j), (1, 700 * j)], [(0, 'ee'), (1, 'ee')], scale=1.18, breath=0.15)
            b = voice(0.24, [(0, 640 * j), (0.4, 860 * j), (1, 760 * j)], [(0, 'eh'), (0.3, 'ee'), (1, 'ee')],
                      scale=1.18, breath=0.15)
            return np.concatenate([a, np.zeros(int(0.03 * RATE)), b])
        rise = [(0, 480 * j), (0.6, 880 * j), (1, 960 * j)] if i % 3 == 0 else [(0, 600 * j), (0.4, 900 * j), (1, 700 * j)]
        return voice(r.uniform(0.3, 0.4), rise, [(0, 'eh'), (0.25, 'ee'), (1, 'ee')], scale=1.18, breath=0.15,
                     attack=0.02, release=0.1)
    if kind == 'growl':  # a Shifter's Savage Bite or Throat Rip: a vicious snarl
        secs = r.uniform(0.8, 1.0)
        g = voice(secs, P([(0, 85), (0.2, 120), (0.7, 105), (1, 70)]),
                  [(0, 'mm'), (0.15, 'ah'), (0.7, 'aw'), (1, 'uh')],
                  scale=0.85, breath=0.6, rough=0.5, attack=0.04, release=0.2, tilt=0.6)
        t = np.arange(len(g)) / RATE
        g = g * (1 - 0.45 * (0.5 + 0.5 * np.sin(2 * np.pi * 31 * t)))   # the rattle in the throat
        return np.tanh(norm(g) * 2.5)
    if kind == 'roar':  # the Bear Maul, the Honey Badger: something HUGE comes out of her
        secs = r.uniform(1.5, 1.8)
        n = int(secs * RATE)
        g = voice(secs, P([(0, 70), (0.15, 125), (0.5, 140), (0.8, 110), (1, 60)]),
                  [(0, 'oo'), (0.12, 'oh'), (0.3, 'ah'), (0.75, 'aw'), (1, 'uh')],
                  scale=0.7, breath=0.7, rough=0.55, attack=0.08, release=0.4, tilt=0.55)
        g = g * (1 - 0.4 * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(curve(n, [(0, 22), (0.5, 34), (1, 18)])) / RATE)))
        chest = band(rng.normal(0, 1, n), 40, 400) * curve(n, [(0, 0), (0.1, 1), (0.6, 0.9), (1, 0)])
        return np.tanh((norm(g) + 0.6 * norm(chest)) * 3.0)
    if kind == 'gag':  # Happy hurling: two heaves, then BLEAGH, and the splatter
        def heave(p):
            return voice(0.16, [(0, p), (1, p * 0.75)], [(0, 'uh'), (1, 'aw')], rough=0.55, release=0.02, **MAN)
        return _hurl([heave(150 * j), heave(140 * j)],
                     voice(0.45, P([(0, 150), (0.3, 135), (1, 85)]), [(0, 'eh'), (0.3, 'ah'), (1, 'aw')], rough=0.55,
                           breath=0.4, scale=0.92, tilt=0.85, release=0.1))
    if kind == 'retch':  # a heroine with Happy's norovirus doing the same
        def heave(p):
            return voice(0.14, [(0, p), (1, p * 0.8)], [(0, 'uh'), (1, 'aw')], scale=1.2, breath=0.4, rough=0.3,
                         release=0.02, tilt=1.1)
        return _hurl([heave(330 * j), heave(310 * j)],
                     voice(0.4, P([(0, 360), (0.3, 340), (1, 250)]), [(0, 'eh'), (0.3, 'ah'), (1, 'aw')], scale=1.2,
                           breath=0.45, rough=0.3, release=0.1, tilt=1.1))
    if kind == 'cackle':  # the Witch's Evil Cackle (Ted, Nov 18): a rising shriek, a run of "heh"s, a long wicked trill
        return cackle(r, j, i)
    raise ValueError(kind)


CRONE = dict(scale=1.1, breath=0.3, rough=0.22, tilt=0.85)   # an old witch: a bit lower and bigger than the heroines, raspy, nasal


def cackle(r, j, i):
    """eeEEEH... heh-heh-heh-heh-heh-heh... HAAAaaa-a-a-a. Each take differs in its pitches, how many heh's and their speed."""
    top = [880, 960, 820][i % 3] * j
    pieces, t = [], 0.0
    rise = voice(0.38, [(0, top * 0.62), (0.7, top), (1, top * 1.05)], [(0, 'ee'), (0.6, 'eh'), (1, 'eh')],
                 attack=0.04, release=0.05, **CRONE)
    pieces.append((t, rise))
    t += 0.38 + 0.05
    hehs = [7, 9, 8][i % 3]
    step = [0.125, 0.11, 0.135][i % 3]
    for k in range(hehs):
        p = top * (0.98 - 0.32 * k / hehs) * r.uniform(0.96, 1.04)   # each one a little lower
        syl = voice(step * 0.72, [(0, p * 1.06), (1, p * 0.9)], [(0, 'eh' if k % 2 else 'ah'), (1, 'uh')],
                    attack=0.006, release=0.03, **CRONE)
        h = fricative(0.025, 900, 4000) * 0.5   # the "h" puff in front of each
        pieces += [(t, h), (t + 0.02, syl)]
        t += step
    t += 0.06
    trill_s = [0.9, 0.75, 1.0][i % 3]
    trill = voice(trill_s, [(0, top * 0.85), (0.25, top * 1.12), (0.7, top * 0.95), (1, top * 0.55)],
                  [(0, 'ah'), (0.5, 'ah'), (1, 'aw')], attack=0.03, release=0.3, **CRONE)
    tt = np.arange(len(trill)) / RATE
    trill = trill * (1 - 0.55 * (0.5 + 0.5 * np.sin(2 * np.pi * curve(len(trill), [(0, 11), (1, 7)]) * tt)))   # ha-a-a-a
    pieces.append((t, trill))
    dry = at(int((t + trill_s + 0.05) * RATE), pieces)
    tail_n = int(0.7 * RATE)   # a stone room around her
    ir = r.normal(0, 1, tail_n) * np.exp(-np.arange(tail_n) / RATE * 7)
    ir[:int(0.02 * RATE)] = 0
    n = len(dry) + tail_n
    wet = np.convolve(dry, ir / np.sqrt((ir ** 2).sum()))[:n]
    return norm(np.concatenate([dry, np.zeros(tail_n)]) + 0.35 * norm(np.pad(wet, (0, n - len(wet)))))


def _hurl(heaves, bleagh):
    """Two heaves, the big one, and what comes out of it hitting the floor."""
    n = int(0.9 * RATE)
    t = np.arange(n) / RATE
    gush = band(rng.normal(0, 1, n), 250, 3500) * np.exp(-t * 4) * (0.6 + 0.4 * wobbly(n, RATE, 0.03))
    drops = np.zeros(n)
    for p in rng.integers(int(0.1 * RATE), n - 2000, 22):   # chunks and drops landing: little rising blips
        k = int(rng.integers(300, 900))
        tt = np.arange(k) / RATE
        f0 = rng.uniform(300, 900)
        drops[p:p + k] += np.sin(2 * np.pi * np.cumsum(f0 + 3000 * tt) / RATE) * np.exp(-tt * 60) * rng.uniform(0.3, 1)
    splash = norm(gush) * 0.7 + norm(drops) * 0.5
    return at(int(1.9 * RATE), [(0.0, heaves[0]), (0.28, heaves[1]), (0.6, bleagh), (0.82, splash)])


def sfx_whoosh(i):
    """A swing that finds only air: SHWOOP. Noise through a band-pass that sweeps up and back down."""
    secs = [0.3, 0.26, 0.36][i % 3]
    n = int(secs * RATE)
    peak = [0.4, 0.35, 0.45][i % 3]
    fc = curve(n, [(0, 350), (peak, [2400, 3000, 2000][i % 3]), (1, 450)])
    noise = rng.normal(0, 1, n)
    tone = sweep_band(noise, fc, q=3.5)
    air = sweep_band(noise, fc * 0.6, q=0.8)
    env = curve(n, [(0, 0), (peak * 0.8, 0.6), (peak, 1), (min(1, peak + 0.25), 0.35), (1, 0)]) ** 1.3
    return (norm(tone) + 0.5 * norm(air)) * env


def crackles(n, per_s):
    out = np.zeros(n)
    for p in rng.integers(0, n - 400, int(per_s * n / RATE)):
        length = int(rng.integers(40, 300))
        tt = np.arange(length) / RATE
        out[p:p + length] += rng.normal(0, 1, length) * np.exp(-tt * rng.uniform(300, 1200)) * rng.uniform(0.2, 1.0)
    return band(out, 900, 9000)


def sfx_fire():
    """Flames: a whump as it catches, a roar, and crackling."""
    secs = 1.6
    n = int(secs * RATE)
    t = np.arange(n) / RATE
    whump = band(rng.normal(0, 1, n), 60, 700) * np.clip(t / 0.03, 0, 1) * np.exp(-t * 6)
    roar = band(rng.normal(0, 1, n), 80, 1400) * (0.5 + 0.5 * wobbly(n, RATE, 0.08)) * np.exp(-t * 1.2)
    crack = crackles(n, 45) * np.exp(-t * 1.5)
    out = whump / np.abs(whump).max() * 0.9 + roar / np.abs(roar).max() * 0.5 + crack / np.abs(crack).max() * 0.6
    return out * np.clip((secs - t) / 0.4, 0, 1)


def fire_burst():
    m = int(0.6 * RATE)
    tt = np.arange(m) / RATE
    return norm(band(rng.normal(0, 1, m), 50, 900) * np.clip(tt / 0.01, 0, 1) * np.exp(-tt * 9)) * rng.uniform(0.7, 1)


def sfx_firestorm():
    """Fire Rain: a howling firestorm, with fireballs streaking down and bursting all around."""
    secs = 3.4
    n = int(secs * RATE)
    swell = curve(n, [(0, 0), (0.15, 0.8), (0.6, 1), (1, 0)])
    storm = band(rng.normal(0, 1, n), 50, 2200) * (0.45 + 0.55 * wobbly(n, RATE, 0.05)) * swell
    wind = sweep_band(rng.normal(0, 1, n), 500 + 700 * wobbly(n, RATE, 0.4), q=1.5) * swell
    balls = []
    for k in range(9):   # each fireball: a falling shriek, then a whump where it lands
        start = 0.15 + k * 0.32 + rng.uniform(-0.08, 0.08)
        m = int(0.35 * RATE)
        fall = sweep_band(rng.normal(0, 1, m), curve(m, [(0, 3200), (1, 600)]), q=4) * curve(m, [(0, 0), (0.7, 1), (1, 0.2)])
        balls += [(start, norm(fall) * 0.5), (start + 0.33, fire_burst())]
    out = norm(storm) * 0.8 + norm(wind) * 0.35 + norm(crackles(n, 90) * swell) * 0.5 + at(n, balls)
    return np.tanh(out * 1.3)


def sfx_thunder():
    """Lightning: a deafening crack right overhead, a BOOM you feel in your chest, then thunder rolling away."""
    secs = 3.8
    n = int(secs * RATE)
    t = np.arange(n) / RATE
    crack = np.zeros(n)
    for start in (0.0, 0.018, 0.04, 0.07, 0.12):  # the bolt forks: several cracks almost on top of each other
        tt = np.clip(t - start, 0, None)
        crack += (np.diff(rng.normal(0, 1, n), prepend=0) * np.exp(-tt * rng.uniform(18, 35)) * (t >= start)
                  * rng.uniform(0.6, 1))
    crack = band(crack, 120, 7000)
    boom = band(rng.normal(0, 1, n), 25, 180) * np.clip((t - 0.04) / 0.02, 0, 1) * np.exp(-t * 2.2)
    rumble = band(rng.normal(0, 1, n), 25, 260)
    rumble *= (0.35 + 0.65 * wobbly(n, RATE, 0.18) ** 2) * np.clip((t - 0.15) / 0.3, 0, 1) * np.exp(-t * 0.75)
    out = norm(crack) * 1.0 + norm(boom) * 1.1 + norm(rumble) * 0.9
    return np.tanh(out * 2.2) * np.clip((secs - t) / 0.8, 0, 1)


def sfx_holy():
    """Deep Meditation: a harp sweeping up, a choir's 'aaah' and a shimmer of bells."""
    n = int(3.0 * RATE)
    notes = ['d4', 'f#4', 'a4', 'b4', 'd5', 'e5', 'f#5', 'a5', 'b5', 'd6', 'e6', 'f#6']
    out = at(n, [(0.05 + k * 0.06, pluck(hz(midi(p)), 0.2, 0.8, decay=0.998, bright=0.45, seconds=1.6))
                 for k, p in enumerate(notes)])
    voices = sum(choir(hz(midi(p)), 2.0, 0.9) for p in ('d4', 'a4', 'd5', 'f#5'))
    out += at(n, [(0.35, norm(voices) * 0.9)])
    out += at(n, [(0.8 + k * 0.17, bell(hz(midi(p)), 1, 0.5)) for k, p in enumerate(['a6', 'f#6', 'd7', 'a6', 'e7'])]) * 0.6
    stereo = reverb(np.stack([out, out], 1), 2.4, 0.5, False)
    return fade(stereo.mean(1), 0.01, 0.6)


def scratch(r, secs=None):
    """Fingernails dragged down a steel guitar string: a metal string, rasped instead of plucked, sliding."""
    secs = secs or r.uniform(0.4, 1.1)
    n = int(secs * RATE)
    rate = r.uniform(150, 320) * (0.7 + 0.6 * wobbly(n, RATE, 0.05))   # the nail catching on each winding
    ticks = (np.diff(np.floor(np.cumsum(rate) / RATE), prepend=0) > 0) * r.uniform(0.4, 1.0, n)
    p = int(RATE / r.uniform(170, 330))
    y = np.zeros(n + p)
    x = np.concatenate([np.zeros(p), ticks + rng.normal(0, 0.05, n)])
    for start in range(p, n + p, p):   # a string: each period is the last one, a little duller, plus the rasping
        end = min(start + p, n + p)
        prev = y[start - p:end - p]
        y[start:end] = x[start:end] + 0.985 * 0.5 * (prev + np.roll(prev, 1))
    y = y[p:]
    slide = curve(n, [(0, 1), (1, r.choice([0.82, 1.18, 0.9]))])   # the hand sliding along it
    y = np.interp(np.clip(np.cumsum(slide), 0, n - 1), np.arange(n), y)
    squeal = sweep_band(rng.normal(0, 1, n), r.uniform(2500, 3800) * slide, q=12)
    out = norm(band(y, 300, 9000)) + 0.4 * norm(squeal) * (0.5 + 0.5 * norm(lowpass(ticks, 200)))
    return fade(norm(out), 0.03, secs * 0.4)


def giggle(r):
    """A Kobold giggling somewhere in the dark: hee-hee-hee-hee."""
    out = []
    top = r.uniform(780, 1000)
    for k in range(int(r.integers(4, 7))):
        p = top * (1 - 0.06 * k)
        out += [voice(r.uniform(0.06, 0.08), [(0, p * 1.08), (1, p * 0.9)], [(0, 'ee'), (1, 'eh')], scale=1.4,
                      breath=0.5, rough=0.05, attack=0.008, release=0.03),
                np.zeros(int(r.uniform(0.035, 0.06) * RATE))]
    return np.concatenate(out)


def sfx_pick(kind):
    """A heroine getting her weapon (or spell, or potion) ready, as it's picked from the menu."""
    if kind == 'blade':   # SHING: steel sliding out, then ringing
        m = int(0.18 * RATE)
        scrape = sweep_band(rng.normal(0, 1, m), curve(m, [(0, 1800), (1, 4800)]), q=6) * curve(m, [(0, 0), (0.8, 1), (1, 0.6)])
        t = np.arange(int(0.9 * RATE)) / RATE
        ring = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, a, d in
                   ((2350, 1, 5), (3720, 0.7, 7), (5130, 0.5, 9), (6900, 0.3, 12)))
        return at(int(1.1 * RATE), [(0, norm(scrape) * 0.8), (0.15, norm(ring) * 0.7)])
    if kind == 'heavy':   # a big weapon hefted: WHOOMPH, and a clank
        m = int(0.45 * RATE)
        swing = sweep_band(rng.normal(0, 1, m), curve(m, [(0, 200), (0.6, 700), (1, 250)]), q=1.5) * curve(m, [(0, 0), (0.6, 1), (1, 0)])
        t = np.arange(int(0.6 * RATE)) / RATE
        clank = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, a, d in ((410, 1, 14), (1130, 0.6, 20), (2270, 0.3, 30)))
        return at(int(1.0 * RATE), [(0, norm(swing)), (0.33, norm(clank) * 0.6)])
    if kind == 'bow':   # an arrow nocked and the string drawn back: creak, creak, creeeak
        n = int(0.7 * RATE)
        t = np.arange(n) / RATE
        rate = curve(n, [(0, 60), (1, 140)])
        ticks = (np.diff(np.floor(np.cumsum(rate) / RATE), prepend=0) > 0) * rng.uniform(0.5, 1, n) * np.clip(t / 0.1, 0, 1)
        ir_t = np.arange(int(0.03 * RATE)) / RATE
        wood = sum(a * np.sin(2 * np.pi * f * ir_t) * np.exp(-ir_t * d) for f, a, d in ((620, 1, 70), (1400, 0.7, 90), (2600, 0.4, 120)))
        return fade(np.convolve(ticks, wood, 'full')[:n], 0.01, 0.1)
    if kind == 'magic':   # a spell gathering: a rising shimmer
        n = int(0.8 * RATE)
        out = at(n, [(k * 0.07, bell(hz(midi(p)), 1, 0.6)) for k, p in enumerate(['a5', 'c#6', 'e6', 'a6', 'c#7'])])
        sparkle = sweep_band(rng.normal(0, 1, n), curve(n, [(0, 1500), (1, 4800)]), q=3) * curve(n, [(0, 0), (0.5, 1), (1, 0)])
        return fade(norm(out) + 0.35 * norm(sparkle), 0.005, 0.2)
    if kind == 'fists':   # cracking her knuckles
        n = int(0.45 * RATE)
        pops = np.zeros(n)
        for s in (0.0, 0.09, 0.15, 0.26):
            i = int(s * RATE)
            pops[i:i + 260] += rng.normal(0, 1, 260) * np.exp(-np.arange(260) / 30) * rng.uniform(0.6, 1)
        return band(pops, 900, 7000)
    if kind == 'beast':   # an animal snort and huff
        n = int(0.5 * RATE)
        t = np.arange(n) / RATE
        return band(rng.normal(0, 1, n), 250, 2200) * (np.exp(-((t - 0.08) / 0.05) ** 2) + 0.8 * np.exp(-((t - 0.3) / 0.08) ** 2))
    if kind == 'potion':   # the cork popping and a glug-glug
        n = int(0.7 * RATE)
        t = np.arange(n) / RATE
        pop = np.sin(2 * np.pi * np.cumsum(700 - 300 * t) / RATE) * np.exp(-t * 60) + rng.normal(0, 1, n) * 0.3 * np.exp(-t * 200)
        m = int(0.09 * RATE)
        tt = np.arange(m) / RATE
        glug = np.sin(2 * np.pi * np.cumsum(220 + 900 * tt) / RATE) * np.exp(-tt * 25)
        return norm(pop) + 0.6 * at(n, [(s, glug) for s in (0.25, 0.4, 0.53)])
    if kind == 'tear':   # a bandage ripped off the roll
        n = int(0.4 * RATE)
        return band(crackles(n, 400) + rng.normal(0, 0.3, n), 600, 6000) * curve(n, [(0, 0), (0.1, 1), (0.8, 0.7), (1, 0)])
    if kind == 'bomb':   # a fuse lit: the strike, then fizzing
        n = int(0.8 * RATE)
        t = np.arange(n) / RATE
        strike = band(rng.normal(0, 1, n), 1500, 8000) * np.exp(-t * 25)
        fizz = band(crackles(n, 300) + rng.normal(0, 0.4, n), 2500, 9000) * np.clip((t - 0.08) / 0.05, 0, 1)
        return fade(norm(strike) * 0.7 + norm(fizz) * 0.5, 0.002, 0.15)
    raise ValueError(kind)


# Effects with several takes (grunt_1.ogg, grunt_2.ogg, ...). Keep in step with Slayer_Music.TAKES.
TAKES = {'grunt': 4, 'kobold': 3, 'yelp': 3, 'groan': 4, 'squeal': 3, 'growl': 2, 'whoosh': 3, 'roar': 2,
         'scream': 3, 'gag': 2, 'retch': 2, 'dwarf_die': 2, 'kobold_die': 2, 'wolf_die': 2, 'heroine_die': 3,
         'cackle': 3}
PICKS = ['blade', 'heavy', 'bow', 'magic', 'fists', 'beast', 'potion', 'tear', 'bomb']

SOUNDS = {'buzz': sfx_buzz, 'zap': sfx_zap, 'tink': sfx_tink, 'catch': sfx_catch, 'door': sfx_door,
          'fire': sfx_fire, 'firestorm': sfx_firestorm, 'thunder': sfx_thunder, 'holy': sfx_holy,
          **{f'pick_{kind}': (lambda kind=kind: sfx_pick(kind)) for kind in PICKS},
          **{f'{kind}_{i + 1}': (lambda kind=kind, i=i: sfx_whoosh(i) if kind == 'whoosh' else ouch(kind, i))
             for kind, takes in TAKES.items() for i in range(takes)}}
SOUND_OUT = OUT.parent / 'sounds'

# The title's tube and the door were balanced by ear against each other, so they keep plain peak levels.
# The rest are set by how loud they SOUND (their loudest moment), times these: bigger is louder.
PEAK_ONLY = {'buzz', 'zap', 'tink', 'catch', 'door'}
LOUDNESS = {'thunder': 1.7, 'roar': 1.5, 'firestorm': 1.35, 'fire': 1.1, 'gag': 1.1, 'retch': 1.05, 'whoosh': 0.85,
            'grunt': 1.15, 'dwarf_die': 1.2, 'heroine_die': 1.1, 'scream': 1.0, 'groan': 1.0, 'squeal': 0.85,
            'growl': 1.25, 'holy': 0.9, 'kobold': 0.85, 'kobold_die': 0.95, 'yelp': 0.9, 'wolf_die': 0.95,
            'cackle': 1.05}
PICK_LOUDNESS = 0.6


def level_sound(name, audio):
    """Peak-normalise the title sounds; set the rest by their loudest 150 ms, then round off the peaks."""
    if name in PEAK_ONLY:
        return audio / np.abs(audio).max() * 0.8
    kind = name.rsplit('_', 1)[0] if name.rsplit('_', 1)[-1].isdigit() else name
    gain = PICK_LOUDNESS if kind.startswith('pick_') else LOUDNESS.get(kind, 1.0)
    w = int(0.15 * RATE)
    power = np.convolve(audio ** 2, np.ones(w) / w, 'same')
    audio = audio / np.sqrt(power.max() + 1e-12) * 0.26 * gain
    return np.tanh(audio * 1.4) / 1.4 * 1.05


def write_ogg(path, audio):
    # Written a little at a time: libsndfile's Vorbis encoder overflows its stack on one big write.
    with soundfile.SoundFile(str(path), 'w', RATE, audio.shape[1], format='OGG', subtype='VORBIS') as f:
        for i in range(0, len(audio), 4096):
            f.write(audio[i:i + 4096])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    SOUND_OUT.mkdir(parents=True, exist_ok=True)
    wanted = sys.argv[1:] or list(SONGS) + list(SOUNDS)
    for name in wanted:
        if name in SOUNDS:
            audio = level_sound(name, SOUNDS[name]()).astype(np.float32)[:, None]
            path = SOUND_OUT / f'{name}.ogg'
            write_ogg(path, audio)
            print(f'{name}: {len(audio) / RATE:.2f} s -> {path.relative_to(OUT.parent.parent)}')
            continue
        song = SONGS[name]
        audio = render(song)
        path = OUT / f'{name}.ogg'
        write_ogg(path, audio)
        print(f'{name}: {len(audio) / RATE:.1f} s, peak {np.abs(audio).max():.2f}, '
              f'{path.stat().st_size // 1024} KB -> {path.relative_to(OUT.parent.parent)}')


if __name__ == '__main__':
    main()
