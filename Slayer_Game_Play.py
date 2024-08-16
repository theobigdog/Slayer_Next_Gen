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
    party['narration'] = acc.yes_no(input('Would you like narrative?  '))
    if party['narration']:
        print("Really?  It's super boring, but, whatever.")
    else:
        print("Oh I see how it is.  Fine.  I'll just shutup then.")
    next()
    if party['narration']:
        nar.intro()
        nar.happy_intro()
    mob = Slayer_Dwarf.Disgruntled_Dwarf()
    combat.show_current_status(party['party'], mob)
    next()
    #print([x for x in mob.inv]) ############
    #for x in mob.inv.keys():
    #    print(f"{x}: {mob.inv[x]}")
    #mob_rolls = combat.get_mob_rolls(mob)
    #for x in mob.stats:
    #    print(f"{x}: {mob.stats[x]}")
    #next()
    #mob.enraged = True
    '''
    for stat in mob.stats:
        print(stat + ': ' + str(mob.stats[stat]))
    next()
    for i in range(5):
        mob_rolls = combat.get_mob_rolls(mob)
        for x in mob_rolls:
            print(f"{x}: {mob_rolls[x]}")
        next()  ##################
    '''
    for heroine in party['party']:
        heroine_rolls = combat.get_heroine_rolls(heroine)
        for x in heroine_rolls:
            print(f"{x}: {heroine_rolls[x]}")
        next()
    return party
