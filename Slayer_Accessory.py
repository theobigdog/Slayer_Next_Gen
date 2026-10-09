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

yes = ['YES','Y']
no = ['NO','N']

whines = ["Jesus Christ this game is pissing me off!  Sorry, I'm good, I'm good", "Would you stop that shit?  And I mean, right now!  Oh sorry", "I'm ready to kill somebody right now", "I just have zero patience for this shit, do I have to keep doing this?", "Why do I do this to myself?  I told mother I would never.... Umm Hi!", "I don't care.  I just don't even fucking care anymore.  What?  Oh!"]

items = pd.read_csv('supporting_docs/items.csv')
stats = pd.read_csv('supporting_docs/hero_stats.csv')
mobs = pd.read_csv('supporting_docs/mobs.csv')
mob_equipment = pd.read_csv('supporting_docs/mob_equipment.csv')


def get_hero_classes():
    return ['Warrior', 'Shifter', 'Battle_Mage', 'Hunter', 'Wizard', 'Sapper', 'Cleric']

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
    init()
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
        'crit_cutoff' : 20,
        'crit_mult_cutoff' : 2.5, ##  Does it even make sense to have this?
        'low_miss' : 1,
        'high_miss' : 100,
        'miss_threshold' : 70,
        'luck_cutoff' : 20,
        'expertise_cutoff' : 50,
        'toughness_cutoff' : 20,
        'dodge_cutoff' : 15,
        'parry_cutoff' : 20,
        'fear_cutoff' : 20,
        'heal_cutoff' : 100,
        'aoe_heal_cutoff' : 20,
    }

def get_dice_cutoffs_mobs() -> dict:  ### These are only for mobs, not heroine
    return {
        'crit_cutoff' : 20,
        'crit_mult_cutoff' : 5, ## Does it even make sense to have this?
        'miss_cutoff' : 30,
        'luck_cutoff' : 20,
        'expertise_cutoff' : 20,
        'toughness_cutoff' : 20,
        'dodge_cutoff' : 15,
        'healing_chance_cutoff' : 20,
        'scare_cutoff' : 20,
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
        'miss': mobs[mobs['mob_class'] == mob_class]['miss'][index].values[0],
        'enraged_miss': mobs[mobs['mob_class'] == mob_class]['enraged_miss'][index].values[0],
        'luck': mobs[mobs['mob_class'] == mob_class]['luck'][index].values[0],
        'enraged_luck': mobs[mobs['mob_class'] == mob_class]['enraged_luck'][index].values[0],
        'expertise': mobs[mobs['mob_class'] == mob_class]['expertise'][index].values[0],
        'enraged_expertise': mobs[mobs['mob_class'] == mob_class]['enraged_expertise'][index].values[0],
        'toughness': mobs[mobs['mob_class'] == mob_class]['toughness'][index].values[0],
        'enraged_toughness': mobs[mobs['mob_class'] == mob_class]['enraged_toughness'][index].values[0],
        'dodge': mobs[mobs['mob_class'] == mob_class]['dodge'][index].values[0],
        'enraged_dodge': mobs[mobs['mob_class'] == mob_class]['enraged_dodge'][index].values[0],
        'healing_chance': mobs[mobs['mob_class'] == mob_class]['healing_chance'][index].values[0],
        'enraged_healing_chance': mobs[mobs['mob_class'] == mob_class]['enraged_healing_chance'][index].values[0],
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
    #mob.stats = mob.stats[0]
    mob.inv = get_mob_inv(mob.mob_class, mob_equipment)
    mob.starting_health = mob.stats['starting_hp']
    mob.health = mob.stats['starting_hp']
    mob.is_dead = False
    mob.enraged = False