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
    
def alive_mobs(mobs: list) -> bool:
    living_mobs = [x for x in mobs if not x.is_dead]
    return len(living_mobs) > 0

def check_wiped(party : list) -> bool:
    return all(heroine.is_dead for heroine in party)


def play_game(party: dict) -> dict:
    if party['narration']:
        party['narration'] = acc.yes_no(input('Would you like narrative?  '))
        if party['narration']:
            print("Really?  It's super boring, but, whatever.")
        else:
            print("Oh I see how it is.  Fine.  I'll just shutup then.")
        next()
        if party['narration']:
            nar.intro()
            nar.happy_intro()
    else:
        first = acc.yes_no(input(f"I'm assuming you don't want to hear me blabber the-fuck on about details again, do you?"))
        if first:
            second = acc.yes_no(input(f"Uh, yes you DO want me to provide narrative, or not?"))
        else:
            second = acc.yes_no(input(f"Oh, so no I assumed wrong you you do need narrative again, or did you mean you didn't want repeated narrative?")) 
        time.sleep(0.3)
        print("But wait, bone-head, you're still not clearly answering my question.....")
        print("I could go on like this all day....")
        time.sleep(0.3)
        print('Oh, right.  Sorry.')
        time.sleep(0.2)

        party['narration'] = acc.yes_no(input(f"Ok, for realsies, would you like narration?")) # need to change this as a final question, which phrases it in such a way that it is very clear now
        if party['narration']:
            print("Shirley you can't be serious....")
            time.sleep(0.3)
            print(f"Sorry, I'll stop calling you \"Shirley\", {party.name}...")
            time.sleep(0.7)
            print('You masochistic fuck.')
            time.sleep(1)
        else:
            print('What a jerk!  Fine.  Grabbing a roll of duct tape....')
            next()

    mobs = [Slayer_Dwarf.Disgruntled_Dwarf('Happy'), Slayer_Dwarf.Disgruntled_Dwarf('Sneezy')]

    #encounter_over = False
    round = 0
    while not party['wiped'] and alive_mobs(mobs):
        round += 1
        turn_order = get_turn_order(party['party'], mobs)
        for attacker in turn_order:
            if not attacker.is_dead and alive_mobs(mobs):
                print(f"Round {round}:\n\n")
                combat.show_current_status(party['party'], mobs)
                time.sleep(0.5)
                if hasattr(attacker, 'hero_class'): # player's turn with the given heroine
                    party, mobs, luck_roll = combat.player_turn(attacker, party, mobs)
                    if luck_roll and not attacker.is_dead and alive_mobs(mobs): #  Intentionally, this does not loop, only one lucky attack per round ;)
                        print(f"{attacker.heroine_name}'s lucky fuckin' day!  She get's a second turn.  Hope you do better this time...")
                        next()
                        combat.show_current_status(party['party'], mobs)
                        party, mobs, _ = combat.player_turn(attacker, party, mobs)
                else: # mob's turn with the given mob(attacker)
                    party, mobs, luck_roll = combat.mob_turn(attacker, party, mobs)
                    party['wiped'] = check_wiped(party['party'])
                    if luck_roll and not attacker.is_dead and alive_mobs(mobs) and not party['wiped']:#  Intentionally, this does not loop, only one lucky attack per round ;) - though it's possible I might want to be able to toble this for mobs so that multiple luck rolls are possible.  Maybe a separate luck function for certain mob class_types
                        print(f"Well \"lucky\" you.  {attacker.name} gets a second attack!")
                        next()
                        combat.show_current_status(party['party'], mobs)
                        party, mobs, _ = combat.mob_turn(attacker, party , mobs)
                party['wiped'] = check_wiped(party['party'])
        if party['wiped'] or not alive_mobs(mobs):
            combat.show_current_status(party['party'], mobs)
            next()
            #encounter_over = True
    return party
