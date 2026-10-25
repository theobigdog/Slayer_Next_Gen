import random
from msvcrt import kbhit, getch
#import time
from colorama import Fore, Back, Style, Cursor, win32, init
from colorama.winterm import WinTerm
import pandas as pd
#import uuid
#import csv
#from dataclasses import dataclass
import joblib as jb

init()

yes = ['YES','Y']
no = ['NO','N']

whines = ["Jesus Christ, this dungeon's plumbing is a nightmare. Sorry, I'm good, I'm good", "Would you stop that sh-- oh, sorry, I was yelling at the banshee in the walls", "I haven't had a day off since the Third Age, but sure, let's go", "I'm running on four hours of sleep and pure spite, but for YOU? Anything", "Why do I do this to myself?  I told mother I would never.... Umm Hi!", "Sometimes, I just care too fucking much about this, that's my problem.  What?  Oh!"]

items = pd.read_csv('supporting_docs/items.csv')
stats = pd.read_csv('supporting_docs/hero_stats.csv')
mobs = pd.read_csv('supporting_docs/mobs.csv')
mob_equipment = pd.read_csv('supporting_docs/mob_equipment.csv')


def get_hero_classes():
    return ['Warrior', 'Shifter', 'Battle_Mage', 'Hunter', 'Witch', 'Sapper', 'Cleric']

def yes_no(response : str) -> bool:
    response = str(response).upper()
    while (response not in yes) and (response not in no):
        response = str(input("Let's pretend you didn't type that and try again.  Yes or No?:  ")).upper()
    return True if response in yes else False

def next():
    done = False
    while not done:
        if kbhit():
            key = ord(getch())
            if key == 13:
                print()
                done = True

def wt():
    #init()
    winterm = WinTerm()
    winterm.erase_screen(mode=2)
    print()
    print()

def end(full = False):
    print()
    print("The End.")
    if full:
        x = "Fill stuff in here later"
    print()
    print()
    exit()

def multi_roll(low_range : int, high_range : int) -> int:
    return random.randint(low_range, high_range)

def get_dice_cutoffs() -> dict: ### These are only for heroine, not mobs
    return {
        'low' : 1,
        'crit_cutoff' : 100,#20,
        'crit_mult_cutoff' : 2.5, ##  Does it even make sense to have this?
        #'low_miss' : 1,
        #'high_miss' : 100,
        #'miss_threshold' : 70,
        'hit_cutoff' : 100,
        'luck_cutoff' : 100,#20,
        'speed_cutoff' : 40,
        'expertise_cutoff' : 100,#50,
        'toughness_cutoff' : 100,#20,
        'dodge_cutoff' : 100,#15,
        'parry_cutoff' : 100,#20,
        'fear_cutoff' : 100,#20,
        'heal_cutoff' : 100,
        'aoe_heal_cutoff' : 100,#20,
    }

def get_dice_cutoffs_mobs() -> dict:  ### These are only for mobs, not heroine
    return {
        'crit_cutoff' : 100,#20,
        'crit_mult_cutoff' : 5, ## Does it even make sense to have this?
        'hit_cutoff' : 100,#30,
        'luck_cutoff' : 100,#20,
        'speed_cutoff' : 40,
        'expertise_cutoff' : 100,#20,
        'toughness_cutoff' : 100,#20,
        'dodge_cutoff' : 100,#15,
        'healing_chance_cutoff' : 100,#20,
        'scare_cutoff' : 100,#20,
        'low' : 1,
    }

def print_classes():
    print('Class Options:')
    print()
    for hero_class in get_hero_classes():
        print(hero_class)

def save_party(party : dict):
    jb.dump(party, f"saved_parties/{party['name'].title()}.pkl")
    print(f"Your party has been saved as {party['name'].title()}.")
    print(f"Keep track of this saved name if you want to recover your party: {party['name'].title()}")
    next()

def load_party(name : str = 'saved_parties/default.pkl') -> list:
    return jb.load(f'saved_parties/{name.title()}.pkl')

def whine() -> str:
    whine_itself = whines[random.randint(0, len(whines)-1)]
    whine_itself = str("..." + whine_itself)
    return whine_itself

def print_player_starting_summary(party : list, items : pd.DataFrame = items):
    for dudette in party:
        print(f"{dudette.heroine_name}:  {dudette.hero_class}")
        print('Inventory:  ')
        for inv_item in dudette.inv:
            item = items[items['item'] == inv_item]['item_desc'].values[0]
            print(item)
        print(f"Starting Health: {int(round(dudette.starting_health, 0))}")
        print()
    next()

def get_items() -> pd.DataFrame:
    return items

def get_stats() -> pd.DataFrame:
    return stats

def get_mobs() -> pd.DataFrame:
    return mobs

def get_mob_equipment() -> pd.DataFrame:
    return mob_equipment

def get_mob_stats(mob_class: str, mobs: pd.DataFrame) -> dict:
    index = mobs.index[mobs['mob_class'] == mob_class]
    return {
        'turn': mobs[mobs['mob_class'] == mob_class]['turn_chance'][index].values[0],
        'enraged_turn': mobs[mobs['mob_class'] == mob_class]['enraged_turn_chance'][index].values[0],
        'crit': mobs[mobs['mob_class'] == mob_class]['crit_multiplier'][index].values[0],
        'enraged_crit': mobs[mobs['mob_class'] == mob_class]['enraged_crit_multiplier'][index].values[0],
        'crit_chance': mobs[mobs['mob_class'] == mob_class]['crit_chance'][index].values[0],
        'enraged_crit_chance': mobs[mobs['mob_class'] == mob_class]['enraged_crit_chance'][index].values[0],
        'starting_hp': mobs[mobs['mob_class'] == mob_class]['starting_hp'][index].values[0],
        'enraged_hp': mobs[mobs['mob_class'] == mob_class]['enraged_hp'][index].values[0],
        'hit': mobs[mobs['mob_class'] == mob_class]['hit'][index].values[0],
        'enraged_hit': mobs[mobs['mob_class'] == mob_class]['enraged_hit'][index].values[0],
        'luck': mobs[mobs['mob_class'] == mob_class]['luck'][index].values[0],
        'enraged_luck': mobs[mobs['mob_class'] == mob_class]['enraged_luck'][index].values[0],
        'speed': mobs[mobs['mob_class'] == mob_class]['speed'][index].values[0],
        'enraged_speed': mobs[mobs['mob_class'] == mob_class]['enraged_speed'][index].values[0],
        'expertise': mobs[mobs['mob_class'] == mob_class]['expertise'][index].values[0],
        'enraged_expertise': mobs[mobs['mob_class'] == mob_class]['enraged_expertise'][index].values[0],
        'toughness': mobs[mobs['mob_class'] == mob_class]['toughness'][index].values[0],
        'enraged_toughness': mobs[mobs['mob_class'] == mob_class]['enraged_toughness'][index].values[0],
        'dodge': mobs[mobs['mob_class'] == mob_class]['dodge'][index].values[0],
        'enraged_dodge': mobs[mobs['mob_class'] == mob_class]['enraged_dodge'][index].values[0],
        #'healing_chance': mobs[mobs['mob_class'] == mob_class]['healing_chance'][index].values[0],
        #'enraged_healing_chance': mobs[mobs['mob_class'] == mob_class]['enraged_healing_chance'][index].values[0],
        'healing': mobs[mobs['mob_class'] == mob_class]['healing'][index].values[0],
        'enraged_healing': mobs[mobs['mob_class'] == mob_class]['enraged_healing'][index].values[0],
        'scare': mobs[mobs['mob_class'] == mob_class]['scare'][index].values[0],
        'enraged_scare': mobs[mobs['mob_class'] == mob_class]['enraged_scare'][index].values[0],
    }

def get_mob_inv(mob_class: object, mob_equipment: pd.DataFrame = mob_equipment):
    inv = []
    for row in mob_equipment.index:
        item_class = mob_equipment['mob_class'].iat[row]
        if mob_class == item_class:
            inv.append(mob_equipment['item'].iat[row])
    return inv

def initialize_mob(mob: object, mobs: pd.DataFrame, mob_equipment: pd.DataFrame):
    index = mobs.index[mobs['mob_class'] == mob.mob_class]
    mob.attack_style = mobs[mobs['mob_class'] == mob.mob_class]['attack_style'][index].values[0]
    mob.stats = get_mob_stats(mob.mob_class, mobs)
    mob.inv = get_mob_inv(mob.mob_class, mob_equipment)
    mob.starting_health = mob.stats['starting_hp']
    mob.health = mob.stats['starting_hp']
    mob.is_dead = False
    mob.enraged = False
    mob.starting_ai = mobs[mobs['mob_class'] == mob.mob_class]['ai'][index].values[0]
    mob.enraged_ai = mobs[mobs['mob_class'] == mob.mob_class]['enraged_ai'][index].values[0]
    return mob

def get_random_party_member(party: list) -> object:
    return party[random.randint(0,len(party)-1)]

def generic_wipe_taunts() -> list:
    return [
        "{mob} casually stands over {victim}'s corpse, mumbling, \"Not today....\"",
        "{mob} shouts in triumph!",
        "{mob} starts to shake, then suddenly begins to bellow with terrible, evil laughter.  \"Puny weaklings!\"",
        "{mob} sits atop {victim}'s head, grinding in, real deep.",
        "{mob} begins to pick at what remains of {victim}.  \"Well that was easy!\"",
    ]

def item_specific_wipe_taunts() -> list:
    return [
        "{mob} walks over to pick up {victim}'s {item}, immediately hurling it into {victim2}'s remains.  \"Take That!!\", they scream!!\nJesus Christ, what a CUNT!!",
        "{mob} immediately starts cackling, eyeing {victim}'s {item}.  \"What a pathetic little garbage weapon that was!  No wonder they wiped!!\"\nI hope you come back and teach these bitches a lesson!!",
        "{mob} sneers at {victim}'s dead body.  \"{item}?  Really?  You thought you could take ME down with your {item}??!!!\"\nNow was that really necessary.  Don't take their shit!!",
        "With her last dying breath, {victim} makes one more attempt with the {item}, completely missing {mob}, who begins to chuckle.\"  Guess I'd try the same, but, that was kinda sad....\"\nDon't let them get away with that.  Come back and take them down next time!!",
    ]

def get_loot(mob : object, party_dict : dict) -> dict:
    print('Add looting process here, per party member, from specific mob loot-tables in the items.csv')
    next()
    return party_dict

def get_stat_increases(party_dict : dict) -> dict:
    print('Add stat increase process here, per party member.  Right now, NOT specified by mob, or difficulty thereof, but this should probably be implemented.')
    next()
    return party_dict

def refresh_party(party : dict, increment : bool) -> dict:
    if increment:
        party['times_run_dungeon'] += 1
    party['wiped'] = False
    for heroine in party['party']:
        heroine.is_dead = False
        heroine.health = heroine.starting_health
    #party['narration'] = False  ####  Claude, this line may cause an issue yeah?  When the party gets refreshed after Happy, then even if narration was desired, it will stop after this point, won't it?  Can you look into what all may need to be fixed to make this work correctly, please?
    return party

def wipe_party(party_dict : dict) -> dict:
    party_dict['wiped'] = True
    for heroine in party_dict['party']:
        heroine.is_dead = True
        heroine.health = 0
    return party_dict

