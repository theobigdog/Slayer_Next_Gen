import Slayer_Accessory as acc
from Slayer_Accessory import next
import Slayer_Combat as combat
import Slayer_Dwarf
import Slayer_Narration as nar
import random
import time

happy_buddy_names = ['Burpy', 'Gassy', 'Smelly', 'Grumpy', 'Hairy', 'Slappy', 'Fuck-Head']

def get_turn_order(party: list, mobs: list) -> list:
    heroine_dice_cutoff = acc.get_dice_cutoffs()['speed_cutoff']
    mob_dice_cutoff = acc.get_dice_cutoffs_mobs()['speed_cutoff']
    entity_dict = {}
    for heroine in party:
        if not heroine.is_dead:
            speed = heroine.stats['speed']
            speed_roll = acc.multi_roll(1,heroine_dice_cutoff)
            entity_dict[heroine] = speed + speed_roll
    for mob in mobs:
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
    dev_mode = acc.dev_mode()
    if not dev_mode:
        if party_dict['times_run_dungeon'] == 1:
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
            first = acc.yes_no(input("I'm assuming you don't want to hear me blabber the-fuck on about details again, do you?  "))
            if first:
                _ = acc.yes_no(input("Uh, yes you DO want me to provide narrative, or not?  "))
            else:
                _ = acc.yes_no(input("Oh, so no I assumed wrong you do need narrative again, or did you mean you didn't want repeated narrative?  ")) 
            time.sleep(0.3)
            print("But wait, bone-head, you're still not clearly answering my question.....")
            time.sleep(0.75)
            print("I could go on like this all day....")
            time.sleep(0.3)
            print('Oh, right.  Sorry.')
            time.sleep(0.2)

            party_dict['narration'] = acc.yes_no(input("Ok, for realsies, would you like narration?  "))
            if party_dict['narration']:
                print("Shirley you can't be serious....")
                time.sleep(0.3)
                print(f"Sorry, I'll stop calling you \"Shirley\", {party_dict['name']}...")
                time.sleep(0.7)
                print('You beautiful masochist.')
                time.sleep(1)
            else:
                print('Understood.  Grabbing a roll of duct tape for my own mouth.')
                time.sleep(0.5)
                print('Umm....  May I at least have a small breathing hole?  I have a deviated septum and I\'m a mouth-breather....')
                next()

    happy = Slayer_Dwarf.Disgruntled_Dwarf('Happy')
    buddy1, buddy2 = random.sample(happy_buddy_names, 2)
    mobs = [happy, Slayer_Dwarf.Drunk_Dwarf(buddy1), Slayer_Dwarf.Drunk_Dwarf(buddy2)]

    round_num = 0
    while not party_dict['wiped'] and alive_mobs(mobs):
        round_num += 1
        turn_order = get_turn_order(party_dict['party'], mobs)
        for attacker in turn_order:
            if not attacker.is_dead and alive_mobs(mobs):
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
                            turn_stat = 'enraged_turn' if mob.enraged else 'turn'
                            if acc.multi_roll(1,100) <= mob.stats[turn_stat]:
                                party_dict['wiped'] = check_wiped(party_dict['party'])
                                combat.show_current_status(party_dict['party'], mobs, round_num)
                                print(f"{mob.name}, that insane bastard, moves like a horny jack-rabbit on a date and gets an extra attack.  Boo.")
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
        if party_dict['wiped'] or not alive_mobs(mobs):
            combat.show_current_status(party_dict['party'], mobs, round_num)
            next()
    if party_dict['wiped']:
        party_dict = happy.trigger_happy_wipe(party_dict, happy.is_dead)
        party_dict = acc.refresh_party(party_dict, False)

    return party_dict
