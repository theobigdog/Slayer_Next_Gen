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


def additive(f, dur, weights, attack=0.02, release=0.12, vib=(5.5, 0.0, 0.0), bright=None):
    """A sum of harmonics. vib = (rate Hz, depth, delay s): vibrato that swells in after the delay."""
    hold = int(dur * RATE)
    n = hold + int(release * RATE)
    t = np.arange(n) / RATE
    rate, depth, delay = vib
    swell = np.clip((t - delay) / 0.3, 0, 1) if depth else 0
    inst_f = f * (1 + depth * swell * np.sin(2 * np.pi * rate * t + rng.uniform(0, 6)))
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


def drum(kind, vel):
    length = {'k': 0.4, 'b': 0.45, 'x': 0.06, 's': 0.25, 'h': 0.06, 't': 0.6, 'g': 3.5}.get(kind, 0.2)
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
    else:
        out = np.zeros(n)
    return out * vel


INSTRUMENTS = {'fiddle': fiddle, 'whistle': whistle, 'drone': drone, 'brass': brass, 'strings': strings,
               'choir': choir, 'bell': bell, 'lute': lute, 'pizz': cello_pizz}


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
        for step, length, pitches, vel in parse(part, song['bars'], bar_steps):
            start = int(round(step * step_s * RATE))
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
    buf = reverb(buf, song.get('reverb', 1.6), song.get('wet', 0.25), looping)
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

SONGS = {
    # The tavern (and the title and party screens): a rowdy jig for Happy and his drunk mates.
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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    wanted = sys.argv[1:] or list(SONGS)
    for name in wanted:
        song = SONGS[name]
        audio = render(song)
        path = OUT / f'{name}.ogg'
        # Written a little at a time: libsndfile's Vorbis encoder overflows its stack on one big write.
        with soundfile.SoundFile(str(path), 'w', RATE, 2, format='OGG', subtype='VORBIS') as f:
            for i in range(0, len(audio), 4096):
                f.write(audio[i:i + 4096])
        print(f'{name}: {len(audio) / RATE:.1f} s, peak {np.abs(audio).max():.2f}, '
              f'{path.stat().st_size // 1024} KB -> {path.relative_to(OUT.parent.parent)}')


if __name__ == '__main__':
    main()
