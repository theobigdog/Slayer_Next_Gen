import Slayer_Accessory as acc
from Slayer_Accessory import next, end, wt
import Slayer_Combat as combat
import Slayer_Heroes as heroes
import Slayer_Dwarf
import Slayer_Narration as nar
import random
from colorama import Fore, Back, Style, Cursor
import time

def get_turn_order(party: dict, mobs: list) -> list:
    heroine_dice_cutoff = acc.get_dice_cutoffs()['speed_cutoff']
    mob_dice_cutoff = acc.get_dice_cutoffs_mobs()['speed_cutoff']
    entity_dict = {}
    for heroine in party:
        if not heroine.is_dead:
            speed = heroine.stats['speed']
            speed_roll = acc.multi_roll(1,heroine_dice_cutoff)
            entity_dict[heroine] = speed + speed_roll
    for mob in mobs:
        speed = None
        if not mob.is_dead:
            if mob.enraged:
                speed = mob.stats['enraged_speed']
            else:
                speed = mob.stats['speed']
            speed_roll = acc.multi_roll(1,mob_dice_cutoff)
            entity_dict[mob] = speed + speed_roll
    return sorted(entity_dict, key=entity_dict.get, reverse=True)
    
    


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
    mobs = [Slayer_Dwarf.Disgruntled_Dwarf()]
    #combat.show_current_status(party['party'], mobs)
    #next()

    turn_order = get_turn_order(party['party'], mobs)
    for attacker in turn_order:
        if not attacker.is_dead:
            combat.show_current_status(party['party'], mobs)
            next()
            #luck_roll = False
            if hasattr(attacker, 'hero_class'):
                party['party'], mobs, luck_roll = combat.player_turn(attacker, party['party'], mobs)
                if luck_roll and not attacker.is_dead:
                    print(f"{attacker.heroine_name}'s lucky fuckin' day!  She get's a second turn.  Hope you do better this time...")
                    next()
                    combat.show_current_status(party['party'], mobs)
                    next()
                    party['party'], mobs, _ = combat.player_turn(attacker, party['party'], mobs)
            else:
                party['party'], mobs, luck_roll = combat.mob_turn(attacker, party['party'], mobs)
                if luck_roll and not attacker.is_dead:
                    print(f"Well \"lucky\" you.  {attacker.name} gets a second attack!")
                    next()
                    combat.show_current_status(party['party'], mobs)
                    next()
                    party['party'], mobs, _ = combat.mob_turn(attacker, party['party'], mobs)

    return party
