"""Starts Slayer in a Pygame window. (game/Slayer_Main.py still starts the command-prompt version.)

This file has to be called main.py: pygbag, which packs the game for the browser, looks for it.
On the web there's no window to close, so after "The End" a click starts a fresh game.
"""
import asyncio
import os
import sys
import pygame  # unused here, but Pydroid 3 (Android) looks for this line to start in graphics mode

# The game's code lives in the game folder next to this file. Putting it on the import path lets every
# Slayer_*.py keep importing the others by name, here, in Slayer.exe and in the browser.
here = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()  # (the browser may not set __file__)
sys.path.insert(0, os.path.join(here, 'game'))

import Slayer_UI as ui
from Slayer_Window import WindowUI


async def main():
    while True:
        window = WindowUI()
        ui.use(window)
        import Slayer_Main # imported after ui.use, so the game talks to the window from its first line
        if await window.run(Slayer_Main.play()) != 'restart':
            break

asyncio.run(main())
