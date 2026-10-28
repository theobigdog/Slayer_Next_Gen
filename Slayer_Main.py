import Slayer_Accessory as acc
from Slayer_Accessory import next, end, wt
import Slayer_Graphics as gr
import Slayer_Form_Party as fp
import Slayer_Game_Play as gp

wt()
gr.slayer_opening()
#next() # Once the gr.slayer_opening() is set to "non-dev" settings, I want the player to get a look at the opening, so I want next here when the game is ready for real play
wt()
party_dict = fp.get_party()
party_dict = gp.play_game(party_dict)
confirm_save = acc.yes_no(input(f"Would you like to save your game (as {party_dict['name'].title()})?  "))
if confirm_save:
    acc.save_party(party_dict)
#gr.loser_banner() # I don't need to see this banner every test, put this back in when the game is done
end()