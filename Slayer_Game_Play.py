import Slayer_Accessory as acc
from Slayer_Accessory import next, end, wt
import Slayer_Combat as combat
import Slayer_Heroes as heroes
import Slayer_Dwarf
import random
from colorama import Fore, Back, Style, Cursor
import time

def play_game(party: dict) -> dict:
    mob = Slayer_Dwarf.Disgruntled_Dwarf()
    combat.show_current_status(party['party'], mob)
    return party
