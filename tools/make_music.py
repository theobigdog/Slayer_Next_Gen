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
    Drum letters: k kick, b bodhran (frame drum), x its rim tap, s snare, h hat, t low tom, g gong.
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


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, 'same')


def drum(kind, vel):
    length = {'k': 0.4, 'b': 0.45, 'x': 0.06, 's': 0.25, 'h': 0.06, 't': 0.6, 'g': 3.5, 'c': 0.7,
              'w': 0.3}.get(kind, 0.2)
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
    elif kind == 'w':  # a brush swished across the snare
        env = np.clip(t / 0.03, 0, 1) * np.exp(-t * 14)
        out = lowpass(hiss, 3) * 0.3 * env
    else:
        out = np.zeros(n)
    return out * vel


INSTRUMENTS = {'fiddle': fiddle, 'whistle': whistle, 'drone': drone, 'brass': brass, 'strings': strings,
               'choir': choir, 'bell': bell, 'lute': lute, 'pizz': cello_pizz, 'reed': reed,
               'squeezebox': squeezebox, 'tuba': tuba, 'honky': honky}


# ---------- putting a song together ----------

def parse(part, bars, bar_steps):
    events, last, drums = [], None, part['inst'] == 'drums'
    shift = 12 * part.get('oct', 0)
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


def murmur(n, voices=7):
    """A room full of low talk: pitched 'voices' babbling through shifting vowels, no words in them.
    Worked out at 8 kHz (talk has nothing up high), then stretched to RATE. Loops: the end fades into the start."""
    sr, fade = 8000, 8000
    m = n * sr // RATE + fade
    t = np.arange(m) / sr
    vowels = np.array([(730, 1090), (530, 1840), (300, 870), (570, 840), (440, 1020), (660, 1700)])
    out = np.zeros((m, 2))
    for _ in range(voices):
        f0 = rng.uniform(85, 165) * (1 + 0.07 * (wobbly(m, sr, 0.12) - 0.5) + 0.05 * (wobbly(m, sr, 1.5) - 0.5))
        phase = 2 * np.pi * np.cumsum(f0) / sr
        syll = rng.integers(0, len(vowels), int(m / sr / 0.16) + 3)
        pos = t / 0.16
        f1 = np.interp(pos, np.arange(len(syll)), vowels[syll, 0])
        f2 = np.interp(pos, np.arange(len(syll)), vowels[syll, 1])
        voice = np.zeros(m)
        for k in range(1, 18):
            fk = k * f0
            amp = np.exp(-((fk - f1) / 140) ** 2) + 0.6 * np.exp(-((fk - f2) / 220) ** 2) + 0.15 / k
            voice += amp * np.sin(k * phase) * (fk < sr * 0.45)
        # syllables, and a voice that talks for a few seconds then listens for a few
        gate = np.clip(np.sin(np.pi * pos) ** 2 * 1.3, 0, 1) * (wobbly(m, sr, 0.16, 0.2, 1.0))
        talking = np.clip((wobbly(m, sr, 2.5, -1, 1.6)) * 3, 0, 1)
        voice *= gate * talking
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
    n = frames if looping else frames + int(3.5 * RATE)
    buf = np.zeros((n, 2))
    for part in song['parts']:
        vol, pan = part.get('vol', 0.5), part.get('pan', 0.0)
        gains = vol * np.sqrt(0.5 * (1 - pan)), vol * np.sqrt(0.5 * (1 + pan))
        sway = part.get('sway', 0.0)  # seconds of drunken slop in when each note lands
        for step, length, pitches, vel in parse(part, song['bars'], bar_steps):
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
    buf = reverb(buf, song.get('reverb', 1.6), song.get('wet', 0.25), looping)
    if song.get('wow'):
        buf = wow(buf, *song['wow'])
    # Match loudness between songs, then a soft limiter so peaks round off instead of clipping.
    rms = np.sqrt((buf ** 2).mean())
    buf *= 0.17 / rms
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


SOUNDS = {'buzz': sfx_buzz, 'zap': sfx_zap, 'tink': sfx_tink, 'catch': sfx_catch, 'door': sfx_door}
SOUND_OUT = OUT.parent / 'sounds'


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
            audio = SOUNDS[name]()
            audio = (audio / np.abs(audio).max() * 0.8).astype(np.float32)[:, None]
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
