"""Starts Slayer in a Pygame window. (Slayer_Main.py still starts the command-prompt version.)

This file has to be called main.py: pygbag, which packs the game for the browser, looks for it.
On the web there's no window to close, so after "The End" a click starts a fresh game.
"""
import asyncio
import pygame  # unused here, but Pydroid 3 (Android) looks for this line to start in graphics mode
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
