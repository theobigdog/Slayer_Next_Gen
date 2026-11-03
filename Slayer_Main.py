import asyncio
import Slayer_Accessory as acc
import Slayer_UI as ui
from Slayer_UI import pause, clear, yes_no, title_screen, loser_banner
import Slayer_Form_Party as fp
import Slayer_Game_Play as gp

async def play():
    await clear()
    dev_mode = acc.dev_mode()
    await title_screen()
    if not dev_mode:
        await pause()
    await clear()
    party_dict = await fp.get_party()
    party_dict = await gp.play_game(party_dict)
    confirm_save = await yes_no(f"Would you like to save your game (as {party_dict['name'].title()})?  ")
    if confirm_save:
        await acc.save_party(party_dict)
    if not dev_mode:
        await loser_banner()
    await acc.end()

if __name__ == '__main__': # run this file for the command-prompt version; main.py starts the Pygame window
    ui.use(ui.TerminalUI())
    asyncio.run(play())
