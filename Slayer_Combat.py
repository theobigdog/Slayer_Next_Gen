import Slayer_Accessory as acc
from Slayer_Accessory import wt, next, whine
import joblib as jb
import random
from colorama import Fore, Back, Style, Cursor
import time

def display_mob_summary(mob: dict):
    print()
    print(f"Name: {mob.name}")
    print(f"Class: {mob.mob_class}")
    low_health = mob.health <= (mob.starting_health * 0.1)
    half_health = mob.health <= (mob.starting_health * 0.5)
    if low_health:
        print(f"Current Health: {Fore.RED}{int(round(mob.health, 0))}{Style.RESET_ALL}/{mob.starting_health}")
    elif half_health:
        print(f"Current Health: {Fore.MAGENTA}{int(round(mob.health, 0))}{Style.RESET_ALL}/{mob.starting_health}")
    else:
        print(f"Current Health: {mob.health}/{mob.starting_health}")

def display_party_summary(party : list):
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
    print('Enemy')
    display_mob_summary(mob)
    print()
    print()
    print('Party')
    display_party_summary(party)

def get_heroine_attack_rolls(heroine: object) -> dict:
    roll_results = {}
    heroine_stats = heroine.stats
    heroine_dice_cutoffs = acc.get_dice_cutoffs()
    crit = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['crit_cutoff'])
    miss = acc.multi_roll(heroine_stats['low_miss'], heroine_stats['high_miss'])
    luck = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['luck_cutoff'])
    expertise = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['expertise_cutoff'])
    toughness = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['toughness_cutoff'])
    dodge = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['dodge_cutoff'])
    parry = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['parry_cutoff'])
    fear = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['fear_cutoff'])
    heal = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['heal_cutoff'])
    aoe_heal = acc.multi_roll(heroine_dice_cutoffs['low'], heroine_dice_cutoffs['aoe_heal_cutoff'])
    if crit > heroine_stats['crit_mult']:
        roll_results['crit_mult'] = heroine_stats['crit_mult'] # crit roll is higher than cutoff, so the crit_mult is returned
    else:
        roll_results['crit_mult'] = 1 # if not a crit, multiplier is 1
    roll_results['miss'] = miss < heroine_dice_cutoffs['miss_threshold']
    roll_results['luck'] = luck > heroine_stats['luck']
    roll_results['expertise'] = expertise > heroine_stats['expertise']
    roll_results['toughness'] = toughness > heroine_stats['toughness']
    roll_results['dodge'] = dodge > heroine_stats['dodge']
    roll_results['parry'] = parry > heroine_stats['parry']
    roll_results['fear'] = fear > heroine_stats['fear']
    roll_results['heal'] = heal > heroine_stats['heal']
    roll_results['aoe_heal'] = aoe_heal > heroine_stats['aoe_heal']
    return roll_results
    