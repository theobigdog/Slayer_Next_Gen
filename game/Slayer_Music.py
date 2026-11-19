"""Slayer_Music: the soundtrack and sound effects. The window version plays them; the command-prompt version stays quiet.

The songs are .ogg files in assets/music/, the effects in assets/sounds/, all composed and rendered by
tools/make_music.py (all original).
    play('tavern')     loop a song (the old one fades out, then the new one fades in; the same song again does nothing)
    sting('victory')   a one-off: the loop stops and the sting plays (the next play() starts music again)
    sound('door')      a one-off effect over whatever is playing (combat: see Slayer_Combat.attack_sound/hurt_sound)
    tube(0.6)          the title's flickering fluorescent tube: its buzz at 0 (dark) .. 1 (lit); the next play() stops it
    set_volume(0.4)    0 = off .. 1 = full (the window's volume slider, for music and effects); remembered for next time
    toggle()           off, or back to the volume it was at (clicking the ♪ next to the slider)
    update()           called every frame by the window: starts a song once the one before it has faded out
Game code goes through Slayer_UI.music() / sting() / sound(), so the command-prompt version never loads pygame's mixer.
If anything about sound fails (no speakers, no mixer, a missing file), the game carries on in silence.
"""
import random
import time

import pygame

import Slayer_Accessory as acc

FOLDER = acc.root_dir / 'assets' / 'music'
SOUND_FOLDER = acc.root_dir / 'assets' / 'sounds'
DEFAULT_VOLUME = 0.1    # Ted, Nov 17: 0.5 was "so fucking loud", and 0.25 still too much
STING_BOOST = 1.3       # stings play a little louder than the loop
SFX_BOOST = 1.2         # and so do the effects
FADE_MS = 900           # a new song fading in
FADE_OUT_MS = 500       # the old one fading out first
# Songs that take their time coming in: (fade the old one out, fade this one in), in ms.
SLOW_FADES = {'seedy': (2500, 3500),         # the jig dies away as the tavern door creaks shut behind the party
              'resurrection': (500, 4000),   # creeping in under Happy's breakdown
              'lurk': (2500, 3000),          # the jolly music dies away as they drop into the basin
              'enraged': (250, 300)}         # NOW HE'S ANGRY: no waiting about
# Songs that play once and then hand over to a loop: the basin's creeping build-up, then the creep at its worst.
THEN = {'lurk': 'lurk_loop'}
SAVE_FILE = acc.player_dir / 'music_volume.txt'     # (in the browser: localStorage, see _load/_save)
BROWSER_KEY = 'slayer_music_volume'

_current = None     # the song looping now (or fading in next)
_wanted = None      # the song that should be looping (kept while it's off, so turning it up brings it back)
_pending = None     # (song, when, fade-in ms): the next song, waiting for the last one to fade out
_stings = {}        # name -> pygame Sound
_sounds = {}        # name -> pygame Sound
_tube = None        # the Channel the title's fluorescent tube buzzes on


def _load() -> float:
    try:
        storage = acc.browser_storage()
        text = storage.getItem(BROWSER_KEY) if storage is not None else SAVE_FILE.read_text()
        return min(1.0, max(0.0, float(text)))
    except Exception:
        return DEFAULT_VOLUME


def _save():
    try:
        storage = acc.browser_storage()
        if storage is not None:
            storage.setItem(BROWSER_KEY, f'{volume:.2f}')
        else:
            SAVE_FILE.write_text(f'{volume:.2f}')
    except Exception:
        pass  # can't save it (read-only folder): it just starts at the default next time


volume = _load()
_unmuted = volume or DEFAULT_VOLUME   # what the ♪ brings it back to after turning it off


def on() -> bool:
    return volume > 0.001


def _ready() -> bool:
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            pygame.mixer.set_num_channels(16)  # the title's flicker can have a few clicks going at once
        return bool(pygame.mixer.get_init())
    except pygame.error:
        return False


def _start(name: str, fade_in: int):
    global _current
    tube_off()
    try:
        # Stop the old song outright first. Loading over a song that's still fading out makes pygame wait for the fade
        # to finish. On a PC that's a moment. In the browser the fade can't move while the game waits for it, so it
        # waited forever: the tablet froze whenever the song changed (Ted, Nov 18: the party screen, the first battle).
        pygame.mixer.music.stop()
        pygame.mixer.music.load(str(FOLDER / f'{name}.ogg'))
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(0 if name in THEN else -1, fade_ms=fade_in)
        _current = name
    except (pygame.error, FileNotFoundError):
        _current = None


def play(name: str):
    global _current, _wanted, _pending
    _wanted = name
    if not on() or name == _current or not _ready():
        return
    fade_out, fade_in = SLOW_FADES.get(name, (FADE_OUT_MS, FADE_MS))
    if _current and pygame.mixer.music.get_busy():
        pygame.mixer.music.fadeout(fade_out)
        _pending = (name, time.monotonic() + fade_out / 1000, fade_in)
        _current = name  # (so asking for it again while the old one fades does nothing)
    else:
        _pending = None
        _start(name, fade_in)


def update():
    global _pending, _wanted
    if _pending and time.monotonic() >= _pending[1]:
        name, _, fade_in = _pending
        _pending = None
        if on() and _ready():
            _start(name, fade_in)
    elif _current in THEN and not _pending and on() and _ready() and not pygame.mixer.music.get_busy():
        _wanted = THEN[_current]   # a play-once song has finished: its loop takes over
        _start(_wanted, 0)


def stop():
    global _current, _wanted, _pending
    _wanted, _pending = None, None
    if _current and _ready():
        pygame.mixer.music.fadeout(FADE_MS)
    _current = None


def sting(name: str):
    global _current, _pending
    if not on() or not _ready():
        return
    try:
        if name not in _stings:
            _stings[name] = pygame.mixer.Sound(str(FOLDER / f'{name}.ogg'))
        _stings[name].set_volume(min(1.0, volume * STING_BOOST))
        pygame.mixer.music.fadeout(300)
        _current, _pending = None, None
        _stings[name].play()
    except (pygame.error, FileNotFoundError):
        pass


def _sound(name: str):
    if name not in _sounds:
        _sounds[name] = pygame.mixer.Sound(str(SOUND_FOLDER / f'{name}.ogg'))
    return _sounds[name]


# Effects with several takes (grunt_1.ogg, grunt_2.ogg, ...): sound('grunt') picks one at random.
TAKES = {'grunt': 4, 'kobold': 3, 'yelp': 3, 'groan': 4, 'squeal': 3, 'growl': 2, 'whoosh': 3, 'roar': 2,
         'scream': 3, 'gag': 2, 'retch': 2, 'dwarf_die': 2, 'kobold_die': 2, 'wolf_die': 2, 'heroine_die': 3,
         'cackle': 3}
PILE_UP = 2         # at most this many of the same effect at once (an area attack hits everybody at the same moment)
PILE_UP_S = 0.25
_recent = {}        # name -> when it last started, for PILE_UP


def sound(name: str, level: float = 1.0):
    """A one-off effect ('door', 'fire', 'thunder', 'grunt', ...), at the slider's volume times level."""
    if not on() or not _ready():
        return
    now = time.monotonic()
    recent = [t for t in _recent.get(name, []) if now - t < PILE_UP_S]
    if len(recent) >= PILE_UP:
        return
    _recent[name] = recent + [now]
    try:
        s = _sound(f'{name}_{random.randint(1, TAKES[name])}' if name in TAKES else name)
        s.set_volume(min(1.0, volume * SFX_BOOST * level))
        s.play()
    except (pygame.error, FileNotFoundError):
        pass


def tube(level: float):
    """The title's fluorescent tube, buzzing at level (0 = dark, 1 = fully lit). It loops until tube_off()."""
    global _tube
    if not on() or not _ready():
        return
    try:
        if _tube is None:
            _tube = _sound('buzz').play(-1)
        if _tube is not None:
            _tube.set_volume(min(1.0, volume * SFX_BOOST * level))
    except (pygame.error, FileNotFoundError):
        _tube = None


def tube_off(fade_ms: int = 1200):
    global _tube
    if _tube is not None:
        try:
            _tube.fadeout(fade_ms) if fade_ms else _tube.stop()
        except pygame.error:
            pass
        _tube = None


def set_volume(level: float, save: bool = True):
    """The slider. 0 stops the music; anything above picks the song back up at that volume."""
    global volume, _current, _unmuted, _pending
    was_on = on()
    volume = min(1.0, max(0.0, level))
    if on():
        _unmuted = volume
    if _ready():
        if not on():
            pygame.mixer.music.fadeout(300)
            pygame.mixer.stop()
            _current, _pending = None, None
            tube_off(0)
        else:
            pygame.mixer.music.set_volume(volume)
            for s in _stings.values():
                s.set_volume(min(1.0, volume * STING_BOOST))
            if not was_on and _wanted:
                play(_wanted)
    if save:
        _save()


def toggle():
    """The ♪: off, or back to the volume it was at."""
    set_volume(0.0 if on() else _unmuted)
