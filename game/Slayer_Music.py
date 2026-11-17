"""Slayer_Music: the soundtrack. The window version plays it; the command-prompt version stays quiet.

The songs are .ogg files in assets/music/, composed and rendered by tools/make_music.py (all original).
    play('tavern')     loop a song (fades over from whatever was playing; the same song again does nothing)
    sting('victory')   a one-off: the loop stops and the sting plays (the next play() starts music again)
    toggle()           music on/off (the window's music button)
Game code goes through Slayer_UI.music() / Slayer_UI.sting(), so the command-prompt version never loads pygame's mixer.
If anything about sound fails (no speakers, no mixer, a missing file), the game carries on in silence.
"""
import pygame

import Slayer_Accessory as acc

FOLDER = acc.root_dir / 'assets' / 'music'
VOLUME = 0.5        # music volume (first guess; stings play a little louder)
FADE_MS = 900

_current = None     # the song looping now
_wanted = None      # the song that should be looping (kept while muted, so unmuting brings it back)
_stings = {}        # name -> pygame Sound
on = True


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
    if not on or name == _current or not _ready():
        return
    try:
        pygame.mixer.music.load(str(FOLDER / f'{name}.ogg'))
        pygame.mixer.music.set_volume(VOLUME)
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
    if not on or not _ready():
        return
    try:
        if name not in _stings:
            _stings[name] = pygame.mixer.Sound(str(FOLDER / f'{name}.ogg'))
            _stings[name].set_volume(min(1.0, VOLUME * 1.4))
        pygame.mixer.music.fadeout(300)
        _current = None
        _stings[name].play()
    except (pygame.error, FileNotFoundError):
        pass


def toggle():
    """The music button: off stops everything, on picks the song back up."""
    global on, _current
    on = not on
    if not on:
        if _ready():
            pygame.mixer.music.fadeout(300)
            pygame.mixer.stop()
        _current = None
    elif _wanted:
        play(_wanted)
