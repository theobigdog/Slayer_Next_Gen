import Slayer_Accessory as acc
from Slayer_Accessory import next, end, wt
import Slayer_Combat as combat
import Slayer_Heroes as heroes
import Slayer_Dwarf
import Slayer_Narration as nar
import random
from colorama import Fore, Back, Style, Cursor
import time

def play_game(party: dict) -> dict:
    narration = acc.yes_no(input('Would you like narrative?  '))
    if narration == True:
        print("Really?  It's super boring, but, whatever.")
    else:
        print("Oh I see how it is.  Fine.  I'll just shutup then.")
    next()
    if narration:
        nar.intro()
    mob = Slayer_Dwarf.Disgruntled_Dwarf()
    combat.show_current_status(party['party'], mob)
    next()
    return party
