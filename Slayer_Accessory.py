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
        'crit' : 20,
        'crit_mult' : 2.5,
        'low_miss' : 1,
        'high_miss' : 100,
        'luck' : 20,
        'expertise' : 50,
        'toughness' : 20,
        'dodge' : 15,
        'parry' : 20,
        'fear' : 20,
        'heal' : 100,
        'aoe_heal' : 20,
    }

def save_party(party : list, name : str = 'default'):
    jb.dump(party, f'saved_parties/{name}.pkl')

def load_party(name : str = 'default') -> list:
    return jb.load(f'saved_parties/{name}.pkl')