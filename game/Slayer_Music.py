"""Slayer_Music: the soundtrack. The window version plays it; the command-prompt version stays quiet.

The songs are .ogg files in assets/music/, composed and rendered by tools/make_music.py (all original).
    play('tavern')     loop a song (fades over from whatever was playing; the same song again does nothing)
    sting('victory')   a one-off: the loop stops and the sting plays (the next play() starts music again)
    set_volume(0.4)    0 = off .. 1 = full (the window's volume slider); remembered for next time
    toggle()           off, or back to the volume it was at (clicking the ♪ next to the slider)
Game code goes through Slayer_UI.music() / Slayer_UI.sting(), so the command-prompt version never loads pygame's mixer.
If anything about sound fails (no speakers, no mixer, a missing file), the game carries on in silence.
"""
import pygame

import Slayer_Accessory as acc

FOLDER = acc.root_dir / 'assets' / 'music'
DEFAULT_VOLUME = 0.25   # Ted, Nov 17: 0.5 was "so fucking loud"
STING_BOOST = 1.3       # stings play a little louder than the loop
FADE_MS = 900
SAVE_FILE = acc.player_dir / 'music_volume.txt'     # (in the browser: localStorage, see _load/_save)
BROWSER_KEY = 'slayer_music_volume'

_current = None     # the song looping now
_wanted = None      # the song that should be looping (kept while it's off, so turning it up brings it back)
_stings = {}        # name -> pygame Sound


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
        return bool(pygame.mixer.get_init())
    except pygame.error:
        return False


def play(name: str):
    global _current, _wanted
    _wanted = name
    if not on() or name == _current or not _ready():
        return
    try:
        pygame.mixer.music.load(str(FOLDER / f'{name}.ogg'))
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(-1, fade_ms=FADE_MS)
        _current = name
    except (pygame.error, FileNotFoundError):
        _current = None


def stop():
    global _current, _wanted
    _wanted = None
    if _current and _ready():
        pygame.mixer.music.fadeout(FADE_MS)
    _current = None


def sting(name: str):
    global _current
    if not on() or not _ready():
        return
    try:
        if name not in _stings:
            _stings[name] = pygame.mixer.Sound(str(FOLDER / f'{name}.ogg'))
        _stings[name].set_volume(min(1.0, volume * STING_BOOST))
        pygame.mixer.music.fadeout(300)
        _current = None
        _stings[name].play()
    except (pygame.error, FileNotFoundError):
        pass


def set_volume(level: float, save: bool = True):
    """The slider. 0 stops the music; anything above picks the song back up at that volume."""
    global volume, _current, _unmuted
    was_on = on()
    volume = min(1.0, max(0.0, level))
    if on():
        _unmuted = volume
    if _ready():
        if not on():
            pygame.mixer.music.fadeout(300)
            pygame.mixer.stop()
            _current = None
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
