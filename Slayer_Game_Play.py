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
    combat.show_current_status(party['party'], mobs)
    next()

    turn_order = get_turn_order(party['party'], mobs)
    for attacker in turn_order:
        if hasattr(attacker, 'hero_class'):
            party['party'], mobs = combat.player_turn(attacker, party['party'], mobs)
        else:
            party['party'], mobs = combat.mob_turn(attacker, party['party'], mobs)


    """
    for i in range(10):
        turn_order = get_turn_order(party['party'], mobs)
        print(f'Round{i}')
        for entry in turn_order:
            try:
                print(f'{entry.heroine_name}:  {entry.hero_class}')
            except(AttributeError):
                print(f'{entry.name}')
        print()
    mobs[0].enraged = True
    for i in range(10):
        turn_order = get_turn_order(party['party'], mobs)
        print(f'Round{i}')
        for entry in turn_order:
            try:
                print(f'{entry.heroine_name}:  {entry.hero_class}')
            except(AttributeError):
                print(f'Enraged {entry.name}')
        print()
    mobs[0].is_dead = True
    #party['party'][0].is_dead = True
    #party['party'][2].is_dead = True
    for i in range(10):
            turn_order = get_turn_order(party['party'], mobs)
            print(f'Round{i}')
            for entry in turn_order:
                try:
                    print(f'{entry.heroine_name}:  {entry.hero_class}')
                except(AttributeError):
                    print(f'Enraged {entry.name}')
            print()
    """
            

    '''
    #print([x for x in mob.inv]) ############
    #for x in mob.inv.keys():
    #    print(f"{x}: {mob.inv[x]}")
    #mob_rolls = combat.get_mob_rolls(mob)
    #for x in mob.stats:
    #    print(f"{x}: {mob.stats[x]}")
    #next()
    #mob.enraged = True
    
    for stat in mob.stats:
        print(stat + ': ' + str(mob.stats[stat]))
    next()
    for i in range(5):
        mob_rolls = combat.get_mob_rolls(mob)
        for x in mob_rolls:
            print(f"{x}: {mob_rolls[x]}")
        next()  ##################
    
    for heroine in party['party']:
        heroine_rolls = combat.get_heroine_rolls(heroine)
        for x in heroine_rolls:
            print(f"{x}: {heroine_rolls[x]}")
        next()
    '''
    return party
