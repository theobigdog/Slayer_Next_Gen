import Slayer_Accessory as acc
from Slayer_Accessory import next, end, wt
import Slayer_Graphics as gr
import Slayer_Form_Party as fp
import Slayer_Game_Play as gp

wt()
dev_mode = acc.dev_mode()
gr.slayer_opening()
if not dev_mode:
    next()
wt()
party_dict = fp.get_party()
party_dict = gp.play_game(party_dict)
confirm_save = acc.yes_no(input(f"Would you like to save your game (as {party_dict['name'].title()})?  "))
if confirm_save:
    acc.save_party(party_dict)
if not dev_mode:
    gr.loser_banner()
end()