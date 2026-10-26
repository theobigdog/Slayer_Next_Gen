import Slayer_Accessory as acc
from Slayer_Accessory import next, end, wt
import Slayer_Combat as combat
import Slayer_Heroes as heroes
import Slayer_Dwarf
import Slayer_Narration as nar
import random
from colorama import Fore, Back, Style, Cursor
import time

happy_buddy_names = ['Burpy', 'Gassy', 'Smelly', 'Grumpy', 'Hairy', 'Slappy', 'Fuck-Head']

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
    return any(not mob.is_dead for mob in mobs)

def check_wiped(party: list) -> bool:
    return all(heroine.is_dead for heroine in party)


def play_game(party_dict: dict) -> dict:
    if party_dict['times_run_dungeon'] == 1:  #### THIS NEEDS TO BE COMMENTED BACK IN when working on narration, I just don't want to have to deal with it for every test during dev haha
        party_dict['narration'] = acc.yes_no(input('Would you like narrative?  '))
        if party_dict['narration']:
            print("Really?  Oh hell yes, I've been practicing my voices.")
        else:
            print("Fair.  I'll be over here.  Quietly.  Silently judging the mobs, not you.")
        next()
        if party_dict['narration']:
            nar.intro()
            nar.happy_intro()
    else:
        first = acc.yes_no(input(f"I'm assuming you don't want to hear me blabber the-fuck on about details again, do you?"))
        if first:
            _ = acc.yes_no(input(f"Uh, yes you DO want me to provide narrative, or not?"))
        else:
            _ = acc.yes_no(input(f"Oh, so no I assumed wrong you you do need narrative again, or did you mean you didn't want repeated narrative?")) 
        time.sleep(0.3)
        print("But wait, bone-head, you're still not clearly answering my question.....")
        time.sleep(0.75)
        print("I could go on like this all day....")
        time.sleep(0.3)
        print('Oh, right.  Sorry.')
        time.sleep(0.2)

        party_dict['narration'] = acc.yes_no(input(f"Ok, for realsies, would you like narration?")) # need to change this as a final question, which phrases it in such a way that it is very clear now
        if party_dict['narration']:
            print("Shirley you can't be serious....")
            time.sleep(0.3)
            print(f"Sorry, I'll stop calling you \"Shirley\", {party_dict['name']}...")
            time.sleep(0.7)
            print('You beautiful masochist.')
            time.sleep(1)
        else:
            print('Understood.  Grabbing a roll of duct tape for my own mouth....')
            next()

    buddy1 = random.choice(happy_buddy_names)
    buddy2 = random.choice([x for x in happy_buddy_names if x != buddy1])
    mobs = [Slayer_Dwarf.Disgruntled_Dwarf('Happy'), Slayer_Dwarf.Drunk_Dwarf(buddy1), Slayer_Dwarf.Drunk_Dwarf(buddy2)]

    encounter_over = False
    round_num = 0
    while not party_dict['wiped'] and alive_mobs(mobs) and not encounter_over:
        round_num += 1
        turn_order = get_turn_order(party_dict['party'], mobs)
        for attacker in turn_order:
            if not attacker.is_dead and alive_mobs(mobs):
                #print(f"Round {round}:\n\n")
                combat.show_current_status(party_dict['party'], mobs, round_num)
                time.sleep(0.5)
                if hasattr(attacker, 'hero_class'): # player's turn with the given heroine
                    party_dict, mobs, luck_roll = combat.player_turn(attacker, party_dict, mobs)
                    if luck_roll and not attacker.is_dead and alive_mobs(mobs): #  Intentionally, this does not loop, only one lucky attack per round ;)
                        print(f"{attacker.heroine_name}'s lucky fuckin' day!  She get's a second turn.  Make it count!")
                        next()
                        combat.show_current_status(party_dict['party'], mobs, round_num)
                        party_dict, mobs, _ = combat.player_turn(attacker, party_dict, mobs)
                    for mob in mobs:
                        if not mob.is_dead:
                            response_attack = False
                            if mob.enraged:
                                response = acc.multi_roll(1,100)
                                if response <= (mob.stats['enraged_turn'] * 100):
                                    response_attack = True
                            else:
                                response = acc.multi_roll(1,100)
                                if response <= (mob.stats['turn'] * 100):
                                    response_attack = True
                            if response_attack:
                                party_dict['wiped'] = check_wiped(party_dict['party'])
                                party_dict, mobs, _ = combat.mob_turn(mob, party_dict, mobs)
                                
                else: # mob-group's turn with the given mob(attacker)
                    party_dict, mobs, luck_roll = combat.mob_turn(attacker, party_dict, mobs)
                    party_dict['wiped'] = check_wiped(party_dict['party'])
                    if luck_roll and not attacker.is_dead and alive_mobs(mobs) and not party_dict['wiped']:#  Intentionally, this does not loop, only one lucky attack per round ;) - though it's possible I might want to be able to toggle this for mobs so that multiple luck rolls are possible.  Maybe a separate luck function for certain mob class_types
                        print(f"Oh, shit.  {attacker.name} gets a second attack!  Brace yourselves!")
                        next()
                        combat.show_current_status(party_dict['party'], mobs, round_num)
                        party_dict, mobs, _ = combat.mob_turn(attacker, party_dict , mobs)
                party_dict['wiped'] = check_wiped(party_dict['party'])
                if mobs[0].is_dead and mobs[0].mob_class == 'Disgruntled Dwarf' and alive_mobs(mobs) and not party_dict['wiped']:
                    #party_dict = mobs[0].trigger_happy_wipe(party_dict, True)
                    #party_dict = acc.refresh_party(party_dict, False)
                    encounter_over = True
                    break
        if party_dict['wiped'] or not alive_mobs(mobs):
            combat.show_current_status(party_dict['party'], mobs, round_num)
            next()
    if (party_dict['wiped'] or mobs[0].is_dead) and mobs[0].mob_class == 'Disgruntled Dwarf':
        if mobs[0].is_dead:
            party_dict = mobs[0].trigger_happy_wipe(party_dict, True)
        else:
            party_dict = mobs[0].trigger_happy_wipe(party_dict, False)
        party_dict = acc.refresh_party(party_dict, False)

    return party_dict
