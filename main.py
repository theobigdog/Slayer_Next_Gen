"""Starts Slayer in a Pygame window. (Slayer_Main.py still starts the command-prompt version.)

This file has to be called main.py: pygbag, which packs the game for the browser, looks for it.
"""
import asyncio
import Slayer_UI as ui
from Slayer_Window import WindowUI


async def main():
    window = WindowUI()
    ui.use(window)
    import Slayer_Main # imported after ui.use, so the game talks to the window from its first line
    await window.run(Slayer_Main.play())

asyncio.run(main())
