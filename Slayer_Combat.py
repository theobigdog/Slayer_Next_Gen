import Slayer_Accessory as acc
from Slayer_Accessory import wt, next, whine
import joblib as jb
import random
from colorama import Fore, Back, Style, Cursor
import time

def display_mob_summary(mob: dict):
    print(f"name: {mob.name}, type: {mob.mob_class}, attack style: {mob.attack_style}, mob stats: {mob.stats}, and mob inventory: {mob.inv}")

def display_party_summary(party : list):
    print()
    print()
    for heroine in party:
        low_health = heroine.health <= (heroine.starting_health * 0.1)
        half_health = heroine.health <= (heroine.starting_health * 0.5)
        if low_health:
            print(f"{heroine.heroine_name}:  {heroine.hero_class}, {Fore.RED}{int(round(heroine.health, 0))}{Style.RESET_ALL}/{heroine.starting_health}")
        elif half_health:
            print(f"{heroine.heroine_name}:  {heroine.hero_class}, {Fore.MAGENTA}{int(round(heroine.health, 0))}{Style.RESET_ALL}/{heroine.starting_health}")
        else:
            print(f"{heroine.heroine_name}:  {heroine.hero_class}, {int(round(heroine.health, 0))}/{heroine.starting_health}")

def show_current_status(party: dict, mob: dict):
    display_mob_summary(mob)
    display_party_summary(party)