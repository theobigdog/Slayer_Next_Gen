import Slayer_Accessory as acc
from Slayer_Accessory import wt, next, whine
import joblib as jb
import random
from colorama import Fore, Back, Style, Cursor
import time

def display_party_summary(party : list):
    print()
    print()
    for heroine in party:
        low_health = heroine.health <= (heroine.starting_health * 0.1)
        if low_health:
            print(f"{heroine.heroine_name}:  {heroine.hero_class}, {Fore.RED}{heroine.health}{Style.RESET_ALL}/{heroine.starting_health}")
        else:
            print(f"{heroine.heroine_name}:  {heroine.hero_class}, {heroine.health}/{heroine.starting_health}")
    next()