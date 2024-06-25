import Slayer_Accessory as acc
from Slayer_Accessory import next, end, wt
import Slayer_Graphics as gr
import Slayer_Form_Party as fp

wt()
gr.slayer_opening()
#next()
wt()
party = fp.get_party()
#play_game(party)
#next()
temp_save = acc.yes_no(input(f"Would you like to save your game (as {party['name'].title()})?  "))
if temp_save:
    acc.save_party(party)
#gr.loser_banner()
end()



