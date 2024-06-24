import random
from msvcrt import kbhit, getch
import time
from colorama import Fore, Back, Style, Cursor, win32, init
from colorama.winterm import WinTerm
import pandas as pd
import uuid
import csv
from dataclasses import dataclass
import joblib as jb

yes = ['YES','Y']
no = ['NO','N']

whines = ["Jesus Christ this game is pissing me off!  Sorry, I'm good, I'm good", "I'm ready to kill somebody right now", "I just have zero patience for this shit, do I have to keep doing this?", "Why do I do this to myself?  I told mother I would never.... Umm Hi!", "I don't care.  I just don't even fucking care anymore.  What?  Oh!"]

items = pd.read_csv('supporting_docs/items.csv')
stats = pd.read_csv('supporting_docs/hero_stats.csv')

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

def get_dice_cutoffs():
    return {
        'crit_cutoff' : 20,
        'crit_mult_cutoff' : 2.5,
        'low_miss' : 1,
        'high_miss' : 100,
        'luck_cutoff' : 20,
        'expertise_cutoff' : 50,
        'toughness_cutoff' : 20,
        'dodge_cutoff' : 15,
        'parry_cutoff' : 20,
        'fear_cutoff' : 20,
        'heal_cutoff' : 100,
        'aoe_heal_cutoff' : 20,
    }

def print_classes():
    print('Class Options:')
    print()
    for hero_class in get_hero_classes():
        print(hero_class)

def save_party(party : dict, name : str = 'default'):
    jb.dump(party, f'saved_parties/{name.title()}.pkl')
    print(f'Your party has been saved as {name.title()}.')
    print(f'Keep track of this saved name if you want to recover your party: {name.title()}')
    next()

def load_party(name : str = 'saved_parties/default.pkl') -> list:
    return jb.load(f'saved_parties/{name.title()}.pkl')

def whine() -> str:
    whine_itself = whines[random.randint(0, len(whines)-1)]
    whine_itself = str("..." + whine_itself)
    return whine_itself

def print_player_summary(party : dict, items : pd.DataFrame = items):
    for dudette in party:
        print(f"{dudette.name}:  {dudette.hero_class}")
        print('Inventory:  ')
        for inv_item in dudette.inv:
            item = items[items['item'] == inv_item]['item_desc'].values[0]
            print(item)
        print(f"Starting Health: {dudette.health}")
        print()
    next()

def get_items() -> pd.DataFrame:
    return items

def get_stats() -> pd.DataFrame:
    return stats