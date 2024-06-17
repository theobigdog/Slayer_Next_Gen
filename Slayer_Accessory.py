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
        'low_miss_cutoff' : 1,
        'high_miss_cutoff' : 100,
        'luck_cutoff' : 20,
        'expertise_cutoff' : 50,
        'toughness_cutoff' : 20,
        'dodge_cutoff' : 15,
        'parry_cutoff' : 20,
        'fear_cutoff' : 20,
        'heal_cutoff' : 100,
        'aoe_heal_cutoff' : 20,
    }
'''
def write_to_csvX(file_path, data_instances):
    with open(file_path, mode='w', newline='') as f:
        writer = csv.writer(f)

        writer.writerow(data_instances[0].__annotations__.keys())

        for instance in data_instances:
            writer.writerow(instance.__dict__.values)

def save_charX(char) -> str:
    id = uuid.uuid4().hex
    #char.to_csv(f'saved_chars/{id}.csv')
    write_to_csvX(f'saved_chars/{id}.csv', char)
    return id

def save_partyX(party : list, name : str):    
    uuids = []
    for hero in party:
        uuids.append(save_charX(hero))
    
    with open(f'saved_parties/{name}', 'w') as f:
        write = csv.writer(f)
        write.writerow(uuids)
'''
        
def save_char(hero, id):
    jb.dump(hero, 'saved_chars/' + str(id) + '.pkl')

def save_party(party : list, name : str = 'default'):
    jb.dump(party, f'saved_parties/{name}.pkl')

